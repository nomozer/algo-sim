# general-polygon-base — kế hoạch và tiền đăng ký (G05 chóp/lăng trụ đáy đa giác)

Việc: G05 trên kiến trúc sẵn có (ROADMAP §0.2). Cloud, nhánh `feat/general-polygon-base` từ `origin/main` = `d5287ff7`
(khớp, cây sạch). `LLM_ONLY` mặc định không đổi; compiler opt-in; 0 lượt gọi model; frontend không đổi.

## 1. Kiểm kê (mã tại `d5287ff7`, probe offline 0 lượt gọi)

| Câu hỏi | Trả lời từ mã | Loại |
|---|---|---|
| Kernel dựng đa giác nào | `construct_polygon` mọi n ≥ 3 (đa giác phẳng, toạ độ ℚ hoặc căn), diện tích `area_polygon`, thể tích tổng có dấu trên mặt biên (lồi và lõm có biên kín) | (1) có, dùng được |
| `construct_prism` / `construct_pyramid` (primitive compiler) | mặt dựng theo n, không cố định 3/4 | (1) có; compiler chỉ gọi cho đáy tam giác vuông / chữ nhật / vuông |
| Hợp đồng biểu diễn đa giác | `base_cycle` mọi n; `base_shape ∈ {rectangle, square}`; quan hệ `perpendicular_lines` tại một đỉnh; độ dài cạnh; toạ độ (`point_coordinate`) | đủ cho đáy xác định bởi CHUỖI góc vuông + độ dài; không có "đều", "hình thang", góc theo độ |
| Đa giác cho bằng toạ độ (mọi n, lồi/lõm) | LLM_ONLY phục vụ qua C0 (probe: chóp S.ABCDE toạ độ, V = 8) | (5) đã phục vụ sản phẩm (chương trình kiểu mô hình); compiler KHÔNG đọc toạ độ (adapter đòi `segment_length`) |
| Hình thang vuông (chóp/lăng trụ đứng) | bộ đọc nguồn không đọc "hình thang vuông tại A và B" ⇒ LLM_ONLY từ chối `ASSUMPTION_INVARIANCE_UNPROVEN`; compiler coi đáy có góc vuông là HÌNH CHỮ NHẬT ⇒ từ chối NHẦM `INVALID_CONFLICT RECTANGLE_OPPOSITE_EDGES_UNEQUAL` | (3) thiếu + một lỗi compiler |
| Chóp đáy tam giác vuông, chân đường cao KHÔNG ở đỉnh vuông | T1 đòi góc vuông tại chân; compiler `BASE_RIGHT_ANGLE_VERTEX_MISMATCH` | (3) thiếu — cùng một phép dựng thiếu |
| Đa giác đều (lục giác, ngũ giác đều) | không đọc; toạ độ vô tỉ | ngoài miền (L03 + L06) |
| Đáy lõm | kernel đúng (khối lõm `foundation_only`); không bộ đọc/khuôn | ngoài phạm vi lượt này |

## 2. Phạm vi lượt này (đóng)

Đa giác đáy LỒI, n ≥ 3, xác định bởi một CHUỖI n − 2 đỉnh liên tiếp có góc vuông (giữa hai cạnh đáy kề) cùng độ dài
của n − 1 cạnh của chuỗi; cạnh còn lại khép đa giác. Gồm: tam giác vuông (góc vuông ở bất kỳ đỉnh), hình thang vuông
(hai góc vuông kề), đa giác n cạnh có n − 2 góc vuông liên tiếp. Khối: chóp có cạnh bên `SX ⊥ (đáy)` tại một đỉnh đáy X
bất kỳ; lăng trụ đứng (cạnh bên ⊥ đáy). Hỏi thể tích. Toạ độ ℚ³ (độ dài hữu tỉ).

Một phép dựng chung (hàm tổng quát theo n) phục vụ cả hai khối; họ đã có (tam giác vuông với chân ở đỉnh vuông,
chữ nhật/vuông) GIỮ NGUYÊN đường cũ.

Ngoài phạm vi (từ chối đúng): đa giác đều ngoài hình vuông; hình bình hành/thoi theo góc; đáy lõm; chuỗi thiếu cạnh;
góc theo độ; đa giác cho bằng toạ độ trên tuyến compiler (LLM_ONLY đã phục vụ — giữ nguyên).

## 3. Thay đổi dự kiến

1. Amendment §20: từ vựng `đáy (ABCD)? là hình thang vuông tại X và Y` ⇒ hai `line_perp_line` tại X, Y (giữa hai cạnh
   đáy kề của mỗi đỉnh); khuôn **T10** (chuỗi góc vuông) — thử CHỈ khi T1/T2/T3–T6 trả `TEMPLATE_NOT_MATCHED`.
2. `assumption_gate`: T10 (khung `_Khuon` sẵn có).
3. `geometry_compiler`: hàm bố cục chung `_bo_cuc_chuoi_vuong` + hai họ `polygon_base_pyramid_volume`,
   `polygon_base_right_prism_volume`; đỉnh chóp/đáy trên do kernel (`translate`), chiều cao = khoảng cách tới mặt đáy,
   thể tích do kernel. Chỉ thử khi họ cũ không nhận (không đổi ca đang phục vụ); đáy tứ giác `base_shape` trống với
   đúng hai góc vuông kề ⇒ dùng kết luận của họ mới (sửa lỗi từ chối nhầm).
4. Bề mặt mô hình KHÔNG đổi. `CACHE_VERSION` quyết bằng bằng chứng.

## 4. Tiêu chí (đăng ký trước)

`labels.json` (7 dương, 7 âm), hai tuyến mỗi hàng; `oracle.py` tính diện tích đáy bằng công thức tay (hình thang,
tam giác, đa giác tách hình) từ kích thước của đề — không import sản phẩm, không dùng shoelace của sản phẩm. Bất biến:
V − E + F = 2; đáy phẳng, lồi, góc vuông đúng chỗ; chóp: SX ⊥ đáy; lăng trụ: đáy trên = tịnh tiến theo pháp tuyến; chiều
cao đo = độ dài đề cho. Hồi quy §0.3 + G04 + toàn bộ pytest so với baseline sạch `d5287ff7` cùng máy.
