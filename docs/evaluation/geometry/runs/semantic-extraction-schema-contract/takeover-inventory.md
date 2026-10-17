# Claude takeover inventory

2026-10-17; worktree `.superpowers/worktrees/semantic-extraction-v3`; branch `research/semantic-extraction-v3`; HEAD `cf6a2d234f6483d68c5163658196b4508637d831`.

## Initial working tree

Tracked modified: none. Staged: none. Untracked source/scripts: none. Untracked research files (all under `inputs/heldout/`):

| File | Bytes | SHA-256 (original bytes) | Role |
|---|---:|---|---|
| authoring.md | 3221 | d5b329a16216535897cb60be615d89f07e722d8c71c89a34100b0910f1f89f98 | Independent corpus author's provenance |
| corpus.json | 27062 | 23f9ea9c4ec2f41b2418f41afb4dbca9d7c8c9637a4e21726344683f6d37b9ae | Fresh held-out sources/requests |
| oracle.py | 13641 | 0f4a281ec2911a0c30fd89bd14c4d3388a6e19efb60c48edd5a589dda0ef3875 | Independent mathematical oracle |

Copied without editing to the main checkout's Git-ignored `.superpowers/preserved/semantic-extraction-v3-takeover-2026-10-17/` with `inventory.json`. No loss/revert/deletion. No raw provider receipt, approval, secret or generated manifest in the initial v3 diff.

## Committed work and interrupted tasks

| Component | Takeover state | Evidence |
|---|---|---|
| Research kind/goal response schema | DONE_UNVERIFIED | ec0b6a24; `backend/app/ai/fact_extraction.py`, schema tests |
| Research contract arm switch | DONE_UNVERIFIED | c932580f; flat remains default |
| Paired flat/v3 runner | DONE_UNVERIFIED | cf6a2d23; runner tests |
| Grounding safety follow-up | WAITING_REVIEW | e3827c00 on separate `integration/extraction-v2-safety`, refreeze 330a222a; not yet on v3 |
| Original independent reviewer | WAITING_REVIEW | Agent a96859fba94d4c15e ends 10:22:59Z with session limit; no final verdict |
| Fresh corpus/oracle author | DONE_UNVERIFIED | Agent a7f3086e6996f6c61 produced preserved three files |
| Original gold encoder | WAITING_GOLD | Agent aade312cbb5561179 ends 10:22:28Z with session limit, no output files |
| V3 protocol/preregistration/approval identities | NOT_STARTED | Not present at takeover |
| V3 candidate freeze/final T3 | NOT_STARTED | Existing candidate metadata belongs to earlier safety work |
| Live/integration | BLOCKED_APPROVAL | User requires new explicit GO for each; LIVE_NOT_AUTHORIZED |

Original session `cd3501fd-bbad-487d-90b7-aed7575abeea` ends 10:22:29Z with session limit. Only task messages and assistant commentary were inspected; raw model manifests were not copied. Fresh reviewer contexts now handle v3 and safety; a separate encoder authors gold.

## Other working trees/processes

Main checkout's untracked `frontend/public/` untouched. Safety worktree has uncommitted EVIDENCE_INDEX/handoff/integration documentation; untouched. Other worktrees (Scene3D, contract-driven composition, v2) untouched.

Claude processes still exist as Chrome native host and VS Code stream host. Identified Node processes are Playwright and the main frontend Vite server. No Python job observed; original task logs and the three file mtimes are unchanged since the limit. No old process was terminated. Only the resumed encoder may write its two new assigned files; parent preserves original held-out files. Any observed concurrent source mutation stops overlapping writes.

## Second takeover: Codex → Claude (2026-10-17 20:23 +0700)

Codex's sections above are kept unchanged. At takeover: HEAD `13c0f157`, `main` = `origin/main` = `4abc4afb`
(already merged into this branch at `49779a13`), 0 tracked modifications, 0 staged, 11 untracked files, all in this run directory.
The three preserved author files were re-hashed and are byte-identical to `.superpowers/preserved/semantic-extraction-v3-takeover-2026-10-17/`.
Gold SHA-256 matches the encoder's report (`ea33013a…`, `1b633b3c…`).

Codex session (local 19:56–20:03), reconstructed from its own transcripts:

| item | state at takeover | evidence |
|---|---|---|
| safety fix e3827c00 on v3 | DONE_UNVERIFIED | cherry-picked as `0507cb01` |
| merge current main | DONE_VERIFIED | `49779a13`; candidate conflict resolved to the older freeze, refreeze still pending |
| v3 reviewer findings 1–3 (+ L4 partly) | DONE_UNVERIFIED | `13c0f157`; RED 17 failures → GREEN 381/385 in scratch logs |
| v3 re-review of the fixes | WAITING_REVIEW | the reviewer's reply is encrypted in the transcript and cannot be read, so a fresh review is needed |
| safety review (NO-GO, prism-rightness blocker) | WAITING_REVIEW | fix present; the blocker has not been re-reviewed |
| held-out gold | DONE_UNVERIFIED | 24 cases / 49 requests / 148 facts; AI-authored, not human-validated |
| gold audit | WAITING_REVIEW | auditor interrupted without a verdict |
| protocol assembly/lock scripts | PARTIAL | draft prepare runs; the selfcheck failed on a cross-drive `relpath`; NOT_LOCKED |
| candidate refreeze, offline results, T3, report | NOT_STARTED | — |

Processes: no writer to this worktree. The Codex app-server was idle (last write 20:03). The running pytest and
`measure_goal_composition.py` belong to Gemini (Antigravity) in `contract-driven-goal-composition`. Nothing was terminated
except Claude's own exploratory runs.
