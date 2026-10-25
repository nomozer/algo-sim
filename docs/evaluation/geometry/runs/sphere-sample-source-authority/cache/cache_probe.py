# -*- coding: utf-8 -*-
"""Cache 128 -> 129 probe (curved-section cutting plane role on the default LLM_ONLY route). 0 model calls.

Derived from `../../visual-hybrid-final-corrections/cache/cache_probe.py` (kept unchanged). Run ONCE PER TREE:

    python cache_probe.py <tree>/backend <out.json> [--rows <rows.json>]

Each case goes through the real `POST /api/analyze` of that tree (domain gate, cache lookup, `run_pipeline`, cache
write). Fresh SQLite in a temp dir; outbound sockets refused. Request 1 must MISS and write one row, request 2 HIT it.

Cases:
  * `p6_ellipse_section_of_cylinder`: the recorded live case `p6_thiet_dien_elip_cua_hinh_tru`, replayed through the
    real analyze/program stages by the offline replay provider (`tests.test_photo_problem_live_runner.RNB`). Before:
    the cutting plane carries `CONSTRUCT_AUXILIARY_GEOMETRY` (hidden once the ellipse exists). After:
    `CONSTRUCT_CUTTING_OBJECT`, as for a polyhedral section.
  * served polyhedral families and one refusal: controls, expected byte-identical / never cached.
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
_db = os.path.join(tempfile.mkdtemp(prefix="cache129-probe-"), "probe.db").replace("\\", "/")
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
from tests.geometry import route_cases as W  # noqa: E402
from tests.geometry import test_regular_square_pyramid as RSP  # noqa: E402
from tests.test_photo_problem_live_runner import CA_P6, RNB  # noqa: E402

_STAGES = (PL.stage_semantic_analyze, PL.stage_semantic_program, PL.call_gemini)


def _stubbed(text, contract, prog):
    return text, ("stub", contract, W.spec_cua(prog))


def _replayed(cid):
    return RNB.doc_de_bai()[cid], ("replay", RNB.ProviderPhatLaiTheoThuTu({**RNB.doc_raw_theo_thu_tu(cid)}), None)


def _rsp(ca):
    contract, prog = RSP.CA[ca]()
    return _stubbed(RSP.NHAN[ca]["text"], contract, prog)


def _compiled(text, contract):
    return _stubbed(text, contract, W.chuong_trinh(contract))


CASES = {
    "p6_ellipse_section_of_cylinder": lambda: _replayed(CA_P6),
    "S1_side_height_volume": lambda: _rsp("S1_side_height_volume"),
    "right_triangular_prism": lambda: _compiled(*W.lang_tru_tam_giac()),
    "cube": lambda: _compiled(*W.lap_phuong()),
    "REFUSED_oblique_prism": lambda: _stubbed(W.LANG_TRU_XIEN_TEXT, *W.ca_lang_tru_xien()),
}


def _canon(d: dict) -> str:
    return json.dumps({k: v for k, v in d.items() if k not in ("cached", "source")}, ensure_ascii=False, sort_keys=True)


def _sha(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


def _plane_roles(env: dict) -> dict:
    sc = env.get("scene3d") or {}
    return {o["id"]: o.get("formation_roles") for o in sc.get("objects", []) if o.get("type") == "plane3"}


def main() -> int:
    init_db()
    client = TestClient(M.app)
    report, rows = {"cache_version": M.CACHE_VERSION, "cases": {}}, {}
    for cid, make in CASES.items():
        text, (mode, a, b) = make()
        PL.stage_semantic_analyze, PL.stage_semantic_program, PL.call_gemini = _STAGES
        if mode == "stub":
            async def analyze(*_x, _c=a, **_k):
                return _c, None

            async def program(*_x, _s=b, **_k):
                return _s, None

            PL.stage_semantic_analyze, PL.stage_semantic_program = analyze, program
        else:
            PL.call_gemini = a
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
            "plane_formation_roles": _plane_roles(e1),
        }
    report["provider_requests"] = 0
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=1, sort_keys=True)
        f.write("\n")
    if ROWS:
        with open(ROWS, "w", encoding="utf-8") as f:
            json.dump({"written_by_cache_version": M.CACHE_VERSION, "rows": rows}, f, ensure_ascii=False, indent=1,
                      sort_keys=True)
            f.write("\n")
    print(json.dumps({c: (v["status"], v["request1"]["source"], v["request2"]["source"], v["plane_formation_roles"])
                      for c, v in report["cases"].items()}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
