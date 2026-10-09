# unnamed-pyramid-vertex-binding — bàn giao cho LOCAL

Nhánh `fix/unnamed-pyramid-vertex-binding` (từ `a7c56942`), đã push; không merge, không PR.

| commit | nội dung |
|---|---|
| `9f9e66d`, `07afbd4` | nghiên cứu phương án B: nhãn toán học, oracle, probe khả thi ⇒ `ARCHITECTURE_DECISION_REQUIRED` |
| `1bb5c02` | nhãn chính sách A (`policy_a_labels.json`) — trước commit sản phẩm |
| `5669292` | chính sách A (§25): vùng U3 + lý do của cổng, `CACHE_VERSION` 123, khoá, test, ghim |
| (commit cuối) | report, handoff, plan §4, bằng chứng cache, so sánh pytest, chuyển trạng thái, OPEN_ISSUES, CODE_INDEX, CURRENT_STATE, ROADMAP |

## Việc LOCAL

1. Toàn bộ pytest + T3 `full-gate.mjs` trên worktree sạch của nhánh.
2. Đóng băng lại candidate MỘT lần (`backend/scripts/freeze_evaluation_candidate.py` — không có `--help`) — mã sản phẩm
   đổi (`shape_constraint.py`, `assumption_gate.py`, `main.py`). Năm test danh tính candidate đỏ tới bước này
   (`results/pytest_compare.json` `new_red`). Không sửa hash tay.
3. Kiểm độc lập bump 123 (`cache/decision.json`; `diagnostics/probe_c1_variants_a7c56942.log` ↔
   `probe_c1_variants_candidate.log`).
4. Người dùng duyệt tích hợp. Sau đó: quay lại G05 (ROADMAP); phương án B là nâng cấp tuỳ chọn, không mở trong lượt này.

## Kết quả LOCAL (2026-10-09, Windows, 0 lượt gọi model)

- Nhận nhánh: `fix/unnamed-pyramid-vertex-binding` = `1258bbcd` khớp `origin`, 6 commit trên `a7c56942` (2 nghiên cứu (b)
  + 4 chính sách A). Product commit thực tế `56692926` (= `5669292` Cloud báo). Sản phẩm chỉ đổi `neu_khoi_da_dien`,
  `_nhan_khuon` và `CACHE_VERSION`; không parser/kernel/solver/compiler/khuôn mới, không dùng `solid_topology`, không logic
  theo ID ca, không đoán tên đỉnh, không dùng `SOURCE_SHAPE_CONTRADICTS_COORDINATES` cho đề chỉ thiếu gắn đỉnh. Không sửa
  mã sản phẩm LOCAL.
- Chạy lại probe C1 trên `a7c56942` và nhánh — hai log TRÙNG BYTE log Cloud; probe C0 của ba run trước (29 + 27 + 11 hàng)
  TRÙNG BYTE `main` ↔ nhánh.
- **21 đề chính sách A:** 21/21 từ chối. 12 served → refused, tất cả `assumption` / `ASSUMPTION_INVARIANCE_UNPROVEN` — gồm
  `N5` (không còn SA = 3), `R2_N9` (không còn phục vụ SA = 3, SB = 5), `W5_C` (không còn thể tích 16/3); 9 refused → refused
  giữ đúng chặng/lý do đã đăng ký (cột `baseline_a7c56942` khớp `main` cả 21 hàng). Không đáp số, không Scene3D (test
  `run_pipeline`), không vòng sửa LLM (`ASSUMPTION_INVARIANCE_UNPROVEN` thuộc tập không gửi sửa).
- **5 đề GIỚI HẠN NĂNG LỰC** — tính lại tay từ chính đề, đều xác định: S5 (a = 4, h = 3 ⇒ SA = √17), S7 (AB = 4, SO = 3 là
  chiều cao ⇒ V = 16), R2_S9 (a = 4, SA = 3 ⇒ h = 1 ⇒ V = 16/3), P9 (a = 3√2, SG = √3 ⇒ V = 9/2), P11 (a = 3√2, h = √3 ⇒
  SA = 3). `main` phục vụ đúng các giá trị này; chính sách A từ chối chúng vì chưa có cơ chế gắn đỉnh được chứng nhận — KHÔNG
  phải vì đề sai. Nhãn toán học + oracle không đổi kể từ `07afbd44` (oracle 21/21).
- **Không từ chối oan ngoài phạm vi:** 15 dòng C1 đổi = 12 hàng chính sách + 3 hàng biến thể `unnamed` có văn bản TRÙNG hàng
  đăng ký (N5, S5, P11); 26 hàng gắn được, ký hiệu chuẩn, hai lối viết run bộ đọc: 0 đổi; C0 29 + 27 + 11 hàng không đổi.
- `CACHE_VERSION` 123 kiểm độc lập: 12 served → refused tái hiện; `_cache_lookup` trượt hàng `policy_version` khác;
  `lock_cache_identity.py --verify` khớp 123; 0 file bề mặt mô hình đổi; 7 chỗ ghim = 123; `fixture_diff` 49/49 trùng.
- Đóng băng MỘT lần tại `1258bbcd` (worktree tách rời sạch): **`b13a3ef1…`** (102 file, product `56692926`, cache 123;
  `--verify` khớp — `diagnostics/freeze_56692926.log`). Năm đỏ danh tính (candidate ghi 122 + mã cũ) hết nhờ đóng băng;
  lớp khai lệch, log tích luỹ (`cache_version_hien_tai` 123), `KHAI_LECH`, manifest Tier-A — commit `39b0fb4a`.
- Test: mới + cập nhật 97/97; C0 §21–§24, C1 T7/T8, G04, G05, compiler, hồi quy, danh tính, tài liệu, `test_api`
  1582/1582; bốn oracle OK; node harness 102/102.
- T3 một lần tại `39b0fb4a`: **`FULL_PRODUCT_GATE_PASS`** — pytest 7627 passed / 1 skipped / 2 deselected, vitest
  1040/1040, build, demo, bề mặt sập; cây sạch sau gate (`diagnostics/t3_39b0fb4a.log`).
- Ghi nhận: giảm thiểu an toàn của chính sách A ĐÃ KIỂM CHỨNG trong phạm vi 21 đề; 5 đề do đề xác định CHƯA HỖ TRỢ; phương án
  B là nâng cấp năng lực HOÃN (bằng chứng nghiên cứu giữ nguyên). Không tuyên bố hệ giải được 21 bài, không tuyên bố C0 an
  toàn với mọi loại bài; 0 Gemini live; chưa chứng minh tiết kiệm token.
- Chưa merge `main`, không PR, không xoá nhánh; G05 chưa bắt đầu — chờ người dùng phê duyệt.
