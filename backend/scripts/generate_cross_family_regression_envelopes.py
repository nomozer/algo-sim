# -*- coding: utf-8 -*-
"""Sinh envelope production-route cho browser audit chéo các họ đa diện."""
from __future__ import annotations

import asyncio
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "backend"))

from app.ai import pipeline as PL
from tests.geometry.test_prism_production_route import (
    _prism_p01_contract,
    _pyramid_control_contract,
)
from tests.geometry.test_rectangular_pyramid_production_route import (
    _rect_pyramid_contract,
)


def _generate(contract_factory):
    text, contract = contract_factory()

    async def run():
        saved_analyze = PL.stage_semantic_analyze
        saved_gemini = PL.call_gemini
        saved_mode = os.environ.get("GEOMETRY_COMPILER_MODE")
        try:
            os.environ["GEOMETRY_COMPILER_MODE"] = "DETERMINISTIC_FIRST"

            async def mock_analyze(*args, **kwargs):
                return contract, None

            async def no_gemini(*args, **kwargs):
                raise AssertionError("Cross-family evidence attempted a live model call")

            PL.stage_semantic_analyze = mock_analyze
            PL.call_gemini = no_gemini
            return await PL.run_pipeline(text, "offline_evidence_key")
        finally:
            PL.stage_semantic_analyze = saved_analyze
            PL.call_gemini = saved_gemini
            if saved_mode is None:
                os.environ.pop("GEOMETRY_COMPILER_MODE", None)
            else:
                os.environ["GEOMETRY_COMPILER_MODE"] = saved_mode

    envelope = asyncio.run(run())
    assert envelope.get("status") == "ok", envelope
    return text, envelope


def main() -> None:
    out = Path(os.environ.get(
        "CROSS_FAMILY_EVIDENCE_DIR",
        ROOT / "docs" / "evaluation" / "geometry" / "cross-family-regression-20260927",
    )).resolve()
    out.mkdir(parents=True, exist_ok=True)
    cases = (
        ("triangular_pyramid", _pyramid_control_contract, ["S", "A", "B", "C"], "10"),
        ("triangular_prism", _prism_p01_contract, ["A", "B", "C", "D", "E", "F"], "30"),
        ("rectangular_pyramid", _rect_pyramid_contract, ["S", "A", "B", "C", "D"], "24"),
    )
    for name, factory, labels, answer in cases:
        text, envelope = _generate(factory)
        (out / f"{name}_envelope.json").write_text(
            json.dumps({"envelope": envelope}, ensure_ascii=False, indent=2), encoding="utf-8",
        )
        (out / f"{name}_case.json").write_text(
            json.dumps({"input_text": text, "labels": labels, "volume": answer},
                       ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        print(f"Wrote {name}: {len(envelope['scene3d']['objects'])} objects")


if __name__ == "__main__":
    main()
