# Underdetermined simulation semantics (P4)

## Vấn đề

"Vẽ hình lập phương ABCD.A'B'C'D'." không cho cạnh. Về **hình dạng**, hình được xác định duy nhất sai khác một phép đồng
dạng: mọi lập phương đều như nhau ở mọi thứ có thể vẽ. Chỉ **số đo** là chưa xác định. Một đề chỉ xin dựng hình thì không
hỏi số đo nào, nên hệ không cần chứng chỉ bất biến cho một đại lượng được hỏi vì không có đại lượng nào được hỏi.

## Hành vi đo được (lượt mù, `V11_UNDERDETERMINED_RESULTS.json`, văn bản người học từ I05)

| ca | đề | phản hồi | người học đọc | so với tiêu chí đăng ký |
|---|---|---|---|---|
| D01 | chóp S.ABCD đáy vuông, SA ⊥ đáy, không số đo | `AMBIGUOUS_FACT` + câu hỏi làm rõ | "Đề bài cần thêm dữ kiện… bạn hãy nói rõ các số đo cần thiết" | CLARIFY ✓ |
| D02 | lập phương, không cạnh | `MISSING_DIMENSION`, `capability_gap`, **không** câu hỏi | "**Axo chưa hỗ trợ phép dựng này** / … chưa có chứng chỉ bất biến tổng quát cho **đại lượng được hỏi**" | ✗ (thông điệp "chưa hỗ trợ") |
| D03 | tứ diện đều, không cạnh | như D02 | như D02 | ✗ |
| D04 | lăng trụ đứng đáy tam giác đều, không số đo | `AMBIGUOUS_FACT` + câu hỏi | câu hỏi làm rõ | CLARIFY ✓ |
| D05 | chóp đáy vuông tại B, SA ⊥ (ABC), không số đo | `MISSING_DIMENSION`, `insufficient_specification` | "Đề bài chưa đủ dữ kiện để dựng hình / … Em hãy kiểm tra và bổ sung số đo" | CLARIFY ✓ |

Kết quả 3/5 CLARIFY, 0/5 ILLUSTRATIVE, 2/5 vi phạm. Không ca nào bịa số đo, và không ca nào trình cảnh như là duy nhất.

## Nguyên nhân gốc của D02/D03

Engine hoặc planner (đang khoá) đi qua nhánh "hình chưa cố định duy nhất ⇒ cần chứng chỉ bất biến cho đại lượng được
hỏi" ngay cả khi `simulation_goals` chỉ có `construct_object` và `math_goals = []`. Envelope ra `failure_category =
capability_gap`, `refusal_cause = UNKNOWN`. Frontend thì đúng luật HFOI-F6: chỉ mời bổ sung dữ kiện khi backend chứng nhận
`refusal_cause = SOURCE`, nên nó hiện nhãn "chưa hỗ trợ". **Sửa đúng chỗ là backend, không phải đè ở frontend.** Đè ở
frontend sẽ phá luật HFOI-F6 và gắn nhãn sai cho các capability gap thật.

## Thiết kế đề xuất (bàn giao; planner/engine/kernel khoá theo owner)

1. **Phân loại tất định trước planner**: `determinacy = UNIQUE | UNIQUE_UP_TO_SIMILARITY | UNDERDETERMINED_SHAPE`, tính từ
   FactGraph (đếm bậc tự do hình dạng sau khi đã trừ phép đồng dạng).
2. `math_goals = []` và `UNIQUE_UP_TO_SIMILARITY` (D02, D03): dựng với **một đơn vị tượng trưng** `a`, gắn
   `illustrative_scale = true`, và hiện một dòng công khai "Đề không cho số đo; hình vẽ theo đơn vị tượng trưng a." Mọi
   chứng chỉ quan hệ (vuông góc, song song, đều) vẫn kiểm chính xác như cũ. Không có đáp số nên không có gì để bịa.
3. `UNDERDETERMINED_SHAPE` (D01, D04, D05: tỉ lệ các cạnh thật sự tự do) ⇒ giữ CLARIFY có câu hỏi như hiện nay. Không
   minh hoạ, vì hình minh hoạ sẽ trông như khẳng định một tỉ lệ mà đề không cho.
4. Có `math_goals` và không duy nhất ⇒ giữ nguyên `MISSING_DIMENSION` hiện hành (đúng: không kết luận từ hình mẫu).

Ràng buộc: R0 không đổi (LLM không phán toạ độ); đơn vị tượng trưng là quy ước hiển thị đã công khai, không phải dữ kiện;
`CACHE_VERSION` phải bump khi (2) được triển khai (envelope phục vụ đổi).

## Vì sao không prototype trong /11

Owner khoá planner/engine/kernel và cho phép "prototype cô lập + handoff". Phần (1) cần FactGraph và đếm bậc tự do bên
trong planner. Một prototype đặt ngoài planner sẽ phải nhân bản logic đó, trái luật "một thẩm quyền". Hồ sơ này dừng ở
thiết kế cùng 5 ca đo được làm tiêu chí nghiệm thu cho wave sở hữu planner.
