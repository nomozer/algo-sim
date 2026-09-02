# PRESENTATION_UI_POLISH — hoàn thiện tầng trình bày của xưởng hình 3D

> **Phạm vi: TRÌNH BÀY.** Không đổi bài toán, biểu diễn trung gian, vết thực
> thi, toạ độ, nhân hình học, checker, truy nguồn dữ kiện, hay kết quả thực
> nghiệm. Backend không đổi một dòng.
>
> Lượt sửa: 2026-09-02. **0 lượt gọi mô hình.**

---

## Vì sao có lượt này

Ảnh chụp thật của tập trình diễn cho thấy tầng trình bày chưa tương xứng với
engine bên dưới. Tám vấn đề đo được, không phải cảm giác:

| # | vấn đề | đo được |
|:-:|---|---|
| 1 | khung 3D bó hẹp giữa màn hình rộng | canvas **606 px** trên 1585 px khả dụng |
| 2 | ô soi là lớp phủ đè lên khối | `position: absolute`, che phần lớn hình chóp |
| 3 | nhãn dài chồng nhau, chạy ra ngoài mép | *"Hình chiếu vuông góc H của I lên mặt phẳng (SBC)"* in cạnh một chấm |
| 4 | vectơ hiện thành một chấm đỏ khó hiểu | `vector_AA_prime` vẽ tại (1,1,3), nơi không có điểm nào của hình |
| 5 | mặt phẳng phụ quá lớn, nuốt cảnh | `PlaneGeometry` cỡ cố định, không theo hình |
| 6 | camera không tận dụng khung | `position.set(6, 5, 8)` — hằng số cho mọi bài |
| 7 | hai thanh cùng ghi "Bước" | trên hiện `Bước 7/7`, dưới hiện `Bước 1/7` |
| 8 | nhãn từ chối nói sai loại thất bại | `geometry_generation_failed` → *"NGOÀI DANH MỤC MÔ PHỎNG"* |

---

## Đã sửa gì

### 1 · Xưởng 3D lấy bề rộng màn hình

Lưới vỏ được đặt cho các cơ chế 2D: cột nội dung `auto` với sàn bằng chính sách
khay, và `.panel-center` căn giữa con của nó. Một xưởng 3D **không có bề rộng
nội tại**, nên nó co về bề rộng tối thiểu của nội dung.

Sửa: `App.tsx` gắn lớp `la-canh-3d` khi cảnh là 3D — dùng lại đúng vị ngữ
`canvasFirst` đã có, dẫn từ `scene3d` **có thật** chứ không từ một chế độ được
khai, nên vỏ và ruột không thể lệch nhau. CSS cho cột nuốt phần còn lại và cho
xưởng nhận trọn cột, có trần 1320 px.

**606 px → 1320 px** khi ô soi đóng · **952 px** khi ô soi mở.

### 2 · Ô soi thành cột bên cạnh, không còn đè lên hình

Ở bề rộng ≥ 1100 px, `.geo3d-san` thành lưới hai cột và `.geo3d-soi` chuyển từ
`position: absolute` sang `static`. Hết tuyệt đối thì hết đè — không phải né
bằng khoảng cách. Ở khung hẹp hơn, lớp phủ vẫn giữ nguyên như cũ.

Giữ nguyên mọi thông tin và mọi nút của ô soi: Loại · Phép dựng · Dựa trên ·
Chỉ xem phần này · Xem cấu tạo · Ẩn.

### 3 · Nhãn mặc định là ký hiệu, câu mô tả chuyển sang ô soi

Module mới `scene3d-presentation.ts`. Khung mặc định in ký hiệu hình học —
`A`, `M`, `H`, `B′` — đúng thứ học sinh đọc trên bảng. Câu mô tả đầy đủ vẫn ở ô
soi và cây thành phần: **không mất thông tin, chỉ đổi chỗ trình bày**.

Nhãn chồng nhau thì ẩn cái ưu tiên thấp hơn (đang chọn > dẫn xuất > gốc).
**Không xê dịch nhãn** — xê dịch làm nhãn rời khỏi vật nó gọi tên.

### 4 · Vectơ không còn bị vẽ như một điểm

Tầng sinh cảnh phát vectơ với `type: "point3"`, `render: "point_marker"`, còn
`xyz` là **thành phần vectơ** chứ không phải toạ độ một điểm. Vẽ nó lên khung là
đặt vào bài một vật không tồn tại.

Sửa theo hướng bảo thủ: **không vẽ lên khung mặc định**, vẫn giữ trong cây và ô
soi. Không vẽ thành mũi tên, vì thêm một loại vẽ là đổi `RENDER_KINDS` — hợp
đồng khoá đồng bộ hai chiều với backend — còn dựng mũi tên từ `depends` là
renderer tự suy vị trí, đúng thứ ranh giới R0 cấm.

### 5 · Khung nhìn tính từ hộp bao

Module mới `scene3d-camera.ts`. Camera đưa hình về khoảng 68% chiều khung, lấy
ràng buộc lớn hơn giữa chiều dọc và chiều ngang. Trả `null` thay vì `NaN` khi
đầu vào hỏng, để nơi gọi giữ nguyên khung nhìn.

⚠️ **Không gọi khi đổi bước.** Chỉ ba dịp: nạp cảnh khác · người dùng bấm *Xem
lại toàn hình* · tách/ráp khối. Đặt lại khung nhìn ở mỗi bước sẽ biến việc tua
bước thành việc đổi góc máy, và hai hình so sánh bước 5 với bước 12 chỉ có nghĩa
khi camera đứng yên.

*Xem lại toàn hình* nay đặt lại **cả** tập vật đang hiện **và** khung nhìn.

### 6 · Một khay điều khiển trên một màn hình

`SimulationControls` là khay của đường 2D, lái bước trong store. Xưởng 3D có bộ
tua riêng, lái `InteractionState`. Hai trạng thái **thật sự khác nhau** — nên
hiện cả hai là bày ra hai thanh cùng ghi "Bước" mà kéo thanh dưới thì hình không
đổi. Ẩn khay 2D khi cảnh là 3D; đường 2D giữ nguyên khay của nó.

### 7 · Nhãn từ chối nói đúng loại thất bại

`geometry_generation_failed` nay mang nhãn **"CHƯA DỰNG ĐƯỢC MÔ PHỎNG"** thay vì
nhãn mặc định *"NGOÀI DANH MỤC MÔ PHỎNG"* — vốn mâu thuẫn với chính thân thông
điệp ngay dưới nó, nơi hệ nói rằng nó **đã** nhận ra đây là bài hình học và
**đã** thử dựng.

Chỉ đổi **nhãn hiển thị**. `failure_category`, `error_code`, phân loại thất bại
và hành vi fail-closed giữ nguyên.

---

## Điều KHÔNG sửa, và vì sao

| bỏ qua | lý do |
|---|---|
| Kích thước hiển thị mặt phẳng (§9 của chỉ thị) | `PLANE_DISPLAY_SIZE` sống ở `scene3d-model.ts`, cùng file với `RENDER_KINDS` đang khoá đồng bộ hai chiều với backend. Sau khi khung nhìn đã tính từ hộp bao, mặt phẳng không còn nuốt cảnh trong các ca đã kiểm — nên đây là sửa **chưa cần**, và chạm vào file khoá đồng bộ là rủi ro không tương xứng |
| Vẽ vectơ thành mũi tên | đòi thêm một loại vẽ vào hợp đồng khoá đồng bộ với backend |
| Thứ bậc độ mờ (§10) | các ca đã kiểm không cho thấy mặt phụ lấn át sau khi khung nhìn được sửa; đổi màu/độ mờ khi màu đang mang ngữ nghĩa là rủi ro không cần thiết |

---

## Truy vết

**CHANGED_FILES**

| tệp | loại |
|---|---|
| `frontend/src/simulations/domains/geometry/scene3d-presentation.ts` | **mới** — quy tắc trình bày thuần |
| `frontend/src/simulations/domains/geometry/scene3d-camera.ts` | **mới** — khung nhìn từ hộp bao |
| `frontend/src/simulations/domains/geometry/scene3d-presentation.test.ts` | **mới** — 12 ca hồi quy |
| `frontend/src/simulations/domains/geometry/scene3d-view.tsx` | nhãn ngắn · lọc vectơ · lọc nhãn chồng · gọi khung nhìn |
| `frontend/src/simulations/domains/geometry/scene3d-playback.tsx` | chuyển tiếp `fitToken` |
| `frontend/src/simulations/domains/geometry/Scene3DExplorer.tsx` | nút *Xem lại toàn hình* đặt lại khung nhìn |
| `frontend/src/simulations/domains/geometry/scene3d.test.tsx` | danh sách nhập hợp lệ + 2 test độ thuần |
| `frontend/src/components/SimulationWorkspace.tsx` | nhãn từ chối |
| `frontend/src/components/ux-shell.test.tsx` | 4 ca hồi quy vỏ |
| `frontend/src/App.tsx` | lớp `la-canh-3d` · ẩn khay 2D khi cảnh 3D |
| `frontend/src/styles/global.css` | bố cục xưởng 3D |
| `docs/CODE_INDEX.md` | entry cho hai module mới |

**VISUAL_BEHAVIOR_CHANGED** — bề rộng xưởng, vị trí ô soi, nội dung nhãn, tập
vật được vẽ trên khung mặc định, khung nhìn ban đầu, số khay điều khiển, nhãn
từ chối.

| | |
|---|---|
| SEMANTIC_BEHAVIOR_CHANGED | **NO** |
| BACKEND_CHANGED | **NO** |
| GEOMETRY_RESULT_CHANGED | **NO** |
| TRACE_SEMANTICS_CHANGED | **NO** |
| HISTORICAL_SCORES_CHANGED | **NO** |
| APPLICATION_LLM_CALLS | **0** |
