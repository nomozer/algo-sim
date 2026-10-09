# unnamed-regular-pyramid-grounding — kế hoạch và tiền đăng ký

Việc: `ISSUE-ARCH-C0-WHOLE-SOLID-CLAIMS-NOT-READ` (phần còn lại: chóp đều không tên) và
`ISSUE-ARCH-UNNAMED-REGULAR-PYRAMID-OUTSIDE-REFUSAL-ZONE`. Cloud, nhánh `fix/unnamed-regular-pyramid-grounding` từ
`origin/main` = `ede8d329` (khớp). Candidate `c3f83399…`, `CACHE_VERSION` 121, `LLM_ONLY`, compiler opt-in, frontend
đóng băng, 0 lượt gọi model.

## 1. Điều tra (`ede8d329`; `diagnostics/probe_c1_variants_ede8d329.log` trùng byte log candidate của run trước)

47 đề chóp đều không tên (biến thể `unnamed_everywhere` của hai corpus): 37 phục vụ — 22 đúng nhãn, 4 sai giá trị, 11
nhãn đòi từ chối; 10 không phục vụ. Trả lời các câu hỏi của brief:

1. **Bộ đọc nhận tính chất đều nhưng không gắn?** Không nhận gì: `_khoi_cua_du_kien` coi khối là khối không tên duy nhất
   (`((), (), m)`) nhưng `doc_rang_buoc` chỉ phát `regular_*_pyramid` từ ký hiệu khối; "đều" thành chữ chưa đọc
   (`phan_chua_doc`). Khung `()` đã có sẵn cho lăng trụ đứng không tên và cho số đo (`height ()`, `base_square ()`).
2. **RequestContract đủ để xác định khối?** `solid_topology` của hợp đồng là đầu ra mô hình (analyze), không phải đề —
   không dùng làm căn cứ gắn. Đề tự nó: đúng một danh từ khối ⇒ khối của đề là DUY NHẤT; nhưng đề không gọi tên đỉnh.
3. **C1 gắn khối thế nào?** `_nhan_khuon`: ký hiệu khối có tên ⇒ thực thể của đề; không tên ⇒ chỉ lăng trụ đứng + đáy
   vuông, gắn vào khối DUY NHẤT của chương trình qua bảng mặt (`phan_loai_bang_mat`) và CHỈ nhận cách đọc thoả mọi ràng
   buộc khuôn trên giá trị chương trình — kiểm, không tin. Chóp không tên: không có nhánh ⇒ `TEMPLATE_NOT_MATCHED`.
4. **Vì sao ca sai vẫn được phục vụ?** Đề không ký hiệu khối nằm NGOÀI vùng từ chối U3 (`neu_khoi_da_dien`): cổng tính
   nhưng không chặn ⇒ phục vụ mọi chương trình (thiếu chiều cao ⇒ 16; khung affine không có metric dẫn xuất ⇒ 5 thay 3√3).
5. **Vì sao nới vùng làm hỏng ca đúng?** Trong vùng, chóp không tên không khớp khuôn nào ⇒ 22 ca đúng cũng bị từ chối.
6. **Kiểm chứng được bằng kernel/ràng buộc nguồn?** Có, khi việc đặt tên đỉnh KHÔNG mang nghĩa đề chưa cố định: đề không
   gọi tên điểm nào (hoặc mọi điểm có toạ độ trong đề) ⇒ gắn vào khối duy nhất của chương trình rồi KIỂM như ký hiệu
   chuẩn (khuôn T7/T8 trên giá trị chương trình, metric T8 dẫn xuất từ đề, §22 trên toạ độ). Đề gọi tên điểm mà không
   toạ độ (`AB = 4, SA = 3`, `cạnh bên SA`): đề không nói điểm nào là đỉnh — vd `AB = 4, SA = 3` nhất quán cả với đỉnh S
   (V = 16/3) lẫn đỉnh B (cạnh bên 4, cạnh đáy 3 ⇒ V khác) ⇒ chỉ cách đặt tên của chương trình quyết định = tự xác nhận
   bằng đầu ra LLM ⇒ KHÔNG gắn, giữ nguyên (21 hàng, scope `unchanged`).

## 2. Sửa (đăng ký trước)

1. Bộ đọc: khối không tên duy nhất là `hình/khối chóp tứ|tam giác đều` (không ngay sau "không phải (là)") ⇒ phát
   `regular_square_pyramid ()` + `base_square ()` (hoặc tam giác + `base_equilateral ()`); khối số đo sẵn có
   (`cạnh đáy/cạnh bên/trung đoạn/tâm đáy/tất cả các cạnh`) tự gắn `()` như hiện nay.
2. Một thẩm quyền "đặt tên đỉnh không mang nghĩa": `ten_diem_khong_toa_do(đề)` (điểm đề gọi tên mà không cho toạ độ).
3. Vùng U3: thêm khẳng định chóp đều `()` khi tập trên rỗng.
4. Cổng: khi tập trên rỗng và chương trình dựng ĐÚNG một khối, gắn mọi ràng buộc `()` vào từng cách đọc chóp (bảng mặt)
   có số đỉnh đáy khớp; C1 và metric T8 dùng cách đọc đầu tiên (kiểm bởi khuôn); C0: mâu thuẫn khi KHÔNG cách đọc nào
   thoả (§22). Không gắn ⇒ như cũ. `formation` chịu được `()`.
Không đổi: compiler, khuôn, mã từ chối, pipeline mặc định, frontend.

## 3. Tiêu chí

- `labels.json`: 47 hàng C1 (lớp, phạm vi, nhãn; scope `bind` ⇒ kỳ vọng = nhãn corpus, oracle dẫn xuất lại từ kích
  thước đề; scope `unchanged` ⇒ = baseline) + 11 hàng C0; `oracle.py` độc lập (OK).
- Mục tiêu trên scope `bind` (26): 13 đúng giữ đúng giá trị; 4 sai ⇒ đúng giá trị hoặc từ chối đúng lý do; 8 nhãn từ
  chối ⇒ từ chối; 1 từ chối giữ từ chối. Scope `unchanged` (21) không đổi. Không ca mới phục vụ sai.
- Bảo vệ: C0 §21–§23 (nhãn ba run trước), C1 hai corpus (chuẩn + hai lối viết), G04, G05, compiler, danh tính, demo,
  bề mặt sập; toàn bộ pytest so baseline sạch. Kỳ vọng thay đổi có chủ đích: test của run trước khoá "không phát khẳng
  định cho chóp đều không tên" (`test_c0_whole_solid_reader::test_chop_deu_khong_ten_khong_gan_vao_khoi_nao`) — giới hạn
  được run này gỡ; nhãn `baseline` của run ấy giữ nguyên byte.
- Cache: quyết bằng probe trước/sau.
