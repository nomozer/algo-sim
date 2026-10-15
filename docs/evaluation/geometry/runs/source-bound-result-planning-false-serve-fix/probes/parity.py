import sys; sys.path.insert(0, ".")
from app.ai.function_route import run_fact_route
from tests.geometry import hybrid_compiler_benchmark as HB
for s, fact in [("Tính khoảng cách từ S đến (ABCD) và nửa chu vi đáy.", HB._ask("q", "Tính khoảng cách từ S đến (ABCD) và nửa chu vi đáy.", "distance", points_a=["S"], points_b=list("ABCD"))),
                ("Tính độ dài SC và nửa chu vi đáy.", HB._ask("q", "Tính độ dài SC và nửa chu vi đáy.", "length", points=list("SC"))),
                ("Tính khoảng cách từ S đến (ABCD) và chu vi đáy.", HB._ask("q", "Tính khoảng cách từ S đến (ABCD) và chu vi đáy.", "distance", points_a=["S"], points_b=list("ABCD")))]:
    q, f = HB._with(HB._square(), fact)
    r = run_fact_route(" ".join(q), {"facts": f}); print(repr(s), r.status, r.code)
