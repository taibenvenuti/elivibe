# Reviewing and releasing eliVibe

[v1.1.0](https://github.com/taibenvenuti/elivibe/releases/tag/v1.1.0) is the stable MIT release on GitHub and npm. It, [v1.0.0](https://github.com/taibenvenuti/elivibe/releases/tag/v1.0.0) and [v0.1.0](https://github.com/taibenvenuti/elivibe/releases/tag/v0.1.0) each shipped two archives and `SHA256SUMS` under MIT. Keep their terms, tags, bytes and evidence unchanged; project policy forbids replacing tags or assets, regardless of GitHub's immutable-release settings. [Status](status.md) records which distribution checks actually ran. The **2.0.0 GPL-3.0-only candidate is not published**. Use exact local candidate artifacts for review; keep public consumer examples on the last published, verified route.

## Version and contents

`package.json` is the product manifest for Git, npm and the native archive. Keep its version, lockfiles, tag and archive names aligned. The [explicit semantic-release policy](../dev/release-policy.mjs) uses `fix` → patch, `feat` → minor and `!`/`BREAKING CHANGE` → major, including before 1.0. Never run semantic-release with its default plugins or mistake the untagged fixture result for a decision on this repository.

The host-managed **v1.0.0 release** broke the v0.1.0 contract: it replaced report-only inference with ordinary OMP conversation and retired isolated model, judge and route-approval controls. The reviewed squash subject was `feat(omp)!: explain handoffs in the host conversation`; the disclosure change was recorded in the squash body, release notes and migration guide. Always check the policy decision on the actual final main history before tagging.

The proposed **2.0.0** release changes the license for newly distributed eliVibe copies to GPL-3.0-only, not the runtime behavior or the terms of older copies. Record that change in the approved squash message and release notes, including how to roll back to v1.1.0. A manifest version or fixture result alone is not a release-policy decision or publication approval.

From a **clean checkout of the exact reviewed main commit** with its hosted checks complete, prepare artifacts outside the repository. The steps below use the same dedicated Bash shell (`set -euo pipefail`) and pinned tools from [development](development.md); stop on any failed command or unexpected remote result. Fill in review inputs from the approval record, not from a moving ref or an earlier candidate. Build while the candidate tag is absent and retain those exact artifacts for approval and any retry.

```bash
: "${sha:?approved full main SHA}" "${version:?approved manifest version}"
test -z "$(git status --porcelain)"
test "$(git rev-parse HEAD)" = "$sha"
test "$(node -p 'require("./package.json").version')" = "$version"
test "$(node -p 'require("./package-lock.json").version')" = "$version"
test "$(node -p 'require("./package-lock.json").packages[""].version')" = "$version"
output=$(mktemp -d)
assets="$output/github"
zip="elivibe-$version.zip"
native="elivibe-omp-$version.tar.gz"
npm_tarball="$output/elivibe-$version.tgz"
sh dev/rehearse-release.sh candidate "$sha" "$output"
tar -tzf "$npm_tarball"
for member in README.md LICENSE; do
  git show "$sha:$member" | cmp - <(unzip -p "$assets/$zip" "$member")
  git show "$sha:$member" | cmp - <(tar -xOzf "$assets/$native" "elivibe-omp/$member")
  git show "$sha:$member" | cmp - <(tar -xOzf "$npm_tarball" "package/$member")
done
git show "$sha:LICENSE" | cmp - <(git show "$sha:skills/LICENSE")
git show "$sha:LICENSE" | cmp - <(git show "$sha:skills/elivibe/LICENSE")
git show "$sha:LICENSE" | cmp - <(unzip -p "$assets/$zip" elivibe/LICENSE)
git show "$sha:skills/elivibe/SKILL.md" | cmp - <(unzip -p "$assets/$zip" elivibe/SKILL.md)
git show "$sha:skills/elivibe/SKILL.md" | cmp - <(tar -xOzf "$assets/$native" elivibe-omp/skills/elivibe/SKILL.md)
git show "$sha:skills/elivibe/SKILL.md" | cmp - <(tar -xOzf "$npm_tarball" package/skills/elivibe/SKILL.md)
sha256sum "$assets/$zip" "$assets/$native" "$assets/SHA256SUMS" "$npm_tarball" > "$output/approved.sha256"
```

Inspect the **actual** npm `.tgz`: manifest (including `GPL-3.0-only`), version, entry point, runtime, regular canonical skill, public README with copyright attribution, and full GPLv3 text. The same notices and license must reach recipients of the native archive. The standalone ZIP has a root license and another in `elivibe/` so a copied skill directory keeps the license; the Git marketplace package ships its own root license, attributed README, and the same licensed skill directory. The npm pack runs offline with scripts disabled from a clean `git archive` of the approved SHA. Exclude lifecycle scripts, runtime dependencies, development files, credentials, private research and raw transcripts. Do not rebuild historical releases with the current builder. Keep the npm tarball separate from the GitHub asset directory. Approve exact names and digests; a changed source tree, squash SHA, package or dependency invalidates the corresponding evidence.

Use the helper's private export for npm. Both Git's archive mask and the extraction mask are pinned to `0022`: `npm pack` includes file permissions in the tar headers. With an inherited `0077` and otherwise identical source, the files would be `0600` instead of `0644`, changing registry integrity. An unexpected digest stops publication even when file contents match.

### License and corresponding source

Apply the [project's license policy](../README.md#license) to each actual delivery route, not just the project repository. When conveying source, preserve its license, copyright and other required notices. When conveying any covered file in a form other than its preferred form for modification, GPLv3 §6 also requires a compliant way for recipients to get the Corresponding Source for that exact copy, including scripts needed to generate, install and run the object code or modify the work. The shipped TypeScript and Markdown are source. The Git marketplace package and the candidate directory ZIP also ship `icon.svg`, the editable source corresponding to `icon.png`. Check the whole delivered package, including what the destination actually lets recipients obtain.

For a public download using GPLv3 §6(d), offer equivalent access to the exact Corresponding Source at no further charge. If hosted separately, put clear directions next to the download, check the link without credentials, and keep the source available as needed to satisfy the license. An unpushed SHA, moving branch, unrelated version, or generic repository URL is not that offer. Ensure the chosen channel preserves notices, source access and recipients' GPL rights without incompatible terms or technical restrictions. Record this for each destination before approval. Approval of local artifacts does not authorize sending them elsewhere; even a private upload may convey a copy to another party.

### Published reproduction or candidate rehearsal

The [read-only rehearsal workflow](../.github/workflows/release-rehearsal.yml) fetches full history and tags and uploads nothing. Its default **published** mode selects the highest stable annotated version tag reachable from the dispatch checkout (`v1.1.0` until a newer tag is reachable) and uses that tag's peeled commit, manifest, license and builder. Leave `candidate_sha` blank; optionally name another already published annotated `published_tag`. For the MIT `v0.1.0` tag, the helper uses the tag's `tools/package.py` to reproduce its three GitHub assets only, without applying the pre-tag `--bootstrap` guard. Check the tag signature with existing trust and compare the build output with the recorded digests or anonymous downloads; a tag by itself is not proof of publication.

For **candidate** mode, select the reviewed branch and enter its full `candidate_sha`, with `published_tag` blank. The workflow requires the selected checkout to match that SHA. The helper uses the candidate's own builder and manifest and rejects any existing `v<version>` tag. If a docs-only checkout still carries an already tagged version, use published mode for reproduction; do not substitute `HEAD` for the tag's commit or call the rebuilt tag a candidate.

To reproduce **published v1.1.0** locally, run from the repository root of a full clone with all release tags and the [pinned tools](development.md). The helper requires an existing empty output directory and uses the tagged revision's committed manifest and `npm@11.19.0`; there is no need to switch the checkout or install `node_modules` to run it. The hosted policy checks use the committed lock separately.

```bash
replay=$(mktemp -d)
sh dev/rehearse-release.sh published v1.1.0 "$replay"
```

Expect `published: v1.1.0 from 13b0cb94f66f6f9aa7793737201a5f95e2674997`. Compare the three files in `$replay/github` with the public downloads or approved digests in [status](status.md). Compare `$replay/elivibe-1.1.0.tgz` with its approved digest separately: this is a local reproduction, not a public npm download.

**2.0.0 candidate only — do not run candidate mode for v1.1.0.** Use the [candidate build](#version-and-contents) with `version=2.0.0`, the approved SHA carrying that version and GPL-3.0-only, and a new empty output directory. The helper takes `candidate SHA EMPTY_OUTPUT_DIR` and refuses an existing `v<version>` tag even if the SHA differs from the tag's commit. Keep those pre-tag digests separate from the published MIT record.

### Smoke the intended distribution

For the candidate, use OMP 19.2.1 and its checkout's [isolated native smoke](development.md#native-omp-smoke) with the three exact packages and a source archive of the same SHA, not the npm `latest` release:

```bash
git archive --format=tar.gz -o "$output/reviewed-source.tar.gz" "$sha"
python3.14 dev/omp_smoke.py --omp "$(command -v omp)" \
  --archive "$assets/elivibe-omp-$version.tar.gz" --skill-archive "$assets/elivibe-$version.zip" \
  --npm-archive "$output/elivibe-$version.tgz" --source-archive "$output/reviewed-source.tar.gz"
```

For published **1.0.0**, use that tag's own smoke driver and the **public** `elivibe-1.0.0.zip`, `elivibe-omp-1.0.0.tar.gz`, `SHA256SUMS` and `elivibe-1.0.0.tgz`. First compare each download to the corresponding published-mode rebuild (or the recorded SHA-256), then verify the archive manifest. The current candidate smoke driver expects newer archive contents; it is not a substitute for the tagged driver.

```bash
stable=v1.0.0
stable_replay=$(mktemp -d)
sh dev/rehearse-release.sh published "$stable" "$stable_replay"
stable_dir=$(mktemp -d)
mkdir "$stable_dir/source"
git archive --format=tar -o "$stable_dir/source.tar" "$stable"
tar -xf "$stable_dir/source.tar" -C "$stable_dir/source"
for file in elivibe-1.0.0.zip elivibe-omp-1.0.0.tar.gz SHA256SUMS; do
  curl -q -fsSL "https://github.com/taibenvenuti/elivibe/releases/download/$stable/$file" -o "$stable_dir/$file"
  cmp "$stable_replay/github/$file" "$stable_dir/$file"
done
curl -q -fsS https://registry.npmjs.org/elivibe/-/elivibe-1.0.0.tgz -o "$stable_dir/elivibe-1.0.0.tgz"
cmp "$stable_replay/elivibe-1.0.0.tgz" "$stable_dir/elivibe-1.0.0.tgz"
(cd "$stable_dir" && sha256sum -c SHA256SUMS)
python3.14 "$stable_dir/source/dev/omp_smoke.py" --omp "$(command -v omp)" \
  --archive "$stable_dir/elivibe-omp-1.0.0.tar.gz" --skill-archive "$stable_dir/elivibe-1.0.0.zip" \
  --npm-archive "$stable_dir/elivibe-1.0.0.tgz"
```

This OMP smoke uses controlled loopback inference and a disposable registry; actual public acquisition and first use are separate checks. For a release with Codex and Claude Code packaging, exercise the reviewed ZIP and exact Git source in fresh Codex CLI 0.162.1 and Claude Code 2.1.291 profiles on Linux x64. Compare the installed canonical skill, verify explicit discovery and removal, and record the source route/ref and resolved SHA. Use a detached local checkout at the reviewed SHA for an unpushed candidate; for stable public acquisition use the published ZIP and tag (Claude's `#ref` syntax requires a branch or tag). See [installation](installation.md) for the host commands. Label scripted inference, live output and untested routes separately.

### Directory preparation — local only

OpenAI's [submission workflow](https://developers.openai.com/plugins/deploy/submission) has a skills-only ZIP path. Prepare an inspection ZIP from the reviewed cross-harness tree with Git supporting `archive --mtime`. It is **not upload-approved**, not the standalone GitHub release ZIP, not a fourth GitHub asset and not the npm tarball.

For 2.0.0, use the `version` and exact approved `sha` from the candidate build. The ZIP includes `elivibe/LICENSE` with the skill and `icon.svg` with the exported PNG. To reproduce the historical MIT 1.1.0 directory ZIP instead, set `version=1.1.0` and `sha=$(git rev-parse 'v1.1.0^{commit}')`; its expected members remain unchanged.

```bash
dir=$(mktemp -d)
prep="$dir/elivibe-codex-$version.zip"
directory_paths=(.codex-plugin elivibe LICENSE README.md icon.png)
case "$version" in
  2.0.0) directory_paths+=(icon.svg) ;;
  1.1.0) test "$sha" = "$(git rev-parse 'v1.1.0^{commit}')" ;;
  *) exit 2 ;;
esac
TZ=UTC git archive --format=zip --mtime=1980-01-01T00:00:00Z -o "$prep" \
  "$sha:skills" "${directory_paths[@]}"
python3.14 - "$prep" "$sha" "$version" <<'PY'
import subprocess
import sys
from zipfile import ZipFile

expected = [
    ".codex-plugin/plugin.json", "elivibe/SKILL.md", "elivibe/agents/openai.yaml",
    "LICENSE", "README.md", "icon.png",
]
if sys.argv[3] == "2.0.0":
    expected += ["elivibe/LICENSE", "icon.svg"]
with ZipFile(sys.argv[1]) as archive:
    assert sorted(item.filename for item in archive.infolist() if not item.is_dir()) == sorted(expected)
    assert all(item.date_time == (1980, 1, 1, 0, 0, 0) for item in archive.infolist())
    for name in expected:
        assert archive.read(name) == subprocess.check_output(["git", "show", f"{sys.argv[2]}:skills/{name}"])
    if sys.argv[3] == "2.0.0":
        assert archive.read("LICENSE") == archive.read("elivibe/LICENSE")
PY
sha256sum "$prep"
```

For the [Claude Code submission portal](https://code.claude.com/docs/en/plugins/publish), the plugin's repository path is `skills` in `taibenvenuti/elivibe`, not the repository root or either ZIP. Review the checked-in `.claude-plugin/marketplace.json` and `skills/.claude-plugin/plugin.json`. For either directory, require separate owner approval and review the then-current submission, hosting and redistribution terms, including whether they let recipients retain GPLv3 rights and receive notices and any required source. Neither the vendor's acceptance of GPL-3.0-only uploads nor the compatibility of its terms with this candidate has been established. If the destination cannot meet those obligations, do not submit. Do not infer review, listing or publication from local CLI validation or successful ZIP construction.

## Destination gates — do not conflate them

### Protected squash merge and Git source

The owner separately authorizes the merge of the reviewed PR head. Require a ready, current PR targeting protected `main`, resolved review threads, the Conventional Commit title and passing required jobs: **Product checks (Linux, Python 3.14, Node 24)** and **Native OMP smoke (Linux x64)**. Document review; sole-maintainer review is not independent approval. Do not use admin bypass, auto-merge, force-push or branch deletion.

Before merging, calculate the version on the **proposed squash history**, not the topic branch's individual commits or the fixtures. Install the pinned development dependencies in the reviewed checkout (`npm ci --ignore-scripts --no-audit --no-fund`). Get the intended base from `origin/main`, verify it and the PR head are the reviewed inputs, and use the actual approved subject and body (including any breaking footer). This constructs one disposable commit with the proposed parent, message and reviewed tree. It makes no remote call for semantic-release and never publishes or tags.

```bash
: "${base:?approved full main parent SHA}" "${head:?approved full PR head SHA}"
: "${subject:?approved squash subject}" "${squash_body:?approved absolute squash body path}"
git fetch --tags origin main
test "$(git rev-parse FETCH_HEAD)" = "$base"
git merge-base --is-ancestor "$base" "$head"
review=$(mktemp -d)
policy="$PWD/dev/release-version.mjs"
git clone --quiet --no-hardlinks -- "$PWD" "$review/source"
(
  cd "$review/source"
  git switch --detach "$head"
  proposed=$(git -c user.name='Release rehearsal' -c user.email=rehearsal@example.invalid \
    commit-tree "$head^{tree}" -p "$base" -m "$subject" -F "$squash_body")
  git show -s --format='%H%n%P%n%T%n%B' "$proposed"
  node "$policy" "$proposed"
)
```

The helper runs the lockfile-pinned semantic-release and explicit policy on a disposable `main` and local upstream, enforces the candidate manifest version and checks that the dry-run leaves refs unchanged. Record the base tag and commit selected by the policy, proposed parent/tree/message, version and synthetic SHA. For **2.0.0**, expect `v1.1.0` as the base and require an approved breaking squash (`!` or a `BREAKING CHANGE` footer) that actually selects a major release. If the base, reviewed head, subject or body changes, repeat this calculation before merging.

```bash
repo=taibenvenuti/elivibe
: "${pr:?approved PR number}" "${head:?approved full PR head SHA}"
: "${subject:?approved Conventional Commit squash subject}" "${squash_body:?approved squash body file}"
gh pr view "$pr" -R "$repo" --json baseRefName,headRefOid,isDraft,title,mergeStateStatus |
  jq -e --arg head "$head" --arg title "$subject" \
    '.baseRefName == "main" and .headRefOid == $head and .title == $title and
     (.isDraft | not) and .mergeStateStatus == "CLEAN"'
gh pr checks "$pr" -R "$repo" --required
gh pr merge "$pr" -R "$repo" --squash --match-head-commit "$head" \
  --subject "$subject" --body-file "$squash_body"
```

Read the resulting commit from `gh pr view "$pr" -R "$repo" --json state,mergedAt,mergeCommit`; only use its full SHA once merged. In the release checkout fetch it, confirm it is the intended `main` tip and its tree and subject match the review, and check out that exact SHA. Record the successful `main` **push** run URL for that SHA, not the PR run:

```bash
: "${sha:?approved squash SHA}"
git fetch origin main
test "$(git rev-parse FETCH_HEAD)" = "$sha"
test "$(git rev-parse "$sha^")" = "$base"
test "$(git show -s --format=%s "$sha")" = "$subject"
test "$(git rev-parse "$sha^{tree}")" = "$(git rev-parse "$head^{tree}")"
gh run list -R "$repo" --workflow ci.yml --branch main --event push --commit "$sha" --status success
```

Inspect the run's two required jobs. Compare the final squash body to the approved message (including any breaking footer), then repeat the decision **before tagging** from a clean checkout of the final SHA with its locked dependencies: `node dev/release-version.mjs "$sha"`. Record the final SHA and confirmed version; the synthetic decision is not proof of the final main history. Prepare the artifacts above. If the approved SHA is reachable at the intended GitHub source, install `omp plugin install "github:$repo#$sha"` in a clean consumer environment; a local detached checkout proves a different route. Record version, source, skill/command discovery and actual first use and removal; verify rollback with the retained v1.1.0 installation or verified artifact for that route. If trust, SSH or isolation blocks the test, report it rather than bypassing it. Authenticated preview is separate; do not activate the [parked privileged workflow](../.github/release-workflow.yml).

### Signed tag and GitHub draft

Require explicit owner approval for the exact `sha` and `version`, license, digests, release title and notes before creating the protected tag or draft. Only a repository admin can create a `v*` tag; nobody can move or delete one. Use the approved signing identity and existing trust. For SSH signatures, set `allowed_signers` to a reviewer-controlled absolute path and use the command-scoped override below; for OpenPGP, use `git verify-tag "$tag"` with the approved trusted key. Do not alter global Git configuration or bypass a failed signature check.

```bash
: "${release_title:?approved title}" "${notes:?approved release notes file}"
tag="v$version"
test -z "$(git ls-remote --tags origin "refs/tags/$tag")"
test "$(git ls-remote origin refs/heads/main | cut -f1)" = "$sha"
sha256sum -c "$output/approved.sha256"
git tag -s "$tag" "$sha" -m "eliVibe $tag"
git -c gpg.ssh.allowedSignersFile="$allowed_signers" verify-tag "$tag"
test "$(git rev-parse "$tag^{}")" = "$sha"
git push origin "refs/tags/$tag"
test "$(git ls-remote origin "refs/tags/$tag" | cut -f1)" = "$(git rev-parse "$tag")"
test "$(git ls-remote origin "refs/tags/$tag^{}" | cut -f1)" = "$sha"
gh release create "$tag" -R "$repo" --verify-tag --draft --title "$release_title" \
  --notes-file "$notes" "$assets/$zip" "$assets/$native" "$assets/SHA256SUMS"
```

Confirm before any write that `origin` is the expected GitHub repository. If tag or draft creation fails, inspect remote state before retrying; do not replace a tag or clobber assets. Record the numeric release ID and the asset IDs, names and sizes:

```bash
gh api "repos/$repo/releases" --paginate \
  --jq ".[] | select(.tag_name == \"$tag\") | {id,tag_name,draft,prerelease,name,body,assets:[.assets[]|{id,name,size}]}"
```

Set `release_id` to the inspected numeric ID. Compare title and body with the approved copy. Download each asset independently by ID into an empty directory; verify the exact three names, bytes and manifest before seeking publication approval.

```bash
: "${release_id:?verified numeric draft ID}"
release_api="repos/$repo/releases/$release_id"
gh api "$release_api" | jq -S '{id,tag_name,draft,prerelease,name,body,
  assets: [.assets[] | {id,name,size,digest}] | sort_by(.name)}' > "$output/draft.json"
jq -e --arg tag "$tag" --arg title "$release_title" --arg zip "$zip" --arg native "$native" '
  .draft and (.prerelease | not) and .tag_name == $tag and .name == $title and
  ([.assets[].name] | sort) == (["SHA256SUMS", $zip, $native] | sort)
' "$output/draft.json"
draft_assets=$(mktemp -d)
for name in "$zip" "$native" SHA256SUMS; do
  asset_id=$(jq -er --arg name "$name" '.assets[] | select(.name == $name) | .id' "$output/draft.json")
  gh api "repos/$repo/releases/assets/$asset_id" -H 'Accept: application/octet-stream' > "$draft_assets/$name"
  cmp "$assets/$name" "$draft_assets/$name"
done
(cd "$draft_assets" && sha256sum -c SHA256SUMS)
python3.14 dev/package.py verify --commit "$sha" --version "$version" --license-id GPL-3.0-only --output-dir "$draft_assets"
```

### Publish the verified GitHub draft

Only after separate approval of that draft ID, notes and asset digests, compare the current draft to the approved snapshot. Publish by ID, without re-uploading anything. Then use a fresh anonymous consumer environment to confirm the same public release and download the three assets without credentials.

```bash
gh api "$release_api" | jq -S '{id,tag_name,draft,prerelease,name,body,
  assets: [.assets[] | {id,name,size,digest}] | sort_by(.name)}' | cmp "$output/draft.json" -
test "$(git ls-remote origin "refs/tags/$tag^{}" | cut -f1)" = "$sha"
gh api --method PATCH "$release_api" -F draft=false --jq '{id,tag_name,draft,prerelease,html_url}'
```

```bash
public_assets=$(mktemp -d)
curl -q -fsS "https://api.github.com/repos/$repo/releases/tags/$tag" |
  jq -e --argjson id "$release_id" --arg tag "$tag" \
    '.id == $id and .tag_name == $tag and (.draft or .prerelease | not)'
for name in "$zip" "$native" SHA256SUMS; do
  curl -q -fsSL "https://github.com/$repo/releases/download/$tag/$name" -o "$public_assets/$name"
  cmp "$assets/$name" "$public_assets/$name"
done
(cd "$public_assets" && sha256sum -c SHA256SUMS)
python3.14 dev/package.py verify --commit "$sha" --version "$version" --license-id GPL-3.0-only --output-dir "$public_assets"
```

Use the exact public assets in a fresh profile to try the standalone skill and link the native archive; apply the [installation guide's procedure](installation.md) with the newly verified filenames and checksum entries, not its v1.1.0 download links. Record the verified public URL, source-access evidence where required, and observed consumer results in [status](status.md).

Publishing affects only the approved GitHub draft and its three existing assets. A subsequent docs-only closure records observed results and remaining gates without changing the tag, assets, runtime or npm package; it still follows the [ordinary protected-main PR requirements](#protected-squash-merge-and-git-source). Independently audit the published bytes and consumer journeys before promotion. npm publication and directory submission each require separate authority and evidence.

### First npm publication

The [first npm version, `elivibe@1.0.0`](https://www.npmjs.com/package/elivibe/v/1.0.0), is public and [consumer-verified](status.md). The bootstrap steps below are retained for reference; do not rerun them for `elivibe`.

This was a separate write to the public registry under the exact `elivibe` identity from the reviewed tarball. The package and `/latest` returned 404 during review; that was not a reservation or proof of ownership. The first-version preflight required both still to return 404 immediately before the decision; a 200, conflicting owner or unexpected status meant stop and investigate. The authorized publisher had to match `npm whoami` to the approved account; identity alone did not establish permission to claim an unpublished name. Never read or print npm credentials or change auth settings to force a release.

```bash
registry=https://registry.npmjs.org
for path in elivibe elivibe/latest; do
  test "$(curl -q -sS -o /dev/null -w '%{http_code}' "$registry/$path")" = 404
done
: "${publisher:?approved npm account}"
test "$(npm whoami --registry="$registry")" = "$publisher"
tar -xOzf "$npm_tarball" package/package.json |
  jq -e --arg version "$version" '.name == "elivibe" and .version == $version and
    .repository.url == "git+https://github.com/taibenvenuti/elivibe.git"'
sha256sum -c "$output/approved.sha256"
```

[npm Trusted Publishing](https://docs.npmjs.com/trusted-publishers/) is configured in **existing package settings**; [first-version OIDC support](https://github.com/npm/cli/issues/8544) is not available for this bootstrap. The repository's active workflows are **Product checks** and **Release rehearsal (no publication)**, neither with `id-token: write`. A later trusted publisher needs a separately approved workflow under `.github/workflows/`, matching npm's owner/repository/workflow filename and environment (if configured), `id-token: write`, a GitHub-hosted runner, npm ≥ 11.5.1 and Node ≥ 22.14.0. Do not bootstrap with placeholder bytes or enable automated publication here.

After explicit approval of the account, exact tarball, version, public visibility and `latest` tag, the authorized owner publishes with normal npm authentication and [interactive 2FA](https://docs.npmjs.com/creating-and-publishing-unscoped-public-packages/). If that path isn't available, stop.

```bash
npm publish "$npm_tarball" --ignore-scripts --access public --tag latest --registry="$registry"
```

### Subsequent npm publications

This is an independent write to the existing public package. Use the final main SHA and policy result, package bytes and SHA-256 digests already approved above. Never repack from `main` or publish from a directory. Confirm the `origin` repository and recheck that the target Git tag is either **absent** or the **same signed annotated tag at the approved SHA**. Check the unpeeled and peeled remote refs (`git ls-remote` below) and verify a matching tag with the existing signing trust as above. A local or remote conflict, lightweight tag, missing matching local tag, or bad signature stops the gate; never create or repair a tag to get past npm preflight.

```bash
tag="v$version"
remote_tag=$(git ls-remote --sort=refname origin "refs/tags/$tag" "refs/tags/$tag^{}")
if test -n "$remote_tag"; then
  tagged=$(git rev-parse --verify "refs/tags/$tag^{tag}")
  test "$(git rev-parse "refs/tags/$tag^{commit}")" = "$sha"
  test "$remote_tag" = "$(printf '%s\trefs/tags/%s\n%s\trefs/tags/%s^{}' "$tagged" "$tag" "$sha" "$tag")"
  git -c gpg.ssh.allowedSignersFile="$allowed_signers" verify-tag "$tag"
else
  test -z "$(git for-each-ref --format='%(refname)' "refs/tags/$tag")"
fi
```

Separately inspect the registry anonymously. Set `npm_latest_before` from the approved rollout baseline, not from this lookup. For a 2.0.0 rollout directly after the current release, the expected baseline is `1.1.0`; the historical 1.1.0 publication used `1.0.0`. A 404 at the **version endpoint** is required before the first publish attempt; the existing package and `latest` are expected to resolve.

```bash
registry=https://registry.npmjs.org
: "${npm_latest_before:?approved pre-publication latest version}"
sha256sum -c "$output/approved.sha256"
tar -xOzf "$npm_tarball" package/package.json |
  jq -e --arg version "$version" '.name == "elivibe" and .version == $version and
    .license == "GPL-3.0-only" and .repository.url == "git+https://github.com/taibenvenuti/elivibe.git"'
probe=$(mktemp -d)
status=$(curl -q -sS -H 'Cache-Control: no-cache' -o "$probe/target.json" -w '%{http_code}' \
  "$registry/elivibe/$version")
latest=$(curl -q -fsS -H 'Cache-Control: no-cache' "$registry/elivibe/latest" |
  jq -er 'select(.name == "elivibe") | .version')
case "$status" in
  404) test "$latest" = "$npm_latest_before" ;;
  200) test "$latest" = "$version" ;;
  *) printf 'Unexpected npm status: %s\n' "$status" >&2; exit 1 ;;
esac
```

- **404 and expected previous `latest`:** continue to the publisher checks below.
- **200 and target is `latest`:** go straight to [public verification](#verify-public-npm-bytes-and-first-use). If both manifest responses, registry integrity and downloaded bytes match the approved artifact, record *already published*; do not publish again.
- **Anything else:** stop. This includes different bytes, a moved `latest`, a missing package, or unexpected registry status. Do not republish, unpublish, move `latest`, retry on a different version, or widen permissions to work around a failed gate.

For the absent target, in the authorized publisher's environment, check the account against the approval and the current [npm owners](https://docs.npmjs.com/cli/v11/commands/npm-owner/) for `elivibe`. Confirm that the account can publish under the package's current policy and that the intended interactive 2FA path is available. Owner membership is not a substitute for 2FA, package policy or explicit release authorization. Do not print, copy or change credentials. If the identity, rights or required authentication do not match, stop.

```bash
: "${publisher:?approved npm account}"
test "$(npm whoami --registry="$registry")" = "$publisher"
npm owner ls elivibe --registry="$registry" |
  awk -v publisher="$publisher" '$1 == publisher { found = 1 } END { exit !found }'
```

After separate approval for this account, package/version, exact tarball digest, public visibility and `latest`, serialize the publish with other maintainers. Recheck the tag state, version absence and unchanged prior `latest` immediately before the write, and rehash the tarball. The registry does not offer an atomic compare-and-set of `latest`; a competing publish means stop and inspect. Run only the approved interactive publish; no `dist-tag add`, auth bypass, or parked-workflow activation.

```bash
test "$(curl -q -sS -H 'Cache-Control: no-cache' -o /dev/null -w '%{http_code}' \
  "$registry/elivibe/$version")" = 404
test "$(curl -q -fsS -H 'Cache-Control: no-cache' "$registry/elivibe/latest" |
  jq -er 'select(.name == "elivibe") | .version')" = "$npm_latest_before"
sha256sum -c "$output/approved.sha256"
npm publish "$npm_tarball" --ignore-scripts --access public --tag latest --registry="$registry"
```

If npm accepts the tarball **for processing**, record that the write was accepted. An immediate public 404 or the previous `latest` does not authorize a second publish. Wait for the public registry to serve the version, then verify it below. If it remains unavailable, leave the distribution gate open and have the maintainer check npm's publication status.

### Verify public npm bytes and first use

From a fresh unauthenticated consumer, using the approved tarball as a byte reference only, confirm the pinned version and `latest` resolve to the same public package. Verify registry `dist.integrity` and compare an independent tarball download to the approved bytes. Use the same verification for an already-published exact target and for recovery after an ambiguous publish response; never retry blindly.


```bash
registry=https://registry.npmjs.org
integrity="sha512-$(openssl dgst -sha512 -binary "$npm_tarball" | openssl base64 -A)"
for ref in "$version" latest; do
  curl -q -fsS -H 'Cache-Control: no-cache' "$registry/elivibe/$ref" |
    jq -e --arg version "$version" --arg integrity "$integrity" \
      --arg url "$registry/elivibe/-/elivibe-$version.tgz" \
      '.name == "elivibe" and .version == $version and .license == "GPL-3.0-only" and
       .repository.url == "git+https://github.com/taibenvenuti/elivibe.git" and
       .dist.integrity == $integrity and .dist.tarball == $url'
done
npm_download=$(mktemp -d)
curl -q -fsS "$registry/elivibe/-/elivibe-$version.tgz" -o "$npm_download/elivibe-$version.tgz"
cmp "$npm_tarball" "$npm_download/elivibe-$version.tgz"
omp plugin install "elivibe@$version"
omp plugin list --json
```
In that clean OMP 19.2.1 environment, record the registry source and pinned install command alongside the observed plugin name, version, installed path and extension; the listing does not itself prove the source. Start a fresh session, confirm `/elivibe` discovery and try a synthetic handoff with normal authorized access if available. Then remove the plugin and confirm absence in another fresh session:

```bash
omp plugin uninstall elivibe
omp plugin list --json
```

Record any blocked first-use step rather than claiming success from the byte comparison or the isolated fixture. Only then update [installation](installation.md), [compatibility](compatibility.md) and [status](status.md) with observed results. A published npm name/version cannot be reused for different bytes. A GitHub release does not publish to npm; neither destination grants marketplace acceptance.

