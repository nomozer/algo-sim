# -*- coding: utf-8 -*-
"""Final Backend Product Completion — end-to-end integration, 7-family coverage,
continuous 3D construction state, learner-surface notation, and continuity validation.

0 live Gemini HTTP calls (`ALLOW_LIVE_AI=0`). Uses recorded C26 payloads, deterministic
7-family product inputs, and adversarial fault injections.
"""
from __future__ import annotations

from copy import deepcopy
import importlib.util
import json
import re
from pathlib import Path

from fastapi.testclient import TestClient
import pytest

from app.ai.adapter4_route import run_typed_fact_next_v2_route
from app.ai.hybrid_offline import hybrid_offline_policy, run_hybrid_offline
from app.ai.typed_fact_next_extraction import (
    ReplayExtractor,
    _normalize_transport_payload,
    extract_typed_fact_next_v2,
)
from app.simulation.geometry.radical import parse_exact

ROOT = Path(__file__).resolve().parents[3]
LIVE_C26_DIR = ROOT / "docs/evaluation/geometry/runs/hybrid-live-extraction-retest"
TOOLS_DIR = ROOT / "docs/evaluation/geometry/runs/hybrid-master-backend-replacement/tools"
PREVIEW_POLICY = hybrid_offline_policy({"HYBRID_ROUTE_D_PREVIEW": "1"})

FORBIDDEN_LEARNER_SUBSTRINGS = (
    "Đại lượng đo",
    "Khối đa diện dựng từ",
    "Tiếp tục lời giải hình học",
    "Ghi nhận giá trị vừa tính được",
    "Khối cầu tâm điểm",
    "«Thể tích khối cong» trừ «Thể tích khối cong»",
    "đã chứng minh",
    "được chứng minh",
    "đpcm",
)
RAW_COORD_RE = re.compile(r"\(\s*-?\d+(?:/\d+)?\s*,\s*-?\d+(?:/\d+)?\s*,\s*-?\d+(?:/\d+)?\s*\)")


def _load_tool_module(name: str):
    spec = importlib.util.spec_from_file_location(name, TOOLS_DIR / f"{name}.py")
    mod = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(mod)
    return mod


def _c26_row(jsonl_name: str, case_id: str) -> tuple[dict, dict]:
    import sys

    if str(ROOT / "backend" / "scripts") not in sys.path:
        sys.path.insert(0, str(ROOT / "backend" / "scripts"))
    import run_s2_student_language_pilot as pilot

    study_map = {"k1-live.jsonl": "K-1", "s2-live.jsonl": "S-2", "r1-live.jsonl": "R-1"}
    specs = pilot.default_c21_pilot_specs()
    corpus = json.loads(Path(specs[study_map[jsonl_name]]["corpus_path"]).read_text(encoding="utf-8"))
    cases = {c["id"]: c for c in corpus["cases"]}
    for phase in ("full", "canary"):
        for line in (LIVE_C26_DIR / phase / jsonl_name).read_text(encoding="utf-8").splitlines():
            row = json.loads(line)
            if row.get("type") == "row" and row.get("case_id") == case_id:
                return cases[case_id], row
    raise KeyError(case_id)


def _seven_family_cases() -> list[tuple[str, dict, str]]:
    curved = _load_tool_module("curved_probe")
    curved_sec = _load_tool_module("curved_section_probe")
    circum_sph = _load_tool_module("circumscribed_sphere_probe")

    pyr_case, pyr_row = _c26_row("k1-live.jsonl", "K-A01")
    prism_case, prism_row = _c26_row("k1-live.jsonl", "K-A03")

    cuboid_text = (
        "Cho hình hộp chữ nhật ABCD.A'B'C'D' có AB = 2, AD = 3 và AA' = 4. "
        "Tính thể tích khối hộp chữ nhật ABCD.A'B'C'D'."
    )
    cuboid_payload = {
        "schema_version": "typed-fact-next/2",
        "problem_text": cuboid_text,
        "length_unit": "1",
        "solids": [
            {
                "solid_id": "s1",
                "solid_type": "prism",
                "notation": "ABCD.A'B'C'D'",
                "quote": "Cho hình hộp chữ nhật ABCD.A'B'C'D'",
            }
        ],
        "premises": [
            {"kind": "right_prism", "args": {"base": list("ABCD"), "top": ["A'", "B'", "C'", "D'"]}, "quote": "Cho hình hộp chữ nhật ABCD.A'B'C'D'", "solid_id": "s1"},
            {"kind": "rectangle", "args": {"vertices": list("ABCD")}, "quote": "Cho hình hộp chữ nhật ABCD.A'B'C'D'", "solid_id": "s1"},
            {"kind": "segment_length", "args": {"segment": ["A", "B"], "value": "2"}, "quote": "AB = 2", "solid_id": "s1"},
            {"kind": "segment_length", "args": {"segment": ["A", "D"], "value": "3"}, "quote": "AD = 3", "solid_id": "s1"},
            {"kind": "segment_length", "args": {"segment": ["A", "A'"], "value": "4"}, "quote": "AA' = 4", "solid_id": "s1"},
        ],
        "relations": [],
        "derived_sections": [],
        "simulation_goals": [{"goal_id": "sg1", "kind": "construct_object", "target_solid_id": "s1", "quote": "Cho hình hộp chữ nhật ABCD.A'B'C'D'"}],
        "math_goals": [{"goal_id": "mg1", "kind": "measurement", "goal_type": "volume", "solid_id": "s1", "target": {"solid_id": "s1"}, "quote": "Tính thể tích khối hộp chữ nhật ABCD.A'B'C'D'."}],
    }

    cube_text = "Cho hình lập phương MNPQ.M'N'P'Q' cạnh 3. Tính thể tích khối lập phương MNPQ.M'N'P'Q'."
    cube_quote = "Cho hình lập phương MNPQ.M'N'P'Q' cạnh 3."
    cube_payload = {
        "schema_version": "typed-fact-next/2",
        "problem_text": cube_text,
        "length_unit": "1",
        "solids": [
            {
                "solid_id": "s1",
                "solid_type": "prism",
                "notation": "MNPQ.M'N'P'Q'",
                "quote": cube_quote,
            }
        ],
        "premises": [
            {"kind": "right_prism", "args": {"base": list("MNPQ"), "top": ["M'", "N'", "P'", "Q'"]}, "quote": cube_quote, "solid_id": "s1"},
            {"kind": "regular_polygon", "args": {"vertices": list("MNPQ"), "side": "3"}, "quote": cube_quote, "solid_id": "s1"},
            {"kind": "segment_length", "args": {"segment": ["M", "M'"], "value": "3"}, "quote": cube_quote, "solid_id": "s1"},
        ],
        "relations": [],
        "derived_sections": [],
        "simulation_goals": [{"goal_id": "sg1", "kind": "construct_object", "target_solid_id": "s1", "quote": cube_quote}],
        "math_goals": [{"goal_id": "mg1", "kind": "measurement", "goal_type": "volume", "solid_id": "s1", "target": {"solid_id": "s1"}, "quote": "Tính thể tích khối lập phương MNPQ.M'N'P'Q'."}],
    }
    sph_payload = curved.payload(curved.SPH, "area", "Tính diện tích mặt cầu.")
    cyl_payload = curved.payload(curved.CYL, "area", "Tính diện tích toàn phần của hình trụ.")
    cone_res_payload = next(c[1] for c in curved_sec.CASES if c[0] == "cone.residual")
    cs_payload = next(c[1] for c in circum_sph.POSITIVE_CASES if c[0] == "cs.tetra_iso.volume")
    cs_unlabelled_payload = next(c[1] for c in circum_sph.POSITIVE_CASES if c[0] == "cs.tetra_236.surface_area")

    return [
        ("pyramid_constrained_section", pyr_row["raw_extraction"], pyr_case["expected"]["oracle"]["area"][0]),
        ("prism_right", prism_row["raw_extraction"], prism_case["expected"]["oracle"]["area"][0]),
        ("cuboid_volume", cuboid_payload, "24"),
        ("cube_nonstandard_labels", cube_payload, "27"),
        ("sphere_surface_area", sph_payload, "36π"),
        ("cylinder_total_area", cyl_payload, "48π"),
        ("cone_frustum_residual", cone_res_payload, "21π/2"),
        ("polyhedron_circumscribed_sphere", cs_payload, "4π√3"),
        ("polyhedron_circumscribed_sphere_unlabelled", cs_unlabelled_payload, "49π"),
    ]


# ── 1. End-to-End C26 Live-Replay Repairs & Fail-Closed Twins ───────────────────────────────────────────────────────


def _assert_matches_case_oracle(case: dict, envelope: dict) -> None:
    import run_s2_student_language_pilot as pilot

    observed = {k: sorted(map(str, v)) for k, v in pilot.P.served_quantities(envelope).items()}
    assert observed == pilot.expected_record(case)["expected_answers"]


def test_c26_s2_b_a03_simulation_goal_vertex_wire_shape_serves_and_adversarial_twins_refuse():
    case, row = _c26_row("s2-live.jsonl", "S2-B-A03_control_with_dimensions")
    raw = deepcopy(row["raw_extraction"])
    out = run_hybrid_offline(case["problem_text"], ReplayExtractor({case["problem_text"]: raw}), policy=PREVIEW_POLICY)
    assert out.response["route_d"]["status"] == "SERVED", out.response["envelope"].get("reason_code")
    _assert_matches_case_oracle(case, out.response["envelope"])

    # Adversarial twin 1: vertex label not mentioned in sg.quote must NOT be repaired and must fail closed
    bad_quote = deepcopy(raw)
    bad_quote["simulation_goals"][1]["vertex"] = "A"
    res_bad_quote = extract_typed_fact_next_v2(case["problem_text"], ReplayExtractor({case["problem_text"]: bad_quote}))
    assert res_bad_quote.payload is None and res_bad_quote.code == "INVALID_SIMULATION_GOAL"

    # Adversarial twin 2: unknown vertex in quote still fails S10 (`UNKNOWN_VERTEX_REF`)
    unknown_text = case["problem_text"] + " Dựng điểm Z."
    bad_unknown = deepcopy(raw)
    bad_unknown["problem_text"] = unknown_text
    bad_unknown["simulation_goals"][1] = {
        "goal_id": "sg2",
        "kind": "construct_object",
        "target_solid_id": "s1",
        "quote": "điểm Z",
        "vertex": "Z",
    }
    res_unknown = extract_typed_fact_next_v2(unknown_text, ReplayExtractor({unknown_text: bad_unknown}))
    assert res_unknown.payload is None and res_unknown.code == "UNKNOWN_VERTEX_REF"


def test_c26_r1_g01_line_through_two_points_serves_and_wrong_operand_refuses():
    case, row = _c26_row("r1-live.jsonl", "R1-G01")
    raw = deepcopy(row["raw_extraction"])
    out = run_hybrid_offline(case["problem_text"], ReplayExtractor({case["problem_text"]: raw}), policy=PREVIEW_POLICY)
    assert out.response["route_d"]["status"] == "SERVED", out.response["envelope"].get("reason_code")
    _assert_matches_case_oracle(case, out.response["envelope"])

    # Adversarial twin: model claims line passes through B instead of A while quoting "đi qua A"
    wrong_pt = deepcopy(raw)
    wrong_pt["math_goals"][0]["target"]["line"] = ["B", "@dp1"]
    r_bad = run_typed_fact_next_v2_route(wrong_pt)
    assert r_bad.status == "REFUSED" and r_bad.code == "SOURCE_OBJECT_MISMATCH"


def test_c26_r1_g02_diem_chinh_giua_serves_both_unnamed_and_named_and_wrong_edge_refuses():
    case, row = _c26_row("r1-live.jsonl", "R1-G02")
    raw = deepcopy(row["raw_extraction"])
    out = run_hybrid_offline(case["problem_text"], ReplayExtractor({case["problem_text"]: raw}), policy=PREVIEW_POLICY)
    assert out.response["route_d"]["status"] == "SERVED", out.response["envelope"].get("reason_code")
    _assert_matches_case_oracle(case, out.response["envelope"])

    # Named variant: "Gọi M là điểm chính giữa cạnh SB."
    named_text = (
        "Cho hình chóp S.ABCD có đáy ABCD là hình vuông cạnh 2, SA vuông góc với mặt phẳng (ABCD) và SA = 2. "
        "Gọi M là điểm chính giữa cạnh SB. Tính khoảng cách từ M đến mặt phẳng (SCD)."
    )
    named_payload = {
        "schema_version": "typed-fact-next/2",
        "problem_text": named_text,
        "length_unit": "1",
        "solids": [{"solid_id": "s1", "solid_type": "pyramid", "notation": "S.ABCD", "quote": "hình chóp S.ABCD"}],
        "premises": [
            {"kind": "regular_polygon", "args": {"vertices": list("ABCD"), "side": "2"}, "quote": "đáy ABCD là hình vuông cạnh 2", "solid_id": "s1"},
            {"kind": "perpendicular_line_plane", "args": {"line": ["S", "A"], "plane": list("ABCD")}, "quote": "SA vuông góc với mặt phẳng (ABCD)", "solid_id": "s1"},
            {"kind": "segment_length", "args": {"segment": ["S", "A"], "value": "2"}, "quote": "SA = 2", "solid_id": "s1"},
            {"kind": "midpoint", "args": {"point": "M", "segment": ["S", "B"]}, "quote": "Gọi M là điểm chính giữa cạnh SB", "solid_id": "s1"},
        ],
        "relations": [],
        "derived_sections": [],
        "simulation_goals": [{"goal_id": "sg1", "kind": "construct_object", "target_solid_id": "s1", "quote": "hình chóp S.ABCD"}],
        "math_goals": [{"goal_id": "mg1", "kind": "measurement", "goal_type": "distance", "solid_id": "s1", "target": {"point": "M", "plane": ["S", "C", "D"]}, "quote": "Tính khoảng cách từ M đến mặt phẳng (SCD)."}],
    }
    r_named = run_typed_fact_next_v2_route(named_payload)
    assert r_named.status == "SERVED" and r_named.answers == out.response["route_d"]["answers"]

    # Adversarial twin: wrong segment ["S", "C"] while text says "điểm chính giữa cạnh SB"
    wrong_seg = deepcopy(raw)
    wrong_seg["described_points"][0]["segment"] = ["S", "C"]
    r_wrong = run_typed_fact_next_v2_route(wrong_seg)
    assert r_wrong.status == "REFUSED" and r_wrong.code == "SOURCE_OBJECT_MISMATCH"


def test_c26_r1_f03_nested_unsupported_operand_refuses_out_of_scope_while_genuine_ambiguity_clarifies():
    case_f03, row_f03 = _c26_row("r1-live.jsonl", "R1-F03")
    out_f03 = run_hybrid_offline(
        case_f03["problem_text"],
        ReplayExtractor({case_f03["problem_text"]: deepcopy(row_f03["raw_extraction"])}),
        policy=PREVIEW_POLICY,
    )
    assert out_f03.response["route_d"]["status"] == "REFUSED"
    assert out_f03.response["route_d"]["refusal"]["code"] == "OUT_OF_SCOPE"
    assert out_f03.response["envelope"]["failure_category"] == "capability_gap"

    # Genuine missing/ambiguous cases remain AMBIGUOUS_FACT, and R1-E02 remains fail-closed SOURCE_OBJECT_MISMATCH
    for fn, cid in (("k1-live.jsonl", "K-E01"), ("k1-live.jsonl", "K-E02"), ("s2-live.jsonl", "S2-C-A01_goc_chieu"), ("r1-live.jsonl", "R1-E01")):
        c_amb, r_amb = _c26_row(fn, cid)
        out_amb = run_hybrid_offline(
            c_amb["problem_text"],
            ReplayExtractor({c_amb["problem_text"]: deepcopy(r_amb["raw_extraction"])}),
            policy=PREVIEW_POLICY,
        )
        assert out_amb.response["route_d"]["refusal"]["code"] == "AMBIGUOUS_FACT", cid

    c_e02, r_e02 = _c26_row("r1-live.jsonl", "R1-E02")
    out_e02 = run_hybrid_offline(
        c_e02["problem_text"],
        ReplayExtractor({c_e02["problem_text"]: deepcopy(r_e02["raw_extraction"])}),
        policy=PREVIEW_POLICY,
    )
    assert out_e02.response["route_d"]["status"] == "REFUSED"
    assert out_e02.response["route_d"]["refusal"]["code"] == "SOURCE_OBJECT_MISMATCH"


# ── 2. All 7 Geometry Families: Learner Surface, Notation, and Continuous Construction Steps ─────────────────────────


@pytest.mark.parametrize("family_id,payload,oracle", _seven_family_cases(), ids=[x[0] for x in _seven_family_cases()])
def test_seven_families_serve_clean_learner_surface_and_continuous_pedagogical_steps(family_id, payload, oracle):
    from app.simulation.geometry_functions.construction_continuity import validate_construction_continuity

    normed = _normalize_transport_payload(deepcopy(payload))
    text = normed["problem_text"]
    out = run_hybrid_offline(text, ReplayExtractor({text: normed}), policy=PREVIEW_POLICY)
    assert out.response["route_d"]["status"] == "SERVED", (family_id, out.response["envelope"].get("reason_code"))
    ans_map = out.response["route_d"]["answer_exact"]
    first_goal = next(iter(ans_map))
    assert parse_exact(ans_map[first_goal]["coef"]) == parse_exact(oracle)

    scene = out.response["envelope"]["scene3d"]
    assert validate_construction_continuity(scene) == []

    # Learner surface checks: no underscore, no generic placeholders, no broken curved strings, no raw coordinates
    learner_strings: list[str] = []
    for obj in scene["objects"]:
        if obj.get("render") != "non_visual":
            for field in ("label", "notation", "reference", "role", "display_label"):
                if obj.get(field):
                    learner_strings.append(str(obj[field]))
        if obj.get("formula") and obj["formula"].get("text"):
            learner_strings.append(str(obj["formula"]["text"]))
    for ev in scene["events"]:
        if ev.get("learner_text"):
            learner_strings.append(str(ev["learner_text"]))
        if ev.get("justification_text"):
            learner_strings.append(str(ev["justification_text"]))
    for st in scene["formation"]["steps"]:
        if st.get("learner_text"):
            learner_strings.append(str(st["learner_text"]))
            assert len(st["learner_text"]) <= 240, (family_id, st["learner_text"])

    bad = [
        s
        for s in learner_strings
        if "_" in s or any(tok in s for tok in FORBIDDEN_LEARNER_SUBSTRINGS) or RAW_COORD_RE.search(s)
    ]
    assert bad == [], (family_id, bad)

    if family_id == "pyramid_constrained_section":
        justs = [ev["justification_text"] for ev in scene["events"] if ev.get("justification_text")]
        assert justs and all("(P)" in j and "H1" not in j for j in justs), justs
    if family_id == "cylinder_total_area":
        assert any("O.O′" in s for s in learner_strings) and not any("O.O'" in s for s in learner_strings)

    # Continuous cumulative step invariants & 5-question pedagogical step_summary
    steps = scene["formation"]["steps"]
    assert len(steps) >= 2
    prev_state: set[str] = set()
    for idx, st in enumerate(steps):
        assert st["step_index"] == idx
        assert st["step_id"] == f"step_{idx}"
        assert st["coordinate_frame_id"] == "canonical_chart_v1"
        for req_key in (
            "depends_on",
            "preconditions",
            "created_ids",
            "reused_ids",
            "highlighted_ids",
            "retired_ids",
            "verification_refs",
            "step_summary",
        ):
            assert req_key in st, (family_id, idx, req_key)
        curr_state = set(st["visible_ids"]) | set(st["readout_ids"])
        created = set(st["created_ids"])
        reused = set(st["reused_ids"])
        highlighted = set(st["highlighted_ids"])
        retired = set(st["retired_ids"])
        assert created == curr_state - prev_state
        assert created.isdisjoint(reused)
        assert created.isdisjoint(highlighted)
        assert reused <= prev_state
        assert highlighted <= prev_state
        assert (prev_state - curr_state) <= retired
        summary = st["step_summary"]
        assert set(summary) == {"what", "inputs", "validity", "result", "next_use"}
        assert summary["what"] and summary["validity"] and summary["result"]
        assert isinstance(summary["inputs"], list) and isinstance(summary["next_use"], list)
        prev_state = curr_state


# ── 3. All 7 Adversarial Geometric Continuity Violations (§IV.4) ────────────────────────────────────────────────────


def _sample_section_scene() -> dict:
    case, row = _c26_row("k1-live.jsonl", "K-A01")
    raw = _normalize_transport_payload(deepcopy(row["raw_extraction"]))
    out = run_hybrid_offline(case["problem_text"], ReplayExtractor({case["problem_text"]: raw}), policy=PREVIEW_POLICY)
    assert out.response["route_d"]["status"] == "SERVED"
    return deepcopy(out.response["envelope"]["scene3d"])


@pytest.mark.parametrize(
    "tamper_kind,expected_code",
    [
        ("uncreated_dependency", "DEPENDENCY_BEFORE_CREATION"),
        ("identity_mutation", "OBJECT_IDENTITY_MUTATION"),
        ("step_contradiction", "GEOMETRIC_STEP_CONTRADICTION"),
        ("missing_provenance", "MISSING_OBJECT_PROVENANCE"),
        ("object_disappearance", "UNEXPLAINED_OBJECT_DISAPPEARANCE"),
        ("undetermined_measurement", "MEASUREMENT_USES_UNDETERMINED_OBJECT"),
        ("section_mismatch", "SECTION_OR_INTERSECTION_MISMATCH"),
    ],
)
def test_continuity_validator_rejects_all_seven_adversarial_discontinuities(tamper_kind: str, expected_code: str):
    from app.simulation.geometry_functions.construction_continuity import validate_construction_continuity

    scene = _sample_section_scene()
    assert validate_construction_continuity(scene) == []

    if tamper_kind == "uncreated_dependency":
        scene["formation"]["steps"][1]["depends_on"].append(scene["formation"]["steps"][-1]["readout_ids"][-1])
    elif tamper_kind == "identity_mutation":
        dup = deepcopy(scene["objects"][0])
        scene["objects"].append(dup)
    elif tamper_kind == "step_contradiction":
        scene["formation"]["steps"][-1]["coordinate_frame_id"] = "switched_frame_v2"
    elif tamper_kind == "missing_provenance":
        ghost = {
            "id": "ghost_pt",
            "type": "point3",
            "origin": "derived",
            "producer": None,
            "depends": [],
            "xyz": ["0", "0", "0"],
            "render": "point_marker",
            "label": "Điểm lạ",
            "display_label": "Điểm lạ",
            "reference": "điểm lạ",
            "notation": None,
            "role": "Điểm",
        }
        scene["objects"].append(ghost)
        scene["formation"]["steps"][1]["visible_ids"].append("ghost_pt")
        scene["formation"]["steps"][1]["created_ids"].append("ghost_pt")
    elif tamper_kind == "object_disappearance":
        victim = scene["formation"]["steps"][0]["visible_ids"][0]
        scene["formation"]["steps"][1]["visible_ids"] = [
            oid for oid in scene["formation"]["steps"][1]["visible_ids"] if oid != victim
        ]
    elif tamper_kind == "undetermined_measurement":
        fin_ev = next(e for e in scene["events"] if e["semantic_kind"] == "FINAL_RESULT")
        q_obj = next(o for o in scene["objects"] if o["id"] == fin_ev["object"])
        q_obj["exact"] = None
    elif tamper_kind == "section_mismatch":
        sec = next(o for o in scene["objects"] if o["type"] == "section")
        sec["polygon"][0] = ["99", "99", "99"]

    issues = validate_construction_continuity(scene)
    assert any(i["code"] == expected_code for i in issues), (tamper_kind, issues)


def test_function_route_fails_closed_when_continuity_validation_detects_violation(monkeypatch):
    import app.ai.function_route as FR
    from app.simulation.geometry_functions import construction_continuity as CC

    monkeypatch.setattr(
        CC,
        "validate_construction_continuity",
        lambda scene, trace=None: [{"code": "SECTION_OR_INTERSECTION_MISMATCH", "detail": "injected fault"}],
    )
    case, row = _c26_row("k1-live.jsonl", "K-A03")
    raw = _normalize_transport_payload(deepcopy(row["raw_extraction"]))
    r = run_typed_fact_next_v2_route(raw)
    assert r.status == "REFUSED" and r.code == "SCENE_BUILD_FAILED"


# ── 4. API Opt-in (`staging-replay`) and Production Default / Rollback (`LLM_ONLY`, `off`) ──────────────────────────


def test_analyze_api_hybrid_default_staging_replay_and_fail_closed_invalid_mode(monkeypatch, tmp_path):
    from app.ai.hybrid_offline import LOCAL_REPLAY_SCHEMA
    import app.main as main

    assert not (Path(main.__file__).resolve().parent / "simulation" / "geometry_compiler").exists()
    assert not (Path(main.__file__).resolve().parent / "ai" / "pipeline.py").exists()
    assert main.CACHE_VERSION == "132"
    monkeypatch.delenv("HYBRID_ROUTE_MODE", raising=False)
    assert main.hybrid_route_mode() == "live"

    case, row = _c26_row("k1-live.jsonl", "K-A03")
    normed = _normalize_transport_payload(deepcopy(row["raw_extraction"]))
    fixture_file = tmp_path / "staging_replay.json"
    fixture_file.write_text(
        json.dumps({"schema": LOCAL_REPLAY_SCHEMA, "outputs": {case["problem_text"]: normed}}, ensure_ascii=False),
        encoding="utf-8",
    )

    monkeypatch.setenv("ALLOW_LIVE_AI", "0")
    monkeypatch.setenv("HYBRID_ROUTE_MODE", "staging-replay")
    monkeypatch.setenv("HYBRID_REPLAY_CORPUS", str(fixture_file))

    from tests.route_client import route_client
    client = route_client(main.app)
    resp = client.post("/api/analyze", json={"input": {"type": "text", "content": case["problem_text"]}})
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["envelope"]["status"] == "ok"
    assert body["route_d"]["status"] == "SERVED"
    steps = body["envelope"]["scene3d"]["formation"]["steps"]
    assert steps and "step_summary" in steps[0] and steps[0]["coordinate_frame_id"] == "canonical_chart_v1"

    # Setting HYBRID_ROUTE_MODE=off fails closed with 503 INVALID_HYBRID_ROUTE_MODE
    monkeypatch.setenv("HYBRID_ROUTE_MODE", "off")
    assert main.hybrid_route_mode() == "invalid"
    r_off = client.post("/api/analyze", json={"input": {"type": "text", "content": case["problem_text"]}})
    assert r_off.status_code == 503 and r_off.json()["reason_code"] == "INVALID_HYBRID_ROUTE_MODE"
