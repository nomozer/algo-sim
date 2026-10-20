# WAVE3A_CONTRACT_DECISION.md — Exact Composite Volume Reasoning Contract

- **Status:** Active Contract (Wave 3A — Local Research)
- **Branch:** `research/hybrid-wave3a-volume-reasoning`
- **Baseline `main`:** `1613e0d3ebe16f0f2fe4be755052491ff581e51b` (`product_commit_sha` = `050bb35377b40146d4862afe050a40228821a758`)
- **Governance Mode:** `GO_HYBRID_WAVE3A_LOCAL_RESEARCH` (`LOCAL IMPLEMENTATION — NO GO MAIN`)
- **Canonical Contract Path:** [`docs/architecture/WAVE3A_CONTRACT_DECISION.md`](../../../architecture/WAVE3A_CONTRACT_DECISION.md)

---

## 1. Architectural Contract Decision Question

> **Question:** *Can exact composite volume reasoning (`volume_ratio` and `residual_volume`) be represented using the existing internal research contract without weakening source grounding, or does it require a new internal goal/function kind?*

### Answer & Layer-by-Layer Resolution

1. **Provider-Facing Schema & Extraction Contract (`TypedFact`, `fact_extraction.py`, `function_calling.py`) — NO CHANGE TO FROZEN SURFACE FINGERPRINTS:**
   - The provider-facing `TypedFact.model_json_schema()` (`aa9d93eeac9f1659af8e5acd42af1904b7aaed674a8ab0f56f0c7dd8b2ad4ee8`), `fact_extraction.surface_fingerprint("flat")` (`485d3834db8b18cfdb24143bfbb14deb8f5b7a9d74cb612d48db8c08252e507a`), `fact_extraction.surface_fingerprint("v3")` (`4bff35bbf690a9973b2b7834019b908d507bbbb4277928e36d12dcff657e226f`), `function_calling.surface_fingerprint()` (`7ea511a6e3828c9adcc8402aa2d7d6b1d433e67a01ec4329c3009c46af652b25`), and `registry.function_declarations()` (`5ceb0f999d4d7c1ee37c02207ea6470a7f972a168d6c52fa597392934d86f169`) remain **byte-identical**.
   - In `planner.py`, `QuantityKind` uses `WithJsonSchema` (the same mechanism already established for `PointKind` in Wave 2B) so `TypedFact.model_json_schema()` continues to emit `FLAT_QUANTITIES = ("volume", "area", "length", "distance", "angle")` while offline research payloads may supply:
     - `kind="ask"`, `quantity="volume_ratio"` (or `quantity="volume"` when `quote` matches the closed volume-ratio grammar), with `solid` (or `points_a`) naming `numerator_solid` and `points_b` naming the vertex sequence `[apex, *base]` (or `[*base, *top]`) of `denominator_solid`.
     - `kind="ask"`, `quantity="residual_volume"` (or `quantity="volume"` when `quote` matches the closed residual-volume grammar), with `solid` naming `original_solid` and `points_b` (and optional `points_a` when two subtracted solids are specified) naming the vertex sequence(s) of `subtracted_solids`.

2. **Internal Function Registry (`registry.py`) — NEW INTERNAL `ask` FUNCTIONS REQUIRED (`provider_offered=False`):**
   - Overloading `ask_volume(solid: str)` for ratio or residual volume would violate contract soundness for three reasons:
     1. `ask_volume` accepts a single `solid: str` and has dimensional degree `bac = 3` ($a^3$), whereas `volume_ratio` is an **ordered binary relation** (`numerator_solid`, `denominator_solid`) with dimensionless degree `bac = 0` ($a^0$).
     2. `residual_volume` is an **explicit relational subtraction** between `original_solid` and `subtracted_solids: list[str]` (`bac = 3`) that requires formal geometric containment, shared-boundary, and disjoint-interior certificates before subtraction is legal.
     3. Source Gate (`kiem_hop_le`) must bind every solid operand in `ask_volume_ratio` and `ask_residual_volume` to exact Vietnamese phrasing in `quote` and reject operand swaps, self-ratios, uncertified cuts, and invalid units fail-closed.
   - Therefore, Wave 3A introduces two internal (`provider_offered=False`) ask functions in `registry.py`:
     - `ask_volume_ratio(numerator_solid: str, denominator_solid: str)` (`AskVolumeRatioArgs`)
     - `ask_residual_volume(original_solid: str, subtracted_solids: list[str])` (`AskResidualVolumeArgs`)

3. **Semantic Program IR & Kernel (`contract.py`, `measure_contract.py`, `interpreter.py`) — NO NEW IR STATEMENT KIND REQUIRED:**
   - `SemanticProgramSpec` (`contract.py`) and `BANG_PHEP_DO` (`measure_contract.py`) remain untouched (`semantic_program.schema.json` unchanged).
   - Both capabilities compile to existing IR primitives:
     - `MeasureStatement(kind="measure_quantity", metric="volume", ...)` for each participating verified solid.
     - `AssignStatement` with `RationalConst` and `BinaryArithExpr` (`*`, `-`) for exact rational/radical arithmetic.
     - `CheckStatement(kind="check_equality", ...)` for kernel-level verification against the certified volume ratio.
   - `interpreter.py::_eval_value(BinaryArithExpr)` is upgraded to use `radical.add`, `radical.negate`, and `radical.multiply` instead of raw Python `+`, `-`, `*`, enabling exact arithmetic (`a - b`, `r * b`) over `ExactNumber` (`Fraction | Radical`) when solid volumes contain square roots (`Radical`).

---

## 2. Capability A — `ask_volume_ratio(numerator_solid, denominator_solid)`

| Specification Dimension | Contract Rule |
|---|---|
| **1. Allowed Source Vietnamese Phrasing Patterns** | Closed grammar requiring explicit ratio phrasing and two ordered solid references in `quote`:<br>- `"tỉ số thể tích (của) (khối/hình) (chóp/lăng trụ/hộp/...) <Solid_A> và (khối/hình) (...) <Solid_B>"`<br>- `"tỉ số thể tích giữa (khối/hình) (...) <Solid_A> với/và (khối/hình) (...) <Solid_B>"`<br>- `"tỉ số V(<Solid_A>)/V(<Solid_B>)"` or `"tỉ số V_<Solid_A> / V_<Solid_B>"` |
| **2. Source Gate Binding Rules (`registry.py`)** | - `numerator_solid` and `denominator_solid` must both be valid solid identifiers (`Apex.Base` or `Base.Top`).<br>- `numerator_solid != denominator_solid` (`DEGENERATE_VOLUME_RATIO` / `SCHEMA_INVALID` if equal up to base cyclic/reversal equivalence).<br>- The first solid mentioned in the ratio phrase of `quote` must match `numerator_solid` (up to valid pyramid base cycle/reversal or prism base+top cycle/swap), and the second solid mentioned in `quote` must match `denominator_solid`.<br>- Swapping `numerator_solid` and `denominator_solid` relative to `quote` is rejected with `SOURCE_OBJECT_MISMATCH`.<br>- Dimensional unit annotations on a dimensionless ratio (e.g. `(đơn vị: cm^3)`, `(đơn vị: m^2)`, `(đơn vị: độ)`) are rejected with `QUESTION_CONTEXT_UNSUPPORTED`. |
| **3. `TypedFact` / Function-Call Representation** | - **Function Call:** `{"id": "...", "fn": "ask_volume_ratio", "args": {"numerator_solid": "S.AMN", "denominator_solid": "S.ABC"}, "quote": "..."}`<br>- **`TypedFact`:** `TypedFact(kind="ask", quantity="volume_ratio", solid="S.AMN", points_b=["S", "A", "M", "N"], ...)` where `solid` is `numerator_solid` and `points_b` encodes the vertex list of `denominator_solid` (e.g. `["S", "A", "B", "C"]` for `S.ABC`, or `["A", "B", "C", "A'", "B'", "C'"]` for `ABC.A'B'C'`), OR `points_a` encodes `numerator_solid` vertices and `points_b` encodes `denominator_solid` vertices. Both solids must already be declared in `k.solids`. |
| **4. Planner Preconditions & Ordering Rules (`planner.py`)** | - Both `numerator_solid` and `denominator_solid` must resolve to declared solids in `k.solids`; otherwise fail closed with `UNKNOWN_SOLID` / `UNSUPPORTED_FACT_SHAPE`.<br>- In `_sap_xep_phu_thuoc_loi_goi`, `ask_volume_ratio` is a `Tier 5` ask call with hard dependency edges from the solid-construction calls of both `numerator_solid` and `denominator_solid` and all vertex producers of both solids. |
| **5. Engine Construction & Relationship Certificates (`engine.py`)** | - Both `numerator_solid` and `denominator_solid` must exist in `self.khoi`, live in the single root affine+Gram chart, pass face-planarity/simplicity checks (`kiem_mat_phang_don`), and have strictly positive squared volume (`v2_num > 0`, `v2_den > 0`).<br>- Emits a structured `verify_volume_ratio` trace step (`VolumeRatioCertificate`) recording `numerator_solid`, `denominator_solid`, `v2_numerator`, `v2_denominator`, `ratio_squared`, and `exact_ratio`. |
| **6. Exact Mathematical Formula** | In a single chart $\mathbb{Q}^3$ with SPD Gram matrix $G$, every polyhedron volume has the form $V(K) = V_{\text{chart}}(K) \cdot \sqrt{\det G}$ with $V_{\text{chart}}(K) \in \mathbb{Q}_{>0}$. Therefore:<br>$$r = \frac{V(\text{numerator\_solid})}{V(\text{denominator\_solid})} = \frac{V_{\text{chart}}(\text{numerator\_solid})}{V_{\text{chart}}(\text{denominator\_solid})} \in \mathbb{Q}_{>0}$$<br>Cross-checked independently via Gram-metric squared volumes:<br>$$r^2 = \frac{V_{\text{Gram}}^2(\text{numerator\_solid})}{V_{\text{Gram}}^2(\text{denominator\_solid})} = \frac{\text{square}(V_{\text{kernel}}(\text{numerator\_solid}))}{\text{square}(V_{\text{kernel}}(\text{denominator\_solid}))}$$ |
| **7. Dimension / Degree in Symbolic Parameter `a`** | `bac = 0` (`dim = 0`, `unit = None`). When the problem uses symbolic length $a$, $a^3$ cancels in $V(A)/V(B)$, so the answer is a pure rational number (e.g. `"1/4"`, `"3/8"`, `"2"`). |
| **8. Refusal Codes** | - `UNKNOWN_SOLID`: Either solid is not declared in `self.khoi`.<br>- `SOURCE_OBJECT_MISMATCH`: Solid labels or `numerator`/`denominator` order in args do not match `quote`.<br>- `DEGENERATE_VOLUME_RATIO`: Both operands refer to the same solid.<br>- `DEGENERATE_SOLID` / `NON_SIMPLE_FACE` / `POINTS_NOT_COPLANAR`: Either solid is degenerate or non-simple.<br>- `UNSUPPORTED_MULTIPLE_BASES`: Solids do not share a single verified root chart.<br>- `QUESTION_CONTEXT_UNSUPPORTED`: Invalid dimensional unit attached to a dimensionless ratio.<br>- `ENGINE_SELF_CHECK_FAILED`: Kernel volume ratio disagrees with independent Gram-metric certificate. |
| **9. Scene3D & Pedagogical Readout Policy** | - Both `numerator_solid` and `denominator_solid` are constructed in the IR and rendered as verified `solid` objects in `Scene3D` using `formation.lop_khoi` topology.<br>- `simulation_state.py` labels the quantity `"Tỉ số thể tích"` (`kind="ratio"`, `unit=None`). |

---

## 3. Capability B — `ask_residual_volume(original_solid, subtracted_solids)`

| Specification Dimension | Contract Rule |
|---|---|
| **1. Allowed Source Vietnamese Phrasing Patterns** | Closed grammar requiring explicit residual/subtraction phrasing and ordered references to `original_solid` first and `subtracted_solids` second:<br>- `"thể tích (của) phần còn lại của (khối/hình) (...) <Original> sau khi cắt (bỏ/đi) (khối/hình/hai khối chóp) (...) <Sub_1> [và <Sub_2>]"`<br>- `"thể tích phần (khối/hình) (...) <Original> còn lại sau khi cắt (bỏ/đi) (khối/hình) (...) <Sub_1> [và <Sub_2>]"`<br>- `"hiệu thể tích (của) (khối/hình) (...) <Original> và (khối/hình) (...) <Sub_1>"` |
| **2. Source Gate Binding Rules (`registry.py`)** | - `original_solid` must match the first solid mentioned in the residual/subtraction question phrase.<br>- `subtracted_solids` (non-empty list of 1 or 2 distinct solid names) must match the subtracted solid(s) mentioned after `"cắt bỏ"` / `"cắt đi"` / `"và"` in `quote`.<br>- Swapping `original_solid` and `subtracted_solid` (e.g. `V(sub) - V(orig)`) is rejected with `SOURCE_OBJECT_MISMATCH` (if contradicting `quote`) or `SUBTRACTED_SOLID_NOT_CONTAINED` / `NON_POSITIVE_RESIDUAL_VOLUME`.<br>- Duplicate entries in `subtracted_solids` or `original_solid in subtracted_solids` are rejected with `SCHEMA_INVALID` / `OVERLAPPING_SUBTRACTED_SOLIDS`.<br>- Unit policy matches `"volume"` (`cm^3`, `m^3`, `dm^3`, `lít` allowed; `cm^2`, `độ` rejected with `QUESTION_CONTEXT_UNSUPPORTED`). |
| **3. `TypedFact` / Function-Call Representation** | - **Function Call:** `{"id": "...", "fn": "ask_residual_volume", "args": {"original_solid": "S.ABC", "subtracted_solids": ["S.AMN"]}, "quote": "..."}`<br>- **`TypedFact`:** `TypedFact(kind="ask", quantity="residual_volume", solid="S.ABC", points_b=["S", "A", "M", "N"], ...)` (and optional `points_a=["B", "C", "M", "P"]` when a second subtracted solid is present alongside `solid="S.ABC"`). All referenced solids must be declared in `k.solids`. |
| **4. Planner Preconditions & Ordering Rules (`planner.py`)** | - `original_solid` and every solid in `subtracted_solids` must resolve to declared solids in `k.solids`; otherwise fail closed with `UNKNOWN_SOLID` / `UNSUPPORTED_FACT_SHAPE`.<br>- In `_sap_xep_phu_thuoc_loi_goi`, `ask_residual_volume` is placed in `Tier 5` after `original_solid`, all `subtracted_solids`, and all their vertex producers. |
| **5. Engine Construction & Relationship Certificates (`engine.py`)** | Subtraction is permitted **if and only if** all 5 formal certificates pass (see §4 below):<br>1. `ORIGINAL_SOLID_CERTIFIED`<br>2. `SUBTRACTED_SOLIDS_CERTIFIED`<br>3. `CONTAINMENT_VERIFIED` (exact rational convex-hull / half-space inclusion of all subtracted vertices inside `original_solid`)<br>4. `SHARED_BOUNDARY_VERIFIED` (each subtracted solid is a certified corner/face cut sharing at least one boundary face/vertex structure with `original_solid`)<br>5. `DISJOINT_INTERIORS_VERIFIED` (for multiple subtracted solids, an exact rational separating plane strictly separates their interiors)<br>6. `POSITIVE_RESIDUAL_VERIFIED` ($V(\text{original}) - \sum_i V(\text{sub}_i) > 0$) |
| **6. Exact Mathematical Formula** | Single subtraction:<br>$$V_{\text{residual}} = V(\text{original\_solid}) - V(\text{subtracted\_solid})$$<br>Multi-subtraction:<br>$$V_{\text{residual}} = V(\text{original\_solid}) - \sum_{i=1}^m V(\text{subtracted}_i) = \left(1 - \sum_{i=1}^m r_i\right) V(\text{original\_solid})$$<br>where $r_i = V(\text{subtracted}_i) / V(\text{original\_solid}) \in \mathbb{Q}_{>0}$ and $r_{\text{res}} = 1 - \sum_{i=1}^m r_i \in (0, 1) \cap \mathbb{Q}$.<br>Cross-checked against the independent Gram-metric volume squared: $\text{square}(V_{\text{residual}}) = r_{\text{res}}^2 \cdot V_{\text{Gram}}^2(\text{original\_solid})$. |
| **7. Dimension / Degree in Symbolic Parameter `a`** | `bac = 3` (`dim = 3`, `unit = "đvtt"`), scaled by $a^3$ when symbolic parameter $a$ is present in the problem. |
| **8. Refusal Codes** | - `UNKNOWN_SOLID`: `original_solid` or any subtracted solid is not in `self.khoi`.<br>- `SOURCE_OBJECT_MISMATCH`: Solid operands do not match `quote`.<br>- `SUBTRACTED_SOLID_NOT_CONTAINED`: A subtracted solid has a vertex outside `original_solid` or is not a proper sub-solid.<br>- `UNVERIFIED_SOLID_CONTAINMENT`: Subtracted solid does not satisfy the shared-boundary corner/face cut certificate.<br>- `OVERLAPPING_SUBTRACTED_SOLIDS`: Duplicate or interior-overlapping subtracted solids.<br>- `NON_POSITIVE_RESIDUAL_VOLUME`: Residual volume is $\le 0$.<br>- `ENGINE_SELF_CHECK_FAILED`: Kernel subtraction result disagrees with the independent Gram-metric certificate. |
| **9. Scene3D & Pedagogical Readout Policy** | - **Truthful Scene3D Policy (No Fabricated Topology):** `ask_residual_volume` is explicitly defined as an exact scalar relation over `original_solid` and `subtracted_solids`. Scene3D renders ONLY the verified `original_solid` and verified `subtracted_solids` as `solid` objects; it **never** fabricates an unverified residual frustum/polyhedron mesh.<br>- `simulation_state.py` labels the quantity `"Thể tích phần còn lại"` (`kind="volume"`, `unit="đvtt"`). |

---

## 4. Capability C — Formal Relationship Certificates (`engine.py`)

Every composite volume query emits a machine-verifiable certificate in `d.trace`:

### 4.1 `VolumeRatioCertificate` (`step = "verify_volume_ratio"`)
1. **Solid Validity:** Both `k_num = self.khoi[numerator_solid]` and `k_den = self.khoi[denominator_solid]` are verified 3D polyhedra in the same chart with $V_{\text{Gram}}^2(k_{\text{num}}) > 0$ and $V_{\text{Gram}}^2(k_{\text{den}}) > 0$.
2. **Chart-Volume Ratio:** Using exact signed tetrahedral decomposition in $\mathbb{Q}^3$, $V_{\text{chart}}(k) \in \mathbb{Q}_{>0}$ is computed for each solid, yielding $r = V_{\text{chart}}(k_{\text{num}}) / V_{\text{chart}}(k_{\text{den}}) \in \mathbb{Q}_{>0}$.
3. **Gram-Metric Cross-Check:** Verify $r^2 == V_{\text{Gram}}^2(k_{\text{num}}) / V_{\text{Gram}}^2(k_{\text{den}})$, where $V_{\text{Gram}}^2$ is computed independently from base polygon Gram area squared and Gram point-to-plane altitude squared.
4. **Kernel Cross-Check:** Verify `r * V_kernel(k_den) == V_kernel(k_num)` via IR `check_equality` and `square(V_kernel(k_num)) / square(V_kernel(k_den)) == r * r`.

### 4.2 `ResidualVolumeCertificate` (`step = "verify_residual_volume"`)
1. **Inward Half-Space Representation of `original_solid`:**
   - Every face $F$ of `original_solid` defines a plane $\Pi_F$ in $\mathbb{Q}^3$ with exact normal covector $n_F$ oriented **inward** (so that every vertex of `original_solid` not on $F$ has strictly positive signed evaluation $s_F(v) > 0$, while vertices on $F$ have $s_F(v) = 0$).
   - Since `original_solid` is a verified convex pyramid or prism with planar simple faces, a point $p \in \mathbb{Q}^3$ lies in the closure of `original_solid` if and only if $s_F(p) \ge 0$ for every boundary face $F$ of `original_solid`.
2. **Containment Certificate (`CONTAINMENT_VERIFIED`):**
   - Every vertex $u$ of every `sub` in `subtracted_solids` must satisfy $s_F(u) \ge 0$ for all boundary faces $F$ of `original_solid`. If any vertex has $s_F(u) < 0$, refuse immediately with `SUBTRACTED_SOLID_NOT_CONTAINED`.
   - Furthermore, every vertex $u$ of `sub` must lie on the boundary of `original_solid` (i.e., $s_F(u) = 0$ for at least one boundary face $F$ of `original_solid`), and each `sub` must have $0 < V_{\text{chart}}(\text{sub}) < V_{\text{chart}}(\text{orig})$.
3. **Shared Boundary / Cut Certificate (`SHARED_BOUNDARY_VERIFIED`):**
   - Each subtracted pyramid `sub` must share at least 3 boundary faces (in plane support) with boundary faces of `original_solid` (a corner/edge/face cut of `original_solid`, e.g., a corner pyramid cut by a single plane $\Pi_{\text{cut}}$ where the remaining 3+ faces of `sub` lie on boundary planes of `original_solid`). If fewer than 3 faces of `sub` lie on boundary planes of `original_solid`, refuse with `UNVERIFIED_SOLID_CONTAINMENT`.
4. **Disjoint Interiors Certificate (`DISJOINT_INTERIORS_VERIFIED`):**
   - For every pair of distinct subtracted solids $(\text{sub}_i, \text{sub}_j)$, there must exist an exact rational plane $\Pi$ (drawn from the boundary face planes of $\text{sub}_i$ or $\text{sub}_j$) that strictly separates their interiors: all vertices of $\text{sub}_i$ satisfy $\Pi(v) \ge 0$ (with at least one $> 0$) and all vertices of $\text{sub}_j$ satisfy $\Pi(w) \le 0$ (with at least one $< 0$). Otherwise refuse with `OVERLAPPING_SUBTRACTED_SOLIDS`.
5. **Strict Positivity & Independent Volume Cross-Check (`POSITIVE_RESIDUAL_VERIFIED`):**
   - Verify $r_{\text{res}} = 1 - \sum_i \frac{V_{\text{chart}}(\text{sub}_i)}{V_{\text{chart}}(\text{orig})} > 0$ (otherwise refuse with `NON_POSITIVE_RESIDUAL_VOLUME` or `SUBTRACTED_SOLID_NOT_CONTAINED`).
   - Verify $\text{square}(V_{\text{residual}}) == r_{\text{res}}^2 \cdot V_{\text{Gram}}^2(\text{orig})$.
