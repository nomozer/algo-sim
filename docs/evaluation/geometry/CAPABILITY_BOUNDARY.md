# RANH GIỚI NĂNG LỰC BIỂU DIỄN — đóng băng trước Phase 7B

> Trả lời **một** câu: *Phase 7B đang đo cái gì?*
>
> Chốt **2026-08-27 (Phase 7A.5)**. Không sửa một dòng năng lực nào — mọi mục
> dưới đây **dẫn từ mã đang có**, kèm chỗ tra. Đây là bản mô tả, không phải bản
> thiết kế.
>
> ⚠️ **Luật đọc quan trọng nhất:** một bài rơi vào phần `UNSUPPORTED` mà hệ
> không làm được thì đó là **giới hạn biểu diễn đã biết trước**, **KHÔNG** phải
> lỗi của mô hình. Ghi nó vào nhóm `model generation` của taxonomy là báo một
> con số thấp hơn thực tế *và* kết tội mô hình ở chỗ nó không có lỗi.

---

## 0. Vì sao ranh giới này nằm ở `Fraction`

Kernel dựng trên số hữu tỉ **có chủ đích**, không phải vì tiện
(`geometry/exact.py`):

```
vuông góc  ⇔  u · v == 0      (chính xác, không epsilon)
song song  ⇔  u × v == 0
đồng phẳng ⇔  det   == 0
```

Đó là thứ nâng claim của luận văn từ *"kernel tất định"* lên **"kernel chính
xác"**: tất định nghĩa là chạy lại ra cùng kết quả — **kể cả cùng một kết quả
sai**; chính xác nghĩa là không có sai số nào để tích luỹ.

Cái giá là ranh giới ở §2. Cái giá ấy **được chọn**, và Phase 7B đo hệ **bên
trong** nó.

---

## 1. SUPPORTED — được phép xuất hiện trong held-out

### 1.1 Phép dựng (câu lệnh IR)

| Năng lực | Hỗ trợ ở đâu | Oracle kiểm bằng cách nào |
|---|---|---|
| `construct_point` | `contract.py:624` → `geometry_exec.exec_construct_point` | so toạ độ hữu tỉ, hoặc so **bất biến tỉ lệ** (*"Q là trung điểm AD"*) |
| `construct_line` | `contract.py:634` | `point_on_line` cho hai điểm xác định nó |
| `construct_plane` | `contract.py:657` | `point_on_plane` cho các điểm sinh nó |
| `construct_polygon` | `contract.py:772` | `coplanar` trên tập đỉnh |
| `construct_solid` | `contract.py:798` | `volume`, hoặc `coplanar` từng mặt |
| `construct_section` | `contract.py:816` → `section.cross_section` | số cạnh thiết diện · `coplanar` các đỉnh |

### 1.2 Biểu thức dựng

| Năng lực | Kernel | Oracle |
|---|---|---|
| `midpoint` | `kernel.midpoint:35` | bất biến tỉ lệ `2Q = A + D` |
| `divide_segment` | `kernel.divide_segment:39` | như trên, với `t` hữu tỉ |
| `intersect_line_plane` | `kernel:49` | `point_on_line` **và** `point_on_plane` cho giao điểm |
| `intersect_plane_plane` | `kernel:74` | `line_in_plane` với **cả hai** mặt |
| `intersect_line_line` | `kernel:98` | `point_on_line` với **cả hai** đường |
| `project_onto` (điểm→mặt, điểm→đường) | `kernel:121`, `:128` | `point_on_plane`/`point_on_line` + `perpendicular` |

Kernel còn có `plane_through_point_perpendicular_to`,
`plane_through_point_parallel_to`, `line_through_point_parallel_to`,
`perpendicular_foot_line` (`kernel:134–148`).

### 1.3 Quan hệ (vị từ → nghĩa vụ kiểm)

Tất cả là phép so **chính xác** trên ℚ, `predicates.py`:

| Nghĩa vụ | Vị từ | Biến thể |
|---|---|---|
| `point_on_line` | `point_on_line:47` | — |
| `point_on_plane` | `point_on_plane:51` | + `line_in_plane:55` |
| `parallel` | `parallel_lines:70` · `parallel_line_plane:75` · `parallel_planes:80` | **ba** biến thể |
| `perpendicular` | `perpendicular_lines:101` · `line_perpendicular_plane:110` · `perpendicular_planes:120` | **ba** biến thể |
| `coplanar` | `coplanar:42` | + `collinear:35`, `skew_lines:84` |

Oracle: **true/false**, không có đơn vị để nhầm.

### 1.4 Đại lượng đo được — và đơn vị của từng cái

Đây là chỗ dễ sai nhất, nên dẫn thẳng từ `geometry_exec._do:166`:

| Đại lượng | Trả về | Luôn hữu tỉ? | Oracle khai bằng |
|---|---|:-:|---|
| **`volume`** | `Fraction` — `measure.volume_tetrahedron:125` · `volume_pyramid_fan:135` | ✅ **luôn** | phân số |
| **`angle` (đường–đường)** | `cos²` — `cos_sq_between_lines:100` | ✅ **luôn** | `cos²` |
| **`angle` (mặt–mặt)** | `cos²` — `cos_sq_between_planes:113` | ✅ **luôn** | `cos²` |
| **`angle` (đường–mặt)** | ⚠️ **`sin²`** — `sin_sq_line_plane:104` | ✅ **luôn** | **`sin²`** |
| **`distance`** (điểm–mặt · điểm–đường · điểm–điểm) | khoảng cách **thật** | ❌ **chỉ khi hữu tỉ** | phân số, **chỉ khi hữu tỉ** |

> **Vì sao `volume` và `angle` không bao giờ vướng vô tỉ:** thể tích là
> `|det|/6` trên toạ độ hữu tỉ; `cos²`/`sin²` là thương của hai tích vô hướng.
> Cả hai **ở lại trong ℚ**. Vô tỉ chỉ sinh ra khi **lấy căn**, và chỉ `distance`
> lấy căn.
>
> ⚠️ **BẪY IM LẶNG:** cặp đường–mặt trả **`sin²`** nhưng đi qua cùng một tên
> trường `angle_cos_sq`. Ô **A10** khai nhầm `cos²` thì chấm sai mà **không cổng
> nào báo** — không phải lỗi hệ, là lỗi soạn oracle.

### 1.5 Miền hình

**Chỉ khối đa diện LỒI.** `section.cross_section:135` đòi đa diện ≥4 đỉnh và
mặt phẳng; `volume_pyramid_fan` **kiểm** đáy phẳng chứ không giả định (`:148`) —
đáy không phẳng thì phép chia quạt cho một con số trông hợp lý nhưng vô nghĩa.

---

## 2. UNSUPPORTED — KHÔNG thuộc Phase 7B

Mỗi mục: **vì sao loại · lỗi gì nếu đưa vào · và nó KHÔNG phải lỗi AI**.

### 2.1 `distance` ra số VÔ TỈ

| | |
|---|---|
| **Vì sao** | `geometry_exec._do:220` gọi `_can_huu_ti(d²)`; không hữu tỉ ⇒ **ném** |
| **Lỗi** | `GEOMETRY_IRRATIONAL_RESULT` — *"khoảng cách là căn của {d²}, một số vô tỉ"* |
| **Không phải lỗi AI** | Mô hình có thể đã dựng hình **đúng hoàn toàn**. Lỗi nằm ở chỗ **không biểu diễn chính xác được kết quả**, và hệ chọn **báo** thay vì làm tròn — đó là hành vi đúng |
| **Kiểm chứng** | `d(P,(MED))` lập phương cạnh 6: `d² = 54`, `_can_huu_ti(54) → None`. Khoá bởi `test_distance_VO_TI_thi_engine_NEM_chu_khong_tra_binh_phuong` |

⚠️ Đây là lớp loại **nhiều bài nhất**: đáp án đề thi thật hầu như luôn có căn
(`a√3/3`, `a√2/2`, `a√6/3`).

### 2.2 TỈ SỐ hai dữ kiện độ dài là vô tỉ

| | |
|---|---|
| **Ví dụ** | *"đáy hình vuông cạnh `a`, `SA = a√3`"* |
| **Vì sao** | Toạ độ phải hữu tỉ. Chọn `a=1` ⇒ `SA=√3` vô tỉ; chọn `a=√3` ⇒ đáy vô tỉ. **Không hệ trục nào** làm cả hai hữu tỉ |
| **Lỗi** | Không có lỗi sạch: mô hình hoặc **làm tròn** (rồi mọi vị từ chính xác phán sai), hoặc bí ở bước khai toạ độ |
| **Không phải lỗi AI** | Đề nằm ngoài miền số của kernel. Mô hình không có nước đi đúng nào |

⚠️ Lớp này **cực phổ biến** trong đề thi Việt Nam.

### 2.3 Khoảng cách ĐƯỜNG–ĐƯỜNG (chéo nhau) và ĐƯỜNG–MẶT ∥, MẶT–MẶT ∥

| | |
|---|---|
| **Vì sao** | `measure.py` **có** `distance_sq_skew_lines:63` và `distance_sq_parallel_lines:53`, nhưng `geometry_exec._do` **không có nhánh** `(Line3, Line3)` — chỉ có điểm–mặt, điểm–đường, điểm–điểm |
| **Lỗi** | `GEOMETRY_OPERAND_TYPE` — *"cặp đối tượng không hợp lệ cho khoảng cách"* |
| **Không phải lỗi AI** | Kernel tính được; **cầu nối IR chưa nối**. Đây là giới hạn của lớp hợp đồng, không phải của mô hình lẫn của toán |

> Ghi rõ vì nó dễ bị đọc nhầm nhất: *"kernel làm được"* **≠** *"hệ phục vụ
> được"*. Ô **B01** và **B02** dựng ra để đo đúng chỗ này — bằng thang **từ chối
> trung thực**, không bằng đáp án.

### 2.4 Góc NHỊ DIỆN có miền (có thể tù)

| | |
|---|---|
| **Vì sao** | `cos_sq_between_planes` trả **bình phương** ⇒ mất dấu ⇒ góc luôn thuộc `[0°, 90°]` |
| **Lỗi** | **Không có lỗi** — và đó chính là vấn đề: hệ trả một con số **hợp lệ cho một câu hỏi khác** |
| **Không phải lỗi AI** | Quy ước `cos²` là của kernel |

⚠️ **Ô B03 là ô quan trọng nhất cả tập.** "Từ chối trung thực" ở đây nghĩa là
**không được lặng lẽ trả lời câu nhị diện bằng góc mặt–mặt**. Một mô phỏng sai
hình còn tệ hơn không có mô phỏng: học sinh sẽ tin nó.

### 2.5 Đầu ra CĂN THỨC / ký hiệu

| | |
|---|---|
| **Vì sao** | Không có tầng đại số ký hiệu. `exact.py` khai rõ: `Fraction` đủ vì mọi phép **dựng** ở lại trong ℚ; vô tỉ chỉ ở *độ dài* và *góc*, và `measure` xử lý bằng cách giữ **bình phương** |
| **Lỗi** | không biểu diễn được ⇒ `GEOMETRY_IRRATIONAL_RESULT` |
| **Không phải lỗi AI** | — |

> `measure.length()` và `measure.degrees()` **trả `float`** (`:78`, `:117`).
> Chúng dành cho **trình bày**, và **CẤM dùng làm oracle**: dùng chúng là đưa
> sai số dấu phẩy động quay lại qua cửa sau, sau khi cả kernel đã dựng bằng
> `Fraction` để tránh nó.

### 2.6 Mặt CONG — cầu · nón · trụ

| | |
|---|---|
| **Vì sao** | Kernel dựng trên đa diện. `GEOMETRY_CURRICULUM_COVERAGE` #19, #20 đều ghi **KHÔNG** |
| **Lỗi** | `execution_authority_gate` từ chối sớm (`geometric_circle`, `geometric_locus` **không** nằm trong `GEOMETRY_OWNED_GAP_ROLES`) |
| **Không phải lỗi AI** | Từ chối sớm ở đây là **hành vi đúng**: miễn trừ cả miền thì một đề mặt cầu đi thẳng vào sinh, tiêu ~5 lượt LLM rồi hỏng muộn — hoặc tệ hơn, dựng một khối đa diện *"gần giống"* và học sinh tin nó |

### 2.7 Oxyz — VIẾT PHƯƠNG TRÌNH mặt phẳng / đường / mặt cầu

| | |
|---|---|
| **Vì sao** | Taxonomy **không có** `kind` nào nhận một biểu thức đại số làm câu trả lời (`GEOMETRY_CURRICULUM_COVERAGE` #18) |
| **Lỗi** | không khai được nghĩa vụ ⇒ `executable` mà không bao giờ `servable` |
| **Không phải lỗi AI** | Oxyz là **nền tính toán bên trong**, không phải chủ đề dạy (`GEOMETRY_ROADMAP §2`) |

### 2.8 Phép toán VECTƠ ở tầng biểu thức · phép chiếu song song

| | |
|---|---|
| **Vì sao** | Không có phép vectơ ở tầng biểu thức (`COVERAGE` #6, #5). `project_onto` là chiếu **vuông góc** |
| **Lỗi** | không diễn đạt được yêu cầu ⇒ nhóm `contract` |
| **Không phải lỗi AI** | — |

### 2.9 Kéo để thấy bất biến (kiểu GeoGebra)

Ngoài phạm vi **đề tài**, không chỉ ngoài Phase 7B: nó liên tục, phá song ánh
`frame k ⇔ trace[k]` (bất biến #31). `GEOMETRY_ROADMAP §2`.

---

## 3. Hệ quả cho taxonomy thất bại của Phase 7B

Taxonomy 4 nhóm (`PHASE7_METRIC_CONTRACT §3`) **không đổi**. Nhưng một lượt
trượt vì §2 **không thuộc nhóm nào trong bốn** — nó không phải lỗi sinh, không
phải hợp đồng thiếu diễn đạt, không phải validator sai, không phải định tuyến:

> **Bài ngoài ranh giới không được đưa vào tầng A ngay từ đầu.** Đó là lý do
> `HOLDOUT_PROTOCOL` nay có điều kiện nhận bài (§3b), và lý do
> `COVERAGE_MATRIX_BOUNDARY_REVIEW.md` gắn điều kiện miền cho từng ô.

Nếu **vẫn** lọt một bài như thế vào tầng A: ghi vào `FAILURE_LOG.md` với nhãn
**`out_of_capability`**, **không** nhét vào bốn nhóm, và nêu riêng trong báo
cáo. Cùng luật đã áp cho lỗi hạ tầng (mạng/quota).

---

## 4. Điều tài liệu này KHÔNG làm

- **Không** sửa một dòng năng lực nào. Không thêm symbolic engine, không đổi
  `Fraction` sang `float`, không thêm căn thức, không sửa `distance`, không mở
  rộng DSL.
- **Không** đổi taxonomy, metric, `k`, số ô, hay ngân sách.
- **Không** phán rằng ranh giới này *nên* rộng hơn. Mở rộng là việc **sau**
  Phase 7B, và phải là quyết định có chủ đích — `GEOMETRY_CURRICULUM_COVERAGE
  §4` đã liệt món rẻ nhất (nối `distance` cho cặp đường–đường) và món **không
  nên làm** (mặt cong).
