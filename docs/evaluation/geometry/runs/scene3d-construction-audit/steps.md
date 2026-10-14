# Bảng từng bước dựng — ba cảnh phục vụ

Sinh từ `after/audit-intel-d3d11/construction-audit.json` (cột «toán», ảnh) và `before/audit/construction-audit.json`
(cột «hình» trước sửa). Mỗi bước trace thuộc một bước học (`geometryTimeline`); ảnh là khung của bước học, cùng tên trong
`after/{swiftshader,intel-d3d11}/<cảnh>/` và `before/swiftshader/<cảnh>/`. Bước MEASURE vectơ `derived_*_vec` không vẽ
(`non_visual`), là bước diễn giải nhập vào bước học trước. Định nghĩa, toạ độ khung, quan hệ và vị trí trong/ngoài khối
của từng điểm: `points` trong JSON; đối chiếu oracle thiết diện: `section`; biến thể metamorphic: `metamorphic`.
Hình FAIL trước sửa = nhãn đỉnh bị giấu khi hộp nhãn không chạm nhãn nào đang hiện (S ở chóp; A′, B′ ở hộp).
Cột «hình» lấy phán quyết của BƯỚC HỌC chứa bước trace (khung `anchor`), không đo riêng từng bước trace.


### two-line-pyramid — đáp số 9/4, 16 bước trace, 8 điểm

| trace | bước học | thao tác | đầu vào | đầu ra mới | toán | hình (trước → sau) | ảnh |
|---|---|---|---|---|---|---|---|
| 0 | 1 | INIT |  | A, B, C, D, S | PASS | PASS → PASS | `step-01.png` |
| 1 | 2 | CREATE M | A, B | M | PASS | PASS → PASS | `step-02.png` |
| 2 | 2 | MEASURE derived_H_vec | B, C | derived_H_vec | PASS | PASS → PASS | `step-02.png` |
| 3 | 3 | CREATE H | M, derived_H_vec | H | PASS | PASS → PASS | `step-03.png` |
| 4 | 3 | MEASURE derived_H1_vec | A, S | derived_H1_vec | PASS | PASS → PASS | `step-03.png` |
| 5 | 4 | CREATE H1 | M, derived_H1_vec | H1 | PASS | FAIL → PASS | `step-04.png` |
| 6 | 5 | CREATE day_ABCD | A, B, C, D | day_ABCD | PASS | FAIL → PASS | `step-05.png` |
| 7 | 6 | CREATE canh_ben | canh_ben_S_A, canh_ben_S_B, canh_ben_S_C, canh_ben_S_D | canh_ben_S_A, canh_ben_S_B, canh_ben_S_C, canh_ben_S_D | PASS | FAIL → PASS | `step-06.png` |
| 8 | 7 | CREATE khoi_S_ABCD | S, A, B, C, D | khoi_S_ABCD | PASS | FAIL → PASS | `step-07.png` |
| 9 | 8 | CREATE mp_td_q | M, H, H1 | mp_td_q | PASS | FAIL → PASS | `step-08.png` |
| 10 | 9 | EXTEND td_q (mặt ABCD) | khoi_S_ABCD, mp_td_q | td_q | PASS | FAIL → PASS | `step-09.png` |
| 11 | 10 | EXTEND td_q (mặt SCD) | khoi_S_ABCD, mp_td_q | cạnh thiết diện 2 | PASS | FAIL → PASS | `step-10.png` |
| 12 | 11 | EXTEND td_q (mặt SBC) | khoi_S_ABCD, mp_td_q | cạnh thiết diện 3 | PASS | FAIL → PASS | `step-11.png` |
| 13 | 12 | EXTEND td_q (mặt SAB) | khoi_S_ABCD, mp_td_q | cạnh thiết diện 4 khép | PASS | FAIL → PASS | `step-12.png` |
| 14 | 13 | STEP td_q | khoi_S_ABCD, mp_td_q | cạnh thiết diện 4 khép + tô | PASS | FAIL → PASS | `step-13.png` |
| 15 | 13 | MEASURE kq_q | td_q | kq_q | PASS | FAIL → PASS | `step-13.png` |

### two-line-prism — đáp số 3, 14 bước trace, 9 điểm

| trace | bước học | thao tác | đầu vào | đầu ra mới | toán | hình (trước → sau) | ảnh |
|---|---|---|---|---|---|---|---|
| 0 | 1 | INIT |  | A, A_prime, B, B_prime, C, C_prime | PASS | PASS → PASS | `step-01.png` |
| 1 | 2 | CREATE M | A, B | M | PASS | PASS → PASS | `step-02.png` |
| 2 | 2 | MEASURE derived_H_vec | B, C | derived_H_vec | PASS | PASS → PASS | `step-02.png` |
| 3 | 3 | CREATE H | M, derived_H_vec | H | PASS | PASS → PASS | `step-03.png` |
| 4 | 3 | MEASURE derived_H1_vec | B, B_prime | derived_H1_vec | PASS | PASS → PASS | `step-03.png` |
| 5 | 4 | CREATE H1 | M, derived_H1_vec | H1 | PASS | PASS → PASS | `step-04.png` |
| 6 | 5 | CREATE khoi_ABC_A_primeB_primeC_prime | A, B, C, A_prime, B_prime, C_prime | khoi_ABC_A_primeB_primeC_prime | PASS | PASS → PASS | `step-05.png` |
| 7 | 6 | CREATE mp_td_q | M, H, H1 | mp_td_q | PASS | PASS → PASS | `step-06.png` |
| 8 | 7 | EXTEND td_q (mặt ABC) | khoi_ABC_A_primeB_primeC_prime, mp_td_q | td_q | PASS | PASS → PASS | `step-07.png` |
| 9 | 8 | EXTEND td_q (mặt CAA′C′) | khoi_ABC_A_primeB_primeC_prime, mp_td_q | cạnh thiết diện 2 | PASS | PASS → PASS | `step-08.png` |
| 10 | 9 | EXTEND td_q (mặt A′B′C′) | khoi_ABC_A_primeB_primeC_prime, mp_td_q | cạnh thiết diện 3 | PASS | PASS → PASS | `step-09.png` |
| 11 | 10 | EXTEND td_q (mặt ABB′A′) | khoi_ABC_A_primeB_primeC_prime, mp_td_q | cạnh thiết diện 4 khép | PASS | PASS → PASS | `step-10.png` |
| 12 | 11 | STEP td_q | khoi_ABC_A_primeB_primeC_prime, mp_td_q | cạnh thiết diện 4 khép + tô | PASS | PASS → PASS | `step-11.png` |
| 13 | 11 | MEASURE kq_q | td_q | kq_q | PASS | PASS → PASS | `step-11.png` |

### two-line-cuboid — đáp số 12, 14 bước trace, 11 điểm

| trace | bước học | thao tác | đầu vào | đầu ra mới | toán | hình (trước → sau) | ảnh |
|---|---|---|---|---|---|---|---|
| 0 | 1 | INIT |  | A, A_prime, B, B_prime, C, C_prime, D, D_prime | PASS | PASS → PASS | `step-01.png` |
| 1 | 2 | CREATE M | A, B | M | PASS | PASS → PASS | `step-02.png` |
| 2 | 2 | MEASURE derived_H_vec | B, C | derived_H_vec | PASS | PASS → PASS | `step-02.png` |
| 3 | 3 | CREATE H | M, derived_H_vec | H | PASS | PASS → PASS | `step-03.png` |
| 4 | 3 | MEASURE derived_H1_vec | B, B_prime | derived_H1_vec | PASS | PASS → PASS | `step-03.png` |
| 5 | 4 | CREATE H1 | M, derived_H1_vec | H1 | PASS | FAIL → PASS | `step-04.png` |
| 6 | 5 | CREATE khoi_ABCD_A_primeB_primeC_primeD_prime | A, B, C, D, A_prime, B_prime, C_prime, D_prime | khoi_ABCD_A_primeB_primeC_primeD_prime | PASS | FAIL → PASS | `step-05.png` |
| 7 | 6 | CREATE mp_td_q | M, H, H1 | mp_td_q | PASS | FAIL → PASS | `step-06.png` |
| 8 | 7 | EXTEND td_q (mặt ABCD) | khoi_ABCD_A_primeB_primeC_primeD_prime, mp_td_q | td_q | PASS | FAIL → PASS | `step-07.png` |
| 9 | 8 | EXTEND td_q (mặt CDD′C′) | khoi_ABCD_A_primeB_primeC_primeD_prime, mp_td_q | cạnh thiết diện 2 | PASS | FAIL → PASS | `step-08.png` |
| 10 | 9 | EXTEND td_q (mặt A′B′C′D′) | khoi_ABCD_A_primeB_primeC_primeD_prime, mp_td_q | cạnh thiết diện 3 | PASS | FAIL → PASS | `step-09.png` |
| 11 | 10 | EXTEND td_q (mặt ABB′A′) | khoi_ABCD_A_primeB_primeC_primeD_prime, mp_td_q | cạnh thiết diện 4 khép | PASS | FAIL → PASS | `step-10.png` |
| 12 | 11 | STEP td_q | khoi_ABCD_A_primeB_primeC_primeD_prime, mp_td_q | cạnh thiết diện 4 khép + tô | PASS | FAIL → PASS | `step-11.png` |
| 13 | 11 | MEASURE kq_q | td_q | kq_q | PASS | FAIL → PASS | `step-11.png` |
