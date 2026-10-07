# HANDOFF — regular-triangular-pyramid-w01

```text
TASK_SLUG             = regular-triangular-pyramid
RUN_ID                = regular-triangular-pyramid-w01 (REGULAR_TRIANGULAR_PYRAMID_AND_TETRAHEDRON_SLICE)
BRANCH                = feat/regular-square-pyramid (local; giữ theo lệnh người dùng; chưa push)
START_HEAD            = e9435d67 (W5)
PRODUCT_COMMIT        = 1e90ca0ec70552df38d17f7f0c2df13822cb93a0
CANDIDATE             = 92c9e198ff26e81115ef8c9fdc069fc39c54b800518fff27a3865fd793a41ff9 (was 5e1c0639…; hai lần đóng băng, cùng tree hash)
CACHE_VERSION         = 116 (bump — diagnostics/cache_proof/CACHE_DECISION.json)
MEASUREMENT_COMMIT    = 1bb11018 (lần đo 3; bằng chứng c08a1eed)
MODEL_SURFACE_CHANGED = NO · DEFAULT_MODE = LLM_ONLY · LIVE_GEMINI_REQUESTS = 0 · SUBAGENTS = 0
HUMAN_VISUAL_REVIEW   = NOT_APPROVED
MERGE / PUSH / PR     = NO / NO / NO
FAVICON_TOUCHED       = NO (deletion của người dùng giữ ngoài staging)
FINAL_DECISION        = READY_FOR_HUMAN_VISUAL_REVIEW (T3 + cổng danh tính tại aa845902 — §2)
```

## 1. Đã làm

| # | Yêu cầu brief | Trạng thái | Nơi |
|---|---|---|---|
| A | Tiếp nhận; dọn Tin học theo danh sách tệp; đính chính bản ghi W5 bằng lớp mới, không đo lại | xong | `0d4c4f8b`, `corrections/W05_RECORD_CORRECTION.json` |
| B | Bảng phạm vi; chóp tam giác đều ≠ tứ diện đều; ba cạnh bên bằng nhau không suy ra đáy đều; chân đường cao suy ra | xong | `PLAN.md` §2, nhãn N8/N9/N5/N5b/N7 |
| C | Backend trên route thật; GIVEN có nguồn, DERIVED có phụ thuộc; bố cục không thành giả thiết; giới hạn biểu diễn khai | xong (miền ℚ³) | `REPORT.md` §1–2 |
| D | D1–D4 sửa · D5 tái hiện, chờ chọn · D6 giữ | một phần (D5) | `REPORT.md` §3 |
| E | Ảnh: lưu có chọn, mỗi ảnh có yêu cầu → ca → trạng thái → commit/candidate → khung nhìn | xong | `results/IMAGE_POLICY.json`, `TEST_TIERS.md` |
| F | Ca phân biệt, oracle độc lập, kiểm trình duyệt, cổng trên checkout sạch | xong | §2 |
| G | `LLM_ONLY`, 0 lượt gọi, cache theo bằng chứng, đóng băng candidate | xong | `REPORT.md` §6 |

## 2. Cổng tại commit cuối

Worktree tách rời sạch `D:/tmp/rtp diag` (CRLF, có dấu cách) tại commit **`aa845902`**, log ngoài worktree rồi chép vào
`diagnostics/logs/` (`T3_FULL_GATE_aa845902.log`, `GATES_aa845902.log`); cây sạch trước và sau.

| Cổng | Kết quả |
|---|---|
| T3 `full-gate.mjs` | **`FULL_PRODUCT_GATE_PASS`** — pytest 7251 passed, 1 skipped; vitest 1145/1145; tsc + build; demo 5/5; bề mặt sập 6/6 |
| T3 lần đầu tại `d2e8a778` | **FAIL** — khoá đếm fixture (`test_generic_tier_a_fixture_generator.py`: 37 ≠ 43) chưa cập nhật từ `4e285690`; sửa ở `aa845902` (log `T3_FULL_GATE_d2e8a778_FAIL.log`). Lời trước đây "pytest đầy đủ chỉ đỏ vì môi trường/candidate" là sai |
| candidate / cache verify | `92c9e198…` khớp (110 file) / khoá 116 khớp, môi trường `b1714b56…` |
| schema ×2 | trùng byte `d852b47c…`; git status không đổi |
| `DEFAULT_MODE` | `LLM_ONLY`; routing.py không đổi từ `e9435d67`; compiler không được gọi từ `app/ai`/`main.py`; `FIXTURE_TIN_CAY` 0 |
| bề mặt mô hình | 1 file trong danh sách đổi: `product_capability.py` (hàng `regular_triangular_pyramid`, `foundation_only`) — băm năng lực/môi trường ngữ nghĩa `b1714b56…` KHÔNG đổi (khoá cache khớp); prompt, thẻ văn phạm, lược đồ không đổi |
| bằng chứng lịch sử | ngoài run chỉ hai sổ sống (candidate, khai lệch); "1 of 181" báo cáo catalog = `EVIDENCE_INDEX.md` — dương tính giả đã biết (như W4/W5) |
| `git diff --check e9435d67..aa845902` | 0 |
| audit tài liệu | PASS |
| node harness | 94: 92 pass, 0 fail, 2 skip |

Mọi cổng bắt buộc đạt, lượt đo 3 có kết quả hợp lệ cho mọi bước ⇒ **`FINAL_DECISION = READY_FOR_HUMAN_VISUAL_REVIEW`**. Không cổng nào
bị hạ ngưỡng. D5 chưa sửa (chờ chọn phương án); kiến trúc tổng thể KHÔNG được tuyên bố hoàn tất (`REPORT.md` §8).

## 3. Chờ người dùng

| Câu | Nội dung |
|---|---|
| **Duyệt hình R1–R12** (chặn merge) | `REVIEW.md` §1, cùng gói W5 R1–R10 và W4 R1–R10 |
| **D5 — chọn phương án** | `OPEN_ISSUES.md` `ISSUE-ARCH-MOBILE-CANVAS-WHITESPACE-AND-PANEL-SCROLL` (a)–(d) |
| Khung đồng dạng cho cạnh hữu tỉ | `ISSUE-ARCH-REGULAR-TRIANGULAR-RATIONAL-EDGES` — việc riêng nếu chọn |
| Ngân sách đo live bố cục nghiêng | `ISSUE-ARCH-REGULAR-TRIANGULAR-MODEL-LAYOUT-UNMEASURED` |

Chỉ người dùng ghi `APPROVED_BY_USER`. Worktree đo `D:/tmp/rtp diag` và `D:/tmp/rtp pre` gỡ sau khi T3 xong.
