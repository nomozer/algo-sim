# Hybrid Wave 3A — Exact Composite Volume Reasoning (`volume-reasoning`)

- **Branch:** `research/hybrid-wave3a-volume-reasoning` from `main` = `origin/main` = `1613e0d3ebe16f0f2fe4be755052491ff581e51b`
- **Authorization:** `GO_HYBRID_WAVE3A_LOCAL_RESEARCH` (local implementation only; no GO MAIN)
- **Product Commits:** `2e277e6ec6b87a1e64bfc8c1c9127f591fedf24f` (initial Wave 3A) → `4c282ecd9f15b14ddbbe6e0be0b247e455d8edca` (review round 1 fix: reject self-ratio `numerator_solid == denominator_solid`)
- **Candidate Freeze:** `0a4b6d7027624849b53b5d79a78dd6f2116cffcd`, measured tree `df262376b3f2de7bcb0c295932c7c867a7ee2bf268ed9408071e5953ee9fc821` (112 files; supersedes `817b1730d5b3a61cd18b30348e32040337428841` / `99cef1a99038d8bf13ed6f9a2cc476fc315986650c4c038e30479d1212d18338`)
- **Independent Review:** `INDEPENDENT_REVIEW_PASS` round 2 ([`verification/independent-review.md`](verification/independent-review.md))
- **Authoritative Full T3:** `FULL_PRODUCT_GATE_PASS` at `373116d212758458c923252ef5fb72d63d0e07fb` (`11401 passed, 1 skipped, 2 deselected, 9 xfailed` backend; `70/70` files `1146` tests frontend; `tsc -b && vite build` PASS; `5/5` demo replay; `6/6` crash surface; post-T3 `freeze --verify` MATCH; [`verification/authoritative-t3.json`](verification/authoritative-t3.json))
- **Contract:** [`WAVE3A_CONTRACT_DECISION.md`](../../../../architecture/WAVE3A_CONTRACT_DECISION.md) ([run copy](WAVE3A_CONTRACT_DECISION.md)); plan [`plan.md`](plan.md)

---

## 1. Architectural Decision & Capabilities Implemented

Wave 3A extends Wave 2C's verified composite geometry (`composite-geometry`) with two bounded composite volume reasoning capabilities while preserving all five public LLM/provider surface fingerprints and `ADAPTER_VERSION = "hybrid-preview-adapter/2"`:

1. **Primary Capability — `ask_volume_ratio(numerator_solid, denominator_solid)` (`bac = 0`, dimensionless):**
   - Computes exact rational volume ratios $r = V(\text{numerator\_solid}) / V(\text{denominator\_solid}) \in \mathbb{Q}_{>0}$ between two distinct verified solids (`pyramid` or `prism`) in a single root affine+Gram chart.
   - Enforces ordered source-quote binding (`_ten_khoi_khop` in `registry.py`) and rejects dimensional units attached to a dimensionless ratio (`QUESTION_CONTEXT_UNSUPPORTED`), swapped operands (`SOURCE_OBJECT_MISMATCH`), self-ratios (`SCHEMA_INVALID` / `UNSUPPORTED_VOLUME_RATIO`), and irrational volume ratios (`UNSUPPORTED_VOLUME_RATIO`).
   - Emits `VolumeRatioCertificate` (`step = "certify_volume_ratio"`) and cross-checks the interpreter's `final_memory` against the independent Gram-metric squared volumes $V_{\text{Gram}}^2(\text{num})$ and $V_{\text{Gram}}^2(\text{den})$ (`ENGINE_SELF_CHECK_FAILED` on any discrepancy).

2. **Secondary Capability — `ask_residual_volume(original_solid, subtracted_solids)` (`bac = 3`, cubic units):**
   - Computes exact residual volumes $V(\text{original\_solid}) - \sum_{i=1}^m V(\text{subtracted}_i)$ ($1 \le m \le 2$) when and only when five formal certificates pass in `engine.py::_kiem_phan_con_lai`:
     - `ORIGINAL_SOLID_CERTIFIED` & `SUBTRACTED_SOLIDS_CERTIFIED` (strictly convex polyhedra with planar simple faces and positive squared volumes via `_mat_ngoai_khoi` and `_the_tich2_khoi`).
     - `CONTAINMENT_VERIFIED`: every vertex $u$ of every subtracted solid satisfies $n_F \cdot u - d_F \le 0$ for all outward face planes $(n_F, d_F)$ of `original_solid` (`RESIDUAL_CONTAINMENT_UNPROVED` otherwise).
     - `SHARED_BOUNDARY_VERIFIED`: every subtracted solid has at least 1 boundary face ($\ge 3$ non-collinear vertices) lying on a boundary plane $n_F \cdot u - d_F = 0$ of `original_solid` (`RESIDUAL_CONTAINMENT_UNPROVED` otherwise).
     - `DISJOINT_INTERIORS_VERIFIED`: for multiple subtracted solids, exact 3D Separating Axis Theorem (SAT) over all face normals of $\text{sub}_i$, all face normals of $\text{sub}_j$, and all non-zero edge-pair cross products $e_a \times e_b$ proves disjoint interiors (`OVERLAPPING_SUBTRACTED_SOLIDS` otherwise).
     - `POSITIVE_RESIDUAL_VERIFIED`: $\alpha_i = \sqrt{V_{\text{Gram}}^2(\text{sub}_i) / V_{\text{Gram}}^2(\text{orig})} \in \mathbb{Q}_{>0}$ and $1 - \sum_i \alpha_i > 0$ (`NON_POSITIVE_RESIDUAL_VOLUME` otherwise).
   - **Truthful Scene3D Policy:** `Scene3D.objects` renders only the verified `original_solid` and verified `subtracted_solids` as `solid` objects; it never fabricates an unverified arbitrary residual polyhedron mesh. `simulation_state.py` and `display_names.py` emit `"Tỉ số của V(A) và V(B)"` (`"V(A)/V(B)"`) and `"Hiệu của V(orig) trừ ..."` (`"V(orig) - V(sub)"`).

---

## 2. Controlled Development & Regression Results

| Suite | Class | Result |
|---|---|---|
| Wave 3A Development Corpus (`32` cases: `12` ratio, `6` residual, `14` negative) | `DEVELOPMENT_EVALUATION_NOT_BLIND` | **18/18** positive exact served (`12/12` `volume_ratio`, `6/6` `residual_volume`), **20/20** goals exact (`100%` oracle match), **14/14** negative/adversarial refusals, **0 wrong serves**, **18/18** valid `Scene3D` ([`dev-evaluation.json`](dev-evaluation.json)) |
| BH2C External Holdout (`24` cases; `D:\Documents\AlgoSim-Research\BH2C` untouched) | `KNOWN_REGRESSION_NOT_BLIND` | `fact_route` **11/11** positive (`25/25` goals), `function_route` **11/11** positive (`25/25` goals), **13/13** negative refusals, **0** diffs vs Wave 2C receipt ([`regression-summary.json`](regression-summary.json)) |
| Wave 2C Development Corpus (`30` cases) | `DEVELOPMENT_EVALUATION_NOT_BLIND` | **16/16** positive (`26/26` goals), **14/14** negative refusals, **0** diffs vs Wave 2C |
| SGH-01..18 (`268c5d66…`, lock `fe335684…`) | `KNOWN_REGRESSION_NOT_BLIND` | **10/10** positive (`16/16` math goals), **5/5** negative refusals, **0** diffs vs Wave 2C |
| SG-1..SG-6 (`30` cases) | Locked regression | **18/18** positive, **12/12** negative refusals, **0** diffs vs Wave 2C |
| BH2A-01..18 + variant ABCD | `KNOWN_REGRESSION_NOT_BLIND` | **11/12** positive + sentinel `BH2A-13` + diagnostic `BH2A-03-variant-ABCD` served, **5/5** negative refusals, **0** diffs vs Wave 2C |
| NLU GOLD (`60` cases) | Declared deltas | **0** changed |
| Historical `174` rows & Adapter `/2` `41` fixtures | Full T3 | `PASS` (`test_offline_v3_matrix_parity_on_combined_candidate`, `test_hybrid_preview_fixtures.py`) |

---

## 3. Governance & Surface Fingerprints

- `DEFAULT_MODE = "LLM_ONLY"`, `RESPONSE_CONTRACT = "flat"`, `CACHE_VERSION = "127"` (`NO_BUMP`: default `/api/analyze` path is untouched), Hybrid product enablement `NO-GO`, `ALLOW_LIVE_AI = 0`, `live_requests = 0`.
- Internal route D versions: `REGISTRY_VERSION = "geometry-functions/11"`, `PLANNER_VERSION = "geometry-fact-planner/11"`, `ENGINE_VERSION = "geometry-function-engine/9"`, `ADAPTER_VERSION = "hybrid-preview-adapter/2"`.
- Locked provider surface fingerprints (all unchanged):
  - `TypedFact.model_json_schema()`: `aa9d93eeac9f1659af8e5acd42af1904b7aaed674a8ab0f56f0c7dd8b2ad4ee8`
  - `surface_fingerprint("flat")`: `485d3834db8b18cfdb24143bfbb14deb8f5b7a9d74cb612d48db8c08252e507a`
  - `surface_fingerprint("v3")`: `4bff35bbf690a9973b2b7834019b908d507bbbb4277928e36d12dcff657e226f`
  - `function_calling.surface_fingerprint()`: `7ea511a6e3828c9adcc8402aa2d7d6b1d433e67a01ec4329c3009c46af652b25`
  - `registry.function_declarations()`: `5ceb0f999d4d7c1ee37c02207ea6470a7f972a168d6c52fa597392934d86f169`
