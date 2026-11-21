# Kiểm chứng hiển thị trên trình duyệt thật (P6 · Gate H3, H4)

## Môi trường

- Frontend: `vite preview` phục vụ `frontend/dist` build từ `e10697092` (dist tree `89fe949b…`), proxy `/api` → `127.0.0.1:8000`.
- Backend: uvicorn từ nhánh tích hợp, `HYBRID_ROUTE_MODE=local-only-scoped`, **không** `GEMINI_API_KEY`, DB SQLite mới mỗi lượt,
  llama.cpp b12470 + `Qwen3-0.6B-AxoV9-Q4_K_M.gguf` (`73f1484b…`).
- Trình duyệt: Playwright Chromium 151.0.7922.34 headless (WebGL qua SwiftShader), Windows 11 Pro, viewport 1366×768.
- Không mock, không chặn route, không fixture cảnh: mọi cảnh là response thật của `POST /api/analyze` (đã lưu `evidence/browser/responses_*.jsonl`,
  sha256 từng response trong `browser_records_*.jsonl`).
- Harness: `tools/live_browser_acceptance.mjs` (đóng băng ở `451a59040`); móc đo cài trước script trang (`addInitScript`), không sửa mã sản phẩm.

## Tiêu chí mỗi cảnh (đăng ký trước, `ACCEPTANCE_FREEZE.json`)

canvas hiện, tỉ lệ pixel "có mực" ≥ 1%; mọi nhãn đỉnh/điểm phụ gold hiện và nằm trong canvas; 0 lỗi console; xoay đổi khung
với tập nhãn ổn định; thu phóng đổi khung; 0 lượt `/api/analyze` trong lúc tương tác.

## Kết quả

| Lượt | Candidate | Cảnh phục vụ | Hiển thị đạt | Tương tác (thao tác) | Lỗi console | Nhãn thiếu / ngoài canvas |
|---|---|---|---|---|---|---|
| 1 (mù) | `a7a6bc41` | 38 | 38/38 | 151/152 | 0 | 0 / 0 |
| 2 | `ce3e3c4b` | 40 | **40/40** [0.91, 1.00] | **159/160** [0.97, 1.00] | 0 | 0 / 0 |

Phân loại (lượt 2): `MATHEMATICALLY_CORRECT_VISUALLY_CORRECT` 40 · `MATHEMATICALLY_CORRECT_VISUALLY_BROKEN` 0 ·
`MATHEMATICALLY_INVALID` 0 · `VISUAL_NOT_VERIFIED` 0 (mọi cảnh phục vụ đều đã xem trên trình duyệt).

Tôi xem trực tiếp ảnh chụp D1, V07, V17, V20, V24 và bốn kích thước U16: đúng loại khối, đúng nhãn đỉnh, nét khuất nét đứt,
đường cao tô màu, không có cạnh lạ, không vật thể trùng.

Thất bại tương tác duy nhất: **V17** — kéo bắt đầu ở tâm canvas không xoay (cả hai lượt), thu phóng và bước dựng vẫn đạt.
Kiểm có chủ đích (U05): kéo từ vùng trống xoay bình thường; kéo bắt đầu trên chip số đo xoay được 3/4 lần. Root cause
**chưa xác lập** (giả thuyết "chip nuốt sự kiện" không được xác nhận).

## Kịch bản UI (`evidence/ui4/ui_scenarios.json`)

| ID | Kịch bản | Kết quả | Ghi chú |
|---|---|---|---|
| U01 | readiness keyless | PASS | `aiAvailable=true`, `hasKey=false`, không chữ "khóa AI/API key/Gemini" |
| U02 | hai đề liên tiếp trong cùng phiên | PASS | nhãn đổi đúng `ABCDS` → `ABCO`, không giữ cảnh cũ |
| U03 | phục vụ → từ chối | PASS | canvas bị gỡ (0), toast "Dữ kiện đề bài chưa nhất quán" |
| U04 | từ chối → phục vụ | PASS | nhãn lăng trụ đúng |
| U05 | xoay từ vùng trống | PASS | khung đổi, 4 nhãn di chuyển, 0 lượt phân tích |
| U06 | thu phóng | PASS | |
| U07 | bước trước / sau | PASS | `5/5 → 4/5 → 5/5` |
| U08 | đặt lại góc nhìn | **FAIL theo ngưỡng tự đặt** | khung sau đặt lại khác cảnh đã xoay 9.9%; bấm lần hai khung gần như trùng (0.024% pixel) nhưng một nhãn DOM lệch 8 px > ngưỡng 2 px. Camera trở về đúng; nhãn có dao động bố trí. |
| U09 | X-ray, bật/tắt nhãn | PASS | X-ray đổi khung và trả lại (0.026%); menu "Nhãn" ẩn hết 4 nhãn rồi hiện lại đủ |
| U10 | chọn đối tượng | PASS | chip `S` ⇒ nhãn `S` có lớp `la-chon` |
| U00 | lỗi console suốt kịch bản | PASS | 0 |

Các lần chạy `evidence/ui/`, `ui2/`, `ui3/` được giữ: lần 1 dùng selector menu không có trong bố cục này; lần 2–3 so khung bằng
hash pixel tuyệt đối (quá khắt khe vì hiệu ứng hover dưới con trỏ) và đếm nhãn chỉ theo `display`. `ui4` dùng tỉ lệ pixel khác
biệt với con trỏ ngoài canvas và `checkVisibility()`.

## Bước dựng

Bước tích luỹ từ `events` hoạt động (prev/next/phát). `DYNAMIC_CONSTRUCTION_STEPS = NOT_IN_PRODUCT` (Construction /2 chưa tích hợp,
không coi là lỗi của cutover local).

**Gate H3: PASS** (frontend thật + backend thật + model thật, cảnh hiện, trace/ảnh lưu, 0 lỗi renderer, không rò cảnh cũ).
**Gate H4: PASS có ghi chú** (159/160; V17 chưa rõ nguyên nhân; U08 lệch nhãn 8 px).
