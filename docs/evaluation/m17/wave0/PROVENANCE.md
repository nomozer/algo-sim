# Provenance — M17-Lite Wave 0 artifacts

File này KHÔNG thuộc bộ 6 artifact sync-locked (nó là ghi chú xuất xứ, viết
tay một lần khi đóng Wave 0; không tự sinh lại).

## Trình tự sinh và commit (thực tế)

1. `620a09a` — proposal M17-Lite (docs-only, user duyệt scope).
2. `f1cdce0` — **commit chứa TOÀN BỘ nội dung Wave 0** (contract, audit,
   learner mapping, 6 artifact lần đầu). Artifact trong commit này mang
   `run_meta.git_commit = 620a09a` (sinh TRƯỚC khi commit — hạn chế cố hữu
   của trứng-gà provenance).
3. `4d5eed2` — regenerate 6 artifact tại HEAD `f1cdce0` để
   `run_meta.git_commit` trỏ đúng commit chứa nội dung cuối (tiền lệ M16
   `183eb1a`). Diff đúng 2 field volatile × 4 JSON; 2 MD nguyên văn không đổi
   (bằng chứng builder tất định).

Closeout HEAD của Wave 0 vì vậy là `4d5eed2`; commit nội dung là `f1cdce0`;
`run_meta.git_commit` trong artifact = `f1cdce0`. Đây là trình tự đúng như
thiết kế, không phải sai lệch.

## Correction số liệu (user yêu cầu khi duyệt closeout)

- **Con số ĐÚNG (từ artifact máy-sinh `authenticity_metrics.json`):**
  tổng **55 case** = 46 ok-archetype (direct 14 + paraphrase 14 +
  changed_input 14 + boundary 4, tất cả matched) + 4 near-miss + 5 control
  (2 leak_control + 1 leak_probe + 2 refusal_control).
- Commit message `f1cdce0` và báo cáo closeout đầu tiên ghi "56 case /
  47/47 ok-archetype" — đó là **lỗi tường thuật của người viết báo cáo**
  (đếm nhầm), không phải lỗi artifact. Lịch sử git không rewrite; ghi chú
  này là bản đính chính chuẩn. Mọi trích dẫn số liệu Wave 0 phải lấy từ
  artifact, không lấy từ commit message.

## Quyết định user khi duyệt closeout (2026-07-21)

- Chấp nhận `CONDITIONAL_LEAK_CONFIRMED` (probe adversarial duyệt cây) là
  **limitation đã biết** — phương án (a): không siết production gate/classify
  trong Wave 0; giữ test pin + ledger.
- Claim boundary: 0 generic leak vô điều kiện trong audit hiện tại; luồng
  production phụ thuộc analyze cung cấp ownership đúng; KHÔNG tuyên bố gate
  chống được analyze khai sai.
- Limitation phải được kiểm lại và đóng khi `tree_traversal` triển khai ở
  Wave 2.
