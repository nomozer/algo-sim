# geometry-grounding-safety — báo cáo

Nhánh `fix/geometry-grounding-safety` từ `e6c3cf68` (= `origin/main`, khớp, cây sạch). Cloud, 0 lượt gọi model, `LLM_ONLY`
mặc định, compiler opt-in, frontend không đổi. Tiền đăng ký `17353c3` (plan, nhãn, oracle, amendment §21) trước mọi sửa
sản phẩm. Kết luận: **`CLOUD_IMPLEMENTATION_COMPLETE_LOCAL_VERIFICATION_REQUIRED`**.

## 1. Lỗi C0 — mô tả hình mâu thuẫn toạ độ

- **Tái hiện:** probe của general-polygon-base tại `e6c3cf68`: "hình thang vuông tại C và D" với toạ độ vuông tại A, B
  được phục vụ `V = 6`, `PROVEN_SAFE` C0 (`cache/proof_probe_e6c3cf68.log`).
- **Nguyên nhân:** `assumption_gate.kiem_gia_dinh` cấp C0 ngay khi mọi literal được nguồn ghim; ràng buộc hình dạng server
  đọc (`shape_constraint.doc_rang_buoc`) chỉ dùng cho khuôn C1, không bao giờ kiểm trên toạ độ.
- **Sửa (tầng: cổng chứng chỉ giả định, dùng chung mọi tuyến):** `_mau_thuan_c0` kiểm CHÍNH XÁC trên toạ độ chương
  trình mọi ràng buộc đọc được thuộc 8 kind (vuông góc đường–đường, đường–mặt, tam giác vuông, chữ nhật, vuông + cạnh,
  bình hành, thoi, tam giác đều + cạnh) khi mọi điểm của nó có trong chương trình. Sai ⇒ từ chối
  `SOURCE_SHAPE_CONTRADICTS_COORDINATES` (nguyên nhân `SOURCE`, không gửi đi sửa, lời riêng cho học sinh, không Scene3D).
  Thiếu điểm hoặc kind ngoài danh sách ⇒ không kiểm, không từ chối. Thứ tự ưu tiên nguồn không đổi; độ dài/toạ độ vẫn do
  cổng bất biến nguồn cũ. Không tắt hay nới cổng nào.

## 2. Lỗi compiler — tự coi đáy là hình chữ nhật

- **Tái hiện:** đáy tứ giác không khai dạng, một góc vuông ⇒ họ chóp đáy chữ nhật / hộp nhận (`SUPPORTED`), chỉ cổng giả
  định chặn (test LOCAL của general-polygon-base).
- **Sửa (tầng: eligibility của compiler):** `_da_chung_minh_chu_nhat` — hình chữ nhật khi góc vuông giữa hai cạnh KỀ ở ≥ 3
  đỉnh (tái dùng `_goc_vuong_day` của G05); một góc vuông ⇒ `BASE_RECTANGLE_NOT_PROVEN`, lùi về LLM. Đáy khai
  chữ nhật/vuông, khối khai hộp/lập phương, chuỗi G05 không đổi.

## 3. Kiểm chứng

- `test_geometry_grounding_safety.py` 21/21: 11 ca C0 (5 mâu thuẫn bị từ chối có mã + chủ thể; 6 nhất quán/thiếu mô tả vẫn
  phục vụ đúng oracle; đổi tên đỉnh, đổi vị trí góc vuông, cạnh hình vuông, đường vuông góc mặt), không Scene3D qua
  `run_pipeline`; 7 ca compiler (một góc vuông ×3 biến thể ⇒ lùi; 3 góc vuông, chữ nhật khai, hộp khai, hình thang G05 ⇒
  giữ). Red-before tại mã `e6c3cf68`: 10 đỏ / 11 xanh. Oracle độc lập khớp.
- Đính chính nhãn R06 TRƯỚC khi sửa sản phẩm (`label_corrections.json`): lăng trụ đứng đáy chữ nhật không chữ "hộp" vốn bị
  cổng từ chối (giới hạn có sẵn) — hàng nay chỉ khẳng định quyết định compiler.
- Hồi quy: G04 51/51, G05 53/53 (một test LOCAL cập nhật theo hợp đồng mới: compiler lùi về LLM thay vì dựng hình chữ nhật
  rồi bị cổng chặn — vẫn không Scene3D), compiler/bộ đọc/chứng chỉ giả định/C0 toạ độ xanh; demo 5/5, bề mặt sập 6/6;
  49/49 fixture Tier-A trùng byte.
- Toàn bộ pytest (worktree sạch, cùng máy): `fbade46` 7224 passed / 136 failed / 4 errors; baseline `e6c3cf68`
  7208 / 131 / 4 — 131 + 4 có sẵn trùng hệt; 5 đỏ mới = danh tính candidate (mã sản phẩm + `CACHE_VERSION` ghi trong
  candidate) — `results/pytest_compare.json`.

## 4. Cache · schema · candidate

- Bề mặt mô hình KHÔNG đổi (prompt, thẻ văn phạm, hai lược đồ, băm năng lực IR).
- **`CACHE_VERSION` 118 → 119**: một đề từng PHỤC VỤ nay bị từ chối (probe trước/sau) ⇒ hàng cache 118 sẽ trả envelope cũ
  (`cache/decision.json`). Khoá danh tính sinh lại bằng `lock_cache_identity.py`; các test ghim 118 cập nhật kèm ghi chú.
- Candidate `72d6070a…` CHƯA đóng băng lại (LOCAL).

## 5. Chưa kiểm chứng

Kind ràng buộc toàn khối (`right_prism`, `cuboid`, `cube`, chóp đều, `height`) trong C0; quan hệ có điểm vắng trong chương
trình; mâu thuẫn trong đề KHÔNG có toạ độ (C1 tự kiểm ràng buộc khuôn); T3 trình duyệt; mô hình thật.
