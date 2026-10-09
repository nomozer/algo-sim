# APPROVAL — tích hợp G05 chóp lục giác đều (regular-hexagonal-pyramid) vào main và dọn nhánh

Lớp ghi nhận của run `regular-hexagonal-pyramid`, 2026-10-10. Ghi bởi agent theo lời người dùng (tiền lệ
`runs/unnamed-pyramid-vertex-binding/APPROVAL.md`); agent không tự phê duyệt, không suy phê duyệt từ kết quả tự động, và
không sửa lịch sử kiểm thử. Phê duyệt này là cho TÍCH HỢP lát G05 đã nghiệm thu độc lập; KHÔNG phải tuyên bố năng lực Gemini
thực tế, KHÔNG phải phê duyệt mở rộng T11, họ lăng trụ, phương án B hay G16/G06.

## Nguyên văn (tin nhắn của người dùng trong phiên, 2026-10-10)

```text
# ALGOSIM — MERGE G05 REGULAR HEXAGONAL PYRAMID

**MÔI TRƯỜNG: Claude Code LOCAL — Windows.**

Tôi phê duyệt tích hợp nhánh `feat/g05-geometry-capability-expansion` vào `main`, push remote và dọn nhánh sau khi xác minh toàn bộ điều kiện an toàn.

Đây là lượt TÍCH HỢP bản G05 đã được nghiệm thu độc lập. Không phát triển thêm mã sản phẩm trong lượt này.

## 1. Baseline

- `main` / `origin/main`: `f20caf8a`.
- Branch: `feat/g05-geometry-capability-expansion`.
- Branch HEAD LOCAL: `55f51395`.
- Product commit: `6c792434`.
- Candidate SHA-256: `cf47dd6142f2d46fd5b9be252fee0d9a7530844d3e1bf07ece47b52b4b433f5a`.
- Candidate: 102 file.
- `CACHE_VERSION=124`.
- T3 PASS tại `0fe806ff`.
- `LLM_ONLY` mặc định; compiler opt-in.
- Frontend không thay đổi.

LOCAL đã nghiệm thu:

- 8/8 bài G05 dương có đáp số đúng và C1-certified.
- 7 refused → served.
- 1 served sai 1 → served đúng 6√3.
- N4 được chấp nhận bằng chứng minh metric độc lập.
- C0: hình lục giác đều tọa độ hợp lệ được phục vụ; ca đỉnh lệch trục bị từ chối.
- Scene3D: 7 đỉnh, 7 mặt, chart_metric hợp lệ.
- Renderer transformation đúng; kiểm tra trình duyệt thực tế H6, H8, N4 PASS.
- 38/38 test mới.
- 1620/1620 test liên quan.
- 49/49 Tier-A fixture byte-identical.
- Node harness 102/102.
- T3: 7665 pytest passed, 1 skipped, 2 deselected; 1040 vitest passed; build, demo và crash surface PASS.

## 2. Kiểm tra trước merge

Đọc `AGENTS.md`, `docs/RULES.md`, quy trình tích hợp và hồ sơ:

`docs/evaluation/geometry/runs/regular-hexagonal-pyramid/`

Thực hiện:

1. Kiểm tra working tree và các worktree đang tồn tại.
2. Fetch remote.
3. Xác minh `origin/main=f20caf8a`.
4. Xác minh branch local và remote cùng HEAD `55f51395`.
5. Kiểm tra ancestry và commit riêng của branch.
6. Kiểm tra toàn bộ commit sau T3 `0fe806ff`.
7. Chỉ kế thừa T3 nếu các thay đổi sau đó chỉ thuộc tài liệu, không thay đổi mã sản phẩm, test, candidate hoặc điều kiện chạy kiểm thử.
8. Chạy candidate `--verify`.
9. Chạy cache identity lock `--verify`.
10. Xác minh không xuất hiện thay đổi ngoài phạm vi nghiệm thu.

Nếu SHA không khớp, remote drift, cây bẩn hoặc có thay đổi ảnh hưởng T3, DỪNG báo cáo. Không reset, không force.

## 3. Tích hợp

Nếu các điều kiện hợp lệ:

1. Checkout `main`.
2. Đồng bộ fast-forward an toàn với `origin/main`.
3. Merge:

   `git merge --ff-only feat/g05-geometry-capability-expansion`

4. Chạy bộ cổng tích hợp theo tiền lệ G04/G05 và các lượt C0 gần nhất trên clean detached worktree.
5. Xác minh candidate `cf47dd61…`.
6. Xác minh cache identity ở version 124.
7. Xác minh `LLM_ONLY` vẫn mặc định, không bật compiler-first.
8. Xác minh routing mặc định không đổi.
9. Xác minh bề mặt mô hình: prompt, grammar, schema, IR capability.
10. Xuất schema hai lần và đối chiếu byte.
11. Chạy audit tài liệu, `git diff --check`, node harness và các integration gate bắt buộc.

Kế thừa T3 tại `0fe806ff` nếu đúng điều kiện repository. Không chạy lại T3 chỉ để lặp công việc.

Nếu PASS, push `main` bình thường, không force.

Xác minh:

`main = origin/main = git ls-remote origin refs/heads/main`

Nếu push thất bại do mạng, xác minh trạng thái remote trước khi thử lại.

## 4. Hồ sơ phê duyệt

Ghi nhận lời phê duyệt này theo tiền lệ, không sửa lịch sử kiểm thử.

### Năng lực G05 mới

Hình chóp lục giác đều:

- Reader hỗ trợ ký hiệu chuẩn và các cách diễn đạt đã đăng ký.
- Template T11 và metric suy từ số đo trong văn bản.
- 8 bài toán dương được phục vụ đúng.
- 7 bài trước từ chối nay phục vụ đúng.
- 1 bài trước phục vụ sai nay phục vụ đúng.
- N4 chuyển thành được phục vụ đúng sau đính chính nhãn đã kiểm chứng độc lập.
- Scene3D chứa 7 đỉnh, 7 mặt và chart_metric.
- Kiểm chứng renderer bằng trình duyệt thực tế đối với H6, H8, N4.

### Đính chính N4

Ghi nhận N4 được CHẤP NHẬN theo chứng minh độc lập bằng metric.

Phân biệt rõ nhãn gốc, `label_corrections.json` và giới hạn hiện tại của `oracle.py`.

Không chỉnh sửa oracle lịch sử hoặc tuyên bố oracle gốc đã được cập nhật.

### Giới hạn còn lại

- `foundation_only`: chưa có kết quả chạy Gemini thật.
- Compiler chưa có họ hình lục giác.
- Chưa hỗ trợ lăng trụ lục giác đều, lăng trụ tam giác đều, chóp lục giác đều không tên, ngũ giác đều và các loại đáy khác đã liệt kê.
- Vị trí dòng đáp số trên giao diện chưa được kiểm chứng trong lượt này.
- Không tuyên bố giảm token.
- Không tuyên bố năng lực Gemini thực tế được cải thiện dựa riêng trên corpus chương trình viết tay.

### Cache và candidate

- Product commit `6c792434`.
- Candidate `cf47dd61…`.
- `CACHE_VERSION=124`.
- Cache bump có căn cứ từ thay đổi đáp số H5 và từ chối C0.
- T3 kế thừa từ `0fe806ff`.

Cập nhật `APPROVAL.md`, `run.json`, `STATUS_LEDGER`, `CURRENT_STATE`, `ROADMAP`, `AI_CONTEXT_BUNDLE` và `OPEN_ISSUES` theo quy định repository.

Nếu cần commit hồ sơ tích hợp, chỉ sửa trong `docs/`, commit và push bình thường.

## 5. Dọn branch

Chỉ sau khi main đã push và được xác minh:

1. Xác nhận mọi commit của branch đã nằm trong `origin/main`.
2. Xác nhận local và remote branch cùng SHA, không có commit riêng.
3. Xác nhận không có worktree sử dụng branch.
4. Xóa local bằng `git branch -d`.
5. Xóa remote bằng `git push origin --delete`.

Không force-delete.

## 6. Báo cáo cuối

Báo cáo:

- SHA cuối của `main`, `origin/main`, `ls-remote`.
- Kết quả merge/push.
- Candidate/cache verify.
- Integration gate.
- Hồ sơ phê duyệt.
- Giới hạn năng lực còn OPEN.
- Branch cleanup.
- Working tree sạch.

Không sửa mã sản phẩm.
Không tự mở rộng T11.
Không triển khai họ lăng trụ trong lượt merge này.
Không triển khai phương án B của chóp không tên.
Không mở G16/G06.
Không OCR, không Gemini live.
Không tạo PR.

**Điểm dừng: G05_REGULAR_HEXAGONAL_PYRAMID_MERGED_MAIN_VERIFIED.**

Không tự bắt đầu công việc Cloud tiếp theo.
```

## Thực hiện

- Trước merge: `git fetch`; cây sạch, một worktree; `main` = `origin/main` = `f20caf8a` là tổ tiên của `feat/g05-geometry-capability-expansion` = `origin/…` = `55f51395`
  (6 commit, 0 sau). Sau T3 (`0fe806ff`) chỉ có `55f51395`, đổi đúng `docs/` ⇒ T3 kế thừa, không chạy lại. Candidate
  `cf47dd61…` và khoá cache 124 verify trước merge.
- `git merge --ff-only feat/g05-geometry-capability-expansion` trên `main`: `f20caf8a` → `55f51395`.
- Cổng tích hợp (bộ của tiền lệ G04/G05/các run C0) trên worktree tách rời sạch tại `55f51395`:
  `diagnostics/gates_55f51395.log` (candidate `cf47dd61…`, cache 124, `LLM_ONLY`, `routing.py` không đổi, bề mặt mô hình:
  chỉ `product_capability.py` — dòng `foundation_only`, không phải đầu vào băm năng lực; prompt/thẻ văn phạm/lược đồ/IR
  không đổi; lược đồ ×2 trùng byte, audit tài liệu PASS, `diff --check`, node harness 100/0/2).
- `git push origin main` (không force, một lần, không lỗi mạng): `f20caf8a..55f51395`; `main` = `origin/main` = `ls-remote`
  = `55f51395`.
- Dọn nhánh sau khi `main` đã push và xác minh: local = remote = `55f51395`, ⊂ `origin/main`, 0 commit riêng, không
  worktree nào dùng; `git branch -d` và `git push origin --delete` thành công; `git fetch --prune` không còn nhánh `feat/`
  hay `fix/` nào.

## Ghi nhận phạm vi được phê duyệt

- **Năng lực G05 mới (chóp lục giác đều):** reader đọc kí hiệu chuẩn và các cách diễn đạt đã đăng ký; template T11 với metric
  suy từ số đo trong văn bản; 8/8 bài dương phục vụ đúng, C1-certified; 7 refused → served; H5 served sai 1 → served đúng
  6√3; C0: lục giác đều toạ độ hợp lệ được phục vụ, đỉnh lệch trục bị từ chối `SOURCE_SHAPE_CONTRADICTS_COORDINATES`;
  Scene3D 7 đỉnh, 7 mặt, `chart_metric`; renderer kiểm bằng trình duyệt thật cho H6, H8, N4.
- **Đính chính N4 (CHẤP NHẬN):** chứng minh độc lập bằng metric suy từ văn bản (`diagnostics/local_verification/
  hex_independent.py`): S−O ⟂ e1, e2 và |S−O|² = 9 — đỉnh nằm trên pháp tuyến qua tâm đáy, "đứng trên một đỉnh" chỉ là hệ
  toạ độ affine. Ba lớp phân biệt rõ: nhãn gốc `labels.json` giữ nguyên (N4 = từ chối); đính chính nằm ở
  `label_corrections.json`; `oracle.py` vẫn mã hoá luật trước đính chính (chương trình phải "đều") — oracle lịch sử KHÔNG
  được sửa và KHÔNG được tuyên bố là đã cập nhật.
- **Giới hạn (còn OPEN):** `foundation_only` — chưa có kết quả chạy Gemini thật; compiler chưa có họ lục giác; chưa hỗ trợ
  lăng trụ lục giác đều, lăng trụ tam giác đều, chóp lục giác đều không tên, ngũ giác đều, đáy cho bằng góc, đáy lõm; vị trí
  dòng đáp số trên giao diện chưa được kiểm chứng trong lượt này; không tuyên bố giảm token; không tuyên bố năng lực Gemini
  thực tế được cải thiện dựa riêng trên corpus chương trình viết tay.
- **Cache và candidate:** product commit `6c792434`, candidate `cf47dd6142f2d46fd5b9be252fee0d9a7530844d3e1bf07ece47b52b4b433f5a`
  (102 file), `CACHE_VERSION` 124 — bump có căn cứ từ thay đổi đáp số H5 (1 → 6√3) và từ chối C0 (served → refused); T3
  kế thừa từ `0fe806ff`. 0 lượt gọi Gemini live.
