# Tương thích Scene3D, provenance và hợp đồng

Kết luận: **không đổi schema hay contract**. Không thêm trường mới; chỉ đổi giá trị của các trường tên đã có, và chỉ
trong cảnh của tuyến D (Adapter /4). Hệ quả cho người đọc dữ liệu:

## 1. Trường nào đổi, ai đọc

| trường | vật | ai đọc | trước → sau |
|---|---|---|---|
| `notation` | mặt cắt `mp_td_*` | canvas (`scene3d-presentation.ts::kyHieu`) | `(MHH1)` → `(α)` |
| `reference` | mặt cắt; thiết diện có đỉnh không tên; đại lượng trên nó | inspector (`Scene3DExplorer.tsx::ten`, dòng "Mặt phẳng cắt", "Thuộc") | tên ghép → tên nguồn / mô tả |
| `role` | mặt cắt; vật nhắc tới mặt toán hạng | inspector (dòng vai) | "qua M, H, H1" → quan hệ nguồn, mặt tham chiếu đúng chữ của đề |
| *(không đổi)* `explanation` event dựng mặt; `envelope.config.frames[].narration` | event CREATE của mặt; khung narration | không render trên đường Scene3D khi có `learner_text` | vẫn "qua ba điểm M, H, H1" (review R1, F5): khai |
| `label`/`display_label` | thiết diện lăng trụ; đại lượng dựng trên vật đổi tên | tiêu đề inspector, cây thành phần, thanh bước | "HMH1"/"Đoạn của thiết diện" → mô tả đúng loại |
| `formula.text` | đại lượng trên vật đổi tên | readout operator (đáp số ẩn với người học) | ký hiệu cũ → mô tả |
| `learner_text`/`explanation`/`display_label` (event, bước) | chỉ chỗ nêu tên cũ | thanh bước | thay đúng ký hiệu cũ |

## 2. Không đổi (được assert)

id · type · xyz · polygon · depends · origin · render · `formula.value` · `value` · thứ tự event (object, action,
step_index) · `formation.steps[].visible_ids` · mọi khoá và độ dài danh sách · toàn bộ `route_d` (sections, vertex
provenance, closure certificate, answers, answer_exact). Assert ở `export_fixtures.py::name_diff` (ném lỗi khi một giá
trị không phải tên khác) và `test_presentation_fix_moves_no_geometry_provenance_answer_or_order` (22 cảnh).

## 3. Provenance

| loại đỉnh | trước | sau |
|---|---|---|
| `SOURCE_NAMED` (N, P, Q…) | notation có, nhãn đề | không đổi |
| `THROUGH_POINT_REUSE` (M) | notation có | không đổi |
| `STATED_UNNAMED` (I, I1 của lăng trụ) | notation `null`, role "Điểm dựng phụ"; **nhưng chu trình thiết diện "HMH1" gọi tên chúng qua H/H1** | notation `null`, role "Điểm dựng phụ", không còn tên nào lọt qua thiết diện hay đại lượng |
| `DERIVED_FRESH` (PARTIAL, PLANE-ONLY) | notation `null`, "Điểm dựng phụ" | không đổi; `formula.text` không còn `MII1` |

Consumer frontend `hybrid-preview-adapter.ts::kiemSections` so `notation` **của điểm** (`type === "point3"`) và luật
`LUAT_NGUON`. Điểm không đổi ⇒ cảnh mới qua consumer. Đã kiểm: browser acceptance 94/94 trên cảnh mới.

## 4. Đề xuất contract cho phần còn lại (Owner quyết)

Vấn đề: thiết diện lăng trụ có hai điểm ngữ nghĩa ở mỗi đỉnh 1 và 3 (H phụ dựng mặt, I giao điểm). `_banDoDiem` cố ý
bỏ tên khi hai điểm trùng toạ độ, nên inspector hiện "Đỉnh 1 / Đỉnh 3".

**Đính chính (review F4):** bản nháp trước nói phần này *bắt buộc* đổi contract. Sai. Scene3D đã có đủ dữ liệu:
`section.endpoint_entities` gắn mỗi đỉnh với cạnh khối (`…edge:B-B_prime`), và I/I1 đã mang nhãn mô tả. Đây là đọc dữ liệu
backend đã quyết, không phải che dữ liệu sai. Ràng buộc thật là `sectionDetails` dùng chung với tuyến mặc định.

| phương án | thay đổi | rủi ro |
|---|---|---|
| **C0 (đề xuất)** `sectionDetails`: khi nhiều điểm trùng một đỉnh, chọn điểm nằm trên cạnh khối mà `endpoint_entities` của đỉnh đó chỉ ra | chỉ frontend (`scene3d-subentities.ts`), không đổi schema | đổi mã frontend dùng chung ⇒ candidate mới (`frontend/src` là product), test frontend mới, browser + T3; phải chứng minh không đổi tuyến mặc định |
| C1 thêm `section.vertex_point_ids` song song `polygon` | schema Scene3D, backend + frontend | đổi bề mặt Scene3D ⇒ export schema, schema sync; tuyến mặc định cũng phát trường (quyết bump `CACHE_VERSION`) |
| C2 ẩn H/H1 khi trùng giao điểm đã khai | backend + một luật frontend | điểm dựng phụ biến mất trong khi bước "Qua M dựng điểm H…" vẫn còn |
| C3 giữ nguyên | không | inspector "Đỉnh 1 / Đỉnh 3": trung thực nhưng kém thông tin |
