# docs-cleanup — handoff

## Trạng thái bàn giao

- Nhánh `feat/regular-square-pyramid`, local only; không push, merge, PR, xoá nhánh hay viết lại lịch sử.
- Product commit `f967ba24`; candidate `7f3f042309dd1c54767d60d111c445298e081e726389bbce2048171613c4d1c0`
  (102 file, đóng băng ở detached clean checkout); evidence commit `267c195a`; consumer/guard sync + clean-gate base
  `838237fe`.
- `CACHE_VERSION` 118; semantic environment `b1714b566e25c912…`; mặc định `LLM_ONLY`; 0 model call; 0 screenshot.
- Thay đổi của người dùng `D frontend/public/favicon.svg` được giữ ngoài staging.
- Duyệt hình vẫn **NOT_APPROVED**; D5 mobile vẫn mở.

## Cleanup đã khép

- Đã phân loại 180/180 report, 13.174/13.174 file artifact và 3.097/3.097 folder path.
- Giữ 167 report và 10.650 artifact có consumer/claim/tái lập cụ thể. Xoá phần Tin học retire: 13 report,
  2.523 artifact và 2 test pin; khôi phục được từ commit `4acd1f61`.
- Tổ chức 167 report: 33 cạnh package đo, 123 trong `evaluation/reports/`, 11 ngoại lệ path-bound; 167/167 blob
  report giữ nguyên byte. Đổi tên `CURRENT_ARCHITECTURE_GAP_AUDIT.md` thành
  `architecture-gap-audit-2026-09.md` theo kiểu R100.
- Gộp `docs-cleanup-2026-10-08` và `docs-organization` vào run này rồi xoá hai folder dư. Hai manifest và log phép
  kiểm độc lập vẫn giữ riêng dưới `run-artifact-cleanup.json`, `run-report-organization.json` và `diagnostics/`.
- Giữ `n04-targeted-rejection-registry-v2-preregistration` vì scripts/tests dùng N04 + registry V2 và 14 artifact tự
  ghim path; giữ các package `second-family-*` vì correction/preregistration/live-reconciliation chain còn được registry,
  scripts và tests sử dụng. Không dùng nhãn historical/frozen làm lý do độc lập.
- Prompt/IR và `semantic_*` không bị gỡ trong lượt này; caller evidence được để cho issue riêng
  `ISSUE-ARCH-INFORMATICS-MODEL-SURFACE-AND-IR-VOCABULARY`.

## Kiến trúc và lát cắt backend

`docs/ARCHITECTURE_MAP.md` ghi bảng request → Scene3D: đường ảnh có checkpoint; `RequestContract`; route mặc định
LLM sinh `SemanticProgram`; validator/interpreter/kernel và các cổng tất định; response envelope/store/frontend.
FactGraph/compiler chỉ là đường opt-in, không phải compiler-first đã hoàn tất. Tag lightweight
`SEMANTIC_PROGRAM_CONTRACT_V1` vẫn là mốc lịch sử tại `8dbd5bc7`; runtime authority là Pydantic + schema được đồng bộ.

Lát cắt duy nhất đóng `ISSUE-ARCH-MISSING-SIZE-REASON-ON-AFFINE-CHART`: với thể tích chóp tam giác đều T8 trong miền
đóng, cổng giả định lần theo phụ thuộc thực `V = sqrt(3)*b²*h/12`, nêu `AB` và/hoặc `chiều cao` còn thiếu, rồi vẫn trả
`unsupported / ASSUMPTION_DETERMINES_ANSWER / SOURCE`. Caller thật:
`POST /api/analyze` → `pipeline` → `semantic_program.route` → `assumption_gate`. Không đoán theo tên họ, không đổi ca
mâu thuẫn thành thiếu dữ kiện, không phục vụ Scene3D khi chưa đủ dữ kiện.

## Kiểm chứng

Detached clean worktree tại `838237fe`, temp nằm ngoài checkout:

- Backend: **7239 passed, 1 skipped, 2 deselected**; log `diagnostics/final-backend.log`, exit code 0.
- Frontend: **67 files / 1023 tests passed**; `tsc -b` + Vite production build đạt.
- Docs audit: PASS; 0 link hỏng, 0 stale path, 167 report catalogued, không file gốc chưa phân lớp.
- Candidate verify: `7f3f042309dd1c54…` / 102 file; cache identity verify: 118 / `b1714b566e25c912…`.
- `git diff --check` sạch; detached checkout sạch trước/sau gate.

`diagnostics/final-backend-temp-acl-failed.log` chỉ là lần thử không hợp lệ: sandbox từ chối tạo basetemp trong
checkout và lệnh chạm timeout; không được tính là kết quả test. Sau khi chuyển temp ra ngoài checkout, gate ở trên đạt.

## Nhiệm vụ sản phẩm kế tiếp duy nhất

Người dùng duyệt gói hình hiện có của `exact-dimensions`, `regular-triangular-pyramid-w01` và W5/W4, đồng thời chốt
phương án D5 mobile. Không mở thêm cleanup, prompt/IR hay họ hình trước quyết định này.
