# AXO HYBRID /11 — Simulation intent generalization, grounded SLM recovery & live acceptance revalidation

**Kết luận một dòng:** /11 tìm ra và sửa các nguyên nhân hợp đồng khiến SLM của /10 phục vụ 0/20 cảnh. Lượt mù mới trên
app thật cho 4 cảnh SLM sống, đúng toán, cùng 58/58 cảnh phục vụ đúng toán và 0 vi phạm an toàn. Nhưng độ phủ chỉ đạt
**0.659 < 0.85** và tầng SLM chỉ đạt **4/30 < 0.30**. Vì vậy `LIVE_SIMULATION_ACCEPTED = FALSE` và
`GROUNDED_SLM_RECOVERY_VERIFIED = FALSE`. Chặn chính, do holdout mù làm lộ: câu yêu cầu **có khai báo lồng** chưa được
parser, SLM hay Source Gate nhận diện.

Nhánh `feat/simulation-intent-slm-recovery`, chưa merge/push; `main` không chạm; mặc định `live` giữ nguyên.

## Verdict (chi tiết: `V11_RELEASE_READINESS_DECISION.md`)

`SIMULATION_INTENT_GENERALIZATION_VERIFIED = FALSE (một phần)` · `GROUNDED_SLM_RECOVERY_VERIFIED = FALSE` ·
`FULL_STACK_LOCAL_ONLY_VERIFIED = TRUE` · `LIVE_SIMULATION_ACCEPTED = FALSE` · `SCOPED_CUTOVER_READY = FALSE` ·
`SCOPED_CUTOVER_COMPLETED = FALSE` · `BLOCKED_SOURCE_GROUNDING = YES` · `BLOCKED_OWNERSHIP = YES` ·
`BLOCKED_MODEL_EXTRACTION = NO` · `BLOCKED_DOWNSTREAM_CAPABILITY = PARTIAL` · `BLOCKED_VISUAL_INTERACTION = NO` ·
`BLOCKED_PERFORMANCE = NO (host dev)` · `NOT_MEASURED`: độc lập ngoài, RAM 4–8 GiB thật, người học thật, tương đương Gemini.

## Trình tự và bằng chứng

| pha | kết quả | hiện vật |
|---|---|---|
| P0 baseline/ownership | khoá đúng; Construction /2 giống từng byte `03200886a` | `BASELINE_AND_OWNERSHIP_AUDIT.md` |
| P1 SLM20 | 20/20 có nguyên nhân gốc; mô hình đúng ở 17/20 | `SLM20_ROOT_CAUSE_AUDIT.json`, `SLM20_GOLD_INTERVENTION_RESULTS.json`, `V10_CASE_LEVEL_FAILURE_RECONCILIATION.json`, `SOURCE_GATE_REJECTION_TAXONOMY.md`, `MODEL_VS_DOWNSTREAM_CAUSAL_ANALYSIS.md` |
| P2 ý định mô phỏng | văn phạm chung cho parser, Source Gate (hẹp) và SLM | `SIMULATION_INTENT_GENERALIZATION_DESIGN.md`, `PARSER_GENERALIZATION_TEST_RESULTS.json` |
| P3 SLM | văn phạm chỉ-mô-phỏng; ablation | `SLM_GROUNDED_RECOVERY_REPORT.md`, `SLM_RECOVERY_ABLATION.json` |
| P4 underdetermined | đo 5 ca D; thiết kế bàn giao | `UNDERDETERMINED_SIMULATION_SEMANTICS.md` |
| P5 UX | câu hỏi làm rõ hiện trên UI; không thử lại lỗi đã phân loại | `SIMULATION_CLARIFICATION_UX_REPORT.md`, `LOCAL_RUNTIME_RETRY_VALIDATION.md` |
| P6 cache | 145 → 146 | `CACHE_SEMANTIC_IDENTITY_DECISION.md` |
| P7 Scene3D | V17 sửa; U08 sửa (sau lượt mù) | `SCENE3D_INTERACTION_DEFECT_REPORT.md`, `V17_POINTER_INTERACTION_RESULTS.json` |
| P8 lượt mù | 114 ca + I01–I08 | `V11_LIVE_ACCEPTANCE_*`, `V11_SLM_REQUIRED_EVALUATION.json`, `V11_MATHEMATICAL_SCENE_VALIDATION.json`, `V11_BROWSER_RENDER_EVIDENCE.md`, `V11_UI_SCENARIO_RESULTS.json`, `V11_UNDERDETERMINED_RESULTS.json` |
| P9 hiệu năng/mạng | tách tuyến nhanh và SLM; mạng 4 lớp | `V11_FULL_STACK_PERFORMANCE.json`, `V11_NETWORK_ISOLATION_REPORT.md` |
| P10 hồi quy | T3 | `V11_REGRESSION_REPORT.md` |

## 40 câu hỏi bắt buộc

1. **Trong 20 ca SLM của /10, mô hình trích xuất đúng bao nhiêu ca?** 17/20 đúng ngữ nghĩa. 2 ca không biểu đạt được dưới
   văn phạm cũ (V02, V19). 1 ca lỗi mô hình (C25).
2. **Bao nhiêu ca lỗi quote grounding?** 1 ca là nguyên nhân chính (Q10: tiền đề góc vuông trích nhầm mệnh đề), 4 ca là
   nguyên nhân phụ (V06, V08 trích `construct_object` từ câu khai báo; Q04, Q05 lệch trích dẫn mục tiêu).
3. **Bao nhiêu ca bị Source Gate từ chối vì không hiểu ý định mô phỏng?** 8 ca (Q03, Q08, V06, V08, V11, V16, V26, V28).
   Nhánh D xác nhận câu lệnh không được đọc ở 7 ca SIMULATE_ONLY. Thêm 2 ca "biểu diễn <đại lượng>" không được coi là câu
   hỏi (Q04, Q05).
4. **Bao nhiêu ca thật sự vượt năng lực hạ tầng?** 0/20. Nhánh E phục vụ 24/24 ca, đúng theo oracle.
5. **Gold Typed Facts giải được bao nhiêu ca?** Đặt dữ kiện/ý định gold vào payload gần như không cứu được gì: nhánh C 0,
   nhánh D 1 (V13). Lý do là Source Gate kiểm trích dẫn trên đề gốc, nên lỗi văn phạm yêu cầu vẫn còn. Diễn đạt lại chuẩn
   tắc (nhánh E) cứu 24/24, xác nhận nút thắt nằm ở ngôn ngữ đầu vào và văn phạm, không ở planner.
6. **Mở rộng parser cứu được bao nhiêu ca?** Trên SLM20 (đã lộ): 11/20 ca nay được parser phục vụ, đúng toán. Trên lượt
   mù: tầng PARSER_COMPLETE gồm 55/85 ca và hoàn tất 52/55.
7. **Mở rộng parser có tạo false positive không?** Không phục vụ sai: 24/24 ca âm bị từ chối, gồm phủ định "Không/Đừng",
   nhãn lạ `M.PQR` và hai khối cùng lớp. Còn 10 test âm và 5 test biến đổi giữ nghĩa ngoại tuyến. Có một câu làm rõ sai:
   S15 hỏi lại số đo đã có vì "3cm" viết liền.
8. **SLM thật sự đóng góp bao nhiêu cảnh mới?** 4 cảnh trong lượt mù (S19, S36, Q07, C17). Trên SLM20 sau sửa: 1 cảnh
   (Q10).
9. **Bao nhiêu ca SLM được grounding và chứng minh thành công?** 4/30 ở tầng SLM_REQUIRED (mù). Mỗi cảnh qua Source Gate,
   oracle độc lập và kiểm hiển thị/tương tác trên trình duyệt.
10. **Có phát sinh giả thiết không nguồn không?** Không: 0 mục tiêu số bịa trên đề SIMULATE_ONLY, 0 cảnh phục vụ sai, 0
    sai đáp số. Mọi dữ kiện đi qua kiểm trích dẫn.
11. **Có cần fine-tune AxoV9 tiếp không?** Không, ở thời điểm này. Trong 26 ca hỏng, chỉ 1–2 ca do mô hình (S22 `contra`);
    21 ca do hợp đồng hoặc Source Gate, 3 ca do cổng miền.
12. **Cần mô hình lớn hơn không?** Không có bằng chứng. Giới hạn nằm ở văn phạm của parser, SLM và Source Gate. Phép tách
    máy móc cứu 11/26 ca mà không cần mô hình.
13. **Tỉ lệ hoàn tất SIMULATE_ONLY?** 22/39 = 0.564 [0.410, 0.707].
14. **SIMULATE_AND_QUERY?** 5/16 = 0.3125 [0.142, 0.556].
15. **QUERY_WITH_SCENE?** 29/30 = 0.967 [0.833, 0.994].
16. **Có dựng được hình minh hoạ hợp lệ khi thiếu kích thước không?** Không: 0/5 ca minh hoạ. Có 3/5 câu hỏi làm rõ, còn
    D02/D03 hiện "chưa hỗ trợ". Thiết kế đã bàn giao.
17. **Hệ có phân biệt hình minh hoạ với hình xác định duy nhất không?** Chưa có chế độ minh hoạ. Hệ không bao giờ trình
    một hình không duy nhất như hình duy nhất: nó làm rõ hoặc từ chối.
18. **Câu hỏi làm rõ có tới frontend không?** Có (I05; D01, D04, D05, S21, N17 đều hiện câu hỏi). Ngoại lệ là câu hỏi sai
    ở S15.
19. **Đề không dấu được nhận diện đúng không?** Không: S37, S38, C24 bị cổng miền chặn. Bản vá đã bàn giao, chưa áp.
20. **Thử lại khi timeout còn kéo dài bất hợp lý không?** Không: 1 lượt, 504, 45.3 s (đúng hạn chót runtime). /10 là 135 s.
21. **V17 đã giải quyết chưa?** Rồi: nguyên nhân là chip số đo nuốt `pointerdown`. Đã sửa; kéo từ tâm xoay được 4/4.
22. **U08 còn lệch nhãn không?** Build mù lệch 3–4 px kéo dài. Đã tìm nguyên nhân (nhãn trượt dở dang) và sửa `31e6b47c9`:
    0 px (kiểm sau lượt mù).
23. **Cảnh phục vụ còn đúng toán không?** 58/58, 333 quan hệ, 0 vi phạm. 35/35 đáp số.
24. **Có cảnh trông đúng mà sai quan hệ không?** 0.
25. **Có lỗi hiển thị nguồn/suy ra không?** Có: điểm O suy ra được trình như điểm tự do ở 7 cảnh khối đều (adapter, bàn
    giao). Cộng V11-VIS-1: S07/Q01 bị cắt đỉnh B.
26. **Độ trễ SLM của các cảnh phục vụ?** Backend 2866–4015 ms; khứ hồi 2919–4078 ms; khung tương tác đầu 3833–5045 ms.
    Toàn tuyến SLM: p50 2796 / p95 5172 ms.
27. **Thời gian backend và trình duyệt chênh lớn không?** Khứ hồi ≈ backend + 50 ms. Khung nhìn thấy đầu: p50 190 ms /
    p95 3126 ms. Khung tương tác đầu: p50 932 ms. Phần chênh còn lại là dựng WebGL và bố cục, không phải mạng.
28. **Có gọi cloud hoặc lùi ngầm không?** 0 (proxy, bảng TCP, trình duyệt, telemetry).
29. **Lượt mù mới có đạt ngưỡng đã đăng ký không?** Không: 0.659 < 0.85 và SLM 0.133 < 0.30. An toàn, tương tác và từ chối
    an toàn đều đạt.
30. **Tập mới có thật sự độc lập không?** Không độc lập với tác giả: agent viết và khoá trước khi sửa mã
    (`EXTERNAL_INDEPENDENCE = NOT_MEASURED`). 3 ca SPEC_ANTICIPATED (S09, S10, S11) có cách viết lấy từ prompt.
31. **Đã thử trên máy RAM 4–8 GiB thật chưa?** Chưa (`NOT_MEASURED`). Trên host dev, WS tối đa của toàn stack là 2223 MB
    (llama 903 MB, backend 126 MB).
32. **Có cần đổi cache identity không?** Có: 145 → 146, có test nền đỏ và tiêm lỗi.
33. **Có hồi quy ở các tuyến cũ không?** Xem `V11_REGRESSION_REPORT.md` (T3 trong worktree sạch).
34. **Commit sản phẩm /10 đã tích hợp tới đâu?** `7554e2b72` (keep-alive) và `e10697092` (frontend không cần khoá) nằm
    trong lịch sử nhánh /11, được T3 và lượt mù kiểm lại (0 lỗi hạ tầng trên 114 ca). **Chưa** vào `main`.
35. **Ownership còn chặn những gì?** Source Gate ngoài `_VAT_MO_PHONG`, cổng miền, planner/engine (underdetermined),
    adapter (nguồn gốc O), và quyền merge/push/đổi mặc định.
36. **Đủ điều kiện chuẩn bị cutover local-only chưa?** Chưa.
37. **Còn cần fine-tune Model 1 trước khi tích hợp Construction Planner không?** Không. Việc trước tiên là văn phạm câu
    yêu cầu có khai báo lồng.
38. **Việc nào chuyển sang Construction Integration?** Bước trình bày cho quan hệ đã kiểm (V20); lineage cho điểm suy ra
    (O); ProofGraph/StepGraph cho bước dựng phụ.
39. **Việc nào dành cho Model 2?** Chọn và diễn đạt bước trình bày trên đồ thị đã kiểm, so với
    `DeterministicModel2BaselineSelector`. Model 2 không tạo quan hệ.
40. **Giới hạn nào cần công bố cho người dùng?** Đề cần có dấu tiếng Việt. Câu kiểu "Vẽ <khối> có … và tính …" thường bị
    từ chối, nên viết "Cho … . Hãy vẽ hình …". Thiếu kích thước thì hệ hỏi lại hoặc từ chối, chưa vẽ minh hoạ. Tuyến SLM
    mất 3–5 s. Chưa thử trên máy yếu. Tập đánh giá do tác giả soạn.

## Tái lập

| mục | giá trị |
|---|---|
| commit đo | `fec016682` (đóng băng); candidate `fad0db5f2` / `18aadea7b`, hệ đo `13a32060…` (123 file) |
| mô hình | `qwen3-0.6b-axo-v9-q4_k_m` sha256 `73f1484b08b97ed2a1f44e32bcf6610210c7fda51567c4cd0a03d98dffc6cc35`; llama.cpp `b12470` |
| phiên bản | parser `local-geometry-parser/2`; extractor `local-slm-extractor/5`; grounding `slm-grounding-validator/5`; Source Gate theo registry `geometry-functions/33`; cache `146` / `146:route-d` |
| dữ liệu | manifest sha `86136867…`; tiêu chí sha trong `V11_LIVE_ACCEPTANCE_FREEZE.json` |
| oracle | `tools/scene_oracle.py` (độc lập, Fraction, metric Gram; thêm `ratio2`) |
| trình duyệt | Playwright 1.62.1 Chromium headless, 1366×768 |
| lệnh | `tools/freeze_v11_acceptance.py`, `tools/live_browser_acceptance.mjs`, `tools/scene_oracle.py`, `tools/v11_ui_scenarios.mjs`, `tools/aggregate_v11.py`, `tools/v11_slm_stratum_audit.py` (hậu kiểm) |
| môi trường | Windows 11 Pro, CPU, không GPU cho suy luận |
