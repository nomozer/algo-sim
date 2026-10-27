"""Additive adversarial controls; never rewrites the locked development corpus."""
from copy import deepcopy
import json
from pathlib import Path
from build_development import replace_source

RUN = Path(__file__).resolve().parents[1]
cs=json.loads((RUN/"inputs/development.json").read_text(encoding="utf-8"))["cases"]
base=deepcopy(next(c for c in cs if c["id"]=="DEV-4-2"))
base["payload"]["problem_text"] += " Biết AC vuông góc với BC."
base.update(id="ADD-contradictory-two-line-premise",expected_status="REFUSED",
            expected_codes=["SOURCE_PREMISE_UNREAD","SOURCE_OBJECT_MISMATCH","INCONSISTENT_FACTS"])
base.pop("oracle")
cases=[base]
for verb in ("là","trùng với"):
    p=deepcopy(next(c for c in cs if c["id"]=="DEV-4-2"))
    q=f"Hình chiếu vuông góc của B trên mặt phẳng (A'B'C') {verb} đỉnh A'"
    p["payload"]["problem_text"] += " "+q+"."
    p["payload"]["premises"].append(dict(kind="orthogonal_projection",
        args=dict(point="B",image="A'",plane=["A'","B'","C'"]),quote=q))
    p["id"]="ADD-primed-target-"+verb.replace(" ","-")
    cases.append(p)
p=deepcopy(next(c for c in cs if c["id"]=="DEV-4-2"))
q="Gọi J là trung điểm của AB"
p["payload"]["problem_text"] += " "+q+"."
p["payload"]["premises"].append(dict(kind="midpoint",args=dict(point="J",segment=["A","B"]),quote=q))
replace_source(p["payload"],"đỉnh B","đỉnh J")
next(f for f in p["payload"]["premises"] if f["kind"]=="orthogonal_projection")["args"]["image"]="J"
next(f for f in p["payload"]["premises"] if f["kind"]=="segment_length" and f["args"]["segment"]==["A'","B"])["args"]["segment"]=["A'","J"]
replace_source(p["payload"],"A'B = 10","A'J = 10")
p.update(id="ADD-midpoint-is-not-vertex",expected_status="REFUSED",
         expected_codes=["SOURCE_OBJECT_MISMATCH","SOURCE_PREMISE_UNREAD"])
p.pop("oracle")
cases.append(p)
for name,tail in [("unread-tail",", với SB = SC"),("negated"," không"),("conditional"," nếu SB = SC")]:
    p=deepcopy(next(c for c in cs if c["id"]=="DEV-1-2"))
    f=next(f for f in p["payload"]["premises"] if f["kind"]=="divide_segment")
    replace_source(p["payload"],f["quote"],f["quote"]+tail)
    p.update(id="ADD-"+name,expected_status="REFUSED",expected_codes=[
        "SOURCE_PREMISE_UNREAD","SOURCE_OBJECT_MISMATCH","NEGATED_CLAUSE","CONDITIONAL_CLAUSE"])
    p.pop("oracle")
    cases.append(p)
out=RUN/"inputs/supplemental.json"
with out.open("x",encoding="utf-8") as f:
    f.write(json.dumps(dict(classification="ADDITIVE_DEVELOPMENT_CONTROLS",cases=cases),ensure_ascii=False,indent=2)+"\n")
print(len(cases))
