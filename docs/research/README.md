# research/ — nghiên cứu, khoá luận, bài báo

> Tài liệu **viết** (khác bằng chứng đo ở `../evaluation/`). Luật trích dẫn ở
> [`thesis/THESIS_REFERENCES.md`](thesis/THESIS_REFERENCES.md) áp dụng cho **mọi** file trong thư mục này: không trích
> theo tiêu đề, không bịa DOI, preprint không trình bày như bài đã phản biện, không suy *"Không"* từ im lặng.

## Dùng chung

| file | vai trò |
|---|---|
| [`CLAIM_EVIDENCE_MAP.md`](CLAIM_EVIDENCE_MAP.md) | **thẩm quyền duy nhất**: tuyên bố ↔ bằng chứng ↔ giới hạn, mức, mục dùng được |
| [`GEOMETRY_CURRICULUM_COVERAGE.md`](GEOMETRY_CURRICULUM_COVERAGE.md) | độ phủ chương trình hình học THPT (snapshot 2026-09-04; `backend/tests/geometry/test_curriculum_coverage.py` đọc) |
| [`RESEARCH_GAP_AND_CONTRIBUTIONS.md`](RESEARCH_GAP_AND_CONTRIBUTIONS.md) | khoảng trống nghiên cứu và đóng góp |
| [`LITERATURE_COMPARISON_MATRIX.md`](LITERATURE_COMPARISON_MATRIX.md) | so sánh công trình liên quan |
| [`SYSTEMATIC_LITERATURE_GAP_SYNTHESIS.md`](SYSTEMATIC_LITERATURE_GAP_SYNTHESIS.md) + `systematic_literature_*.json` | tổng hợp tài liệu có hệ thống, dữ liệu máy và nhật ký tìm kiếm |
| [`RELATED_WORK_SEARCH_PROTOCOL.md`](RELATED_WORK_SEARCH_PROTOCOL.md) | phương pháp tìm công trình liên quan |
| [`HYBRID_ARCHITECTURE_EVALUATION_PROTOCOL.md`](HYBRID_ARCHITECTURE_EVALUATION_PROTOCOL.md) + manifest | tiền đăng ký đánh giá kiến trúc lai (chưa chạy) |
| [`LLM_ONLY_PAIRED_BASELINE_COLLECTION_PREREGISTRATION.md`](LLM_ONLY_PAIRED_BASELINE_COLLECTION_PREREGISTRATION.md) + registry | tiền đăng ký baseline cặp; `backend/scripts/collect_llm_only_paired_baseline.py` đọc registry |

Ngoại lệ đã ghi: [`RECTANGULAR_BASE_PYRAMID_COMPILER_VERTICAL_SLICE.md`](RECTANGULAR_BASE_PYRAMID_COMPILER_VERTICAL_SLICE.md)
là **báo cáo wave** (bằng chứng) do wave của nó đặt ở đây; giữ đường dẫn theo luật bất biến của bằng chứng, không phải
tài liệu nghiên cứu.

## [`thesis/`](thesis/) — khoá luận

| file | vai trò |
|---|---|
| [`thesis/THESIS_DRAFT.md`](thesis/THESIS_DRAFT.md) | bản thảo chính (cập nhật lần cuối 2026-09-09; chưa phản ánh w09–w18) |
| [`thesis/CHAPTER_4_RESULTS_AND_DISCUSSION.md`](thesis/CHAPTER_4_RESULTS_AND_DISCUSSION.md) · [`thesis/CHAPTER_5_CONCLUSION_AND_LIMITATIONS.md`](thesis/CHAPTER_5_CONCLUSION_AND_LIMITATIONS.md) | chương 4–5 viết riêng (bản thảo có **hai thân Chương 4 rời nhau** — hợp nhất là việc của wave viết bản thảo) |
| [`thesis/THESIS_ARCHITECTURE.md`](thesis/THESIS_ARCHITECTURE.md) | kiến trúc hệ đóng băng 2026-09-02 cho chương thiết kế; hệ **hiện tại** ở `../ARCHITECTURE_MAP.md` |
| [`thesis/RELATED_WORK_DRAFT.md`](thesis/RELATED_WORK_DRAFT.md) · [`thesis/references_geometry_systems.bib`](thesis/references_geometry_systems.bib) | công trình liên quan |
| [`thesis/THESIS_REFERENCES.md`](thesis/THESIS_REFERENCES.md) · [`thesis/THESIS_CITATION_MATRIX.md`](thesis/THESIS_CITATION_MATRIX.md) · [`thesis/THESIS_REFERENCE_NEEDS.md`](thesis/THESIS_REFERENCE_NEEDS.md) | luật trích dẫn + danh mục, ma trận trích dẫn, nhu cầu tài liệu |
| [`thesis/THESIS_DEMO.md`](thesis/THESIS_DEMO.md) | kịch bản trình bày demo (vận hành demo: `../DEMO_RUNBOOK.md`) |
| [`thesis/THESIS_FIGURE_CAPTURE_PLAN.md`](thesis/THESIS_FIGURE_CAPTURE_PLAN.md) · [`thesis/figures/`](thesis/figures/FIGURE_MANIFEST.md) | kế hoạch chụp hình và hình (SVG/PNG + nhật ký chụp) |
| [`thesis/THESIS_SUBMISSION_CHECKLIST.md`](thesis/THESIS_SUBMISSION_CHECKLIST.md) | checklist nộp |

## [`paper/`](paper/) — bài báo

[`paper/PUBLICATION_READINESS_ASSESSMENT.md`](paper/PUBLICATION_READINESS_ASSESSMENT.md) — đánh giá 2026-09-10: phù hợp
nhất là system/demo paper; hội nghị chính cần thêm k ≥ 3 lượt, bộ held-out, mẫu lớn hơn, baseline (hàng E4, G1 của
bản đồ).

## Báo cáo của các wave nghiên cứu

Báo cáo wave (`THESIS_*_ACCEPTANCE_*`, `THESIS_OBJECTIVE_AND_CLAIM_ALIGNMENT_REVIEW`,
`RESEARCH_GAP_AND_SYSTEM_CONTRIBUTION_FORMALIZATION`, …) là bằng chứng, ở gốc `docs/`; tra theo chủ đề ở
[`../evaluation/HISTORICAL_REPORTS.md`](../evaluation/HISTORICAL_REPORTS.md). Ba bảng tuyên bố cũ và nhật ký
`THESIS_READINESS` ở [`../legacy/research/`](../legacy/research/).
