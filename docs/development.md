# Developing eliVibe

Consumers use [installation](installation.md); they don't need this toolchain. Work from the public product checkout with full Git history. The [status ledger](status.md) names the reviewed baseline and the current evidence, not just the checks we intend to run.

## Product checks

The pinned Linux development job uses CPython 3.14.4, Node 24.21.0, npm 11.19.0, uv 0.12.5 and actionlint 1.7.12. From the repository root on Linux x64:

```sh
sh dev/check --setup
```

This sets up locked Python and Node **development** dependencies and checksum-verified actionlint. After setup, use `sh dev/check`. The command checks the product manifest/lock, workflow syntax, local Markdown links/anchors and shell example syntax, commit subjects, Ruff format/lint, product and adapter tests, strict no-emit TypeScript against OMP 19.2.1, and disposable semantic-version rule fixtures. Markdown syntax is not a network or consumer-install check. A fake host can establish parser and lifecycle behavior, not actual routing or teaching quality. Do not unset your proxies or change your personal OMP profile to make a mock pass.

## Native OMP smoke

Use the [official OMP 19.2.1 Linux x64 binary](https://github.com/can1357/oh-my-pi/releases/download/v19.2.1/omp-linux-x64), SHA-256 `e8b937f9bf023baa147bdd300ad5421af0a6ef8b1f350c47a9a93d5fca94feca`, Python 3.14, and working unprivileged bubblewrap namespaces. [CI](../.github/workflows/ci.yml) supplies the exact checkout's packages. To exercise the candidate built in the [release instructions](release.md#version-and-contents), use the same shell variables and full source SHA:

```sh
git archive --format=tar.gz --output="$output/source.tar.gz" "$sha"
python3.14 dev/omp_smoke.py --omp "$(command -v omp)" \
  --archive "$assets/elivibe-omp-$version.tar.gz" --skill-archive "$assets/elivibe-$version.zip" \
  --npm-archive "$npm_tarball" --source-archive "$output/source.tar.gz"
```

### What survived the removal of the side client

The v0.1.0 Node suite included provider selection, isolated role/payload validation, Jev transport and proxy handling, per-route grants, judgment replies and background request cleanup. Those implementations **no longer run**. Recreating their mocks would not protect the ordinary host path. Assess the replacement by responsibility, not by the number of test cases:

| Guarantee | Current check |
|---|---|
| Exact controls, completion, optional settings, opt-outs and independent depth | [`command.test.ts`](../tests/plugin/command.test.ts) and [`host.test.ts`](../tests/plugin/host.test.ts); controls and missing reports do not dispatch a model request. |
| Original account retained; ordinary host policy; explanation and focus attributed correctly | Host replay tests and [native smoke](../dev/omp_smoke.py) inspect roles, source text, top-level teaching policy, and the actual shown answer on the next request. |
| Intentional repeats versus automatic duplicates | Host tests exercise `more`, new ordinary answers, filtered markers and in-turn Light/Full guidance. The native trace counts requests rather than relying on a mocked dispatch. |
| Turn cleanup, branch, compaction and model changes | Host lifecycle tests cover ambiguous, rewritten and missing source positions, busy admission, cancellation, restoration and selection of the current model. |
| Preference migration and environmental isolation | Host tests load old preference entries without restoring grants. Generic command/host tests don't need a provider or ambient proxy configuration; the native fixture owns its environment and private loopback endpoint. |
| Discovery and upgrade/removal | Native OMP inspects the extension and explicit-only skill independently, and checks registry install, version changes, removal and the unrelated plugin registration. It also checks the clean Git export as a source-root package, not a fetch from GitHub. |

Keep developer scripts in `dev/`, not root `tools/`: OMP discovers scripts in an installed plugin's `tools/` as custom tools, including when installed from a Git checkout.

`dev/omp_smoke.py --help` also lists optional `--ponytail` and `--context-mode` paths for testing coexistence with those extensions, when already available. Neither is required for eliVibe or the standard smoke.

The native sandbox checks its own non-root identity, dropped capabilities, distinct loopback-only network namespace and lack of an external route. Hosted mode additionally requires the expected enforced AppArmor stack. The [runner preflight](../.github/native-namespace.sh) is for disposable hosted Ubuntu runners only. Do not run it on a workstation or relax global policy to make a smoke pass. Synthetic loopback responses make request payloads inspectable without exposing a developer's normal profile or credentials. They do not establish provider support, reader outcomes or live quality.

## Codex and Claude Code package checks

Use Codex CLI **0.162.1** and Claude Code **2.1.291** on Linux x64; record their `--version` output, the exact source revision and archive identity, and the discovery scope. Use the [reviewed candidate build](release.md#version-and-contents) or the exact published ZIP and tag. Test the ZIP **and** the Git marketplace in separate scratch projects/profiles; do not keep both copies visible. Keep the extraction outside discovery roots and compare the installed skill and Codex policy with the reviewed bytes. See [installation](installation.md) for consumer commands.

For local package validation, set `checkout` to the absolute path of the reviewed checkout. Run these from disposable host state, not your normal profile:

```sh
claude plugin validate "$checkout" --strict
claude plugin validate "$checkout/skills" --strict
codex plugin marketplace add "$checkout"
codex plugin add elivibe@elivibe
claude plugin marketplace add "$checkout" --scope local
claude plugin install elivibe@elivibe-marketplace --scope local
```

- **Codex:** Start `codex app-server` in the scratch project with a disposable Codex home. Initialize, use `skills/list` to check exactly one eliVibe, then `thread/start` and `turn/start` against an isolated loopback fixture. Compare a plain input, the literal `$elivibe` or `$elivibe:elivibe` for the installed route, and a structured `skill` input using the name and path from discovery. Submit a picker selection in the native TUI too. Inspect the actual outgoing request, not the debug prompt builder. After removal, a fresh session should not discover the skill; an unrelated control skill must still be present. A filesystem catalog reinstall with replacement fixture bytes is not a remote Git upgrade.
- **Claude Code:** Run `claude -p --output-format stream-json --verbose` in the scratch project against a disposable loopback fixture. Check the `system/init` command advertisement and use `--resume` with the same session for the explanation and ordinary follow-ups. Use a fresh session for the missing-source probe. Check that disable and enable in the chosen scope hide and restore the command after restarting; verify removal and compare discovery in a sibling project for `local`, `project`, and `user` scope. `--plugin-dir "$checkout/skills"` is a separate session-only check.
- **Both:** Use a [synthetic handoff](qa-examples.md) and keep the delivered answer intact. Ask a focused question about an explicitly unchecked outcome, deepen it with an ordinary follow-up, then return to unrelated work. Inspect the actual request for explicit activation, earlier assistant messages and inline focus, and the absence of **new** activation on the unrelated turn. Test a bare command in a fresh thread separately from a self-contained conceptual question. Inspect payload, rendered fixture and host tool results separately. Use bounded deterministic replies, no real credentials and no ambient account state; an isolated profile is not itself a network sandbox.

Repository checks validate manifest metadata, package boundaries and byte identity; they do not drive Codex/Claude inference. Local CLI validation and discovery are not hosted CI, anonymous GitHub acquisition, or directory validation. For future submission review, compare the narrow package with [OpenAI's ZIP contract](https://developers.openai.com/plugins/deploy/submission) and Anthropic's [strict CLI and portal checklist](https://code.claude.com/docs/en/plugins/publish#submit-to-anthropics-directory). Check the README, support and privacy URLs against the actual public ref. Do not upload or submit during development.

No mandatory provider CI. An authorized optional walkthrough uses the host's existing route without new grants, endpoint overrides or credential copying. In the [development trials](product-qa.md), the Codex live attempt stopped before output on HTTP 401; Claude Code had no authorized route and made no live request. Neither is a reason to substitute scripted text for a real answer or work around the host's access controls.

## Teaching and first-use review

Use a meaningful [synthetic handoff](qa-examples.md). In a working, authorized conversation, invoke the command for the installed host, ask a focused question and try deepening it (OMP also offers `/elivibe more`). Compare with the untouched report: can a reader explain why the system behaves that way or make a better-informed decision? A passing payload assertion, a scripted answer and an actual model-generated response answer different questions. Label each precisely; do not attribute implementer observations to independent readers. Record sanitized excerpts and meaningful failures only. Do not copy private sessions, ask for extra provider access or start an external evaluation service.

## Dependency and repository policy

Use reviewed updates with exact dev pins, lockfile integrity, `npm ci --ignore-scripts`, pinned CI actions and no saved checkout credentials. No development dependencies belong in a runtime archive. Keep PR checks read-only and separate from privileged release operations. Review and squash on protected `main`; use a Conventional Commit PR title. Sole-maintainer review is not independent approval. See the [release gates](release.md) before any external write.
