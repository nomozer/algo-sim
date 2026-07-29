# M17 W3-LIVE-C1 — rerun live `binary.character_encoding`

**Kết luận: `W3_LIVE_PARTIAL`** (baseline cũng PARTIAL, nhưng 7/12 → **9/12
PASS**, và cổng cơ chế đã ngừng chặn hai trong ba case được hỗ trợ).

| | Baseline `w3-live` | Rerun C1 |
|---|---|---|
| PASS | 7/12 | **9/12** |
| FAIL_SAFE | 5 | **3** |
| `mechanism_gate_failure` | 5 | **2** (chỉ ENC-3) |
| HTTP | 27/45 | **29/45** (0 transient · 0 retry) |
| Mọi trục an toàn | 0 | **0** |

Artifact baseline **giữ nguyên**, không sửa một byte — đặt cạnh để so sánh.

## Cấu hình

`gemini-2.5-flash` · google-gemini ·
`…/v1beta/models/gemini-2.5-flash:generateContent` · analyze `0.1` · classify
`0.0` · simulate `0.1` · transport `max_attempts=2` · simulate validation-retry 3.
Prompt, số lượt, thứ tự, provider, model, sampling: **y hệt baseline**.

**Runtime: IN-PROCESS**, source `f8f3790` + patch C1 · `cache=24 · family=11 ·
target=22 · hash=4d7c8e65e1fa`. Container Docker đang chạy nhưng **STALE**
(`sha=0513740a · cache=22 · family=10 · target=20`) — nó **không** phải runtime
được kiểm, và `runtime_identity.json` ghi lại đúng như vậy.

## Kết quả từng case

| Case | L1 | L2 | `prescribed_procedure` đo được |
|---|---|---|---|
| ENC-1 ASCII một ký tự | **PASS** | FAIL_SAFE | `character_code_mapping` cả hai lượt |
| ENC-2 ASCII chuỗi | **PASS** | **PASS** | `character_code_mapping` cả hai lượt |
| ENC-3 Unicode BMP | FAIL_SAFE | FAIL_SAFE | `binary_positional_weights` cả hai lượt |
| ENC-4 ranh giới với SỐ | **PASS** | **PASS** | → `binary.decimal_to_binary` |
| ENC-5 thiếu dữ kiện | **PASS** | **PASS** | từ chối an toàn |
| ENC-6 emoji ngoài BMP | **PASS** | **PASS** | từ chối an toàn |

`semantic_loss` · `fabricated_input` · `result_leakage` · `generic_leak` ·
`unsafe_acceptance` · `wrong_target_acceptance` = **0**. `safe_failure` = 3 ·
`mechanism_gate_failure` = 2.

Candidate được chấp nhận (đúng hợp đồng nhỏ nhất, **không** mang kết quả):

```json
{"spec_version": "charenc-1.0", "text": "A",   "encoding": "ascii"}
{"spec_version": "charenc-1.0", "text": "Tin", "encoding": "ascii"}
```

Code point thực tế: `A` → `U+0041` · `Tin` → `U+0054 U+0069 U+006E`. Không đổi
hoa/thường, không bỏ ký tự.

## Ba lượt chưa PASS — phân loại đúng nguyên nhân

**ENC-1 run2 — KHÔNG phải cổng cơ chế.** `prescribed =
character_code_mapping`, cổng cơ chế **đã cho qua**; bị chặn ở cổng **đủ dữ kiện**
(`insufficient_specification` / `input_insufficient`) vì lượt đó analyze không
phơi được bằng chứng ký tự trong dấu nháy. Root cause: `MODEL_VARIABILITY`. Từ
chối an toàn, không bịa dữ kiện.

**ENC-3 cả hai lượt — cổng cơ chế, và chặn ĐÚNG.** Đề nói *"…**và chuyển mã đó
sang nhị phân**"* nên analyze đặt cơ chế chính là `binary_positional_weights` —
cơ chế của `decimal_to_binary`, vốn chặn cứng 0–255/8 bit nên **không biểu diễn
nổi** code point 7871 của `ế`. Cổng từ chối trung thực thay vì mô phỏng bằng cơ
chế sai. Đây là giới hạn ĐÃ BIẾT, không phải lỗi an toàn.

Hệ quả: **`U+1EBF` vẫn CHƯA đo được ở đường live** — không có candidate nào được
chấp nhận cho ENC-3, nên E2E Unicode = `NOT_MEASURED` (§13). Không dựng config
tay để lấp chỗ trống.

## Phạm vi

6 case × 2 lượt là **smoke**, không phải benchmark độ chính xác trên mọi đề tiếng
Việt. Không nói gì về hiệu quả học tập.
