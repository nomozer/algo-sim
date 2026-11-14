"""OCR → semantics consistency of run `grounded-vietnamese-geometry-understanding` on the 27 exposed REAL27 images.

For each image the SAME learner path as the acceptance harness (prepare → scripted confirmation of flagged spans only,
SCRIPTED_NOT_REAL_STUDENT) gives the text the parser receives; it is parsed next to the dataset's own statement text and
the two semantic representations are compared (solids, premises, goals). A difference is attributed to the stage that
lost it: the OCR / region layer (the texts differ where the representation differs) or the parser (same text, same
loss). Multi-problem isolation: the confirmed text must name one problem (one "Câu N", no answer options of another).

  python ocr_semantic_consistency.py <out.json>     # from backend/, measured_app on :8767 with LOCAL_OCR_* configured
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

RUN = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(RUN.parent / "semantic-to-scene3d-verified-simulation/tools")]
import simulation_acceptance as SA  # noqa: E402


def rep(text: str) -> dict:
    from app.ai.local_geometry_parser import parse_geometry_problem_locally
    lp = parse_geometry_problem_locally(text, use_cache=False)
    import app.ai.local_geometry_parser as L
    raw = L.normalize_problem_text(text)
    clauses = L.split_into_clauses(raw)
    b = L._AstBuilder(raw)
    for i in L._clause_order(clauses):
        L._parse_clause_into_ast(b, clauses[i])
    norm = lambda xs: sorted(json.dumps({k: v for k, v in x.items() if k not in ("quote", "goal_id", "solid_id", "unresolved_id")},  # noqa: E731
                                        ensure_ascii=False, sort_keys=True) for x in xs)
    return {"status": lp.status, "reason": lp.reason_code, "solids": norm(b.solids), "premises": norm(b.premises),
            "goals": norm(b.math_goals), "clause_classes": [c.classification for c in clauses]}


def main(out: Path) -> int:
    import evaluate_images as EV
    os.environ["ALLOW_LIVE_AI"], os.environ["GEMINI_API_KEY"] = "0", ""
    E = EV.E
    E.route_mode()
    rows = {}
    for item in SA.corpus():
        prep = E.request_prepare(SA.ROOT / item["cache_path"])["result"]
        txt = prep.get("problem_text") or ""
        if prep.get("status") == "needs_confirmation":
            txt = E.previous.simulate_student(txt, prep.get("uncertain_tokens", []), item["ground_truth_text"])["text"]
        elif prep.get("status") != "ready":
            rows[item["case_id"]] = {"prepare_status": prep.get("status"), "reason": prep.get("reason_code"),
                                     "attribution": "OCR_OR_REGION_FAILURE"}
            continue
        a, g = rep(txt), rep(item["statement"])
        same = {k: a[k] == g[k] for k in ("solids", "premises", "goals")}
        headers = re.findall(r"(?:Câu|Bài)\s*\d+", txt)
        # instrument correction (first output kept in logs/…first-instrument.json): the REAL27 items are multiple-choice,
        # so ONE option group (A–D, each letter once) belongs to the problem itself; a second group is another problem's
        options = [m.strip()[0] for m in re.findall(r"(?:^|\s)[A-D]\s*[.)]\s", txt)]
        options = [o for o in set(options) if options.count(o) > 1]
        rows[item["case_id"]] = {
            "prepare_status": prep.get("status"), "confirmed_text_sha256": hashlib.sha256(txt.encode()).hexdigest(),
            "statement_sha256": hashlib.sha256(item["statement"].encode()).hexdigest(),
            "texts_identical": re.sub(r"\s+", " ", txt).strip() == re.sub(r"\s+", " ", item["statement"]).strip(),
            "ocr": {k: a[k] for k in ("status", "reason")}, "statement": {k: g[k] for k in ("status", "reason")},
            "same_representation": same,
            "single_problem": len(set(headers)) <= 1 and not options,
            "attribution": ("CONSISTENT" if all(same.values()) and a["status"] == g["status"] else
                            "OCR_OR_REGION_FAILURE" if not all(same.values()) else "PARSER_STATUS_DIFFERS")}
    from collections import Counter
    data = {"run_id": RUN.name, "generated_at_utc": datetime.now(timezone.utc).isoformat(),
            "input": "image → /api/input/prepare (local OCR) → scripted confirmation of flagged spans only → local parser",
            "rows": rows, "attribution": dict(Counter(r["attribution"] for r in rows.values())),
            "multi_problem_leaks": [k for k, r in rows.items() if r.get("single_problem") is False]}
    out.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(data["attribution"], "leaks", data["multi_problem_leaks"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main(Path(sys.argv[1])))
