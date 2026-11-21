# Construction Release Readiness Decision (`AXO CONSTRUCTION /2`)

## 1. Bảng thẩm định tiêu chí hoàn thành (§34 Checklist)

| Tiêu chí §34 | Trạng thái | Bằng chứng xác minh |
| --- | --- | --- |
| Tái lập Baseline Construction /1 | `PASS` | `16/16` tệp `/1` nguyên vẹn (`v1_immutability.intact = True`), `16/16` `/1` pytests PASS |
| Xử lý `D02` đúng 3 ngữ nghĩa toán học | `PASS` | [CONSTRUCTION_GOAL_SEMANTICS.md](CONSTRUCTION_GOAL_SEMANTICS.md): `point_distance` = `0`, `segment_length` = `DEGENERATE_CONSTRUCTION`, tiền đề nhất quán |
| Đối soát metric auxiliary witness & 6 cờ | `PASS` | [CONSTRUCTION_V1_BENCHMARK_RECONCILIATION.md](CONSTRUCTION_V1_BENCHMARK_RECONCILIATION.md): `/1` `26/33` vs `0` `7/33`; `/2` `16/33` implicit aux |
| So sánh baseline 4 nhánh công bằng | `PASS` | [FAIR_PLANNER_COMPARISON_RESULTS.json](FAIR_PLANNER_COMPARISON_RESULTS.json): `Arm A1 26/33`, `Arm A2 32/33`, `Arm C 33/33` (`40/40 P_strict`) |
| Kiểm chứng từng node & từ chối đột biến | `PASS` | [PROOF_MUTATION_TEST_RESULTS.json](PROOF_MUTATION_TEST_RESULTS.json): **`12/12`** mutation bị chặn (`11/12` đã lọt `/1`) |
| Không rò rỉ oracle vào Planner | `PASS` | [ORACLE_ISOLATION_REPORT.md](ORACLE_ISOLATION_REPORT.md): AST `0` hits; SHA-256 bất biến với oracle ngoài |
| Kiểm chứng 9 bất biến hình học | `PASS` | [GEOMETRY_INVARIANCE_RESULTS.json](GEOMETRY_INVARIANCE_RESULTS.json): **`9/9 PASS`** gồm `SO(3, Q)` và `GL(3, Q)` hiệp biến $G' = A^{-T} G A^{-1}$ |
| Phân loại đa nhãn `N0`–`N5` & phát hiện điểm phụ | `PASS` | [CONSTRUCTION_NOVELTY_RECLASSIFICATION.json](CONSTRUCTION_NOVELTY_RECLASSIFICATION.json): `N0=4, N1=12, N2=22, N3=17, N4=14, N5=1, NEG=6` |
| Holdout mới sau đóng băng (`N=60`) | `PASS_WITH_FINDINGS` | [INDEPENDENT_CONSTRUCTION_EVALUATION.json](INDEPENDENT_CONSTRUCTION_EVALUATION.json): `53/60` (`42/44` pos = `95.5%`, `0` wrong/hallucinated, `11/16` exact neg label / `16/16` fail-closed); `EXTERNAL_INDEPENDENCE = NOT_MEASURED` |
| Stress Search & Hiệu năng E2E | `PASS` | [SEARCH_STRESS_BENCHMARK.json](SEARCH_STRESS_BENCHMARK.json): depth 2..20 `19–58 ms`, budget limits không nhầm `CONTRADICTORY_CONSTRAINTS`, `B01` E2E `47.04 ms` |
| Integration Adapter + Feature Flag + Fallback | `PASS` | `integration_adapter.py`: `off` / `shadow` / `experimental` + `SAFE_VERIFIED_LEGACY_FALLBACK` + `FAIL_CLOSED_REFUSED` |
| Tích hợp Backend / Frontend sản phẩm | `BLOCKED_OWNERSHIP` | `Gate F7 = BLOCKED_OWNERSHIP` (`backend/app/**`), `Gate F8 = PASS_ARTIFACT_ONLY` (`frontend/` ở `axo-geometry-library`); `2` patch `git apply --check` PASS |
| Baseline tất định cho Model 2 | `PASS` | `DeterministicModel2BaselineSelector`: 100% walkthrough có kiểm chứng, `0` Needle 3 |
| Không phá hợp đồng cũ / freeze / cache | `PASS` | `freeze_evaluation_candidate` MATCH (`123` files), `lock_cache_identity` MATCH (`145`), `0` AI calls |

## 2. Kết luận nghiệm thu chính thức

$$\textbf{DECISION: Level 2 — BACKEND\_INTEGRATION\_READY}$$

- **Không kết luận `Level 3 — CONTROLLED_INTEGRATION_VALIDATED`:** Mặc dù nguyên mẫu `/2` đã vượt toàn bộ cổng toán học, chứng chỉ đột biến `12/12`, bất biến `9/9`, bảo toàn `Source Gate`, `Presentation Validator`, và cung cấp cả `integration_adapter.py` + `handoff/*.patch` vượt `git apply --check`, mã sản phẩm (`backend/app/ai/adapter4_route.py` và `frontend/src/simulations/domains/geometry/Scene3DExplorer.tsx`) vẫn ở trạng thái **`BLOCKED_OWNERSHIP`** (`0` dòng thay đổi trực tiếp trên sản phẩm). Theo nguyên tắc §34/§36, Level 3 chỉ được cấp sau khi owner áp dụng patch vào tuyến chạy thật và chạy cổng tích hợp trên sản phẩm.
- **Không đổi mặc định Gemini 2.5 Flash**, không merge `main`, không push, không triển khai Needle 3 hay fine-tuning trong `/2`.

## 3. Các khoảng trống / Rào cản còn lại bàn giao cho bước tiếp theo

1. **Áp dụng patch sở hữu (`Gate F7 / F8`):** Áp dụng [backend_adapter4_dynamic_construction_flag.patch](handoff/backend_adapter4_dynamic_construction_flag.patch) (`backend/app`) và [frontend_scene3d_multiplan_switcher.patch](handoff/frontend_scene3d_multiplan_switcher.patch) (`axo-geometry-library`) với `AXO_DYNAMIC_CONSTRUCTION_MODE = "off"` mặc định và `"shadow"` trước khi mở `"experimental"`.
2. **Xử lý 3 nhóm phát hiện trên Single-Shot Holdout `N=60` (sau khi mở khóa bản chỉnh mới — không sửa candidate `/2` đã đóng băng):**
   - *Rút gọn tên trùng tọa độ (`H17, H44, HN05`):* Cho phép đăng ký bí danh (*alias*) khi điểm dựng mới (`O_ac`, `O2`) trùng tọa độ điểm sẵn có (`O`, `O1`) để `point_distance(O1, O2)` trả `"0"` và `segment_length(O1, O2)` từ chối chính xác `DEGENERATE_CONSTRUCTION`.
   - *Tiền kiểm định phân loại mục tiêu trước BFS (`HN04, HN13, HN14`):* Từ chối trực tiếp `MISSING_PRECONDITION` cho đỉnh mục tiêu chưa khai báo (`Z_MISSING`) và `UNSUPPORTED_OPERATOR` cho mục tiêu ngoài miền (`circumscribed_sphere_radius`, `inscribed_sphere_radius`) thay vì để BFS chạy tới `NO_PLAN_FOUND_WITHIN_BUDGET`.
   - *Cập nhật trích dẫn/hợp đồng `Registry /33` & `MAX_MEMORY_DECLARATIONS = 32`:* Mở rộng `7/23` toán tử chưa có `PlanningContract` nếu muốn đưa vào đường legacy/Hybrid.
3. **Đo kiểm định độc lập ngoài (`EXTERNAL_INDEPENDENCE = NOT_MEASURED`):** Tập `N=60` hiện tại được tổng hợp hậu đóng băng nội bộ (`INTERNAL_POST_FREEZE_INDEPENDENT_SYNTHESIS`); cần đánh giá bổ sung trên kho đề thi ngoài hoàn toàn chưa từng chạm tay tác giả (`H-1` / VNHSGE có bản quyền hợp lệ).
