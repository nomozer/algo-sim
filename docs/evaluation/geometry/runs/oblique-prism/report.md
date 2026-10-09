# oblique-prism — báo cáo (G04 lăng trụ xiên)

Nhánh `feat/oblique-prism` từ `ba995887` (= `origin/main`, khớp khi bắt đầu). Cloud, 0 lượt gọi model, `LLM_ONLY`
mặc định không đổi, frontend không đổi. Kế hoạch và tiền đăng ký: `plan.md` (commit `e39ed32`, trước mọi thay đổi sản
phẩm). Kết luận: **`CLOUD_IMPLEMENTATION_COMPLETE_LOCAL_VERIFICATION_REQUIRED`** — xem §6.

## 1. Năng lực G04 có từ trước (đọc mã tại `ba995887`)

| Thành phần | Trạng thái trước | Loại (theo brief) |
|---|---|---|
| `PrismTopologySpec.lateral_structure ∈ {right, oblique}`, quan hệ `perpendicular_line_plane`, độ dài `segment_length` | có — đủ biểu diễn "A'B ⊥ (ABC), A'B = 6" | (2) có, chưa ai tiêu thụ |
| `construct_prism` (mặt cho mọi n, không giả định đứng) | có | (1) có, compiler chỉ gọi cho lăng trụ đứng |
| Kernel: `translate`, `vector_from_points`, `construct_plane`, `distance(point, plane)`, `volume` chính xác, `sqrt_rational` | có | (1) có, compiler chưa gọi |
| Bộ đọc nguồn server: `oblique_prism`, `line_perp_plane`, `right_triangle`, `base_rectangle/square` | có | (4) có, chưa khuôn nào dùng |
| Compiler eligibility | lăng trụ tam giác **bỏ qua** `lateral_structure` (đề xiên có `AA' ⊥ (ABC)` bị dựng thành lăng trụ đứng); lăng trụ tứ giác `oblique` ⇒ mâu thuẫn | (3) thiếu thật + một lỗi |
| Cổng chứng chỉ giả định (dùng chung hai tuyến) | T3/T6 chỉ cho lăng trụ ĐỨNG ⇒ mọi lăng trụ xiên `ASSUMPTION_INVARIANCE_UNPROVEN` | (3) thiếu thật — mắt xích chặn cả LLM_ONLY |
| Phục vụ sản phẩm (LLM_ONLY) | **0 dạng G04 có đáp số** (red-before: 6/6 hàng dương bị từ chối ở `assumption`) | (5) không |

## 2. Thay đổi (tái sử dụng tối đa; không engine thứ hai)

- **Khuôn T9** (`assumption_gate._khuon_lang_tru_xien`, amendment §19 đăng ký trước mã): cùng khung `_Khuon` của
  T1–T8 (ràng buộc chính xác trên đỉnh, kích thước bắt buộc, hiện thực chính tắc, phản ví dụ `phap_tuyen`). Dùng chung
  `_goc_vuong_tai`, `_chu_nhat_chinh_tac`, `_can_huu_ti`, `square`, `_do_dai_tu_rb`. Là thay đổi DUY NHẤT trên tuyến
  mặc định có hệ quả phục vụ.
- **Họ compiler `oblique_prism_volume`** (`compiler.py`): đáy ℚ³ + đỉnh neo T trên pháp tuyến tại F (`LAYOUT_DERIVED`);
  vectơ cạnh bên `vector_from_points(B₀, T)` và các đỉnh đáy trên `translate` — **kernel** tính; khối bằng
  `construct_prism`; chiều cao = `distance(T, mặt phẳng đáy)` do kernel đo; thể tích do kernel. Compiler chỉ tính phép
  Pythagore để ĐẶT T khi chiều cao suy từ cạnh bên (`sqrt_rational` của kernel; vô tỉ ⇒ từ chối). Không sao chép phép
  dựng/đo nào của kernel.
- `primitives.py`: hai builder mỏng `vector_from_points`, `translate_point` (ngoài `REGISTRY`, như `construct_polygon`).
- `interpreter.py`: chương trình compiler kể vectơ "Lấy vectơ AA′." thay cho repr `Vec3(…)`; tuyến LLM giữ nguyên byte
  (lỗi ấy của tuyến LLM: `ISSUE-ARCH-LLM-VECTOR-ASSIGN-NARRATION`).
- `product_capability.py`: dòng `oblique_prism` = `foundation_only` (mô hình chưa đo).

## 3. Dạng G04 nay được phục vụ (đúng hoặc từ chối)

Lăng trụ (đáy tam giác vuông / chữ nhật / vuông) có `T F ⊥ (đáy)` với F là một đỉnh đáy KHÁC đỉnh tương ứng của T;
chiều cao: cho trực tiếp `TF`, cụm `chiều cao bằng h`, hoặc suy từ cạnh bên khi h² là bình phương hữu tỉ; có hay không
chữ "xiên"; đổi tên đỉnh; phân số. Sáu biến thể dương, mỗi biến thể qua CẢ HAI tuyến:

| Hàng | Biến thể | V (oracle) | compiler | LLM_ONLY (chương trình kiểu mô hình) |
|---|---|---|---|---|
| OP01 | tam giác, chân ở đỉnh khác, chiều cao trực tiếp | 36 | 36 | 36 |
| OP02 | không chữ "xiên", h từ cạnh bên AA′ = 5 | 24 | 24 | 24 |
| OP03 | đổi tên MNP.QRS, góc vuông không ở chân | 15 | 15 | 15 |
| OP04 | phân số, đỉnh neo B′ | 7/2 | 7/2 | 7/2 |
| OP05 | đáy chữ nhật, chân ở đỉnh chéo, h từ cạnh bên | 144 | 144 | 144 |
| OP06 | đáy vuông, đáy trên EFGH | 6 | 6 | 6 |

## 4. Vẫn chưa hỗ trợ (từ chối đúng — 10/10 hàng âm khớp nhãn trên hai tuyến)

Thiếu dữ kiện cạnh bên (ON01) · có chân không có chiều cao (ON02 — LLM: `ASSUMPTION_DETERMINES_ANSWER`) · góc nghiêng
60° (ON03) · chiều cao vô tỉ √7 (ON04 — compiler `IRRATIONAL_HEIGHT` lùi về LLM; chương trình xấp xỉ bị từ chối) ·
"xiên" + `AA' ⊥ (ABC)` (ON05 — compiler `REFUSE`) · cạnh bên ngắn hơn khoảng lệch (ON06) · chiều cao ≠ cạnh bên
(ON07) · chân ở trung điểm H (ON08) · đáy bình hành (ON09) · chương trình LLM dựng sai chân đường cao (ON10 — từ chối;
compiler phục vụ đúng 36). Mắt xích còn thiếu cho trung điểm/trọng tâm/góc: `ISSUE-ARCH-OBLIQUE-PRISM-FOOT-VOCABULARY`
(hợp đồng chưa có quan hệ trung điểm ⇒ đổi bề mặt mô hình, cần ngân sách đo live; bộ đọc chưa đọc "hình chiếu … là B").

## 5. Hai tuyến đạt đến đâu

- **LLM_ONLY (mặc định):** route tất định (grounding · hậu điều kiện · T9 · Scene3D) nhận đúng và từ chối đúng trên
  chương trình kiểu mô hình. **Chưa đo mô hình thật** sinh được chương trình ấy (prompt không đổi; 0 lượt gọi) ⇒
  `foundation_only`.
- **Compiler (opt-in `DETERMINISTIC_FIRST`):** đi trọn FactGraph → eligibility → Semantic Program → validator → toàn bộ
  cổng của tuyến LLM → Scene3D, 0 lượt gọi synthesis; bước dựng: đáy → đỉnh neo → vectơ cạnh bên → tịnh tiến từng đỉnh
  → đáy trên + cạnh bên (bước bổ sung chung `formation`) → khối → S đáy → (mặt phẳng đáy) → chiều cao → V = S × h.
  Compiler-first KHÔNG bật.

## 6. Kiểm chứng

- `tests/geometry/test_oblique_prism.py`: 51 test (oracle độc lập; quyết định compiler 16/16 theo nhãn; route sản phẩm
  7 hàng phục vụ; bất biến Euler, tịnh tiến, hai đáy song song, cạnh bên xiên, chiều cao đo = thành phần pháp tuyến;
  xuất xứ `LAYOUT_DERIVED`/`GIVEN`; tuyến mặc định `DISABLED`; LLM_ONLY 16/16 theo nhãn; lời kể không repr).
- Red-before: cùng file test chạy trên `ba995887` — 39 đỏ / 11 xanh (mọi hàng dương đỏ trên hai tuyến).
- `CACHE_VERSION` **118, không bump** (`cache/decision.json`): 49/49 envelope fixture Tier-A trùng byte (14 phục vụ);
  T9 chỉ đổi chiều từ chối → phục vụ (lời từ chối không cache). Bề mặt mô hình không đổi (`test_cache_identity` xanh).
- Hồi quy §0.3: demo 5/5 (`replay_demo_cases.py`), bề mặt sập 6/6 (`audit_demo_crash_surface.py`), sáu họ compiler +
  corpus gold/assumption trong bộ pytest. Toàn bộ pytest trên worktree sạch: xem `handoff.md` §2 (so với baseline sạch
  `ba995887` cùng máy).
- **Không chạy trên Cloud:** T3 `full-gate.mjs` / vitest / trình duyệt (frontend không cài, không đổi mã frontend).
