# -*- coding: utf-8 -*-
"""W17 — cache evidence by rows. 0 model calls.

Question: would an envelope served BEFORE W17 (CACHE_VERSION 108) still be returned from the
cache after W17, although W17 refuses that request (operation binding §15.1, goal-clause grounding §15.2)?

Same two modes as `w16-premerge-closure/diagnostics/proof_cache_row_w16.py`:
  envelopes --backend <backend dir> --out <json>
      runs every W17 corpus row (frozen contract + frozen program, JSON — loads in both trees)
      through `run_pipeline` with the code of <backend dir>: a detached worktree at the W17
      start dd6e86b0 (W16 end) for "before", the main tree for "W17";
  prove --before <json> --w17 <json> --out <json>
      with DATABASE_URL pointing at a TEMPORARY sqlite file: stores every "before" envelope with
      status "ok" as a cache row under the current CACHE_VERSION, asks `_cache_lookup` whether it
      HITs, simulates the bump, and compares with the W17 envelope.
"""
from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
import os
import sys
from pathlib import Path

CORPUS = Path(__file__).resolve().parent / "assumption_corpus_w17" / "CORPUS.json"


def _tom_tat(env: dict) -> dict:
    return {"status": env.get("status"), "stage_reached": env.get("stage_reached"),
            "reason_code": env.get("reason_code"),
            "envelope_sha256": hashlib.sha256(json.dumps(env, sort_keys=True, ensure_ascii=False,
                                                         default=str).encode("utf-8")).hexdigest()}


def envelopes(backend: Path, out: Path) -> None:
    if out.exists():
        raise SystemExit(f"refusing to overwrite {out}")
    sys.path.insert(0, str(backend))
    os.environ["GEOMETRY_COMPILER_MODE"] = "LLM_ONLY"
    from app.ai import pipeline as PL
    from app.simulation.semantic_program.contract import SemanticProgramSpec
    from app.simulation.semantic_program.request_contract import RequestContract
    from scripts import replay_negative_boundaries as RNB

    async def khong_goi(*_a, **_k):
        raise AssertionError("proof attempted a live model call")

    def chay(contract, spec) -> dict:
        goc = (PL.stage_semantic_analyze, PL.stage_semantic_program, PL.call_gemini)

        async def a(*_x, **_k):
            return contract, None

        async def p(*_x, **_k):
            return spec, None

        PL.stage_semantic_analyze, PL.stage_semantic_program, PL.call_gemini = a, p, khong_goi
        try:
            with RNB.NetworkGuard() as g:
                env = asyncio.run(PL.run_pipeline(contract.problem_text, "REPLAY_KHONG_PHAI_KEY",
                                                  semantic_route="serve"))
            assert not g.attempts
            return env
        finally:
            PL.stage_semantic_analyze, PL.stage_semantic_program, PL.call_gemini = goc

    ra = {}
    for r in json.loads(CORPUS.read_text(encoding="utf-8"))["rows"]:
        ct = RequestContract.model_validate(r["contract"])
        ra[r["id"]] = {"text": ct.problem_text, "group": r["group"], "label": r["label"],
                       "envelope": chay(ct, SemanticProgramSpec.model_validate(r["program"]))}
    out.write_text(json.dumps(ra, ensure_ascii=False, default=str) + "\n", encoding="utf-8", newline="\n")
    print(out, {k: _tom_tat(v["envelope"])["status"] for k, v in ra.items()})


def prove(before: Path, w17: Path, out: Path) -> None:
    if out.exists():
        raise SystemExit(f"refusing to overwrite {out}")
    url = os.environ.get("DATABASE_URL", "")
    if not url.startswith("sqlite:///") or "w17_cache_proof" not in url:
        raise SystemExit("set DATABASE_URL=sqlite:///<scratch>/w17_cache_proof.db (never the dev DB)")
    sys.path.insert(0, str(Path(__file__).resolve().parents[6] / "backend"))
    import app.main as M
    from app.main import DSL_VERSION, SessionLocal, SimulationCache, _cache_key, _cache_lookup, init_db

    init_db()
    truoc = json.loads(before.read_text(encoding="utf-8"))
    sau = json.loads(w17.read_text(encoding="utf-8"))
    hang: dict = {}
    with SessionLocal() as s:
        for ca, v in truoc.items():
            env, text = v["envelope"], v["text"]
            row = {"group": v["group"], "label": v["label"], "before_w17": _tom_tat(env),
                   "w17": _tom_tat(sau[ca]["envelope"])}
            if env.get("status") != "ok":
                row["cached_before_w17"] = False  # main.py caches only status == "ok"
                hang[ca] = row
                continue
            key = _cache_key(text)
            s.query(SimulationCache).filter_by(key=key).delete()
            s.add(SimulationCache(key=key, problem_text=text, simulation_id=env.get("simulation_id") or "proof",
                                  envelope_json=json.dumps(env, ensure_ascii=False, default=str),
                                  dsl_version=DSL_VERSION, policy_version=M.CACHE_VERSION))
            s.commit()
            row["cached_before_w17"] = True
            row["HIT_under_current_version"] = _cache_lookup(s, key) is not None
            goc = M.CACHE_VERSION
            try:
                M.CACHE_VERSION = str(int(goc) + 1)
                row["HIT_after_simulated_bump"] = _cache_lookup(s, key) is not None
            finally:
                M.CACHE_VERSION = goc
            row["w17_refuses_what_was_served"] = sau[ca]["envelope"].get("status") != "ok"
            row["replayed_envelope_differs_from_w17"] = (
                row["before_w17"]["envelope_sha256"] != row["w17"]["envelope_sha256"])
            s.query(SimulationCache).filter_by(key=key).delete()
            s.commit()
            hang[ca] = row
    stale = [ca for ca, r in hang.items() if r.get("HIT_under_current_version") and r.get("w17_refuses_what_was_served")]
    ket = {"proof": "W17_CACHE_ROW_PROOF", "model_calls": 0, "cache_version_current": M.CACHE_VERSION,
           "rows": hang, "stale_rows_replayed_under_current_version": stale,
           "bump_makes_them_miss": all(not hang[c]["HIT_after_simulated_bump"] for c in stale),
           "CACHE_DECISION": ("BUMP — envelopes served before W17 would be replayed under the current version "
                              f"although W17 refuses them: {stale}") if stale else
                             "NO_BUMP — no served envelope is refused under W17"}
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
    p.add_argument("--w17", type=Path, required=True)
    p.add_argument("--out", type=Path, required=True)
    a = ap.parse_args()
    if a.mode == "envelopes":
        envelopes(a.backend.resolve(), a.out)
    else:
        prove(a.before, a.w17, a.out)
