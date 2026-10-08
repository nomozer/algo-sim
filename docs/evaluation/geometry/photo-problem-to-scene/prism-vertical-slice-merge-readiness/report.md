# PRISM_VERTICAL_SLICE_MERGE_READINESS_REVIEW — Báo cáo Đánh giá Sẵn sàng Merge Vertical Slice Lăng trụ

> **Trạng thái:** HOÀN THÀNH — LOCAL MERGE READINESS: PASS · REMOTE MERGE READINESS: PENDING_REMOTE_REFRESH  
> **Thời điểm thực hiện:** 2026-09-24  
> **Mục tiêu:** Rà soát toàn diện mức độ sẵn sàng merge cho toàn bộ milestone vertical slice lăng trụ (`right_triangle_base_right_prism_volume`) từ `f4a547ab` đến HEAD, bảo đảm tuyệt đối các bất biến an toàn hệ thống, hợp đồng dữ liệu, và ranh giới nghiên cứu.

---

## 1. Bảng Thông số Đầu vào & Danh tính Hệ thống

```text
WAVE = PRISM_VERTICAL_SLICE_MERGE_READINESS_REVIEW
BRANCH = feat/photo-problem-to-scene
START_HEAD = d3fc1c72df500d1da1ed2758ef84fa85fd48b582
LOCAL_MAIN_HEAD = 085cae67392d3607ad0a58a7f48c17d8a5e5157d
MERGE_BASE = 085cae67392d3607ad0a58a7f48c17d8a5e5157d
FEATURE_COMMITS_AHEAD = 111
REMOTE_MAIN_FRESHNESS = NOT_ESTABLISHED

CANDIDATE_TREE_HASH = 669ea2f160810c4f89e24fbe985abfefcc2f82a8f65e1a8fe0b9e1e9b47f9f95
CANDIDATE_FILE_COUNT = 103
CACHE_VERSION = 100
DEFAULT_MODE = LLM_ONLY

USER_CHANGE_TO_PRESERVE = D frontend/public/favicon.svg
NEW_GEMINI_REQUESTS = 0
NETWORK_REQUESTS = 0
API_KEY_LOADED = NO
DOTENV_LOADED = NO
MERGE_EXECUTED = NO
PUSH_EXECUTED = NO
REBASE_EXECUTED = NO
AMEND_EXECUTED = NO
```

---

## 2. Gate A — Git và Phạm vi Nhánh (PASS)

1. **Xác minh Branch và Working Tree:**
   - Nhánh công tác: `feat/photo-problem-to-scene` tại commit `d3fc1c72df500d1da1ed2758ef84fa85fd48b582`.
   - Trạng thái working tree người dùng: Chỉ duy nhất file `frontend/public/favicon.svg` bị xóa (`D`), hoàn toàn không bị stage, commit hoặc restore.
2. **Đối soát Lịch sử với Local Main:**
   - `LOCAL_MAIN_HEAD` = `085cae67392d3607ad0a58a7f48c17d8a5e5157d`.
   - `MERGE_BASE` = `085cae67392d3607ad0a58a7f48c17d8a5e5157d`.
   - Nhánh `feat/photo-problem-to-scene` đi trước `main` 111 commit, đi sau 0 commit.
   - Kiểm tra xung đột read-only bằng `git merge-tree`: **0 conflicts** (cây sạch mã `11844a9b9addb3bfc45f3869938cf26df82ab8f4`).
   - `REMOTE_MAIN_FRESHNESS = NOT_ESTABLISHED` (không fetch mạng ngoại vi theo đúng bất biến).
3. **Phân loại Diff Vertical Slice (`f4a547ab...HEAD` — 96 file):**
   - **Product runtime (10 files):**
     - `backend/app/main.py`
     - `backend/app/simulation/geometry_compiler/compiler.py`
     - `backend/app/simulation/geometry_compiler/contract_adapter.py`
     - `backend/app/simulation/geometry_compiler/fact_graph.py`
     - `backend/app/simulation/geometry_compiler/primitives.py`
     - `backend/app/simulation/photo_problem_to_scene/analyze_contract.py`
     - `backend/app/simulation/photo_problem_to_scene/contract.py`
     - `backend/app/simulation/photo_problem_to_scene/grounding_gate.py`
     - `backend/app/simulation/photo_problem_to_scene/request_contract.py`
     - `backend/app/simulation/photo_problem_to_scene/structured_relations.py`
   - **Schema & Model-facing Prompt (3 files):**
     - `backend/app/ai/skills/geometry_analyze.md`
     - `docs/superpowers/specs/semantic_program.schema.json`
     - `frontend/src/simulations/domains/semantic/semantic_program.schema.json`
   - **Tests & Tooling (34 files):** Suites kiểm thử hình học, schema sync, apparatus đo lường, lock/freeze scripts.
   - **Documentation (15 files):** Tài liệu phân tích, đặc tả, tiền đăng ký và nhật ký các wave.
   - **Evaluation Evidence (33 files):** Bằng chứng artifact, kết quả retry, manifest, run summaries.
   - **Khóa danh tính (1 file):** `backend/cache_identity.lock.json`.
   - **File ngoài dự kiến:** 0 file.

---

## 3. Gate B — Review Kiến trúc và Code (PASS)

Đã rà soát toàn bộ diff của vertical slice và kiểm chứng 10 bất biến kiến trúc:

| STT | Bất biến Kiến trúc | Kết quả | Chi tiết Kiểm tra |
|---|---|---|---|
| 1 | `DEFAULT_MODE = LLM_ONLY` | **PASS** | Kiểm tra `routing.py:17` và `main.py:65`; không tự ý chuyển default sang compiler-first |
| 2 | Prism compiler không đọc `problem_text` | **PASS** | `compiler.py` và `primitives.py` chỉ nhận `FactGraph`/hợp đồng cấu trúc; 0 dòng đọc text tự nhiên |
| 3 | Không có ground truth / fixtures trong production | **PASS** | 0 grep hit từ khóa benchmark hay test fixture trong `backend/app/` |
| 4 | `LAYOUT_DERIVED` không bị giả mạo thành `GIVEN` | **PASS** | `construct_prism` gán đúng provenance `LAYOUT_DERIVED` cho tọa độ đỉnh sinh ra |
| 5 | Pyramid family cũ không hồi quy | **PASS** | Primitive `construct_pyramid` và các quan hệ chóp giữ nguyên vẹn |
| 6 | Generic polyhedron chưa rollout ngoài ý muốn | **PASS** | Chỉ hỗ trợ đúng 2 họ bài (pyramid và right prism); các đa diện khác fail closed |
| 7 | Negative cases fail closed đúng mã lỗi | **PASS** | Trả mã chuẩn: `UNSUPPORTED_STRUCTURED_RELATION_MISSING`, `INVALID_NON_POSITIVE_LENGTH`, `INVALID_CONFLICT` |
| 8 | Không có duplicate semantic source | **PASS** | Ranh giới giữa topology fields và derived primitives phân định đơn nhất, rõ ràng |
| 9 | Không có fallback âm thầm | **PASS** | Khi thiếu dữ kiện cấu trúc, compiler từ chối dứt khoát, không lén lút gọi heuristic |
| 10 | Không có debug/test hook trong production | **PASS** | Mã runtime không chứa cờ debug hay injection bypass |

### Phân loại Findings

- **BLOCKER:** 0
- **HIGH:** 0
- **MEDIUM:** 0
- **LOW:** 0
- **INFORMATIONAL:** 3
  - `FINDING-INFO-01`: Primitive `construct_prism` hiện định hướng đáy tam giác vuông trên mặt phẳng Oxy và tịnh tiến theo trục Oz; các phép xoay tổng quát 3D là bài toán ngoài phạm vi của vertical slice này.
  - `FINDING-INFO-02`: Contract adapter định hướng hẹp cho lăng trụ đứng đáy tam giác vuông. Các họ lăng trụ khác (tam giác đều, ngũ giác) sẽ cần đăng ký primitive riêng trong các wave sau.
  - `FINDING-INFO-03`: Apparatus kiểm thử đo lường đã được chuẩn hóa để nhận diện nhãn token tiếng Việt ("Đoạn thẳng AB" -> "AB"); mã sản phẩm runtime không bị ảnh hưởng.

---

## 4. Gate C — Bằng chứng Preregistration và Live Result (PASS)

1. **Tính bất biến của Artifact Tiền đăng ký:**
   - Manifest SHA-256: `f5978eb580228bbce570be0e2eebca5db606fcb37da54b6fcda07ff6683515fa` (MATCH).
   - Ground truth SHA-256: `faf42e896dd7ff5eb41f0a82705299446d6b67bcfa728c7c9ec417bfd755cbe8` (MATCH).
2. **Tính nhất quán của Lần Live Retry:**
   - Request Body SHA-256: `4461e38e56033809987ee65e0a8a0d556229656af6938dbba078b66d26a7a082` (MATCH).
   - Prompt SHA-256: `a6df8f08f92dd4557c8d2f8a3ce7a5ded14ef75b072efdf58eac832b52af807f` (MATCH).
   - Sanitized Response Schema SHA-256: `90b2da5ddd8524f40b7bf2162b520de3187aba04452d652223011c548dce147c` (MATCH).
3. **Kiểm tra Raw Response Ngoài Repo:**
   - Đường dẫn ngoài: `D:/tmp/live_retry_evidence`
   - Hash SHA-256: `f1bd804523c9320e6a39d48b77fb7973fb0beea66e3ff5c5a0833a683bb5be86`
   - Kích thước: 2,322 bytes
   - Git tree: **KHÔNG** nằm trong Git repository.
4. **Correction Chain & Kết luận Hiện hành:**
   - Chuỗi đính chính hoàn toàn acyclic (không chu trình) và không có entry treo.
   - Kết luận cũ `SCHEMA_ACCEPTED_MODEL_SEMANTIC_FAILURE` đã được đính chính bằng chuỗi attribution apparatus.
   - Kết luận hiện hành: **`SCHEMA_ACCEPTED_PIPELINE_PASS`** với đáp số thể tích tính toán $V = 30.0$ khớp tuyệt đối với ground truth.

---

## 5. Gate D — Kiểm thử Trước Merge (PASS)

### Backend Test Suites
- **Focused suites (5 files):** 88 passed / 0 failed / exit code 0.
- **Full backend suite:**
  - Tổng số item: 6,171 tests
  - Collected: 6,170 tests (1 deselected theo cờ `-m "not postgres"`)
  - Skipped: 1 test
  - Passed: 6,169 tests
  - Failed: 0
  - Errors: 0
  - Exit code: 0
  - Cân bằng số học telemetry: $6169 + 1 \text{ (skipped)} + 1 \text{ (deselected)} = 6171 \text{ items}$.

### Frontend Test Suites
- **Typecheck:** `npx --no-install tsc -b` -> Exit code 0 (PASS).
- **Vite production build:** `npx --no-install vite build` -> Exit code 0, 3.84s (PASS).
- **Vitest unit tests:** `npx --no-install vitest run` -> 59 files, 870 passed / 0 failed, exit code 0 (PASS).

### Offline Visual Smoke Test / Browser Replay
- Trạng thái: **`BROWSER_REPLAY = NOT_ESTABLISHED`**
- Lý do: Repository hiện chỉ có harness browser replay chuyên biệt cho họ hình chóp (`R01`, các điểm S, A, B, C). Chưa có envelope hay harness dựng sẵn cho họ lăng trụ tam giác. Theo quy tắc Gate D, wave review không tự ý mở rộng sản phẩm để tạo harness mới.

---

## 6. Gate E — Tính Đúng đắn của Tuyên bố Nghiên cứu (PASS)

Báo cáo xác lập và tuân thủ nghiêm ngặt các ranh giới tuyên bố khoa học:

### Được phép tuyên bố:
1. Schema live được model provider chấp nhận mà không gặp lỗi biên giao vận (HTTP 400).
2. Lượt chạy live retry trên ca tiền đăng ký `PRISM_SCHEMA_LIVE_P01` đã trích xuất đầy đủ quan hệ cấu trúc và độ dài.
3. Pipeline tất định downstream đã dựng đúng hình học lăng trụ đứng, tạo ra topology 6 đỉnh, 9 cạnh, 5 mặt, và tính đúng đáp số $V = 30.0$.
4. Vertical slice hoạt động end-to-end hoàn chỉnh cho ca `PRISM_SCHEMA_LIVE_P01`.

### Tuyệt đối không tuyên bố (Guardrails):
```text
CASE_LEVEL_100_PERCENT_ONLY = YES
FAMILY_WIDE_GENERALIZATION = NOT_ESTABLISHED
STATISTICAL_SIGNIFICANCE = NOT_ESTABLISHED
PEDAGOGICAL_EFFICACY = NOT_ESTABLISHED
PRODUCTION_READINESS = NOT_ESTABLISHED
```

*Ghi chú đính chính (Correction Note):* Mọi cụm từ trong tài liệu cũ ám chỉ "trích xuất đúng đủ 100% dữ kiện của họ bài" chỉ có giá trị hiệu lực trên **phạm vi từng ca đơn lẻ (case-level)** đã được kiểm chứng bằng máy, hoàn toàn không đại diện cho năng lực tổng quát hóa toàn họ bài lăng trụ (`FAMILY_WIDE_GENERALIZATION = NOT_ESTABLISHED`).

---

## 7. Secret và Repository Hygiene (PASS)

- Quét toàn bộ diff `f4a547ab...HEAD` và các artifacts mới tạo:
  - 0 API key hoặc token bí mật.
  - 0 Authorization header hoặc bearer token.
  - 0 raw model response trong git tree.
  - 0 file `.env` hoặc file tạm `.tmp`.
  - 0 thông tin machine path nhạy cảm chưa được rút gọn.
  - 0 `Co-Authored-By` header trong commit messages.
  - Trạng thái file người dùng `frontend/public/favicon.svg` được bảo tồn nguyên vẹn.
  - Temporary worktree kiểm thử đã được dọn sạch hoàn toàn sau khi kiểm chứng.

---

## 8. Kết luận và Hành động Kế tiếp

### Đánh giá Sẵn sàng Merge:
- **`LOCAL_MERGE_READINESS = PASS`**
- **`REMOTE_MERGE_READINESS = PENDING_REMOTE_REFRESH`**
- **`MERGE_ALLOWED = NO`** (Không được phép tự merge khi chưa thiết lập freshness của remote main).
- **`FINAL_DECISION = PASS_LOCAL_PENDING_REMOTE`**

### Hành động Kế tiếp (NEXT_ACTION):
```text
NEXT_ACTION = PUSH_FEATURE_BRANCH_AND_OPEN_PR
```
*(Ghi chú: Agent không tự thực hiện `NEXT_ACTION`. Việc đẩy nhánh và mở PR sẽ do người dùng hoặc CI pipeline thực hiện).*
