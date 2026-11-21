# Source Gate rejection taxonomy (P1)

Nguồn: `evidence/slm20/slm20_audit_baseline.json`. Đây là 20 ca SLM thất bại ở /10 cộng 4 ca đối chứng (V13, V18, C24,
C20), chạy lại trên mã /10 (`2f12b96b0`) với GGUF AxoV9 thật qua runtime sản phẩm. Mỗi ca chạy 5 nhánh:
A sản phẩm · B payload SLM → hạ tầng · D dữ kiện SLM + ý định gold · C dữ kiện parser + ý định gold · E đề diễn đạt
lại chuẩn tắc. Mỗi mã từ chối dưới đây được truy về **mệnh đề nguồn** làm nó bật ra, không dừng ở tên mã.

## Mã quan sát ở nhánh A (sản phẩm, /10)

| mã | số ca | ca | cơ chế thật (truy tới mệnh đề) | lớp sai | xử lý ở /11 |
|---|---|---|---|---|---|
| `SOURCE_OBJECT_MISMATCH` | 9 | V06 V08 V11 V14 V16 V26 V28 Q10 (+V13 ở B) | (a) GBNF buộc ≥ 1 mục tiêu số hoặc `u`, nên mô hình phải bịa `goal:vol`/`dist`; mục tiêu bịa trỏ vào mệnh đề khai báo ⇒ đối tượng trích dẫn ≠ đối tượng mục tiêu. (b) Q10: tiền đề góc vuông trích nhầm mệnh đề "SA vuông góc với (ABC)" thay vì "vuông tại A" | văn phạm SLM + lowering | nhánh văn phạm chỉ-mô-phỏng (`g:[]`), `construct_object` trích **mệnh đề yêu cầu**, cue góc vuông `vuông (tại\|ở) <đỉnh>` (`fcf68e91b`) |
| `AMBIGUOUS_FACT` (grounding rejected) | 5 | V02 V09 V10 V19 C25 | lối thoát hợp lệ duy nhất của văn phạm cũ cho đề không hỏi gì là `u:[ambig]` (V02, V19) hoặc mục tiêu `lratio` bị từ chối `UNGROUNDED_GOAL_CLAUSE_TOKENS` (V09, V10). C25 là lỗi mô hình thật | văn phạm SLM (4) · mô hình (1) | văn phạm chỉ-mô-phỏng; `SIM_ONLY_UNRESOLVED_WITHOUT_FACTS` chỉ cho `u` khi `r:[]` |
| `UNGROUNDED_VALUE` | 2 | V05 C03 | mô hình đọc đúng `len(S.ABCD)=a` ("tất cả các cạnh bằng a"); lowering chỉ hạ `SA = a`, rồi Source Gate không đọc cụm "tất cả các cạnh (đều) bằng" | lowering + văn phạm Source Gate | **mở** — luật Source Gate khoá; handoff |
| `QUESTION_CONTEXT_UNSUPPORTED` | 2 | Q03 Q08 | mục tiêu đúng; Source Gate không nhận "mô phỏng hình lập phương và tính …" / "vẽ hình hộp và tính …" vì danh từ khối không nằm trong văn phạm yêu cầu | văn phạm Source Gate | `_VAT_MO_PHONG` hẹp (owner duyệt, `806a7d338`) |
| `NOT_ASKED_IN_SOURCE` | 1 | Q04 | "biểu diễn góc giữa …" không phải động từ hỏi trong văn phạm câu hỏi | hợp đồng câu hỏi | **mở** — quyết định hợp đồng của owner |
| `AMBIGUOUS_VALUE_QUOTE` | 1 | Q05 | trích dẫn mục tiêu lấy nhầm mệnh đề dữ kiện; thêm vào đó "biểu diễn khoảng cách" không phải câu hỏi | lowering + hợp đồng câu hỏi | **mở** (hai lớp) |
| `SOURCE_PREMISE_UNREAD` | 1 | C26 | tiêu đề đề thi "Câu 2 (2 điểm)." không được Source Gate đọc | văn phạm Source Gate | **mở** — handoff |
| `gate_out_of_scope` | 2 | V18 C24 | đề gõ không dấu; `detect_domain` khớp cụm có dấu nên trả `tin_hoc` trước mọi parser/SLM | cổng miền | **mở** — `handoff/domain_gate_diacritic_free.patch` (chỉ patch, owner) |
| `MISSING_DIMENSION` | 1 | C20 | đề thật sự thiếu một kích thước; từ chối **đúng** (đối chứng) | — | giữ |

## Nhánh nào chứng minh điều gì

- **E 24/24 SERVED, 24/24 hợp lệ theo oracle**: phần hạ tầng (planner/engine/kernel/adapter) dựng được mọi cảnh khi
  ngôn ngữ đầu vào nằm trong văn phạm. Nút thắt nằm **trước** planner.
- **B = A** ở mọi ca có payload: lỗi không do định tuyến mà do payload SLM gặp Source Gate.
- **D chuyển lỗi**: với 7 ca SIMULATE_ONLY, bỏ mục tiêu bịa thì lỗi đầu tiên đổi từ `SOURCE_OBJECT_MISMATCH` sang
  `SOURCE_PREMISE_UNREAD`, tức Source Gate không đọc câu lệnh. Hai nguyên nhân chồng lên nhau, và phải sửa cả hai.

## Không làm

Không nới Source Gate toàn cục. Không thêm cụm theo ca. Không cho mục tiêu số không có trong đề. Các luật còn mở ở trên
đều chạm văn phạm câu hỏi hoặc tiền đề của Source Gate, nằm ngoài quyền hẹp owner đã cấp, và có mô tả bàn giao trong
`OWNER_HANDOFF.md`.
