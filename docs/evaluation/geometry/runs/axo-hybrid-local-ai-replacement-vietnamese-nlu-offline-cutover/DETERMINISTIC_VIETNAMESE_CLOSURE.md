# AXO HYBRID /9 — Deterministic Vietnamese Language Closure & Fail-Closed Guard (`DETERMINISTIC_VIETNAMESE_CLOSURE.md`)

## 1. Objective & Scope Boundary

Phase P2 closes all empirically proven deterministic surface, extraction-contract, and routing gaps on Vietnamese 3D geometry inputs **without modifying any locked Gemini surface (`typed_fact_next_surface`, `function_calling`, `flat`, `v3`), any `/5`–`/8` baseline/rule constant, or `BLOCKED_OWNERSHIP` files (`registry.py`, `planner.py`, `engine.py`, `frontend/**`)**.

- **Additive Versioning Preserved:**
  - Frozen `/6` (`slm-verified-normalizer/1`) and `/7` (`slm-verified-normalizer/2`, `local-slm-extractor/3`, `slm-grounding-validator/3`, `slm-grounding-envelope/3`, `DEFAULT_CLOSURE_MODE = "v7"`) code paths remain bit-for-bit untouched.
  - New `/9` contracts activate strictly under `closure_mode="v9"` (`normalizer_version="v3"`):
    - Normalizer: `SLM_VERIFIED_NORMALIZER_V3_VERSION = "slm-verified-normalizer/3"` (`backend/app/ai/slm_verified_normalizer.py`)
    - Extractor / Validator / Envelope: `LOCAL_SLM_EXTRACTOR_V9_VERSION = "local-slm-extractor/4"`, `SLM_GROUNDING_VALIDATOR_V9_VERSION = "slm-grounding-validator/4"`, `SLM_GROUNDING_ENVELOPE_V9_VERSION = "slm-grounding-envelope/4"`, `V9_CLOSURE_MODE = "v9"` (`backend/app/ai/local_slm_extractor.py`)

## 2. Normalizer `slm-verified-normalizer/3` Rule Families (`VN06`–`VN11`)

Every rewrite emits a 10-field `VerifiedNormalizationStep` provenance entry (`rule_id`, `original_text`, `original_span`, `original_clause_id`, `normalized_text`, `original_entity_refs`, `scope`, `polarity`, `semantic_equivalence_evidence`, `validation_result`) and passes conservative typo/conditional/negation/entity guards:

| Family | Key Rules | Deterministic Closure | Safety Guards |
|---|---|---|---|
| **`VN06`** | `VN06_IMPLICIT_MOT_HINH`, `VN06_IMPLICIT_BARE_SOLID`, `VN06_SOLID_SEP_DAY`, `VN06_BA_KICH_THUOC`, `VN06_VOI_DIMENSIONS`, `VN06_CHAINED_SEGMENT_EQ`, `VN06_CUBE_CANH_BANG`, `VN06_IMPLICIT_BASE_LABEL_SHAPE`, `VN06_IMPLICIT_VOLUME_SOLID`, `VN06_RIGHT_PRISM_CANH_BEN` | Canonicalizes missing `"Cho "` openers (`Một hình...`, `Hình chóp...`), expands `có ba kích thước`, expands chained equalities (`OA = OB = OC = 3` → `OA = 3, OB = 3, OC = 3`), resolves implicit cube `cạnh 2` → `có cạnh bằng 2`, right-prism `cạnh bên AA' = 6` → `AA' = 6`, and unique base/solid volume targets. | Conditional `"Nếu/Khi/Giả sử"`, negated clauses, non-prism ambiguous `"cạnh bên"`, and RHS vertex labels strictly blocked (`skip_if_cond_or_neg=True`). |
| **`VN07`** | `VN07_MP_PAREN`, `VN07_SEMICOLON_TO_COMMA`, `VN07_CANH_BEN_PERP_PREFIX`, `VN07_IMPLICIT_MAT_DAY_PERP`, `VN07_IMPLICIT_MAT_DAY_GOAL`, `VN07_DUONG_CHEO_TO_DUONG_THANG` | Normalizes `mp(SBC)` / `mặt phẳng SBC` → `mặt phẳng (SBC)`, disambiguates `mặt đáy`/`đáy` to unique solid base `(ABCD)` using case-scoped lookaheads (`(?!\s*\(?[A-Z])` outside `re.IGNORECASE`!), and maps angle-operand `đường chéo AC'` → `đường thẳng AC'`. | Never rewrites `đoạn thẳng` → `đường thẳng` (`D05`/`L12` protected). |
| **`VN08`** | `VN08_LAY_TRUNG_DIEM`, `VN08_DUNG_HINH_CHIEU` | Rewrites construction imperatives (`Lấy trung điểm của cạnh CC' rồi đặt tên nó là M` → `Gọi M là trung điểm của cạnh CC'`, `Hãy dựng hình chiếu vuông góc..., gọi là H, rồi...` → `Gọi H là hình chiếu vuông góc... . Tính...`). | Skips conditional/negated sentences. |
| **`VN09`** | `VN09_SPLIT_ENUM_GOALS`, `VN09_SPLIT_COORDINATED_GOALS`, `VN09_CAPITALIZE_SPLIT_GOALS`, `VN09_SHORTHAND_TINH_SEG`, `VN09_ANAPHORA_TWO_LINES_*`, `VN09_CENTROID_DISTANCE_TO_NAMED*`, `VN09_RIGHT_PRISM_FACE_CENTER`, `VN09_PROJECTION_FOOT_DISTANCE` | Splits `a)/b)` & coordinated asks into atomic sentences; resolves unique preceding 2-line anaphora (`AB' và BC'`, `BD và B'C`); introduces unused point labels (`G`/`O`) for centroid distance and right-prism face center (`((?:[A-Z][0-9]*'*){4})` preserving `CO`, not `CO'`); equates orthogonal-foot distance to point–plane distance. | `(?![²^0-9])` protects `SC²` (`L10`); unused-point collision guard avoids colliding with existing points. |
| **`VN10`** | `VN10_QUESTION_FIRST_*`, `VN10_BANG_MAY`, `VN10_DUONG_CHEO_DAI_BAO_NHIEU`, `VN10_HOI_CACH_MAT_PHANG`, `VN10_KC_BAO_NHIEU_VAY_A`, `VN10_TAO_VOI_GOC` | Reorders non-conditional `, biết ...` question-first problems; converts `thì đoạn AC' bằng mấy` BEFORE `v2` `VN05_SEG_BANG` (eliminating `=mấy` corruption); standardizes colloquial questions. | Blocks any sentence with `nếu`/`khi`/`giả sử` or negations. |
| **`VN11`** | `VN11_COS2_TO_COSIN` | Rewrites `cos² (của) góc giữa ...` → `cosin góc giữa ...` so Source Gate (`ham_luong_giac_hoi`) passes without lowering trig fidelity (`cos²=...` answer verified unchanged). | Does not conflate `sin`/`tan`/`cot` or general `góc`. |

## 3. Extractor (`local-slm-extractor/4`) & Adaptive Router (`/9`) Upgrades

1. **Fixed Existing Tetrahedron Indexing Bug (`local_slm_extractor.py:2241-2244`):** `re.finditer` on `tứ diện OABC` previously scanned `tm.group(0)`, counting `'T'` from `"Tứ"` as a 5th point and dropping every non-dotted tetrahedron solid (`L19`, `L23`). Wrapping vertex capture in `((?:[A-Z][0-9]*'*){4})` and reading `tm.group(1)` restores `"O.ABC"`.
2. **Raised GBNF Goal Cap (`2` → `4`) & Casual Goal Markers (`closure_mode="v9"`):** Raises `goallistreq` to 4 goals (`D12`, `L23`, `L27`, `L30`), adds `"bằng mấy"` / `"dài bao nhiêu"` to `_GOAL_VERB_RE`, enables `{pfx}cent` (`centroid`) in GBNF, exposes solid base polygon `ABCD` on cube/box clauses, and grounds cube edge `len(AA', q)` when `"lập phương"` + `"cạnh"` + `q` appear in clause (`D09`, `D12`, `L20`, `L29`).
3. **Fail-Closed Multi-Goal Completeness (`classify_multi_goal_status`):** Under `closure_mode="v9"`, if the source asks ≥ 2 distinct goal clauses and fewer goals are grounded, returns `REQUEST_NOT_ANSWERED` (`INCOMPLETE_EXTRACTION_REFUSED`) rather than silently dropping asked subgoals.
4. **Adaptive Fast-Path Before SLM (`adaptive_input_router.py`):** Under `v9`/`v3`:
   - Runs `detect_prompt_injection` and `normalize_for_slm_grounding(..., "v3")` typo guard up front (`slm_invoked=False` on injection or typo).
   - Attempts deterministic `route_text_input(v3_norm.canonical_text, allow_live_ai=False)` before escalating to `llama-server`, attaching `normalizer_provenance` and setting `extraction_mode = "LOCAL_PARSER_AFTER_V3_NORMALIZER"`.

## 4. Verification Summary

- **`backend/tests/geometry/test_slm_language_closure.py` + `test_local_slm_understanding.py` (`task-4445` & `task-4512`):** **`13 passed`** / **`14 passed, 0 failed`** across frozen `/6`–`/7` suites — zero regression on frozen contracts.
- **`backend/tests/geometry/test_slm_v9_language_closure_and_security.py` (`task-4456` & `task-4512`):** **`4 passed, 0 failed`** (`test_v1_v2_preserved_while_v3_adds_provenance_and_closure`, `test_v3_fixes_l03_l07_l21_and_resolves_fast_path`, `test_tetrahedron_without_dot_and_v9_gbnf_lifts`, `test_security_10_adversarial_and_failure_categories` covering typos, conditionals, negations, finite `đoạn thẳng`, prompt injection, malformed non-dict JSON, incomplete multi-goal drops, and cube edge grounding).
- **Post-P2 Full C60 + `/7` Residual Live Audit (`backend/scripts/evaluate_p2_and_p3_residual_v9.py`, `task-4513`):**
  - `C60_BLIND_NLU` with unmodified `AxoV7` + `/9` closure (`v3`/`v9`): **`26/42` (`61.90%`) served exact strictly-all** (`23` via deterministic fast-path + `3` via SLM `L02`, `L03`, `L20`), **`0` wrong-served** across all 60 cases (up from `13/42` baseline).
  - Remaining genuine solvable SLM misses establishing empirical need for P3 targeted LoRA (`AxoV9`): **`13`** total (**`7`** C60 cases `D09`, `D11`, `L19`, `L21`, `L24`, `L27`, `L30` + **`6`** `/7` residual holdouts `v7h_p5_09`, `v7h_p8_01..05`).
