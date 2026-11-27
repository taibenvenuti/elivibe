# Development

The [standalone skill](../skill/elivibe/SKILL.md) and native plugin use the same method. OMP loads the plugin's TypeScript sources directly. Node, npm, uv and Python are development tools, not prerequisites for using a prebuilt plugin or the standalone skill.

## Product checks

Start with a full Git checkout containing `main` or `origin/main`. The clean setup target is Linux x64 (including WSL2), with CPython 3.14.4, uv 0.12.5, Node 24.21.0 and its npm. From the checkout:

```sh
sh tools/check --setup
```

Setup uses `uv sync --locked` with wheels, `npm ci` with install scripts and implicit audit disabled, and the SHA-256-verified actionlint 1.7.12 release. It needs network access to trusted public tool and dependency sources, not provider accounts, credentials or private research. After setup, `sh tools/check` reuses the toolchain without downloads. Run setup again when tooling or lockfiles change.

The same entry point runs in **Product checks (Linux, Python 3.14, Node 24)**. It checks workflow syntax, package and test configuration, active local Markdown links and heading anchors, shell example syntax without executing examples, Conventional Commit subjects, Ruff formatting and lint, the active Python and Node tests, and release rule fixtures. Links to external sites are not fetched and archived research is not in the gate.

TypeScript uses strict, no-emit `tsc` for the core, provider, adapter and portable test sources, against the actual declarations from the pinned OMP package. External declaration internals are not rechecked. The adapter's fake-host fixtures run as Node tests, not as proof of native compatibility. Follow the surrounding TypeScript source style; don't run a broad reformatter. Ruff covers the active Python tooling and tests; there is no separate Python type checker. See [release](release.md) for the package and immutable revision checks.

## Native OMP smoke

Use the official [OMP 19.2.1 Linux x64 asset](https://github.com/can1357/oh-my-pi/releases/download/v19.2.1/omp-linux-x64), CPython 3.14 and system bubblewrap with working unprivileged namespaces. The pinned SHA-256 is `e8b937f9bf023baa147bdd300ad5421af0a6ef8b1f350c47a9a93d5fca94feca`. Verify the digest before making the asset executable; the smoke script independently verifies the digest and host version. Pass verified packages built from the same reviewed Git commit, at different versions so the test can detect update and rollback:

```sh
python3.14 tools/omp_smoke.py --omp /absolute/path/to/verified/omp \
  --skill-archive /absolute/path/to/candidate/elivibe-0.1.0.zip \
  --archive /absolute/path/to/candidate/elivibe-omp-0.1.0.tar.gz \
  --update-archive /absolute/path/to/update/elivibe-omp-0.1.0-rc.1.tar.gz
```

The separate **Native OMP smoke (Linux x64)** job builds and verifies both packages from its checkout SHA using reserved, untagged fixture versions (`0.0.0-rc.1` and `0.0.0-rc.2`). Local release acceptance still exercises the actual candidate version as shown above.

On the disposable Ubuntu 24.04 GitHub-hosted VM the native job probes Bubblewrap before package preparation. Only on a matching AppArmor `unprivileged_userns` denial of `net_admin` does it load Ubuntu's [opt-in Bubblewrap profile](https://bugs.launchpad.net/ubuntu/+source/apparmor/+bug/2064672). The job verifies the package and profile digests, adds only that profile without replacing existing policy, and checks the enforced child stack. Bubblewrap may use namespace capabilities for setup; its payload cannot. The job verifies private loopback, no external route and no payload capabilities before running OMP. Any other failure blocks the gate. Do not apply this CI accommodation to developer machines, relax global restrictions or substitute a mocked import.

The smoke uses disposable profiles and synthetic loopback responses. It does not access your normal profile or establish live-provider compatibility, quality, latency or cost.

## Manual regression

Try the [ordinary OMP path](../README.md#quick-start) on a meaningful task in an approved session. Read the technical report and the supplement separately. Is the original still available? Can a reader now explain a distinction, mechanism or consequence that was implicit in the report? Check that the explanation preserves what is unknown and does not turn a safeguard into permission. No extra tools or checks should be needed merely to write it.

Use the [constructed QA examples](qa-examples.md) as prompts, not as wording or scoring requirements. Record observations with their limits and keep private source, raw results and credentials outside Git and CI.

## Commit and CI policy

Use a Conventional Commit PR title such as `fix(omp): preserve the original handoff`; use the title as the squash commit subject. The check reruns on title edits and independently checks all main subjects on a main push. Avoid ordinary merge commits and preserve signed-commit practices. CI uses read-only permissions, pinned actions and no saved checkout credential. Only trusted main pushes write the uv cache.

The recommended `main` protection is to require pull requests and both named product checks, allow squash merges only with the PR title as the default subject, and block force-pushes and deletion. This is a recommendation, not a claim about hosted settings. Local validation does not establish hosted execution or permissions.

## Dependency maintenance

Use reviewed manual update PRs. Change exact pins and regenerate both affected lockfiles using the existing tooling. Review lockfile origin and integrity changes, public license declarations and advisories, then run clean product and native checks. Keep `npm ci --ignore-scripts` and SHA-pinned workflow actions; don't run audit fixes or automated downgrades. No dev dependency is bundled in a product asset.

For review, query the npm registry with `npm audit --package-lock-only --ignore-scripts` and inspect the locked license metadata; query PyPI's public `/pypi/<name>/<version>/json` for each registry package in `uv.lock`, including transitives. Send public dependency names and versions only, not project content. A missing license needs follow-up, not an inferred license: for example, `qrcode-terminal` lacks a license field in the lock but its exact release's npm metadata declares Apache 2.0. Registry metadata is not a redistribution clearance or a complete security inventory.

Review serious advisories against the product and privileged release paths. For example, the OMP npm package is pinned for TypeScript declarations, not imported at runtime or shipped in either bundle. Audit findings in its transitive dependencies do not assess the separate native executable. Reassess if the version, import boundary or execution path changes. See [release](release.md) for publication safeguards.
