"""Read immutable Wave2 Git objects; execute only current product; write post-feedback results to THIS run."""
from collections import Counter
import hashlib
import json
from pathlib import Path
import subprocess
import sys
from evaluate_development import ROOT, RUN, historical, scorer, HISTORY


def main():
    path = RUN/"results/wave2-post-feedback-regression.json"
    if path.exists():
        raise FileExistsError(path)
    s = scorer()
    cases = json.loads(historical("inputs/holdout-wave2.json"))["cases"]
    expected = json.loads(historical("oracle/expected.json"))
    tax = json.loads(historical("tools/refusal_taxonomy.json"))
    rows = [s.score_case(c, expected.get(c["id"]), tax) for c in cases]
    for r in rows:
        if r.get("outcome") == "HARNESS_ERROR" or r.get("product_exception"):
            raise RuntimeError("Replay execution/scoring error; do not save raw exception content")
        r["classification"] = "POST_FEEDBACK_DEVELOPMENT_REGRESSION"
        r["expected_certificate_category"] = (expected.get(r["id"]) or {}).get("expected_certificate_category")
    def by(key):
        return {k: s._tally([r for r in rows if (r.get(key) or "none") == k])
                for k in sorted({r.get(key) or "none" for r in rows})}
    served = [r for r in rows if r["expected"] == "SERVE" and r["served"]]
    result = dict(classification="POST_FEEDBACK_DEVELOPMENT_REGRESSION",
                  claim_ceiling="NOT_INDEPENDENT_HOLDOUT",
                  historical_commit=HISTORY, corpus_git_sha256=hashlib.sha256(historical("inputs/holdout-wave2.json")).hexdigest(),
                  head=subprocess.check_output(["git","rev-parse","HEAD"],cwd=ROOT,text=True).strip(),
                  product_diff_sha256=hashlib.sha256(subprocess.check_output(["git","diff","--","backend/app"],cwd=ROOT)).hexdigest(),
                  live_provider_calls=0, overall=s._tally(rows),
                  exact_oracle_agreement=dict(agree=sum(not r.get("oracle_mismatches") for r in served),served=len(served)),
                  by_family=by("family"),by_plane_relation=by("plane_relation"),by_category=by("expected_certificate_category"),
                  remaining_first_refusal=dict(Counter(r["code"] for r in rows if r["outcome"]=="FALSE_REFUSAL")),
                  refusal_reason_mismatches=[r["id"] for r in rows if r["outcome"]=="REFUSED_REASON_DISAGREEMENT"],
                  cases=rows)
    with path.open("x",encoding="utf-8") as f:
        f.write(json.dumps(result,ensure_ascii=False,indent=2)+"\n")
    print(json.dumps({k:result[k] for k in ["classification","overall","exact_oracle_agreement","remaining_first_refusal"]}))
    for r in rows:
        if r["outcome"] in ("FALSE_REFUSAL","WRONG_SERVED"):
            print(r["id"],r["outcome"],r["code"],r.get("reason"),r.get("oracle_mismatches"))


if __name__ == "__main__":
    main()
