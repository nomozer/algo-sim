# SAFE_STRUCTURE_TRACE_REPAIR_EVIDENCE_RECONCILIATION

**2026-09-22** · Nhánh `feat/photo-problem-to-scene` · START_HEAD `efee245c` · `main` giữ `085cae6` ·
**0 Gemini request · 0 network request · 0 byte gửi ngoài · 0 API key loaded**

```text
DIAGNOSIS_WAVE                 SAFE_STRUCTURE_TRACE_REPAIR_EVIDENCE_RECONCILIATION
START_HEAD_EXPECTED            efee245c084cf58253928a31b8627745cdf0c85e
START_HEAD_ACTUAL              efee245c084cf58253928a31b8627745cdf0c85e
CODE_COMMIT                    866a1257bf85ad742ed61e65c77578e0f5373352
REPORT_BASE_HEAD               866a1257bf85ad742ed61e65c77578e0f5373352
EVIDENCE_COMMIT_ROLE           SELF
BRANCH_HEAD_OBSERVED           efee245c084cf58253928a31b8627745cdf0c85e
MAIN_HEAD                      085cae67392d3607ad0a58a7f48c17d8a5e5157d
COMMIT_IDENTITY_RESULT         COMMIT_ROLE_LABELING_ERROR
HISTORY_DRIFT                  NO
EVIDENCE_IDENTITY_RESULT       RECONCILED
LIVE_RETRY_ALLOWED             YES
STATUS                         PASS
NEXT_ACTION                    FRESH_PREREGISTERED_FAILURE_REPRODUCTION_RETRY
```

---

## 1. Tiền kiểm và Bất biến Kho mã

| Tiêu chí | Kỳ vọng | Thực tế | Trạng thái |
| :--- | :--- | :--- | :--- |
| **Branch** | `feat/photo-problem-to-scene` | `feat/photo-problem-to-scene` | `MATCH` |
| **START_HEAD** | `efee245c...` | `efee245c...` | `MATCH` |
| **main** | `085cae6...` | `085cae6...` | `MATCH` |
| **Source Working Tree** | Chỉ bẩn bởi `D frontend/public/favicon.svg` | Chỉ có `favicon.svg` | `PRESERVED` |
| **Candidate Verify** | `077dbc6b...` (103 files) | `077dbc6b...` (103 files) | `PASS` |
| **Cache Version** | `99` | `99` | `PASS` |
| **Tiến trình Live Chạy ngầm** | 0 | 0 | `NONE` |
| **Worktree Ghi Cùng Nhánh** | 0 | 0 | `NONE` |

---

## 2. Đối chiếu Đồ thị Commit & Phân loại Vai trò

### 2.1 Hiện tượng Bất nhất Ban đầu
- Báo cáo đã commit `docs/SAFE_STRUCTURE_TRACE_REPAIR_OFFLINE.md` ghi `END_HEAD = 866a1257bf85ad742ed61e65c77578e0f5373352`.
- Bảng tổng kết terminal sau commit ghi `END_HEAD = efee245c084cf58253928a31b8627745cdf0c85e`.

### 2.2 Kết quả Audit
Kiểm tra đồ thị bằng `git rev-list --parents`, `git show`, `git diff-tree`:
1. **Commit `866a1257`**:
   - Parent: `45702b36785d1260f306e5f844a8487945f540e6`.
   - Nội dung: `backend/scripts/run_preregistered_failure_reproduction.py`, `backend/tests/geometry/test_safe_structure_trace_repair_offline.py`, `docs/CODE_INDEX.md`.
   - Phân loại: **`CODE_COMMIT`** (hay `REPORT_BASE_HEAD`).
2. **Commit `efee245c`**:
   - Parent: `866a1257bf85ad742ed61e65c77578e0f5373352`.
   - Nội dung: `docs/SAFE_STRUCTURE_TRACE_REPAIR_OFFLINE.md`, 15 artifact JSON trong thư mục `safe-structure-trace-repair-offline/`.
   - Phân loại: **`EVIDENCE_COMMIT`**.
3. **Nguyên nhân cốt lõi**:
   - Giới hạn tự tham chiếu (`non-self-referential commit SHA`): Khi văn bản báo cáo được tạo và ghi ra đĩa trước khi commit, HEAD của cây làm việc là `866a1257`. Một commit không thể chứa trước SHA của chính nó. Do đó, việc báo cáo ghi `END_HEAD = 866a1257...` là do gán nhãn `CODE_COMMIT` thành `END_HEAD`.
4. **Kết luận**:
   - `COMMIT_IDENTITY_RESULT = COMMIT_ROLE_LABELING_ERROR` (Trường hợp A).
   - `HISTORY_DRIFT = NO`. Không có nhánh rẽ, không có rewrite lịch sử.

---

## 3. Đối chiếu Hash Thành phần & Chính sách Chuẩn hóa

### 3.1 Hiện tượng Bất nhất Hash
Báo cáo repair ghi nhận:
```text
MANIFEST_LF_SHA = 90efb22c...
GROUND_TRUTH_LF_SHA = df8d1a10...
PROMPT_SHA = 390317e3...
```
trong khi live/benchmark trước dùng:
```text
MANIFEST_SHA256 = e043903849ebd5799ac87e788bacea95e31277cbc528cff21060ff873e29b60a
GROUND_TRUTH_SHA256 = 115c0518a1997fa719500415d876a0a864a7fcb695170e88369e9ba9177793af
PROMPT_SHA256 = 50a076e15ed9189ab1e664d7d26f3a4b3450178802bc3826a3b4164e52d63500
SCHEMA_SHA256 = 0542161e56ecca5e224964200208be93a648af93a14f6e733c94dedef99c2b7b
```

### 3.2 Kết quả Audit Truy nguyên Bằng chứng
1. **Nội dung thực tế trên kho mã**:
   - `BENCHMARK_MANIFEST.json` (tại `docs/evaluation/geometry/photo-problem-to-scene/multicase-benchmark/`):
     - LF-normalized SHA-256 = `e043903849ebd5799ac87e788bacea95e31277cbc528cff21060ff873e29b60a` (**TRÙNG 100%**).
   - `GROUND_TRUTH.json` (tại `docs/evaluation/geometry/photo-problem-to-scene/multicase-benchmark/`):
     - LF-normalized SHA-256 = `115c0518a1997fa719500415d876a0a864a7fcb695170e88369e9ba9177793af` (**TRÙNG 100%**).
   - `geometry_analyze.md` (tại `backend/app/ai/skills/`):
     - LF-normalized SHA-256 = `50a076e15ed9189ab1e664d7d26f3a4b3450178802bc3826a3b4164e52d63500` (**TRÙNG 100%**).
   - `analyze_schema_for("hinh_hoc")` (từ `app.simulation.semantic_program.analyze_contract`):
     - Python sorted JSON SHA-256 = `0542161e56ecca5e224964200208be93a648af93a14f6e733c94dedef99c2b7b` (**TRÙNG 100%**).
   - `NEGATIVE_TARGETED_REJECTION_REGISTRY.json` (Registry v1):
     - LF-normalized SHA-256 = `52bc6379d2f01372513d5aa21bd25433ea27783edae416cc7a1ed95fa8bb7100` (**TRÙNG 100%**).
   - `NEGATIVE_TARGETED_REJECTION_REGISTRY_V2.json` (Registry v2):
     - LF-normalized SHA-256 = `03a87ba37a6df62604d33119f346101e1f9e6f10f8db63b6fdbff6ce40c07e81` (**TRÙNG 100%**).
2. **Nguồn gốc các chuỗi `90efb22c...`, `df8d1a10...`, `390317e3...`**:
   - Truy nguyên lịch sử trong `transcript.jsonl` (bước 935) chứng minh: khi tạo script cào artifact ở wave trước, agent đã hardcode các chuỗi hash tổng hợp giả định vào bảng precheck thay vì đọc và tính toán từ các file thực tế.
   - Không có bất kỳ tệp tin nào trong lịch sử kho mã từng mang các hash này.
   - **Phân loại**: `HISTORICAL_HASH_NOT_REPRODUCIBLE`.
   - **Nội dung tệp thực tế**: Tuyệt đối **KHÔNG BỊ DRIFT** (`CONTENT_DRIFT = NO`).

---

## 4. Ma trận Băm Toàn diện (Component Hash Matrix)

| Thành phần | Đường dẫn Kho | Cỡ (byte) | LE | SHA-256 LF / Git Blob | Hash Lịch sử Hợp lệ | Phân loại Đối chiếu |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Manifest** | `docs/.../multicase-benchmark/BENCHMARK_MANIFEST.json` | 4,385 | CRLF | `e043903849eb...` | `e043903849eb...` | `MATCH_SAME_FILE_SAME_POLICY` |
| **Ground Truth** | `docs/.../multicase-benchmark/GROUND_TRUTH.json` | 17,645 | CRLF | `115c0518a199...` | `115c0518a199...` | `MATCH_SAME_FILE_SAME_POLICY` |
| **Analyze Prompt** | `backend/app/ai/skills/geometry_analyze.md` | 5,764 | CRLF | `50a076e15ed9...` | `50a076e15ed9...` | `MATCH_SAME_FILE_SAME_POLICY` |
| **Analyze Schema** | `analyze_schema_for("hinh_hoc")` | 3,246 | LF | `0542161e56ec...` | `0542161e56ec...` | `MATCH_SAME_FILE_SAME_POLICY` |
| **Registry v1** | `docs/.../NEGATIVE_TARGETED_REJECTION_REGISTRY.json` | 3,948 | LF | `52bc6379d2f0...` | `52bc6379d2f0...` | `MATCH_SAME_FILE_SAME_POLICY` |
| **Registry v2** | `docs/.../NEGATIVE_TARGETED_REJECTION_REGISTRY_V2.json` | 3,137 | LF | `03a87ba37a6d...` | `03a87ba37a6d...` | `MATCH_SAME_FILE_SAME_POLICY` |
| **Safe Trace Contract** | `docs/.../SAFE_STRUCTURE_TRACE_CONTRACT.json` | 3,980 | LF | `b429618c8577...` | `b429618c8577...` | `MATCH_SAME_FILE_SAME_POLICY` |
| **Runner** | `backend/scripts/run_preregistered_failure_reproduction.py` | 55,848 | CRLF | `089de2103b49...` | `866a1257...` | `REPAIRED_IN_SCOPE` |

---

## 5. Kiểm tra Đối chiếu Thân Request Model-Facing

Dựng độc lập 2 lần từ HEAD hiện tại:
- **P03 Request Body SHA-256**:
  - Run 1: `6a2090edcc35c7819e808cd905dc0f6eda463dd5e88717d8cbb646a1f93aeca4`
  - Run 2: `6a2090edcc35c7819e808cd905dc0f6eda463dd5e88717d8cbb646a1f93aeca4`
  - So với đăng ký trước: **TRÙNG KHỚP 100%** (`P03_REQUEST_PARITY = MATCH`).
- **P05 Request Body SHA-256**:
  - Run 1: `8a1497359004583e876a5b88787a6d02beb851ac7d7057688351745c85b30b5a`
  - Run 2: `8a1497359004583e876a5b88787a6d02beb851ac7d7057688351745c85b30b5a`
  - So với đăng ký trước: **TRÙNG KHỚP 100%** (`P05_REQUEST_PARITY = MATCH`).

---

## 6. Đối chiếu Thống kê Pytest

Bất biến số học chuẩn hóa:
```text
SELECTED = PASSED + FAILED + SKIPPED + XFAILED + XPASSED + ERROR
INITIAL_COLLECTED = SELECTED + DESELECTED
```

Đối chiếu số liệu:
- `PYTEST_INITIAL_COLLECTED` = **5925**
- `PYTEST_DESELECTED` = **1**
- `PYTEST_SELECTED` = **5924** (5925 - 1)
- Trong worktree sạch tách biệt:
  - `PYTEST_PASSED` = **5923**
  - `PYTEST_SKIPPED` = **1**
  - `PYTEST_FAILED` = **0**
  - `PYTEST_EXIT_CODE` = **0**
  - `5923 + 1 + 0 = 5924` (Khớp tuyệt đối!).
- Trong cây làm việc repo chính (bảo toàn favicon dirty):
  - `PYTEST_PASSED` = **5922**
  - `PYTEST_SKIPPED` = **1**
  - `PYTEST_FAILED` = **1** (`test_bao_cao_da_sinh_va_KHONG_TROI` bắt buộc `cay_sach == True`)
  - `5922 + 1 + 1 = 5924` (Khớp tuyệt đối!).

Giải thích bất nhất cũ: Báo cáo wave trước ghi `FULL_BACKEND_COLLECTED = 5925` và `PASSED = 5924`, nhầm lẫn `SELECTED` (5924) thành `PASSED`, dẫn tới tổng lệch 1 đơn vị. Bất biến nay đã được chỉnh lý hoàn toàn.

---

## 7. Bảo toàn Lịch sử và Lớp Đính chính Mới

- `HISTORICAL_REPORT_CHANGED = NO`: Tệp `docs/SAFE_STRUCTURE_TRACE_REPAIR_OFFLINE.md` và 15 artifact của wave repair được bảo toàn nguyên vẹn 100% từng byte (xem `HISTORICAL_IMMUTABILITY.json`).
- `CORRECTION_LAYER_CREATED = YES`: Toàn bộ bằng chứng đối chiếu được đặt tại:
  `docs/evaluation/geometry/photo-problem-to-scene/safe-structure-trace-repair-evidence-reconciliation/`

---

## 8. Kết quả 10 Phép Tiêm Lỗi (Fault Injections)

- `FI-01` (Đổi 1 byte manifest): Bị bắt bởi `test_FI_01_doi_mot_byte_manifest`.
- `FI-02` (Đổi line ending): Bị bắt bởi `test_FI_02_doi_line_ending_nhung_giu_noi_dung_lf`.
- `FI-03` (Tráo path manifest/ground truth): Bị bắt bởi `test_FI_03_trao_path_manifest_ground_truth`.
- `FI-04` (Gắn nhãn code commit thành END_HEAD): Bị bắt bởi `test_FI_04_gan_nhan_code_commit_thanh_end_head`.
- `FI-05` (Đưa commit ngoài branch vào lineage): Bị bắt bởi `test_FI_05_dua_commit_ngoai_branch`.
- `FI-06` (Khai COLLECTED bằng SELECTED): Bị bắt bởi `test_FI_06_khai_collected_bang_selected`.
- `FI-07` (Sửa báo cáo lịch sử): Bị bắt bởi `test_FI_07_sua_historical_report`.
- `FI-08` (Sửa request body): Bị bắt bởi `test_FI_08_doi_request_body`.
- `FI-09` (Nạp .env): Bị bắt bởi `test_FI_09_nap_dotenv`.
- `FI-10` (Gọi network không budget): Bị bắt bởi `test_FI_10_goi_network`.

---

## 9. Báo cáo Chuẩn hóa Mục 14

```text
SAFE_STRUCTURE_TRACE_REPAIR_EVIDENCE_RECONCILIATION
BRANCH = feat/photo-problem-to-scene
START_HEAD_EXPECTED = efee245c084cf58253928a31b8627745cdf0c85e
START_HEAD_ACTUAL = efee245c084cf58253928a31b8627745cdf0c85e
CODE_COMMIT = 866a1257bf85ad742ed61e65c77578e0f5373352
REPORT_BASE_HEAD = 866a1257bf85ad742ed61e65c77578e0f5373352
EVIDENCE_COMMIT_ROLE = SELF
BRANCH_HEAD_OBSERVED_BEFORE_COMMIT = efee245c084cf58253928a31b8627745cdf0c85e
FINAL_END_HEAD = ghi_trong_output_sau_commit
MAIN_HEAD_BEFORE/AFTER = 085cae6 / 085cae6
COMMIT_IDENTITY_RESULT = COMMIT_ROLE_LABELING_ERROR
HISTORY_DRIFT = NO
MANIFEST_PATH = docs/evaluation/geometry/photo-problem-to-scene/multicase-benchmark/BENCHMARK_MANIFEST.json
MANIFEST_HASH_POLICY = LF_NORMALIZED_SHA256
MANIFEST_HASH_RESULT = e043903849ebd5799ac87e788bacea95e31277cbc528cff21060ff873e29b60a
GROUND_TRUTH_PATH = docs/evaluation/geometry/photo-problem-to-scene/multicase-benchmark/GROUND_TRUTH.json
GROUND_TRUTH_HASH_POLICY = LF_NORMALIZED_SHA256
GROUND_TRUTH_HASH_RESULT = 115c0518a1997fa719500415d876a0a864a7fcb695170e88369e9ba9177793af
PROMPT_PATH = backend/app/ai/skills/geometry_analyze.md
PROMPT_HASH_POLICY = LF_NORMALIZED_SHA256
PROMPT_HASH_RESULT = 50a076e15ed9189ab1e664d7d26f3a4b3450178802bc3826a3b4164e52d63500
SCHEMA_PATH = backend/app/simulation/semantic_program/analyze_contract.py:analyze_schema_for('hinh_hoc')
SCHEMA_HASH_POLICY = JSON_SORT_KEYS_PYTHON_SERIALIZATION
SCHEMA_HASH_RESULT = 0542161e56ecca5e224964200208be93a648af93a14f6e733c94dedef99c2b7b
P03_REQUEST_BODY_SHA256 = 6a2090edcc35c7819e808cd905dc0f6eda463dd5e88717d8cbb646a1f93aeca4
P03_REQUEST_PARITY = MATCH
P05_REQUEST_BODY_SHA256 = 8a1497359004583e876a5b88787a6d02beb851ac7d7057688351745c85b30b5a
P05_REQUEST_PARITY = MATCH
PYTEST_INITIAL_COLLECTED = 5925
PYTEST_DESELECTED = 1
PYTEST_SELECTED = 5924
PYTEST_PASSED = 5923 (clean worktree) / 5922 (source tree)
PYTEST_SKIPPED = 1
PYTEST_FAILED = 0 (clean worktree) / 1 (source tree)
PYTEST_EXIT_CODE = 0
HISTORICAL_REPORT_CHANGED = NO
CORRECTION_LAYER_CREATED = YES
NEW_GEMINI_REQUESTS = 0
NETWORK_REQUESTS = 0
API_KEY_LOADED = NO
PRODUCT_CODE_CHANGED = NO
RUNNER_CHANGED = NO
PROMPT_CHANGED = NO
SCHEMA_CHANGED = NO
FACT_GRAPH_CHANGED = NO
COMPILER_CHANGED = NO
CANDIDATE_HASH_BEFORE/AFTER = 077dbc6b7bf6f62f7d07838696f5bcf71c74d3210ae65fbfc36683ee19e42bc1 / 077dbc6b7bf6f62f7d07838696f5bcf71c74d3210ae65fbfc36683ee19e42bc1
CACHE_VERSION_BEFORE/AFTER = 99 / 99
FAULT_INJECTIONS = 10/10 CAUGHT
SECRET_LEAKS = 0
COMMITS_CREATED = 1
USER_FAVICON_DELETION_PRESERVED = YES
SOURCE_WORKING_TREE = DIRTY_ONLY_USER_FAVICON
VERIFICATION_WORKTREE_STATUS = CLEAN_AND_REMOVED
EVIDENCE_IDENTITY_RESULT = RECONCILED
LIVE_RETRY_ALLOWED = YES
MERGE_ALLOWED = NO
```
