# -*- coding: utf-8 -*-
"""W20 — cache evidence by rows (pattern of `w18-binding-focus/diagnostics/proof_cache_row_w18.py`, immutable).
0 model calls.

Question: would an envelope served BEFORE W20 (CACHE_VERSION 110) still be returned from the cache after W20,
although W20 refuses that request (§17, a text-relation target defined by coordinates)?

Three modes:
  corpus --out <json>
      serializes the 27 W20 LABELS rows (contract + program JSON) from the builders of
      `backend/tests/geometry/test_construction_binding_literal.py` (main tree), so both trees load the same rows;
  envelopes --backend <backend dir> --corpus <json> --out <json>
      runs every row through `run_pipeline` with the code of <backend dir> (LLM stages replaced by the frozen
      contract and program): a detached worktree at f0edcd11 (product = W19 end) for "before", the tree at the
      fix for "after";
  prove --before <json> --after <json> --out <json>
      with DATABASE_URL pointing at a TEMPORARY sqlite file: stores every "before" envelope with status "ok" as a
      cache row under the current CACHE_VERSION, asks `_cache_lookup` whether it HITs, simulates the bump, and
      compares with the "after" envelope.
Every mode refuses to overwrite its output.
"""
from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
import os
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[6]


def _tom_tat(env: dict) -> dict:
    return {"status": env.get("status"), "stage_reached": env.get("stage_reached"), "reason_code": env.get("reason_code"),
            "envelope_sha256": hashlib.sha256(json.dumps(env, sort_keys=True, ensure_ascii=False,
                                                         default=str).encode("utf-8")).hexdigest()}


def _khong_ghi_de(out: Path) -> None:
    if out.exists():
        raise SystemExit(f"refusing to overwrite {out}")


def corpus(out: Path) -> None:
    _khong_ghi_de(out)
    sys.path.insert(0, str(REPO / "backend"))
    from tests.geometry import test_construction_binding_literal as T20

    rows = []
    for ca in T20.NHAN:
        contract, program = T20.CA[ca]()
        rows.append({"id": ca, "label": T20.NHAN[ca]["expect"],
                     "contract": contract.model_dump(mode="json"), "program": program})
    out.write_text(json.dumps({"source": "tests/geometry/test_construction_binding_literal.py CA (= probe builders)",
                               "rows": rows}, ensure_ascii=False, indent=1) + "\n", encoding="utf-8", newline="\n")
    print(out, len(rows), "rows")


def envelopes(backend: Path, corpus_json: Path, out: Path) -> None:
    _khong_ghi_de(out)
    sys.path.insert(0, str(backend))
    os.environ["GEOMETRY_COMPILER_MODE"] = "LLM_ONLY"
    from app.ai import pipeline as PL
    from app.simulation.semantic_program.request_contract import RequestContract
    from app.simulation.semantic_program.validator import validate_semantic_program
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
                env = asyncio.run(PL.run_pipeline(contract.problem_text, "REPLAY_KHONG_PHAI_KEY", semantic_route="serve"))
            assert not g.attempts
            return env
        finally:
            PL.stage_semantic_analyze, PL.stage_semantic_program, PL.call_gemini = goc

    ra = {}
    for r in json.loads(corpus_json.read_text(encoding="utf-8"))["rows"]:
        ct = RequestContract.model_validate(r["contract"])
        v = validate_semantic_program(r["program"])
        ra[r["id"]] = {"text": ct.problem_text, "label": r["label"],
                       "envelope": chay(ct, v.spec) if v.spec is not None else {"status": "invalid_program"}}
    out.write_text(json.dumps(ra, ensure_ascii=False, default=str) + "\n", encoding="utf-8", newline="\n")
    print(out, {k: v["envelope"].get("status") for k, v in ra.items()})


def prove(before: Path, after: Path, out: Path) -> None:
    _khong_ghi_de(out)
    url = os.environ.get("DATABASE_URL", "")
    if not url.startswith("sqlite:///") or "w20_cache_proof" not in url:
        raise SystemExit("set DATABASE_URL=sqlite:///<scratch>/w20_cache_proof.db (never the dev DB)")
    sys.path.insert(0, str(REPO / "backend"))
    import app.main as M
    from app.main import DSL_VERSION, SessionLocal, SimulationCache, _cache_key, _cache_lookup, init_db

    init_db()
    truoc = json.loads(before.read_text(encoding="utf-8"))
    sau = json.loads(after.read_text(encoding="utf-8"))
    hang: dict = {}
    with SessionLocal() as s:
        for ca, v in truoc.items():
            env, text = v["envelope"], v["text"]
            row = {"label": v["label"], "before_w20": _tom_tat(env), "w20": _tom_tat(sau[ca]["envelope"])}
            if env.get("status") != "ok":
                row["cached_before_w20"] = False  # main.py caches only status == "ok"
                hang[ca] = row
                continue
            key = _cache_key(text)
            s.query(SimulationCache).filter_by(key=key).delete()
            s.add(SimulationCache(key=key, problem_text=text, simulation_id=env.get("simulation_id") or "proof",
                                  envelope_json=json.dumps(env, ensure_ascii=False, default=str),
                                  dsl_version=DSL_VERSION, policy_version=M.CACHE_VERSION))
            s.commit()
            row["cached_before_w20"] = True
            row["HIT_under_current_version"] = _cache_lookup(s, key) is not None
            goc = M.CACHE_VERSION
            try:
                M.CACHE_VERSION = str(int(goc) + 1)
                row["HIT_after_simulated_bump"] = _cache_lookup(s, key) is not None
            finally:
                M.CACHE_VERSION = goc
            row["w20_refuses_what_was_served"] = sau[ca]["envelope"].get("status") != "ok"
            s.query(SimulationCache).filter_by(key=key).delete()
            s.commit()
            hang[ca] = row
    stale = [ca for ca, r in hang.items() if r.get("HIT_under_current_version") and r.get("w20_refuses_what_was_served")]
    ket = {"proof": "W20_CACHE_ROW_PROOF", "model_calls": 0, "cache_version_current": M.CACHE_VERSION,
           "rows": hang, "stale_rows_replayed_under_current_version": stale,
           "bump_makes_them_miss": all(not hang[c]["HIT_after_simulated_bump"] for c in stale),
           "CACHE_DECISION": ("BUMP — envelopes served before W20 would be replayed under the current version "
                              f"although W20 refuses them: {stale}") if stale else
                             "NO_BUMP — no served envelope is refused under W20"}
    out.write_text(json.dumps(ket, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps({k: ket[k] for k in ("cache_version_current", "stale_rows_replayed_under_current_version",
                                          "bump_makes_them_miss", "CACHE_DECISION")}, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="mode", required=True)
    c = sub.add_parser("corpus")
    c.add_argument("--out", type=Path, required=True)
    e = sub.add_parser("envelopes")
    e.add_argument("--backend", type=Path, required=True)
    e.add_argument("--corpus", type=Path, required=True)
    e.add_argument("--out", type=Path, required=True)
    p = sub.add_parser("prove")
    p.add_argument("--before", type=Path, required=True)
    p.add_argument("--after", type=Path, required=True)
    p.add_argument("--out", type=Path, required=True)
    a = ap.parse_args()
    if a.mode == "corpus":
        corpus(a.out)
    elif a.mode == "envelopes":
        envelopes(a.backend.resolve(), a.corpus, a.out)
    else:
        prove(a.before, a.after, a.out)
