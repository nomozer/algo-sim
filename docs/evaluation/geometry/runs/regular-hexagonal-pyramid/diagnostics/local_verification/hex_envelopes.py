"""LOCAL: full /api/analyze envelopes for chosen hexagonal rows through run_pipeline (model stubbed: the corpus
contract + model-style program), for a browser replay through the repository's existing openFixture. 0 model calls.
Run from backend/: python hex_envelopes.py <run dir> <out dir> <row> [<row> …]"""
import asyncio, json, os, sys
sys.path.insert(0, os.getcwd()); sys.path.insert(0, os.path.join(sys.argv[1], "diagnostics"))
from cases import LABELS, hop_dong_va_chuong_trinh
from app.ai import pipeline as PL

out = sys.argv[2]
os.makedirs(out, exist_ok=True)
for rid in sys.argv[3:]:
    c, sp = hop_dong_va_chuong_trinh(rid)

    async def analyze(*_a, **_k):
        return c, None

    async def program(*_a, **_k):
        return sp, None

    PL.stage_semantic_analyze, PL.stage_semantic_program = analyze, program
    os.environ.pop("GEOMETRY_COMPILER_MODE", None)
    env = asyncio.run(PL.run_pipeline(LABELS[rid]["text"], "fake_key"))
    v = next((o.get("value") for o in (env.get("scene3d") or {}).get("objects", []) if o.get("id") in ("V", "d_SA")), None)
    print(rid, env.get("status"), "value", v, "chart_metric", "chart_metric" in (env.get("scene3d") or {}))
    with open(os.path.join(out, f"{rid}.fixture.json"), "w", encoding="utf-8") as f:
        json.dump({"problem_text": LABELS[rid]["text"], "envelope": env}, f, ensure_ascii=False)
