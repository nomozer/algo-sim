# evaluation/ — bằng chứng thực thi

> Artifact đo (JSON, log, ảnh, báo cáo của run) — **bất biến sau khi commit** (`../../AGENTS.md` §4). Thẩm quyền tra
> cứu là [`../EVIDENCE_INDEX.md`](../EVIDENCE_INDEX.md) (wave → báo cáo → artifact → `CORRECTED_BY`); file này chỉ chỉ
> đường. Tuyên bố được phép rút từ các artifact này: [`../research/CLAIM_EVIDENCE_MAP.md`](../research/CLAIM_EVIDENCE_MAP.md).

## Bố cục

| vùng | nội dung |
|---|---|
| [`geometry/runs/`](geometry/runs/) | một thư mục / run từ w09 (`wNN-short-slug`, luật ở [`RUN_NAMING.md`](RUN_NAMING.md)); mỗi run có `README.md`, `REPORT.md`, `HANDOFF.md`, `RUN.json`, `MANIFEST.json`, `inputs/`, `results/`, `diagnostics/` |
| [`geometry/photo-problem-to-scene/`](geometry/photo-problem-to-scene/) | artifact các wave đề-từ-ảnh và đo live 2026-09-13 … 09-24 (báo cáo ở gốc `docs/`) |
| `geometry/<tên-wave>/` khác | artifact các wave hình học 2026-08-24 … 09-27 (`thesis-final-acceptance/`, `curved-acceptance-v3/`, `holdout/`, …) |
| `m16/` … `m20/`, `semantic-*/`, `tier2-live-pilot/`, … | artifact giai đoạn Tin học (trước đổi đề 2026-08-24) |
| [`HISTORICAL_REPORTS.md`](HISTORICAL_REPORTS.md) | catalog **đóng** các báo cáo wave cũ nằm ở gốc `docs/`, theo chủ đề |
| [`AUDIT_ARTIFACT_MANIFEST.md`](AUDIT_ARTIFACT_MANIFEST.md) | nguồn gốc bảy bộ artifact audit W4B-0 |

## Báo cáo của một wave nằm ở đâu

- Từ w09: `REPORT.md` / `HANDOFF.md` trong thư mục run.
- Trước đó: một file `docs/<TÊN_WAVE>.md` ở gốc — tra [`HISTORICAL_REPORTS.md`](HISTORICAL_REPORTS.md) hoặc
  `../EVIDENCE_INDEX.md`. Danh sách ấy đóng: wave mới **không** thêm báo cáo vào gốc `docs/`.

## Run gần nhất

| run | chủ đề |
|---|---|
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
**offline** (0 lượt gọi: mọi run w09–w19). Số offline không nói gì về hành vi của mô hình; số live chỉ mô tả candidate
lúc đo. Cột *Commit / candidate đo* của bản đồ tuyên bố ghi rõ từng trường hợp.
