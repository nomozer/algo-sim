# AXO: chứng minh bất biến mục tiêu và ngữ nghĩa tứ diện đều

| Mục | Giá trị |
|---|---|
| Worktree / nhánh | `local-first-geometry-understanding`, `feat/local-first-geometry-understanding`; mốc `07c17fef0` (sản phẩm `902a3171c`, candidate `901c02702`, `243d9327…`, 116 file, CACHE 135) — toàn vẹn, cây sạch |
| Worktree A | `axo-geometry-library` (cùng kho): không đụng tới; HEAD của nó đã sang `3085b182e` (commit của phiên khác) |
| Commit sản phẩm | `8f7f00a2c` tích hợp GEO-BE-001 · `bdc34a89e` bất biến mục tiêu + tứ diện đều + soundness + CACHE 136 |
| Candidate | lưu ở `ade820bd3` (trường `commit` `96ed1461e`, cây sạch), measured_system `2a18f935…`, **117** file (thêm `target_invariance.py`), `CACHE_VERSION` **136** |
| Hợp đồng | planner `/26`, registry `/33`, engine `/24`, `height-invariance-certificate/2`, `output-policy/1`, envelope `/4`, `typed-fact-next/2`: không đổi phiên bản. Thêm giá trị tuỳ chọn `scene_configuration.kind = TARGET_INVARIANT_ILLUSTRATIVE` |
| Lượt gọi AI | 0 |

Nhãn: **VF** VERIFIED FACT · **INF** INFERENCE · **HYP** HYPOTHESIS · **NM** NOT_MEASURED · **BL** BLOCKED.

## 1. Kết luận chính

- **VF. GEO-BE-001 đã vào AlgoSim**, bằng đúng một hunk `display_names.py` của `5a229507b`, không cherry-pick.
  - Blob trước khi sửa của hai worktree trùng nhau (`1c25e32c`), blob sau khi sửa cũng trùng (`8d71e28c`).
  - 22/22 test đạt trên bảng đầu vào thật của hai mẫu đã tái hiện lỗi; 18 test đỏ trước khi tích hợp.
  - Các cảnh do tuyến này tự dựng **không** kích hoạt lỗi (thiết diện do engine tính), nên ở B lỗi chỉ ở dạng tiềm ẩn.
- **VF. Phát hiện và vá một lỗ hổng độ đúng trong chứng chỉ tỉ lệ của run trước.**
  - Bước chuẩn hoá trả kết quả **trước** bước khám phá các nhánh dấu, nên với từ 2 neo độ cao trở lên có thể chứng nhận một nhánh chưa xét.
  - Nay từ chối trường hợp đó, và chứng chỉ khai rõ `certification_level = ENGINE_DOMAIN_CERTIFIED`: duy nhất *trong miền của engine*, không phải chứng minh Euclid đầy đủ.
- **VF. Có chứng minh bất biến mục tiêu khi hình còn tự do hình dạng** (`target-invariance-certificate/1`).
  - Chứng minh tổng hợp có giới hạn trên các lời gọi đã kiểm, với bảng 7 luật đóng; bộ kiểm độc lập kiểm lại từng bước.
  - Hình đại diện chỉ là minh hoạ: `TARGET_INVARIANT_ILLUSTRATIVE`, `unique: false`.
  - **r520 được phục vụ**, ∠ = ∠SBA của tam giác SAB vuông cân, với mọi tỉ số BC/AB.
- **VF. "Tứ diện đều" nay mang đủ nghĩa.**
  - Trước đây nó chỉ là `regular_pyramid` (chóp tam giác đều).
  - Nay có thêm **một** `equal_length` định nghĩa (cạnh bên = cạnh đáy), trích dẫn đúng cụm "tứ diện đều ABCD"; gate chỉ đọc phép bằng nhau này từ chính cụm đó.
  - **r559 được phục vụ** (chuẩn hoá tỉ lệ, côsin `NOT_ANSWERED`).
- **VF. REAL27:**
  - văn bản 10 → **12/27**, ảnh 6 → **7/27**;
  - khớp đáp án số: văn bản 8 → **9/27** (r520 hỏi chính góc), ảnh vẫn 4/27;
  - 0 cảnh sai.
- **BL / NM.** Đánh giá độc lập: NOT_MEASURED. H-1: 0 dòng được mở. Publication HEAD vẫn BLOCKED.

## 2. Trả lời 45 câu hỏi

1. **VF.** Có: HEAD `07c17fef0`, tổ tiên đúng, `--verify` khớp, cây sạch.
2. **VF.** Có: `8f7f00a2c`, chỉ hunk `display_names.py`.
3. **VF.** Có: bảng đầu vào không bị sửa (test `graph_references_are_left_as_ids`), `id/sources/depends/producer` giữ nguyên.
4. **VF.** Không, trên các cảnh và fixture được kiểm.
5. **VF.** Có, 135 → 136. Có guard siết chặt hơn (≥ 2 neo bị từ chối) và envelope đổi (tứ diện đều, tên hiển thị) trong khi khoá Route D không đổi. Hàng `135:route-d` nay trượt cache (`test_cache_target_invariance_invalidation.py`).
6. **VF.** Engine dựng mọi vật bằng luật bắt buộc từ các lời gọi và từ chối khi còn kích thước hoặc nhánh dấu bỏ ngỏ (nay đòi đúng một neo). Đó là duy nhất trong miền của engine, không phải chứng minh Euclid.
7. **VF.** Từng có rủi ro: chuẩn hoá đi trước bước tìm nhánh phản xạ. Đã sửa. **INF**: trên các bộ đo, không ca nào đã phục vụ có ≥ 2 neo.
8. **VF.** Có: tỉ số BC/AB (r520), và cạnh bên của tứ diện đều không cho cạnh (r559, do thiếu biểu diễn).
9. **VF.** `similarity-scale-certificate/1` (nay `ENGINE_DOMAIN_CERTIFIED`), và `target-invariance-certificate/1` (`MATHEMATICALLY_PROVEN` cho mục tiêu, hình đại diện `ENGINE_DOMAIN_CERTIFIED`).
10. **VF.** Có: `verify_target_invariance_certificate` kiểm lại từng bước theo lược đồ luật trên chính các lời gọi, không gọi bộ tìm.
11. **VF.** Không: nhân chứng (hình dạng 2, 5, ½ và tỉ lệ 3) chỉ là phép thử hồi quy; chứng minh là chứng minh tổng hợp.
12. **VF.** Có (chứng chỉ, bộ kiểm độc lập và gate đều đạt).
13. **VF.** Theo tỉ lệ toàn cục và tỉ số BC/AB.
14. **VF.** Có: 4/4 nhân chứng cho cùng cos² = 1/2. Kiểm tay: n(SBC) = (−c, 0, c), n(ABC) = (0, 0, 1), nên cos² = 1/2 với mọi c ≠ 0.
15. **VF.** Có, và đều bị từ chối:
    - chiều cao tự do (bỏ SA = AB);
    - góc SC–(ABC) (đổi theo BC);
    - thể tích tuyệt đối;
    - (SAC)–(ABC): thực ra bằng 90° với mọi cấu hình, nhưng chưa có luật chứng minh nên vẫn bị từ chối, an toàn.
16. **VF.** Có: E2E đạt 24/24, gồm 4 khung nhìn.
17. **VF.** Có: các độ dài minh hoạ nội bộ (cạnh đáy thứ nhất và thứ hai = 1), đi qua `do_dai`, không bao giờ là lời gọi.
18. **VF.** Có: `unique: false`, `source_length_supplied: false`, cùng câu báo "hình minh họa … không phải dữ kiện của đề" (không chứa chữ số).
19. **VF.** Có, với các dạng "Cho tứ diện đều ABCD" và "tứ diện đều PQRS". **NM**: "Tứ diện ABCD là tứ diện đều", "Hình tứ diện đều có các đỉnh A, B, C, D".
20. **VF.** Có: `regular_pyramid` (đáy đều, cạnh bên bằng nhau) cộng một phép bằng nhau cạnh bên = cạnh đáy, nên cả sáu cạnh bằng nhau.
21. **VF.** Có: trích dẫn là chính cụm định nghĩa; quy tắc và gate `_canh_tu_dien_deu` được ghi vào receipt.
22. **VF.** Không: chỉ một phép bằng nhau, không bịa sáu trích dẫn. Gate vẫn từ chối các cụm "tứ diện ABCD" và "tam giác đều BCD".
23. **VF.** Không: "tứ diện ABCD" và "hình chóp tam giác đều S.ABC" vẫn bị từ chối.
24. **VF.** Có.
25. **VF.** Có: dựng bằng primitive trung điểm của kernel, và bộ kiểm cảnh độc lập đạt.
26. **VF.** Một phần:
    - nhánh dấu (≥ 2 neo) bị từ chối;
    - suy biến (đỉnh trùng, đường giao không duy nhất) do engine từ chối;
    - mục tiêu góc giữa các mặt phẳng trong [0°, 90°] không đổi qua phép phản xạ;
    - **NM**: mục tiêu có hướng (góc nhị diện có dấu) dưới tự do hình dạng.
27. **VF.**
    - Bộ kiểm chứng chỉ bắt 8/8 đột biến: luật lạ, sai giao tuyến, sai tia, sai đỉnh góc vuông, bỏ một bước phụ thuộc, đường không nằm trong mặt, thiếu giả thiết cạnh bằng nhau, đổi dữ kiện nguồn.
    - Đột biến cảnh: 36/36.
28. **VF.** Không, trên các bộ có oracle: 85/85 phép kiểm độc lập trên cảnh mới, 124/124 trên các probe cũ.
29. **VF.** 10 → 12/27.
30. **VF.** 6 → 7/27.
31. **VF.** Văn bản 3 (r498, r258, r559); ảnh 3.
32. **VF.** Văn bản 9/27, ảnh 4/27.
33. **VF.** Không (kiểm DOM trong E2E).
34. **VF.** 24/24.
35. **VF.**
    - đề được chứng minh bất biến mục tiêu: khoảng 30 → 112 ms (chứng minh, hình đại diện, 4 nhân chứng);
    - tứ diện đều: khoảng 35 → 76 ms;
    - ca bị từ chối: không tăng.
    Tìm chứng minh có trần `MAX_DERIVED` = 256, vượt thì trả `PROOF_SEARCH_BUDGET_EXCEEDED`.
36. **VF.** Không: heap tăng 3,4 MB sau 12 lần phân tích có lưu lịch sử, số canvas không đổi. **INF**: chưa đủ để kết luận có rò rỉ.
37. **VF.** Backend 14 521 PASS, frontend 2 057 PASS kèm build; demo replay, crash audit, docs IA, `freeze_verify` đều PASS.
38. **VF.** Không.
39. **BL.** Không có.
40. **VF.** 97, đều chờ ngoại lệ.
41. **VF.** `07c17fef0..HEAD`: 55 blob, 0 vi phạm ⇒ PASS; governance BLOCKED.
42. **VF.** `ade820bd3`.
43. **VF.** Không merge, push, deploy; 0 lượt gọi AI live.
44. **INF.** Giới hạn toán học còn lại:
    - luật chứng minh mới chỉ cho góc giữa hai mặt phẳng; chưa có góc đường–mặt, đường–đường, tỉ số dưới tự do hình dạng, cũng chưa có luật hai mặt vuông góc;
    - hình dạng tam giác chỉ được cố định bởi "góc vuông + hai cạnh góc vuông bằng nhau" hoặc "tam giác đều";
    - chứng chỉ tỉ lệ dừng ở mức miền của engine;
    - chưa có mục tiêu có hướng.
45. **INF.** Bước giá trị nhất:
    - về kỹ thuật: mở rộng bảng luật (hai mặt vuông góc; tỉ số cạnh đã cho cố định hình tam giác; góc đường–mặt qua hình chiếu);
    - về đánh giá: dữ liệu độc lập chưa lộ — chỉ có nó mới cho con số khái quát hoá.

## 3. Kỳ vọng cũ bị thay (năng lực mới của run này)

- `test_local_semantic_coverage::test_scale_free_equality…` — bài vuông tại B, SA = AB nay được phục vụ dưới chứng minh. Ý định "không đoán độ dài" được giữ: bỏ SA = AB thì vẫn từ chối `MISSING_DIMENSION`.
- `test_certified_scale_normalization` và `test_compositional_semantics_goals`: các ca tứ diện đều và góc hai mặt phẳng được thay bằng ca tứ diện **không** đều và ca góc **đổi** theo hình dạng.
- Bộ COMP của run này: `scale_shape_free`, `scale_regular_tetra_no_side`, `goal_cos_scale_free` chuyển REFUSE → SERVE (ghi trong `compositional_dev_corpus.py`).

Mọi con số là số phát triển, trên dữ liệu đã lộ hoặc do agent viết; r520 và r559 là ca hồi quy phát triển, không phải ca chưa thấy.
