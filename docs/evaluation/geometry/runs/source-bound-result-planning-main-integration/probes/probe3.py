import sys; sys.path.insert(0, ".")
from app.ai.function_route import run_fact_route
from tests.geometry import hybrid_compiler_benchmark as HB
ask=HB._ask; MID=HB._mid("f5","M","S","C")
DPP=lambda s: ask("q",s,"distance",points_a=["S"],points_b=list("ABCD"))
VOL=lambda s: ask("q",s,"volume",solid="S.ABCD")
LEN=lambda s: ask("q",s,"length",points=list("SC"))
SAREA=lambda s: ask("q",s,"area",solid="S.ABCD",points=list("MAB"))
def run(src, qf, quote=None, mid=False):
    q, fs = HB._square()
    if mid: q, fs = q+[MID["quotes"][0]], fs+[MID]
    r = run_fact_route(" ".join(q)+" "+src, {"facts": fs+[qf(quote or src)]})
    return r.status, r.code, r.answers
for src, qf, quote, mid in [
    ("Tính bình phương khoảng cách từ S đến (ABCD).", DPP, None, False),
    ("Tính bình phương khoảng cách từ S đến (ABCD).", DPP, "Tính bìnhphương khoảng cách từ S đến (ABCD).", False),
    ("Tính nửa thể tích khối chóp S.ABCD.", VOL, "Tính nửathể tích khối chóp S.ABCD.", False),
    ("Tính nửa độ dài SC.", LEN, None, False),
    ("Tính bình phương độ dài SC.", LEN, None, False),
    ("Tính nửa diện tích thiết diện của hình chóp S.ABCD cắt bởi (MAB).", SAREA, None, True),
    ("Tính bình phương diện tích thiết diện của hình chóp S.ABCD cắt bởi (MAB).", SAREA, None, True),
    ("Tính diện tích thiết diện của hình chóp S.ABCD cắt bởi (MAB).", SAREA, None, True),
    ("Tính hai lần khoảng cách từ S đến (ABCD).", DPP, None, False),
]:
    print(repr(src), "quote=", repr(quote), run(src, qf, quote, mid))
