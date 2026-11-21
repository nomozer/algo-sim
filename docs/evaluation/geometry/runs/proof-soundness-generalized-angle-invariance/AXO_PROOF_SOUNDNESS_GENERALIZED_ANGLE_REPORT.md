# AXO: tính đúng đắn của chứng chỉ chứng minh và bất biến góc tổng quát

Run `proof-soundness-generalized-angle-invariance` · 2026-11-14 · nhánh `feat/local-first-geometry-understanding`
· bắt đầu ở `914dd41db` · `CACHE_VERSION` 136 → **137** · 0 lượt gọi AI live · không merge, push hay deploy.

Ký hiệu nhãn: **VF** = VERIFIED FACT, **INF** = INFERENCE, **HYP** = HYPOTHESIS, **NM** = NOT_MEASURED, **BL** = BLOCKED.

| Mốc | Commit |
|---|---|
| Sửa sản phẩm | `c54db0da0` (chứng chỉ `/2`, ràng buộc mục tiêu, giá trị và cảnh, ba họ góc mới, cache 137) |
| Kỳ vọng cũ được viết lại | `79fae066b` |
| Bundle fixture thay thế | `421d7a7f8` (do commit `9d5e9b408` của owner) |
| Candidate đóng băng | `f30363597`, trường commit `5481d5ddc`, hệ đo `610b4ee1…`, 117 file, cây sạch |
| Test cấu hình suy biến | `94281be58` (chỉ thêm test, sau đóng băng) |

## 1. Kết luận chính

- **Lỗi r520 đã được tái hiện và sửa (VF).**
  - `/1` viết góc phẳng thành bộ ba trần `["B","S","A"]`, với đỉnh đứng **đầu**. Đọc theo ký hiệu chuẩn thì đó là ∠BSA (đỉnh S), trong khi câu tuyên bố nói ∠(SBA).
  - Verifier cũ chấp nhận ba chứng chỉ sai (`logs/old_verifier_probe.json`, chạy trên mã của `914dd41db`):
    - chứng chỉ bị trỏ sang mục tiêu khác;
    - tam giác cố định hình dạng được liệt kê theo thứ tự khác;
    - bộ ba ở dạng được sinh ra.
  - Giá trị phục vụ (45°) vẫn đúng **chỉ vì** tam giác SAB vuông cân, nên ∠SBA = ∠BSA.
- **Phản ví dụ phân biệt hai cách đọc (VF).** Với SA = 2AB, góc tại B có cos² = 1/5 (đúng là góc phẳng, không phụ thuộc BC), còn góc tại S có cos² = 4/5. Hệ nay phục vụ 1/5. Một chứng chỉ trỏ sang đỉnh S, dù nhất quán nội bộ, bị từ chối.
- **Chứng chỉ `target-invariance-certificate/2` (VF):**
  - nhân chứng góc có cấu trúc `{vertex, ray_1, ray_2, domain}`;
  - bước hình dạng tam giác phải cố định góc **tại đỉnh nhân chứng**;
  - verifier đòi đúng mục tiêu được hỏi và tính lại cos²;
  - engine thêm TI-6: cos² đã chứng minh phải bằng đáp số chính xác của nhân trên hình đại diện;
  - adapter thêm `_invariance_proof_bound`: góc được vẽ phải là góc của nhân chứng (cùng id đỉnh, cùng id hai đầu tia), và `scene_configuration` của envelope phải trùng với của engine.
- **Họ góc mới, mỗi họ đều có chứng chỉ và verifier độc lập (VF):**
  - hai mặt phẳng vuông góc (`PERP_PLANES`);
  - góc đường–mặt (`LINE_PLANE_ANGLE`, `LINE_PERP_PLANE_ANGLE`);
  - góc đường–đường (`LINE_ANGLE`, `LINES_PERPENDICULAR`). Hai đường chéo nhau chỉ được phục vụ khi đã chứng minh vuông góc.
  - Tỉ số hai cạnh góc vuông đọc từ `equal_length` / `segment_ratio`.
- **Kết quả đo (VF):**
  - corpus phát triển: 38 → 49 ca được phục vụ, 0 ca từ phục vụ chuyển sang từ chối, 0 đáp số đổi;
  - REAL27 văn bản 12 → 12, ảnh 7 → 7;
  - 15/15 biến thể (mutation) theo luật bị bắt, đủ 12 luật;
  - 15/15 ca góc khớp phép tính lại từ toạ độ cảnh và Gram;
  - E2E 33/33;
  - backend 14 576 PASS, frontend 2 057 PASS kèm build.
- **Phát hành bị chặn (VF):**
  - publication HEAD BLOCKED: 97 finding chờ ngoại lệ của owner;
  - FULL_RELEASE_GATE BLOCKED.

## 2. Trả lời 50 câu hỏi

1. **VF.** Có, toàn vẹn lúc bắt đầu: HEAD `914dd41db`, candidate `ade820bd3` (`2a18f935…`, 117 file), cache 136.
   - Trong lúc run chạy có commit `9d5e9b408` của owner (thêm dòng dõi dựng hình vào `backend/app`). Commit này làm `--verify` đỏ cho đến khi đóng băng lại.
   - Để chỉ đo thay đổi của run này, phía "before" của mọi phép so sánh là `9d5e9b408` (`baseline_candidate_integrity.json`).
2. **VF.** Có. Trên mã của `914dd41db`, bước `PLANE_ANGLE` sinh ra `equals_angle: ["B","S","A"]`. Verifier cũ chấp nhận chính bộ ba đó, chấp nhận chứng chỉ trỏ sang `goal_id` khác và chấp nhận tam giác liệt kê với S đứng đầu (`r520_angle_witness_defect_reproduction.json`).
3. **VF.** Thứ tự trong mã là `[X, U, V]` với X là đỉnh. Ký hiệu chuẩn lại đặt đỉnh ở giữa, nên `["B","S","A"]` đọc thành ∠BSA, tức đỉnh S. Không có trường nào nói rõ đâu là đỉnh (`plane_angle_root_cause_analysis.json`).
4. **VF.** Verifier cũ thiếu bốn ràng buộc:
   - với mục tiêu được hỏi (không nhìn thấy các mặt phẳng được hỏi);
   - giữa bước hình dạng tam giác và đỉnh của góc;
   - giữa giá trị đã chứng minh và đáp số của nhân;
   - giữa góc đã chứng minh và góc được vẽ.
5. **VF.** Có.
   - Phép thăm dò trên mã cũ cho 3 chứng chỉ sai được chấp nhận.
   - Các test mới đỏ trên lớp `/1` và xanh sau sửa: `test_the_r520_vertex_first_triple_certificate_is_not_accepted`, `test_a_shape_fixed_at_another_vertex_is_rejected_even_when_the_figure_makes_it_equal`, `test_a_certificate_is_bound_to_the_goal_it_was_proven_for`.
   - Riêng ràng buộc cảnh có phép tiêm lỗi: tắt `_invariance_proof_bound` thì cả 6 phép giả mạo đều được phục vụ.
6. **VF.** Có: `witness.vertex` (r520: đỉnh B).
7. **VF.** Có. Verifier kiểm:
   - hai tia xuất phát từ đỉnh;
   - hai đầu tia khác nhau;
   - mỗi tia nằm trong mặt phẳng của nó và ngoài giao tuyến;
   - mỗi tia đã được chứng minh vuông góc với giao tuyến bằng một bước trước đó.
8. **VF.** Có: `intersection_line` phải đúng bằng P ∩ Q và đỉnh phải nằm trên đó (r520: BC).
9. **VF.** Có: miền `UNORIENTED_LINE_ANGLE_0_90`; góc nhị diện có hướng nằm ngoài phạm vi. **NM:** cụm từ "góc nhị diện" chưa được đo trong run này.
10. **VF.** Không. Đỉnh, tia và giao tuyến được kiểm về cấu trúc. cos² được dùng sau đó để ràng buộc giá trị, vì cos² trùng nhau cho một góc và góc bù của nó.
11. **VF.** Có: cả 7 luật cũ, cộng 6 luật mục tiêu mới, đều có biến thể bị bắt (`existing_rule_soundness_audit.json`, 15/15).
12. **VF.** Có, ngoài lỗi về đỉnh còn bốn lỗi:
    - không ràng buộc mục tiêu;
    - bước hình dạng không gắn với đỉnh;
    - không ràng buộc giá trị với nhân;
    - không ràng buộc góc vẽ với chứng chỉ.

    Ngoài chứng chỉ:
    - `9d5e9b408` đổi envelope phục vụ mà không cập nhật bundle fixture và không bump cache;
    - một lỗi đo của chính tôi: lượt ảnh đầu tiên chạy thiếu cấu hình OCR cục bộ, cho 0/27. Kết quả đó được giữ ở `logs/invalid-image-acceptance-ocr-not-configured.json` và **không** được tính.
13. **VF.** Cách sửa từng lỗi:
    - nhân chứng có cấu trúc;
    - `goal_id` và các toán hạng phải trùng với lời gọi `ask_angle_*`;
    - `TRIANGLE_SHAPE_FIXED.angle_at` phải là đỉnh nhân chứng, và phải có đúng một bước hình dạng;
    - kiểm TI-6 trong engine;
    - kiểm `_invariance_proof_bound` trong adapter;
    - bundle fixture mới;
    - cache 137;
    - đo lại ảnh với `LOCAL_OCR_PYTHON` / `LOCAL_OCR_TESSDATA`.
14. **VF.** Có. Verifier dẫn lại từng bước từ các lời gọi và các bước trước đó, không bao giờ gọi bộ tìm (test AST `test_the_verifier_never_calls_the_search`). Nó chỉ dùng chung với bộ tìm `_ln`, `_args`, `_Domain` và `_ratio_sq`.
15. **VF.** Không có chứng chỉ sai nào được chấp nhận trong các biến thể đã thử.
    - **INF:** `_Domain` dùng chung, nên một lỗi trong cách định nghĩa miền (chóp đáy lồi) sẽ ảnh hưởng cả hai phía.
    - Tính lồi của đáy được giả định chứ không kiểm.
16. **VF.** Có. Ví dụ (SAC) ⊥ (ABC) vì SA ⊂ (SAC) và SA ⊥ (ABC); cũng phục vụ (SBC) ⊥ (SAB).
17. **VF.** Có, các ca SB/(ABC):
    - với SA = AB: cos² 1/2;
    - với SA = 2AB: cos² 1/5;
    - bản đổi tên T.XYZ cho cùng kết quả;
    - SA/(ABC) cho 90°.
18. **VF.** Có:
    - SB và SA: cos² 1/2;
    - SB và BC: 90°.
19. **VF.** Một phần. SA và BC chéo nhau và được phục vụ 90° vì SA ⊥ BC đã được chứng minh. SC và AB chéo nhau, không vuông góc, và bị từ chối: chưa có luật tịnh tiến song song. cos² của cặp này đổi giữa 1/3 và 1/11 khi BC đổi.
20. **VF.** Có, 9 test không sinh chứng minh hoặc bị từ chối:
    - mặt phẳng lặp lại;
    - mặt phẳng hai nhãn;
    - bốn nhãn không đồng phẳng;
    - nhãn lặp;
    - một đường thẳng lặp lại;
    - đường nằm trong mặt;
    - nhãn không thuộc khối;
    - tia lặp;
    - điểm dẫn xuất M nằm ngoài miền chứng minh.

    Lăng trụ nằm ngoài miền và bị từ chối.
21. **VF.** Không. Có 4 phản ví dụ (`generalized_angle_counterexamples.json`), giá trị cos² đổi trên hai hình cùng thoả đề, và cả 4 đều bị từ chối:
    - SC và AB: 1/3 / 1/11;
    - SC và (SAB): 2/3 / 2/11;
    - SC và (ABC): 2/3 / 10/11;
    - SB và (ABC) khi không có tỉ số: 1/2 / 1/10.
22. **VF.** Không. Chứng minh là tổng hợp trên nhãn. Các nhân chứng số (TI-5) chỉ là phép thử hồi quy, còn TI-6 là ràng buộc giá trị.
23. **VF.** Số biến thể bị bắt:
    - 15/15 biến thể theo luật;
    - 3 biến thể cấu trúc;
    - 4 biến thể nhân chứng hoặc mục tiêu;
    - 1 phép tiêm lỗi TI-6;
    - 6/6 phép giả mạo cảnh;
    - 46/46 biến thể cảnh của bộ kiểm cũ.
24. **VF.** Không có biến thể nào lọt.
    - Ghi chú: ở lần viết đầu, 7 phép giả mạo cảnh bị các kiểm tra khác bắt, chứ không phải ràng buộc mới. Tôi viết lại chúng thành giả mạo nhất quán, rồi tiêm lỗi để xác nhận chính ràng buộc mới bắt chúng.
25. **VF.** Không: `registry.py` không đổi trong run này.
26. **VF.** Không. Tỉ số đọc từ lời gọi đã qua Source Gate, và chứng chỉ không tạo lời gọi nào.
27. **VF.** Có. r520 có nhân chứng đỉnh B, tia {S, A}; cảnh vẽ `vertex_id` B, hai tay `S`, `A`.
28. **VF.** Không, trên các ca được đo. Với góc 90°, cảnh không vẽ góc. Các ca này được kiểm bằng cách tính lại từ toạ độ và Gram (`generalized_angle_scene_checks.json`, 15/15).
29. **VF.** Không. Hàng `136:route-d` mang chứng chỉ `/1` bị trượt cache và được tính lại thành `/2` (`test_cache_proof_soundness_invalidation.py`). Phép đối chứng: cùng hàng đó dưới policy hiện hành được phát lại nguyên văn, đó là lý do phải bump.
30. **VF.** Có, 136 → 137: guard siết chặt hơn và envelope đổi trong khi khoá Route D không đổi. Bump này cũng phủ thay đổi envelope của `9d5e9b408`.
31. **VF.** 12 → 12/27.
32. **VF.** 7 → 7/27.
33. **VF.** REAL27: văn bản 12, ảnh 7 ở mức `GOAL_CONSTRUCTION_VERIFIED`. Corpus phát triển: 49 ca được phục vụ, 102 phép kiểm độc lập không lỗi.
34. **VF.** Văn bản 9/27, ảnh 4/27 khớp đáp án của bộ dữ liệu. Có 3 + 3 ca chỉ hiển thị mục tiêu, chưa trả lời giá trị số.
35. **VF.** Không: `wrong_scene_served` rỗng ở cả văn bản lẫn ảnh, 0 bất biến bị phá.
36. **VF.** 33/33 trên 4 khung nhìn (1920, 1366, 768, 390).
    - Có 6 ca mới.
    - Hai ca 90° có `construction_only_at_conclusion = null` vì cảnh không vẽ góc.
37. **VF.**
    - Tìm chứng minh tốn ≤ 0,181 ms, kiểm ≤ 0,118 ms, tối đa 8 bước, chưa lần nào vượt ngân sách (256).
    - So cùng tập ca: ca đã phục vụ 36,53 → 36,93 ms, ca bị từ chối 3,20 → 3,18 ms.
    - 11 ca mới được phục vụ có trung vị 136 ms (tối đa 184 ms). Phần lớn thời gian là dựng hình đại diện và 4 nhân chứng, không phải chứng minh.
38. **VF.** Không có rò rỉ được chứng minh: heap tăng 2,24 MB qua 12 lần phân tích có lưu lịch sử, 1,44 MB qua 15 lần duyệt timeline, số canvas không đổi. **INF:** chưa đủ để kết luận có rò rỉ.
39. **VF.** Không: 0 dòng H-1 bị mở, 0 dòng W2/W3 bị đọc.
40. **BL.** Không có nguồn mới. `NEW_INDEPENDENT_EVALUATION = BLOCKED_DATA`.
41. **VF.** 14 576 passed, 7 skipped, 17 xfailed, 0 lỗi. Demo replay, crash audit, docs IA và `freeze_verify` đều PASS.
42. **VF.** 141 file, 2 057 test PASS, build PASS.
43. **VF.** 97 finding, đều chờ ngoại lệ (`BLOCKED_PENDING_OWNER_REVIEW`).
44. **VF.** `914dd41db..HEAD` lúc quét: 112 blob, 0 vi phạm ⇒ PASS. Governance vẫn BLOCKED.
45. **VF.** `f30363597` (trường commit `5481d5ddc`).
46. **VF.** Không có merge, push hay deploy; 0 lượt gọi AI live.
47. **INF.** Các luật toán học còn thiếu:
    - tịnh tiến song song cho hai đường chéo nhau không vuông góc;
    - góc tại điểm dẫn xuất (trung điểm, chân đường cao);
    - lăng trụ, hình hộp và khối nhiều hơn một chóp;
    - tỉ số suy ra (Pythagore, tam giác đồng dạng);
    - tam giác cân hoặc đều không có `regular_polygon`;
    - góc có hướng hoặc góc nhị diện.
48. **INF.** Hai giới hạn lớn nhất của verifier:
    - Nó tin miền: chóp đáy lồi, không ba đỉnh thẳng hàng. Miền này được khai báo chứ không kiểm trên toạ độ.
    - Nó dùng chung `_Domain` / `_ratio_sq` với bộ tìm.

    Ngoài ra nó chỉ biết các nhãn đỉnh, không biết điểm dẫn xuất.
49. **INF.** Đủ để demo nội bộ trong phạm vi sau:
    - offline, cục bộ;
    - chóp có cạnh bên vuông góc đáy, tam giác vuông, có tỉ số cạnh;
    - các họ góc kể trên;
    - hình minh hoạ được ghi rõ là "không duy nhất".

    Không đủ để pilot với học sinh hay để tuyên bố tổng quát hoá: dữ liệu độc lập chưa có, H-1 chưa đo, publication bị chặn.
50. **VF + INF.**
    - **VF:** không ca REAL27 nào còn bị từ chối vì thiếu chứng minh. Có 15 ca bị từ chối, theo các nguyên nhân sau (`semantic_development_before_after.json`):
      - `UNRECOGNIZED_GOAL`: 3;
      - `SOURCE_PROVENANCE_MISSING`: 3;
      - `UNRECOGNIZED_GEOMETRIC_ENTITY`: 3;
      - `INCOMPLETE_FACT_EXTRACTION`: 2;
      - 4 nguyên nhân khác, mỗi nguyên nhân 1 ca.
    - **INF:** vì vậy, với REAL27, bước có giá trị nhất là bộ đọc đề cục bộ: nhận dạng mục tiêu, thực thể và trích dẫn nguồn.
    - **INF:** với module chứng minh, bước tiếp theo là mở rộng miền sang điểm dẫn xuất (trung điểm, chân đường cao) có verifier độc lập, rồi đến luật tịnh tiến song song cho hai đường chéo nhau.

## 3. Kỳ vọng cũ bị thay

Test cũ không bị xoá; mỗi thay đổi được ghi trong commit `79fae066b` và `historical_certificate_compatibility.json`.

- `test_the_proof_is_the_synthetic_one`: điều kiện cũ `equals_angle ⊇ {S, A, B}` (bộ ba trần) được thay bằng nhân chứng có đỉnh B và tia {S, A}.
- `test_unproven_or_varying_goals_are_refused`: "(SAC) và (ABC)" trước bị từ chối với ghi chú "invariant but unproven". Nay ca này được chứng minh 90° bằng `PERP_PLANES`; xem `test_perpendicular_planes_are_now_proven`.
- Corpus phát triển: 11 ca chuyển từ REFUSE sang SERVE nhờ năng lực mới, đều nằm trong các họ góc đã liệt kê ở mục 1.
- Bundle fixture `fixtures-dihedral-altitude` được thay bằng `fixtures-lineage-proof-soundness`.
  - Nguyên nhân là `9d5e9b408`: 12/41 fixture đổi.
  - Không có đường dẫn nào về đáp số, toạ độ, trạng thái hay lý do từ chối bị đổi (`logs/fixture_bundle_supersession.json`).
  - Bundle cũ giữ nguyên.
- Các biên nhận của run `target-invariant-regular-solid-semantics` không đổi (0 file đổi băm). Ba file trong đó nay được run này thay thế về nội dung:
  - `universal_goal_invariance_proofs.json`;
  - `goal_invariance_mutation_tests.json`;
  - `target_invariance_capability_audit.json`.

## 4. Cổng nghiệm thu

| Cổng | Kết quả |
|---|---|
| A tái hiện lỗi | PASS |
| B góc có cấu trúc | PASS |
| C verifier độc lập | PASS |
| D bảy luật cũ | PASS (15/15) |
| E mặt phẳng vuông góc | PASS |
| F góc đường–mặt | PASS |
| G góc đường–đường | PASS (đường chéo nhau chỉ khi vuông góc) |
| H Source Gate | PASS (không đổi) |
| I an toàn cache | PASS (137) |
| J Scene3D | PASS (ràng buộc chứng chỉ ↔ cảnh, kiểm Gram 15/15) |
| K đánh giá | PASS (không dùng holdout; tổng quát hoá NOT_MEASURED) |
| L regression | PASS (cổng sản phẩm) |
| M publication | BLOCKED, không tự duyệt |

## 5. Giới hạn

- Corpus do agent viết, cộng các ca REAL27 đã lộ; không có dữ liệu chưa thấy.
- Trình duyệt chạy headless.
- Chưa có học sinh và chưa đo H-1.
- Máy đo là máy dev dùng chung.
- Cổng 8000 có một tiến trình đã chạy từ trước run; run không khởi động nó và không đụng vào nó.
