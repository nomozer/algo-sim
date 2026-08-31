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

**Rửa năng lực — đáp số đúng cho một khái niệm runtime không có.**

`gm_10` hỏi bán kính mặt cầu ngoại tiếp; runtime không biểu diễn mặt cầu. Mô
hình khai `P_opposite = [2,2,2]` kèm `model_assumption` *"điểm đối diện trong
hình hộp bao quanh"*, lấy `midpoint(A, P_opposite)` làm tâm rồi `distance` ra
`√3` — **đúng**. Nó tự giải trong đầu rồi giấu định lý vào toạ độ một điểm nó
bịa ra, và trường `model_assumption` hợp thức hoá điều đó.

`gm_03` mang cùng bệnh với `P_parallel`, và phát hiện ấy đến từ lượt soát lại
chứ không từ lượt chấm — tức lượt chấm không có công cụ để thấy nó.

Cả hai ca **đã** được xếp GROUNDING fail lúc chạy, nên điểm không đổi. Nhưng
chúng chết vì **thiếu `source_fact_id`**, tức chết tình cờ: đổi một chi tiết
không liên quan là chúng qua, và một chương trình có `√3` đúng sẽ được ghi là
thành công. Fail-closed do may không phải fail-closed.

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

`semantic_program/source_entities.py` + hai chốt mới trong `grounding_gate` —
cổng trung thực năng lực, chặn ở tầng **grounding**, trước thực thi:

| mã | chặn cái gì |
|---|---|
| `UNANCHORED_DERIVED_ASSUMPTION` | thực thể **tự bịa** (`P_opposite`, `P_parallel`) khai bằng toạ độ thô kèm nhãn giả thiết |
| `DERIVED_ENTITY_WITHOUT_PRODUCER` | thực thể đề **có nêu nhưng là hệ quả** (*"Gọi H là hình chiếu…"*) khai bằng toạ độ thay vì dựng |

Ranh giới giữ đúng chỗ khó: chọn hệ trục cho các đỉnh đề cho — `A=(0,0,0)`,
`B=(2,0,0)` — vẫn là mô hình hoá hợp lệ và vẫn qua. Cấm nó là giết mọi bài.

Thay thế trên `gm_10` và `gm_03`: vẫn CHẶN, nhưng nay chặn **đúng lý do** và
nêu được phép dựng còn thiếu. `tests/semantic_program/test_capability_honesty.py`
khoá cả hai chiều — 43 ca, gồm replay `gm_10` thật, tám tên thay thế
(`X`/`H`/`O`/`T1`/`helper_7`…) để guard không bám vào chuỗi `P_opposite`, và
chứng cứ dương cho tứ diện · lăng trụ · trung điểm · hình chiếu · giao điểm.

**Giới hạn còn lại, khai thẳng:** `nhan_suy_ra` khớp mẫu chữ tiếng Việt
(*"Gọi … là"*, *"… là trung điểm"*), không phân tích cú pháp. Đề định nghĩa
điểm phụ bằng lối viết ngoài các mẫu ấy vẫn lọt.
