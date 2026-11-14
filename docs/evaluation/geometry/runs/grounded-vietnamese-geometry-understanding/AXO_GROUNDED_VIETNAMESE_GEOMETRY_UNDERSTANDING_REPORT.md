# AXO: đọc đề hình học tiếng Việt có căn cứ nguồn và độ phủ ngữ nghĩa

Run `grounded-vietnamese-geometry-understanding` · 2026-11-15 · nhánh `feat/local-first-geometry-understanding`
· bắt đầu ở `83fdc3071` · `CACHE_VERSION` 138 → **139** · 0 lượt gọi AI live · không merge, push hay deploy.

Nhãn: **VF** = VERIFIED FACT, **INF** = INFERENCE, **HYP** = HYPOTHESIS, **NM** = NOT_MEASURED, **BL** = BLOCKED.

| Mốc | Commit |
|---|---|
| Sửa parser + Source Gate (đọc có căn cứ, không nới cổng), cache 139 | `ac276a5c9` |
| Hai kỳ vọng test nêu lại (cùng nguyên nhân, phát hiện sớm hơn một tầng) | `ad090cead` |
| Lời chẩn đoán cho người học khi tuyến cục bộ đọc thiếu đề (backend + frontend) | `d222e6d9b` |
| Công cụ, corpus phát triển, handoff frontend | `cbcd8af2d` (trường commit của candidate) |
| Candidate đóng băng | `63def519a`, hệ đo `c25f9695…`, 117 file, cây sạch, `--verify` PASS |

## 1. Kết luận chính

- **Bộ đọc đề hiểu thêm năm dạng câu tiếng Việt mà không nới Source Gate (VF).**
  1. Đáy không tên: "có đáy là hình vuông cạnh a" gắn với khối đã khai báo, chỉ khi không có mệnh đề đổi chủ ngữ đứng trước.
  2. "Góc giữa cạnh bên và mặt đáy": một góc duy nhất, nhưng chỉ khi hình chóp đều. Chóp thường thì từ chối vì mơ hồ.
  3. Ký hiệu lăng trụ không có dấu chấm ("ABCA'B'C'"): chỉ được tách khi đỉnh trên đúng là đỉnh đáy có phẩy, theo đúng thứ tự.
  4. "Tam giác SAB cân" không nêu đỉnh: hai cạnh bên phải ở góc vuông mà một lệnh gọi hợp lệ khác chứng minh.
  5. "Diện tích đáy bằng V": hiểu là diện tích đáy của khối duy nhất trong đề.
- **Không còn bỏ dữ kiện trong im lặng (VF).** Nếu một giá trị trong phần giả thiết không được trích dẫn của mục nào đọc tới (ví dụ "chu vi đáy bằng 8"), mệnh đề bị đánh `UNREAD_VALUE`. Đề có mệnh đề như vậy không bao giờ được coi là đã đọc trọn (`LOCAL_PARSE_COMPLETE`).
- **Người học biết phần nào của đề chưa được đọc (VF).** Trước đây một đề đọc thiếu chỉ nhận lời "AI tạm tắt". Nay lời báo nói rõ hệ thống chưa đọc được gì và trích lại đúng câu chữ của em: thực thể, mục tiêu, quan hệ, phép dựng chưa hỗ trợ, thiếu dữ kiện, chứng minh hay mâu thuẫn. Khi nguyên nhân là năng lực của hệ thống, lời báo không khuyên em viết lại đề. Không lộ mã máy hay ID. Phân loại hạ tầng (503, `INFRASTRUCTURE_FAILURE`) giữ nguyên.
- **REAL27 (dữ liệu phát triển đã lộ, VF):**
  - Văn bản: 12 → **15/27** dựng được; khớp đáp án dataset 9 → **12**; 3 ca hỏi giá trị lượng giác được dựng góc nhưng không trả số.
  - Ảnh: 7 → **9/27**; khớp đáp án 4 → **6**.
  - Không có ca nào phục vụ sai cảnh. 116 cảnh đã phục vụ ở cả hai phía giữ nguyên dấu vân toán học.
- **Phép kiểm đã chạy (VF):**
  - E2E: 61/61 trên 4 khung nhìn (lần đầu bị `timeout` của wrapper cắt sau 46/46 lượt pass; log được giữ).
  - Backend: 14 638 passed. Frontend: 2 058 passed, build PASS.
  - Corpus phát triển COMP đạt kỳ vọng 102 → 111/112.
- **Phát hành bị chặn (VF):** publication HEAD còn 97 finding chờ owner; FULL_RELEASE_GATE BLOCKED_GATES_REMAIN.

## 2. Trả lời 55 câu hỏi

1. **VF.** `6da2795a4..83fdc3071` gồm 31 file, tất cả là báo cáo, receipt, manifest và tài liệu sống của run trước. Không có file sản phẩm hay test (`head_candidate_reconciliation.json`).
2. **VF.** Không.
   - Ở đầu run, candidate `225f4bba…` vẫn khớp `83fdc3071`.
   - Mọi thay đổi sản phẩm của run (`ac276a5c9`, `ad090cead`, `d222e6d9b`) đều nằm trong candidate mới `c25f9695…`.
   - Sau commit `cbcd8af2d`, không file nào dưới `backend/app` hay `frontend/src` thay đổi.
3. **VF.** Chưa tích hợp; phân loại như sau (`frontend_handoff_reconciliation.json`):
   - FE-2 `BLOCKED_OWNERSHIP`. Blob fixture của thư viện không đổi tại HEAD `8af24a5c8`. Patch bàn giao (9 hunk thêm `readout_ids`) áp sạch.
   - FE-3 `BLOCKED_DEPENDENCY`. Generator của thư viện cần `circumscribed_sphere`, mà kernel nhánh này không có.
   - FE-4 `BLOCKED_OWNERSHIP`. Chưa worktree nào vẽ `auxiliary_points`.
   - FE-6 `MERGE_NOTE`.
4. **VF.** Không. Worktree thư viện chỉ được đọc qua `git` (status/show/grep). Task ghi 96 mục chưa commit; lúc tôi đọc có 78–83 mục, vì phiên kia vẫn đang làm việc.
5. **VF.** Trước sửa có 15 ca bị từ chối, theo nguyên nhân gốc:
   - 3 `UNRECOGNIZED_GOAL`, 3 `SOURCE_PROVENANCE_MISSING`, 3 `UNRECOGNIZED_GEOMETRIC_ENTITY`, 2 `INCOMPLETE_FACT_EXTRACTION`.
   - 1 mỗi loại: `DESCRIBED_POINT_IN_PREMISE_UNSUPPORTED`, `PLANNER_COMPOSITION_UNSUPPORTED`, `UNSUPPORTED_POINT_CONSTRUCTION`, `FREE_POINT_UNDERDETERMINED`.

   Lý do đầu cuối của 14 ca là `LIVE_AI_DISABLED` (`real27_root_cause_matrix.json`).
6. **VF.** Có ba ca.
   - r284 bị ghi `SOURCE_PROVENANCE_MISSING`. Thật ra là luật gắn vai của cổng không đọc được đáy không nhãn; trích dẫn không thiếu.
   - r463 và r460 bị ghi lỗi đọc đề. Sau sửa, đề đã được hiểu trọn, và lý do từ chối thật là năng lực (`MISSING_DIMENSION`: chiều cao suy từ góc, cạnh góc vuông suy từ cạnh huyền).
   - Nhóm chẩn đoán gộp hai ca này vào `INSUFFICIENT_CONSTRAINTS`, nghe như đề thiếu dữ kiện. **INF:** nhãn đó nên tách thành "đã hiểu, thiếu năng lực".
7. **VF.** Thông tin mất đầu tiên ở **luật mệnh đề** (`_parse_clause_into_ast`) với 5 dạng câu ở §1, và ở **luật gắn vai của Source Gate** với đáy không nhãn. Một chỗ thứ ba: giá trị trong câu đã nhận dạng bị bỏ mà không ai báo (completeness).
8. **VF.** Không. Có 0 đề `LOCAL_PARSE_COMPLETE` mà còn mệnh đề `UNPARSED_*` trên 215 văn bản phát triển (`clause_level_semantic_coverage.json`). `UNREAD_VALUE` bắt được 4 trường hợp: 3 ca âm của corpus và r537.
9. **VF.** Đáy không tên của chóp và của hộp chữ nhật; cạnh bên của chóp đều; ký hiệu lăng trụ không dấu chấm; tam giác cân không nêu đỉnh; diện tích đáy không tên.
10. **VF.** Có, nhưng chỉ khi đối tượng xác định duy nhất từ đề. "Đáy" là đáy của khối duy nhất, và "cạnh bên" chỉ đại diện được khi chóp đều. Đối tượng mô tả mà không xác định thì bị từ chối: "điểm thuộc cạnh SB" cho `FREE_POINT_UNDERDETERMINED`; "trung điểm" không có toán hạng cũng bị từ chối.
11. **VF.** Không. Run này tự đặt 0 thực thể. Ký hiệu lăng trụ bị xáo thứ tự ("ABCB'A'C'") bị từ chối thay vì đoán.
12. **VF.** Có, với các ca có sẵn: `order_*` và `order_goal_first` vẫn đi qua `_clause_order`. Run này không đổi thứ tự xử lý. 19 ca tham chiếu giữa các mệnh đề: 0 lệch kỳ vọng (`cross_clause_reference_tests.json`).
13. **VF.** Trên REAL27, 1 trong 3 ca `UNRECOGNIZED_GOAL` được sửa: r538 "góc giữa cạnh bên và mặt đáy". Trên corpus: 2 ca chóp đều mới, cộng DEV37 `elliptical_role`, một kỳ vọng cũ đã được thay (lý do ở `goal_extraction_before_after.json`). r256 (lỗi gõ "đên") và r488 vẫn chưa đọc được.
14. **VF.** Có. Khi đề hỏi giá trị cos/sin/tan, câu trả lời là `GOAL_VISUALIZATION_READY_NUMERIC_NOT_ANSWERED` và `source_goal_completion` ghi là không trả số. Có 3 ca REAL27 như vậy (r258, r498, r559), cả văn bản lẫn ảnh. `output-policy/1` không đổi.
15. **VF.** Không. Các ca âm "đã cho … tính" và "chứng minh SA ⊥ đáy" vẫn bị từ chối. "Chứng minh SA ⊥ (ABCD)" khác với cùng quan hệ khi là giả thiết: cặp tối thiểu `gv_pair_perp_*` PASS.
16. **VF.** Có. Ví dụ "Tính thể tích … và tính khoảng cách …" phục vụ hai mục tiêu `a³/3` và `a√3/3`, kể cả trong E2E (`gv_two_goals`).
17. **VF.** Có. Đã kiểm 852 mục: 0 trích dẫn không nằm nguyên văn trong văn bản chuẩn hoá, và 0 span mệnh đề lệch nguồn (`source_span_provenance_audit.json`).
18. **VF.** Không. Spans và trích dẫn là offset vào cùng văn bản đã chuẩn hoá mà cả parser lẫn cổng đều đọc. Biến thể Unicode như phẩy ′ và dấu trừ được quy về trước khi tách mệnh đề.
19. **VF.** Không (câu 17).
20. **VF.** Không. Góc vuông ở đỉnh tam giác cân là `VERIFIED_DERIVED_FACT`: một lệnh gọi khác chứng minh, và `_can_co_goc_vuong` kiểm. Nó không bao giờ được trích như dữ kiện nguồn.
21. **VF.** Không. Không có luật nào bị gỡ hay nới. Mỗi cách đọc mới đi kèm một luật đối tượng. 16 ca âm đều bị từ chối (`source_gate_integrity.json`).
22. **VF.** r284 và r295: đáy không nhãn nay gắn vai theo thứ tự mệnh đề.
23. **VF.** r537 vẫn bị từ chối: diện tích đáy viết theo a² không biểu diễn được (bộ đọc số chỉ giữ độ dài). Trên corpus, ca chủ ngữ đổi trước "có đáy …" (`gv_base_unnamed_subject_first`) vẫn bị từ chối.
24. **VF.** Không. 12 đáp số mới phục vụ của corpus khớp oracle toạ độ thực độc lập trong `tools/derive_receipts.py`, không dùng kernel. 116 cảnh có cùng dấu vân toán học trước và sau.
25. **VF.**
    - COMP đạt kỳ vọng 102 → 111/112. Ca còn lệch, `dp_unnamed_through_point`, đã lệch từ trước và không đổi.
    - Số được phục vụ: COMP 54 → 63; DEV37 27 → 28; PROBES 23 → 23.
26. **VF.** 16/16 ca âm `gv_` bị từ chối.
27. **VF.** 17/17 ca metamorphic cho cùng đáp số, ví dụ đổi tên đỉnh, có hay không câu "như hình vẽ", có hay không dấu chấm. 12/12 cặp tối thiểu đạt kỳ vọng ở cả hai vế.
28. **VF.** Không. `git grep` mã định danh ca trong `backend/app` và phần frontend đã sửa: 0 kết quả. Luật đọc dạng câu, không đọc chuỗi đề cụ thể.
29. **VF.** Văn bản 12 → 15/27 dựng được. Khớp đáp án 9 → 12 (r284, r295, r538).
30. **VF.** Ảnh 7 → 9/27; khớp đáp án 4 → 6 (r295, r538). r284 vẫn trượt ở OCR.
31. **VF.** 13 cảnh mới, đều qua audit nhân quả với 0 vi phạm: 3 REAL27, 9 COMP, 1 DEV37.
32. **VF.** Trả số thật: văn bản 12/27, ảnh 6/27. Không có ca trực quan hoá nào được tính là đã trả lời.
33. **VF.** Không. `wrong_scene_served` rỗng cả văn bản lẫn ảnh, oracle 12/12 khớp.
34. **VF.** 12 ca văn bản chưa phục vụ:
    - Năng lực: r463, r460, r537, r266, r277, r491.
    - Phân đoạn và chính tả: r513, r256 (chờ quyết định S-1 về dấu).
    - Điểm mô tả trong giả thiết: r254.
    - Mục tiêu nhiều phần: r488.
    - Bài toán mô hình hoá, ngoài phạm vi: r461, r475.
35. **VF.** Ảnh có 18 ca chưa phục vụ:
    - 6 do OCR: 5 ca văn bản được phục vụ nhưng bản OCR khác biểu diễn; r695 lệch ở câu hỏi.
    - 7 do parser: bản OCR nhất quán với đề, nhưng chính đề cũng bị từ chối.
    - 5 vướng cả hai.
36. **VF.** Không. Cờ duy nhất là r492, dương tính giả từ vựng: "vuông tại A." trông giống nhãn phương án, còn biểu diễn trùng hoàn toàn với đề. Bộ đo đầu tiên nhầm 4 phương án của chính đề là đề khác; bản đó được giữ trong `logs/`.
37. **VF.** 61/61 trên 1920×1080, 1366×768, 768×1024 và 390×844. Gồm 12 lượt từ chối có lời giải thích đúng loại, không lộ mã, không dựng cảnh.
38. **VF.** Không. Toàn bộ pytest PASS, gồm kernel, certificate/2 và chứng chỉ thiết diện. Ở hai phía có 48 và 52 mục tiêu góc được chứng minh; 0 lần vượt ngân sách.
39. **VF.** Có, 138 → 139. Parser và cổng quyết định khác trên cùng văn bản, trong khi khoá Route D không phụ thuộc parser.
40. **VF.** Không. Một envelope được phục vụ dưới `138:route-d`, với văn bản mà cổng completeness mới từ chối, bị MISS. Dưới 139 nó được phát lại; đây là đối chứng (`test_cache_grounded_understanding_invalidation.py`). Thay đổi chẩn đoán `d222e6d9b` chỉ chạm phản hồi 503 và từ chối, mà cả hai không bao giờ được cache.
41. **VF.** Trên cùng 54 đề được phục vụ ở cả hai phía:
    - Parse lạnh 11,3 → 12,1 ms.
    - End-to-end dưới cProfile 136 → 140 ms.
    - Wall ấm 53 → 65 ms.

    Trung vị đề bị từ chối 2,3 → 3,7 ms (khác tập: 33 → 22 đề, vì một số đề nay được phục vụ). **INF:** chênh lệch wall ấm nằm trong nhiễu của máy dùng chung, vì parse đã cache trong tiến trình; cần máy cô lập để kết luận.
42. **VF/INF.** Không chứng minh được rò rỉ bộ nhớ.
    - 12 lần chuyển đề: heap sau GC tăng 3,1 MB, gồm cả lịch sử học sinh lưu từng lượt.
    - 15 lần duyệt timeline không phân tích lại: +1,7 MB.
    - Số canvas không đổi; ghi chú số không bị mang sang đề khác.

    `MEMORY_LEAK = INCONCLUSIVE`, vì không có bằng chứng tăng tuyến tính dài hạn. Sáu `foreign_ids` là chính thiết diện của đề hiện tại (hậu tố `#4cf`), do bộ đo chỉ tách `::`.
43. **VF.** Không. 0 dòng H-1 mở, 0 dòng W2/W3 đọc, 0 file dữ liệu holdout được tham chiếu.
44. **VF.** Không. `NEW_INDEPENDENT_EVALUATION = BLOCKED_DATA`, `INDEPENDENT_GENERALIZATION = NOT_MEASURED`.
45. **VF.** 14 638 passed, 7 skipped, 3 deselected, 17 xfailed. Demo replay, crash audit, docs IA và freeze verify đều PASS.
46. **VF.** Vitest 141 file, 2 058 test PASS (cả T2 lẫn toàn bộ). `tsc -b` cùng `vite build` PASS.
47. **VF.** Lưu ở `63def519a`; trường commit `cbcd8af2d`.
48. **VF.** Có. `--verify` cuối khớp `c25f9695…` với 117 file, và các template chờ owner đã gắn lại hệ đo này. Sau candidate chỉ có commit đo, receipt và tài liệu.
49. **VF.** 97, cả 97 đang chờ ngoại lệ của owner; không phát sinh thêm. PUBLICATION_HEAD = BLOCKED_PENDING_OWNER_REVIEW.
50. **VF.** PASS: `83fdc3071..HEAD` có 75 file, 0 vi phạm.
51. **VF.** Không merge, push hay deploy. Không gọi AI live: `ALLOW_LIVE_AI=0` suốt run.
52. **VF/INF.** Các giới hạn còn lại:
    - Diện tích hay giá trị theo a² không biểu diễn được.
    - Chiều cao suy từ góc và cạnh góc vuông suy từ cạnh huyền chưa có.
    - Đề lỗi chính tả cần quyết định S-1.
    - Câu thiếu dấu chấm và mặt phẳng không có ngoặc chưa đọc được.
    - Điểm mô tả không tên làm toán hạng giả thiết vẫn ngoài R-1.
    - Đề chứng minh không được dựng.
    - Nhãn chẩn đoán `INSUFFICIENT_CONSTRAINTS` gộp cả ca đã hiểu mà thiếu năng lực.
    - Trên giao diện, tiêu đề từ chối do mâu thuẫn vẫn là "Đề bài chưa được hỗ trợ"; phần mô tả thì nói đúng là mâu thuẫn.
53. **VF.** FE-2, FE-3, FE-4, FE-6 (câu 3). Thêm một quyết định sư phạm còn mở: dấu góc vuông vẫn bị ẩn khi chính nó là đáp số.
54. **INF.** Đủ để demo offline trong các trường hợp sau:
    - Chóp, lăng trụ, hộp với các dạng câu của corpus.
    - Mục tiêu khoảng cách, góc, thể tích, thiết diện và giao tuyến.
    - Đề nhiều mục tiêu.
    - Từ chối có giải thích.
    - Ảnh một bài sau khi người học xác nhận OCR.

    Chưa đủ cho dữ liệu chưa lộ hay cho học sinh thật.
55. **INF.** Giá trị lớn nhất tiếp theo, theo thứ tự:
    - Tách "đã hiểu, thiếu năng lực" khỏi "thiếu dữ kiện" trong chẩn đoán.
    - Mở rộng bộ đọc số cho giá trị a²/a³.
    - Thêm hàm dựng chiều cao từ góc cho trước, đi qua `REGISTRY` đóng.
    - Đều không nới cổng. Sau đó cần một tập độc lập chưa lộ để đo tổng quát hoá.

## 3. Bằng chứng

Các artifact 1–32 nằm trong thư mục run và được băm trong `run.json`. Công cụ ở `tools/`: `semantic_compare.py`, `scene_sweep.py`, `acceptance.py`, `ocr_semantic_consistency.py`, `scene3d_goal_e2e.mjs`, `perf.py`, `run_full_regression.py`, `derive_receipts.py`.

Hai bộ đo được sửa trước khi diễn giải; bản đầu giữ trong `logs/`:

- Kiểm cô lập đa đề, nhầm phương án của chính đề.
- Đo tầng parser trúng cache, nên thêm phép đo parse lạnh.

Lần E2E đầu bị cắt bởi timeout và được giữ ở `logs/e2e-first-attempt/`.
