# Mạng khi chạy thật (P7 · Gate H6)

## Ba trạng thái — không đánh đồng

| Trạng thái | Kết luận | Căn cứ |
|---|---|---|
| `NO_EXTERNAL_AI` | **Đạt trong phạm vi đo** | bốn lớp bằng chứng runtime dưới đây, 0 ở mọi lớp |
| `FULLY_OFFLINE_RUNTIME` | **Chưa đo trực tiếp** | không ngắt Internet vật lý (phiên làm việc cần mạng); chỉ chứng minh được: không có phụ thuộc mạng ra ngoài nào được *dùng* trong lúc chạy và `dist/` không tham chiếu tài nguyên ngoài |
| `ON_DEVICE_INFERENCE` | **Suy luận tại máy chủ backend** | llama-server chạy cạnh backend trên cùng máy (ở đây: máy dev Windows). Trình duyệt người học chỉ nhận cảnh. Không được nói model chạy trên laptop của mọi học sinh |

## Bằng chứng runtime

| Lớp | Cách | Cửa sổ chứng (bộ đo bắt được lỗi đã biết?) | Lượt 1 | Lượt 2 + runtime/rollback |
|---|---|---|---|---|
| Proxy egress (HTTP/HTTPS) | `tools/egress_blackhole_proxy.py` là `HTTP(S)_PROXY`/`ALL_PROXY` của tiến trình backend (`NO_PROXY` = loopback); mọi request bị ghi và chặn 403 | **có**: lời gọi cố ý tới `generativelanguage.googleapis.com:443` bị ghi (`egress_proxy_selfcheck.jsonl`) | 0 bản ghi | 0 bản ghi (gồm cả lúc backend chạy `live` không khoá) |
| Bảng TCP tiến trình | `tools/tcp_egress_sampler.ps1` lấy mẫu kết nối của backend (:8000) + mọi `llama-server` | **có**: kết nối cố ý tới `1.1.1.1:443` bị ghi (v1 và v2) | 131 mẫu / 1532 s (≈11.8 s/mẫu, v1 dùng `Get-NetTCPConnection` chậm — thưa, chỉ bổ trợ), 0 kết nối ngoài | 1578 mẫu / 1660 s (≈1.05 s/mẫu, v2 `netstat`), 0 kết nối ngoài |
| Request của trình duyệt | Playwright ghi mọi request không phải loopback | — | 0 / 82 ca | 0 / 82 ca (+15 rerun1) |
| Telemetry của route | `route_d.adaptive_telemetry.total_provider_calls`, `gemini_typed_fact_calls`, `gemini_vision_calls` | — | 0 ở mọi response có `route_d` | 0 |

Giới hạn trung thực: bộ lấy mẫu TCP ~1 s/mẫu có thể bỏ sót kết nối sống < 1 s không đi qua proxy; proxy chỉ bắt client tôn
trọng biến proxy (httpx — gồm SDK Gemini — mặc định `trust_env=True`). Không dùng biến môi trường hay AST làm bằng chứng duy nhất.

## Không có fallback đám mây

- `local-only-scoped` không có nhánh Gemini: khi model thiếu/hỏng/bận ⇒ `503` (`MODEL_RUNTIME_UNAVAILABLE`, `MODEL_CHECKSUM_MISMATCH`,
  `LOCAL_SLM_BUSY`), proxy vẫn 0 bản ghi (U11, U12, U15).
- Ở `live` không khoá (rollback cấu hình): `503 MISSING_API_KEY` ngay ở cổng, 0 egress — không có lời gọi nào được thử.
- Ảnh/PDF quét ở local-only: `503 LOCAL_ONLY_CLOUD_VISION_DISABLED` (theo /9; run này không kiểm lại đường ảnh).

## Kết quả

`gemini_invocations = 0` · `external_ai_calls = 0` · `silent_cloud_fallbacks = 0` — trên lượt 1, lượt 2, rerun1, U11/U12/U14/U15,
rollback model và rollback cấu hình.

**Gate H6: PASS** cho `NO_EXTERNAL_AI` trong phạm vi khai báo; không tuyên bố `FULLY_OFFLINE_RUNTIME`.
