# COVERAGE.md — Phủ chương trình, phủ năng lực, và GIÁ TRỊ SƯ PHẠM

Kết quả hai audit trước M8: **PRE-M8 Coverage Audit** và **PRE-M8 Pedagogical
Simulation Value Audit**. Đây là nơi ghi **được phép tuyên bố gì** và **cấm tuyên
bố gì** về độ phủ của AlgoSim.

Cập nhật khi phạm vi phủ / bộ đề / chính sách sư phạm đổi. Khi tài liệu này lệch
với code/test → **CODE/TEST THẮNG** (theo `ARCHITECTURE_MAP.md §0`).

---

## 1. Nguồn chương trình (provenance) — đọc trước khi trích số liệu

**Nguồn:** 5 SGK trong `data/knowledge/sources/` (gitignore, không commit):
`tin-hoc-10.pdf`, `tin-hoc-11-cs.pdf`, `tin-hoc-11-ict.pdf`, `tin-hoc-12-cs.pdf`,
`tin-hoc-12-ict.pdf` — bộ **"Kết nối tri thức với cuộc sống"**, NXB Giáo dục Việt
Nam (2022), biên soạn theo **Chương trình GDPT 2018**.

Cấu trúc đã trích (từ `Mục lục` của từng cuốn):

| Sách | Số trang | Chủ đề | Bài |
|---|---|---|---|
| Tin học 10 | 170 | 6 | 34 |
| Tin học 11 — Khoa học máy tính (CS) | 151 | 6 | 31 |
| Tin học 11 — Tin học ứng dụng (ICT) | 155 | 7 | 31 |
| Tin học 12 — CS | 168 | 7 | 30 |
| Tin học 12 — ICT | 160 | 7 | 28 |

### GIỚI HẠN CỦA NGUỒN (bắt buộc nêu khi trích dẫn)

1. Đây là SGK của **một bộ sách (KNTT)** — **không phải** văn bản *Chương trình
   GDPT 2018* (văn bản quy phạm). Bộ sách khác có thể chia bài khác.
2. **Các PDF là ảnh scan, KHÔNG có lớp text** (đã kiểm: `extract_text()` trả về
   **0 ký tự** trên toàn bộ 170 trang của Tin học 10). Chỉ **Mục lục** được đọc
   bằng mắt. **Không OCR toàn văn** — OCR/RAG là việc **cố ý không làm**.
3. Độ mịn của taxonomy: **mức TÊN BÀI**, không phải mức *yêu cầu cần đạt*.

### ✅ Được phép tuyên bố
- "Phủ **đại diện**, **có neo nguồn**, ở mức tên bài của SGK KNTT (GDPT 2018)."
- "Phủ **năng lực mô phỏng** / **hình thức tương tác** / **mức độ phức tạp**."

### ❌ CẤM tuyên bố (overclaim)
- ~~"Phủ **toàn bộ** kiến thức Tin học THPT Việt Nam"~~
- ~~"Phủ **vét cạn** chương trình GDPT 2018"~~
- ~~"Mọi chủ đề trong chương trình đều mô phỏng được"~~
- ~~"3D **luôn** giúp học tốt hơn"~~ (xem §8)
- ~~"`practice_activity` đã hoàn thiện"~~ (xem §6)

---

## 2. Nguyên tắc sư phạm (chốt — ràng buộc mọi milestone sau)

> **Chỉ mô phỏng khi có: (a) CƠ CHẾ ẨN, (b) trạng thái biến thiên theo thời gian
> hoặc theo hành động, (c) lợi thế RÕ RÀNG so với text/ảnh/video/quiz.**
> Nếu học sinh đã thấy hết mọi thứ trong một hình tĩnh → mô phỏng chỉ thêm
> chuyển động, không thêm hiểu biết.

Hệ quả bắt buộc:

1. **Một chủ đề CÓ trong chương trình KHÔNG phải là lý do để mô phỏng nó.**
2. **KHÔNG** thêm module riêng cho mỗi bài học (ưu tiên: specialized có sẵn →
   generic DSL → mở rộng năng lực TÁI SỬ DỤNG được → `capability_gap`).
3. **KHÔNG** gọi một sơ đồ tĩnh là "executable simulation" (thực thi bằng code:
   `semantic._check_system_flow`, `moving=False` → cấm có process diễn biến).
4. **2D là mặc định.** 3D chỉ khi chiều sâu/phân tầng/không gian mang NGHĨA.
5. Dạng mạnh nhất là **phủ định dự đoán**: học sinh dự đoán → làm sai → engine
   tất định cho thấy hậu quả (`what-if branch`). Hiện **chỉ domain algorithm** có.
6. **(M9-S1) Mọi tương tác của người học phải CHẠM VÀO CƠ CHẾ ẨN và sinh hệ quả
   tất định.** Tương tác trang trí / gần-như-không-đổi-gì **không được admit** —
   phải gỡ, đóng khung (framed/challenge), hoặc ẩn. Tiền lệ thực thi:
   `frontend/.../algorithm/interaction-policy.ts` (free/framed/challenge/hidden,
   kèm `rationale` tự khai; khoá bằng `interaction-policy.test.ts`). Câu hỏi
   dự đoán phải nhắm ĐÚNG cơ chế của từng bài và KHÔNG được lộ đáp án sớm
   (narration bước quyết định là câu hỏi — `decision.test.ts`).
7. **(M9-UX2) Kiến trúc được phép TỔNG QUÁT, nhưng danh mục CÔNG KHAI hướng
   học sinh khoanh CÓ CHỦ ĐÍCH trong các trải nghiệm Tin học THPT đại diện.**
   Ví dụ liên miền (vd tam giác) có thể ở lại làm **fixture nội bộ** hoặc
   **case đánh giá** mà không được quảng bá cho học sinh. Hệ quả hai chiều:
   (a) gỡ một mẫu khỏi danh mục công khai **không** đồng nghĩa gỡ năng lực
   tái sử dụng đã nuôi nó; (b) phân loại bằng **metadata tường minh**
   (`OfflineSample.visibility`), cấm lọc theo chuỗi tiêu đề. Lịch sử học mở
   lại bằng envelope đã validate nên không phụ thuộc danh mục. Thực thi:
   `data/offline-catalog.ts` (`publicCatalog`); khoá bằng `catalog.test.tsx`.

---

## 3. Ma trận GIÁ TRỊ SƯ PHẠM theo chủ đề

### Tier 1 — GIÁ TRỊ CAO (có cơ chế ẩn + biến thiên + phủ định được dự đoán)

| Chủ đề (SGK) | Cơ chế ẩn | Result mode | Chiều | Hỗ trợ hiện tại |
|---|---|---|---|---|
| Sắp xếp (T11CS B21–22) | quyết định so sánh→đổi chỗ; đuôi đã sắp lớn dần | executable | **2D** | ✅ engine + **đã có bằng chứng (M8-PRE)** |
| Tìm kiếm nhị phân (T11CS B19) | **nửa bị loại** mỗi bước | executable | **2D** | ✅ |
| Lặp/rẽ nhánh/biến (T10 B17–21) | biến lặp, điều kiện, thân vòng lặp chạy khi nào | executable | **2D** | ⚠️ chỉ trong 8 thuật toán cố định |
| Đếm/tổng có điều kiện (T10 CĐ5) | biến tích luỹ **sống sót** qua vòng lặp | executable | **2D** | ✅ |
| Hệ nhị phân (T10 B4) | trọng số vị trí | executable | **2D** | ✅ |
| Dữ liệu lôgic (T10 B5) | bảng chân trị sau một bóng đèn | interactive_viz | **2D** | ✅ |
| Định tuyến gói tin (T10 CĐ2 · T12 CĐ2) | các CHẶNG; đường đi được **tính** (BFS) | executable | **2D** | ✅ |
| **Hệ thống thông tin / luồng dữ liệu** (T11 B10 · T12CS B29) | **HƯỚNG và ĐÍCH của dữ liệu** | interactive_viz → executable | **2D** | ✅ **mới (M8-PRE S2)** |

### Tier 2 — GIÁ TRỊ TRUNG BÌNH (có cơ chế, nhưng media tĩnh cũng làm được phần nào)

| Chủ đề | Cơ chế ẩn | Hỗ trợ | Thiếu gì |
|---|---|---|---|
| HTML/CSS (T12 CĐ4, 12 bài) | quan hệ markup ↔ kết quả hiển thị | ⚠️ structural + reveal | **practice**: học sinh tự dựng/đổi thứ tự |
| **CSDL: bảng, bản ghi, truy vấn** (T11 CĐ4, **cả hai ban**) | **vị từ WHERE giữ lại dòng nào** | ❌ | **table/grid + query** ← khối chương trình lớn nhất chưa phủ |
| Giao thức, phân tầng mạng (T12 B4 · 12CS B22–24) | đóng gói/mở gói qua các tầng | ✅ **M10 (2D+3D) · định tuyến NL M10-AI-ROUTE** | — (`network.protocol_encapsulation`; **3D có nghĩa: Z=tầng**). Còn thiếu: TCP/UDP branching, handshake — cố ý ngoài v1 |
| Hệ điều hành: tiến trình (T11 B1–2) | máy trạng thái | ❌ | FSM |
| Kiểm soát truy cập (T10 B9 · T11 B15) | quy tắc logic sau cánh cửa | ✅ **tái sử dụng `boolean`** | — (đã có case) |
| Mã hoá văn bản/âm thanh/ảnh (T10 B3, B6) | bảng mã / lấy mẫu | ⚠️ một phần | table/grid |
| Mảng 1D/2D (T11CS B17) | chỉ số ↔ giá trị | ⚠️ ngầm trong trace | mảng 2D |

### Tier 3 — GIÁ TRỊ THẤP / **KHÔNG MÔ PHỎNG** (§7)

Xem §7 — danh sách chống "phủ giả".

---

## 4. Phủ NĂNG LỰC mô phỏng (khác với phủ kiến thức)

| Năng lực | Trạng thái |
|---|---|
| Sequence/timeline · Iteration · Comparison · Accumulator · Search path | ✅ |
| **Sorting movement** | ✅ engine — **bằng chứng benchmark: có từ M8-PRE** (trước đó **0 case**) |
| Boolean rule · Weighted sum · Node-edge · Moving entity · Progressive reveal · Structural/textual · Toggle · Drag · Contextual edit | ✅ generic |
| **Data flow (edge có chiều)** | ✅ **mới (M8-PRE S2)** |
| Conditional branching · State transition | ⚠️ chỉ trong specialized |
| **Table/grid · Query/filter** | ❌ — ứng viên **post-M8** giá trị cao nhất (mở khoá CSDL, mảng 2D, bảng chân trị, bảng tính) |
| State machine (FSM) · Client/server hai chiều | ❌ |
| Stack/queue/tree | ❌ **KHÔNG có trong chương trình KNTT → scope creep** |
| **practice_activity** | ⚠️ **substrate, CHƯA phải một mode** (§6) |
| `capability_gap` (từ chối trung thực) | ✅ — 8 gap role, gate tất định, `gap_gate_recall = 1.0` |

---

## 5. Mức độ phức tạp (L1–L4) và Result mode

- **L1 atomic** (một cổng AND, tìm max) · **L2 composed** (gói tin, tổng trọng số,
  dựng web) · **L3 multi-stage** (dựng cảnh RỒI chạy quá trình trên cảnh đó) ·
  **L4 boundary** (vượt năng lực → phải từ chối).

**Result mode** (`EvalItem.result_mode`):

| Mode | Nghĩa | Trạng thái |
|---|---|---|
| `executable_simulation` | có state/process/timeline tất định | ✅ |
| `interactive_visualization` | cấu trúc/quan hệ có nghĩa + khám phá được | ✅ |
| `practice_activity` | học sinh tự dựng/thao tác, engine kiểm được | ⚠️ **PARTIAL — chưa implement** |
| `unsupported` | năng lực chưa đủ → từ chối trung thực | ✅ |

> **Baseline lịch sử (30 case) gần như toàn L1/L2 và KHÔNG có case sắp xếp.** Đó
> chính là lý do có pool mới — không phải vì baseline sai.

---

## 6. `practice_activity` — nói thật về trạng thái

**ĐANG CÓ:** học sinh *hành động được* (toggle, drag, what-if swap, edit tăng
dần) và engine *phán được* **chỉ khi có rule tất định** (drag bounds →
`InteractionFeedback`; không có rule → `unsupported_to_verify`).

**M8-PRE-LIP (mới):** thêm **`PredictionCapability`** — vòng lặp *Quan sát → Dự đoán
→ Nộp → engine tất định chấm → phản hồi là dữ liệu → canonical không đổi*, dùng
**một** UI chung cho **hai** domain (`network`: chọn chặng kế tiếp, ground truth =
BFS; `algorithm`: hệ quả của phép so sánh, ground truth = trace thật).
`network.packet_routing` **hết watch-only**.

**VẪN CHƯA CÓ:** cấu trúc **mục tiêu → nhiệm vụ → chấm điểm → theo dõi tiến độ**.
Không có gợi ý, không có dashboard, không có phản hồi hội thoại.

→ **`practice_activity` = PARTIAL / CHƯA IMPLEMENT. CẤM tuyên bố đã hoàn thiện.**
M8-PRE-LIP là **bằng chứng khả thi** (một capability + một UI phục vụ nhiều domain),
**không phải** practice mode đầy đủ.

**Ưu tiên #1 sau M8** — cao hơn cả việc thêm primitive mới (kể cả table/grid):
**learner practice/experimental mode**. Lý do: **ground truth đã có sẵn miễn phí**
trong mọi engine tất định (trace biết bước kế tiếp; BFS biết đường đi ngắn nhất).
Giá trị sư phạm của nó lớn hơn thêm hình vẽ mới.

---

## 7. Chủ đề GIÁ TRỊ THẤP / TRANG TRÍ — **cố ý KHÔNG có đề nào**

Chống "phủ giả" (fake coverage). Các chủ đề sau **có trong chương trình** nhưng
**không có cơ chế ẩn động** → mô phỏng chỉ là trang trí:

- Đạo đức, pháp luật, văn hoá môi trường số (CĐ3, **mọi khối**); bản quyền; ứng
  xử trên mạng → *static_explanation_better*.
- Hướng nghiệp (mọi khối) → **không mô phỏng**.
- Kĩ năng dùng phần mềm: đồ hoạ Inkscape (T10 CĐ4), chỉnh sửa ảnh/làm video
  (T11-ICT CĐ7) → **chính phần mềm đó mới là "mô phỏng"**.
- Thông tin & xử lí thông tin; thiết bị số (T10 B1–2, B7) → khái niệm.
- "Bên trong máy tính", "thiết bị mạng thông dụng" (T11 B4, T12 B3) → **sự kiện
  tra cứu** (thông số, cổng cắm); một tấm ảnh có chú thích tốt hơn.
- Lưu trữ đám mây, email, mạng xã hội (T11 B6–8) → thao tác công cụ.
- **Tổng quan AI / Học máy / KHDL** (T12 CĐ1, 12CS CĐ7) → "mạng nơ-ron 3D xoay
  tròn" là ví dụ kinh điển của mô phỏng trang trí.
- **Bất kỳ sơ đồ tĩnh nào bị gắn nhãn "mô phỏng"** — vd vẽ heading + paragraph
  thành hai cái hộp rồi gọi là mô phỏng web. (`d-webstatic` trung thực: nó là
  `interactive_visualization`, `static_structural`, **không** reveal giả.)

---

## 8. 2D / 3D — vị trí chính thức của M8

**M8 = architectural-first, pedagogically bounded 3D.**

- **Mục tiêu kiến trúc (chính):** *cùng* config/state/timeline → renderer 2D **hoặc**
  3D. Đây là hệ quả trực tiếp của **renderer-neutral state** (M7.FREEZE).
- **Chỉ 3D hoá case có lý do sư phạm thật.**
- **PoC ưu tiên:** kiến trúc mạng **phân tầng** / topology / dữ liệu di chuyển
  trong không gian — **ứng viên 3D có cơ sở duy nhất** tìm được trong chương trình
  (T12 B4; 12CS B22–24: đóng gói qua các tầng).
- **KHÔNG 3D hoá cho đẹp:** cổng logic · đổi nhị phân · **sắp xếp** · **mảng** ·
  cấu trúc trang web · **bảng CSDL**.

**Tuyên bố được phép của M8:**
> *"AlgoSim dùng lại config/state/timeline tất định trên nhiều renderer, và chỉ áp
> dụng 3D cho nội dung mà chiều sâu/phân tầng thực sự mang giá trị biểu diễn."*

**Tuyên bố bị cấm:** ~~"3D luôn giúp học tốt hơn."~~

### Kết quả M8 (Slice 1+2 — đã ship, xem `CURRENT_STATE.md §2`)

- **Đã chứng minh phần kiến trúc** của tuyên bố trên bằng PoC
  `network.packet_routing`: cùng module/config/engine state/timeline/action/
  PredictionCapability phục vụ renderer 2D **và** 3D; đổi mode không restart,
  không reset cursor, không đụng canonical state (bất biến #16).
- **M8 KHÔNG chứng minh** 3D dạy tốt hơn 2D cho bất kỳ chủ đề nào — nó chỉ chứng
  minh **renderer sharing**. Mọi phát ngôn sư phạm về 3D vẫn bị ràng bởi mục này.
- **Mạng phân tầng (ứng viên có cơ sở duy nhất) — (ghi chú M8) khi đó CHƯA làm**:
  cần năng lực tất định mới (trạng thái PDU biến đổi khi đóng gói/mở gói qua tầng).
  Hộp-tầng hiện dần bằng `reveal_sequence` là **progressive visualization**, CẤM
  dán nhãn *executable simulation* (phân biệt ở §6). → **✅ ĐÃ SHIP ở M10** với
  engine 9 bước tất định (xem mục M10 ngay dưới) — reveal-boxes vẫn bị cấm.
- Phạm vi 3D hiện tại: **một** module (`network.packet_routing`); logic/binary/
  algorithm/generic **cố ý** 2D-only.

### M10 — 3D SƯ PHẠM đầu tiên (đã ship, nhánh `m10-3d-ped`)

- `network.protocol_encapsulation` là mô phỏng ĐẦU TIÊN có **chiều sâu 3D mang
  nghĩa khái niệm**: `meaning_of_z = tầng giao thức` (X = chiều truyền gửi→nhận).
  Đóng gói đi xuống, truyền băng ngang, mở gói đi lên — **cùng engine/state** cho
  2D và 3D (PDU là danh sách phân đoạn ngữ nghĩa; renderer không tính lại).
- `network.packet_routing` được **phân loại lại TRUNG THỰC** là `architectural_poc`
  (Z ở đó chỉ tách nút trên/ngoài tuyến — bố cục). Khoá bằng `threeD` metadata
  (bất biến #18, `ARCHITECTURE_MAP §5`).
- 2D vẫn có, là baseline dễ đọc + **mặc định khi mở**; 3D là lựa chọn qua toggle.
  Tuyên bố được phép: *"dùng chiều thứ ba để mã hoá độ sâu tầng giao thức, cho
  biểu diễn 3D một vai trò ngữ nghĩa tường minh."* **CẤM**: ~~"3D dạy tốt hơn 2D."~~
- Là **MÔ HÌNH SƯ PHẠM** của đóng gói (một transport TCP; không bắt tay/seq/ack/
  phân mảnh/UDP) — không phải bộ mô phỏng chồng giao thức đầy đủ.
- **M10-AI-ROUTE (đã ship):** đề tiếng Việt về đóng gói qua tầng nay được pipeline
  LLM phân tích → classify → định tuyến tới `network.protocol_encapsulation` (không
  còn catalog/offline-only). Tuyên bố được phép: *"LLM phân tích đề ngôn ngữ tự
  nhiên và ĐỀ XUẤT ứng viên năng lực/config trong ranh giới được validate; engine
  tất định sở hữu và sinh trạng thái/timeline/hệ quả."* **CẤM**: ~~"LLM sinh ra mô
  phỏng."~~ Đề giao thức nâng cao (handshake/seq-ACK/retransmission/congestion/DNS)
  → **unsupported trung thực** (kiểm live 5/5, xem `CURRENT_STATE.md §nhật-ký-live`).
- `practice_activity` vẫn **PARTIAL / CHƯA làm**.

---

## 9. Bộ đề: baseline ĐÓNG BĂNG + pool mới

| Pool | Nội dung | Ràng buộc |
|---|---|---|
| `regression` | **30 case lịch sử** (`dataset.py`) | **ĐÓNG BĂNG.** Khoá bởi `test_dataset_du_30_de_3_nhom` + `test_datasets::test_dataset_lich_su_van_dong_bang`. Giữ so sánh được số liệu M7.13/M7.14/M7.14T |
| `curriculum` | phủ SGK đại diện (6 case) | chỉ chủ đề Tier 1/2 |
| `capability` | phủ hình thức mô phỏng (4 case) — **sorting**, L3, data-flow | vá lỗ hổng bằng chứng |
| `cross_domain` | **cùng năng lực, khác miền** (3 case) | bằng chứng tái sử dụng |
| `thesis` | **flagship 12 case** | mỗi case chứng minh một tính chất RIÊNG |

Chạy: `ALLOW_LIVE_AI=1 python -m app.evaluation.live --dataset thesis --suite full`

### LUẬT KẾT NẠP (thực thi bằng `datasets.check_admission`, khoá bằng test)

Case mới **chỉ** được thêm nếu trả lời rõ **6 câu**:

1. `learning_objective` — học sinh hiểu/làm được gì?
2. `pedagogical_rationale` — **cơ chế ẩn nào** được mô phỏng, và **vì sao hơn**
   text/ảnh/video/quiz?
3. `capability_family` — đang kiểm năng lực nào?
4. `complexity` — L1/L2/L3/L4?
5. `result_mode` — executable / interactive_viz / practice / unsupported?
6. `curriculum_area` — neo vào đâu trong SGK?

> **`pedagogical_rationale` mơ hồ → LOẠI case.** Không thêm đề chỉ vì chủ đề tồn
> tại trong chương trình.

**Metadata mới là optional + backward-compatible:** không metric nào đọc chúng →
ngữ nghĩa metric cũ **giữ nguyên tuyệt đối**. Bộ flagship gắn nhãn cho case lịch
sử bằng **bản sao** (`dataclasses.replace`), **không** sửa `DATASET`.

---

## 10. Bộ flagship (12 case) — mỗi case chứng minh một điều KHÁC nhau

| Case | L | Chứng minh |
|---|---|---|
| `cap-bubble` | L2 | **sắp xếp** — engine có sẵn mà trước M8-PRE **không có bằng chứng nào** |
| `cur-t11cs-binsearch` | L2 | định tuyến theo **năng lực** ("tìm nhanh"/"đã sắp xếp" → chia đôi) |
| `a-sumif` | L2 | điều kiện + tích luỹ; **và** capability gate **không nổ oan** |
| `a-binconv` | L1 | biểu diễn dữ liệu (trọng số vị trí) |
| `b-xor` | L1 | DSL generic **compose được** cổng logic |
| `a-and` | L1 | engine chuyên biệt cho cùng khái niệm → **cặp** với `b-xor` = ranh giới specialized ↔ generic (**trùng lặp DUY NHẤT được phép**) |
| `a-packet` | L2 | đường đi do **BFS tất định** sinh — LLM không sinh timeline |
| `d-webbuild` | L2 | cấu trúc + thời gian |
| `d-webstatic` | L1 | **trung thực scene-mode**: cảnh tĩnh không được giả vờ có diễn biến |
| `xd-access-boolean` | L2 | **tái sử dụng** `boolean` sang miền bảo mật — không thêm module |
| `xd-order-workflow` | L3 | **tái sử dụng** node+edge+moving_entity **ngoài miền mạng** (S2) |
| `c-geo-complex` | L4 | **từ chối trung thực** bài "nhìn có vẻ vẽ được" → `capability_gap` |

**Không** nhồi biến thể OR/NOT/XOR — chúng chứng minh lặp lại đúng một năng lực.

---

## 11. Tái sử dụng liên miền (bằng chứng cho tuyên bố kiến trúc trung tâm)

| Năng lực | Dùng lại ở các miền |
|---|---|
| `boolean` | cổng logic (T10 B5) · **kiểm soát truy cập** (T11 B15) · đèn cầu thang (XOR) |
| `weighted_sum` | **đổi nhị phân** (T10 B4) · **mã ASCII** (T10 B3) |
| `node`+`edge` | mạng · đồ thị · **hệ thống thông tin** · quy trình nghiệp vụ · hình học (node không node_type) |
| `moving_entity`+`move_along_path` | **gói tin** · **dữ liệu qua các công đoạn xử lí** |
| `reveal_sequence` | dựng hình · dựng trang web · **dựng mạng từng bước** |
| `container`+`heading`/`paragraph` | trang web · tài liệu · mô tả I/O của hệ thống |

**Không thêm module cho từng miền — dùng lại primitive.**

---

## 11b. Ngân sách object & NÉN DƯ THỪA AN TOÀN (M8-PRE plan C)

`max_objects = 20` **không phải bất biến ngữ nghĩa** — nó là **ngân sách chứa đầu ra
LLM + ngân sách dễ đọc của renderer**. Engine không phụ thuộc con số này.

**Bằng chứng (đo live):** mọi cảnh hệ thống HỢP LỆ đều nằm gọn trong 20 (11–19 object).
Chỉ bản nháp BỊ PHỒNG mới vượt: Gemini vừa đặt `label` inline cho node/edge, vừa tạo
thêm **object `label` rời lặp lại đúng chuỗi đó**.

→ **Không nâng hạn mức toàn cục. Không capability-aware budget.** Thay bằng
`compact_redundant_labels` (cả hai tầng validator):

| Được phép gỡ | KHÔNG BAO GIỜ gỡ |
|---|---|
| object `label` rời có chữ **TRÙNG HỆT** nhãn inline của node/edge có thật | label mang chữ **riêng** (có nghĩa) |
| …và **chỉ khi** cảnh đã **vượt** hạn mức | label đang bị **tham chiếu cấu trúc** (rule/interaction/parent/path) |
| | bất cứ gì chỉ để "lách" hạn mức |

Cấm tuyệt đối: đoán liên kết theo **khoảng cách**; dùng **LLM** để nén; bỏ **chữ có
nghĩa**. Cảnh đang trong hạn mức **không bị đụng tới** → 0 bề mặt regression.
Thứ tự: candidate → suy `directed` (tất định) → nén dư thừa an toàn → kiểm hạn mức →
validator còn lại → engine smoke.

## 12. Cái gì phải ĐÓNG BĂNG

1. `dataset.py` — 30 case lịch sử (id, text, group, expectation, tags).
2. **Ngữ nghĩa metric** trong `harness.py` (`EvalReport.metrics()`); `gap_gate_recall`
   là metric **song song**.
3. **R0** — LLM không bao giờ sinh timeline/state/steps/kết quả.
4. **8 gap role + capability gate** — đây là **bảo chứng trung thực**, không phải TODO.
5. **Trung thực scene-mode** — cảnh tĩnh không được gắn reveal giả.
6. **Renderer-neutral state** — không có pixel/layout trong engine state.
7. Validate **hai tầng** + **manifest là nguồn chân lý duy nhất**.
8. Danh sách **DO NOT ADD BEFORE M8** (`CURRENT_STATE.md §5b`) — gồm **không thêm
   hệ learner-feedback mới** (vì vậy `practice_activity` chờ sau M8, dù nó là hạng
   mục giá trị nhất).
9. **Ranh giới canonical ↔ learner** (`CORRECTNESS.md §2`): hệ thì phải đúng hoặc
   từ chối; **học sinh thì được phép sai**.
