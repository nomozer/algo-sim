# Occlusion and Scene Identity Architecture Amendment

**Effective date:** 2026-09-28

**Authority:** product code and tests at the eight-commit occlusion repair wave

**Verification state:** w09 human review `FAIL_REQUIRES_PEDAGOGICAL_VISUAL_REPAIR`; w10 automation — see §Trạng thái kiểm chứng (human review pending)

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
8. **Khoá camera của classifier là khoá chuẩn hoá** (w09). OrbitControls với
   damping ghi lại pose ở vài ULP cuối mỗi frame; khoá dùng 10 chữ số có nghĩa
   (±0 và nhiễu < 1e-12 → 0). Mọi đổi pose làm điểm chiếu dịch > 0,5 px vẫn
   buộc tính lại. Danh tính camera đóng băng phía bằng chứng so theo preimage
   đã xác minh sha256 + tương đương phép chiếu, không theo float thô.
9. **Giá trị trace đi qua biên vận chuyển** (w09). `scene3d.events[].details`
   ra envelope, nên giá trị hình học trong trace dùng đúng khuôn của vật cảnh
   (`_than_hinh_hoc`); kiểu runtime chưa đăng ký thì ném, không đi thô tới
   `json.dumps` của API.
10. **Phân loại CPU là thẩm quyền của CẢ HAI lớp nét** (w10). Đoạn khuất và
    đoạn thấy của cạnh chuẩn đều tắt `depthTest`: GPU kiểm lại từng loại mất
    hết điểm ảnh của đoạn khuất (nằm sau lớp chiều sâu của chính khối) và làm
    nhạt đoạn thấy giữa hai mặt trước (mẫu MSAA trượt phép kiểm). Nét ở hàng đợi
    trong suốt nên vẽ sau mặt tô; mực cạnh tách khỏi màu mặt tô. Giới hạn đã
    khai: phân loại chỉ xét mặt của chính khối — cảnh nhiều khối chồng nhau cần
    `occluders` (`ponytail:` ở `canonicalEdgeMaterial`).
11. **Đoạn trùng cạnh khối trỏ về owner chuẩn** (w10). Backend gắn
    `boundary_edge_ids` cho `segment3` trùng cạnh (theo TÊN đầu mút); khi khối
    có mặt cùng vị trí trình bày thì đoạn chỉ còn vùng bấm — quyết định 2 nay
    áp cả cho đoạn thẳng, không chỉ đa giác/thiết diện.
12. **Camera mặc định được CHỌN theo số đo cảnh** (w10). Hướng Z-up lấy từ
    lưới phương vị × góc ngẩng theo diện tích bao chiếu, độ sâu, khoảng đỉnh,
    khoảng đỉnh–cạnh và độ nghiêng mặt; khoảng cách vừa khít theo hình chiếu.
    Vì camera đã duyệt ở wave occlusion không còn, phía bằng chứng chuyển kỳ
    vọng người sang camera mới CHỈ khi đo khai đổi camera và oracle tái tạo
    đúng tập đã duyệt ở cả hai camera (`transfer_expectation`); registry giữ
    nguyên từng byte.

## Trạng thái kiểm chứng

**w10 (`HUMAN_VISUAL_REVIEW_AND_PEDAGOGICAL_PLAYBACK_CLOSURE`):** review người của
w09 là `FAIL_REQUIRES_PEDAGOGICAL_VISUAL_REPAIR` (ghi bổ sung ở run w10). Kết quả
tự động của wave sửa: [`REPORT.md`](../evaluation/geometry/runs/w10-pedagogical-playback/REPORT.md).
Chưa có human visual acceptance, chưa merge.

**w09 (measurement `defb77ed`, trước review người):** mọi cổng tự động PASS — T3 trong
detached worktree, browser 6 family × desktop/mobile, 12/12 cửa sổ bất biến,
camera đóng băng 3 `EXACT` + 3 `CANONICAL_EQUIVALENT`, product ↔ oracle 0
mismatch ⇒ `READY_FOR_HUMAN_VISUAL_REVIEW`. Chưa có human visual acceptance, chưa
merge. Nguồn: [`REPORT.md`](../evaluation/geometry/runs/w09-verify-cleanup/REPORT.md).

Lịch sử (wave occlusion, đã được w09 đính chính):

Exact edge IDs/spans, perspective cross-check, formation semantics, section
identity và worktree recovery đều PASS. Toàn wave vẫn
`VERIFICATION_NOT_CLEAN` vì frozen camera identity fail ở 2 cases, mobile
`immutable_120_frames` fail ở 5 families, frontend full còn 1 failure và
backend full còn 35 failures. Không có human visual acceptance và không có
merge readiness.

Nguồn bằng chứng:
[`REPORT.md`](../evaluation/geometry/runs/20260928-cross-family-hidden-line-occlusion-oracle-and-formation-repair/REPORT.md),
[`VERIFICATION_SUMMARY.json`](../evaluation/geometry/runs/20260928-cross-family-hidden-line-occlusion-oracle-and-formation-repair/results/VERIFICATION_SUMMARY.json).
