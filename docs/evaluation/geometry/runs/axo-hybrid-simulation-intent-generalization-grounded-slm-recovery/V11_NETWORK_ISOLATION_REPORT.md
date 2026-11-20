# V11 network isolation (P9)

Bốn lớp bằng chứng cho lượt mù cùng mọi kịch bản UI (`V11_NETWORK_ISOLATION_RESULTS.json`):

| lớp | cách đo | kết quả |
|---|---|---|
| 1. Cấu hình | backend chạy với `env -u GEMINI_API_KEY`, `HYBRID_ROUTE_MODE=local-only-scoped`; `/api/health` | `hasKey=false`, `local_only=true`, `extraction_mode=LOCAL_ONLY_V9_SCOPED` |
| 2. Proxy hố đen | `HTTP(S)_PROXY`/`ALL_PROXY` của backend trỏ vào `tools/egress_blackhole_proxy.py`; proxy ghi mọi request rồi trả 403 | **0 bản ghi**: file log không được tạo trong suốt lượt chạy. Tự kiểm sau lượt chạy: 2/2 request thử (HTTP và CONNECT) được ghi (`egress_proxy_v11_selfcheck.jsonl`), chứng minh bộ ghi hoạt động |
| 3. Bảng TCP | `tools/tcp_egress_sampler.ps1` lấy mẫu `netstat` của backend, llama-server và witness | 1692 mẫu trong 1771.6 s, **0** endpoint ngoài loopback |
| 4. Trình duyệt | harness ghi mọi request của trang không tới `127.0.0.1` | **0** |

`route_d.adaptive_telemetry.total_provider_calls` = 0 ở mọi response có trường này. Không có lối lùi ngầm sang cloud:
khi SLM không đọc được, response là từ chối có phân loại, không phải một lượt gọi Gemini.

Phạm vi: chỉ trên host Windows dev này. Khả năng độc lập mạng trên máy đích thật: `NOT_MEASURED`.
