# Release status and evidence

**Public stable:** [v1.0.0 on GitHub](https://github.com/taibenvenuti/elivibe/releases/tag/v1.0.0), published 2026-11-27 (release ID `461018452`), and [elivibe@1.0.0 on npm](https://www.npmjs.com/package/elivibe/v/1.0.0). The signed annotated Git tag peels to `caf8c089cad3a67d242d0eaa15329fca117a66a8`. See the [verified installation routes](installation.md).

## Cross-harness release candidate

Base: `15d6d849677b1509396352ff3e5348a4bff33852`, [green main CI](https://github.com/taibenvenuti/elivibe/actions/runs/46066913459). Branch: `feat/cross-harness-skills`. The pinned analyzer evaluated the three docs commits since `v1.0.0` plus the proposed squash `feat(skills): support Codex and Claude Code`: **minor → 1.1.0**. This is not a published version.

| Gate | Current evidence |
|---|---|
| Baseline | Remote `main` and the peeled tag matched the revisions above; GitHub listed the three v1.0.0 assets and npm `latest` resolved to 1.0.0. |
| Codex | CLI 0.162.1 available on Linux x64. Actual explicit invocation with implicit selection disabled, distribution, lifecycle and focused review pending. |
| Claude Code | CLI 2.1.291 available on Linux x64. Runtime and review pending the Codex gate. |
| Shared distribution and public docs | Integrated native regression, packed README, release rehearsal, fresh-reader review, draft PR and remote acquisition pending. No directory submission or release authorized. |

## v1.0.0 release record

**Breaking change:** v1.0.0 uses the ordinary host conversation for teachable handoffs and no longer offers v0.1.0's isolated report routes, independent model/judge selection or route grants. This changes what can reach the model. The pinned analyzer selected `major` for the reviewed squash subject `feat(omp)!: explain handoffs in the host conversation`. See [privacy](privacy.md) and [migration](installation.md#move-from-a-v010-linked-install).

**Previous release:** [v0.1.0](https://github.com/taibenvenuti/elivibe/releases/tag/v0.1.0), commit `fe5ae8a9427b8d25a82b09c6186ab17b95b9882d`. Its [accepted hosted run](https://github.com/taibenvenuti/elivibe/actions/runs/45996234687) applies to that version and its isolated model routes. Its tag and assets remain unchanged.

## Release checks

| Gate | Evidence |
|---|---|
| Scope and migration | [ADR 0005](../design/adr/0005-host-managed-teaching-and-distribution.md) preserves the original report, teaches alongside it, and supersedes the side client. Use [installation](installation.md) to migrate; see [privacy](privacy.md) before using ordinary conversation on a report. |
| Independent review | Fresh code and product/package reviews examined the baseline-to-candidate changes. Review identified the breaking version and time-sensitive install instructions embedded in the npm README. Migration explains resumed Light mode. A fresh reader reviewed the install, fictional handoff, follow-up, migration and feedback journey; that is not a reader outcome study. |
| Test responsibilities | [Development](development.md#what-survived-the-removal-of-the-side-client) maps the old suite's responsibilities to current command, replay and native checks. New regressions distinguish a missing durable explanation marker from a new ordinary handoff. |
| Protected merge and hosted CI | [PR #2](https://github.com/taibenvenuti/elivibe/pull/2) was squash-merged from `577aca73e8f5a09e5b03c1a9161e2b162bc65a0f` with an identical tree. Both the product and native jobs passed on the [actual release commit's main push](https://github.com/taibenvenuti/elivibe/actions/runs/46060633972). |
| Real model and reader evidence | [Actual synthetic-input model walkthrough](product-qa.md#observed-development-walkthrough): OMP 19.2.1 ACP / `openai-codex/gpt-6.2-astra` at `b85ae4420c`; three same-model turns, no observed tools. No independent reader outcomes. [Earlier Windows archive scope](compatibility.md) does not establish Windows registry or Git-source support. |
| GitHub source | Fresh OMP 19.2.1 on Linux x64 installed both the full release SHA and exact public `v1.0.0` tag. The tagged archive matched the reviewed files. Discovery, ordinary first use, `more`, and clean removal passed with synthetic replies. |
| Public archives | Independent anonymous downloads matched the verified draft assets and checksum manifest. On OMP 19.2.1, Linux x64, both the linked native archive and the standalone skill passed discovery, first use and removal, preserving unrelated registrations and files. The native and fixture registry checks exercised 27 isolated ordinary synthetic requests; this was not a live-provider trial. |
| Public npm | Anonymous pinned and `latest` lookups resolved to `1.0.0`. Registry integrity and the canonical download matched the approved tarball. A fresh unauthenticated profile on OMP 19.2.1, Linux x64, passed installation, command and skill discovery, Manual/Light/Full behavior, bare `/elivibe`, `more`, and removal without disturbing an unrelated plugin. The run used 21 synthetic requests, not a live provider. Fixture update and rollback passed separately in a disposable registry. |

## Verified artifacts

The three public GitHub assets and the public npm tarball were built from the exact release commit, not the later documentation closure. All distributions use the same regular canonical skill and MIT license. The native archive includes the manifest, core and adapter; the npm tarball also includes the release commit's README. The npm tarball is not a GitHub asset.

| File | SHA-256 |
|---|---|
| [elivibe-1.0.0.zip](https://github.com/taibenvenuti/elivibe/releases/download/v1.0.0/elivibe-1.0.0.zip) | `450cf51dbf2feae055cdeedacac333270d7a9540744a7a63abe138f566b69059` |
| [elivibe-omp-1.0.0.tar.gz](https://github.com/taibenvenuti/elivibe/releases/download/v1.0.0/elivibe-omp-1.0.0.tar.gz) | `3b5a4a21b8f22cee6d9b76b0ac8fb2982e833c5305ea2bb4fed6d28954cd0840` |
| [SHA256SUMS](https://github.com/taibenvenuti/elivibe/releases/download/v1.0.0/SHA256SUMS) | `8dbfc1d120874d7ace6ed0bfb2a704fa1e6feb22457259bb6e5d748b685d4f8b` |
| [elivibe-1.0.0.tgz](https://registry.npmjs.org/elivibe/-/elivibe-1.0.0.tgz) | `5954851ee4f7a621eda8ed5d4bffbc63e3e945cabeb807bf7432ffb49947db5c` |

The release record above is historical. The next product task is the cross-harness acceptance work at the top of this ledger, not reader recruitment.
