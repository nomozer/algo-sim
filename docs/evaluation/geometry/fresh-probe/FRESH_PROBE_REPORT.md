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

## 1. Kết quả

*(điền sau khi chạy)*
