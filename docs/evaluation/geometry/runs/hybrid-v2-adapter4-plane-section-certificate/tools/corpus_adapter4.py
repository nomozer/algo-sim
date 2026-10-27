"""Finite authored development and tamper corpus for Adapter /4 plane-only section certificates.

Registration precedes product modification. Zero live provider calls.
"""
from __future__ import annotations

from copy import deepcopy
from fractions import Fraction as F
import importlib.util
import json
from pathlib import Path


def _load_oracle():
    path = Path(__file__).with_name("oracle_adapter4.py")
    spec = importlib.util.spec_from_file_location("oracle_adapter4", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _prism_positive(
    cid: str,
    family: str = "triangle",
    line: tuple[str, str] = ("A", "B"),
    dims: tuple[int, int, int] = (6, 8, 12),
    symbolic: bool = False,
    labels: str = "ABC",
    reverse: bool = False,
    mode: str = "both",  # "both" | "section_only" | "area_only"
) -> dict:
    x, y, h = dims
    base = list(labels if family in ("triangle", "oblique") else "ABCD")
    top = [v + "'" for v in base]
    name = "".join(base) + "." + "".join(top)
    a, b, c = base[:3]
    oblique = family == "oblique"
    word = (
        "hình lập phương"
        if family == "cube"
        else "hình hộp chữ nhật"
        if family == "cuboid"
        else "lăng trụ"
        if oblique
        else "lăng trụ đứng"
    )
    decl = f"Cho {word} {name}."
    unit = "a" if symbolic else "1"
    val = lambda n: f"{n}a" if symbolic else str(n)

    premises = []
    if not oblique:
        premises.append({"kind": "right_prism", "args": {"base": base, "top": top}, "quote": decl})
    if family == "cube":
        q_sq = f"Đáy {''.join(base)} là hình vuông cạnh {val(x)}."
        premises.append({"kind": "base_is_square", "args": {"vertices": base, "side": val(x)}, "quote": q_sq})
        coords = {a: (0, 0, 0), b: (x, 0, 0), c: (x, y, 0), base[3]: (0, y, 0)}
    elif len(base) == 3:
        q_right = f"Đáy {a}{b}{c} là tam giác vuông tại {a}."
        q_ab = f"{a}{b} = {val(x)}."
        q_ac = f"{a}{c} = {val(y)}."
        premises += [
            {"kind": "right_angle", "args": {"vertex": a, "rays": [b, c]}, "quote": q_right},
            {"kind": "segment_length", "args": {"segment": [a, b], "value": val(x)}, "quote": q_ab},
            {"kind": "segment_length", "args": {"segment": [a, c], "value": val(y)}, "quote": q_ac},
        ]
        coords = {a: (0, 0, 0), b: (x, 0, 0), c: (0, y, 0)}
    else:
        q_rect = f"Đáy {''.join(base)} là hình chữ nhật."
        q_ab = f"{a}{b} = {val(x)}."
        q_ad = f"{a}{base[3]} = {val(y)}."
        premises += [
            {"kind": "rectangle", "args": {"vertices": base}, "quote": q_rect},
            {"kind": "segment_length", "args": {"segment": [a, b], "value": val(x)}, "quote": q_ab},
            {"kind": "segment_length", "args": {"segment": [a, base[3]], "value": val(y)}, "quote": q_ad},
        ]
        coords = {a: (0, 0, 0), b: (x, 0, 0), c: (x, y, 0), base[3]: (0, y, 0)}

    lateral = (0, 0, h)
    if oblique:
        q_foot = f"Gọi H là trung điểm của {b}{c}."
        q_proj = f"Hình chiếu vuông góc của {a}' lên ({''.join(base)}) là H."
        q_aa = f"{a}{a}' = {val(13)}."
        premises += [
            {"kind": "midpoint", "args": {"point": "H", "segment": [b, c]}, "quote": q_foot},
            {"kind": "orthogonal_projection", "args": {"point": a + "'", "image": "H", "plane": base}, "quote": q_proj},
            {"kind": "segment_length", "args": {"segment": [a, a + "'"], "value": val(13)}, "quote": q_aa},
        ]
        coords["H"] = (F(x, 2), F(y, 2), 0)
        lateral = (F(x, 2), F(y, 2), h)
    else:
        q_aa = f"{a}{a}' = {val(h)}."
        premises.append({"kind": "segment_length", "args": {"segment": [a, a + "'"], "value": val(h)}, "quote": q_aa})

    for v in base:
        coords[v + "'"] = tuple(q + r for q, r in zip(coords[v], lateral))

    seg = [b, c + "'"] if len(base) == 3 else [a, c + "'"]
    coords["M"] = tuple(F(u + v, 2) for u, v in zip(coords[seg[0]], coords[seg[1]]))
    q_mid = f"Gọi M là trung điểm của {''.join(seg)}."
    premises.append({"kind": "midpoint", "args": {"point": "M", "segment": seg}, "quote": q_mid})

    mapping = dict(zip("ABC", base)) | {v + "'": base[i] + "'" for i, v in enumerate("ABC")}
    d = [mapping.get(v, v) for v in line]
    defn = f"Dựng mặt phẳng (P) đi qua M và vuông góc với {''.join(d)}."
    sec_ask = f"Dựng thiết diện của {word} {name} với (P)."
    area_ask = f"Tính diện tích thiết diện của {word} {name} với (P)."

    quotes = [decl, *(p["quote"] for p in premises if p["quote"] != decl)]
    sim_goals = []
    math_goals = []
    if mode == "both":
        sec_q = f"{defn} {sec_ask}"
        area_q = f"{defn} {area_ask}"
        quotes += [sec_q, area_q]
        sim_goals.append({"goal_id": "draw", "kind": "construct_plane_section", "target_section_id": "sec", "quote": sec_q})
        math_goals.append({"goal_id": "q", "kind": "measurement", "goal_type": "area", "target": {"section_id": "sec"}, "quote": area_q})
    elif mode == "section_only":
        sec_q = f"{defn} {sec_ask}"
        quotes.append(sec_q)
        sim_goals.append({"goal_id": "draw", "kind": "construct_plane_section", "target_section_id": "sec", "quote": sec_q})
    elif mode == "area_only":
        sec_q = defn
        area_q = f"{defn} {area_ask}"
        quotes.append(area_q)
        sim_goals.append({"goal_id": "sim_solid", "kind": "construct_object", "target_solid_id": "pr", "quote": decl})
        math_goals.append({"goal_id": "q", "kind": "measurement", "goal_type": "area", "target": {"section_id": "sec"}, "quote": area_q})

    text = " ".join(dict.fromkeys(quotes))
    if reverse:
        premises = list(reversed(premises))
    payload = {
        "schema_version": "typed-fact-next/2",
        "problem_text": text,
        "length_unit": unit,
        "solids": [{"solid_id": "pr", "solid_type": "prism", "notation": name, "quote": decl}],
        "premises": premises,
        "derived_sections": [
            {
                "section_id": "sec",
                "plane_name": "P",
                "target_solid_id": "pr",
                "plane_kind": "through_point_perpendicular_line",
                "through_point": "M",
                "perpendicular_line": d,
                "stated_intersections": [],
                "quote": sec_q,
            }
        ],
        "simulation_goals": sim_goals,
        "math_goals": math_goals,
    }
    geometry = {
        "solid_type": "prism",
        "points": {k: [str(v_i) for v_i in v] for k, v in coords.items()},
        "base": base,
        "top": top,
        "point": "M",
        "plane_relation": "perpendicular",
        "line": d,
    }
    return {
        "id": cid,
        "group": "positive",
        "family": family,
        "mode": mode,
        "payload": payload,
        "geometry": geometry,
        "expected_route_status": "SERVED",
        "expected_adapter4_status": "SERVED",
        "expected_codes": [],
        "expected_certificate_category": "ENGINE_DERIVED_SECTION",
    }


def _prism_parallel_base_positive() -> dict:
    decl = "Cho lăng trụ đứng ABC.A'B'C'."
    q_base = "Đáy ABC là tam giác đều cạnh a."
    q_aa = "AA' = a."
    q_mid = "Gọi M là trung điểm của AA'."
    q_sec = "Gọi (α) là mặt phẳng qua M và song song với (ABC). Dựng thiết diện của lăng trụ đứng ABC.A'B'C' cắt bởi (α)."
    q_area = "Gọi (α) là mặt phẳng qua M và song song với (ABC). Tính diện tích thiết diện của lăng trụ đứng ABC.A'B'C' cắt bởi (α)."
    text = " ".join([decl, q_base, q_aa, q_mid, q_sec, q_area])
    payload = {
        "schema_version": "typed-fact-next/2",
        "problem_text": text,
        "length_unit": "a",
        "solids": [{"solid_id": "pr", "solid_type": "prism", "notation": "ABC.A'B'C'", "quote": decl}],
        "premises": [
            {"kind": "right_prism", "args": {"base": ["A", "B", "C"], "top": ["A'", "B'", "C'"]}, "quote": decl},
            {"kind": "base_is_equilateral_triangle", "args": {"vertices": ["A", "B", "C"], "side": "a"}, "quote": q_base},
            {"kind": "segment_length", "args": {"segment": ["A", "A'"], "value": "a"}, "quote": q_aa},
            {"kind": "midpoint", "args": {"point": "M", "segment": ["A", "A'"]}, "quote": q_mid},
        ],
        "derived_sections": [
            {
                "section_id": "sec",
                "plane_name": "α",
                "target_solid_id": "pr",
                "plane_kind": "through_point_parallel_plane",
                "through_point": "M",
                "parallel_plane": ["A", "B", "C"],
                "stated_intersections": [],
                "quote": q_sec,
            }
        ],
        "simulation_goals": [{"goal_id": "draw", "kind": "construct_plane_section", "target_section_id": "sec", "quote": q_sec}],
        "math_goals": [{"goal_id": "q", "kind": "measurement", "goal_type": "area", "target": {"section_id": "sec"}, "quote": q_area}],
    }
    return {
        "id": "prism-parallel-base-plane-only",
        "group": "positive",
        "family": "equilateral_prism_parallel",
        "mode": "both",
        "payload": payload,
        "geometry": {"area_squared_override": "3/16", "vertex_count_override": 3},
        "expected_route_status": "SERVED",
        "expected_adapter4_status": "SERVED",
        "expected_codes": [],
        "expected_certificate_category": "ENGINE_DERIVED_SECTION",
    }


def _pyramid_parallel_base_positive(cid: str, mode: str = "both") -> dict:
    decl = "Cho hình chóp S.ABC."
    q_base = "Đáy ABC là tam giác đều cạnh a."
    q_perp = "SA vuông góc với mặt phẳng (ABC)."
    q_sa = "SA = a."
    q_mid = "Gọi M là trung điểm của SA."
    defn = "Mặt phẳng (α) qua M và song song với (ABC)."
    sec_ask = "Dựng thiết diện của hình chóp S.ABC cắt bởi (α)."
    area_ask = "Tính diện tích thiết diện của hình chóp S.ABC cắt bởi (α)."
    quotes = [decl, q_base, q_perp, q_sa, q_mid, defn, sec_ask]
    math_goals = []
    if mode == "both":
        quotes.append(area_ask)
        math_goals.append({"goal_id": "q", "kind": "measurement", "goal_type": "area", "target": {"section_id": "sec"}, "quote": area_ask})
    text = " ".join(quotes)
    payload = {
        "schema_version": "typed-fact-next/2",
        "problem_text": text,
        "length_unit": "a",
        "solids": [{"solid_id": "pyr", "solid_type": "pyramid", "notation": "S.ABC", "quote": decl}],
        "premises": [
            {"kind": "base_is_equilateral_triangle", "args": {"vertices": ["A", "B", "C"], "side": "a"}, "quote": q_base},
            {"kind": "line_perp_plane", "args": {"line": ["S", "A"], "plane": ["A", "B", "C"]}, "quote": q_perp},
            {"kind": "segment_length", "args": {"segment": ["S", "A"], "value": "a"}, "quote": q_sa},
            {"kind": "point_is_midpoint", "args": {"point": "M", "segment": ["S", "A"]}, "quote": q_mid},
        ],
        "derived_sections": [
            {
                "section_id": "sec",
                "plane_name": "α",
                "target_solid_id": "pyr",
                "plane_kind": "through_point_parallel_plane",
                "through_point": "M",
                "parallel_plane": ["A", "B", "C"],
                "stated_intersections": [],
                "quote": defn,
            }
        ],
        "simulation_goals": [{"goal_id": "draw", "kind": "construct_plane_section", "target_section_id": "sec", "quote": sec_ask}],
        "math_goals": math_goals,
    }
    return {
        "id": cid,
        "group": "positive",
        "family": "pyramid_parallel",
        "mode": mode,
        "payload": payload,
        "geometry": {"area_squared_override": "3/256", "vertex_count_override": 3},
        "expected_route_status": "SERVED",
        "expected_adapter4_status": "SERVED",
        "expected_codes": [],
        "expected_certificate_category": "ENGINE_DERIVED_SECTION",
    }


def _pyramid_perpendicular_line_positive() -> dict:
    decl = "Cho hình chóp S.ABCD."
    q_base = "Đáy ABCD là hình vuông cạnh 4."
    q_perp = "SA vuông góc với mặt phẳng (ABCD)."
    q_sa = "SA = 4."
    q_mid = "Gọi M là trung điểm của SA."
    q_sec = "Dựng mặt phẳng (P) đi qua M và vuông góc với SA. Dựng thiết diện của hình chóp S.ABCD với (P)."
    q_area = "Dựng mặt phẳng (P) đi qua M và vuông góc với SA. Tính diện tích thiết diện của hình chóp S.ABCD với (P)."
    text = " ".join([decl, q_base, q_perp, q_sa, q_mid, q_sec, q_area])
    payload = {
        "schema_version": "typed-fact-next/2",
        "problem_text": text,
        "length_unit": "1",
        "solids": [{"solid_id": "pyr", "solid_type": "pyramid", "notation": "S.ABCD", "quote": decl}],
        "premises": [
            {"kind": "base_is_square", "args": {"vertices": ["A", "B", "C", "D"], "side": "4"}, "quote": q_base},
            {"kind": "line_perp_plane", "args": {"line": ["S", "A"], "plane": ["A", "B", "C", "D"]}, "quote": q_perp},
            {"kind": "segment_length", "args": {"segment": ["S", "A"], "value": "4"}, "quote": q_sa},
            {"kind": "midpoint", "args": {"point": "M", "segment": ["S", "A"]}, "quote": q_mid},
        ],
        "derived_sections": [
            {
                "section_id": "sec",
                "plane_name": "P",
                "target_solid_id": "pyr",
                "plane_kind": "through_point_perpendicular_line",
                "through_point": "M",
                "perpendicular_line": ["S", "A"],
                "stated_intersections": [],
                "quote": q_sec,
            }
        ],
        "simulation_goals": [{"goal_id": "draw", "kind": "construct_plane_section", "target_section_id": "sec", "quote": q_sec}],
        "math_goals": [{"goal_id": "q", "kind": "measurement", "goal_type": "area", "target": {"section_id": "sec"}, "quote": q_area}],
    }
    geometry = {
        "solid_type": "pyramid",
        "apex": "S",
        "base": ["A", "B", "C", "D"],
        "points": {"A": ["0", "0", "0"], "B": ["4", "0", "0"], "C": ["4", "4", "0"], "D": ["0", "4", "0"], "S": ["0", "0", "4"], "M": ["0", "0", "2"]},
        "point": "M",
        "plane_relation": "perpendicular",
        "line": ["S", "A"],
    }
    return {
        "id": "pyramid-perpendicular-line-plane-only",
        "group": "positive",
        "family": "pyramid_perpendicular",
        "mode": "both",
        "payload": payload,
        "geometry": geometry,
        "expected_route_status": "SERVED",
        "expected_adapter4_status": "SERVED",
        "expected_codes": [],
        "expected_certificate_category": "ENGINE_DERIVED_SECTION",
    }


def _pyramid_two_lines_positive() -> dict:
    decl = "Cho hình chóp S.ABCD."
    q_base = "Đáy ABCD là hình vuông cạnh 2."
    q_perp = "SA vuông góc với mặt phẳng (ABCD)."
    q_sa = "SA = 3."
    q_mid = "Gọi M là trung điểm của SB."
    defn = "Dựng mặt phẳng (P) đi qua M và song song với AB và SD."
    q_sec = "Xác định thiết diện của hình chóp S.ABCD với (P)."
    q_area = "Tính diện tích thiết diện của hình chóp S.ABCD với (P)."
    text = " ".join([decl, q_base, q_perp, q_sa, q_mid, defn, q_sec, q_area])
    payload = {
        "schema_version": "typed-fact-next/2",
        "problem_text": text,
        "length_unit": "1",
        "solids": [{"solid_id": "pyr", "solid_type": "pyramid", "notation": "S.ABCD", "quote": decl}],
        "premises": [
            {"kind": "base_is_square", "args": {"vertices": ["A", "B", "C", "D"], "side": "2"}, "quote": q_base},
            {"kind": "line_perp_plane", "args": {"line": ["S", "A"], "plane": ["A", "B", "C", "D"]}, "quote": q_perp},
            {"kind": "segment_length", "args": {"segment": ["S", "A"], "value": "3"}, "quote": q_sa},
            {"kind": "midpoint", "args": {"point": "M", "segment": ["S", "B"]}, "quote": q_mid},
        ],
        "derived_sections": [
            {
                "section_id": "sec",
                "plane_name": "P",
                "target_solid_id": "pyr",
                "plane_kind": "through_point_parallel_two_lines",
                "through_point": "M",
                "parallel_line_a": ["A", "B"],
                "parallel_line_b": ["S", "D"],
                "stated_intersections": [],
                "quote": defn,
            }
        ],
        "simulation_goals": [{"goal_id": "draw", "kind": "construct_plane_section", "target_section_id": "sec", "quote": q_sec}],
        "math_goals": [{"goal_id": "q", "kind": "measurement", "goal_type": "area", "target": {"section_id": "sec"}, "quote": q_area}],
    }
    geometry = {
        "solid_type": "pyramid",
        "apex": "S",
        "base": ["A", "B", "C", "D"],
        "points": {"A": ["0", "0", "0"], "B": ["2", "0", "0"], "C": ["2", "2", "0"], "D": ["0", "2", "0"], "S": ["0", "0", "3"], "M": ["1", "0", "3/2"]},
        "point": "M",
        "plane_relation": "parallel_two_lines",
        "lines": [["A", "B"], ["S", "D"]],
    }
    return {
        "id": "pyramid-parallel-two-lines-plane-only",
        "group": "positive",
        "family": "pyramid_two_lines",
        "mode": "both",
        "payload": payload,
        "geometry": geometry,
        "expected_route_status": "SERVED",
        "expected_adapter4_status": "SERVED",
        "expected_codes": [],
        "expected_certificate_category": "ENGINE_DERIVED_SECTION",
    }


def _category_a_preserved_positive() -> dict:
    decl = "Cho hình chóp S.ABC."
    q_base = "Đáy ABC là tam giác đều cạnh a."
    q_perp = "SA vuông góc với mặt phẳng (ABC)."
    q_sa = "SA = a."
    q_mid = "Gọi M là trung điểm của SA."
    q_sec = "Mặt phẳng (α) qua M và song song với (ABC) cắt SB, SC lần lượt tại N, P."
    q_goal = "Dựng thiết diện của hình chóp S.ABC bởi (α) và khối chóp S.MNP."
    q_ratio = "Tính tỉ số thể tích của khối chóp S.MNP và khối chóp S.ABC."
    text = " ".join([decl, q_base, q_perp, q_sa, q_mid, q_sec, q_goal, q_ratio])
    payload = {
        "schema_version": "typed-fact-next/2",
        "problem_text": text,
        "length_unit": "a",
        "solids": [{"solid_id": "pyr", "solid_type": "pyramid", "notation": "S.ABC", "quote": decl}],
        "premises": [
            {"kind": "base_is_equilateral_triangle", "args": {"vertices": ["A", "B", "C"], "side": "a"}, "quote": q_base},
            {"kind": "line_perp_plane", "args": {"line": ["S", "A"], "plane": ["A", "B", "C"]}, "quote": q_perp},
            {"kind": "segment_length", "args": {"segment": ["S", "A"], "value": "a"}, "quote": q_sa},
            {"kind": "point_is_midpoint", "args": {"point": "M", "segment": ["S", "A"]}, "quote": q_mid},
        ],
        "derived_sections": [
            {
                "section_id": "sec",
                "plane_name": "α",
                "target_solid_id": "pyr",
                "plane_kind": "through_point_parallel_plane",
                "through_point": "M",
                "parallel_plane": ["A", "B", "C"],
                "stated_intersections": [
                    {"edge": ["S", "B"], "point": "N", "quote": "cắt SB, SC lần lượt tại N, P"},
                    {"edge": ["S", "C"], "point": "P", "quote": "cắt SB, SC lần lượt tại N, P"},
                ],
                "quote": q_sec,
            }
        ],
        "simulation_goals": [
            {"goal_id": "g_sec", "kind": "construct_plane_section", "target_section_id": "sec", "quote": q_goal},
            {"goal_id": "g_sub", "kind": "construct_derived_solid", "derived_solid_id": "sub", "target_section_id": "sec", "apex_ref": "S", "parent_solid_id": "pyr", "quote": q_goal},
        ],
        "math_goals": [
            {"goal_id": "g_ratio", "kind": "volume_ratio", "numerator_solid_id": "sub", "denominator_solid_id": "pyr", "quote": q_ratio}
        ],
    }
    return {
        "id": "pyramid-category-a-stated-cuts-preserved",
        "group": "positive_category_a",
        "family": "pyramid_category_a",
        "mode": "ratio",
        "payload": payload,
        "geometry": None,
        "expected_route_status": "SERVED",
        "expected_adapter4_status": "SERVED",
        "expected_codes": [],
        "expected_certificate_category": "CATEGORY_A_DINH_CAT_CANH",
    }


def build_cases() -> list[dict]:
    oracle_mod = _load_oracle()
    rows = [
        _prism_positive("right-base"),
        _prism_positive("right-top", line=("A'", "B'")),
        _prism_positive("right-lateral", line=("A", "A'")),
        _prism_positive("right-diagonal", line=("B", "C'")),
        _prism_positive("cuboid-base", family="cuboid"),
        _prism_positive("cube-diagonal", family="cube", dims=(4, 4, 4), line=("A", "C'")),
        _prism_positive("oblique-base", family="oblique"),
        _prism_positive("oblique-diagonal", family="oblique", line=("A", "C'")),
        _prism_positive("renamed-changed-reversed", dims=(3, 4, 5), labels="DEF", line=("C'", "B"), reverse=True),
        _prism_positive("symbolic-top", line=("B'", "A'"), symbolic=True),
        _prism_positive("right-base-section-only", mode="section_only"),
        _prism_positive("right-base-area-only", mode="area_only"),
        _prism_parallel_base_positive(),
        _pyramid_parallel_base_positive("pyramid-parallel-base-plane-only", mode="both"),
        _pyramid_parallel_base_positive("pyramid-parallel-base-section-only", mode="section_only"),
        _pyramid_perpendicular_line_positive(),
        _pyramid_two_lines_positive(),
        _category_a_preserved_positive(),
    ]
    for r in rows:
        if r["geometry"] is not None:
            res = oracle_mod.compute_section_oracle(r["geometry"])
            assert res["interior_cut"] and F(res["area_squared"]) > 0, r["id"]
            r["expected_area_squared"] = res["area_squared"]
            r["expected_vertex_count"] = res["vertex_count"]
        else:
            r["expected_area_squared"] = None
            r["expected_vertex_count"] = 3

    # ── Source / Route-level Negative Cases (§5) ──
    def add_neg(cid: str, neg_class: str, codes: list[str], mutator):
        base = deepcopy(rows[0])
        mutator(base["payload"])
        rows.append({
            "id": cid,
            "group": "negative_route",
            "negative_class": neg_class,
            "family": "negative",
            "mode": "negative",
            "payload": base["payload"],
            "geometry": None,
            "expected_area_squared": None,
            "expected_vertex_count": None,
            "expected_route_status": "REFUSED",
            "expected_adapter4_status": "REFUSED",
            "expected_codes": codes,
        })

    add_neg(
        "neg-wrong-solid-identity",
        "wrong_solid_identity",
        ["INVALID_TYPED_FACT_NEXT", "UNKNOWN_SOLID_ID", "UNKNOWN_SOLID"],
        lambda p: p["derived_sections"][0].update(target_solid_id="nonexistent_solid"),
    )

    def _contradict_kind(p):
        old = "lăng trụ đứng ABC.A'B'C'"
        new = "hình lập phương ABC.A'B'C'"
        p["problem_text"] = p["problem_text"].replace(old, new)
        p["solids"][0]["quote"] = p["solids"][0]["quote"].replace(old, new)
        p["premises"][0]["quote"] = p["premises"][0]["quote"].replace(old, new)
        p["derived_sections"][0]["quote"] = p["derived_sections"][0]["quote"].replace(old, new)
        p["simulation_goals"][0]["quote"] = p["simulation_goals"][0]["quote"].replace(old, new)
        p["math_goals"][0]["quote"] = p["math_goals"][0]["quote"].replace(old, new)

    add_neg(
        "neg-source-kind-contradiction",
        "source_kind_contradiction",
        ["SOURCE_OBJECT_MISMATCH"],
        _contradict_kind,
    )

    def _unverified_plane(p):
        p["problem_text"] = p["problem_text"].replace("vuông góc với AB", "vuông góc với AC")
        p["derived_sections"][0]["quote"] = p["derived_sections"][0]["quote"].replace("vuông góc với AB", "vuông góc với AC")
        p["simulation_goals"][0]["quote"] = p["simulation_goals"][0]["quote"].replace("vuông góc với AB", "vuông góc với AC")
        p["math_goals"][0]["quote"] = p["math_goals"][0]["quote"].replace("vuông góc với AB", "vuông góc với AC")

    add_neg(
        "neg-unverified-plane",
        "unverified_plane",
        ["SOURCE_OBJECT_MISMATCH"],
        _unverified_plane,
    )

    def _missing_dep(p):
        p["problem_text"] = p["problem_text"].replace("AA' = 12. ", "")
        p["premises"] = [pr for pr in p["premises"] if pr.get("args", {}).get("segment") != ["A", "A'"]]

    add_neg(
        "neg-missing-geometric-dependency",
        "missing_geometric_dependency",
        ["MISSING_DIMENSION"],
        _missing_dep,
    )

    def _boundary_face(p):
        old = "đi qua M và vuông góc với AB"
        new = "đi qua A và vuông góc với AB"
        p["problem_text"] = p["problem_text"].replace(old, new)
        p["derived_sections"][0].update(through_point="A", quote=p["derived_sections"][0]["quote"].replace(old, new))
        p["simulation_goals"][0]["quote"] = p["simulation_goals"][0]["quote"].replace(old, new)
        p["math_goals"][0]["quote"] = p["math_goals"][0]["quote"].replace(old, new)

    add_neg(
        "neg-degenerate-section-boundary-face",
        "degenerate_section",
        ["SECTION_PLANE_IS_FACE"],
        _boundary_face,
    )

    def _vertex_touch(p):
        old = "đi qua M và vuông góc với AB"
        new = "đi qua C' và vuông góc với AC'"
        p["problem_text"] = p["problem_text"].replace(old, new)
        p["derived_sections"][0].update(
            through_point="C'",
            perpendicular_line=["A", "C'"],
            quote=p["derived_sections"][0]["quote"].replace(old, new),
        )
        p["simulation_goals"][0]["quote"] = p["simulation_goals"][0]["quote"].replace(old, new)
        p["math_goals"][0]["quote"] = p["math_goals"][0]["quote"].replace(old, new)

    add_neg(
        "neg-degenerate-section-vertex-touch",
        "degenerate_section",
        ["PLANE_TOUCHES_VERTEX", "PLANE_DOES_NOT_CUT"],
        _vertex_touch,
    )

    add_neg(
        "neg-unsupported-topology-curved",
        "unsupported_topology",
        ["BRIDGE_UNSUPPORTED_CURVED", "INVALID_SOLID_NOTATION", "INVALID_TYPED_FACT_NEXT"],
        lambda p: p["solids"][0].update(solid_type="cylinder"),
    )

    # ── Adapter /4 Certificate Tamper Cases (§5) ──
    tamper_specs = [
        ("tamper-forged-certificate", "malformed_or_forged_certificate", ["PREVIEW_RESULT_INVALID"]),
        ("tamper-mismatched-edge-and-vertex", "mismatched_edge_and_vertex", ["PREVIEW_RESULT_INVALID"]),
        ("tamper-wrong-intersection-ordering", "wrong_intersection_ordering", ["PREVIEW_RESULT_INVALID"]),
        ("tamper-duplicated-or-missing-vertex", "duplicated_or_missing_section_vertex", ["PREVIEW_RESULT_INVALID"]),
        ("tamper-degenerate-collinear-polygon", "degenerate_section", ["PREVIEW_RESULT_INVALID"]),
        ("tamper-exact-area", "tampered_exact_area", ["PREVIEW_RESULT_INVALID", "RESULT_BINDING_UNVERIFIED"]),
        ("tamper-unknown-certificate-version", "unknown_certificate_version", ["PREVIEW_IDENTITY_CHANGED", "PREVIEW_RESULT_INVALID"]),
        ("tamper-unsupported-topology-diagonal-edge", "unsupported_topology", ["PREVIEW_RESULT_INVALID"]),
        ("tamper-inconsistent-provenance", "inconsistent_provenance", ["PREVIEW_RESULT_INVALID"]),
        ("tamper-certificate-reuse-across-plane-or-solid", "certificate_reuse", ["PREVIEW_RESULT_INVALID"]),
        ("tamper-wrong-solid-identity", "wrong_solid_identity", ["PREVIEW_RESULT_INVALID"]),
    ]
    for tid, tclass, codes in tamper_specs:
        rows.append({
            "id": tid,
            "group": "negative_tamper",
            "negative_class": tclass,
            "tamper_kind": tid,
            "family": "tamper",
            "mode": "tamper",
            "payload": deepcopy(rows[0]["payload"]),
            "secondary_payload": deepcopy(rows[3]["payload"]) if tid == "tamper-certificate-reuse-across-plane-or-solid" else None,
            "geometry": None,
            "expected_area_squared": None,
            "expected_vertex_count": None,
            "expected_route_status": "SERVED",
            "expected_adapter4_status": "REFUSED",
            "expected_codes": codes,
        })
    return rows


if __name__ == "__main__":
    run = Path(__file__).resolve().parents[1]
    dev_path = run / "inputs/development.json"
    orc_path = run / "inputs/oracle.json"
    if dev_path.exists() or orc_path.exists():
        raise SystemExit("Refusing to overwrite registered inputs.")
    cases = build_cases()
    oracle_mod = _load_oracle()
    oracles = {
        c["id"]: oracle_mod.compute_section_oracle(c["geometry"])
        for c in cases
        if c["geometry"] is not None
    }
    dev_path.parent.mkdir(parents=True, exist_ok=True)
    dev_path.write_text(
        json.dumps(
            {
                "classification": "AUTHORED_DEVELOPMENT_AND_TAMPER_NOT_HOLDOUT",
                "live_calls": 0,
                "cases": cases,
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    orc_path.write_text(
        json.dumps(oracles, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"Registered {len(cases)} cases and {len(oracles)} oracle sections.")
