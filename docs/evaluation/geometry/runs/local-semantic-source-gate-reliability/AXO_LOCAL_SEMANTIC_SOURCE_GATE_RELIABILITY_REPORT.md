# AXO: phủ ngữ nghĩa local, cứng hoá Source Gate và độ tin cậy end-to-end

| Mục | Giá trị |
|---|---|
| Nhánh / worktree | `feat/local-first-geometry-understanding` (worktree cố định, không tạo nhánh hay worktree mới) |
| Mốc bắt đầu | `c5bb73f51` (candidate trước: commit `835786746`, measured_system `cd9b9f51…`) |
| Commit sản phẩm | `262ff46d5` parser · `d6b38b172` ingestion · `81bcb5d0f` frontend · `1c9c26489` parser + gate |
| Candidate | đóng băng tại `dcad65e5e` (lưu ở `be3467457`), product `1c9c26489`, measured_system `1cc979f559a632c3…` (115 file), `CACHE_VERSION` 132 |
| Hợp đồng | `geometry-fact-planner/26`, `geometry-functions/33`, `geometry-function-engine/24`, `height-invariance-certificate/2`, `output-policy/1`: **không đổi** |
| Lượt gọi model | 0 (`ALLOW_LIVE_AI=0`, khoá rỗng). Không merge, push hay deploy. |
| Nguồn tham chiếu | Bản chép tay của agent (`AGENT_TRANSCRIBED_UNVERIFIED`). Đáp án lấy theo khoá của dataset. |

Nhãn kết luận: **VF** = VERIFIED FACT, **INF** = INFERENCE, **HYP** = HYPOTHESIS, **NM** = NOT_MEASURED, **BL** = BLOCKED.

## 1. Kết luận chính

- **VF.** Trên văn bản đã kiểm, số bài đa diện giải được tăng từ 4 lên 7 trên 23, không có bài nào trả sai ([text_to_geometry_before_after.json](text_to_geometry_before_after.json)). Cả 23 bài đều đã được đọc trong lúc viết luật, nên đây là bằng chứng phát triển, không phải bằng chứng tổng quát hoá.
- **VF.** Mẫu fresh lấy sau freeze (48 dòng VMMU chưa ai mở, seed 20261113, đã đăng ký trước) chỉ có 2 bài trong phạm vi. Cả hai không được phục vụ và không bài nào trả sai ([fresh_external_evaluation.json](fresh_external_evaluation.json)). Năng lực tổng quát hoá của các luật mới **chưa được chứng minh**.
- **VF.** Root cause lỗi SQLITE_BUSY: OCR đồng bộ chạy trên event loop trong khi phiên của request đang giữ khoá ghi. Sau khi chuyển OCR ra threadpool, 8 upload đồng thời từ 24/40 thành công lên 40/40, lặp lại được 80/80. Không còn 5xx hay 401, và `/api/health` luôn dưới 0,7 s ([sqlite_concurrency_before_after.json](sqlite_concurrency_before_after.json)).
- **VF.** Học sinh nối được một chỗ OCR với chữ kế tiếp rồi sửa cả cụm (`4BCD-` + `A'B'C'D'` thành `ABCD.A'B'C'D'`) và tách lại được. Đã kiểm trong Chromium thật trên bản build, đạt 2/2 viewport ([browser_span_angle_check.json](browser_span_angle_check.json)). Phản hồi prepare trong phép kiểm này là FIXTURE.
- **VF.** Nhãn góc theo độ ở frontend chạy đúng ở mức component, nhưng **không hiện trên workspace đang ship**. Workspace ẩn đáp số cuối (mô phỏng trước), còn bảng "Phân tích toán học" thuộc `Scene3DExplorer`, không được gắn ở mã sản phẩm.
- **VF.** Publication HEAD vẫn `BLOCKED_PENDING_OWNER_REVIEW`. Verdict tổng vì vậy là **BLOCKED**, kể cả khi mọi cổng offline đều đạt.

## 2. Trả lời 35 câu hỏi

1. **12 lỗi Parser do đâu?** *(INF, dựa trên trace VF)* Có 6 nhóm: (a) cách viết mục tiêu không khớp luật nào: thể tích không có chữ "khối" (r270), thể tích khối con `A'ABC` hay `B'.ACC'A'` (r254, r488), góc gọi theo vai trò "cạnh bên / mặt đáy" (r538); (b) dựng hình chưa có: chân đường cao trùng trọng tâm (r254), mặt bên ⟂ đáy (r256, r284), điểm đối xứng (r277), điểm I tự do trên BC (r491); (c) danh sách kích thước `cạnh đáy …, cạnh bên …` (r298); (d) đẳng thức trần `SA = AB` bị bỏ im lặng (r258); (e) khối viết thiếu dấu chấm `ABCDA'B'C'D'` (r463); (f) giá trị đứng trước "biết" mà không có dấu câu (r270, r520). Chi tiết: [semantic17_case_diagnostics.json](semantic17_case_diagnostics.json).
2. **5 lỗi Source Gate do đâu?** *(INF)* Chỉ r460 là lỗ của gate thật: đuôi câu hỏi "… theo a bằng" không được nhận là câu hỏi. r375 và r537 là parser bỏ im lặng một mệnh đề; gate bắt được, và bắt đúng. r498 là parser bỏ danh sách kích thước, cộng với đề hỏi "cosin của góc", một hàm đầu ra mà chính sách đóng không phục vụ. r513 thiếu dấu chấm trước câu hỏi, và mặt phẳng viết không có ngoặc.
3. **Wave trước có phân loại sai không?** *(VF / INF)* Có, ở hai chỗ. 4 trong 5 ca "Source Gate" thực ra bắt nguồn từ parser (câu 2). Nhãn candidate `a78b1e087` là commit lưu manifest; candidate thật là `835786746`, cùng một sản phẩm ([candidate_commit_reconciliation.json](candidate_commit_reconciliation.json)). Receipt cũ giữ nguyên; lớp đính chính nằm trong `EVIDENCE_INDEX`.
4. **Sửa được bao nhiêu lỗi ở Parser?** *(VF)* 4 ca nay đi hết parser (r270, r298, r375, r520); 3 trong số đó được phục vụ đúng. 3 ca khác đọc thêm được dữ kiện nhưng vẫn dừng ở tầng sau (r258, r498, r460).
5. **Ở Typed Facts / Bridge?** *(VF)* 0. Không tìm thấy lỗi ở tầng này: 16/17 lược đồ hợp lệ, ca còn lại không có khối nào; 0 mơ hồ ở bridge ([typed_facts_bridge_integrity.json](typed_facts_bridge_integrity.json)).
6. **Ở Source Gate?** *(VF)* 2 luật biên: đuôi câu hỏi `theo a bằng`, và giá trị kết thúc tại "biết" hoặc tại mệnh đề mới viết hoa. Chúng góp phần cho r270 và r460, và gỡ một nửa r513.
7. **Có bao nhiêu rule tổng quát mới?** *(VF)* 6: danh sách kích thước khối đều/đứng, đẳng thức đoạn thẳng trần, các cách viết mục tiêu thể tích, "vuông (cân) ở X", đuôi câu hỏi "theo a", biên giá trị. Ngoài ra mỗi guard nay ghi lý do giữ mệnh đề lại; đây là công cụ chẩn đoán, không phải luật ngữ nghĩa ([parser_generalization_receipt.json](parser_generalization_receipt.json)).
8. **Có handler riêng theo case không?** *(VF)* Không. Không luật nào nêu case ID, bộ nhãn đỉnh hay đáp số. Các luật được kiểm bằng câu tổng hợp khác với 17 bài và có phản ví dụ.
9. **Có mất mệnh đề không?** *(VF)* Không có mệnh đề nào bị bỏ im lặng mà vẫn được phục vụ. Mọi lần phục vụ đều qua Source Gate, và gate từ chối khi còn mệnh đề tiền đề chưa đọc. Hai lần bỏ im lặng cũ (r375, r537) đã được tìm ra; r375 nay được đọc.
10. **Nguồn gốc có được bảo toàn không?** *(VF)* Có. Mỗi dữ kiện mới mang trích dẫn nguyên văn của chính nó; trong danh sách kích thước, mỗi mục sau tự trích dẫn để mỗi giá trị chỉ được gán một lần.
11. **Có dữ kiện không nguồn nào vượt gate không?** *(VF trên tập đã kiểm, INF ngoài tập đó)* Không. Phản ví dụ vẫn bị từ chối: `SA = AA`, `SA = 2AB`, "theo a bằng 2a³", phép "hoặc", và giá trị diện tích `a²` (bị chặn với `UNGROUNDED_VALUE`).
12. **Planner có tận dụng primitive cũ không?** *(VF)* Có. 3 bài mới được phục vụ đều dùng hàm REGISTRY có sẵn (khối đều, độ dài đoạn, thể tích). Không có hàm mới, không đổi phiên bản planner hay engine ([planner_composition_verification.json](planner_composition_verification.json)).
13. **Bao nhiêu bài cần capability hình học mới thật sự?** *(INF)* 8/17 cần dựng hình hoặc kernel mới: chân đường cao trùng trọng tâm, mặt bên ⟂ đáy (×2), điểm đối xứng, khối con, tham số tự do bất biến, bài không có thang đo, cạnh góc vuông suy từ cạnh huyền. 2/17 cần một phiên bản chính sách đầu ra mới (cos, tan). 4/17 chỉ là văn phạm parser. 3/17 đã được phục vụ.
14. **23 bài đa diện trước/sau giải được bao nhiêu?** *(VF, tập phát triển)* Văn bản: 4 → 7. Ảnh (chỉ xác nhận các chỗ bị đánh dấu, có mô phỏng): 3 → 4 trên 25 ảnh, thêm r298 ([image_to_scene3d_before_after.json](image_to_scene3d_before_after.json)).
15. **Bao nhiêu bài bị từ chối đúng?** *(VF / INF)* Cả 16 bài không được phục vụ đều dừng an toàn (0 trả sai). Theo phân xử, 4 lần từ chối là đúng theo thiết kế: r258 và r498 hỏi tan/cos, r537 có giá trị diện tích, r520 không có thang đo. 12 bài còn lại dừng vì thiếu năng lực: an toàn, nhưng chưa phải hành vi mong muốn.
16. **Có bao nhiêu wrong-served?** *(VF)* 0 trên văn bản (23 bài), 0 trên ảnh (25), 0 trên mẫu fresh (2).
17. **Có bao nhiêu đề mới được giải đúng mà chưa từng dùng phát triển?** *(VF)* 0. Mẫu fresh có 2 bài trong phạm vi: r559 hỏi "Côsin của góc" (hàm đầu ra không hỗ trợ), r695 có cạnh hình vuông cho muộn bằng `AB = 1` (hệ hỏi lại để xác nhận).
18. **H-1 có độc lập không?** *(NM)* Không có H-1. Mẫu fresh do chính agent đã viết bản sửa chọn, chép và chấm. Còn 94 dòng chưa mở được giữ lại ([independent_h1_status.json](independent_h1_status.json)).
19. **Có cải thiện bài hỏi góc và đáp án theo độ không?** *(VF)* Backend không đổi: trả `60°` khi đề hỏi "số đo góc", còn lại trả `cos²=1/4`. Frontend gắn nhãn độ cho cos² đặc biệt và giữ cos² chính xác bên cạnh; với góc giữa đường và mặt (0°–90°), cos² xác định duy nhất góc nên không phải đoán nhánh. Tuy vậy, workspace đang ship không hiển thị đáp số này ([angle_output_policy_receipt.json](angle_output_policy_receipt.json)).
20. **Còn `cos²(θ)` hiện như đáp số khi đề hỏi góc không?** *(VF)* Ở API thì còn, theo đúng `output-policy/1`: "Tính góc …" nhận `cos²=1/4`. Đổi điều này cần một phiên bản chính sách mới, nên chưa làm. Học sinh trên workspace không thấy cả hai dạng.
21. **Sửa được biểu thức OCR bị tách nhiều span không?** *(VF)* Có. Học sinh nối, sửa, tách lại được; nối hoặc tách đều huỷ xác nhận. Có unit test và kiểm trình duyệt 2/2 (FIXTURE) ([multi_span_confirmation_receipt.json](multi_span_confirmation_receipt.json)).
22. **Cache có làm mới đúng sau khi sửa đề không?** *(VF / INF)* Trình duyệt gửi đúng văn bản đã sửa tới `/api/analyze` và được phục vụ (VF). Cache backend tính khoá từ văn bản (`main.py::_cache_key`) và chỉ lưu kết quả SERVED, nên văn bản sửa là khoá mới (INF từ code). Bề mặt cache không đổi; `test_cache_identity` đạt.
23. **Lỗi SQLite ở 8 upload khắc phục tới đâu?** *(VF)* 0 lỗi trong 120 upload (5 + 10 vòng), không có SQLITE_BUSY. Đây là load test loopback có giới hạn, **không** phải tuyên bố về concurrency production; trung vị prepare ở mức 8 đồng thời khoảng 13 s vì OCR chạy hàng đợi.
24. **Còn HTTP 401/500 sai nguyên nhân không?** *(VF)* Không. Trước khi sửa, 500 là `INFRASTRUCTURE` (SQLITE_BUSY). Mỗi 401 đều đi sau một lần `/api/auth/me` thất bại, tức client không có phiên, nên ánh xạ 401 là đúng. Hợp đồng auth không đổi ([api_error_classification.json](api_error_classification.json)).
25. **OCR Fidelity Gate có từ chối nhầm không?** *(VF / INF)* Có dấu hiệu. Ở 13/16 ảnh đủ mọi dữ kiện, mọi cờ chặn đều là báo nhầm (59/70 cờ chặn); 3 ảnh trong số đó (r266, r277, r463) không bị giữ vì hình vẽ. Gate vẫn **không nới**: tham chiếu chưa được người kiểm, và phép diff còn thấy sai khác toán học không bị đánh dấu ở 2 ảnh ([ocr_false_rejection_summary.json](ocr_false_rejection_summary.json)).
26. **Bao nhiêu ảnh được local OCR tự động chấp nhận?** *(VF)* 0/25, và 0/2 ở mẫu fresh.
27. **Bao nhiêu ảnh Image-to-3D được giải đúng?** *(VF)* 4/25 sau khi xác nhận có mô phỏng (trước đó 3), 0/2 ở mẫu fresh, 0 trả sai.
28. **Hiệu năng text và image thay đổi thế nào?** *(VF)* Parser: 18/25 câu không đổi (tỉ lệ 0,94–1,08). 7 câu nay đi xa hơn (tới Stage 8) tốn hơn 1,6–11 lần nhưng vẫn ≤ 15 ms; tổng 95 → 134 ms trên 25 câu ([parser_latency_before_after.json](parser_latency_before_after.json)). Prepare ảnh: trung vị hai phiên đo khác nhau là 3,1 s → 1,9–2,3 s; đây không phải so sánh có kiểm soát. Bộ nhớ: NM, vì không thêm tiến trình hay model.
29. **Có regression ở Planner, Kernel hoặc Scene3D không?** *(VF)* Không. Toàn bộ backend pytest (gồm các test planner, kernel, oracle và cache identity) và vitest (gồm Scene3D) đều đạt; demo replay và crash audit (6/6) cũng đạt (§6).
30. **Full regression có hoàn tất không?** *(VF)* Có. Cả 8 cổng đã chạy trên cây sạch, mã nguồn không đổi trong suốt lượt chạy. 7 cổng đạt; `publication_head` là BLOCKED với 97 finding chờ Owner, nên verdict của bộ chạy là `INCOMPLETE_OR_FAIL` và verdict tổng là **BLOCKED**.
31. **97 finding publication đã được owner duyệt chưa?** *(BL)* Chưa. Agent không ghi phê duyệt, không thêm ngoại lệ, không viết lại lịch sử ([publication_owner_review_status.json](publication_owner_review_status.json)).
32. **Live Vision đã được gọi chưa?** *(VF)* Chưa; 0 lượt gọi provider.
33. **Candidate đủ điều kiện pilot ở mức nào?** *(INF)* Dùng được cho demo có người hướng dẫn trên văn bản, với các họ đa diện đã hỗ trợ, nhờ 0 trả sai trên mọi tập đã đo. Chưa dùng được cho học sinh tự học: ảnh luôn cần xác nhận, phủ đề thật còn thấp (2/2 bài fresh không được phục vụ), và publication đang bị chặn.
34. **Những vấn đề nào còn tồn tại?** Xem §5.
35. **Việc kế tiếp có giá trị cao nhất?** *(INF)* (1) Owner quyết định `output-policy/2` cho cos/tan của góc đã phục vụ: lỗ này xuất hiện ở 3 bài (r258, r498, r559, gồm cả bài fresh) và chỉ cần một luật tất định trên cos² chính xác. (2) Luật parser cho cạnh đa giác đều cho muộn ("đáy là hình vuông, biết AB = 1"). (3) Một H-1 độc lập trên 94 dòng còn để dành.

## 3. Thay đổi sản phẩm

| Commit | Thay đổi | Khoá bằng |
|---|---|---|
| `262ff46d5` | Parser: danh sách kích thước, đẳng thức trần, mục tiêu thể tích, ghi chú guard | `backend/tests/geometry/test_local_semantic_coverage.py` |
| `d6b38b172` | Ingestion: phát hiện vùng, đếm đầu đề và OCR chạy qua `run_in_threadpool` | `backend/tests/test_input_prepare_concurrency.py` |
| `81bcb5d0f` | Frontend: nối/tách span; nhãn độ cho cos² đặc biệt | `photo-span-review.test.tsx`, `hybrid-preview-contract.test.tsx` |
| `1c9c26489` | Parser "vuông (cân) ở X"; gate: biên giá trị tại "biết" / mệnh đề mới | cùng file test parser |

`CACHE_VERSION` không bump, vì `test_cache_identity` đạt: bề mặt mô hình có băm không đổi ([candidate_freeze.json](candidate_freeze.json)).

## 4. Tính toàn vẹn dữ liệu đánh giá

- **VF.** Cả 23 bản chép đa diện của run trước, trong đó có 13 bài thuộc tập `frozen_external_evaluation`, đã bị lộ trong run này. Tập ấy không còn là held-out cho các luật mới ([dataset_partition_audit.json](dataset_partition_audit.json)).
- **VF.** Mẫu fresh được đăng ký trước khi tải ảnh ([fresh_external_preregistration.json](fresh_external_preregistration.json), commit `9ba56f9d8`). Manifest được đóng băng trước khi chạy Axo (commit `9f2314e11`). Agent đã xem cả 48 ảnh, không lọc bằng từ khoá; 46 ảnh ngoài phạm vi (hàm số và giải tích là chính).

## 5. Vấn đề còn tồn tại

- **Năng lực:** hàm đầu ra cos/tan; thể tích khối con; chân đường cao trùng trọng tâm; mặt bên ⟂ đáy; điểm đối xứng; tham số tự do; bài không thang đo; cạnh huyền và cạnh góc vuông; đỉnh tam giác cân; giá trị diện tích làm tiền đề.
- **Văn phạm parser:** khối viết thiếu dấu chấm (phải hỏi lại, không được đoán); mặt phẳng không có ngoặc; góc gọi theo vai trò; cạnh đa giác đều cho muộn.
- **UX:** đáp số góc không hiện trên workspace; ảnh không bao giờ được tự chấp nhận; gate span giữ lại nhiều ảnh đúng.
- **Chưa đo / bị chặn:** H-1 (NM), học sinh thật (NM), Live Vision (không được phép), PostgreSQL và máy yếu (NM), publication (BL, chờ Owner).

## 6. Regression

Chi tiết ở [full_regression_summary.json](full_regression_summary.json). Lượt chạy trên cây sạch tại `8e727333d`, `ALLOW_LIVE_AI=0`, mã nguồn không đổi trong lúc chạy.

| Cổng | Kết quả |
|---|---|
| backend pytest | **PASS**: 14290 passed, 7 skipped, 3 deselected, 15 xfailed |
| frontend `test:wave` | **PASS**: 139 file, 2024 test; build (tsc + vite) đạt |
| demo replay | **PASS** |
| crash audit | **PASS** 6/6, 0 uncaught |
| docs IA | **PASS**: 0 link gãy, 0 lộ bí mật |
| publication HEAD | **BLOCKED**: 97 vi phạm, đều là `pending_exception`, chờ Owner |
| publication range `c5bb73f51..HEAD` | **PASS**: 75 file, 0 vi phạm |
| freeze verify | **PASS**: 115 file, `1cc979f559a632c3…` |

Các phép kiểm ngoài bộ chạy: trình duyệt nối/tách span đạt 2/2 viewport. Từ lần freeze trước, chỉ có 3 mẫu owner-approval PENDING được gắn lại measured_system, và vẫn giữ PENDING ([pending_template_refresh.json](pending_template_refresh.json)).

## 7. Giới hạn

Tham chiếu do agent chép, chưa được người kiểm. Dữ liệu chỉ từ một dataset trắc nghiệm, ảnh là trang đề render sẵn. Bước xác nhận được mô phỏng bằng script. Bài kiểm trình duyệt dùng phản hồi prepare FIXTURE. Mẫu fresh chỉ có 2 bài trong phạm vi. Không có con số nào ở đây chứng minh khả năng tổng quát hoá.
