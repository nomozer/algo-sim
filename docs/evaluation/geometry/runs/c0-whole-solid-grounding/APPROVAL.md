# APPROVAL — tích hợp c0-whole-solid-grounding vào main và dọn nhánh

Lớp ghi nhận của run `c0-whole-solid-grounding`, 2026-10-09. Ghi bởi agent theo lời người dùng (tiền lệ
`runs/geometry-grounding-safety/APPROVAL.md`); agent không tự phê duyệt, không suy phê duyệt từ kết quả tự động, và không
sửa lịch sử kiểm thử. Phê duyệt này là cho TÍCH HỢP kết quả đã nghiệm thu; không có nghĩa toàn bộ C0 đã an toàn.

## Nguyên văn (tin nhắn của người dùng trong phiên, 2026-10-09)

```text
# ALGOSIM — MERGE C0 WHOLE-SOLID GROUNDING

**Môi trường: Claude Code LOCAL — Windows. Không chạy trên Cloud.**

Tôi phê duyệt tích hợp `fix/c0-whole-solid-grounding` vào `main`, push remote và dọn nhánh sau khi xác minh an toàn.

Đây là lượt tích hợp kết quả đã nghiệm thu, không phải lượt phát triển chức năng.

## 1. Thông tin bàn giao

- `main` / `origin/main`: `9762f441`.
- Branch: `fix/c0-whole-solid-grounding`.
- HEAD đã push: `11be6092`.
- Product commit: `c11e8c9d`.
- T3 PASS tại `d838cc5b`.
- Candidate: `8c4c0128…`, 102 file.
- `CACHE_VERSION=120`.
- `LLM_ONLY` vẫn mặc định.
- Geometry Compiler vẫn opt-in.

LOCAL đã xác minh:

- C0 Whole-Solid: 34/34.
- Oracle: 29/29.
- G04: 51/51.
- G05: 53/53.
- Regression, identity, docs, test_api: 1314/1314.
- T3: 7401 pytest passed, 1040 vitest passed; build, demo và crash surface PASS.
- Không có thay đổi mã sản phẩm trong lượt LOCAL.
- Không ghi nhận regression mới so với `main`.

**Đính chính quan trọng:** Chính xác có 15 ca chuyển từ served sang refused. Trong 18 ca được gắn nhãn refused, 3 ca đã bị từ chối từ baseline. Không sử dụng con số 16 làm số ca được sửa mới.

## 2. Kiểm tra trước merge

Đọc `AGENTS.md`, `docs/RULES.md`, quy trình tích hợp và hồ sơ:

`docs/evaluation/geometry/runs/c0-whole-solid-grounding/`

Thực hiện:

1. Kiểm tra working tree sạch và các worktree đang tồn tại.
2. Fetch remote.
3. Xác minh `origin/main=9762f441`.
4. Xác minh `origin/fix/c0-whole-solid-grounding=11be6092`.
5. Xác minh branch local/remote trùng nhau.
6. Kiểm tra ancestry và toàn bộ commit sau T3 tại `d838cc5b`.
7. Xác minh thay đổi sau T3 chỉ thuộc tài liệu, không thay đổi mã sản phẩm, test, candidate hoặc điều kiện kiểm thử.
8. Kiểm tra candidate `--verify` và khoá cache 120.

Nếu remote thay đổi ngoài dự kiến, working tree bẩn hoặc không thể kế thừa T3 hợp lệ, dừng và báo cáo. Không reset hoặc force.

## 3. Merge vào main

Nếu tất cả điều kiện đạt:

1. Checkout `main`.
2. Đồng bộ `main` với `origin/main` bằng fast-forward an toàn nếu cần.
3. Merge bằng:

   `git merge --ff-only fix/c0-whole-solid-grounding`

4. Chạy bộ cổng tích hợp theo tiền lệ G04, G05 và Geometry Grounding Safety.
5. Xác minh candidate/cache.
6. Xác minh `LLM_ONLY` vẫn mặc định và compiler-first chưa bật.
7. Kiểm tra không đổi prompt, grammar, schema và model-facing capability.
8. Kiểm tra tính tái lập schema, audit tài liệu, `git diff --check` và node harness theo quy định.
9. Không chạy lại T3 nếu đủ điều kiện kế thừa và quy định repository cho phép.
10. Push `main` bình thường, không force.
11. Xác minh `main`, `origin/main` và `git ls-remote` cùng SHA.

## 4. Hồ sơ tích hợp

Ghi nhận merge theo tiền lệ repository.

Trong hồ sơ phải thể hiện rõ:

- C0 đã bổ sung kiểm chứng quan hệ toàn khối trong phạm vi đã đăng ký.
- 15 trường hợp trước phục vụ nay từ chối.
- Candidate `8c4c0128…`.
- `CACHE_VERSION=120`.
- T3 PASS kế thừa từ `d838cc5b`.
- Không chạy Gemini live.
- Không tuyên bố tiết kiệm token.

**Giữ OPEN:** `ISSUE-ARCH-C0-WHOLE-SOLID-CLAIMS-NOT-READ`.

Ghi rõ ba biến thể diễn đạt hình chóp đều chưa được parser nhận diện. Vì vậy, không tuyên bố toàn bộ C0 đã an toàn.

Nếu cần commit tài liệu tích hợp, chỉ sửa hồ sơ theo quy định, commit, push và xác minh lại `main`.

Không sửa ngược báo cáo Cloud lịch sử chỉ để che sự đính chính 16 → 15; ghi nhận đính chính của LOCAL trong hồ sơ tích hợp.

## 5. Dọn nhánh

Chỉ thực hiện sau khi `main` đã push thành công và được xác minh.

Với `fix/c0-whole-solid-grounding`:

1. Kiểm tra local/remote HEAD.
2. Xác minh tất cả commit đã nằm trong `origin/main`.
3. Kiểm tra không có worktree khác đang dùng nhánh.
4. Nếu an toàn, xóa local bằng `git branch -d`.
5. Xóa remote bằng `git push origin --delete`.

Không force-delete, không xóa branch chưa được tích hợp.

Nếu xóa không an toàn, giữ nhánh và báo cáo.

## 6. Báo cáo cuối

Báo cáo ngắn:

- SHA cuối của `main`, `origin/main`, `ls-remote`.
- Kết quả fast-forward và push.
- Candidate và cache verify.
- Kết quả bộ cổng tích hợp.
- Hồ sơ tích hợp đã ghi.
- Trạng thái cleanup branch.
- Working tree sạch hay không.
- Issue parser còn OPEN.

Không sửa parser, không mở rộng G05/G16/G06, không làm OCR, không gọi Gemini và không thay đổi frontend.

**Điểm dừng: C0_WHOLE_SOLID_GROUNDING_MERGED_MAIN_VERIFIED.**
```

## Thực hiện

- Trước merge: `git fetch`; cây sạch, một worktree; `main` = `origin/main` = `9762f441` là tổ tiên của
  `fix/c0-whole-solid-grounding` = `origin/…` = `11be6092` (7 commit, 0 sau). Sau T3 (`d838cc5b`) chỉ có `11be6092`, đổi
  đúng `docs/` ⇒ T3 kế thừa, không chạy lại. Candidate `8c4c0128…` và khoá cache 120 verify trước merge.
- `git merge --ff-only fix/c0-whole-solid-grounding` trên `main`: `9762f441` → `11be6092`.
- Cổng tích hợp (bộ của tiền lệ G04/G05/geometry-grounding-safety) trên worktree tách rời sạch tại `11be6092`:
  `diagnostics/gates_11be6092.log` (candidate, cache 120, `LLM_ONLY`, routing không đổi, 0 file bề mặt mô hình, lược đồ ×2
  trùng byte, audit tài liệu PASS, `diff --check`, node harness 100/0/2).
- `git push origin main` (không force): `9762f441..11be6092`; `main` = `origin/main` = `ls-remote` = `11be6092`.
- Dọn nhánh sau khi `main` đã push và xác minh: local = remote = `11be6092`, ⊂ `origin/main`, 0 commit riêng, không
  worktree nào dùng; `git branch -d` và `git push origin --delete` thành công.

## Ghi nhận tích hợp

- C0 kiểm thêm khẳng định toàn khối trong phạm vi amendment §22 (lăng trụ đứng/xiên, hộp chữ nhật, lập phương + cạnh, chóp
  tứ giác/tam giác đều + cạnh bên, trung đoạn, tâm đáy, tứ diện đều, mọi cạnh, chiều cao = khoảng cách tới mặt đáy).
- **15** hàng nhãn trước phục vụ nay bị từ chối (`SOURCE_SHAPE_CONTRADICTS_COORDINATES`). Đính chính LOCAL: báo cáo Cloud
  (`report.md`) và `cache/decision.json` ghi 16 — trong 18 hàng nhãn `refused`, 3 đã bị từ chối sẵn trên `main`
  (`RSP_C_centre_off`, `P_C_prism_top_not_translate`, `RT_C_tetrahedron_not_regular`). Hai tệp Cloud giữ nguyên (bất biến);
  đính chính nằm ở `handoff.md` (LOCAL), `run.json` và tệp này.
- Candidate `8c4c0128…`, `CACHE_VERSION` 120; T3 `FULL_PRODUCT_GATE_PASS` kế thừa từ `d838cc5b`.
- 0 lượt gọi Gemini live; không tuyên bố tiết kiệm token.
- **Còn OPEN:** `ISSUE-ARCH-C0-WHOLE-SOLID-CLAIMS-NOT-READ` — ba cách viết chóp đều bộ đọc chưa nhận ("hình chóp tứ giác đều
  có đỉnh S và đáy ABCD", "hình chóp tứ giác đều" không tên, "hình chóp đều S.ABCD"), toạ độ mâu thuẫn vẫn được phục vụ.
  Vì vậy KHÔNG tuyên bố toàn bộ C0 đã an toàn.
