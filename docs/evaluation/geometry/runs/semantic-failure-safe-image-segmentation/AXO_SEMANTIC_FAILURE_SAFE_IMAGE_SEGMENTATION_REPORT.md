# AXO: định vị nguyên nhân từ chối và tách an toàn ảnh nhiều đề

| Mục | Giá trị |
|---|---|
| Nhánh / worktree | `feat/local-first-geometry-understanding` (worktree cố định; không tạo nhánh/worktree, không merge/push/deploy) |
| Mốc bắt đầu | `dcbedcb0d` (candidate `8852c4070`, sản phẩm `697b097ac`, measured_system `040de2fd…`, 115 file, `CACHE_VERSION` 134) |
| Commit sản phẩm | `cc449ae4b`: chẩn đoán nguyên nhân gốc, sửa parser, tách đề an toàn. `7315cf3b0`: mỗi khối hình chỉ thuộc một bài |
| Candidate | đóng băng ở `18a7ba008`, measured_system `1f62a4a4…` (**116** file: thêm module chẩn đoán), `CACHE_VERSION` 134 (không nâng) |
| Hợp đồng | planner `/26`, registry `/33`, engine `/24`, `height-invariance-certificate/2`, `output-policy/1`, envelope `/4`, `typed-fact-next/2`: **không đổi**. Source Gate không đổi. Thêm trường tuỳ chọn `route_d.local_diagnostics`, chỉ có trên phản hồi từ chối |
| Lượt gọi model | 0 (`ALLOW_LIVE_AI=0`) |

Nhãn: **VF** VERIFIED FACT · **INF** INFERENCE · **HYP** HYPOTHESIS · **NM** NOT_MEASURED · **BL** BLOCKED.

## 1. Kết luận chính

- **VF. Lời từ chối nay có nguyên nhân gốc, tách khỏi mã cuối.** Trước run này, mọi đề tuyến local chưa đọc trọn đều kết thúc bằng `LIVE_AI_DISABLED`, mã này chỉ nói rằng fallback bị chặn.
  - Nay `route_d.local_diagnostics` cho biết tầng đầu tiên làm mất thông tin, tầng phát hiện và tầng quyết định.
  - Nó cũng cho kiểu và offset của từng mệnh đề, kèm phụ thuộc xuôi dòng (một câu hỏi trên (P) chỉ hỏng vì định nghĩa (P) chưa được đọc).
  - Nó tách "hiểu nhưng chưa hỗ trợ" (côsin/tang của góc, chứng minh) khỏi "không hiểu".
  - Chỉ chạy trên phản hồi từ chối, 0,17 ms mỗi lần; từ chối không bao giờ được cache.
- **VF. Trên 27 đề thật đã lộ, có 19 đề bị từ chối.**
  - 17 đề mất thông tin tại parser: 9 do parser tự phát hiện mệnh đề chưa đọc, 8 do Source Gate phát hiện dữ kiện parser tạo ra mà nguồn không chống đỡ.
  - 1 đề vượt miền tính chính xác (planner), 1 đề thiếu kích thước.
  - Không có lỗi nào thực sự của Source Gate: trong cả 8 ca, gate chặn đúng.
- **VF. Sửa ngữ nghĩa theo chẩn đoán**, trên tập phát triển mới (37 đề do agent viết, có cặp tối thiểu và biến thể metamorphic):
  - phục vụ được 19 → 23/37; đúng kỳ vọng 27 → 31/37; giữ kết quả qua biến đổi metamorphic 11 → 14/17;
  - 0 đề âm bị phục vụ;
  - 27 đề thật và 39 đề thăm dò không đổi (8/27; 35/39).
- **VF. Không còn tự gộp đề** trên các trang ghép từ ảnh thật đã lộ (luồng `prepare` thật, so trước/sau):

  | Loại trang | Gộp không hỏi | Mọi bài chọn sạch được |
  |---|---|---|
  | 2 bài xếp chồng | 3/12 → 0/12 | 7/12 → 10/12 |
  | 3 bài xếp chồng | 0/8 → 0/8 | 0/8 → 8/8 |
  | 2 cột | 2/6 → 0/6 | 0/6 → 4/6 |

  Ảnh một bài: 0/25 bị hỏi chọn thừa, trước và sau như nhau.
- **VF. E2E chọn bài trên Chromium thật đạt 4/4 viewport.** Bài được chọn đi tới Scene3D, văn bản gửi đi chỉ của bài đó, đổi lựa chọn thì văn bản đổi theo, mobile không tràn.
- **VF. Hai track âm đã tách riêng, mỗi track qua đúng ranh giới của nó.** Lời đề có lỗi: 8/8 bị từ chối. Payload bị làm hỏng: 8/8 bị chặn tại bridge/Source Gate.
- **NM / BL.** Không có dữ liệu độc lập mới (`BLOCKED_DATA`); H-1 chưa đo; publication HEAD vẫn chờ Owner.

## 2. Thay đổi sản phẩm

| Commit | Thay đổi | Khoá bằng |
|---|---|---|
| `cc449ae4b` | `local_failure_diagnostics.py` + router: chẩn đoán trên phản hồi từ chối. Parser: "(mặt phẳng/mặt) đáy" làm toán hạng góc; điểm có tên định nghĩa trong mệnh đề mặt phẳng ("qua trung điểm M của SA"); "Thiết diện … cắt bởi (P) là hình gì?"; câu hỏi dạng đề thi "Diện tích thiết diện … bằng" (không bao giờ đọc thành giả thiết). Ảnh: đếm nhóm phương án trắc nghiệm từ hộp chữ OCR (mỗi bài một phương án A); dải theo từng bài, cắt cột tại chỗ không dòng OCR nào vắt qua; vùng đơn có ≥ 2 nhóm → `needs_selection`; luật "≤ 1 tiêu đề Câu N" chỉ giữ cả trang khi trang cũng có ≤ 1 nhóm phương án | `test_semantic_failure_diagnostics.py` (17), `test_multi_problem_segmentation.py` (10) |
| `7315cf3b0` | Một khối bố cục thuộc về dải chứa ≥ 50% diện tích của nó, nên hình vẽ không bị gán cho hai bài | idem; [diagram_to_problem_association.json](diagram_to_problem_association.json) |

Đã gỡ khỏi parser (không đưa vào): "thiết diện do (P) cắt hình chóp". Văn phạm của gate không đọc dạng này cho mặt phẳng dẫn xuất; nếu parser đọc thì chỉ chuyển lời từ chối sang mã khác. Ghi vào backlog, không nới gate.

## 3. Trả lời 48 câu hỏi

1. **Candidate baseline có toàn vẹn không?** *(VF)* Có: `freeze --verify` khớp 115 file `040de2fd…`, khoá cache khớp 134, cây sạch ([baseline_candidate_integrity.json](baseline_candidate_integrity.json)).
2. **Có đọc dữ liệu holdout chưa được phép không?** *(VF)* Không. W2/W3 không bị chạy lại cũng không bị đọc; chỉ `phase0.py` đọc byte để băm. H-1: 0 lần mở ([holdout_protection_audit.json](holdout_protection_audit.json)).
3. **Parser chia mệnh đề theo phương pháp nào?** *(VF)* `split_into_clauses`: tách theo dấu câu kết thúc câu, `;` và các dấu phân cách cấp mệnh đề. Mỗi mệnh đề được phân loại MAPPED / BENIGN / UNPARSED / UNRESOLVED kèm offset ([existing_parser_observability_audit.json](existing_parser_observability_audit.json)).
4. **Bao nhiêu mệnh đề bị mất trước Source Gate?** *(VF)* 27 đề thật: 17 mệnh đề, trong 9 đề. Tập phát triển: 10 → 6 ([semantic_root_cause_matrix.json](semantic_root_cause_matrix.json)).
5. **Bao nhiêu mệnh đề được đọc một phần?** *(VF)* 27 đề thật: 2 đề có parser tưởng đã đọc trọn nhưng gate thấy còn phần chưa đọc (`SOURCE_PREMISE_UNREAD`, `QUESTION_CONTEXT_UNSUPPORTED`). 7 đề có một phần mệnh đề được nhận.
6. **Bao nhiêu lỗi do entity resolution?** *(VF)* 27 đề thật: 4 (định nghĩa điểm, khối hoặc mặt chưa đọc). Tập phát triển: 2 → 1.
7. **Bao nhiêu lỗi do relation extraction?** *(VF)* 27 đề thật: 2. Tập phát triển: 1 → 0.
8. **Bao nhiêu lỗi do goal extraction?** *(VF)* 27 đề thật: 3. Có thêm 3 đề **hiểu đúng nhưng chưa hỗ trợ** (côsin/tang của góc). Tập phát triển: 6 → 4.
9. **Bao nhiêu lỗi thật sự thuộc Source Gate?** *(VF)* 0. Gate *phát hiện* 8 lỗi của parser trên 27 đề thật và chặn đúng cả 8.
10. **Bao nhiêu lỗi thật sự thuộc Planner/Kernel?** *(VF)* 27 đề thật: 1 (`EXACT_DOMAIN_EXCEEDED`). Đề thăm dò: 3 ca suy biến được từ chối đúng.
11. **`LIVE_AI_DISABLED` đã được phân rã chưa?** *(VF)* Rồi. Mã này vẫn là mã cuối; nguyên nhân gốc, tầng chịu trách nhiệm và trạng thái fallback (`LOCAL_PROVIDER_FALLBACK_DISABLED`) nằm trong `local_diagnostics`.
12. **Có lưu source span và provenance đúng không?** *(VF)* Có. Offset trỏ vào văn bản đã chuẩn hoá mà parser đọc; test xác nhận đoạn văn bản theo offset đúng là mệnh đề bị mất. Chẩn đoán không lặp lại nội dung mệnh đề.
13. **Có ca parser bỏ dữ kiện quan trọng mà vẫn dựng không?** *(VF)* Không trong các tập đã đo. Parser từ chối nếu còn mệnh đề dữ kiện hoặc mục tiêu chưa map; gate đọc mọi câu tiền đề.
14. **Có những thay đổi semantic tổng quát nào?** *(VF)* Bốn thay đổi, xem §2.
15. **Mỗi thay đổi có test âm và metamorphic không?** *(VF)* Có:
    - đáy không được khai báo → không đọc;
    - điểm đã định nghĩa → không định nghĩa lại;
    - (Q) chưa định nghĩa → không đọc;
    - "bằng 5" là dữ kiện, không phải câu hỏi;
    - đổi tên đỉnh T.MNPQ.
16. **Có handler theo case ID hoặc tên đỉnh không?** *(VF)* Không.
17. **Có thay đổi Source Gate policy không?** *(VF)* Không: `registry.py` không đổi kể từ `dcbedcb0d` ([source_gate_integrity.json](source_gate_integrity.json)).
18. **Tỷ lệ hiểu đề trước/sau trên development?** *(VF)*
    - Tập phát triển: đọc trọn 26 → 30/37; phục vụ được 19 → 23/37; đúng kỳ vọng 27 → 31/37.
    - 27 đề thật: không đổi (16 đọc trọn, 8 phục vụ được).
    - Đây là số đo trên tập phát triển, không phải bằng chứng tổng quát hoá.
19. **Có chạy lại W2/W3 còn khoá để tune không?** *(VF)* Không: 0 dòng.
20. **Hai ca wrong-served lịch sử được giữ và diễn giải ra sao?** *(VF)* Giữ nguyên: W2 2/48, W3 0/72 và 2 ca WRONG_SERVED theo luật đã đăng ký. Ghi chú hậu nghiệm của run trước đã giải thích; run này không sửa lại số.
21. **Âm văn bản và âm payload đã tách chưa?** *(VF)* Rồi ([text_vs_payload_negative_evaluation.json](text_vs_payload_negative_evaluation.json)):
    - Track A, lời đề: mâu thuẫn, thiếu dữ kiện, điểm không hợp lệ, quan hệ không thoả được, mặt không duy nhất, đối tượng không tồn tại, mục tiêu chưa hỗ trợ, mục tiêu viết như giả thiết → 8/8 bị từ chối.
    - Track B, payload đưa vào `run_typed_fact_next_v2_route`: quote không có trong nguồn, bỏ mệnh đề, thay giá trị, ký hiệu khác văn bản, cờ verified giả, dữ kiện bài khác, thực thể không tồn tại, nguồn bị cắt → 8/8 bị chặn với mã riêng. Payload đối chứng hợp lệ được phục vụ.
22. **Ảnh nhiều đề còn bị tự gộp bao nhiêu ca?** *(VF, trang tổng hợp)* 0/26: trang xếp chồng 0/20, trang hai cột 0/6. Trước run: 5/26.
23. **Ảnh một đề bị báo nhầm nhiều đề bao nhiêu ca?** *(VF)* Ở tầng sản phẩm: 0/25. Ở tầng bộ phát hiện vẫn tách nhầm 11/25, nhưng tín hiệu OCR (≤ 1 tiêu đề **và** ≤ 1 nhóm phương án) giữ trọn trang ([single_problem_false_split_audit.json](single_problem_false_split_audit.json)).
24. **Có lấy lẫn nội dung bài bên cạnh không?** *(VF/INF)*
    - Trang xếp chồng: 46/48 lựa chọn sạch. Hai ca còn lại có độ chứa của bài đích thấp (0,36 và 0,27) vì OCR đọc yếu; độ chứa của bài bên cạnh lần lượt là 0,01 và 0,18.
    - Trang hai cột: 9/12 sạch.
    - Phần trùng 5-gram ≈ 0,07–0,11 với bài bên cạnh là chữ khuôn mẫu ("Cho hình …"), không phải dữ kiện.
25. **Có gắn nhầm hình minh họa không?** *(VF)* 0 khối hình bị gán cho hai bài; 56/58 dải có hình riêng ([diagram_to_problem_association.json](diagram_to_problem_association.json)). Dữ kiện chỉ có trên hình không bao giờ thành typed fact.
26. **Có phát hiện trang nhiều bài không có tiêu đề "Câu N" không?** *(VF)* Có với đề trắc nghiệm, qua nhóm phương án. Trang nhiều bài không có phương án và không có tiêu đề: chưa phát hiện được (NM, backlog).
27. **Khi không chắc chắn, hệ có hỏi chọn vùng không?** *(VF)* Có: trả `needs_selection` kèm dải, hoặc `AMBIGUOUS_PROBLEM_BOUNDARIES` kèm lời nhắn chụp sát bài. Không bao giờ gửi cả trang đi.
28. **Người học có đổi vùng sau khi chọn được không?** *(VF)* Có. E2E đóng bảng xác nhận, tải lại và chọn bài khác; văn bản soát lại theo đúng lựa chọn mới.
29. **OCR span có bị gắn nhầm sang bài khác không?** *(VF)* Không. Dải là các byte ảnh mới nên OCR, span và offset là của riêng dải. Id dải cũ hoặc lạ bị từ chối, không đoán ([ocr_confirmation_state_integrity.json](ocr_confirmation_state_integrity.json)).
30. **Cache có bị dùng lại sai sau khi đổi vùng không?** *(VF/INF)* Không. Cache OCR khoá theo byte, cache phân tích khoá theo văn bản đã xác nhận. Reducer của frontend thay toàn bộ trạng thái ở mỗi phản hồi `prepare`.
31. **Có cải thiện nào làm tăng thao tác xác nhận thừa không?** *(VF)* Không. Ảnh một bài 0/25 bị hỏi chọn, như trước; trang nhiều bài trước đây bị gộp nay phải chọn, đó là thao tác cần thiết.
32. **Bao nhiêu ảnh đi hết tới verified Scene3D?** *(VF)* 4/27 bài nghiệm thu (không đổi). Thêm vào đó, bài được chọn từ trang 2 bài ghép trong E2E được phục vụ ở 4/4 viewport.
33. **Bao nhiêu scene sai được phục vụ?** *(VF)* 0: nghiệm thu 0; đề thăm dò 0 (124/124 phép kiểm, 35/39 đúng kỳ vọng) ([scene3d_correctness_regression.json](scene3d_correctness_regression.json)).
34. **Có đáp án cuối nào bị hiển thị không?** *(VF/INF)* Frontend không đổi trong run này. Chính sách không hiện đáp số đã được E2E của các run trước kiểm. Run này không đo lại trên trang Scene3D.
35. **Browser E2E đạt kết quả gì?** *(VF)* Chọn bài: 4/4 viewport ([image_selection_browser_e2e.json](image_selection_browser_e2e.json)).
36. **Mobile có hoạt động đúng không?** *(VF)* 390×844: không tràn ngang, nút ứng viên cao 64 px, chọn và đổi bài được.
37. **Diagnostic overhead là bao nhiêu?** *(VF)* 0,17 ms mỗi lần gọi `diagnose`. Đề bị từ chối: trung vị 1,85 → 1,99 ms; đề phục vụ: 24,7 → 23,4 ms. `prepare` ảnh đơn: 2,84 → 3,11 s (máy dùng chung); trang ghép: 3,98 → 3,62 s ([performance_impact.json](performance_impact.json)).
38. **Có memory leak được chứng minh không?** *(NM)* Không đo lại, vì frontend không đổi. Kết luận cũ vẫn giữ: INCONCLUSIVE.
39. **Có bộ dữ liệu đánh giá độc lập mới không?** *(BL)* Không: `BLOCKED_DATA` ([new_locked_evaluation_status.json](new_locked_evaluation_status.json)).
40. **H-1 có tiếp tục niêm phong không?** *(VF)* Có, 94 dòng, 0 lần mở.
41. **Full regression kết quả ra sao?** *(VF)* Mọi cổng sản phẩm đạt ngay lần đầu: backend 14 422 test, frontend 2 047 test (§5).
42. **Publication HEAD còn bị chặn không?** *(BL)* Còn: 97 finding, tất cả `pending_exception`; `BLOCKED_PENDING_OWNER_REVIEW`; `FULL_RELEASE_GATE = BLOCKED_GATES_REMAIN`.
43. **Publication range scan kết quả thế nào?** *(VF)* Quét `dcbedcb0d..HEAD`: **PASS**, 0 vi phạm. Về quản trị vẫn bị chặn: blob lịch sử `2bfce9c8` và 97 finding ở HEAD đang chờ Owner. Agent không duyệt và không thêm ngoại lệ ([publication_gate_status.json](publication_gate_status.json)).
44. **Candidate freeze ở commit nào?** *(VF)* `18a7ba008` (sản phẩm `7315cf3b0`, measured_system `1f62a4a4…`, 116 file). Template K-1/S-2/R-1 được gắn lại ở `262edecea`, vẫn PENDING ([candidate_freeze.json](candidate_freeze.json)).
45. **Có merge, push, deploy hoặc live AI call không?** *(VF)* Không có.
46. **Những nguyên nhân semantic quan trọng nào chưa khắc phục?** *(VF/INF)*
    - Hàm của góc (côsin/tang): cần một phiên bản output-policy mới.
    - Điểm mô tả không tên trong premise (`INVALID_DESCRIBED_POINT` theo thiết kế R-1).
    - Thể tích khối con; điểm đối xứng.
    - Câu dài nối bằng dấu phẩy (gate báo `UNGROUNDED_VALUE`).
    - "(tham khảo hình vẽ)" nằm trong câu hỏi.
    - "Thiết diện do (P) cắt".
    - Câu hỏi đặt trước định nghĩa ("…, biết (P) …").
    - Ca thiếu ràng buộc còn báo là "không hiểu" thay vì `PLANE_NOT_UNIQUE`.
47. **Những tình huống ảnh nhiều đề nào còn chưa xử lý?** *(VF/INF)*
    - Trang nhiều bài tự luận (không có phương án, không đọc được tiêu đề).
    - Cột không tách được bằng một đường cắt sạch.
    - Ảnh chụp camera thật, nghiêng mạnh, chữ viết tay.
    - Một bài có hai hình mà không có phương án: chưa có ảnh để đo.
48. **Bước tiếp theo giá trị cao nhất?** *(INF)* Hai việc:
    - Một tập ảnh và đề thật có giấy phép và người kiểm (cần Owner quyết), vì mọi con số ở đây là development.
    - Về kỹ thuật: nâng output-policy để phục vụ côsin/tang của góc (3/27 đề thật đã hiểu đúng nhưng đang bị chặn), và mở rộng hợp đồng cho điểm mô tả trong premise. Đây là hai lỗ hổng phủ nhiều nhất trong các nguyên nhân gốc.

## 4. Tính toàn vẹn dữ liệu

- Tập phát triển (37 đề) do agent viết trong run này, là `NEW_DIAGNOSTIC_DEVELOPMENT`.
- 27 đề thật và 39 đề thăm dò là `DEVELOPMENT_EXPOSED`.
- Ảnh là 25 ảnh VMMU đã lộ. Trang nhiều bài là bố cục tổng hợp từ các ảnh đó, không phải ảnh chụp học sinh.
- W2/W3 vẫn khoá (trừ 2 ca đã lộ); H-1 niêm phong.
- Phép đánh giá tách đề chạy ở `cc449ae4b`. Bản sửa gán khối hình `7315cf3b0` được kiểm lại bằng E2E và phép đo liên kết hình, không chạy lại phép đánh giá tách đề.
- Không con số nào ở đây là bằng chứng tổng quát hoá.

## 5. Regression và publication

Chi tiết ở [full_regression_summary.json](full_regression_summary.json). Cây sạch, `ALLOW_LIVE_AI=0`. Verdict của bộ chạy là `INCOMPLETE_OR_FAIL` chỉ vì cổng publication HEAD; verdict tổng là **BLOCKED**.

| Cổng | Kết quả |
|---|---|
| backend pytest | **PASS**: 14 422 passed, 7 skipped, 3 deselected, 15 xfailed |
| frontend `test:wave` | **PASS**: 140 file, 2 047 test; tsc + vite build |
| demo replay · crash audit · docs IA | **PASS** |
| freeze verify | **PASS**: 116 file, `1f62a4a4…` |
| publication HEAD | **BLOCKED**: 97 `pending_exception` |
| publication range `dcbedcb0d..HEAD` | **PASS**: 0 vi phạm |

Trong quá trình phát triển, các lượt pytest có 13 test đỏ do measured system lệch khỏi bản đã đóng băng, đúng như dự kiến; sau khi đóng băng lại thì tất cả đều xanh. Ngoài bộ chạy: E2E chọn bài 4/4; độ đúng Scene3D 124/124; Track A 8/8, Track B 8/8.

## 6. Giới hạn

- Trình duyệt chạy headless trên máy host; xác nhận bằng script.
- Oracle là của agent (`AGENT_DIAGNOSTIC`); tiêu chí lẫn bài dùng độ chứa 5-gram so với bản chép của agent.
- Chưa có ảnh chụp thật, chữ viết tay, máy cấu hình thấp, học sinh thật hay H-1.
