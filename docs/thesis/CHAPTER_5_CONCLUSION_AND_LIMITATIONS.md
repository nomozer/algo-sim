# Chương 5. Kết luận, giới hạn và hướng phát triển

> Bản thảo. Mọi con số dẫn ở đây đều lấy từ Chương 4 và truy được về artifact có
> băm; không con số nào phát sinh mới ở chương này.

---

## 5.1. Kết luận

Đề tài đặt ra một câu hỏi thực tế: **có thể để mô hình ngôn ngữ đọc một đề hình
học không gian bằng tiếng Việt và cho ra một mô phỏng 3D đúng, mà không để mô
hình chạm vào phép tính hay không?**

Lượt đánh giá cuối, chạy đúng một lần trên bản mã đã đóng băng `d72db7c3…`, cho
câu trả lời sau — trong phạm vi bộ đánh giá và với những giới hạn ở §5.3:

**Được, với ba điều kiện, và mỗi điều kiện đều đo được.**

**Điều kiện thứ nhất — phần tất định phải giữ toàn bộ phép tính.** Bảy ca dương
cho **11/11 đại lượng chính xác tuyệt đối**, đối chiếu với một oracle cài độc lập
với nhân hình học. Ba trong số đó là số vô tỉ — `3√6`, `25π√5`, `2π√6` — được giữ
nguyên dạng chính xác suốt chuỗi tính toán và hiển thị, không làm tròn ở bất kỳ
khâu nào. Đây không phải một chi tiết kỹ thuật: nếu mô hình được phép trả về
toạ độ hay đáp số, không cơ chế nào ở phía sau còn kiểm được nó.

**Điều kiện thứ hai — mô hình phải tìm được chương trình.** Trên bộ ca này, mô
hình tự tìm được chương trình đúng ở **6/7 ca ngay lần đầu** (85,7 %) và **7/7
sau tối đa một lượt sửa** (100 %), phủ đủ **10/10 họ hình trong phạm vi** mà
**không thêm một phép IR nào, một kiểu bộ nhớ nào, hay một module riêng cho bài
nào**. Mệnh đề *"bài mới không đòi mã mới"* đứng vững trên bảy dạng bài khác
nhau — nhưng nó là mệnh đề **có điều kiện**: điều kiện là bài phải biểu diễn được
bằng IR hiện có.

**Điều kiện thứ ba — bài ngoài bao đóng phải bị từ chối, không được xấp xỉ.**
Hai ca âm đều fail-closed, **không ca nào phát ra một đại lượng nào**;
`SILENT_WRONG_ANSWER_COUNT = 0` và `UNHANDLED_EXCEPTION_COUNT = 0`. Điều đáng ghi
nhận không nằm ở con số mà ở **cách** hệ từ chối: ở `n1`, mô hình đã cố bịa ba
điểm không có trong đề để đi tiếp, và cổng xuất xứ chặn lại. Ranh giới R0 vì thế
không chỉ là một nguyên tắc trên giấy — nó là một ràng buộc được cưỡng chế trên
đường chạy thật, và nó đã thật sự chặn một lần.

Chi phí để đạt những điều trên: **19 lượt gọi mô hình, 97 869 token cho 9 ca** —
tương đương **13 981 token và 2,71 lượt gọi cho mỗi mô phỏng được phục vụ đúng**.

---

## 5.2. Đóng góp của đề tài

**(1) Một kiến trúc phân vai có ranh giới cưỡng chế được, không chỉ khai báo.**
Mô hình sở hữu *hợp đồng yêu cầu* và *chương trình ngữ nghĩa* — tức các **bước
dựng**; toàn bộ toạ độ, phép đo, thẩm định và cảnh 3D thuộc về các tầng tất định.
Ranh giới này được cưỡng chế ở **lược đồ**: mọi toán hạng hình học trong IR là
**tên** của một vật đã dựng, nên mô hình không có chỗ nào để viết một con số vào.
Đóng góp nằm ở chỗ ranh giới ấy được **kiểm chứng trên đường chạy thật**, chứ
không phải được mô tả trong tài liệu thiết kế.

**(2) Một nhân hình học tính chính xác trên `ℚ(√, π)`, mở rộng được sang mặt
cong.** Khối cầu, hình trụ và hình nón được khai bằng **ba điểm hữu tỉ** thay vì
bằng cặp (trục, bán kính) — nhờ vậy toạ độ ở lại trong ℚ³ ngay cả khi bán kính là
số vô tỉ. Kết quả đo được của lựa chọn này là hai ca thiết diện elip xiên cho đáp
số đúng ở dạng chính xác, điều mà một nhân dấu phẩy động không thể tuyên bố.

**(3) Một phương pháp đánh giá tách ba chiều và đăng ký trước.** Đáp số đúng ·
hình dựng đúng · hệ dám phát được ghi **riêng biệt** ở mọi artifact và không
chiều nào suy ra từ chiều khác — vì trong lớp hệ thống này, "phát ra một đáp số
đúng" và "dựng đúng hình" là hai thất bại độc lập. Toàn bộ tiêu chí, ngưỡng, ngân
sách và bộ ca được khoá **trước** khi có kết quả, và băm được. Một số chỉ báo
hành vi được **cố ý** để không ngưỡng, kèm lý do — vì một vạch đặt sau khi thấy
kết quả chỉ mô tả lại kết quả.

**(4) Một cơ chế truy vết bằng chứng gắn vào mã nguồn, không gắn vào commit.**
Mọi artifact mang dấu vân tay của cây mã được đo; sửa một dòng mã sản phẩm làm
mọi bằng chứng trước đó lập tức mang nhãn cũ. Cùng với đó là cơ chế **đóng băng
ứng viên**: ba đường dẫn được đo được liệt kê tường minh, và chạm vào chúng làm
số đo mất hiệu lực cho tới khi đóng băng lại. Hệ quả là mọi con số trong luận văn
đều nói được nó thuộc về **bản mã nào**.

**(5) Một ghi chép trung thực về sai sót của chính công cụ đo.** Lượt chấm đầu
tiên báo sáu đáp số sai âm thầm; điều tra cho thấy **hệ đúng, bộ chấm sai** — nó
tra kết quả bằng tên biến của chương trình mẫu trong khi tên biến là thứ mô hình
tự đặt. Sự cố được sửa **ngoại tuyến**, không gọi lại mô hình, không chạy lại ca
nào, dữ liệu thô giữ nguyên từng byte, bản đính chính nối với bản gốc bằng băm.
Việc công bố sự cố này — cùng với lý do provider giả không thể bắt được nó — là
một phần của đóng góp phương pháp, không phải một phụ lục.

---

## 5.3. Giới hạn

Bốn nhóm, xếp theo mức độ ảnh hưởng tới điều có thể tuyên bố.

### 5.3.1. Giới hạn về phạm vi ngoại suy

**Bộ đánh giá không phải held-out.** `HELD_OUT_CLAIM = NO`. Đề do chính người
triển khai soạn và nằm trong kho mã. Mô hình không nhận đáp số, chương trình mẫu
hay bất kỳ siêu dữ liệu chấm điểm nào — đường gửi tới mô hình trả về đúng một
trường là đề bài — nhưng *"mô hình chưa thấy"* không đồng nghĩa với *"người soạn
bộ đo chưa thấy"*. Mọi con số ở Chương 4 mô tả **hệ này trên bộ ca này**, và
không được diễn giải như ước lượng cho đề chưa từng gặp.

**Mẫu nhỏ: `n = 1` mỗi họ hình.** Bảy ca dương là một lời giải set-cover tối
thiểu — hiệu quả về ngân sách, nhưng có nghĩa là mỗi họ chỉ có một quan sát. Con
số 85,7 % không có khoảng tin cậy có ý nghĩa.

**Chỉ một lượt đánh giá.** `STABILITY_UNDER_ACCEPTANCE = NOT_MEASURED` —
kết luận này được khoá **trước** lượt chạy, không suy từ kết quả. Với mô hình
sinh có `temperature = 0.2`, một lượt không cho biết kết quả có lặp lại được
không. Tỷ lệ 6/7 có thể là 5/7 hoặc 7/7 ở lượt sau; đề tài không có cơ sở để nói
khác.

### 5.3.2. Giới hạn về năng lực hệ thống

**Bao đóng biểu đạt hữu hạn.** Hai họ hình nằm ngoài phạm vi vì lý do kiến trúc
đo được: khối tròn xoay tổng quát cần thẩm quyền tích phân ký hiệu mà hệ không
có, và khối ghép/bù cần hình học boolean mà nhân không có. Bằng chứng thuộc lớp
**chứng minh vắng mặt** — quét mã nguồn cho thấy không tồn tại thẩm quyền tương
ứng — chứ không phải một mã lỗi mang tên hai họ đó. Vì vậy `C9` được ghi
**PARTIAL**.

**Ranh giới không phải lúc nào cũng nói đúng tên mình.** `TARGET_BOUNDARY_PASS =
1/2`: `n2` bị từ chối đúng mã đã đăng ký trước, còn `n1` bị từ chối ở một tầng
**sớm hơn** — trong vòng tổng hợp, trước khi bất kỳ mã lỗi thẩm định nào tồn tại
để đối chiếu. Hành vi an toàn đạt; nhưng phép đăng ký trước đã đăng ký một thứ
mà tầng quan sát không nhìn thấy được. Luận văn **giữ nguyên** kỳ vọng đã đăng ký
và ghi lại sai lệch, thay vì sửa kỳ vọng cho khớp kết quả.

**Chưa đủ điều kiện bật cho sản phẩm.** `PRODUCT_PROMOTION_ELIGIBLE = NO`. Điều
kiện *"đã đo độ ổn định"* của chính sách không thoả với `n = 1` và một lượt chạy.
Một lượt đánh giá tốt không phải là giấy phép bật tính năng.

### 5.3.3. Giới hạn về đo lường

**Công cụ đo đã từng sai một lần, và sai theo hướng nguy hiểm.** Sự cố ở §4.8
báo *sai* rằng hệ phát ra sáu đáp số sai. Nó bị phát hiện vì con số đủ phi lý để
buộc phải soi lại — tức là **cơ chế phát hiện là sự chú ý của con người**, không
phải một guard tự động. Sau sự cố, guard và phép tiêm lỗi tương ứng đã được bổ
sung, nhưng bài học tổng quát vẫn đứng: **một provider giả giống bản mẫu quá mức
thì không kiểm được những lỗi chỉ xuất hiện khi mô hình được tự do lựa chọn.**

**Tái lập ở mức hạn chế.** `MODEL_REPRODUCIBILITY = LIMITED_ACCEPTED`. Alias mô
hình, thời điểm UTC và các tham số gửi/không-gửi đều được ghi lại, nhưng nhà cung
cấp có thể đổi bản dựng phía sau một alias. Đề tài không tuyên bố tái lập từng
bit.

**Người soạn bộ đo cũng là người triển khai hệ.** `OPERATOR_INDEPENDENCE_REQUIRED
= NO`. Biện pháp giảm nhẹ là khoá và băm toàn bộ tiêu chí trước khi có kết quả —
nó ngăn được việc **sửa vạch sau khi thấy điểm**, nhưng không ngăn được việc
**chọn bài dễ trúng năng lực hệ** ngay từ đầu.

**Chỉ đo cấu trúc cảnh, không đo chất lượng thị giác.** `C4` xác nhận cảnh 3D
được dẫn xuất từ trạng thái tất định và đủ thành phần; nó **không** nói cảnh dễ
hiểu hay có ích cho người học.

### 5.3.4. Giới hạn về vận hành

**Dự báo chi phí lệch 31 %** (97 869 thực so với 74 763 dự báo), nguyên nhân đã
định vị: `thought_tokens` chiếm 34 % tổng mà trung vị lịch sử không tách riêng.
Cần phân biệt hai vai trò: dự báo sai 31 %, còn **trần cứng vẫn hoàn thành vai
trò an toàn** — dư 50 %, và ngân sách được kiểm trước từng lượt gọi.

**Con số chi phí không so được liên lượt.** 13 981 token/ca chỉ có nghĩa cùng với
mẫu số 7 ca đạt; một lượt đo có tỷ lệ đạt khác sẽ cho một mẫu số khác.

---

## 5.4. Hướng phát triển

Xếp theo thứ tự mà kết quả ở Chương 4 **thật sự chỉ ra**, không theo mức độ hấp
dẫn.

**(1) Đo độ ổn định — việc phải làm trước mọi việc khác.** Chạy lại cùng bộ ca
`k` lần để chuyển `STABILITY_UNDER_ACCEPTANCE` từ `NOT_MEASURED` sang một con số.
Đây là điều kiện chưa thoả duy nhất chặn `PRODUCT_PROMOTION_ELIGIBLE`, và cũng là
thứ quyết định con số 85,7 % có ý nghĩa gì. Mọi hướng phía dưới đều nên đợi kết
quả này.

**(2) Một bộ đánh giá thật sự held-out, do người khác soạn.** Giới hạn nặng nhất
của đề tài là ngoại suy, và nó **không** sửa được bằng cách thêm ca vào bộ hiện
có — chỉ sửa được bằng cách đổi **ai soạn đề**. Bộ đề do giáo viên soạn theo
chuẩn chương trình, người triển khai không xem trước, sẽ cho một con số khác hẳn
về chất.

**(3) Cải thiện cách hệ mô tả hợp đồng cho mô hình, trước khi mở rộng IR.** Ca
`p3` hỏng ở một lỗi **kiểu** — mô hình chọn đúng phép nhưng khai sai kiểu vật —
và tự sửa được ngay khi nhận lại chính thông điệp từ chối. Kinh nghiệm của dự án
cho thấy nhiều khoảng trống tưởng là thiếu năng lực hoá ra chỉ là **thiếu cách
nói cho mô hình biết hệ làm được gì**. Hướng rẻ và có nhiều khả năng thắng: làm
thẻ văn phạm nói rõ kiểu vật của từng phép.

**(4) Mở rộng bao đóng biểu đạt — đắt, và chỉ nên làm khi có bằng chứng cần.**
Hai họ ngoài phạm vi đòi hai thẩm quyền mới: tích phân ký hiệu cho khối tròn xoay
tổng quát, và hình học boolean cho khối ghép/bù. Cả hai đều chạm **bề mặt mô
hình**, nên kéo theo trọn nhịp đóng băng lại và đo lại. Trước khi mở, nên hỏi câu
rẻ hơn ở mục (3).

**(5) Đánh giá sư phạm — chiều mà đề tài chưa chạm.** Mọi con số ở Chương 4 nói
về **tính đúng**, không nói về **tính hữu ích**. Một mô phỏng đúng tuyệt đối vẫn
có thể vô dụng trên lớp. Đo điều đó cần học sinh thật, giáo viên thật và một
thiết kế nghiên cứu khác hẳn — nằm ngoài phạm vi luận văn này, nhưng là bước tiếp
theo tự nhiên của một hệ đã chứng minh được nó không nói dối.

**(6) Củng cố công cụ đo theo bài học đã trả giá.** Provider giả nên **cố ý khác
bản mẫu** ở những chỗ mô hình có tự do — tên biến, thứ tự bước, cách đặt tên
trung gian — vì đó chính xác là nơi bộ chấm đã mù một lần.
