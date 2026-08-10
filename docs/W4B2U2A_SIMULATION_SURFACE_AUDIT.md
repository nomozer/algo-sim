# W4B-2U2A — AUDIT BỀ MẶT MÔ PHỎNG TOÀN DANH MỤC

Baseline `fdcd4ea`, cây sạch. **Wave AUDIT — không sửa một dòng mã sản phẩm nào.**
Hợp đồng đi kèm: `docs/SIMULATION_SURFACE_COMPOSITION_CONTRACT.md`.

Số liệu dẫn xuất từ **nguồn hiện tại** (`capability-descriptors.json`,
`sim-samples.ts`, `offline-catalog.ts`, khai `apply`/`predict` của từng module),
không chép lại từ wave cũ. Phép đo bố cục lấy từ
`docs/evaluation/m17/w4b2t-composition/measure-after.json` (Chrome, 1920×1080)
— sân khấu chưa đổi kể từ lần đo đó.

## 1. Con số nền

| | |
|---|---|
| Target trong danh mục | **22** |
| Mẫu offline (tổng) | **17** |
| Mẫu **PUBLIC_SURFACE** | **13** |
| Mẫu **INTERNAL_FIXTURE** | **4** — `gen-and`, `gen-binary`, `gen-packet`, `gen-reveal` |
| `simulation_id` chạy được offline | **13** |
| Target khai `predict` | **11** |
| …trong đó chạy được công khai | **10** (`selection_sort` có năng lực nhưng **không có mẫu**) |
| Target có `apply` thật (engine sở hữu thao tác) | **14** |
| Target `apply` = identity | **8** |
| Target hỗ trợ 3D | **1** (`network.protocol_encapsulation`) |
| Trùng kết quả ở bước cuối | **0** (W4B-2T đã sửa; trước đó 8) |

**Đính chính quan trọng:** cả bốn `INTERNAL_FIXTURE` đều là spec của
`generic.rule_scene`. Nhưng `generic.rule_scene` **cũng có** một mẫu công khai
(`gen-web`). Nên target đó vừa PUBLIC vừa có fixture nội bộ — không được nói
"rule_scene là nội bộ". `LibraryView` render `publicCatalog()` (lọc
`visibility === "public"`), nên bốn fixture kia **học sinh không thấy**.

## 2. Nhận dạng · chính sách biểu diễn · vòng đời

`VIS` = PUBLIC / INTERNAL-only · `LC` = vòng đời · `LVL` = mức tương tác.

| # | target | họ | VIS | mode | LC | LVL |
|---|---|---|---|---|---|---|
| 1 | `algorithm.find_max` | quét | PUBLIC | 2d | TRACE_FIRST | L3 |
| 2 | `algorithm.find_min` | quét | PUBLIC | 2d | TRACE_FIRST | L3 |
| 3 | `algorithm.count_if` | quét | PUBLIC | 2d | TRACE_FIRST | L3 |
| 4 | `algorithm.sum_if` | quét | PUBLIC | 2d | TRACE_FIRST | L3 |
| 5 | `algorithm.linear_search` | tìm | PUBLIC | 2d | TRACE_FIRST | L3 |
| 6 | `algorithm.binary_search` | tìm | PUBLIC | 2d | TRACE_FIRST | L3 |
| 7 | `algorithm.bubble_sort` | sắp | PUBLIC | 2d | TRACE_FIRST | L3 |
| 8 | `algorithm.insertion_sort` | sắp | PUBLIC | 2d | TRACE_FIRST | L3 |
| 9 | `algorithm.selection_sort` | sắp | *không mẫu* | 2d | TRACE_FIRST | L3 |
| 10 | `algorithm.scan` | quét | *không mẫu* | 2d | TRACE_FIRST | L2 |
| 11 | `algorithm.bounded_control_flow` | luồng | *không mẫu* | 2d | TRACE_FIRST | L2 |
| 12 | `binary.decimal_to_binary` | nhị phân | PUBLIC | 2d | **EXPLORATION_FIRST** | **L4** |
| 13 | `binary.base_conversion` | nhị phân | *không mẫu* | 2d | TRACE_FIRST | L2 |
| 14 | `binary.character_encoding` | nhị phân | *không mẫu* | 2d | TRACE_FIRST | L2 |
| 15 | `logic.and_gate` | logic | PUBLIC | 2d | **EXPLORATION_FIRST** | **L4** |
| 16 | `logic.boolean_dag` | logic | *không mẫu* | 2d | **EXPLORATION_FIRST** | **L4** |
| 17 | `tree.traversal` | cấu trúc | *không mẫu* | 2d | TRACE_FIRST | L2 |
| 18 | `network.graph_traversal` | cấu trúc | *không mẫu* | 2d | TRACE_FIRST | L2 |
| 19 | `network.packet_routing` | mạng | PUBLIC | 2d | **HYBRID** | L3 |
| 20 | `network.protocol_encapsulation` | mạng | PUBLIC | **2d+3d** | TRACE_FIRST | L2 |
| 21 | `database.relational_table_query` | bảng | *không mẫu* | 2d | TRACE_FIRST | L2 |
| 22 | `generic.rule_scene` | generic | PUBLIC **+4 fixture** | 2d | **EXPLORATION_FIRST** | **L4** |

**Phân bố mức:** L0 = 0 · L1 = 0 · **L2 = 8** · **L3 = 10** · **L4 = 4**.
**Phân bố vòng đời:** TRACE_FIRST = 18 · EXPLORATION_FIRST = 4 · HYBRID = 1
*(packet_routing tính vào HYBRID; 18+4 ở trên đã gồm nó ở TRACE_FIRST — con số
chuẩn là TRACE_FIRST 17 · HYBRID 1 · EXPLORATION_FIRST 4)*.

Lưu ý phương pháp: **nút play KHÔNG nâng mức lên L3.** L3 đòi học sinh đổi được
state/đầu vào và engine tính lại — với 9 bài thuật toán đó là `whatif_swap` sinh
nhánh, với `packet_routing` là `net_connect/disconnect/reset` → `recompute`.
**`predict` KHÔNG được tính là L3**: nó nộp một câu trả lời *về* state kế tiếp,
không đổi mô hình.

## 3. Vị trí tương tác + blocker chính

| target | vị trí tương tác | blocker chính |
|---|---|---|
| 9 bài thuật toán trực tiếp | INLINE_CONTEXTUAL (kéo trên `ArrayView` sau cổng Thí nghiệm) + QUIZ_ACTION (`PredictionBar`) | **QUIZ_FLOW_DOMINANT** |
| `algorithm.scan`, `bounded_control_flow` | PLAYBACK_ONLY | INTERACTION_CONTRACT_MISSING |
| `binary.decimal_to_binary` | **ON_STAGE_DIRECT** (bấm bit) | NONE |
| `binary.base_conversion`, `character_encoding` | PLAYBACK_ONLY | INTERACTION_CONTRACT_MISSING |
| `logic.and_gate`, `boolean_dag` | **ON_STAGE_DIRECT** (bấm công tắc) | NONE |
| `tree.traversal`, `graph_traversal` | PLAYBACK_ONLY | INTERACTION_CONTRACT_MISSING |
| `network.packet_routing` | **ON_STAGE_DIRECT** (bấm liên kết) + QUIZ_ACTION | QUIZ_FLOW_DOMINANT |
| `network.protocol_encapsulation` | QUIZ_ACTION + PLAYBACK_ONLY | INTERACTION_CONTRACT_MISSING |
| `database.relational_table_query` | PLAYBACK_ONLY | INTERACTION_CONTRACT_MISSING |
| `generic.rule_scene` | **ON_STAGE_DIRECT** (bấm switch) | NONE |

**INTERACTION_CONTRACT_MISSING = 8 target** (`apply` = identity):
`algorithm.scan` · `bounded_control_flow` · `base_conversion` ·
`character_encoding` · `tree.traversal` · `graph_traversal` ·
`relational_table_query` · `protocol_encapsulation`.

## 4. Blast radius của bề mặt quiz (§10)

`PredictionBar` có **một chủ sở hữu duy nhất**: dựng ở
`SimulationWorkspace.tsx:217`, hiện khi module khai `predict` **và** bước hiện
tại có `challenge`. Chuỗi "Dự đoán bước này" ở `PredictionBar.tsx:94`.

```
QUIZ_SURFACE_PUBLIC_TARGETS = [
  algorithm.find_max, algorithm.find_min, algorithm.count_if, algorithm.sum_if,
  algorithm.linear_search, algorithm.binary_search,
  algorithm.bubble_sort, algorithm.insertion_sort,      # 8 chạy được công khai
  network.packet_routing, network.protocol_encapsulation # 10
]
+ algorithm.selection_sort   # khai predict nhưng KHÔNG có mẫu → 11 theo danh mục
```

**Xác nhận con số 11 của prelude, kèm đính chính:** 11 là số target **khai
`predict` trong danh mục**; số **chạy được công khai** là **10**. U2-B phải phủ
cả 11 (sửa ở chủ sở hữu chung), nhưng chỉ **10** kiểm được bằng trình duyệt.

**Sắc thái phải giữ khi sang U2-B:** `PredictionBar` **KHÔNG chặn playback** —
nó trả `null` khi `busy` (`PredictionBar.tsx:75`) và mặc định THU GỌN; `nextStep`
không đọc `prediction` (khoá bởi `observe-lifecycle-w4b2r.test.ts`). Nên lỗi
không phải *"quiz chặn Quan sát"* mà là *"nút quiz có mặt thường trực trong
Quan sát"*, khiến bề mặt mặc định đọc thành hỏi-đáp. U2-B sửa **sự hiện diện**,
không phải gỡ một cái chốt (chốt vốn không tồn tại).

## 5. Ngữ pháp thị giác (PUBLIC · đo/suy từ nguồn)

`V` = VISIBLE · `P` = PARTIAL · `T` = TEXT_ONLY · `N/A` = không áp dụng.

| target | OBJECT | ROLE | RELATION | TRANSITION | PROGRESS |
|---|---|---|---|---|---|
| `binary_search` | V | V (low/mid/high/target) | V (`7 < 8,5`) | V (nửa bị loại xám) | V (vùng xét) |
| `linear_search` | V | V | V | V | V (khối chi phí) |
| `find_max`/`find_min` | V | V | V | V | P (vùng đã duyệt) |
| `count_if`/`sum_if` | V | V | V | **T** (bộ đếm/tổng ở vùng hành động, không trên sân khấu) | P |
| `insertion_sort` | V | V (HELD/GAP) | V | V | V (tiền tố đã sắp) |
| `bubble_sort` | V | V | V | V | P |
| `decimal_to_binary` | V | V | V (trọng số) | V | N/A |
| `logic.and_gate` | V | V | V (dây) | V | N/A |
| `packet_routing` | V (glyph W4B-2S) | V (nguồn/đích) | V (liên kết) | V (gói tin nhảy chặng) | V (tuyến đã đi) |
| `protocol_encapsulation` | V | V | V (tầng) | V | V |
| `generic.rule_scene` | V | V | **V** (quan hệ `rules`, fdcd4ea) | V | N/A |

**Khoảng trống ngữ pháp duy nhất còn lại: `count_if`/`sum_if` — TRANSITION là
TEXT_ONLY.** Biến tích luỹ (bộ đếm / tổng) sống trong `ScanInteractionModel`
(vùng hành động), **chưa chiếu lên sân khấu** — đã ghi từ W4B-2I là
REPRESENTATION_GAP, nay xác nhận lại bằng ngữ pháp.

## 6. Phụ thuộc chữ (§9)

| phân loại | target |
|---|---|
| `VISUAL_WITH_SHORT_CAPTION` | binary_search · linear_search · insertion_sort · bubble_sort · find_max/min · packet_routing · protocol_encapsulation · decimal_to_binary · and_gate · rule_scene |
| `REPRESENTATION_GAP` | **count_if · sum_if** (tích luỹ chỉ có ở chữ) |
| `TEXT_DEPENDENT` | *(không có)* |

Trùng kết quả bước cuối: **0/13** — W4B-2T đã dời quyền sở hữu về
`.result-banner`, thuyết minh chỉ giữ vế tiến trình (`processLeadOf`).

## 7. Bố cục sân khấu (đo Chrome 1920×1080)

| target | hUse | phân loại |
|---|---|---|
| 8 bài thuật toán | 36.3–59.7% | `COMPOSITION_ADAPTED_AND_INTENTIONAL` (`arrayChartLayout` thích ứng rồi **chạm trần** `MAX_COL_W` — W4B-2A) |
| `decimal_to_binary` | 17% | `COMPOSITION_ADAPTED_AND_INTENTIONAL` — **ca phản chứng**, kéo giãn sẽ phá quan hệ trọng số vị trí |
| `logic.and_gate` | 28.4% | `COMPOSITION_GOOD` (mạch nhỏ, luồng vào→cổng→ra liên tục) |
| `generic.rule_scene` | 37% | `COMPOSITION_GOOD` |
| `packet_routing` | 54.3% | `COMPOSITION_GOOD` (W4B-2T đã bỏ hằng số 610px) |
| `protocol_encapsulation` | *không đo được* | dựng bằng `div` ⇒ harness chỉ bắt `svg/table`. **Giới hạn phép đo, không phải lỗi sản phẩm** |

**Không có target nào `COMPOSITION_UNDERUTILIZED` sau W4B-2T.** Bài học giữ
nguyên: **tỉ lệ dùng thấp một mình KHÔNG phải lỗi.**

## 8. Biểu diễn theo miền (§13)

| phân loại | target |
|---|---|
| `DOMAIN_REPRESENTATION_GOOD` | packet_routing (glyph thiết bị) · and_gate/boolean_dag (hình cổng) · relational_table_query (`<table>` thật) · protocol_encapsulation (tầng/phong bì) · 3 target nhị phân (ô bit/trọng số) · rule_scene (quan hệ từ `rules`) |
| `GENERIC_ABSTRACTION_APPROPRIATE` | 11 target mảng (cột = giá trị/thứ tự/chỉ số) · tree.traversal · graph_traversal (đỉnh/cạnh trừu tượng là ĐÚNG) |
| `DOMAIN_ROLE_CARRIED_BY_TEXT` | *(không còn — W4B-2S đã đóng ca cuối)* |

## 9. Chính sách 2D/3D (§14 — chỉ ghi nhận)

21 `2D_ONLY` · 0 `3D_ONLY` · 1 `2D_AND_3D_JUSTIFIED`.

`protocol_encapsulation` giữ 3D vì nguồn khai
`pedagogicalFit: ["relation_clarity","dimensional_value","mechanism_fidelity"]`
+ `whyNot2d`: cơ chế là **LỒNG NHAU**, mà 2D phải quy ước hoá "bọc" thành xếp
chồng/thụt lề. `packet_routing` giữ `2D_ONLY` — chấm lại ở W4B-2S bằng 10 tiêu
chí, 3D **không thắng tiêu chí nào**. **Không đề xuất đổi gì.**

## 10. ArrayView — hai phát hiện lặp lại, CHỐT LẠI (§15)

### A. `#dcebfa` → **`TOKEN_DRIFT_CONFIRMED`**

`ArrayView.tsx:172`, trong `columnState`, giữa hai láng giềng dùng token
(`var(--accent-teal)`, `var(--hairline)`). Đây là màu nền cột **mặc định/nhàn
rỗi**.

**Không có token đúng nào đang tồn tại:** `--accent-sky` là `#62aef0` (đậm,
dùng cho "đang xét"), còn `#dcebfa` là **sắc nhạt** của chính nó;
`--canvas-soft` là `#f6f5f4` — **xám ấm**, thay vào sẽ đổi nghĩa (cột nhàn rỗi
hoá xám thay vì xanh nhạt).

→ **Khuyến nghị U2-C:** thêm **ĐÚNG MỘT** token ngữ nghĩa ở
`styles/tokens.css` (vd `--col-idle`), rồi `ArrayView` dùng nó.
Chủ sở hữu = `tokens.css`. **Không** mở đợt dọn token toàn hệ.

### B. transition `y`/`height` trên `<rect>` → **`HOOK_FALSE_POSITIVE_FOR_SVG_GEOMETRY`**

Bằng chứng, chốt để **thôi phát hiện lại mỗi wave**:

1. Phần tử là **SVG `<rect>`**; `y`/`height` là **thuộc tính hình học SVG**,
   không phải thuộc tính box-model CSS ⇒ không sinh reflow của layout HTML.
2. Cách sửa mà rule đề nghị **không áp dụng được**: `transform: scaleY()` sẽ co
   giãn **cả `stroke-width` lẫn bo góc `rx`**, làm méo mọi cột.
3. **Không có phép đo hiệu năng nào** cho thấy khuyết tật thật.

→ **Không sửa.** Nếu muốn tắt cảnh báo, dùng đúng một dòng ignore theo file;
nhưng khuyến nghị **giữ hiển thị** và sửa rule để nó hiểu hình học SVG.

## 11. Bug sản phẩm phát hiện khi audit (§19 — GHI, KHÔNG SỬA)

1. **`algorithm.selection_sort` khai `predict` nhưng không có mẫu offline** ⇒
   không kiểm được bằng trình duyệt ở mọi wave. Cân nhắc thêm mẫu (U2-C trở đi).
2. **Harness đo bố cục mù với sân khấu dựng bằng `div`** (`protocol_encapsulation`).
   Là giới hạn của `measure-composition.mjs`, nên mở rộng khi cần đo encap.
3. **9 target không có mẫu offline** ⇒ mọi khẳng định UX về chúng là **suy từ
   mã**, không phải đo. Đã đánh dấu *"không mẫu"* ở §2.

## 12. Câu hỏi chưa trả lời

- `count_if`/`sum_if`: chiếu biến tích luỹ lên sân khấu thuộc U2-C (bố cục) hay
  cần đổi `ScanInteractionModel` (hợp đồng)? **Chưa quyết.**
- `protocol_encapsulation` là L2 nhưng khai `predict` — sau U2-B nó còn bề mặt
  tương tác nào ngoài playback? Có thể lộ ra một `INTERACTION_CONTRACT_MISSING`
  vốn đang bị `PredictionBar` che.
