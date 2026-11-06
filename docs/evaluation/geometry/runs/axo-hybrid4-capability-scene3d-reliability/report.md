# Axo × Hybrid /4 — capability completion, Scene3D reliability and pre-merge hardening

Run `axo-hybrid4-capability-scene3d-reliability` · 2026-11-06 · branch `integration/axo-hybrid4-reliability` ·
0 provider calls · not merged, not pushed, no history rewritten.

Evidence labels used below: **[test]** verified by an automated test · **[browser]** verified by observation in a real
Chrome on a production build · **[code]** inferred from source · **[not verified]** · **[out of scope]**.

## A. Baseline and Git state

| item | value |
|---|---|
| wave base | `d3da429b` (previous run `axo-hybrid4-final-premerge-hardening`, READY_FOR_OWNER_REVIEW; product `b98a470b`, tested tree `2330b675`) |
| `main` | `bb61a804`; `git merge-base main HEAD` = `bb61a804` (fully contained; main has not moved) |
| user's uncommitted work | `frontend/index.html` in the old worktree `axo-pedagogical-integration`, `.playwright-mcp/` in the main checkout — untouched |
| candidate seal at start | 103 files `a0cb684e…` (verified) |
| `CACHE_VERSION` | 132 at start and at end |

Commits of this wave (no `Co-Authored-By` in any):

| commit | kind | what |
|---|---|---|
| `555802da` | product | Hybrid /4 sections by the plane through three named points; prompt rule; cache identity re-locked |
| `e3960bd2` | measurement | orbit gate v4 (display-frame counter, rebuild/steady-state allocation criterion) |
| `286e4820` | product | Scene3D: no full rebuild when a drag starts; projection step titles; camera-views check; fixtures |
| `abf3d403` | test | node harness: frozen oracle sources repinned (SHA-256 unchanged) |
| `e23e3983` | product | per-request token telemetry; Postgres test; single-process deployment lock |
| `ac8e610d` | eval | candidate frozen at `e23e3983` (103 files `f75779e2…`), K-1/R-1/S-2 templates rebound |
| (evidence + final docs) | eval | this run folder |

## B. Root cause of each issue

| issue | reproduction | root cause | owning layer | fix |
|---|---|---|---|---|
| "(MNP)" section refused `SOURCE_OBJECT_MISMATCH` | Case C `/2` payload | `/2` could only say "constrained" with a ⊥/∥ relation; a plane given ONLY by three named points matched no grammar, although planner/registry/engine already had `section(solid, plane)` (the `/1` path) | Extraction contract → bridge | bridge maps `constrained` with exactly one `contains_points` of 3 labels to the existing three-point section fact; prompt rule 4 tells the model how to encode "(MNP)" |
| orbit gate `KHONG_ON_DINH` on every Axo build | gate p1/p6/p7 | the gate counted the PAGE's rAF calls; Axo's demand-driven loop stops calling rAF once the camera rests (measured: camera exactly still 465 ms after release), so the 30-frame settle window froze on the damping tail | measurement (gate) | count display frames with the gate's own heartbeat |
| gate `TU_KHOP_KHUNG` on p6 (4 allocations) | gate p6 | three.js uploads a buffer lazily at an object's first draw (create-only, once — e.g. hidden arcs seen from below); the gate counted any create | measurement (gate) | allocations = deletes (both passes) + creates in a repeat pass |
| full scene rebuild at every drag start | GL-call counter: 262 objects created + deleted per drag on the pyramid | `pointerdown` cleared `hoveredObject`, a dependency of the 1 000-line scene-build effect | Rendering (Scene3D view) | drag hides the tooltip through its own state; hover kept |
| "Hạ hình chiếu vuông góc Hình chiếu của I lên (ABC) của I lên (ABC)" | real /4 tangent-plane scene | an unnamed foot's description spliced into a sentence that already describes it | Pedagogical policy (frontend presenter) | name the foot only when it has a short symbol |
| 2 node-harness failures | `node --test` | manifest pinned three oracle files deleted by main's cutover `52205f45` | test harness | exact blobs frozen in this run folder, path moved, SHA-256 unchanged |
| overlapping analyses double-charged tokens | test: two overlapping requests, 100 tokens each → 200/200 | process-wide before/after usage delta | telemetry | per-request ContextVar accumulator |

## C. TypedFactNext and Case C end to end

[test] `backend/tests/geometry/test_hybrid4_case_c_exterior_intersection.py::test_case_c_section_by_three_named_points_is_served_end_to_end_without_q_as_a_vertex`:
TypedFactNext /2 → bridge_v2 → Source Gate → planner → engine → Adapter /4 → Scene3D. Served; pentagon with 5 vertices,
`ENGINE_DERIVED_SECTION` certificate, plane label `(MNP)`; Q on line SD at t = 3/2 (outside the segment), never a section
vertex; exact affine checks (planar, every vertex on a solid edge, convex and cyclic, Q outside); construction-order
check `CS.check` clean (no object before its step); area 11√6/8 = hand value (|Σ vᵢ×vᵢ₊₁|²/4 = 363/32). The guard window
(Q spliced into the polygon must fail the same checks) stays.

Design decisions and why:
- no new `plane_kind`: the `/2` schema already allows `constrained` + `contains_points` (1..4 labels); the bridge rule is
  "exactly one constraint, `contains_points`, three labels" — nothing keyed on letters, sample names or Case C;
- the Source Gate grounds "cắt bởi (MNP)" with its existing grammar (`mat_cat_dung_nguon`); an area question on that
  section carries the section's quote so the gate verifies the plane is named in the source;
- the engine proves distinct, non-collinear points and derives every vertex; an exterior line–plane intersection is
  never a vertex (engine behaviour, now reachable from /4);
- stated cuts / a declared boundary on such a plane have no carrier on that function yet ⇒ refused
  `UNSUPPORTED_CAPABILITY`, never silently dropped; repeated labels ⇒ `INVALID_DERIVED_SECTION` (schema), unknown
  labels ⇒ `UNDERDETERMINED_POINT`, collinear ⇒ `COLLINEAR_POINTS`, plane never named ⇒ `PLANE_NOT_IN_QUOTE`;
- the scene's declared plane name is checked as `(MNP)` (not the default "α").

Versioning: the prompt change altered the extraction surface; `tests/test_cache_identity.py` went red as designed. The
lock offers "re-lock if cached envelopes stay correct, else bump". Only SERVED results are cached and the cache key
covers registry/planner/engine/contract/adapter/envelope, none changed here; both changes only affect inputs that were
refused before (bridge rule limited to three-point `constrained`; prompt sentence about three-point planes). So no
cached result changes meaning ⇒ re-locked with `scripts/lock_cache_identity.py`, `CACHE_VERSION` stays 132 [test].

Anti-overfitting [test] `backend/tests/geometry/test_hybrid4_three_point_plane_sections.py`: an independent oracle
(hand Euclidean coordinates, exact edge–plane intersection, own ordering and cross-sum area; never reads engine output)
against 8 served cases — renamed square pyramid T.EFGH, rectangle base, right-triangle-base pyramid (triangle section),
plane through two solid vertices, right prism with mixed points, oblique prism (projection-defined), cube hexagon, Case C
— sections of 3, 4, 5 and 6 vertices, all exact; refusals: collinear, repeated, unknown, contradictory data, stated cuts.
Fault injection: rule disabled ⇒ 11 of 19 tests red.

[out of scope / not covered] parallelogram bases (no `/2` premise kind), a three-point plane that misses the solid or
only touches it (every named point the `/2` vocabulary can construct lies on the solid; not constructible here).

## D. Camera, orbit and zoom

Root cause of `KHONG_ON_DINH`: see B. Proof by data [browser]: diagnostic with the gate's own hook plus the app's camera
snapshot per frame — after release the true camera stops completely at 465 ms; the last 30 drawn frames still move
0.0118 → 0.00105 units/frame; after that no rAF tick arrives, so v3's window never advanced.

Gate v4 (`frontend/scripts/scene3d-orbit-gate.mjs`, thresholds unchanged, documented in the file):
| build | p1 | p6 | p7 |
|---|---|---|---|
| candidate, gate v4 | DAT | DAT (first pass 4 lazy creates, 0 deletes; repeat pass 0) | DAT |
| injected per-frame geometry rebuild | TU_KHOP_KHUNG (4 544) | TU_KHOP_KHUNG (7 612) | TU_KHOP_KHUNG (7 324) |
| injected never-settling damping (0.0008) | KHONG_ON_DINH | — | — |

Rebuild at drag start [browser, then locked by test]: GL-call counter around press → drag → release starting over an
object: pre-fix build pyramid 262/262 (create/delete) on every drag, cone 85/85, sphere 110–120; candidate 0/0. New
check in `axo-scene-consistency-browser-check.mjs`: 3 FAIL on the pre-fix build, PASS on the candidate. Hover-in itself
still rebuilds (measured: at most one long task of 51 ms on the first hover, later changes < 50 ms) — open (L).

Camera behaviour [browser] `frontend/scripts/axo-camera-views-browser-check.mjs`, eight scenes covering the seven
families (pyramid + section and the three-point pentagon, oblique prism, cube hexagon, sphere cut, plane tangent to a
sphere, cylinder circular section, cone axial section; four of them real /4 responses through the composer): orbit
target never moves through orbit 90°/180°, near-top view, zoom in/out, step change and dock toggle; step change and
dock collapse/reopen leave the camera exactly where it was; zoom stops at finite limits with the figure still rendered;
reset returns to the default pose; one canvas; no duplicate visual owner; no page error — **8/8 PASS** on the final build (`camera-views/receipt.json`). Captures of every
view are in `camera-views/`; reviewed by eye for the pentagon (default, 180°), cube hexagon (near top) and tangent plane:
labels sit on their points, hidden edges dashed, nothing cropped [browser]. Visible/hidden correctness across angles is
otherwise covered by product tests and these captures, not by an independent occlusion oracle [not verified beyond that].

## E. Scene3D and construction order

[test] construction order clean for the three-point Case C scene (`CS.check`); no answer surface, no conclusion panel,
no "Xem kết quả" (E2E, all catalog samples, first and final step) [browser]. Labels "Đề cho / Được dựng / Được suy ra"
unchanged by this wave [code].
Fixed: projection step titles with unnamed feet (B) [test].
Open (not fixed, reported): the three-point section's last step says "Nối các đoạn giao tuyến (MN ⊂ (SAB), NP ⊂
(SBC))" and does not name the segments through the two unnamed vertices on CD and AD; the polygon is correct, the
explanation is incomplete — owning layer: engine construction-step summary for `section(solid, plane)` (pedagogical).

## F. Node harness and regression tests

[test] `node --test "scripts/*.node-test.mjs"`: 153/155 pass, 0 fail, 2 skipped (both in `full-gate.node-test.mjs`,
`skip: !existsSync(VENV)` — environment-conditional, unchanged). The three pinned oracle sources are frozen byte-exact in
`frozen-oracle-sources/` (`git show 52205f45^:…`); staged blobs hash to the pinned 18170a78…/85403c6b…/4f9fb1e6…; only
the manifest `path` moved. No Adapter /3 reference remains in the harness scripts. Restored files are `.py.txt`, never
collected as tests.

## G. PostgreSQL, idempotency and telemetry

PostgreSQL [test, real `postgres:16-alpine`, throw-away container, no volume, `logs/postgres-tests.log`]:
`test_postgres_integration.py` (upgrade, real models, container restart, `alembic check`) and the new
`test_postgres_axo_history_migration.py`: upgrade from main's head `a1c7e4b90d52` with a user present → `d5f9b82c3a14`,
user kept; `uq_learning_history_per_user` (unique) and the FK to `users` present, both indexes present; two accounts
isolated over HTTP (same key allowed per account; foreign PATCH/DELETE 404); order strict when writes share one clock
tick; six concurrent upserts of one key ⇒ one row, no 5xx; downgrade to main's head drops exactly the five Axo tables
(history, account meta, admin settings, audit log, analysis telemetry — the data lost on downgrade) and keeps the user;
re-upgrade and `alembic check` clean. Docker Desktop had to be started for this; afterwards it was stopped and
`wsl --shutdown` was run to release memory (this also stops any other WSL distro that was running; two containers that
Docker Desktop had auto-restarted were stopped with it).

Idempotency: deployment = one uvicorn process (Dockerfile `CMD`, no `--workers`, no `WEB_CONCURRENCY`, no compose
replicas); now locked by `test_shipped_deployment_runs_one_server_process` [test] — adding workers or replicas turns it
red and points at the DB-backed variant. No Redis or new infrastructure. Retry after a lost response, timeout,
cancellation, concurrency, expiry and no second trial charge are covered by the previous wave's 15 tests, all green.

Telemetry: overlapping analyses were each charged both requests' tokens (proved: 200/200 instead of 100/100) ⇒ fixed
with a per-request accumulator [test]. Remaining by design: the telemetry row is written after the response (background
task); a crash in between loses that row and the daily-usage increment — an undercount (lenient to the learner), not an
overcount [code]. Logs carry no problem text (tested last wave).

## H. Publication safety

Scans (`logs/publication-*.log`, values never printed into evidence):

| scan | result |
|---|---|
| `--range d3da429b..HEAD` (this wave, incl. the /4 response fixtures) | **PASS**, 0 violations |
| `--range bb61a804..HEAD` (whole integration) | BLOCKED, 1 violation: `HARDCODED_PASSWORD`, commit `6533b586`, `backend/tests/test_auth_api.py`, blob `28be1ef6…` |
| `--head` | BLOCKED, 98 violations, all already pending owner exceptions, 0 new |

Classification by group (verified by inspection, values not reproduced):

| group | count | classification | evidence | residual risk | lowest-risk handling |
|---|---|---|---|---|---|
| `HARDCODED_PASSWORD` · `6533b586` · `test_auth_api.py` (history only) | 1 | test fixture | 13-char "new password" of a change-password test on a throw-away SQLite DB; never outside `backend/tests/`; absent from HEAD since `cb564b1e`; in no evidence file | readable in this branch's history if published | owner exception keyed by (path, blob SHA-1, content SHA-256, rule) — `OWNER_DECISION_REQUIRED` |
| `HARDCODED_PASSWORD` · `backend/tests/conftest_classroom.py` (HEAD) | 1 | test fixture | the shared `TEST_PASSWORD` constant used to register throw-away test accounts | none beyond the test DB | already pending; owner decision |
| `BEARER_TOKEN` · `backend/tests/test_dev_backend_launcher.py`, `…/docker-backend-dev-auto-refresh/SECRET_SCAN.json` | 2 | test fixture / placeholder | the same 24-char lowercase word in both, beside variables named as fakes, in a test of the launcher's redaction | none (not a credential) | already pending; owner decision |
| `PY_TRACEBACK` · 16 log files of 12 historical runs (`classroom-band-fit`, `regular-square-pyramid-w01/w03`, `w15`…`w20`, …) | 95 | diagnostic logs, low sensitivity | no key/token-like string (0 of 16 files); 15 of 16 contain a local Windows path including the OS user name | reveals the local user name and folder layout | owner choice: accept as-is, or replace those logs by summaries in a NEW commit (history keeps them either way) |

This run creates no exception, deletes no pending entry, rewrites no history. Publication gate: **BLOCKED pending owner
decisions** (`OWNER_DECISION_REQUIRED`).

## I. Generalization

Held-out set written after the implementation, not in the test suite (`tools/three_point_generalization_eval.py`,
`generalization-results.json`), served answers checked against the independent oracle:

| class | count | cases |
|---|---|---|
| CORRECTLY_SERVED | 6 | "cắt bởi (MNP)" without "mặt phẳng" (3√5/8); "Tìm thiết diện …" points on SB/SD/SC (4); O.KLMN / X,Y,Z side 6 height 3 mixed ratios (9√149/10); points on SA, SC, AB (5√3/4); right prism with shuffled premises (6); plane equal to face (SAB) served as that triangle |
| CORRECTLY_REFUSED | 3 | collinear points on a base edge (`COLLINEAR_POINTS`); undeclared points (`UNDERDETERMINED_POINT`); section request that never names the plane (`PLANE_NOT_IN_QUOTE`) |
| INCORRECTLY_REFUSED | 0 | — |
| INCORRECTLY_SERVED | 0 | — |

Together with C: 14 served cases exact against the oracle, 0 wrong; refusals carry precise codes. This is support and
accuracy on this capability only, on 0-provider-call payloads — it says nothing about what the live extractor emits for
free text [not verified: live extraction, by rule 0 provider calls].

## J. Performance before and after

Baseline = previous candidate product `b98a470b` (fresh detached worktree), candidate = `e23e3983`; both production
builds; Chrome 157 headless 1440×900 DPR 1; GPU read from SystemInfo: Intel(R) UHD Graphics via ANGLE (the GTX 1650 is
not the renderer; nothing here says anything about phones). Order ABBA, nothing else running; Docker stopped first
(a Node build had hit an out-of-memory error while the Docker VM held memory). Raw samples in `perf/`.

Navigation (`--navigation`, 8 runs B C C B B C C B × 12 = 48 samples per build, `perf/navigation-raw-samples.json`):

| metric | baseline median / p95 (ms) | candidate median / p95 (ms) |
|---|---|---|
| cold library | 140.2 / 208.7 | 137.7 / 204.7 |
| cold open | 176.0 / 278.9 | 175.6 / 268.4 |
| warm reopen | 117.3 / 149.5 | 119.2 / 190.2 |
| Back | 65.9 / 72.5 | 65.1 / 77.3 |
| Forward | 113.7 / 148.7 | 112.6 / 151.2 |

Scenes (`perf-1-B`, `perf-2-C`, `perf-3-C`, `perf-4-B`; 15 s orbit each; `perf/perf-summary.json`): step-change median
62.2→62.4 (pyramid), 51.1→53.5 (sphere cut), 36.2→36.6 (cone), 44.0→44.9 (cylinder), 66.8→67.0 (cube hexagon), 37.3→37.7
(oblique prism), 52.1→49.9 ms (dense multi-solid); frame-interval p95 7.0–7.1 ms in both; frames > 16.7 ms ≤ 0.05 % in
both; 1 render per frame; GPU buffers+programs created − deleted = 0; one WebGL context; heap after the scene 25–53 MB in
both with ±13 MB swings in both directions.

Reading: every difference is within run-to-run variation (medians within ±3 ms, p95 swings in both directions; the
warm-reopen p95 rise has an unchanged median and comes from a few outlier samples). No speed-up and no regression is
claimed. The orbit cadence (6.9–7.1 ms at 144 Hz) says no vsync was missed while orbiting, not that perceived latency is
7 ms; perceived latency is the step/load/navigation columns. The removed drag-start rebuild (D) is not in these numbers:
the perf harness starts its orbit without hovering an object first.

## K. Full T3 gate and browser evidence

Tested tree **`69c5e910`** (evidence commit; product `e23e3983`), clean detached worktree (`git status` empty before
and after), log copied to `logs/t3-full-gate-69c5e910.log`:

| gate | result |
|---|---|
| **T3** `frontend/scripts/full-gate.mjs --python <venv>` | **FULL_PRODUCT_GATE_PASS** (459.8 s) |
| ↳ full pytest | 13 836 passed, 7 skipped, 3 deselected (opt-in markers), 9 xfailed |
| ↳ Vitest | 129 files / 1 930 tests |
| ↳ `tsc -b` + production build | pass |
| ↳ demo replay · crash surface | DEMO_REPLAY_PASS 5/5 · pass |
| node harness (outside every tier), same clean tree | 153/155, **0 fail**, 2 environment skips (`logs/node-harness-69c5e910.log`) |
| candidate seal `--verify` | matches 103 files `f75779e2…` |

Commits after the tested tree: one docs-only commit inside this run folder (this section, M, `run.json`, `handoff.md`, the
two copied logs). No product path, no test changes; docs gate, seal and publication safety re-run on it.

Browser evidence on the final build (`frontend/dist-perf` = product `e23e3983`, logs `logs/browser-*.log`):

| check | result |
|---|---|
| two real tabs (7 scenarios + retry), run twice | 8/8, 8/8 (`two-tab-1/`, `two-tab-2/`) |
| E2E scene consistency (routes, statements, no answer surface, history, reload, Back/Forward, real composer, deep-frozen Scene3D, captures, 6 widths, real Chrome zoom 110 %, drag-start rebuild) | 39/39 (`e2e-scene-consistency/`) |
| UI harness (cards/labels/scrolling 360–1440 px, restore per problem, camera across dock, zoom 110 %) | 40/40 (`ui-run/`) |
| camera views, 7 families / 8 scenes | 8/8 (`camera-views/`) |
| orbit gate v4 p1/p6/p7 | DAT/DAT/DAT (`orbit-gate/ORBIT_GATE.json`) |
| PostgreSQL 16 (opt-in) | 2/2 PASSED (`logs/postgres-tests.log`) |
| node harness | 153/155, 0 fail, 2 env skips |

## L. Remaining risks and owner decisions

Owner decisions (`OWNER_DECISION_REQUIRED`, nothing decided by this run):
1. publication: exception for `6533b586` / `test_auth_api.py` blob `28be1ef6…`; the 98 pending entries (H) — including
   whether the 95 traceback logs that show the local user name should be replaced by summaries in a new commit;
2. merge/push of `integration/axo-hybrid4-reliability` (not done; needs explicit permission for that task).

Open, measured, not fixed in this wave:
- hover-in (pointer entering an object) still rebuilds the scene (≤ one 51 ms long task, first hover; later < 50 ms);
  fixing it means moving hover emphasis out of the scene-build effect (Rendering);
- three-point section step text names only the named-vertex segments (E) (pedagogical policy / step summary);
- telemetry row written after the response can be lost on a crash (undercount, lenient) (G);
- idempotency holds for one server process only — locked by test; multi-worker needs the DB-backed variant (G);
- three-point planes: stated cuts/declared boundary refused (`UNSUPPORTED_CAPABILITY`); parallelogram bases not
  expressible in `/2`; planes missing/touching the solid not constructible with the `/2` point vocabulary (C);
- live extraction of "(MNP)" wording by the provider NOT_MEASURED (0 provider calls by rule); the prompt rule is in the
  extraction surface and the cache identity is re-locked;
- performance measured on one machine (Intel UHD / ANGLE); no phone/NVIDIA claim.

## M. Technical conclusion

**READY_FOR_OWNER_REVIEW.**

Done and verified: the plane through three named points is served on Hybrid /4 through the general planner/engine path
with no per-problem code [test]; Case C runs the whole pipeline and never makes the exterior intersection a vertex
[test]; the orbit gate is now a trustworthy measurement (root cause shown with data, evidence windows red) and the camera
meets the checked invariants on seven families [browser]; a real drag-start rebuild and a step-title defect are fixed
[browser/test]; the node harness has no failures [test]; PostgreSQL migration and history behaviour are verified on a
real server [test]; idempotency's deployment assumption is locked and token telemetry is per request [test]; no answer
surface or statement/scene mix-up came back [browser]; generalization 14/14 served cases exact, refusals precise
[test]; T3 and browser regression green on the final tree; performance within variation.

Not `READY_TO_MERGE_RECOMMENDATION` because the publication gate is BLOCKED on owner decisions (H, L) and merge/push
needs explicit permission. Open items in L are measured and reported, none hides a failing gate.
