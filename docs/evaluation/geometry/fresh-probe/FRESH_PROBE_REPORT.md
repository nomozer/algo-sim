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

*(điền sau khi chạy)*
