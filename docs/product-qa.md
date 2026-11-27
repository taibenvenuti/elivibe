# Product QA

Published [v0.1.0](https://github.com/taibenvenuti/elivibe/releases/tag/v0.1.0) has historical archive and synthetic native evidence. It is not evidence for the unreleased v0.2.0 candidate. The engineering checklist below describes what to check; the development walkthrough records one observation, not an acceptance result. See [status](status.md) for current evidence. Synthetic checks and constructed comparisons do not measure comprehension, improvement in safety, or live-provider behavior.

## Engineering checks

Use the [development checks](development.md) and [native smoke procedure](development.md#native-omp-smoke) for the revision under review. Record the exact commit, OMP version, platform, package source, observed requests, and results. The target is OMP 19.2.1 on Linux x64/glibc. Use a disposable profile and synthetic provider, not your everyday account or data.

| Case | Evidence to look for |
|---|---|
| Discovery and lifecycle | The intended version links or installs, discovers one regular explicit-only `eliVibe` skill and exposes one adapter command. Check archive and package layouts, update, rollback and removal without touching other registrations. |
| Manual, Off and controls | Tasks in Manual (the default) and Off do not get automatic teaching instructions. Help, status, mode and depth changes, and retired controls don't start a model request. Old model/consent commands show their migration notice. |
| Explicit explanation, question and `more` | They use ordinary OMP turns in any mode, keep the source report unchanged, and use the applicable source and prior explanation. Include a focused question, a repeated follow-up, and a stale or absent source case. A named event from another session must not be silently substituted. |
| Light and Full | Light instructs the ordinary model to teach selectively; Full asks it to teach with meaningful technical handoffs. Both use the selected depth and keep the report first. No separate judgment, explanation client, or grant. Inspect what went to OMP separately from how a model responded. |
| Provenance, opt-out and exact format | A fixture must not invent evidence, alter the preceding handoff, promote a quoted instruction into user authority, or add explanation to an explicitly output-only response. Record what was observed in both the messages and request traces; don't infer request isolation from the UI. |

Count OMP metadata discovery separately from model inference. For an explicit request, expect an ordinary OMP turn, not zero traffic; for in-turn guidance, compare with an equivalent ordinary task, not a fixed number of model calls (a task can use tools or take multiple steps). A synthetic test can establish tested request paths, payloads, and lifecycle behavior. It can't establish how a different host, a real provider, or a particular model will behave, or prove isolation or redaction.

## Observed development walkthrough

On local revision `d412c3ca89d90cc6748c3ca3c10fb5542b6f76c5`, an implementer used OMP 19.2.1 on WSL Linux x64 in an ordinary ACP host session with `openai-codex/gpt-6.2-astra`. The outbox task was synthetic; the following short excerpts are actual model output.

**Handoff:** “A crash after acknowledgement but before the sent mark leaves the row eligible for retry. On restart, the publisher resends the event with the same ID.”

**After bare `/elivibe`:** “The unchanged event ID makes two copies recognizable as the same logical event. It does not make a subscriber act only once. No fault-injection result shows that a duplicate occurred, and no subscriber design tells us what effect one would have.”

`/elivibe more` produced another assistant turn, but no excerpt was retained, so there is no evidence that it improved the depth. Three turns and zero tool calls were observed. This was not an independent reader review, an inspection of wire message roles, or a check of the final revision. No raw transcript is included.

## Qualitative walkthrough

Read the [constructed comparisons](qa-examples.md) first as **A** (the original handoff) and then as **B** (exactly A, plus the illustrated supplement if useful). Ask:

- What could the reader infer incorrectly from A, and which mechanism or relationship does B make clear?
- Does B preserve the evidence, caveats, outstanding work and decision owner? Does it distinguish what might happen from what happened?
- Does a focused follow-up deepen the explanation rather than repeat A or invent facts? Would the same answer still be honest if evidence were missing or two observations conflicted?
- For a trivial change, strict output or opt-out, is A alone the right answer?

The examples are written for review, not real reports, user research or model output. When offering [feedback](../CONTRIBUTING.md), recreate the smallest example with synthetic facts. Say what the explanation helped you distinguish and what's still unclear, without sharing private reports, transcripts or credentials. Treat anecdotes as observations, not measured comprehension gains.
