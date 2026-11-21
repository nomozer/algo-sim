# Tích hợp frontend keyless (P3 · Gate H5)

**Trạng thái: tích hợp thật trên nhánh `integration/local-only-3d-live-acceptance` (commit `e10697092`), chưa merge, chưa push.**
Không chỉ là bản vá: đã build (`tsc -b` + vite), chạy test, và chạy trong trình duyệt thật.

## Thay đổi

1. Bản vá /9 `frontend_local_ai_status_and_keyless_ux.patch` (kiểm lại trước khi áp): `ServerHealth` nhận `aiAvailable`,
   `localOnlyMode`, `localSlmReady`, `localSlmModel`, `routeMode`; `isAiAvailable(health)` thay mọi chỗ đọc `hasKey`
   (4 chỗ trong `ProblemInput.tsx`); dòng trạng thái cho trình đọc màn hình nói "Mô hình AI cục bộ chưa sẵn sàng" ở chế độ cục bộ.
2. Bổ sung của run: ở chế độ cục bộ, `503` hiện tiêu đề **"Bộ đọc đề trên máy chưa sẵn sàng"** kèm câu tiếng Việt của backend
   (thiếu model / đang bận / timeout), thay câu "Máy chủ chưa bật kết nối AI cho đề tự nhập" vốn sai ngữ cảnh.
3. Test `frontend/src/components/local-ai-keyless-ux.test.tsx` (nền đỏ trước sửa 2: 1 fail / 3 pass; sau: 4/4) + mục `docs/CODE_INDEX.md`.

Không đổi giao diện nhập đề hay Scene3D; readiness vẫn là văn bản cho trình đọc màn hình như thiết kế hiện hành (không có huy hiệu
trạng thái nhìn thấy được — đó là quyết định thiết kế, không phải việc của cutover).

## Kiểm chứng

| Kiểm | Kết quả |
|---|---|
| vitest liên quan (6 file) | 52/52 |
| `npm run build` | xanh |
| U01 readiness thật | `aiAvailable=true`, không chữ khoá đám mây trong DOM |
| 82×2 ca trình duyệt | `cloud_key_text = 0`, `ui_token_leak = 0` (regex mã máy `ABC_DEF…`, `kq_`, `Traceback`, `reason_code`) |
| U11 thiếu model (UI thật) | readiness "Mô hình AI cục bộ chưa sẵn sàng…"; đề cần SLM ⇒ toast "Bộ đọc đề trên máy chưa sẵn sàng / Mô hình xử lý trên máy chưa được cài đặt đầy đủ…"; đề tất định vẫn dựng hình |
| Crash runtime (lượt 1, V28/Q08/C03) | toast "Bộ đọc đề trên máy chưa sẵn sàng / Quá trình phân tích đề mất nhiều thời gian…" |
| Từ chối hình học | toast riêng ("Dữ kiện đề bài chưa nhất quán", "Axo chưa hỗ trợ phép dựng này", "Đề bài chưa được hỗ trợ") — không lẫn với lỗi model |

## Giới hạn còn lại (không sửa trong /10)

- **Timeout 504**: `postJsonWithBoundedRetry` tự thử lại tới 2 lần với 502/504 ⇒ một timeout 45 s của SLM giữ "Đang dựng hình…"
  khoảng 3×45 s trước khi báo (quan sát lượt 1, `acceptance_V02.png` chụp ở ~75 s vẫn đang tải; có nút **Huỷ** nên không kẹt cứng).
- Thiếu dữ kiện hiển thị thành "Axo chưa hỗ trợ phép dựng này" (backend gắn `capability_gap`); câu hỏi làm rõ không tới UI.
- Đề không dấu hiển thị "Bài này thuộc môn học khác…".

**Gate H5: PASS** (không cần khoá Gemini; readiness đúng; lỗi thiếu model đúng; lỗi ngoài phạm vi hiện riêng; không lộ token nội bộ),
kèm ba giới hạn UX trên.
