# unnamed-regular-pyramid-grounding — báo cáo

Nhánh `fix/unnamed-regular-pyramid-grounding` từ `ede8d329` (= `origin/main`, khớp). Cloud, 0 lượt gọi model, `LLM_ONLY`
mặc định, compiler opt-in, frontend không đổi. Tiền đăng ký `94b2f89` (47 hàng C1 + 11 hàng C0, oracle, probe baseline)
trước mọi sửa sản phẩm. Kết luận: **`CLOUD_IMPLEMENTATION_COMPLETE_LOCAL_VERIFICATION_REQUIRED`** cho phần gắn được; phần
còn lại cần **quyết định kiến trúc** (§5) — hai issue giữ OPEN, thu hẹp.

## 1. Nguyên nhân (`ede8d329`, `plan.md` §1)

- Bộ đọc không phát khẳng định nào cho "hình chóp tứ/tam giác đều" không tên ("đều" thành chữ chưa đọc).
- C1 chỉ gắn khối không tên cho lăng trụ đứng (bảng mặt của khối duy nhất, nhận cách đọc thoả khuôn) — chóp thì không.
- Đề không ký hiệu khối nằm ngoài vùng từ chối U3 ⇒ cổng tính nhưng không chặn ⇒ phục vụ mọi chương trình (thiếu chiều
  cao ⇒ 16; khung affine T8 không có metric dẫn xuất ⇒ 5 thay 3√3). Nới vùng đơn thuần ⇒ từ chối luôn 22 đề đúng.
- `solid_topology` của RequestContract là đầu ra mô hình — không dùng làm căn cứ gắn.

## 2. Sửa (amendment §24)

- **Bộ đọc:** khối không tên duy nhất là chóp tứ/tam giác đều (không phủ định) ⇒ `regular_*_pyramid ()` + `base_* ()`;
  số đo gắn `()` như sẵn có. Không bao giờ đoán tên đỉnh. `ten_diem_khong_toa_do` = điểm đề gọi tên mà không cho toạ độ.
- **Cổng:** chỉ khi tập trên RỖNG và chương trình dựng đúng một khối: ràng buộc `()` gắn vào cách đọc chóp của bảng mặt
  (như `S.ABCD`). C1/metric T8/nhánh thiếu kích thước: khuôn KIỂM trên giá trị chương trình (gắn ≠ tin). C0: mâu thuẫn chỉ
  khi không cách đọc nào thoả. **Vùng U3** thêm đúng các đề ấy. `formation` chịu `()`.
- Đề gọi tên điểm thiếu toạ độ: KHÔNG gắn — đề không cố định đỉnh (`oracle.py` `ambiguity_witness`: "AB = 4, SA = 3"
  hợp với đỉnh S (V = 16/3) lẫn đỉnh B (thể tích khác)) ⇒ gắn sẽ để cách đặt tên của chương trình quyết định.

## 3. Kết quả (`results/transitions.json`)

**47 đề C1 không tên:**

| phạm vi / lớp | số | trước → sau |
|---|---|---|
| gắn được / đúng | 13 | phục vụ → phục vụ, cùng giá trị |
| gắn được / sai giá trị | 4 | phục vụ sai → phục vụ ĐÚNG giá trị nhãn (5 → 3√3, 3/2 → 9/2, 5/2 → 3√3/2, 9/2 → 3√3) |
| gắn được / nhãn đòi từ chối | 8 | phục vụ → từ chối đúng lý do nhãn (thiếu kích thước ⇒ `ASSUMPTION_DETERMINES_ANSWER`; mâu thuẫn / chiều cao vô tỉ / góc ⇒ `ASSUMPTION_INVARIANCE_UNPROVEN`) |
| gắn được / đã từ chối | 1 | giữ từ chối |
| có tên điểm thiếu toạ độ | 21 | KHÔNG đổi: 9 đúng, 9 từ chối, **3 vẫn phục vụ trái nhãn** (N5 SA = 3, R2_N9 16, W5_C 16/3) |

Mọi 26 hàng gắn được = nhãn corpus (oracle dẫn xuất lại từng giá trị/lý do từ kích thước đề). Không ca mới phục vụ sai.
Biến thể khác (ký hiệu chuẩn, hai lối viết run trước, khối gọi tên ở câu hỏi): 0 thay đổi.

**C0 (11 hàng):** 3 mâu thuẫn không tên served → refused (`SOURCE_SHAPE_CONTRADICTS_COORDINATES`, không Scene3D, không
sửa vòng LLM); 8 giữ phục vụ (nhất quán, đổi tên + phân số, chương trình lấy mặt khác làm đáy nhưng một cách đọc thoả,
phủ định, mục tiêu; 2 hàng không gắn được — điểm M không toạ độ, hai khối — như `main`). Nhãn C0 của hai run trước: §22
29/29 không đổi; run bộ đọc: 2 hàng `P2` (giới hạn ghi `baseline`) nay từ chối, 25 không đổi.

**Kiểm chứng:** `test_unnamed_regular_pyramid_grounding.py` 72/72 (trên `ede8d329`: lỗi thu thập — hàm mới; red-before
hành vi = log probe baseline); bộ đọc + C0 §21/§22 + C1 chóp đều + G04 + G05 + cổng giả định: 848 + 2 test cập nhật có chủ
đích (run trước khoá "không phát khẳng định cho chóp không tên"); demo 5/5; bề mặt sập 6/6. Toàn bộ pytest (worktree sạch,
cùng máy): `12edf57` 7462 passed / 136 failed / 4 errors; `ede8d329` 7395 / 131 / 4 — 131 + 4 có sẵn trùng hệt; 5 đỏ mới =
danh tính candidate (LOCAL đóng băng) — `results/pytest_compare.json`. 49/49 fixture Tier-A trùng byte. Compiler không
đọc bộ đọc này trực tiếp; chương trình compiler qua cùng cổng (trong bộ pytest).

## 4. Cache · candidate

Bề mặt mô hình KHÔNG đổi. **`CACHE_VERSION` 121 → 122** (`cache/decision.json`): 11 đề phục vụ ở 121 nay từ chối, 4 đổi
giá trị đã phục vụ. Khoá danh tính sinh lại bằng script. Mã sản phẩm đổi ⇒ LOCAL đóng băng lại candidate.

## 5. Còn mở — quyết định kiến trúc

21 đề gọi tên điểm mà không toạ độ, không ký hiệu khối (3 phục vụ trái nhãn) + C0 không tên có điểm thiếu toạ độ / hai
khối. Phạm vi nhỏ nhất cho mỗi phương án:
- **(a) Từ chối:** thêm các đề ấy vào vùng U3 với lý do "đề không cố định đỉnh" — ~5 dòng; 9 đáp số đúng-theo-quy-ước
  thành từ chối.
- **(b) Kiểm cách đặt tên:** trong cổng, mọi ánh xạ đơn ánh từ điểm đề gọi tên vào vị trí của khối gắn được (≤ 120) mà
  thoả đề phải cho cùng đáp số — chỉ khi ấy phục vụ. Đúng nhất, cần bộ giải thoả ràng buộc nhỏ trên khuôn T7/T8 + nhãn
  riêng.
- **(c) Giữ nguyên** (hiện trạng nhánh).
Không thực hiện trong lượt này. T3 trình duyệt và mô hình thật: không chạy trên Cloud.
