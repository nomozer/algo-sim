# -*- coding: utf-8 -*-
"""Regression & cache-invalidation lock for undotted primed prism topology in `hop_dong_to_po_da_khai`.

Covers:
1. Undotted primed 4-gon & 3-gon prisms (`MNPQM'N'P'Q'`, `EFGE'F'G'`) produce byte-for-byte identical `Scene3D`
   objects, `ENGINE_VERIFIED` lateral-edge `perpendicular_witness`es, and 6-step causal formation timelines as the
   dotted notations (`MNPQ.M'N'P'Q'`, `EFG.E'F'G'`).
2. Negative guard: unprimed undotted notations (`MNPQRSTU`) and undotted pyramids (`SMNP`) do not trigger
   `hop_dong_to_po_da_khai`.
3. Cache invalidation (`140:route-d` -> `141:route-d`): a stale `140:route-d` `SimulationCache` row for an undotted
   prism MUST miss under `141:route-d`, recompute the 16-object / 4-witness `Scene3D`, and store under `141:route-d`.
"""
from __future__ import annotations

import json
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient

from app import main as M
from app.ai.adaptive_input_router import route_text_input
from app.ai.hybrid_offline import prepare_local_first_hybrid, resolve_hybrid_gemini_model
from app.main import SUPPORTED_VERSIONS
from app.persistence.db import SessionLocal, SimulationCache, init_db
from app.simulation.geometry_functions.engine import hop_dong_to_po_da_khai

UNDOTTED_QUAD_PRISM = (
    "Cho khối lăng trụ đứng MNPQM'N'P'Q' có đáy MNPQ là hình thoi, góc QMN = 60°, "
    "cạnh bên MM' = 2a và MP' hợp với đáy góc 30°. Tính thể tích khối lăng trụ đã cho."
)
DOTTED_QUAD_PRISM = UNDOTTED_QUAD_PRISM.replace("MNPQM'N'P'Q'", "MNPQ.M'N'P'Q'")

UNDOTTED_TRI_PRISM = (
    "Cho lăng trụ đứng EFGE'F'G' có đáy EFG là tam giác vuông tại E, "
    "EF = a, EG = a, cạnh bên EE' = 2a. Tính thể tích khối lăng trụ đã cho."
)
DOTTED_TRI_PRISM = UNDOTTED_TRI_PRISM.replace("EFGE'F'G'", "EFG.E'F'G'")


@pytest.mark.parametrize(
    ("undotted_text", "dotted_text", "expected_pw_count"),
    [
        (UNDOTTED_QUAD_PRISM, DOTTED_QUAD_PRISM, 4),
        (UNDOTTED_TRI_PRISM, DOTTED_TRI_PRISM, 3),
    ],
)
def test_undotted_primed_prism_matches_dotted_scene3d_and_witnesses(
    undotted_text: str,
    dotted_text: str,
    expected_pw_count: int,
) -> None:
    out_undot = route_text_input(undotted_text)
    out_dot = route_text_input(dotted_text)
    assert out_undot.response["route_d"]["status"] == "SERVED"
    assert out_dot.response["route_d"]["status"] == "SERVED"
    assert out_undot.response["route_d"]["answers"] == out_dot.response["route_d"]["answers"]

    sc_u = out_undot.response["envelope"]["scene3d"]
    sc_d = out_dot.response["envelope"]["scene3d"]
    assert sc_u["objects"] == sc_d["objects"]
    assert sc_u["events"] == sc_d["events"]

    pw_segs = [
        o for o in sc_u["objects"]
        if o.get("type") == "segment3"
        and isinstance(o.get("perpendicular_witness"), dict)
        and o["perpendicular_witness"].get("status") == "ENGINE_VERIFIED"
    ]
    assert len(pw_segs) == expected_pw_count
    assert any(str(o["id"]).startswith("day_") for o in sc_u["objects"])
    assert len([e for e in sc_u["events"] if e["action"] == "CREATE"]) >= 4


def test_hop_dong_to_po_da_khai_negative_guards() -> None:
    # Unprimed undotted prism stays None (no fabricated pairing)
    unprimed_prism = SimpleNamespace(
        id="c1",
        fn="prism",
        args=SimpleNamespace(base=["M", "N", "P", "Q"], top=["R", "S", "T", "U"], right=True),
        quotes=("Cho lăng trụ đứng MNPQRSTU.",),
    )
    assert hop_dong_to_po_da_khai((unprimed_prism,)) is None

    # Undotted pyramid also stays None (only dotted S.ABC names an apex)
    undotted_pyramid = SimpleNamespace(
        id="c2",
        fn="pyramid",
        args=SimpleNamespace(apex="S", base=["M", "N", "P"]),
        quotes=("Cho hình chóp SMNP.",),
    )
    assert hop_dong_to_po_da_khai((undotted_pyramid,)) is None


@pytest.fixture
def client(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("HYBRID_ROUTE_MODE", "local-first")
    monkeypatch.setenv("ALLOW_LIVE_AI", "0")
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    from tests.route_client import sign_in

    with TestClient(M.app) as c:
        sign_in(c)
        yield c


def test_stale_140_undotted_prism_row_misses_and_rebuilds_under_141(client: TestClient) -> None:
    assert M.CACHE_VERSION == "147"
    assert M.ROUTE_D_CACHE_POLICY == "147:route-d"

    r_fresh = client.post("/api/analyze", json={"input": {"type": "text", "content": UNDOTTED_QUAD_PRISM}})
    assert r_fresh.status_code == 200
    fresh_body = r_fresh.json()
    assert fresh_body["route_d"]["status"] == "SERVED"

    # Simulate a legacy 140:route-d row carrying the degraded 10-object scene with zero witnesses.
    poisoned = json.loads(json.dumps(fresh_body, ensure_ascii=False))
    poisoned["envelope"]["scene3d"]["objects"] = [
        o for o in poisoned["envelope"]["scene3d"]["objects"]
        if not str(o.get("id", "")).startswith(("day_", "canh_ben_"))
    ]
    assert len(poisoned["envelope"]["scene3d"]["objects"]) == 10

    key = prepare_local_first_hybrid(UNDOTTED_QUAD_PRISM, model=resolve_hybrid_gemini_model()).cache_key
    init_db()
    try:
        with SessionLocal() as s:
            s.query(SimulationCache).filter_by(key=key).delete()
            s.add(
                SimulationCache(
                    key=key,
                    problem_text=UNDOTTED_QUAD_PRISM,
                    simulation_id="generic.semantic_program",
                    envelope_json=json.dumps(poisoned, ensure_ascii=False),
                    dsl_version=next(iter(SUPPORTED_VERSIONS)),
                    policy_version="140:route-d",
                )
            )
            s.commit()

        r_after = client.post("/api/analyze", json={"input": {"type": "text", "content": UNDOTTED_QUAD_PRISM}})
        assert r_after.status_code == 200
        body_after = r_after.json()
        pw_ids = [o["id"] for o in body_after["envelope"]["scene3d"]["objects"] if o.get("perpendicular_witness")]
        assert len(pw_ids) == 4
        assert len(body_after["envelope"]["scene3d"]["objects"]) == 16

        with SessionLocal() as s:
            row = s.query(SimulationCache).filter_by(key=key, policy_version=M.ROUTE_D_CACHE_POLICY).first()
            assert row is not None
    finally:
        with SessionLocal() as s:
            s.query(SimulationCache).filter_by(key=key).delete()
            s.commit()
