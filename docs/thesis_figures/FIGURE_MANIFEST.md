# FIGURE_MANIFEST — xuất xứ của từng hình

> Mỗi hình nêu **nó chứng minh điều gì** trước, rồi mới tới cách dựng. Hình nào
> không trả lời được câu ấy thì đã bị loại — xem §4.
>
> Lượt dựng: 2026-09-02, trên phiên bản hệ thống đã đóng băng. **0 lượt gọi mô
> hình**; ảnh chụp dựng từ các bản ghi thực nghiệm đã niêm phong, nạp qua đúng
> cửa mà người dùng đi qua (`loadEnvelope`).

---

## 1. Kiểm kê

| | số |
|---|:-:|
| Sơ đồ (SVG, kèm PNG kết xuất) | **5** |
| Ảnh chụp màn hình (PNG) | **4** |
| **Tổng** | **9** |

Sơ đồ giữ ở dạng **vector**; bản PNG chỉ để xem trước và để chèn vào công cụ
không đọc được SVG. Ảnh chụp ở **2× tỉ lệ thiết bị**, đủ nét khi in A4.

---

## 2. Sơ đồ

### Hình 3.1 — Kiến trúc tổng thể

| | |
|---|---|
| Tệp | `fig_3_1_architecture.svg` · `.png` (1800 × 2160) |
| Chứng minh | Ranh giới R0: đúng **hai** khối thuộc mô hình ngôn ngữ, và cả hai nằm **trước** khi tồn tại toạ độ nào. Đề ngoài miền bị từ chối với **0 lượt gọi** |
| Nguồn nội dung | `docs/THESIS_ARCHITECTURE.md §B`, `§C`; bản thảo §3.1, §3.2 |
| Cách dựng | SVG viết tay. Ba vùng phân biệt bằng màu và khung nét đứt; bốn tầng nhân hình học là khối con bên trong khối thực thi (gộp từ sơ đồ riêng — xem §4) |
| Chú thích | *Hình 3.1. Kiến trúc tổng thể của hệ thống. Hai khối tô màu cam thuộc mô hình ngôn ngữ; toàn bộ phần còn lại là tất định. Ranh giới R0 nằm ngay sau bước tổng hợp chương trình: sau điểm này không còn lượt gọi mô hình nào, nên mọi toạ độ và mọi phán quyết đúng/sai đều do các tầng tất định sinh ra.* |

### Hình 3.2 — Cùng một bài qua ba tầng biểu diễn

| | |
|---|---|
| Tệp | `fig_3_2_semantic_pipeline.svg` · `.png` (2240 × 1120) |
| Chứng minh | Toạ độ chỉ có ở các điểm **đề cho**; toạ độ của hai điểm **được dựng ra** không có mặt trong chương trình. Toán hạng hình học là **tên** |
| Ca dùng | Bài hình thoi — cùng ví dụ đã trình bày ở bản thảo §3.4.4 |
| Cách dựng | SVG viết tay; chương trình ở cột giữa là bản **rút gọn 4 câu lệnh** của chương trình thật, cột phải là **phác hoạ** cấu hình chứ không phải ảnh chụp |
| Chú thích | *Hình 3.2. Cùng một bài toán qua ba tầng biểu diễn. Toạ độ xuất hiện ở cột giữa chỉ cho các điểm mà đề cho, mỗi điểm kèm định danh dữ kiện nguồn; toạ độ của hai điểm được dựng ra không có mặt trong chương trình, vì nhân hình học tính chúng khi thực thi.* |

### Hình 3.3 — Dẫn xuất cảnh ba chiều từ vết thực thi

| | |
|---|---|
| Tệp | `fig_3_3_trace_scene3d.svg` · `.png` (2080 × 1240) |
| Chứng minh | Song ánh **khung k ⇔ bước k**, và việc **gộp bước để trình bày nằm ở tầng sau** nên không phá song ánh ấy |
| Nguồn nội dung | `docs/THESIS_ARCHITECTURE.md §G`; bản thảo §3.7 |
| Cách dựng | SVG viết tay; ba hàng xếp thẳng cột, nối bằng đường nét đứt để thấy tương ứng một–một |
| Chú thích | *Hình 3.3. Cảnh ba chiều được dẫn xuất từ vết thực thi. Khung hình thứ k suy ra hoàn toàn từ ảnh chụp bộ nhớ tại bước k, nên thao tác “tua tới bước k” có nghĩa xác định. Việc gộp bước cho mục đích trình bày nằm ở một tầng sau và không phá song ánh này.* |

### Hình 3.4 — Trình tự xử lý một yêu cầu

| | |
|---|---|
| Tệp | `fig_3_4_request_sequence.svg` · `.png` (2000 × 1600) |
| Chứng minh | Thứ tự bảy cổng, và **chi phí gọi mô hình của từng đường từ chối** — đặc biệt: đề ngoài miền tốn **0 lượt** |
| Nguồn nội dung | `docs/THESIS_ARCHITECTURE.md §I` (đã có bản nháp dạng mermaid); bản thảo §3.6, §3.9 |
| Cách dựng | SVG viết tay, dạng sơ đồ tuần tự năm làn |
| Chú thích | *Hình 3.4. Trình tự xử lý một yêu cầu. Đề không thuộc hình học không gian bị từ chối tại biên miền với không lượt gọi mô hình nào; các đường từ chối còn lại dừng sau bước tổng hợp và trước khi phát ra mô phỏng.* |

### Hình 4.1 — Quan hệ giữa bốn lượt thực nghiệm

| | |
|---|---|
| Tệp | `fig_4_1_experiment_trajectory.svg` · `.png` (2320 × 1320) |
| Chứng minh | Mỗi lượt đo cho một **khuôn hỏng lặp lại**; khuôn ấy chỉ đích danh một khiếm khuyết **giao diện**; sửa giao diện làm khuôn biến mất ở lượt sau |
| Nguồn nội dung | Bản thảo §4.3–§4.7, Bảng 4.7 |
| Cách dựng | SVG viết tay; ba hàng — lượt đo, khuôn hỏng, bản sửa — nối theo trục thời gian |
| Chú thích | *Hình 4.1. Quan hệ giữa bốn lượt thực nghiệm. Mỗi lượt không chỉ cho một điểm số mà còn cho một khuôn hỏng lặp lại; khuôn hỏng ấy chỉ ra một khiếm khuyết ở giao diện giữa mô hình và hệ thống, và việc sửa giao diện làm khuôn hỏng tương ứng không còn xuất hiện ở lượt kế tiếp.* |

---

## 3. Ảnh chụp màn hình

**Điều kiện chung.** Khung nhìn 1600 × 900 (16 : 9), tỉ lệ thiết bị 2×, trình
duyệt thật có WebGL, không thanh dấu trang, không phần mở rộng, không bảng gỡ
lỗi. Con trỏ chuột được đưa ra góc trước mỗi lần chụp để không để lại chú giải
nổi. **0 lỗi bảng điều khiển** trong toàn bộ lượt chụp.

### Hình 4.2 — Xuất xứ và phụ thuộc

| | |
|---|---|
| Tệp | `fig_4_2_provenance.png` (2424 × 2232) |
| Chứng minh | Mỗi vật trong cảnh mang **xuất xứ**: phép dựng nào tạo ra nó, và nó **dựa trên** cái gì. Nếu mô hình chỉ đoán toạ độ rồi khai ra, hai trường này sẽ trống |
| Ca | Chóp S.ABCD, giao điểm rồi hình chiếu (bản ghi `clean-baseline-v2`) |
| Trạng thái | Bước 8/8 · chế độ **Chi tiết** bật · đang chọn *Giao điểm I của hai đường chéo AC và BD* |
| Đọc được trong ảnh | `Loại: point3` · `Phép dựng: construct_point.midpoint` · `Dựa trên: A, C`, cùng dòng mô tả cho người học *“Trung điểm của A, C”* |
| Vùng cắt | phần tử `.geo3d` |
| Chú thích | *Hình 4.2. Giao diện xưởng hình ba chiều ở chế độ chi tiết. Ô soi hiển thị phép dựng đã tạo ra đối tượng đang chọn và danh sách đối tượng mà nó phụ thuộc; cấu trúc phụ thuộc này được dẫn xuất từ chương trình, chứ không phải một danh sách toạ độ được khai trực tiếp.* |

⚠️ **Hạn chế của ảnh, khai để không nói quá.** Ô soi là một lớp phủ và ở khung
nhìn này nó che phần lớn khối chóp. Đây là bố cục thật của sản phẩm ở bề rộng
ấy; không chỉnh giao diện để ảnh đẹp hơn.

### Hình 4.3 — Cùng một bài tại hai bước, giữ nguyên góc nhìn

| | |
|---|---|
| Tệp | `fig_4_3a_step5.png` · `fig_4_3b_step12.png` (mỗi tấm 2424 × 2232) |
| Chứng minh | Cảnh tại bước *k* là **kết quả của lượt chạy tới bước *k***, không phải một hoạt hình dựng sẵn |
| Ca | Chóp S.ABCD, thiết diện qua ba trung điểm (bản ghi `clean-baseline-v2`) |
| Trạng thái | (a) bước 5/12 — mới có các điểm và mặt phẳng cắt · (b) bước 12/12 — đủ khối, cạnh và thiết diện |
| Ràng buộc camera | **Camera mặc định, không xoay** giữa hai lần chụp, nên khác biệt duy nhất là bước |
| Vùng cắt | phần tử `.geo3d-canvas` |
| Ghép ảnh | đặt cạnh nhau, hai khung **cùng kích thước**, nhãn nhỏ (a) và (b); không thêm đoạn giải thích vào trong ảnh |
| Chú thích | *Hình 4.3. Cùng một bài tại bước 5 (a) và bước 12 (b), giữ nguyên góc nhìn. Các đối tượng xuất hiện đúng theo thứ tự chương trình dựng chúng; cảnh tại mỗi bước được dẫn xuất từ trạng thái bộ nhớ tại bước tương ứng.* |

### Hình 4.4 — Từ chối có địa chỉ

| | |
|---|---|
| Tệp | `fig_4_4_refusal.png` (3200 × 1800) |
| Chứng minh | Hệ **không đoán**: khi dữ kiện không truy được về đề, nó nêu lý do bằng tiếng Việt và **không dựng cảnh 3D nào** |
| Nguồn dữ liệu | Trạng thái từ chối dựng lại từ bản ghi thật của ca hỏng ở cổng truy nguồn (`name-contract-probe`, phân loại `FAIL_GROUNDING`). Thông điệp cho người học lấy **nguyên văn** từ mã nguồn sản phẩm; không câu chữ nào do người soạn viết ra |
| Đo được trong ảnh | số phần tử `canvas` = **0** · thân trang **không** chứa mã lỗi kỹ thuật nào |
| Vùng cắt | toàn trang |
| Chú thích | *Hình 4.4. Màn hình khi cổng truy nguồn dữ kiện từ chối một chương trình. Hệ thống nêu lý do bằng ngôn ngữ người học đọc được và không dựng cảnh ba chiều kèm theo — thà không trình bày gì còn hơn trình bày một kết quả chưa được kiểm chứng.* |

⚠️ **Một điểm không nhất quán của sản phẩm, khai ra thay vì giấu.** Nhãn nhỏ
phía trên thông điệp đọc là *“NGOÀI DANH MỤC MÔ PHỎNG”*, trong khi thân thông
điệp nói ngược lại — rằng hệ **đã nhận ra** đây là bài hình học và **đã thử
dựng**. Nguyên nhân: loại thất bại *“sinh chương trình hình học không thành”*
chưa có nhãn riêng nên rơi vào nhãn mặc định. Đây là khiếm khuyết giao diện có
thật ở phiên bản đã đóng băng; **không sửa** (mã đã đóng băng), và **chú thích
không dựa vào nhãn ấy**. Nếu cần, có thể cắt bỏ dòng nhãn khi đưa vào bản in —
việc cắt phải được ghi rõ ở chú thích.

### Hình 4.5 — Tách khối

| | |
|---|---|
| Tệp | `fig_4_5_section.png` (2424 × 2232) |
| Chứng minh | Một trong bốn thao tác **trong phạm vi** (§3.8): **tách khối** để nhìn cấu trúc bên trong. Nút đổi nhãn thành *“Ráp lại”* xác nhận cảnh đang ở trạng thái tách |
| Ca | Cùng bài với Hình 4.3, ở bước 12/12, sau khi bấm **Tách khối** |
| Vùng cắt | phần tử `.geo3d-canvas` |
| Chú thích | *Hình 4.5. Cùng cấu hình ở Hình 4.3b, sau thao tác tách khối. Các mặt của khối được tách rời để nhìn được cấu trúc bên trong; tương tác trong phạm vi đề tài là chọn, tách khối và tua bước, không phải kéo–thả liên tục.* |

⚠️ **Đã hạ phạm vi tuyên bố của hình này.** Kế hoạch ban đầu định dùng nó để
chứng minh *“phân biệt được thiết diện với các mặt của khối”*. Ảnh thật **không**
chứng minh điều đó rõ ràng: ở trạng thái tách, mặt thiết diện lẫn với các mặt vừa
tách ra. Thiết diện thực ra dễ thấy hơn ở Hình 4.3b (chưa tách). Do đó tuyên bố
của hình này được thu về đúng thứ ảnh cho thấy: **thao tác tách khối**.

---

## 4. Điều đã loại, và lý do

| bị loại | lý do |
|---|---|
| Sơ đồ riêng *“bốn tầng nhân hình học”* | Nó minh hoạ **một khối** của Hình 3.1. Bốn hộp xếp thẳng hàng không thêm thông tin nào mà đoạn văn §3.5.1 chưa nói ⇒ **gộp** vào Hình 3.1 |
| Ảnh chụp bảng kết quả kiểm thử | Số liệu đã có ở Bảng 4.9; ảnh chụp một bảng chữ không thêm gì |
| Ảnh chụp danh mục bài mẫu | Không chống đỡ luận điểm nào |
| Nhiều góc nhìn của cùng một cảnh | Trùng lặp; việc xoay được đã thể hiện qua chính các hình khác |

---

## 5. Hai điều phát hiện khi chụp, đáng ghi lại

**① Kế hoạch chụp ban đầu đặt kỳ vọng theo *tên ca*, không theo nội dung cảnh.**
Hình 4.2 lúc đầu định dùng ca *“lăng trụ xiên”* và yêu cầu ảnh phải *“thấy rõ
khối lăng trụ”*. Nhưng cảnh của ca ấy **không có khối nào**: chương trình dựng
tám điểm, một vectơ, một đường và một phép đo, còn hình lăng trụ chỉ tồn tại
trong đầu người đọc đề. Kiểm kê lại toàn bộ sáu ca cho thấy **chỉ hai ca có đối
tượng khối**. Kỳ vọng đã được sửa cho khớp cảnh thật, và ca chụp đổi sang một ca
có khối.

**② Hai hình dùng chung một ca, và đó là ràng buộc của tập trình diễn.** Hình
4.3 và Hình 4.5 cùng dựng trên bài chóp có thiết diện, vì chỉ hai ca có khối và
**đúng một** ca có đối tượng thiết diện. Hai hình chứng minh hai điều khác nhau —
tiến trình dựng theo bước, và thao tác tách khối — nên đây là dùng lại ca, không
phải chụp trùng.

---

## 6. Cách dựng lại

Sơ đồ: sửa tệp `.svg` rồi kết xuất lại sang PNG bằng bất kỳ trình duyệt nào.

Ảnh chụp: cần `cd frontend && npm run dev` (không cần khoá API, không cần
Docker), rồi điều khiển trình duyệt theo đúng trạng thái ghi ở §3. Kịch bản chụp
là công cụ tạm, cố ý đặt **ngoài** cây mã sản phẩm vì `frontend/scripts/**` đang
đóng băng.
