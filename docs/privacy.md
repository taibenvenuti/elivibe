# What reaches the model?

**eliVibe uses your ordinary host conversation, not a report-only request.** OMP v1.0.0 changed the disclosure contract for Manual and Light in the [published v0.1.0](https://github.com/taibenvenuti/elivibe/blob/v0.1.0/docs/privacy.md). Old isolated-route approvals are not authority for the current behavior. If the conversation is not suitable for the active host model or your organization's policy, do not invoke eliVibe on it.

| Action | Disclosure and effect |
|---|---|
| OMP adapter: Manual (default) or Off | No automatic teaching. An accepted explicit explanation, focus question or `more` requests an ordinary model turn; it doesn't change the mode. |
| OMP adapter: Light or Full | Teaching guidance during ordinary generation, not a second eliVibe judge or background request. Requested output formats and opt-outs take priority. |
| OMP adapter: help, status, settings or a preference change | Local controls. No explanation request. |
| Explicit skill (Codex CLI, Claude Code CLI or OMP skill command) | Packaged and standalone skills use the host's normal turn. No eliVibe modes, stored preferences or source tracking; the host can still retain the conversation. |

Your host chooses the route, credentials and context under its usual policy. Context may include earlier messages, tool output, other integrations' context and a summary after compaction. Instructions and explanations may remain in session history and be sent again during follow-up. Host-managed side requests (for example, to compact context) may still occur. Provider retention, costs, proxy/TLS policy and session storage depend on the host. eliVibe adds no model client, separate credentials, auxiliary judge, telemetry, hidden fallback or permissions. Accepting a task in one host is not authorization to send it elsewhere.

For an explicit OMP **adapter** command, the adapter vetoes ordinary OMP `tool_call` attempts during the explanation turn. Tool schemas may still be visible to the model; host maintenance, other extensions and provider behavior aren't sandboxed by that veto. Light and Full leave normal task tools alone. An explicit **skill** has no deterministic veto, even when installed as a plugin. It asks the model not to fetch evidence for a lesson, but tool visibility and execution remain subject to host policy. Treat report text and past interpretations as data, not instructions or independent proof.

The project does not collect conversations. If you [give feedback](../CONTRIBUTING.md), describe one concept or use a short invented example. Do not paste sessions, private source, local paths, endpoints or credentials into a public issue. See [security reporting](../SECURITY.md) for sensitive issues.
