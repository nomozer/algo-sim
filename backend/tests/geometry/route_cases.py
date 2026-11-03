# -*- coding: utf-8 -*-
"""W14 — ca dùng chung (0 lượt gọi) cho test dựng hình theo lớp, cổng giả định và census.

Không phải file test (không có tiền tố `test_`): test và phép đo cùng import từ đây
để một ca chỉ được viết MỘT lần. Mọi hợp đồng đi qua biên đóng băng của sản phẩm
(`build_request_contract(..., problem_text=...)`), trừ ca CỐ Ý thiếu đề.
"""
from __future__ import annotations

import copy
import json
from fractions import Fraction
from pathlib import Path
from typing import Any, Callable

from app.simulation.semantic_program.analyze_contract import build_request_contract
from app.simulation.semantic_program.contract import SemanticProgramSpec
from app.simulation.semantic_program.interpreter import SemanticProgramInterpreter
from app.simulation.semantic_program.route import verify_and_compile
from tests.geometry.scene3d_test_helper import _dung_scene3d

_PROGRAMS: dict[str, dict] = json.loads(
    (Path(__file__).with_name("route_cases_programs.json")).read_text(encoding="utf-8")
)

CHOP_TAM_GIAC_TEXT = (
    "Cho hình chóp S.ABC có đáy ABC là tam giác vuông tại A, AB = 3, AC = 4. "
    "Cạnh bên SA vuông góc với đáy, SA = 5. Tính thể tích khối chóp S.ABC."
)


def hop_dong(text: str, payload: dict):
    return build_request_contract(payload, problem_text=text, domain="hinh_hoc")


def chop_tam_giac_payload() -> dict:
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
        "obligations": [{"kind": "volume", "container": "khoi_chop", "witness": "the_tich_khoi"}],
    }


def chop_tam_giac():
    return CHOP_TAM_GIAC_TEXT, hop_dong(CHOP_TAM_GIAC_TEXT, chop_tam_giac_payload())


def lang_tru_tam_giac():
    text = (
        "Cho hình lăng trụ đứng ABC.DEF có đáy ABC là tam giác vuông tại A, "
        "AB = 3, AC = 4. Cạnh bên AD = 5. Tính thể tích khối lăng trụ ABC.DEF."
    )
    payload = {
        "input_facts": [
            {"id": "fact_len_AB", "kind": "float", "label": "AB", "value": ["3"]},
            {"id": "fact_len_AC", "kind": "float", "label": "AC", "value": ["4"]},
            {"id": "fact_len_AD", "kind": "float", "label": "AD", "value": ["5"]},
        ],
        "geometric_relations": [
            {"kind": "perpendicular_lines", "line": ["A", "B"], "other_line": ["A", "C"],
             "source_fact_id": "fact_perp_base", "model_assumption": False},
            {"kind": "perpendicular_line_plane", "line": ["A", "D"], "plane": ["A", "B", "C"],
             "source_fact_id": "fact_perp_lateral", "model_assumption": False},
        ],
        "obligations": [{"kind": "volume", "container": "solid_ABCDEF", "witness": "the_tich_lang_tru"}],
        "solid_topology": {
            "solid_kind": "prism",
            "base_cycle": ["A", "B", "C"],
            "top_cycle": ["D", "E", "F"],
            "correspondence": [["A", "D"], ["B", "E"], ["C", "F"]],
        },
    }
    return text, hop_dong(text, payload)


def chop_chu_nhat():
    text = (
        "Cho hình chóp S.ABCD có đáy ABCD là hình chữ nhật, AB = 3, AD = 4. "
        "Cạnh bên SA vuông góc với mặt phẳng đáy, SA = 6. Tính thể tích khối chóp S.ABCD."
    )
    payload = {
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
        "solid_topology": {"solid_kind": "pyramid", "apex": "S",
                           "base_cycle": ["A", "B", "C", "D"], "base_shape": "rectangle"},
    }
    return text, hop_dong(text, payload)


CHOP_VUONG_TEXT = (
    "Cho hình chóp S.ABCD có đáy ABCD là hình vuông cạnh 3. "
    "Cạnh bên SA vuông góc với mặt phẳng đáy, SA = 6. Tính thể tích khối chóp S.ABCD."
)


def chop_vuong():
    payload = {
        "input_facts": [
            {"id": "fact_len_AB", "kind": "float", "label": "AB", "value": ["3"]},
            {"id": "fact_len_SA", "kind": "float", "label": "SA", "value": ["6"]},
        ],
        "geometric_relations": [
            {"kind": "perpendicular_lines", "line": ["A", "B"], "other_line": ["A", "D"],
             "source_fact_id": "fact_perp_base", "model_assumption": False},
            {"kind": "perpendicular_line_plane", "line": ["S", "A"], "plane": ["A", "B", "C"],
             "source_fact_id": "fact_perp_lateral", "model_assumption": False},
        ],
        "obligations": [{"kind": "volume", "container": "khoi_chop", "witness": "v"}],
        "solid_topology": {"solid_kind": "pyramid", "apex": "S",
                           "base_cycle": ["A", "B", "C", "D"], "base_shape": "square"},
    }
    return CHOP_VUONG_TEXT, hop_dong(CHOP_VUONG_TEXT, payload)


def _square_prism_control_payload() -> tuple[str, dict]:
    text = (
        "Cho hình lăng trụ đứng có đáy là hình vuông cạnh 3, chiều cao bằng 7. "
        "Tính thể tích khối lăng trụ đứng đó."
    )
    payload = {
        "input_facts": [
            {"id": "fact_base_edge", "kind": "float", "label": "AB", "value": ["3"]},
            {"id": "fact_height", "kind": "float", "label": "AA'", "value": ["7"]},
        ],
        "geometric_relations": [
            {"kind": "perpendicular_lines", "line": ["A", "B"], "other_line": ["A", "D"],
             "source_fact_id": "fact_perp_base", "model_assumption": False},
            {"kind": "perpendicular_line_plane", "line": ["A'", "A"], "plane": ["A", "B", "D"],
             "source_fact_id": "fact_perp_lat", "model_assumption": False},
        ],
        "obligations": [{"kind": "volume", "container": "khoi_lang_tru", "witness": "V"}],
        "solid_topology": {
            "solid_kind": "prism",
            "base_cycle": ["A", "B", "C", "D"],
            "top_cycle": ["A'", "B'", "C'", "D'"],
            "correspondence": [["A", "A'"], ["B", "B'"], ["C", "C'"], ["D", "D'"]],
            "base_shape": "square",
            "lateral_structure": "right",
            "solid_subkind": "right_square_prism",
            "source_grounding": "hình lăng trụ đứng có đáy là hình vuông",
        },
    }
    return text, payload


def _hop_chu_nhat_payload() -> tuple[str, dict]:
    text = (
        "Cho hình hộp chữ nhật ABCD.A'B'C'D' có AB = 3, AD = 4, AA' = 5. "
        "Tính thể tích khối hộp chữ nhật ABCD.A'B'C'D'."
    )
    payload = {
        "input_facts": [
            {"id": "fact_ab", "kind": "float", "label": "AB", "value": ["3"]},
            {"id": "fact_ad", "kind": "float", "label": "AD", "value": ["4"]},
            {"id": "fact_aa_prime", "kind": "float", "label": "AA'", "value": ["5"]},
        ],
        "geometric_relations": [
            {"kind": "perpendicular_lines", "line": ["A", "B"], "other_line": ["A", "D"],
             "source_fact_id": "fact_perp_base", "model_assumption": False},
            {"kind": "perpendicular_line_plane", "line": ["A'", "A"], "plane": ["A", "B", "D"],
             "source_fact_id": "fact_perp_lat", "model_assumption": False},
        ],
        "obligations": [{"kind": "volume", "container": "khoi_hop", "witness": "V"}],
        "solid_topology": {
            "solid_kind": "prism",
            "base_cycle": ["A", "B", "C", "D"],
            "top_cycle": ["A'", "B'", "C'", "D'"],
            "correspondence": [["A", "A'"], ["B", "B'"], ["C", "C'"], ["D", "D'"]],
            "base_shape": "rectangle",
            "lateral_structure": "right",
            "solid_subkind": "cuboid",
            "source_grounding": "hình hộp chữ nhật",
        },
    }
    return text, payload


def hop_chu_nhat():
    text, payload = _hop_chu_nhat_payload()
    return text, hop_dong(text, payload)


def _lap_phuong_payload() -> tuple[str, dict]:
    text = "Cho hình lập phương ABCD.A'B'C'D' có cạnh bằng 4. Tính thể tích của hình lập phương đó."
    payload = {
        "input_facts": [{"id": "fact_edge", "kind": "float", "label": "AB", "value": ["4"]}],
        "geometric_relations": [
            {"kind": "perpendicular_lines", "line": ["A", "B"], "other_line": ["A", "D"],
             "source_fact_id": "fact_perp_base", "model_assumption": False},
        ],
        "obligations": [{"kind": "volume", "container": "khoi_hop", "witness": "V"}],
        "solid_topology": {
            "solid_kind": "prism",
            "base_cycle": ["A", "B", "C", "D"],
            "top_cycle": ["A'", "B'", "C'", "D'"],
            "correspondence": [["A", "A'"], ["B", "B'"], ["C", "C'"], ["D", "D'"]],
            "base_shape": "square",
            "lateral_structure": "right",
            "solid_subkind": "cube",
            "source_grounding": "hình lập phương",
        },
    }
    return text, payload


def lap_phuong():
    text, payload = _lap_phuong_payload()
    return text, hop_dong(text, payload)


def lang_tru_day_vuong():
    text, payload = _square_prism_control_payload()
    return text, hop_dong(text, payload)


HO: dict[str, Callable[[], tuple[str, Any]]] = {
    "chop_tam_giac": chop_tam_giac,
    "lang_tru_tam_giac": lang_tru_tam_giac,
    "chop_chu_nhat": chop_chu_nhat,
    "hop_chu_nhat": hop_chu_nhat,
    "lap_phuong": lap_phuong,
    "lang_tru_day_vuong": lang_tru_day_vuong,
}
LOP = {
    "chop_tam_giac": "PYRAMID_LIKE",
    "chop_chu_nhat": "PYRAMID_LIKE",
    "lang_tru_tam_giac": "PRISM_LIKE",
    "hop_chu_nhat": "PRISM_LIKE",
    "lap_phuong": "PRISM_LIKE",
    "lang_tru_day_vuong": "PRISM_LIKE",
}

_TEXT_TO_KEY = {
    CHOP_TAM_GIAC_TEXT: "chop_tam_giac",
    CHOP_VUONG_TEXT: "chop_vuong",
}


def chuong_trinh(contract) -> dict:
    """Chương trình tất định cho hợp đồng chuẩn (0-LLM fixture)."""
    pt = getattr(contract, "problem_text", "") or ""
    if pt in _TEXT_TO_KEY:
        return copy.deepcopy(_PROGRAMS[_TEXT_TO_KEY[pt]])
    for key, fn in HO.items():
        if fn()[0] == pt:
            return copy.deepcopy(_PROGRAMS[key])
    if "cạnh 4, chiều cao bằng 4" in pt:
        return copy.deepcopy(_PROGRAMS["square_prism_4x4"])
    rels = list(getattr(contract, "geometric_relations", ()) or ())
    lp = next((r for r in rels if r.kind == "perpendicular_line_plane" and len(r.line) == 2 and len(r.plane) == 3), None)
    ll = next((r for r in rels if r.kind == "perpendicular_lines" and len(r.line) == 2 and len(r.other_line) == 2), None)
    if lp is not None and ll is not None:
        common = set(ll.line) & set(ll.other_line)
        if len(common) == 1 and common <= set(lp.line) and common <= set(lp.plane):
            foot = next(iter(common))
            apex = next(v for v in lp.line if v != foot)
            adj1 = next(v for v in ll.line if v != foot)
            adj2 = next(v for v in ll.other_line if v != foot)
            vmap = {"A": foot, "B": adj1, "C": adj2, "S": apex}
            facts_by_pair: dict[frozenset[str], Any] = {}
            for f in getattr(contract, "input_facts", ()) or ():
                lbl = str(getattr(f, "label", "") or "")
                if len(lbl) == 2:
                    facts_by_pair[frozenset((lbl[0], lbl[1]))] = f
            f_ab = facts_by_pair.get(frozenset((foot, adj1)))
            f_ac = facts_by_pair.get(frozenset((foot, adj2)))
            f_sa = facts_by_pair.get(frozenset((apex, foot)))
            if f_ab and f_ac and f_sa:
                prog = copy.deepcopy(_PROGRAMS["chop_tam_giac"])
                name_map = {
                    **vmap,
                    "AB_length": f"{foot}{adj1}_length",
                    "AC_length": f"{foot}{adj2}_length",
                    "SA_length": f"{apex}{foot}_length",
                    "day_ABC": f"day_{foot}{adj1}{adj2}",
                    "dien_tich_day_ABC": f"dien_tich_day_{foot}{adj1}{adj2}",
                }
                fact_meta = {
                    "AB_length": (f_ab.fact_id, str(f_ab.values[0])),
                    "AC_length": (f_ac.fact_id, str(f_ac.values[0])),
                    "SA_length": (f_sa.fact_id, str(f_sa.values[0])),
                }
                for d in prog["memory_declarations"]:
                    old_n = d["name"]
                    if old_n in fact_meta:
                        d["source_fact_id"], d["initial_value"] = fact_meta[old_n]
                    d["name"] = name_map.get(old_n, old_n)

                def _walk(node, key=None):
                    if isinstance(node, str):
                        if key in ("kind", "quantity", "op", "title", "label"):
                            return node
                        return name_map.get(node, node)
                    if isinstance(node, list):
                        return [_walk(x, key) for x in node]
                    if isinstance(node, dict):
                        return {k: _walk(v, k) for k, v in node.items()}
                    return node

                prog["statements"] = _walk(prog["statements"])
                for s in prog["statements"]:
                    if s.get("kind") == "declare_point":
                        if s["target_var"] == adj1:
                            s["at"] = [str(f_ab.values[0]), "0", "0"]
                        elif s["target_var"] == adj2:
                            s["at"] = ["0", str(f_ac.values[0]), "0"]
                        elif s["target_var"] == apex:
                            s["at"] = ["0", "0", str(f_sa.values[0])]
                return prog
    raise KeyError(f"Unmapped fixture contract text: {pt!r}")


def spec_cua(program: dict) -> SemanticProgramSpec:
    return SemanticProgramSpec.model_validate(program)


def chay(contract, program: dict | None = None, **kw):
    sp = spec_cua(program if program is not None else chuong_trinh(contract))
    out = verify_and_compile(contract, sp, **kw)
    return sp, out, (_dung_scene3d(sp, contract) if out.executable else None)


def bo_nho_cuoi(sp: SemanticProgramSpec) -> dict:
    return SemanticProgramInterpreter().execute(sp).final_memory


def dinh_cua(o: dict) -> frozenset:
    return frozenset(o.get("vertex_ids") or o.get("endpoint_ids") or ())


def vat_theo_dinh(scene: dict, loai: str, dinh) -> list[dict]:
    want = frozenset(dinh)
    return [o for o in scene["objects"] if o["type"] == loai and dinh_cua(o) == want]


def buoc_hien_dau(scene: dict, oid: str) -> int | None:
    for k, s in enumerate(scene["formation"]["steps"]):
        if oid in s["visible_ids"]:
            return k
    return None


def khoi(scene: dict) -> dict:
    solids = [o for o in scene["objects"] if o["type"] == "solid"]
    assert len(solids) == 1, [o["id"] for o in solids]
    return solids[0]


def thu_tu_vai_tro(scene: dict, vai: list[str]) -> list[int]:
    steps = scene["formation"]["steps"]
    return [next((k for k, s in enumerate(steps) if r in s.get("formation_roles", [])), -1)
            for r in vai]


def _w12():
    from tests.geometry import test_source_grounding_closure as T

    return T


def kenh_gia_dinh(channel: str) -> tuple[Any, dict]:
    T = _w12()
    raw = copy.deepcopy(T._program_with_height_5())
    if channel != "given_length":
        raw["memory_declarations"] = [d for d in raw["memory_declarations"]
                                      if d["name"] != "AD_length"]
    if channel == "model_assumption":
        for d in raw["memory_declarations"]:
            if d.get("provenance") == "LAYOUT_DERIVED":
                d.pop("provenance")
                d["model_assumption"] = f"Đặt {d['name']} trong hệ trục tiện dựng"
        raw["statements"] = [dict(s, model_assumption=f"Đặt {s['target_var']} trong hệ trục")
                             if s["kind"] == "declare_point" else s for s in raw["statements"]]
    return T._contract(T.PRISM_WITHOUT_AD, T._prism_payload()), raw


def _xoay(p):
    x, y, z = (Fraction(str(c)) for c in p)
    m = ((-1, -2, -2), (-2, -1, 2), (-2, 2, -1))
    return [str(sum(Fraction(a) * v for a, v in zip(row, (x, y, z))) / 3) for row in m]


def doi_toa_do(raw: dict, f: Callable) -> dict:
    raw = copy.deepcopy(raw)
    for s in raw["statements"]:
        if s.get("kind") == "declare_point" and "at" in s:
            s["at"] = f(s["at"])
    for d in raw["memory_declarations"]:
        if d.get("type") == "point3" and isinstance(d.get("initial_value"), list):
            d["initial_value"] = f(d["initial_value"])
    return raw


def ca_xy_length_gia_dinh() -> tuple[Any, dict]:
    contract, raw = kenh_gia_dinh("layout_derived")
    raw["memory_declarations"].append(
        {"name": "AD_length", "type": "float", "provenance": "LAYOUT_DERIVED",
         "initial_value": "5"})
    return contract, raw


def ca_xoay_thieu_AD() -> tuple[Any, dict]:
    contract, raw = kenh_gia_dinh("layout_derived")
    return contract, doi_toa_do(raw, _xoay)


LANG_TRU_DAY_VUONG_THIEU_CAO = (
    "Cho hình lăng trụ đứng ABCD.A'B'C'D' có đáy là hình vuông cạnh 4. "
    "Tính thể tích khối lăng trụ đứng đó."
)


def ca_canh_khac_che_chieu_cao() -> tuple[Any, dict]:
    _text, payload = _square_prism_control_payload()
    raw = copy.deepcopy(_PROGRAMS["square_prism_4x4"])
    cao = {"AA_prime_length"}
    raw["memory_declarations"] = [d for d in raw["memory_declarations"] if d["name"] not in cao]
    thieu = copy.deepcopy(payload)
    thieu["input_facts"] = [dict(f, value=["4"]) for f in thieu["input_facts"] if f["label"] == "AB"]
    return hop_dong(LANG_TRU_DAY_VUONG_THIEU_CAO, thieu), raw


LANG_TRU_XIEN_TEXT = (
    "Cho hình lăng trụ xiên ABC.DEF có đáy ABC là tam giác vuông tại A, AB = 3, AC = 4. "
    "Tính thể tích khối lăng trụ ABC.DEF."
)


def _diem_gia_dinh(ten: str, xyz: list) -> dict:
    return {"name": ten, "type": "point3", "initial_value": [str(c) for c in xyz],
            "model_assumption": "Đặt điểm trong hệ trục tiện dựng"}


def ca_lang_tru_xien() -> tuple[Any, dict]:
    payload = {
        "input_facts": [
            {"id": "fact_len_AB", "kind": "float", "label": "AB", "value": ["3"]},
            {"id": "fact_len_AC", "kind": "float", "label": "AC", "value": ["4"]},
        ],
        "geometric_relations": [
            {"kind": "perpendicular_lines", "line": ["A", "B"], "other_line": ["A", "C"],
             "source_fact_id": "fact_perp_base", "model_assumption": False},
        ],
        "obligations": [{"kind": "volume", "container": "lang_tru", "witness": "V"}],
    }
    pts = {"A": [0, 0, 0], "B": [3, 0, 0], "C": [0, 4, 0],
           "D": [1, 1, 5], "E": [4, 1, 5], "F": [1, 5, 5]}
    raw = {
        "spec_version": "1.0",
        "title": "Thể tích lăng trụ xiên",
        "memory_declarations": [_diem_gia_dinh(k, v) for k, v in pts.items()] + [
            {"name": "day_ABC", "type": "polygon3"}, {"name": "lang_tru", "type": "solid"},
            {"name": "V", "type": "float"}],
        "statements": [
            {"kind": "construct_polygon", "target_var": "day_ABC", "vertices": ["A", "B", "C"]},
            {"kind": "construct_solid", "target_var": "lang_tru",
             "vertices": ["A", "B", "C", "D", "E", "F"],
             "faces": [["A", "B", "C"], ["D", "E", "F"], ["A", "B", "E", "D"],
                       ["B", "C", "F", "E"], ["C", "A", "D", "F"]]},
            {"kind": "assign", "target_var": "V",
             "expr": {"kind": "measure", "quantity": "volume", "of": "lang_tru"}},
        ],
    }
    return hop_dong(LANG_TRU_XIEN_TEXT, payload), raw


CHOP_CHAN_AN_TEXT = (
    "Cho hình chóp S.ABC có đáy ABC là tam giác vuông tại A, AB = 3, AC = 4, chiều cao "
    "bằng 5. Tính khoảng cách từ S đến đường thẳng BC."
)


def ca_chan_duong_cao_an() -> tuple[Any, dict]:
    payload = {
        "input_facts": [
            {"id": "fact_len_AB", "kind": "float", "label": "AB", "value": ["3"]},
            {"id": "fact_len_AC", "kind": "float", "label": "AC", "value": ["4"]},
        ],
        "geometric_relations": [
            {"kind": "perpendicular_lines", "line": ["A", "B"], "other_line": ["A", "C"],
             "source_fact_id": "fact_perp_base", "model_assumption": False},
        ],
        "obligations": [{"kind": "distance", "container": "S", "witness": "d",
                         "wrt": "BC"}],
    }
    pts = {"A": [0, 0, 0], "B": [3, 0, 0], "C": [0, 4, 0], "S": [1, 1, 5]}
    raw = {
        "spec_version": "1.0",
        "title": "Khoảng cách từ S đến BC",
        "memory_declarations": [_diem_gia_dinh(k, v) for k, v in pts.items()] + [
            {"name": "BC", "type": "line3"}, {"name": "d", "type": "float"}],
        "statements": [
            {"kind": "construct_line", "target_var": "BC", "through_a": "B", "through_b": "C"},
            {"kind": "assign", "target_var": "d",
             "expr": {"kind": "measure", "quantity": "distance", "of": "S", "wrt": "BC"}},
        ],
    }
    return hop_dong(CHOP_CHAN_AN_TEXT, payload), raw


def hop_dong_khong_de(contract):
    return contract.model_copy(update={"problem_text": ""})


def _p01_them(cau_them: str, nghia_vu_them: list[dict]) -> tuple[Any, dict]:
    T = _w12()
    payload = T._prism_payload()
    payload["obligations"] = payload["obligations"] + nghia_vu_them
    raw = copy.deepcopy(_PROGRAMS["lang_tru_tam_giac"])
    return hop_dong(T.PRISM_TEXT + cau_them, payload), raw


def ca_nhan_vo_huong_gia_dinh() -> tuple[Any, dict]:
    ct, raw = _p01_them(" Cho điểm M bất kỳ.", [])
    raw["memory_declarations"] += [_diem_gia_dinh("M", [1, 0, 0]),
                                   {"name": "k", "type": "float"}]
    cuoi = next(s for s in raw["statements"]
                if s["kind"] == "assign" and s["target_var"] == "the_tich_lang_tru")
    nguon = cuoi["expr"]["name"]
    i = raw["statements"].index(cuoi)
    raw["statements"].insert(i, {"kind": "assign", "target_var": "k",
                                 "expr": {"kind": "measure", "quantity": "distance",
                                          "of": "A", "wrt": "M"}})
    cuoi["expr"] = {"kind": "arith", "op": "*", "left": {"kind": "var", "name": nguon},
                    "right": {"kind": "var", "name": "k"}}
    return ct, raw


def ca_hai_dap_so_mot_phu_thuoc() -> tuple[Any, dict]:
    ct, raw = _p01_them(" Cho điểm M bất kỳ. Tính khoảng cách AM.",
                        [{"kind": "distance", "container": "A", "witness": "d_AM", "wrt": "M"}])
    raw["memory_declarations"] += [_diem_gia_dinh("M", [0, 0, 7]),
                                   {"name": "d_AM", "type": "float"}]
    raw["statements"].append({"kind": "assign", "target_var": "d_AM",
                              "expr": {"kind": "measure", "quantity": "distance",
                                       "of": "A", "wrt": "M"}})
    return ct, raw


def ca_hai_dap_so_mot_ngoai_pham_vi() -> tuple[Any, dict]:
    ct, raw = _p01_them(" Tính cos² của góc giữa AD và mặt phẳng (ABC).",
                        [{"kind": "angle_cos_sq", "container": "dt_AD", "witness": "g",
                          "wrt": "mp_ABC"}])
    raw["memory_declarations"] += [{"name": "dt_AD", "type": "line3"},
                                   {"name": "mp_ABC", "type": "plane3"},
                                   {"name": "g", "type": "float"}]
    raw["statements"] += [
        {"kind": "construct_line", "target_var": "dt_AD", "through_a": "A", "through_b": "D"},
        {"kind": "construct_plane", "target_var": "mp_ABC", "through": ["A", "B", "C"]},
        {"kind": "assign", "target_var": "g",
         "expr": {"kind": "measure", "quantity": "angle_cos_sq", "of": "dt_AD", "wrt": "mp_ABC"}},
    ]
    return ct, raw


GOLD_KHOI_DA_DIEN = ("p1_chop_thiet_dien_khoang_cach", "p2_chop_day_ngu_giac_lom")


def gold(case_id: str) -> tuple[str, Any, dict]:
    from scripts import replay_negative_boundaries as RNB

    raw = RNB.doc_raw_theo_thu_tu(case_id)
    text = RNB.doc_de_bai()[case_id]
    contract = hop_dong(text, json.loads(raw["semantic_analyze"][0]))
    return text, contract, json.loads(raw["semantic_program"][0])


def mau_offline_co_khoi() -> list[tuple[str, dict]]:
    from scripts import build_geometry_samples as B

    ra = []
    for sid, _nhom, fn in B.BAI_MAU:
        prog = fn()
        if any(s.get("kind") == "construct_solid" for s in prog["statements"]):
            ra.append((sid, prog))
    return ra


def nguon_khoi() -> list[tuple[str, SemanticProgramSpec]]:
    ra = [(f"ho:{ten}", spec_cua(chuong_trinh(f()[1]))) for ten, f in HO.items()]
    ra += [(f"gold:{cid}", spec_cua(gold(cid)[2])) for cid in GOLD_KHOI_DA_DIEN]
    ra += [(f"mau:{sid}", spec_cua(prog)) for sid, prog in mau_offline_co_khoi()]
    return ra
