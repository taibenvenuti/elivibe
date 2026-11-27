# Candidate status and acceptance ledger

**Public stable:** [v0.1.0](https://github.com/taibenvenuti/elivibe/releases/tag/v0.1.0), commit `fe5ae8a9427b8d25a82b09c6186ab17b95b9882d`. The [accepted hosted run](https://github.com/taibenvenuti/elivibe/actions/runs/45996234687) applies to that version and its isolated model routes. Its tag and assets are immutable.

**Under review:** branch `feature/host-managed-elivibe`. The reviewed upgrade is **1.0.0**, not the provisional 0.2.0 used in local development trials. v0.1.0 documented a report-only Manual transport, model/judge selection and route grants. The new `/elivibe` deliberately uses the ordinary host conversation, and those controls no longer configure a route. That is a breaking public behavior and disclosure change, not merely an additive feature. The pinned analyzer returned `minor` (0.2.0) for the original six feature/fix commits but `major` (1.0.0) for the intended squash subject `feat(omp)!: explain handoffs in the host conversation`. Main squashes using the PR title. This version decision does not enlarge the tested compatibility surface.

## Review checkpoints

| Gate | Evidence and next action |
|---|---|
| Scope and migration | [ADR 0005](../design/adr/0005-host-managed-teaching-and-distribution.md) preserves the original report, teaches alongside it, and supersedes the side client. Use [installation](installation.md) to migrate; see [privacy](privacy.md) before using ordinary conversation on a report. |
| Independent review | Two fresh code and product/package review contexts examined the actual baseline-to-candidate changes. The packaging review identified the breaking version and time-sensitive instructions embedded in the npm README. The stable README now links to verified routes instead; migration explains resumed Light mode. A fresh reader followed install → fictional task → `/elivibe` → `more`, migration and feedback. |
| Test responsibilities | [Development](development.md#what-survived-the-removal-of-the-side-client) maps the old suite's responsibilities to current command, replay and native checks. New regressions distinguish a missing durable explanation marker from a new ordinary handoff. |
| Local checks | At `440f0f3024253fd86f7955db4ab251364fb96cd5`, `sh dev/check` passed: 59 Python tests, 22 Node tests, 11 release-rule fixtures, type, workflow and documentation checks. Independent review also verified that the new failed-write regression fails with the original adapter. |
| Real model and reader evidence | [Actual synthetic-input model walkthrough](product-qa.md#observed-development-walkthrough): OMP 19.2.1 ACP / `openai-codex/gpt-6.2-astra` at `b85ae4420c`; three same-model turns, no observed tools. No independent reader outcomes. [Earlier Windows archive scope](compatibility.md) does not establish Windows registry or Git-source support. |
| Package and consumer | Offline repacks reproduced the provisional 0.2.0 bytes at `e1354664a2c9b80960c132e5a78ba79b0fa8a9f8` and `d21f8a5`. The 1.0.0 version and README changed package bytes at `64449beca4`; the corrected adapter changed them again at `440f0f3`. At the latter SHA, real Linux x64 OMP 19.2.1 installed the actual packed 1.0.0 from a disposable registry. Fresh install, fixture update, rollback and removal preserved the unrelated registration. The loopback sandbox exercised 27 ordinary synthetic requests, not a live external model. |
| Remote and publication | [Draft PR #2](https://github.com/taibenvenuti/elivibe/pull/2) targets `main`. Only the feature branch and ordinary PR checks are authorized. No merge, tag, release or npm publication. Anonymous public registry lookups for `elivibe` and `latest` returned 404; no authenticated npm publisher was established. A name lookup isn't ownership. [Publication steps and postpublication checks](release.md). |
| GitHub source and hosted CI | [Pinned GitHub install](installation.md#install-the-omp-candidate) passed from a fresh consumer at `440f0f3024253fd86f7955db4ab251364fb96cd5`: resolved archive, discovery, ordinary first use, `more` and clean uninstall. [Product and native CI](https://github.com/taibenvenuti/elivibe/actions/runs/46055740384) both tested this exact PR head after checkout of same-tree synthetic merge `c215dfa8978cc943a84b24e64bfbfdcf85b8c1c1`. For later documentation commits see the [PR checks](https://github.com/taibenvenuti/elivibe/pull/2/checks); final evidence belongs to the actual head, not this earlier run. |

## Review artifacts

Built from the exact Git tree `440f0f3024253fd86f7955db4ab251364fb96cd5`. In local `results/1.0.0/<build-sha>/`, `github/` holds the two archives and their manifest; `npm/` holds the **actual tested tarball**. These are not published assets. All share the same regular canonical skill; `LICENSE` is MIT, no `NOTICE` exists in this tree. The native archive includes manifest, core and adapter; npm includes those plus README (six files). No consumer build scripts, private material or developer dependency tree.

| File | SHA-256 |
|---|---|
| `elivibe-1.0.0.zip` | `450cf51dbf2feae055cdeedacac333270d7a9540744a7a63abe138f566b69059` |
| `elivibe-omp-1.0.0.tar.gz` | `3b5a4a21b8f22cee6d9b76b0ac8fb2982e833c5305ea2bb4fed6d28954cd0840` |
| `SHA256SUMS` | `8dbfc1d120874d7ace6ed0bfb2a704fa1e6feb22457259bb6e5d748b685d4f8b` |
| `elivibe-1.0.0.tgz` | `5954851ee4f7a621eda8ed5d4bffbc63e3e945cabeb807bf7432ffb49947db5c` |

Next product milestone after publication: collect voluntary sanitized feedback about a mechanism a reader could explain afterward, or an explanation that was repetitive or misleading. The [public issue chooser](https://github.com/taibenvenuti/elivibe/issues/new/choose) is available; the candidate's specific form is not on the default branch yet. Pi/Claude are [future channels](compatibility.md), not supported adapters.
