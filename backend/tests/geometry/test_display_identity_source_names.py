# -*- coding: utf-8 -*-
"""Backend-owned display identity (run `visual-hybrid-final-corrections`).

Two learner-visible names were wrong at the backend; the frontend prints notation verbatim (`a9d05dda`) so only the
backend may fix them:

  1. A section's vertex-cycle notation fell back to the IR id of a vertex that has no notation
     (`ky_hieu_toan(s) or s`), and spelled an id where the vertex shows another name. (Adapter /3's own `MI1I2I3`
     is a separate, unconsumed research builder: §3 locks that it stays out of the product.)
  2. On the default route a plane the problem calls `(P)` was shown as `(HUW)`, a name made of model construction
     points. Owner rule (2026-10-24): the declared one-letter name wins only when the problem text writes it and exactly
     one plane in the scene declares it.

Names only: ids, coordinates, dependencies and provenance are asserted unchanged where a case could move them.
"""
from __future__ import annotations

import re
from copy import deepcopy
from pathlib import Path

import pytest

from app.simulation.semantic_program.contract import SemanticProgramSpec
from app.simulation.semantic_program.display_names import ten_hien_thi
from app.simulation.semantic_program.interpreter import SemanticProgramInterpreter
from app.simulation.semantic_program.request_contract import RequestContract
from app.simulation.semantic_program.scene3d import build_scene3d
from app.simulation.semantic_program.simulation_state import build_simulation_state
from app.simulation.semantic_program.source_entities import ky_hieu_toan

# ══ 1. Section vertex cycle: only from notations the vertices themselves show ══════════════════════════════════════


def test_section_cycle_never_falls_back_to_an_unnamed_vertex_id():
    an = "giao_canh_sb"
    assert ky_hieu_toan(an) is None                       # precondition: an id, not a symbol
    ht = ten_hien_thi({"M": {"type": "point3"}, "N": {"type": "point3"}, an: {"type": "point3"},
                       "td": {"type": "section", "section_vertex_names": ["M", "N", an]}})
    assert ht[an]["notation"] is None
    assert ht["td"]["notation"] is None
    assert all(an not in (ht["td"][k] or "") for k in ("label", "reference", "role"))


def test_section_cycle_kept_when_every_vertex_is_named():
    ht = ten_hien_thi({p: {"type": "point3"} for p in "MNP"}
                      | {"td": {"type": "section", "section_vertex_names": ["M", "N", "P"]}})
    assert ht["td"]["notation"] == "MNP"
    assert ht["td"]["label"] == "Thiết diện MNP"


def test_section_cycle_spells_the_notation_each_vertex_shows():
    # A vertex whose id is not a symbol but whose declared label is: the cycle reads the shown name, not the id.
    ht = ten_hien_thi({"M": {"type": "point3"}, "N": {"type": "point3"},
                       "trung_diem_sc": {"type": "point3", "label": "P"},
                       "td": {"type": "section", "section_vertex_names": ["M", "N", "trung_diem_sc"]}})
    assert ht["trung_diem_sc"]["notation"] == "P"
    assert ht["td"]["notation"] == "MNP"


# ══ 2. Declared plane name on the default route: grounded in the problem text and unique ═══════════════════════════

_DIEM = [("H", [0, 0, 3]), ("U", [1, 0, 3]), ("W", [0, 1, 3]), ("X", [0, 0, 1]), ("Y", [1, 0, 1]), ("Z", [0, 1, 1])]


def _chuong_trinh(*mat: tuple[str, str, tuple[str, str, str]]) -> dict:
    return {
        "spec_version": "1.0", "title": "Mặt phẳng khai tên",
        "memory_declarations": [{"name": n, "type": "point3", "initial_value": v} for n, v in _DIEM]
        + [{"name": ten, "type": "plane3"} for ten, _, _ in mat],
        "statements": [{"kind": "construct_plane", "target_var": ten, "label": nhan, "through": list(qua)}
                       for ten, nhan, qua in mat],
    }


def _mat(ct: dict, de: str | None) -> dict[str, dict]:
    spec = SemanticProgramSpec.model_validate(ct)
    ket = SemanticProgramInterpreter().execute(spec)
    hd = None if de is None else RequestContract(problem_text=de)
    canh = build_scene3d(build_simulation_state(spec, ket, hd))
    return {o["id"]: o for o in canh["objects"] if o["type"] == "plane3"}


DE_P = "Cho mặt cầu tâm I bán kính 5. Mặt phẳng (P) cách tâm I một khoảng bằng 3 cắt mặt cầu theo một đường tròn."


def test_declared_plane_name_written_in_the_problem_replaces_the_construction_point_name():
    p = _mat(_chuong_trinh(("P", "(P)", ("H", "U", "W"))), DE_P)["P"]
    assert p["notation"] == "(P)"


@pytest.mark.parametrize("de", [
    None,                                                       # no contract: nothing to ground against
    "",                                                         # empty source is "unchecked", not grounding
    "Cho mặt phẳng đi qua ba điểm và cắt mặt cầu tâm I.",       # the problem never names the plane
    "Cho điểm P nằm ngoài mặt cầu tâm I.",                       # a POINT named P does not ground the plane (P)
    "Mặt phẳng (P') cắt mặt cầu tâm I.",                         # (P′) is another name than (P)
])
def test_declared_plane_name_not_written_as_a_plane_keeps_the_composed_name(de):
    p = _mat(_chuong_trinh(("P", "(P)", ("H", "U", "W"))), de)["P"]
    assert p["notation"] == "(HUW)"


def test_two_planes_declaring_the_same_name_keep_their_composed_names():
    m = _mat(_chuong_trinh(("P", "(P)", ("H", "U", "W")), ("Q", "(P)", ("X", "Y", "Z"))), DE_P)
    assert (m["P"]["notation"], m["Q"]["notation"]) == ("(HUW)", "(XYZ)")


def test_greek_and_primed_declared_names_are_grounded_exactly():
    assert _mat(_chuong_trinh(("a", "(α)", ("H", "U", "W"))), "Mặt phẳng (α) cắt khối cầu.")["a"]["notation"] == "(α)"
    assert _mat(_chuong_trinh(("q", "(Q′)", ("H", "U", "W"))), "Mặt phẳng (Q') cắt khối cầu.")["q"]["notation"] == "(Q′)"


def test_plane_name_rule_moves_no_geometry():
    co, khong = (_mat(_chuong_trinh(("P", "(P)", ("H", "U", "W"))), de)["P"] for de in (DE_P, None))
    bo = {"notation", "label", "display_label", "reference", "role"}
    assert {k: v for k, v in co.items() if k not in bo} == {k: v for k, v in khong.items() if k not in bo}


# ══ 3. Adapter /4 (the only Hybrid scene the product consumes): no name spells an unnamed point ═══════════════════

_ROOT = Path(__file__).resolve().parents[3]


@pytest.fixture(scope="module")
def adapter4_scenes() -> list[tuple[str, dict]]:
    import runpy

    from app.ai.hybrid_offline import hybrid_offline_policy, run_hybrid_offline
    from app.ai.typed_fact_next_extraction import ReplayExtractor

    lock = runpy.run_path(str(_ROOT / "docs/evaluation/geometry/runs/hybrid-contract-v2/evaluate_grammar_set.py"))
    policy = hybrid_offline_policy({"HYBRID_ROUTE_D_PREVIEW": "1"})
    ra = []
    for case in lock["load_lock"]():
        raw = case["payload"]
        r = run_hybrid_offline(raw["problem_text"], ReplayExtractor({raw["problem_text"]: deepcopy(raw)}), policy=policy)
        if r.response["route_d"]["status"] == "SERVED":
            ra.append((case["id"], r.response["envelope"]["scene3d"]))
    return ra


def test_adapter4_never_names_an_object_through_a_point_without_notation(adapter4_scenes):
    assert len(adapter4_scenes) >= 20                                   # precondition: the served corpus is exercised
    lo = []
    for case_id, canh in adapter4_scenes:
        vo_danh = {o["id"] for o in canh["objects"] if o["type"] == "point3" and not o.get("notation")}
        if not vo_danh:
            continue
        an = re.compile(r"(?<![\w′'])[A-Z0-9′'.]*(?:" + "|".join(map(re.escape, sorted(vo_danh, key=len, reverse=True)))
                        + r")[A-Z0-9′'.]*(?![\w′'])")
        lo += [(case_id, o["id"], o["notation"]) for o in canh["objects"]
               if isinstance(o.get("notation"), str) and an.search(o["notation"])]
    assert lo == []


def test_adapter3_is_not_reachable_from_the_product():
    # Adapter /3 still spells `MI1I2I3` through points it declares unnamed (run report §P2). It is a research builder
    # with no product consumer: the frontend accepts only `hybrid-route-d-simulation/4`, and no product module imports it.
    nguoi_dung = [p.relative_to(_ROOT).as_posix() for p in (_ROOT / "backend/app").rglob("*.py")
                  if p.name != "adapter3_simulation.py"
                  and re.search(r"\badapter3_simulation\b", p.read_text(encoding="utf-8"))]
    assert nguoi_dung == []
