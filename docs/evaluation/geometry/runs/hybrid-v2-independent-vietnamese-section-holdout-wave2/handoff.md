# Handoff — Hybrid V2 Independent Vietnamese Section Holdout Wave 2 (`hybrid-v2-independent-vietnamese-section-holdout-wave2`)

---

## 1. Final Status

- **Final Status:** `INDEPENDENT_HOLDOUT_EXECUTED`
- **Independent Reviewer Verdict (`review.md`):** `INDEPENDENT_HOLDOUT_WAVE2_REVIEW_PASS`
- **Curator Independence Verdict (`results/independence-audit.json`):** `HOLDOUT_INDEPENDENCE_ESTABLISHED`
- **Live Provider Calls (`ALLOW_LIVE_AI`):** `0` (`ALLOW_LIVE_AI=0`)
- **Product Modifications:** `0` (`freeze_evaluation_candidate.py --verify` = `MATCH`)
- **Merge / Push / Worktree Cleanup Performed:** `NONE` (awaiting Owner review)

---

## 2. Baseline Commit & Frozen Product Hash

- **Authoritative Baseline (`main = origin/main = GitHub remote`):** `d7a94d3cd4bbdea3df99e383bec78425fcc8bf1c`
- **Product Commit:** `e3678608f1f7110d7046c9c43c312c69d7614f55`
- **Frozen Full T3 Candidate Commit:** `e7bcff316ee6d443e753105a887e0689ea04848b`
- **Evaluation Branch:** `research/hybrid-v2-independent-vietnamese-section-holdout-wave2`
- **Evaluation Worktree:** `.superpowers/worktrees/independent-section-holdout-wave2`
- **Measured Product System (`freeze_evaluation_candidate.py --verify`):**
  - Status: `MATCH`
  - Product file count: `118`
  - `measured_system.tree_hash`: `84ccf653441d1bd54f352756b9a5e917ee02a9ea11a83ac60585dfc585f3f99f`
- **Component Versions:**
  - `REGISTRY_VERSION`: `geometry-functions/18`
  - `PLANNER_VERSION`: `geometry-fact-planner/17`
  - `ENGINE_VERSION`: `geometry-function-engine/14`
  - `ADAPTER_V4_VERSION`: `hybrid-simulation-adapter/4`
  - `PLANE_SECTION_CERTIFICATE_VERSION`: `plane-section-certificate/1`
  - `CACHE_VERSION`: `130`
  - `DEFAULT_MODE`: `LLM_ONLY` (Hybrid V2 opt-in only)

---

## 3. Preregistration Commit & Pre-Execution Freeze Commit

- **Preregistration & Scorer Self-Tests Commit (Before Corpus Generation):** `5e329d759af675fdc3a7393c9479bfacd636460f`
  - Committed `plan.md`, `preregistration.md`, `supported-family-matrix.md`, `scoring-contract.md`, `curator-brief.md`, `tools/refusal_taxonomy.json`, `tools/evaluate_holdout_wave2.py`, and `tools/test_evaluate_holdout_wave2.py` (`18/18` synthetic controls passing before the curator was spawned).
- **Pre-Execution Corpus, Oracle & Manifest Freeze Commit (Before Scored Run):** `7e5c3ddde78710f4ea174956302d11e711b51635`
  - Committed `inputs/holdout-wave2.json`, `oracle/geometry.json`, `oracle/oracle_holdout_wave2.py`, `oracle/expected.json`, `curator-attestation.md`, `corpus-provenance.md`, `tools/dedup_check_wave2.py`, `tools/audit_curator_log.py`, `results/deduplication-audit.json`, `results/independence-audit.json`, `results/independent-oracle-review-48.json`, and `holdout-manifest.json` (`19` frozen files verified prior to running `scored-run-1`).

---

## 4. Curator Independence Audit & Semantic Deduplication Result

- **Curator Subagent:** `317d3ae6-3a79-4d40-976e-f528d0124b31` (`Independent Holdout Wave 2 Curator`)
- **Transcript Audit (`results/independence-audit.json`):**
  - Status: `HOLDOUT_INDEPENDENCE_ESTABLISHED`
  - Total tool calls audited: `80`
  - Forbidden reads (`registry.py`, `planner.py`, `engine.py`, `adapter4_route.py`, `typed_fact_next_bridge.py`, `backend/tests/**`, historical evaluation runs): `0`
  - Forbidden product execution commands: `0`
- **9-Dimensional Semantic Deduplication (`results/deduplication-audit.json`):**
  - Historical items compared: `654` (`84` Wave 1 holdout cases, `32` M1–M5 development cases, all historical evaluation runs, and `backend/tests/**`)
  - External text similarity flags ($\ge 0.70$): `0` (`max_external_5gram_jaccard = 0.6372`)
  - External exact 8D configuration matches: `0`
  - External scale-invariant configuration matches: `0`
  - Internal duplicate flags: `0`
- **Independent Pre-Freeze Oracle Audit (`results/independent-oracle-review-48.json`):**
  - Reviewer Subagent: `9b55a8a4-4834-4cbb-b8bc-aec696ad8026` (`Independent Holdout Wave 2 Oracle & Evaluation Reviewer`)
  - Verified all `48 / 48` positive oracle cases (`W2-B01..W2-B36`, `W2-A01..W2-A12`) in independent `fractions.Fraction` arithmetic: `48 / 48` exact agreement (`0` discrepancies).

---

## 5. Corpus Counts by Stratum, Family, Plane Relation, Question Type & Negative Class

- **Total Cases:** `96` (`48` positive `SERVE`, `48` negative/adversarial `REFUSE`)
- **By Stratum:**
  - `P-B` (Supported Category B Engine-Derived): `36` (`6` solid families $\times$ `3` plane relations $\times$ `2` cases per cell; balanced `12` `section_only`, `12` `area_only`, `12` `section_and_area`)
  - `P-A` (Supported Category A Stated Intersections): `12` (`2` per supported solid family; balanced `4` `section_only`, `4` `area_only`, `4` `section_and_area`; includes solid-vertex reuse, genuine interior cuts, named and unnamed intersections, and exact cut ratios)
  - `N` (Negative / Adversarial): `48` (`16` adversarial classes $\times$ `3` cases per class)
- **By Solid Family (`96` cases):**
  - `triangular_pyramid`: `26` (`9` `SERVE`, `17` `REFUSE`)
  - `quadrilateral_pyramid`: `24` (`9` `SERVE`, `15` `REFUSE`)
  - `right_triangular_prism`: `14` (`8` `SERVE`, `6` `REFUSE`)
  - `oblique_triangular_prism`: `9` (`7` `SERVE`, `2` `REFUSE`)
  - `cuboid`: `12` (`8` `SERVE`, `4` `REFUSE`)
  - `cube`: `9` (`7` `SERVE`, `2` `REFUSE`)
  - `unsupported_solid`: `2` (`0` `SERVE`, `2` `REFUSE`)
- **By Plane Relation (`96` cases):**
  - `perpendicular_line`: `27` (`12` `SERVE`, `15` `REFUSE`)
  - `parallel_plane`: `35` (`12` `SERVE`, `23` `REFUSE`)
  - `parallel_two_lines`: `19` (`12` `SERVE`, `7` `REFUSE`)
  - `stated_intersections`: `15` (`12` `SERVE`, `3` `REFUSE`)
- **By Question Type (`96` cases):**
  - `section_only`: `48` (`16` `SERVE`, `32` `REFUSE`)
  - `area_only`: `29` (`16` `SERVE`, `13` `REFUSE`)
  - `section_and_area`: `16` (`16` `SERVE`, `0` `REFUSE`)
  - `other_metric`: `3` (`0` `SERVE`, `3` `REFUSE`)

---

## 6. Track A & Track B Headline Results (Side-by-Side Raw vs. Harness-Corrected)

| Metric | Raw `results/scored-run-1/` (`k / n`, `%`, 95% Wilson CI) | Harness-Corrected `results/scored-run-2-harness-corrected/` (`k / n`, `%`, 95% Wilson CI) |
|---|---|---|
| **Positive `SERVED_CORRECT` (`n = 48`)** | `3 / 48` (`6.25%`, `[0.0215, 0.1684]`) | **`5 / 48` (`10.42%`, `[0.0453, 0.2217]`)** |
| **Category B `SERVED_CORRECT` (`n = 36`)** | `3 / 36` (`8.33%`, `[0.0287, 0.2183]`) | **`3 / 36` (`8.33%`, `[0.0287, 0.2183]`)** |
| **Category A `SERVED_CORRECT` (`n = 12`)** | `0 / 12` (`0.00%`, `[0.0000, 0.2425]`) | **`2 / 12` (`16.67%`, `[0.0470, 0.4480]`)** |
| **Positive `FALSE_REFUSAL` (`n = 48`)** | `43 / 48` (`89.58%`, `[0.7783, 0.9547]`) | **`43 / 48` (`89.58%`, `[0.7783, 0.9547]`)** |
| **Positive `WRONG_SERVED` (`n = 48`)** | `2 / 48` (`4.17%`, `[0.0115, 0.1398]`) (`W2-A01`, `W2-A03`) | **`0 / 48` (`0.00%`, `[0.0000, 0.0741]`)** |
| **Negative `REFUSE` Cases Refused (`n = 48`)** | `48 / 48` (`100.00%`, `[0.9259, 1.0000]`) | **`48 / 48` (`100.00%`, `[0.9259, 1.0000]`)** |
| **Negative `WRONG_SERVED` (`n = 48`)** | `0 / 48` (`0.00%`, `[0.0000, 0.0741]`) | **`0 / 48` (`0.00%`, `[0.0000, 0.0741]`)** |
| **Negative `REFUSED_CORRECT_REASON` (`n = 48`)** | `33 / 48` (`68.75%`, `[0.5467, 0.8005]`) | **`33 / 48` (`68.75%`, `[0.5467, 0.8005]`)** |
| **Negative `REFUSED_REASON_DISAGREEMENT` (`n = 48`)** | `15 / 48` (`31.25%`, `[0.1995, 0.4533]`) | **`15 / 48` (`31.25%`, `[0.1995, 0.4533]`)** |
| **Total `WRONG_SERVED` (`n = 96`)** | `2 / 96` (`2.08%`, `[0.0057, 0.0728]`) | **`0 / 96` (`0.00%`, `[0.0000, 0.0385]`)** |
| **`PRODUCT_EXCEPTION` / `HARNESS_ERROR`** | `0` / `0` | **`0` / `0`** |

- **Track B Representability (`results/scored-run-2-harness-corrected/track-b.json`):**
  - Positive (`SERVE`, `48`): `48` `representable_without_loss`
  - Negative (`REFUSE`, `48`): `27` `representable_without_loss`, `9` `representable_with_explicit_gap`, `12` `intentionally_outside_v2`

---

## 7. Exact-Oracle Agreement Rate

- **Raw (`scored-run-1`):** `3 / 5` (`60.00%`) among Adapter `/4`-served positive cases (`W2-B08`, `W2-B12`, `W2-B14` passed; `W2-A01`, `W2-A03` flagged solely for `closure_certificate=None` by the pre-correction harness).
- **Harness-Corrected (`scored-run-2-harness-corrected`):** **`5 / 5` (`100.00%`, 95% Wilson CI `[0.5655, 1.0000]`)** exact oracle agreement across all 5 Adapter `/4`-served positive cases (`W2-B08`: `area_squared = "2187/4"`, `W2-B12`, `W2-B14`, `W2-A01`, `W2-A03`: `area_squared = "1225/4"`).
- **Route-Level (`run_typed_fact_next_v2_route`):** **`7 / 7` (`100.00%`)** exact oracle agreement across all 7 route-served positive cases (including `W2-A07` with `area_squared = "1875/8"` and `W2-A10`, which were refused in `Adapter /4` due to `W2-M5`).

---

## 8. Wrong-Served Count

- **Raw (`scored-run-1`):** `2 / 96` (`2 / 48` on `SERVE` cases `W2-A01` and `W2-A03` due to the Category A `closure_certificate=None` harness defect; `0 / 48` on `REFUSE` cases).
- **Harness-Corrected (`scored-run-2-harness-corrected`):** **`0 / 96` (`0.00%`, 95% Wilson CI `[0.0000, 0.0385]`)** across all 96 cases (`0 / 48` on `SERVE` cases and `0 / 48` on `REFUSE` cases).

---

## 9. False-Refusal Count & 5-Mechanism Root-Cause Breakdown

- **False-Refusal Count:** `43 / 48` (`89.58%`, 95% Wilson CI `[0.7783, 0.9547]`).
- **Mutually Exclusive First-Refusal Partition (`23 + 5 + 12 + 1 + 2 = 43`):**
  1. **`W2-M1` (`23` cases first-refused; `39 / 48` total co-occurrence):** Inverted Vietnamese `divide_segment` syntax (`"Trên cạnh SA lấy điểm M sao cho SM = 2/7 SA."`) rejected by `registry._TY_SO` (`registry.py:4310`) with `SOURCE_OBJECT_MISMATCH: vai trò điểm và toán hạng dựng không khớp nguồn`.
  2. **`W2-M2` (`5` cases first-refused; `7 / 48` total co-occurrence):** Orthogonal projection target noun `"đỉnh"` (`"hình chiếu vuông góc của A' trên mặt phẳng (ABC) trùng với đỉnh B"`) rejected by `registry.construction_source_bound` (`registry.py:4381`) with `SOURCE_OBJECT_MISMATCH: vai trò ảnh và điểm chiếu không khớp nguồn`.
  3. **`W2-M3` (`12` cases first-refused):** `MAT_HAI_DUONG` (`parallel_two_lines`) standalone premise guard `atomic_forms` (`registry.py:4647–4659`) omits `'divide_segment'` and oblique `'lăng trụ'`, rejecting with `SOURCE_PREMISE_UNREAD: quote tiền đề chưa nằm trọn trong văn phạm lát hai đường`.
  4. **`W2-M4` (`1` case first-refused, `W2-A04`):** Exact radical ceiling `MAX_RADICAND = 10**12` (`radical.py:103, 214`) exceeded (`122970403125000 > 10**12`) before squarefree reduction on quadrilateral pyramid `S.ABCD` (`AB=6, AD=8, SA=10` cut perpendicular to `SC`), rejecting with `ENGINE_EXECUTION_FAILED` (`subcode = RADICAL_DOMAIN_OVERFLOW`).
  5. **`W2-M5` (`2` cases first-refused at `Adapter /4`, `W2-A07` and `W2-A10`):** Category A (`DINH_CAT_CANH`) validation in `adapter4_route._validate_sections` (`adapter4_route.py:261`) looks up `objects[vertex["label"]]` with raw `"A'"` instead of `ir_name("A'") == "A_prime"`, raising `KeyError: "A'"` (`PREVIEW_VALIDATION_FAILED`) after `run_typed_fact_next_v2_route` returned `SERVED`.
- **Non-Mutating In-Memory Completeness Proof (`results/diagnostics.json`):** Resolving `W2-M1..W2-M5` in memory yields **`48 / 48` (`100.0%`) `SERVED_CORRECT`** with `0` oracle mismatches.

---

## 10. Refusal-Reason Agreement on Negative Cases

- **Negative Refusal Rate:** `48 / 48` (`100.00%`, 95% Wilson CI `[0.9259, 1.0000]`).
- **`REFUSED_CORRECT_REASON`:** `33 / 48` (`68.75%`, 95% Wilson CI `[0.5467, 0.8005]`).
- **`REFUSED_REASON_DISAGREEMENT`:** `15 / 48` (`31.25%`, 95% Wilson CI `[0.1995, 0.4533]`):
  - `7` cases (`W2-N25`, `W2-N34..N36`, `W2-N41..N42`, `W2-N43`) were refused by `Planner /17` with `UNSUPPORTED_CAPABILITY` (`mg1: mặt cho bằng quan hệ chỉ dùng cho thiết diện / diện tích thiết diện` or `sec: ['FG'] không phải cạnh bên của S.EFG`) before reaching Source Gate / Engine checks.
  - `8` cases (`W2-N06`, `W2-N23`, `W2-N27`, `W2-N29`, `W2-N30`, `W2-N44`, `W2-N45`, `W2-N47`) were refused earlier at `Source Gate /18` (`SOURCE_OBJECT_MISMATCH` `4`, `SOURCE_PREMISE_UNREAD` `3`, `UNGROUNDED_VALUE` `1`) before reaching downstream dimension or geometric degeneracy checks.

---

## 11. Scene3D Learner-Facing Semantics Findings (Track 10.A vs. Track 10.B)

- **Track 10.A — Source-Identity Correctness (`source_identity_leaks`):**
  - **`0 / 5` (`0.0%`) served cases had any source-identity leak (`source_identity_leaks = []`).**
- **Track 10.B — Pedagogical Auxiliary Display (`R2_AUXILIARY_POINT_NOTATION_DEFERRED`):**
  - **`5 / 5` (`100.0%`) served cases had `r2_auxiliary_notation_observed = True`** (`point3` objects for synthesized auxiliary points `H, H1, H2, H3` carry `notation`).
  - **`5 / 5` (`100.0%`) served cases had `all_auxiliary_visibly_distinguished = True`** in `scored-run-2-harness-corrected` (`origin == "derived"` and role distinct from `"Điểm cho trước"`).

---

## 12. Harness Defects Discovered & Adjudication Protocol Applied

- Following Section 11 and `preregistration.md §9`:
  1. `results/scored-run-1/` was preserved byte-identically (`track-a.json`, `summary.json`, `track-b.json`).
  2. The Category A `closure_certificate=None` scorer defect in `tools/evaluate_holdout_wave2.py` (lines 441–443) and two secondary diagnostic refinements (`RadicalDomainError` subcode matching and Track 10.B derived-role matching) were documented and proved in [`results/harness-adjudication-receipt.json`](results/harness-adjudication-receipt.json) and [`results/harness-adjudication-receipt.md`](results/harness-adjudication-receipt.md).
  3. The harness correction and regression test (`test_19_category_a_single_solid_null_closure_certificate_and_vertices_contract`, `19/19` tests passing) were applied in `tools/evaluate_holdout_wave2.py` and `tools/test_evaluate_holdout_wave2.py`.
  4. The harness-corrected evaluation was written to `results/scored-run-2-harness-corrected/`.
  5. Both raw (`scored-run-1`) and harness-corrected (`scored-run-2-harness-corrected`) numbers are reported side by side across all deliverables.

---

## 13. SHA-256 Hashes of All Key Artifacts

| Relative Path | Bytes | SHA-256 |
|---|---:|---|
| `plan.md` | `4817` | `51f9a426ffbe027b8b907e3d7366e208a93953a91a0c6eafc27a8222bc7ae037` |
| `preregistration.md` | `15810` | `2864c2f111c1afb0e24265601ecfbfb6aa0e7ff286714eef45ef33d9e4faa5b4` |
| `supported-family-matrix.md` | `7717` | `ea4c4c3f5a87f9325112d8c29ac42af8070c171bd35dc0da1c8c85698caca542` |
| `scoring-contract.md` | `8978` | `88b32f56df396acc0e1b3d70cd94621db19063b9105451ac817b2375274719df` |
| `curator-brief.md` | `11252` | `9dd31c18cd4ee205d3904a39192e3d7b19d9e82b8f0d194b0ecb24b65913aa7c` |
| `curator-attestation.md` | `6719` | `dd1a2dee3eba7601d1fbab2d2aa625f7bf12a0db1673a5be5354867b32aeda9e` |
| `corpus-provenance.md` | `19304` | `90ce7aa3fd39191db5802caf72ae10ddc70ad2e2a679b1769a256eab6d88d70d` |
| `holdout-manifest.json` | `3945` | `684be19ccac67237fd5bf81913394f6ed20b889a2b92313ba96666598fbb9dad` |
| `inputs/holdout-wave2.json` | `471848` | `1104be2ad8d4c5c96363f3648bc3c57dfcef5af4334c714e9cc94fc466f38e2d` |
| `oracle/geometry.json` | `148844` | `dcee137a2a10bad499401bd3b45b4c9cc530d9e0ebf51fe669a7ab3bf7ae8d33` |
| `oracle/oracle_holdout_wave2.py` | `20871` | `5511dd0e7dbfb854dcdda4f523c2cd0dd3f52ab22c5851769f7424b243d897d8` |
| `oracle/expected.json` | `28976` | `5efbe57de91c31e18995e679ae6f0ecd69c366ea6bf148ee96255d4cfae7c844` |
| `tools/refusal_taxonomy.json` | `4962` | `a30ebeae583275ca7b3bff809ca93193e0b11f961c9c8c667a681e1f8190e5d8` |
| `tools/dedup_check_wave2.py` | `17690` | `ada310bde4754112273d6de39593508915b6a2cc65b9ec9dea4d68f65cc51849` |
| `tools/audit_curator_log.py` | `6606` | `34c430be83a2aeef5e00716a31f5ca1a3465229ad375b60f1ba45ed3ffe41a22` |
| `tools/evaluate_holdout_wave2.py` (pre-correction) | `31719` | `1a053c4ea2499838626cc7a2be30b14ebaa1a86259718492e149c1a158c37345` |
| `tools/evaluate_holdout_wave2.py` (post-correction) | `32575` | `e9c36a177c2f43cb8af59f361a78421b6f253a5c642e980ad98939793ae51e12` |
| `tools/test_evaluate_holdout_wave2.py` (pre-correction) | `19718` | `33da058cac56e65694735fa2a7914bf093b47ffdd0f68b96a03b54ac891fb3d5` |
| `tools/test_evaluate_holdout_wave2.py` (post-correction) | `20986` | `07330fca6bed5e58cd07d0eb9dfa3e526d322083d7e97b75907eb4c3435e5cd2` |
| `results/deduplication-audit.json` | `833` | `f256fcfc96a20916617c992ec287189818b8d0c4cd7feb69708f1d4a3d389535` |
| `results/independence-audit.json` | `4277` | `3fa99f0aed29710e8fc9d0d3f4a67f80a5927bc86d98a979cc5141f991e480c9` |
| `results/independent-oracle-review-48.json` | `71125` | `373e7094f20d2f2ce95ba2aa934307c7b1a693d5e9de56686aa8b6066e697c12` |
| `results/scored-run-1/track-a.json` | `84233` | `eea9c5d88265bedaeccff06dc059ef39d60496d923f0c7a1426c4fa867c1e3eb` |
| `results/scored-run-1/summary.json` | `31344` | `7287aee2a166afc030ec68e69107762cbe636e0d13674d101740312667c7a512` |
| `results/scored-run-1/track-b.json` | `26034` | `53fee45e31b19ee5a25993412d7674e7c05ad2f9a01ee9df315d64f2a31748b8` |
| `results/scored-run-2-harness-corrected/track-a.json` | `84100` | `2034468882f7e9663f81b033abb2bdc54d3139a9d871de8aa81dabb29463b6ec` |
| `results/scored-run-2-harness-corrected/summary.json` | `31259` | `a3f6521fa227f12a51aaa52ecd4fc1bf7959c48d3ad6331f699c687faef68abc` |
| `results/scored-run-2-harness-corrected/track-b.json` | `26034` | `53fee45e31b19ee5a25993412d7674e7c05ad2f9a01ee9df315d64f2a31748b8` |
| `results/harness-adjudication-receipt.json` | `14076` | `7b1736bee77e8858fc81868a4ebe318afbe5ea55ddb53c94d218f6a5dc610988` |
| `results/harness-adjudication-receipt.md` | `7519` | `e9da80ed7666595a838d3521799a57fec6f9bca8a0536581c18613bb335dbbaa` |
| `results/diagnostics.json` | `15514` | `20f6ed092cd4e884cb64debc293b66970906a2ae44e306b4399fa8f60d77b95b` |
| `results/analysis.json` | `70980` | `e24aa380918311bcd048e355276f093588c3ca84a6e97157e83d0cdeb25cc0db` |
| `report.md` | `22746` | `e55a3e4fe8b0620ecef64deab9120147a3a0a725f67ebb5360dcb2eaffb10861` |
| `review.md` | `16754` | `cf433ec7ece52b8aa9ffeb19a7d9195140651a10032d0d3021cddd5a7b742b3f` |

---

## 14. Evidence Classification Table

| Evaluation Package | Commit | Cases | Evidence Status | Headline Score |
|---|---|---:|---|---|
| `hybrid-v2-independent-vietnamese-section-holdout` | `129c1a95` | `84` | `INDEPENDENT_BLIND_HOLDOUT_WAVE1_BASELINE` | `9/42` served-correct, `33/42` false refusals, `42/42` negatives refused (`23/42` reason match), `0/84` wrong-served |
| `hybrid-v2-holdout-failure-repair` (Wave 1 re-run) | `e3678608` | `84` | `POST_FEEDBACK_DEVELOPMENT_REGRESSION` | `38/42` raw (`40/42` adjudicated) served-correct, `42/42` negatives refused, `0/84` adjudicated wrong-served |
| `hybrid-v2-holdout-failure-repair` (`new-development-corpus.json`) | `e3678608` | `32` | `DEVELOPMENT_REGRESSION_EVIDENCE` | `16/16` served-correct, `16/16` negatives refused, `0/32` wrong-served |
| `hybrid-v2-independent-vietnamese-section-holdout-wave2` (`scored-run-1` raw) | `d7a94d3c` | `96` | `INDEPENDENT_BLIND_HOLDOUT_WAVE2_RAW` | `3/48` served-correct, `43/48` false refusals, `2/48` Category A harness-flagged, `48/48` negatives refused (`33/48` reason match) |
| `hybrid-v2-independent-vietnamese-section-holdout-wave2` (`scored-run-2-harness-corrected`) | `d7a94d3c` | `96` | `INDEPENDENT_BLIND_HOLDOUT_WAVE2_ADJUDICATED` | **`5/48` (`10.42%`) served-correct (`5/5` = `100%` oracle agreement), `43/48` (`89.58%`) false refusals, `48/48` (`100%`) negatives refused (`33/48` = `68.75%` reason match), `0/96` (`0%`) wrong-served** |

---

## 15. Remaining Limitations & Recommended Next Steps

1. **Product Mathematical & Safety Boundary:** Hybrid V2 maintains `0 / 96` genuine wrong-served outputs, `48 / 48` (`100%`) negative refusal safety, `5 / 5` (`100%`) exact oracle agreement on served cases (`7 / 7` at the route level), and `0 / 5` Scene3D source-identity leaks (Track 10.A).
2. **Positive Coverage Bottlenecks (`W2-M1..W2-M5`):** Positive recall on unseen problem phrasing is `5 / 48` (`10.42%`) due to `W2-M1` (`23` cases, inverted `"Trên cạnh XY lấy điểm P sao cho ..."`), `W2-M2` (`5` cases, `"trùng với đỉnh B"`), `W2-M3` (`12` cases, `MAT_HAI_DUONG` `atomic_forms` missing `divide_segment` and oblique `prism`), `W2-M4` (`1` case `W2-A04`, `MAX_RADICAND = 10**12` before rational square reduction), and `W2-M5` (`2` cases `W2-A07, W2-A10`, `Adapter /4` `_validate_sections` raw `"A'"` lookup vs `"A_prime"`).
3. **Recommended Next Action:** Review Wave 2 evidence on branch `research/hybrid-v2-independent-vietnamese-section-holdout-wave2`. Decide whether to (a) integrate the Wave 2 evaluation package into `main` as the authoritative Wave 2 holdout baseline, and/or (b) authorize a targeted follow-up repair wave for `W2-M1..W2-M5` (which would reclassify Wave 2 as `POST_FEEDBACK_DEVELOPMENT_REGRESSION` for any future repair validation).
