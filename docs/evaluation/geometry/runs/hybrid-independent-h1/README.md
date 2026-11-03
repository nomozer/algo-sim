# Run `hybrid-independent-h1`

Hồ sơ chuẩn bị, tiền đăng ký, giải quyết quy tắc chấm Strict vs Semantic, đề xuất ngân sách và phán quyết kiểm soát chuyển đổi cho phép đo độc lập `H-1` bắt cặp `HYBRID` vs `LLM_ONLY` thuộc Master Epic `ALGOSIM_MASTER_HYBRID_BACKEND_REPLACEMENT` (**backend only**, `frontend/**` không chạm, `0` live provider calls).

## Danh mục tài liệu & biên nhận

1. [`H1_AUTHORING_HANDOFF.md`](H1_AUTHORING_HANDOFF.md) — Gói hướng dẫn biên soạn 60 đề hình học tiếng Việt độc lập (`45 SERVE` + `5/5/5 REFUSE`), hoàn toàn cách ly khỏi danh sách lỗi phát triển C25/C26.
2. [`H1_PREREGISTRATION.md`](H1_PREREGISTRATION.md) — Tiền đăng ký danh tính candidate `180db769` (`d331e75b`, `276fc548…`), quy tắc ba tầng **Mathematical / Semantic Goal (`h1-section-determination-equivalence/1`) / Strict Contract**, giao thức bắt cặp §7, thống kê và quy kết lỗi 11 nhóm.
3. [`H1_CORPUS_INTEGRITY.json`](H1_CORPUS_INTEGRITY.json) — Biên nhận máy trạng thái toàn vẹn corpus (`H1_AUTHORING_INDEPENDENCE = NOT_ESTABLISHED`, `H1_MEASUREMENT = NOT_MEASURED`, khóa mã băm candidate & runtime).
4. [`PAIRED_LIVE_BUDGET_PROPOSAL.md`](PAIRED_LIVE_BUDGET_PROPOSAL.md) — Tính toán ngân sách dựa trên telemetry C26 & `LLM_ONLY` (`max_requests = 300`, chi phí thực tế dự kiến `$1.50 – $2.00`, đặt chỗ preflight `max_usd = 52.0`) kèm [`paired-live-owner-approval.template.json`](paired-live-owner-approval.template.json) (`PENDING_OWNER_DECISION`).
5. *(Chưa tạo `H1_PAIRED_LIVE_EVALUATION_REPORT.md` vì chưa có corpus độc lập và ngân sách được duyệt để đo thật).*
6. [`HYBRID_CUTOVER_DECISION.md`](HYBRID_CUTOVER_DECISION.md) — Báo cáo tổng hợp và phán quyết hiện hành (`HYBRID_CUTOVER_BLOCKED`, `LEGACY_REMOVAL_BLOCKED`), kế hoạch cutover/rollback/dọn legacy khi đạt GO và checklist 2 đầu vào cần Owner cung cấp.
7. [`c26-three-tier-verification.json`](c26-three-tier-verification.json) & [`run.json`](run.json) — Biên nhận kiểm chứng chỉ-đọc quy tắc ba tầng trên 70 dòng C26 (không sửa nhãn lịch sử) và metadata của run.
