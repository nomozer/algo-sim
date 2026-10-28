# Independent Post-Run Evaluation Audit — `hybrid-v2-independent-vietnamese-section-holdout-wave2`

- **Task:** `HYBRID_V2_INDEPENDENT_VIETNAMESE_SECTION_HOLDOUT_WAVE2` (Owner GO 2026-10-27)
- **Reviewer Role:** Independent Holdout Wave 2 Oracle & Evaluation Reviewer
- **Authoritative Baseline (`main = origin/main = GitHub remote`):** `d7a94d3cd4bbdea3df99e383bec78425fcc8bf1c`
- **Product Commit:** `e3678608f1f7110d7046c9c43c312c69d7614f55` (T3 candidate `e7bcff316ee6d443e753105a887e0689ea04848b`)
- **Pre-Registration Commit:** `5e329d759af675fdc3a7393c9479bfacd636460f`
- **Pre-Execution Freeze Commit:** `7e5c3ddde78710f4ea174956302d11e711b51635`
- **Measured System:** `118` product files, `measured_system.tree_hash = 84ccf653441d1bd54f352756b9a5e917ee02a9ea11a83ac60585dfc585f3f99f`
- **Live Provider Calls:** `0` (`ALLOW_LIVE_AI = 0`)
- **Review Verdict:** `INDEPENDENT_HOLDOUT_WAVE2_REVIEW_PASS`

---

## 1. Product Freeze & Manifest Integrity Verification

### 1.1 Product Candidate Freeze Check
Executed `python backend/scripts/freeze_evaluation_candidate.py --verify`:
- **Status:** `MATCH` (`Candidate khớp bản đã đóng băng (mã sản phẩm: 118 file, 84ccf653441d1bd5…).`)
- **Measured Product File Count:** `118`
- **Measured Product Tree Hash:** `84ccf653441d1bd54f352756b9a5e917ee02a9ea11a83ac60585dfc585f3f99f`
- **Component Versions:** Registry `geometry-functions/18`, Planner `geometry-fact-planner/17`, Engine `geometry-function-engine/14`, Adapter `hybrid-simulation-adapter/4`, Certificate `plane-section-certificate/1`, `CACHE_VERSION = 130`, `DEFAULT_MODE = LLM_ONLY`.
- Zero product files were modified during or after the Holdout Wave 2 evaluation.

### 1.2 Pre-Execution Manifest & Corpus/Oracle Immutability Check
Verified `holdout-manifest.json` against the pre-execution freeze commit `7e5c3ddde78710f4ea174956302d11e711b51635`:
- `git diff 7e5c3ddde78710f4ea174956302d11e711b51635 -- docs/evaluation/geometry/runs/hybrid-v2-independent-vietnamese-section-holdout-wave2/holdout-manifest.json` is empty (`0` bytes changed).
- All **17** preregistration, contract, provenance, corpus, oracle, taxonomy, and pre-freeze audit files remain byte-identical to their frozen SHA-256 hashes at `7e5c3ddde78710f4ea174956302d11e711b51635`:

| File | Frozen Bytes | Frozen & Post-Run SHA-256 | Status |
|---|---:|---|---|
| `plan.md` | 4,817 | `51f9a426ffbe027b8b907e3d7366e208a93953a91a0c6eafc27a8222bc7ae037` | `MATCH` |
| `preregistration.md` | 15,810 | `2864c2f111c1afb0e24265601ecfbfb6aa0e7ff286714eef45ef33d9e4faa5b4` | `MATCH` |
| `supported-family-matrix.md` | 7,717 | `ea4c4c3f5a87f9325112d8c29ac42af8070c171bd35dc0da1c8c85698caca542` | `MATCH` |
| `scoring-contract.md` | 8,978 | `88b32f56df396acc0e1b3d70cd94621db19063b9105451ac817b2375274719df` | `MATCH` |
| `curator-brief.md` | 11,252 | `9dd31c18cd4ee205d3904a39192e3d7b19d9e82b8f0d194b0ecb24b65913aa7c` | `MATCH` |
| `curator-attestation.md` | 6,719 | `dd1a2dee3eba7601d1fbab2d2aa625f7bf12a0db1673a5be5354867b32aeda9e` | `MATCH` |
| `corpus-provenance.md` | 19,304 | `90ce7aa3fd39191db5802caf72ae10ddc70ad2e2a679b1769a256eab6d88d70d` | `MATCH` |
| `inputs/holdout-wave2.json` | 471,848 | `1104be2ad8d4c5c96363f3648bc3c57dfcef5af4334c714e9cc94fc466f38e2d` | `MATCH` |
| `oracle/geometry.json` | 148,844 | `dcee137a2a10bad499401bd3b45b4c9cc530d9e0ebf51fe669a7ab3bf7ae8d33` | `MATCH` |
| `oracle/oracle_holdout_wave2.py` | 20,871 | `5511dd0e7dbfb854dcdda4f523c2cd0dd3f52ab22c5851769f7424b243d897d8` | `MATCH` |
| `oracle/expected.json` | 28,976 | `5efbe57de91c31e18995e679ae6f0ecd69c366ea6bf148ee96255d4cfae7c844` | `MATCH` |
| `tools/refusal_taxonomy.json` | 4,962 | `a30ebeae583275ca7b3bff809ca93193e0b11f961c9c8c667a681e1f8190e5d8` | `MATCH` |
| `tools/audit_curator_log.py` | 6,606 | `34c430be83a2aeef5e00716a31f5ca1a3465229ad375b60f1ba45ed3ffe41a22` | `MATCH` |
| `tools/dedup_check_wave2.py` | 17,690 | `ada310bde4754112273d6de39593508915b6a2cc65b9ec9dea4d68f65cc51849` | `MATCH` |
| `results/independence-audit.json` | 4,277 | `3fa99f0aed29710e8fc9d0d3f4a67f80a5927bc86d98a979cc5141f991e480c9` | `MATCH` |
| `results/deduplication-audit.json` | 833 | `f256fcfc96a20916617c992ec287189818b8d0c4cd7feb69708f1d4a3d389535` | `MATCH` |
| `results/independent-oracle-review-48.json` | 71,125 | `373e7094f20d2f2ce95ba2aa934307c7b1a693d5e9de56686aa8b6066e697c12` | `MATCH` |

### 1.3 Preservation of `results/scored-run-1/`
Verified that all 3 output artifacts in `results/scored-run-1/` are preserved untouched and match `raw_scored_run_hashes` in `results/harness-adjudication-receipt.json`:
- `results/scored-run-1/track-a.json`: `eea9c5d88265bedaeccff06dc059ef39d60496d923f0c7a1426c4fa867c1e3eb` (`MATCH`)
- `results/scored-run-1/summary.json`: `7287aee2a166afc030ec68e69107762cbe636e0d13674d101740312667c7a512` (`MATCH`)
- `results/scored-run-1/track-b.json`: `53fee45e31b19ee5a25993412d7674e7c05ad2f9a01ee9df315d64f2a31748b8` (`MATCH`)

---

## 2. Independent Audit of `results/scored-run-1/`, `results/harness-adjudication-receipt.json`, and `results/scored-run-2-harness-corrected/`

### 2.1 Verification of Scorer Harness Defect in `scored-run-1` (`W2-A01` and `W2-A03`)
1. **Pre-Correction Scorer Check (`tools/evaluate_holdout_wave2.py` at `7e5c3ddde78710f4ea174956302d11e711b51635`):**
   - Inspected lines 441–443 of `git show 7e5c3ddde78710f4ea174956302d11e711b51635:.../tools/evaluate_holdout_wave2.py`:
     ```python
     cert = sec.get("closure_certificate")
     if not isinstance(cert, dict) or cert.get("verified") is not True or not cert.get("rule"):
         checks.append("missing or unverified section closure_certificate")
     ```
   - This check ran unconditionally on **all** sections before branching on `is_cat_b` (`ENGINE_DERIVED_SECTION` vs. `DINH_CAT_CANH`).
2. **Product Architecture Verification (`adapter4_route.py` and `engine.py`):**
   - In `backend/app/simulation/geometry_functions/engine.py` (`kiem_dinh_cat`, lines 1420–1435), Category A (`DINH_CAT_CANH`) populates `d["closure"]` only when `d.get("declared_boundary") is not None` or `d.get("derived")` (a derived pyramid standing on the section) is present.
   - In `backend/app/ai/adapter4_route.py` (`_phong_bi`, line 78), `closure_certificate` is set to `d.get("closure")`.
   - In `backend/app/ai/adapter4_route.py` (`_validate_sections`, lines 280–288), single-solid Category A sections with `boundary is None and cert is None` are explicitly valid by design and are certified via `section["vertices"]` (`label`, `edge`, `provenance`, `stated`) and `scene3d` polygon/vertex-source checks (lines 255–279).
   - Therefore, marking `W2-A01` and `W2-A03` as `WRONG_SERVED` in `results/scored-run-1/` with `oracle_mismatches = ["missing or unverified section closure_certificate"]` was a genuine scorer harness defect, not a product defect.
   - The protocol in `preregistration.md` Section 9 was followed strictly: `results/scored-run-1/` was preserved byte-identically, `results/harness-adjudication-receipt.json` documented the pre/post hashes (`1a053c4ef4caaa22f2618d6d89e34adf9d024cd35f2d77c4c01759af3c96aa44` $\rightarrow$ `e9c36a177c2f43cb8af59f361a78421b6f253a5c642e980ad98939793ae51e12`), and the corrected run was written to `results/scored-run-2-harness-corrected/`.

### 2.2 Independent Verification of All 5 Served Positive Cases (`5/5` = `100%` Agreement)
Cross-checked all 5 served positive cases against the independent exact-`Fraction` oracle (`results/independent-oracle-review-48.json`):

| Case ID | Stratum | Family | Solid | Cert Category | Vertex Count (Prod / Oracle) | Canonical Boundary Cycle Match | `area_squared` (Prod / Oracle) | Outcome (`run-1` $\rightarrow$ `run-2`) |
|---|---|---|---|---|---:|---|---|---|
| `W2-B08` | `P-B` | `quadrilateral_pyramid` | `S.MNPQ` | `ENGINE_DERIVED_SECTION` | `4 / 4` | `True` (`M`, `SQ@1/2`, `SP@1/3`, `SN@1/2`) | `2187/4` / `2187/4` | `SERVED_CORRECT` $\rightarrow$ `SERVED_CORRECT` |
| `W2-B12` | `P-B` | `quadrilateral_pyramid` | `S.ABCD` | `ENGINE_DERIVED_SECTION` | `4 / 4` | `True` (`SB@1/2`, `AB@1/2`, `CD@1/2`, `SC@1/2`) | `53361/64` / `53361/64` (cert) | `SERVED_CORRECT` $\rightarrow$ `SERVED_CORRECT` |
| `W2-B14` | `P-B` | `right_triangular_prism` | `MNP.M'N'P'` | `ENGINE_DERIVED_SECTION` | `4 / 4` | `True` (`MN@1/2`, `NP@1/2`, `N'P'@1/2`, `M'N'@1/2`) | `20449/4` / `20449/4` (cert) | `SERVED_CORRECT` $\rightarrow$ `SERVED_CORRECT` |
| `W2-A01` | `P-A` | `triangular_pyramid` | `S.ABC` | `DINH_CAT_CANH` | `3 / 3` | `True` (`A`, `SC@1/3`, `SB@1/2`) | `2401/48` (section_only) | `WRONG_SERVED` $\rightarrow$ `SERVED_CORRECT` |
| `W2-A03` | `P-A` | `triangular_pyramid` | `S.MNP` | `DINH_CAT_CANH` | `3 / 3` | `True` (`SM@1/2`, `SP@1/2`, `SN@1/2`) | `1225/4` / `1225/4` (`mg1 = 35/2`) | `WRONG_SERVED` $\rightarrow$ `SERVED_CORRECT` |

All `5/5` (`100.0%`) served positive cases exhibit exact mathematical, topological, solid-identity, vertex-provenance, and `area_squared` agreement with the independent oracle (`0` mismatches).

### 2.3 Verification of Headline Outcome Counts (`scored-run-1` vs. `scored-run-2-harness-corrected`)

| Metric | `results/scored-run-1/` (Raw) | `results/scored-run-2-harness-corrected/` (Corrected) | Verified |
|---|---:|---:|---|
| Total Cases (`n`) | `96` | `96` | `PASS` |
| Positive (`SERVE`) Cases | `48` | `48` | `PASS` |
| `SERVED_CORRECT` | `3 / 48` (`6.25%`, 95% CI `[2.15%, 16.84%]`) | `5 / 48` (`10.42%`, 95% CI `[4.53%, 22.17%]`) | `PASS` |
| `FALSE_REFUSAL` | `43 / 48` (`89.58%`, 95% CI `[77.83%, 95.47%]`) | `43 / 48` (`89.58%`, 95% CI `[77.83%, 95.47%]`) | `PASS` |
| `WRONG_SERVED` on `SERVE` | `2 / 48` (`W2-A01`, `W2-A03` harness false-alarm) | `0 / 48` (`0.00%`) | `PASS` |
| Negative (`REFUSE`) Cases | `48` | `48` | `PASS` |
| `REFUSE` Cases Refused | `48 / 48` (`100.00%`, 95% CI `[92.59%, 100.00%]`) | `48 / 48` (`100.00%`, 95% CI `[92.59%, 100.00%]`) | `PASS` |
| `REFUSED_CORRECT_REASON` | `33 / 48` (`68.75%`, 95% CI `[54.67%, 80.05%]`) | `33 / 48` (`68.75%`, 95% CI `[54.67%, 80.05%]`) | `PASS` |
| `REFUSED_REASON_DISAGREEMENT` | `15 / 48` (`31.25%`) | `15 / 48` (`31.25%`) | `PASS` |
| `WRONG_SERVED` Total | `2 / 96` | `0 / 96` (`0.00%`, 95% CI `[0.00%, 3.85%]`) | `PASS` |
| `HARNESS_ERROR` | `0` | `0` | `PASS` |
| `PRODUCT_EXCEPTION` (`internal_exceptions`) | `0` | `0` | `PASS` |

---

## 3. Independent Audit of Diagnostic Findings (`results/diagnostics.json` & `results/analysis.json`)

### 3.1 Positive False-Refusal Mechanism Partition (`43` Cases Across `W2-M1..W2-M5`)
Independently verified that the 43 positive false refusals partition cleanly and mutually exclusively by first-failure mechanism (`23 + 5 + 12 + 1 + 2 = 43`, disjoint from the 5 served cases, totaling `48` positive cases), and verified each mechanism directly in the product source code:

1. **`W2-M1` (`23` first-refusal cases, `39` total affected): Inverted Vietnamese `divide_segment` syntax (`"Trên cạnh XY lấy điểm P sao cho ..."`):**
   - **Code Location Verified:** `backend/app/simulation/geometry_functions/registry.py` line 4310 (`_TY_SO`) and line 4362 (`construction_source_bound`).
   - **Finding:** `_TY_SO` requires the point label `(?P<p>[A-Z][0-9]*'?)` at the start of the clause before `thuộc|nằm trên|trên` and rejects standard inverted Vietnamese phrasing `"Trên cạnh SA lấy điểm M sao cho SM = 2/7 SA."` with `SOURCE_OBJECT_MISMATCH` (`"vai trò điểm và toán hạng dựng không khớp nguồn"`).
   - **23 First-Refusal Cases:** `W2-B01`, `W2-B02`, `W2-B03`, `W2-B04`, `W2-B07`, `W2-B09`, `W2-B10`, `W2-B13`, `W2-B15`, `W2-B16`, `W2-B25`, `W2-B26`, `W2-B27`, `W2-B28`, `W2-B31`, `W2-B32`, `W2-B33`, `W2-B34`, `W2-A02`, `W2-A05`, `W2-A08`, `W2-A11`, `W2-A12`.

2. **`W2-M2` (`5` first-refusal cases, `7` total affected): Orthogonal projection target noun `"đỉnh"` (`"trùng với đỉnh B"`):**
   - **Code Location Verified:** `backend/app/simulation/geometry_functions/registry.py` line 4381 (`construction_source_bound`).
   - **Finding:** The second pattern in `construction_source_bound` allows `(?:(?:điểm|đỉnh)\s+)?` before the projected source point (`src`), but allows only `(?:điểm\s+|trọng tâm\s+|trung điểm\s+)?` (omitting `đỉnh\s+`) before the image point (`out`), rejecting `"hình chiếu vuông góc của A' trên mặt phẳng (ABC) trùng với đỉnh B"` with `SOURCE_OBJECT_MISMATCH` (`"vai trò ảnh và điểm chiếu không khớp nguồn"`).
   - **5 First-Refusal Cases:** `W2-B19`, `W2-B20`, `W2-B21`, `W2-B22`, `W2-A09` (plus secondary co-occurrence on `W2-B23`, `W2-B24`).

3. **`W2-M3` (`12` first-refusal cases): `MAT_HAI_DUONG` (`parallel_two_lines`) standalone premise guard omits `divide_segment` and oblique `lăng trụ`:**
   - **Code Location Verified:** `backend/app/simulation/geometry_functions/registry.py` lines 4647–4659 (`atomic_forms`).
   - **Finding:** When `MAT_HAI_DUONG` is present in the plan, the standalone premise guard checks every premise quote against `atomic_forms`, which includes only `pyramid`, `regular_pyramid`, `prism` (`lăng trụ đứng|hình hộp chữ nhật`), `regular_polygon`, `rectangle`, and `midpoint`, rejecting standalone `divide_segment` quotes and oblique prism quotes with `SOURCE_PREMISE_UNREAD` (`"quote tiền đề chưa nằm trọn trong văn phạm lát hai đường"`).
   - **12 First-Refusal Cases:** `W2-B05`, `W2-B06`, `W2-B11`, `W2-B17`, `W2-B18`, `W2-B23`, `W2-B24`, `W2-B29`, `W2-B30`, `W2-B35`, `W2-B36`, `W2-A06`.

4. **`W2-M4` (`1` first-refusal case: `W2-A04`): Exact radical radicand ceiling `MAX_RADICAND = 10**12` exceeded before squarefree reduction:**
   - **Code Location Verified:** `backend/app/simulation/geometry/radical.py` lines 103 and 214 (`MAX_RADICAND = 10**12` in `radical()`).
   - **Finding:** In `W2-A04` (`S.ABCD` with rectangle base $6 \times 8$ and $SA = 10$, cut by plane through $A$ perpendicular to $SC$), intermediate radical multiplication produces `can = 122970403125000` ($> 10^{12}$) before squarefree reduction, raising `RadicalDomainError` and refusing with `ENGINE_EXECUTION_FAILED` (`subcode = "RADICAL_DOMAIN_OVERFLOW"`).

5. **`W2-M5` (`2` first-refusal cases: `W2-A07`, `W2-A10`): Adapter `/4` Category A `_validate_sections` raw primed vertex lookup (`"A'"` vs. `"A_prime"`):**
   - **Code Location Verified:** `backend/app/ai/adapter4_route.py` line 261 (`point = objects[vertex["label"]]` inside `_validate_sections`).
   - **Finding:** Both `W2-A07` and `W2-A10` succeed through Bridge `/2`, Planner `/17`, Source Gate `/18`, and Engine `/14` (`r.status == "SERVED"`), with `THROUGH_POINT_REUSE` on primed prism vertex `"A'"`. In `_validate_sections`, Category A looks up `objects[vertex["label"]]` using raw `"A'"` instead of `ir_name("A'") == "A_prime"` (unlike Category B `_validate_engine_derived_section` which resolves via notation/ir_name), raising `KeyError: "A'"` caught by `build_adapter4_response` and returning `PREVIEW_VALIDATION_FAILED`.

### 3.2 Scene3D Learner-Facing Semantics Separation (Track 10.A vs. Track 10.B)
Verified across all 5 served cases (`W2-B08`, `W2-B12`, `W2-B14`, `W2-A01`, `W2-A03`):
- **Track 10.A (`source_identity_leaks`):** `[]` (`0/5` cases have any source-identity leak; no synthesized auxiliary identifier has `origin == "given"`, none appears in any `section`, `plane3`, `solid`, or `quantity` name/label/notation, and `identity_diagnostics` is empty).
- **Track 10.B (`pedagogical_auxiliary_display`):** `r2_auxiliary_notation_observed = True` on `5/5` served cases (`R2_AUXILIARY_POINT_NOTATION_DEFERRED`), and `all_auxiliary_visibly_distinguished = True` across all `5/5` served cases (all auxiliary construction points carry `origin == "derived"` and descriptive derived roles such as `"Điểm dựng phụ"`, `"Hình chiếu của ..."`, or `"Ảnh của ... qua phép tịnh tiến ..."`).

---

## 4. Signed Independent Review Verdict

- **Pre-Freeze 48-Case Exact Oracle Verification:** `48/48` (`100.0%`) exact agreement (`0` discrepancies).
- **Product Candidate & Manifest Freeze Integrity:** `PASS` (`118` product files, tree hash `84ccf653441d1bd54f352756b9a5e917ee02a9ea11a83ac60585dfc585f3f99f`; `17/17` non-harness frozen files byte-identical to `7e5c3ddde78710f4ea174956302d11e711b51635`; `results/scored-run-1/` preserved untouched).
- **Harness Adjudication & Post-Run Scoring Integrity:** `PASS` (`5/48` `SERVED_CORRECT`, `43/48` `FALSE_REFUSAL`, `0/96` `WRONG_SERVED`, `48/48` `REFUSE` cases refused, `33/48` `REFUSED_CORRECT_REASON`, `15/48` `REFUSED_REASON_DISAGREEMENT`, `0` `HARNESS_ERROR`, `0` `PRODUCT_EXCEPTION`; `5/5` served cases in `100.0%` exact oracle agreement).
- **Final Verdict:** **`INDEPENDENT_HOLDOUT_WAVE2_REVIEW_PASS`**
