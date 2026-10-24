# -*- coding: utf-8 -*-
"""Cache 127 -> 128 probe (backend display identity on the default LLM_ONLY route). 0 model calls.

Derived from `../../segment-witness-cache-invalidation/cache/cache_probe.py` (kept unchanged). Run ONCE PER TREE:

    python cache_probe.py <tree>/backend <out.json> [--rows <rows.json>]

Each case goes through the real `POST /api/analyze` of that tree (domain gate, cache lookup, `run_pipeline`, cache
write) with only the two LLM stages replaced by a fixed contract + program. Fresh SQLite in a temp dir; outbound
sockets refused. Request 1 must MISS and write one row, request 2 must HIT it.

Cases:
  * `declared_plane_P`: the offline sample `cau-cat-mat-phang` program (plane P declared "(P)" through construction
    points H, U, W) with a contract whose problem text writes "(P)". The default route refuses it on both trees
    (free layout points), so it is a refusal control, never cached.
  * `cube_named_plane_P`: the cube production case plus "Mặt phẳng (P) đi qua ba điểm A, B′, D′." and one
    `construct_plane` labelled "(P)" through those named vertices. Before: "(AB′D′)". After: "(P)".
  * the served families and the refusal of the previous probe: controls, expected byte-identical.
"""
from __future__ import annotations

import hashlib
import importlib.util
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
_db = os.path.join(tempfile.mkdtemp(prefix="cache128-probe-"), "probe.db").replace("\\", "/")
os.environ["DATABASE_URL"] = f"sqlite:///{_db}"
os.environ["GEMINI_API_KEY"] = "khoa-gia"
for _k in ("ALLOW_LIVE_AI", "GEOMETRY_COMPILER_MODE", "SEMANTIC_TELEMETRY"):
    os.environ.pop(_k, None)

_connect = socket.socket.connect


def _loopback_only(self, addr, *a, **k):
    host = addr[0] if isinstance(addr, tuple) else str(addr)
    if host not in ("127.0.0.1", "::1", "localhost"):
        raise RuntimeError(f"cache_probe: network is blocked (0 provider calls): {addr!r}")
    return _connect(self, addr, *a, **k)


socket.socket.connect = _loopback_only  # type: ignore[method-assign]

from fastapi.testclient import TestClient  # noqa: E402

import app.main as M  # noqa: E402
from app.ai import pipeline as PL  # noqa: E402
from app.persistence.db import SessionLocal, SimulationCache, init_db  # noqa: E402
from app.simulation.semantic_program.obligations import Obligation  # noqa: E402
from app.simulation.semantic_program.request_contract import RequestContract  # noqa: E402
from tests.geometry import route_cases as W  # noqa: E402
from tests.geometry import test_regular_square_pyramid as RSP  # noqa: E402

_spec = importlib.util.spec_from_file_location("bgs", os.path.join(BACKEND, "scripts", "build_geometry_samples.py"))
BGS = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(BGS)


def _rsp(ca):
    contract, prog = RSP.CA[ca]()
    return RSP.NHAN[ca]["text"], contract, prog


def _compiled(text, contract):
    return text, contract, W.chuong_trinh(contract)


def _declared_plane_p():
    prog = BGS.chuong_trinh_cau_cat_mp()
    text = prog["description"]
    contract = RequestContract(problem_text=text, obligations=(
        Obligation(kind="radius", container="C", params={"witness": "r"}),
        Obligation(kind="area", container="C", params={"witness": "S"})))
    return text, contract, prog


def _cube_plane_p():
    from tests.geometry import test_cuboid_cube_production_route as CC

    text, payload = CC._cube_p01_payload()
    text = f"{text} Mặt phẳng (P) đi qua ba điểm A, B′, D′."
    contract = W.hop_dong(text, payload)
    prog = W.chuong_trinh(contract)
    prog["memory_declarations"].append({"name": "P", "type": "plane3"})
    prog["statements"].append({"kind": "construct_plane", "target_var": "P", "label": "(P)",
                               "through": ["A", "B_prime", "D_prime"]})
    return text, contract, prog


CASES = {
    "declared_plane_P": _declared_plane_p,
    "cube_named_plane_P": _cube_plane_p,
    "S1_side_height_volume": lambda: _rsp("S1_side_height_volume"),
    "S7_named_centre": lambda: _rsp("S7_named_centre"),
    "SA_given_right_triangle_pyramid": lambda: _compiled(*W.chop_tam_giac()),
    "SA_given_rectangular_pyramid": lambda: _compiled(*W.chop_chu_nhat()),
    "right_triangular_prism": lambda: _compiled(*W.lang_tru_tam_giac()),
    "cuboid": lambda: _compiled(*W.hop_chu_nhat()),
    "cube": lambda: _compiled(*W.lap_phuong()),
    "REFUSED_oblique_prism": lambda: (W.LANG_TRU_XIEN_TEXT, *W.ca_lang_tru_xien()),
}


def _canon(d: dict) -> str:
    return json.dumps({k: v for k, v in d.items() if k not in ("cached", "source")}, ensure_ascii=False, sort_keys=True)


def _sha(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


def _names(env: dict) -> dict:
    sc = env.get("scene3d") or {}
    return {o["id"]: o.get("notation") for o in sc.get("objects", []) if o.get("type") in ("plane3", "section")}


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
            "http": [r1.status_code, r2.status_code], "status": e1.get("status"),
            "reason_code": e1.get("reason_code"),
            "request1": {"cached": bool(e1.get("cached")), "source": e1.get("source")},
            "request2": {"cached": bool(e2.get("cached")), "source": e2.get("source")},
            "rows_for_key": len(got), "row_policy_version": None if row is None else row.policy_version,
            "envelope_sha256_fresh": _sha(_canon(e1)), "cached_equals_fresh": _canon(e1) == _canon(e2),
            "plane_and_section_notation": _names(e1),
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
    print(json.dumps({c: (v["status"], v["request1"]["source"], v["request2"]["source"],
                          v["plane_and_section_notation"]) for c, v in report["cases"].items()}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
