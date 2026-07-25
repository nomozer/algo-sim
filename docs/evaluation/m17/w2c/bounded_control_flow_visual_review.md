# M17 W2C-VR — Review thị giác `algorithm.bounded_control_flow`

**Ngày:** 2026-07-26 · **Nhánh:** `main` · **HEAD trước VR:** `f762056` ·
**Phân loại:** SUPPORTING (kiểm tra trực quan cho capability CORE của W2C)

Chrome thật qua CDP (`frontend/scripts/capture-w2c-program.mjs`, dùng lại hạ tầng
của `capture-w2b-patch.mjs`). **Viewport đặt TRƯỚC khi trang dựng** và nạp lại
trang cho từng viewport — không lặp lại artefact phép đo VIS-003 của RC1 §E1.

Fixture đi qua **chính `validateProgramSpec` + `runProgram` của sản phẩm** —
không dựng engine fixture song song, không sửa production code để chụp.

## Kết quả

| | |
|---|---|
| Fixture review | **8** (5 mô phỏng + 3 từ chối) |
| Ảnh | **32** — desktop **20** · 768px **12** |
| Lỗi phát hiện | **4** |
| Lỗi đã sửa | **4** |
| Blocker còn lại | **0** |
| **REAL_VISUAL** | **7** |
| **PARTIAL_VISUAL** | **1** (VR-CF-1) |
| **BROKEN_VISUAL** | **0** (sau vá; **1** trước vá) |

| Fixture | Trạng thái |
|---|---|
| VR-CF-1 gán | **PARTIAL_VISUAL** — xem ghi chú |
| VR-CF-2 if/else | REAL_VISUAL |
| VR-CF-3 while hoàn thành | REAL_VISUAL |
| VR-CF-4 biểu thức logic | REAL_VISUAL |
| VR-CF-8 chạm giới hạn lặp | REAL_VISUAL |
| VR-CF-5 thiếu dữ kiện | REAL_VISUAL |
| VR-CF-6 hàm/đệ quy | REAL_VISUAL |
| VR-CF-7 biến chưa có giá trị | REAL_VISUAL |

## Lỗi CHỈ REVIEW ẢNH mới thấy (unit test đều xanh)

### VR1 — **BROKEN**: bước kết thúc highlight nhánh KHÔNG chạy

Bước `done` trỏ vào **dòng cuối** của mã giả. Ở VR-CF-4 dòng cuối là `x ← 0` —
nhánh **ngược lại**, vốn không hề chạy (chương trình đi nhánh **thì**, x = 1).
Ảnh `visual/before/vr-cf4-boolean-desktop-final.png` cho thấy dòng `x ← 0` được
tô sáng ngay cạnh câu "…x = 1": học sinh đọc thành *"nhánh đó vừa chạy và cho
x = 1"* — sai hoàn toàn về execution trace. VR-CF-3 cũng vậy (tô thân vòng lặp
sau khi đã thoát).

**Vá:** bước kết thúc **không trỏ vào dòng nào** — không câu lệnh nào đang thực
hiện thì không tô gì. Khoá bằng hai test: bước cuối `line === undefined`, và
dòng của nhánh không chạy **không bao giờ** nằm trong tập dòng được tô.

### VR2 — **PARTIAL**: không thấy giá trị TRƯỚC của biến

Panel biến chỉ hiện giá trị *sau*. Với chương trình một câu lệnh, học sinh mở
lên đã thấy `y 7` mà không thấy nó từ đâu ra.

**Vá:** hiện `y: 0 → 7` cho biến vừa đổi, lấy từ dữ liệu **có thẩm quyền** —
snapshot bước liền trước, hoặc `variables` ban đầu của spec đã validate ở bước
đầu. Không suy diễn, không chạy lại gì trong renderer.

### VR3 — thuyết minh lặp hai lần ở bước cuối

Băng thuyết minh và băng kết quả hiện **cùng một câu**. **Vá:** ẩn băng thuyết
minh khi nó trùng khít câu kết quả.

### VR4 — thuật ngữ luận lý không nhất quán

Chip biến hiện `true`/`false` trong khi mã giả và thuyết minh cùng màn hình viết
`đúng`/`sai`. **Vá:** `formatVarValue` trong `VarsView` hiển thị boolean bằng
tiếng Việt. Chỉ luồng điều khiển hữu hạn đưa boolean vào `vars` nên không làm
trôi cách hiển thị của domain khác.

## Ghi chú VR-CF-1 — vì sao PARTIAL chứ không REAL

Chương trình **một câu lệnh**: bước 0 chính là câu lệnh duy nhất, nên vừa mở đã
thấy `y = 7`. Không có gì **sai** (đó đúng là snapshot của bước đó) và sau VR2
thì phép tính đã quan sát được (`y: 0 → 7`), nhưng học sinh **không có bước
TRƯỚC khi chạy**.

Sửa triệt để = thêm một **bước tiền-thực-thi** vào trace = **đổi executor**,
nằm ngoài phạm vi được phép của VR (§9). Ghi nhận thành finding mở, chờ quyết
định — **không tự mở patch wave**. Lưu ý: đây là hành vi CHUNG của `TraceBuilder`
toàn kho mã (`runScan` cũng bắt đầu bằng bước gán hạt giống), không phải đặc thù
W2C.

## Điều đã được chứng minh bằng ảnh

- **Mã giả** thụt cấp đúng, dòng hiện tại tô rõ, **không có phantom highlight**
  (sau VR1), số dòng hiển thị, không lộ `statement_id`.
- **Điều kiện** hiện bằng **CHỮ** `ĐÚNG`/`SAI` — không chỉ bằng màu.
- **Nhánh được chọn** ghi rõ ("Chạy: nhánh NGƯỢC LẠI"); nhánh không chạy **không**
  mang trạng thái đã thực hiện.
- **Vòng lặp**: kiểm điều kiện · vào thân · cập nhật biến · thoát là **các bước
  riêng biệt**; "Lượt lặp thứ n" hiện rõ; thoát ghi "sau 4 lượt".
- **Chạm giới hạn** nói *"chưa kết thúc trong giới hạn mô phỏng"*, **không** gọi
  là hoàn thành, controls vẫn dùng được.
- **Từ chối**: tiêu đề *"CHƯA ĐỦ DỮ KIỆN"*, đòi đúng ba thứ cần bổ sung, **không**
  hiện chương trình mẫu, **không** lộ mã lỗi/target id/enum validator.
- **768px**: `scrollWidth ≤ clientWidth` mọi ảnh, 0 phần tử bị cắt, mã giả không
  bị ancestor clip, controls nhìn thấy và bấm được, thuyết minh xuống dòng.

## Artefact phép đo (ghi trung thực, KHÔNG phải lỗi sản phẩm)

1. `condition_has_words` dùng `\b(ĐÚNG|SAI)\b`: **`Đ` không phải word-char** trong
   regex JS nên mọi ca hiện `ĐÚNG` bị báo `False`. **Ảnh chứng minh chữ có thật**
   (vd `vr-cf3-while-desktop-mid_iteration.png`).
2. `notice_title` bắt nhầm `h2` "Gợi ý khám phá" của mục gợi ý bên dưới; **ảnh**
   cho thấy tiêu đề thật là "CHƯA ĐỦ DỮ KIỆN".

Cả hai là lý do vì sao **không được chấm REAL_VISUAL chỉ vì assertion xanh**.

## Coverage gap

- Panel biến ở 768px nằm sau nút "Quan sát" của app shell — **hành vi chung của
  mọi domain**, không phải đặc thù W2C; chưa đánh giá trong wave này.
- Prediction/what-if chưa có nên không có tiêu chí thị giác tương ứng.

## Giới hạn phải giữ khi trích dẫn

- Đây là review **thị giác offline**. **Chưa chạy live LLM** — chưa có bằng chứng
  Gemini sinh được `ProgramSpec` hợp lệ từ đề tiếng Việt thật.
- Không đụng `relational_table_query`, không mở Wave 2D, không merge archive.
