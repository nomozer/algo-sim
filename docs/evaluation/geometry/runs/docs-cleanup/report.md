# docs-cleanup — báo cáo

Việc `docs-cleanup` (task `DOCUMENTATION_AND_NAMING_CLEANUP`), máy local, cùng nhánh `feat/regular-square-pyramid`,
bắt đầu ở `2a7179a9`. Metadata: `run.json`. Từng file đã xử lý, consumer và lý do: `inventory.md`. Bảng cũ → mới:
`docs/evaluation/RUN_NAMING.md` mục *Đã đổi (run `docs-cleanup`)*. 0 lượt gọi model, 0 ảnh chụp.

## 1. Đã làm

| việc | kết quả | commit |
|---|---|---|
| Tên test theo hành vi | 123 hàm pytest bỏ tiền tố `test_wNN_`/`test_phase3_` (4 đặt tên tay); 74 tiêu đề vitest, 44 tiêu đề node:test bỏ thẻ đầu; bộ chọn `-k w16/w17/w18` trong tài liệu sống thành đường dẫn file | `a993aa8f` (chỉ đổi tên) |
| CSS chết + chú thích | 12 lớp `geo3d-*` / 17 luật không module sản phẩm nào render; chú thích phạm vi danh mục của `offline-catalog.ts` | `c1a291ba` |
| `RULES_v0.3.md` | gỡ cùng khối test (28) chỉ canh chính bản ấy; test (27) giữ | `8c66249d` |
| `docs/legacy/` + Superpowers | 42 → 15 file: xoá 25 ở commit này (16 plan/spec M9–M17, W13; bảy tài liệu chuyển đề; quyết định lát cắt; REPOSITORY_MAP) + `RULES_v0.3.md` ở dòng trên, chuyển 2 (thiết kế + kế hoạch route Semantic Program → `legacy/architecture/`), đưa 1 về hiện hành (`CUBOID_CUBE_CONTRACT_DECISION.md` → `docs/architecture/`, mã còn cài đúng nó); danh sách ngoài phạm vi còn hiệu lực của roadmap chuyển đề chép sang `STATUS_LEDGER §0-2026-08-24` | `9efb8af6` |
| Hướng dẫn cấu trúc tài liệu | AGENTS §4 + `docs/README.md` §8 + `architecture/README.md`: thiết kế do skill sinh ⇒ `docs/architecture/` nếu là contract hiện hành, kế hoạch ⇒ `plan.md` của run; không `docs/superpowers/` (đã có `test_inv_23` chặn thư mục lạ); `docs/README.md` §8, `evaluation/README.md` theo luật tên run hiện hành | `9efb8af6` |
| Lớp tên hiển thị | bảng nội dung từng thư mục bằng chứng mang mã (`m16`…`m20`, `semantic-*`, `integration`, …) ở `evaluation/README.md` — tên giữ vì AGENTS §4 | `9efb8af6` |
| Hai issue Tin học | SHELL-RESIDUE: CSS chết + chú thích xong, chú thích xuất xứ giữ có lý do, còn `SamplePreview`/`threeD`/`specDrift`; MODEL-SURFACE: đọc lại caller — **sáu** prompt không loader (không phải bốn), `pipeline._call_json` không còn người gọi | `9efb8af6` |
| Candidate | đóng băng lại một lần ở `8c66249d` (worktree tách rời sạch, đường dẫn có dấu cách): product commit `be4b8287` → `8c66249d`, mã đo **không đổi** (102 file, `b4a33205…`) | `976e0eea` |
| Thư mục rỗng local | `docs/legacy/superpowers/{plans,specs}`, `backend/app/{validation,evaluation}` (chỉ `.pyc` gitignore của gói đã gỡ) | — (Git không theo dõi) |

## 2. Kiểm trong lúc sửa

- pytest: thu thập 7242/7244 (2 deselected) trước và sau đổi tên, không trùng node id; 17 file đổi tên: 792 passed.
- vitest 1032/1032 (68 file) sau đổi tên và sau gỡ CSS; node harness 97/97.
- CSS: parser 528 → 511 luật, 0 thêm, mọi luật giữ lại trùng nguyên văn, mọi luật gỡ chứa một lớp chết.
- Bộ kiểm tài liệu (`test_docs_information_architecture.py`) xanh sau khi viết `inventory.md`, trừ `test_inv_20` cho tới lần đóng
  băng lại (product commit đã dời) — xanh sau `976e0eea`.
- Cổng đầy đủ và cổng danh tính: `handoff.md` §2.

## 3. Bề mặt mô hình và cache

Không đổi: prompt, thẻ văn phạm, lược đồ analyze/synthesis, bảng năng lực, route, cổng. `CACHE_VERSION` giữ **117** — không
envelope nào đổi; khoá danh tính cache khớp nguyên (`diagnostics/freeze_8c66249d.log`). Candidate giữ băm `b4a33205…`;
khai báo độ lệch của run `repo-cleanup` vẫn đúng.

## 4. Còn lại, có lý do

| mục | vì sao còn | theo dõi |
|---|---|---|
| sáu prompt Tin học không loader, `_call_json`, nhánh `domain=None`, từ vựng container IR + renderer 2D | xoá = đổi bề mặt mô hình có băm + bump `CACHE_VERSION`; IR cấm đổi trong việc dọn | `ISSUE-ARCH-INFORMATICS-MODEL-SURFACE-AND-IR-VOCABULARY` (caller ghi từng file) |
| `SamplePreview` (11 id Tin học), `threeD`, `specDrift` | đổi cái giao diện hiển thị (lịch sử cũ) / hợp đồng shell — cần kiểm trực quan | `ISSUE-ARCH-SHELL-INFORMATICS-RESIDUE` |
| hằng `TEN_TU_CHOI_W17`, `W17_STATES` (`build_scene3d_visual_evidence.py`) | định danh mã nội bộ, ngoài phạm vi tên file/test | `RUN_NAMING.md` (giữ có chủ đích) |
| 180 báo cáo lịch sử ở gốc `docs/`, mọi `docs/evaluation/**` | bất biến (AGENTS §4); tên hiển thị ở catalog/README | `ISSUE-DOCS-HISTORICAL-REPORTS-AT-DOCS-ROOT` (INTENDED_LIMITATION) |
| `frontend/scripts/demo-geometry-interaction.mjs` đọc `.geo3d-tree-type` | script tay; trường `loai` luôn rỗng từ khi chip bị gỡ | `ISSUE-ARCH-SHELL-INFORMATICS-RESIDUE` |

## 5. Không gọi là "dọn toàn kho hoàn tất"

Đã đọc trọn nhóm được giao trừ: 180 báo cáo lịch sử ở gốc (không đọc từng file — bất biến, không hành động nào khả dĩ) và
nội dung artifact `docs/evaluation/**` (chỉ đọc bố cục). Mã `backend/app`/`frontend/src` không đọc lại ngoài tên test và
CSS (đã rà ở `repo-cleanup`). Chi tiết mức đọc: `inventory.md` §F.

## 6. Kết luận hợp nhất (thay thế giới hạn §4–§5)

Cleanup tiếp nối đã khép phần §5 từng để mở: 180/180 report và 13.174/13.174 artifact được phân loại; phần Tin học
hết consumer đã xoá, 167 report còn dùng được bố trí vật lý và kiểm byte. Hai run phụ không còn tồn tại; manifest/log
độc lập nằm trong run `docs-cleanup`. Tổng đã xoá ở lần artifact cleanup là 2.538 tracked file; tổng move tổ chức report
là 156; lần khép này chỉ gộp hồ sơ, đổi một report snapshot sang tên chức năng và cập nhật consumer.

Audit kiến trúc xác nhận Semantic Program vẫn là đường sản phẩm mặc định `LLM_ONLY`; tag V1 chỉ là mốc khởi tạo,
không phải contract runtime hiện hành. Chuẩn hoá quan hệ nguồn đã có caller thật, nên backend slice duy nhất của lượt
này đóng `ISSUE-ARCH-MISSING-SIZE-REASON-ON-AFFINE-CHART`: quyết định vẫn `unsupported`, nhưng ca thể tích T8 thiếu
kích thước nay nêu đúng đại lượng nguồn thay vì UNKNOWN. Vì envelope cache đổi, `CACHE_VERSION` tăng 117 → 118;
prompt/schema/model surface không đổi.
