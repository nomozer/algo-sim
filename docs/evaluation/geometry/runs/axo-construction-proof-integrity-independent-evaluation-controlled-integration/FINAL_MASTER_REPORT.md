# Final Master Report — `AXO CONSTRUCTION /2`

## Proof Integrity, Independent Evaluation & Controlled Integration

**Run ID:** `axo-construction-proof-integrity-independent-evaluation-controlled-integration`
**Branch:** `feat/local-first-geometry-understanding` · **Base Commit:** `a0f573913a03a3d08a16e308663a654b454ff9c3` · **Candidate Freeze SHA-256:** `26c9b505fc7796ed9ff6a5c9578701978e92b9c1d6726a8208916a9ea3dca60c`
**Measured System (Product):** `113a6a7cf6bbc15ac23119150b805437e785d2b0714b26c2157d147514c2ef67` (`123` files, `CACHE_VERSION = 145` / `6233c43c395c9b49…`, **`0` diffs `backend/app/**` & `frontend/`**)
**Readiness Verdict:** **`Level 2 — BACKEND_INTEGRATION_READY`** (`INTEGRATION_STATUS = BLOCKED_OWNERSHIP`, `EXTERNAL_INDEPENDENCE = NOT_MEASURED`)

---

## 1. Reproducibility Metadata (§32)

| Thuộc tính | Giá trị xác minh thực tế |
| --- | --- |
| Commit base before `/2` | `a0f573913a03a3d08a16e308663a654b454ff9c3` (`418dd89f8` là `/1`, `498f35460` là pre-`/1`) |
| Prototype & Evaluator Versions | `dynamic-construction-planner/2`, `construction-exact-verifier/2`, `verified-construction-graph/1`, `presentation-step-graph/1`, `construction-operator/1` (`23` ops), `construction-scene3d-bridge/1`, `presentation-step-validator/1`, `verified-input-bridge/1`, `dynamic-construction-integration-adapter/1`, `model2-deterministic-selector/1`, `construction-benchmark-evaluator/2` |
| Candidate Freeze Digest (`14` `.py` files) | `26c9b505fc7796ed9ff6a5c9578701978e92b9c1d6726a8208916a9ea3dca60c` (kiểm trước và sau holdout single-shot) |
| Oracle Provenance (`N=60`) | `INTERNAL_POST_FREEZE_INDEPENDENT_SYNTHESIS` · `EXTERNAL_INDEPENDENCE = NOT_MEASURED` (`0` overlap với 40 ca `/1`) |
| AI / Fine-Tuning / Needle 3 / Network | `ALLOW_LIVE_AI = 0`, `GEMINI_API_KEY = ""`, `external_ai_calls = 0`, `0` fine-tuning, `0` Needle 3 |
| Ownership Status | `backend/experimental/construction_planner/**` + `scripts/*_v2.py` + `tests/...v2...` (`ALLOWED`); `backend/app/**` & `frontend/**` (`BLOCKED_OWNERSHIP`, `0` edits) |
| Environment & Test Commands | Windows 11 host (`PYTHONUTF8=1`); `pytest -c backend/pytest.ini backend/tests/geometry/test_verified_construction_graph_and_planner.py backend/tests/geometry/test_axo_construction_v2_integrity_and_integration.py -q` (`34 passed, 13.78s`); `pytest -c backend/pytest.ini backend/tests -q` (`15070 passed, 7 skipped, 3 deselected, 12 xfailed, 0 failed, 770.27s`) |

---

## 2. Trả Lời Đầy Đủ 20 Câu Hỏi Bắt Buộc (§35)

1. **Benchmark `/1` có lỗi toán học hoặc sai nhãn nào không?**
   Có **4 sai lệch / thiếu sót kỹ thuật** được đối soát mà không sửa byte `/1` ([CONSTRUCTION_V1_BENCHMARK_RECONCILIATION.md](CONSTRUCTION_V1_BENCHMARK_RECONCILIATION.md)): (a) Ca `D02` (`"Tính AA."`) bị evaluator `/1` tự chèn `PendingConstruction("op.connect_segment", "A", "A")` cho Candidate B và gán nhãn kỳ vọng chưa chuẩn `CONTRADICTORY_CONSTRAINTS` dù tiền đề khối chóp nhất quán (`DEGENERATE_CONSTRUCTION`); (b) Tuyên bố *"33/33 có witness phụ"* gộp chung với chỉ số `auxiliary_count > 0` vốn chỉ đạt **`26/33`** (`7/33` bằng `0` trong chính log `/1`); (c) Trong `A07_angle_sc_base_square`, `angle_line_plane` bỏ sót `proj_seg_k` khỏi `witness_keys` khiến `prune_to_goal_closure` cắt nhầm đoạn `seg_C_A`; (d) Bộ kiểm chứng `/1` (`strict_node_replay=False`) chưa tái thực thi toán tử từng node ở `L2` hay tái kiểm chứng bao đóng `GOAL` ở `L3`, và trong `/2` phát hiện thêm `certificates.verify_perpendicular_witness` bị gọi sai đối số trước khi đóng băng holdout.

2. **Kết quả chính xác sau khi sửa evaluator là bao nhiêu?**
   Trên 40 ca `/1` ([CONSTRUCTION_V1_METRIC_RECONCILIATION.json](CONSTRUCTION_V1_METRIC_RECONCILIATION.json)): dưới chính sách `P_metric` (`d(A,A)=0` hợp lệ) — `Baseline A = 33/40`, `Candidate B (/1) = 39/40`, **`Candidate C (/2) = 40/40`**; dưới chính sách `P_strict_segment` — `Baseline A = 32/40`, `Candidate B (/1) hành vi = 40/40` (nhãn `D02` sửa thành `DEGENERATE_CONSTRUCTION`), **`Candidate C (/2) = 40/40`** (`33/33` dương đạt `L0`–`L4` + `5/5` Group E đa phương án + `7/7` từ chối an toàn).

3. **Dynamic Planner vượt Planner cũ ở những năng lực nào khi dùng đầu vào tương đương?**
   Qua thí nghiệm 4 nhánh công bằng ([FAIR_PLANNER_COMPARISON_RESULTS.json](FAIR_PLANNER_COMPARISON_RESULTS.json)): khi dùng đầu vào `typed-facts/2` chuẩn `Source Gate` (`Arm A2`), **`Planner /26` giải đúng `32/33` ca dương (`avg 17.666 ms`)** (rớt duy nhất `B09` ở `IR_MEMORY_BUDGET_EXCEEDED`). Tuy nhiên, `Arm C (/2)` vượt trội ở **3 năng lực cốt lõi**: (a) dựng đầy đủ đối tượng phụ phi-cạnh và `perpendicular_witness` kiểm chứng vào `Scene3D` (**`33/33`** so với **`2/33`** ở `Arm A2`, cụ thể `14/16` ca cần đối tượng phụ ngầm định không có hình phụ ở `Scene3D` cũ); (b) tìm và chuyển đổi nhiều phương án dựng hình tự chứa trên `Group E` (**`5/5`** so với **`0/33`**); (c) giải vượt trần 32 IR slots trên chuỗi 19 bước `B09` (**`33/33`** vs `32/33`).

4. **Có bao nhiêu ca thật sự cần phát hiện đối tượng phụ?**
   Trên 33 ca dương của `/1`, có **`16/33`** ca `HAS_GENUINE_IMPLICIT_AUXILIARY_OBJECT` (`17` ca được gắn nhãn `N3_IMPLICIT_AUXILIARY_DISCOVERY` nếu tính cả `A07` phát hiện đoạn chiếu chứng nhân `seg_C_A`) nơi đề bài không gọi tên điểm/đoạn trung gian nhưng hệ thống tự dựng chân đường cao, đường thẳng song song truyền khoảng cách hoặc tia góc nhị diện.

5. **Có bao nhiêu ca chỉ sắp xếp những phép dựng đã được chỉ định?**
   Theo [CONSTRUCTION_NOVELTY_RECLASSIFICATION.json](CONSTRUCTION_NOVELTY_RECLASSIFICATION.json), có **`12/40`** ca (`A02..A04, A09, B01, B02, B06..B10, C08`) thuộc nhóm `N1_EXPLICIT_CONSTRUCTION_SCHEDULING` (chủ yếu lập lịch các điểm trung điểm/trọng tâm/tỉ lệ/giao điểm đã nêu trong đề); **`4/40`** ca thuộc `N0_EXISTING_COMPLETE_RECIPE` (`A01, A05, A06, A08`).

6. **Có bao nhiêu ca tổ hợp toán tử không có recipe hoàn chỉnh?**
   Có **`22/40`** ca được gắn nhãn đa chiều `N2_OPERATOR_COMPOSITION` (kết hợp từ `>= 2` toán tử và có công đoạn khám phá hoặc ghép mục tiêu vượt khỏi một recipe đơn lẻ).

7. **Có bao nhiêu ca tự phát hiện được chiến lược dựng phụ?**
   Có **`17/40`** ca gắn `N3_IMPLICIT_AUXILIARY_DISCOVERY` và **`14/40`** ca gắn `N4_ALTERNATIVE_VERIFIED_STRATEGY` (tìm ra `>= 2` chiến lược chứng minh độc lập đạt cùng đáp số và vượt `validate_multiplan_switching`, gồm toàn bộ `5/5` Group E và các ca `B03..B06`, `C01..C05`).

8. **Các chứng chỉ toán học có chống được mutation không?**
   **Có (`12/12 = 100%` bị chặn).** Sau khi nâng cấp `construction-exact-verifier/2` (tái thực thi toàn bộ operator đại số ở `L2`, tái tính mục tiêu trên bao đóng ngược ở `L3`, và gọi đúng `certificates.verify_perpendicular_witness` ở `L4`), tất cả `12/12` kịch bản tấn công (`M01..M10`, `M11` sửa witness trong `Scene3D`, `M12` tiêm đối tượng ma/token vào `PresentationStepGraph`) đều bị từ chối sạch, trong đó **`11/12`** kịch bản từng lọt qua verifier `/1` ([PROOF_MUTATION_TEST_RESULTS.json](PROOF_MUTATION_TEST_RESULTS.json)).

9. **Search có bị rò oracle hoặc tính trước goal không?**
   **Không.** Kiểm tra AST tĩnh trên `construction_state.py`, `construction_operators.py`, `construction_search.py`, `construction_verifier.py` ghi nhận **`0` tham số oracle**; mã nguồn không gọi `evaluate_goal` ngoài điều kiện dừng chứng nhận; đồ thị `C01` giữ SHA-256 `d2ba32353460872a9154b66ff1d278cf6e9ed5e32dc8b3240bc33ae24dd5431f` bất biến với oracle ngoài; cùng một khung `f_c01` rẽ sang `a√21/7` (`distance_point_plane`) hoặc `a³√3/12` (`solid_volume`) hoàn toàn theo `GoalSpec` ([ORACLE_ISOLATION_REPORT.md](ORACLE_ISOLATION_REPORT.md)).

10. **Có tồn tại lỗi hình học khi đổi tên đỉnh hoặc hệ tọa độ không?**
    **Không.** Toàn bộ **`9/9`** phép biến đổi trong [GEOMETRY_INVARIANCE_RESULTS.json](GEOMETRY_INVARIANCE_RESULTS.json) — đổi tên đỉnh, hoán vị pending, tịnh tiến hữu tỉ, quay `SO(3, Q)`, biến đổi cơ sở tổng quát `GL(3, Q)` với hiệp biến tensor Gram $G' = A^{-T} G A^{-1}$ trên lăng trụ xiên không chéo, đối xứng gương, phóng đại $\times 3$, đổi biểu diễn đường thẳng, và đổi pháp tuyến mặt phẳng — đều giữ **100% bất biến đáp số**, `L0`–`L4 PASS`, và **`graph_structural_isomorphism_signature` trùng khớp tuyệt đối**.

11. **Kết quả trên bài toán mới khác bao nhiêu so với `/1`?**
    Trên tập holdout mới hoàn toàn `N=60` (`44` dương + `16` âm, chạy single-shot sau khi đóng băng `CANDIDATE_V2_FREEZE_SHA256 = 26c9b505...`, `EXTERNAL_INDEPENDENCE = NOT_MEASURED`, [INDEPENDENT_CONSTRUCTION_EVALUATION.json](INDEPENDENT_CONSTRUCTION_EVALUATION.json)):
    - Tổng thể đạt **`53/60` (`88.3%`)**: dương **`42/44` (`95.5%`)** (`100%` đạt `L0`–`L4` và Presentation 6 bất biến, **`0` đáp số sai hay chứng minh lậu**), âm tính **`11/16` (`68.8%` đúng mã nhãn chính xác, nhưng `16/16 = 100%` an toàn không bịa đáp số)**.
    - Đặc biệt đạt `6/6` trên lăng trụ xiên chart Gram không chéo (`ObliquePrism_Gram`), `6/6` chóp chữ nhật lệch cạnh (`RightRect_1_2_2`), `6/6` chóp tam giác vuông lệch cạnh (`RightTri_1_2_2`), `7/7` chóp tứ giác đều cạnh `a`, `6/6` chóp tam giác đều (`1_1` & `1_2`), `10/11` hình hộp chữ nhật `1:2:2`.
    - Khoảng hở thật sự lộ diện ở `7` ca rớt so với `40/40` của `/1` (giữ nguyên không chỉnh code sau holdout): (1) va chạm bí danh cùng tọa độ (`H17`, `H44`, `HN05`: điểm dựng mới trùng tọa độ điểm sẵn có `O`/`O1` bị lọc trùng khóa trước khi khớp mục tiêu); (2) thiếu tiền kiểm định nhãn mục tiêu trước BFS (`HN04` đỉnh `Z_MISSING`, `HN13`/`HN14` bán kính mặt cầu trả `NO_PLAN_FOUND_WITHIN_BUDGET` thay vì `MISSING_PRECONDITION`/`UNSUPPORTED_OPERATOR`); (3) `HN11` quote mâu thuẫn dừng ngay ở Source Gate `MISSING_PRECONDITION` (`SOURCE_PREMISE_UNREAD`).

12. **Search có ổn định khi số nhánh tăng không?**
    **Có và fail-closed đúng loại lỗi.** Trong [SEARCH_STRESS_BENCHMARK.json](SEARCH_STRESS_BENCHMARK.json): chuỗi tăng độ sâu từ `2` lên `20` bước pending (`proof_nodes = 7..25`) đều giải `GOAL_VERIFIED` ổn định trong **`19.02 – 58.343 ms`**; giới hạn `max_expanded_states=1` trả đúng **`SEARCH_RESOURCE_LIMIT`**, giới hạn thời gian cực chặt trả đúng **`SEARCH_TIMEOUT`** — **tuyệt đối `0` ca bị gán nhầm thành `CONTRADICTORY_CONSTRAINTS`**.

13. **Chi phí end-to-end thực tế là bao nhiêu?**
    - Trên 40 ca `/1` ([FAIR_PLANNER_COMPARISON_RESULTS.json](FAIR_PLANNER_COMPARISON_RESULTS.json)): `Arm C (/2)` mất trung bình **`65.463 ms`** (Planner-only) và **`85.641 ms`** (E2E `VerifiedInputBridge + Source Gate + Search + L0–L4`), so với **`17.666 ms`** của `Arm A2` (~3.7x–4.8x).
    - Phân tích chi tiết 9 chặng trên `B01` ([SEARCH_STRESS_BENCHMARK.json](SEARCH_STRESS_BENCHMARK.json)): `Bridge + Source Gate = 33.969 ms` (`72.2%`), `Dynamic Search = 11.866 ms`, `Scene3D Compile = 0.219 ms`, `L0–L4 Strict Verify = 0.986 ms` -> tổng **`47.040 ms`** (vs `Arm A2 = 28.494 ms`).
    - Trên Holdout `N=60`: trung bình tìm kiếm **`134.17 ms`** (chủ yếu tăng ở `6` ca budget exhaustion quét hết không gian).

14. **Có thể tái sử dụng bao nhiêu toán tử với Exact Kernel hiện hành?**
    **100% tính toán đại số tái sử dụng Exact Kernel (`/24`: `exact.py`, `metric.py`, `measure.py`, `section.py`)**; về mặt hợp đồng hàm mức `Registry /33`: **`16/23`** toán tử dựa trên nền có sẵn hoặc đồng đẳng trực tiếp (`EXISTS_IN_REGISTRY_33`), còn **`7/23`** toán tử hình học phụ & suy diễn là phần mở rộng mới chưa có hợp đồng riêng trong `Registry /33`.

15. **Những phần nào vẫn cần thay đổi Registry hoặc Planner?**
    (a) Mở hợp đồng cho `7` toán tử phụ/suy diễn (như `plane_through_point_parallel_plane`, `common_perpendicular_skew_lines`, `construct_dihedral_linear_angle`, v.v.); (b) Nới hoặc thay cơ chế trần tĩnh `MAX_MEMORY_DECLARATIONS = 32` trong `Planner /26` (`B09`); (c) Sau `/2`, bổ sung cơ chế alias tọa độ cho điểm trùng nhau (`H17, H44, HN05`) và phân loại tiền kiểm định `GoalSpec` (`HN04, HN13, HN14`).

16. **Backend đã được tích hợp thật hay mới có adapter?**
    Mới dừng ở **tầng Adapter cô lập + Handoff Patch sẵn sàng áp dụng**, chưa sửa mã sản phẩm vì `backend/app/**` thuộc `BLOCKED_OWNERSHIP` (`INTEGRATION_STATUS = BLOCKED_OWNERSHIP`, `Gate F7 = BLOCKED_OWNERSHIP`). Đã hoàn thiện `verified_input_bridge.py`, `integration_adapter.py` (`off`/`shadow`/`experimental` + `SAFE_VERIFIED_LEGACY_FALLBACK` + `FAIL_CLOSED_REFUSED`), và patch [backend_adapter4_dynamic_construction_flag.patch](handoff/backend_adapter4_dynamic_construction_flag.patch) vượt `git apply --check` ([CONSTRUCTION_BACKEND_INTEGRATION_REPORT.md](CONSTRUCTION_BACKEND_INTEGRATION_REPORT.md)).

17. **Scene3D đã hỗ trợ chuyển phương án thực tế chưa?**
    Chế độ chuyển phương án hoạt động đầy đủ ở tầng **Backend Bundle + 7-Invariant Switch Validator (`5/5` Group E PASS)** kèm bản vá frontend [frontend_scene3d_multiplan_switcher.patch](handoff/frontend_scene3d_multiplan_switcher.patch) đạt `git apply --check`; nhưng UI `frontend/` nằm trong worktree riêng `axo-geometry-library` (`BLOCKED_OWNERSHIP`) nên trạng thái là **`Gate F8 = PASS_ARTIFACT_ONLY`** ([SCENE3D_INTEGRATION_REPORT.md](SCENE3D_INTEGRATION_REPORT.md)).

18. **Các bước trình bày có bảo toàn chứng cứ không?**
    **Có.** `PresentationStepGraph` vượt đủ **6 bất biến** kiểm định bởi `presentation_validator.py` (`issue_count = 0` trên `33/33` `/1` và `42/42` Holdout served), mọi bước đều trỏ `construction_graph_refs` về nút `VERIFIED`, giữ thứ tự topo, tách `MEASURE_GOAL`, và chặn sạch rò rỉ token nội bộ (`M12` bị từ chối với `PRESENTATION_INVARIANT_FAILED`) ([PRESENTATION_STEP_VALIDATION.md](PRESENTATION_STEP_VALIDATION.md)).

19. **Model 2 cần thiết ở phần nào mà deterministic selector chưa giải quyết?**
    `DeterministicModel2BaselineSelector` đã giải quyết sạch 100% trình tự mở từng bước dựng hình theo topo, đổi phương án, phát lại bước, và giải thích chuẩn hóa bảo toàn chứng cứ (`0` lỗi phụ thuộc). Model 2 trong tương lai **chỉ cần thiết** cho các tác vụ sư phạm linh hoạt chưa có trong luồng tất định: trả lời câu hỏi tự do ngược dòng của học sinh (*"vì sao không chiếu lên cạnh khác?"*), chọn góc nhấn sư phạm theo năng lực người học, hoặc diễn đạt đối thoại giàu ngữ cảnh mà vẫn bị ràng buộc bởi `validate_model2_action` ([MODEL2_DETERMINISTIC_BASELINE.md](MODEL2_DETERMINISTIC_BASELINE.md)).

20. **Những điều kiện nào còn thiếu để nghiệm thu sản phẩm (Level 3 / Level 4)?**
    1. Chủ sở hữu áp dụng và nghiệm thu thực tế `backend_adapter4_dynamic_construction_flag.patch` + `frontend_scene3d_multiplan_switcher.patch` dưới `AXO_DYNAMIC_CONSTRUCTION_MODE = "off"` / `"shadow"` (khắc phục `BLOCKED_OWNERSHIP` của `F7`/`F8`).
    2. Thực nghiệm holdout ngoài hoàn toàn độc lập (`EXTERNAL_INDEPENDENCE = NOT_MEASURED`).
    3. Khắc phục các phát hiện trên holdout sau đóng băng (`H17/H44/HN05` alias trùng điểm, `HN04/HN13/HN14` tiền kiểm định mục tiêu) trong wave kế tiếp, cùng đầy đủ E2E trình duyệt + người dùng thật.
