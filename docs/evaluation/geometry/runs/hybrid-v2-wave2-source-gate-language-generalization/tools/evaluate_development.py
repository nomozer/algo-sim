"""Execute the actual product path; reuse the audited scorer without modifying historical artifacts."""
from collections import Counter
from copy import deepcopy
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
from types import ModuleType

os.environ["ALLOW_LIVE_AI"] = "0"
sys.dont_write_bytecode = True
RUN = Path(__file__).resolve().parents[1]
ROOT = RUN.parents[4]
HISTORY = "ecdc26b012c8ce80d53524a98dc75cdcb020079d"
HIST_PATH = "docs/evaluation/geometry/runs/hybrid-v2-independent-vietnamese-section-holdout-wave2"


def historical(rel):
    return subprocess.check_output(["git", "show", f"{HISTORY}:{HIST_PATH}/{rel}"], cwd=ROOT)


def scorer():
    source = historical("tools/evaluate_holdout_wave2.py")
    assert hashlib.sha256(source).hexdigest() == "e9c36a177c2f43cb8af59f361a78421b6f253a5c642e980ad98939793ae51e12"
    mod = ModuleType("historical_section_scorer")
    mod.__file__ = str(RUN/"tools/historical_scorer_read_only.py")
    exec(compile(source, mod.__file__, "exec"), mod.__dict__)
    mod.ROOT = ROOT
    return mod


def evaluate_case(case, score=None):
    sys.path.insert(0, str(ROOT/"backend"))
    from app.ai.adapter4_route import run_typed_fact_next_v2_route, build_adapter4_response
    s = score or scorer()
    tax = json.loads(historical("tools/refusal_taxonomy.json"))
    r = run_typed_fact_next_v2_route(deepcopy(case["payload"]))
    resp = build_adapter4_response(r, case["payload"]["problem_text"])
    c = dict(case, stratum="development", question_type="section_and_area",
             expected_disposition="SERVE" if case["expected_status"] == "SERVED" else "REFUSE",
             acceptable_categories=[])
    rec = s.score_observed_response(c, case.get("oracle"), tax, r, resp)
    if rec.get("outcome") == "HARNESS_ERROR":
        raise RuntimeError("SCORER_ERROR (raw diagnostics intentionally not saved)")
    if case["expected_status"] == "REFUSED":
        rec["outcome"] = ("WRONG_SERVED" if rec["served"] else
                          "REFUSED_CORRECT_REASON" if rec["code"] in case["expected_codes"] else
                          "REFUSED_REASON_DISAGREEMENT")
    rec["matches_expected"] = rec["outcome"] in ("SERVED_CORRECT", "REFUSED_CORRECT_REASON")
    return rec


def main(name):
    output = RUN/"results"/name
    if output.exists():
        raise FileExistsError(output)
    raw = (RUN/"inputs/development.json").read_bytes()
    cases = json.loads(raw)["cases"]
    s = scorer()
    rows = [evaluate_case(c, s) for c in cases]
    result = dict(classification="AUTHORED_DEVELOPMENT_NOT_INDEPENDENT_HOLDOUT",
                  corpus_sha256=hashlib.sha256(raw).hexdigest(), historical_scorer_commit=HISTORY,
                  head=subprocess.check_output(["git","rev-parse","HEAD"],cwd=ROOT,text=True).strip(),
                  product_diff_sha256=hashlib.sha256(subprocess.check_output(["git","diff","--","backend/app"],cwd=ROOT)).hexdigest(),
                  live_provider_calls=0, overall=s._tally(rows),
                  matches_expected=sum(r["matches_expected"] for r in rows), cases=rows)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("x",encoding="utf-8") as f:
        f.write(json.dumps(result,ensure_ascii=False,indent=2)+"\n")
    print(json.dumps(dict(overall=result["overall"],matches=result["matches_expected"]),ensure_ascii=False))
    for r in rows:
        if not r["matches_expected"]:
            print(r["id"],r["outcome"],r.get("code"),r.get("oracle_mismatches"),r.get("reason"))


if __name__ == "__main__":
    main(sys.argv[1])
