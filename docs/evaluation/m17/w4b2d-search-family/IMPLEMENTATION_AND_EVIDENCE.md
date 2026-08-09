# W4B-2D — HỌ TÌM KIẾM QUA CỔNG THÍ NGHIỆM

Kết luận: **W4B2D_SEARCH_FAMILY_COMPLETE — LINEAR_SEARCH + BINARY_SEARCH VERIFIED.**

Nguồn đóng băng khi đo: `4e64595` (+ artifact/doc của chính wave này).
Vite khởi động lại SẠCH trước mỗi lượt đo, cổng 3000, `strictPort`.

## 0. Môi trường

`vite.config.ts` nay có `strictPort: true`. Vite mặc định nhảy 3001/3002 khi
3000 bận, mà mọi `capture-*.mjs` đều mặc định `--port 3000` ⇒ runner vẫn chụp
được ảnh, của một server CŨ. Hai artifact đã phải gỡ vì đúng lỗi đó (`0a71268`,
`7ce27e3`). Đã chứng minh guard đỏ được: `Port 3000 is already in use`, exit 1.

## 1. §3 — Kéo của `linear_search` là WHAT-IF

| Câu hỏi §5 | Trả lời |
|---|---|
| Học sinh đổi gì | thứ tự phần tử trong dãy (đổi chỗ hai cột) |
| Đại lượng nhân quả | số lần so sánh tới khi tìm thấy |
| Có trong thuật toán canonical? | **không** — `runLinearSearch` chỉ phát `compare_value`/`mark`/`done`; mã giả trên màn hình không có bước đổi chỗ |
| Vậy là gì | đổi ĐẦU VÀO rồi chạy lại ⇒ what-if |
| Quan sát có cần kéo? | **không** — khối chi phí (đã so sánh / chưa xét / xấu nhất) đã chở cơ chế |
| Hiểu được khi ẩn kéo? | có — ảnh `position-numbering/before/` là màn hình đọc được đầy đủ, chưa hề kéo |
| Đặt sau cổng có mạch lạc hơn? | có — trước wave này Quan sát bày ĐỒNG THỜI cam kết và lời mời kéo, không gì phân biệt |

**Trước:** kéo dùng được thẳng ở Quan sát, cạnh vùng cam kết.
**Sau:** Quan sát thuần mô phỏng; mở Thí nghiệm mới có cam kết **và** kéo, kèm
`framing` nói tách bạch hai câu hỏi (§18). `mode` giữ `framed` — lý do cũ không
sai, chỉ đổi chỗ đặt.

## 2. §4 — Hệ đếm vị trí: MAJOR, đã sửa

Chi tiết + ba lượt đo: [`position-numbering/README.md`](position-numbering/README.md).
Tóm tắt: mã giả 1-based vs `VarsView`/`ArrayView` in giá trị thô 0-based, cùng
màn hình. Chủ sở hữu mới `POSITION_VARS` (`core/pseudocode.ts`), truyền vào
`VarsView` qua tham số nên `scan`/`program` an toàn theo cấu trúc.
Engine **không đổi một giá trị nào** — chỉ trình bày.

## 3. Bằng chứng trình duyệt

| Lượt | Phạm vi | Kết quả |
|---|---|---|
| `browser-flow/` | linear_search + binary_search, luồng §20/§27 đầy đủ | **PASS 36/36** |
| `regression-gated/` | 5 target đã gác từ W4B-2B/2C | **PASS** (không hồi quy) |
| `responsive/` | 6 viewport × 4 route, hình học vỏ | **PASS** |
| `responsive-states/` | 1366×768 · 1024×768 · 768×900 × luồng 4 trạng thái | **PASS** |
| `position-numbering/` | before → fault-injection → after | `NO_CONTRADICTION` |

Luồng đã chứng minh cho cả hai bài: Quan sát không vùng cam kết · quan hệ ở lại
· mở cổng **bằng bàn phím** (Enter) · cam kết sai → `incorrect` · cam kết đúng →
`correct` · canonical state KHÔNG đổi qua mọi lần bật/tắt trình bày · 0 rò đáp
án · đóng cổng không reset · timeline vẫn chạy.

### Hai lỗi PHÉP ĐO tự bắt được (không phải lỗi sản phẩm)

1. `audit-search-position.mjs` bản đầu suy "VarsView 0-based" từ việc vùng hành
   động in `i+1` — khẳng định về một bề mặt nó không đọc. Sửa thành so chip
   THẬT với vùng hành động THẬT, rồi chạy lại trên mã CŨ (`fault-injection/`)
   để chứng minh nó không hoá mù.
2. `capture-w4b2b-experiment.mjs` ánh xạ nhãn nút theo VỊ TRÍ
   (`commitButtons[options.indexOf(id)]`). Đúng cho hai họ cũ (2 lựa chọn cùng
   thứ tự), **vỡ** cho `binary_search`: `DecisionPoint.options` xếp
   `[left, right, found]` còn `SearchActionZone` cố ý dựng `[right, found, left]`
   kèm ĐẢO NGHĨA nhãn. Lượt đầu vì thế báo "engine chấm đúng thành sai" — một
   kết luận oan cho sản phẩm. Nay hỏi thẳng mô hình, id đi theo cặp với label.

Cả hai đều thuộc anti-pattern #14: một guard chưa từng thấy màu đỏ chưa được
chứng minh, và một guard đo nhầm chỗ còn tệ hơn không có guard.

## 4. §28–§30 — Ba bất biến họ

- **COMMITMENT_SURFACE_COUNT ≤ 1** — §2 **không** phải viết lại.
  `commitmentSurfaceVisible` đã là chủ sở hữu; hai bài tìm kiếm tự chuyển từ ca
  (A) sang ca (B) vì cả hai test đọc thẳng bản khai policy.
- **RELATION ∈ OBSERVE** — phải sửa `ui.tsx`: bộ lọc dải nhân quả dùng `!search`
  VÔ ĐIỀU KIỆN trong khi scan/sort đã dùng `!(x && commitmentVisible)`. Để
  nguyên thì Quan sát mất **cả** cam kết **lẫn** quan hệ.
- **WHAT-IF ≠ COMMITMENT** — `predict.check` vẫn là bên chấm duy nhất; kéo sinh
  nhánh what-if, không bao giờ quyết định đúng/sai.

## 5. §34 — Soát có phạm vi (chỉ bề mặt Search)

| Mục | Nhận xét |
|---|---|
| Đánh số vị trí | đã nhất quán 4 bề mặt; xem §2 |
| Cổng có tìm thấy được không | có — teaser + nút, Tab tới được, `aria-expanded` đúng |
| Trùng lặp framing/hint | tiền đề nay nói **một** lần (test khoá); teaser không nhắc lại |
| Cam kết vs what-if | tách bạch bằng `framing` hai vế |
| Gắn phản hồi | phản hồi hiện trong đúng vùng vừa bấm |
| Thẻ câu hỏi khổng lồ | không có |

**Ghi nhận, KHÔNG sửa trong wave này:** ở 768×900, mở đồng thời Thí nghiệm và
Giải thích thì panel Giải thích **phủ** sân khấu (ảnh
`responsive-states/768x900/*-5-*`). Đây là hành vi vỏ có sẵn từ trước, không
phải hồi quy của W4B-2D; runner báo PASS vì không nút nào bị cắt và trang không
cuộn ngang. Nếu muốn sửa thì đó là việc của vỏ, không của họ tìm kiếm.

## 6. Nợ khai báo

- `algorithm.scan` (#10) còn nguyên mâu thuẫn hệ đếm: `scanPseudocode` sinh
  `ivar ← 1`, `scan.ts:246` ghi `trackIndexVar = 0`. Ngoài phạm vi đã chốt.
- `selection_sort` **không có bài mẫu offline** (`samples.ts` chỉ có 8/9 bài) ⇒
  không kiểm được bằng trình duyệt. Nó không bị wave này đụng tới; bằng chứng
  của nó là vitest, và điều đó phải nói rõ chứ không được ngầm tính vào "9
  target đã soát".
- Ma trận 6 viewport × 4 trạng thái chỉ chạy **3** viewport hẹp cho họ tìm kiếm
  (1920×1080 đã có ở lượt chính). 1536×864 và 1920×768 chưa chạy ở chế độ 4
  trạng thái.

## 7. Cổng

```
vitest      1009 / 64 file      xanh
pytest      1135 passed, 2 skipped, 1 deselected
tsc -b + vite build             sạch
git diff --check                sạch
browser     36/36 (search) · PASS (regression 5 bài) · PASS (responsive)
```

Baseline đối chiếu: tại `489f6a5` là **999/63** — đề bài ghi 996/62, đó là số
tại `df756d9`, trước khi `489f6a5` thêm 3 test sync-lock CODE_INDEX.
