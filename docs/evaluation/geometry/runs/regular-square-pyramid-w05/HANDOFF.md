# HANDOFF — regular-square-pyramid-w05

```text
TASK_SLUG            = regular-square-pyramid
RUN_ID               = regular-square-pyramid-w05 (IMMERSIVE_SIMULATION_AND_ARCHITECTURE_SLICE)
BRANCH               = feat/regular-square-pyramid (local; các commit W5 chưa push)
START_HEAD           = 73bc404e (W4)
PRODUCT_COMMIT       = 82225a7b129a45e722af6abd13d3d63cb9cc40d2
CANDIDATE            = 5e1c0639393295df1b37a33e25b18ed69da87160197524abd1dab0f78ac51b18 (was 8a27a58b…; hai lần đóng băng, cùng tree hash)
CACHE_VERSION        = 115 (không bump — diagnostics/cache_proof/CACHE_DECISION_W05.json)
MEASUREMENT_COMMIT   = f01df0e5 (lần đo 4; bằng chứng 3b31aa18)
MODEL_SURFACE_CHANGED = NO · DEFAULT_MODE = LLM_ONLY · LIVE_GEMINI_REQUESTS = 0 · SUBAGENTS = 0
HUMAN_VISUAL_REVIEW  = NOT_APPROVED
MERGE / PUSH / PR    = NO / NO / NO
FAVICON_TOUCHED      = NO (deletion của người dùng giữ ngoài staging)
FINAL_DECISION       = xem §2
```

## 1. Đã làm

| # | Yêu cầu | Trạng thái | Nơi |
|---|---|---|---|
| A | Tiếp nhận, giữ W3/W4 | xong (không làm lại; cổng W4 chạy lại xanh) | `PLAN.md` |
| B | Skill + DESIGN.md | đã dùng thật | `diagnostics/SKILL_NOTES.md` |
| C | Chế độ tập trung (không header, quay lại, toàn màn hình tuỳ chọn, giữ trạng thái, bố cục một màn) | xong, đo 7 họ × 3 khổ | `REPORT.md` §1, §3 |
| D | Nhóm công cụ | xong (kiểm kê trước) | `diagnostics/TOOL_INVENTORY.md` |
| E | Bỏ thẻ lời giải lặp, chú giải vào «Hiển thị» | xong | `REPORT.md` §1 |
| F | Lát cắt backend: bộ đọc chuỗi bằng nhau | xong, trên route thật | `REPORT.md` §2 |
| G | Kiểm thật | lần đo 4 xanh trọn; 3 lần trước ghi lại | `MEASUREMENT_ATTEMPTS.json` |
| H | Cache / candidate / tài liệu | 115 giữ; `5e1c0639…`; tài liệu sống | `REPORT.md` §5 |

## 2. Cổng tại commit cuối

Chạy ở worktree tách rời sạch sau commit tài liệu — kết quả ghi ở mục này bởi commit kế tiếp (`T3_FULL_GATE_<sha>.log`,
`GATES_<sha>.log` trong `diagnostics/logs/`).

## 3. Chờ người dùng

| Câu | Nội dung |
|---|---|
| **Duyệt hình R1–R10** (chặn merge) | `REVIEW.md` §1 |

Chỉ người dùng ghi `APPROVED_BY_USER`. Việc kế tiếp đề xuất (không làm): `REPORT.md` §7.
