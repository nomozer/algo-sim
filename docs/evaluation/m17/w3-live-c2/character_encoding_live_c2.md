# M17 W3-LIVE-C2 — rerun live sau khi bổ sung luật phát cho họ positional

**Kết luận: `W3_LIVE_PARTIAL` — ĐÓNG.** Hard stop một-vòng đã áp dụng: không sửa
thêm `analyze.md`, không đổi test, không chạy lại, **không mở C3**.

**Khiếm khuyết được nhắm tới đã ĐÓNG:** `mechanism_gate_failure` **5 → 2 → 0**.

| | baseline `w3-live` | `w3-live-c1` | **`w3-live-c2`** |
|---|---|---|---|
| PASS | 7/12 | 9/12 | **8/12** |
| FAIL_SAFE | 5 | 3 | **4** |
| `mechanism_gate_failure` | 5 | 2 | **0** |
| `prescribed_mechanism_error` | — | — | **0** |
| `classification_error` | — | — | **0** |
| `spec_synthesis_error` | — | — | **0** |
| Mọi trục an toàn | 0 | 0 | **0** |
| HTTP | 27/45 | 29/45 | **28/45** (0 transient · 0 retry) |

Số PASS giảm 1 so với C1 **không phải hồi quy của bản sửa**: lượt PASS đó của
ENC-1 ở C1 đến từ một lần analyze may mắn phơi đủ dữ kiện, không phải từ cơ chế.
Chỉ số đo đúng mục tiêu C2 là `mechanism_gate_failure`, và nó về **0**.

## Cấu hình

`gemini-2.5-flash` · google-gemini ·
`…/v1beta/models/gemini-2.5-flash:generateContent` · analyze `0.1` · classify
`0.0` · simulate `0.1` · transport `max_attempts=2` · simulate validation-retry 3.
Prompt/provider/model/sampling/số lượt: **y hệt** baseline và C1.

**Runtime: IN-PROCESS** tại `b0ecb19` · `cache=25 · family=11 · target=22 ·
hash=4d7c8e65e1fa`. Container Docker vẫn **STALE** (`cache=22 · family=10 ·
target=20`) — **không được dùng**, không trộn request. 12/12 lượt cùng một runtime.

## Bản sửa đã có tác dụng đúng chỗ

`prescribed_procedure = positional_representation.character_code_mapping` ở
**6/6** lượt của ENC-1/ENC-2/ENC-3 — kể cả ENC-3, nơi trước đây analyze phát
`binary_positional_weights`. Cổng cơ chế **không còn chặn lượt nào**.

| Case | L1 | L2 | `prescribed` | Cổng chặn (nếu có) |
|---|---|---|---|---|
| ENC-1 | FAIL_SAFE | FAIL_SAFE | `character_code_mapping` 2/2 | `input_sufficiency` |
| ENC-2 | **PASS** | **PASS** | `character_code_mapping` 2/2 | — |
| ENC-3 | FAIL_SAFE | FAIL_SAFE | `character_code_mapping` 2/2 | `completeness_requested` · `input_sufficiency` |
| ENC-4 | **PASS** | **PASS** | → `binary.decimal_to_binary` | — |
| ENC-5 | **PASS** | **PASS** | — | từ chối an toàn |
| ENC-6 | **PASS** | **PASS** | — | từ chối an toàn |

Candidate được chấp nhận: `{"spec_version":"charenc-1.0","text":"Tin","encoding":"ascii"}`
(2/2), code point `U+0054 U+0069 U+006E` — giữ đúng hoa/thường, không bỏ ký tự,
không rò kết quả.

## Bốn lượt chưa PASS — đều AN TOÀN, và ở cổng KHÁC

Thất bại đã **dịch xuống hạ nguồn**, không còn ở cổng cơ chế:

- **ENC-1 (2/2) và ENC-3 run2 — cổng đủ dữ kiện** (`insufficient_specification` /
  `input_insufficient`). Định tuyến và cơ chế đều đúng, nhưng analyze không phơi
  được bằng chứng `objects.quoted_characters` / `constraints.encoding_name` mà
  `input_requirements` của target đòi. Hệ **hỏi lại học sinh** thay vì tự chọn ký
  tự — hành vi đúng, chỉ là chưa ổn định.
- **ENC-3 run1 — cổng đủ ngữ nghĩa** (`semantic_incomplete` /
  `multiple_operations_not_supported`). analyze tách đề thành **hai việc** ("đổi
  số thập phân sang nhị phân" + "tra mã ký tự rồi đổi sang nhị phân") nên cổng
  báo mỗi lần chỉ trình bày được một. Đây là **dương tính giả** ở kênh
  `requested_operations`: đề thật sự chỉ yêu cầu MỘT quy trình mà target sở hữu
  trọn vẹn.

Cả hai đều **không** nằm trong phạm vi C2 (chỉ sửa luật phát cơ chế), và hard stop
cấm mở vòng sửa thứ hai.

## Hệ quả phải nêu thẳng

**`U+1EBF` VẪN chưa đo được ở đường live.** ENC-3 không cho candidate nào được
chấp nhận ⇒ theo §15, **E2E-ENC-2 KHÔNG chạy**: không dựng config bằng tay, không
lấy candidate từ C1, không sửa adapter. **0 ảnh** trong checkpoint này.

Bằng chứng E2E Unicode do đó vẫn là **NOT MEASURED**; bằng chứng E2E ASCII của
C1 (`E2E-ENC-1`, hash khớp) vẫn nguyên giá trị và không bị đụng tới.

## Sư phạm

Không đánh giá tác động học tập. Learner task của W3 giữ nguyên: điều khiển
timeline, quan sát ký tự → code point → chuỗi chia lấy dư → dãy bit.
Interaction: **`TIMELINE_CONTROL`**, **không nâng**. `learner impact =
NOT_EVALUATED`. Vì E2E Unicode không chạy nên **không** phát biểu
`PEDAGOGICAL_ALIGNMENT_EVIDENCED_FOR_REPRESENTATIVE_UNICODE_CASE`.

## Phạm vi

6 case × 2 lượt là **smoke**, không phải benchmark trên mọi đề tiếng Việt.
