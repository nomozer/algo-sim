# c0-whole-solid-reader — kế hoạch và tiền đăng ký

Việc: `ISSUE-ARCH-C0-WHOLE-SOLID-CLAIMS-NOT-READ`. Cloud, nhánh `fix/c0-whole-solid-reader` từ `origin/main` = `a1350da3`
(khớp, cây sạch). Candidate `8c4c0128…`, `CACHE_VERSION` 120, `LLM_ONLY` mặc định, compiler opt-in, frontend đóng băng,
0 lượt gọi model.

## 1. Phân tích (mã tại `a1350da3`)

- **Hàm đọc khẳng định:** `shape_constraint.doc_rang_buoc` (ký hiệu khối `_KHOI_CHOP` ⇒ `pyramid` + `regular_*_pyramid`
  + `base_*`) và `_khoi_cua_du_kien` (khối DUY NHẤT của phần dữ kiện, để gắn số đo). Biểu diễn đã có: `pyramid`,
  `regular_square_pyramid`, `regular_triangular_pyramid`, `base_square`, `base_equilateral` (checker §22).
- **(1) "hình chóp tứ giác đều có đỉnh S và đáy ABCD":** `_KHOI_CHOP` chỉ nhận ký hiệu `X.Y` ⇒ không phát gì; khối
  được coi là không tên. Đỉnh và đáy được ĐỀ gọi tên tường minh ⇒ gắn duy nhất.
- **(3) "hình chóp đều S.ABCD":** `_KHOI_CHOP` đòi `tam|tứ|… giác` trước `đều` ⇒ không khớp; "chóp đều" với đáy k đỉnh
  là chóp k-giác đều (định nghĩa SGK). Ký hiệu cho đỉnh và đáy ⇒ gắn duy nhất.
- **(2) "hình chóp tứ giác đều" không tên:** dữ kiện không gọi tên đỉnh/đáy. Route chỉ TỪ CHỐI theo cổng giả định trong
  vùng đa diện (`neu_khoi_da_dien`, quyết định U3): chóp không tên nằm ngoài vùng ⇒ kể cả khi C0 phát hiện mâu thuẫn,
  route chỉ ghi trạng thái. Probe C1 (`diagnostics/probe_c1_equivalence_a1350da3.log`, biến thể `unnamed_everywhere`):
  ngoài vùng, MỌI đề chóp đều không tên đều được phục vụ — kể cả đáp số sai (thiếu chiều cao ⇒ 16; chiều cao vô tỉ ⇒
  4/3; …) — và nới vùng sẽ từ chối cả đề đúng (S1 = 16) vì C1 không có phép gắn chóp không tên. ⇒ **Không sửa trong
  phạm vi này** (đổi vùng U3 hoặc mở rộng C1); ghi bằng chứng, giữ hành vi `main` (nhãn `baseline`).
- **Tác động C0/C1 khi bộ đọc phát quan hệ cho (1), (3):** mọi bên tiêu thụ (`formation`, phát hiện T7/T8, `do_luong_cua`,
  `construction_binding`, `display_names`, `neu_khoi_da_dien`, §22) đọc CÙNG các kind ấy. Tiêu chí: với (1)/(3), bộ đọc
  phát ĐÚNG tập ràng buộc mà ký hiệu chuẩn `hình chóp tứ/tam giác đều X.Y` phát (trừ span) ⇒ mọi bên tiêu thụ, C1 gồm
  cả, xử lý như ký hiệu chuẩn. Không phát gì cho "hình chóp có đỉnh S và đáy ABCD" (không "đều": ngoài phạm vi, không mở
  rộng C1 chóp thường) và cho "chóp đều" có đáy ≠ 3, 4 đỉnh (như ký hiệu chuẩn ngũ/lục giác).
- **Phủ định:** probe phát hiện lỗi có sẵn: "không phải là hình chóp tứ giác đều S.ABCD" bị đọc thành tiền đề
  (`N_K_negation_canonical_notation` bị từ chối). Mọi khẳng định chóp đều (ký hiệu chuẩn và hai lối mới) không phát khi
  đứng ngay sau "không phải (là)".
- **Mục tiêu/câu hỏi:** đã che bởi `che_muc_tieu` (không đổi).

## 2. Sửa (đăng ký trước) — chỉ bộ đọc

1. `_KHOI_CHOP`: nhận thêm `chóp đều X.Y`; phát `regular_square_pyramid`/`regular_triangular_pyramid` (+ `base_*`) theo
   số đỉnh đáy như ký hiệu chuẩn.
2. Mẫu mới cho `chóp tứ/tam giác đều có đỉnh (là) X (và|,) (mặt) đáy (là) Y` — cùng nhóm `dinh`/`day`, dùng chung ở
   `doc_rang_buoc` và `_khoi_cua_du_kien`.
3. Không phát khẳng định chóp đều ngay sau "không phải (là)".
Không đổi `assumption_gate`, route, vùng U3, compiler, khuôn C1.

## 3. Tiêu chí

- `labels.json` (27 hàng C0, `claims` viết tay) + `oracle.py` độc lập; baseline `diagnostics/probe_a1350da3.log`.
- C1: `c1_rule` — trên candidate, kết cục (1)/(3) == kết cục chuẩn ở MỌI hàng của hai corpus chóp đều, bộ đọc trùng
  ký hiệu chuẩn; kết cục chuẩn không đổi; baseline `diagnostics/probe_c1_equivalence_a1350da3.log`.
- Đếm served→refused / refused→served / giữ nguyên so với `main`; hồi quy C0 §21/§22, G04, G05, khuôn C1, compiler,
  toàn bộ pytest so baseline sạch; cache quyết bằng probe trước/sau.
