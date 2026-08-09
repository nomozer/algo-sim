# W4B-2B — GIẢI THÍCH TUỲ CHỌN + KHE HỞ QUAN SÁT (§7–§10)

Phạm vi lượt này **đã bị cắt có chủ đích** sau phản biện: chỉ §7–§10 cho
`algorithm.find_max`. Experiment gating, pilot `insertion_sort`, motion và ma
trận 22 target **KHÔNG mở** — lý do ở §6 bên dưới.

| | |
|---|---|
| Base | `614b2ed` (BEFORE baseline đóng băng) |
| §7–§8 | `39ad0df` |
| §9–§10 | commit của lượt này |

## 1. §7–§8 — đổi tên + đóng mặc định (đã đóng ở `39ad0df`)

Panel phải: **“Quan sát” → “Giải thích”**, ĐÓNG mặc định ở mọi bề rộng, hằng
`WIDE_SCREEN` gỡ bỏ (SSR và trình duyệt nay khởi tạo giống nhau).

**Ranh giới giữ được:** `generic/ui.tsx` có nhãn “Quan sát” thuộc cặp
[Quan sát][Chỉnh sửa] của renderer generic — **khác khái niệm**, giữ nguyên.
Guard `ui-hygiene.test.ts` cấm nhãn ở mọi component TRỪ đúng file đó, **và**
khẳng định file đó vẫn còn nhãn (allowlist không được thành xác).

**`core/program.ts::conditionWithValues` giữ nguyên, vẫn chạy vô điều kiện.**
`VarsView` chỉ sống trong panel phải ⇒ panel đóng thì narration là đường DUY
NHẤT chở giá trị biến. Lý do cũ (“ở màn hẹp”) không hết hiệu lực mà **mở rộng ra
mọi viewport**.

## 2. §9 — Giải thích đào sâu, không chép lại trang chính

Gỡ hai thứ header workspace **đã** sở hữu:

| Trùng lặp | Bằng chứng |
|---|---|
| `problem.summary` dựng thành `<h2 class="card-title">` trong panel | `offline-catalog.ts:59` đặt `envelope.title = analysis.problem.summary`, mà `SimulationWorkspace` đã dựng chuỗi đó thành `<h2 class="workspace-title">` ⇒ **hai `<h2>` chữ y hệt trên một màn** |
| hàng “Thuật toán: Tìm giá trị lớn nhất” | header in `mod.title` = `ALGORITHM_NAMES[algorithm_id]` (cùng bảng), và `PseudocodeView` ngay dưới có đầu mục “THUẬT TOÁN” ⇒ **một ý ba lần trong một cột hẹp** |

Giữ lại đúng phần header **không** nói: Input · Output · Dữ liệu. Thêm nhãn
“BIẾN” do chính `VarsView` dựng (bước không có biến ⇒ mất cả mục, không để lại
đầu mục rỗng).

**Bán kính ảnh hưởng:** `AnalysisCard` chỉ có MỘT consumer
(`AlgorithmInspector`) ⇒ 9 target thuật toán, không lan ra 13 target còn lại.

**Không có rò rỉ tương lai (§7 của kế hoạch):** Explain chỉ mang Input/Output
(mô tả, không phải đáp án), `VarsView` đọc `snapshot.vars` của **bước hiện tại**,
`PseudocodeView` là mã giả tĩnh. Bất biến “inspector không mù bước” vẫn khoá ở
`simulations/inspector-exposure.test.tsx`.

## 3. §10 — khe hở QUAN SÁT của `find_max`, đo trước khi vá

Ảnh: `observe-baseline/find-max-explain-closed/` (Explain ĐÓNG, 1920×1080 +
1366×768, initial/mid/final).

**A. Học sinh đã thấy gì** — giá trị trên đầu cột, tên bạn dưới cột, chỉ số,
vùng xám “đã duyệt qua”, vùng hành động (`Dũng — vị trí 4 · 8`, `8 > 9 ?`,
`max 9`) và nút Thí nghiệm.

**B. Câu hỏi cơ chế còn mờ** — *cột nào đang được xét, cột nào là max hiện tại*.
Ở bước 5/10 Bình (9) và Dũng (8) tô **hệt nhau**, và **cả hai đều có con trỏ ▲**.

**C. Loại thông tin thiếu** — **QUAN HỆ / VAI TRÒ**, không phải state. Dữ liệu đã
có sẵn trong engine: `compare` mang `i` (đang xét) và `j` (ứng viên), còn cột ứng
viên mang mark `considering` liên tục (`core/algorithms.ts:85,119`).

**Nguyên nhân gốc:** `columnState` cho **ưu tiên sự kiện đè lên mark**, nên đúng
ở bước mà phân biệt là quan trọng nhất thì phân biệt bị xoá.

**Nặng hơn — chú giải nói dối.** `arrayLegendItems` đọc mark `considering` nên
vẫn in hai mục riêng “đang xét / so sánh” và “max hiện tại”, trong khi sân khấu
chỉ tô một trạng thái. Chú giải sai còn tệ hơn không có.

### Bản vá — nhỏ nhất, từ state sẵn có

Cột đang mang mark `considering` thì sáng lên vì là **ứng viên**, không phải vì
đang bị xét ⇒ giữ tông `considering` và **không** vẽ con trỏ. Hai kênh phân biệt
đúng `DESIGN_BRIEF §3.5`: màu + có/không con trỏ. Con trỏ ▲ nay chỉ **một** thứ:
chỗ thuật toán đang đứng.

Không thêm prop, không đọc `algorithm_id`, không đụng hình học W4B-2A.

**Bán kính ảnh hưởng chính xác = 2 bài.** `grep considering core/algorithms.ts`
chỉ ra hai chỗ, đều trong `runFindExtreme` ⇒ `find_max` + `find_min`. Bảy bài
còn lại không đổi một pixel; test khoá riêng `bubble_sort` (hai cột so sánh
NGANG VAI vẫn phải cùng tông, vẫn hai con trỏ).

Ảnh sau vá: `after/find-max-observe-cue/`.

**Còn nguyên KHÔNG vá (đúng §17):** *“max vừa đổi hay giữ nguyên”* vẫn **không**
đọc được trên sân khấu ở bước chưa cam kết. Đó là ranh giới rò rỉ đáp án, không
phải thiếu sót — hệ quả thuộc bước kế tiếp.

## 4. §27 — `insertion_sort` quan sát: đã đạt sẵn, không cần vá

Ảnh: `observe-baseline/insertion-sort-explain-closed/`. Ở bước 17/33 với Explain
đóng, cả bốn tín hiệu §27 đều đã hiện: khay **ĐANG GIỮ 8** (viền cam đứt) · ô
**trống** đúng vị trí 4 · vùng **đã sắp xong** xanh lá · cột **đang xét** xanh có
con trỏ. **Không thêm cue nào.**

## 5. Sự cố công cụ (ghi lại, không giấu)

Lượt chụp đầu chết với `Simulation "algorithm.find_max" đã được đăng ký trước
đó`. Chú thích trong `diagnose-responsive.mjs` tin rằng `registerAllSimulations`
idempotent — **sai**: cờ `registered` sống ở `simulations/index.ts` còn Map sống
ở `simulations/registry.ts`; HMR dựng lại index.ts mà không dựng lại registry.ts
⇒ cờ về `false` trong khi Map vẫn đầy. Runner nay gác theo **trạng thái thật của
registry**. Chỉ sửa script, **không** đụng mã sản phẩm để chụp được ảnh.

Artifact `WRONG_VISUAL_MODE_OR_RENDERER.json` của lượt hỏng đã xoá khỏi thư mục
baseline: đó là hỏng **công cụ**, để lại sẽ bị đọc nhầm thành phán quyết sản phẩm.

## 6. Vì sao lượt này dừng ở §10

Ba phản biện làm đổi kế hoạch, đã được duyệt trước khi code:

1. **§21 đảo ngược một bất biến đang bị test khoá.** `interaction-policy.ts:125`
   ghi luật W3B §15 *“cam kết trước, thí nghiệm sau”*, khoá ở
   `interaction-family-sorting-w3b.test.tsx:354`. §21 muốn ActionZone ẩn tới khi
   mở Thí nghiệm ⇒ cam kết chỉ tới được *qua* Thí nghiệm. **Giữ W3B §15.**
2. **Trigger Thí nghiệm cho `find_max` ĐÃ tồn tại** —
   `whatIfPolicyOf("find_max").mode === "challenge"` + `challengeLabel` +
   `labOpen` (`ui.tsx:268`). Kiểm kê cũ ghi “chưa tồn tại” là **sai**.
3. **`insertion_sort` cố ý là `mode: "free"`** vì kéo CHÍNH LÀ cơ chế đang học.
   §29/§30 sẽ **hạ cấp** một thao tác hiện luôn dùng được. **Giữ `free`.**

## 7. Cổng đã chạy

| Cổng | Kết quả |
|---|---|
| vitest | **978 passed** / 61 file (964 → 969 sau §7–§8 → 978) |
| `npm run build` (`tsc -b`) | sạch |
| pytest | **1135 passed**, 2 skipped (backend không đụng) |
| catalog matrix | **Target 22 · conformance 0 · ownership 0 · parity 0 · PASS** |
| responsive 22 target × 3 viewport, Explain ĐÓNG | **PASS**, 0 failure (`after/catalog22-responsive-closed/`) |
| renderer-fit + container-density | trong cùng lượt trên, 0 vi phạm |
| `git diff --check` | sạch |

**Guard mới đều đã chứng minh đỏ được bằng tiêm lỗi giả:**
trả nhãn “QUAN SÁT” về → 3 đỏ · trả `rightOpen: WIDE_SCREEN` về → 2 đỏ ·
trả `<h2>{problem.summary}</h2>` về → 1 đỏ · gộp lại hai vai trò cột → 3 đỏ.

## 8. Giới hạn — không được trích dẫn quá

- **`LEARNER_IMPACT_NOT_EVALUATED`** · **`CURRICULUM_SUPPORT_PARTIAL`**. Ảnh
  chứng minh tín hiệu cơ chế **nhìn thấy được**, không chứng minh học sinh học
  tốt hơn.
- Ảnh `observe-baseline/` chụp tại `39ad0df` với Explain ĐÓNG ⇒ là **baseline
  trung gian**, KHÔNG phải BEFORE đóng băng. BEFORE (`614b2ed`) chụp với panel
  **MỞ** và chỉ có **một** khung panel-đóng (find_max mid @1920) ⇒ so trực tiếp
  BEFORE↔AFTER cho `insertion_sort` ở trạng thái panel-đóng là **không có cơ sở**.
- Chưa đo: Experiment gating · keyboard flow · canonical-state qua đóng/mở UI ·
  answer-leak có kiểm chứng · viewport 1920×768 và 1024×768 · motion.
- ~40 finding token drift ở `global.css` **vẫn còn nguyên**, không sửa không ẩn
  không ignore → `POST-W4B2B_DESIGN_TOKEN_AUDIT`.

---

# PHẦN 2 — CỔNG THÍ NGHIỆM (§0–§29 của lượt kế tiếp)

Lượt này đảo ngược quyết định của lượt trước (khi đó chốt "giữ W3B §15" và "giữ
`insertion_sort` = free"). Ghi lại để không ai đọc hai artifact rồi tưởng mâu thuẫn.

## A. `labOpen` sở hữu gì TRƯỚC wave (truy vết, không suy từ tên)

| Câu hỏi | Sự thật đo được |
|---|---|
| Sống ở đâu | `useState(false)` **cục bộ** trong `AlgorithmWorkspace` (`ui.tsx:115`) — không phải store, không persist |
| Gác cái gì | ĐÚNG MỘT thứ: `dragAllowedByPolicy`, và chỉ khi `mode === "challenge"` |
| ActionZone có phụ thuộc nó không | **Không** — `ui.tsx:192/217` render chỉ theo `scan`/`sort` khác null |
| `whatIfPolicyOf` tham gia ra sao | cấp `mode` + copy; `labOpen` chỉ có nghĩa với `challenge` |

## B. Thay đổi — EXTEND, không CREATE

Thêm **một** cờ khai báo `experimentGated?: boolean` vào `WhatIfPolicy`. Cờ này
gác **cả vùng cam kết lẫn kéo-thả**. Bật cho đúng hai bài pilot.

Vì sao là cờ riêng chứ không thêm `mode`: hai pilot có `mode` khác nhau vì lý do
chính đáng (`find_max` = `challenge`, kéo chỉ có nghĩa như phép thử bất biến;
`insertion_sort` = `free`, kéo CHÍNH LÀ cơ chế đang học). Gộp lại sẽ xoá đúng
phân biệt mà `mode` sinh ra để giữ. **Cổng là TRÌNH BÀY; `mode` là NGỮ NGHĨA.**

- state mới: **không có** (dùng lại `labOpen`)
- bên chấm mới: **không có** (`submitPrediction → predict.check` nguyên vẹn)
- if-chain theo tên bài trong shell: **không có** (test quét mã nguồn khoá điều này)

## C. Quan hệ Ở LẠI Quan sát — quyết định đáng chú ý nhất

Ẩn vùng cam kết làm lộ ra một rủi ro: dải nhân quả vốn tắt khi có ActionZone
(luật chống lặp W1), nên gác cổng sẽ **lấy mất luôn quan hệ đang xét**
("Dũng — vị trí 4", "8 > 9 ?") khỏi màn mặc định. Điều kiện nay đọc **vùng đang
hiện**, không đọc "bước có phải điểm quyết định": quan hệ thuộc Quan sát, chỉ
NÚT CAM KẾT thuộc Thí nghiệm.

## D. Blast radius (§25) — 5 test khoá hợp đồng CŨ

`algorithm-ui.test.tsx` (×2) · `interaction-family-w1.test.tsx` ·
`scan-semantics-w3b1.test.tsx` · `interaction-family-sorting-w3b.test.tsx`.

Không nới lỏng cái nào. Bất biến thật là **"không bao giờ HAI bề mặt cam kết"**,
nó chưa bao giờ đòi "luôn có một" — nay kỳ vọng đọc từ **chính bản khai policy**
(`whatIfPolicyOf(id).experimentGated`) nên thêm target vào pilot thì test đi theo,
mà lỡ có hai bề mặt thì vẫn đỏ như cũ.

Anh em KHÔNG bị kéo theo: `find_min`, `bubble_sort`, `selection_sort`,
`binary_search`, `linear_search`, `sum_if`, `count_if` giữ nguyên hành vi — có
test khẳng định `experimentGated` của chúng là `undefined`.

## E. Bằng chứng trình duyệt (`browser-flow/`)

**34/34 PASS**, cả hai pilot, Chrome thật, thao tác thật:

Quan sát không có vùng cam kết · cổng nhìn thấy được · **Tab tới được và Enter mở
được** (không cần chuột) · vùng cam kết hiện ra · cam kết SAI → `verdict:
"incorrect"` · cam kết ĐÚNG → `verdict: "correct"` · mở Giải thích KHÔNG đóng Thí
nghiệm · đóng cổng → Quan sát trở lại, **không reset** · timeline vẫn tiến được.

**Canonical state:** repo không có tiện ích hash ở frontend, nên bằng chứng là
`JSON.stringify(active.state)` **toàn phần** — mạnh hơn một digest tự chế. Chuỗi
này **không đổi một ký tự** qua: mở cổng → chấm sai → mở/đóng Giải thích → đóng
cổng. `canonical_stable_across_ui_modes: true` cho cả hai target.

**Rò rỉ đáp án:** `correctActionId` / `expectedId` / `expectedAction` / "đáp án
đúng" — **0 lần** trong `document.body.innerHTML`, cả ở Quan sát lẫn khi Thí
nghiệm đang mở.

## F. Hai sự cố công cụ (ghi lại, không giấu)

1. **Tiến trình Vite "bẩn" cho ra phán quyết sai.** Trên server đã phục vụ nhiều
   lượt, `loadEnvelope` đặt được `view:"workspace"` mà React vẫn vẽ Trang chủ —
   và `diagnose-responsive.mjs` cũng hỏng y hệt trên đúng server đó. Không phải
   lỗi sản phẩm. Trên tiến trình Vite MỚI, cả hai chạy sạch. Đây là lý do §0 của
   đề bài đòi "fresh Vite process" — đòi hỏi đó đúng.
2. **Enter không kích hoạt nút nếu phát phím thiếu.** `Input.dispatchKeyEvent`
   chỉ `keyDown`/`keyUp` thì phím tới DOM nhưng không thành activation. Phải đủ
   `rawKeyDown` + `char` + `keyUp` kèm mã phím gốc. Runner nay thử bàn phím
   TRƯỚC, chuột chỉ là đường lùi **có ghi nhãn** (`experiment_opened_by`) — để
   không bao giờ gộp "bàn phím hỏng" với "cách đo hỏng" thành một kết luận.

## G. Cổng đã chạy (lượt 2)

vitest **992** / 62 file · build sạch · pytest **1135** (+2 skip) ·
catalog **22 PASS** · responsive **22 target × 6 viewport** (thêm 1920×768,
1024×768, 768×900) **PASS 0 failure** · `git diff --check` sạch.

## H. Chưa làm — KHÔNG được claim

- **Ma trận 22 target (`CONTEXTUAL_TOOL_CAPABILITY_MATRIX.md`) chưa viết.**
- **Impeccable critique có phạm vi: chưa chạy.**
- What-if drag trong Thí nghiệm: chỉ chứng minh gián tiếp qua policy + test đơn
  vị; **chưa** có kịch bản kéo thật trong trình duyệt rồi khôi phục.
- `LEARNER_IMPACT_NOT_EVALUATED` · `CURRICULUM_SUPPORT_PARTIAL` giữ nguyên.
- ~40 finding token drift `global.css` vẫn nguyên → `POST-W4B2B_DESIGN_TOKEN_AUDIT`.
