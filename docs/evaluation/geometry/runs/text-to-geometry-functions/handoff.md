# text-to-geometry-functions — bàn giao cho bước kế

Trạng thái: `NEW_TEXT_TO_GEOMETRY_FUNCTIONS_VERTICAL_SLICE_AWAITING_REVIEW`. Nhánh `feat/text-to-geometry-functions` (local,
chưa push, chưa merge). Nhánh pilot `feat/real-model-pilot-tooling` @ `471a2c79` giữ nguyên (local, chờ review riêng).

## Đọc trước

`report.md` → `ARCHITECTURE_IMPLEMENTATION_MAP.md` → `FUNCTION_REGISTRY_SPEC.md` → `EXPERIMENT_PROTOCOL.md` →
`LITERATURE_GAP_MATRIX.md`. Mã: `backend/app/simulation/geometry_functions/`. Tái lập 0 lượt gọi:

```bash
cd backend && PYTHONIOENCODING=utf-8 .venv/Scripts/python.exe -m pytest tests/geometry/test_text_to_geometry_functions.py -q
cd backend && PYTHONIOENCODING=utf-8 .venv/Scripts/python.exe scripts/run_text_to_functions_fixtures.py --out-dir <tạm>
cd frontend && npx esbuild ../docs/evaluation/geometry/runs/text-to-geometry-functions/scene_world_metric_check.ts \
  --bundle --platform=node --format=esm --outfile=<tạm>/swmc.mjs && node <tạm>/swmc.mjs <tạm>/scenes
```

## Người dùng cần quyết

1. Chấp nhận kiến trúc lời gọi hàm (registry + cổng nguồn + engine bố cục) làm hướng chính trên nhánh nghiên cứu?
2. Thứ tự bước kế (đề xuất): (a) adapter Gemini function calling + fixture tái lập đầu ra function calling (0 lượt) →
   (b) pilot nhỏ có ngân sách (Q1 của `EXPERIMENT_PROTOCOL.md`, cần duyệt) → (c) mở rộng hàm theo lỗi đo được, ưu tiên độ
   dài ký hiệu `a`.
3. Tiêu chí chuyển default (không đổi ở run này; cổng chính thức vẫn là 20 cổng `docs/MIGRATION_CHECKLIST.md`): đề xuất
   thêm — trên cùng corpus đăng ký trước và cùng model, đường mới (i) phục vụ đúng ≥ `LLM_ONLY`, (ii) 0 phục vụ sai,
   (iii) mọi từ chối có mã, (iv) cảnh qua kiểm renderer, (v) chi phí token ≤ — và đường mới phải được nối vào `/api/analyze`
   sau một cờ, có test không lùi ngầm.

## Không làm ở run này (cố ý)

Nối Gemini; đổi default/routing; sửa P1/P2 của `LLM_ONLY`; frontend; ghi `STATUS_LEDGER`/`CURRENT_STATE`/`ROADMAP` (chờ
quyết định 1); xoá legacy.
