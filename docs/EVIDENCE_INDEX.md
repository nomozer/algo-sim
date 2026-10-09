# EVIDENCE_INDEX.md — Chỉ mục bằng chứng và chuỗi đính chính (Master Evidence Index)

> **Tài liệu Canonical cho việc tra cứu toàn bộ bằng chứng thực nghiệm, báo cáo và chuỗi đính chính.**
> Quy tắc bảo toàn: Báo cáo và artifact còn làm bằng chứng cho sản phẩm, nghiên cứu hiện hành hoặc khả năng tái lập phải giữ nguyên byte. Có thể đổi đường dẫn nếu mọi consumer/index/manifest được cập nhật; có thể xoá sau inventory khi đã xác minh không còn các vai trò ấy. Sai lệch của bằng chứng còn dùng được đính chính thông qua chuỗi `CORRECTED_BY`, không sửa kết quả lịch sử.
> Không có chu trình trong chuỗi đính chính (Acyclic DAG).

---

## 1. Chuỗi Đính Chính Tiêu Biểu (Primary Correction Chain)

```text
FRESH_PREREGISTERED_FAILURE_REPRODUCTION_RETRY (Đo live P03/P05: P03 valid, P05 valid, token ghi 0, trace false positives)
  │
  ▼ CORRECTED_BY
MODEL_VARIANCE_EVIDENCE_REVIEW (Đính chính offline: token 0 -> UNKNOWN, trace sửa, tách biệt outcome vs causality)
  │
  ▼ CORRECTED_BY
MODEL_VARIANCE_EVIDENCE_PROVENANCE_REPAIR_OFFLINE (Đính chính provenance máy: commit 1 full SHA, JUnit telemetry, 2-run determinism)

DOCS_INFORMATION_ARCHITECTURE_AND_HANDOFF_HARDENING (Báo cáo và cấu trúc tài liệu ban đầu)
  │
  ▼ CORRECTED_BY
DOCS_INFORMATION_ARCHITECTURE_EVIDENCE_PROVENANCE_REPAIR_OFFLINE (Đính chính provenance máy, loại bỏ hardcode)
  │
  ▼ CORRECTED_BY
DOCS_TEST_TELEMETRY_RECONCILIATION_FINAL (Khép lại số liệu telemetry pytest bằng 2 bất biến số học và plugin hook máy)

PRIMITIVE_COMPILER_SECOND_FAMILY_SELECTION_AND_PREREGISTRATION (Tiền đăng ký họ thứ hai: 95.5 điểm, manifest 8 ca)
  │
  ▼ CORRECTED_BY
SECOND_FAMILY_PREREGISTRATION_EVIDENCE_REPAIR_OFFLINE (Đính chính điểm THPT NOT_ESTABLISHED, 12 tầng kỹ thuật, ghi nhầm 94.0)
  │
  ▼ CORRECTED_BY
SECOND_FAMILY_SOURCE_SCOPE_RECONCILIATION_OFFLINE (Đối soát mã nguồn: sửa 94.0->95.5, 6 primitives, RequestContract = CHANGE_REQUIRED, fail-closed INCOMPLETE)

PRISM_VERTICAL_SLICE_MERGE_READINESS_REVIEW (Review merge: ghi nhầm nhãn hash manifest, ground truth và raw response do transcription error)
  │
  ▼ CORRECTED_BY
PRISM_MERGE_READINESS_EVIDENCE_IDENTITY_RECONCILIATION_OFFLINE (Đính chính danh tính bằng chứng máy: raw response f1bd804584..., manifest f5978eb5f7..., ground truth faf42e894f..., đường dẫn thực tế semantic_program)

CROSS_FAMILY_SCENE3D_PRODUCT_SEMANTIC_REPAIR (READY_FOR_HUMAN_VISUAL_REVIEW)
  │  phát hiện: bằng chứng hidden-line chưa đủ — không có oracle perspective độc lập, không có frozen camera identity, không có recovery audit
  ▼ CORRECTED_BY
CROSS_FAMILY_HIDDEN_LINE_OCCLUSION_ORACLE_AND_FORMATION_REPAIR (sửa occlusion/oracle/formation → VERIFICATION_NOT_CLEAN)
  │  phát hiện: 28 lỗi "runner fixture" thật ra là REAL_PRODUCT_REGRESSION (HTTP 500); mobile recompute do khoá camera float thô
  ▼ CORRECTED_BY
VERIFICATION_CLEANUP_AFTER_OCCLUSION_REPAIR (mọi cổng tự động xanh → READY_FOR_HUMAN_VISUAL_REVIEW)
  │  review người: FAIL_REQUIRES_PEDAGOGICAL_VISUAL_REPAIR (cạnh khuất không có điểm ảnh, playback, camera)
  ▼ CORRECTED_BY
HUMAN_VISUAL_REVIEW_AND_PEDAGOGICAL_PLAYBACK_CLOSURE (w10 → READY_FOR_HUMAN_VISUAL_REVIEW)
  │  review người: FAIL_REQUIRES_TARGETED_PEDAGOGICAL_REPAIR (W10-H1…H9: chóp/lăng trụ tam giác không công thức, ảnh xoay gần suy biến, …)
  ▼ CORRECTED_BY · SUPERSEDED_FOR_HUMAN_VERDICT
W11_PEDAGOGICAL_FORMULA_VISUAL_POLISH_AND_HUMAN_REREVIEW (w11 → READY_FOR_HUMAN_VISUAL_REVIEW)
  │  review người: NEEDS_CHANGES (W11-H1…H5: timeline trộn bước tính, bước tĩnh, lớp lời giải, cam đậm hai nghĩa, GIVEN không có trong đề)
  ▼ CORRECTED_BY · SUPERSEDED_FOR_HUMAN_VERDICT
W12_PEDAGOGICAL_TIMELINE_AND_SOURCE_GROUNDING_CLOSURE (w12 → READY_FOR_HUMAN_VISUAL_REVIEW)
  │  review người: NEEDS_CHANGES (W12-H1…H4: chóp/lăng trụ tam giác thiếu bước dựng riêng, không vá riêng hai họ, kênh giả định còn mở)
  ▼ CORRECTED_BY
W13_GEOMETRY_CAPABILITY_AND_NON_ABSOLUTE_ARCHITECTURE_PREREGISTRATION (w13, chỉ tài liệu → ARCHITECTURE_PREREGISTRATION_READY; không ảnh mới nên không SUPERSEDED_FOR_HUMAN_VERDICT)
  ▼ thực hiện tiền đăng ký · trả lời review w12 · SUPERSEDED_FOR_HUMAN_VERDICT (ảnh w12)
W14_GENERIC_FORMATION_AND_ASSUMPTION_FOUNDATION (w14 → FORMATION_FOUNDATION_INCOMPLETE; Track B ASSUMPTION_POLICY_INCOMPLETE; chưa có review người)
  ▼ CORRECTED_BY (Track B: nguyên nhân gốc RC1–RC5 rồi đóng cổng; W15-D1 giải W14-D1) · SUPERSEDED_FOR_HUMAN_VERDICT (ảnh w14)
W15_SOURCE_CONSTRAINT_AND_ASSUMPTION_CLOSURE (w15 → READY_FOR_HUMAN_VISUAL_REVIEW; chưa có review người)
  ▼ CORRECTED_BY (hai lỗ chứng chỉ: mặt phẳng cùng thực thể, yêu cầu chứng minh làm tiền đề; phần tô đè cạnh; ô từ chối trắng) · SUPERSEDED_FOR_HUMAN_VERDICT (ảnh w15)
W16_PREMERGE_SOUNDNESS_AND_VISUAL_EVIDENCE_CLOSURE (w16 → READY_FOR_HUMAN_VISUAL_REVIEW; chưa có review người)
  ▼ CORRECTED_BY (giới hạn A′ đóng cho phép cắt; grounding không đọc yêu cầu chứng minh như dữ kiện ở mọi vùng; ảnh "cạnh 4" là lỗi bộ sinh fixture) · SUPERSEDED_FOR_HUMAN_VERDICT (ảnh w16)
W17_OPERATION_BINDING_AND_ON_SCENE_ANNOTATIONS (w17 → READY_FOR_HUMAN_VISUAL_REVIEW; chưa có review người)
  ▼ CORRECTED_BY (phép dựng điểm — trung điểm, hình chiếu — gắn với quan hệ của đề theo danh tính; giới hạn phép dựng ngoài phép cắt đóng một phần) · SUPERSEDED_FOR_HUMAN_VERDICT (ảnh w17: hai công tắc thay bằng "Hiện tất cả")
W18_CONSTRUCTION_BINDING_AND_FOCUSED_ANNOTATIONS (w18 → READY_FOR_HUMAN_VISUAL_REVIEW; chưa có review người)
```

**Các điểm đính chính quan trọng đã được xác lập:**
1. **Kết quả retry P03 và P05:** Cả hai ca Analyze live đều thành công, hợp đồng dữ kiện hợp lệ, FactGraph và Primitive Compiler xử lý trọn vẹn, topology, `final_memory` và đáp số đều đạt. Lỗi `MODEL_MALFORMED_RELATION` không tái diễn.
2. **Token usage:** Hai request HTTP 200 có token ghi nhận ban đầu là `0` do giới hạn client đo lường; lớp đính chính đã chuẩn hóa thành `UNKNOWN`.
3. **Trace false-positive:** Quan hệ hợp lệ nhưng gắn nhãn sai lệch `MULTIPLE_STRUCTURAL_DEFECTS` đã được khắc phục bằng bộ đánh giá kind-aware trace.
4. **Historical root cause:** Nguyên nhân lịch sử của cụm lỗi P03/P05 vẫn là `NOT_ESTABLISHED` (nhất quán với giả thuyết biến thiên tự nhiên của mô hình - model variance).
5. **Commit label & identity:** Short SHA `3ba5afbb` có full SHA thực tế từ Git là `3ba5afbbd6b6e22781b03f29563c9d1589780603` (thay vì chuỗi ghép sai `3ba5afbbf46d...`). Phân loại: `COMMIT_ROLE_LABELING_ERROR` với `HISTORY_DRIFT = NO`.
6. **Tách biệt JUnit SHA-256:**
   - Worktree A (`CODE_HEAD = 18704f14`): focused sha256 = `955d5be51888496739bb5cba896f3068e52a806cbf18a8b163306dbddc360be8`, full backend sha256 = `a9307d083d06eb4f85e5094dbe1513e9a4f4d2f8cb8b77dcf95eb7f7b3c2e171`.
   - Worktree B (`END_HEAD = 2678cc65`): focused sha256 = `3c219c3ab81e1ec3c7c4a463fcf0092cd96843202736383b88dfc19b9bf15a3a`, full backend sha256 = `a36f82b9841569d4842637639809549fa97eb28d050b1507c472d86b6f19edbb`.

---

## 2. Bảng Danh Mục Các Wave Thực Nghiệm

## WAVE_ID = COMPLETION_RUNNER_REPAIR_OFFLINE
- **DATE:** 2026-09-17
- **REPORT:** docs/evaluation/geometry/photo-problem-to-scene/completion-runner-repair-offline/report.md
- **ARTIFACT_DIRECTORY:** docs/evaluation/geometry/photo-problem-to-scene/completion-runner-repair-offline/
- **START_BASE:** bd370157
- **CODE_COMMIT:** 25c3f5b8
- **EVIDENCE_COMMIT_ROLE:** 35d84da0
- **CLASSIFICATION:** RUNNER_REPAIR_OFFLINE
- **PRODUCT_CHANGE:** NO
- **MODEL_REQUEST_COUNT:** 0
- **CANDIDATE_CHANGE:** NO
- **CACHE_CHANGE:** NO
- **CORRECTED_BY:** NONE
- **SUPERSEDES:** NONE
- **THESIS_USE:** SUPPORTING_EVIDENCE

## WAVE_ID = STRUCTURED_RELATION_SAFETY_REPAIR
- **DATE:** 2026-09-17
- **REPORT:** docs/evaluation/geometry/photo-problem-to-scene/structured-relation-safety-repair/report.md
- **ARTIFACT_DIRECTORY:** docs/evaluation/geometry/photo-problem-to-scene/structured-relation-safety-repair/
- **START_BASE:** 35d84da0
- **CODE_COMMIT:** 8dd5f8b6
- **EVIDENCE_COMMIT_ROLE:** cac49a09
- **CLASSIFICATION:** COMPILER_SAFETY_REPAIR
- **PRODUCT_CHANGE:** YES
- **MODEL_REQUEST_COUNT:** 0
- **CANDIDATE_CHANGE:** YES
- **CACHE_CHANGE:** NO
- **CORRECTED_BY:** NONE
- **SUPERSEDES:** NONE
- **THESIS_USE:** CORE_CONTRIBUTION

## WAVE_ID = N04_TARGETED_REJECTION_REGISTRY_V2_PREREGISTRATION
- **DATE:** 2026-09-17
- **REPORT:** docs/evaluation/geometry/photo-problem-to-scene/n04-targeted-rejection-registry-v2-preregistration/report.md
- **ARTIFACT_DIRECTORY:** docs/evaluation/geometry/photo-problem-to-scene/n04-targeted-rejection-registry-v2-preregistration/
- **START_BASE:** cac49a09
- **CODE_COMMIT:** 330334a0
- **EVIDENCE_COMMIT_ROLE:** d01254c2
- **CLASSIFICATION:** EVALUATION_PREREGISTRATION
- **PRODUCT_CHANGE:** NO
- **MODEL_REQUEST_COUNT:** 0
- **CANDIDATE_CHANGE:** NO
- **CACHE_CHANGE:** NO
- **CORRECTED_BY:** NONE
- **SUPERSEDES:** NONE
- **THESIS_USE:** EVALUATION_METHODOLOGY

## WAVE_ID = COMPLETION_MEASUREMENT_REPAIR_OFFLINE_POST_SAFETY
- **DATE:** 2026-09-18
- **REPORT:** docs/evaluation/geometry/photo-problem-to-scene/completion-measurement-repair-offline-post-safety/report.md
- **ARTIFACT_DIRECTORY:** docs/evaluation/geometry/photo-problem-to-scene/completion-measurement-repair-offline-post-safety/
- **START_BASE:** d01254c2
- **CODE_COMMIT:** e0fbbb22
- **EVIDENCE_COMMIT_ROLE:** e76419f4
- **CLASSIFICATION:** RUNNER_MEASUREMENT_REPAIR
- **PRODUCT_CHANGE:** NO
- **MODEL_REQUEST_COUNT:** 0
- **CANDIDATE_CHANGE:** NO
- **CACHE_CHANGE:** NO
- **CORRECTED_BY:** NONE
- **SUPERSEDES:** NONE
- **THESIS_USE:** SUPPORTING_EVIDENCE

## WAVE_ID = RETRY_REMAINING_PREREGISTERED_CASES_POST_MEASUREMENT_REPAIR
- **DATE:** 2026-09-18
- **REPORT:** docs/evaluation/geometry/photo-problem-to-scene/multicase-benchmark-completion-live-post-measurement-repair/report.md
- **ARTIFACT_DIRECTORY:** docs/evaluation/geometry/photo-problem-to-scene/multicase-benchmark-completion-live-post-measurement-repair/
- **START_BASE:** e76419f4
- **CODE_COMMIT:** NONE
- **EVIDENCE_COMMIT_ROLE:** 12df583a
- **CLASSIFICATION:** LIVE_EVALUATION
- **PRODUCT_CHANGE:** NO
- **MODEL_REQUEST_COUNT:** 12
- **CANDIDATE_CHANGE:** NO
- **CACHE_CHANGE:** NO
- **CORRECTED_BY:** NONE
- **SUPERSEDES:** NONE
- **THESIS_USE:** EMPIRICAL_RESULTS

## WAVE_ID = ANALYZE_FAILURE_CLUSTER_DIAGNOSIS
- **DATE:** 2026-09-19
- **REPORT:** docs/evaluation/geometry/photo-problem-to-scene/analyze-failure-cluster-diagnosis/report.md
- **ARTIFACT_DIRECTORY:** docs/evaluation/geometry/photo-problem-to-scene/analyze-failure-cluster-diagnosis/
- **START_BASE:** 12df583a
- **CODE_COMMIT:** 5806fec9
- **EVIDENCE_COMMIT_ROLE:** 0ff69cbb
- **CLASSIFICATION:** DIAGNOSIS_OFFLINE
- **PRODUCT_CHANGE:** NO
- **MODEL_REQUEST_COUNT:** 0
- **CANDIDATE_CHANGE:** NO
- **CACHE_CHANGE:** NO
- **CORRECTED_BY:** NONE
- **SUPERSEDES:** NONE
- **THESIS_USE:** SUPPORTING_EVIDENCE

## WAVE_ID = FRESH_PREREGISTERED_FAILURE_REPRODUCTION
- **DATE:** 2026-09-19
- **REPORT:** docs/evaluation/geometry/photo-problem-to-scene/fresh-preregistered-failure-reproduction/report.md
- **ARTIFACT_DIRECTORY:** docs/evaluation/geometry/photo-problem-to-scene/fresh-preregistered-failure-reproduction/
- **START_BASE:** 0ff69cbb
- **CODE_COMMIT:** 2dbf23c7
- **EVIDENCE_COMMIT_ROLE:** 45702b36
- **CLASSIFICATION:** REPRODUCTION_PREREGISTRATION
- **PRODUCT_CHANGE:** NO
- **MODEL_REQUEST_COUNT:** 1
- **CANDIDATE_CHANGE:** NO
- **CACHE_CHANGE:** NO
- **CORRECTED_BY:** NONE
- **SUPERSEDES:** NONE
- **THESIS_USE:** SUPPORTING_EVIDENCE

## WAVE_ID = SAFE_STRUCTURE_TRACE_REPAIR_OFFLINE
- **DATE:** 2026-09-20
- **REPORT:** docs/evaluation/geometry/photo-problem-to-scene/safe-structure-trace-repair-offline/report.md
- **ARTIFACT_DIRECTORY:** docs/evaluation/geometry/photo-problem-to-scene/safe-structure-trace-repair-offline/
- **START_BASE:** 45702b36
- **CODE_COMMIT:** 866a1257
- **EVIDENCE_COMMIT_ROLE:** efee245c
- **CLASSIFICATION:** RUNNER_PERSISTENCE_REPAIR
- **PRODUCT_CHANGE:** NO
- **MODEL_REQUEST_COUNT:** 0
- **CANDIDATE_CHANGE:** NO
- **CACHE_CHANGE:** NO
- **CORRECTED_BY:** SAFE_STRUCTURE_TRACE_REPAIR_EVIDENCE_RECONCILIATION
- **SUPERSEDES:** NONE
- **THESIS_USE:** SUPPORTING_EVIDENCE

## WAVE_ID = SAFE_STRUCTURE_TRACE_REPAIR_EVIDENCE_RECONCILIATION
- **DATE:** 2026-09-20
- **REPORT:** docs/evaluation/geometry/photo-problem-to-scene/safe-structure-trace-repair-evidence-reconciliation/report.md
- **ARTIFACT_DIRECTORY:** docs/evaluation/geometry/photo-problem-to-scene/safe-structure-trace-repair-evidence-reconciliation/
- **START_BASE:** efee245c
- **CODE_COMMIT:** NONE
- **EVIDENCE_COMMIT_ROLE:** c6c6448e
- **CLASSIFICATION:** RECONCILIATION_OFFLINE
- **PRODUCT_CHANGE:** NO
- **MODEL_REQUEST_COUNT:** 0
- **CANDIDATE_CHANGE:** NO
- **CACHE_CHANGE:** NO
- **CORRECTED_BY:** NONE
- **SUPERSEDES:** SAFE_STRUCTURE_TRACE_REPAIR_OFFLINE
- **THESIS_USE:** SUPPORTING_EVIDENCE

## WAVE_ID = FRESH_PREREGISTERED_FAILURE_REPRODUCTION_RETRY
- **DATE:** 2026-09-21
- **REPORT:** docs/evaluation/geometry/photo-problem-to-scene/fresh-preregistered-failure-reproduction-retry/report.md
- **ARTIFACT_DIRECTORY:** docs/evaluation/geometry/photo-problem-to-scene/fresh-preregistered-failure-reproduction-retry/
- **START_BASE:** c6c6448e
- **CODE_COMMIT:** 934b4aeb
- **EVIDENCE_COMMIT_ROLE:** d09331ea
- **CLASSIFICATION:** LIVE_RETRY_EVALUATION
- **PRODUCT_CHANGE:** NO
- **MODEL_REQUEST_COUNT:** 2
- **CANDIDATE_CHANGE:** NO
- **CACHE_CHANGE:** NO
- **CORRECTED_BY:** MODEL_VARIANCE_EVIDENCE_REVIEW
- **SUPERSEDES:** NONE
- **THESIS_USE:** EMPIRICAL_RESULTS

## WAVE_ID = MODEL_VARIANCE_EVIDENCE_REVIEW
- **DATE:** 2026-09-21
- **REPORT:** docs/evaluation/geometry/photo-problem-to-scene/model-variance-evidence-review/report.md
- **ARTIFACT_DIRECTORY:** docs/evaluation/geometry/photo-problem-to-scene/model-variance-evidence-review/
- **START_BASE:** d09331ea
- **CODE_COMMIT:** 3ba5afbb
- **EVIDENCE_COMMIT_ROLE:** 63eb0640
- **CLASSIFICATION:** EVIDENCE_REVIEW_OFFLINE
- **PRODUCT_CHANGE:** NO
- **MODEL_REQUEST_COUNT:** 0
- **CANDIDATE_CHANGE:** NO
- **CACHE_CHANGE:** NO
- **CORRECTED_BY:** MODEL_VARIANCE_EVIDENCE_PROVENANCE_REPAIR_OFFLINE
- **SUPERSEDES:** FRESH_PREREGISTERED_FAILURE_REPRODUCTION_RETRY
- **THESIS_USE:** EMPIRICAL_RESULTS

## WAVE_ID = MODEL_VARIANCE_EVIDENCE_PROVENANCE_REPAIR_OFFLINE
- **DATE:** 2026-09-22
- **REPORT:** docs/evaluation/geometry/photo-problem-to-scene/model-variance-evidence-provenance-repair/report.md
- **ARTIFACT_DIRECTORY:** docs/evaluation/geometry/photo-problem-to-scene/model-variance-evidence-provenance-repair/
- **START_BASE:** 63eb0640
- **CODE_COMMIT:** 18704f14
- **EVIDENCE_COMMIT_ROLE:** 2678cc65
- **CLASSIFICATION:** PROVENANCE_REPAIR_OFFLINE
- **PRODUCT_CHANGE:** NO
- **MODEL_REQUEST_COUNT:** 0
- **CANDIDATE_CHANGE:** NO
- **CACHE_CHANGE:** NO
- **CORRECTED_BY:** NONE
- **SUPERSEDES:** MODEL_VARIANCE_EVIDENCE_REVIEW
- **THESIS_USE:** AUTHORITATIVE_EVIDENCE

## WAVE_ID = DOCS_INFORMATION_ARCHITECTURE_AND_HANDOFF_HARDENING
- **DATE:** 2026-09-22
- **REPORT:** docs/evaluation/geometry/photo-problem-to-scene/docs-information-architecture-handoff-hardening/report.md
- **ARTIFACT_DIRECTORY:** docs/evaluation/geometry/photo-problem-to-scene/docs-information-architecture-handoff-hardening/
- **START_BASE:** 2678cc65
- **CODE_COMMIT:** 34c36872
- **EVIDENCE_COMMIT_ROLE:** c36f2042
- **CLASSIFICATION:** DOCS_HARDENING_OFFLINE
- **PRODUCT_CHANGE:** NO
- **MODEL_REQUEST_COUNT:** 0
- **CANDIDATE_CHANGE:** NO
- **CACHE_CHANGE:** NO
- **CORRECTED_BY:** DOCS_INFORMATION_ARCHITECTURE_EVIDENCE_PROVENANCE_REPAIR_OFFLINE
- **SUPERSEDES:** NONE
- **THESIS_USE:** ARCHITECTURE_HARDENING

## WAVE_ID = DOCS_INFORMATION_ARCHITECTURE_EVIDENCE_PROVENANCE_REPAIR_OFFLINE
- **DATE:** 2026-09-22
- **REPORT:** docs/evaluation/geometry/photo-problem-to-scene/docs-information-architecture-evidence-provenance-repair/report.md
- **ARTIFACT_DIRECTORY:** docs/evaluation/geometry/photo-problem-to-scene/docs-information-architecture-evidence-provenance-repair/
- **START_BASE:** c36f2042
- **CODE_COMMIT:** 27ed66aa
- **EVIDENCE_COMMIT_ROLE:** 02a7a860
- **CLASSIFICATION:** PROVENANCE_REPAIR_OFFLINE
- **PRODUCT_CHANGE:** NO
- **MODEL_REQUEST_COUNT:** 0
- **CANDIDATE_CHANGE:** NO
- **CACHE_CHANGE:** NO
- **CORRECTED_BY:** DOCS_TEST_TELEMETRY_RECONCILIATION_FINAL
- **SUPERSEDES:** DOCS_INFORMATION_ARCHITECTURE_AND_HANDOFF_HARDENING
- **THESIS_USE:** AUTHORITATIVE_EVIDENCE

## WAVE_ID = DOCS_TEST_TELEMETRY_RECONCILIATION_FINAL
- **DATE:** 2026-09-22
- **REPORT:** docs/evaluation/geometry/photo-problem-to-scene/docs-test-telemetry-reconciliation-final/report.md
- **ARTIFACT_DIRECTORY:** docs/evaluation/geometry/photo-problem-to-scene/docs-test-telemetry-reconciliation-final/
- **START_BASE:** 02a7a860
- **CODE_COMMIT:** dbb1ef1c
- **EVIDENCE_COMMIT_ROLE:** SELF
- **CLASSIFICATION:** TELEMETRY_RECONCILIATION_OFFLINE
- **PRODUCT_CHANGE:** NO
- **MODEL_REQUEST_COUNT:** 0
- **CANDIDATE_CHANGE:** NO
- **CACHE_CHANGE:** NO
- **CORRECTED_BY:** NONE
- **SUPERSEDES:** DOCS_INFORMATION_ARCHITECTURE_EVIDENCE_PROVENANCE_REPAIR_OFFLINE
- **THESIS_USE:** AUTHORITATIVE_EVIDENCE

## WAVE_ID = PRIMITIVE_COMPILER_SECOND_FAMILY_SELECTION_AND_PREREGISTRATION
- **DATE:** 2026-09-22
- **REPORT:** docs/evaluation/geometry/photo-problem-to-scene/primitive-compiler-second-family-selection/report.md
- **ARTIFACT_DIRECTORY:** docs/evaluation/geometry/photo-problem-to-scene/primitive-compiler-second-family-selection/
- **START_BASE:** 6ec2e0d3
- **CODE_COMMIT:** abb377b8
- **EVIDENCE_COMMIT_ROLE:** SELF
- **CLASSIFICATION:** PREREGISTRATION_OFFLINE
- **PRODUCT_CHANGE:** NO
- **MODEL_REQUEST_COUNT:** 0
- **CANDIDATE_CHANGE:** NO
- **CACHE_CHANGE:** NO
- **CORRECTED_BY:** SECOND_FAMILY_PREREGISTRATION_EVIDENCE_REPAIR_OFFLINE
- **SUPERSEDES:** NONE
- **THESIS_USE:** AUTHORITATIVE_EVIDENCE

## WAVE_ID = SECOND_FAMILY_PREREGISTRATION_EVIDENCE_REPAIR_OFFLINE
- **DATE:** 2026-09-22
- **REPORT:** docs/evaluation/geometry/photo-problem-to-scene/second-family-preregistration-evidence-repair/report.md
- **ARTIFACT_DIRECTORY:** docs/evaluation/geometry/photo-problem-to-scene/second-family-preregistration-evidence-repair/
- **START_BASE:** 2a5b28eb
- **CODE_COMMIT:** 4a218d2d
- **EVIDENCE_COMMIT_ROLE:** SELF
- **CLASSIFICATION:** EVIDENCE_REPAIR_OFFLINE
- **PRODUCT_CHANGE:** NO
- **MODEL_REQUEST_COUNT:** 0
- **CANDIDATE_CHANGE:** NO
- **CACHE_CHANGE:** NO
- **CORRECTED_BY:** SECOND_FAMILY_SOURCE_SCOPE_RECONCILIATION_OFFLINE
- **SUPERSEDES:** PRIMITIVE_COMPILER_SECOND_FAMILY_SELECTION_AND_PREREGISTRATION
- **THESIS_USE:** AUTHORITATIVE_EVIDENCE

## WAVE_ID = SECOND_FAMILY_SOURCE_SCOPE_RECONCILIATION_OFFLINE
- **DATE:** 2026-09-22
- **REPORT:** docs/evaluation/geometry/photo-problem-to-scene/second-family-source-scope-reconciliation/report.md
- **ARTIFACT_DIRECTORY:** docs/evaluation/geometry/photo-problem-to-scene/second-family-source-scope-reconciliation/
- **START_BASE:** dc444acd
- **CODE_COMMIT:** 4630f24d
- **EVIDENCE_COMMIT_ROLE:** SELF
- **CLASSIFICATION:** SOURCE_SCOPE_RECONCILIATION_OFFLINE
- **PRODUCT_CHANGE:** NO
- **MODEL_REQUEST_COUNT:** 0
- **CANDIDATE_CHANGE:** NO
- **CACHE_CHANGE:** NO
- **CORRECTED_BY:** NONE
- **SUPERSEDES:** SECOND_FAMILY_PREREGISTRATION_EVIDENCE_REPAIR_OFFLINE
- **THESIS_USE:** AUTHORITATIVE_EVIDENCE

## WAVE_ID = GENERIC_SOLID_TOPOLOGY_CONTRACT_DESIGN_AND_PREREGISTRATION_OFFLINE
- **DATE:** 2026-09-22
- **REPORT:** docs/evaluation/geometry/photo-problem-to-scene/generic-solid-topology-contract-design/report.md
- **ARTIFACT_DIRECTORY:** docs/evaluation/geometry/photo-problem-to-scene/generic-solid-topology-contract-design/
- **START_BASE:** 65d09a89
- **CODE_COMMIT:** d0ba8bb7
- **EVIDENCE_COMMIT_ROLE:** SELF
- **CLASSIFICATION:** CONTRACT_DESIGN_AND_PREREGISTRATION_OFFLINE
- **PRODUCT_CHANGE:** NO
- **MODEL_REQUEST_COUNT:** 0
- **CANDIDATE_CHANGE:** NO
- **CACHE_CHANGE:** NO
- **CORRECTED_BY:** NONE
- **SUPERSEDES:** NONE
- **THESIS_USE:** AUTHORITATIVE_EVIDENCE

## WAVE_ID = PRIMITIVE_COMPILER_SECOND_FAMILY_VERTICAL_SLICE_OFFLINE
- **DATE:** 2026-09-22
- **REPORT:** docs/evaluation/geometry/photo-problem-to-scene/primitive-compiler-second-family-vertical-slice/report.md
- **ARTIFACT_DIRECTORY:** docs/evaluation/geometry/photo-problem-to-scene/primitive-compiler-second-family-vertical-slice/
- **START_BASE:** f4a547ab
- **CODE_COMMIT:** 5a5534fe
- **EVIDENCE_COMMIT_ROLE:** SELF
- **CLASSIFICATION:** VERTICAL_SLICE_IMPLEMENTATION_AND_VERIFICATION_OFFLINE
- **PRODUCT_CHANGE:** YES
- **MODEL_REQUEST_COUNT:** 0
- **CANDIDATE_CHANGE:** YES
- **CORRECTED_BY:** SECOND_FAMILY_FROZEN_BENCHMARK_ALIGNMENT_REPAIR_OFFLINE
- **SUPERSEDES:** NONE
- **THESIS_USE:** AUTHORITATIVE_EVIDENCE

## WAVE_ID = SECOND_FAMILY_FROZEN_BENCHMARK_ALIGNMENT_REPAIR_OFFLINE
- **DATE:** 2026-09-22
- **REPORT:** docs/evaluation/geometry/photo-problem-to-scene/second-family-frozen-benchmark-alignment-repair/report.md
- **ARTIFACT_DIRECTORY:** docs/evaluation/geometry/photo-problem-to-scene/second-family-frozen-benchmark-alignment-repair/
- **START_BASE:** b4521d28
- **CODE_COMMIT:** 0714e929
- **EVIDENCE_COMMIT_ROLE:** SELF
- **CLASSIFICATION:** REPORTING_AND_TEST_ASSERTION_EVIDENCE_MISMATCH
- **PRODUCT_CHANGE:** NO
- **MODEL_REQUEST_COUNT:** 0
- **CANDIDATE_CHANGE:** NO
- **CACHE_CHANGE:** NO
- **CORRECTED_BY:** NONE
- **SUPERSEDES:** PRIMITIVE_COMPILER_SECOND_FAMILY_VERTICAL_SLICE_OFFLINE
- **THESIS_USE:** AUTHORITATIVE_EVIDENCE

## WAVE_ID = SECOND_FAMILY_POST_VERTICAL_SLICE_FULL_REGRESSION_REPAIR_OFFLINE_GATE_2
- **DATE:** 2026-09-23
- **REPORT:** docs/evaluation/reports/SECOND_FAMILY_POST_VERTICAL_SLICE_FULL_REGRESSION_REPAIR_OFFLINE_GATE_2.md
- **ARTIFACT_DIRECTORY:** NONE
- **START_BASE:** 8703fb50
- **CODE_COMMIT:** SELF
- **EVIDENCE_COMMIT_ROLE:** SELF
- **CLASSIFICATION:** REGRESSION_REPAIR_OFFLINE
- **PRODUCT_CHANGE:** NO
- **MODEL_REQUEST_COUNT:** 0
- **CANDIDATE_CHANGE:** NO
- **CACHE_CHANGE:** NO
- **CORRECTED_BY:** SCHEMA_SYNC_AND_CANDIDATE_REFREEZE_REPAIR_OFFLINE
- **SUPERSEDES:** NONE
- **THESIS_USE:** AUTHORITATIVE_EVIDENCE

## WAVE_ID = SCHEMA_SYNC_AND_CANDIDATE_REFREEZE_REPAIR_OFFLINE
- **DATE:** 2026-09-23
- **REPORT:** docs/evaluation/semantic-benchmark/report.md
- **ARTIFACT_DIRECTORY:** docs/evaluation/semantic-benchmark/
- **START_BASE:** c69eef96
- **CODE_COMMIT:** 6eb23e8d
- **EVIDENCE_COMMIT_ROLE:** SELF
- **CLASSIFICATION:** SCHEMA_SYNC_AND_CANDIDATE_REFREEZE_OFFLINE
- **PRODUCT_CHANGE:** NO
- **MODEL_REQUEST_COUNT:** 0
- **CANDIDATE_CHANGE:** YES (measured_system.tree_hash fc88b200… → 669ea2f1…, schema_hash 3db1e1c… → 7610ff0…)
- **CACHE_CHANGE:** NO (CACHE_VERSION 100)
- **CORRECTED_BY:** NONE
- **SUPERSEDES:** SECOND_FAMILY_POST_VERTICAL_SLICE_FULL_REGRESSION_REPAIR_OFFLINE_GATE_2
- **THESIS_USE:** AUTHORITATIVE_EVIDENCE

## WAVE_ID = SECOND_FAMILY_LIVE_SCHEMA_REVALIDATION_PREREGISTRATION
- **DATE:** 2026-09-24
- **REPORT:** docs/evaluation/geometry/photo-problem-to-scene/second-family-live-schema-revalidation-preregistration/report.md
- **ARTIFACT_DIRECTORY:** docs/evaluation/geometry/photo-problem-to-scene/second-family-live-schema-revalidation-preregistration/
- **START_BASE:** 002b8da5
- **CODE_COMMIT:** NONE
- **EVIDENCE_COMMIT_ROLE:** SELF
- **CLASSIFICATION:** PREREGISTRATION_OFFLINE
- **PRODUCT_CHANGE:** NO
- **MODEL_REQUEST_COUNT:** 0
- **CANDIDATE_CHANGE:** NO (tree_hash 669ea2f1…, schema_hash 7610ff0…)
- **CACHE_CHANGE:** NO (CACHE_VERSION 100)
- **CORRECTED_BY:** NONE
- **SUPERSEDES:** NONE
- **THESIS_USE:** AUTHORITATIVE_EVIDENCE

## WAVE_ID = SECOND_FAMILY_LIVE_SCHEMA_REVALIDATION
- **DATE:** 2026-09-24
- **REPORT:** docs/evaluation/geometry/photo-problem-to-scene/second-family-live-schema-revalidation/report.md
- **ARTIFACT_DIRECTORY:** docs/evaluation/geometry/photo-problem-to-scene/second-family-live-schema-revalidation/
- **START_BASE:** ef8af771
- **CODE_COMMIT:** NONE
- **EVIDENCE_COMMIT_ROLE:** SELF
- **CLASSIFICATION:** SCHEMA_ACCEPTED_MODEL_SEMANTIC_FAILURE
- **PRODUCT_CHANGE:** NO
- **MODEL_REQUEST_COUNT:** 1
- **CANDIDATE_CHANGE:** NO (tree_hash 669ea2f1…, schema_hash 7610ff0…)
- **CACHE_CHANGE:** NO (CACHE_VERSION 100)
- **CORRECTED_BY:** SECOND_FAMILY_LIVE_MEASUREMENT_RECONCILIATION_OFFLINE
- **SUPERSEDES:** NONE
- **THESIS_USE:** AUTHORITATIVE_EVIDENCE

## WAVE_ID = SECOND_FAMILY_LIVE_MEASUREMENT_RECONCILIATION_OFFLINE
- **DATE:** 2026-09-24
- **REPORT:** docs/evaluation/geometry/photo-problem-to-scene/second-family-live-measurement-reconciliation/report.md
- **ARTIFACT_DIRECTORY:** docs/evaluation/geometry/photo-problem-to-scene/second-family-live-measurement-reconciliation/
- **START_BASE:** 532f447e
- **CODE_COMMIT:** NONE
- **EVIDENCE_COMMIT_ROLE:** SELF
- **CLASSIFICATION:** HISTORICAL_EVIDENCE_INSUFFICIENT
- **PRODUCT_CHANGE:** NO
- **MODEL_REQUEST_COUNT:** 0
- **CANDIDATE_CHANGE:** NO (tree_hash 669ea2f1…, schema_hash 7610ff0…)
- **CACHE_CHANGE:** NO (CACHE_VERSION 100)
- **CORRECTED_BY:** NONE
- **SUPERSEDES:** SECOND_FAMILY_LIVE_SCHEMA_REVALIDATION
- **THESIS_USE:** AUTHORITATIVE_EVIDENCE

## WAVE_ID = SECOND_FAMILY_LIVE_RETRY_PREREGISTRATION
- **DATE:** 2026-09-24
- **REPORT:** docs/evaluation/geometry/photo-problem-to-scene/second-family-live-retry-preregistration/report.md
- **ARTIFACT_DIRECTORY:** docs/evaluation/geometry/photo-problem-to-scene/second-family-live-retry-preregistration/
- **START_BASE:** 462645ec
- **CODE_COMMIT:** ab7d94eb
- **EVIDENCE_COMMIT_ROLE:** SELF
- **CLASSIFICATION:** PREREGISTRATION_OFFLINE
- **PRODUCT_CHANGE:** NO
- **MODEL_REQUEST_COUNT:** 0
- **CANDIDATE_CHANGE:** NO (tree_hash 669ea2f1…, schema_hash 7610ff0…)
- **CACHE_CHANGE:** NO (CACHE_VERSION 100)
- **CORRECTED_BY:** NONE
- **SUPERSEDES:** NONE
- **THESIS_USE:** AUTHORITATIVE_EVIDENCE

## WAVE_ID = SECOND_FAMILY_LIVE_RETRY
- **DATE:** 2026-09-24
- **REPORT:** docs/evaluation/geometry/photo-problem-to-scene/second-family-live-retry/report.md
- **ARTIFACT_DIRECTORY:** docs/evaluation/geometry/photo-problem-to-scene/second-family-live-retry/
- **START_BASE:** 5d92afa2
- **CODE_COMMIT:** NONE
- **EVIDENCE_COMMIT_ROLE:** SELF
- **CLASSIFICATION:** SCHEMA_ACCEPTED_PIPELINE_PASS
- **PRODUCT_CHANGE:** NO
- **MODEL_REQUEST_COUNT:** 1
- **CANDIDATE_CHANGE:** NO (tree_hash 669ea2f1…, schema_hash 7610ff0…)
- **CACHE_CHANGE:** NO (CACHE_VERSION 100)
- **CORRECTED_BY:** NONE
- **SUPERSEDES:** NONE
- **THESIS_USE:** AUTHORITATIVE_EVIDENCE

## WAVE_ID = PRISM_VERTICAL_SLICE_MERGE_READINESS_REVIEW
- **DATE:** 2026-09-24
- **REPORT:** docs/evaluation/geometry/photo-problem-to-scene/prism-vertical-slice-merge-readiness/report.md
- **ARTIFACT_DIRECTORY:** docs/evaluation/geometry/photo-problem-to-scene/prism-vertical-slice-merge-readiness/
- **START_BASE:** d3fc1c72
- **CODE_COMMIT:** NONE
- **EVIDENCE_COMMIT_ROLE:** SELF
- **CLASSIFICATION:** MERGE_READINESS_REVIEW_PASS
- **PRODUCT_CHANGE:** NO
- **MODEL_REQUEST_COUNT:** 0
- **CANDIDATE_CHANGE:** NO (tree_hash 669ea2f1…, schema_hash 7610ff0…)
- **CACHE_CHANGE:** NO (CACHE_VERSION 100)
- **CORRECTED_BY:** PRISM_MERGE_READINESS_EVIDENCE_IDENTITY_RECONCILIATION_OFFLINE
- **SUPERSEDES:** NONE
- **THESIS_USE:** AUTHORITATIVE_EVIDENCE

## WAVE_ID = PRISM_MERGE_READINESS_EVIDENCE_IDENTITY_RECONCILIATION_OFFLINE
- **DATE:** 2026-09-24
- **REPORT:** docs/evaluation/geometry/photo-problem-to-scene/prism-merge-readiness-evidence-identity-reconciliation/report.md
- **ARTIFACT_DIRECTORY:** docs/evaluation/geometry/photo-problem-to-scene/prism-merge-readiness-evidence-identity-reconciliation/
- **START_BASE:** f0d040f6
- **CODE_COMMIT:** NONE
- **EVIDENCE_COMMIT_ROLE:** SELF
- **CLASSIFICATION:** PASS_WITH_EVIDENCE_LABEL_CORRECTION
- **PRODUCT_CHANGE:** NO
- **MODEL_REQUEST_COUNT:** 0
- **CANDIDATE_CHANGE:** NO (tree_hash 669ea2f1…, schema_hash 7610ff0…)
- **CACHE_CHANGE:** NO (CACHE_VERSION 100)
- **CORRECTED_BY:** NONE
- **SUPERSEDES:** PRISM_VERTICAL_SLICE_MERGE_READINESS_REVIEW
- **THESIS_USE:** AUTHORITATIVE_EVIDENCE

## WAVE_ID = REFRESH_REMOTE_MAIN_AND_REVALIDATE_MERGE_BASE
- **DATE:** 2026-09-24
- **REPORT:** docs/evaluation/geometry/photo-problem-to-scene/remote-main-refresh-revalidation/report.md
- **ARTIFACT_DIRECTORY:** docs/evaluation/geometry/photo-problem-to-scene/remote-main-refresh-revalidation/
- **START_BASE:** f0d8f4b2
- **CODE_COMMIT:** NONE
- **EVIDENCE_COMMIT_ROLE:** SELF
- **CLASSIFICATION:** REMOTE_INTEGRATION_READY
- **PRODUCT_CHANGE:** NO
- **MODEL_REQUEST_COUNT:** 0
- **CANDIDATE_CHANGE:** NO (tree_hash 669ea2f1…, schema_hash 7610ff0…)
- **CACHE_CHANGE:** NO (CACHE_VERSION 100)
- **CORRECTED_BY:** NONE
- **SUPERSEDES:** NONE
- **THESIS_USE:** AUTHORITATIVE_EVIDENCE

## WAVE_ID = CUBOID_CUBE_VISUAL_INTEGRITY
- **DATE:** 2026-09-26
- **REPORT:** NONE (artifact-only historical wave)
- **ARTIFACT_DIRECTORY:** docs/evaluation/geometry/cuboid-cube-visual-integrity/
- **START_BASE:** 51e0c9ca
- **CODE_COMMIT:** 08c118f0
- **EVIDENCE_COMMIT_ROLE:** d9e79a00
- **CLASSIFICATION:** SUPERSEDED_EVIDENCE
- **PRODUCT_CHANGE:** YES
- **MODEL_REQUEST_COUNT:** 0
- **CANDIDATE_CHANGE:** YES (historical fd9d61dd…)
- **CACHE_CHANGE:** NO (CACHE_VERSION 102)
- **CORRECTED_BY:** CUBOID_VISUAL_SEMANTIC_CLOSURE_AND_CROSS_FAMILY_REGRESSION_AUDIT
- **SUPERSEDES:** NONE
- **THESIS_USE:** HISTORICAL_ONLY

## WAVE_ID = CUBOID_VISUAL_SEMANTIC_CLOSURE_AND_CROSS_FAMILY_REGRESSION_AUDIT
- **DATE:** 2026-09-27
- **REPORT:** docs/evaluation/geometry/cuboid-cube-semantic-closure-20260927/report.md
- **ARTIFACT_DIRECTORY:** docs/evaluation/geometry/cuboid-cube-semantic-closure-20260927/; docs/evaluation/geometry/cross-family-regression-20260927/
- **START_BASE:** d9e79a00
- **CODE_COMMIT:** 2822beb3
- **EVIDENCE_COMMIT_ROLE:** 40c20948
- **CLASSIFICATION:** PASS_WITH_EXPLICIT_TIER_A_EVIDENCE_GAPS
- **PRODUCT_CHANGE:** YES
- **MODEL_REQUEST_COUNT:** 0
- **CANDIDATE_CHANGE:** YES (tree_hash 72516eb5…, clean product commit 2822beb3)
- **CACHE_CHANGE:** NO (CACHE_VERSION 102)
- **CORRECTED_BY:** NONE
- **SUPERSEDES:** CUBOID_CUBE_VISUAL_INTEGRITY
- **THESIS_USE:** AUTHORITATIVE_WITH_DECLARED_SCOPE

## WAVE_ID = CLOSE_GENERIC_TIER_A_BROWSER_EVIDENCE_BEFORE_CUBOID_MERGE
- **DATE:** 2026-09-27
- **REPORT:** docs/evaluation/geometry/generic-tier-a-browser-closure-20260927/report.md
- **ARTIFACT_DIRECTORY:** docs/evaluation/geometry/generic-tier-a-browser-closure-20260927/
- **START_BASE:** 1c83418a
- **CODE_COMMIT:** 2747f4b926511bd526e2eab541099f01e4b8acb5
- **MEASUREMENT_COMMIT:** 2747f4b926511bd526e2eab541099f01e4b8acb5
- **EVIDENCE_COMMIT_ROLE:** 7cee042c9a539f89970722ac56eb9f490d5e753b
- **CLASSIFICATION:** GENERIC_TIER_A_BROWSER_CLOSURE_PASS_MERGE_READY
- **PRODUCT_CHANGE:** NO
- **MODEL_REQUEST_COUNT:** 0
- **CANDIDATE_CHANGE:** NO (product commit 2822beb3, tree_hash 72516eb5…)
- **CACHE_CHANGE:** NO (CACHE_VERSION 102)
- **CORRECTED_BY:** GENERIC_TIER_A_BROWSER_EVIDENCE_SEMANTIC_CORRECTION
- **SUPERSEDES:** NONE (closes the explicit NOT_MEASURED scope in the cuboid audit)
- **THESIS_USE:** HISTORICAL_ONLY

## WAVE_ID = GENERIC_TIER_A_BROWSER_EVIDENCE_SEMANTIC_CORRECTION
- **DATE:** 2026-09-27
- **REPORT:** docs/evaluation/geometry/generic-tier-a-browser-semantic-correction-20260927/report.md
- **ARTIFACT_DIRECTORY:** docs/evaluation/geometry/generic-tier-a-browser-semantic-correction-20260927/
- **START_BASE:** 26479cc7
- **CODE_COMMIT:** NONE
- **EVIDENCE_COMMIT_ROLE:** da86db7f138b1a3a9293cb6fb9f5c64444faca71
- **CLASSIFICATION:** PRODUCT_REGRESSION_FOUND_AND_PRIOR_EVIDENCE_INVALIDATED
- **PRODUCT_CHANGE:** NO
- **MODEL_REQUEST_COUNT:** 0
- **CANDIDATE_CHANGE:** NO (product commit 2822beb3, tree_hash 72516eb5…)
- **CACHE_CHANGE:** NO (CACHE_VERSION 102)
- **CORRECTED_BY:** CROSS_FAMILY_SCENE3D_PRODUCT_SEMANTIC_REPAIR
- **SUPERSEDES:** CLOSE_GENERIC_TIER_A_BROWSER_EVIDENCE_BEFORE_CUBOID_MERGE
- **THESIS_USE:** AUTHORITATIVE_CORRECTION

## WAVE_ID = CROSS_FAMILY_SCENE3D_PRODUCT_SEMANTIC_REPAIR
- **DATE:** 2026-09-27
- **REPORT:** docs/evaluation/geometry/runs/20260927-cross-family-scene3d-product-semantic-repair/REPORT.md
- **ARTIFACT_DIRECTORY:** docs/evaluation/geometry/runs/20260927-cross-family-scene3d-product-semantic-repair/
- **START_BASE:** 686a8e0e5f8540725c0a500429cc18a7faf1015a
- **CODE_COMMIT:** 5dd9f2b2851cdef64de0272f9a3d2b41bb05ad45
- **MEASUREMENT_COMMIT:** f5fefce02bf6f930c29b58a12979340ac2affe5d
- **EVIDENCE_COMMIT_ROLE:** 5f2f24f064d8f06de41e76353fb61ff5a74e7afa
- **CLASSIFICATION:** READY_FOR_HUMAN_VISUAL_REVIEW
- **PRODUCT_CHANGE:** YES
- **MODEL_REQUEST_COUNT:** 0
- **CANDIDATE_CHANGE:** YES (72516eb5… -> 5d8eb3af…, product commit 5dd9f2b2)
- **CACHE_CHANGE:** NO (CACHE_VERSION 102, fingerprint b1714b56… unchanged)
- **CORRECTED_BY:** CROSS_FAMILY_HIDDEN_LINE_OCCLUSION_ORACLE_AND_FORMATION_REPAIR
- **SUPERSEDES:** NONE (repairs the regression identified by `GENERIC_TIER_A_BROWSER_EVIDENCE_SEMANTIC_CORRECTION`; does not rewrite that historical finding)
- **THESIS_USE:** AUTHORITATIVE_AUTOMATION_PENDING_HUMAN_VISUAL_REVIEW

## WAVE_ID = CROSS_FAMILY_HIDDEN_LINE_OCCLUSION_ORACLE_AND_FORMATION_REPAIR
- **DATE:** 2026-09-28
- **REPORT:** docs/evaluation/geometry/runs/20260928-cross-family-hidden-line-occlusion-oracle-and-formation-repair/REPORT.md
- **ARTIFACT_DIRECTORY:** docs/evaluation/geometry/runs/20260928-cross-family-hidden-line-occlusion-oracle-and-formation-repair/
- **START_BASE:** 532d436611d58023cfabac6020f1ad85e2446e16
- **CODE_COMMIT:** 50a31e0b7124cb038ff5c56dd9c856778a263725
- **ORACLE_HARNESS_COMMIT:** 1dab0f7db516e8ce8eee1280ded4d220a10018d5
- **MEASUREMENT_COMMIT:** e115c31df24efc35fe1d5590e3cab6737b5b13d8
- **EVIDENCE_COMMIT_ROLE:** 09934eb7d0850d3f1f6d5c4f4c79f93b33bb92d9
- **CLASSIFICATION:** VERIFICATION_NOT_CLEAN
- **PRODUCT_CHANGE:** YES
- **MODEL_REQUEST_COUNT:** 0
- **CANDIDATE_CHANGE:** YES (tree_hash 5d8eb3af… -> 31725284…, CACHE_VERSION unchanged)
- **CACHE_CHANGE:** NO (CACHE_VERSION 102, fingerprint b1714b56… unchanged)
- **CORRECTED_BY:** VERIFICATION_CLEANUP_AFTER_OCCLUSION_REPAIR
- **SUPERSEDES:** NONE (additively corrects the prior readiness conclusion; historical artifacts remain intact)
- **THESIS_USE:** AUTHORITATIVE_CORRECTION_NOT_READY_FOR_HUMAN_REVIEW
- **AUTHORITATIVE_FILES:** `RUN.json` · `MANIFEST.json` · `HANDOFF.md` · `results/VERIFICATION_SUMMARY.json` · `inputs/human_expected_visibility.json` · `contact-sheet.png` (trong ARTIFACT_DIRECTORY) · recovery inventory `docs/evaluation/geometry/worktree-recovery/WORKTREE_RECOVERY_INVENTORY.json`
- **RUN_ID_POLICY:** LEGACY_LONG_RUN_ID — giữ nguyên đường dẫn; run mới theo `docs/evaluation/RUN_NAMING.md`

## WAVE_ID = VERIFICATION_CLEANUP_AFTER_OCCLUSION_REPAIR
- **DATE:** 2026-09-28
- **REPORT:** docs/evaluation/geometry/runs/w09-verify-cleanup/REPORT.md
- **ARTIFACT_DIRECTORY:** docs/evaluation/geometry/runs/w09-verify-cleanup/
- **START_BASE:** 42c736ead3433d32d4cd2b1c3fd93c41e691d3ae
- **CODE_COMMIT:** f337323f599964246507017613cfe3c016e71a32 (backend) · 7b8528a95d364c6a624922d9acff789239ed3ef8 (frontend + harness)
- **MEASUREMENT_COMMIT:** defb77ede20bd952b08ac4996d3a2bf40bcfdb1a
- **EVIDENCE_COMMIT_ROLE:** 774377dd
- **CLASSIFICATION:** READY_FOR_HUMAN_VISUAL_REVIEW
- **PRODUCT_CHANGE:** YES
- **MODEL_REQUEST_COUNT:** 0
- **CANDIDATE_CHANGE:** YES (tree_hash 31725284… -> 3bc9415b…, CACHE_VERSION unchanged)
- **CACHE_CHANGE:** NO (CACHE_VERSION 102, fingerprint b1714b56… unchanged)
- **CORRECTED_BY:** HUMAN_VISUAL_REVIEW_AND_PEDAGOGICAL_PLAYBACK_CLOSURE (human review FAIL_REQUIRES_PEDAGOGICAL_VISUAL_REPAIR, recorded additively in the w10 run; this run's files stay byte-identical)
- **SUPERSEDES:** NONE (additively corrects VERIFICATION_NOT_CLEAN of the occlusion wave; its artifacts and frozen registry remain byte-identical)
- **THESIS_USE:** HISTORICAL_AUTOMATION — human visual review FAILED afterwards; do not cite as visual acceptance. `inputs/REGISTERED_CAMERA_PREIMAGES.json` stays authoritative for the frozen registry.
- **AUTHORITATIVE_FILES:** `RUN.json` · `MANIFEST.json` · `HANDOFF.md` · `results/VERIFICATION_SUMMARY.json` · `results/BACKEND_FAILURE_RECONCILIATION.json` · `diagnostics/VERIFICATION_FAILURE_INVENTORY.json` · `diagnostics/MEASUREMENT_ATTEMPTS.json` · `inputs/REGISTERED_CAMERA_PREIMAGES.json` · `images/contact-sheet.png`
- **RUN_ID_POLICY:** SHORT_RUN_ID (`docs/evaluation/RUN_NAMING.md`)

## WAVE_ID = HUMAN_VISUAL_REVIEW_AND_PEDAGOGICAL_PLAYBACK_CLOSURE
- **DATE:** 2026-09-29
- **REPORT:** docs/evaluation/geometry/runs/w10-pedagogical-playback/REPORT.md
- **ARTIFACT_DIRECTORY:** docs/evaluation/geometry/runs/w10-pedagogical-playback/
- **START_BASE:** be23e88d
- **CODE_COMMIT:** 9dc56ae1 · f5a3adf2 (backend + frontend) · 7a03e50d · f0deaa0d (frontend)
- **MEASUREMENT_COMMIT:** 40ce889fe83b7220195a89f50c22757a02770511 (post-processing 52de6f22)
- **EVIDENCE_COMMIT_ROLE:** 8a09a5d8
- **CLASSIFICATION:** READY_FOR_HUMAN_VISUAL_REVIEW
- **PRODUCT_CHANGE:** YES
- **MODEL_REQUEST_COUNT:** 0
- **CANDIDATE_CHANGE:** YES (tree_hash 3bc9415b… -> 875bc19c… -> 8539acbc…)
- **CACHE_CHANGE:** YES (CACHE_VERSION 102 -> 103, user decision; fingerprint b1714b56… unchanged)
- **CORRECTED_BY:** W11_PEDAGOGICAL_FORMULA_VISUAL_POLISH_AND_HUMAN_REREVIEW (human review FAIL_REQUIRES_TARGETED_PEDAGOGICAL_REPAIR, recorded additively in the w11 run; this run's files stay byte-identical)
- **SUPERSEDED_FOR_HUMAN_VERDICT:** W11_PEDAGOGICAL_FORMULA_VISUAL_POLISH_AND_HUMAN_REREVIEW — its images are no longer the ones a reviewer should judge; its automation stays valid for the w10 candidate `8539acbc…`
- **CORRECTS:** VERIFICATION_CLEANUP_AFTER_OCCLUSION_REPAIR (human review FAIL_REQUIRES_PEDAGOGICAL_VISUAL_REPAIR)
- **SUPERSEDES:** NONE (w09 and occlusion-wave artifacts and the frozen registry remain byte-identical; the registry's expectations transfer to the new default camera only under `DECLARED_CAMERA_CHANGE`)
- **THESIS_USE:** HISTORICAL_AUTOMATION — human visual review FAILED afterwards (W10-H1…H9); do not cite as visual acceptance.
- **AUTHORITATIVE_FILES:** `RUN.json` · `MANIFEST.json` · `HANDOFF.md` · `REPORT.md` · `results/VERIFICATION_SUMMARY.json` · `results/BROWSER_EVIDENCE.json` · `results/OCCLUSION_MEASUREMENT.json` · `results/GOLDEN_REVIEW.json` · `images/playback/PLAYBACK_EVIDENCE.json` · `images/crops/CROPS_INDEX.json` · `images/contact-sheet.png` · `diagnostics/MEASUREMENT_ATTEMPTS.json` · `inputs/W09_HUMAN_VISUAL_REVIEW.json`
- **RUN_ID_POLICY:** SHORT_RUN_ID (`docs/evaluation/RUN_NAMING.md`)

## WAVE_ID = W11_PEDAGOGICAL_FORMULA_VISUAL_POLISH_AND_HUMAN_REREVIEW
- **DATE:** 2026-09-29
- **REPORT:** docs/evaluation/geometry/runs/w11-pedagogical-polish/REPORT.md
- **ARTIFACT_DIRECTORY:** docs/evaluation/geometry/runs/w11-pedagogical-polish/
- **START_BASE:** b9193766
- **CODE_COMMIT:** f147dde6 (backend) · e186b4cf · e633ad0c · 60292ecf (frontend)
- **MEASUREMENT_COMMIT:** 39e5404686fdf25ddae310759c87c8c64dd8dc41 (trace post-processing ac19e03d)
- **EVIDENCE_COMMIT_ROLE:** 5e3dbab4
- **CLASSIFICATION:** READY_FOR_HUMAN_VISUAL_REVIEW
- **PRODUCT_CHANGE:** YES
- **MODEL_REQUEST_COUNT:** 0
- **CANDIDATE_CHANGE:** YES (tree_hash 8539acbc… -> df04a613…, refrozen once)
- **CACHE_CHANGE:** YES (CACHE_VERSION 103 -> 104; fingerprint b1714b56… unchanged)
- **CORRECTED_BY:** W12_PEDAGOGICAL_TIMELINE_AND_SOURCE_GROUNDING_CLOSURE (human review NEEDS_CHANGES, W11-H1…H5, recorded additively in the w12 run; this run's files stay byte-identical)
- **SUPERSEDED_FOR_HUMAN_VERDICT:** W12_PEDAGOGICAL_TIMELINE_AND_SOURCE_GROUNDING_CLOSURE — its images are no longer the ones a reviewer should judge; its automation stays valid for the w11 candidate `df04a613…`, except that its LLM route served a GIVEN length absent from the text (W11-H5, closed in w12)
- **CORRECTS:** HUMAN_VISUAL_REVIEW_AND_PEDAGOGICAL_PLAYBACK_CLOSURE (human review FAIL_REQUIRES_TARGETED_PEDAGOGICAL_REPAIR)
- **SUPERSEDES:** HUMAN_VISUAL_REVIEW_AND_PEDAGOGICAL_PLAYBACK_CLOSURE for the human verdict only (w10, w09, the occlusion wave and the frozen registry remain byte-identical; the registry's expectations transfer under `DECLARED_CAMERA_CHANGE`)
- **THESIS_USE:** HISTORICAL_AUTOMATION — human visual review NEEDS_CHANGES afterwards (W11-H1…H5); do not cite as visual acceptance.
- **AUTHORITATIVE_FILES:** `RUN.json` · `MANIFEST.json` · `HANDOFF.md` · `REPORT.md` · `results/VERIFICATION_SUMMARY.json` · `results/BROWSER_EVIDENCE.json` · `results/OCCLUSION_MEASUREMENT.json` · `results/PLAYBACK_EVIDENCE.json` · `results/HIDDEN_EDGE_CROPS.json` · `images/<family>/SHEET.png` · `diagnostics/MEASUREMENT_ATTEMPTS.json` · `diagnostics/FORMULA_PROVENANCE_TRACE_BEFORE.json` · `diagnostics/FORMULA_PROVENANCE_TRACE_AFTER.json` · `inputs/W10_HUMAN_VISUAL_REVIEW.json` · `inputs/CANDIDATE_DIVERGENCE_CORRECTION.json`
- **RUN_ID_POLICY:** SHORT_RUN_ID (`wNN-short-slug`, `docs/evaluation/RUN_NAMING.md`)

## WAVE_ID = W12_PEDAGOGICAL_TIMELINE_AND_SOURCE_GROUNDING_CLOSURE
- **DATE:** 2026-09-30 … 2026-10-01
- **REPORT:** docs/evaluation/geometry/runs/w12-pedagogical-grounding-closure/REPORT.md
- **ARTIFACT_DIRECTORY:** docs/evaluation/geometry/runs/w12-pedagogical-grounding-closure/
- **START_BASE:** a4fd5fec
- **CODE_COMMIT:** 79eb1e59 · 8aaeae80 (backend) · 98b505ef · 233f8720 · 4014f311 (frontend) · d17550c3 (cache)
- **MEASUREMENT_COMMIT:** c243968b1ec263d2ab48040d569eec45efe9cfaa
- **EVIDENCE_COMMIT_ROLE:** 442584cf
- **CLASSIFICATION:** READY_FOR_HUMAN_VISUAL_REVIEW
- **PRODUCT_CHANGE:** YES
- **MODEL_REQUEST_COUNT:** 0
- **CANDIDATE_CHANGE:** YES (tree_hash df04a613… -> 8ffd6d46… -> 548f5b3b…, frozen three times; the last freeze moved only the product commit 8aaeae80 -> 4014f311)
- **CACHE_CHANGE:** YES (CACHE_VERSION 104 -> 105; fingerprint b1714b56… unchanged)
- **CORRECTED_BY:** W13_GEOMETRY_CAPABILITY_AND_NON_ABSOLUTE_ARCHITECTURE_PREREGISTRATION (human review NEEDS_CHANGES, W12-H1…H4, recorded additively in the w13 run; this run's files stay byte-identical)
- **CORRECTS:** W11_PEDAGOGICAL_FORMULA_VISUAL_POLISH_AND_HUMAN_REREVIEW (human review NEEDS_CHANGES)
- **SUPERSEDES:** W11_PEDAGOGICAL_FORMULA_VISUAL_POLISH_AND_HUMAN_REREVIEW for the human verdict only (w11, w10, w09, the occlusion wave and the frozen registry remain byte-identical); inside this run the attempts BROWSER-1 (e115eede) and BROWSER-2 (7b039621, committed in 399fc423) are superseded — `diagnostics/MEASUREMENT_ATTEMPTS.json`
- **THESIS_USE:** AUTHORITATIVE_AUTOMATION_FOR_CANDIDATE_548f5b3b — human visual review NEEDS_CHANGES afterwards (W12-H1…H4); do not cite as visual acceptance. It was the latest product measurement until w14 (candidate 40263983, measurement 380db58c); it stays valid for candidate 548f5b3b.
- **SUPERSEDED_FOR_HUMAN_VERDICT:** W14_GENERIC_FORMATION_AND_ASSUMPTION_FOUNDATION — its images are no longer the ones a reviewer should judge (w14 changes the formation of every polyhedral family); this run's files stay byte-identical.
- **AUTHORITATIVE_FILES:** `RUN.json` · `MANIFEST.json` · `HANDOFF.md` · `REPORT.md` · `results/VERIFICATION_SUMMARY.json` · `results/BROWSER_EVIDENCE.json` · `results/OCCLUSION_MEASUREMENT.json` · `results/PLAYBACK_EVIDENCE.json` · `results/HIDDEN_EDGE_CROPS.json` · `results/BACKEND_COUNT_RECONCILIATION.json` · `images/<family>/SHEET.png` · `diagnostics/MEASUREMENT_ATTEMPTS.json` · `diagnostics/hue-gate-known-answer-e115eede/KNOWN_ANSWER.json` · `diagnostics/WORKTREE_CLEANUP.json` · `inputs/W11_HUMAN_VISUAL_REVIEW.json` · `inputs/CANDIDATE_DIVERGENCE_CORRECTION.json`
- **RUN_ID_POLICY:** SHORT_RUN_ID (`wNN-short-slug`, `docs/evaluation/RUN_NAMING.md`)

## WAVE_ID = W13_GEOMETRY_CAPABILITY_AND_NON_ABSOLUTE_ARCHITECTURE_PREREGISTRATION
- **DATE:** 2026-10-01
- **REPORT:** docs/evaluation/geometry/runs/w13-geometry-preregistration/REPORT.md
- **ARTIFACT_DIRECTORY:** docs/evaluation/geometry/runs/w13-geometry-preregistration/
- **START_BASE:** bf5a7907
- **CODE_COMMIT:** NONE (no product code; the docs-audit allow-list in backend/scripts gained the W13/W14 action names)
- **MEASUREMENT_COMMIT:** NONE (offline reader probe only, run at bf5a7907)
- **EVIDENCE_COMMIT_ROLE:** SELF
- **CLASSIFICATION:** ARCHITECTURE_PREREGISTRATION_READY
- **PRODUCT_CHANGE:** NO
- **MODEL_REQUEST_COUNT:** 0
- **CANDIDATE_CHANGE:** NO (548f5b3b…, product commit 4014f311; verify PASS)
- **CACHE_CHANGE:** NO (CACHE_VERSION 105; verify PASS)
- **CORRECTED_BY:** NONE
- **CORRECTS:** W12_PEDAGOGICAL_TIMELINE_AND_SOURCE_GROUNDING_CLOSURE (human review NEEDS_CHANGES)
- **SUPERSEDES:** NONE (w12 stays the latest product automation; w13 adds no images, so nothing is superseded for the human verdict)
- **THESIS_USE:** ARCHITECTURE_AUDIT_AND_PREREGISTRATION — capability-by-layer matrix and the next-wave preregistration; not empirical results, not visual acceptance.
- **AUTHORITATIVE_FILES:** `RUN.json` · `MANIFEST.json` · `HANDOFF.md` · `REPORT.md` · `inputs/W12_HUMAN_VISUAL_REVIEW.json` · `results/ABSOLUTE_ASSUMPTION_INVENTORY.json` · `results/REMAINING_GEOMETRY_CAPABILITY_MATRIX.json` · `diagnostics/SOURCE_GROUNDING_PHRASING_PROBE.json` · `docs/architecture/geometry_capability_matrix_v2.json` · `docs/architecture/GEOMETRY_CAPABILITY_AND_NON_ABSOLUTE_AUDIT.md` · `docs/architecture/GENERIC_GEOMETRY_FOUNDATION_PREREGISTRATION.md`
- **RUN_ID_POLICY:** SHORT_RUN_ID (`wNN-short-slug`, `docs/evaluation/RUN_NAMING.md`)

## WAVE_ID = W14_GENERIC_FORMATION_AND_ASSUMPTION_FOUNDATION
- **DATE:** 2026-10-01 … 2026-10-02
- **REPORT:** docs/evaluation/geometry/runs/w14-generic-formation-assumption/REPORT.md
- **ARTIFACT_DIRECTORY:** docs/evaluation/geometry/runs/w14-generic-formation-assumption/
- **START_BASE:** ce9c672d
- **CODE_COMMIT:** 44f2dd32 (formation) · d537cf74 (trust policy) · 2f2c97b2 (length vocabulary) · 69d3c985 (sample text, frontend/src) · 733435ac (cache) · a2af56e4 (cleanup; last product commit)
- **MEASUREMENT_COMMIT:** 380db58c37da6088d8dba47647d15ba7ed77cf35
- **EVIDENCE_COMMIT_ROLE:** 54af39a4
- **CLASSIFICATION:** FORMATION_FOUNDATION_INCOMPLETE
- **PRODUCT_CHANGE:** YES
- **MODEL_REQUEST_COUNT:** 0
- **CANDIDATE_CHANGE:** YES (tree_hash 548f5b3b… -> 40263983…, 105 files, frozen once at a2af56e4)
- **CACHE_CHANGE:** YES (CACHE_VERSION 105 -> 106; fingerprint b1714b56… unchanged)
- **CORRECTED_BY:** W15_SOURCE_CONSTRAINT_AND_ASSUMPTION_CLOSURE — w15 traced every Track B failure of this run to a root cause (RC1 coordinates classed as model realisation, RC2 `claimed` relations, RC3 stale demo contracts, RC4/RC5 invalid counterexample witnesses) and shipped the gate; decision W15-D1 settles W14-D1 (a refused program is not in the enforced formation set). This run's files stay byte-identical.
- **CORRECTS:** W12_PEDAGOGICAL_TIMELINE_AND_SOURCE_GROUNDING_CLOSURE (answers its human review W12-H1…H4, as preregistered in w13)
- **SUPERSEDES:** W12_PEDAGOGICAL_TIMELINE_AND_SOURCE_GROUNDING_CLOSURE for the human verdict only (w12, w13, the occlusion wave and the frozen registry remain byte-identical); nothing superseded inside this run
- **SUPERSEDED_FOR_HUMAN_VERDICT:** W15_SOURCE_CONSTRAINT_AND_ASSUMPTION_CLOSURE — w15 changes what the cross-section shows (the closed fill) and measures a new candidate; a reviewer judges the w15 images.
- **THESIS_USE:** AUTHORITATIVE_AUTOMATION_FOR_CANDIDATE_40263983 — not visual acceptance (no human review yet). It was the latest product measurement until w15 (candidate b3b7eb79, measurement c57ebd1b); it stays valid for candidate 40263983. Formation by shape class for compiler and LLM programs (six families and served gold COMPLETED; the refused gold negative n2 AMBIGUOUS_TOPOLOGY); assumption gate NOT shipped — the census is a corpus result inside the certificate scope (C0 ∪ C1 over PHEP_DO_C1), never a soundness proof; the frozen hidden-line expectations do not transfer to the four scenes S4 changed.
- **AUTHORITATIVE_FILES:** `RUN.json` · `MANIFEST.json` · `HANDOFF.md` · `REPORT.md` · `results/BROWSER_EVIDENCE.json` · `results/OCCLUSION_MEASUREMENT.json` · `results/PLAYBACK_EVIDENCE.json` · `results/HIDDEN_EDGE_CROPS.json` · `images/<family>/FILMSTRIP.png` · `images/<family>/SHEET.png` · `diagnostics/MEASUREMENT_ATTEMPTS.json` · `diagnostics/S4_INVENTORY_AT_380db58c.json` · `diagnostics/OCCLUSION_TRANSFER_DIAGNOSTIC.json` · `diagnostics/ASSUMPTION_CENSUS.json` · `diagnostics/ASSUMPTION_MECHANISM_DECISION.json` · `diagnostics/SOURCE_GROUNDING_PHRASING_PROBE_W14.json` · `diagnostics/PROOF_CACHE_ROW_W14.json` · `diagnostics/TRUST_POLICY_CALLERS.json` · `diagnostics/WORKTREE_CLEANUP.json` · `inputs/W14_SCOPE_DECISIONS.json` · `inputs/CANDIDATE_DIVERGENCE_CORRECTION.json`
- **RUN_ID_POLICY:** SHORT_RUN_ID (`wNN-short-slug`, `docs/evaluation/RUN_NAMING.md`)

## WAVE_ID = W15_SOURCE_CONSTRAINT_AND_ASSUMPTION_CLOSURE
- **DATE:** 2026-10-02 … 2026-10-03
- **REPORT:** docs/evaluation/geometry/runs/w15-assumption-closure/REPORT.md
- **ARTIFACT_DIRECTORY:** docs/evaluation/geometry/runs/w15-assumption-closure/
- **START_BASE:** 4f6a0ab6
- **CODE_COMMIT:** 5dd8e7f5 (solid_faces) · cf57332b (reader + certificate) · 6fa6e582 (fully-read counterexample) · 2305f072 (phrasings, scope) · a1b17fef (symbol-key binding) · 45d014b0 (route wiring, U3) · 33b11a79 (U5) · 8239a2a4 (section fill) · 0579d559 (cache) · d41176f2 (review simplifications) · 909a3a2d (section fill without depth test) · 41a26f11 (final-review soundness fix; last product commit)
- **MEASUREMENT_COMMIT:** c57ebd1b4b34abe14947a97d8169dfead99ab622
- **EVIDENCE_COMMIT_ROLE:** 23cc880a (supersedes 751169dd, measured at e5b88647 on the intermediate candidate aaa5b5bd)
- **CLASSIFICATION:** READY_FOR_HUMAN_VISUAL_REVIEW
- **PRODUCT_CHANGE:** YES
- **MODEL_REQUEST_COUNT:** 0
- **CANDIDATE_CHANGE:** YES (tree_hash 40263983… -> b3b7eb79…, 107 files; frozen three times — d41176f2 and 909a3a2d gave the intermediate aaa5b5bd…, 41a26f11 gave b3b7eb79)
- **CACHE_CHANGE:** YES (CACHE_VERSION 106 -> 107 in 0579d559, real-row proof; fingerprint b1714b56… unchanged)
- **CORRECTED_BY:** W16_PREMERGE_SOUNDNESS_AND_VISUAL_EVIDENCE_CLOSURE — w16 reproduced two soundness gaps of this run's certificate at its RED commit: a plane-equation literal accepted for any proportional text equation, so five wrong-entity programs were served; a relation the text asks to prove read as a premise, so seven programs were served. W16 closed both. It also found that this run's fill was drawn over the solid edges, and that its sheets printed blank refusal cells (the builder read `negative[viewport]`). This run's files stay byte-identical.
- **CORRECTS:** W14_GENERIC_FORMATION_AND_ASSUMPTION_FOUNDATION (Track B root causes RC1–RC5 and the shipped gate; W15-D1 settles W14-D1)
- **SUPERSEDES:** W14_GENERIC_FORMATION_AND_ASSUMPTION_FOUNDATION for the human verdict only; inside this run, the evidence of 751169dd (M2) is superseded by 23cc880a (M3) after the final-review fix, and the failed first browser attempt is kept apart in `diagnostics/browser-attempt1-c1638891/`
- **SUPERSEDED_FOR_HUMAN_VERDICT:** W16_PREMERGE_SOUNDNESS_AND_VISUAL_EVIDENCE_CLOSURE — w16 changes how the cross-section fill sits against the edges, completes the refusal panels and measures a new candidate; a reviewer judges the w16 images.
- **THESIS_USE:** AUTHORITATIVE_AUTOMATION_FOR_CANDIDATE_b3b7eb79 — not visual acceptance (human review NOT_APPROVED). It was the latest product measurement until w16 (candidate 9bb0aaa7, measurement 7f3658b0); it stays valid for candidate b3b7eb79, with the two certificate gaps w16 closed. The assumption certificate (C0 ∪ C1 over volume/area/distance, closed vocabulary) is a corpus result inside the registered scope, never a general soundness proof; enforcement covers polyhedral texts only (U3).
- **AUTHORITATIVE_FILES:** `RUN.json` · `MANIFEST.json` · `HANDOFF.md` · `REPORT.md` · `results/BROWSER_EVIDENCE.json` · `results/OCCLUSION_MEASUREMENT.json` · `results/PLAYBACK_EVIDENCE.json` · `results/HIDDEN_EDGE_CROPS.json` · `images/<family>/FILMSTRIP.png` · `images/<family>/SHEET.png` · `diagnostics/MEASUREMENT_ATTEMPTS.json` · `diagnostics/ASSUMPTION_CENSUS_W15_R3.json` · `diagnostics/ASSUMPTION_MECHANISM_DECISION_W15_R3.json` · `diagnostics/TRACK_B_ROOT_CAUSE_TABLE.json` · `diagnostics/GOLD_ROW_VERIFICATION.json` · `diagnostics/PROOF_CACHE_ROW_W15.json` · `diagnostics/logs/FAULT_INJECTION_ASSUMPTION_GATE_FINAL.log` · `diagnostics/PONYTAIL_REVIEW.json` · `diagnostics/WORKTREE_CLEANUP.json` · `diagnostics/TEMP_FILE_INVENTORY.json` · `inputs/W15_SCOPE_DECISIONS.json` · `inputs/CANDIDATE_DIVERGENCE_CORRECTION.json`
- **RUN_ID_POLICY:** SHORT_RUN_ID (`wNN-short-slug`, `docs/evaluation/RUN_NAMING.md`)

## WAVE_ID = W16_PREMERGE_SOUNDNESS_AND_VISUAL_EVIDENCE_CLOSURE
- **DATE:** 2026-10-03
- **REPORT:** docs/evaluation/geometry/runs/w16-premerge-closure/REPORT.md
- **ARTIFACT_DIRECTORY:** docs/evaluation/geometry/runs/w16-premerge-closure/
- **START_BASE:** 8a339d17
- **CODE_COMMIT:** 24161657 (plane binding) · 93d4ec69 (goal clauses) · 29da8e5a (section fill under the edges, frontend/src) · 2ec02b3a (cache) · 6b120036 (primed plane names; last product commit)
- **MEASUREMENT_COMMIT:** 7f3658b00f48dae854e5ab2527ca0ff3f701f828
- **EVIDENCE_COMMIT_ROLE:** 705970dd (browser, occlusion, playback, sheets, T3, gates); the failed first browser attempt at 55cde06e is kept apart in `diagnostics/browser-attempt1-55cde06e/`
- **CLASSIFICATION:** READY_FOR_HUMAN_VISUAL_REVIEW
- **PRODUCT_CHANGE:** YES
- **MODEL_REQUEST_COUNT:** 0
- **CANDIDATE_CHANGE:** YES (tree_hash b3b7eb79… -> 9bb0aaa7…, 107 files; frozen twice — 2ec02b3a gave the intermediate 8d14469b…, 6b120036 gave 9bb0aaa7)
- **CACHE_CHANGE:** YES (CACHE_VERSION 107 -> 108 in 2ec02b3a, real-row proof; fingerprint b1714b56… unchanged)
- **CORRECTED_BY:** W17_OPERATION_BINDING_AND_ON_SCENE_ANNOTATIONS — w17 closed this run's declared limit A′ (a construct_section on a correctly pinned plane other than the one the text cuts was certified and served, area 9 where the text gives 16) and the goal-clause datum that grounding still read outside the polyhedral scope; it also traced this run's cube "cạnh 4" refusal image to a fixture-generator defect (the text stayed valid while the contract carried AB = 0). This run's files stay byte-identical.
- **CORRECTS:** W15_SOURCE_CONSTRAINT_AND_ASSUMPTION_CLOSURE (plane-equation entity binding, goal clauses as premises, fill drawn over the edges, blank refusal cells)
- **SUPERSEDES:** W15_SOURCE_CONSTRAINT_AND_ASSUMPTION_CLOSURE for the human verdict only; inside this run, census round 1 and the first backend fault-injection run (before the primed-name fix) are superseded by round 2 and the final run
- **SUPERSEDED_FOR_HUMAN_VERDICT:** W17_OPERATION_BINDING_AND_ON_SCENE_ANNOTATIONS — w17 adds on-figure labels, the Số đo/Kết quả chips, cause-specific refusal panels and named group steps, and measures a new candidate; a reviewer judges the w17 images.
- **THESIS_USE:** AUTHORITATIVE_AUTOMATION_FOR_CANDIDATE_9bb0aaa7 — not visual acceptance (human review NOT_APPROVED). It was the latest product measurement until w17 (candidate d63d6fd4, measurement 99925723); it stays valid for candidate 9bb0aaa7, with limit A′ that w17 closed. The certificate scope of w15 is unchanged; inside it, "same entity" now holds for plane equations, and goal clauses are never premises. Declared limit A′: a construction that uses an entity other than the one the text names is not checked. The census is a corpus result inside the registered scope, never a general soundness proof.
- **AUTHORITATIVE_FILES:** `RUN.json` · `MANIFEST.json` · `HANDOFF.md` · `REPORT.md` · `results/BROWSER_EVIDENCE.json` · `results/OCCLUSION_MEASUREMENT.json` · `results/PLAYBACK_EVIDENCE.json` · `results/HIDDEN_EDGE_CROPS.json` · `images/<family>/SHEET.png` · `images/<family>/FILMSTRIP.png` · `diagnostics/MEASUREMENT_ATTEMPTS.json` · `diagnostics/PROBE_W16_PHASE1_6d01511.json` · `diagnostics/ASSUMPTION_CENSUS_W16_R2.json` · `diagnostics/ASSUMPTION_MECHANISM_DECISION_W16_R2.json` · `diagnostics/PROOF_CACHE_ROW_W16.json` · `diagnostics/logs/FAULT_INJECTION_W16_FINAL.log` · `diagnostics/logs/FAULT_INJECTION_W16_FRONTEND.log` · `diagnostics/PONYTAIL_REVIEW.json` · `diagnostics/WORKTREE_CLEANUP.json` · `diagnostics/TEMP_FILE_INVENTORY.json` · `inputs/CANDIDATE_DIVERGENCE_CORRECTION.json`
- **RUN_ID_POLICY:** SHORT_RUN_ID (`wNN-short-slug`, `docs/evaluation/RUN_NAMING.md`)

## WAVE_ID = W17_OPERATION_BINDING_AND_ON_SCENE_ANNOTATIONS
- **DATE:** 2026-10-03 / 2026-10-04
- **REPORT:** docs/evaluation/geometry/runs/w17-operation-annotations/REPORT.md
- **ARTIFACT_DIRECTORY:** docs/evaluation/geometry/runs/w17-operation-annotations/
- **START_BASE:** dd6e86b0
- **CODE_COMMIT:** 2678b363 (operation binding) · 0b71502b (goal-only givens, refusal causes) · ce9a4c1f (group-step label) · 8e002028 (annotation binding) · fa5f8382 (labels and chips, frontend/src) · 2c7d4134, 240ecba5, dbb38b95 (Task 7, frontend/src) · fadfd10e (cache) · add4afb0 (ponytail) · d3817d5f (final-review fix; last product commit)
- **MEASUREMENT_COMMIT:** 99925723e6179e9f67852a2aa393db163dd07c4f
- **EVIDENCE_COMMIT_ROLE:** 781c14e5 (browser, occlusion, playback, sheets, T3, gates, frontend fault injections); kept apart: the complete measurement at c5592c1a on the intermediate candidate (`diagnostics/evidence-intermediate-c5592c1a/`, images at f07b0d24) and the failed attempt 1 at 83f101e4 (`diagnostics/browser-final-attempt1-83f101e4/`)
- **CLASSIFICATION:** READY_FOR_HUMAN_VISUAL_REVIEW
- **PRODUCT_CHANGE:** YES
- **MODEL_REQUEST_COUNT:** 0
- **CANDIDATE_CHANGE:** YES (tree_hash 9bb0aaa7… -> d63d6fd4…, 109 files; frozen twice — add4afb0 gave the intermediate d4a24eba…, d3817d5f gave d63d6fd4)
- **CACHE_CHANGE:** YES (CACHE_VERSION 108 -> 109 in fadfd10e, real-row proof; fingerprint b1714b56… unchanged)
- **CORRECTED_BY:** W18_CONSTRUCTION_BINDING_AND_FOCUSED_ANNOTATIONS — w18 checks point constructions (midpoints, projections) against the text relation by identity, closing part of this run's declared limit "constructions other than section cuts are not checked": before w18 a projection onto the wrong line or plane, a swapped "lần lượt" list, a renamed target and a same-coordinate identity swap were served. This run's files stay byte-identical.
- **CORRECTS:** W16_PREMERGE_SOUNDNESS_AND_VISUAL_EVIDENCE_CLOSURE (declared limit A′, goal clauses read as data by grounding outside the polyhedral scope, the cube "cạnh 4" refusal image)
- **SUPERSEDES:** W16_PREMERGE_SOUNDNESS_AND_VISUAL_EVIDENCE_CLOSURE for the human verdict only; inside this run, the measurement at c5592c1a on the intermediate candidate is superseded by the one at 99925723, census round 1 by round 2, and the earlier fault-injection runs by run 3
- **SUPERSEDED_FOR_HUMAN_VERDICT:** W18_CONSTRUCTION_BINDING_AND_FOCUSED_ANNOTATIONS — w18 replaces the two chips with "Hiện tất cả" and a compact default, makes the inspector the one explanation place, draws distance witnesses, adds the W18 refusal panels, and measures a new candidate; a reviewer judges the w18 images.
- **THESIS_USE:** AUTHORITATIVE_AUTOMATION_FOR_CANDIDATE_d63d6fd4 — not visual acceptance (human review NOT_APPROVED). Inside the registered scope, a served section is cut by the plane and solid the text names, a value stated only in a goal clause is never a datum, and every refusal names its cause; the numbers on the figure are bound by the backend. The census is a corpus result inside the registered scope, never a general soundness proof; constructions other than section cuts are not checked against the text. It was the latest product measurement until w18 (candidate d3b4cab9).
- **AUTHORITATIVE_FILES:** `RUN.json` · `MANIFEST.json` · `HANDOFF.md` · `REPORT.md` · `results/BROWSER_EVIDENCE.json` · `results/OCCLUSION_MEASUREMENT.json` · `results/PLAYBACK_EVIDENCE.json` · `results/HIDDEN_EDGE_CROPS.json` · `images/<family>/SHEET.png` · `images/<family>/FILMSTRIP.png` · `diagnostics/MEASUREMENT_ATTEMPTS.json` · `diagnostics/OPERATION_BINDING_REPRODUCTION_bce0b7bb.json` · `diagnostics/NEGATIVE_FIXTURE_RECONCILIATION_0b71502b.json` · `diagnostics/ASSUMPTION_CENSUS_W17_R2.json` · `diagnostics/ASSUMPTION_MECHANISM_DECISION_W17_R2.json` · `diagnostics/PROOF_CACHE_ROW_W17.json` · `diagnostics/logs/FAULT_INJECTION_W17_R3.log` · `diagnostics/logs/FAULT_INJECTION_W17_FRONTEND_R3.log` · `diagnostics/PONYTAIL_REVIEW_W17.json` · `diagnostics/WORKTREE_CLEANUP.json` · `diagnostics/TEMP_FILE_INVENTORY.json` · `inputs/CANDIDATE_DIVERGENCE_CORRECTION.json`
- **RUN_ID_POLICY:** SHORT_RUN_ID (`wNN-short-slug`, `docs/evaluation/RUN_NAMING.md`)

## WAVE_ID = W18_CONSTRUCTION_BINDING_AND_FOCUSED_ANNOTATIONS
- **DATE:** 2026-10-04
- **REPORT:** docs/evaluation/geometry/runs/w18-binding-focus/REPORT.md
- **ARTIFACT_DIRECTORY:** docs/evaluation/geometry/runs/w18-binding-focus/
- **START_BASE:** 0ec2bbbb
- **CODE_COMMIT:** 84ce7b70 (construction binding) · f2a040f9 (label roles, same_as, witness, S(T)) · b6868e19 (focused labels, one explanation place, witness layer; frontend/src) · 1e8c5658 (cache) · 7a06ee47 (ponytail; last product commit)
- **MEASUREMENT_COMMIT:** 0ca3accf7e921797e75aebcbc19e3a05b2557859
- **EVIDENCE_COMMIT_ROLE:** 4a9db1ff (browser, occlusion, playback, sheets, T3, gates, frontend fault injections run 2); kept apart: acceptance attempt 1 at 8caa8307 (`diagnostics/evidence-attempt1-8caa8307/`), superseded by the harness fix 1d8dfc6f
- **CLASSIFICATION:** READY_FOR_HUMAN_VISUAL_REVIEW
- **PRODUCT_CHANGE:** YES
- **MODEL_REQUEST_COUNT:** 0
- **CANDIDATE_CHANGE:** YES (tree_hash d63d6fd4… -> d3b4cab9…, 110 files; frozen once at 7a06ee47)
- **CACHE_CHANGE:** YES (CACHE_VERSION 109 -> 110 in 1e8c5658, real-row proof; lock 5cfb53a1; fingerprint b1714b56… unchanged)
- **CORRECTED_BY:** W20_REPOSITORY_CLEANUP_AND_PREMERGE_CORRECTNESS_CLOSURE — w20 checks a text-relation target defined by coordinates (directly or through an alias chain) and refuses it in every scope, closing this run's deferred limit `ISSUE-ARCH-CONSTRUCTION-BINDING-LITERAL-TARGET` (amendment §17); the w18 artifacts stay as they are
- **CORRECTS:** W17_OPERATION_BINDING_AND_ON_SCENE_ANNOTATIONS (point constructions — midpoints, projections — not checked against the text)
- **SUPERSEDES:** W17_OPERATION_BINDING_AND_ON_SCENE_ANNOTATIONS for the human verdict only; inside this run, acceptance attempt 1 (8caa8307) is superseded by attempt 2 (0ca3accf), the backend fault-injection runs 1–2 by run 3, and the frontend run 1 by run 2
- **THESIS_USE:** AUTHORITATIVE_AUTOMATION_FOR_CANDIDATE_d3b4cab9 — not visual acceptance (human review NOT_APPROVED). Inside the registered vocabulary (§16), a point the text defines as a midpoint or projection is built on the entities the text names, checked by identity; a mismatch is refused in every scope and named to the learner; numbers on the figure carry backend roles and one explanation place. The census is a corpus result, never a general proof; centres, intersections and unread phrasings are not checked.
- **AUTHORITATIVE_FILES:** `RUN.json` · `MANIFEST.json` · `HANDOFF.md` · `REPORT.md` · `results/BROWSER_EVIDENCE.json` · `results/OCCLUSION_MEASUREMENT.json` · `results/PLAYBACK_EVIDENCE.json` · `results/HIDDEN_EDGE_CROPS.json` · `images/<family>/SHEET.png` · `images/<family>/FILMSTRIP.png` · `diagnostics/MEASUREMENT_ATTEMPTS.json` · `diagnostics/CONSTRUCTION_BINDING_REPRODUCTION_bb9f7004.json` · `diagnostics/CONSTRUCTION_BINDING_REPRODUCTION_84ce7b70.json` · `diagnostics/CONSTRUCTION_BINDING_CENSUS_W18.json` · `diagnostics/CONSTRUCTION_BINDING_DECISION_W18.json` · `diagnostics/PROOF_CACHE_ROW_W18.json` · `diagnostics/logs/FAULT_INJECTION_W18_R3.log` · `diagnostics/logs/FAULT_INJECTION_W18_FRONTEND_R2.log` · `diagnostics/PONYTAIL_REVIEW_W18.json` · `diagnostics/WORKTREE_CLEANUP.json` · `diagnostics/TEMP_FILE_INVENTORY.json` · `inputs/CANDIDATE_DIVERGENCE_CORRECTION.json`
- **RUN_ID_POLICY:** SHORT_RUN_ID (`wNN-short-slug`, `docs/evaluation/RUN_NAMING.md`)

## WAVE_ID = W19_DOCS_REORGANIZATION_AND_RESEARCH_EVIDENCE_CURATION
- **DATE:** 2026-10-04
- **REPORT:** docs/evaluation/geometry/runs/w19-docs-organization/REPORT.md
- **ARTIFACT_DIRECTORY:** docs/evaluation/geometry/runs/w19-docs-organization/
- **START_BASE:** 6d0e6321
- **CODE_COMMIT:** NONE for the product. Docs tooling only: `backend/scripts/audit_docs_information_architecture.py` (`audit_docs_layout`, `PROJECT_DOCS`, `NAVIGATION_DOCS`, allowed next actions) and `backend/tests/geometry/test_docs_information_architecture.py` (four tests), one doc path in `backend/tests/geometry/test_curriculum_coverage.py`
- **MEASUREMENT_COMMIT:** NONE (no product measurement; verification of the final tree in a detached clean worktree, see `HANDOFF.md`)
- **EVIDENCE_COMMIT_ROLE:** a5c2e6f2 (structure + migration, inventory, migration map) · a44631a9 (claim map, hubs, closed docs root, catalog) · the documentation commit (state, report, handoff, verification)
- **CLASSIFICATION:** DOCS_REORGANIZED_AND_VERIFIED
- **PRODUCT_CHANGE:** NO
- **MODEL_REQUEST_COUNT:** 0
- **CANDIDATE_CHANGE:** NO (d3b4cab96c69a09f…, `--verify` exit 0)
- **CACHE_CHANGE:** NO (110, `lock_cache_identity.py --verify` exit 0)
- **CORRECTED_BY:** NONE
- **CORRECTS:** NONE (no report or artifact is corrected)
- **SUPERSEDES:** as claim authority only — `THESIS_READINESS.md`, `thesis/CLAIM_EVIDENCE_MATRIX.md`, `research/CLAIM_TO_EVIDENCE_MAP.md` (archived byte-identical in `docs/legacy/research/`) by `docs/research/CLAIM_EVIDENCE_MAP.md`
- **THESIS_USE:** NAVIGATION_AND_CLAIM_AUTHORITY — no new measurement; the claim map quotes existing evidence only and lists 0 rows at HUMAN_REVIEWED
- **AUTHORITATIVE_FILES:** `README.md` · `REPORT.md` · `HANDOFF.md` · `RUN.json` · `MANIFEST.json` · `inventory/INVENTORY.json` · `inventory/MIGRATION_MAP.json` · `verification/FROZEN_IDENTITY.json` · `verification/LINKS_FINAL.json` · `verification/OLD_PATH_CONSUMERS_FINAL.json` · `verification/logs/`
- **RUN_ID_POLICY:** SHORT_RUN_ID (`wNN-short-slug`, `docs/evaluation/RUN_NAMING.md`)

## WAVE_ID = W20_REPOSITORY_CLEANUP_AND_PREMERGE_CORRECTNESS_CLOSURE
- **DATE:** 2026-10-04 → 2026-10-05
- **REPORT:** docs/evaluation/geometry/runs/w20-cleanup-premerge/REPORT.md
- **ARTIFACT_DIRECTORY:** docs/evaluation/geometry/runs/w20-cleanup-premerge/
- **START_BASE:** 2cb4ed8c
- **CODE_COMMIT:** 65c90bde (construction binding §17) · bedb1040 (CACHE_VERSION 110 -> 111) · a4f771b3 (comments only) · 4e647861 + 654beda3 (`run_reconciliation(out_dir)` and its tests)
- **MEASUREMENT_COMMIT:** 5fbb397b7d485de183526451ae9003631c395d94 (authoritative verification in a clean detached worktree); probe, census and cache proof at 65c90bde
- **EVIDENCE_COMMIT_ROLE:** f0edcd11 (labels + before probe, before any fix) · 8b6a1a3a (after probe, census, fault injections r1–r2) · 31716373 (cleanup inventory + deletion log) · the documentation commit (T3, gates, final probe, fault injections r3, report, handoff, manifest)
- **CLASSIFICATION:** READY_FOR_HUMAN_VISUAL_REVIEW
- **PRODUCT_CHANGE:** YES
- **MODEL_REQUEST_COUNT:** 0
- **CANDIDATE_CHANGE:** YES (tree_hash d3b4cab9… -> 2a15102b… (intermediate, bedb1040) -> 27c31de6…, 110 files; frozen twice, declared in `inputs/CANDIDATE_DIVERGENCE_CORRECTION.json`)
- **CACHE_CHANGE:** YES (CACHE_VERSION 110 -> 111 in bedb1040, real-row proof; lock ac241a8d; fingerprint b1714b56… unchanged)
- **CORRECTED_BY:** COMPLETE_DOCS_CLEANUP_AND_CUBOID_BRANCH_ACCEPTANCE (scope note only: W20 was a correctness closure plus a bounded cleanup; the full docs review is the run cuboid-final-review; W20 measurements and conclusions unchanged)
- **CORRECTS:** W18_CONSTRUCTION_BINDING_AND_FOCUSED_ANNOTATIONS (deferred limit: a text-relation target defined by coordinates was neither checked nor recorded by `construction_binding`)
- **SUPERSEDES:** inside this run only — fault-injection logs r1 and r2 by r3 (clean worktree), probe `before` (23 rows) by `before-r2` (27 rows, labels amended before any fix)
- **THESIS_USE:** AUTHORITATIVE_AUTOMATION_FOR_CANDIDATE_27c31de6 — not visual acceptance (human review NOT_APPROVED). Inside the §16.1 vocabulary, a text-relation target the program defines by coordinates is refused in every scope (claim C6 of `docs/research/CLAIM_EVIDENCE_MAP.md`)
- **AUTHORITATIVE_FILES:** `RUN.json` · `MANIFEST.json` · `HANDOFF.md` · `REPORT.md` · `diagnostics/literal_target_corpus/LABELS.json` · `results/LITERAL_TARGET_PROBE_before-r2_2cb4ed8c.json` · `results/LITERAL_TARGET_PROBE_after_65c90bde.json` · `results/LITERAL_TARGET_PROBE_final_5fbb397b.json` · `diagnostics/CONSTRUCTION_BINDING_DECISION_W20.json` · `diagnostics/PROOF_CACHE_ROW_W20.json` · `inventory/CLEANUP_INVENTORY.json` · `inventory/DELETION_LOG.json` · `results/logs/T3_FULL_GATE_5fbb397b.log` · `results/logs/GATES_5fbb397b.log` · `results/logs/FAULT_INJECTION_W20_r3.log`
- **RUN_ID_POLICY:** SHORT_RUN_ID (`wNN-short-slug`, `docs/evaluation/RUN_NAMING.md`)

## WAVE_ID = COMPLETE_DOCS_CLEANUP_AND_CUBOID_BRANCH_ACCEPTANCE
- **RUN_ID:** cuboid-final-review (closing run of the work cuboid-visual-semantic-closure; no wave number)
- **DATE:** 2026-10-05
- **REPORT:** docs/evaluation/geometry/runs/cuboid-final-review/REPORT.md
- **ARTIFACT_DIRECTORY:** docs/evaluation/geometry/runs/cuboid-final-review/
- **START_BASE:** 4048ff83
- **CODE_COMMIT:** 284a9bfa (refusal card of §17: message from `reason_subjects`, label from `reason_code`) · fac2769e (tooling: focused browser check)
- **MEASUREMENT_COMMIT:** a1c53cdbf9cd35667f0e1d918584e880a67daab3 (authoritative verification in a clean detached worktree); cache proof at 284a9bfa against 4048ff83; inventories at 4048ff83 (before) and a1c53cdb (after)
- **EVIDENCE_COMMIT_ROLE:** 42dd1af5 (docs inventory, verbatim history split, cleanup log) · 284a9bfa (red and green logs) · 6ec40806 (cache proof) · a1c53cdb (refreeze, pre-freeze log) · the documentation commit (T3, gates, browser check and images, inventories, report, handoff) · the final docs-gate log commit
- **CLASSIFICATION:** READY_FOR_HUMAN_VISUAL_REVIEW
- **PRODUCT_CHANGE:** YES (learner-facing only)
- **MODEL_REQUEST_COUNT:** 0
- **CANDIDATE_CHANGE:** YES (tree_hash 27c31de6… -> b2d4187a…, 110 files; frozen once at 284a9bfa, declared in `inputs/CANDIDATE_DIVERGENCE_CORRECTION.json`)
- **CACHE_CHANGE:** NO (111; `diagnostics/cache_proof/CACHE_DECISION_CFR.json`: served envelopes byte-identical, refusals never cached; lock `--verify` exit 0)
- **CORRECTED_BY:** CUBOID_INVARIANT_RECONCILIATION_AND_MERGE_HANDOFF (count only: the rows of ARCHITECTURE_MAP §5 with dead pointers were 24, not 22 — #9 and #12 inherit through "như trên"; this run's artifacts unchanged)
- **CORRECTS:** W20_REPOSITORY_CLEANUP_AND_PREMERGE_CORRECTNESS_CLOSURE (scope note only: W20's cleanup was bounded; the full docs review is this run)
- **SUPERSEDES:** inside this run only — browser check attempt 1 (stopped by the dist freshness guard) by attempt 2; the docs inventory committed in 42dd1af5 by the inventories measured at 4048ff83 and a1c53cdb
- **THESIS_USE:** AUTHORITATIVE_AUTOMATION_FOR_CANDIDATE_b2d4187a — not visual acceptance (human review NOT_APPROVED). The §17 refusal states the verification limit in learner terms; the docs keep one current authority per topic, with the informatics-era history kept verbatim in `docs/legacy/`
- **AUTHORITATIVE_FILES:** `RUN.json` · `MANIFEST.json` · `HANDOFF.md` · `REPORT.md` · `inventory/DOCS_INVENTORY.json` · `inventory/DOCS_INVENTORY_BEFORE_4048ff83.json` · `inventory/HISTORY_SPLIT.json` · `inventory/CLEANUP_LOG.json` · `diagnostics/cache_proof/CACHE_DECISION_CFR.json` · `results/BROWSER_REFUSAL_CFR.json` · `results/logs/T3_FULL_GATE_a1c53cdb.log` · `results/logs/GATES_a1c53cdb.log` · `images/`
- **RUN_ID_POLICY:** CLOSING_RUN_OF_A_WORK (short id set by the brief, an abbreviation of the task slug; `docs/evaluation/RUN_NAMING.md` — waves of new works use `<task-slug>-wNN`)

## WAVE_ID = CUBOID_INVARIANT_RECONCILIATION_AND_MERGE_HANDOFF
- **RUN_ID:** cuboid-acceptance (acceptance package of the work cuboid-visual-semantic-closure; no wave number)
- **DATE:** 2026-10-05
- **REPORT:** docs/evaluation/geometry/runs/cuboid-acceptance/REPORT.md
- **ARTIFACT_DIRECTORY:** docs/evaluation/geometry/runs/cuboid-acceptance/
- **START_BASE:** 903e874c
- **CODE_COMMIT:** NONE (documentation only; product bytes equal to candidate b2d4187a, product commit 284a9bfa)
- **MEASUREMENT_COMMIT:** the documentation commit of this run (invariant checks and docs gates in a clean detached worktree); product evidence reused, not re-measured: a1c53cdb (cuboid-final-review) and 0ca3accf (w18)
- **EVIDENCE_COMMIT_ROLE:** documentation commit (reconciliation, check script, living docs) · final log commit (`results/logs/INVARIANT_CHECKS_FINAL.log`, `results/logs/DOCS_GATES_FINAL.log`)
- **CLASSIFICATION:** READY_FOR_HUMAN_VISUAL_REVIEW
- **PRODUCT_CHANGE:** NO
- **MODEL_REQUEST_COUNT:** 0
- **CANDIDATE_CHANGE:** NO (b2d4187a…, `--verify` in the clean worktree)
- **CACHE_CHANGE:** NO (111; no product byte changed)
- **CORRECTED_BY:** NONE
- **CORRECTS:** COMPLETE_DOCS_CLEANUP_AND_CUBOID_BRANCH_ACCEPTANCE (count only: 24 invariant rows with dead pointers, not 22)
- **SUPERSEDES:** NONE
- **THESIS_USE:** AUTHORITATIVE_RECONCILIATION_OF_ARCHITECTURE_MAP_§5 — 24 rows: 9 CURRENT_ENFORCED, 1 CURRENT_UNVERIFIED (#14, ISSUE-OPS-LIVE-OPT-IN-NOT-UNIFORM), 14 HISTORICAL_NOT_APPLICABLE, 0 VIOLATED; not visual acceptance (human review NOT_APPROVED)
- **AUTHORITATIVE_FILES:** `RUN.json` · `HANDOFF.md` · `REPORT.md` · `results/INVARIANT_RECONCILIATION.json` · `diagnostics/invariant_checks_cacc.sh` · `diagnostics/cacc_gates.sh` · `results/logs/INVARIANT_CHECKS_FINAL.log` · `results/logs/DOCS_GATES_FINAL.log`
- **RUN_ID_POLICY:** CLOSING_RUN_OF_A_WORK (short id set by the brief; `docs/evaluation/RUN_NAMING.md`)

## WAVE_ID = CUBOID_ACCEPTANCE_AND_DIRECT_MAIN_INTEGRATION
- **RUN_ID:** cuboid-merge (review package and integration of the work cuboid-visual-semantic-closure; no wave number)
- **DATE:** 2026-10-05
- **REPORT:** docs/evaluation/geometry/runs/cuboid-merge/REVIEW.md
- **ARTIFACT_DIRECTORY:** docs/evaluation/geometry/runs/cuboid-merge/
- **START_BASE:** 37b23f04
- **CODE_COMMIT:** NONE (documentation only; product commit 284a9bfa, candidate b2d4187a unchanged)
- **MEASUREMENT_COMMIT:** fixture transfer at 0ca3accf (w18 measurement) and 37b23f04, clean detached worktrees, offline generator; gates at the documentation commit of this run
- **EVIDENCE_COMMIT_ROLE:** documentation commit (REVIEW, HANDOFF, RUN.json, FIXTURE_TRANSFER.json, TRANSFER.log, scripts, living docs) · final log commit (`results/logs/GATES_FINAL.log`)
- **CLASSIFICATION:** MERGED_AND_PUSHED (user approval A–F in `APPROVAL.md`; main fast-forwarded to c282a5f3 and pushed; integrated-tree gates `results/logs/INTEGRATED_MAIN_GATES.log`)
- **PRODUCT_CHANGE:** NO
- **MODEL_REQUEST_COUNT:** 0
- **CANDIDATE_CHANGE:** NO
- **CACHE_CHANGE:** NO
- **CORRECTED_BY:** NONE
- **CORRECTS:** NONE (extends the w18 visual evidence to candidate b2d4187a; w18 artifacts unchanged)
- **SUPERSEDES:** NONE
- **THESIS_USE:** TRANSFER_OF_W18_VISUAL_EVIDENCE_TO_CANDIDATE_b2d4187a — the regenerated w18 fixtures are byte-exact (manifest 10dbe2de…), the 32 current fixtures differ only in product_commit_sha/product_tree_sha, frontend changes are confined to the refusal card; not visual acceptance (human review NOT_APPROVED)
- **AUTHORITATIVE_FILES:** `REVIEW.md` · `HANDOFF.md` · `RUN.json` · `results/FIXTURE_TRANSFER.json` · `results/logs/TRANSFER.log` · `diagnostics/fixture_transfer_cmerge.py` · `diagnostics/cmerge_gates.sh` · `results/logs/GATES_FINAL.log`
- **RUN_ID_POLICY:** CLOSING_RUN_OF_A_WORK (short id set by the brief; `docs/evaluation/RUN_NAMING.md`)

## WAVE_ID = REGULAR_SQUARE_PYRAMID_AND_PEDAGOGICAL_UI
- **RUN_ID:** regular-square-pyramid-w01 (task regular-square-pyramid, wave W1; `docs/evaluation/RUN_NAMING.md`)
- **DATE:** 2026-10-05
- **REPORT:** docs/evaluation/geometry/runs/regular-square-pyramid-w01/REPORT.md
- **ARTIFACT_DIRECTORY:** docs/evaluation/geometry/runs/regular-square-pyramid-w01/
- **START_BASE:** 38d41588
- **CODE_COMMIT:** 3bdada32 · ae9c72a5 · b2d224f6 · 98e2b8f7 · 9d66c603 · de5b2331 · ad7172ab (final self-review fix)
- **MEASUREMENT_COMMIT:** ed37f9fa (clean detached worktree with a space in its path; browser suite attempt 3, occlusion, playback, builder); transferred to candidate 5234c37e at b5cf4503 (37/37 envelopes byte-identical, frontend/src unchanged); T3 and identity gates at the final documentation commit
- **EVIDENCE_COMMIT_ROLE:** 025bbff4 (evidence) · state commit (`diagnostics/logs/T3_FULL_GATE_*.log`, `GATES_*.log`, `MEASUREMENT_ATTEMPTS.json`, `MANIFEST.json`)
- **CLASSIFICATION:** READY_FOR_HUMAN_VISUAL_REVIEW
- **PRODUCT_CHANGE:** YES
- **MODEL_REQUEST_COUNT:** 0
- **CANDIDATE_CHANGE:** YES (b2d4187a… → 4629c3e8… at de5b2331, intermediate → 5234c37e… at ad7172ab; two freezes)
- **CACHE_CHANGE:** YES (CACHE_VERSION 111 -> 112 in de5b2331, real-row proof `diagnostics/PROOF_CACHE_ROW_W01.json`; semantic environment b1714b56… unchanged)
- **CORRECTED_BY:** NONE
- **CORRECTS:** NONE (the w18/cuboid evidence describes b2d4187a and earlier candidates and stays as it is)
- **SUPERSEDES:** NONE
- **THESIS_USE:** REGULAR_SQUARE_PYRAMID_CERTIFICATE_AND_ROADMAP_0_1_UI — claim C7 and the W1 notes of B2/D5 in `docs/research/CLAIM_EVIDENCE_MAP.md`; offline only; human review NOT_APPROVED
- **AUTHORITATIVE_FILES:** `REPORT.md` · `HANDOFF.md` · `RUN.json` · `diagnostics/corpus/LABELS.json` · `diagnostics/PREREGISTRATION_CORRECTIONS.json` · `diagnostics/corpus/LABELS_R2.json` · `diagnostics/PROOF_CACHE_ROW_W01.json` · `diagnostics/PROOF_CACHE_ROW_W01_R2.json` · `diagnostics/SCOPE_LENGTH_CLUE_PROBE_1310658b.json` · `results/FIXTURE_TRANSFER_b5cf4503_r2.json` · `results/BROWSER_EVIDENCE.json` · `results/OCCLUSION_MEASUREMENT.json` · `results/PLAYBACK_EVIDENCE.json` · `images/` · `inputs/CANDIDATE_DIVERGENCE_CORRECTION.json`
- **RUN_ID_POLICY:** TASK_WAVE (`<task-slug>-wNN`)

## WAVE_ID = REGULAR_SQUARE_PYRAMID_PEDAGOGICAL_CLOSURE
- **RUN_ID:** regular-square-pyramid-w02 (task regular-square-pyramid, wave W2; `docs/evaluation/RUN_NAMING.md`)
- **DATE:** 2026-10-05
- **REPORT:** docs/evaluation/geometry/runs/regular-square-pyramid-w02/REPORT.md
- **ARTIFACT_DIRECTORY:** docs/evaluation/geometry/runs/regular-square-pyramid-w02/
- **START_BASE:** e821b9b5 (W1 head)
- **CODE_COMMIT:** 2a63da7d · 9f454d6b · 71cf0e80 · 6ca3b35e · c86cf53c · e68fa199 (CACHE_VERSION 113) · 7a88a789 · c5142f07 · 527d642e · 75a0af9a · 70665542 (CRLF-safe test; divergence declaration at 113)
- **MEASUREMENT_COMMIT:** 94200b50403bdf823eb49697d54c0cb53e8e4ccb (cloud, clean detached CRLF worktree with a space in its path; browser suite, W2 probe, occlusion, playback, builder); earlier attempts at c453fae3, 527d642e, bac5d80f, 4a6af4e9 kept (`diagnostics/MEASUREMENT_ATTEMPTS.json`)
- **EVIDENCE_COMMIT_ROLE:** evidence commit after the measurement (results, images, inputs, logs)
- **CLASSIFICATION:** CLOUD_IMPLEMENTATION_COMPLETE_LOCAL_VERIFICATION_REQUIRED
- **PRODUCT_CHANGE:** YES
- **MODEL_REQUEST_COUNT:** 0
- **CANDIDATE_CHANGE:** YES (5234c37e… → d3de9c44…; four freezes, same tree hash, product commit 70665542; evidence of 94200b50 transferred, `results/EVIDENCE_TRANSFER_70665542.json`)
- **CACHE_CHANGE:** YES (CACHE_VERSION 112 -> 113 in e68fa199, row proof `diagnostics/PROOF_CACHE_ROW_W02.json`; semantic environment b1714b56… unchanged)
- **CORRECTED_BY:** regular-square-pyramid-w03 — PC1-W2 restored to the W18 expectation (`annotation_id: d_kq`); the hidden-helper exemption of `no_static_frames`, the structured-reference check and `every_geometry_step_changes_the_figure` removed (the W12 invariant holds without it); `camera_settled_rotated_neutral` and cross-section `causal_restore` reclassified as environment (green locally at fe68b4ca). W2 artifacts unchanged
- **CORRECTS:** NONE (W1 artifacts unchanged; the W1 equal-value height rule is replaced in code, not in W1 evidence)
- **SUPERSEDES:** NONE
- **THESIS_USE:** REGULAR_SQUARE_PYRAMID_PEDAGOGICAL_CLOSURE — claims C8 and D6 in `docs/research/CLAIM_EVIDENCE_MAP.md`; cloud measurement, local acceptance and human review pending
- **AUTHORITATIVE_FILES:** `REPORT.md` · `HANDOFF.md` · `RUN.json` · `diagnostics/PROOF_CACHE_ROW_W02.json` · `diagnostics/PREREGISTRATION_CORRECTIONS.json` · `diagnostics/ENV_CAMERA_SETTLE_BASELINE.json` · `diagnostics/MEASUREMENT_ATTEMPTS.json` · `results/BROWSER_EVIDENCE.json` · `results/W02_CLOSURE_PROBE.json` · `results/OCCLUSION_MEASUREMENT.json` · `results/PLAYBACK_EVIDENCE.json` · `results/EVIDENCE_TRANSFER_70665542.json` · `images/` · `inputs/CANDIDATE_DIVERGENCE_CORRECTION.json`
- **RUN_ID_POLICY:** TASK_WAVE (`<task-slug>-wNN`)

## WAVE_ID = REGULAR_SQUARE_PYRAMID_LOCAL_ACCEPTANCE
- **RUN_ID:** regular-square-pyramid-w03 (task regular-square-pyramid, wave W3; `docs/evaluation/RUN_NAMING.md`)
- **DATE:** 2026-10-06
- **REPORT:** docs/evaluation/geometry/runs/regular-square-pyramid-w03/REPORT.md
- **ARTIFACT_DIRECTORY:** docs/evaluation/geometry/runs/regular-square-pyramid-w03/
- **START_BASE:** fe68b4ca (cloud W2 head, fast-forwarded)
- **CODE_COMMIT:** 824924d7 (H-W2-4) · 45beaed3 (H-W2-2; CACHE_VERSION 114) · a5d233ce (scenario tree-hash pin)
- **MEASUREMENT_COMMIT:** a5d233ce4e635b0228f04af55aa04f3407d4a8d8 (local, clean detached CRLF worktree with a space in its path; browser suite, W2 probe, occlusion, playback, builder); baseline at fe68b4ca (`diagnostics/baseline_fe68b4ca/`) and attempt 1 at 47941832 (`diagnostics/attempts/`) kept (`MEASUREMENT_ATTEMPTS.json`)
- **EVIDENCE_COMMIT_ROLE:** evidence commit 0d0d1de3 after the measurement (results, images, inputs, logs)
- **CLASSIFICATION:** READY_FOR_HUMAN_VISUAL_REVIEW (T3 FULL_PRODUCT_GATE_PASS + identity gates at 4c0f9219)
- **PRODUCT_CHANGE:** YES
- **MODEL_REQUEST_COUNT:** 0
- **CANDIDATE_CHANGE:** YES (d3de9c44… → 5dec4572…; one freeze at 45beaed3)
- **CACHE_CHANGE:** YES (CACHE_VERSION 113 -> 114 in 45beaed3, row proof `diagnostics/PROOF_CACHE_ROW_W03.json`; semantic environment b1714b56… unchanged)
- **CORRECTED_BY:** NONE
- **CORRECTS:** regular-square-pyramid-w02 (PC1-W2; the hidden-helper gate exemption; the cloud classification of two browser gates) — by a new layer, W2 files untouched
- **SUPERSEDES:** NONE
- **THESIS_USE:** REGULAR_SQUARE_PYRAMID_LOCAL_ACCEPTANCE — local measurement of the W1/W2 claims; human review NOT_APPROVED
- **AUTHORITATIVE_FILES:** `REVIEW.md` · `REPORT.md` · `HANDOFF.md` · `RUN.json` · `MEASUREMENT_ATTEMPTS.json` · `diagnostics/PROOF_CACHE_ROW_W03.json` · `diagnostics/baseline_fe68b4ca/` · `results/BROWSER_EVIDENCE.json` · `results/W02_CLOSURE_PROBE.json` · `results/OCCLUSION_MEASUREMENT.json` · `results/PLAYBACK_EVIDENCE.json` · `images/` · `inputs/CANDIDATE_DIVERGENCE_CORRECTION.json`
- **RUN_ID_POLICY:** TASK_WAVE (`<task-slug>-wNN`)

## WAVE_ID = SHARED_SIMULATION_UI_CLOSURE
- **RUN_ID:** regular-square-pyramid-w04 (task regular-square-pyramid, wave W4; `docs/evaluation/RUN_NAMING.md`)
- **DATE:** 2026-10-06
- **REPORT:** docs/evaluation/geometry/runs/regular-square-pyramid-w04/REPORT.md
- **ARTIFACT_DIRECTORY:** docs/evaluation/geometry/runs/regular-square-pyramid-w04/
- **START_BASE:** f3db0f6f (W3 head)
- **CODE_COMMIT:** ce44eb38 · 98b1ce8d · 270cae4e · a1c17714 · e41b0ab1 · aa754cb9 (CACHE_VERSION 115) · c8c49f3c · ecbe55c0 · 53e4bec5
- **MEASUREMENT_COMMIT:** 103494c4 (local, clean detached CRLF worktree with a space in its path; browser suite, W2 probe, W4 panels probe, SM control, occlusion, playback, builder); attempts 1–3 at d7154ab8 and 643b7d7a kept (`diagnostics/attempts/`, `MEASUREMENT_ATTEMPTS.json`)
- **EVIDENCE_COMMIT_ROLE:** evidence commit b4f924c1 after the measurement (results, images, inputs, logs)
- **CLASSIFICATION:** READY_FOR_HUMAN_VISUAL_REVIEW (T3 FULL_PRODUCT_GATE_PASS + identity gates at d6e41d80)
- **PRODUCT_CHANGE:** YES
- **MODEL_REQUEST_COUNT:** 0
- **CANDIDATE_CHANGE:** YES (5dec4572… → 8a27a58b…; three freezes, same tree hash, product commit 53e4bec5)
- **CACHE_CHANGE:** YES (CACHE_VERSION 114 -> 115 in aa754cb9, row proof `diagnostics/PROOF_CACHE_ROW_W04.json`; semantic environment b1714b56… unchanged)
- **CORRECTED_BY:** NONE
- **CORRECTS:** NONE (W1–W3 files untouched)
- **SUPERSEDES:** NONE
- **THESIS_USE:** SHARED_SIMULATION_UI_CLOSURE — presentation layer of the simulation (panels, layout, selection); human review NOT_APPROVED
- **AUTHORITATIVE_FILES:** `REVIEW.md` · `REPORT.md` · `HANDOFF.md` · `RUN.json` · `MEASUREMENT_ATTEMPTS.json` · `PLAN.md` · `diagnostics/PANEL_INVENTORY.md` · `diagnostics/PROOF_CACHE_ROW_W04.json` · `diagnostics/scene_hash/SCENE_DIFF.json` · `diagnostics/sm_overlap/` · `results/BROWSER_EVIDENCE.json` · `results/W02_CLOSURE_PROBE.json` · `results/W04_PANELS_PROBE.json` · `results/SM_OVERLAP_AFTER_103494c4.json` · `results/OCCLUSION_MEASUREMENT.json` · `results/PLAYBACK_EVIDENCE.json` · `images/` · `inputs/CANDIDATE_DIVERGENCE_CORRECTION.json`
- **RUN_ID_POLICY:** TASK_WAVE (`<task-slug>-wNN`)

## WAVE_ID = IMMERSIVE_SIMULATION_AND_ARCHITECTURE_SLICE
- **RUN_ID:** regular-square-pyramid-w05 (task regular-square-pyramid, wave W5; `docs/evaluation/RUN_NAMING.md`)
- **DATE:** 2026-10-06/07
- **REPORT:** docs/evaluation/geometry/runs/regular-square-pyramid-w05/REPORT.md
- **ARTIFACT_DIRECTORY:** docs/evaluation/geometry/runs/regular-square-pyramid-w05/
- **START_BASE:** 73bc404e (W4 head)
- **CODE_COMMIT:** c15e6fab · 470adc3a · 82225a7b (harness c1070389 · f01df0e5)
- **MEASUREMENT_COMMIT:** f01df0e5 (local, clean detached CRLF worktree with a space in its path; browser suite, W2 probe, W4 panels probe, W05 focus probe, occlusion, playback, builder); attempts 1–3 at a588f8db, c1070389, 74c91060 kept (`diagnostics/attempts/`, `MEASUREMENT_ATTEMPTS.json`)
- **EVIDENCE_COMMIT_ROLE:** evidence commit 3b31aa18 after the measurement (results, images, inputs, logs)
- **CLASSIFICATION:** READY_FOR_HUMAN_VISUAL_REVIEW (T3 FULL_PRODUCT_GATE_PASS + identity gates at 4123fb4f)
- **PRODUCT_CHANGE:** YES
- **MODEL_REQUEST_COUNT:** 0
- **CANDIDATE_CHANGE:** YES (8a27a58b… → 5e1c0639…; two freezes, same tree hash, product commit 82225a7b)
- **CACHE_CHANGE:** NO (CACHE_VERSION 115; `diagnostics/cache_proof/CACHE_DECISION_W05.json`)
- **CORRECTED_BY:** regular-triangular-pyramid-w01 `corrections/W05_RECORD_CORRECTION.json` (attempt-4 record missing from `MEASUREMENT_ATTEMPTS.json`; REPORT §4 node harness 93/93 → 91 pass, 2 skipped, 0 fail; W5 files untouched)
- **CORRECTS:** regular-square-pyramid-w01 `LABELS_R2.json` row R2_L1 (by a new layer; W1 files untouched)
- **SUPERSEDES:** NONE
- **THESIS_USE:** focused simulation workspace (presentation) + chained-equality source reader; human review NOT_APPROVED
- **AUTHORITATIVE_FILES:** `REVIEW.md` · `REPORT.md` · `HANDOFF.md` · `RUN.json` · `MEASUREMENT_ATTEMPTS.json` · `PLAN.md` · `diagnostics/TOOL_INVENTORY.md` · `diagnostics/SKILL_NOTES.md` · `diagnostics/corpus/LABELS_W05.json` · `diagnostics/cache_proof/` · `results/BROWSER_EVIDENCE.json` · `results/W05_FOCUS_PROBE.json` · `results/W04_PANELS_PROBE.json` · `results/W02_CLOSURE_PROBE.json` · `results/OCCLUSION_MEASUREMENT.json` · `results/PLAYBACK_EVIDENCE.json` · `images/` · `inputs/CANDIDATE_DIVERGENCE_CORRECTION.json`
- **RUN_ID_POLICY:** TASK_WAVE (`<task-slug>-wNN`)

## WAVE_ID = REGULAR_TRIANGULAR_PYRAMID_AND_TETRAHEDRON_SLICE
- **RUN_ID:** regular-triangular-pyramid-w01 (task regular-triangular-pyramid, wave W1; `docs/evaluation/RUN_NAMING.md`; kept on `feat/regular-square-pyramid` by user instruction — `RUN.json`)
- **DATE:** 2026-10-07
- **REPORT:** docs/evaluation/geometry/runs/regular-triangular-pyramid-w01/REPORT.md
- **ARTIFACT_DIRECTORY:** docs/evaluation/geometry/runs/regular-triangular-pyramid-w01/
- **START_BASE:** e9435d67 (W5 head)
- **CODE_COMMIT:** 983cfc16 · 82beaf62 · df614b30 · 3487c0a7 · e7b92e49 · 1e90ca0e (harness 4e285690; cleanup 0d4c4f8b; labels/oracle/amendment §18 before the change dc0a804b)
- **MEASUREMENT_COMMIT:** 1bb11018 (attempt 3; local, clean detached CRLF worktree with a space in its path; suite, W02, W04, W05, occlusion, playback, builder, prune; W02 and W04 cross_section rerun alone at the same commit); attempts 1 (aa583ad9) and 2 (1bb11018) kept (`MEASUREMENT_ATTEMPTS.json`, `diagnostics/attempts/`)
- **EVIDENCE_COMMIT_ROLE:** evidence commit c08a1eed after the measurement (results, images, inputs, logs)
- **CLASSIFICATION:** READY_FOR_HUMAN_VISUAL_REVIEW (T3 FULL_PRODUCT_GATE_PASS + identity gates at aa845902; first T3 at d2e8a778 failed on a stale fixture-count lock, fixed)
- **PRODUCT_CHANGE:** YES
- **MODEL_REQUEST_COUNT:** 0
- **CANDIDATE_CHANGE:** YES (5e1c0639… → 92c9e198…; two freezes, same tree hash, product commit 1e90ca0e)
- **CACHE_CHANGE:** YES (CACHE_VERSION 115 -> 116 in 82beaf62; `diagnostics/cache_proof/CACHE_DECISION.json`; semantic environment b1714b56… unchanged)
- **CORRECTED_BY:** NONE
- **CORRECTS:** regular-square-pyramid-w05 record (`corrections/W05_RECORD_CORRECTION.json`; W5 files untouched)
- **SUPERSEDES:** NONE
- **THESIS_USE:** regular triangular pyramid / regular tetrahedron in a declared exact (ℚ³) domain with honest refusal outside it; selective image retention; human review NOT_APPROVED
- **AUTHORITATIVE_FILES:** `REVIEW.md` · `REPORT.md` · `HANDOFF.md` · `RUN.json` · `MEASUREMENT_ATTEMPTS.json` · `PLAN.md` · `diagnostics/corpus/LABELS.json` · `diagnostics/oracle_rtp_w01.py` · `diagnostics/fault_injection_rtp_w01.py` · `diagnostics/cache_proof/CACHE_DECISION.json` · `inputs/REVIEW_SET.json` · `inputs/CANDIDATE_DIVERGENCE_CORRECTION.json` · `results/IMAGE_POLICY.json`
- **RUN_ID_POLICY:** TASK_WAVE (`<task-slug>-wNN`)

## WAVE_ID = EXACT_DIMENSIONS_AND_CAPTURE_POLICY
- **RUN_ID:** exact-dimensions (task exact-dimensions; `docs/evaluation/RUN_NAMING.md` naming policy 2026-10-07; same branch)
- **DATE:** 2026-10-07/08
- **REPORT:** docs/evaluation/geometry/runs/exact-dimensions/report.md
- **ARTIFACT_DIRECTORY:** docs/evaluation/geometry/runs/exact-dimensions/
- **START_BASE:** 4ceadd55
- **CODE_COMMIT:** 1c8f3cb4 · de6d3e35 · 14892061 · 0ed6332f · 6c89abcd · ed3ae208 (harness d4834d92, 2d62f69c; plan/labels/oracle before the change 1c91f90d)
- **MEASUREMENT_COMMIT:** 3bbb8052 (fixtures, build, scene controls, panels, focus) · fe83c46e (suite, occlusion) · d51db4e2 (playback, builder); local clean detached CRLF worktree with a space in its path; only failed steps rerun
- **EVIDENCE_COMMIT_ROLE:** evidence commit c5cae8af (results, images, fixtures, logs)
- **CLASSIFICATION:** READY_FOR_HUMAN_VISUAL_REVIEW (T3 FULL_PRODUCT_GATE_PASS + identity gates at 4ef0a02e)
- **PRODUCT_CHANGE:** YES
- **MODEL_REQUEST_COUNT:** 0
- **CANDIDATE_CHANGE:** YES (92c9e198… → e1927f84…; product commit ed3ae208)
- **CACHE_CHANGE:** YES (CACHE_VERSION 116 -> 117 in ed3ae208; `cache/decision.json`; semantic environment b1714b56… unchanged)
- **CORRECTED_BY:** NONE
- **CORRECTS:** regular-triangular-pyramid-w01 `diagnostics/corpus/LABELS.json` rows N5, N5b, U1–U4 and regular-square-pyramid-w01 row U3_regular_triangular (by `label_corrections.json`; earlier files untouched); candidate register by `inputs/candidate_divergence.json`
- **SUPERSEDES:** NONE
- **THESIS_USE:** rational sizes via an affine chart + Gram metric derived from the text; source-side capture policy; human review NOT_APPROVED
- **AUTHORITATIVE_FILES:** `review.md` · `report.md` · `handoff.md` · `run.json` · `plan.md` · `labels.json` · `label_corrections.json` · `oracle.py` · `capture_counts.json` · `cache/` · `inputs/REVIEW_SET.json` · `inputs/candidate_divergence.json` · `results/BROWSER_EVIDENCE.json` · `results/PLAYBACK_EVIDENCE.json` · `results/OCCLUSION_MEASUREMENT.json` · `results/W02_CLOSURE_PROBE.json` · `results/W04_PANELS_PROBE.json` · `results/W05_FOCUS_PROBE.json` · `images/` · `diagnostics/attempt1–3/`
- **RUN_ID_POLICY:** TASK_NAME (naming policy 2026-10-07)

## WAVE_ID = REPO_CLEANUP
- **RUN_ID:** repo-cleanup (task repo-cleanup; same branch)
- **DATE:** 2026-10-08
- **REPORT:** docs/evaluation/geometry/runs/repo-cleanup/report.md
- **ARTIFACT_DIRECTORY:** docs/evaluation/geometry/runs/repo-cleanup/
- **START_BASE:** 2c2dfbbf
- **CODE_COMMIT:** 88769dc5 · 8ff42b58 · 67e11671 · 11bea4a7 · be4b8287
- **MEASUREMENT_COMMIT:** NONE (no browser or live measurement; candidate refreeze 372f78c2)
- **EVIDENCE_COMMIT_ROLE:** inventory and relocated snapshot in the run directory
- **CLASSIFICATION:** CLEANUP_COMPLETE (T3 FULL_PRODUCT_GATE_PASS at 645705ae; identity gates green at 2da4cdeb)
- **PRODUCT_CHANGE:** YES (dead code, unused /api/explain)
- **MODEL_REQUEST_COUNT:** 0
- **CANDIDATE_CHANGE:** YES (e1927f84… → b4a33205…; product commit be4b8287)
- **CACHE_CHANGE:** NO (CACHE_VERSION 117; cache identity lock unchanged)
- **CORRECTED_BY:** NONE
- **CORRECTS:** exact-dimensions `inputs/candidate_divergence.json` (current candidate) by `runs/repo-cleanup/inputs/candidate_divergence.json`
- **SUPERSEDES:** NONE
- **THESIS_USE:** none
- **AUTHORITATIVE_FILES:** `report.md` · `handoff.md` · `run.json` · `inventory.json` · `code_index_removed_entries.md` · `relocated/capability-descriptors.json` · `inputs/candidate_divergence.json` · `diagnostics/freeze_be4b8287.log`
- **RUN_ID_POLICY:** TASK_NAME (naming policy 2026-10-07)

## WAVE_ID = DOCUMENTATION_AND_NAMING_CLEANUP
- **RUN_ID:** docs-cleanup (task docs-cleanup; same branch)
- **DATE:** 2026-10-08
- **REPORT:** docs/evaluation/geometry/runs/docs-cleanup/report.md
- **ARTIFACT_DIRECTORY:** docs/evaluation/geometry/runs/docs-cleanup/
- **START_BASE:** 2a7179a9
- **CODE_COMMIT:** a993aa8f · c1a291ba · 8c66249d · 9efb8af6 · artifact cleanup from `4acd1f61` · report organization `23aff0ad`/`a3448c71` · product/consolidation `f967ba24` · candidate `267c195a` · consumer/guard sync `838237fe`
- **MEASUREMENT_COMMIT:** NONE (0 model requests, 0 screenshots); independent manifests retained as `run-artifact-cleanup.json` and `run-report-organization.json`
- **EVIDENCE_COMMIT_ROLE:** one consolidated inventory plus independent historical manifests/logs
- **CLASSIFICATION:** CLEANUP_CONSOLIDATED_AND_OFFLINE_VERIFIED
- **PRODUCT_CHANGE:** cleanup NO; same delivery closes one separately scoped assumption-reason gap without changing serve/refuse decision
- **MODEL_REQUEST_COUNT:** 0
- **CANDIDATE_CHANGE:** YES (`b4a33205…` → `7f3f042309dd1c54…`; 102 file; clean refreeze at product commit `f967ba24`)
- **CACHE_CHANGE:** YES (117 → 118 because cached refusal envelope changes)
- **CORRECTED_BY:** NONE
- **CORRECTS:** first-run unread-scope limitation; continuation and organization are histories inside this run
- **SUPERSEDES:** NONE
- **THESIS_USE:** none
- **AUTHORITATIVE_FILES:** `plan.md` · `inventory.md` · `report.md` · `handoff.md` · `run.json` · `run-artifact-cleanup.json` · `run-report-organization.json` · `diagnostics/`
- **RUN_ID_POLICY:** TASK_NAME (naming policy 2026-10-07)

## WAVE_ID = MOBILE_CANVAS_FIT
- **RUN_ID:** mobile-canvas-fit (task mobile-canvas-fit; same branch)
- **DATE:** 2026-10-08
- **REPORT:** docs/evaluation/geometry/runs/mobile-canvas-fit/report.md
- **ARTIFACT_DIRECTORY:** docs/evaluation/geometry/runs/mobile-canvas-fit/
- **START_BASE:** 38a19c65
- **CODE_COMMIT:** c9bcdcdb (product) · harness b8615356 · a51c788b (candidate refreeze 002185a8; plan/review set/baseline 2d169347, 90921f53)
- **MEASUREMENT_COMMIT:** 90921f53 (local, clean detached CRLF worktree with a space in its path; D5 probe, suite, W02, W04, W05, occlusion, playback, builder; eight families); suite step for regular_triangular_pyramid rerun alone at a51c788b (stale suite expectation); baseline probe on a scratch build of 38a19c65 (`diagnostics/baseline_38a19c65/`)
- **EVIDENCE_COMMIT_ROLE:** evidence commit 3f874fed after the measurement (results, images, fixtures, logs)
- **CLASSIFICATION:** READY_FOR_HUMAN_VISUAL_REVIEW (T3 + identity gates at the run's final documentation commit — `handoff.md` §2)
- **PRODUCT_CHANGE:** YES (frontend only: narrow-layout canvas height, steps panel scroll)
- **MODEL_REQUEST_COUNT:** 0
- **CANDIDATE_CHANGE:** product_commit_sha only (f967ba24 -> c9bcdcdb); measured-system tree 7f3f0423... unchanged
- **CACHE_CHANGE:** NO (CACHE_VERSION 118; no envelope changes)
- **CORRECTED_BY:** NONE
- **CORRECTS:** suite manifest `frontend/scripts/generic-tier-a-scenarios.json` (two oracle_source pins stale since 23aff0ad/f967ba24; T8 missing-height refusal expectation stale since f967ba24); living docs `AI_CONTEXT_BUNDLE.md` §1 (CACHE_VERSION 117) and `ROADMAP.md` §0 (docs-cleanup identity) — earlier run files untouched
- **SUPERSEDES:** NONE (earlier review packages stay; images of A-R8, B-R5, C-R1-R3, C-R9 now also exist on the final candidate)
- **THESIS_USE:** learner-facing simulation on phones (D5); human review NOT_APPROVED
- **AUTHORITATIVE_FILES:** `review.md` · `report.md` · `handoff.md` · `run.json` · `plan.md` · `inputs/REVIEW_SET.json` · `results/MOBILE_LAYOUT_PROBE.json` · `results/BROWSER_EVIDENCE.json` · `results/rerun/BROWSER_EVIDENCE.json` · `results/W02_CLOSURE_PROBE.json` · `results/W04_PANELS_PROBE.json` · `results/W05_FOCUS_PROBE.json` · `results/OCCLUSION_MEASUREMENT.json` · `results/PLAYBACK_EVIDENCE.json` · `images/` · `diagnostics/`
- **RUN_ID_POLICY:** TASK_NAME (naming policy 2026-10-07)

## WAVE_ID = PHONE_LANDSCAPE_LAYOUT
- **RUN_ID:** phone-landscape-layout (task phone-landscape-layout; same branch)
- **DATE:** 2026-10-08/09
- **REPORT:** docs/evaluation/geometry/runs/phone-landscape-layout/report.md
- **ARTIFACT_DIRECTORY:** docs/evaluation/geometry/runs/phone-landscape-layout/
- **START_BASE:** f6ebe946
- **CODE_COMMIT:** d8ad153b · 95a56a17 (product); candidate refreeze f884aa67, 5892fefd; plan/review set/baseline 9af3e8a3, 221ec0a0
- **MEASUREMENT_COMMIT:** 221ec0a0 attempt 3 (local, clean detached CRLF worktree with a space in its path; every step in one run: landscape/mobile probe over 7 viewports, full Tier-A suite, W02, W04, W05, occlusion, playback, builder); attempts 1 (9af3e8a3) and 2 (221ec0a0) kept (`MEASUREMENT_ATTEMPTS.json`, `diagnostics/attempts/`); baseline on a scratch build of f6ebe946 (`diagnostics/baseline_f6ebe946/`)
- **EVIDENCE_COMMIT_ROLE:** evidence commit b1ba2575 after the measurement (results, images, fixtures, logs, attempt records)
- **CLASSIFICATION:** READY_FOR_HUMAN_VISUAL_REVIEW (T3 + identity gates at the run's final documentation commit — `handoff.md` §2)
- **PRODUCT_CHANGE:** YES (frontend only: short-landscape control column, 360 px play buttons)
- **MODEL_REQUEST_COUNT:** 0
- **CANDIDATE_CHANGE:** product_commit_sha only (c9bcdcdb -> d8ad153b -> 95a56a17); measured-system tree 7f3f0423... unchanged
- **CACHE_CHANGE:** NO (CACHE_VERSION 118)
- **CORRECTED_BY:** NONE
- **CORRECTS:** NONE (earlier runs untouched; ISSUE-ARCH-PHONE-LANDSCAPE-CONTROLS-BELOW-FOLD resolved in OPEN_ISSUES)
- **SUPERSEDES:** NONE
- **THESIS_USE:** learner-facing simulation on phones in landscape and on small screens; human review NOT_APPROVED
- **AUTHORITATIVE_FILES:** `review.md` · `report.md` · `handoff.md` · `run.json` · `plan.md` · `MEASUREMENT_ATTEMPTS.json` · `inputs/REVIEW_SET.json` · `results/MOBILE_LAYOUT_PROBE.json` · `results/BROWSER_EVIDENCE.json` · `results/W02_CLOSURE_PROBE.json` · `results/W04_PANELS_PROBE.json` · `results/W05_FOCUS_PROBE.json` · `results/OCCLUSION_MEASUREMENT.json` · `results/PLAYBACK_EVIDENCE.json` · `images/` · `diagnostics/`
- **RUN_ID_POLICY:** TASK_NAME (naming policy 2026-10-07)

## WAVE_ID = FINAL_ACCEPTANCE
- **RUN_ID:** final-acceptance (task final-acceptance; same branch)
- **DATE:** 2026-10-09
- **REPORT:** docs/evaluation/geometry/runs/final-acceptance/report.md
- **ARTIFACT_DIRECTORY:** docs/evaluation/geometry/runs/final-acceptance/
- **START_BASE:** bc989cd2
- **CODE_COMMIT:** NONE (no product change)
- **MEASUREMENT_COMMIT:** bc989cd2 source (frontend/src identical to 95a56a17); scratch builds of that source and of main 38d41588 (removed detached worktree); two one-off probes (classroom band, emulated touch), 0 model requests
- **EVIDENCE_COMMIT_ROLE:** the run's documentation commit (results, probes, one image)
- **CLASSIFICATION:** READY_FOR_USER_ACCEPTANCE (identity re-verified; Tier-A 8/8 and T3 of phone-landscape-layout reused — same product)
- **PRODUCT_CHANGE:** NO
- **MODEL_REQUEST_COUNT:** 0
- **CANDIDATE_CHANGE:** NO (7f3f0423..., --verify match)
- **CACHE_CHANGE:** NO (CACHE_VERSION 118)
- **CORRECTED_BY:** NONE
- **CORRECTS:** NONE (phone-landscape-layout report §6 listed the classroom band as unmeasured; measured here, earlier files untouched)
- **SUPERSEDES:** NONE
- **THESIS_USE:** merge readiness of the branch; classroom band defect (pre-existing on main); emulated-touch support for E-R6/F-R7 (not a device check)
- **AUTHORITATIVE_FILES:** `review.md` · `report.md` · `handoff.md` · `run.json` · `results/CLASS_BAND_PROBE.json` · `results/TOUCH_PROXY_PROBE.json` · `images/` · `diagnostics/`
- **RUN_ID_POLICY:** TASK_NAME (naming policy 2026-10-07)

## WAVE_ID = CLASSROOM_BAND_FIT
- **RUN_ID:** classroom-band-fit (task classroom-band-fit; same branch)
- **DATE:** 2026-10-09
- **REPORT:** docs/evaluation/geometry/runs/classroom-band-fit/report.md
- **ARTIFACT_DIRECTORY:** docs/evaluation/geometry/runs/classroom-band-fit/
- **START_BASE:** 1086da7f
- **CODE_COMMIT:** 45f5a7f0 (product); candidate refreeze 83db0e97; plan/probe/baseline 9284202d, 6a1801e7
- **MEASUREMENT_COMMIT:** 6a1801e7 attempt 3 (local, clean detached CRLF worktree with a space in its path; every step in one run: class band probe 3 roles x 8 viewports, phone/landscape probe without a band, full Tier-A suite, W02, W04, W05); attempts 1-2 kept (`MEASUREMENT_ATTEMPTS.json`, `diagnostics/attempts/`); baseline on a scratch build of 95a56a17 (`diagnostics/baseline_95a56a17/`)
- **EVIDENCE_COMMIT_ROLE:** evidence commit 3095e4f0 after the measurement (results, fixtures, 3 images, logs)
- **CLASSIFICATION:** READY_FOR_USER_ACCEPTANCE (T3 + identity gates at the run's final documentation commit — `handoff.md` §2)
- **PRODUCT_CHANGE:** YES (frontend only: classroom band chip on tight screens, title floor, tool group no-wrap)
- **MODEL_REQUEST_COUNT:** 0
- **CANDIDATE_CHANGE:** product_commit_sha only (95a56a17 -> 45f5a7f0); measured-system tree 7f3f0423... unchanged
- **CACHE_CHANGE:** NO (CACHE_VERSION 118)
- **CORRECTED_BY:** NONE
- **CORRECTS:** NONE (final-acceptance recorded the defect and an unmeasured proposal; that proposal measured 15/24 here and was superseded by the user's chip decision — earlier files untouched)
- **SUPERSEDES:** NONE
- **THESIS_USE:** classroom mode on phones; human review NOT_APPROVED
- **AUTHORITATIVE_FILES:** `review.md` · `report.md` · `handoff.md` · `run.json` · `plan.md` · `MEASUREMENT_ATTEMPTS.json` · `results/CLASS_BAND_PROBE.json` · `results/MOBILE_LAYOUT_PROBE.json` · `results/BROWSER_EVIDENCE.json` · `results/W02_CLOSURE_PROBE.json` · `results/W04_PANELS_PROBE.json` · `results/W05_FOCUS_PROBE.json` · `images/` · `diagnostics/`
- **RUN_ID_POLICY:** TASK_NAME (naming policy 2026-10-07)
