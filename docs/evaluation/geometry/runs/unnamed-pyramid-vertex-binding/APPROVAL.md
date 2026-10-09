# APPROVAL — tích hợp chính sách A (unnamed-pyramid-vertex-binding) vào main và dọn nhánh

Lớp ghi nhận của run `unnamed-pyramid-vertex-binding`, 2026-10-09. Ghi bởi agent theo lời người dùng (tiền lệ
`runs/unnamed-regular-pyramid-grounding/APPROVAL.md`); agent không tự phê duyệt, không suy phê duyệt từ kết quả tự động, và
không sửa lịch sử kiểm thử. Phê duyệt này là cho TÍCH HỢP một biện pháp giảm thiểu an toàn đã nghiệm thu; KHÔNG phải tuyên bố
hệ giải được 21 bài, KHÔNG phải phê duyệt phương án B hay G05.

## Nguyên văn (tin nhắn của người dùng trong phiên, 2026-10-09)

```text
# ALGOSIM — MERGE POLICY A INTO MAIN

**MÔI TRƯỜNG: Claude Code LOCAL — Windows. KHÔNG chạy trên Cloud.**

Tôi phê duyệt tích hợp `fix/unnamed-pyramid-vertex-binding` vào `main`, push remote và dọn nhánh sau khi xác minh an toàn.

Đây là lượt TÍCH HỢP bản sửa đã nghiệm thu, không phải lượt phát triển sản phẩm.

Không triển khai phương án B. Không bắt đầu G05 trong lượt merge này.

## 1. Baseline

- `main` / `origin/main`: `a7c56942`.
- Branch: `fix/unnamed-pyramid-vertex-binding`.
- Branch HEAD: `32705882`.
- Product commit: `56692926`.
- Candidate: `b13a3ef1…`, 102 file.
- `CACHE_VERSION=123`.
- T3 PASS tại `39b0fb4a`.
- Pipeline mặc định: `LLM_ONLY`.
- Compiler: opt-in.
- Frontend không đổi.

LOCAL đã nghiệm thu:

- Policy A: 21/21 ca từ chối.
- 12 served → refused.
- 9 refused → refused, giữ stage/reason.
- 97/97 test mới và cập nhật.
- 1582/1582 test liên quan.
- 4 oracle khớp.
- Node harness 102/102.
- T3: 7627 pytest passed, 1 skipped, 2 deselected; 1040 vitest passed; build, demo và crash surface PASS.
- Candidate và cache identity verify.
- 49/49 Tier-A fixture byte-identical.
- Không sửa mã sản phẩm trong lượt LOCAL.

## 2. Kiểm tra trước merge

Đọc `AGENTS.md`, `docs/RULES.md`, quy trình tích hợp và hồ sơ:

`docs/evaluation/geometry/runs/unnamed-pyramid-vertex-binding/`

Thực hiện:

1. Kiểm tra working tree và các worktree đang tồn tại.
2. Fetch remote.
3. Xác minh `origin/main=a7c56942`.
4. Xác minh branch local = remote = `32705882`.
5. Kiểm tra ancestry, các commit riêng của branch.
6. Kiểm tra mọi commit sau T3 tại `39b0fb4a`.
7. Xác nhận sau T3 chỉ thay đổi `docs/`, không thay đổi mã sản phẩm, test, candidate hoặc điều kiện kiểm thử.
8. Chạy candidate `--verify`.
9. Kiểm tra cache identity lock 123.
10. Kiểm tra không có thay đổi ngoài phạm vi đã nghiệm thu.

Nếu remote drift, working tree bẩn, có thay đổi sản phẩm sau T3 hoặc bằng chứng không khớp, DỪNG và báo cáo.

Không reset hoặc force.

## 3. Tích hợp

Nếu mọi điều kiện hợp lệ:

1. Checkout `main`.
2. Đồng bộ `main` với `origin/main` bằng fast-forward an toàn.
3. Merge bằng:

   `git merge --ff-only fix/unnamed-pyramid-vertex-binding`

4. Chạy bộ cổng tích hợp theo tiền lệ G04, G05 và các lượt C0 gần nhất.
5. Xác minh candidate `b13a3ef1…`.
6. Xác minh `CACHE_VERSION=123`.
7. Xác minh cache identity lock.
8. Xác minh `LLM_ONLY` mặc định, compiler-first chưa bật.
9. Xác minh không thay đổi prompt, grammar, schema hoặc IR capability.
10. Xuất schema hai lần, đối chiếu byte.
11. Chạy audit tài liệu, `git diff --check`, node harness và các cổng tích hợp bắt buộc.

Kế thừa T3 tại `39b0fb4a` nếu toàn bộ điều kiện hợp lệ theo quy định repository.

Không chạy lại T3 không cần thiết.

Nếu PASS, push `main` bình thường, không force.

Xác minh:

`main = origin/main = git ls-remote origin refs/heads/main`

Nếu push gặp lỗi mạng, kiểm tra trạng thái remote trước khi thử lại; không tạo commit hoặc reset ngoài dự kiến.

## 4. Hồ sơ tích hợp

Ghi phê duyệt và kết quả tích hợp theo tiền lệ.

### Policy A

Ghi nhận:

- 21 trường hợp chóp đều không tên chưa đủ cơ sở liên kết đỉnh đã được từ chối theo chính sách.
- 12 served → refused.
- 9 refused → refused, không đổi stage/reason.
- Không trả đáp số hay Scene3D cho các trường hợp bị chặn.
- Không gửi lỗi `ASSUMPTION_INVARIANCE_UNPROVEN` sang LLM repair.
- Không sử dụng `SOURCE_SHAPE_CONTRADICTS_COORDINATES` cho trường hợp chỉ thiếu liên kết đỉnh.

### Giới hạn năng lực

Năm bài có đáp số xác định nhưng bị từ chối theo chính sách A:

- S5: SA = √17.
- S7: V = 16.
- R2_S9: V = 16/3.
- P9: V = 9/2.
- P11: SA = 3.

Không gọi năm bài này là đề sai hoặc không giải được về mặt toán học.

Giữ nguyên nhãn toán học và oracle của nghiên cứu phương án B.

Phương án B là nâng cấp năng lực được HOÃN, không triển khai trong đợt này.

### Cache và candidate

- Candidate `b13a3ef1…`.
- Product commit `56692926`.
- `CACHE_VERSION=123`.
- T3 kế thừa từ `39b0fb4a`.
- Không gọi Gemini live.
- Không tuyên bố giảm token.
- Không tuyên bố C0 an toàn với mọi loại bài.

Phân biệt rõ safety mitigation đã được triển khai và giới hạn capability vẫn OPEN.

Cập nhật `APPROVAL.md`, `run.json`, `STATUS_LEDGER`, `CURRENT_STATE`, `ROADMAP`, `AI_CONTEXT_BUNDLE`, `OPEN_ISSUES` theo đúng quy định và tiền lệ.

Nếu cần commit hồ sơ tích hợp, chỉ thay đổi trong `docs/`; commit, push và xác minh lại SHA của main.

## 5. Dọn branch

Chỉ sau khi main đã được push và xác minh thành công:

1. Kiểm tra toàn bộ commit branch đã nằm trong `origin/main`.
2. Kiểm tra local/remote branch cùng HEAD.
3. Xác minh không có worktree nào sử dụng branch.
4. Nếu an toàn, xóa local bằng `git branch -d`.
5. Xóa remote bằng `git push origin --delete`.

Không force-delete.

Nếu chưa đủ điều kiện, giữ branch và báo cáo.

## 6. Báo cáo cuối

Báo cáo:

- SHA cuối của `main`, `origin/main`, `ls-remote`.
- Kết quả fast-forward merge và push.
- Candidate và cache verify.
- Kết quả các cổng tích hợp.
- Hồ sơ phê duyệt đã ghi.
- Giới hạn năng lực còn OPEN.
- Kết quả dọn branch.
- Working tree sạch hay không.

Không mở rộng parser/C0/C1.
Không triển khai phương án B.
Không mở G05/G16/G06 trong lượt này.
Không OCR, không frontend, không Gemini live.
Không tạo PR nếu không được yêu cầu.

**Điểm dừng: POLICY_A_MERGED_MAIN_VERIFIED.**

Không tự bắt đầu công việc Cloud tiếp theo.
```

## Thực hiện

- Trước merge: `git fetch`; cây sạch, một worktree; `main` = `origin/main` = `a7c56942` là tổ tiên của
  `fix/unnamed-pyramid-vertex-binding` = `origin/…` = `32705882` (8 commit, 0 sau). Sau T3 (`39b0fb4a`) chỉ có `32705882`,
  đổi đúng `docs/` ⇒ T3 kế thừa, không chạy lại. Candidate `b13a3ef1…` và khoá cache 123 verify trước merge.
- `git merge --ff-only fix/unnamed-pyramid-vertex-binding` trên `main`: `a7c56942` → `32705882`.
- Cổng tích hợp (bộ của tiền lệ G04/G05/các run C0) trên worktree tách rời sạch tại `32705882`:
  `diagnostics/gates_32705882.log` (candidate `b13a3ef1…`, cache 123, `LLM_ONLY`, routing không đổi, 0 file bề mặt mô
  hình, lược đồ ×2 trùng byte, audit tài liệu PASS, `diff --check`, node harness 100/0/2).
- `git push origin main` (không force, một lần, không lỗi mạng): `a7c56942..32705882`; `main` = `origin/main` = `ls-remote`
  = `32705882`.
- Dọn nhánh sau khi `main` đã push và xác minh: local = remote = `32705882`, ⊂ `origin/main`, 0 commit riêng, không
  worktree nào dùng; `git branch -d` và `git push origin --delete` thành công.

## Ghi nhận phạm vi được phê duyệt

- **Giảm thiểu an toàn (chính sách A — đã triển khai, đã kiểm):** 21 đề chóp đều không tên chưa đủ cơ sở gắn đỉnh bị từ chối
  theo chính sách; 12 served → refused, 9 refused → refused giữ nguyên chặng/lý do; không đáp số, không Scene3D cho đề bị
  chặn; `ASSUMPTION_INVARIANCE_UNPROVEN` không được gửi sang vòng sửa LLM; không dùng `SOURCE_SHAPE_CONTRADICTS_COORDINATES`
  cho đề chỉ thiếu gắn đỉnh.
- **Giới hạn năng lực (còn OPEN):** 5 bài có đáp số xác định bị từ chối theo chính sách A — S5 SA = √17, S7 V = 16, R2_S9
  V = 16/3, P9 V = 9/2, P11 SA = 3. Đây KHÔNG phải đề sai hay vô nghiệm. Nhãn toán học (`labels.json`) và `oracle.py` của
  nghiên cứu phương án B giữ nguyên.
- **Phương án B:** nâng cấp năng lực HOÃN, không triển khai trong đợt này.
- **Cache và candidate:** candidate `b13a3ef1…`, product commit `56692926`, `CACHE_VERSION` 123; T3 kế thừa từ `39b0fb4a`.
  0 lượt gọi Gemini live; không tuyên bố giảm token; không tuyên bố C0 an toàn với mọi loại bài.
