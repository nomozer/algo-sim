# AXO HYBRID /15 — Grounded geometry language recovery & local text Model 1 acceptance

Run `grounded-geometry-language-recovery` · branch `feat/grounded-geometry-language-recovery` from `/14` HEAD `034d89681`, in the
shared worktree `.superpowers/worktrees/simulation-intent-slm-recovery` · not merged, not pushed · `main` unchanged (`bc6ff5e33`).
OCR/Vision development is postponed by the owner; this run is text only.

## 1. Trạng thái phát hành

| cờ | giá trị | căn cứ |
|---|---|---|
| `FULL_PRODUCT_GATE_PASS` | **TRUE** | candidate 155 (`cd2a21abc`, `9867d391…`, 127 file): backend `15,122 passed / 0 failed`, vitest `2,345/2,345`, build, demo, crash — [`FULL_T3_CACHE155_RECEIPT.json`](FULL_T3_CACHE155_RECEIPT.json) |
| Hoàn tất văn bản (Holdout-3) | **58/66 = 0.879 ≥ 0.85** | [`LIVE_TEXT_ACCEPTANCE_RESULTS.json`](LIVE_TEXT_ACCEPTANCE_RESULTS.json) |
| Cổng SLM (đã đăng ký) | **FAIL** — `5/38 = 0.13 < 0.30` (số cảnh `5 ≥ 5` đạt) | [`SLM_CONTRIBUTION_AUDIT.json`](SLM_CONTRIBUTION_AUDIT.json) |
| An toàn | `22/22` ca âm từ chối; `0` phục vụ sai / vi phạm grounding / quan hệ chưa kiểm / mục tiêu số bịa / số sai; `0` lượt gọi AI ngoài | cùng tệp |
| `LIVE_TEXT_SIMULATION_ACCEPTED` | **FALSE** | tiêu chí đăng ký gồm cả cổng SLM |
| `LOCAL_TEXT_MODEL1_VERIFIED` | **FALSE** | cổng SLM trượt, còn khoảng trống văn bản — [`MODEL1_TEXT_ROLE_MATRIX.json`](MODEL1_TEXT_ROLE_MATRIX.json) |
| `LOCAL_VISION_REPLACEMENT_VERIFIED` | **FALSE** | OCR/Vision hoãn, không đo |
| `FULL_GEMINI_ROLE_REPLACEMENT_VERIFIED` | **FALSE** | vai trò Vision chưa thay thế |
| `MAIN_MERGE_READY` | **FALSE** | điều kiện thay thế toàn bộ chưa đạt |
| `MAIN_MERGE_COMPLETED` / `REMOTE_PUSH_COMPLETED` | **FALSE** / **FALSE** | — |

## 2. Bộ nghiệm thu Holdout-3 (đóng băng trước mọi sửa)

`77cbce583`: 66 dương (họ A–G + đối chứng sách giáo khoa + đề nhiều câu), 22 âm phản chứng; nhãn đỉnh tham số hoá; oracle nhân chứng
chính xác, đáp số viết tay đối chiếu với đáp số tính từ toạ độ; `0` trùng với 28 905 chuỗi đề / huấn luyện trước đó. Rà soát oracle
độc lập chỉ-đọc ([`holdout-3/ORACLE_REVIEW.json`](holdout-3/ORACLE_REVIEW.json)) sửa N03, N15, G08 **trước** khi đóng băng.
Baseline CACHE 154: parser COMPLETE 28/66, SLM-required 38. Tác giả bộ đề cũng là người sửa sản phẩm ⇒ `EXTERNAL_INDEPENDENCE = NOT_MEASURED`;
bộ đề nhắm đúng các họ đã biết, nên nó đo khả năng phục hồi trên câu mới của họ đã biết, không đo khả năng gặp họ chưa biết
([`holdout-3/PROVENANCE.json`](holdout-3/PROVENANCE.json)).

## 3. Sửa — `cd2a21abc`, `CACHE_VERSION` 154 → 155

Cơ chế dùng lại: bộ chuẩn hoá có kiểm chứng `slm-verified-normalizer` (span gốc, `rule_id`, guard điều kiện/phủ định). Luật mới `VN12`–`VN17`
chỉ viết sang dạng mà parser **và** Source Gate vốn đã kiểm chứng, và chỉ chạy khi parser không đọc trọn văn bản gốc. Chi tiết, điều kiện
không kích hoạt và kết quả theo họ: [`LANGUAGE_RECOVERY_AUDIT.json`](LANGUAGE_RECOVERY_AUDIT.json).

| họ | hoàn tất Holdout-3 |
|---|---|
| A vuông góc từng đôi | 6/10 |
| B một chủ ngữ nhiều vị ngữ | 8/8 |
| C giá trị lần lượt | 8/8 |
| D đẳng thức chuỗi | 6/6 |
| E chiều cao | 5/6 |
| F yêu cầu mô phỏng trần | 6/6 |
| G dữ kiện trong câu hỏi | 7/8 |
| M nhiều câu | 4/6 |
| S đối chứng sách giáo khoa | 8/8 |

**Lỗi an toàn tìm thấy và đã sửa:** ở CACHE 154, "IJ, IK, IL **không** đôi một vuông góc" được AxoV9 hạ thành ba góc vuông, validator và
Source Gate cho qua ⇒ phục vụ sai. Source Gate nay đọc `không (đôi một | từng đôi | cùng …) <quan hệ>` là phủ định. Test đỏ trên 154, xanh trên 155.

Test: 43 test họ câu + 1 test cô lập cache, trong các file chức năng sẵn có (`test_slm_v9_language_closure_and_security.py`, `test_model1_residual_phrasings.py`),
25 đỏ trước sửa; mỗi luật có bộ "không được kích hoạt" (lệch số lượng, khác đoạn, hai khối, góc không chung đỉnh, điều kiện, câu có/không,
yêu cầu bị phủ định).

**Thiết kế cần biết:** sau một phép viết lại, Source Gate kiểm chứng trên văn bản chuẩn hoá, không trên nguyên văn; mỗi luật vì thế là một bước
được tin cậy và có test không-kích-hoạt riêng; provenance trong phản hồi giữ span gốc.

## 4. AxoV9

Quần thể SLM-required đã khoá (38): 25 hoàn tất tất định nhờ luật mới (tiến bộ của hệ, không phải của SLM), 5 hoàn tất bằng AxoV9 live
(C07, D05, G05, M02, M03), 7 AxoV9 tự báo mơ hồ (A01, A02, A03, A05, G08, M05, M06), 1 hạ đúng nhưng Gate từ chối (E02). Với các ca mơ hồ,
dữ kiện đủ và dạng chuẩn của chúng được tuyến tất định dựng đúng ⇒ mất mát nằm ở trích xuất SLM; envelope không lưu token thô nên không
tách được prompt/grammar với trọng số ⇒ giữ AxoV9, không fine-tune.

Các họ A dạng đồng nghĩa ("vuông góc với nhau từng đôi một", "ba cạnh … đôi một vuông góc") được SERVED trong lúc thăm dò là **nhờ AxoV9**,
không phải nhờ luật, nên không có luật tất định cho chúng; trên Holdout-3 AxoV9 báo mơ hồ. Không sửa sau khi thấy kết quả holdout.

## 5. Hạ nguồn (P4)

`XY ⊥ (XZW)` + `XZ ⊥ XW` trong tứ diện: dữ kiện đủ, parser COMPLETE, planner trả `MISSING_DIMENSION` — khoảng trống năng lực planner,
không phải lỗi parser; biến thể thiếu `XZ ⊥ XW` bị từ chối đúng. Không sửa trong /15 (Holdout-3 không có dạng này).

## 6. Hồi quy trên các tập đã lộ (in-process, có gọi AxoV9, chỉ đếm "served")

Holdout-1: 154 → 155: 6/28 → 11/28; Holdout-2: 35/38 (155); ca âm phục vụ 0/13 ở cả hai. Không phải nghiệm thu mù.

## 7. Hiệu năng (máy dev Windows, không khẳng định trên phần cứng khác)

Phục vụ tất định p50/p95 `163/219 ms` (n = 53); SLM phục vụ p50/p95 `5,308/5,473 ms` (n = 5); từ chối ca dương p50 `1,589 ms`; cache ấm p50
`59.9 ms`; đồng thời 2/4 yêu cầu đều HTTP 200; đỉnh bộ nhớ backend `118 MB`, Chromium `600 MB` (`performance.json` của lượt đo).

## 8. Đính chính

Mô tả "replay `runtime=None`, 0 lượt gọi model" trong `runs/local-model1-recovery-offline-vision/FIRST_FAILING_LAYER_AUDIT.json` không đúng cho
các ca parser chưa đọc trọn: `runtime=None` dùng runtime SLM toàn cục. Các ca phục vụ mà audit gọi là tất định vẫn đúng. Bản /14 giữ nguyên;
đính chính ở `LANGUAGE_RECOVERY_AUDIT.json` và `EVIDENCE_INDEX.md`.

## 9. Toàn vẹn candidate

HEAD lúc T3 `657bb2592` · sản phẩm `cd2a21abce499ca82e0500f085bbc63e2934b65c` · tree `9867d39132faca013ab9865c8e7d29c6cb304bdaad24d9dae503f5ff3e9f6274`
· model `73f1484b08b97ed2a1f44e32bcf6610210c7fda51567c4cd0a03d98dffc6cc35` · llama.cpp `b12470` · `CACHE_VERSION 155` (`155:route-d`).
Live và T3 cùng danh tính. Đo trên cây sạch trong **worktree dùng chung** (theo chỉ thị owner), **không** phải worktree detached như CLAUDE.md
yêu cầu cho phép đo có thẩm quyền — khác biệt chính sách này cần owner xác nhận.

## 10. Việc tiếp theo

Cần quyết định của owner: (1) luật tất định cho các đồng nghĩa họ A và tiêu đề "Đề bài / Yêu cầu", Gate cho đáy lăng trụ không tên vuông tại
một đỉnh, planner cho `XY ⊥ (XZW)`, rồi một tập prospective mới; (2) cách nghiệm thu SLM khi hệ tất định đã hấp thụ phần lớn quần thể
SLM-required (mẫu số đăng ký giữ nguyên); (3) OCR/Vision vẫn là điều kiện cho `FULL_GEMINI_ROLE_REPLACEMENT_VERIFIED` và merge `main`.
