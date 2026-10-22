# SESSION3_RESUME_STATE — Claude Opus 5.5 → Gemini 4 Argon Handoff Recovery

- **Timestamp (local):** `2026-10-23T00:32:00+07:00`
- **Authorization:** `GO_HYBRID_SESSION3_CONTRACT_V2_LOCAL_RESEARCH` (Owner decisions `D1 GO`, `D2 GO-conditional`, `D3 GO`, `D4 KEEP 32`, `D5 GO`, `D6 GO-limited`).
- **Active Worktree:** `D:\Documents\projects\algo-sim\.superpowers\worktrees\hybrid-backend-s3`
- **Active Branch:** `research/hybrid-backend-session3-contract-v2`
- **Current `HEAD`:** `42f19eecec0b43635c6f7809250b93249d79bf5d`
- **Running Background Subprocesses:** `0` (verified via `Win32_Process`).

---

## 1. Status Classification of Session 3 Checkpoints (`plan.md`)

### A. Đã triển khai và kiểm chứng (Implemented & Verified in Committed History)
1. **P1 Safety (`fe6ad30bea6aa90a4827befaf8091c6b3fdee505`)**:
   - Schema-level validation of `PremiseSpec.args` per premise kind (`INVALID_PREMISE_ARGS`) and `named_intersections` edge keys (`INVALID_DERIVED_SECTION`).
   - Public-boundary technical refusal (`ADAPTER_INTERNAL_ERROR` / `ROUTE_INTERNAL_ERROR`) for unexpected internal exceptions without disguising them as bad input; narrowed `_shared_source_gate` exception handler in `adapter3_simulation.py` to bridge parsing only.
   - Explicit engine-owned name set in `gop_doi_tuong_trung` (`engine.py`), never rewriting `label` or `kind` fields.
   - Mutation fuzz receipts (`verification/fuzz/p1-adapter3.json`, `p1-bridge.json`): `13,661` mutants per route, `0` escaped exceptions (down from `1,015`), `0` internal errors.
2. **P4a Locked Grammar & Contract-V2 Evaluation Set (`4268f4e214125fe20c858930bc92b0c5798dfc67`)**:
   - Preregistered `47`-case evaluation set (`grammar-set.json`, LF-normalized SHA-256 `10c57be7b485d7b3f1a97183ff41b28988e70641e297e01cccf68d1434cc4abe` locked in `grammar-set.lock.json`) committed before any `/2`, D6, or grammar changes: `22` `SERVE`, `19` `REFUSE_SOURCE`, `4` `REFUSE_GEOMETRY`, `2` `REFUSE_KERNEL`.
3. **P2 Canonical Contract `typed-fact-next/2` & Converter (`fa1599c657006317d482a4630f641a236defdcb0`)**:
   - `TypedFactNextV2Payload`, `DerivedPlaneSectionV2Spec`, `StatedIntersectionSpec` (`stated_intersections` with per-intersection quote inside section quote, optional `declared_boundary`, no `requires_closed_boundary` bypass flag).
   - Explicit route-labelled converter `convert_v1_to_v2(raw, route)` requiring `route in ("bridge", "adapter3")` (`ROUTE_LABEL_REQUIRED` otherwise); strict version separation (`SCHEMA_VERSION_MISMATCH` if `/1` and `/2` parsers cross).
4. **P3 Planner D6 (`DERIVED_FRESH` + Closure Certificate) & P5 Adapter `/4` (`42f19eecec0b43635c6f7809250b93249d79bf5d`)**:
   - `Registry /13`, `Planner /13`, `Engine /11`, `Bridge /2` (`typed-fact-next-bridge/2`), `Adapter /4` (`hybrid-simulation-adapter/4`, `hybrid-route-d-simulation/4` in `backend/app/ai/adapter4_route.py`).
   - `intersect_line_plane` carries a `PlanningContract` (effect `Meet`); planner derives unstated lateral cut vertices (`derived_fresh`, cost `2`, provenance `DERIVED_FRESH`) only on `/2` sections requiring closure (derived solid or declared boundary), with fresh labels hidden from learner text.
   - `chung_chi_khep_kin` in `engine.py` certifies closed cyclic boundaries (`cross_section`) and verifies `declared_boundary` (up to cyclic rotation/reversal).
   - Mutation fuzz receipt on `/2` (`verification/fuzz/p3-v2.json`): `19,114` mutants, `0` escaped exceptions, `0` internal errors.

### B. Đang triển khai dở (In Progress in Working Tree — Uncommitted)
5. **P4b Source Gate Grammar Expansion (`D3` — G7 checkpoint)**:
   - Uncommitted edits in `backend/app/simulation/geometry_functions/planner.py` (`+5` lines) and `backend/app/simulation/geometry_functions/registry.py` (`+88 / -20` lines), plus untracked `docs/evaluation/geometry/runs/hybrid-contract-v2/evaluate_grammar_set.py` and `verification/grammar/baseline-before-grammar.json`.
   - At `42f19eec` (before P4b grammar edits), `evaluate_grammar_set.py` scored `match: 34/47` (`SERVE: 11/22`).
   - With Claude's uncommitted P4b edits, `evaluate_grammar_set.py` improved to `match: 42/47` (`SERVE: 19/22`, `wrong_served: []`, `served_without_gate: []`), and crashed on console printing of `PARA-3` due to Windows `cp1252` `UnicodeEncodeError` right as Claude hit its session limit.

### C. Đã triển khai nhưng chưa kiểm chứng đầy đủ (Implemented, Pending Final Gate Verification)
- `test_d6_described_derived_pyramid_ratio_is_exact` in `backend/tests/geometry/test_hybrid_contract_v2.py` was marked `@pytest.mark.xfail(strict=True)` in `42f19eec` pending the D3 `_KHOI_MO_TA` change now present in the working tree (`XPASS` once pytest runs on the working tree).

### D. Chưa triển khai (Not Yet Executed)
- **Completion of P4b (`5` remaining mismatches in `evaluate_grammar_set.py`)**:
  1. `PARA-3`: point-first plane definition `"Qua M dựng mặt phẳng (α) song song với (ABC), (α) cắt SA, SB, SC, SD lần lượt tại M, N, P, Q."` (`_QUA_SONG_SONG` / `_QUA_VUONG_DUONG` only matchplane-first `Mặt phẳng (α) qua M ...`, not point-first `Qua M dựng mặt phẳng (α) ...`).
  2. `CORPUS-DEV09-construct`: `"Mặt phẳng (α) qua M và song song với (ABCD) cắt SB, SC, SD. Dựng thiết diện, khối chóp đỉnh S cắt bởi (α)."` (bare `"Dựng thiết diện"` without `"bởi (α)"` or `"của hình chóp"` when `(α)` is the sole section plane in the problem).
  3. `CORPUS-DEV10-prism-area`: `"Dựng lăng trụ, thiết diện bởi (α) và tính diện tích thiết diện."` (`_kiem_du_kien_cau_hoi` question-context stripping for `"Dựng lăng trụ, thiết diện bởi (α) và"` before `"tính diện tích thiết diện"`).
  4. `NEG-per-edge-same-name` (`INVALID_DERIVED_SECTION` classified as `EXTRACTION_FAILED` -> `REFUSE_OTHER` in `evaluate_grammar_set.py` instead of `REFUSE_SOURCE`, or duplicate intersection name check) & `KER-plane-equation` (`BRIDGE_UNSUPPORTED_PLANE_KIND` missing from `_NHOM["CAPABILITY"]` in `hybrid_preview.py`, causing `classify_refusal("BRIDGE_UNSUPPORTED_PLANE_KIND")` to return `FALLBACK` -> `REFUSE_OTHER` instead of `CAPABILITY` -> `REFUSE_KERNEL`!).
- **P6 IR Check**: Verify whether `mp_td_*` vs operand plane needs any change or is already within the `32`-declaration budget (`49/49` served in Session 2).
- **P7 Evaluation & Migration Readiness**: Full evaluation across families A–H, dual-run `/1` vs `/2`, and re-evaluation of the 20 migration gates (`docs/MIGRATION_CHECKLIST.md`).
- **P8 Independent Review, Candidate Freeze & Authoritative Full T3**: Run independent review on final Session 3 diff, freeze `EVALUATION_CANDIDATE.json` + `candidate_divergence.json`, and run Authoritative Full T3 once.
- **P9 Final Reports**: Write `SESSION3_FINAL_REPORT.md`, `CONTRACT_V2_IMPLEMENTATION_REPORT.md`, `SOURCE_GATE_COVERAGE_MATRIX.md`, `PLANNER_COMPOSITION_AND_REUSE_REPORT.md`, `BACKEND_MIGRATION_READINESS.md`, and `INDEPENDENT_REVIEW.md`.

### E. Blocker hiện tại
- **Không có architectural blocker** chặn hoàn thành Session 3 local research.

---

## 2. Forensic Answers to Section 2 Checkpoint (`Evaluate locked set after G7`)

1. **G7 là gate nào?**
   - Trong kế hoạch Session 3 (`P4b`), G7 là cổng kiểm chứng tập đánh giá ngữ pháp và hợp đồng V2 đã khóa (`grammar-set.json`) thông qua script `docs/evaluation/geometry/runs/hybrid-contract-v2/evaluate_grammar_set.py`.
2. **Locked set có bao nhiêu ca? Đã được khóa trước evaluation bằng commit/hash nào?**
   - Có **47 ca**, được khóa tại commit `4268f4e214125fe20c858930bc92b0c5798dfc67` trong `grammar-set.json` và `grammar-set.lock.json` với mã băm SHA-256 (chuẩn hóa LF): `10c57be7b485d7b3f1a97183ff41b28988e70641e297e01cccf68d1434cc4abe`.
3. **`match: 42` đo đại lượng gì?**
   - Số ca trong tổng số 47 ca mà lớp kết quả thực tế (`observed` ∈ `{SERVE, REFUSE_SOURCE, REFUSE_GEOMETRY, REFUSE_KERNEL}`) khớp chính xác với lớp kỳ vọng (`expected`) **và** nếu `SERVE` thì đáp số bình phương khớp 100% với oracle đóng (`wrong_served == False`).
4. **`19/22` là tỷ lệ SERVE nào và có bao nhiêu positive hợp lệ?**
   - Có **22 ca positive hợp lệ** (`expected == "SERVE"`). Tại thời điểm Claude dừng, `19/22` ca đã `SERVED` đúng đáp số tuyệt đối (tăng từ `11/22` ở `baseline-before-grammar.json`), `0` wrong serves (`wrong_served: []`), và `19/19` ca phục vụ đều đi qua `registry.kiem_nguon` (`served_without_gate: []`).
5. **Ba trường hợp positive chưa SERVE (`3/22`) và hai trường hợp lệch nhóm từ chối (`2/25`) có nguyên nhân gì?**
   - **3 ca `SERVE` chưa đạt:**
     - `PARA-3` (`SOURCE_OBJECT_MISMATCH`): câu định nghĩa mặt phẳng đặt điểm lên đầu (`"Qua M dựng mặt phẳng (α) song song với (ABC), (α) cắt SA, SB, SC, SD lần lượt tại M, N, P, Q."`) chưa có mẫu đóng trong `_QUA_SONG_SONG` / `_QUA_VUONG_DUONG`.
     - `CORPUS-DEV09-construct` (`SOURCE_OBJECT_MISMATCH`): câu yêu cầu `"Dựng thiết diện, khối chóp đỉnh S cắt bởi (α)."` viết tắt `"thiết diện"` không kèm `"bởi (α)"` ở vế đầu (dù vế sau cùng câu nêu rõ `"cắt bởi (α)"` và đề chỉ có duy nhất một mặt cắt `(α)`).
     - `CORPUS-DEV10-prism-area` (`QUESTION_CONTEXT_UNSUPPORTED`): câu `"Dựng lăng trụ, thiết diện bởi (α) và tính diện tích thiết diện."` có cụm `"Dựng lăng trụ, thiết diện bởi (α) và"` đứng trước `"tính diện tích thiết diện"` chưa được `_doc_phep_dung_cau_hoi` đánh dấu đã đọc.
   - **2 ca từ chối đúng trạng thái `REFUSED` nhưng lệch nhóm phân loại (`REFUSE_OTHER`):**
     - `KER-plane-equation`: mã `BRIDGE_UNSUPPORTED_PLANE_KIND` (và các mã `BRIDGE_UNSUPPORTED_*` khác của bridge) chưa được thêm vào tập `CAPABILITY` trong `backend/app/ai/hybrid_preview.py::_NHOM`, nên `classify_refusal` trả về `FALLBACK` (`REFUSE_OTHER`) thay vì `CAPABILITY` (`REFUSE_KERNEL`).
     - `NEG-per-edge-same-name`: câu `"cắt SB tại N, cắt SC tại N"` bị chặn ngay tại tầng schema `parse_typed_fact_next_v2` với mã `INVALID_DERIVED_SECTION` (thuộc nhóm `EXTRACTION_FAILED` في `hybrid_preview.py`) trước khi tới Source Gate.
6. **Evaluation đã kết thúc thành công hay chỉ in kết quả trung gian?**
   - Lần chạy của Claude đang là bước kiểm tra trong quá trình triển khai P4b và bị văng `UnicodeEncodeError` (do `cp1252` trên console Windows ở dòng 81 của `evaluate_grammar_set.py` khi in ký tự tiếng Việt trong `mismatches`).
