# Preregistration amendment 1 — residual-volume ancestry (F7)

Registered on product `959e23a6`, before the fix, while assembling Gate A. The previous reviewer's 117 committed probes
(`../unified-solid-scope/review/probes.py`) were re-run on `959e23a6` (`closure-review1-probes.out`): every NEG is
refused and no route raises an internal error, except the cases below, all identical on main and on the previous
candidate (pre-existing):

| probe | result | adjudication |
|---|---|---|
| `SEC1.residual_parent_other`: `residual_volume(parent=t_abcd, cut=s_top)` where `s_top` is cut from `s_abcd` | A3 **SERVED** | **F7 MAJOR, same class (derived-solid ancestry)**: the declared cut solid is not derived from the declared parent. Registered here, fixed next. |
| `SEC1.ratio_den_other_solid`: `volume_ratio(s_top, t_abcd)` | A3 SERVED | valid: a ratio of two declared solids has no ancestry contract |
| `C1.premise_unscoped_cross_namespace`: unscoped segment `s1::A`–`s2::T` | SERVED ×3 | valid: `A` is the same point in both pyramids (identity bindings), the premise is consistent |
| `C1.premises_all_unscoped_shared_labels` | `AMBIGUOUS_REFERENCE` ×3 | intended fail-closed (Owner GO mandatory control) |
| SEC1 controls, `C1.dist_segment_scope_s1_control`, `C1.angle_plane1_plane2_scope_s1_control` on Adapter /4 | `SOURCE_OBJECT_MISMATCH` | Source Gate (quote) refusal, same text on main — not a scope verdict; Adapter /3 serves or refuses with its own capability code |

Rule extension: S3 for `residual_volume` — when `cut_solid_id` is a declared derived solid, its parent must be
`parent_solid_id` (`SOURCE_OBJECT_MISMATCH`). A primary cut solid keeps the existing geometric containment checks.
Inventory: `schema-field-inventory-v2.json` (v1 kept) lists S3 on `MathGoalSpec.parent_solid_id`/`cut_solid_id` with the
negative test `test_residual_cut_must_descend_from_parent`; RED expected on `959e23a6`.
