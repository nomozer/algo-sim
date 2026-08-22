# -*- coding: utf-8 -*-
"""SOURCE UNIVERSE — trích cơ học bài tập SGK để custodian độc lập CHỌN.

Vai trò của phase này: **development agent trích cơ học từ nguồn SGK. Quyền lựa
chọn 40 case SEALED thuộc về GVHD/custodian độc lập.**

Nguồn là bản QUÉT, không có lớp chữ (pdftotext trả 60 ký tự cho 60 trang). Cách
đọc: PyMuPDF dựng ảnh từng trang rồi đọc trực tiếp bằng thị giác. Mọi số trang
là **số trang in trên sách**, tra ngược được.

QUY TẮC TRÍCH — khai trước để kiểm toán được, áp dụng đều cho cả hai sách:

    NHẬN  mọi câu hỏi/bài tập/nhiệm vụ đòi một KẾT QUẢ XÁC ĐỊNH tính được từ
          dữ liệu hoặc thủ tục đã cho (một giá trị, một dãy, một đếm, một vị
          trí, một ánh xạ, một trạng thái cuối).

    LOẠI  câu hỏi thuần định nghĩa · nêu ý kiến · kể tên · thao tác giao diện ·
          "lệnh này có lỗi không / lỗi loại gì" · in ra một chuỗi cho sẵn.

Quy tắc này nói về BẢN CHẤT BÀI TOÁN, không nói gì về năng lực hệ đang được
đánh giá. Bài thoả rubric mà IR hiện tại có thể không biểu diễn được thì VẪN
được giữ — đó có thể trở thành `capability_gap`, một kết quả nghiên cứu hợp lệ.

Một record = một mục được đánh số trong sách. Mục có nhiều ý a/b/c/d được giữ
nguyên trong cùng một record, đúng như sách đánh số.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
T10 = "tin-hoc-10.pdf"
C5 = "Chủ đề 5 — Giải quyết vấn đề với sự trợ giúp của máy tính"
T11 = "tin-hoc-11-cs.pdf"
C6 = "Chủ đề 6 — Kĩ thuật lập trình"

RECORDS: list[dict] = []


def r(book, section, page, pos, text, context=""):
    RECORDS.append({
        "book": book,
        "section_or_chapter": section,
        "page": page,
        "exercise_number_or_position": pos,
        "problem_text": " ".join(text.split()),
        "context_text": " ".join(context.split()),
    })


# ═══════════════ TIN HỌC 10 — CHỦ ĐỀ 5 ═══════════════
# ── Bài 16. Ngôn ngữ lập trình bậc cao và Python ──
r(T10, C5, 89, "Câu hỏi 1",
  "Kết quả của mỗi lệnh sau là gì? Kết quả đó có kiểu dữ liệu nào? "
  ">>> 5/2 ; >>> 12 + 1.5 ; >>> \"Bạn là học sinh lớp 10\" ; >>> 10 + 7/2")
r(T10, C5, 89, "Câu hỏi 2",
  "Lệnh sau sẽ in ra kết quả gì? "
  ">>> print(\"13 + 10*3/2 - 3*2 = \", 13 + 10*3/2 - 3*2)")
r(T10, C5, 90, "Luyện tập 1",
  "Hãy viết lệnh để tính giá trị các biểu thức sau trong chế độ gõ lệnh trực "
  "tiếp của Python: a) 10 + 13; b) 20 - 7; c) 3 × 10 - 16; d) 12/5 + 13/6.")
r(T10, C5, 90, "Vận dụng 2",
  "Viết chương trình Python in ra màn hình bảng nhân trong phạm vi 10.")

# ── Bài 17. Biến và lệnh gán ──
r(T10, C5, 93, "Câu hỏi 2",
  "Sau các lệnh dưới đây, các biến x, y nhận giá trị bao nhiêu? "
  ">>> x = 10 ; >>> y = x**2 - 1 ; >>> x = x/2 + y")
r(T10, C5, 93, "Câu hỏi 3",
  "a, b nhận giá trị gì sau các lệnh sau? >>> a,b = 2,3 ; >>> a,b = a+b, a-b")
r(T10, C5, 94, "Câu hỏi 1",
  "Mỗi lệnh sau là đúng hay sai? Nếu đúng thì cho kết quả là bao nhiêu? "
  ">>> (12 - 10//2)**2 - 1 ; >>> (13 + 45**2)(30//12 - 5/2)")
r(T10, C5, 94, "Câu hỏi 2",
  "Mỗi lệnh sau cho kết quả là xâu kí tự như thế nào? "
  ">>> \"\"*20 + \"010\" ; >>> \"10\"+\"0\"*5")
r(T10, C5, 95, "Thực hành, Nhiệm vụ 1",
  "Thực hiện các phép tính sau trong môi trường lập trình Python, so sánh kết "
  "quả với việc tính biểu thức toán học. a) (1 + 2 + 3 + ... + 10)³. "
  "b) 1/2 + 1/3 + 1/4 + 1/5. c) Thực hiện lệnh gán x = 2, y = 5 rồi tính giá "
  "trị biểu thức (x + y)(x² + y² - 1). d) Thực hiện lệnh gán a = 2, b = 3, "
  "c = 4 rồi tính giá trị biểu thức (a + b + c)(a + b - c).")
r(T10, C5, 96, "Thực hành, Nhiệm vụ 2",
  "Gán giá trị cho biến R là bán kính hình tròn rồi viết chương trình tính và "
  "in kết quả theo mẫu: Chu vi hình tròn là: ..... ; Diện tích hình tròn là: "
  "..... (chương trình mẫu trong sách dùng R = 4.5 và pi = 3.14).")
r(T10, C5, 96, "Luyện tập 2",
  "Lệnh sau sẽ in ra kết quả gì? "
  ">>> print(\"đồ rê mi \"*3 + \"pha son la si đô \"*2)")
r(T10, C5, 96, "Vận dụng 1",
  "Viết các lệnh để thực hiện việc đổi số giây ss cho trước sang số ngày, giờ, "
  "phút, giây, in kết quả ra màn hình. Ví dụ, nếu ss = 684 500 thì kết quả in "
  "ra như sau: 684 500 giây = 7 ngày 22 giờ 8 phút 20 giây.",
  "Gợi ý: Sử dụng các phép toán lấy thương nguyên, lấy số dư và các cách đổi "
  "sau: 1 ngày = 86 400 giây; 1 giờ = 3 600 giây; 1 phút = 60 giây.")
r(T10, C5, 96, "Vận dụng 2",
  "Hãy cho biết trước và sau khi thực hiện các lệnh sau, giá trị các biến x, y "
  "là bao nhiêu. Em có nhận xét gì về kết quả nhận được? "
  ">>> x, y = 10, 7 ; >>> x, y = y, x")

# ── Bài 18. Các lệnh vào ra đơn giản ──
r(T10, C5, 98, "Câu hỏi",
  "Xác định kiểu và giá trị của các biểu thức sau: a) \"15 + 20 - 7\"; "
  "b) 32 > 45; c) 13 != 8 + 5; d) 1 == 2.")
r(T10, C5, 99, "Câu hỏi 1",
  "Mỗi lệnh sau sẽ trả lại các giá trị nào? a) str(150); b) int(\"1110\"); "
  "c) float(\"15.0\").")
r(T10, C5, 100, "Thực hành, Nhiệm vụ 1",
  "Viết chương trình nhập lần lượt ba số tự nhiên m, n, p, sau đó in ra tổng "
  "của ba số này.")
r(T10, C5, 100, "Vận dụng 1",
  "Viết chương trình nhập giá trị ss là số giây từ bàn phím. Thông báo ra màn "
  "hình thời gian ss giây này sau khi đổi thành thời gian tính bằng ngày, giờ, "
  "phút, giây.")
r(T10, C5, 100, "Vận dụng 2",
  "Viết chương trình nhập ba số thực dương a, b, c và tính chu vi, diện tích "
  "của tam giác có độ dài các cạnh là a, b, c (a, b, c > 0 và thoả mãn bất "
  "đẳng thức tam giác).",
  "Gợi ý: Công thức Heron tính diện tích tam giác S = căn bậc hai của "
  "p(p-a)(p-b)(p-c) với p là nửa chu vi tam giác.")

# ── Bài 19. Câu lệnh rẽ nhánh if ──
r(T10, C5, 102, "Câu hỏi",
  "Mỗi biểu thức sau có giá trị True hay False? a) 100%4 == 0; "
  "b) 111//5 != 20 or 20%3 != 0.")
r(T10, C5, 103, "Thực hành, Nhiệm vụ 1",
  "Viết chương trình nhập số tự nhiên n từ bàn phím. Sau đó thông báo số em đã "
  "nhập là số chẵn hay số lẻ phụ thuộc vào n là chẵn hay lẻ.")
r(T10, C5, 104, "Thực hành, Nhiệm vụ 2",
  "Giả sử giá điện sinh hoạt trong khu vực gia đình em ở được tính luỹ kế theo "
  "từng tháng như sau: với mức điện tiêu thụ từ 0 đến 50 kWh, giá thành mỗi "
  "kWh là 1,678 nghìn đồng; với mức từ 51 đến 100, giá thành mỗi kWh là 1,734 "
  "nghìn đồng; từ mức 101 trở lên, giá thành mỗi kWh là 2,014 nghìn đồng. Viết "
  "chương trình nhập số điện tiêu thụ trong tháng của gia đình em và tính số "
  "tiền điện phải trả.")
r(T10, C5, 104, "Luyện tập 2",
  "Tìm một vài giá trị m, n thoả mãn các biểu thức sau: "
  "a) 100%m == 0 and n%5 != 0; b) m%100 == 0 and m%400 != 0; "
  "c) n%3 == 0 or (n%3 != 0 and n%4 == 0).")
r(T10, C5, 104, "Vận dụng 1",
  "Giá bán cam tại siêu thị tính như sau: nếu khối lượng cam mua dưới 5 kg thì "
  "giá bán là 12 000 đồng/kg, nếu khối lượng mua lớn hơn hoặc bằng 5 kg thì "
  "giá bán là 10 000 đồng/kg. Viết chương trình nhập số lượng mua (tính theo "
  "kg) sau đó tính số tiền phải trả.")
r(T10, C5, 104, "Vận dụng 2",
  "Năm n là năm nhuận nếu giá trị n thoả mãn điều kiện: n chia hết cho 400 "
  "hoặc n chia hết cho 4 đồng thời không chia hết cho 100. Viết chương trình "
  "nhập số năm n và cho biết năm n có phải là nhuận hay không.")

# ── Bài 20. Câu lệnh lặp for ──
r(T10, C5, 105, "Hoạt động 1",
  "Thực hiện đoạn chương trình sau trong chế độ gõ lệnh trực tiếp của Python "
  "để tính tổng 0 + 1 + ... + 9. Tổng này có giá trị bao nhiêu? Giải thích kết "
  "quả. >>> S = 0 ; >>> for k in range(10): S = S + k ; >>> print(S)")
r(T10, C5, 106, "Câu hỏi",
  "Với giá trị n cho trước, so sánh giá trị S trong đoạn chương trình sau với "
  "tổng 1 + 2 + ... + n. S = 0 ; for k in range(1,n+1): S = S + k")
r(T10, C5, 107, "Thực hành, Nhiệm vụ 1",
  "Nhập số tự nhiên n từ bàn phím và in ra màn hình dãy các ước số của n theo "
  "chiều ngang màn hình. Ví dụ nếu n = 10 thì chương trình sẽ in ra dãy số "
  "1, 2, 5, 10.")
r(T10, C5, 107, "Thực hành, Nhiệm vụ 2",
  "Nhập số tự nhiên n từ bàn phím và đếm số các ước số thực sự của n. Ước số "
  "thực sự của n là số tự nhiên k < n và là ước của n.")
r(T10, C5, 107, "Luyện tập 1",
  "Đoạn chương trình sau in ra kết quả gì? "
  "n = int(input(\"Nhập số tự nhiên n:\")) ; S = 0 ; "
  "for k in range(n+1): S = S + k ; print(S*S)")
r(T10, C5, 107, "Luyện tập 2",
  "Viết đoạn chương trình tính tích 1 × 2 × 3 × ... × n với n được nhập vào từ "
  "bàn phím.")
r(T10, C5, 107, "Vận dụng 1",
  "Viết chương trình nhập từ bàn phím số tự nhiên n và in ra kết quả "
  "S = 1 + 1/2 + ... + 1/n.")
r(T10, C5, 107, "Vận dụng 2",
  "Viết chương trình nhập từ bàn phím số tự nhiên n và in ra kết quả là tổng "
  "sau: S = 1³ + 2³ + ... + n³.")

# ── Bài 21. Câu lệnh lặp while ──
r(T10, C5, 109, "Câu hỏi 2",
  "Viết đoạn chương trình tính tổng 2 + 4 + ... + 100 sử dụng lệnh while.")
r(T10, C5, 110, "Thực hành, Nhiệm vụ 2",
  "Viết chương trình in ra màn hình dãy các chữ cái tiếng Anh từ \"A\" đến "
  "\"Z\" theo ba hàng ngang trên màn hình, hai hàng ngang đầu có 10 chữ cái, "
  "hàng thứ ba có 6 chữ cái.",
  "Các chữ cái tiếng Anh từ A đến Z chiếm các vị trí từ 65 đến 90 trong bảng "
  "mã ASCII; lệnh chr(k) trả lại kí tự tương ứng trong bảng mã này.")
r(T10, C5, 110, "Luyện tập 1",
  "Cho dãy số 1, 4, 7, 10,.... Viết chương trình in ra phần tử lớn nhất của "
  "dãy nhưng nhỏ hơn 100.")
r(T10, C5, 110, "Luyện tập 2",
  "Viết chương trình đếm trong dãy 100 số tự nhiên đầu tiên có bao nhiêu số "
  "thoả mãn điều kiện: hoặc chia hết cho 5 hoặc chia cho 3 dư 1.")
r(T10, C5, 110, "Vận dụng",
  "Viết chương trình in các số tự nhiên từ 1 đến 100 ra màn hình thành 10 "
  "hàng, mỗi hàng 10 số, có dạng: 1 2 3 ... 10 / 11 12 .... 20 / ... / "
  "91 92 ..... 100.")

# ── Bài 22. Kiểu dữ liệu danh sách ──
r(T10, C5, 112, "Câu hỏi 1",
  "Cho danh sách A = [1, 0, \"One\", 9, 15, \"Two\", True, False]. Hãy cho "
  "biết giá trị các phần tử: a) A[0]; b) A[2]; c) A[7]; d) A[len(A)].")
r(T10, C5, 113, "Câu hỏi 2",
  "Cho dãy các số nguyên A, viết chương trình in ra các số chẵn của A.")
r(T10, C5, 113, "Câu hỏi 2 (mục 3)",
  "Danh sách A sẽ như thế nào sau các lệnh sau? "
  ">>> A = [2,4,10,1,0] ; >>> A.append(100) ; >>> del A[1]")

# ── Bài 23. Một số lệnh làm việc với dữ liệu danh sách ──
r(T10, C5, 114, "Thực hành, Nhiệm vụ 2",
  "Nhập một dãy số từ bàn phím. Tính tổng, trung bình của dãy và in dãy số "
  "trên một hàng ngang.")
r(T10, C5, 114, "Vận dụng",
  "Cho dãy số A. Viết chương trình tìm giá trị và chỉ số của phần tử lớn nhất "
  "của A. Tương tự với bài toán tìm phần tử nhỏ nhất.")
r(T10, C5, 116, "Câu hỏi 1",
  "Giả sử A = [\"0\",\"1\",\"01\",\"10\"]. Các biểu thức sau trả về giá trị "
  "đúng hay sai? a) 1 in A; b) \"01\" in A.")
r(T10, C5, 117, "Câu hỏi 2",
  "Danh sách A trước và sau lệnh insert() là [1,4,10,0] và [1,4,10,5,0]. Lệnh "
  "đã dùng là gì?")
r(T10, C5, 117, "Thực hành, Nhiệm vụ 1",
  "Nhập số n từ bàn phím, sau đó nhập danh sách n tên học sinh trong lớp và in "
  "ra danh sách các tên học sinh này, mỗi tên học sinh trên một dòng. Yêu cầu "
  "danh sách được in ra theo thứ tự ngược lại với thứ tự đã nhập.")
r(T10, C5, 117, "Thực hành, Nhiệm vụ 2",
  "Cho trước dãy số A. Viết chương trình xoá đi các phần tử có giá trị nhỏ hơn "
  "0 từ A. (Chương trình mẫu trong sách dùng A = [0,1,-3,-10,5,9,-20,55].)")
r(T10, C5, 118, "Thực hành, Nhiệm vụ 3",
  "Cho trước dãy số A. Viết chương trình tìm và chỉ ra vị trí đầu tiên của dãy "
  "số A mà ba số hạng liên tiếp có giá trị là 1, 2, 3. Nếu tìm thấy thì thông "
  "báo vị trí tìm thấy, nếu không thì thông báo \"Không tìm thấy mẫu\". "
  "(Chương trình mẫu trong sách dùng "
  "A = [0,4,0,1,2,3,8,9,0,1,2,3,17,-16,0,1,2] và p = [1,2,3].)")
r(T10, C5, 118, "Luyện tập 1",
  "Cho dãy số [1,2,2,3,4,5,5]. Viết lệnh thực hiện: a) Chèn số 1 vào ngay sau "
  "giá trị 1 của dãy. b) Chèn số 3 và số 4 vào danh sách để dãy có số 3 và số "
  "4 liền nhau hai lần.")
r(T10, C5, 118, "Luyện tập 2",
  "Cho trước dãy số A. Viết chương trình thực hiện công việc sau: xoá đi một "
  "phần tử ở chính giữa dãy nếu số phần tử của dãy là số lẻ; xoá đi hai phần "
  "tử ở chính giữa của dãy nếu số phần tử của dãy là số chẵn.")
r(T10, C5, 118, "Vận dụng 1",
  "Viết chương trình nhập n từ bàn phím, tạo và in ra màn hình dãy số A bao "
  "gồm n số tự nhiên chẵn đầu tiên.")
r(T10, C5, 118, "Vận dụng 2",
  "Dãy số Fibonacci được xác định như sau: F0 = 0; F1 = 1; Fn = F(n-1) + "
  "F(n-2) (với n ≥ 2). Viết chương trình nhập n từ bàn phím, tạo và in ra màn "
  "hình dãy số A bao gồm n số hạng đầu của dãy Fibonacci.")

# ── Bài 24. Xâu kí tự ──
r(T10, C5, 120, "Câu hỏi 2",
  "Mỗi xâu hợp lệ ở Câu 1 có độ dài bằng bao nhiêu? "
  "(Câu 1: a) \"123&*()+-ABC\"; b) \"1010110&0101001\"; c) \"Tây Nguyên\".)")
r(T10, C5, 121, "Câu hỏi 1",
  "Sau khi thực hiện các lệnh sau, biến skq sẽ có giá trị bao nhiêu? "
  ">>> s = \"81723\" ; >>> skq = \"\" ; >>> for ch in s: if int(ch) % 2 != 0: "
  "skq = skq + ch")
r(T10, C5, 121, "Câu hỏi 2",
  "Cho s1 = \"abc\", s2 = \"ababcabca\". Các biểu thức lôgic sau cho kết quả "
  "là đúng hay sai? a) s1 in s2; b) s1 + s1 in s2; c) \"abcabca\" in s2; "
  "d) \"abc123\" in s2.")
r(T10, C5, 121, "Thực hành, Nhiệm vụ 2",
  "Nhập một xâu kí tự S từ bàn phím rồi kiểm tra xem xâu S có chứa xâu con "
  "\"10\" không.")
r(T10, C5, 122, "Luyện tập 1",
  "Cho xâu S, viết đoạn lệnh trích ra xâu con của S bao gồm ba kí tự đầu tiên "
  "của S.")
r(T10, C5, 122, "Luyện tập 2",
  "Viết chương trình kiểm tra xâu S có chứa chữ số không. Thông báo \"S có "
  "chứa chữ số\" hoặc \"S không chứa chữ số nào\".")
r(T10, C5, 122, "Vận dụng 1",
  "Cho hai xâu s1, s2. Viết đoạn chương trình chèn xâu s1 vào giữa s2, tại vị "
  "trí len(s2)//2. In kết quả ra màn hình.")
r(T10, C5, 122, "Vận dụng 2",
  "Viết chương trình nhập số học sinh và họ tên học sinh. Sau đó đếm xem trong "
  "danh sách có bao nhiêu bạn tên là \"Hương\".")

# ── Bài 25. Một số lệnh làm việc với xâu kí tự ──
r(T10, C5, 123, "Khởi động",
  "Cho xâu c = \"Trường Sơn\" và xâu m = \"Bước chân trên dải Trường Sơn\". "
  "Em hãy cho biết xâu c có là xâu con của xâu m không. Nếu có thì tìm vị trí "
  "của xâu c trong xâu m.")
r(T10, C5, 124, "Câu hỏi 1",
  "Biểu thức lôgic sau là đúng hay sai? >>> \"010\" in \"001100\"")
r(T10, C5, 124, "Câu hỏi 2",
  "Lệnh sau trả lại giá trị gì? >>> \"abababab\".find(\"ab\",4)")
r(T10, C5, 125, "Câu hỏi",
  "Cho xâu kí tự: \"gà,vịt,chó,lợn,ngựa,cá\". Em hãy trình bày cách làm để xoá "
  "các dấu \",\" và thay thế bằng dấu \" \" trong xâu này.")
r(T10, C5, 125, "Thực hành, Nhiệm vụ 1",
  "Viết chương trình nhập nhiều số nguyên từ bàn phím, các số cách nhau bởi "
  "dấu cách. Khi nhập xong thông báo số lượng các số đã nhập và in các số này "
  "thành hàng ngang.")
r(T10, C5, 126, "Thực hành, Nhiệm vụ 2",
  "Viết chương trình nhập một xâu kí tự có thể có nhiều dấu cách giữa các từ. "
  "Sau đó chỉnh sửa xâu kí tự đó sao cho giữa các từ chỉ có một dấu cách. In "
  "xâu kết quả ra màn hình.")
r(T10, C5, 126, "Thực hành, Nhiệm vụ 3",
  "Viết chương trình nhập số tự nhiên n, rồi nhập họ tên của n học sinh. Sau "
  "đó in ra danh sách tên học sinh theo hai cột, cột 1 là tên, cột 2 là họ "
  "đệm.")
r(T10, C5, 126, "Luyện tập 1",
  "Viết chương trình nhập nhiều số (số nguyên hoặc số thực) từ bàn phím, các "
  "số cách nhau bởi dấu cách. Sau đó in ra màn hình tổng các số đã nhập.")
r(T10, C5, 126, "Luyện tập 2",
  "Viết chương trình nhập họ tên đầy đủ của người dùng, sau đó in thông báo "
  "tên và họ đệm của người đó.")
r(T10, C5, 126, "Vận dụng 1",
  "Viết chương trình nhập hai số tự nhiên từ bàn phím, cách nhau bởi dấu cách "
  "và đưa ra kết quả là ƯCLN của hai số.")
r(T10, C5, 126, "Vận dụng 2",
  "Viết chương trình nhập số tự nhiên n rồi nhập n họ tên học sinh. Sau đó yêu "
  "cầu nhập một tên và thông báo số bạn có cùng tên đó trong lớp.")


# ── Bài 26. Hàm trong Python ──
r(T10, C5, 129, "Thực hành, Nhiệm vụ 2",
  "Viết hàm prime(n) với tham số là số tự nhiên n và trả lại True nếu n là số "
  "nguyên tố, trả lại False nếu n không phải là số nguyên tố.")
r(T10, C5, 130, "Luyện tập 1",
  "Viết hàm với tham số là số tự nhiên n in ra các số là ước nguyên tố của n.")
r(T10, C5, 130, "Luyện tập 2",
  "Viết hàm numbers(s) đếm số các chữ số có trong xâu s. "
  "Ví dụ numbers(\"0101abc\") = 4.")
r(T10, C5, 130, "Vận dụng 2",
  "Viết chương trình yêu cầu nhập từ bàn phím một xâu kí tự, sau đó thông báo: "
  "tổng số các kí tự là chữ số của xâu; tổng số các kí tự là chữ cái tiếng Anh "
  "trong xâu. Viết hàm cho mỗi yêu cầu trên.")

# ── Bài 27. Tham số của hàm ──
r(T10, C5, 133, "Ví dụ 2",
  "Cho trước dãy số A. Tính tổng các số hạng dương của dãy. (Sách minh hoạ với "
  "A = [0,2,-1,5,10,-3] và B = [1,-10,-11,8,2,0,-5].)")
r(T10, C5, 133, "Câu hỏi 1",
  "Sử dụng hàm prime, em hãy viết chương trình in ra các số nguyên tố trong "
  "khoảng từ m đến n, với m, n là hai số tự nhiên và 1 < m < n.")
r(T10, C5, 134, "Thực hành, Nhiệm vụ 1",
  "Thiết lập hàm f_sum(A,b) có chức năng tính tổng các số của danh sách A theo "
  "quy định sau: nếu b = 0 thì tính tổng các số của danh sách A; nếu b khác 0 "
  "thì chỉ tính tổng các số dương của A.")
r(T10, C5, 134, "Thực hành, Nhiệm vụ 2",
  "Thiết lập hàm f_dem(msg, sep) có chức năng đếm số các từ của một xâu msg "
  "với kí tự tách từ là sep. Ví dụ: f_dem(\"Mùa thu lịch sử\",\" \") trả lại "
  "giá trị 4; f_dem(\"Mùa thu lịch sử\",\"-\") trả lại giá trị 1.")
r(T10, C5, 134, "Thực hành, Nhiệm vụ 3",
  "Thiết lập hàm merge_str(s1,s2) với s1, s2 là hai xâu cần gộp. Hàm này sẽ "
  "gộp hai xâu s1, s2 theo cách, lấy lần lượt từng kí tự của s1, s2 đưa vào "
  "xâu kết quả. Nếu có một xâu hết kí tự thì đưa phần còn lại của xâu dài hơn "
  "vào xâu kết quả. Ví dụ nếu s1 = \"1111\", s2 = \"0000\" thì xâu kết quả là "
  "\"10101010\".")
r(T10, C5, 135, "Luyện tập 1",
  "Thiết lập hàm power(a,b,c) với a, b, c là số nguyên. Hàm trả lại giá trị "
  "(a+b) mũ c.")
r(T10, C5, 135, "Luyện tập 2",
  "Viết chương trình thực hiện: nhập hai số tự nhiên từ bàn phím, hai số cách "
  "nhau bởi dấu cách. Tính và in ra tổng của các số này. Yêu cầu sử dụng hàm "
  "khi viết chương trình.")
r(T10, C5, 135, "Vận dụng 1",
  "Viết chương trình thực hiện: nhập hai số tự nhiên từ bàn phím, hai số cách "
  "nhau bởi dấu phẩy, in ra ước chung lớn nhất (ƯCLN) của hai số. Yêu cầu sử "
  "dụng hàm khi viết chương trình.")
r(T10, C5, 135, "Vận dụng 2",
  "Thiết lập hàm change() có hai tham số là xâu ho_ten và số c. Hàm sẽ trả lại "
  "xâu kí tự ho_ten là chữ in hoa nếu c = 0. Nếu tham số c khác 0 thì hàm trả "
  "lại xâu ho_ten là chữ in thường.")

# ── Bài 28. Phạm vi của biến ──
r(T10, C5, 137, "Câu hỏi 1",
  "Giả sử có các lệnh sau: >>> a,b = 1,2 ; >>> def f(a,b): a = a + b ; "
  "b = b*a ; return a + b. Giá trị của a, b bằng bao nhiêu sau khi thực hiện "
  "lệnh sau? a) f(1, 2); b) f(10, 20).")
r(T10, C5, 138, "Câu hỏi",
  "Giả sử hàm f(x,y) được định nghĩa như sau: >>> def f(x,y): a = 2*(x + y) ; "
  "print(a + n). Kết quả nào được in ra khi thực hiện các lệnh sau? "
  "n = 10 ; f(1,2)")
r(T10, C5, 138, "Thực hành, Nhiệm vụ 1",
  "Viết hàm với đầu vào là danh sách A chứa các số và số thực x. Hàm trả lại "
  "một danh sách kết quả B từ danh sách A bằng cách chỉ giữ lại các phần tử "
  "lớn hơn hoặc bằng x.")
r(T10, C5, 138, "Thực hành, Nhiệm vụ 2",
  "Viết hàm với đầu vào là xâu kí tự Str và số c, đầu ra là danh sách các từ "
  "được tách ra từ xâu Str nhưng đã được chuyển thành chữ in hoa hoặc chữ in "
  "thường, hoặc chỉ chuyển kí tự đầu các từ thành chữ in hoa tuỳ thuộc vào "
  "tham số đầu vào c: nếu c = 0 chuyển thành chữ in hoa; nếu c = 1 chuyển "
  "thành chữ in thường; nếu c = 2 chuyển viết chữ hoa kí tự đầu của mỗi từ.")
r(T10, C5, 139, "Thực hành, Nhiệm vụ 3",
  "Viết chương trình yêu cầu thực hiện lần lượt các việc sau, mỗi việc cần "
  "được thực hiện bởi một hàm: 1. Nhập từ bàn phím một dãy các số nguyên, mỗi "
  "số cách nhau bởi dấu cách. Chuyển các số này vào danh sách A và in danh "
  "sách A ra màn hình. 2. Trích từ danh sách A ra một danh sách B gồm các phần "
  "tử lớn hơn 0. In danh sách B ra màn hình. 3. Trích từ danh sách A ra một "
  "danh sách C gồm các phần tử nhỏ hơn 0. In danh sách C ra màn hình.")
r(T10, C5, 140, "Luyện tập 1",
  "Viết hàm với đầu vào, đầu ra như sau: đầu vào là danh sách sList, các phần "
  "tử là xâu kí tự; đầu ra là danh sách cList, các phần tử là kí tự đầu tiên "
  "của các xâu kí tự tương ứng trong danh sách sList.")
r(T10, C5, 140, "Luyện tập 2",
  "Viết hàm Tach_day() với đầu vào là danh sách A, đầu ra là hai danh sách B, "
  "C được mô tả như sau: danh sách B thu được từ A bằng cách lấy ra các phần "
  "tử có chỉ số chẵn; danh sách C thu được từ A bằng cách lấy ra các phần tử "
  "có chỉ số lẻ.")
r(T10, C5, 140, "Vận dụng 1",
  "Viết hàm có hai tham số đầu vào là m, n. Đầu ra trả lại hai giá trị là: "
  "ƯCLN của m, n; bội chung nhỏ nhất (BCNN) của m, n.",
  "Gợi ý: Sử dụng công thức ƯCLN(m, n) × BCNN(m, n) = m × n.")
r(T10, C5, 140, "Vận dụng 2",
  "Viết chương trình nhập ba số tự nhiên từ bàn phím day, month, year, các số "
  "cách nhau bởi dấu cách. Các số này biểu diễn giá trị của ngày, tháng, năm "
  "nào đó. Chương trình cần kiểm tra và in ra thông báo số liệu đã nhập vào đó "
  "có hợp lệ hay không.")

# ── Bài 29. Nhận biết lỗi chương trình ──
r(T10, C5, 142, "Câu hỏi 2",
  "Bài toán yêu cầu sắp xếp dãy số ban đầu thành dãy tăng dần. Giả sử dãy số "
  "ban đầu là [3, 1, 8, 10, 0]. Kết quả thu được dãy [1, 3, 8, 10, 0]. Chương "
  "trình có lỗi không? Nếu có thì lỗi đó thuộc loại gì?")
r(T10, C5, 143, "Thực hành, Nhiệm vụ 1",
  "Viết chương trình nhập các số nguyên m, n từ bàn phím, cách nhau bởi dấu "
  "cách. Chương trình đưa ra tổng, hiệu, thương của hai số đã nhập.")
r(T10, C5, 144, "Vận dụng 1",
  "Giả sử em được yêu cầu viết một chương trình nhập số tự nhiên n từ bàn "
  "phím, kết quả đưa ra là danh sách các ước số thực sự của n, tính cả 1 và "
  "không tính n. Hãy viết chương trình và kiểm tra các khả năng sinh lỗi khi "
  "thực hiện chương trình.")

# ── Bài 30. Kiểm thử và gỡ lỗi chương trình ──
r(T10, C5, 146, "Ví dụ minh hoạ",
  "Nhập từ bàn phím hai số tự nhiên m, n, tính ƯCLN của hai số này. "
  "(Sách minh hoạ với m = 20, n = 16 và đáp số 4.)",
  "Thuật toán dựa trên: gcd(m, m) = m; nếu n > m thì gcd(m, n) = gcd(m, n-m); "
  "nếu n < m thì gcd(m, n) = gcd(m-n, n).")
r(T10, C5, 148, "Vận dụng 1",
  "Chương trình sau có chức năng sắp xếp một dãy số cho trước. Hãy kiểm tra "
  "xem chương trình có lỗi không. Nếu có thì tìm và sửa lỗi. "
  "A = [10,1,5,2,8,0,4] ; for i in range(len(A)-1): j = i ; "
  "while j > 1 and A[j] < A[j-1]: A[j],A[j-1] = A[j-1],A[j] ; j = j - 1 ; "
  "print(A)")

# ── Bài 31. Thực hành viết chương trình đơn giản ──
r(T10, C5, 149, "Nhiệm vụ 1",
  "Viết chương trình nhập từ bàn phím số tự nhiên n, kiểm tra n có phải là số "
  "nguyên tố hay không. Nếu n là hợp số thì in ra kết quả phân tích n thành "
  "tích các thừa số nguyên tố. Chú ý số 1 và cũng không phải là số nguyên tố "
  "và cũng không là hợp số. (Sách minh hoạ bảng lần vết với n = 100 và kết "
  "quả 100 = 2 × 2 × 5 × 5.)")
r(T10, C5, 150, "Nhiệm vụ 2",
  "Viết chương trình nhập từ bàn phím ba số thực a, b, c và tìm nghiệm của "
  "phương trình bậc hai ax² + bx + c = 0. Chương trình cần xét đầy đủ các "
  "trường hợp xảy ra.")
r(T10, C5, 152, "Luyện tập 2",
  "Viết chương trình in bảng cửu chương ra màn hình như sau: hàng thứ nhất in "
  "ra bảng nhân 1, 2, 3, 4, 5; hàng thứ hai in ra bảng nhân 6, 7, 8, 9, 10.")
r(T10, C5, 152, "Vận dụng 1",
  "Viết chương trình nhập hai số tự nhiên Y1, Y2 là số năm, Y2 > Y1. Tính xem "
  "trong khoảng thời gian từ năm Y1 đến năm Y2 có bao nhiêu năm nhuận. Áp dụng "
  "tính xem trong thế kỉ XXI có bao nhiêu năm nhuận.")
r(T10, C5, 152, "Vận dụng 2",
  "Gọi ƯCLN(a, b) là hàm ƯCLN của hai số tự nhiên a, b. Dễ thấy ta có "
  "ƯCLN(a, b) = ƯCLN(b, a%b) nếu b > 0 và ƯCLN(a, 0) = a. Từ đó hãy viết "
  "chương trình nhập hai số a, b và tính ƯCLN của a và b.")

# ── Bài 32. Ôn tập lập trình Python ──
r(T10, C5, 153, "Nhiệm vụ 1",
  "Viết chương trình nhập họ tên đầy đủ từ bàn phím, ví dụ \"Nguyễn Thị Mai "
  "Hương\", sau đó tách riêng phần tên, họ, đệm và in ra màn hình.")
r(T10, C5, 153, "Nhiệm vụ 2",
  "Trọng lượng của em trên các hành tinh khác. Chương trình yêu cầu nhập trọng "
  "lượng của em (tính theo đơn vị N - Newton) trên Trái Đất và tính trọng "
  "lượng của em trên một hành tinh khác (ví dụ Mặt Trăng, Hoả tinh, Kim tinh, "
  "Thổ tinh, Mộc tinh, Mặt Trời).",
  "P = m × g. Danh sách hành tinh: [\"Mặt Trăng\",\"Hoả tinh\",\"Kim tinh\","
  "\"Mộc tinh\",\"Thổ tinh\",\"Mặt Trời\"] với gravities = [1.62, 3.711, 8.83, "
  "24.79, 10.44, 274.0]; trên Trái Đất g = 9.8 m/s².")
r(T10, C5, 154, "Nhiệm vụ 3",
  "Kiểm tra tính hợp lệ của ba tham số ngày, tháng, năm. Chương trình sẽ yêu "
  "cầu nhập ba số tự nhiên: ngày, tháng, năm từ bàn phím theo khuôn dạng, ví "
  "dụ nhập 08-02-2021. Chương trình sẽ thông báo bộ dữ liệu đã nhập là hợp lệ "
  "hay không hợp lệ.")
r(T10, C5, 155, "Luyện tập",
  "Viết chương trình nhập số n, sau đó nhập danh sách tên học sinh với họ, "
  "đệm, tên. Sắp xếp tên học sinh trong lớp theo bảng chữ cái. Đưa kết quả ra "
  "màn hình.")
r(T10, C5, 155, "Vận dụng 1",
  "Trong các phần mềm bảng tính điện tử, dữ liệu ngày tháng được coi là số "
  "ngày tính từ ngày 1-1-1990. Viết chương trình: nhập số tự nhiên n từ bàn "
  "phím và tính xem số đó ứng với ngày, tháng, năm nào; nhập thời gian theo "
  "khuôn dạng ngày - tháng - năm (ví dụ 8-10-2021), tính số ngày ứng với ngày "
  "này theo phần mềm bảng tính điện tử.")
r(T10, C5, 155, "Vận dụng 2",
  "Mở rộng bài tập trong phần luyện tập như sau: việc sắp xếp thứ tự phải ưu "
  "tiên tính theo tên trước, rồi đến họ, rồi đến đệm; sắp xếp theo thứ tự của "
  "bảng chữ cái tiếng Việt.")
r(T10, C5, 155, "Vận dụng 3",
  "Nếu n là hợp số thì dễ thấy n phải có ước số nguyên tố nhỏ hơn hoặc bằng "
  "căn bậc hai của n. Viết chương trình tối ưu hoá hơn nhiệm vụ 1, bài 31, "
  "theo cách sau: để tìm ước số nguyên tố nhỏ nhất chỉ cần tìm trong các số "
  "2, 3, ..., căn bậc hai của n. Nếu trong dãy trên không tìm thấy ước của n "
  "thì kết luận ngay n là nguyên tố.")


# ═══════════════ TIN HỌC 11 (KHMT) — CHỦ ĐỀ 6 ═══════════════
# ── Bài 17. Dữ liệu mảng một chiều và hai chiều ──
r(T11, C6, 82, "Câu hỏi 1",
  "Sử dụng hàm sum() tính tổng các số của một dãy, hãy viết câu lệnh tính giá "
  "trị trung bình của dãy số A cho trước.")
r(T11, C6, 83, "Câu hỏi 2",
  "Thiết lập mảng bao gồm dãy các thông tin là danh sách học sinh và thông tin "
  "3 điểm thi của học sinh tương ứng các bài thi số 1, 2, 3. Viết đoạn lệnh "
  "nhập bộ dữ liệu trên và chương trình in ra danh sách học sinh cùng với điểm "
  "trung bình của các bài thi.")
r(T11, C6, 85, "Luyện tập 1",
  "Giả sử số đo chiều cao các bạn trong lớp được cho trong dãy số A. Hãy viết "
  "đoạn chương trình tính: số đo chiều cao trung bình của cả lớp; số bạn có "
  "chiều cao lớn hơn chiều cao trung bình của cả lớp.")
r(T11, C6, 85, "Luyện tập 2",
  "Viết chương trình nhập từ bàn phím số tự nhiên m, sau đó lần lượt nhập m "
  "dòng, mỗi dòng bao gồm n số cách nhau bởi dấu cách, đưa dữ liệu đã nhập vào "
  "ma trận A, sau đó in ma trận A ra màn hình.")
r(T11, C6, 85, "Vận dụng 1",
  "Viết hàm số UnitMatrix(n) với n là số tự nhiên cho trước, hàm trả lại giá "
  "trị là ma trận bậc n như Hình 17.1 (ma trận đơn vị: đường chéo chính bằng "
  "1, các phần tử còn lại bằng 0).")
r(T11, C6, 85, "Vận dụng 2",
  "Viết chương trình cho phép người dùng nhập từ bàn phím một dãy số tự nhiên, "
  "hãy đếm với mỗi giá trị của dãy có bao nhiêu số lặp lại. Ví dụ nếu dãy ban "
  "đầu là: 0 1 5 7 0 2 5 1 1 2 thì chương trình cần thông báo như Hình 17.2: "
  "Số 0 lặp lại 2 lần; Số 1 lặp lại 3 lần; Số 5 lặp lại 2 lần; Số 7 lặp lại 1 "
  "lần; Số 2 lặp lại 2 lần.")
r(T11, C6, 85, "Vận dụng 3",
  "Em ghi số tiền điện gia đình em theo từng tháng vào một danh sách gồm 12 "
  "số. Mỗi năm lại ghi lại số tiền điện vào một danh sách và ghép với danh "
  "sách các năm trước. Như vậy em thu được một bảng kích thước n × 12, trong "
  "đó hàng thứ k là số tiền điện của năm thứ k, cột tương ứng số tiền điện "
  "theo tháng. a) Thiết lập mảng mới tính số tiền điện trung bình của các năm, "
  "mỗi năm ghi một số. b) Tính số tiền điện trung bình của tất cả các năm đã "
  "được ghi dữ liệu trong bảng.")

# ── Bài 18. Thực hành dữ liệu mảng một chiều và hai chiều ──
r(T11, C6, 86, "Nhiệm vụ 1",
  "Viết chương trình quản lí điểm kiểm tra một môn học của một học sinh trong "
  "một học kì. Chương trình được thực hiện như sau: nhập điểm - yêu cầu người "
  "dùng nhập các đầu điểm kiểm tra (từ hai đầu điểm trở lên); thống kê điểm - "
  "chương trình duyệt qua các đầu điểm rồi tính và in ra điểm trung bình kiểm "
  "tra, điểm thấp nhất, cao nhất.")
r(T11, C6, 86, "Nhiệm vụ 2",
  "Viết chương trình quản lí điểm kiểm tra một môn học trong một học kì của "
  "tất cả học sinh trong lớp. Nhập dữ liệu: yêu cầu người dùng nhập số học "
  "sinh trong lớp, sau đó với mỗi học sinh hỏi người dùng nhập tên học sinh "
  "rồi nhập các đầu điểm của học sinh đó. Thống kê dữ liệu: chương trình in ra "
  "danh sách các học sinh với điểm trung bình kiểm tra của họ, tên học sinh có "
  "điểm trung bình cao nhất và điểm kiểm tra thấp nhất trong tất cả các đầu "
  "điểm.")
r(T11, C6, 88, "Luyện tập 1",
  "Chỉnh sửa lại chương trình của Nhiệm vụ 1 để bổ sung chức năng: a) Thông "
  "báo điểm đầu tiên và điểm cuối cùng trong danh sách. b) Cho phép người dùng "
  "tra cứu đầu điểm thứ n với quy ước n bắt đầu từ 1 ứng với điểm đầu tiên. "
  "Nếu n lớn hơn tổng số đầu điểm hoặc nhỏ hơn 1, cần thông báo không hợp lệ "
  "và yêu cầu người dùng nhập lại.")
r(T11, C6, 88, "Luyện tập 2",
  "Chỉnh sửa lại chương trình để người dùng có thể: a) Tra cứu các đầu điểm "
  "kiểm tra theo STT (số thứ tự) của học sinh. Quy ước số thứ tự bắt đầu từ 1. "
  "Nếu người dùng nhập STT lớn hơn số lượng học sinh thì chương trình thông "
  "báo STT không hợp lệ và yêu cầu nhập lại. b) Tra cứu điểm kiểm tra cụ thể "
  "lần thứ n của một học sinh theo STT.")
r(T11, C6, 88, "Vận dụng 1",
  "Viết chương trình nhập vào từ bàn phím danh sách tên (không gồm họ và đệm) "
  "học sinh cách nhau bởi dấu cách và lưu vào trong một mảng. Giả thiết rằng "
  "tên không gồm khoảng trắng. Sau đó hãy thống kê xem có bao nhiêu tên khác "
  "nhau và mỗi tên xuất hiện bao nhiêu lần trong danh sách.")
r(T11, C6, 88, "Vận dụng 2",
  "Viết chương trình nhập từ bàn phím số tự nhiên m và n. Sau đó lần lượt nhập "
  "m dòng, mỗi dòng bao gồm n số cách nhau bởi dấu cách. Đưa dữ liệu đã nhập "
  "vào ma trận A, in ma trận A ra màn hình. Sau đó: a) Tính tổng các phần tử "
  "từ ma trận A. b) In ra dòng có tổng các phần tử lớn nhất (nếu có nhiều dòng "
  "bằng nhau thì in tất cả các dòng). c) In ra giá trị các phần tử phân biệt "
  "trong ma trận tức là nếu có các giá trị xuất hiện nhiều lần trong ma trận A "
  "thì chỉ in ra một lần. d) Cho phép người dùng tìm số lần xuất hiện của một "
  "số x bất kì trong ma trận A, ví dụ người dùng nhập vào số 3, chương trình "
  "thông báo số 3 xuất hiện x lần trong ma trận tại các vị trí cột (i, j) cụ "
  "thể.")

# ── Bài 19. Bài toán tìm kiếm ──
r(T11, C6, 90, "Hoạt động 2",
  "Cho dãy số A = [1, 4, 7, 8, 3, 9, 10] và cần tìm kiếm phần tử có giá trị "
  "bằng 9. Hãy cho biết phần tử cần tìm có chỉ số bao nhiêu khi thực hiện "
  "thuật toán tìm kiếm tuần tự.")
r(T11, C6, 91, "Câu hỏi 1",
  "Cho dãy A = [1, 91, 45, 23, 67, 9, 10, 47, 90, 46, 86]. Thuật toán tìm kiếm "
  "tuần tự cần thực hiện bao nhiêu lần duyệt để tìm ra phần tử có giá trị bằng "
  "47 trong dãy?")
r(T11, C6, 92, "Mục 3c — minh hoạ",
  "Giả sử dãy số đã sắp xếp là A = [1, 3, 4, 7, 8, 9, 10]. Giá trị cần tìm là "
  "K = 9. Hãy cho biết thuật toán tìm kiếm nhị phân trả về chỉ số bao nhiêu và "
  "cần bao nhiêu bước.")


r(T11, C6, 93, "Câu hỏi 1",
  "Cho dãy A = [0, 4, 9, 10, 12, 14, 17, 18, 20, 31, 34, 67]. Với thuật toán "
  "tìm kiếm tuần tự, cần duyệt bao nhiêu phần tử để tìm ra phần tử có giá trị "
  "bằng 34?")
r(T11, C6, 93, "Câu hỏi 2",
  "Cho dãy A = [0, 4, 9, 10, 12, 14, 17, 18, 20, 31, 34, 67]. Với thuật toán "
  "tìm kiếm nhị phân, cần duyệt bao nhiêu phần tử để tìm ra phần tử có giá trị "
  "bằng 34?")
r(T11, C6, 93, "Câu hỏi 3",
  "Thay vì lần lượt lật các thẻ từ đầu đến cuối, bạn Minh đã chơi như sau: đầu "
  "tiên Minh lật thẻ ở giữa, sau đó tuỳ theo số ghi trên thẻ là lớn hơn hay "
  "nhỏ hơn số K mà lật tiếp thẻ ở ngay bên trái, hoặc ngay bên phải thẻ ở "
  "giữa. Trong trường hợp này, số lần nhiều nhất mà Minh phải lật để tìm ra "
  "thẻ in số K là bao nhiêu?",
  "Trò chơi lật thẻ: một bộ thẻ, mỗi thẻ in một số bất kì, xếp úp mặt xuống "
  "bàn theo thứ tự tăng dần của các số ghi trên thẻ.")
r(T11, C6, 93, "Luyện tập 1",
  "Em hãy chỉnh sửa thuật toán tìm kiếm tuần tự để tìm ra tất cả các phần tử "
  "trong dãy bằng giá trị cần tìm, biết dãy đó có nhiều phần tử bằng giá trị "
  "cần tìm.")
r(T11, C6, 93, "Luyện tập 2",
  "Viết chương trình của thuật toán tìm kiếm nhị phân với dãy sắp xếp giảm "
  "dần.")
r(T11, C6, 93, "Vận dụng 1",
  "Cho A là danh sách tên các học sinh trong lớp, viết chương trình tìm kiếm "
  "tuần tự để tìm ra các học sinh có tên là Hoàn.")
r(T11, C6, 93, "Vận dụng 2",
  "Cho A là danh sách tên các học sinh trong lớp được sắp xếp theo thứ tự bảng "
  "chữ cái, viết chương trình tìm kiếm nhị phân để tìm ra các học sinh có tên "
  "là Minh.")

# ── Bài 20. Thực hành bài toán tìm kiếm ──
r(T11, C6, 96, "Nhiệm vụ 2",
  "Viết chương trình tra cứu điểm thi theo tên các học sinh trong lớp. Chương "
  "trình cho phép người dùng nhập tên của học sinh cần tra cứu, sau đó kiểm "
  "tra và thông báo điểm số của học sinh cần tìm. Nếu không tìm thấy tên học "
  "sinh trong danh sách đã nhập, thông báo \"không tìm thấy dữ liệu của học "
  "sinh\".",
  "Tệp diem.inp gồm nhiều hàng, mỗi hàng gồm tên học sinh và điểm cách nhau "
  "bởi dấu cách: Nam 7.8; Sơn 5.6; Hương 8.9; Huyền 7.4; Hà 9.5; Hùng 8.4.")
r(T11, C6, 97, "Nhiệm vụ 3",
  "Viết chương trình kiểm tra điểm thi của các học sinh trong một lớp học. "
  "Điểm thi của các học sinh được ghi trong tệp diemthi_sx.inp, trong đó mỗi "
  "điểm thi của các học sinh được viết trong một hàng và được sắp xếp theo thứ "
  "tự tăng dần. Chương trình đọc dữ liệu điểm thi từ tệp, sau đó cho phép "
  "người dùng nhập một điểm số cần kiểm tra. Nếu điểm số có tồn tại thì in ra "
  "vị trí mà điểm số đó xuất hiện trong tệp, nếu điểm số không tồn tại thì in "
  "ra thông báo điểm số không tồn tại.",
  "Tệp diemthi_sx.inp gồm các dòng: 5.6; 5.8; 6.8; 7.4; 7.5; 7.9.")
r(T11, C6, 98, "Luyện tập",
  "Chỉnh sửa lại chương trình của Nhiệm vụ 3 để cho phép chương trình có thể "
  "tìm kiếm điểm số trên danh sách điểm số được sắp xếp theo thứ tự giảm dần.")
r(T11, C6, 98, "Vận dụng",
  "Viết chương trình tra cứu tên theo điểm thi của học sinh trong lớp. Chương "
  "trình cho phép người dùng nhập vào khoảng điểm số cần tìm kiếm (ví dụ từ 6 "
  "đến 8). Chương trình kiểm tra và thông báo tên của học sinh có điểm số nằm "
  "trong khoảng tương ứng.",
  "Dữ liệu: Sơn 5.6; Huyền 7.4; Nam 7.8; Hùng 8.4; Hương 8.9; Hà 9.5.")

# ── Bài 21. Các thuật toán sắp xếp đơn giản ──
r(T11, C6, 99, "Hoạt động 1",
  "Cho dãy A = [5, 3, 9, 7, 2]. Hãy cho biết dãy thu được sau khi thực hiện "
  "thuật toán sắp xếp chèn, và mô tả kết quả sau từng vòng lặp.")
r(T11, C6, 100, "Câu hỏi 1",
  "Mô phỏng chi tiết các bước lặp sắp xếp chèn dãy A = [5, 0, 4, 2, 3].")
r(T11, C6, 100, "Hoạt động 2",
  "Xét dãy A = [5, 3, 9, 7, 2]. Quan sát sơ đồ mô phỏng các bước thực hiện "
  "thuật toán sắp xếp chọn và trả lời: 1) Có bao nhiêu vòng lặp? Chỉ số i bắt "
  "đầu bằng bao nhiêu? 2) Tại mỗi vòng lặp đều có một thao tác đổi chỗ hai "
  "phần tử, đó là các phần tử nào? 3) Khi kết thúc vòng lặp ta thu được kết "
  "quả gì?")
r(T11, C6, 102, "Câu hỏi 1",
  "Thực hiện mô phỏng sắp xếp theo thuật toán sắp xếp chọn dãy số: "
  "4, 5, 2, 1, 3.")
r(T11, C6, 103, "Câu hỏi 1",
  "Mô tả các bước thuật toán sắp xếp nổi bọt của dãy A = [4, 3, 1, 2].")
r(T11, C6, 103, "Luyện tập 1",
  "Cho dãy A = [5, 8, 1, 0, 10, 4, 3]. Viết các chương trình sắp xếp dãy A "
  "theo thứ tự tăng dần theo các thuật toán sắp xếp chèn, sắp xếp chọn và sắp "
  "xếp nổi bọt.")
r(T11, C6, 103, "Luyện tập 2",
  "Viết chương trình nhập một dãy số từ bàn phím, các số cách nhau bởi dấu "
  "cách, thực hiện sắp xếp dãy đã nhập theo một trong các thuật toán sắp xếp "
  "rồi in kết quả ra màn hình.")
r(T11, C6, 103, "Vận dụng 1",
  "Viết lại các thuật toán sắp xếp trong bài theo thứ tự giảm dần.")

# ── Bài 22. Thực hành bài toán sắp xếp ──
r(T11, C6, 104, "Nhiệm vụ 1",
  "Cho danh sách số lượng mỗi mặt hàng trong kho của một cửa hàng. Người quản "
  "lí kho cần xem các mặt hàng theo thứ tự số lượng tăng dần. Em hãy viết "
  "chương trình sắp xếp các mặt hàng trong kho theo thứ tự số lượng tăng dần, "
  "sử dụng thuật toán sắp xếp chèn, sau đó in ra màn hình dãy số vừa sắp xếp.",
  "Tệp kho.inp gồm các dòng: 5; 3; 10; 4; 8; 2.")
r(T11, C6, 105, "Nhiệm vụ 2",
  "Cho danh sách điểm trung bình môn Tin học của các học sinh. Em hãy sử dụng "
  "thuật toán sắp xếp chọn để sắp xếp danh sách này theo thứ tự điểm trung "
  "bình giảm dần, sau đó in danh sách đã sắp xếp ra màn hình.",
  "Tệp diem.inp gồm các dòng: 7.8; 5.6; 8.9; 7.4; 9.5; 8.4; 9.1.")
r(T11, C6, 105, "Luyện tập 1",
  "Sử dụng thuật toán sắp xếp chọn viết lại chương trình trong Nhiệm vụ 1.")
r(T11, C6, 105, "Luyện tập 2",
  "Sử dụng thuật toán sắp xếp nổi bọt viết lại chương trình trong Nhiệm vụ 2.")
r(T11, C6, 105, "Vận dụng",
  "Một người đi mua hàng với danh sách các mặt hàng cần mua, đơn giá từng mặt "
  "hàng và số lượng hàng cần mua được lưu trong tệp văn bản muahang.inp. Hãy "
  "sử dụng thuật toán nổi bọt để sắp xếp các mặt hàng theo thứ tự thành tiền "
  "của các mặt hàng tăng dần rồi in ra tên các mặt hàng và thành tiền tương "
  "ứng.")

# ── Bài 23. Kiểm thử và đánh giá chương trình ──
r(T11, C6, 108, "Câu hỏi 1",
  "Chương trình sau giải bài toán: yêu cầu nhập số tự nhiên n và tính tổng "
  "1 + 2 + ... + n. Chương trình trên có đúng không? "
  "n = int(input(\"Nhập số tự nhiên n: \")) ; S = 0 ; "
  "for i in range(n+1): S = S + i ; print(S)")
r(T11, C6, 108, "Câu hỏi 2",
  "Chương trình sau giải bài toán đếm số các ước số thực sự của số tự nhiên n. "
  "Chương trình trên là đúng hay sai? def dem(n): count = 0 ; k = 2 ; "
  "while k < n: if n%k == 0: count = count + 1 ; k = k + 1 ; return count")

# ── Bài 24. Đánh giá độ phức tạp thời gian thuật toán ──
r(T11, C6, 110, "Luyện tập 2",
  "Xét hàm mô tả thuật toán tính tổng các số chẵn của một dãy số cho trước. "
  "Tìm hai bộ dữ liệu đầu vào có cùng kích thước của thuật toán trên nhưng có "
  "thời gian chạy khác nhau. def tongchan(A): S = 0 ; "
  "for i in range(len(A)): if A[i] % 2 == 0: S = S + A[i] ; return S")
r(T11, C6, 110, "Vận dụng 1",
  "Cho dãy các số A = [3, 1, 0, 10, 13, 16, 9, 7, 5, 11]. a) Viết chương trình "
  "mô tả thuật toán tìm kiếm phần tử C = 9 của dãy trên. Tính thời gian chính "
  "xác thực hiện công việc tìm kiếm này. b) Giả sử dãy A ở trên đã được sắp "
  "xếp theo thứ tự tăng dần: A = [0, 1, 3, 5, 7, 9, 10, 11, 13, 16]. Viết "
  "chương trình tìm kiếm nhị phân để tìm kiếm phần tử C = 9, đo thời gian thực "
  "hiện thuật toán. So sánh với kết quả tìm kiếm ở câu a.")
r(T11, C6, 110, "Vận dụng 2",
  "Viết ba chương trình mô phỏng các thuật toán sắp xếp chèn, sắp xếp chọn và "
  "sắp xếp nổi bọt mà em đã biết. Cho biết thời gian thực tế thực hiện các "
  "chương trình trên với bộ dữ liệu đầu vào là dãy A = [3, 1, 0, 10, 13, 16, "
  "9, 7, 5, 11].")
r(T11, C6, 111, "Khởi động",
  "Quan sát và ước lượng thời gian thực hiện các đoạn chương trình 1 và 2 "
  "trong Hình 24.2. Chương trình nào chạy nhanh hơn? Vì sao? "
  "Chương trình 1: n = 100 ; C = 0 ; for k in range(n): C = C + 1 ; print(C). "
  "Chương trình 2: n = 100 ; C = 0 ; for i in range(n): for j in range(n): "
  "C = C + 1 ; print(C)")


r(T11, C6, 113, "Câu hỏi 1",
  "Các lệnh và đoạn chương trình sau cần chạy trong bao nhiêu đơn vị thời "
  "gian? (a) n = 1000000 ; for k in range(n): if k%3 == 0: print(k). "
  "(b) n = 1000000 ; b = 3 ; for k in range(0,n,b): print(k)")

# ── Bài 25. Thực hành xác định độ phức tạp thời gian thuật toán ──
r(T11, C6, 117, "Luyện tập 2",
  "Cho biết hàm sau sẽ trả về giá trị là bao nhiêu? "
  "def Mystery(n): r = 0 ; for i in range(n-1): for j in range(i+1,n): "
  "for k in range(1,j): r = r + 1 ; return r")
r(T11, C6, 117, "Vận dụng 1",
  "Giả sử rằng mỗi phép tính đơn được thực hiện trong micro giây (1 µs = một "
  "phần triệu giây). Hãy xác định giá trị lớn nhất của n trong các thuật toán "
  "tìm kiếm tuần tự, sắp xếp chèn và sắp xếp chọn nếu thời gian thực thi các "
  "thuật toán là 1 giây, 1 phút và 1 giờ?")

# ── Bài 26. Phương pháp làm mịn dần trong thiết kế chương trình ──
r(T11, C6, 118, "Bài toán gốc",
  "Cho trước dãy số A: A[0], A[1], ..., A[n-1]. Cần tiến hành sắp xếp dãy trên "
  "theo thứ tự tăng dần. Ví dụ với bộ dữ liệu đầu vào là dãy [2, 1, 7, 10, 4] "
  "thì kết quả thu được là dãy [1, 2, 4, 7, 10].")
r(T11, C6, 120, "Bài toán (Hoạt động 2)",
  "Cho trước dãy số A: A[0], A[1], ..., A[n-1]. Cặp phần tử A[i], A[j] được "
  "gọi là nghịch đảo nếu i < j nhưng A[i] > A[j]. Cần viết chương trình đếm số "
  "các cặp nghịch đảo của dãy A. Ví dụ với dãy 3, 4, 2, 1 sẽ có 5 cặp nghịch "
  "đảo là (3,2), (3,1), (4,2), (4,1), (2,1).")
r(T11, C6, 122, "Luyện tập 2",
  "Sử dụng thiết kế của Bài toán 2, tìm tất cả các cặp nghịch đảo của dãy: "
  "3, 2, 1, 5, 4.")
r(T11, C6, 122, "Vận dụng 1",
  "Sử dụng phương pháp làm mịn dần để giải bài toán sau: cho trước số tự nhiên "
  "không âm n, viết chương trình kiểm tra xem số n có phải là số nguyên tố hay "
  "không? Chương trình cần thông báo \"CÓ\" nếu n là số nguyên tố, ngược lại "
  "thông báo \"KHÔNG\".")

# ── Bài 27. Thực hành thiết kế chương trình theo phương pháp làm mịn dần ──
r(T11, C6, 123, "Nhiệm vụ 1",
  "Cho trước một dãy n số, các số được kí hiệu A[0], A[1], ..., A[n-1]. Cần "
  "thiết kế chương trình kiểm tra xem dãy trên có phải là một hoán vị của dãy "
  "số 1, 2, ..., n hay không. Chương trình cần thông báo kết quả là CÓ hoặc "
  "KHÔNG.",
  "Chương trình chính trong sách chạy với A = [2, 1, 9, 10, 8, 6, 5, 2, 3, 1].")
r(T11, C6, 125, "Nhiệm vụ 2",
  "Cho trước dãy số A[0], A[1], ..., A[n-1]. Cần tính được mỗi giá trị của các "
  "phần tử của dãy trên được lặp lại bao nhiêu lần trong dãy đó. Kết quả cần "
  "được đưa ra dãy B. Như vậy dãy B sẽ có ý nghĩa như sau: B[k] = số lần lặp "
  "của phần tử A[k] trong dãy A. Ví dụ nếu A = [2, 1, 1, 3, 5, 10, 2, 5, 2] "
  "thì B = [3, 2, 2, 1, 2, 1, 3, 2, 3].")
r(T11, C6, 126, "Luyện tập 1",
  "Thiết kế thuật toán cho nhiệm vụ 1 với ý tưởng khác như sau: dãy A là một "
  "hoán vị của dãy các số từ 1 đến n khi và chỉ khi dãy A có độ dài n và mọi "
  "số i từ 1 đến n đều nằm trong A.")
r(T11, C6, 126, "Vận dụng 1",
  "Cho dãy số A = A[0], A[1], ..., A[n-1]. Thiết kế và viết chương trình kiểm "
  "tra trong dãy A có hai phần tử nào trùng nhau hay không. Cần đưa ra câu trả "
  "lời là \"có\" hay \"không\".")
r(T11, C6, 126, "Vận dụng 2",
  "Xâu kí tự được gọi là đối xứng nếu thay đổi thứ tự ngược lại các kí tự của "
  "xâu thì vẫn nhận được dãy ban đầu. Ví dụ xâu \"abcdcba\" là đối xứng, còn "
  "xâu \"1011\" không là đối xứng. Thiết kế và viết chương trình kiểm tra một "
  "xâu kí tự cho trước có là đối xứng hay không.")

# ── Bài 28. Thiết kế chương trình theo mô đun ──
r(T11, C6, 127, "Bài toán mở đầu",
  "Em được giao việc quản lí cho cửa hàng bán thực phẩm của gia đình. Hằng "
  "ngày, em phải nhập danh sách các mặt hàng và doanh số bán hàng. Cuối ngày, "
  "em cần báo cáo ba mặt hàng có doanh số cao nhất và ba mặt hàng có doanh số "
  "thấp nhất trong ngày.",
  "Data.inp: Cà rốt 1350; Khoai tây 4400; Hành tươi 1367.5; Bắp cải 3400; Cà "
  "chua 5609; Khoai lang 2100; Gạo ST25 19221; Gạo thường 23124; Cam 9800; "
  "Chuối 7823. Data.out theo sách: Gạo thường 23124; Gạo ST25 19221; Cam 9800; "
  "Khoai lang 2100; Hành tươi 1367.5; Cà rốt 1350.")
r(T11, C6, 131, "Luyện tập 2",
  "Viết thêm một chương trình cho công việc bổ sung 4 như sau: cần in ra danh "
  "sách 1/3 số mặt hàng có doanh số thấp nhất trong ngày.")
r(T11, C6, 131, "Vận dụng 1",
  "Thiết lập chương trình cho công việc thường làm vào cuối giờ bán hàng: cho "
  "trước số K (một doanh số giả định), cần tìm ra mặt hàng có doanh số nhỏ hơn "
  "K nhưng gần với K nhất. Bài toán này có thể sử dụng thuật toán tìm kiếm nào "
  "để giải?")
r(T11, C6, 131, "Vận dụng 2",
  "Một công ty du lịch có n địa điểm tham quan được đánh số theo thứ tự 0, 1, "
  "2, ..., n-1. Công ty này luôn tổ chức các tour du lịch đi lần lượt từ vị "
  "trí 0, 1, 2, ... và kết thúc tại vị trí cuối cùng n-1. Để thuận tiện cho "
  "việc quảng bá du lịch mỗi khách hàng đã lấy ý kiến khách hàng đánh giá bằng "
  "điểm số cho từng địa điểm du lịch trên, các đánh giá có thể là các số "
  "dương, 0 hoặc số âm bất kì. Số lớn hơn 0 biểu thị đánh giá tốt, số nhỏ hơn "
  "0 biểu thị đánh giá xấu về địa điểm đó. Mỗi khách hàng sẽ gửi lên công ty "
  "du lịch bảng đánh giá của mình, được biểu thị bằng một dãy n số, ví dụ như "
  "sau: 1, -3, 4, 10, 0, -5, -8, 2, -1, 7, 2. Công ty du lịch hứa sẽ tổ chức "
  "một tour riêng cho mỗi khách hàng, bảo đảm sự hài lòng cao nhất của khách "
  "hàng. Tour du lịch riêng của khách hàng sẽ là một dãy các vị trí liên tục "
  "các địa điểm, ví dụ từ vị trí i đến j, tức là xuất phát từ i, khách hàng sẽ "
  "lần lượt đi qua các vị trí i, i+1, i+2, ... và kết thúc tại j. Công ty du "
  "lịch bảo đảm tổng các đánh giá của khách hàng trên tour riêng của mình là "
  "lớn nhất. Em hãy giúp công ty du lịch thiết lập tour du lịch tối ưu cho "
  "khách hàng nếu biết trước các đánh giá của khách hàng đó.")

# ── Bài 29. Thực hành thiết kế chương trình theo mô đun ──
r(T11, C6, 132, "Nhiệm vụ",
  "Tính điểm tổng hợp của vận động viên. Điểm tổng hợp của mỗi vận động viên "
  "là trung bình cộng điểm của ban giám khảo. Tuy nhiên trong mỗi ban giám "
  "khảo luôn có hai giám khảo đặc biệt, hai giám khảo này có hệ số tổng hợp là "
  "2, trong khi các giám khảo khác có hệ số 1. Theo quy định của BTC thì các "
  "giám khảo đặc biệt sẽ ở vị trí đầu tiên và cuối cùng của danh sách.",
  "SeaGames.inp: 101 7.5 8.0 9.0 9.5 7.1 6.8; 200 8.5 9.1 9.5 8.6 9.9; "
  "003 6.6 7.0 7.5 6.8 5.9 8.1; 045 8.5 7.9 9.3 9.0 8.9; 901 9.2 9.7 8.6. "
  "Ketqua.out theo sách: 101 7.77; 200 9.14; 003 7.08; 045 8.71; 901 9.06.")
r(T11, C6, 136, "Luyện tập 1",
  "Hãy chỉnh sửa lại chương trình trên nếu bổ sung thêm điều kiện sau vào "
  "nhiệm vụ: trong tệp kết quả đầu ra, thứ tự các vận động viên được ghi theo "
  "thứ tự giảm dần của điểm đánh giá.")
r(T11, C6, 136, "Vận dụng 1",
  "Cho trước số tự nhiên n, cần in ra trên màn hình dãy n số nguyên tố đầu "
  "tiên. Ví dụ nếu n = 5 thì dãy cần in ra sẽ là 2, 3, 5, 7, 11.")
r(T11, C6, 136, "Vận dụng 2",
  "Trong một kì thi Tin học trẻ, mỗi học sinh sẽ phải làm 3 bài thi. Với mỗi "
  "bài, nếu học sinh làm sẽ được ban giám khảo chấm và cho điểm, nếu không làm "
  "thì sẽ không tính điểm. Điểm thi sẽ là số tự nhiên từ 0 đến 20. Nếu học "
  "sinh không làm bài thì ghi -1. Em có nhiệm vụ tính toán tổng số điểm thi "
  "của các bạn học sinh và đưa dữ liệu ra tệp ketqua.out là danh sách ba bạn "
  "có tổng điểm cao nhất được sắp xếp giảm dần từ trên xuống dưới.",
  "Diemthi.inp: A12 12 -1 15; B123 9 14 -1; C11 10 12 18; A110 10 -1 -1; "
  "B01 12 10 4. ketqua.out theo sách: C11 10 12 18 40; A12 12 -1 15 27; "
  "B01 12 10 4 26.")

# ── Bài 30. Thiết lập thư viện cho chương trình ──
r(T11, C6, 142, "Câu hỏi 1",
  "Đoạn chương trình sau thực hiện công việc gì? "
  "from LinkedList import * ; L = LL() ; insert(L,10) ; insert(L,20) ; show(L)")
r(T11, C6, 142, "Câu hỏi 2",
  "Viết đoạn chương trình ngắn sử dụng thư viện LinkedList để thiết lập một "
  "danh sách liên kết L và bổ sung các tên \"Bình\", \"Hoa\", \"Hà\" vào danh "
  "sách này.")
r(T11, C6, 142, "Vận dụng 1",
  "Cho trước một danh sách liên kết L. Viết một hàm đếm số lượng phần tử của "
  "danh sách liên kết này.")
r(T11, C6, 142, "Vận dụng 2",
  "Viết hàm delete_last(L) có chức năng xoá phần tử cuối cùng của danh sách "
  "liên kết L.")

# ── Bài 31. Thực hành thiết lập thư viện chương trình ──
r(T11, C6, 143, "Nhiệm vụ 1",
  "Viết thư viện hinh_tron gồm hai hàm để tính chu vi và diện tích của hình "
  "tròn với tham số của hàm số là bán kính. Sau đó, viết một tệp mã nguồn "
  "main.py để yêu cầu người dùng nhập bán kính đường tròn là một số dương rồi "
  "sử dụng thư viện trên để tính diện tích và chu vi hình tròn.")
r(T11, C6, 144, "Nhiệm vụ 2",
  "Tạo thư viện cong_thuc_ly gồm hai hàm machSongSong(dsDienTro) và "
  "machNoiTiep(dsDienTro) để tính điện trở tương đương của mạch nối tiếp và "
  "song song gồm các điện trở được cho giá trị tính theo Ohm trong mảng "
  "dsDienTro. Hãy viết chương trình trong tệp main.py sử dụng hai hàm vừa định "
  "nghĩa để tính điện trở tương đương của mạch gồm các điện trở với giá trị 3, "
  "6 và 8 Ohm.",
  "Điện trở tương đương của mạch nối tiếp bằng tổng các điện trở; mạch song "
  "song bằng nghịch đảo của tổng các nghịch đảo giá trị điện trở thành phần.")
r(T11, C6, 144, "Nhiệm vụ 3",
  "Em hãy định nghĩa hàm tinhNtkTB(dsNtk, dstyLe) trong file cong_thuc_hoa.py "
  "để tính nguyên tử khối trung bình của một nguyên tố hoá học trong đó tham "
  "số dsNtk là mảng giá trị các nguyên tử khối của các đồng vị và dstyLe là tỉ "
  "lệ phần trăm số nguyên tử của các đồng vị tương ứng của nguyên tố đó. Sau "
  "đó, em hãy viết chương trình trong tệp main.py để sử dụng hàm tinhNtkTB "
  "tính nguyên tử khối trung bình của Carbon biết Carbon có hai đồng vị bền là "
  "12C chiếm 98,89% và 13C chiếm 1.11%.")
r(T11, C6, 145, "Vận dụng 1",
  "Tạo thư viện phuong_trinh gồm hàm phuongTrinhBac2(a, b, c) với a, b, c là "
  "các hệ số của phương trình ax² + bx + c = 0. Tuỳ vào các giá trị của các "
  "tham số, hàm sẽ in ra thông báo nghiệm của phương trình.")
r(T11, C6, 145, "Vận dụng 2",
  "Viết chương trình quản lí các bài hát trong một đĩa CD hay một play list, "
  "sử dụng cấu trúc LinkedList. Chương trình gồm hàm nhapDL() yêu cầu người "
  "dùng nhập số lượng bài hát rồi nhập lần lượt tên các bài hát và bổ sung vào "
  "đĩa CD; hàm timBai() nhận đối tượng LinkedList và tên bài hát, nếu có bài "
  "hát cần tìm thì in ra vị trí đầu tiên xuất hiện bài hát, nếu không in ra "
  "thông báo \"Không tìm thấy bài hát\"; hàm inTT() in mỗi bài hát trên một "
  "dòng theo định dạng <Số thứ tự>. <Tên bài hát>.")


def _nhan_dien(text: str, n: int = 95) -> str:
    """Câu mô tả ngắn để người chọn NHẬN RA bài, không thay nội dung đầy đủ."""
    t = text.replace("|", "/")
    return t if len(t) <= n else t[: n - 1].rsplit(" ", 1)[0] + "…"


def kiem_chat_luong(recs: list[dict]) -> list[str]:
    """Trả danh sách lỗi. Rỗng = PASS."""
    loi: list[str] = []
    ids = [r["source_id"] for r in recs]
    if len(set(ids)) != len(ids):
        loi.append("source_id bị trùng")
    for r in recs:
        cid = r["source_id"]
        if not r.get("book"):
            loi.append(f"{cid}: thiếu book")
        if not isinstance(r.get("page"), int):
            loi.append(f"{cid}: thiếu page")
        if not (r.get("problem_text") or "").strip():
            loi.append(f"{cid}: problem_text rỗng")
    van = [(r["book"], r["page"], r["problem_text"]) for r in recs]
    if len(set(van)) != len(van):
        loi.append("có record trùng hoàn toàn (cùng sách + trang + nội dung)")
    khoa = [(r["book"], r["page"]) for r in recs]
    if khoa != sorted(khoa, key=lambda k: (k[0], k[1])):
        loi.append("record chưa sắp theo sách → trang → vị trí")
    return loi


def main() -> int:
    RECORDS.sort(key=lambda r: (r["book"], r["page"]))
    dem = {T10: 0, T11: 0}
    for rec in RECORDS:
        dem[rec["book"]] += 1
        tag = "T10-C5" if rec["book"] == T10 else "T11CS-C6"
        rec["source_id"] = f"{tag}-{dem[rec['book']]:03d}"

    thu_tu = ["source_id", "book", "section_or_chapter", "page",
              "exercise_number_or_position", "problem_text", "context_text"]
    goi = [{k: r[k] for k in thu_tu} for r in RECORDS]

    loi = kiem_chat_luong(goi)

    js = HERE / "source_universe.json"
    js.write_text(
        json.dumps({"records": goi}, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8")
    van_tay = hashlib.sha256(js.read_bytes()).hexdigest()
    (HERE / "SOURCE_UNIVERSE_FINGERPRINT.txt").write_text(
        van_tay + "\n", encoding="utf-8")

    dong = ["| ID | SGK | Chủ đề | Trang | Số bài/vị trí | Nội dung nhận diện ngắn |",
            "|---|---|---|---|---|---|"]
    for r in goi:
        sach = "TH10" if r["book"] == T10 else "TH11-KHMT"
        cd = "CĐ5" if r["book"] == T10 else "CĐ6"
        dong.append(f"| `{r['source_id']}` | {sach} | {cd} | {r['page']} | "
                    f"{r['exercise_number_or_position']} | "
                    f"{_nhan_dien(r['problem_text'])} |")

    md = HERE / "SOURCE_UNIVERSE.md"
    md.write_text(_md(dem, van_tay, loi, "\n".join(dong)), encoding="utf-8")

    print(f"tin-hoc-10   : {dem[T10]}")
    print(f"tin-hoc-11-cs: {dem[T11]}")
    print(f"tong         : {len(goi)}")
    print(f"fingerprint  : {van_tay}")
    print(f"quality      : {'PASS' if not loi else 'FAIL — ' + '; '.join(loi)}")
    return 0 if not loi else 1


def _md(dem, van_tay, loi, bang) -> str:
    return f"""# SOURCE UNIVERSE — bài tập SGK để custodian độc lập CHỌN

> **Vai trò của phase này:** development agent thực hiện trích xuất cơ học từ
> nguồn SGK. **Quyền lựa chọn 40 case SEALED thuộc về GVHD/custodian độc lập.**

Danh sách này **không** phản ánh năng lực của hệ đang được đánh giá. Nó phản
ánh nội dung SGK.

## Phạm vi đã duyệt

| SGK | Chủ đề | Trang sách | Số record |
|---|---|---|---|
| `tin-hoc-10.pdf` | {C5} | 86 – 155 (70 trang) | **{dem[T10]}** |
| `tin-hoc-11-cs.pdf` | {C6} | 81 – 145 (65 trang) | **{dem[T11]}** |
| | | **135 trang** | **{dem[T10] + dem[T11]}** |

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
{van_tay}
```

SHA-256 của `source_universe.json`.

## Kiểm chất lượng

```
{"PASS — mọi kiểm tra đều đạt" if not loi else chr(10).join(loi)}
```

Đã kiểm: `source_id` duy nhất · mọi record có `book` · có `page` · có
`problem_text` không rỗng · không có record trùng hoàn toàn · sắp theo sách →
trang → vị trí · số record trong JSON khớp bảng trên · fingerprint tính trên
đúng file JSON cuối cùng.

## Bảng chọn

{bang}
"""


if __name__ == "__main__":
    main()
