# Install, update, roll back, or remove

## Try the published release

[v1.0.0](https://github.com/taibenvenuti/elivibe/releases/tag/v1.0.0) is the stable release. With OMP 19.2.1, install the native plugin from your shell:

```sh
omp plugin install github:taibenvenuti/elivibe#v1.0.0
```

To install from [npm](https://www.npmjs.com/package/elivibe/v/1.0.0) instead, run `omp plugin install elivibe@1.0.0`.

The plugin includes the skill; install only one copy. [Check the installation](#check-the-installation) and then [try your first explanation](#try-your-first-explanation). If replacing a v0.1.0 link, [migrate it first](#move-from-a-v010-linked-install). For the old release itself, use the [tagged v0.1.0 guide](https://github.com/taibenvenuti/elivibe/blob/v0.1.0/docs/installation.md).

### Standalone ZIP

For skill-only use, you need OMP, an already configured model and an unzip tool, but no plugin or build tools.

1. Download [elivibe-1.0.0.zip](https://github.com/taibenvenuti/elivibe/releases/download/v1.0.0/elivibe-1.0.0.zip) and [SHA256SUMS](https://github.com/taibenvenuti/elivibe/releases/download/v1.0.0/SHA256SUMS) from the same release into one directory. From that directory on Linux/WSL:

   ```sh
   grep -F '  elivibe-1.0.0.zip' SHA256SUMS | sha256sum -c -
   ```

   Continue only if this prints `elivibe-1.0.0.zip: OK`. A checksum checks that the download matches the trusted manifest; it doesn't establish trust in a manifest from an unknown source.
2. Extract the ZIP into a fresh directory. In the project where you use OMP, [copy just `elivibe/SKILL.md` into the project's skill directory](#standalone-skill).
3. Start OMP from that project with skill commands enabled, then [try the example handoff](#try-your-first-explanation) using `/skill:elivibe`.

## OMP installation sources

Use OMP 19.2.1 in the intended profile. Pick **one** source. A GitHub tag, an npm package and a release archive become available independently; see [distribution status](status.md).

| Source | OMP command | When to run |
|---|---|---|
| GitHub release tag | `omp plugin install github:taibenvenuti/elivibe#v1.0.0` | Verified on OMP 19.2.1, Linux x64. The signed annotated tag peels to `caf8c089cad3a67d242d0eaa15329fca117a66a8`. |
| Offline native archive | `omp plugin link /absolute/path/to/extracted/elivibe-omp` | [Download, verify and extract the release archive first](#verify-and-link-an-offline-archive). Verified on OMP 19.2.1, Linux x64. |
| Local checkout | `omp plugin link "$PWD"` | Run from the root of a clean, reviewed checkout. OMP loads the files directly: keep the directory intact and unchanged while linked. |
| [npm](https://www.npmjs.com/package/elivibe/v/1.0.0) | `omp plugin install elivibe@1.0.0` | Verified from the public registry on OMP 19.2.1, Linux x64. |

Consumers need a working OMP installation. Its standalone binary embeds the package-manager runtime; no Python, uv, separate Node or Bun install. The tested `github:` shorthand fetched an HTTPS archive from GitHub. By default OMP registers plugins in the active user plugin directory, which may be shared by profiles. If you already have eliVibe linked, [migrate the existing install](#move-from-a-v010-linked-install) rather than forcing a replacement.

## Verify and link an offline archive

Download [elivibe-omp-1.0.0.tar.gz](https://github.com/taibenvenuti/elivibe/releases/download/v1.0.0/elivibe-omp-1.0.0.tar.gz) and [SHA256SUMS](https://github.com/taibenvenuti/elivibe/releases/download/v1.0.0/SHA256SUMS) into the same directory. Set `version=1.0.0` and set `output` to that directory's absolute path. Verify before extraction (a mismatch means stop):

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

Keep the extracted directory intact while linked. Don't pass this tarball to `omp plugin link` or `omp plugin install`. If preparing archives for review, see the [release build instructions](release.md#version-and-contents).

## Check the installation

1. In your **shell**, run `omp plugin list --json`. Look for exactly one `elivibe` at version `1.0.0`; the list does **not** show the resolved GitHub SHA. Keep your original pinned command for rollback. Use `omp skill list --json` from the project root to check skill discovery. If you also have a standalone copy, move only that copy outside discovery to keep it for rollback.
2. In a **new interactive OMP session** in that profile and project, enter `/elivibe status` and `/elivibe help`. With default settings, expect `manual` mode and usage for `more` and focused questions. `/elivibe status` checks adapter settings, not the installed version. These expectations do not apply to a standalone install or the v0.1.0 adapter.

A profile is not a sandbox. Use the [native smoke procedure](development.md#native-omp-smoke) for contributor checks.

## Try your first explanation

In an idle interactive OMP session with a configured model, paste this as a normal chat message. Let OMP return the handoff as an **assistant reply** before invoking eliVibe:

```text
Return a short technical handoff for a fictional API that stages an inventory batch and activates it in one database transaction. State what that guarantees and one failure case still untested. Don't use tools, edit files, or claim you ran checks.
```

- **v1.0.0 native plugin:** enter `/elivibe` on its own.
- **Standalone skill:** enter `/skill:elivibe Why does the transaction matter?`. This needs OMP's skill commands enabled.

If OMP is still working and the command doesn't start a response, wait until the session is idle and try again. The explanation should be distinct from the unchanged handoff. The report is the source account, not independent verification. These are ordinary OMP turns; use only material you can share through your active OMP setup.

With the native plugin, follow up with `/elivibe more` or `/elivibe What wouldn't that transaction guarantee?`. For a future task, use `/elivibe light` to explain selectively or `/elivibe full` to request explanations with meaningful technical handoffs. The selected depth applies in both modes. See the [command table](../README.md#omp-commands).

## Move from a v0.1.0 linked install

1. In the profile that owns the existing link, use `omp plugin list --json` to record the current registration and keep the absolute path to the verified v0.1.0 extracted `elivibe-omp` directory. Do not overwrite it.
2. Close the old session. In the same profile, unregister the old link with `omp plugin uninstall elivibe` before installing from your [chosen source](#omp-installation-sources). Don't use `--force` to move away from a link to a locally edited path. This leaves the old files available for rollback. Open a fresh session to check the new source, version and commands.
3. Use `/elivibe status` and set the mode/depth you want. `depth adaptive` still works as `depth auto`. `/elivibe model`, `/elivibe judge`, `/elivibe consent`, and `/elivibe judge-consent` now show a migration notice instead of setting anything. Old route grants don't carry over; there is no independent model or separate judge. Select the ordinary model through OMP itself. Manual and Light no longer isolate the report; the ordinary conversation can include more context. Check the [new disclosure boundary](privacy.md) before using v1.0.0.

A resumed branch keeps its saved mode and depth. In particular, a saved **Light** setting now asks the ordinary model to teach during a coding task, even without an old route grant. For explanations only on request, select `/elivibe manual` before the next task. A new branch without saved preferences defaults to Manual.

## Update, roll back, or uninstall

- **GitHub source:** record the installed tag or full SHA. Uninstall the current registration, then install from the next verified tag or full SHA. To roll back, reinstall from the previous verified ref. Keep the previous pin before switching; don't substitute a moving branch.
- **Checkout or offline archive:** keep the previous reviewed directory. Unregister the current link and `omp plugin link` the new reviewed directory, or link the previous directory to roll back. Don't overwrite a linked path or use `omp plugin upgrade` for a local link. A rollback to v0.1.0 still has its old side-request paths.
- **Uninstall:** `omp plugin uninstall elivibe` in the same profile, then open a fresh session. This unregisters the adapter and bundled skill. An unlinked checkout or extracted archive is still yours to keep. Restore a former standalone copy only if you want skill-only use.

After updating or rolling back, [check the installed version and source](#check-the-installation) in a fresh session.

## Standalone skill

Use the extracted `elivibe/SKILL.md` from the verified ZIP, or the [canonical `skills/elivibe/SKILL.md`](../skills/elivibe/SKILL.md) from a reviewed checkout. Run this from your OMP project's root, replacing the source path:

```sh
mkdir -p .agents/skills &&
  mkdir .agents/skills/elivibe &&
  cp /absolute/path/to/elivibe/SKILL.md .agents/skills/elivibe/
```

The second `mkdir` stops if an installation already exists. Do not copy the skill beside a native install. From the project root, run `omp skill list --json`, then start a fresh session. Use `/skill:elivibe` with the report already in the conversation or with an explicit question. The v1.0.0 skill is not advertised for automatic model invocation; native modes require the plugin.

To update or roll back a skill-only install, save the old file outside discovery and replace only that installation's file. To remove it, remove your copied `SKILL.md` and its now-empty `elivibe` directory, then start a fresh session. If you redistribute the standalone file, include the copyright and [MIT license text](../LICENSE) outside the runtime skill directory.

## Troubleshooting

- **Command missing or duplicated:** in the shell, check the active profile with `omp plugin list --json` and skill discovery with `omp skill list --json`. Look for a broken package link, disabled skill discovery or skill commands, or a second copy. Restart OMP after changing a registration or file.
- **No explanation:** Manual and Off do not add one automatically; use `/elivibe <question>` or `/skill:elivibe`. For a report that's no longer in context, quote its relevant non-sensitive evidence; eliVibe does not retrieve it from another session. An output-only request or opt-out takes precedence over automatic explanation.
- **Unexpected version or checksum:** stop. Compare the intended version, verified bundle, and linked path; relink the previous verified archive if needed.
- **A question contains an `@file` or `^model` mention:** OMP can expand these before sending the request. eliVibe refuses expanding mentions instead of reading a file or changing the request. Describe the file or model by name without the mention prefix, or paste a short non-sensitive excerpt.
