# ALGOSIM — SHARED-SHELL USABILITY + VISUAL POLISH (patch wave)

**CHƯA COMMIT.** Working tree còn nguyên để duyệt. Baseline `b7ec7dc`, nhánh `main`.

Không redesign. Không đụng engine / state / timeline / LLM / schema / capability.
Không thêm module, family, target. Không thêm thư viện UI. `UI_INTERACTION_BASELINE.md`
giữ nguyên — bản vá này **thực hiện** nó, không sửa nó.

## 0. Kết quả kiểm tra

| Cổng | Trước | Sau ba fix | Sau ba quyết định cuối |
|---|---|---|---|
| `npx vitest run` | 728 pass | 737 pass | **752 pass** (+24 so với baseline, 0 đỏ) |
| `npm run build` (`tsc -b`) | xanh | xanh | **xanh** |
| `pytest -q` | 1129 · 2 skip | 1129 · 2 skip | **1129 · 2 skip** (backend không bị đụng) |
| `git diff --check` | — | sạch | **sạch** |
| Chrome thật | 1440×1000 · 768×900 | +1024×768 | **3 viewport + bàn phím thật** |

Ảnh: `shots/` (trước, 72) · `shots-after/` (sau ba fix, 108) ·
`shots-final/` (sau ba quyết định cuối, 39).
Số liệu: `captures.json` / `captures-after.json` ·
`narrow-controls-probe.json` / `narrow-controls-probe-after.json` ·
`dag-acceptance.json`.

---

## 1. Correctness / usability — thay đổi CÓ HỆ QUẢ CHỨC NĂNG

### FIX-1 · Thanh điều khiển tụt dưới nếp gấp ở màn hẹp → **đã hết**

`RESPONSIVE_DEFECT` · chỉ CSS, không đổi DOM module, desktop không đổi một pixel.

Nguyên nhân: `@media (max-width: 1100px)` đặt `.app-layout { height: auto }` (đúng —
màn hẹp phải cuộn được), nhưng điều đó làm `panel-controls` thôi là hàng lưới ghim
đáy và trôi theo chiều cao nội dung. Cách chữa: `position: sticky; bottom: 0` —
giữ nguyên luồng cuộn (khác `fixed`: không cần bù padding, cuộn tới đáy vẫn thấy
hết nội dung) mà vẫn dán thanh vào đáy màn hình. `z-index: 50` để drawer Quan sát
(40) trượt **ra sau** thanh điều khiển.

Đo lại ở 768×900 (`narrow-controls-probe-after.json`), 5/5 target, mọi bước:

| Target | Trước: dưới nếp gấp | Sau |
|---|---|---|
| `algorithm.bubble_sort` (bước có ô dự đoán) | **99px** — click KHÔNG ăn | **0px** — `visible=true` |
| `network.protocol_encapsulation` (bước 5) | **21px** | **0px** |
| ba target còn lại | 0px | 0px |

Bằng chứng mạnh nhất là con trỏ bước: **trước**, ba lần bấm `Tiến` liên tiếp giữ
`cursor` đứng yên ở 1; **sau**, cùng kịch bản cho `cursor` 1 → 2 → 3 → 4.
Ảnh: `shots/bubble-sort-narrow-2-forward.png` (6 nút ngoài khung) →
`shots-after/bubble-sort-narrow-2-forward.png` (thanh dán đáy, đang ở bước 4/40).
Drawer không còn che controls: `shots-after/bubble-sort-narrow-7-observer-toggled.png`.

### FIX-2 · Thuyết minh trở thành khe của shell

`STRUCTURAL_INCONSISTENCY` · hợp đồng module + shell; **không** đụng engine/state/trace.

Trước: **bốn** hiện thực song song cho cùng một vai trò — `.narration-bar` (11 tệp),
`.notes` ở `logic/dag-module.tsx`, bản dựng riêng trong `database/table-module.tsx`,
và `.notes` ở `tree/tree-module.tsx` (cái thứ tư này audit chưa thấy vì chỉ soi 5
target đại diện). Hệ quả đo được: `narration_bar_count = 0` ở `boolean_dag` và
`relational_table_query` dù cả hai vẫn hiện một câu thuyết minh.

Nay: `SimulationModule.narrate?(state, config): Narration | null` — module trả
**chuỗi**, `SimulationWorkspace` dựng **một** khe ngay dưới sân khấu.

Kèm theo, ba vai trò từng dùng chung một lớp CSS được tách đúng tên:

| Lớp | Vai trò | Ai sở hữu |
|---|---|---|
| `.narration-bar` | tường thuật **bước hiện tại** | **shell** |
| `.feedback-bar` | phản hồi cho **thao tác vừa rồi** (rule engine sinh) | module |
| `.stage-affordance` | hướng dẫn **bấm/kéo cái gì** | module |

Đo lại: `narration_bar_count = 1` ở **cả ba viewport** cho cả `boolean_dag` lẫn
`relational_table_query`.

**Bốn hệ quả kèm theo, đều là được:**

1. **2D và 3D hết chép đôi.** `network/ui.tsx` + `ui3d.tsx` và `encap-ui.tsx` +
   `encap-ui3d.tsx` mỗi cặp từng có hai dòng narration giống hệt nhau phải giữ
   đồng bộ bằng tay. Nay một nguồn. Lời hứa "2D và 3D kể cùng một câu" đúng theo
   **cấu trúc**, không nhờ hai bản sao tình cờ khớp.
2. **Luật ẩn thuyết minh ở bước cuối** (W2C-VR3 / W3-VR1: không nói hai lần cùng
   một câu với băng kết quả) nay là **một luật ở một chỗ** — `narrate` trả `null`.
   Trước đó là ba đoạn `if` chép tay ở ba module.
3. **Có `aria-live`.** Khe dùng `role="status"` + `aria-live="polite"`; trước bản
   này workspace **không có vùng aria-live nào** (0/56 lượt đo), người dùng đọc
   màn hình bấm `Tiến` không nghe gì.
4. **Có răng.** Hai guard mới: quét mã nguồn (`ui-hygiene.test.ts`) cấm module tự
   dựng `.narration-bar` và chốt `SimulationWorkspace.tsx` là nơi duy nhất dựng
   khe; guard hợp đồng (`domains.test.ts`) bắt mọi module **có timeline** phải
   khai `narrate()`. Đây chính là thứ audit nói là đang thiếu.

### FIX-3 · `boolean_dag` — tương tác cốt lõi nay tự giới thiệu

`PEDAGOGICAL_VISIBILITY_DEFECT` · chỉ thêm chữ, cơ chế không đổi.

Thêm đúng câu đã chốt: *"Bấm A, B hoặc C để đổi giá trị đầu vào và quan sát tín
hiệu lan truyền qua các cổng."* Cộng `aria-pressed` trên các nút toggle (trước
đây công nghệ hỗ trợ không biết chúng là nút hai trạng thái).

### Sơ đồ node-edge cho `boolean_dag` — **đã triển khai**

Điều kiện của đề bài đều thoả, nên làm; nếu phải đổi data model thì đã dừng và báo.

- **Không state mới, không engine thứ hai.** Toàn bộ dẫn xuất từ
  `config.inputs/gates/output` + `values` + `nodeOutputs` + `steps` **đã có**.
- **Bố cục là của renderer** (luật renderer-neutral M7.FREEZE): độ sâu phụ thuộc
  và toạ độ tính ngay trong component, không một trường nào chạm engine state.
- **Không lộ đáp án sớm:** cổng chưa tới lượt hiện `?` — đúng idiom sẵn có của
  bảng cổng, không phải luật thứ hai. Khoá bằng test: ở bước intro có đúng 3 dấu
  `?` (bằng số cổng), ở bước cuối không còn dấu nào.
- **Bảng chân trị vẫn ở panel Quan sát**, và **bảng cổng vẫn còn** — nó là
  `gate_table_with_engine_outputs`, một `renderer_semantic_requirement` trong hợp
  đồng authenticity của target này, không được bỏ.
- Màu dây (xanh = 1) **không** là tín hiệu duy nhất: mỗi node in kèm chữ số.

Ảnh: `shots/boolean-dag-desktop-2-forward.png` → `shots-after/boolean-dag-desktop-2-forward.png`.

---

## 2. Visual polish — KHÔNG đổi hành vi

| # | Thay đổi | Vì sao |
|---|---|---|
| POLISH-1 | `.workspace-card` thôi `flex: 1`, thay bằng `min-height: 320px` | `flex: 1` kéo thẻ cao bằng cả cột nên module ít nội dung để lại mảng trắng chiếm gần nửa màn hình **bên trong** thẻ — trông như hỏng. Nay nội dung quyết định chiều cao, có sàn để không bị bẹp. |
| POLISH-1 | `.sim-stage { min-height: 180px }` | Sàn, **không phải** trần: không ép chiều cao cố định lớn — đó chính là thứ đẻ ra khoảng trắng chết. |
| POLISH-2 | tiêu đề 22px → **24px**; mô tả ngắn xuống hẳn dòng dưới; badge miền 12px → **11px** | Ba mức phân cấp rõ ràng thay vì ba thứ nằm cùng một dòng cạnh tranh nhau. |
| POLISH-2 | panel Quan sát: mục AI đẩy xuống đáy, khoảng cách section rõ | Nội dung module và mục AI trước đây trôi liền một mạch. |
| POLISH-3 | gom nhóm thanh điều khiển + `.control-divider` | **Giữ nguyên 6 nút, đúng thứ tự, đúng nhãn, không thêm nút.** Chỉ bọc `[về đầu · lùi · chạy · tiến · đến cuối]` thành một khối, tách khỏi `Đặt lại` / tiến độ / tốc độ. |
| POLISH-3 | `.btn-icon:disabled` xám trung tính, `opacity: 1` | Nút bước hết đường đi là trạng thái **bình thường**, gặp liên tục; mờ 40% vừa khó đọc vừa trông như hỏng. Cùng luật với `.btn-primary:disabled`, và nay cũng có test khoá. |
| POLISH-4 | `.starter-card { min-height: 76px }`; nhóm cách nhau `--sp-xl`; tiêu đề nhóm 12px→13px, đậm và tối hơn | Thẻ hết cao thấp so le; Thư viện đọc thành **từng nhóm** thay vì một tấm thảm thẻ. |
| POLISH-5 | `.input-toggle-row` | Ba nút toggle của `boolean_dag` trước đây nằm trong `<div>` trần nên dính sát nhau. |

Cấu trúc Trang chủ và Thư viện **giữ nguyên**. Không dashboard, không chatbot,
không neon/AI, không animation trang trí.

---

## 3. Responsive — ba viewport

| | 1440×1000 | 1024×768 | 768×900 |
|---|---|---|---|
| Tràn ngang | không | không | không |
| Controls trong màn hình, mọi bước | có (ghim lưới) | có (sticky) | có (sticky) |
| Drawer che controls | — | không | không |

`0/108` lượt đo có `page_overflows_horizontally = true`;
`0` lượt có `controls_all_in_viewport = false`.

1024×768 là viewport **mới được kiểm** ở lượt này (baseline chỉ có 2). Nó nằm dưới
ngưỡng 1100px nên nhận cùng cách xử lý màn hẹp: Quan sát thành drawer, controls sticky.

---

## 4. Việc KHÔNG làm (giữ nguyên phạm vi)

- **`⌂ Góc nhìn`** — ký tự Unicode làm icon ở `network/ui3d.tsx:369` và
  `encap-ui3d.tsx:358`. Đã sửa file đó ở dòng ngay bên cạnh nhưng **cố ý không
  đụng**: nó nằm ngoài ba fix và ngoài shell polish (§ khoá phạm vi). Vẫn là
  `COSMETIC_ONLY / MINOR` đang hoãn; khi sửa **phải** thêm `⌂` vào cả hai danh
  sách cấm (`ux-shell.test.tsx`, `ui-hygiene.test.ts`) — U+2302 hiện lọt qua cả hai.
- **Khe Mục tiêu học tập / Nhiệm vụ** — vẫn chưa mở. Lý do không đổi: 3/5 target
  đại diện có **0** case khai `learning_objective`, mở khe bây giờ là mời người ta
  bịa mục tiêu.
- **Generic `rule_scene`** giữ câu hướng dẫn thao tác trong renderer (chỉ với cảnh
  một khung) vì nó phụ thuộc chế độ Chỉnh sửa — trạng thái **trình bày** cục bộ,
  không nằm trong engine state. Đưa nó vào state để shell đọc được sẽ phá luật
  renderer-neutral. Thuyết minh **bước** của generic thì đã về khe chung.

---

## 5. Hai ghi chú trung thực về quá trình đo

1. **`captures.json` của lượt BEFORE từng bị ghi đè.** Script chụp ghi tệp số liệu
   ở thư mục cha của `--out`, nên lượt after đã đè lên tệp trước. Đã khôi phục
   bằng cách dựng `git worktree` tại `b7ec7dc` (mã nguồn sạch, **không** đụng
   working tree đang sửa) và chụp lại đúng bộ 2 viewport cũ. Ảnh before trong
   `shots/` không bị ảnh hưởng. Tệp nay tách rõ: `captures.json` (before) ·
   `captures-after.json` (after).
2. **Lượt chụp 1024×768 đầu tiên sai và đã bị loại.** Thẻ "đóng gói" nằm dưới nếp
   gấp trang Thư viện ở chiều cao 768 nên cú click theo toạ độ không ăn — ảnh
   `encapsulation-laptop-*` khi đó ghi nhầm **trang Thư viện**. Đã sửa harness
   (cuộn phần tử vào màn hình rồi mới đo toạ độ) và chụp lại toàn bộ. Đây là lỗi
   dụng cụ đo, không phải lỗi sản phẩm.

Dọn dẹp còn lại: thư mục `d:/tmp/algo-sim-before/` (bản sao worktree tạm) đã được
gỡ khỏi đăng ký git nhưng **chưa xoá được trên đĩa** — xoá tay khi tiện.

---

## 5b. Final review decisions

Ba quyết định chốt sau khi xem ảnh của bản vá trên. Tất cả đều **chỉ ở tầng trình
bày/tương tác**: engine, state, timeline, schema, LLM, số lượng target — không đổi.

### QĐ-1 · Bỏ hẳn "Hỏi AI về bước này" khỏi workspace

Panel Quan sát không còn control AI nào. Không thay bằng chatbot / "Trợ lý AI" /
"Giải thích bằng AI" / ô nhập mới.

Lý do sản phẩm: narration + Observer phải **tự đủ** để giải thích bước; workspace
là nơi học sinh làm việc với mô phỏng; và không nên còn một đường tiêu token ngay
cạnh timeline. AI lùi hẳn về giai đoạn hiểu đề.

Phạm vi: **chỉ gỡ phần render ở frontend**. Endpoint `/api/explain` và
`getExplainContext` của các module **giữ nguyên** — backend không bị đụng một dòng.
`AIHelpPanel.tsx` nay không còn ai gọi; **cố ý không xoá** vì tiêu chí cho phép xoá
là *"TypeScript/lint yêu cầu"*, mà `tsc` không báo lỗi. Nếu muốn dọn hẳn, đó là
một quyết định riêng — nêu ở §10.

Danh sách AI trong `UI_INTERACTION_BASELINE.md §5` nay là **danh sách đóng bốn
mục**. Audit READ-ONLY tại `b7ec7dc` **giữ nguyên** như bằng chứng lịch sử: nó ghi
đúng những gì có mặt lúc đó.

### QĐ-2 · `boolean_dag` chỉ còn MỘT bộ A/B/C — chính node là control

Trước: node A/B/C trong sơ đồ (chỉ để xem) **và** hàng nút `A:1 · B:0 · C:1` bên
dưới (để bấm) — trùng thông tin, mơ hồ vùng nào bấm được.
Sau: hàng nút bỏ hẳn; chính node trong sơ đồ là control.

Mỗi node đầu vào mang đủ hợp đồng: `role="button"` · `tabindex="0"` ·
`aria-pressed` · tên khả truy cập *"Đầu vào A, giá trị 1, bấm để đổi"* ·
Enter/Space · focus ring · hover + con trỏ · luôn in chữ A/B/C **và** chữ số 0/1
(màu không phải tín hiệu duy nhất). Cổng AND/NOT/OR **không** thành nút — giá trị
của chúng thuộc về engine.

Dùng lại **đúng** action `{ type: "toggle" }` sẵn có. Không action mới, không
state mới, không engine thứ hai.

> **Một lỗi thật do lượt nghiệm thu Chrome bắt được.** Space trên node đầu vào vừa
> đổi giá trị, **vừa** bật "Tự chạy" — vì Space là phím tắt play/pause toàn cục.
> Timeline chạy mất và node bị khoá (`busy`) ngay sau đó. Đã sửa hai lớp: node
> `stopPropagation()` ở tầng native, và handler phím tắt toàn cục bỏ qua sự kiện
> phát từ trong `[role="button"]`. Có guard mã nguồn kèm theo.
> Lỗi này chỉ lộ ra khi bấm phím **thật** — SSR không có sự kiện bàn phím.

### QĐ-3 · Sơ đồ là sân khấu, bảng cổng là chi tiết

Bảng `Cổng · Phép · Vào · Ra` **giữ nguyên dữ liệu** (nó là
`gate_table_with_engine_outputs` — yêu cầu renderer trong hợp đồng authenticity).
Chỉ hạ trọng lượng thị giác: tiêu đề nhỏ "CHI TIẾT CÁC CỔNG", chữ 13px, header
11px chữ hoa nhạt, hàng thưa hơn bằng hairline, `max-width: 520px`, và đặt **ra
ngoài `.sim-stage`**, sát thuyết minh. Không accordion, không ẩn dữ liệu, không
đổi cấu trúc dữ liệu. Bảng chân trị **vẫn ở panel Quan sát**, không đụng tới.

Đo trên ảnh nghiệm thu (desktop): sơ đồ ở `top = 219px`, bảng ở `top = 400px`;
diện tích sơ đồ `49 056 px²` so với bảng `17 576 px²` — mắt gặp sơ đồ trước, gấp
~2,8 lần diện tích.

> Một lỗi trình bày kèm theo đã sửa: repo **không có** rule `.data-table` cơ sở
> nào, nên bảng trước giờ chỉ giãn ra nhờ tình cờ là flex-item của `.sim-stage`.
> Đưa ra ngoài, `width: auto` co bảng lại và các cột dính vào nhau. Nay khai
> `width` + padding ngang tường minh.

### Nghiệm thu Chrome — bằng chứng

`dag-acceptance.json` + `shots-final/` (39 ảnh, 3 viewport). Chuột thật
(`Input.dispatchMouseEvent`), **bàn phím thật** (`Input.dispatchKeyEvent`).

| Pha | Kết quả đo (desktop; laptop/narrow giống) |
|---|---|
| 1 · đầu | đúng **3** control đầu vào, `legacy_toggle_row = false`, sơ đồ `?`×3, bảng chân trị `?`×8 |
| 2 · click chuột node A | `A: 1 → 0`, `aria-pressed true → false`, engine tính lại downstream |
| 3 · Space trên B | `B: 0 → 1`; Enter trên B → `1 → 0`; **cursor vẫn 0** (không còn cướp phím) |
| 4 · giữa (bước 3/5) | sơ đồ còn `?`×1, cổng đang xét được viền primary |
| 5 · cuối (bước 5/5) | `?` = 0 ở cả sơ đồ lẫn bảng cổng; bảng chân trị mới mở cột "Ra" |
| 6 · Đặt lại | `values` về `A:1 B:0 C:1`, `cursor = 0`, `?` quay lại 3 và 8 |
| 7 · Observer | **không** có "Hỏi AI"; bảng chân trị đầy đủ |

Shell trên **5 target × 3 viewport = 15/15 đạt**: `controls_in_viewport = 6/6`,
`narration_count = 1`, `ai_control_present = false`, không tràn ngang, sân khấu
hiển thị, không màn trắng. 2D↔3D của `protocol_encapsulation`: `cursor 4 → 4`
(không đổi), narration vẫn đúng 1. Drawer ở laptop và narrow: `z_controls = 50`
vs `z_drawer = 40`, `elementFromPoint` giữa thanh điều khiển trả về **chính thanh
điều khiển** ⇒ drawer không che.

---

## 6. Tệp đã đổi (32 tệp, không tệp backend nào)

**Hợp đồng + shell (4):** `simulations/types.ts` · `components/SimulationWorkspace.tsx`
· `components/SimulationControls.tsx` · `styles/global.css`

**Module — bỏ narration tự dựng, khai `narrate()` (13):** algorithm (`index.ts`,
`ui.tsx`, `program-module.tsx`, `scan-module.tsx`) · binary (`index.ts`, `ui.tsx`,
`encoding-module.tsx`) · logic (`index.ts`, `ui.tsx`, `dag-module.tsx`) ·
network (`index.ts`, `ui.tsx`, `ui3d.tsx`, `encap.ts`, `encap-ui.tsx`,
`encap-ui3d.tsx`) · database (`table-module.tsx`) · tree (`tree-module.tsx`) ·
generic (`index.ts`, `ui.tsx`)

**Test (8):** `ui-hygiene.test.ts` (+4 guard mới) · `domains.test.ts` (+1) ·
`logic/dag.test.tsx` (+3) · `logic/render.test.tsx` · `binary/render.test.tsx` ·
`network/render.test.tsx` · `network/render3d.test.tsx` ·
`network/encap-render3d.test.tsx`

Các test cũ được sửa **giữ nguyên ý định**, chỉ chuyển chỗ khẳng định từ HTML của
renderer sang `narrate()` — nơi chuỗi thật sự được sinh ra. Riêng test
*"2D và 3D kể cùng một narration"* nay khẳng định **mạnh hơn**: một nguồn duy nhất,
và **không** renderer nào còn giữ bản sao.
