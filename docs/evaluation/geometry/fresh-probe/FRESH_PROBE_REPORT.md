# FRESH PROBE — PROMPT BIAS + SYNTHESIS CLEANUP

> Sáu đề tươi, niêm phong trước khi gọi model. Trần cứng 12 lượt. Chạy một lần.

## 0. PHÁT HIỆN TRƯỚC KHI CHẠY — hai tuyến đo cũ dùng NHẦM PROMPT

Tìm ra lúc chuẩn bị runner, **không** phải bằng probe.

`program_skill_for(domain)` so `domain == "hinh_hoc"`. Mọi chuỗi khác rơi vào
nhánh `else` và trả `"semantic_program"` — **prompt Tin học**. Không lỗi, không
cảnh báo.

```
program_skill_for("geometry")  →  "semantic_program"          ← Tin học
program_skill_for("hinh_hoc")  →  "geometry_program_generator" ← hình học
```

Hai runner truyền chuỗi `"geometry"`:

| runner | artifact | prompt THẬT SỰ dùng |
|---|---|---|
| `run_generalization_matrix.py` | `generalization-matrix/matrix.json` | **Tin học** |
| `probe_dihedral_synthesis.py` | `dihedral-probe*/` (6 thư mục) | **Tin học** |
| `run_geometry_dev_evaluation.py` | `dev-results*/` | hình học ✓ (dùng hằng số) |

Sản phẩm thì đúng: `detect_domain()` trả `"hinh_hoc"`. Chỉ **bộ đo** sai.

### Điều này đổi cách đọc gì

| tuyên bố | còn đứng? |
|---|---|
| `angle_cos` trên `line3` — 14 lượt / 220.898 token | **CÒN** — số đếm không phụ thuộc prompt nào |
| nhãn `construct_plane.through` = `[x,y,z]` gây lỗi | **CÒN** — thẻ văn phạm chung cho cả hai prompt |
| thẻ không nói kiểu toán hạng `measure` | **CÒN** — cũng là thẻ chung |
| *"bảng prompt gắn 'nhị diện' cạnh `angle_cos` nên mô hình chọn nó"* | **KHÔNG** — các lượt ấy chưa từng nhận bảng đó |
| matrix 3/9 đo năng lực tổng hợp hình học | **KHÔNG** — nó đo tổng hợp hình học *bằng hợp đồng Tin học* |

Quy kết đúng cho 14 lượt ấy hẹp hơn và mạnh hơn: mô hình chỉ thấy dòng enum
trần `quantity(distance|angle_cos_sq|angle_cos|volume)` — không kiểu toán hạng,
không ngữ nghĩa — nên nó chọn theo **tên**, và tên chứa sẵn chữ "cos". Bản sửa
thiên lệch trong prompt vẫn đúng (bảng ấy có thật và sản phẩm có dùng), nhưng
**bằng chứng cho nó thì chưa có**.

### Không hồi tố

`matrix.json` và `dihedral-probe*/` **giữ nguyên**. Điểm 3/9 không đổi. Hai
runner đã sửa để lượt SAU đo đúng thứ nó tưởng đang đo; artifact cũ sinh ra
trước bản sửa và phải đọc dưới ghi chú này.

Hàng rào thứ ba: `tests/semantic_program/test_domain_string.py` quét mọi
`scripts/*.py`, bắt mọi `domain="…"` không phải hằng số. Lỗi này đã xảy ra
**hai lần** — lần đầu ở sản phẩm (`stage_semantic_program` viết cứng
`"semantic_program"`), lần này ở bộ đo. Cùng một hình: một chuỗi tự do ở chỗ
đáng lẽ là hằng số.

### Hệ quả cho probe này

Sáu đề dưới đây là **lượt đo đầu tiên** của `geometry_program_generator.md`
qua harness probe. Không có baseline cùng điều kiện để so — mọi so sánh với
matrix hay dihedral probe đều là so hai prompt khác nhau, và báo cáo này
không làm phép so đó.

## 0b. LƯỢT 1 VỠ — và điều đó phải nằm ở đây, không ở đâu khác

Lượt live đầu tiên **vỡ giữa chừng** vì lỗi của bộ đo, không phải của hệ.

`_Nhat` được viết với `__call__(ten, **kw)`, trong khi hợp đồng observer là
`emit(event_type, data)`. Nó **không** vỡ ở đề 1 mà ở đề 6, vì năm đề trước
đều trả spec ngay lượt đầu nên pipeline không phát event nào. Tức bug ẩn đúng
ở ca cần nhật ký nhất — ca có lượt sửa.

    ~6 lượt gọi đã tiêu · artifact KHÔNG được ghi

### Điều tôi đã thấy trước khi chạy lại

Đây là toàn bộ output còn đọc được của lượt 1. Ghi ra vì lượt 2 chạy **sau khi
tôi đã thấy nó**, nên bộ đề không còn "unseen" trọn vẹn, và người đọc phải
biết chính xác cái gì đã lộ:

| đề | lớp | ghi chú console |
|---|---|---|
| `fp_1_tu_dien_nhieu_buoc` | *(trôi khỏi màn hình — không đọc được)* | — |
| `fp_2_lang_tru_goc` | FAIL_AFTER_REPAIR · GROUNDING | `source_fact_id 'AB = 2'` không có trong hợp đồng |
| `fp_3_hop_chu_nhat_can` | ONE_SHOT_CORRECT | — |
| `fp_4_thiet_dien_hoi_tiep` | FAIL_AFTER_REPAIR · GROUNDING | `source_fact_id 'ABCD là hình vuông cạnh 2'` |
| `fp_5_goc_va_khoang_cach` | EXECUTABLE_BUT_INCORRECT | WRONG_ANSWER |
| `fp_6_nhieu_nghia_vu_sau` | *(vỡ giữa lượt)* | AttributeError trong bộ đo |

Không thấy: token từng đề, `attempts_log`, chương trình thô, mọi số của §17.

### Vì sao chạy lại thay vì dừng

§15 cấm rerun để chặn việc chọn lọc điểm số. Một lượt vỡ không sinh ra điểm số
nào để chọn. Nhưng nó có sinh ra **thông tin**, nên đánh đổi được khai thẳng:
lượt 2 đo trên bộ đề mà tôi đã biết 4/6 kết quả lớp. Quyết định do người vận
hành, không phải do bộ đo.

Điều KHÔNG đổi giữa hai lượt: bộ đề, oracle tính tay, prompt, thẻ văn phạm,
trần 12 lượt. Chỉ `_Nhat.emit` đổi — một hàm của bộ đo, không nằm trên đường
sinh chương trình.

## 1. Kết quả

Niêm phong `27529d9f`, cây sạch, `CACHE_VERSION 56`, prompt `e5423cee` (4.733 B),
thẻ `19f6298e` (2.877 B). Nhiễm chéo: sạch. Nguồn: `probe.json`.

| | |
|---|---|
| ONE_SHOT_CORRECT | **4/6** |
| REPAIRED_CORRECT | 0/6 |
| CORRECT_WITHIN_BUDGET | **4/6** |
| EXECUTABLE_BUT_INCORRECT | 1/6 |
| FAIL_AFTER_REPAIR | 1/6 |
| SYSTEM_FAILURE | 0/6 |
| SCHEMA_FAILURES | 1 |
| **PROMPT_BIAS_FAILURES** | **0** |
| HONESTY_FAILURES | 0 |
| UNSUPPORTED_IR_FAILURES | 0 |
| LOGICAL_CALLS | 7/12 |
| TOTAL_INPUT / OUTPUT / TOTAL | 16.207 / 7.212 / 38.473 |
| TOKENS_PER_CORRECT_EXECUTABLE_IR | 9.618 |
| REPAIR_TOKEN_SHARE | 0,199 |
| AVERAGE_CALLS_PER_SUCCESS | 1,75 |

**`fp_2` là ca đáng chú ý nhất.** Đề hỏi *"tính côsin của góc giữa hai đường
thẳng AB' và BC'"* — chữ "côsin" nằm ngay trong câu hỏi, đúng bẫy đã kéo mô
hình chọn `angle_cos` 14 lần trong AUDIT. Lần này nó chọn **`angle_cos_sq`**,
dựng hai `construct_line` rồi đo, không dựng vectơ thừa nào, và ra đúng 0.

## 2. HAI BUG HỆ THỐNG probe tìm ra — ghi, KHÔNG sửa rồi chạy lại (§19)

### 2.1 `angle_cos_sq` trả **sin²** cho cặp (đường, mặt)

`fp_5` hỏi côsin góc giữa `SC` và mặt `(ABC)`. Mô hình dùng `angle_cos_sq`,
đặt tên biến `cos_angle_SC_ABC_sq`, và nhận **1/3**. Oracle tính tay là **2/3**.

1/3 là **sin²**, không phải cos². Kernel:

```python
if isinstance(a, Line3) and isinstance(b, Plane3):
    return M.sin_sq_line_plane(a, b)     # ← một trong bốn nhánh trả sin²
```

Hàm `sin_sq_line_plane` **tự nó trung thực** — docstring nói rõ *"trả `sin²`
để tên hàm nói đúng thứ nó trả"*. Chỗ nói dối là **tên ở tầng IR**: mô hình
được đưa cho một primitive tên `angle_cos_sq` kèm câu *"trả cos²"*, và với
một trong bốn cặp toán hạng thì điều đó sai.

Đây đúng lớp bệnh của cả wave — hợp đồng nói một đằng, kernel làm một nẻo —
chỉ khác chỗ nó nằm sâu hơn tất cả những chỗ đã sửa. Mô hình không sai: nó làm
đúng thứ hợp đồng dạy.

⚠️ `measure_contract.BANG_PHEP_DO["angle_cos_sq"].nghia` hiện ghi *"trả cos²"*
— **câu ấy sai** cho cặp (đường, mặt). Chưa sửa trong wave này: đổi ngữ nghĩa
một phép đo là đổi năng lực hình học, và §20 cấm.

### 2.2 Bảng nghĩa vụ trong prompt quảng cáo từ vựng mô hình KHÔNG viết được

`fp_6` yêu cầu *"chứng minh BD vuông góc với (SAC)"*. Mô hình phát:

```json
{"kind": "perpendicular", ...}
```

ở cả **hai** lượt, rồi hết ngân sách. Nó không bịa: prompt có bảng

| Đề hỏi | `measure.quantity` | Nghĩa vụ | `witness` |
| song song · vuông góc | — | `parallel`·`perpendicular` | đối tượng thứ hai |

Nhưng `SemanticProgramSpec` **không có trường `obligations`**, và
`perpendicular` không nằm trong `ValueExpr`. Nghĩa vụ do `analyze` sinh ra ở
phía hợp đồng, mô hình tổng hợp không có ô nào để viết chúng vào.

Bảng ấy dạy một từ vựng không tồn tại. Đây là **cùng một lớp lỗi** với nhãn
`construct_plane.through` mà wave này vừa sửa, chỉ ở tầng prompt thay vì tầng
thẻ: *nhãn sai của ta đẻ ra lỗi của nó.*

## 3. Giới hạn của phép đo — ba điều phải khai

**① Hợp đồng KHÔNG có `input_facts`.** Probe gọi thẳng
`stage_semantic_program`, bỏ `stage_analyze` để tiết kiệm token, nên
`RequestContract` chỉ mang `problem_text`. Hệ quả: **mọi** `source_fact_id`
mô hình phát đều không giải được. Đường hạ cấp (Wave 3) cứu được ca có kèm
`model_assumption`; ca không kèm thì chết. Sản phẩm thật không như vậy.

**② Phương sai giữa hai lượt LỚN.** Lượt 1 (§0b) và lượt 2 chạy trên **cùng**
đề, cùng prompt, cùng hash — `fp_2` và `fp_4` hỏng grounding ở lượt 1 và
ONE_SHOT_CORRECT ở lượt 2. Hai trong sáu ca lật, ở nhiệt độ 0,1.

⇒ **4/6 KHÔNG phải một con số ổn định.** Với n = 6 và phương sai quan sát được
là 2 ca, khoảng dao động hợp lý ít nhất là 2/6–4/6. Báo cáo này **không**
tuyên bố một tỉ lệ thành công; nó tuyên bố đúng hai điều đếm được:
`PROMPT_BIAS_FAILURES = 0` (bẫy `fp_2` không cắn) và hai bug ở §2.

**③ Không có baseline cùng điều kiện.** Đây là lượt đo **đầu tiên** của
`geometry_program_generator.md` qua harness probe (§0). So với matrix hay
dihedral probe là so hai prompt khác nhau, nên báo cáo không làm phép so đó.
Câu *"one-shot có tăng không"* của §18 **chưa trả lời được**, và nói được là
nói quá.

## 4. Điều wave này đo được, và không đo được

| câu hỏi | trả lời |
|---|---|
| Thiên lệch từ khoá góc còn cắn không? | **Không** — `fp_2` chọn đúng phép đo dù đề có chữ "côsin" |
| Lỗi trung thực có được gửi đi sửa không? | **Không** — `HONESTY_REPAIR_CALLS = 0` |
| Ma sát schema còn không? | **Còn** — 1/6, và nguyên nhân là bảng nghĩa vụ (§2.2) |
| one-shot có tăng so với trước? | **Chưa biết** — không có baseline cùng prompt (§3③) |
| token/success có giảm? | **Chưa biết** — cùng lý do |
