# Kiểm toán hợp đồng mô phỏng (P1)

Phạm vi: đường thực thi thật của `POST /api/analyze` ở `HYBRID_ROUTE_MODE=local-only-scoped` tại commit
`a0f979392` (nhánh `integration/local-only-3d-live-acceptance`). Mỗi câu trả lời nêu chỗ đọc mã và bằng chứng live
(lượt 2, `evidence/browser/`), không suy từ việc có hay không có một hàm cùng tên.

## Đường thực thi

```
/api/analyze → main._analyze_hybrid_route → ai/hybrid_offline (local-only-scoped)
  → ai/adaptive_input_router: parser tất định trước (ai/local_geometry_parser, không LLM)
      đọc đủ mọi mệnh đề  ⇒ LOCAL_DETERMINISTIC_PARSER
      còn mệnh đề chưa đọc ⇒ SLM AxoV9 qua llama.cpp (ai/local_slm_extractor) ⇒ LOCAL_SLM_GROUNDED
  → TypedFactNext /2 → bridge_v2 → registry.kiem_nguon (Source Gate) → planner /26 → engine /24 + certificates
  → ai/adapter4_route (+ construction_continuity) → envelope.scene3d + route_d
→ frontend Scene3DExplorer (three.js), nhãn đỉnh là lớp DOM `.geo3d-label`
```

## 14 câu hỏi bắt buộc

| # | Câu hỏi | Trả lời | Nguồn / bằng chứng |
|---|---|---|---|
| 1 | Input nào là yêu cầu mô phỏng? | Câu lệnh cuối khớp quy tắc 7b `(Hãy) (mô phỏng\|vẽ) hình (chóp\|lăng trụ)? (và điểm X)?` ⇒ `simulation_goals=[construct_object]`. Đề chỉ có giả thiết ("Cho…/Một hình chóp…") cũng được parser gắn `construct_object` cho khối đã khai báo. Router tính "mục tiêu đầy đủ" khi có động từ `vẽ\|dựng\|mô phỏng\|biểu diễn\|cho … xem` hoặc có mục tiêu toán. | `local_geometry_parser.py:3881` (7b), `:1323–1671` (construct_object theo họ khối), `adaptive_input_router.py:987`; V15 (không có động từ) SERVED |
| 2 | Input nào là yêu cầu tính toán? | Mệnh đề "Tính/Tìm/Xác định …" khớp luật mục tiêu ⇒ `math_goals` (`ask_*`). | `local_geometry_parser.py` luật 7c–7e |
| 3 | Có bắt buộc `ask_*` để khởi tạo Scene3D? | **Không.** `TypedFactNext /2` là *simulation-first*: bắt buộc ≥1 `simulation_goal`, `math_goals` tuỳ chọn. | `typed_fact_next.py:1016` (`EMPTY_SIMULATION_GOALS`); 14/28 ca SIMULATE_ONLY SERVED với `answers={}` |
| 4 | Tạo Scene3D từ giả thiết thuần? | Có, khi parser tất định đọc được mọi mệnh đề. | V15 SERVED |
| 5 | Chóp/lăng trụ hợp lệ không hỏi độ dài/thể tích? | Có. | V01, V03, V07, V21, V25… SERVED, oracle hợp lệ |
| 6 | Scene3D lấy dữ liệu từ đâu? | `envelope.scene3d` do `adapter4_route` dựng từ kết quả engine: `objects` (toạ độ `xyz` là chuỗi phân số chính xác), `chart_metric`, `events`, `formation`. | responses_pass2.jsonl |
| 7 | Khi nào là "đã kiểm chứng"? | Chỉ khi `route_d.status=SERVED`: đã qua Source Gate, planner, engine + chứng chỉ, và `verify_and_compile` của adapter. Mọi nhánh khác là từ chối có mã. | `adapter4_route.py`, `semantic_program/route.py` |
| 8 | Hệ toạ độ và metric? | Khung affine hữu tỉ + ma trận Gram `chart_metric` (không mặc định Euclid; tam giác đều cho G=`[[1,½,0],[½,1,0],[0,0,1]]`). Frontend ánh xạ T·p một lần ở biên hiển thị. | D1 probe; `scene3d-chart.ts` |
| 9 | Quan hệ nào kiểm bằng Exact Kernel? | Độ dài, vuông góc đường–đường/đường–mặt/mặt–mặt, song song, trung điểm, chia tỉ lệ, trọng tâm, hình chiếu, khoảng cách, góc, thể tích — số học `Fraction`/`Radical`. Oracle độc lập của run kiểm lại 40/40 cảnh. | `SCENE3D_MATHEMATICAL_VALIDATION.json` |
| 10 | Quan hệ nào chỉ giả định ở renderer? | Không có quan hệ hình học nào được tính ở renderer; renderer chỉ chiếu, phân loại nét khuất (nét đứt) và bố trí nhãn. Phân loại khuất/hiện là quyết định hiển thị, không phải chứng minh. | `OCCLUSION_AND_SCENE_IDENTITY_AMENDMENT.md` |
| 11 | Thao tác tương tác có sẵn? | Xoay, thu phóng, đặt lại góc nhìn, bước trước/sau/phát, X-ray, menu lớp hiển thị (Vỏ khối, **Nhãn**, Thông số hình học, Mặt phẳng, Thiết diện, Hình phụ, Trục Oxyz, Lưới nền), chọn đối tượng qua chip, toàn màn hình. | `evidence/ui4/ui_scenarios.json` |
| 12 | Bước dựng nào có trong production? | Bước tích luỹ từ `events` (`construction_continuity`): dựng đáy → đường cao → cạnh bên → hoàn thiện. **Construction /2 (dynamic planner) không nằm trong sản phẩm** ⇒ `DYNAMIC_CONSTRUCTION_STEPS = NOT_IN_PRODUCT`. | U07; `.geo3d-progress` |
| 13 | Nguy cơ hiển thị hình cũ khi đổi đề? | Không quan sát thấy: đổi đề trong cùng phiên (U02), phục vụ→từ chối (U03, canvas bị gỡ), từ chối→phục vụ (U04); 2×40 cảnh có tập nhãn đúng bằng gold. | U02–U04 |
| 14 | Cache trả Scene3D không khớp đề? | Không quan sát thấy. Mỗi lượt chạy trên DB mới; khoá cache gồm văn bản đề + `CACHE_VERSION` (khoá bởi `test_cache_identity.py`). Run này không tấn công cache riêng. | `tests/test_cache_identity.py` |

## Phát hiện về hợp đồng (không sửa trong /10)

1. **Phủ câu lệnh mô phỏng hẹp (blocker chính của SIMULATE_ONLY).** Quy tắc 7b chỉ nhận `mô phỏng|vẽ hình (chóp|lăng trụ)`.
   "Hãy mô phỏng hình lập phương / tứ diện / hình hộp / lăng trụ (tam giác đều) …", "Hãy dựng hình chóp", "Vẽ hình chóp S.ABCD.",
   "Mô phỏng hình hộp chữ nhật đó" để lại `UNPARSED_GOAL_CANDIDATE` ⇒ rơi sang SLM ⇒ SLM đề xuất mục tiêu không khớp nguồn ⇒
   Source Gate chặn (`SOURCE_OBJECT_MISMATCH`/`AMBIGUOUS_FACT`). An toàn (không phục vụ sai) nhưng 11/28 ca SIMULATE_ONLY (V02, V06, V08,
   V09, V10, V11, V14, V16, V19, V26, V28) bị từ chối vì lý do này; thêm V05 ("tất cả các cạnh đều bằng a" — mệnh đề dữ kiện chưa đọc).
   Sửa thuộc `local_geometry_parser.py` (luật 7b dùng chung cho mọi họ khối), cần owner duyệt — xem `OWNER_HANDOFF.md`.
2. **"Biểu diễn …" không phải từ hỏi.** "Hãy mô phỏng và biểu diễn khoảng cách/góc …" bị chặn `NOT_ASKED_IN_SOURCE`/`AMBIGUOUS_VALUE_QUOTE`.
   Đúng luật Source Gate hiện hành (không trả lời điều đề không hỏi); không nới.
3. **Thiếu kích thước bị gắn nhãn "chưa hỗ trợ".** Đề đủ quan hệ nhưng thiếu số đo (N01, A3 dev) có bản ghi làm rõ `MISSING_DATA` ở `route_d`,
   nhưng `classify_refusal` gắn `failure_category=capability_gap` (vì kiểm tra xác định "UNPROVED_DUE_TO_CAPABILITY_GAP") và người học
   thấy toast "Axo chưa hỗ trợ phép dựng này"; câu hỏi làm rõ "nói rõ các số đo cần thiết" không tới UI.
4. **Đề không dấu bị gắn "thuộc môn học khác".** V18, C24 (không dấu) bị cổng miền trả `out_of_scope` với lời "Bài này thuộc môn học khác".
   Ma trận /9 ghi hỗ trợ không dấu (VN11) — trên đường sản phẩm live điều đó không đúng.
5. **Điểm bố trí `O` gắn nhóm `given`.** Chóp đều/tứ diện đều có điểm `O` (tâm đáy, chân đường cao — đúng toán học, oracle xác nhận) nằm trong
   nhóm hiển thị `given` dù đề không nêu `O`.
