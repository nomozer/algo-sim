# M17 W3-LIVE — `binary.character_encoding` live natural-language integration smoke

**Kết luận: `W3_LIVE_PARTIAL`.** 7/12 lượt PASS · 5/12 **thất bại AN TOÀN** ·
**0 chấp nhận sai** trên mọi trục an toàn.

| | |
|---|---|
| Baseline | `472314e` (tree sạch trước và sau) |
| Provider / model | google-gemini · `gemini-2.5-flash` |
| Endpoint | `https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent` |
| Sampling | analyze `0.1` · classify `0.0` · simulate `0.1`; transport `max_attempts=2` (đúng 1 retry) |
| Runtime | **IN-PROCESS** · `cache=23 · family=11 · target=22 · hash=4d7c8e65e1fa` |
| Ngân sách | **27 / 45 HTTP** · 0 transient · 0 retry |
| Case | 6 case × 2 lượt độc lập = 12 |

> Phạm vi: đây là **smoke 6 case × 2 lượt**, KHÔNG phải benchmark độ chính xác
> trên mọi đề tiếng Việt. Không nói gì về hiệu quả học tập.

## 1. Kết quả từng case

| Case | Lượt 1 | Lượt 2 | Định tuyến (raw classify) | Ghi chú |
|---|---|---|---|---|
| LIVE-ENC-1 ASCII một ký tự | FAIL_SAFE | FAIL_SAFE | `binary.character_encoding` 2/2 | chặn ở cổng cơ chế |
| LIVE-ENC-2 ASCII chuỗi | FAIL_SAFE | **PASS** | `binary.character_encoding` 2/2 | lượt 2 ra `text="Tin"` đúng |
| LIVE-ENC-3 Unicode BMP | FAIL_SAFE | FAIL_SAFE | `binary.character_encoding` 2/2 | chặn ở cổng cơ chế |
| LIVE-ENC-4 ranh giới với SỐ | **PASS** | **PASS** | `binary.decimal_to_binary` 2/2 | KHÔNG nhầm sang mã hoá ký tự |
| LIVE-ENC-5 thiếu dữ kiện | **PASS** | **PASS** | — | từ chối an toàn, không bịa |
| LIVE-ENC-6 emoji ngoài BMP | **PASS** | **PASS** | — | từ chối đúng phạm vi |

**Semantic fidelity (§6) — toàn số 0 ở mọi trục an toàn:**

| Chỉ số | Giá trị |
|---|---|
| `semantic_loss` | **0** |
| `fabricated_input` | **0** |
| `result_leakage` | **0** |
| `generic_leak` | **0** |
| `unsafe_acceptance` | **0** |
| `wrong_target_acceptance` | **0** |
| `safe_failure` | 5 |

Lượt thành công (ENC-2 run2) cho candidate đúng hợp đồng nhỏ nhất và **không mang
kết quả**: raw `{"text":"Tin","encoding":"ascii","notes":null,"spec_version":"charenc-1.0"}`
→ validated `{"spec_version":"charenc-1.0","text":"Tin","encoding":"ascii"}`.

## 2. Phát hiện chính — cơ chế bị chặn bởi cổng ownership

**Phân loại LLM đúng 6/6** trên ba case được hỗ trợ: `classify` chọn
`binary.character_encoding` mọi lượt. Việc từ chối xảy ra **SAU classify**, ở
cổng cơ chế, với mã CÓ CẤU TRÚC:

```
failure_category = capability_gap
error_code       = gate_mechanism_ownership
gates_fired      = [{"gate":"mechanism","fired":true,
                     "reason_code":"gate_mechanism_ownership"}]
```

Bằng chứng cấu trúc (không suy từ thông điệp học sinh):

- `mechanism_gate.check_mechanism_consistency_for_target` đòi
  `prescribed ∈ owned(target, family)` — một phép thử **thành viên đơn**.
- `binary.character_encoding` khai sở hữu **đúng một** cơ chế:
  `positional_representation.character_code_mapping` (`catalog.py:1226`), cố ý
  KHÔNG giành `non_binary_base` — comment tại chỗ nói rõ điều đó.
- Nhưng chính taxonomy ghi năng lực này là một **CHUỖI**:
  `character_code_mapping → non_binary_base` (`mechanisms.py:26–30`), và
  `non_binary_base` thuộc `binary.base_conversion` (`catalog.py:559–562`).
- Đề bài nêu thẳng mắt xích thứ hai ("chuyển mã đó sang nhị phân"), nên analyze
  đặt `prescribed_procedure` vào mắt xích đó → không nằm trong `owned` của
  target → `capability_gap`.

Cổng **không có khái niệm chuỗi cơ chế**; nó chỉ kiểm sở hữu đơn trên final
route. Đây là va chạm giữa một quyết định kiến trúc có chủ đích (không giành
quyền sở hữu bước đổi cơ số) và một cổng chỉ biết kiểm sở hữu đơn.

Lượt PASS duy nhất rơi vào nhánh permissive của cổng (`prescribed` là
`null`/`none` → không ép cơ chế). Cùng một prompt, hai lượt cho hai
`prescribed_procedure` khác nhau ⇒ **MODEL_VARIABILITY** trên đúng một trường.

**Hệ quả cần nêu thẳng:** ở baseline này, `binary.character_encoding` gần như
**không tiếp cận được end-to-end bằng ngôn ngữ tự nhiên** — dù offline đã
VERIFIED, visual đã REAL_VISUAL và authenticity đã REAL_SIMULATION.

### Root cause (§9)

| Case | Root cause |
|---|---|
| ENC-1 (×2), ENC-2 run1, ENC-3 (×2) | `MODEL_VARIABILITY` là **tác nhân kích hoạt**; nguyên nhân tất định là **cổng ownership không mô hình hoá chuỗi cơ chế** |

Danh sách đóng ở §9 **không có nhãn đúng** cho nguyên nhân tất định này: đây
không phải `CLASSIFICATION_ERROR` (classify đúng 6/6), không phải
`SPEC_SYNTHESIS_ERROR` hay `VALIDATOR_ERROR` (simulate và validator **chưa bao
giờ chạy** ở 5 lượt đó). Ghi lại như một thiếu sót của chính taxonomy root-cause.

## 3. Đính chính phép đo của harness (không phải kết quả sản phẩm)

Lượt chấm ĐẦU TIÊN báo `W3_LIVE_FAILED` — **sai, do lỗi của harness**, đã sửa và
chấm lại:

- bộ khoá "rò kết quả" của `character_encoding` bị áp cho **mọi route**, nên
  `decimalValue` — **input hợp lệ** của `binary.decimal_to_binary` — bị chấm là
  rò kết quả ⇒ LIVE-ENC-4 FAIL oan ⇒ lật phân loại tổng thể sang FAILED;
- đã tách hợp đồng rò-kết-quả **theo target** và chấm lại trên **chính dữ liệu
  live đã thu**: `--rescore`, **0 API call mới**, không lượt chạy nào bị lặp lại;
- mọi trường live (prompt / raw / validated / http / timestamp) giữ **nguyên văn**;
  provenance nằm ở khối `rescore` trong file JSON.

`FAIL → PASS` của ENC-4 là sửa **phép đo**, không phải nới tiêu chí: route của
ENC-4 vốn đã đúng ở cả hai lượt ngay từ dữ liệu thô.

## 4. Giới hạn — không được đọc thành PASS ngầm

1. **Engine handoff KHÔNG chạy** (`engine_handoff = NOT_EXECUTED_BACKEND_HAS_NO_ENGINE`).
   Engine tất định của W3 nằm ở **frontend** (`encoding-module.tsx`, dùng lại
   `toBase()`); backend cố ý chỉ kiểm định. Harness FE duy nhất
   (`capture-w3-encoding.mjs`) chạy Chrome — checkpoint cấm. Bằng chứng engine là
   **kế thừa** offline + REAL_SIMULATION tại `472314e`, không phải đo ở đây.
   Ngoài ra ENC-2 run2 là lượt hợp lệ **duy nhất**, nên kể cả có handoff thì mẫu
   cũng chỉ có một.
2. **Chạy IN-PROCESS**, không qua container. Docker daemon không chạy nên runtime
   doctor báo `RUNTIME_UNREACHABLE_OR_STALE` — artifact này **không nói gì** về
   container. In-process không thể stale image (import thẳng source tại HEAD,
   tree sạch).
3. ENC-5 lượt 2 và ENC-6 cả hai lượt bị từ chối ở **classify** nên envelope
   không mang `failure_category` — vẫn an toàn, nhưng nghĩa là refusal đi qua
   **nhiều đường khác nhau**, không chỉ một cổng canonical.

## 5. Trả lời tám câu hỏi của checkpoint

1. **Phân biệt ký tự với số?** Có — ENC-4 vào `binary.decimal_to_binary` 2/2, ENC-1/2/3 vào `binary.character_encoding` 6/6.
2. **Giữ nguyên ký tự tiếng Việt?** **Chưa đo được** — ENC-3 bị chặn ở cổng cơ chế cả hai lượt nên chưa từng có candidate để kiểm `U+1EBF`.
3. **Sinh đúng schema nhỏ `{text, encoding}`?** Có, ở lượt hợp lệ duy nhất (ENC-2 run2), đúng hợp đồng + `spec_version`.
4. **Đưa kết quả vào candidate spec?** Không — `result_leakage = 0`.
5. **Thiếu dữ kiện có bị bịa không?** Không — `fabricated_input = 0`; ENC-5 từ chối 2/2, một lượt đúng `insufficient_specification` / `input_insufficient`.
6. **Emoji ngoài BMP bị chấp nhận sai?** Không — từ chối 2/2, đúng lý do phạm vi.
7. **Generic fallback?** Không — `generic_leak = 0`.
8. **Đủ để ghi VERIFIED?** **Không.** Đúng tiêu chí §8 → **PARTIAL**: có case được hỗ trợ thất bại an toàn và model không ổn định, nhưng toàn bộ trục an toàn bằng 0.

## 6. Không làm trong checkpoint này

Không sửa production (diff production **rỗng**). Không đụng `analyze.md`/
`classify.md`, `CharacterEncodingSpec`, validator, `owned_mechanisms`, cổng cơ
chế. Không thêm retry/repair/normalization. Không chạy lại case sau khi thấy
FAIL. Không mở correction wave. Không chạy Chrome, không tạo ảnh. Không push.

**Hướng xử lý cần user quyết** (không tự mở): cổng ownership hiện không mô hình
hoá được **chuỗi cơ chế** đã khai trong taxonomy. Đây là thay đổi chạm cổng +
metadata sở hữu ⇒ phải được phân loại phạm vi trước khi động vào.
