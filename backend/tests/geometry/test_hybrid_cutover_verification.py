# -*- coding: utf-8 -*-
"""Final Hybrid Architecture Cutover verification suite (`§II`–`§VI`).

Verifies with 0 live Gemini HTTP calls:
1. Real `POST /api/analyze` production call graph executes `TypedFactNext /2` ->
   `Source Gate` -> `FactGraph` -> `Planner /26` -> `Registry /33` -> `Engine /24`
   (`IR` + `Exact Geometry Kernel`) -> `Adapter /4`.
2. Legacy `LLM_ONLY` (`app.ai.pipeline`), Compiler C (`app.simulation.geometry_compiler`),
   Adapter `/3` (`app.ai.adapter3_simulation`), and the 10 legacy `.md` prompts are
   physically absent and never imported.
3. All 11 `POST /api/analyze` scenarios (`§V.B`) + `HYBRID_ROUTE_MODE=off` fail-closed
   behavior + two-way cache isolation (`131` <-> `132`, `staging-replay` <-> `live`).
4. `Scene3D` envelope + cumulative construction continuity fields (`created_ids`,
   `reused_ids`, `highlighted_ids`, `retired_ids`, `step_summary`, `verification_refs`,
   `coordinate_frame_id`).
"""
from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path
import sys
from typing import Any

from fastapi.testclient import TestClient
import httpx
import pytest

from app import main as M
from app.ai import (
    adapter4_route as A4,
    function_calling as FC,
    function_route as FR,
    hybrid_offline as HO,
    typed_fact_next_extraction as TFE,
)
SimulationCache = M.SimulationCache
from app.simulation.geometry_functions import (
    construction_continuity as CC,
    engine as ENG,
    planner as PLN,
    typed_fact_next_bridge as BRG,
)
from app.ai.hybrid_preview import _validate_scene
from app.simulation.semantic_program.interpreter import SemanticProgramInterpreter
from app.simulation.semantic_program.transport import check_envelope_transport

ROOT = Path(__file__).resolve().parents[3]
APP_DIR = ROOT / "backend" / "app"


def _gemini_wire_body(canonical_payload: dict[str, Any]) -> dict[str, Any]:
    wire = TFE.to_wire_typed_fact_next_v2(canonical_payload)
    return {
        "candidates": [
            {
                "content": {"parts": [{"text": json.dumps(wire, ensure_ascii=False)}]},
                "finishReason": "STOP",
            }
        ],
        "usageMetadata": {"promptTokenCount": 120, "candidatesTokenCount": 80, "totalTokenCount": 200},
    }


def _cuboid_payload(
    *,
    problem_text: str | None = None,
    premises_override: list[dict[str, Any]] | None = None,
    math_goals_override: list[dict[str, Any]] | None = None,
    sim_quote: str | None = None,
) -> dict[str, Any]:
    text = problem_text or (
        "Cho hình hộp chữ nhật ABCD.A'B'C'D' có AB = 2, AD = 3 và AA' = 4. "
        "Tính thể tích khối hộp chữ nhật ABCD.A'B'C'D'."
    )
    solid_quote = "Cho hình hộp chữ nhật ABCD.A'B'C'D'"
    premises = premises_override if premises_override is not None else [
        {"kind": "right_prism", "args": {"base": list("ABCD"), "top": ["A'", "B'", "C'", "D'"]}, "quote": solid_quote, "solid_id": "s1"},
        {"kind": "rectangle", "args": {"vertices": list("ABCD")}, "quote": solid_quote, "solid_id": "s1"},
        {"kind": "segment_length", "args": {"segment": ["A", "B"], "value": "2"}, "quote": "AB = 2", "solid_id": "s1"},
        {"kind": "segment_length", "args": {"segment": ["A", "D"], "value": "3"}, "quote": "AD = 3", "solid_id": "s1"},
        {"kind": "segment_length", "args": {"segment": ["A", "A'"], "value": "4"}, "quote": "AA' = 4", "solid_id": "s1"},
    ]
    math_goals = math_goals_override if math_goals_override is not None else [
        {
            "goal_id": "mg1",
            "kind": "measurement",
            "goal_type": "volume",
            "solid_id": "s1",
            "target": {"solid_id": "s1"},
            "quote": "Tính thể tích khối hộp chữ nhật ABCD.A'B'C'D'.",
        }
    ]
    return {
        "schema_version": "typed-fact-next/2",
        "problem_text": text,
        "length_unit": "1",
        "solids": [
            {
                "solid_id": "s1",
                "solid_type": "prism",
                "notation": "ABCD.A'B'C'D'",
                "quote": solid_quote,
            }
        ],
        "premises": premises,
        "relations": [],
        "derived_sections": [],
        "simulation_goals": [
            {
                "goal_id": "sg1",
                "kind": "construct_object",
                "target_solid_id": "s1",
                "quote": sim_quote or solid_quote,
            }
        ],
        "math_goals": math_goals,
    }


def _install_transport_map(monkeypatch: pytest.MonkeyPatch, by_text: dict[str, dict[str, Any]], calls: list[str]) -> None:
    def _fake_live_transport(api_key: str, *, model: str | None = None, timeout_seconds: float = 60.0, **_kw):
        assert api_key, "live_transport must never be called without an API key"

        def _send_once(request: dict[str, Any], **_send_kw) -> dict[str, Any]:
            user_text = request["contents"][0]["parts"][0]["text"]
            for prob, payload in by_text.items():
                if prob in user_text:
                    calls.append(prob)
                    return _gemini_wire_body(payload)
            raise AssertionError(f"Unexpected problem in offline transport stub: {user_text!r}")

        return _send_once

    monkeypatch.setattr(FC, "live_transport", _fake_live_transport)


def test_default_analyze_route_call_graph_and_retired_legacy_absence(monkeypatch: pytest.MonkeyPatch):
    """`POST /api/analyze` defaults to Hybrid `/4`, traverses every Hybrid stage, and preserves Scene3D + continuity."""
    monkeypatch.delenv("HYBRID_ROUTE_MODE", raising=False)
    monkeypatch.delenv("ALLOW_LIVE_AI", raising=False)
    monkeypatch.setenv("GEMINI_API_KEY", "unit-test-offline-stub-key")

    assert M.CACHE_VERSION == "132"
    assert M.ROUTE_D_CACHE_POLICY == "132:route-d"
    assert M.hybrid_route_mode() == "live"

    # Physical retirement & module-closure checks
    assert not (APP_DIR / "ai" / "pipeline.py").exists()
    assert not (APP_DIR / "ai" / "adapter3_simulation.py").exists()
    assert not (APP_DIR / "simulation" / "geometry_compiler").exists()
    skills_files = {p.name for p in (APP_DIR / "ai" / "skills").glob("*.md")}
    assert skills_files == {"transcribe.md"}
    for retired_mod in ("app.ai.pipeline", "app.ai.adapter3_simulation", "app.simulation.geometry_compiler"):
        assert retired_mod not in sys.modules

    # Spy on real Hybrid pipeline stages
    stage_order: list[str] = []

    def _wrap(module: Any, attr: str, label: str) -> None:
        orig = getattr(module, attr)

        def _spy(*args, **kwargs):
            stage_order.append(label)
            return orig(*args, **kwargs)

        monkeypatch.setattr(module, attr, _spy)

    _wrap(HO, "extract_typed_fact_next_v2", "extract_typed_fact_next_v2")
    _wrap(HO, "run_typed_fact_next_v2_route", "run_typed_fact_next_v2_route")
    _wrap(BRG, "bridge_v2", "bridge_v2")
    _wrap(PLN, "lap_ke_hoach", "lap_ke_hoach")
    _wrap(FR, "dung_tu_loi_goi", "dung_tu_loi_goi")
    _wrap(ENG, "kiem_nguon", "kiem_nguon")
    _wrap(SemanticProgramInterpreter, "execute", "ir_exact_kernel_execute")
    _wrap(HO, "build_adapter4_response", "build_adapter4_response")

    # Use a unique length so DB cache is guaranteed cold
    text = (
        "Cho hình hộp chữ nhật ABCD.A'B'C'D' có AB = 5, AD = 6 và AA' = 7. "
        "Tính thể tích khối hộp chữ nhật ABCD.A'B'C'D'."
    )
    payload = _cuboid_payload(
        problem_text=text,
        premises_override=[
            {"kind": "right_prism", "args": {"base": list("ABCD"), "top": ["A'", "B'", "C'", "D'"]}, "quote": "Cho hình hộp chữ nhật ABCD.A'B'C'D'", "solid_id": "s1"},
            {"kind": "rectangle", "args": {"vertices": list("ABCD")}, "quote": "Cho hình hộp chữ nhật ABCD.A'B'C'D'", "solid_id": "s1"},
            {"kind": "segment_length", "args": {"segment": ["A", "B"], "value": "5"}, "quote": "AB = 5", "solid_id": "s1"},
            {"kind": "segment_length", "args": {"segment": ["A", "D"], "value": "6"}, "quote": "AD = 6", "solid_id": "s1"},
            {"kind": "segment_length", "args": {"segment": ["A", "A'"], "value": "7"}, "quote": "AA' = 7", "solid_id": "s1"},
        ],
    )
    transport_calls: list[str] = []
    _install_transport_map(monkeypatch, {text: payload}, transport_calls)

    with TestClient(M.app) as client:
        resp = client.post("/api/analyze", json={"input": {"type": "text", "content": text}})

    assert resp.status_code == 200
    assert len(transport_calls) == 1
    first_seen_stages = list(dict.fromkeys(stage_order))
    assert first_seen_stages == [
        "extract_typed_fact_next_v2",
        "run_typed_fact_next_v2_route",
        "bridge_v2",
        "lap_ke_hoach",
        "dung_tu_loi_goi",
        "kiem_nguon",
        "ir_exact_kernel_execute",
        "build_adapter4_response",
    ]
    for retired_mod in ("app.ai.pipeline", "app.ai.adapter3_simulation", "app.simulation.geometry_compiler"):
        assert retired_mod not in sys.modules

    body = resp.json()
    assert body["route_d"]["status"] == "SERVED"
    assert body["route_d"]["adapter_version"] == "hybrid-simulation-adapter/4"
    assert body["route_d"]["schema_version"] == "hybrid-route-d-simulation/4"
    assert body["route_d"]["extraction_mode"] == "LIVE_GEMINI_STRUCTURED"
    env = body["envelope"]
    assert env["status"] == "ok"
    assert "210" in json.dumps(body["route_d"], ensure_ascii=False)
    _validate_scene(env["scene3d"])
    assert check_envelope_transport(env) is None
    assert CC.validate_construction_continuity(env["scene3d"]) == []

    steps = env["scene3d"]["formation"]["steps"]
    assert len(steps) >= 2
    for st in steps:
        for field in (
            "created_ids",
            "reused_ids",
            "highlighted_ids",
            "retired_ids",
            "step_summary",
            "verification_refs",
            "coordinate_frame_id",
        ):
            assert field in st, f"Missing continuity field {field} on step {st.get('id')}"
        assert set(st["step_summary"]) >= {"what", "inputs", "validity", "result", "next_use"}


def test_api_analyze_11_scenarios_cache_isolation_and_fail_closed_modes(monkeypatch: pytest.MonkeyPatch, tmp_path: Path):
    """Covers all 11 `POST /api/analyze` scenarios (`§V.B`), two-way cache isolation, and `off` rejection (`§VI`)."""
    from tests.geometry.test_final_backend_product_completion import _c26_row

    monkeypatch.delenv("ALLOW_LIVE_AI", raising=False)
    monkeypatch.delenv("HYBRID_ROUTE_MODE", raising=False)
    monkeypatch.setenv("GEMINI_API_KEY", "unit-test-offline-stub-key")

    # 1. Valid constrained-section pyramid (`K-A01`)
    pyr_case, pyr_row = _c26_row("k1-live.jsonl", "K-A01")
    valid_pyr_text = pyr_case["problem_text"]
    valid_pyr_payload = pyr_row["raw_extraction"]

    # 2. Missing dimension (cuboid without AA')
    missing_text = (
        "Cho hình hộp chữ nhật ABCD.A'B'C'D' có AB = 2 và AD = 3. "
        "Tính thể tích khối hộp chữ nhật ABCD.A'B'C'D'."
    )
    missing_payload = _cuboid_payload(
        problem_text=missing_text,
        premises_override=[
            {"kind": "right_prism", "args": {"base": list("ABCD"), "top": ["A'", "B'", "C'", "D'"]}, "quote": "Cho hình hộp chữ nhật ABCD.A'B'C'D'", "solid_id": "s1"},
            {"kind": "rectangle", "args": {"vertices": list("ABCD")}, "quote": "Cho hình hộp chữ nhật ABCD.A'B'C'D'", "solid_id": "s1"},
            {"kind": "segment_length", "args": {"segment": ["A", "B"], "value": "2"}, "quote": "AB = 2", "solid_id": "s1"},
            {"kind": "segment_length", "args": {"segment": ["A", "D"], "value": "3"}, "quote": "AD = 3", "solid_id": "s1"},
        ],
    )

    # 3. Contradictory facts (AB = 2 and AB = 9 on same segment)
    contradict_text = (
        "Cho hình hộp chữ nhật ABCD.A'B'C'D' có AB = 2, AB = 9, AD = 3 và AA' = 4. "
        "Tính thể tích khối hộp chữ nhật ABCD.A'B'C'D'."
    )
    contradict_payload = _cuboid_payload(
        problem_text=contradict_text,
        premises_override=[
            {"kind": "right_prism", "args": {"base": list("ABCD"), "top": ["A'", "B'", "C'", "D'"]}, "quote": "Cho hình hộp chữ nhật ABCD.A'B'C'D'", "solid_id": "s1"},
            {"kind": "rectangle", "args": {"vertices": list("ABCD")}, "quote": "Cho hình hộp chữ nhật ABCD.A'B'C'D'", "solid_id": "s1"},
            {"kind": "segment_length", "args": {"segment": ["A", "B"], "value": "2"}, "quote": "AB = 2", "solid_id": "s1"},
            {"kind": "segment_length", "args": {"segment": ["A", "B"], "value": "9"}, "quote": "AB = 9", "solid_id": "s1"},
            {"kind": "segment_length", "args": {"segment": ["A", "D"], "value": "3"}, "quote": "AD = 3", "solid_id": "s1"},
            {"kind": "segment_length", "args": {"segment": ["A", "A'"], "value": "4"}, "quote": "AA' = 4", "solid_id": "s1"},
        ],
    )

    # 4. Out-of-scope non-geometry text
    oos_text = "Giải phương trình bậc hai x^2 - 5x + 6 = 0 trên tập số thực."

    # 5. Pure simulation goal (0 math_goals, SL-1 student simulation request)
    sim_only_text = (
        "Hãy mô phỏng hình chóp S.ABCD có đáy ABCD là hình vuông cạnh 2, "
        "SA vuông góc với mặt phẳng (ABCD) và SA = 2."
    )
    sim_only_payload = {
        "schema_version": "typed-fact-next/2",
        "problem_text": sim_only_text,
        "length_unit": "1",
        "solids": [{"solid_id": "s1", "solid_type": "pyramid", "notation": "S.ABCD", "quote": "hình chóp S.ABCD"}],
        "premises": [
            {"kind": "regular_polygon", "args": {"vertices": list("ABCD"), "side": "2"}, "quote": "đáy ABCD là hình vuông cạnh 2", "solid_id": "s1"},
            {"kind": "perpendicular_line_plane", "args": {"line": ["S", "A"], "plane": list("ABCD")}, "quote": "SA vuông góc với mặt phẳng (ABCD)", "solid_id": "s1"},
            {"kind": "segment_length", "args": {"segment": ["S", "A"], "value": "2"}, "quote": "SA = 2", "solid_id": "s1"},
        ],
        "relations": [],
        "derived_sections": [],
        "simulation_goals": [{"goal_id": "sg1", "kind": "construct_object", "target_solid_id": "s1", "quote": "Hãy mô phỏng hình chóp S.ABCD"}],
        "math_goals": [],
    }

    # 6. Calculation goal (volume = 24)
    calc_text = (
        "Cho hình hộp chữ nhật ABCD.A'B'C'D' có AB = 2, AD = 3 và AA' = 4. "
        "Tính thể tích khối hộp chữ nhật ABCD.A'B'C'D'."
    )
    calc_payload = _cuboid_payload(problem_text=calc_text)

    # 7. Multi-goal (both volume of cuboid AND space-diagonal length AC')
    multi_text = (
        "Cho hình hộp chữ nhật ABCD.A'B'C'D' có AB = 2, AD = 3 và AA' = 6. "
        "Tính thể tích khối hộp chữ nhật ABCD.A'B'C'D' và tính độ dài đoạn thẳng AC'."
    )
    multi_payload = _cuboid_payload(
        problem_text=multi_text,
        premises_override=[
            {"kind": "right_prism", "args": {"base": list("ABCD"), "top": ["A'", "B'", "C'", "D'"]}, "quote": "Cho hình hộp chữ nhật ABCD.A'B'C'D'", "solid_id": "s1"},
            {"kind": "rectangle", "args": {"vertices": list("ABCD")}, "quote": "Cho hình hộp chữ nhật ABCD.A'B'C'D'", "solid_id": "s1"},
            {"kind": "segment_length", "args": {"segment": ["A", "B"], "value": "2"}, "quote": "AB = 2", "solid_id": "s1"},
            {"kind": "segment_length", "args": {"segment": ["A", "D"], "value": "3"}, "quote": "AD = 3", "solid_id": "s1"},
            {"kind": "segment_length", "args": {"segment": ["A", "A'"], "value": "6"}, "quote": "AA' = 6", "solid_id": "s1"},
        ],
        math_goals_override=[
            {
                "goal_id": "mg_vol",
                "kind": "measurement",
                "goal_type": "volume",
                "solid_id": "s1",
                "target": {"solid_id": "s1"},
                "quote": "Tính thể tích khối hộp chữ nhật ABCD.A'B'C'D'",
            },
            {
                "goal_id": "mg_diag",
                "kind": "measurement",
                "goal_type": "distance",
                "solid_id": "s1",
                "target": {"segment": ["A", "C'"]},
                "quote": "tính độ dài đoạn thẳng AC'.",
            },
        ],
    )

    transport_calls: list[str] = []
    _install_transport_map(
        monkeypatch,
        {
            valid_pyr_text: valid_pyr_payload,
            missing_text: missing_payload,
            contradict_text: contradict_payload,
            sim_only_text: sim_only_payload,
            calc_text: calc_payload,
            multi_text: multi_payload,
        },
        transport_calls,
    )

    with TestClient(M.app) as client:
        # (1) Valid geometry
        r1 = client.post("/api/analyze", json={"input": {"type": "text", "content": valid_pyr_text}})
        assert r1.status_code == 200 and r1.json()["route_d"]["status"] == "SERVED"
        _validate_scene(r1.json()["envelope"]["scene3d"])

        # (2) Missing fact -> REFUSED, no scene3d
        r2 = client.post("/api/analyze", json={"input": {"type": "text", "content": missing_text}})
        assert r2.status_code == 200
        assert r2.json()["route_d"]["status"] == "REFUSED"
        assert "scene3d" not in r2.json()["envelope"]

        # (3) Contradictory facts -> REFUSED, no scene3d
        r3 = client.post("/api/analyze", json={"input": {"type": "text", "content": contradict_text}})
        assert r3.status_code == 200
        assert r3.json()["route_d"]["status"] == "REFUSED"
        assert "scene3d" not in r3.json()["envelope"]

        # (4) Out-of-scope -> unsupported out_of_scope, 0 new transport calls
        before_oos = len(transport_calls)
        r4 = client.post("/api/analyze", json={"input": {"type": "text", "content": oos_text}})
        assert r4.status_code == 200
        assert r4.json()["status"] == "unsupported"
        assert r4.json()["failure_category"] == "out_of_scope"
        assert "scene3d" not in r4.json()
        assert len(transport_calls) == before_oos

        # (5) Simulation-only goal -> SERVED with Scene3D
        r5 = client.post("/api/analyze", json={"input": {"type": "text", "content": sim_only_text}})
        assert r5.status_code == 200 and r5.json()["route_d"]["status"] == "SERVED"
        assert len(r5.json()["envelope"]["scene3d"]["formation"]["steps"]) >= 1

        # (6) Calculation goal + (10) Cache miss -> hit + two-way cache isolation
        live_plan = HO.prepare_live_hybrid(calc_text, model=HO.resolve_hybrid_gemini_model())
        # Seed a legacy 131:route-d entry under the SAME key idea (different key in DB, or even forced same cache_key with old policy_version)
        poison_resp = {"route_d": {"status": "SERVED", "poisoned": True}, "envelope": {"status": "ok"}}
        with M.SessionLocal() as session:
            session.query(SimulationCache).filter_by(key=live_plan.cache_key).delete()
            session.query(SimulationCache).filter_by(key=f"legacy131:{live_plan.cache_key[:40]}").delete()
            session.add(
                SimulationCache(
                    key=f"legacy131:{live_plan.cache_key[:40]}",
                    problem_text=calc_text,
                    simulation_id="sim_legacy_131",
                    envelope_json=json.dumps(poison_resp),
                    dsl_version=M.DSL_VERSION,
                    policy_version="131:route-d",
                )
            )
            session.commit()

        before_calc = len(transport_calls)
        r6_miss = client.post("/api/analyze", json={"input": {"type": "text", "content": calc_text}})
        assert r6_miss.status_code == 200 and r6_miss.headers.get("X-Algosim-Cache") == "miss"
        assert r6_miss.json()["route_d"]["status"] == "SERVED"
        assert "poisoned" not in r6_miss.json()["route_d"]
        assert "24" in json.dumps(r6_miss.json()["route_d"], ensure_ascii=False)
        assert len(transport_calls) == before_calc + 1

        r6_hit = client.post("/api/analyze", json={"input": {"type": "text", "content": calc_text}})
        assert r6_hit.status_code == 200 and r6_hit.headers.get("X-Algosim-Cache") == "hit"
        assert len(transport_calls) == before_calc + 1

        # Verify policy_version mismatch on identical cache_key ALSO fails lookup cleanly (two-way 131 <-> 132 guard)
        with M.SessionLocal() as session:
            assert M._cache_lookup(session, live_plan.cache_key, "131:route-d") is None
            assert M._cache_lookup(session, live_plan.cache_key, "131") is None
            assert M._cache_lookup(session, live_plan.cache_key, M.ROUTE_D_CACHE_POLICY) is not None

        # (7) Multi-goal (volume = 36 AND diagonal AC' = 7)
        r7 = client.post("/api/analyze", json={"input": {"type": "text", "content": multi_text}})
        assert r7.status_code == 200 and r7.json()["route_d"]["status"] == "SERVED"
        answers_str = json.dumps(r7.json()["route_d"], ensure_ascii=False)
        assert "36" in answers_str and "7" in answers_str

        # (11) Staging replay + two-way isolation vs live cache
        corpus_file = tmp_path / "staging_replay.json"
        corpus_file.write_text(
            json.dumps({"schema": HO.LOCAL_REPLAY_SCHEMA, "outputs": {calc_text: calc_payload}}, ensure_ascii=False),
            encoding="utf-8",
        )
        monkeypatch.setenv("HYBRID_ROUTE_MODE", "staging-replay")
        monkeypatch.setenv("HYBRID_REPLAY_CORPUS", str(corpus_file))
        replay_plan = HO.prepare_staging_replay(calc_text, str(corpus_file))
        assert replay_plan is not None and replay_plan.cache_key != live_plan.cache_key
        with M.SessionLocal() as session:
            session.query(SimulationCache).filter_by(key=replay_plan.cache_key).delete()
            session.commit()

        before_replay = len(transport_calls)
        r11_ok = client.post("/api/analyze", json={"input": {"type": "text", "content": calc_text}})
        assert r11_ok.status_code == 200
        assert r11_ok.headers.get("X-Algosim-Cache") == "miss"  # Did NOT hit live cache!
        assert r11_ok.json()["route_d"]["status"] == "SERVED"
        assert r11_ok.json()["route_d"].get("extraction_mode") != "LIVE_GEMINI_STRUCTURED"
        assert len(transport_calls) == before_replay

        r11_unrecorded = client.post(
            "/api/analyze",
            json={"input": {"type": "text", "content": "Cho hình chóp S.ABC có SA = 1. Tính thể tích S.ABC."}},
        )
        assert r11_unrecorded.status_code == 200
        assert r11_unrecorded.json()["route_d"]["status"] == "REFUSED"
        assert r11_unrecorded.json()["route_d"]["refusal"]["code"] == "NO_RECORDED_EXTRACTION"

        monkeypatch.setenv("HYBRID_REPLAY_CORPUS", str(tmp_path / "does_not_exist.json"))
        r11_nocorpus = client.post("/api/analyze", json={"input": {"type": "text", "content": calc_text}})
        assert r11_nocorpus.status_code == 503
        assert r11_nocorpus.json()["reason_code"] == "STAGING_CORPUS_UNAVAILABLE"

        # (9) Missing API key in live mode -> 503 MISSING_API_KEY, no fallback
        monkeypatch.setenv("HYBRID_ROUTE_MODE", "live")
        monkeypatch.setenv("GEMINI_API_KEY", "")
        unrecorded_live_text = "Cho hình chóp S.ABC có SA = 11, AB = 12, AC = 13. Tính thể tích S.ABC."
        r9 = client.post("/api/analyze", json={"input": {"type": "text", "content": unrecorded_live_text}})
        assert r9.status_code == 503
        assert r9.json()["reason_code"] == "MISSING_API_KEY"

        # (8) Provider error (502) & timeout (504) in live mode -> technical error, no fallback, not cached
        monkeypatch.setenv("GEMINI_API_KEY", "unit-test-offline-stub-key")

        def _failing_transport(*_a, **_kw):
            def _boom(_req, **_skw):
                raise FC.ProviderHTTPError(500, "upstream error")

            return _boom

        monkeypatch.setattr(FC, "live_transport", _failing_transport)
        r8_err = client.post("/api/analyze", json={"input": {"type": "text", "content": unrecorded_live_text}})
        assert r8_err.status_code == 502
        assert r8_err.json()["reason_code"] == "PROVIDER_ERROR"

        def _timeout_transport(*_a, **_kw):
            def _slow(_req, **_skw):
                raise httpx.ReadTimeout("timed out")

            return _slow

        monkeypatch.setenv("HYBRID_LIVE_TIMEOUT_SECONDS", "0.05")
        monkeypatch.setenv("HYBRID_LIVE_DEADLINE_SECONDS", "0.08")
        monkeypatch.setattr(FC, "live_transport", _timeout_transport)
        r8_to = client.post("/api/analyze", json={"input": {"type": "text", "content": unrecorded_live_text}})
        assert r8_to.status_code == 504
        assert r8_to.json()["reason_code"] == "HYBRID_DEADLINE_EXCEEDED"

        # Invalid / legacy `off` mode -> 503 INVALID_HYBRID_ROUTE_MODE (never rolls back to LLM_ONLY)
        monkeypatch.setenv("HYBRID_ROUTE_MODE", "off")
        r_off = client.post("/api/analyze", json={"input": {"type": "text", "content": calc_text}})
        assert r_off.status_code == 503
        assert r_off.json()["reason_code"] == "INVALID_HYBRID_ROUTE_MODE"
