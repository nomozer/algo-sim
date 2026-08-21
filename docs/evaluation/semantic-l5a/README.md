# L5a — soát thị giác đại diện cho `generic.semantic_program`

Ngày: 2026-08-21 · Runner: `frontend/scripts/l5a-semantic-visual.mjs`

## Chạy lại

```bash
cd frontend && npm run dev -- --port 3100 --strictPort     # cửa sổ khác
cd frontend && node scripts/l5a-semantic-visual.mjs --port 3100
cd frontend && node scripts/l5a-semantic-visual.mjs --port 3100 --faultcheck
```

Fixture (`public/fixtures/semantic_l5a.json`) **sinh từ backend thật** bằng
`compile_semantic_program_to_envelope` trên `fixtures_coverage_18.py` — không
phải JSON viết tay, nên nó luôn phản ánh hợp đồng envelope hiện hành.

## Vì sao ĐO HÌNH HỌC, không so ảnh pixel

Repo chỉ có thư viện `playwright`, không có `@playwright/test`, nên không có
`toHaveScreenshot()` và bộ ảnh nền. Nhưng `getBoundingClientRect()` cho bằng
chứng **chặt hơn**: nó nói được *vì sao* hỏng ("nhãn A đè nhãn B 14px") thay vì
"12.000 pixel đổi màu", và không đỏ oan khi đổi một token màu.

## Năm phép đo

| # | Bắt gì | Vì sao có |
|---|---|---|
| 1 | Chữ đè chữ | Con trỏ `i` đè dòng thuyết minh trong ảnh gốc (spec §0b) |
| 2 | Tràn khỏi sân khấu / tràn ngang trang | Clipping ở bề rộng hẹp |
| 3 | Con trỏ chui vào nhãn khác | Neo hỏng (bất biến #34) |
| 4 | **Chữ lặp** | Thêm sau khi chính lượt này phơi ra lỗi — xem dưới |
| 5 | Khung ĐỔI sau 6 bước | Hồi quy trực tiếp cho E1 ("narration chạy, hình đứng") |

## Kết quả

**8/8 hàng SẠCH** · 4 ca × 2 bề rộng (1366×768 · 1920×1080).
Ca: `stack_bracket` · `find_max` · `graph_bfs` · `bar_chart`.

Hai điều kiện trước khi tin bản soát này (`ARCHITECTURE_MAP §8` #14):

- **Dấu vân tay trang** — khẳng định `moduleId === "generic.semantic_program"`
  và có `[data-route='semantic']` trước khi đo. Dev server chạy cổng **3100
  tường minh**, không để Vite nhảy cổng ngầm: `vite.config.ts` cấm điều đó vì
  hai artifact từng phải gỡ do chụp nhầm server cũ giữ cổng 3000.
- **Tiêm lỗi giả** — `--faultcheck` cho **8/8 hàng ĐỎ**. Guard chưa từng đỏ là
  guard chưa được chứng minh.

## Một lỗi mà bốn phép đo đầu KHÔNG bắt được

Ảnh chụp lượt đầu cho thấy dòng thuyết minh hiện **hai lần**: module tự vẽ
`.sem-narration`, rồi shell vẽ lại qua `narrate()` → `NarrationSlot`. Hai khối
xếp **dọc** nên không chồng nhau — phép đo chồng lấn mù hoàn toàn.

Đã sửa theo đúng quy ước sẵn có (`generic/ui.tsx`, `algorithm/ui.tsx` đều không
tự vẽ narration), và **thêm phép đo #4** để loại lỗi này không tái phát.

Đáng ghi: bản thân ảnh chụp mới là thứ phát hiện ra nó, không phải phép đo. Đó
là lý do runner vẫn lưu ảnh dù đã đo hình học.

## Giới hạn đã biết — KHÔNG phải lỗi bố cục

`graph_bfs` **không vẽ đồ thị**. `graph` là một `MemoryType` của IR nhưng KHÔNG
có trong enum `VisualContainerBinding.primitive`, nên không cách nào buộc một
đồ thị vào hình. Mô phỏng hiện chỉ thấy hàng đợi và thứ tự duyệt.

Đây là khoảng trống ở **tầng hợp đồng**, thuộc loại quyết định kiến trúc — ghi
lại ở đây, không tự vá trong Task 11.
