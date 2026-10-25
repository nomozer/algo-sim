# Sphere sample — source authority fix

Authorization `GO_LOCAL_F2_POLICY_REVIEW_B3_VERIFICATION_SPHERE_SOURCE_FIX`, 2026-10-25. Branch
`research/sphere-sample-source-authority` (from the visual closure `de49c592`, independent of B3), integrated in
`integration/visual-b3-sphere-candidate`.

## Problem source → sample builder → formation roles → envelope → frontend

| Layer | Before | Defect |
|---|---|---|
| Problem | "Cho mặt cầu tâm I bán kính 5. Mặt phẳng (P) cách tâm I một khoảng bằng 3 …" | Names I, (S), (P); gives 5 and 3. |
| Sample builder (`build_geometry_samples.chuong_trinh_cau_cat_mp`) | free points I, A(5,0,0), H(0,0,3), U(1,0,3), W(0,1,3); sphere through rim A; plane through H, U, W | A, H, U, W are not in the problem; they existed only because the IR then needed a rim point and three plane points. |
| Scene builder (`scene3d._nhom`) | `display_group: given` ⇔ `origin == "free"` | Every free point became "given". The learner saw four invented data points. |
| Formation (`formation._vai_cua`) | cutting planes recognised only as sources of a `section` object | The plane cutting a curved solid fell back to `CONSTRUCT_AUXILIARY_GEOMETRY`. |
| Frontend (`scene3d-auxiliary`) | auxiliary planes hidden once their constructed child exists | (P) disappeared as soon as the circle was drawn. |

The frontend's role reading was correct; the authority errors were in the sample program and in formation. No frontend
rule was changed, so a point that a problem really gives is never hidden by name.

## Fix

1. **Sample program.** Only source data are declared:
   - `I` (point, `MODEL_ASSUMPTION` "chọn tâm I làm gốc toạ độ");
   - `R = 5` (`GIVEN`, `source_fact_id: f_ban_kinh`), with the sphere built by the IR's `radius` form (since 2026-09-04);
   - `(P)` by `construct_plane_from_equation` z = d (position = layout; the distance d is the source's).

   The builder's `RequestContract` now carries `input_facts` (`DU_KIEN`), so the existing `_nhan_du_kien_tu_fact` labels
   R "Bán kính mặt cầu" instead of "Đại lượng đo". The cylinder sample `tru-thiet-dien-tron` had the same invented rim
   point and is fixed the same way (`R = 2`, "Bán kính đáy").
2. **Formation.** A plane that is a source of an `intersect_plane_curved*` result is `CONSTRUCT_CUTTING_OBJECT`, as for
   polyhedral sections (one `elif` in `formation._vai_cua`'s collector). It affects served LLM_ONLY envelopes with
   curved sections.

## Object classification after the fix (`cau-cat-mat-phang`)

| Object | Class | Evidence |
|---|---|---|
| I | source-given (named), position = layout assumption | `origin free`, `display_group given`, `MODEL_ASSUMPTION` |
| R = 5 | source-given | `GIVEN`, InputFact `f_ban_kinh`, label "Bán kính mặt cầu" |
| (S) | constructed from source data | `construct_curved_solid.ball` from I + R |
| (P) | source-named plane, placed by layout | `construct_plane_from_equation`, `CONSTRUCT_CUTTING_OBJECT`, label (P) |
| C | derived with witness | `intersect_plane_curved`, radius² = 16 = R² − d² (exact kernel) |
| r = 4, S = 16π | derived, asked | measures of C |
| A, H, U, W | **removed** | were unjustified |

## Circle / tangent / no intersection — no clamp

The exact kernel already distinguishes the three cases (`curved.py`). Through the sample program with d = 3, 5, 6:

| d | Result |
|---|---|
| 3 (d < R) | completed, circle r² = 16 |
| 5 (d = R) | `GeometryError CURVED_PLANE_TANGENT` ("giao là một ĐIỂM … dựng bằng project_onto") |
| 6 (d > R) | `GeometryError CURVED_PLANE_DOES_NOT_CUT` |

No circle is drawn in the last two cases. The Owner HTML clamps `sqrt(max(0.1, R² − d²))`; it was not copied. The
canonical V2 curved-solid bridge stays disabled (`BRIDGE_UNSUPPORTED_CURVED`).

## CACHE_VERSION 128 → 129 (contract change that forced the decision)

The formation change alters served default-route envelopes. A cache probe (`sphere-sample-source-authority/cache/cache_probe.py`) through the real `/api/analyze` on the clean
v128 tree `de49c592` and on the new tree found:

- `p6_thiet_dien_elip_cua_hinh_tru` (replayed recorded case) differs **only** in the cutting plane's `formation_roles`
  (2 entries);
- 3 controls (pyramid, right prism, cube) are byte-identical;
- the refusal control is never cached.

Without the bump, the genuine v128 row would keep being served with the plane hidden. The precedent wording "vẫn HIT"
(127, 128) means "would hit without the bump". After the bump the migration test proves it misses, and that
re-analysis changes nothing but that role (`backend/tests/test_cache_curved_cutting_plane_invalidation.py`).

All sync points moved in one commit: constant + note, `test_api` assert with reason, the `CURRENT_STATE` identity table,
and seven other version pins. The cache identity lock was re-written (`98d52e90`). The environment components (prompts,
grammar card, synthesis/analyze schema, capability table) are unchanged, so the **model surface is unchanged**.

The first Full T3 of this branch **failed** at `301692c8` (10 tests). I had not re-run `lock_cache_identity.py` after
the bump. Receipt kept: `verification/full-t3/sphere-301692c8-FAIL/receipt.json`. After the relock: **PASS at `98d52e90`**
(pytest 11877, vitest 1357).

## Independent oracle

`step-math-validation/oracle.py` is hash-locked and cannot read scalar-radius solids. It was **not edited**. The new
layer `oracle_scalar_radius.py` checks `radius_sq == R²` against the given quantity the solid depends on. It then
hands the locked oracle a copy with a rim point built from that R (Euclidean charts only), so the circle check
r² = R² − d² runs unchanged. Faults rejected: wrong radius_sq, wrong R, missing R dependency, non-Euclidean chart,
corrupted circle; plus a wrong cylinder radius. Review M-8: it checks consistency with the scene's own R; fidelity to
"bán kính 5" is locked by `test_given_radius_is_the_source_number`.

## Browser (integrated candidate)

Captured on the final integrated candidate `63faa5af` (`verification/sphere-capture/receipt.json`, 0 page errors), 1440 and 390 px, final step:

| Sample | Canvas labels | Learner text matching `đại lượng` / `đi qua` / `Điểm A/H/U/W` | (P) at final step |
|---|---|---|---|
| `cau-cat-mat-phang` | I | none | visible, labelled (P) |
| `tru-thiet-dien-tron` | O, O′, M | none | visible |

The first integrated capture (`c57c7c05`) still showed "Hình trụ đáy tâm O, tâm đáy trên O′, **qua đại lượng**" in the cylinder's step text. The radius-declared solid name was fixed in `display_names` (`9ced3d27`) and covered by the pending 129 bump (`visual-b3-sphere-integration/cache/decision-addendum.json`). RED/GREEN: `test_scalar_radius_solid_is_never_named_through_a_quantity`. The F2 probe's circle case now runs on this corrected sample (6/6, 30/30). The official suite's static fixtures do not include these samples.

Learner-facing defaults: clean shell, (P) visible and named, intersection circle prominent, centre I; no meridian or equator loops (removed in `53fe3d25`).

## Not done / open

- A tangent problem would need a typed tangent-point construction (`project_onto`) to be served. Today it is refused
  with `CURVED_PLANE_TANGENT`.
