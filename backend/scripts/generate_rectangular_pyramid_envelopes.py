# -*- coding: utf-8 -*-
"""Tạo envelope chuẩn tắc cho Rectangular & Square Pyramid từ Python pipeline."""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "backend"))

from app.ai import pipeline
from app.simulation.geometry_compiler import contract_adapter as A, compiler as C
from app.simulation.semantic_program.route import verify_and_compile
from app.simulation.semantic_program.validator import validate_semantic_program
from tests.geometry.test_rectangular_pyramid_compiler import _build_rect_pyramid_contract


def generate_envelope(shape: str, len_ab: str, len_ad: str | None, len_sa: str) -> dict:
    contract = _build_rect_pyramid_contract(
        apex="S",
        base_cycle=("A", "B", "C", "D"),
        base_shape=shape,
        len_ab=len_ab,
        len_ad=len_ad,
        len_sa=len_sa,
    )
    ka = A.build_fact_graph(contract)
    assert ka.status == "VALID" and ka.graph is not None, f"Fact graph failed: {ka.diagnostics}"
    bd = C.bien_dich(ka.graph)
    assert bd.status == "COMPILED" and bd.program is not None, "Compile failed"
    val = validate_semantic_program(bd.program)
    assert val.ok and val.spec is not None, f"Validation failed: {val.error}"
    outcome = verify_and_compile(contract, val.spec)
    assert outcome.stage_reached == "served", f"Verify failed: {outcome.error_code}"
    outcome.scene3d = pipeline._dung_scene3d(val.spec, contract)
    env = pipeline._envelope_tu_route_sinh(outcome, {}, {}, None)
    return env


def main():
    rect_env = generate_envelope("rectangle", "3", "4", "6")
    square_env = generate_envelope("square", "3", None, "6")

    out_dirs = [
        ROOT / "docs" / "evaluation" / "geometry" / "rectangular-pyramid-visual-integrity",
        ROOT / "docs" / "evaluation" / "geometry" / "rectangular-pyramid-replay",
    ]

    for d in out_dirs:
        d.mkdir(parents=True, exist_ok=True)
        rect_path = d / "rect_pyramid_envelope.json"
        square_path = d / "square_pyramid_envelope.json"
        rect_path.write_text(json.dumps(rect_env, indent=2, ensure_ascii=False), encoding="utf-8")
        square_path.write_text(json.dumps(square_env, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"Wrote {rect_path} (objects: {len(rect_env['scene3d']['objects'])})")
        print(f"Wrote {square_path} (objects: {len(square_env['scene3d']['objects'])})")


if __name__ == "__main__":
    main()
