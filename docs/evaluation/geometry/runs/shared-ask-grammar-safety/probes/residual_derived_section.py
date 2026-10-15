import os, sys
os.environ["ALLOW_LIVE_AI"]="0"; sys.path.insert(0,".")
from app.ai.function_route import run_fact_route
from tests.geometry.test_goal_directed_section_planning import _pyramid_problem
OLD = "Tính diện tích thiết diện của hình chóp S.ABCD với (P)."
for new in [OLD,
            "Xác định thiết diện của hình chóp S.ABCD với (P) và tính diện tích thiết diện đó.",
            "Xác định thiết diện của hình chóp S.ABCD với (P), rồi tính diện tích thiết diện của hình chóp S.ABCD với (P).",
            "Xác định thiết diện của hình chóp S.ABCD với (P). Tính diện tích thiết diện của hình chóp S.ABCD với (P).",
            "Nhân đôi kết quả, tính diện tích thiết diện của hình chóp S.ABCD với (P).",
            "Tính diện tích thiết diện của hình chóp S.ABCD với (P). Hãy tính kết quả nhân đôi.",
            "Chứng minh SA ⊥ BD, nhân đôi kết quả và tính diện tích thiết diện của hình chóp S.ABCD với (P).",
            "a) Tính diện tích thiết diện của hình chóp S.ABCD với (P) (làm tròn đến hàng phần trăm)."]:
    text, payload = _pyramid_problem()
    assert OLD in text
    text = text.replace(OLD, new)
    for f in payload["facts"]:
        f["quotes"] = [new if x == OLD else x for x in f["quotes"]]
    r = run_fact_route(text, payload)
    print(r.status, r.code, r.answers, repr(new))
