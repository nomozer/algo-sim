# Khởi động, lỗi và hồi phục runtime model (P7 · Phase I §15)

Model thật `Qwen3-0.6B-AxoV9-Q4_K_M.gguf` (`73f1484b…`), llama.cpp b12470, backend thật. Bằng chứng: `evidence/runtime/`.

## Lỗi nghiêm trọng tìm thấy và đã sửa: socket keep-alive cũ bị báo là crash

**Triệu chứng (lượt 1, candidate /9):** 9 ca `504 LOCAL_SLM_TIMEOUT`, 3 ca `503 LOCAL_SLM_PROCESS_CRASHED` trên 82 ca;
19 lượt 504 ở log backend vì client tự thử lại.

**Tái hiện cô lập (cùng lớp `LocalSlmRuntime`, model thật):** suy luận, nghỉ, suy luận lại:

| Quãng nghỉ | Trước sửa | Sau sửa (`7554e2b72`) |
|---|---|---|
| 0 s / 3 s | OK | OK (1559 / 144 ms) |
| 8 s | **FAIL** `WinError 10053` ⇒ `PROCESS_CRASHED` | OK 165 ms |
| 15 s | OK (server đã bị dừng, khởi động lạnh 1090 ms) | OK 172 ms |
| 30 s | **FAIL** | OK 175 ms |
| 65 s | OK (lạnh) | OK 169 ms |
| 125 s | **FAIL** | OK 196 ms |

**Root cause:** llama-server đóng kết nối keep-alive rỗi (~5 s). `_post_completion_keepalive` chỉ thử lại khi thông điệp lỗi chứa
`10013`, `RemoteDisconnected` hoặc "forcibly closed"; `WinError 10053` (và `BrokenPipe`) rơi xuống nhánh crash ⇒ báo 503 và
**dừng một server đang khoẻ**; lượt sau phải khởi động lạnh. Benchmark /9 chạy liên tục nên không gặp; người học nghỉ > 5 s giữa
hai đề sẽ gặp ở mọi lượt SLM thứ hai.

**Sửa (một chỗ):** lỗi trên một socket *được dùng lại* khi tiến trình còn sống ⇒ kết nối lại một lần. Test
`backend/tests/geometry/test_local_slm_keepalive_stale_socket.py` (nền đỏ 2/5 — 10053 và BrokenPipe; sau sửa 5/5; thêm ca kết nối
mới bị từ chối vẫn phải ném lỗi). Chỉ tầng vận chuyển ⇒ `CACHE_VERSION` giữ 145 (không kết quả cache hay bề mặt trích xuất nào đổi;
`test_cache_identity.py` xanh). Candidate đóng băng lại `a0f979392`.

**Hiệu quả trên trình duyệt (lượt 2, cùng manifest):** 0 lỗi HTTP, 0 timeout, 0 crash trên 82 ca; SLM round trip p95 8.4 s
(lượt 1: 21.3 s), toàn bộ request p95 6.0 s (lượt 1: 49.9 s).

## Ma trận lỗi

| Kịch bản | Cách tạo | Kết quả | Trạng thái |
|---|---|---|---|
| Model tồn tại + SHA đúng | sha256sum file thật | khớp AxoV9, AxoV7 | PASS |
| Runtime version | `llama-server --version` | build 12470 | PASS |
| Khởi động + warm-up | backend mới, lượt SLM đầu | cảnh tất định đầu tiên 875 ms; khởi động llama ≈ 1.1–1.6 s (diag) | PASS |
| Thiếu GGUF (U11) | `LOCAL_SLM_CACHE_DIR` rỗng | health `localSlmReady=false`, `MODEL_NOT_PROVISIONED`; SLM ⇒ `503 MODEL_RUNTIME_UNAVAILABLE` + câu tiếng Việt; **tất định vẫn SERVED**; UI đúng | PASS |
| GGUF hỏng (U12) | bản sao lật 4 byte, cùng kích thước | `503 MODEL_CHECKSUM_MISMATCH`, không nạp; tất định vẫn SERVED | PASS |
| Crash giữa hai lượt (U14) | `Stop-Process` llama-server | lượt sau tự khởi động lại (6.2 s), 200 | PASS |
| Bão hoà hàng đợi (U15) | 8 lượt đồng thời, `max_queue=4` | 5 xử lý, 3 `503 LOCAL_SLM_BUSY` trong ~260 ms kèm câu tiếng Việt; sau đó tất định 90 ms, SLM 4.2 s | PASS |
| Timeout | không có biến cấu hình (45 s cố định trong mã) ⇒ **không tiêm** | quan sát tự nhiên ở lượt 1: `504`, không ghi cache, UI giữ loading qua 2 lần client thử lại | OBSERVED_NOT_INJECTED |
| Runtime bận (busy) | U15 | như trên | PASS |
| Restart backend | 7 lần khởi động trong run (dev, lượt 1, lượt 2, U11, U12, rollback v7, rollback `live`) | health đúng cấu hình mỗi lần | PASS |
| Phục hồi sau lỗi | U14, U15, sau sửa keep-alive | tự hồi phục, không cần thao tác | PASS |
| Không tự dựng hình suy đoán để che lỗi | mọi lỗi runtime ⇒ 503, không có `scene3d` | 0 cảnh khi lỗi hạ tầng | PASS |

Không có fallback đám mây trong bất kỳ kịch bản nào (proxy 0 bản ghi).
