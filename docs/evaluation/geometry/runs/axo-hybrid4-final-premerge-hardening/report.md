# Axo × Hybrid /4 — end-to-end pre-merge reliability hardening

Run `axo-hybrid4-final-premerge-hardening` · 2026-11-06 · branch `integration/axo-hybrid4-reliability` · 0 provider calls ·
not merged, not pushed.

## A. Baseline

| item | value |
|---|---|
| branch | `integration/axo-hybrid4-reliability` (worktree `.superpowers/worktrees/axo-hybrid4-integration`) |
| start of this wave | `01cfda03` (previous report `axo-hybrid4-integration-reliability`, READY_FOR_USER_REVIEW) |
| `main` | `bb61a804`; `git merge-base main HEAD` = `bb61a804` (main fully contained) |
| Axo baseline for performance | `67f780ca` (last Axo-only commit before the integration) |
| working tree at start | clean except untracked diagnostics (`perf-after/`, `nav-after/` of the previous run, `frontend/dist-int/`), left untouched |
| user's uncommitted `frontend/index.html` | in the OLD worktree `axo-pedagogical-integration`, not touched |
| sources of truth read | `AGENTS.md`, `docs/RULES.md`, previous run `report.md`/`run.json`, `EVIDENCE_INDEX.md`, `CODE_INDEX.md` |

Commits of this wave (conventional, no `Co-Authored-By`, each checked with `git log -1 --format=%B | grep -c Co-Authored-By` = 0):

| commit | kind | what |
|---|---|---|
| `ce676a17` | test | Case C locked on the Hybrid engine and the /4 envelope |
| `8248eae0` | product | server idempotency of `POST /api/analyze` (`Idempotency-Key` = attempt id) |
| `6d0796d4` | product | server history order strict when writes share one clock tick |
| `c8e4bb17` | product | telemetry middleware: replays not counted, write after response, raw headers kept |
| `4e5a7af7` | product | local history: one localStorage key per record (two-tab lost update) + two-tab browser check |
| `b98a470b` | product | registry: quadrilateral "vuông tại A" is a right angle, not a triangle claim; restored Axo engine regressions on /4 |
| `09634f92` | eval | candidate frozen at `b98a470b` (103 files `a0cb684e…`), K-1/R-1/S-2 templates rebound |
| (evidence commit) | eval | this report, logs, receipts |

## B. Case C — exterior intersection never part of the bounded section

`backend/tests/geometry/test_hybrid4_case_c_exterior_intersection.py` (5 tests). Independent hand computation (exact,
affine-invariant checks): S.ABCD, square side 2, SA ⊥ base, SA = 4, SM = 3MA, SN = 3/5 NB, P = mid SC ⇒ (MNP): −2x+y+z=1,
Q = SD ∩ (MNP) = (0,3,−2), t = 3/2 on SD (outside the segment); section = pentagon M, N, P, (1/2,2,0)∈CD, (0,1,0)∈AD.

| layer | result |
|---|---|
| shared planner + engine (`run_fact_route`, the same `planner.py`/`engine.py` /4 runs) | full section served; checks: Q on line SD with t = 3/2, polygon planar, every vertex on a solid edge, convex and cyclic, Q not a vertex and outside the polygon; M/N/P parameters 3/4, 3/8, 1/2 |
| guard window | the same checks REJECT a polluted scene with Q spliced into the polygon (the old failure mode) |
| product envelope (TypedFactNext /2 → bridge_v2 → Source Gate → planner → engine → /4) | Q served exactly: t = 3/2, SQ = 3√5 (= 3/2·SD = 3/2·2√5), no section object drawn when none is asked |
| /4 section "cắt bởi mặt phẳng (MNP)" | **refused** `SOURCE_OBJECT_MISMATCH`: /2 has no plane kind "plane through three named points"; the closest form (`constrained` with only `contains_points`) is outside the Source Gate's closed grammar (needs a ⊥/∥ relation). The test locks: refuse with no scene, OR serve a section passing the exact Case C checks — never a polygon containing Q |
| refusals | parallel line ⇒ `PARALLEL_NO_INTERSECTION`; contradictory lengths ⇒ `INCONSISTENT_FACTS` |

Owning layer of the gap: **Extraction contract (TypedFactNext /2)** — a capability gap, not a geometry fault. Not
extended here (it changes the extraction surface ⇒ `CACHE_VERSION`, prompt, re-measurement): `OWNER_DECISION_REQUIRED`.

## C. Server-side idempotency of `/api/analyze`

`backend/app/idempotency.py::run_once`, wired in `main.py::analyze` (wraps `_analyze_once`), client
`analyzeViaServer(input, signal, retryPolicy, attemptId)` sends `Idempotency-Key: <newAttemptId()>`, shared by its
bounded retries; a new submit gets a new id. The attempt key is NOT the geometry identity (same text twice = two attempts).

| state of `(sha256(session cookie), key)` | behaviour |
|---|---|
| no key | unchanged (legacy clients) |
| malformed key | 400 `IDEMPOTENCY_KEY_INVALID`, nothing runs |
| in progress, same payload | waits for the original and gets its response (no second provider call, no second trial charge); after `WAIT_S` = 240 s ⇒ 409 `IDEMPOTENCY_REQUEST_IN_PROGRESS` + `Retry-After: 5` |
| completed 2xx | byte-for-byte replay, `Idempotent-Replayed: true`, BEFORE the guest-trial gate (a retry of the attempt that used the last trial gets its result, not 402) until `TTL_S` = 600 s |
| failed (non-2xx, exception, cancellation) | forgotten ⇒ a retry executes again; a 5xx is never replayed as a result |
| same key, different payload | 409 `IDEMPOTENCY_KEY_REUSED`, nothing runs |
| expired | purged ⇒ executes again |
| bounded | `MAX_ENTRIES` = 2048 (oldest completed evicted) |

Privacy: scope is the hashed session cookie (another session never sees a replay — tested); the problem text is held as
a sha256 and inside the stored response in memory only; nothing is logged (test asserts neither text nor key in logs).

Scope, stated in the module: **single process only** (Dockerfile `CMD` runs one uvicorn process, no `--workers`). With
several workers or hosts each keeps its own table — the guarantee does NOT hold there. Upgrade path: DB row with a unique
`(scope, key)` constraint.

Tests (`backend/tests/test_analyze_idempotency.py`, 17; `frontend/src/components/attempt-identity.test.tsx`, 7):
one submit; two independent submits; retry after a lost response (replay, one trial); replay after the trial gate would
close; concurrent same-key HTTP requests (one execution); retry while in progress (waits); in-progress timeout; cancelled
original forgotten and two waiters coalesce into one fresh run; same key + other payload; backend 5xx never replayed;
invalid/no key; cross-session; expiry; bounded table; no text in logs; client sends the key, shares it across a 502→200
retry and changes it per submit; a backend error on the next send never brings back the previous scene;
reload/Back/Forward/reopen keep the attempt (browser, D and `e2e-scene-consistency`).
Fault injection: guard disabled ⇒ 8/15 red; three targeted faults (no expiry, no session scope, 5xx replayed) each caught
by its own test.

## D. Two real browser tabs

`frontend/scripts/axo-two-tab-browser-check.mjs`: real Chrome, two tabs of one profile (same origin, shared
localStorage), real composer, `/api/analyze` answered from main's frozen /4 fixtures, every request's `Idempotency-Key`
logged. After every scenario the invariants wait until both tabs see byte-identical history (bounded poll on a
condition), then check: no record lost, statement/scene of each tab = its own record, stored scene = scene at creation
(no mutation), a tab never shows a record storage no longer holds, one key per served attempt, history below its cap
(eviction cannot mask a loss).

| run | build | result |
|---|---|---|
| `two-tab-run-1` | before fix | 0/8 — inconclusive by itself (invariant had no convergence wait and the run exceeded the 30-record cap) |
| `two-tab-run-2` | before fix | 0/8 — **lost update confirmed after convergence**: scenario 1 (A and B send different problems at once) already loses one tab's record; 4–6 then time out on the missing record |
| `two-tab-run-3`, `two-tab-run-4` | after `4e5a7af7` | **8/8**, 8/8 |

Root cause: history was ONE localStorage key holding the whole array; each tab read-modify-wrote it while seeing the
other tab's writes late (each Chromium renderer keeps its own copy, synchronised asynchronously). Fix at the persistence
layer, no sleeps: one key per record (`algosim.history.v1:<id>`), old array key migrated on read; `touch` writes only its
own key. Unit lock with stale per-tab views (`history.test.ts`) is red on the old file and green on the new.
Scenarios: (1) different problems at once, (2) same problem at once ⇒ two attempts, (3) A saves while B steps/touches
(6 UI rounds + 8 direct concurrent rounds), (4) B reloads after A updated, (5) different records + Back/Forward per tab,
(6) independent Scene3D/camera/steps, (7) A plays while B creates an attempt, plus a 502→200 retry keeping its key.

## E. Accounts, history, admin, telemetry, migrations

| item | finding | evidence |
|---|---|---|
| Alembic chain | linear: `72095b7dd318 → f32f9b107b77 → a1c7e4b90d52` (main head) `→ c4e8a91b2f03 → d5f9b82c3a14` (Axo); both Axo revisions only create tables/indexes | `logs/alembic-round-trip.log` |
| upgrade from main's head with data | user row kept; downgrade to main's head drops only the five Axo tables (history/telemetry rows are lost on downgrade, by design); re-upgrade OK; `alembic check` clean | SQLite; **Postgres NOT_RUN** |
| history ownership | every query filters `user_id = caller`; cross-user GET/PATCH/DELETE ⇒ empty/404 (existing test) | `test_learning_history_api.py` |
| admin routes | all 7 call `require_admin()` (403 otherwise) | code read |
| **history order bug** | `last_viewed_at` from a clock that ticks every ≈15.6 ms on Windows/Python 3.12: two writes in one tick tied and the `id DESC` tiebreak listed (and the 30-entry pruning would drop) the wrong row; found as a suite-order flake. Fixed: `_view_time` strictly increasing per user; red-first test with a frozen clock | `6d0796d4` |
| **telemetry replay bug** | the middleware counted an idempotent replay again (admin telemetry row + `used_today` +1) — a retry would consume a logged-in student's daily quota twice. Fixed + red-first test | `c8e4bb17` |
| telemetry buffering | needed (outcome is read from the body). Real /4 responses 0.9–69 KB (17 frozen fixtures). Over real HTTP (uvicorn loopback, 4 alternating rounds × 15 samples after warm-up) the overhead at 70 KB fell from 4.8 → 1.6 ms median (p95 12.7 → 3.7) by moving the synchronous SQLite write to a Starlette background task (after the response, off the event loop); 1 MB: 6.3 → 2.6 ms; 4 MB: 9.8 → 7.2 ms | `logs/telemetry-middleware-http.json`, `-before.json` |
| headers | `dict(response.headers)` collapsed duplicate headers (latent: no cookie is set on this route); raw header list now kept; test with duplicate `Vary` | `c8e4bb17` |
| known limitation | `usage_report()` deltas are process-wide: concurrent analyses can cross-attribute tokens in telemetry | not fixed |

## F. Mathematics and supported scope

The merge had deleted two Axo modules wholesale (they imported Adapter /3). Their tests were re-run on the current tree
with the Adapter /3 entry routed through main's own `convert_v1_to_v2(raw, "adapter3")` → Adapter /4: **9 hold on /4
and are restored** (`test_axo_generalization_on_hybrid4.py`, `test_axo_construction_integrity_on_hybrid4.py`): midpoint
sections on square/rectangle/parallelogram bases, ⊥ premise required for (MAB), Case C, cross-family prisms
(right/oblique) distances and angles, tetrahedra dihedral/skew/intersection line, midpoint-section provenance and square
certificate (two renamings), MNPQ never certified square on non-square bases, skew lines common perpendicular and
adversarial refusals. Not restored, each with its reason in the module docstring.

| finding | owning layer | action |
|---|---|---|
| right-trapezoid wording "Đáy ABCD vuông tại A … tại B" refused `INCONSISTENT_FACTS` (main `9e059eb7`: any "vuông" base wording became a `right_triangle` claim, certified on four vertices) — false contradiction verdict on consistent data | **Planning / Source Gate** (`registry._phan_loai_hinh_2d`, read by `engine.kiem_khang_dinh_loai_hinh`) | fixed `b98a470b` (≥ 4 vertices ⇒ no triangle kind; the right angle stays a checked premise); red-first; triangle control still refused when false; served 9/4 (hand oracle). `CACHE_VERSION` not bumped: every affected input was refused before and only SERVED results are cached |
| cylinder whose axis is not certified ⊥ base (OO' not ⊥ OA; explicit oblique 60°; ⊥ to one radius only) | Extraction contract / Source Gate | correct: refused `NEGATED_CLAUSE` / `CURVED_WORDING_UNSUPPORTED`, never 15π; control with stated radius and height served 15π. New `/4` lock `test_hybrid4_cylinder_never_assumed_right.py`. `oblique_cylinder` NOT added |
| sphere section given by `plane_equation` | Planning (bridge) | refused `BRIDGE_UNSUPPORTED_CURVED` on /4 — capability gap, safe |
| `convert_v1_to_v2` raises `KeyError` on a `/1` payload without `derived_sections` | tool-only converter (no product consumer) | reported, not changed |
| section by a plane through three named points | Extraction contract (/2) | see B |

Invariants and where they are locked (all green in the full suites, J): metric-correct ⊥ (Gram) — `test_geometry_kernel.py`,
Case C checks; intersection lines on parent objects and section inside the solid — Case C + restored Axo tests + main's
section suites; no point/edge outside the domain reported as section — Case C guard window; visible/hidden over camera
angles — `scene3d-orbit-gate` (J); no future-step object before its step — `scene3d-no-answer-surface.test.tsx`,
browser captures; no dependence on sample names — `fixture-point-identity.test.tsx`, synthetic fixtures with their own
identity; provenance and relation certificates backend → Scene3D — `hybrid-preview-adapter` checks (previous wave) +
contract matrix; input data and envelope not mutated by display — deep-frozen Scene3D browser check, two-tab "stored
scene = scene at creation". Rotating a right circular cylinder in space ≠ true oblique cylinder: both kept apart
(`test_curved_foundation.py`, `test_oblique_cylinder_ellipse.py` untouched).

## G. Performance

Setup: production builds of baseline **Axo `67f780ca`** (fresh detached worktree) and **candidate `09634f92`** (tree
of `b98a470b`; no product code after it), both `vite build` into separate `dist-perf/`; offline static server; Chrome
157.0.8103.38 headless, 1440×900, DPR 1; **actual GPU read from `SystemInfo`: Intel(R) UHD Graphics via ANGLE
Direct3D11** (the machine's GTX 1650 is not the renderer). Nothing else ran during the measurements (no pytest/build in
parallel). Raw samples saved; order alternated (ABBA) to cancel drift and heat.

**Navigation (the questioned cold open).** `measure-axo-performance.mjs --navigation`, 8 runs B C C B B C C B × 12
iterations = 48 samples per build (`perf/nav-*`, `perf/navigation-raw-samples.json`):

| metric | baseline median / p95 (ms) | candidate median / p95 (ms) |
|---|---|---|
| cold library | 165.4 / 231.8 | 158.1 / 230.1 |
| **cold open** `/simulation/pyramid-cross-section` | 204.8 / 299.0 | **190.2 / 285.2** |
| warm reopen | 165.5 / 250.1 | 135.9 / 186.9 |
| Back | 80.4 / 107.1 | 67.9 / 86.7 |
| Forward | 144.5 / 173.4 | 127.9 / 172.9 |

The previous report's cold-open p95 332.6 → 435.4 ms is **not reproduced**: with alternation and 48 samples the
candidate is not slower. The earlier figures came from one non-alternated run per build, the candidate run taken while
the machine was measured ≈2× slower (previous report); the most likely explanation is drift, which cannot be proven after
the fact. No optimisation was made.

**Cold-open phases** (`frontend/scripts/axo-cold-open-phases.mjs`, warm-up 4, then 12 alternating samples per build,
cache disabled, `perf/cold-open-phases/`), medians baseline → candidate (ms from navigation start): HTML 4.2 → 3.3;
scripts fetched 40.7 → 35.5; DOMContentLoaded 84.8 → 88.0; first WebGL context 164.5 → 171.6; first draw call 245.2 →
255.3; rendered Scene3D objects observed 343.5 → 364.1 (includes the harness's polling granularity). Script bytes
2 041 048 → 2 046 535 (+5.5 KB: client provenance checks, idempotency header, per-record history). CPU profile (one cold
open per build): the same shape — engine/program time, the app chunk ≈ 90 ms self, WebGL program linking
(`getProgramInfoLog` ≈ 50 ms, driver shader compile) and `vendor-three` ≈ 40 ms. Differences of ≤ 10 ms median in both
directions across the two harnesses ⇒ within noise; nothing to fix.

**Scenes** (`measure-axo-performance.mjs`, ABBA `perf-1-B`, `perf-2-C`, `perf-3r-C`, `perf-4-B`; `perf-3-C` was
interrupted by a session end after 2 scenes, kept, excluded; 15 s continuous orbit per scene; `perf/perf-summary.json`):

| scene | step median/p95 B → C | load median B → C | frame interval median/p95 B → C | frames > 16.7 ms B → C | renders/frame | GPU buffers+programs created − deleted |
|---|---|---|---|---|---|---|
| thiet-dien-chop | 65.2/84.0 → 62.2/82.3 | 129.1 → 124.4 | 6.9/7.1 → 6.9/7.1 | 0.10% → 0.05% | 1 / 1 | 0 / 0 |
| cau-cat-mat-phang | 55.7/71.3 → 57.1/66.8 | 100.2 → 97.8 | 6.9/7.1 → 7.0/13.9* | 0.05% → 0.20%* | 1 / 1 | 0 / 0 |
| non-thiet-dien-truc | 37.8/52.4 → 37.0/45.9 | 67.3 → 68.1 | 6.9/7.1 → 6.9/7.1 | 0.05% → 0.05% | 1 / 1 | 0 / 0 |
| tru-thiet-dien-tron | 44.6/60.5 → 43.2/54.8 | 94.4 → 94.8 | 6.9/7.1 → 6.9/7.1 | 0.09% → 0.05% | 1 / 1 | 0 / 0 |
| cube-hexagon | 75.4/96.2 → 71.6/81.3 | 155.2 → 142.7 | 6.9/7.1 → 6.9/7.1 | 0.09% → 0.14% | 1 / 1 | 0 / 0 |
| oblique-prism | 42.3/61.0 → 38.4/44.9 | 89.3 → 85.4 | 6.9/7.1 → 6.9/7.1 | 0.05% → 0.05% | 1 / 1 | 0 / 0 |
| dense-multi-solid | 53.1/60.7 → 52.2/58.4 | 113.5 → 101.2 | 6.9/7.1 → 6.9/7.0 | 0.05% → 0.05% | 1 / 1 | 0 / 0 |

\* one candidate run only (`perf-3r-C`, right after the session resumed): 13.9 ms = one missed vsync of the 144 Hz
display; the other candidate runs (`perf-2-C`, partial `perf-3-C`) show p95 7.1 and the baseline `perf-1-B` shows the
same 13.8 ms at p99 ⇒ not reproducible. Heap after the scene: 26–51 MB, ±10 MB in both directions between runs, no
growth trend. One WebGL context throughout; every buffer/program created is deleted.

How to read these numbers: the frame interval is the requestAnimationFrame cadence of frames that actually drew (1 render
per frame), on a 144 Hz display, so 6.9 ms says "no dropped vsync while orbiting", NOT "the learner always sees
140 FPS" or "no perceived lag". Perceived latency is the step-change and load columns (tens of ms) and the navigation
table (hundreds of ms on a cold open).

## H. Pedagogy and UI regressions

Offline production-build E2E `e2e-scene-consistency/receipt.json` (**36/36**, build of `09634f92`'s tree): per-route
statement/title/rendered objects for every catalog sample, no answer surface at first and final step (no "Xem kết quả",
no conclusion panel, no answer token in the DOM), given data per step, same-title problems through history A→B→A,
title-only legacy record, F5, rapid switching, switching during playback, Back/Forward, real composer attempts (two
sends = two attempts, 502→200 = one), deep-frozen Scene3D through steps/play/orbit/zoom/select/hide/isolate/restore/
dock/switch/history, first/middle/last + two-angle captures, 6 widths (360–1440) and real Chrome 110% zoom.
UI harness `ui-run/` (`measure-axo-performance.mjs --ui`, candidate build): **40/40** — cards, labels and scrolling at
360/390/430/768/1024/1440 for five scenes, hide/isolate/select restored per problem, camera invariant across dock
open/close, browser zoom 110%. Two-tab check (D) covers statement/scene per attempt across tabs.

Scene3D orbit gate (`scene3d-orbit-gate.mjs`, cases p1/p6/p7): **KHÔNG ĐẠT on both builds** — verdict `KHONG_ON_DINH`
(the camera never meets the gate's settle criterion, < 0.01° per frame for 30 frames, within 20 s, so the gate itself
declares its angle readings unreliable). Identical on the Axo baseline `67f780ca` ⇒ pre-existing on the Axo UI, not
introduced by this wave. A single candidate p7 reading (axis norm 0.83, 1 snap) did not reproduce in three alternating
re-runs (C, B, C: axis Z ‖1.000‖, 0 snaps on both). Visible/hidden classification across angles therefore rests on the
product tests and the browser captures, not on this gate. Open item (K).
No style or feature was changed in this wave.

## I. Publication safety

| scan | result |
|---|---|
| `--range bb61a804..HEAD` (all integration commits) | BLOCKED, **1** violation: `HARDCODED_PASSWORD` · commit `6533b586` (Axo, 2026-10-28) · `backend/tests/test_auth_api.py` · blob `28be1ef6…` line 197 (`logs/publication-safety-range.log`) |
| `--head` | BLOCKED, 98 violations, **all 98 already carried as pending owner exceptions** (95 `PY_TRACEBACK`, 2 `BEARER_TOKEN`, 1 `HARDCODED_PASSWORD` in `tests/conftest_classroom.py`); 0 new; not accepted by this run (`logs/publication-safety-head.log`) |

Finding `6533b586`, verified without reproducing the value: a 13-character literal used as the NEW password in a
change-password test (`/api/auth/password` then login) against the test suite's throw-away SQLite database. It never
appears outside `backend/tests/` in any commit, is not in the HEAD tree (removed by `cb564b1e`, which derives it from
`TEST_PASSWORD`), and is in no report, log or receipt of either run folder. Nature: test fixture, not a usable
credential (no deployment, seed, config or documentation uses it). Residual risk: the string stays readable in Git
history of this branch if published. Mechanism: an owner entry in
`docs/evaluation/geometry/runs/publication-safety-remediation/publication_exceptions.json` keyed by (path, blob SHA-1,
content SHA-256, rule) — **`OWNER_DECISION_REQUIRED`**; this run creates no exception, rewrites no history. Evidence of
this run was checked for secrets: logs carry paths/blobs/lines only.

## J. Gates on the final HEAD

Tested tree: **`2330b675`** (evidence commit; product code = `b98a470b`), in a clean detached worktree
(`git status` empty before and after), log outside the worktree then copied to `logs/t3-full-gate-2330b675.log`.

| gate | result |
|---|---|
| **T3** `frontend/scripts/full-gate.mjs --python <venv>` | **FULL_PRODUCT_GATE_PASS** (499.4 s) |
| ↳ full pytest | 13 820 passed, 7 skipped, 2 deselected, 9 xfailed |
| ↳ Vitest | 128 files / 1 929 tests passed |
| ↳ `tsc -b` + production build (the repo's only typecheck) | pass |
| ↳ `replay_demo_cases.py`, `audit_demo_crash_surface.py` | DEMO_REPLAY_PASS 5/5; crash-surface audit pass |
| candidate seal `freeze_evaluation_candidate.py --verify` | matches (103 files `a0cb684e…`); also inside pytest |
| Chromium E2E (offline, production build) | 36/36 (H) |
| two real tabs | 8/8 twice (D) |
| UI harness | 40/40 (H) |
| performance | no reproducible regression (G) |
| publication safety | `--range 09634f92..2330b675` PASS (0 violations); `--range bb61a804..HEAD` 1 historical finding (I); `--head` 98 pending, 0 new |
| node harness `node --test "scripts/*.node-test.mjs"` (outside every tier) | 151/155 pass, **2 fail**, 2 skipped — both are `compiler-scene-replay` manifest tests reading `backend/tests/geometry/test_prism_production_route.py`, which main's own cutover `52205f45` deleted; the lib, its test and the pinned `suite.json` are byte-identical to main ⇒ inherited from main, not introduced here; not edited (frozen evidence input) — `logs/node-harness-2330b675.log` |
| Scene3D orbit gate | KHONG_ON_DINH on baseline and candidate alike (H) |

Commits after the tested tree: one docs-only commit (this section, L, `run.json`, `handoff.md`, the two copied logs),
all inside this run folder. It changes no product path (`MEASURED_SYSTEM_PATHS` untouched, seal still matches) and no
test; the docs gate `test_docs_information_architecture.py` and publication safety are re-run on it (L).

## K. Open risks and owner decisions

1. `OWNER_DECISION_REQUIRED` — publication exception for `6533b586` / blob `28be1ef6…` (I), and the 98 pre-existing pending entries.
2. `OWNER_DECISION_REQUIRED` — TypedFactNext /2 has no "plane through three named points" (B); extending it changes the extraction surface.
3. Idempotency is single-process (C); multi-worker deployment needs the DB-backed variant.
4. Postgres migration round trip NOT_RUN (E).
5. Telemetry token deltas are process-wide (E).
6. Live provider behaviour NOT_MEASURED (0 calls by rule).
7. Scene3D orbit gate `KHONG_ON_DINH` on the Axo UI (baseline and candidate alike) — the camera does not settle by the
   gate's criterion; root cause not investigated in this wave (H).
8. Performance measured on one machine (Intel UHD via ANGLE); NVIDIA GPU path NOT_MEASURED.

## L. Conclusion

**READY_FOR_OWNER_REVIEW** — not `READY_TO_MERGE`.

Every required engineering item of the brief is done and verified on the final tree: Case C locked on both layers,
server idempotency per attempt (single-process, stated), two real tabs (a real lost update found and fixed at the
persistence layer), accounts/history/telemetry audited with two real bugs fixed and measured, migrations verified
additive with a data round trip, one real math fault fixed at its owning layer with the retired regressions restored on
/4, the questioned cold-open regression shown not reproducible, no UI/pedagogy regression, T3 green.

What still blocks a merge is not engineering this run may decide: the publication exception for `6533b586`
(`OWNER_DECISION_REQUIRED`, no exception created, no history rewritten), the 98 pre-existing pending entries, the /2
contract gap for three-named-point planes, and explicit permission to merge/push. Inherited items reported, not hidden:
2 node-harness manifest tests red since main's cutover, orbit gate `KHONG_ON_DINH` on the Axo UI, Postgres round trip
not run.
