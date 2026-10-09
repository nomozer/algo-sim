# c0-whole-solid-grounding — kế hoạch và tiền đăng ký

Việc: `ISSUE-ARCH-C0-WHOLE-SOLID-RELATIONS-NOT-CHECKED`. Cloud, nhánh `fix/c0-whole-solid-grounding` từ `origin/main` =
`9762f441` (khớp, cây sạch). `LLM_ONLY` mặc định, compiler opt-in, 0 lượt gọi model, frontend không đổi.

## 1. Kiểm kê (mã tại `9762f441`)

| kind (bộ đọc `shape_constraint`) | đọc từ đề | đủ để kiểm trên toạ độ | đã kiểm ở cổng khác | baseline (probe) |
|---|---|---|---|---|
| `right_prism` (`lăng trụ đứng X.Y`) | có (ký hiệu khối) | có: tương ứng theo vị trí trong ký hiệu | không | **phục vụ sai** (RP_C) |
| `oblique_prism` (`lăng trụ xiên X.Y`) | có | có | chỉ với quan hệ của MÔ HÌNH (`REFUTED_BY_SOURCE`) | **phục vụ sai** (OP_C) |
| `cuboid` (`hình hộp chữ nhật`) | có | có | không | **phục vụ sai** (CU_C ×2) |
| `cube` / `cube_edge` | có | có | không | **phục vụ sai** (CB_C ×2) |
| `regular_square_pyramid` (+ `lateral_edge`, `apothem`, `base_centre`) | có | có | `base_centre` có điểm O khai bằng toạ độ: `construction_binding` | **phục vụ sai** ×4 (RSP_C …) |
| `regular_triangular_pyramid` (+ `base_equilateral`) | có | có (ℚ³ khi đề cho toạ độ) | đáy đều: §21 | **phục vụ sai** (RTP_C) |
| `regular_tetrahedron` / `edge_all` | có | có | đáy đều: §21 (đáy BCD) | **phục vụ sai** khi đáy đều mà cạnh bên khác (hàng thêm sau baseline) |
| `height` (`chiều cao bằng h`, khối duy nhất) | có | có: khoảng cách đỉnh / đáy trên tới mặt đáy | không | **phục vụ sai** (chóp và lăng trụ) |
| `prism` (`lăng trụ X.Y`, đáy trên không phải tịnh tiến) | có | có | thực thi bác mặt bên không phẳng (P_C bị từ chối) | đã từ chối — **không thêm checker** |
| khối không tên (`entities = ()`) | có | KHÔNG (không ký hiệu đỉnh) | — | ngoài phạm vi |

Kernel dùng lại: `Vec3.dot/cross/norm_sq/is_zero` (exact), `measure.distance_sq_point_plane` + `Plane3.through` cho
chiều cao. Thiếu toạ độ của một điểm (chương trình không khai và đề không cho) ⇒ không kiểm (§21, giữ nguyên).

## 2. Sửa (đăng ký trước) — amendment §22

Thêm vào `_KIEM_C0` các định nghĩa chính xác của: `right_prism`, `oblique_prism`, `cuboid`, `cube`, `cube_edge`,
`regular_square_pyramid`, `regular_triangular_pyramid`, `regular_tetrahedron`, `edge_all`, `lateral_edge`, `apothem`,
`base_centre`, `height` (chóp: khoảng cách đỉnh tới mặt đáy; lăng trụ: khoảng cách đỉnh đáy trên tới mặt đáy — không phải
độ dài cạnh bên). Sai ⇒ cùng mã `SOURCE_SHAPE_CONTRADICTS_COORDINATES`, cùng đường từ chối §21. Không đổi bộ đọc, không
đổi mệnh đề mục tiêu (đã che), không đổi thứ tự nguồn.

## 3. Tiêu chí

`labels.json` (28 hàng: 15 mâu thuẫn, 13 nhất quán gồm đổi tên + phân số, chiều cao ≠ cạnh bên, mệnh đề chứng minh, câu phủ
định, điểm không có toạ độ, điểm có toạ độ trong đề mà chương trình không khai); `oracle.py` độc lập; baseline
`diagnostics/probe_9762f441.log`. Hồi quy: C0 (§21), G04, G05, compiler, toàn bộ pytest so baseline sạch. Cache: quyết
bằng probe trước/sau (dự kiến served → refused ⇒ bump 119 → 120).
