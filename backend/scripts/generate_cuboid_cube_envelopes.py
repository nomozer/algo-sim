# -*- coding: utf-8 -*-
"""Tạo envelope chuẩn tắc cho Cuboid, Cube và Right Square Prism từ Python production pipeline."""
import asyncio
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "backend"))

from app.ai import pipeline as PL
from app.simulation.semantic_program.analyze_contract import build_request_contract
from tests.geometry.test_cuboid_cube_production_route import (
    _cuboid_p01_payload,
    _cube_p01_payload,
    _square_prism_control_payload,
)


def generate_envelope_for_case(payload_fn):
    text, payload = payload_fn()
    contract = build_request_contract(payload, problem_text=text, domain="hinh_hoc")

    async def run():
        saved_analyze = PL.stage_semantic_analyze
        saved_gemini = PL.call_gemini
        saved_mode = os.environ.get("GEOMETRY_COMPILER_MODE")
        try:
            os.environ["GEOMETRY_COMPILER_MODE"] = "DETERMINISTIC_FIRST"

            async def mock_analyze(*args, **kwargs):
                return contract, None

            async def no_gemini(*args, **kwargs):
                raise AssertionError("Gemini was called!")

            PL.stage_semantic_analyze = mock_analyze
            PL.call_gemini = no_gemini
            return await PL.run_pipeline(text, "fake_key")
        finally:
            PL.stage_semantic_analyze = saved_analyze
            PL.call_gemini = saved_gemini
            if saved_mode is not None:
                os.environ["GEOMETRY_COMPILER_MODE"] = saved_mode
            else:
                os.environ.pop("GEOMETRY_COMPILER_MODE", None)

    env = asyncio.run(run())
    assert env.get("status") == "ok", f"Envelope generation failed: {env}"
    assert env.get("scene3d") is not None, "Missing scene3d in envelope"
    return env


def main():
    cuboid_env = generate_envelope_for_case(_cuboid_p01_payload)
    cube_env = generate_envelope_for_case(_cube_p01_payload)
    square_prism_env = generate_envelope_for_case(_square_prism_control_payload)

    out_dir = ROOT / "docs" / "evaluation" / "geometry" / "cuboid-cube-visual-integrity"
    out_dir.mkdir(parents=True, exist_ok=True)

    cuboid_path = out_dir / "cuboid_envelope.json"
    cube_path = out_dir / "cube_envelope.json"
    square_prism_path = out_dir / "square_prism_envelope.json"

    cuboid_path.write_text(json.dumps(cuboid_env, indent=2, ensure_ascii=False), encoding="utf-8")
    cube_path.write_text(json.dumps(cube_env, indent=2, ensure_ascii=False), encoding="utf-8")
    square_prism_path.write_text(json.dumps(square_prism_env, indent=2, ensure_ascii=False), encoding="utf-8")

    print(f"Wrote {cuboid_path} (objects: {len(cuboid_env['scene3d']['objects'])})")
    print(f"Wrote {cube_path} (objects: {len(cube_env['scene3d']['objects'])})")
    print(f"Wrote {square_prism_path} (objects: {len(square_prism_env['scene3d']['objects'])})")


if __name__ == "__main__":
    main()
