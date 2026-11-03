"""Route D /4 repairs driven by gold-extraction replay failures (run `hybrid-live-validation`).

The Wave 3 corpus is read-only evidence; it is already development-contaminated (W3-F1), so these cases are regression
locks, not held-out evidence. Every positive repair has an adversarial neighbour that must keep refusing.
"""
from __future__ import annotations

import json
import os
from copy import deepcopy
from pathlib import Path

import pytest

os.environ.setdefault("ALLOW_LIVE_AI", "0")

from app.ai.adapter4_route import build_adapter4_response, run_typed_fact_next_v2_route  # noqa: E402

ROOT = Path(__file__).resolve().parents[3]
CORPUS = ROOT / "docs/evaluation/geometry/runs/hybrid-v2-independent-vietnamese-geometry-holdout-wave3/inputs/holdout-wave3.json"


def _case(cid: str) -> dict:
    cases = json.loads(CORPUS.read_text(encoding="utf-8"))["cases"]
    return deepcopy(next(c for c in cases if c["id"] == cid)["payload"])


def _swap(payload: dict, old: str, new: str) -> dict:
    """Same text substitution in the source and in every quote (a consistent mutant, not a forged quote)."""
    return json.loads(json.dumps(payload, ensure_ascii=False).replace(old, new))


def _run(payload: dict) -> tuple[object, dict]:
    r = run_typed_fact_next_v2_route(payload)
    return r, build_adapter4_response(r, payload["problem_text"])


def test_versions_record_the_result_changes():
    """LUẬT BUMP (MIGRATION_CHECKLIST M-2): Source Gate wording ⇒ registry /32; coverage + radicals ⇒ engine /24."""
    from app.simulation.geometry_functions.engine import ENGINE_VERSION
    from app.simulation.geometry_functions.planner import PLANNER_VERSION
    from app.simulation.geometry_functions.registry import REGISTRY_VERSION

    assert (REGISTRY_VERSION, PLANNER_VERSION, ENGINE_VERSION) == (
        "geometry-functions/32", "geometry-fact-planner/26", "geometry-function-engine/24")


# ── 1. "khi bị cắt bởi" is construction wording, not a condition (both clause readers agree) ──────────────────────────

def test_khi_bi_cat_in_the_goal_sentence_is_not_a_conditional_clause():
    r, resp = _run(_case("W3-B01"))
    assert r.status == "SERVED", (r.code, getattr(r, "reason", None))
    assert resp["route_d"]["status"] == "SERVED"


@pytest.mark.parametrize("old,new", [
    ("Thiết lập mặt phẳng (P) đi qua", "Nếu mặt phẳng (P) đi qua"),
    ("Thiết lập mặt phẳng (P) đi qua", "Giả sử mặt phẳng (P) đi qua"),
])
def test_a_real_condition_on_the_plane_still_refuses(old, new):
    p = _swap(_case("W3-B01"), old, new)
    r, resp = _run(p)
    assert r.status != "SERVED"
    assert resp["route_d"]["status"] == "REFUSED"


def test_khi_followed_by_a_non_construction_word_after_the_plane_still_conditional():
    from app.simulation.geometry_functions.registry import _vai_tro_tai

    de = "Mặt phẳng (P) qua H vuông góc SF khi H trùng S. Tìm thiết diện."
    assert _vai_tro_tai(de, de.index("Mặt phẳng")) == "CONDITIONAL"
    de2 = "Hãy tìm thiết diện của khối chóp S.EFG khi bị cắt bởi mặt phẳng (P)."
    assert _vai_tro_tai(de2, de2.index("thiết diện")) is None


# ── 2. "khối lăng trụ tam giác X.Y" in the two-line plane slice ────────────────────────────────────────────────────────

@pytest.mark.parametrize("cid", ["W3-B34", "W3-B35", "W3-B36"])
def test_solid_noun_khoi_and_base_polygon_word_are_read_on_the_two_line_slice(cid):
    r, resp = _run(_case(cid))
    assert r.status == "SERVED", (r.code, getattr(r, "reason", None))
    assert resp["route_d"]["status"] == "SERVED"


def test_base_polygon_word_that_contradicts_the_base_still_refuses():
    p = _swap(_case("W3-B34"), "khối lăng trụ tam giác BCD.B'C'D'", "khối lăng trụ tứ giác BCD.B'C'D'")
    r, resp = _run(p)
    assert r.status != "SERVED"
    assert resp["route_d"]["status"] == "REFUSED"


@pytest.mark.parametrize("cid", ["W3-B34", "W3-B35", "W3-B36"])
def test_projection_and_altitude_foot_wording_still_bind_point_and_image(cid):
    """"của đỉnh B'" and "chân đường cao hạ/kẻ từ K' xuống/đến (KLM) là/trùng với L" bind exactly the source's point and
    image: any other vertex of the plane as image, or another top vertex as point, refuses."""
    p = _case(cid)
    proj = next(x for x in p["premises"] if x["kind"] == "orthogonal_projection")["args"]
    for wrong in [v for v in proj["plane"] if v != proj["image"]]:
        q = deepcopy(p)
        next(x for x in q["premises"] if x["kind"] == "orthogonal_projection")["args"]["image"] = wrong
        assert run_typed_fact_next_v2_route(q).status == "REFUSED", wrong
    other_top = next(v + "'" for v in proj["plane"] if v + "'" != proj["point"])
    q = deepcopy(p)
    next(x for x in q["premises"] if x["kind"] == "orthogonal_projection")["args"]["point"] = other_top
    assert run_typed_fact_next_v2_route(q).status == "REFUSED"


@pytest.mark.parametrize("old,new", [
    ("xuống mặt phẳng (KLM)", "tới mặt phẳng (KLM)"),
    ("chân đường cao hạ từ", "chân đường vuông góc hạ từ"),
    ("trùng với đỉnh L", "trùng với trung điểm L"),
])
def test_both_readers_share_one_altitude_foot_grammar(old, new):
    """Review MINOR-1: the sentence reader (`_C_CHIEU`) accepts exactly the binder's words; other wordings refuse."""
    from app.simulation.geometry_functions.registry import _C_CHIEU

    ok = "chân đường cao hạ từ K' xuống mặt phẳng (KLM) trùng với đỉnh L"
    assert _C_CHIEU.fullmatch(ok)
    assert not _C_CHIEU.fullmatch(ok.replace(old, new))
    r, _resp = _run(_swap(_case("W3-B35"), old, new))
    assert r.status == "REFUSED"


def test_ratio_with_he_thuc_is_read_and_a_wrong_ratio_still_refuses():
    from app.simulation.geometry_functions.registry import _TY_SO

    assert _TY_SO.search("Trên đoạn thẳng SE chọn điểm H thỏa mãn hệ thức SH = 3/11 SE")
    p = _case("W3-B01")
    next(x for x in p["premises"] if x["kind"] == "divide_segment")["args"]["ratio"] = "4/11"
    assert run_typed_fact_next_v2_route(p).status == "REFUSED"


# ── 4. Exact radicals whose square part is made of small primes above MAX_RADICAND² ────────────────────────────────────

def test_radicand_above_the_old_input_bound_with_a_small_prime_square_part_normalizes_exactly():
    from fractions import Fraction

    from app.simulation.geometry.radical import Radical, RadicalDomainError, radical

    n = 1125673687043559399375000                       # 60259484250² · 310
    r = radical(1, n)
    assert isinstance(r, Radical) and (r.he, r.can) == (Fraction(60259484250), 310)
    for bad in (10**24 + 7, 10**36 + 1, 4 * (10**12 + 39)):
        with pytest.raises(RadicalDomainError):
            radical(1, bad)


def test_rectangle_pyramid_perpendicular_section_with_large_intermediate_radicand_is_served():
    r, resp = _run(_case("W3-A06"))
    assert r.status == "SERVED", (r.code, getattr(r, "reason", None))
    assert resp["route_d"]["status"] == "SERVED"


# ── 3. Stated cuts that do not cover the section: typed refusal at the kernel, not an adapter-invalid result ─────────

@pytest.mark.parametrize("cid", ["W3-N54", "W3-N55"])
def test_stated_cuts_missing_a_section_vertex_refuse_section_boundary_incomplete(cid):
    r, resp = _run(_case(cid))
    assert r.status == "REFUSED"
    assert r.code == "SECTION_BOUNDARY_INCOMPLETE"
    assert resp["route_d"]["refusal"]["code"] == "SECTION_BOUNDARY_INCOMPLETE"


def test_stated_cuts_covering_every_section_vertex_are_served():
    p = _swap(_case("W3-N54"), "cắt các cạnh bên SB, SC lần lượt tại N, P", "cắt các cạnh bên SB, SC, SD lần lượt tại N, P, K")
    sec = p["derived_sections"][0]
    sec["stated_intersections"].append({"edge": ["S", "D"], "point": "K", "quote": "cắt các cạnh bên SB, SC, SD lần lượt tại N, P, K"})
    r, resp = _run(p)
    assert r.status == "SERVED", (r.code, getattr(r, "reason", None))
    assert resp["route_d"]["status"] == "SERVED"
    labels = [v["label"] for v in resp["route_d"]["sections"][0]["vertices"]]
    assert sorted(labels) == ["K", "M", "N", "P"]
