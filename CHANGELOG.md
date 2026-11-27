# Changelog

## Unreleased — v0.2.0

- Manual explanations, focused questions, and `/elivibe more` use the active OMP conversation. Manual stays the default; explicit explanations also work in Off and Full.
- Light and Full guide the ordinary task response, with no separate judgment or explanation transport. Light teaches selectively when a meaningful gap warrants it. Full asks for teaching with meaningful technical handoffs. The selected depth applies in both; neither replaces the report.
- Depth is `auto`, `brief`, or `detailed`; `adaptive` still means `auto`. The adapter's `model`, `judge`, `consent`, and `judge-consent` controls now show a migration notice. See [moving from a v0.1.0 linked install](docs/installation.md#move-from-a-v010-linked-install).
- The same regular `skills/elivibe/SKILL.md` supplies explicit portable use and native teaching guidance. The standalone skill is not advertised for automatic model invocation.
- The candidate can be linked from a reviewed local checkout without a build. [GitHub source and npm installation](docs/installation.md#install-the-omp-candidate) are separate pending routes. Source packaging also produces the standalone ZIP, offline native OMP tarball and checksums.

## [v0.1.0](https://github.com/taibenvenuti/elivibe/releases/tag/v0.1.0)

- First public release: a portable skill and a native OMP plugin with Off, Manual, Light, and Full modes. In this version, Full runs in the ordinary conversation; Manual explanations and Light use separately authorized isolated routes, subject to [v0.1.0 routing limitations](https://github.com/taibenvenuti/elivibe/blob/v0.1.0/docs/compatibility.md).
- Published the licensed standalone ZIP, native OMP tarball, and SHA-256 manifest for `fe5ae8a9427b8d25a82b09c6186ab17b95b9882d`. See the [release notes](https://github.com/taibenvenuti/elivibe/releases/tag/v0.1.0) for the tested environment and evidence limits.
