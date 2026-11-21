# EXISTING CONSTRUCTION ARCHITECTURE AUDIT (`AXO CONSTRUCTION /1` — Phase A)

- **Run ID:** `axo-construction-verified-graph-dynamic-planner-feasibility`
- **Verified Base HEAD:** `498f354608c45ce98ba4f75a0222afbe56139ce2`
- **Branch:** `feat/local-first-geometry-understanding`
- **Product Baseline:** `product_commit = 6310113f2202bc3a4919406b26fad08cb09b38c9`, `measured_system_sha256 = 113a6a7cf6bbc15ac23119150b805437e785d2b0714b26c2157d147514c2ef67` (`123` files), `CACHE_VERSION = 145` (`145:route-d`)
- **Audit Script:** [audit_existing_construction_architecture.py](file:///D:/Documents/projects/algo-sim/.superpowers/worktrees/local-first-geometry-understanding/backend/scripts/audit_existing_construction_architecture.py)
- **Machine Inventory:** [CONSTRUCTION_CAPABILITY_INVENTORY.json](file:///D:/Documents/projects/algo-sim/.superpowers/worktrees/local-first-geometry-understanding/docs/evaluation/geometry/runs/axo-construction-verified-graph-dynamic-planner-feasibility/CONSTRUCTION_CAPABILITY_INVENTORY.json)

> [!IMPORTANT]
> Kiến trúc hiện hành **không hoàn toàn tĩnh** (`_EffectResolver` đã có regression theo `PlanningContract` giới hạn ở độ sâu 4 và `7` macro auxiliary schemas), nhưng cũng **chưa phải Dynamic Construction Planner** theo nghĩa tìm kiếm, chứng minh, lưu nhiều phương án và tách `ConstructionProofGraph` khỏi `PresentationStepGraph`.

---

## 1. Hợp đồng phiên bản & Quyền sở hữu đã xác minh

| Thành phần | Module kiểm tra | Phiên bản thực tế | Trạng thái sở hữu |
| --- | --- | --- | --- |
| Local Parser | [local_geometry_parser.py](file:///D:/Documents/projects/algo-sim/.superpowers/worktrees/local-first-geometry-understanding/backend/app/ai/local_geometry_parser.py) | `local-geometry-parser/2` | Chỉ đọc (`backend/app/**` đóng băng) |
| Typed Facts Next | [typed_fact_next.py](file:///D:/Documents/projects/algo-sim/.superpowers/worktrees/local-first-geometry-understanding/backend/app/simulation/geometry_functions/typed_fact_next.py) | `typed-fact-next/2` | Chỉ đọc |
| Bridge | [typed_fact_next_bridge.py](file:///D:/Documents/projects/algo-sim/.superpowers/worktrees/local-first-geometry-understanding/backend/app/simulation/geometry_functions/typed_fact_next_bridge.py) | `typed-fact-next-bridge/2` | Chỉ đọc |
| Planner | [planner.py](file:///D:/Documents/projects/algo-sim/.superpowers/worktrees/local-first-geometry-understanding/backend/app/simulation/geometry_functions/planner.py) | `geometry-fact-planner/26` | Chỉ đọc |
| Registry | [registry.py](file:///D:/Documents/projects/algo-sim/.superpowers/worktrees/local-first-geometry-understanding/backend/app/simulation/geometry_functions/registry.py) | `geometry-functions/33` | Chỉ đọc |
| Exact Kernel | [engine.py](file:///D:/Documents/projects/algo-sim/.superpowers/worktrees/local-first-geometry-understanding/backend/app/simulation/geometry_functions/engine.py) | `geometry-function-engine/24` | Chỉ đọc (tái sử dụng trực tiếp) |
| Adapter /4 | [adapter4_route.py](file:///D:/Documents/projects/algo-sim/.superpowers/worktrees/local-first-geometry-understanding/backend/app/ai/adapter4_route.py) | `hybrid-simulation-adapter/4` | Chỉ đọc (lưu ý vị trí thực tại `backend/app/ai/`) |
| Continuity & Certs | [construction_continuity.py](file:///D:/Documents/projects/algo-sim/.superpowers/worktrees/local-first-geometry-understanding/backend/app/simulation/geometry_functions/construction_continuity.py), [certificates.py](file:///D:/Documents/projects/algo-sim/.superpowers/worktrees/local-first-geometry-understanding/backend/app/simulation/geometry_functions/certificates.py) | `exact-gram-line-plane-orthogonality/1` | Chỉ đọc (tái sử dụng trực tiếp) |
| Frontend Scene3D | [Scene3DExplorer.tsx](file:///D:/Documents/projects/algo-sim/.superpowers/worktrees/local-first-geometry-understanding/frontend/src/simulations/domains/geometry/Scene3DExplorer.tsx) | — | **`BLOCKED_OWNERSHIP`** (worktree `axo-geometry-library`) |

---

## 2. Trả lời 14 câu hỏi kiểm toán bắt buộc (§2)

1. **Planner `/26` đang thực hiện lập kế hoạch, lựa chọn công thức hay thực sự tìm kiếm phép dựng?** (`PARTIAL`)
   `lap_ke_hoach` (`planner.py:642-826`) kết hợp 3 lớp: (a) ánh xạ 1-1 tiền đề qua `_LUAT` và mở rộng định nghĩa (`regular_pyramid`, `rectangle`); (b) `7` quy tắc macro phụ đăng ký sẵn trong `AUXILIARY_RULES`; (c) tìm kiếm hồi quy mục tiêu ngược bị chặn (`_EffectResolver`, `planner.py:2454`, `MAX_EFFECT_DEPTH = 4`, `MAX_EFFECT_NEEDS = 96`, `MAX_EFFECT_CANDIDATES = 48`) trên `15/64` hàm có `PlanningContract`. Khi nhiều lựa chọn hợp lệ cùng tồn tại, `_EffectResolver` chỉ giữ một nhánh chi phí thấp nhất (`min(choices, ...)`). Vì vậy hệ thống có tìm kiếm chuỗi nhỏ theo effect-slot nhưng **chưa** tìm kiếm đồ thị dựng hình tổng quát hay tách metric solver khỏi phép dựng hình học.

2. **Registry `/33` chứa những phép dựng nguyên tử nào?** (`PARTIAL`)
   Kiểm toán trực tiếp cho thấy `REGISTRY` có **`64` hàm**: `24` `fact` (tiền đề), `23` `ask` (truy vấn đại lượng), `16` `construct` (`centroid`, `curved_section`, `curved_solid`, `curved_subsolid`, `divide_segment`, `intersect_line_line`, `intersect_line_plane`, `intersection_line`, `midpoint`, `orthogonal_projection_line`, `point_reflection`, `prism`, `pyramid`, `regular_pyramid`, `section`, `translate_point`), và `1` `escape` (`unsupported`). Trong đó chỉ **`15/64`** hàm khai báo `PlanningContract` cho `_EffectResolver`; `divide_segment`, `point_reflection`, `ask_angle_plane_plane`, `ask_volume`, `ask_section_area`, `ask_distance_planes` đều có **`planning_contract_count = 0`**.

3. **Có hỗ trợ tạo đối tượng phụ không?** (`PARTIAL`)
   Có ở mức hẹp: qua `7` quy tắc `AUXILIARY_RULES` (`MAT_SONG_SONG`, `MAT_HAI_DUONG`, `MAT_VUONG_DUONG`, `MAT_RANG_BUOC`, `DINH_CAT_CANH`, `distance(point,line)`, `section(...)`), `POINT_DEFINITIONS` (`orthocenter`, `circumcenter`), và kết nối effect-chain cho `@described_point` (`typed_fact_next_v2`). Tuy nhiên, đối với bài toán phổ biến như `d(A, (SBC))` (chóp `S.ABC`), thực nghiệm trực tiếp xác nhận Adapter `/4` trả về `a√2/2` trong `answers['q1']` **nhưng `scene3d.objects` không chứa điểm phụ `H` hay đoạn cao `AH`** (`has_auxiliary_foot_point = false`).

4. **Có cơ chế biểu diễn sự phụ thuộc giữa các bước không?** (`EXISTS_VERIFIED` ở mức danh sách / `ABSENT_VERIFIED` ở mức Proof DAG tách biệt)
   `Planner /26` sắp xếp thứ tự gọi hàm theo đồ thị phụ thuộc (`_sap_xep_phu_thuoc_loi_goi`, `planner.py:849`), phát sinh các tier 0→5; sau đó `construction_continuity.py` bổ sung `depends_on`, `visible_prerequisites`, `created_ids`, `reused_ids` trên `scene3d.formation.steps`. Tuy nhiên chưa có cấu trúc `VerifiedConstructionGraph` phân biệt tường minh nút `GIVEN` / `CONSTRUCTION` / `DERIVED_RELATION` / `VERIFICATION` / `GOAL`.

5. **Bước dựng có được kiểm chứng bằng điều kiện toán học không?** (`PARTIAL`)
   Tầng thực thi hình học (`geometry/kernel.py`, `engine.py`, `certificates.py`) kiểm tra chặt trong không gian phân số chính xác `Fraction` + Gram `Metric` (ma trận Gram SPD theo tiêu chuẩn Sylvester, giao cắt không suy biến `GeometryError`, `certify_line_plane_perpendicularity` với `dot(u1) == 0` và `dot(u2) == 0`). Tuy nhiên ở pha lập kế hoạch, `_EffectResolver` mới khớp chữ ký slot (`Point`, `PerpDir`, `Meet`) chứ chưa chạy chứng minh hình học/kiểm suy biến cho từng bước trung gian trước khi phát hành kế hoạch.

6. **Một kết quả hình học có thể có nhiều phương án dựng không?** (`ABSENT_VERIFIED`)
   `Planner /26` (`_EffectResolver._resolve`) luôn thu gọn về một `_Choice` duy nhất nhỏ nhất theo chi phí; `KeHoach` chỉ lưu một chuỗi `calls: list[dict]` duy nhất, không giữ hay xếp hạng các phương án thay thế (ví dụ hạ trực tiếp hình chiếu lên mặt phẳng so với dựng hai bước cổ điển qua trung gian cạnh đáy `BC -> SM -> AH`).

7. **Có hỗ trợ các chuỗi dựng dài tùy biến không?** (`PARTIAL`)
   Về mặt số học kernel (`geometry/kernel.py`), không bị giới hạn độ dài; nhưng `Planner /26` khóa chặt `_EffectResolver` tại `MAX_EFFECT_DEPTH = 4` (`MAX_CALLS = 64`), còn `validator.py:143` giới hạn bảng bộ nhớ IR `SemanticProgramSpec` tại **`MAX_MEMORY_DECLARATIONS = 32`** (gây lỗi `IR_MEMORY_BUDGET_EXCEEDED` với chuỗi dài như `MG9`).

8. **Có phát hiện vòng phụ thuộc không?** (`EXISTS_VERIFIED`)
   Thực nghiệm trên `_sap_xep_phu_thuoc_loi_goi` với hai lệnh `midpoint` phụ thuộc chéo (`M <-> N`) trả ngay ngoại lệ `TuChoi("DEPENDENCY_CYCLE", "phụ thuộc vòng qua c2 → c1")`.

9. **Có khả năng loại bỏ bước dư thừa không?** (`PARTIAL`)
   `planner.py:752-762` gộp lời gọi trùng tên hàm + JSON `args`, và `scene3d` xuất `unused_auxiliary_ids`; nhưng chưa có cơ chế định danh hình học chính tắc bất biến theo phương trình đường/mặt (`canonical_geom_key` tách khỏi nhãn biến `object_id`) và cắt tỉa đồ thị theo closure của mục tiêu `GOAL`.

10. **Scene3D hiện nhận danh sách thao tác, đồ thị hay một biểu diễn khác?** (`EXISTS_VERIFIED`)
    `Scene3D` (`scene3d.py`) nhận một `dict` phẳng gồm `objects` (mảng thực thể có `depends`, `computational_depends`, `visible_prerequisites`), `events` (danh sách `INIT`/`CREATE`/`HIGHLIGHT`/`READOUT`) và `formation.steps` (mảng bước tuyến tính kèm `step_summary` 5 phần). `Scene3DExplorer.tsx` tiêu thụ trực tiếp cấu trúc này để dựng cây thành phần và thanh phát theo bước.

11. **Các bước hiển thị cho học sinh có tương ứng với các phép toán được kiểm chứng không?** (`PARTIAL`)
    Với các phép dựng đã được engine tạo ra (như `midpoint`, `section`, `segment` có `perpendicular_witness`), `construction_continuity.py` nối `verification_refs` vào chứng chỉ kernel. Nhưng với các câu hỏi metric tính thẳng (`ask_distance_point_plane`, `ask_distance_line_plane`, `ask_angle_plane_plane`), hệ thống trả lời đúng con số mà không có bước dựng đối tượng chứng kiến tương ứng trên `Scene3D`.

12. **Có giới hạn nào xuất phát từ Registry hoặc Exact Kernel chứ không phải Planner?** (`EXISTS_VERIFIED`)
    Có 3 nhóm giới hạn đã xác minh từ Registry/Kernel/IR:
    - `Registry /33` chưa gắn `PlanningContract` cho `divide_segment`, `point_reflection`, `ask_angle_plane_plane`, `ask_volume`, `ask_section_area`, `ask_distance_planes` (`49/64` hàm không có contract).
    - `geometry_functions/registry.py` + `measure.py` xem `ask_distance_*` là truy vấn vô hướng thay vì phép dựng có chứng nhân bắt buộc.
    - `semantic_program/validator.py` giới hạn `MAX_MEMORY_DECLARATIONS = 32`.

13. **Những quy trình nào đang được hardcode?** (`EXISTS_VERIFIED`)
    - `7` quy tắc trong `AUXILIARY_RULES` (`MAT_SONG_SONG`, `MAT_HAI_DUONG`, `MAT_VUONG_DUONG`, `MAT_RANG_BUOC`, `DINH_CAT_CANH`, `distance(point,line)`, `section(...)`).
    - Luật ánh xạ đề bài 1-1 `_LUAT` và mở rộng khối `chóp đều` / `lập phương` / `hình hộp chữ nhật` trong `planner.py`.
    - Bố cục tọa độ khối cơ sở trong `engine.py`.

14. **Những khả năng nào đã là dynamic và có thể tái sử dụng?** (`EXISTS_VERIFIED` — **tái sử dụng trực tiếp trong nguyên mẫu**)
    - **Hệ tọa độ affine + Gram `Metric` chính xác** từ tiền đề (`bridge_v2 -> lap_ke_hoach -> dung_tu_loi_goi` chạy với `math_goals=[]`, thu được `points` phân số chính xác và `chart_metric` SPD — đã xác minh chạy thành công).
    - **Toàn bộ thư viện phép dựng nguyên tử** trong `app.simulation.geometry.kernel`, `exact`, `metric`, `measure`, `radical`, `section`.
    - **Bộ chứng chỉ & kiểm tra liên tục**: `certificates.py` (`validate_gram_metric_spd`, `certify_line_plane_perpendicularity`, `certify_deductive_line_plane_perpendicularity`) và `construction_continuity.py` (`enrich_construction_continuity`, `validate_construction_continuity`).
    - **Cổng kiểm định đáp số toán học độc lập**: `slm_math_evaluator_v2` (`axo-math-evaluator/2`).

---

## 3. Khuyến nghị thiết kế nguyên mẫu cho Phase B–H

1. **Không viết lại Exact Kernel**: tái sử dụng hoàn toàn `engine.dung_tu_loi_goi` ở chế độ tiền đề-only để khởi tạo hệ quy chiếu `GIVEN` + `chart_metric` SPD, sau đó vận hành mọi operator nguyên mẫu bên trong `with metric.using(chart_metric):`.
2. **Đặt nguyên mẫu tách biệt tại `backend/experimental/construction_planner/`**: giữ nguyên `backend/app/**` (`123` file đóng băng) và `frontend/**` (`BLOCKED_OWNERSHIP`).
3. **Khắc phục trực tiếp 4 khoảng trống lớn nhất của `Planner /26`**:
   - Tách rõ `ConstructionProofGraph` và `PresentationStepGraph` (`verified-construction-graph/1`).
   - Bắt buộc mọi mục tiêu khoảng cách/góc/thể tích phải có **chứng nhân dựng hình hợp lệ** (`distance(P, Q)` phải dựng chân đường vuông góc `H` hoặc chuỗi dựng gián tiếp song song, kèm chứng chỉ Gram `L2`).
   - Lưu giữ và xếp hạng đa phương án (`Group E`) thay vì thu gọn greedy về một nhánh.
   - Không bị ràng buộc bởi `MAX_MEMORY_DECLARATIONS = 32` trong quá trình tìm kiếm đồ thị dựng hình.
