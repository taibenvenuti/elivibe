# Privacy and controls

The ordinary technical report is the evidence. eliVibe does not scan your repository, rerun work, or send product telemetry. OMP may make its own requests (for example, metadata-only skill discovery) independently of eliVibe. Follow your project's data policy even when using the same provider as OMP.

## What each mode sends

| Mode | eliVibe instructions and data |
|---|---|
| Off | No adapter instructions or isolated requests. OMP, its skill discovery, and other extensions keep their own behavior. |
| Manual | Ordinary handoff unchanged. After separately approving the explanation destination, `/elivibe` sends the report and explanation instructions, not the task. |
| Light | Ordinary handoff unchanged. With both roles authorized, an isolated judge receives the report and judgment instructions. Only after a positive decision can the separately authorized explainer receive the report and explanation instructions. Neither receives the task. |
| Full | Teaching instructions are included in an ordinary OMP request. There is no additional eliVibe model request; the ordinary conversation uses OMP's existing data, tools, routing and hooks. |

The standalone skill also runs in the ordinary OMP conversation. Full does not inject a second copy of the skill body when explicitly invoked. Normal OMP turns can include more conversation context than an isolated request; choose according to your host and project policy.

## Side-request boundaries

Manual and light do not collect a transcript, tool results, hidden reasoning, attachments, or additional source context to explain a report. Text or code already included in the report is a different matter: the handoff is sent whole, apart from surrounding whitespace, or refused rather than silently truncated. Quoted logs and instructions are data. Screens for sensitive-looking text, source dumps, and unsafe output are heuristics, **not comprehensive redaction**. Do not send reports containing secrets or private material you aren't authorized to share. The provider's response can also become part of the local OMP session record.

Isolated requests **bypass OMP's ordinary protection/provider hooks**: they don't run third-party redaction or routing hooks, and don't inherit your normal Hide Secrets arrangement. OMP 19.2.1 doesn't expose the final route used by the ordinary request to this adapter. It therefore can't authorize a side request based on which model produced the report, even on a fresh handoff. Approve a report-only request only if you can share the report unchanged without redaction or other hooks. If you're unsure, leave the report alone, use full mode for the next handoff, or use `/skill:elivibe` in an ordinary turn subject to OMP's existing policy. Do not treat consent as a way to work around an organizational safeguard.

Isolation means the request is not a new agent turn and provides no native tools. It does not mean the provider is local, free, or doesn't retain data. The request stays on its approved endpoint and never falls back to another model, provider, or route. Provider retention, access and charges are governed by the provider and your account settings. Cancelling locally or revoking consent can prevent later dispatch or delivery; it cannot recall a report the provider already received or guarantee that processing or billing stops.

### Proxy eligibility

Isolated requests don't implement proxy forwarding, and OMP 19.2.1 offers no read-only way to ask whether its proxy layers would carry a given request. (Its provider lookup caches its answer on first query, and the startup `PI_PROXY` value is captured with no status API.) eliVibe therefore applies a conservative rule to both roles, including the default TypeSafe Jev judge, before any credential is read and again immediately before the request is sent:

1. **Configured proxy settings win.** If a current proxy setting applies to the destination, the request is refused, even when `NO_PROXY` or a loopback or private address would otherwise match. The settings are listed under [isolated transports](compatibility.md#isolated-transports).
2. **Otherwise, the host must prove a bypass.** The request proceeds only if OMP's own exported `shouldBypassProxy` check says this destination would skip both proxy layers: a built-in local, private or metadata address, or a host your existing `NO_PROXY` already covers. An unknown, unavailable, negative or failing answer is a refusal.

A public cloud endpoint, including the default Jev judge, is eligible only when OMP positively proves a bypass. This requires an existing `NO_PROXY` rule that covers the endpoint, with no applicable proxy setting. Empty proxy environment variables or no apparent proxy configuration are not proof. The default judge is therefore usually unavailable. A deliberately configured loopback `openai-completions` endpoint usually passes, but a local explainer does not make the separate judge eligible. A refusal never sends the report and never replaces it.

Prefer `/skill:elivibe` for a report already visible, or `/elivibe full` before the next task. Those are ordinary turns: OMP applies its normal routing and protections, and may send more context than the report alone. Do not add bypass entries or remove proxy settings to make a side request eligible.

The automatic pipeline is bounded to 15 seconds for judgment and any explanation combined; manual is bounded to 45 seconds. These are local deadlines, not promises of when a provider stops processing or billing. OMP's isolated judgment has an 8 KiB ceiling on the UTF-8 report and judgment instructions. An explanation exceeding 64 KiB of UTF-8 is refused rather than clipped for display. Neither byte limit is exact token accounting or a network response-size guarantee; explanations have a separate output budget and are subject to the provider's context limit.

If an explanation cannot fit, use an approved supported model with a bigger context or ask for a shorter handoff; for incomplete or oversized output, try brief depth. For an oversized light-mode judgment try manual, or use full or standalone instead. A refusal, skip, timeout, cancel or failed response does not replace the source report.

## Approvals and refusals

Review and confirmation are available in the interactive terminal and in RPC clients that show command notices. Print and JSON modes refuse them because they cannot present a destination for review.

- `/elivibe model` shows the explanation selection. Default `auto` follows OMP's live active model. If the live model is unavailable, does not match the registered route, or changes the selection or route in flight, eliVibe refuses or cancels rather than sending to a stale or newly active destination. `/elivibe model <provider>/<id>` pins an explanation model independently of the ordinary model; `/elivibe model auto` clears that override. Selection and `/elivibe status` are not consent.
- **Explanation:** enter `/elivibe consent <provider>/<id>` to review the selected provider/model, API and exact endpoint. If the displayed destination is correct and you can share the whole report there, enter `/elivibe consent <provider>/<id> confirm`. Then, for a completed handoff in manual mode, enter `/elivibe`.
- **Judgment:** select the judge with `/elivibe judge <provider>/<id>` if changing the default (TypeSafe Jev). Enter `/elivibe judge-consent <provider>/<id>` to review its destination, then `/elivibe judge-consent <provider>/<id> confirm` if acceptable. Light needs both approvals before it can send a report; establish both before entering `/elivibe light`. Neither role's approval authorizes the other.
- Confirmation without a pending review, or after the exact destination changes, cannot grant approval. Start a fresh review before confirming a changed route. Pending reviews and grants are in memory for the current session and branch; resume, switch and branch do not restore them. Changing an eliVibe model selection invalidates that role's review and grant, as does revoking with `/elivibe consent off` or `/elivibe judge-consent off`. OMP session state stores preferences, not grants; no consumer configuration file is written.

`/elivibe off` stops adapter processing. You can also ask to skip eliVibe for one task or preserve a requested format.
