# Kiểm chứng rollback (P8 · Gate H9)

Ba loại rollback khác nhau, chạy thật, không xoá môi trường. `active_model.json` thật của máy **không bị đụng**: rollback model
chạy trên một bản sao cache trong scratchpad (runtime + AxoV7 + AxoV9 sạch).

| Loại | Thao tác | Kết quả quan sát | Bằng chứng |
|---|---|---|---|
| **Model** AxoV9 → AxoV7 | `provision_local_slm.py --cache-dir <bản sao> --rollback v7 --json` | `ok`, `active_model_key=qwen3-0.6b-axo-v7-q4_k_m`, sha `36e784d1…`; backend khởi động lại báo `localSlmModel=…axo-v7…`, `aiAvailable=true`; **llama-server thực sự nạp `Qwen3-0.6B-AxoV7-Q4_K_M.gguf`** (dòng lệnh tiến trình); đề tất định SERVED, đề SLM chạy trên v7 (200) | `evidence/runtime/rollback_cli_to_v7.json`, `rollback_model_v7.jsonl`, `rollback_model_v7_llama_cmdline.txt` |
| **Model** AxoV7 → AxoV9 | `--activate v9 --json` | `ok`, `active_model_key=qwen3-0.6b-axo-v9-q4_k_m` | `rollforward_cli_to_v9.json` |
| **Cấu hình tuyến** `local-only-scoped` → mặc định | khởi động backend **không đặt** `HYBRID_ROUTE_MODE` | `routeMode=live`, `aiAvailable=false` (không khoá); mọi đề ⇒ `503 MISSING_API_KEY`; proxy egress 0 bản ghi (không thử gọi Gemini) | `rollback_route_default_live.jsonl` |
| **Mã sản phẩm** về candidate /9 | lượt nghiệm thu 1 chạy đúng mã runtime của /9 (`a7a6bc41`, trước sửa keep-alive) trên cùng frontend | chạy được, cùng bộ đề; khác biệt đo được là lỗi keep-alive | `LIVE_SIMULATION_ACCEPTANCE_RESULTS.json` (pass1) |

Đường rollback mã: các commit của nhánh tích hợp là tiến tới, độc lập — `git revert 7554e2b72` (runtime) hoặc `git revert
e10697092` (frontend) không cần viết lại lịch sử; tag kiến trúc `pre-hybrid-cutover-f986e897` không liên quan run này.

Không làm hỏng cache/dữ liệu người dùng: mỗi cấu hình dùng một DB SQLite riêng trong scratchpad; DB và cache model thật không bị ghi.

Rollback model ≠ rollback tuyến: đổi model giữ nguyên `local-only-scoped`; rollback tuyến đưa sản phẩm về `live` (cần khoá Gemini
để phục vụ — run không gọi Gemini).

**Rollback: PASS** (model hai chiều, cấu hình, mã).
