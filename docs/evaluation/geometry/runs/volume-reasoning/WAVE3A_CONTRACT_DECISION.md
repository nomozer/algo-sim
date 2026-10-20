# WAVE3A_CONTRACT_DECISION.md — Exact Composite Volume Reasoning Contract

- **Status:** Active Contract (Wave 3A — Local Research)
- **Branch:** `research/hybrid-wave3a-volume-reasoning`
- **Baseline `main`:** `1613e0d3ebe16f0f2fe4be755052491ff581e51b` (`product_commit_sha` = `050bb35377b40146d4862afe050a40228821a758`)
- **Governance Mode:** `GO_HYBRID_WAVE3A_LOCAL_RESEARCH` (`LOCAL IMPLEMENTATION — NO GO MAIN`)
- **Prerequisite Contract:** [`COMPOSITE_GEOMETRY_CONTRACT.md`](../../../../architecture/COMPOSITE_GEOMETRY_CONTRACT.md) (Wave 2C)

---

## 1. Architectural Contract Decision Question

> **Question:** *Can exact composite volume reasoning (`volume_ratio` and `residual_volume`) be represented using the existing internal research contract without weakening source grounding, or does it require a new internal goal/function kind?*

### Answer & Layer-by-Layer Resolution

1. **Provider-Facing Schema & Extraction Contract (`TypedFact`, `fact_extraction.py`, `function_calling.py`) — NO CHANGE TO FROZEN SURFACE FINGERPRINTS:**
   - The provider-facing `TypedFact.model_json_schema()` (`aa9d93eeac9f1659af8e5acd42af1904b7aaed674a8ab0f56f0c7dd8b2ad4ee8`), `fact_extraction.surface_fingerprint("flat")` (`485d3834db8b18cfdb24143bfbb14deb8f5b7a9d74cb612d48db8c08252e507a`), `fact_extraction.surface_fingerprint("v3")` (`4bff35bbf690a9973b2b7834019b908d507bbbb4277928e36d12dcff657e226f`), `function_calling.surface_fingerprint()` (`7ea511a6e3828c9adcc8402aa2d7d6b1d433e67a01ec4329c3009c46af652b25`), and `registry.function_declarations()` (`5ceb0f999d4d7c1ee37c02207ea6470a7f972a168d6c52fa597392934d86f169`) remain **byte-identical**.
   - In `planner.py`, `QuantityKind` uses `WithJsonSchema` (the same mechanism already established for `PointKind` in Wave 2B) so `TypedFact.model_json_schema()` continues to emit `FLAT_QUANTITIES = ("volume", "area", "length", "distance", "angle")` while offline research payloads may supply:
     - `kind="question"`, `quantity="volume_ratio"` (or `quantity="volume"` when `points_a` and `points_b` specify two solids), with `points_a` (or `solid`) naming `numerator_solid` and `points_b` naming the vertex sequence `[apex, *base]` (or `[*base, *top]`) of `denominator_solid`.
     - `kind="question"`, `quantity="residual_volume"` (or `quantity="volume"` when `solid` and `points_a`/`points_b` specify original and subtracted solids), with `solid` (or `points`) naming `original_solid` and `points_a` (and optional `points_b` when two subtracted solids are specified) naming the vertex sequence(s) of `subtracted_solids`.

2. **Internal Function Registry (`registry.py`) — NEW INTERNAL `ask` FUNCTIONS REQUIRED (`provider_offered=False`):**
   - Overloading `ask_volume(solid: str)` for ratio or residual volume would violate contract soundness for three reasons:
     1. `ask_volume` accepts a single `solid: str` and has dimensional degree `bac = 3` ($a^3$), whereas `volume_ratio` is an **ordered binary relation** (`numerator_solid`, `denominator_solid`) with dimensionless degree `bac = 0` ($a^0$).
     2. `residual_volume` is an **explicit relational subtraction** between `original_solid` and `subtracted_solids: list[str]` (`bac = 3`) that requires formal geometric containment, shared-boundary, and disjoint-interior certificates before subtraction is legal.
     3. Source Gate (`kiem_nguon`) must bind every solid operand in `ask_volume_ratio` and `ask_residual_volume` to exact Vietnamese phrasing in `quotes` and reject operand swaps, self-ratios, uncertified cuts, and invalid units fail-closed.
   - Therefore, Wave 3A introduces two internal (`provider_offered=False`) ask functions in `registry.py`:
     - `ask_volume_ratio(numerator_solid: str, denominator_solid: str)` (`AskVolumeRatioArgs`)
     - `ask_residual_volume(original_solid: str, subtracted_solids: list[str])` (`AskResidualVolumeArgs`, `1 <= len(subtracted_solids) <= 2`)

3. **Semantic Program IR & Kernel (`contract.py`, `measure_contract.py`, `interpreter.py`) — NO NEW IR STATEMENT KIND REQUIRED:**
   - `SemanticProgramSpec` (`contract.py`) and `BANG_PHEP_DO` (`measure_contract.py`) remain untouched (`semantic_program.schema.json` unchanged).
   - Both capabilities compile to existing IR primitives:
     - `measure_quantity` (`metric="volume"`) for each participating verified solid.
     - `assign` with `BinaryArithExpr` (`*`, `-`, `+`) and exact rational literals (`parse_exact`).
   - `interpreter.py::_eval_value(BinaryArithExpr)` supports `Radical` arithmetic (`+`, `-`, `*`) and `parse_exact` rational string literals, enabling exact arithmetic over `ExactNumber` (`Fraction | Radical`) when solid volumes contain square roots (`Radical`).

---

## 2. Capability A — `ask_volume_ratio(numerator_solid, denominator_solid)`

| Specification Dimension | Contract Rule |
|---|---|
| **1. Allowed Source Vietnamese Phrasing Patterns** | Closed grammar (`_CUM_HOI["ask_volume_ratio"]`) requiring explicit ratio phrasing and two ordered solid references in `quotes`:<br>- `"tỉ số thể tích (của) (hai )?(khối/hình) (chóp/lăng trụ/hộp/...) <Solid_A> và (khối/hình) (...) <Solid_B>"`<br>- `"tỉ số thể tích giữa (khối/hình) (...) <Solid_A> với/và (khối/hình) (...) <Solid_B>"`<br>- `"tỉ số V(<Solid_A>)/V(<Solid_B>)"` or `"tỉ số V_<Solid_A> / V_<Solid_B>"` |
| **2. Source Gate Binding Rules (`registry.py`)** | - `numerator_solid` and `denominator_solid` must both be valid solid identifiers (`Apex.Base` or `Base.Top`).<br>- `numerator_solid != denominator_solid` (`SCHEMA_INVALID` on `AskVolumeRatioArgs`; `UNSUPPORTED_VOLUME_RATIO` in `planner.py` and `engine.py` if both resolve to the same solid).<br>- The first solid mentioned in the ratio phrase of `quotes` must match `numerator_solid`, and the second solid mentioned in `quotes` must match `denominator_solid` (`_ten_khoi_khop`).<br>- Swapping `numerator_solid` and `denominator_solid` relative to `quotes` is rejected with `SOURCE_OBJECT_MISMATCH`.<br>- Dimensional unit annotations on a dimensionless ratio (e.g. `(đơn vị: cm^3)`, `(đơn vị: m^2)`, `(đơn vị: độ)`) are rejected with `QUESTION_CONTEXT_UNSUPPORTED`. |
| **3. `TypedFact` / Function-Call Representation** | - **Function Call:** `{"id": "...", "fn": "ask_volume_ratio", "args": {"numerator_solid": "S.AMN", "denominator_solid": "S.ABC"}, "source": {"quotes": ["..."]}}`<br>- **`TypedFact`:** `TypedFact(kind="question", role="question", quantity="volume_ratio", points_a=["S", "A", "M", "N"], points_b=["S", "A", "B", "C"], quotes=["..."])` where `points_a` (or `solid`) encodes `numerator_solid` and `points_b` encodes `denominator_solid`. Both solids must already be declared in `k.solids`. |
| **4. Planner Preconditions & Ordering Rules (`planner.py`)** | - Both `numerator_solid` and `denominator_solid` must resolve to declared solids in `k.solids`; otherwise fail closed with `UNKNOWN_SOLID`.<br>- In `_sap_xep_phu_thuoc_loi_goi`, `ask_volume_ratio` is a `Tier 5` ask call with hard dependency edges from the solid-construction calls of both `numerator_solid` and `denominator_solid` and all vertex producers of both solids. |
| **5. Engine Construction & Relationship Certificates (`engine.py`)** | - Both `numerator_solid` and `denominator_solid` must exist in `self.khoi`, live in the single root affine+Gram chart, pass face-planarity/simplicity checks (`kiem_mat_phang_don`), and have strictly positive squared volume (`v2_num > 0`, `v2_den > 0`).<br>- Emits a structured `certify_volume_ratio` trace step (`VolumeRatioCertificate`) recording `numerator_solid`, `denominator_solid`, `numerator_volume_squared`, `denominator_volume_squared`, and `ratio`. |
| **6. Exact Mathematical Formula** | In a single chart $\mathbb{Q}^3$ with SPD Gram matrix $G$, every polyhedron volume has the form $V(K) = V_{\text{chart}}(K) \cdot \sqrt{\det G}$ with $V_{\text{chart}}(K) \in \mathbb{Q}_{>0}$. Therefore:<br>$$r = \frac{V(\text{numerator\_solid})}{V(\text{denominator\_solid})} = \sqrt{\frac{V_{\text{Gram}}^2(\text{numerator\_solid})}{V_{\text{Gram}}^2(\text{denominator\_solid})}} \in \mathbb{Q}_{>0}$$<br>Cross-checked post-execution against the interpreter's `final_memory`: `_binh_phuong(fm[v_tu]) == v2_num`, `_binh_phuong(fm[v_mau]) == v2_den`, and `_binh_phuong(fm[kq]) == r * r`. |
| **7. Dimension / Degree in Symbolic Parameter `a`** | `bac = 0` (`dim = 0`, `unit = None`). When the problem uses symbolic length $a$, $a^3$ cancels in $V(A)/V(B)$, so the answer is a pure rational number (e.g. `"1/4"`, `"3/8"`, `"2"`). |
| **8. Refusal Codes** | - `UNKNOWN_SOLID`: Either solid is not declared in `self.khoi`.<br>- `SOURCE_OBJECT_MISMATCH`: Solid labels or `numerator`/`denominator` order in args do not match `quotes`.<br>- `SCHEMA_INVALID` / `UNSUPPORTED_VOLUME_RATIO`: Both operands refer to the same solid, or volume ratio is not a positive rational number.<br>- `DEGENERATE_SOLID` / `NON_SIMPLE_FACE` / `NON_COPLANAR_POINTS`: Either solid is degenerate or non-simple.<br>- `UNSUPPORTED_MULTIPLE_BASES`: Solids do not share a single verified root chart.<br>- `QUESTION_CONTEXT_UNSUPPORTED`: Invalid dimensional unit attached to a dimensionless ratio.<br>- `ENGINE_SELF_CHECK_FAILED`: Kernel volume ratio disagrees with independent Gram-metric certificate. |
| **9. Scene3D & Pedagogical Readout Policy** | - Both `numerator_solid` and `denominator_solid` are constructed in the IR and rendered as verified `solid` objects in `Scene3D` using `formation.lop_khoi` topology.<br>- `simulation_state.py` and `display_names.py` label the quantity `"Tỉ số của V(A) và V(B)"` with formula `"V(A)/V(B)"` (`producer="assign.volume_ratio"`). |

---

## 3. Capability B — `ask_residual_volume(original_solid, subtracted_solids)`

| Specification Dimension | Contract Rule |
|---|---|
| **1. Allowed Source Vietnamese Phrasing Patterns** | Closed grammar (`_CUM_HOI["ask_residual_volume"]`) requiring explicit residual/subtraction phrasing and ordered references to `original_solid` first and `subtracted_solids` second:<br>- `"thể tích (của) phần còn lại của (khối/hình) (...) <Original> sau khi cắt (bỏ/đi) (khối/hình/hai khối chóp) (...) <Sub_1> [và <Sub_2>]"`<br>- `"thể tích phần (khối/hình) (...) <Original> còn lại sau khi cắt (bỏ/đi) (khối/hình) (...) <Sub_1> [và <Sub_2>]"`<br>- `"hiệu thể tích (của) (khối/hình) (...) <Original> và (khối/hình) (...) <Sub_1>"` |
| **2. Source Gate Binding Rules (`registry.py`)** | - `original_solid` must match the first solid mentioned in the residual/subtraction question phrase.<br>- `subtracted_solids` (`1 <= len(subtracted_solids) <= 2`, distinct solid names) must match the subtracted solid(s) mentioned after `"cắt bỏ"` / `"cắt đi"` / `"và"` in strictly increasing textual order (`_ds_khoi_khop`).<br>- Swapping `original_solid` and `subtracted_solid` (e.g. `V(sub) - V(orig)`) is rejected with `SOURCE_OBJECT_MISMATCH` (if contradicting `quotes`) or `RESIDUAL_CONTAINMENT_UNPROVED` / `NON_POSITIVE_RESIDUAL_VOLUME`.<br>- Duplicate entries in `subtracted_solids` or `original_solid in subtracted_solids` are rejected with `SCHEMA_INVALID` / `FACT_INCOMPLETE`.<br>- Unit policy matches `"volume"` (`cm^3`, `m^3`, `dm^3`, `lít` allowed; `cm^2`, `độ` rejected with `QUESTION_CONTEXT_UNSUPPORTED`). |
| **3. `TypedFact` / Function-Call Representation** | - **Function Call:** `{"id": "...", "fn": "ask_residual_volume", "args": {"original_solid": "S.ABC", "subtracted_solids": ["S.AMN"]}, "source": {"quotes": ["..."]}}`<br>- **`TypedFact`:** `TypedFact(kind="question", role="question", quantity="residual_volume", solid="S.ABC", points_a=["S", "A", "M", "N"], ...)` (and optional `points_b=["B", "C", "M", "P"]` when a second subtracted solid is present alongside `solid="S.ABC"`). All referenced solids must be declared in `k.solids`. |
| **4. Planner Preconditions & Ordering Rules (`planner.py`)** | - `original_solid` and every solid in `subtracted_solids` must resolve to declared solids in `k.solids`; otherwise fail closed with `UNKNOWN_SOLID`.<br>- In `_sap_xep_phu_thuoc_loi_goi`, `ask_residual_volume` is placed in `Tier 5` after `original_solid`, all `subtracted_solids`, and all their vertex producers. |
| **5. Engine Construction & Relationship Certificates (`engine.py`)** | Subtraction is permitted **if and only if** all formal checks pass (see §4.2 below):<br>1. `ORIGINAL_SOLID_CERTIFIED` & `SUBTRACTED_SOLIDS_CERTIFIED`<br>2. `CONTAINMENT_VERIFIED` (exact rational outward half-space inclusion $n_i \cdot v - d_i \le 0$ of all subtracted vertices inside strictly convex `original_solid`)<br>3. `SHARED_BOUNDARY_VERIFIED` (each subtracted solid has at least 1 boundary face with $\ge 3$ non-collinear vertices lying on a boundary plane $n_i \cdot v - d_i = 0$ of `original_solid`)<br>4. `DISJOINT_INTERIORS_VERIFIED` (for multiple subtracted solids, exact 3D Separating Axis Theorem over face normals and edge-pair cross products proves disjoint interiors)<br>5. `POSITIVE_RESIDUAL_VERIFIED` ($V(\text{original}) - \sum_i V(\text{sub}_i) > 0$) |
| **6. Exact Mathematical Formula** | Single subtraction:<br>$$V_{\text{residual}} = V(\text{original\_solid}) - V(\text{subtracted\_solid})$$<br>Multi-subtraction:<br>$$V_{\text{residual}} = V(\text{original\_solid}) - \sum_{i=1}^m V(\text{subtracted}_i) = \left(1 - \sum_{i=1}^m \alpha_i\right) V(\text{original\_solid})$$<br>where $\alpha_i = \sqrt{V_{\text{Gram}}^2(\text{sub}_i) / V_{\text{Gram}}^2(\text{orig})} \in \mathbb{Q}_{>0}$ and $1 - \sum_{i=1}^m \alpha_i > 0$.<br>Cross-checked post-execution against the independent Gram-metric residual volume squared: $\text{square}(V_{\text{residual}}) = \left(1 - \sum_i \alpha_i\right)^2 \cdot V_{\text{Gram}}^2(\text{orig})$. |
| **7. Dimension / Degree in Symbolic Parameter `a`** | `bac = 3` (`dim = 3`, `unit = "đvtt"`), scaled by $a^3$ when symbolic parameter $a$ is present in the problem. |
| **8. Refusal Codes** | - `UNKNOWN_SOLID`: `original_solid` or any subtracted solid is not in `self.khoi`.<br>- `SOURCE_OBJECT_MISMATCH`: Solid operands do not match `quotes`.<br>- `RESIDUAL_CONTAINMENT_UNPROVED`: A subtracted solid has a vertex outside `original_solid`, does not share a boundary face with `original_solid`, or has an incommensurable volume ratio.<br>- `OVERLAPPING_SUBTRACTED_SOLIDS`: Duplicate or interior-overlapping subtracted solids.<br>- `NON_POSITIVE_RESIDUAL_VOLUME`: Residual volume is $\le 0$.<br>- `ENGINE_SELF_CHECK_FAILED`: Kernel subtraction result disagrees with the independent Gram-metric certificate. |
| **9. Scene3D & Pedagogical Readout Policy** | - **Truthful Scene3D Policy (No Fabricated Topology):** `ask_residual_volume` is explicitly defined as an exact scalar relation over `original_solid` and `subtracted_solids`. Scene3D renders ONLY the verified `original_solid` and verified `subtracted_solids` as `solid` objects; it **never** fabricates an unverified residual frustum/polyhedron mesh.<br>- `simulation_state.py` and `display_names.py` label the quantity `"Hiệu của V(orig) trừ ..."` with formula `"V(orig) - V(sub)"` (`producer="assign.residual_volume"`). |

---

## 4. Capability C — Formal Relationship Certificates (`engine.py`)

Every composite volume query emits a machine-verifiable certificate in `d.trace`:

### 4.1 `VolumeRatioCertificate` (`step = "certify_volume_ratio"`)
1. **Solid Validity:** Both `k_num = self.khoi[numerator_solid]` and `k_den = self.khoi[denominator_solid]` are distinct verified 3D polyhedra in the same chart with $V_{\text{Gram}}^2(k_{\text{num}}) > 0$ and $V_{\text{Gram}}^2(k_{\text{den}}) > 0$.
2. **Gram-Metric Volume Ratio:** Compute $r = \sqrt{V_{\text{Gram}}^2(k_{\text{num}}) / V_{\text{Gram}}^2(k_{\text{den}})} \in \mathbb{Q}_{>0}$ using exact rational square-root verification (`_sqrt_q`).
3. **Kernel Cross-Check:** Post-execution self-check verifies `_binh_phuong(fm[v_tu]) == v2_num`, `_binh_phuong(fm[v_mau]) == v2_den`, and `_binh_phuong(fm[kq]) == r * r`.

### 4.2 `ResidualVolumeCertificate` (`step = "certify_residual_volume"`)
1. **Strict Convexity & Outward Half-Space Representation of `original_solid` (`_mat_ngoai_khoi`):**
   - Every topological face $F$ of `original_solid` defines a plane $\Pi_F = \{x \in \mathbb{Q}^3 : n_F \cdot x - d_F = 0\}$ with exact outward normal $n_F$ oriented so that every off-face vertex $q$ of `original_solid` satisfies $n_F \cdot q - d_F < 0$ (`{val > 0 for val in off} == {False}`). Any non-convex or degenerate face configuration is immediately rejected with `DEGENERATE_SOLID`.
   - Therefore `original_solid` is certified to be a strictly convex polyhedron equal to $\bigcap_F \{x \in \mathbb{R}^3 : n_F \cdot x - d_F \le 0\}$.
2. **Containment Certificate (`CONTAINMENT_VERIFIED`):**
   - Every vertex $u$ of every `sub` in `subtracted_solids` must satisfy $n_F \cdot u - d_F \le 0$ for all boundary faces $F$ of `original_solid`. If any vertex violates this, refuse immediately with `RESIDUAL_CONTAINMENT_UNPROVED`.
3. **Shared Boundary Certificate (`SHARED_BOUNDARY_VERIFIED`):**
   - Each subtracted solid `sub` must have at least one boundary face ($\ge 3$ non-collinear vertices) lying entirely on a boundary plane $n_F \cdot u - d_F = 0$ of `original_solid`. Otherwise refuse with `RESIDUAL_CONTAINMENT_UNPROVED`.
4. **Disjoint Interiors Certificate (`DISJOINT_INTERIORS_VERIFIED`):**
   - For every pair of distinct subtracted solids $(\text{sub}_i, \text{sub}_j)$, the engine runs the exact 3D Separating Axis Theorem (SAT) over all face normals of $\text{sub}_i$, all face normals of $\text{sub}_j$, and all non-zero edge-pair cross products $e_a \times e_b$ to verify weak separation ($\max_{p \in \text{sub}_i} n \cdot p \le \min_{q \in \text{sub}_j} n \cdot q$ or vice versa). Otherwise refuse with `OVERLAPPING_SUBTRACTED_SOLIDS`.
5. **Strict Positivity & Independent Volume Cross-Check (`POSITIVE_RESIDUAL_VERIFIED`):**
   - Verify $\alpha_i = \sqrt{V_{\text{Gram}}^2(\text{sub}_i) / V_{\text{Gram}}^2(\text{orig})} \in \mathbb{Q}_{>0}$ and $r_{\text{res}} = 1 - \sum_i \alpha_i > 0$ (otherwise refuse with `NON_POSITIVE_RESIDUAL_VOLUME`).
   - Verify post-execution that `_binh_phuong(fm[kq]) == (r_res ** 2) * v2_orig`.
