# PHASE 5 — GEOMETRY GENERATION EVALUATION · lượt 2

> **TẬP DEV, KHÔNG phải benchmark.** Được nhìn, hệ đã được sửa theo nó. Số ở đây
> **không bao giờ** là số held-out của luận văn.

| | |
|---|---|
| Commit đo | `027c9e1` · nhánh `main` · **cây sạch toàn kho** |
| `measured_system_hash` | `24e80b8ff48ac361` · 141 file |
| `CACHE_VERSION` | 40 |
| Model | `gemini-2.5-flash` |
| Chạy | **10/10**, `hoan_tat = true`, không đứt ngân sách |
| So với | lượt 1 (`5c93e22`, 2026-08-24) |

---

## 1. Metrics

| | lượt 1 | **lượt 2** | |
|---|:---:|:---:|---|
| **G1** cú pháp | 6/10 | **9/10** | qua schema Pydantic |
| **G2** ngữ nghĩa | 6/10 | **9/10** | qua `validate_semantic_program` |
| **A** chạy trọn | 0/10 | **1/10** | interpreter chạy hết, 0 vi phạm biên |
| **O** oracle | 0/0 | **1/1 PASS** | ← **lần đầu có dữ liệu** |
| `obligation_match` | 3/6 | **10/10** | khai đúng LOẠI nghĩa vụ |

`O = 1/1`, không phải `1/10`. Mẫu số là **số bài chạy được**; chín bài kia không
tới interpreter nên oracle không có gì để chấm — chúng là `NO_RESULT`, một trạng
thái riêng, không phải `FAIL`.

Mẫu số 10 < 20 nên `RELIABILITY_EVALUATION_PLAN §3.3` cấm viết phần trăm.

## 2. Từng case

| case | G1 | G2 | A | oracle | obl | tầng | mã lỗi |
|---|:-:|:-:|:-:|---|:-:|:-:|---|
| geo_01 | ✅ | ✅ | ❌ | `NO_RESULT` | ✅ | 6 | `requested_operation_uncovered` |
| geo_02 | ✅ | ✅ | ❌ | `NO_RESULT` | ✅ | 6 | `requested_operation_uncovered` |
| geo_03 | ✅ | ✅ | ❌ | `NO_RESULT` | ✅ | 6 | `input_not_grounded` |
| **geo_04** | ✅ | ✅ | **✅** | **`PASS`** | ✅ | — | — |
| geo_05 | ✅ | ✅ | ❌ | `NO_RESULT` | ✅ | 6 | `input_not_grounded` |
| geo_06 | ✅ | ✅ | ❌ | `NO_RESULT` | ✅ | 6 | `input_not_grounded` |
| geo_07 | ✅ | ✅ | ❌ | `NO_RESULT` | ✅ | 6 | `input_not_grounded` |
| geo_08 | ✅ | ✅ | ❌ | `NO_RESULT` | ✅ | 6 | `input_not_grounded` |
| geo_09 | ✅ | ✅ | ❌ | `NO_RESULT` | ✅ | 6 | `input_not_grounded` |
| geo_10 | ❌ | ❌ | ❌ | — | ✅ | 2 | `semantic_program_invalid` |

**Phân bố: tầng 6 = 8 · tầng 2 = 1 · đi trọn đường = 1.**
Tầng 3 (dependency) và 4 (execution): **0**.

---

## 3. Failure taxonomy

| Nhóm | Ca | Bài |
|---|---:|---|
| schema failure | 1 | geo_10 |
| semantic validation failure | 0 | — |
| **grounding failure** | **6** | geo_03 · 05 · 06 · 07 · 08 · 09 |
| dependency failure | 0 | — |
| execution failure | 0 | — |
| oracle failure | 0 | — |
| obligation mismatch | **0** | — |
| coverage (C₁a) | 2 | geo_01 · geo_02 |

### ① Grounding — 6 ca. **Luật ưu tiên của TÔI giết chương trình đúng.**

Chạy lại cổng tất định offline (0 API call) trên chương trình đã sinh:

```
geo_09  7 khai báo · 5 có model_assumption · giả thiết được nhận: 1
        B: source_fact_id 'canh_day' không có trong RequestContract
        D: source_fact_id 'canh_day' không có trong RequestContract
        C: source_fact_id 'abcd_hinh_vuong' không có trong RequestContract
```

Chương trình `geo_09` mô hình sinh ra **gần như trùng khít** bản viết tay dùng
làm chuẩn trong `test_geometry_wave2.py`:

```
A point3 [0,0,0]  assum=CÓ        s_abcd          solid  init=None
B point3 [1,0,0]  assum=CÓ fact=canh_day          construct_solid
C point3 [1,1,0]  assum=CÓ fact=abcd_hinh_vuong   the_tich_s_abcd float
D point3 [0,1,0]  assum=CÓ fact=canh_day          measure(volume)
S point3 [0,0,2]  assum=CÓ fact=chieu_cao_sa
```

**Mô hình dùng `model_assumption` ĐÚNG.** Nó còn làm hơn thế: gắn *thêm*
`source_fact_id` để nói toạ độ ấy bắt nguồn từ dữ kiện nào của đề. Nhưng Wave 2
tôi viết luật *"`source_fact_id` VẪN THẮNG khi khai cả hai"*, cho rằng đó là
chiều an toàn. Hệ quả thật ngược lại: **một id sai biến cả chương trình đúng
thành trượt**, và mô hình bị phạt vì đã nói nhiều thông tin hơn.

Vì sao id sai? `canh_day`, `abcd_hinh_vuong`, `sa_vuong_goc_day` là những id
**hợp lý** — nhưng chúng không có trong `RequestContract`. Hai lượt LLM không
dùng chung không gian tên cho id dữ kiện: lượt đọc đề đặt id của nó, lượt viết
chương trình đặt id khác. Đây đúng họ với khe hở `_obligations_for_prompt` đã
phải vá cho `container`/`witness` ở miền Tin học (12/40 ca).

### ② C₁a — 2 ca. Witness không có ai tạo ra.

```
geo_01  khai: A B C D M S abcd point_on_plane
        tạo : M abcd
geo_02  khai: A B C D S a b giao_tuyen_sab_abcd plane_abcd plane_sab
        tạo : a b giao_tuyen_sab_abcd plane_abcd plane_sab
```

`geo_02` tạo ra **mọi thứ nó cần** mà C₁a vẫn từ chối ⇒ tên witness do lượt
`analyze` chọn **không nằm trong chương trình**. Cùng gốc với ①: lệch danh xưng
giữa hai lượt.

⚠️ **Tôi không xác nhận được tên witness đó.** Artifact **không lưu
`RequestContract`** — xem §6. Kết luận này là suy ra từ dấu vết, không phải đọc
từ vật chứng, và tôi ghi rõ mức chắc chắn của nó.

Đối chứng có ích: `geo_04` **PASS** với cùng hình dạng (`point_on_plane` cũng
không được tạo ra) — khác biệt duy nhất là witness của nó rơi trúng một biến
chương trình có sinh.

### ③ Schema — 1 ca (geo_10)

```
statements.0.construct_plane.through
  Input should be a valid list
  input_value = {'kind': 'literal', 'value': ['A','B','C']}
statements.3.construct_solid.vertices   (cùng lỗi)
```

Không phải bịa từ vựng như lượt 1 — hai primitive **đã tồn tại và được gọi
đúng tên**. Lỗi là **bọc thừa**: mô hình gói danh sách tên vào một biểu thức
`literal` thay vì đưa danh sách trần. Đây là lớp lỗi *hình dạng wire*, cùng họ
với ba lớp `canonical_*` đã phải mở ở miền Tin học.

---

## 4. Cost report — **số THẬT, không ước lượng**

| | |
|---|---|
| model | `gemini-2.5-flash` |
| lượt logic | **28** / 60 |
| HTTP request | **30** / 80 |
| request do retry | **2** |
| gặp 429/5xx | **0** |
| tổng token | **143 098** |

```
prompt_tokens           65 007        semantic_analyze   10 lượt
candidates_tokens       20 220          prompt 11 205 · out  2 554 · thoughts 11 835
thoughts_tokens         57 871        semantic_program   18 lượt
cached_content_tokens    7 956          prompt 53 802 · out 17 666 · thoughts 46 036
```

**USD ≈ 0.2171** — CHẶN TRÊN (token cache tính đầy giá input, không trừ bậc
miễn phí). Đơn giá `input 0.30 · output 2.50` / triệu token, tra ngày
2026-08-25, ghi kèm trong artifact để tái lập được.

**Độ trễ** (tính lại từ `do_tre` từng bài):

```
tổng 639.49s · trung bình 63.95s/bài · một lượt gọi chậm nhất 270.20s (geo_02)
```

`thoughts_tokens` chiếm **40%** tổng token và `semantic_program` ăn 18/28 lượt
logic — 8 lượt là vòng sửa. Một lượt 270s cho thấy đuôi phân bố rất dài.

---

## 5. Kết luận ba tầng

### Tầng 1 — Hệ đã đo được AI sinh Geometry Program chưa?

**RỒI.** Lượt 1 không thu được dữ liệu nào về mô hình vì mọi bài chết ở hợp đồng
của ta. Lượt này: **9/10 chương trình hợp lệ, 1 chạy trọn, và oracle độc lập
phán `PASS`.** `obligation_match` **10/10** — không còn một ca nào khai nhầm
nghĩa vụ, so với 3/6 lượt trước.

### Tầng 2 — LLM sinh được đến mức nào?

Nói đúng phạm vi: **"AI sinh Geometry Program trong semantic simulation
framework"** — không phải "AI sinh mô phỏng 3D".

- **Đọc đề → nghĩa vụ: 10/10.** Tách miền `analyze` giải quyết trọn vấn đề này.
- **Viết IR hợp lệ: 9/10.** Dùng đúng `construct_plane`/`construct_solid`/
  `measure`, đặt hệ toạ độ hợp lý, khai `model_assumption` đúng chỗ.
- **Đi qua toàn bộ cổng: 1/10.** Chín bài chết ở **hợp đồng**, không ở **toán**.
- **Đúng toán khi tới được oracle: 1/1.**

Điều **KHÔNG** được suy ra: `1/1` chưa nói gì về độ tin cậy toán học — một mẫu
không phải một tỉ lệ. Và `9/10 hợp lệ` **không** đồng nghĩa `9/10 đúng`: qua
thẩm định nghĩa là *hình dạng hợp lệ*.

### Tầng 3 — Còn thiếu lớp nào để tới mô phỏng 3D tương tác?

| Lớp | Trạng thái |
|---|---|
| Sinh IR | **đo được**, 9/10 |
| Chạy tất định | đo được, nghẽn ở hợp đồng |
| Đúng toán (O) | mới có 1 mẫu |
| **B — servable** | **CHƯA đo được**: tập nguyên thuỷ thị giác không có nguyên thuỷ 3D nào |
| Renderer 3D | **chưa tồn tại** |
| Tương tác / kéo thả | **chưa tồn tại** |

Ba lớp cuối chưa nằm trong phép đo này, nên **không kết luận gì về chúng**.

---

## 6. Thiếu sót của chính lượt đo — khai để lần sau đừng lặp

1. **Artifact không lưu `RequestContract`.** Đây là thiếu sót nặng nhất: nó biến
   chẩn đoán §3② thành *suy ra từ dấu vết* thay vì *đọc từ vật chứng*. Không có
   `input_facts` và `obligations` mà lượt `analyze` sinh ra thì không xác nhận
   được id/witness nào đã lệch.
2. **`chi_phi.do_tre` cấp lượt = `{so_luot: 0}`.** `tong_ket` gọi
   `AU.bao_cao(model, budget)` mà **không truyền bộ ghi**, nên độ trễ tổng in ra
   `0s`. Dữ liệu không mất — `do_tre` từng bài vẫn đủ, và §4 tính lại từ đó —
   nhưng con số in ra màn hình lúc chạy là **sai**, và một con số sai in ra
   trong lúc chạy là thứ dễ bị chép lại nhất.
3. **`failure_reason` không mang `details`.** Mã lỗi chi tiết (`[MODEL_ASSUMPTION_
   IS_ANSWER]`…) nằm ở `outcome.details`, runner chỉ lưu `outcome.reason`. Phải
   chạy lại cổng offline mới lấy được.

Cả ba là lỗi **harness**, không đụng kết quả đã đo.

---

## 7. Điều KHÔNG được làm sau báo cáo này

Kết quả là **dữ liệu**, không phải lỗi cần vá gấp. Cấm: sửa prompt để tăng tỉ
lệ · nới grounding cho dễ thở · bỏ case fail · đổi dataset · gọi lượt này là
benchmark · lấy điểm DEV làm accuracy.

Hai nguyên nhân chặn ở §3①② đều là **lệch danh xưng giữa hai lượt LLM** —
cùng một lớp lỗi, và sửa nó là một wave riêng có phạm vi khai trước. Đặc biệt
luật ưu tiên `source_fact_id`: nó là quyết định **của tôi ở Wave 2**, và bằng
chứng lượt này cho thấy nó phạt nhầm. Nhưng đảo nó là đụng cổng an toàn, phải
có thiết kế riêng.

**Không renderer. Không tương tác. Không kéo thả. Không mở rộng primitive.**
