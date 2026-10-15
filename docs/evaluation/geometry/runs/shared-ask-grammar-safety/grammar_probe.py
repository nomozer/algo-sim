"""Preregistered probe set for the shared ask-grammar safety wave (run `shared-ask-grammar-safety`).

Run with cwd = <checkout>/backend:  python <this file> <out.json>
0 model calls: Route B uses supplied Typed Facts, Route A replays planner calls with the probe text substituted.
Each case declares the expected outcome BEFORE the fix; the classification is WRONG_SERVED / CORRECT_SERVED /
CORRECT_REFUSAL / FALSE_REFUSAL against that expectation.
"""
import json
import os
import sys

os.environ.setdefault("ALLOW_LIVE_AI", "0")
sys.path.insert(0, ".")
from app.ai.function_route import run_fact_route, run_function_route  # noqa: E402
from tests.geometry import hybrid_compiler_benchmark as HB  # noqa: E402

OBJ = {  # object phrase, ask fact kwargs, served value on the square pyramid (side 2, SA = 3 ⟂ base)
    "line": ("khoảng cách từ S đến BD", dict(quantity="distance", points_a=["S"], points_b=["B", "D"]), "√11"),
    "plane": ("khoảng cách từ S đến (ABCD)", dict(quantity="distance", points_a=["S"], points_b=list("ABCD")), "3"),
    "length": ("độ dài SC", dict(quantity="length", points=["S", "C"]), "√17"),
}
S, R = "SERVED", "REFUSED"

# (id, group, sentence template with {O}, expected) — groups: W false serve, P positive control, C role, D transform
TEMPLATES = [
    ("W1", "W", "Nhân đôi kết quả, tính {O}.", R),
    ("W2", "W", "Hai lần của đại lượng sau bằng bao nhiêu: {O}?", R),
    ("W3", "W", "Bình phương của đại lượng sau bằng bao nhiêu: {O}?", R),
    ("W4", "W", "Đáp số là bình phương của kết quả; tính {O}.", R),
    ("W5", "W", "Lấy bình phương, tính {O}.", R),
    ("W6", "W", "Một nửa của đại lượng sau là bao nhiêu: {O}?", R),
    ("W7", "W", "Đề hỏi bình phương; hãy tính {O}.", R),
    ("W8", "W", "Gấp ba kết quả rồi tính {O}.", R),
    ("W9", "W", "Tính {O} (kết quả nhân đôi).", R),
    ("W10", "W", "Tính {O} (kết quả lấy bình phương).", R),
    ("W11", "W", "Tính {O} (kết quả gấp đôi).", R),
    ("W12", "W", "Tính {O} (kết quả ghi dưới dạng bình phương).", R),
    ("W13", "W", "Tính {O} (đơn vị: một nửa cm).", R),
    ("W14", "W", "Tính {O} (đơn vị: cm, kết quả bình phương).", R),
    ("W15", "W", "Tính {O} (làm tròn sau khi nhân đôi).", R),
    ("W16", "W", "Tính {O} (kết quả bằng 3).", R),
    ("W17", "W", "Tính {O} (kết quả 3).", R),
    ("W18", "W", "Tính {O} (kết quả có lớn hơn 3 không).", R),
    ("P1", "P", "Tính {O}.", S),
    ("P2", "P", "Hơn nữa, tính {O}.", S),
    ("P3", "P", "{O} bằng bao nhiêu?", S),
    ("P4", "P", "Hãy tính {O}.", S),
    ("P5", "P", "Tính {O} (làm tròn đến hàng phần trăm).", S),
    ("P6", "P", "Tính {O} (đơn vị: cm).", S),
    ("P7", "P", "Tính {O} (kết quả làm tròn đến hàng phần mười).", S),
    ("P8", "P", "Khi đó, tính {O}.", S),
    ("P9", "P", "Tìm {O}.", S),
    ("P10", "P", "Hỏi {O} bằng bao nhiêu?", S),
    ("C1", "C", "Nếu SA = 4 thì tính {O}.", R),
    ("C2", "C", "Chứng minh rằng {O} bằng 4.", R),
    ("C3", "C", "Giả sử SA = 4, tính {O}.", R),
    ("C4", "C", "Tính {O} khi SA = 4.", R),
    ("D1", "D", "Tính {O} bình phương.", R),
    ("D2", "D", "Tính căn bậc hai của {O}.", R),
    ("D3", "D", "Tính 1/2 {O}.", R),
    ("D4", "D", "Tính hai lần {O}.", R),
]


def _cap(s):
    return s[0].upper() + s[1:]


def route_b(text, facts):
    r = run_fact_route(text, {"facts": facts})
    return r.status, r.code, r.answers, r


def classify(expected, status, answers, value):
    if status == S:
        return "CORRECT_SERVED" if expected == S and value in (answers or {}).values() else "WRONG_SERVED"
    return "CORRECT_REFUSAL" if expected == R else "FALSE_REFUSAL"


def cases():
    out = []
    base_q, base_f = HB._square()
    for kind, (phrase, kw, value) in OBJ.items():
        for cid, group, tpl, exp in TEMPLATES:
            sentence = _cap(tpl.format(O=phrase))
            q, f = HB._with((base_q, base_f), HB._f("q", "question", sentence, role="question", **kw))
            out.append({"id": f"{cid}-{kind}", "group": group, "route": "B", "text": " ".join(q), "facts": f,
                        "expected": exp, "value": value})
        # Same-sentence premise before the question (P11): read by its own fact quote.
        sent = f"Gọi M là trung điểm SC, tính {phrase}."
        q, f = HB._with((base_q, base_f))
        f = f + [HB._f("f5", "point_def", "Gọi M là trung điểm SC", point="M", point_kind="midpoint", points=["S", "C"]),
                 HB._f("q", "question", f"tính {phrase}.", role="question", **kw)]
        out.append({"id": f"P11-{kind}", "group": "P", "route": "B", "text": " ".join(q + [sent]), "facts": f,
                    "expected": S, "value": value})
        # Whole problem in one sentence (P12).
        one = (f"Cho hình chóp S.ABCD có đáy ABCD là hình vuông cạnh 2, SA vuông góc với (ABCD) và SA = 3, "
               f"tính {phrase}.")
        f = [HB._f("f1", "solid", "Cho hình chóp S.ABCD", solid="S.ABCD", solid_type="pyramid"),
             HB._f("f2", "polygon_shape", "đáy ABCD là hình vuông cạnh 2", points=list("ABCD"), shape="square", value="2"),
             HB._f("f3", "perpendicular", "SA vuông góc với (ABCD)", points_a=["S", "A"], points_b=list("ABCD")),
             HB._f("f4", "length", "SA = 3", points=["S", "A"], measure="segment", value="3"),
             HB._f("q", "question", f"tính {phrase}.", role="question", **kw)]
        out.append({"id": f"P12-{kind}", "group": "P", "route": "B", "text": one, "facts": f, "expected": S, "value": value})
    # Reused foot (effect_binding, source-defined H) — IMPORTANT-1 of review-2427289a and its controls.
    proj = HB._proj("f5", "H", "S", "BD")
    for cid, src, quote, exp in [
            ("Q1", "Tính hai lần.khoảng cách từ S đến BD?", "hai lần. khoảng cách từ S đến BD?", R),
            ("Q2", "Tính khoảng cách từ S đến BD.", "Tính khoảng cách từ S đến BD.", S),
            ("Q3", "Tính khoảng cách từ S đến BD.", "Tính khoảngcách từ S đến BD.", S),
            ("Q4", "Nhân đôi kết quả, tính khoảng cách từ S đến BD.", "tính khoảng cách từ S đến BD.", R),
            ("Q5", "Tính khoảng cách từ S đến BD (kết quả nhân đôi).", "khoảng cách từ S đến BD", R),
            ("Q6", "Tính bình phương khoảng cách từ S đến BD.", "khoảng cách từ S đến BD.", R)]:
        q, f = HB._with(HB._square(), proj)
        f = f + [HB._f("q", "question", quote, role="question", **OBJ["line"][1])]
        out.append({"id": f"{cid}-reused-foot", "group": "Q", "route": "B", "text": " ".join(q + [src]), "facts": f,
                    "expected": exp, "value": "√11"})
    # Auxiliary (fresh foot) with substituted quotes.
    for cid, src, quote, exp in [
            ("Q7", "Tính hai lần khoảng cách từ S đến BD.", "khoảng cách từ S đến BD.", R),
            ("Q8", "Nhân đôi kết quả, tính khoảng cách từ S đến BD.", "tính khoảng cách từ S đến BD.", R),
            ("Q9", "Tính khoảng cách từ S đến BD.", "Tính khoảngcách từ S đến BD.", S)]:
        q, f = HB._with(HB._square())
        f = f + [HB._f("q", "question", quote, role="question", **OBJ["line"][1])]
        out.append({"id": f"{cid}-aux", "group": "Q", "route": "B", "text": " ".join(q + [src]), "facts": f,
                    "expected": exp, "value": "√11"})
    return out


def route_a_cases():
    """Route A replays the planner's calls for the plain question with the probe sentence substituted in text and quotes."""
    out = []
    base_q, base_f = HB._square()
    for kind, (phrase, kw, value) in OBJ.items():
        if kind == "line":
            continue  # Route A may not introduce an auxiliary foot (test_route_a_cannot_introduce_an_auxiliary): by design
        plain = _cap(f"tính {phrase}.")
        q, f = HB._with((base_q, base_f), HB._f("q", "question", plain, role="question", **kw))
        r = run_fact_route(" ".join(q), {"facts": f})
        if r.status != S:
            out.append({"id": f"A-setup-{kind}", "outcome": "SETUP_FAILED", "code": r.code})
            continue
        calls = r.planner["calls"]
        for cid, group, tpl, exp in TEMPLATES:
            sentence = _cap(tpl.format(O=phrase))
            text = " ".join(q).replace(plain, sentence)
            sub = json.loads(json.dumps(calls, ensure_ascii=False).replace(json.dumps(plain, ensure_ascii=False)[1:-1],
                                                                           json.dumps(sentence, ensure_ascii=False)[1:-1]))
            ra = run_function_route(text, {"calls": sub})
            out.append({"id": f"{cid}-{kind}", "group": group, "route": "A", "expected": exp, "status": ra.status,
                        "code": ra.code, "answers": ra.answers,
                        "outcome": classify(exp, ra.status, ra.answers, value)})
    return out


def main(path):
    rows = []
    for c in cases():
        st, code, ans, _r = route_b(c["text"], c["facts"])
        rows.append({"id": c["id"], "group": c["group"], "route": "B", "expected": c["expected"], "status": st,
                     "code": code, "answers": ans, "outcome": classify(c["expected"], st, ans, c["value"])})
    rows += route_a_cases()
    summary = {}
    for r in rows:
        summary.setdefault(r["route"], {}).setdefault(r["outcome"], 0)
        summary[r["route"]][r["outcome"]] += 1
    with open(path, "w", encoding="utf-8") as fh:
        json.dump({"summary": summary, "rows": rows}, fh, ensure_ascii=False, indent=1)
    print(json.dumps(summary, ensure_ascii=False))
    for r in rows:
        if r["outcome"] in ("WRONG_SERVED", "FALSE_REFUSAL", "SETUP_FAILED"):
            print(r["outcome"], r["route"], r["id"], r.get("code"))


if __name__ == "__main__":
    main(sys.argv[1])
