# Gemini credential transport & offline isolation — báo cáo ngắn

Run `gemini-credential-transport` · 2026-11-07 · tiếp nối `hybrid-backend-reliability` trên cùng nhánh
`feat/hybrid-backend-reliability`, rồi tích hợp `--no-ff` vào `main` theo yêu cầu Owner. 0 lượt gọi provider.

## 1. Khoá API (`backend/app/ai/gemini.py`, product `6f184bda`)

`call_gemini` — transport của đường đọc ảnh, consumer sản phẩm duy nhất — gửi khoá trong query `?key=`. Đã chứng minh
(khoá giả, `MockTransport`): bật INFO cho logger `httpx` là dòng `HTTP Request: POST …:generateContent?key=<khoá>` in nguyên
khoá. Sửa: khoá chỉ đi trong header `x-goog-api-key` (như `function_calling.live_transport` của tuyến Hybrid); lỗi mạng ném
`from None`. Model, payload, ảnh, timeout, retry, parser, usage, thông điệp lỗi không đổi. Không còn đường sản phẩm nào đặt
khoá vào URL (grep toàn `backend/`). Test: `tests/test_gemini.py` (httpx thật trên `MockTransport`: header, URL/body/log
sạch, mọi lần retry, 400/401/403 không retry, 429/500 retry đủ lượt, lỗi mạng đã làm sạch),
`test_image_extract_api.py::test_doc_anh_qua_transport_that_khoa_chi_trong_header` (endpoint đầu–cuối; thiếu khoá ⇒ 0 request).

## 2. Cách ly mạng offline (`backend/conftest.py`, `backend/tests/offline_child/`)

Lỗ thật: tiến trình Python CON do test spawn import `app` ⇒ `load_dotenv` ⇒ **có lại khoá thật**, không guard nào (đo:
`key present = True`; sau sửa `False`). Thêm lớp 3, chỉ ở tầng test: socket chỉ nối loopback (trong tiến trình), và
`tests/offline_child` lên đầu `PYTHONPATH` ⇒ `sitecustomize` của mọi con: `GEMINI_API_KEY=""` trước khi `.env` nạp, guard
socket + chặn httpx. Không thêm biến runtime nào. Giới hạn: trên Windows asyncio Proactor nối bằng `ConnectEx` (vượt
`socket.connect`); HTTP async trong tiến trình vẫn bị lớp httpx chặn. Hai lane script của T3 (`replay_demo_cases.py`,
`audit_demo_crash_surface.py`) chạy ngoài pytest nhưng không import `app.ai`/httpx — không chạm được provider.
Test (`tests/test_offline_guard.py`): `.env` nạp lại khoá (giả) vẫn bị chặn ở cả hai transport và socket thô; loopback vẫn
nối; con tạo bằng kế thừa / lọc `GEMINI*` / khoá giả tường minh không thấy khoá thật, không mở được socket/httpx ra ngoài.
Đích kiểm: TEST-NET-3 `203.0.113.10` và `.invalid` — không dịch vụ thật nào bị chạm.

`ALLOW_LIVE_AI=0`: `/api/analyze` (trước cache, `test_hybrid_product_integration.py`) và `/api/image/extract` (trước cache,
`05cf4db1`) ⇒ 503 `LIVE_AI_DISABLED`; transport Hybrid cũng tự kiểm. Không còn đường provider sản phẩm nào khác.

## 3. Đối chiếu sự cố (đính chính diễn giải `hybrid-backend-reliability` §9 — báo cáo gốc giữ nguyên)

| mục | kết luận | căn cứ |
|---|---|---|
| `UNAUTHORIZED_REQUEST_COUNT` | **UNKNOWN**; ≤ 8 lời gọi `call_gemini` thành công, ≤ 16 HTTP attempt (`VISION_MAX_ATTEMPTS = 2`) | cache ảnh nằm trong bộ nhớ tiến trình đã thoát; đọc ảnh không ghi DB (DB tạm của lượt ấy chỉ có `simulation_cache`, sổ lượt, telemetry analyze) |
| `UNAUTHORIZED_SPEND` | **UNKNOWN** | không có quyền/công cụ tra billing Google Cloud ở máy này (`gcloud` không cài); không suy "≈ 0" từ kích thước ảnh |
| khoá bị log / lộ | **không tìm thấy** (rủi ro tiềm ẩn đã đóng, không phải sự cố đã xác minh) | tiến trình lượt ấy không cấu hình logging ⇒ dòng INFO httpx không phát; 0 tệp chứa mẫu `generateContent?key=AIza…` hay chuỗi dạng khoá Google trong scratch, log tác vụ và 34 thư mục DB tạm; 0 commit chứa mẫu đó; publication scan PASS |
| khoá trong Git | không | như trên |
| dữ liệu người học | không — ảnh trắng tổng hợp do Pillow sinh trong công cụ | `tools/image_boundary_probe.py` của run trước |
| đường gây sự cố | đã chặn ba lớp: công cụ (`block_network`), công tắc dừng ảnh (`05cf4db1`), lớp 3 ở mọi test + con | §2 |
| xoay vòng khoá | **không bắt buộc theo bằng chứng**; quyết định thuộc Owner (agent không xoay/thu hồi) | khoá chỉ đi tới endpoint Google qua TLS |

## 4. Kiểm chứng

Targeted: 1 040 passed + 10 đỏ đúng nhóm con dấu candidate (xanh sau khi đóng băng lại). Candidate `b8e20c8f`
(product `6f184bda`, 103 file `befb10b5…`, MATCH). `CACHE_VERSION` 132: khoá cache ảnh (`vision_identity`) và Route D
không chứa gì về xác thực. Full T3 và tích hợp: `run.json`.
