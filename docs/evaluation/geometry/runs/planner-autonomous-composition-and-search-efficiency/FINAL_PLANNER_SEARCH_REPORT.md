# FINAL_PLANNER_SEARCH_REPORT — Báo Cáo Tổng Hợp Chiến Dịch `planner-autonomous-composition-and-search-efficiency`

- **Run ID:** `planner-autonomous-composition-and-search-efficiency`
- **Nhánh / Worktree:** `feat/local-first-geometry-understanding` (`D:/Documents/projects/algo-sim/.superpowers/worktrees/local-first-geometry-understanding`)
- **Mốc ban đầu (`start_head`):** `39b2f3691`
- **Product commit:** `8d12e93c4` (`feat(planner): generalize autonomous effect composition, cross-role reuse, and precondition pruning`)
- **Evaluator / Template refresh commit:** `3fa23e481`
- **Candidate freeze commit:** `009c06df1` (`measured_system`: `120` file, SHA-256 `a9e6a372da73497b438c12e5763042ab4cab88faaacfe6a2357393b8598f88a3`, `cay_lam_viec_sach = true`, `CACHE_VERSION = "142"`, `ROUTE_D_CACHE_POLICY = "142:route-d"`, `semantic_environment_hash = "6233c43c395c9b493d31d3dbb5d0ca952604730f6185cf541d2f179c077f955b"`, `SEALED = DA_NIEM_PHONG`)
- **Môi trường kiểm chứng:** `ALLOW_LIVE_AI = 0`, `GEMINI_API_KEY = ""`, `HYBRID_ROUTE_MODE` chưa đặt (replay dùng `ReplayExtractor` hoặc test cô lập), **`0` lượt gọi AI live**. Không hợp nhất `main`, không push, không chạm `axo-geometry-library`, không mở `H-1` hay `W2`/`W3`.

---

## 1. Bảo Toàn Định Vị Sản Phẩm, `output-policy/1` & Khóa Bề Mặt

- Axo duy trì kiến trúc **Hybrid `/4`** tất định (`Local Geometry Parser /2` / `Gemini -> TypedFactNext /2` -> `Source Gate` -> `FactGraph` -> `Planner /26` -> `Registry /33` -> `Exact Kernel /24` -> `Adapter /4` -> `Scene3D`), không để AI chọn hàm hay sinh mã giải từng đề.
- `output-policy/1` (Chế độ A) được giữ nguyên (`envelope["result"] is None` trên câu trả lời mặc định cho học sinh), không rò machine ID nội bộ (`@o1`, `@c1`, `sec1_normal1`, `__line_endpoints__`) vào nhãn hiển thị hay timeline học tập, và cả 4 bề mặt trích xuất khóa cứng (`function_calling`, `fact_extraction("flat" | "v3")`, `typed_fact_next_surface_fingerprint()`) không đổi byte.

---

## 2. Kết Quả Đánh Giá Tự Khám Phá Tổ Hợp & Hiệu Năng Tìm Kiếm (`NOVEL_COMPOSITION_EVALUATION.json`)

Báo cáo máy: [`NOVEL_COMPOSITION_EVALUATION.json`](NOVEL_COMPOSITION_EVALUATION.json) (`OFFLINE_DEVELOPMENT_EVIDENCE`, đo trên candidate đóng băng `009c06df1`, `0` AI calls).

### 2.1 Bộ Kiểm Định `reasoning_matrix.py` (`72` ca) & Phân Tích `MG9`
- **Tổng quan:** **`61 / 62`** ca dương `EXACT_SERVED` · **`10 / 10`** ca âm `CORRECT_REFUSAL` / `CORRECT_CLARIFICATION` · **`0` `false_served`** · `latency_p50 = 231.053 ms`, `latency_p95 = 840.139 ms`, `peak_memory_p95 = 2006.36 KiB` (đo dưới `tracemalloc`).
- **`MG9` (7 câu hỏi chẩn đoán):**
  - Trước tối ưu: thất bại sớm ở Planner (`PLAN_TOO_LARGE`, `54 > MAX_EFFECT_CANDIDATES = 48`) do `21` ứng viên trượt tiên điều kiện vẫn bị cộng ngân sách.
  - Sau cắt tỉa tiên điều kiện trước `self.candidates += 1`: **`planner.lap_ke_hoach` thành công** (`classification = REGISTERED_DECOMPOSITION`, `candidate_evaluations = 33 <= 48`, `pruned_nodes = 21`, `explored_states = 72`, `search_depth = 4`, `plan_cost = 13`, `rejection_reasons = ['precondition: the point lies on the line']`), và toàn tuyến Hybrid `/4` từ chối trung thực tại **`route_ir_budget`** với **`reason_code = "IR_MEMORY_BUDGET_EXCEEDED"`** (IR cần `34` `memory_declarations` sau gộp đường, tối thiểu `33 > MAX_MEMORY_DECLARATIONS = 32` được bảo toàn nguyên vẹn).

### 2.2 Bộ `r1-described-point-probe` (`19` ca)
- **`13 / 13`** ca dương (`C1a..C7`, `N1`, `D1`, `D2`, `C3-dist`) đạt oracle chính xác & `0` lỗi continuity.
- **`6 / 6`** ca đối kháng (`X1–X6`) từ chối fail-closed, **`0` `false_served`**.

### 2.3 Bộ Thử Tổ Hợp Tự Động Mới (`21` ca dương + `11` ca âm/đối kháng)
- **Tổ hợp mới (`21 / 21` = 100.0%, `0` lỗi continuity, `latency_p50 = 291.702 ms`, `p95 = 487.548 ms`):**
  - Phân lớp tìm kiếm: `5` `DISCOVERED_FUNCTION_COMPOSITION` (`NC-C1..C5`: giao hai đường dẫn xuất không có `"hai"` trên chóp/lăng trụ, hình chiếu lên đường dẫn xuất từ `@orthocenter`/`@centroid`, trung điểm nối `@orthocenter` + đỉnh), `8` `REGISTERED_DECOMPOSITION`, `8` `SOURCE_EXPLICIT_SEQUENCE`; `7` ca có `reused_intermediates >= 1`.
  - Độ phủ đa họ hình cho `ask_distance_lines` (`NC-A1..A5`, `NC-B1..B4`): hình chóp vuông `S.ABCD` (`2√5/5`, `√11/11`, `√2/5`, `√35/35`), lăng trụ đứng tam giác `ABC.A'B'C'` (`12√61/61`), hình lập phương `ABCD.A'B'C'D'` (`4√11/11`, `√14/7`), tứ diện đều `ABCD` (`2√22/11`, `2√70/35`).
  - Tái sử dụng anh em trong mục tiêu (`NC-D1_T1`, `NC-D2_E1`, `NC-D3_T1_SA4`): `plan_cost = 8` (giảm từ `10`), `reused_intermediates = 2`, **`0` điểm trùng `H4`** trong `Scene3D`.
  - Tái sử dụng xuyên luật (`NC-E1_T3` `reused=3`, `NC-E2_T4` `reused=1`, `NC-E3_T5` `reused=1`, `NC-E4_DCC` `reused=1`): đều khớp oracle & `0` lỗi continuity.
- **Cô lập Gold `TypedFactNext /2` vs `Local Geometry Parser /2`:**
  - `4 / 4` ca kỳ vọng đọc cục bộ (`NC-D1_T1` `57.194 ms`, `NC-D3_T1_SA4` `50.672 ms`, `NC-E1_T3` `47.903 ms`, `NC-E3_T5` `106.444 ms`) đạt `LOCAL_PARSE_COMPLETE`, `SERVED`, khớp đáp số Gold 100%.
  - `NC-D2_E1` (câu hỏi góc giữa hai đầu mút đều là mô tả ẩn danh) dừng trung thực ở `LOCAL_PARSE_PARTIAL -> LIVE_AI_DISABLED` do luật `m_ang` hiện tại chỉ đọc đầu mút đơn `{_PT}` trước `"với ..."`.
- **An toàn ca âm (`11 / 11`, `0` `false_served`):** bao gồm song song/chéo nhau trên `intersect_line_line` (`PARALLEL_NO_INTERSECTION`, `SKEW_NO_INTERSECTION`), chu trình phụ thuộc (`DEPENDENCY_CYCLE`), hai đường trùng nhau ở `distance_lines` (`AUXILIARY_RULE_MISMATCH`), mặt phẳng 3 điểm thẳng hàng, hai đầu mút trùng tọa độ, thiếu kích thước, mâu thuẫn độ dài cạnh, trích dẫn ngụy tạo, sửa cây chứng chỉ phụ, và giới hạn ngân sách tìm kiếm `MAX_EFFECT_CANDIDATES = 4` (`PLAN_TOO_LARGE`).

---

## 3. Kiểm Chứng Hồi Quy Toàn Repo & Cổng An Toàn

| Cổng kiểm | Lệnh / Phạm vi | Kết quả thực tế trên candidate `009c06df1` |
|---|---|---|
| `test_planner_autonomous_composition.py` | `pytest ... -q` | **PASS** — **`8 passed`** (`11.08s`) |
| `test_compositional_planner_expansion.py` | `pytest ... -q` | **PASS** — **`9 passed`** (`8.89s`) |
| `test_hybrid_reasoning_generalization.py` | `pytest ... -q` | **PASS** — **`40 passed, 1 xfailed`** (`MG9`, `9.56s`) |
| `test_production_dynamic_composition.py` | `pytest ... -q` | **PASS** — **`12 passed`** (`4.81s`) |
| `test_s2_student_language_pilot_runner.py` | `pytest ... -q` | **PASS** — **`106 passed`** |
| Toàn bộ Backend Pytest | `pytest -c backend/pytest.ini backend/tests -q` | **PASS** — **`14,850 passed`**, `7 skipped`, `3 deselected`, **`12 xfailed`**, **`0 failed`** (`603.63s`) |
| Toàn bộ Frontend Wave | `frontend/npm.cmd run test:wave` (`vitest run && tsc -b && vite build`) | **PASS** — **`142` file / `2,062 tests passed`** (`69.14s`), `0` lỗi TS, Vite build `5.53s` |
| `demo_replay` | `backend/scripts/replay_demo_cases.py --json` | **PASS** — `5/5` + `REDUCED_CHAIN_CASES = 1/1` |
| `crash_audit` | `backend/scripts/audit_demo_crash_surface.py --json` | **PASS** — `6/6` biên (`khop: true, nem: false`) |
| `export_hybrid_preview_fixtures.py --verify` | `docs/evaluation/geometry/runs/dimension-aware-verified-construction/fixtures-dimension-aware` | **PASS** — `verified = 41`, `problems = []` (`same_source_fingerprint: false` do product commit mới `8d12e93c4`) |
| Candidate freeze verify | `backend/scripts/freeze_evaluation_candidate.py --verify` | **PASS** — `120` files (`a9e6a372da73497b...`, `cay_lam_viec_sach = true`) |
| Cache lock verify | `backend/scripts/lock_cache_identity.py --verify` | **PASS** — `CACHE_VERSION 142` (`6233c43c395c9b49...`) |

---

## 4. Phán Quyết & Ranh Giới Trung Thực

- **`PRODUCT_TECHNICAL_VERDICT = PASS` · `OFFLINE_DEVELOPMENT_EVALUATION = PASS` (`21/21` novel positives, `11/11` negatives, `61/62` `reasoning_matrix`, `13/13` `r1`)**
- **`INDEPENDENT_H1_VALIDATION = NOT_MEASURED`** (`W2`/`W3` & `H-1` không mở)
- **`REAL_STUDENT_USABILITY = NOT_MEASURED`** · **`PHYSICAL_LOW_END = NOT_MEASURED`**
- **`FE-2/3/4/6 = BLOCKED_OWNERSHIP`** (worktree riêng `axo-geometry-library`)
- **`FULL_RELEASE_GATE = BLOCKED_GATES_REMAIN`**
