# RESEARCH_GAP_AND_CONTRIBUTIONS — khoảng trống và đóng góp

> Nguồn: `LITERATURE_COMPARISON_MATRIX.md` (20 hàng) · `RELATED_WORK_SEARCH_PROTOCOL.md`
> (giao thức + **sai lệch giao thức**) · `CLAIM_TO_EVIDENCE_MAP.md` (bằng chứng nội bộ).
> Ngày: **2026-09-10**, HEAD `df8ad21`. `APPLICATION_LLM_CALLS = 0`.
>
> ⚠️ **Điều kiện đọc.** Khảo sát đi qua **một** giao diện web tổng quát, **chưa**
> truy vấn native IEEE Xplore / ACM DL / SpringerLink / Google Scholar. Mọi phát
> biểu dưới đây mang giới từ *"trong phạm vi đã khảo sát"*. Không cụm nào trong
> file này là *"lần đầu tiên"*, *"duy nhất"*, *"chưa từng có"* hay *"hoàn toàn
> mới"* — trừ hai lần dùng *"duy nhất trong tập khảo sát"* đã khai ở
> `CLAIM_AUDIT.json`.

---

## 1. Ba loại khoảng trống — không gộp

### 1.1. Khoảng trống **NGHIÊN CỨU**

Điều các công trình hiện có chưa giải quyết đồng thời. Bảy điều kiện, và điểm
đáng nói là **không điều kiện nào tự nó mới**:

| # | điều kiện | ai đã làm | ai chưa |
|---|---|---|---|
| 1 | đề hình học **không gian** bằng ngôn ngữ tự nhiên | Draw2Think (khai phủ hình không gian) | phần còn lại của nhóm sinh hình đều 2D |
| 2 | chương trình hình học trung gian **có kiểu** | GeoLoom (GeoLingua), GeoBuildBench (DSL), Geoparsing (ngôn ngữ hợp nhất) | kiểm tra **kiểu** thì `NR` ở mọi hàng ngoài AlgoSim |
| 3 | kiểm chứng **tất định** | MagicGeo, GeoLoom, GF-Reasoner, SD-GPS, VeriGeo | — |
| 4 | **số học chính xác** (không `float` trong miền hình học) | — (VeriGeo gần nhất, nhưng cách biểu diễn số là `UNCLEAR`) | tất cả |
| 5 | mô phỏng **3D tương tác** | GeoGebra/Desmos/Cabri — nhưng **không** nhận đề bài | mọi hệ nhận đề bài |
| 6 | **phát lại quá trình dựng hình** | VeriGeo (vết thực thi), Text2CAD (chuỗi lệnh) | không ai gắn vết ấy với **khung hình 3D tua được** |
| 7 | **từ chối có cấu trúc** khi không kiểm chứng được | VeriGeo (*repair or reject* trong pipeline) | không ai đưa lời từ chối **ra tới người học** kèm giai đoạn dừng và mã lỗi |

**Phát biểu khoảng trống, dạng chặt:** các nghiên cứu được khảo sát chưa đồng
thời hỗ trợ **(1) + (4) + (5) + (6) + (7)**. Giao của bảy điều kiện là chỗ trống;
từng điều kiện riêng lẻ thì không.

⚠️ **Hai công trình phải nêu tên ngay trong phát biểu**, nếu không phát biểu sẽ
mỏng hơn nó tưởng:

- **GeoBuildBench (2026)** đã đặt đúng bài toán *"đề tự nhiên → chương trình DSL
  → hình thoả ràng buộc kiểm được"* thành một benchmark. Ý tưởng nền **không
  mới**. Khác biệt còn lại: 2D, tiếng Trung, và nó **đo** chứ không **phục vụ**.
- **Draw2Think (2026)** khai phủ cả hình học không gian, dựng hình qua constraint
  engine của GeoGebra, báo +16,4% ở hình không gian. Vậy *"dựng hình 3D từ đề
  bài"* **không** còn là chỗ trống. Chỗ trống nằm ở **mục đích và thẩm quyền số**:
  Draw2Think dựng hình để **giải đúng hơn**; AlgoSim dựng hình để **người học xem
  được quá trình**, và bắt mọi đại lượng đi qua một nhân số học chính xác riêng.

### 1.2. Khoảng trống **KỸ THUẬT**

Lỗi cụ thể đã gặp và đã đóng trong kho này. Đây là đóng góp **kỹ thuật**, không
phải điểm mới khoa học — nhưng chúng là thứ làm luận điểm đứng được.

| # | lỗi | trạng thái | bằng chứng |
|---|---|---|---|
| K1 | chương trình **hợp lệ JSON nhưng sai quan hệ hình học** | đóng — `ir_static_check` + `GEOMETRY_CHECKERS` + hậu điều kiện | `stage_a_first_attempt.json`: `p3` bị chặn ở `ir_static` (`IR_OPERAND_TYPE: cần solid, có curved_solid`) rồi sửa được |
| K2 | **nguồn dữ kiện tồn tại nhưng nội dung không khớp** | đóng — bất biến nguồn; và bản vá `chuan_hoa_dau_tru` (U+2212) | trước bản vá, `2x − z + 12 = 0` bị cắt thành `z + 12 = 0` rồi báo vi phạm **trên một chương trình đúng** |
| K3 | **đáp số đúng nhưng hình/bước dựng sai** | đóng về mặt phương pháp — ba cột ghi **riêng** (đáp số · trace · scene3d), không cột nào suy từ cột kia | `FINAL_SUMMARY.json`, 9 cột độc lập |
| K4 | **khối lõm cho thể tích sai** | đóng — tổng có dấu trên mặt biên, `abs` đúng một lần ở cuối | trước bản vá hệ **phục vụ** khối lõm với số **28** thay vì **20**; nay `p2 = 96` khớp oracle shoelace có dấu |
| K5 | **mặt phẳng khác nhau cho cùng diện tích thiết diện** | đóng — phân xử conic bằng phép so **hữu tỉ**, không khai căn | `p6 = 25π√5`, `p7 = 2π√6`, khớp ba oracle độc lập |
| K6 | **mô phỏng thành công nhưng thiếu trace hoặc producer** | đóng — `producer`/`depends` bắt buộc trên mọi vật dựng | `replay_demo_cases.py` kiểm mọi ca |
| K7 | **hình chưa kiểm chứng vẫn có nguy cơ được phục vụ** | đóng — fail-closed sáu tầng | `NEGATIVE_FAIL_CLOSED 2/2`, `SILENT_WRONG_ANSWER 0` |
| K8 | **bộ đo sai theo hướng tố cáo hệ** | đóng — ánh xạ theo `kind` của nghĩa vụ thay vì theo tên biến mô hình tự đặt | lượt gốc báo `SILENT_WRONG_ANSWER = 6` trên một hệ **không phạm lỗi nào**; xem `THESIS_FINAL_ACCEPTANCE_EXECUTION.md` §5 |

⚠️ **K8 đáng kể ngang một đóng góp kỹ thuật.** Nó là bằng chứng cho một luận
điểm phương pháp: *một provider giả giống bản mẫu quá mức thì không kiểm được thứ
chỉ sai khi mô hình được tự do.*

### 1.3. Khoảng trống **SẢN PHẨM**

Giao diện · nhãn hiển thị · responsive · thẩm mỹ · độ dễ nhìn. **Có giá trị sử
dụng, không được gọi là điểm mới khoa học.** Ví dụ đã đóng trong kho: nhãn hiển
thị 10/12 → 12/12 · nét thấy–khuất đọc được · thẻ từ chối một giọng · miếng mặt
phẳng đặt theo vùng hình học.

Một mục ở đây bị **từ chối** và đã gỡ: prototype giao diện `design/frontend-product-prototype`
(`USER_APPROVAL = REJECTED`, 2026-09-10) — bố cục kiểu dashboard mẫu, renderer
chưa đạt trực quan, hình bị cắt. Ghi lại để đừng đếm nó vào đóng góp.

---

## 2. Đóng góp — phân loại bốn mức

```
C1 — NOVELTY_CANDIDATE          1
C2 — INTEGRATIVE_CONTRIBUTION   3
C3 — ENGINEERING_CONTRIBUTION   4
C4 — PRODUCT_FEATURE            3
```

### C1 — `NOVELTY_CANDIDATE` (1 mục, hẹp, có điều kiện)

> **C1.1 — Nhân số học chính xác làm thẩm quyền DUY NHẤT của đáp số trong một
> đường ống LLM → dựng hình, với đáp số giữ nguyên dạng ký hiệu và được đối chiếu
> bằng một oracle cài độc lập.**

Căn cứ nâng lên `NOVELTY_CANDIDATE`: trong 19 hàng của ma trận, cột *"số học
chính xác"* trả về **`Không`** cho hai hàng đã đọc rõ (MagicGeo — tối ưu toạ độ;
GeoLoom — tối ưu Monte Carlo) và **`NR`/`UNCLEAR`** cho phần còn lại. Không hàng
nào khai giữ đáp số ở dạng chính xác như `3√6`, `25π√5`, `2π√6`.

⚠️ **Ba điều kiện phải đi kèm mỗi lần dẫn C1.1:**

1. **`NR` không phải `Không`.** Mười ba hàng chưa công bố trục này. C1.1 là *chưa
   tìm thấy công trình tương đương*, không phải *không tồn tại*.
2. **VeriGeo (2026) là đối thủ gần nhất** và phải nêu tên: nó có ba chặng kiểm
   *numerical consistency / analytical realizability / global consistency*. Bản
   tóm tắt **không** nói cách biểu diễn số, nên trục này còn `UNCLEAR`. Nếu đọc
   toàn văn VeriGeo và thấy nó giữ dạng chính xác, **C1.1 phải hạ xuống C2**.
3. Bằng chứng nội bộ của C1.1 là **12/12 đại lượng, n = 1 mỗi họ, một lượt** —
   đủ để nói *hệ làm được*, không đủ để nói *hệ ổn định*.

### C2 — `INTEGRATIVE_CONTRIBUTION` (3 mục)

> **C2.1 — Đóng góp chính, đúng như giả thuyết của wave:** chuyển đề hình học
> không gian **tiếng Việt** thành chương trình dựng hình 3D **có kiểu**, rồi dùng
> các cổng tất định và số học chính xác để **chỉ phục vụ** những mô phỏng thoả dữ
> kiện nguồn. Kết luận dự kiến của wave được **giữ nguyên** sau khảo sát.

> **C2.2 — Ranh giới R0 cưỡng chế bằng LƯỢC ĐỒ, không bằng lời dặn:** mọi toán
> hạng hình học trong IR là **TÊN** của vật đã dựng. Bằng chứng nó là ràng buộc
> thật chứ không phải khẩu hiệu: `RAW_GEOMETRY_LITERAL_ATTEMPTS = 0` trên 42/42 ô
> toán hạng ở bản thô, và ca `n1` **đã thử** bịa ba điểm rồi bị chặn.
> ⚠️ Không phải mới hoàn toàn: ở MagicGeo/GeoLoom, LLM cũng chỉ phát ràng buộc
> còn solver tính toạ độ. Cái khác là chỗ cưỡng chế — **lược đồ dữ liệu** thay vì
> phân công vai trò trong pipeline.

> **C2.3 — Song ánh `khung k ⇔ bước k`** giữa vết thực thi và khung hình 3D, cho
> phép tua lại đúng quá trình dựng. Trong tập khảo sát, vết thực thi có (VeriGeo,
> Text2CAD) và tương tác 3D có (GeoGebra/Desmos/Cabri), nhưng **không hàng nào có
> cả hai gắn bằng một song ánh**.

### C3 — `ENGINEERING_CONTRIBUTION` (4 mục)

**C3.1** Biên thẩm định sáu tầng fail-closed (grounding → phủ cấu trúc → tĩnh →
thực thi → phủ đã hiện thực → hậu điều kiện), 7/7 qua cả sáu tầng.
**C3.2** Nền tất định cho **khối lõm** (K4) và **thiết diện xiên** của trụ/nón
bằng phân xử conic hữu tỉ (K5).
**C3.3** Cơ chế **trung thực năng lực** ba mức (`supported` · `foundation_only` ·
`unsupported`) — phân biệt *không làm được* với *làm được nhưng chưa kiểm chứng
được*.
**C3.4** Kỷ luật đo lường: candidate đóng băng · niêm phong trước lượt chạy ·
oracle cài độc lập · và **tự bác bộ đo của chính mình** khi nó sai (K8).

### C4 — `PRODUCT_FEATURE` (3 mục)

**C4.1** Nhãn hiển thị bằng tên toán học có nghĩa (12/12).
**C4.2** Nét thấy–nét khuất động, phân loại che khuất bằng oracle độc lập 3/3.
**C4.3** Thẻ từ chối hiển thị bằng tiếng Việt cho người học (73/73 phép kiểm).

⚠️ C4 **không** được đếm vào đóng góp khoa học. Nó là điều kiện để demo được.

---

## 3. Phát biểu khoảng trống — ba phiên bản

### 3.1. Phiên bản ngắn (2 câu) — dùng cho phần mở đầu

> Các công cụ hình học động cho phép dựng và quan sát hình không gian nhưng đòi
> người dùng tự dịch đề bài thành chuỗi thao tác, còn các hệ sinh hình từ văn bản
> mới xuất hiện gần đây thì hầu hết dừng ở hình học phẳng và ở một hình vẽ tĩnh.
> Khoá luận này nhắm vào khoảng giao chưa được bao phủ đầy đủ giữa chúng: từ một
> đề hình học **không gian** viết bằng tiếng Việt, sinh ra một **mô phỏng 3D tua
> được theo từng bước dựng**, trong đó mọi đại lượng được tính bằng **số học chính
> xác** và mô phỏng nào không kiểm chứng được thì bị **từ chối có địa chỉ** thay
> vì được vẽ ra.

### 3.2. Phiên bản học thuật (1 đoạn) — dùng cho tổng quan nghiên cứu

> Ba hướng đang tiến gần nhau. Thứ nhất, phần mềm hình học động (GeoGebra, Cabri
> 3D, Desmos 3D) cung cấp môi trường dựng và thao tác hình không gian, nhưng đầu
> vào là **thao tác của người dùng**: theo mô tả chính thức của cả ba sản phẩm,
> không sản phẩm nào nhận một đề bài bằng ngôn ngữ tự nhiên rồi tự dựng hình. Thứ
> hai, một nhóm công trình 2024–2026 sinh sơ đồ hình học từ văn bản và dùng bộ
> giải hình thức để bảo đảm tính đúng — MagicGeo, GeoLoom, GeoBuildBench — nhưng
> tất cả đều làm **hình học phẳng**, đầu ra là một hình tĩnh, và toạ độ được tìm
> bằng **tối ưu số** chứ không bằng số học chính xác. Thứ ba, hướng LLM sinh
> chương trình hình thức cho bộ giải (PAL, GF-Reasoner, AutoGPS, SD-GPS,
> AlphaGeometry) đặt mục tiêu ở **đáp số hoặc chứng minh**, không ở một mô phỏng
> người học xem được. Hai công trình vượt ra khỏi khuôn ấy và phải được nêu tên:
> *Geoparsing* (ACL 2026) xây ngôn ngữ hình thức hợp nhất cho cả hình phẳng và
> hình không gian, nhưng chạy chiều **hình → ngôn ngữ hình thức**; và
> *Draw2Think* (2026) dựng hình qua bộ máy ràng buộc và có báo cáo kết quả trên
> hình không gian, nhưng nhằm **nâng độ chính xác giải bài**, với thẩm quyền số
> nằm ở bộ máy có sẵn. Kết quả khảo sát cho thấy còn thiếu một hệ đồng thời:
> nhận đề **hình học không gian** bằng ngôn ngữ tự nhiên; biểu diễn nó bằng một
> chương trình trung gian **có kiểu** mà mọi toán hạng hình học là tên của vật đã
> dựng; tính mọi đại lượng bằng **số học chính xác** trên ℚ mở rộng bởi căn thức
> và π; dẫn xuất một **cảnh 3D tua được** giữ song ánh giữa khung hình và bước
> dựng; và **từ chối có cấu trúc** khi không kiểm chứng được, thay vì hạ chất
> lượng trong im lặng.

### 3.3. Phiên bản đầy đủ

**Bối cảnh.** Hình học không gian là phần chương trình Toán 11–12 mà người học
gặp khó nhất ở khâu *hình dung*, và tài liệu giáo dục đã đo được rằng công cụ
trực quan hoá giúp đúng chỗ ấy (Juandi và cs. 2021; Medina Herrera và cs. 2024 —
lưu ý mẫu của cả hai đều không phải học sinh THPT Việt Nam).

**Những hướng đã được nghiên cứu.** (a) Phần mềm hình học động, hướng lâu đời
nhất, có đánh giá định lượng. (b) LLM sinh chương trình cho runtime tất định
(PAL) — vì mô hình phân rã bài tốt nhưng sai ở phần tính (Mirzadeh và cs. 2025).
(c) Suy luận hình học tự động có kiểm chứng hình thức (AlphaGeometry). (d) Sinh
sơ đồ hình học từ văn bản với bộ giải hình thức (MagicGeo, GeoLoom,
GeoBuildBench, SDE-GPG, VeriGeo). (e) Benchmark hình học **không gian** cho mô
hình đa phương thức (SolidGeo, DynaSolidGeo) — cho thấy mô hình còn cách xa mức
người ở miền 3D.

**Điểm các hướng chưa đồng thời giải quyết.** Hướng (a) không nhận đề bài. Hướng
(b) và (c) dừng ở đáp số hoặc chứng minh. Hướng (d) làm hình phẳng, đầu ra tĩnh,
toạ độ tìm bằng tối ưu số. Hướng (e) chỉ **đo**, không dựng. Hai ngoại lệ đã nêu
(Geoparsing, Draw2Think) chạm được một phần: một cái có ngôn ngữ hình thức phủ
3D nhưng đi chiều ngược; một cái dựng hình 3D nhưng để giải bài chứ không để
trình bày, và không mang thẩm quyền số riêng.

**Hậu quả của khoảng trống.** Khi không có tầng kiểm chứng tất định giữa mô hình
và màn hình, một hệ sinh mô phỏng có thể vẽ ra một hình *trông hợp lý* cho một
đáp số **sai** — và người học không có cách nào phát hiện. Đây là chiều sai đắt
nhất trong giáo dục: sai mà **im lặng**. Kho này đã gặp đúng nó hai lần ở phía
sản phẩm (thể tích khối lõm trả `28` thay vì `20`) và một lần ở phía **bộ đo**
(báo `SILENT_WRONG_ANSWER = 6` trên một hệ không phạm lỗi nào).

**Hướng tiếp cận của AlgoSim.** Chia trách nhiệm ở một ranh giới đặt tên là R0:
mô hình ngôn ngữ chỉ **đọc đề và tổng hợp các bước dựng**; sau bước ấy không còn
lượt gọi mô hình nào. Mọi toạ độ, mọi đại lượng, mọi phán quyết đúng/sai do các
tầng tất định sinh ra, với số học chính xác trên ℚ(√, π). Ràng buộc được cưỡng
chế bằng **lược đồ dữ liệu** — mọi toán hạng hình học là tên của vật đã dựng —
chứ không bằng lời dặn trong prompt.

**Phạm vi và giới hạn.** Phủ chương trình là **một phần**, có chủ đích. Hai họ
nằm ngoài vì lý do kiến trúc đo được (khối tròn xoay tổng quát: không có tích
phân ký hiệu; khối ghép/bù: không có thẩm quyền boolean). Kéo–thả liên tục kiểu
GeoGebra nằm ngoài vì nó phá song ánh khung ⇔ bước. Tác động lên người học
**chưa đánh giá**. Mọi con số thực nghiệm đến từ **một** lượt đo trên **9 ca**,
**n = 1 mỗi họ**, **không held-out**.

### 3.4. Năm khái niệm phải tách rời khi phát biểu

Nhập nhằng năm chữ này là cách nhanh nhất để một phát biểu khoảng trống bị bác:

| khái niệm | ai làm | AlgoSim |
|---|---|---|
| **sinh sơ đồ** | MagicGeo, GeoLoom, SDE-GPG | không phải mục tiêu |
| **giải bài** | GF-Reasoner, AutoGPS, SD-GPS, PAL | không phải mục tiêu; đáp số là **hệ quả** của việc dựng đúng |
| **mô phỏng 3D thực thi được** | — (GeoGebra: người dùng tự dựng) | **mục tiêu chính** |
| **kiểm chứng mô phỏng** | VeriGeo, GeoBuildBench (mức ràng buộc) | mục tiêu chính, sáu tầng + oracle độc lập |
| **trình bày quá trình dựng** | Text2CAD (chuỗi lệnh), AlphaGeometry (chứng minh) | mục tiêu chính, dạng **tua được theo khung** |

---

## 4. Rà soát năm câu hỏi nghiên cứu

Nguồn RQ: `docs/THESIS_ACCEPTANCE_MATRIX_AND_DOCUMENTATION.md` Bảng 2 +
`CLAIMS_MATRIX.json` (`created_before_live_run = true`).
**Không sửa văn bản đăng ký lịch sử** — cột *đề nghị* chỉ áp cho bản thảo hiện hành.

| RQ | nội dung | có được trả lời trực tiếp không | đề nghị | lý do |
|---|---|---|---|---|
| **RQ1** độ phủ | `NEW_PER_PROBLEM_MODULES = 0` · `ABSENCE_PROOF_PASS 2/2` | **Có** — đo end-to-end, 7 ca phủ 10/10 họ trong phạm vi | **giữ nguyên** | metric khách quan, đo được bằng quét AST; không phụ thuộc phán đoán |
| **RQ2** tính đúng | mọi `*_MISMATCH_COUNT = 0` | **Có** — 12/12 đại lượng, oracle độc lập | **chỉnh câu chữ** | ma trận đăng ký ghi *"11 đại lượng"*; bản thảo phải viết **12** kèm đính chính D-1, giữ nguyên văn bản đăng ký |
| **RQ3** tự sinh | `FIRST_ATTEMPT_SERVABLE_RATE` · `RECOVERY_WITHIN_ONE_REPAIR_RATE` | **Một phần** — có số (6/7 · 1/1) nhưng **không ngưỡng**, n = 1 | **chỉnh câu chữ** | phải viết dạng *"trên bộ ca này"* + mẫu số. Cấm mọi câu có chữ *ổn định* hoặc tỉ lệ phần trăm đứng một mình |
| **RQ4** an toàn | `NEGATIVE_FAIL_CLOSED_RATE` · `SILENT_WRONG_ANSWER_COUNT` | **Có** — 2/2 · 0 | **tách** | RQ4 đang gộp hai câu hỏi khác nhau: *có từ chối không* (2/2, đạt) và *có từ chối ĐÚNG CHỖ không* (`TARGET_BOUNDARY_PASS = 1/2`). Đề nghị tách **RQ4a fail-closed** / **RQ4b boundary-accuracy** trong bản thảo, vì gộp lại làm con số 1/2 biến mất khỏi tầm mắt |
| **RQ5** hiệu quả | `TOKENS_PER_CORRECT_SERVABLE` · `CALLS_PER_CORRECT_SERVABLE` | **Một phần** — có số (13 981 token/ca · 2,71 lượt/ca) nhưng **không ngưỡng** | **giữ nguyên** | đúng là mô tả; chỉ cần in kèm mẫu số và **không** so với lượt đo có mẫu số khác |

`RQS_MAPPED = 5/5`.

**Đối chiếu với năm trục gợi ý của wave:** (1) khả năng biểu đạt và độ phủ → RQ1.
(2) tính đúng tất định và số học chính xác → RQ2. (3) khả năng mô hình tự sinh →
RQ3. (4) ngăn mô phỏng sai và từ chối có cấu trúc → RQ4 (nên tách làm hai). (5)
chi phí/hiệu quả → RQ5. Năm RQ hiện có **phủ đủ** năm trục; không cần thêm RQ
mới, chỉ cần tách RQ4.

---

## 5. Những tuyên bố PHẢI giới hạn

Hệ thống **chưa chứng minh** — và bản thảo không được viết như thể đã chứng minh:

| # | tuyên bố bị cấm | trạng thái thật |
|---|---|---|
| 1 | cải thiện kết quả học tập của học sinh | **chưa đánh giá**, ngoài phạm vi có khai báo |
| 2 | cải thiện tư duy không gian | **chưa đánh giá** |
| 3 | dễ sử dụng với mọi nhóm người dùng | **chưa đánh giá**; chưa có nghiên cứu người dùng |
| 4 | ổn định trên phân phối bài toán rộng | `STABILITY_UNDER_ACCEPTANCE = NOT_MEASURED`, khoá **trước** lượt chạy |
| 5 | bao phủ toàn bộ hình học không gian | phủ **một phần**, có chủ đích; `COVERAGE.md` cấm tuyên bố ngược lại |
| 6 | tốt hơn GeoGebra trên mọi tiêu chí | **sai chiều so sánh** — GeoGebra có kéo liên tục mà AlgoSim cố ý không có |
| 7 | có thể triển khai sản phẩm đại trà | `PRODUCT_DEPLOYMENT_READY = NOT_CLAIMED` |
| 8 | mọi chương trình do mô hình sinh đều đúng | 6/7 lần đầu; một ca phải sửa; `n1` từng thử **bịa dữ kiện** |
| 9 | hỗ trợ khối tròn xoay tổng quát hoặc boolean geometry | `OUT_OF_SCOPE` vì **lý do kiến trúc đo được** |

⚠️ **Một ca mỗi họ chỉ tạo bằng chứng phát triển hoặc nghiệm thu hẹp.** Nó
**không** tạo bằng chứng về độ ổn định thống kê. Mọi tỉ lệ trong khoá luận phải
in kèm mẫu số, và `product_capability.py` giữ khối cong · khối lõm · thiết diện
xiên ở `foundation_only` chính vì lý do này.
