# hybrid-compiler-selection — bàn giao

Trạng thái: `HYBRID_COMPILER_SELECTION_OFFLINE_EVALUATION_AWAITING_REVIEW`.

- Nhánh `feat/text-to-geometry-functions` (local, chưa push, chưa merge).
- Nhánh pilot `feat/real-model-pilot-tooling` @ `471a2c79` giữ nguyên.
- `LLM_ONLY` vẫn mặc định.
- Nhánh B là thực nghiệm, không nối vào route nào.
- Candidate `e9d20aa2…`.

## Đọc trước

`report.md` → `ARCHITECTURE_COMPARISON.md` → `AB_OFFLINE_RESULTS.md` → `TYPED_FACTS_CONTRACT.md` → `PLANNER_MAP.md` →
`REAL_MODEL_AB_PROTOCOL.md` → `RESEARCH_GAP_UPDATE.md`. ADR `docs/architecture/TEXT_TO_GEOMETRY_FUNCTIONS_DECISION.md` không đổi.

## Tái lập (0 lượt gọi, từ `backend/`, `PYTHONIOENCODING=utf-8`)

```bash
.venv/Scripts/python.exe -m pytest tests/geometry/test_hybrid_compiler_selection.py -q
.venv/Scripts/python.exe scripts/hybrid_ab_offline.py --out-dir <tạm>       # so với offline/ — phải trùng từng byte
.venv/Scripts/python.exe ../docs/evaluation/geometry/runs/hybrid-compiler-selection/diagnostics/mutation_check.py
.venv/Scripts/python.exe ../docs/evaluation/geometry/runs/hybrid-compiler-selection/diagnostics/independent_oracle_check.py
.venv/Scripts/python.exe ../docs/evaluation/geometry/runs/hybrid-compiler-selection/diagnostics/responsibility_and_surface.py
```

Kiểm renderer: `docs/evaluation/geometry/runs/text-to-geometry-functions/scene_world_metric_check.ts` (esbuild + node) trên
`<tạm>/scenes`.

## Người dùng cần quyết

1. Duyệt run này. Nó cùng nhánh với `ai-function-route` và `text-to-geometry-functions`, cả hai đang chờ duyệt.
2. Chọn **một** trong hai pilot có phí, hoặc không chạy:
   - P-FC1: chỉ nhánh A, trần 4 USD (`ai-function-route/EXPERIMENT_PROTOCOL_V2.md`);
   - P-AB1: A và B, trần 7 USD, B′ duyệt riêng (`REAL_MODEL_AB_PROTOCOL.md`).

   P-AB1 phủ F-ANY của P-FC1. Pilot nào cũng cần trước một runner có ngân sách, viết và chứng nhận với 0 lượt gọi.
3. Có giữ nhánh B sau pilot không. Nếu giữ, gộp bộ đọc vỏ phản hồi chung (`PLANNER_MAP.md` §5).

## Ghi chú

- Cổng nguồn được nới cho cả hai nhánh: thêm "lập phương", và "hình chữ nhật" thành "chữ nhật". Khai báo và phép thử ở
  `AB_OFFLINE_RESULTS.md` §6. Chưa có test âm riêng cho các từ khoá mới.
- Tự rà soát tìm và sửa 2 lỗi của B ở `91e2edf9`, nên candidate được đóng băng hai lần. `2c4ea2d2` là candidate trung gian.
- `frontend/public/favicon.svg` vẫn là tệp **chưa theo dõi** của người dùng. Run này không tạo nó, không stage, không xoá.
- Không làm: gọi API có phí, đổi mặc định, đổi kiến trúc đích, xoá `LLM_ONLY`, sửa kết quả cũ, frontend, push, merge.
