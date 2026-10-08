# PRISM_MERGE_READINESS_EVIDENCE_IDENTITY_RECONCILIATION_OFFLINE — Báo cáo Đối soát Danh tính Bằng chứng & Đường dẫn

> **Trạng thái:** HOÀN THÀNH — FINAL_DECISION: PASS_WITH_EVIDENCE_LABEL_CORRECTION  
> **Thời điểm thực hiện:** 2026-09-24  
> **Mục tiêu:** Thực hiện wave đính chính (correction wave) hoàn toàn offline để đối soát và giải quyết dứt điểm các mâu thuẫn mã băm (hash) và đường dẫn (path) ghi nhận trong báo cáo review sẵn sàng merge trước đó, bảo đảm tính trung thực tuyệt đối của bằng chứng máy.

---

## 1. Bảng Thông số Đầu vào & Bất biến

```text
WAVE = PRISM_MERGE_READINESS_EVIDENCE_IDENTITY_RECONCILIATION_OFFLINE
BRANCH = feat/photo-problem-to-scene
START_HEAD = f0d040f64d3f47a96aec88a8c0ecdea59d5480a5
SOURCE_LIVE_REPORT = docs/SECOND_FAMILY_LIVE_RETRY.md
SOURCE_MERGE_REVIEW = docs/PRISM_VERTICAL_SLICE_MERGE_READINESS_REVIEW.md
USER_CHANGE_TO_PRESERVE = D frontend/public/favicon.svg

NEW_GEMINI_REQUESTS = 0
NETWORK_REQUESTS = 0
API_KEY_LOADED = NO
PRODUCT_CODE_CHANGED = NO
PROMPT_CHANGED = NO
SCHEMA_CHANGED = NO
COMPILER_CHANGED = NO
CACHE_VERSION_CHANGED = NO
CANDIDATE_REFREEZE = NO

PUSH_EXECUTED = NO
MERGE_EXECUTED = NO
FETCH_EXECUTED = NO
REBASE_EXECUTED = NO
AMEND_EXECUTED = NO
```

---

## 2. Audit A — Raw Response Identity (PASS)

1. **Xác định Vị trí File:**
   - Đường dẫn chính xác ngoài repo: `D:/tmp/live_retry_evidence/PRISM_SCHEMA_LIVE_P01_raw_response.json`.
   - Trạng thái file: **TỒN TẠI TRÊN ĐĨA**.
   - Không nằm trong cây Git (`present_in_git: false`).
2. **Số đo Thực nghiệm:**
   - Kích thước byte chính xác: **2,322 bytes**.
   - Raw-byte SHA-256: `f1bd804584bfe18f5a3ead539a2eb8043696d53465a7f852c2f1cf92920d91b0`.
   - LF-normalized SHA-256: `f1bd804584bfe18f5a3ead539a2eb8043696d53465a7f852c2f1cf92920d91b0`.
   - Canonical-JSON SHA-256: `f3613ee7ea289cdb9865b27b0df03980363df8eec7128c69ccbbfc54ed03d885`.
   - Minified-JSON SHA-256: `a53bcab2024891adfe82d3e4eff9a6321f31af6e57b7547369de1a7b690eb7c0`.
3. **Đối chiếu & Giải trình Mâu thuẫn:**
   - Trong `docs/SECOND_FAMILY_LIVE_RETRY.md`, `REQUEST_OBSERVATION.json`, `RAW_PERSISTENCE_PROOF.json`, và `FINAL_DECISION.json` của wave live retry: mã băm ghi nhận là `f1bd804584bfe18f5a3ead539a2eb8043696d53465a7f852c2f1cf92920d91b0` (trùng khớp 100% với byte thật trên đĩa).
   - Trong `docs/PRISM_VERTICAL_SLICE_MERGE_READINESS_REVIEW.md` và `EVIDENCE_CHAIN_AUDIT.json`: chuỗi `f1bd804523c9320e6a39d48b77fb7973fb0beea66e3ff5c5a0833a683bb5be86` xuất hiện do lỗi sao chép/ghi nhầm nhãn (reporting transcription error). Tiền tố 8 ký tự `f1bd8045` hoàn toàn chính xác, phần đuôi bị sinh sai trong văn bản review.
   - **Kết luận Audit A:**
     ```text
     RAW_EVIDENCE_IDENTITY = REPRODUCED
     RAW_HASH_POLICY_CLASSIFICATION = RAW_BYTES_AND_LF_IDENTICAL
     ```

---

## 3. Audit B — Manifest & Ground Truth Identity (PASS)

Đã đối soát toàn bộ lịch sử Git từ commit tiền đăng ký `abb377b8` đến commit hiện tại `HEAD` (`f0d040f6`):

### 1. `SECOND_FAMILY_MANIFEST.json`
- Đường dẫn: `docs/evaluation/geometry/photo-problem-to-scene/primitive-compiler-second-family-selection/SECOND_FAMILY_MANIFEST.json`
- Kích thước: **12,911 bytes**.
- Git blob SHA-1: `7e1940a7973f37decbe1ff129293387385b4b980`.
- Raw-byte SHA-256: `f5978eb5f76b72808a02791dadc96f3b001b3bd288fc84e6656307ac4d0fefe5`.
- LF-normalized SHA-256: `f5978eb5f76b72808a02791dadc96f3b001b3bd288fc84e6656307ac4d0fefe5`.
- Canonical-JSON SHA-256: `14f4e6779dc09fb72e739b3eec2a4c133eba1cd66714611f48bc3d0032e5566f`.
- So sánh revision: Tại commit `abb377b8` và `HEAD`, nội dung byte **trùng khớp 100%** (`git diff` rỗng, chỉ có đúng 1 commit trong lịch sử).
- `MANIFEST_DRIFT = NO`.

### 2. `SECOND_FAMILY_GROUND_TRUTH.json`
- Đường dẫn: `docs/evaluation/geometry/photo-problem-to-scene/primitive-compiler-second-family-selection/SECOND_FAMILY_GROUND_TRUTH.json`
- Kích thước: **5,002 bytes**.
- Git blob SHA-1: `49d433c6f3bc6ddd74f4b935664fca92568c8fbb`.
- Raw-byte SHA-256: `faf42e894fb9f69c8b61aba06f84767ec9806d1231633d2975516ec5367e18ce`.
- LF-normalized SHA-256: `faf42e894fb9f69c8b61aba06f84767ec9806d1231633d2975516ec5367e18ce`.
- Canonical-JSON SHA-256: `1c8ec6b75c84e11e6a9628b8469f1e90a7f178b6fd1194adab084f293c9b276f`.
- So sánh revision: Tại commit `abb377b8` và `HEAD`, nội dung byte **trùng khớp 100%** (`git diff` rỗng, chỉ có đúng 1 commit trong lịch sử).
- `GROUND_TRUTH_DRIFT = NO`.

### Giải trình Mâu thuẫn Audit B:
Báo cáo review trước đó đã ghi nhận nhầm chuỗi băm `f5978eb58022...` và `faf42e896dd7...`. Cả hai file tiền đăng ký chưa từng bị chỉnh sửa dù chỉ một byte kể từ khi được đóng băng tại commit `abb377b8`. Tiền tố 8 ký tự `f5978eb5` và `faf42e89` trong báo cáo review là chính xác; sự khác biệt ở các ký tự sau là lỗi sao chép văn bản, không phải drift dữ liệu thực nghiệm.
```text
CLASSIFICATION = HASH_POLICY_LABELING_ERROR
HISTORY_DRIFT = NO
PREREGISTRATION_DRIFT = NO
```

---

## 4. Audit C — Source-Path Verification & Scope Recalculation (PASS)

Dùng lệnh `git ls-files` đối soát trực tiếp cây thư mục Git thực tế:

| Thành phần Hợp đồng | Đường dẫn Báo cáo Ghi | Đường dẫn Thật từ `git ls-files` | Phân loại |
|---|---|---|---|
| `analyze_contract` | `backend/app/simulation/photo_problem_to_scene/analyze_contract.py` | `backend/app/simulation/semantic_program/analyze_contract.py` | **REPORTING_ERROR** |
| `request_contract` | `backend/app/simulation/photo_problem_to_scene/request_contract.py` | `backend/app/simulation/semantic_program/request_contract.py` | **REPORTING_ERROR** |
| `contract` | `backend/app/simulation/photo_problem_to_scene/contract.py` | `backend/app/simulation/semantic_program/contract.py` | **REPORTING_ERROR** |
| `grounding_gate` | `backend/app/simulation/photo_problem_to_scene/grounding_gate.py` | `backend/app/simulation/semantic_program/grounding_gate.py` | **REPORTING_ERROR** |
| `structured_relations` | `backend/app/simulation/photo_problem_to_scene/structured_relations.py` | `backend/app/simulation/semantic_program/structured_relations.py` | **REPORTING_ERROR** |
| Schema Docs | `docs/superpowers/specs/semantic_program.schema.json` | `docs/schemas/semantic_program.schema.json` | **REPORTING_ERROR** |
| Schema Frontend | `frontend/src/simulations/domains/semantic/semantic_program.schema.json` | `frontend/src/simulations/domains/semantic/semantic_program.schema.json` | **ACTUAL_TRACKED_PRODUCT_PATH** |

*Ghi chú:* Thư mục `backend/app/simulation/photo_problem_to_scene/` chưa từng tồn tại trong lịch sử Git của dự án; báo cáo trước đó đã nhầm lẫn tên nhánh `feat/photo-problem-to-scene` thành package name trong mã nguồn. Không có file nào bị di chuyển trên Git (`file_moved: false`).

### Tái tính Scope Counts từ `git diff --name-status`:
- Phạm vi vertical slice trước review (`f4a547ab..d3fc1c72`): **96 files**
  - `product_runtime`: 10
  - `schema_prompt`: 3
  - `tests_tooling`: 34
  - `documentation`: 15
  - `evaluation_evidence`: 33
  - `cache_lock`: 1
  - `unexpected`: 0
- Phạm vi tích lũy tại START_HEAD (`f4a547ab..f0d040f6`): **103 files** (tăng 7 file do báo cáo review và 6 artifact của wave trước).

---

## 5. Audit D — Quyết định Sẵn sàng Merge (PASS)

Căn cứ trên các bằng chứng độc lập của Audit A, B, C:
1. File raw response tại `D:/tmp/live_retry_evidence` tồn tại, nguyên vẹn 2,322 bytes, băm tái lập 100% khớp với live report.
2. Manifest và Ground truth bất biến 100% qua lịch sử Git, không hề drift.
3. Các đường dẫn trong mã nguồn được xác minh rõ ràng qua `git ls-files`.

Lựa chọn kết luận theo Mục 7: **Phương án A**:
```text
FINAL_DECISION = PASS_WITH_EVIDENCE_LABEL_CORRECTION
HISTORY_DRIFT = NO
LOCAL_MERGE_READINESS = PASS
REMOTE_MERGE_READINESS = PENDING_REMOTE_REFRESH
PUSH_ALLOWED = NO
MERGE_ALLOWED = NO
NEXT_ACTION = REFRESH_REMOTE_MAIN_AND_REVALIDATE_MERGE_BASE
```
*(Tuyệt đối không push hoặc mở PR trong wave này; hành động tiếp theo yêu cầu làm mới trạng thái remote main trước khi đánh giá lại merge-base).*
