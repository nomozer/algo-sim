# V11 browser render evidence (P8)

## Môi trường

- Frontend: `vite preview` phục vụ `frontend/dist` build tại `fec016682` (mã sản phẩm giống hệt `31c209a8e`; băm cây dist `06806e05…`), proxy `/api` → backend
  `127.0.0.1:8000`.
- Backend: uvicorn tại worktree /11, `HYBRID_ROUTE_MODE=local-only-scoped`, `GEMINI_API_KEY` bị gỡ khỏi môi trường
  (`/api/health`: `hasKey=false`), DB SQLite mới, `HTTP(S)_PROXY/ALL_PROXY` trỏ vào proxy hố đen.
- Mô hình: `qwen3-0.6b-axo-v9-q4_k_m` (`73f1484b…`), llama.cpp `b12470`.
- Trình duyệt: Playwright 1.62.1 Chromium (headless), viewport 1366×768. Harness: `tools/live_browser_acceptance.mjs`
  (chép nguyên từ /10). Móc đo được cài trước script trang; không sửa mã sản phẩm, không mock, không chặn route.
- Đóng băng trước mọi lượt gọi sống: `V11_LIVE_ACCEPTANCE_FREEZE.json` (`fec016682`). Tập mù gồm 85 ca trong phạm vi,
  5 ca D, 24 ca âm và 8 kịch bản UI. Tác giả là agent và tập được khoá trước khi sửa mã (`5d0e86dad`), nên
  `EXTERNAL_INDEPENDENCE = NOT_MEASURED`.

## Tiêu chí mỗi cảnh (đăng ký trước)

Canvas có mực ≥ 1%; mọi nhãn gold hiện và nằm trong canvas; 0 lỗi console; xoay làm đổi khung và giữ nguyên tập nhãn; thu
phóng làm đổi khung; bước trước/sau khôi phục đúng; 0 lượt `/api/analyze` trong lúc tương tác.

## Kết quả (`V11_LIVE_ACCEPTANCE_RESULTS.json`)

| chỉ số | giá trị |
|---|---|
| cảnh phục vụ (trong phạm vi) | 58/85 |
| đúng toán (oracle độc lập, Fraction + Gram) | **58/58**, 333 quan hệ, 0 vi phạm (`V11_MATHEMATICAL_SCENE_VALIDATION.json`) |
| đáp số | **35/35** CORRECT |
| hiển thị đạt | **56/58**. S07 và Q01: đỉnh B ngoài mép canvas (V11-VIS-1) |
| thao tác tương tác | **232/232** (xoay, thu phóng, bước, không gọi lại phân tích) |
| lỗi console trên cảnh phục vụ | 0 |
| rò định danh kỹ thuật / chữ "khoá API" | 0 / 0 |
| ca âm từ chối an toàn | 24/24 |

Ảnh chụp từng ca nằm ở `evidence/browser/screenshots/v11_<id>.png`. Mỗi response có sha256 trong
`browser_records_v11.jsonl`, và nguyên văn response nằm trong `responses_v11.jsonl`.

## Kịch bản UI I01–I08 (`V11_UI_SCENARIO_RESULTS.json`)

| | kết quả |
|---|---|
| I01 kéo từ tâm (V17) | PASS 4/4 cảnh |
| I02 kéo trên cạnh / chip / cạnh nhãn | PASS |
| I03 kéo sau đặt lại và sau đổi đề | PASS |
| I04 U08 đặt lại hai lần | build mù **FAIL** (3–4 px); sau sửa `31e6b47c9` **PASS** 0 px (kiểm sau lượt mù) |
| I05 câu hỏi làm rõ hiện trên UI | PASS (N17); D01/D04/D05 hiện câu hỏi; D02/D03 hiện "chưa hỗ trợ" |
| I06 timeout phân loại không thử lại | PASS (1 lượt, 504, 45.3 s; ngưỡng harness đã đính chính, xem `LOCAL_RUNTIME_RETRY_VALIDATION.md`) |
| I07 huỷ rồi thay đề | PASS. Lượt đầu là lỗi harness: đề chậm nằm sẵn trong cache SLM nên nút Huỷ chưa kịp hiện, và nhãn `data-id` của điểm phụ C09 bị so với gold đỉnh. Đã sửa harness; build mù và build sau sửa đều PASS. |
| I08 4 viewport (1920×1080 … 390×844) | PASS 4/4 (không tràn ngang, nhãn trong canvas, kéo từ tâm xoay được) |
| lỗi console qua mọi lượt UI | 0 |
