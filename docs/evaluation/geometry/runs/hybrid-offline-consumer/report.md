# Session 5 report — Hybrid V2 offline frontend consumer (`hybrid-offline-consumer`)

Authorization `GO_SESSION5_HYBRID_V2_OFFLINE_CONSUMER_RESEARCH`. Classification `OFFLINE_DEVELOPMENT_EVALUATION_NOT_BLIND`.
Provider calls 0. Codex implemented until its usage limit; Claude Opus 5.5 took over in the same worktree
([`SESSION5_TAKEOVER_CHECKPOINT.md`](SESSION5_TAKEOVER_CHECKPOINT.md)). Final status:
**`SESSION5_READY_FOR_OWNER_GO_MAIN_REVIEW`** (see §10 for what that does and does not cover).

## 1. What Codex completed before the limit

- P0 audit of the 22 preserved logs: [`SECURITY_AUDIT.md`](SECURITY_AUDIT.md) → `REMOTE_PUSH_SECURITY_BLOCKED` (one raw traceback in an inherited blob; history unchanged).
- P1/P2 consumer: commit `56507602` — `/4` identity, section provenance/closure and refusal checks in `hybrid-preview-adapter.ts`; `adapter4-consumer.test.tsx`; browser harness `check-adapter4-browser.mjs`.
- P3: fresh export of the 47-case grammar through real Adapter /4 (`results/fixtures.json`, 22 served + 25 refused); browser attempts 1–5 (attempt 5 PASS on an uncommitted harness).
- P4/P5: scoring seam `extraction_scoring.py` + tests, replay `results/extraction-replay.json`, [`E2E_EXTRACTION_READINESS_UPDATE.md`](E2E_EXTRACTION_READINESS_UPDATE.md), [`HYBRID_V2_REMAINING_GAPS.md`](HYBRID_V2_REMAINING_GAPS.md).
- P6 partial: [`SAFE_WORKSPACE_CLEANUP_REPORT.md`](SAFE_WORKSPACE_CLEANUP_REPORT.md), `results/workspace-inventory.json`, backend targeted receipts.
- Not done: typecheck, `code-index-sync`, docs gate, independent review, freeze, Full T3, report/handoff, indexes; harness fix and 35 evidence files were uncommitted.

## 2. What Claude added

| commit | content |
|---|---|
| `922e8979` | preserved Codex's uncommitted harness fix + evidence; takeover checkpoint |
| `2f4be5a7` | `CODE_INDEX` entries (code-index-sync was red); `run_check.py` wrote withheld raw failure logs to an unignored `<cwd>/.superpowers` — now repo-root store, test proves it |
| `12a56461` | review round 1 fixes (provenance rule per kind, certificate-less sections, dangling depends, no-throw boundary, empty closure rule, `″`); 11 new red-first tests + 25 refusal fixtures in vitest; harness independent of `entitiesPresentAt` for section parts; `tree_clean` |
| `e090af1c` | review round 2 fix (through-point provenance, `formation.visible_ids`); harness per-index bound; **product commit** |
| `9f06ed2b` | candidate re-freeze (separate commit) |
| `478d50e8` | authoritative browser acceptance at the frozen candidate |

**Correction to the checkpoint** (file left as written): it says attempts 3–4 failed because the old harness flagged
*solid* faces/edges. Attempt 3 did (`khoi_S_ABCD::face:0`…); attempt 4 flagged a *section* vertex (`td_sp::vertex:0`).
The `entitiesPresentAt` change fixed both, and was too broad for section parts — closed in `12a56461`/`e090af1c`.

## 3. Does Adapter /4 have a working frontend consumer?

**Yes, offline.** `docPhanHoiHybrid` accepts a `hybrid-route-d-simulation/4` wrapper, verifies identity
(`hybrid-simulation-adapter/4`, `typed-fact-next/2`, `registry.kiem_nguon`), answer↔`kq_` binding and unit, and checks
every section against the scene (provenance per planner rule, source edges, closure certificate = scene polygon,
plane-only only without a derived solid). Refusals keep no scene and must match `reason_code`. The view is re-checked in
`validateEnvelope`, then rendered by the existing `Scene3DExplorer` — no new renderer, no geometry computed in the
frontend. **No backend endpoint produces the `/4` wrapper** (`hybrid_preview.py` still emits wrapper `/1`;
`adapter4_route.py` produces `route_d` only) — by design while Hybrid is NO-GO; fixtures are injected into the store.
Final answers stay hidden in the learner UI (simulation-first policy); they are read only through a test-inserted
operator readout.

## 4. Browser acceptance

**PASS** — [`results/browser-final-9f06ed2b/receipt.json`](results/browser-final-9f06ed2b/receipt.json): source
`9f06ed2b` (candidate), `tree_clean: true`, harness `0a7cce8c…`, Chrome headless/SwiftShader, Vite dev on source.
94/94 rows = 47 fixtures × {1440×900, 390×844}; 0 page errors, 0 console errors, 0 forbidden requests.
Coverage: 22 served (pyramids + prism, all with sections; 14 volume-ratio, 12 residual-volume, 1 area; 4 with
`DERIVED_FRESH` intersections; 1 plane-only prism section; 17–22 construction frames each) and 25 refusals (10 codes).
Per frame: no missing dependency, no early/unknown/duplicate object, no early answer, section progress per
`geometry_progress`, open sections unfilled with no face and no vertex ahead of edges; section raster pixels;
selection/highlight keeps dash policy; derived points shown as *Điểm dựng phụ*; refusals: canvas detached, learner
message shown, no code or internal name leaked; no horizontal overflow. Also PASS at `12a56461`. Screenshots are not
the math authority; human visual review **NOT_APPROVED** (owner only).

## 5. Geometry or source-semantics regression?

None found. `backend/app` unchanged vs base; measured system `413ee525…` (116 files) identical before and after.
Full T3 backend 11572 passed (same count as Session 4B candidate). The consumer change is stricter only: 0 false
refusals on the 22 served /4 fixtures, the 25 refusals and all /2 contract fixtures.

## 6. What E2E extraction still lacks

Unchanged from Codex's [`E2E_EXTRACTION_READINESS_UPDATE.md`](E2E_EXTRACTION_READINESS_UPDATE.md): three tracks kept
separate — TypedFacts V2→Scene3D (development offline evidence, this run); NL→TypedFacts V2 (**quality UNKNOWN**, no
eligible provider V2 output: archived 44/44 are extraction failures); full NL→Scene3D (**NOT_MEASURED**). Missing:
appointed independent curator and sealed holdout, a provider transport/model/prompt lock, budget/stop rules and an
owner GO for live. Gaps the consumer does not close: `/4` wrapper producer, negation/conditional expressibility in V2,
planner/kernel stage timing. The 25 refusal envelopes are synthesised through `classify_refusal` by
`export_consumer.py`, not by a product envelope builder; `extraction-replay.json` has no execution receipt.
Failure classes stay distinct (extraction / source mismatch / missing premise / planner / kernel; renderer only after a
served scene).

## 7. Tests run (this session, exit codes)

| check | commit | result |
|---|---|---|
| typecheck `tsc -b` | 2f4be5a7 · 12a56461 · e090af1c | exit 0 ×3 (`results/takeover-build`, `review-fix-build`, `review2-fix-build`)¹ |
| targeted vitest | pre-index | exit 1 — `code-index-sync` red (missing index entry) |
| targeted vitest | after fixes | exit 0 — 180, 242, 245 passed |
| new consumer tests on pre-fix adapter (red baseline) | 2f4be5a7 / 12a56461 | 11 and 3 failing, as intended |
| docs IA gate | 2f4be5a7 | exit 1 — `test_inv_20` (candidate stale) → resolved by freeze |
| `test_run_check.py` | 2f4be5a7 | 1 passed |
| browser acceptance | 12a56461 · **9f06ed2b** | PASS 94/94 ×2 |
| freeze `--verify` | 9f06ed2b, after T3 | exit 0 MATCH |
| **Full T3** `full-gate.mjs` | **478d50e8** | **exit 0 `FULL_PRODUCT_GATE_PASS`** — pytest 11572 passed / 1 skipped / 2 deselected / 15 xfailed; vitest 73 files / 1238; build; demo 5/5; crash surface 6/6 — [`verification/full-t3/execution.json`](verification/full-t3/execution.json) |

¹ `run_check.py` records `git rev-parse HEAD`; receipts taken on a dirty tree before commit name the parent commit.
Codex's earlier receipts (backend targeted 281 passed, scoring 15 passed, default isolation) are in §1 / `results/`.
Not run: `frontend/scripts/*.node-test.mjs` (no harness touched has one), live/provider anything.

## 8. Independent review

[`verification/independent-review.md`](verification/independent-review.md): round 1 `PASS_WITH_FINDINGS` (3 MAJOR),
round 2 `PASS_WITH_FINDINGS` (1 MAJOR), **round 3 `PASS`** at `e090af1c`. All MAJOR fixed with red-first tests.
Disclosed ceilings: `STATED_UNNAMED` vs `DERIVED_FRESH` indistinguishable in the scene; coordinated multi-field scene
fabrication is not detectable by a consumer that computes no geometry; `REUSED_INTERSECTION` unconstrained.

## 9. Identity

Branch `research/hybrid-session5-offline-consumer`, base local main `3f6d7375`. Product commit `e090af1c`; candidate
freeze `9f06ed2b` (`product_commit_sha = e090af1c`, measured `413ee525d20874aa346b13df7e51019266f7d4701af56719c2a2ee736266b5df`,
116 files, `cay_lam_viec_sach: true`); T3 target `478d50e8`; HEAD = the docs commit recording this report.
Invariants held: `LLM_ONLY`, `flat`, Hybrid NO-GO, `ALLOW_LIVE_AI=0`, `CACHE_VERSION=127` (no bump: no prompt/policy
change), `MAX_MEMORY_DECLARATIONS=32`. No merge, no push, no history rewrite.

## 10. Ready to merge into main in disabled state?

Technically **eligible for owner GO-main review**: product change is frontend-only and stricter, Full T3 PASS at the
candidate, browser PASS at the candidate, review PASS, defaults untouched, no activation path added. Not covered:
owner visual approval, remote publication (still `REMOTE_PUSH_SECURITY_BLOCKED` by the inherited traceback blob),
any NL extraction or live claim. Merge/push need separate owner authorization.

## 11. Worktrees and disk D:

Retained: this Session 5 worktree (only one created; no new worktree by Claude). No other worktree, branch or orphan
touched; ACL-locked `hybrid-backend-s1` untouched. Vite :3115 (Session 5's own) stopped.
**Reclaimed: 0 bytes.** Deleting Session 5's own preserved/rebuildable temporaries was **denied by the permission
prompt** and left for the owner: `frontend/dist` in this worktree (1,061,569 B, T3 build output, ignored),
`.superpowers/takeover-backup` (46,395 B, pre-fix copies) and root `.superpowers/session5-t3` (18,963 B; logs
byte-identical to `verification/full-t3/`) — 1,126,927 B in total. Raw withheld failure logs under
`.superpowers/session5-raw` and `session5-attempts` are kept as the only copy. D: free 23,724,978,176 B at report
time vs 25,700,540,416 B before the worktree was created (observations; other campaigns write to D: concurrently).
