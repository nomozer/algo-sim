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
FINAL_DECISION        = ⟨T3⟩
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

⟨T3 table⟩

## 3. Chờ người dùng

| Câu | Nội dung |
|---|---|
| **Duyệt hình R1–R12** (chặn merge) | `REVIEW.md` §1, cùng gói W5 R1–R10 và W4 R1–R10 |
| **D5 — chọn phương án** | `OPEN_ISSUES.md` `ISSUE-ARCH-MOBILE-CANVAS-WHITESPACE-AND-PANEL-SCROLL` (a)–(d) |
| Khung đồng dạng cho cạnh hữu tỉ | `ISSUE-ARCH-REGULAR-TRIANGULAR-RATIONAL-EDGES` — việc riêng nếu chọn |
| Ngân sách đo live bố cục nghiêng | `ISSUE-ARCH-REGULAR-TRIANGULAR-MODEL-LAYOUT-UNMEASURED` |

Chỉ người dùng ghi `APPROVED_BY_USER`. Worktree đo `D:/tmp/rtp diag` và `D:/tmp/rtp pre` gỡ sau khi T3 xong.
