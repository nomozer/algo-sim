# PLAN — regular-square-pyramid-w02

Việc `regular-square-pyramid`, wave W2. Brief: `REGULAR_SQUARE_PYRAMID_PEDAGOGICAL_CLOSURE`.
Thực thi: `CLOUD_IMPLEMENTATION_THEN_LOCAL_ACCEPTANCE` — phiên cloud triển khai, máy local nghiệm thu.

Tiếp nhận:
- `SOURCE_W1_HEAD = e821b9b5330480b791284548c3e49d683955682e` = `origin/feat/regular-square-pyramid`.
- `main` = `38d4158826cbbffd013d971a9484b9f0fd2a6130`.
- Phiên cloud khởi tạo sẵn trên nhánh `feat/regular-square-pyramid` tại W1 head; không fast-forward, không đổi `main`.

Ràng buộc: `LLM_ONLY`; 0 lượt gọi Gemini; không PR, không merge, không push `main`; không sửa artifact W1;
stage theo danh sách; không đụng `frontend/public/favicon.svg`.

## 0. Tái hiện (trước mọi sửa)

Trên fixture W1 (`runs/regular-square-pyramid-w01/inputs/fixtures/`), không gọi model:

| # | lỗi | sự thật |
|---|---|---|
| A1 | chóp tam giác: nhãn `AB = 3`, `AC = 4`, `SA = 5` hiện ở bước 0 | `annotationsAt` chỉ đòi hai ĐIỂM đầu mút có mặt; đoạn mang số đo (`day_ABC`, `chieu_cao_SA`) dựng ở bước 1–2 |
| A2 | lăng trụ tam giác: nhãn `AD = 5` hiện từ bước 0 | `canh_ben_A_D` dựng ở bước 3 |
| A0 | đối chứng | nhãn diện tích/thể tích (chủ thể là vật, có mặt mới hiện) đúng; bước 0 của chóp đều không có nhãn (dữ kiện không tên đoạn) |
| B | panel «Các bước dựng» chiếm cột lưới `.co-cac-buoc` ≥ 1100 px — mở/đóng đổi kích thước khung | `scene3d-playback.tsx` + `global.css` |
| C | chóp đều không có đoạn SO; chiều cao hiện là `d(S, (ABC))` + nhân chứng nét đứt | `formation._chan_ung_vien` chỉ biết quan hệ ⊥ của hợp đồng và `project_onto` |
| D | `mp_day` (mặt phẳng chỉ để đo) và AC, BD vẽ suốt cảnh trung tính | không có lớp "phụ trợ" trong trình bày |
| E | chọn chiều cao của công thức bằng **giá trị bằng nhau** (`98e2b8f7`) | đầu dò: lăng trụ đứng, chương trình khai `DF_length := AC_length` (cạnh đáy trên, = 4) và đo d(D, (ABC)) = 4 ⇒ công thức **`V = S(ABC) × DF = 24`** — sai vai trò |
| F | không có lưới nền | — |

## 1. Thứ tự

1. PLAN (file này).
2. **A** — test đỏ trên fixture thật → luật "đối tượng mang số đo đã dựng" trong `annotationsAt` (theo danh tính:
   `endpoint_ids` của đoạn, cạnh của đa giác `vertex_ids`, `edge_ownership` của khối); móc trình duyệt phân biệt
   nhãn chưa hợp lệ với nhãn hợp lệ nhưng thiếu chỗ.
3. **C/E** (TDD backend) — formation: nguồn chân đường cao thứ ba = tâm đáy của chóp tứ giác đều (ràng buộc có
   kiểu từ `shape_constraint`, tâm dựng bằng giao hai đường chéo hoặc trung điểm đường chéo) ⇒ đoạn `SO` vai
   `CONSTRUCT_HEIGHT`; `quantity_annotations`: nhân chứng trùng một đoạn đã dựng thì nhãn bám đoạn ấy; chiều cao
   của công thức chọn bằng **kiểm vuông góc chính xác** (kernel) trên đoạn mang số đo, giá trị chỉ kiểm nhất quán.
4. **D** — đường/mặt vai `CONSTRUCT_AUXILIARY_GEOMETRY` không phải dữ kiện/đích: mặt phẳng phụ ẩn mặc định, có công
   tắc; nhóm bước con "Dựng tâm đáy" trong danh sách bước, giữ thứ tự và delta.
5. **B** — panel nổi kéo được (desktop), bottom sheet (mobile); không đổi kích thước khung.
6. **F** — công tắc lưới, mặc định tắt; việc nhỏ: nhãn InputFact có gạch dưới, `aria-controls`.
7. Bộ đo trình duyệt (kéo panel thật, nhãn theo bước, SO, phụ trợ, lưới, mobile), node harness, ảnh mới.
8. Cache theo envelope thật; refreeze candidate; T3 + cổng danh tính trong worktree tách rời.
9. Tài liệu sống, REPORT, HANDOFF; commit + push nhánh làm việc.
