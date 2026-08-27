# CHÍNH SÁCH NGUỒN CHO TẬP HELD-OUT

> Luật nhận/loại **nguồn** (tài liệu), khác `CAPABILITY_BOUNDARY` (luật nhận/loại
> **bài**). Một nguồn hợp lệ vẫn đầy bài không hợp lệ, và ngược lại thì không —
> bài từ nguồn không hợp lệ **không bao giờ** vào tập, dù bài ấy hoàn hảo.
>
> Mọi con số dưới đây **đo được**, không phỏng đoán. Nguồn của từng con số:
> `HOLDOUT_ACQUISITION_LOG.md`, `SOURCE_CANDIDATE_REPORT.md`.

---

## 1. Vì sao MỞ RỘNG nguồn

Ban đầu giao thức chỉ nhận **đề thi công khai có đáp án chính thức**
(`HOLDOUT_PROTOCOL §1`), vì lập luận: *"tôi không viết được ra chúng và không
sửa được đáp án"*.

Bốn lượt thu thập cho thấy ràng buộc ấy **quá hẹp so với thứ nó bảo vệ**:

| | Đo được | Hệ quả |
|---|---|---|
| Đề thi THPT sau 2025 | **92%** là trắc nghiệm 4 phương án | hệ **không "chọn phương án"** ⇒ lệch kiểu nhiệm vụ |
| 1154 url mathvn | 26 câu hình học không gian · **0** tự luận trong ranh giới | nguồn dễ lấy nhất là nguồn ít khớp nhất |

Thứ giao thức thật sự bảo vệ là **hai điều**:

1. **Người đo không viết ra đề** — chống việc vô thức né đúng chỗ hệ yếu.
2. **Người đo không sửa được đáp án** — chống oracle tự phong.

**SGK, sách bài tập, sách chuyên đề, đề HSG** thoả **cả hai** y hệt đề thi, và
lại **giàu bài tự luận**. Nên mở rộng sang chúng **không nới lỏng** bảo đảm nào
— nó chỉ bỏ một ràng buộc phụ (*"phải là đề thi"*) vốn không phục vụ mục đích.

---

## 2. Nguồn HỢP LỆ

| Loại | Điều kiện | Tra ngược bằng |
|---|---|---|
| **SGK Toán 11/12** | bản in hoặc PDF chính thức | tên sách · bộ · tập · bài · trang |
| **Sách bài tập** | đi kèm SGK | như trên |
| **Sách chuyên đề** | có tác giả, có lời giải | tên tài liệu · tác giả · trang · câu |
| **Đề thi / đề minh hoạ** | công khai, có đáp án chính thức | mã đề · câu · năm · url |
| **Đề HSG** | có đáp án của ban tổ chức | kỳ thi · năm · câu |
| **Giáo trình đại học nhập môn hình học** | có lời giải hoặc đáp số | tên · tác giả · trang |

**Điều kiện chung, không có ngoại lệ:**

1. **Đáp án đến từ nguồn**, không do người soạn tính. Phép **duy nhất** người
   soạn được làm là gán tham số (`a = 1`) và ghi vào `phep_chuyen`.
2. **Tra ngược được** — đủ thông tin để người khác mở đúng chỗ ấy.
3. **Đề tự luận**, có mệnh lệnh dựng hoặc tính.
4. **Người đọc trực tiếp nguồn và chép** — xem §4.

---

## 3. Nguồn KHÔNG hợp lệ — kèm lý do đo được

| Nguồn | Vì sao loại | Bằng chứng |
|---|---|---|
| **Blog lời giải không kèm đề** | không có `problem_text` để chép | trang giải SGK viết thẳng lời giải vì người đọc đã có sách; 269 url → 4 sạch |
| **OCR / trích PDF tự động** | **rơi ký hiệu toán, IM LẶNG** | `⊥` **0 lần** trong chuyên đề 217 trang *về quan hệ vuông góc*; `√` 0 · `∈` 0 · `∥` 0 · `=` 1303. Hai thư viện độc lập cùng kết quả |
| **AI đọc lại / tóm tắt** | thêm một bước diễn giải ⇒ mất thông tin | công cụ đọc web trả nội dung qua một mô hình tóm tắt |
| **Bài AI sinh** | không tra ngược được; người đo thành người soạn đề | — |
| **Đề không nêu nguồn** | oracle không tra lại được ⇒ *"một con số ai đó gõ vào"* | `kiem_pool` chặn thiếu `nguon.url` |
| **Đề tham chiếu hình vẽ** không có trong văn bản | thiếu dữ kiện | tr 46 · Câu 4: *"(tham khảo hình vẽ)"* |

### ⛔ NGUYÊN NHÂN GỐC — tài liệu toán Việt soạn bằng MathType

Ba lượt trước kết luận riêng lẻ: *"PDF rơi ký hiệu"*, *"web là ảnh"*, *"trang
SGK không chép đề"*. Lượt bốn tìm ra **một nguyên nhân chung**.

Tải bản **`.docx`** của *Chuyên đề hình học không gian 11* (thuvienhoclieu,
9,2 MB) — giả thuyết: Word giữ toán dạng OMML nên trích được. **Sai**, và cách
nó sai giải thích luôn ba lượt trước:

| Nội dung `.docx` | |
|---|--:|
| `word/embeddings/*.bin` — **OLE MathType** | **2281** file · 7,3 MB |
| `word/media/*.wmf` — ảnh render của từng công thức | **2236** file · 1,8 MB |
| `m:rad` · `m:f` · `m:sup` (OMML thật) | **0** |
| `⊥` · `√` · `∈` · `°` trong dòng văn bản | **0** |

Văn bản trích ra có lỗ đúng chỗ công thức:

```
"Cho hình chóp ⟨lỗ⟩, đáy ⟨lỗ⟩ có …"      ← S.ABCD và ABCD là OLE, không phải chữ
```

> **Tài liệu toán phổ thông Việt Nam gần như đều soạn bằng MathType**, và
> MathType nhúng mỗi công thức thành **một đối tượng OLE kèm ảnh WMF**. Nên:
>
> - **PDF** — in ra từ Word ấy ⇒ công thức thành glyph không ánh xạ Unicode;
> - **Word** — công thức **chưa bao giờ** là chữ;
> - **Web** — xuất từ Word ấy ⇒ công thức thành `<img>`.
>
> Ba triệu chứng, **một nguyên nhân**. Đây là lý do không kênh tự động nào
> chạm tới được, và cũng là lý do **đổi định dạng không giúp gì** — vấn đề nằm
> ở khâu **soạn thảo**, không ở khâu phân phối.

Hệ quả cho chính sách: **không tiếp tục thử định dạng mới** (`.doc`, `.tex`,
`.epub`…). Việc ấy đã đủ bằng chứng để dừng. Người đọc màn hình rồi gõ lại là
đường duy nhất, và nó **không phải giới hạn kỹ thuật của repo** mà là tính chất
của kho tài liệu.

### ⛔ Vì sao trích PDF bị loại dù đọc ra chữ tiếng Việt

Không phải vì văn bản khó đọc — mà vì nó **hỏng đúng chỗ quyết định**:

```
NGUỒN (đọc bằng mắt)   AC = a√3          AC = 2a
TRÍCH TỰ ĐỘNG          "3 AC a ="        "2 AC a ="
```

Hai thứ ra **cùng một dạng**. `a√3` **ngoài** ranh giới, `2a` **trong** — và bản
trích khiến cái ngoài trông như cái trong. Đây là hỏng theo hướng **NHẬN NHẦM**,
nguy hiểm hơn hẳn hỏng theo hướng bỏ sót: một đề ngoài phủ lọt vào tập niêm
phong, hệ trượt nó, và cái trượt ấy vào luận văn thành *"mô hình không làm
được"*.

---

## 4. Quy trình xác minh — ba bước, không rút gọn

```
① NGƯỜI mở nguồn gốc  →  ② đọc trực tiếp  →  ③ gõ lại nguyên văn
```

Hành vi ở ③ **chính là** bước xác minh. Nó được ghi lại bằng dòng:

```
NGƯỜI CHÉP: <tên> · <ngày> · <chép từ đâu>
```

`ingest_holdout_batch.py` **từ chối cả lô** khi thiếu dòng ấy, hoặc khi nó còn
chỗ trống `<…>`. Trường `human_verifier` trong `pool.json` lưu tên ấy, và
`kiem_pool` **ĐỎ** nếu `problem_text_verified: true` mà không có người đứng tên
— *chữ ký không có người ký thì không phải chữ ký*.

### Ai KHÔNG được ký

**Agent không được tự điền `NGƯỜI CHÉP`.** Không phải quy ước hình thức: mọi
kênh máy đọc đã **đo được** là hỏng im lặng ở đúng ký hiệu quyết định tư cách
bài. Một chữ ký do máy tự ký sẽ chứng nhận cho thứ chính nó biết là không đáng
tin. `test_bo_nap_KHONG_tu_viet_dong_NGUOI_CHEP` khoá điều này.

### Bản nháp do máy đọc

Được phép **tồn tại** để đối chiếu, **không** được dùng làm nguồn chép — và khi
dùng để đối chiếu thì phải **chép sang file khác**, vì soát một bản có sẵn dễ
lướt hơn gõ lại, mà chỗ sai nằm đúng ký hiệu quyết định.

---

## 5. Chọn BÀI trong một nguồn hợp lệ

Nguồn hợp lệ **không** bảo đảm bài hợp lệ. Tỉ lệ đo được: **≈ 2/11**.

> **Luật đủ, và là luật duy nhất đủ:**
> **"Đặt được cả hình vào toạ độ HỮU TỈ không?"**

| Hình | Tỉ số | |
|---|---|:-:|
| vuông cân | `1 : 1 : √2` | ⛔ |
| tam giác đều (đường cao) | `a√3/2` | ⛔ |
| góc `30°` · `60°` · `120°` | `tan`/`cos` sinh `√3` | ⛔ |
| vuông, hai cạnh góc vuông **bội nguyên của `a`** | | ✅ |

Ba luật phụ, nhanh hơn nhưng **không đủ một mình**:
đáp án có `√` ⇒ bỏ · dữ kiện có `√` ⇒ bỏ · trắc nghiệm ⇒ bỏ.

⚠️ Bốn lớp rào vô tỉ, và **mỗi lớp phá luật của lớp trước**:

| | Dữ kiện | Đáp án | Toạ độ | Ví dụ |
|---|:-:|:-:|:-:|---|
| §2.1 | hữu tỉ | **vô tỉ** | — | `d = 3√6` |
| §2.2 | **vô tỉ** | — | vô tỉ | `SA = a√3` |
| §2.2b | hữu tỉ | **vô tỉ** | vô tỉ | `BC = √(AC²−AB²)` |
| §2.2c | hữu tỉ | hữu tỉ | **vô tỉ** | vuông cân, `V = a³/12` |

Chỉ luật *"toạ độ hữu tỉ"* bắt được cả bốn.

---

## 6. Nguồn đã kiểm — tính tới 2026-08-28

| Nguồn | Kết quả | Lý do |
|---|---|---|
| mathvn.com (1154 url) | ⛔ | 92% trắc nghiệm; 0 bài tự luận trong ranh giới |
| toanmath.com — trang HTML | ⛔ | **0** khối đề; chỉ 2 link `.pdf` + 16 `<img>` |
| toanmath.com — **8 PDF chuyên đề** | ✅ **nguồn hợp lệ** | 5 nguồn ≥ 30 trang tự luận; **cần người chép** |
| vted · hoc247 · diendantoanhoc | ⛔ | chặn fetch tự động |
| loigiaihay · vietjack | ⛔ | đề là ảnh / chặn |
| SGK PDF chính thức | ⛔ chưa tìm được | bản trên mạng không tra ngược được về nguồn chính thức |
| **thuvienhoclieu.com** — HTML | ⛔ | 391 KB · **0** đề dạng chữ · 116 `<img>` |
| **thuvienhoclieu.com** — `.docx` | ✅ **nguồn hợp lệ** | **74 bài** *"Cho hình chóp…"*; nhưng toán là **OLE MathType** ⇒ vẫn cần người chép |
| toanmath 2021 — HHKG 11 (255tr) | ✅ nguồn hợp lệ | PDF, cần người chép |
| Nguồn nước ngoài (IB · A-Level · đại học) | ⛔ **về ngôn ngữ** | đề phải là **tiếng Việt** (bề mặt hệ + `dev/cases.json §luat_soan`); dịch đề = **tự biến đổi đề**, bị cấm |

### ⚠️ Nguồn nước ngoài — loại vì NGÔN NGỮ, không vì chất lượng

Đã tìm: bài thể tích chóp tiếng Anh có sẵn và nhiều bài **hữu tỉ, tự luận**
(*"square pyramid, height 7 m, base 2 m"*). Nhưng bề mặt hệ là **tiếng Việt**,
prompt tiếng Việt, và `dev/cases.json` đòi *"văn xuôi tiếng Việt"*. Đưa đề tiếng
Anh vào là đo **năng lực dịch + hình học**, không phải thứ đề tài tuyên bố đo.
Dịch sang tiếng Việt thì người đo trở thành người soạn đề.

⇒ Nhận đề tiếng Anh là một **quyết định giao thức**, không phải việc thu thập.

**Nguồn KHÔNG phải là chỗ tắc.** 5 nguồn hợp lệ đã xác minh, ước lượng 35 bài
lấy được. Chỗ tắc là **bước ③ của §4** — và đó là bước chỉ người làm được.
