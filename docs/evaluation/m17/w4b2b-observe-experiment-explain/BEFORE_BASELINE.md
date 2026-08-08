# W4B-2B — BASELINE TRƯỚC KHI ĐỔI BỀ MẶT HỌC SINH

Chụp trên hình học **vừa được đóng băng** ở `W4B2A_RENDERER_FIT_COMPLETE`
(HEAD `a099cba`). Không đụng một dòng mã sản phẩm nào trong lượt chụp này.

Đây là mốc so sánh duy nhất hợp lệ cho Phase B: mọi ảnh BEFORE cũ hơn đều nằm
trên bố cục trước bản vá mật độ container, nên không so trực tiếp được.

## Bộ ảnh

| Thư mục | Nội dung |
|---|---|
| `before/find-max-panel-open/` | `algorithm.find_max` · initial · mid · final · 1920×1080 · 1536×864 · 1366×768 · panel MỞ (mặc định hiện tại) |
| `before/insertion-sort-panel-open/` | `algorithm.insertion_sort` · cùng ma trận |
| `before/find-max-panel-closed/` | `algorithm.find_max` · mid · 1920×1080 · panel ĐÓNG |

Mỗi thư mục kèm `responsive-diagnosis.json` mang đầy đủ hình học: `stage`,
`visual`, `workspace_card`, `panel_center`, `panel_right`, `panel_controls`,
`renderer_fit`, hit-test và phán quyết cổng chấm.

## Trạng thái mặc định HIỆN TẠI (thứ Phase B sẽ đổi)

- Panel phải **MỞ** mặc định ở màn rộng (`rightOpen: WIDE_SCREEN`).
- Panel mang nhãn **“Quan sát”**.
- `ActionZone` hiện **vô điều kiện** mỗi khi bước có tương tác — không có cổng
  Observe nào; `labOpen` mới chỉ gác thao tác **kéo** cho policy `challenge`.

## Kiểm kê nhãn “Quan sát” — cho §7

Đổi tên phải quét cả ba loại bề mặt, không chỉ nút bấm:

**Mã sản phẩm**
- `App.tsx:73` — nhãn nút bật/tắt panel
- `components/SimulationInspector.tsx:35` — `<span className="eyebrow">QUAN SÁT</span>`
- `simulations/domains/generic/ui.tsx:544` — nhãn trong renderer generic

**Test đang khoá chuỗi này** (đổi nhãn mà quên thì suite đỏ, hoặc tệ hơn là
xanh giả nếu test chỉ khớp lỏng):
`components/ux-shell.test.tsx` · `components/ui-hygiene.test.ts` ·
`components/array-layout.test.ts` · `simulations/domains/generic/mode-switch.test.tsx` ·
`simulations/domains/algorithm/program-module.test.tsx` ·
`simulations/domains/logic/dag.test.tsx`

**Comment/tài liệu** (không phải bề mặt học sinh, nhưng để lại sẽ gây hiểu nhầm
cho lượt sau): `App.tsx:14,44` · `ArrayView.tsx:26,271` ·
`SimulationInspector.tsx:7,13` · `core/program.ts:789`

Lưu ý một chỗ dễ sót: `core/program.ts:789` ghi *"Ở màn hẹp panel Quan sát đóng
mặc định, nên bước xét điều kiện là chỗ DUY NHẤT…"* — đó là một **giả định logic**
gắn với trạng thái panel, không phải chỉ một nhãn. §8 đổi panel thành đóng mặc
định ở **mọi** màn, nên phải đọc lại đoạn đó chứ không thay chuỗi rồi đi tiếp.

## Giới hạn

Lượt này **chỉ** chụp baseline. Chưa đổi tên, chưa đóng panel mặc định, chưa gác
`ActionZone`, chưa có `Thí nghiệm`. Không có tuyên bố nào về Phase B.
