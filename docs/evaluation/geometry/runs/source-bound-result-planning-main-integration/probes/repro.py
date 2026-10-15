import sys
sys.path.insert(0, ".")
from app.ai.function_route import run_fact_route
from tests.geometry import hybrid_compiler_benchmark as HB
def aux(src, quote):
    q, f = HB._with(HB._square(), HB._ask("q", quote, "distance", points_a=["S"], points_b=["B", "D"]))
    text = " ".join(q).replace(quote, src)
    r = run_fact_route(text, {"facts": f})
    return r.status, r.code, r.answers
for src, quote in [("Tính khoảng cách từ S đến BD.",)*2,
                   ("Tính hai lần khoảng cách từ S đến BD.",)*2,
                   ("Tính khoảng cách từ S đến BD bình phương.",)*2,
                   ("Tính bình phương khoảng cách từ S đến BD.", "Tính bìnhphương khoảng cách từ S đến BD.")]:
    print(repr(src), "| quote", repr(quote), "->", aux(src, quote))
