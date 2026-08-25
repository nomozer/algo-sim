# PHASE 6.7.1 — CHUẨN HOÁ TÊN Ở CỔNG THẨM ĐỊNH (2026-08-26)

> Loại bỏ false negative của validator khi đối tượng đã được resolver chuẩn hoá.
> **Không sửa prompt, không sửa model pipeline, không thêm primitive, không
> thêm DSL.**

---

## 1. Root cause

`check_structural_coverage` hoà giải tên rồi **vứt kết quả đi ở dòng kế**:

```python
if ten_hh and con not in declared:
    if (kq := _hoa_giai(con, set(declared), ob.kind)):
        con = thay              # S.ABCD  →  S_ABCD_solid   ✔
...
elif ob.container not in goc:   # ← tra TÊN HỢP ĐỒNG trong bao đóng
                                #   chỉ chứa TÊN CHƯƠNG TRÌNH        ✘
```

Hai dòng ấy nằm **trong cùng một hàm**, cách nhau vài chục dòng.

Hậu quả **không chỉ** là một false negative. Lời từ chối **vu oan**:

> `witness 'V_S_ABCD' không dẫn xuất từ 'S.ABCD' — chương trình khai đáp án chứ
> không tính nó`

…trong khi chương trình gọi đúng `measure(volume, of="S_ABCD_solid")`.

### Soát toàn bộ tìm ra một lỗi THỨ HAI, cùng lớp

| Cổng | Trạng thái trước | Xử lý |
|---|---|---|
| **C₁a** — kiểm dẫn xuất | dùng `ob.container` thô | → `con` (tên đã phân giải) |
| **C₁b** — `witness not in realized` | **thô hoàn toàn** ← *lỗi mới tìm ra* | nhận `ten_da_hoa_giai` |
| **C₂** — 52 chỗ dùng `ob.*` | đã được **bí danh** che từ trước | không đổi |

C₁b tra `realized` — một tập **tên chương trình**. Không đổi tên trước khi tra
thì mọi nghĩa vụ từng phải hoà giải sẽ bị báo *"chưa hiện thực hoá"* dù biến ấy
có giá trị thật ở mọi bước. Lỗi này **chưa từng nổ** trong 15 lượt Phase 6.7 —
nó nằm sau C₁a, và C₁a đã chặn trước.

`route.verify_and_compile` nay truyền `c1a.ten_da_hoa_giai` cho **cả C₁b lẫn
C₂**: một nguồn sự thật, ba cổng dùng chung. Không alias thủ công, không bảng
tên cố định — ánh xạ do resolver topology của Phase 6.6 sinh ra.

---

## 2. Files changed

| File | +/− | Đổi gì |
|---|:-:|---|
| `semantic_program/coverage_gate.py` | +46/−7 | C₁a dùng `con`; C₁b nhận ánh xạ; thông điệp nói **cả hai tên** |
| `semantic_program/route.py` | +2/−1 | truyền `ten_da_hoa_giai` cho C₁b |
| `tests/geometry/test_validator_name_normalization.py` | +230 | **mới**, 11 test |
| `tests/geometry/test_coverage_semantic_producer.py` | +24/−7 | một test cũ **đang xanh nhờ bug** — xem §5 |

Thông điệp từ chối nay nói cả hai phía khi có hoà giải:
`'S.ABCD' (≡ 'S_ABCD_solid')`. Wave 3 đã học một lần rằng thông điệp một phía
buộc lượt phân tích sau phải chạy forensics.

---

## 3. Test before / after

### Trên IR THẬT của hai lượt đã trượt (không sửa một ký tự nào của chương trình)

| | Trước | Sau |
|---|---|---|
| `2-the-tich-lan2` | `structural_coverage` · exec=False | **`served`** · `V_S_ABCD = 12` |
| `2-the-tich-lan3` | `structural_coverage` · exec=False | **`served`** · `V_S_ABCD = 12` |

`12` khớp kiểm tay `1/3 · 3² · 4`. Qua cổng **và** ra đúng số — nếu chỉ qua cổng
thì bản vá này mới chỉ mở đường cho một lỗi khác.

### Bất biến, không chỉ hai test hiện trường

Đây là lần **thứ ba** cùng một lớp lỗi trong dự án (lưới áp ở cổng này mà không
áp ở cổng kia). Hai test hiện trường chỉ chặn hai chỗ đã biết, nên:

```
test_DOI_TEN_KHONG_DOI_PHAN_QUYET
    đổi tên MỌI vật dựng, giữ nguyên topology  ⇒  phán quyết phải Y HỆT
```

Cổng nào còn đọc tên gốc sẽ lệch ở đó — bất kể nó nằm ở C₁a, C₁b, C₂ hay một
cổng chưa ai viết.

### R0 không yếu đi — có test từng vế

| Vế | Test |
|---|---|
| gán thẳng `V = 12` **vẫn bị chặn**, kể cả khi 12 là đáp án đúng | `test_KHAI_THANG_DAP_AN_van_bi_chan` |
| grounding nguyên vẹn: thiếu cả `source_fact_id` lẫn `model_assumption` vẫn chặn | `test_GROUNDING_khong_bi_dung_toi` |
| `model_assumption` mang đáp án **vẫn bị chặn** | `test_model_assumption_KHONG_duoc_mang_dap_an` |

⚠️ Bản nháp đầu của test *"khai thẳng đáp án"* **xanh vì lý do sai**: grounding
chặn trước nên nó không bao giờ tới cổng phủ. Đã thêm `model_assumption` cho
điểm gốc để nó tới đúng cổng cần kiểm, và ghi chuyện ấy vào docstring — một test
chặn đúng chỗ nhưng vì lý do sai là một test sẽ mất hiệu lực lặng lẽ.

```
pytest  2839 passed  (trước: 2837 + 2 test mới thay 1 test cũ)
```

---

## 4. Vì sao đây là lỗi VALIDATOR, không phải lỗi MODEL

Bằng chứng trực tiếp, không suy luận: **chạy lại đúng IR mà mô hình đã sinh**,
không sửa một ký tự nào của chương trình → cả hai lượt `served`, `V = 12`.

Chương trình vốn đã đúng ở cả ba tầng:

```
construct_solid  S_ABCD_solid ← S, A, B, C, D        đúng topology
assign           V_S_ABCD = measure(volume, of=S_ABCD_solid)   đúng cách tính
kết quả          12                                   đúng đáp án
```

Thứ duy nhất "sai" là **cái tên** `S_ABCD_solid` ≠ `S.ABCD`. Mà tên là thứ
resolver đã hoà giải xong — cổng chỉ không dùng kết quả ấy.

Phân biệt này **không phải chuyện chữ nghĩa**. Nếu ghi nó vào nhóm A (model
generation), luận văn sẽ báo cáo một con số thấp hơn thực tế **và** kết tội mô
hình ở đúng chỗ nó làm đúng. Với một đề tài mà luận điểm là *"AI sinh được
chương trình đáng tin cậy hay không"*, một thước đo vu oan còn tệ hơn không đo.

---

## 5. Một test cũ đang xanh **nhờ chính con bug**

`test_details_noi_hai_phia_khi_CONTAINER_lech` dùng container `khoi_chop`. Nhưng
`khoi` là một phụ tố kiểu hợp lệ, nên lưới Phase 6.6 hoà giải `khoi_chop ≡ chop`
từ trước pha này. Test vẫn xanh **chỉ vì** phép kiểm dẫn xuất tra tên gốc và vẫn
phát ra một thông điệp lệch.

Sửa bug đi thì test mất đối tượng. **Ý định giữ nguyên** (thông điệp phải nói cả
hai phía khi container *không* phân giải được), đổi sang `hinh_lang_tru` — tên
không lưới nào hoà giải nổi. Thêm một test cho vế còn lại:
`khoi_chop ≡ chop` là hoà giải **đúng**, và trước pha này bị từ chối oan.

Ghi lại vì nó là một bài học chung: **một bug đủ lâu sẽ có test dựa vào nó.**

---

## 6. Ba smoke sau bản vá

```
1 · trung điểm      ❌  execution · GEOMETRY_OPERAND_TYPE: biểu thức lạ `literal`
2 · thể tích        ✅  served · 8 đối tượng · 4 bước · V = 12
3 · thiết diện PMN  ✅  served · 14 đối tượng · 10 bước
                        plane_abcd plane_pmn d line_ad Q pyramid_sabcd
```

**2/3.** Bài 3 đáng chú ý: mô hình đặt tên **chữ thường** (`plane_abcd`,
`pyramid_sabcd`) và resolver topology vẫn khớp — đúng thứ Phase 6.6 thiết kế.

### Bài 1 — phân loại: **A. Model generation**

Hai lượt thử:

1. viết `{"kind": "point_on_line", …}` làm một **biểu thức giá trị** — schema từ
   chối, retry
2. viết `construct_point M = literal(...)` — kênh sai: toạ độ điểm gốc thuộc về
   `memory_declarations[].initial_value` + `model_assumption`

Đường đúng vẫn mở và mô hình **đã** đi đúng ở những lượt khác
(`construct_point M = midpoint(S, A)`). Nên đây là mô hình chọn sai kênh, không
phải hợp đồng thiếu cách nói.

⚠️ **Một quan trắc về cấu trúc, không sửa trong pha này**: lỗi ấy nổ ở
`execution`, tức **sau** vòng sửa. Lỗi validator được gửi ngược cho mô hình sửa
(≤3 lượt); lỗi runtime thì không. Một chương trình sai kênh kiểu này **không bao
giờ có cơ hội được sửa**, dù thông báo đã nói rõ chỗ sai. Ghi lại cho pha sau —
ngoài phạm vi 6.7.1.

---

## 7. Đủ điều kiện chạy lại Phase 6.7 chưa?

# ✅ ĐỦ

| Điều kiện | |
|---|---|
| lỗi nhóm C đã sửa, có bằng chứng trên IR thật | ✅ |
| R0 không yếu đi — ba vế đều có test | ✅ |
| grounding không bị đụng tới | ✅ |
| `pytest` xanh (2839) | ✅ |
| môi trường: `runtime_doctor --doi-mode serve` PASS, cây sạch, cache 0 row | ✅ |
| không sửa prompt / pipeline / primitive / DSL | ✅ |

Bản đo mới: `8a3adb8` · `CACHE_VERSION 45` · skill `6208fc2a` · thẻ `7441ed3c`.

**Lượt đo lại phải là một PHÉP ĐO, không phải xác nhận một phép chiếu.** Phase
6.7 chiếu rằng bài 2 lẽ ra `4/5` và tổng `11/15` — con số ấy **chưa được đo**, và
lượt sau phải đối chiếu với bảng thật ở `PHASE6_7_STABILITY_REPORT.md §1` chứ
không đối chiếu với phép chiếu.

Và nhắc lại điều Phase 6.7 đã kết luận, vì nó không đổi sau pha này: **chỉ số
phải là một CẶP** — `served` **và** `obligation_match`. Bài 3 đạt 4/5 `served`
nhưng 1/5 `obligation_match`, trong đó 2 lượt served **không kiểm gì cả**.
Báo cáo `served` một mình sẽ nói quá.

---

## Chi phí

3 lượt smoke ≈ **20 lượt LLM**. Phần còn lại của pha này chạy **0 API call** —
hai lượt trượt được tái hiện bằng chính IR đã lưu ở `stability-6.7/`.
