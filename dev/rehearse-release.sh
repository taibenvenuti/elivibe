#!/bin/sh
set -eu

fail() { printf '%s\n' "$*" >&2; exit 1; }
valid_version() {
    case "$1" in ''|*[!0-9.]*) return 1 ;; esac
    printf '%s\n' "$1" | grep -Exq '(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)'
}

[ "$#" -eq 3 ] || fail 'Usage: sh dev/rehearse-release.sh published TAG|candidate SHA EMPTY_OUTPUT_DIR'
mode=$1
ref=$2
output=$(realpath -- "$3")
[ -d "$output" ] && [ -z "$(ls -A -- "$output")" ] || fail 'Use an existing empty output directory'
export GIT_NO_REPLACE_OBJECTS=1
root=$(git rev-parse --show-toplevel)
cd "$root"
[ "$(git rev-parse --is-shallow-repository)" = false ] || fail 'Fetch full history and all tags first'
git rev-parse --verify -q 'refs/tags/v1.0.0^{tag}' >/dev/null || fail 'Fetch all release tags first'

case "$mode" in
  published)
    if [ -z "$ref" ]; then
        refs=$(git for-each-ref --merged=HEAD --sort=-version:refname \
            --format='%(objecttype) %(refname:lstrip=2)' refs/tags)
        ref=$(printf '%s\n' "$refs" |
            awk '$1 == "tag" && $2 ~ /^v(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)$/ { print $2; exit }')
    fi
    version=${ref#v}
    [ "$ref" = "v$version" ] && valid_version "$version" || fail 'Expected a published tag vX.Y.Z'
    git rev-parse --verify -q "refs/tags/$ref^{tag}" >/dev/null || fail 'Expected an annotated release tag'
    sha=$(git rev-parse --verify "refs/tags/$ref^{commit}")
    ;;
  candidate)
    case "$ref" in ''|*[!0-9a-f]*) fail 'Expected the reviewed full lowercase commit SHA' ;; esac
    [ "${#ref}" -eq 40 ] || fail 'Expected the reviewed full lowercase commit SHA'
    sha=$(git rev-parse --verify "$ref^{commit}")
    [ "$ref" = "$sha" ] || fail 'Expected a commit SHA, not a tag object'
    ;;
  *) fail 'Select published or candidate explicitly' ;;
esac

scratch=$(mktemp -d)
trap 'rm -rf -- "$scratch"' EXIT
mkdir "$scratch/source"
# npm pack records extracted modes. Fix both masks inside the private build directory.
git -c tar.umask=0022 archive --format=tar -o "$scratch/source.tar" "$sha"
(umask 022; tar -xf "$scratch/source.tar" -C "$scratch/source")
source=$scratch/source
builder=$source/dev/package.py
manifest_version=$(cd "$source" && node -p 'require("./package.json").version')
if [ "$mode:$ref" = published:v0.1.0 ]; then
    # Bootstrap had no public npm manifest; reproduce its GitHub assets without --bootstrap.
    builder=$source/tools/package.py
else
    valid_version "$manifest_version" || fail 'Expected a stable manifest version X.Y.Z'
    if [ "$mode" = published ]; then
        [ "$version" = "$manifest_version" ] || fail 'Tag and tagged manifest versions differ'
    else
        version=$manifest_version
        if git show-ref --verify --quiet "refs/tags/v$version"; then
            fail "v$version already exists; use published mode for that tag, not candidate mode"
        fi
    fi
    package_manager=$(cd "$source" && node -p 'require("./package.json").packageManager')
    [ "$package_manager" = "npm@$(npm --version)" ] || fail "Use the committed package manager: $package_manager"
fi

printf '%s: v%s from %s\n' "$mode" "$version" "$sha"
mkdir "$output/github"
for command in rehearse build verify; do
    set -- --source-root "$root" --version "$version" --commit "$sha" --license-id MIT
    if [ "$command" != rehearse ]; then set -- "$@" --output-dir "$output/github"; fi
    python3.14 "$builder" "$command" "$@"
done
sha256sum "$output/github/"*

if [ "$mode:$ref" != published:v0.1.0 ]; then
    touch "$scratch/user.npmrc" "$scratch/global.npmrc"
    (cd "$source" && npm pack --offline --ignore-scripts --cache "$scratch/npm-cache" \
        --userconfig "$scratch/user.npmrc" --globalconfig "$scratch/global.npmrc" --pack-destination "$output")
    sha256sum "$output/elivibe-$version.tgz"
fi
