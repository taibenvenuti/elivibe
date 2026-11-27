# Install, update, roll back, or remove

Choose the host you already use. The plugin paths below need an already working host and its usual model access, but no eliVibe account, separate runtime, build, or manual clone. Install **one** copy per host: native plugin **or** standalone skill. If you already have a copy, [update or remove it](#update-roll-back-or-uninstall) rather than adding a second one.

## Codex

For Codex and Claude Code, check the [release tags](https://github.com/taibenvenuti/elivibe/tags) before copying. If `v1.1.0` is not listed, use the GitHub preview: run `export ELIVIBE_REF=feat/cross-harness-skills` in the same shell. For the released tag, leave `ELIVIBE_REF` unset. Use a release tag for a stable installation, not a moving preview branch. You can also use a reviewed [standalone copy](#standalone-skill).

```sh
codex plugin marketplace add "taibenvenuti/elivibe@${ELIVIBE_REF:-v1.1.0}" &&
  codex plugin add elivibe@elivibe
```

Open a fresh session in that Codex profile. In the `$` picker, choose **elivibe (elivibe)**; the inserted token is `$elivibe:elivibe`. Use it in [your first explanation](#try-your-first-explanation).

## Claude Code

Use the same GitHub ref selection described [above](#codex). From your project directory:

```sh
claude plugin marketplace add "taibenvenuti/elivibe#${ELIVIBE_REF:-v1.1.0}" --scope local &&
  claude plugin install elivibe@elivibe-marketplace --scope local
```

The `local` scope applies to this project on your machine (`.claude/settings.local.json`), not your shared project settings or other projects. Use a **branch or tag** in the GitHub shorthand, not a full commit SHA. Open a fresh session in the same project and use `/elivibe:elivibe` for [your first explanation](#try-your-first-explanation).

## Oh My Pi (OMP)

```sh
omp plugin install elivibe@1.0.0
```

This is the published [npm package](https://www.npmjs.com/package/elivibe/v/1.0.0). If replacing a v0.1.0 link, [migrate it first](#move-from-a-v010-linked-install). Open a new OMP session and use `/elivibe` for [your first explanation](#try-your-first-explanation).

### Try the published release

For the same stable [v1.0.0](https://github.com/taibenvenuti/elivibe/releases/tag/v1.0.0) adapter from GitHub instead of npm, run this in your shell with OMP 19.2.1:

```sh
omp plugin install github:taibenvenuti/elivibe#v1.0.0
```

[Check the installation](#check-the-installation) before first use. For the older release itself, use the [tagged v0.1.0 guide](https://github.com/taibenvenuti/elivibe/blob/v0.1.0/docs/installation.md).

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

1. In your **shell**, run `omp plugin list --json`. Look for exactly one enabled `elivibe` with the expected version and path. The list does **not** identify the source: links, npm and GitHub can all appear in the `npm` group. Keep your install command and pin. Run `omp skill list --json` from the project root; move any standalone duplicate outside discovery to keep it for rollback.
2. In a **new interactive OMP session** in that profile and project, enter `/elivibe status` and `/elivibe help`. With default settings, expect `manual` mode and usage for `more` and focused questions. `/elivibe status` checks adapter settings, not the installed version. These expectations do not apply to a standalone install or the v0.1.0 adapter.

Before updating, look at `dependencies.elivibe` in the **plugin manager's** `package.json` (above `node_modules` in the listed path), not the installed plugin's manifest. In the tested installs:

| Source | What identifies it |
|---|---|
| npm | A version or range such as `1.0.0` or `^1.0.0`. The listing gives the version actually installed. |
| GitHub | A value such as `github:taibenvenuti/elivibe#v1.0.0`; keep this ref separately from the version shown in the listing. |
| Linked directory | No dependency entry **and** the listed path is a symlink. On Linux/WSL, `readlink -f -- "/path/from/the/listing"` gives the actual directory to keep. |

If the evidence doesn't match one of these cases, don't force a reinstall over it.

A profile is not a sandbox. Use the [native smoke procedure](development.md#native-omp-smoke) for contributor checks.

## Try your first explanation

In a fresh interactive session in the intended project, paste this as a normal chat message. Wait for the **assistant's handoff** before invoking the installed skill or plugin:

```text
Return a short technical handoff for a fictional API that stages an inventory batch and activates it in one database transaction. State what that guarantees and one failure case still untested. Don't use tools, edit files, or claim you ran checks.
```

| Installation | Ask a specific question in the same session |
|---|---|
| Codex plugin | Select **elivibe (elivibe)** in the `$` picker, then send `$elivibe:elivibe Why does the transaction matter?` |
| Codex standalone | `$elivibe Why does the transaction matter?` |
| Claude Code plugin | `/elivibe:elivibe Why does the transaction matter?` |
| Claude Code standalone | `/elivibe Why does the transaction matter?` |
| OMP plugin | `/elivibe Why does the transaction matter?` (or `/elivibe` for the whole handoff) |
| OMP standalone | `/skill:elivibe Why does the transaction matter?` (requires OMP skill commands enabled) |

The explanation should be distinct from the unchanged handoff, not another verification. To go deeper, ask an ordinary follow-up: “If two batches are activated at once, what can't we conclude from this report?” Then continue working normally, for example: “Write one acceptance criterion for concurrent activation. Return only the criterion.”

OMP's `/elivibe more` is an alternative when the preceding explanation **and its original handoff** are still available. If the original is gone, use a self-contained question, such as `/elivibe explain The fictional handoff says staging and activation occur in one database transaction; it doesn't report a concurrent activation test. Why does that distinction matter?` Then ask another focused question in the same conversation; `more` does not retrieve the old handoff. See [OMP modes and commands](../README.md#omp-commands).

These are ordinary host turns. Use only material you can share through your active host and model setup; see [what reaches the model](privacy.md).

## Move from a v0.1.0 linked install

1. In the profile that owns the existing link, [identify its source](#check-the-installation) and record the resolved absolute path to the verified v0.1.0 extracted `elivibe-omp` directory. Do not overwrite it.
2. Close the old session. In the same profile, unregister the old link with `omp plugin uninstall elivibe` before installing from your [chosen source](#omp-installation-sources). Don't use `--force` to move away from a link to a locally edited path. This leaves the old files available for rollback. Open a fresh session to check the new source, version and commands.
3. Use `/elivibe status` and set the mode/depth you want. `depth adaptive` still works as `depth auto`. `/elivibe model`, `/elivibe judge`, `/elivibe consent`, and `/elivibe judge-consent` now show a migration notice instead of setting anything. Old route grants don't carry over; there is no independent model or separate judge. Select the ordinary model through OMP itself. Manual and Light no longer isolate the report; the ordinary conversation can include more context. Check the [new disclosure boundary](privacy.md) before using v1.0.0.

A resumed branch keeps its saved mode and depth. In particular, a saved **Light** setting now asks the ordinary model to teach during a coding task, even without an old route grant. For explanations only on request, select `/elivibe manual` before the next task. A new branch without saved preferences defaults to Manual.

## Update, roll back, or uninstall

For normal use, choose a release tag. A moving preview branch can contain different files under the **same** plugin version: a marketplace refresh or “already at the latest version” is not proof that cached plugin files match a newer commit. To review immutable skill bytes independently, use the [standalone snapshot](#standalone-skill).

### Codex plugin

- **Update:** for the same Git marketplace ref, run `codex plugin marketplace upgrade elivibe` and `codex plugin add elivibe@elivibe` again. A pinned tag won't advance to another tag. To change pins or roll back, remove the plugin and marketplace as below, then rerun the install commands with the desired named ref. For a filesystem marketplace, use a reviewed source directory and re-add the plugin; the Git-marketplace upgrade command doesn't apply.
- **Disable for one session:** start Codex with `codex -c 'plugins.elivibe@elivibe.enabled=false'`. Start it normally again to use the installed plugin; this doesn't change the persisted registration.
- **Remove:** run `codex plugin remove elivibe@elivibe`, then `codex plugin marketplace remove elivibe` if you no longer want the marketplace. These operate on the current Codex profile. Start a fresh session after changing the install.

### Claude Code plugin

- **Update:** from the same project, run `claude plugin marketplace update elivibe-marketplace`, then `claude plugin update elivibe@elivibe-marketplace --scope local`. A pinned tag won't advance to another tag. To switch pins or roll back, remove the plugin and marketplace as below, then rerun the install commands with the desired named ref.
- **Same-version preview:** if the GitHub branch moved but the CLI says “already at the latest version,” the refreshed marketplace and the installed plugin can be at different commits. After the marketplace update, run `claude plugin uninstall elivibe@elivibe-marketplace --scope local` and then `claude plugin install elivibe@elivibe-marketplace --scope local` in the same project. This refreshed the cached files on Claude Code 2.1.291 without removing the marketplace or unrelated skills. Start a fresh session; don't clear your global cache.
- **Disable or re-enable:** run `claude plugin disable elivibe@elivibe-marketplace --scope local` or `claude plugin enable elivibe@elivibe-marketplace --scope local`.
- **Remove:** run `claude plugin uninstall elivibe@elivibe-marketplace --scope local`, then `claude plugin marketplace remove elivibe-marketplace --scope local` if you no longer want the marketplace. Use the scope in which you installed it; the examples use `local`, not shared `project` or all-projects `user`. Start a fresh session after changing the install.

### OMP plugin

- **Registry source only:** record your current version before switching. With a confirmed registry install, run `omp plugin install elivibe@VERSION --force`, replacing `VERSION` with the exact available npm version. Use the same command with the previous version to roll back. This is a pinned reinstall tested with registry fixtures, not `omp plugin upgrade` or a claim that another public version is available. Never force over a GitHub install, local link, or unknown source.
- **GitHub source:** record the installed tag or full SHA. Uninstall the current registration, then install from the next verified tag or full SHA. To roll back, reinstall from the previous verified ref. Keep the previous pin before switching; don't substitute a moving branch.
- **Checkout or offline archive:** keep the previous reviewed directory. Unregister the current link and `omp plugin link` the new reviewed directory, or link the previous directory to roll back. Don't overwrite a linked path or use `omp plugin upgrade` for a local link. A rollback to v0.1.0 still has its old side-request paths.
- **Remove:** `omp plugin uninstall elivibe` in the same profile. This unregisters the adapter and bundled skill without deleting a linked checkout or extracted archive. Restore a former standalone copy only if you want skill-only use.

Close the old OMP session before switching or removing. [Check the resulting version and registration](#check-the-installation), then open a fresh session.

## Standalone skill

### Standalone ZIP

If you have the prepared `elivibe-1.1.0.zip` locally, use it with its matching `SHA256SUMS`; this is not a claim that the asset is published. From the download directory on Linux/WSL, run `grep -F '  elivibe-1.1.0.zip' SHA256SUMS | sha256sum -c -` and proceed only on `elivibe-1.1.0.zip: OK`. Extract into a fresh directory **outside** skill discovery and use its `elivibe/` folder. Leave the ZIP's root `README.md` and `LICENSE` in staging; keep the license with any redistribution.

If you don't have the ZIP, use a **GitHub source archive**: download [the signed product snapshot](https://github.com/taibenvenuti/elivibe/archive/d038ddfefe0e39d45cb0f5df37da3cbacf45f511.zip) or use **Code → Download ZIP** on the reviewed branch or tag. Extract outside skill discovery and use its `skills/elivibe/` folder. No plugin marketplace or clone is needed. Keep the ref or snapshot you downloaded so you can reinstall the same files.

For the older OMP-only release, follow the [v1.0.0 ZIP instructions](https://github.com/taibenvenuti/elivibe/blob/v1.0.0/docs/installation.md#standalone-zip) instead. **Do not install that ZIP in Codex:** it lacks `agents/openai.yaml`, the file that keeps Codex invocation explicit-only.

### Copy into one project

From the project root, choose the destination for your host:

| Host | Project skill directory | New-session invocation |
|---|---|---|
| Codex | `.agents/skills/elivibe/` | `$elivibe` (the standalone option in the `$` picker) |
| Claude Code | `.claude/skills/elivibe/` | `/elivibe` |
| OMP | `.agents/skills/elivibe/` | `/skill:elivibe` (skill commands enabled) |

Copy only the whole `elivibe/` skill folder from the prepared ZIP or GitHub snapshot, including `SKILL.md` and `agents/openai.yaml`. This recipe refuses to install a source missing either file. Set `source` to the extracted skill folder's absolute path and use `.claude/skills` instead of `.agents/skills` for Claude Code:

```sh
source=/absolute/path/to/extracted/elivibe
destination=.agents/skills
test -f "$source/SKILL.md" &&
  test -f "$source/agents/openai.yaml" &&
  mkdir -p "$destination" &&
  mkdir "$destination/elivibe" &&
  cp -R "$source/." "$destination/elivibe/"
```

The second `mkdir` stops if that destination already exists. Check other discovery paths before adding a copy: Codex and OMP can share `.agents/skills/`, and OMP can also discover project `.claude/skills/` and Claude plugin resources. Different versions in those locations can produce a second, namespaced entry. Open a fresh session from this project and [try an explanation](#try-your-first-explanation); in OMP, `omp skill list --json` shows the path and source of each discovered skill.

To disable or remove the standalone skill, move just the copied `elivibe/` directory outside every skill discovery path or delete just that copy. To update, keep the previous copy outside discovery and install the new folder; reverse that swap to roll back or restore it. Start a fresh session after each change. None of these steps requires editing any other skill.

## Troubleshooting

- **Command missing or duplicated:** check the active profile and project, and use the invocation matching your installation. Start a fresh session after changing a registration or file. For OMP, check `omp plugin list --json` and `omp skill list --json`; also check that standalone skill commands are enabled.
- **No handoff or explanation to build on:** use the same session or include the relevant non-sensitive facts with a specific question. Do not expect `/elivibe more` to retrieve a missing OMP source, or any host to fetch a report from another conversation. OMP's Manual and Off modes don't add explanations automatically.
- **Unexpected version or checksum:** stop. Compare the recorded source, verified bundle, and installed path; restore the previous verified copy if needed.
- **A question contains an `@file` or `^model` mention:** OMP can expand these before sending the request. eliVibe refuses expanding mentions instead of reading a file or changing the request. Describe the file or model by name without the mention prefix, or paste a short non-sensitive excerpt.
