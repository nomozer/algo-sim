# Scene3D C0: báo cáo cuối

Authorization `GO_SCENE3D_AB_MAIN_AND_C0_FINALIZATION_LOCAL`. 0 lượt gọi model. Không push, không bật production.
**Trạng thái: `SCENE3D_C0_READY_FOR_OWNER_GO_MAIN`.** Nhánh `research/scene3d-section-inspector-c0` **chưa merge**.

## Thay đổi (so với `main` = `9978e512`)

| commit | nội dung |
|---|---|
| `0c5723f3` | **C0** frontend `scene3d-subentities.ts::_diemCuaDinh`: đỉnh thiết diện trùng toạ độ được gọi bằng điểm mà phụ thuộc chứng minh là giao của đúng cạnh khối với mặt cắt; không đủ ⇒ "Đỉnh k" ([`INSPECTOR_PROVENANCE_VALIDATION.md`](INSPECTOR_PROVENANCE_VALIDATION.md)) |
| `a5060bd4` | **R1** `function_route.py`: `explanation` dự phòng của mặt cắt nêu định nghĩa nguồn rồi phép dựng thật |
| `ff5b551f` | **F5** harness trình duyệt: không narration `config.frames` nào lên trang (kiểm chứng, không sửa builder dùng chung) |
| `c04094f1` | **kd** fail-closed bằng `_KhoiKhongKhai` bắt riêng → `SCENE_BUILD_FAILED`; hợp đồng đã cưỡng chế ở Source Gate (`AUXILIARY_RULE_MISMATCH`) |
| `048d58bd`, `4d3b8849` | review N2, P1: dấu phẩy trên `′` trong nhãn giao điểm và bước "Xét mặt phẳng …" đang hiển thị |
| `19e1fbcd`, `d268c222`, `ce2aa0f1` | ba lần freeze; hai lần đầu bị thay sau review |
| `c3916629`, `a62b6add`, `9fa40dcd` | ba lần export Adapter /4; dùng bản cuối `adapter4-export-reviewed` |

Product: `backend/app/ai/function_route.py` + `frontend/src/simulations/domains/geometry/scene3d-subentities.ts`.
Không đổi schema, contract, IR, kernel, planner, Source Gate, `simulation_state`/`display_names`.

## Kết quả

| kiểm | kết quả |
|---|---|
| candidate | freeze `ce2aa0f1`, product `4d3b8849`, measured `4acdac53…` (116 file), NO_BUMP 127 |
| **Full T3** tại `ce2aa0f1` | **`FULL_PRODUCT_GATE_PASS`**: pytest 11,683 / vitest 74 file 1,245 / build / demo 5/5 / crash 6/6; freeze MATCH sau T3 |
| browser | **94/94 PASS** + F5 mỗi khung; refusal **50/50 PASS** (cây sạch) ([`BROWSER_ACCEPTANCE_REPORT.md`](BROWSER_ACCEPTANCE_REPORT.md)) |
| export Adapter /4 | 47 case; 22 served chỉ đổi tên (135 trường so với lịch sử), `route_d` bằng nhau; 25 refusal không đổi |
| review độc lập | 3 vòng; cuối `PASS` ([`INDEPENDENT_REVIEW.md`](INDEPENDENT_REVIEW.md)) |
| nền đỏ / tiêm lỗi | C0 3 đỏ trước + 2 đột biến đỏ; R1 22 đỏ; kd 2 đỏ; N2, P1 đỏ trước |
| tầm ảnh hưởng LLM_ONLY | 0 cảnh đã lưu đổi (chỉ hai đỉnh lăng trụ nhập nhằng trong toàn kho); `/api/analyze` không nhập `function_route` |

## Giới hạn còn lại (khai, không chặn)

- Canvas lăng trụ vẫn hiện nhãn H, H1 tại hai đỉnh. Đó là điểm dựng phụ có thật; inspector nay nói đúng vai trò của đỉnh.
- Payload API của Hybrid vẫn mang narration `config.frames` có tên dựng nội bộ. Không render; sửa sẽ phải đổi contract config dùng chung.
- Hai dấu `'` ASCII có từ trước, ở trường không render (`explanation` dự phòng và `details.label` của khối lăng trụ).
- Cảnh LLM_ONLY trực tiếp (không lưu) chưa đo được. Nếu có cảnh như vậy, nó chỉ có thể đổi theo một chiều có chứng minh ("Đỉnh k" → giao điểm được phụ thuộc xác nhận).
