# ai-function-route — bàn giao

Trạng thái: `NEW_ARCHITECTURE_AI_ADAPTER_AND_GEOMETRY_EXPANSION_AWAITING_REVIEW`. Nhánh `feat/text-to-geometry-functions`
(local, chưa push/merge; nhánh pilot `feat/real-model-pilot-tooling` @ `471a2c79` giữ nguyên). `LLM_ONLY` vẫn mặc định.

## Đọc trước

`docs/architecture/TEXT_TO_GEOMETRY_FUNCTIONS_DECISION.md` → `…_CONTRACT.md` → `report.md` → `ADAPTER_REPORT.md` →
`SEMANTIC_ROBUSTNESS_EVALUATION.md` → `GEOMETRY_EXPANSION.md` → `EXPERIMENT_PROTOCOL_V2.md` → `LITERATURE_GAP_MATRIX_V2.md`.

## Tái lập (0 lượt gọi)

```bash
cd backend && PYTHONIOENCODING=utf-8 .venv/Scripts/python.exe -m pytest tests/geometry/test_ai_function_route.py tests/geometry/test_text_to_geometry_functions.py -q
cd backend && PYTHONIOENCODING=utf-8 .venv/Scripts/python.exe scripts/run_text_to_functions_fixtures.py --fixtures paraphrase_cases.json --via-fake-gemini --out-dir <tạm>
cd backend && PYTHONIOENCODING=utf-8 .venv/Scripts/python.exe ../docs/evaluation/geometry/runs/ai-function-route/diagnostics/mutation_check.py
```

Kiểm renderer: `docs/evaluation/geometry/runs/text-to-geometry-functions/scene_world_metric_check.ts` (esbuild + node) trên `<tạm>/scenes`.

## Người dùng cần quyết

1. Duyệt run này (và run `text-to-geometry-functions` cùng nhánh).
2. Duyệt hay không pilot P-FC1 (`EXPERIMENT_PROTOCOL_V2.md` §2, trần 4 USD). Trước pilot: viết runner có ngân sách cho
   đường mới theo khuôn pilot G05 (0 lượt) và tách lỗi sản phẩm/công cụ, lưu phản hồi thô.
3. Có đo nhánh đối chứng `LLM_ONLY` cùng corpus không (phê duyệt riêng, chi phí cao hơn).

## Ghi chú

- `frontend/public/favicon.svg` xuất hiện lại là tệp CHƯA theo dõi (đã xoá ở `f89a1a8b` theo lệnh người dùng) — không do
  lượt này tạo, không stage, để nguyên.
- Không làm: pilot có phí, đổi mặc định, xoá `LLM_ONLY`, sửa P1/P2 của `LLM_ONLY`, frontend, đáy hình thoi/hình thang.
