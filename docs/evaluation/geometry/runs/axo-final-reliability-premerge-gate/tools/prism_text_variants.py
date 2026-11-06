"""Right-prism oracle (V = 30) through the product route under learner typing variants (NFD combining marks,
spacing, non-breaking spaces); the recorded extraction copies its quotes from the text it received, as a model
would. Offline, 0 model calls. Usage (from backend/): PYTHONPATH=. python <this>
"""
from pathlib import Path
import copy, json, sys, unicodedata
sys.stdout.reconfigure(encoding="utf-8")
import importlib.util
spec = importlib.util.spec_from_file_location("p", Path(__file__).resolve().parents[2] / "axo-end-to-end-authority-scene3d-usability/tools/prism_layer_probe.py")
P = importlib.util.module_from_spec(spec); spec.loader.exec_module(P)
from app.ai.hybrid_offline import hybrid_offline_policy, run_hybrid_offline
from app.ai.typed_fact_next_extraction import ReplayExtractor

def deep(obj, fn):
    if isinstance(obj, dict): return {k: (fn(v) if k in ("problem_text", "quote") and isinstance(v, str) else deep(v, fn)) for k, v in obj.items()}
    if isinstance(obj, list): return [deep(x, fn) for x in obj]
    return obj

variants = {
  "reference (NFC)": lambda s: s,
  "NFD combining marks": lambda s: unicodedata.normalize("NFD", s),
  "double spaces": lambda s: s.replace(" ", "  "),
  "no spaces around =": lambda s: s.replace(" = ", "="),
  "non-breaking spaces": lambda s: s.replace(" ", "\u00a0"),
}
for name, fn in variants.items():
    payload = deep(P.reference(), fn)
    text = payload["problem_text"]
    resp = run_hybrid_offline(text, ReplayExtractor({text: payload}), policy=hybrid_offline_policy({"HYBRID_ROUTE_D_PREVIEW": "1"})).response
    rd, env = resp["route_d"], resp["envelope"]
    print(f"{name:24} -> {rd['status']:8} {env.get('reason_code')} {env.get('failure_category')} answers={rd.get('answers')}")
