# APPROVAL — tích hợp G05 lăng trụ đều (regular-prisms) vào main và dọn nhánh

Lớp ghi nhận của run `regular-prisms`, 2026-10-10. Ghi bởi agent theo lời người dùng (tiền lệ
`runs/regular-hexagonal-pyramid/APPROVAL.md`); agent không tự phê duyệt, không suy phê duyệt từ kết quả tự động, và không sửa
lịch sử kiểm thử. Phê duyệt này là cho TÍCH HỢP lát G05 lăng trụ tam giác đều / lục giác đều đã nghiệm thu độc lập; KHÔNG
phải tuyên bố năng lực Gemini thực tế, KHÔNG phải phê duyệt lát G05 tiếp theo, compiler-first, phương án B hay G16/G06/OCR.

## Nguyên văn (tin nhắn của người dùng trong phiên, 2026-10-10)

```text
# ALGOSIM — MERGE G05 REGULAR PRISMS INTO MAIN

**MÔI TRƯỜNG: Claude Code LOCAL — Windows.**

Tôi phê duyệt tích hợp `feat/g05-regular-prisms` vào `main`, push remote và dọn nhánh sau khi các điều kiện tích hợp được xác minh.

Đây là lượt TÍCH HỢP bản sản phẩm đã được nghiệm thu độc lập. Không phát triển thêm tính năng.

## 1. Baseline

- Main: `ea85216b`.
- Branch: `feat/g05-regular-prisms`.
- Branch HEAD: `9b783cb4`.
- Product commit: `d8b9da74`.
- Candidate SHA-256: `93077b51d033c198bfb68504e3517f98cb2f9738886f058e687f3562d4520883`.
- Candidate: 102 file.
- `CACHE_VERSION=125`.
- T3 PASS tại `eaeedb38`.
- `LLM_ONLY` mặc định.
- Geometry Compiler opt-in.
- Frontend không thay đổi.

LOCAL đã xác nhận:

- 13/13 bài dương phục vụ đúng, C1-certified.
- 12/12 bài biên từ chối đúng.
- C0 chặn 6 trường hợp lăng trụ tọa độ mâu thuẫn và 2 trường hợp chóp đáy lục giác mâu thuẫn.
- Renderer transform 13/13 PASS.
- Browser visual X4, X5, T1, T5 đạt.
- 49/49 Tier-A không đổi.
- Tám probe lịch sử byte-identical.
- 64/64 test mới.
- Node harness 102/102.
- T3: 7729 pytest passed, 1 skipped, 2 deselected; 1040 vitest passed; build, demo và crash surface PASS.

## 2. Kiểm tra trước merge

Đọc:

- `AGENTS.md`.
- `docs/RULES.md`.
- Quy trình tích hợp repository.
- `docs/evaluation/geometry/runs/regular-prisms/`.
- `handoff.md`, `run.json`, `report.md`.
- Hồ sơ candidate, cache và nghiệm thu LOCAL.

Thực hiện:

1. Kiểm tra Git working tree sạch.
2. Fetch remote.
3. Xác minh `main = origin/main = ea85216b`.
4. Xác minh branch local = remote = `9b783cb4`.
5. Xác minh ancestry và không có commit ngoài phạm vi.
6. Kiểm tra mọi commit sau T3 `eaeedb38`.
7. Chỉ kế thừa T3 nếu các commit sau đó chỉ thay đổi tài liệu/hồ sơ, không ảnh hưởng mã sản phẩm, kiểm thử, candidate hay môi trường xác định kết quả.
8. Chạy candidate `--verify`.
9. Chạy cache identity lock `--verify`.
10. Kiểm tra không có thay đổi ngoài phạm vi đã nghiệm thu.

Nếu remote drift, SHA không khớp, cây bẩn hoặc phát hiện thay đổi ảnh hưởng T3, DỪNG để phân tích.

Không reset, không force.

## 3. Merge

Nếu đủ điều kiện:

1. Checkout `main`.
2. Đồng bộ fast-forward an toàn với `origin/main`.
3. Merge:

   `git merge --ff-only feat/g05-regular-prisms`

4. Chạy bộ cổng tích hợp theo tiền lệ G05 gần nhất trên clean detached worktree.
5. Xác minh candidate SHA-256.
6. Xác minh `CACHE_VERSION=125`.
7. Xác minh cache identity lock.
8. Xác minh `LLM_ONLY` vẫn mặc định.
9. Xác minh compiler-first không được bật.
10. Kiểm tra routing không bị thay đổi.
11. Kiểm tra prompt, grammar, schema, IR capability và các phần model-facing.
12. Xuất schema hai lần, đối chiếu byte.
13. Chạy audit tài liệu và `git diff --check`.
14. Chạy node harness, các cổng tích hợp bắt buộc và kiểm tra hồ sơ theo quy định.

Kế thừa T3 tại `eaeedb38` nếu đúng điều kiện repository.

Không chạy lại T3 không cần thiết.

Nếu PASS, push `main` bình thường, không force.

Xác minh:

`main = origin/main = git ls-remote origin refs/heads/main`

## 4. Ghi hồ sơ phê duyệt

Tạo hoặc cập nhật `APPROVAL.md` theo tiền lệ trong:

`docs/evaluation/geometry/runs/regular-prisms/`

Ghi chính xác phê duyệt của người dùng và kết quả tích hợp; không sửa lịch sử kiểm thử.

### Năng lực G05 mới

- Lăng trụ tam giác đều.
- Lăng trụ lục giác đều.
- Template T12.
- Affine frame và text-derived metric.
- 13 bài toán từ refused → served đúng.
- 12 boundary giữ đúng trạng thái refused.
- C1 và oracle độc lập đạt.
- Scene3D lăng trụ tam giác: 6 đỉnh, 5 mặt, 9 cạnh.
- Scene3D lăng trụ lục giác: 12 đỉnh, 8 mặt, 18 cạnh.
- `chart_metric` được renderer áp dụng đúng.
- Browser visual đạt với X4, X5, T1, T5.

### C0 và cache

- Sáu trường hợp C0 lăng trụ mâu thuẫn được từ chối thay vì phục vụ.
- Hai trường hợp chóp đáy lục giác mâu thuẫn phát hiện ngoài nhãn cũng được từ chối.
- Cache bump 124 → 125 đã kiểm chứng.
- Cache version cũ không tái sử dụng.
- Model-facing surface không thay đổi ngoài phạm vi đã được xác minh.
- Candidate `93077b51…`, product commit `d8b9da74`.

### Những giới hạn còn OPEN

- `foundation_only`: chưa đo Gemini thật.
- Compiler chưa hỗ trợ họ lăng trụ đều T12.
- Chưa hỗ trợ lăng trụ/chóp đều không tên.
- Chưa hỗ trợ lăng trụ xiên đáy đều theo T12.
- Chưa đọc một số cách viết lăng trụ tứ giác đều.
- Chưa đọc một số cách viết lăng trụ tam giác đều không có tiền tố "hình"/"khối".
- Chưa hỗ trợ ngũ giác đều, đáy theo góc, đáy lõm.
- Các khối quá mảnh có thể che hoặc chồng nhãn đỉnh.
- Vị trí dòng đáp số trong giao diện chưa được nghiệm thu.
- Chưa chứng minh tiết kiệm token hoặc tăng hiệu quả Gemini thực tế.

Phân biệt giới hạn năng lực, giới hạn trình bày và lỗi toán học.

Không đánh dấu các giới hạn này là đã giải quyết.

### Hồ sơ trạng thái

Cập nhật theo quy định:

- `APPROVAL.md`.
- `run.json`.
- `STATUS_LEDGER`.
- `CURRENT_STATE`.
- `ROADMAP`.
- `OPEN_ISSUES`.
- `AI_CONTEXT_BUNDLE`.

Nếu cần commit hồ sơ tích hợp, chỉ thay đổi `docs/`.

Commit, push bình thường và xác minh lại SHA của main.

## 5. Dọn branch

Chỉ thực hiện sau khi main đã push và xác minh thành công.

Kiểm tra:

- Toàn bộ branch thuộc `origin/main`.
- Local branch trùng remote.
- Không còn commit riêng.
- Không có worktree sử dụng branch.

Nếu đạt:

`git branch -d feat/g05-regular-prisms`

`git push origin --delete feat/g05-regular-prisms`

Không force-delete.

Chạy fetch/prune theo tiền lệ.

## 6. Dọn tài nguyên tạm

Hai đường dẫn LOCAL báo còn tồn tại:

- `D:/tmp/prism-dist`
- `D:/tmp/prism_local`

Chỉ xử lý sau khi nghiệm thu và merge hoàn tất.

Kiểm tra từng đường dẫn, xác minh đúng tài nguyên tạm do run này tạo ra, không chứa dữ liệu cần giữ và không có tiến trình sử dụng.

Nếu toàn bộ bằng chứng cần thiết đã được lưu trong repository hoặc hồ sơ phù hợp, có thể dọn đúng hai thư mục đã xác minh.

Không xóa toàn bộ `D:/tmp`, không dọn theo wildcard và không thay đổi ACL hoặc quyền sở hữu để ép xóa.

Nếu không chắc về nguồn gốc hoặc nội dung, giữ nguyên và báo cáo.

## 7. Báo cáo cuối

Báo cáo:

- SHA cuối của main, origin/main, ls-remote.
- Kết quả fast-forward và push.
- Candidate/cache verify.
- Integration gates.
- T3 được kế thừa hợp lệ hay phải chạy lại.
- Hồ sơ phê duyệt.
- Các giới hạn còn OPEN.
- Kết quả dọn branch.
- Kết quả dọn thư mục tạm.
- Working tree và worktree list.

Không sửa mã sản phẩm.
Không triển khai lát G05 tiếp theo.
Không bật compiler-first.
Không gọi Gemini live.
Không OCR hoặc G16/G06.
Không triển khai phương án B của chóp không tên.
Không tạo PR.

**Điểm dừng: G05_REGULAR_PRISMS_MERGED_MAIN_VERIFIED.**

Không tự bắt đầu lượt phát triển tiếp theo.
```

## Thực hiện

- Trước merge: `git fetch`; cây sạch, một worktree; `main` = `origin/main` = `ea85216b` là tổ tiên của
  `feat/g05-regular-prisms` = `origin/…` = `9b783cb4` (8 commit, 0 sau). Sau T3 (`eaeedb38`) chỉ có `9b783cb4`, đổi đúng
  `docs/` ⇒ T3 kế thừa, không chạy lại. Phạm vi ngoài `docs/` của cả nhánh: 4 file sản phẩm (`main.py`, `product_capability.py`,
  `assumption_gate.py`, `shape_constraint.py`), khoá cache, ghim test + `test_regular_prisms.py`, `KHAI_LECH`, manifest Tier-A —
  đúng phạm vi đã nghiệm thu. Candidate `93077b51…` và khoá cache 125 verify trước merge.
- `git merge --ff-only feat/g05-regular-prisms` trên `main`: `ea85216b` → `9b783cb4`.
- Cổng tích hợp (bộ của tiền lệ G05 gần nhất, `diagnostics/gates.sh`) trên worktree tách rời sạch tại `9b783cb4`:
  `diagnostics/gates_9b783cb4.log` — candidate `93077b51…`, cache 125, `LLM_ONLY`, `routing.py` không đổi, compiler không
  được tham chiếu từ `app/ai`/`main.py`; bề mặt mô hình: chỉ `product_capability.py` (dòng `foundation_only`, không phải đầu
  vào băm năng lực — môi trường ngữ nghĩa b1714b56… không đổi); prompt/thẻ văn phạm/lược đồ/IR không đổi; lược đồ ×2 trùng
  byte; ngoài thư mục run chỉ `EVALUATION_CANDIDATE.json` + `CANDIDATE_DIVERGENCE.json` (thủ tục đóng băng); 0/12 báo cáo lịch
  sử đổi; `diff --check` sạch; audit tài liệu PASS; node harness 100/0/2.
- `git push origin main` (không force, một lần, không lỗi mạng): `ea85216b..9b783cb4`; `main` = `origin/main` = `ls-remote`
  = `9b783cb4`.
- Dọn nhánh sau khi `main` đã push và xác minh: local = remote = `9b783cb4`, ⊂ `origin/main`, 0 commit riêng, không worktree
  nào dùng; `git branch -d` và `git push origin --delete` thành công; `git fetch --prune`: chỉ còn `main`.

## Ghi nhận phạm vi được phê duyệt

- **Năng lực G05 mới (lăng trụ tam giác đều, lăng trụ lục giác đều):** bộ đọc + khuôn T12 trên khung affine với metric dẫn
  xuất từ đề; 13 bài refused → served đúng (C1, khớp `oracle.py` và kiểm toán độc lập `prism_independent.py`); 12 biên giữ
  refused; Scene3D lăng trụ tam giác 6 đỉnh / 5 mặt / 9 cạnh, lục giác 12 / 8 / 18; renderer áp `chart_metric` đúng
  (`prism_render_check.ts` 13/13); trình duyệt thật X4, X5, T1, T5 đạt.
- **C0 và cache:** 6 đề C0 lăng trụ "… đều" có toạ độ mâu thuẫn nay từ chối `SOURCE_SHAPE_CONTRADICTS_COORDINATES` thay vì
  phục vụ; 2 đề C0 chóp "đáy là lục giác đều" mâu thuẫn toạ độ (phát hiện LOCAL ngoài nhãn) cũng từ chối; `CACHE_VERSION`
  124 → 125 đã kiểm, hàng `policy_version` 124 không được dùng lại; bề mặt mô hình không đổi ngoài phạm vi đã xác minh;
  candidate `93077b51d033c198bfb68504e3517f98cb2f9738886f058e687f3562d4520883`, product commit `d8b9da74`; T3 kế thừa từ
  `eaeedb38`; 0 lượt gọi Gemini live.
- **Giới hạn còn OPEN — không đánh dấu đã giải quyết:**
  - *Giới hạn năng lực:* `foundation_only` (chưa đo Gemini thật); compiler chưa có họ lăng trụ đều T12; chưa hỗ trợ lăng trụ /
    chóp đều không tên; lăng trụ xiên đáy đều không thuộc T12; chưa đọc một số cách viết lăng trụ tứ giác đều ("lăng trụ (đứng)
    tứ giác đều X.Y"); chưa đọc "lăng trụ tam giác đều X.Y" không có tiền tố "hình"/"khối" (đề bị từ chối, không phục vụ sai);
    chưa hỗ trợ ngũ giác đều, đáy theo góc, đáy lõm.
  - *Giới hạn trình bày:* khối quá mảnh (X5, T5) có thể ẩn/chồng nhãn đỉnh — hình học vẫn đúng; vị trí dòng đáp số trên giao
    diện chưa được nghiệm thu.
  - *Tuyên bố không đưa ra:* không chứng minh tiết kiệm token hay hiệu quả Gemini thực tế tăng.
  - *Lỗi toán học:* không phát hiện — mọi hàng phục vụ khớp công thức sách dưới metric dựng độc lập.

## Dọn tài nguyên tạm (sau merge)

- Bằng chứng giữ trong kho trước khi dọn: 16 log hồi quy (8 probe × `ea85216b`/`d8b9da74`) chép vào
  `diagnostics/local_verification/regression/` (ba trong số đó chưa có bản commit ở run gốc); diff fixture Tier-A trùng byte
  `cache/fixture_diff.json` của Cloud; log probe nhãn/ngoài nhãn trùng byte log Cloud đã commit; log đóng băng, T3, ảnh, log
  probe LOCAL đã commit ở `9b783cb4`. Phần còn lại (cảnh JSON, fixture trình duyệt, bundle `render_check.mjs`) dựng lại được
  bằng các script đã commit.
- `D:/tmp/prism-dist` (bản build tạm cho `vite preview`) và `D:/tmp/prism_local` (đầu ra probe/kiểm của lượt LOCAL) — do run
  này tạo, không tiến trình nào dùng (cổng 4792 trống) — đã xoá đúng hai đường dẫn này (`Remove-Item -LiteralPath`), không
  wildcard, không đổi ACL. `D:/tmp/prism_labels.json` (bản sao `labels.json` của run) ngoài danh sách được duyệt ⇒ giữ nguyên.
