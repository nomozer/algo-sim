# AXO: ngữ nghĩa mệnh đề ghép và mục tiêu mô phỏng có kiểm chứng

| Mục | Giá trị |
|---|---|
| Nhánh / worktree | `feat/local-first-geometry-understanding` (worktree cố định; không tạo nhánh/worktree, không merge/push/deploy) |
| Mốc bắt đầu | `1a9ee8b0c` (sản phẩm `7315cf3b0`, candidate lưu ở `18a7ba008`, measured_system `1f62a4a4…`, 116 file, `CACHE_VERSION` 134) — đã kiểm lại, toàn vẹn |
| Commit sản phẩm | `13f1b482c`: mệnh đề ghép, thứ tự mệnh đề, mục tiêu lượng giác của góc, chẩn đoán. `379d33969`: ràng chú thích góc vào các điểm đã kiểm |
| Candidate cuối | lưu ở `54268761e` (trường `commit` = `07f29a83a`, cây sạch), sản phẩm `379d33969`, measured_system `b652e635…`, **116** file, `CACHE_VERSION` 134 (không nâng) |
| Hợp đồng | planner `/26`, registry `/33`, engine `/24`, `height-invariance-certificate/2`, `output-policy/1`, envelope `/4`, `typed-fact-next/2`: **không đổi phiên bản**. Thêm trường TUỲ CHỌN `route_d.source_goal_completion` (`source-goal-completion/1`) |
| Lượt gọi model | 0 (`ALLOW_LIVE_AI=0`) |

Nhãn: **VF** VERIFIED FACT · **INF** INFERENCE · **HYP** HYPOTHESIS · **NM** NOT_MEASURED · **BL** BLOCKED.

## 1. Kết luận chính

- **VF. Parser không còn mất mệnh đề phụ một cách im lặng.** Trước run này, parser chạy mọi luật trên cả câu; guard 7k chỉ kiểm vài ký hiệu canh gác (`=`, `∥`, `⊥`, `góc`, "Gọi P là").
  - Một mệnh đề nối bằng dấu phẩy hay "và" không có ký hiệu đó ("…, N thuộc cạnh SB", "tam giác SAB cân", "và hình chiếu vuông góc của S … trùng với trọng tâm …") bị bỏ mà câu vẫn được đánh dấu đọc trọn.
  - Chỉ Source Gate chặn được các ca đó, nên chưa ca nào bị phục vụ sai.
  - Nay mỗi phần có nội dung hình học phải chồng lên trích dẫn của một mục mà chính câu ấy sinh ra; nếu không, ghi `UNREAD_SUBCLAUSE@offset` và câu chỉ được đọc một phần.
  - Trên các bộ đo, **5 mất mát im lặng ở parser nay hiện ra** (4 ca của bộ phát triển, 1 ca REAL27: r460 "tam giác SAB cân").
- **VF. Câu dài nhiều giả thiết và mặt phẳng định nghĩa sau câu hỏi đã được đọc.**
  - "…, M là trung điểm của SA, mặt phẳng (P) đi qua M và song song với mặt đáy." trước đây bị gate từ chối (`UNGROUNDED_VALUE`): mệnh đề (P) "mờ" làm cả câu không gắn được "cạnh a". Nay là một mệnh đề đóng của gate: không chứa số, và vẫn tính là đổi chủ ngữ nên vai trò không nhãn vẫn không được gắn.
  - "…bởi mặt phẳng (P), biết (P) đi qua M …" và "…bởi mặt phẳng (P). Biết (P) …" nay được đọc. Tên chưa định nghĩa vẫn bị từ chối với `UNRESOLVED_REFERENCE`.
  - Các cặp tương đương (câu gộp ↔ tách, (P) ↔ (α), đổi tên đỉnh, đổi thứ tự) cho **cùng** toạ độ thiết diện và cùng đáp số chính xác.
- **VF. Câu hỏi côsin/sin/tang của góc nay là mô phỏng góc, không phải đáp số.**
  - Gate đọc "cos / sin / tan / cot (của) **góc** …" là yêu cầu về *đối tượng góc*, và chỉ đọc như vậy ngay trước cụm góc.
  - Phản hồi mang `source_goal_completion`: `GOAL_VISUALIZATION_READY`, `numeric_source_goal = NOT_ANSWERED`, `source_goal_fully_satisfied = false`, `numeric_answer_shown = false`.
  - Học sinh thấy câu "Axo không tính hộ giá trị côsin", câu này không chứa chữ số nào. Không giá trị lượng giác nào xuất hiện trong DOM.
  - "cos của độ dài", "bình phương côsin", "nửa góc", côsin cho làm giả thiết, hay một yêu cầu khác chưa được trả lời đều vẫn bị từ chối.
  - Không mở `output-policy/2`.
- **VF. REAL27: văn bản 8 → 9/27, ảnh 4 → 5/27.** Ca thêm là r498 (côsin của góc giữa hai mặt phẳng). Ca này được chấm `GOAL_VISUALIZATION_READY_NUMERIC_NOT_ANSWERED` và **không** được tính là trả lời đúng số. Số ca khớp đáp án giữ nguyên 8/27 và 4/27; 0 cảnh sai.
- **VF. Ca REAL27 duy nhất trước đây bị gọi là "thiếu dữ kiện" (r520) thực ra đủ dữ kiện cho góc.** Hai ca côsin/tang r258 và r559 nay đọc được mục tiêu nhưng dừng ở cùng chỗ.
  - Cả ba không cho độ dài nào, mà góc bất biến qua phép đồng dạng.
  - Nay chẩn đoán là `SCALE_NORMALIZATION_UNSUPPORTED`: một năng lực planner còn thiếu, không phải thiếu dữ kiện.
  - Không bịa ra một độ dài để phục vụ chúng.
- **VF. Phép tiêm lỗi tìm ra một lỗ hổng của sản phẩm, và đã sửa.** Adapter /4 kiểm mọi điểm và đại lượng, nhưng không ràng chú thích `angle-construction/1` (đỉnh, tia, chân vuông góc) vào chúng, nên một chân chiếu bị dời vẫn được phục vụ.
  - Nay chú thích phải trùng các điểm đã kiểm; đột biến bị chặn 18/18.
  - Bộ kiểm độc lập của run trước không kiểm trường này. Chỉ biên sản phẩm bắt được 5 đột biến chân vuông góc.
- **BL / NM.** Không có dữ liệu độc lập chưa lộ ⇒ `NEW_INDEPENDENT_EVALUATION = BLOCKED_DATA`, `INDEPENDENT_GENERALIZATION = NOT_MEASURED`. H-1 vẫn niêm phong (0/94 dòng mở). Publication HEAD vẫn `BLOCKED_PENDING_OWNER_REVIEW`.

## 2. Thay đổi sản phẩm

| Tầng | Thay đổi | Khoá bằng |
|---|---|---|
| Parser | `_subclause_spans` / `_unread_subclauses` (guard 7): phần nối bằng dấu phẩy, hoặc bằng "và" mở mệnh đề mới, phải chồng lên trích dẫn của mục câu ấy sinh ra. Danh sách nhãn, số thập phân, ngoặc không bị cắt; yêu cầu "mô phỏng hình (và điểm …)" là lời yêu cầu | `test_compositional_semantics_goals.py` |
| Parser | `_clause_order`: câu hỏi dùng tên mặt phẳng chỉ được định nghĩa ở mệnh đề sau thì được phân tích ngay sau định nghĩa đó. 6c đọc "(P) đi qua …" trần ở đầu mệnh đề "biết" hay đầu câu | như trên |
| Source Gate | `_C_MPDN`: mệnh đề định nghĩa mặt phẳng có tên, không chứa số, là đổi chủ ngữ. Câu chứa khối hình mà có định nghĩa mặt phẳng do bộ đọc vùng tiền đề đọc (trước đây bị thêm lại thành ngữ cảnh dựng) | như trên + bộ test gate cũ |
| Source Gate | `_ham_truoc_goc` / `ham_luong_giac_hoi`: hàm lượng giác chỉ được đọc trước cụm GÓC; dòng `_GIUA_HOP_LE` cũ giữ nguyên, nên phép tiêm lỗi cũ vẫn bắn trúng | `test_hybrid_ask_operand_binding.py` |
| Adapter /4 | `source_goal_completion` (chỉ có mặt khi cần) và `_angle_construction_bound` | test trên + `numeric-goal-not-answered.test.tsx` |
| Chẩn đoán | `FREE_POINT_UNDERDETERMINED`, `UNSUPPORTED_POINT_CONSTRUCTION`, `DESCRIBED_POINT_IN_PREMISE_UNSUPPORTED`, `SCALE_NORMALIZATION_UNSUPPORTED`; nguyên nhân đọc từ chính phần chưa đọc | `test_compositional_semantics_goals.py` |
| Frontend | Kiểm bản ghi (bản ghi tự xưng đã trả lời / đã hiện số ⇒ từ chối view); câu `#stage-numeric-goal-note` | `numeric-goal-not-answered.test.tsx` |

**Hai kỳ vọng cũ bị thay** (không xoá phép kiểm, mà chuyển thành khẳng định mới), vì task này đổi quyết định sản phẩm:
- `test_hybrid_ask_operand_binding`: "Tính sin góc giữa SC và (ABCD)." trước đây khẳng định bị từ chối. Nay khẳng định ca này được phục vụ dạng góc, `ham_luong_giac_hoi` trả `sin`, còn "bình phương sin" và "nửa góc" vẫn bị từ chối.
- `test_semantic_failure_diagnostics`: ca côsin được thay bằng "bình phương côsin" (vẫn `UNSUPPORTED_GOAL_FUNCTION`).

`CACHE_VERSION` 134 không nâng, vì chỉ hàng SERVED được cache:
- mọi đề mới được phục vụ trước đây đều bị từ chối, nên chưa bao giờ vào cache;
- trên mọi bộ đo, không đề nào đã phục vụ đổi trạng thái hay đáp số;
- trường mới chỉ xuất hiện trên đề lượng giác.

Giới hạn còn lại (**INF**): một đề từng được phục vụ mà nay guard 7 chặt hơn sẽ từ chối, nếu đã nằm trong cache, vẫn có thể được trả từ cache. Kết quả đó đã qua gate khi được tạo; chưa gặp ca nào như vậy (**NM** ngoài các bộ đo).

## 3. Trả lời 52 câu hỏi

1. **VF.** Toàn vẹn: HEAD `1a9ee8b0c`, `7315cf3b0` và `18a7ba008` là tổ tiên, `--verify` khớp `1f62a4a4…` (116 file), sản phẩm không đổi giữa `7315cf3b0` và HEAD (`baseline_candidate_integrity.json`).
2. **VF.** Không đổi phiên bản hợp đồng nào. Có thêm một trường tuỳ chọn của `/4` (cùng tiền lệ `scene_configuration`) và hai luật văn phạm đóng của gate (registry `/33` giữ nguyên vì không đổi hàm hay đối số).
3. **VF.** Một câu đọc được bất kỳ tổ hợp mệnh đề nào mà từng mệnh đề thuộc các luật hiện có (khối, đáy, ⊥, độ dài, điểm định nghĩa, mặt phẳng có tên, mục tiêu), nối bằng dấu phẩy hoặc "và"; trước đây định nghĩa mặt phẳng trong câu gộp bị gate từ chối. Bộ COMP: 41/43 ca đạt kỳ vọng (trước 29/43).
4. **VF.** Trên các bộ đo thì không: 5 mất mát im lặng ở parser nay bị phát hiện (`compositional_clause_parser_tests.json`). **INF**: phần có nội dung hình học nhưng không chứa từ nào trong `_SUBCLAUSE_CONTENT_RE` vẫn có thể lọt; gate vẫn là lớp chặn thứ hai.
5. **VF.** Có: mệnh đề mở đầu bằng động từ yêu cầu là mục tiêu ("Hãy xác định trung điểm của SC" bị từ chối, không thành định nghĩa); "Chứng minh SA ⊥ đáy" không thành giả thiết.
6. **VF.** Có, cho mặt phẳng có tên (2 cách viết); tên chưa định nghĩa ⇒ `UNRESOLVED_REFERENCE`.
7. **VF.** Một phần: tham chiếu mặt phẳng có tên qua câu; điểm có tên dùng lại qua câu như trước. Tham chiếu ngược kiểu "đó/này" cho đối tượng khác chưa làm.
8. **VF.** Không xây AST mới: dùng lại `ClauseSpan`, `source_coverage`, bộ chẩn đoán và `DescribedPointSpec`.
9. **VF.** Có, nguyên vẹn (R-1 giữ nguyên).
10. **VF.** Trung điểm, trọng tâm, trực tâm, tâm ngoại tiếp, giao hai đường, giao đường–mặt, hình chiếu lên đường / mặt, lồng tối đa 2 tầng; ở vị trí mục tiêu, `through_point` và toán hạng.
11. **VF.** Có, trên bộ đo: khoảng cách từ trung điểm / trọng tâm không tên được phục vụ, bộ kiểm độc lập đạt. Mặt phẳng **không tên** đi qua điểm mô tả trong câu hỏi (`dp_unnamed_through_point`) vẫn chưa đọc được.
12. **VF.** Không: điểm không tên mang id nội bộ `@m1`, `@g1`…, không có nhãn nguồn mới.
13. **VF.** Có: "M thuộc cạnh SC" (không tỉ số, không khoảng cách) ⇒ từ chối `FREE_POINT_UNDERDETERMINED`, không đặt vào trung điểm.
14. **VF.** Những gì engine đã kiểm vẫn được kiểm (giao chéo nhau ⇒ `SKEW_NO_INTERSECTION`, mặt phẳng không duy nhất, định nghĩa trùng ⇒ `INCONSISTENT_FACTS`). Run này không thêm phép dựng mới.
15. **VF.** Không trên bộ đo: mọi ca phục vụ đều qua gate (mỗi dữ kiện có trích dẫn). Quan hệ suy ra (chân vuông góc của phép dựng góc) là điểm phụ có luật khai báo, không phải dữ kiện nguồn.
16. **VF.** Chính sách không đổi (mệnh đề mờ ⇒ không gắn; mọi câu tiền đề phải được đọc; mỗi yêu cầu phải được trả lời). Có thêm hai cách *đọc* đóng: mệnh đề mặt phẳng có tên, và hàm lượng giác trước cụm góc. Cách đọc thứ hai được khai thành trạng thái `NOT_ANSWERED` chứ không coi là đã trả lời.
17. **VF.** COMP: 41/43 ca đạt kỳ vọng (trước 29). DEV37: mệnh đề thiếu 7 → 6. REAL27: thiếu 17 → 18, vì lộ ra 1 mất mát im lặng (r460) — đó là cải thiện về độ trung thực, không phải tụt.
18. **VF.** COMP 8 → 20/43, DEV37 23 → 27/37, PROBES 22 → 23/39.
19. **VF.** 1 (r498), ở dạng trực quan hoá; số ca khớp đáp án không đổi (8/27).
20. **VF.** Không (bộ kiểm cảnh 45/45, 124/124; mọi ca phục vụ qua gate). **NM** ngoài các bộ đo.
21. **VF.** REAL27: 3 ca `UNRECOGNIZED_GEOMETRIC_ENTITY` (r461, r475 là bài toán thực tế ngoài phạm vi; r463 viết khối "ABCDA'B'C'D'" không dấu chấm).
22. **VF.** 0 ca `UNRECOGNIZED_RELATION` (2 ca cũ nay có nguyên nhân cụ thể: r254 điểm mô tả ở vị trí giả thiết, r491 điểm tự do), cộng 2 ca `INCOMPLETE_FACT_EXTRACTION` (r460 tam giác cân không "tại", r513 thiếu dấu chấm).
23. **VF.** 3 (r256 lỗi gõ "đên", r488 thể tích khối chóp con, r538 "cạnh bên" không tên).
24. **VF.** 0 ca thiếu dữ kiện thật trong 18 ca từ chối của REAL27: ca duy nhất trước đây tính là thiếu (r520, `INSUFFICIENT_CONSTRAINTS`) nay là `SCALE_NORMALIZATION_UNSUPPORTED`, cùng nhóm với r258 và r559. **INF**: r491 có điểm tự do (`FREE_POINT_UNDERDETERMINED`) nhưng đáp số có thể bất biến — chưa chứng minh.
25. **VF.** 1 ca planner (r266 `EXACT_DOMAIN_EXCEEDED`), 1 phép đối xứng (r277), 3 ca chuẩn hoá tỉ lệ, cùng nhóm thể tích khối con (r254, r488).
26. **VF.** Có: côsin, sin, tang, côtang của góc (đường–mặt, hai mặt phẳng, hai đường), kể cả dạng trắc nghiệm "… bằng".
27. **VF.** Có: cảnh của câu côsin cho **cùng** `answer_exact` với câu hỏi góc thường (cặp tương đương đạt), và qua mọi kiểm tra của angle-construction (đỉnh trên đường và mặt, chân trên mặt, cạnh góc vuông với mặt, góc vẽ không tù).
28. **VF.** Có: `source_goal_fully_satisfied = false`, `NOT_ANSWERED`, và bộ chấm nghiệm thu tách riêng (`GOAL_VISUALIZATION_READY_NUMERIC_NOT_ANSWERED`).
29. **VF.** Không: E2E kiểm DOM của 13 hàng, không lộ đáp số, không có `cos²`, không có "cos/tang … bằng <số>"; câu báo không chứa chữ số nào.
30. **VF.** Có: yêu cầu chứng minh ⇒ `UNSUPPORTED_GOAL_KIND` (PROOF_NOT_PROVIDED); không có trực quan hoá thay cho chứng minh.
31. **VF.** Không, vì trạng thái hoàn thành nằm gọn trong một trường tuỳ chọn của `/4`, và không giá trị nào được hiển thị.
32. **VF.** Không: probe 60°/120° và nhị diện đạt (124/124 phép kiểm có dấu); góc hai mặt phẳng dùng đúng miền [0°, 90°].
33. **VF.** Không (`holdout_protection_audit.json`).
34. **VF.** Có, 0/94 dòng được mở.
35. **BL.** Không có: `BLOCKED_DATA`.
36. **VF.** Có, trên candidate cuối (`final_candidate_image_segmentation_revalidation.json`).
37. **VF.** Không trên 26 trang ghép (ghép 2 / ghép 3 / hai cột) dựng từ ảnh thật đã lộ. **NM**: ảnh camera.
38. **VF.** Không: 0/25.
39. **VF.** Không: 56/58 dải có hình riêng, 0 khối hình bị chia cho hai bài.
40. **VF.** Luồng mục tiêu: 12/13 hàng đạt (4 khung nhìn cho câu gộp và câu côsin). Hàng hỏng (`unnamed_midpoint_distance`) hỏng vì **công cụ đo** chưa có tiêu chí "đối tượng mục tiêu chỉ xuất hiện ở bước cuối" cho mục tiêu khoảng cách; mọi phép kiểm khác của hàng đó (camera, chọn đoạn vuông góc, không lộ đáp số, không tràn) đều đạt. Tôi không sửa luật sau khi đã thấy kết quả. Chọn vùng ảnh 4/4; câu báo không bao giờ bị giữ lại khi đổi đề (12 lần đổi).
41. **VF.** Có: probe ràng buộc mặt phẳng 36/39 đúng kỳ vọng (trước 35), 0 phục vụ sai; probe thiết diện / giao tuyến / nhị diện 124/124; cảnh mới 45/45; đột biến 18/18.
42. **VF.** Không, trên các bộ có oracle.
43. **VF.** Mọi cổng sản phẩm đạt ở lần cuối: backend 14 452 PASS, frontend 2 055 PASS (kèm build), demo replay, crash audit, docs IA, `freeze_verify`. Lần 1, backend có 1 FAIL (`test_candidate_ghi_dung_commit_va_cay_sach`, manifest đóng băng trên cây bẩn); đã giữ lại trong commit `07f29a83a`.
44. **VF.** Cùng tập đề: phục vụ 24,2 → 26,7 ms (trung vị), từ chối 1,97 → 1,98 ms, `diagnose` 0,12 ms, prepare không đổi. Lần đo 1 bị nhiễu máy (prepare 2,7 → 6,3 s trên mã ingestion không đổi), đã giữ trong `logs/`. **NM**: máy yếu.
45. **VF.** Không: heap tăng 2,9 MB sau 12 lần phân tích có lưu lịch sử, 1,5 MB qua 15 lần duyệt timeline, số canvas không đổi. **INF**: `MEMORY_LEAK = INCONCLUSIVE` (máy dùng chung, headless).
46. **VF.** 97 phát hiện, 97 đang chờ ngoại lệ ⇒ `BLOCKED`; không phát hiện mới.
47. **VF.** `1a9ee8b0c..HEAD`: 44 blob được quét, 0 vi phạm ⇒ scan PASS; governance vẫn `BLOCKED_PENDING_OWNER_REVIEW`.
48. **VF.** Lưu ở `54268761e` (trường `commit` `07f29a83a`, cây sạch), sản phẩm `379d33969`, measured_system `b652e635d5497dc3…`. Hai lần đóng băng trước trong run: `cf12c59e1` (sau `13f1b482c`) và `9b16af799`. Lần sau chạy trên cây còn receipt chưa track, nên `test_candidate_ghi_dung_commit_va_cay_sach` đỏ ở hồi quy lần 1 (commit `07f29a83a`); đóng băng lại trên cây sạch, cùng hệ đo.
49. **VF.** Không merge, push, deploy; 0 lượt gọi AI live.
50. **INF.** Theo thứ tự tác động trên đề thật:
    - chuẩn hoá tỉ lệ cho mục tiêu bất biến đồng dạng (3 ca REAL27);
    - điểm mô tả không tên ở vị trí giả thiết (cần hợp đồng R-1 mới);
    - thể tích khối con;
    - phép đối xứng;
    - mặt phẳng không tên trong câu hỏi;
    - số thập phân dấu phẩy ("3,5");
    - "cạnh bên" không tên;
    - tham chiếu "đó/này".
51. **INF.** Đủ cho demo có người hướng dẫn trên các dạng đã đo (khối chuẩn, thiết diện mặt phẳng có tên, khoảng cách, góc, câu hỏi côsin/tang ở dạng trực quan hoá). Chưa đủ cho pilot tự do: không có số đo độc lập, publication đang chặn, chưa đo trên học sinh và ảnh camera.
52. **INF.** Hai bước giá trị nhất:
    - **dữ liệu độc lập chưa lộ cùng một người chấm độc lập** — không có thì mọi con số vẫn chỉ là số phát triển;
    - về kỹ thuật, **chuẩn hoá tỉ lệ có chứng chỉ** (chọn đơn vị cho hình xác định đến đồng dạng khi mục tiêu bất biến, ghi rõ trên cảnh như `scene_configuration`).

## 4. Tính toàn vẹn dữ liệu

- Dữ liệu phát triển: bộ COMP (43 ca, agent viết trong run này, kỳ vọng ghi trước khi đo); DEV37 của run trước; REAL27 và PROBES (đã lộ).
- Không đọc dòng W2/W3 còn khoá; không mở H-1; không có luật nào viết theo mã đề.
- Kỳ vọng cũ bị thay được liệt kê ở §2 và trong `semantic_development_before_after.json`.
- Mọi phép đo chạy trên candidate cuối, trừ:
  - `logs/performance_impact_attempt1.json` — lần đo nhiễu, giữ lại;
  - bảng 2 mất mát im lặng trong lúc phát triển (log phiên).

## 5. Regression và publication

| Cổng | Kết quả |
|---|---|
| backend pytest | **PASS** 14 452 (7 skip, 15 xfail). Lần 1: 1 FAIL (manifest đóng băng trên cây bẩn) — giữ lại |
| frontend test wave | **PASS** 2 055 test / 141 file + build |
| demo replay · crash audit · docs IA | **PASS** |
| freeze verify | **PASS** (`b652e635…`, 116 file) |
| publication HEAD scan | **FAIL / BLOCKED**: 97 vi phạm, 97 chờ ngoại lệ (quyết định của Owner) |
| publication range scan `1a9ee8b0c..HEAD` | **PASS** (44 blob, 0 vi phạm) |

- `PRODUCT_REGRESSION_VERDICT = PASS`.
- `PUBLICATION_HEAD_SCAN_VERDICT = FAIL` (chờ Owner); `PUBLICATION_RANGE_SCAN_VERDICT = PASS`.
- `PUBLICATION_GOVERNANCE_STATUS = BLOCKED_PENDING_OWNER_REVIEW`; `FULL_RELEASE_VERDICT = BLOCKED_GATES_REMAIN`.
- Agent không ghi phê duyệt, không thêm ngoại lệ, không đổi chính sách quét.
- Ba mẫu phê duyệt K-1/R-1/S-2 được gắn lại vào hệ đo mới, chỉ đổi metadata, vẫn `PENDING_OWNER_DECISION`.

## 6. Giới hạn

- Mọi con số là số phát triển, trên dữ liệu đã lộ hoặc do agent viết. Không có số khái quát hoá.
- Trang nhiều đề là bố cục tổng hợp, không phải ảnh camera.
- E2E là trình duyệt tự động, không phải học sinh.
- Bộ kiểm cảnh độc lập không kiểm `perpendicular.foot`; biên sản phẩm kiểm trường này.
- Guard 7 dựa trên danh sách từ mở đầu mệnh đề sau "và" và một biểu thức "có nội dung"; nó chặt hơn trước nhưng không đầy đủ.
