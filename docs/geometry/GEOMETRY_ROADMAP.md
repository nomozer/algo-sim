# GEOMETRY ROADMAP — phạm vi và thứ tự

> Đề: *"Nghiên cứu và xây dựng hệ thống mô phỏng 3D hình học không gian"*.
> **Không mở ngoài hình học không gian THPT.**

---

## 0. Câu phạm vi

> Hệ nhận **đề hình học không gian bằng ngôn ngữ tự nhiên** (kèm hình vẽ nếu
> có), LLM tổng hợp một **mô hình ngữ nghĩa hình học có biên**, một **kernel
> tất định** tính mọi toạ độ và quan hệ, engine dựng **timeline từng bước**, và
> học sinh **quan sát – xoay – chọn – kéo trong ràng buộc toán học** trên cảnh
> 3D.

**KHÔNG phải**: *"AI vẽ hình 3D rồi hiển thị."* Ranh giới R0 giữ nguyên — LLM
**không bao giờ** quyết toạ độ cuối cùng.

---

## 1. Trong phạm vi — ba lớp bài, MỘT kernel

Chọn ba lớp vì chúng **dùng chung một nhân**, nên chi phí không cộng ba lần.

| # | Lớp bài | Chương trình | Cơ chế ẩn (điều kiện `COVERAGE §2`) |
|---|---|---|---|
| **1** | **Thiết diện** của mặt phẳng với hình chóp / lăng trụ | Toán 11 | Học sinh **không hình dung nổi giao tuyến** trong đầu. Cơ chế ẩn lớn nhất của cả chương |
| **2** | **Quan hệ song song & vuông góc** đường–mặt, mặt–mặt | Toán 11 | Hình biểu diễn phẳng **nói dối**: hai đường trông cắt nhau mà thực ra chéo nhau |
| **3** | **Khoảng cách & thể tích** | Toán 11–12 | Chân đường vuông góc nằm ở đâu — thứ hình vẽ tay hay đặt sai |

**Chỉ khối đa diện lồi.** Không mặt cong.

---

## 2. Ngoài phạm vi — cố ý, ghi để khỏi trôi

| Bỏ | Vì sao |
|---|---|
| Mặt tròn xoay (nón, trụ, cầu) | kernel phải xử lý mặt cong — nhân đôi độ khó, dùng cho **một** lớp bài |
| Oxyz như chuyên đề riêng | Oxyz là **nền tính toán bên trong**, không phải chủ đề dạy |
| Dựng hình bằng thước–compa | phẳng, khác miền |
| Kéo cập nhật **theo từng pixel** | phá song ánh `frame ⇔ trace` (xem GAP §0) |
| Chấm bài / sinh đề / luyện tập | ngoài "mô phỏng" |
| Tự động chứng minh | LLM tổng hợp **các bước dựng**, không sinh chứng minh hình thức |

---

## 3. Bảy giai đoạn — thứ tự bị ràng buộc bởi phụ thuộc

Không đảo được: mỗi giai đoạn tiêu thụ đầu ra của giai đoạn trước.

| # | Giai đoạn | Ra cái gì | Cổng qua |
|---|---|---|---|
| **1** | **Audit** ✅ *đã xong* | `GEOMETRY_ARCHITECTURE_GAP_REPORT` | — |
| **2** | **Geometry kernel** + oracle | nhân tất định; oracle **cài độc lập** | cùng input = cùng output; oracle khớp trên bộ bài kiểm tay |
| **3** | **Mở IR** | 6 kiểu · 5 biểu thức · 3 câu lệnh dựng · 7 nghĩa vụ | schema sync; bump `CACHE_VERSION` 3 chỗ |
| **4** | **Renderer 3D** | cảnh Three.js + camera + picking | 4 bề rộng; faultcheck ĐỎ được |
| **5** | **Timeline dựng hình** | mỗi bước = giao/nối/tô | song ánh #31 giữ; narration khớp state |
| **6** | **Tương tác** | orbit/zoom/pan · chọn · **kéo có ràng buộc** | mọi thay đổi đi qua `module.apply`; renderer không tự sửa |
| **7** | **Đánh giá** | corpus + SEALED hình học | quy trình cũ, corpus mới |

**Giai đoạn 2 là đường găng.** Sai ở đó thì mọi thứ sau đều xây trên cát, và
sai kiểu **im lặng** (float so bằng `==`) chứ không kiểu nổ.

---

## 4. Ba demo bắt buộc — ánh xạ thẳng vào ba lớp bài

| Demo | Bài | Đủ tiêu chí khi |
|---|---|---|
| **1** | Thiết diện hình chóp S.ABCD cắt bởi (MNP) | xoay · zoom · highlight · timeline 5 bước · giải thích từng bước |
| **2** | Chứng minh `SA ⊥ (ABCD)` | quan hệ nổi bật được; xoay để thấy vuông góc thật; **so hình biểu diễn phẳng ↔ khối 3D** |
| **3** | Khoảng cách từ A đến (SBC), thể tích chóp | chân đường vuông góc dựng bằng kernel; số khớp oracle |

Demo 2 mang **luận điểm sư phạm mạnh nhất**: chỉ ra chỗ **hình vẽ trong vở nói
dối**. Đó là lý do 3D **không trang trí** — cùng khuôn `meaning_of_z` đã có
tiền lệ.

---

## 5. Ràng buộc không được phá

Năm cái này **đã là bất biến có test**, không phải mục tiêu phải dựng:

1. **R0** — LLM không quyết kết quả. Với hình học: LLM **không được** khai toạ
   độ giao điểm; nó chỉ được nói *"lấy giao tuyến của (SAB) và (SCD)"*.
2. **Song ánh #31** — khung `k` suy hoàn toàn từ trạng thái bước `k`.
3. **Renderer chỉ ĐỌC** — mọi toạ độ có sẵn trong frame.
4. **Fail-closed** — hai mặt phẳng song song mà đòi giao tuyến ⇒ **ném lỗi**,
   không trả `None`, không vẽ bừa.
5. **Right-or-refuse** — đề ngoài năng lực → `capability_gap` trung thực.

---

## 6. Rủi ro, và cách cắt nếu hụt thời gian

| Rủi ro | Mức | Cắt được gì |
|---|---|---|
| Kernel nuốt thời gian | **CAO** | bỏ thể tích, giữ thiết diện + quan hệ |
| Renderer 3D nuốt thời gian | **CAO** | **làm 2D trước cho state đúng**, 3D sau. Nét đứt cạnh khuất là bắt buộc, còn lại cắt được |
| Kéo có ràng buộc | TRUNG BÌNH | cắt xuống chỉ còn **chọn + xoay**; luận văn vẫn đứng |
| Corpus + SEALED mới | TRUNG BÌNH | hạ `N`, khai rõ mẫu nhỏ theo luật đã tiền đăng ký |
| LLM sinh IR hình học kém | TRUNG BÌNH | **đo trên DEV trước** — hạ tầng đã có |

**Thứ tự cắt, quyết trước cho khỏi hoảng lúc gần hạn:** (1) thể tích → (2) kéo
có ràng buộc → (3) demo 3 → (4) hạ `N`.

**Không được cắt:** kernel tất định · oracle độc lập · song ánh #31 · fail-closed.
Cắt bốn cái đó là mất chính luận điểm.
