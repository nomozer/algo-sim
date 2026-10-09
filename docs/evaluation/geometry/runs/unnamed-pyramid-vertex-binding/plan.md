# unnamed-pyramid-vertex-binding — kế hoạch, tiền đăng ký và kết luận khả thi

Việc: phương án (b) cho 21 đề chóp đều không tên gọi tên điểm mà không cho toạ độ
(`ISSUE-ARCH-UNNAMED-REGULAR-PYRAMID-OUTSIDE-REFUSAL-ZONE`, phần còn lại sau unnamed-regular-pyramid-grounding). Cloud,
nhánh `fix/unnamed-pyramid-vertex-binding` từ `origin/main` = `a7c56942` (khớp). Candidate `d07a92de…`, `CACHE_VERSION`
122, `LLM_ONLY`, compiler opt-in, frontend đóng băng, 0 lượt gọi model. **Không sửa mã sản phẩm** (§3).

## 1. Baseline (`diagnostics/probe_c1_variants_a7c56942.log`, trùng byte log candidate của run trước)

21 hàng: 9 phục vụ đúng nhãn/quy ước, 9 từ chối, 3 phục vụ trái nhãn (`square/N5` SA = 3, `square/R2_N9` 16,
`square/W5_C` 16/3).

## 2. Nhãn độc lập (`labels.json`, `oracle.py` — OK 21/21)

Mỗi hàng: điều đề KHẲNG ĐỊNH (độ dài có tên, chuỗi bằng nhau, "cạnh đáy/chiều cao", vai trò "cạnh bên SA", điểm phụ
O = giao hai đường, G = trọng tâm) viết tay; oracle liệt kê MỌI ánh xạ đơn ánh tên điểm → vị trí của chóp đều
(≤ 120), mỗi ánh xạ là một hệ tuyến tính theo (b², h²) (mọi bình phương khoảng cách trên chóp đều là α·b² + β·h²).

| kết luận theo đề | hàng | kỳ vọng phương án (b) |
|---|---|---|
| xác định (mọi cách hiểu hợp lệ cùng đáp số) | S7 16, S5 √17, R2_S9 16/3, P9 9/2, P11 3; N4, N5, N6 (cùng đề, chương trình lỗi) | phục vụ 5; từ chối 3 (chương trình) |
| mơ hồ thật (hai cách hiểu hợp lệ, đáp số khác) | R2_L1, W5_A, W5_D, W5_E (AB là cạnh đáy hay đường chéo), R2_S10, R2_S8 (đỉnh S hay B), R2_U4, tam giác N4 | từ chối |
| mâu thuẫn nguồn (không cách hiểu nào hợp lệ) | R2_N8, R2_N9, W5_B, tam giác N3 | từ chối |
| thiếu dữ kiện | W5_C (SA = SB = SC = SD không giá trị) | từ chối |

Trong 9 ca đang phục vụ đúng theo quy ước: 5 được chính đề xác định; 4 (R2_L1, W5_A, R2_S10, R2_S8) mơ hồ thật — giữ
phục vụ chúng là dựa vào quy ước đặt tên, không phải đề.

## 3. Khả thi trong giới hạn của brief — KHÔNG

Thử thiết kế chỉ dùng cái đã có: với mỗi ánh xạ, viết lại đề bằng ký hiệu chuẩn rồi để bộ đọc + khuôn T7/T8 của sản
phẩm quyết (`diagnostics/template_per_labelling.py` → `template_per_labelling_a7c56942.log`). Kết quả: khớp oracle 3/21;
cả 5 ca xác định đều ra "mở" (⇒ từ chối), vì khuôn được thiết kế cho MỘT cách đặt tên đã biết và để phần còn lại cho
phép kiểm trên toạ độ chương trình:

- T7 lấy cạnh đáy từ cụm "cạnh đáy" trước, KHÔNG đối chiếu với `SA` khi S, A kề nhau ở đáy (R2_S9: 12 ánh xạ "khớp" mà
  oracle chứng minh mâu thuẫn); không đọc đường chéo (`AB` là đường chéo ⇒ bỏ qua);
- O = giao `AC`, `BD` chỉ được đọc khi đó là hai đường chéo đáy theo ký hiệu; G = trọng tâm mặt bên không có khoảng
  cách nào (P9); vai trò "cạnh bên SA" trong câu hỏi không được đọc (S5, P11);
- khuôn không sinh độ dài đoạn được hỏi.

Đạt oracle cần trong sản phẩm: mô hình tham số của chóp đều (vị trí, dạng tuyến tính theo b², h²), giải hệ hai ẩn,
điểm phụ, đọc vai trò "cạnh bên XY" — tức một mô hình hình học thứ hai + đại số mới, nằm ngoài giới hạn brief ⇒
`ARCHITECTURE_DECISION_REQUIRED`.

## 4. Quyết định của người dùng: phương án A (cuối cùng) — triển khai

Người dùng chọn A: chặn cả 21 đề, chấp nhận không phục vụ 5 đề mà chính đề xác định; B hoãn (nâng cấp năng lực tuỳ
chọn). Nhãn toán học `labels.json` + `oracle.py` GIỮ NGUYÊN; kỳ vọng sản phẩm riêng: `policy_a_labels.json` (21 ×
`refused`; 5 `capability_limit`, 16 `safety`), commit `1bb5c02` trước commit sản phẩm.

Sửa (amendment §25), chỉ lớp vùng từ chối + lý do của cổng:
1. `shape_constraint.neu_khoi_da_dien`: mọi khẳng định chóp đều không tên `()` thuộc vùng U3 (bỏ điều kiện "không tên
   điểm thiếu toạ độ").
2. `assumption_gate._nhan_khuon`: khẳng định ấy không được §24 gắn ⇒ `TEMPLATE_NOT_MATCHED unnamed regular pyramid: its
   vertices are not fixed by the text` ⇒ `ASSUMPTION_INVARIANCE_UNPROVEN` (mã hiện hành, không phải mâu thuẫn toạ độ).
Không đổi: §24 (26 hàng gắn được), ký hiệu chuẩn, hai lối viết, khối gọi tên ở câu hỏi, C0 (đề toạ độ không gắn vẫn qua
C0), compiler, kernel, frontend. Kỳ vọng: 12 served → refused, 9 refused → refused.
