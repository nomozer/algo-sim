# Mở rộng hình học trên kiến trúc mới — triển khai và oracle

Oracle khoá trước khi sửa mã: `backend/tests/geometry/fixtures/geometry_expansion_cases.json` (`f47c56bb`), mỗi ca có
lời giải sách viết tay (`oracle`) độc lập với engine. Kết quả: 8/8 (`offline/geometry_expansion_cases/results.json`).

## 1. Chọn phạm vi — vì sao những thứ này

Trong sáu nhu cầu báo cáo trước nêu, chọn theo **phụ thuộc thực tế**:

1. **Độ dài ký hiệu a** — chặn nhiều đề Việt Nam nhất và *cắt ngang* mọi hàm: không có nó, mọi hàm khác chỉ phục vụ đề
   có số. Không đòi đổi kernel.
2. **Mặt bên ⊥ đáy** — dạng đề thi rất hay gặp, là một CẤU TRÚC dựng mới (đỉnh trong mặt phẳng qua một cạnh đáy, vuông
   góc đáy), ghép được với a và với các câu hỏi khoảng cách/góc.
3. **Hình chiếu vuông góc của một điểm lên mặt phẳng** — làm cùng phần độ bền diễn đạt (hàm `orthogonal_projection`) +
   **trọng tâm** để có chân dựng được.
4. **Góc giữa hai mặt phẳng**, **khoảng cách hai đường thẳng (chéo nhau)** — kernel đã tính được
   (`angle_cos_sq` mặt×mặt, `distance_sq_skew_lines`); chỉ thiếu hàm hỏi.

Hoãn: **đáy hình thoi / hình thang** (cần hàm dữ kiện góc và độ dài đường chéo; nên làm sau khi có số liệu đề thật).

## 2. Từng tính năng

| tính năng | hợp đồng | tiền điều kiện | kiểm toán học | ca dương / âm |
|---|---|---|---|---|
| độ dài ký hiệu | `ExactNumber`: `a`, `2a`, `a√3`, `a√3/2`, `3a/2` | MỌI độ dài đề cho cùng theo a (đồng bậc 1); trộn số ⇒ `NON_HOMOGENEOUS_LENGTHS` | hình đồng dạng khi a đổi ⇒ dựng ở a = 1 là đúng cho mọi a; đáp số = hệ số · a^bậc (V: 3, S: 2, độ dài/khoảng cách: 1, cos²: 0) | X01 a³√2/3, X02, X04 / X06 |
| mặt bên ⊥ đáy | `face_perpendicular_base(face[S,A,B], base)` | đúng một đỉnh ngoài đáy; A, B trên đáy; biết SA², SB² (đề, `equal_length`, tam giác đều…) | chân F = A + t(B − A), t = (SA² − SB² + AB²)/2AB², h² = SA² − t²AB² > 0; kiểm lại mặt ⊥ mặt bằng n₁ᵀG⁻¹n₂ = 0 | X02 (t = 1/2), X03 (t = 0) / X07 thiếu, X08 mâu thuẫn |
| hình chiếu + trọng tâm | `orthogonal_projection`, `centroid` (tam giác) | ảnh ≠ điểm; ảnh trên mặt; trọng tâm của 3 điểm đã dựng | trọng tâm dựng bằng IR có sẵn: `divide_segment(A, trung điểm BC, 2/3)` — kernel tính | X05 4√11/3 / N04 (paraphrase) |
| góc hai mặt | `ask_angle_plane_plane` | hai mặt dựng được (3 điểm) | `angle_cos_sq` của kernel dưới metric | X02 cos² = 4/7 |
| khoảng cách hai đường | `ask_distance_lines` | — | `distance` đường×đường của kernel (chéo nhau ⇒ `distance_sq_skew_lines`) | X04 a√3/2 |

**Độ dài ký hiệu không thành dữ kiện:** trace có bước `choose_unit` (`LAYOUT_DERIVED`, ghi "đơn vị, không phải dữ kiện"),
Scene3D có `length_unit = {symbol: "a", is_given: false}`, chương trình IR không có `GIVEN` nào (test khoá).

**Chân đường cao dẫn xuất, không giả định:** X02 ra trung điểm AB (vì SA = SB), X03 ra chính A (tam giác 3-4-5 vuông tại
A). Đột biến "chân luôn tại trung điểm" bị bắt.

## 3. Oracle độc lập (trích `oracle` của fixture)

- X01: V = ⅓·a²·a√2 = a³√2/3; SC² = 2a² + 2a² = 4a².
- X02: SH = a√3/2; V = a³√3/6; AB ∥ (SCD) ⇒ d(A,(SCD)) = d(H,(SCD)) = SH·HM/SM = a√21/7; cos²(SCD,ABCD) = HM²/SM² = 4/7.
- X03: SAB vuông tại A ⇒ h = 3, V = 16; SD² = 25.
- X04: AA' ⊥ đáy, BC ⊂ đáy ⇒ đoạn vuông góc chung = đường cao của tam giác đều = a√3/2.
- X05: GA² = 16/3, h² = 11/3, V = 4√11/3.

Test đọc Scene3D + `chart_metric` để so độ dài² (không đọc toạ độ nội bộ engine); renderer `veKhongGian` OK trên 5 cảnh
mở rộng (`diagnostics/renderer_metric_check.log`).

## 4. Tái sử dụng và trùng lặp

- **Tái sử dụng:** kernel (`metric`, `measure` — khoảng cách đường chéo nhau, góc mặt×mặt), IR (`midpoint`,
  `divide_segment`, `construct_plane/line`), interpreter, Scene3D; engine dùng 8/12 bộ tạo câu lệnh của
  `semantic_program/ir_builders.py` (dời nguyên văn từ compiler, compiler re-export).
- **Trùng lặp với compiler họ-bài** (`geometry_compiler/compiler.py`, 9 họ thể tích, opt-in, không nối sản phẩm): chồng
  lấn về PHẠM VI ở chóp/lăng trụ đáy tam giác vuông, chữ nhật, hộp, lập phương — hai cơ chế khác nhau (compiler: eligibility
  theo họ, toạ độ Euclid; engine: lời gọi có kiểu, khung affine + Gram). Engine CHƯA phủ: lăng trụ xiên (compiler có họ
  G04), đáy đa giác theo chuỗi góc vuông k > 4. Không thêm code vào compiler; quyết định có gộp/ngừng compiler là việc sau
  (ADR: không mở rộng tiếp compiler).
