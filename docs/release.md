# Reviewing and releasing eliVibe

The [v0.1.0 GitHub release](https://github.com/taibenvenuti/elivibe/releases/tag/v0.1.0) shipped two archives and `SHA256SUMS`. Keep its tag and bytes unchanged. [Status](status.md) identifies the candidate and which distribution checks actually ran. Do not advertise GitHub source installation on an old ref, or npm installation before a version resolves and works.

## Version and contents

`package.json` is the product manifest for the Git checkout, registry package and native release archive. Its version must agree with the release decision, tag and archive names. The [explicit semantic-release policy](../dev/release-policy.mjs) analyzes Conventional Commits: `fix` → patch, `feat` → minor, `!`/`BREAKING CHANGE` → major, including before 1.0. Review the actual decision on the final main history. The untagged `1.0.0` result in the disposable rule fixtures is not applicable to this tagged repository. Never run semantic-release with its default plugins.

From a **clean checkout of the reviewed commit**, run the [product and native checks](development.md). Prepare the files outside the repository:

```sh
sha=$(git rev-parse HEAD)
version=$(node -p 'require("./package.json").version')
assets=$(mktemp -d)
registry=$(mktemp -d)
python3.14 dev/package.py rehearse --commit "$sha" --version "$version" --license-id MIT
python3.14 dev/package.py build --commit "$sha" --version "$version" --license-id MIT --output-dir "$assets"
python3.14 dev/package.py verify --commit "$sha" --version "$version" --license-id MIT --output-dir "$assets"
source_dir=$(mktemp -d)
git archive -o "$registry/reviewed-source.tar" "$sha" &&
  tar -xf "$registry/reviewed-source.tar" -C "$source_dir" &&
  (cd "$source_dir" && npm pack --offline --ignore-scripts --pack-destination "$registry")
tar -tzf "$registry/elivibe-$version.tgz"
sha256sum "$assets"/* "$registry/elivibe-$version.tgz"
```

Keep the npm tarball **separate** from the GitHub asset directory. Inspect the actual `.tgz`, not just `npm pack --dry-run`: manifest and entry points, runtime, regular canonical skill, public documentation, license and notices. Compare the file bytes to the reviewed commit and the native archive; the standalone ZIP contains the very same skill. There must be no dependencies to install at runtime, lifecycle scripts to execute, credentials, raw transcripts, scratch, or development tree. The npm tarball is not interchangeable with the release `.tar.gz`. Preserve exact filenames and hashes for review. A new checkout, different squash SHA, dependency change or changed file requires checking the relevant evidence again.

## Destination gates — do not conflate them

1. **Rules and local artifacts.** Record rule fixture results, version decision, reviewed SHA, package identity, asset names and digests. Exercise an actual OMP install, use, removal and rollback in a clean consumer environment. A link to a checkout proves neither registry resolution nor a remote Git install.
2. **Hosted checks and Git source.** With owner authorization, push the reviewed branch and open a PR. Require protected main's product and native jobs on the current revision, Conventional Commit title, review and squash merge. Record the main SHA, CI URL and results. Exercise `omp plugin install github:taibenvenuti/elivibe#<full-reviewed-sha>` from a fresh consumer environment. Do not bypass an SSH, trust, namespace or protection failure. A branch diff is not evidence of an available ref.
3. **Preview (if requested).** The [rehearsal workflow](../.github/workflows/release-rehearsal.yml) is separate from publication. An authenticated dry run is a separate operation; it does not run prepare/publish hooks or publish bytes. The [privileged workflow](../.github/release-workflow.yml) is parked outside the workflows directory. Do not activate it, or enable implicit npm publication, as part of a package change.
4. **GitHub release.** With explicit authority for the exact main SHA and version, create the protected tag and draft release, attach **only** the verified ZIP, native archive and checksums, and verify downloads against the approved bytes. Publish only the approved draft. Download anonymously, verify and install again. Never move a tag or replace an existing asset to repair a release.
5. **npm.** Confirm that the maintainer controls the actual name and can use an [npm-supported publishing identity](https://docs.npmjs.com/trusted-publishers/). A 404, `npm whoami`, a local registry exercise and `npm pack` are not a name reservation or proof of rights. Publishing the reviewed tarball is an external write: after explicit approval, in the authorized publisher environment run `npm publish "$registry/elivibe-$version.tgz" --access public --registry=https://registry.npmjs.org`. Use normal registry authentication/2FA or an already configured trusted publisher; don't introduce tokens into the repo or weaken account requirements. Verify registry `dist.integrity` against the approved tarball, fetch the public version independently, then use `omp plugin install elivibe@<published-version>` in a fresh environment and exercise the first command. Update [installation](installation.md), [compatibility](compatibility.md) and [status](status.md) only after the corresponding observations.

If any operation fails, inspect the remote tag, release, exact asset digests and registry version before retrying. A published npm name/version cannot be reused for different bytes. A GitHub release does not publish to npm. Neither destination grants marketplace acceptance. Keep credentials, private research and raw transcripts out of all destinations.
