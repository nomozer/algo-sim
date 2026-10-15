# CLAUDE_RESUME_HANDOFF — shared-ask-grammar-safety (2026-10-16)

**Status:** `SHARED_ASK_GRAMMAR_REVIEW_FINDINGS_CLOSED_PENDING_INDEPENDENT_REVIEW`. Không merge, không push, không refreeze candidate trước khi review độc lập đạt.

## Kiểm lại trước khi tin

```bash
git rev-parse HEAD main origin/main          # research/source-bound-result-planning; main = origin/main = 2a3c0787
cd backend && PYTHONIOENCODING=utf-8 .venv/Scripts/python.exe -m pytest tests/geometry/test_shared_ask_grammar.py -q
cd backend && PYTHONIOENCODING=utf-8 .venv/Scripts/python.exe -m pytest tests/geometry/test_result_binding_planning.py -q
cd backend && PYTHONIOENCODING=utf-8 .venv/Scripts/python.exe ../docs/evaluation/geometry/runs/shared-ask-grammar-safety/grammar_probe.py <out.json>
```

## Trạng thái

- Đã đóng toàn bộ phát hiện trong review độc lập `9ce1298f` (`C1`–`C4`, `I2`, `I3` tại `4acfc731`) **và** toàn bộ phát hiện trong kiểm toán độc lập đối với `4acfc731` (`CR-1`, `CR-2`, `IM-1`, `IM-2`) cùng chính sách fail-closed đối với yêu cầu làm tròn số thập phân và biểu diễn góc theo độ/radian (xem [`report.md`](report.md) §8):
  - **CR-1:** `_kiem_ghi_chu` kiểm tra đơn vị trong câu ghi chú ở cả trước câu hỏi (`_kiem_vung_tien_de`) và từ câu hỏi trở đi (`_kiem_du_kien_cau_hoi`) đối chiếu với chiều đại lượng và `don_vi_de`.
  - **CR-2:** `_SAU_HOP_LE` và `_kiem_don_vi_hoi` phân biệt tham số đã khai báo (`theo a` chỉ khi `_co_tham_so_a(calls)` và không dùng đơn vị mét) với đơn vị trần (`theo m`, `theo mm`, `theo cm`, ... phải khớp `chieu` và `don_vi_de`).
  - **IM-1:** Khôi phục các mệnh đề mục tiêu hợp lệ (`nhau`, `bằng hai cách` — phục hồi `P11-line`/`P11-plane`/`P11-length` trong `grammar_probe.py`, `gấp đôi`/`hai lần`/`một nửa`, `ΔSAB`, mục tiêu nối bằng dấu phẩy, và kiểm `_DUOI_BANG` trong `_muc_tieu_mau_thuan`) mà không mở lại mệnh đề mục tiêu chứa bổ ngữ đổi đại lượng.
  - **Chính sách làm tròn / góc (§6):** Từ chối fail-closed (`QUESTION_CONTEXT_UNSUPPORTED`) mọi yêu cầu làm tròn kết quả (`_LAM_TRON` khi đề có lệnh `ask_*`) và mọi yêu cầu đổi biểu diễn góc sang độ/radian (`theo độ`, `theo radian`, `(độ)`, `(radian)`). Trong `grammar_probe.py` (không sửa file lịch sử), 10 ca `P5-*` và `P7-*` bị báo `FALSE_REFUSAL` là do nhãn cũ `expected = "SERVED"` trước khi đổi chính sách.
  - **IM-2:** Đính chính số liệu `benchmark-30-metrics.json` thực tế là **19 `correct_served` (`SERVED`), 9 `correct_refusal` (`REFUSED`), 0 `wrong_served`, 2 `false_refusal` (`REFUSED` strict xfail `B27`, `B28`)** (tổng `19 SERVED, 11 REFUSED`) và `test_hybrid_compiler_benchmark.py` có **98 pytest items = 94 passed, 4 xfailed**.
- Biên lai RED (`158 failed, 275 passed` tại `4acfc731`) lưu ở [`red/red-review-4acfc731.txt`](red/red-review-4acfc731.txt) và 6 biên lai GREEN lưu ở [`verification/`](verification/).

## Bước tiếp theo

1. Chạy **Independent Code Review** đối với commit đóng lỗi hiện tại.
2. Sau khi review độc lập đạt (`PASS`), mới thực hiện refreeze `EVALUATION_CANDIDATE.json`, cập nhật `inputs/candidate_divergence.json` và chạy authoritative T3 trên detached worktree sạch.
3. Scene3D product–Playwright parity audit (`ISSUE-ARCH-SCENE3D-CONSTRUCTION-READABILITY` OPEN).

