# AXO: an toàn cache ngữ nghĩa và chuẩn hoá tỉ lệ có chứng chỉ (kèm GEO-BE-001)

| Mục | Giá trị |
|---|---|
| Repo B | `algo-sim`, worktree `local-first-geometry-understanding`, nhánh `feat/local-first-geometry-understanding`; mốc `30884a2e8` (sản phẩm `379d33969`, candidate `54268761e`, `b652e635…`, 116 file, `CACHE_VERSION` 134) — toàn vẹn |
| Repo A | `axo-geometry-library` — **một git worktree của chính kho `algo-sim`** (chung `.git`), nhánh `feat/axo-geometry-library-verification`; mốc `c7a6077fd`; sửa `5a229507b`, biên nhận `312962e1d` (`docs/evaluation/geometry/runs/geo-be-001-display-name-incidence/`) |
| Commit sản phẩm B | `78bdc4c43` cache 134 → 135 · `fb0639a01` số thập phân · `902a3171c` chuẩn hoá tỉ lệ có chứng chỉ |
| Candidate B | lưu ở `901c02702` (trường `commit` `6bb8b0713`, cây sạch), measured_system `243d932765f7…`, 116 file, `CACHE_VERSION` **135** |
| Hợp đồng | planner `/26`, registry `/33`, engine `/24`, `height-invariance-certificate/2`, `output-policy/1`, envelope `/4`, `typed-fact-next/2`: không đổi phiên bản. Thêm giá trị tuỳ chọn `scene_configuration.kind = SIMILARITY_SCALE_ILLUSTRATIVE` |
| Lượt gọi AI | 0 |

Nhãn: **VF** VERIFIED FACT · **INF** INFERENCE · **HYP** HYPOTHESIS · **NM** NOT_MEASURED · **BL** BLOCKED.

## 1. Kết luận chính

- **VF. GEO-BE-001 đã sửa tận gốc ở repo A.**
  - Nguyên nhân: nhánh `points_on_plane` của `display_names._mot_luot` giải đệ quy cả những điểm giao mà định nghĩa của chúng đi qua chính mặt phẳng đang giải. Lời gọi ngược thoát sớm (`dang_giai`), nên câu của điểm rơi về raw ID. Lỗi phụ thuộc thứ tự duyệt.
  - Bản sửa: incidence ≠ định nghĩa; ký hiệu trước, mô tả sau (lượt hai); không còn fallback bằng raw ID; chu trình thật được báo cáo.
  - Catalog nâng cao: đúng 4 trường `role` đổi, sinh lại trùng byte.
  - Chi tiết trong `geo_be_001_final_report.md` của repo A.
- **VF. Cache có thể bypass guard ngữ nghĩa mới, và đã được vá.**
  - Khoá cache của `/api/analyze` được tính **trước** khi chạy parser, chỉ từ chuỗi phiên bản và văn bản đề.
  - Run trước siết guard mà giữ 134. Hệ quả: một cảnh SERVED cũ cho một đề mà guard nay từ chối vẫn được phát lại. Tôi đã tái hiện điều này qua `/api/analyze` thật.
  - Đã nâng `CACHE_VERSION` lên **135**.
  - Lý lẽ "chỉ hàng SERVED được cache nên không cần nâng" của run trước là **sai** khi guard trở nên chặt hơn; tôi ghi nhận đính chính đó.
- **VF. Ca E2E `unnamed_midpoint_distance` là lỗi của bộ đo, không phải của sản phẩm.**
  - Đối tượng khoảng cách chỉ được tạo ở bước `FINAL_RESULT`.
  - Oracle mới đòi đối tượng có mặt ở bước cuối và vắng ở **mọi** bước trước. E2E đạt 18/18.
- **VF. `3,5` nay là một số thập phân.** Lỗi nằm ở `_VAL` của parser. Hợp đồng và gate vốn đã đọc được dạng này.
- **VF. Chuẩn hoá tỉ lệ chỉ chạy khi có chứng chỉ, PO-1..PO-5.**
  - Đơn vị nội bộ là một tham số dựng của engine (đi qua `do_dai`), **không bao giờ** là một lời gọi.
  - Gate đã chứng tỏ nó chặn mọi độ dài chèn vào lời gọi (`UNGROUNDED_VALUE`).
  - Trên REAL27, chỉ **r258** đủ điều kiện. r520 có tự do hình dạng (BC/AB) và bị từ chối; r559 thiếu sự kiện "mọi cạnh bằng nhau" trong biểu diễn và bị từ chối.
- **VF. REAL27:** văn bản 9 → **10/27**, ảnh 5 → **6/27**. Số ca khớp đáp án không đổi: 8/27 và 4/27. Ca thêm r258 hỏi tang, nên được chấm `GOAL_VISUALIZATION_READY_NUMERIC_NOT_ANSWERED`. 0 cảnh sai.

## 2. Trả lời 32 câu hỏi

1. **VF.** Tái hiện tại `c7a6077fd` (repo A), qua đường thật của generator.
2. **VF.** Đúng. `points_on_plane` đệ quy sang F/Q/E, mà `sources` của chúng chứa chính mặt phẳng; `dang_giai` làm lời gọi ngược thoát sớm; `goi_ngan.get(s, s)` rơi về ID; kết quả được ghi nhớ. Test đổi thứ tự (đỏ trước khi sửa) chứng minh lỗi phụ thuộc thứ tự.
3. **VF.** `_mot_luot`: nhánh `points_on_plane`, cách dựng câu, và lượt hai mới; cùng `ten_hien_thi` (tham số `unresolved`) và các hàm trợ giúp `_dua_vao`, `_ky_hieu_diem_rieng`, `_goi_tam`.
4. **VF.** Có. Bước ký hiệu hoàn tất trước; câu nào dựng trên toán hạng còn dang dở thì được dựng lại ở lượt hai.
5. **VF.** Không: quét theo tập ID của từng cảnh, 0/11 mẫu còn rò.
6. **VF.** Có, đúng nguyên văn (test khoá chuỗi).
7. **VF.** Có: `id`, `sources`, `depends`, `producer` không đổi; diff chỉ ở `role`.
8. **VF.** Có: sinh lại trùng byte. Catalog cơ bản có trôi `steps` **có từ trước** (không do bản sửa), không được commit.
9. **VF.** `v9413` 8/8; miền geometry 1370/1371. Ca đỏ là phép quét tĩnh `family-icons.tsx` (commit `65ffb998a` của phiên frontend). **NM**: trình duyệt thật ở repo A.
10. **VF.** A là worktree của cùng kho; `display_names.py` trùng byte giữa hai worktree trước khi sửa. **INF**: worktree B mang cùng lỗi tiềm ẩn; bản sửa **không** được chép sang (quy định của task). Catalog nâng cao chỉ có ở A.
11. **BL.**
    - Đóng băng candidate ở A: cây có 82 file chưa commit của phiên khác.
    - Tài liệu sống của A (CODE_INDEX, EVIDENCE_INDEX) đang bị phiên đó sửa, nên tôi không đụng.
12. **VF.** Có (trước run này): hàng `134:route-d` cho đề nay bị từ chối vẫn được trả. Test tấn công đỏ ở 134 với `'SERVED' != 'SERVED'`.
13. **VF.** Nâng phiên bản chính sách theo giao thức của kho:
    - hằng số trong `main.py`;
    - khoá danh tính (identity lock);
    - bảng danh tính trong `CURRENT_STATE`;
    - 15 chỗ ghim phiên bản hiện hành;
    - test vô hiệu hoá đi qua `/api/analyze` thật.
    Không chọn kiểm lại khi đọc cache (làm cache vô nghĩa với tuyến local-first, và không kiểm lại được hàng do provider trích xuất), cũng không chọn đưa vân tay mã nguồn vào khoá (xung đột với khoá danh tính đã khai) — `semantic_cache_audit.json`.
14. **VF.** Có, 134 → 135. Mọi hàng Route D cũ trượt cache một lần: đề local-first tính lại khoảng 25 ms, đề qua provider tốn một lượt trích xuất. Hợp đồng không đổi.
15. **VF.** Lỗi của test: sản phẩm tạo `kq_q1` ở bước 6/6, không bước nào trước có nó.
16. **VF.** Đã xử lý: `COMP:mc_decimal_value` được phục vụ. 3,5 = 3.5 = 7/2 cho cùng đáp số chính xác; "AB = 3, AC = 4" vẫn là danh sách; "3,5,6", "≈ 3,5" và "3," bị từ chối. Một kỳ vọng cũ coi "3,5" là hỏng đã được viết lại theo yêu cầu B5 (ca hỏng thật "3,5,6" vẫn phải bị từ chối).
17. **VF.** `similarity-scale-certificate/1`:
    - **PO-1** không có số đo có thứ nguyên;
    - **PO-2** chỉ hỏi góc hoặc tỉ số;
    - **PO-3** cố định một đoạn đơn vị cho đúng một cấu hình (engine từ chối hình thiếu xác định);
    - **PO-4** dựng lại với đơn vị 2 và 5 cho cùng đáp số chính xác — chỉ là nhân chứng nhất quán;
    - **PO-5** đơn vị không phải dữ kiện nguồn.
    Lý lẽ: giả thiết bất biến qua phép vị tự và nghiệm duy nhất khi cố định một độ dài ⇒ đúng một lớp đồng dạng ⇒ mục tiêu bất biến chỉ có một giá trị.
18. **VF.** Có: tự do hình dạng trượt PO-3 (tam giác vuông tại B; chiều cao tự do).
19. **VF.** Không, trên bộ đo (`shape_freedom_counterexamples.json`).
20. **VF.** Có:
    - tự do hình dạng, chiều cao tự do, thể tích tuyệt đối, tứ diện đều không cho cạnh ⇒ đều bị từ chối;
    - đề có cho độ dài ⇒ phục vụ **không** chuẩn hoá, cùng góc.
21. **VF.** r258 được phục vụ: chứng chỉ đạt, cos² = 1/3, tính tay khớp, tang `NOT_ANSWERED`. r520 bị từ chối (PO-3, còn BC/AB; **INF**: góc thật là 45° với mọi BC, nhưng chưa có chứng minh bất biến hình dạng). r559 bị từ chối (PO-3, biểu diễn thiếu "mọi cạnh bằng nhau").
22. **VF.** Cảnh chuẩn hoá mới: 5 ca ở COMP (gồm 1 ca đổi tên) và 1 ca REAL27, tất cả qua 59/59 phép kiểm độc lập.
23. **VF.** Số yêu cầu số được đáp ứng đầy đủ trên REAL27 không đổi: 8/27 (văn bản), 4/27 (ảnh). Các ca mới chỉ là mô phỏng.
24. **VF.** Không: đơn vị không xuất hiện trong lời gọi, giả thiết hay provenance; `source_length_supplied = false`; câu báo cho học sinh nói rõ độ dài không phải dữ kiện của đề.
25. **VF.** Không: E2E kiểm DOM, câu báo không chứa chữ số nào, không có giá trị lượng giác.
26. **VF.** 18/18 hàng (4 khung nhìn cho câu gộp, côsin, tang trên hình chuẩn hoá).
27. **VF.**
    - **B:** backend 14 472 PASS, frontend 2 056 PASS kèm build, demo replay, crash audit, docs IA, `freeze_verify` đều PASS.
    - **A:** 13 880 PASS / 16 đỏ trên cây bẩn. Phân loại:
      - 14 ca thuộc nhóm trôi danh tính/candidate;
      - `inv_08` do thay đổi chưa commit của phiên khác (đạt trên archive sạch);
      - 1 ca có từ trước, đỏ cả ở `HEAD^` sạch.
28. **VF.** Không: 0 dòng H-1, 0 dòng W2/W3 khoá (`holdout_protection_audit.json`).
29. **VF.** Publication HEAD BLOCKED (97 phát hiện chờ duyệt); quét theo khoảng commit `30884a2e8..HEAD` PASS. Repo A dùng chung lịch sử và chưa được quét riêng.
30. **VF.**
    - **B:** sản phẩm `902a3171c`, candidate `901c02702`.
    - **A:** sửa `5a229507b`, biên nhận `312962e1d`; đóng băng BLOCKED.
31. **VF.** Không merge, push, deploy; 0 lượt gọi AI live.
32. **INF.**
    - chứng minh bất biến **hình dạng** (r520);
    - biểu diễn "mọi cạnh bằng nhau" cho tứ diện đều không cho cạnh (r559);
    - giới hạn thứ tự mệnh đề có sẵn ("đáy là …" đứng cuối câu bị gate từ chối, `xfail strict`);
    - điểm mô tả ở vị trí giả thiết (R-1);
    - cache không kiểm lại khi đọc — mọi lần siết guard sau này **phải** nâng phiên bản chính sách;
    - mang bản sửa GEO-BE-001 sang worktree B (chờ Owner);
    - không có số đo độc lập (`INDEPENDENT_GENERALIZATION = NOT_MEASURED`).

## 3. Kỳ vọng cũ bị thay và giới hạn

- `test_correctness_ocr_performance`: "AB = 3,5" (cũ coi là hỏng) thay bằng "3,5,6"; đề thập phân nay được phục vụ, V = 35 (kiểm tay).
- `_NOT_REFUSAL` của `test_hybrid_preview_contract`: thêm ba giá trị metadata, theo đúng tiền lệ `HEIGHT_INVARIANT_ILLUSTRATIVE`.
- Mọi con số là số phát triển, trên dữ liệu đã lộ hoặc do agent viết. E2E là trình duyệt tự động. Chi phí chuẩn hoá: khoảng +42 ms cho mỗi đề được chuẩn hoá (ba lần dựng).
