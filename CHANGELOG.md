# Changelog

## 1.1.0 — unreleased

- Explain a handoff in Codex or Claude Code without installing an executable extension. Install one repository-backed plugin and ask `$elivibe:elivibe` (Codex) or `/elivibe:elivibe` (Claude Code). A focused question can use the same conversation. Neither host needs eliVibe credentials, a background request or a permission grant.
- The standalone skill remains available. Its ZIP now includes Codex's explicit-only invocation policy as well as the canonical teaching file. A missing handoff is a reason to ask for it, not to infer what happened.
- Oh My Pi (OMP) retains its native command, source-bound `more`, optional modes and depth settings. The GitHub and npm OMP packages do not install the Codex or Claude Code plugins.
- The portable ZIP, native OMP archive and npm package include the same consumer README. See [installation and removal](docs/installation.md), [tested versions and limits](docs/compatibility.md), and [release evidence](docs/status.md). No official directory listing is included in this release.

**Upgrading:** No OMP preference migration is required from 1.0.0. Install only one copy per host. When updating a standalone installation, replace the whole skill directory, not just `SKILL.md`. Runtime evidence is for Linux x64 CLI: Codex 0.162.1, Claude Code 2.1.291 and OMP 19.2.1. Synthetic turns demonstrate command delivery and continuity, not model quality; the new skill-only plugins do not enforce a tool veto.

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
