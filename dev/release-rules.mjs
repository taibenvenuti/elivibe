// Copyright (c) 2026 Tai Benvenuti
// SPDX-License-Identifier: GPL-3.0-only

import assert from "node:assert/strict";
import { execFileSync } from "node:child_process";
import { mkdtempSync, mkdirSync, rmSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";
import { Writable } from "node:stream";
import semanticRelease from "semantic-release";
import { verifyRelease } from "../.github/release-publish.mjs";
import { releasePolicy } from "./release-policy.mjs";

const releaseGate = fileURLToPath(new URL("../.github/release-publish.mjs", import.meta.url));

const work = mkdtempSync(join(tmpdir(), "elivibe-release-rules-"));
const env = {
  PATH: process.env.PATH,
  HOME: work,
  GIT_CONFIG_NOSYSTEM: "1",
  GIT_CONFIG_GLOBAL: "/dev/null",
  GIT_CONFIG_COUNT: "0",
  GIT_ALLOW_PROTOCOL: "file",
  GIT_TERMINAL_PROMPT: "0",
};
const cases = [
  ["untagged upstream default (never used for bootstrap)", ["feat: initial product"], "1.0.0", false],
  ["patch and scope", ["fix(adapter): retain original evidence"], "0.1.1"],
  ["minor and patch precedence", ["fix: first", "feat(omp): support depth", "fix: last"], "0.2.0"],
  ["pre-1.0 breaking bang", ["feat!: replace status"], "1.0.0"],
  ["pre-1.0 breaking footer and precedence", ["chore(release): update layout\n\nBREAKING CHANGE: packages moved", "feat: a feature", "fix: a fix"], "1.0.0"],
  ["pre-1.0 breaking ignored type", ["perf(adapter)!: remove compatibility"], "1.0.0"],
  ["no release", ["docs: clarify", "test: add coverage", "refactor: simplify", "chore: tidy", "Nothing conventional"], null],
  ["performance does not release", ["perf(core): speed up"], null],
  ["plain revert does not release", ["revert: undo"], null],
  ["Git revert of released fix does not release", ["git-revert"], null],
  ["fix and its Git revert cancel", ["fix-and-git-revert"], null],
];

try {
  for (const [index, [label, messages, expected, tagged = true]] of cases.entries()) {
    const cwd = join(work, `source-${index}`);
    const upstream = join(work, `upstream-${index}.git`);
    mkdirSync(cwd);
    const git = (...args) => execFileSync("git", args, { cwd, env, encoding: "utf8" }).trim();
    git("init", "-q", "--initial-branch=main", "--template=");
    git("config", "user.name", "Fixture");
    git("config", "user.email", "fixture@example.invalid");
    writeFileSync(join(cwd, "package.json"), JSON.stringify({ version: expected ?? "0.1.0" }));
    git("add", "package.json");
    git("commit", "--allow-empty", "-qm", "chore: baseline");
    if (messages.includes("git-revert")) {
      writeFileSync(join(cwd, "revert-fixture"), "original fix\n");
      git("add", "revert-fixture");
      git("commit", "-qm", "fix: released fix");
    }
    if (tagged) git("tag", "v0.1.0");
    for (const message of messages) {
      if (message === "git-revert") {
        git("revert", "--no-edit", "HEAD");
      } else if (message === "fix-and-git-revert") {
        writeFileSync(join(cwd, "revert-fixture"), "unreleased fix\n");
        git("add", "revert-fixture");
        git("commit", "-qm", "fix: unreleased fix");
        git("revert", "--no-edit", "HEAD");
      } else {
        git("commit", "--allow-empty", "-qm", message);
      }
    }
    git("clone", "-q", "--bare", cwd, upstream);
    const refs = () => git("ls-remote", "--refs", upstream);
    const before = refs();
    let log = "";
    const stdout = new Writable({ write(data, _encoding, done) { log += data; done(); } });
    try {
      const sha = git("rev-parse", "HEAD");
      const run = (approvedVersion) => semanticRelease({
        ...releasePolicy,
        repositoryUrl: pathToFileURL(upstream).href,
        ci: false,
        dryRun: true,
        plugins: [
          ...releasePolicy.plugins,
          [releaseGate, { approvedSha: sha, approvedVersion }],
        ],
      }, { cwd, env, stdout, stderr: stdout });
      const result = await run(expected);
      const actual = result?.nextRelease?.version ?? null;
      assert.equal(actual, expected);
      if (expected !== null) {
        assert.equal(result.nextRelease.gitTag, `v${expected}`);
        assert.equal(result.nextRelease.gitHead, sha);
        assert.match(result.nextRelease.notes, new RegExp(expected.replaceAll(".", "\\.")));
        assert.ok(result.nextRelease.notes.includes(`Built from \`${sha}\` (\`v${expected}\`)`));
      }
      if (index === 1) {
        await assert.rejects(run("0.1.2"), /did not select the approved version and commit/);
        await assert.rejects(
          verifyRelease(
            { approvedSha: sha, approvedVersion: "0.1.2" },
            { cwd, env, nextRelease: { version: "0.1.2", gitTag: "v0.1.2", gitHead: sha } },
          ),
          /does not match the committed package.json/,
        );
      }
      const tags = tagged ? "v0.1.0" : "";
      assert.equal(git("tag", "--list"), tags);
      assert.equal(refs(), before);
      console.log(`${label}: expected ${expected ?? "no release"}, actual ${actual ?? "no release"}`);
    } catch (error) {
      console.error(log);
      throw error;
    }
  }
} finally {
  rmSync(work, { recursive: true, force: true });
}
