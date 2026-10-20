# Handoff — `source-gate-followup-ab`

- **Status**: `SOURCE_GATE_FOLLOWUP_AB_READY_FOR_GO_MAIN_REVIEW`
- **Branch**: `research/hybrid-source-gate-followup-ab`
- **Base (`main` = `origin/main`)**: `97cfff9c3085ec00a236f87587c2e4144b38836c`
- **Product Commit**: `68acc140a7d956e494f3bc847d01d20e394e2830` (`68acc140`)
- **Candidate Freeze Commit**: `b5e803801a9493b719813a7f5d5b68fd5ff20c14` (`b5e80380`)
- **Authoritative Full T3**: `FULL_PRODUCT_GATE_PASS` at `b0b2a3c3563db6420d8700bb4e9a62efee7f57f1` (`b0b2a3c3`; pytest `11,347` passed, vitest `1,146` passed, build `PASS`, demo `5/5`, crash surface `6/6`; [`verification/authoritative-t3.json`](verification/authoritative-t3.json))
- **Independent Review**: `INDEPENDENT_REVIEW_PASS` ([`verification/independent-review.md`](verification/independent-review.md))
- **Measured System Tree SHA-256**: `de66bd5ca6ee798dab043a1a1a7e79fc635aff5b2c5259de8878fe8f66bcae50` (`112` files)
- **Authorization**: `GO_SOURCE_GATE_FOLLOWUP_AB_LOCAL_IMPLEMENTATION` (local implementation & verification only; NO `GO MAIN` authorization)

---

## 1. Summary of Changes

1. **Fix A — Multi-Goal Question Boundary Before Unnamed Described-Point Goals (`SGH-04`, `SGH-09`)**:
   - `backend/app/simulation/geometry_functions/registry.py::_kiem_don_vi_hoi` now sets `patterns = _mau_hoi_tat_ca()`, so subsequent goal phrases (including unnamed described-point contracts from `_mau_khoang_cach_mo_ta` and `_mau_muc_tieu_mo_ta`) are included in `other` (`before_next` / `after_last`) and their plane operands `(ABC)` are not misread as invalid unit annotations (`QUESTION_CONTEXT_UNSUPPORTED`).
   - `backend/app/simulation/geometry_functions/registry.py::_kiem_du_kien_cau_hoi` includes `{_bien_cau(de, a) for a, _b in buoc}` in `questions` and `_mau_hoi_tat_ca()` in `patterns`.
2. **Fix B — Compound Premise Sentences on `line_ref` / `MAT_HAI_DUONG` Slice (`SGH-02`, `SGH-10`, `BH2A-03-variant-ABCD`)**:
   - `backend/app/simulation/geometry_functions/registry.py` (`_C_DOAN`, `_C_VUONG`, `_C_NOI`) accepts `"với"` before segment-length and perpendicularity clauses.
   - `backend/app/simulation/geometry_functions/registry.py::_cau_tien_de_dong_hop_le` and `_kiem_nguon_dong` validate compound premise spans on the `line_ref` / `MAT_HAI_DUONG` slice when every clause in the span is parsed by `_phan_tich_cau` (`SG-3` closed premise grammar) with zero opaque (`"mo"`) clauses, at least one non-`"khoi"` clause, and every substantive clause (`"day"`, `"dagiac"`, `"vuong"`, `"doan"`, `"vai"`, `"diem"`, `"dcao"`) is backed 1-to-1 by a validated call in `calls` (with `"diem"` checked against `m.group()` itself via `construction_source_bound(replace(d, quotes=(m.group(),)), de)` and `"chieu"`, `"mat"`, `"mo"` rejected fail-closed).

---

## 2. Post-Feedback Regression & Safety Invariants

- **`SGH-01..18` (`POST_FEEDBACK_REGRESSION`, not blind)**:
  - Positive cases: `10/10 SERVED` (`100%`, up from `6/10` on `c5a83b74`).
  - Positive goals: `16/16` mathematically exact (`100%`, up from `10/16` on `c5a83b74`); `14/16` strict tuple (`SGH-05 q2` $\cos^2\theta = 49/81$, `SGH-07 q2` $\cos^2\theta = 64/343$ dimensionless).
  - Negative cases: `5/5 REFUSED` with exact expected codes (`UNGROUNDED_VALUE`, `SOURCE_OBJECT_MISMATCH`, `REQUEST_NOT_ANSWERED`, `INCONSISTENT_FACTS`, `UNDERDETERMINED_POINT`).
  - Ambiguous: `1/2` (`SGH-16` refused `UNGROUNDED_VALUE`; `SGH-17` served `2a` due to oracle discrepancy adjudicated separately without manifest edit).
  - Out-of-scope: `1/1 REFUSED` (`SCHEMA_INVALID`).
  - False serves: `0`.
  - Artifact: [`sgh-post-feedback-regression.json`](sgh-post-feedback-regression.json).
- **`BH2A-01..18` (`KNOWN_REGRESSION_NOT_BLIND`)**:
  - Positive cases: `11/12 SERVED` (`14/15` goals exact) + sentinel `BH2A-13` `SERVED` (`a²√3`) + `5/5` negatives `REFUSED`.
  - Diagnostic `BH2A-03-variant-ABCD`: `SERVED` (`q1 = a√10`, `EXACT`).
  - Artifact: [`bh2a-post-feedback-regression.json`](bh2a-post-feedback-regression.json).
- **`SG-1..SG-6` Locked Corpus**:
  - `18/18` positive `SERVED` (`21/21` goals exact), `12/12` negative `REFUSED`, `0` wrong serves (`30/30` match).
  - Artifact: [`sg1-sg6-regression.json`](sg1-sg6-regression.json).
- **Invariants**:
  - `DEFAULT_MODE = "LLM_ONLY"`, `RESPONSE_CONTRACT = "flat"`, `HYBRID_PRODUCT_ENABLEMENT = "NO-GO"`, `ALLOW_LIVE_AI = 0`, `CACHE_VERSION = "127"` (`NO_BUMP`).
  - `REGISTRY_VERSION = "geometry-functions/9"`, `PLANNER_VERSION = "geometry-fact-planner/10"`, `ENGINE_VERSION = "geometry-function-engine/7"`, `ADAPTER_VERSION = "hybrid-preview-adapter/2"`.
  - Surface fingerprints (`TypedFact` `aa9d93eeac9f…`, `flat` `485d3834db8b…`, `v3` `4bff35bbf690…`, `function_declarations` `5ceb0f999d4d…`, `function_calling` `7ea511a6e382…`) unchanged.
