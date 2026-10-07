# exact-dimensions — plan

Written before any product change of this run (2026-10-07). Run metadata: `run.json`. Labels: `labels.json`.
Independent oracle: `oracle.py`.

## 1. Starting point

- Branch `feat/regular-square-pyramid`, HEAD `4ceadd55`, working tree: only the user's `D frontend/public/favicon.svg`.
- `aa845902..4ceadd55`: one docs-only commit (living state). No product, harness or test change after the
  acceptance gate ⇒ the evidence of run `regular-triangular-pyramid-w01` stays valid; nothing is re-measured for it.
- Product `1e90ca0e` · candidate `92c9e198…` · `CACHE_VERSION` 116 · `LLM_ONLY` · human review NOT_APPROVED.

## 2. Where the limit is (B)

Points are `Vec3` over `Fraction` (ℚ³). An equilateral triangle with rational vertices has side² = 2N (N an
Eisenstein norm), never a rational square, so a rational edge has no Euclidean ℚ³ layout.

| limit | module / caller | current handling | needed change | check |
|---|---|---|---|---|
| layout must be Euclidean-faithful | `assumption_gate._khuon_chop_tam_giac_deu` (T8) ← `kiem_gia_dinh` on the route | `TEMPLATE_NOT_REPRESENTABLE T8` unless b² ∈ {2k², 6k²}, h² = 3t² | layout = affine chart; metric from the text | corpus P/N/U rows through `verify_and_compile` |
| metric = identity everywhere | `geometry/kernel.py` (projection, ⊥ plane), `measure.py` (distance, angle, area, volume), `predicates.py` (⊥), `section.the_tich_da_dien` | Euclidean `dot` | one active metric (default identity, byte-identical) | kernel tests in an oblique chart vs the identity chart |
| canonical cross-check frames | `_doi_chieu_chinh_tac`, T8 `chinh_tac` (N1/N3 only) | needs a rational Euclidean frame | canonical chart + its own derived metric | the same answers from two charts |
| renderer shows chart coordinates | `scene3d-view.tsx` root group (rotation only) | quaternion | chart → world linear map (Cholesky of G, then the display rotation) | browser cases, oracle with `model_matrix` |

## 3. Options (B)

1. **Wider exact coordinates** (ℚ(√3), ℚ(√2,√3)): changes `Vec3`, every kernel op, the payload's exact coordinate
   strings and the frontend parser; the tetrahedron needs a biquadratic field; segment lengths² leave ℚ and fall
   outside `radical.py` (`a·√b`). Largest change.
2. **One similarity factor λ**: lays out a rational similar copy and scales lengths by λ. Fails for an independent
   base/height pair (λ fixing b leaves h·√(3/2)-type factors) — the brief's warning; rejected.
3. **Affine chart + derived metric (chosen)**. The program's points stay rational and carry only affine meaning
   (incidence, ratios, intersections, centroids, sections — all invariant under invertible linear maps). Lengths
   come from a rational Gram matrix G: |v|² = vᵀGv. For four affinely independent chart points the six squared
   edge lengths fix G uniquely (a 6×6 linear system). The six values are DERIVED from the text by the regular
   pyramid relations already in T8: base b², lateral l² = b²/3 + h² (or read), tetrahedron a².

Proof sketch kept with the code (`geometry/metric.py`): G symmetric positive definite ⇒ G = TᵀT for an invertible T;
T maps the chart to a Euclidean figure with exactly the six text lengths, so it is the text's figure up to an
isometry; affine constructions commute with T; every metric quantity of the figure equals the G-quantity in the
chart. Exactness: G rational ⇒ |v|², areas² = det G·cᵀG⁻¹c/4, distances² to planes (s²/nᵀG⁻¹n), cos² stay in ℚ;
volume = |det|·√(det G)/6 is `a·√b`. Everything stays inside `radical.py`.

Scope: G ≠ identity only when (a) the text is a regular triangular pyramid / regular tetrahedron (single authority
`shape_constraint.la_chop_tam_giac_deu`), (b) the text fixes b² and h² (directly, from a lateral edge, or as a
tetrahedron), (c) the program declares the four vertices with literal chart coordinates, affinely independent, and
(d) the solved G is not the identity. Otherwise G = identity and every existing family is byte-identical. Curved
solids under a non-identity metric are refused (fail closed). Not done: a general metric for other families,
symbolic sizes, sums of radicals.

## 4. Operations (D)

| operation | in → out | condition | product caller | reuse |
|---|---|---|---|---|
| declare/construct point, segment, polygon, solid | names, chart coordinates → objects | — | interpreter | unchanged (affine) |
| midpoint, divide_segment, intersect line·line / line·plane / plane·plane, centroid by medians | points → point | — | `geometry_exec` | unchanged (affine) |
| project point → plane / line, plane ⊥ line | point, plane → foot | metric | `geometry_exec`, `quantity_annotations` | metric-aware |
| distance (point·point, point·plane, point·line, lines, planes) | → length² | metric | `measure`, `geometry_exec` | metric-aware |
| angle cos²/cos | → ℚ / `a·√b` | metric | `measure` | metric-aware |
| area polygon | vertices → `a·√b` | metric | `measure.area_polygon` | metric-aware |
| volume polyhedron | solid → `a·√b` | metric | `geometry_exec.volume_polyhedron` | × √det G |
| ⊥ predicates | → bool | metric | `predicates`, postconditions, checkers | metric-aware |
| metric from six lengths | chart vertices + lengths² → G | affinely independent, G positive definite | new `geometry/metric.py`, called once per program | new, shared |

## 5. Domain to reach (C) and corpus

Regular triangular pyramid with rational (incl. fractional, decimal) base and height; base + lateral edge;
regular tetrahedron with rational edge; the previous `k√2`/`k√6` radical cases. Any program chart (axis chart, an
approximate Euclidean chart, the old tilted frames). Expectations in `labels.json` before the change.

## 6. Other parts of this run

- E: screenshots decided at the runner (capture only what an assertion, the review set or a failure needs).
- F: one naming convention (`docs/evaluation/RUN_NAMING.md`), active files renamed in a separate commit.
- G: browser checks for the new sizes on desktop / low / mobile; one full gate on a clean checkout at the end.
