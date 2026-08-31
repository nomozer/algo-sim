# CLEAN_BASELINE_V1 — baseline tổng hợp hình học đầu tiên đo đúng hệ

> 6 đề mới, niêm phong trước khi gọi model, đường sản phẩm đầy đủ (có analyze).
> Chạy một lần. Không sửa code hay prompt giữa các đề.

Niêm phong `6ffb0753`, cây sạch, `CACHE_VERSION 57`, miền `hinh_hoc` →
`geometry_program_generator`, prompt `b8bb766b` (4.705 B), thẻ `38dc6b0c`
(2.922 B), seal `fa00ac08`. Tiền kiểm PASS, nhiễm chéo SẠCH.

## 1. Kết quả

| | |
|---|---|
| ONE_SHOT_CORRECT | 1/6 |
| REPAIRED_CORRECT | 1/6 |
| **CORRECT_WITHIN_BUDGET** | **2/6** |
| FAIL_AFTER_REPAIR | 0/6 |
| **SYSTEM_FAILURE** | **4/6** |
| SCHEMA / GROUNDING / HONESTY / SYNTHESIS | 0 / 0 / 0 / 0 |
| LOGICAL_CALLS (tổng hợp) | 7/12 · analyze 6 riêng |
| TOTAL_INPUT / OUTPUT / TOTAL | 18.432 / 8.220 / 51.095 |
| ONE_SHOT / REPAIR TOKEN SHARE | 0,858 / 0,142 |
| ENVELOPE_TRANSPORT | PASS |
| NEW_CODE_REQUIRED_DURING_PROBE | **0** |

**Không ca nào hỏng vì schema, grounding, trung thực hay tổng hợp.** Bốn ca
hỏng ở **runtime**, và cả bốn cùng một nguyên nhân.

## 2. Nguyên nhân gốc — `assign` hình học không khai bị chặn ở SAI TẦNG

| dạng | schema | thẩm định tĩnh | runtime |
|---|---|---|---|
| `assign M = midpoint(B,C)`, `M` **không khai** | ✓ | ✓ | **NÉM** |
| `assign M = midpoint(B,C)`, `M` có khai | ✓ | ✓ | ✓ |
| `construct_point M = midpoint(B,C)`, không khai | ✓ | ✓ | ✓ |

`construct_point` **tự đăng ký** đích. `assign` thì đòi đích phải có trong
`memory_declarations` — nhưng đó là một tính chất **TĨNH**, và không tầng nào
trước runtime kiểm nó.

Tương quan hoàn hảo trên cả sáu ca:

| đề | lớp | `assign` hình học không khai |
|---|---|---|
| `cb_01` | SYSTEM_FAILURE | `M=midpoint`, `H=project_onto` |
| `cb_02` | ONE_SHOT_CORRECT | — |
| `cb_03` | REPAIRED_CORRECT | — |
| `cb_04` | SYSTEM_FAILURE | `M,N,P,Q = midpoint` |
| `cb_05` | SYSTEM_FAILURE | `M=midpoint` |
| `cb_06` | SYSTEM_FAILURE | `I=intersect_line_line` |

### Vì sao đây là lỗi HỆ, không phải lỗi mô hình

Ba lý do, mỗi lý do đủ một mình:

1. **Thẻ văn phạm quảng cáo cả hai lối.** Nó liệt kê `assign: target_var
   expr:biểu thức` và liệt kê `midpoint`, `project_onto`,
   `intersect_line_line` trong danh sách biểu thức giá trị. Không một chữ nào
   nói `assign` trên một giá trị hình học đòi khai trước còn `construct_point`
   thì không. Mô hình chọn một lối được bày ra.
2. **Lỗi nổ ở tầng KHÔNG SỬA ĐƯỢC.** Vòng sửa chỉ gửi ngược lỗi validator và
   thẩm định tĩnh; lỗi runtime giết cả ca. Một tính chất tĩnh bị canh ở runtime
   là đổi một lượt sửa rẻ thành một ca mất trắng.
3. **Đây là lớp lỗi wave trước vừa sửa hai lần** — nhãn
   `construct_plane.through`, từ vựng nghĩa vụ của `fp_6`. Cùng một câu:
   *bề mặt nói được nhiều hơn thứ toàn bộ ngăn xếp chấp nhận.*

Theo §12, `SYNTHESIS` **không** được gắn khi chương trình mô hình đúng mà hệ
chặn sai. Bốn ca này là `SYSTEM`.

## 3. §18 — kiểm khả biểu diễn sau lượt chạy

`EXISTING_IR_EXPRESSIBLE = 6/6`, đo **trước** khi gọi model bằng cách CHẠY lời
giải chuẩn tắc do người viết qua đúng chuỗi cổng sản phẩm và đối chiếu oracle
tính tay (`expressibility.json`). Lời giải ấy không gửi cho model, không tính
là thành công.

⇒ Bốn ca hỏng **không** phải khoảng trống IR. Chúng là
`EXISTING_IR_SYNTHESIS_FAILURE` theo chữ của §18 — nhưng nguyên nhân nằm ở
**hợp đồng bề mặt**, không ở khả năng suy luận của mô hình: lời giải chuẩn tắc
dùng `construct_point`, mô hình dùng `assign`, và chỉ một trong hai lối được
toàn ngăn xếp chấp nhận dù cả hai đều được bày ra.

## 4. Phát hiện phụ, ghi lại chứ không sửa (§7, §20)

**`construct_section` ném `MALFORMED_SOLID` khi mặt cắt đi qua ĐỈNH của khối.**
Bản đầu của `cb_04` cắt hình chóp bằng `(MBC)` với `M` là trung điểm `SA`; mặt
ấy chứa nguyên cạnh `BC`, và thuật toán không nối kín được chuỗi đỉnh. Tìm ra
lúc kiểm khả biểu diễn, tức **trước** khi tiêu call. Đề đã đổi hình cắt để đo
được thứ nó định đo.

## 5. §19 — spot check trình duyệt

Hai ca đúng, Chrome thật, WebGL: **8/8, 0 lỗi console.**

| ca | xưởng 3D | cây thành phần | tua bước |
|---|---|---|---|
| `cb_02` lăng trụ | canvas 1 | 9 mục, chọn được | 2 nút, cảnh còn nguyên |
| `cb_03` hộp, kết quả `3√5/10` | canvas 1 | 31 mục | 2 nút, cảnh còn nguyên |

⚠️ Lượt spot check ĐẦU đỏ 6/8 với **0 lỗi console** — và đó là lỗi của bộ đo,
không của sản phẩm: `compile_semantic_program_to_envelope` một mình cho ra
envelope **2D** (`domain: "generic"`, không `scene3d`). Cảnh 3D do
`pipeline._dung_scene3d` đổ, và thiếu bước ấy thì học sinh mở bài ra thấy một
bảng khung 2D. Không JSON nào phát hiện được điều này — chỉ một câu hỏi trình
duyệt phát hiện được.

## 6. So sánh — và ba thứ KHÔNG được so

| lượt | điểm | vì sao không so trực tiếp |
|---|---|---|
| GENERALIZATION MATRIX | 3/9 | harness truyền `domain="geometry"` ⇒ prompt Tin học |
| dihedral probes | 0/4 | cùng lỗi miền |
| fresh probe | 4/6 | hai bug hợp đồng đã biết (`angle_cos_sq`, từ vựng nghĩa vụ) |
| **CLEAN_BASELINE_V1** | **2/6** | đo đúng hệ |

Ba lượt trên là **bằng chứng phát triển**, không phải baseline. Con số 2/6
thấp hơn 4/6 của fresh probe, và điều đó **không** có nghĩa hệ kém đi: fresh
probe không có analyze nên hợp đồng rỗng, và bộ đề khác hẳn. Hai con số đo hai
thứ khác nhau.

## 7. Phân loại (§21)

**MIXED — nhưng ma sát nằm ở HỆ, không ở mô hình.**

Không phải WEAK: 6/6 đề biểu diễn được, 0 ca hỏng vì schema/grounding/trung
thực/tổng hợp, 0 lỗi provider, và hai ca đúng dựng lên màn hình sạch.

Không phải STRONG: 4/6 không tới được đáp số, và một chương trình đúng về ngữ
nghĩa bị giết ở tầng không sửa được.

Đây là probe nhỏ (n = 6). Nó **không** tuyên bố gì về độ chính xác trên toàn
bộ hình học THPT.
