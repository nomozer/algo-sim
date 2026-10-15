import os, sys, json
os.environ["ALLOW_LIVE_AI"]="0"; sys.path.insert(0,".")
from app.ai.function_route import run_fact_route
from tests.geometry import hybrid_compiler_benchmark as HB
def run(qs):
    base = ["Cho hình chóp S.ABCD.", "Đáy ABCD là hình vuông cạnh 2 cm.", "SA vuông góc với (ABCD).", "SA = 3 cm."]
    f = [HB._f("f1","solid",base[0],solid="S.ABCD",solid_type="pyramid"),
         HB._f("f2","polygon_shape",base[1],points=list("ABCD"),shape="square",value="2"),
         HB._f("f3","perpendicular",base[2],points_a=["S","A"],points_b=list("ABCD")),
         HB._f("f4","length",base[3],points=["S","A"],measure="segment",value="3"),
         HB._f("q","question",qs,role="question",quantity="length",points=["S","C"])]
    r = run_fact_route(" ".join(base+[qs]), {"facts": f})
    print(r.status, r.code, r.answers, repr(qs))
for s in ["Tính độ dài SC.", "Tính độ dài SC (đơn vị: mm).", "Tính độ dài SC theo đơn vị mm.", "Tính độ dài SC (mm).", "Tính độ dài SC (đơn vị m).", "Tính độ dài SC (dm; làm tròn đến hàng phần trăm)."]:
    run(s)
