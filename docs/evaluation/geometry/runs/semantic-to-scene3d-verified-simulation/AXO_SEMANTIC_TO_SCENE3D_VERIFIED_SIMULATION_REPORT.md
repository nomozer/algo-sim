# AXO: từ ngữ nghĩa đến Scene3D, mô phỏng hình học có kiểm chứng

| Mục | Giá trị |
|---|---|
| Nhánh / worktree | `feat/local-first-geometry-understanding` (worktree cố định; không tạo nhánh/worktree, không merge/push/deploy) |
| Mốc bắt đầu | `8a5a54e37` (candidate `dcad65e5e`, measured_system `1cc979f5…`, `CACHE_VERSION` 132) |
| Commit sản phẩm | `5958df73d` phép dựng góc + cache 133 · `6e3989ba5` ba luật parser · `70e393fd8` nút bước 40 px |
| Candidate | đóng băng tại `15e98444b`, measured_system `b222260d…` (115 file), `CACHE_VERSION` **133** |
| Hợp đồng | planner `/26`, registry `/33`, engine `/24`, envelope `hybrid-route-d-simulation/4`: **không đổi**; thêm trường tuỳ chọn `angle-construction/1` |
| Lượt gọi model | 0 (`ALLOW_LIVE_AI=0`) |

Nhãn: **VF** VERIFIED FACT · **INF** INFERENCE · **HYP** HYPOTHESIS · **NM** NOT_MEASURED · **BL** BLOCKED.

## 1. Kết luận chính

- **VF.** Trước run này, câu hỏi góc khác 90° chỉ dựng được hai vật toán hạng: đường và mặt, hai đường, hoặc hai mặt. Không có hình chiếu, đỉnh góc hay góc phẳng nào, và backend tự báo `ANNOTATION_UNBOUND`. Kết quả là 8/16 đề thăm dò được phục vụ chỉ dừng ở **hình cơ sở** ([semantic_to_scene_gap_matrix.json](semantic_to_scene_gap_matrix.json)).
- **VF.** Nay mọi phép đo góc khác 90° đều mang phép dựng `angle-construction/1`:
  - góc đường–mặt: giao điểm, chân hình chiếu và góc giữa đường với hình chiếu của nó;
  - góc hai đường cắt nhau: dựng tại đỉnh giao điểm;
  - góc hai đường chéo nhau: dùng một đoạn có tên song song, kiểu sách giáo khoa (A′D ∥ B′C ⇒ ∠ACB′);
  - góc nhị diện: hai tia cùng vuông góc giao tuyến tại một điểm.

  Phép dựng chỉ ghép từ primitive kernel sẵn có và **chỉ được phát khi cos² của góc dựng bằng đúng giá trị kernel đo**, tính theo metric khung.
- **VF.** Ở 24 đề thăm dò, số đề dựng được đối tượng đề hỏi (Level 2) tăng từ 8 lên 18. 26 cảnh phục vụ qua 95 phép kiểm bất biến viết độc lập, không lỗi nào. Đồ thị phụ thuộc có 0 vi phạm. Cả hai bộ kiểm đều có cửa sổ chứng: cảnh bị tiêm lỗi thì bị bắt.
- **VF.** E2E trong Chromium thật trên bản build đạt 12/12 ca ở 4 viewport. Phép dựng chỉ hiện ở bước kết luận; xoay, zoom, reset camera và chọn vật đều hoạt động; không có đáp số hay chuỗi cos² nào trên trang.
- **VF.** Nghiệm thu: văn bản phục vụ 8/27, ảnh phục vụ 4/27 sau khi xác nhận mô phỏng. Tất cả đều Level 2 và khớp khoá; 0 cảnh sai.
- **NM.** Chưa có đánh giá trên dữ liệu chưa thấy, và H-1 chưa đo. **BL.** Publication HEAD vẫn chờ Owner.

## 2. Thay đổi sản phẩm

| Commit | Thay đổi | Khoá bằng |
|---|---|---|
| `5958df73d` | `quantity_annotations.gan_dung_goc` (4 quan hệ, tự kiểm); `scene3d._TRUONG` chở trường; renderer `scene3d-angle-construction.ts` (kiểm lại fail-closed, cung trình bày) + `vatDungGoc`; T·p ánh xạ trường mới. Sửa lỗi nhân chứng góc vuông bị đổi thành nhãn "độ dài SA". `CACHE_VERSION` 132→133 vì envelope phục vụ đổi | `test_angle_construction.py` (tính lại độc lập bằng Gram, metamorphic đổi tên/thang đo, suy biến, tiêm lỗi), `test_cache_angle_construction_invalidation.py`, `scene3d-angle-construction.test.ts`, guard thuần trong `scene3d.test.tsx` |
| `6e3989ba5` | Luật parser: ảnh của phép chiếu là điểm có tên định nghĩa tại chỗ (trọng tâm/trung điểm); mặt bên ⟂ đáy; tam giác mặt bên đều; cạnh đa giác đều cho muộn | `test_scene_semantic_rules.py` (đáp số tính tay + 5 phản ví dụ) |
| `70e393fd8` | Nút bước ≥40 px trên màn cảm ứng/hẹp (E2E đo được 26 px) | E2E 390×844 |

## 3. Trả lời 38 câu hỏi

1. **Scene3D hiện có những primitive nào?** *(VF)* Điểm, đường (cắt hiển thị), đoạn, mặt phẳng, đa giác, khối đa diện (chóp, lăng trụ, hộp, lập phương, tứ diện), thiết diện, vật cong. Có thêm đường cao có chứng chỉ vuông góc, hình chiếu điểm lên đường/mặt, đoạn vuông góc chung, hình phụ tự ẩn, và nay là phép dựng góc ([existing_scene3d_capability_audit.json](existing_scene3d_capability_audit.json)).
2. **Primitive nào thiếu thật sự?** *(INF)* Không thiếu primitive kernel nào cho các goal đã nhắm. Phần thiếu nằm ở *phép ghép* (đã thêm cho góc), đường cao của bài mặt bên ⟂ đáy, khối con, và văn phạm parser cho thiết diện/giao tuyến.
3. **Bao nhiêu chức năng đã có mà chưa được nối?** *(VF)* 5: chân hình chiếu cho góc đường–mặt, đỉnh góc hai đường, đường song song cho đường chéo nhau, góc phẳng nhị diện (kernel có đủ, cảnh không dựng), và typed facts `centroid`/`face_perpendicular_base` mà parser local không đọc.
4. **Construction graph đã có nguồn dữ kiện chưa?** *(VF)* Có từ trước: `depends`, `dependency_edges`, `source.provenance`, các bước formation (`depends_on`, `created_ids`, `verification_refs`). Phép dựng góc thuộc loại trợ giúp hiển thị: không sinh typed fact, không vào `depends` ([construction_contract_verification.json](construction_contract_verification.json)).
5. **Có vật nào dựng bằng toạ độ giả định không?** *(VF)* Toạ độ là khung chuẩn do hệ chọn và được đánh dấu `LAYOUT_DERIVED`. Khi mọi độ dài tỉ lệ với a, hệ dựng ở a = 1 và ghi rõ "đơn vị, không phải dữ kiện". Không toạ độ nào quay lại Source Gate.
6. **Giả định biểu diễn được phân loại thế nào?** *(VF/INF)* Có 4 lớp: xác định đầy đủ (phục vụ); xác định tới thang đo (phục vụ nếu có độ dài thuần nhất, ngược lại `MISSING_DIMENSION`); họ tham số (từ chối, `UNDERDETERMINED_POINT`); thiếu dữ kiện cho phép dựng (từ chối hoặc hỏi lại). Cả 6/6 đề thăm dò thiếu xác định đều bị từ chối ([parametric_geometry_safety.json](parametric_geometry_safety.json)).
7. **Hỗ trợ những loại hình chiếu nào?** *(VF)* Điểm lên đường, điểm lên mặt (cho khoảng cách và nay cho góc), và đoạn lên mặt (cạnh đỉnh → chân của góc đường–mặt).
8. **Hỗ trợ những loại giao tuyến nào?** *(VF)* Đường∩mặt và đường∩đường (đỉnh góc), mặt∩mặt (giao tuyến của nhị diện). Cạnh∩mặt / thiết diện có ở kernel nhưng parser local không đọc tới.
9. **Hỗ trợ những loại góc nào?** *(VF)* Đường–mặt, hai đường cắt nhau, hai đường chéo nhau, nhị diện, và góc vuông (nhân chứng có sẵn, ẩn ở chế độ A vì chính nó là đáp số).
10. **Hỗ trợ những loại khoảng cách nào?** *(VF, đã có từ trước)* Điểm–điểm, điểm–đường, điểm–mặt, hai đường chéo nhau (đoạn vuông góc chung).
11. **Có dựng được thiết diện không?** *(VF)* Kernel và cảnh có, mẫu offline có. Nhưng parser local từ chối cả 2 đề thiết diện thăm dò, nên trên tuyến không AI là **chưa**.
12. **Bao nhiêu primitive mới thật sự cần?** *(VF)* 0 primitive kernel; 4 phép ghép.
13. **Có primitive chỉ dùng cho một case không?** *(VF)* Không. Không luật nào gọi case ID hay nhãn đỉnh; test metamorphic đổi tên S.ABCD → T.MNPQ cho cùng phép dựng.
14. **Có kiểm thử suy biến không?** *(VF)* Có: đường song song/nằm trong mặt, hai đường song song, hai mặt song song/trùng, chân trùng đỉnh (góc 90°).
15. **Có kiểm thử bất biến hình học không?** *(VF)* Có: 95 phép kiểm chính xác trên 26 cảnh, gồm chân trên mặt, đoạn ⟂ mặt theo G, tia ⟂ giao tuyến, cos² = đáp số, độ dài khoảng cách. Có thêm metamorphic về đổi tên và đổi thang đo ([scene3d_mathematical_invariants.json](scene3d_mathematical_invariants.json)). Oracle là `AGENT_VERIFIED_DIAGNOSTIC`.
16. **Backend và Scene3D có nhất quán không?** *(VF)* Có. Frontend kiểm lại phép dựng sau T·p ở toạ độ thế giới; với tứ diện đều (G ≠ I), chân hình chiếu trùng trọng tâm đáy trong sai số 1e-9. Sai số này là của chuỗi thập phân ở biên hiển thị, không phải lỗi kernel.
17. **Bao nhiêu đề dựng được hình cơ sở?** *(VF)* Thăm dò: 19/24. Bản chép: 8/27. Ảnh: 4/27.
18. **Bao nhiêu đề dựng được đối tượng goal?** *(VF)* Thăm dò: 18/24 (trước run là 8). Bản chép: 8/8 đề phục vụ. Ảnh: 4/4 đề phục vụ. Còn 1 đề thăm dò ở Level 1: mặt bên ⟂ đáy (thể tích đúng nhưng đường cao không được vẽ).
19. **Bao nhiêu đề đạt mô phỏng tương tác đã kiểm chứng?** *(VF)* 6 loại đề (12 tổ hợp đề × viewport) được kiểm trọn trong trình duyệt. Mức tương tác của từng ảnh: NM.
20. **Bao nhiêu đề bị từ chối đúng?** *(VF/INF)* 6/6 đề thăm dò thiếu xác định. Ở bản chép: 2 từ chối an toàn và 17 chưa hỗ trợ; tất cả đều không phục vụ sai.
21. **Có mô hình sai nào phục vụ như đã kiểm chứng không?** *(VF)* Không có, ít nhất trên mọi tập đã đo.
22. **Có bảo toàn quan hệ khi đổi tham số hợp lệ không?** *(VF)* Không có thao tác đổi tham số; kéo đỉnh nằm ngoài phạm vi theo thiết kế (bất biến #31). Đổi đề thì cảnh được dựng lại từ văn bản; đổi thang đo cho cùng phép dựng.
23. **Có mô phỏng được hình chưa xác định duy nhất không?** *(VF)* Không. Hệ từ chối thay vì vẽ một cấu hình như thể nó là duy nhất.
24. **Có timeline dựng hình không?** *(VF)* Có từ trước (các bước formation, nút ←/→). Phép dựng góc gắn vào bước kết luận của đại lượng.
25. **Timeline có phản ánh dependency graph thật không?** *(VF)* Có. Mọi `depends_on` đều là vật tạo ở bước trước, và vật luôn sinh sau phụ thuộc của nó: 0 vi phạm trên 26 cảnh, có cửa sổ chứng ([construction_dependency_graph_tests.json](construction_dependency_graph_tests.json)).
26. **Camera và chọn vật có ổn định không?** *(VF)* 12/12 ca: xoay và zoom đổi camera, reset về đúng pose ban đầu, chọn vật đặt đúng `selected_id`, không có lỗi trang ([scene3d_interaction_browser_e2e.json](scene3d_interaction_browser_e2e.json)).
27. **Mobile dùng được không?** *(VF)* Ở 390×844 không tràn ngang. Nút bước đo được 26 px; đã nâng lên 40 px và đo lại đạt.
28. **Có lộ đáp án cuối không?** *(VF)* Không: trên trang không có giá trị đáp số hay "cos²" ở bất kỳ ca nào. Phép dựng góc không mang con số.
29. **Bao nhiêu đề mới chưa dùng phát triển được mô phỏng đúng?** *(NM)* Không có dữ liệu chưa thấy nào dùng được mà không mở 94 dòng niêm phong. r559 vẫn bị từ chối; r695 nay đã bị lộ vì là mục tiêu của luật cạnh muộn ([new_external_simulation_evaluation.json](new_external_simulation_evaluation.json)).
30. **H-1 độc lập đã đo chưa?** *(NM)* Chưa.
31. **Có regression ở Parser, Gate, Planner hoặc Kernel không?** Xem §5.
32. **Hiệu năng render và thao tác?** *(VF, máy host headless)* Từ bấm gửi đến canvas có timeline: 351–489 ms. Chuyển bước: trung vị 82 ms, tối đa 164 ms (gồm 2 khung hình). Tuyến backend: trung vị 33 ms, parse 11 ms, envelope trung vị 34,5 KB. Ảnh: upload → mô hình 2,0–2,8 s phía server ([frontend_performance_profile.json](frontend_performance_profile.json)). Máy cấu hình thấp vật lý: NM.
33. **Có rò bộ nhớ không?** *(INF)* Chưa chứng minh có, cũng chưa loại trừ. Sau GC, heap tăng 2,5 MB qua 12 lần phân tích trong một phiên đăng nhập (lịch sử giữ từng envelope). 15 lần đi timeline của cùng một đề không tăng đơn điệu (24,2 → 27,2 → 25,6 MB). Số canvas giữ nguyên ([resource_cleanup_audit.json](resource_cleanup_audit.json)).
34. **Full regression ra sao?** Xem §5.
35. **Publication còn bị chặn không?** *(BL)* Còn: 97 finding / 18 blob chờ Owner.
36. **Candidate đủ điều kiện pilot ở mức nào?** *(INF)* Đủ cho demo có hướng dẫn trên các họ đa diện được hỗ trợ: dựng được đối tượng đề hỏi và chưa có cảnh sai nào. Chưa đủ cho học sinh tự học, vì phủ đề thật thấp (8/27 văn bản, 4/27 ảnh), ảnh luôn cần xác nhận, chưa có dữ liệu chưa thấy và publication đang bị chặn.
37. **Tính năng mô phỏng quan trọng nào chưa hỗ trợ?** *(VF)* Thiết diện và giao tuyến trên tuyến local; khối con; đường cao của bài mặt bên ⟂ đáy; điểm mô tả không tên; hình chỉ xác định tới thang đo khi đề không có độ dài nào; điểm tự do; tương tác tham số.
38. **Bước tiếp theo có giá trị cao nhất?** *(INF)* Đưa thiết diện và giao tuyến lên tuyến local, vì kernel và cảnh đã có và đây là dạng đề hình không gian phổ biến nhất. Sau đó dựng đường cao từ quan hệ mặt bên ⟂ đáy. Song song, Owner quyết định một đợt đánh giá trên dữ liệu chưa thấy và H-1 độc lập.

## 4. Tính toàn vẹn dữ liệu

Đề thăm dò là câu tổng hợp do agent viết, một loại goal mỗi đề. 25 bản chép của controlled-vision và r695 đều đã bị lộ. 94 dòng H-1 niêm phong không bị mở. Không con số nào trong báo cáo này là bằng chứng tổng quát hoá.

## 5. Regression

Chi tiết ở [full_regression_summary.json](full_regression_summary.json); bảng được điền sau khi chạy.

## 6. Giới hạn

Trình duyệt chạy headless trên máy host; xác nhận ảnh là script, không phải học sinh; oracle bất biến do chính agent viết (đường mã độc lập, không phải người kiểm). Chưa có máy cấu hình thấp, PostgreSQL hay Live Vision.
