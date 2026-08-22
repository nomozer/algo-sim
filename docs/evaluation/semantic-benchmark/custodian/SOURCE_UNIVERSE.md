# SOURCE UNIVERSE — bài tập SGK để custodian độc lập CHỌN

> **Vai trò của phase này:** development agent thực hiện trích xuất cơ học từ
> nguồn SGK. **Quyền lựa chọn 40 case SEALED thuộc về GVHD/custodian độc lập.**

Danh sách này **không** phản ánh năng lực của hệ đang được đánh giá. Nó phản
ánh nội dung SGK.

## Phạm vi đã duyệt

| SGK | Chủ đề | Trang sách | Số record |
|---|---|---|---|
| `tin-hoc-10.pdf` | Chủ đề 5 — Giải quyết vấn đề với sự trợ giúp của máy tính | 86 – 155 (70 trang) | **109** |
| `tin-hoc-11-cs.pdf` | Chủ đề 6 — Kĩ thuật lập trình | 81 – 145 (65 trang) | **75** |
| | | **135 trang** | **184** |

Duyệt **tuần tự toàn bộ** hai chương, không bỏ trang nào.

## Cách đọc nguồn

Năm cuốn SGK là **bản quét, không có lớp chữ** — `pdftotext` trả về 60 ký tự
cho 60 trang, đúng bằng số dấu ngắt trang. Máy cũng không có OCR nào
(`pytesseract`, `PIL`, `pdf2image`, `tesseract` CLI đều vắng).

Cách đọc: cài `pymupdf`, dựng ảnh từng trang ở 95 DPI, ghép 4 trang một ảnh rồi
đọc trực tiếp bằng thị giác. **Mọi số trang trong bảng là số trang IN TRÊN
SÁCH**, tra ngược được.

Không có trang nào khó đọc hoặc không xác định được nội dung.

## Quy tắc trích — khai trước để kiểm toán được

**NHẬN** mọi câu hỏi/bài tập/nhiệm vụ đòi một **kết quả xác định tính được** từ
dữ liệu hoặc thủ tục đã cho: một giá trị, một dãy, một đếm, một vị trí, một ánh
xạ, hay một trạng thái cuối.

**LOẠI** câu hỏi thuần định nghĩa · nêu ý kiến · kể tên · thao tác giao diện ·
"lệnh này có lỗi không / thuộc loại lỗi gì" · in ra một chuỗi cho sẵn.

Quy tắc này nói về **bản chất bài toán**. Nó không hỏi hệ có làm được hay
không: bài thoả rubric mà IR hiện tại có thể không biểu diễn được thì **vẫn
được giữ** — đó có thể trở thành `capability_gap`, một kết quả nghiên cứu hợp
lệ.

Một record = một mục được đánh số trong sách. Mục có nhiều ý a/b/c/d giữ nguyên
trong cùng một record, đúng như sách đánh số.

## Chưa làm ở phase này

Chưa giải bài · chưa tạo ground truth · chưa phân loại theo khả năng hệ thống ·
**chưa chọn 40 case SEALED**.

## Lưu ý khi chọn

Tập **INTERNAL LIVE PILOT** (`../pilot/sealed-pilot-34a10a9c/`) đã lấy một số
bài từ chính hai chương này. Bộ 40 case SEALED phải **khác** tập đó. Nếu cần
danh sách đối chiếu, mở `cases.json` của pilot — mỗi case ở đó ghi rõ
`source.location` là trang và số bài.

## Fingerprint

```
971981da321a918a61c15357bfe1edb756a369115c9410b0b80cf219c41818a1
```

SHA-256 của `source_universe.json`.

## Kiểm chất lượng

```
PASS — mọi kiểm tra đều đạt
```

Đã kiểm: `source_id` duy nhất · mọi record có `book` · có `page` · có
`problem_text` không rỗng · không có record trùng hoàn toàn · sắp theo sách →
trang → vị trí · số record trong JSON khớp bảng trên · fingerprint tính trên
đúng file JSON cuối cùng.

## Bảng chọn

| ID | SGK | Chủ đề | Trang | Số bài/vị trí | Nội dung nhận diện ngắn |
|---|---|---|---|---|---|
| `T10-C5-001` | TH10 | CĐ5 | 89 | Câu hỏi 1 | Kết quả của mỗi lệnh sau là gì? Kết quả đó có kiểu dữ liệu nào? >>> 5/2 ; >>> 12 + 1.5 ; >>>… |
| `T10-C5-002` | TH10 | CĐ5 | 89 | Câu hỏi 2 | Lệnh sau sẽ in ra kết quả gì? >>> print("13 + 10*3/2 - 3*2 = ", 13 + 10*3/2 - 3*2) |
| `T10-C5-003` | TH10 | CĐ5 | 90 | Luyện tập 1 | Hãy viết lệnh để tính giá trị các biểu thức sau trong chế độ gõ lệnh trực tiếp của Python: a)… |
| `T10-C5-004` | TH10 | CĐ5 | 90 | Vận dụng 2 | Viết chương trình Python in ra màn hình bảng nhân trong phạm vi 10. |
| `T10-C5-005` | TH10 | CĐ5 | 93 | Câu hỏi 2 | Sau các lệnh dưới đây, các biến x, y nhận giá trị bao nhiêu? >>> x = 10 ; >>> y = x**2 - 1 ;… |
| `T10-C5-006` | TH10 | CĐ5 | 93 | Câu hỏi 3 | a, b nhận giá trị gì sau các lệnh sau? >>> a,b = 2,3 ; >>> a,b = a+b, a-b |
| `T10-C5-007` | TH10 | CĐ5 | 94 | Câu hỏi 1 | Mỗi lệnh sau là đúng hay sai? Nếu đúng thì cho kết quả là bao nhiêu? >>> (12 - 10//2)**2 - 1… |
| `T10-C5-008` | TH10 | CĐ5 | 94 | Câu hỏi 2 | Mỗi lệnh sau cho kết quả là xâu kí tự như thế nào? >>> ""*20 + "010" ; >>> "10"+"0"*5 |
| `T10-C5-009` | TH10 | CĐ5 | 95 | Thực hành, Nhiệm vụ 1 | Thực hiện các phép tính sau trong môi trường lập trình Python, so sánh kết quả với việc tính… |
| `T10-C5-010` | TH10 | CĐ5 | 96 | Thực hành, Nhiệm vụ 2 | Gán giá trị cho biến R là bán kính hình tròn rồi viết chương trình tính và in kết quả theo… |
| `T10-C5-011` | TH10 | CĐ5 | 96 | Luyện tập 2 | Lệnh sau sẽ in ra kết quả gì? >>> print("đồ rê mi "*3 + "pha son la si đô "*2) |
| `T10-C5-012` | TH10 | CĐ5 | 96 | Vận dụng 1 | Viết các lệnh để thực hiện việc đổi số giây ss cho trước sang số ngày, giờ, phút, giây, in… |
| `T10-C5-013` | TH10 | CĐ5 | 96 | Vận dụng 2 | Hãy cho biết trước và sau khi thực hiện các lệnh sau, giá trị các biến x, y là bao nhiêu. Em… |
| `T10-C5-014` | TH10 | CĐ5 | 98 | Câu hỏi | Xác định kiểu và giá trị của các biểu thức sau: a) "15 + 20 - 7"; b) 32 > 45; c) 13 != 8 + 5;… |
| `T10-C5-015` | TH10 | CĐ5 | 99 | Câu hỏi 1 | Mỗi lệnh sau sẽ trả lại các giá trị nào? a) str(150); b) int("1110"); c) float("15.0"). |
| `T10-C5-016` | TH10 | CĐ5 | 100 | Thực hành, Nhiệm vụ 1 | Viết chương trình nhập lần lượt ba số tự nhiên m, n, p, sau đó in ra tổng của ba số này. |
| `T10-C5-017` | TH10 | CĐ5 | 100 | Vận dụng 1 | Viết chương trình nhập giá trị ss là số giây từ bàn phím. Thông báo ra màn hình thời gian ss… |
| `T10-C5-018` | TH10 | CĐ5 | 100 | Vận dụng 2 | Viết chương trình nhập ba số thực dương a, b, c và tính chu vi, diện tích của tam giác có độ… |
| `T10-C5-019` | TH10 | CĐ5 | 102 | Câu hỏi | Mỗi biểu thức sau có giá trị True hay False? a) 100%4 == 0; b) 111//5 != 20 or 20%3 != 0. |
| `T10-C5-020` | TH10 | CĐ5 | 103 | Thực hành, Nhiệm vụ 1 | Viết chương trình nhập số tự nhiên n từ bàn phím. Sau đó thông báo số em đã nhập là số chẵn… |
| `T10-C5-021` | TH10 | CĐ5 | 104 | Thực hành, Nhiệm vụ 2 | Giả sử giá điện sinh hoạt trong khu vực gia đình em ở được tính luỹ kế theo từng tháng như… |
| `T10-C5-022` | TH10 | CĐ5 | 104 | Luyện tập 2 | Tìm một vài giá trị m, n thoả mãn các biểu thức sau: a) 100%m == 0 and n%5 != 0; b) m%100 ==… |
| `T10-C5-023` | TH10 | CĐ5 | 104 | Vận dụng 1 | Giá bán cam tại siêu thị tính như sau: nếu khối lượng cam mua dưới 5 kg thì giá bán là 12 000… |
| `T10-C5-024` | TH10 | CĐ5 | 104 | Vận dụng 2 | Năm n là năm nhuận nếu giá trị n thoả mãn điều kiện: n chia hết cho 400 hoặc n chia hết cho 4… |
| `T10-C5-025` | TH10 | CĐ5 | 105 | Hoạt động 1 | Thực hiện đoạn chương trình sau trong chế độ gõ lệnh trực tiếp của Python để tính tổng 0 + 1… |
| `T10-C5-026` | TH10 | CĐ5 | 106 | Câu hỏi | Với giá trị n cho trước, so sánh giá trị S trong đoạn chương trình sau với tổng 1 + 2 + ... +… |
| `T10-C5-027` | TH10 | CĐ5 | 107 | Thực hành, Nhiệm vụ 1 | Nhập số tự nhiên n từ bàn phím và in ra màn hình dãy các ước số của n theo chiều ngang màn… |
| `T10-C5-028` | TH10 | CĐ5 | 107 | Thực hành, Nhiệm vụ 2 | Nhập số tự nhiên n từ bàn phím và đếm số các ước số thực sự của n. Ước số thực sự của n là số… |
| `T10-C5-029` | TH10 | CĐ5 | 107 | Luyện tập 1 | Đoạn chương trình sau in ra kết quả gì? n = int(input("Nhập số tự nhiên n:")) ; S = 0 ; for k… |
| `T10-C5-030` | TH10 | CĐ5 | 107 | Luyện tập 2 | Viết đoạn chương trình tính tích 1 × 2 × 3 × ... × n với n được nhập vào từ bàn phím. |
| `T10-C5-031` | TH10 | CĐ5 | 107 | Vận dụng 1 | Viết chương trình nhập từ bàn phím số tự nhiên n và in ra kết quả S = 1 + 1/2 + ... + 1/n. |
| `T10-C5-032` | TH10 | CĐ5 | 107 | Vận dụng 2 | Viết chương trình nhập từ bàn phím số tự nhiên n và in ra kết quả là tổng sau: S = 1³ + 2³ +… |
| `T10-C5-033` | TH10 | CĐ5 | 109 | Câu hỏi 2 | Viết đoạn chương trình tính tổng 2 + 4 + ... + 100 sử dụng lệnh while. |
| `T10-C5-034` | TH10 | CĐ5 | 110 | Thực hành, Nhiệm vụ 2 | Viết chương trình in ra màn hình dãy các chữ cái tiếng Anh từ "A" đến "Z" theo ba hàng ngang… |
| `T10-C5-035` | TH10 | CĐ5 | 110 | Luyện tập 1 | Cho dãy số 1, 4, 7, 10,.... Viết chương trình in ra phần tử lớn nhất của dãy nhưng nhỏ hơn 100. |
| `T10-C5-036` | TH10 | CĐ5 | 110 | Luyện tập 2 | Viết chương trình đếm trong dãy 100 số tự nhiên đầu tiên có bao nhiêu số thoả mãn điều kiện:… |
| `T10-C5-037` | TH10 | CĐ5 | 110 | Vận dụng | Viết chương trình in các số tự nhiên từ 1 đến 100 ra màn hình thành 10 hàng, mỗi hàng 10 số,… |
| `T10-C5-038` | TH10 | CĐ5 | 112 | Câu hỏi 1 | Cho danh sách A = [1, 0, "One", 9, 15, "Two", True, False]. Hãy cho biết giá trị các phần tử:… |
| `T10-C5-039` | TH10 | CĐ5 | 113 | Câu hỏi 2 | Cho dãy các số nguyên A, viết chương trình in ra các số chẵn của A. |
| `T10-C5-040` | TH10 | CĐ5 | 113 | Câu hỏi 2 (mục 3) | Danh sách A sẽ như thế nào sau các lệnh sau? >>> A = [2,4,10,1,0] ; >>> A.append(100) ; >>>… |
| `T10-C5-041` | TH10 | CĐ5 | 114 | Thực hành, Nhiệm vụ 2 | Nhập một dãy số từ bàn phím. Tính tổng, trung bình của dãy và in dãy số trên một hàng ngang. |
| `T10-C5-042` | TH10 | CĐ5 | 114 | Vận dụng | Cho dãy số A. Viết chương trình tìm giá trị và chỉ số của phần tử lớn nhất của A. Tương tự… |
| `T10-C5-043` | TH10 | CĐ5 | 116 | Câu hỏi 1 | Giả sử A = ["0","1","01","10"]. Các biểu thức sau trả về giá trị đúng hay sai? a) 1 in A; b)… |
| `T10-C5-044` | TH10 | CĐ5 | 117 | Câu hỏi 2 | Danh sách A trước và sau lệnh insert() là [1,4,10,0] và [1,4,10,5,0]. Lệnh đã dùng là gì? |
| `T10-C5-045` | TH10 | CĐ5 | 117 | Thực hành, Nhiệm vụ 1 | Nhập số n từ bàn phím, sau đó nhập danh sách n tên học sinh trong lớp và in ra danh sách các… |
| `T10-C5-046` | TH10 | CĐ5 | 117 | Thực hành, Nhiệm vụ 2 | Cho trước dãy số A. Viết chương trình xoá đi các phần tử có giá trị nhỏ hơn 0 từ A. (Chương… |
| `T10-C5-047` | TH10 | CĐ5 | 118 | Thực hành, Nhiệm vụ 3 | Cho trước dãy số A. Viết chương trình tìm và chỉ ra vị trí đầu tiên của dãy số A mà ba số… |
| `T10-C5-048` | TH10 | CĐ5 | 118 | Luyện tập 1 | Cho dãy số [1,2,2,3,4,5,5]. Viết lệnh thực hiện: a) Chèn số 1 vào ngay sau giá trị 1 của dãy.… |
| `T10-C5-049` | TH10 | CĐ5 | 118 | Luyện tập 2 | Cho trước dãy số A. Viết chương trình thực hiện công việc sau: xoá đi một phần tử ở chính… |
| `T10-C5-050` | TH10 | CĐ5 | 118 | Vận dụng 1 | Viết chương trình nhập n từ bàn phím, tạo và in ra màn hình dãy số A bao gồm n số tự nhiên… |
| `T10-C5-051` | TH10 | CĐ5 | 118 | Vận dụng 2 | Dãy số Fibonacci được xác định như sau: F0 = 0; F1 = 1; Fn = F(n-1) + F(n-2) (với n ≥ 2).… |
| `T10-C5-052` | TH10 | CĐ5 | 120 | Câu hỏi 2 | Mỗi xâu hợp lệ ở Câu 1 có độ dài bằng bao nhiêu? (Câu 1: a) "123&*()+-ABC"; b)… |
| `T10-C5-053` | TH10 | CĐ5 | 121 | Câu hỏi 1 | Sau khi thực hiện các lệnh sau, biến skq sẽ có giá trị bao nhiêu? >>> s = "81723" ; >>> skq =… |
| `T10-C5-054` | TH10 | CĐ5 | 121 | Câu hỏi 2 | Cho s1 = "abc", s2 = "ababcabca". Các biểu thức lôgic sau cho kết quả là đúng hay sai? a) s1… |
| `T10-C5-055` | TH10 | CĐ5 | 121 | Thực hành, Nhiệm vụ 2 | Nhập một xâu kí tự S từ bàn phím rồi kiểm tra xem xâu S có chứa xâu con "10" không. |
| `T10-C5-056` | TH10 | CĐ5 | 122 | Luyện tập 1 | Cho xâu S, viết đoạn lệnh trích ra xâu con của S bao gồm ba kí tự đầu tiên của S. |
| `T10-C5-057` | TH10 | CĐ5 | 122 | Luyện tập 2 | Viết chương trình kiểm tra xâu S có chứa chữ số không. Thông báo "S có chứa chữ số" hoặc "S… |
| `T10-C5-058` | TH10 | CĐ5 | 122 | Vận dụng 1 | Cho hai xâu s1, s2. Viết đoạn chương trình chèn xâu s1 vào giữa s2, tại vị trí len(s2)//2. In… |
| `T10-C5-059` | TH10 | CĐ5 | 122 | Vận dụng 2 | Viết chương trình nhập số học sinh và họ tên học sinh. Sau đó đếm xem trong danh sách có bao… |
| `T10-C5-060` | TH10 | CĐ5 | 123 | Khởi động | Cho xâu c = "Trường Sơn" và xâu m = "Bước chân trên dải Trường Sơn". Em hãy cho biết xâu c có… |
| `T10-C5-061` | TH10 | CĐ5 | 124 | Câu hỏi 1 | Biểu thức lôgic sau là đúng hay sai? >>> "010" in "001100" |
| `T10-C5-062` | TH10 | CĐ5 | 124 | Câu hỏi 2 | Lệnh sau trả lại giá trị gì? >>> "abababab".find("ab",4) |
| `T10-C5-063` | TH10 | CĐ5 | 125 | Câu hỏi | Cho xâu kí tự: "gà,vịt,chó,lợn,ngựa,cá". Em hãy trình bày cách làm để xoá các dấu "," và thay… |
| `T10-C5-064` | TH10 | CĐ5 | 125 | Thực hành, Nhiệm vụ 1 | Viết chương trình nhập nhiều số nguyên từ bàn phím, các số cách nhau bởi dấu cách. Khi nhập… |
| `T10-C5-065` | TH10 | CĐ5 | 126 | Thực hành, Nhiệm vụ 2 | Viết chương trình nhập một xâu kí tự có thể có nhiều dấu cách giữa các từ. Sau đó chỉnh sửa… |
| `T10-C5-066` | TH10 | CĐ5 | 126 | Thực hành, Nhiệm vụ 3 | Viết chương trình nhập số tự nhiên n, rồi nhập họ tên của n học sinh. Sau đó in ra danh sách… |
| `T10-C5-067` | TH10 | CĐ5 | 126 | Luyện tập 1 | Viết chương trình nhập nhiều số (số nguyên hoặc số thực) từ bàn phím, các số cách nhau bởi… |
| `T10-C5-068` | TH10 | CĐ5 | 126 | Luyện tập 2 | Viết chương trình nhập họ tên đầy đủ của người dùng, sau đó in thông báo tên và họ đệm của… |
| `T10-C5-069` | TH10 | CĐ5 | 126 | Vận dụng 1 | Viết chương trình nhập hai số tự nhiên từ bàn phím, cách nhau bởi dấu cách và đưa ra kết quả… |
| `T10-C5-070` | TH10 | CĐ5 | 126 | Vận dụng 2 | Viết chương trình nhập số tự nhiên n rồi nhập n họ tên học sinh. Sau đó yêu cầu nhập một tên… |
| `T10-C5-071` | TH10 | CĐ5 | 129 | Thực hành, Nhiệm vụ 2 | Viết hàm prime(n) với tham số là số tự nhiên n và trả lại True nếu n là số nguyên tố, trả lại… |
| `T10-C5-072` | TH10 | CĐ5 | 130 | Luyện tập 1 | Viết hàm với tham số là số tự nhiên n in ra các số là ước nguyên tố của n. |
| `T10-C5-073` | TH10 | CĐ5 | 130 | Luyện tập 2 | Viết hàm numbers(s) đếm số các chữ số có trong xâu s. Ví dụ numbers("0101abc") = 4. |
| `T10-C5-074` | TH10 | CĐ5 | 130 | Vận dụng 2 | Viết chương trình yêu cầu nhập từ bàn phím một xâu kí tự, sau đó thông báo: tổng số các kí tự… |
| `T10-C5-075` | TH10 | CĐ5 | 133 | Ví dụ 2 | Cho trước dãy số A. Tính tổng các số hạng dương của dãy. (Sách minh hoạ với A =… |
| `T10-C5-076` | TH10 | CĐ5 | 133 | Câu hỏi 1 | Sử dụng hàm prime, em hãy viết chương trình in ra các số nguyên tố trong khoảng từ m đến n,… |
| `T10-C5-077` | TH10 | CĐ5 | 134 | Thực hành, Nhiệm vụ 1 | Thiết lập hàm f_sum(A,b) có chức năng tính tổng các số của danh sách A theo quy định sau: nếu… |
| `T10-C5-078` | TH10 | CĐ5 | 134 | Thực hành, Nhiệm vụ 2 | Thiết lập hàm f_dem(msg, sep) có chức năng đếm số các từ của một xâu msg với kí tự tách từ là… |
| `T10-C5-079` | TH10 | CĐ5 | 134 | Thực hành, Nhiệm vụ 3 | Thiết lập hàm merge_str(s1,s2) với s1, s2 là hai xâu cần gộp. Hàm này sẽ gộp hai xâu s1, s2… |
| `T10-C5-080` | TH10 | CĐ5 | 135 | Luyện tập 1 | Thiết lập hàm power(a,b,c) với a, b, c là số nguyên. Hàm trả lại giá trị (a+b) mũ c. |
| `T10-C5-081` | TH10 | CĐ5 | 135 | Luyện tập 2 | Viết chương trình thực hiện: nhập hai số tự nhiên từ bàn phím, hai số cách nhau bởi dấu cách.… |
| `T10-C5-082` | TH10 | CĐ5 | 135 | Vận dụng 1 | Viết chương trình thực hiện: nhập hai số tự nhiên từ bàn phím, hai số cách nhau bởi dấu phẩy,… |
| `T10-C5-083` | TH10 | CĐ5 | 135 | Vận dụng 2 | Thiết lập hàm change() có hai tham số là xâu ho_ten và số c. Hàm sẽ trả lại xâu kí tự ho_ten… |
| `T10-C5-084` | TH10 | CĐ5 | 137 | Câu hỏi 1 | Giả sử có các lệnh sau: >>> a,b = 1,2 ; >>> def f(a,b): a = a + b ; b = b*a ; return a + b.… |
| `T10-C5-085` | TH10 | CĐ5 | 138 | Câu hỏi | Giả sử hàm f(x,y) được định nghĩa như sau: >>> def f(x,y): a = 2*(x + y) ; print(a + n). Kết… |
| `T10-C5-086` | TH10 | CĐ5 | 138 | Thực hành, Nhiệm vụ 1 | Viết hàm với đầu vào là danh sách A chứa các số và số thực x. Hàm trả lại một danh sách kết… |
| `T10-C5-087` | TH10 | CĐ5 | 138 | Thực hành, Nhiệm vụ 2 | Viết hàm với đầu vào là xâu kí tự Str và số c, đầu ra là danh sách các từ được tách ra từ xâu… |
| `T10-C5-088` | TH10 | CĐ5 | 139 | Thực hành, Nhiệm vụ 3 | Viết chương trình yêu cầu thực hiện lần lượt các việc sau, mỗi việc cần được thực hiện bởi… |
| `T10-C5-089` | TH10 | CĐ5 | 140 | Luyện tập 1 | Viết hàm với đầu vào, đầu ra như sau: đầu vào là danh sách sList, các phần tử là xâu kí tự;… |
| `T10-C5-090` | TH10 | CĐ5 | 140 | Luyện tập 2 | Viết hàm Tach_day() với đầu vào là danh sách A, đầu ra là hai danh sách B, C được mô tả như… |
| `T10-C5-091` | TH10 | CĐ5 | 140 | Vận dụng 1 | Viết hàm có hai tham số đầu vào là m, n. Đầu ra trả lại hai giá trị là: ƯCLN của m, n; bội… |
| `T10-C5-092` | TH10 | CĐ5 | 140 | Vận dụng 2 | Viết chương trình nhập ba số tự nhiên từ bàn phím day, month, year, các số cách nhau bởi dấu… |
| `T10-C5-093` | TH10 | CĐ5 | 142 | Câu hỏi 2 | Bài toán yêu cầu sắp xếp dãy số ban đầu thành dãy tăng dần. Giả sử dãy số ban đầu là [3, 1,… |
| `T10-C5-094` | TH10 | CĐ5 | 143 | Thực hành, Nhiệm vụ 1 | Viết chương trình nhập các số nguyên m, n từ bàn phím, cách nhau bởi dấu cách. Chương trình… |
| `T10-C5-095` | TH10 | CĐ5 | 144 | Vận dụng 1 | Giả sử em được yêu cầu viết một chương trình nhập số tự nhiên n từ bàn phím, kết quả đưa ra… |
| `T10-C5-096` | TH10 | CĐ5 | 146 | Ví dụ minh hoạ | Nhập từ bàn phím hai số tự nhiên m, n, tính ƯCLN của hai số này. (Sách minh hoạ với m = 20, n… |
| `T10-C5-097` | TH10 | CĐ5 | 148 | Vận dụng 1 | Chương trình sau có chức năng sắp xếp một dãy số cho trước. Hãy kiểm tra xem chương trình có… |
| `T10-C5-098` | TH10 | CĐ5 | 149 | Nhiệm vụ 1 | Viết chương trình nhập từ bàn phím số tự nhiên n, kiểm tra n có phải là số nguyên tố hay… |
| `T10-C5-099` | TH10 | CĐ5 | 150 | Nhiệm vụ 2 | Viết chương trình nhập từ bàn phím ba số thực a, b, c và tìm nghiệm của phương trình bậc hai… |
| `T10-C5-100` | TH10 | CĐ5 | 152 | Luyện tập 2 | Viết chương trình in bảng cửu chương ra màn hình như sau: hàng thứ nhất in ra bảng nhân 1, 2,… |
| `T10-C5-101` | TH10 | CĐ5 | 152 | Vận dụng 1 | Viết chương trình nhập hai số tự nhiên Y1, Y2 là số năm, Y2 > Y1. Tính xem trong khoảng thời… |
| `T10-C5-102` | TH10 | CĐ5 | 152 | Vận dụng 2 | Gọi ƯCLN(a, b) là hàm ƯCLN của hai số tự nhiên a, b. Dễ thấy ta có ƯCLN(a, b) = ƯCLN(b, a%b)… |
| `T10-C5-103` | TH10 | CĐ5 | 153 | Nhiệm vụ 1 | Viết chương trình nhập họ tên đầy đủ từ bàn phím, ví dụ "Nguyễn Thị Mai Hương", sau đó tách… |
| `T10-C5-104` | TH10 | CĐ5 | 153 | Nhiệm vụ 2 | Trọng lượng của em trên các hành tinh khác. Chương trình yêu cầu nhập trọng lượng của em… |
| `T10-C5-105` | TH10 | CĐ5 | 154 | Nhiệm vụ 3 | Kiểm tra tính hợp lệ của ba tham số ngày, tháng, năm. Chương trình sẽ yêu cầu nhập ba số tự… |
| `T10-C5-106` | TH10 | CĐ5 | 155 | Luyện tập | Viết chương trình nhập số n, sau đó nhập danh sách tên học sinh với họ, đệm, tên. Sắp xếp tên… |
| `T10-C5-107` | TH10 | CĐ5 | 155 | Vận dụng 1 | Trong các phần mềm bảng tính điện tử, dữ liệu ngày tháng được coi là số ngày tính từ ngày… |
| `T10-C5-108` | TH10 | CĐ5 | 155 | Vận dụng 2 | Mở rộng bài tập trong phần luyện tập như sau: việc sắp xếp thứ tự phải ưu tiên tính theo tên… |
| `T10-C5-109` | TH10 | CĐ5 | 155 | Vận dụng 3 | Nếu n là hợp số thì dễ thấy n phải có ước số nguyên tố nhỏ hơn hoặc bằng căn bậc hai của n.… |
| `T11CS-C6-001` | TH11-KHMT | CĐ6 | 82 | Câu hỏi 1 | Sử dụng hàm sum() tính tổng các số của một dãy, hãy viết câu lệnh tính giá trị trung bình của… |
| `T11CS-C6-002` | TH11-KHMT | CĐ6 | 83 | Câu hỏi 2 | Thiết lập mảng bao gồm dãy các thông tin là danh sách học sinh và thông tin 3 điểm thi của… |
| `T11CS-C6-003` | TH11-KHMT | CĐ6 | 85 | Luyện tập 1 | Giả sử số đo chiều cao các bạn trong lớp được cho trong dãy số A. Hãy viết đoạn chương trình… |
| `T11CS-C6-004` | TH11-KHMT | CĐ6 | 85 | Luyện tập 2 | Viết chương trình nhập từ bàn phím số tự nhiên m, sau đó lần lượt nhập m dòng, mỗi dòng bao… |
| `T11CS-C6-005` | TH11-KHMT | CĐ6 | 85 | Vận dụng 1 | Viết hàm số UnitMatrix(n) với n là số tự nhiên cho trước, hàm trả lại giá trị là ma trận bậc… |
| `T11CS-C6-006` | TH11-KHMT | CĐ6 | 85 | Vận dụng 2 | Viết chương trình cho phép người dùng nhập từ bàn phím một dãy số tự nhiên, hãy đếm với mỗi… |
| `T11CS-C6-007` | TH11-KHMT | CĐ6 | 85 | Vận dụng 3 | Em ghi số tiền điện gia đình em theo từng tháng vào một danh sách gồm 12 số. Mỗi năm lại ghi… |
| `T11CS-C6-008` | TH11-KHMT | CĐ6 | 86 | Nhiệm vụ 1 | Viết chương trình quản lí điểm kiểm tra một môn học của một học sinh trong một học kì. Chương… |
| `T11CS-C6-009` | TH11-KHMT | CĐ6 | 86 | Nhiệm vụ 2 | Viết chương trình quản lí điểm kiểm tra một môn học trong một học kì của tất cả học sinh… |
| `T11CS-C6-010` | TH11-KHMT | CĐ6 | 88 | Luyện tập 1 | Chỉnh sửa lại chương trình của Nhiệm vụ 1 để bổ sung chức năng: a) Thông báo điểm đầu tiên và… |
| `T11CS-C6-011` | TH11-KHMT | CĐ6 | 88 | Luyện tập 2 | Chỉnh sửa lại chương trình để người dùng có thể: a) Tra cứu các đầu điểm kiểm tra theo STT… |
| `T11CS-C6-012` | TH11-KHMT | CĐ6 | 88 | Vận dụng 1 | Viết chương trình nhập vào từ bàn phím danh sách tên (không gồm họ và đệm) học sinh cách nhau… |
| `T11CS-C6-013` | TH11-KHMT | CĐ6 | 88 | Vận dụng 2 | Viết chương trình nhập từ bàn phím số tự nhiên m và n. Sau đó lần lượt nhập m dòng, mỗi dòng… |
| `T11CS-C6-014` | TH11-KHMT | CĐ6 | 90 | Hoạt động 2 | Cho dãy số A = [1, 4, 7, 8, 3, 9, 10] và cần tìm kiếm phần tử có giá trị bằng 9. Hãy cho biết… |
| `T11CS-C6-015` | TH11-KHMT | CĐ6 | 91 | Câu hỏi 1 | Cho dãy A = [1, 91, 45, 23, 67, 9, 10, 47, 90, 46, 86]. Thuật toán tìm kiếm tuần tự cần thực… |
| `T11CS-C6-016` | TH11-KHMT | CĐ6 | 92 | Mục 3c — minh hoạ | Giả sử dãy số đã sắp xếp là A = [1, 3, 4, 7, 8, 9, 10]. Giá trị cần tìm là K = 9. Hãy cho… |
| `T11CS-C6-017` | TH11-KHMT | CĐ6 | 93 | Câu hỏi 1 | Cho dãy A = [0, 4, 9, 10, 12, 14, 17, 18, 20, 31, 34, 67]. Với thuật toán tìm kiếm tuần tự,… |
| `T11CS-C6-018` | TH11-KHMT | CĐ6 | 93 | Câu hỏi 2 | Cho dãy A = [0, 4, 9, 10, 12, 14, 17, 18, 20, 31, 34, 67]. Với thuật toán tìm kiếm nhị phân,… |
| `T11CS-C6-019` | TH11-KHMT | CĐ6 | 93 | Câu hỏi 3 | Thay vì lần lượt lật các thẻ từ đầu đến cuối, bạn Minh đã chơi như sau: đầu tiên Minh lật thẻ… |
| `T11CS-C6-020` | TH11-KHMT | CĐ6 | 93 | Luyện tập 1 | Em hãy chỉnh sửa thuật toán tìm kiếm tuần tự để tìm ra tất cả các phần tử trong dãy bằng giá… |
| `T11CS-C6-021` | TH11-KHMT | CĐ6 | 93 | Luyện tập 2 | Viết chương trình của thuật toán tìm kiếm nhị phân với dãy sắp xếp giảm dần. |
| `T11CS-C6-022` | TH11-KHMT | CĐ6 | 93 | Vận dụng 1 | Cho A là danh sách tên các học sinh trong lớp, viết chương trình tìm kiếm tuần tự để tìm ra… |
| `T11CS-C6-023` | TH11-KHMT | CĐ6 | 93 | Vận dụng 2 | Cho A là danh sách tên các học sinh trong lớp được sắp xếp theo thứ tự bảng chữ cái, viết… |
| `T11CS-C6-024` | TH11-KHMT | CĐ6 | 96 | Nhiệm vụ 2 | Viết chương trình tra cứu điểm thi theo tên các học sinh trong lớp. Chương trình cho phép… |
| `T11CS-C6-025` | TH11-KHMT | CĐ6 | 97 | Nhiệm vụ 3 | Viết chương trình kiểm tra điểm thi của các học sinh trong một lớp học. Điểm thi của các học… |
| `T11CS-C6-026` | TH11-KHMT | CĐ6 | 98 | Luyện tập | Chỉnh sửa lại chương trình của Nhiệm vụ 3 để cho phép chương trình có thể tìm kiếm điểm số… |
| `T11CS-C6-027` | TH11-KHMT | CĐ6 | 98 | Vận dụng | Viết chương trình tra cứu tên theo điểm thi của học sinh trong lớp. Chương trình cho phép… |
| `T11CS-C6-028` | TH11-KHMT | CĐ6 | 99 | Hoạt động 1 | Cho dãy A = [5, 3, 9, 7, 2]. Hãy cho biết dãy thu được sau khi thực hiện thuật toán sắp xếp… |
| `T11CS-C6-029` | TH11-KHMT | CĐ6 | 100 | Câu hỏi 1 | Mô phỏng chi tiết các bước lặp sắp xếp chèn dãy A = [5, 0, 4, 2, 3]. |
| `T11CS-C6-030` | TH11-KHMT | CĐ6 | 100 | Hoạt động 2 | Xét dãy A = [5, 3, 9, 7, 2]. Quan sát sơ đồ mô phỏng các bước thực hiện thuật toán sắp xếp… |
| `T11CS-C6-031` | TH11-KHMT | CĐ6 | 102 | Câu hỏi 1 | Thực hiện mô phỏng sắp xếp theo thuật toán sắp xếp chọn dãy số: 4, 5, 2, 1, 3. |
| `T11CS-C6-032` | TH11-KHMT | CĐ6 | 103 | Câu hỏi 1 | Mô tả các bước thuật toán sắp xếp nổi bọt của dãy A = [4, 3, 1, 2]. |
| `T11CS-C6-033` | TH11-KHMT | CĐ6 | 103 | Luyện tập 1 | Cho dãy A = [5, 8, 1, 0, 10, 4, 3]. Viết các chương trình sắp xếp dãy A theo thứ tự tăng dần… |
| `T11CS-C6-034` | TH11-KHMT | CĐ6 | 103 | Luyện tập 2 | Viết chương trình nhập một dãy số từ bàn phím, các số cách nhau bởi dấu cách, thực hiện sắp… |
| `T11CS-C6-035` | TH11-KHMT | CĐ6 | 103 | Vận dụng 1 | Viết lại các thuật toán sắp xếp trong bài theo thứ tự giảm dần. |
| `T11CS-C6-036` | TH11-KHMT | CĐ6 | 104 | Nhiệm vụ 1 | Cho danh sách số lượng mỗi mặt hàng trong kho của một cửa hàng. Người quản lí kho cần xem các… |
| `T11CS-C6-037` | TH11-KHMT | CĐ6 | 105 | Nhiệm vụ 2 | Cho danh sách điểm trung bình môn Tin học của các học sinh. Em hãy sử dụng thuật toán sắp xếp… |
| `T11CS-C6-038` | TH11-KHMT | CĐ6 | 105 | Luyện tập 1 | Sử dụng thuật toán sắp xếp chọn viết lại chương trình trong Nhiệm vụ 1. |
| `T11CS-C6-039` | TH11-KHMT | CĐ6 | 105 | Luyện tập 2 | Sử dụng thuật toán sắp xếp nổi bọt viết lại chương trình trong Nhiệm vụ 2. |
| `T11CS-C6-040` | TH11-KHMT | CĐ6 | 105 | Vận dụng | Một người đi mua hàng với danh sách các mặt hàng cần mua, đơn giá từng mặt hàng và số lượng… |
| `T11CS-C6-041` | TH11-KHMT | CĐ6 | 108 | Câu hỏi 1 | Chương trình sau giải bài toán: yêu cầu nhập số tự nhiên n và tính tổng 1 + 2 + ... + n.… |
| `T11CS-C6-042` | TH11-KHMT | CĐ6 | 108 | Câu hỏi 2 | Chương trình sau giải bài toán đếm số các ước số thực sự của số tự nhiên n. Chương trình trên… |
| `T11CS-C6-043` | TH11-KHMT | CĐ6 | 110 | Luyện tập 2 | Xét hàm mô tả thuật toán tính tổng các số chẵn của một dãy số cho trước. Tìm hai bộ dữ liệu… |
| `T11CS-C6-044` | TH11-KHMT | CĐ6 | 110 | Vận dụng 1 | Cho dãy các số A = [3, 1, 0, 10, 13, 16, 9, 7, 5, 11]. a) Viết chương trình mô tả thuật toán… |
| `T11CS-C6-045` | TH11-KHMT | CĐ6 | 110 | Vận dụng 2 | Viết ba chương trình mô phỏng các thuật toán sắp xếp chèn, sắp xếp chọn và sắp xếp nổi bọt mà… |
| `T11CS-C6-046` | TH11-KHMT | CĐ6 | 111 | Khởi động | Quan sát và ước lượng thời gian thực hiện các đoạn chương trình 1 và 2 trong Hình 24.2.… |
| `T11CS-C6-047` | TH11-KHMT | CĐ6 | 113 | Câu hỏi 1 | Các lệnh và đoạn chương trình sau cần chạy trong bao nhiêu đơn vị thời gian? (a) n = 1000000… |
| `T11CS-C6-048` | TH11-KHMT | CĐ6 | 117 | Luyện tập 2 | Cho biết hàm sau sẽ trả về giá trị là bao nhiêu? def Mystery(n): r = 0 ; for i in range(n-1):… |
| `T11CS-C6-049` | TH11-KHMT | CĐ6 | 117 | Vận dụng 1 | Giả sử rằng mỗi phép tính đơn được thực hiện trong micro giây (1 µs = một phần triệu giây).… |
| `T11CS-C6-050` | TH11-KHMT | CĐ6 | 118 | Bài toán gốc | Cho trước dãy số A: A[0], A[1], ..., A[n-1]. Cần tiến hành sắp xếp dãy trên theo thứ tự tăng… |
| `T11CS-C6-051` | TH11-KHMT | CĐ6 | 120 | Bài toán (Hoạt động 2) | Cho trước dãy số A: A[0], A[1], ..., A[n-1]. Cặp phần tử A[i], A[j] được gọi là nghịch đảo… |
| `T11CS-C6-052` | TH11-KHMT | CĐ6 | 122 | Luyện tập 2 | Sử dụng thiết kế của Bài toán 2, tìm tất cả các cặp nghịch đảo của dãy: 3, 2, 1, 5, 4. |
| `T11CS-C6-053` | TH11-KHMT | CĐ6 | 122 | Vận dụng 1 | Sử dụng phương pháp làm mịn dần để giải bài toán sau: cho trước số tự nhiên không âm n, viết… |
| `T11CS-C6-054` | TH11-KHMT | CĐ6 | 123 | Nhiệm vụ 1 | Cho trước một dãy n số, các số được kí hiệu A[0], A[1], ..., A[n-1]. Cần thiết kế chương… |
| `T11CS-C6-055` | TH11-KHMT | CĐ6 | 125 | Nhiệm vụ 2 | Cho trước dãy số A[0], A[1], ..., A[n-1]. Cần tính được mỗi giá trị của các phần tử của dãy… |
| `T11CS-C6-056` | TH11-KHMT | CĐ6 | 126 | Luyện tập 1 | Thiết kế thuật toán cho nhiệm vụ 1 với ý tưởng khác như sau: dãy A là một hoán vị của dãy các… |
| `T11CS-C6-057` | TH11-KHMT | CĐ6 | 126 | Vận dụng 1 | Cho dãy số A = A[0], A[1], ..., A[n-1]. Thiết kế và viết chương trình kiểm tra trong dãy A có… |
| `T11CS-C6-058` | TH11-KHMT | CĐ6 | 126 | Vận dụng 2 | Xâu kí tự được gọi là đối xứng nếu thay đổi thứ tự ngược lại các kí tự của xâu thì vẫn nhận… |
| `T11CS-C6-059` | TH11-KHMT | CĐ6 | 127 | Bài toán mở đầu | Em được giao việc quản lí cho cửa hàng bán thực phẩm của gia đình. Hằng ngày, em phải nhập… |
| `T11CS-C6-060` | TH11-KHMT | CĐ6 | 131 | Luyện tập 2 | Viết thêm một chương trình cho công việc bổ sung 4 như sau: cần in ra danh sách 1/3 số mặt… |
| `T11CS-C6-061` | TH11-KHMT | CĐ6 | 131 | Vận dụng 1 | Thiết lập chương trình cho công việc thường làm vào cuối giờ bán hàng: cho trước số K (một… |
| `T11CS-C6-062` | TH11-KHMT | CĐ6 | 131 | Vận dụng 2 | Một công ty du lịch có n địa điểm tham quan được đánh số theo thứ tự 0, 1, 2, ..., n-1. Công… |
| `T11CS-C6-063` | TH11-KHMT | CĐ6 | 132 | Nhiệm vụ | Tính điểm tổng hợp của vận động viên. Điểm tổng hợp của mỗi vận động viên là trung bình cộng… |
| `T11CS-C6-064` | TH11-KHMT | CĐ6 | 136 | Luyện tập 1 | Hãy chỉnh sửa lại chương trình trên nếu bổ sung thêm điều kiện sau vào nhiệm vụ: trong tệp… |
| `T11CS-C6-065` | TH11-KHMT | CĐ6 | 136 | Vận dụng 1 | Cho trước số tự nhiên n, cần in ra trên màn hình dãy n số nguyên tố đầu tiên. Ví dụ nếu n = 5… |
| `T11CS-C6-066` | TH11-KHMT | CĐ6 | 136 | Vận dụng 2 | Trong một kì thi Tin học trẻ, mỗi học sinh sẽ phải làm 3 bài thi. Với mỗi bài, nếu học sinh… |
| `T11CS-C6-067` | TH11-KHMT | CĐ6 | 142 | Câu hỏi 1 | Đoạn chương trình sau thực hiện công việc gì? from LinkedList import * ; L = LL() ;… |
| `T11CS-C6-068` | TH11-KHMT | CĐ6 | 142 | Câu hỏi 2 | Viết đoạn chương trình ngắn sử dụng thư viện LinkedList để thiết lập một danh sách liên kết L… |
| `T11CS-C6-069` | TH11-KHMT | CĐ6 | 142 | Vận dụng 1 | Cho trước một danh sách liên kết L. Viết một hàm đếm số lượng phần tử của danh sách liên kết… |
| `T11CS-C6-070` | TH11-KHMT | CĐ6 | 142 | Vận dụng 2 | Viết hàm delete_last(L) có chức năng xoá phần tử cuối cùng của danh sách liên kết L. |
| `T11CS-C6-071` | TH11-KHMT | CĐ6 | 143 | Nhiệm vụ 1 | Viết thư viện hinh_tron gồm hai hàm để tính chu vi và diện tích của hình tròn với tham số của… |
| `T11CS-C6-072` | TH11-KHMT | CĐ6 | 144 | Nhiệm vụ 2 | Tạo thư viện cong_thuc_ly gồm hai hàm machSongSong(dsDienTro) và machNoiTiep(dsDienTro) để… |
| `T11CS-C6-073` | TH11-KHMT | CĐ6 | 144 | Nhiệm vụ 3 | Em hãy định nghĩa hàm tinhNtkTB(dsNtk, dstyLe) trong file cong_thuc_hoa.py để tính nguyên tử… |
| `T11CS-C6-074` | TH11-KHMT | CĐ6 | 145 | Vận dụng 1 | Tạo thư viện phuong_trinh gồm hàm phuongTrinhBac2(a, b, c) với a, b, c là các hệ số của… |
| `T11CS-C6-075` | TH11-KHMT | CĐ6 | 145 | Vận dụng 2 | Viết chương trình quản lí các bài hát trong một đĩa CD hay một play list, sử dụng cấu trúc… |
