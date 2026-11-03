# -*- coding: utf-8 -*-
"""0-LLM deterministic Scene3D test helper for shared `SemanticProgramSpec` / kernel / Scene3D tests.

Giữ hướng phụ thuộc một chiều (`app/simulation` không import `scene3d` trực tiếp ngoài `scene3d.py`)
sau khi orchestrator `LLM_ONLY` (`app/ai/pipeline.py`) đã được gỡ bỏ ở cutover Hybrid `/4`.
"""
from __future__ import annotations


def _dung_scene3d(spec, contract=None) -> dict | None:
    from app.simulation.geometry import metric as _metric
    from app.simulation.semantic_program.assumption_gate import do_luong_cua
    from app.simulation.semantic_program.formation import hoan_thien_dung_hinh
    from app.simulation.semantic_program.interpreter import SemanticProgramInterpreter
    from app.simulation.semantic_program.scene3d import build_scene3d
    from app.simulation.semantic_program.section_provenance import normalize_section_provenance
    from app.simulation.semantic_program.simulation_state import build_simulation_state

    try:
        spec = hoan_thien_dung_hinh(spec, contract).spec
        do_luong = do_luong_cua(getattr(contract, "problem_text", "") or "", spec)
        with _metric.using(do_luong):
            ket = SemanticProgramInterpreter().execute(spec)
            canh = build_scene3d(build_simulation_state(spec, ket, contract))
        if do_luong is not None:
            canh = {**canh, "chart_metric": do_luong.as_json()}
        canh = normalize_section_provenance(canh, ket.final_memory, contract).scene
    except Exception:  # noqa: BLE001
        return None
    return canh if canh["objects"] else None


def _envelope_tu_route_sinh(outcome, analysis: dict, plan: dict, observer=None) -> dict:
    env = dict(outcome.envelope or {})
    env["analysis"] = analysis
    env["representation_plan"] = plan
    env["source"] = "semantic_program"
    if outcome.scene3d:
        env["scene3d"] = outcome.scene3d
        env["domain"] = "geometry"
    if observer is not None:
        observer.emit(
            "envelope",
            {
                "status": "ok",
                "simulation_id": env.get("simulation_id"),
                "source": "semantic_program",
            },
        )
    return env
