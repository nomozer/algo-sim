# Multi-Object FactGraph & Typed Geometric Relation Audit (`typed-fact-next/2`)

- **Epic**: `ALGOSIM_MASTER_HYBRID_BACKEND_REPLACEMENT` (Continuation 9 — Multi-Object FactGraph + Composite Geometry + Generalized Geometric Relations)
- **Baseline checkpoint audited**: `7da83164b4d3e08ee9f7eec0fe028537903a8fa6`
- **Target contract**: `typed-fact-next/2` (Route D `/4` only; `/1` and Adapter `/3` preserved unchanged)

---

## 1. Executive Summary & Architectural Map

At checkpoint `7da83164`, Route D `/4` supported either:
1. Pure polyhedral multi-solid graphs (`shared_faces`, `shared_vertices`, `perpendicular`, `coordinate_frame="root"`, plus derived sections and derived pyramids on sections), **or**
2. Pure single-curved-solid graphs (cylinder, cone, standalone sphere, plus axial/parallel sections and derived apex sub-cones), **or**
3. Narrow 2-solid `(1 polyhedron + 1 circumscribed sphere)` composites via `SolidSpec.circumscribes` with `relations=[]` and `derived_sections=[]`.

### End-to-End Multi-Object Architecture Map (Route D `/4`)

```text
Vietnamese Problem Text
  │
  ▼
TypedFactNextPayloadV2 (typed_fact_next.py)
  ├─ solids: tuple[SolidSpec, ...]            ← OBJECT_IDENTITY + host coordinate_frame
  ├─ relations: tuple[GeometricRelationSpecV2]← GEOMETRIC_RELATION (directional, typed)
  ├─ premises / derived_sections              ← Intra-object & derived-object premises
  ├─ simulation_goals / math_goals            ← Multi-object & multi-goal queries
  │  (every record carries immutable quote    ← SOURCE_REFERENCE)
  ▼
Scope & Ownership Validator (_validate_declared_solid_scope)
  ├─ Disjoint solid_id / notation / vertex ownership across unlinked solids
  ├─ Shared vertex/face ownership via explicit GeometricRelationSpecV2
  ├─ Directional relation role validation (sphere → host solid / plane)
  ▼
Bridge Normalizer (typed_fact_next_bridge.py)
  ├─ Admits arbitrary polyhedral FactGraphs + ≥1 relation-anchored spheres
  ├─ Admits 1 axial host solid (cylinder/cone) + ≥1 relation-anchored spheres
  ├─ Rejects unanchored multi-curved charts (BRIDGE_UNSUPPORTED_CURVED_COMPOSITE)
  ▼
Closed Vietnamese Source Gate (registry.py /26)
  ├─ Verifies premise role (rejects GOAL / CONDITIONAL / QUESTION / NEGATED clauses)
  ├─ Binds closed clauses for circumscribes, inscribed_in, sphere_tangent_plane
  ├─ Disambiguates multi-solid / multi-sphere asks ((S1) vs (S2), ngoại tiếp vs nội tiếp)
  ▼
Generalized Dependency Planner (planner.py /22)
  ├─ Typed goal decomposition + shared intermediate reuse
  ├─ Explicit producer → consumer DAG (_sap_xep_phu_thuoc_loi_goi) + cycle detection
  ├─ Honest composition classification per plan
  ▼
Exact Geometry Kernel & Certifier (engine.py /18)
  ├─ Exact chart placement + rational Cholesky Euclidean normalization (Point3 = Fraction³)
  ├─ Exact Fraction circumsphere solver (all vertices) + G4 IR construction
  ├─ Exact Fraction insphere solver (all boundary faces, inward normals, interior contacts)
  ├─ Exact sphere–plane tangency verifier (d² = R² vs secant d² < R² vs disjoint d² > R²)
  ├─ 4-Layer Relation Certificates + Pedagogical Construction Trace + Scene3D
```

---

## 2. Sixteen-Dimension Audit of `typed-fact-next/2` (§3.1)

| # | FactGraph Dimension | Baseline (`7da83164`) | Gap Identified | Continuation 9 Target State |
|---|---|---|---|---|
| 1 | **Solid identity** | Unique `solid_id` + `notation` on `SolidSpec`; `CIRCUMSCRIBED_NAME_PATTERN` for `(S)` / `(S.ABCD)`. | `CIRCUMSCRIBED_NAME_PATTERN` only unlocked when `circumscribes` was set; `inscribed_in` and relation-anchored spheres lacked it. | Unlocked for any sphere anchored by `circumscribes` or `inscribed_in` (field or `GeometricRelationSpecV2`); duplicate `solid_id` or `notation` refused fail-closed. |
| 2 | **Point ownership** | `_validate_declared_solid_scope` (`# S1`–`# S9`) maps vertices and derived points (`midpoint`, `centroid`, `divide_segment`, projections, intersections) to owning solids. | Curved contact points (`contact_ref` on `tangent_to`) and named incenters were not tracked in scope ownership. | `SolidSpec.center_or_apex` for `inscribed_in` and `GeometricRelationSpecV2.contact_ref` registered in scope ownership and point-label validation. |
| 3 | **Line ownership** | Segment/line premises (`segment_length`, `perpendicular_lines`, `altitude`) checked against owning `solid_id` vertex closures. | Preserved; axial segments (`SO`, `OO'`) owned by host cylinder/cone. | Preserved and verified across composite polyhedron + sphere runs. |
| 4 | **Plane ownership** | Faces, base planes, diagonal planes (`_mat_coplanar_khoi`), and derived planes (`(P)`, `(α)`) bound to owning `solid_id`. | Tangency target plane (`entity_b` in `tangent_to`) had no relation-level validation. | `tangent_to` validates `entity_b` (`≥ 3` distinct vertices in declared solid scope) and verifies coplanarity in the kernel. |
| 5 | **Shared vertices** | `GeometricRelationSpec(kind="shared_vertices")` merges allowed vertex pools cleanly. | Blocked by bridge whenever any curved solid existed in `p.solids`. | Bridge permits `shared_vertices` / `shared_faces` polyhedral graphs together with relation-anchored spheres. |
| 6 | **Shared edges** | Represented via 2-point `shared_vertices` or boundary of `shared_faces`; standalone `shares_edge_with` not a separate `/1` kind. | Evaluated in §4: 2-vertex sharing already lossless via `shared_vertices` (`entity_a`/`entity_b` of length ≥ 1) without duplicating `/1` kinds. | Documented and verified; `/1` `GeometricRelationSpec` kept 100% frozen. |
| 7 | **Shared faces** | `GeometricRelationSpec(kind="shared_faces")` + `coordinate_frame="root"` places second pyramid/prism on shared face in exact chart. | Bridge rejected `curved and p.relations`, blocking multi-polyhedron + sphere composites. | Bridge routes multi-polyhedron `shared_faces` + anchored sphere(s) end-to-end on Route D `/4`. |
| 8 | **Derived points** | `POINT_PRODUCERS` (`midpoint`, `centroid`, `divide_segment`, `intersect_line_line`, `intersect_line_plane`) + `orthogonal_projection*`, circumcenter `I`. | Incenter `I` and sphere–plane tangency contact point `T` lacked exact producer/placement paths. | Exact `Fraction` incenter `I` (via 3 inward bisector planes in IR) and tangency foot `T` (`project_onto` in IR) added with conflict checks against pre-declared points. |
| 9 | **Derived solids** | Derived pyramid on plane section (`DINH_CAT_CANH`) and derived apex cone (`curved_subsolid`). | Bridge blocked `curved and p.derived_sections`, preventing polyhedron section / derived pyramid from coexisting with a sphere. | Bridge unlocks polyhedron `derived_sections` + derived solids coexisting with anchored spheres. |
| 10 | **Parent / child objects** | Section (`DerivedSectionSpec.solid_id`) and sub-cone (`curved_subsolid.solid`) reference parent `solid_id`. | Anchored spheres were limited to 1 sphere on 1 polyhedron. | Multiple child/companion spheres (`(S1)` circumscribed, `(S2)` inscribed) can anchor to the same parent polyhedron or axial host solid. |
| 11 | **Coordinate chart ownership** | Engine builds affine chart `(pts, G)` from root polyhedron, then `chuan_hoa_euclid()` maps `(Q³, G) → (Q³, I)` via rational Cholesky. | Axial host solids (`cylinder`/`cone`) in `_dung_cong` had canonical pose `(0,0,0) → (0,0,h)` only for 1 curved solid. | Root polyhedron chart owns all anchored spheres; canonical axial pose owns host cylinder/cone + its anchored spheres. |
| 12 | **Multiple reference frames** | Polyhedra require `coordinate_frame="root"` when `len(poly_solids) > 1`; unrelated frames refused (`UNSUPPORTED_COORDINATE_FRAME`). | Two unanchored curved solids refused `BRIDGE_UNSUPPORTED_CURVED_COMPOSITE`. | Preserved strictly: every object in a served composite must embed into ONE shared exact Euclidean chart; unanchored multi-curved solids remain refused. |
| 13 | **Cross-solid relations** | `/1` had 7 polyhedral relation kinds; Continuation 8 added `SolidSpec.circumscribes` field only. | No explicit `GeometricRelationSpecV2` for `circumscribes`, `inscribed_in`, `tangent_to`; no inscribed sphere; no tangency check. | `GeometricRelationSpecV2` + `SolidSpec.inscribed_in` implemented with full directional & agreement checks. |
| 14 | **Source provenance** | Every `SolidSpec`, `PremiseSpec`, `GeometricRelationSpec`, `DerivedSectionSpec`, and goal carries mandatory `quote` checked by `kiem_nguon`. | Multi-sphere quotes and tangency quotes had no closed Vietnamese grammar. | Closed Vietnamese grammars added for `inscribed_in`, axial `circumscribes`/`inscribed_in`, `sphere_tangent_plane`, and multi-curved ask disambiguation. |
| 15 | **Construction provenance** | Engine emits `construction_trace` (`preconditions`, `postconditions`). | Composite relation steps lacked explicit `dependencies`, source vs derived provenance tags, and 4-layer relation certificates. | Every relation-driven step carries explicit `dependencies`, `provenance_kind` (`source_premise` / `derived_relation`), `preconditions`, `postconditions`, and links to 4-layer `relation_certificates`. |
| 16 | **Multiple requested goals & ambiguous references** | `math_goals` supports multiple goals (`mg1`, `mg2`, ...) on polyhedron + 1 sphere. | `_cong_khop` hardcoded `len(cong) == 1`, rejecting all 2-sphere runs (`(S1)` + `(S2)`), and could not disambiguate `"ngoại tiếp"` vs `"nội tiếp"`. | `_cong_khop` generalizes to `N` curved solids: serves iff the ask phrase uniquely identifies 1 curved solid by notation `(S1)`, center `I`, kind, or relation (`ngoại tiếp` vs `nội tiếp`), refusing bare `"khối cầu"` when `≥ 2` spheres exist. |

---

## 3. Strict Five-Concept Separation (§3.2)

To prevent ontology conflation across schema, planner, Source Gate, and certificates, Route D `/4` enforces five orthogonal representations:

1. **`OBJECT_IDENTITY`** (`SolidSpec.solid_id`, `SolidSpec.notation`, `LoiGoi.args.solid`, IR `VarName`):
   - Identifies *what object* exists (`"poly"`, `"sph_out"`, `"sph_in"`, `"S.ABCD"`, `"(S1)"`, `"(S2)"`). Never encodes how it is constructed or how it relates to other objects.
2. **`GEOMETRIC_RELATION`** (`GeometricRelationSpecV2`, normalized onto typed relation facts / `CurvedSolidArgs.circumscribes` / `inscribed_in` / `sphere_tangent_plane`):
   - States a *mathematical predicate between two geometric entities* with explicit directionality (`(S2) INSCRIBED_IN S.ABCD` vs `(S1) CIRCUMSCRIBES S.ABCD` vs `(S2) TANGENT_TO (ABCD) at H`).
3. **`CONSTRUCTION_DEPENDENCY`** (`LoiGoi.depends_on`, planner `_sap_xep_phu_thuoc_loi_goi`, trace `dependencies`):
   - States the *DAG execution order* (`c_sph` depends on `c_poly` and optional pre-declared center producer; `c_tan` depends on `c_sph` and plane vertex producers; `c_ask` depends on `c_sph`). Validated acyclic (`DEPENDENCY_CYCLE` otherwise).
4. **`SOURCE_REFERENCE`** (`quote` / `quotes` on schema specs and `LoiGoi`, verified by `kiem_nguon`):
   - Locates the *exact verbatim Vietnamese text span* licensing the object, relation, or goal, checked for clause role (`PREMISE` vs `QUESTION` vs `GOAL` vs `CONDITIONAL`) and negation.
5. **`DERIVATION_PROVENANCE`** (`KetQuaTuyen.construction_trace` + `KetQuaTuyen.relation_certificates`):
   - Records *how the engine derived and certified* coordinates, auxiliary planes/projections, contact points, and exact measures across four separated proof layers (`SOURCE_GROUNDING_PROOF`, `GEOMETRIC_RELATION_PROOF`, `KERNEL_EXECUTION_PROOF`, `RESULT_CERTIFICATE`).

---

## 4. Twelve-Relation Evaluation & Canonical Contract (§4)

 Note on schema compatibility: `/1` `GeometricRelationSpec` (`KIND_ALLOWED_FIELDS["relation"]`) is locked by `test_scope_census_closure.py` for `/1` freeze parity and remains **100% untouched**. On `typed-fact-next/2`, `TypedFactNextPayloadV2.relations` uses `GeometricRelationSpecV2`, which extends `/1`'s 7 relation kinds with `"circumscribes"`, `"inscribed_in"`, and `"tangent_to"` plus optional `contact_ref`.

| Candidate Relation | Status in `/2` | Canonical Subject (`solid_a` / `entity_a`) | Canonical Target (`solid_b` / `entity_b`) | Directionality & Semantics | Verification & Refusal Contract |
|---|---|---|---|---|---|
| 1. `CIRCUMSCRIBES` | **SERVED** (`SolidSpec.circumscribes` & `GeometricRelationSpecV2(kind="circumscribes")`) | `solid_a`: axisless `sphere` | `solid_b`: convex polyhedron (`pyramid`/`prism`) or right `cylinder`/`cone` (`solid_a != solid_b`) | Asymmetric: `Sphere CIRCUMSCRIBES Solid`. Reversed (`Polyhedron CIRCUMSCRIBES Sphere`) → `SOURCE_OBJECT_MISMATCH`. | Polyhedron: all vertices satisfy $\|V - I\|^2 = R^2$ (`NO_CIRCUMSCRIBED_SPHERE`, `METRIC_REQUIRES_EUCLIDEAN_CHART`, `INCONSISTENT_FACTS`). Cylinder/Cone: exact rim circles & apex equidistant (`EXACT_DOMAIN_EXCEEDED` if irrational height). |
| 2. `INSCRIBED_IN` | **SERVED** (`SolidSpec.inscribed_in` & `GeometricRelationSpecV2(kind="inscribed_in")`) | `solid_a`: axisless `sphere` | `solid_b`: convex polyhedron (`pyramid`/`prism`) or right `cylinder`/`cone` (`solid_a != solid_b`) | Asymmetric: `Sphere INSCRIBED_IN Solid` (never conflated with `CIRCUMSCRIBES`). Reversed (`Polyhedron INSCRIBED_IN Sphere`) → `SOURCE_OBJECT_MISMATCH`. | Polyhedron: all boundary faces coplanar & convex, inward $d_G(I, F_k) = r > 0$, every foot $T_k \in \text{relint}(F_k)$, $9V^2 = \rho^2(\sum \tilde{S}_k)^2$ (`NO_INSCRIBED_SPHERE`, `EXACT_DOMAIN_EXCEEDED`, `METRIC_REQUIRES_EUCLIDEAN_CHART`, `INCONSISTENT_FACTS`). Cylinder: $h = 2r$ (`NO_INSCRIBED_SPHERE` otherwise). Cone: $r_{\text{in}} = rh/(r+l) \in \mathbb{Q}$ (`EXACT_DOMAIN_EXCEEDED` if $l \notin \mathbb{Q}$). |
| 3. `TANGENT_TO` | **SERVED** (`GeometricRelationSpecV2(kind="tangent_to")`) | `solid_a`: declared `sphere` | `entity_b`: plane (`≥ 3` vertices, optionally scoped to `solid_b`); optional `contact_ref` | Sphere tangent to plane at unique orthogonal foot $T$: exact $d(I, P)^2 = R^2$. Distinct from all-face `inscribed_in` and vertex `circumscribes`. | $d^2 < R^2 \to$ `PLANE_INTERSECTS_SPHERE_NOT_TANGENT`; $d^2 > R^2 \to$ `PLANE_DOES_NOT_TOUCH_SPHERE`; named $T \ne \text{foot}(I, P) \to$ `INCONSISTENT_FACTS`. |
| 4. `SHARES_VERTEX_WITH` | **SERVED** (`kind="shared_vertices"`) | `solid_a` + `entity_a` (`≥ 1` vertex labels) | `solid_b` + `entity_b` (matching vertex labels) | Symmetric vertex identification across polyhedra in shared root frame. | Validated in `_validate_declared_solid_scope` + bridge `_kiem_pham_vi_tien_de`; coexists with spheres in `/2`. |
| 5. `SHARES_EDGE_WITH` | **REPRESENTED VIA `shared_vertices` / `shared_faces`** | Polyhedron `solid_a` | Polyhedron `solid_b` | 2 shared adjacent vertices in `shared_vertices` or boundary of `shared_faces` in `coordinate_frame="root"`. | Standalone hinge-angle DOF without root-frame placement refuses `UNSUPPORTED_COORDINATE_FRAME` / `UNDERDETERMINED` fail-closed. |
| 6. `SHARES_FACE_WITH` | **SERVED** (`kind="shared_faces"`) | `solid_a` + `entity_a` (`≥ 3` face vertices) | `solid_b` + `entity_b` (matching face vertices) | Identifies a full face of `solid_a` and `solid_b` (`_kiem_mat_chung` + root chart placement). | Non-face vertex set → `INCONSISTENT_FACTS`; now composes with spheres and multi-solid volume/ratio/residual goals. |
| 7. `INTERSECTS` | **SERVED VIA TYPED CONSTRUCTIONS / REFUSED AS GENERIC TAG** | Line/Plane/Solid | Line/Plane/Solid | Route D models intersections by exact output kind (`intersect_line_line`, `intersect_line_plane`, `intersection_line`, `DerivedSectionSpec`, `curved_section`), never an untyped `INTERSECTS` tag. | Secant plane claimed as `tangent_to` refuses `PLANE_INTERSECTS_SPHERE_NOT_TANGENT`; generic untyped `relations.kind="intersects"` refuses `INVALID_RELATION_SPEC`. |
| 8. `CONTAINS` | **SERVED FOR POINT/LINE-IN-PLANE PREMISES; GENERIC SOLID CONTAINMENT REFUSED** | Point/Line | Segment/Plane | `divide_segment`, `midpoint`, `centroid` certify point containment; strict half-space $n_k \cdot I > d_k$ certifies incenter containment inside polyhedron. | Arbitrary solid-in-solid inequality (`A ⊂ B` without metric contact) has uncountably many DOF → refused `INVALID_RELATION_SPEC` fail-closed. |
| 9. `CONCENTRIC_WITH` | **REPRESENTED VIA SHARED `center_or_apex` / CERTIFIED ON DUAL SPHERES** | Sphere `(S1)` | Sphere `(S2)` | Shared named center `I` on `SolidSpec.center_or_apex` (or dual circumscribed + inscribed spheres on cube/regular tetrahedron/cylinder where engine proves $I_1 = I_2$). | If pre-declared shared center `I` disagrees with either sphere's true center ($I_{\text{out}} \ne I_{\text{in}}$, e.g. square pyramid), engine refuses `INCONSISTENT_FACTS`! |
| 10. `COAXIAL_WITH` | **IMPLICIT IN HOST AXIAL SOLID + ANCHORED SPHERE; STANDALONE MULTI-AXIAL REFUSED** | Anchored sphere | Host `cylinder` / `cone` | Sphere inscribed/circumscribed on right cylinder or cone has center on symmetry axis $OO'$ / $SO$ by exact solver. | Two independent axial solids without shared relation refuse `BRIDGE_UNSUPPORTED_CURVED_COMPOSITE`. |
| 11. `PERPENDICULAR_TO` | **SERVED** (`kind="perpendicular"`, `perpendicular_line_plane`, `perpendicular_lines`, `face_perpendicular_base`, `MAT_VUONG_DUONG`) | Line / Plane | Line / Plane | Exact vanishing inner product $u^T G v = 0$ / normal orthogonality. | Contradictory orthogonality refuses `INCONSISTENT_FACTS`. |
| 12. `PARALLEL_TO` | **SERVED** (`kind="parallel"`, `MAT_SONG_SONG`, `MAT_HAI_DUONG`, `curved_section` parallel to base) | Line / Plane | Line / Plane | Exact direction/normal proportionality; parallel section planes certified non-degenerate. | Degenerate/coincident or out-of-range parallel cuts refuse `DEGENERATE_SECTION` / `CURVED_CUT_OUT_OF_RANGE`. |

### Detailed Canonical Specification of the Three New `/2` Relation Kinds (`GeometricRelationSpecV2`)

1. **`circumscribes`**:
   - **Fields**: `relation_id`, `kind="circumscribes"`, `solid_a=<sphere_id>`, `solid_b=<host_solid_id>`, `quote=<verbatim span>` (`entity_a=None`, `entity_b=None`, `contact_ref=None`).
   - **Agreement rule**: May be declared on `SolidSpec.circumscribes`, on `GeometricRelationSpecV2(kind="circumscribes")`, or both (if both, `solid_b` must match and `inscribed_in` must be `None`, else `SOURCE_OBJECT_MISMATCH`).
   - **Preconditions**: `solid_a` is an axisless `sphere` with no explicit `radius`/`rim_point`; `solid_b` is a declared polyhedron or right cylinder/cone (`solid_a != solid_b`).
   - **Postconditions & 4-Layer Certificate**: All vertices of polyhedron (or top/bottom rims / apex of cylinder/cone) lie at identical exact rational squared distance $R^2 > 0$ from $I \in \mathbb{Q}^3$.

2. **`inscribed_in`**:
   - **Fields**: `relation_id`, `kind="inscribed_in"`, `solid_a=<sphere_id>`, `solid_b=<host_solid_id>`, `quote=<verbatim span>` (`entity_a=None`, `entity_b=None`, `contact_ref=None`).
   - **Agreement rule**: May be declared on `SolidSpec.inscribed_in`, on `GeometricRelationSpecV2(kind="inscribed_in")`, or both (mutually exclusive with `circumscribes` on the same sphere; conflict → `SOURCE_OBJECT_MISMATCH`).
   - **Preconditions**: `solid_a` is an axisless `sphere` with no explicit `radius`/`rim_point`; `solid_b` is a declared convex polyhedron or right cylinder/cone (`solid_a != solid_b`).
   - **Postconditions & 4-Layer Certificate**:
     - Polyhedron: Every boundary face $F_k$ is coplanar and convex; $I \in \mathbb{Q}^3$ lies strictly on the inward side of every $F_k$; squared orthogonal distance from $I$ to every $F_k$ equals $r^2 \in \mathbb{Q}_{>0}$; every orthogonal foot $T_k$ lies strictly inside polygon $F_k$; independent volume-surface identity $9V^2 = \rho^2 (\sum_k \tilde{S}_k)^2$ holds in exact `Fraction` arithmetic.
     - Cylinder: $h = 2r \in \mathbb{Q}_{>0}$, $I = (0, 0, r)$, $r_{\text{in}}^2 = r^2$, tangent to both bases and lateral surface.
     - Cone: $r, h, l = \sqrt{r^2+h^2} \in \mathbb{Q}_{>0}$, $r_{\text{in}} = \frac{rh}{r+l}$, $I = (0, 0, r_{\text{in}})$, equidistant to base disk and slant surface.

3. **`tangent_to`**:
   - **Fields**: `relation_id`, `kind="tangent_to"`, `solid_a=<sphere_id>`, `solid_b=<optional plane owner solid_id>`, `entity_b=("A", "B", "C", ...)`, `contact_ref="<optional single point label>"`, `quote=<verbatim span>`.
   - **Preconditions**: `solid_a` is a declared `sphere`; `entity_b` names `≥ 3` non-collinear coplanar points in scope; optional `contact_ref` is a single point label.
   - **Postconditions & 4-Layer Certificate**: Exact orthogonal squared distance $d(I, \text{plane}(entity_b))^2 == R^2$; unique tangency point $T = \text{foot}(I, P) \in \mathbb{Q}^3$ satisfies $T \in P$, $(I - T) \perp P$, and $\|I - T\|^2 = R^2$ (plus $T == \text{pts}[contact\_ref]$ if pre-declared). Refuses secant planes (`PLANE_INTERSECTS_SPHERE_NOT_TANGENT`) and disjoint planes (`PLANE_DOES_NOT_TOUCH_SPHERE`).
