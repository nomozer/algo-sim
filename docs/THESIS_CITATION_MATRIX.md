# THESIS_CITATION_MATRIX — mỗi trích dẫn đang chống đỡ câu nào

> **Vì sao có file này.** Một danh mục tài liệu tham khảo đẹp mà không ai biết
> nguồn nào chống đỡ câu nào là một danh mục **không kiểm được**. Bảng dưới đây
> đi theo chiều ngược lại: bắt đầu từ **câu trong bản thảo**, rồi mới hỏi nguồn
> nào chống đỡ nó, và chống đỡ tới mức nào.
>
> Metadata đầy đủ của từng mã nguồn: `docs/THESIS_REFERENCES.md`.
>
> **Ba mức chống đỡ**
> **DIRECT** — nguồn phát biểu đúng điều claim nói, trên đúng đối tượng ấy.
> **PARTIAL** — nguồn phát biểu điều tương tự nhưng khác đối tượng, khác phạm vi,
> hoặc chỉ chống đỡ một vế.
> **CONTEXT_ONLY** — nguồn dựng bối cảnh; **không** được dùng để chống đỡ một
> khẳng định mạnh.
>
> Lượt lập: 2026-09-02. **0 lượt gọi model ứng dụng.**

---

## 1. Chương trình chính thức

| ID | vị trí | câu trong bản thảo | nguồn | mức | giới hạn |
|---|---|---|---|:-:|---|
| `C16.1` | §4.10, MĐ §4 | Khung tham chiếu là Chương trình GDPT môn Toán ban hành kèm Thông tư 32/2018/TT-BGDĐT (26/12/2018), phần Toán không bị Thông tư 13/2022 sửa đổi | [BGD-TT32] [BGD-TT13] | **DIRECT** | TT13 mới xác minh ở mức trang liệt kê |
| `C16.2` | §4.10 | Chương trình chính thức chia hình học không gian lớp 11–12 thành **15 đầu mục nội dung** (11 ở lớp 11, 4 ở lớp 12) | [BGD-TOAN] | **DIRECT** | đếm từ mục *Nội dung* trong bảng "Yêu cầu cần đạt", tr. 97–101 và 108–109 |
| `C16.3` | §4.10, §5.3.6 | *"Khoảng cách trong không gian"* là **một** đầu mục chính thức, bao gồm cả khoảng cách hai đường chéo nhau | [BGD-TOAN] | **DIRECT** | — |
| `C16.4` | §4.10, §5.3.1 | Mặt cầu · mặt nón · mặt trụ thuộc **lớp 9**; lớp 12 chỉ có *"Phương trình mặt cầu"*. *"Quỹ tích"* **không xuất hiện** trong chương trình | [BGD-TOAN] | **DIRECT** | đã tìm toàn văn 123 trang; "quỹ tích" cho 0 kết quả |

---

## 2. Khó khăn không gian và trực quan hoá

| ID | vị trí | câu trong bản thảo | nguồn | mức | giới hạn |
|---|---|---|---|:-:|---|
| `C1.1` | MĐ §1, §1.1, §1.2 | Người học gặp khó khi làm việc với khái niệm toán trong môi trường ba chiều; năng lực hình dung không gian là một kỹ năng riêng cần phát triển | [MED24] | **PARTIAL** | mẫu là **sinh viên kỹ thuật**, không phải học sinh THPT Việt Nam |
| `C2.1` | MĐ §1, §1.2 | Phần mềm hình học động cải thiện năng lực toán của học sinh so với dạy học truyền thống | [JUA21] [MED24] | **DIRECT** | [JUA21] chỉ gộp nghiên cứu **tại Indonesia 2010–2020**; effect size lớn nhưng bối cảnh hẹp |

⛔ **Ranh giới bắt buộc.** Không claim nào ở đây được dùng để nói **hệ thống của
khoá luận** cải thiện kết quả học tập. `LEARNER_IMPACT_NOT_EVALUATED` giữ nguyên
(§5.3.5). Hai claim này chống đỡ **động cơ thiết kế**, không chống đỡ hiệu quả
của sản phẩm.

---

## 3. Mô hình ngôn ngữ — năng lực và giới hạn

| ID | vị trí | câu trong bản thảo | nguồn | mức | giới hạn |
|---|---|---|---|:-:|---|
| `C4.1` | §1.3, §2.1 | Mô hình ngôn ngữ đọc và phân rã được bài toán phát biểu bằng ngôn ngữ tự nhiên | [GAO23] | **DIRECT** | [GAO23] nêu rõ mô hình *"adept at step-by-step decomposition"* |
| `C4.2` | §1.4, §2.1 | Nhưng suy luận toán của chúng **không có bảo đảm hình thức**: mô hình sai ở phần tính toán ngay cả khi phân rã đúng | [GAO23] [MIR25] | **DIRECT** | — |
| `C5.1` | §2.1 | Đầu ra dao động giữa các biến thể của cùng một bài; hiệu năng giảm khi độ phức tạp tăng, và một mệnh đề không liên quan có thể làm giảm tới 65% | [MIR25] | **DIRECT** | đo trên bài toán lời văn số học (GSM), **không** trên hình học không gian |

> `C5.1` là claim gần nhất mà tài liệu bên ngoài chống đỡ được cho luận điểm
> *"đầu ra LLM không tất định"*. Nó nói về **độ bền trước biến thể đầu vào**,
> không nói về tính ngẫu nhiên của phép lấy mẫu. Bản thảo phát biểu đúng phạm vi
> ấy — xem `THESIS_REFERENCE_NEEDS §5`.

---

## 4. Đầu ra có cấu trúc

| ID | vị trí | câu trong bản thảo | nguồn | mức | giới hạn |
|---|---|---|---|:-:|---|
| `C6.1` | §2.1 | **Lược đồ ràng buộc hình dạng, không ràng buộc ngữ nghĩa** — một chương trình khớp lược đồ hoàn toàn vẫn có thể dựng sai hình | *(lập luận thiết kế của đề tài)* + bằng chứng nội bộ §4.6.3 | **—** | **không** gán cho nguồn ngoài nào |
| `C6.2` | §2.1 | Ràng buộc định dạng có thể **làm suy giảm** năng lực suy luận, và ràng buộc càng chặt thì suy giảm càng lớn | [TAM24] | **DIRECT** | mới xác minh ở mức trang liệt kê; kết quả đo trên tác vụ suy luận tổng quát |

> **`C6.1` cố ý KHÔNG có citation.** Không nguồn nào tìm được phát biểu đúng câu
> ấy. Nó là **suy luận thiết kế** của đề tài, và nó được minh hoạ bằng thực
> nghiệm nội bộ: ở §4.6.3, cả bốn chương trình đều tuân thủ hợp đồng ở bản thô
> (42/42 ô đúng hình dạng) mà hai trong số đó vẫn hỏng vì hai luật khác. Ghi
> nguồn ngoài cho câu này sẽ là gán cho bài báo một kết luận nó không nói.

---

## 5. LLM sinh chương trình thay vì đáp án

| ID | vị trí | câu trong bản thảo | nguồn | mức | giới hạn |
|---|---|---|---|:-:|---|
| `C7.1` | §1.4, §2.9 mới | Hướng **để mô hình sinh chương trình, giao phần tính cho một runtime tất định** đã có trong tài liệu (PAL), và nó vượt chuỗi-suy-nghĩ trên các bộ đo toán | [GAO23] | **DIRECT** | — |
| `C7.2` | §5.2 | ⇒ Ý tưởng "LLM sinh chương trình" **KHÔNG phải đóng góp mới** của khoá luận | [GAO23] | **DIRECT** | dùng để **hạ** claim của chính khoá luận, không để nâng |

> `C7.2` là loại trích dẫn quan trọng nhất và dễ bị bỏ sót nhất: nguồn được dùng
> để **thu hẹp** tuyên bố đóng góp, chứ không để chống đỡ nó.

---

## 6. Số học và vị ngữ hình học

| ID | vị trí | câu trong bản thảo | nguồn | mức | giới hạn |
|---|---|---|---|:-:|---|
| `C10.1` | §2.5 | Số dấu chấm động không biểu diễn chính xác phần lớn số hữu tỉ và sai số tích luỹ qua chuỗi phép tính | [GOL91] | **DIRECT** | kinh điển; mới xác minh metadata qua ACM DL |
| `C10.2` | §2.5, §3.5.2 | Với hình học, hệ quả là **vị ngữ trở thành không quyết định được**: cài bằng `float` có thể cho kết quả sai hoặc không nhất quán | [SHE97] | **DIRECT** | — |
| `C9.1` | §2.4 | Tính chắc chắn (robustness) của thuật toán hình học là vấn đề đã được ngành nhận diện và có lời giải bằng số học chính xác | [SHE97] | **DIRECT** | ⇒ số học chính xác là **quyết định thiết kế đã biết**, không phải phát minh của khoá luận |

⛔ **Không** claim nào ở đây nói *"mọi engine dùng `float` đều không dùng được"*.
[SHE97] chính nó đưa ra số học **thích ứng** trên nền `float`.

---

## 7. Rủi ro của đầu ra sai trong giáo dục

| ID | vị trí | câu trong bản thảo | nguồn | mức | giới hạn |
|---|---|---|---|:-:|---|
| `C13.1` | MĐ §1, §2.8 | Quan niệm sai một khi hình thành thì **khó sửa** và dai dẳng | *(chưa có nguồn đã xác minh)* | **—** | xem cảnh báo dưới |
| `C13.2` | MĐ §1, §2.8, §5.5 | Người dùng có xu hướng **chấp nhận đầu ra sai của AI** (lệ thuộc quá mức), làm giảm việc kiểm chứng độc lập | [PAS22] | **DIRECT** | **báo cáo kỹ thuật, không bình duyệt**; tổng hợp ~60 công trình |

⚠️ **`C13.1` chưa có nguồn đã xác minh.** Tìm được vài tổng quan về tính dai dẳng
của quan niệm sai nhưng **chưa mở và đọc** bài nào, nên không ghi vào danh mục.
Hệ quả cho bản thảo: câu tương ứng đã được **hạ giọng** — xem §18 của
`THESIS_REFERENCE_NEEDS` và cách phát biểu mới ở §2.8.

---

## 8. Định vị neural-symbolic và công trình liên quan

| ID | vị trí | câu trong bản thảo | nguồn | mức | giới hạn |
|---|---|---|---|:-:|---|
| `C14.1` | §1.8 mới, §5.2 | Kết hợp thành phần nơ-ron với thành phần ký hiệu là một hướng **có tên và có khảo sát** trong tài liệu | [GIB23] | **CONTEXT_ONLY** | **tiền ấn bản**, chưa mở toàn văn ⇒ **không** trích taxonomy cụ thể nào |
| `C14.2` | §1.8 mới | Đã có hệ neuro-symbolic đạt mức olympiad cho **hình học phẳng**, với nhiệm vụ là **chứng minh định lí** | [TRI24] | **DIRECT** | phạm vi: Euclidean **plane** geometry |
| `C14.3` | §1.8 mới, §5.2 | ⇒ Nhiệm vụ của khoá luận **khác**: hình học **không gian**, và đầu ra là **mô phỏng 3D chạy được**, không phải một chứng minh | [TRI24] | **DIRECT** | dùng để **phân biệt**, không để so điểm chuẩn |

⛔ **Không gán nhãn taxonomy.** Việc phân loại kiến trúc của đề tài ở §5.2 là
**suy luận của tác giả khoá luận**, nêu rõ như vậy, và **không** được trình bày
như một phân loại lấy từ [GIB23].

---

## 9. Kiểm toán trích dẫn

Mọi số dưới đây **đếm từ các bảng §1–§8** của chính file này.

### Phân bố claim

| | số | dẫn từ |
|---|:-:|---|
| §1 chương trình | 4 | C16.1 C16.2 C16.3 C16.4 |
| §2 khó khăn không gian | 2 | C1.1 C2.1 |
| §3 năng lực/giới hạn LLM | 3 | C4.1 C4.2 C5.1 |
| §4 đầu ra có cấu trúc | 2 | C6.1 C6.2 |
| §5 sinh chương trình | 2 | C7.1 C7.2 |
| §6 số học & vị ngữ | 3 | C10.1 C10.2 C9.1 |
| §7 rủi ro đầu ra sai | 2 | C13.1 C13.2 |
| §8 định vị neural-symbolic | 3 | C14.1 C14.2 C14.3 |
| **Tổng claim** | **21** | |

### Trạng thái nguồn

| | số | dẫn từ |
|---|:-:|---|
| Có nguồn ngoài **đã xác minh** | **19** | 21 trừ C6.1 và C13.1 |
| **Cố ý** không có nguồn ngoài | **1** | `C6.1` — lập luận thiết kế, minh hoạ bằng bằng chứng nội bộ |
| Còn **thiếu** nguồn, đã hạ giọng trong bản thảo | **1** | `C13.1` |

`19 + 1 + 1 = 21` ✔

### Mức chống đỡ (trên 19 claim có nguồn)

| mức | số | dẫn từ |
|---|:-:|---|
| **DIRECT** | **17** | 19 trừ C1.1 và C14.1 |
| **PARTIAL** | **1** | `C1.1` (mẫu là sinh viên kỹ thuật) |
| **CONTEXT_ONLY** | **1** | `C14.1` (tiền ấn bản, chưa mở toàn văn) |

`17 + 1 + 1 = 19` ✔

### Kiểm toán

| chỉ số | số |
|---|:-:|
| Trích dẫn **không gắn claim** nào | **0** |
| Nguồn **trùng lặp** | **0** |
| Nguồn **thứ cấp** dùng ở chỗ đã có nguồn gốc | **0** |
| Claim mạnh **không có** nguồn tương xứng | **0** |

Về dòng cuối: `C6.1` và `C13.1` đều **không** còn là claim mạnh trong bản thảo —
cái thứ nhất được khai rõ là lập luận thiết kế, cái thứ hai đã hạ giọng. Năm liên
kết tài liệu ôn thi từng đóng vai nguồn chương trình nay đã bị hạ xuống *tài liệu
thứ cấp tham khảo*, thay bằng [BGD-TOAN].
