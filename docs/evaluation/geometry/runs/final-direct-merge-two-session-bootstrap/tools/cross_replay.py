"""Paired live diagnosis, offline half: replay every captured provider payload through ONE checkout's full deterministic
pipeline (run_hybrid_offline: TypedFactNext validation -> bridge -> Source Gate -> Planner -> Kernel -> Adapter /4), exactly
as tools/live_pair_capture.py saw it enter validation. 0 provider calls (ALLOW_LIVE_AI=0, key removed).

usage: python -B cross_replay.py <checkout_backend_dir> <preregistration.json> <out.json> <capture.json> [<capture.json> ...]
"""
import hashlib
import json
import os
import sys
from pathlib import Path

backend, prereg_p, out_p = (Path(a).resolve() for a in sys.argv[1:4])
captures = [Path(a).resolve() for a in sys.argv[4:]]
if out_p.exists():
    raise SystemExit(f"refusing to overwrite {out_p}")
texts = {hashlib.sha256(c["text"].encode()).hexdigest()[:16]: c for c in json.loads(prereg_p.read_text(encoding="utf-8"))["cases"]}
os.environ["ALLOW_LIVE_AI"] = "0"
os.environ.pop("GEMINI_API_KEY", None)
sys.dont_write_bytecode = True
sys.path.insert(0, str(backend))
os.chdir(backend)
from app.ai.hybrid_offline import hybrid_offline_policy, run_hybrid_offline  # noqa: E402
from app.ai.typed_fact_next_extraction import ReplayExtractor  # noqa: E402
import app.ai.hybrid_offline as HO  # noqa: E402

assert Path(HO.__file__).resolve().is_relative_to(backend), HO.__file__
policy = hybrid_offline_policy({"HYBRID_ROUTE_D_PREVIEW": "1"})
rows = []
for cap_p in captures:
    cap = json.loads(cap_p.read_text(encoding="utf-8"))
    for i, item in enumerate(cap["captured"]):
        case = texts[item["text_sha16"]]
        row = {"capture": cap_p.name, "index": i, "id": case["id"], "captured_from": cap["checkout_backend"]}
        if "payload" not in item:
            row.update(status="NO_PAYLOAD", reason=item.get("raised"))
        else:
            try:
                res = run_hybrid_offline(case["text"], ReplayExtractor({case["text"]: item["payload"]}),
                                         policy=policy, timeout_seconds=30.0)
                rd = (res.response or {}).get("route_d") or {}
                ref = rd.get("refusal") if isinstance(rd.get("refusal"), dict) else {}
                answers = sorted(str(v) for v in (rd.get("answers") or {}).values())
                row.update(status=rd.get("status"), reason=ref.get("code") or ref.get("reason_code"),
                           answer_values=answers, matches_oracle=answers == case["expected_answer_values"])
            except Exception as e:  # a crash is a finding, never a pass
                row.update(status="CRASH", reason=type(e).__name__)
        rows.append(row)
        print(row["capture"], row["id"], row["status"], row.get("reason"), row.get("answer_values"), flush=True)
out_p.write_text(json.dumps({"schema": "axo-live-pair-cross-replay/1", "replayed_in": str(backend), "module": HO.__file__,
                             "rows": rows}, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
