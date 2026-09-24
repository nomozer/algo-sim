# BÁO CÁO WAVE: DOCS_INFORMATION_ARCHITECTURE_AND_HANDOFF_HARDENING

## 1. TỔNG QUAN VÀ TRẠNG THÁI BẮT BUỘC

Wave **`DOCS_INFORMATION_ARCHITECTURE_AND_HANDOFF_HARDENING`** chuẩn hóa toàn diện hệ thống tài liệu và quy trình handoff của AlgoSim. Sau đợt củng cố này, bất kỳ agent hay phiên làm việc mới nào cũng có thể xác định ngay lập tức:
* Hệ thống hiện tại đang làm được gì và đang ở trạng thái nào;
* Kiến trúc hiện tại (`LLM_ONLY` mặc định), lát cắt thử nghiệm compiler, và kiến trúc đích (`compiler-first`);
* Bằng chứng nào còn hiệu lực, báo cáo nào đã được chuỗi sửa đổi (correction chain) đính chính;
* Những vấn đề kỹ thuật nào còn đang mở và kế hoạch giải quyết;
* Bước tiếp theo duy nhất là gì;
* File nào là nguồn sự thật chuẩn tắc (canonical source of truth) cho từng loại thông tin.

### Trạng thái căn bản và vai trò commit
```text
WAVE_ID = DOCS_INFORMATION_ARCHITECTURE_AND_HANDOFF_HARDENING
BRANCH = feat/photo-problem-to-scene
START_HEAD = 2678cc653f702e06620f49ae8069e46d418bfd55
MAIN_HEAD = 085cae67392d3607ad0a58a7f48c17d8a5e5157d
DOCUMENTATION_BASE_HEAD = 34c36872d70245a8f294e4ca9cbf5a975990914a
REPORT_COMMIT_ROLE = SELF
DATE = 2026-09-22
VERIFICATION_MODE = 100% OFFLINE
```

### Bất biến vận hành (100% Offline)
* `NEW_GEMINI_REQUESTS = 0`
* `NETWORK_REQUESTS = 0`
* `DOTENV_PRESENT = NO`
* `API_KEY_LOADED = NO`
* `PRODUCT_CODE_CHANGED = NO`
* `PROMPT_CHANGED = NO`
* `SCHEMA_CHANGED = NO`
* `FACT_GRAPH_CHANGED = NO`
* `COMPILER_CHANGED = NO`
* `LIVE_RUNNER_CHANGED = NO`
* `DEFAULT_MODE = LLM_ONLY`
* `CANDIDATE_SHA256 = 077dbc6b7bf6f62f7d07838696f5bcf71c74d3210ae65fbfc36683ee19e42bc1` (103 tệp được kiểm tra bitwise)
* `CACHE_VERSION = 99`

---

## 2. PHASE -1 — DOCUMENTATION OWNERSHIP VÀ REFERENCE AUDIT

### 2.1. Kiểm kê tài liệu (Doc Inventory)
Đã rà soát toàn bộ tài liệu hiện hữu trong kho:
* **Tài liệu căn bản**: 13 tệp Markdown tại root và `docs/`.
* **Báo cáo wave lịch sử**: 15 báo cáo wave trong `docs/`.
* **Thư mục artifact lịch sử**: 16 thư mục wave trong `docs/evaluation/`.
* **Hiện tượng chồng lấn trước khi chuẩn hóa**:
  * `docs/RULES.md` chứa HEAD commit động, candidate hash, cache version, danh sách open issue thay vì quy tắc ổn định.
  * `docs/CURRENT_STATE.md` sao chép lặp lại toàn bộ lịch sử wave từ `STATUS_LEDGER.md`.
  * Không có `AGENTS.md` tại root kho lưu trữ để làm điểm chạm khởi đầu cho công cụ và agent.
  * Thiếu `docs/README.md` đóng vai trò bảng điều hướng trung tâm.
  * Thiếu `docs/ROADMAP.md`, `docs/OPEN_ISSUES.md`, `docs/MIGRATION_CHECKLIST.md`, `docs/AI_CONTEXT_BUNDLE.md`, `docs/EVIDENCE_INDEX.md`.
  * `docs/CODE_INDEX.md` chứa đường dẫn tham chiếu đến các tệp đã gỡ bỏ trong các wave trước mà chưa có nhãn `HISTORICAL_REMOVED`.

### 2.2. Ma trận 11 Miền Canonical và Phân quyền Sở hữu Độc quyền

| Miền (Domain) | Tệp Canonical | Trách nhiệm Duy nhất (Single Ownership) | Loại Nội dung Được phép |
|---|---|---|---|
| `AGENT_RULES` | `docs/RULES.md` (pointer `AGENTS.md`) | Quy tắc bất biến, thứ tự đọc tài liệu, lệnh cấm kỹ thuật, chính sách an toàn | Ổn định (Stable) |
| `ARCHITECTURE` | `docs/ARCHITECTURE_MAP.md` | Bản đồ kiến trúc, luồng pipeline, ranh giới LLM vs Deterministic Compiler | Bán ổn định (Semi-stable) |
| `CURRENT_STATE` | `docs/CURRENT_STATE.md` | Trạng thái hiện tại của nhánh, base commit, năng lực đã kiểm chứng, next action | Động (Mutable) |
| `STATUS_LEDGER` | `docs/STATUS_LEDGER.md` | Sổ cái lịch sử toàn bộ các wave phát triển, commit hash, kết quả, phân loại | Động (Append-only) |
| `CODE_INDEX` | `docs/CODE_INDEX.md` | Bản chỉ mục các tệp mã nguồn, kiểm thử, công cụ, cấu hình và tệp lịch sử | Bán ổn định (Semi-stable) |
| `ROADMAP` | `docs/ROADMAP.md` | Kế hoạch tương lai, các tầng ưu tiên P0–P6, điều kiện tiên quyết và mục tiêu | Động (Mutable) |
| `OPEN_ISSUES` | `docs/OPEN_ISSUES.md` | Danh sách vấn đề kỹ thuật đang mở, mã định danh ổn định, phân loại, wave kế tiếp | Động (Mutable) |
| `MIGRATION_CHECKLIST` | `docs/MIGRATION_CHECKLIST.md` | 20 cổng kiểm tra di chuyển sang kiến trúc compiler-first | Động (Mutable) |
| `AI_HANDOFF` | `docs/AI_CONTEXT_BUNDLE.md` | Tệp bàn giao cô đọng (<= 300 dòng) dành riêng cho LLM/agent khi khởi động | Động (Mutable) |
| `EVIDENCE_INDEX` | `docs/EVIDENCE_INDEX.md` | Chỉ mục bằng chứng đánh giá, báo cáo wave, chuỗi đính chính (correction chains) | Động (Append-only) |
| `DOCS_NAVIGATION` | `docs/README.md` | Trung tâm điều hướng tài liệu, mục lục 11 miền, thứ tự đọc cho phiên mới | Ổn định (Stable) |

**Kết quả giải quyết xung đột**:
* `OWNERSHIP_COLLISION_COUNT_BEFORE = 3`
* `OWNERSHIP_COLLISION_COUNT_AFTER = 0`
* `CONDITIONAL_FILES_PROPOSED = 7`
* `FILES_CREATED = 7` (`AGENTS.md`, `docs/ROADMAP.md`, `docs/OPEN_ISSUES.md`, `docs/MIGRATION_CHECKLIST.md`, `docs/AI_CONTEXT_BUNDLE.md`, `docs/EVIDENCE_INDEX.md`, `docs/README.md`)
* `FILES_UPDATED = 5` (`docs/RULES.md`, `docs/ARCHITECTURE_MAP.md`, `docs/CURRENT_STATE.md`, `docs/STATUS_LEDGER.md`, `docs/CODE_INDEX.md`)
* `FILES_NOT_CREATED_DUE_TO_EXISTING_EQUIVALENT = 0`

---

## 3. PHASE 0 — ĐỐI SOÁT VÀ HÀI HÒA BẰNG CHỨNG KIỂM THỬ (TEST EVIDENCE RECONCILIATION)

Trong wave `MODEL_VARIANCE_EVIDENCE_PROVENANCE_REPAIR_OFFLINE`, bằng chứng máy đã được thu thập độc lập qua hai commit liên tiếp:
1. `CODE_HEAD` (`18704f145cf35029a888c3a9d9e607c3906371df`): Thêm tooling và test harness.
2. `END_HEAD` (`2678cc653f702e06620f49ae8069e46d418bfd55`): Bổ sung báo cáo và correction layer artifacts.

### 3.1. Phân định Invocations và SHA-256 JUnit XML
* **Focused Test Suite** (`test_model_variance_evidence_review.py` + `test_model_variance_evidence_provenance_repair.py`):
  * `CODE_HEAD_FOCUSED_JUNIT_SHA256`: `955d5be51888496739bb5cba896f3068e52a806cbf18a8b163306dbddc360be8` (36 passed, exit code 0).
  * `END_HEAD_FOCUSED_JUNIT_SHA256`: `3c219c3ab81e1ec3c7c4a463fcf0092cd96843202736383b88dfc19b9bf15a3a` (36 passed, exit code 0).
* **Full Backend Suite** (`pytest backend/tests -q`):
  * `CODE_HEAD_FULL_JUNIT_SHA256`: `a9307d083d06eb4f85e5094dbe1513e9a4f4d2f8cb8b77dcf95eb7f7b3c2e171` (5984 passed, 1 skipped, exit code 0).
  * `END_HEAD_FULL_JUNIT_SHA256`: `a36f82b9841569d4842637639809549fa97eb28d050b1507c472d86b6f19edbb` (5984 passed, 1 skipped, exit code 0).

### 3.2. Giải trình Số học Thu thập và Bỏ chọn Kiểm thử (Test Count Invariant)
* **Số ca kiểm thử được Pytest phát hiện (collected)**: `5985`.
* **Số ca kiểm thử được chọn thực thi (selected)**: `5984`.
* **Số ca kiểm thử bị bỏ chọn qua đánh dấu cấu hình (deselected/skipped)**: `1` (test node: `test_agent_memory_runs_end_to_end_if_enabled`, yêu cầu cờ môi trường riêng).
* **Kết quả thực thi**: `5984 passed, 0 failed, 0 errors, 1 skipped/deselected`.
* **Đẳng thức bất biến**:
  $$\text{INITIAL\_COLLECTED } (5985) = \text{SELECTED } (5984) + \text{DESELECTED } (1)$$
  $$\text{TOTAL\_XML\_CASES } (5985) = \text{PASSED } (5984) + \text{SKIPPED } (1)$$
* **Phán quyết đối soát**: `TEST_COUNT_INVARIANT = HOLDS_TRUE`. Toàn bộ dữ liệu kiểm thử từ wave trước hoàn toàn nhất quán và được giải trình minh bạch.

---

## 4. CHI TIẾT CỦNG CỐ CÁC MIỀN TÀI LIỆU (CANONICAL DOMAINS)

### 4.1. AGENT_RULES Domain
* **Điểm tiếp cận**: `AGENTS.md` được tạo tại root repository, đóng vai trò hướng dẫn đọc đầu tiên (read order), liệt kê các tệp canonical, và áp đặt lệnh cấm can thiệp tệp bẩn `frontend/public/favicon.svg`.
* **Quy tắc ổn định**: `docs/RULES.md` được loại bỏ toàn bộ dữ liệu biến đổi động (không còn chứa mutable HEAD SHA, candidate hash, cache version, danh sách bug tạm thời). Mọi lệnh cấm kiến trúc (như `NEW_GEMINI_REQUESTS = 0` trong wave offline, cấm can thiệp schema trong giai đoạn freeze, cấm sửa `favicon.svg`) được quy chuẩn hóa.

### 4.2. ARCHITECTURE Domain
* `docs/ARCHITECTURE_MAP.md` được cập nhật Mục 2 làm rõ luồng đường ống chuẩn:
  $$\text{Input} \longrightarrow \text{Analyze LLM} \longrightarrow \text{RequestContract + structured relations} \longrightarrow \text{FactGraph}$$
  $$\longrightarrow \text{Deterministic Compiler (nếu eligible)} \longrightarrow \text{Semantic Program} \longrightarrow \text{Scene Builder}$$
  $$\longrightarrow \text{Visual Obligation Gate} \longrightarrow \text{Frontend Step Replay}$$
* Phân định rõ 3 trạng thái kiến trúc:
  1. **Hiện tại mặc định**: `LLM_ONLY` (toàn bộ các ca toán đều được giải qua Gemini qua prompt + structured schema).
  2. **Lát cắt thử nghiệm**: Primitive compiler song song chỉ kích hoạt khi FactGraph thỏa mãn điều kiện tiên quyết của họ hình học đã đăng ký.
  3. **Kiến trúc đích**: Compiler-first (Deterministic compiler phân tích quan hệ FactGraph trước; chỉ gọi LLM hỗ trợ khi FactGraph thiếu liên kết hoặc bài toán chứa yếu tố phi chuẩn).

### 4.3. CURRENT_STATE Domain
* `docs/CURRENT_STATE.md` thiết lập căn cứ trạng thái:
  * `PRODUCT_AND_EVIDENCE_BASE_HEAD = 2678cc653f702e06620f49ae8069e46d418bfd55`
  * `DOCUMENTATION_COMMIT_ROLE = SELF`
* Bảng đồng bộ danh tính được xác minh: 11 phép dựng, 8 câu lệnh, 7 phép đo, `CACHE_VERSION = 99`.
* Thiết lập hành động tiếp theo chuẩn tắc duy nhất: `PRIMITIVE_COMPILER_SECOND_FAMILY_SELECTION_AND_PREREGISTRATION`.

### 4.4. STATUS_LEDGER Domain
* `docs/STATUS_LEDGER.md` được cập nhật Mục 6, bổ sung đầy đủ 12 wave gần nhất từ 2026-09-17 đến 2026-09-22 với 11 trường thông tin chuẩn (`WAVE_ID`, `DATE`, `START_BASE`, `CODE_COMMIT_OR_NONE`, `EVIDENCE_COMMIT_ROLE`, `CLASSIFICATION`, `PRODUCT_CHANGED`, `MODEL_REQUESTS`, `REPORT_PATH`, `ARTIFACT_PATH`, `CORRECTED_BY`, `NEXT_ACTION_AT_TIME`).

### 4.5. CODE_INDEX Domain
* `docs/CODE_INDEX.md` được đồng bộ hóa hoàn toàn:
  * Các đường dẫn tệp tin lịch sử bị xóa trong các đợt dọn dẹp trước được đưa vào các mục có nhãn `HISTORICAL_REMOVED`.
  * Đánh chỉ mục chính xác các công cụ audit mới (`backend/scripts/audit_docs_information_architecture.py`), bộ test (`backend/tests/geometry/test_docs_information_architecture.py`), và toàn bộ các tệp tài liệu canonical mới.

### 4.6. ROADMAP Domain
* `docs/ROADMAP.md` được xây dựng với cấu trúc phân tầng nghiêm ngặt từ P0 đến P6:
  * **P0**: Ổn định kiến trúc tài liệu (wave hiện tại).
  * **P1**: Lựa chọn và tiền đăng ký họ hình học thứ hai cho compiler (`PRIMITIVE_COMPILER_SECOND_FAMILY_SELECTION_AND_PREREGISTRATION`).
  * **P2**: Triển khai deterministic compiler cho họ hình học thứ hai.
  * **P3**: Tích hợp routing tự động FactGraph -> Compiler/LLM.
  * **P4**: Củng cố Frontend Visual Obligation Replay.
  * **P5**: Tối ưu hóa hiệu năng và bộ nhớ.
  * **P6**: Mở rộng toàn diện các dạng bài toán hình học phức hợp.

### 4.7. OPEN_ISSUES Domain
* `docs/OPEN_ISSUES.md` tập hợp 13 vấn đề kỹ thuật có mã định danh ổn định (`ISSUE-ARCH-*`, `ISSUE-EVAL-*`, `ISSUE-DOCS-*`, `ISSUE-OPS-*`), mô tả rõ bản chất, mức độ nghiêm trọng, bằng chứng, và wave dự kiến giải quyết.

### 4.8. MIGRATION_CHECKLIST Domain
* `docs/MIGRATION_CHECKLIST.md` thiết lập 20 cổng kiểm soát quá trình chuyển dịch từ `LLM_ONLY` sang `compiler-first`, quy định rõ trạng thái boolean, tệp bằng chứng, blocker, và bài test tiếp theo.

### 4.9. AI_HANDOFF Domain
* `docs/AI_CONTEXT_BUNDLE.md` được đóng gói cô đọng trong **89 dòng** (tiêu chuẩn: $\le 300$ dòng), bao gồm 12 mục then chốt: định danh dự án, quy tắc vàng, trạng thái nhánh, tệp canonical, lệnh kiểm tra, kiến trúc luồng dữ liệu, phân loại lỗi, bằng chứng máy, và bước tiếp theo duy nhất.

### 4.10. EVIDENCE_INDEX Domain
* `docs/EVIDENCE_INDEX.md` hệ thống hóa toàn bộ báo cáo wave, thư mục artifact, và chuỗi đính chính ba tầng:
  $$\text{LIVE\_RETRY } (\text{FAIL}) \longrightarrow \text{EVIDENCE\_REVIEW } (\text{LABEL\_ERROR}) \longrightarrow \text{PROVENANCE\_REPAIR } (\text{PASS})$$

### 4.11. DOCS_NAVIGATION Domain
* `docs/README.md` đóng vai trò bản đồ chỉ dẫn tổng thể cho kho tài liệu, thiết lập trình tự đọc tài liệu cho các phiên làm việc và agent mới.

---

## 5. CÔNG CỤ AUDIT VÀ BỘ KIỂM THỬ TỰ ĐỘNG

### 5.1. Công cụ Kiểm tra Kiến trúc Tài liệu (`backend/scripts/audit_docs_information_architecture.py`)
Công cụ được xây dựng độc lập, hỗ trợ cả cờ `--strict` và chế độ thư viện, tự động kiểm tra 10 khía cạnh kiến trúc:
1. **Kiểm kê và Phân quyền**: Đảm bảo 11 miền tồn tại, đúng vị trí và không trùng quyền sở hữu.
2. **Toàn vẹn Liên kết**: Quét toàn bộ liên kết nội bộ `[text](path)` trong các tệp canonical, phát hiện liên kết gãy hoặc sai tệp.
3. **Đồng bộ Chỉ mục Mã nguồn**: So khớp `docs/CODE_INDEX.md` với cây thư mục thật của kho; cảnh báo tệp thiếu hoặc tệp stale không có nhãn `HISTORICAL_REMOVED`.
4. **Sổ cái Không Trùng lặp**: Xác thực toàn bộ các wave trong `docs/STATUS_LEDGER.md` có định danh duy nhất.
5. **Chỉ mục Bằng chứng**: Xác thực các báo cáo và thư mục artifact trong `docs/EVIDENCE_INDEX.md` đều tồn tại trên ổ đĩa.
6. **Danh sách Vấn đề Mở**: Kiểm tra tính duy nhất của mã định danh issue (`ISSUE-*`) và định dạng cấu trúc.
7. **Hành động Tiếp theo Chuẩn tắc**: Đối chiếu hành động duy nhất giữa `CURRENT_STATE.md`, `ROADMAP.md`, và `AI_CONTEXT_BUNDLE.md`.
8. **Tách biệt Ổn định / Động**: Đảm bảo `docs/RULES.md` không rò rỉ HEAD commit động hay cache version biến đổi.
9. **Quét Bí mật (Secret Scan)**: Quét toàn bộ kho tài liệu, đảm bảo không có API key hay thông tin nhạy cảm.
10. **Cân đối Số học Kiểm thử**: Kiểm tra tính toàn vẹn của đẳng thức số lượng test từ Phase 0.

### 5.2. Bộ Kiểm thử Tự động (`backend/tests/geometry/test_docs_information_architecture.py`)
Bộ kiểm thử gồm **36 bài test**, chia làm hai nhóm:
* **22 Bài test Bất biến (Invariants)**: Xác nhận sự tồn tại, đúng định dạng, không có liên kết hỏng, độ dài bundle $\le 300$ dòng, và sự đồng thuận của hành động tiếp theo.
* **14 Bài test Tiêm lỗi (Fault Injections F1–F14)**: Kiểm chứng công cụ audit phát hiện chính xác mọi vi phạm giả lập:
  * `F1`: Miền sở hữu bị mất hoặc sai tên file -> Phát hiện lỗi.
  * `F2`: Liên kết nội bộ trỏ tới tệp không tồn tại -> Báo broken link.
  * `F3`: Tệp mã nguồn biến mất khỏi đĩa nhưng vẫn ghi trong `CODE_INDEX` mà không có nhãn `HISTORICAL_REMOVED` -> Báo stale path.
  * `F4`: Tệp mới tạo trên đĩa nhưng không được đưa vào `CODE_INDEX` -> Báo unindexed path.
  * `F5`: Hai wave trong `STATUS_LEDGER` trùng lặp `WAVE_ID` -> Báo duplicate wave.
  * `F6`: Báo cáo wave hoặc artifact trong `EVIDENCE_INDEX` không tồn tại -> Báo missing evidence.
  * `F7`: Hai issue trong `OPEN_ISSUES` trùng lặp mã -> Báo duplicate issue.
  * `F8`: `CURRENT_STATE.md` và `ROADMAP.md` tuyên bố hai hành động tiếp theo khác nhau -> Báo divergence.
  * `F9`: `docs/RULES.md` chứa chuỗi SHA động -> Báo mutable leakage.
  * `F10`: Chèn chuỗi giả định API key vào tài liệu -> Quét bí mật báo vi phạm.
  * `F11`: Số liệu `PASSED + SKIPPED` không khớp với `TOTAL` trong Phase 0 -> Báo arithmetic mismatch.
  * `F12`: Cổng kiểm tra trong `MIGRATION_CHECKLIST` thiếu trường dữ liệu bắt buộc -> Báo invalid checklist.
  * `F13`: `AI_CONTEXT_BUNDLE.md` vượt quá giới hạn 300 dòng -> Báo line count overflow.
  * `F14`: Lệnh sửa đổi trái phép tệp bẩn `frontend/public/favicon.svg` -> Báo vi phạm bảo tồn working tree.

---

## 6. KẾT QUẢ THỰC THI KIỂM THỬ VÀ BẰNG CHỨNG MÁY

### 6.1. Kết quả Kiểm thử
* `backend/scripts/audit_docs_information_architecture.py`: **PASS** (10/10 tiêu chí).
* `pytest backend/tests/geometry/test_docs_information_architecture.py`: **36 passed in 3.71s** (exit code 0).
* `Focused Test Suite` (`test_rules_hygiene.py`, `test_doc_contracts.py`, `test_docs_information_architecture.py`): **75 passed** (exit code 0).
* `Frontend Hygiene Tests` (`npm test src/__tests__/code-index-sync.test.ts src/__tests__/rules-hygiene.test.ts`): **8 passed** (exit code 0).
* `Full Backend Suite` (`pytest backend/tests -q`): **5984 passed, 1 skipped** (exit code 0).

### 6.2. Danh mục 17 Artifacts JSON Sinh ra tại Thư mục Wave
Toàn bộ 17 artifact được lưu trữ tại:
`docs/evaluation/geometry/photo-problem-to-scene/docs-information-architecture-handoff-hardening/`

1. `PRECHECK.json`: Trạng thái môi trường, git SHA, và xác nhận 100% offline.
2. `DOC_INVENTORY.json`: Danh mục toàn bộ 44 tệp và thư mục tài liệu được kiểm kê.
3. `DOCUMENTATION_OWNERSHIP_AND_REFERENCE_AUDIT.json`: Báo cáo phân bổ 11 miền và giải quyết xung đột.
4. `STABLE_MUTABLE_OWNERSHIP.json`: Báo cáo phân định nội dung ổn định trong `RULES.md` và nội dung động trong các tệp khác.
5. `CODE_INDEX_AUDIT.json`: Báo cáo rà soát 272 tệp được lập chỉ mục và các tệp lịch sử.
6. `TEST_EVIDENCE_RECONCILIATION.json`: Số liệu đối soát kiểm thử từ `18704f14` và `2678cc65`.
7. `EVIDENCE_CHAIN_INDEX.json`: Sơ đồ chuỗi đính chính 3 tầng và danh sách bằng chứng hiệu lực.
8. `WAVE_LEDGER_BACKFILL.json`: Bảng dữ liệu 12 wave được bổ sung vào `STATUS_LEDGER.md`.
9. `LINK_INTEGRITY.json`: Kết quả kiểm tra tính toàn vẹn liên kết nội bộ (0 broken links).
10. `HANDOFF_CONTRACT.json`: Hợp đồng bàn giao AI context bundle (89 dòng, đáp ứng đầy đủ yêu cầu).
11. `ROADMAP_VALIDATION.json`: Xác nhận lộ trình phân tầng P0–P6 và hành động tiếp theo.
12. `OPEN_ISSUES_VALIDATION.json`: Danh mục 13 vấn đề kỹ thuật với mã định danh ổn định.
13. `MIGRATION_CHECKLIST_VALIDATION.json`: Xác thực 20 cổng kiểm soát chuyển dịch kiến trúc.
14. `FAULT_INJECTIONS.json`: Báo cáo chi tiết kết quả 14 ca tiêm lỗi F1–F14 (100% caught).
15. `TEST_RESULTS.json`: Toàn bộ số liệu kiểm thử thực tế từ JUnit XML và console.
16. `SECRET_SCAN.json`: Kết quả quét bí mật toàn bộ kho tài liệu (0 vi phạm).
17. `FINAL_DECISION.json`: Phán quyết cuối cùng của wave (`PASS`).

---

## 7. BẢO TỒN CÂY LÀM VIỆC VÀ AN TOÀN HỆ THỐNG

* **Tệp bẩn của người dùng**: `frontend/public/favicon.svg` ở trạng thái bị xóa trong working tree của người dùng được **bảo tồn tuyệt đối**:
  * Không chạy `git checkout`, `git restore`, hoặc `git add` đối với tệp này.
  * Tệp không xuất hiện trong Commit 1 (`34c36872`) và sẽ không xuất hiện trong Commit 2.
* **Tệp mã nguồn sản phẩm**: `git diff --stat 2678cc653f702e06620f49ae8069e46d418bfd55 HEAD -- backend/app frontend/src` trả về rỗng. Tuyệt đối không thay đổi mã nguồn sản phẩm, prompt, schema, hay compiler.
* **Candidate freeze**: Giữ nguyên `077dbc6b7bf6f62f7d07838696f5bcf71c74d3210ae65fbfc36683ee19e42bc1` (103 tệp verified).
* **Cache version**: Giữ nguyên `99`.

---

## 8. PHÁN QUYẾT VÀ BƯỚC TIẾP THEO

* **Phán quyết wave**: **`PASS`**
* **Trạng thái bàn giao**: Hệ thống tài liệu đã đạt trạng thái chuẩn mực (hardened information architecture), sẵn sàng cho các phiên làm việc và agent mới tiếp quản mà không gây mất mát ngữ cảnh hay xung đột thẩm quyền.
* **Hành động tiếp theo chuẩn tắc duy nhất**:
  ```text
  PRIMITIVE_COMPILER_SECOND_FAMILY_SELECTION_AND_PREREGISTRATION
  ```
