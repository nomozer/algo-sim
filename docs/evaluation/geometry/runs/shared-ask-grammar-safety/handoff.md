# CLAUDE_RESUME_HANDOFF — shared-ask-grammar-safety (2026-10-15)

**Status:** `SHARED_ASK_GRAMMAR_SAFETY_BLOCKED`. Không merge, không push.

## Kiểm lại trước khi tin

```bash
git rev-parse HEAD main origin/main          # research tip ≥ 5fc1645c; main = origin/main = 2a3c0787
git diff --stat 5f1b576c HEAD -- backend/app frontend/src     # rỗng nếu chưa có sửa sản phẩm mới
cd backend && PYTHONIOENCODING=utf-8 .venv/Scripts/python.exe scripts/freeze_evaluation_candidate.py --verify   # 4b95dcc6…
cd backend && PYTHONIOENCODING=utf-8 .venv/Scripts/python.exe ../docs/evaluation/geometry/runs/shared-ask-grammar-safety/grammar_probe.py <out.json>
```

## Trạng thái

- Product `5f1b576c` đọc trọn câu hỏi, đóng ngoặc/làm tròn/đơn vị, và reused-foot đọc nguồn. Harness probe đăng ký
  trước: 0 WRONG_SERVED trên A/B (trước đó B 47, A 32).
- Bất biến giữ nguyên. Candidate `4b95dcc6…` (freeze `5fc1645c`). T3 chưa chạy.

## Blocker — cần người dùng quyết phạm vi

Theo [`review-9ce1298f.md`](review-9ce1298f.md), xem [`report.md`](report.md) §5.

- **Trong phạm vi đã duyệt, chưa đúng:**
  - **C1:** đọc mệnh đề mục tiêu bằng `_ket_muc_tieu` (kết ở `,`/`;`), không đánh dấu tới điểm dừng đầu tiên. Có hồi
    quy G1/G7-line so với `8da9ae31`.
  - **C4:** đơn vị được hỏi phải khớp đơn vị của dữ kiện (`unit()` của `cover()` đã có chính sách này).
  - **I2/I3:** cụm dựng ("Xác định thiết diện … và tính …", "Dựng hình chiếu … và tính …") và vài dạng làm tròn
    ("đến 0,01", "chữ số thập phân thứ hai", "(đơn vị diện tích)") phải được đọc.
- **Ngoài phạm vi, cần duyệt mới:**
  - **C2:** đọc các câu sau yêu cầu đầu tiên, kể cả câu có động từ hỏi hay từ dẫn dữ kiện nhưng không có cụm được hỏi.
  - **C3:** đưa `ask_section_area` của mặt suy dẫn (`mat_song_song_dung_nguon`, `_mat_hai_duong_dung_nguon`) qua
    `_vung_hoi` và cổng đọc câu.

Mọi sửa tiếp theo đều chạm `MEASURED_SYSTEM_PATHS`, nên phải đóng băng lại candidate, chạy T3 sạch và review độc lập
lại. Mở rộng harness probe theo các dạng của reviewer (`probes/`).

## Chưa làm

T3 · Scene3D product–Playwright parity audit (`ISSUE-ARCH-SCENE3D-CONSTRUCTION-READABILITY` OPEN).
