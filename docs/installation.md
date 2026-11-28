# Install, update, roll back, or remove

This guide installs **eliVibe v1.1.0**. Start with the host you already use and its usual model access. No separate eliVibe account, build, or manual clone is needed. Install **one** copy per host: a plugin or the [standalone skill](#standalone-skill). If you already have a copy, [update or remove it](#update-roll-back-or-uninstall) instead of adding a second one.

The GitHub tag, release downloads, and npm version become available separately. Check the [maintained release status](https://github.com/taibenvenuti/elivibe/blob/main/docs/status.md) for availability and provenance. If a route isn't available, use another available route for v1.1.0 or wait. For OMP only, you can instead follow the [v1.0.0 guide](https://github.com/taibenvenuti/elivibe/blob/v1.0.0/docs/installation.md) for that older release.

## Codex

From your shell:

```sh
codex plugin marketplace add taibenvenuti/elivibe@v1.1.0 &&
  codex plugin add elivibe@elivibe
```

Open a fresh session in that Codex profile. In the `$` picker, choose **elivibe (elivibe)**; the inserted token is `$elivibe:elivibe`. Use it in [your first explanation](#try-your-first-explanation).

## Claude Code

From your project directory:

```sh
claude plugin marketplace add 'taibenvenuti/elivibe#v1.1.0' --scope local &&
  claude plugin install elivibe@elivibe-marketplace --scope local
```

The `local` scope applies to this project on your machine (`.claude/settings.local.json`), not your shared project settings or other projects. Open a fresh session in the same project and use `/elivibe:elivibe` for [your first explanation](#try-your-first-explanation).

## Oh My Pi (OMP)

```sh
omp plugin install elivibe@1.1.0
```

This requests the exact [npm version](https://www.npmjs.com/package/elivibe/v/1.1.0). If you're replacing an existing install, [check its source first](#check-the-installation) and [migrate a v0.1.0 link](#move-from-a-v010-linked-install) before installing. Open a new OMP session and use `/elivibe` for [your first explanation](#try-your-first-explanation).

### GitHub instead of npm

To install the same version from the GitHub tag instead of npm:

```sh
omp plugin install 'github:taibenvenuti/elivibe#v1.1.0'
```

If neither online route works, you can [verify and link the offline archive](#verify-and-link-an-offline-archive). [Check the installation](#check-the-installation) before first use.

## OMP installation sources

Use OMP 19.2.1 in the intended profile and pick **one** source.

| Source | How to install |
|---|---|
| npm | `omp plugin install elivibe@1.1.0` |
| GitHub release tag | `omp plugin install 'github:taibenvenuti/elivibe#v1.1.0'` |
| Offline native archive | [Verify and extract the release archive, then link its `elivibe-omp/` directory](#verify-and-link-an-offline-archive). |

OMP's standalone binary embeds the package-manager runtime; no separate Python, uv, Node or Bun installation is needed. OMP can share its user plugin directory across profiles. Check the active profile and installation path before changing an existing registration.

## Verify and link an offline archive

Download [elivibe-omp-1.1.0.tar.gz](https://github.com/taibenvenuti/elivibe/releases/download/v1.1.0/elivibe-omp-1.1.0.tar.gz) and its matching [SHA256SUMS](https://github.com/taibenvenuti/elivibe/releases/download/v1.1.0/SHA256SUMS). Keep both files together, including if you transfer them to an offline machine. On Linux/WSL, open a shell in that download directory and run:

```sh
checksum=$(awk '$2 == "elivibe-omp-1.1.0.tar.gz" { line = $0; count++ } END { if (count != 1) exit 1; print line }' SHA256SUMS) &&
  printf '%s\n' "$checksum" | sha256sum --check --strict - &&
  mkdir -p "$HOME/.local/share/elivibe" &&
  install_dir=$(mktemp -d "$HOME/.local/share/elivibe/install.XXXXXXXX") &&
  tar -xzf elivibe-omp-1.1.0.tar.gz -C "$install_dir" &&
  omp plugin link "$install_dir/elivibe-omp"
```

If the manifest entry is missing, duplicated or doesn't verify, stop before extraction. Only link the extracted `elivibe-omp/` directory, never the tarball itself. Record the absolute path and keep it intact while linked; OMP loads directly from it. Keep the tarball and checksum for offline reinstall or rollback. To remove it, [unregister the plugin first](#omp-plugin), then delete just this extracted directory if you no longer need it.

## Check the installation

1. In your **shell**, run `omp plugin list --json`. Look for exactly one enabled `elivibe` with the expected version and path. The list does **not** identify the source: links, npm and GitHub can all appear in the `npm` group. Keep your install command and pin. Run `omp skill list --json` from the project root; move any standalone duplicate outside discovery to keep it for rollback.
2. In a **new interactive OMP session** in that profile and project, enter `/elivibe status` and `/elivibe help`. With default settings, expect `manual` mode and usage for `more` and focused questions. `/elivibe status` checks adapter settings, not the installed version. These expectations do not apply to a standalone install or the v0.1.0 adapter.

Before updating, look at `dependencies.elivibe` in the **plugin manager's** `package.json` (above `node_modules` in the listed path), not the installed plugin's manifest. In the tested installs:

| Source | What identifies it |
|---|---|
| npm | A version or range such as `1.1.0` or `^1.1.0`. The listing gives the version actually installed. |
| GitHub | A value such as `github:taibenvenuti/elivibe#v1.1.0`; keep this ref separately from the version shown in the listing. |
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
3. Use `/elivibe status` and set the mode/depth you want. `depth adaptive` still works as `depth auto`. `/elivibe model`, `/elivibe judge`, `/elivibe consent`, and `/elivibe judge-consent` now show a migration notice instead of setting anything. Old route grants don't carry over; there is no independent model or separate judge. Select the ordinary model through OMP itself. Manual and Light no longer isolate the report; the ordinary conversation can include more context. Check the [disclosure boundary](privacy.md) before using the new install.

A resumed branch keeps its saved mode and depth. In particular, a saved **Light** setting now asks the ordinary model to teach during a coding task, even without an old route grant. For explanations only on request, select `/elivibe manual` before the next task. A new branch without saved preferences defaults to Manual.

## Update, roll back, or uninstall

Record the installed version, source, and scope before changing anything. Change the pin deliberately to update or roll back; a marketplace refresh alone doesn't advance a pinned tag. Use the same profile or project where you installed eliVibe, and leave unrelated registrations and caches alone.

### Codex plugin

- **Update or roll back:** remove the plugin and its marketplace registration as below, then rerun the [Codex install commands](#codex) with the exact tag named in the target release's guide.
- **Disable for one session:** start Codex with `codex -c 'plugins.elivibe@elivibe.enabled=false'`. Start it normally again to use the installed plugin; this doesn't change the persisted registration.
- **Remove:** run `codex plugin remove elivibe@elivibe`, then `codex plugin marketplace remove elivibe` if you no longer want the marketplace. These operate on the current Codex profile. Start a fresh session after changing the install.

### Claude Code plugin

- **Update or roll back:** remove the plugin and its marketplace registration as below, then rerun the [Claude Code install commands](#claude-code) with the exact tag named in the target release's guide.
- **Troubleshooting a stale same-version install:** if you've corrected or refreshed your marketplace registration but Claude Code still loads the old cached files and reports “already at the latest version,” refresh the marketplace with `claude plugin marketplace update elivibe-marketplace`. In the same project, run `claude plugin uninstall elivibe@elivibe-marketplace --scope local`, then `claude plugin install elivibe@elivibe-marketplace --scope local`. Use the original installation scope if it wasn't `local`. Start a fresh session. This reinstalls just eliVibe; don't reset your global cache.
- **Disable or re-enable:** run `claude plugin disable elivibe@elivibe-marketplace --scope local` or `claude plugin enable elivibe@elivibe-marketplace --scope local`.
- **Remove:** run `claude plugin uninstall elivibe@elivibe-marketplace --scope local`, then `claude plugin marketplace remove elivibe-marketplace --scope local` if you no longer want the marketplace. Use the scope in which you installed it; the examples use `local`, not shared `project` or all-projects `user`. Start a fresh session after changing the install.

### OMP plugin

- **Registry source only:** after confirming this is an npm install, run `omp plugin install elivibe@1.1.0 --force` to switch to v1.1.0. To roll back, use the same command with the exact previous npm version. Never force over a GitHub install, local link, or unknown source.
- **GitHub source:** record the installed tag or commit. Uninstall the current registration and install from the exact tag in the target release's guide. To roll back, reinstall the previous verified ref.
- **Linked directory:** keep the previous verified directory outside skill discovery. Unregister the current link and `omp plugin link` the new extracted directory, or link the previous directory to roll back. Don't overwrite a linked path or use `omp plugin upgrade` on a link. A rollback to v0.1.0 restores its old side-request behavior.
- **Remove:** run `omp plugin uninstall elivibe` in the profile that owns the registration. Confirm it's gone with `omp plugin list --json`. Unregistering a link doesn't delete its target: keep it for rollback or delete just that directory after confirming nothing else uses it. Restore a former standalone copy only if you want skill-only use.

Close the old OMP session before switching or removing. [Check the resulting version and registration](#check-the-installation), then open a fresh session.

## Standalone skill

### Standalone ZIP

Download [elivibe-1.1.0.zip](https://github.com/taibenvenuti/elivibe/releases/download/v1.1.0/elivibe-1.1.0.zip) and its matching [SHA256SUMS](https://github.com/taibenvenuti/elivibe/releases/download/v1.1.0/SHA256SUMS). Keep both files for reinstall. On Linux/WSL, run this from the download directory, outside skill discovery:

```sh
checksum=$(awk '$2 == "elivibe-1.1.0.zip" { line = $0; count++ } END { if (count != 1) exit 1; print line }' SHA256SUMS) &&
  printf '%s\n' "$checksum" | sha256sum --check --strict - &&
  staging=$(mktemp -d "$PWD/elivibe-1.1.0.XXXXXXXX") &&
  unzip -q elivibe-1.1.0.zip -d "$staging" &&
  printf 'Skill source: %s/elivibe\n' "$staging"
```

Stop if the manifest entry is missing, duplicated or doesn't verify. Use only the extracted `elivibe/` folder as the skill source. Leave the ZIP's root `README.md` and `LICENSE` in staging, and include the license if you redistribute the skill.

**If the release ZIP isn't available:** use the pinned plugin path for your host, or, if the tag is available, download the [v1.1.0 GitHub source archive](https://github.com/taibenvenuti/elivibe/archive/refs/tags/v1.1.0.zip). Extract it outside skill discovery and use `skills/elivibe/` inside the extracted source tree. The release `SHA256SUMS` does not cover this GitHub-generated archive; if you require a checksum-verified bundle, wait for the release ZIP and its manifest. Neither source needs a clone or build.

For the older OMP-only release, follow the [v1.0.0 ZIP instructions](https://github.com/taibenvenuti/elivibe/blob/v1.0.0/docs/installation.md#standalone-zip). **Do not install that ZIP in Codex:** it lacks `agents/openai.yaml`, the file that keeps Codex invocation explicit-only.

### Copy into one project

From the project root, choose the destination for your host:

| Host | Project skill directory | New-session invocation |
|---|---|---|
| Codex | `.agents/skills/elivibe/` | `$elivibe` (the standalone option in the `$` picker) |
| Claude Code | `.claude/skills/elivibe/` | `/elivibe` |
| OMP | `.agents/skills/elivibe/` | `/skill:elivibe` (skill commands enabled) |

Copy only the whole `elivibe/` skill folder from the release ZIP or tagged source archive, including `SKILL.md` and `agents/openai.yaml`. The commands below stop if either file is missing. Set `source` to the extracted skill folder's absolute path and use `.claude/skills` instead of `.agents/skills` for Claude Code:

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
