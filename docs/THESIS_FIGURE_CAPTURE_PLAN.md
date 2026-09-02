# THESIS_FIGURE_CAPTURE_PLAN — kế hoạch dựng hình và chụp màn hình

> **Mục đích.** Khi tới bước chụp hình, người thực hiện chỉ cần mở tài liệu này,
> làm theo từng dòng, không phải suy luận lại xem hình nào chứng minh điều gì.
>
> **Điều kiện chạy:** `cd frontend && npm run dev` — **không cần khoá API, không
> cần Docker**. Toàn bộ ảnh dưới đây chụp được từ tập bài mẫu chạy ngoại tuyến.
>
> **Quy ước:** mỗi hình nêu *chứng minh điều gì* trước, *chụp thế nào* sau. Hình
> nào không trả lời được câu "nó chứng minh điều gì" thì không nên có trong khoá
> luận.

---

## 1. Kiểm kê — trước và sau

| | trước | sau | thay đổi |
|---|:-:|:-:|---|
| Hình cần dựng (sơ đồ) | 6 | **5** | gộp Hình 3.5 vào 3.1 |
| Ảnh chụp màn hình | 3 | **4** | tách ca từ chối thành hình riêng |
| **Tổng** | 9 | **9** | |

Bốn ảnh chụp là số **tối thiểu** để phủ bốn luận điểm khác nhau. Không chụp thêm
màn hình gần giống nhau chỉ để tăng số hình.

---

## 2. Hình vẽ (dựng bằng công cụ đồ hoạ, không chụp màn hình)

### Hình 3.1 — Kiến trúc tổng thể · **GIỮ**

| | |
|---|---|
| Chứng minh | Ranh giới R0: chỉ **hai** khối thuộc mô hình ngôn ngữ, và cả hai nằm **trước** khi tồn tại bất kỳ toạ độ nào |
| Nguồn nội dung | `docs/THESIS_ARCHITECTURE.md §B`; bản thảo §3.1 |
| Cách dựng | Sơ đồ khối dọc, tô **ba vùng**: vùng mô hình ngôn ngữ · vùng tất định · vùng từ chối. Ghi rõ vị trí *"từ đây không còn lượt gọi mô hình"* |
| Gộp thêm | **Hình 3.5 cũ** (bốn tầng nhân hình học) đưa vào đây làm một khối con — nó là chi tiết của một khối, không cần một hình riêng |

**Chú thích dự kiến:** *Hình 3.1. Kiến trúc tổng thể của hệ thống. Hai khối tô
đậm thuộc mô hình ngôn ngữ; toàn bộ phần còn lại là tất định. Ranh giới R0 nằm
ngay sau bước tổng hợp chương trình: sau điểm này không còn lượt gọi mô hình nào,
nên mọi toạ độ và mọi phán quyết đúng/sai đều do các tầng tất định sinh ra.*

### Hình 3.2 — Từ đề bài tới Semantic Program tới cảnh 3D · **GIỮ**

| | |
|---|---|
| Chứng minh | Một bài đi trọn ba tầng biểu diễn, và **không tầng nào chứa toạ độ kết quả** |
| Nguồn nội dung | Bản thảo §3.4.4 (ca hình thoi) |
| Cách dựng | Ba cột song song: **đề bài** (tiếng Việt) → **chương trình** (rút gọn, xem §5 dưới) → **cảnh 3D** (phác thảo, không cần ảnh thật) |

**Chú thích dự kiến:** *Hình 3.2. Cùng một bài toán qua ba tầng biểu diễn. Toạ độ
xuất hiện ở cột giữa chỉ cho các điểm mà đề cho, mỗi điểm kèm định danh dữ kiện
nguồn; toạ độ của hai điểm được dựng ra không có mặt trong chương trình, vì nhân
hình học tính chúng khi thực thi.*

### Hình 3.3 — Vết thực thi → khung hình → cảnh 3D · **GIỮ**

| | |
|---|---|
| Chứng minh | Song ánh **khung hình thứ *k* ⇔ bước thứ *k*** |
| Nguồn nội dung | `docs/THESIS_ARCHITECTURE.md §G`; bản thảo §3.7 |
| Cách dựng | Ba hàng ngang xếp thẳng cột, mũi tên dọc nối bước *k* với khung *k*. Thể hiện **hai ngân sách tách bạch**: gộp bước để trình bày nằm ở tầng sau, không ở tầng dẫn xuất |

**Chú thích dự kiến:** *Hình 3.3. Cảnh ba chiều được dẫn xuất từ vết thực thi.
Khung hình thứ k suy ra hoàn toàn từ ảnh chụp bộ nhớ tại bước k, nên thao tác
"tua tới bước k" có nghĩa xác định. Việc gộp bước cho mục đích trình bày nằm ở
một tầng sau và không phá song ánh này.*

### Hình 3.4 — Sơ đồ tuần tự một yêu cầu · **GIỮ**

| | |
|---|---|
| Chứng minh | Thứ tự bảy cổng, và bốn đường từ chối cùng chi phí gọi mô hình của mỗi đường |
| Nguồn nội dung | `docs/THESIS_ARCHITECTURE.md §I` (đã có bản mermaid) |
| Cách dựng | Chuyển bản mermaid sẵn có sang hình vẽ. Ghi rõ trên mỗi nhánh từ chối: **số lượt gọi mô hình đã tiêu** |

**Chú thích dự kiến:** *Hình 3.4. Trình tự xử lý một yêu cầu. Đề không thuộc hình
học không gian bị từ chối tại biên miền với không lượt gọi mô hình nào; các đường
từ chối còn lại dừng sau bước tổng hợp và trước khi phát ra mô phỏng.*

### Hình 4.1 — Quỹ đạo bốn lượt thực nghiệm · **GIỮ**

| | |
|---|---|
| Chứng minh | Mỗi lượt đo cho một **khuôn hỏng lặp lại**, và khuôn ấy chỉ đích danh một khiếm khuyết giao diện cụ thể; sửa giao diện làm khuôn biến mất ở lượt sau |
| Nguồn nội dung | Bản thảo §4.7, Bảng 4.7 |
| Cách dựng | Trục ngang = bốn lượt theo thời gian. Mỗi lượt: kết quả chính (trên) và khuôn hỏng dẫn tới lượt sau (dưới), nối bằng mũi tên |

**Chú thích dự kiến:** *Hình 4.1. Quan hệ giữa bốn lượt thực nghiệm. Mỗi lượt
không chỉ cho một điểm số mà còn cho một khuôn hỏng lặp lại; khuôn hỏng ấy chỉ ra
một khiếm khuyết ở giao diện giữa mô hình và hệ thống, và việc sửa giao diện làm
khuôn hỏng tương ứng không còn xuất hiện ở lượt kế tiếp.*

### ~~Hình 3.5 — Bốn tầng nhân hình học~~ · **GỘP vào Hình 3.1**

Lý do: nó minh hoạ **một khối** của kiến trúc tổng thể. Một hình riêng cho bốn
hộp xếp thẳng hàng không thêm thông tin nào mà đoạn văn §3.5.1 chưa nói.

---

## 3. Ảnh chụp màn hình

> **Chuẩn bị chung (làm một lần).**
> ```bash
> cd frontend && npm run dev        # mở http://localhost:3000
> ```
> Chọn bài mẫu hình học từ danh mục ngoại tuyến. Đặt cửa sổ trình duyệt ở tỉ lệ
> **16:9**, độ rộng tối thiểu **1440 px** để chữ trong ảnh còn đọc được sau khi
> thu nhỏ vào khổ giấy. Ẩn thanh dấu trang và các phần mở rộng của trình duyệt.

### Hình 4.2 — Xưởng hình 3D, chế độ chi tiết · **CHỤP**

| trường | giá trị |
|---|---|
| **Chứng minh** | Mỗi vật trong cảnh mang **xuất xứ**: bước nào tạo ra nó, và nó phụ thuộc cái gì. Nếu mô hình chỉ đoán toạ độ rồi khai ra, cột phụ thuộc sẽ trống |
| Màn hình | Xưởng hình 3D (`Scene3DExplorer`) |
| Ca demo | **Lăng trụ xiên** (ca thứ hai của tập trình diễn) — có hai vectơ dẫn xuất và một trung điểm, nên cây phụ thuộc đủ sâu để thấy |
| Trạng thái | Tua tới **bước cuối** |
| Thao tác | Bật **Chi tiết** → chọn một đỉnh dẫn xuất → mở ô soi bên phải |
| Khung nhìn | Xoay sao cho thấy rõ tính **xiên** của lăng trụ (không nhìn chính diện) |
| Phải thấy trong ảnh | ô soi hiện `producer` và `depends`; ô số bước hiện `7/7` |

**Chú thích dự kiến:** *Hình 4.2. Giao diện xưởng hình ba chiều ở chế độ chi
tiết. Ô soi bên phải hiển thị bước đã tạo ra đối tượng đang chọn và danh sách đối
tượng mà nó phụ thuộc; cấu trúc phụ thuộc này được dẫn xuất từ chương trình, chứ
không phải một danh sách toạ độ được khai trực tiếp.*

### Hình 4.3 — Tua bước · **CHỤP** (ảnh ghép hai trạng thái)

| trường | giá trị |
|---|---|
| **Chứng minh** | Cảnh tại bước *k* là **kết quả của lượt chạy tới bước *k***, không phải một hoạt hình dựng sẵn |
| Màn hình | Xưởng hình 3D |
| Ca demo | **Dây chuyền tịnh tiến bốn đỉnh** (10 bước — chuỗi sâu nhất trong tập) |
| Trạng thái | **Hai ảnh**: bước 4 và bước 10, **cùng góc camera** |
| Thao tác | Kéo thanh trượt bước; **không** xoay camera giữa hai lần chụp |
| Phải thấy trong ảnh | ô số bước hiện `4/10` rồi `10/10`; số đối tượng trong cảnh tăng lên |

**Chú thích dự kiến:** *Hình 4.3. Cùng một bài tại bước 4 (trái) và bước 10
(phải), giữ nguyên góc nhìn. Các đối tượng xuất hiện đúng theo thứ tự chương
trình dựng chúng; cảnh tại mỗi bước được dẫn xuất từ trạng thái bộ nhớ tại bước
tương ứng.*

### Hình 4.4 — Từ chối có địa chỉ · **CHỤP**

| trường | giá trị |
|---|---|
| **Chứng minh** | Hệ **không đoán**: khi dữ kiện không truy được về đề, nó dừng **trước khi thực thi**, nói vì sao bằng tiếng Việt, và **không dựng cảnh 3D nào** |
| Màn hình | Vùng làm việc, trạng thái từ chối |
| Ca demo | **Giao đường–mặt, dữ kiện không truy được** (ca thứ năm) |
| Trạng thái | Ngay sau khi mở ca |
| Phải thấy trong ảnh | thông điệp tiếng Việt đọc được; **không có khung 3D nào**; không có mã lỗi kỹ thuật lộ lên giao diện |

**Chú thích dự kiến:** *Hình 4.4. Màn hình khi cổng truy nguồn dữ kiện từ chối
một chương trình. Hệ thống nêu lý do bằng ngôn ngữ người học đọc được và không
dựng cảnh ba chiều kèm theo — thà không trình bày gì còn hơn trình bày một kết
quả chưa được kiểm chứng.*

### Hình 4.5 — Thiết diện và tách khối · **CHỤP**

| trường | giá trị |
|---|---|
| **Chứng minh** | Hệ dựng được **thiết diện** như một đối tượng thật trong cảnh, và người học tách khối ra để nhìn cấu trúc bên trong |
| Màn hình | Xưởng hình 3D |
| Ca demo | **Thiết diện, góc và thể tích** (ca thứ sáu, chế độ rút gọn) |
| Trạng thái | Bước cuối, đã bấm **Tách khối** |
| Khung nhìn | Xoay để mặt cắt hướng về phía người xem |
| Phải thấy trong ảnh | mặt thiết diện phân biệt rõ với các mặt của khối |

**Chú thích dự kiến:** *Hình 4.5. Thiết diện của một khối đa diện, hiển thị ở chế
độ tách khối. Thiết diện là một đối tượng do chương trình dựng và được kiểm chứng
bằng cách dựng lại từ khối và mặt phẳng rồi so chu trình đỉnh, chứ không phải một
mặt phẳng được vẽ chồng lên hình.*

---

## 4. Điều KHÔNG chụp

| bị loại | lý do |
|---|---|
| Bảng kết quả kiểm thử trong trình duyệt | dữ liệu đã có ở Bảng 4.9; ảnh chụp một bảng chữ không thêm gì |
| Màn hình danh mục bài mẫu | không chống đỡ luận điểm nào |
| Ảnh cảnh 3D không có ô soi | trùng Hình 4.2 nhưng ít thông tin hơn |
| Nhiều góc nhìn của cùng một hình | trùng lặp; nếu cần thể hiện việc xoay được thì dùng Hình 4.3 |

---

## 5. Rút gọn khối mã trong bản thảo

Ví dụ Semantic Program ở §3.4.4 hiện dài **8 câu lệnh**. Với bản in:

- **Thân luận văn** giữ **4 câu lệnh** đủ thể hiện bốn ý: một `declare_point` có
  định danh dữ kiện nguồn · một `assign` dựng vectơ · một `construct_point` dùng
  phép tịnh tiến với toán hạng là **tên** · một `assign` gọi phép đo.
- **Phụ lục C** giữ chương trình đầy đủ, kèm phần khai báo bộ nhớ.

Lý do: bốn câu lệnh ấy đã chứng minh trọn năm điều mà §3.4.4 rút ra; bốn câu còn
lại chỉ lặp lại cùng một hình dạng.

---

## 6. Thứ tự thực hiện

1. Dựng năm hình vẽ (§2) — không cần chạy ứng dụng.
2. Mở ứng dụng, chụp bốn ảnh theo §3, **theo đúng thứ tự** để không phải mở lại
   ứng dụng nhiều lần.
3. Rút gọn khối mã theo §5, chuyển bản đầy đủ xuống Phụ lục C.
4. Chèn chú thích đã viết sẵn ở trên; **không viết lại chú thích** — chúng đã
   được soạn để nêu ý nghĩa chứ không chỉ mô tả nội dung ảnh.
