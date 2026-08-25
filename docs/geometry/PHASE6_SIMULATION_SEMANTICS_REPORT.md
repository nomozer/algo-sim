# PHASE 6 — NGỮ NGHĨA MÔ PHỎNG: audit

> Câu hỏi: hệ **thật sự mô phỏng quá trình hình thành hình học**, hay chỉ **phát
> lại một chương trình đã sinh**?
>
> Không sửa mã. Mọi khẳng định dưới đây đo trên IR thật của lượt `8b4025e`.

---

## 1. Ba tầng — và chúng KHÔNG phải một

| Tầng | Trạng thái | Bằng chứng |
|---|:-:|---|
| ① **Geometric execution** | ✅ đủ | 5 phép dựng · 3 phép đo · kernel hữu tỉ chính xác |
| ② **Construction reasoning** | ⚠️ **một nửa** | có *thứ tự* + *phụ thuộc*; **không có *vì sao*** |
| ③ **Visual playback** | ✅ đủ | từng bước · camera · lời kể |

Nửa còn thiếu của ② là toàn bộ nội dung báo cáo này.

**Cấu trúc** (`M` dựng từ `A`, `B`; `V` đo từ `chop`) — hệ **có**, và có ở dạng
máy đọc được.

**Mục đích** (*vì sao dựng mặt đáy trước*, *vì sao cần điểm này*) — hệ **không
có**, ở bất kỳ tầng nào.

---

## 2. IR lưu gì cho từng primitive

```
ConstructPointStmt     target_var · expr · label
ConstructLineStmt      target_var · through_a · through_b · label
ConstructPlaneStmt     target_var · through · label
ConstructSolidStmt     target_var · vertices · faces · label
ConstructSectionStmt   target_var · solid · plane · label
MeasureExpr            quantity · of · wrt
```

Đối chiếu bốn câu hỏi của TASK 2:

| Câu hỏi | Trả lời | Nhờ đâu |
|---|:-:|---|
| Object được tạo **khi nào**? | ✅ | thứ tự `statements` → `step_index` |
| Object phụ thuộc **vào gì**? | ✅ | `_phu_thuoc` → `depends` |
| **Tại sao** object được tạo? | ❌ | — |
| Có **mục đích hình học** không? | ❌ | — |

Quét toàn bộ trường mang nghĩa *why / reason / intent / purpose*:

```
ConstructPointStmt   — KHÔNG CÓ
ConstructSolidStmt   — KHÔNG CÓ
SemanticTraceStep    — KHÔNG CÓ
SemanticProgramSpec  — pedagogical_intent   ← MỘT chuỗi cho CẢ chương trình
```

Nên câu trả lời gọn: **IR lưu `input → output` cộng `khi nào` và `từ gì`.
Không lưu `vì sao`.**

`tier1_narration` không lấp được chỗ đó: engine sinh nó **từ trạng thái thật**,
nên nó kể *"Dựng điểm M = (1/2, 0, 0)"* — tường thuật cái **đã xảy ra**, không
phải lý do nó phải xảy ra.

---

## 3. `construct_solid` có che mất quá trình dựng không?

**Có.** Đo được ở Phase 5G: chuỗi phụ thuộc sâu nhất trên cả 6 IR thật là **2
tầng** (`điểm tự do → đối tượng → đại lượng`). Không bài nào có chuỗi
`đáy → chiều cao → đỉnh → cạnh → khối`.

```
geo_09   S.ABCD ← [A,B,C,D,S]      MỘT bước, năm đỉnh
         V      ← [S.ABCD]
```

Đề nói *"hình chóp S.ABCD có **đáy ABCD** là hình vuông"* — **đáy là một đối
tượng có tên trong đề**, mà IR không có cách gọi tên nó.

### Đề xuất — và tôi khuyên KHÔNG làm

```
construct_base(ABCD) → construct_apex(S) → construct_edges → construct_solid
```

| Tiêu chí | Đánh giá |
|---|---|
| Có cần thiết không? | Không cho **tính đúng** — kết quả y hệt |
| Có làm giống GeoGebra hơn không? | **CÓ, rất giống** — xem §4 |
| Có tăng giá trị nghiên cứu không? | **Không** |

Lý do từ chối, và nó là điểm mấu chốt của cả báo cáo:

> Chia nhỏ `construct_solid` cho ra **cái GÌ mịn hơn**, không cho ra **vì sao**.
> Đó đúng là mức chi tiết mà *Construction Protocol* của GeoGebra đã có từ 20
> năm trước. Ta sẽ tốn một wave để đuổi kịp một tính năng có sẵn, mà vẫn không
> trả lời được câu hỏi ②.

Ghi vào `POST_THESIS_BACKLOG`, không mở wave.

---

## 4. So với GeoGebra — bản chất, không phải giao diện

### Sự thật khó chịu, và phải nói ra

GeoGebra **đã có** *Construction Protocol* + *Navigation Bar*: bảng liệt kê mọi
bước dựng, đi tới/lui từng bước, **có tính tới phụ thuộc**, chạy được thành hoạt
cảnh, hiện *"2 / 7"* — và có cả *Breakpoint* để gộp nhóm bước.

Đó **chính là** thứ Phase 5D–5E dựng ra.

Nên câu hỏi của TASK 4 — *"khác biệt nằm ở AI sinh chương trình hay ở
simulation?"* — có câu trả lời thẳng:

> **Gần như toàn bộ khác biệt nằm ở "AI đọc đề → sinh chương trình → được kiểm
> chứng độc lập". Tầng simulation của ta, xét về năng lực, KHÔNG vượt GeoGebra.**

Ba thứ tầng simulation của ta hơn, và cả ba đều nhỏ:

| | Ta | GeoGebra |
|---|---|---|
| Số học | `Fraction` **chính xác**, so **bằng đúng** | dấu phẩy động + epsilon |
| Nguồn hình | **chỉ** từ chương trình đã thẩm định | người dùng vẽ tay |
| Biết đề hỏi gì | **có** (`RequestContract`) | **không** |

Hai dòng đầu là *ràng buộc*, không phải *năng lực* — chúng làm hệ **hẹp hơn**
GeoGebra, và hẹp hơn một cách có chủ đích.

**Dòng thứ ba mới là trục còn dư địa**, và §5 đo nó.

---

## 5. Thứ GeoGebra KHÔNG làm được, và ta ĐANG CÓ SẴN dữ liệu

Hệ biết **đề hỏi gì** (`obligations`) *và* **mỗi đối tượng dựng từ gì**
(`_phu_thuoc`). Ghép hai thứ ấy cho ra một câu hỏi GeoGebra không đặt được:

> **Bước nào thật sự phục vụ câu hỏi của đề, và bước nào là đường cụt?**

Đo trên IR thật, dùng bao đóng phụ thuộc của `container ∪ witness`:

```
geo_06  parallel        phục vụ = [AB, DC]                    thừa = —
geo_07  distance        phục vụ = [ABCD, khoang_cach]         thừa = —
geo_08  angle           phục vụ = [AB, AC, goc_ab_ac]         thừa = —
geo_09  volume          phục vụ = [S.ABCD, V_S_ABCD]          thừa = —
geo_02  point_on_plane  phục vụ = [SAB]        thừa = [ABCD, giao_tuyen]
geo_05  perpendicular   phục vụ = []           thừa = [ABCD_plane, SA_line]
```

**Dẫn xuất được, từ dữ liệu đã có, không cần đổi hợp đồng.**

⚠️ Và nó lộ ra hai bệnh **khác nhau** mà hiện đang bị gộp:

- `geo_02` — mô hình dựng `giao_tuyen` rồi **không dùng tới**: chương trình có
  bước thừa thật.
- `geo_05` — *"phục vụ = []"* **không** phải vì mọi bước đều thừa, mà vì hợp
  đồng gọi `(ABCD)`/`SA` còn chương trình khai `ABCD_plane`/`SA_line`. Đây là
  **lệch danh xưng** (đã biết từ Wave 4), không phải đường cụt.

Phân biệt được hai thứ ấy là một chỉ số mới, và nó **thuộc về sư phạm**: một mô
phỏng chỉ ra *"ba bước này là cần, bước kia em dựng thừa"* dạy được điều mà một
bảng liệt kê bước không dạy được.

---

## 6. Trả lời câu hỏi trung tâm

> **Hệ có thật sự mô phỏng quá trình hình thành hình học không?**

**Có, ở mức CẤU TRÚC. Chưa, ở mức LÝ DO.**

Nó phát lại đúng **thứ tự** dựng, đúng **quan hệ phụ thuộc**, mỗi bước có lời kể
sinh từ trạng thái thật, và mọi đối tượng truy ngược được về câu lệnh sinh ra
nó. Đó **nhiều hơn** "phát lại một chương trình": một bản phát lại thuần tuý
không biết `M` dựng từ `A` và `B`.

Nhưng nó **chưa** trả lời được *"vì sao bước này"*. Và ở mức cấu trúc thì
GeoGebra đã làm được từ lâu — nên **nếu chỉ tính tầng simulation, đây chưa phải
đóng góp**.

Đóng góp thật nằm ở chỗ khác, và nó đúng là chỗ đề tài tuyên bố:

```
đề bằng lời → chương trình dựng hình → ĐƯỢC KIỂM CHỨNG ĐỘC LẬP → mô phỏng
```

GeoGebra bắt đầu từ **người đã biết cách dựng**. Hệ này bắt đầu từ **một đoạn
văn**, và có oracle độc lập nói câu trả lời đúng hay sai.

---

## 7. Ba lựa chọn — chọn theo giá trị luận văn

### ❌ C — làm renderer/tương tác sâu hơn

Đuổi theo thứ GeoGebra đã có 20 năm. Mỗi giờ bỏ vào đây làm luận văn **giống một
bản sao hơn**. Và `B` (servable) vẫn chưa mở, nên công sức không đổi được một
chỉ số nào.

### ❌ B1 — chia nhỏ `construct_solid`

Cho **cái gì mịn hơn**, không cho **vì sao**. Chính là mức chi tiết của
Construction Protocol. §3.

### ✅ **A — giữ hợp đồng, dồn vào benchmark AI** *(chính)*

Đây là trục **duy nhất** đang thiếu bằng chứng, và là trục luận văn đứng lên:

```
A = 4/10, và 10 bài ấy ĐÃ BỊ NHÌN qua bốn wave
held-out hình học:  CHƯA CÓ
bảng phủ:           9/20 chủ đề diễn đạt được
```

Việc cụ thể, xếp theo giá trị / công:

1. **Chạy lại Phase 5 sau 5A** — bản vá `faces` nhắm đúng 3/4 ca trượt schema
   của lượt W4, mà **chưa ai đo**. Rẻ nhất, ~0.36 USD.
2. **Soạn pool held-out** từ đề thi công khai + xin seed GVHD.
3. **Nối `distance` cho đường–đường / đường–mặt / mặt–mặt** — kernel đã tính
   được, thiếu vài nhánh `isinstance`; phủ thêm một dạng bài tần suất cao.

### ✅ **B2 — "bước nào phục vụ đáp án" ** *(phụ, rẻ, và là thứ GeoGebra không có)*

**Không** đổi hợp đồng, **không** thêm primitive: chỉ phơi ra bao đóng phụ thuộc
của `container ∪ witness` đã tính sẵn (§5). Một wave nhỏ, và nó cho luận văn một
câu mà bản sao GeoGebra không nói được.

⚠️ Điều kiện: phải **tách được** *bước thừa thật* khỏi *lệch danh xưng* (§5),
nếu không chỉ số này sẽ vu oan cho mô hình ở đúng những ca mà lỗi thuộc hợp đồng.

---

## 8. Những thay đổi NÊN TRÁNH vì biến hệ thành GeoGebra

| Tránh | Vì sao |
|---|---|
| Chia nhỏ phép dựng thành `base`/`apex`/`edges` | mức chi tiết Construction Protocol; mịn hơn ≠ có lý do |
| Kéo thả điểm tự do | thao tác trung tâm của GeoGebra; hệ này hình **chỉ** đến từ chương trình đã thẩm định |
| Toolbar dựng hình · ô nhập lệnh | biến người học thành người vẽ; đề tài mất mệnh đề *"AI sinh"* |
| Mặt cầu · nón · trụ · quỹ tích | đổi nền toán từ đa diện hữu tỉ sang mặt cong ⇒ viết lại kernel |
| Camera preset · hiệu ứng · hoạt cảnh đẹp | `COVERAGE.md` cấm chấm bằng vẻ đẹp |
| Constraint editor | trở thành phần mềm hình học động, đúng nghĩa |

Ranh giới chung, và nó kiểm được bằng một câu:

> **Người học điều khiển THỜI GIAN và GÓC NHÌN. Không điều khiển NỘI DUNG TOÁN
> HỌC.** Mọi tính năng phá câu đó là một bước về phía GeoGebra.

---

## Nguồn

- [Construction Protocol — GeoGebra Manual](https://geogebra.github.io/docs/manual/en/Construction_Protocol/)
- [Navigation Bar — GeoGebra Manual](https://geogebra.github.io/docs/manual/en/Navigation_Bar/)
- [ConstructionStep Command — GeoGebra Manual](https://wiki.geogebra.org/en/ConstructionStep_Command)
