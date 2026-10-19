# -*- coding: utf-8 -*-
"""Cache 126 -> 127 probe, v2 (Wave 1, `segment3.perpendicular_witness` on the default LLM_ONLY route).

v2 of `../../hybrid-architecture-wave1-exact-certificates-planner/cache/cache_probe.py` (kept unchanged): adds the
served prism family (right triangular prism, cuboid, cube, square prism) and the rectangular pyramid with a given
SA ⟂ base, because the independent review found that v1 had no served prism case and the prism branch was dead.

Run ONCE PER TREE, 0 model calls:

    <tree>/backend/.venv/Scripts/python.exe cache_probe.py <tree>/backend <out.json> [--rows <rows.json>]

Each case goes through the real `POST /api/analyze` of that tree (domain gate, cache lookup, `run_pipeline`, cache write)
with only the two LLM stages replaced by a fixed contract + program from the committed route cases. The database is a
fresh SQLite file in a temp directory (never `backend/algosim.db`); outbound sockets are refused. Request 1 must be a MISS
that writes one row, request 2 must be a HIT on that row. `--rows` also dumps the raw cache rows (on `main` these are
genuine rows written by v126 code — the legacy fixture of `test_cache_segment_witness_invalidation.py`).
"""
from __future__ import annotations

import hashlib
import json
import os
import socket
import sys
import tempfile

BACKEND = os.path.abspath(sys.argv[1])
OUT = os.path.abspath(sys.argv[2])
ROWS = os.path.abspath(sys.argv[sys.argv.index("--rows") + 1]) if "--rows" in sys.argv else None

sys.path.insert(0, BACKEND)
os.chdir(BACKEND)
_db = os.path.join(tempfile.mkdtemp(prefix="cache127-probe-"), "probe.db").replace("\\", "/")
os.environ["DATABASE_URL"] = f"sqlite:///{_db}"
os.environ["GEMINI_API_KEY"] = "khoa-gia"
for _k in ("ALLOW_LIVE_AI", "GEOMETRY_COMPILER_MODE", "SEMANTIC_TELEMETRY"):
    os.environ.pop(_k, None)


_connect = socket.socket.connect


def _loopback_only(self, addr, *a, **k):
    # asyncio's Windows self-pipe is a loopback socketpair; anything else would be a provider call.
    host = addr[0] if isinstance(addr, tuple) else str(addr)
    if host not in ("127.0.0.1", "::1", "localhost"):
        raise RuntimeError(f"cache_probe: network is blocked (0 provider calls): {addr!r}")
    return _connect(self, addr, *a, **k)


socket.socket.connect = _loopback_only  # type: ignore[method-assign]

from fastapi.testclient import TestClient  # noqa: E402

import app.main as M  # noqa: E402
from app.ai import pipeline as PL  # noqa: E402
from app.persistence.db import SessionLocal, SimulationCache, init_db  # noqa: E402
from tests.geometry import route_cases as W  # noqa: E402
from tests.geometry import test_regular_square_pyramid as RSP  # noqa: E402


def _rsp(ca):
    contract, prog = RSP.CA[ca]()
    return RSP.NHAN[ca]["text"], contract, prog


#: id -> (text, contract, program). S1/S6/S7 (regular square pyramid) gain a certified altitude SO; the right-triangle
#: pyramid with the GIVEN SA ⊥ (ABC) (not regular, A is not the base centre) gains SA only — its lateral edges SB, SC
#: are oblique and must never carry a marker. Right prisms / cuboid / cube gain one witness per lateral edge, never on a
#: base or top edge. The oblique prism without a given height is refused on every tree: a refusal is never cached, so it
#: is the "unchanged refusal" control.
CASES = {
    "S1_side_height_volume": lambda: _rsp("S1_side_height_volume"),
    "S6_renamed_vertices": lambda: _rsp("S6_renamed_vertices"),
    "S7_named_centre": lambda: _rsp("S7_named_centre"),
    "SA_given_right_triangle_pyramid": lambda: _compiled(*W.chop_tam_giac()),
    "SA_given_rectangular_pyramid": lambda: _compiled(*W.chop_chu_nhat()),
    "right_triangular_prism": lambda: _compiled(*W.lang_tru_tam_giac()),
    "cuboid": lambda: _compiled(*W.hop_chu_nhat()),
    "cube": lambda: _compiled(*W.lap_phuong()),
    "square_prism": lambda: _compiled(*W.lang_tru_day_vuong()),
    "REFUSED_oblique_prism": lambda: (W.LANG_TRU_XIEN_TEXT, *W.ca_lang_tru_xien()),
}


def _compiled(text, contract):
    return text, contract, W.chuong_trinh(contract)


def _canon(d: dict) -> str:
    return json.dumps({k: v for k, v in d.items() if k not in ("cached", "source")}, ensure_ascii=False, sort_keys=True)


def _sha(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


def _witnesses(env: dict) -> dict:
    sc = env.get("scene3d") or {}
    return {o["id"]: {k: o["perpendicular_witness"].get(k) for k in ("from", "foot_id", "on", "rule", "status")}
            for o in sc.get("objects", []) if o.get("type") == "segment3" and "perpendicular_witness" in o}


def _answers(env: dict) -> dict:
    sc = env.get("scene3d") or {}
    return {o["id"]: o.get("value") for o in sc.get("objects", []) if o.get("value") is not None}


def main() -> int:
    init_db()
    client = TestClient(M.app)
    calls = {"analyze": 0, "program": 0}
    report, rows = {"cache_version": M.CACHE_VERSION, "cases": {}}, {}
    for cid, make in CASES.items():
        text, contract, prog = make()
        sp = W.spec_cua(prog)

        async def analyze(*_a, _c=contract, **_k):
            calls["analyze"] += 1
            return _c, None

        async def program(*_a, _s=sp, **_k):
            calls["program"] += 1
            return _s, None

        PL.stage_semantic_analyze, PL.stage_semantic_program = analyze, program
        r1 = client.post("/api/analyze", json={"input": {"type": "text", "content": text}})
        r2 = client.post("/api/analyze", json={"input": {"type": "text", "content": text}})
        e1, e2 = r1.json(), r2.json()
        key = M._cache_key(text)
        with SessionLocal() as s:
            got = s.query(SimulationCache).filter_by(key=key).all()
            row = got[0] if got else None
            rows[cid] = None if row is None else {"text": text, "key": key, "policy_version": row.policy_version,
                                                  "dsl_version": row.dsl_version, "simulation_id": row.simulation_id,
                                                  "envelope_json": row.envelope_json}
        report["cases"][cid] = {
            "http": [r1.status_code, r2.status_code],
            "status": e1.get("status"),
            "request1": {"cached": bool(e1.get("cached")), "source": e1.get("source")},
            "request2": {"cached": bool(e2.get("cached")), "source": e2.get("source")},
            "rows_for_key": len(got),
            "row_policy_version": None if row is None else row.policy_version,
            "envelope_sha256_fresh": _sha(_canon(e1)),
            "envelope_sha256_cached": _sha(_canon(e2)),
            "cached_equals_fresh": _canon(e1) == _canon(e2),
            "scene3d_bytes": len(json.dumps(e1.get("scene3d") or {}, ensure_ascii=False, sort_keys=True)),
            "segment3_perpendicular_witness": _witnesses(e1),
            "segment3_perpendicular_witness_cached": _witnesses(e2),
            "answers": _answers(e1),
        }
    report["llm_stage_stub_calls"] = calls
    report["provider_requests"] = 0
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=1, sort_keys=True)
        f.write("\n")
    if ROWS:
        with open(ROWS, "w", encoding="utf-8") as f:
            json.dump({"written_by_cache_version": M.CACHE_VERSION, "rows": rows}, f, ensure_ascii=False, indent=1,
                      sort_keys=True)
            f.write("\n")
    print(json.dumps({c: (v["status"], v["request1"], v["request2"], v["segment3_perpendicular_witness"])
                      for c, v in report["cases"].items()}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
