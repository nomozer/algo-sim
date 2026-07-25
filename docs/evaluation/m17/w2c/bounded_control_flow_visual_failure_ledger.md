# W2C-VR — SỔ LỖI THỊ GIÁC

Chỉ ghi lỗi **quan sát được trên ảnh Chrome thật**. Mọi lỗi dưới đây đều lọt qua
toàn bộ unit test + SSR (offline W2C xanh 1047/626) — đó chính là lý do bước
review ảnh tồn tại.

| # | Fixture | Mức | Triệu chứng trên ảnh | Nguyên nhân | Vá | Trạng thái |
|---|---|---|---|---|---|---|
| VR1 | vr-cf4-boolean (và vr-cf3) | **BROKEN** | Bước cuối tô sáng `x ← 0` — nhánh KHÔNG chạy — ngay cạnh câu "x = 1" | Bước `done` gán `line = số dòng cuối` của mã giả; dòng cuối thường là nhánh else / thân vòng lặp | Bước kết thúc **không trỏ dòng nào** (`core/program.ts`, chỉ con trỏ dòng — không đụng phép tính, biến, điều kiện hay kết quả) | **ĐÃ SỬA** |
| VR2 | vr-cf1-assignment | PARTIAL | Chỉ thấy `y 7`, không thấy `y` vốn bằng mấy | Panel biến chỉ đọc snapshot bước hiện tại | Hiện `y: 0 → 7` từ snapshot bước trước / `spec.variables` (dữ liệu có thẩm quyền) | **ĐÃ SỬA** |
| VR3 | mọi fixture, bước cuối | Nhỏ | Cùng một câu hiện hai lần (băng thuyết minh + băng kết quả) | Renderer luôn vẽ cả hai | Ẩn băng thuyết minh khi trùng khít câu kết quả | **ĐÃ SỬA** |
| VR4 | vr-cf4-boolean | Nhỏ | Chip biến ghi `true`/`false` còn mã giả ghi `đúng`/`sai` | `VarsView` dùng `String(value)` | `formatVarValue` hiển thị boolean bằng tiếng Việt | **ĐÃ SỬA** |

## Còn mở (KHÔNG sửa trong VR — cần quyết định riêng)

| # | Vấn đề | Vì sao không sửa ở đây |
|---|---|---|
| VR-O1 | Chương trình **một câu lệnh** hiện kết quả ngay khi mở, vì trace không có bước **tiền-thực-thi** | Thêm bước đó = **đổi executor/trace**, §9 cấm trong VR. Là hành vi CHUNG của `TraceBuilder` toàn kho mã (`runScan` cũng bắt đầu bằng bước gán hạt giống), không phải đặc thù W2C |

## Artefact phép đo — KHÔNG phải lỗi sản phẩm

| # | Artefact | Bằng chứng ngược lại |
|---|---|---|
| M1 | `condition_has_words` báo `False` cho ca hiện `ĐÚNG` | `Đ` không phải word-char trong regex JS (`\b` không khớp). Ảnh `vr-cf3-while-desktop-mid_iteration.png` có chữ "ĐÚNG" rõ ràng |
| M2 | `notice_title` trả "Gợi ý khám phá" | Selector bắt nhầm `h2` của mục gợi ý bên dưới; ảnh `vr-cf5-insufficient-narrow.png` cho thấy tiêu đề thật "CHƯA ĐỦ DỮ KIỆN" |

**Bài học giữ lại:** assertion xanh **không** đủ để chấm REAL_VISUAL. Ba trong
bốn lỗi trên (VR1, VR3, VR4) không có assertion nào bắt được — chỉ có mắt người
nhìn PNG.
