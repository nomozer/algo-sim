# Geometry library expansion: fixes for review findings I1–I3

Status: `GEOMETRY_LIBRARY_IMPORTANT_FIXES_AWAITING_REVIEW`

- **Branch:** `feat/geometry-library-expansion`. It starts from the independent review (`c6a99ac6`, [report](../geometry-library-integration-review/report.md)).
- **Scope:** the user approved fixing findings I1, I2 and I3 within the scope the review defined.
- **Constraints kept:** LIVE GEMINI CALLS = 0. No paid API, no merge or push, no default switch (`LLM_ONLY`, `CACHE_VERSION` 125 unchanged).
- **History:** no historical artifact was rewritten.

## 1. How each finding was resolved

### I1: a forward projection re-rooted the tetrahedron in the scene

**Root cause.** Two places dropped the topology the problem declares:
- The engine supplemented the program with `formation.hoan_thien_dung_hinh(spec)` **without a contract**.
- The function route built scene roles with `build_simulation_state(spec, exec_result)`, also without one.

Formation therefore read the four-way tetrahedron from typed relations alone. The new `project_onto(A, plane SBC)` IR was the only such relation, so it became "apex A, base SBC, height AK".

**Fix.** One authority feeds both places.
- `engine.hop_dong_to_po_da_khai(calls)` returns `RequestContract(solid_topology=PyramidTopologySpec(...))`. It does so only when there is exactly one solid, it is a pyramid, and its source quote writes the dot notation `S.ABC` matching the call's apex and base.
- "Tứ diện ABCD" names no apex. The apex in the call is then the model's or planner's choice (planner B picks the last letter), so the function returns `None` and no topology is invented.
- The same value is stored on `KetQuaTuyen.declared_topology` and passed to the scene.

**Auxiliary perpendicular.** A `project_onto` point now carries `perpendicular_witness`:
- the from point,
- the exact kernel foot, which must equal the constructed point or the scene is refused,
- marker vectors `u` and `v`.

It reuses `quantity_annotations._nhan_chung`, the helper behind distance witnesses. The renderer draws it through the existing `vatNhanChung`. `projectionWitnessesAt` shows it only when the projected point is present at the current step (invariant #31). It is never a solid edge or a "Chiều cao".

What was not changed: no new Scene3D builder, no kernel coordinates, no IR schema.

### I2: product identity ignored renderer changes

**Root cause.** `3b6104e3` narrowed `product_commit_sha` to `MEASURED_SYSTEM_PATHS`. That avoided refreezes for test-only frontend commits, but it also hid real renderer fixes: the W12 incident class.

**Fix.**
- `product_commit(rule, rev)` = last commit on `backend/app` + `frontend/src` minus `TEST_ONLY_GLOBS` (`*.test.ts[x]`, `*fixture*.json`, `test-setup.ts`, `test-source.ts`).
- The rule is named in the manifest: `product_commit_rule = product-paths-excluding-test-only/1`.
- A manifest without a rule name is verified with the legacy rule. All **61** historical candidate manifests re-derive their own `product_commit_sha` (a test checks this), so no historical identity changes.
- `MEASURED_SYSTEM_PATHS` is unchanged.
- The read-only `ALGOSIM_TEST_CANDIDATE` override is removed.

### I3: the full backend gate was green only under overrides

The reproduced reds and how each was resolved:

| Reproduced red | Resolution |
|---|---|
| 6 × `TOKEN_CAP` in the A/B runner tests: the current registry's SMOKE_AB reservation exceeds the locked 500,000 accounted tokens | Split into three questions, below |
| 2 × candidate identity | The divergence declaration is found by following the `corrects` chain from the locked A/B file, not `ALGOSIM_TEST_DIVERGENCE`. `EVALUATION_CANDIDATE.json` is refrozen by the standard protocol in a clean detached worktree (separate commit), not via `ALGOSIM_TEST_CANDIDATE` |

The `TOKEN_CAP` reds are split into three questions:
1. **Does the locked A/B pilot still reproduce?**
   - The two runner modules always run on the locked provider surface: a committed fixture extracted from `2990d87d`.
   - The fixture is accepted only if both arms hash to the surfaces recorded in the locked `fake-provider/final/CERTIFICATION.json` (A `f329e891…`, B `aa198078…`).
   - No environment switch and no external worktree; budget, hash, source and network guards stay on.
   - A tampered fixture is refused (two mutants).
2. **Is the current product correct?** The product and geometry suites run on the current adapters.
3. **May the current surface run a live pilot?**
   - **NO-GO**, locked by `test_hybrid_ab_branch_readiness.py`.
   - Caps are asserted unchanged; the current surface is not the locked one; the SMOKE_AB reservation exceeds 500,000.
   - The runner stops at `TOKEN_CAP` **before completing its 24 calls**. Against a real provider the calls made before the stop would be spent, so a pilot on this surface needs its own pre-registered budget.

No cap, corpus, oracle or hash was changed or faked, and no test was skipped.

## 2. RED → GREEN

| Finding | RED (watched failing first, for the right reason) | GREEN |
|---|---|---|
| I1 backend | 10 failures: A/B/C onto the opposite face re-rooted (×2 arms), S.ABC skeleton not drawn, missing witness. 4 guards green before the fix | `test_projection_scene_topology.py` 17/17, including 3 behavioural mutants (drop topology, invent topology, drop witness) |
| I1 frontend | `projectionWitnessesAt` not a function (2) | `scene3d-annotations.test.ts` 25/25 |
| I2 | 12 × missing `product_commit`/`TEST_ONLY_GLOBS` | 12/12; real commits in a throwaway repo cover test-only, backend, renderer (W12), fixture-only, missing measured file, right and altered candidate (3 fields), legacy rule, 61-manifest history, no product import of an excluded file |
| I3 | plain `pytest`: 6 runner + 2 identity reds (review) | runner + readiness 93/93 with no env; readiness 7/7 |

## 3. Remaining defects

- **Orbit browser gate is red in this environment.**
  - `scene3d-orbit-gate.mjs`: `KHONG_DU_VONG` on p1/p6/p7 (333–348° against the historical 437°).
  - The pre-fix renderer (`c6a99ac6`) built and measured the same way, on the same machine, fails identically (336–342°). Every other metric is identical.
  - So it is not attributable to this wave, but the gate is **not green**. Results: `diagnostics/orbit-gate-*.json`.
- **Intermittent test, cause UNKNOWN.** `test_generic_tier_a_fixture_generator.py::test_cross_section_fixture_preserves_verifiable_measurement_provenance` failed in 1 of 3 full runs. The generator subprocess exited non-zero, and its stderr was not captured. It passes in isolation and its script passed 6/6 direct runs.
- **Windows prerequisite.** The repository contains paths longer than 260 characters. Without `core.longpaths=true`, `git status` reports 151 phantom changes and `test_holdout_readiness` sees a dirty tree. This predates the branch: the expansion run also set it.
- **Minor display findings from the review are still open:**
  - m2: label collision hides some vertex labels depending on the view.
  - m3: a midpoint can appear before its segment.
  - m4: order-strict plane binding.
- **Existing gap, not introduced here.** For an undeclared "tứ diện ABCD", formation may still read an apex from a projection relation.

## 4. Backend gate

| Run | Commit | Environment | Result |
|---|---|---|---|
| 1 | `797138da` | plain (no `ALGOSIM_*`, no `PYTHONUTF8`, no longpaths) | 8196 passed, **2 failed**: my I2 history test decoded UTF-8 with the console code page (fixed in `811896f8`); `test_holdout_readiness` (longpaths, above) |
| 2 | `811896f8` | plain + `core.longpaths` | 8197 passed, **1 failed** (intermittent, above) |
| 3 | `811896f8` | plain + `core.longpaths`, `--showlocals` | **8198 passed, 0 failed**, 1 skipped, 2 deselected, 377.20 s |

All runs used a clean detached worktree, `ALLOW_LIVE_AI=0` and `PYTHONIOENCODING=utf-8`. Summaries: `diagnostics/full-backend-*.summary.txt`. The worktree was clean after every run.

## 5. Candidate freeze / verify

- **Frozen:** in a clean detached worktree at `66aad28f`, committed as `797138da`. Product commit `4ad89909`, rule `product-paths-excluding-test-only/1`, `cay_lam_viec_sach: true`, 110 files.
- **`--verify` exit 0** at `66aad28f` and again at `811896f8`. That second commit only touches a test, so by the I2 rule the candidate stays valid with no refreeze.

## 6. Visual regression

The real `Scene3DWorkspace`, served from a static build of `diagnostics/review-visual.tsx` on 127.0.0.1. 24 screenshots in `screenshots/`.

| Label | Scope |
|---|---|
| VERIFIED_BY_AUTOMATED_TEST | Topology labels, K/H coordinates, witness foot = point, witness only when the point is present, A/B scene byte-equality (9 scenes) |
| AGENT_VISUALLY_INSPECTED | See below |
| HUMAN_ACCEPTANCE_PENDING | Every scene. No user has accepted any visual |

What the agent inspected:
- **S.ABC without a projection:** apex S on top, base ABC, hidden edges dashed.
- **A→(SBC), B→(SAC), C→(SAB):** S stays the apex and ABC the base. The dashed auxiliary perpendicular and the right-angle square are anchored at K, and stay anchored after rotation and zoom.
- **Square-pyramid scenes D→(SBC) and A→SO:** now have the perpendicular and marker at H.
- **SO∩AM, AC∩BD, BN∩AD:** unchanged.
- **Formation order:** the witness and K appear together at step 2, not before.
- **Mobile 390 px:** no horizontal scroll.

## 7. Backend and frontend tests

- **Backend:** see section 4.
- **Focused function route:** 311/311.
- **Frontend:**
  - full vitest 1050/1050 (68 files);
  - geometry domain + `code-index-sync` 700/700;
  - `npm run build` (`tsc -b` + vite) PASS.

## 8. Candidates

| Candidate | Hash |
|---|---|
| New (this wave) | `a8dc02fc…` (110 files, product `4ad89909`) |
| Previous branch | `8ff994c6…` |
| Locked A/B | `12da4768…` (untouched; still certified by its own evidence) |
| Thesis run | `d72db7c3…` |

Divergence is declared as a correction layer in `candidate_divergence.json`.

## 9. Commits of this wave

| Commit | Role |
|---|---|
| `4ad89909` | I1 fix (engine, function route, renderer, tests, CODE_INDEX) |
| `b1333695` | I2 fix (freeze script + tests) |
| `176f77f0` | I3 test gate (frozen surface, readiness, corrects chain, telemetry revert) |
| `66aad28f` | divergence declaration |
| `797138da` | candidate refreeze |
| `811896f8` | test UTF-8 decoding |
| docs commit | this report, living docs |

## 10. Integration readiness

**Ancestry.**
- `main` = `28ac1d61` is the merge-base, with no commits since.
- The research line is linear on top of it: 28 `text-to-geometry-functions`/hybrid commits, then 9 expansion commits, the review, and this wave.
- None of it is in `main`.

**Proposed plan** (not executed):
1. Create `integration/geometry-functions` from `main`.
2. Fast-forward it to the reviewed HEAD of this branch. There are no conflicts because the history is linear and nothing is rewritten.
3. Run T3 (`npm run test:full`) and the orbit gate there.
4. Integrating means taking the whole research line: `geometry_functions/` does not exist on `main`. It stays off the default route (import-closure guard).

**What should not be taken separately:** nothing now needs excluding. `3b6104e3`'s freeze narrowing and the env-based plugin are superseded inside the linear history by `b1333695` and `176f77f0`, so cherry-picking older commits alone would reintroduce them.

**Decision.** Code-level evidence is strong:
- all three findings are fixed with RED→GREEN and mutants;
- plain backend 8198/0;
- frontend 1050/0.

But integration is **NOT GO yet**, because:
- the orbit browser gate is not green in this environment (it fails identically before the fix);
- one backend test is intermittent with an UNKNOWN cause;
- human visual acceptance is pending.

| Use | Decision |
|---|---|
| Live pilot | NO-GO |
| Default switch | NO-GO |

## 11. Next steps

1. Human review of `screenshots/` (tetrahedron and projection scenes).
2. Orbit gate: run it on the machine or state where the historical 437° was measured, pre-fix and post-fix side by side. If both still fail, recalibrating the gate is a separate decision.
3. Capture the generator's stderr on the next intermittent failure (the test discards it; rerun the full suite with that output kept) to find its cause.
4. Set `core.longpaths=true` for the repository on Windows, or document it as a gate prerequisite.
5. After approval: integration branch as proposed in section 10, then T3 there.
