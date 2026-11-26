# eliVibe

Coding agents tell you what they did. **eliVibe helps you understand it.** This experimental, research-informed skill and OMP plugin is for people commissioning coding work, including developers working outside their own domain.

**Technical report:** “After the update, the local cart read back quantity 3. No remote acknowledgement was captured.”

**eliVibe supplement:** “A read-back tells you what the local cart can see. An acknowledgement would give evidence from the other system; what it confirms depends on the protocol. Seeing 3 locally doesn't establish that the remote order changed. The missing acknowledgement doesn't establish that the request failed, either.”

The report remains authoritative. The constructed supplement teaches a distinction without inventing how this cart works. eliVibe does not independently verify work, audit systems, or approve actions. It has not demonstrated improved comprehension or safety.

## Quick start

**Start with the ordinary Oh My Pi (OMP) conversation.** For a report that's already visible, use `/skill:elivibe`. For your next task with the native plugin, enter `/elivibe full` before giving the task. Both use OMP's normal routing and protections; an ordinary turn may send more conversation context than the report alone.

**Manual is the safe idle default:** it sends no extra eliVibe model request unless you explicitly request and authorize one. Manual explanations and Light automation are experimental. Their isolated requests bypass ordinary OMP protection and provider hooks. No cloud route is eligible without positive proof from OMP that it bypasses both proxy layers. Empty proxy environment variables aren't proof. The default TypeSafe Jev judge is therefore usually unavailable, and choosing a local explainer does not make the judge eligible.

**Install:** [Build and link the native plugin from source](docs/installation.md#native-source-install), or [install the standalone Markdown skill](docs/installation.md#standalone-skill) without build tools. The native plugin already includes the skill; don't install a second copy. There is no published bundle linked here.

The native path was exercised with synthetic responses on **OMP 19.2.1 on Linux x64 (WSL2)**. No live-provider compatibility has been verified, and there are no other native adapters. See [compatibility and evidence limits](docs/compatibility.md).

## Modes

| Command | What happens | Additional adapter inference per eligible handoff |
|---|---|---|
| `/elivibe off` | No adapter instructions or side requests. OMP can still discover its installed skills. | None |
| `/elivibe manual` | Keep the ordinary report. Enter `/elivibe` to ask for a distinct supplement. | None automatically; at most one explanation when requested |
| `/elivibe light` | A separately approved judge looks for a meaningful gap, even in a well-written report. Judgment can miss or overselect a handoff. | At most one judgment and, after a positive decision, one explanation |
| `/elivibe full` | Ask the ordinary agent to give its report and a distinct supplement in the same answer. | None beyond normal OMP requests |

`/elivibe status` shows the current mode and choices. Use `/elivibe depth adaptive` (the default) to fit the explanation to the task, `/elivibe depth brief` for the key distinction, or `/elivibe depth detailed` for connected concepts and consequences. Depth changes what you ask the model to explain, not which facts count as evidence. You can also ask for a specific format or say “skip eliVibe for this task.”

Experimental side requests may add cost and latency. The original report stays visible if a request is denied or fails. See [privacy, proxy eligibility and separate approvals](docs/privacy.md) before trying Manual explanations or Light.

[Install, update, roll back, or remove](docs/installation.md) · [Compatibility](docs/compatibility.md) · [Privacy and controls](docs/privacy.md) · [QA and constructed examples](docs/product-qa.md) · [Contributing](CONTRIBUTING.md) · [Release policy](docs/release.md)
