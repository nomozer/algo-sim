# -*- coding: utf-8 -*-
"""Freeze six cross-family Scene3D browser fixtures through product boundaries.

Offline only: Analyze is replaced by a canonical RequestContract and synthesis
is either the deterministic compiler or a frozen accepted program. Any attempt
to call a model raises immediately.
"""
from __future__ import annotations

import argparse
import asyncio
import copy
import hashlib
import json
import os
import sys
from pathlib import Path
from typing import Callable

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "backend"))

from app.ai import pipeline as PL  # noqa: E402
from app.learner_messages import attach_learner_reason  # noqa: E402
from app.simulation.semantic_program.analyze_contract import build_request_contract  # noqa: E402
from app.simulation.semantic_program.obligations import Obligation  # noqa: E402
from app.simulation.semantic_program.route import verify_and_compile  # noqa: E402
from app.simulation.semantic_program.validator import validate_semantic_program  # noqa: E402
from scripts import replay_negative_boundaries as RNB  # noqa: E402
from tests.geometry.test_prism_production_route import (  # noqa: E402
    _prism_p01_contract,
    _pyramid_control_contract,
)
from tests.geometry.test_rectangular_pyramid_production_route import (  # noqa: E402
    _rect_pyramid_contract,
)
from tests.geometry.test_cuboid_cube_production_route import (  # noqa: E402
    _cuboid_p01_payload,
    _cube_p01_payload,
)

CANDIDATE = json.loads((
    ROOT / "docs" / "evaluation" / "semantic-benchmark" / "EVALUATION_CANDIDATE.json"
).read_text(encoding="utf-8"))
PRODUCT_COMMIT_SHA = CANDIDATE["product_commit_sha"]
PRODUCT_TREE_SHA = CANDIDATE["measured_system"]["tree_hash"]
P1 = "p1_chop_thiet_dien_khoang_cach"


def _sha(path: Path) -> str:
    # Blob content, so the hash does not depend on a CRLF (core.autocrlf) checkout.
    return hashlib.sha256(path.read_bytes().replace(b"\r\n", b"\n")).hexdigest()


async def _run_compiler(text: str, contract) -> dict:
    saved_analyze = PL.stage_semantic_analyze
    saved_gemini = PL.call_gemini
    saved_mode = os.environ.get("GEOMETRY_COMPILER_MODE")
    try:
        os.environ["GEOMETRY_COMPILER_MODE"] = "DETERMINISTIC_FIRST"

        async def canonical_analyze(*_args, **_kwargs):
            return contract, None

        async def no_model(*_args, **_kwargs):
            raise AssertionError("Generic Tier-A fixture attempted a live model call")

        PL.stage_semantic_analyze = canonical_analyze
        PL.call_gemini = no_model
        return await PL.run_pipeline(text, "offline_evidence_key")
    finally:
        PL.stage_semantic_analyze = saved_analyze
        PL.call_gemini = saved_gemini
        if saved_mode is None:
            os.environ.pop("GEOMETRY_COMPILER_MODE", None)
        else:
            os.environ["GEOMETRY_COMPILER_MODE"] = saved_mode


async def _run_frozen_program(text: str, contract, spec) -> dict:
    saved_analyze = PL.stage_semantic_analyze
    saved_program = PL.stage_semantic_program
    saved_gemini = PL.call_gemini
    saved_mode = os.environ.get("GEOMETRY_COMPILER_MODE")
    try:
        os.environ["GEOMETRY_COMPILER_MODE"] = "LLM_ONLY"

        async def canonical_analyze(*_args, **_kwargs):
            return contract, None

        async def canonical_program(*_args, **_kwargs):
            return spec, None

        async def no_model(*_args, **_kwargs):
            raise AssertionError("Frozen-program replay attempted a live model call")

        PL.stage_semantic_analyze = canonical_analyze
        PL.stage_semantic_program = canonical_program
        PL.call_gemini = no_model
        return await PL.run_pipeline(text, "offline_evidence_key", semantic_route="serve")
    finally:
        PL.stage_semantic_analyze = saved_analyze
        PL.stage_semantic_program = saved_program
        PL.call_gemini = saved_gemini
        if saved_mode is None:
            os.environ.pop("GEOMETRY_COMPILER_MODE", None)
        else:
            os.environ["GEOMETRY_COMPILER_MODE"] = saved_mode


def _zero_ab(text: str, contract):
    changed_text = text.replace("AB = 3", "AB = 0")
    facts = tuple(
        fact.model_copy(update={"values": ("0",)}) if fact.label == "AB" else fact
        for fact in contract.input_facts
    )
    invariants = tuple(
        invariant.model_copy(update={"expected": "0"})
        if set(invariant.points) == {"A", "B"} else invariant
        for invariant in contract.source_invariants
    )
    return changed_text, contract.model_copy(update={
        "input_facts": facts,
        "source_invariants": invariants,
        "problem_text": changed_text,
    })


def _compiler_fixture(factory: Callable, *, negative: bool) -> tuple[str, dict]:
    text, contract = factory()
    if negative:
        text, contract = _zero_ab(text, contract)
    envelope = asyncio.run(_run_compiler(text, contract))
    if negative:
        envelope = attach_learner_reason(envelope)
        assert envelope["status"] == "unsupported", envelope
        assert envelope["reason"] == "NON_POSITIVE_LENGTH", envelope
        assert envelope["error_code"] == "semantic_program_invalid", envelope
        assert envelope["stage_reached"] == "semantic_analyze", envelope
    else:
        assert envelope["status"] == "ok" and envelope.get("scene3d"), envelope
    return text, envelope


def _cuboid_contract():
    text, payload = _cuboid_p01_payload()
    return text, build_request_contract(payload, problem_text=text, domain="hinh_hoc")


def _cube_contract():
    text, payload = _cube_p01_payload()
    return text, build_request_contract(payload, problem_text=text, domain="hinh_hoc")


def _cross_section_negative() -> tuple[str, dict, dict]:
    raw = RNB.doc_raw_theo_thu_tu(P1)
    text = RNB.doc_de_bai()[P1].replace("z = 3", "z = 9")
    analyze = json.loads(raw["semantic_analyze"][0])
    program = json.loads(raw["semantic_program"][0])
    for fact in analyze["input_facts"]:
        if fact["id"] == "alpha_plane_def":
            fact["value"] = ["Mặt phẳng (α): z = 9"]
    for statement in program["statements"]:
        if statement["kind"] == "construct_plane_from_equation":
            statement["d"] = -9
            statement["label"] = "Mặt phẳng (α): z = 9"

    contract = build_request_contract(analyze, problem_text=text, domain="hinh_hoc")
    contract = contract.model_copy(update={
        "obligations": contract.obligations + (
            Obligation(
                kind="section_matches",
                container="T",
                params={"witness": None, "solid": "S.ABCD", "plane": "alpha_plane"},
            ),
        ),
    })
    validation = validate_semantic_program(program)
    assert validation.ok and validation.spec is not None, validation.error
    spec = validation.spec

    kernel_outcome = verify_and_compile(contract, spec)
    assert kernel_outcome.stage_reached == "execution", kernel_outcome
    assert kernel_outcome.error_code == "semantic_program_invalid", kernel_outcome
    assert any("PLANE_DOES_NOT_CUT" in detail for detail in kernel_outcome.details), kernel_outcome

    envelope = attach_learner_reason(asyncio.run(_run_frozen_program(text, contract, spec)))
    assert envelope["status"] == "unsupported", envelope
    assert envelope["error_code"] == "semantic_program_invalid", envelope
    assert envelope["stage_reached"] == "execution", envelope
    assert "PLANE_DOES_NOT_CUT" in envelope["reason"], envelope
    gate = {
        "semantics": "requested_non_empty_section_must_fail_closed",
        "kernel_error_code": "PLANE_DOES_NOT_CUT",
        "product_error_code": envelope["error_code"],
        "product_stage_reached": envelope["stage_reached"],
    }
    return text, envelope, gate


def _cross_section_positive() -> tuple[str, dict]:
    raw = RNB.doc_raw_theo_thu_tu(P1)
    text = RNB.doc_de_bai()[P1]
    contract = build_request_contract(
        json.loads(raw["semantic_analyze"][0]), problem_text=text, domain="hinh_hoc",
    )
    validation = validate_semantic_program(json.loads(raw["semantic_program"][0]))
    assert validation.ok and validation.spec is not None, validation.error
    envelope = asyncio.run(_run_frozen_program(text, contract, validation.spec))
    assert envelope["status"] == "ok" and envelope.get("scene3d"), envelope
    return text, envelope


def _wrapper(case_id: str, text: str, envelope: dict, source: str, **extra) -> dict:
    return {
        "fixture_schema": "generic-tier-a-fixture/1",
        "case_id": case_id,
        "problem_text": text,
        "source": source,
        "product_commit_sha": PRODUCT_COMMIT_SHA,
        "product_tree_sha": PRODUCT_TREE_SHA,
        "application_llm_calls": 0,
        "envelope": envelope,
        **extra,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    out = args.out.resolve()
    fixtures = out / "fixtures"
    fixtures.mkdir(parents=True, exist_ok=True)

    cases = (
        ("triangular_pyramid", _pyramid_control_contract),
        ("triangular_prism", _prism_p01_contract),
        ("rectangular_pyramid", _rect_pyramid_contract),
        ("cuboid", _cuboid_contract),
        ("cube", _cube_contract),
    )
    for name, factory in cases:
        positive_text, positive = _compiler_fixture(factory, negative=False)
        negative_text, negative = _compiler_fixture(factory, negative=True)
        (fixtures / f"{name}_positive.json").write_text(json.dumps(
            _wrapper(name, positive_text, positive, "deterministic_compiler_production_route"),
            ensure_ascii=False, indent=2,
        ), encoding="utf-8")
        (fixtures / f"{name}_negative.json").write_text(json.dumps(
            _wrapper(f"{name}_non_positive", negative_text, negative,
                     "deterministic_compiler_production_refusal",
                     source_reason_code="NON_POSITIVE_LENGTH"),
            ensure_ascii=False, indent=2,
        ), encoding="utf-8")

    canonical_path = ROOT / "docs" / "evaluation" / "geometry" / \
        "product-ui-result-rendering" / "fixtures" / f"{P1}.json"
    canonical = json.loads(canonical_path.read_text(encoding="utf-8"))
    cross_text, cross_envelope = _cross_section_positive()
    positive_cross = _wrapper(
        "cross_section", cross_text, cross_envelope,
        "canonical_program_through_current_production_replay",
        canonical_fixture_path=str(canonical_path.relative_to(ROOT)).replace("\\", "/"),
        canonical_fixture_sha256=_sha(canonical_path),
        source_artifact_path=canonical["source_artifact_path"],
        source_sha256=canonical["source_sha256"],
    )
    (fixtures / "cross_section_positive.json").write_text(
        json.dumps(positive_cross, ensure_ascii=False, indent=2), encoding="utf-8",
    )
    negative_text, negative_cross, contract_gate = _cross_section_negative()
    (fixtures / "cross_section_negative.json").write_text(json.dumps(
        _wrapper("cross_section_outside_plane", negative_text, negative_cross,
                 "canonical_program_through_production_refusal", contract_gate=contract_gate),
        ensure_ascii=False, indent=2,
    ), encoding="utf-8")

    inventory = {}
    for path in sorted(fixtures.glob("*.json")):
        inventory[path.name] = {"sha256": _sha(path), "bytes": path.stat().st_size}
    (out / "FIXTURE_MANIFEST.json").write_text(json.dumps({
        "schema_version": "generic-tier-a-fixtures/1",
        "product_commit_sha": PRODUCT_COMMIT_SHA,
        "product_tree_sha": PRODUCT_TREE_SHA,
        "application_llm_calls": 0,
        "fixtures": inventory,
    }, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Wrote {len(inventory)} frozen fixtures to {fixtures}")


if __name__ == "__main__":
    main()
