# Local runtime retry validation (P5)

## Lỗi /10

Khi tuyến SLM cục bộ trả 504 đã phân loại (`LOCAL_SLM_TIMEOUT`), `frontend/src/llm/client.ts` coi mọi 502/504 là lỗi
thoáng qua và tự gửi lại. Mỗi lượt chờ hết hạn chót 45 s của runtime, nên người học phải đợi khoảng 135 s cho một lỗi
không thể tự khỏi.

## Sửa (`3e5eb8809`)

`NON_RETRYABLE_REASONS` = `LOCAL_SLM_TIMEOUT`, `LOCAL_SLM_BUSY`, `LOCAL_SLM_RESPONSE_INVALID`,
`MODEL_RUNTIME_UNAVAILABLE`, `MODEL_CHECKSUM_MISMATCH`, `HYBRID_DEADLINE_EXCEEDED`. Điều kiện thử lại mới:
`transient = (502 || 504) && !NON_RETRYABLE_REASONS.has(reason)`. Lỗi 502/504 **không** phân loại (proxy, mạng) vẫn được
thử lại như cũ.

## Kiểm

- Đơn vị: `frontend/src/llm/local-runtime-retry.test.ts` (5 test). Lỗi phân loại ⇒ 1 lượt gọi; lỗi không phân loại ⇒
  vẫn thử lại.
- **Trình duyệt thật + lỗi thật (I06):** llama-server bị treo bằng `NtSuspendProcess` (`tools/suspend_process.py`), nên
  socket vẫn mở nhưng không trả lời. Runtime sản phẩm gặp đúng hạn chót của nó và tự phân loại `LOCAL_SLM_TIMEOUT`. Không
  mock, không chặn route.

| lượt | lượt gọi `/api/analyze` | HTTP | thời gian tới thông báo | thông báo |
|---|---|---|---|---|
| I06 run 2 (`evidence/ui/ui_scenarios_i06_suspended_llama_run2.json`) | **1** | 504 | **45.3 s** | "Máy chủ trả về lỗi khi phân tích / Quá trình phân tích đề mất nhiều thời gian hơn dự kiến hoặc đang có nhiều lượt xử lý cùng lúc. Em hãy nhấn thử lại sau vài giây." |

45.3 s là hạn chót của chính runtime (`DEFAULT_LOCAL_SLM_REQUEST_TIMEOUT_S = 45.0`, `local_slm_runtime.py`) cộng 0.3 s;
/10 mất 135 s.

**Đính chính harness (khai báo):** lượt I06 đầu đặt ngưỡng "≤ 45 s", vì tôi đọc nhầm mặc định 30 s của tuyến live trong
`main.py`. Lượt đó cho 1 lượt gọi, 504, 45.3 s nhưng bị chấm FAIL vì vượt ngưỡng tự đặt sai, và văn bản toast bị đọc sau
khi toast đã ẩn. Sau khi đọc nguồn runtime, ngưỡng được sửa thành hạn chót + 5 s và toast được đọc ngay khi hiện. Cả hai
file kết quả đều được giữ.

## Sau timeout

Runtime dừng llama-server bị treo (`_stop_server_locked`, đếm `timeout_recovery_count`). Lượt kế khởi động lạnh: lượt
"warm2" sau I06 run 1 trả 200 sau 5.7 s. Keep-alive (`7554e2b72` của /10) có hồi quy với các quãng nghỉ 0/3/8/15/30/65/125 s
trong `LOCAL_MODEL_RUNTIME_RECOVERY_REPORT.md` của /10 và test `test_local_slm_keepalive_stale_socket.py` (chạy trong T3).
Lượt mù /11 có 114 ca với quãng nghỉ đan xen và **0** lỗi hạ tầng, 0 `LOCAL_SLM_PROCESS_CRASHED`.
