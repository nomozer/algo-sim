"""Final pass: hunt FALSE SERVES only."""
from tests.geometry import hybrid_compiler_benchmark as HB
from app.ai.function_route import run_fact_route
f, ask = HB._f, HB._ask
MID = HB._mid("f5", "M", "S", "C")


def show(tag, s, r):
    if r.status == "SERVED":
        print(f"!! {tag:5s} {s[:100]:102s} SERVED {r.answers}")
    else:
        print(f"   {tag:5s} {s[:100]:102s} {r.code}")


def no_perp():
    q, fs = HB._square(); return [q[0], q[1], q[3]], [fs[0], fs[1], fs[3]]


def no_len():
    q, fs = HB._square(); return q[:3], fs[:3]


SC = ask("q", "Tính độ dài SC.", "length", points=["S", "C"])

for s, qt in [("Hễ SA vuông góc với (ABCD) là SC = 5.", "SA vuông góc với (ABCD)"),
              ("Tìm điều kiện để SA vuông góc với (ABCD).", "SA vuông góc với (ABCD)"),
              ("Hãy chỉ ra rằng SA vuông góc với (ABCD).", "SA vuông góc với (ABCD)"),
              ("Ta sẽ chỉ ra SA vuông góc với (ABCD).", "SA vuông góc với (ABCD)"),
              ("Giải thích vì sao SA vuông góc với (ABCD).", "SA vuông góc với (ABCD)"),
              ("Tại sao SA vuông góc với (ABCD)?", "SA vuông góc với (ABCD)"),
              ("Liệu SA có vuông góc với (ABCD)?", "SA có vuông góc với (ABCD)"),
              ("SA vuông góc với (ABCD) hoặc SB vuông góc với (ABCD).", "SA vuông góc với (ABCD)"),
              ("SA có thể vuông góc với (ABCD).", "SA có thể vuông góc với (ABCD)"),
              ("SA không hề vuông góc với (ABCD).", "SA không hề vuông góc với (ABCD)"),
              ("SA không nhất thiết vuông góc với (ABCD).", "SA không nhất thiết vuông góc với (ABCD)"),
              ("Không đúng là SA vuông góc với (ABCD).", "SA vuông góc với (ABCD)"),
              ("SA chẳng vuông góc với (ABCD).", "SA chẳng vuông góc với (ABCD)"),
              ("Xét trường hợp SA vuông góc với (ABCD).", "SA vuông góc với (ABCD)"),
              ("Cho rằng SA vuông góc với (ABCD), tìm lỗi sai.", "SA vuông góc với (ABCD)"),
              ("Bạn An khẳng định SA vuông góc với (ABCD).", "SA vuông góc với (ABCD)"),
              ("Kiểm chứng rằng SA vuông góc với (ABCD).", "SA vuông góc với (ABCD)"),
              ("Muốn SA vuông góc với (ABCD) cần SA ⊥ AB.", "SA vuông góc với (ABCD)")]:
    q, fs = no_perp()
    text = " ".join(q) + " " + s + " Tính độ dài SC."
    r = run_fact_route(text, {"facts": fs + [f("f9", "perpendicular", qt, points_a=["S", "A"], points_b=list("ABCD")), SC]})
    show("PERP", s, r)
for s, qt, v in [("SA ≥ 3.", "SA ≥ 3.", "3"), ("SA > 3.", "SA > 3.", "3"), ("SA ≈ 3.", "SA ≈ 3.", "3"),
                 ("SA không bằng 4.", "SA không bằng 4.", "4"), ("SA ≠ 4.", "SA ≠ 4.", "4"),
                 ("SA bằng 3 lần AB.", "SA bằng 3 lần AB.", "3"), ("SA lớn hơn 3.", "SA lớn hơn 3.", "3"),
                 ("SA = 3 hoặc SA = 4.", "SA = 3", "3"), ("SA xấp xỉ 3.", "SA xấp xỉ 3.", "3"),
                 ("SA tối đa bằng 3.", "SA tối đa bằng 3.", "3"), ("SA = 3 là sai.", "SA = 3", "3"),
                 ("Độ dài SA bằng 3 khi M trùng S.", "Độ dài SA bằng 3", "3")]:
    q, fs = no_len()
    text = " ".join(q) + " " + s + " Tính độ dài SC."
    r = run_fact_route(text, {"facts": fs + [f("f9", "length", qt, points=["S", "A"], measure="segment", value=v), SC]})
    show("LEN", s, r)


def runq(s, qf, mid=False):
    q, fs = HB._square()
    if mid:
        q, fs = q + [MID["quotes"][0]], fs + [MID]
    return run_fact_route(" ".join(q) + " " + s, {"facts": fs + [qf]})


DPP = lambda s: ask("q", s, "distance", points_a=["S"], points_b=list("ABCD"))
VOL = lambda s: ask("q", s, "volume", solid="S.ABCD")
LEN = lambda s: ask("q", s, "length", points=["S", "C"])
for s, qf in [("Thể tích khối chóp S.ABCD có vượt quá 5 không?", VOL),
              ("Thể tích khối chóp S.ABCD có đúng là 4 không?", VOL),
              ("Liệu thể tích khối chóp S.ABCD có thể là 5?", VOL),
              ("Thể tích khối chóp S.ABCD bằng 4 phải không?", VOL),
              ("Tính bình phương khoảng cách từ S đến (ABCD).", DPP),
              ("Tính nửa thể tích khối chóp S.ABCD.", VOL),
              ("Tính hai lần thể tích khối chóp S.ABCD.", VOL),
              ("Tính thể tích phần còn lại của khối chóp S.ABCD sau khi cắt bởi (MAB).", VOL),
              ("Tính thể tích khối chóp M.ABCD.", VOL),
              ("Tính thể tích khối chóp S.ABC.", VOL),
              ("Tính khoảng cách từ A đến (SBC).", DPP),
              ("Tính khoảng cách từ trung điểm của SC đến (ABCD).", DPP),
              ("Tính khoảng cách từ M đến (ABCD).", DPP),
              ("Tính SC rồi so sánh với khoảng cách từ S đến (ABCD).", DPP),
              ("Tính SC + khoảng cách từ S đến (ABCD).", DPP),
              ("Tính độ dài SM.", LEN),
              ("Tính độ dài hình chiếu của SC lên (ABCD).", LEN),
              ("Tính chu vi tam giác SAC.", LEN),
              ("Tính độ dài trung tuyến SC của tam giác SBD.", LEN),
              ("Tính SC, ở đây khoảng cách từ S đến (ABCD) gấp đôi SB.", DPP),
              ("Tính SC theo khoảng cách từ S đến (ABCD).", DPP),
              ("Tính tỉ số giữa SC và khoảng cách từ S đến (ABCD).", DPP),
              ("Tìm M sao cho khoảng cách từ S đến (ABCD) nhỏ nhất?", DPP),
              ("Hỏi khoảng cách từ S đến (ABCD) có bằng 3 không?", DPP),
              ("Tính giá trị lớn nhất của khoảng cách từ S đến (ABCD).", DPP),
              ("Tính khoảng cách từ S đến (ABCD) khi M thay đổi.", DPP),
              ("Tính khoảng cách từ S đến (ABCD) sau khi tăng SA lên gấp đôi.", DPP),
              ("Tính SC. Biết khoảng cách từ S đến (ABCD)?", DPP),
              ("Tính sin góc giữa SC và (ABCD).", lambda s: ask("q", s, "angle", points_a=["S", "C"], points_b=list("ABCD")))]:
    show("ASK", s, runq(s, qf(s), mid="M" in s))

SEC = lambda s, pl: f("q", "section", s, role="question", solid="S.ABCD", points=list(pl))
AR = lambda s, pl: ask("q", s, "area", solid="S.ABCD", points=list(pl))
for s, fn, pl in [("Xác định thiết diện của hình chóp S.ABCD cắt bởi mặt phẳng (P) song song với (MAB).", SEC, "MAB"),
                  ("Xác định thiết diện của hình chóp S.ABCD cắt bởi mặt phẳng (P) chứa AB và vuông góc với (MAB).", SEC, "MAB"),
                  ("Tính diện tích thiết diện của hình chóp S.ABCD cắt bởi (MAB), biết diện tích thiết diện cắt bởi (SAC) bằng 3√2.", AR, "SAC"),
                  ("Tính diện tích thiết diện của hình chóp S.ABCD cắt bởi (SAC) rồi so sánh với thiết diện cắt bởi (MAB).", AR, "MAB"),
                  ("Tính tỉ số diện tích thiết diện của hình chóp S.ABCD cắt bởi (MAB) và diện tích đáy.", AR, "MAB"),
                  ("Tính diện tích thiết diện lớn nhất của hình chóp S.ABCD cắt bởi (MAB) khi M chạy trên SC.", AR, "MAB"),
                  ("Tính diện tích hình chiếu của thiết diện của hình chóp S.ABCD cắt bởi (MAB) lên đáy.", AR, "MAB"),
                  ("Mặt phẳng (MAB) không cắt hình chóp S.ABCD theo thiết diện nào.", SEC, "MAB"),
                  ("Giả sử mặt phẳng (MAB) cắt hình chóp S.ABCD theo một thiết diện.", SEC, "MAB"),
                  ("Tính diện tích thiết diện của khối lập phương cắt bởi (MAB).", AR, "MAB"),
                  ("Tính diện tích thiết diện của hình chóp S.ABCD với mặt phẳng (MAB) song song với CD.", AR, "MAB"),
                  ("Tính diện tích thiết diện với mặt phẳng (MAB) của hình chóp S.ABCD.", AR, "MAB"),
                  ("Tính diện tích thiết diện của hình chóp S.ABCD cắt bởi (MAB) khi SA tăng gấp đôi.", AR, "MAB")]:
    show("SEC", s, runq(s, fn(s, pl), mid=True))
LN = lambda s, a, b: f("q", "intersection_line", s, role="question", points_a=list(a), points_b=list(b))
for s, a, b in [("Chứng minh giao tuyến của (SAB) và (SCD) song song với AB.", "SAB", "SCD"),
                ("Nếu giao tuyến của (SAB) và (SCD) song song với AB thì SA = 3.", "SAB", "SCD"),
                ("Tìm giao tuyến của (SAB) và mặt phẳng (P) song song với (SCD).", "SAB", "SCD"),
                ("Tìm giao tuyến của (SAB) với mặt phẳng qua M song song với (SCD).", "SAB", "SCD"),
                ("Tìm giao tuyến của (SAB) và (SCD) với (SBC).", "SCD", "SBC"),
                ("Tìm giao điểm của (SAB) và (SCD).", "SAB", "SCD"),
                ("Giao tuyến của (SAB) và (SCD) không song song với AB.", "SAB", "SCD")]:
    show("GT", s, runq(s, LN(s, a, b), mid=True))
