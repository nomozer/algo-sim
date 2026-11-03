# Run `hybrid-independent-h1`

Hồ sơ bàn giao độc lập tự đủ, tiền đăng ký hợp đồng đánh giá **P1**, ngân sách bắt cặp an toàn (`SafeCampaignBudget` bằng `decimal.Decimal` + khóa tương tranh), kiểm định tiếp nhận corpus 10 cổng, kiểm tra biên `Scene3D` và phán quyết chuyển đổi kiến trúc thuộc Master Epic `ALGOSIM_MASTER_HYBRID_BACKEND_REPLACEMENT` (**backend only**, `frontend/**` và `backend/app/**` không chạm, `0` live provider calls, trạng thái thực thi hiện tại: `BLOCKED_EXTERNAL_AUTHOR`).

## Danh mục tài liệu & biên nhận

1. [`H1_AUTHORING_HANDOFF.md`](H1_AUTHORING_HANDOFF.md) & [`h1-corpus-template.json`](h1-corpus-template.json) — Gói bàn giao sạch duy nhất để Owner gửi tác giả con người độc lập biên soạn 60 đề hình học không gian tiếng Việt (`45 SERVE` + `5/5/5 REFUSE`), kèm mẫu JSON đầy đủ trường kiểm toán và 10 điều kiện nghiệm thu đầu vào.
2. [`H1_PREREGISTRATION.md`](H1_PREREGISTRATION.md) — Tiền đăng ký danh tính candidate `180db769` (`d331e75b`, `276fc548…`), chính sách kỹ thuật **P1** (`h1-section-determination-equivalence/1`), tách rời 3 tầng **Mathematical / Semantic Goal / Strict Contract**, kiểm tra biên hợp đồng `Scene3D` (§IX), giao thức bắt cặp §7 và ranh giới diễn giải thống kê.
3. [`H1_CORPUS_INTEGRITY.json`](H1_CORPUS_INTEGRITY.json) & [`publication-safety-receipt.json`](publication-safety-receipt.json) — Biên nhận máy trạng thái toàn vẹn corpus (`H1_AUTHORING_INDEPENDENCE = NOT_ESTABLISHED`, `H1_MEASUREMENT = NOT_MEASURED`, `paired_harness_sha256 = 8af7ca1f…`, `equivalence_scorer_sha256 = 7ada8a06…`) và biên nhận cổng an toàn xuất bản (`verdict = PASS`).
4. [`PAIRED_LIVE_BUDGET_PROPOSAL.md`](PAIRED_LIVE_BUDGET_PROPOSAL.md) & [`paired-live-owner-approval.template.json`](paired-live-owner-approval.template.json) — Đề xuất ngân sách an toàn `campaign_max_requests = 300`, `campaign_max_usd = 5.00` (`PENDING_OWNER_DECISION`, chi thực tế dự kiến `\$1.50 – \$2.00`).
5. *(Chưa tạo `H1_PAIRED_LIVE_EVALUATION_REPORT.md` vì chưa có `h1-independent-corpus.json` từ tác giả độc lập để đo thật).*
6. [`HYBRID_CUTOVER_DECISION.md`](HYBRID_CUTOVER_DECISION.md) — Phán quyết hiện hành (`BLOCKED_EXTERNAL_AUTHOR` / `HYBRID_CUTOVER_BLOCKED` / `LEGACY_REMOVAL_BLOCKED`), ranh giới hợp đồng `Scene3D` & sư phạm (§IX), kế hoạch cutover/rollback/dọn legacy và đầu vào cần từ Owner.
7. [`c26-three-tier-verification.json`](c26-three-tier-verification.json) & [`run.json`](run.json) — Biên nhận kiểm chứng chỉ-đọc quy tắc ba tầng **P1** trên 70 dòng C26 (không sửa nhãn lịch sử) và metadata của run.
