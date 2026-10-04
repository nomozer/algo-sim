# GEOMETRY ARCHITECTURE GAP REPORT — Phase 1

> Đọc mã tại `5b7e921`. **Không sửa mã.** Mọi con số đo cơ học, không ước lượng.
>
> Đề: *"Nghiên cứu và xây dựng hệ thống mô phỏng 3D hình học không gian"*
> (`STATUS_LEDGER §0-2026-08-24`).

---

## ĐÍNH CHÍNH bản audit hôm qua — kéo-thả KHÔNG phá kiến trúc

`THESIS_SCOPE_ALIGNMENT_AUDIT §0` xếp *"kéo để thấy bất biến"* vào loại **phá
song ánh #31** và đẩy ra ngoài phạm vi. **Sai, và sai theo hướng bi quan.**

Luồng ở Phase 3 của kế hoạch không phải khung liên tục:

```
kéo → interaction controller → geometry kernel → NEW VERIFIED STATE → rerender
```

Đó là **đổi tham số đầu vào rồi dựng lại timeline** — đúng hợp đồng đã có ở
`frontend/src/simulations/types.ts:186`:

> *"…rồi `module.apply` tính lại hệ quả. […] mọi biến đổi vẫn đi qua
> `module.apply`."*

Và nó **trùng khuôn `replay_harness.py`**: cùng một chương trình, đổi dữ liệu
đầu vào, chạy lại interpreter. Ràng buộc *"M chỉ chạy trên AB"* là một phép
**chiếu về miền hợp lệ trước khi vào kernel**, không phải một mô hình thực thi
khác.

⇒ **Kéo-thả có ràng buộc NẰM TRONG phạm vi.** Song ánh `frame k ⇔ trace[k]` giữ
nguyên vì timeline được **dựng lại trọn vẹn** sau mỗi lần kéo, không phải bị
chèn thêm khung giữa chừng.

Cái thật sự phá kiến trúc là **kéo mà cập nhật hình theo từng pixel** (mỗi
frame chuột = một khung). Luật rút ra, đủ để làm ràng buộc thiết kế:

> Kéo được phép thay đổi **ĐẦU VÀO**, không được phép thay đổi **TRACE** trực
> tiếp. Sau mỗi lần thả, timeline dựng lại từ đầu bằng kernel tất định.

---

## 1. Semantic IR biểu diễn được gì

Đo trên `MemoryType` (14 giá trị, enum ĐÓNG) và `HANDLED_PRIMITIVES` (9).

| Khái niệm cần | Có? | Ghi chú |
|---|---|---|
| point | ❌ | không có kiểu toạ độ nào |
| line / segment | ❌ | |
| plane | ❌ | |
| polygon | ❌ | |
| solid | ❌ | |
| intersection | ❌ | không có biểu thức hình học |
| distance | ⚠️ **một phần** | `scalar_accumulation` chở được **giá trị**, không chở được **cách tính** |
| angle | ⚠️ một phần | như trên |
| volume | ⚠️ một phần | như trên |

**Kết luận: 0/6 khái niệm cấu trúc, 3/3 khái niệm đại lượng chỉ có vỏ chứa.**

Nhưng **khung IR thì đúng**: `memory_declarations` (đối tượng có định danh) +
`statements` (thao tác theo bước) + `visual_bindings` (ràng buộc thị giác) +
`RequestContract{facts, obligations}` (đề cho gì / phải chứng minh gì) ánh xạ
thẳng sang hình học. Thiếu là **từ vựng**, không phải **ngữ pháp**.

---

## 2. Simulation state hỗ trợ gì

| Yêu cầu | Có? | Ở đâu |
|---|---|---|
| **object identity** | ✅ | `memory_declarations[].name`, `visual_bindings.semantic_id` |
| **coordinate system** | ❌ | không có Oxyz; toạ độ hiện chỉ là **chỉ số mảng** |
| **geometric relation** | ❌ | 11 nghĩa vụ đều rời rạc |
| **transformation** | ❌ | |
| **visibility state** | ❌ | không có khái niệm ẩn/hiện lớp |
| **highlight state** | ✅ | `VisualObject.highlight_indices`, `highlighted_object_ids` |

**2/6.** Hai cái có lại đúng là hai cái khó bỏ (định danh và làm nổi bật);
bốn cái thiếu đều là **thêm mới**, không phải sửa cái sai.

---

## 3. Renderer đang ở đâu

**Chỉ nhận frame, KHÔNG nhận geometry state.**

`VisualFrame` = `{step_index, narration, tier1_fact, objects[], highlighted_object_ids}`
— `objects` là danh sách đã **làm phẳng thành thứ vẽ được** (`items`, `value`,
`highlight_indices`). Renderer **cố ý không được tính lại gì** (`ARCHITECTURE_MAP`:
*renderer 2D/3D chỉ ĐỌC state*).

Với hình học, đây **vừa là điểm mạnh vừa là ràng buộc**:
- **Mạnh**: luật *"renderer không tự tính toán hình học"* trong kế hoạch của bạn
  **đã là bất biến kiến trúc**, không phải thứ phải đi thiết lập.
- **Ràng buộc**: mọi toạ độ 3D phải **có sẵn trong frame**. Kernel tính xong,
  đóng vào frame; Three.js chỉ dựng.

**Hạ tầng 3D thật sự có: đúng 363 dòng** (`encap-ui3d.tsx`, đóng gói giao thức)
+ Three.js đã là dependency + tiền lệ `meaning_of_z` (chiều thứ ba mang nghĩa,
không trang trí). Không có camera orbit, không có nét đứt cạnh khuất, không có
picking đối tượng.

---

## 4. Ba khoảng trống, xếp theo độ khó THẬT

| # | Khoảng trống | Độ khó | Vì sao |
|---|---|---|---|
| 1 | **Geometry kernel** | **CAO** | Đây là chỗ R0 sống hay chết. Không phải "thêm kiểu", mà là **engine phải TỰ TÍNH** giao tuyến/hình chiếu/thể tích. Kèm bẫy dấu phẩy động: so `==` trên float là nguồn sai lặng lẽ kinh điển ở hình học |
| 2 | **Renderer 3D + picking** | **CAO** | 363 dòng hiện có không tái dụng được nhiều; camera orbit, nét đứt cạnh khuất, chọn đối tượng đều là mới |
| 3 | **Từ vựng IR + nghĩa vụ** | **TRUNG BÌNH** | Thêm enum vào tập đóng + checker. Cơ học, có tiền lệ rõ (`12085d5` đã mở taxonomy một lần) |

Điều đáng chú ý: **thứ ai cũng nghĩ là việc chính (thêm point/line/plane) lại
là việc dễ nhất trong ba.**

---

## 5. Điều KHÔNG phải khoảng trống — đừng làm lại

Năm thứ kế hoạch của bạn đặt ra như yêu cầu, mà hệ **đã có và đã có test khoá**:

1. *"Không cho LLM tự quyết toạ độ cuối cùng"* → **ranh giới R0**, khoá bởi
   `execution_authority_gate` + bất biến #1–#3.
2. *"Animation phải có semantic state"* → **bất biến #31**, song ánh
   `frame k ⇔ trace[k]`.
3. *"Renderer không tự tính toán"* → bảng sở hữu `ARCHITECTURE_MAP §3`.
4. *"Narration nói một thứ, hình hiển thị một thứ"* (Phase 4) → **chính là bug
   đã sinh ra bất biến #31**, đã bịt.
5. *"Cùng input = cùng output"* (Phase 2) → interpreter đã tất định; và
   `replay_harness` đã đo được chuyện đó.

⇒ Phase 2/4 phần lớn là **áp lại luật đã có cho miền mới**, không phải dựng mới.
