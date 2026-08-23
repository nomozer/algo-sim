# STACK VISUAL ACCEPTANCE — vNext §8

> Bằng chứng trình duyệt THẬT (Chromium qua Playwright), không phải `renderToString`.
> Runner: `frontend/scripts/capture-stack-vnext.mjs` · dữ liệu máy:
> `../browser-evidence/stack-visual-acceptance.json` · ảnh:
> `../browser-evidence/stack-{A..F}_*.png`.

## 0. Vì sao cần bản soát này

Unit test dựng DOM bằng SSR, mà SSR **chỉ đi qua trạng thái đầu**. Sự cố đã chụp
màn hình — lời kể chạy tới bước 6 trong khi ngăn xếp trên hình vẫn rỗng — nằm
đúng vùng mù đó (`ARCHITECTURE_MAP §8` #11, #13).

**Hai điều kiện trước khi tin một bản soát "SẠCH"** (anti-pattern #14), cả hai
đã thoả:

1. **Dấu vân tay trang** — runner khẳng định đã nạp đúng
   `"Kiểm tra đóng mở ngoặc hợp lệ bằng Stack"` với **7 bước**; sai thì thoát `3`.
2. **Tiêm lỗi giả** — `--faultcheck` thay `push`/`pop` bằng `highlight`. Bản soát
   tụt xuống **2/6** và thoát khác 0. Guard đã chứng minh là đỏ được.

> Chế độ tiêm lỗi tái hiện **chính xác** triệu chứng gốc: ngăn xếp `[]` ở mọi
> khung trong khi narration vẫn kể push/pop. Đó là bằng chứng bản vá đang chặn
> đúng lỗi đã quan sát, không phải chặn một lỗi tưởng tượng.

**Server sạch, có chủ đích.** Cổng 3000 đang bận bởi tiến trình khác nên có nguy
cơ chụp nhầm bản build cũ (tiền lệ `0a71268` "poisoned server"). Bản soát chạy
trên server riêng cổng **3100** dựng từ mã hiện tại. `strictPort: true` đã làm
đúng việc — Vite thoát thay vì lặng lẽ nhảy cổng.

## 1. Bảng nghiệm thu

Đầu vào `{[()]}`. Cột `stack`/`current`/`result` là **phép chiếu ngữ nghĩa đọc
từ DOM** (nội dung `<text>` trong SVG), không phải kỳ vọng pixel.

| khung | input | current | stack | result | verdict |
|---|---|---|---|---|---|
| **A** khởi tạo | `{[()]}` đủ 6 ô | `—` | `[]` | `—` | **PASS** |
| **B** đọc `{` | `{[()]}` | `{` | `[]` | `—` | **PASS** |
| **C** sau push `{` | `{[()]}` | `{` | `["{"]` | `—` | **PASS** |
| **D** sau push `[` | `{[()]}` | `[` | `["{","["]` | `—` | **PASS** |
| **E** sau pop | `{[()]}` | `[` | `["{"]` | `—` | **PASS** |
| **F** kết quả | `{[()]}` | `[` | `["{"]` | `Hợp lệ` | **PASS** |

**6/6 khung PASS.**

Ngăn xếp qua các khung: `[]` → `["{"]` → `["{","["]` → `["{"]` — đổi thật, đúng
thứ tự LIFO (`[` ở đỉnh ở khung D). Đây là điều bản cũ **không** làm được ở bất
kỳ khung nào.

## 2. Gốc rễ — ba tầng, không phải một

Bản vá trước (`undefined → —`) mới chặn renderer **nói dối**; nó không làm
renderer **nói thật**. Truy đủ đường thì có ba tầng:

| # | tầng | hỏng thế nào |
|---|---|---|
| 1 | **routing** | `main.py:303` gọi `run_pipeline(...)` **không truyền `semantic_route`** ⇒ mặc định `"off"`. Engine DUY NHẤT mang trạng thái theo bước (`semantic`, nuôi bằng trace của `SemanticProgramInterpreter`) **không bao giờ chạy trong production**; bài thuật toán rơi xuống `generic`. |
| 2 | **frame** | `buildTimeline` nhánh `step_sequence` đẩy ra Frame chỉ có `visibleIds`/`entityPos`/`narration`/`stepAction` — **không có kênh giá trị**. `valuesOf(spec, state.base)` hằng số suốt timeline. Trong khi validator **nhận và giữ** `value`/`to_index`/`indices` từng bước: hợp đồng hứa, engine vứt. |
| 3 | **renderer binding** | `stack_view` và `array_strip` đọc `o.items` **thẳng từ spec tĩnh**, không bao giờ từ `values`. Nên dù tầng 2 có sửa, collection vẫn đứng yên. Đây cũng là ô rỗng nhãn `[0]` trong ảnh gốc (`items: []` ⇒ `max(1,0)` = một ô trống). |

**`root_cause_layer` chính thức: tầng 2 + 3** (frame và renderer binding) — đó là
hai tầng đã sửa trong lượt này. Tầng 1 là phát hiện kiến trúc **chưa đụng tới**,
xem §4.

## 3. Bản vá

- `model.ts::Frame.values` — trạng thái ngữ nghĩa tại khung, engine sở hữu.
- `model.ts::applyStepAction` — gấp `set_value`/`push`/`pop`/`move_pointer` lên
  bản đồ giá trị chạy dần. **Allowlist đóng, không `eval`**, hành động lạ ⇒ không
  đổi gì (tương thích ngược).
- `ui.tsx` — `valuesOf(spec, frame.values ?? state.base)`; `stack_view` và
  `array_strip` ưu tiên giá trị của khung.

Renderer **không** tự thực thi push/pop. Diễn tiến thuộc engine; renderer chỉ đọc
`frame.values` (ranh giới R0 — renderer tự suy là dựng engine thứ hai ở tầng
trình bày).

## 4. Còn hở — khai tường minh

- **`← TOP` bị cắt.** Chú thích đỉnh ngăn xếp vẽ tràn ra ngoài mép SVG nên chỉ
  còn một glyph mũi tên. Lỗi trình bày, không phải ngữ nghĩa; chưa sửa.
- **Thanh điều khiển bước không hiện** khi envelope được tiêm thẳng qua store
  (ảnh chỉ có "Đặt lại"). Không ảnh hưởng phép chiếu ngữ nghĩa, nhưng nghĩa là
  bản soát này **chưa** đi qua đúng đường bấm nút của học sinh.
- **Tầng 1 (routing) chưa đụng.** `semantic_route` vẫn `off`. Bài stack ở đây
  chạy được vì `generic` nay diễn hoạt được, **không** vì route ngữ nghĩa bật.
- **Chuỗi đầu vào trống trong ảnh gốc** là do spec sinh ra thiếu `items`, không
  phải do engine. Lượt này không sửa phía sinh spec.

`SCALAR_TAXONOMY_EXPANSION: DEFERRED_UNTIL_VISUAL_ACCEPTANCE` — giữ nguyên theo
§10, không đụng taxonomy trong lượt này.
