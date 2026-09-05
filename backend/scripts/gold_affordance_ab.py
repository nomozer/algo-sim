# -*- coding: utf-8 -*-
"""Corpus validation v1 + GOLD PREFLIGHT cho `MODEL_FACING_OPERATION_AFFORDANCE_ALIGNMENT`.

**0 lượt gọi model.** Chạy TRƯỚC mọi lượt gọi provider.

Tám đề MỚI — không trùng `curved-section-discoverability-dev-v1`, khác cả ký
hiệu lẫn số liệu, để phép đo A/B không đo trúng một bộ đề mà thẻ B tình cờ hợp.

Bộ dựng gold dùng lại nguyên các helper của
`gold_section_discoverability.py`: hai corpus khác nhau nhưng **cùng một lối
dựng**, nên nếu lối ấy sai thì cả hai cùng sai — thà thế còn hơn hai bản dựng
tay trôi khỏi nhau.
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path
from typing import Any

GOC = Path(__file__).resolve().parents[1]
for p in (str(GOC), str(GOC / "scripts")):
    if p not in sys.path:
        sys.path.insert(0, p)

from gold_section_discoverability import (  # noqa: E402
    VB,
    _cau,
    _chia,
    _d,
    _diem,
    _do,
    _tron_xoay,
)

from app.simulation.semantic_program.contract import (  # noqa: E402
    SemanticProgramSpec,
)
from app.simulation.semantic_program.obligations import Obligation  # noqa: E402
from app.simulation.semantic_program.request_contract import (  # noqa: E402
    RequestContract,
)
from app.simulation.semantic_program.route import verify_and_compile  # noqa: E402

RA = GOC.parent / "docs" / "evaluation" / "geometry" / \
    "operation-affordance-ab-v1"
FK, FD = "f_kichthuoc", "f_diem"


CORPUS: list[dict[str, Any]] = [
    {
        "case_id": "e1", "family": "cylinder",
        "feature": "perpendicular_section_at_midpoint_radius",
        "problem_text":
            "Cho hình trụ có hai đáy là hai đường tròn tâm G và tâm H, bán "
            "kính đáy bằng 5 và GH bằng 14. Gọi L là một điểm nằm trên đường "
            "tròn đáy tâm G. Gọi N là trung điểm của đoạn GH. Mặt phẳng đi "
            "qua N và vuông góc với GH cắt hình trụ theo một đường tròn (u). "
            "Tính bán kính của đường tròn (u).",
        "expected_obligations": ["radius"],
        "expected_operator_class": "intersect_plane_curved",
        "expected_result_type": "circle3",
        "exact_expected_results": {"radius": "5"},
        "expected_boundary": None,
    },
    {
        "case_id": "e2", "family": "cylinder",
        "feature": "perpendicular_section_off_centre_area",
        "problem_text":
            "Một hình trụ có trục là đoạn thẳng XY, bán kính đáy bằng 11 và "
            "XY bằng 30. Điểm Z nằm trên đường tròn đáy tâm X. Lấy điểm V "
            "thuộc đoạn XY sao cho XV bằng 12. Mặt phẳng đi qua V và vuông "
            "góc với XY cắt hình trụ theo đường tròn (v). Tính diện tích của "
            "đường tròn (v).",
        "expected_obligations": ["area"],
        "expected_operator_class": "intersect_plane_curved",
        "expected_result_type": "circle3",
        "exact_expected_results": {"area": "121π"},
        "expected_boundary": None,
    },
    {
        "case_id": "e3", "family": "cone",
        "feature": "similar_ratio_measured_from_base",
        "problem_text":
            "Cho hình nón có đỉnh F và tâm đáy E, bán kính đáy bằng 12, chiều "
            "cao FE bằng 16. Gọi R là một điểm trên đường tròn đáy. Một mặt "
            "phẳng vuông góc với trục FE cắt trục tại điểm M sao cho EM bằng "
            "4, tính từ tâm đáy E. Mặt phẳng đó cắt hình nón theo đường tròn "
            "(m). Tính bán kính của đường tròn (m).",
        "expected_obligations": ["radius"],
        "expected_operator_class": "intersect_plane_curved",
        "expected_result_type": "circle3",
        # r' = 12·(16−4)/16 = 9. Bộ ba 12–16–20.
        "exact_expected_results": {"radius": "9"},
        "expected_boundary": None,
    },
    {
        "case_id": "e4", "family": "cone",
        "feature": "similar_ratio_measured_from_apex",
        "problem_text":
            "Hình nón có đỉnh P và tâm đáy Q, bán kính đáy bằng 21, chiều cao "
            "PQ bằng 28. Gọi W là một điểm trên đường tròn đáy. Một mặt phẳng "
            "vuông góc với PQ cắt PQ tại điểm T sao cho PT bằng 20, tính từ "
            "đỉnh P. Mặt phẳng đó cắt hình nón theo đường tròn (t). Tính bán "
            "kính của đường tròn (t).",
        "expected_obligations": ["radius"],
        "expected_operator_class": "intersect_plane_curved",
        "expected_result_type": "circle3",
        # r' = 21·(20/28) = 15. Bộ ba 21–28–35.
        "exact_expected_results": {"radius": "15"},
        "expected_boundary": None,
    },
    {
        "case_id": "e5", "family": "ball",
        "feature": "plane_section_radius",
        "problem_text":
            "Cho mặt cầu tâm K có bán kính bằng 41. Gọi J là một điểm sao cho "
            "KJ bằng 9. Mặt phẳng đi qua J và vuông góc với KJ cắt mặt cầu "
            "theo một đường tròn (j). Tính bán kính của đường tròn (j).",
        "expected_obligations": ["radius"],
        "expected_operator_class": "intersect_plane_curved",
        "expected_result_type": "circle3",
        # 9–40–41.
        "exact_expected_results": {"radius": "40"},
        "expected_boundary": None,
    },
    {
        "case_id": "e6", "family": "ball",
        "feature": "plane_section_area",
        "problem_text":
            "Cho mặt cầu tâm D có bán kính bằng 29. Điểm C nằm sao cho DC "
            "bằng 21. Mặt phẳng đi qua C và vuông góc với DC cắt mặt cầu theo "
            "đường tròn (c). Tính diện tích của đường tròn (c).",
        "expected_obligations": ["area"],
        "expected_operator_class": "intersect_plane_curved",
        "expected_result_type": "circle3",
        # 20–21–29.
        "exact_expected_results": {"area": "400π"},
        "expected_boundary": None,
    },
    {
        "case_id": "e7", "family": "polyhedron",
        "feature": "control__construct_section_is_correct",
        "problem_text":
            "Cho hình lập phương MNPQ.M'N'P'Q' có cạnh bằng 6. Mặt phẳng đi "
            "qua ba điểm M, P và N' cắt hình lập phương theo một thiết diện. "
            "Tính diện tích của thiết diện đó.",
        "expected_obligations": ["area"],
        "expected_operator_class": "construct_section",
        "expected_result_type": "section",
        # Tam giác đều cạnh 6√2 ⇒ S = (√3/4)·72 = 18√3.
        "exact_expected_results": {"area": "18√3"},
        "expected_boundary": None,
    },
    {
        "case_id": "e8", "family": "cylinder",
        "feature": "negative__oblique_outside_v1_closure",
        "problem_text":
            "Cho hình trụ có hai đáy là hai đường tròn tâm A₁ và tâm A₂, bán "
            "kính đáy bằng 4 và A₁A₂ bằng 9. Gọi B là một điểm trên đường "
            "tròn đáy tâm A₁ và gọi C là một điểm trên đường tròn đáy tâm A₂ "
            "sao cho C không nằm trên đường thẳng đi qua B và song song với "
            "A₁A₂. Mặt phẳng đi qua ba điểm A₁, B, C cắt mặt xung quanh của "
            "hình trụ theo một đường cong. Tính bán kính của đường cong đó.",
        "expected_obligations": ["radius"],
        "expected_operator_class": "refusal",
        "expected_result_type": None,
        "exact_expected_results": {},
        "expected_boundary": "CURVED_SECTION_OUTSIDE_V1_CLOSURE",
    },
]


#: `case_id → ca`, để bộ test tra thẳng mà không dựng lại danh sách.
CA_MONG: dict[str, dict[str, Any]] = {c["case_id"]: c for c in CORPUS}


def gold(case_id: str):
    """`case_id → (facts, spec_json, obligations)`. Dùng primitive TỔNG QUÁT."""
    if case_id == "e1":
        td = {"G": (0, 0, 0), "H": (0, 0, 14), "L": (5, 0, 0)}
        d, s = _tron_xoay(ho="cylinder", tam="G", dinh="H", vanh="L",
                          ten_khoi="Tru", ten_tron="u", cat_bien="N",
                          cat_expr={"kind": "midpoint", "a": "G", "b": "H"},
                          fid_diem=FD, do=[("bk_u", "radius")], toa_do=td)
        f = [{"fact_id": FK, "label": "bán kính đáy 5, GH bằng 14",
              "values": [5, 14], "provenance": "confirmed"},
             {"fact_id": FD, "label": "G và H là tâm hai đáy, L trên đường "
                                     "tròn đáy tâm G, N là trung điểm GH",
              "values": ["G", "H", "L", "N"], "provenance": "confirmed"}]
        ob = [("radius", "u", "bk_u")]

    elif case_id == "e2":
        td = {"X": (0, 0, 0), "Y": (0, 0, 30), "Z": (11, 0, 0)}
        d, s = _tron_xoay(ho="cylinder", tam="X", dinh="Y", vanh="Z",
                          ten_khoi="Tru", ten_tron="v", cat_bien="V",
                          cat_expr=_chia("X", "Y", "2/5"),
                          fid_diem=FD, do=[("dt_v", "area")], toa_do=td)
        f = [{"fact_id": FK, "label": "bán kính đáy 11, XY bằng 30, XV bằng 12",
              "values": [11, 30, 12], "provenance": "confirmed"},
             {"fact_id": FD, "label": "X và Y là tâm hai đáy, Z trên đường "
                                     "tròn đáy tâm X, V thuộc đoạn XY",
              "values": ["X", "Y", "Z", "V"], "provenance": "confirmed"}]
        ob = [("area", "v", "dt_v")]

    elif case_id == "e3":
        td = {"E": (0, 0, 0), "F": (0, 0, 16), "R": (12, 0, 0)}
        d, s = _tron_xoay(ho="cone", tam="E", dinh="F", vanh="R",
                          ten_khoi="Non", ten_tron="m", cat_bien="M",
                          cat_expr=_chia("E", "F", "1/4"),
                          fid_diem=FD, do=[("bk_m", "radius")], toa_do=td)
        f = [{"fact_id": FK, "label": "bán kính đáy 12, chiều cao FE 16, EM 4",
              "values": [12, 16, 4], "provenance": "confirmed"},
             {"fact_id": FD, "label": "F là đỉnh, E là tâm đáy, R trên đường "
                                     "tròn đáy, M thuộc trục FE",
              "values": ["E", "F", "R", "M"], "provenance": "confirmed"}]
        ob = [("radius", "m", "bk_m")]

    elif case_id == "e4":
        td = {"Q": (0, 0, 0), "P": (0, 0, 28), "W": (21, 0, 0)}
        d, s = _tron_xoay(ho="cone", tam="Q", dinh="P", vanh="W",
                          ten_khoi="Non", ten_tron="t", cat_bien="T",
                          cat_expr=_chia("P", "Q", "5/7"),
                          fid_diem=FD, do=[("bk_t", "radius")], toa_do=td)
        f = [{"fact_id": FK, "label": "bán kính đáy 21, chiều cao PQ 28, PT 20",
              "values": [21, 28, 20], "provenance": "confirmed"},
             {"fact_id": FD, "label": "P là đỉnh, Q là tâm đáy, W trên đường "
                                     "tròn đáy, T thuộc đoạn PQ",
              "values": ["P", "Q", "W", "T"], "provenance": "confirmed"}]
        ob = [("radius", "t", "bk_t")]

    elif case_id in ("e5", "e6"):
        cf = {"e5": ("K", "J", 41, 9, "j", "bk_j", "radius"),
              "e6": ("D", "C", 29, 21, "c", "dt_c", "area")}[case_id]
        tam, ngoai, R, kc, ten_tron, bien, luong = cf
        td = {tam: (0, 0, 0), ngoai: (0, 0, kc)}
        d, s = _cau(tam=tam, ngoai=ngoai, ten_khoi="Cau", ten_tron=ten_tron,
                    fid_diem=FD, do=[(bien, luong)], toa_do=td)
        d = [x if x["name"] != "bk_" else
             _d("bk_", "float", initial_value=R, source_fact_id=FK) for x in d]
        f = [{"fact_id": FK, "label": f"bán kính mặt cầu {R}, "
                                     f"{tam}{ngoai} bằng {kc}",
              "values": [R, kc], "provenance": "confirmed"},
             {"fact_id": FD, "label": f"{tam} là tâm mặt cầu, {ngoai} là điểm "
                                     f"cách {tam} một khoảng {kc}",
              "values": [tam, ngoai], "provenance": "confirmed"}]
        ob = [(luong, ten_tron, bien)]

    elif case_id == "e7":
        ten = ["M", "N", "P", "Q", "M_", "N_", "P_", "Q_"]
        xyz = [(0, 0, 0), (6, 0, 0), (6, 6, 0), (0, 6, 0),
               (0, 0, 6), (6, 0, 6), (6, 6, 6), (0, 6, 6)]
        d = [_diem(n, p, FD) for n, p in zip(ten, xyz)]
        d += [_d("LP", "solid"), _d("mp_", "plane3"), _d("td", "section"),
              _d("dt_td", "float")]
        s = [{"kind": "construct_solid", "target_var": "LP", "vertices": ten,
              "faces": [[0, 1, 2, 3], [4, 5, 6, 7], [0, 1, 5, 4],
                        [1, 2, 6, 5], [2, 3, 7, 6], [3, 0, 4, 7]]},
             {"kind": "construct_plane", "target_var": "mp_",
              "through": ["M", "P", "N_"]},
             {"kind": "construct_section", "target_var": "td",
              "solid": "LP", "plane": "mp_"},
             _do("dt_td", "area", "td")]
        f = [{"fact_id": FK, "label": "cạnh hình lập phương bằng 6",
              "values": [6], "provenance": "confirmed"},
             {"fact_id": FD, "label": "MNPQ.M'N'P'Q' là hình lập phương",
              "values": ten, "provenance": "confirmed"}]
        ob = [("area", "td", "dt_td")]

    elif case_id == "e8":
        td = {"A1": (0, 0, 0), "A2": (0, 0, 9), "B": (4, 0, 0),
              "Cc": (0, 4, 9)}
        d = [_diem(n, td[n], FD) for n in td]
        d += [_d("Tru", "curved_solid"), _d("mp_", "plane3"),
              _d("cong", "circle3"), _d("bk_cong", "float")]
        s = [{"kind": "construct_curved_solid", "target_var": "Tru",
              "curved_kind": "cylinder", "anchor": "A1", "apex_or_top": "A2",
              "rim_point": "B"},
             {"kind": "construct_plane", "target_var": "mp_",
              "through": ["A1", "B", "Cc"]},
             {"kind": "assign", "target_var": "cong",
              "expr": {"kind": "intersect_plane_curved", "solid": "Tru",
                       "plane": "mp_"}},
             _do("bk_cong", "radius", "cong")]
        f = [{"fact_id": FK, "label": "bán kính đáy 4, A₁A₂ bằng 9",
              "values": [4, 9], "provenance": "confirmed"},
             {"fact_id": FD, "label": "A₁ và A₂ là tâm hai đáy, B trên đáy "
                                     "tâm A₁, C trên đáy tâm A₂",
              "values": ["A1", "A2", "B", "Cc"], "provenance": "confirmed"}]
        ob = [("radius", "cong", "bk_cong")]

    else:
        raise KeyError(case_id)

    return f, {"spec_version": "1.0", "title": f"Gold {case_id}",
               "description": "Chương trình gold do người viết cho preflight.",
               "pedagogical_intent": "Kiểm đường đúng đi được trước khi đo.",
               "memory_declarations": d, "statements": s,
               "visual_bindings": VB}, ob


def _bam(x: Any) -> str:
    return hashlib.sha256(
        json.dumps(x, ensure_ascii=False, sort_keys=True).encode("utf-8")
    ).hexdigest()


def chay_gold(ca: dict) -> dict[str, Any]:
    from app.ai import pipeline

    cid = ca["case_id"]
    f, spec_json, ob = gold(cid)
    hd = RequestContract(
        problem_text=ca["problem_text"], input_facts=f,
        obligations=tuple(Obligation(kind=k, container=c,
                                     params={"witness": w})
                          for k, c, w in ob))
    kq: dict[str, Any] = {"case_id": cid}
    try:
        spec = SemanticProgramSpec.model_validate(spec_json)
    except Exception as e:                                        # noqa: BLE001
        return {**kq, "stage": "schema", "servable": False,
                "loi": f"SCHEMA: {str(e)[:200]}"}
    out = verify_and_compile(hd, spec)
    mem = {k: str(v) for k, v in (out.final_memory or {}).items()}
    kq.update({"stage": out.stage_reached, "servable": bool(out.servable),
               "error_code": out.error_code,
               "details": [str(x)[:200] for x in (out.details or [])]})
    if ca["expected_operator_class"] == "refusal":
        kq["gold_ok"] = (not out.servable and any(
            ca["expected_boundary"] in x for x in (out.details or [])))
        return kq
    thuc = {k: mem.get(w) for (k, _, w) in ob}
    kq["thuc_te"] = thuc
    kq["exact_match"] = thuc == ca["exact_expected_results"]
    try:
        canh = pipeline._dung_scene3d(spec, hd) or {}
        ten = {o.get("name") or o.get("id") for o in canh.get("objects", [])}
        kq["scene3d_ok"] = all(w in ten for _, _, w in ob)
    except Exception as e:                                        # noqa: BLE001
        kq["scene3d_ok"] = False
        kq["scene3d_loi"] = f"{type(e).__name__}: {str(e)[:160]}"
    kq["gold_ok"] = bool(out.servable and kq["exact_match"]
                         and kq.get("scene3d_ok"))
    return kq


def main() -> int:
    RA.mkdir(parents=True, exist_ok=True)
    cong = [{k: v for k, v in c.items()
             if k in ("case_id", "family", "feature", "problem_text")}
            for c in CORPUS]
    mong = [{k: v for k, v in c.items()
             if k in ("case_id", "expected_obligations",
                      "expected_operator_class", "expected_result_type",
                      "exact_expected_results", "expected_boundary")}
            for c in CORPUS]
    ch, eh = _bam(cong), _bam(mong)
    kq = [chay_gold(c) for c in CORPUS]
    duong = [r for r, c in zip(kq, CORPUS)
             if c["expected_operator_class"] != "refusal"]
    am = [r for r, c in zip(kq, CORPUS)
          if c["expected_operator_class"] == "refusal"]
    dat = sum(1 for r in duong if r.get("gold_ok"))
    khop = sum(1 for r in duong if r.get("exact_match"))
    canh = sum(1 for r in duong if r.get("scene3d_ok"))
    dat_am = sum(1 for r in am if r.get("gold_ok"))

    print(f"CORPUS_HASH           = {ch}")
    print(f"EXPECTED_RESULTS_HASH = {eh}\n")
    for r, c in zip(kq, CORPUS):
        print(f"{r['case_id']:4} {c['family']:11} {str(r['stage']):22} "
              f"{'OK' if r.get('gold_ok') else 'HỎNG':5} "
              f"{r.get('thuc_te') or r.get('error_code') or ''}")
        if not r.get("gold_ok"):
            print(f"      └ {r.get('details') or r.get('loi')}")
    print(f"\nGOLD_POSITIVE_SERVABLE = {dat}/{len(duong)}")
    print(f"GOLD_EXACT_MATCH       = {khop}/{len(duong)}")
    print(f"GOLD_SCENE3D_PASS      = {canh}/{len(duong)}")
    print(f"GOLD_NEGATIVE_BOUNDARY = {'PASS' if dat_am == len(am) else 'FAIL'}")
    mo = dat == len(duong) and dat_am == len(am)
    print(f"PRE_LIVE_GUARD         = {'OPEN' if mo else 'BLOCKED'}")

    (RA / "corpus.json").write_text(json.dumps(
        {"version": "ab-v1", "corpus_hash": ch, "cases": cong},
        ensure_ascii=False, indent=2), encoding="utf-8")
    (RA / "expected_results.json").write_text(json.dumps(
        {"version": "ab-v1", "expected_results_hash": eh, "expected": mong},
        ensure_ascii=False, indent=2), encoding="utf-8")
    (RA / "gold_preflight.json").write_text(json.dumps(
        {"corpus_hash": ch, "expected_results_hash": eh,
         "gold_positive_servable": f"{dat}/{len(duong)}",
         "gold_exact_match": f"{khop}/{len(duong)}",
         "gold_scene3d_pass": f"{canh}/{len(duong)}",
         "gold_negative_boundary": "PASS" if dat_am == len(am) else "FAIL",
         "pre_live_guard": "OPEN" if mo else "BLOCKED", "ket_qua": kq},
        ensure_ascii=False, indent=2), encoding="utf-8")
    return 0 if mo else 1


if __name__ == "__main__":
    raise SystemExit(main())
