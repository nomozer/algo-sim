# TypedFact Next (`typed-fact-next/1`) & Adapter /3 (`hybrid-simulation-adapter/3`) Contract Specification

> **Status:** Active Offline Research Contract (`GO_TYPEDFACT_NEXT_ADAPTER3_OFFLINE_RESEARCH_IMPLEMENTATION`)  
> **Schema Versions:** `typed-fact-next/1` (`TYPED_FACT_NEXT_SCHEMA_VERSION`), `hybrid-simulation-adapter/3` (`ADAPTER_V3_VERSION`)  
> **Default Product Mode:** `LLM_ONLY` (unchanged); `RESPONSE_CONTRACT = "flat"` (unchanged); `HYBRID_PRODUCT_ENABLEMENT = "NO-GO"` (unchanged)

---

## 1. Purpose and Scope

`TypedFactNext` (`typed-fact-next/1`) is a versioned simulation-first contract expansion that coexists alongside the frozen `TypedFact` (`typed-facts/2`) contract and `hybrid-preview-adapter/2`. Neither `TypedFact` nor Adapter `/2` is modified.

The primary pipeline is:

$$\text{User Input} \longrightarrow \text{TypedFactNext (`typed-fact-next/1`)} \longrightarrow \text{Adapter /3} \longrightarrow \text{Verified Geometry Functions \& Bounded Planner} \longrightarrow \text{Constructed Scene3D Objects} \longrightarrow \text{Interactive 3D Simulation}$$

Numeric measurements (exact volume, exact volume ratio, certified residual volume) are **optional auxiliary outputs** certified on top of the constructed 3D coordinate chart and topology.

---

## 2. Versioned Schema Identity (`typed-fact-next/1`)

Top-level payload `TypedFactNextPayload` (`extra="forbid"`):

| Field | Type | Description |
|---|---|---|
| `schema_version` | `Literal["typed-fact-next/1"]` | Mandatory version discriminator. Rejects any other version (`SCHEMA_VERSION_MISMATCH`). |
| `problem_text` | `str` | Source problem text used for quote grounding and fail-closed source verification. |
| `length_unit` | `Literal["1", "a"] \| None` | Optional symbolic length unit (`"1"` or `"a"`). |
| `solids` | `tuple[SolidSpec, ...]` | One or more declared solids with unique `solid_id`, `notation`, `solid_type`, `quote`, and optional local-to-canonical `vertex_bindings`. |
| `premises` | `tuple[PremiseSpec, ...]` | Grounded geometric premises (`kind`, `args`, `quote`, optional `solid_id` scope). Args may use unqualified labels or `solid_id::label` (`SolidQualifiedRef`). |
| `derived_sections` | `tuple[DerivedPlaneSectionSpec, ...]` | Declarative cutting-plane specifications supporting unnamed section vertices on lateral edges. |
| `relations` | `tuple[GeometricRelationSpec, ...]` | Explicit multi-solid and structural relations (`containment`, `shared_vertices`, `shared_faces`, `parallel`, `perpendicular`, `section_membership`, `coordinate_frame`). |
| `simulation_goals` | `tuple[SimulationGoalSpec, ...]` | Primary simulation goals (`construct_object`, `construct_plane_section`, `construct_derived_solid`, `highlight_geometry`, `construction_sequence`). |
| `math_goals` | `tuple[MathGoalSpec, ...]` | Optional certified math goals (`volume_ratio`, `residual_volume`, `measurement`). |

---

## 3. Core Capabilities

### 3.1 Simulation Goals (`simulation_goals`)
Each `SimulationGoalSpec` has a unique `goal_id`, `kind`, and `quote`:
1. `construct_object`: Construct a declared solid (`target_solid_id`) in `Scene3D`.
2. `construct_plane_section`: Construct a cutting plane and its polygonal section (`target_section_id`) in `Scene3D`.
3. `construct_derived_solid`: Construct a derived sub-solid (`derived_solid_id`, `apex`, `section_id`, `parent_solid_id`) bounded by the cutting plane and apex in `Scene3D`.
4. `highlight_geometry`: Emit verified highlight metadata (`target_refs`, `style_role`) linked to constructed `Scene3D` object IDs.
5. `construction_sequence`: Emit a bounded, dependency-ordered construction timeline (`focus_targets`) synchronized with `Scene3D` `dependencyGraph` and `events`.

### 3.2 Derived Object Identity (`DerivedObjectIdentity` & `DerivedPlaneSectionSpec`)
When a cutting plane $(\alpha)$ is uniquely determined (e.g., through a verified point `M` on `SA` parallel to `(ABCD)` or `(ABC)`, perpendicular to `SA`, or parallel to two non-parallel lines) and cuts lateral edges whose intersection points are **unnamed in the problem text**:
- Adapter `/3` resolves the unique plane $(\alpha) = (P_0, X_1, X_2)$ via existing Wave 1–2C primitive steps (`translate_point`, `orthogonal_projection_line`, `intersect_line_plane`).
- For each lateral edge $[S, B_i]$ of the target pyramid:
  - If the defining point already lies on $[S, B_i]$, its existing verified point identity is reused.
  - Otherwise, Adapter `/3` allocates a collision-free internal point symbol `I1, I2, ...` (disjoint from all source labels and planner auxiliary labels) and a deterministic machine identity:
    $$\texttt{derived\_id} = \texttt{sec:}\langle\text{section\_id}\rangle\texttt{:edge:}\langle\text{apex}\rangle\texttt{-}\langle\text{base\_vertex}\rangle$$
  - Explicit dependencies (`[plane_id, apex, base_vertex]`), source provenance (`quote`, `plane_kind`, `cut_edge`), and `anonymous_in_source = True` are recorded in `derived_identities`.
  - Every derived intersection $I_i$ is verified in the exact rational Gram chart to lie strictly on the finite segment $[S, B_i]$ ($0 < t_i \le 1$, where $\overrightarrow{SI_i} = t_i \overrightarrow{SB_i}$). If the plane misses any lateral edge or is degenerate, Adapter `/3` refuses fail-closed (`SECTION_NOT_CLOSED_ON_LATERAL_EDGES` or `DEGENERATE_DERIVED_SECTION`).
  - In `Scene3D`, unnamed derived section vertices carry `notation=None`, descriptive Vietnamese `label` (`"Giao điểm của SB và (α)"`), `reference` (`"giao điểm của SB và (α)"`), and `source.binding = "DERIVED_SECTION_VERTEX"`, preventing fabricated vertex names from leaking to the user UI while keeping `Scene3D` topology (`point3`, `segment3`, `polygon3`, `polyhedron3`) complete and interactive.

### 3.3 Solid-Qualified References (`SolidQualifiedRef`) & Multi-Solid Identity
- Any vertex reference in premises, relations, or goals may be written as `"solid_id::label"` (`SolidQualifiedRef`) or unqualified `"label"`.
- Each `SolidSpec` maps its local vertex labels (`S, A, B, C, ...`) to canonical root-chart point symbols via `vertex_bindings` (defaulting to identity when unambiguous).
- If two solids share a local vertex name (e.g. both `pyr1` and `pyr2` have a local vertex named `D` that refers to distinct 3D points `D1` and `D2`), any unqualified reference `"D"` is rejected fail-closed with `AMBIGUOUS_REFERENCE`.
- Explicit shared entities are validated via `relations`:
  - `shared_vertices`: pairs of `("solid_a::V", "solid_b::W")` must resolve to the exact same canonical point symbol, or Adapter `/3` refuses with `SHARED_ENTITY_MISMATCH`.
  - `shared_faces`: `("solid_a", ["A", "B", "C"])` and `("solid_b", ["A", "B", "C"])` must resolve to identical canonical point cycles and exist as certified faces of both solids.

### 3.4 Optional Mathematical Goals (`math_goals`)
- `volume_ratio`: Computes the exact rational ratio $r = V(\text{numerator\_solid}) / V(\text{denominator\_solid}) \in \mathbb{Q}$ in the shared root Gram chart, cross-checked between `volume_certificates` and `final_memory`.
- `residual_volume`: Computes the exact certified complement volume $V(\text{parent\_solid}) - V(\text{cut\_solid}) = (1 - r)\,V(\text{parent\_solid})$ as an exact `Fraction` or `Radical` with exact squared value in $\mathbb{Q}$.
- `measurement`: Delegates a bounded `distance`, `angle`, `area`, or `volume` goal to the existing Wave 1–2C Planner and Engine.

---

## 4. Refusal Taxonomy (Fail-Closed)

Adapter `/3` never guesses, approximates, or falls back to unverified coordinates:
- `SCHEMA_VERSION_MISMATCH` / `INVALID_TYPED_FACT_NEXT`: Schema or structural validation failure.
- `AMBIGUOUS_REFERENCE`: Unqualified vertex label collides across multiple solids with distinct bindings.
- `UNKNOWN_SOLID_ID` / `UNKNOWN_SECTION_ID` / `UNKNOWN_VERTEX_REF`: Reference to undeclared solid, section, or vertex.
- `DUPLICATE_DERIVED_ID`: Conflicting derived object identities.
- `SHARED_ENTITY_MISMATCH`: Declared `shared_vertices` or `shared_faces` do not resolve to identical canonical geometry.
- `COORDINATE_FRAME_DISCONNECTED`: Multiple solids cannot be embedded in a single verified root coordinate frame.
- `SECTION_NOT_CLOSED_ON_LATERAL_EDGES` / `DEGENERATE_DERIVED_SECTION`: Cutting plane does not intersect the required lateral edges on $(0, 1]$ or produces fewer than 3 distinct non-collinear vertices.
- Plus all existing Source Gate, Planner, and Engine refusal codes (`SOURCE_QUOTE_NOT_FOUND`, `UNDERDETERMINED_GROUND_SET`, `INCONSISTENT_FACTS`, `AMBIGUOUS_TOPOLOGY`, etc.).

## 5. Current closed measurement target contract (`/1` and `/2`)

Owner decisions CIC-D1 and F1/F2 recovery supersede the scope-key statement in the historical
`closed-input-contract/operand-grammar.md`. The runtime authority is `typed_fact_next.py::GOAL_TARGET_ALTERNATIVES`.

| measurement | exact alternative key sets |
|---|---|
| distance | `segment`; `point, plane`; `point, line`; `line1, line2`; `line, plane`; `plane1, plane2` |
| angle | `line, plane`; `line1, line2`; `plane1, plane2` |
| volume | `solid`; `solid_id` |
| radius | `solid`; `section_id` |
| lateral_area | `solid` |
| area | `polygon`; `section_id`; `solid` |

Each alternative is an exact set: redundant `solid, solid_id`, or any scope key beside geometric operands, is
`INVALID_MATH_GOAL`. Goal-level `solid_id` asserts ownership. Schema validity does not promise route capability;
in particular registered `volume {solid_id}` stays valid independently of historical curved-route support.

Every segment/line has exactly two distinct resolved identities; every plane/polygon has at least three, with no
repeated identity. The payload schema resolves qualified references and declared vertex bindings before checking
distinctness. Root-chart symbols, rather than display names or coordinates, define equality. An ambiguous unqualified
binding is `AMBIGUOUS_REFERENCE`; malformed or unregistered operand grammar is refused without adding aliases.
Constructed points and derived lineage still require the existing ownership/existence preflight (S8) before capability
translation or fallback. A schema comparison does not grant ownership, create points or equate coordinates.

Unscoped measurements may combine uniquely resolved identities from the verified common chart. Premise compilation
requires a common owning solid. Neither policy permits an explicit namespace or ownership claim to borrow a foreign
point. Provider emission of explicit null in an inapplicable field remains unmeasured offline.
