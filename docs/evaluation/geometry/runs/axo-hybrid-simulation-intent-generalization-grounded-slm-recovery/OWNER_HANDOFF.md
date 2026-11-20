# Owner handoff — AXO HYBRID /11

Nhánh `feat/simulation-intent-slm-recovery` (worktree `.superpowers/worktrees/simulation-intent-slm-recovery`), **chưa
merge, chưa push**, `main` không chạm. Mặc định `HYBRID_ROUTE_MODE=live` giữ nguyên.

## Cần owner quyết định

1. **Mở quyền Source Gate cho câu yêu cầu có khai báo lồng.** Đây là chặn lớn nhất: 13/26 ca SLM hỏng ở Source Gate với
   payload đã grounded, và phép tách máy móc cứu 11 ca trong hậu kiểm. Quyền hẹp hiện tại chỉ là `_VAT_MO_PHONG`. Cần thêm:
   đọc phần dữ kiện nằm sau danh từ khối trong cùng mệnh đề yêu cầu ("Vẽ hình chóp S.ABCD có đáy … và tính …"). Mỗi dữ
   kiện vẫn được kiểm trích dẫn như hiện nay.
2. **Cổng miền cho đề không dấu:** áp `handoff/domain_gate_diacritic_free.patch`? Bản vá chỉ bật khi **toàn bộ** đề không
   có dấu, nên không nới gì với tiếng Việt viết bình thường. Đã thử trên V18, C24 (hinh_hoc), đề tin học (tin_hoc) và đề
   trộn dấu (giữ tin_hoc). Lưu ý: áp bản vá chỉ mở cổng miền; parser/SLM/Source Gate vẫn phải đọc được đề không dấu.
   S37, S38, C24 của lượt mù **chưa** được đo sau bản vá.
3. **Planner/engine — hình xác định sai khác đồng dạng** (D02, D03): thiết kế ở `UNDERDETERMINED_SIMULATION_SEMANTICS.md`
   (đơn vị tượng trưng có công khai, chỉ khi `math_goals = []`).
4. **Adapter — nguồn gốc điểm suy ra:** điểm O (tâm đáy / chân đường cao) của khối đều có `origin: "free"`,
   `LAYOUT_DERIVED` ở 7 cảnh. Nên mang lineage "tâm của …" để UI không trình nó như điểm tự do.
5. **Luật Source Gate còn khoá:** "tất cả các cạnh (đều) bằng" (V05, C03, S13, S32); "biểu diễn <đại lượng>" là động từ
   hỏi hay không (Q04, Q05, đây là quyết định hợp đồng); tiêu đề đề thi "Câu 2 (2 điểm)." / "Bài 3." (C26, V16); dấu "!"
   cuối câu yêu cầu.
6. **Merge/push nhánh /11:** chỉ khi owner cho phép rõ ràng. T3 xem `V11_REGRESSION_REPORT.md`.

## Đã làm trong quyền (có thể review từng commit)

| commit | nội dung |
|---|---|
| `806a7d338` | Source Gate `_VAT_MO_PHONG` hẹp (owner duyệt) |
| `0557dcaf6` | parser: văn phạm yêu cầu mô phỏng dùng chung, chọn đích theo nhãn/loại |
| `3e5eb8809` | frontend: hiện câu hỏi làm rõ; không thử lại lỗi runtime đã phân loại |
| `fcf68e91b` | SLM: văn phạm chỉ-mô-phỏng, trích dẫn yêu cầu, cue góc vuông |
| `b15fd9e92` | Scene3D: kéo từ chip vẫn xoay (V17) |
| `5c25c7ea9` | `CACHE_VERSION` 146 + test invalidation |
| `31e6b47c9` | Scene3D: vòng vẽ thức tới khi nhãn tới chỗ (U08) |
| `fad0db5f2`, `18aadea7b` | đóng băng lại candidate (worktree sạch) |

## Mở, trong quyền nhưng để wave sau (cần holdout mới)

- Parser + SLM: nhận câu yêu cầu có khai báo lồng (phần thuộc quyền của việc 1 ở trên).
- Parser: đơn vị viết liền "3cm" (S15). Hiện hệ hỏi lại số đo **đã có** trong đề, tức một câu làm rõ sai.
- Scene3D: V11-VIS-1 (đỉnh gần camera bị cắt ở khung ban đầu, S07/Q01).

Không ghi `APPROVED_BY_USER`. Không có trailer `Co-Authored-By`.
