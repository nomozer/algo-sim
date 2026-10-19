# Geometry capability expansion — interface contract (route D, Hybrid Wave 2B)

Run `geometry-capability-expansion`. Route D only (typed facts → planner → Registry → exact engine); not wired to
`/api/analyze`. Every construction is exact in ℚ³ under the chart Gram metric; every new object is re-checked on the
built figure; unknown wording or an underdetermined figure is refused with a code, never approximated.

## A. Ratio point on a segment — `divide_segment`

| Item | Contract |
|---|---|
| Input fact | `point_def` with `point_kind = "divide_segment"`, `point` P, `points` = ORDERED [A, B], `value` = t |
| Typed operands | P: new point label · [A, B]: two distinct labels · t: rational "p/q" |
| Preconditions | 0 < t < 1 (`INVALID_RATIO`), A ≠ B (`FACT_INCOMPLETE`), A, B placed |
| Effect | point P = (1 − t)A + tB; the single convention **t = AP/AB** |
| Registry | `divide_segment(point, segment, ratio)`, kind `construct`, `provider_offered = False` (route B only); listed in `POINT_PRODUCERS` |
| Algorithm | engine `_mot_buoc`: place P once A, B are placed (exact Fractions) |
| Source grounding | `_ty_so_dung_nguon`: closed "P (là điểm) thuộc/nằm trên (cạnh/đoạn) XY sao cho ‹seg› = k·‹seg›"; the gate SOLVES t from the stated equation (XP = t, PY = 1 − t, XY = 1 in units of XY) and binds ([X, Y], t) or ([Y, X], 1 − t) — "SM = 2MA" ⇒ t = 2/3 from S, never confused with SM/SA |
| Invariant | `_dung_khong`: P == (1 − t)A + tB exactly |
| IR | `construct_point` with the existing `divide_segment` expression (`a`, `b`, `ratio`) |
| Scene3D | an ordinary derived `point3`, placed after A and B (Wave 1 dependency order) |
| Refusals | ratio not stated / different from the fact ⇒ `SOURCE_OBJECT_MISMATCH`; t ∉ (0, 1) ⇒ `INVALID_RATIO`; no value ⇒ `FACT_INCOMPLETE` |
| Compatibility | `TypedFact.point_kind` gains one literal ⇒ the route D extraction surface changes (declared identity delta); route A declarations unchanged |

## B. Plane through a point ⊥ a line, and its section — rule `MAT_VUONG_DUONG`

| Item | Contract |
|---|---|
| Input fact | `section` / area `question` with `plane_relation = "perpendicular"`, `point` M, `points_b` = the line d (exactly 2 labels) |
| Typed operands | M: source point · d: two vertices of the solid · the solid (pyramid) |
| Preconditions | `points_b` of ≥ 3 labels is a PLANE ⇒ `PLANE_NOT_UNIQUE` (unchanged); d joins two solid vertices; pyramid only (`UNSUPPORTED_CAPABILITY` otherwise) |
| Effect | the unique plane through M with normal along d; its section of the solid |
| Registry | no new function: decomposition into existing `orthogonal_projection_line` + `translate_point` + `section` / `ask_section_area`; `AUXILIARY_RULES[MAT_VUONG_DUONG]` |
| Algorithm | anchors Z₁, Z₂ from the pyramid's structure (d through apex ⇒ two base vertices off d; else a base vertex off d and the apex); Fᵢ = foot of Zᵢ on d; Xᵢ = M + Fᵢ→Zᵢ; section plane (M, X₁, X₂) |
| Source grounding | `_QUA_VUONG_DUONG`: "(P) đi qua M (và) vuông góc với d" as a premise; section / area bound to (P) by the shared derived-plane binder (`mat_song_song_dung_nguon(…, duong=d)`) |
| Invariant | engine `_kiem_mat_vuong_duong`: ⟨Xᵢ − M, d⟩_G = 0, X₁ − M, X₂ − M independent, same plane as the kernel's `plane_through_point_perpendicular_to(M, d)` (the operation of `PlanePerpendicularToLineExpr`) |
| IR | `project_onto`, `vector_from_points`, `translate`, `construct_plane`, `construct_section` — all existing |
| Scene3D | `section` object of the solid; auxiliary points DERIVED |
| Refusals | wrong line vs source ⇒ `SOURCE_OBJECT_MISMATCH`; plane meeting the solid at a vertex only ⇒ `PLANE_TOUCHES_VERTEX` / `PLANE_DOES_NOT_CUT` |
| Compatibility | the parallel-plane binder is parametrised, not copied; ⊥-plane-to-plane stays refused |

## C. Right-trapezoid base — `right_angle_chain_chart`

| Item | Contract |
|---|---|
| Input facts | quadrilateral base; `right_angle` at two CONSECUTIVE vertices Vi, Vj, each between the polygon's own sides; lengths ViVj, ViVp, VjVn |
| Preconditions | the two right angles exist as stated (source-bound "hình thang vuông tại A và B"); all three lengths (`MISSING_DIMENSION`); VjVn : ViVp rational (`UNSUPPORTED_IRRATIONAL_LAYOUT`) |
| Effect | base chart Vi(0,0), Vj(1,0), Vp(0,1), Vn(1, r), G₂ = diag(ViVj², ViVp²) |
| Registry | none new (existing `right_angle`, `segment_length`) |
| Algorithm | engine `bo_cuc_day` → `_chuoi_goc_vuong` (after regular / rectangle / triangle) |
| Source grounding | existing right-angle binding (wrong vertices ⇒ `SOURCE_OBJECT_MISMATCH`) |
| Invariant | both legs ⊥ ViVj (hence parallel), same side (a simple polygon); a fourth side, if given, re-checked like every fact |
| IR / Scene3D | `declare_point` LAYOUT_DERIVED base vertices; ordinary pyramid formation |
| Refusals | one right angle / non-consecutive ⇒ `UNSUPPORTED_BASE_SHAPE` or `SOURCE_OBJECT_MISMATCH`; missing length ⇒ `MISSING_DIMENSION` |
| Compatibility | reached only when no regular / rectangle / triangle rule applies — earlier bases unchanged |

## D. Oblique prism — `prism_lateral_vector`

| Item | Contract |
|---|---|
| Input facts | `prism` (right = false), base placed, ONE top vertex fixed by the facts (e.g. projection of A' onto the base + AA') |
| Preconditions | base placed; at least one top vertex placed (else `UNDERDETERMINED_POINT`); lateral vector off the base (`INCONSISTENT_FACTS`) |
| Effect | every other top vertex = its base vertex + the same lateral vector |
| Algorithm | engine `_mot_buoc`, after the right-prism rule; one vertex per step (topological trace) |
| Invariant | `_dung_khong(prism)`: one vector for all pairs, z ≠ 0; right prisms additionally ⊥ base |
| Chart | the apex side of the base is the chart's z > 0 — a representation choice; volume, distances and angles are invariant under the reflection |
| Certificates | Wave 1 `perpendicular_witness` only where the exact certificate holds — never on oblique lateral edges |
| Compatibility | right prisms keep `right_prism_translate` |
