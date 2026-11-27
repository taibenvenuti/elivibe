# Product status and acceptance ledger

[Public v0.1.0](https://github.com/taibenvenuti/elivibe/releases/tag/v0.1.0) is immutable at `fe5ae8a9427b8d25a82b09c6186ab17b95b9882d`. Its [hosted product/native checks](https://github.com/taibenvenuti/elivibe/actions/runs/45996234687) cover the old isolated architecture, **not** the next candidate.

## 0.2.0 review candidate

Decision: [0005](../design/adr/0005-host-managed-teaching-and-distribution.md). Help a reader understand a technical handoff without configuring another inference system. Preserve the report; teach mechanisms and tradeoffs alongside it. Work locally on `feature/host-managed-elivibe`; owner review precedes publication.

| Work | Checkpoint and next evidence |
|---|---|
| Baseline | Public release and clean starting commit confirmed; Linux x64 OMP 19.2.1, Node 24.21.0, npm 11.19.0, uv 0.12.5. |
| Conversation | Ordinary OMP turn path and scoped context guidance replace the side client; tests and real-host acceptance pending. See [integration](integration.md). |
| Distribution | Root manifest now identifies `elivibe@0.2.0`. Git, archives and npm share a regular skill path. Developer scripts moved to `dev/` because OMP scans root `tools/` in installed packages. Actual packed-consumer verification pending. |
| Documentation and participation | Beginner install, commands, compatibility, safety, release guidance, examples and feedback form updated. A fresh reader found the guide didn't create an assistant handoff; the first-use exercise now does, and distinguishes shell commands from commands entered in OMP. |
| Verification | Next: check the integrated candidate on Linux, a native Windows archive install and a short live synthetic example if ordinary host authentication is available. No new provider or human evidence inferred from historical tests. |
| External delivery | No push, PR, remote ref for the candidate, release or registry publication authorized before review. `npm view elivibe version` returned 404; `npm whoami` returned 401. Neither response reserves a name. |

See [development](development.md) for checks, [compatibility](compatibility.md) for support scope and [release](release.md) for distribution gates. Next product evidence: does someone outside the implementation team find a particular explanation helpful, repetitive or misleading? Collect sanitized reader feedback, not transcripts or formal efficacy scores.
