# Handoff cho Owner: merge remediation local + sửa hiển thị A/B

Authorization `GO_LOCAL_PUBLICATION_REMEDIATION_MERGE_AND_BACKEND_VISUAL_AB_FIX`. 0 lượt gọi model, không push, không viết
lại lịch sử, không bật production. **Nhánh sửa A/B chưa merge vào `main`.** Dừng ở đây để Owner quyết.

## Trả lời

1. **Remediation đã merge local main:** có. `main` = **`50cee9035d664d7d3d39762610af740a8b8cd558`** (fast-forward từ
   `b4ac5e87`). Freeze MATCH, 83 test docs/identity/gate xanh; gate xuất bản BLOCKED như dự kiến
   ([`LOCAL_REMEDIATION_MERGE_REPORT.md`](LOCAL_REMEDIATION_MERGE_REPORT.md)).
2. **A/B đã sửa đúng gốc chưa:** A có (thẩm quyền đặt tên `prefer_declared_plane_names`, nay bật cho mọi mặt thiết diện
   dẫn xuất; role nói quan hệ đúng chữ của đề). B có cho tên thiết diện và đại lượng (không đặt tên đỉnh không tên qua
   điểm trùng). **B chưa xong ở inspector:** vẫn "Đỉnh 1 – M – Đỉnh 3"; phải sửa `sectionDetails` frontend dùng chung,
   không cần đổi schema (review F4); chờ Owner chọn C0/C1/C2/C3
   ([`BACKEND_VISUAL_AB_FIX_REPORT.md`](BACKEND_VISUAL_AB_FIX_REPORT.md),
   [`SCENE3D_PROVENANCE_COMPATIBILITY.md`](SCENE3D_PROVENANCE_COMPATIBILITY.md)).
   Phát hiện thêm cùng họ và đã sửa: hai đại lượng plane-only bị dán "Đoạn của thiết diện".
3. **Có đổi tính toán hoặc provenance không:** không. Chỉ 94 trường tên trong 22 cảnh; id, toạ độ, depends, thứ tự event,
   `visible_ids`, `route_d` (provenance, closure certificate, answers) bằng lịch sử ở cả 22 cảnh; 25 refusal không đổi.
   Assert ở `export_fixtures.py` + guard test.
4. **Candidate, T3, browser:** product `41c7e6f854c84d4c987b88cd1f4bcd877921cb78`, freeze
   `56bdf9b9218f895fcdc283800a38c5be17d029cc` (116 file, `d16c9b66…`, NO_BUMP 127).
   **Full T3 `FULL_PRODUCT_GATE_PASS`** tại `57138dbb` (pytest 11,637 / vitest 1,238 / build / demo 5/5 / crash 6/6; freeze
   MATCH sau T3) ([`verification/full-t3/execution.json`](verification/full-t3/execution.json)). **Browser acceptance
   94/94 PASS** và **màn từ chối 50/50 PASS** tại `57138dbb`, cây sạch
   ([`BROWSER_VISUAL_ACCEPTANCE_REPORT.md`](BROWSER_VISUAL_ACCEPTANCE_REPORT.md)). Review độc lập vòng 2 `PASS_WITH_FINDINGS`,
   0 BLOCKER/MAJOR ([`INDEPENDENT_REVIEW.md`](INDEPENDENT_REVIEW.md)). Không dùng lại T3 của Session 5.
5. **27 entry xuất bản:** còn **27/27 `PENDING_OWNER_DECISION`**; đã đánh dấu mâu thuẫn mốc ngày và đề xuất văn bản danh
   sách đóng ([`PUBLICATION_SECURITY_PENDING_DECISIONS.md`](PUBLICATION_SECURITY_PENDING_DECISIONS.md)).
   `REMOTE_SECURITY_BLOCKED`.
6. **Đủ điều kiện để Owner nghiệm thu giao diện và merge bản sửa A/B:** đủ để **xem xét** (mọi cổng máy xanh, review không
   còn MAJOR). Chưa nên coi là xong trọn B: inspector đỉnh của lăng trụ còn mở, và còn R1/F5 (văn bản không render vẫn ghi
   "qua ba điểm M, H, H1"). Owner quyết: merge như hiện tại và mở task cho phần còn lại, hay yêu cầu làm tiếp trước.

## Danh tính

| mục | giá trị |
|---|---|
| `main` | `50cee903` (remediation, đã merge) |
| nhánh sửa | `research/scene3d-plane-section-display-identity`, HEAD = commit docs ghi file này (sau `57138dbb`) |
| commit trên nhánh | `ec17602a` fix · `f8ec3222` freeze (bị thay) · `c276b785` tooling · `665f542c` fix · `8efb32b4` freeze (bị thay) · `65cbdd6f` export trung gian · `41c7e6f8` fix review · `56bdf9b9` freeze · `57138dbb` export cuối |
| worktree | `.superpowers/worktrees/hybrid-session5-offline-consumer` (dùng lại, không tạo mới) |
| bất biến | `LLM_ONLY`, `flat`, Hybrid NO-GO, `ALLOW_LIVE_AI=0`, `CACHE_VERSION=127`, IR 32; chỉ `backend/app/ai/function_route.py` đổi |

## Ổ đĩa (P6)

Không tạo worktree mới, không chép `node_modules` (junction có sẵn). Không đổi ACL, không xoá thư mục khoá. Run thêm khoảng
2.2 MB × 2 export JSON và 26 PNG. Ứng viên dọn vẫn như `publication-safety-remediation/ACL_CLEANUP_PLAN.md` (cần admin).
Worktree Session 5 và các nhánh `research/hybrid-session5-offline-consumer`, `research/publication-safety-remediation`
giữ lại (worktree đang mang nhánh sửa A/B chưa merge).

## Owner cần quyết

1. Merge `research/scene3d-plane-section-display-identity` vào `main` (local)?
2. Inspector đỉnh lăng trụ: C0 (frontend dùng dữ liệu có sẵn) / C1 (thêm trường schema) / C2 / C3.
3. R1 + F5 + fail-closed nhánh "khối không `kd`": sửa thêm hay khai là giới hạn?
4. Duyệt hình (bảng trong `BROWSER_VISUAL_ACCEPTANCE_REPORT.md` §3).
5. 27 entry xuất bản và văn bản chính sách (danh sách đóng, không mốc ngày).
