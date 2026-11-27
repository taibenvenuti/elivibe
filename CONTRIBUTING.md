# Contributing

Start with one concrete change:

- **Fix a confusing step.** Tell us which [install](docs/installation.md) or command step you followed, what happened, and what would have made the next step clear.
- **Improve an example.** Add an original synthetic handoff and show the smallest useful supplement. Point to one distinction it teaches and one claim it must not make. See [constructed examples](docs/qa-examples.md).
- **Cover a regression.** Add a synthetic case for one command, opt-out, lifecycle or provenance edge. Keep the report and its evidence intact.
- **Check a host.** Pick a gap in [compatibility](docs/compatibility.md), use a disposable project and synthetic input, and record the host version and what you actually observed.

Use **eliVibe feedback** in the [GitHub issue chooser](https://github.com/taibenvenuti/elivibe/issues/new/choose). If the form is not on the default branch yet, use a plain issue with the same details: eliVibe version or commit, host/version, exact command or mode, expected behavior and what happened. No credentials or normal profile are needed to work on the product. Use [private vulnerability reporting](SECURITY.md), not an issue or PR, for vulnerabilities or suspected data exposure.

For a PR, start with [repository guidance](AGENTS.md) and [development setup and focused checks](docs/development.md). Put changes to teaching guidance in the [canonical skill](skills/elivibe/SKILL.md); keep host integration in the OMP adapter. Update the affected documentation. Use a Conventional Commit squash PR title (for example, `fix(omp): preserve the source handoff`), and follow the [release policy](docs/release.md) and [community standards](CODE_OF_CONDUCT.md).

Describe what changed, the relevant checks you ran, what they establish, and what remains unverified. Separate synthetic evidence from live behavior. Use original synthetic fixtures or material you have clear permission to contribute; leave out credentials, customer data, restricted source, and raw reports or transcripts.
