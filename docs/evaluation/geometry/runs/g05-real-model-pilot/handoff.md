# g05-real-model-pilot — bàn giao PHASE A → PHASE B (phiên LOCAL MỚI)

Nhánh `feat/real-model-pilot-tooling` (từ `docs/real-model-e2e-readiness` = `4cfa547f`, hậu duệ `main` = `28ac1d61`).
PHASE A: công cụ đo, **0 lượt Gemini**, không đổi mã sản phẩm. Điểm dừng:
`PILOT_TOOLING_IMPLEMENTED_INDEPENDENT_VERIFICATION_REQUIRED`.

## Đã làm (PHASE A)

- G1 bộ chấm chính xác, G2 runner trên `mot_luot`/`run_pipeline`, G3 phân loại 10 hạng, G4 dựng lại cảnh offline +
  kiểm biến đổi renderer, G5 an toàn khoá — chi tiết `plan.md`.
- Corpus 16 đề `PILOT_CASES.json`, băm ghim `fda51779…`.
- Chứng nhận provider giả (`CERTIFICATION.json`, `backend/scripts/certify_g05_real_model_pilot.py`): 10/10 SERVED_CORRECT,
  6/6 REFUSED_CORRECT (cả 6 ở chặng `assumption`), 32 lượt logic = 32 lần thử HTTP, token vào/ra/suy luận/cache cộng
  đúng usage giả; dựng lại cảnh 10/10; tiêm lỗi: lỗi provider trên đề âm ⇒ PROVIDER_ERROR, chương trình hỏng ⇒
  PARSER_SCHEMA_ERROR, tiếp tục ⇒ 0 lượt gọi, khoá giả không có trong artifact.
- Biến đổi renderer (`scene_world_check.ts`, chính `veKhongGian`): RENDER_TRANSFORM_OK 10/10
  (`diagnostics/certification_world_check.log`); tiêm lỗi bỏ `chart_metric` ⇒ MISMATCH.
- Test `backend/tests/geometry/test_g05_real_model_pilot.py`: 55 test; kiểm đột biến 7/7 bị bắt (`diagnostics/mutation_check.log`).
- Kết quả kiểm tra đầy đủ: `run.json` `phase_a`.

## Việc của PHASE B — theo thứ tự, dừng ở bước hỏng

1. Đọc `AGENTS.md`, `docs/RULES.md`, `plan.md`, mã bốn script, test. Kiểm ĐỘC LẬP (không tin bản ghi này): bộ chấm,
   provider giả, che khoá, trần, corpus (so lại với `labels.json` gốc). Chạy lại test + `certify_g05_real_model_pilot.py`.
2. Tra giá `gemini-2.5-flash` hiện hành trên tài khoản đang dùng; nếu khác bảng `api_usage_log.BANG_GIA_USD`
   (2026-08-25: 0,30 / 2,50 USD mỗi triệu token vào / ra) thì ghi giá đã tra vào hồ sơ và tính lại trần USD trước khi chạy.
3. `cd backend && ALLOW_LIVE_AI=1 PYTHONIOENCODING=utf-8 .venv/Scripts/python.exe scripts/run_g05_real_model_pilot.py
   --live --out-dir ../docs/evaluation/geometry/runs/g05-real-model-pilot/live` — MỘT lần. Runner tự kiểm trước lượt
   gọi đầu (ALLOW_LIVE_AI, khoá, model = `gemini-2.5-flash`, candidate `93077b51…`, cache 125, băm corpus) và ghi
   `MANIFEST.json`. Mã ra 3 = dừng theo luật dừng: KHÔNG chạy lại để "đủ số"; đọc `SUMMARY.json` `stop_reason`.
4. `scripts/g05_pilot_scene_replay.py <live>` rồi `scene_world_check.ts` trên `<live>/scenes`.
5. Quét khoá toàn bộ thư mục `live/` trước commit (runner đã quét sau mỗi đề; audit tài liệu có "Secret leaks").
6. Báo cáo: kết quả sản phẩm / sinh chương trình / chi phí, mọi tỉ lệ kèm tử–mẫu; phân biệt lỗi mô hình với lỗi công cụ;
   ghi rõ development pilot, corpus đã nhìn, `k = 1`, độc lập một phần. Kết quả xấu giữ nguyên.

Không: merge `main`, compiler-first, sửa sản phẩm/nhãn rồi chạy lại, G05 mới, OCR, held-out.
