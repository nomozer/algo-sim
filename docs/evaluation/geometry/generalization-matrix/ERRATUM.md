# ERRATUM — GENERALIZATION MATRIX

> Ghi thêm, **không sửa** số đo. `matrix.json`, prompt hash, frozen commit và
> mọi điểm số giữ nguyên như lúc chạy.

## Phát hiện sau khi matrix đóng

**Bug serialize sản phẩm, lộ ra SAU khi thực thi tất định đã thành công.**

`visual_adapter` đặt thẳng giá trị bộ nhớ vào `value_box.value` — `Vec3` với
biến hình học, `Fraction`/`Radical` với số đo. Cả ba không `json.dumps` được,
mà `main.py` serialize envelope để **ghi cache**, tức sau khi mọi cổng đã báo
PASS. Học sinh đợi hết một lượt pipeline rồi nhận HTTP 500 không có địa chỉ.

Ba chương trình dùng cho spot check §19 đều qua `check_learner_surface`, nên
không tầng nào chặn trước. Prompt lại dạy mô hình gắn `visual_bindings` cho
witness của mỗi nghĩa vụ, nên một chương trình hình học **đúng** gần như chắc
chắn rơi vào đây.

## Điều erratum này KHÔNG làm

- Không đổi `matrix.json`.
- Không biến phân tích offline thành thành công live.
- Không chạy lại model.

Con số của matrix vẫn là: **3/9 đúng trong ngân sách live**, 7/9 chương trình
đúng khi phân tích lại offline (chênh lệch do bộ đo bỏ tầng `analyze`, xem
`matrix-offline-reanalysis.json`).

## Đã sửa ở wave sau

`semantic_program/transport.py` — một thẩm quyền serialize duy nhất, cộng một
cổng `check_envelope_transport` chạy **trước** cổng bề mặt học sinh. Envelope
của cả ba chương trình spot check nay serialize được mà không cần vá bộ đo.
Xem `tests/semantic_program/test_transport_boundary.py`.
