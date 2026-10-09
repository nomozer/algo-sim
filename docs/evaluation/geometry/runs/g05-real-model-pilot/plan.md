# g05-real-model-pilot — kế hoạch và đăng ký trước

Phê duyệt của người dùng (2026-10-10): G1–G5 + MỘT pilot Gemini live có điều kiện. Khai đo:
`MEASUREMENT_CLASS = DEVELOPMENT_G05_REAL_MODEL_PILOT` · `HELD_OUT_CLAIM = NO` (corpus đã được nhìn khi xây T8/T11/T12) ·
`EVALUATOR_INDEPENDENCE = PARTIAL` (nhãn + oracle ghi trước khi sửa sản phẩm; kiểm metric LOCAL độc lập; cùng nhóm tác
giả). Nền: `main` = `28ac1d61`, candidate `93077b51…`, `CACHE_VERSION` 125, `LLM_ONLY`, compiler opt-in. Khảo sát:
`runs/real-model-e2e-readiness/report.md`.

## PHASE A — công cụ, 0 lượt Gemini (phiên này)

Chỉ `backend/scripts/`, test của công cụ đo, và thư mục run này. Không `backend/app`, frontend, kernel, lược đồ,
candidate, cache.

| | tệp | việc |
|---|---|---|
| G1 | `backend/scripts/g05_pilot_scoring.py` | chấm CHÍNH XÁC: nhãn / `int` / `Fraction` / `Radical` / chuỗi hiển thị → khoá `(mu, dấu, giá trị²)`; float ⇒ không chấm được |
| G2 | `backend/scripts/run_g05_real_model_pilot.py` | mỗi đề qua `measure_geometry_stability.mot_luot` = `run_pipeline` thật; chỉ thay dữ liệu, thư mục ra, kỳ vọng, oracle |
| G3 | `g05_pilot_scoring.phan_loai` | SERVED_CORRECT · SERVED_WRONG · REFUSED_CORRECT (cổng tất định sau IR, ghi `ground`) · REFUSED_WRONG · PROVIDER_ERROR · PARSER_SCHEMA_ERROR · TOOL_ERROR · UNGRADABLE · RUN_STOPPED · NOT_RUN |
| G4 | `backend/scripts/g05_pilot_scene_replay.py` + `scene_world_check.ts` | dựng lại cảnh từ hợp đồng + chương trình đã lưu; kiểm cấu trúc + hình học chính xác theo metric; kiểm biến đổi renderer bằng `veKhongGian` |
| G5 | `run_g05_real_model_pilot.GacCong` / `quet_khoa` / `tat_log_url` | che lỗi provider trước khi rời bộ bọc; `httpx`/`httpcore` ≥ WARNING; quét thư mục ra sau mỗi đề |
| chứng nhận | `backend/scripts/certify_g05_real_model_pilot.py` | provider GIẢ = chương trình corpus viết tay, đi đúng đường live; tiêm lỗi provider / lược đồ / tiếp tục / lộ khoá |

## Corpus — `PILOT_CASES.json` (băm ghim `run_g05_real_model_pilot.CORPUS_SHA256`)

16 đề chép NGUYÊN từ `labels.json` của run gốc (test khoá): 10 dương — X1, X4, X6, T2, T5 (`regular-prisms`), H1, H2,
H8 (`regular-hexagonal-pyramid`), P09, P06 (`exact-dimensions`); 6 âm — NX1, NT2, NT4, NX7 (`regular-prisms`), N8
(`regular-hexagonal-pyramid`), N02 (`exact-dimensions`). Hàng nhãn phụ thuộc CHƯƠNG TRÌNH bị loại. Không đề nào có đính
chính nhãn. Oracle: nhãn gốc + công thức sách độc lập trong `g05_pilot_scoring.v2_cong_thuc` (test khoá cả 10 dương).

## PHASE B — chỉ trong phiên LOCAL MỚI, sau nghiệm thu độc lập

Một lượt duy nhất, `gemini-2.5-flash` (API văn bản chuẩn, không công cụ tính phí), 16 đề × `k = 1`, không gọi lại đề đã
xong. Trần (hằng `CAPS_APPROVED`, không cờ dòng lệnh nào nâng được): **64 lượt logic · 96 lần thử HTTP (kể cả retry) ·
400 000 token** (dự trữ 20 000/lượt gọi khi chặn trước) ⇒ ≤ 1 USD theo bảng giá 2026-08-25 — phải tra lại giá trước live.
Luật dừng: chạm trần; usage thiếu; hai lỗi provider liên tiếp; khoá xuất hiện trong thư mục ra; công cụ sai.
`ALLOW_LIVE_AI=1` chỉ trong tiến trình pilot, không ghi vào `.env`. Không sửa sản phẩm / prompt / thẻ văn phạm / model
giữa các đề. Sau lượt: `g05_pilot_scene_replay.py <thư mục>` + `scene_world_check.ts` trên cảnh dựng lại.
