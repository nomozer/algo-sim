# Handoff cho Owner: A/B vào main + Scene3D C0

**Trạng thái: `SCENE3D_C0_READY_FOR_OWNER_GO_MAIN`.** Remote: `REMOTE_SECURITY_BLOCKED` (27/27 PENDING). Human visual:
`PENDING`. Không push, không gọi model, không bật production. Nhánh C0 **chưa merge**, chờ Owner.

1. **A/B đã nằm trong local main:** có. `main` = **`9978e512a8a2a087475d792c0bd9db639c36acaa`**, fast-forward từ
   `50cee903`. Freeze MATCH, 426 test tương thích xanh; receipt T3 `57138dbb` còn hiệu lực vì cây product/test trùng
   ([`MAIN_AB_MERGE_REPORT.md`](MAIN_AB_MERGE_REPORT.md)).
2. **Inspector đã giải quyết hai đỉnh không tên:** có. Lăng trụ nay hiện "Giao điểm của BB′ và (α) – M – Giao điểm của
   CC′ và (α)". Điểm được chọn vì phụ thuộc của nó chứng minh nó là giao của đúng cạnh khối với mặt cắt; không chọn vì
   trùng toạ độ, thứ tự hay tên. Không đủ ⇒ "Đỉnh k" ([`INSPECTOR_PROVENANCE_VALIDATION.md`](INSPECTOR_PROVENANCE_VALIDATION.md)).
3. **Hình học và provenance không đổi.** 22 cảnh: id, toạ độ, phụ thuộc, thứ tự event, `route_d` (provenance, closure
   certificate, đáp số) bằng lịch sử. I/I1 vẫn `STATED_UNNAMED`, `notation: null`. H/H1 vẫn trong DAG và cảnh.
4. **Hồi quy LLM_ONLY:** không thấy. 0 cảnh đã lưu đổi; `/api/analyze` không nhập `function_route`; cache 127;
   `test_Y` khoá LLM_ONLY xanh; Full T3 PASS.
5. **R1/F5/kd:**
   - R1 sửa.
   - F5 kiểm chứng ở hai mức: bằng chứng là đường mã, nhân chứng là trình duyệt kèm negative control. Không sửa builder
     dùng chung; payload API vẫn mang narration không render.
   - `kd`: bắt buộc theo hợp đồng, đã bị Source Gate từ chối; lớp trình bày nay fail-closed.
   - Đã sửa thêm hai lỗi dấu `′` do review tìm ra.
   ([`NARRATION_AND_FAIL_CLOSED_REGRESSION.md`](NARRATION_AND_FAIL_CLOSED_REGRESSION.md))
6. **Candidate, browser, T3, review:** freeze `ce2aa0f1a9315ea9e6df6801f694cfb2abef39e2` (product `4d3b8849`, measured
   `4acdac53…`). **Full T3 `FULL_PRODUCT_GATE_PASS`** (pytest 11,683 / vitest 1,245 / build / demo 5/5 / crash 6/6).
   Browser **94/94**, refusal **50/50**. Review độc lập vòng 3 **`PASS`**.
7. **Đủ điều kiện merge C0:** đủ để **Owner quyết** (mọi cổng máy xanh, review PASS). Còn chờ duyệt hình
   ([`BROWSER_ACCEPTANCE_REPORT.md`](BROWSER_ACCEPTANCE_REPORT.md) §3).
8. **Blocker trước khi kích hoạt Hybrid:**
   - Không có product endpoint phát wrapper `/4`; `hybrid_preview` vẫn `/1` và chỉ cho operator.
   - Chất lượng NL → TypedFacts V2 là `UNKNOWN`; Full NL → Scene3D `NOT_MEASURED`; chưa có curator độc lập, holdout niêm phong.
   - Chưa có khoá provider/model/prompt, ngân sách và luật dừng, GO live.
   - Chưa qua 20 cổng `docs/MIGRATION_CHECKLIST.md`; quyết định thay mặc định LLM_ONLY.
   - Duyệt hình của người.
   - 27 ngoại lệ xuất bản (remote).
   - Narration `config.frames` trong payload API.

## Owner cần quyết

1. Merge `research/scene3d-section-inspector-c0` (HEAD = commit docs chứa file này) vào `main` (local).
2. Duyệt hình: inspector lăng trụ, nhãn H/H1 trên canvas, refusal, desktop/mobile.
3. 27 ngoại lệ xuất bản và văn bản chính sách (danh sách đóng).

Bất biến: `LLM_ONLY`, `flat`, Hybrid NO-GO, `ALLOW_LIVE_AI=0`, `CACHE_VERSION=127`, IR 32. Worktree dùng lại
(`.superpowers/worktrees/hybrid-session5-offline-consumer`); không tạo worktree, không chép `node_modules`, không đụng ACL.
