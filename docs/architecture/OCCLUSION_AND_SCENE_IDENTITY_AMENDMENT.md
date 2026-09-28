# Occlusion and Scene Identity Architecture Amendment

**Effective date:** 2026-09-28

**Authority:** product code and tests at the eight-commit occlusion repair wave

**Verification state:** `VERIFICATION_NOT_CLEAN`

Tài liệu này bổ sung các snapshot kiến trúc có trước wave sửa occlusion. Nó
không thay đổi nội dung lịch sử của
`ARCHITECTURE_CAPABILITY_MATRIX.md`/`architecture_capability_matrix.json`;
những trường nói hidden-line còn thiếu hoặc cuboid chưa có browser evidence
phải được đọc qua amendment này và correction chain trong `EVIDENCE_INDEX.md`.

## Quyết định kiến trúc

1. **Machine identity tách display label.** Edge ID dùng endpoint entity IDs
   canonical (`A_prime`), sắp theo stable vertex ordinal. Ký hiệu học sinh như
   `A′` chỉ nằm trong `display_label`.
2. **Một logical edge, một visual owner.** Solid sở hữu canonical edge;
   polygon/section/highlight chỉ tham chiếu owner hoặc làm hit proxy, không tạo
   đường vẽ thứ hai.
3. **Occlusion là policy của surface.** Chỉ `surface_role=SOLID_FACE` với
   `occludes_edges=true` che cạnh. `BASE_REGION`, `SECTION_REGION`,
   `CUTTING_PLANE` và `AUXILIARY_SURFACE` không che mặc định.
4. **Visibility có span.** Mỗi edge thuộc đúng một lớp `VISIBLE`, `HIDDEN` hoặc
   `MIXED`; edge mixed được chia thành các visible/hidden spans dưới cùng owner.
   Highlight chỉ đổi màu/độ rộng/emphasis, không đổi dash policy.
5. **Formation được typed tại producer.** Backend phát
   `GEOMETRY_CONSTRUCTION`, `MEASUREMENT`, `EXPLANATION`, `FINAL_RESULT` và
   `geometry_progress`; frontend không suy semantic kind từ learner text.
6. **Section endpoint có identity bền.** Endpoint giữ provenance
   `SOLID_VERTEX` hoặc `SOLID_EDGE_INTERSECTION`; section edge ID dẫn từ các
   endpoint entity IDs. Coordinate hash chỉ là fallback synthetic/legacy và
   không hợp lệ trong evidence authoritative.
7. **Classifier và oracle độc lập.** Product dùng world-space ray/triangle với
   adaptive refinement. Evidence oracle tự triangulate, clip interval trong
   screen space và nội suy depth perspective-correct; synthetic reference dùng
   camera ray/triangle. Oracle không import helper visibility của product.

## Trạng thái kiểm chứng

Exact edge IDs/spans, perspective cross-check, formation semantics, section
identity và worktree recovery đều PASS. Toàn wave vẫn
`VERIFICATION_NOT_CLEAN` vì frozen camera identity fail ở 2 cases, mobile
`immutable_120_frames` fail ở 5 families, frontend full còn 1 failure và
backend full còn 35 failures. Không có human visual acceptance và không có
merge readiness.

Nguồn bằng chứng:
[`REPORT.md`](../evaluation/geometry/runs/20260928-cross-family-hidden-line-occlusion-oracle-and-formation-repair/REPORT.md),
[`VERIFICATION_SUMMARY.json`](../evaluation/geometry/runs/20260928-cross-family-hidden-line-occlusion-oracle-and-formation-repair/results/VERIFICATION_SUMMARY.json).
