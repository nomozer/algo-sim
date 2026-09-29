# Verification cleanup after occlusion repair (w09)

Status: `READY_FOR_HUMAN_VISUAL_REVIEW` — automation only. Human visual review is
**not** approved; nothing here is `MERGE_READY`.

This run corrects the prior wave `CROSS_FAMILY_HIDDEN_LINE_OCCLUSION_ORACLE_AND_FORMATION_REPAIR`
(`VERIFICATION_NOT_CLEAN`). Its artifacts, including the frozen
`human_expected_visibility.json`, are byte-identical.

## Identity

- Branch `fix/cuboid-visual-semantic-closure`, start `42c736ea`, `origin/main` `a9492ee9`.
- Measurement commit `defb77ed` in a detached clean worktree without a local `.venv`.
- Candidate `31725284…` → `3bc9415b…` (refrozen in a clean worktree at `1d1397fa`, commit `5bd8b52c`).
- `CACHE_VERSION = 102`, provider fingerprint `b1714b566e25c912` unchanged, `DEFAULT_MODE = LLM_ONLY`,
  0 live Gemini requests, 0 application LLM calls.

## Fresh reproduction (before any change)

`diagnostics/VERIFICATION_FAILURE_INVENTORY.json`: 40 records, 0 unresolved —
31 backend (main tree), 1 frontend, 2 frozen camera, 5 mobile immutable, 1 detached
full-gate. A detached rerun at `42c736ea` adds exactly 3 detached-only backend failures
(34 = 31 + 3, `diagnostics/DETACHED_BACKEND_BEFORE.txt`). The prior wave's "35" was never
itemized; the difference of 1 is `NOT_RECOVERABLE`.

## Root causes and repairs

| Group | Classification | Root cause | Repair |
|---|---|---|---|
| 28 curved/oblique runner tests | `REAL_PRODUCT_REGRESSION` | `50a31e0b` ships timeline `details` in `scene3d.events`; `_json_an_toan` left `Plane3`/`Circle3`/`Ellipse3` raw. Real case P6 (ellipse section of a cylinder) is `served` yet `main.py`'s cache `json.dumps` would return HTTP 500 | Geometric values take the scene's own `_than_hinh_hoc` shape; unknown runtime types raise `TransportTypeError` (`f337323f`) |
| 5 mobile `immutable_120_frames` | `REAL_PRODUCT_REGRESSION` | Idle OrbitControls damping rewrites the pose in its last ULPs every mobile frame (841/841 recomputes over 6 s); the classifier keyed on raw floats | Camera key at 10 significant digits; a 0.6 px pose change on any axis still invalidates (`7b8528a9`) |
| (found while measuring) | `HARNESS_SETTLING_DEFECT` | Window poll read counters published before the reset (frame_count 138 ≥ 120) | Zero the published counters in the reset task (`91d3e9c3`); harness also settles before snapshots and windows |
| 2 frozen camera identities | `FROZEN_IDENTITY_CANONICALIZATION_DEFECT` | Registry binds reviews to raw-float snapshot hashes; three were pre-settle transients | Verified preimages (sha256 = registered hash, recovered by replay) + projection equivalence ≤ 0.5 px; registry untouched (`7b8528a9`, `fe3eccee`) |
| 1 frontend guard | `LEGACY_TEST_FALSE_POSITIVE` | `/boundary\|corners\|extent/` matched the topology field `boundary_edge_ids` | Assert on declared field names with red cases (`1f151f8d`) |
| 2 golden hashes | `INTENTIONAL_GOLDEN_CHANGE_REQUIRES_REVIEW` | Occlusion wave added fields; `_bam` hashes `repr` | Semantic diff vs `532d4366`: ADDED only (P1 75, P6 28), 0 changed/removed, object counts equal, `final_memory` math unchanged (`9c233f10`) |
| 1 candidate declaration | `STALE_CANDIDATE_OR_REPORT_GUARD` | Refreeze `e115c31d` skipped the per-wave divergence declaration | New declaration in this run, correcting the 20260927 one (`6f8f675e`) |
| detached full-gate + 3 detached-only tests | `DETACHED_ENVIRONMENT_DEFECT` | `URL.pathname` kept `%20`; silent fallback to `python` on PATH; prechecks required a branch name; CRLF-checkout hashing | `resolvePython`/`runGate` (`1d1397fa`); checkout-independent checks (`defb77ed`) |

Every guard added in this wave was shown red first and by fault injection
(raw transport pass-through, coarse or pose-less camera key, forbidden `corners`
field, pathname root, disabled version check, always-stable settle, ignored recompute).

## Final verification (fresh, measurement commit)

| Gate | Result |
|---|---|
| T3 `full-gate.mjs` in the detached worktree | `FULL_PRODUCT_GATE_PASS`, exit 0 — Python `main_worktree_venv` 3.12 |
| Backend full (inside T3) | 6314 passed, 0 failed, 1 skipped, 1 deselected |
| Frontend full (inside T3) | 906 passed, 0 failed; typecheck + production build PASS |
| Browser, 6 families × desktop 1440×900 + mobile 390×844 | 12/12 positive, 12/12 negative PASS |
| `immutable_120_frames` after settling | 12/12, max recompute 0 |
| Frozen camera identity | 3 `EXACT`, 3 `CANONICAL_EQUIVALENT` (≤ 1e-12 px) |
| Product ↔ oracle exact edge IDs and spans; perspective reference | 0 mismatches |
| Candidate / cache / schema export twice | PASS / PASS / byte-identical |
| Backend reconciliation | 34 records, 0 unaccounted, 0 weakened assertions, no bulk snapshot acceptance |

## Limitations (not hidden)

- Frontend tests build paths from `URL.pathname`: vitest fails from a worktree path with a
  space (11 files, 23 tests at `fe3eccee`). `full-gate.mjs` itself handles spaces; the test
  defect is registered as `ISSUE-OPS-FRONTEND-TESTS-SPACE-PATH`.
- Orbit evidence is intermittent: attempt 1 at `defb77ed` stopped with `ORBIT_EVIDENCE_TIMEOUT`;
  the rerun at the same commit passed. All attempts: `diagnostics/MEASUREMENT_ATTEMPTS.json`.
- The frontend geometry product change (`7b8528a9`) is outside `MEASURED_SYSTEM_PATHS`, so the
  candidate hash does not cover it; the browser evidence binds it through the measurement commit.
- No human has reviewed the new screenshots or contact sheet.
