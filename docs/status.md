# Product roadmap

**Mission:** help people using coding agents understand what the agent accomplished, what the evidence supports, and what to do next. One portable methodology, with a harness-independent core and native integration where it provides useful control. Not a service or an independent verifier.

## Experimental v0.1.0

The [skill](../skill/elivibe/SKILL.md) is independently usable. OMP is the only native adapter. The [architecture decision](../design/adr/0004-conceptual-explanation-and-native-integration.md) explains why eliVibe teaches alongside the technical report. Synthetic responses in a real host test show how the integration operates, not how a live provider behaves or whether readers understand more.

Prioritize [everyday use and feedback](product-qa.md#qualitative-walkthrough): does a supplement explain something the report leaves implicit, or does it just repeat the report? Favor fixes to activation, evidence preservation, setup and controls. Keep experiments with Manual and Light within the documented [privacy and transport limits](privacy.md). Defer extra modes, harnesses, telemetry and formal efficacy studies.

Use the [development checks](development.md) and [compatibility limits](compatibility.md) when evaluating a revision. A local build is not a published release; see the [release policy](release.md).
