"""AXO /17 routing ablation — one arm per process, real `/api/analyze` handler (FastAPI TestClient), local-only-scoped.

usage: python ablate.py <arm A|P|B|C> <out_dir> <manifest.json>[,<manifest.json>...] [--ids X,Y]
  A  production (candidate 157 as committed)
  P  Local Parser on the original text only (SLM escalation disabled; the router returns before its v3-normalizer step)
  B  deterministic-first extension: in-memory parser patch (see PATCHES), nothing written to the tree
  BP B patches + deterministic only
  C  SLM-first diagnostic: escalate every case to AxoV9, parser reconcile disabled (Source Gate + kernel unchanged)
Writes <out_dir>/responses.jsonl ({"case_id","body"} for scene_oracle.py) and <out_dir>/rows.jsonl (route facts).
Refuses to write into a non-empty out_dir.
"""
from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path

arm, out_dir = sys.argv[1], Path(sys.argv[2])
manifests = [Path(p) for p in sys.argv[3].split(",")]
ids = None
if "--ids" in sys.argv:
    ids = set(sys.argv[sys.argv.index("--ids") + 1].split(","))
if out_dir.exists() and any(out_dir.iterdir()):
    raise SystemExit(f"refusing to write into non-empty {out_dir}")
out_dir.mkdir(parents=True, exist_ok=True)

os.environ["DATABASE_URL"] = f"sqlite:///{(out_dir / 'arm.db').as_posix()}"
os.environ["HYBRID_ROUTE_MODE"] = "local-only-scoped"
os.environ["ALLOW_LIVE_AI"] = "0"
os.environ.pop("GEMINI_API_KEY", None)
sys.path.insert(0, os.getcwd())

PATCHES = [
    # B-1: a length goal needs a question, not an assignment ("Độ dài KL = 7." is a premise)
    (
        'rf"(?P<full>(?:tính\\s+)?độ\\s+dài(?:\\s+(?:đoạn(?:\\s+thẳng)?|đường\\s+chéo|cạnh(?:\\s+(?:bên|đáy))?))?\\s+(?P<seg>{_PTS2}))(?![\\w\'])",',
        'rf"(?P<full>(?:tính\\s+)?độ\\s+dài(?:\\s+(?:đoạn(?:\\s+thẳng)?|đường\\s+chéo|cạnh(?:\\s+(?:bên|đáy))?))?\\s+(?P<seg>{_PTS2}))(?![\\w\'])(?!\\s*(?:=|bằng|là)\\s*{_VAL})",',
    ),
    # B-2: the pairwise-perpendicular synonym the SLM prompt canonicalizer and the v3 normalizer already accept
    (
        'rf"(?P<full>(?P<e1>{_PTS2})\\s*,\\s*(?P<e2>{_PTS2})\\s*,\\s*(?P<e3>{_PTS2})\\s+đôi\\s+một\\s+vuông\\s+góc(?:\\s+với\\s+nhau)?)",',
        'rf"(?P<full>(?P<e1>{_PTS2})\\s*,\\s*(?P<e2>{_PTS2})\\s*,\\s*(?P<e3>{_PTS2})\\s+(?:đôi\\s+một\\s+vuông\\s+góc(?:\\s+với\\s+nhau)?|vuông\\s+góc\\s+(?:với\\s+nhau\\s+)?từng\\s+đôi(?:\\s+một)?))",',
    ),
]

if arm in ("B", "BP"):
    import app.ai.local_geometry_parser as LGP

    src = Path(LGP.__file__).read_text(encoding="utf-8")
    for old, new in PATCHES:
        if src.count(old) != 1:
            raise SystemExit(f"patch anchor not unique/absent: {old[:60]}")
        src = src.replace(old, new)
    exec(compile(src, LGP.__file__, "exec"), LGP.__dict__)

import app.ai.adaptive_input_router as AIR  # noqa: E402
import app.ai.local_slm_extractor as LSE  # noqa: E402
import app.ai.local_slm_runtime as LSR  # noqa: E402

if arm in ("P", "BP"):
    AIR._should_escalate_to_compact_slm = lambda det, norm_text: False
if arm == "C":
    AIR._should_escalate_to_compact_slm = lambda det, norm_text: det.telemetry.chosen_route != "LOCAL_OUT_OF_SCOPE_GATE"
    _orig_run = LSE.run_local_slm_extraction

    def _no_reconcile(*a, **k):
        k["allow_parser_reconcile"] = False
        return _orig_run(*a, **k)

    LSE.run_local_slm_extraction = _no_reconcile

COUNT = {"n": 0}
_orig_chat = LSR.LocalSlmRuntime.chat_completion_json


def _counting_chat(self, **kw):
    COUNT["n"] += 1
    return _orig_chat(self, **kw)


LSR.LocalSlmRuntime.chat_completion_json = _counting_chat

import app.main as M  # noqa: E402
from tests.route_client import route_client  # noqa: E402

cases = []
for mp in manifests:
    m = json.loads(mp.read_text(encoding="utf-8"))
    for grp in ("valid_cases", "negative_cases"):
        for c in m.get(grp) or []:
            if c.get("input_type", "text") != "text":
                continue
            if ids is None or c["case_id"] in ids:
                cases.append((mp.parent.name + "/" + mp.name, grp, c))

client = route_client(M.app)
resp_f = (out_dir / "responses.jsonl").open("w", encoding="utf-8")
rows_f = (out_dir / "rows.jsonl").open("w", encoding="utf-8")
t_all = time.perf_counter()
for src, grp, c in cases:
    before = COUNT["n"]
    t0 = time.perf_counter()
    r = client.post("/api/analyze", json={"input": {"type": "text", "content": c["original_input"]}})
    ms = (time.perf_counter() - t0) * 1000.0
    try:
        body = r.json()
    except Exception:
        body = {"_raw": r.text[:500]}
    rd = body.get("route_d") or {}
    env = body.get("envelope") or {}
    tel = rd.get("adaptive_telemetry") or {}
    row = {
        "arm": arm, "source": src, "group": grp, "case_id": c["case_id"],
        "expected_behavior": c.get("expected_behavior"), "http": r.status_code, "ms": round(ms, 1),
        "route_status": rd.get("status"), "extraction_mode": rd.get("extraction_mode"),
        "chosen_route": tel.get("chosen_route"), "local_parse_status": tel.get("local_parse_status"),
        "reason_code": (rd.get("refusal") or {}).get("reason_code") or env.get("reason_code") or body.get("reason_code"),
        "slm_inferences": COUNT["n"] - before, "scene_served": bool(env.get("scene3d")),
    }
    rows_f.write(json.dumps(row, ensure_ascii=False) + "\n")
    rows_f.flush()
    resp_f.write(json.dumps({"case_id": c["case_id"], "source": src, "body": body}, ensure_ascii=False) + "\n")
    print(row["case_id"], row["route_status"], row["extraction_mode"], row["reason_code"], row["slm_inferences"], row["ms"], flush=True)
resp_f.close()
rows_f.close()
(out_dir / "summary.json").write_text(json.dumps({"arm": arm, "cases": len(cases), "slm_inferences_total": COUNT["n"],
                                                  "wall_s": round(time.perf_counter() - t_all, 1)}, indent=1), encoding="utf-8")
try:
    LSR.shutdown_global_local_slm_runtimes()
except Exception:
    pass
