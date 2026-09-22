# BÁO CÁO WAVE: MODEL_VARIANCE_EVIDENCE_PROVENANCE_REPAIR_OFFLINE

## 1. TỔNG QUAN VÀ MỤC TIÊU

Wave **`MODEL_VARIANCE_EVIDENCE_PROVENANCE_REPAIR_OFFLINE`** hoàn thành việc kiểm tra, sửa chữa và củng cố toàn bộ lớp bằng chứng (provenance) của wave `MODEL_VARIANCE_EVIDENCE_REVIEW`.
Tất cả các con số, mã băm, exit code, và trạng thái kiểm thử được trích xuất trực tiếp từ máy thực thi thật (Git rev-parse, JUnit XML, manifest hai lượt độc lập), loại bỏ hoàn toàn các chuỗi khai báo cứng (`STATUS: "PASS"`, test counts hardcode) và xác định bản chất kỹ thuật của chuỗi commit `3ba5afbb...` bị ghép sai.

Wave này tuân thủ tuyệt đối nguyên tắc **100% OFFLINE**:
* `NEW_GEMINI_REQUESTS = 0`
* `NETWORK_REQUESTS = 0`
* `DOTENV_PRESENT = NO`
* `API_KEY_PRESENT = NO`
* `API_KEY_LOADED = NO`
* `PRODUCT_CODE_CHANGED = NO`
* `DEFAULT_MODE = LLM_ONLY`

---

## 2. AUDIT A — COMMIT IDENTITY VÀ LỊCH SỬ GIT

### 2.1. Phát hiện và Phân loại Chuỗi Ghép
Trong artifact `PRECHECK.json` của wave trước, commit 1 được ghi nhận là:
```text
3ba5afbbf46d37a222b5805453744e7506063b60
```
Kết quả kiểm chứng máy bằng `git rev-parse` trực tiếp:
* `git rev-parse --verify 3ba5afbb^{commit}` -> `3ba5afbbd6b6e22781b03f29563c9d1589780603` (exit code 0).
* `git rev-parse --verify 3ba5afbbf46d37a222b5805453744e7506063b60^{commit}` -> fatal: ambiguous argument (exit code 128).

**Bản chất nguyên nhân**:
Chuỗi sai được tạo ra do việc ghép thủ công short SHA `3ba5afbb` với 32 ký tự đuôi `f46d37a222b5805453744e7506063b60` lấy nhầm từ commit liền trước `934b4aebf46d37a222b5805453744e7506063b60`.

### 2.2. Kiểm tra Phả hệ (Ancestry) và Phân định Vai trò
* `git merge-base --is-ancestor d09331ea 3ba5afbb` -> Exit code 0 (Hợp lệ).
* `git merge-base --is-ancestor 3ba5afbb 63eb0640` -> Exit code 0 (Hợp lệ).
* `git rev-list --count d09331ea..63eb0640` -> 2 commits.
* Diff `d09331ea..3ba5afbb`: Thêm tooling `kind_aware_trace_evaluator.py`, test `test_model_variance_evidence_review.py` và cập nhật `docs/CODE_INDEX.md`.
* Diff `3ba5afbb..63eb0640`: Thêm báo cáo `docs/MODEL_VARIANCE_EVIDENCE_REVIEW.md` và 13 artifact JSON.

**Phán quyết định danh**:
```text
RECORDED_COMMIT_1 = 3ba5afbbf46d37a222b5805453744e7506063b60
ACTUAL_COMMIT_1 = 3ba5afbbd6b6e22781b03f29563c9d1589780603
RECORDED_EVIDENCE_COMMIT = 63eb06404ae94927228ca13c276ccf04bb9ea8c8
ACTUAL_EVIDENCE_COMMIT = 63eb06404ae94927228ca13c276ccf04bb9ea8c8
COMMIT_IDENTITY_CLASSIFICATION = COMMIT_ROLE_LABELING_ERROR
HISTORY_DRIFT = NO
```

---

## 3. AUDIT B & C — BẰNG CHỨNG MÁY CHO KIỂM THỬ VÀ FAULT INJECTIONS

### 3.1. Kết Quả PyTest Từ JUnit XML Thật
Toàn bộ số liệu kiểm thử được trích xuất từ JUnit XML tạo ra trong Clean Worktree A (`D:\tmp\mvep-machine-worktree`):
* **Focused Test Suite**:
  * Invocations: `test_model_variance_evidence_review.py` (20 tests) + `test_model_variance_evidence_provenance_repair.py` (16 tests).
  * Collected: **36**
  * Passed: **36**
  * Failed: **0**
  * Errors: **0**
  * Skipped: **0**
  * Exit code: **0**
  * JUnit XML SHA-256: `3c219c3ab81e1ec3c7c4a463fcf0092cd96843202736383b88dfc19b9bf15a3a`
* **Full Backend Suite**:
  * Invocations: `pytest backend/tests -q`
  * Collected: **5985**
  * Passed: **5984**
  * Failed: **0**
  * Errors: **0**
  * Skipped: **1**
  * Deselected: **1**
  * Exit code: **0**
  * Duration: **214.7723s**
  * JUnit XML SHA-256: `a36f82b9841569d4842637639809549fa97eb28d050b1507c472d86b6f19edbb`

### 3.2. Bằng Chứng Máy Cho 10 Phép Tiêm Lỗi (F1–F10)
Tất cả 10 phép tiêm lỗi bắt buộc được kiểm chứng trực tiếp từ JUnit test node và đạt trạng thái `CAUGHT_AND_PREVENTED`:
1. **F1**: `test_FI_01_get_input_tokens_default_zero` -> CAUGHT (chặn .get(..., 0)).
2. **F2**: `test_FI_02_usage_or_zero_object` -> CAUGHT (chặn zero-object).
3. **F3**: `test_FI_03_dung_common_keyset_cho_moi_kind` -> CAUGHT (kind-aware keyset).
4. **F4**: `test_FI_04_yeu_cau_plane_cho_perpendicular_lines` -> CAUGHT (loại bỏ plane ép buộc).
5. **F5**: `test_FI_05_yeu_cau_other_line_cho_perpendicular_line_plane` -> CAUGHT (loại bỏ other_line ép buộc).
6. **F6**: `test_FI_06_gan_defect_vao_accepted_relation` -> CAUGHT (bất biến accepted relation không defect).
7. **F7**: `test_FI_07_doi_historical_root_cause_thanh_canonical_valid` -> CAUGHT (chặn áp đặt root cause).
8. **F8**: `test_FI_08_doi_causality_confidence_thanh_high` -> CAUGHT (chặn ép confidence cao).
9. **F9**: `test_FI_09_sua_historical_artifact` -> CAUGHT (bảo vệ bất biến SHA-256 artifact lịch sử).
10. **F10**: `test_FI_10_luu_raw_model_value_vao_trace` -> CAUGHT (cổng redaction ngăn rò rỉ chuỗi raw).

Không có test nào bị skip, xfail, missing hoặc trùng lặp.

---

## 4. AUDIT D — CHỨNG MINH TẤT ĐỊNH (BITWISE DETERMINISM)

Generator correction artifacts được thực thi hai lượt hoàn toàn độc lập từ cùng một evidence bundle máy:
* Lượt A: `D:\tmp\mvep-generator-run-a` (15 files)
* Lượt B: `D:\tmp\mvep-generator-run-b` (15 files)
* Fileset Parity: **TRUE**
* Size Parity: **TRUE**
* SHA-256 Raw Parity: **TRUE**
* SHA-256 LF-Normalized Parity: **TRUE**

**Kết luận xác minh**:
```text
VERIFICATION_RESULT = PROVED_BITWISE_IDENTICAL_ACROSS_RUNS
```

---

## 5. AUDIT E — MA TRẬN BẰNG CHỨNG CLAIM PROVENANCE

Mọi claim mang tính chứng minh (`PROVED`) đều được gắn với nguồn máy, lệnh thực thi, exit code 0 và SHA-256 evidence hash cụ thể:
* Commit code tồn tại: `git rev-parse` -> PROVED
* Phả hệ hợp lệ: `git merge-base` -> PROVED
* Artifact nguồn bất biến (32/32): `git hash-object` -> PROVED
* Focused test suite (36/36): JUnit XML -> PROVED
* Full backend suite (5984/5984): JUnit XML -> PROVED
* F1–F10 tiêm lỗi: JUnit Test Nodes -> PROVED
* Determinism generator: So sánh 2 manifest -> PROVED
* Candidate hash không đổi (103 tệp): `freeze_evaluation_candidate.py --verify` -> PROVED
* Cache identity không đổi (99): `lock_cache_identity.py --verify` -> PROVED
* Secret scan (0 rò rỉ): `scan_secrets` -> PROVED
* Product parity không đổi: `git diff` -> PROVED

Các nhận định phương pháp luận được phân loại minh bạch:
* `HISTORICAL_ROOT_CAUSE`: `METHODOLOGICAL_POLICY` (`NOT_ESTABLISHED`)
* `CAUSALITY_CONFIDENCE`: `METHODOLOGICAL_POLICY` (`NOT_ESTABLISHED`)
* `MODEL_VARIANCE_HYPOTHESIS`: `METHODOLOGICAL_POLICY` (`CONSISTENT_WITH_CURRENT_EVIDENCE`)

Số lượng claim unsupported mang nhãn PROVED: **0**.

---

## 6. BẤT BIẾN KHO VÀ ĐẢM BẢO AN TOÀN

* **Candidate SHA-256**: `077dbc6b7bf6f62f7d07838696f5bcf71c74d3210ae65fbfc36683ee19e42bc1` (103 files verified, exit 0).
* **CACHE_VERSION**: `99` (exit 0).
* **Mainline**: `085cae67392d3607ad0a58a7f48c17d8a5e5157d` (không đổi).
* **Source working tree**: Chỉ bẩn bởi ` D frontend/public/favicon.svg` (giữ nguyên, không động chạm).
* **Secret scan**: 0 rò rỉ API key, 0 email cá nhân chưa redact, 0 forbidden raw keys.

---

## 7. KẾT LUẬN WAVE VÀ BƯỚC TIẾP THEO

* **Phán quyết wave**: **`PASS_WITH_LABEL_CORRECTION`**
* **Core outcome**: **`CORE_OUTCOME_VALID_WITH_MACHINE_VERIFIED_PROVENANCE`**
* **Next action**: **`DOCS_INFORMATION_ARCHITECTURE_AND_HANDOFF_HARDENING`**
