# -*- coding: utf-8 -*-
"""regular-square-pyramid-w01 — cache evidence by rows (pattern of `w20-cleanup-premerge/diagnostics/
proof_cache_row_w20.py`, immutable). 0 model calls.

Question: would an envelope served BEFORE W1 (CACHE_VERSION 111) still be returned from the cache after W1,
although W1 now serves that request with DIFFERENT content (or refuses it)?

Rows: the 17 W1 corpus rows (`backend/tests/geometry/test_regular_square_pyramid.py`, LABELS.json) plus two
probes of the W1 paths that can change a request that was already served before W1:
  P_cube_notationless_given — a cube whose GIVEN edge has no segment name (`_nhan_du_kien_tu_fact`);
  P_rect_pyramid_two_heights — SA given and d(S, (ABC)) measured (apex-to-base-plane height rule).

Modes (each refuses to overwrite its output):
  corpus --out <json>                                     rows serialised from the main-tree builders;
  envelopes --backend <backend dir> --corpus <json> --out <json>
      every row through `run_pipeline` with <backend dir>'s code (LLM stages replaced by the frozen contract and
      program): a detached worktree at 38d41588 (main before W1) for "before", the W1 tree for "after";
  prove --before <json> --after <json> --out <json>
      DATABASE_URL must point at a TEMPORARY sqlite file: stores each "before" envelope with status "ok" as a cache
      row under the current CACHE_VERSION, asks `_cache_lookup` whether it HITs, simulates the bump, and compares
      the "after" envelope by sha256.
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


def _sha(env: dict) -> str:
    return hashlib.sha256(json.dumps(env, sort_keys=True, ensure_ascii=False, default=str).encode("utf-8")).hexdigest()


def _tom_tat(env: dict) -> dict:
    return {"status": env.get("status"), "stage_reached": env.get("stage_reached"),
            "reason_code": env.get("reason_code"), "envelope_sha256": _sha(env)}


def _khong_ghi_de(out: Path) -> None:
    if out.exists():
        raise SystemExit(f"refusing to overwrite {out}")


def _lap_phuong(W):
    van = "Cho hình lập phương ABCD.A'B'C'D' có cạnh bằng 4. Tính thể tích khối lập phương."
    pay = {"input_facts": [{"id": "f_canh", "kind": "float", "label": "cạnh", "value": ["4"]}],
           "obligations": [{"kind": "volume", "container": "khoi", "witness": "V"}],
           "solid_topology": {"solid_kind": "prism", "base_cycle": ["A", "B", "C", "D"],
                              "top_cycle": ["A'", "B'", "C'", "D'"],
                              "correspondence": [["A", "A'"], ["B", "B'"], ["C", "C'"], ["D", "D'"]]}}
    ten = {"A": "A", "B": "B", "C": "C", "D": "D", "A'": "A_prime", "B'": "B_prime", "C'": "C_prime", "D'": "D_prime"}
    toa = {"A": "000", "B": "400", "C": "440", "D": "040", "A'": "004", "B'": "404", "C'": "444", "D'": "044"}
    mem = [{"name": "canh", "type": "float", "provenance": "GIVEN", "source_fact_id": "f_canh", "initial_value": "4"}]
    mem += [{"name": ten[p], "type": "point3", "provenance": "LAYOUT_DERIVED"} for p in toa]
    mem += [{"name": "khoi", "type": "solid"}, {"name": "V", "type": "float"}]
    n = lambda *ps: [ten[p] for p in ps]  # noqa: E731
    st = [{"kind": "declare_point", "target_var": ten[p], "at": list(v)} for p, v in toa.items()]
    st += [{"kind": "construct_solid", "target_var": "khoi", "vertices": n(*toa),
            "faces": [n("A", "B", "C", "D"), n("A'", "B'", "C'", "D'"), n("A", "B", "B'", "A'"),
                      n("B", "C", "C'", "B'"), n("C", "D", "D'", "C'"), n("D", "A", "A'", "D'")],
            "label": "ABCD.A'B'C'D'"},
           {"kind": "assign", "target_var": "V", "expr": {"kind": "measure", "quantity": "volume", "of": "khoi"}}]
    return W.hop_dong(van, pay), {"spec_version": "1.0", "title": "Lập phương", "memory_declarations": mem,
                                  "statements": st}


def corpus(out: Path) -> None:
    _khong_ghi_de(out)
    sys.path.insert(0, str(REPO / "backend"))
    from tests.geometry import test_regular_square_pyramid as T
    from tests.geometry import w14_cases as W

    rows = []
    for ca in sorted(T.NHAN):
        contract, program = T._nap(ca)
        rows.append({"id": ca, "label": T.NHAN[ca]["expect"], "contract": contract.model_dump(mode="json"),
                     "program": program})
    for ca, build in (("P_cube_notationless_given", lambda: _lap_phuong(W)),
                      ("P_rect_pyramid_two_heights", T._chop_chu_nhat_co_ca_SA_va_khoang_cach)):
        contract, program = build()
        rows.append({"id": ca, "label": "probe:served_before_w1", "contract": contract.model_dump(mode="json"),
                     "program": program})
    out.write_text(json.dumps({"source": "tests/geometry/test_regular_square_pyramid.py (_nap, NHAN, "
                                         "_chop_chu_nhat_co_ca_SA_va_khoang_cach) + _lap_phuong (this script)",
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
    if not url.startswith("sqlite:///") or "w01_cache_proof" not in url:
        raise SystemExit("set DATABASE_URL=sqlite:///<scratch>/w01_cache_proof.db (never the dev DB)")
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
            row = {"label": v["label"], "before_w01": _tom_tat(env), "w01": _tom_tat(sau[ca]["envelope"])}
            if env.get("status") != "ok":
                row["cached_before_w01"] = False  # main.py caches only status == "ok"
                hang[ca] = row
                continue
            key = _cache_key(text)
            s.query(SimulationCache).filter_by(key=key).delete()
            s.add(SimulationCache(key=key, problem_text=text, simulation_id=env.get("simulation_id") or "proof",
                                  envelope_json=json.dumps(env, ensure_ascii=False, default=str),
                                  dsl_version=DSL_VERSION, policy_version=M.CACHE_VERSION))
            s.commit()
            row["cached_before_w01"] = True
            row["HIT_under_current_version"] = _cache_lookup(s, key) is not None
            goc = M.CACHE_VERSION
            try:
                M.CACHE_VERSION = str(int(goc) + 1)
                row["HIT_after_simulated_bump"] = _cache_lookup(s, key) is not None
            finally:
                M.CACHE_VERSION = goc
            row["w01_envelope_differs"] = _sha(env) != _sha(sau[ca]["envelope"])
            s.query(SimulationCache).filter_by(key=key).delete()
            s.commit()
            hang[ca] = row
    stale = [ca for ca, r in hang.items() if r.get("HIT_under_current_version") and r.get("w01_envelope_differs")]
    ket = {"proof": "W01_CACHE_ROW_PROOF", "model_calls": 0, "cache_version_current": M.CACHE_VERSION,
           "rows": hang, "stale_rows_replayed_under_current_version": stale,
           "bump_makes_them_miss": all(not hang[c]["HIT_after_simulated_bump"] for c in stale),
           "CACHE_DECISION": ("BUMP — envelopes served before W1 would be replayed under the current version "
                              f"although W1 now builds a different envelope: {stale}") if stale else
                             "NO_BUMP — every envelope served before W1 is unchanged under W1"}
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
