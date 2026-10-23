# Review độc lập: sửa hiển thị A/B (Adapter /4)

Reviewer: subagent Claude ngữ cảnh mới, đọc-chỉ (không ghi repo/git, không mạng, không gọi model; probe trong thư mục
tạm ngoài repo). Người sửa: agent chính. Reviewer không phải curator holdout. Reviewer tự chạy test, probe và quét export;
không chỉ đọc báo cáo.

**Kết luận cuối: vòng 2 `PASS_WITH_FINDINGS`**, 0 BLOCKER, 0 MAJOR còn mở.

## Vòng 1: `50cee903..65cbdd6f` (product `665f542c`): `PASS_WITH_FINDINGS`

| id | mức | phát hiện | xử lý |
|---|---|---|---|
| F1 | MAJOR | Cờ tên khai chỉ bật khi có `DINH_CAT_CANH`; đề chỉ "dựng thiết diện … bởi (α)" (không khai cạnh cắt) vẫn ra `(MHH1)`, role mâu thuẫn notation (probe thật trên `PLANE-ONLY-construct` bỏ goal khối dẫn xuất) | **sửa** `41c7e6f8`: bật cho mọi luật mặt dẫn xuất; test mới `test_A_a_section_without_stated_cut_edges_still_shows_the_declared_name` (đỏ trước) |
| F2 | MINOR | Role "song song với (ABC)" trong khi đề viết "(ABCD)" (DEV01, DEV09, PARTIAL-2of3); test chỉ kiểm tiền tố | **sửa** `41c7e6f8`: dùng tên mà câu nguồn chứa (mặt của khối hoặc điểm của planner); test A khớp toàn câu và đòi vật được nêu có trong quote (đỏ trước 3 cảnh) |
| F3 | MINOR | Look-behind không loại `.` (`V(S.MII1)` → `V(S.thiết diện…)`); chữ đầu câu không viết hoa; nhánh khối không có `kd` rơi vào "Đoạn của thiết diện" | **sửa** phần regex + hoa (`_thay_ten` cấp module, test tham số hoá, đỏ trước); nhánh khối không `kd`: **còn lại**, không với tới từ corpus (reviewer đồng ý là residual; khuyên fail-closed) |
| F4 | MINOR | Inspector lăng trụ "Đỉnh 1 – M – Đỉnh 3"; sửa được ở frontend bằng dữ liệu có sẵn (`endpoint_entities`, nhãn mô tả của I/I1), **không cần đổi contract** | **không sửa**: `sectionDetails` dùng chung với tuyến mặc định; Owner quyết (xem `SCENE3D_PROVENANCE_COMPATIBILITY.md` §4, đã đính chính theo F4) |
| F5 | NOTE | `envelope.config.frames[].narration` (18/22 cảnh) còn "qua ba điểm M, H, H1", "Dựng khối S.MII1…"; bằng byte lịch sử, không render trên đường Scene3D (`SimulationWorkspace.tsx:497-525`) nhưng có trong payload API | khai, không sửa (envelope dùng chung `compile_semantic_program_to_envelope`) |
| F6 | NOTE | `name_diff` chỉ chứng "chỉ khoá tên đổi", không chứng "tên nói cùng nghĩa"; reviewer đọc tay toàn bộ `before-after.json`: ổn | khai |
| F7 | NOTE | Giá trị trung gian nay hiện trong bước của `PLANE-ONLY-ratio-described` (trước bị nhãn sai che); là `FINAL_RESULT`+`target`, `tapKetQuaCuoi` ẩn; nhất quán với PARA-0 | không cần |
| F8 | NOTE | Có từ trước: "BB'" ASCII ở vài bước, bước 11 nhắc (α) trước bước dựng, role M "Trung điểm của A và A′"; `kiemSections` không kiểm trường tên | backlog |

## Vòng 2: `65cbdd6f..57138dbb` (product `41c7e6f8`, freeze `56bdf9b9`): `PASS_WITH_FINDINGS`

F1, F2, F3 xác nhận đã sửa bằng probe chạy lại: section-only ra `(α)`, ba role "(ABCD)", `_thay_ten` không đụng tên có dấu
chấm/phẩy trên. `route_d_equal` 22/22; 25 refusal không đổi.

| id | mức | phát hiện | xử lý |
|---|---|---|---|
| R1 | MINOR | 22/22 cảnh: `explanation` của event CREATE mặt phẳng còn "Dựng mặt phẳng (α) qua ba điểm M, H, H1." (bằng byte lịch sử). Không render khi có `learner_text` (`scene3d-model.ts:688`; bước hiện "Dựng (α).") và đúng sự thật (H, H1 là điểm dựng có tên trên hình); nhưng `_learner()` của test tuyên bố phủ "mọi chuỗi frontend render" và lệnh cấm hoán vị không bắt dạng "qua ba điểm …" | **chưa sửa**: khai cho Owner. Sửa ⇒ thêm một vòng product/freeze/T3/browser |
| R2 | NOTE | `_thay_ten` viết hoa sau `:`; "Khối S.MII1" → "Khối khối chóp …". Không có trong corpus (reviewer đã quét) | khai |

## Lệnh reviewer đã chạy (tóm tắt, exit code)

`git log/diff` (0) · `pytest test_section_display_identity.py test_typedfactnext_planner_bridge.py`: vòng 1 112 passed, vòng 2
117 passed (0) · `pytest test_structured_geometry_relations.py -k test_Y`: 14 passed (0) · `freeze_evaluation_candidate.py
--verify` (0, MATCH) · probe F1 offline có audit-hook chặn mạng (0) · probe `_thay_ten` (0) · quét export toàn chuỗi (0) ·
`git status --porcelain` rỗng.
