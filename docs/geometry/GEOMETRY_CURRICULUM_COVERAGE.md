# PHỦ CHƯƠNG TRÌNH — Hình học không gian THPT

> Bảng này trả lời câu hội đồng sẽ hỏi: **"hệ làm được bao nhiêu phần của chương
> trình phổ thông?"** — bằng con số, không bằng cảm giác.
>
> Mọi ô **ĐƯỢC / KHÔNG** dưới đây đo bằng cách **chạy thật** phép đo/vị ngữ
> tương ứng, không suy từ tên hàm. Nhật ký đo ở §5.

Khung chương trình tham chiếu: **GDPT 2018 môn Toán** — nhưng xem cảnh báo ở
`## Nguồn` (cuối file): **`CURRICULUM_SOURCE_VERIFICATION = NEEDS_EXTERNAL_SOURCE`**.
Danh sách chủ đề hiện dẫn từ tài liệu ôn tập thứ cấp, **chưa** từ văn bản gốc.

---

## 1. Kết quả gọn

> **Mỗi số dưới đây ĐẾM ĐƯỢC từ các bảng §2–§4 của chính file này.** Không có
> con số nào chép tay. Kiểm lại bằng một lệnh:
>
> ```bash
> grep -cE '^\| [0-9]+b? \|.*\| ✅ \|$' docs/geometry/GEOMETRY_CURRICULUM_COVERAGE.md
> ```
> (đổi `✅` thành `⚠️` / `❌` cho hai hàng còn lại).
>
> Chốt trên hệ đóng băng `082da95` (candidate `a075e9f5…`), audit năng lực chạy
> lại ngày 2026-09-02 — xem §5.

| | | dẫn từ |
|---|---|---|
| Chủ đề khảo sát | **21** | số hàng của §2 (6) + §3 (8) + §4 (7) |
| **ĐƯỢC** diễn đạt trọn | **15** | #1 #2 #3 #4 #7 #8 #9 #10 #12 **#13** #14 #15 #16 #16b #17 |
| **MỘT PHẦN** | **2** | #6 (phép toán vectơ) · #11 (góc nhị diện có miền) |
| **KHÔNG** diễn đạt được | **4** | #5 · #18 · #19 · #20 |

`15 + 2 + 4 = 21` ✔

⚠️ Đây là phủ **HỢP ĐỒNG** (IR biểu đạt nổi hay không), **KHÔNG** phải phủ
**NĂNG LỰC** (AI có sinh đúng hay không). Một chủ đề "ĐƯỢC" vẫn có thể trượt vì
mô hình viết sai — đó là câu hỏi của Phase 5, không phải của bảng này.

### 1b. ⛔ Bản tóm tắt CŨ đã SAI TỪ ĐẦU — ghi lại để không ai khôi phục nó

Khối §1 trước đây ghi **18 chủ đề = 9 trọn / 4 một phần / 5 không**. Con số ấy
**chưa bao giờ khớp** các bảng chi tiết — và đây không phải chuyện lạc hậu, đã
truy bằng `git`:

| bản | bảng chi tiết đếm được | khối tóm tắt ghi |
|---|---|---|
| `a19529f` (bản đầu tiên) | 21 hàng — 14 ✅ / 2 ⚠️ / 5 ❌ | 18 — 9 / 3 / 6 |
| `ff3b713` (nối khoảng cách, 2026-08-30) | 21 hàng — 14 ✅ / 3 ⚠️ / 4 ❌ | 18 — 9 / 4 / 5 |
| `082da95` (nay, sau khi vá #13) | 21 hàng — 15 ✅ / 2 ⚠️ / 4 ❌ | *(khối này)* |

Đọc theo hàng ngang: **tập hàng chưa từng đổi** — vẫn đúng 21 hàng `#1`–`#20`
cộng `#16b`, không hàng nào được thêm, tách, gộp hay bỏ. Thứ duy nhất từng đổi
là **một ô phân loại** (`#13`, hai lần).

Đọc theo hàng dọc: khối tóm tắt **được cập nhật đúng chiều** ở `ff3b713`
(`3→4` một phần, `6→5` không) — tức người sửa có theo dõi thay đổi. Nhưng nó
cập nhật **trên một nền sai**: `18` và `9` không dẫn từ hàng nào cả.

⇒ Bài học vận hành, và nó là bài học chung của repo này: **một con số chép tay
không có sync-lock thì sai ngay từ lúc gõ, chứ không chỉ trôi về sau.** Mọi số
ở §1 nay đều kèm cột *dẫn từ* và một lệnh đếm.

---

## 2. Toán 11 — Đường thẳng & mặt phẳng trong không gian

| # | Chủ đề | Nghĩa vụ / cơ chế | |
|---|---|---|:-:|
| 1 | Đại cương: điểm · đường · mặt, **giao tuyến hai mặt** | `point_on_line` + `intersect_plane_plane` | ✅ |
| 2 | Hai đường thẳng **song song** | `parallel` → `P.parallel_lines` | ✅ |
| 3 | Đường thẳng **∥ mặt phẳng** | `parallel` → `P.parallel_line_plane` | ✅ |
| 4 | Hai mặt phẳng **song song** | `parallel` → `P.parallel_planes` | ✅ |
| 5 | **Phép chiếu song song**, hình biểu diễn | — | ❌ |
| 6 | **Vectơ** trong không gian | kiểu `vector3` có; **phép toán vectơ không có** | ⚠️ |

**#5 — vì sao KHÔNG.** IR chỉ có `project_onto`, và nó là **chiếu vuông góc**
(`K.project_point_onto_plane`). Chiếu song song theo một phương cho trước là
phép khác, kernel không có. Đây là chủ đề *dựng hình biểu diễn* — cốt lõi của
việc **vẽ hình không gian trên giấy**, và hệ không nói về nó được.

**#6 — vì sao MỘT PHẦN.** `vector3` là một kiểu bộ nhớ, nhưng IR **không có**
phép cộng vectơ, nhân vô hướng, hay tích vô hướng ở tầng biểu thức. Đề *"phân
tích $\vec{SM}$ theo $\vec{SA}, \vec{SB}, \vec{SC}$"* không viết ra được.

---

## 3. Toán 11 — Quan hệ vuông góc

| # | Chủ đề | Nghĩa vụ / cơ chế | |
|---|---|---|:-:|
| 7 | Hai đường thẳng **vuông góc** | `perpendicular` → `P.perpendicular_lines` | ✅ |
| 8 | Đường thẳng **⊥ mặt phẳng** | `perpendicular` → `P.line_perpendicular_plane` | ✅ |
| 9 | Hai mặt phẳng **vuông góc** | `perpendicular` → `P.perpendicular_planes` | ✅ |
| 10 | **Góc** giữa đường–đường · đường–mặt · mặt–mặt | `angle`, đo bằng `cos²`/`sin²` | ✅ |
| 11 | **Góc nhị diện** | chỉ có góc hai mặt phẳng | ⚠️ |
| 12 | **Khoảng cách** — điểm↔mặt, điểm↔đường | `distance` | ✅ |
| 13 | **Khoảng cách** — đường↔mặt ∥, mặt↔mặt ∥, **hai đường chéo nhau** | `distance` (nối 2026-08-30; miền số mở 2026-08-31) | ✅ |
| 14 | **Hình chiếu vuông góc** của điểm | `project_onto` | ✅ |

**#11 — vì sao MỘT PHẦN.** Góc nhị diện có **miền** (nửa mặt phẳng) và có thể
tù; `cos_sq_between_planes` trả **bình phương cosin của góc giữa hai mặt phẳng**,
luôn thuộc $[0°, 90°]$. Đề hỏi *"góc nhị diện $[A, SB, C]$ bằng $120°$"* thì hệ
trả lời được góc mặt-mặt là $60°$ — **đúng theo định nghĩa của nó**, sai theo
câu hỏi.

**#16 — checker đổi 2026-08-30.** `coplanar` trên một thiết diện **gần như
luôn xanh**: mọi đỉnh của nó sinh ra từ giao với đúng MỘT mặt phẳng nên chúng
đồng phẳng theo định nghĩa — một chương trình bỏ sót đỉnh thứ tư vẫn qua cổng.
Nghĩa vụ `section_matches` dựng lại thiết diện chuẩn từ `params.solid +
params.plane` rồi so chu trình (bất biến với xoay và đảo hướng). Chi tiết và
giới hạn còn lại: `docs/evaluation/geometry/FULL_SECTION_EXTENSION.md`.

**#13 — NAY LÀ ✅. Hai lần vá, hai lỗ khác nhau, và ô này lạc hậu ở lần thứ hai.**

| ngày | lỗ được vá | ô #13 |
|---|---|---|
| 2026-08-30 | **cầu nối IR** — `geometry_exec._do` không nối tới `distance_sq_*` của kernel | ❌ → ⚠️ |
| 2026-08-31 | **miền số** — `distance` ném `GEOMETRY_IRRATIONAL_RESULT` khi kết quả vô tỉ | ⚠️ → ✅ *(cập nhật 2026-09-02)* |

Lần vá thứ hai không được phản ánh vào ô này lúc ấy, nên nó ở lại ⚠️ thêm hai
ngày với một lý do đã hết hiệu lực. Bằng chứng cho ✅, cả ba đều kiểm lại được:

- **Audit chạy lại 2026-09-02** (`scripts/audit_geometry_capability.py`, 0 lượt
  gọi model): cả năm cặp của ô này ra số chính xác — `đường–đường CHÉO (hữu tỉ)
  = 2` · `đường–đường CHÉO (VÔ TỈ) = √2/2` · `đường–đường ∥ = 1` ·
  `đường–mặt (∥) = 1` · `mặt–mặt (∥) = 1`.
- **Mã nguồn:** `geometry/radical.py::sqrt_rational` **không có nhánh thất
  bại** — mọi `√(p/q)` với `p/q ≥ 0` viết được dưới dạng `a·√b`. Chú thích tại
  chỗ ghi thẳng: *"đó chính là lý do `GEOMETRY_IRRATIONAL_RESULT` biến mất khỏi
  đường khoảng cách"*.
- **Test khoá:** `tests/geometry/test_curriculum_coverage.py::test_khoang_cach_VO_TI_ra_CAN_THUC_khong_lam_tron`.

`GEOMETRY_IRRATIONAL_RESULT` **vẫn còn trong mã**, và giữ lại là đúng — nhưng
nay nó chỉ canh **một** ca: toạ độ khổng lồ đẩy căn thức vượt `MAX_RADICAND`.
Đó là fail-closed cho một biên hiếm, không phải một giới hạn phủ chương trình.

Khối dưới đây giữ nguyên vì nó ghi lại *vì sao* lỗ thứ nhất từng tồn tại — đọc
như **lịch sử**, không như trạng thái. Đo lại: `CAPABILITY_GAP_AUDIT.md §1`.

> ⛔ **LỊCH SỬ (trạng thái trước 2026-08-30) — không đọc như hiện tại.**

```
kernel  CÓ  distance_sq_skew_lines · distance_sq_parallel_lines
measure CHƯA nối       →  đo được: điểm–mặt · điểm–đường
                          KHÔNG   : đường–đường · đường–mặt · mặt–mặt
```

*Khoảng cách giữa hai đường thẳng chéo nhau* là dạng bài **tần suất cao** ở đề
tốt nghiệp. Kernel tính được **chính xác** rồi; chỉ thiếu một nhánh `isinstance`
trong `geometry_exec._do`. Đây là món rẻ nhất trong toàn bảng.

⚠️ **Đoạn dưới đây ĐÃ HẾT HIỆU LỰC từ 2026-08-31** — giữ lại vì nó ghi đúng
*hình dạng* của lỗ thứ hai, và vì nó cho thấy chẩn đoán lúc ấy sai ở đâu.

> Cùng chỗ ấy còn một ràng buộc **không** vá bằng code được: `distance` trả
> `GEOMETRY_IRRATIONAL_RESULT` khi kết quả vô tỉ (ví dụ điểm–điểm $(0,0,3)$ tới
> $(1,1,1)$ ra $\sqrt{6}$). Đó là **quyết định thiết kế đúng** — thà báo còn hơn
> làm tròn — nhưng nó loại mọi đề mà khoảng cách không hữu tỉ. Muốn phủ nhóm ấy
> phải cho `measure` trả **bình phương** khoảng cách, và sửa cả cách đề khai đáp án.

**Chỗ chẩn đoán ấy sai:** vấn đề chưa bao giờ là *tính được hay không* — kernel
đã tính xong — mà là **viết kết quả ra sao**. Lời giải không phải "trả bình
phương khoảng cách" (đụng cách đề khai đáp án, như đoạn trên lo) mà là **mở miền
số**: thêm `Radical` để `√6` là một câu trả lời thay vì một lời từ chối. Vẫn
không làm tròn.

---

## 4. Toán 12

| # | Chủ đề | Nghĩa vụ / cơ chế | |
|---|---|---|:-:|
| 15 | **Thể tích** khối đa diện (chóp, lăng trụ) | `volume` — `construct_solid` + `measure.volume` | ✅ |
| 16 | **Thiết diện** · bốn điểm **đồng phẳng** | `section_matches` (2026-08-30) — dựng lại từ khối + mặt phẳng rồi so CHU TRÌNH; `coplanar` vẫn nhận thiết diện nhưng không còn là thẩm quyền | ✅ |
| 16b | **Điểm thuộc mặt phẳng / đường thẳng** | `point_on_plane` · `point_on_line` | ✅ |
| 17 | Hệ toạ độ **Oxyz**: đề cho sẵn toạ độ | fact số + `point3` | ✅ |
| 18 | **Phương trình** mặt phẳng / đường thẳng / mặt cầu | — | ❌ |
| 19 | **Mặt cầu · mặt nón · mặt trụ** (khối tròn xoay) | — | ❌ |
| 20 | **Quỹ tích** điểm | — | ❌ |

**#18 — vì sao KHÔNG.** Hệ có `Plane3` là một **đối tượng**, không có *"phương
trình mặt phẳng"* là một **kết quả cần tìm**. Đề *"viết phương trình mặt phẳng
(P) đi qua A và vuông góc d"* hỏi một **biểu thức đại số**; taxonomy 8 nghĩa vụ
không có kind nào nhận nó.

**#19, #20 — prompt TỰ KHAI, và đó là hành vi đúng.**

> *"Đề cần mặt cầu, mặt nón, mặt trụ, hoặc quỹ tích — **nói thẳng là không diễn
> đạt được**. Đừng thay bằng một khối đa diện gần giống. Một mô phỏng sai hình
> còn tệ hơn không có mô phỏng: học sinh sẽ tin nó."*

Kernel dựng trên `Fraction` và đa diện; mặt cong không nằm trong mô hình. Đây
**không** phải thiếu sót cài đặt mà là **ranh giới của phương pháp** — và khai
nó ra là trung thực, không phải là yếu.

---

## 5. Nhật ký đo

### Lượt còn hiệu lực — 2026-09-02, hệ đóng băng `082da95`

`backend/scripts/audit_geometry_capability.py`, **0 lượt gọi model**, thoát `0`.

```
CẦU NỐI IR: 20/23 năng lực đi trọn tới số.

MEASURE   12/12 ✅   (gồm đường–đường CHÉO hữu tỉ = 2 · VÔ TỈ = √2/2 ·
                      đường–đường ∥ = 1 · đường–mặt ∥ = 1 · mặt–mặt ∥ = 1)
CONSTRUCT  7/10 ✅   ❌ chiếu SONG SONG · cộng/trừ vectơ · tích vô hướng
EXACT       1/1 ✅   khoảng cách VÔ TỈ (√2) → √2
CHECKER     9/9 ✅   point_on_line · point_on_plane · parallel · perpendicular ·
                      coplanar · section_matches · distance · angle · volume
```

Ba ô ❌ khớp đúng ba chủ đề chưa trọn ở §2–§4: `#5` (chiếu song song) và `#6`
(phép toán vectơ). Không có ô ❌ nào không giải thích được bằng một hàng của
bảng chủ đề, và ngược lại.

⚠️ **Một nhãn của audit dễ đọc nhầm.** Audit in `✅ góc mặt–mặt (nhị diện)`.
Nó đo **góc giữa hai mặt phẳng**, không đo **góc nhị diện có miền** — hai khái
niệm khác nhau, và đó chính là lý do `#11` vẫn là ⚠️. Đừng dùng dòng audit ấy
để nâng `#11` lên ✅.

### ⛔ Lượt cũ — HẾT HIỆU LỰC, giữ làm mốc so sánh

Bốn dòng `KHÔNG … GEOMETRY_OPERAND_TYPE` đã được nối ngày 2026-08-30, và ràng
buộc vô tỉ đã gỡ 2026-08-31.

Chạy trên `8b4025e`, không suy từ tên hàm.

```
distance   ĐƯỢC  điểm–mặt = 3   ·  điểm–đường = 3
           KHÔNG điểm–điểm (GEOMETRY_IRRATIONAL_RESULT — √6)
           KHÔNG đường–đường chéo · đường–mặt · mặt–mặt (GEOMETRY_OPERAND_TYPE)
angle      ĐƯỢC  đường–đường · mặt–mặt · đường–mặt
kernel có  distance_sq_skew_lines · distance_sq_parallel_lines  ← chưa nối
predicate  collinear · coplanar · line_in_plane · line_perpendicular_plane
           parallel_line_plane · parallel_lines · parallel_planes
IR dựng    point · line · plane · solid · section   (5, không có extrude/base)
```

---

## 6. Bốn việc, xếp theo phủ thêm được bao nhiêu / tốn bao nhiêu

| | Việc | Phủ thêm | Công |
|---|---|---|---|
| ~~1~~ | ~~Nối `distance` cho **đường–đường · đường–mặt · mặt–mặt**~~ | **XONG 2026-08-30** | — |
| ~~2~~ | ~~`measure` trả **bình phương** khoảng cách khi vô tỉ~~ | **XONG 2026-08-31 — bằng cách KHÁC**: mở miền số (`Radical`), không đổi cách khai đáp án. `#13` lên ✅ | — |
| 3 | Phép toán **vectơ** ở tầng biểu thức | **#6** trọn vẹn | thêm biểu thức, không đụng kernel |
| 4 | Góc **nhị diện** có miền | **#11** | cần khái niệm mới ở kernel |
| 5 | Chiếu **song song** theo một phương | **#5** | phép mới ở kernel |

Hai việc còn lại (3, 4) cộng thêm việc 5 là **toàn bộ** khoảng cách giữa trạng
thái hiện tại (15 trọn / 2 một phần / 4 không) và trạng thái *"trọn mọi chủ đề
đa diện"*. Ba chủ đề còn lại (`#18` phương trình · `#19` mặt cong · `#20` quỹ
tích) nằm ngoài phạm vi khoá luận có chủ đích.

**KHÔNG nên làm**: mặt cầu/nón/trụ (#19) — đổi cả nền toán từ đa diện hữu tỉ
sang mặt cong, tức viết lại kernel. Ngoài phạm vi khoá luận.

---

## 7. Điều bảng này KHÔNG nói

Nó nói **hợp đồng biểu đạt được gì**, không nói **AI sinh đúng bao nhiêu**. Hai
số ấy độc lập, và số thứ hai chỉ có ở lượt đo Phase 5 (`A = 4/10` trên tập DEV
đã bị nhìn).

Nó cũng **không** đo tần suất: chưa ai đếm mỗi chủ đề chiếm bao nhiêu phần trăm
đề thi thật. Bảng nói *"phủ 15/21 chủ đề"*, **không** được đọc thành *"làm được
71% đề thi"*.

### 7b. ⚠️ Và nó CHƯA nói rằng 21 hàng là cách chia đúng của chương trình

Tập 21 hàng ổn định từ bản đầu tiên và mỗi hàng đều có lý do — nhưng **độ mịn
của nó chưa được đối chiếu với văn bản chương trình chính thức**, và ba chỗ dưới
đây có thể đổi khi việc đối chiếu ấy được làm:

| chỗ | vấn đề | ảnh hưởng nếu sửa |
|---|---|---|
| `#12` / `#13` | "khoảng cách" bị **tách hai hàng theo đúng ranh giới cài đặt cũ** (cái nào đo được trước 2026-08-30). Nay cả hai đều ✅ nên phép tách không còn đổi phân loại, nhưng nó vẫn là một phép tách **theo năng lực**, không theo chương trình | gộp ⇒ tổng 20, trọn 14 |
| `#16b` | "điểm thuộc mặt phẳng / đường thẳng" chồng ngữ nghĩa với `#1` (đại cương, quan hệ liên thuộc), lại xếp nhầm vào §4 Toán 12. Số hiệu `b` cho thấy nó được thêm sau, và nó tồn tại vì **có checker**, không vì nó là một chủ đề riêng | gộp vào `#1` ⇒ tổng 20, trọn 14 |
| `#18`, `#19` | mỗi hàng **gộp ba khái niệm** (phương trình mặt phẳng/đường thẳng/mặt cầu; mặt cầu/nón/trụ), trong khi các hàng khác chỉ mang một | tách ⇒ tổng tăng tới 25, *không* làm trọn tăng |

Ba chỗ này kéo tổng theo **hai chiều ngược nhau**, nên không thể đoán kết quả
ròng. Quy tắc đã áp: **không tự chia lại khung** khi chưa có văn bản chương
trình — một con số đúng theo khung tự đặt vẫn là một con số không truy nguồn
được. Xem `## Nguồn` ở cuối file.

⇒ Cách phát biểu an toàn, và là cách khoá luận đang dùng: *"trên khung 21 chủ đề
mà tài liệu này khảo sát, hệ diễn đạt trọn 15"* — nêu khung cùng với số, đừng
nêu số một mình.

---

## Nguồn

### ⚠️ `CURRICULUM_SOURCE_VERIFICATION = NEEDS_EXTERNAL_SOURCE`

Năm liên kết dưới đây đều là **tài liệu thứ cấp** — trang ôn thi và tài liệu dạy
thêm. Không cái nào là **văn bản chương trình gốc**. Header của file từng ghi
*"Nguồn chương trình: GDPT 2018 môn Toán — xem §6"*, nhưng §6 là bảng việc cần
làm, không phải mục nguồn — con trỏ ấy trỏ vào chỗ trống, và đã sửa.

Hệ quả: **danh sách 21 chủ đề là một khung làm việc, chưa phải một khung có
thẩm quyền.** Nó đủ tốt để đo và để so sánh nội bộ; nó **chưa** đủ để in vào
khoá luận như một tuyên bố về chương trình phổ thông mà không nêu rõ khung.

**Cần bổ sung ở bước `LITERATURE_AND_CITATION_COMPLETION`** (tra cứu ngoài repo,
KHÔNG làm trong wave này — xem `docs/THESIS_REFERENCE_NEEDS.md §16`):

- văn bản Chương trình giáo dục phổ thông môn Toán do Bộ GD&ĐT ban hành năm
  2018 — **tên đầy đủ, cơ quan ban hành, năm, số hiệu thông tư**, và mục/phần
  dùng để hình thành danh sách chủ đề;
- sách giáo khoa Toán 11 và Toán 12 hiện hành (nêu rõ bộ sách), để chốt độ mịn
  của ba chỗ nêu ở §7b.

⛔ **Không đoán số hiệu văn bản.** Cho tới khi có bản gốc, mọi phát biểu về phủ
chương trình phải **nêu kèm khung** (*"trên khung 21 chủ đề mà tài liệu này khảo
sát…"*), không được nêu con số trần.

### Tài liệu thứ cấp đang dùng

- [Chuyên đề Quan hệ vuông góc trong không gian — Toán 11 KNTT (VietJack)](https://www.vietjack.com/toan-lop-11/quan-he-vuong-goc-trong-khong-gian-kntt.jsp)
- [Tài liệu ôn thi tốt nghiệp THPT môn Toán theo GDPT 2018 (TOANMATH)](https://toanmath.com/2025/04/tai-lieu-on-thi-tot-nghiep-thpt-mon-toan-theo-chuong-trinh-gdpt-2018.html)
- [Lý thuyết chương Mặt nón · mặt trụ · mặt cầu — Toán 12 (VietJack)](https://vietjack.com/toan-lop-12/tong-hop-ly-thuyet-chuong-mat-non-mat-tru-mat-cau.jsp)
- [Chuyên đề hình học không gian ôn thi tốt nghiệp THPT 2025 (Thư Viện Học Liệu)](https://thuvienhoclieu.com/chuyen-de-hinh-hoc-khong-gian-on-thi-tot-nghiep-thpt-giai-chi-tiet/)
- [Lời giải chi tiết đề thi Toán tốt nghiệp THPT 2025 chính thức (MathVN)](https://www.mathvn.com/2025/07/loi-giai-chi-tiet-e-thi-toan-tot-nghiep.html)
