# c0-whole-solid-reader — bàn giao cho LOCAL

Nhánh `fix/c0-whole-solid-reader` (từ `a1350da3`), đã push; không merge, không PR.

| commit | nội dung |
|---|---|
| `3660523` | tiền đăng ký: plan, 27 nhãn C0, luật tương đương C1, oracle, probe baseline C0 + C1 |
| `7d55153` | bộ đọc (hai lối viết chóp đều, phủ định), `CACHE_VERSION` 121, khoá danh tính, test, ghim |
| (commit cuối) | report, handoff, bằng chứng cache, so sánh pytest, probe candidate, OPEN_ISSUES, CODE_INDEX, CURRENT_STATE, ROADMAP, amendment §23 |

## Việc LOCAL

1. Toàn bộ pytest + T3 `full-gate.mjs` trên worktree sạch của nhánh.
2. Đóng băng lại candidate MỘT lần (`backend/scripts/freeze_evaluation_candidate.py` — không có `--help`) theo thủ tục của
   run trước — mã sản phẩm đổi (`shape_constraint.py`, `main.py`). Các test danh tính candidate đỏ tới khi làm bước này
   (`results/pytest_compare.json` `new_red`). Không sửa hash tay.
3. Kiểm độc lập bump 121 (`cache/decision.json`; `diagnostics/probe_a1350da3.log` ↔ `probe_candidate.log`,
   `probe_c1_equivalence_a1350da3.log` ↔ `probe_c1_equivalence_candidate.log`).
4. Người dùng duyệt; quyết định về chóp đều không tên (`ISSUE-ARCH-UNNAMED-REGULAR-PYRAMID-OUTSIDE-REFUSAL-ZONE`) là
   việc riêng; không mở việc mới trong lượt này.

## Kết quả LOCAL (2026-10-09, Windows, 0 lượt gọi model)

- Nhận nhánh: `fix/c0-whole-solid-reader` = `b47945e8` khớp `origin`, đúng 4 commit Cloud trên `a1350da3`. Sản phẩm chỉ
  đổi `shape_constraint.py` (bộ đọc) + `main.py` (cache 121) + khoá danh tính + ghim test; KHÔNG đổi cổng giả định, route,
  compiler, khuôn C1, frontend. Không sửa mã sản phẩm LOCAL.
- Review bộ đọc: hai lối viết phát ĐÚNG các kind sẵn có (`pyramid`, `regular_*_pyramid`, `base_*`) qua cùng nhóm
  `dinh`/`day`; "chóp đều" lấy loại theo số đỉnh đáy; phủ định "không phải (là)" chặn khẳng định chóp đều; không logic
  hình học, không tên đỉnh cố định.
- **C0:** chạy lại `probe.py` trên `a1350da3` và nhánh — log TRÙNG BYTE log Cloud; oracle 27/27. Chuyển trạng thái: 10
  served → refused (`SOURCE_SHAPE_CONTRADICTS_COORDINATES`), 1 refused → served (phủ định ký hiệu chuẩn), 16 giữ nguyên;
  bộ đọc gắn đúng đỉnh đổi tên, dạng "là … ,", tam giác, khối sau toạ độ, hai khối; mục tiêu/phủ định không thành tiền đề;
  chóp không "đều"/không tên không bị bịa khẳng định (hàng P2 nhãn `baseline`, giống `main`).
- **C1 (trọng tâm):** chạy lại `probe_c1_equivalence.py` trên `a1350da3` và nhánh — log TRÙNG BYTE log Cloud. Đối chiếu
  NHÃN CORPUS ĐỘC LẬP (`expect` của hai corpus chóp đều, có wildcard): chuẩn + hai lối viết × 47 hàng = 141/141 khớp. Mỗi
  lối viết: 24 refused → served — giá trị BẰNG nhãn corpus (không chỉ bằng ký hiệu chuẩn); 1 served → refused =
  `square/N5_apex_over_vertex`: đề nhất quán nhưng chương trình dựng chóp KHÔNG đều, `main` phục vụ SA = 3 (sai, đúng là
  √17), nhãn đòi từ chối ⇒ từ chối đúng, không phải từ chối oan; 20 refused → refused đúng lý do nhãn; 2 served → served.
  Hàng ký hiệu chuẩn không đổi; kết cục lối viết mới == chuẩn 94/94.
- **Chóp đều không tên:** tính lại từ log LOCAL: 47 hàng, 37 phục vụ — 22 đúng nhãn, 4 khác giá trị, 11 nhãn đòi từ chối —
  TRÙNG HỆT trên `main` và nhánh ⇒ có sẵn, không đổi. Không sửa (nới vùng từ chối đơn thuần sẽ từ chối oan 22 đề đúng; không
  bịa gắn đỉnh/đáy). `ISSUE-ARCH-C0-WHOLE-SOLID-CLAIMS-NOT-READ` (thu hẹp) và
  `ISSUE-ARCH-UNNAMED-REGULAR-PYRAMID-OUTSIDE-REFUSAL-ZONE` giữ OPEN.
- `CACHE_VERSION` 121 kiểm độc lập: served → refused tái hiện (C0 10 hàng + C1 N5 đáp số sai); refused → served chưa từng
  được cache; `_cache_lookup` trượt hàng `policy_version` khác; `lock_cache_identity.py --verify` khớp 121; 0 file bề mặt
  mô hình đổi; mọi chỗ ghim = 121; `fixture_diff` 49/49 trùng.
- Đóng băng MỘT lần tại `b47945e8` (worktree tách rời sạch): **`c3f83399…`** (102 file, product `7d551535`, cache 121;
  `--verify` khớp — `diagnostics/freeze_7d551535.log`). Năm đỏ danh tính (candidate ghi 120 + mã cũ) hết nhờ đóng băng;
  lớp khai lệch `inputs/candidate_divergence.json`, log tích luỹ (`cache_version_hien_tai` 121), `KHAI_LECH`, manifest
  Tier-A — commit `1396878e`.
- Test: bộ đọc 129/129 + oracle 27/27; C0 §21/§22, khuôn C1 chóp đều, G04, G05, compiler, hồi quy, danh tính, tài liệu,
  `test_api` 1485/1485; node harness 102/102.
- T3 một lần tại `1396878e`: **`FULL_PRODUCT_GATE_PASS`** — pytest 7530 passed / 1 skipped / 2 deselected, vitest
  1040/1040, build, demo, bề mặt sập; cây sạch sau gate (`diagnostics/t3_1396878e.log`).
- Giới hạn giữ nguyên: `LLM_ONLY` mặc định; compiler opt-in; chưa đo Gemini thật; không tuyên bố giảm token.
- Chưa merge `main`, không PR, không xoá nhánh — chờ người dùng phê duyệt.
