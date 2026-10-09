# c0-whole-solid-grounding — bàn giao cho LOCAL

Nhánh `fix/c0-whole-solid-grounding` (từ `9762f441`), đã push; không merge, không PR.

| commit | nội dung |
|---|---|
| `3bbd8c2` | tiền đăng ký: plan, 28 nhãn, oracle, amendment §22, probe baseline |
| `139aa1a` | hàng `edge_all` (kind đã đăng ký, thiếu nhãn) + probe baseline của nó — trước mọi sửa sản phẩm |
| `c11e8c9` | sửa C0 (§22), `CACHE_VERSION` 120, khoá danh tính, test, ghim |
| (commit cuối) | report, handoff, bằng chứng cache, so sánh pytest, OPEN_ISSUES, CODE_INDEX, CURRENT_STATE, ROADMAP |

## Việc LOCAL

1. Toàn bộ pytest + T3 `full-gate.mjs` trên worktree sạch của nhánh.
2. Đóng băng lại candidate MỘT lần (`backend/scripts/freeze_evaluation_candidate.py` — không có `--help`) theo thủ tục của
   run trước. Các test danh tính candidate đỏ tới khi làm bước này (`results/pytest_compare.json` `new_red`). Không sửa
   hash tay.
3. Kiểm độc lập bump 120 (`cache/decision.json`, `diagnostics/probe_9762f441*.log` ↔ `diagnostics/probe_c11e8c9.log`).
4. Người dùng duyệt; không mở việc mới trong lượt này.

## Kết quả LOCAL (2026-10-09, Windows, 0 lượt gọi model)

- Nhận nhánh: `fix/c0-whole-solid-grounding` = `825f109d` khớp `origin`, đúng 5 commit Cloud trên `9762f441`; sản phẩm
  chỉ đổi `assumption_gate.py` + `main.py` (cache 120) + khoá danh tính; không sửa mã sản phẩm LOCAL.
- Review §22: định nghĩa chính xác đúng toán (lăng trụ đứng: v ∥ vectơ diện tích đáy; xiên: tịnh tiến, v ∦; chóp đều:
  đỉnh trên pháp tuyến tại trọng tâm đáy; chiều cao = khoảng cách² tới mặt đáy, không phải cạnh bên); `base_centre` chỉ
  phát cho chóp đều (tâm = trọng tâm, không mơ hồ); khối không tên / thiếu số đo / điểm không toạ độ ⇒ không kiểm.
- Chạy lại nhãn trên `9762f441` và trên nhánh: 29/29 khớp; **15** hàng served → refused (báo cáo Cloud và
  `cache/decision.json` ghi 16 — đếm nhầm: 3 trong 18 hàng `refused` đã bị từ chối sẵn trên `main`: `RSP_C_centre_off`,
  `P_C_prism_top_not_translate`, `RT_C_tetrahedron_not_regular` qua §21); 11 hàng nhất quán phục vụ trên cả hai; 0 hồi quy.
  Đính chính này không đổi quyết định cache (≥ 1 hàng served → refused là đủ).
- Ca biên LOCAL: độ dài căn nhất quán (cạnh bên √11, trung đoạn √10) phục vụ, mâu thuẫn (2√3) từ chối; "chiều cao bằng √11"
  (= cạnh bên) từ chối, "chiều cao bằng 3" phục vụ; ký hiệu `a` không được đọc (không phải mâu thuẫn); mệnh đề "Chứng minh …
  là hình chóp tứ giác đều", câu hỏi và phủ định "không phải hình lập phương" không thành tiền đề.
- `ISSUE-ARCH-C0-WHOLE-SOLID-CLAIMS-NOT-READ`: 3/3 tái hiện trên nhánh VÀ `main` (có sẵn, không phải hồi quy). Cả ba là lỗ
  BỘ ĐỌC (không phát khẳng định chóp đều ⇒ checker không được gọi), không phải checker kiểm sai — cùng toạ độ, viết
  "hình chóp tứ giác đều S.ABCD" thì bị từ chối. Giữ OPEN: an toàn C0 toàn khối chưa trọn với các cách viết ấy.
- `CACHE_VERSION` 120 kiểm độc lập: served → refused tái hiện; `_cache_lookup` trượt hàng `policy_version` khác;
  `lock_cache_identity.py --verify` khớp 120; 0 file bề mặt mô hình đổi; mọi chỗ ghim = 120; `fixture_diff` 49/49 trùng.
- Đóng băng MỘT lần tại `825f109d` (worktree tách rời sạch): **`8c4c0128…`** (102 file, product `c11e8c9d`, cache 120;
  `--verify` khớp — `diagnostics/freeze_c11e8c9d.log`). Năm đỏ danh tính (candidate ghi 119 + mã cũ) hết nhờ đóng băng;
  lớp khai lệch `inputs/candidate_divergence.json`, log tích luỹ (`cache_version_hien_tai` 120), `KHAI_LECH`, manifest
  Tier-A — commit `d838cc5b`.
- Test: C0 toàn khối 34/34 + oracle; grounding-safety 24/24; G04 51/51, G05 53/53; hồi quy + danh tính + tài liệu +
  `test_api` 1314/1314; node harness 102/102.
- T3 một lần tại `d838cc5b`: **`FULL_PRODUCT_GATE_PASS`** — pytest 7401 passed / 1 skipped / 2 deselected, vitest
  1040/1040, build, demo, bề mặt sập; cây sạch sau gate (`diagnostics/t3_d838cc5b.log`).
- Giới hạn giữ nguyên: `LLM_ONLY` mặc định; compiler opt-in; chưa đo Gemini thật; không tuyên bố giảm token.
- Chưa merge `main`, không PR, không xoá nhánh — chờ người dùng phê duyệt.
