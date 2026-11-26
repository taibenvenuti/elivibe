# Compatibility

The native target is **Oh My Pi 19.2.1**, Linux x64/glibc on WSL2. It was exercised locally with the real host and synthetic model responses. Native Windows and macOS, other OMP versions, other Linux runners or containers, other CPU architectures and their extraction or symlink behavior are unverified. No live-provider compatibility has been verified. See [what QA does and does not establish](product-qa.md) and the [native smoke procedure](development.md#native-omp-smoke).

| Component | What it needs | Scope |
|---|---|---|
| Standalone skill | One Markdown file and a host that can discover and follow Agent Skills instructions | OMP skill discovery and explicit invocation are exercised locally. Other hosts may be able to read the skill, but none are tested or supported integrations. |
| Portable TypeScript core | A compatible runtime; the caller supplies model operations and their authorization | Designed without OMP APIs. Synthetic core tests are not proof of another harness adapter. |
| Native OMP plugin | The tested OMP host, bundled skill discovery link, and host APIs described in [integration requirements](integration.md) | Only native adapter. Needs lifecycle and source handoff access, session state and commands, model and credential information, and a way to deliver a supplement separately. Side requests have an additional transport boundary. |

## Isolated transports

Eligibility is about the actual API and route, not the name of a provider in OMP's registry. Only the following transport shapes are eligible for explicitly authorized manual/light requests:

- **OpenAI-compatible Chat Completions (`openai-completions`):** an exact `POST` to the registered base's `/chat/completions` route, using certificate-verified HTTPS or deliberately configured, keyless HTTP on literal `127.0.0.1` or `[::1]`. The endpoint must accept standard non-streaming JSON with the catalog model ID and `max_tokens`; this client does not apply OMP compatibility wrappers, provider hooks, or custom headers. A supported HTTPS route uses a plain registry bearer credential or no credential, not an opaque credential envelope.
- **TypeSafe Jev, judgment only:** a typed request to the fixed HTTPS `/v1/systemone` endpoint with an authorized bearer credential, only if the [proxy rule](privacy.md#proxy-eligibility) also passes. As a public remote destination, it is usually unavailable under that rule. Jev is not an explanation transport, and choosing a local explainer does not change the judge's eligibility. Synthetic fixtures do not verify the live service.

**Proxies:** isolated requests do not implement proxy forwarding. Both explanation and judgment (including Jev) refuse if a current proxy setting applies: `PI_PROXY_<NORMALIZED_PROVIDER>` for the actual destination provider, `PI_PROXY`, `ALL_PROXY`/`all_proxy`, or `HTTPS_PROXY`/`https_proxy` for HTTPS and `HTTP_PROXY`/`http_proxy` for HTTP. OMP's provider key uses uppercase with each character outside `A–Z` and `0–9` replaced by `_`. An unrelated provider key does not block the route; `NO_PROXY`/`no_proxy` and private addresses never override a configured setting. With none configured, the route is accepted only on host proof of bypass. See [proxy eligibility](privacy.md#proxy-eligibility) for the full rule, effect and alternatives.

Unsupported APIs (including `pi-native`), LAN or hostname HTTP, URL credentials, query strings, fragments, route escapes, redirects and HTTPS with certificate verification disabled fail closed. Do not downgrade to HTTP, disable a required proxy or remove an organizational security hook to make a route eligible. Use `/elivibe full` for future tasks or `/skill:elivibe` in the ordinary OMP conversation, where the host manages routing and protections. The local exercise uses synthetic providers; it does not certify named commercial providers or prove live auth, cost, latency, retention, or model behavior.
