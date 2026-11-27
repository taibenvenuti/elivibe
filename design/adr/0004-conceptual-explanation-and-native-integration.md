# 0004 — Teach alongside the handoff; integrate activation with the host

**Historical: v0.1.0.** [ADR 0005](0005-host-managed-teaching-and-distribution.md) retains the teaching decision and supersedes the activation, transport and authorization design below. See the [tagged implementation](https://github.com/taibenvenuti/elivibe/tree/v0.1.0) for this earlier behavior.

## Why keep the report?

A stopped worker is not an empty queue: one observation concerns a process, the other concerns outstanding work. A well-written report can give accurate evidence about the first without explaining why it tells us little about the second. That distinction is the teaching layer's job. It illustrates the design, not a measured comprehension or safety benefit.

Keep the ordinary technical handoff visible. It is the source account, not independently verified ground truth. Add a distinct teaching supplement only when there is a concept worth explaining or the reader asks. Don't turn an illustrative mechanism into a claim about this system. Preserve explicit format instructions and opt-out. One [portable skill at v0.1.0](https://github.com/taibenvenuti/elivibe/blob/v0.1.0/skill/elivibe/SKILL.md) supplies the methodology; depth changes detail, not the evidence or the activation mode.

## Why a native adapter?

Skill discovery alone cannot offer a predictable user command, observe a newly delivered terminal message, or grant permission for a specific model route. OMP owns those boundaries. The [adapter](../../adapters/omp/index.ts) reads the canonical skill and translates host events, model identity, session state and permissions. The [core](../../core/index.ts) decides what to do with an eligible report and bounds the operation. It does not read host history, rendering state or files.

| Path | Evidence available | Cost and limitation |
|---|---|---|
| Standalone or full | Ordinary generation, using context already visible to the coding agent | No separate eliVibe model request. A model can ignore an instruction; injection is not proof of compliance. |
| Manual (default) | One visible handoff. OMP's ordinary turn does not attest its final URL; even on the active model, approval is explicit and the task is omitted. | At most one isolated explanation on invocation. Approval authorizes the report, not a transcript. |
| Light | One eligible terminal report, with separate judge and explanation permissions | At most one judgment and one explanation following a positive decision. Lifecycle signals and judgment can misclassify a handoff. |
| Off | No adapter processing | Does not disable independent native skill discovery or explicit skill use. |

Manual and light trade an optional, potentially billable request for a supplement *after* delivery. They bypass ordinary conversation hooks and cannot recover evidence lost to compaction. Model selection is not authorization; no implicit redirect, substitute destination, retry, tools or transcript replay. Uncertain provenance cannot authorize a task or an automatic transfer. On refusal, timeout or failure leave the original intact. See the [integration contract](../../docs/integration.md) and [privacy boundary](../../docs/privacy.md).

## What survives from OPERA?

- A plan is not an action. Writing code is not checking its behavior. Expected effects are not observations.
- A passing check does not cancel a failing, missing or unrun check. Command success does not establish deployment health.
- Partial work is not done. Preserve assumptions, unresolved risk and consequential decisions; never grant approval or invent missing evidence.

These are fidelity rules, not an output outline. A generic ELI5 rewrite or selectable OPERA template would compete with the original report rather than explain a distinction. An autonomous verifier would need new evidence, authority and cost. Extra adapters would add untested lifecycle and consent assumptions. None is part of this decision.

Revisit the supplement if redacted observations repeatedly show only restatement or misleading new claims. Restrict a transport if its destination or tool boundary cannot be enforced. Reconsider another harness only with a concrete need and native evidence of activation, preservation, consent and removal. Formal evaluation requires a separately approved protocol; engineering tests establish routing, not reader outcomes.
