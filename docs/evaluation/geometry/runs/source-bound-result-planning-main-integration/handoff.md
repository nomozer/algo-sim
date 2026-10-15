# Handoff — source-bound-result-planning-main-integration (2026-10-15)

**Status:** `RESULT_BINDING_MAIN_INTEGRATION_BLOCKED`, chờ người dùng quyết định. `main` vẫn là `2a3c0787`, chưa push.

## Quyết định đang chờ

1. **Chấp nhận giới hạn rồi fast-forward:** IMPORTANT-1/2 là false serve có từ trước, cũng có trên `main`, chỉ ở tuyến
   nghiên cứu không nối vào API; nhánh nghiên cứu từ chối nhiều ca hơn main. Nếu GO: chạy lại preflight (`report.md`
   §2), rồi `git switch main && git merge --ff-only research/source-bound-result-planning`, rồi candidate `--verify`,
   docs/identity gate và targeted gate. T3 `7b14fe04` được `REUSED_NOT_RERUN` nếu cây sản phẩm không đổi. Ghi kết
   quả bằng một addendum trong run này. Không push.
2. **Sửa trước:** trên nhánh nghiên cứu, theo RED → GREEN, `_kiem_phu` kiểm bổ ngữ trên `de` gốc (IMPORTANT-1) và
   dùng văn phạm đóng như ask thường (IMPORTANT-2). Sau đó đóng băng lại candidate, chạy T3 sạch, review độc lập, rồi
   mới tích hợp. Thay đổi này chạm `MEASURED_SYSTEM_PATHS`.

## Ưu tiên kiến trúc kế tiếp (chưa bắt đầu)

**SCENE3D PRODUCT–PLAYWRIGHT VISUAL PARITY AUDIT.** Kiểm xem harness (`frontend/scripts/hybrid-section-visual.tsx`,
`result-binding-visual-check.mjs`) có tái hiện đúng trạng thái UI sản phẩm hay không: màu và opacity, nét khuất/thấy,
chồng nét dựng phụ/giao tuyến/cạnh, mặt phẳng lớn che hình, camera, nhãn, selection, thứ bậc thị giác. Phải kiểm toán
trước khi sửa renderer. `ISSUE-ARCH-SCENE3D-CONSTRUCTION-READABILITY` vẫn OPEN. Không viết lại frontend, Scene3DWorkspace,
Engine hay Kernel.
