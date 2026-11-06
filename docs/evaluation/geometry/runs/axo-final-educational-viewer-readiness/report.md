# Axo — final educational viewer quality, performance and release readiness

Run `axo-final-educational-viewer-readiness` · 2026-11-06 · branch `integration/axo-hybrid4-reliability` · 0 provider
calls (`ALLOW_LIVE_AI=0`) · not merged, not pushed, no history rewritten, no `Co-Authored-By`.

Started by a Codex agent, interrupted by its usage limit (not completed); resumed and finished by Claude without
re-implementing: every Codex commit and uncommitted edit was read, kept and verified. Evidence labels: **[test]**,
**[browser]**, **[code]**, **[not verified]**.

## A. Baseline and Git state

| item | value |
|---|---|
| start of the task (Codex) | `1be6a7ae` (previous run `axo-hybrid4-capability-scene3d-reliability`) |
| state found on resume | HEAD `21ab6fa7`, 3 Codex commits; 2 modified harness scripts uncommitted; untracked run evidence (logs, before/after captures, tools, `plan.md`, `wording-holdout.json`, `baseline.json`, `worktree-status-audit.json`) |
| other agents | the VS Code Codex app-server process was alive but idle; no file changed under me during the resume (checked before every commit) |
| `main` / merge-base | `bb61a804` / `bb61a804` |
| user's uncommitted work | `frontend/index.html` (old worktree `axo-pedagogical-integration`), `.playwright-mcp/` (main checkout) — untouched |
| `CACHE_VERSION` | 132 throughout |

Commits (see `run.json`):

| commit | by | kind | what |
|---|---|---|---|
| `0fb49397` | Codex | product | hover drawn as a transient material change; no geometry rebuild on hover; Vitest ≤ 4 workers |
| `5558b1ba` | Codex | product | restored camera pose keeps scene-derived zoom/clip bounds |
| `21ab6fa7` | Codex | product | section narration explains certified cuts through unnamed vertices |
| `6dbbd019` | Claude | test/docs | Codex's uncommitted harness edits kept (820/1280 px, `--skip-recovery`); CODE_INDEX |
| `a994790f` | Claude | eval | candidate frozen after the Codex product commits |
| `703f3b5d` | Claude | product | registry grounds "mặt phẳng (đi) qua (ba điểm) U, V, W" and its appositive form |
| `4e7ea0dc` | Claude | eval | candidate frozen at `703f3b5d`, templates rebound |
| (evidence, docs) | Claude | eval | this run folder |

## B. What the previous agent did, and what was kept

| area | Codex | evidence Codex left | verified on resume | kept? |
|---|---|---|---|---|
| hover rebuild | `applyHoverFeedback`, hover removed from the scene-build deps, `__geo3d_geometry_build_count` | `hover-before.log` FAIL (110/110 on pointer-enter) → `hover-after.log` PASS; unit red→green | code read; targeted tests 38/38; my own GL counter before/after (C) | yes |
| camera | restore pose after the fit | `camera-before.log` 8/10 (nested pyramids zoom to 0.0044) → `camera-after.log` 10/10; recovery red (3.01 → 0.12) → green | code read; final camera run (D) | yes |
| narration | engine-certified cuts and face traces | `narration-red.log` 9 failed → `narration-targeted-final.log` 33/33; held-out 11/11 | code read; real Case C capture reads "… còn gặp các cạnh CD, AD … thiết diện ngũ giác" | yes |
| wording (D) | `evaluate_wording.py`, `wording-holdout.json` | **8/16 INCORRECTLY_REFUSED** | reproduced; root cause fixed (E) | evidence kept unchanged; tool given an optional output name |
| publication | `audit_publication.py` (metadata only) | not yet run | read; run on the final HEAD (H) | yes |
| harness | 820/1280 px widths, `--skip-recovery` | uncommitted | read, committed | yes |
| report/handoff/run.json, T3, freeze | not done | — | done by Claude | — |

Nothing Codex wrote was found wrong; one finding Codex recorded (wording) was a real product gap and is fixed.

## C. Hover without geometry rebuild

Root cause [code]: `hoveredObject` was a dependency of the 1 000-line scene-build effect, and hover emphasis was baked
into `buildObject3D`, so every pointer enter/leave disposed and rebuilt the whole scene (buffers and shader programs).
Fix (Codex `0fb49397`): hover is applied at draw time on existing materials by `applyHoverFeedback` and undone right
after `renderer.render`; selected objects are untouched; tooltip, click-select, hide/isolate, drag unchanged.

Before/after [browser] (`perf/hover-gl-B.jsonl`, `perf/hover-gl-C.jsonl`; production builds of `e23e3983` vs HEAD's
frontend; 5 enter/leave cycles per scene):

| scene | baseline: GPU objects created/deleted per enter, per leave | candidate | long tasks baseline → candidate |
|---|---|---|---|
| pyramid section | 262 / 262, 262 | 0 / 0, 0 | 55 ms, 52 ms → none |
| sphere cut by plane | 110 / 110, 110 | 0 / 0, 0 | 51 ms → none |

Regression locks: `scene3d-hover.test.ts` (unit, red on the old effect), E2E "starting a drag over an object does not
rebuild the scene" and Codex's hover-lifecycle checks in `axo-scene-consistency-browser-check.mjs` [test/browser].

## D. Camera, orbit, zoom

Root cause [browser + code]: a recovered camera pose was applied INSTEAD of the scene fit, so OrbitControls kept its
default zoom bounds (0..∞) and clipping; after a reload the minimum distance fell from 3.01 to 0.12 and nested pyramids
could be zoomed to 0.0044 (inside the figure). Fix (Codex `5558b1ba`): fit first (bounds, clipping), then restore the
pose. Final camera-views run on the final build: **10/10 scenes PASS** (`final/camera-views/`, incl. nested pyramids and reload recovery of zoom bounds). Orbit gate v4: **DAT/DAT/DAT** on p1/p6/p7 (`final/orbit-gate/ORBIT_GATE.json`). No camera jump on step change,
selection or dock toggle (asserted per scene); reset returns to the default pose; legitimate flattened views near the
axis are not treated as defects.

## E. Construction provenance and narration; TypedFactNext /2 wording

Narration [test, browser]: for a polygon section the presenter reads the engine's `vertex_sources`
(SOLID_EDGE_INTERSECTION / SOLID_VERTEX) and certified face traces, names cuts through unnamed vertices by their solid
edge ("giao điểm của CD với mặt phẳng cắt") and lists "Trên mặt (…), nối … với …"; it never re-intersects, never invents
a label, and an exterior line–plane point (Case C's Q) is not a section vertex. No Case C / MNP / fixture key in code.

Wording [test]: held-out set by Codex (2 notations × 4 wordings × 2 premise orders, offline replay) — before 8/16
served, 8 INCORRECTLY_REFUSED (`wording-holdout.json`); after `703f3b5d` 16/16 CORRECTLY_SERVED, all 4-vertex sections
(`wording-holdout-after.json`). Root cause: the Source Gate's plane operand (two copies: the cut-by grammar
`_MAT_TOAN_HANG`, the ask grammar `_mat_cum`/`_mat_cua`, and the plane-mention check `_co_mat`) only read "(UVW)"/"UVW".
Fix: the three-label list after "qua" lives in the same operand group (every reader sees the same label set); a
"(UVW) đi qua ba điểm U, V, W" appositive is read only when it names the same points — "… U, V, K" is refused [test].
`test_hybrid4_three_point_plane_sections.py` 20/20 (4 wordings exact against the independent oracle, 2 inconsistent
wordings refused). CACHE: no cached SERVED result changes meaning (only refused inputs change); `test_cache_identity.py`
15/15 unchanged. Live extraction of these wordings NOT_MEASURED (no provider call) [not verified].

## F. Performance and resources

Same machine, production builds, Chrome 157 headless 1440×900, GPU from SystemInfo: Intel(R) UHD Graphics (ANGLE); no
phone or NVIDIA claim. Baseline `e23e3983`, candidate HEAD frontend. Raw samples in `perf/`.

Navigation (4 runs B C C B × 12 = 24 samples per build): cold library 140.5/203.3 → 135.9/201.0 ms (median/p95); cold open
170.3/297.9 → 170.5/275.9; warm reopen 123.1/167.4 → 116.3/135.8; Back 68.0/97.5 → 65.1/78.2; Forward 112.1/175.2 →
111.1/139.1.

Scenes (clean runs `perf-3-C`, `perf-4-B`, `perf-5-B`, `perf-6-C`; `perf-1-B`/`perf-2-C` excluded — they overlapped a
pytest run I started by mistake): step-change medians within ±3 ms on all seven scenes (e.g. pyramid 64.5 → 61.0, cube
hexagon 65.0 → 65.3, dense multi-solid 49.4 → 51.2 ms); frame-interval p95 7.0 ms both; frames > 16.7 ms ≤ 0.05 % both;
1 render per frame; GPU created − deleted 0; heap after a scene 29–54 MB with swings in both directions.

Reading: the hover change is a real, measured improvement (C); everything else is within run-to-run variation — no
speed-up claimed. Resources: free RAM 6.2 GB of 16 GB and CPU ≈ 6 % at resume; Vitest capped at 4 workers; one browser
at a time; Docker/WSL and user processes untouched. One process slip: the geometry pytest overlapped two perf runs
(≈12:53–13:00); detected from timestamps, those runs excluded and re-measured.

## G. Visual QA and product decisions

Final build (frontend of HEAD = product `21ab6fa7`; backend change `703f3b5d` is offline-only), logs `final/browser-*.log` [browser]:

| check | result |
|---|---|
| two real tabs, 7 scenarios + retry | 8/8 |
| E2E scene consistency: every catalog route, statement/scene identity, no answer surface (no "Xem kết quả", no "KẾT LUẬN", no answer token in DOM/ARIA), history, reload, Back/Forward, real composer, deep-frozen Scene3D, drag/hover lifecycle, widths 360/390/430/768/**820**/1024/**1280**/1440, real Chrome zoom 110 % | 41/41 |
| UI harness (cards, labels, scrolling, per-problem restore, camera across dock, zoom 110 %) | 40/40 |
| camera views (pyramid, three-point pentagon, oblique prism, cube hexagon, sphere cut, tangent plane, cylinder, cone, nested pyramids …) | 10/10 |
| orbit gate v4 | DAT ×3 |

Inspected by eye: 360 px and 820 px sphere-section captures (given data only, right-angle mark, labels attached, no horizontal
overflow), Case C pentagon narration (B). Product decisions held: no answer button or conclusion panel, no quiz, no new
Scene3D mode, no design change.

## H. Publication safety

Scanner `backend/scripts/check_publication_safety.py` and the metadata-only classifier `tools/audit_publication.py`
(output `publication-audit.json`: path, blob, line, content SHA-256, classification, decision — no flagged value) on
HEAD `bac9e065`:

| scan | result |
|---|---|
| this task `1be6a7ae..HEAD` | **PASS** (0 violations) |
| whole integration `bb61a804..HEAD` | BLOCKED: 1 × `HARDCODED_PASSWORD` · commit `6533b586` · `backend/tests/test_auth_api.py` · blob `28be1ef6…` — TEST_FIXTURE (change-password test on a throw-away DB, never outside `backend/tests/`, absent from HEAD since `cb564b1e`) |
| HEAD tree | BLOCKED: 98 findings, all already pending owner exceptions, 0 new — 95 HISTORICAL_DIAGNOSTIC_TRACEBACK (90 contain a local Windows path with the OS user name; no key/token), 2 REDACTION_TEST_PLACEHOLDER (`Bearer` placeholder in a redaction test and its scan report), 1 TEST_FIXTURE (`TEST_PASSWORD` constant in `tests/conftest_classroom.py`); 0 NEEDS_MANUAL_SECRET_REVIEW |

No exception created, no pending entry removed, no history rewritten, no value printed. Lowest-risk handling for the
owner: exact-blob exceptions for the fixture/placeholder findings; for the traceback logs, accept or replace by summaries
in a new commit (history keeps them either way). Status: **BLOCKED pending owner decision**.

## I. Full T3 gate

Tested tree **`bac9e065`** (evidence commit; product `703f3b5d` backend + `21ab6fa7` frontend), clean detached worktree
(`git status` empty before/after), log `logs/t3-full-gate-bac9e065.log`:

| gate | result |
|---|---|
| **T3** `frontend/scripts/full-gate.mjs` | **FULL_PRODUCT_GATE_PASS** (456.7 s) |
| ↳ full pytest | 13 842 passed, 7 skipped, 3 deselected (opt-in), 9 xfailed |
| ↳ Vitest (≤ 4 workers) | 131 files / 1 943 tests |
| ↳ `tsc -b` + production build | pass |
| ↳ demo replay · crash surface | 5/5 · pass |
| node harness, same clean tree | 153/155, 0 fail, 2 environment skips (`logs/node-harness-bac9e065.log`) |
| candidate seal `--verify` | matches 103 files `5ef50761…` |

Not run in this task: PostgreSQL opt-in tests (backend persistence untouched since the previous run, where they passed;
Docker not started, by instruction) [not verified on this HEAD]; live provider calls (forbidden).
After the tested tree: one docs-only commit (this report's §H/§I/§K, `run.json`, `handoff.md`, EVIDENCE_INDEX, the two
copied logs, `publication-audit.json`); docs gate, seal and publication scan re-run on it.

## J. Remaining risks and owner decisions

Owner decisions (`OWNER_DECISION_REQUIRED`): publication exception for `6533b586` and the pending entries (H); merge/push.
Open, not fixed: live extraction of three-point wordings NOT_MEASURED; three-point planes with stated cuts / declared
boundary still refused (`UNSUPPORTED_CAPABILITY`); idempotency single-process (locked by test); telemetry row after the
response may be lost on a crash (undercount); performance only on Intel UHD.

## K. Conclusion

**BLOCKED_BY_OWNER_DECISION.**

Technically the task is complete and verified on the final tree: hover no longer rebuilds geometry (262/110 GPU objects
and 51–55 ms long tasks per hover → 0) [browser/test]; camera restore keeps scene zoom/clip bounds [browser/test];
section narration explains every certified cut through an unnamed vertex from engine provenance [test/browser]; the
three-point plane is grounded in all four standard wordings (held-out 8/16 → 16/16, inconsistent wording refused)
[test]; product decisions held (no answer surface, no quiz, no new mode) [browser]; T3, node harness and the browser
suite are green on the final tree; performance otherwise within variation.

What blocks a merge is not technical: the publication gate is BLOCKED by findings only the owner may except (H), and
merge/push needs explicit permission. Nothing was merged or pushed.
