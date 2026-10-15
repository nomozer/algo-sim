# CLAUDE_RESUME_HANDOFF — source-bound-result-planning-false-serve-fix (2026-10-15)

**Status:** `RESULT_BINDING_FALSE_SERVE_FIX_BLOCKED`. Không merge, không push.

## Kiểm lại trước khi tin

```bash
git rev-parse HEAD main origin/main        # research tip ≥ f25f2deb; main = origin/main = 2a3c0787
git diff --stat 8da9ae31 HEAD -- backend/app frontend/src   # rỗng nếu chưa có sửa mới
cd backend && PYTHONIOENCODING=utf-8 .venv/Scripts/python.exe scripts/freeze_evaluation_candidate.py --verify   # 7e993f8d…
```

## Đã xong

`_kiem_phu` đọc câu hỏi trên đề gốc bằng văn phạm đóng dùng chung; IMPORTANT-1/2 của review `efb756aa` đã đóng.
Corpus 18/18, benchmark 30 và two-line 45/32 giữ nguyên. Provider không đổi. Candidate `7e993f8d…` (freeze `f25f2deb`).

## Blocker (cần người dùng quyết)

Review độc lập `2427289a` ([`review-2427289a.md`](review-2427289a.md)) chỉ ra 3 lỗi. Cả ba đều nằm ở văn phạm hỏi
**dùng chung** và có từ trước:

1. **CRITICAL-1:** `_hoi_dung_cum` chỉ đọc từ động từ hỏi cuối cùng, nên "Nhân đôi kết quả, tính …" và "Hai lần của đại
   lượng sau bằng bao nhiêu: …" vẫn được phục vụ, trên mọi ask và cả Route A. Muốn đóng phải đọc lượng hỏi ở mức câu, và
   phân biệt được tiền đề trong cùng câu ("Cho …, tính …").
2. **CRITICAL-2:** nội dung ngoặc trong `_SAU_HOP_LE` là mở ("(kết quả nhân đôi)"). Cần văn phạm đóng cho lời dặn
   làm tròn/đơn vị.
3. **IMPORTANT-1:** nhánh chân chiếu tái sử dụng trong `_kiem_result_binding` vẫn đọc văn bản đã ghép quote.

Sửa cả ba là đổi văn phạm của mọi ask trên cả hai tuyến ⇒ một wave riêng, cần duyệt phạm vi. Wave đó phải đo lại
benchmark 30, two-line 45/32, corpus 18 và mutant suite, đóng băng lại candidate, chạy T3 sạch và review độc lập (kể cả
delta chưa review `2427289a..8da9ae31`).

## Chưa làm

- T3 cho candidate `7e993f8d…`.
- Review độc lập của `8da9ae31`.
- Scene3D product–Playwright parity audit (vẫn là ưu tiên sau tích hợp; `ISSUE-ARCH-SCENE3D-CONSTRUCTION-READABILITY` OPEN).
