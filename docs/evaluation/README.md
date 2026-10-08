# evaluation/ — bằng chứng thực thi

> Artifact đo (JSON, log, ảnh, báo cáo của run) — nội dung **bất biến khi còn được dùng làm bằng chứng** (`../../AGENTS.md` §4). Thẩm quyền tra
> cứu là [`../EVIDENCE_INDEX.md`](../EVIDENCE_INDEX.md) (wave → báo cáo → artifact → `CORRECTED_BY`); file này chỉ chỉ
> đường. Tuyên bố được phép rút từ các artifact này: [`../research/CLAIM_EVIDENCE_MAP.md`](../research/CLAIM_EVIDENCE_MAP.md).

## Bố cục

| vùng | nội dung |
|---|---|
| [`geometry/runs/`](geometry/runs/) | một thư mục / run từ w09 (`wNN-short-slug` tới w20, rồi `<task-slug>-wNN`; từ 2026-10-07 tên theo việc — `exact-dimensions`, `repo-cleanup`, `docs-cleanup`; luật hiện hành ở [`RUN_NAMING.md`](RUN_NAMING.md), run cũ giữ tên); run mới có `report.md`, `handoff.md`, `run.json`, `inputs/`, `diagnostics/` (run cũ viết hoa: `REPORT.md`, `RUN.json`, `MANIFEST.json`) |
| [`geometry/photo-problem-to-scene/`](geometry/photo-problem-to-scene/) | package các wave đề-từ-ảnh và đo live 2026-09-13 … 09-24; report đăng ký nằm trong package tương ứng |
| `geometry/<tên-wave>/` khác | artifact các wave hình học 2026-08-24 … 09-27 (`thesis-final-acceptance/`, `curved-acceptance-v3/`, `holdout/`, …) |
| [`reports/`](reports/) | báo cáo đánh giá lịch sử theo chủ đề không có package run riêng; tên rõ chức năng được giữ |
| `semantic-benchmark/` | benchmark SEALED thời Tin học vẫn được `CORRECTNESS.md` dùng, đồng thời chứa candidate register sống; giữ vì consumer cụ thể |
| [`HISTORICAL_REPORTS.md`](HISTORICAL_REPORTS.md) | catalog **đóng** 167 báo cáo cũ theo chủ đề và đường dẫn vật lý hiện hành |
| [`AUDIT_ARTIFACT_MANIFEST.md`](AUDIT_ARTIFACT_MANIFEST.md) | nguồn gốc bảy bộ artifact audit W4B-0 |

### Thư mục bằng chứng ngoài `geometry/` — đọc gì ở đâu

Run `docs-cleanup-2026-10-08` đã đọc lại nội dung và consumer. Các nhóm Tin học không còn phục vụ sản phẩm,
nghiên cứu hiện hành hoặc tái lập cần giữ đã bị gỡ; bảng dưới chỉ còn ngoại lệ có consumer cụ thể.

| thư mục | nội dung | còn được trích bởi mã/test |
|---|---|---|
| `integration/` | **hình học**: hành trình tích hợp sản phẩm khối cong (`journey.json`, `curved-product.json`, ảnh cầu/trụ/nón) | có (9 file) |
| `prompt-freeze/` | bản đóng băng prompt `analyze.md`/`simulate.md` của hệ Tin học | không |
| `semantic-benchmark/` | hồ sơ SEALED 40 (custodian) và **`EVALUATION_CANDIDATE.json` — sổ candidate SỐNG** do `freeze_evaluation_candidate.py` ghi | có (10 file) |

`prompt-freeze/` chưa xử lý trong lượt này vì người dùng tách việc gỡ prompt/IR sang lượt sau. `integration/` giữ tên
do hai báo cáo bằng chứng còn dùng đường dẫn tuyệt đối trong nội dung; đổi tên sẽ phá liên kết hoặc buộc sửa byte.

## Báo cáo của một wave nằm ở đâu

- Run mới (luật 2026-10-07): `report.md` / `handoff.md` trong thư mục run; w09 … w20 và các run `<task-slug>-wNN`:
  `REPORT.md` / `HANDOFF.md`.
- Trước đó: tra [`HISTORICAL_REPORTS.md`](HISTORICAL_REPORTS.md) hoặc `../EVIDENCE_INDEX.md`; report đã đăng ký
  nằm cạnh package artifact, report chủ đề ở `reports/`. Mười một ngoại lệ còn ở gốc vì contract được code trích
  trực tiếp hoặc link tương đối byte-locked cần đúng độ sâu; danh sách ngoại lệ nằm trong run `docs-organization`.

## Run gần nhất

| run | chủ đề |
|---|---|
| [`docs-organization`](geometry/runs/docs-organization/) | tổ chức cuối 167 báo cáo, mapping cũ → mới, kiểm byte/link/full backend; không đổi sản phẩm |
| [`cuboid-merge`](geometry/runs/cuboid-merge/) | gói duyệt hình A–F trước khi merge; ảnh W18 chứng minh chuyển tiếp sang candidate `b2d4187a` (fixture tái sinh offline chỉ khác hai trường danh tính); 0 thay đổi sản phẩm |
| [`cuboid-acceptance`](geometry/runs/cuboid-acceptance/) | đối chiếu 24 bất biến có con trỏ chết của `ARCHITECTURE_MAP` §5 (9 đang khoá, 1 chưa đủ bằng chứng, 14 lịch sử, 0 vi phạm); 0 thay đổi sản phẩm |
| [`cuboid-final-review`](geometry/runs/cuboid-final-review/) | lượt chốt của việc cuboid (không đánh số wave): rà soát trọn tài liệu (lịch sử Tin học tách nguyên văn sang `legacy/`), luật đánh số wave theo từng việc, thẻ từ chối §17 nói "chưa kiểm chứng được phép dựng" |
| [`w20-cleanup-premerge`](geometry/runs/w20-cleanup-premerge/) | đích quan hệ đặt bằng toạ độ bị từ chối (amendment §17), test không ghi bằng chứng đông cứng, dọn kho có bằng chứng |
| [`w19-docs-organization`](geometry/runs/w19-docs-organization/) | tổ chức lại tài liệu, bản đồ tuyên bố ↔ bằng chứng, catalog đóng (0 thay đổi sản phẩm) |
| [`w18-binding-focus`](geometry/runs/w18-binding-focus/) | phép dựng điểm gắn với quan hệ của đề, nhãn tập trung, nhân chứng khoảng cách |
| [`w17-operation-annotations`](geometry/runs/w17-operation-annotations/) | phép cắt gắn câu cắt, nhãn số đo trên hình |
| [`w16-premerge-closure`](geometry/runs/w16-premerge-closure/) · [`w15-assumption-closure`](geometry/runs/w15-assumption-closure/) | đóng lỗ chứng chỉ; chứng chỉ giả định |
| [`w14-generic-formation-assumption`](geometry/runs/w14-generic-formation-assumption/) · [`w13-geometry-preregistration`](geometry/runs/w13-geometry-preregistration/) | dựng hình theo lớp; kiểm kê năng lực + tiền đăng ký |
| w09 … w12 | occlusion, playback, công thức, dòng thời gian — xem `../EVIDENCE_INDEX.md` |

Kết luận và trạng thái duyệt của từng run: `../CURRENT_STATE.md` (wave cuối) và `../EVIDENCE_INDEX.md`.

## Hai lớp bằng chứng — không trộn

**Live** (có lượt gọi provider: lượt nghiệm thu cuối 2026-09-08, lượt V3 2026-09-05, các probe đăng ký trước) và
**offline** (0 lượt gọi: mọi run w09–w20 và `cuboid-final-review`). Số offline không nói gì về hành vi của mô hình; số live chỉ mô tả candidate
lúc đo. Cột *Commit / candidate đo* của bản đồ tuyên bố ghi rõ từng trường hợp.
