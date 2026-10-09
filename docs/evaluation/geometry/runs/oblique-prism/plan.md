# oblique-prism — kế hoạch và tiền đăng ký (G04 lăng trụ xiên)

Việc: mở rộng G04 trên kiến trúc sẵn có (handoff `runs/frontend-freeze/handoff.md` §4). Máy: Cloud. Nhánh
`feat/oblique-prism` rẽ từ `origin/main` = `ba995887`. Mặc định `LLM_ONLY` không đổi; 0 lượt gọi model.

## 1. Kiểm kê trước khi sửa (đọc mã tại `ba995887`, không dựa snapshot W13)

| Tầng | Có sẵn | Phân loại |
|---|---|---|
| Hợp đồng (L01–L02) | `PrismTopologySpec.lateral_structure ∈ {right, oblique}` (lược đồ analyze có enum); `GeometricRelation perpendicular_line_plane` biểu diễn được `A'B ⊥ (ABC)`; `SourceInvariant segment_length` cho `A'B`, `AA'` | có, đủ cho chân đường cao tại MỘT ĐỈNH đáy; không có quan hệ trung điểm/trọng tâm/góc ⇒ chân tại trung điểm, góc nghiêng KHÔNG biểu diễn được (thiếu hợp đồng) |
| Bộ đọc nguồn server (L03) | `shape_constraint`: `oblique_prism`, `prism`, `line_perp_plane(A',B,ABC)`, `right_triangle`, `base_rectangle/square` | có; `hình chiếu … là trung điểm H`, `tạo với đáy góc 60°` ngoài từ vựng |
| FactGraph (L05) | `AdaptedPrismTopology` chở `lateral_structure`; suy diễn `line⟂plane ⇒ line⟂line` | có, chưa được compiler dùng |
| Kernel (L06) | `translate`, `vector_from_points`, `construct_point`, `construct_plane`, `measure distance(point, plane)`, `volume` chính xác; `radical.sqrt_rational` | có — hàm có nhưng compiler chưa gọi |
| Primitive | `construct_prism(base, top, correspondence)` dựng mặt cho mọi n, không giả định đứng | có |
| Compiler (L08) | lăng trụ tam giác: BỎ QUA `lateral_structure` (đề xiên có `AA' ⊥ (ABC)` sẽ bị biên dịch thành lăng trụ đứng); hộp: `oblique` ⇒ mâu thuẫn | thiếu thật |
| Cổng chứng chỉ giả định (dùng chung LLM_ONLY + compiler) | T3/T6 chỉ cho lăng trụ ĐỨNG; lăng trụ không "đứng" ⇒ `TEMPLATE_NOT_MATCHED` ⇒ từ chối | thiếu thật: mọi lăng trụ xiên bị từ chối ở `assumption`, cả đúng lẫn sai |
| LLM_ONLY phục vụ được | KHÔNG dạng G04 nào có đáp số số (đo trên chương trình kiểu LLM: `ASSUMPTION_INVARIANCE_UNPROVEN`) | — |

## 2. Phạm vi (đóng)

Lăng trụ (tam giác đáy vuông; tứ giác đáy chữ nhật/vuông) mà đề cho một quan hệ `T F ⊥ (đáy)` với T là đỉnh đáy
trên, F là đỉnh đáy dưới KHÔNG tương ứng với T, và chiều cao hữu tỉ: cho trực tiếp `TF`, hoặc suy từ một cạnh bên
`l` (h² = l² − |B₀F|², B₀ tương ứng với T) khi h² là bình phương hữu tỉ. Hỏi thể tích.

Ngoài phạm vi (từ chối đúng, không xấp xỉ): góc nghiêng theo độ; chân là trung điểm/trọng tâm/tâm; chiều cao vô tỉ;
đáy bình hành/tam giác thường; nhiều câu hỏi ngoài thể tích (compiler).

## 3. Thay đổi dự kiến

1. `ASSUMPTION_CERTIFICATE_AMENDMENT.md` §19 — khuôn T9 (đăng ký trước mã).
2. `assumption_gate._khuon_lang_tru` — T9 (cùng khung `_Khuon`, không engine mới).
3. `geometry_compiler` — họ `oblique_prism_volume`: đáy bố cục ℚ³, đỉnh neo T trên pháp tuyến tại F, các đỉnh
   đáy trên = `translate(Bᵢ, vector_from_points(B₀, T))` (kernel tính), chiều cao = `distance(T, mặt đáy)` (kernel).
4. Bề mặt mô hình KHÔNG đổi (prompt, thẻ văn phạm, hai lược đồ, băm `capability`). `CACHE_VERSION` quyết bằng
   bằng chứng (dự kiến không bump: chỉ chiều refused → served, lời từ chối không cache).

## 4. Tiêu chí (đăng ký trước khi chạy sản phẩm trên nhãn)

- `labels.json`: 6 dương (biến thể: đáy tam giác/chữ nhật/vuông, chân ở đỉnh khác nhau, đổi tên đỉnh, phân số,
  chiều cao trực tiếp/suy từ cạnh bên, có/không chữ "xiên") + 10 âm. Mỗi hàng chạy HAI tuyến:
  compiler (`GEOMETRY_COMPILER_MODE=DETERMINISTIC_FIRST`, 0 lượt gọi model) và LLM_ONLY với chương trình kiểu mô hình
  viết tay (`chart`) qua `verify_and_compile` — đây là năng lực HỆ, không phải bằng chứng mô hình sinh được.
- Giá trị phục vụ = `oracle.py` (từ kích thước của ĐỀ, không import sản phẩm). Không sửa nhãn/oracle cho test xanh;
  sai nhãn ghi ở `label_corrections.json`.
- Bất biến: V − E + F = 2; đáy trên = tịnh tiến của đáy dưới; hai đáy song song; mặt bên phẳng; chiều cao đo bằng
  khoảng cách tới mặt phẳng đáy; điểm bố cục `LAYOUT_DERIVED`, độ dài đề cho `GIVEN`.
- Hồi quy §0.3 của ROADMAP: sáu họ compiler, corpus gold, demo, bề mặt sập, toàn bộ pytest so baseline sạch tại
  `ba995887` (worktree tách rời). T3 trình duyệt: không chạy được trên Cloud nếu thiếu môi trường — ghi rõ.

## 5. Ghi chú trung thực

Bản nháp compiler được viết và chạy trên MỘT probe (đề OP01) TRƯỚC khi nhãn được ghi — probe dừng ở cổng giả định
(chưa phục vụ giá trị nào). Nhãn và oracle ghi sau probe ấy, trước khi T9 tồn tại và trước mọi lượt chạy sản phẩm
trên tập nhãn.
