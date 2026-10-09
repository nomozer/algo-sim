# APPROVAL — tích hợp c0-whole-solid-reader vào main và dọn nhánh

Lớp ghi nhận của run `c0-whole-solid-reader`, 2026-10-09. Ghi bởi agent theo lời người dùng (tiền lệ
`runs/c0-whole-solid-grounding/APPROVAL.md`); agent không tự phê duyệt, không suy phê duyệt từ kết quả tự động, và không
sửa lịch sử kiểm thử. Phê duyệt này là cho TÍCH HỢP kết quả đã nghiệm thu; không có nghĩa toàn bộ C0 đã an toàn.

## Nguyên văn (tin nhắn của người dùng trong phiên, 2026-10-09)

```text
# ALGOSIM — MERGE C0 WHOLE-SOLID READER

**Môi trường: Claude Code LOCAL — Windows. KHÔNG chạy trên Cloud.**

Tôi phê duyệt tích hợp nhánh `fix/c0-whole-solid-reader` vào `main`, push remote và dọn branch sau khi xác minh an toàn.

Đây là lượt TÍCH HỢP kết quả đã được LOCAL nghiệm thu. Không phát triển chức năng mới.

## 1. Trạng thái bàn giao

- `main` / `origin/main`: `a1350da3`.
- Branch: `fix/c0-whole-solid-reader`.
- Branch HEAD: `81ff8899`.
- Product commit: `7d551535`.
- Candidate: `c3f8339927bfe27273b5ff0bc43811928f85b84d76bd1cea839d0883e1aacaec`.
- `CACHE_VERSION=121`.
- T3 PASS tại `1396878e`.
- `LLM_ONLY` tiếp tục mặc định.
- Geometry Compiler vẫn opt-in.

LOCAL đã nghiệm thu:

- Reader: 129/129.
- C0 oracle: 27/27.
- C1: 141/141 khớp nhãn corpus độc lập.
- Regression, identity, docs, test_api và các suite liên quan: 1485/1485.
- Node harness: 102/102.
- T3: 7530 pytest passed, 1040 vitest passed; build, demo, crash surface PASS.
- Không sửa mã sản phẩm trong lượt LOCAL.
- Không ghi nhận regression mới.

## 2. Kiểm tra trước merge

Đọc `AGENTS.md`, `docs/RULES.md`, quy trình tích hợp và hồ sơ:

`docs/evaluation/geometry/runs/c0-whole-solid-reader/`

Thực hiện:

1. Kiểm tra Git và working tree.
2. Kiểm tra những worktree đang tồn tại.
3. Fetch remote.
4. Xác minh `origin/main=a1350da3`.
5. Xác minh branch local và remote cùng HEAD `81ff8899`.
6. Kiểm tra ancestry và các commit riêng trên branch.
7. Kiểm tra toàn bộ thay đổi kể từ T3 tại `1396878e`.
8. Xác minh các commit sau T3 chỉ sửa tài liệu, không sửa mã sản phẩm, test, candidate hoặc các điều kiện ảnh hưởng đến T3.
9. Chạy candidate `--verify` và kiểm tra cache identity lock tại version 121.

Nếu có remote drift, working tree không sạch, thay đổi sản phẩm sau T3 hoặc bất kỳ điều kiện kế thừa nào không hợp lệ, DỪNG và báo cáo.

Không reset hoặc force.

## 3. Merge và kiểm tra tích hợp

Nếu đủ điều kiện:

1. Checkout `main`.
2. Đồng bộ local main với `origin/main` bằng fast-forward an toàn nếu cần.
3. Merge:

   `git merge --ff-only fix/c0-whole-solid-reader`

4. Chạy bộ cổng tích hợp theo tiền lệ G04, G05, Geometry Grounding Safety và C0 Whole-Solid Grounding.
5. Xác minh candidate `c3f83399…` vẫn khớp.
6. Xác minh `CACHE_VERSION=121`, cache identity lock khớp.
7. Xác minh `LLM_ONLY` mặc định và compiler-first chưa bật.
8. Xác minh không thay đổi prompt, grammar, schema hoặc model-facing capability.
9. Xuất schema hai lần và đối chiếu tính tái lập.
10. Chạy audit tài liệu, `git diff --check`, node harness và các cổng tích hợp theo quy định.
11. Kế thừa T3 tại `1396878e` nếu toàn bộ điều kiện hợp lệ. Không chạy lại T3 không cần thiết.

Nếu đạt, push `main` bình thường, không force.

Xác minh:

`main = origin/main = git ls-remote origin refs/heads/main`

Nếu bất kỳ cổng nào không đạt, dừng và báo cáo thay vì tự sửa ngoài phạm vi.

## 4. Hồ sơ tích hợp

Ghi hồ sơ theo tiền lệ repository, bao gồm `APPROVAL.md` nếu quy trình yêu cầu.

Ghi chính xác phạm vi được phê duyệt:

**C0:**
- Hai nhóm cách diễn đạt hình chóp đều đã được nhận diện.
- 10 trường hợp served → refused do tọa độ mâu thuẫn.
- 1 trường hợp refused → served do trước đây đọc sai câu phủ định.

**C1:**
- 141/141 kết quả khớp nhãn corpus độc lập.
- Với mỗi cách diễn đạt mới: 24 refused → served đúng nhãn; 1 served → refused đúng nhãn; 20 refused → refused; 2 served → served.
- Các hàng dạng canonical không thay đổi.
- Ca N5 không còn trả kết quả SA = 3 sai; chương trình không thỏa tính đều và bị từ chối đúng theo nhãn.

**Danh tính và kiểm thử:**
- Candidate `c3f83399…`.
- Product commit `7d551535`.
- `CACHE_VERSION=121`.
- T3 `FULL_PRODUCT_GATE_PASS` kế thừa từ `1396878e`.
- Không gọi Gemini live.
- Không tuyên bố giảm token.

Giữ OPEN:

1. `ISSUE-ARCH-C0-WHOLE-SOLID-CLAIMS-NOT-READ` — phần hình chóp đều không có tên và không có đủ thông tin liên kết đỉnh/đáy.
2. `ISSUE-ARCH-UNNAMED-REGULAR-PYRAMID-OUTSIDE-REFUSAL-ZONE`.

Ghi rõ baseline và branch đều có cùng vấn đề: 37 trường hợp hình chóp đều không tên được phục vụ, trong đó 22 đúng nhãn, 4 sai đáp số và 11 đáng lẽ phải từ chối.

Không tuyên bố các vấn đề này đã được giải quyết.

Nếu phải thêm commit hồ sơ, chỉ thay đổi docs theo quy định; commit, push và xác minh lại main.

## 5. Dọn branch

Chỉ sau khi main đã push và xác minh thành công:

1. Xác minh toàn bộ commit của `fix/c0-whole-solid-reader` nằm trong `origin/main`.
2. Kiểm tra local/remote branch trùng nhau.
3. Kiểm tra không có worktree sử dụng branch.
4. Nếu an toàn, xóa local bằng `git branch -d`.
5. Xóa remote bằng `git push origin --delete`.

Không force-delete, không rewrite Git history.

Nếu không an toàn, giữ branch và báo cáo.

## 6. Bàn giao cuối

Báo cáo:

- SHA cuối của main, origin/main và ls-remote.
- Kết quả merge fast-forward, push.
- Candidate/cache verify.
- Kết quả các cổng tích hợp.
- Hồ sơ tích hợp đã ghi.
- Trạng thái branch cleanup.
- Working tree sạch hay không.
- Hai issue vẫn OPEN.

Không sửa parser thêm, không mở rộng C1, G05, G16, G06 hoặc OCR.

Không thay đổi frontend, không gọi Gemini live và không bật compiler-first.

**Điểm dừng: C0_WHOLE_SOLID_READER_MERGED_MAIN_VERIFIED.**

Không tự bắt đầu công việc Cloud tiếp theo.
```

## Thực hiện

- Trước merge: `git fetch`; cây sạch, một worktree; `main` = `origin/main` = `a1350da3` là tổ tiên của
  `fix/c0-whole-solid-reader` = `origin/…` = `81ff8899` (6 commit, 0 sau). Sau T3 (`1396878e`) chỉ có `81ff8899`, đổi đúng
  `docs/` ⇒ T3 kế thừa, không chạy lại. Candidate `c3f83399…` và khoá cache 121 verify trước merge.
- `git merge --ff-only fix/c0-whole-solid-reader` trên `main`: `a1350da3` → `81ff8899`.
- Cổng tích hợp (bộ của tiền lệ G04/G05/geometry-grounding-safety/c0-whole-solid-grounding) trên worktree tách rời sạch tại
  `81ff8899`: `diagnostics/gates_81ff8899.log` (candidate `c3f83399…`, cache 121, `LLM_ONLY`, routing không đổi, 0 file
  bề mặt mô hình, lược đồ ×2 trùng byte, audit tài liệu PASS, `diff --check`, node harness 100/0/2).
- `git push origin main` (không force): `a1350da3..81ff8899`; `main` = `origin/main` = `ls-remote` = `81ff8899`.
- Dọn nhánh sau khi `main` đã push và xác minh: local = remote = `81ff8899`, ⊂ `origin/main`, 0 commit riêng, không
  worktree nào dùng; `git branch -d` và `git push origin --delete` thành công.

## Ghi nhận phạm vi được phê duyệt

- **C0:** hai nhóm lối viết chóp đều được bộ đọc nhận ("có đỉnh S và đáy ABCD" và biến thể "là … ,"; "hình chóp đều
  S.ABCD"), như ký hiệu chuẩn; 10 hàng nhãn served → refused (`SOURCE_SHAPE_CONTRADICTS_COORDINATES`, toạ độ mâu thuẫn);
  1 hàng refused → served (`N_K_negation_canonical_notation` — câu phủ định trước bị đọc thành tiền đề).
- **C1:** 141/141 kết cục khớp nhãn corpus độc lập (ký hiệu chuẩn + hai lối viết × 47 hàng). Mỗi lối viết mới: 24 refused →
  served đúng nhãn, 1 served → refused đúng nhãn, 20 refused → refused, 2 served → served. Hàng ký hiệu chuẩn không đổi.
  `N5_apex_over_vertex` không còn trả SA = 3 (sai, đúng là √17): chương trình dựng chóp không thoả tính đều và bị từ chối
  đúng theo nhãn.
- **Danh tính và kiểm thử:** candidate `c3f83399…`, product commit `7d551535`, `CACHE_VERSION` 121; T3
  `FULL_PRODUCT_GATE_PASS` kế thừa từ `1396878e`. 0 lượt gọi Gemini live; không tuyên bố giảm token.
- **Còn OPEN (không giải quyết):** `ISSUE-ARCH-C0-WHOLE-SOLID-CLAIMS-NOT-READ` — chóp đều không tên, không đủ thông tin gắn
  đỉnh/đáy; `ISSUE-ARCH-UNNAMED-REGULAR-PYRAMID-OUTSIDE-REFUSAL-ZONE` — trên `main` (baseline) và nhánh như nhau: 37 đề chóp
  đều không tên được phục vụ, 22 đúng nhãn, 4 sai đáp số, 11 lẽ ra phải từ chối.
