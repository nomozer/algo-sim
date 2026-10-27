"""Interpret a proved authored-label error, retaining all preregistered inputs and raw scores."""
from copy import deepcopy
from fractions import Fraction as F
import hashlib
import json
from pathlib import Path
from evaluate_development import RUN, evaluate_case

corpus=json.loads((RUN/"inputs/development.json").read_text(encoding="utf-8"))
c=deepcopy(next(c for c in corpus["cases"] if c["id"]=="NEG-unproven-two-line-premise"))
# Independent review's orthonormal coordinate witness, not engine coordinates.
a,b,d=(F(0),F(0),F(0)),(F(12),F(0),F(0)),(F(0),F(18),F(0))
dot=sum((b[i]-a[i])*(d[i]-a[i]) for i in range(3))
assert dot==0
area_squared=F(12*18,2)**2
t=F(4,9)
oracle=dict(solid="ABC.A'B'C'",section_id="sec",area_goal_id="area",
            vertex_count=3,expected_certificate_category="ENGINE_DERIVED_SECTION",
            area_squared=str(area_squared),boundary=[dict(edge=[x,x+"'"],t=str(t)) for x in "ABC"])
c.update(expected_status="SERVED",oracle=oracle)
row=evaluate_case(c)
assert row["outcome"]=="SERVED_CORRECT"
raw=json.loads((RUN/"results/green-after.json").read_text(encoding="utf-8"))
hashes={f:hashlib.sha256((RUN/f).read_bytes().replace(b"\r\n",b"\n")).hexdigest() for f in [
    "inputs/development.json","results/red-before.json","results/green-attempt1.json","results/green-after.json"]}
receipt=dict(classification="DEVELOPMENT_CORPUS_ADJUDICATION_NOT_HOLDOUT",
             basis="Independent review review-first-pass.md; exact coordinate witness",
             raw_preserved_lf_sha256=hashes,
             cases={c["id"]:dict(raw_expected_status="REFUSED",adjudicated_expected_status="SERVED",
                 expected_oracle=oracle,mathematical_reason="The extra AC perpendicular AB assertion is precisely angle BAC=90 already in the source.",
                 execution=row)},
             raw_green_overall=raw["overall"],
             adjudicated=dict(original_positive_served_correct=23,original_positive_total=24,
                 original_positive_false_refusals=1,genuine_negative_refused=36,genuine_negative_total=36,
                 mislabeled_negative_served_correct=1,genuine_wrong_served=0,served_exact_oracle_agreement="24/24",
                 locked_literal_acceptance="NOT_MET",
                 unresolved="DEV-1-3 exceeds unchanged radical domain ceiling (excluded W2-M4)."))
with (RUN/"results/development-adjudication.json").open("x",encoding="utf-8") as f:
    f.write(json.dumps(receipt,ensure_ascii=False,indent=2)+"\n")
print(receipt["adjudicated"])
