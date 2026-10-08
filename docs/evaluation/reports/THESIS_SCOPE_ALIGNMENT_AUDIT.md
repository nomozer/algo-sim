# SCOPE ALIGNMENT AUDIT — "Mô phỏng 3D hình học không gian"

> Audit, **không sửa mã, không tạo feature, không đổi taxonomy, không chạy
> benchmark**. Nguồn: đọc mã tại `a453473`, số liệu đo cơ học.
>
> Quyết định đổi đề: `STATUS_LEDGER §0-2026-08-24`.

---

## 0. Phát hiện quyết định — và nó KHÔNG nằm ở primitive

Ai nhìn vào cũng nghĩ vấn đề là *"thiếu điểm, đường, mặt phẳng"*. Thêm mấy kiểu
đó là việc dễ nhất trong toàn bộ danh sách. Vấn đề thật nằm ở **mô hình thực
thi**:

> IR hiện tại là **đột biến trạng thái RỜI RẠC**, với song ánh
> `frame k ⇔ trace[k]` (bất biến #31). Mỗi bước máy = một khung hình.

Hình học không gian THPT tách làm **bốn loại hoạt động**, và chúng **không cùng
số phận**:

| Loại hoạt động | Ví dụ | Khớp IR? |
|---|---|---|
| **Dựng hình / thiết diện** | dựng thiết diện của (α) với hình chóp S.ABCD | ✅ **khớp hoàn hảo** — là một dãy HỮU HẠN bước dựng |
| **Quan hệ & chứng minh** | chứng minh `AB ⊥ (SCD)` | ✅ khớp — chứng minh là dãy suy luận; kết luận là **phán quyết đúng/sai** |
| **Tính toán** | thể tích, khoảng cách, góc | ✅ khớp — tích luỹ vô hướng |
| **Kéo để thấy bất biến** (GeoGebra) | kéo đỉnh, quan sát thiết diện đổi | ❌ **KHÔNG khớp** — LIÊN TỤC, khung sinh từ thao tác người dùng chứ không từ thực thi chương trình |

**Ba loại đầu chiếm gần trọn chương trình Toán 11–12.** Loại thứ tư là thứ phá
kiến trúc — và cũng chính là *"gốc ý tưởng GeoGebra"* trong ghi chép cũ.

⇒ **Phạm vi luận văn phải khoanh vào ba loại đầu.** Đó không phải né tránh: nó
đúng luật `COVERAGE §2` (*chỉ mô phỏng khi có CƠ CHẾ ẨN*) — thiết diện có cơ chế
ẩn khổng lồ, học sinh không hình dung nổi giao tuyến trong đầu.

---

## 1. Phù hợp / phải định vị lại / thiếu hẳn

### 1.1 ĐÃ PHÙ HỢP — giữ nguyên, không đụng

| Thành phần | Vì sao khớp |
|---|---|
| **Ranh giới R0** | *LLM đọc đề, engine tất định diễn hoạt.* Với hình học nó còn **mạnh hơn**: giao tuyến, thiết diện, thể tích đều tính được **chính xác** — LLM tuyệt đối không được quyền phán |
| **Semantic IR (khung)** | `memory_declarations` + `statements` + `visual_bindings` + `RequestContract{facts, obligations}` — cấu trúc đúng nguyên |
| **Interpreter + trace/frame** | song ánh #31, pacer #32, fail-closed 4 mã — dùng lại nguyên |
| **Verification pipeline** | C₁a / C₁b / C₂ + `execution_authority` + scope gate |
| **Replay đa đầu vào** | đổi toạ độ đỉnh → đáp án phải đổi theo. **Ở hình học nó còn sắc hơn** vì đáp án là số, không phải bool |
| **Fail-safe** | `capability_gap` ≠ `verification_gap`, A/B đồng-primary |
| **Toàn bộ máy đánh giá** | SEALED · custodian · seed GVHD · oracle không import mã sản phẩm · taxonomy 8 tầng · luật mẫu nhỏ |
| **Vỏ sản phẩm** | store, timeline/transport, tầng lớp học, test 4 tầng |

### 1.2 PHẢI ĐỔI TÊN / ĐỊNH VỊ LẠI

| Hiện tại | Sau khi đổi |
|---|---|
| `AlgoSim` | tên gợi *algorithm*, nay sai miền |
| `docs/COVERAGE.md` neo **SGK Tin học** | neo **SGK Toán 11/12** — rubric giữ, nội dung thay |
| `prescribed_procedure` (enum thao tác thuật toán) | enum **thao tác dựng hình** |
| `simulation_id` kiểu `algorithm.*`, `binary.*` | `geometry.*` |
| Claim *"hỗ trợ dạy học môn Tin học"* | *"…môn Toán"* — và **`CURRICULUM_SUPPORT_PARTIAL` phải reset**, phủ chương trình cũ không chuyển sang môn mới |

### 1.3 THIẾU HOÀN TOÀN

**Đo cơ học, không ước lượng:** 9 primitive thị giác (`array_strip`,
`bar_chart`, `bit_register`, `graph_view`, `map_view`, `queue_view`,
`stack_view`, `table_grid`, `tree_element`) và 14 `MemoryType` (`int`, `str`,
`bool`, `float`, `array`, `stack`, `queue`, `matrix`, `map`, `set`,
`tree_node`, `graph`, `node_ref`, `null`) — **không một thứ nào là hình học**.

Và thiếu thứ nặng hơn primitive:

1. **Nhân hình học tất định** (geometry kernel) — giao tuyến hai mặt phẳng,
   giao điểm đường–mặt, đồng phẳng, hình chiếu, thể tích. **Đây mới là công
   việc thật**, và nó chính là chỗ R0 sống hay chết: LLM khai *"dựng giao tuyến
   của (SAB) và (SCD)"*, **engine phải tự tính ra giao tuyến ấy**.
2. **Nghĩa vụ hình học**: thuộc · song song · vuông góc · đồng phẳng · khoảng
   cách · thể tích · thiết diện-đúng.
3. **Renderer 3D thật** — hiện có **đúng 363 dòng** (`encap-ui3d.tsx`, cho đóng
   gói giao thức). Hình học cần: camera xoay, **nét đứt cho cạnh khuất** (quy
   ước vẽ hình không gian, không phải trang trí), nhãn 3D, tô thiết diện.
4. **Hệ toạ độ Oxyz** làm nền tất định cho mọi phép tính.

---

## 2. Mức độ lệch: **B** — cần thêm một lớp biểu diễn hình học

**Không phải A**, vì: `MemoryType` và tập primitive là **enum ĐÓNG**; thêm
`point`/`plane` là đổi schema IR ⇒ đổi thẻ văn phạm ⇒ **bump `CACHE_VERSION`**.
Và nghĩa vụ hình học cần **checker mới** trong `postconditions`. Đó không phải
"mở rộng domain" theo nghĩa `catalog.py` + một dòng `register…Domain()`.

**Không phải C**, vì mô hình thực thi **không cần viết lại**: dựng hình là dãy
bước rời rạc, đúng thứ interpreter đang làm. Song ánh #31, pacer, fail-closed,
C₁a/C₁b/C₂, replay, oracle — **giữ nguyên cơ chế**, chỉ thay nội dung.

> **B, với một điều kiện.** B chỉ đúng nếu phạm vi khoanh vào **dựng hình +
> quan hệ + tính toán**. Thêm *kéo-thả liên tục* vào phạm vi thì lập tức thành
> **C** — vì nó phá song ánh khung⇔bước, tức phá bất biến #31, tức phá luôn
> chỗ chắc nhất của hệ.

---

## 3. Hướng chuyển đổi TỐI THIỂU

**Không phá:** semantic IR (khung) · verification pipeline · replay · oracle ·
fail-safe. Cả năm đều **giữ nguyên cơ chế**.

Thêm như **một domain mới**, theo đúng lối mở rộng đã có:

| Nhóm | Thêm gì | Ghi chú |
|---|---|---|
| `MemoryType` | `point3` · `vector3` · `line3` · `plane3` · `polygon3` · `solid` | 6 kiểu, enum đóng như cũ |
| Biểu thức | `intersect_line_plane` · `intersect_plane_plane` · `midpoint` · `project_onto` · `cross`/`dot` | **engine tính**, LLM chỉ khai |
| Câu lệnh dựng | `construct_point` · `construct_line` · `construct_section` | mỗi cái = một bước trace |
| Nghĩa vụ | `incidence` · `parallel` · `perpendicular` · `coplanar` · `distance_value` · `volume_value` · `section_shape` | 7 nghĩa vụ, tập ĐÓNG |
| Primitive thị giác | `solid_view` · `plane_patch` · `point_label` · `section_fill` | 4 primitive |

⚠️ **`Transformation` và `Camera` KHÔNG phải semantic primitive.** Camera thuộc
**renderer** (bảng sở hữu `ARCHITECTURE_MAP §3`: renderer sở hữu layout/camera).
Đưa camera vào IR là để LLM điều khiển góc nhìn — vi phạm ranh giới, và mở đường
cho "hoạt hình đẹp mà state sai".

---

## 4. Kiến trúc mục tiêu — khả thi, với một sửa đổi

Đề xuất trong task:

```
Natural language → Geometry Contract → Semantic Program → 3D State → 3D Renderer
```

**Khả thi**, và `Geometry Contract` **đã có chỗ đứng sẵn**: nó chính là
`RequestContract{facts, obligations}` mà `analyze_contract.py` đang dựng — chỉ
đổi nội dung nghĩa vụ. **Không cần tầng mới**, chỉ cần thay bảng.

Nhưng thiếu một hộp, và thiếu nó thì R0 sụp:

```
Natural language
      ↓
Geometry Contract          ← RequestContract, đã có
      ↓
Semantic Program (IR)      ← khung đã có, thêm 6 kiểu + 5 biểu thức
      ↓
GEOMETRY KERNEL ★          ← THIẾU. Engine TỰ TÍNH giao tuyến/hình chiếu/thể tích
      ↓
3D Simulation State        ← interpreter đã có, mở rộng
      ↓
3D Renderer                ← có 363 dòng, cần dựng thật
```

★ là chỗ **quyết định luận điểm**. Nếu LLM được phép khai *"giao tuyến là đường
MN"* thì LLM đang sở hữu kết quả ⇒ **R0 vỡ**, và luận văn mất lập luận trung
tâm. Kernel phải tự tính, LLM chỉ được nói *"lấy giao tuyến của hai mặt phẳng
này"*.

---

## 5. Thành phần cần bổ sung

### Backend
- **Kernel hình học** (mới, ~400–600 dòng): giao tuyến mp–mp, giao điểm đt–mp,
  đồng phẳng, hình chiếu vuông góc, khoảng cách, thể tích khối đa diện, dựng
  thiết diện. **Số hữu tỉ / dung sai tường minh** — so sánh dấu phẩy động bằng
  `==` là nguồn sai lặng lẽ kinh điển ở hình học.
- **Interpreter**: thêm nhánh cho câu lệnh dựng; **fail-closed giữ nguyên luật**
  (hai mặt phẳng song song thì `intersect` phải NÉM LỖI, không trả `None` —
  đúng bài học đã sửa 2026-08-24).
- **Verifier**: 7 checker nghĩa vụ mới trong `postconditions.py`.

### Frontend
- **Three.js: đã có sẵn**, không phải thêm dependency.
- Renderer 3D: camera quỹ đạo, **nét đứt cạnh khuất**, nhãn đỉnh bám 3D, tô mặt
  thiết diện bán trong suốt, và **2D↔3D song song** — hình biểu diễn phẳng
  (thứ học sinh vẽ trong vở) cạnh khối 3D thật. Chính chỗ lệch giữa hai hình là
  **cơ chế ẩn** đáng mô phỏng nhất.
- Tương tác: **xoay camera** (là *view*, không đụng state ⇒ sạch, làm ngay
  được). **Kéo đỉnh** thuộc loại liên tục ⇒ **ngoài phạm vi**.

### Evaluation
- **Oracle độc lập DỄ HƠN hẳn so với thuật toán.** Hình học giải tích trong Oxyz
  cho đáp án **chính xác** bằng Python thuần: toạ độ vào → thể tích/góc/khoảng
  cách ra. Không phải cài lại thuật toán đang kiểm — tức **thoát được đúng cái
  khó đã buộc phải loại `predicate_verdict` khỏi taxonomy hồi tháng 8**.
- Benchmark: rubric + quy trình custodian **giữ nguyên**; thay corpus 189 bài
  SGK Tin học bằng bài tập hình học không gian Toán 11–12.
- `replay`: đổi toạ độ đỉnh, đáp án phải đổi theo — bắt "gán cứng đáp án" **sắc
  hơn** vì đầu ra là số thực, không phải bool 50/50.

---

## 6. Ba phương án phạm vi

| | Nội dung | Rủi ro | Đánh giá |
|---|---|---|---|
| **1** | Giữ framework AI + **thêm** domain hình học 3D, giữ luôn 24 module Tin học | Bảo vệ hai miền cùng lúc; hội đồng hỏi *"đề tài là hình học, sao nửa hệ là Tin học?"* | ❌ **Không** — 24 module thành gánh nặng phải giải thích |
| **2** | Chuyển **toàn bộ** sang hình học, gỡ hết Tin học | Vứt luôn bằng chứng SEALED #1 và mọi thứ đã đo | ❌ **Không** — bỏ tài sản đắt nhất |
| **3** | **Giữ hệ hiện tại làm FRAMEWORK, chứng minh bằng domain hình học 3D** | Phải nói rõ đâu là framework, đâu là miền chứng minh | ✅ **CHỌN** |

**Vì sao 3.** Luận điểm thành: *"một khung sinh mô phỏng tất định từ ngôn ngữ tự
nhiên, có kiểm chứng độc lập và biết từ chối — chứng minh trên miền hình học
không gian 3D."* Miền Tin học cũ trở thành **bằng chứng khung chạy được trên
nhiều miền**, tức từ gánh nặng hoá thành **điểm mạnh** (`cross_domain_matrix`
đã có sẵn để nói điều đó).

### Phạm vi tối thiểu hoàn thành được

**Ba lớp bài, cùng một cơ chế dựng:**
1. **Thiết diện** của mặt phẳng với hình chóp / lăng trụ (Toán 11)
2. **Quan hệ vuông góc / song song** — đường-mặt, mặt-mặt (Toán 11)
3. **Khoảng cách & thể tích** (Toán 11–12)

Ba lớp này dùng **chung một kernel**, nên chi phí không cộng ba lần. Cố ý **loại
khỏi phạm vi**: mặt tròn xoay · toạ độ Oxyz như một chuyên đề riêng · kéo-thả
liên tục · dựng hình bằng thước-compa.

---

## 7. Kết luận bắt buộc

### Có nên đổi hướng sang 3D không?
**Có — và nên đóng khung là QUAY VỀ, không phải rẽ ngang.** Ý tưởng gốc của dự
án chính là hình học động. Kiến trúc chịu được, phương pháp đo chuyển trọn, và
**oracle độc lập còn dễ hơn** ở miền hình học.

### Nếu đổi thì tối thiểu phải làm gì?
Theo thứ tự phụ thuộc, không đảo được:

1. **Chốt phạm vi 3 lớp bài** + khai vào ledger (0 dòng mã).
2. **Kernel hình học tất định** + oracle Python thuần **viết ĐỘC LẬP với
   kernel** — hai bản cài khác nhau cho cùng một bài toán, đó là nguồn tính độc
   lập.
3. **Mở IR**: 6 `MemoryType` + 5 biểu thức + 3 câu lệnh dựng ⇒ bump
   `CACHE_VERSION` (ba chỗ, theo lệ).
4. **7 nghĩa vụ + checker**, tập đóng.
5. **Renderer 3D** + 4 primitive thị giác.
6. **Corpus + SEALED mới** cho hình học; **quy trình giữ nguyên**.

### Giữ lại được bao nhiêu %?

**Đếm theo dòng là câu hỏi sai.** Hai con số, và con số thứ hai mới quan trọng:

| | Giữ |
|---|---|
| Theo **dòng mã** | **~45–55 %** — mất 24 module + DSL + toàn bộ domain frontend |
| Theo **phần khó nhất** (kiến trúc + máy đánh giá + kỷ luật claim) | **~85 %** |

Cụ thể: `app/ai/*` giữ ~80 % (prompt viết lại) · `semantic_program/*` giữ khung,
thay nội dung · `scripts/*` (sealed runner, replay, `reliability_v2`,
`merge_render_v`, freeze) giữ **~95 %** · 24 module + `dsl/` **~0 %** · vỏ
frontend giữ ~90 %, domain frontend ~0 %.

### Rủi ro deadline

| Rủi ro | Mức | Giảm thiểu |
|---|---|---|
| **Kernel hình học nuốt thời gian** | **CAO** | khoanh 3 lớp bài; đa diện lồi thôi; **không** mặt cong |
| Renderer 3D nuốt thời gian | **CAO** | 2D trước cho đúng state, 3D sau; nét đứt cạnh khuất là bắt buộc, còn lại cắt được |
| Corpus + custodian mới | TRUNG BÌNH | rubric và quy trình đã có, chỉ thay nội dung |
| LLM sinh IR hình học kém hơn IR thuật toán | TRUNG BÌNH | **đo trên DEV trước**, đúng hạ tầng đã dựng |
| **Bảo vệ hai miền cùng lúc** | **CAO** | chính là lý do chọn phương án 3 |

⚠️ **Rủi ro lớn nhất không nằm trong bảng: câu hỏi LLM chưa có đáp án.** Tên đề
mới **không nhắc** LLM. Nếu thầy muốn một công cụ trực quan 3D **thuần**, thì
kernel + renderer vẫn dùng được, nhưng toàn bộ hạ tầng LLM và SEALED thành
**gánh nặng chết**, và novelty phải tìm chỗ khác. **Phải hỏi trước khi viết dòng
mã đầu tiên.**
