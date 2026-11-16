# FINAL_PLANNER_REPORT — Báo Cáo Tổng Hợp Chiến Dịch `compositional-planner-capability-expansion`

- **Run ID:** `compositional-planner-capability-expansion`
- **Nhánh / Worktree:** `feat/local-first-geometry-understanding` (`D:/Documents/projects/algo-sim/.superpowers/worktrees/local-first-geometry-understanding`)
- **Mốc ban đầu (`start_head`):** `c69c10fe6806012998c20245888f600ee9a1f218`
- **Product commits:**
  - `4f302b06a5cf582f8ed424abaae87aeeb3b0e6a2` (`feat(geometry): expand compositional planner discovery and bridge DAG verification`)
  - `7effb76b86522d091dca6af778afecec8aef247b` (`fix(geometry): guard ask_section_area trailing conjunction and promote R1-F01/F02 in staging verification`)
- **Candidate freeze commit:** `7bf744ec2c8da0c1100b462147e2bf96ef0c0ebf` (`measured_system`: `120` file, SHA-256 `d1c9fb815dbae8a4088d468b7e0c96a185c4e8a294a0c2e8a6880768ebd62a9e`, `CACHE_VERSION = "141"`, `semantic_environment_hash = "6233c43c395c9b493d31d3dbb5d0ca952604730f6185cf541d2f179c077f955b"`)
- **Môi trường kiểm chứng:** `ALLOW_LIVE_AI = 0`, `GEMINI_API_KEY = ""`, `HYBRID_ROUTE_MODE` chưa đặt (mặc định `live`, các phép replay dùng `ReplayExtractor` hoặc `staging-replay`), **`0` lượt gọi AI live**. Không hợp nhất `main`, không push, không chạm `axo-geometry-library`, không mở `H-1` hay `W2`/`W3`.

---

## 1. Bảo Toàn Định Vị Sản Phẩm & `output-policy/1` (Chế Độ A)

Axo là **hệ thống mô phỏng hình học không gian 3D tương tác có kiểm chứng toán học**, hỗ trợ học sinh trực quan hóa các đối tượng, quan hệ và tiến trình dựng từng bước — không chuyển sang AI-guided Planner và không để LLM chọn hàm hoặc sinh mã giải từng đề.
- `output-policy/1` (Chế độ A) được giữ nguyên vẹn cả khi áp dụng `ROUND_HALF_UP` lên câu hỏi chứa `effect-chain` đa mô tả (`D1`: `answer_exact.q1.coef == "√2"`, `answers.q1 == "1,4"`, `used_floating_point == false`, `validate_construction_continuity == []`).
- Tên hàm, trường nội bộ `TypedFact` (`goal_trees`, `point_tree`) đều dùng `SkipJsonSchema` + nằm trong `INTERNAL_FACT_FIELDS` nên không thay đổi hợp đồng trích xuất `TypedFactNext /2` và fail-closed nếu bị tiêm từ ngoài.

---

## 2. Kết Quả Đánh Giá Chuyên Sâu (`COMPOSITIONAL_GENERALIZATION_EVALUATION.json`)

Báo cáo máy: [`COMPOSITIONAL_GENERALIZATION_EVALUATION.json`](COMPOSITIONAL_GENERALIZATION_EVALUATION.json) (đo trực tiếp trên candidate đóng băng `7bf744ec2`).

### 2.1 Bộ Kiểm Định Lý Luận Tổ Hợp `reasoning_matrix.py` (`72` ca phát triển)
- **Trước mở rộng:** **`56 / 62`** ca dương trong phạm vi · **`10 / 10`** ca âm từ chối · **`0`** phục vụ sai (`6` `xfail`: `PL5`, `PA3`, `MG5`, `SE3`, `RE10`, `MG9`).
- **Sau mở rộng:** **`61 / 62`** ca dương trong phạm vi **`EXACT_SERVED`** · **`10 / 10`** ca âm **`CORRECT_REFUSAL` / `CORRECT_CLARIFICATION`** · **`0` `false_served`** · độ trễ trung vị `p50 = 33.766 ms`, `p95 = 167.454 ms`.
- **Chi tiết 5 ca được nâng hạng từ `xfail` lên `EXACT_SERVED` (`0` lỗi continuity):**
  1. `PL5`: `REGISTERED_DECOMPOSITION`, depth `3`, candidates `3` (độ dài / khoảng cách điểm-đường lồng `@id`).
  2. `PA3`: `SOURCE_EXPLICIT_SEQUENCE`, depth `2`, candidates `2` (`distance_line_plane` với đường thẳng dẫn xuất `@id`).
  3. `MG5`: `SOURCE_EXPLICIT_SEQUENCE`, depth `2`, candidates `3` (khoảng cách/độ dài hai đầu mút `@id`).
  4. `SE3`: `SOURCE_EXPLICIT_SEQUENCE`, depth `0`, candidates `0` (thiết diện 3 điểm mô tả + diện tích thiết diện).
  5. `RE10`: `DISCOVERED_FUNCTION_COMPOSITION`, depth `4`, candidates `10` (chứng tỏ Planner tự khám phá tổ hợp đa hàm vượt ngoài quy tắc đơn có sẵn).
- **Ranh giới được giữ có chủ đích:** **`MG9`** tiếp tục **`REFUSED`** với **`PLAN_TOO_LARGE`** do giữ nguyên trần hợp đồng `MAX_MEMORY_DECLARATIONS = 32`.

### 2.2 Bộ `r1-described-point-probe` (`13` dương + `6` đối kháng), `test_family_d2` & Cô Lập Ngôn Ngữ Tự Nhiên
- **`r1-described-point-probe` + `C3-dist`:** **`13 / 13`** ca dương (`C1a, C1b, C2, C3, C4, C5, C6a, C6b, C7, N1, D1, D2, C3-dist`) đạt oracle chính xác & `0` lỗi continuity; **`6 / 6`** ca đối kháng (`X1–X6`) từ chối đúng, **`0` `false_served`**.
- **Cô lập Gold `TypedFactNext /2` vs `Local Geometry Parser /2` (NL):** **`7 / 7`** (`PL5`, `PA3`, `MG5`, `SE3`, `RE10`, `F3b_orthocenter_section -> 16/9`, `F4c_circumcenter -> 1`) đi qua `parse_geometry_problem_locally == LOCAL_PARSE_COMPLETE` và `route_text_input(allow_live_ai=False) == SERVED`, đáp số khớp chính xác oracle và `0` lỗi continuity (`F3b` tái sử dụng `reused_intermediates = 3`, `F4c` tìm kiếm depth `4`, candidates `21`, pruned `9`).
- **Thăng hạng `test_family_d2`:** Từ `xfail` lên **`SERVED`** (`q1 = "2"`, `continuity_errors = 0`, tách 3 tầng `FE-4`: `planner_constructed_aux_certs = 1`, `backend_emitted_scene_objects = 22`, frontend render chấm ngoài miền giữ nguyên `BLOCKED_OWNERSHIP` tại `axo-geometry-library`).
- **Thăng hạng trên các bộ phát triển/pilot khác:**
  - `test_local_geometry_parser.py`: **`10 / 10`** đạt (cold parse `< 500 ms`, `R1-F01` `√6/2` & `R1-F02` `√2` đều `SERVED`).
  - `test_s2_student_language_pilot_runner.py`: **`106 / 106`** đạt (bao gồm toàn bộ nhóm `c21`; `R1` gold replay trên bản sao promoted đạt **`(15, 0, 0)`**, bản gốc `r1-live-pilot-corpus.json` & receipt giữ nguyên byte).
  - `test_route_d_function_composition.py`: `C6a` qua `orthocenter(SBD)` đạt `SERVED` (`26√3/27`, `0` lỗi continuity), trong khi đa giác 4 đỉnh trên `orthocenter` giữ nguyên fail-closed `REFUSED`.
  - `test_hybrid_product_integration.py` (16 lớp `/api/analyze` `staging-replay`): `R1-F01` & `R1-F02` được phục vụ ở `09_described_points`, `R1-F03` xác minh từ chối `capability_gap` ở `16_unsupported_goals`.

---

## 3. Kiểm Chứng Hồi Quy Toàn Repo & Cổng An Toàn

| Cổng kiểm | Lệnh / Phạm vi | Kết quả thực tế (sau commit `7bf744ec2`) |
|---|---|---|
| Bộ test mới `test_compositional_planner_expansion.py` | `pytest ... -q` | **PASS** — **`9 passed`** (`6.64s`) |
| `test_hybrid_reasoning_generalization.py` | `pytest ... -q` | **PASS** — **`40 passed, 1 xfailed`** (`MG9`, `7.55s`) |
| `test_route_d4_described_points.py` | `pytest ... -q` | **PASS** — **`55 passed`** (`4.99s`) |
| `test_production_dynamic_composition.py` | `pytest ... -q` | **PASS** — **`12 passed`** (`3.17s`) |
| Toàn bộ Backend Pytest | `pytest -c backend/pytest.ini backend/tests -q` (`ALLOW_LIVE_AI=0`, `HYBRID_ROUTE_MODE` unset) | **PASS** — **`14,842 passed`**, `7 skipped`, `3 deselected`, **`12 xfailed`**, **`0 failed`** (`695.44s`) |
| Toàn bộ Frontend Wave | `frontend/npm.cmd run test:wave` (`vitest run && tsc -b && vite build`) | **PASS** — **`142` file / `2,062 tests passed`** (`46.26s`), `0` lỗi TS, Vite build `3.59s` |
| `demo_replay` | `backend/scripts/replay_demo_cases.py --json` | **PASS** — `5/5` + `REDUCED_CHAIN_CASES = 1/1` (`ok: true`) |
| `crash_audit` | `backend/scripts/audit_demo_crash_surface.py --json` | **PASS** — `6/6` biên, `uncaught = 0` |
| `hybrid_preview_fixtures` | `export_hybrid_preview_fixtures.py --verify .../fixtures-dimension-aware` | **PASS** — `41` fixtures verified (`problems: []`) |
| `freeze_verify` | `backend/scripts/freeze_evaluation_candidate.py --verify` | **PASS** — `120` file, `d1c9fb815dbae8a4…` |
| `cache_lock_verify` | `backend/scripts/lock_cache_identity.py --verify` | **PASS** — `CACHE_VERSION 141`, môi trường `6233c43c395c9b49…` |

---

## 4. Phán Quyết Trung Thực & Các Giới Hạn Còn Mở

- **Kỹ thuật wave (`COMPOSITIONAL_PLANNER_VERDICT`):** **`PASS_WITHIN_DEVELOPMENT_BENCHMARK_AND_OFFLINE_REGRESSION`** — Đóng 5/6 khoảng trống tổ hợp trên `reasoning_matrix` (`56 -> 61/62`), `D1`/`D2` (`13 -> 15` trên R-1), `test_family_d2`, `C3-dist`, `C6a @orthocenter`, giữ nguyên mọi vân tay schema/surface, không hardcode, và đạt `14,842` backend / `2,062` frontend với `0` lượt gọi Gemini live.
- **Các ranh giới & cổng chưa mở (giữ trung thực theo `AGENTS.md §3` & `docs/CURRENT_STATE.md`):**
  - `INDEPENDENT_H1_VALIDATION = NOT_MEASURED` (tập niêm phong `H-1` và `W2`/`W3` không được mở ở wave này).
  - `REAL_STUDENT_USABILITY = NOT_MEASURED`, `PHYSICAL_LOW_END = NOT_MEASURED`.
  - `MG9` (`PLAN_TOO_LARGE` dưới `MAX_MEMORY_DECLARATIONS = 32`) và `@id` trong `PlaneConstraintSpec` (`INVALID_QUALIFIED_REF` ở `typed_fact_next.py`) vẫn là ranh giới có chủ đích.
  - `FE-2/3/4/6`: `BLOCKED_OWNERSHIP` trên worktree `D:/Documents/projects/axo-geometry-library` (chưa đụng tới).
  - Chiến dịch live Gemini `K-1` / `S-2` / `R-1`: `PENDING_OWNER_DECISION` (`paid_project_confirmed = false`).
  - Cổng xuất bản `HEAD` toàn lịch sử (`--head`): giữ trạng thái `BLOCKED_PENDING_OWNER_REVIEW` cho 97 mục lịch sử có sẵn (`--range c69c10fe6806012998c20245888f600ee9a1f218..HEAD` đạt `0` vi phạm mới).
