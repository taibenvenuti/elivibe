# Changelog

## Unreleased — v0.1.0

- A single portable skill teaches concepts beside the ordinary technical report. It does not rewrite the report or require a fixed outline.
- Native OMP adds off, manual, light and full modes, with adjustable depth. Full runs in the ordinary conversation. Manual and light preserve the source and require separate destination review and confirmation for isolated explanation and judgment.
- Isolated explanations follow the live active OMP model unless pinned and refuse when the route cannot be verified. Both isolated roles refuse configured proxies and otherwise accept a destination only when OMP's `shouldBypassProxy` proves it bypasses both proxy layers (local/private/metadata or existing `NO_PROXY`), so the default TypeSafe Jev judge, which remains judgment-only, is often refused. See [proxy eligibility](docs/privacy.md#proxy-eligibility) and [compatibility and evidence limits](docs/compatibility.md).
- Source packaging builds a standalone skill ZIP, a native OMP bundle and SHA-256 checksums. Local builds are not published downloads.

When a version is published, its GitHub release notes identify the tag, commit, compatibility and verification limits. Subsequent notes come from the configured semantic-release process. See [release policy](docs/release.md).
