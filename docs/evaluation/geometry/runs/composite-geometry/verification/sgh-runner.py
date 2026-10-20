"""Temporary offline SGH known-regression runner; reads the original locked manifest directly."""
import argparse
from copy import deepcopy
from fractions import Fraction
import hashlib
import json
from pathlib import Path
import subprocess
import sys

ap = argparse.ArgumentParser()
ap.add_argument("--code-root", type=Path, required=True)
ap.add_argument("--out", type=Path, required=True)
a = ap.parse_args()
path = Path("D:/Documents/AlgoSim-Research/SGH/sgh_locked_manifest.json")
raw = path.read_bytes()
sha = hashlib.sha256(raw).hexdigest()
assert sha == "268c5d666fe19133f9f5a2f523942fcc612f4ee98efe8a6d56aee9e4ea572641"
m = json.loads(raw)
canonical = hashlib.sha256(json.dumps(m["cases"], ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
assert canonical == m["manifest_sha256"] == "fe3356847140000add09f20cfd3f598849c54992751ff70f101a79a1ae039ab2"
assert len(m["cases"]) == m["case_count"] == 18
sys.path.insert(0, str(a.code_root / "backend"))
from app.ai.function_route import run_fact_route
rows = []
for c in m["cases"]:
    assert hashlib.sha256(c["text"].encode()).hexdigest() == c["text_sha256"]
    r = run_fact_route(c["text"], {"facts": deepcopy(c["facts"])})
    got, math_matches, tuples = {}, {}, {}
    for q in r.answers:
        v = r.exec_result.final_memory["kq_" + q]
        value = Fraction(v) if r.answers[q].startswith("cos²=") else Fraction(v.he)**2*v.can if hasattr(v, "can") else Fraction(v)**2
        got[q] = str(value)
        want = c["oracle"].get(q, {})
        math_matches[q] = got[q] == want.get("value_sq")
        tuples[q] = bool(want) and r.answer_exact.get(q) == {k: want.get(k) for k in ("coef", "dim", "unit")}
    rows.append(dict(id=c["id"], category=c["category"], status=r.status, code=r.code, answers=r.answers,
                     exact=r.answer_exact, values=got, oracle=c["oracle"], expected_status=c["expected_status"], expected_code=c["expected_code"],
                     math_matches=math_matches, strict_tuple_matches=tuples, payload_sha256_declared=c["payload_sha256"],
                     direct_payload_canonical_sha256=hashlib.sha256(json.dumps({"facts":c["facts"]}, ensure_ascii=False,sort_keys=True,separators=(",", ":")).encode()).hexdigest(),
                     expected_outcome_match=r.status==c["expected_status"] and (r.code is None if c["expected_code"] is None else r.code in c["expected_code"].split("|"))))
assert path.read_bytes() == raw
result = dict(evaluation_class="KNOWN_REGRESSION_NOT_BLIND", original_manifest_path=str(path), manifest_sha256=sha,
              canonical_manifest_lock=canonical, manifest_unchanged=True, direct_original_text_and_facts=True,
              payload_hash_note="Original opaque payload_sha256 retained verbatim; canonical direct-payload hash recorded separately. File hash, canonical cases lock and all text hashes verified before execution.",
              full_sha=subprocess.check_output(["git", "rev-parse", "HEAD"],cwd=a.code_root,text=True).strip(),live_provider_calls=0,rows=rows,
              summary=dict(positive_exact_served=sum(r["status"]=="SERVED" and all(r["math_matches"].values()) for r in rows if r["category"]=="POSITIVE"),
                           positive_goals_exact=sum(sum(r["math_matches"].values()) for r in rows if r["category"]=="POSITIVE"),
                           positive_strict_tuple=sum(sum(r["strict_tuple_matches"].values()) for r in rows if r["category"]=="POSITIVE"),
                           negative_exact_refusal=sum(r["expected_outcome_match"] for r in rows if r["category"]=="NEGATIVE"),
                           ambiguous_original_expectation=sum(r["expected_outcome_match"] for r in rows if r["category"]=="AMBIGUOUS")))
assert not a.out.exists()
a.out.parent.mkdir(parents=True,exist_ok=True)
a.out.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
print(json.dumps(result["summary"]))
