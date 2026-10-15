import sys; sys.path.insert(0, ".")
from app.ai.function_route import run_fact_route
from tests.geometry import hybrid_compiler_benchmark as HB
def run(sent, quote=None):
    q, f = HB._with(HB._square(), HB._f("q", "question", quote or sent, role="question", quantity="length", points=["S", "C"]))
    r = run_fact_route(" ".join(q + ([sent] if quote else [])) if quote else " ".join(q), {"facts": f})
    print(r.status, r.code, r.answers, repr(sent))
for s in ["Chứng minh BD ⊥ SC; kết quả lấy bình phương; tính độ dài SC.",
          "Chứng minh BD ⊥ SC, nhân đôi kết quả và tính độ dài SC.",
          "Tính độ dài SC rồi suy ra đáp số là bình phương của nó."]:
    run(s)
for s in ["Tính độ dài SC. Hãy tính kết quả dưới dạng bình phương.", "Tính độ dài SC. Đáp số nhân đôi, biết SA = 3."]:
    run(s, quote="Tính độ dài SC.")
