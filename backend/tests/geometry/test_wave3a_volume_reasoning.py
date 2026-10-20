"""Wave 3A (`volume-reasoning`): exact composite volume ratio and residual volume reasoning tests."""
from __future__ import annotations

import ast
import hashlib
import importlib.util
import json
import re
from copy import deepcopy
from fractions import Fraction as F
from pathlib import Path

import pytest

from app.ai import function_calling
from app.ai.fact_extraction import RESPONSE_CONTRACT, surface_fingerprint
from app.ai.function_route import run_fact_route, run_function_route
from app.ai.hybrid_preview import ADAPTER_VERSION
from app.simulation.geometry_functions import engine, planner, registry
from app.simulation.geometry_functions.planner import TypedFact
from app.simulation.semantic_program.interpreter import SemanticProgramInterpreter

ROOT = Path(__file__).resolve().parents[3]
RUN_DIR = ROOT / "docs/evaluation/geometry/runs/volume-reasoning"


def _load_oracle():
    spec = importlib.util.spec_from_file_location("wave3a_oracle_test", RUN_DIR / "oracle.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _squared(r, q: str) -> F:
    v = r.exec_result.final_memory["kq_" + q]
    return F(v.he) ** 2 * v.can if hasattr(v, "can") else F(v) ** 2


def test_independent_oracle_has_zero_product_or_test_imports():
    src = (RUN_DIR / "oracle.py").read_text(encoding="utf-8")
    tree = ast.parse(src)
    imported = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported.append(node.module)
    assert not any(m.startswith(("app", "tests", "backend")) for m in imported), imported


def test_wave3a_development_corpus_matches_independent_oracle():
    oracle = _load_oracle()
    corpus = json.loads((RUN_DIR / "corpus-dev.json").read_text(encoding="utf-8"))
    assert corpus["evaluation_class"] == "DEVELOPMENT_EVALUATION_NOT_BLIND"
    assert corpus["blind_holdout"] is False
    assert corpus["counts"]["positive_volume_ratio"] >= 10
    assert corpus["counts"]["positive_residual_volume"] >= 5
    assert corpus["counts"]["negative"] >= 12

    for c in corpus["cases"]:
        r = run_fact_route(c["text"], deepcopy(c["payload"]))
        if c["kind"] == "positive":
            assert r.status == "SERVED", (c["id"], r.code, r.reason)
            exp = oracle.expected(c)
            actual = {
                gid: {
                    "display": r.answers[gid],
                    "squared": str(_squared(r, gid)),
                }
                for gid in exp
            }
            assert actual == exp, c["id"]
        else:
            assert r.status == "REFUSED" and r.code in c["expected_codes"], (c["id"], r.status, r.code, r.reason)


def test_volume_ratio_and_residual_certificates_and_scene3d_pedagogy():
    corpus = json.loads((RUN_DIR / "corpus-dev.json").read_text(encoding="utf-8"))
    case_ratio = next(c for c in corpus["cases"] if c["id"] == "VR-01-equilateral-midpoint-section-ratio")
    case_res = next(c for c in corpus["cases"] if c["id"] == "RV-05-two-disjoint-subtracted-pyramids-residual")

    r_ratio = run_fact_route(case_ratio["text"], deepcopy(case_ratio["payload"]))
    assert r_ratio.status == "SERVED"
    ratio_certs = [s for s in r_ratio.trace if s["step"] == "certify_volume_ratio"]
    assert len(ratio_certs) == 1
    assert ratio_certs[0]["numerator_solid"] == "P.EFG"
    assert ratio_certs[0]["denominator_solid"] == "P.UVW"
    assert ratio_certs[0]["ratio"] == "1/8"

    qty_ratio = {o["id"]: o for o in r_ratio.scene3d["objects"] if o["type"] == "quantity"}
    assert qty_ratio["kq_q_ratio"]["producer"] == "assign.volume_ratio"
    assert qty_ratio["kq_q_ratio"]["role"] == "Tỉ số thể tích"
    assert qty_ratio["kq_q_ratio"]["notation"] == "V(P.EFG)/V(P.UVW)"
    assert qty_ratio["kq_q_ratio"]["value"] == "1/8"
    assert set(qty_ratio["kq_q_ratio"]["depends"]) == {"v_tu_q_ratio", "v_mau_q_ratio"}

    r_res = run_fact_route(case_res["text"], deepcopy(case_res["payload"]))
    assert r_res.status == "SERVED"
    res_certs = [s for s in r_res.trace if s["step"] == "certify_residual_volume"]
    assert len(res_certs) == 1
    cert = res_certs[0]
    assert cert["original_solid"] == "S.ABC"
    assert cert["subtracted_solids"] == ["S.ABM", "S.ANC"]
    assert cert["containment_verified"] is True
    assert cert["shared_boundary_verified"] is True
    assert cert["disjoint_interiors_verified"] is True
    assert cert["positive_residual_verified"] is True

    # Ensure no fabricated residual 3D solid mesh is created in Scene3D
    solids_in_scene = [o for o in r_res.scene3d["objects"] if o["type"] == "solid"]
    assert {o["notation"] for o in solids_in_scene} == {"S.ABC", "S.ABM", "S.ANC"}
    qty_res = {o["id"]: o for o in r_res.scene3d["objects"] if o["type"] == "quantity"}
    assert qty_res["kq_q_res"]["producer"] == "assign.residual_volume"
    assert qty_res["kq_q_res"]["role"] == "Thể tích phần còn lại"
    assert qty_res["kq_q_res"]["notation"] == "V(S.ABC) - V(S.ABM) - V(S.ANC)"
    assert qty_res["kq_q_res"]["value"] == "24"
    assert set(qty_res["kq_q_res"]["depends"]) == {"v_goc_q_res", "v_cat_q_res_1", "v_cat_q_res_2"}


@pytest.mark.parametrize("case_id", ["VR-04-mixed-simson-lateral-ratios", "RV-01-equilateral-pyramid-cut-midpoint-apex"])
def test_renaming_vertices_and_reversing_facts_preserves_exact_answers(case_id):
    corpus = json.loads((RUN_DIR / "corpus-dev.json").read_text(encoding="utf-8"))
    case = deepcopy(next(c for c in corpus["cases"] if c["id"] == case_id))
    mapping = dict(zip("SABCMNP", "ZUVWDEF"))

    def rename(v):
        if isinstance(v, str):
            return re.sub(r"[A-Z]", lambda m: mapping.get(m[0], m[0]), v)
        if isinstance(v, list):
            return [rename(x) for x in v]
        if isinstance(v, dict):
            return {k: (x if k in ("id", "kind", "role", "quantity", "point_kind", "shape", "measure", "solid_type") else rename(x)) for k, x in v.items()}
        return v

    renamed_text = rename(case["text"])
    renamed_payload = rename(case["payload"])
    renamed_payload["facts"].reverse()
    r = run_fact_route(renamed_text, renamed_payload)
    assert r.status == "SERVED", (r.code, r.reason)
    for gid, exp in _load_oracle().expected(case).items():
        assert r.answers[gid] == exp["display"]
        assert str(_squared(r, gid)) == exp["squared"]


@pytest.mark.parametrize("case_id,goal_key", [
    ("VR-01-equilateral-midpoint-section-ratio", "kq_q_ratio"),
    ("RV-01-equilateral-pyramid-cut-midpoint-apex", "kq_q_res"),
])
def test_tampered_interpreter_answer_fails_closed_with_engine_self_check_failed(monkeypatch, case_id, goal_key):
    corpus = json.loads((RUN_DIR / "corpus-dev.json").read_text(encoding="utf-8"))
    case = deepcopy(next(c for c in corpus["cases"] if c["id"] == case_id))
    orig_exec = SemanticProgramInterpreter.execute

    def tamper(self, *a, **kw):
        res = orig_exec(self, *a, **kw)
        res.final_memory[goal_key] = F(999)
        return res

    monkeypatch.setattr(SemanticProgramInterpreter, "execute", tamper)
    r = run_fact_route(case["text"], case["payload"])
    assert r.status == "REFUSED" and r.code == "ENGINE_SELF_CHECK_FAILED"


def test_direct_route_interior_point_without_shared_boundary_face_refuses(monkeypatch):
    # A sub-pyramid whose apex is an interior point (not sharing any boundary face of the original solid
    # except possibly lower-dimensional contact when base is also shrunk) must fail closed.
    monkeypatch.setattr(engine, "kiem_nguon", lambda *a, **kw: {})
    calls = [
        dict(id="root", fn="pyramid", args=dict(apex="S", base=list("ABC")), source={"quotes": ["Cho hình chóp S.ABC."]}),
        dict(id="base", fn="regular_polygon", args=dict(vertices=list("ABC"), side="6"), source={"quotes": ["Đáy ABC là tam giác đều cạnh 6."]}),
        dict(id="perp", fn="perpendicular_line_plane", args=dict(line=list("SA"), plane=list("ABC")), source={"quotes": ["SA vuông góc với (ABC)."]}),
        dict(id="sa", fn="segment_length", args=dict(segment=list("SA"), value="6"), source={"quotes": ["SA = 6."]}),
        dict(id="pM", fn="divide_segment", args=dict(point="M", segment=list("SA"), ratio="1/3"), source={"quotes": ["Gọi M thuộc SA sao cho MA = 2SM."]}),
        dict(id="pN", fn="divide_segment", args=dict(point="N", segment=list("SB"), ratio="1/3"), source={"quotes": ["Gọi N thuộc SB sao cho NB = 2SN."]}),
        dict(id="pP", fn="divide_segment", args=dict(point="P", segment=list("SC"), ratio="1/3"), source={"quotes": ["Gọi P thuộc SC sao cho PC = 2SP."]}),
        dict(id="pG", fn="centroid", args=dict(point="G", polygon=list("ABC")), source={"quotes": ["Gọi G là trọng tâm tam giác ABC."]}),
        dict(id="pI", fn="midpoint", args=dict(point="I", segment=list("SG")), source={"quotes": ["Gọi I là trung điểm của SG."]}),
        dict(id="child", fn="pyramid", args=dict(apex="I", base=list("MNP")), source={"quotes": ["Xét hình chóp I.MNP."]}),
        dict(id="q_res", fn="ask_residual_volume", args=dict(original_solid="S.ABC", subtracted_solids=["I.MNP"]),
             source={"quotes": ["Tính thể tích phần còn lại của khối chóp S.ABC sau khi cắt bỏ khối chóp I.MNP."]}),
    ]
    text = " ".join(c["source"]["quotes"][0] for c in calls)
    r = run_function_route(text, {"calls": calls})
    assert r.status == "REFUSED" and r.code == "RESIDUAL_CONTAINMENT_UNPROVED", (r.code, r.reason)


def test_wave3a_version_and_surface_fingerprint_invariants():
    assert registry.REGISTRY_VERSION == "geometry-functions/11"
    assert planner.PLANNER_VERSION == "geometry-fact-planner/11"
    assert engine.ENGINE_VERSION == "geometry-function-engine/9"
    assert ADAPTER_VERSION == "hybrid-preview-adapter/2"
    assert RESPONSE_CONTRACT == "flat"
    assert registry.REGISTRY["ask_volume_ratio"].provider_offered is False
    assert registry.REGISTRY["ask_residual_volume"].provider_offered is False

    # All 4 locked provider surface fingerprints must remain byte-identical
    assert surface_fingerprint("flat") == "485d3834db8b18cfdb24143bfbb14deb8f5b7a9d74cb612d48db8c08252e507a"
    assert surface_fingerprint("v3") == "4bff35bbf690a9973b2b7834019b908d507bbbb4277928e36d12dcff657e226f"
    assert function_calling.surface_fingerprint() == "7ea511a6e3828c9adcc8402aa2d7d6b1d433e67a01ec4329c3009c46af652b25"
    typed_fact_sha = hashlib.sha256(
        json.dumps(TypedFact.model_json_schema(), sort_keys=True, ensure_ascii=False).encode("utf-8")
    ).hexdigest()
    assert typed_fact_sha == "aa9d93eeac9f1659af8e5acd42af1904b7aaed674a8ab0f56f0c7dd8b2ad4ee8"
    decl_sha = hashlib.sha256(
        json.dumps(registry.function_declarations(), sort_keys=True, ensure_ascii=False).encode("utf-8")
    ).hexdigest()
    assert decl_sha == "5ceb0f999d4d7c1ee37c02207ea6470a7f972a168d6c52fa597392934d86f169"


def test_self_ratio_and_duplicate_subtracted_solids_refused():
    # Self-ratio (numerator_solid == denominator_solid) must fail closed on both routes
    text = (
        "Cho hình chóp S.ABC có đáy ABC là tam giác đều cạnh 2a. "
        "Cạnh bên SA vuông góc với mặt phẳng (ABC) và SA = 3a. "
        "Tính tỉ số thể tích của khối chóp S.ABC và khối chóp S.ABC."
    )
    payload = {
        "facts": [
            dict(id="sol", kind="solid", role="premise", solid="S.ABC", solid_type="pyramid", points_a=["S"], points_b=list("ABC"),
                 quotes=["Cho hình chóp S.ABC"]),
            dict(id="base", kind="polygon_shape", role="premise", shape="equilateral_triangle", points=list("ABC"),
                 quotes=["đáy ABC là tam giác đều"]),
            dict(id="ab", kind="length", role="premise", points=list("AB"), measure="segment", value="2a",
                 quotes=["đáy ABC là tam giác đều cạnh 2a"]),
            dict(id="perp", kind="perpendicular", role="premise",
                 points_a=list("SA"), points_b=list("ABC"), quotes=["Cạnh bên SA vuông góc với mặt phẳng (ABC)"]),
            dict(id="sa", kind="length", role="premise", points=list("SA"), measure="segment", value="3a",
                 quotes=["SA = 3a"]),
            dict(id="q_ratio", kind="question", role="question", quantity="volume_ratio",
                 points_a=list("SABC"), points_b=list("SABC"),
                 quotes=["Tính tỉ số thể tích của khối chóp S.ABC và khối chóp S.ABC."]),
        ]
    }
    r_fact = run_fact_route(text, payload)
    assert r_fact.status == "REFUSED" and r_fact.code == "UNSUPPORTED_VOLUME_RATIO", (r_fact.code, r_fact.reason)

    calls = [
        dict(id="root", fn="pyramid", args=dict(apex="S", base=list("ABC")), source={"quotes": ["Cho hình chóp S.ABC"]}),
        dict(id="base", fn="regular_polygon", args=dict(vertices=list("ABC"), side="2a"), source={"quotes": ["đáy ABC là tam giác đều cạnh 2a."]}),
        dict(id="perp", fn="perpendicular_line_plane", args=dict(line=list("SA"), plane=list("ABC")), source={"quotes": ["Cạnh bên SA vuông góc với mặt phẳng (ABC)"]}),
        dict(id="sa", fn="segment_length", args=dict(segment=list("SA"), value="3a"), source={"quotes": ["SA = 3a."]}),
        dict(id="q_ratio", fn="ask_volume_ratio", args=dict(numerator_solid="S.ABC", denominator_solid="S.ABC"),
             source={"quotes": ["Tính tỉ số thể tích của khối chóp S.ABC và khối chóp S.ABC."]}),
    ]
    r_call = run_function_route(text, {"calls": calls})
    assert r_call.status == "REFUSED" and r_call.code == "SCHEMA_INVALID", (r_call.code, r_call.reason)
