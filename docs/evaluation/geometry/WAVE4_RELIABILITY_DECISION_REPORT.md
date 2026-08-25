# WAVE 4 — RELIABILITY DECISION REPORT

> Câu hỏi nghiên cứu: **"Sau Wave 4, hệ có sinh Geometry Program đáng tin cậy
> hơn không, và nếu chưa thì giới hạn nằm ở đâu?"**

---

## 1. Trạng thái hệ thống

| | |
|---|---|
| HEAD | `8b4025e` · cây **sạch** |
| Commit đo W4 | `8b4025e` · `measured_system_hash` `811133a2e758aa02` · 141 file |
| freeze verify | **PASS** |
| `CACHE_VERSION` | **41** |
| dataset fingerprint | `221caa959844b113` — **không đổi** qua cả ba lượt |
| pytest | **2543 passed** |

---

## 2. So sánh ba mốc

| Metric | 5.0 | 5.5 | **W4** |
|---|:---:|:---:|:---:|
| **G1** cú pháp | 9/10 | 9/10 | **6/10** ▼ |
| **G2** ngữ nghĩa | 9/10 | 9/10 | **6/10** ▼ |
| **A** chạy trọn | 1/10 | 1/10 | **4/10** ▲ |
| **O** oracle | 1/1 PASS | 1/1 PASS | **4/4 PASS** ▲ |
| `obligation_match` | 10/10 | 9/10 | **9/10** = |

`commit đo` `027c9e1` → `5f42363` → `8b4025e` · `CACHE_VERSION` 40 → 40 → 41.

### Phân bố lỗi — chỗ đọc ra nhiều hơn điểm tổng

```
5.0   grounding 6 · coverage 2 · schema 1 · PASS 1
5.5   grounding 7 · coverage 1 · schema 1 · PASS 1
W4    grounding 1 · coverage 1 · schema 4 · PASS 4
```

**Grounding 7 → 1.** Đó là kết quả trực tiếp của TASK 2, và là thay đổi lớn nhất
của wave.

### Bốn ca đi trọn đường — và chúng phủ BỐN nghĩa vụ khác nhau

```
geo_06  parallel   PASS      geo_08  angle    PASS   (cos²)
geo_07  distance   PASS      geo_09  volume   PASS
```

Ba trong bốn là **nghĩa vụ ĐẠI LƯỢNG**, tức đường `measure` mở từ Wave 2 lần
đầu chạy tới đích và được oracle độc lập xác nhận. Trước W4, `O` chỉ có một mẫu
duy nhất và nó thuộc nhóm quan hệ.

---

## 3. Kiểm ba giả thuyết Wave 4

### H1 — Schema theo miền giảm false rejection: **ĐÚNG, kèm biến thể mới**

`analyze` nay đặt tên theo quy ước hình học:

```
          5.5                       W4
geo_01    abcd / m          →       ABCD / M
geo_06    ab   / dc         →       AB   / DC
geo_09    s_abcd / the_tich →       S.ABCD / V_S_ABCD
```

28 tên chứa chữ hoa. Không còn ca nào trượt vì `m` ↔ `M`.

⚠️ **Nhưng nó đẻ một biến thể**: 2 tên chứa **ngoặc** — `(ABCD)`, ký hiệu mặt
phẳng chuẩn của toán học. `geo_05` chết vì `container '(ABCD)'` trong khi chương
trình khai `ABCD_plane`. Lưới ký hiệu không bắt được: `(ABCD)` không phải alnum.

Chỉ dẫn *"giữ nguyên ký hiệu"* đúng về hướng, **chưa đủ hẹp** — nó cho phép cả
ký tự cú pháp toán.

**False acceptance: không có.** Không ca nào đi qua nhờ hoà giải tên rồi sai.

### H2 — Grounding giả thiết toạ độ: **ĐÚNG, và R0 vẫn giữ**

Grounding failure **7 → 1**. Ca duy nhất còn lại (`geo_02`) bị chặn **đúng**:

```
A: giá trị [0, 0, 0] không có trong mục 'hinh_chop_sabcd'
```

`A` là **witness** của nghĩa vụ, nên khoá R0 loại nó khỏi lối toạ độ — mô hình
đang khai thẳng đáp án. Đây chính là khoá tường minh Wave 4 đặt vào thay chỗ
`model_assumption`, và nó hoạt động trên dữ liệu thật.

Kiểm lại offline ba ca bắt buộc, cả ba đạt:

```
H = literal(answer) + model_assumption=true   → FAIL  MODEL_ASSUMPTION_IS_ANSWER
M = [1/2,1/2,0] không có phép dựng            → FAIL  "không có producer hợp lệ"
M = midpoint(A,B)                             → PASS
```

### H3 — Provenance của phép dựng: **ĐÚNG**

Hệ phân biệt được **"giá trị đúng"** với **"quá trình sinh đúng"**. Bằng chứng
mạnh nhất không phải test mà là một test CŨ đã đỏ trong lúc làm: bản nới C₁a đầu
tiên bỏ hẳn phép kiểm dẫn xuất, và `test_3_gan_dap_an_bang_assign_thi_TRUOT` bắt
được ngay. `H = literal([0,0,0])` **nằm đúng trên mặt phẳng**, nên C₂ và oracle
đều PASS — chỉ C₁a chặn được nó.

---

## 4. Failure taxonomy — 6 ca thất bại

| case | tầng | mã lỗi | nguyên nhân | Loại | W4 xử lý? |
|---|:-:|---|---|---|---|
| geo_01 | 2 | `schema` | `faces` nhận **tên điểm** thay chỉ số | **CONTRACT** | ✗ mới lộ |
| geo_04 | 2 | `schema` | như trên | **CONTRACT** | ✗ mới lộ |
| geo_10 | 2 | `schema` | như trên | **CONTRACT** | ✗ mới lộ |
| geo_03 | 2 | `schema` | trộn nghĩa vụ vào `memory_declarations`; `construct_plane.through` chỉ 1 điểm | **MODEL** | ✗ |
| geo_05 | 6 | `coverage` | `(ABCD)` ↔ `ABCD_plane` | **CONTRACT** | ⚠️ H1 đẻ ra |
| geo_02 | 6 | `grounding` | khai witness `A` bằng toạ độ cứng + khai sai nghĩa vụ | **MODEL** | ✓ chặn đúng |

```
CONTRACT_FAILURE     4      VALIDATOR_FAILURE    0
MODEL_FAILURE        2      INTERPRETER_FAILURE  0
                            ORACLE_FAILURE       0
```

### Lỗi `faces` — một LỚP LỖI, không còn là giai thoại

Ba ca cùng một lỗi:

```
statements.N.construct_solid.faces.0.0
  Input should be a valid integer … input_value='S'
```

`faces: list[list[int]]` dùng **chỉ số vị trí** vào `vertices`. Mô hình viết
`["S","A","B"]`. Đó là mã hoá thân thiện với máy, **thù địch với người** — và
với một model đang được bảo *"giữ nguyên ký hiệu điểm"*, nó là lỗi gần như tất
yếu.

Ở Wave 3 tôi từ chối vá lỗi bọc-thừa-`literal` của `geo_10` với lý do *"một lần
là giai thoại, hai lần là lớp lỗi"*. **Nay là ba lần, cùng một trường.** Ngưỡng
đã vượt, và đây là việc rõ ràng nhất cho wave sau.

---

## 5. Wave 4 sửa được gì

| | |
|---|---|
| grounding failure | **7 → 1**, ca còn lại bị chặn đúng theo R0 |
| `A` chạy trọn | **1 → 4** |
| `O` mẫu PASS | **1 → 4**, phủ 4 nghĩa vụ khác nhau |
| đường `measure` | lần đầu chạy tới đích, 3 đại lượng được oracle xác nhận |
| quy ước tên | `m ↔ M` biến mất hoàn toàn |

## 6. Còn hạn chế gì

**① `G1` tụt 9 → 6.** Không phải model kém đi — ba ca cùng chết ở một trường
hợp đồng (`faces`). Hai lượt trước chỉ 2 bài chạm `construct_solid`; W4 mô hình
viết chương trình **đầy đủ hơn** nên chạm nhiều hơn, và lỗi thiết kế lộ ra.

**② H1 đẻ biến thể `(ABCD)`.** Sửa nguồn đúng hướng nhưng chưa đủ hẹp.

**③ `symbol_reconciled` KHÔNG vào artifact.** Tôi thêm trường quan trắc vào
`CoverageResult` để trả lời *"bản vá nguồn đã đủ chưa?"* nhưng **quên nối qua
`SemanticRouteOutcome` xuống runner**. Nên câu hỏi ấy lượt này **không trả lời
được bằng dữ liệu**. Lỗi của tôi, ghi lại để wave sau nối.

**④ `B` (servable) vẫn chưa đo được.** Không có nguyên thuỷ thị giác 3D.

**⑤ `O = 4/4` KHÔNG phải tỉ lệ.** `n = 4 < 20`, `RELIABILITY_EVALUATION_PLAN
§3.3` cấm chia. Nó là **bốn mẫu, cả bốn đúng** — không phải "100% chính xác".

---

## 7. Chi phí

| | 5.0 | 5.5 | W4 |
|---|---:|---:|---:|
| lượt logic | 28 | 30 | **33**/60 |
| HTTP · retry · 429 | 30·2·0 | 30·0·0 | **33·0·0** |
| tổng token | 143 098 | 196 851 | **214 977** |
| USD (chặn trên) | 0.2171 | 0.3379 | **0.3598** |
| độ trễ tổng | (không đo) | 572.2s | **606.0s** |

`thoughts_tokens` **106 152** = 49% tổng.

---

## 8. Claim

### Được phép nói

> **Wave 4 cải thiện khả năng sinh Geometry Program** bằng cách gỡ hai lỗi hợp
> đồng miền — quy ước đặt tên và phép so giá trị trên toạ độ — và nhờ đó số
> chương trình **thực thi được** tăng 1 → 4, kèm **4 mẫu được oracle độc lập xác
> nhận đúng**, phủ bốn nghĩa vụ khác nhau.

Và: **R0 không yếu đi.** Ca duy nhất còn chết ở grounding là ca mô hình khai
thẳng đáp án, bị chặn đúng.

### KHÔNG được nói

*"AI đã hiểu hình học"* · *"AI sinh mô phỏng 3D"* · *"AI tạo hình học tương
tác"* · *"độ chính xác 100%"*.

Renderer chưa có. Tương tác chưa có. `B` chưa đo. `O` có 4 mẫu, không phải một
tỉ lệ.

---

## 9. Decision gate cho Renderer 3D: **CHƯA MỞ**

| # | Điều kiện | Kết quả |
|---|---|:-:|
| 1 | `A` tăng | ✅ 1 → 4 |
| 2 | `O` có thêm mẫu PASS | ✅ 1 → 4, tất cả PASS |
| 3 | contract failure giảm | ❌ **6 → 4 nhưng đổi CHỖ**, không giảm về bản chất |
| 4 | validator không yếu đi | ✅ 0 validator failure · R0 chặn đúng · test cũ bắt được bản nới sai |
| 5 | `B` mở được *(tôi thêm)* | ❌ **không** |

**Điều kiện 3 — vì sao tôi chấm ❌ dù con số giảm.** Grounding 7 → 1 là thật.
Nhưng cùng lúc xuất hiện **một lớp lỗi hợp đồng mới** (`faces`, 3 ca) và **một
biến thể** (`(ABCD)`, 1 ca). Tổng lỗi hợp đồng 6 → 4 là **dời chỗ**, không phải
đã sửa xong. Ba ca `faces` là lỗi thiết kế trường, không phải nhiễu.

**Điều kiện 5 là ràng buộc KIẾN TRÚC, không phải chất lượng.** Renderer đọc
`envelope`, mà `envelope` chỉ sinh khi `servable = True` — và `servable` luôn
`False` vì tập nguyên thuỷ thị giác đã đóng băng **không có nguyên thuỷ 3D nào**.
Kể cả `A` đạt 10/10, renderer **vẫn không có gì để vẽ**. Bốn điều kiện của đặc
tả đều đo *đầu ra của phép sinh*; không cái nào đo *đầu vào của renderer*.

### Wave 5 nên làm gì thay vì renderer

Xếp theo bằng chứng, không theo cảm giác:

1. **`construct_solid.faces` nhận TÊN đỉnh** — 3 ca, cùng một trường, ngưỡng
   "hai lần là lớp lỗi" đã vượt. Rẻ nhất, tác động lớn nhất.
2. **Siết quy ước tên** — cấm ký tự cú pháp (`(`, `)`, `.`) trong định danh, và
   mở rộng lưới ký hiệu để bắt `(ABCD)` ↔ `ABCD_plane`. 1 ca.
3. **Nối `symbol_reconciled` xuống artifact** — nợ quan trắc của chính wave này.
4. **Nguyên thuỷ thị giác 3D** — điều kiện CẦN để `B` đo được, và là thứ phải có
   *trước* renderer chứ không phải cùng lúc.

---

## 10. Trả lời câu hỏi nghiên cứu

> **"Wave 4 có giúp AI sinh Geometry Program đáng tin cậy hơn không?"**

**Có, ở một nghĩa cụ thể và đo được: số chương trình đi trọn chuỗi
sinh → thẩm định → thực thi → oracle tăng từ 1 lên 4, và cả bốn đều đúng.**
Lần đầu tiên hệ có nhiều hơn một mẫu về tính đúng toán học, và lần đầu đường
`measure` được xác nhận.

**Giới hạn nằm ở HỢP ĐỒNG, không ở mô hình.** Trong 6 ca thất bại còn lại, **4
thuộc hợp đồng của ta** và chỉ 2 thuộc model. Wave 4 gỡ hai lỗi hợp đồng thì lộ
ra một lỗi hợp đồng khác nằm sau chúng — `faces` mã hoá bằng chỉ số. Đó là dấu
hiệu của một nền còn đang được dọn, không phải của một mô hình đã tới hạn.

**Chưa đủ điều kiện làm Renderer 3D**, và lý do quyết định không phải chất lượng
sinh mà là kiến trúc: `B` chưa mở được thì renderer không có đầu vào.

**DỪNG.** Không triển khai Wave 5 khi chưa có quyết định.
