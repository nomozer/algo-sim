# -*- coding: utf-8 -*-
"""W14 Task 7 — cache evidence by REAL rows. 0 model calls.

Question: would an envelope served BEFORE W14 still be returned from the cache under
CACHE_VERSION 105, although W14 refuses that input or serves a different formation?

Two modes, one script:
  envelopes --backend <backend dir> --out <json>
      runs the frozen cases through `run_pipeline` with the code of <backend dir>
      (a detached worktree at the W14 base commit for "before", the main tree for "W14");
  prove --before <json> --w14 <json> --out <json>
      with DATABASE_URL pointing at a TEMPORARY sqlite file: stores every "before" envelope
      with status "ok" as a cache row under the current CACHE_VERSION, asks `_cache_lookup`
      whether it HITs, simulates the bump, and compares with the W14 envelope.

Cases (all with problem text, frozen analyze + frozen program, provider never called):
  dai_cm_wrong_segment  text states "AB dài 5 cm" and never AC; the program declares
                        AC_length = 5 (the leaked number) — W13 NA-57 served → rejected;
  s4_llm_gold_p1        thesis gold p1 (polyhedral pyramid + section): S4 formation change;
  textless_contract     not reachable through /api/analyze (the contract always carries the
                        request text and the cache key is that text) — recorded, not stored;
  assumption_probe      only if Track B shipped — it did not (ASSUMPTION_POLICY_INCOMPLETE).
"""
from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
import os
import sys
from pathlib import Path

DE_DAI_CM = ("Cho hình chóp S.ABC có đáy ABC là tam giác vuông tại A, AB dài 5 cm. "
             "Cạnh bên SA vuông góc với đáy, SA = 3. Tính thể tích khối chóp S.ABC.")
P1 = "p1_chop_thiet_dien_khoang_cach"


def _payload_dai_cm() -> dict:
    """What a mislabelling analyze pass would produce: AC = 5 read off "AB dài 5 cm"."""
    return {
        "input_facts": [
            {"id": "fact_len_AB", "kind": "float", "label": "AB", "value": ["5"]},
            {"id": "fact_len_AC", "kind": "float", "label": "AC", "value": ["5"]},
            {"id": "fact_len_SA", "kind": "float", "label": "SA", "value": ["3"]},
        ],
        "geometric_relations": [
            {"kind": "perpendicular_lines", "line": ["A", "B"], "other_line": ["A", "C"],
             "source_fact_id": "fact_perp_base", "model_assumption": False},
            {"kind": "perpendicular_line_plane", "line": ["S", "A"], "plane": ["A", "B", "C"],
             "source_fact_id": "fact_perp_lateral", "model_assumption": False},
        ],
        "obligations": [{"kind": "volume", "container": "khoi_chop", "witness": "the_tich_khoi"}],
    }


def _tom_tat(env: dict) -> dict:
    sc = env.get("scene3d") or {}
    return {
        "status": env.get("status"),
        "stage_reached": env.get("stage_reached"),
        "error_code": env.get("error_code"),
        "reason_code": env.get("reason_code"),
        "frames": len(((env.get("config") or {}).get("frames")) or []),
        "scene_objects": len(sc.get("objects") or []),
        "formation_steps": len(((sc.get("formation") or {}).get("steps")) or []),
        "envelope_sha256": hashlib.sha256(json.dumps(env, sort_keys=True, ensure_ascii=False,
                                                     default=str).encode("utf-8")).hexdigest(),
    }


def envelopes(backend: Path, out: Path) -> None:
    sys.path.insert(0, str(backend))
    os.environ["GEOMETRY_COMPILER_MODE"] = "LLM_ONLY"
    from app.ai import pipeline as PL
    from app.simulation.geometry_compiler import compiler as C
    from app.simulation.geometry_compiler.contract_adapter import build_fact_graph
    from app.simulation.semantic_program.analyze_contract import build_request_contract
    from app.simulation.semantic_program.contract import SemanticProgramSpec
    from scripts import replay_negative_boundaries as RNB

    async def khong_goi(*_a, **_k):
        raise AssertionError("proof attempted a live model call")

    def chay_dong_bang(text: str, contract, spec) -> dict:
        goc = (PL.stage_semantic_analyze, PL.stage_semantic_program, PL.call_gemini)

        async def a(*_x, **_k):
            return contract, None

        async def p(*_x, **_k):
            return spec, None

        PL.stage_semantic_analyze, PL.stage_semantic_program, PL.call_gemini = a, p, khong_goi
        try:
            with RNB.NetworkGuard() as g:
                env = asyncio.run(PL.run_pipeline(text, "REPLAY_KHONG_PHAI_KEY", semantic_route="serve"))
            assert not g.attempts
            return env
        finally:
            PL.stage_semantic_analyze, PL.stage_semantic_program, PL.call_gemini = goc

    ra: dict = {}
    ct = build_request_contract(_payload_dai_cm(), problem_text=DE_DAI_CM, domain="hinh_hoc")
    bd = C.bien_dich(build_fact_graph(ct).graph)
    sp = SemanticProgramSpec.model_validate({"spec_version": "1.0", **bd.program})
    ra["dai_cm_wrong_segment"] = {"text": DE_DAI_CM, "envelope": chay_dong_bang(DE_DAI_CM, ct, sp)}

    raw = RNB.doc_raw_theo_thu_tu(P1)
    de = RNB.doc_de_bai()[P1]
    PL.call_gemini, goc = RNB.ProviderPhatLaiTheoThuTu(raw), PL.call_gemini
    try:
        with RNB.NetworkGuard() as g:
            env = asyncio.run(PL.run_pipeline(de, "REPLAY_KHONG_PHAI_KEY", semantic_route="serve"))
        assert not g.attempts
    finally:
        PL.call_gemini = goc
    ra["s4_llm_gold_p1"] = {"text": de, "envelope": env}
    out.write_text(json.dumps(ra, ensure_ascii=False, default=str) + "\n", encoding="utf-8", newline="\n")
    print(out, {k: _tom_tat(v["envelope"]) for k, v in ra.items()})


def prove(before: Path, w14: Path, out: Path) -> None:
    if out.exists():
        raise SystemExit(f"refusing to overwrite {out}")
    url = os.environ.get("DATABASE_URL", "")
    if not url.startswith("sqlite:///") or "w14_cache_proof" not in url:
        raise SystemExit("set DATABASE_URL=sqlite:///<scratch>/w14_cache_proof.db (never the dev DB)")
    sys.path.insert(0, str(Path(__file__).resolve().parents[6] / "backend"))
    import app.main as M
    from app.main import DSL_VERSION, SessionLocal, SimulationCache, _cache_key, _cache_lookup, init_db

    init_db()
    truoc = json.loads(before.read_text(encoding="utf-8"))
    sau = json.loads(w14.read_text(encoding="utf-8"))
    hang: dict = {}
    with SessionLocal() as s:
        for ca, v in truoc.items():
            env, text = v["envelope"], v["text"]
            row = {"before_w14": _tom_tat(env), "w14": _tom_tat(sau[ca]["envelope"])}
            if env.get("status") != "ok":
                row["cached_before_w14"] = False  # main.py caches only status == "ok"
                hang[ca] = row
                continue
            key = _cache_key(text)
            s.query(SimulationCache).filter_by(key=key).delete()
            s.add(SimulationCache(key=key, problem_text=text, simulation_id=env.get("simulation_id") or "proof",
                                  envelope_json=json.dumps(env, ensure_ascii=False, default=str),
                                  dsl_version=DSL_VERSION, policy_version=M.CACHE_VERSION))
            s.commit()
            row["cached_before_w14"] = True
            row["HIT_under_current_version"] = _cache_lookup(s, key) is not None
            goc = M.CACHE_VERSION
            try:
                M.CACHE_VERSION = str(int(goc) + 1)
                row["HIT_after_simulated_bump"] = _cache_lookup(s, key) is not None
            finally:
                M.CACHE_VERSION = goc
            row["replayed_envelope_differs_from_w14"] = (
                row["before_w14"]["envelope_sha256"] != row["w14"]["envelope_sha256"])
            s.query(SimulationCache).filter_by(key=key).delete()
            s.commit()
            hang[ca] = row
    hang["textless_contract"] = {"cached_before_w14": "NOT_REACHABLE",
                                 "why": "/api/analyze always builds the contract from the request text, and the "
                                        "cache key is that text; a textless contract never reaches the cache"}
    hang["assumption_probe"] = {"cached_before_w14": "NOT_APPLICABLE",
                                "why": "Track B did not ship (ASSUMPTION_POLICY_INCOMPLETE): no served -> rejected change"}
    stale = [ca for ca, r in hang.items() if r.get("HIT_under_current_version")
             and r.get("replayed_envelope_differs_from_w14")]
    ket = {
        "proof": "W14_CACHE_ROW_PROOF", "model_calls": 0,
        "cache_version_current": M.CACHE_VERSION,
        "rows": hang,
        "stale_rows_replayed_under_current_version": stale,
        "bump_makes_them_miss": all(not hang[c]["HIT_after_simulated_bump"] for c in stale),
        "CACHE_DECISION": ("BUMP — envelopes served before W14 would be replayed under the current version "
                           f"although W14 changes them: {stale}") if stale else
                          "NO_BUMP — no served envelope changes under W14",
    }
    out.write_text(json.dumps(ket, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps({k: ket[k] for k in ("stale_rows_replayed_under_current_version", "bump_makes_them_miss",
                                          "CACHE_DECISION")}, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="mode", required=True)
    e = sub.add_parser("envelopes")
    e.add_argument("--backend", type=Path, required=True)
    e.add_argument("--out", type=Path, required=True)
    p = sub.add_parser("prove")
    p.add_argument("--before", type=Path, required=True)
    p.add_argument("--w14", type=Path, required=True)
    p.add_argument("--out", type=Path, required=True)
    a = ap.parse_args()
    if a.mode == "envelopes":
        envelopes(a.backend.resolve(), a.out)
    else:
        prove(a.before, a.w14, a.out)
