# M17 W3-LIVE-C1 §14 — bằng chứng phù hợp sư phạm (KHÔNG phải tác động học tập)

**Trạng thái: `PEDAGOGICAL_ALIGNMENT_EVIDENCED` cho case W3 đại diện.**
**`learner impact = NOT EVALUATED`.**

> Tài liệu này **không** tuyên bố mô phỏng cải thiện kết quả học tập. Nó chỉ ghi
> rằng affordance quan sát được **khớp** với mục tiêu chương trình. Tác động thật
> chỉ đánh giá được ở một checkpoint pilot có giáo viên và học sinh.

## Bảng affordance — E2E-ENC-1

| Trục | Nội dung |
|---|---|
| **Curriculum objective** | Giải thích mối liên hệ giữa ký tự, mã số và biểu diễn nhị phân; mô tả cơ chế chia lấy dư. Neo: `T10 B3 · T10 B6 (mã hoá văn bản)` |
| **Learner task** | Điều khiển timeline qua 13 bước; quan sát từng phép chia; giải thích cách dãy số dư tạo thành kết quả |
| **Observable state** | ký tự `A` · code point `65` · dividend `65` · quotient `32` · remainder `1` · `collected: ["1"]` · dãy bit `1000001` |
| **Causal transition** | mỗi bước `divide_step` là MỘT chuyển trạng thái thật: `value → quotient` kèm `remainder` được thu vào dãy; kết quả **dẫn ra từ** chuỗi số dư, không phải công bố sẵn |
| **Learner control** | Previous · Next · Reset (shell `SimulationControls` hiện theo capability `timeline` của module) |
| **Deterministic feedback** | state và thuyết minh do engine tất định sinh — *"65 : 2 = 32 dư 1 → chữ số 1. Các số dư đọc NGƯỢC từ dưới lên sẽ thành kết quả."* LLM không sinh bước nào |
| **Evidence source** | `representative_e2e_handoff.json` (engine state + DOM + hash) · `visual/E2E-ENC-1-*.png` (3 ảnh) |
| **Limitation** | quan sát trên MỘT case, MỘT viewport; chưa có người học thật |

**Interaction level: `TIMELINE_CONTROL`.** Đúng như khai báo — W3 chưa có
prediction/what-if, và checkpoint này **không** thêm.

## Vì sao alignment, chứ chưa phải impact

Bằng chứng hiện có chứng minh được ba điều:

1. cơ chế ẩn (chia lấy dư) **được phơi bày từng bước**, không bị rút gọn thành
   một tuyên bố;
2. mọi bước là **hệ quả tất định** của engine, người học có thể tua tới lui để
   đối chiếu nguyên nhân — kết quả;
3. thứ hiển thị **đúng** với thứ engine sở hữu (DOM ↔ state đã đối chiếu).

Nó **không** chứng minh: học sinh hiểu hơn, nhớ lâu hơn, hay làm bài tốt hơn.
Muốn kết luận đó cần thiết kế thực nghiệm có nhóm đối chứng — nằm ngoài phạm vi
mọi checkpoint kỹ thuật.

## Không nâng interaction hàng loạt (§15)

Không sửa mức tương tác của W3 hay bất kỳ target nào khác. Lý do: mức tương tác
phải theo mục tiêu học tập, hệ đã có đủ ba mức (`TIMELINE_CONTROL`,
`MECHANISM_ACTION`, `PREDICTION_OR_WHAT_IF`), và **chưa có dữ liệu người học**
cho thấy module nào cần mức mạnh hơn. Chỉ đề xuất chỉnh sau pilot nếu quan sát
được: học sinh không nắm cơ chế nếu chỉ có timeline; không hoàn thành được
learner task; hoặc giáo viên xác nhận affordance hiện tại chưa đủ.
