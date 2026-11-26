# Install, update, roll back, or remove

## Start here

For an existing report, use `/skill:elivibe` in the ordinary Oh My Pi (OMP) conversation. With the native plugin, use `/elivibe full` **before** your next task to ask for both layers in the same answer. These paths use OMP's normal routing and protections, and an ordinary turn may send more conversation context than the report alone.

Manual is the safe idle default: it sends no extra eliVibe model request unless you explicitly request and authorize one. Manual explanations and Light automation are experimental and bypass ordinary OMP protection and provider hooks. A cloud route requires positive OMP proof that it bypasses both proxy layers; empty proxy environment variables aren't proof. The default TypeSafe Jev judge is usually unavailable, and a local explainer does not make the judge eligible. Read [privacy and controls](privacy.md) before using either side-request path.

The native plugin was exercised with synthetic responses on OMP 19.2.1 on Linux x64 (WSL2). No live-provider compatibility has been verified. See [compatibility](compatibility.md). No published bundle is linked here; build from source or install only the skill.

## Native source install

From the root of a clean checkout at a reviewed commit, use a POSIX shell on Linux/WSL with Git, `tar`, `sha256sum`, Python 3.14 and OMP 19.2.1 on `PATH`. Packaging uses only the Python standard library. These commands build and verify the local archives without publishing them:

```sh
version=0.1.0
commit=$(git rev-parse HEAD) &&
  output=$(mktemp -d) &&
  python3.14 tools/package.py build --output-dir "$output" --version "$version" --commit "$commit" &&
  python3.14 tools/package.py verify --output-dir "$output" --version "$version" --commit "$commit"
```

Only continue if verification succeeds. Perform [verification and linking](#verify-and-link-the-omp-archive) in the same shell. OMP loads the bundled TypeScript; installing an already-built bundle does not need Python, uv or a separate Node install.

## Verify and link the OMP archive

The source build already set `version` and `output`. If you're installing an already-built bundle from a trusted source, set them to its exact version and the absolute directory containing the archive and its trusted `SHA256SUMS`. A checksum detects a mismatch, but does not authenticate a download from an untrusted source. The commands use Linux `sha256sum` and `tar` and extract into a new directory.

```sh
archive="elivibe-omp-$version.tar.gz"
(
  cd "$output" &&
    awk -v name="$archive" '$2 == name {line=$0; found++} END {if (found == 1) print line; else exit 1}' SHA256SUMS |
    sha256sum -c -
) &&
  mkdir -p "$HOME/.local/share/elivibe" &&
  install_dir=$(mktemp -d "$HOME/.local/share/elivibe/install.XXXXXXXX") &&
  tar -xzf "$output/$archive" -C "$install_dir" &&
  omp plugin link "$install_dir/elivibe-omp"
```

The native archive contains the adapter, core, Jev transport, canonical skill, MIT license, OMP manifest and relative `skills` discovery link. Use an extractor that preserves the link. OMP links to the extracted directory, so keep it intact while it is registered.

By default `omp plugin link` registers the package in the active user plugin directory. Profiles that share this directory share the registration. A profile isn't a sandbox; use [isolated native smoke](development.md#native-omp-smoke) to test without touching your normal profile or sending live requests.

Start a fresh OMP session in the intended profile and your project. `omp plugin list --json` should list `elivibe` at the expected version. In a new session, `/elivibe status` should report `manual`, `/elivibe model` should report `auto`, and `/skill:elivibe` should be offered. Those checks don't authorize a side request.

If you had a standalone copy, move only that copy outside skill discovery and keep it for rollback. Don't delete a locally edited copy, the canonical file in this checkout, or another skill. The native plugin supplies `/skill:elivibe` without a second installation.

## Update, roll back, or uninstall

- **Update:** verify the new artifact, extract it to a new directory and link it as above using the same profile. Keep the previous verified directory until the new version works. Open a fresh session and check the registered version and commands. Don't use `omp plugin upgrade` for a locally linked package.
- **Roll back:** `omp plugin link /absolute/path/to/previous/elivibe-omp`, then open a fresh session and check the previous version. If a failed installation left no registration, relink the known-good extracted directory. Don't overwrite a linked directory in place.
- **Uninstall:** `omp plugin uninstall elivibe` in the same profile, then start a fresh session. This unregisters the adapter and bundled skill; it doesn't delete your extracted copy or remove unrelated registrations. If you want skill-only use, restore your former standalone copy after uninstalling. Retire extracted directories only once no profile links to them.

## Standalone skill

This checkout already discovers the [canonical skill](../skill/elivibe/SKILL.md). To install it in a different OMP project, run the following from that project's root, replacing the source path. A verified skill ZIP can supply the same `elivibe/SKILL.md`; verify its entry in the trusted `SHA256SUMS` and extract it to a fresh directory first. Only one Markdown file goes into the skill directory; Python, Node and the plugin are not needed.

```sh
mkdir -p .agents/skills &&
  mkdir .agents/skills/elivibe &&
  cp /path/to/checkout/skill/elivibe/SKILL.md .agents/skills/elivibe/
```

If you redistribute the standalone file, include the project's copyright and [MIT license text](../LICENSE) and any applicable notices alongside it, outside the runtime skill directory. An SPDX identifier alone is not the license text.

`mkdir` stops the installation if a directory or symlink is already there. Run `omp skill list --json` from the project root and start a fresh session. Use `/skill:elivibe Explain why that check was insufficient.` after a report, or invoke it with a coding task to request both layers. This is an ordinary OMP turn, not isolated inference. OMP advertises skills to the active model, which can miss or overselect them; use explicit invocation when it matters.

To update or roll back a skill-only install, save the old file outside discovery and replace only that installation's file with the reviewed new or previous version. To remove it, remove your copied `SKILL.md` and its now-empty `elivibe` directory. In this checkout, no copy was needed: remove or move only the discovery symlink if you want to disable discovery locally, not its target. Remove any reminder you personally added and start a fresh session.

## Troubleshooting

- **Command missing or duplicated:** check the profile and `omp plugin list --json`; check `omp skill list --json` for the source of the skill, a second copy, disabled discovery or a missing archive symlink. Restart OMP after registry or file changes. Don't delete another registration to make this one work.
- **No model or side request refused:** check `/elivibe status` and `/elivibe model`. A successful install doesn't make a model or route eligible. If the active route or the separate judge is refused, use `/skill:elivibe` for the current report or `/elivibe full` before the next task, subject to your ordinary OMP policy. See [authorization and refusals](privacy.md#approvals-and-refusals).
- **Checksum, link, or version mismatch:** stop. Verify the expected commit/version and bundle, or relink the last reviewed version. Do not bypass the checksum or register an uncertain directory.
