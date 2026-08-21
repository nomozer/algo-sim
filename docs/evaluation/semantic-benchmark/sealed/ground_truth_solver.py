# -*- coding: utf-8 -*-
"""INDEPENDENT SOLVER — sinh `cases.json` của tập SEALED.

Ground truth ở đây được tính bằng **Python thuần**, hoàn toàn độc lập với hệ
đang bị đánh giá: không import `SemanticProgramInterpreter`, không gọi
`run_pipeline`, không đụng bất kỳ module nào trong `app.simulation`. Kiểm được
bằng mắt — file này không có một dòng `import` nào trỏ vào mã sản phẩm.

Vì sao dùng máy tính thay vì tính tay: tính tay 40 đáp án là 40 cơ hội sai số
học, và một đáp án sai sẽ âm thầm chấm hệ là SAI trong khi nó ĐÚNG. Sai ở đây
đắt hơn nhiều so với công sức viết mã.

Đề bài lấy từ SGK Tin học (Kết nối tri thức với cuộc sống) trong
`data/knowledge/sources/`. Sách là bản quét, không có lớp chữ; custodian đọc
bằng cách dựng ảnh từng trang (PyMuPDF) rồi đọc trực tiếp. Mỗi case ghi đúng
tên sách và số trang.

    python ground_truth_solver.py > cases.json
"""
from __future__ import annotations

import json
import sys
from datetime import date

CASES: list[dict] = []


def add(cid, book, loc, text, kind, value, provenance, *,
        prescribed=None, expressible=True, note=None, extra_expected=None):
    exp = [{"obligation_kind": kind, "value": value}]
    if extra_expected:
        exp.extend(extra_expected)
    c = {
        "case_id": cid,
        "source": {"book": book, "location": loc},
        "problem_text": text,
        "eligibility_audit": {
            "discrete": True,
            "finite_input": True,
            "deterministic_bounded_procedure": True,
            "in_scope": True,
        },
        "metadata": {
            "no_specialized_module": True,
            "no_target_template": True,
            "not_prompt_example": True,
            "expressible_in_ir": expressible,
        },
        "prescribed_procedure": prescribed,
        "ground_truth": {
            "kind": "independent_solver",
            "provenance": provenance,
            "expected": exp,
        },
    }
    if note:
        c["custodian_note"] = note
    CASES.append(c)


CS11 = "tin-hoc-11-cs.pdf"
T10 = "tin-hoc-10.pdf"

PY = "tính bằng Python thuần trong ground_truth_solver.py, không dùng hệ đang được đánh giá"
SACH = "đáp án in sẵn trong sách"
CUTHE = "custodian cụ thể hoá dữ liệu vì đề gốc nhận dữ liệu từ bàn phím; " + PY

# ── Nhóm A: ma trận (đề Bài 17–18, dữ liệu ma trận A in ở trang 84) ──
A = [[12, 10, 91], [11, 45, 20], [15, 34, 55]]
B = [[3, 1, 3], [2, 3, 1], [1, 2, 2]]

add("sealed_001", CS11, "trang 88, Vận dụng 2a",
    "Cho ma trận A gồm 3 hàng 3 cột:\n12 10 91\n11 45 20\n15 34 55\n"
    "Tính tổng tất cả các phần tử của ma trận A.",
    "aggregate_matching", sum(sum(r) for r in A),
    "dữ liệu ma trận A lấy từ ví dụ trang 84 cùng sách; " + PY)

_tong_dong = [sum(r) for r in A]
add("sealed_002", CS11, "trang 88, Vận dụng 2b",
    "Cho ma trận A gồm 3 hàng 3 cột:\n12 10 91\n11 45 20\n15 34 55\n"
    "Tính tổng các phần tử của từng hàng, rồi cho biết tổng lớn nhất trong các "
    "tổng hàng đó.",
    "extremum", max(_tong_dong),
    "dữ liệu ma trận A lấy từ ví dụ trang 84 cùng sách; " + PY,
    note="bài GHÉP hai cơ chế: gộp theo hàng rồi lấy cực trị trên dãy dẫn xuất")

_phang_B = [x for r in B for x in r]
_pb = []
for _x in _phang_B:
    if _x not in _pb:
        _pb.append(_x)
add("sealed_003", CS11, "trang 88, Vận dụng 2c",
    "Cho ma trận B gồm 3 hàng 3 cột:\n3 1 3\n2 3 1\n1 2 2\n"
    "Hãy liệt kê các giá trị phân biệt xuất hiện trong ma trận B; nếu một giá "
    "trị xuất hiện nhiều lần thì chỉ kể một lần, theo thứ tự gặp đầu tiên khi "
    "duyệt lần lượt từng hàng từ trái sang phải.",
    "derived_sequence", _pb,
    "đề gốc không cho ma trận cụ thể; custodian cụ thể hoá bằng ma trận có giá "
    "trị lặp để câu hỏi 'giá trị phân biệt' có nội dung; " + PY)

add("sealed_004", CS11, "trang 88, Vận dụng 2d",
    "Cho ma trận B gồm 3 hàng 3 cột:\n3 1 3\n2 3 1\n1 2 2\n"
    "Đếm xem giá trị 3 xuất hiện bao nhiêu lần trong ma trận B.",
    "aggregate_matching", _phang_B.count(3), CUTHE)

# ── Nhóm B: dãy số in sẵn trong sách ──
D = [0, 1, 5, 7, 0, 2, 5, 1, 1, 2]
_tan = {}
for _x in D:
    _tan[_x] = _tan.get(_x, 0) + 1
add("sealed_005", CS11, "trang 85, Vận dụng 2",
    "Cho dãy số: 0 1 5 7 0 2 5 1 1 2\n"
    "Với mỗi giá trị xuất hiện trong dãy, hãy cho biết giá trị đó lặp lại bao "
    "nhiêu lần.",
    "total_mapping", {str(k): v for k, v in _tan.items()},
    "dãy in trong đề gốc; " + PY)

E = [3, 2, 1, 5, 4]
_nghich = sum(1 for i in range(len(E)) for j in range(i + 1, len(E)) if E[i] > E[j])
add("sealed_006", CS11, "trang 122, Luyện tập 2",
    "Cho dãy số: 3 2 1 5 4\n"
    "Một cặp nghịch đảo là một cặp vị trí (i, j) với i < j và giá trị tại vị "
    "trí i lớn hơn giá trị tại vị trí j. Hãy đếm số cặp nghịch đảo của dãy.",
    "aggregate_matching", _nghich,
    "dãy in trong đề gốc; " + PY)

F = [2, 1, 1, 3, 5, 10, 2, 5, 2]
add("sealed_007", CS11, "trang 126, ví dụ chương trình tinh_lap",
    "Cho dãy số A: 2 1 1 3 5 10 2 5 2\n"
    "Hãy lập dãy B cùng độ dài với A, trong đó phần tử thứ i của B là số lần "
    "giá trị A[i] xuất hiện trong toàn bộ dãy A.",
    "derived_sequence", [F.count(x) for x in F],
    "dãy A in trong chương trình mẫu của đề gốc; " + PY)

G = [1, -3, 4, 10, 0, -5, -8, 2, -1, 7, 2]
_best = max(sum(G[i:j]) for i in range(len(G)) for j in range(i + 1, len(G) + 1))
add("sealed_008", CS11, "trang 131, Vận dụng 2",
    "Cho dãy điểm đánh giá của một khách hàng cho các địa điểm tham quan, theo "
    "thứ tự: 1 -3 4 10 0 -5 -8 2 -1 7 2\n"
    "Một tour là một đoạn các vị trí liên tiếp của dãy. Hãy cho biết tổng điểm "
    "đánh giá lớn nhất mà một tour có thể đạt được.",
    "extremum", _best,
    "dãy in trong đề gốc; " + PY,
    note="đề gốc phát biểu dưới dạng bài toán du lịch; đây là bài đoạn con "
         "liên tiếp có tổng lớn nhất")

H = [0, 4, 0, 1, 2, 3, 8, 9, 0, 1, 2, 3, 17, -16, 0, 1, 2]
_vt = next(i for i in range(len(H) - 2) if H[i:i + 3] == [1, 2, 3])
add("sealed_009", T10, "trang 118, Nhiệm vụ 3",
    "Cho dãy số A: 0 4 0 1 2 3 8 9 0 1 2 3 17 -16 0 1 2\n"
    "Hãy tìm vị trí đầu tiên trong dãy A mà tại đó ba số hạng liên tiếp lần "
    "lượt có giá trị là 1, 2, 3. Vị trí được đánh số bắt đầu từ 0.",
    "first_match_index", _vt,
    "dãy A in trong chương trình mẫu của đề gốc; " + PY)

_diem = {"A12": [12, -1, 15], "B123": [9, 14, -1], "C11": [10, 12, 18],
         "A110": [10, -1, -1], "B01": [12, 10, 4]}
_tong = sorted((sum(x for x in v if x != -1) for v in _diem.values()), reverse=True)[:3]
add("sealed_010", CS11, "trang 136, Vận dụng 2",
    "Trong một kì thi Tin học trẻ, mỗi học sinh làm 3 bài thi. Điểm mỗi bài là "
    "số tự nhiên từ 0 đến 20; nếu học sinh không làm bài nào thì bài đó ghi "
    "-1 và không được tính điểm. Dữ liệu điểm thi như sau:\n"
    "A12 12 -1 15\nB123 9 14 -1\nC11 10 12 18\nA110 10 -1 -1\nB01 12 10 4\n"
    "Hãy cho biết tổng điểm của ba học sinh có tổng điểm cao nhất, sắp xếp "
    "giảm dần.",
    "ordering", _tong,
    SACH + " (bảng ketqua.out trang 136), đối chiếu lại bằng Python thuần")


def _nguyen_to(n):
    if n < 2:
        return False
    d = 2
    while d * d <= n:
        if n % d == 0:
            return False
        d += 1
    return True


_nt = []
_k = 2
while len(_nt) < 5:
    if _nguyen_to(_k):
        _nt.append(_k)
    _k += 1
add("sealed_011", CS11, "trang 136, Vận dụng 1",
    "Hãy liệt kê 5 số nguyên tố đầu tiên theo thứ tự tăng dần.",
    "derived_sequence", _nt,
    SACH + " (đề nêu rõ với n = 5 thì dãy cần in ra là 2, 3, 5, 7, 11); " + PY)

_ntk = [12, 13]
_tyle = [98.89, 1.11]
add("sealed_012", CS11, "trang 145, ví dụ chương trình tinhNtkTB",
    "Nguyên tố Carbon có hai đồng vị với nguyên tử khối lần lượt là 12 và 13, "
    "chiếm tỉ lệ phần trăm lần lượt là 98,89% và 1,11%. Nguyên tử khối trung "
    "bình được tính bằng tổng của các tích (nguyên tử khối × tỉ lệ phần trăm), "
    "chia cho 100. Hãy tính nguyên tử khối trung bình của Carbon.",
    "aggregate_matching",
    round(sum(a * b for a, b in zip(_ntk, _tyle)) / 100, 4),
    "dữ liệu in trong chương trình mẫu của đề gốc; " + PY)


def _ucln(a, b):
    while b:
        a, b = b, a % b
    return a


add("sealed_013", T10, "trang 148, bảng lần vết chương trình",
    "Cho hai số tự nhiên m = 20 và n = 16. Hãy tìm ước chung lớn nhất của hai "
    "số này.",
    "extremum", _ucln(20, 16),
    SACH + " (bảng lần vết trang 148 cho kết quả 4); " + PY)

# ── Nhóm C: tính trên dãy sinh ra ──
_day = [x for x in range(1, 100, 3)]
add("sealed_014", T10, "trang 110, Luyện tập 1",
    "Cho dãy số 1, 4, 7, 10, … trong đó mỗi số hạng hơn số hạng liền trước 3 "
    "đơn vị. Hãy cho biết số hạng lớn nhất của dãy mà vẫn nhỏ hơn 100.",
    "extremum", max(_day), PY)

add("sealed_015", T10, "trang 110, Luyện tập 2",
    "Xét các số tự nhiên từ 1 đến 100. Hãy đếm xem có bao nhiêu số thoả mãn "
    "điều kiện: hoặc chia hết cho 5, hoặc chia cho 3 dư 1.",
    "aggregate_matching",
    sum(1 for x in range(1, 101) if x % 5 == 0 or x % 3 == 1),
    "đề gốc nói '100 số tự nhiên đầu tiên'; custodian ghi rõ khoảng 1..100 để "
    "loại bỏ mơ hồ; " + PY)


def _nhuan(y):
    return y % 400 == 0 or (y % 4 == 0 and y % 100 != 0)


add("sealed_016", T10, "trang 152, Vận dụng 1",
    "Thế kỉ XXI gồm các năm từ 2001 đến 2100. Một năm là năm nhuận nếu năm đó "
    "chia hết cho 400, hoặc chia hết cho 4 nhưng không chia hết cho 100. Hãy "
    "đếm số năm nhuận trong thế kỉ XXI.",
    "aggregate_matching", sum(1 for y in range(2001, 2101) if _nhuan(y)), PY)

add("sealed_017", T10, "trang 118, Vận dụng 1",
    "Hãy liệt kê 10 số tự nhiên chẵn đầu tiên theo thứ tự tăng dần.",
    "derived_sequence", [2 * i for i in range(10)],
    "đề gốc nhận n từ bàn phím; custodian chọn n = 10; " + PY)

_fib = [0, 1]
while len(_fib) < 10:
    _fib.append(_fib[-1] + _fib[-2])
add("sealed_018", T10, "trang 118, Vận dụng 2",
    "Dãy Fibonacci được xác định như sau: F(0) = 0, F(1) = 1, và với n ≥ 2 thì "
    "F(n) = F(n-1) + F(n-2). Hãy liệt kê 10 số hạng đầu tiên của dãy "
    "Fibonacci.",
    "derived_sequence", _fib,
    "đề gốc nhận n từ bàn phím; custodian chọn n = 10; " + PY)

add("sealed_019", T10, "trang 144, Vận dụng 1",
    "Cho số tự nhiên n = 36. Hãy liệt kê các ước số thực sự của n theo thứ tự "
    "tăng dần, tính cả 1 và không tính chính n.",
    "derived_sequence", [d for d in range(1, 36) if 36 % d == 0],
    "đề gốc nhận n từ bàn phím; custodian chọn n = 36; " + PY)

_uocnt = next(d for d in range(2, 92) if 91 % d == 0 and _nguyen_to(d))
add("sealed_020", T10, "trang 155, Vận dụng 3",
    "Cho số tự nhiên n = 91. Hãy tìm ước số nguyên tố nhỏ nhất của n.",
    "extremum", _uocnt,
    "đề gốc nhận n từ bàn phím; custodian chọn n = 91 (hợp số, ước nguyên tố "
    "nhỏ nhất không phải 2 hay 3); " + PY)

add("sealed_021", T10, "trang 126, Vận dụng 1",
    "Cho hai số tự nhiên a = 48 và b = 18. Hãy tìm ước chung lớn nhất của a "
    "và b.",
    "extremum", _ucln(48, 18),
    "đề gốc nhận hai số từ bàn phím; custodian chọn a = 48, b = 18; " + PY)

_mystery = sum(1 for i in range(4) for j in range(i + 1, 5) for _ in range(1, j))
add("sealed_022", CS11, "trang 117, Luyện tập 2",
    "Xét thủ tục sau với n = 5. Bắt đầu với r = 0. Với mỗi i chạy từ 0 đến "
    "n-2, với mỗi j chạy từ i+1 đến n-1, với mỗi k chạy từ 1 đến j-1, tăng r "
    "thêm 1. Hãy cho biết giá trị của r sau khi thủ tục kết thúc.",
    "aggregate_matching", _mystery,
    "thủ tục in trong đề gốc (hàm Mystery); custodian chọn n = 5; " + PY)

# ── Nhóm D: xâu kí tự ──
add("sealed_023", T10, "trang 122, Luyện tập 1",
    'Cho xâu kí tự S = "Tin hoc". Hãy trích ra xâu con gồm ba kí tự đầu tiên '
    "của S.",
    "derived_sequence", list("Tin hoc"[:3]),
    "đề gốc không cho xâu cụ thể; custodian chọn S = \"Tin hoc\"; " + PY)

_raw = "Hoc   sinh  lop   10"
add("sealed_024", T10, "trang 126, Nhiệm vụ 2",
    'Cho xâu kí tự S = "Hoc   sinh  lop   10", trong đó giữa các từ có thể có '
    "nhiều dấu cách. Hãy tách S thành danh sách các từ, bỏ hết dấu cách thừa.",
    "derived_sequence", _raw.split(),
    "đề gốc nhận xâu từ bàn phím; custodian chọn xâu có nhiều dấu cách liên "
    "tiếp để câu hỏi có nội dung; " + PY)

_hoten = ["Nguyen Van An", "Tran Thi Binh", "Le Hoang Nam"]
add("sealed_025", T10, "trang 126, Nhiệm vụ 3",
    "Cho danh sách họ tên học sinh: Nguyen Van An; Tran Thi Binh; Le Hoang "
    "Nam. Với mỗi họ tên, phần tên là từ cuối cùng. Hãy lập danh sách tên của "
    "các học sinh, giữ nguyên thứ tự.",
    "derived_sequence", [s.split()[-1] for s in _hoten],
    "đề gốc nhận danh sách từ bàn phím; custodian cụ thể hoá ba họ tên; " + PY)


def _merge_str(s1, s2):
    S = ""
    l = min(len(s1), len(s2))
    for i in range(l):
        S += s1[i] + s2[i]
    if len(s1) < len(s2):
        for i in range(l, len(s2)):
            S += s2[i]
    if len(s2) < len(s1):
        for i in range(l, len(s1)):
            S += s1[i]
    return S


add("sealed_026", T10, "trang 135, ví dụ chương trình merge_str",
    'Cho hai xâu kí tự s1 = "abc" và s2 = "12345". Hãy ghép hai xâu theo cách '
    "sau: lần lượt lấy một kí tự của s1 rồi một kí tự của s2, cho đến khi xâu "
    "ngắn hơn hết kí tự; phần còn lại của xâu dài hơn được nối vào cuối. Hãy "
    "cho biết xâu kết quả.",
    "derived_sequence", list(_merge_str("abc", "12345")),
    "thuật toán in trong chương trình mẫu của đề gốc; custodian chọn hai xâu "
    "có độ dài khác nhau; " + PY)

add("sealed_027", T10, "trang 135, Vận dụng 2",
    'Cho xâu họ tên "Nguyen Van An". Hãy đổi toàn bộ xâu này thành chữ in hoa.',
    "derived_sequence", list("Nguyen Van An".upper()),
    "đề gốc mô tả hàm change(ho_ten, c); custodian chọn trường hợp c = 0 (in "
    "hoa) với một họ tên cụ thể; " + PY)

_ds_ten = ["Huong", "Nam", "Huong", "Lan", "Binh", "Huong", "Nam"]
add("sealed_028", T10, "trang 122, Vận dụng 2",
    "Cho danh sách tên học sinh trong lớp: Huong, Nam, Huong, Lan, Binh, "
    'Huong, Nam. Hãy đếm xem trong lớp có bao nhiêu bạn tên là "Huong".',
    "aggregate_matching", _ds_ten.count("Huong"), CUTHE)

_ds2 = ["An", "Binh", "An", "Cuong", "Binh", "An"]
_tan2 = {}
for _t in _ds2:
    _tan2[_t] = _tan2.get(_t, 0) + 1
add("sealed_029", CS11, "trang 88, Vận dụng 1",
    "Cho danh sách tên học sinh: An, Binh, An, Cuong, Binh, An. Hãy cho biết "
    "mỗi tên xuất hiện bao nhiêu lần trong danh sách.",
    "total_mapping", _tan2, CUTHE)

# ── Nhóm E: thống kê, bài ghép nhiều cơ chế ──
_cao = [152, 160, 148, 171, 165, 158, 169, 155]
_tb_cao = sum(_cao) / len(_cao)
add("sealed_030", CS11, "trang 85, Luyện tập 1 (ý 1)",
    "Số đo chiều cao (cm) của các bạn trong lớp lần lượt là: 152, 160, 148, "
    "171, 165, 158, 169, 155. Hãy tính chiều cao trung bình của cả lớp.",
    "aggregate_matching", round(_tb_cao, 3), CUTHE)

add("sealed_031", CS11, "trang 85, Luyện tập 1 (ý 2)",
    "Số đo chiều cao (cm) của các bạn trong lớp lần lượt là: 152, 160, 148, "
    "171, 165, 158, 169, 155. Hãy đếm xem có bao nhiêu bạn cao hơn chiều cao "
    "trung bình của cả lớp.",
    "aggregate_matching", sum(1 for x in _cao if x > _tb_cao), CUTHE,
    note="bài GHÉP hai cơ chế: tính trung bình rồi đếm theo ngưỡng vừa tính")

_dien = [[120, 135, 150, 160, 200, 260, 280, 275, 210, 170, 140, 130],
         [130, 140, 155, 165, 210, 270, 290, 285, 220, 175, 145, 135]]
add("sealed_032", CS11, "trang 85, Vận dụng 3a",
    "Bảng sau ghi số tiền điện (nghìn đồng) của một gia đình theo từng tháng "
    "trong hai năm, mỗi hàng là một năm, mỗi cột là một tháng:\n"
    "120 135 150 160 200 260 280 275 210 170 140 130\n"
    "130 140 155 165 210 270 290 285 220 175 145 135\n"
    "Hãy lập dãy mới gồm số tiền điện trung bình của từng năm, mỗi năm một số.",
    "derived_sequence", [round(sum(r) / len(r), 3) for r in _dien], CUTHE)

_phang_dien = [x for r in _dien for x in r]
add("sealed_033", CS11, "trang 85, Vận dụng 3b",
    "Bảng sau ghi số tiền điện (nghìn đồng) của một gia đình theo từng tháng "
    "trong hai năm, mỗi hàng là một năm, mỗi cột là một tháng:\n"
    "120 135 150 160 200 260 280 275 210 170 140 130\n"
    "130 140 155 165 210 270 290 285 220 175 145 135\n"
    "Hãy tính số tiền điện trung bình của tất cả các tháng đã được ghi trong "
    "bảng.",
    "aggregate_matching",
    round(sum(_phang_dien) / len(_phang_dien), 3), CUTHE)

_nhap = [12, 7, 25, 9, 18, 3]
add("sealed_034", T10, "trang 126, Luyện tập 1",
    "Cho các số được nhập vào lần lượt là: 12 7 25 9 18 3. Hãy tính tổng của "
    "các số đã nhập.",
    "aggregate_matching", sum(_nhap), CUTHE)

_doanh = {"Ao": 120, "Quan": 85, "Mu": 40, "Giay": 210, "Tat": 25, "Khan": 60}
_thap = sorted(_doanh.values())[:len(_doanh) // 3]
add("sealed_035", CS11, "trang 131, Luyện tập 2",
    "Doanh số bán trong ngày của các mặt hàng lần lượt là: Ao 120, Quan 85, "
    "Mu 40, Giay 210, Tat 25, Khan 60. Cửa hàng có 6 mặt hàng nên một phần ba "
    "số mặt hàng là 2 mặt hàng. Hãy cho biết doanh số của 2 mặt hàng có doanh "
    "số thấp nhất, sắp xếp tăng dần.",
    "ordering", _thap, CUTHE)

_K = 100
_duoi = [v for v in _doanh.values() if v < _K]
add("sealed_036", CS11, "trang 131, Vận dụng 1",
    "Doanh số bán trong ngày của các mặt hàng lần lượt là: Ao 120, Quan 85, "
    "Mu 40, Giay 210, Tat 25, Khan 60. Cho K = 100. Hãy tìm doanh số lớn nhất "
    "trong các doanh số nhỏ hơn K.",
    "extremum", max(_duoi), CUTHE,
    note="bài GHÉP hai cơ chế: lọc theo ngưỡng rồi lấy cực trị trên phần đã lọc")

_ngay = (date(2021, 10, 8) - date(1990, 1, 1)).days
add("sealed_037", T10, "trang 155, Vận dụng 1",
    "Trong các phần mềm bảng tính điện tử, dữ liệu ngày tháng được coi là số "
    "ngày tính từ ngày 1-1-1990. Hãy cho biết ngày 8-10-2021 ứng với số ngày "
    "bao nhiêu, tức là số ngày đã trôi qua kể từ ngày 1-1-1990.",
    "aggregate_matching", _ngay,
    "ví dụ ngày 8-10-2021 nêu trong đề gốc; " + PY)

_xoa_giua = [1, 2, 2, 3, 4, 5, 5]
_kq_giua = _xoa_giua[:len(_xoa_giua) // 2] + _xoa_giua[len(_xoa_giua) // 2 + 1:]
add("sealed_038", T10, "trang 118, Luyện tập 2",
    "Cho dãy số A: 1 2 2 3 4 5 5. Dãy có số phần tử là số lẻ, hãy xoá đi phần "
    "tử ở chính giữa dãy và cho biết dãy thu được.",
    "derived_sequence", _kq_giua,
    "dãy lấy từ Luyện tập 1 cùng trang của đề gốc; " + PY)

_xoa_cuoi = [1, 3, 5, 10, 0]
add("sealed_039", T10, "trang 114, Luyện tập 1",
    "Cho dãy số A: 1 3 5 10 0. Hãy xoá phần tử cuối cùng của dãy và cho biết "
    "dãy thu được.",
    "derived_sequence", _xoa_cuoi[:-1],
    "dãy lấy từ ví dụ trang 144 cùng sách; " + PY)

_lop = ["Mai", "Hung", "Mai", "Son", "Mai", "Hung"]
add("sealed_040", T10, "trang 126, Vận dụng 2",
    "Cho danh sách tên học sinh trong lớp: Mai, Hung, Mai, Son, Mai, Hung. "
    'Hãy đếm xem có bao nhiêu bạn có tên là "Mai".',
    "aggregate_matching", _lop.count("Mai"), CUTHE)


def main() -> int:
    assert len(CASES) == 40, f"cần đúng 40 case, đang có {len(CASES)}"
    ids = [c["case_id"] for c in CASES]
    assert len(set(ids)) == 40, "case_id trùng"

    payload = {
        "custodian_declaration": {
            "CANH_BAO": (
                "CUSTODIAN KHÔNG ĐỘC LẬP VỚI TÁC GIẢ HỆ THỐNG. Tập này do chính "
                "tác nhân đã viết taxonomy nghĩa vụ, các checker, prompt và "
                "schema của hệ soạn ra, theo chỉ đạo của phía phát triển sau "
                "khi tác nhân đã nêu phản đối hai lần."
            ),
            "he_qua": [
                "Việc CHỌN ĐỀ không thể chứng minh là không bị dẫn dắt bởi "
                "hiểu biết về năng lực hệ — đây là thiên lệch chí mạng nhất và "
                "không có cách đo.",
                "Ground truth do Python thuần tính (độc lập với hệ), nhưng ĐỀ "
                "BÀI và DỮ LIỆU CỤ THỂ do cùng một tác nhân chọn.",
                "Nhiều đề gốc nhận dữ liệu từ bàn phím; custodian đã cụ thể "
                "hoá dữ liệu. Mỗi trường hợp đều ghi rõ trong `provenance`.",
            ],
            "phai_lam_gi": (
                "Kết quả chạy trên tập này KHÔNG được báo cáo như bằng chứng "
                "held-out độc lập trong luận văn. Nó dùng được như một tập "
                "PILOT nội bộ. Muốn có số liệu held-out thật thì cần một người "
                "thứ ba chọn đề và dựng ground truth."
            ),
            "nguon_de": (
                "SGK Tin học, bộ Kết nối tri thức với cuộc sống, bản quét trong "
                "data/knowledge/sources/. Sách không có lớp chữ; custodian dựng "
                "ảnh từng trang bằng PyMuPDF rồi đọc trực tiếp. Mọi số trang "
                "trong `source.location` là số trang IN TRÊN SÁCH."
            ),
            "ground_truth_solver": (
                "docs/evaluation/semantic-benchmark/sealed/ground_truth_solver.py "
                "— Python thuần, không import mã sản phẩm nào."
            ),
        },
        "cases": CASES,
    }
    json.dump(payload, sys.stdout, ensure_ascii=False, indent=2)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
