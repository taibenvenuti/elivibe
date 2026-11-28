# How the OMP integration works

See [ADR 0005](../design/adr/0005-host-managed-teaching-and-distribution.md) for the decision and [privacy](privacy.md) for what a normal host turn can disclose. This is a teaching layer, not a second agent that verifies the work.

The [portable skill](../skills/elivibe/SKILL.md) supplies the same teaching guidance to Oh My Pi (OMP), Codex and Claude Code. Only the OMP adapter runs eliVibe code. Codex and Claude Code packages register the skill with the host; they don't implement the OMP command, mode/depth settings, source tracking or tool veto.

| Owner | Responsibility |
|---|---|
| [Portable skill](../skills/elivibe/SKILL.md) | How to teach: explain a mechanism, relationship or consequence without changing the evidence. It doesn't select modes or grant permissions. |
| [Core](../core/index.ts) | Interpret command arguments and preferences; compose guidance from the same skill. No provider, credential store, network client or file access. |
| [OMP adapter](../adapters/omp/index.ts) | Register one command, obtain the relevant branch's report, apply scoped teaching policy, restore preferences and let OMP deliver the answer. |
| OMP | Ordinary conversation, model/auth selection, prompt preparation, storage, compaction, tools, cancellation and host safeguards. Other extensions keep their own policy. |

## Explicit command

In the OMP adapter, use `/elivibe`, `/elivibe <question>`, or `/elivibe more`. Controls and missing-source cases that require a report are handled locally. For an explanation or focus request accepted while the host is idle, the adapter starts a normal OMP turn and forwards the user's own command as input. During `before_agent_start` it preserves the ordered host policy and appends a trusted teaching block for that preparation. This distinction matters: some Chat Completions routes serialize a *conversation* developer message as if the user had written it. OMP's top-level system policy is a separate path. `sendUserMessage` skips template/command expansion, so sending a literal `/skill:elivibe` is not a way to invoke the skill. Never interpolate report bytes, logs, prior interpretations or the focus question into system policy.

An existing handoff stays at its original message. The new assistant response is supplementary interpretation and remains in the host conversation so the reader can refer to what was actually shown. Repeated explicit requests are intentional. There is no side-client callback that can append a belated result to another branch. Don't queue a new explanation behind unrelated work; retry once the host is idle. Don't manufacture the missing source from an earlier interpretation or another branch.

Bare and `more` answer different questions. Bare selects the newest completed ordinary assistant answer on the branch, even if that handoff needed no tools. It does not claim every answer was a coding task. `more` selects the preceding eliVibe interpretation and **its own** source, even after an unrelated reply. An aborted response or standalone skill explanation isn't a replacement handoff. The adapter checks the selected message's identity and position again in the prepared context and refuses a mismatch rather than teaching from a different report.

The OMP adapter saves and restores mode and depth through native `elivibe-settings` session entries on the current branch. It reads those two fields only; `adaptive` maps to `auto`, and old model, judge and approval fields have no effect. A content-free turn marker associates an interpretation with its source. It isn't the explanation and doesn't replace the assistant message. If compaction removes the source for a bare or deeper request, ask for a fresh handoff; don't silently treat the summary as the original. A focus question does not require a retained handoff: it can use one if relevant, or ask about a concept without claiming that a particular system uses it.

During an explicit explanation the adapter vetoes tools at OMP's `tool_call` hook; it doesn't replace the host's active tool list or hide every schema from the model. A model can ask for a tool and receive a refusal. Native policy and other extensions are not under eliVibe's control. The automatic modes leave ordinary task tools alone. Teaching instructions are not enforcement of output quality or format. See the [native checks](development.md#native-omp-smoke) for how to distinguish payload, tool execution and displayed output.

## In-turn teaching and discovery

Manual (default) and Off inject no automatic teaching. Light appends a selective policy to ordinary task preparation. Full asks the same model to teach with meaningful handoffs. Both preserve prior host instructions and put the source account first. If the task is trivial, opts out or requires a strict output format, the ordinary answer alone is appropriate. No second request judges or expands the answer automatically. The model can still misunderstand instructions: check generated examples separately from wiring.

Scoped policy can change a provider's cacheable prompt prefix. Reusing the active model does not guarantee a cached, free or fixed-latency explanation; provider billing and cache behavior vary. Keeping teaching instructions attached to every turn merely to improve cache reuse would change Off and Manual. No cache savings or measured overhead are claimed.

The package exposes one regular `skills/elivibe/SKILL.md`. OMP 19.2.1's `disable-model-invocation: true` excludes the bundled skill from the automatic catalog without disabling the interactive `/skill:elivibe` command when host skill commands are enabled. This explicit skill command is a host feature, not a second adapter registration; it does not set modes or carry the adapter's tool veto. Do not install a separate standalone copy alongside the native package. One package manifest identifies the OMP runtime for Git, npm and release archives.

## Codex and Claude Code

| Host | Packaged skill | Standalone skill |
|---|---|---|
| Codex CLI | `$elivibe:elivibe` | `$elivibe` |
| Claude Code CLI | `/elivibe:elivibe` | `/elivibe` |

Both are explicit skill invocations. Ask a follow-up in ordinary text, and name or paste the source if it is no longer clear from the conversation. Earlier instructions and messages may still be present in host context; that's not adapter-managed source selection, restoration or automatic teaching. There is no equivalent of OMP `/elivibe more` in a skill-only install on any host.

The skill asks the model not to use tools just to explain. It adds neither permissions nor a deterministic tool veto. The host's permissions, authentication and request policy remain authoritative. See [compatibility](compatibility.md) for the scope of the CLI evidence; successful skill loading isn't evidence of how a live model will answer.

## Adding another host

First test skill-only discovery, explicit invocation and removal with a pinned version. An *executable adapter* additionally needs clear source/interpretation identity, honest context and cost boundaries, additive prompt hooks, scoped tool policy, persistence and session lifecycle tests. Installing a plugin package doesn't by itself prove any of that. See [compatibility](compatibility.md) before making a support claim.
