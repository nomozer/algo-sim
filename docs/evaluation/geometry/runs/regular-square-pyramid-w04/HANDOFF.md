# HANDOFF — regular-square-pyramid-w04

```text
TASK_SLUG            = regular-square-pyramid
RUN_ID               = regular-square-pyramid-w04 (SHARED_SIMULATION_UI_CLOSURE)
BRANCH               = feat/regular-square-pyramid (local; các commit W4 chưa push)
START_HEAD           = f3db0f6f (W3)
PRODUCT_COMMIT       = 53e4bec5f61722161a20c613c08c4d1f94e2d742
CANDIDATE            = 8a27a58b5a96311dd052a6cc981af558a50878876bef574ec71f8a1b666ed025 (was 5dec4572…; ba lần đóng băng, cùng tree hash)
CACHE_VERSION        = 115 (was 114; diagnostics/PROOF_CACHE_ROW_W04.json)
MEASUREMENT_COMMIT   = 103494c4 (lần đo 4; bằng chứng b4f924c1)
MODEL_SURFACE_CHANGED = NO · DEFAULT_MODE = LLM_ONLY · LIVE_GEMINI_REQUESTS = 0 · SUBAGENTS = 0
HUMAN_VISUAL_REVIEW  = NOT_APPROVED
MERGE / PUSH / PR    = NO / NO / NO
FAVICON_TOUCHED      = NO
FINAL_DECISION       = READY_FOR_HUMAN_VISUAL_REVIEW (T3 + cổng danh tính tại d6e41d80 — §2)
```

## 1. Đã làm (theo yêu cầu)

| # | Yêu cầu | Trạng thái | Nơi |
|---|---|---|---|
| 1 | Tiếp nhận, giữ bản sửa W3 | xong | `REPORT.md` §1 |
| 2 | Skill (Impeccable, Superpowers, Karpathy, Ponytail) | đã dùng | `REPORT.md` §9 |
| 3 | Một cơ chế bảng nổi cho mọi bảng thông tin | xong, đo 7 họ × 3 khổ | `REPORT.md` §2 |
| 4 | Canvas theo chiều cao, «Bước n/N» trong thanh, mô tả bước trong bảng | xong, đo; câu hỏi R4 (mobile) | `REPORT.md` §3 |
| 5 | Chọn trực tiếp + cây «Thành phần» theo bước | xong, đo | `REPORT.md` §4 |
| 6 | Câu chữ tại nguồn, bảy họ | xong, test quét bảy họ | `REPORT.md` §5 |
| 7 | SM trên SA | xong, đo (trước/sau) | `REPORT.md` §6 |
| 8 | Kiểm trình duyệt + T3 + cổng danh tính | trình duyệt xong; T3 + cổng §2 | `REPORT.md` §8 |
| 9 | Cache / candidate / tài liệu sống | 114 → 115; candidate `8a27a58b…` | `REPORT.md` §7 |
| 10 | Commit, gói duyệt | xong | `REVIEW.md` |

## 2. Cổng tại commit cuối

Worktree tách rời sạch `D:/tmp/rsp w04c` (CRLF, có dấu cách), log ngoài worktree rồi chép vào `diagnostics/logs/`.

- T3 lần 1 tại commit tài liệu `82e61f8b` (`T3_FULL_GATE_82e61f8b.log`): **FAIL** đúng 1 test —
  `test_accepted_output_quality.py::test_L_bi_mat…`. Cửa sổ chứng của test đặt bí mật giả ở nhãn thiết diện T và dựa vào
  lời kể chép nhãn thô; W4 thôi chép nhãn không-phải-ký-hiệu nên cảnh không còn chở nó. Sửa ở `d6e41d80`: bí mật đặt ở
  nhãn câu lệnh mặt phẳng (cảnh chở làm tên vật); phép kiểm không lộ giữ nguyên. Test ngoài mã đo ⇒ không đóng băng lại.
- Tại **`d6e41d80`** (`T3_FULL_GATE_d6e41d80.log`, `GATES_d6e41d80.log`; cây sạch trước và sau):

| Cổng | Kết quả |
|---|---|
| T3 `full-gate.mjs` | **`FULL_PRODUCT_GATE_PASS`** — pytest 7174 passed, 1 skipped; vitest 1113/1113; tsc + build; demo; bề mặt sập |
| candidate / cache verify | `8a27a58b…` khớp (110 file) / khoá 115 khớp, môi trường `b1714b56…` |
| schema ×2 | trùng byte `d852b47c…`; git status không đổi |
| `DEFAULT_MODE` | `LLM_ONLY`; routing.py không đổi từ `f3db0f6f`; compiler không được gọi từ `app/ai`/`main.py`; `FIXTURE_TIN_CAY` 0 |
| bề mặt mô hình | 0 file đổi từ `f3db0f6f` |
| bằng chứng lịch sử | ngoài run W4 chỉ hai sổ sống (candidate, khai lệch); "1 of 181" báo cáo catalog = `EVIDENCE_INDEX.md` — dương tính giả đã biết (tài liệu sống khớp regex catalog) |
| `git diff --check f3db0f6f..d6e41d80` | 0 |
| audit tài liệu | PASS |
| node harness | 91: 89 pass, 0 fail, 2 skip |

Mọi cổng bắt buộc đạt, mọi yêu cầu đối chiếu ở §1 ⇒ **`FINAL_DECISION = READY_FOR_HUMAN_VISUAL_REVIEW`**. Không cổng nào
bị hạ hay bỏ; các lần đo không dùng được ghi đủ ở `MEASUREMENT_ATTEMPTS.json`.

## 3. Chờ người dùng

| Câu | Nội dung |
|---|---|
| **Duyệt hình R1–R10** (chặn merge) | `REVIEW.md` §1 |
| R4 | Mobile: giữ canvas cao theo khung nhìn, hay đặt trần chiều cao |

Chỉ người dùng ghi `APPROVED_BY_USER`.
