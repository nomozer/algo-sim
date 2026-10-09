# unnamed-regular-pyramid-grounding — bàn giao cho LOCAL

Nhánh `fix/unnamed-regular-pyramid-grounding` (từ `ede8d329`), đã push; không merge, không PR.

| commit | nội dung |
|---|---|
| `94b2f89` | tiền đăng ký: plan, 47 hàng C1 + 11 hàng C0, oracle, probe baseline C0 + C1 |
| `12edf57` | bộ đọc (`()` cho chóp đều không tên), cổng (§24 gắn + kiểm), vùng U3, `formation`, `CACHE_VERSION` 122, khoá, test, ghim |
| (commit cuối) | oracle + nhân chứng nhập nhằng, report, handoff, bằng chứng cache, so sánh pytest, chuyển trạng thái, OPEN_ISSUES, CODE_INDEX, CURRENT_STATE, ROADMAP |

## Việc LOCAL

1. Toàn bộ pytest + T3 `full-gate.mjs` trên worktree sạch của nhánh.
2. Đóng băng lại candidate MỘT lần (`backend/scripts/freeze_evaluation_candidate.py` — không có `--help`) theo thủ tục
   hiện hành — mã sản phẩm đổi (`shape_constraint.py`, `assumption_gate.py`, `formation.py`, `main.py`). Các test danh tính
   candidate đỏ tới khi làm bước này (`results/pytest_compare.json` `new_red`). Không sửa hash tay.
3. Kiểm độc lập bump 122 (`cache/decision.json`; `diagnostics/probe_c0_ede8d329.log` ↔ `probe_c0_candidate.log`,
   `probe_c1_variants_ede8d329.log` ↔ `probe_c1_variants_candidate.log`).
4. Người dùng duyệt; quyết định kiến trúc cho 21 đề gọi tên điểm thiếu toạ độ (phương án a/b/c trong `report.md` §5 và
   `ISSUE-ARCH-UNNAMED-REGULAR-PYRAMID-OUTSIDE-REFUSAL-ZONE`) là việc riêng; không mở việc mới trong lượt này.

## Kết quả LOCAL (2026-10-09, Windows, 0 lượt gọi model)

- Nhận nhánh: `fix/unnamed-regular-pyramid-grounding` = `c29f69c7` khớp `origin`, đúng 4 commit Cloud trên `ede8d329`.
  Sản phẩm đổi `shape_constraint.py`, `assumption_gate.py`, `formation.py`, `main.py` (cache 122) + khoá danh tính + ghim
  test + một test đăng ký trước được cập nhật; KHÔNG đổi compiler, khuôn, mã từ chối, frontend. Không sửa mã sản phẩm LOCAL.
- Review thiết kế: gắn CHỈ khi `ten_diem_khong_toa_do(đề)` rỗng và chương trình dựng đúng một khối; ràng buộc gắn vào được
  KIỂM bằng khuôn/§22 sẵn có (không engine mới); `solid_topology` (đầu ra mô hình) không dùng; bộ đọc không đoán tên
  (khẳng định giữ `()`). Thứ tự mặt của chương trình: xoay danh sách mặt (mặt bên lên đầu) trên mọi hàng tam giác ⇒ 0 đổi.
- Chạy lại `probe_c1_equivalence.py` + `probe.py` trên `ede8d329` và nhánh — bốn log TRÙNG BYTE log Cloud.
- 47 hàng C1 theo nhóm (đối chiếu `labels.json` + nhãn corpus): gắn/đúng 13 giữ đúng; gắn/sai giá trị 4 → đúng, tính lại tay:
  `square/U3` (tam giác đều a = 3, h = 4) V = 3√3; `triangular/N5b` (a = 3√2, h = √3) V = 9/2; `triangular/U1` (a = 3,
  h = 2) V = 3√3/2; `triangular/U3` (a = 3√2, h = 2) V = 3√3; gắn/nhãn đòi từ chối 8 → từ chối đúng lý do, tính lại tay:
  thiếu chiều cao (square N1, triangular N1, N7, N9), trung đoạn phải là 5 ≠ 6 (square N3), cạnh bên phải là √10 ≠ 3
  (triangular N2), chiều cao √2 vô tỉ (square U1), dữ kiện góc 60° (square U2); gắn/đã từ chối 1 giữ; 21 không gắn TRÙNG
  HỆT `main`.
- C0 11/11: 3 mâu thuẫn không tên từ chối `SOURCE_SHAPE_CONTRADICTS_COORDINATES`; 6 nhất quán phục vụ C0 (kể cả chương trình
  lấy mặt khác làm đáy, phủ định, mệnh đề mục tiêu); điểm M thiếu toạ độ và hai khối không đổi — không từ chối oan mới.
- Lối viết khác (ký hiệu chuẩn, hai lối viết run trước, khối gọi tên ở câu hỏi): 0 đổi `main` → nhánh.
- Còn mở (tái hiện, KHÔNG sửa): `square/N5` (a = 4, h = 3 ⇒ SA = √17; phục vụ 3), `square/R2_N9` (chóp đều ⇒ SA = SB, đề cho
  3 và 5; phục vụ 16), `square/W5_C` (SA = SB = SC = SD không giá trị ⇒ chiều cao chưa xác định; phục vụ 16/3). Người dùng
  đã chọn phương án (b) cho 21 hàng ấy — lượt Cloud RIÊNG sau tích hợp: chỉ xét phép gán hữu hạn có căn cứ, không coi tên
  của chương trình là dữ kiện nguồn, mọi phép gán hợp lệ phải được kiểm, trùng đáp số không là bằng chứng duy nhất, không
  mở rộng thành bộ giải ràng buộc tổng quát khi chưa có phê duyệt mới.
- `CACHE_VERSION` 122 kiểm độc lập: 11 served → refused (8 C1 + 3 C0) và 4 đổi giá trị tái hiện; `_cache_lookup` trượt
  hàng `policy_version` khác; `lock_cache_identity.py --verify` khớp 122; 0 file bề mặt mô hình đổi; ghim = 122;
  `fixture_diff` 49/49 trùng.
- Đóng băng MỘT lần tại `c29f69c7` (worktree tách rời sạch): **`d07a92de…`** (102 file, product `12edf57a`, cache 122;
  `--verify` khớp — `diagnostics/freeze_12edf57a.log`). Năm đỏ danh tính (candidate ghi 121 + mã cũ) hết nhờ đóng băng;
  lớp khai lệch, log tích luỹ (`cache_version_hien_tai` 122), `KHAI_LECH`, manifest Tier-A — commit `97db084f`.
- Test: 72/72 + oracle (47 C1 + 11 C0); C0 §21–§23, C1, G04, G05, compiler, hồi quy, danh tính, tài liệu, `test_api`
  1557/1557; node harness 102/102.
- T3 một lần tại `97db084f`: **`FULL_PRODUCT_GATE_PASS`** — pytest 7602 passed / 1 skipped / 2 deselected, vitest
  1040/1040, build, demo, bề mặt sập; cây sạch sau gate (`diagnostics/t3_97db084f.log`).
- Giới hạn giữ nguyên: `LLM_ONLY` mặc định; compiler opt-in; chưa đo Gemini thật; không tuyên bố giảm token; KHÔNG tuyên bố
  47/47 đã giải quyết.
- Chưa merge `main`, không PR, không xoá nhánh — chờ người dùng phê duyệt.
