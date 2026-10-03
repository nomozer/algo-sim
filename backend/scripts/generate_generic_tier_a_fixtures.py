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


def _ab_bang_0(contract, text: str):
    """The contract an analyze stage produces when it reads AB = 0 (fact, invariant, text)."""
    facts = tuple(
        fact.model_copy(update={"values": ("0",)}) if fact.label == "AB" else fact
        for fact in contract.input_facts
    )
    invariants = tuple(
        invariant.model_copy(update={"expected": "0"})
        if set(invariant.points) == {"A", "B"} else invariant
        for invariant in contract.source_invariants
    )
    return contract.model_copy(update={
        "input_facts": facts,
        "source_invariants": invariants,
        "problem_text": text,
    })


def _zero_ab(text: str, contract):
    """Negative "non-positive length" STATED BY THE TEXT (W17 §15.3 cause SOURCE): the text itself
    writes AB = 0 — or, for the cube, which states its edge without a segment name, "cạnh bằng 0".
    Before W17 the cube text was left saying "cạnh bằng 4" (a valid problem, V = 64) while the
    contract carried AB = 0, and the refusal told the learner to fix a correct text."""
    changed_text = text.replace("AB = 3", "AB = 0").replace("cạnh bằng 4", "cạnh bằng 0")
    assert changed_text != text, text
    return changed_text, _ab_bang_0(contract, changed_text)


def _tiem_ab_bang_0(text: str, contract):
    """System-cause negative (W17 §15.3 cause CONSTRUCTION): the text stays VALID and unchanged; only
    the contract carries AB = 0 — a wrong analyze stage, never a wrong problem."""
    return text, _ab_bang_0(contract, text)


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
        assert envelope["refusal_cause"] == "SOURCE", envelope
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


# ── W12 · a GIVEN the problem text does not state ────────────────────────────
# One stated measurement is removed from the text; the fake analyze TRANSPORT
# still returns it, and the program is the one a model writes when it believes
# the claim (compiled from the full text). Through the default LLM_ONLY route
# the production boundary must refuse, with no Scene3D and no repair round.

def _pyramid_payload() -> dict:
    return {
        "input_facts": [
            {"id": "fact_len_AB", "kind": "float", "label": "AB", "value": ["3"]},
            {"id": "fact_len_AC", "kind": "float", "label": "AC", "value": ["4"]},
            {"id": "fact_len_SA", "kind": "float", "label": "SA", "value": ["5"]},
        ],
        "geometric_relations": [
            {"kind": "perpendicular_lines", "line": ["A", "B"], "other_line": ["A", "C"],
             "source_fact_id": "fact_perp_base", "model_assumption": False},
            {"kind": "perpendicular_line_plane", "line": ["S", "A"], "plane": ["A", "B", "C"],
             "source_fact_id": "fact_perp_lateral", "model_assumption": False},
        ],
        # No `solid_topology`: like `_pyramid_control_contract`, this family is
        # routed by its relations (a 3-vertex base cycle routes to the
        # quadrilateral-base family and is refused there).
        "obligations": [{"kind": "volume", "container": "khoi_chop", "witness": "the_tich_khoi"}],
    }


def _rect_pyramid_payload() -> dict:
    return {
        "input_facts": [
            {"id": "fact_len_AB", "kind": "float", "label": "AB", "value": ["3"]},
            {"id": "fact_len_AD", "kind": "float", "label": "AD", "value": ["4"]},
            {"id": "fact_len_SA", "kind": "float", "label": "SA", "value": ["6"]},
        ],
        "geometric_relations": [
            {"kind": "perpendicular_lines", "line": ["A", "B"], "other_line": ["A", "D"],
             "source_fact_id": "fact_perp_base", "model_assumption": False},
            {"kind": "perpendicular_line_plane", "line": ["S", "A"], "plane": ["A", "B", "C"],
             "source_fact_id": "fact_perp_lateral", "model_assumption": False},
        ],
        "obligations": [{"kind": "volume", "container": "khoi_chop", "witness": "v"}],
        "solid_topology": {"solid_kind": "pyramid", "apex": "S", "base_cycle": ["A", "B", "C", "D"],
                           "base_shape": "rectangle"},
    }


def _ungrounded_cases() -> dict[str, tuple[str, str, str | dict, str | dict]]:
    """family -> (full text, removed sentence part, analyze payload, program)."""
    from tests.geometry.test_source_grounding_closure import PRISM_TEXT, _prism_payload
    from app.simulation.geometry_compiler.compiler import bien_dich
    from app.simulation.geometry_compiler.contract_adapter import build_fact_graph

    def compiled(text: str, payload: dict) -> dict:
        contract = build_request_contract(payload, problem_text=text, domain="hinh_hoc")
        return {"spec_version": "1.0", **bien_dich(build_fact_graph(contract).graph).program}

    pyramid_text = _pyramid_control_contract()[0]
    rect_text = _rect_pyramid_contract()[0]
    cuboid_text, cuboid_payload = _cuboid_p01_payload()
    cube_text, cube_payload = _cube_p01_payload()
    raw = RNB.doc_raw_theo_thu_tu(P1)
    return {
        "triangular_pyramid": (pyramid_text, ", SA = 5", _pyramid_payload(),
                               compiled(pyramid_text, _pyramid_payload())),
        "triangular_prism": (PRISM_TEXT, " Cạnh bên AD = 5.", _prism_payload(),
                             compiled(PRISM_TEXT, _prism_payload())),
        "rectangular_pyramid": (rect_text, ", SA = 6", _rect_pyramid_payload(),
                                compiled(rect_text, _rect_pyramid_payload())),
        "cuboid": (cuboid_text, ", AA' = 5", cuboid_payload, compiled(cuboid_text, cuboid_payload)),
        "cube": (cube_text, " có cạnh bằng 4", cube_payload, compiled(cube_text, cube_payload)),
        "cross_section": (RNB.doc_de_bai()[P1], " và đỉnh S(0;0;6)",
                          raw["semantic_analyze"][0], raw["semantic_program"][0]),
    }


def _fake_analyze_refusal(text: str, payload, program, stage: str, reason_code: str) -> dict:
    """Analyze + synthesis answered by a fake transport (2 responses, 0 model calls); the
    request must be refused at `stage` with `reason_code` and never sent to repair."""
    as_json = lambda x: x if isinstance(x, str) else json.dumps(x, ensure_ascii=False, default=str)
    responses = [as_json(payload), as_json(program)]
    calls: list[int] = []

    async def fake_transport(*_args, **_kwargs):
        calls.append(1)
        if len(calls) > len(responses):
            raise AssertionError("a source defect was sent to repair")
        return responses[len(calls) - 1]

    saved_gemini = PL.call_gemini
    saved_mode = os.environ.pop("GEOMETRY_COMPILER_MODE", None)
    try:
        PL.call_gemini = fake_transport
        envelope = attach_learner_reason(asyncio.run(PL.run_pipeline(text, "offline_evidence_key")))
    finally:
        PL.call_gemini = saved_gemini
        if saved_mode is not None:
            os.environ["GEOMETRY_COMPILER_MODE"] = saved_mode
    assert envelope["status"] == "unsupported", envelope.get("status")
    assert "scene3d" not in envelope and "final_memory" not in envelope, envelope
    assert envelope["error_code"] == "input_not_grounded", envelope
    assert envelope["stage_reached"] == stage, envelope
    assert envelope["reason_code"] == reason_code, envelope
    assert len(calls) == 2, calls
    return envelope


def _ungrounded_fixture(full_text: str, cut: str, payload, program) -> tuple[str, dict]:
    text = full_text.replace(cut, "")
    assert text != full_text, cut
    return text, _fake_analyze_refusal(text, payload, program, "grounding", "GIVEN_VALUE_NOT_IN_SOURCE")


#: W15 — the dimension each family's assumption negative removes: (analyze fact label, scalar).
_BO_KICH_THUOC = {"triangular_pyramid": ("SA", "SA_length"), "triangular_prism": ("AD", "AD_length"),
                  "rectangular_pyramid": ("SA", "SA_length"), "cuboid": ("AA'", "AA_prime_length"),
                  "cube": ("AB", "AB_length")}


def _assumption_cases() -> dict[str, tuple[str, str, dict, dict, str]]:
    """family -> (text, removed part, payload, program, expected reason code).

    W15: the text loses one dimension (the same cut as the ungrounded case) and the program
    keeps it by LAYOUT — the analyze fact and every scalar that carries the dimension are
    dropped, so nothing claims it as GIVEN and the request reaches the assumption gate. The
    cross-section loses S's coordinates; S stays at its layout position as a model assumption,
    and the text never says SA ⊥ (ABCD), so no template applies (INVARIANCE_UNPROVEN)."""
    ra = {}
    for name, (full_text, cut, payload, program) in _ungrounded_cases().items():
        payload = json.loads(payload) if isinstance(payload, str) else copy.deepcopy(payload)
        program = json.loads(program) if isinstance(program, str) else copy.deepcopy(program)
        if name in _BO_KICH_THUOC:
            nhan, ten = _BO_KICH_THUOC[name]
            payload["input_facts"] = [f for f in payload["input_facts"] if f.get("label") != nhan]
            bo = {ten} | {s["target_var"] for s in program["statements"] if ten in json.dumps(s.get("expr", {}))}
            program["memory_declarations"] = [m for m in program["memory_declarations"] if m["name"] not in bo]
            program["statements"] = [s for s in program["statements"] if s.get("target_var") not in bo]
            ma = "ASSUMPTION_DETERMINES_ANSWER"
        else:
            payload["input_facts"] = [f for f in payload["input_facts"] if f.get("id") != "S_coords"]
            for s in program["statements"]:
                if s.get("target_var") == "S":
                    s.pop("source_fact_id", None)
                    s["model_assumption"] = "Đặt đỉnh S trên trục Oz để dựng hình."
            ma = "ASSUMPTION_INVARIANCE_UNPROVEN"
        ra[name] = (full_text.replace(cut, ""), cut, payload, program, ma)
    return ra


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

    # W17 §15.3: a VALID text whose contract the system got wrong — the learner must not be told
    # to fix the text.
    system_text, system_contract = _tiem_ab_bang_0(*_cube_contract())
    system = attach_learner_reason(asyncio.run(_run_compiler(system_text, system_contract)))
    assert (system["status"], system["reason_code"], system["refusal_cause"]) == (
        "unsupported", "NON_POSITIVE_LENGTH", "CONSTRUCTION"), system
    (fixtures / "cube_system_cause.json").write_text(json.dumps(
        _wrapper("cube_injected_non_positive", system_text, system,
                 "deterministic_compiler_injected_contract_refusal",
                 source_reason_code="NON_POSITIVE_LENGTH", refusal_cause="CONSTRUCTION"),
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

    for name, (full_text, cut, payload, program) in _ungrounded_cases().items():
        text, envelope = _ungrounded_fixture(full_text, cut, payload, program)
        (fixtures / f"{name}_ungrounded.json").write_text(json.dumps(
            _wrapper(f"{name}_ungrounded_given", text, envelope,
                     "fake_analyze_transport_through_production_refusal",
                     source_reason_code="GIVEN_VALUE_NOT_IN_SOURCE",
                     removed_from_text=cut.strip(" ,.")),
            ensure_ascii=False, indent=2,
        ), encoding="utf-8")

    for name, (text, cut, payload, program, ma) in _assumption_cases().items():
        envelope = _fake_analyze_refusal(text, payload, program, "assumption", ma)
        (fixtures / f"{name}_assumption.json").write_text(json.dumps(
            _wrapper(f"{name}_assumption", text, envelope,
                     "fake_analyze_transport_through_production_refusal",
                     source_reason_code=ma, removed_from_text=cut.strip(" ,.")),
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
