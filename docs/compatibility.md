# Compatibility

eliVibe has one native adapter: **Oh My Pi (OMP)**. The Markdown skill can travel separately. A host accepting the skill format doesn't mean it can load the OMP adapter or has been tested with eliVibe.

## What is established

| Version or host | Evidence and limits |
|---|---|
| Published [v0.1.0](https://github.com/taibenvenuti/elivibe/releases/tag/v0.1.0) | Release evidence covers the approved archives, OMP 19.2.1 on Linux x64, and installation, update, rollback, and removal with synthetic responses. Local testing also used Linux x64/glibc on WSL2. The [v0.1.0 routing limits](https://github.com/taibenvenuti/elivibe/blob/v0.1.0/docs/compatibility.md) still apply to those archives. |
| v1.0.0 candidate: local checkout and offline native archive | Targets OMP 19.2.1 and the ordinary conversation. A local link or an archive check establishes only that specific route, not a public distribution. See the [candidate status and evidence ledger](status.md). |
| v1.0.0 candidate: GitHub source | [Pinned GitHub installation](installation.md#install-the-omp-candidate) passed at `440f0f3024253fd86f7955db4ab251364fb96cd5` in disposable OMP 19.2.1 on Linux x64. A fresh session discovered one adapter and one skill; help/status, a coding handoff, bare explanation, `more` and removal were exercised. Synthetic replies, not a live-provider trial or stable tag. |
| v1.0.0 candidate: npm | The actual tarball built from the same commit passed a disposable registry install, fixture upgrade, rollback and uninstall in OMP 19.2.1. No public `elivibe@1.0.0` or public-registry install has been verified. |
| 0.2.0 development archive trial: native Windows x64 | Tested local revision `d412c3ca89d90cc6748c3ca3c10fb5542b6f76c5` with native OMP 19.2.1. The verified archive linked, listed and discovered both the adapter and skill. Uninstall removed registration; a fresh session found neither entry, and the extracted files were unchanged. Used a disposable profile, not a sandbox. No Windows registry install or live inference was tested. |
| Pi and Claude Code | Upstream docs describe ways of using or shipping the standalone skill. These are documentation findings, not eliVibe runtime tests, native adapters, gallery or marketplace listings. |

Linux x64/glibc is the primary target; see the [status ledger](status.md) for current Linux, native and model evidence. The Windows archive trial does not establish behavior on the final revision or on other Windows routes. Don't infer support for other OMP versions, operating systems or architectures, or broad provider compatibility from a single run. The candidate uses OMP's own model selection, provider routing and conversation context. These results aren't security certification, a confidentiality guarantee, or a measure of explanation effectiveness.

## Pi: a standalone trial before packaging

[Pi's skill docs](https://github.com/earendil-works/pi/blob/main/packages/coding-agent/docs/skills.md) document project `.agents/skills/` discovery, `disable-model-invocation: true` for explicit-only use, and `/skill:name`. The candidate's single `SKILL.md` fits that layout on paper: try `elivibe/SKILL.md` under a temporary project's `.agents/skills/` and start Pi there. No OMP adapter is needed or expected to load.

[Pi's package docs](https://docs.pi.dev/latest/packages) describe local path, Git and npm sources, the `pi` manifest in `package.json`, and `--local` project scope subject to trust. For official [Pi package gallery](https://pi.dev/packages) discovery, publish a Pi package to npm with the `pi-package` keyword; that is the documented eligibility mechanism. A Git-only or local-path install is distinct from gallery discovery, and eligibility doesn't prove a listing. A skill-only Pi package could declare `skills/` without exposing OMP code; a native Pi integration would separately need [Pi's extension API](https://github.com/earendil-works/pi/blob/main/packages/coding-agent/docs/extensions.md).

**Next evidence:** pin a Pi version and record explicit invocation, absence from automatic skill selection, report preservation on a synthetic input, and removal in a clean project. If package distribution is pursued, test a local project-scoped skill-only package and update, rollback and removal before proposing a public listing.

## Claude Code: project skill before a marketplace

[Claude Code's skill docs](https://code.claude.com/docs/en/skills) document `.claude/skills/<name>/SKILL.md` for a project, `/name` for explicit use and `disable-model-invocation: true` for user-only invocation. The first trial would copy the same file to `.claude/skills/elivibe/SKILL.md` in a temporary project and try `/elivibe`. That would be a skill command, not the OMP adapter's command with modes.

[Claude Code's plugin guide](https://code.claude.com/docs/en/plugins/create) describes a plugin layout with a `skills/` directory, `.claude-plugin/plugin.json`, local `claude --plugin-dir`, and namespaced skill invocations such as `/plugin-name:skill-name`. [Marketplace distribution](https://code.claude.com/docs/en/plugin-marketplaces) uses a separate `.claude-plugin/marketplace.json` and an install ID of the form `plugin@marketplace`. A future plugin could distribute the same skill; the OMP bundle is not installable as that plugin.

**Anthropic's directory is separate from a self-hosted marketplace.** The [publication guide](https://code.claude.com/docs/en/plugins/publish#submit-to-anthropics-directory) directs third-party developers to the [directory developer portal](https://claude.ai/directory/manage) for review. It calls for an eligible paid account, a GitHub source repository, and strict local plugin validation before submission; portal review is additional. Accepted listings can reach Claude Code through account sync. The [official marketplace repository](https://github.com/anthropics/claude-plugins-official) does not take submissions by pull request. `claude-plugins-official` itself does not take portal submissions; the publication guide points partners to their Anthropic contact for that separate listing.

**Next evidence:** pin a Claude Code version and check discovery, explicit invocation, automatic-invocation behavior, report preservation, and removal in a clean project. If distribution is pursued, verify the namespaced skill and scoped lifecycle against a local marketplace, then choose whether to self-host or seek directory review. Managed host policy may restrict either install route. No submission has been made.
