# Pre-merge integration audit — branch → `main`

Run `model1-final-acceptance-premerge` (AXO HYBRID /18), 2026-11-21. Audience: the owner and whoever executes an
approved merge. Read-only audit: **no merge, no push, no tag, no rollback was executed.**

## 1. History

| fact | value |
|---|---|
| `main` = `origin/main` | `bc6ff5e333e32d1d53dc7435fba64fe12b6dd651` (no tag points at it) |
| `merge-base main HEAD` | `bc6ff5e33` → `main` is an ancestor (fast-forward possible) |
| commits `main..HEAD` | 401 (397 up to `/16` + 4 of `/17`; `/18` adds documentation commits only), 5 merge commits, 2026-11-08 → 2026-11-21 |
| merge commits in range | `ba8db5612` (main → /13 branch), `e6a0bb863`, `43670a97c`, `60bba4624`, `6889a31f8` (2026-11-09 integration of parallel OCR/reasoning work) |
| `main` working tree | untracked `docs/evaluation/geometry/runs/post-merge-cleanup-closure/` (6 files, sha256 snapshot taken before /18); no branch file has that path; untouched |

## 2. What would land on `main`

`git diff main...HEAD`: 2,830 files (2,664 A · 139 M · 27 D), +1,669,784 / −56,325 lines, 114.5 MB of tip content.

| area | files | note |
|---|---:|---|
| `docs/evaluation/**` | 2,498 | run evidence /5–/18: 416 PNG, 8 PDF, 2 DOCX; 6 files > 1 MiB (largest 3.3 MB `responses.jsonl`); repository `.git` already 2.9 GB |
| `backend/app/**` | 53 | the product change (below) |
| `backend/tests/**` | 168 (incl. 26 informatics tests deleted in `/13`) | |
| `backend/scripts/**` | 44 (1 deleted) | eval / audit tools |
| `backend/experimental/construction_planner/**` | 14 | Construction /2 prototype, frozen; **no product import** (`backend/app` only mentions it in a comment) |
| `frontend/src/**` | 43 | informatics removal, unit-similarity UI, idempotency fix; covered by vitest 2,345 in T3 |
| `docs/schemas/**`, `contract.py` | 2 | IR lost the informatics vocabulary (`/13` step B) |
| `backend/alembic/**`, `backend/app/persistence/**` | 0 | **no DB migration** |
| canonical docs | 7 | |

Sensitive-name scan of the diff (`.env`, `.db`, `.sqlite`, key/credential files, `.gguf`, `.zip`, `.bin`): **0 files**.
No duplicated live harness (one shared `docs/evaluation/geometry/harness/live-acceptance/`, 0 diff since `c4ae9dd1f`).
CODE_INDEX ownership: `code-index-sync.test.ts` PASS (in T3 and again after the /17–/18 doc edits).

## 3. Contract integrity vs `main`

The branch changes the **shared deterministic core**, not only Model 1:

| component | label (main → HEAD) | diff vs `main` |
|---|---|---|
| TypedFactNext | `typed-fact-next/1` → same | +206/−10, additive (new premise kinds, `math_goal_v2`/`simulation_goal_v2`) |
| bridge | `typed-fact-next-bridge/1` → same | +436/−70 |
| Source Gate / Registry | `geometry-functions/33` → same | +3,768/−421 |
| Planner | `geometry-fact-planner/26` → same | +790/−103 |
| Exact Kernel | `geometry-function-engine/24` → same | engine +3,871/−139; `geometry/expression.py` added (+1,535); `certificates.py` 0 |
| Adapter / envelope | `hybrid-simulation-adapter/4`, `hybrid-route-d-simulation/4` → same | +161/−4 |

Consequence for Option B: the **default `live` (Gemini) route uses the same Source Gate, Planner and Kernel**, so a
merge changes what every user gets, not just operators who turn on local mode. Evidence for the live route on candidate
158: Full T3 (offline fixtures, staging replay, demo replay 5/5, crash surface 6/6). **No live Gemini run** has been made on
candidate 158 (/14–/18 measured local-only with 0 cloud calls; `NEW_LIVE_SMOKE_NOT_MEASURED`; spending quota needs an
owner decision and a registered budget — D7).

Version labels did not move while the code did: they cannot be used to tell `main`'s core from the branch's.

## 4. Product identity chain

| role | commit | tree / note |
|---|---|---|
| product (candidate 158) | `2bb0211a1` | product paths identical at every later commit (`git diff 2bb0211a1 HEAD -- backend/app frontend/src backend/alembic …` = 0) |
| candidate record | `35a17644a` | `EVALUATION_CANDIDATE.json` `commit` field |
| freeze + Full T3 | `b92b68a94` | tree `bdb737bb…`; T3 PASS |
| /17 report | `6789da55a` | docs only (5 canonical docs + run folder) |
| /18 records | this run's commit(s) | docs only; `freeze --verify` PASS at HEAD |
| **merge HEAD** | the `/18` tip, or `b92b68a94` + docs | T3 result belongs to tree `bdb737bb…`; it transfers to the tip only because the diff after `b92b68a94` is docs-only (shown above); docs gate re-run at the tip: 60 passed |

## 5. Merge procedure (only after D1–D4 and an explicit merge permission)

1. Owner records D1 (Option B), D2 (candidate), D3 (measurement), D4 (publication), D7 (live smoke or waiver).
2. Owner tags the rollback point: `git tag pre-model1-merge bc6ff5e33` (local; pushing it is part of the push decision).
3. Authoritative Full T3 on the merge commit per D3.
4. `check_publication_safety.py --range bc6ff5e33..<merge>` exits 0.
5. **Recommended: `git switch main && git merge --no-ff feat/model1-final-acceptance-premerge`** — one merge commit `M`
   whose first parent is `bc6ff5e33`. Fast-forward also works but leaves no single commit to revert.
6. T3 on `main` (smoke at least: identity tests, docs gate, demo replay); push only with a separate permission.

Squash merge is possible but drops the 401 commit identities that `EVIDENCE_INDEX.md` cites (they would need archive
refs, precedent `refs/archive/evidence-index`); it does keep the 5 history-only password blobs off `main`.

## 6. Rollback (corrected)

`/17` described Git rollback as "git revert". With 401 commits including 5 merges that is not one command. The
correct procedures:

**Deployment rollback (fastest, no Git change).** Redeploy the previous known-good release `bc6ff5e33` (tag
`pre-model1-merge`): rebuild the image from that commit (no registry image exists in the repo), keep the database (no
migration on the branch ⇒ the old code reads the same schema), keep the cache table (rows carry `policy_version`;
CACHE 132 never serves `158:route-d` rows and 158 never serves 132 rows). Restore the operator environment
(`HYBRID_ROUTE_MODE` unset ⇒ `live`).

**Git reversal (forward-only, no history rewrite).**

- If merged with `--no-ff` as recommended: `git revert -m 1 M` — one commit restoring `bc6ff5e33`'s tree. Re-merging
  later requires reverting that revert first.
- If fast-forwarded: create one commit whose tree is `bc6ff5e33`'s:
  `git commit-tree bc6ff5e33^{tree} -p main -m "revert: restore pre-model1 tree bc6ff5e33"` then
  `git merge --ff-only <that commit>`. Do not try `git revert bc6ff5e33..main` (5 merge commits need `-m` each and the
  range interleaves).
- Commits made on `main` after the merge: list them (`git log M..main`), revert them first if they depend on merged
  code, then the merge; rehearse on a scratch branch before touching `main`.

**Operational fallback without rollback.** `HYBRID_ROUTE_MODE` stays `live` (Gemini); local modes are opt-in. A missing
or wrong GGUF/runtime gives `503 MODEL_RUNTIME_UNAVAILABLE` / `MODEL_CHECKSUM_MISMATCH` (no-store) while parser-readable
text is still served (`/17` RUNTIME_CAPACITY_REPORT). `ALLOW_LIVE_AI=0` stops live AI. These do not undo the shared-core
changes of §3 — only a rollback does.

## 7. Merge vs public local enablement

| condition | merge code (local mode dormant, `live` default) | enable local mode for public users |
|---|---|---|
| owner D1–D4, D7 | required | required |
| authoritative T3 | required | required |
| publication gate exit 0 | required | required |
| prospective / independent acceptance of the candidate | owner's choice (D2) | **required** |
| Linux llama.cpp pin, hosted + backed-up GGUF, request deadline, multi-process idempotency, target-hardware capacity | not required | **required** (`ISSUE-OPS-LOCAL-SLM-LINUX-RUNTIME-AND-GGUF-PROVISIONING`, `ISSUE-OPS-LOCAL-ROUTE-CAPACITY-AND-DEADLINE`) |

## 8. Merge blockers

1. D1 merge scope not decided (`MERGE_SCOPE_APPROVED = FALSE`).
2. Publication gate BLOCKED: 11 branch entries pending (`PUBLICATION_SAFETY_CLOSURE.json`).
3. Authoritative measurement NOT_VERIFIED (D3).
4. Live default route not measured on the branch (D7).
5. Candidate 158 acceptance NOT_MEASURED (owner may accept the risk under D2 for a dormant-flag merge; not for public local mode).
