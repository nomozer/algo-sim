# APPROVAL — tích hợp G05 (miền hẹp) vào main và dọn hai nhánh đã tích hợp

Lớp ghi nhận của run `general-polygon-base`, 2026-10-09. Ghi bởi agent theo lời người dùng (tiền lệ
`runs/oblique-prism/APPROVAL.md`); agent không tự phê duyệt, không suy phê duyệt từ kết quả tự động, và không sửa lịch
sử kiểm thử. Phê duyệt này là cho TÍCH HỢP miền đã kiểm; G05 vẫn `foundation_only`, không phải toàn họ.

## Nguyên văn (tin nhắn của người dùng trong phiên, 2026-10-09)

```text
# ALGOSIM — G05 MERGE & BRANCH CLEANUP

**Môi trường: Claude Code LOCAL — Windows.**

Tôi phê duyệt tích hợp G05 — lăng trụ/chóp đáy đa giác, trong phạm vi hẹp đã kiểm chứng, vào `main`.

Sau khi merge thành công và xác minh an toàn, cho phép dọn hai branch tính năng đã tích hợp: `feat/oblique-prism` và `feat/general-polygon-base`.

## 1. Trạng thái xuất phát

- `main` / `origin/main`: `d5287ff7`.
- Branch G05: `feat/general-polygon-base`.
- HEAD đã push: `9666b861`.
- T3 đã PASS tại `f250f5ef`.
- Candidate: `72d6070a…`, product commit `4e30a211`.
- `CACHE_VERSION=118`.
- `LLM_ONLY` vẫn mặc định.
- Compiler chỉ chạy opt-in.

G05 được nghiệm thu trong miền đáy đa giác lồi xác định bằng chuỗi góc vuông liên tiếp, không phải toàn bộ họ G05.

## 2. Xác minh trước merge

1. Fetch remote, xác minh SHA local/remote và working tree sạch.
2. Xác minh `d5287ff7` là tổ tiên của `9666b861`.
3. Kiểm tra diff của các commit sau T3 tại `f250f5ef`.
4. Chỉ kế thừa T3 nếu không có thay đổi mã sản phẩm, điều kiện kiểm thử hoặc candidate làm mất hiệu lực kết quả.
5. Kiểm tra các quy định tích hợp của `AGENTS.md`, `docs/RULES.md` và tiền lệ G04.

Nếu xuất hiện thay đổi ngoài dự kiến hoặc điều kiện không đạt, dừng và báo cáo.

## 3. Merge G05

Nếu đạt:

1. Checkout `main`.
2. Fast-forward bằng `git merge --ff-only feat/general-polygon-base`.
3. Chạy các cổng tích hợp bắt buộc theo tiền lệ G04.
4. Xác minh candidate `--verify` và cache identity lock.
5. Xác minh `LLM_ONLY` vẫn mặc định, compiler-first không được bật.
6. Push `main` bình thường, không force.
7. Xác minh `main`, `origin/main` và `ls-remote` trùng SHA.

Không tự mở rộng G05, sửa frontend hoặc chạy Gemini live.

Không chạy lại T3 nếu bằng chứng kế thừa hợp lệ và quy định không bắt buộc.

## 4. Hồ sơ tích hợp

Ghi kết quả tích hợp theo tiền lệ repository nếu bắt buộc.

Giữ nguyên các giới hạn và issue:

- `ISSUE-ARCH-G05-REMAINING-BASES`.
- `ISSUE-ARCH-COMPILER-UNTAGGED-RECTANGLE-ASSUMPTION`.
- Chưa kiểm nghiệm Gemini thật cho G05.
- Chưa chứng minh mức giảm token.
- Compiler-first chưa đủ điều kiện chuyển mặc định.

Ghi nhận thêm hành vi đã tồn tại từ trước: tọa độ được ưu tiên dù mô tả hình học có thể mâu thuẫn. Không sửa ngoài phạm vi; bảo đảm có issue theo dõi phù hợp, tránh tạo issue trùng.

Không nâng trạng thái G05 khỏi `foundation_only`.

## 5. Cleanup branch

**Chỉ sau khi main đã push thành công và được xác minh.**

Kiểm tra cả local và remote của:

- `feat/oblique-prism`
- `feat/general-polygon-base`

Xác minh tất cả commit trên từng nhánh đều đã nằm trong `origin/main`, không có worktree khác sử dụng, không có commit riêng chưa bảo toàn.

Nếu đạt, xóa nhánh local bằng `git branch -d` và xóa nhánh remote bằng `git push origin --delete`.

Nếu `git branch -d` từ chối chỉ do upstream cũ, kiểm tra lại ancestry với `origin/main`, sau đó có thể bỏ cấu hình upstream của nhánh và thử lại thao tác xóa an toàn.

Không sử dụng `git branch -D`, không force-delete và không xóa branch nào chưa được xác minh đã tích hợp.

Nếu cleanup có vướng mắc, giữ nhánh và báo cáo; không ảnh hưởng kết quả merge G05.

## 6. Kiểm tra cuối

Báo cáo:

- SHA cuối của `main` local/remote.
- Kết quả fast-forward và push.
- Cổng tích hợp đã chạy.
- Candidate và cache còn hợp lệ.
- Trạng thái hai nhánh sau cleanup.
- Working tree sạch hay không.
- Những issue còn OPEN.

Không chạy lại T3 hoặc tạo screenshot không cần thiết.

Không bắt đầu G06, OCR hay công việc mới.

**Điểm dừng: G05_MERGED_MAIN_VERIFIED.**
```

## Thực hiện

- Trước merge: `git fetch`; cây sạch, một worktree; `main` = `origin/main` = `d5287ff7` là tổ tiên của
  `feat/general-polygon-base` = `origin/…` = `9666b861` (6 commit, 0 sau). Sau T3 (`f250f5ef`) chỉ có `9666b861`, đổi
  đúng `docs/` ⇒ T3 kế thừa, không chạy lại.
- `git merge --ff-only feat/general-polygon-base` trên `main`: `d5287ff7` → `9666b861`.
- Cổng tích hợp (bộ của tiền lệ G04) trên worktree tách rời sạch tại `9666b861`: `diagnostics/gates_9666b861.log`.
- `git push origin main` (không force): `d5287ff7..9666b861`; `main` = `origin/main` = `ls-remote` = `9666b861`.
- Hành vi toạ độ-ưu-tiên có từ trước: issue mới `ISSUE-ARCH-C0-SHAPE-TEXT-NOT-CHECKED-AGAINST-COORDINATES` (không issue
  nào sẵn có phủ nó; bằng chứng `diagnostics/probe_c0_shape_text_vs_coordinates.*`).
- Dọn nhánh sau khi `main` đã push và xác minh: `feat/oblique-prism` (`a0fdbba4`) và `feat/general-polygon-base`
  (`9666b861`) — local = remote, cả hai ⊂ `origin/main`, 0 commit riêng, không worktree nào dùng; `git branch -d` (không
  cần gỡ upstream) và `git push origin --delete` đều thành công; `ls-remote refs/heads/feat/*` rỗng.
