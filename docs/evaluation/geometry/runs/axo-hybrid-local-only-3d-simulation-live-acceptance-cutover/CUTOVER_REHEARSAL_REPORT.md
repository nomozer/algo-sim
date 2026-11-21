# Rehearsal cutover (P8 · Gate H9)

Môi trường được phép: nhánh tích hợp `integration/local-only-3d-live-acceptance`, máy dev, backend + frontend thật.
Cutover thử bằng **biến môi trường** `HYBRID_ROUTE_MODE=local-only-scoped`; mặc định trong mã **không đổi** (owner quyết định).

## Điều kiện tiên quyết

| Điều kiện | Trạng thái |
|---|---|
| Owner approval cho frontend trên nhánh tích hợp | có (phiên này) |
| Owner approval đổi mặc định | **không** — owner chọn giữ `live` |
| Git sạch / candidate xác minh | candidate `a0f979392` khớp (`--verify`) |
| Model xác minh | AxoV9 `73f1484b…` |
| Backend route chạy | có |
| Frontend keyless | có (`LOCAL_ONLY_FRONTEND_INTEGRATION_REPORT.md`) |
| Live smoke / nghiệm thu | chạy; xem `LIVE_ACCEPTANCE_GATE_SUMMARY.md` |
| Network isolation | `NO_EXTERNAL_AI` đạt |
| Rollback | đạt (`ROLLBACK_VALIDATION_REPORT.md`) |

## Rehearsal staging (biến môi trường)

| Kiểm | Kết quả |
|---|---|
| Không cần `GEMINI_API_KEY` | đúng (biến bị xoá khỏi môi trường tiến trình; không có `backend/.env` trong worktree) |
| `/api/health` | `routeMode=local-only-scoped`, `localOnlyMode=true`, `localSlmReady=true`, `localSlmModel=qwen3-0.6b-axo-v9-q4_k_m`, `aiAvailable=true`, `ux_state=READY_OFFLINE` |
| `/api/analyze` dùng Local AI | có: `extraction_mode ∈ {LOCAL_DETERMINISTIC_PARSER, LOCAL_SLM_GROUNDED, …}`, `total_provider_calls=0` |
| Scene3D trả về và hiển thị | 40/40 cảnh phục vụ hiện đúng trên trình duyệt |
| Đề chỉ-mô-phỏng theo hợp đồng | 14/28 phục vụ, phần còn lại từ chối an toàn |
| Đề ngoài phạm vi báo phù hợp | 18/18 ca âm từ chối; 2 lỗi phân loại thông điệp (đề không dấu) |
| Không fallback đám mây | 0 egress |
| Frontend không chặn vì thiếu khoá | đúng |
| Feature flags | `local-only-general` vẫn khoá sau `AXO_ALLOW_GENERAL_LOCAL_CUTOVER` (không bật); mặc định `live` xác nhận bằng chạy thật |

## Default cutover

**Không thực hiện.** `SCOPED_CUTOVER_COMPLETED = FALSE`. Bản vá `handoff/default_cutover_local_only_scoped.patch` của /9 vẫn áp được
lên nhánh tích hợp (một dòng trong `main.py::hybrid_route_mode`) và chờ quyết định owner sau khi đọc `PRODUCTION_CUTOVER_DECISION.md`.
Không kích hoạt `local-only-general`.
