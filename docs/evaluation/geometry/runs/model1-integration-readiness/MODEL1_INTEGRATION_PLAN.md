# Local Model 1 (text) — integration plan, rollback and deployment readiness

Run `model1-integration-readiness` (AXO HYBRID /17), 2026-11-21. Audience: the owner deciding whether and how the
local text Model 1 reaches `main`, and whoever executes that decision. **Nothing here has been executed: no merge, no
push, no default change, no deployment.**

## 1. Where things stand

| | value |
|---|---|
| `main` | `bc6ff5e33` (CACHE 132), unchanged by this run |
| branch | `feat/model1-integration-readiness` = `/16` branch + this run; **`main` is an ancestor** (397 commits ahead, 0 behind) ⇒ a merge is a fast-forward, no conflict resolution |
| last accepted candidate | **157** (`4c1b94b61`, freeze `39c95599e`): `LOCAL_TEXT_MODEL1_VERIFIED = TRUE` on Holdout-6 (`/16`) |
| successor candidate | see `FINAL_MASTER_REPORT.md` §4 — the parser routing fix of this run |
| default route | `HYBRID_ROUTE_MODE` unset ⇒ `live` (Gemini). Model 1 runs only when the operator sets a local mode |

## 2. Architecture compatibility (P5 result)

Model 1 replaces only the *extractor* that produces TypedFactNext; everything after it is the same code on both routes.

```
text ─► domain gate ─► Local Parser ─(incomplete)─► v3 verified normalizer ─► Local Parser
                          │ complete                                 │ still incomplete
                          ▼                                          ▼
                    TypedFactNext ◄──── AxoV9 (GBNF-constrained JSON) + grounding validator
                          │            (llama.cpp on 127.0.0.1, one process)
                          ▼
     bridge_v2 ─► Source Gate (registry.kiem_nguon) ─► Planner ─► Registry ─► Exact Kernel ─► Adapter /4 ─► Scene3D
```

| boundary | check | result |
|---|---|---|
| Model output → Typed Facts | AxoV9 output goes through `slm-grounding-validator/6` and is wrapped as a TypedFactNext payload replayed through `run_hybrid_offline` | unchanged contract (`typed_fact_next.py` 0 lines changed since `/13`) |
| Typed Facts → Source Gate | every route reaches `run_typed_fact_next_v2_route` → `registry.kiem_nguon`; there is no path from the SLM to the planner that skips it | preserved |
| Source text the gate verifies | the v3-normalized text (`slm_res.norm_text`), plus the original-source polarity/role guard `_verify_canonical_against_original_source` | design of `/15`–`/16`, unchanged here |
| Planner / Registry | `planner.py` 0 lines changed since `/13`; `registry.py` changed only in Source Gate reading rules (`/13`–`/16`) | compatible |
| Exact Kernel | `simulation/geometry/**` and `certificates.py` 0 lines changed since `/13`; `engine.py` +142/−41 (`/13` §17 unit similarity, §19 point O, `/16` B18 apex placement); no `app.ai` import in `engine.py`, `registry.py`, `planner.py`, `geometry/*` | independent of the model runtime |
| Adapter / Scene3D | `adapter4_route.py` +7 (`scale_policy` for unit-similarity scenes, bound in the result check); frontend geometry domain +40/−3; no model name anywhere in `frontend/src/simulations/domains/geometry` | Scene3D does not know which extractor ran |
| Cache | `ROUTE_D_CACHE_POLICY = "<CACHE_VERSION>:route-d"` is part of every lookup | rows of another candidate are never served |
| Errors | infrastructure failures are HTTP 502/503/504 `INFRASTRUCTURE_FAILURE`, `Cache-Control: no-store`, never a mathematical refusal; learner text contains no internals | verified in `RUNTIME_CAPACITY_REPORT.json` |

Changes `/13` → `/16`, by kind:

1. **Implementation** — parser, v3 normalizer, SLM extractor, adaptive router, Source Gate reading rules, engine
   placement fixes.
2. **Data contract** — the semantic-program IR lost the informatics container vocabulary (`contract.py`, exported
   schemas; `/13` step B, CACHE 150). TypedFactNext and Route D envelopes are unchanged except the optional
   `scale_policy` field.
3. **Trust boundary** — none removed. Added: original-source polarity guard for normalizer rewrites, SLM grounding
   validator, prompt-injection and typo refusals before any rewrite.
4. **Geometry algorithms** — unit-similarity representative scenes (cube / regular tetrahedron without a length,
   no numeric answer), explicit base-centre point O provenance, B18 apex placement order. Kernel arithmetic unchanged.
5. **Interface** — clarification surfacing (`route-d-clarification/1`), frontend idempotency fix (`/13`), unit-similarity
   presentation.

Verdict: `MODEL1_TEXT_ARCHITECTURE_COMPATIBLE = TRUE` — no core redesign needed.

## 3. The decision the owner has to make (P7)

Two standing decisions conflict: OCR/Vision is postponed, and `main` waits for a full Gemini-role replacement.

| | Option A — full replacement first | Option B — scoped text integration |
|---|---|---|
| what merges | nothing until local Vision is verified | the branch, with `live` (Gemini) still the default; Model 1 only behind `HYBRID_ROUTE_MODE=local-only-scoped` |
| what users get | `main` stays at CACHE 132 | the same `live` product as today plus 397 commits of parser, Source Gate, kernel and UI fixes; local text mode available to operators |
| risk | branch drifts from `main`; the release line misses verified fixes | `main` ships code not yet independently validated; local mode needs Windows + a hand-provisioned GGUF (§5) |
| claim allowed | — | "local text Model 1 verified on candidate 157 (team-authored holdout)"; **never** "Gemini replaced" |

The agent does not choose. Without a new written owner decision, **`MAIN_MERGE_READY = FALSE`**.

## 4. If Option B is approved — merge plan

Pre-merge gates (all must be green on the exact commit to merge):

1. Owner decision recorded (Option B, which candidate: 157 or the successor).
2. Publication safety: `check_publication_safety.py --range bc6ff5e33..<commit>` currently reports **12
   `HARDCODED_PASSWORD`** — the synthetic local test-account password in frozen `/10`–`/12` browser tools. Frozen
   evidence is not edited; the owner adds exception entries (owner-only) or approves moving the tools. `main` itself
   carries 96 pending traceback exceptions — the gate is already `BLOCKED` on `main`.
3. Authoritative measurement per `AGENTS.md §2` (clean detached worktree at the merge commit) — currently
   `NOT_VERIFIED`, see §7.
4. `npm run test:full` PASS on that commit; `freeze_evaluation_candidate.py --verify` and
   `lock_cache_identity.py --verify` PASS.
5. `docs` gate (`test_docs_information_architecture.py`) PASS.

Steps: `git switch main && git merge --ff-only <commit>`; T3 again on `main`; then push only with a separate owner
permission. The user's uncommitted folder `docs/evaluation/geometry/runs/post-merge-cleanup-closure/` in the main
checkout must stay untouched (it does not conflict: no branch file has that path).

## 5. Deployment readiness (VPS / zero-setup)

Goal: a learner opens the website; nothing is installed on their machine. Today's state:

| requirement | state | blocker? |
|---|---|---|
| model runtime on the server OS | `LLAMA_CPP_RUNTIME_SPEC` pins **`llama-b12470-bin-win-cpu-x64.zip` / `llama-server.exe`** only; the shipped image is `python:3.12-slim` (Linux). Local mode cannot start in the container | **yes** — needs a pinned Linux asset + sha256 + a test, then a re-measurement (it is a different binary) |
| model artifact provisioning | AxoV9 GGUF has `url = ""`: it exists only in this machine's `%LOCALAPPDATA%\axo-slm` (396,704,736 B, sha256 `73f1484b…`) | **yes** — store it (private artifact store or release asset) and back it up; today a disk loss loses Model 1 |
| process model | one uvicorn process (`Dockerfile` CMD, no `--workers`); one llama-server child, one inference at a time (`Semaphore(1)`), queue limit 4 ⇒ 503 `LOCAL_SLM_BUSY` | design limit, see capacity |
| idempotency | in-process dict (`app/idempotency.py`, ponytail note) — correct only for one process | blocker for multi-worker/multi-host |
| deadline | local route has no end-to-end deadline; each inference is bounded by 45 s | needs a request deadline before public traffic |
| health / readiness | `/api/health` reports `routeMode`, `localSlmReady`, `localSlmModel`, `aiAvailable`; `/api/diagnostics/runtime` reports identity | usable as readiness probe; it also counts the cache table on every call |
| HTTPS, auth, rate limit | accounts + per-user daily quota exist; no reverse proxy / TLS config in the repo | deployment work |
| persistent storage | SQLite default, Postgres supported (`DATABASE_URL`), Alembic migrations — **0 migration changes on the branch** | no |
| observability | per-response `adaptive_telemetry` + stage timings; no metrics export | deployment work |
| auto-restart | llama-server crash recovery is in-process (verified); uvicorn restart needs a supervisor | deployment work |

No number of concurrent students can be promised: target hardware is unknown and unmeasured
(`TARGET_HARDWARE_PERFORMANCE_MEASURED = FALSE`). Measure on the target before any capacity statement; to verify:
CPU model and core count (AVX2/AVX-512), RAM ≥ 2 GiB free for llama + backend, disk for the 397 MB GGUF, OS.

## 6. Rollback

| layer | how | data loss |
|---|---|---|
| code | `main` before the merge is `bc6ff5e33`: `git revert` the merge range forward, or deploy tag `bc6ff5e33` (no history rewrite) | none |
| cache | `ROUTE_D_CACHE_POLICY` is in every lookup: after rollback CACHE 132 never reads 157/158 rows and vice versa; rows stay in the table | none (stale rows are unused, may be pruned later) |
| database | no Alembic revision on the branch ⇒ schema identical, no downgrade | none |
| route | operational kill switch without a deploy: unset `HYBRID_ROUTE_MODE` (back to `live`) and restart; `ALLOW_LIVE_AI=0` stops live AI | none |
| model / runtime | pinned by sha256 (GGUF and llama.cpp zip); a missing or wrong file fails closed as 503 `MODEL_RUNTIME_UNAVAILABLE` / `MODEL_CHECKSUM_MISMATCH` — keep the GGUF backup | none if backed up |
| frontend/backend contract | Route D envelope `/4` unchanged; frontend of the branch reads both | none |

## 7. Measurement compliance (P8)

`AGENTS.md §2`: *"Khi cần xác minh có thẩm quyền, tạo git worktree detached sạch tại commit tương ứng."* The local
`CLAUDE.md` repeats it ("worktree detached sạch"). The rule asks for a **new** detached worktree; the owner's standing
instruction forbids creating one. The shared worktree can give a detached HEAD and a clean tracked tree, but not an
isolated worktree. Therefore `AUTHORITATIVE_DETACHED_COMPLIANCE = NOT_VERIFIED`. Options for the owner:

1. allow one throw-away detached worktree for the final pre-merge measurement (removed afterwards), or
2. amend `AGENTS.md §2` to accept "detached HEAD + clean tree in the shared worktree" as authoritative — the owner's edit,
   not the agent's.
