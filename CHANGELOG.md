# Changelog

## 1.1.0

Explain a technical handoff without replacing it. All three hosts use the same teaching skill in the ordinary host conversation. Add a focus or a desired depth to the request, or ask a follow-up in chat. If a request needs a handoff that is not in view, provide it rather than asking eliVibe to reconstruct it.

- **Codex:** Install the repository-backed plugin and invoke `$elivibe:elivibe`, or use `$elivibe` with the standalone skill. Both are explicit-only.
- **Claude Code:** Install the repository-backed plugin and invoke `/elivibe:elivibe`, or use `/elivibe` with the standalone skill. Both are explicit-only.
- **Oh My Pi (OMP):** Use `/elivibe` with the native plugin, including source-bound `/elivibe more` and optional modes and depth settings. Use `/skill:elivibe` with the standalone skill. The OMP GitHub and npm packages do not install the Codex or Claude Code plugins.

The standalone ZIP now ships Codex's explicit-only policy alongside the teaching file. The standalone ZIP, native OMP archive, and npm package include the same consumer README. Neither skill-only plugin adds an inference client or needs separate eliVibe credentials or a permission grant. Neither enforces the native OMP adapter's explicit-turn tool veto.

**Upgrading from 1.0.0:** No OMP preference migration is required. Install only one copy per host. When updating a standalone installation, replace the whole skill directory, not just `SKILL.md`.

**Tested scope:** Linux x64 CLI: Codex 0.162.1, Claude Code 2.1.291, and OMP 19.2.1. Real host runs with scripted replies exercised invocation and follow-up, not live-provider compatibility or explanation quality. No desktop, IDE, web, or mobile support is asserted, and no official vendor directory listing is included.

[Installation and removal](https://github.com/taibenvenuti/elivibe/blob/v1.1.0/docs/installation.md) · [Tested paths and limits](https://github.com/taibenvenuti/elivibe/blob/v1.1.0/docs/compatibility.md) · [Release status and evidence](https://github.com/taibenvenuti/elivibe/blob/main/docs/status.md)

## [v1.0.0](https://github.com/taibenvenuti/elivibe/releases/tag/v1.0.0) — 2026-11-27

- **Breaking:** The ordinary conversation replaces v0.1.0's report-only routes. Manual and Light no longer use isolated requests; the host model can receive more than the report. Old route grants do not carry over. See [privacy and disclosure](docs/privacy.md).
- Manual explanations, focused questions, and `/elivibe more` use the active OMP conversation. Manual stays the default; explicit explanations also work in Off and Full.
- Light and Full guide the ordinary task response, with no separate judgment or explanation transport. Light teaches selectively when a meaningful gap warrants it. Full asks for teaching with meaningful technical handoffs. The selected depth applies in both; neither replaces the report.
- Depth is `auto`, `brief`, or `detailed`; `adaptive` still means `auto`. The adapter's `model`, `judge`, `consent`, and `judge-consent` controls now show a migration notice. See [moving from a v0.1.0 linked install](docs/installation.md#move-from-a-v010-linked-install).
- The same regular `skills/elivibe/SKILL.md` supplies explicit portable use and native teaching guidance. The standalone skill is not advertised for automatic model invocation.
- Published the standalone ZIP, offline native OMP archive, and checksums. [Install from the verified GitHub tag, npm version, or a release archive](docs/installation.md).

## [v0.1.0](https://github.com/taibenvenuti/elivibe/releases/tag/v0.1.0)

- First public release: a portable skill and a native OMP plugin with Off, Manual, Light, and Full modes. In this version, Full runs in the ordinary conversation; Manual explanations and Light use separately authorized isolated routes, subject to [v0.1.0 routing limitations](https://github.com/taibenvenuti/elivibe/blob/v0.1.0/docs/compatibility.md).
- Published the licensed standalone ZIP, native OMP tarball, and SHA-256 manifest for `fe5ae8a9427b8d25a82b09c6186ab17b95b9882d`. See the [release notes](https://github.com/taibenvenuti/elivibe/releases/tag/v0.1.0) for the tested environment and evidence limits.
