// Used only by the inactive publication workflow, after a separately authorized bootstrap.
import { execFileSync } from "node:child_process";
import { mkdtempSync, rmSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { Writable } from "node:stream";
import { fileURLToPath } from "node:url";
import semanticRelease from "semantic-release";
import { releasePolicy } from "../tools/release-policy.mjs";

const sha = process.env.ELIVIBE_SHA;
const version = process.env.ELIVIBE_EXPECTED_VERSION;
const license = process.env.ELIVIBE_LICENSE_ID;
const repo = process.env.GITHUB_REPOSITORY;
const token = process.env.GH_TOKEN;
const semver = /^(?:0|[1-9][0-9]*)(?:\.(?:0|[1-9][0-9]*)){2}$/;
const git = (...args) => execFileSync("git", args, { encoding: "utf8", stdio: "pipe" }).trim();

class ReleaseGateError extends Error {}

export async function verifyRelease({ approvedSha, approvedVersion }, { nextRelease }) {
  if (nextRelease.version !== approvedVersion ||
      nextRelease.gitTag !== `v${approvedVersion}` || nextRelease.gitHead !== approvedSha) {
    throw new ReleaseGateError("semantic-release did not select the approved version and commit");
  }
}

export async function generateNotes(_options, { nextRelease }) {
  return "Built from `" + nextRelease.gitHead + "` (`" + nextRelease.gitTag + "`). " +
    "See the attached SHA256SUMS and the review record for verification limits. " +
    "The native integration targets OMP 19.2.1; synthetic tests do not exercise live provider behavior.";
}

async function github(path, expected = 200) {
  const url = `https://api.github.com/repos/${repo}` + (path ? `/${path}` : "");
  const response = await fetch(url, {
    redirect: "error",
    headers: {
      authorization: `Bearer ${token}`,
      accept: "application/vnd.github+json",
      "x-github-api-version": "2022-11-28",
    },
    signal: AbortSignal.timeout(15_000),
  });
  if (response.status !== expected) {
    throw new ReleaseGateError(`GitHub preflight rejected the release state (status ${response.status})`);
  }
  return expected === 200 ? response.json() : undefined;
}

async function requireCurrentMain() {
  const branch = await github("git/ref/heads/main");
  if (branch.object.sha !== sha) throw new ReleaseGateError("approved SHA is no longer the head of main");
  await github(`git/ref/tags/v${version}`, 404);
}

export async function prepare(options, { cwd }) {
  const args = ["--output-dir", options.assetsDir,
    "--version", version, "--commit", sha, "--license-id", license];
  const { GH_TOKEN: _gh, GITHUB_TOKEN: _github, ...env } = process.env;
  for (const command of ["build", "verify"]) {
    try {
      execFileSync("python", ["tools/package.py", command, ...args], { cwd, env, stdio: "pipe" });
    } catch {
      throw new ReleaseGateError(`licensed package ${command} failed`);
    }
  }
  await requireCurrentMain();
}

async function main([mode, ...extra]) {
  const operation = mode === "--dry-run" ? "preview" : "publish";
  if (extra.length || !["--dry-run", "--publish"].includes(mode) ||
      process.env.GITHUB_ACTIONS !== "true" || process.env.GITHUB_REF !== "refs/heads/main" ||
      !/^[0-9a-f]{40}$/.test(sha ?? "") || !semver.test(version ?? "") || version === "0.1.0" ||
      !/^[A-Za-z0-9][A-Za-z0-9.-]*$/.test(license ?? "") ||
      !/^[A-Za-z0-9_.-]+\/[A-Za-z0-9_.-]+$/.test(repo ?? "") || !token ||
      process.env.ELIVIBE_APPROVAL !== `${operation}:${sha}:${version}:${license}` ||
      git("rev-parse", "HEAD") !== sha) {
    throw new ReleaseGateError("release requires approval for this operation, main SHA, stable version, and license");
  }
  git("merge-base", "--is-ancestor", "refs/tags/v0.1.0^{commit}", sha);
  const config = await github("");
  if (config.default_branch !== "main") throw new ReleaseGateError("release repository does not use main");
  await requireCurrentMain();
  for (let page = 1; ; page++) {
    const releases = await github(`releases?per_page=100&page=${page}`);
    if (releases.some((release) => release.tag_name === `v${version}`)) {
      throw new ReleaseGateError("a release already uses the approved tag; inspect it before retrying");
    }
    if (releases.length < 100) break;
  }

  const assetsDir = mkdtempSync(join(tmpdir(), "elivibe-publish-"));
  // Do not send Git/authentication diagnostics or commit messages to action logs.
  const quiet = new Writable({ write(_data, _encoding, done) { done(); } });
  try {
    const result = await semanticRelease({
      ...releasePolicy,
      repositoryUrl: `https://github.com/${repo}.git`,
      dryRun: mode === "--dry-run",
      plugins: [
        ...releasePolicy.plugins,
        [fileURLToPath(import.meta.url), { assetsDir, approvedSha: sha, approvedVersion: version }],
        ["@semantic-release/github", {
          assets: ["elivibe-" + version + ".zip", "elivibe-omp-" + version + ".tar.gz", "SHA256SUMS"]
            .map((filename) => join(assetsDir, filename)),
          successComment: false,
          failComment: false,
          releasedLabels: false,
          failTitle: false,
        }],
      ],
    }, { stdout: quiet, stderr: quiet });
    if (!result || result.nextRelease.version !== version || result.nextRelease.gitHead !== sha) {
      throw new ReleaseGateError("no release selected for the approved version and commit");
    }
    console.log(`${operation} completed for v${version} at ${sha}; semantic-release checked Git push permission`);
  } finally {
    rmSync(assetsDir, { recursive: true, force: true });
  }
}

if (process.argv[1] === fileURLToPath(import.meta.url)) {
  main(process.argv.slice(2)).catch((error) => {
    console.error(error instanceof ReleaseGateError
      ? error.message
      : "Release operation failed; inspect the tag and release state before retrying.");
    process.exitCode = 1;
  });
}
