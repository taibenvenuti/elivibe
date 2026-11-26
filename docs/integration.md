# Adding a harness

The product has one methodology: [`skill/elivibe/SKILL.md`](../skill/elivibe/SKILL.md). A user can install that file alone. The native integration adds control over **when** it applies; it is not another set of writing rules.

The [active architecture decision](../design/adr/0004-conceptual-explanation-and-native-integration.md) explains why a terminal event can trigger a judgment but cannot prove semantic completion. [Privacy and consent](privacy.md) describes what each mode can transmit.

| Owner | Responsibility |
|---|---|
| [Core](../core/index.ts) | Apply mode, destination authorization and input budgets; judge whether explaining an implicit concept would help, request a tool-free explanation, or leave the report alone. No session, filesystem, UI or OMP imports. |
| [Jev transport](../providers/jev.ts) | Encode the core's decision question as a [TypeSafe System One Choice](https://docs.typesafe.ai/primitives/choice), with the report as `state`. Return one of the allowed choices. Not an explanation model. |
| [OMP adapter](../adapters/omp/index.ts) | Recognize a live completion, isolate its final visible text, own native commands and session lifecycle, resolve authorized models, and deliver the result. The skill is read from the installed artifact, not discovered by the agent. |

## Inference boundary

Full mode uses the ordinary host request, which already has conversational context. The standalone skill can likewise explain earlier discussion still visible in that conversation. A tool-free explanation made afterward does **not** have the same evidence. For instance, the report might say a worker was stopped without mentioning that the user wanted to preserve queued orders. Knowing that goal changes which distinction deserves explaining. There is no need to give the explainer the entire session to convey it.

The portable contract permits a short, screened task only on a proven original active route. **OMP 19.2.1 cannot attest to the URL actually used by the ordinary turn.** A provider request event identifies the model, not the final dispatch destination. Manual and light therefore send report text only after separate review and confirmation of the exact isolated route for each role. No task, tool list, hidden reasoning, raw tool results, attachments or reconstructed transcript. Do not silently shorten an oversized report: the ending might contain the caveat that reverses the decision. Screening cannot establish that arbitrary prose is safe to share.

OMP's conversational and ephemeral turns start with session history. Disabling tools doesn't remove that history. The adapter instead constructs one tool-free request, rather than assuming an available transcript is an authorized payload. When older discussion genuinely matters, explicitly invoking the standalone skill in the active conversation is a useful alternative to sending more data to a second model.

The cheap judge has its own spending limit. With an exact token count the core budgets instructions, report and reply together; without one it caps the judgment payload at 8 KiB of UTF-8 text. That byte cap does **not** apply to explanations. An adapter without an exact tokenizer sends the whole handoff and relies on the provider to enforce its context window. A context rejection or incomplete response is not a successful explanation. eliVibe neither retries with a cut-down report nor splits it into separately billed chunks.

An isolated chat request uses a direct Chat Completions POST, not OMP's general model runner. A custom fetch on that runner is not a security boundary: provider-specific handlers can choose another path. The separate Jev choice transport is judgment-only. Both apply the [proxy eligibility rule](privacy.md#proxy-eligibility) before credential lookup and again before dispatch. Full mode and explicit standalone invocation keep the ordinary host path.

Side requests bypass the ordinary agent's tool, context and redaction hooks. Use the standalone skill or full mode if native protections are required. Request flags and local screening do not establish the provider's actual retention or privacy policy.

The adapter resolves `auto` through OMP 19.2.1's live `ctx.models.current()` query, not the model snapshot on a command context. It captures the exact registered route and rechecks it against live selection after asynchronous prerequisites, immediately before dispatch and before delivery. Missing, unusable or changed live state fails closed; an in-flight request never switches destinations. A pinned explanation model and the separate judge resolve through the registry independently of the ordinary model. Model selection never grants approval. See the [review and confirmation interaction](privacy.md#approvals-and-refusals).

## Minimum capabilities by mode

- **Off / manual baseline:** a trusted way to select a mode (default manual) and invoke an explanation. Scope state and consent to the user/session; a checkout must not be able to grant permission to send a report. Off needs no model operation.
- **Manual explanation:** identify the preceding report and its generating route. If the host can establish that the active model and destination are unchanged, the invocation authorizes that one explanation. If it cannot, require separate approval for the actual destination. Retain the source report on success and failure.
- **Light:** additionally distinguish a *new*, successful terminal assistant message from tool calls, progress, aborts, history replay and adapter output. A judge can ask whether the reader needs a mental model without ever receiving the rest of the conversation. No explanation after a negative or failed judgment.
- **Full:** supply the canonical skill before generation so the ordinary report and teaching layer arrive together. Preserve host instructions, explicit user formats and opt-outs. A host without this hook cannot claim full mode; a post-generation request would have a different data and cost boundary.

Persistence, a model picker and a status UI are optional. Display explanations distinctly. A host that cannot preserve the source, isolate a report or constrain the inference destination must not emulate the feature with an autonomous agent turn.

A second adapter must exercise its own command, boundary, preservation, consent, resume and removal paths in the real harness before claiming support. No second harness is currently implemented.
