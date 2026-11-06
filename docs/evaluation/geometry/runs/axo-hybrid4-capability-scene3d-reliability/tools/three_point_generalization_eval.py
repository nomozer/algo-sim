"""Held-out generalization evaluation for the three-point plane capability (offline, 0 provider calls).

Run from `backend/`:  PYTHONIOENCODING=utf-8 .venv/Scripts/python.exe <this file> <out.json>

Cases were written AFTER the implementation and are not in the test suite: other wordings of the section request,
shuffled premise order, other letters and sizes, points on mixed edges, a plane equal to a face, invalid inputs. Each
served answer is compared with the independent oracle of `tests/geometry/test_hybrid4_three_point_plane_sections.py`
(exact vertex count and area²). Classification:
CORRECTLY_SERVED · CORRECTLY_REFUSED · INCORRECTLY_REFUSED · INCORRECTLY_SERVED.
"""
from __future__ import annotations

import json
import sys
from fractions import Fraction as F

sys.path.insert(0, ".")
import tests.geometry.test_hybrid4_three_point_plane_sections as T  # noqa: E402
from app.ai.hybrid_offline import run_hybrid_offline  # noqa: E402
from app.ai.typed_fact_next_extraction import ReplayExtractor  # noqa: E402


def payload(solid, prem, plane, sec_q, area=True, shuffle=False):
    prem = list(reversed(prem[3:])) + prem[:3] if shuffle else prem
    sentences = [s for s, _ in prem if s] + [sec_q] + ([T.AREA_Q] if area else [])
    text = ". ".join(sentences) + "."
    _t, p = T._payload(solid, prem, plane, area=area)
    p["problem_text"] = text
    p["derived_sections"][0]["quote"] = sec_q
    p["simulation_goals"][1]["quote"] = sec_q
    return text, p


def run(text, p):
    out = run_hybrid_offline(text, ReplayExtractor({text: p}), policy=T.POLICY)
    return out.response["envelope"], out.response["route_d"]


def square(apex, base, side, h):
    return T.square_pyramid(apex, base, side, h)


CASES = []


def case(name, expect, build):
    CASES.append((name, expect, build))


# ── valid, in scope: expect a served, oracle-exact section ──
def _wording_no_plane_word():
    solid, prem = square("S", "ABCD", 2, 4)
    prem += [T.midpoint("M", "S", "A"), T.midpoint("N", "S", "B"), T.divide("P", "S", "C", "1/4", "SP = 1/3 PC")]
    V = {"A": (0, 0, 0), "B": (2, 0, 0), "C": (2, 2, 0), "D": (0, 2, 0), "S": (0, 0, 4)}
    oracle = T.oracle_section(V, T.pyramid_edges("S", "ABCD"), (T.mid(V["S"], V["A"]), T.mid(V["S"], V["B"]), T.at(V["S"], V["C"], F(1, 4))))
    return solid, prem, ["M", "N", "P"], "Xác định thiết diện của hình chóp S.ABCD cắt bởi (MNP)", oracle


def _wording_plane_subject():
    solid, prem = square("S", "ABCD", 4, 2)
    prem += [T.midpoint("M", "S", "B"), T.midpoint("N", "S", "D"), T.midpoint("P", "S", "C")]
    V = {"A": (0, 0, 0), "B": (4, 0, 0), "C": (4, 4, 0), "D": (0, 4, 0), "S": (0, 0, 2)}
    oracle = T.oracle_section(V, T.pyramid_edges("S", "ABCD"), (T.mid(V["S"], V["B"]), T.mid(V["S"], V["D"]), T.mid(V["S"], V["C"])))
    return solid, prem, ["M", "N", "P"], "Tìm thiết diện của hình chóp S.ABCD cắt bởi mặt phẳng (MNP)", oracle


def _letters_and_scale():
    solid, prem = square("O", "KLMN", 6, 3)
    prem += [T.divide("X", "O", "K", "1/3", "OX = 1/2 XK"), T.midpoint("Y", "O", "L"), T.divide("Z", "O", "M", "2/3", "OZ = 2ZM")]
    V = {"K": (0, 0, 0), "L": (6, 0, 0), "M": (6, 6, 0), "N": (0, 6, 0), "O": (0, 0, 3)}
    oracle = T.oracle_section(V, T.pyramid_edges("O", "KLMN"), (T.at(V["O"], V["K"], F(1, 3)), T.mid(V["O"], V["L"]), T.at(V["O"], V["M"], F(2, 3))))
    return solid, prem, ["X", "Y", "Z"], "Xác định thiết diện của hình chóp O.KLMN cắt bởi mặt phẳng (XYZ)", oracle


def _mixed_apex_and_base_edges():
    solid, prem = square("S", "ABCD", 2, 2)
    prem += [T.midpoint("M", "S", "A"), T.midpoint("N", "S", "C"), T.midpoint("P", "A", "B")]
    V = {"A": (0, 0, 0), "B": (2, 0, 0), "C": (2, 2, 0), "D": (0, 2, 0), "S": (0, 0, 2)}
    oracle = T.oracle_section(V, T.pyramid_edges("S", "ABCD"), (T.mid(V["S"], V["A"]), T.mid(V["S"], V["C"]), T.mid(V["A"], V["B"])))
    return solid, prem, ["M", "N", "P"], "Xác định thiết diện của hình chóp S.ABCD cắt bởi mặt phẳng (MNP)", oracle


def _shuffled_premises_prism():
    solid, prem = T.right_prism("DEF", 4, 3, 5)
    prem += [T.midpoint("I", "D", "D'"), T.midpoint("J", "E", "E'"), T.midpoint("K", "F", "F'")]
    V = {"D": (0, 0, 0), "E": (4, 0, 0), "F": (0, 3, 0), "D'": (0, 0, 5), "E'": (4, 0, 5), "F'": (0, 3, 5)}
    oracle = T.oracle_section(V, T.prism_edges(["D", "E", "F"], ["D'", "E'", "F'"]), (T.mid(V["D"], V["D'"]), T.mid(V["E"], V["E'"]), T.mid(V["F"], V["F'"])))
    return solid, prem, ["I", "J", "K"], "Xác định thiết diện của lăng trụ DEF.D'E'F' cắt bởi mặt phẳng (IJK)", oracle, True


case("wording 'cắt bởi (MNP)' without 'mặt phẳng'", "SERVE", _wording_no_plane_word)
case("wording 'Tìm thiết diện … cắt bởi mặt phẳng (MNP)', points on SB/SD/SC", "SERVE", _wording_plane_subject)
case("letters O.KLMN / X,Y,Z, side 6, height 3, mixed ratios", "SERVE", _letters_and_scale)
case("points on apex edges and a base edge (SA, SC, AB)", "SERVE", _mixed_apex_and_base_edges)
case("right prism DEF.D'E'F', premise order shuffled, mid-height plane", "SERVE", _shuffled_premises_prism)


# ── invalid or degenerate input: expect a refusal (any precise code), never a scene ──
def _face_plane():
    solid, prem = square("S", "ABCD", 2, 2)
    return solid, prem, ["S", "A", "B"], "Xác định thiết diện của hình chóp S.ABCD cắt bởi mặt phẳng (SAB)", None


def _collinear_on_base_edge():
    solid, prem = square("S", "ABCD", 2, 2)
    prem += [T.midpoint("M", "A", "B")]
    return solid, prem, ["A", "M", "B"], "Xác định thiết diện của hình chóp S.ABCD cắt bởi mặt phẳng (AMB)", None


def _undeclared_point():
    solid, prem = square("S", "ABCD", 2, 2)
    prem += [T.midpoint("M", "S", "A")]
    return solid, prem, ["M", "X", "Y"], "Xác định thiết diện của hình chóp S.ABCD cắt bởi mặt phẳng (MXY)", None


def _plane_not_in_text():
    solid, prem = square("S", "ABCD", 2, 2)
    prem += [T.midpoint("M", "S", "A"), T.midpoint("N", "S", "B"), T.midpoint("P", "S", "C")]
    return solid, prem, ["M", "N", "P"], "Xác định thiết diện của hình chóp S.ABCD", None


case("plane equal to a face (SAB)", "REFUSE_OR_FACE", _face_plane)
case("three collinear points on a base edge (A, M, B)", "REFUSE", _collinear_on_base_edge)
case("undeclared points X, Y", "REFUSE", _undeclared_point)
case("section request that never names the plane", "REFUSE", _plane_not_in_text)


def main(out_path: str) -> None:
    rows = []
    for name, expect, build in CASES:
        built = build()
        solid, prem, plane, sec_q, oracle = built[:5]
        shuffle = len(built) > 5 and built[5]
        text, p = payload(solid, prem, plane, sec_q, area=expect == "SERVE", shuffle=shuffle)
        env, route = run(text, p)
        served = route["status"] == "SERVED" and env["status"] == "ok"
        row = {"case": name, "expected": expect, "status": route["status"],
               "code": (route.get("refusal") or {}).get("code")}
        if served:
            v = len(route["sections"][0]["vertices"]) if route.get("sections") else None
            row["vertices"] = v
            if expect == "SERVE":
                a2 = T.coef_squared(route["answer_exact"]["q1"]["coef"])
                row["area"] = route["answer_exact"]["q1"]["coef"]
                ok = v == oracle["vertices"] and a2 == oracle["area2"]
                row["oracle"] = {"vertices": oracle["vertices"], "area2": str(oracle["area2"])}
                row["class"] = "CORRECTLY_SERVED" if ok else "INCORRECTLY_SERVED"
            elif expect == "REFUSE_OR_FACE":
                row["class"] = "CORRECTLY_SERVED" if v == 3 else "INCORRECTLY_SERVED"
            else:
                row["class"] = "INCORRECTLY_SERVED"
        else:
            row["class"] = "INCORRECTLY_REFUSED" if expect == "SERVE" else "CORRECTLY_REFUSED"
        rows.append(row)
        print(f"{row['class']:20} {name}  [{row['status']} {row.get('code') or ''} {row.get('area') or ''}]")
    summary = {k: sum(r["class"] == k for r in rows) for k in
               ("CORRECTLY_SERVED", "CORRECTLY_REFUSED", "INCORRECTLY_REFUSED", "INCORRECTLY_SERVED")}
    json.dump({"provider_calls": 0, "summary": summary, "rows": rows}, open(out_path, "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    print(summary)


if __name__ == "__main__":
    main(sys.argv[1])
