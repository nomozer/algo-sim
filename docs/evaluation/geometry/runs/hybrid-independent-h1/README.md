# Run `hybrid-independent-h1`

Hồ sơ tiền đăng ký, chốt quy ước mục tiêu ngữ nghĩa **P1**, cải tiến cơ chế kiểm soát ngân sách an toàn theo từng request (`SafeCampaignBudget` dùng `decimal.Decimal` chính xác và khoá tương tranh), kiểm định độc lập corpus `H-1` và phán quyết kiểm soát chuyển đổi kiến trúc cho phép đo bắt cặp `HYBRID` vs `LLM_ONLY` thuộc Master Epic `ALGOSIM_MASTER_HYBRID_BACKEND_REPLACEMENT` (**backend only**, `frontend/**` và `backend/app/**` không chạm, `0` live provider calls).

## Danh mục tài liệu & biên nhận

1. [`H1_AUTHORING_HANDOFF.md`](H1_AUTHORING_HANDOFF.md) — Gói hướng dẫn biên soạn 60 đề hình học tiếng Việt độc lập (`45 SERVE` + `5/5/5 REFUSE`), cách ly khỏi danh sách lỗi phát triển C25/C26 và cấm sao chép/đổi tên đỉnh từ ví dụ mẫu.
2. [`H1_PREREGISTRATION.md`](H1_PREREGISTRATION.md) — Tiền đăng ký danh tính candidate `180db769` (`d331e75b`, `276fc548…`), chính sách kỹ thuật **P1** (`h1-section-determination-equivalence/1`) giữ nguyên tách biệt 3 tầng **Mathematical / Semantic Goal / Strict Contract**, mô hình ngân sách `SafeCampaignBudget`, giao thức bắt cặp §7 và ranh giới diễn giải thống kê.
3. [`H1_CORPUS_INTEGRITY.json`](H1_CORPUS_INTEGRITY.json) — Biên nhận máy trạng thái toàn vẹn corpus (`H1_AUTHORING_INDEPENDENCE = NOT_ESTABLISHED`, `H1_MEASUREMENT = NOT_MEASURED`, khóa mã băm candidate, `paired_harness_sha256 = 4ba15bc1…`, `equivalence_scorer_sha256 = 49bd9343…`).
4. [`PAIRED_LIVE_BUDGET_PROPOSAL.md`](PAIRED_LIVE_BUDGET_PROPOSAL.md) — Đề xuất ngân sách an toàn sau khi gỡ bỏ phép nhân worst-case thô ở preflight: `campaign_max_requests = 300`, `campaign_max_usd = 5.00` (chi phí thực tế dự kiến `\$1.50 – \$2.00`), đặt chỗ `Decimal` trước từng HTTP request kèm [`paired-live-owner-approval.template.json`](paired-live-owner-approval.template.json) (`PENDING_OWNER_DECISION`).
5. *(Chưa tạo `H1_PAIRED_LIVE_EVALUATION_REPORT.md` vì chưa có corpus độc lập và ngân sách được Owner phê duyệt để đo thật).*
6. [`HYBRID_CUTOVER_DECISION.md`](HYBRID_CUTOVER_DECISION.md) — Báo cáo tổng hợp trả lời 6 câu hỏi cốt lõi của Master Task, giữ phán quyết `HYBRID_CUTOVER_BLOCKED` & `LEGACY_REMOVAL_BLOCKED`, kế hoạch cutover/rollback/dọn legacy khi đạt GO và đầu vào duy nhất cần Owner bàn giao.
7. [`c26-three-tier-verification.json`](c26-three-tier-verification.json) & [`run.json`](run.json) — Biên nhận kiểm chứng chỉ-đọc quy tắc ba tầng **P1** trên 70 dòng C26 (không sửa nhãn lịch sử) và metadata của run.
