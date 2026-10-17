"""One-time pre-lock annotation corrections, independently reviewed before any prompt change. No product imports."""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent


def sha(value):
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def main():
    if (HERE / "protocol.json").exists():
        raise SystemExit("ALREADY_LOCKED")
    corpus = json.loads((HERE / "corpus.json").read_text(encoding="utf-8"))
    gold = json.loads((HERE / "gold_facts.json").read_text(encoding="utf-8"))
    changes = []
    for case in corpus["cases"]:
        requests = {r["rid"]: r for r in case["requests"]}
        for r in requests.values():
            if r["quantity"] == "angle":
                r["response_form"] = "cos_squared" if "cos" in r["source_quote"].lower() else "angle"
        for f in gold["cases"][case["id"]]["facts"]:
            before = dict(f)
            if f["kind"] == "right_angle":
                f["points"] = [p for p in f.get("points", []) if p != f.get("at")]
            if ((f["kind"] == "point_def" and not f.get("point_kind"))
                    or (f["kind"] == "intersection_line" and not f.get("points_a"))
                    or "description" in f or "domain" in f):
                kept = {k: v for k, v in f.items() if k in {"id", "rid", "role", "quotes", "negated", "ambiguous"}}
                f.clear()
                f.update(kept, kind="unsupported", reason="Source relation has no faithful TypedFact representation; no substitute invented.")
            if f["kind"] == "unsupported":
                for k in list(f):
                    if k not in {"id", "rid", "role", "quotes", "negated", "ambiguous", "kind", "reason"}:
                        f.pop(k)
            if f.get("rid") in requests and requests[f["rid"]]["intent"] == "prove":
                f["role"] = "prove"
            if f != before:
                changes.append({"case_id": case["id"], "fact_id": f["id"], "before": before, "after": f})
    for name, obj in (("corpus", corpus), ("gold_facts", gold), ("prelock_corrections", {"scope": "ENCODING_ONLY_BEFORE_PROMPT_TUNING", "changes": changes})):
        (HERE / f"{name}.json").write_text(json.dumps(obj, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    files = ("oracle.py", "authoring.md", "baseline_prompt.txt", "baseline_schema.json", "prelock_corrections.json")
    protocol = {"schema": "semantic-extraction-protocol/2", "model": "gemini-2.5-flash", "scorer": "grounded-source-obligations/2",
                "locked_sha256": {"corpus": sha(corpus), "gold_facts": sha(gold)},
                "file_sha256": {name: hashlib.sha256((HERE / name).read_bytes().replace(b"\r\n", b"\n")).hexdigest() for name in files},
                "caps": {"PILOT": {"logical_calls": 12, "http_attempts": 12, "accounted_tokens": 400000, "usd": 0.50, "samples": 1},
                         "LOCKED": {"logical_calls": 24, "http_attempts": 24, "accounted_tokens": 800000, "usd": 1.00, "samples": 1}},
                "arms": ["baseline", "v2"], "retries": 0, "timeout_seconds": 90,
                "pilot_total_calls": 24, "pilot_total_usd_cap": 1.00, "locked_total_calls": 48, "locked_total_usd_cap": 2.00,
                "human_validation": "NOT_HUMAN_VALIDATED", "live_decision": "PENDING_OWNER_GO", "integration_decision": "PENDING_OWNER_GO"}
    (HERE / "protocol.json").write_text(json.dumps(protocol, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"corrections": len(changes), "locked_sha256": protocol["locked_sha256"]}))


if __name__ == "__main__":
    main()
