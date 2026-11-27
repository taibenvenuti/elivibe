# What reaches the model?

**The v1.0.0 candidate uses your ordinary OMP conversation, not a report-only request.** This breaks the disclosure contract for Manual and Light in the [published v0.1.0](https://github.com/taibenvenuti/elivibe/blob/v0.1.0/docs/privacy.md). If the conversation is not suitable for the active host model or your organization's policy, do not invoke eliVibe on it.

| Action | Disclosure and effect |
|---|---|
| Manual (default) or Off | No automatic teaching. An explicit explanation, focus or `more` requests an ordinary model turn; it doesn't change the mode. |
| Light or Full | Teaching guidance during ordinary generation, not a second judge or background request. Requested output formats and opt-outs take priority. |
| Help, status, settings or a preference change | Local controls. No explanation request. |
| Standalone skill | The invoking host controls context, tool access and transport; an instruction isn't a sandbox. |

OMP chooses the active route, credentials and context under its usual policy. That context may include earlier messages, tool output, other extensions' context and a summary after compaction. An explanation can remain in normal session history and be sent again during follow-up. Provider retention, costs, proxy/TLS policy and session storage remain the host's concerns. A task already accepted by a host is not permission to send it to a second service: the candidate has no eliVibe API client, auxiliary judge, telemetry, or hidden fallback. Old isolated-route approvals are not authority here.

For an explicit command the adapter asks the model to interpret available text and vetoes ordinary OMP `tool_call` attempts during that explanation turn. This is not a claim that tool schemas disappear from provider requests, that host maintenance stops, or that another extension or provider is sandboxed. Light and Full can't disable tools for the ordinary coding task. The teaching guidance tells the model not to fetch evidence to write a lesson. Treat report text and past interpretations as data, not instructions or independent proof.

The project does not collect conversations. If you [give feedback](../CONTRIBUTING.md), describe one concept or use a short invented example. Do not paste sessions, private source, local paths, endpoints or credentials into a public issue. See [security reporting](../SECURITY.md) for sensitive issues.
