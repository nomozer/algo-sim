# Agent takeover checkpoint (Codex → Claude), 2026-10-27

Supplementary record. It changes no earlier artifact in this run.

## Identity

- Branch `research/hybrid-v2-planner-generalization`, worktree `.superpowers/worktrees/planner-generalization/`.
- HEAD `386d214952e6a7ba98f0931b5ecfd7a5b89d1667` (= `main`, ancestor check OK). Staged: none. Tracked modifications: none.
- No process had the worktree in its command line at takeover (`Win32_Process` scan).

## Inherited untracked inventory (SHA-256 of raw bytes, first 16 hex)

| path (run-relative unless noted) | bytes | sha256[:16] |
|---|---|---|
| `plan.md` | 6320 | B077D97A32974BC4 |
| `capability-gap-matrix.md` | 15175 | 92E591AD2E18D333 |
| `inputs/development.json` | 78853 | 9B6C4206429FAE9E |
| `inputs/oracle.json` | 3462 | D6F3C6774AFDB52A |
| `results/baseline.json` | 8511 | 496C8994D63AB5E5 |
| `tools/corpus.py` | 10362 | EE6098BF7305199E |
| `tools/evaluate.py` | 5023 | AE46562F14D26B3E |
| `tools/oracle.py` | 2691 | 2A9CA0491E6F6232 |
| `tools/verify_baseline.py` | 3984 | 4C2752EB7BC6146E |
| `verification/baseline-candidate.json` | 3487 | 5A9E386521891590 |
| `verification/baseline-identity.json` | 3076 | 26DB5751BA0702AD |
| `backend/tests/geometry/test_prism_perpendicular_section_planning.py` (repo path) | 6213 | 9A9C693893FCBA0D |

The owner handoff named three files (`plan.md`, `evaluate.py`, `verify_baseline.py`). The worktree holds twelve, all untracked.

## Audit claims checked at takeover

- `results/baseline.json` records planner `geometry-fact-planner/15`, planner LF hash `9a67a48e…`, input LF hash `0e638742…` and oracle LF hash `572f3ff0…`. The checkout reproduces all three hashes.
- I re-ran the new test file once on the unchanged product (offline, `ALLOW_LIVE_AI=0`): **20 failed, 16 passed**.
  - All 10 positive cases are REFUSED with `UNSUPPORTED_CAPABILITY`. The reason is `sec: mặt qua M vuông góc AB — bản này chỉ chọn điểm neo trên khối chóp`.
  - All 10 volume controls (same facts, volume goal instead of the section) are SERVED.
  - Five negative cases fail the reason-code check because they are blocked at the same guard before their registered stage: missing-dimension, conflicting-length, wrong-source-line, boundary-face and vertex-touch. Three negatives pass with their registered code: constructed-line-endpoint, unmentioned-line-endpoint and plane-perpendicular-plane.
- The oracle (`tools/oracle.py`) imports nothing from the product, uses only `Fraction`, and clips the edges of hand-authored Euclidean coordinates. I hand-checked `right-base`: the plane is x = 3, the section is a 4 × 12 rectangle, and area² = 2304.
- I did not re-execute `verify_baseline.py`. Its output `verification/baseline-identity.json` is inherited.

## Root cause

`planner._mat_vuong_duong` contains the guard `if kh.loai != "pyramid": raise TuChoi("UNSUPPORTED_CAPABILITY", …)`, and that guard is the cause. The Source Gate (`registry._kiem_mat_vuong_duong`) and the Engine (`engine._kiem_mat_vuong_duong`, `_kiem_mat_phu` face check) contain no restriction to a solid kind. The gap is therefore classified **PLANNER_COMPOSITION_GAP** (anchor choice only). There is no gap in effect contracts, producers, typed prerequisites or budget.

## Smallest fix

Generalize the anchor choice structurally. Treat each solid as two layers: `[base, [apex]]` for a pyramid and `[base, top]` for a prism.

- If line d lies in one layer, take the first vertex of that layer that is off d, plus the first vertex of the other layer.
- Otherwise, take the first two base vertices that are off d.

For pyramids this rule yields exactly the old anchors, in the old order. The Planner computes no coordinates. The Engine still verifies Gram ⊥, plane independence, kernel-plane agreement and the boundary-face check. `PLANNER_VERSION` moves /15 → /16. Nothing else changes: no Source Gate, Engine, Registry, schema, IR or provider change.

## After the Planner fix (planner/16, uncommitted), 2026-10-27

The Planner guard is gone, and the cases now reach deeper layers. Everything below ran offline with 0 live calls.

- **2/10 positives SERVED**, both with exact oracle agreement: cuboid-base (area² 9216) and cube-diagonal (area² 432).
- **8/10 positives REFUSED** at the Source Gate with `SOURCE_OBJECT_MISMATCH`. These are the 8 triangular-prism cases, right and oblique. The registered section phrase reads "thiết diện của **lăng trụ đứng** ABC.A'B'C' với (P)" or "… của **lăng trụ** …". The closed grammar `registry._KHOI_NGU` (used by `_DAN_THIET_DIEN`) accepts the solid word only as "(hình|khối) lăng trụ …". Without "hình"/"khối", nothing binds the section to (P). This is a **SOURCE_GROUNDING_GAP** (grammar coverage). It is not a Planner gap. The cuboid and cube fixtures say "hình hộp chữ nhật" and "hình lập phương", so they pass.
- Negatives: no case is wrongly served. constructed-line-endpoint, unmentioned-line-endpoint, plane-perpendicular-plane and wrong-source-line match their registered codes. missing-dimension, conflicting-length, boundary-face and vertex-touch are refused, but with `SOURCE_OBJECT_MISMATCH`, which is not their registered code. They stop at the same grammar gap before reaching their intended stage.
- DIAGNOSTIC (post-hoc, not registered, scratch script outside the run): I inserted "hình" before "lăng trụ" in the section phrase only. With that change, **10/10 positives are SERVED with exact oracle agreement** and **8/8 negatives refuse with their registered code** (MISSING_DIMENSION, INCONSISTENT_FACTS, UNSUPPORTED_CAPABILITY ×2, SOURCE_OBJECT_MISMATCH, PLANE_NOT_UNIQUE, SECTION_PLANE_IS_FACE, PLANE_TOUCHES_VERTEX). So no gap remains in the Planner, Engine or Adapter for this slice.
- `tests/geometry` with the new file excluded: 9672 passed, 14 failed, 15 xfailed. The 14 failures are identity locks only. Four tests pin `geometry-fact-planner/15`. The other ten depend on `EVALUATION_CANDIDATE --verify`, which changes because planner.py is a measured path, and the candidate re-freeze clears them. The pyramid ⊥-section regression, the dependency cycle/dangling tests and every other planner/section test pass.

**Owner decision needed.** Closing the 8 cases requires one of these:

- (a) A Source Gate grammar change. This touches a layer this slice declared unchanged.
- (b) A newly registered corpus revision. That would be post-hoc, disclosed, with the original inputs immutable.
- (c) Accepting the 2/10 result plus the deeper refusal as the honest outcome of this slice.

## Owner decisions and later findings, 2026-10-27

1. The owner chose to **widen the grammar**. `registry._TU_KHOI` now accepts bare "chóp" / "lăng trụ" / "tứ diện" in `_KHOI_NGU` and `_khoi_cum`, mirroring `_MO_KHOI_DUNG`. Registry version /14 → /15. Result on the registered corpus as registered: **10/10 SERVED with exact oracle agreement and 8/8 refused with the registered code**.
2. **ADAPTER_INTEGRATION_GAP**, pre-existing and recorded as a separate gap by owner choice. The V2 route serves all 10 canonical payloads. The /4 wrapper `build_adapter4_response` refuses them fail-closed with `PREVIEW_RESULT_INVALID`. Every /4 section needs a `DINH_CAT_CANH` vertex certificate, and a plane-only derived section has none. A pristine export of 386d2149 shows the same refusal for the existing pyramid plane-only case (`test_v2_plane_only_section_area_without_derived_solid_is_served` asserts the route only). Codex's /4 test now pins the fail-closed behaviour.
3. **SOURCE_GROUNDING fail-open**, pre-existing and found by an adversarial check of item 1. When a section goal and an area goal share one derived plane, an area question that names a wrong or non-existent solid is SERVED. On the 386d2149 export the pyramid ⊥ fixture with a section+area pair serves "hình chóp T.XYZ" and "hình lăng trụ ABC.A'B'C'". Cause: the solid phrase inside the bound section reference (`_DAN_THIET_DIEN … (P)`) is never compared with the call's solid. `_khoi_trong_quote` accepts any symbol in any merged quote. Item 1 extends the same hole to bare wording ("lăng trụ" was refused on baseline only because the grammar failed to match). The registered corpus contains no case of this class. → Owner decision.

## Risks to preserve

- Registered negative expectations stay as written. If a code differs after the fix, it is reported as a mismatch, not re-registered.
- The pyramid decomposition must stay identical (regression test).
- `DEFAULT_MODE=LLM_ONLY`, no live calls, no merge or push, old worktrees untouched.
