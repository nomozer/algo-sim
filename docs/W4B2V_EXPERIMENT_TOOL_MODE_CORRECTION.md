# W4B-2V/C2 — CHỈNH SAI: từ TẤM NỘI DUNG NHỎ HƠN sang CÔNG CỤ

`THESIS_SCOPE = T3`. Baseline `c1899e3`. Không đụng engine.

## 1. Phân loại lại verdict trước

Wave C tuyên bố `EXPERIMENT_TOOL_MODE_COMPLETE` dựa trên: chữ ít đi, chiều cao
giảm 39–50%, canonical ổn định. **Ba điều đó đúng nhưng không đủ.** Cấu trúc vẫn
là `<section className="action-zone">` — một phần tử block mang
`background: canvas-soft` + `border` + `padding md lg` + `flex-direction: column`
⇒ **trải 100% bề ngang**. Nhỏ hơn, nhưng vẫn là tấm nội dung.

Verdict đúng của trạng thái đó: **`EXPERIMENT_PANEL_COMPACTED — TOOL_MODE_NOT_YET_ACHIEVED`**.

Bài học đo lường: `workspaceDelta` một mình **nghiệm thu được một cái panel**.
Phải đo **hình học** — bề rộng, chrome, vị trí lối đóng — mới phân biệt được.

## 2. Hình học đo trong Chrome

`.experiment-tool` / `.action-zone` so với khối chứa mô phỏng, tại 1920×1080:

| target | bề rộng TRƯỚC → SAU | chrome thẻ | close nằm trong tool | Δ chiều cao |
|---|---|---|---|---|
| `linear_search` | 100% → **34%** | có → **không** | không → **có** | +105 → **+17** |
| `binary_search` | 100% → **43%** | có → **không** | không → **có** | +105 → **+17** |
| `insertion_sort` | 100% → **64%** | có → **không** | không → **có** | +94 → **−34** |
| `count_if` | 100% → **47%** | có → **không** | không → **có** | +61 → **−34** |

Hai target **âm**: mở Thí nghiệm làm vùng làm việc *ngắn hơn* Quan sát, vì hàng
teaser + nút mở biến mất và được thay bằng công cụ inline. Tất cả đều dưới xa
ngưỡng §22 (≤60px không phản hồi, ≤90px có phản hồi).

**Nói rõ một điểm:** `display` tính toán ra `flex`, không phải `inline-flex` —
`.experiment-tool` là flex item của `.stack` nên bị blockify theo đúng CSS. Việc
co theo nội dung đạt được bằng `width: fit-content`, và bằng chứng là tỉ lệ
34–64%, không phải bằng thuộc tính `display`.

**Số hàng** đo được 2–3. Phép đếm này thô (nó gom con và cháu theo toạ độ `top`),
nên coi là chỉ báo, không phải con số chính xác — bằng chứng mạnh là ảnh chụp.

## 3. Đã đổi gì

| | TRƯỚC | SAU |
|---|---|---|
| khung cam kết khi gác cổng | `<section class="action-zone">` full-width, có nền/viền | nằm trong `.experiment-tool`, chrome `.is-tool` gỡ nền/viền/padding, xếp **ngang** |
| ba zone rời | ba khối JSX song song | **một** `commitZone` (ba mô hình vốn loại trừ nhau) ⇒ chỉ **một** chỗ quyết định chrome |
| chrome | cố định | `chrome = gated ? "tool" : "panel"` — dẫn xuất **capability** |
| framing | hàng chữ riêng | **`aria-label` của công cụ** — người đọc màn hình vẫn nghe mục đích, người nhìn đọc thẳng nhãn nút |
| teaser | hàng chữ riêng trên nút | `title` của nút; nhãn nút vốn đã tự mô tả |
| what-if | hàng chữ full-width | chip `ⓘ what-if`, nội dung đầy đủ ở `title`/`aria-label` |
| close | hàng riêng, đẩy phải | `×` **bên trong** công cụ, `aria-label="Đóng thí nghiệm"` |

Bài **chưa gác cổng** (`bubble_sort`, `selection_sort`) giữ nguyên chrome thẻ:
vùng cam kết của chúng không phải Thí nghiệm mà là phần thường trực của Quan sát.
Không cờ nào được bật thêm.

## 4. Bằng chứng phép đo phân biệt được panel với tool

§29 đòi chứng minh cấu trúc `c1899e3` **trượt** các phép kiểm mới. Đã khôi phục
đúng năm file của `c1899e3` rồi chạy: **6/10 test ĐỎ** — chrome thẻ, `.is-tool`
vắng, chrome không dẫn xuất, close ngoài tool, framing là hàng chữ, teaser là
hàng riêng. Khôi phục bản mới: **10/10 XANH**.

Đây là điều wave C thiếu: khi đó phép đo *không thể* phân biệt hai cấu trúc.

## 5. Bất biến cũ giữ nguyên

`CORE_OBSERVATION_STATE_PRESERVED_UNDER_GATING` xanh · commitment surface ≤ 1 ·
canonical ổn định qua mọi chế độ UI (đo ở cả bốn target) · 0 rò đáp án ·
`predict.check` vẫn là bên chấm duy nhất · spec reuse xanh · 0 nhánh renderer
theo ngữ cảnh/định danh · position numbering nguyên.

Phân biệt **cam kết ↔ what-if** không mất: nó ở chip `ⓘ what-if` (nội dung đầy
đủ trong `title`/`aria-label`) và có test khoá trên cặp `framing ∪ hint`.

## 6. Cổng

`vitest 1057/69` · `pytest 1135 passed, 2 skipped` · build sạch ·
browser **72/72 PASS** ở cả BEFORE lẫn AFTER · responsive `1920×1080 · 1366×768
· 768×900` PASS · `git diff --check` sạch.

## 7. Không đụng tới

Rollout họ Sort · `bubble_sort`/`selection_sort` · `sum_if` accumulator ·
`packet_routing` destination · `algorithm.scan` · `bounded_control_flow` ·
`base_conversion` · tree rule · database predicate · `generic.rule_scene` ·
motion · Explain · chồng lấp vỏ 768×900 · Home/Library/History · design token.

Tuyên bố được phép: *"giao diện trình bày Thí nghiệm như một công cụ hành động
theo ngữ cảnh, trên cùng một trạng thái mô phỏng tất định."* Không tuyên bố gì về
tải nhận thức hay kết quả học tập: `LEARNER_IMPACT_NOT_EVALUATED`,
`CURRICULUM_SUPPORT_PARTIAL`.
