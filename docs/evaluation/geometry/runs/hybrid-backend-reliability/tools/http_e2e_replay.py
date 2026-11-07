"""HTTP end-to-end replay of every stored `typed-fact-next/2` payload through `POST /api/analyze` (staging-replay).

Offline, 0 provider calls: `HYBRID_ROUTE_MODE=staging-replay`, `ALLOW_LIVE_AI=0`, no `GEMINI_API_KEY`. Each problem text
is posted twice on a fresh SQLite database (first = cache MISS, second = HIT), through the real middleware, idempotency,
usage ledger, cache and JSON serialization. Checks per response:

- HTTP status / `X-Algosim-Cache`; hit body byte-equal to miss body; HTTP body == direct `build_adapter4_response`;
- served envelope contract: `scene3d.objects`, `formation.steps` fields (step_id, depends_on, created/reused/
  highlighted/retired ids, verification_refs, coordinate_frame_id, step_summary), id references resolvable,
  `depends_on` only to earlier steps, every exact answer present;
- no internal reprs (`Fraction(`, `Vec3(`, `Plane3(`, `Radical(`) in any learner-facing string.

Usage (from backend/): PYTHONIOENCODING=utf-8 .venv/Scripts/python.exe <this> <fresh out-dir>
Writes `<out>/http-e2e-summary.json` (counts + findings) and `<out>/served-responses.json` (frontend audit input).
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import statistics
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[6]
sys.path.insert(0, str(ROOT / "backend"))

INTERNAL = re.compile(r"\b(Fraction|Vec3|Plane3|Radical|Point3|Line3)\(")
STEP_FIELDS = ("step_id", "depends_on", "created_ids", "reused_ids", "highlighted_ids", "retired_ids",
               "verification_refs", "coordinate_frame_id", "step_summary")
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


def collect() -> dict[str, dict]:
    by_text: dict[str, dict] = {}
    for base in SEARCH:
        for f in sorted(base.rglob("*.json")):
            if "/perf/" in f.as_posix():
                continue
            try:
                data = json.loads(f.read_text(encoding="utf-8"))
            except (UnicodeDecodeError, json.JSONDecodeError, OSError):
                continue
            for p in payloads(data):
                by_text.setdefault(p["problem_text"], p)     # staging replay is keyed by exact text: first wins
    return by_text


def learner_strings(node, path=""):
    """Strings a learner can see: everything under envelope except ids/keys; route_d proofs are not rendered raw."""
    if isinstance(node, dict):
        for k, v in node.items():
            yield from learner_strings(v, f"{path}.{k}")
    elif isinstance(node, list):
        for i, v in enumerate(node):
            yield from learner_strings(v, f"{path}[{i}]")
    elif isinstance(node, str):
        yield path, node


def check_served(body: dict) -> list[str]:
    out = []
    env = body["envelope"]
    scene = env.get("scene3d") or {}
    objs = scene.get("objects") or []
    if not objs:
        out.append("scene3d.objects empty")
    ids = {o.get("id") for o in objs if isinstance(o, dict)}
    steps = (scene.get("formation") or {}).get("steps") or []
    if not steps:
        out.append("formation.steps empty")
    seen_steps: set[str] = set()
    created: set[str] = set()
    for s in steps:
        miss = [f for f in STEP_FIELDS if f not in s]
        if miss:
            out.append(f"{s.get('step_id')}: missing {miss}")
            continue
        # `depends_on` lists GEOMETRY ids the step builds on (not step ids): each must exist and be created earlier.
        late = [d for d in s["depends_on"] if d not in created and d not in seen_steps]
        if late:
            out.append(f"{s['step_id']}: depends_on ids not created by an earlier step {late[:4]}")
        for key in ("created_ids", "reused_ids", "highlighted_ids", "retired_ids"):
            unknown = [i for i in s[key] if i not in ids]
            if unknown:
                out.append(f"{s['step_id']}: {key} not in scene objects {unknown[:4]}")
        early = [i for i in s["reused_ids"] if i not in created]
        if early:
            out.append(f"{s['step_id']}: reuses ids never created earlier {early[:4]}")
        again = [i for i in s["created_ids"] if i in created]
        if again:
            out.append(f"{s['step_id']}: re-creates ids {again[:4]}")
        created |= set(s["created_ids"])
        seen_steps.add(s["step_id"])
        if not isinstance(s["step_summary"], dict) or not s["step_summary"].get("what"):
            out.append(f"{s['step_id']}: empty step_summary")
    answers = body["route_d"].get("answer_exact") or {}
    for q in answers:
        if not any(isinstance(o, dict) and q in json.dumps(o, ensure_ascii=False) for o in objs) \
                and q not in json.dumps(env, ensure_ascii=False):
            out.append(f"answer {q} not referenced by the envelope")
    for p, s in learner_strings(env, "envelope"):
        if INTERNAL.search(s):
            out.append(f"internal repr at {p}: {s[:80]!r}")
            break
    return out


def block_network() -> None:
    """Offline by construction, same two layers as `backend/conftest.py::block_real_network`.

    `app/persistence/db.py` runs `load_dotenv` at IMPORT, which refills a key popped earlier — so db is imported first,
    then the key is removed, then every real httpx transport raises. (An earlier version of this tool popped the key
    before the import; `/api/image/extract`, which ignores `ALLOW_LIVE_AI=0`, then reached the real provider.)"""
    import httpx

    import app.persistence.db  # noqa: F401  — let load_dotenv run BEFORE removing the key

    os.environ.pop("GEMINI_API_KEY", None)

    def refuse(*_a, **_k):
        raise RuntimeError("network blocked: offline evaluation tool")

    async def refuse_async(*_a, **_k):
        raise RuntimeError("network blocked: offline evaluation tool")

    httpx.HTTPTransport.handle_request = refuse
    httpx.AsyncHTTPTransport.handle_async_request = refuse_async


def make_client(corpus: dict[str, dict]):
    """Offline product app on a fresh SQLite DB, staging-replay over `corpus`, signed-in route-test session."""
    tmp = Path(tempfile.mkdtemp(prefix="http-e2e-"))
    corpus_file = tmp / "staging-corpus.json"
    corpus_file.write_text(json.dumps({"schema": "hybrid-v2-local-replay-corpus/1", "outputs": corpus},
                                      ensure_ascii=False), encoding="utf-8")
    os.environ.update(HYBRID_ROUTE_MODE="staging-replay", HYBRID_REPLAY_CORPUS=str(corpus_file), ALLOW_LIVE_AI="0")
    block_network()
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker

    import app.accounts.router as router_module
    from app import main as M
    from app.persistence import db as db_module
    from app.persistence.db import Base
    from tests.route_client import route_client

    engine = create_engine(f"sqlite:///{tmp / 'e2e.db'}", connect_args={"check_same_thread": False})
    TS = sessionmaker(bind=engine, autoflush=False)
    Base.metadata.create_all(engine)
    db_module.engine, db_module.SessionLocal, M.SessionLocal, router_module.SessionLocal = engine, TS, TS, TS
    # ENTERED client: one event loop / portal for the whole run. A non-entered TestClient builds and tears down a
    # Windows Proactor loop per request (~33 ms of `_cancel_overlapped`), a harness cost no deployed server pays.
    client = route_client(M.app)
    client.__enter__()
    return client


def main() -> None:
    out_dir = Path(sys.argv[1])
    out_dir.mkdir(parents=True, exist_ok=False)
    corpus = collect()
    client = make_client(corpus)
    from app.ai.adapter4_route import build_adapter4_response, run_typed_fact_next_v2_route
    from app.ai.hybrid_offline import StagingReplay, hybrid_offline_policy

    counts = {"texts": len(corpus), "http": {}, "served": 0, "refused": 0, "hit_ok": 0, "hit_mismatch": 0,
              "http_vs_direct_mismatch": 0, "contract_findings": 0, "refusal_categories": {}}
    findings, served_rows, lat = [], [], {"miss": [], "hit": [], "refused": []}
    for text, payload in corpus.items():
        t0 = time.perf_counter()
        r1 = client.post("/api/analyze", json={"input": {"type": "text", "content": text}})
        t1 = time.perf_counter()
        counts["http"][str(r1.status_code)] = counts["http"].get(str(r1.status_code), 0) + 1
        key = hashlib.sha256(text.encode()).hexdigest()[:12]
        if r1.status_code != 200:
            findings.append({"key": key, "issue": f"HTTP {r1.status_code}", "body": r1.text[:200]})
            continue
        body = r1.json()
        if "route_d" not in body:          # pre-provider domain gate (`_ngoai_pham_vi`): no Route D ran
            code = body.get("error_code") or body.get("reason_code") or "?"
            counts["domain_gate"] = counts.get("domain_gate", 0) + 1
            direct_status = run_typed_fact_next_v2_route(payload).status
            findings.append({"key": key, "issue": f"domain gate {code}; direct route would be {direct_status}",
                             "text": text[:160]})
            continue
        status = (body.get("route_d") or {}).get("status")
        # HTTP fidelity: the body must equal what the orchestrator the handler calls returns (serialization adds nothing).
        orchestrated = StagingReplay(text, payload, hybrid_offline_policy({"HYBRID_ROUTE_D_PREVIEW": "1"}), None).run()
        if body != json.loads(json.dumps(orchestrated.response, ensure_ascii=False)):
            counts["http_vs_direct_mismatch"] += 1
            findings.append({"key": key, "issue": "HTTP body differs from the staging orchestrator response"})
        # Defence in depth: the extraction validator may refuse BEFORE the route with a more specific code. A served
        # result must never depend on which layer ran (served by one and refused by the other is a finding).
        direct = build_adapter4_response(run_typed_fact_next_v2_route(payload), text)
        if (direct["route_d"]["status"] == "SERVED") != (body["route_d"]["status"] == "SERVED"):
            findings.append({"key": key, "issue": f"served/refused differs: route {direct['route_d']['status']} "
                                                  f"vs HTTP {body['route_d']['status']}"})
        elif direct["envelope"].get("reason_code") != body["envelope"].get("reason_code"):
            counts["earlier_extraction_refusal"] = counts.get("earlier_extraction_refusal", 0) + 1
        if status != "SERVED":
            counts["refused"] += 1
            cat = body["envelope"].get("failure_category") or "?"
            counts["refusal_categories"][cat] = counts["refusal_categories"].get(cat, 0) + 1
            lat["refused"].append(t1 - t0)
            if r1.headers.get("X-Algosim-Cache") != "none":
                findings.append({"key": key, "issue": f"refusal cache state {r1.headers.get('X-Algosim-Cache')}"})
            continue
        counts["served"] += 1
        lat["miss"].append(t1 - t0)
        for issue in check_served(body):
            counts["contract_findings"] += 1
            findings.append({"key": key, "issue": issue})
        t2 = time.perf_counter()
        r2 = client.post("/api/analyze", json={"input": {"type": "text", "content": text}})
        lat["hit"].append(time.perf_counter() - t2)
        if r1.headers.get("X-Algosim-Cache") == "miss" and r2.headers.get("X-Algosim-Cache") == "hit" \
                and r2.content == r1.content:
            counts["hit_ok"] += 1
        else:
            counts["hit_mismatch"] += 1
            findings.append({"key": key, "issue": f"cache {r1.headers.get('X-Algosim-Cache')}->"
                                                  f"{r2.headers.get('X-Algosim-Cache')} equal={r2.content == r1.content}"})
        if body["route_d"].get("answer_exact"):
            served_rows.append({"key": key, "source": "http", "answers": body["route_d"]["answer_exact"],
                                "problem_text": text, "response": body})

    def q(xs, p):
        xs = sorted(xs)
        return round(xs[min(len(xs) - 1, int(p * len(xs)))] * 1000, 1) if xs else None

    counts["latency_ms"] = {k: {"n": len(v), "p50": q(v, .5), "p95": q(v, .95), "max": q(v, 1.0),
                                "mean": round(statistics.mean(v) * 1000, 1) if v else None} for k, v in lat.items()}
    (out_dir / "http-e2e-summary.json").write_text(json.dumps({"counts": counts, "findings": findings},
                                                              ensure_ascii=False, indent=1), encoding="utf-8")
    (out_dir / "served-responses.json").write_text(json.dumps({"rows": served_rows}, ensure_ascii=False),
                                                   encoding="utf-8")
    print(json.dumps(counts, ensure_ascii=False))


if __name__ == "__main__":
    main()
