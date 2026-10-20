# Independent Mathematical & Architecture Review — Wave 3A (`volume-reasoning`)

- **Reviewer Subagent:** `Independent Wave 3A Math & Architecture Reviewer` (`c382d66b-37f3-4826-b04d-edd822fd7254`)
- **Branch:** `research/hybrid-wave3a-volume-reasoning`
- **Baseline `main`:** `1613e0d3ebe16f0f2fe4be755052491ff581e51b`
- **Round 1 Candidate:** Product `2e277e6ec6b87a1e64bfc8c1c9127f591fedf24f` / Freeze `817b1730d5b3a61cd18b30348e32040337428841` (tree `99cef1a99038d8bf13ed6f9a2cc476fc315986650c4c038e30479d1212d18338`) — **`PASS_WITH_FINDINGS`** (`0 BLOCKER`, `1 IMPORTANT`, `2 MINOR`)
- **Round 2 Final Candidate:** Product `4c282ecd9f15b14ddbbe6e0be0b247e455d8edca` / Freeze `0a4b6d7027624849b53b5d79a78dd6f2116cffcd` (tree `df262376b3f2de7bcb0c295932c7c867a7ee2bf268ed9408071e5953ee9fc821`, 112 files) — **`INDEPENDENT_REVIEW_PASS`** (`0 BLOCKER`, `0 IMPORTANT`, `0 MINOR`)

---

## 1. Audited Scope

1. **Contract & Surface Fingerprint Invariance:**
   - Verified `TypedFact.model_json_schema()` SHA-256 (`aa9d93eeac9f1659af8e5acd42af1904b7aaed674a8ab0f56f0c7dd8b2ad4ee8`), `surface_fingerprint("flat")` (`485d3834db8b18cfdb24143bfbb14deb8f5b7a9d74cb612d48db8c08252e507a`), `surface_fingerprint("v3")` (`4bff35bbf690a9973b2b7834019b908d507bbbb4277928e36d12dcff657e226f`), `function_calling.surface_fingerprint()` (`7ea511a6e3828c9adcc8402aa2d7d6b1d433e67a01ec4329c3009c46af652b25`), `registry.function_declarations()` SHA-256 (`5ceb0f999d4d7c1ee37c02207ea6470a7f972a168d6c52fa597392934d86f169`), and `ADAPTER_VERSION = "hybrid-preview-adapter/2"` remain byte-identical to `main`.
2. **Registry & Source Gate (`registry.py`):**
   - Verified ordered ratio operand binding (`_ten_khoi_khop`), ordered residual operand binding (`_ds_khoi_khop`), dimensionless unit rejection on `"ratio"` (`QUESTION_CONTEXT_UNSUPPORTED`), and distinct solid enforcement (`AskVolumeRatioArgs._check_distinct_solids`).
3. **Planner Lowering & Dependency Ordering (`planner.py`):**
   - Verified `_khoi_tu_toan_hang`, `_cau_hoi`, `_NON_POINT_ARG_KEYS`, and `_sap_xep_phu_thuoc_loi_goi` (`Tier 5` ordering after all solid construction calls and vertex producers).
4. **Engine Mathematical Proofs (`engine.py`):**
   - **Exact Squared Volume (`_the_tich2_khoi`):** Verified Gram base area squared $\times$ altitude squared $/ 9$ (pyramid) or $/ 1$ (prism) after `kiem_mat_phang_don` face planarity and simplicity verification.
   - **`VolumeRatioCertificate` (`certify_volume_ratio`):** Verified exact rational square-root check `_sqrt_q(v2_num / v2_den)` (`UNSUPPORTED_VOLUME_RATIO` on irrational/non-positive ratios) and post-execution interpreter cross-check (`ENGINE_SELF_CHECK_FAILED` on any discrepancy).
   - **`ResidualVolumeCertificate` (`certify_residual_volume`):**
     - **Strict Convexity & Outward Half-Spaces (`_mat_ngoai_khoi`):** Verified outward face normals $(n_F, d_F)$ require all off-face vertices $q$ to satisfy $n_F \cdot q - d_F < 0$, rejecting non-convex or degenerate faces with `DEGENERATE_SOLID`.
     - **Containment (`CONTAINMENT_VERIFIED`):** Every vertex $u$ of every subtracted solid satisfies $n_F \cdot u - d_F \le 0$ for all faces $F$ of `original_solid` (`RESIDUAL_CONTAINMENT_UNPROVED` otherwise).
     - **Shared Boundary (`SHARED_BOUNDARY_VERIFIED`):** Every subtracted solid has at least 1 boundary face ($\ge 3$ non-collinear vertices) lying on a boundary plane $n_F \cdot u - d_F = 0$ of `original_solid` (`RESIDUAL_CONTAINMENT_UNPROVED` otherwise).
     - **Disjoint Interiors (`DISJOINT_INTERIORS_VERIFIED`):** Exact 3D Separating Axis Theorem (SAT) over all face normals of $\text{sub}_i$, all face normals of $\text{sub}_j$, and all non-zero edge-pair cross products $e_a \times e_b$ (`OVERLAPPING_SUBTRACTED_SOLIDS` otherwise).
     - **Positive Residual (`POSITIVE_RESIDUAL_VERIFIED`):** Exact rational ratio compatibility $\alpha_i = \sqrt{V^2(\text{sub}_i)/V^2(\text{orig})} \in \mathbb{Q}_{>0}$ and $1 - \sum_i \alpha_i > 0$ (`NON_POSITIVE_RESIDUAL_VOLUME` otherwise), cross-checked post-execution against `final_memory`.
5. **Interpreter, Scene3D Pedagogy & Preview Plumbing (`interpreter.py`, `simulation_state.py`, `display_names.py`, `hybrid_preview.py`):**
   - Verified `Radical` arithmetic (`+`, `-`, `*`), `parse_exact` rational string literals, `"assign.volume_ratio"` / `"assign.residual_volume"` provenance validation, Vietnamese formulas (`"V(A)/V(B)"`, `"V(orig) - V(sub)"`), and absence of fabricated residual 3D solid meshes in `Scene3D.objects`.
6. **Independent Oracle & Corpus (`oracle.py`, `corpus-dev.json`, `dev-evaluation.json`, `regression-summary.json`):**
   - Verified `oracle.py` has 0 imports from `app`/`tests`/`backend`, 32/32 cases in `corpus-dev.json` match oracle (`18/18` positive, `20/20` goals, `14/14` negative refusals, `0` wrong serves), and `D:\Documents\AlgoSim-Research\BH2C` is untouched (`0` diffs).

---

## 2. Round 1 Findings & Round 2 Resolution

| ID | Severity | Finding in Round 1 (`817b1730`) | Resolution Verified in Round 2 (`0a4b6d70` / `4c282ecd`) |
|---|---|---|---|
| `IMPORTANT-01` | `IMPORTANT` | `AskVolumeRatioArgs`, `planner.py`, and `engine.py` allowed self-ratio (`numerator_solid == denominator_solid`), returning `"1"` instead of refusing as specified in `WAVE3A_CONTRACT_DECISION.md` §2. | Resolved: `AskVolumeRatioArgs._check_distinct_solids` (`registry.py:242-246`) rejects `numerator_solid == denominator_solid` (`SCHEMA_INVALID`), and `planner.py:900-901` + `engine.py:826-827` reject `kh_a.ten == kh_b.ten` (`UNSUPPORTED_VOLUME_RATIO`). Verified by `test_self_ratio_and_duplicate_subtracted_solids_refused`. |
| `MINOR-01` | `MINOR` | Minor field/step/code name drift between `WAVE3A_CONTRACT_DECISION.md` and `planner.py`/`engine.py`. | Resolved: `docs/architecture/WAVE3A_CONTRACT_DECISION.md` and `docs/evaluation/geometry/runs/volume-reasoning/WAVE3A_CONTRACT_DECISION.md` synchronized with implemented field names, trace steps (`certify_volume_ratio`, `certify_residual_volume`), refusal codes, and outward normal convention. |
| `MINOR-02` | `MINOR` | Documentation note on `AskResidualVolumeArgs.subtracted_solids` length bound (`1 <= len <= 2`). | Resolved: `WAVE3A_CONTRACT_DECISION.md` and `AskResidualVolumeArgs` (`Field(min_length=1, max_length=2)`) are completely aligned. |

---

## 3. Final Verdict

**`INDEPENDENT_REVIEW_PASS`** (`0 BLOCKER`, `0 IMPORTANT`, `0 MINOR`) on candidate commit `0a4b6d7027624849b53b5d79a78dd6f2116cffcd` (product commit `4c282ecd9f15b14ddbbe6e0be0b247e455d8edca`, measured tree `df262376b3f2de7bcb0c295932c7c867a7ee2bf268ed9408071e5953ee9fc821`).
