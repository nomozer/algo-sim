# M17 W3-VR — Review thị giác `binary.character_encoding`

**Ngày:** 2026-07-26 · **Nhánh:** `main` · **HEAD trước VR:** `4ab1262` ·
**Phân loại:** SUPPORTING

Chrome thật qua CDP (`frontend/scripts/capture-w3-encoding.mjs`, dùng lại khuôn
CDP của `capture-w2c-program.mjs`). Viewport đặt **trước khi trang dựng**, nạp
lại trang cho từng viewport (bài học VIS-003, RC1 §E1).

Fixture đi qua **chính `validateCharEncodingSpec` + `runCharacterEncoding`** của
sản phẩm; dãy bit do **`toBase()` của `base_conversion`** sinh — không có engine
fixture song song, không sửa production để chụp.

## Kết quả

| | |
|---|---|
| Fixture review | **4** |
| Ảnh | **16** — desktop **11** · 768px **5** |
| Lỗi phát hiện | **2** |
| Lỗi đã sửa | **2** |
| Blocker còn lại | **0** |
| **REAL_VISUAL** | **4** · PARTIAL **0** · **BROKEN 0** |

| Fixture | Trạng thái |
|---|---|
| VR-ENC-1 ASCII một ký tự | REAL_VISUAL |
| VR-ENC-2 ASCII chuỗi ngắn | REAL_VISUAL |
| VR-ENC-3 Unicode precomposed | REAL_VISUAL |
| VR-ENC-4 emoji — từ chối | REAL_VISUAL |

## Hai lỗi CHỈ REVIEW ẢNH mới thấy

### W3-VR1 — thuyết minh lặp hai lần ở bước cuối

Băng thuyết minh và băng kết quả hiện **cùng một câu** (*"Đã mã hoá 1 ký tự theo
bảng mã Unicode code point."*), làm học sinh tưởng là hai thông tin khác nhau.

**Vá:** ẩn băng thuyết minh khi nó trùng khít câu kết quả.

> Đây là **cùng lớp lỗi đã gặp ở W2C-VR3**. Module W3 viết mới từ đầu nên không
> mang theo bản vá — ghi lại để lần sau tạo renderer timeline thì kiểm mục này
> ngay, đừng đợi review ảnh bắt.

### W3-VR2 — ký tự chữ số dễ đọc thành con số

Ô "Ký tự" in `7` trần, ngay cạnh cột "Thập phân 55". Đó **chính là điểm nhầm mà
bài học này tồn tại để sửa** — nếu bảng tự nó gây nhầm thì phản tác dụng.

**Vá:** `displayChar()` bọc nháy cho ký tự in được (`'7'`, `'A'`, `'ế'`); ký tự
đã có nhãn mô tả (`dấu cách`) giữ nguyên nhãn. Thuần trình bày — cả `char` lẫn
`label` đều đọc từ trace.

## Điều đã được chứng minh bằng ảnh

- **Progressive reveal thật, không phải CSS che:** ở bước đầu bảng chỉ có ký tự
  và ba ô `…`; DOM **không chứa** 65 hay dãy bit. Mã xuất hiện **sau** bước tra,
  dãy bit **sau** bước đổi cơ số, hàng chốt **sau** commit.
- **Unicode đúng:** `ế` giữ nguyên dấu, `U+1EBF`, thập phân **7871**, nhị phân
  `1111010111111` — **không đệm**, khớp đúng `toBase(7871, 2)`. Vượt xa trần 255
  của `decimal_to_binary`, đúng lý do chọn đường `base_conversion`.
- **Chuỗi nhiều ký tự:** `Tin` → T(84) · i(105) · n(110), đúng thứ tự; hàng chưa
  xử lý không mang kết quả thật.
- **Từ chối emoji sạch:** không mount mô phỏng, **không** hiện hai hàng surrogate,
  tiêu đề *"NGOÀI DANH MỤC MÔ PHỎNG"* đúng bản chất (`capability_gap`, không phải
  thiếu dữ kiện), thông điệp nói rõ chỉ hỗ trợ BMP ≤ 65535.
- **768px:** `scrollWidth ≤ clientWidth` mọi ảnh · 0 phần tử bị cắt · bảng không
  tràn · controls nhìn thấy và bấm được · notice không bị cắt.
- **Không lộ token kỹ thuật** ở bất kỳ ảnh nào (quét 15 chuỗi cấm: tên spec,
  target id, `InputKind`, tên phase, `capability_gap`, `undefined`/`null`/`NaN`).

## Guard renderer-authority (giữ + thêm)

- renderer **không** gọi `charCodeAt`/`codePointAt`/`toString(2)`/`toBase` để
  tính giá trị ngữ nghĩa — khoá bằng test dùng **trace bịa** (`'A'` mang mã 999):
  renderer hiện 999, không hiện 65;
- ký tự, thập phân, nhị phân đều lấy từ `rows` của trace;
- hàng hiện tại lấy từ cursor authoritative;
- bảng cuối không lộ ở initial;
- emoji refusal không mount module;
- decomposed **không** bị renderer normalize.

## Giới hạn được chấp nhận (không sửa trong VR này)

1. **Chip domain hiện "HỆ CƠ SỐ"** — nhãn của domain `binary`, đúng về đăng ký
   nhưng hơi lệch nghĩa cho một bài mã hoá ký tự. Đổi nhãn domain ảnh hưởng cả
   `decimal_to_binary` và `base_conversion` ⇒ **ngoài phạm vi** VR này.
2. **Learner action chỉ là điều khiển timeline** — chưa có prediction/what-if;
   đây là năng lực **quan sát**.
3. Panel phải ở 768px nằm sau nút "Quan sát" của app shell — hành vi **chung mọi
   domain**, không đặc thù W3.

## Giới hạn khi trích dẫn

Đây là review **thị giác offline**. **Chưa chạy live LLM** — chưa có bằng chứng
Gemini sinh được `CharacterEncodingSpec` hợp lệ từ đề tiếng Việt thật.
