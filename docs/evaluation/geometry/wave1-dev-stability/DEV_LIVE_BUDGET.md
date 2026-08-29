# DEV_LIVE_BUDGET — wave xác minh end-to-end sau WAVE 1

**Ngày**: 2026-08-29 · Đọc TRƯỚC lời gọi live đầu tiên, **0 API call**.

## Cấu hình model hiện tại — đọc, không đổi

| | Giá trị | Nguồn |
|---|---|---|
| `MODEL` | `gemini-2.5-flash` | `app/ai/gemini.py` |
| thinking config | **KHÔNG gửi** — không có `thinkingConfig` trong payload; mặc định của provider áp dụng | `gemini.call_gemini` |
| `maxOutputTokens` | **KHÔNG đặt** — mặc định provider | `generation_config` chỉ có `temperature` (+ `responseMimeType`/`responseSchema` khi có schema) |
| `temperature` | `0.2` | mặc định của `call_gemini` |
| HTTP timeout | `120.0`s | `httpx.AsyncClient` |
| retry TRANSPORT | `MAX_ATTEMPTS = 4` (1 + 3 lần lại), backoff base `1.0`s, trên `{429,500,502,503,504}` | `gemini` |
| retry NGỮ NGHĨA | `MAX_SEMANTIC_PROGRAM_ATTEMPTS = 3` | `pipeline` |

**Không tăng thinking hay retry để test qua được.** Cả hai con số trên là
phần của hệ đã đóng băng; sửa chúng ở wave này là đo một hệ khác với hệ vừa
sửa, và làm hỏng chính câu hỏi cần trả lời.

⚠️ `thoughtsTokenCount` **có** được `telemetry` bắt nếu provider trả về. Vì
`thinkingConfig` không được gửi, con số ấy phản ánh hành vi mặc định của
`gemini-2.5-flash`, không phải một lựa chọn của hệ.

## Trần cứng của wave

```
TRAN_LOGIC_WAVE = 90        TRAN_HTTP_WAVE = 120
```

Dẫn ra: canary `3 đề × 1 lượt × 6 logic = 18`; bộ ổn định nhỏ
`4 đề × 3 lượt × 6 logic = 72`; cộng `= 90`. HTTP theo tỉ lệ `8/6`.

Trần **chặn trước khi vượt**, không dừng sau: bộ chạy kiểm `tl + 6 > 90`
trước mỗi lượt. Mục tiêu không phải benchmark rộng — nó là phép chứng minh
end-to-end sau khi sửa, nên trần đặt sát chứ không đặt rộng cho yên tâm.

## Ba mẫu số của token, và vì sao cần cả ba

```
TOKENS_PER_RUN             mỗi lượt gọi tốn bao nhiêu
TOKENS_PER_EXECUTABLE_IR   mỗi IR CHẠY ĐƯỢC tốn bao nhiêu — lượt hỏng vẫn tiêu
TOKENS_PER_CORRECT_IR      mỗi IR ĐÚNG tốn bao nhiêu — giá thật của kết quả dùng được
```

Một con số *tổng token* che mất chỗ đắt. Nếu 1/3 lượt hỏng thì
`TOKENS_PER_CORRECT_IR` gấp ba `TOKENS_PER_RUN`, và chính khoảng cách ấy là
thứ phải báo cáo khi nói về hạn chế token.

## Không đổi model trong wave này

Câu hỏi của wave: *"các phép sửa kiến trúc có thông end-to-end không?"* Trộn
việc đổi model vào cùng một lượt đo thì không tách được nguyên nhân. So sánh
hiệu quả model là việc riêng, nhỏ, và chỉ sau khi tuyến đã thông.
