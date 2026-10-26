# -*- coding: utf-8 -*-
"""Score the Stage 2 local Hybrid V2 route END TO END through `POST /api/analyze` (0 provider calls).

Same locked authored development corpus, expected dispositions, refusal grouping and independent oracle answers as
`../../hybrid-contract-v2/evaluate_grammar_set.py` (imported, unchanged); what differs is the path: problem text →
`/api/analyze` (loopback client, `HYBRID_V2_LOCAL=offline-replay`) → replay extraction → validation → Source Gate →
planner → exact engine → Adapter /4 → HTTP response. Texts excluded from the replay corpus (several payloads for one
text) are reported as such, not scored. DEVELOPMENT data — never a holdout or a language-understanding measurement.

    python tools/evaluate_local_route.py <tree>/backend <corpus.json> <out.json>
"""
from __future__ import annotations

import json
import os
import runpy
import socket
import sys
import tempfile
from collections import Counter
from pathlib import Path

BACKEND, CORPUS, OUT = (os.path.abspath(a) for a in sys.argv[1:4])
RUN = Path(__file__).resolve().parents[1]
sys.path.insert(0, BACKEND)
os.chdir(BACKEND)
os.environ["DATABASE_URL"] = "sqlite:///" + os.path.join(tempfile.mkdtemp(prefix="hv2-local-"), "e.db").replace("\\", "/")
os.environ.update(HYBRID_V2_LOCAL="offline-replay", HYBRID_V2_LOCAL_REPLAY_CORPUS=CORPUS)
for k in ("GEMINI_API_KEY", "ALLOW_LIVE_AI", "HYBRID_ROUTE_D_PREVIEW"):
    os.environ.pop(k, None)
_connect = socket.socket.connect
socket.socket.connect = lambda s, a, *x, **k: (_connect(s, a, *x, **k) if (a[0] if isinstance(a, tuple) else str(a))
                                               in ("127.0.0.1", "::1", "localhost") else (_ for _ in ()).throw(
                                                   RuntimeError(f"network blocked: {a!r}")))

from fastapi.testclient import TestClient  # noqa: E402

import app.main as M  # noqa: E402
from app.ai.hybrid_preview import classify_refusal  # noqa: E402
from app.persistence.db import init_db  # noqa: E402

EV = runpy.run_path(str(RUN.parents[0] / "hybrid-contract-v2" / "evaluate_grammar_set.py"))
corpus = json.loads(Path(CORPUS).read_text(encoding="utf-8"))
excluded = {cid for ids in corpus["excluded_texts_with_several_payloads"].values() for cid in ids}


def main() -> int:
    init_db()
    rows = []
    for case in EV["load_lock"]():
        if case["id"] in excluded:
            rows.append({"id": case["id"], "expected": case["expected"], "observed": "EXCLUDED_FROM_REPLAY"})
            continue
        text = case["payload"]["problem_text"]
        res = TestClient(M.app, client=("127.0.0.1", 40000)).post(
            "/api/analyze", json={"input": {"type": "text", "content": text}})
        body = res.json()
        rd = body.get("route_d") or {}
        row = {"id": case["id"], "category": case["category"], "expected": case["expected"], "http": res.status_code,
               "schema": body.get("schema_version"), "status": rd.get("status"),
               "code": (body.get("envelope") or {}).get("reason_code"), "no_store": res.headers.get("cache-control")}
        if rd.get("status") == "SERVED":
            got = {k: str(EV["square_of"](v["coef"])) for k, v in (rd.get("answer_exact") or {}).items()}
            row.update(observed="SERVE", answers=got,
                       answers_correct=all(got.get(k) == v for k, v in case["answers"].items()))
        else:
            row["observed"] = EV["_GROUP"].get(classify_refusal(row["code"] or "").group, "REFUSE_OTHER")
        row["wrong_served"] = row["observed"] == "SERVE" and (case["expected"] != "SERVE" or not row["answers_correct"])
        row["match"] = row["observed"] == case["expected"] and not row["wrong_served"]
        rows.append(row)
    scored = [r for r in rows if r["observed"] != "EXCLUDED_FROM_REPLAY"]
    summary = {
        "schema": "hybrid-v2-local-route-evaluation/1",
        "classification": "AUTHORED_DEVELOPMENT_CORPUS_END_TO_END_NOT_HOLDOUT_NOT_PROVIDER",
        "corpus_sha256_lf": EV["LOCK_SHA"], "cases": len(rows), "scored": len(scored),
        "excluded_from_replay": sorted(excluded),
        "correct_served": sum(r["observed"] == "SERVE" and not r["wrong_served"] for r in scored),
        "wrong_served": sum(r["wrong_served"] for r in scored),
        "correct_refusal": sum(r["observed"] != "SERVE" and r["match"] for r in scored),
        "false_refusal": sum(r["expected"] == "SERVE" and r["observed"] != "SERVE" for r in scored),
        "refusal_class_mismatch": sum(r["expected"] != "SERVE" and r["observed"] != "SERVE" and not r["match"]
                                      for r in scored),
        "all_v4_no_store": all(r["schema"] == "hybrid-route-d-simulation/4" and r["no_store"] == "no-store"
                               for r in scored),
        "confusion": dict(Counter(f"{r['expected']} -> {r['observed']}" for r in scored)),
        "provider_requests": 0,
    }
    Path(OUT).write_text(json.dumps({"summary": summary, "rows": rows}, ensure_ascii=False, indent=1) + "\n",
                         encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False))
    return 0 if summary["wrong_served"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
