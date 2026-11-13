# AXO: thiết diện, giao tuyến, an toàn góc nhị diện trên tuyến local

| Mục | Giá trị |
|---|---|
| Nhánh / worktree | `feat/local-first-geometry-understanding` (worktree cố định; không tạo nhánh/worktree, không merge/push/deploy) |
| Mốc bắt đầu | `ffc62f6fe` (candidate `15e98444b`, measured_system `b222260d…`, `CACHE_VERSION` 133) |
| Commit sản phẩm | `420851be6` sửa góc bù · `6aad1f6b8` thiết diện, giao tuyến, đường cao trên tuyến local + cache 134 · `a74aa3325` bộ fixture hybrid-preview mới · `ea4b2a197` sửa census phạm vi (hành vi không đổi) |
| Candidate | đóng băng tại `f0fa7e359` (manifest commit `cf058f0ee`), measured_system `dc834af0…` (115 file), `CACHE_VERSION` **134**; bản đóng băng `89aed139e` trước đó bị thay vì regression lần 1 fail |
| Hợp đồng | planner `/26`, registry `/33`, engine `/24`, envelope `hybrid-route-d-simulation/4`: **không đổi**. `angle-construction/1` thêm trường `angle_domain`; trường tuỳ chọn mới `altitude-construction/1`; TypedFactNext `/2` thêm goal `construct_intersection_line` (snapshot `/1` và fingerprint môi trường `3d5400a5` giữ nguyên) |
| Lượt gọi model | 0 (`ALLOW_LIVE_AI=0`) |

Nhãn: **VF** VERIFIED FACT · **INF** INFERENCE · **HYP** HYPOTHESIS · **NM** NOT_MEASURED · **BL** BLOCKED.

## 1. Kết luận chính

- **VF. Có lỗi thật ở góc giữa hai mặt phẳng.** Với chóp S.ABCD đáy vuông, SA ⟂ đáy, SA = a, góc giữa (SBC) và (SCD) là 60°, nhưng cảnh vẽ góc 120° (nhị diện B–SC–D). Chứng chỉ cũ chỉ so cos², mà cos² 60° = cos² 120° = 1/4, nên lỗi lọt qua. Lỗi xuất hiện ở 3 đề thăm dò (bản gốc, đổi thứ tự hai mặt, đổi tên đỉnh); sau `420851be6` còn 0 ([dihedral_angle_semantic_audit.json](dihedral_angle_semantic_audit.json)).
- **VF.** Thiết diện và giao tuyến hai mặt phẳng nay đi được trên tuyến local từ đề tiếng Việt. Trên đề thăm dò, số thiết diện phục vụ tăng từ 0 lên 9/12 và số giao tuyến từ 0 lên 5/7. Các ca còn lại đều bị từ chối đúng lý do. Không thêm primitive kernel nào, và Source Gate không đổi.
- **VF.** Bài "mặt bên ⟂ đáy" nay có đường cao: chân là hình chiếu kernel của đỉnh, nằm trên giao tuyến của mặt bên với đáy (với SAB đều thì chân là trung điểm AB). Có 5 kiểm chính xác, đáp số thể tích không đổi.
- **VF.** Bộ kiểm độc lập viết bằng Fraction và ma trận Gram của envelope: 31 cảnh, 124 kiểm, 0 lỗi; tiêm lỗi bắt được 52/53. E2E trên Chromium thật đạt 12/12 ca ở 4 viewport, không hiện đáp số.
- **VF.** Nghiệm thu văn bản 8/27 và ảnh 4/27, không đổi so với trước. Corpus 27 bài không có bài thiết diện hay giao tuyến nào, nên phần mới chưa được đo trên đề thật. 0 cảnh sai.
- **NM.** Dữ liệu chưa thấy và H-1 độc lập chưa đo. **BL.** Publication HEAD vẫn chờ Owner.

## 2. Thay đổi sản phẩm

| Commit | Thay đổi | Khoá bằng |
|---|---|---|
| `420851be6` | `quantity_annotations`: nếu hai tia mở góc tù thì đảo tia thứ hai, ưu tiên điểm có tên trên tia đối. Chứng chỉ mới yêu cầu cos có dấu ≥ 0 **và** cos² = giá trị đo. Thêm `angle_domain = "[0°, 90°]"` cho mọi quan hệ (đường–mặt, hai đường cắt nhau/chéo nhau, hai mặt). Renderer từ chối tia tù hoặc thiếu domain (fail-closed) | `test_angle_construction_domain.py` (15/18 đỏ trước khi sửa), `scene3d-angle-construction.test.ts` |
| `6aad1f6b8` | Parser local có luật 7c-0 (thiết diện cắt bởi mặt phẳng ba điểm có tên) và 7c-1 (giao tuyến của hai mặt phẳng). TypedFactNext `/2` thêm goal `construct_intersection_line`, bridge ánh xạ sang fact planner `intersection_line` đã có. `gan_duong_cao` ghi `altitude-construction/1` cho thể tích chóp; renderer kiểm lại rồi vẽ. `CACHE_VERSION` 133→134 | `test_section_intersection_local.py` (23 test, oracle thiết diện độc lập), `test_cache_dihedral_altitude_invalidation.py` |
| `a74aa3325` | Bộ fixture hybrid-preview mới `fixtures-dihedral-altitude/`; bộ cũ giữ nguyên | `tests/test_hybrid_preview_fixtures.py` |
| `ea4b2a197` | Nhãn hai mặt phẳng của goal giao tuyến được gộp vào tham chiếu trên một dòng riêng, nên dòng mà mutant `remove_apex_ownership` nhắm tới giữ nguyên. `SimulationGoalSpecV2` được phân loại trong phần mở rộng census (chỉ cộng thêm). Bản ghi phạm vi không đổi | `test_scope_census_closure.py` (+2 test phạm vi `target_planes`), [schema-census-extension.json](schema-census-extension.json) |

## 3. Trả lời 40 câu hỏi

1. **Phép dựng góc nhị diện trước đây có nguy cơ chọn sai góc bù không?** *(VF)* Có. Tia được chọn theo điểm có tên đầu tiên, và chứng chỉ chỉ so cos², nên một góc tù vẫn qua kiểm.
2. **Có phát hiện lỗi thực tế không?** *(VF)* Có: (SBC)/(SCD) bị vẽ 120° thay vì 60°, ở cả bản gốc, bản đổi thứ tự và bản đổi tên. Đáp số hiển thị ở chế độ khác vẫn đúng, vì kernel đo góc không định hướng; chỉ hình vẽ sai.
3. **Validator cũ kiểm tra điều gì?** *(VF)* cos² của góc dựng bằng giá trị kernel đo (theo metric G), tia vuông góc giao tuyến, và điểm nằm trên mặt.
4. **Validator mới kiểm tra thêm điều gì?** *(VF)* Tích vô hướng có dấu của hai tia phải ≥ 0 (`drawn_angle_not_obtuse`) và phải có `angle_domain`. Frontend kiểm lại cả hai sau phép biến đổi hiển thị; thiếu một trong hai thì không vẽ.
5. **Các phản ví dụ 60°/120° có bị phân biệt đúng không?** *(VF)* Có. 60° được vẽ ở cả hai thứ tự mặt và khi đổi tên. Cặp mặt tổng hợp 45°/135° được vẽ 45°; hai đường có điểm tên mở 135° được vẽ 45°; giá trị cos sai bị từ chối. Đảo tia trong mutation bị bắt 12/12 ([dihedral_complementary_angle_counterexamples.json](dihedral_complementary_angle_counterexamples.json)).
6. **Có breaking contract nào không?** *(VF)* Không. Mọi trường mới đều là trường cộng thêm; planner, registry, engine và envelope giữ phiên bản. Envelope cũ không có `angle_domain` thì không được vẽ, và cache 134 cách ly mọi row 133.
7. **Kernel có sẵn những phép giao nào?** *(VF)* Đường∩mặt (một điểm / song song / nằm trong), mặt∩mặt (`intersect_plane_plane`), đường∩đường, hình chiếu điểm lên đường/mặt, thiết diện khối đa diện bởi mặt ba điểm (planner `section` + chứng chỉ khép kín của engine, cạnh dựng theo từng mặt) ([existing_intersection_section_capability_audit.json](existing_intersection_section_capability_audit.json)).
8. **Parser trước đây thiếu những dạng giao tuyến nào?** *(VF)* Tất cả: "Tìm/Xác định/Dựng giao tuyến của (XYZ) và (UVW)", "Gọi d là giao tuyến …". Về thiết diện: "Xác định/Dựng/Tìm/Vẽ thiết diện của hình chóp cắt bởi (tạo bởi) mặt phẳng (XYZ)". Trước run, cả 14 đề thăm dò thiết diện và giao tuyến đều dừng ở `LIVE_AI_DISABLED`.
9. **Local Parser đã hỗ trợ thêm những cách diễn đạt nào?** *(VF)* Với thiết diện: động từ Xác định / Dựng / Tìm / Vẽ; "cắt bởi" hoặc "tạo bởi"; "mặt phẳng", "mp" hoặc chỉ dấu ngoặc; có hoặc không nêu tên khối; "tính diện tích thiết diện"; dấu phẩy Unicode ′. Với giao tuyến: Tìm / Xác định / Dựng / Vẽ, "Gọi d là giao tuyến", "hai mặt phẳng", "mp", nối bằng "và" hoặc "với". Có thêm đề đảo mệnh đề, đổi tên đỉnh, và đề có cả hai goal. 24/24 ca đúng kỳ vọng ([local_section_intersection_parser_tests.json](local_section_intersection_parser_tests.json)).
10. **Có dữ kiện nào bị suy đoán không?** *(VF)* Không. Mặt cắt chỉ dựng từ ba điểm có tên do đề nêu; điểm chưa định nghĩa bị từ chối (`UNDERDETERMINED_POINT`). Chân đường cao là hình chiếu kernel; cạnh và mặt bên chỉ được gắn khi đề khẳng định mặt ⟂ đáy và G xác nhận. Dạng câu hỏi "Mặt phẳng (…) cắt … theo thiết diện là hình gì?" bị Source Gate chặn (`QUESTION_CLAUSE_NOT_PREMISE`), nên parser để nguyên không đọc thay vì nới gate ([source_gate_construction_integrity.json](source_gate_construction_integrity.json)).
11. **Có bao nhiêu bài dựng được giao tuyến?** *(VF)* 5/7 đề thăm dò, trước run là 0. Hai ca còn lại (mặt song song, mặt trùng) bị từ chối. Đề thật: 0, vì corpus không có bài giao tuyến ([plane_intersection_correctness.json](plane_intersection_correctness.json)).
12. **Có bao nhiêu bài dựng được thiết diện?** *(VF)* 9/12 đề thăm dò, trước run là 0. Ba ca còn lại là thẳng hàng, điểm không xác định và dạng câu hỏi, đều bị từ chối. Thiết diện có tam giác, tứ giác, ngũ giác và lục giác; diện tích 3a²√2/8 khớp tính tay. Đề thật: 0 ([polyhedron_section_correctness.json](polyhedron_section_correctness.json)).
13. **Thiết diện có được kiểm chứng topology không?** *(VF)* Có, bằng 5 kiểm độc lập: đỉnh trên mặt cắt, đỉnh trên cạnh khối, các đỉnh phân biệt, đa giác lồi theo thứ tự vòng, mỗi cạnh nằm trong một mặt khối. Engine kiểm thêm chứng chỉ khép kín. Kết quả còn được so với oracle thiết diện độc lập của bộ test cũ.
14. **Có xử lý các giao suy biến không?** *(VF/NM)* Có: mặt cắt chứa một cạnh, mặt cắt trùng một mặt của khối, mặt qua đỉnh, ba điểm thẳng hàng (`COLLINEAR_POINTS`), mặt song song và mặt trùng. Mặt trùng bị từ chối nhưng mang mã `PARALLEL_PLANES`: an toàn nhưng chưa chính xác, đã đưa vào backlog. Mặt chỉ chạm khối tại một điểm hoặc một cạnh: NM trên tuyến local, vì không cách diễn đạt nào được hỗ trợ dẫn tới ca này ([section_degenerate_cases.json](section_degenerate_cases.json)).
15. **Có kiểm tra mặt phẳng cắt không xác định duy nhất không?** *(VF)* Có: ba điểm thẳng hàng, điểm không xác định, mặt không tên ("một mặt phẳng") và cùng một mặt nêu hai lần đều không được phục vụ.
16. **Có cần thêm Kernel primitive mới không?** *(VF)* Không, 0 primitive mới.
17. **Có dùng lại những primitive hiện có không?** *(VF)* Có: `intersect_plane_plane`, thiết diện ba điểm của planner/engine, `project_point_onto_plane` cho chân đường cao, và metric G cho mọi kiểm.
18. **Đường cao mặt bên vuông góc đáy đã dựng đúng chưa?** *(VF)* Đúng trên 3 đề mặt bên ⟂ đáy (đáy vuông với SAB đều, cùng đề viết bằng ký hiệu, và đáy tam giác) và trên chóp đều (chân là tâm đáy). Mỗi cảnh qua 5 kiểm (3 kiểm với chóp đều). Không vẽ đường cao thứ hai khi SA đã được vẽ. Có test cho chân nằm ngoài đoạn, mặt không ⟂ đáy và đỉnh nằm trong mặt đáy; đặt sai chân bị bắt 4/4 ([altitude_face_perpendicular_verification.json](altitude_face_perpendicular_verification.json)).
19. **Có bao nhiêu scene đạt Goal Construction?** *(VF)* Thăm dò: 31/31 cảnh phục vụ (124/124 kiểm). Văn bản: 8/8 cảnh phục vụ; ảnh: 4/4 cảnh phục vụ ([scene3d_mathematical_invariants.json](scene3d_mathematical_invariants.json)).
20. **Có bao nhiêu scene đạt Verified Interactive Simulation?** *(VF/NM)* 6 loại đề (thiết diện chóp, thiết diện lục giác, hai giao tuyến, đường cao, góc 60°) qua 12 tổ hợp đề × viewport đều kiểm trọn trong trình duyệt. Tương tác của từng bài nghiệm thu: NM.
21. **Có bao nhiêu scene bị từ chối đúng?** *(VF)* Thăm dò: 5 (3 thiết diện, 2 giao tuyến). Parser: 10 ca phủ định/mơ hồ/mâu thuẫn/phụ thuộc hình vẽ đều không được phục vụ. Văn bản: 2 `SAFE_REFUSAL`.
22. **Có bao nhiêu wrong-scene-served?** *(VF)* 0 trên mọi tập đã đo.
23. **Có đáp án cuối nào bị hiển thị không?** *(VF)* Không. Trong cả 12 ca, trang không có giá trị đáp số và không có "cos²" ([scene3d_section_intersection_browser_e2e.json](scene3d_section_intersection_browser_e2e.json)).
24. **Có test hình học độc lập với renderer không?** *(VF)* Có. `tools/verify_constructions.py` tính lại từ toạ độ envelope và G bằng Fraction, không gọi mã dựng; oracle thiết diện lấy từ bộ test có từ trước. Đây là phép kiểm `AGENT_DIAGNOSTIC`, không phải người kiểm độc lập.
25. **Mutation tests phát hiện được bao nhiêu lỗi cố ý?** *(VF)* 52/53. Ca lọt duy nhất là đảo thứ tự đỉnh của một thiết diện tam giác: kết quả vẫn là chu trình hợp lệ theo chiều ngược, không phải sai toán học.
26. **Browser E2E đạt kết quả gì?** *(VF)* 12/12. Vật goal vắng ở bước đầu và có ở bước cuối (bước ←/→ thật); xoay và zoom đổi camera, reset về pose ban đầu; chọn chip goal đặt đúng `selected_id`; 0 lỗi trang.
27. **Mobile có còn lỗi tương tác không?** *(VF)* Không, ở mức đã đo. Ở 390×844 và 768×1024 không tràn ngang, nút bước 40 px, chọn vật hoạt động (chip goal có thể nằm sau "Xem thêm").
28. **Có memory leak được chứng minh không?** *(INF)* Không chứng minh có, cũng không loại trừ. Sau GC, heap tăng 2,78 MB qua 12 lần phân tích trong một phiên (lịch sử giữ từng envelope theo thiết kế). 15 lần đi timeline không tăng đơn điệu (23,6 → 25,7 → 26,0 → 24,6 MB). Số canvas giữ nguyên ([resource_cleanup_audit.json](resource_cleanup_audit.json)).
29. **Hiệu năng có thay đổi không?** *(VF, máy host headless)* Tuyến backend: trung vị 22,1 → 21,4 ms, đo trước và sau trong cùng máy. Trình duyệt: từ bấm gửi đến mô hình 380–593 ms; chuyển bước trung vị 98 ms, tối đa 181 ms. Không thấy hồi quy; chênh lệch so với run trước nằm trong biến thiên giữa các ca (INF) ([performance_impact.json](performance_impact.json)). Máy cấu hình thấp vật lý: NM.
30. **Có bao nhiêu bài mới chưa dùng phát triển được mô phỏng?** *(NM)* 0 được đo. Không có dữ liệu chưa thấy nào ngoài 94 dòng niêm phong ([fresh_external_simulation_evaluation.json](fresh_external_simulation_evaluation.json)).
31. **Có mở 94 dòng H-1 không?** *(VF)* Không: không tải, không xem, không OCR, không đọc.
32. **H-1 có được đánh giá độc lập không?** *(NM)* Chưa ([independent_h1_status.json](independent_h1_status.json)).
33. **Full backend/frontend regression đạt không?** *(VF)* Đạt, ở lần chạy thứ hai. Lần 1, backend có 2 test census phạm vi fail, đều do lỗi của run này; đã sửa ở `ea4b2a197` rồi đóng băng lại. Lần 2, backend đạt 14 363 test; frontend có 1 test quá thời hạn 5 s dưới tải, chạy riêng 3 lần đều đạt trong khoảng 1 s, và cả cổng chạy lại đạt 2 047/2 047 (§5).
34. **Publication HEAD còn bao nhiêu finding?** *(BL)* 97, tất cả là `pending_exception`, như trước run. `PUBLICATION_HEAD = BLOCKED_PENDING_OWNER_REVIEW`.
35. **Publication range đã xử lý thế nào?** *(VF/BL)* Quét `ffc62f6fe..HEAD`: **PASS**, 0 vi phạm (136 file). Run này không sinh finding mới vì mật khẩu thử là ngẫu nhiên mỗi lần chạy. Blob lịch sử `2bfce9c8` (`HARDCODED_PASSWORD`, mật khẩu tổng hợp cho tài khoản thử trong SQLite cục bộ) đã được git xác minh: có ở `fe835d424`, không còn ở `8da3ea754` và HEAD, và nằm trước mốc bắt đầu run nên không thuộc khoảng quét. Blob vẫn nằm trong lịch sử và chỉ Owner được thêm ngoại lệ đúng blob này, nên `PUBLICATION_RANGE = BLOCKED_PENDING_OWNER_REVIEW` và `FULL_RELEASE_GATE = BLOCKED_GATES_REMAIN`. Agent không duyệt, không thêm wildcard, không sửa chính sách quét, không viết lại lịch sử ([publication_gate_status.json](publication_gate_status.json)).
36. **Candidate freeze ở commit nào?** *(VF)* `f0fa7e359` lưu manifest của HEAD `cf058f0ee`, sản phẩm `ea4b2a197`, measured_system `dc834af0001169e6…`, 115 file; `freeze --verify` đạt trong regression. Các template K-1/S-2/R-1 được gắn lại ở `c29cff312` (chỉ metadata, giữ PENDING). Bản trước, `89aed139e` / `8f49cd2d…`, bị thay thế ([candidate_freeze.json](candidate_freeze.json)).
37. **Có merge, push, deploy hoặc live AI call không?** *(VF)* Không có.
38. **Những khoảng trống mô phỏng nào còn tồn tại?** *(VF/INF)*
    - Thiết diện nêu trong câu hỏi bị chặn đúng theo thiết kế.
    - Thiết diện bởi mặt xác định qua quan hệ song song/vuông góc ("qua M và song song với …") chưa đi qua luật 7c-0.
    - Mặt trùng mang mã chưa chính xác.
    - Giao chỉ tại điểm hoặc cạnh chưa đo.
    - Khối con, điểm mô tả không tên, hình chỉ xác định tới thang đo, điểm tự do, tương tác tham số.
    - Corpus đề thật chưa có bài thiết diện hay giao tuyến.
39. **Candidate đã đủ điều kiện pilot ở mức nào?** *(INF)* Đủ cho demo có hướng dẫn trên các họ đa diện được hỗ trợ: dựng được góc, thiết diện, giao tuyến và đường cao, chưa có cảnh sai. Chưa đủ cho học sinh tự học, vì phủ đề thật thấp (8/27, 4/27), dữ liệu chưa thấy bằng 0 và publication đang bị chặn.
40. **Công việc tiếp theo có giá trị cao nhất là gì?** *(INF)* Owner quyết định một tập đánh giá chưa thấy có bài thiết diện và giao tuyến; nếu thiếu tập này, mọi con số ở đây vẫn chỉ là bằng chứng phát triển. Về kỹ thuật: mặt cắt xác định qua quan hệ song song (dạng sách giáo khoa phổ biến nhất sau mặt ba điểm), dùng lại phép dựng song song đã có. Song song với đó, Owner xử lý publication.

## 4. Tính toàn vẹn dữ liệu

Đề thăm dò là câu tổng hợp do agent viết. 27 bản chép và ảnh nghiệm thu đều đã bị lộ. 94 dòng H-1 niêm phong không bị mở. Không con số nào trong báo cáo này là bằng chứng tổng quát hoá.

## 5. Regression và publication

Chi tiết ở [full_regression_summary.json](full_regression_summary.json). `ALLOW_LIVE_AI=0`, mã nguồn không đổi trong lúc chạy. Verdict của bộ chạy là `INCOMPLETE_OR_FAIL` chỉ vì cổng publication HEAD; verdict tổng là **BLOCKED**.

| Cổng | Lần 1 (candidate `8f49cd2d…`) | Lần 2 (candidate `dc834af0…`) |
|---|---|---|
| backend pytest | **FAIL**: 2 failed, 14 359 passed. `test_census_inventory_complete` báo `SimulationGoalSpecV2` chưa phân loại; mutant `remove_apex_ownership` không áp được | **PASS**: 14 363 passed, 7 skipped, 3 deselected, 15 xfailed |
| frontend `test:wave` | PASS 2 047 | 1 timeout 5 s dưới tải (`axo-cross-family-scene3d-acceptance`); chạy riêng 3/3 đạt (~1 s); chạy lại cả cổng: **PASS**, 140 file, 2 047 test, tsc + vite build |
| demo replay · crash audit · docs IA | PASS | **PASS** |
| freeze verify | PASS (`8f49cd2d…`) | **PASS**: 115 file, `dc834af0…` |
| publication HEAD | BLOCKED 97 | **BLOCKED**: 97, tất cả `pending_exception` |
| publication range `ffc62f6fe..HEAD` | PASS 0 | **PASS**: 0 |

Biên nhận lần 1 ở `logs/attempt1/`; biên nhận frontend lần 2 ở `logs/attempt2/` và trong `previous_attempts` của summary. Ngoài bộ chạy: E2E trình duyệt 12/12, kiểm bất biến 124/124, mutation 52/53, đồ thị phụ thuộc 0 vi phạm.

## 6. Giới hạn

Trình duyệt chạy headless trên máy host; xác nhận ảnh là script; oracle bất biến do agent viết, theo đường mã độc lập nhưng không phải người kiểm. Chưa có máy cấu hình thấp, PostgreSQL hay Live Vision.
