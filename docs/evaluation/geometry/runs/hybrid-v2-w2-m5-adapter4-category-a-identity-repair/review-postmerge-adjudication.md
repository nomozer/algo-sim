# Independent Verification Review — W2-M5 Post-Merge Case Identity & Evidence Adjudication

- **Task:** `HYBRID_V2_W2_M5_POSTMERGE_CASE_IDENTITY_ADJUDICATION`
- **Reviewer Role:** `Independent W2-M5 Post-Merge Case Identity Reviewer` (`95cabb69-16a8-4241-9ffc-97003ad79f20`)
- **Review Verdict:** `APPROVED_NO_FINDINGS` (`0 BLOCKER, 0 MAJOR, 0 MINOR, 0 NIT`)
- **Adjudication Status:** `EVIDENCE_CORRECTION_REQUIRED` (narrative/conversational reporting discrepancies corrected additively; `0` product regressions; `0` machine-JSON discrepancies)
- **Reviewed Branch:** `docs/hybrid-v2-w2-m5-postmerge-case-identity-adjudication`
- **Authoritative `main = origin/main = remote`:** `2c42f6cf23ddde89cc752e0ee6dfec6e4e230d3b`
- **Frozen Full T3 Candidate:** `b61f16995dfbe0110a639a2127d0fb5a9c3afde0`
- **Product Commit:** `73ca8d92e74059680ce53b99692af396df37a2f8`
- **Measured Product System (`118` files):** `1170ca163529dd40b57f4058826db92a6433359546aa2ad718712f38a538c10d` (`MATCH`)
- **Historical Holdout Wave 2 Commit:** `ecdc26b012c8ce80d53524a98dc75cdcb020079d` (`0` bytes modified)

---

## 1. Detailed Verification by Criterion (Owner GO Section 6)

### Criterion 1 — Every Case ID Matches Its Payload (`PASS`)
- Independently parsed `docs/evaluation/geometry/runs/hybrid-v2-independent-vietnamese-section-holdout-wave2/inputs/holdout-wave2.json` (`96` cases: `36` `P-B`, `12` `P-A`, `48` `N`; LF SHA-256 `1104be2ad8d4c5c96363f3648bc3c57dfcef5af4334c714e9cc94fc466f38e2d`).
- Verified **100% uniqueness across all 96 Wave 2 cases**: `96` unique case IDs, `96` unique canonical case SHA-256 digests, and `96` unique canonical `payload` SHA-256 digests (`0` collisions).
- Verified `W2-A07` (`inputs/holdout-wave2.json:5965–6114` and `inputs/development.json`):
  - Canonical case SHA-256: `717ee585a0411ec67e2045ee4f71beb217088a0264eb649399bb4386d7999e73`
  - Canonical `payload` SHA-256: `ed8f11b8aa49478ee62bd6ce8c4a7e29e86865c336f5cd880edabbd2f3e23142`
  - Right triangular prism `ABC.A'B'C'` (`right_triangular_prism`, right at `B`, $AB=5, BC=5, AA'=10$), cut by $(\alpha) \ni A' \perp AC'$ at stated intersections `M` on `BB'` and `N` on `CC'`, asking `section_area` (`mg1`).
- Verified `W2-A10` (`inputs/holdout-wave2.json:6434–6583` and `inputs/development.json`):
  - Canonical case SHA-256: `3f1d5a6142b34b715032aca475ae7e97322b88c7bb08b1e2b077b2d11ec1b88a`
  - Canonical `payload` SHA-256: `922e49a272dd8a3836c52792d8ee60e8e5156a34ee4c895a25df8610b7feb85d`
  - Rectangular cuboid `ABCD.A'B'C'D'` (`cuboid`, base rectangle `ABCD`, $AB=3a, AD=6a, AA'=9a$), cut by $(Q) \ni A' \perp AC'$ at unnamed stated intersections on `BB'`, `CC'`, `DD'`, `section_only` (`math_goals = []`).

### Criterion 2 — Oracles Are Not Swapped (`PASS`)
- Independently verified `oracle/expected.json` (`LF SHA-256 da70fe6a08530e49e7292782592a618c6268385adbb8958dbf46f3693944efa`), `oracle/geometry.json` (`LF SHA-256 3bed9d0844a1084dce43b69cfd8dd73624a19090be901d97c48d83f996bd78ae`), and W2-M5 `inputs/oracle.json` (`LF SHA-256 83137971fca1fc87e0cef6af10be164d8987eda5742db9c414a84af98002b40d`):
  - **`W2-A07` (`expected.json:1474–1500`, `geometry.json:7758–7936`):** `solid = "ABC.A'B'C'"`, `expected_certificate_category = "DINH_CAT_CANH"`, `area_goal_id = "mg1"`, `vertex_count = 3`, `boundary = [{"vertex": "A'"}, {"edge": ["B", "B'"], "t": "3/4"}, {"edge": ["C", "C'"], "t": "1/2"}]`, `area_squared = "1875/8"`.
  - **`W2-A10` (`expected.json:1563–1596`, `geometry.json:8323–8538`):** `solid = "ABCD.A'B'C'D'"`, `expected_certificate_category = "DINH_CAT_CANH"`, `area_goal_id = null`, `vertex_count = 4`, `boundary = [{"vertex": "A'"}, {"edge": ["B", "B'"], "t": "8/9"}, {"edge": ["C", "C'"], "t": "4/9"}, {"edge": ["D", "D'"], "t": "5/9"}]`, `area_squared = "504"`.
- Both entries in W2-M5 `inputs/oracle.json` match frozen Holdout Wave 2 `oracle/expected.json` byte-for-byte.

### Criterion 3 — Polygons Are Not Swapped Between Fixtures (`PASS`)
- Independently executed `run_typed_fact_next_v2_route` and `build_adapter4_response` on `W2-A07` and `W2-A10`:
  - **`W2-A07` Product Polygon (`td_sec`, `notation = "MA′N"`):**
    - Normalized coordinates: `[["1", "0", "3/4"], ["0", "0", "1"], ["0", "1", "1/2"]]` (`[M, A', N]`).
    - Canonical boundary descriptors: `[("EDGE", "B", "B'", "3/4"), ("VERTEX", "A'"), ("EDGE", "C", "C'", "1/2")]`.
    - Matches `W2-A07` oracle cycle `[("VERTEX", "A'"), ("EDGE", "B", "B'", "3/4"), ("EDGE", "C", "C'", "1/2")]` under reversal + cyclic shift `1` (`cyclic_equivalent = True, orientation = "reversed", shift = 1`).
  - **`W2-A10` Product Polygon (`td_sec`, `label = "Thiết diện bởi (Q)"`, `notation = null`):**
    - Normalized coordinates: `[["1", "0", "8/9"], ["0", "0", "1"], ["0", "1", "5/9"], ["1", "1", "4/9"]]` (`[I, A', I2, I1]`).
    - Canonical boundary descriptors: `[("EDGE", "B", "B'", "8/9"), ("VERTEX", "A'"), ("EDGE", "D", "D'", "5/9"), ("EDGE", "C", "C'", "4/9")]`.
    - Matches `W2-A10` oracle cycle `[("VERTEX", "A'"), ("EDGE", "B", "B'", "8/9"), ("EDGE", "C", "C'", "4/9"), ("EDGE", "D", "D'", "5/9")]` under reversal + cyclic shift `2` (`cyclic_equivalent = True, orientation = "reversed", shift = 2`).
- Confirmed via `git grep` at `2c42f6cf23ddde89cc752e0ee6dfec6e4e230d3b` that the conversational compaction hallucinations `section_37467f986437 (A, B, C, A′)` and `section_fa8b24d27d9e (A, M, P, N)` have **zero (`0`) occurrences** anywhere in the repository.

### Criterion 4 — `area_squared` Matches (`1875/8` for `W2-A07`, `504` for `W2-A10`) (`PASS`)
- **`W2-A07`:** Euclidean vertices $A'=(0,0,10)$, $M=(5,0,15/2)$, $N=(5,5,5)$ yield $\overrightarrow{A'M} \times \overrightarrow{A'N} = (25/2, 25/2, 25)$ and $\text{area\_squared} = \frac{1}{4}(625/4 + 625/4 + 625) = \text{Fraction}(1875, 8)$, matching `_binh_phuong(res07.exec_result.final_memory["kq_mg1"]) == Fraction(1875, 8)` and formatted answer `"25√6/4"`.
- **`W2-A10`:** Euclidean vertices $I=(3,0,8)$, $A'=(0,0,9)$, $I_2=(0,6,5)$, $I_1=(3,6,4)$ form a parallelogram with $(I - A') \times (I_2 - A') = (6, 12, 18)$ and $\text{area\_squared} = 6^2 + 12^2 + 18^2 = 504$, matching `oracle/expected.json` (`"504"`).

### Criterion 5 — Product Status Is Accurate (`PASS`)
- Both `W2-A07` and `W2-A10` return `route_status == "SERVED"`, `adapter4_status == "SERVED"`, and `envelope_status == "ok"` on `main` (`2c42f6cf23ddde89cc752e0ee6dfec6e4e230d3b`), with `A_prime.notation == "A′"` and `0` `_prime` leaks.
- `git diff --name-only b61f16995dfbe0110a639a2127d0fb5a9c3afde0..HEAD -- backend/app frontend/src` is empty (`0` product regressions, `0` code changes).
- `freeze_evaluation_candidate.py --manifest docs/evaluation/semantic-benchmark/EVALUATION_CANDIDATE.json --verify` passed (`118` files, tree SHA-256 `1170ca163529dd40b57f4058826db92a6433359546aa2ad718712f38a538c10d`).
- `audit_docs_information_architecture.py` passed with `0` errors (`=== DOCS INFORMATION ARCHITECTURE AUDIT: PASS ===`).

### Criterion 6 — Raw (`47/48`) vs Adjudicated (`48/48`) Scores Strictly Distinguished & Scorer Bug Attributed to `W2-A10` (`PASS`)
- Verified `evaluate_holdout_wave2.py:178–193`: at line `184`, `elif v.get("label") and v["label"] in objects_by_id:` fails to resolve `"A'"` because `objects_by_id` is keyed by `ir_name("A'") == "A_prime"`, even though `_find_point_xyz(objects_by_id, label)` is defined at line `146` and called at line `232`.
- Verified why `W2-A07` is unaffected (`SERVED_CORRECT` under raw scorer, `47/48`): `W2-A07` is a 3-vertex triangle `{A', M, N}`, and every permutation of 3 elements is either a cyclic shift or reversal of the 3-cycle.
- Verified why `W2-A10` fails the raw scorer (`WRONG_SERVED` under raw scorer $\to$ `SERVED_CORRECT` under adjudicated scorer, `48/48`): `W2-A10` is a 4-vertex quadrilateral `[I, A', I2, I1]`; `"A'"` falls back to `poly_idx = 0`, colliding with `"I"` (`poly_idx = 0`) and sorting into the bow-tie order `[A', I, I2, I1]`.
- `correction-addendum.md`, `results/postmerge-case-identity-adjudication.json`, `docs/EVIDENCE_INDEX.md`, and `docs/CURRENT_STATE.md` strictly distinguish raw (`47/48`) and adjudicated (`48/48`) scores and accurately attribute the line `184` scorer bug exclusively to `W2-A10`.

### Criterion 7 — Historical Evidence Is Not Rewritten (`PASS`)
- Verified `git diff ecdc26b012c8ce80d53524a98dc75cdcb020079d..HEAD -- docs/evaluation/geometry/runs/hybrid-v2-independent-vietnamese-section-holdout-wave2` and `git status --porcelain` on that directory: **`0` bytes modified**.
- Verified all `26/26` existing files committed in `docs/evaluation/geometry/runs/hybrid-v2-w2-m5-adapter4-category-a-identity-repair/` at `2c42f6cf23ddde89cc752e0ee6dfec6e4e230d3b` against the working tree: **`26/26` byte-for-byte untouched** (`0` modifications). Only additive adjudication files (`correction-addendum.md`, `review-postmerge-adjudication.md`, `results/postmerge-case-identity-adjudication.json`, `tools/adjudicate_postmerge_case_identity.py`) and the three index/state docs (`docs/EVIDENCE_INDEX.md`, `docs/CURRENT_STATE.md`, `docs/CODE_INDEX.md`) are added/updated.
