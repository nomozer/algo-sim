# general-polygon-base — báo cáo (G05 chóp / lăng trụ đáy đa giác)

Nhánh `feat/general-polygon-base` từ `d5287ff7` (= `origin/main`, khớp, cây sạch). Cloud, 0 lượt gọi model, `LLM_ONLY`
mặc định, compiler opt-in, frontend không đổi. Tiền đăng ký: `plan.md`, `labels.json`, `oracle.py`, amendment §20 —
commit `5e1e3e9`, trước mọi thay đổi sản phẩm. Kết luận: **`CLOUD_IMPLEMENTATION_COMPLETE_LOCAL_VERIFICATION_REQUIRED`**.

## 1. G05 có từ trước (mã tại `d5287ff7`)

| Thành phần | Trạng thái | Loại |
|---|---|---|
| `construct_polygon`, thể tích/diện tích chính xác mọi n; primitive `construct_pyramid`/`construct_prism` mọi n | có | (1) dùng được; compiler chỉ gọi cho đáy tam giác vuông / chữ nhật / vuông |
| Đa giác cho bằng toạ độ (mọi n) | LLM_ONLY phục vụ qua C0 (probe S.ABCDE, V = 8) | (5) đã phục vụ (chương trình kiểu mô hình); compiler không đọc toạ độ |
| Hợp đồng: `base_cycle` mọi n, góc vuông `perpendicular_lines`, độ dài | có | (2) đủ cho đáy theo chuỗi góc vuông, chưa ai tiêu thụ |
| Hình thang vuông | bộ đọc không đọc ⇒ LLM_ONLY `ASSUMPTION_INVARIANCE_UNPROVEN`; compiler coi đáy có góc vuông là HÌNH CHỮ NHẬT (eligibility `INVALID_CONFLICT RECTANGLE_OPPOSITE_EDGES_UNEQUAL`, định tuyến lùi về LLM — `plan.md` ghi "từ chối nhầm"; đính chính: là lùi về LLM với mô hình đáy sai) | (3) thiếu + lỗi mô hình đáy |
| Chóp đáy tam giác vuông, chân ≠ đỉnh vuông | T1 đòi góc vuông tại chân ⇒ từ chối | (3) thiếu |
| Đa giác đều ≠ hình vuông, góc theo độ, đáy lõm | không đọc / vô tỉ / không khuôn | ngoài miền |

## 2. Bổ sung (tái dùng tối đa)

| Thành phần | Mới hay tái dùng | Lý do |
|---|---|---|
| `kernel.right_angle_chain_start`, `kernel.polygon_from_right_angle_chain` | **mới** (2 hàm) | không hàm nào dựng đa giác từ cạnh + góc vuông; đặt ở kernel để cổng và compiler dùng MỘT thẩm quyền |
| `shape_constraint._HINH_THANG_VUONG` | **mới** (1 mẫu) | cụm "hình thang vuông tại P và Q" phát `line_perp_line` (từ vựng đã có) |
| `assumption_gate._khuon_day_chuoi` (T10), `_vuong_tai_dinh` | **mới** trong khung `_Khuon` | tái dùng `_KichThuoc`, `_vuong`, `_do_dai_tu_rb`, `square`, `_o`, phản ví dụ `canh`/`phap_tuyen`, đối chiếu chính tắc |
| compiler `_danh_gia_eligibility_day_chuoi`, `_uu_tien_day_chuoi`, `_bien_dich_day_chuoi` | **mới** | tái dùng `construct_pyramid`, `construct_prism`, `construct_polygon`, `vector_from_points`/`translate_point` (G04), `_khai_do_dai_de_cho`, `_gia_tri`; kernel tính đỉnh trên, chiều cao (khoảng cách tới mặt đáy), diện tích, thể tích |

Không engine thứ hai; compiler không tính thể tích/diện tích; không nhánh theo số cạnh trong họ mới (test
`test_cung_mot_ham_cho_moi_so_canh`: tam giác, tứ giác, ngũ giác → cùng một họ, cùng một chuỗi câu lệnh).

## 3. Dạng được phục vụ (đúng hoặc từ chối) — 7/7 dương, hai tuyến, khớp oracle

| Hàng | Biến thể | V |
|---|---|---|
| P01 | chóp, hình thang vuông tại A, B, chân A | 6 |
| P02 | đổi tên MNPQ, chân ở đỉnh vuông thứ hai N | 15 |
| P03 | phân số, đáy lớn ở phía xa | 7/2 |
| P04 | lăng trụ đứng đáy hình thang vuông | 30 |
| P05 | chóp đáy tam giác vuông tại B, chân A (trước bị từ chối) | 12 |
| P06 | ngũ giác ba góc vuông liên tiếp (độ phủ theo số cạnh, cho bằng quan hệ ⊥) | 20/3 |
| P07 | hình thang vuông tại A và D | 5 |

## 4. Từ chối đúng — 8/8 âm, hai tuyến

N01 thiếu cạnh của chuỗi (compiler `REQUIRED_FACT_MISSING` — trước đây họ chữ nhật nhận như hình chữ nhật) · N02 thiếu
chiều cao (`ASSUMPTION_DETERMINES_ANSWER`) · N03 cạnh khép mâu thuẫn (compiler `REFUSE`) · N04 lục giác đều · N05 chuỗi
khép không lồi (`BASE_CHAIN_NOT_CONVEX`) · N06 hình bình hành theo góc 60° · N07 chương trình LLM đặt đáy sai chiều
(compiler phục vụ đúng 6) · N08 lăng trụ không nói "đứng", không có cạnh bên ⊥ đáy.

## 5. Hai tuyến

- **LLM_ONLY:** bộ đọc + T10 nhận đúng/từ chối đúng 15/15 trên chương trình kiểu mô hình viết tay. **Chưa đo Gemini
  thật** ⇒ `product_capability.right_angle_chain_base = foundation_only`.
- **Compiler (`DETERMINISTIC_FIRST`, opt-in):** FactGraph → eligibility → Semantic Program → validator → toàn bộ cổng →
  kernel → Scene3D. Lượt gọi model đo được trên 8 hàng phục vụ: synthesis **0** (`call_gemini` bị chặn ném lỗi trong
  test); `analyze` được giả lập (sản phẩm thật vẫn gọi 1 lượt analyze). Không suy ra mức tiết kiệm token toàn pipeline.
  Compiler-first KHÔNG bật.

## 6. Kiểm chứng

- `test_general_polygon_base.py` 51/51 (oracle độc lập; bộ đọc; quyết định compiler 15/15; route sản phẩm 8 hàng; bất
  biến phẳng, lồi, góc vuông, cạnh đứng ⊥ đáy, tịnh tiến, chiều cao đo = độ dài đề cho, Euler; xuất xứ; mặc định
  `DISABLED`; LLM_ONLY 15/15). Red-before trên mã `d5287ff7`: 39 đỏ / 12 xanh.
- Hồi quy: G04 51/51; sáu họ compiler cũ + bộ đọc + chứng chỉ giả định 535 test xanh; demo 5/5; bề mặt sập 6/6; 49/49
  fixture Tier-A trùng byte.
- Toàn bộ pytest (worktree sạch, cùng máy): `4e30a21` 7202 passed / 135 failed / 4 errors; baseline `d5287ff7`
  7155 / 131 / 4 — 131 + 4 có sẵn trùng hệt; 4 đỏ mới = danh tính candidate (`results/pytest_compare.json`).
- `CACHE_VERSION` 118, không bump (`cache/decision.json`); bề mặt mô hình không đổi (`lock_cache_identity --verify` khớp).
- **Không chạy trên Cloud:** T3 `full-gate.mjs`, vitest, build, trình duyệt; đóng băng candidate.
