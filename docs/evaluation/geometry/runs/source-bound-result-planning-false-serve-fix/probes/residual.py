import sys; sys.path.insert(0, ".")
from app.ai.function_route import run_fact_route
from tests.geometry import hybrid_compiler_benchmark as HB
C1 = ["Đáp số là bình phương của kết quả; tính khoảng cách từ S đến BD.", "Lấy bình phương, tính khoảng cách từ S đến BD.",
      "Bình phương của đại lượng sau bằng bao nhiêu: khoảng cách từ S đến BD?", "Một nửa của đại lượng sau là bao nhiêu: khoảng cách từ S đến BD?",
      "Đề hỏi bình phương; hãy tính khoảng cách từ S đến BD.", "Hai lần của đại lượng sau bằng bao nhiêu: khoảng cách từ S đến BD?",
      "Nhân đôi kết quả, tính khoảng cách từ S đến BD."]
C2 = [f"Tính khoảng cách từ S đến BD ({x})." for x in ["kết quả nhân đôi", "kết quả lấy bình phương", "kết quả gấp đôi",
      "kết quả ghi dưới dạng bình phương", "đơn vị: một nửa cm", "đơn vị: cm, kết quả bình phương"]]
for tag, xs in (("C1", C1), ("C2", C2)):
    for s in xs:
        q, f = HB._with(HB._square(), HB._ask("q", s, "distance", points_a=["S"], points_b=["B", "D"]))
        r = run_fact_route(" ".join(q), {"facts": f}); print(tag, repr(s), r.status, r.code, r.answers)
