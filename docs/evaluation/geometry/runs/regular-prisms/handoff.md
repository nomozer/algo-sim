# regular-prisms — bàn giao cho LOCAL

Nhánh `feat/g05-regular-prisms` (từ `ea85216b`), đã push; không merge, không PR.

| commit | nội dung |
|---|---|
| `680d830` | khảo sát G05 lăng trụ đều, tiền đăng ký: plan (ma trận năng lực), 25 nhãn, oracle, ca, probe baseline |
| `00770c3` | bộ đọc + T12 + metric lăng trụ + C0 lục giác đều / cạnh bên lăng trụ, năng lực sản phẩm, `CACHE_VERSION` 125, khoá, test, ghim, probe ứng viên + probe chuyển trạng thái ngoài nhãn |
| `d8b9da7` | sửa phát hiện ở so sánh toàn bộ pytest: "lăng trụ xiên … đều" không phát T12; ghim "đều" chưa đọc của `test_shape_constraint` chuyển sang lăng trụ tứ giác đều (cập nhật có chủ đích) |
| (commit cuối) | report, handoff, bằng chứng cache, chuyển trạng thái, so sánh pytest, OPEN_ISSUES, CODE_INDEX, CURRENT_STATE, ROADMAP |

## Việc LOCAL

1. Toàn bộ pytest + T3 `full-gate.mjs` trên worktree sạch của nhánh. Frontend KHÔNG đổi mã: cảnh lăng trụ đều dùng
   `chart_metric` qua `scene3d-chart.ts` sẵn có (như T8/T11). Cần T3/trình duyệt xác nhận khung affine 60° của lục giác
   và lưới tam giác hiển thị thành đa giác đều thật, cạnh bên vuông góc đáy (chưa kiểm trên Cloud).
2. Đóng băng lại candidate MỘT lần (`backend/scripts/freeze_evaluation_candidate.py`) — mã sản phẩm đổi
   (`shape_constraint.py`, `assumption_gate.py`, `product_capability.py`, `main.py`). Năm test danh tính candidate đỏ tới
   bước này (`results/pytest_compare.json` `new_red`). Không sửa hash tay.
3. Kiểm độc lập bump 125 (`cache/decision.json`, `diagnostics/probe_extra_ea85216b.log` ↔ `probe_extra_candidate.log`:
   6 hàng C0 served → refused).
4. Kiểm toán học độc lập 13 hàng dương (metric Gram từ độ dài của đề tại A, B, C, A′; V = (3√3/2)a²h | (√3/4)a²h).
   Người dùng duyệt; không mở việc mới trong lượt này.

## Kết quả LOCAL (2026-10-10, Windows, 0 lượt gọi model)

- Nhận nhánh: `feat/g05-regular-prisms` = `9148450d` khớp `origin`, 6 commit trên `ea85216b` (= `main` = `origin/main`).
  Product commit thực tế **`d8b9da74`** (commit cuối chạm `backend/app`; `00770c34` + sửa `d8b9da74`). Sản phẩm đổi
  `shape_constraint.py`, `assumption_gate.py`, `product_capability.py`, `main.py` (cache) + khoá danh tính + ghim test; 0 file
  kernel, compiler, prompt, thẻ văn phạm, lược đồ, `routing.py`, frontend. Không sửa mã sản phẩm LOCAL.
- Thiết kế T12 (đọc mã): nằm trong `_khuon_lang_tru` (một nhánh, không engine thứ hai, không solver); tịnh tiến từng đỉnh
  trên (affine), cạnh bên ⊥ MỌI cạnh đáy, đáy đều (k = 3: ba cạnh bằng nhau; k = 6: đối xứng tâm O = A + C − B và
  AB = BC = CD — đủ cho lục giác đều), cạnh đáy, chiều cao — tất cả THEO METRIC; kích thước chỉ từ đề (`kich_thuoc_t12`,
  một thẩm quyền cho khuôn và metric); cặp cạnh bên A–A′… lấy từ ký hiệu `ABC.A′B′C′` của ĐỀ, không từ thứ tự mặt;
  `solid_topology` chỉ là vũ trụ đỉnh của grounding (không vào khuôn); không ID ca.

### A. Bằng chứng năng lực

- Probe nhãn + probe ngoài nhãn chạy lại trên `ea85216b` và nhánh — bốn log TRÙNG BYTE log Cloud (bỏ CR). 13 refused → served
  đúng oracle, C1 (X1–X7, T1–T6: nguyên, phân số 1/2 và 2/3, căn √3 và 2√3, đổi tên MNPQRS/MNP.QRS, ba lối viết);
  12 refused → refused giữ nguyên chặng/lý do (thiếu chiều cao, chiều cao ≠ cạnh bên, đáy chương trình không đều, mặt trên
  không tịnh tiến, phủ định, mệnh đề chứng minh, ngũ giác, lăng trụ xiên, đề không nói "đều").
- Toán độc lập (`diagnostics/local_verification/prism_independent.py`, không import sản phẩm, KHÁC cách dựng của sản phẩm):
  dựng lăng trụ đều EUCLID THẬT cạnh b, cao h, kéo tích vô hướng cơ sở e1 = B−A, e2 = C−A, e3 = A′−A về khung affine của
  chương trình — mọi hàng phục vụ: cạnh đáy và cạnh mặt trên² = b², mặt trên tịnh tiến, cạnh bên ⊥ mọi cạnh đáy, |AA′|² = h²,
  V² = (diện tích khung · cao khung)² · det G = công thức sách ((3√3/2)b²h)² | ((√3/4)b²h)² = nhãn; và G TRÙNG CHÍNH XÁC
  `chart_metric` của cảnh sản phẩm — **ALL_OK** (X1 18√3, X2 18√3, X3 3√3, X4 9√3, X5 3√3/2, X6 18√3, X7 18√3, T1–T3 3√3,
  T4 3√3, T5 √3, T6 4√3).
- C0 (`probe_extra.py`, hai cây): toạ độ khớp đề ⇒ phục vụ 9 (lục giác trên x + y + z = 0 cạnh √2, cao √3) và 3/2 (tam giác
  (1,0,0),(0,1,0),(0,0,1)); 6 đề `main` từng PHỤC VỤ nay từ chối `SOURCE_SHAPE_CONTRADICTS_COORDINATES` (cạnh bên không ⊥ đáy,
  cạnh bên hoặc cạnh đáy đề nói trái toạ độ — lục giác và tam giác). `run_pipeline` (`prism_envelopes.py`): cả 6 envelope
  `unsupported`, không Scene3D, mang mã ấy, đúng 1 lượt gọi chặng chương trình (không vòng sửa LLM).
- Bộ đọc (`prism_reader_probe.py`, hai cây): "lăng trụ xiên tam/lục giác đều" và "lăng trụ xiên … đáy là tam giác đều" không
  phát `right_prism`/đáy đều (T12 không áp; "đều" của danh từ xiên để CHƯA ĐỌC ⇒ fail-closed); "lăng trụ đứng tam/lục giác
  đều" đọc trọn; sai số đỉnh ("tam giác đều ABCD.…"), phủ định sau, mệnh đề chứng minh: không phát khẳng định lăng trụ đều.
  Route (`prism_phrasing_route_probe.py`, hai cây, chương trình lưới của corpus): "hình lăng trụ đứng tam giác đều" mới phục
  vụ C1 V = 3√3 (đúng); "lăng trụ tam giác đều" không "hình", "xiên tam/lục giác đều", phủ định sau: từ chối trên cả hai cây.
- **Ghim bộ đọc đổi sang "lăng trụ đứng tứ giác đều"** (`test_shape_constraint.py::test_thong_tin_bi_bo_trong_span_tinh_la_chua_doc`):
  test khoá TÍNH CHẤT an toàn "thông tin bị bỏ trong span đã đọc tính là chưa đọc" (⇒ cổng không kết luận đề đọc trọn). Ghim
  cũ (tam giác đều) đỏ đúng vì T12 nay đọc "đều" ấy; ghim mới dùng "lăng trụ đứng tứ giác đều" — khẳng định hình học ĐÚNG
  (lăng trụ đứng đáy vuông), bộ đọc chưa đọc "đều" của tứ giác nên span vẫn để lại "đều" chưa đọc: test chỉ khoá GIỚI HẠN
  NĂNG LỰC fail-closed, không mã hoá luật toán sai, không phải dữ liệu tiện cho xanh. Giới hạn ghi: "lăng trụ (đứng) tứ giác
  đều X.Y" chưa được đọc như lăng trụ đều (đường T6 "đáy là hình vuông" sẵn có).
- **Phát hiện LOCAL ngoài nhãn** (`pyramid_hex_base_probe.py`, hai cây): `_DAY` nay đọc "đáy là lục giác đều" cả cho CHÓP.
  C1 (khung lưới, SA ⊥ đáy): vẫn từ chối trên cả hai cây — không năng lực mới ngoài phạm vi. C0: toạ độ khớp vẫn phục vụ
  V = 3; 2 đề `main` PHỤC VỤ (cạnh đáy đề nói trái toạ độ; đáy toạ độ không đều — `main` trả V = 4) nay từ chối
  `SOURCE_SHAPE_CONTRADICTS_COORDINATES` — đúng chiều an toàn, cùng cơ chế, thuộc bump 125.

### B. Bằng chứng kỹ thuật

- Scene3D (`prism_scene_dump.py`): 13/13 — 1 khối; lục giác 12 đỉnh / 8 mặt (2 lục giác + 6 tứ giác) / 18 cạnh, tam giác
  6 / 5 (2 tam giác + 3 tứ giác) / 9; Euler 2; mỗi cạnh thuộc đúng hai mặt; định hướng nhất quán ĐƯỢC (kiểm lật BFS độc lập —
  chương trình kiểu mô hình khai mặt đáy và mặt bên cùng chiều; kernel tự định hướng lại theo thiết kế `section.py`, lưới vẽ
  `DoubleSide`); không mặt suy biến; có `chart_metric` — **SCENE_OK**.
- Renderer — mức biến đổi (`prism_render_check.ts`, chính `veKhongGian` của frontend bundle bằng esbuild có sẵn, không sửa
  frontend): hình thế giới là đa giác đều cạnh b (bán kính ngoại tiếp b | b/√3), hai đáy phẳng, tịnh tiến, cạnh bên ⊥ đáy
  (|cos| = 1), cao h — **RENDER_TRANSFORM_OK** 13/13, gồm X4 (√3), T4 (2√3), X5 (1/2), T5 (2/3). Tiêm lỗi: bỏ `chart_metric`
  của X1 ⇒ cạnh √2…1 ⇒ `RENDER_TRANSFORM_FAILED` (`prism_render_check_injection.log`).
- Renderer — mức hình thật: `openFixture` có sẵn (`compiler-scene-suite.mjs`) trên `vite preview` của bản build mới, envelope
  thật từ `run_pipeline` (mô hình thay bằng chương trình corpus): X4 (lục giác, cạnh √3), X5 (lục giác, cạnh 1/2),
  T1 (tam giác), T5 (tam giác, cạnh 2/3) ở bước 5/5 vẽ đúng lăng trụ đều, hai đáy song song bằng nhau, cạnh bên thẳng ⊥ đáy,
  cạnh khuất nét đứt, tỉ lệ cao/cạnh đúng (X5 8:1, T5 13,5:1) — ảnh `diagnostics/local_verification/*.png`. Quan sát: ở hai
  khối rất mảnh (X5, T5) vài nhãn đỉnh bị ẩn/chồng (X5: B, E; T5: B′, C′, C) — trình bày nhãn, không phải hình học; frontend
  đóng băng. Vị trí chữ đáp số trên giao diện không được kiểm trong lượt này.
- Hồi quy (hai cây, trùng byte): C1 chóp đều 235 dòng (gồm Policy A), C0 c0-whole-solid-grounding 29 + reader gap 3,
  c0-whole-solid-reader 27, unnamed-regular-pyramid-grounding 11, general-polygon-base C0 6, chóp lục giác đều 17,
  unnamed-pyramid-vertex-binding 21. Mười oracle lịch sử OK. Tier-A sinh lại trên hai cây: 49/49 trùng (14 phục vụ, 0 đổi),
  manifest trùng.
- `CACHE_VERSION` 125: 6 + 2 đề C0 served → refused tái hiện; 13 + 3 refused → served chưa từng được cache; `_cache_lookup`
  trượt hàng `policy_version` khác; `lock_cache_identity.py --verify` khớp 125 (môi trường b1714b56… không đổi); 0 file bề
  mặt mô hình đổi; 7 chỗ ghim = 125.
- Đóng băng MỘT lần tại `9148450d` (worktree tách rời sạch): **`93077b51d033c198bfb68504e3517f98cb2f9738886f058e687f3562d4520883`**
  (102 file, product `d8b9da74`, cache 125; taxonomy, primitive set, schema không đổi; `--verify` khớp —
  `diagnostics/freeze_d8b9da74.log`); năm đỏ danh tính (`test_C2b`, `test_cache_version_khop_nguon`,
  `test_ma_san_pham_khong_troi…`, `test_inv_20`, `test_inv_05`) hết; khai lệch `inputs/candidate_divergence.json` + log tích
  luỹ + `KHAI_LECH` + manifest Tier-A — commit `eaeedb38`.
- Test: 64/64 mới (`test_regular_prisms.py`); bộ liên quan (T7/T8/T11/T12, C0 §21–§27, C1, Policy A, chóp tam/tứ/lục giác
  đều, lăng trụ T3–T6/T9/T10, G04/G05, compiler lăng trụ, grounding, danh tính, tài liệu, `test_api`) 1453 passed + 4 đỏ danh
  tính trước đóng băng ⇒ sau đóng băng 132/132 ở năm tệp danh tính; node harness 102/102.
- T3 một lần tại `eaeedb38` (worktree tách rời sạch): **`FULL_PRODUCT_GATE_PASS`** — pytest 7729 passed / 1 skipped /
  2 deselected (= 7665 + 64 mới), vitest 1040/1040, typecheck + build, demo 5/5, bề mặt sập 6/6 (0 lỗi 500)
  (`diagnostics/t3_eaeedb38.log`). T3 không chụp hình; kiểm hình thật ở mục trên.

### Giới hạn

`foundation_only`: route kiểm trên chương trình kiểu mô hình, chưa đo Gemini thật; compiler KHÔNG có họ lăng trụ đều; chưa hỗ
trợ: lăng trụ/chóp đều không tên, lăng trụ xiên đáy đều, "lăng trụ (đứng) tứ giác đều X.Y" như lăng trụ đều, "lăng trụ tam
giác đều X.Y" không có "hình/khối" phía trước (danh từ không đọc ⇒ từ chối), ngũ giác đều, đáy theo góc, đáy lõm. Không tuyên
bố giảm token, không tuyên bố năng lực Gemini thật tăng dựa riêng trên corpus chương trình viết tay. Chưa merge `main`, không
PR, không xoá nhánh, không bắt đầu lát kế tiếp — chờ người dùng phê duyệt.
