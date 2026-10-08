# docs-cleanup — kiểm kê

Mỗi hàng: đường dẫn → nội dung → consumer → hành động → lý do. Consumer đo bằng `git grep` tên file trên toàn kho
(trừ chính `docs/legacy/`), tách consumer **sống** (mã, test, runner, tài liệu sống) khỏi bản kiểm kê đóng băng của run cũ
(`runs/w19-docs-organization/inventory/*.json`, `runs/w20-cleanup-premerge/inventory/*.json`,
`runs/cuboid-final-review/inventory/*.json` — chúng ghi đường dẫn tại commit của chúng, không cần file còn tồn tại).
Bản gỡ còn nguyên trong git history (`git show 2a7179a9:<đường dẫn>`).

Mức đọc: mọi file `docs/legacy/` được mở; với file dài (plan/spec 100–2154 dòng, ba file tách nguyên văn 130–434 KB)
đọc tiêu đề, mục tiêu/phạm vi, trạng thái và toàn bộ heading, rồi đọc kỹ phần quyết định giữ/bỏ phụ thuộc vào
(§4 của quyết định cuboid, §1.1/§3 của thiết kế route, §2 của roadmap chuyển đề) — không đọc từng dòng mọi file.

## A. `docs/legacy/` — 42 file lúc bắt đầu

| đường dẫn (dưới `docs/legacy/`) | nội dung | consumer sống | hành động | lý do |
|---|---|---|---|---|
| `superpowers/plans/2026-07-15-m10-3d-ped-protocol-encapsulation.md` + `specs/…-design.md` | module mạng `network.protocol_encapsulation` (TCP/IP, 3D) | không | **xoá** | miền mạng Tin học đã gỡ khỏi mã; không nghĩa vụ tái lập |
| `superpowers/specs/2026-07-15-m9-ux3-home-preview-design.md` | trang chủ + tranh preview cho các bài thuật toán | không | **xoá** | preview Tin học còn sót được theo dõi ở `ISSUE-ARCH-SHELL-INFORMATICS-RESIDUE`, không cần thiết kế cũ |
| `superpowers/plans/2026-07-16-m13-generic-semantic-soundness.md` + `specs/…-design.md` + `specs/2026-07-16-m13-semantic-matrix.md` | DSL generic, ba trạng thái nguồn số, cổng thuật toán | không | **xoá** | `simulation/dsl/`, `generic` đã gỡ; nguyên tắc right-or-refuse sống ở `CORRECTNESS.md` |
| `superpowers/plans/2026-07-18-m14-…` + `specs/2026-07-17-m14-…-design.md` | họ năng lực, descriptor, `catalog.py` | không | **xoá** | catalog/family Tin học đã gỡ |
| `superpowers/plans/2026-07-18-m15-…` + `specs/…-design.md` | taxonomy cơ chế, hợp đồng năng lực công khai | không | **xoá** | như trên |
| `superpowers/plans/2026-07-19-m16-…` + `specs/…-design.md` + `specs/2026-07-19-m16-evaluation-audit.md` | đánh giá LLM toàn diện trên catalog Tin học | không | **xoá** | `app/evaluation/` đã gỡ; artifact đo bất biến ở `docs/evaluation/m16/` |
| `superpowers/specs/2026-07-21-m17-lite-proposal.md` + `…-m17-wave2a-tree-traversal.md` | đề xuất M17-Lite, họ duyệt cây | không | **xoá** | miền Tin học; bằng chứng `m17/` vẫn ghim |
| `superpowers/plans/2026-08-17-w13-bo-hinh-thuc-hoi-dap.md` | gỡ `predict` khỏi 11 target thuật toán | không | **xoá** | quyết định còn ràng buộc (không phán đúng/sai trên thao tác người học) đã khoá ở `frontend/src/simulations/no-verdict.test.ts` + `ARCHITECTURE_MAP §5` #27; phần còn lại nói về target đã gỡ |
| `superpowers/specs/2026-08-20-semantic-program-generative-route-design.md` | thiết kế gốc route Semantic Program (Tin học, IR thuật toán, 2D) | `RULES.md` luật 11 (§3.3), `CODE_INDEX`, `STATUS_LEDGER` (§0-2026-08-20 hết hiệu lực) | **chuyển + đổi tên** → `architecture/SEMANTIC_PROGRAM_ROUTE_DESIGN.md` | thiết kế đã thực thi, còn được trích; phần còn hiệu lực đã ở `RULES.md` + `ARCHITECTURE_MAP §5` #31–#34 nên không đưa về hiện hành; thư mục mang tên công cụ hết lý do tồn tại |
| `superpowers/plans/2026-08-20-semantic-program-generative-route.md` | kế hoạch triển khai route + giao thức niêm phong SEALED | `STATUS_LEDGER` | **chuyển + đổi tên** → `architecture/SEMANTIC_PROGRAM_ROUTE_PLAN.md` | đi cặp với thiết kế; Task 1 là giao thức niêm phong của bộ mà `test_benchmark_seal.py` còn ghim |
| `architecture/CUBOID_CUBE_CONTRACT_DECISION.md` | contract hình hộp chữ nhật / lập phương / lăng trụ đứng đáy vuông | không (README legacy ghi "không ai tham chiếu") | **chuyển** → `docs/architecture/` + khối trạng thái | đối chiếu mã: `PrismTopologySpec`, lược đồ `analyze_contract`, luật cube/cuboid, `OBLIQUE_LATERAL_EDGE_FOR_CUBOID` khớp — contract đang hiệu lực đặt nhầm chỗ; một khác biệt ghi trong khối trạng thái |
| `architecture/NEXT_VERTICAL_SLICE_DECISION.md` | chọn cuboid/cube làm lát cắt kế tiếp | không | **xoá** | đã thực thi; chọn họ hình nay ở `ROADMAP.md §0.2` |
| `geometry/CAPABILITY_GAP_AUDIT.md` | cách đọc + bảng (2026-08-30) của `audit_geometry_capability.py` | `CODE_INDEX` (mục của script), `evaluation/geometry/SPATIAL_DISTANCE_EXTENSION.md` | **giữ** | script còn chạy; README legacy ghi bảng là ảnh chụp |
| `geometry/CURRENT_SYSTEM_MAPPING.md` | giữ/sửa/bỏ từng thư mục lúc đổi đề | không | **xoá** | đã thực thi (repo-cleanup khép phần cuối) |
| `geometry/GEOMETRY_ARCHITECTURE_GAP_REPORT.md` | khoảng trống kiến trúc Phase 1 tại `5b7e921` | không | **xoá** | ba khoảng trống đã đóng; kéo-thả nay ngoài phạm vi (`STATUS_LEDGER §0-2026-08-24`) |
| `geometry/GEOMETRY_ROADMAP.md` | phạm vi và bảy giai đoạn lúc đổi đề | không | **xoá** | thay bởi `ROADMAP.md`; danh sách ngoài phạm vi còn hiệu lực **chép sang** `STATUS_LEDGER §0-2026-08-24` (mặt tròn xoay ghi rõ là đã mở một phần) |
| `geometry/MIGRATION_PLAN.md` | kế hoạch di trú bảy bước | không | **xoá** | đã thực thi |
| `geometry/PHASE6_SIMULATION_SEMANTICS_REPORT.md` | audit "mô phỏng hay phát lại", so GeoGebra | không | **xoá** | dẫn tới các wave playback/sư phạm đã làm; không bản thảo nào trích |
| `geometry/SIMULATION_FOUNDATION_AUDIT.md` | audit nền mô phỏng 3D (chưa code) | không | **xoá** | đã thực thi |
| `geometry/SIMULATION_STATE_DESIGN.md` | thiết kế `GeometryScene`/`SimulationState` (5B) | không | **xoá** | luật còn hiệu lực ("chiếu, không tính", "không float") nằm ngay trong docstring `semantic_program/simulation_state.py`; phần kéo-thả đã ngoài phạm vi |
| `REPOSITORY_MAP.md` | bản đồ vị trí trước đổi đề | chỉ báo cáo lịch sử `THESIS_RESULTS_ANALYSIS_AND_CHAPTER_DRAFTING.md` (bất biến, trích tại commit của nó) | **xoá** | thay bởi `docs/README.md` + `CODE_INDEX.md` |
| `RULES_v0.3.md` | thiết kế v0.3 hệ Tin học | `RULES.md` dòng 8, khối (28) của `rules-hygiene.test.ts` | **xoá** (commit riêng `8c66249d`) | không tài liệu/bản thảo nào dùng; khối test chỉ canh chính bản lưu ấy; test (27) giữ |
| `README.md` | mục lục legacy | cổng điều hướng (`test_inv_24`) | **giữ, cập nhật** | bảng theo hiện trạng mới |
| `CURRENT_STATE_HISTORY.md` | nhật ký CURRENT_STATE cũ | `CURRENT_STATE.md`, `AI_CONTEXT_BUNDLE.md`, báo cáo lịch sử trích "CURRENT_STATE §n" | **giữ** | đích của các trích dẫn cũ |
| `*_INFORMATICS_ERA.md` (6) + `CODE_INDEX_REMOVED_ENTRIES.md` | khối tách nguyên văn từ bảy tài liệu sống | tài liệu sống để lại dòng trỏ; `runs/cuboid-final-review/inventory/HISTORY_SPLIT.json` (sha256 từng khối) | **giữ** | chuỗi bằng chứng của run `cuboid-final-review` |
| `research/CLAIM_EVIDENCE_MATRIX.md`, `CLAIM_TO_EVIDENCE_MAP.md`, `THESIS_READINESS.md` | bảng tuyên bố cũ, định nghĩa đính chính D-1…D-4 | `EVIDENCE_INDEX.md` (chuỗi `CORRECTED_BY`), `OPEN_ISSUES.md`, `CODE_INDEX.md` | **giữ** | chuỗi đính chính đang được trích |

Kết quả: 42 → 15 file; `superpowers/` (2 thư mục) hết.

## B. Tên test và tiêu đề

Bảng cũ → mới: `docs/evaluation/RUN_NAMING.md` mục *Đã đổi (run `docs-cleanup`)*. Commit riêng `a993aa8f`, không đổi
logic. pytest: 123 hàm, 17 file, thu thập 7242 trước/sau, không trùng node id; vitest 74 tiêu đề (32 file); node:test 44
tiêu đề (`compiler-scene-replay-lib.node-test.mjs`). Giữ có lý do: `test_wave0_*`/`test_wave1_*`, `test_gm10_*`; hằng
`TEN_TU_CHOI_W17`/`W17_STATES` trong `build_scene3d_visual_evidence.py` (định danh mã, ngoài phạm vi tên file/test).

## C. CSS chết (commit `c1a291ba`)

`frontend/src/styles/global.css`: 12 lớp, 17 luật — `geo3d-explorer`, `-explorer-main`, `-panel`, `-panel-title`,
`-inspect`, `-inspect-list`, `-actions`, `-section`, `-heading` (bố cục bảng trước `BangNoi`), `geo3d-focus` (dải đã gỡ),
`geo3d-lead`, `geo3d-tree-type`. Không module sản phẩm nào render chúng (`geo3d-focus`/`geo3d-lead` chỉ có trong test kiểm
vắng mặt; `geo3d-tree-type` chỉ do script tay `demo-geometry-interaction.mjs` đọc). Kiểm bằng parser: 528 → 511 luật, 0
luật thêm, mọi luật giữ lại trùng nguyên văn.

## D. Thư mục rỗng — local (Git không theo dõi thư mục rỗng)

| thư mục | trước khi dọn | hành động |
|---|---|---|
| `docs/legacy/superpowers/plans/`, `specs/`, `superpowers/` | rỗng sau khi chuyển/xoá (đã liệt kê kể cả file ẩn) | `rmdir` |
| `backend/app/validation/`, `backend/app/evaluation/` (+ `datasets/`) | chỉ `__pycache__/*.cpython-312.pyc` (gitignore) của gói đã gỡ ở `88769dc5`; Python không import `.pyc` mồ côi | xoá đúng các `.pyc` đã liệt kê rồi `rmdir` |

## E. Chưa theo dõi / rỗng — giữ, có lý do

| đường dẫn | lý do giữ |
|---|---|
| `frontend/public/` (rỗng) | rỗng vì thay đổi của người dùng (xoá `favicon.svg`, không stage) |
| `frontend/.impeccable/live/*` (rỗng), `.impeccable/` | nháp của công cụ thiết kế, gitignore, không do việc này tạo |
| `.superpowers/` (108 mục theo `AI_CONTEXT_BUNDLE §5`) | người dùng đã quyết giữ (brief `cuboid-acceptance`); gitignore |
| `.secrets/`, `data/` | dữ liệu người dùng / bí mật — không mở |

## F. Mức đọc của lần cleanup đầu (đã được §G thay thế)

- **Đã đọc**: toàn bộ `docs/legacy/` (mức đọc ở đầu file); tên mọi file/thư mục được theo dõi dưới `backend/`,
  `frontend/`, `.claude/`, cấu hình gốc (quét mã lượt `m*`/`w*`/`phase*`/`wave*`/`v*`); mọi tên test pytest, vitest, node:test;
  bố cục `docs/evaluation/` (từng thư mục ngoài `geometry/`, mở tệp đầu của mỗi thư mục); CSS `geo3d-*` so với mọi tham chiếu.
- **Không đọc lại**: mã `backend/app`, `frontend/src` đã rà ở run `repo-cleanup` — không có dấu hiệu liên quan ngoài tên
  test và CSS ở trên.
- **Chưa đọc từng file ở lần đầu**: 180 báo cáo lịch sử ở gốc `docs/`. Quy tắc khi đó được hiểu là cấm sửa/chuyển/xoá; tên hiển thị và chủ đề
  đã có ở `docs/evaluation/HISTORICAL_REPORTS.md` (kiểm mẫu các hàng mang mã `W12_REMAINING`, `G4_…`, `PHASE_2/3_…`: có
  tiêu đề mô tả). Đọc nội dung từng báo cáo không đổi được hành động nào.
- **Chưa đọc nội dung ở lần đầu**: artifact trong các thư mục `docs/evaluation/**`; chỉ đọc bố cục để viết lớp tên hiển thị ở
  `docs/evaluation/README.md`.

## G. Đính chính mức đọc và cleanup vật lý tiếp nối

Hai dòng "không đọc" ở §F là giới hạn của lần đầu, **không còn là trạng thái cuối**. Lần kiểm độc lập có manifest
`run-artifact-cleanup.json` đã đọc/phân loại **180/180 report**, **13.174/13.174 file** và **3.097/3.097 folder path**;
chi tiết nhóm đồng nhất, consumer, claim và giá trị tái lập đã được nhập vào bảng dưới. Kết quả vật lý: giữ 167 report
và 10.650 artifact; xoá 13 report + 2.523 artifact + 2 test pin snapshot Tin học; đổi `manual-demo` →
`geometry-demo`, `manual-demo-5` → `point-projection-check` (22 file). Mọi deletion khôi phục từ `4acd1f61`.

| nội dung/nhóm | consumer | kết luận/chương dùng | tái lập | hành động |
|---|---|---|---|---|
| 167 report hình học/sản phẩm/nghiên cứu | `EVIDENCE_INDEX`, claim map, report catalog và package tương ứng | kiến trúc, correctness, chương kết quả/giới hạn | lớp diễn giải của raw artifact | giữ; lần tổ chức sau chuyển 33 report cạnh package, 123 vào `evaluation/reports`, 11 ngoại lệ root |
| 13 report + 2.523 artifact Tin học retire (`curriculum-ui-admission`, m16–m20, `semantic-l5a/vnext`, audit UI catalog, demo lặp) | không còn consumer sản phẩm/nghiên cứu; test pin tự thân đã gỡ | không còn claim luận văn hình học | producer/evaluator đã retire | xoá có ledger; Git là đường khôi phục |
| `semantic-benchmark`, `integration`, evidence geometry | freeze/verify scripts, tests, thesis claims, report path-bound | SEALED/candidate, product integration và các claim C1–C8/B2/D5/D6 | bắt buộc | giữ nguyên byte; `integration` giữ tên vì consumer/path trong evidence |
| `prompt-freeze` | chưa có caller sản phẩm | việc prompt/IR riêng | cần cho quyết định sau | giữ tạm, không nhập lượt này |

Lần tổ chức độc lập có manifest `run-report-organization.json` bảo toàn **167/167 blob report**, thực hiện 156 move
`R100`, rồi full backend sạch đạt 7.234 passed / 1 skipped / 2 deselected. Log nguyên byte ở
`diagnostics/report-organization-backend.log` và exit code ở file cùng tên. Hai lần đo vẫn là hai manifest/log riêng;
chỉ hồ sơ trách nhiệm được hợp nhất.

## H. Audit tên và tài liệu kiến trúc

| mục | phân loại/căn cứ | hành động |
|---|---|---|
| `CURRENT_ARCHITECTURE_GAP_AUDIT.md` | snapshot 2026-09-03; test/cache comments còn trích kết luận §12 nhưng chữ `CURRENT` gây hiểu nhầm | đổi path byte-identical → `evaluation/reports/architecture-gap-audit-2026-09.md`; giữ title trong blob lịch sử |
| `n04-targeted-rejection-registry-v2-preregistration/` | package đang được scripts/tests đọc; `N04` là case preregistered, `V2` là version registry; 14 file tự ghim path | giữ tên: đổi sẽ buộc sửa manifest/evidence đang dùng, trái bảo toàn byte |
| các package `second-family-*` | chuỗi chọn họ → preregistration → correction → live retry/reconciliation; scripts, test và research registry trỏ từng package | giữ: "second family" là danh tính thí nghiệm trong correction chain, không chỉ nhãn lịch sử |
| tên report dài còn lại | report snapshot đã được catalog theo chức năng; phần lớn nằm cạnh package có run identity | giữ blob/tên khi đổi không cải thiện caller hoặc sẽ phá path-bound evidence; chỉ đổi tên sai nghĩa `CURRENT` ở trên |
| `SEMANTIC_PROGRAM_ROUTE_DESIGN/PLAN` | thiết kế gốc đã thực thi; RULES §11 trích design §3.3, plan ghi giao thức SEALED mà test còn ghim | giữ trong `legacy/architecture`, không coi là contract hiện hành; authority hiện tại là code/test + `ARCHITECTURE_MAP` |
| tag `SEMANTIC_PROGRAM_CONTRACT_V1` | lightweight tag → commit `8dbd5bc7`, thêm contract/validator + hai schema V1; contract đã tiến hoá qua nhiều commit | giữ tag như mốc lịch sử; runtime không resolve tag, contract hiện hành do Pydantic/schema-sync sở hữu |

## I. Folder hợp nhất

`docs-cleanup-2026-10-08` và `docs-organization` không còn là hai nơi trách nhiệm song song. Manifest độc lập được
chuyển nguyên byte thành `run-artifact-cleanup.json` và `run-report-organization.json`; log full backend chuyển vào
`diagnostics/`. `plan/inventory/report/handoff` duy nhất là các file tại run này. Reference đóng băng bên trong inventory
run cũ không được viết lại; link/consumer sống đều trỏ về `docs-cleanup`.
