# c0-whole-solid-grounding — báo cáo

Nhánh `fix/c0-whole-solid-grounding` từ `9762f441` (= `origin/main`, khớp, cây sạch). Cloud, 0 lượt gọi model,
`LLM_ONLY` mặc định, compiler opt-in, frontend không đổi. Tiền đăng ký `3bbd8c2` (plan, 28 nhãn, oracle, amendment §22,
probe baseline) và `139aa1a` (hàng `edge_all` đã đăng ký kind nhưng thiếu nhãn, kèm probe baseline) — đều trước mọi sửa
sản phẩm. Kết luận: **`CLOUD_IMPLEMENTATION_COMPLETE_LOCAL_VERIFICATION_REQUIRED`**.

## 1. Kiểm kê và lỗi tái hiện (`9762f441`)

Bộ đọc server (`shape_constraint.doc_rang_buoc`) đã phát các khẳng định toàn khối trên khối có tên (ký hiệu `X.Y`,
`S.ABCD`, `tứ diện đều ABCD`), nhưng `_KIEM_C0` (§21) không có định nghĩa nào cho chúng ⇒ đề có toạ độ mâu thuẫn vẫn
được chứng nhận C0. Probe (`diagnostics/probe_9762f441.log`, `probe_9762f441_edge_all.log`) — **16 đề mâu thuẫn được
phục vụ**:

| kind | tái hiện | hàng |
|---|---|---|
| `right_prism` | có | RP_C |
| `oblique_prism` | có | OP_C |
| `cuboid` | có | CU_C ×2 (đáy bình hành; cạnh bên xiên) |
| `cube` / `cube_edge` | có | CB_C ×2 |
| `regular_square_pyramid` + `lateral_edge`, `apothem`, `base_centre` (O chỉ có toạ độ trong đề) | có | RSP_C ×4 |
| `regular_triangular_pyramid` | có | RTP_C |
| `regular_tetrahedron` / `edge_all` | có (đáy đều, cạnh bên khác; cạnh nêu sai) | RT_C ×2 |
| `height` chóp / lăng trụ | có | H_C ×2 |
| `base_centre` với O được chương trình khai | không — đã bị `construction_binding` từ chối | RSP_C_centre_off |
| `prism` trơn (đáy trên không phải tịnh tiến) | không — thực thi đã bác mặt bên không phẳng | P_C ⇒ **không thêm checker** |
| khối không tên (`entities = ()`) | không kiểm được (không ký hiệu đỉnh) | ngoài phạm vi |

## 2. Sửa (tầng: cổng chứng chỉ giả định, dùng chung mọi tuyến)

`assumption_gate._KIEM_C0` thêm định nghĩa CHÍNH XÁC (ℚ, `Vec3` của kernel; Euclid thô như §21 vì toạ độ đề là Descartes):
lăng trụ đứng (đáy trên = đáy dưới + v, v ≠ 0, v ∥ vectơ diện tích đáy), lăng trụ xiên (tịnh tiến, v ∦), hộp chữ nhật
(đứng + đáy chữ nhật), lập phương (hộp + ba cạnh tại một đỉnh bằng nhau), cạnh lập phương, chóp tứ giác/tam giác đều (đáy
vuông/đều + đỉnh trên pháp tuyến tại tâm đáy, ngoài đáy), tứ diện đều (sáu cạnh bằng nhau), mọi cạnh = a, cạnh bên,
trung đoạn, tâm đáy (= trung bình đỉnh đáy), chiều cao (khoảng cách² tới mặt đáy — từ đỉnh chóp hoặc đỉnh đáy trên; KHÔNG
phải cạnh bên). `height` gắn với chóp/lăng trụ có cùng ký hiệu; không gắn được ⇒ không kiểm. Sai ⇒ cùng đường §21:
`SOURCE_SHAPE_CONTRADICTS_COORDINATES`, nguyên nhân `SOURCE`, không gửi đi sửa, không Scene3D. Không đổi bộ đọc, mệnh đề
mục tiêu (đã che), thứ tự nguồn, hay cổng nào khác.

Thiếu dữ kiện ≠ mâu thuẫn: khối không tên, điểm không có toạ độ ở cả chương trình lẫn đề, thiếu số đo ⇒ không kiểm.

## 3. Kiểm chứng

- `tests/geometry/test_c0_whole_solid_grounding.py` 34/34: oracle độc lập; 29 hàng theo nhãn (13 nhất quán phục vụ đúng
  V của oracle với C0 — đổi tên + phân số, chiều cao ≠ cạnh bên, mệnh đề "Chứng minh … là lăng trụ đứng", câu phủ định,
  O không toạ độ; 16 mâu thuẫn bị từ chối có mã + kind + chủ thể, 2 hàng từ chối sẵn giữ chặng cũ); thiếu dữ kiện không
  từ chối; không Scene3D qua `run_pipeline`. **Red-before** (cùng file, mã `9762f441`): 18 đỏ / 16 xanh.
- Probe sau sửa: `diagnostics/probe_c11e8c9.log` — 29/29 khớp nhãn.
- Hồi quy: C0 §21, G04, G05, compiler, bộ đọc, chứng chỉ giả định, chóp đều, toạ độ điểm — trong toàn bộ pytest; demo
  5/5 (`replay_demo_cases.py`), bề mặt sập 6/6 (`audit_demo_crash_surface.py`).
- Toàn bộ pytest (worktree sạch, cùng máy): `results/pytest_compare.json`.

## 4. Cache · schema · candidate

- Bề mặt mô hình KHÔNG đổi (prompt, thẻ văn phạm, hai lược đồ, băm năng lực IR; môi trường `b1714b56…` giữ nguyên).
- **`CACHE_VERSION` 119 → 120**: 16 đề từng PHỤC VỤ nay bị từ chối (probe trước/sau) ⇒ hàng cache 119 sẽ trả envelope cũ
  (`cache/decision.json`). Khoá danh tính sinh lại bằng `lock_cache_identity.py` (`--verify` khớp); test ghim cập nhật.
- Candidate `bbfa5b0d…` CHƯA đóng băng lại (LOCAL; không sửa hash tay).

## 5. Chưa kiểm chứng / còn mở

- `ISSUE-ARCH-C0-WHOLE-SOLID-CLAIMS-NOT-READ`: "hình chóp tứ giác đều có đỉnh S và đáy ABCD", "hình chóp tứ giác đều"
  không tên, "hình chóp đều S.ABCD" — bộ đọc không phát khẳng định ⇒ toạ độ mâu thuẫn vẫn phục vụ
  (`diagnostics/probe_reader_gap_c11e8c9.log`). Sửa bộ đọc đổi cả khuôn C1 ⇒ việc riêng.
- Mâu thuẫn trong đề KHÔNG có toạ độ (C1 tự kiểm ràng buộc khuôn); T3 trình duyệt; mô hình thật.
