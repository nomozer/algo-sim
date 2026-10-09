# APPROVAL — tích hợp G04 lăng trụ xiên vào main (nhánh feat/oblique-prism)

Lớp ghi nhận của run `oblique-prism`, 2026-10-09. Ghi bởi agent theo lời người dùng (tiền lệ
`runs/frontend-freeze/APPROVAL.md`, `runs/cuboid-merge/APPROVAL.md`); agent không tự phê duyệt, không suy phê duyệt từ kết
quả tự động, và không sửa lịch sử kiểm thử. Phê duyệt này là cho TÍCH HỢP; G04 vẫn `foundation_only`.

## Nguyên văn (tin nhắn của người dùng trong phiên, 2026-10-09)

```text
# AlgoSim — Merge G04 vào main

**Môi trường: Claude Code LOCAL — Windows.**

Tôi cho phép tích hợp G04 — lăng trụ xiên vào `main` và push `main` lên remote, với các điều kiện sau.

## 1. Xác minh trước merge

- Branch nguồn: `feat/oblique-prism`, HEAD tham chiếu `a0fdbba4`.
- `main`/`origin/main` tham chiếu `ba995887`.
- Candidate `02ce5e1e…`, `CACHE_VERSION=118`.
- T3 đã PASS tại `75c24394`.
- Những commit sau T3 chỉ được kế thừa kết quả kiểm thử nếu xác minh không thay đổi mã sản phẩm hoặc điều kiện kiểm thử.

Fetch remote, kiểm tra Git status và ancestry.

Nếu có commit mới ngoài dự kiến, thay đổi chưa commit, xung đột hoặc điều kiện repository chưa đạt thì dừng và báo cáo.

## 2. Tích hợp

Nếu điều kiện đạt:

1. Chuyển sang `main`.
2. Fast-forward bằng `git merge --ff-only feat/oblique-prism`.
3. Chạy đúng các kiểm tra tích hợp bắt buộc theo repository.
4. Không chạy lại T3 hoặc screenshot chỉ vì thao tác merge nếu quy định và bằng chứng hiện có cho phép kế thừa.
5. Push `main` bình thường, tuyệt đối không force push.
6. Xác minh `main`, `origin/main` và `ls-remote` cùng SHA.
7. Ghi hồ sơ kết quả tích hợp theo tiền lệ repository nếu bắt buộc.

Không mở PR, không sửa frontend, không thay đổi pipeline mặc định.

## 3. Giữ nguyên giới hạn

- G04 mới đạt mức `foundation_only`.
- Chưa có bằng chứng Gemini thật tự sinh Semantic Program G04.
- Compiler G04 chỉ chạy opt-in.
- `LLM_ONLY` tiếp tục mặc định.
- Hai issue về từ vựng chân đường cao và lời kể vectơ vẫn OPEN.
- Không tuyên bố giảm token đã được đo.
- Không tự động chuyển compiler-first.

## 4. Nhánh cũ

Sau khi merge, giữ lại `feat/oblique-prism` ở local và remote.

Chưa cho phép xóa nhánh trong lượt này.

## 5. Bàn giao

Báo cáo ngắn:
- SHA cuối của `main` local/remote.
- Fast-forward có thành công không.
- Cổng tích hợp đã chạy và kết quả.
- Candidate/cache còn hợp lệ không.
- Working tree có sạch không.
- Trạng thái branch G04.

Không bắt đầu G05 trong lượt LOCAL này.

Việc tiếp theo sau khi tích hợp thành công là CLOUD triển khai **G05 — lăng trụ/chóp đáy đa giác tổng quát**, trên kiến trúc theo hàm hiện có, theo ROADMAP §0.2.

Dừng sau khi hoàn thành tích hợp.
```

## Thực hiện

- Trước merge: `git fetch`; cây sạch; `main` = `origin/main` = `ba995887` là tổ tiên của `feat/oblique-prism` =
  `origin/feat/oblique-prism` = `a0fdbba4` (6 commit, 0 sau). Sau T3 (`75c24394`) chỉ có `a0fdbba4`, đổi đúng
  `docs/` (bundle, CURRENT_STATE, ROADMAP, handoff, log T3) ⇒ T3 kế thừa, không chạy lại.
- `git merge --ff-only feat/oblique-prism` trên `main`: `ba995887` → `a0fdbba4`.
- Cổng tích hợp (bộ của tiền lệ frontend-freeze) trên worktree tách rời sạch tại `a0fdbba4`: `diagnostics/gates_a0fdbba4.log`.
- `git push origin main` (không force): `ba995887..a0fdbba4`; `main` = `origin/main` = `ls-remote` = `a0fdbba4`.
- Nhánh `feat/oblique-prism` giữ ở local và remote. Không PR.
