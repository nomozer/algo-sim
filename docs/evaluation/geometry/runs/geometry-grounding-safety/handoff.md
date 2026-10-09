# geometry-grounding-safety — bàn giao cho LOCAL

Nhánh `fix/geometry-grounding-safety` (từ `e6c3cf68`), đã push; không merge, không PR.

| commit | nội dung |
|---|---|
| `17353c3` | tiền đăng ký: plan, labels, oracle, amendment §21 |
| `fbade46` | sửa C0 + compiler, `CACHE_VERSION` 119, test, đính chính nhãn R06, bằng chứng cache |
| (commit cuối) | report, handoff, OPEN_ISSUES (hai issue RESOLVED), CODE_INDEX, CURRENT_STATE, ROADMAP |

## Việc LOCAL

1. Toàn bộ pytest + T3 `full-gate.mjs` trên worktree sạch của nhánh.
2. Đóng băng lại candidate MỘT lần (`backend/scripts/freeze_evaluation_candidate.py` — không có `--help`) theo thủ tục của
   hai run trước (`inputs/candidate_divergence.json`, `KHAI_LECH`, manifest Tier-A). Năm test danh tính đỏ tới khi làm
   bước này (gồm `test_cache_version_khop_nguon`: candidate ghi 118). Không sửa hash tay.
3. Kiểm độc lập bump 119 (`cache/decision.json`, hai log probe).
4. Người dùng duyệt; không mở việc mới trong lượt này.

## Kết quả LOCAL (2026-10-09, Windows, 0 lượt gọi model)

- Nhận nhánh: `fix/geometry-grounding-safety` = `175510c4` khớp `origin`, đúng 3 commit Cloud trên `e6c3cf68`; sản phẩm
  chỉ đổi 7 file `backend/app` đã khai + khoá danh tính cache.
- **Lỗi A (C0):** kiểm qua route thật — mâu thuẫn trên điểm chương trình dùng bị từ chối `SOURCE_SHAPE_CONTRADICTS_COORDINATES`
  (không Scene3D qua `run_pipeline`, test Cloud); đề nhất quán, mệnh đề mục tiêu ("Chứng minh…", câu hỏi) và câu phủ định
  ("không vuông góc") vẫn phục vụ — không từ chối oan. **Lỗ tìm thấy:** quan hệ có điểm chương trình KHÔNG khai bị bỏ qua
  ⇒ `E(5;5;0)` + "AE vuông góc với AB" (đề tự mâu thuẫn kiểm chứng được) vẫn phục vụ. **Sửa LOCAL `765291ab`:** điểm vắng
  lấy toạ độ CHÍNH ĐỀ cho (`point_coordinate`); điểm không toạ độ ở đâu vẫn bỏ qua. 3 test (mâu thuẫn / nhất quán / không
  toạ độ); tiêm lỗi (bỏ phần lấy toạ độ đề) ⇒ ca mâu thuẫn đỏ. Không mở rộng kind: ràng buộc toàn khối vẫn chưa kiểm —
  `ISSUE-ARCH-C0-WHOLE-SOLID-RELATIONS-NOT-CHECKED` (OPEN, mới).
- **Lỗi B (compiler):** một góc vuông ⇒ `FALLBACK_TO_LLM / BASE_RECTANGLE_NOT_PROVEN` (chóp, lăng trụ, có/không cụm "góc
  BAD vuông"); 3 góc vuông, chữ nhật khai, hộp khai, hình thang G05 vẫn đúng (test Cloud). Ép quy tắc compiler mở ⇒ cổng
  giả định vẫn từ chối `ASSUMPTION_INVARIANCE_UNPROVEN` — hai lớp chặn, không còn một.
- `CACHE_VERSION` 119 kiểm độc lập: served → refused (probe trước/sau); `_cache_lookup` trượt mọi hàng `policy_version`
  khác (khoá bởi `test_api` + test ghi đè sau bump); `lock_cache_identity.py --verify` khớp 119; 0 file bề mặt mô hình đổi;
  mọi chỗ ghim phiên bản = 119. Bổ sung LOCAL thêm ca served → refused trong cùng bump (119 chưa phát hành).
- Đóng băng MỘT lần tại `765291ab` (worktree tách rời sạch): **`bbfa5b0d…`** (102 file, cache 119; `--verify` khớp —
  `diagnostics/freeze_765291ab.log`). Năm đỏ danh tính (`test_C2b`, `test_cache_version_khop_nguon`,
  `test_ma_san_pham_khong_troi…`, `test_inv_20`, `test_inv_05`) — candidate ghi 118 + mã cũ — hết nhờ đóng băng; lớp khai
  lệch `inputs/candidate_divergence.json`, log tích luỹ (`cache_version_hien_tai` 119), `KHAI_LECH`, manifest Tier-A —
  commit `e1dfc851`.
- Test: grounding-safety 24/24 + oracle OK; G04 51/51, G05 53/53; hồi quy + danh tính + tài liệu + `test_api` 1229/1229;
  node harness 102/102.
- T3 một lần tại `e1dfc851`: **`FULL_PRODUCT_GATE_PASS`** — pytest 7367 passed / 1 skipped / 2 deselected, vitest 1040/1040,
  build, demo, bề mặt sập; cây sạch sau gate (`diagnostics/t3_e1dfc851.log`).
- Giới hạn giữ nguyên: `LLM_ONLY` mặc định; compiler opt-in; chưa đo Gemini thật; không tuyên bố giảm token.
- Chưa merge `main`, không PR — chờ người dùng phê duyệt.
