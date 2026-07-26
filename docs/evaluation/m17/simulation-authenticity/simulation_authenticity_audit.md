# SIMULATION AUTHENTICITY AUDIT — PART A: PRODUCT EVIDENCE

**Ngày:** 2026-07-27 · **Nhánh:** `main` · **HEAD:** `3846e5b` · **Cây làm việc:** sạch
**Phạm vi:** read-only. Không sửa production, không commit, không push, không chạy live LLM.

---

## 1. Tóm tắt điều hành

Câu hỏi của audit: **sản phẩm có mô phỏng thật không, hay chỉ hiện kết quả dần dần?**

Trả lời: **có mô phỏng thật, ở 10/11 family.** Engine thực sự chạy cơ chế và phát ra
trace; renderer chỉ đọc. Đây không phải slideshow.

Nhưng có **hai chỗ phải nói thẳng**, và cả hai đều đã bị chính registry của kho mã
tự khai báo — audit này chỉ đọc lại cho đúng tên:

| # | Phát hiện | Mức |
|---|---|---|
| **F1** | `binary.character_encoding` (W3) **mượn hàm đổi cơ số nhưng bỏ qua cơ chế đổi cơ số**. Dãy bit được **thông báo**, không được **dẫn ra** — dù `divideSteps()` đã nằm sẵn trong đúng module mà nó import. | **P1** |
| **F2** | `structural_progressive_representation` (`generic.rule_scene`) là **PROGRESSIVE_VISUALIZATION**, không phải mô phỏng. Registry đã tự khai `result_authority = REPRESENTATION`. Nguy cơ nằm ở **cách trích dẫn**, không ở code. | **P1** |

Và một phát hiện về **dữ liệu mô tả sản phẩm**, quan trọng riêng cho luận văn:

| # | Phát hiện | Mức |
|---|---|---|
| **F3** | Backend `CATALOG` khai `visual_mode = "2d"` cho **cả 22 target**, kể cả 2 target thực sự có 3D. Nguồn sự thật 3D nằm ở frontend `supportedVisualModes`. **Bảng nào sinh từ field backend sẽ báo 3D = 0.** | **P0** (chỉ với luận văn) |

Không có target nào **BROKEN_OR_MISLEADING**. Không có target nào thiếu bằng chứng.

---

## 2. Phạm vi & phương pháp

- **Đọc mã thật** của engine + module, không đọc tài liệu mô tả engine.
- **Dùng lại artifact có sẵn** theo REUSE-FIRST (`docs/RULES.md §3`):
  RC1 **324 PNG** (7 renderer) · W2B-PATCH 18 · W2C 32 · W3 16 = **390 ảnh**.
- **Không chụp ảnh mới.** RC1 đã có sẵn cả `binary-base-conversion-hex-mid-*` và
  `generic-reveal-scene-mid-*` — đúng hai mid-state mà audit này cần. Chụp lại chỉ
  để tăng số lượng là vi phạm §9.
- **Đại diện:** 15/22 target, phủ **11/11 family**, tối đa 2 target mỗi family,
  và đủ 4 target bắt buộc (W2C, W3, generic, cả hai target 3D).

Ranh giới bằng chứng: đây là audit **tĩnh + ảnh cũ**. Không chạy live LLM, nên
**không** kết luận gì về việc Gemini có sinh được spec hợp lệ hay không.

---

## 3. Bảng bao phủ 11 family

| # | Family | Target | Đại diện đã đọc | `result_authority` |
|---|---|---|---|---|
| 1 | `single_pass_scan` | 6 | `find_max`, `scan` | computation |
| 2 | `comparison_sort` | 3 | `bubble_sort`, `insertion_sort` | computation |
| 3 | `interval_elimination` | 1 | `binary_search` | computation |
| 4 | `bounded_control_flow` | 1 | `bounded_control_flow` **(W2C)** | computation |
| 5 | `positional_representation` | 3 | `base_conversion`, `character_encoding` **(W3)** | computation |
| 6 | `boolean_composition` | 3 | `and_gate`, `boolean_dag` | computation |
| 7 | `structural_progressive_representation` | 1 | `rule_scene` **(generic)** | **representation** |
| 8 | `graph_traversal` | 2 | `graph_traversal` **(3D)**, `packet_routing` | computation |
| 9 | `layered_pdu_transform` | 1 | `protocol_encapsulation` **(3D)** | computation |
| 10 | `relational_table_query` | 1 | `relational_table_query` | computation |
| 11 | `tree_traversal` | 1 | `traversal` | computation |

**10/11 family khai `computation`. Đúng 1 family khai `representation`** — và đó chính
là family duy nhất bị xếp PROGRESSIVE_VISUALIZATION. Registry đã trung thực từ đầu.

---

## 4. Ma trận phân loại ba trục

| Family | Tính xác thực | Tương tác | Thị giác |
|---|---|---|---|
| `single_pass_scan` | REAL_SIMULATION | **PREDICTION_OR_WHAT_IF** | 2D |
| `comparison_sort` | REAL_SIMULATION | **PREDICTION_OR_WHAT_IF** | 2D |
| `interval_elimination` | REAL_SIMULATION | **PREDICTION_OR_WHAT_IF** | 2D |
| `bounded_control_flow` (W2C) | REAL_SIMULATION | TIMELINE_CONTROL | 2D |
| `positional_representation` → `base_conversion` | REAL_SIMULATION | TIMELINE_CONTROL | 2D |
| `positional_representation` → `decimal_to_binary` | REAL_SIMULATION | **MECHANISM_ACTION** | 2D |
| `positional_representation` → `character_encoding` (W3) | **PARTIAL_SIMULATION** | TIMELINE_CONTROL | 2D |
| `boolean_composition` | REAL_SIMULATION | **MECHANISM_ACTION** | 2D |
| `structural_progressive_representation` | **PROGRESSIVE_VISUALIZATION** | MECHANISM_ACTION | 2D |
| `graph_traversal` | REAL_SIMULATION | **PREDICTION_OR_WHAT_IF** | **2D_AND_3D** |
| `layered_pdu_transform` | REAL_SIMULATION | **PREDICTION_OR_WHAT_IF** | **2D_AND_3D** |
| `relational_table_query` | REAL_SIMULATION | TIMELINE_CONTROL | 2D |
| `tree_traversal` | REAL_SIMULATION | TIMELINE_CONTROL | 2D |

Tổng theo target đại diện (15): REAL **13** · PARTIAL **1** · PROGRESSIVE **1** ·
BROKEN **0** · INSUFFICIENT **0**.

---

## 5. Bằng chứng theo target đại diện

### 5.1 W2C — `algorithm.bounded_control_flow` → REAL_SIMULATION

`frontend/src/core/program.ts` là **trình thông dịch thật**: đánh giá điều kiện, rẽ
nhánh, đếm vòng lặp, chặn `max_execution_steps`. `Step.line` là **program counter**
thật, `Snapshot.vars` là **trạng thái biến** thật. Phân tích definite-assignment
(giao hai nhánh if/else) được **chạy**, không phải tra bảng.

Kiểm chứng mạnh nhất: executor **chỉ seed biến đã khởi tạo**, nên màn hình hiện
"Chưa có giá trị: y" — một trạng thái mà slideshow không thể tạo ra.

### 5.2 W3 — `binary.character_encoding` → **PARTIAL_SIMULATION**

**Phần THẬT** (không được hạ thấp):

- duyệt theo **code point** (`Array.from` / `codePointAt`), không theo UTF-16 unit —
  `encoding-module.test.tsx` chứng minh `ế` tách rời cho **3 hàng**, không phải 1;
- **progressive reveal là state, không phải CSS**: ở bước 0, DOM **không chứa** `65`
  lẫn dãy bit (W3-VR đã chứng minh bằng ảnh + test);
- **renderer không tự tính**: test trace bịa (`'A'` mang mã 999) buộc màn hình hiện
  **999**; nếu renderer gọi `codePointAt` nó sẽ hiện 65 và test đỏ.

**Phần THIẾU** — và đây là phát hiện trung tâm của audit:

> `runCharacterEncoding` gọi thẳng **`toBase(cp, 2)`**, tức là **hàm thuần**, và
> **bỏ qua `buildConvSteps()` / `divideSteps()`** đang nằm trong **chính module
> `convert-module.tsx` mà nó import**.

`base_conversion` có cơ chế thật, thuật minh từng phép chia:

```
${v} : ${base} = ${quotient} dư ${remainder} → chữ số ${digit}
Các số dư đọc NGƯỢC từ dưới lên sẽ thành kết quả.
```

W3 **không dùng chuỗi đó**. Học sinh thấy `65 → 1000001` như một **tuyên bố**.
Bước "tra mã" là mô phỏng thật; bước "đổi cơ số" là **hiện kết quả**.

Vì vậy: **correctness VERIFIED · visual REAL_VISUAL · authenticity PARTIAL_SIMULATION.**
Đúng như §10 đã cảnh báo — REAL_VISUAL không tự động nâng thành REAL_SIMULATION.

### 5.3 generic — `generic.rule_scene` → **PROGRESSIVE_VISUALIZATION**

```ts
// frontend/src/simulations/domains/generic/model.ts:108
export interface RevealStep {
  objects: string[];      // các object BẮT ĐẦU xuất hiện ở bước này
  narration?: string;
}
```

Một bước **chỉ khai object nào bắt đầu tồn tại**. Không có hệ quả miền nào giữa hai
bước — đúng khuôn §12 (hidden → revealed, không domain consequence). `move_along_path`
là **nội suy trên đường đã khai**, không phải quỹ đạo dẫn ra.

Registry đã tự khai `result_authority = REPRESENTATION` — **family duy nhất** làm vậy.
Code trung thực; rủi ro nằm ở chỗ **trích dẫn nó như mô phỏng thuật toán**.

### 5.4 Hai target 3D → 3D **có nghĩa**, không phải trang trí

`network.graph_traversal`:

- `ui3d.tsx:171` — `Network3DWorkspace({ state })` đọc `currentStep(state)`,
  `state.nodes`, `state.route`. **3D là góc nhìn thứ hai của cùng một state
  authoritative**, không phải scene song song.
- `ui3d.tsx:25` — camera/orbit sống trong closure/ref, **không bao giờ vào store**.
  Xoay camera không thể làm hỏng timeline.
- `render-parity.test.tsx` ép 2D và 3D phải khớp nhau.

`network.protocol_encapsulation` — **trục Z mang nghĩa miền**:

```ts
// encap-ui3d.tsx:26
export function layerDepth(layer: LayerId): number {
  const z = -LAYERS.indexOf(layer) * LAYER_GAP;   // ĐỘ SÂU CHÍNH LÀ TẦNG GIAO THỨC
```

Đây là lý do 3D chính đáng: gói tin đi **xuống** qua các tầng khi đóng gói và đi
**lên** khi mở gói. 2D phải vẽ ẩn dụ; 3D vẽ đúng thứ nó là.

### 5.5 `boolean_composition` — bề mặt tương tác mạnh nhất sản phẩm

`logic/index.ts:47` và `dag-module.tsx:370` có `apply()` **đổi state thật**: học sinh
bật/tắt đầu vào, engine tính lại, nút hạ nguồn đổi theo. Đây là **nhân → quả** thật,
không phải tua băng.

---

## 6. Red flags §7 — kết quả rà

| Red flag | Kết quả |
|---|---|
| `reveal_sequence` thuần hé lộ | **CÓ 1** — `generic.rule_scene`, đã xếp PROGRESSIVE_VISUALIZATION |
| Hàng/bảng tiền tính trong config | **KHÔNG** |
| Kết quả nằm sẵn trong config | **KHÔNG** — `FORBIDDEN_SPEC_KEYS` chặn (`character_encoding.py:38`, `program_spec.py:96`) |
| Renderer tự tính giá trị ngữ nghĩa | **KHÔNG** — **8 module** có guard trace bịa |
| State chỉ là visibility | **CÓ 1** — cùng `generic.rule_scene` |
| Cơ chế bị bỏ qua dù đã tồn tại | **CÓ 1 — W3 bỏ qua `divideSteps`** (F1) |

**Ghi nhận phụ (không phải lỗi):** luật "không được mang kết quả trong config" đang
được thi hành bằng **hai cách khác nhau** — `FORBIDDEN_SPEC_KEYS` tường minh cho 2
family mới, schema chặt cho các family cũ. Hoạt động đúng, nhưng nếu thêm family thứ
12 thì không có chỗ nào bắt buộc chọn cách nào.

---

## 7. Trục tương tác — điểm yếu hệ thống

| Mức tương tác | Số target đại diện | Ai |
|---|---|---|
| PREDICTION_OR_WHAT_IF | 6 | algorithm (scan/sort/search), network ×2 |
| MECHANISM_ACTION | 3 | logic ×2, `decimal_to_binary` |
| **TIMELINE_CONTROL** | **6** | **W2C**, **W3**, `base_conversion`, database, tree |
| OBSERVATION_ONLY | 0 | — |

**Mọi năng lực làm gần đây (W2C, W3) đều rơi vào TIMELINE_CONTROL.** Bề mặt tương tác
đang **thoái lui** so với các module cũ: `logic` cho học sinh bật đầu vào từ rất sớm,
còn hai family mới nhất chỉ cho tua băng.

Đáng chú ý nhất: **`database.relational_table_query` có mô hình dữ liệu giàu nhất sản
phẩm (5 cơ chế, pipeline thật) nhưng bề mặt tương tác nghèo nhất** (`apply: (state) => state`).

---

## 8. Trục 2D/3D

| | |
|---|---|
| Target có 3D | **2 / 22** (9%) |
| Ai | `network.graph_traversal`, `network.protocol_encapsulation` |
| 3D dùng chung state authoritative? | **Có** — đã dẫn chứng ở §5.4 |
| Trục Z có nghĩa? | **Có** ở `protocol_encapsulation` (Z = tầng OSI) |
| Có parity test 2D/3D? | **Có** (`render-parity.test.tsx`, `encap-render3d.test.tsx`) |

3D **hẹp nhưng thật**. Đây là điểm mạnh phòng thủ được: 2/22 là ít, nhưng hai chỗ đó
là hai chỗ 3D **đáng có**, và chúng không bịa ra một scene riêng.

---

## 9. Audit tuyên bố kho mã (§14)

| Tuyên bố | Trạng thái | Ghi chú |
|---|---|---|
| "mô phỏng tương tác **2D/3D**" | **ĐÚNG, có điều kiện** | 3D thật nhưng chỉ 2/22 target. Phải nói rõ phạm vi, không để hiểu là toàn bộ. |
| "LLM phân tích bài toán bằng ngôn ngữ tự nhiên" | **ĐÚNG** | LLM sinh spec, không sở hữu runtime (R0) |
| R0: LLM không sở hữu runtime | **ĐÚNG** | 8 guard trace bịa + `FORBIDDEN_SPEC_KEYS` |
| "11 family / 22 target" | **ĐÚNG** | verify lại bằng `CATALOG` trong checkpoint này |
| Backend `visual_mode` mô tả đúng 2D/3D | **SAI** | khai `"2d"` cho cả 22, kể cả 2 target 3D — xem F3 |

**F3 chi tiết.** `CATALOG` khai `visual_mode = "2d"` đồng loạt; nguồn sự thật 3D là
`supportedVisualModes` bên frontend (`network/index.ts:100`, `network/encap.ts:42`).
Hệ quả: **mọi bảng năng lực sinh tự động từ backend sẽ ghi 3D = 0** và tự bác bỏ chữ
"3D" trong tên đề tài. Đây là lỗi **mô tả**, không phải lỗi chức năng — sản phẩm vẫn
render 3D đúng — nhưng với luận văn thì nó là loại lỗi nguy hiểm nhất: **tự mâu thuẫn
bằng chính dữ liệu của mình.**

---

## 10. Giới hạn của audit

1. **Không chạy live LLM.** Không kết luận gì về tỉ lệ Gemini sinh spec hợp lệ.
2. **Tĩnh + ảnh cũ.** 7/22 target không đọc trực tiếp; suy ra theo family (các target
   này dùng chung engine và chung module đã đọc).
3. **Không chụp ảnh mới**, nên các kết luận thị giác dựa trên artifact RC1/W2C/W3 —
   tất cả đều chụp bằng Chrome thật qua CDP, không phải mock.
4. **Không đánh giá sư phạm.** Audit hỏi "có mô phỏng thật không", không hỏi "dạy có
   hiệu quả không".

---

## 11. PART B STATUS

```
PART B — THESIS CROSSWALK: BLOCKED
Lý do:     chưa có file DOCX luận văn thật.
Đã kiểm:   không có DOCX luận văn trong kho mã hoặc thư mục làm việc.
KHÔNG dùng: các DOCX đề cương cũ — chúng là bản đề xuất, không phải luận văn,
            dùng làm bằng chứng sẽ tạo crosswalk sai.
Connector:  Google Drive chưa xác thực trong phiên này (phiên không tương tác),
            nên không thể tự tìm DOCX. Người dùng cần cấp quyền trong phần
            connector của claude.ai, hoặc đưa thẳng đường dẫn file.
Chưa tạo:   thesis_evidence_crosswalk.md  (đúng quy định Part A)
```

Part A **không phụ thuộc** Part B: mọi kết luận ở trên đến từ mã sản phẩm, và giữ
nguyên giá trị bất kể luận văn viết gì. Khi có DOCX, Part B sẽ đối chiếu **tuyên bố
trong luận văn ↔ ma trận này**, và bảng §9 chính là chỗ nối.

---

## 12. Ưu tiên sửa

Chi tiết ở [correction_priority.md](correction_priority.md). Tóm tắt:

| Mức | Việc |
|---|---|
| **P0** | Sửa `visual_mode` (F3) — luận văn đang bị chính dữ liệu sản phẩm phản chứng |
| **P1** | W3 dùng lại `divideSteps` (F1); ghi rõ `rule_scene` là PROGRESSIVE_VISUALIZATION (F2) |
| **P2** | Nâng bề mặt tương tác cho database / W2C |
| **P3** | Thống nhất một cách chặn kết quả-trong-config |

**Khuyến nghị bao trùm: không thêm family thứ 12 trước khi đóng P0 và P1.**
Thêm family làm tăng *bề rộng*; hai việc trên sửa *độ tin cậy*. Với luận văn, một
sản phẩm 11 family nói đúng về chính nó mạnh hơn 12 family có một chỗ nói quá.

---

## ERRATA (bổ sung sau — không sửa kết luận)

### E1 — nhầm danh tính một target 3D · phát hiện 2026-07-27

**Sai:** §5.4 và §8 gọi `network.graph_traversal` là một trong hai target 3D.

**Đúng:** hai target 3D là **`network.packet_routing`** (`network/index.ts:94`
khai id, `:100` khai `["2d","3d"]`) và **`network.protocol_encapsulation`**
(`encap.ts:42`). `network.graph_traversal` **chỉ 2D** (`traverse-module.tsx:377`).

**Nguyên nhân:** `ui3d.tsx` đọc `state.route` / `state.nodes` — đó là state của
**packet_routing**. File nằm cạnh module traversal nên bị quy nhầm chủ.

**Ảnh hưởng:** **không đổi con số nào.** Tổng 3D vẫn **2/22**; mọi phân loại ba
trục giữ nguyên. Chỉ danh tính một target sai. Dòng `truth_source` ở §9
(`network/index.ts:100`, `network/encap.ts:42`) vốn **đã đúng** — vì
`index.ts:100` chính là packet_routing.

**Xử lý:** đã sửa trong `simulation_authenticity_matrix.json`; test P0 khoá đúng
hai id thật ở **cả hai phía**, nên sai sót này không thể tái diễn âm thầm.

Thân audit ở trên **giữ nguyên** như bằng chứng tại baseline `3846e5b`.

---

## TRẠNG THÁI SỬA (cập nhật sau checkpoint CORRECTION)

| Mục | Trạng thái |
|---|---|
| **P0** visual mode | **XONG** — `SimSpec.visual_modes` thành nguồn (danh sách đóng); `visual_mode` là property **dẫn xuất** nên không thể khai tay mâu thuẫn; descriptor mang `visual_modes`; parity FE↔BE khoá ở `capability-descriptors.test.ts`. **20 chỉ-2D · 2 có 3D.** |
| **P1b** claim alignment | **XONG** — `CODE_INDEX §0h` + danh tính `CURRENT_STATE`: **10 computation / 1 representation**, cấm đếm phẳng. |
| **P1a** W3 cơ chế | **XONG** — `binary.character_encoding` nay chạy CHÍNH `divideSteps()` của `base_conversion`; nhị phân **dẫn ra từ chuỗi số dư**, không còn gọi `toBase()` ở runtime. **PARTIAL_SIMULATION → REAL_SIMULATION**. Bằng chứng: `docs/evaluation/m17/w3-sim/`. |
| **P2** tương tác | chưa mở |
| **P3** hai cách chặn kết quả-trong-config | chưa mở |
