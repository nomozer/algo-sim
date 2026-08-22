# EXTERNAL SELECTION POOL — chọn 40 ID từ bảng dưới

> Bảng này dành cho **GVHD/người thứ ba**. Quyền chọn 40 case thuộc về bạn.
> Development agent chỉ lọc theo các guard đã đóng băng và trình bày.

Bảng **cố ý không hiển thị**: checker support · IR support · dự đoán thành công
· chi tiết cài đặt · kết quả pilot. Chọn dựa trên **nội dung bài và nguồn**, chứ
không dựa trên phỏng đoán hệ làm được gì.

## Quy mô

| | |
|---|---|
| Source universe V2 | 189 record |
| **Đủ điều kiện (pool)** | **89** |
| Bị loại bởi guard | 100 |

Cần chọn **40** trong 89 — dư khoảng 2.2×.

## Guard đã áp (chỉ hai, đều đã đóng băng từ trước)

1. **Trùng INTERNAL LIVE PILOT** — loại theo provenance (sách + trang + nhãn
   bài), đọc thẳng từ `pilot/sealed-pilot-34a10a9c/cases.json`. Tập pilot đã bị
   chạy bốn lượt nên tính held-out của nó bằng không.

2. **`no_specialized_module`** — loại bài thuộc dạng hệ **đã có module chuyên
   biệt**. Bảng mẫu dẫn xuất từ **tên 24 target trong `CATALOG`**, không từ hành
   vi hay kết quả chạy. Đây là guard chống **nhiễm dữ liệu**: benchmark phải đo
   lớp bài hệ chưa có module dựng sẵn.

`expressible_in_ir` **không** được dùng để lọc — nó chỉ là metadata mô tả. Bài
thoả rubric mà IR hiện tại có thể chịu thua vẫn ở trong pool; nếu được chọn và
hệ chịu thua thì đó là `capability_gap`, một kết quả nghiên cứu hợp lệ.

Danh sách bị loại kèm **lý do từng case**: `EXTERNAL_SELECTION_POOL_EXCLUDED.json`.

## Fingerprint

```
34d11adc5084047f92b290ac906fc6177c8aa3d23b9b0323dd8b325d48d50808
```

SHA-256 của `EXTERNAL_SELECTION_POOL.json`. Selection chỉ được thực hiện **sau**
khi fingerprint này đã đóng băng.

Cách chọn: `EXTERNAL_SELECTION_INSTRUCTIONS.md`.

## Bảng chọn

| ID | SGK | Lớp | Chủ đề | Trang | Số bài/vị trí | Mô tả nhận diện ngắn |
|---|---|---|---|---|---|---|
| `T10-C5-001` | TH10 | 10 | Chủ đề 5 | 89 | Câu hỏi 1 | Kết quả của mỗi lệnh sau là gì? Kết quả đó có kiểu dữ liệu nào? >>> 5/2 ; >>> 12 + 1.5 ; >>> "Bạn… |
| `T10-C5-002` | TH10 | 10 | Chủ đề 5 | 89 | Câu hỏi 2 | Lệnh sau sẽ in ra kết quả gì? >>> print("13 + 10*3/2 - 3*2 = ", 13 + 10*3/2 - 3*2) |
| `T10-C5-003` | TH10 | 10 | Chủ đề 5 | 90 | Luyện tập 1 | Hãy viết lệnh để tính giá trị các biểu thức sau trong chế độ gõ lệnh trực tiếp của Python: a) 10 +… |
| `T10-C5-004` | TH10 | 10 | Chủ đề 5 | 90 | Vận dụng 2 | Viết chương trình Python in ra màn hình bảng nhân trong phạm vi 10. |
| `T10-C5-005` | TH10 | 10 | Chủ đề 5 | 93 | Câu hỏi 2 | Sau các lệnh dưới đây, các biến x, y nhận giá trị bao nhiêu? >>> x = 10 ; >>> y = x**2 - 1 ; >>> x… |
| `T10-C5-006` | TH10 | 10 | Chủ đề 5 | 93 | Câu hỏi 3 | a, b nhận giá trị gì sau các lệnh sau? >>> a,b = 2,3 ; >>> a,b = a+b, a-b |
| `T10-C5-007` | TH10 | 10 | Chủ đề 5 | 94 | Câu hỏi 1 | Mỗi lệnh sau là đúng hay sai? Nếu đúng thì cho kết quả là bao nhiêu? >>> (12 - 10//2)**2 - 1 ; >>>… |
| `T10-C5-008` | TH10 | 10 | Chủ đề 5 | 94 | Câu hỏi 2 | Mỗi lệnh sau cho kết quả là xâu kí tự như thế nào? >>> ""*20 + "010" ; >>> "10"+"0"*5 |
| `T10-C5-009` | TH10 | 10 | Chủ đề 5 | 95 | Thực hành, Nhiệm vụ 1 | Thực hiện các phép tính sau trong môi trường lập trình Python, so sánh kết quả với việc tính biểu… |
| `T10-C5-010` | TH10 | 10 | Chủ đề 5 | 96 | Thực hành, Nhiệm vụ 2 | Gán giá trị cho biến R là bán kính hình tròn rồi viết chương trình tính và in kết quả theo mẫu:… |
| `T10-C5-011` | TH10 | 10 | Chủ đề 5 | 96 | Luyện tập 2 | Lệnh sau sẽ in ra kết quả gì? >>> print("đồ rê mi "*3 + "pha son la si đô "*2) |
| `T10-C5-012` | TH10 | 10 | Chủ đề 5 | 96 | Vận dụng 1 | Viết các lệnh để thực hiện việc đổi số giây ss cho trước sang số ngày, giờ, phút, giây, in kết quả… |
| `T10-C5-013` | TH10 | 10 | Chủ đề 5 | 96 | Vận dụng 2 | Hãy cho biết trước và sau khi thực hiện các lệnh sau, giá trị các biến x, y là bao nhiêu. Em có… |
| `T10-C5-014` | TH10 | 10 | Chủ đề 5 | 98 | Câu hỏi | Xác định kiểu và giá trị của các biểu thức sau: a) "15 + 20 - 7"; b) 32 > 45; c) 13 != 8 + 5; d) 1… |
| `T10-C5-015` | TH10 | 10 | Chủ đề 5 | 99 | Câu hỏi 1 | Mỗi lệnh sau sẽ trả lại các giá trị nào? a) str(150); b) int("1110"); c) float("15.0"). |
| `T10-C5-017` | TH10 | 10 | Chủ đề 5 | 100 | Vận dụng 1 | Viết chương trình nhập giá trị ss là số giây từ bàn phím. Thông báo ra màn hình thời gian ss giây… |
| `T10-C5-018` | TH10 | 10 | Chủ đề 5 | 100 | Vận dụng 2 | Viết chương trình nhập ba số thực dương a, b, c và tính chu vi, diện tích của tam giác có độ dài… |
| `T10-C5-019` | TH10 | 10 | Chủ đề 5 | 102 | Câu hỏi | Mỗi biểu thức sau có giá trị True hay False? a) 100%4 == 0; b) 111//5 != 20 or 20%3 != 0. |
| `T10-C5-020` | TH10 | 10 | Chủ đề 5 | 103 | Thực hành, Nhiệm vụ 1 | Viết chương trình nhập số tự nhiên n từ bàn phím. Sau đó thông báo số em đã nhập là số chẵn hay số… |
| `T10-C5-022` | TH10 | 10 | Chủ đề 5 | 104 | Luyện tập 2 | Tìm một vài giá trị m, n thoả mãn các biểu thức sau: a) 100%m == 0 and n%5 != 0; b) m%100 == 0 and… |
| `T10-C5-024` | TH10 | 10 | Chủ đề 5 | 104 | Vận dụng 2 | Năm n là năm nhuận nếu giá trị n thoả mãn điều kiện: n chia hết cho 400 hoặc n chia hết cho 4 đồng… |
| `T10-C5-025` | TH10 | 10 | Chủ đề 5 | 105 | Hoạt động 1 | Thực hiện đoạn chương trình sau trong chế độ gõ lệnh trực tiếp của Python để tính tổng 0 + 1 + ...… |
| `T10-C5-026` | TH10 | 10 | Chủ đề 5 | 106 | Câu hỏi | Với giá trị n cho trước, so sánh giá trị S trong đoạn chương trình sau với tổng 1 + 2 + ... + n. S… |
| `T10-C5-027` | TH10 | 10 | Chủ đề 5 | 107 | Thực hành, Nhiệm vụ 1 | Nhập số tự nhiên n từ bàn phím và in ra màn hình dãy các ước số của n theo chiều ngang màn hình.… |
| `T10-C5-029` | TH10 | 10 | Chủ đề 5 | 107 | Luyện tập 1 | Đoạn chương trình sau in ra kết quả gì? n = int(input("Nhập số tự nhiên n:")) ; S = 0 ; for k in… |
| `T10-C5-030` | TH10 | 10 | Chủ đề 5 | 107 | Luyện tập 2 | Viết đoạn chương trình tính tích 1 × 2 × 3 × ... × n với n được nhập vào từ bàn phím. |
| `T10-C5-031` | TH10 | 10 | Chủ đề 5 | 107 | Vận dụng 1 | Viết chương trình nhập từ bàn phím số tự nhiên n và in ra kết quả S = 1 + 1/2 + ... + 1/n. |
| `T10-C5-032` | TH10 | 10 | Chủ đề 5 | 107 | Vận dụng 2 | Viết chương trình nhập từ bàn phím số tự nhiên n và in ra kết quả là tổng sau: S = 1³ + 2³ + ... +… |
| `T10-C5-033` | TH10 | 10 | Chủ đề 5 | 109 | Câu hỏi 2 | Viết đoạn chương trình tính tổng 2 + 4 + ... + 100 sử dụng lệnh while. |
| `T10-C5-037` | TH10 | 10 | Chủ đề 5 | 110 | Vận dụng | Viết chương trình in các số tự nhiên từ 1 đến 100 ra màn hình thành 10 hàng, mỗi hàng 10 số, có… |
| `T10-C5-038` | TH10 | 10 | Chủ đề 5 | 112 | Câu hỏi 1 | Cho danh sách A = [1, 0, "One", 9, 15, "Two", True, False]. Hãy cho biết giá trị các phần tử: a)… |
| `T10-C5-039` | TH10 | 10 | Chủ đề 5 | 113 | Câu hỏi 2 | Cho dãy các số nguyên A, viết chương trình in ra các số chẵn của A. |
| `T10-C5-040` | TH10 | 10 | Chủ đề 5 | 113 | Câu hỏi 2 (mục 3) | Danh sách A sẽ như thế nào sau các lệnh sau? >>> A = [2,4,10,1,0] ; >>> A.append(100) ; >>> del A[1] |
| `T10-C5-043` | TH10 | 10 | Chủ đề 5 | 116 | Câu hỏi 1 | Giả sử A = ["0","1","01","10"]. Các biểu thức sau trả về giá trị đúng hay sai? a) 1 in A; b) "01"… |
| `T10-C5-044` | TH10 | 10 | Chủ đề 5 | 117 | Câu hỏi 2 | Danh sách A trước và sau lệnh insert() là [1,4,10,0] và [1,4,10,5,0]. Lệnh đã dùng là gì? |
| `T10-C5-045` | TH10 | 10 | Chủ đề 5 | 117 | Thực hành, Nhiệm vụ 1 | Nhập số n từ bàn phím, sau đó nhập danh sách n tên học sinh trong lớp và in ra danh sách các tên… |
| `T10-C5-046` | TH10 | 10 | Chủ đề 5 | 117 | Thực hành, Nhiệm vụ 2 | Cho trước dãy số A. Viết chương trình xoá đi các phần tử có giá trị nhỏ hơn 0 từ A. (Chương trình… |
| `T10-C5-047` | TH10 | 10 | Chủ đề 5 | 118 | Thực hành, Nhiệm vụ 3 | Cho trước dãy số A. Viết chương trình tìm và chỉ ra vị trí đầu tiên của dãy số A mà ba số hạng… |
| `T10-C5-052` | TH10 | 10 | Chủ đề 5 | 120 | Câu hỏi 2 | Mỗi xâu hợp lệ ở Câu 1 có độ dài bằng bao nhiêu? (Câu 1: a) "123&*()+-ABC"; b) "1010110&0101001";… |
| `T10-C5-053` | TH10 | 10 | Chủ đề 5 | 121 | Câu hỏi 1 | Sau khi thực hiện các lệnh sau, biến skq sẽ có giá trị bao nhiêu? >>> s = "81723" ; >>> skq = "" ;… |
| `T10-C5-055` | TH10 | 10 | Chủ đề 5 | 121 | Thực hành, Nhiệm vụ 2 | Nhập một xâu kí tự S từ bàn phím rồi kiểm tra xem xâu S có chứa xâu con "10" không. |
| `T10-C5-060` | TH10 | 10 | Chủ đề 5 | 123 | Khởi động | Cho xâu c = "Trường Sơn" và xâu m = "Bước chân trên dải Trường Sơn". Em hãy cho biết xâu c có là… |
| `T10-C5-062` | TH10 | 10 | Chủ đề 5 | 124 | Câu hỏi 2 | Lệnh sau trả lại giá trị gì? >>> "abababab".find("ab",4) |
| `T10-C5-063` | TH10 | 10 | Chủ đề 5 | 125 | Câu hỏi | Cho xâu kí tự: "gà,vịt,chó,lợn,ngựa,cá". Em hãy trình bày cách làm để xoá các dấu "," và thay thế… |
| `T10-C5-064` | TH10 | 10 | Chủ đề 5 | 125 | Thực hành, Nhiệm vụ 1 | Viết chương trình nhập nhiều số nguyên từ bàn phím, các số cách nhau bởi dấu cách. Khi nhập xong… |
| `T10-C5-065` | TH10 | 10 | Chủ đề 5 | 126 | Thực hành, Nhiệm vụ 2 | Viết chương trình nhập một xâu kí tự có thể có nhiều dấu cách giữa các từ. Sau đó chỉnh sửa xâu kí… |
| `T10-C5-066` | TH10 | 10 | Chủ đề 5 | 126 | Thực hành, Nhiệm vụ 3 | Viết chương trình nhập số tự nhiên n, rồi nhập họ tên của n học sinh. Sau đó in ra danh sách tên… |
| `T10-C5-071` | TH10 | 10 | Chủ đề 5 | 129 | Thực hành, Nhiệm vụ 2 | Viết hàm prime(n) với tham số là số tự nhiên n và trả lại True nếu n là số nguyên tố, trả lại… |
| `T10-C5-072` | TH10 | 10 | Chủ đề 5 | 130 | Luyện tập 1 | Viết hàm với tham số là số tự nhiên n in ra các số là ước nguyên tố của n. |
| `T10-C5-074` | TH10 | 10 | Chủ đề 5 | 130 | Vận dụng 2 | Viết chương trình yêu cầu nhập từ bàn phím một xâu kí tự, sau đó thông báo: tổng số các kí tự là… |
| `T10-C5-076` | TH10 | 10 | Chủ đề 5 | 133 | Câu hỏi 1 | Sử dụng hàm prime, em hãy viết chương trình in ra các số nguyên tố trong khoảng từ m đến n, với m,… |
| `T10-C5-079` | TH10 | 10 | Chủ đề 5 | 134 | Thực hành, Nhiệm vụ 3 | Thiết lập hàm merge_str(s1,s2) với s1, s2 là hai xâu cần gộp. Hàm này sẽ gộp hai xâu s1, s2 theo… |
| `T10-C5-080` | TH10 | 10 | Chủ đề 5 | 135 | Luyện tập 1 | Thiết lập hàm power(a,b,c) với a, b, c là số nguyên. Hàm trả lại giá trị (a+b) mũ c. |
| `T10-C5-084` | TH10 | 10 | Chủ đề 5 | 137 | Câu hỏi 1 | Giả sử có các lệnh sau: >>> a,b = 1,2 ; >>> def f(a,b): a = a + b ; b = b*a ; return a + b. Giá… |
| `T10-C5-085` | TH10 | 10 | Chủ đề 5 | 138 | Câu hỏi | Giả sử hàm f(x,y) được định nghĩa như sau: >>> def f(x,y): a = 2*(x + y) ; print(a + n). Kết quả… |
| `T10-C5-086` | TH10 | 10 | Chủ đề 5 | 138 | Thực hành, Nhiệm vụ 1 | Viết hàm với đầu vào là danh sách A chứa các số và số thực x. Hàm trả lại một danh sách kết quả B… |
| `T10-C5-087` | TH10 | 10 | Chủ đề 5 | 138 | Thực hành, Nhiệm vụ 2 | Viết hàm với đầu vào là xâu kí tự Str và số c, đầu ra là danh sách các từ được tách ra từ xâu Str… |
| `T10-C5-088` | TH10 | 10 | Chủ đề 5 | 139 | Thực hành, Nhiệm vụ 3 | Viết chương trình yêu cầu thực hiện lần lượt các việc sau, mỗi việc cần được thực hiện bởi một… |
| `T10-C5-089` | TH10 | 10 | Chủ đề 5 | 140 | Luyện tập 1 | Viết hàm với đầu vào, đầu ra như sau: đầu vào là danh sách sList, các phần tử là xâu kí tự; đầu ra… |
| `T10-C5-090` | TH10 | 10 | Chủ đề 5 | 140 | Luyện tập 2 | Viết hàm Tach_day() với đầu vào là danh sách A, đầu ra là hai danh sách B, C được mô tả như sau:… |
| `T10-C5-092` | TH10 | 10 | Chủ đề 5 | 140 | Vận dụng 2 | Viết chương trình nhập ba số tự nhiên từ bàn phím day, month, year, các số cách nhau bởi dấu cách.… |
| `T10-C5-094` | TH10 | 10 | Chủ đề 5 | 143 | Thực hành, Nhiệm vụ 1 | Viết chương trình nhập các số nguyên m, n từ bàn phím, cách nhau bởi dấu cách. Chương trình đưa ra… |
| `T10-C5-099` | TH10 | 10 | Chủ đề 5 | 150 | Nhiệm vụ 2 | Viết chương trình nhập từ bàn phím ba số thực a, b, c và tìm nghiệm của phương trình bậc hai ax² +… |
| `T10-C5-100` | TH10 | 10 | Chủ đề 5 | 152 | Luyện tập 2 | Viết chương trình in bảng cửu chương ra màn hình như sau: hàng thứ nhất in ra bảng nhân 1, 2, 3,… |
| `T10-C5-103` | TH10 | 10 | Chủ đề 5 | 153 | Nhiệm vụ 1 | Viết chương trình nhập họ tên đầy đủ từ bàn phím, ví dụ "Nguyễn Thị Mai Hương", sau đó tách riêng… |
| `T10-C5-104` | TH10 | 10 | Chủ đề 5 | 153 | Nhiệm vụ 2 | Trọng lượng của em trên các hành tinh khác. Chương trình yêu cầu nhập trọng lượng của em (tính… |
| `T10-C5-105` | TH10 | 10 | Chủ đề 5 | 154 | Nhiệm vụ 3 | Kiểm tra tính hợp lệ của ba tham số ngày, tháng, năm. Chương trình sẽ yêu cầu nhập ba số tự nhiên:… |
| `T11CS-C6-010` | TH11-KHMT | 11 | Chủ đề 6 | 88 | Luyện tập 1 | Chỉnh sửa lại chương trình của Nhiệm vụ 1 để bổ sung chức năng: a) Thông báo điểm đầu tiên và điểm… |
| `T11CS-C6-011` | TH11-KHMT | 11 | Chủ đề 6 | 88 | Luyện tập 2 | Chỉnh sửa lại chương trình để người dùng có thể: a) Tra cứu các đầu điểm kiểm tra theo STT (số thứ… |
| `T11CS-C6-024` | TH11-KHMT | 11 | Chủ đề 6 | 96 | Nhiệm vụ 2 | Viết chương trình tra cứu điểm thi theo tên các học sinh trong lớp. Chương trình cho phép người… |
| `T11CS-C6-027` | TH11-KHMT | 11 | Chủ đề 6 | 98 | Vận dụng | Viết chương trình tra cứu tên theo điểm thi của học sinh trong lớp. Chương trình cho phép người… |
| `T11CS-C6-041` | TH11-KHMT | 11 | Chủ đề 6 | 108 | Câu hỏi 1 | Chương trình sau giải bài toán: yêu cầu nhập số tự nhiên n và tính tổng 1 + 2 + ... + n. Chương… |
| `T11CS-C6-046` | TH11-KHMT | 11 | Chủ đề 6 | 111 | Khởi động | Quan sát và ước lượng thời gian thực hiện các đoạn chương trình 1 và 2 trong Hình 24.2. Chương… |
| `T11CS-C6-047` | TH11-KHMT | 11 | Chủ đề 6 | 113 | Câu hỏi 1 | Các lệnh và đoạn chương trình sau cần chạy trong bao nhiêu đơn vị thời gian? (a) n = 1000000 ; for… |
| `T11CS-C6-053` | TH11-KHMT | 11 | Chủ đề 6 | 122 | Vận dụng 1 | Sử dụng phương pháp làm mịn dần để giải bài toán sau: cho trước số tự nhiên không âm n, viết… |
| `T11CS-C6-054` | TH11-KHMT | 11 | Chủ đề 6 | 123 | Nhiệm vụ 1 | Cho trước một dãy n số, các số được kí hiệu A[0], A[1], ..., A[n-1]. Cần thiết kế chương trình… |
| `T11CS-C6-055` | TH11-KHMT | 11 | Chủ đề 6 | 125 | Nhiệm vụ 2 | Cho trước dãy số A[0], A[1], ..., A[n-1]. Cần tính được mỗi giá trị của các phần tử của dãy trên… |
| `T11CS-C6-056` | TH11-KHMT | 11 | Chủ đề 6 | 126 | Luyện tập 1 | Thiết kế thuật toán cho nhiệm vụ 1 với ý tưởng khác như sau: dãy A là một hoán vị của dãy các số… |
| `T11CS-C6-057` | TH11-KHMT | 11 | Chủ đề 6 | 126 | Vận dụng 1 | Cho dãy số A = A[0], A[1], ..., A[n-1]. Thiết kế và viết chương trình kiểm tra trong dãy A có hai… |
| `T11CS-C6-058` | TH11-KHMT | 11 | Chủ đề 6 | 126 | Vận dụng 2 | Xâu kí tự được gọi là đối xứng nếu thay đổi thứ tự ngược lại các kí tự của xâu thì vẫn nhận được… |
| `T11CS-C6-067` | TH11-KHMT | 11 | Chủ đề 6 | 142 | Câu hỏi 1 | Đoạn chương trình sau thực hiện công việc gì? from LinkedList import * ; L = LL() ; insert(L,10) ;… |
| `T11CS-C6-068` | TH11-KHMT | 11 | Chủ đề 6 | 142 | Câu hỏi 2 | Viết đoạn chương trình ngắn sử dụng thư viện LinkedList để thiết lập một danh sách liên kết L và… |
| `T11CS-C6-070` | TH11-KHMT | 11 | Chủ đề 6 | 142 | Vận dụng 2 | Viết hàm delete_last(L) có chức năng xoá phần tử cuối cùng của danh sách liên kết L. |
| `T11CS-C6-071` | TH11-KHMT | 11 | Chủ đề 6 | 143 | Nhiệm vụ 1 | Viết thư viện hinh_tron gồm hai hàm để tính chu vi và diện tích của hình tròn với tham số của hàm… |
| `T11CS-C6-074` | TH11-KHMT | 11 | Chủ đề 6 | 145 | Vận dụng 1 | Tạo thư viện phuong_trinh gồm hàm phuongTrinhBac2(a, b, c) với a, b, c là các hệ số của phương… |
| `T11CS-C6-075` | TH11-KHMT | 11 | Chủ đề 6 | 145 | Vận dụng 2 | Viết chương trình quản lí các bài hát trong một đĩa CD hay một play list, sử dụng cấu trúc… |
| `T11ICT-001` | TH11-ICT | 11 | Chủ đề 7 | 121 | Luyện tập 1 | Cho ảnh số có số điểm ảnh là 3000 × 2000 điểm ảnh. Tính kích thước ảnh với mỗi độ phân giải: a) 72… |
| `T11ICT-002` | TH11-ICT | 11 | Chủ đề 7 | 121 | Luyện tập 2 | Nếu in một ảnh ở độ phân giải 300 dpi thì thu được ảnh in có kích thước 10 × 10 inch. Để ảnh in có… |
| `T11ICT-003` | TH11-ICT | 11 | Chủ đề 7 | 136 | Luyện tập 2 | Một tệp ảnh mở trong GIMP có 5 lớp ảnh. Nếu dùng hiệu ứng Blend với số khung hình trung gian là 5… |
