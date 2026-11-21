# AXO: mặt phẳng xác định bằng ràng buộc, đánh giá trên tập khoá và vùng ảnh thật

| Mục | Giá trị |
|---|---|
| Nhánh / worktree | `feat/local-first-geometry-understanding` (worktree cố định; không tạo nhánh/worktree, không merge/push/deploy) |
| Mốc bắt đầu | `4222f021b` (candidate `f0fa7e359`, sản phẩm `ea4b2a197`, measured_system `dc834af0…`, `CACHE_VERSION` 134) |
| Giao thức đăng ký trước | `60ce483cc`, trước mọi thay đổi sản phẩm ([evaluation_preregistration.json](evaluation_preregistration.json)) |
| Commit sản phẩm | `697b097ac`: luật parser 7c-0b / 6c (đáy) / 6d-0, văn phạm Source Gate cho mặt đặt tên qua điểm–đường, mã mặt phẳng trùng |
| Candidate | đóng băng ở `8852c4070` (manifest commit `da06829fe`), measured_system `040de2fd…` (115 file), `CACHE_VERSION` **134** (không nâng) |
| Hợp đồng | planner `/26`, registry `/33`, engine `/24`, `typed-fact-next/2`, envelope `/4`, output-policy `/1`: **không đổi** |
| Lượt gọi model | 0 (`ALLOW_LIVE_AI=0`) |

Nhãn: **VF** VERIFIED FACT · **INF** INFERENCE · **HYP** HYPOTHESIS · **NM** NOT_MEASURED · **BL** BLOCKED.

## 1. Kết luận chính

- **VF. Không có tập đánh giá mới từ bên ngoài.**
  - VMMU Math đã cạn: 456 dòng, trong đó 94 dòng niêm phong.
  - VNHSGE không có giấy phép. Bản mirror trên HF chỉ ghi "cc", không rõ phiên bản, và không có hình. ViExam trùng nguồn với VMMU.
  - Vì vậy `NEW_LOCKED_EVALUATION = BLOCKED_DATA`.
  - Thay vào đó, tôi đánh giá trên hai bộ holdout nội bộ do AI soạn có tường lửa (W2: 96 đề, W3: 144 đề), có oracle hữu tỉ. Hai bộ này chưa từng chạy qua parser local. Giao thức được đăng ký trước khi sửa mã.
- **VF.** Parser local nay đọc được câu hỏi thiết diện trên mặt phẳng đã định nghĩa:
  - "Xác định/Tìm thiết diện … cắt bởi (P)";
  - "song song với mặt đáy";
  - "(P) chứa AB và đi qua M";
  - "(P) chứa hai đường thẳng cắt nhau".

  Kết quả không cần primitive kernel mới, không cần luật planner mới. Mặt phẳng trùng nhau không còn bị gọi là song song.
- **VF.** Trên đề thăm dò do agent viết, thiết diện tăng từ 2/25 lên 22/25 (đúng kỳ vọng 35/39 so với 15/39 trước). Trong 22 cảnh được phục vụ, 0 phép kiểm độc lập thất bại; tiêm lỗi bị bắt 148/148. E2E trình duyệt đạt 14/14 ở 4 viewport.
- **VF. Kết quả trên tập khoá, chạy đúng một lần: tuyến local chỉ phục vụ đúng 2/120 đề thiết diện viết độc lập** (W2 2/48, W3 0/72; trước là 0/120). Bộ ngữ pháp khớp với cách agent viết đề, không khớp cách người soạn độc lập viết. Kết quả trên đề thăm dò **không** phải bằng chứng tổng quát hoá.
- **VF.** Theo luật đã đăng ký có 2 ca WRONG_SERVED. Kiểm tra hậu nghiệm (đọc 2 lời đề, nay đã lộ) cho thấy cả hai ca chỉ "âm" vì payload trích xuất bị cố ý làm hỏng. Lời đề hợp lệ, và hình được phục vụ khớp chính xác kết quả tính tay (diện tích² 225 và 19 600).
- **VF. Vùng ảnh:**
  - Trên 25 ảnh thật đơn đề, sản phẩm giữ trọn đề cùng hình vẽ ở cả 25 ảnh.
  - Trên trang ghép nhiều đề từ ảnh thật, 5/20 trang bị gộp thành một vùng mà không hỏi người dùng.
- **NM.** H-1 độc lập chưa đo. **BL.** Publication HEAD vẫn chờ Owner.

## 2. Thay đổi sản phẩm (`697b097ac`)

| Thành phần | Thay đổi | Khoá bằng |
|---|---|---|
| Parser 7c-0b | Câu hỏi thiết diện trên mặt phẳng đã định nghĩa bằng tên; tên chưa định nghĩa thì không đọc | `test_plane_constraint_sections.py` |
| Parser 6c | "song song với (mặt phẳng) đáy" = đáy đã khai của khối | idem |
| Parser 6d-0 + Source Gate (`_MAT_TEN_DIEM_RE`, `_CAT_BOI_TEN`, `_CUM_DUNG_THIET_DIEN_TEN`) | Văn phạm đóng cho "(P) chứa XY và qua Z", "(P) qua Z và chứa XY", "(P) chứa hai đường thẳng (cắt nhau) XY và XZ": đúng mặt (XYZ). Bốn nhãn phân biệt hoặc "song song" thì không đọc | idem (đỉnh tính tay, văn phạm, phản ví dụ) |
| Engine `kiem_mat_cat` | Hai mặt trùng nhau → `CONTAINED_INFINITE_INTERSECTION` (mã kernel sẵn có); mặt song song phân biệt giữ `PARALLEL_PLANES` | idem; benchmark phân loại mã |

## 3. Trả lời 50 câu hỏi

1. **HEAD và measured system thực tế?** *(VF)* Sản phẩm `697b097ac`, candidate lưu ở `8852c4070`, measured_system `040de2fd63fb6872…`, 115 file. HEAD cuối ghi trong [run.json](run.json).
2. **Candidate cũ có được bảo toàn không?** *(VF)* Có. `f0fa7e359` / `dc834af0…` khớp `freeze --verify` ở đầu run; mọi SHA được báo cáo đều là tổ tiên của HEAD ([baseline_integrity.json](baseline_integrity.json)).
3. **Bao nhiêu bài đã lộ?** *(VF)*
   - 27 bài nghiệm thu.
   - 362/456 dòng VMMU Math đã xem hoặc sàng lọc.
   - 196 ca benchmark của parser.
   - Mọi đề thăm dò của agent.
   - Mọi lời đề trong `backend/tests`.
   - Thêm 2 lời đề holdout đọc sau khi chạy (W2-N03, W3-N63).

   Xem [dataset_partition_audit.json](dataset_partition_audit.json).
4. **Protocol có được đăng ký trước không?** *(VF)* Có, ở commit `60ce483cc`, trước mọi thay đổi sản phẩm. Bộ chấm được commit ở `e30b72db6`, trước lần chạy duy nhất.
5. **Có nguồn dữ liệu mới hợp lệ không?** *(BL)* Không: `BLOCKED_DATA`.
6. **Ground truth do ai xác minh?** *(VF)* Oracle hữu tỉ của curator AI chạy trong phiên cô lập (W3 có thêm một reviewer AI độc lập). Không có người kiểm ([evaluation_ground_truth_status.json](evaluation_ground_truth_status.json)).
7. **Có bài nào được đánh giá độc lập thật không?** *(INF)* Độc lập về quy trình (AI soạn có tường lửa, oracle viết từ đầu), nhưng không độc lập về người. Không phải H-1, không phải `HUMAN_VERIFIED`.
8. **94 dòng H-1 có còn niêm phong không?** *(VF)* Có: 0 lần tải, xem, OCR; không đọc tên file. Ảnh trang VMMU có thể chứa câu niêm phong cũng không được mở ([sealed_h1_status.json](sealed_h1_status.json)).
9. **Kernel có những phép dựng mặt phẳng nào?** *(VF)* Qua ba điểm; qua điểm ∥ mặt; qua điểm ⊥ đường; qua điểm ∥ hai đường; mặt theo ràng buộc (chứa điểm, ∥ đường, ⊥ mặt) có chứng chỉ hạng affine; cùng giao hai mặt, hình chiếu, thiết diện ([existing_plane_constraint_capability_audit.json](existing_plane_constraint_capability_audit.json)).
10. **Có cần primitive mới không?** *(VF)* Không: 0 primitive, 0 luật planner.
11. **Parser hiểu thêm những ràng buộc nào?** *(VF)* Câu hỏi thiết diện trên mặt đã đặt tên (Xác định / Tìm / Dựng / Vẽ; cắt bởi / tạo bởi / với); "song song với (mặt phẳng) đáy"; đường + điểm (hai thứ tự); hai đường cắt nhau có chung nhãn.
12. **Mặt qua điểm ∥ mặt có dựng đúng không?** *(VF)* Có. Đỉnh trùng kết quả tính tay (trung điểm các cạnh bên, mặt ∥ (SAB), (A′BD) trong lập phương). Điểm nằm trên mặt tham chiếu thì bị từ chối với `DERIVED_PLANE_IS_REFERENCE`.
13. **Mặt qua điểm ⊥ đường có dựng đúng không?** *(VF)* Có. ⊥ SA qua trung điểm và ⊥ AA′ đều cho mặt cắt ở nửa chiều cao; qua B ⊥ AC′ cho (A′BD). Phép kiểm ⊥ theo G đạt.
14. **Mặt qua đường và điểm có dựng đúng không?** *(VF)* Có (ABMN). Điểm nằm trên đường thì bị từ chối với `COLLINEAR_POINTS`.
15. **Có kiểm tính duy nhất không?** *(VF)* Có. Engine dùng chứng chỉ hạng affine (`PLANE_NOT_UNIQUE` / `INCONSISTENT_FACTS`); bộ kiểm độc lập xác nhận quan hệ đã nêu trên từng mặt được phục vụ ([plane_uniqueness_verification.json](plane_uniqueness_verification.json)).
16. **Có ràng buộc mâu thuẫn nào vượt gate không?** *(VF)* Không, trong các tập đã đo.
17. **Bao nhiêu bài mặt phẳng bị từ chối đúng?** *(VF)* Thăm dò: 13/13 (mã: `DERIVED_PLANE_IS_REFERENCE`, `FACT_INCOMPLETE`, `COLLINEAR_POINTS`, `PLANE_NOT_UNIQUE`, `SECTION_PLANE_IS_FACE`, còn lại là không đọc). Các ca thiếu ràng buộc bị từ chối vì không được đọc (`LIVE_AI_DISABLED`), chưa phải `PLANE_NOT_UNIQUE`: mã chưa chính xác. Tập khoá: 118/120 theo luật đã đăng ký.
18. **Bao nhiêu thiết diện mới dựng được?** *(VF)* Thăm dò: 2/25 → 22/25. Tập khoá: 0/120 → 2/120.
19. **Bao nhiêu giao tuyến mới?** *(VF)* 0. Giao tuyến với mặt xác định bằng ràng buộc chưa được hỗ trợ ([constraint_to_intersection_composition.json](constraint_to_intersection_composition.json)).
20. **Có dùng Kernel hiện có không?** *(VF)* Có, toàn bộ.
21. **Có handler theo case ID không?** *(VF)* Không. Có test metamorphic đổi tên đỉnh (T.MNPQ).
22. **Giao suy biến được phân loại thế nào?** *(VF)* Mặt trùng một mặt của khối → `SECTION_PLANE_IS_FACE`. Hai mặt trùng nhau → `CONTAINED_INFINITE_INTERSECTION`. Mặt song song → `PARALLEL_PLANES`. Chạm điểm/cạnh: không cách diễn đạt nào dẫn tới ca này (NM) ([plane_contradiction_and_degenerate_cases.json](plane_contradiction_and_degenerate_cases.json)).
23. **Có phân biệt góc giữa hai mặt và góc nhị diện không?** *(VF)* Có. Góc giữa hai mặt được dựng nhọn (cos có dấu ≥ 0). Câu hỏi góc nhị diện [B, SC, D] hoặc "hai nửa mặt phẳng" không được đọc, và khi bị thay vào payload góc hai mặt thì Source Gate từ chối ([angle_semantics_audit.json](angle_semantics_audit.json)).
24. **Có ca 60°/120° nào sai không?** *(VF)* Không: 60° được vẽ ở cả hai thứ tự mặt; đảo tia bị bắt 3/3.
25. **Có phép dựng nào thiếu provenance không?** *(VF)* Không. Mọi thiết diện phụ thuộc khối và mặt; mặt phụ thuộc ≥ 3 điểm đã dựng. Mutation xoá provenance bị bắt 22/22.
26. **Có mô hình sai nào được phục vụ như VERIFIED không?** *(VF/INF)* Không có cảnh sai hình học nào trong các tập đã đo. Hai ca WRONG_SERVED theo luật là âm vì payload; hình phục vụ đúng với lời đề.
27. **Bộ kiểm có độc lập với mã dựng không?** *(VF)* Độc lập về đường mã (Fraction + Gram G từ envelope; oracle tập khoá do curator viết), nhưng cùng agent: `AGENT_DIAGNOSTIC`.
28. **Mutation bắt được những lỗi nào?** *(VF)* 148/148 trên 8 loại: pháp tuyến, vị trí mặt, điểm thuộc mặt, bỏ đỉnh, nối sai cạnh, thay đỉnh, xoá provenance, đảo tia ([geometry_mutation_verification.json](geometry_mutation_verification.json)). Bộ kiểm tôi viết có hai lỗi, đã sửa trước khi đo: regex `(?:{P}){3,}`, và vectơ dời trùng hướng mặt.
29. **OCR khoanh vùng đề đạt mức nào?** *(VF)* Ảnh thật đơn đề: 24/25 giữ ≥ 98% vết mực. Ca còn lại chỉ mất nhãn "Câu 43.". Bộ phát hiện tách nhầm 11/25 ảnh, nhưng tầng sản phẩm (đếm tiêu đề bằng OCR) giữ cả trang ở cả 11 ảnh ([image_region_detection_evaluation.json](image_region_detection_evaluation.json)).
30. **Có lấy nhầm bài bên cạnh không?** *(VF, ảnh ghép tổng hợp)* Có. 5/20 trang ghép bị gộp thành một vùng mà không hỏi người dùng. Khi chọn vùng đích, vùng đó lẫn > 5% bài bên cạnh ở 13/24 (trang 2 đề) và 21/24 (trang 3 đề).
31. **Có liên kết nhầm hình vẽ không?** *(VF/INF)* Với ảnh đơn, hình vẽ luôn đi cùng đề của nó. Với trang bị gộp, mọi hình vẽ đi cùng mọi đề, nên không xác định được hình nào thuộc bài nào ([diagram_association_evaluation.json](diagram_association_evaluation.json)).
32. **Có bỏ sót dữ kiện chỉ nằm trên hình không?** *(NM)* Không đo riêng trong run này. Fidelity Gate vẫn từ chối dữ kiện chỉ có trên hình.
33. **Bao nhiêu ảnh đi hết tới Scene3D?** *(VF)* 4/27, sau khi xác nhận bằng script. Phân bổ lỗi: 19 dừng ở parser/Source Gate (ngay cả với bản chép đúng), 2 ở dữ kiện OCR, 2 ở xác nhận/khác ([ocr_to_scene_failure_attribution.json](ocr_to_scene_failure_attribution.json)).
34. **Học sinh phải xác nhận hoặc sửa bao nhiêu lần?** *(VF, script)* 100 chỗ được gắn cờ, 26 lần sửa trên 27 ảnh. Đây là xác nhận bằng script, không phải học sinh thật.
35. **Browser E2E đạt bao nhiêu?** *(VF)* 14/14 ([scene3d_browser_e2e.json](scene3d_browser_e2e.json)).
36. **Mobile và timeline có đúng không?** *(VF)*
    - 390×844 và 768×1024: không tràn ngang, nút bước 40 px.
    - Vật goal vắng ở bước đầu, có ở bước cuối.
    - Xoay, zoom, pan, reset camera, chọn vật và bật/tắt hình phụ đều đạt.
37. **Có đáp án cuối nào xuất hiện không?** *(VF)* Không: 0 chuỗi đáp số, 0 "cos²".
38. **Có memory leak được chứng minh không?** *(INF)* `INCONCLUSIVE`. Heap +3,2 MB qua 12 lần phân tích (lịch sử giữ envelope). Đi timeline 15 lần: 23,6 → 24,4 → 27,2 → 25,7 MB, không tăng đơn điệu. Số canvas giữ nguyên ([resource_cleanup_audit.json](resource_cleanup_audit.json)).
39. **Hiệu năng trước/sau?** *(VF, máy host headless)*
    - Tuyến backend trên 12 đề thiết diện: trung vị 1,7 → 39,8 ms. Trước đây các đề này bị từ chối ngay ở bước parse; nay hệ dựng thiết diện thật.
    - Trình duyệt: mô hình đầu tiên hiện sau 414–1 052 ms (1 052 ms là lượt đầu, còn nguội).
    - Chuyển bước: trung vị 118 ms, chậm nhất 255 ms ([performance_impact.json](performance_impact.json)).
    - Máy cấu hình thấp vật lý: NM.
40. **Bao nhiêu bài unseen được mô phỏng đúng?** *(VF)* 2/120 trên holdout nội bộ chưa từng chạy qua parser local. Dữ liệu ngoài mới: NM (`BLOCKED_DATA`) ([unseen_evaluation_results.json](unseen_evaluation_results.json)).
41. **Đã có bằng chứng tổng quát hoá đủ mạnh chưa?** *(VF)* Chưa. Số liệu cho thấy điều ngược lại: luật mới chưa tổng quát hoá sang cách viết độc lập.
42. **Full regression ra sao?** *(VF)* Mọi cổng sản phẩm đạt ngay lần đầu (§5).
43. **Publication HEAD còn bao nhiêu finding?** *(BL)* 97, tất cả đang chờ ngoại lệ.
44. **Publication range scan có PASS không?** *(VF)* Có: `4222f021b..HEAD`, 0 vi phạm. Về quản trị vẫn `BLOCKED_PENDING_OWNER_REVIEW`, vì blob lịch sử `2bfce9c8` (mật khẩu tổng hợp) chưa có quyết định ([publication_gate_status.json](publication_gate_status.json)).
45. **Full release còn BLOCKED không?** *(BL)* Còn: `BLOCKED_GATES_REMAIN`.
46. **Candidate freeze ở đâu?** *(VF)* `8852c4070` (manifest `da06829fe`, sản phẩm `697b097ac`, `040de2fd…`). Template K-1/S-2/R-1 được gắn lại ở `25d37b3d1`, vẫn PENDING ([candidate_freeze.json](candidate_freeze.json)).
47. **Có merge, push, deploy hoặc gọi Gemini live không?** *(VF)* Không có.
48. **Ba giới hạn quan trọng nhất còn lại?** *(VF/INF)*
    1. Parser local chưa tổng quát hoá sang cách viết độc lập (2/120).
    2. Trang nhiều đề không có tiêu đề "Câu N" bị gộp thành một vùng.
    3. Không có dữ liệu ngoài mới, không có người kiểm.

    Ngoài ra: chưa có giao tuyến với mặt xác định bằng ràng buộc; chưa đọc mặt trung trực; ca thiếu ràng buộc chưa trả `PLANE_NOT_UNIQUE`.
49. **Axo đủ điều kiện ở mức nào?** *(INF)* Đủ cho demo có hướng dẫn với các cách diễn đạt đã hỗ trợ, và chưa phục vụ hình sai. Chưa đủ cho pilot tự học: phủ đề viết tự do rất thấp, ảnh nhiều đề có rủi ro lẫn bài, và publication đang bị chặn.
50. **Việc tiếp theo có giá trị cao nhất?** *(INF)* Owner quyết định một nguồn đề có giấy phép rõ ràng và người kiểm độc lập. Về kỹ thuật, trước khi viết thêm luật: đo xem lời đề độc lập thất bại ở mệnh đề nào, mà không đọc lời đề. Ví dụ: thống kê mệnh đề chưa đọc trên một tập phát triển mới tách khỏi tập khoá, rồi mở rộng ngữ pháp theo mẫu thật thay vì theo đề agent tự viết. Song song với đó, cho tầng `prepare` hỏi lại khi trang có từ hai hình vẽ trở lên mà không đọc được tiêu đề.

## 4. Tính toàn vẹn dữ liệu

Đề thăm dò do agent viết, là `NEW_DIAGNOSTIC_DEVELOPMENT`. Hai holdout nội bộ:
- được đăng ký và băm trước;
- chỉ đọc metadata trước khi chạy (bảng thiết kế W2 §1–§2, tên trường, đếm nhóm);
- chạy đúng một lần cho mỗi phía (trước/sau);
- không viết luật nào từ kết quả.

Sau khi chạy, tôi đọc 2 lời đề (W2-N03, W3-N63); hai ca này nay đã lộ. Kiểm tra trùng lặp 5-gram: điểm Jaccard cao nhất 0,63 (W2), 0,45 (W3); không có ca nào là bản sao của đề phát triển. 94 dòng H-1 không bị mở.

## 5. Regression

Chi tiết ở [full_regression_summary.json](full_regression_summary.json). Cây sạch, `ALLOW_LIVE_AI=0`. Verdict của bộ chạy là `INCOMPLETE_OR_FAIL` chỉ vì cổng publication HEAD; verdict tổng là **BLOCKED**.

| Cổng | Kết quả |
|---|---|
| backend pytest | **PASS**: 14 395 passed, 7 skipped, 3 deselected, 15 xfailed |
| frontend `test:wave` | **PASS**: 140 file, 2 047 test; tsc + vite build |
| demo replay · crash audit · docs IA | **PASS** |
| freeze verify | **PASS**: 115 file, `040de2fd…` |
| publication HEAD | **BLOCKED**: 97 `pending_exception` |
| publication range `4222f021b..HEAD` | **PASS**: 0 vi phạm |

Trong quá trình phát triển, một test benchmark đỏ vì mã mới `CONTAINED_INFINITE_INTERSECTION` chưa được phân loại. Đã thêm mã vào bảng phân loại, trước lần chạy chính thức.

## 6. Giới hạn

- Trình duyệt chạy headless trên máy host.
- Xác nhận ảnh là script.
- Ảnh là bản render đề đã lộ; ảnh ghép và ảnh nhiễu là tổng hợp.
- Oracle của agent và của curator đều là AI.
- Chưa có máy cấu hình thấp, PostgreSQL, Live Vision hay học sinh thật.
