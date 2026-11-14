# AXO: tính nhân quả của phép dựng Scene3D và tính toàn vẹn của vết sư phạm

Run `scene3d-causal-pedagogical-integrity` · 2026-11-14 · nhánh `feat/local-first-geometry-understanding`
· bắt đầu ở `9d0949b09` · `CACHE_VERSION` 137 → **138** · 0 lượt gọi AI live · không merge, push hay deploy.

Nhãn: **VF** = VERIFIED FACT, **INF** = INFERENCE, **HYP** = HYPOTHESIS, **NM** = NOT_MEASURED, **BL** = BLOCKED.

| Mốc | Commit |
|---|---|
| Sửa 1: cờ phụ trợ thừa, tiên quyết trực quan, góc vuông, cache 138 | `70befe6f1` |
| Sửa 2: phương pháp giao tuyến cho đỉnh thiết diện (GEO-BE-V9415-001 trên Route D) | `fac7ead77` |
| Catalog `geometry-samples.json` tái sinh (hình học không đổi) | `af3e4dddd`, `a2874d273` |
| Bundle fixture thay thế (hai lần, bundle cũ giữ nguyên) | `d1789d71a`, `1a1b6834a` |
| Candidate đóng băng | `4ddec5666`, trường commit `634565203`, hệ đo `225f4bba…`, 117 file, cây sạch |

## 1. Kết luận chính

- **Bốn ticket V9.4.15 trên HEAD hiện tại.** Commit `9d5e9b408` của owner đã xử lý phần lớn ở backend. Phiên frontend đã tích hợp các bản vá vào HEAD thư viện (`b5810dcc3`). Run này kiểm lại độc lập bằng một bộ kiểm chỉ đọc cảnh đã tuần tự hoá (`tools/causal_audit.py`). Kết quả: 004 và 003 vẫn còn trên **bản sao ở nhánh này** (fixture tĩnh cũ), nhưng sạch trên bản thư viện; 002 sạch trên Route D. Còn 001 tái hiện được **trên Route D** và đã được sửa ở run này.
- **Năm khoảng hở backend thật do run này tìm ra và sửa (VF):**
  1. Route D gắn cờ "phụ trợ thừa" cho **chính giao tuyến đề hỏi** và cho một điểm đề nêu. Nguyên nhân: cờ được tính khi chưa có `targets`.
  2. Một đại lượng tự do (bán kính R đề cho) nằm trong `visible_prerequisites`.
  3. Hai mặt phẳng vuông góc và hai đường chéo nhau vuông góc đã được chứng minh 90° nhưng không được vẽ.
  4. Adapter chưa ràng buộc *loại* góc vuông được vẽ với mục tiêu.
  5. Đỉnh thiết diện qua ba điểm không song song xuất hiện mà không có lý do. Nay chúng được giải thích theo phương pháp giao tuyến của sách giáo khoa, kiểm chính xác trên ℚ.
- **Hình học không đổi (VF).** Trên 111 cảnh Route D được phục vụ, trước và sau sửa có cùng đáp số chính xác, toạ độ điểm, đỉnh thiết diện, chứng chỉ và trạng thái phục vụ. Thay đổi duy nhất về hình là 3 phép dựng góc 90° được thêm. REAL27 không đổi: văn bản 12/27, ảnh 7/27.
- **Phép kiểm đã chạy (VF):** 12/12 đột biến nhân quả bị bắt; E2E 43/43 trên 4 khung nhìn; backend 14 610 PASS; frontend 2 057 PASS kèm build.
- **Phát hành bị chặn (VF):** publication HEAD còn 97 finding chờ owner; FULL_RELEASE_GATE BLOCKED.

## 2. Trả lời 55 câu hỏi

1. **VF.** Có. HEAD `9d0949b09`, freeze `f30363597` (`610b4ee1…`, 117 file), cache 137, `--verify` khớp, cây sạch.
2. **VF.** Có. Lúc bắt đầu, `--verify` khớp mã sản phẩm của HEAD. Sau run, candidate mới `4ddec5666` cũng khớp (`225f4bba…`).
3. **VF.** Trên HEAD `9d0949b09` của nhánh này và HEAD `8b0c270ad` của thư viện (`v9415_issue_reproduction_matrix.json`):
   - 004 (`K` dùng `SB_line` chưa có CREATE): còn trên bản sao ở nhánh này, đã sửa ở thư viện.
   - 003 (`A_prime`, `D` → `vec_OB`, `vec_OC`): còn ở nhánh này, sạch ở thư viện.
   - 002: 0 câu MEASURE chung chung trên 111 cảnh Route D.
   - 001: tái hiện trên Route D. Với (MNP), M là trung điểm SA, N trung điểm BC, P trung điểm CD, các đỉnh trên SB và SD không có lý do.
4. **VF.** Thuộc backend: 002 (generator, owner đã sửa), một phần 003 (`visible_prerequisites`, run này tổng quát hoá), và 001 trên Route D (run này sửa). Run này tìm thêm hai lỗi backend: cờ phụ trợ thừa trên Route D và góc vuông không được vẽ.
5. **VF.** 004 là fixture tĩnh viết tay của frontend. Fixture vòng tròn ngoại tiếp của 003 cũng là fixture tĩnh, dù owner đã bàn giao bản do backend dựng.
6. **VF.** `geometry-samples.json` có generator canonical ở nhánh này (`build_geometry_samples.py`). `advanced-geometry-samples.json` chỉ có generator ở nhánh thư viện, và generator đó cần `circumscribed_sphere`, không có trong kernel của nhánh này. Hai fixture Scene3D kia không có generator.
7. **VF.** Không. Worktree thư viện có 96 mục chưa commit của phiên khác; tôi chỉ đọc nó qua `git show`, không chuyển nhánh, reset, clean hay sửa.
8. **VF.** Có, và dùng biểu diễn sẵn có:
   - `computational_depends` cho phụ thuộc toán học;
   - `construction_lineage`, `justification` và `certified_relation` cho quan hệ ngữ nghĩa;
   - `visible_prerequisites` cùng thứ tự sự kiện cho thứ tự dựng.

   Không thêm DAG mới.
9. **VF.** Không, trên 111 cảnh Route D: `CAUSAL_BIRTH_ORDER` = 0 cả trước lẫn sau. Trong trình duyệt, `late_prerequisites` rỗng ở cả 43 lượt.
10. **VF.** Đây là đường nguồn. Bản thư viện tạo nó (CREATE, phụ thuộc S và B) trước K. Run này không thêm CREATE giả nào.
11. **VF.** Không, ở bản thư viện và bản owner bàn giao: `visible_prerequisites` của A′ là [A, B, O], của D là [A′, C, O]. Bản sao ở nhánh này vẫn cũ.
12. **VF.** Có. `computational_depends` giữ nguyên; tôi chỉ đổi quy tắc *trực quan* với đại lượng không có phụ thuộc. Catalog tái sinh giữ nguyên vật, sự kiện và giá trị.
13. **VF.**
    - Route D: 0 → 0.
    - Fixture ở nhánh này: 1 (`K`/`SB_line`).
    - Bản thư viện: 0.
14. **VF.** Không. Đột biến "chèn vật không nguồn" bị bắt (`UNRESOLVED_REFERENCE`).
15. **VF.** Route D, 145 sự kiện MEASURE: 0 câu chung chung. 72 sự kiện không có `measured_quantity`; đó là các bước nội bộ "Lấy vectơ AB" (`non_visual`), timeline gộp chúng lại và chúng không khẳng định quan hệ nào.
16. **VF.** 11 sự kiện có giá trị 0 trong catalog nâng cao, đã sửa ở `9d5e9b408` (bảng của owner). Run này không cần sửa thêm sự kiện MEASURE nào.
17. **VF.** Không. 0 vi phạm nhất quán: khẳng định vuông góc mà góc khác 0, góc 0 mà không ghi vuông góc, hay khoảng cách mà khẳng định vuông góc.
18. **VF.** Không lộ trên trang: 43/43 lượt có `answer_text_on_page` rỗng. **INF:** envelope vẫn mang giá trị cuối theo thiết kế (`FINAL_RESULT`, `answers`); giao diện học sinh ẩn chúng (`tapKetQuaCuoi`).
19. **VF.** Không. O nằm trong bài catalog `chop-thiet-dien-ba-diem` và được gắn cờ `UNUSED_REDUNDANT` từ `9d5e9b408`. Bản coplanar mà thư viện đã tích hợp không có O.
20. **INF.** Có, theo bảng giá trị tương đương mà owner đã kiểm (`S_td`, `V_chop`, các cạnh). Run này không tái sinh catalog nâng cao (BL, xem câu 33).
21. **VF.** Có, ở dạng dữ liệu kèm lời giải thích (`auxiliary_points`, ví dụ I = NP ∩ AB, J = NP ∩ AD); không thêm vật nào vào cảnh. Vẽ chúng là việc bàn giao cho frontend (FE-4).
22. **VF.** Có. Mỗi điểm phụ là giao chính xác trên ℚ của hai đường đồng phẳng và nằm trên mặt cắt. Bộ kiểm độc lập trong `test_section_edge_justification.py::trace_holds` kiểm lại từ toạ độ của cảnh.
23. **VF.** Có. Ví dụ ngũ giác: "Trong mặt (ABCD), gọi J là giao điểm của NP và đường thẳng AD; trong mặt (SDA), MJ cắt cạnh SD tại giao điểm thuộc cạnh SD." Cạnh thiết diện không có lý do trên Route D giảm từ 18 xuống 2.
24. **VF.** Không: 0 cảnh đổi đỉnh thiết diện hay toạ độ điểm.
25. **VF.** Không.
26. **VF.**
    - Gắn cờ trên Route D: 3 trước (đều sai), 0 sau.
    - Mồ côi thật: 0.
    - Catalog: O được gắn cờ đúng.
27. **VF.** Có. N được đề nêu ("Gọi M, N …") và giao tuyến được đề hỏi, nên cả hai là `SOURCE_REQUIRED`. Đối chứng dương: gỡ các lời gọi đề nêu thì N bị gắn cờ lại.
28. **VF.**
    - (SAC) ⊥ (ABC), (SBC) ⊥ (SAB): `plane_plane`, hai tia ⊥ giao tuyến.
    - SA ⊥ BC (chéo nhau): `line_line_skew`, có đường song song phụ.
    - Đường ⊥ mặt và hai đường cắt nhau vuông góc: dùng dấu vuông sẵn có, nhưng giao diện học sinh **ẩn** dấu này khi góc vuông chính là đáp số (`laDapSoAn`).
29. **VF.** Có. Theo Gram của cảnh: hai tia vuông góc với nhau, và với hai mặt phẳng thì cả hai tia vuông góc giao tuyến.
30. **VF.** Có. Các chứng chỉ `/2` không đổi. Với mục tiêu 90° không có tam giác nhân chứng, adapter kiểm *loại* góc vuông được vẽ (`_RIGHT_ANGLE_DRAWING`); có tiêm lỗi chứng minh ràng buộc này.
31. **VF.** 12/12 đột biến: 9 cấu trúc do bộ kiểm độc lập bắt, 3 hình học hoặc chứng minh do adapter bắt.
32. **VF.** Không có đột biến nào lọt.
33. **VF.** `geometry-samples.json`: có, chạy lại cho đúng từng byte. **BL:** catalog nâng cao (BLOCKED_OWNERSHIP, generator ở nhánh thư viện).
34. **VF.** Có: hai fixture Scene3D của frontend. Phiên frontend đã sửa ở thư viện; run này không sửa thủ công fixture nào.
35. **VF.** Không đổi phiên bản hợp đồng. Chỉ thêm trường: `trace_derivation`, định lý `COPLANAR_TRACE_INTERSECTION`, và `angle_construction` cho góc 90°.
36. **VF.** Có, 137 → 138: envelope phục vụ đổi và adapter siết chặt hơn trong khi khoá Route D không đổi. Phần lý do theo phương pháp giao tuyến được thêm sau commit 138 nhưng trước mọi lần đóng băng hay đo, nên không có hàng 138 nào từng được phục vụ từ một candidate.
37. **VF.** Không: hàng `137:route-d` trượt cache. Đối chứng: cùng hàng đó dưới policy hiện hành được phát lại nguyên văn (`test_cache_causal_pedagogical_invalidation.py`).
38. **VF.** 43/43. Ghi chú: hai lần chạy đầu (giữ ở `logs/e2e-*`) là lỗi của harness, không phải của sản phẩm:
    - harness đọc sai chỗ hiển thị "Vì sao" (đúng là "Xem giải thích" trong danh sách bước);
    - harness đòi thấy dấu vuông mà chính sách không lộ đáp số cố ý ẩn.
39. **VF.** 1920×1080, 1366×768, 768×1024 và 390×844.
40. **VF.** Không: test proof và soundness đều xanh, chứng chỉ không đổi.
41. **VF.** Không: văn bản 12/27 (9 khớp số), ảnh 7/27 (4 khớp số).
42. **VF.** Không: `wrong_scene_served` rỗng.
43. **VF.**
    - Đề được phục vụ: 61,64 → 60,49 ms trung vị.
    - Đề bị từ chối: 2,03 → 1,95 ms.
    - Thiết diện: 31,62 → 31,59 ms (chênh tối đa 1,4 ms).
    - Tìm chứng minh: ≤ 0,13 ms.
44. **VF.** Không có rò rỉ được chứng minh: heap tăng 3,19 MB qua 12 lần phân tích có lưu lịch sử, số canvas không đổi. `MEMORY_LEAK = INCONCLUSIVE`.
45. **VF.** 14 610 passed, 7 skipped, 17 xfailed, 0 lỗi. Demo replay, crash audit, docs IA và `freeze_verify` đều PASS.
46. **VF.** 141 file, 2 057 test PASS, build PASS (wave tier của regression chuẩn). Riêng vitest miền geometry chạy sau khi tái sinh catalog: 1 291 PASS.
47. **VF.** Không bị truy cập: 0 dòng H-1 bị mở, 0 dòng W2/W3 bị đọc.
48. **VF.** Không.
49. **VF.** 97 finding, tất cả `pending_exception` (BLOCKED_PENDING_OWNER_REVIEW).
50. **VF.** `9d0949b09..HEAD`: 159 blob, 0 vi phạm ⇒ PASS. Governance vẫn BLOCKED.
51. **VF.** `4ddec5666` (trường commit `634565203`).
52. **VF.** Không.
53. **INF.** Giới hạn Scene3D còn lại:
    - Mặt cắt cần mặt phẳng phụ chéo (ví dụ "chứa BD và song song với SC" cần (SAC)): 2 cạnh chưa có lý do; hệ không khẳng định gì cho chúng.
    - Điểm phụ của phương pháp giao tuyến chưa được vẽ.
    - Dấu vuông của góc vuông là đáp số bị ẩn ở chế độ học sinh; **HYP:** cần quyết định sư phạm cho trường hợp này.
    - Catalog nâng cao chưa được tái sinh.
    - Trình duyệt chạy headless, chưa có học sinh thật.
54. **VF.** Bàn giao cho frontend owner (`frontend_handoff_status.json`):
    - FE-2: archetype `multi_layer_aux_pyramid` thiếu `readout_ids` ở 9 bước.
    - FE-3: tái sinh catalog nâng cao sau khi merge (mặt cầu `cau` đang có R là tiên quyết trực quan).
    - FE-4: vẽ `auxiliary_points`.
    - FE-6: hai fixture trên nhánh này đã cũ; khi merge, lấy bản của thư viện.
55. **INF.** Bước có giá trị nhất: mở rộng phương pháp giao tuyến sang mặt phẳng phụ qua đỉnh khối (mặt chéo như (SAC), (SBD)), có bộ kiểm độc lập. Đi cùng là việc frontend vẽ điểm và đường phụ đã có trong dữ liệu. Với REAL27, bộ đọc đề cục bộ vẫn là nút thắt chính.

## 3. Kỳ vọng cũ bị thay

Test cũ không bị xoá.

- `test_section_edge_justification.py::test_justifications_are_emitted_where_the_theorem_applies_and_only_there`: điều kiện cũ "chỉ 1 cạnh có lý do" với mặt cắt vuông góc được viết lại thành "đúng 1 lý do *song song*". Các cạnh còn lại nay mang lý do theo phương pháp giao tuyến và được kiểm lại độc lập.
- Fixture hybrid-preview được thay hai lần trong run này:
  - lần 1: `served-intersection-SAB-SCD` bỏ cờ thừa trên giao tuyến đề hỏi;
  - lần 2: `served-section-MAB-trapezoid` thêm lý do theo phương pháp giao tuyến.

  Không có đường dẫn nào về đáp số, toạ độ hay trạng thái bị đổi. Các bundle cũ giữ nguyên.
- E2E: kỳ vọng "dấu vuông phải hiện" cho SA ⊥ (ABC) được đổi thành "dấu bị ẩn và trang không lộ đáp số", theo chính sách sản phẩm đã ghi trong code. Lần chạy theo kỳ vọng cũ được giữ trong `logs/e2e-first-attempt`.

## 4. Cổng nghiệm thu

| Cổng | Kết quả |
|---|---|
| A quyền sở hữu | PASS |
| B thứ tự ra đời | PASS |
| C tách toán ẩn | PASS |
| D MEASURE | PASS |
| E vết Euclid | PASS (2 cạnh chưa có lý do, không khẳng định) |
| F góc vuông | PASS (có ẩn theo chính sách không lộ đáp số) |
| G nhân quả toàn cục | PASS |
| H hợp đồng liên tầng | PASS (bàn giao FE-2/3/4) |
| I cache | PASS (138) |
| J toán học | PASS |
| K E2E | PASS (43/43) |
| L regression | PASS (cổng sản phẩm) |
| M đánh giá | PASS (không dùng holdout; tổng quát hoá NOT_MEASURED) |
| N publication | BLOCKED, không tự duyệt |
