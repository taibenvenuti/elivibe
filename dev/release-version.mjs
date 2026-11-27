import assert from "node:assert/strict";
import { execFileSync } from "node:child_process";
import { mkdtempSync, readFileSync, rmSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { Writable } from "node:stream";
import { pathToFileURL } from "node:url";
import semanticRelease from "semantic-release";
import { releasePolicy } from "./release-policy.mjs";

const [sha, ...extra] = process.argv.slice(2);
assert.ok(!extra.length && /^[0-9a-f]{40}$/.test(sha ?? ""), "Pass the full proposed or final main SHA");
const work = mkdtempSync(join(tmpdir(), "elivibe-release-version-"));
try {
  const env = {
    PATH: process.env.PATH,
    HOME: work,
    GIT_CONFIG_NOSYSTEM: "1",
    GIT_CONFIG_GLOBAL: "/dev/null",
    GIT_CONFIG_COUNT: "0",
    GIT_ALLOW_PROTOCOL: "file",
    GIT_TERMINAL_PROMPT: "0",
    GIT_NO_REPLACE_OBJECTS: "1",
  };
  const git = (cwd, ...args) => execFileSync("git", args, { cwd, env, encoding: "utf8" }).trim();
  const root = git(process.cwd(), "rev-parse", "--show-toplevel");
  assert.equal(git(root, "rev-parse", "--is-shallow-repository"), "false", "Fetch full history and tags");
  assert.equal(git(root, "rev-parse", "--verify", `${sha}^{commit}`), sha);
  git(root, "merge-base", "--is-ancestor", "refs/tags/v1.0.0^{commit}", sha);
  for (const path of ["dev/release-policy.mjs", "package.json", "package-lock.json"]) {
    const committed = execFileSync("git", ["show", `${sha}:${path}`], { cwd: root, env });
    assert.ok(readFileSync(new URL(`../${path}`, import.meta.url)).equals(committed),
      `Use the reviewed checkout's ${path}`);
  }
  const expected = JSON.parse(git(root, "show", `${sha}:package.json`)).version;
  const remote = join(work, "upstream.git");
  const cwd = join(work, "main");
  git(work, "clone", "--quiet", "--bare", "--shared", "--", root, remote);
  git(remote, "branch", "--force", "main", sha);
  git(work, "clone", "--quiet", "--branch", "main", "--", remote, cwd);
  const refs = () => git(remote, "for-each-ref");
  const before = refs();
  const quiet = new Writable({ write(_data, _encoding, done) { done(); } });
  const result = await semanticRelease({
    ...releasePolicy, repositoryUrl: pathToFileURL(remote).href, ci: false, dryRun: true,
  }, { cwd, env, stdout: quiet, stderr: quiet });
  assert.equal(refs(), before, "Dry-run changed the disposable upstream");
  assert.ok(result, `Pinned policy selects no release at ${sha}`);
  const { lastRelease, nextRelease } = result;
  assert.equal(nextRelease.gitHead, sha);
  assert.equal(nextRelease.version, expected, "Pinned policy and committed manifest disagree");
  assert.equal(nextRelease.gitTag, `v${expected}`);
  console.log(`${lastRelease.gitTag} (${lastRelease.gitHead}) -> ${nextRelease.gitTag} (${sha})`);
} finally {
  rmSync(work, { recursive: true, force: true });
}
