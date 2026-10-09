# APPROVAL — tích hợp geometry-grounding-safety vào main và dọn nhánh

Lớp ghi nhận của run `geometry-grounding-safety`, 2026-10-09. Ghi bởi agent theo lời người dùng (tiền lệ
`runs/general-polygon-base/APPROVAL.md`); agent không tự phê duyệt, không suy phê duyệt từ kết quả tự động, và không sửa
lịch sử kiểm thử. Phê duyệt này là cho TÍCH HỢP hai bản sửa đã kiểm; không có nghĩa mọi mâu thuẫn hình học đã được kiểm.

## Nguyên văn (tin nhắn của người dùng trong phiên, 2026-10-09)

```text
# ALGOSIM — MERGE GEOMETRY GROUNDING SAFETY

**Môi trường: Claude Code LOCAL — Windows.**

Tôi phê duyệt tích hợp nhánh `fix/geometry-grounding-safety` vào `main`, push remote và dọn branch sau khi xác minh an toàn.

## 1. Trạng thái

- `main` / `origin/main`: `e6c3cf68`.
- Branch nguồn: `fix/geometry-grounding-safety`.
- HEAD nguồn: `47d05f22`.
- Product commit cuối: `765291ab`.
- T3 PASS tại `e1dfc851`.
- Candidate: `bbfa5b0d…`, 102 file.
- `CACHE_VERSION=119`.
- `LLM_ONLY` vẫn mặc định; compiler opt-in.

Đọc `AGENTS.md`, quy định tích hợp và hồ sơ `runs/geometry-grounding-safety/`.

## 2. Kiểm tra trước merge

1. Fetch và xác minh SHA local/remote.
2. Kiểm tra working tree sạch, ancestry và commit riêng.
3. Xác minh mọi commit sau T3 tại `e1dfc851` chỉ thay đổi tài liệu, không thay đổi mã sản phẩm, test hoặc điều kiện T3.
4. Kiểm tra candidate `--verify` và cache identity lock ở phiên bản 119.
5. Xác minh không có thay đổi ngoài phạm vi hoặc remote drift.

Nếu có bất thường, dừng và báo cáo.

## 3. Tích hợp

Nếu đạt:

1. Checkout `main`.
2. Fast-forward bằng `git merge --ff-only fix/geometry-grounding-safety`.
3. Chạy đúng bộ cổng tích hợp theo tiền lệ G04/G05.
4. Không chạy lại T3 nếu đủ điều kiện kế thừa kết quả đã đạt.
5. Xác minh `LLM_ONLY` vẫn mặc định, không bật compiler-first.
6. Push `main` bình thường, không force.
7. Kiểm tra `main`, `origin/main`, `ls-remote` trùng SHA.

Ghi hồ sơ tích hợp theo tiền lệ repository nếu cần. Nếu có commit tài liệu sau merge, push và xác minh lại.

## 4. Giữ đúng giới hạn

- Hai lỗi đã sửa không đồng nghĩa mọi mâu thuẫn hình học đã được kiểm chứng.
- `ISSUE-ARCH-C0-WHOLE-SOLID-RELATIONS-NOT-CHECKED` tiếp tục OPEN.
- Không sửa thêm các quan hệ toàn khối trong lượt này.
- Không thay đổi schema, prompt hoặc pipeline mặc định.
- Không chạy Gemini live.
- Không tuyên bố giảm token.
- Không sửa frontend hoặc phát triển OCR.

## 5. Dọn branch

Sau khi main đã push và xác minh:

- Kiểm tra nhánh `fix/geometry-grounding-safety` tại local và remote không có commit chưa tích hợp.
- Kiểm tra không có worktree đang sử dụng nhánh.
- Nếu an toàn, xóa branch local bằng `git branch -d` và remote bằng `git push origin --delete`.
- Không force-delete hoặc rewrite history.

Nếu không xóa an toàn được, giữ nhánh và báo cáo nguyên nhân.

## 6. Báo cáo cuối

Báo cáo ngắn:

- SHA cuối cùng của main local/remote.
- Kết quả fast-forward, push.
- Candidate/cache đã verify.
- Kết quả các cổng tích hợp.
- Branch đã dọn hay chưa.
- Working tree.
- Những giới hạn còn OPEN.

Không bắt đầu công việc Cloud tiếp theo.

**Điểm dừng: GEOMETRY_GROUNDING_SAFETY_MERGED_MAIN_VERIFIED.**
```

## Thực hiện

- Trước merge: `git fetch`; cây sạch, một worktree; `main` = `origin/main` = `e6c3cf68` là tổ tiên của
  `fix/geometry-grounding-safety` = `origin/…` = `47d05f22` (6 commit, 0 sau). Sau T3 (`e1dfc851`) chỉ có `47d05f22`, đổi
  đúng `docs/` ⇒ T3 kế thừa, không chạy lại. Candidate `bbfa5b0d…` và khoá cache 119 verify trước merge.
- `git merge --ff-only fix/geometry-grounding-safety` trên `main`: `e6c3cf68` → `47d05f22`.
- Cổng tích hợp (bộ của tiền lệ G04/G05) trên worktree tách rời sạch tại `47d05f22`: `diagnostics/gates_47d05f22.log`
  (candidate, cache 119, `LLM_ONLY`, routing không đổi, 0 file bề mặt mô hình, lược đồ ×2 trùng byte, audit tài liệu PASS,
  `diff --check`, node harness 100/0/2).
- `git push origin main` (không force): `e6c3cf68..47d05f22`; `main` = `origin/main` = `ls-remote` = `47d05f22`.
- Dọn nhánh sau khi `main` đã push và xác minh: local = remote = `47d05f22`, ⊂ `origin/main`, 0 commit riêng, không
  worktree nào dùng; `git branch -d` và `git push origin --delete` thành công.
