# Reviewing and releasing eliVibe

[v1.0.0](https://github.com/taibenvenuti/elivibe/releases/tag/v1.0.0) is the stable GitHub release. It and [v0.1.0](https://github.com/taibenvenuti/elivibe/releases/tag/v0.1.0) each shipped two archives and `SHA256SUMS`; keep both tags and their assets unchanged. [Status](status.md) identifies the release commit and which distribution checks actually ran. Do not advertise GitHub source installation on an old ref, or npm installation before a version resolves and works.

## Version and contents

`package.json` is the product manifest for Git, npm and the native archive. Keep its version, lockfiles, tag and archive names aligned. The [explicit semantic-release policy](../dev/release-policy.mjs) uses `fix` → patch, `feat` → minor and `!`/`BREAKING CHANGE` → major, including before 1.0. Never run semantic-release with its default plugins or mistake the untagged fixture result for a decision on this repository.

The host-managed **v1.0.0 release** broke the v0.1.0 contract: it replaced report-only inference with ordinary OMP conversation and retired isolated model, judge and route-approval controls. The reviewed squash subject was `feat(omp)!: explain handoffs in the host conversation`; the disclosure change was recorded in the squash body, release notes and migration guide. Always check the policy decision on the actual final main history before tagging.

From a **clean checkout of the exact reviewed main commit** with its hosted checks complete, prepare artifacts outside the repository. The steps below use the same dedicated Bash shell (`set -euo pipefail`); stop on any failed command or unexpected remote result. Fill in review inputs from the approval record, not from a moving ref or an earlier candidate.

```bash
: "${sha:?approved full main SHA}" "${version:?approved manifest version}"
test -z "$(git status --porcelain)"
test "$(git rev-parse HEAD)" = "$sha"
test "$(node -p 'require("./package.json").version')" = "$version"
output=$(mktemp -d)
assets=$(mktemp -d "$output/github.XXXXXXXX")
source_dir=$(mktemp -d "$output/source.XXXXXXXX")
zip="elivibe-$version.zip"
native="elivibe-omp-$version.tar.gz"
npm_tarball="$output/elivibe-$version.tgz"
python3.14 dev/package.py rehearse --commit "$sha" --version "$version" --license-id MIT
python3.14 dev/package.py build --commit "$sha" --version "$version" --license-id MIT --output-dir "$assets"
python3.14 dev/package.py verify --commit "$sha" --version "$version" --license-id MIT --output-dir "$assets"
git archive -o "$output/reviewed-source.tar" "$sha"
tar -xf "$output/reviewed-source.tar" -C "$source_dir"
(cd "$source_dir" && npm pack --offline --ignore-scripts --pack-destination "$output")
tar -tzf "$npm_tarball"
sha256sum "$assets/$zip" "$assets/$native" "$assets/SHA256SUMS" "$npm_tarball" > "$output/approved.sha256"
```

Inspect the **actual** npm `.tgz`: manifest, version, entry point, runtime, regular canonical skill, public documentation and MIT license. Compare the shipped files with the reviewed commit; verify that npm, the native archive and the standalone ZIP include the same skill bytes. Exclude lifecycle scripts, runtime dependencies, development files, credentials, private research and raw transcripts. Keep the npm tarball separate from the GitHub asset directory. Record and approve the exact names and digests, not just the fact that packaging ran. A changed source tree, squash SHA, package or dependency invalidates the corresponding evidence.

## Destination gates — do not conflate them

### Protected squash merge and Git source

The owner separately authorizes the merge of the reviewed PR head. Require a ready, current PR targeting protected `main`, resolved review threads, the Conventional Commit title and passing required jobs: **Product checks (Linux, Python 3.14, Node 24)** and **Native OMP smoke (Linux x64)**. Document review; sole-maintainer review is not independent approval. Do not use admin bypass, auto-merge, force-push or branch deletion.

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
test "$(git show -s --format=%s "$sha")" = "$subject"
test "$(git rev-parse "$sha^{tree}")" = "$(git rev-parse "$head^{tree}")"
gh run list -R "$repo" --workflow ci.yml --branch main --event push --commit "$sha" --status success
```

Inspect the run's two required jobs, read the final release decision, and prepare the artifacts above. Install `omp plugin install "github:$repo#$sha"` in a clean consumer environment. Record version, source, skill/command discovery and actual first use and removal; verify rollback with a retained installation. If trust, SSH or isolation blocks the test, report it rather than bypassing it. The [rehearsal workflow](../.github/workflows/release-rehearsal.yml) does not publish. Authenticated preview is separate; do not activate the [parked privileged workflow](../.github/release-workflow.yml).

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
python3.14 dev/package.py verify --commit "$sha" --version "$version" --license-id MIT --output-dir "$draft_assets"
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
python3.14 dev/package.py verify --commit "$sha" --version "$version" --license-id MIT --output-dir "$public_assets"
```

Use the public downloads to [try the standalone skill and link the native archive](installation.md). Record the verified public URL and consumer results before closing this gate.

### First npm publication

This is a separate write. Use the public registry and exact `elivibe` identity from the reviewed tarball. The package and `/latest` returned 404 during review; that is not a reservation or proof of ownership. Recheck anonymously just before the decision. For the planned **first** npm release, both must still be 404; a 200, conflicting owner or unexpected status means stop and investigate. In the owner's authorized publisher environment, compare `npm whoami` to the approved account. Identity does not prove permission to claim an unpublished name. Never read or print npm credentials or change auth settings to force a release.

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

From a clean unauthenticated consumer, confirm the pinned version and `latest` resolve to the same public package. Verify registry `dist.integrity` and compare an independent tarball download to the approved bytes:

```bash
integrity="sha512-$(openssl dgst -sha512 -binary "$npm_tarball" | openssl base64 -A)"
for ref in "$version" latest; do
  curl -q -fsS "$registry/elivibe/$ref" |
    jq -e --arg version "$version" --arg integrity "$integrity" \
      --arg url "$registry/elivibe/-/elivibe-$version.tgz" \
      '.name == "elivibe" and .version == $version and
       .repository.url == "git+https://github.com/taibenvenuti/elivibe.git" and
       .dist.integrity == $integrity and .dist.tarball == $url'
done
npm_download=$(mktemp -d)
curl -q -fsS "$registry/elivibe/-/elivibe-$version.tgz" -o "$npm_download/elivibe-$version.tgz"
cmp "$npm_tarball" "$npm_download/elivibe-$version.tgz"
omp plugin install "elivibe@$version"
omp plugin list --json
```

Check discovery, actual first use and removal in that clean OMP environment. Only then update [installation](installation.md), [compatibility](compatibility.md) and [status](status.md) with observed results. After any failed write, inspect remote state and digest before retrying. A published npm name/version cannot be reused for different bytes. A GitHub release does not publish to npm; neither destination grants marketplace acceptance.
