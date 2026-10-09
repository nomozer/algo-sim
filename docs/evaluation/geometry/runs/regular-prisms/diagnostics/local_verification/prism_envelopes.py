"""LOCAL: full /api/analyze envelopes through run_pipeline (model stubbed: corpus contract + model-style program;
0 model calls).
  - served rows given on the command line ⇒ <out>/<row>.fixture.json for the browser replay (openFixture);
  - C0 contradiction rows of probe_extra.py ⇒ envelope status, no answer, no Scene3D, and how many times the program
    stage was called (1 = no LLM repair round).
Run from backend/ (PYTHONPATH=.): python prism_envelopes.py <run dir> <out dir> <row> [<row> …]"""
import asyncio, importlib.util, json, os, sys
sys.path.insert(0, os.getcwd()); sys.path.insert(0, os.path.join(sys.argv[1], "diagnostics"))
from cases import LABELS, hop_dong_va_chuong_trinh
from app.ai import pipeline as PL

spec = importlib.util.spec_from_file_location("probe_extra", os.path.join(sys.argv[1], "diagnostics", "probe_extra.py"))
PE = importlib.util.module_from_spec(spec)
spec.loader.exec_module(PE)                                       # main() is guarded; only builders are loaded


def pipeline(text, c, sp):
    calls = {"program": 0}

    async def analyze(*_a, **_k):
        return c, None

    async def program(*_a, **_k):
        calls["program"] += 1
        return sp, None

    PL.stage_semantic_analyze, PL.stage_semantic_program = analyze, program
    os.environ.pop("GEOMETRY_COMPILER_MODE", None)
    return asyncio.run(PL.run_pipeline(text, "fake_key")), calls["program"]


out = sys.argv[2]
os.makedirs(out, exist_ok=True)
for rid in sys.argv[3:]:
    c, sp = hop_dong_va_chuong_trinh(rid)
    env, n = pipeline(LABELS[rid]["text"], c, sp)
    v = next((o.get("value") for o in (env.get("scene3d") or {}).get("objects", []) if o.get("id") == "V"), None)
    print(json.dumps({"row": rid, "status": env.get("status"), "value": v, "program_calls": n,
                      "chart_metric": "chart_metric" in (env.get("scene3d") or {})}, ensure_ascii=False))
    with open(os.path.join(out, f"{rid}.fixture.json"), "w", encoding="utf-8") as f:
        json.dump({"problem_text": LABELS[rid]["text"], "envelope": env}, f, ensure_ascii=False)

# C0 contradictions (built exactly as probe_extra.py does)
for nm, base in (("hex", PE.HEX), ("tri", PE.TRI)):
    for rid, shift, suffix in ((f"C0_{nm}_skew", [1, 1, 0] if nm == "hex" else [2, 1, 0], ""),
                               (f"C0_{nm}_lateral_contradicts", [1, 1, 1], " có cạnh bên bằng 2"),
                               (f"C0_{nm}_base_side_contradicts", [1, 1, 1], " có cạnh đáy bằng 1")):
        pts = {**base, **{p + "'": [a + b for a, b in zip(v, shift)] for p, v in base.items()}}
        nn, t = "".join(base), "".join(p + "'" for p in base)
        PE.M.LABELS[rid] = {"text": f"Cho hình {PE.PHRASE[nm]} {nn}.{t}{suffix} với {{coords}}. Tính thể tích khối lăng trụ "
                                    f"{nn}.{t}.", "points": pts,
                            "solid": {"kind": "prism", "base": list(base), "top": [p + "'" for p in base]}}
        de, c, sp = PE.M.hop_dong_va_chuong_trinh(rid)
        env, n = pipeline(de, c, sp)
        body = json.dumps(env, ensure_ascii=False)
        print(json.dumps({"row": rid, "status": env.get("status"), "scene3d": bool(env.get("scene3d")),
                          "reason_in_envelope": "SOURCE_SHAPE_CONTRADICTS_COORDINATES" in body,
                          "program_calls": n}, ensure_ascii=False))
