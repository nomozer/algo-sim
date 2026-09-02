# THESIS_SUBMISSION_CHECKLIST — việc còn lại trước khi nộp

> Chỉ liệt kê việc **thật sự còn lại**. Nội dung nghiên cứu đã đóng; danh sách
> này không chứa việc nào đòi sửa mã nguồn, chạy thêm thực nghiệm, hay đo lại.
>
> Cập nhật lần cuối: 2026-09-02, sau lượt hoàn thiện tầng trình bày.

---

## A. Chưa làm được vì thiếu thông tin từ nhà trường

| | việc | vì sao chưa làm |
|:-:|---|---|
| A1 | Áp mẫu trình bày của trường (bìa, lề, phông, cỡ chữ, trang ký duyệt) | **không tìm thấy mẫu nào trong kho**; không tự đặt ra định dạng |
| A2 | Chốt kiểu trích dẫn (APA / IEEE / kiểu riêng của khoa) | chưa biết quy định; bản thảo đang dùng **tác giả–năm** tạm thời, metadata đủ để chuyển kiểu |
| A3 | Xác định độ dài tối đa và cấu trúc chương bắt buộc | chưa biết quy định; cấu trúc hiện tại là cấu trúc thông dụng |

⚠️ **Ba việc này chặn bước chuyển sang Word/LaTeX.** Cần hỏi giảng viên hướng dẫn
hoặc văn phòng khoa trước khi định dạng.

---

## B. Việc kỹ thuật còn lại, không cần thông tin thêm

| | việc | thời lượng ước tính | tài liệu hướng dẫn |
|:-:|---|---|---|
| ~~B1~~ | ~~Dựng 5 sơ đồ~~ | **XONG** 2026-09-02 | `thesis_figures/fig_3_*.svg`, `fig_4_1_*.svg` |
| ~~B2~~ | ~~Chụp 4 ảnh màn hình~~ | **XONG** 2026-09-02 | `thesis_figures/fig_4_*.png` — 0 lỗi bảng điều khiển |
| ~~B3~~ | ~~Rút gọn ví dụ §3.4.4~~ | **XONG** | 4 câu lệnh ở thân bài, bản đầy đủ ở Phụ lục C |
| B4 | Dựng bảng ánh xạ 21 ↔ 15 thành **hình** nếu bảng quá dài cho khổ giấy | ngắn | quyết sau khi biết bề rộng trang của mẫu trường |
| B5 | Rút gọn tóm tắt tiếng Việt nếu trường quy định giới hạn từ | ngắn | hiện **459 âm tiết** (tiếng Anh 317 từ). Nếu phải cắt, đoạn cắt được là đoạn phạm vi ở cuối — nhưng **không được bỏ** ý *tác động lên người học chưa được đánh giá* |
| ~~B6~~ | ~~Ghép Hình 4.3 thành một tấm~~ | **XONG** 2026-09-02 | `fig_4_3_playback.png` |
| ~~B7~~ | ~~Cân nhắc cắt dòng nhãn sai ở Hình 4.4~~ | **KHÔNG CÒN CẦN** | nhãn đã sửa thành *“CHƯA DỰNG ĐƯỢC MÔ PHỎNG”*; xem `docs/PRESENTATION_UI_POLISH.md` |

### Ghi chú độ dài

Chương 4 dài **~7 500 từ**, gấp gần hai lần Chương 3. Đây là chương thực nghiệm
với bốn lượt đo trình bày theo cùng một cấu trúc, nên độ dài là hợp lý về nội
dung; nhưng nếu trường giới hạn tổng số trang, đây là chương nên chuyển bớt xuống
phụ lục. Phần chuyển được mà **không mất lập luận**: các bảng kết quả chi tiết
của từng lượt (giữ lại bảng tổng hợp 4.7 trong thân bài).

Phụ lục hiện rất mỏng (~20 từ) vì mới chỉ có mục lục trỏ; khi chuyển nội dung
theo gợi ý trên, phụ lục sẽ đầy lên tương ứng.

---

## C. Hai việc trích dẫn còn treo

| | việc | mức | ghi chú |
|:-:|---|---|---|
| C1 | Chốt nơi công bố của Saltzer & Schroeder | **cần làm** | có **mâu thuẫn metadata**: *Proceedings of the IEEE* 63(9), 1975 hay *CACM* 17(7), 1974. Nội dung trích đã đọc nguyên văn nên không ảnh hưởng lập luận. Đối chiếu IEEE Xplore hoặc ACM DL rồi chốt một bản |
| C2 | Đối chiếu bản PDF chương trình môn Toán với bản trên cổng Bộ GD&ĐT | nên làm | bản đã đọc là bản đăng lại trên cổng ngành cấp tỉnh; nội dung khớp, nhưng nơi truy cập nên ghi đúng |
| C3 | Bổ sung nguồn bình duyệt cho luận điểm *quan niệm sai khó sửa* | tuỳ chọn | hiện câu trong bản thảo **đã hạ giọng** cho khớp bằng chứng có; nếu tìm được nguồn thì có thể nâng lại |
| C4 | Đọc toàn văn ba nguồn đang xác minh ở mức trang liệt kê | tuỳ chọn | `[GAO23]` `[MIR25]` `[TAM24]` — chúng chống đỡ những câu nặng nhất của Chương 1 và Chương 5 |

---

## D. Soát cuối trước khi in

- [ ] Đọc lại toàn văn một lượt để bắt lỗi chính tả và lỗi gõ.
- [ ] Kiểm mọi tham chiếu chéo sau khi đánh số lại theo mẫu của trường (§x.y,
      Hình x.y, Bảng x.y không được trôi).
- [ ] Kiểm danh mục hình và danh mục bảng khớp với hình/bảng thật trong bài.
- [ ] Kiểm tóm tắt tiếng Việt và tiếng Anh nói cùng một điều.
- [ ] Kiểm mọi số liệu trong bài khớp với `THESIS_READINESS.md` — tài liệu ấy là
      bảng đối chiếu duy nhất cho số liệu.

---

## E. Điều KHÔNG được làm ở các bước sau

Ghi ra để tránh mở lại việc đã đóng:

| ⛔ | lý do |
|---|---|
| Sửa mã sản phẩm | hệ đã đóng băng; sửa một dòng làm mọi bằng chứng hiện có mất hiệu lực |
| Chạy thêm thực nghiệm với mô hình | các tuyến đo đã đóng; thêm số liệu sẽ phá tính nhất quán của Chương 4 |
| Sửa điểm số lịch sử | nguyên tắc không hồi tố (§4.2) |
| Làm biến mất các giới hạn đã khai | §5.3 là một phần của đóng góp, không phải một điểm yếu cần giấu |
| Chia lại khung đo 21 hàng cho khớp 15 đầu mục | đó là đổi phương pháp đo; mọi số liệu trước đó sẽ không so được nữa |
| Nâng cấp tuyên bố đóng góp sau khi có thêm nguồn | §5.2 đã phân hạng theo tài liệu đã khảo sát; nâng lại cần một tổng quan hệ thống |
