# Inspector C0: đỉnh thiết diện trùng toạ độ, kiểm provenance

## 1. Luật (`frontend/src/simulations/domains/geometry/scene3d-subentities.ts::_diemCuaDinh`)

Dùng cho `sectionDetails` (dòng "Các đỉnh" của inspector) và sub-entity đỉnh thiết diện (`deriveSectionSubEntities`).

1. Toạ độ đỉnh có **đúng một** điểm ngữ nghĩa ⇒ điểm ấy (hành vi cũ, không đổi).
2. Không có điểm ⇒ `null` (cũ).
3. Có **≥ 2** điểm ⇒ chỉ nhận điểm P thoả cả ba điều kiện (đều là dữ liệu backend đã quyết):
   - `section.vertex_sources[k].solid_edge_vertex_indices` chỉ cạnh {U, V} của khối (qua `vertex_ids` của khối);
   - P có đúng hai phụ thuộc: một `line3` có `depends` **đúng bằng** {U, V}, một `plane3` **là** mặt cắt của thiết diện (cùng id, hoặc cùng tập điểm dựng);
   - P là ứng viên **duy nhất**.
   Không thoả ⇒ `null` ⇒ nhãn trung tính "Đỉnh k".

Không đọc thứ tự vật, tên/ký hiệu, `producer`; không chọn chỉ vì trùng toạ độ. Không đổi schema.

## 2. Lăng trụ `CORPUS-DEV10-prism-area`

| đỉnh | toạ độ | điểm ở đó | cạnh (`vertex_sources`) | điểm thoả luật | trước | sau |
|---|---|---|---|---|---|---|
| 1 | (1, 0, ½) | H (tịnh tiến M + AB), I | B–B′ | I = `intersect_line_plane(derived_I_line[B,B′], derived_I_plane[H,H1,M])` | Đỉnh 1 | Giao điểm của BB′ và (α) |
| 2 | (0, 0, ½) | M | (duy nhất) | — | M | M |
| 3 | (0, 1, ½) | H1, I1 | C–C′ | I1 | Đỉnh 3 | Giao điểm của CC′ và (α) |

H/H1 không thoả (phụ thuộc là điểm + vectơ, không phải đường cạnh + mặt cắt) và **vẫn ở** cảnh, DAG và canvas.
I/I1 vẫn `notation: null`, role "Điểm dựng phụ", không có `given`; `sectionCycleLabel` vẫn `null`;
`route_d` vẫn `STATED_UNNAMED`. Polygon, cạnh ("Cạnh 1–3"), mặt tô không đổi.
Sub-entity đỉnh: `depends` từ `[]` thành `["I"]`/`["I1"]`. Người dùng duy nhất là `withSubEntities` → chọn/tô sáng
đỉnh nay tô I. I tồn tại từ bước 12, thiết diện từ bước 16, nên không có phụ thuộc sớm (browser acceptance kiểm mọi khung).

## 3. Tầm ảnh hưởng (tuyến mặc định)

Quét mọi JSON có Scene3D trong `frontend/src` và `docs/evaluation` (178 cảnh của tôi; reviewer quét độc lập 399 lần
xuất hiện): đỉnh nhập nhằng duy nhất là hai đỉnh của lăng trụ này, lặp lại trong các bản export Adapter /4. Không có cảnh
LLM_ONLY đã lưu nào đổi. Cảnh LLM_ONLY trực tiếp chưa đo được. Nếu có, nó chỉ có thể đổi từ "Đỉnh k" sang một điểm mà
chính các phụ thuộc chứng minh là giao của cạnh đó; không bao giờ ngược lại, và không bao giờ sang một tên.

## 4. Test (`scene3d-section-vertex-identity.test.ts`, 7, nền đỏ 3)

- Tên vai trò cho lăng trụ (đỏ trước).
- Sub-entity cùng điểm, cạnh không đổi (đỏ trước).
- Không phụ thuộc thứ tự vật hay ký hiệu của H (đỏ trước).
- Trung tính khi đường của I không nằm trên cạnh đó.
- Trung tính khi có hai ứng viên thoả.
- `STATED_UNNAMED` không được nâng, chu trình vẫn `null`.
- Ở 22 cảnh served, mọi đỉnh không nhập nhằng giữ đúng tên theo toạ độ, và đúng 2 đỉnh đổi.

Tiêm lỗi: nhận ứng viên đầu tiên ⇒ đỏ ("hai ứng viên"); bỏ kiểm cạnh ⇒ đỏ ("không phải giao của cạnh đó").
