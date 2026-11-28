# Contributing

Start with one concrete change:

- **Fix a confusing step.** Tell us which [install](docs/installation.md) or command step you followed, what happened, and what would have made the next step clear.
- **Improve an example.** Add an original synthetic handoff and show the smallest useful supplement. Point to one distinction it teaches and one claim it must not make. See [constructed examples](docs/qa-examples.md).
- **Cover a regression.** Add a synthetic case for one command, opt-out, lifecycle or provenance edge. Keep the report and its evidence intact.
- **Check a host.** Pick a gap in [compatibility](docs/compatibility.md), use a disposable project and synthetic input, and record the host version and what you actually observed.

No development setup is needed to [leave feedback](https://github.com/taibenvenuti/elivibe/issues/new?template=feedback.yml). A short invented example is enough to describe a concept that clicked, stayed confusing, or seemed misleading. For an installation or command issue, include the eliVibe version, installation source, host and version, operating system, exact invocation and observed result if known. For Oh My Pi, Codex CLI or Claude Code CLI, say whether you used the OMP adapter, a packaged skill or a standalone skill. Never paste raw transcripts or credentials. Use [private vulnerability reporting](SECURITY.md), not a public issue, for suspected data exposure.

For a PR, start with [repository guidance](AGENTS.md) and [development setup and focused checks](docs/development.md). Put changes to teaching guidance in the [canonical skill](skills/elivibe/SKILL.md). Keep executable integration in the OMP adapter and Codex and Claude Code packages declarative. Update the affected documentation. Use a Conventional Commit squash PR title (for example, `fix(omp): preserve the source handoff`), and follow the [release policy](docs/release.md) and [community standards](CODE_OF_CONDUCT.md).

Describe what changed, the relevant checks you ran, what they establish, and what remains unverified. Separate synthetic evidence from live behavior. Use original synthetic fixtures or material you have clear permission to contribute; leave out credentials, customer data, restricted source, and raw reports or transcripts.
