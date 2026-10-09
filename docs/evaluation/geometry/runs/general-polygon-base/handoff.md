# general-polygon-base — bàn giao cho LOCAL

Nhánh `feat/general-polygon-base` (rẽ từ `d5287ff7`), đã push lên `origin`; không merge, không PR. Đọc `report.md`.

| commit | nội dung |
|---|---|
| `5e1e3e9` | tiền đăng ký: `plan.md`, `labels.json`, `oracle.py`, amendment §20 — trước mọi thay đổi sản phẩm |
| `4e30a21` | sản phẩm + test: kernel chuỗi góc vuông, bộ đọc hình thang vuông, T10, họ compiler `polygon_base_*`, `product_capability` |
| (commit cuối) | CODE_INDEX, OPEN_ISSUES, quyết định cache, report, handoff, CURRENT_STATE, ROADMAP |

## Việc LOCAL (theo thứ tự)

1. Toàn bộ pytest + T3 (`full-gate.mjs`) trên worktree sạch của nhánh, so baseline local.
2. Đóng băng lại candidate MỘT lần (`backend/scripts/freeze_evaluation_candidate.py` — không có `--help`, gọi là ghi)
   và khai theo thủ tục của run oblique-prism (`inputs/candidate_divergence.json`, `KHAI_LECH`, manifest Tier-A) — bốn
   test danh tính đỏ tới khi làm bước này. Không sửa hash/test tay.
3. Kiểm độc lập quyết định `CACHE_VERSION` 118 (`cache/decision.json`).
4. Người dùng quyết tích hợp; không bắt đầu họ hình tiếp theo trong lượt này. Mục còn mở: `ISSUE-ARCH-G05-REMAINING-BASES`
   (đa giác toạ độ trên compiler là phần rẻ nhất — không đổi bề mặt mô hình), `ISSUE-ARCH-COMPILER-UNTAGGED-RECTANGLE-ASSUMPTION`.

## Kết quả LOCAL (2026-10-09, Windows, 0 lượt gọi model)

- Nhận nhánh: `feat/general-polygon-base` = `45d732f0` khớp `origin`, đúng 3 commit Cloud trên `d5287ff7`; sản phẩm chỉ
  đổi 5 file `backend/app` đã khai. Review kernel / bộ đọc / T10 / hai họ compiler — không sửa mã sản phẩm.
- `ISSUE-ARCH-COMPILER-UNTAGGED-RECTANGLE-ASSUMPTION` kiểm bằng chạy thật qua `run_pipeline` (`DETERMINISTIC_FIRST`):
  đáy tứ giác chỉ MỘT góc vuông (chóp, lăng trụ, có/không cụm "góc BAD vuông") ⇒ compiler chọn họ chữ nhật nhưng route
  từ chối `ASSUMPTION_INVARIANCE_UNPROVEN`, không Scene3D, không đáp số; đề nói "hình thang vuông" mà hợp đồng mất một
  góc vuông + một cạnh ⇒ `REFUSE GIVEN_FACT_WITHOUT_SOURCE`. Khoá bằng
  `test_mot_goc_vuong_khong_phuc_vu_hinh_chu_nhat_tu_gia_dinh` (commit `d3feb877`); tiêm lỗi (tắt cổng khối đa diện) ⇒
  cả hai ca `status: ok` ⇒ test đỏ — cổng giả định là rào duy nhất. Issue giữ OPEN (chặn compiler-first).
- Đóng băng candidate MỘT lần trong worktree tách rời sạch tại `d3feb877`: **`72d6070a…`** (102 file, product commit
  `4e30a211`; taxonomy / primitive set / schema không đổi; `--verify` khớp — `diagnostics/freeze_4e30a211.log`). Bốn đỏ
  danh tính của Cloud (`test_inv_20`, `test_inv_05`, `test_C2b`, `test_ma_san_pham_khong_troi…`) cùng một nguyên nhân —
  `product_commit_sha` + `measured_system.tree_hash` lệch — hết nhờ đóng băng; lớp khai lệch `inputs/candidate_divergence.json`
  (`corrects` lớp oblique-prism), log tích luỹ, `KHAI_LECH`, manifest Tier-A dời theo thủ tục — commit `f250f5ef`.
- `CACHE_VERSION` 118 kiểm độc lập: `lock_cache_identity.py --verify` khớp; 0 file bề mặt mô hình đổi từ `d5287ff7`;
  T10 chỉ chạy sau `TEMPLATE_NOT_MATCHED`; ca toạ độ C0 có cụm "hình thang vuông" cho kết quả route TRÙNG BYTE trước/sau
  (`d5287ff7` vs nhánh); họ compiler opt-in.
- Test đích: G05 53/53 (51 Cloud + 2 LOCAL), oracle độc lập OK; G04 51/51; hồi quy compiler/giả định/bộ đọc/kernel +
  danh tính + tài liệu 910/910; node harness 102/102.
- T3 một lần tại `f250f5ef` (worktree tách rời sạch, đường dẫn có dấu cách): **`FULL_PRODUCT_GATE_PASS`** — pytest 7343
  passed / 1 skipped / 2 deselected (G04: 7290; +53 test G05), vitest 67 file / 1040, build, demo, bề mặt sập; cây sạch
  sau gate (`diagnostics/t3_f250f5ef.log`). 131 đỏ + 4 lỗi môi trường Cloud không tái hiện LOCAL.
- Ghi nhận (có từ trước, không đổi bởi G05): ca C0 lấy toạ độ làm thẩm quyền; cụm hình dạng trái toạ độ (vd. "vuông tại
  C và D" với toạ độ vuông tại A, B) vẫn được phục vụ theo toạ độ ở cả `d5287ff7` lẫn nhánh.
- Giới hạn giữ nguyên: miền hẹp (đáy lồi theo chuỗi góc vuông); LLM_ONLY chỉ kiểm bằng chương trình kiểu mô hình viết
  tay (`foundation_only`); compiler opt-in, analyze giả lập trong test; không tuyên bố giảm token;
  `ISSUE-ARCH-G05-REMAINING-BASES` và `ISSUE-ARCH-COMPILER-UNTAGGED-RECTANGLE-ASSUMPTION` OPEN; không bật compiler-first.
- Chưa merge `main`, không PR, không xoá nhánh — chờ người dùng phê duyệt.
