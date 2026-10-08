# legacy/ — tài liệu hết hiệu lực, giữ để truy vết

> **Không dùng làm căn cứ hiện hành.** Nội dung giữ nguyên byte so với vị trí cũ. Link tương đối bên trong các file đã
> chuyển viết cho vị trí **cũ**; bảng cũ → mới:
> [`../evaluation/geometry/runs/w19-docs-organization/inventory/MIGRATION_MAP.json`](../evaluation/geometry/runs/w19-docs-organization/inventory/MIGRATION_MAP.json).
> Khi tìm luật hay trạng thái hiện hành, loại `docs/legacy/` khỏi grep.

| file / thư mục | vị trí cũ | vì sao hết hiệu lực | thẩm quyền hiện hành |
|---|---|---|---|
| [`CURRENT_STATE_HISTORY.md`](CURRENT_STATE_HISTORY.md) | `docs/CURRENT_STATE.md` dòng 88–5475 tại `6d0e6321` | nhật ký phát triển: bảng w17 trở về trước, khối W4B, §1–§7 cũ | [`../CURRENT_STATE.md`](../CURRENT_STATE.md) (trạng thái), [`../STATUS_LEDGER.md`](../STATUS_LEDGER.md) (lịch sử) |
| [`research/THESIS_READINESS.md`](research/THESIS_READINESS.md) | `docs/` | bảng tuyên bố cũ + nhật ký "được nói / không được nói" và đính chính tới W18 | [`../research/CLAIM_EVIDENCE_MAP.md`](../research/CLAIM_EVIDENCE_MAP.md) |
| [`research/CLAIM_EVIDENCE_MATRIX.md`](research/CLAIM_EVIDENCE_MATRIX.md) | `docs/thesis/` | 29 tuyên bố 2026-09-09; định nghĩa đính chính D-1 … D-4 | như trên |
| [`research/CLAIM_TO_EVIDENCE_MAP.md`](research/CLAIM_TO_EVIDENCE_MAP.md) | `docs/research/` | lớp bằng chứng 2026-09-10; điều kiện bài báo A1–A6 | như trên |
| [`architecture/SEMANTIC_PROGRAM_ROUTE_DESIGN.md`](architecture/SEMANTIC_PROGRAM_ROUTE_DESIGN.md) + [`…_PLAN.md`](architecture/SEMANTIC_PROGRAM_ROUTE_PLAN.md) | `docs/superpowers/specs/` + `plans/` `2026-08-20-semantic-program-generative-route*` | thiết kế gốc và kế hoạch đã thực thi của route Semantic Program, viết khi sản phẩm còn là Tin học (IR thuật toán, 2D); `RULES.md` luật 11 trích §3.3; kế hoạch giữ giao thức niêm phong bộ SEALED mà `test_benchmark_seal.py` còn ghim | `../ARCHITECTURE_MAP.md` §5 (#31–#34), `../RULES.md` §4 |
| [`geometry/CAPABILITY_GAP_AUDIT.md`](geometry/CAPABILITY_GAP_AUDIT.md) | `docs/geometry/` | cách đọc + bảng (2026-08-30) của `backend/scripts/audit_geometry_capability.py` — script còn chạy; bảng là ảnh chụp | chạy lại script (`--md`); năng lực sản phẩm: `product_capability.py` |

**Đã gỡ ở run `docs-cleanup` (2026-10-08)**, sau khi đọc và kiểm consumer — danh sách, lý do và consumer từng file:
[`../evaluation/geometry/runs/docs-cleanup/inventory.md`](../evaluation/geometry/runs/docs-cleanup/inventory.md): 16
plan/spec của skill cho M9–M17 và W13 (miền Tin học đã retire), bảy tài liệu giai đoạn chuyển đề trong `geometry/` và
`architecture/NEXT_VERTICAL_SLICE_DECISION.md` (đã thực thi, có bản thay), `REPOSITORY_MAP.md`, `RULES_v0.3.md`.
`architecture/CUBOID_CUBE_CONTRACT_DECISION.md` đưa về [`../architecture/`](../architecture/) vì mã vẫn cài đúng nó.
Mọi bản gỡ còn trong git history.

## Phần tách nguyên văn khỏi tài liệu sống (2026-10-05, `cuboid-final-review`)

Bảy file dưới đây chứa các **khối** chép nguyên văn từ tài liệu sống tại commit `4048ff83`: mỗi khối ghi dòng gốc và
sha256 trong chú thích, và tài liệu sống để lại một dòng trỏ về đây. Kiểm lại byte:
`docs/evaluation/geometry/runs/cuboid-final-review/diagnostics/split_history_cfr.py --verify` (bản ghi:
[`../evaluation/geometry/runs/cuboid-final-review/inventory/HISTORY_SPLIT.json`](../evaluation/geometry/runs/cuboid-final-review/inventory/HISTORY_SPLIT.json)).

| file | tách từ | nội dung |
|---|---|---|
| [`CODE_INDEX_REMOVED_ENTRIES.md`](CODE_INDEX_REMOVED_ENTRIES.md) | `../CODE_INDEX.md` | mục mô tả mã đã gỡ (Tin học, DSL, công cụ và module đã xoá); chỉ mục truy vết ngắn vẫn ở §0j |
| [`STATUS_LEDGER_INFORMATICS_ERA.md`](STATUS_LEDGER_INFORMATICS_ERA.md) | `../STATUS_LEDGER.md` | bảng trạng thái §1–§5 (gồm §4f–§4h, các mục W12) và tên đề tài 2026-08-18 |
| [`COVERAGE_INFORMATICS_ERA.md`](COVERAGE_INFORMATICS_ERA.md) | `../COVERAGE.md` | nguồn SGK Tin học và tuyên bố cấm của nó, ma trận giá trị, phủ năng lực, bộ đề (§1, §1b, §3, §4, §6–§12) |
| [`CORRECTNESS_INFORMATICS_ERA.md`](CORRECTNESS_INFORMATICS_ERA.md) | `../CORRECTNESS.md` | tiền lệ what-if, PatchResult (§3), phân loại A/B/C (§5–§6), runner `live.py`, §8–§9 |
| [`ARCHITECTURE_MAP_INFORMATICS_ERA.md`](ARCHITECTURE_MAP_INFORMATICS_ERA.md) | `../ARCHITECTURE_MAP.md` | hai trục DSL/edit (§6), điểm mở rộng (§7), cache pattern reuse (§9), hướng tương lai (§10) |
| [`DESIGN_BRIEF_INFORMATICS_ERA.md`](DESIGN_BRIEF_INFORMATICS_ERA.md) | `../DESIGN_BRIEF.md` | mô tả sản phẩm Tin học (§1), bố cục workspace, hợp đồng theo miền (§4), việc thiết kế (§8) |
| [`POST_THESIS_BACKLOG_INFORMATICS_ERA.md`](POST_THESIS_BACKLOG_INFORMATICS_ERA.md) | `../POST_THESIS_BACKLOG.md` | hai mục ý tưởng của sản phẩm Tin học, dòng phạm vi "môn Tin học" |

Link tương đối bên trong các khối viết cho thư mục `docs/` nên từ `legacy/` chúng trỏ lệch một cấp — cùng ngoại lệ đã
ghi ở đầu file này.
