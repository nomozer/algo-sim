# MẬT ĐỘ CONTAINER — chẩn đoán, và một giả thuyết ĐÃ BỊ BÁC

## 1. Vấn đề có thật và dùng chung

Đo ở 1920×1080 (`density/before`), khoảng cách từ **đáy thẻ nội dung** tới **đáy
cột chứa nó**:

| Target | Thẻ cao | Cột cao | Trống | % cột |
|---|---:|---:|---:|---:|
| `binary.decimal_to_binary` | 381 | 885 | **538** | **59%** |
| `binary.base_conversion` | 382 | 885 | 503 | 57% |
| `logic.and_gate` | 439 | 919 | 480 | 52% |
| `algorithm.scan` | 467 | 885 | 418 | 47% |
| `network.packet_routing` | 475 | 885 | 410 | 46% |
| `database.relational_table_query` | 518 | 885 | 367 | 41% |
| `logic.boolean_dag` | 547 | 885 | 338 | 38% |
| … | | | | |
| `binary.character_encoding` | 757 | 885 | 128 | 14% |

**21/22 target có ≥150px trống** ở 1920×1080 · 10/22 ở 1536×864 · 7/22 ở
1366×768. Đây là `SHORT_CONTENT_IN_TALL_VIEWPORT`, dùng chung toàn danh mục —
**không phải** lỗi của renderer nào.

`.workspace-card` đã là `flex: 0 1 auto` (bản vá POLISH-1), tức **thẻ không hề
giãn**. Nội dung dừng đúng chỗ nó cần.

## 2. Giả thuyết đầu tiên — SAI, đã bác bằng phép đo

**Giả thuyết**: thủ phạm là `height: calc(100vh − 57px)` ở `.app-layout`; bỏ
trần `max-height: 900px` để bố cục cao theo nội dung ở mọi màn rộng thì cụm sân
khấu · thuyết minh · điều khiển sẽ đứng liền nhau.

**Đã thử**: đổi `@media (min-width: 1101px) and (max-height: 900px)` thành
`@media (min-width: 1101px)`.

**Kết quả đo** (`density/after`):

| Viewport | Trống TB trước → sau | Lớn nhất | ≥150px |
|---|---|---|---|
| 1920×1080 | 308 → **309** | 538 → 538 | 21/22 → **21/22** |
| 1536×864 | 174 → 174 | 322 → 322 | 10/22 → 10/22 |
| 1366×768 | 155 → 155 | 253 → 253 | 7/22 → 7/22 |

**Không đổi một pixel nào.** Đã hoàn nguyên — giữ một thay đổi CSS không có lợi
ích đo được, mà lại mở rộng phạm vi sticky + `padding-bottom: 140px` sang mọi màn
cao, là nợ kỹ thuật không có lý do.

**Vì sao sai**: `min-height` không loại bỏ được hàng `minmax(0, 1fr)`. Container
cao tối thiểu một màn, và hàng `1fr` **vẫn nuốt trọn phần dư** — nên
`.panel-center` vẫn giãn hệt như cũ.

## 3. Chủ sở hữu thật

```css
.app-layout {
  grid-template-rows: minmax(0, 1fr) auto;   /* ← hàng center luôn lấp đầy */
  grid-template-areas: "center right" "controls controls";
}
```

Muốn cụm nội dung ôm sát thì phải đụng **cách chia hàng**, không phải chiều cao
container: hàng theo `auto` cộng `align-content: start`, để phần dư rơi xuống
**dưới cả lưới** thay vì vào trong cột giữa.

Đó là thay đổi ở đúng vùng W4B-1A vừa ổn định (cuộn trang, sticky controls, bù
padding), nên nó xứng đáng có một lượt riêng với BEFORE/AFTER và đủ sáu viewport
— không phải một sửa vội.

## 4. Trạng thái

Không giữ thay đổi mã nào từ lượt này. Cây làm việc sạch ngoài phần đo thêm
`workspace_card` trong runner (thuần đo, không đụng sản phẩm).

`W4B-2A` vẫn **PARTIAL**: bốn renderer cô đọng đã xác nhận `B`, nhưng
`STAGE_OR_CONTAINER_DENSITY_ISSUE` **còn mở** — nay đã có chủ sở hữu chính xác
và một giả thuyết bị loại, nên lượt sau không phải dò lại từ đầu.
