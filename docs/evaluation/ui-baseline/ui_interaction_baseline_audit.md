# ALGOSIM — UI / INTERACTION BASELINE AUDIT

**Lượt READ-ONLY.** Không sửa một dòng production code nào. Không thêm module /
family / target. Không commit. Không gọi LLM (backend không chạy — xem §3).

| | |
|---|---|
| Nhánh · HEAD | `main` · `b7ec7dc` |
| Working tree | sạch, trừ `docs/evaluation/m17/pedagogical-alignment/` (untracked, **không đụng tới**) |
| Phân loại task | **SUPPORTING** (đánh giá + tài liệu; không tạo năng lực mới) |
| Phạm vi | 5 target đại diện · 2 viewport · 72 ảnh · 2 tệp dữ liệu đo |
| Bằng chứng | `shots/` · `captures.json` · `narrow-controls-probe.json` |

Phương pháp: Chrome **thật** (headless) qua CDP. Viewport đặt **trước khi trang
dựng** và nạp lại trang cho từng viewport (bài học VIS-003, RC1 §E1). Mọi thao
tác Tiến / Lùi / Tự chạy / Dừng / Đến cuối / Đặt lại / toggle / 2D–3D là **sự
kiện chuột thật** (`Input.dispatchMouseEvent`) lên chính nút của sản phẩm. Store
chỉ dùng để **nạp đề** (3 target không có trong Thư viện) và **đọc state đối
chiếu** — không thay cho thao tác người dùng.

---

## 1. Executive verdict

### `KEEP_WITH_TARGETED_FIXES`

Khung giao diện hiện tại **đúng và giữ được**. Năm module đại diện — bốn miền
khác nhau, hai chế độ hiển thị, bốn kiểu tương tác khác nhau — chạy trên **cùng
một product shell**, và điều đó đo được chứ không phải cảm nhận:

- **56/56** lượt đo trong workspace (5 target × 2 viewport × các pha) cho ra
  **đúng 6 nút điều khiển, đúng thứ tự, đúng nhãn**: `Về đầu · Lùi một bước ·
  Tự chạy · Tiến một bước · Đến cuối · Dựng lại từ đầu`.
- **56/56** có thanh tua (`aria-label="Tua đến bước"`), chỉ báo `Bước n / N`,
  điều khiển tốc độ, gợi ý phím tắt.
- **56/56** có header sản phẩm, nhãn miền tiếng Việt, tên mô phỏng; **28/28**
  lượt panel Quan sát đang mở đều cùng một chỗ, cùng tiêu đề `QUAN SÁT`.
- **0/56** tràn ngang ở cả hai viewport.
- 3D là **renderer trong cùng cái vỏ đó**, không phải màn hình riêng (§11).

Không chọn `KEEP_AS_BASELINE` vì có ba lỗi thật phải sửa trước pilot (§12). Không
chọn `STRUCTURAL_REVISION_REQUIRED` vì **chỉ một** thành phần chung thực sự không
nhất quán (thuyết minh — §5), phần còn lại của vỏ đã thống nhất; sửa nó là một
việc gom nhỏ, không phải chỉnh lại khung. Không chọn `REDESIGN_REQUIRED`: không
có target nào mà khung hiện tại không đỡ nổi.

**Câu trả lời cho 12 điều kiện hoàn thành nằm ở §12.13.**

---

## 2. Product identity

AlgoSim đọc như **công cụ học tập**, không phải ứng dụng chat. Đo trên toàn bộ
lượt chụp:

| Dấu hiệu "AI quá" | Kết quả |
|---|---|
| ô chat chiếm trung tâm | **không** |
| avatar robot | **không** |
| bong bóng hội thoại | **không** |
| sparkle / gradient AI | **không** |
| chữ "AI generated" lặp lại | **không** |
| AI explanation dài che sân khấu | **không** |
| kết quả giống câu trả lời chatbot | **không** — kết quả là state + timeline |

Trong workspace, từ "AI" xuất hiện **đúng một lần**: mục thu gọn *"Hỏi AI về bước
này"* ở đáy panel Quan sát, mặc định **đóng** (`aria-expanded="false"` ở **28/28**
lượt panel đang mở). Đây là R0 được phản chiếu đúng lên giao diện: LLM không sở hữu runtime,
nên nó cũng không được sở hữu diện tích màn hình.

Bản sắc thị giác: nền sáng, một accent xanh cấu trúc, chữ gần-đen, icon SVG,
không emoji. Ngôn ngữ hướng học sinh ("Em muốn khám phá bài toán nào?", "Bổ sung
dữ liệu còn thiếu vào đề rồi gửi lại").

---

## 3. User flow

**Hai màn hình sản phẩm chính:**

1. **Trang chủ / cửa vào** (`view = home`) — một ô nhập đề, một hành động chính
   *"Phân tích đề bằng AI"*, 6 gợi ý, 1 thẻ "Tiếp tục học". Đây là nơi **duy
   nhất** AI đứng ở trung tâm, và đúng như vậy: đây là lúc AI làm việc của nó.
2. **Workspace / phiên học** (`view = workspace`) — sân khấu + Quan sát + điều
   khiển. AI lùi xuống một dòng thu gọn.

Hai mặt phụ: **Thư viện** (danh mục đầy đủ, có lọc) và **Lịch sử** (mở lại
zero-AI).

Ba đường vào workspace: (a) dán đề → AI phân tích; (b) chọn thẻ ở Trang chủ /
Thư viện; (c) mở lại từ Lịch sử.

**Quan sát về khả năng tiếp cận danh mục.** 3/5 target đại diện —
`logic.boolean_dag`, `database.relational_table_query`,
`algorithm.bounded_control_flow` — khai `reachability = [registered,
ai_reachable_public]` **không có** `library_discoverable`. Tức là học sinh chỉ
tới được chúng bằng cách **dán đề**, không tìm thấy trong Thư viện. Đây là một
**quyết định phạm vi danh mục đã khai tường minh** trong descriptor, không phải
lỗi giao diện — nên §14 xếp nó ra ngoài phạm vi lượt này, nhưng nó đáng được
quyết định có ý thức trước pilot (giáo viên demo sẽ tìm chúng trong Thư viện).

**Trạng thái xuống cấp trung thực.** Lượt đo chạy với backend **không chạy**.
Sản phẩm không vỡ: Trang chủ hiện dải *"Máy chủ phân tích chưa chạy — vẫn dùng
được các mô phỏng mẫu bên dưới"* và toàn bộ đường offline (Thư viện, Lịch sử,
engine tất định) vẫn hoạt động đầy đủ. Đây là hành vi đúng và nên **đưa vào
baseline**.

---

## 4. Shared shell

Đánh giá 12 thành phần theo §5 của đề bài. `BẮT BUỘC` = đề nghị đưa vào baseline.

| # | Thành phần | Đã có | Nhất quán 5 module | Phục vụ học tập | Baseline |
|---|---|---|---|---|---|
| 1 | Header sản phẩm | ✅ | ✅ 20/20 | gián tiếp (điều hướng) | **BẮT BUỘC** |
| 2 | Tên mô phỏng | ✅ | ✅ 20/20 (badge + title + hint) | ✅ | **BẮT BUỘC** |
| 3 | Mục tiêu học tập | ❌ **không có ở đâu** | — | ✅ nếu có | **BẮT BUỘC KHI CÓ DỮ LIỆU** (§12) |
| 4 | Nhiệm vụ quan sát/thao tác | ❌ **không có ở đâu** | — | ✅ nếu có | **BẮT BUỘC KHI CÓ DỮ LIỆU** |
| 5 | Sân khấu mô phỏng | ✅ | ✅ (module sở hữu nội dung) | ✅ | **BẮT BUỘC** |
| 6 | Panel Quan sát | ✅ | ✅ vị trí + tiêu đề; ⚠️ **độ dày nội dung chênh lệch lớn** | ✅ | **BẮT BUỘC** |
| 7 | Thuyết minh bước hiện tại | ✅ về mặt thị giác | ❌ **ba cách hiện thực khác nhau** | ✅ | **BẮT BUỘC — cần gom** |
| 8 | Timeline | ✅ | ✅ 20/20 | ✅ | **BẮT BUỘC** |
| 9 | Điều khiển chung | ✅ | ✅ 20/20 đủ 6 nút đúng thứ tự | ✅ | **BẮT BUỘC** |
| 10 | Interaction riêng | ✅ | ✅ chỉ hiện khi module thật sự khai | ✅ | **TÙY CHỌN theo capability** |
| 11 | Trạng thái lỗi/từ chối | ✅ | ✅ 4 loại tiêu đề, không rò token kỹ thuật | ✅ | **BẮT BUỘC** |
| 12 | Responsive narrow | ✅ một phần | ⚠️ **thanh điều khiển tụt dưới nếp gấp** | ✅ | **BẮT BUỘC — cần sửa** |

**Ba nhận xét quan trọng nhất:**

- **#3 + #4 không tồn tại.** Ở cả 20 lượt đo, không có một chuỗi nào khớp
  `Mục tiêu`, `Em sẽ học`, `Yêu cầu cần đạt`, `Nhiệm vụ`, `Việc của em`. Học sinh
  mở workspace ra và thấy **cơ chế**, nhưng không thấy **mình cần học gì** hay
  **cần làm gì**. Đây là khoảng trống lớn nhất so với khung mong muốn.
- **#7 chỉ nhất quán ở bề mặt.** Xem §5.
- **#6 nhất quán về khung nhưng không về mật độ.** `bubble_sort` có thẻ "XÁC ĐỊNH
  BÀI TOÁN" (INPUT/OUTPUT/THUẬT TOÁN/DỮ LIỆU) + panel mã giả 6 dòng;
  `relational_table_query` chỉ có ba câu. Không xếp là lỗi — hợp đồng cho module
  sở hữu nội dung quan sát — nhưng nó tạo cảm giác hai sản phẩm khác nhau và nên
  được nói rõ trong baseline (§5).

---

## 5. Module stage contract

### Ranh giới đang có trên thực tế

**Shell đang thật sự sở hữu:** bố cục 2 cột + footer, header sản phẩm, nhãn miền
+ tên mô phỏng, container panel Quan sát, timeline + 6 nút điều khiển + tốc độ +
phím tắt, khung 2D/3D toggle, `PredictionBar` (dùng chung, ngoài renderer),
trạng thái từ chối, drawer responsive.

**Module đang thật sự cung cấp:** nội dung sân khấu, dữ liệu quan sát
(`Inspector`), nội dung thuyết minh, đánh dấu ngữ nghĩa, action tuỳ chọn,
renderer 3D tuỳ chọn.

Hướng phụ thuộc đúng: `types ← registry ← store ← components`; renderer chỉ ĐỌC
state và phát `SimAction`. Không có module nào tự dựng layout riêng, tự đổi vị trí
điều khiển, hay tự tính lại kết quả trong renderer.

### Chỗ ranh giới bị rò: THUYẾT MINH

Thuyết minh bước hiện tại là **thành phần chung về ý nghĩa nhưng module-owned về
hiện thực**, với **ba cách khác nhau**:

| Cách | Ai dùng | Bằng chứng |
|---|---|---|
| `<div className="narration-bar">` | algorithm (program, scan, ui), binary (encoding, ui), generic, network (2D **và** 3D) | 11 tệp |
| `<p className="notes">` | `logic/dag-module.tsx:305` | narration nằm trong lớp CSS dùng cho *ghi chú phụ* |
| dựng riêng trong module | `database/table-module.tsx:681` | `narration_bar_count = 0` ở 12/12 lượt đo |

Hệ quả đo được: `narration_bar_count` = 1 với bubble_sort / bounded_control_flow /
encapsulation, = **0** với boolean_dag và relational_table_query — dù cả năm đều
hiển thị một câu thuyết minh cho bước hiện tại.

Hợp đồng authenticity làm rõ **đúng bản chất** vấn đề: `narration_per_step` là
`renderer_semantic_requirement` bắt buộc của **cả năm** target đại diện. Nghĩa là
yêu cầu *"phải thuyết minh từng bước"* đã tồn tại và có hiệu lực — thứ **không**
tồn tại là ràng buộc về **CÁCH và CHỖ** dựng câu đó. Hợp đồng nói *phải có*,
không nói *ở đâu*; nên ba hiện thực song song vẫn thoả hợp đồng trong khi học
sinh nhận ba trải nghiệm khác nhau, và module thứ 23 vẫn có thể tự chế cách thứ
tư mà không test nào đỏ.

> **Đính chính (2026-08-04).** Bản đầu của mục này viết rằng `narration_per_step`
> *không* nằm trong yêu cầu của bốn target ngoài `bubble_sort`. Sai — do đọc một
> kết quả `grep` bị cắt cụt. Cả năm target đều khai yêu cầu này; kiểm lại bằng
> `capability-descriptors.json`. Kết luận của mục không đổi (thuyết minh cần một
> khe dùng chung), nhưng lý do đúng là *thiếu ràng buộc về vị trí*, không phải
> *thiếu ràng buộc về sự tồn tại*.

Một mô phỏng từng bước mà không nói bước hiện tại đang làm gì thì chỉ còn là hoạt
hình. Đây là lý do §12 xếp việc gom thuyết minh về shell là **fix #2**.

---

## 6. Desktop baseline (1440 × 1000)

Khung chuẩn, đo trên cả 5 target:

```
┌─ nav-bar 57px ─────────────────────────────────────────────────────┐
│ AlgoSim              Trang chủ  Thư viện  Lịch sử  │  [Quan sát ▣] │
├────────────────────────────────────────┬───────────────────────────┤
│ panel-center (1fr)                     │ panel-right (300px)       │
│ ┌ workspace-card ────────────────────┐ │ QUAN SÁT                  │
│ │ [BADGE MIỀN]  Tên mô phỏng   hint  │ │ ┌ Inspector (module) ───┐ │
│ │ ────────────────────────────────── │ │ │ … nội dung theo miền │ │
│ │  SÂN KHẤU (module sở hữu)          │ │ └──────────────────────┘ │
│ │  ────────────────────────────────  │ │ ▸ Hỏi AI về bước này     │
│ │  Thuyết minh bước hiện tại         │ │   (thu gọn, mặc định ĐÓNG)│
│ │  [PredictionBar nếu module khai]   │ │                           │
│ └────────────────────────────────────┘ │                           │
├────────────────────────────────────────┴───────────────────────────┤
│ panel-controls (GHIM ĐÁY — grid row cố định)                       │
│ ⏮ ◀ [▶ Tự chạy] ▶ ⏭  [↻ Đặt lại]  Bước n/N     Tốc độ ▬▬  ←→ Space│
│ ▬▬▬▬▬▬▬▬▬▬▬▬▬ thanh tua toàn chiều rộng ▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬ │
└────────────────────────────────────────────────────────────────────┘
```

`height: calc(100vh - 57px)` + `grid-template-rows: minmax(0,1fr) auto` ⇒ thanh
điều khiển **luôn ghim đáy màn hình**, sân khấu tự cuộn bên trong. Đây là hành vi
đúng và là thứ narrow đang đánh mất (§7).

Điểm mỹ thuật hoãn lại: khi sân khấu thấp (boolean_dag 5 bước, table 8 dòng),
vùng trắng dưới thuyết minh chiếm ~40% chiều cao thẻ. Không cản trở học tập →
`COSMETIC_ONLY` (§13).

---

## 7. Narrow baseline (768 × 900)

**Đúng:** không tràn ngang ở bất kỳ lượt nào (`scrollWidth 758 / clientWidth
768`). Panel Quan sát chuyển thành **drawer nổi** (`position: fixed`, rộng
`min(360px, 88vw)`, có shadow) thay vì bị bóp nhỏ — chiến lược đúng, và mặc định
**đóng** ở màn hẹp (`rightOpen: WIDE_SCREEN` trong store), mở lại bằng nút
`Quan sát` luôn thấy trên header. Bảng dữ liệu 5 cột vẫn đọc được, không bóp chữ.

**Sai — và đây là fix #1.** Ở `≤1100px`, media query đặt `.app-layout { height:
auto }`, nên `panel-controls` **thôi là hàng lưới ghim đáy** và trôi theo chiều
cao nội dung. Đo trực tiếp (`narrow-controls-probe.json`):

| Target | Bước | Đáy thanh điều khiển | Viewport | Dưới nếp gấp |
|---|---|---|---|---|
| `bounded_control_flow` | mọi bước | 848px | 900 | 0 |
| `boolean_dag` | mọi bước | 848px | 900 | 0 |
| `relational_table_query` | mọi bước | 848px | 900 | 0 |
| **`bubble_sort`** | 1 | 848px | 900 | 0 |
| **`bubble_sort`** | **2 (ô dự đoán hiện)** | **999px** | 900 | **99px** |
| **`protocol_encapsulation`** | **5** | **921px** | 900 | **21px** |

**Đã phân biệt rõ nguyên nhân — không phải nút hỏng.** Cùng một cú click chuột
thật vào toạ độ của nút `Tiến một bước`:

- khi nút nằm dưới nếp gấp → `cursor` **đứng yên ở 1** qua 3 lần click;
- sau `window.scrollTo(0, scrollHeight)` → **cùng cú click đó ăn ngay**, `cursor
  1 → 2`.

⇒ `RESPONSIVE_DEFECT`, **không phải** `BROKEN_INTERACTION`.

Điều làm nó nặng hơn một lỗi cuộn thông thường: thanh điều khiển **ra vào nếp gấp
theo từng bước**, vì ô dự đoán chỉ hiện ở bước có điểm quyết định. Với
`protocol_encapsulation`, nó nằm trong màn hình ở bước 1–4, tụt xuống ở bước 5,
rồi lại lên. Người học đang bấm `Tiến` liên tục sẽ thấy nút **tự dịch chuyển
dưới ngón tay** — mất tin cậy vào chính bộ điều khiển chính của sản phẩm.

Ảnh chứng minh: `shots/bubble-sort-narrow-2-forward.png` — toàn bộ 6 nút nằm
ngoài khung 900px.

---

## 8. AI presence rules

AI **chỉ** được xuất hiện ở bốn chỗ, và hiện tại đang đúng cả bốn:

1. **Ô nhập đề tự nhiên** (Trang chủ) — hành động chính duy nhất.
2. **Trạng thái "đang phân tích"** — dải trạng thái của composer.
3. **Bản tóm tắt ngắn "hệ thống đã hiểu"** — thẻ `XÁC ĐỊNH BÀI TOÁN` trong panel
   Quan sát (INPUT / OUTPUT / THUẬT TOÁN / DỮ LIỆU).
4. **Phản hồi thiếu dữ liệu / ngoài phạm vi** — bốn tiêu đề `CHƯA ĐỦ DỮ KIỆN` ·
   `CHƯA DỰNG ĐỦ CÁC BƯỚC` · `TÁCH THÀNH TỪNG YÊU CẦU` · `NGOÀI DANH MỤC MÔ PHỎNG`.

Cộng thêm **một** ngoại lệ đã có và nên giữ: mục thu gọn *"Hỏi AI về bước này"* ở
đáy panel Quan sát, **mặc định đóng**, không bao giờ mở sẵn, không bao giờ chiếm
diện tích ngang với sân khấu.

Sau khi workspace mở, trọng tâm phải là cơ chế / state / interaction /
explanation / learning task. Hiện tại đúng.

---

## 9. Pedagogical interaction rules

Ba thời điểm học tập, đo trên 5 module:

| Thời điểm | Thành phần cần có | Hiện trạng |
|---|---|---|
| **Trước** | mục tiêu học tập ngắn | ❌ **0/5** |
| **Trước** | nhiệm vụ học sinh cần làm | ❌ **0/5** |
| **Trong** | trạng thái hiện tại | ✅ 5/5 (sân khấu + Quan sát) |
| **Trong** | hành động / điều kiện | ✅ 5/5 |
| **Trong** | kết quả | ✅ 5/5 |
| **Trong** | hệ quả | ✅ 5/5 (thuyết minh từng bước) |
| **Trong** | interaction phù hợp mục tiêu | ✅ 5/5 *(xem cảnh báo dưới)* |
| **Sau** | kết luận | ✅ 5/5 (bước cuối có băng kết quả) |
| **Sau** | câu hỏi giải thích / chuyển giao | ❌ **0/5** |

Đúng như đề bài yêu cầu, **không** đòi mọi module phải có prediction: timeline là
đủ khi mục tiêu là quan sát và giải thích một cơ chế tất định
(`relational_table_query`, `bounded_control_flow` thuộc nhóm này).

**Không lộ đáp án sớm — kiểm chứng được:** narration của bước quyết định là **câu
hỏi** (`"So sánh cặp kề (172, 158): có cần đổi chỗ không?"`), và bảng chân trị
của `boolean_dag` giữ cột "Ra" là `?` cho cả 8 hàng cho tới bước cuối, kèm câu
*"Cột 'Ra' mở ở bước cuối — em thử tự suy luận trước."* Đây là hành vi đúng và
phải khoá vào baseline.

**Cảnh báo về affordance (fix #3).** `logic.boolean_dag` là target duy nhất trong
5 mà tương tác **là** cơ chế (COVERAGE §2.6: thao tác phải chạm cơ chế ẩn). Thao
tác đó — bấm để đổi giá trị đầu vào — hoạt động đúng (đo được: `A: 1 → A: 0`,
engine tính lại downstream). Nhưng trên màn hình nó chỉ là ba chip `A: 1` `B: 0`
`C: 1`, **không một chữ nào nói rằng bấm được**, trong khi `bubble_sort` ngay bên
cạnh lại có câu hướng dẫn tường minh *"Kéo một cột thả lên cột khác để thử 'nếu
đổi chỗ thì sao?'"*. Cơ chế học tập trung tâm của module đang phụ thuộc vào việc
học sinh **đoán ra** là mình bấm được.

Không đề xuất LMS, điểm số, huy hiệu, quản lý lớp.

---

## 10. Accessibility rules

| Trục | Đo được | Đánh giá |
|---|---|---|
| Nút không có tên khả truy cập | **0** trên toàn bộ 56 lượt | ✅ |
| `input[type=range]` không nhãn | **0** (`aria-label="Tua đến bước"`) | ✅ |
| Icon là SVG, không Unicode/emoji | ✅ — trừ **một** ca (dưới) | ⚠️ |
| Màu không phải tín hiệu duy nhất | ✅ — `✓ Giữ` / `▷ Đang xét` có **icon + chữ**; điều kiện đúng/sai có **chữ ĐÚNG/SAI** | ✅ |
| `role="group"` cho toggle 2D/3D | ✅ (`aria-label="Chế độ hiển thị"`) | ✅ |
| Vùng `aria-live` khi đổi bước | **0 trên cả 56/56 lượt** | ❌ **thiếu hoàn toàn** |
| Phím tắt | ✅ `←` `→` `Space`, có ghi trên màn hình, bỏ qua khi đang gõ trong input | ✅ |

**Hai điểm cần ghi thẳng:**

1. **Đổi bước không được thông báo.** `live_regions = 0` ở gần như mọi lượt; chỉ
   kết quả dự đoán có `role="status"`. Người dùng đọc màn hình bấm `Tiến` sẽ
   không nghe gì. Đây là `ACCESSIBILITY_DEFECT` thật — §13 **hoãn lại chứ không
   bác bỏ**, vì bối cảnh pilot đầu tiên là lớp học có màn chiếu, và sửa đúng cách
   cần quyết định thông báo cái gì (thuyết minh? số bước? cả hai?).
2. **Một ký tự Unicode làm icon vẫn còn.** `⌂ Góc nhìn` ở
   `network/ui3d.tsx:369` và `network/encap-ui3d.tsx:358`. Đây đúng là lỗi mà
   luật icon M9-UX5 sinh ra để chặn (`◧` từng thành ô vuông rỗng trên Windows),
   nhưng **cả hai guard đều không bắt được**: `⌂` (U+2302) không nằm trong
   `FORBIDDEN_ICON_CHARS` của `ux-shell.test.tsx`, cũng không nằm trong dải emoji
   `☀-➿` của `ui-hygiene.test.ts`. Ảnh hưởng thực tế nhỏ (nó vẽ được
   trên máy đo) → `COSMETIC_ONLY`, hoãn (§13) — nhưng khi sửa thì **phải bổ sung
   ký tự vào danh sách cấm**, nếu không lỗi sẽ quay lại.

---

## 11. Five-module comparison

| | `bounded_control_flow` | `bubble_sort` | `boolean_dag` | `relational_table_query` | `protocol_encapsulation` |
|---|---|---|---|---|---|
| Lý do chọn | mã giả + biến + điều kiện | prediction / what-if | thao tác vào cơ chế | pipeline dữ liệu | 2D/3D chung state |
| Vào bằng | dán đề | **Thư viện** | dán đề | dán đề | **Thư viện** |
| Badge miền | THUẬT TOÁN | THUẬT TOÁN | LOGIC | TRUY VẤN BẢNG | MẠNG |
| Số bước | 12 | 40 | 5 | 32 | 9 |
| 6 nút chuẩn | ✅ | ✅ | ✅ | ✅ | ✅ |
| Timeline + tua | ✅ | ✅ | ✅ | ✅ | ✅ |
| Thuyết minh | `.narration-bar` | `.narration-bar` | **`.notes`** | **riêng** | `.narration-bar` |
| Panel Quan sát | biến + mã giả | thẻ đề + mã giả | bảng chân trị | 3 câu tóm tắt | thẻ PDU |
| Interaction riêng | không (đúng) | `predict` + kéo-thả | **`toggle`** | không (đúng) | `predict` + 2D/3D |
| Ẩn đáp án tới lúc cần | ✅ | ✅ (narration là câu hỏi) | ✅ (`?` tới bước cuối) | ✅ (kết quả dần) | ✅ |
| Narrow: điều khiển trong màn | ✅ | ❌ **99px dưới nếp gấp** | ✅ | ✅ | ⚠️ **21px ở bước 5** |
| Tràn ngang | không | không | không | không | không |

**Bằng chứng 2D/3D dùng chung state** (bất biến #16, #18): bấm `3D` ở bước 9 →
`visualMode: "3d"`, `cursor` **giữ nguyên 8**, `Bước 9 / 9` không đổi, cùng một
câu thuyết minh, cùng bộ điều khiển, cùng panel Quan sát. Đổi mode là **đổi
renderer**, không phải đổi mô phỏng. 3D còn có chú thích trục ngay trên sân khấu:
*"Trục sâu = tầng giao thức · trục ngang = chiều truyền"* — xử lý đúng rủi ro
"đọc trục Z là khoảng cách vật lý" mà audit sư phạm trước đó ghi là *chưa xử lý*
(mục §6 của `pedagogical_alignment_audit.md` nay **đã cũ** ở dòng này).

---

## 12. Ba lỗi phải sửa trước pilot

> Chỉ `BLOCKER` / `IMPORTANT`. Không quá 3. Mọi thứ khác xuống §13.

### FIX-1 — Thanh điều khiển tụt dưới nếp gấp ở màn hẹp
`RESPONSIVE_DEFECT` · **IMPORTANT**

- **Hiện tượng:** ở 768×900, khi nội dung module cao lên (ô dự đoán hiện), toàn
  bộ 6 nút điều khiển ra khỏi màn hình đầu tiên — 99px với `bubble_sort`, 21px
  với `protocol_encapsulation` ở bước 5 — và **ra vào theo từng bước**.
- **Vì sao quan trọng:** đây là bộ điều khiển chính của sản phẩm; học sinh dùng
  laptop/tablet ở chiều cao này là ca thật.
- **Đã loại trừ:** không phải nút hỏng — cuộn xuống rồi click là ăn ngay.
- **Gốc rễ:** `global.css` `@media (max-width: 1100px)` đặt `.app-layout{height:
  auto}`, làm `panel-controls` thôi là hàng lưới ghim đáy.
- **Bằng chứng:** `narrow-controls-probe.json`,
  `shots/bubble-sort-narrow-2-forward.png`.

### FIX-2 — Thuyết minh bước hiện tại chưa phải thành phần của shell
`STRUCTURAL_INCONSISTENCY` · **IMPORTANT**

- **Hiện tượng:** ba cách hiện thực (`.narration-bar` / `.notes` / dựng riêng)
  cho cùng một vai trò; không có gì trong hợp đồng bắt module mới phải có thuyết
  minh, cũng không bắt đặt nó đúng chỗ.
- **Vì sao quan trọng:** thuyết minh là thứ biến hoạt hình thành lời giải thích.
  Để nó là quy ước tự nguyện thì module thứ 23 sẽ quên, và không có test nào đỏ.
- **Hướng nhỏ nhất:** shell cấp một khe thuyết minh cố định ngay dưới sân khấu;
  module chỉ trả **chuỗi** cho bước hiện tại. Không đổi engine, không đổi state.
- **Bằng chứng:** `captures.json` (`narration_bar_count` 0 ở
  `boolean_dag`/`relational_table_query`), `logic/dag-module.tsx:305`,
  `database/table-module.tsx:681`.

### FIX-3 — Tương tác cốt lõi của `boolean_dag` không có affordance
`PEDAGOGICAL_VISIBILITY_DEFECT` · **IMPORTANT**

- **Hiện tượng:** ba chip `A: 1` `B: 0` `C: 1` là **thao tác chạm cơ chế ẩn** duy
  nhất của module, nhưng không có một chữ nào nói rằng bấm được và bấm thì gì xảy
  ra. Module ngay cạnh (`bubble_sort`) thì có câu hướng dẫn tường minh.
- **Vì sao quan trọng:** COVERAGE §2.6 đòi mọi tương tác phải chạm cơ chế ẩn —
  tương tác này đạt yêu cầu đó nhưng **không ai tìm ra nó**, nên trên thực tế
  module tụt xuống thành "chỉ xem". Sửa bằng **một câu chữ**, không đụng engine.
- **Bằng chứng:** `shots/boolean-dag-desktop-2-forward.png`,
  `logic/dag-module.tsx:267–277`.

### 12.13 — Trả lời 12 điều kiện hoàn thành

1. **Giữ được khung không?** Có — `KEEP_WITH_TARGETED_FIXES`.
2. **Có cần redesign không?** Không.
3. **Hai màn hình chính?** Trang chủ (cửa vào) và Workspace (phiên học); Thư viện
   + Lịch sử là mặt phụ.
4. **AI xuất hiện ở đâu?** Bốn chỗ ở §8, cộng mục "Hỏi AI về bước này" thu gọn,
   mặc định đóng.
5. **Workspace dùng chung gồm gì?** Header · tên mô phỏng · sân khấu · Quan sát ·
   thuyết minh · timeline · 6 nút · trạng thái từ chối · responsive (§4).
6. **Module được thay phần nào?** Sân khấu, dữ liệu quan sát, nội dung thuyết
   minh, đánh dấu ngữ nghĩa, interaction tuỳ chọn, renderer 3D tuỳ chọn (§5).
7. **Mục tiêu học tập nằm ở đâu?** **Hiện chưa nằm ở đâu cả** — và chưa điền được
   cho 3/5 target vì chưa có neo chương trình (§13.1).
8. **Narration nằm ở đâu?** Ngay dưới sân khấu, trong panel giữa — nhưng đang do
   module tự dựng (FIX-2).
9. **Interaction riêng được phép khi nào?** Khi module khai capability tương ứng
   và thao tác đó chạm cơ chế ẩn, sinh hệ quả tất định (COVERAGE §2.6).
10. **Narrow xử lý panel Quan sát thế nào?** Thành drawer nổi `min(360px, 88vw)`,
    mặc định đóng, mở bằng nút `Quan sát` trên header. Đúng, giữ nguyên.
11. **Ba lỗi phải sửa?** FIX-1, FIX-2, FIX-3 ở trên.
12. **Hoãn tới sau khi học sinh dùng thử?** §13.

---

## 13. Deferred — hoãn tới sau pilot

| # | Vấn đề | Loại | Mức | Vì sao hoãn |
|---|---|---|---|---|
| 1 | **Khe mục tiêu học tập + nhiệm vụ** trong shell | `PEDAGOGICAL_VISIBILITY_DEFECT` | IMPORTANT nhưng **BỊ CHẶN** | Không phải vì nhỏ, mà vì **chưa có dữ liệu để điền**: 3/5 target đại diện (`boolean_dag`, `relational_table_query`, `bounded_control_flow`) hiện có **0** case khai `learning_objective`. Thêm khe rồi bịa mục tiêu là đúng thứ `pedagogical_alignment_audit.md §3` cấm. Việc phải làm **trước** là thêm eval case qua `check_admission`; khe UI đi sau. |
| 2 | Không có `aria-live` khi đổi bước | `ACCESSIBILITY_DEFECT` | IMPORTANT | Hoãn, **không bác bỏ**. Cần quyết định nội dung thông báo trước khi code. |
| 3 | `⌂ Góc nhìn` — ký tự Unicode làm icon | `COSMETIC_ONLY` | MINOR | Vẽ được trên máy đo; nhưng khi sửa **phải** thêm `⌂` vào cả hai danh sách cấm, nếu không nó quay lại. |
| 4 | Vùng trắng lớn dưới sân khấu khi nội dung thấp | `COSMETIC_ONLY` | MINOR | Không cản trở học tập. |
| 5 | Độ dày panel Quan sát chênh lệch lớn giữa module | `STRUCTURAL_INCONSISTENCY` | MINOR | Hợp đồng cho module sở hữu nội dung quan sát; chờ phản hồi người dùng thật rồi mới chuẩn hoá. |
| 6 | Thuyết minh của `relational_table_query` bị cắt bằng `…` | `COSMETIC_ONLY` | MINOR | Chờ FIX-2 gom về shell rồi xử một lần. |
| 7 | Câu hỏi chuyển giao sau mô phỏng | — | — | Đề bài §8 cho phép dùng **phiếu học tập** thay vì UI; rẻ hơn và không đụng code. |

---

## 14. Out-of-scope

Đã kiểm tra và **cố ý không đề xuất**: đăng nhập/đăng ký · quản lý người
dùng/lớp học · chatbot · dashboard · gamification · LMS/điểm số/huy hiệu · thêm
module/family/target · sửa prompt/schema/LLM · blocker `while.body` rỗng · audit
đủ 22 target · sửa lỗi MINOR trong lúc audit · redesign toàn bộ.

Hai việc **liên quan nhưng thuộc quyết định khác**, ghi lại để không rơi:

- **3/5 target không có trong Thư viện** (§3) — quyết định phạm vi danh mục đã
  khai tường minh trong descriptor, không phải lỗi UI. Nếu pilot có giáo viên
  demo, nên quyết định có ý thức trước.
- **Neo chương trình cho 3 family mới** — đã có mục riêng ở
  `docs/evaluation/m17/pedagogical-alignment/`, không mở lại ở đây.

---

## 15. Final baseline diagram

```
                        ┌──────────── SHELL SỞ HỮU ────────────┐
                        │                                       │
  ┌─────────────────────┴───────────────────────────────────────┴──────────┐
  │ HEADER: AlgoSim · Trang chủ / Thư viện / Lịch sử · [Quan sát]          │  BẮT BUỘC
  ├────────────────────────────────────────────┬───────────────────────────┤
  │ [BADGE MIỀN]  TÊN MÔ PHỎNG  ·  hint        │  QUAN SÁT                 │  BẮT BUỘC
  │ ─────────────────────────────────────────  │  ┌─────────────────────┐  │
  │ ┌────────────────────────────────────────┐ │  │  Inspector          │  │
  │ │                                        │ │  │  ↑ MODULE cấp dữ liệu│ │  BẮT BUỘC (khung)
  │ │        SÂN KHẤU                        │ │  └─────────────────────┘  │  MODULE (nội dung)
  │ │        ↑ MODULE sở hữu hoàn toàn       │ │                           │
  │ │        (2D hoặc 3D — cùng state)       │ │  ▸ Hỏi AI về bước này     │  BẮT BUỘC
  │ └────────────────────────────────────────┘ │    (thu gọn · ĐÓNG sẵn)   │  mặc định đóng
  │ ┌────────────────────────────────────────┐ │                           │
  │ │ THUYẾT MINH BƯỚC HIỆN TẠI              │ │  ── narrow ≤1100px: ──    │  BẮT BUỘC
  │ │ ↑ khe của SHELL · chữ của MODULE       │ │  panel này thành DRAWER   │  ⚠ FIX-2
  │ └────────────────────────────────────────┘ │  nổi, mặc định đóng       │
  │ [ Ô DỰ ĐOÁN — chỉ khi module khai predict ]│                           │  TÙY CHỌN
  ├────────────────────────────────────────────┴───────────────────────────┤
  │ ⏮ ◀ [▶ Tự chạy] ▶ ⏭   [↻ Đặt lại]   Bước n/N        Tốc độ   ←→ Space │  BẮT BUỘC
  │ ▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬ thanh tua ▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬ │  ⚠ FIX-1
  │ ↑ GHIM ĐÁY ở desktop — narrow đang MẤT tính chất này                   │  (narrow)
  └────────────────────────────────────────────────────────────────────────┘

  TRẠNG THÁI TỪ CHỐI (thay chỗ sân khấu, hoặc dưới ô nhập ở Trang chủ):     BẮT BUỘC
  ┌────────────────────────────────────────────────────────────────────────┐
  │ [CHƯA ĐỦ DỮ KIỆN | CHƯA DỰNG ĐỦ CÁC BƯỚC | TÁCH THÀNH TỪNG YÊU CẦU |    │
  │  NGOÀI DANH MỤC MÔ PHỎNG]                                              │
  │ learner_reason (không token kỹ thuật) + một câu gợi ý làm gì tiếp       │
  └────────────────────────────────────────────────────────────────────────┘

  CHƯA CÓ — khe dành sẵn, chỉ mở khi có neo chương trình:
  ┌ MỤC TIÊU HỌC TẬP ─────────────────┐  ┌ NHIỆM VỤ CỦA EM ────────────────┐
  │ (0/5 target có hôm nay)           │  │ (0/5 target có hôm nay)         │
  └───────────────────────────────────┘  └─────────────────────────────────┘
```

---

## 16. Screenshot index

Tất cả trong `docs/evaluation/ui-baseline/shots/`. 72 ảnh · 2 viewport
(`desktop` 1440×1000, `narrow` 768×900).

**Vỏ sản phẩm và trạng thái từ chối (6)**

| Tệp | Nội dung |
|---|---|
| `00-home-{desktop,narrow}.png` | Trang chủ — một hành động chính + 6 gợi ý |
| `01-library-{desktop,narrow}.png` | Thư viện — danh mục công khai, gom nhóm |
| `90-refusal-{desktop,narrow}.png` | `CHƯA ĐỦ DỮ KIỆN` dưới ô nhập đề |

**Mỗi target × mỗi viewport (7 pha)**

| Hậu tố | Pha |
|---|---|
| `-1-initial` | trạng thái đầu |
| `-2-forward` | sau 3 lần bấm `Tiến một bước` |
| `-3-autoplay-paused` | sau `Tự chạy` → `Dừng` |
| `-4-final` | sau `Đến cuối` |
| `-5-interaction` | tương tác riêng — `predict` / `toggle` / `3D` (chỉ 3 target có) |
| `-6-reset` | sau `Đặt lại` |
| `-7-observer-toggled` | sau khi bật/tắt panel Quan sát |

Tiền tố: `bounded-control-flow-` · `bubble-sort-` · `boolean-dag-` ·
`table-query-` · `encapsulation-`, ghép với `desktop-` / `narrow-`.
(`bounded-control-flow` và `table-query` không có `-5-interaction`: hai module này
cố ý chỉ có timeline.)

**Ảnh mang bằng chứng của kết luận**

| Kết luận | Ảnh |
|---|---|
| FIX-1 — điều khiển dưới nếp gấp | `bubble-sort-narrow-2-forward.png` |
| FIX-3 — chip toggle không affordance | `boolean-dag-desktop-2-forward.png` |
| Khung desktop chuẩn | `bubble-sort-desktop-1-initial.png` |
| 2D/3D cùng state, cùng vỏ | `encapsulation-desktop-5-interaction.png` |
| Drawer Quan sát ở narrow | `bubble-sort-narrow-7-observer-toggled.png` |
| Từ chối trung thực + xuống cấp khi backend tắt | `90-refusal-desktop.png` |

**Tệp dữ liệu đo**

| Tệp | Nội dung |
|---|---|
| `captures.json` | 16 bản ghi — 12 trục đo khung giao diện ở mỗi pha, mỗi target, mỗi viewport |
| `narrow-controls-probe.json` | toạ độ tuyệt đối thanh điều khiển vs viewport ở 768×900, kèm phép thử cuộn-rồi-click phân biệt nguyên nhân |

---

## Giới hạn của lượt đo này

1. **Không có dữ liệu người học.** Mọi kết luận là về *giao diện*, không phải về
   *tác động học tập* — `learner impact = NOT_EVALUATED`, và checkpoint này không
   thể thay đổi điều đó.
2. **Backend không chạy** ⇒ không đo đường AI thật (phân tích đề → envelope).
   Ba target vào bằng `loadEnvelope` với config **canonical** lấy từ fixture đã
   khoá hai chiều (`program-normalized-envelope.json`), không phải config tự chế.
3. **Chỉ 5/22 target.** Đúng phạm vi được giao; không suy rộng cho 17 target còn lại.
4. **Chrome headless, một máy, một hệ phông chữ.** Rủi ro glyph thiếu (mục §10.2)
   không quan sát được ở đây — đó chính là lý do luật icon tồn tại.
5. Một lượt chạy đầu bị hỏng do fixture `program-1.0` đã cũ; sản phẩm **từ chối
   đúng** (`program_version phải là 'program-2.0'`) và lượt đo được chạy lại với
   hợp đồng hiện hành. Ghi lại vì nó là bằng chứng fail-closed hoạt động ở biên
   frontend.
