# Release engineering

The first intended public version is `v0.1.0`; a local candidate is **not** a release. Git tags and the pinned semantic-release context govern public versions after bootstrap. Python's virtual developer project and the private Node workspace do not supply distribution versions. Use GitHub Releases only; npm, PyPI and marketplace publication are not configured.

## Release rules and rehearsal

The [policy](../tools/release-policy.mjs) uses the pinned commit analyzer and release-notes generator. Conventional `fix` → patch, `feat` → minor, and `!` or a `BREAKING CHANGE:` footer → major, even before 1.0. Scopes do not change the rule; the highest applicable bump wins. Ordinary `perf`, reverts, `docs`, `test`, `chore` and other types do not trigger a release. Git reverts paired with their original unreleased commit cancel. A breaking marker still triggers a major bump on an otherwise ignored type. Do not invoke semantic-release with its default configuration.

Run the [product checks](development.md#product-checks). Their release-policy fixture can also run separately once the Node lock is installed:

```sh
node tools/release-rules.mjs
```

This invokes the actual analyzer, notes generator and release guard via dry-run semantic-release against disposable local Git repositories. It prints expected and actual decisions and checks that the guard rejects the wrong approved version. Its untagged fixture intentionally demonstrates the upstream `1.0.0` default, **not** the initial candidate version. No real refs or remotes are touched. The [read-only rehearsal workflow](../.github/workflows/release-rehearsal.yml) can also check the selected checkout and build the candidate twice without uploading any assets.

## Build and verify an exact candidate

Use a clean checkout at the reviewed full SHA, with full history and tags, Python 3.14.4 and Git. The builder reads only fixed paths from that commit's Git tree, not local edits or untracked files. `--bootstrap` requires `0.1.0` and no existing stable release tag. It neither writes a tag nor asks semantic-release for the first version.

```sh
sha=$(git rev-parse HEAD)
version=0.1.0
output=$(mktemp -d)
python tools/package.py rehearse --version "$version" --commit "$sha" --bootstrap --license-id MIT
python tools/package.py build --version "$version" --commit "$sha" --bootstrap --license-id MIT --output-dir "$output"
python tools/package.py verify --version "$version" --commit "$sha" --bootstrap --license-id MIT --output-dir "$output"
```

The output directory must already exist and be empty for `build`. `verify` independently recreates the exact allowlisted bytes from the reviewed commit and rejects extra files, symlinks, malformed archives and altered checksums before extraction. `rehearse` builds twice in separate empty directories, compares the results, checks extraction and reports the skill digest, native manifest and asset SHA-256 values. No artifacts are written into the repository. An optional `--source-root` points to a different Git checkout root.

- `elivibe-0.1.0.zip`: `elivibe/SKILL.md`, byte-for-byte from the canonical skill, plus `LICENSE` and any `NOTICE` at archive root.
- `elivibe-omp-0.1.0.tar.gz`: the OMP adapter, core, Jev provider, canonical skill, generated private manifest and a relative `skills` link targeting `skill`. `LICENSE` and any `NOTICE` are at the package root. The archive excludes dependencies, logs, private sources and repository settings.
- `SHA256SUMS`: the two archive digests. Compare against the approved digest record; a checksum file from the same untrusted source is not independent authentication.

For another local version, pass it explicitly and omit `--bootstrap`. `0.1.0-rc.N` (positive `N`) is an optional local label for installation testing, **not** a published prerelease or an automation branch. Local prerelease builds do not require `--license-id`. If a matching Git tag is present, the supplied SHA must match its commit.

Every build takes `LICENSE` and any `NOTICE` from the reviewed revision, keeps them outside the runtime skill tree, and sets `MIT` in the private native manifest. Use `--license-id MIT` to assert the approved license for a stable release. Package verification tests the mechanics, not rights clearance.

## Install, update or remove the OMP plugin

Follow the [local setup instructions](installation.md). Verify the archive before extracting it into a fresh directory; use `tar` or another extractor that preserves the internal `skills` link. Keep the extracted directory: `omp plugin link` registers that directory, not the archive. Run native installation, update and rollback checks from both verified candidate archives in the [isolated OMP smoke](development.md#native-omp-smoke); this tests OMP 19.2.1 on Linux x64 with synthetic responses, not other host versions or a live provider.

## Hosted repository policy

The intended repository is `taibenvenuti/elivibe`, with `taibenvenuti` as sole maintainer and `main` as the default branch. Verify these settings in GitHub before publication; this policy does not mean they have been applied.

- Use pull requests and squash merges only. Use a Conventional Commit PR title as the squash commit subject. Require both **Product checks (Linux, Python 3.14, Node 24)** and **Native OMP smoke (Linux x64)** on the current PR revision. The sole maintainer records a self-review in the PR before merging after both checks pass; self-review is not independent approval. Revisit independent review when another maintainer joins.
- Protect `main` from force pushes and deletion. Protect `v*` release tags from update and deletion, and restrict creation to the authorized release actor. Verify that neither routine merges nor incidental workflow permissions can bypass these protections.
- Keep write access limited to authorized maintainers, routine workflow tokens read-only, and Actions unable to create or approve pull requests. Grant any future publisher only the permissions needed for the approved operation. Verify GitHub private vulnerability reporting is enabled and usable before the first public release.

If the host cannot enforce a required control, stop and have the owner review the gap before proceeding. Do not bypass a failed check to merge or release.

## Publication remains disabled

[Publication configuration](../.github/release-workflow.yml) is parked (EV-06) outside the active workflow directory and cannot be triggered. `v0.1.0` is a controlled bootstrap, not a semantic-release publication. Approve the public history, destination and rights first. On the exact trusted `main` SHA, verify both hosted checks and the local licensed `0.1.0` build, reproducibility, and native install/update/rollback gates. Review the notes and exact assets and digests before any publication.

Require explicit owner authorization before creating `v0.1.0` at that SHA or creating or publishing a GitHub Release. Review the draft before changing its visibility, and release only the approved bytes. Never tag an unreviewed revision or run uninitialized semantic-release to publish the first release. Confirm the release, notes, signed or otherwise approved tag provenance, downloaded asset bytes and installed manifest at the target. Keep the publisher parked throughout bootstrap.

If separately authorized **after** bootstrap, move the reviewed inactive workflow into `workflows/` and use explicit dispatch from trusted `main`; there is no push or pull-request publication trigger. Review actual branch and tag protections first. Set the approved `ELIVIBE_LICENSE_ID` and the exact `ELIVIBE_APPROVAL` tuple `OPERATION:SHA:VERSION:LICENSE_ID` as repository variables, then clear the approval after the attempt. `preview` authorizes only authenticated dry-run; `publish` requires a separate approval and explicit publication dispatch. No assumed environment reviewer gate or personal access token is needed.

Both named hosted jobs (product and native) must have succeeded in one `ci.yml` push attempt at the identical main SHA. The review job has a read-only token for checking those results and reruns local gates. Only the release job has `contents: write`: its pinned checkout receives the job token but does not persist credentials, and only the release-driver step receives that token as `GH_TOKEN`. Both jobs fetch full history and avoid untrusted caches and artifacts. The release driver checks `main` and tag/release state, verifies the expected version and prepares licensed assets before creating the tag. Release notes record the revision, tag, compatibility and verification limits; [CHANGELOG.md](../CHANGELOG.md) records the initial changes and notes policy.

Do not retry blindly after a failed publication. Check whether the tag exists (and where it points), the release state, notes and every asset digest, against the approved revision. A tag or release already using the target version blocks automation. Do not delete, retag, or overwrite published assets; preserve evidence and obtain owner authorization for incident handling, normally a corrected new version. After approved publication, verify separately downloaded assets and install the downloaded native archive.

## Verification levels

Record expected/actual decisions, commands, tested SHA, version, manifest and digests in the candidate review:

| Level | Evidence | Limit |
| --- | --- | --- |
| R1 | Disposable semantic-release decisions plus the `test_bootstrap_and_tag_require_exact_version_and_commit` regression | No package or destination authorization evidence |
| R2 | Candidate `rehearse`, `build`/`verify`, and isolated native install/update/rollback from verified assets | No authentication or upload evidence |
| R3 | Only if separately authorized: authenticated dry-run against the trusted branch and tags, with push-permission check and exact decision recorded | Dry-run is not offline, skips prepare/publish, and a no-release decision tests only that path. Untagged bootstrap uses local checks and owner review instead |
| R4 | Only after scoped owner approval: actual tag, release visibility, notes, downloaded hashes and native install at the authorized destination | No efficacy, broader compatibility or security certification |
