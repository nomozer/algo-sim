# APPROVAL — tích hợp unnamed-regular-pyramid-grounding vào main và dọn nhánh

Lớp ghi nhận của run `unnamed-regular-pyramid-grounding`, 2026-10-09. Ghi bởi agent theo lời người dùng (tiền lệ
`runs/c0-whole-solid-reader/APPROVAL.md`); agent không tự phê duyệt, không suy phê duyệt từ kết quả tự động, và không sửa
lịch sử kiểm thử. Phê duyệt này là cho TÍCH HỢP bản sửa đã nghiệm thu; KHÔNG có nghĩa 47/47 đề chóp đều không tên đã được
giải quyết, và KHÔNG là phê duyệt triển khai phương án (b).

## Nguyên văn (tin nhắn của người dùng trong phiên, 2026-10-09)

```text
# ALGOSIM — MERGE UNNAMED REGULAR PYRAMID GROUNDING

**Môi trường: Claude Code LOCAL — Windows. KHÔNG chạy trên Cloud.**

Tôi phê duyệt tích hợp nhánh `fix/unnamed-regular-pyramid-grounding` vào `main`, push remote và dọn branch sau khi xác minh an toàn.

Đây chỉ là lượt tích hợp bản sửa đã được LOCAL nghiệm thu. Không triển khai phương án (b) trong lượt này.

## 1. Thông tin bàn giao

- `main` / `origin/main`: `ede8d329`.
- Branch: `fix/unnamed-regular-pyramid-grounding`.
- Branch HEAD đã push: `2d3c510c`.
- Product commit: `12edf57a`.
- Candidate: `d07a92decc0fe635ff32ea858ef86ddd891cc355ff1eef42ffba1d35685ea17e`.
- `CACHE_VERSION=122`.
- T3 PASS tại `97db084f`.
- `LLM_ONLY` mặc định; Geometry Compiler opt-in.
- Frontend không đổi.

LOCAL đã nghiệm thu:

- C1: 26/26 trường hợp bindable khớp nhãn corpus; 21 trường hợp chưa thể binding giữ nguyên.
- C0: 11/11.
- Test mới: 72/72.
- Các test liên quan: 1557/1557.
- Node harness: 102/102.
- T3: 7602 pytest passed, 1 skipped, 2 deselected; 1040 vitest passed; build, demo, crash surface PASS.
- Candidate và cache identity verify.
- Không sửa mã sản phẩm trong lượt LOCAL.
- Không có regression mới được phát hiện trong phạm vi kiểm chứng.

## 2. Kiểm tra trước merge

Đọc `AGENTS.md`, `docs/RULES.md`, quy trình tích hợp và hồ sơ run:

`docs/evaluation/geometry/runs/unnamed-regular-pyramid-grounding/`

Thực hiện:

1. Kiểm tra working tree và worktree tạm.
2. Fetch remote.
3. Xác minh `origin/main=ede8d329`.
4. Xác minh branch local và remote cùng SHA `2d3c510c`.
5. Kiểm tra ancestry và các commit riêng.
6. Kiểm tra thay đổi kể từ T3 tại `97db084f`.
7. Xác nhận sau T3 chỉ có thay đổi tài liệu, không thay đổi sản phẩm, test, candidate hay điều kiện kiểm thử.
8. Chạy candidate `--verify` và cache identity lock `--verify`.
9. Kiểm tra không có thay đổi ngoài phạm vi đã nghiệm thu.

Nếu remote drift, working tree bẩn, có sửa mã sản phẩm sau T3 hoặc bằng chứng không khớp, DỪNG và báo cáo. Không reset hoặc force.

## 3. Merge vào main

Nếu mọi điều kiện hợp lệ:

1. Checkout `main`.
2. Đồng bộ với `origin/main` theo fast-forward an toàn.
3. Merge bằng:

   `git merge --ff-only fix/unnamed-regular-pyramid-grounding`

4. Chạy bộ cổng tích hợp theo tiền lệ G04, G05, C0 Whole-Solid Grounding và C0 Whole-Solid Reader.
5. Xác minh candidate `d07a92de…`.
6. Xác minh `CACHE_VERSION=122` và khóa cache.
7. Xác minh `LLM_ONLY` vẫn mặc định, compiler-first chưa bật.
8. Xác minh prompt, grammar, schema, IR capability không thay đổi.
9. Xuất schema hai lần, đối chiếu byte.
10. Chạy audit tài liệu, `git diff --check`, node harness và các cổng tích hợp bắt buộc.
11. Kế thừa T3 tại `97db084f` nếu mọi điều kiện hợp lệ theo quy định repository. Không chạy lại T3 không cần thiết.

Nếu PASS, push `main` bình thường, không force.

Xác minh:

`main = origin/main = git ls-remote origin refs/heads/main`

Nếu một cổng thất bại, dừng và báo cáo; không tự mở rộng phạm vi sửa chữa.

## 4. Hồ sơ tích hợp

Ghi nhận phê duyệt và tích hợp theo tiền lệ repository.

Phạm vi được duyệt:

### C1

Trong 47 trường hợp hình chóp đều không tên:

- 13 trường hợp vốn đúng tiếp tục phục vụ đúng.
- 4 trường hợp trước trả sai đáp số nay trả đúng.
- 8 trường hợp phục vụ không hợp lệ nay bị từ chối đúng lý do.
- 1 trường hợp đã từ chối tiếp tục từ chối.
- 21 trường hợp có điểm được gọi tên nhưng thiếu tọa độ giữ nguyên.

Không tuyên bố đã xử lý 47/47.

### C0

- 3 trường hợp tọa độ mâu thuẫn với khẳng định chóp đều không tên nay bị từ chối.
- Không có Scene3D, đáp số hoặc LLM repair cho các trường hợp mâu thuẫn bị chặn.
- Các ca nhất quán giữ nguyên hành vi được nghiệm thu.
- Trường hợp có điểm thiếu tọa độ hoặc có hai khối chưa được xử lý vẫn giữ nguyên.

### Cache và candidate

- Candidate `d07a92de…`.
- Product commit `12edf57a`.
- `CACHE_VERSION=122`.
- 11 served → refused.
- 4 served → served nhưng đáp số thay đổi.
- T3 kế thừa từ `97db084f`.
- Không gọi Gemini live.
- Không tuyên bố giảm token.

### Giữ issue OPEN

1. `ISSUE-ARCH-C0-WHOLE-SOLID-CLAIMS-NOT-READ`.
2. `ISSUE-ARCH-UNNAMED-REGULAR-PYRAMID-OUTSIDE-REFUSAL-ZONE`.

Ghi rõ các trường hợp chưa giải quyết, đặc biệt:

- `square/N5`: trả 3 thay vì giá trị đúng √17.
- `square/R2_N9`: đề mâu thuẫn SA = 3, SB = 5 nhưng vẫn phục vụ.
- `square/W5_C`: không đủ dữ kiện xác định chiều cao nhưng vẫn phục vụ 16/3.

Ghi nhận lựa chọn phương án (b) đã được phê duyệt VỀ ĐỊNH HƯỚNG cho lượt Cloud riêng:

- Kiểm tất cả phép gán tên đỉnh hợp lệ trong phạm vi hữu hạn.
- Không tin tên do chương trình LLM đặt.
- Không coi đáp số trùng nhau là bằng chứng duy nhất.
- Không phát triển solver tổng quát khi chưa được phê duyệt.
- Không thực hiện phương án (b) trong lượt merge này.

Nếu cần commit hồ sơ tích hợp, chỉ sửa docs theo tiền lệ; commit, push và xác minh lại main.

## 5. Dọn branch

Chỉ khi main đã push thành công:

1. Xác minh toàn bộ commit branch nằm trong `origin/main`.
2. Xác minh branch local và remote cùng HEAD.
3. Kiểm tra không có worktree sử dụng branch.
4. Nếu an toàn, xóa local bằng `git branch -d`.
5. Xóa remote bằng `git push origin --delete`.

Không force-delete.

Nếu không đủ điều kiện, giữ branch và báo cáo.

## 6. Báo cáo cuối

Báo cáo:

- SHA cuối của main, origin/main, ls-remote.
- Kết quả merge và push.
- Candidate/cache verify.
- Kết quả cổng tích hợp.
- Hồ sơ phê duyệt đã ghi.
- Hai issue vẫn OPEN.
- Branch cleanup.
- Working tree sạch hay không.

Không triển khai phương án (b), không bắt đầu G05/G16/G06, không làm OCR, không gọi Gemini, không thay đổi frontend.

**Điểm dừng: UNNAMED_REGULAR_PYRAMID_GROUNDING_MERGED_MAIN_VERIFIED.**

Không tự bắt đầu công việc Cloud tiếp theo.
```

## Thực hiện

- Trước merge: `git fetch`; cây sạch, một worktree; `main` = `origin/main` = `ede8d329` là tổ tiên của
  `fix/unnamed-regular-pyramid-grounding` = `origin/…` = `2d3c510c` (6 commit, 0 sau). Sau T3 (`97db084f`) chỉ có
  `2d3c510c`, đổi đúng `docs/` ⇒ T3 kế thừa, không chạy lại. Candidate `d07a92de…` và khoá cache 122 verify trước merge.
- `git merge --ff-only fix/unnamed-regular-pyramid-grounding` trên `main`: `ede8d329` → `2d3c510c`.
- Cổng tích hợp (bộ của tiền lệ G04/G05/c0-whole-solid-grounding/c0-whole-solid-reader) trên worktree tách rời sạch tại
  `2d3c510c`: `diagnostics/gates_2d3c510c.log` (candidate `d07a92de…`, cache 122, `LLM_ONLY`, routing không đổi, 0 file
  bề mặt mô hình, lược đồ ×2 trùng byte, audit tài liệu PASS, `diff --check`, node harness 100/0/2).
- `git push origin main` (không force): lần đầu lỗi mạng (`getaddrinfo() thread failed to start`) trước khi chạm remote —
  `origin/main` vẫn `ede8d329`; đẩy lại y nguyên: `ede8d329..2d3c510c`; `main` = `origin/main` = `ls-remote` = `2d3c510c`.
- Dọn nhánh sau khi `main` đã push và xác minh: local = remote = `2d3c510c`, ⊂ `origin/main`, 0 commit riêng, không
  worktree nào dùng; `git branch -d` và `git push origin --delete` thành công.

## Ghi nhận phạm vi được phê duyệt

- **C1 (47 đề chóp đều không tên):** 13 vốn đúng giữ đúng; 4 trước trả sai nay trả đúng (`square/U3` 3√3,
  `triangular/N5b` 9/2, `triangular/U1` 3√3/2, `triangular/U3` 3√3); 8 phục vụ không hợp lệ nay từ chối đúng lý do; 1 đã
  từ chối giữ từ chối; 21 đề gọi tên điểm thiếu toạ độ giữ nguyên. KHÔNG tuyên bố 47/47.
- **C0:** 3 đề toạ độ mâu thuẫn khẳng định chóp đều không tên nay bị từ chối (`SOURCE_SHAPE_CONTRADICTS_COORDINATES`;
  không Scene3D, không đáp số, không vòng sửa LLM); ca nhất quán giữ nguyên hành vi; điểm thiếu toạ độ và hai khối giữ nguyên.
- **Cache và candidate:** candidate `d07a92de…`, product commit `12edf57a`, `CACHE_VERSION` 122; 11 served → refused, 4
  served → served đổi đáp số; T3 kế thừa từ `97db084f`. 0 lượt gọi Gemini live; không tuyên bố giảm token.
- **Còn OPEN:** `ISSUE-ARCH-C0-WHOLE-SOLID-CLAIMS-NOT-READ`, `ISSUE-ARCH-UNNAMED-REGULAR-PYRAMID-OUTSIDE-REFUSAL-ZONE`.
  Chưa giải quyết, đặc biệt: `square/N5` trả 3 thay vì √17; `square/R2_N9` đề mâu thuẫn (SA = 3, SB = 5) vẫn phục vụ;
  `square/W5_C` thiếu dữ kiện xác định chiều cao vẫn phục vụ 16/3.
- **Phương án (b) — phê duyệt VỀ ĐỊNH HƯỚNG cho lượt Cloud riêng, KHÔNG thực hiện ở đây:** kiểm mọi phép gán tên đỉnh hợp
  lệ trong phạm vi hữu hạn; không tin tên do chương trình LLM đặt; không coi đáp số trùng là bằng chứng duy nhất; không phát
  triển bộ giải tổng quát khi chưa được phê duyệt.
