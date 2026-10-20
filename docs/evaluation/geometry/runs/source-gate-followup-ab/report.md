# Source Gate Follow-up A+B — Targeted Defect Closure (`source-gate-followup-ab`)

- **Branch**: `research/hybrid-source-gate-followup-ab` (from `main` = `origin/main` = `97cfff9c3085ec00a236f87587c2e4144b38836c`; product commit `68acc140a7d956e494f3bc847d01d20e394e2830`)
- **Owner Authorization**: `GO_SOURCE_GATE_FOLLOWUP_AB_LOCAL_IMPLEMENTATION` (local implementation and verification only; no `GO MAIN` authorization)
- **Measured System Tree SHA-256**: `de66bd5ca6ee798dab043a1a1a7e79fc635aff5b2c5259de8878fe8f66bcae50` (`112` files; supersedes `0512dbc53e09696dfecee4cec8ed360af4ad66d8816c782c2993c3617a0d2583`)
- **Versions & Surface Invariants**:
  - `REGISTRY_VERSION = "geometry-functions/9"`
  - `PLANNER_VERSION = "geometry-fact-planner/10"`
  - `ENGINE_VERSION = "geometry-function-engine/7"`
  - `ADAPTER_VERSION = "hybrid-preview-adapter/2"`
  - `CACHE_VERSION = "127"` (`NO_BUMP`)
  - `DEFAULT_MODE = "LLM_ONLY"`, `RESPONSE_CONTRACT = "flat"`, `HYBRID_PRODUCT_ENABLEMENT = "NO-GO"`, `ALLOW_LIVE_AI = 0`, `live_requests = 0`
  - Surface fingerprints unchanged:
    - `TypedFact`: `aa9d93eeac9f1659af8e5acd42af1904b7aaed674a8ab0f56f0c7dd8b2ad4ee8`
    - `flat`: `485d3834db8b18cfdb24143bfbb14deb8f5b7a9d74cb612d48db8c08252e507a`
    - `v3`: `4bff35bbf690a9973b2b7834019b908d507bbbb4277928e36d12dcff657e226f`
    - `function_declarations`: `5ceb0f999d4d7c1ee37c02207ea6470a7f972a168d6c52fa597392934d86f169`
    - `function_calling`: `7ea511a6e3828c9adcc8402aa2d7d6b1d433e67a01ec4329c3009c46af652b25`

---

## 1. Scope & Defect Root Causes

Following the first official blind evaluation of `SGH-01..18` against the frozen `source-gate-hardening` candidate `c5a83b745d14f7321cb8593d9190a53e459a34bb`, all `4/4` false refusals on positive cases (`SGH-02`, `SGH-04`, `SGH-09`, `SGH-10`) and the diagnostic `BH2A-03` 4-vertex base variant (`(ABCD)`) traced to exactly two remaining source-gate defect classes in `backend/app/simulation/geometry_functions/registry.py`:

### 1.1 Defect Class A — Multi-Goal Question Boundary Before Unnamed Described-Point Goals (`SGH-04`, `SGH-09`)

- **Root Cause**:
  1. In `_kiem_don_vi_hoi` (`registry.py:2899`), `patterns` on `97cfff9c` was `(*(mau for ds in _CUM_HOI.values() for mau, _b in ds), _KHOANG_CACH_DIEM_DUONG, _KHOANG_CACH_GIAO_TUYEN, _CUM_HOI_THIET_DIEN_PHU)`, which omitted unnamed described-point goal contracts (`_mau_khoang_cach_mo_ta` and `_mau_muc_tieu_mo_ta`). When a first goal was followed in the same sentence by an `effect-chain` goal whose target was a plane `(ABC)` (as in `SGH-04` and `SGH-09`), `_kiem_don_vi_hoi` only matched sub-tokens such as `"cạnh BC"` (`ask_length`) inside `duoi_raw`, leaving `" và mặt phẳng (ABC)."` exposed in `after_last` (`seg`). The parenthesized-note loop `for ngoac in re.finditer(r"\(([^()]*)\)", seg):` then matched `(ABC)` as an invalid unit note and returned `False` (`QUESTION_CONTEXT_UNSUPPORTED`).
  2. In `_kiem_du_kien_cau_hoi` (`registry.py:2056, 2062`), `questions` only collected sentences from direct `ask_*` call spans (`{_bien_cau(de, s) for _, s in ask_spans}`) rather than including auxiliary `effect-chain` goal spans `buoc`, and checked `_cum_lon_nhat` against `patterns` without `_mau_hoi_tat_ca()`.
- **Fix A (`P1`)**:
  - Updated `_kiem_don_vi_hoi` to set `patterns = _mau_hoi_tat_ca()`, so every recognized goal pattern in the sentence masks its own operand parentheses in `other` (`before_next` / `after_last`) while still checking each goal's own segment for invalid unit or rounding annotations.
  - Updated `_kiem_du_kien_cau_hoi` to include `{_bien_cau(de, a) for a, _b in buoc}` in `questions` and set `patterns = _mau_hoi_tat_ca()`, preserving `REQUEST_NOT_ANSWERED` when any goal in a multi-goal sentence is omitted.

### 1.2 Defect Class B — Compound Premise Sentences on the `line_ref` / `MAT_HAI_DUONG` Slice (`SGH-02`, `SGH-10`, `BH2A-03-variant-ABCD`)

- **Root Cause**:
  1. On plans using `line_ref` or `MAT_HAI_DUONG`, `kiem_nguon` runs `_kiem_nguon_dong` to verify every call's `source_quote` against a closed premise grammar (`SOURCE_PREMISE_UNREAD`) and verify full sentence coverage (`SOURCE_SENTENCE_UNCOVERED`).
  2. `_kiem_nguon_dong` rejected any non-ask quote containing `,` or `và` (`if "," in s or re.search(r"\bvà\b", s, re.IGNORECASE): return Refusal("SOURCE_PREMISE_UNREAD", call.fn)`), and also rejected multi-clause quotes joined by `"có"` / `"với"` without `,` or `và` (such as `SGH-02`'s `f2` quote `"Cho hình chóp S.MNPQ có đáy MNPQ là hình vuông cạnh 6a"`, or `SGH-10` and `BH2A-03-variant-ABCD` full-sentence premise quotes).
  3. Additionally, `_C_DOAN`, `_C_VUONG`, and `_C_NOI` in the SG-3 closed clause grammar `_phan_tich_cau` did not allow the Vietnamese conjunction `"với"` before segment length or perpendicularity clauses (`"có đáy ABCD là hình chữ nhật với AB = 4a, AD = 2a"`, `"tam giác ABC vuông tại A với AB = 4a"`).
- **Fix B (`P2` + Independent Review Round 1 Hardening `B-1`, `I-1`, `I-2`, `M-1`)**:
  - Extended `_C_DOAN`, `_C_VUONG`, and `_C_NOI` to accept `"với"` alongside `"có"`, `"biết"`, `"và"`, `","`, `";"`.
  - Added `_doc_nhom` and `_cau_tien_de_dong_hop_le(s, s_start, de, calls, allow_single=False)` in `registry.py`, which parses `s` via `_phan_tich_cau(s)` (`SG-3` closed premise grammar) and accepts a compound premise span if and only if:
    1. Every clause in `cau` has a closed grammatical tag (`k != "mo"` — zero opaque clauses), at least one clause is a substantive geometry premise (`k != "khoi"`), and `_so_dinh_cau_khop(cau, khoi_goi)` holds.
    2. Every substantive clause (`"day"`, `"dagiac"`, `"vuong"`, `"doan"`, `"vai"`, `"diem"`, `"dcao"`) is backed 1-to-1 by a validated call in `calls` whose solid (`khoi is not None` for `"day"` and `"dcao"`), role/segment value `(val², has_a)` (with `m["ds"] is None` enforced for rectangle and right-triangle `"day"` clauses), perpendicularity operands, or point construction (`construction_source_bound(replace(d, quotes=(m.group(),)), de)` bound to the exact clause `m.group()` itself, preventing cross-sentence bypass `B-1`) matches the clause; `"chieu"`, `"mat"`, and `"mo"` return `False`.
  - Wired `_kiem_nguon_dong` to validate both the quote `q` and its full enclosing sentence `sent_s` via `_cau_tien_de_dong_hop_le` (`allow_single=True` when `,` or `và` is present; `allow_single=False` for multi-clause spans joined by `"có"` / `"với"`).

---

## 2. TDD Verification (`P1` + `P2`)

`backend/tests/geometry/test_source_gate_hardening.py` was expanded from `226` to `235` tests (`+9` test items across `5` test functions, including parameterized variants):

| Test Function | Defect Class | RED on `97cfff9c` | GREEN on Candidate |
|---|---|---|---|
| `test_followup_a_sgh04_multi_goal_boundaries_served` (`3` parameterized variants) | A (`SGH-04`) | `REFUSED (QUESTION_CONTEXT_UNSUPPORTED)` | `SERVED` (`q1 = 3a`, `q2 = cos²=3/4`) |
| `test_followup_a_sgh09_multi_goal_boundaries_served` (`3` parameterized variants) | A (`SGH-09`) | `REFUSED (QUESTION_CONTEXT_UNSUPPORTED)` | `SERVED` (`q1 = 2a`, `q2 = cos²=13/29`) |
| `test_followup_a_negative_controls_stay_refused` | A negatives (invalid degree unit `(đơn vị: độ)`, rounding note, omitted 2nd goal, spoofed plane `(A'BC)`) | `REFUSED` | `REFUSED` (`QUESTION_CONTEXT_UNSUPPORTED`, `REQUEST_NOT_ANSWERED`, `SOURCE_OBJECT_MISMATCH`) |
| `test_followup_b_sgh02_sgh10_bh2a03_compound_premise_with_line_ref_served` | B (`SGH-02`, `SGH-10`, `BH2A-03-variant-ABCD`, rectangle pyramid, right prism, explicit `intersection_line` sentence) | `REFUSED (SOURCE_PREMISE_UNREAD)` | `SERVED` (`SGH-02`: `a√37`; `SGH-10`: `2a√2`; `BH2A-03-variant-ABCD`: `a√10`; rectangle pyramid: `3a√70/14`; right prism: `3a√2`) |
| `test_followup_b_negative_controls_stay_refused` | B negatives (unread clause `"mặt bên SBC là tam giác đều"`, swapped values `AB=2a, AD=4a`, dropped parameter `a`, spoofed `line_ref` planes, 3-label `(ABC)` for `(ABCD)`, cross-sentence point/projection clause `B-1`) | `REFUSED` | `REFUSED` (`SOURCE_PREMISE_UNREAD`, `UNGROUNDED_VALUE`, `SOURCE_OBJECT_MISMATCH`) |

---

## 3. Controlled Post-Feedback Regression Evaluation (`P3`)

> [!IMPORTANT]
> **Scientific Labeling Rule**: Because `SGH-02`, `SGH-04`, `SGH-09`, `SGH-10`, and `BH2A-03` were previously inspected during evaluation diagnosis, all post-fix executions on `SGH-01..18` and `BH2A-01..18` are strictly classified as **`POST_FEEDBACK_REGRESSION`** / **`KNOWN_REGRESSION_NOT_BLIND`** (`blind_holdout: false`). The first official blind evaluation record of `SGH-01..18` (`6/10` positive, `10/16` math goals, `5/5` negative) remains preserved untouched in `docs/evaluation/geometry/runs/source-gate-hardening/`.

### 3.1 `SGH-01..18` Post-Feedback Regression (`sgh-post-feedback-regression.json`)

- **Manifest Identity Verified**:
  - `manifest_file_sha256`: `268c5d666fe19133f9f5a2f523942fcc612f4ee98efe8a6d56aee9e4ea572641` (unchanged)
  - `canonical_manifest_lock`: `fe3356847140000add09f20cfd3f598849c54992751ff70f101a79a1ae039ab2` (unchanged)
- **Summary**:
  - **Positive cases (`SGH-01..10`)**: `10/10 SERVED` (`100%`, up from `6/10` on `c5a83b74`: `SGH-01` `2a√14`; `SGH-02` `a√37`; `SGH-03` `7a²`; `SGH-04` `q1=3a, q2=cos²=3/4`; `SGH-05` `q1=2a√6, q2=cos²=49/81`; `SGH-06` `q1=2√11, q2=9√2`; `SGH-07` `q1=2a, q2=cos²=64/343`; `SGH-08` `q1=2a√3, q2=3a²√3/2`; `SGH-09` `q1=2a, q2=cos²=13/29`; `SGH-10` `2a√2`).
  - **Positive goals (`16` total across `SGH-01..10`)**: `16/16` mathematically exact (`100%`, up from `10/16` on `c5a83b74`); `14/16` strict tuple match (`SGH-05 q2` $\cos^2\theta = 49/81$ and `SGH-07 q2` $\cos^2\theta = 64/343$ are dimensionless with `has_a=0, dim=0`, where the manifest stored `dim=1` by convention).
  - **Negative cases (`SGH-11..15`)**: `5/5 REFUSED` with exact expected refusal codes (`SGH-11`: `UNGROUNDED_VALUE`, `SGH-12`: `SOURCE_OBJECT_MISMATCH`, `SGH-13`: `REQUEST_NOT_ANSWERED`, `SGH-14`: `INCONSISTENT_FACTS`, `SGH-15`: `UNDERDETERMINED_POINT`).
  - **Ambiguous cases (`SGH-16..17`)**: `1/2` (`SGH-16` refused `UNGROUNDED_VALUE`; `SGH-17` served `2a` due to manifest design discrepancy where all premises are explicitly grounded, adjudicated separately without manifest edit).
  - **Out-of-scope (`SGH-18`)**: `1/1 REFUSED` (`SCHEMA_INVALID`, matching expected `UNSUPPORTED_CAPABILITY|SCHEMA_INVALID|SOURCE_OBJECT_MISMATCH`).
  - **False serves**: `0`.

### 3.2 `BH2A-01..18` Known Regression (`bh2a-post-feedback-regression.json`)

- **Summary**:
  - **Positives (`BH2A-01..12`)**: `11/12 SERVED` (`14/15` goals exact; only `BH2A-03` original 3-label `(ABC)` for a 4-vertex square pyramid base `(ABCD)` remains intentionally refused `SOURCE_OBJECT_MISMATCH`).
  - **Negatives (`BH2A-14..18`)**: `5/5 REFUSED`.
  - **Sentinel (`BH2A-13`)**: `SERVED` (`a²√3`).
  - **Diagnostic `BH2A-03-variant-ABCD` (square pyramid `S.ABCD` with 4-vertex base `(ABCD)`)**: transitions from `REFUSED (SOURCE_PREMISE_UNREAD)` on `97cfff9c` to **`SERVED` (`q1 = a√10`, `EXACT`)**.

### 3.3 `SG-1..SG-6` Locked Corpus (`sg1-sg6-regression.json`) & Full Geometry Regression

- **`SG-1..SG-6` Locked Corpus (`30` cases)**: `18/18` positive `SERVED` (`21/21` goals exact), `12/12` negative `REFUSED`, `0` wrong serves — byte-for-byte outcome match with `source-gate-hardening`.
- **Backend & Frontend Regression Suites**:
  - `test_source_gate_hardening.py` + `test_shared_ask_grammar.py` + `test_result_binding_planning.py` + `test_two_line_plane_section.py`: `1036/1036` passed.
  - Wave 1, Wave 2A, Wave 2B, 174-row historical regression, 41/41 Adapter `/2` fixtures, NLU GOLD (`L27` served, `L28` declared code), Route A isolation, Scene3D & IR suites: `977/977` passed (once `EVALUATION_CANDIDATE.json` is frozen to `de66bd5ca6ee798dab043a1a1a7e79fc635aff5b2c5259de8878fe8f66bcae50`).
  - `test_hybrid_preview_contract.py`: `64/64` passed.
  - Frontend `scene3d-annotations.test.ts`: `34/34` passed.
