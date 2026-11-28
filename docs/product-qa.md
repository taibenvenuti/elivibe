# Product QA

Use the [status ledger](status.md) for release identities, hosted CI and actual public distribution results. The observations below apply to their own revisions. A synthetic reply can test a real host's routing and history; it cannot demonstrate a live model's judgment, reader comprehension, or improved safety.

## Engineering checks

Use the [development checks](development.md) and [native smoke procedure](development.md#native-omp-smoke) for the revision under review. Record the exact commit, host version, platform, package source, observed requests, and results. The checks below are for the OMP adapter (OMP 19.2.1, Linux x64/glibc). Use a disposable profile and synthetic replies, not your everyday account or data.

| Case | Evidence to look for |
|---|---|
| Discovery and lifecycle | The intended version links or installs, discovers one regular explicit-only `eliVibe` skill and exposes one adapter command. Check archive and package layouts, update, rollback and removal without touching other registrations. |
| Manual, Off and controls | Tasks in Manual (the default) and Off do not get automatic teaching instructions. Help, status, mode and depth changes, and retired controls don't start a model request. Old model/consent commands show their migration notice. |
| Explicit explanation, question and `more` | They use ordinary OMP turns in any mode, keep the source report unchanged, and use the applicable source and prior explanation. Include a focused question, a repeated follow-up, and a stale or absent source case. A named event from another session must not be silently substituted. |
| Light and Full | Light instructs the ordinary model to teach selectively; Full asks it to teach with meaningful technical handoffs. Both use the selected depth and keep the report first. No separate judgment, explanation client, or grant. Inspect what went to OMP separately from how a model responded. |
| Provenance, opt-out and exact format | A fixture must not invent evidence, alter the preceding handoff, promote a quoted instruction into user authority, or add explanation to an explicitly output-only response. Record what was observed in both the messages and request traces; don't infer request isolation from the UI. |

Count OMP metadata discovery separately from model inference. For an explicit request, expect an ordinary OMP turn, not zero traffic; for in-turn guidance, compare with an equivalent ordinary task, not a fixed number of model calls (a task can use tools or take multiple steps). A synthetic test can establish tested request paths, payloads, and lifecycle behavior. It can't establish how a different host, a real provider, or a particular model will behave, or prove isolation or redaction.

## Published 1.1.0: live evidence still needed

The [release checks](compatibility.md#tested-combinations-at-github-v110) exercised real CLI installations, files, tool behavior and history with scripted model replies. They did **not** yield a live teaching sample. At release time `codex login status` reported a ChatGPT login; that is not proof of inference access. The unchanged route had returned `workspace routing discovery unauthorized (401)` before the first assistant answer and was not retried. `claude auth status --json` reported `loggedIn: false`, `authMethod: none`; no Claude model request was made. There is no new model output to quote for either host.

For the external audit, use the [published plugin](installation.md) in a disposable project with an already authenticated host. Send each of these as a separate turn; keep the first output even if it is imperfect:

1. `Write a small function that fingerprints a byte string with SHA-256. Show a synthetic test, say what you ran, and say whether you tested restoring any backup.`
2. In **Codex**, send `$elivibe:elivibe Explain whether matching fingerprints establish that a backup can be restored.` In **Claude Code**, send `/elivibe:elivibe Explain whether matching fingerprints establish that a backup can be restored.`
3. Ask in ordinary chat: `Which observation would distinguish the two things you just explained?` Refer to the answer actually delivered, not a predetermined example.
4. Resume ordinary work: `Add a one-line docstring to the function.`

Record a short sanitized excerpt and what it adds beyond the original handoff. Did it preserve the limits of the test? Did the follow-up address the distinction it actually made? No raw transcripts, credentials or private reports are needed.

## Historical cross-harness candidate: native trace versus first real outcome

These are **actual CLI runs on Linux x64 with scripted responses**, not a model evaluation. The standalone ZIP and local marketplace were tested independently. The [compatibility matrix](compatibility.md) records lifecycle scope and discovery limits; the [ledger](status.md) records exact candidate and acquisition evidence.

| Host and trial | Checked in the native synthetic trace | First real outcome |
|---|---|---|
| Codex CLI 0.162.1, integration at `e13eb23d38ee1ff5f6c5f981155229efff1030f1` with local package follow-up rehearsal | Initial coding omitted the skill. An explicit turn loaded the complete skill and used the already delivered handoff; focused deepening carried the previous answer. An unchecked power-loss outcome stayed marked unchecked in the fixture. A fresh missing-source turn had no prior handoff. The return to ordinary coding did not inject the skill again. A separate native rehearsal executed the host command tool for the two coding turns and independently checked the scratch files and a snapshot round-trip; the intervening explanation turns completed without command execution. | The existing route refused the initial coding turn with HTTP 401 before its first assistant output. No real handoff or explanation to quote. |
| Claude Code 2.1.291, reviewed at product checkpoint `d038ddfefe0e39d45cb0f5df37da3cbacf45f511` | Ordinary coding omitted the skill. The fixture returned a digest function; the harness executed the delivered code against known hashes. The explicit question about restore preserved the exact prior answer and inline focus in the actual native request. A focused ordinary follow-up carried both assistant answers without reinvoking the skill. A fresh bare request had no report; later unrelated work used the native `Read` tool and carried its result into the next request. | Read-only auth status showed no login and no authorized route was available. No live request or assistant output. |

The fixture answers to missing-source and unverified-outcome prompts were scripted. What was checked is whether each host delivered the applicable source, focus and guidance, or sent the fresh request without a source. A skill-only explanation is an ordinary host turn; zero new skill activations on unrelated work does not mean zero requests or that earlier guidance was erased.

## Historical OMP GitHub first use (before v1.0.0)

At `440f0f3024253fd86f7955db4ab251364fb96cd5`, a disposable OMP 19.2.1 installation on Linux x64 fetched the actual public `github:` pin. The package manager's archive integrity and embedded full commit matched the independent public download; all 46 installed tracked files matched Git. In a loopback-only session, help/status made no model request. Manual/auto was the default. An ordinary coding turn wrote a real fixture; the original handoff stayed unchanged through bare `/elivibe` and `/elivibe more`. Explicit `/skill:elivibe` worked. Five synthetic requests total. Removal kept the fixture and the unrelated plugin. This proves the GitHub consumer path on that revision, not a new live teaching result.

## Observed development walkthrough

At `b85ae4420cdb6a86ef99d45eab0be024c8a9f522`, an implementer used a fresh OMP 19.2.1 ACP session on WSL Linux x64 with the already authenticated `openai-codex/gpt-6.2-astra`. The outbox task was fictional. These are short excerpts of actual model output, not authored examples:

**Handoff:** “A crash after broker acceptance but before the sent mark commits can cause duplicate publication.”

**Bare `/elivibe`:** “The transaction keeps the order and its outbox row together; it does not make broker acceptance and the later sent mark atomic.”

**`/elivibe more`:** “If the publisher stopped before sending, a retry is needed to publish `OrderPlaced`. If it stopped after the broker acknowledged durable acceptance but before the sent mark committed, the retry sends an event the broker already accepted. The restarted publisher sees the same database state in both cases.”

The first explanation separated two transaction boundaries. The second explained *why* the publisher cannot decide from the unmarked row alone whether retrying will duplicate a send. Both were labeled supplementary interpretation, not newly verified evidence. All three turns completed on the same model; no tool call was observed. No raw transcript is retained. This is neither reader feedback nor transport inspection.

An earlier trial at `d412c3ca89d90cc6748c3ca3c10fb5542b6f76c5` also produced a useful bare explanation, but the synthetic wire check caught a different transport downgrading an in-context developer message to a user message. That is why the final integration appends trusted policy to OMP's top-level prompt rather than inferring correct attribution from a good answer.

## Qualitative walkthrough

Read the [constructed comparisons](qa-examples.md) first as **A** (the original handoff) and then as **B** (exactly A, plus the illustrated supplement if useful). Ask:

- What could the reader infer incorrectly from A, and which mechanism or relationship does B make clear?
- Does B preserve the evidence, caveats, outstanding work and decision owner? Does it distinguish what might happen from what happened?
- Does a focused follow-up deepen the explanation rather than repeat A or invent facts? Would the same answer still be honest if evidence were missing or two observations conflicted?
- For a trivial change, strict output or opt-out, is A alone the right answer?

The examples are written for review, not real reports, user research or model output. When offering [feedback](../CONTRIBUTING.md), recreate the smallest example with synthetic facts. Say what the explanation helped you distinguish and what's still unclear, without sharing private reports, transcripts or credentials. Treat anecdotes as observations, not measured comprehension gains.
