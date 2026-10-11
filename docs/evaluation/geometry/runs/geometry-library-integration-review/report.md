# Geometry library expansion: independent review and integration readiness

Status: `GEOMETRY_LIBRARY_INTEGRATION_READINESS_AWAITING_APPROVAL`

- Branch `feat/geometry-library-expansion`, reviewed at `be6608a3`, base `2990d87d`.
- Review commit: `0343d5ed`, which adds only a strict-xfail test; no source change.
- Reviewer: an independent session. It did not write the implementation and reran nothing from the handoff on trust.
- LIVE GEMINI CALLS = 0. No paid API, no merge or push, production default unchanged.
- No historical artifact was rewritten. Candidate `8ff994c6…` is unchanged because this review touched no measured path.

## 1. Findings

### Critical

None.

### Important

**I1. A forward plane projection re-roots a tetrahedron in the scene. The math is right; the scene identity is wrong.**

- **Trigger.** In S.ABC with apex S declared, the fact "K là hình chiếu vuông góc của A lên (SBC)" computes K = (3/8, 3/8, 1/4) exactly.
- **Symptom.** The scene is built as apex A over base SBC: `Đáy SBC`, `Chiều cao AK`, and lateral edges AS, AB, AC. The same happens for B→(SAC) and C→(SAB).
- **On screen.** The display rotation lays SBC flat, so the declared apex S is drawn at the bottom. The right-angle marker sits partway along AK, not at K; its root cause is UNKNOWN.
- **Root cause.** `app/ai/function_route.py` calls `build_simulation_state(spec, exec_result)` without a contract. `formation.lop_khoi` has no declared `solid_topology`, so it settles the four-way tetrahedron reading from typed relations. The new `project_onto(A, plane SBC)` IR is the only such relation.
- **Why the branch tests missed it.** All oracles use the square pyramid, which has a single face reading.
- **Recorded.** RED as strict xfail in `backend/tests/geometry/test_projection_scene_topology.py`.
- **Fix: deferred by the user's decision.** Pass the declared topology into formation. This also changes tetrahedron scenes without a projection, which today draw no base or edges at all (see m7), so it is outside the two primitive groups.

**I2. The branch weakens a shared measurement rule outside primitive scope.**

- **Change.** `scripts/freeze_evaluation_candidate.py` now derives `product_commit_sha` from `MEASURED_SYSTEM_PATHS` instead of `backend/app` + `frontend/src` (commit `3b6104e3`). `test_product_provenance_uses_measured_paths_not_renderer_tests` locks the new behaviour in.
- **Why the branch made it.** A test-only frontend commit (`ddb0ce34`) would otherwise move the product commit.
- **Side effect.** A real renderer fix under `frontend/src` (outside `domains/semantic`) can no longer turn `--verify` red. That is the W12 incident class, where a renderer fix was measured without a refreeze.
- **Fix options.** Exclude test files from the old path set, or keep the old rule. Do not integrate `3b6104e3`'s freeze-script hunk without an explicit decision.

**I3. "Full backend 8166 PASS" holds only under the three branch-identity overrides.**

A plain `pytest` on this branch has 8 red tests:

| Tests | Cause | Assessment |
|---|---|---|
| 6 in `test_hybrid_ab_pilot_runner` and `test_hybrid_ab_pilot_mutations` | `TOKEN_CAP`; accounted tokens 536,172 against a pre-registered cap of 500,000 | The expanded registry no longer fits the locked pilot budget |
| `test_ma_san_pham_khong_troi_khoi_ban_da_dong_bang`, `test_C2b_candidate_hien_tai_phai_duoc_KHAI` | Branch candidate differs from the frozen one | Expected divergence |

The override mechanics are sound:
- The plugin pins the frozen surface to product hash `12da4768…` and only rebinds `build_request` for the two runner modules.
- `ALGOSIM_TEST_CANDIDATE` is verify-only: freezing is refused, and drift and missing files are rejected.

So the overrides do not certify the wrong candidate, but they are not an integration gate either. Integrating this branch into the A/B line breaks the pilot budget certification until the caps are re-registered. The handoff discloses this; this report states it as a blocker.

### Minor

- **m1.** Perpendicular feet are drawn without the perpendicular segment or a right-angle marker, even with auxiliary on (D→(SBC), A→SO). Intersections show their defining lines only with auxiliary on.
- **m2.** Existing renderer label collision hides given-vertex labels in the default view (A and M in SO∩AM, on desktop and mobile). They reappear on rotation.
- **m3.** Formation step 4 shows midpoint M before segment SC is drawn.
- **m4.** Source binding of plane operands is order-strict: "(ABD)" with plane `[A,D,B]` is refused. It also accepts "đáy" for projections but not for intersections. Both fail closed.
- **m5.** On Windows without `core.longpaths`, the worktree shows about 150 `worktree-recovery` screenshots as deleted. A blanket `git add -A` would stage those deletions.
- **m6.** Kernel `intersect_line_line` reports skew lines under the PARALLEL code. The engine classifies skew lines first, so callers see `SKEW_NO_INTERSECTION`. No action needed.
- **m7.** Not introduced by this branch: S.ABC on the function route with no extra fact renders no base polygon or edges (ambiguous reading).

## 2. Oracle and regression results

**Focused suite** (expansion, text-to-functions, AI route, hybrid selection): 311 passed, 0 failed.

**Independent probes** (`diagnostics/probe.py`): 32/32 match on both arms. Expected values are hand-derived in Euclidean coordinates; no kernel call.
- **Two derived operands.** SO∩AM = (1/3,1/3,1/3), in both call orders.
- **Projection onto a derived line.** A→SO = (9/22,9/22,2/11).
- **Intersection outside the segments.** BN∩AD = (0,2,0).
- **Non-orthogonal Gram, plane projection** (not covered by the branch tests). A→(SBC) = (3/8,3/8,1/4) and B→(SAC) = (0,1/2,0). Line projection S→BC = (1/2,1/2,0).
- **Fail-closed classes:**
  - skew → `SKEW_NO_INTERSECTION`
  - parallel lines, and a line parallel to a plane → `PARALLEL_NO_INTERSECTION`
  - coincident lines, and a line inside a plane → `CONTAINED_INFINITE_INTERSECTION`
  - non-coplanar plane points → `NON_COPLANAR_POINTS`
  - collinear plane points → `COLLINEAR_POINTS`
  - self-referencing operand → `UNDERDETERMINED_POINT`
  - contradictory definitions → `INCONSISTENT_FACTS`

**Branch identity and docs:** with the overrides, the docs, telemetry, expansion, candidate and new RED tests give 173 passed and 2 strict-xfailed.

**Not rerun:** the full backend suite. This review changed no source code, so the handoff's clean run at `815f06be` remains the evidence, subject to I3.

## 3. Independent assessment of the new capabilities

- **Kernel math is sound.**
  - Line–line and line–plane intersections use coordinate-level formulas, which are affine-invariant.
  - Projections use `_metric` (Gram).
  - The engine's relation check is independent of the construction: incidence plus Gram-orthogonality, not a repeated kernel call.
- **Provenance is correct.**
  - Every new point carries `DERIVED`, a producer, dependencies and `relation_verified`.
  - The IR emits `construct_point` with an expression and never with coordinates.
  - The dependency order holds in both the trace and the formation.
- **One authority.** The engine calls the kernel. IR is re-executed by the existing interpreter. No second geometry authority exists.
- **Both adapters agree.** A and B produce byte-identical scenes in all 7 exported cases.

## 4. Visual inspection

| Label | Scope |
|---|---|
| VERIFIED_BY_AUTOMATED_TEST | Point coordinates, provenance and fail-closed codes (sections 1–2) |
| AGENT_VISUALLY_INSPECTED | The 12 screenshots in `screenshots/`. The real `Scene3DWorkspace` ran in a static build of `diagnostics/review-visual.tsx`, desktop 1280×900 and mobile 390×844. Covers intersection points on their lines, the extended line through X outside AD, hidden-edge dashing, auxiliary lines and planes, step order, rotate and zoom. The SO∩AM scene shows formation order: O and M before K. Defects: I1, m1–m3 |
| HUMAN_ACCEPTANCE_PENDING | Everything visual. No user has accepted any scene |

Browser console: only the harness page's favicon 404. The Vite dev server tripped a browser-side network denial, so the bundle was built and served statically on 127.0.0.1.

## 5. Remaining limits

- **Source grammar.** Bounded; unknown wording is refused.
- **Planes.** The first three plane points must be non-collinear.
- **Missing compositions.** No line-object composition, no section, no new base families.
- **Display gaps.** I1, plus m1–m3.
- **Not measured.** Real Gemini extraction of the new typed facts.

## 6. Candidate divergence

| Candidate | Hash | Scope |
|---|---|---|
| Locked A/B | `12da4768…` | Untouched |
| Branch | `8ff994c6…` (product `a0eb1450`) | Declared in `candidate_divergence.json` |

This review adds no measured-path change, so there is no new divergence.

## 7. GO / NO-GO

| Use | Decision | Why |
|---|---|---|
| Kernel and engine primitives (four functions, line targets, square-pyramid scenes) | GO | |
| Projection onto a face of a tetrahedron in the scene | NO-GO | Until I1 is fixed |
| Integrating `freeze_evaluation_candidate.py` changes and the root `conftest` plugin | NO-GO | Without a decision on I2 and I3 |
| Any SMOKE_AB or FULL_AB pilot | NO-GO | Until the token caps are re-registered (I3) |

## 8. Integration list (proposal only; nothing merged or cherry-picked)

| Commit | Content | Proposal |
|---|---|---|
| `86741f38` | Scope audit (docs) | Take |
| `4e2b3fb1` | Pre-registered oracles (tests) | Take |
| `f6df7646` | Exact intersections and projections (engine, planner, registry, prompt) | Take |
| `a0eb1450` | Source-role guard, projection dependencies | Take |
| `ddb0ce34` | Branch identity, renderer oracles | Take the tests; do not take the identity wiring |
| `1bbd0edb` | Fixture loading without conftest shadowing | Hold with I3 |
| `3b6104e3` | Read-only candidate verification and freeze-script path change | Split; the freeze-script hunk needs an I2 decision |
| `815f06be` | Telemetry identity, CODE_INDEX | Take the CODE_INDEX part |
| `be6608a3` | Handoff | Take as evidence |
| `0343d5ed` | RED strict xfail (this review) | Take |

Integration requires a refreeze of `EVALUATION_CANDIDATE.json` in a clean worktree at the integrated product commit.

## 9. Tests after integration

1. The full T3 gate, run plain, without `ALGOSIM_*` overrides.
2. The freeze-script `--verify` check, under whichever rule I2 settles on.
3. The I1 fix turns the strict xfail into a pass. Add a tetrahedron oracle for each vertex-to-opposite-face projection.
4. Browser gate `scene3d-orbit-gate.mjs` on a fresh build.
5. Token-cap re-registration before any pilot.
6. Human visual acceptance of the screenshots.
