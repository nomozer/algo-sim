# PILOT_SELECTION_RATIONALE — vì sao chọn `logic.boolean_dag`

## 1. Hai cổng lọc, áp theo thứ tự

**Cổng 1 — chương trình.** Chỉ xét target nhãn **CỐT LÕI** (mọi học sinh THPT đều
học). Loại ngay 6 target ĐỊNH HƯỚNG, 2 target CHUYÊN ĐỀ, 1 CÔNG CỤ. Còn **13**.

**Cổng 2 — có khuyết điểm ĐO ĐƯỢC, không phải cảm nhận.** Trong 13 target còn lại,
chỉ giữ những cái có ít nhất một số đo xấu trong [UI_COMPLEXITY_MATRIX.md](UI_COMPLEXITY_MATRIX.md)
**và** một lỗi ngữ nghĩa cụ thể quan sát được trên ảnh chụp.

## 2. Bốn ứng viên cuối và lý do loại ba

| Ứng viên | Số đo | Vì sao **không** chọn |
|---|---|---|
| `binary.character_encoding` | stage 26 % — thấp nhất | `stage_share_of_card` **không hợp lệ** cho family này (`svg_in_stage=false`, sân khấu là **bảng**). Tôi đã tự đánh dấu chỉ số này vô hiệu ở mục 2 của UI_COMPLEXITY_MATRIX, nên không được quay lại dùng nó để chọn pilot. Không có bằng chứng thay thế ⇒ loại. |
| `network.packet_routing` | stage 28 % | Là target **3D `architectural_poc`**. Sửa trực quan ở đây đụng vào ranh giới 2D/3D và bất biến #16 — vượt quá quy mô "pilot nhỏ". |
| `algorithm.bounded_control_flow` | stage 40 %, **đã có chú giải** | Vừa được sửa ở đợt trước (trục vòng lặp + chặng). Sửa tiếp là gia cố cái đã tốt, không phải vá chỗ thủng. |
| **`logic.boolean_dag`** | **stage 32 %**, **không chú giải**, **sơ đồ 11 % < bảng 24 %** | **Chọn.** Lý do đầy đủ ở mục 3. |

## 3. Bằng chứng cho lựa chọn

**(a) Đúng nhóm học sinh rộng nhất.** Cổng logic và bảng chân lý nằm ở **Tin học 11,
Chủ đề A, phần chung cho cả hai định hướng** (KNTT Bài 4 / Cánh diều Bài 1). Đây là
nội dung **mọi** học sinh THPT đều học — rộng hơn hẳn BFS/queue (chỉ chuyên đề 12 KHMT).

**(b) Cơ chế chính NHỎ HƠN bảng tra cứu — đo được, không phải cảm nhận.**
Đo bằng cùng một harness trên mã trước pilot (worktree tại HEAD `722acea`):

| Viewport | sơ đồ mạch (svg) | bảng chân lý | Nhận xét |
|---|---:|---:|---|
| desktop 1440×1000 | **11 %** | **24 %** | bảng **to gấp 2,2 lần** cơ chế |
| laptop 1024×768 | 10 % | 25 % | gấp 2,5 lần |
| narrow 768×900 | 13 % | 24 % | gấp 1,8 lần |

Điều này vi phạm trực tiếp **NT-1** rút từ benchmark: không hệ tham khảo nào để
bảng tra lớn hơn cơ chế chính. Học sinh mở trang ra thì thứ đập vào mắt là **bảng
số**, không phải **mạch điện**.

**(c) Quá tải màu — có ảnh chụp làm bằng.** Trước pilot, cổng đầu ra được đánh dấu
bằng **viền xanh lá**, trong khi xanh lá **đồng thời** là "tín hiệu = 1" trên dây và
trên chữ số. Ảnh `screenshots/before/logic-boolean_dag-desktop-1-initial.png` bắt
được đúng ca gây hiểu nhầm: **cổng OR mang viền xanh lá trong khi giá trị của nó
vẫn là `?`**. Một học sinh đọc quy ước màu của chính hệ thống sẽ hiểu thành "cổng
này đang ra 1". Đo được: **1 thẻ `<rect>` mang `--accent-green`** ở mọi pha, mọi viewport.

**(d) Không có chú giải.** `legend = false`. Hệ thống có ngôn ngữ màu thống nhất
nhưng ở target này không nói ra — cộng với (c) thì quy ước màu vừa **không được
giải thích** vừa **bị dùng sai**.

**(e) Chi phí thấp, rủi ro thấp.** Sửa nằm trọn trong tầng renderer: không đụng
engine, state, timeline, schema, hay backend. Không thêm family/target/module.

## 4. Vì sao KHÔNG chọn BFS

Yêu cầu ghi rõ: *"Ưu tiên BFS chỉ khi audit chương trình xác nhận BFS hoặc queue có
vai trò phù hợp."*

Audit xác nhận BFS/DFS, hàng đợi và ngăn xếp **có** trong chương trình — nhưng ở
**chuyên đề học tập Tin học 12 định hướng Khoa học máy tính** (nguồn S8), tức nhóm
học sinh **hẹp nhất** trong ba nhóm. Điều kiện để được **ưu tiên** không đạt.

Thêm nữa, `network.graph_traversal` (65 %) và `tree.traversal` (67 %) đang là hai
target có **sân khấu lớn nhất** trong cả 22, **đã có chú giải**, và vừa nhận primitive
Frontier ở đợt trước. Đầu tư tiếp vào đây là dồn công sức vào chỗ đã tốt nhất, cho
nhóm học sinh hẹp nhất.
