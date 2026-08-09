# W4B-2V/C — Thí nghiệm là CÔNG CỤ, không phải tấm nội dung thứ hai

`THESIS_SCOPE = T3`. Baseline `d0c15ce`. Bản audit BEFORE (`fe6b0d5`) **không sửa**.

## 1. Đo được — không phải "trông gọn hơn"

Chiều cao mà việc **mở Thí nghiệm** thêm vào khối mô phỏng, và số **khối chữ dài**
(≥60 ký tự) học sinh đọc khi cổng mở:

| target | +px TRƯỚC | +px SAU | giảm | khối chữ TRƯỚC → SAU |
|---|---|---|---|---|
| `linear_search` | +186 | **+105** | −81 (43%) | 2 → **1** |
| `binary_search` | +186 | **+105** | −81 (43%) | 2 → **1** |
| `insertion_sort` | +155 | **+94** | −61 (39%) | 1 → **0** |
| `count_if` | +122 | **+61** | −61 (50%) | 1 → **0** |

Phần còn lại (+61…+105px) **chính là công cụ**: nút hành động + phản hồi + lối
đóng. Đó là thứ Thí nghiệm tồn tại để thêm.

> Lượt đo đầu suýt cho số sai: selector `.workspace-main, .app-single, main` trả
> **927px bất động** ở cả bốn target — nó bắt trúng container cao bằng khung
> nhìn. Một con số không đổi trông y hệt một kết quả tốt. Phép đo nay lấy **cha
> trực tiếp của `.sim-stage`**, tức khối thật sự co giãn.

## 2. Đã đổi gì

| | trước | sau |
|---|---|---|
| khung Thí nghiệm | thẻ `.notes` (nền + padding) mang đoạn **135–310 ký tự** | khay **một dòng** `.experiment-tray`: câu hỏi hành động + lối đóng |
| `framing` | đoạn giảng | **câu hỏi hành động** < 60 ký tự ("Em chọn nửa để tìm tiếp.") |
| nghĩa what-if | nằm trong `framing` | chuyển sang **`hint`** — chuỗi render ngay cạnh chính công cụ kéo |
| lời nhắc trong zone | luôn in ("Em hãy quyết định bước tiếp theo.") | `showPrompt={!gated}` — bài gác cổng để **khay** hỏi, bài chưa gác giữ nguyên |
| nhãn nút đóng | "Đóng thí nghiệm" | "Đóng" + `aria-label="Đóng thí nghiệm"` |

## 3. Ràng buộc KHÔNG được đánh đổi — và cách nó được giữ

Cắt `framing` xuống một câu suýt xoá mất phân biệt **cam kết ↔ what-if**, thứ
W4B-2D §7 bắt buộc ("không được trình bày kéo như bước tiếp theo của thuật
toán"). Ý đó **không bị xoá** — nó chuyển sang `hint`:

- `linear_search`: *"Kéo = thí nghiệm, không phải bước thuật toán: dời đích, xem chi phí đổi."*
- `binary_search`: *"Kéo = thí nghiệm: phá thứ tự đã sắp, xem còn tìm đúng không."*
- `find_max`/`find_min`: giữ nguyên câu "vùng đã duyệt".

Bốn test cũ khoá ý này vào **đúng một trường và đúng một từ** nên chúng đỏ dù
học sinh vẫn đọc được. Đã đổi sang khẳng định trên **cặp `framing ∪ hint`** —
thứ học sinh thấy khi công cụ mở. Vẫn chặt: bỏ hẳn khái niệm thì vẫn đỏ.

## 4. Bất biến mới + tiêm lỗi

`simulations/experiment-tool-mode.test.tsx` —
`EXPERIMENT_IS_A_TOOL_NOT_A_CONTENT_PANEL`: `framing` < 60 ký tự cho mọi bài gác
cổng · khay không được dựng bằng `.notes` · Quan sát nhiều nhất **một** khối chữ
dài · teaser và nhãn nút **phải còn** (đối trọng: gọn không có nghĩa là câm, nút
bí ẩn là lỗi PhET/CLT đã bắt ở W4B-2B).

| Lỗi tiêm | Kết quả |
|---|---|
| `framing` phình lại thành đoạn giảng | **ĐỎ** |
| khay quay lại dùng `.notes` | **ĐỎ** |
| khôi phục | **XANH** |

`CORE_OBSERVATION_STATE_PRESERVED_UNDER_GATING` giữ **xanh** — không probe cơ chế
lõi nào bị mất; đây là điều kiện §16 và nó chặn đúng cám dỗ "gọn bằng cách giấu".

## 5. Cổng

`vitest 1052/69` · `pytest 1135 passed, 2 skipped` · build sạch ·
browser **72/72 PASS** cả BEFORE lẫn AFTER, `canonical_stable_across_ui_modes`
đúng ở cả bốn target · responsive `1366×768 · 1920×1080 · 768×900` PASS.

Runner cũng phải sửa một lần: nó bấm nút đóng theo chữ `"Đóng thí nghiệm"`, mà
nhãn hiện rút còn `"Đóng"` ⇒ bốn lượt báo FAIL *"đóng cổng ⇒ vùng cam kết biến
mất"*. **Runner hết hạn, không phải sản phẩm hỏng** — nay bấm theo `aria-label`,
danh tính bền hơn chữ hiện.

## 6. Không đụng tới

`generic.rule_scene` (THESIS_LIMITATION) · `packet_routing` destination ·
`sum_if` accumulator · `algorithm.scan` · `bounded_control_flow` ·
`base_conversion` · tree rule · database predicate · rollout họ Sort · chồng lấp
vỏ ở 768×900 (khay gọn hơn có thể làm nhẹ, **chưa đo nên không claim**).

Không tuyên bố gì về tải nhận thức hay kết quả học tập:
`LEARNER_IMPACT_NOT_EVALUATED`, `CURRICULUM_SUPPORT_PARTIAL`.
