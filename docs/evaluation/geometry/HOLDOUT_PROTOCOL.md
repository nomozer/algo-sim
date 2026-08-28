# HELD-OUT HÌNH HỌC — giao thức (N = 20)

> Trả lời câu *"hệ làm được với bài **chưa từng thấy** không?"*. Tập DEV **không**
> trả lời được câu đó: nó đã bị nhìn, và hệ đã được sửa theo nó qua bốn wave.

---

## 0. Vấn đề cốt lõi, và vì sao nó không tự giải được

**Tôi không thể tự tạo một tập held-out.** Bất kỳ đề nào tôi viết ra, tôi đã
nhìn — và mọi bản vá sau đó đều có thể vô tình nhắm vào nó. Tập DEV hiện tại
chính là ví dụ: 10 bài tôi viết, rồi bốn wave sửa hệ theo đúng chỗ chúng hỏng.

Nên giao thức này đặt trên một nguyên tắc khác: **đề và đáp án đều phải đến từ
NGOÀI hệ thống và NGOÀI tôi.**

---

## 1. Nguồn: đề thi công khai, KHÔNG phải đề tôi soạn

| | Đề tôi soạn | **Đề thi công khai** |
|---|---|---|
| Ai viết đề | tôi | Bộ GD-ĐT / sở / trường |
| Ai tính đáp án | tôi | **đáp án chính thức** |
| Tôi đã nhìn trước chưa | rồi | rồi — nhưng **không sửa được đề** |
| Đại diện chương trình | tự nhận | **có căn cứ** |

Điểm mạnh không nằm ở chỗ *"tôi chưa nhìn"* — mà ở chỗ **tôi không viết được ra
chúng, và không sửa được đáp án**. Một đề tôi tự soạn có thể vô thức né đúng
những chỗ hệ yếu; một câu trong đề tốt nghiệp thì không.

**Nguồn dùng**: §8.

---

## 2. Bốn bảo đảm, và cái nào máy giữ

| | Bảo đảm | Ai giữ |
|---|---|---|
| ① | 20 ô đích danh, phủ đủ **tám** nghĩa vụ hình học | `seal_geometry_holdout.BANG_O` + `test_holdout_protocol` |
| ② | Đáp án đến từ **nguồn ngoài**, tra ngược được | `kiem_pool` — thiếu `nguon.url` là dừng |
| ③ | Không bài nào **trùng tập DEV** | `kiem_pool` — so đề đã chuẩn hoá |
| ④ | Hệ **không đổi** giữa niêm phong và chạy | `run_geometry_dev_evaluation --holdout` |

⚠️ Ba trong bốn cái trên **không kiểm lại được sau khi chạy**. Nên chúng phải đỏ
được từ trước — đó là lý do chúng nằm trong test chứ không nằm trong đoạn văn này.

**Ngoài ra, hai luật không máy nào giữ hộ được:**

**Niêm phong TRƯỚC khi chạy.** Băm nội dung tập đã chọn, commit con dấu, rồi mới
chạy. Không có con dấu trong lịch sử thì không có cách nào chứng minh tập không
bị sửa sau khi thấy kết quả.

**Chạy MỘT PHIÊN.** Trượt thì ghi nhận là trượt. Sửa hệ rồi chạy lại trên cùng
tập held-out thì tập ấy **thành DEV** — và phải nói ra điều đó, không được im.

> ### ⚠️ "MỘT LƯỢT" nghĩa là gì — làm rõ 2026-08-27 (Phase 7A.3)
>
> Bản trước viết *"chạy MỘT LƯỢT"*, và câu ấy đọc được theo hai nghĩa. Nghĩa
> đúng là nghĩa hẹp:
>
> | | |
> |---|---|
> | ✅ **CÓ** nghĩa là | **một PHIÊN ĐO đã niêm phong**, gồm `k` lượt độc lập cho mỗi bài, **không sửa hệ giữa các lượt**, **không chọn lượt đẹp nhất** |
> | ❌ **KHÔNG** có nghĩa là | chạy đúng một lần cho mỗi bài rồi kết luận |
>
> Điều luật này cấm là **lặp CÓ SỬA**: chạy → thấy trượt → sửa hệ → chạy lại
> trên cùng tập. Đó là thứ biến held-out thành DEV. `k` lượt **trong cùng một
> phiên**, cùng một `measured_system_hash`, không đụng gì ở giữa, **không** vi
> phạm điều ấy — chúng là `k` phép lấy mẫu của **một** phép đo.
>
> **Vì sao phải làm rõ, chứ không phải nới lỏng:** `PHASE7_METRIC_CONTRACT §2⑤`
> đòi `k ≥ 3` cho chỉ số `stability`, và §4 **cấm** báo pass/fail cho một đề
> chạy `k` lượt. Đọc *"một lượt"* theo nghĩa rộng thì hai tài liệu chống nhau và
> một trong hai phải bị phá — trong khi thật ra chúng nói về hai chuyện khác
> nhau: cái này về **lặp lại sau khi thấy kết quả**, cái kia về **cỡ mẫu**.
>
> Bằng chứng cho thấy `k = 1` không đủ, đo được trên chính kho này: Phase 6.6
> cùng mã cùng đề cho **0/3 rồi 3/3**; Phase 7A bài `5-goc` qua ở lượt 1 và 3,
> trượt ở lượt 2 vì `analyze` không tất định. Lượt trượt ấy, nếu là lượt **duy
> nhất**, sẽ vào luận văn thành *"mô hình không làm được"* — và nó không đúng.
>
> Chốt `k`: **`HOLDOUT_K_FINAL.md`**. Phân tích ba phương án:
> `HOLDOUT_K_DECISION.md`.

---

## 2b. ĐIỀU KIỆN NHẬN BÀI VÀO TẦNG A — thêm 2026-08-27 (Phase 7A.5)

Một bài chỉ được vào **tầng A** khi thoả **cả ba**:

| | Điều kiện | Kiểm ở đâu |
|---|---|---|
| **1** | **Thuộc ranh giới năng lực** | [`CAPABILITY_BOUNDARY.md`](CAPABILITY_BOUNDARY.md) §1, và điều kiện miền của đúng ô ở [`COVERAGE_MATRIX_BOUNDARY_REVIEW.md`](COVERAGE_MATRIX_BOUNDARY_REVIEW.md) |
| **2** | **Oracle biểu diễn được trong kernel** | `distance` phải **hữu tỉ** · `angle` khai `cos²` (đường–đường, mặt–mặt) hoặc **`sin²`** (đường–mặt) · `volume` phân số · quan hệ true/false |
| **3** | **Có expectation độc lập** | một mục trong `expectations/holdout.json`, `nguoi_danh_gia.loai ≠ nguoi_do`, mỗi nghĩa vụ có `ly_do` trích từ đề |

### Bài NGOÀI ranh giới thì làm gì

- **KHÔNG** đưa vào tầng A. Một ô mà hệ **không thể** phục vụ là một ô **chắc
  chắn trượt**, và cái trượt ấy sẽ vào báo cáo như *"mô hình không làm được"* —
  trong khi mô hình có thể đã dựng hình đúng hoàn toàn.
- Được phép: **loại khỏi pool** (`status: rejected_capability_boundary`, kèm
  `reason` và giữ `nguon.url`), hoặc để dành cho một **nghiên cứu riêng về hành
  vi từ chối** sau Phase 7B.

### ⛔ KHÔNG tự chuyển bài khó xuống tầng B

Sáu ô `B*` là **sáu loại đích danh** đã khai từ đầu (chéo nhau · đường∥mặt ·
nhị diện · Oxyz · mặt cong · vectơ). Nhét một bài A11 vô tỉ vào đó là **đổi
thiết kế tập đo** — `N`, ngân sách và `HOLDOUT_K_FINAL` đổi theo.

Muốn mở một ô tầng B cho lớp *"đáp án vô tỉ"* thì phải **sửa giao thức trước**,
và phải do người duyệt quyết, **trước khi niêm phong**. Làm ngược lại — rút
xong rồi mới đổi ô — là chọn tập sau khi đã thấy nó.

### Và một luật đọc, cho lúc báo cáo

Bài ngoài ranh giới mà lọt vào tầng A thì lượt trượt của nó **không thuộc bốn
nhóm** taxonomy (`PHASE7_METRIC_CONTRACT §3`): nó không phải lỗi sinh, không
phải hợp đồng thiếu diễn đạt, không phải validator sai, không phải định tuyến.
Ghi nhãn **`out_of_capability`** trong `FAILURE_LOG.md` và nêu riêng — cùng luật
đã áp cho lỗi hạ tầng.

---

## 3. Hai mươi ô — đa dạng do THIẾT KẾ, không do may rủi của seed

Bản trước rút `70% / 30%` từ hai rổ. **Tỉ lệ không bảo đảm đa dạng**: 14 bài
"trong phủ" hoàn toàn có thể ra 14 bài thể tích, và điểm cao ấy không nói được gì.

Nên tập khai **20 ô đích danh**, mỗi ô một loại hình học. Seed quyết định *bài
nào trong ô*, **không** quyết định *ô nào có mặt*.

### Tầng A — trong phủ hợp đồng (14 ô) · chấm **A · O · obligation_match**

| Ô | Loại hình học | Nghĩa vụ |
|---|---|---|
| A01 | Giao tuyến hai mặt phẳng — điểm thuộc giao tuyến | `point_on_line` |
| A02 | Điểm thuộc mặt phẳng | `point_on_plane` |
| A03 | Hai đường thẳng song song | `parallel` |
| A04 | Đường thẳng song song mặt phẳng | `parallel` |
| A05 | Hai mặt phẳng song song | `parallel` |
| A06 | Hai đường thẳng vuông góc | `perpendicular` |
| A07 | Đường thẳng vuông góc mặt phẳng | `perpendicular` |
| A08 | Hai mặt phẳng vuông góc | `perpendicular` |
| A09 | Góc giữa hai đường thẳng | `angle` |
| A10 | Góc giữa đường thẳng và mặt phẳng | `angle` |
| A11 | Khoảng cách từ điểm đến mặt phẳng | `distance` |
| A12 | Khoảng cách từ điểm đến đường thẳng | `distance` |
| A13 | Thiết diện / bốn điểm đồng phẳng | `coplanar` |
| A14 | Thể tích khối chóp hoặc lăng trụ | `volume` |

`parallel` và `perpendicular` mỗi loại **ba ô** vì chúng có ba biến thể
đường–đường, đường–mặt, mặt–mặt — đó là **ba bài toán khác nhau**, không phải
một bài lặp ba lần. Tập nghĩa vụ của tầng A **dẫn** từ
`geometry_obligation_kinds()`; thêm một nghĩa vụ hình học vào taxonomy mà quên mở
ô cho nó thì test đỏ.

### Tầng B — ngoài / một phần phủ (6 ô) · chấm **DUY NHẤT: từ chối trung thực?**

| Ô | Loại hình học | Vì sao ngoài phủ |
|---|---|---|
| B01 | Khoảng cách **hai đường chéo nhau** | `measure` chưa nối cặp đường–đường (coverage #13) |
| B02 | Khoảng cách đường ∥ mặt, mặt ∥ mặt | như trên |
| B03 | **Góc nhị diện** có miền | `cos_sq_between_planes` luôn thuộc [0°,90°] (#11) |
| B04 | Oxyz: **phương trình** mặt phẳng / đường / mặt cầu | taxonomy không có kind nhận biểu thức đại số (#18) |
| B05 | **Mặt cầu · nón · trụ** | kernel dựng trên `Fraction` + đa diện (#19) |
| B06 | Phép toán **vectơ**, hoặc phép chiếu song song | không có phép vectơ ở tầng biểu thức (#6, #5) |

⚠️ **Sáu ô này không phải để lấy điểm.** Chúng kiểm: gặp đề ngoài khả năng, hệ
**nói thẳng là không diễn đạt được** hay **bịa ra một hình gần giống**? Prompt đã
dặn phải nói thẳng; đây là chỗ kiểm lời dặn ấy có tác dụng không.

**B03 là ô khó nhất và quan trọng nhất.** Hệ *tính được* góc giữa hai mặt phẳng —
một đại lượng **khác** góc nhị diện. "Từ chối trung thực" ở đây nghĩa là **không
được lặng lẽ trả lời câu hỏi nhị diện bằng góc mặt–mặt**. Một mô phỏng sai hình
còn tệ hơn không có mô phỏng: học sinh sẽ tin nó.

```
tầng A (14)   chấm A · O · obligation_match
tầng B  (6)   chấm nhị phân: TỪ CHỐI TRUNG THỰC  |  BỊA HÌNH
```

Hai thang **không được gộp** thành một cột.

---

## 4. Oracle độc lập — ba trường, và vì sao phải ba

Đáp án chính thức viết `a√3/3`; checker so **phân số**. Nên "chép đáp án vào" là
không đủ — phải có một phép đổi đơn vị, và phép đổi ấy là chỗ **duy nhất** người
soạn được phép tính. Giấu nó đi thì *"oracle độc lập"* chỉ còn là lời khai.

| Trường | Nội dung | Ai tạo |
|---|---|---|
| `dap_an_chinh_thuc` | **nguyên văn** đáp án nguồn | nguồn ngoài |
| `phep_chuyen` | cách đổi sang đơn vị checker, kèm giá trị gán cho cạnh | người soạn — **hiện ra để kiểm lại** |
| `oracle_result` | đơn vị checker: phân số · cos² · true/false | dẫn từ hai dòng trên |

Cộng `chua_chay_he: true` khai tại thời điểm soạn — **soạn đáp án sau khi thấy hệ
chạy là chép bài của chính mình**, đúng lỗi mà `dev/cases.json` đã ghi ra để tránh.

Khuôn đầy đủ: [`holdout/pool.template.json`](holdout/pool.template.json).

---

## 5. Quy trình

```
① SOẠN POOL          ≥40 bài, phủ ĐỦ 20/20 ô, trích từ nguồn công khai
                      holdout/pool.json   — CÓ đề, CÓ đáp án chính thức, CÓ url
                      chưa chạy hệ trên bất kỳ bài nào
                      kiểm: seal_geometry_holdout.py --seed 0 --chi-kiem-pool

② GVHD CHO SEED      một số nguyên. KHÔNG do tôi chọn — nếu tôi chọn seed
                      thì tôi chọn được cả tập (chạy thử vài seed rồi lấy
                      cái cho điểm đẹp nhất)

③ RÚT TẤT ĐỊNH       seed → một bài cho MỖI ô. Ô thiếu bài ⇒ DỪNG, KHÔNG
                      rút bù từ ô khác
                      seal_geometry_holdout.py --seed <SỐ>

④ NIÊM PHONG         seal_hash + measured_system_hash → HOLDOUT_SEAL.json
                      → COMMIT.  Cây phải SẠCH, freeze --verify PASS

⑤ CHẠY MỘT PHIÊN     run_geometry_dev_evaluation.py --holdout
                      k = 3 lượt ĐỘC LẬP mỗi bài, trong CÙNG một phiên
                      runner đối chiếu CẢ HAI băm trước khi tiêu call đầu tiên
                      không sửa prompt, không bỏ bài, không retry riêng,
                      không chọn lượt đẹp nhất

⑥ BÁO CÁO            tầng A: G1 · G2 · A · O · construction_match ·
                              verification_match · stability (x/k)
                      tầng B: từ chối trung thực / bịa hình
                      cộng: taxonomy nguyên nhân trượt
```

**Ngân sách** — `k = 3`, chốt ở `HOLDOUT_K_FINAL.md`:

```
mỗi lượt/bài   6 logic · 8 HTTP      dẫn từ call graph:
                                     analyze ≤2 · semantic_analyze 1
                                     · semantic_program ≤3

logic   20 bài × 3 lượt × 6 logic  =  360
HTTP    20 bài × 3 lượt × 8 HTTP   =  480
```

**Hằng số mỗi lượt KHÔNG đổi một đơn vị** kể từ trần đã duyệt cho DEV (60/80 ở
N=10, `k=1`) — vẫn đúng `6 × N × k`. Cái đổi là **`k`**, và chỉ nó. Bảng dưới để
so, và để thấy phần tăng đến từ đâu:

| | N | k | logic | HTTP |
|---|--:|--:|--:|--:|
| DEV (đã duyệt) | 10 | 1 | 60 | 80 |
| Held-out, bản trước (`k=1`) | 20 | 1 | 120 | 160 |
| **Held-out, chốt (`k=3`)** | 20 | **3** | **360** | **480** |

---

## 6. "Không sửa hợp đồng theo từng bài" — biến lời hứa thành cổng

Đây là chỗ dễ trượt nhất, và trượt một cách hoàn toàn thiện chí: chạy tới bài
thứ 7, thấy nó hỏng vì một trường IR khó dùng, sửa trường ấy, chạy tiếp. Kết quả
vẫn mang nhãn "held-out" nhưng đã không còn là held-out.

Nên con dấu ghi **băm mã sản phẩm** (`measured_system_hash`, mượn đúng hàm của
cổng đóng băng để hai con số không bao giờ trôi khỏi nhau), và runner **từ chối
chạy** nếu băm hiện tại khác. Lối thoát duy nhất là **niêm phong lại** — tức khai
ra rằng đây là lượt khác, trên một hệ khác.

---

## 7. Điều giao thức này KHÔNG bảo đảm

- **Không phải blind thật.** Tôi soạn pool nên tôi đã đọc mọi đề trong đó. Bảo
  đảm thật là *"tôi không viết ra đề và không sửa được đáp án"*, yếu hơn *"tôi
  chưa từng thấy"*. Phải khai đúng mức ấy khi báo số.
- **N = 20 đủ để chia, chưa đủ để tin khoảng tin cậy.**
  `RELIABILITY_EVALUATION_PLAN §3.3` cấm chia khi mẫu < 20; N=20 vừa chạm ngưỡng,
  nên tỉ lệ đọc được nhưng **khoảng tin cậy vẫn rất rộng** (một bài đổi chiều là
  ±5 điểm phần trăm). Và tầng A chỉ có 14 bài — mẫu số của A/O là **14**, không
  phải 20.
- **Không đo tần suất chương trình.** Chưa ai đếm mỗi chủ đề chiếm bao nhiêu
  phần trăm đề thi thật, nên tập này *đại diện chủ đề*, không *đại diện tần suất*.
- **Một bài mỗi ô vẫn không tách được ô khỏi bài.** Bài A11 trượt cả 3 lượt
  không phân biệt được *"hệ không làm được khoảng cách điểm–mặt"* với *"bài A11
  ấy có gì đó lạ"*.

  ⚠️ Từ `k = 3` (Phase 7A.3), hạn chế này **thu hẹp lại chứ không mất**. Cái
  `k` mua được là **phương sai GIỮA CÁC LƯỢT trên cùng một bài** — phân biệt
  được *"hệ không làm được"* (0/3) với *"hệ làm được, không ổn định"* (2/3).
  Cái `k` **không** mua được là phương sai **giữa các bài trong cùng một ô**:
  muốn thứ đó phải rút nhiều bài mỗi ô, tức một tập khác. Đừng đọc `2/3` thành
  *"ô A11 đạt 67%"* — nó là *"bài A11 ấy đạt 2/3 lượt"*.

---

## 8. Trạng thái

```
BANG_O (20 ô)      XONG     seal_geometry_holdout.BANG_O
kiem_pool          XONG     4 bảo đảm, 25 test khoá
cổng con dấu       XONG     --holdout, đối chiếu seal_hash + measured_system_hash
khuôn pool         XONG     holdout/pool.template.json
─────────────────────────────────────────────────────────────────
pool.json          CHƯA CÓ  — cần ≥40 bài trích từ nguồn ngoài
seed từ GVHD       CHƯA CÓ  — CHẶN CỨNG bước ③
HOLDOUT_SEAL.json  CHƯA CÓ
```

**Chặn cứng ở seed.** Không có seed của người ngoài thì bước rút không có tính
độc lập, và cả giao thức tụt xuống thành *"tôi chọn 20 bài tôi thích"*.

---

## 9. Nguồn đề

- [Lời giải chi tiết đề thi Toán tốt nghiệp THPT 2025 chính thức (MathVN)](https://www.mathvn.com/2025/07/loi-giai-chi-tiet-e-thi-toan-tot-nghiep.html)
- [Đề minh hoạ môn Toán kì thi tốt nghiệp THPT từ 2025 — đề tham khảo và đáp án](https://cmcu.edu.vn/de-minh-hoa-mon-toan-ki-thi-tot-nghiep-thpt-tu-nam-2025-de-tham-khao-va-dap-an/)
- [Chuyên đề hình học không gian ôn thi tốt nghiệp THPT 2025, giải chi tiết (Thư Viện Học Liệu)](https://thuvienhoclieu.com/chuyen-de-hinh-hoc-khong-gian-on-thi-tot-nghiep-thpt-giai-chi-tiet/)
- [Chuyên đề hình học không gian ôn thi tốt nghiệp THPT (HOCMAI)](https://hocmai.vn/kho-tai-lieu/read.php?id=17710)
- [100 bài tập Toán 11 chương Quan hệ vuông góc, có đáp án (VietJack)](https://vietjack.com/toan-11-ct/trac-nghiem-chuong-8-quan-he-vuong-goc-trong-khong-gian.jsp)

---

## PROTOCOL_AMENDMENT_PRESEAL — 2026-08-28

Thay yêu cầu **"người chép tự gõ nguyên văn toàn bộ đề"** bằng
**chép máy từ nguồn đã dẫn + xác minh của người theo rủi ro**.

> **Lý do**: giảm công cơ học mà **không** đổi xuất xứ, tính độc lập của
> oracle, tính bất biến trước niêm phong, hay các cơ chế chống nhiễm.

Ghi ở đây **trước** khi niêm phong, đúng lệ khai sai lệch tiền đăng ký.

### Cái gì đổi, cái gì KHÔNG

| | Trước | Sau |
|---|---|---|
| `problem_text` | người gõ 100% | **máy chép** từ nguồn đã dẫn |
| Xác minh | ngầm định qua hành vi gõ | **tường minh, theo rủi ro** |
| Chữ ký | mỗi lô một lần | một lần, kèm **cam kết** nói rõ đã kiểm gì |

**KHÔNG đổi** — ba bảo đảm thật của tính held-out:
① đề đến từ **nguồn công khai có trích dẫn**;
② **đáp án là của nguồn**, không do người soạn tính;
③ tập đo **đóng băng và băm** trước khi model chạy.

### Vì sao "gõ tay" không phải bảo đảm

Nó bảo đảm **chống chép sai**, không bảo đảm **chống nhiễm**. Chống nhiễm nằm ở
① ② ③. Đổi lại, chống chép sai nay do **kiểm theo rủi ro** đảm nhiệm — mạnh hơn
ở chỗ nó **nhắm đúng** những bài dễ sai, thay vì rải đều công sức lên 42 bài.

### Chép máy nghĩa là gì ở đây

⚠️ **KHÔNG phải trích text PDF.** Đo trong kho: trích text các tài liệu này cho
`⊥` 204 lần nhưng `√` **0 lần** — mọi bài vô tỉ hiện ra như hữu tỉ (§7g của
`HOLDOUT_ACQUISITION_LOG`). Chép máy ở đây là **dựng ảnh trang rồi đọc**, hoặc
HTML hiển thị đủ ký hiệu. Chỗ máy không đọc chắc thì để trống và gắn `HIGH`.

### Ba mức rủi ro và nghĩa vụ kiểm

| Mức | Khi nào | Người phải làm |
|---|---|---|
| `HIGH` | có `√` · phân số phức · dấu phẩy trên · nguồn từng nghi ngờ · trích dẫn không tra ra · công thức là ảnh · tên điểm từng bị rơi | **mở nguồn đối chiếu 100%** |
| `MEDIUM` | có số liệu, ký hiệu mặt phẳng, chỉ số dưới | nằm trong **mẫu QC** |
| `LOW` | HTML sạch, bài chứng minh, không số liệu | nằm trong **mẫu QC** |

**Mẫu QC**: toàn bộ `HIGH` + khoảng **20%** số khối `LOW`/`MEDIUM`, tối thiểu 8
khối. Phát hiện một lỗi chép trong mẫu ⇒ **mở rộng** sang cả họ nguồn của nó.

### Câu duy nhất được viết trong báo cáo

> *"Tập held-out được chép máy từ các nguồn đã trích dẫn. Các trường hợp rủi ro
> cao và một mẫu kiểm chất lượng đã được đối chiếu độc lập với trang nguồn
> trước khi niêm phong."*

❌ **Không được viết** *"42/42 do người kiểm"* nếu thực tế không phải vậy.
