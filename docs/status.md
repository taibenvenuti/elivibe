# Product status and acceptance ledger

**Published:** [v0.1.0](https://github.com/taibenvenuti/elivibe/releases/tag/v0.1.0), at `fe5ae8a9427b8d25a82b09c6186ab17b95b9882d`. Its [hosted checks](https://github.com/taibenvenuti/elivibe/actions/runs/45996234687) cover the earlier architecture. Do not move this tag or replace its assets.

**Local review:** `feature/host-managed-elivibe`, candidate `elivibe@0.2.0`. Final packaged runtime: `e1354664a2c9b80960c132e5a78ba79b0fa8a9f8`. This is **not** a public GitHub source ref, npm release, or GitHub release. From the local checkout `omp plugin link "$PWD"` registers the package; start a new OMP session, finish a task and enter `/elivibe`. For the archive-only public version, use the [version-specific first-use guide](installation.md#try-the-published-release).

## Acceptance

| Gate | State | Evidence or remaining action |
|---|---|---|
| Scope and intent | PASS | [ADR 0005](../design/adr/0005-host-managed-teaching-and-distribution.md), one canonical skill, original report plus separate interpretation. The report is not independent proof. |
| Zero-configuration Manual | PASS — local | Real OMP installed the exact npm tarball via a loopback registry; an ordinary task and bare `/elivibe` used the same host session without eliVibe credentials, grants or configuration. Synthetic replies establish routing; [model walkthroughs](product-qa.md) are separate observations. |
| Optional configuration | PASS | Clean profile defaults to Manual/auto. No auxiliary client or judge. Help/status/settings don't send an explanation request. Old routing and approval fields do not grant authority. |
| Commands | PASS | Bare, focused, `explain`, `more`, malformed controls, missing source, busy state and text fallback exercised. In a real OMP 19.2.1 terminal at `b85ae4420c`, Escape closed settings with Manual/auto unchanged; selecting `depth brief` changed status to Manual/brief. No model prompt or loopback connection. |
| Discoverability | PASS | Source and packed consumer discovery: one `/elivibe` extension and one explicit-only `/skill:elivibe`. Native terminal completion showed `settings`, `status` and `depth brief`. No onboarding wizard. |
| Modes and opt-outs | PASS | Native payload inspection covered default Manual, Off, Light/Full in ordinary turns, depth and strict-format opt-out. Explicit skill expands; absent from automatic model catalog. Output quality still depends on the model. |
| Follow-up continuity | PASS | Native assertions compare original assistant message, prior response and selected source/interpretation positions through questions and `more`. No automatic second request. A newer tool-free report and an older teaching pair remain distinct. |
| Lifecycle and host policy | PASS — tested cases | Session/branch/compaction, changed active model, cancellation, rewritten prompt refusal and replay ambiguity covered by adapter tests. Native wire verifies guidance as host policy, not user input. A write attempted by the synthetic model was vetoed on an explanation; ordinary coding turns could still write. Schemas can remain visible; not a sandbox guarantee. |
| Teaching quality | PASS — live example, not efficacy | [Constructed cases](qa-examples.md) and [actual ACP output](product-qa.md#observed-development-walkthrough) are separately labeled. At `b85ae4420c`, `openai-codex/gpt-6.2-astra` explained the producer/broker boundary; `more` distinguished the two crash states. Final mention/cancellation edge changes were tested with fixtures, not another live run. No independent reader outcome. |
| GitHub package | PASS local / BLOCKED remote | Clean full source export registered through OMP with no build or developer tools. Actual `github:` install awaits a reviewed, authorized remote ref. |
| npm package | PASS local / BLOCKED public | `npm pack --offline --ignore-scripts`; actual six-file tarball installed through OMP's registry resolver. Public lookup returned 404 and account check 401 on 27 November 2026. No name reservation or publishing rights established. |
| Artifact consistency | PASS | `dev/package.py rehearse`, licensed `build`/`verify`, actual npm tar listing and file comparisons across checkout, native archive, npm and standalone ZIP. Regular skill file; MIT included. |
| Upgrade/removal | PASS — local | OMP registry install/uninstall; previous synthetic version → 0.2.0 → previous; fresh discovery after removal. Unrelated registration and user edits in linked directory survived. [Windows archive-link scope](compatibility.md) is narrower. |
| Tests and CI | PASS local / BLOCKED hosted | Local product checks include 59 Python tests, 20 Node tests, strict TypeScript, docs/workflow checks and 11 release rules. Final packaged runtime: OMP 19.2.1 Linux x64 under WSL2, 27 synthetic ordinary streaming requests in a loopback-only sandbox. No hosted run for this candidate. |
| Docs and context | PASS | Fresh reader located installs, commands, support limits, developer checks and next task. Fixed the missing first assistant handoff and shell/session confusion. Independent review led to exact-commit npm packing, withholding a copyable unowned npm install, and stricter handling of host-expanded prompts and interrupted history. |
| Participation | PASS local / BLOCKED public form | Existing public [issue chooser](https://github.com/taibenvenuti/elivibe/issues/new/choose) accepts reader feedback without tooling. Candidate includes a sanitized feedback form; it appears after merging. [Private security reporting](../SECURITY.md) is separate. |
| Future channels | PASS documentation / DEFERRED integrations | [Pi and Claude matrix](compatibility.md) separates skill trials, native support, eligibility and submission. No listing or extra adapter claimed. |
| External delivery | BLOCKED | Owner review first. No new remote branch, PR, hosted SHA, authenticated preview, tag, GitHub assets or registry version. Follow the [destination gates](release.md#destination-gates--do-not-conflate-them) in order. |

## Candidate bytes (SHA-256)

Built from the packaged runtime commit above, including the reviewed README. The exact-commit export prevents local changes from entering the npm tarball. Store GitHub assets separately from the npm tarball.

| File | SHA-256 |
|---|---|
| `elivibe-0.2.0.zip` | `450cf51dbf2feae055cdeedacac333270d7a9540744a7a63abe138f566b69059` |
| `elivibe-omp-0.2.0.tar.gz` | `9693bfd9f601d3e5e0a0b61f383d3d23d0b8f71edfb04e78466ed1d8bf0589c6` |
| `SHA256SUMS` (GitHub archive manifest) | `1f602093aeb9df0bd61ccd51a5396255bb389c8f22c8db8260f13097487f0afd` |
| `elivibe-0.2.0.tgz` (npm) | `26e61517146e9322d21a348899e86fe8b92675170a97b14efba52770adb5b2a6` |

Rebuild from the exact approved main SHA after review and check the bytes before release. Building, an authenticated preview, GitHub publication and npm publication are independent states. Next product milestone: gather a few sanitized reader reports about concepts they could explain afterward, particularly where `more` adds a new distinction rather than repeating the handoff.
