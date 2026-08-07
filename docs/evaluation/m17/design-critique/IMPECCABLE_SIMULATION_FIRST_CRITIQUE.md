# IMPECCABLE — SIMULATION-FIRST DESIGN CRITIQUE

**Method: partial dual-agent.** Assessment A (design review) chạy như sub-agent
cô lập và hoàn tất. **⚠️ Assessment B (detector + browser evidence) chạy như
sub-agent nhưng CHẾT giữa chừng vì chạm giới hạn phiên, không trả kết quả nào.**
Phần tất định của nó được chạy lại **inline bởi context cha, SAU khi A đã khoá**
— nên mục đích của bất biến (A không bị detector neo phán đoán) vẫn giữ, nhưng
đây **không** phải một lượt dual-agent đầy đủ. Phần browser-overlay của B **không
được thực hiện**: không có overlay nào hiển thị trong trình duyệt của bạn.

Lượt này là **read-only design critique**. Không sửa một dòng production nào.

Ngày: 2026-08-08 · HEAD `63d9896` (sau W4B-1A) · Chrome 150.0.7871.187 · zoom 100%.

---

## A. DESIGN CONTEXT

| | |
|---|---|
| Sản phẩm | AlgoSim — hệ mô phỏng tương tác 2D/3D cho Tin học THPT |
| Bề mặt xét | Workspace shell: `App.tsx` + `.app-layout` · `.panel-center` · `.panel-right` · `.panel-controls` · `.sim-stage` |
| Mode (Impeccable) | **Operate** — người học hoàn thành một nhiệm vụ |
| Nguyên tắc số 1 (do đề tài đặt) | **SIMULATION FIRST** |
| Thẩm quyền thị giác | `DESIGN.md` gốc repo — thế giới "Notion Analysis"; `--primary` là accent cấu trúc **duy nhất**, bảng sticker chỉ để trang trí/status |
| Hợp đồng sư phạm | `docs/DESIGN_BRIEF.md` §3 — **bảy ràng buộc không được phá** |
| PRODUCT.md | **không có.** `context.mjs` phát `NO_PRODUCT_MD` nhưng nói rõ lệnh scoped trên mã sẵn có cứ chạy tiếp. Không chạy `init` ở lượt này — nó sẽ thêm file tracked mới ở gốc repo, và `shape`/`new-work` có quyền **ghi đè `DESIGN.md`** |

---

## B. ARCHETYPE REVIEW — điểm Nielsen

Nguồn: Assessment A, quan sát trên Chrome thật ở 1366×768 · 1440×1000 ·
1920×1080 · 768×900 qua `tree.traversal`, `network.graph_traversal`,
`algorithm.find_max`, `binary_search`, `bubble_sort`, `scan`, `selection_sort`
và các trạng thái từ chối.

| # | Heuristic | Điểm | Vấn đề chính |
|---|---|---|---|
| 1 | Visibility of system status | 3/4 | Bước N/M + `aria-live` tốt; nhưng ở 1366×768 dòng thuyết minh nằm **309–336px dưới nếp gấp** đúng lúc nó đổi |
| 2 | Match system ↔ real world | 2/4 | `Xét a[2] = 31…`, chip `nguong 35`, `Thứ tự thăm (engine)` — từ vựng máy trên bề mặt học sinh |
| 3 | User control and freedom | 3/4 | Đủ transport + seek + thoát nhánh what-if; nhưng **hai nút "làm lại" không phân biệt được** |
| 4 | Consistency and standards | 2/4 | Nhãn tĩnh sơn `--primary` (màu hành động); tree giấu đáp án, network in ra; ba hệ đánh số trên một màn |
| 5 | Error prevention | 3/4 | Taxonomy từ chối tốt, guard phím tắt cẩn thận; không xác nhận trước khi `Đặt lại` xoá lượt chạy |
| 6 | Recognition rather than recall | 2/4 | Chú giải 12px, có target **không có chú giải nào** trong khi màu vẫn mang nghĩa; mã giả cách hình 300px |
| 7 | Flexibility and efficiency | 3/4 | ← → Space có gợi ý hiện; slider tốc độ **đảo chiều**, không số, không đơn vị |
| 8 | Aesthetic and minimalist design | **1/4** | Sân khấu hằng số trong màn 1910px; 250–350px canvas chết; **đồng thời** 336px cơ chế bị giấu ở 1366×768; câu kết in **hai lần** |
| 9 | Error recovery | 3/4 | Copy từ chối là điểm sáng; nhưng `Không tìm thấy module "{moduleId}"` và text validator vẫn lọt tới học sinh |
| 10 | Help and documentation | 3/4 | Trợ giúp tại chỗ tốt; gợi ý quan trọng nhất lại là chữ **tương phản thấp nhất** trang |
| **Tổng** | | **25/40** | cả 10 heuristic đều áp dụng được |

### Deterministic scan (chạy inline)

```
detect.mjs frontend/src/App.tsx                → [] (exit 0, sạch)
detect.mjs frontend/src/components             → 1 phát hiện (exit 2)
detect.mjs frontend/src/simulations/domains    → sạch (exit 0)
```

Phát hiện duy nhất: `ArrayView.tsx:304` — `[layout-transition] transition: height`
(animate chiều cao gây layout thrash; nên dùng `transform`/`grid-template-rows`).

**Chính sự chênh lệch này là một kết luận.** Detector tất định quét ba cây mã và
tìm được **một** anti-pattern, trong khi phần đánh giá thiết kế tìm ra **hai P0**
— cả hai đều là *quan hệ giữa các thành phần* (bố cục không đòi màn hình; panel
lộ đáp án), thứ không một luật tĩnh nào bắt được. Đừng dùng "detector sạch" làm
bằng chứng thiết kế đạt.

---

## C. CATALOG PATTERNS — mở rộng ra 22 target (§5)

Đo từ artifact W4B-1A tại HEAD, checkpoint thuận lợi nhất cho mỗi target,
1366×768. `h%` = chiều cao sân khấu / chiều cao cột giữa.

| Target | Sân khấu | Cột giữa | h% | Cờ |
|---|---|---|---:|---|
| `network.packet_routing` | 180×643 | 615×693 | **0.29** | VISUAL_UNDERSIZED |
| `binary.decimal_to_binary` | 182×584 | 607×634 | 0.30 | VISUAL_UNDERSIZED |
| `binary.base_conversion` | 180×638 | 573×688 | 0.31 | VISUAL_UNDERSIZED |
| `binary.character_encoding` | 180×570 | 573×620 | 0.31 | VISUAL_UNDERSIZED |
| `algorithm.binary_search` | 286×877 | 773×927 | 0.37 | UNDERSIZED · AUXILIARY_DENSE |
| `algorithm.bounded_control_flow` | 290×710 | 764×760 | 0.38 | UNDERSIZED · AUXILIARY_DENSE |
| `algorithm.bubble_sort` | 286×942 | 743×992 | 0.38 | UNDERSIZED · AUXILIARY_DENSE |
| `algorithm.sum_if` | 286×942 | 747×992 | 0.38 | UNDERSIZED · AUXILIARY_DENSE |
| `algorithm.linear_search` | 286×942 | 722×992 | 0.40 | UNDERSIZED · AUXILIARY_DENSE |
| `logic.and_gate` | 240×762 | 607×812 | 0.40 | VISUAL_UNDERSIZED |
| `algorithm.count_if` · `find_max` · `find_min` | 286×914…935 | 702×964…985 | 0.41 | BALANCED |
| `database.relational_table_query` | 273×718 | 658×768 | 0.41 | BALANCED |
| `network.protocol_encapsulation` | 297×942 | 732×992 | 0.41 | BALANCED |
| `algorithm.insertion_sort` | 344×896 | 827×946 | 0.42 | BALANCED |
| `algorithm.selection_sort` | 286×717 | 661×767 | 0.43 | BALANCED |
| `algorithm.scan` | 268×669 | 607×719 | 0.44 | BALANCED |
| `logic.boolean_dag` | 309×718 | 687×768 | 0.45 | BALANCED |
| `generic.rule_scene` | 393×802 | 778×852 | 0.51 | BALANCED |
| `network.graph_traversal` | 456×586 | 798×636 | 0.57 | BALANCED |
| `tree.traversal` | 470×831 | 809×881 | 0.58 | BALANCED |

**10/22 target dưới 40%. Không target nào vượt 0.58.** Theo diện tích, cả danh
mục nằm trong 0.27–0.55. Đây là phát biểu đo được về nguyên tắc "SIMULATION
FIRST", không phải cảm nhận.

`OBSERVATION_SPARSE` **không kết luận được**: phép đo của tôi trả về chiều cao ô
lưới đã bị kéo bằng cột giữa, không phải chiều cao nội dung panel. Assessment B
lẽ ra đo độc lập phần này thì đã chết. Xem §L.

---

## D. SIMULATION SCALE — nguyên nhân gốc, và cái bẫy

### D.1. Shell không bao giờ đòi màn hình

`.app-layout` có **23 giá trị bề rộng khác nhau** ở 1366×768, và **đúng bộ giá
trị đó** ở 1536×864 (kiểm từ `catalog-after/responsive-diagnosis.json`, thu thập
*trước* khi agent chạy). Lưới stretch thì bề rộng phải là hằng số theo viewport.
Nó không phải hằng số ⇒ **bề rộng do nội dung quyết định, không do màn hình.**

Assessment A truy được cơ chế: `.app-layout { margin: 0 auto }`
([global.css:1521](../../../../frontend/src/styles/global.css#L1521)) trên một
flex item của `#root { display:flex; flex-direction:column }`. **Auto margin trên
trục ngang triệt tiêu `align-self: stretch`**, nên grid co về fit-content. Hệ quả
A đo được ở 1920×1080: 871px (**46%**) màn hình là lề trống, và bề rộng của mô
phỏng thực chất đang do **độ dài câu thuyết minh dài nhất** quyết định.

> **Guard W4B-1A của tôi không thể bắt được lỗi này.** Năm điều kiện chấm đều hỏi
> "có tràn / có bị giấu / có bị che không". Không điều kiện nào hỏi "app có dùng
> hết màn hình không". Một bố cục bỏ không 46% màn hình vẫn PASS sạch.

### D.2. Cái bẫy: đừng cho SVG giãn ra

Mọi renderer 2D tự khoá `maxWidth` bằng đúng bề rộng `viewBox`:
[traverse-module.tsx:250-302](../../../../frontend/src/simulations/domains/network/traverse-module.tsx#L250-L302) (`W=420`) ·
[logic/ui.tsx:37](../../../../frontend/src/simulations/domains/logic/ui.tsx#L37) (460) ·
[program-module.tsx:165](../../../../frontend/src/simulations/domains/algorithm/program-module.tsx#L165) (560) ·
[network/ui.tsx:66](../../../../frontend/src/simulations/domains/network/ui.tsx#L66) ·
[tree-module.tsx:404](../../../../frontend/src/simulations/domains/tree/tree-module.tsx#L404) ·
[ArrayView.tsx:239](../../../../frontend/src/components/ArrayView.tsx#L239).

Phản xạ tự nhiên — "bỏ `maxWidth` đi cho nó giãn" — **đã thử và đã hỏng**:
[dag-module.tsx:273-305](../../../../frontend/src/simulations/domains/logic/dag-module.tsx#L273-L305)
ghi lại rằng `maxWidth: 720` trên `viewBox` 432 làm SVG bị **phóng 1,667 lần**,
chữ trong node giãn theo. Có **test khoá** `maxWidth ≤ viewBox width`
([dag.test.tsx:305](../../../../frontend/src/simulations/domains/logic/dag.test.tsx#L305)).

**Cách đúng đã được ghi ngay tại đó**: giữ `scale ≈ 1`, muốn hình lớn hơn thì
**tính bố cục lớn hơn** (đơn vị viewBox = đúng pixel hiển thị), không kéo giãn
viewBox. Tức là `W`/`COL`/`RW` phải là **hàm của bề rộng khung đo được**, không
phải hằng số.

---

## E. INFORMATION DENSITY

- **Thanh điều khiển phơi 10 affordance cùng lúc** (5 nút transport + `Đặt lại` +
  chỉ số bước + slider tốc độ + thanh tua toàn chiều rộng + gợi ý phím tắt) cho
  một việc **không phải** nhiệm vụ của người học. Vượt xa ngưỡng 4 lựa chọn.
- **Hai cơ chế tua trùng nhau** (nút mũi tên và thanh tua) và **hai nút khởi động
  lại không phân biệt** (`⏮ Về đầu` → `toStart`, `↺ Đặt lại` → `resetSim`) cách
  nhau một dấu phân cách, không gì trên màn giải thích khác biệt.
- **Ba hệ đánh số phải hoà giải mỗi bước**: trục hình 0-based, chip Quan sát in
  giá trị engine thô, thuyết minh `i + 1`, mã giả 1-based — **cùng một màn hình**.
- **Câu kết in hai lần**: `.result-banner` và `.narration-bar` mang **cùng một
  chuỗi**, cách nhau ~50px, đúng khoảnh khắc peak-end đáng giá nhất.
- Điểm cần **giữ**: các điểm quyết định của người học đúng **hai** lựa chọn. Kỷ
  luật đó không được nới.

---

## F. OBSERVATION PANEL

- **P0 — panel in đáp án trước khi học sinh chạy mô phỏng.**
  [traverse-module.tsx:374-392](../../../../frontend/src/simulations/domains/network/traverse-module.tsx#L374-L392)
  render **toàn bộ** `visitedOrder` và **toàn bộ** `path` vô điều kiện — tức là ở
  bước 1/8. Module anh em **đã sửa đúng lỗi này**:
  [tree-module.tsx:485-495](../../../../frontend/src/simulations/domains/tree/tree-module.tsx#L485-L495)
  có `done ? thứ tự đầy đủ : "Đã thăm k/n"` kèm comment *"HIỆN DẦN (M17-VR1):
  … KHÔNG lộ thứ tự cuối ngay từ bước 0"*.
  Vi phạm trực tiếp `DESIGN_BRIEF §3.3`, và là đúng hình dạng
  `ARCHITECTURE_MAP §8` anti-pattern #10 (vá một bề mặt, quên bề mặt anh em).
- Chuỗi `(engine)` hiển thị nguyên văn trên màn học sinh — vi phạm §3.4.
- Panel `.notes` **vô hình** ở desktop: `.notes` tô `--canvas-soft` còn
  `.panel-right` không có nền trắng ở desktop, nên chỉ còn padding, đọc ra như
  khoảng trống ~60px không lý do.
- 300px chiều rộng cố định cho ba dòng chữ, trong khi sân khấu bị bó.

---

## G. TIMELINE

Thanh điều khiển **không** ồn về màu — nó ồn về **số lượng affordance** và về
**vị trí**: ghim đáy, z-index 50, đổ bóng, chiếm toàn chiều rộng, và ở 1366×768
nó nằm **đè lên 47px cuối của sân khấu**. Slider tốc độ đảo chiều
(`value={2800 - speedMs}`), không số, không đơn vị — mức ưu tiên thị giác của nó
cao hơn giá trị sư phạm của nó.

---

## H. EDUCATIONAL HIERARCHY

Thứ tự học tập đúng phải là: **hình → nhiệm vụ hiện tại → thao tác → phản hồi →
thuyết minh**. Thứ tự thị giác thực tế ở 1366×768 là: hình (bị cắt 47px) →
thuyết minh (**dưới nếp gấp 309–336px**) → điều khiển (ghim đáy, nổi nhất).

Nghĩa là: **thứ nổi bật nhất là transport, thứ biến mất là cơ chế.** Và bề mặt
`aria-live` duy nhất của shell chính là thứ biến mất.

Điểm sáng cần bảo vệ: nhịp cam kết (`ScanActionZone`) từ chối mang
`correctActionId` vào component nên đáp án không rò ra DOM và renderer không tự
phán — đúng bất biến #11. Sai thì đóng khung bằng bóng đèn, không phải dấu ✗.

---

## I. SHARED DESIGN RULES (rút từ bằng chứng, áp toàn danh mục)

1. **VIEWPORT OWNERSHIP.** Shell tuyên bố bề rộng của mình từ **màn hình**, không
   từ nội dung. Không `margin: auto` trên trục ngang của một flex item nếu muốn
   nó stretch.
2. **SIMULATION SCALE.** Kích thước nội tại của renderer là **sàn, không phải
   trần**. Muốn hình lớn hơn thì tính bố cục lớn hơn ở `scale ≈ 1` — **không bao
   giờ** phóng `viewBox`.
3. **STEP-SCOPED INSPECTOR.** Inspector chỉ được đọc trạng thái mà **bước hiện
   tại đã tới**. Kết quả cuối chỉ công bố ở bước cuối.
4. **ONE POSITION CONVENTION.** Một quy ước đánh số duy nhất trên toàn bộ trục
   hình · chip · thuyết minh · mã giả. Chuyển đổi chỉ ở ranh giới hiển thị.
5. **NARRATION IS ALWAYS ON SCREEN.** Bề mặt `aria-live` mang bước hiện tại
   không bao giờ được nằm dưới nếp gấp.
6. **NO UNANSWERABLE QUESTION.** Thuyết minh chỉ được đặt câu hỏi khi module có
   khai một tương tác để trả lời — nếu không thì phát biểu, đừng hỏi.
7. **LEGEND ⇔ STATE.** Chú giải chỉ liệt kê trạng thái **đang thực sự dùng ở bước
   này**, và mọi trạng thái mang nghĩa đều phải có mục chú giải (hai chiều).

---

## J. TOP 5 CHANGES

| # | Thay đổi | Owner | Mức | Vì sao đứng ở đây |
|---|---|---|---|---|
| 1 | **Shell đòi bề rộng viewport** — `width: 100%` + `max-width: 1720px` + `margin-inline: auto`, kèm điều kiện chấm mới `LAYOUT_NOT_USING_VIEWPORT` trong `diagnose-responsive.mjs` | `global.css` `.app-layout` + runner | **P0** | Sửa một dòng CSS, cải thiện **cả 22 target cùng lúc**, và đóng lỗ mà guard hiện tại không thể thấy |
| 2 | **Inspector hiện dần cho `graph_traversal`** — soi gương `tree-module`, kèm test chéo cấm mọi inspector render trường mà bước hiện tại chưa tới | `traverse-module.tsx` | **P0** | Đang phá hợp đồng sư phạm cốt lõi (§3.3); và là anti-pattern #10 đang lặp lại lần nữa |
| 3 | **Thuyết minh luôn trong màn ở nhánh màn thấp** — đưa `NarrationSlot` lên vùng ghim đáy phía trên transport; thêm loại `NARRATION_BELOW_FOLD` vào cổng chấm | `global.css` nhánh `max-height: 900px` + shell | **P1** | 1366×768 là máy phổ biến nhất; hiện cơ chế biến mất đúng lúc nó xảy ra |
| 4 | **Một quy ước đánh số** — chuẩn hoá 1-based qua một formatter hiển thị duy nhất; trục hình đánh `1…n` | `ArrayView` · `VarsView` · `decision.ts` | **P2** | Rẻ, khoá được bằng test, gỡ bỏ một câu đố không ai cố ý tạo ra |
| 5 | **Giảm tải thanh điều khiển** — gộp hai nút khởi động lại, bỏ một trong hai cơ chế tua, cho slider tốc độ một số đọc được hoặc hạ nó xuống mức phụ | `SimulationControls.tsx` | **P2** | 10 affordance cho việc **không phải** nhiệm vụ học tập |

**Không nằm trong top 5, có chủ đích:** cho renderer scale theo khung (§D.2) — giá
trị cao nhưng phải làm sau #1 (khung phải rộng trước thì mới có gì để scale vào),
và phải **thử trên đúng một renderer trước**, giữ `scale ≈ 1`, không đụng test khoá.

---

## K. COMMAND PLAN

| Cụm | Lệnh | Phạm vi chính xác |
|---|---|---|
| #1 shell width | không cần lệnh Impeccable — sửa trực tiếp 3 dòng + guard | `.app-layout` trong `global.css`; điều kiện chấm trong `diagnose-responsive.mjs` |
| #2 hiện dần | không cần lệnh Impeccable — hợp đồng sư phạm, làm trong **W4B-1B** | `traverse-module.tsx::TraverseInspector` |
| #3 thuyết minh | `/impeccable layout frontend/src/styles/global.css` | **chỉ** khối `@media (min-width:1101px) and (max-height:900px)` |
| #4 đánh số | `/impeccable clarify frontend/src/components/ArrayView.tsx` | trục + nhãn vị trí; kéo theo `VarsView`, `decision.ts` |
| #5 điều khiển | `/impeccable distill frontend/src/components/SimulationControls.tsx` | **chỉ** file này |

**Không chạy `polish` toàn app. Không chạy `init` / `shape` / `new-work` /
`document`** — ba lệnh sau có quyền ghi đè `DESIGN.md` (file tracked 498 dòng).

---

## L. CLAIM LIMITS

- **Lượt này KHÔNG đo tác động học tập.** `LEARNER_IMPACT_NOT_EVALUATED` giữ
  nguyên. Điểm 25/40 là **điểm heuristic thiết kế**, không phải kết quả học tập,
  và không được trích dẫn như vậy ở bất kỳ đâu.
- `CURRICULUM_SUPPORT_PARTIAL` giữ nguyên — lượt này không đụng độ phủ chương
  trình.
- **Assessment B không hoàn tất** (chết vì giới hạn phiên). Phần detector đã chạy
  lại inline; phần **browser overlay không có**, và phần đo hình học độc lập của
  B **không tồn tại** — nên các số hình học ở §C, §D đều đến từ artifact W4B-1A
  và từ Assessment A, không có nguồn thứ ba đối chứng.
- **`OBSERVATION_SPARSE` chưa kết luận được** — phép đo hiện tại không tách được
  chiều cao *nội dung* panel khỏi chiều cao ô lưới.
- Các con số tương phản màu và một số quan sát chi tiết ở §B/§E là **của
  Assessment A**, tôi chưa kiểm lại từng cái.
- **Khiếm khuyết đã biết của chính công cụ đo** (Assessment A phát hiện, tôi đã
  xác nhận trong mã): `diagnose-responsive.mjs` dùng **cổng CDP cố định 9337** và
  chỉ `chrome.kill()` trên hai đường thoát bình thường — không có `finally`. Hai
  lượt chạy song song, hoặc một lượt ném lỗi, sẽ để lại Chrome mồ côi mà lượt sau
  **âm thầm bám vào**. Nặng hơn: dấu vân tay §5 chỉ kiểm **cấu trúc** (`.app-layout`
  … có mặt) chứ **không kiểm danh tính** (đang mở đúng mô phỏng nào), nên không
  phát hiện được ca bám nhầm. Hai agent của lượt này chạy script đó **đồng thời**
  ⇒ số hình học của chúng có nguy cơ nhiễm chéo.
  Bằng chứng W4B-1A đã commit **không** bị ảnh hưởng theo cùng cơ chế (các lượt
  chạy tuần tự, đều thoát bình thường và tự kill Chrome) — nhưng **guard hiện tại
  không thể chứng minh điều đó**, và đó chính là lỗ cần vá.
