"""Regenerate Adapter /4 responses on the CURRENT backend for every TypedFactNext /2 payload stored in the repo.

Offline, 0 model calls. Old fixtures may come from older backends, so only the payload is reused; the response is
recomputed. Usage (from backend/): python <this> <fresh output.json>
Output rows: source file, payload, status/code/category, answers, and the full Adapter /4 response for SERVED rows
that carry at least one exact answer (the frontend authority audit consumes them).
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[6]
sys.path.insert(0, str(ROOT / "backend"))

from app.ai.adapter4_route import build_adapter4_response, run_typed_fact_next_v2_route  # noqa: E402

SEARCH = [ROOT / "docs/evaluation", ROOT / "backend/tests"]


def payloads(node):
    if isinstance(node, dict):
        if node.get("schema_version") == "typed-fact-next/2" and isinstance(node.get("problem_text"), str):
            yield node
            return
        for v in node.values():
            yield from payloads(v)
    elif isinstance(node, list):
        for v in node:
            yield from payloads(v)


def main() -> None:
    out = Path(sys.argv[1])
    seen, rows, counts = set(), [], {"files": 0, "payloads": 0, "unique": 0, "served_with_answer": 0, "errors": 0}
    for base in SEARCH:
        for f in sorted(base.rglob("*.json")):
            if "/perf/" in f.as_posix():
                continue
            try:
                data = json.loads(f.read_text(encoding="utf-8"))
            except (UnicodeDecodeError, json.JSONDecodeError):
                continue
            found = False
            for p in payloads(data):
                found = True
                counts["payloads"] += 1
                key = hashlib.sha256(json.dumps(p, sort_keys=True, ensure_ascii=False).encode()).hexdigest()
                if key in seen:
                    continue
                seen.add(key)
                counts["unique"] += 1
                try:
                    r = run_typed_fact_next_v2_route(p)
                    resp = build_adapter4_response(r, p["problem_text"])
                except Exception as e:  # schema-invalid historical payloads are reported, not fixed
                    counts["errors"] += 1
                    rows.append({"source": f.relative_to(ROOT).as_posix(), "key": key[:16], "error": type(e).__name__})
                    continue
                row = {"source": f.relative_to(ROOT).as_posix(), "key": key[:16], "status": r.status, "code": r.code,
                       "category": resp["envelope"].get("failure_category"), "answers": r.answer_exact or {},
                       "problem_text": p["problem_text"]}
                if r.status == "SERVED" and r.answer_exact:
                    counts["served_with_answer"] += 1
                    row["response"] = resp
                rows.append(row)
            counts["files"] += found
    with out.open("x", encoding="utf-8") as s:
        json.dump({"counts": counts, "rows": rows}, s, ensure_ascii=False)
    print(json.dumps(counts))


if __name__ == "__main__":
    main()
