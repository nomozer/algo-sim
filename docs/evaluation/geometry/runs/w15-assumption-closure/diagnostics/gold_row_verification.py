# -*- coding: utf-8 -*-
"""W15 Task 1 — verify every claim about the 18 AC2 gold rows (0 model calls).

The W15 plan's root-cause table is a reading of code; this file is the mathematical
check the plan requires before any certificate is built. Per row it records:
  (i)   the facts the TEXT states, quoted (spans located in `problem_text`);
  (ii)  a written determination argument (why those facts fix the configuration —
        up to congruence or absolutely — or why they do not);
  (iii) every requested quantity recomputed from the text alone, with the independent
        oracle `docs/evaluation/geometry/custodian/geometry_oracle.py` (pure fractions,
        no product import) or an explicit hand derivation where it lacks the kind,
        compared EXACTLY with the value the program serves;
  (iv)  on the served program: names in the witness closure written more than once in
        the execution trace, and the statement-level literals in that closure;
  (v)   the certificate route expected in W15 — a HYPOTHESIS for Tasks 2-5, not a result.
The oracle side never imports product code; product code is imported only to execute
the stored program (served values, trace). Refuses to overwrite. Run from the repo root:
  backend/.venv/Scripts/python.exe docs/evaluation/geometry/runs/w15-assumption-closure/diagnostics/gold_row_verification.py
"""
from __future__ import annotations

import importlib.util
import json
import sys
from fractions import Fraction as F
from pathlib import Path

HERE = Path(__file__).resolve()
ROOT = HERE.parents[6]
OUT = HERE.with_name("GOLD_ROW_VERIFICATION.json")
W14 = ROOT / "docs/evaluation/geometry/runs/w14-generic-formation-assumption/diagnostics"

sys.path.insert(0, str(ROOT / "docs/evaluation/geometry/custodian"))
import geometry_oracle as O  # noqa: E402  (pure fractions; independent of the product)


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


# ── oracle helpers (fractions only) ─────────────────────────────────────────

def dist_sq_point_line(p, a, b):
    d = O.sub(b, a)
    c = O.cross(O.sub(p, a), d)
    return O.dot(c, c) / O.dot(d, d)


def area_sq_triangle_x4(a, b, c):
    """(2·area)² of a triangle = |AB × AC|²."""
    c_ = O.cross(O.sub(b, a), O.sub(c, a))
    return O.dot(c_, c_)


def polygon_area_xy(pts):
    """Shoelace area of a polygon in a plane z = const (any simple polygon, convex or not)."""
    s = sum(p[0] * q[1] - q[0] * p[1] for p, q in zip(pts, pts[1:] + pts[:1]))
    return abs(s) / 2


def pyramid_volume(base_xy_area, apex_height):
    """(1/3)·base·height — valid for ANY planar base (the oracle's volume is convex-only)."""
    return base_xy_area * apex_height / 3


def prism(base, t):
    """Vertices + faces of the prism base ∪ (base + t), for the oracle's convex volume."""
    n = len(base)
    top = [O.add(p, t) for p in base]
    faces = [tuple(range(n)), tuple(range(n, 2 * n))]
    faces += [(i, (i + 1) % n, n + (i + 1) % n, n + i) for i in range(n)]
    return base + top, faces


def turn_signs(pts):
    """Sign of the z-cross product at each vertex of a polygon in the xy-plane (mixed ⇒ non-convex)."""
    m = len(pts)
    out = []
    for i in range(m):
        a, b, c = pts[i - 1], pts[i], pts[(i + 1) % m]
        z = (b[0] - a[0]) * (c[1] - b[1]) - (b[1] - a[1]) * (c[0] - b[0])
        out.append((z > 0) - (z < 0))
    return out


def radical(he, can=1, mu=0):
    """The product's exact value form `Radical(he, can, mu)` = he·√can·π^mu, for comparison."""
    return {"he": str(F(he)), "can": can, "mu": mu}


def rad_sqrt(x: F):
    """√x for a rational x = n/d as he·√can with square-free can (exact)."""
    x = F(x)
    n, d = x.numerator * x.denominator, x.denominator  # √(n/d²·d) = √(n·d)/d
    he, can = F(1, d), n
    k = 2
    while k * k <= can:
        while can % (k * k) == 0:
            can //= k * k
            he *= k
        k += 1
    return radical(he, can, 0)


# ── per-row verification (written by hand from each problem text) ──────────

def rows():
    V = O.V
    r = {}
    # Template rows: a canonical realisation built from the stated facts only.
    A, B, C, S = V(0, 0, 0), V(3, 0, 0), V(0, 4, 0), V(0, 0, 5)
    v = O.volume_from_interior_point([A, B, C, S], [(1, 2, 3), (0, 1, 2), (0, 2, 3), (0, 3, 1)])
    for cid in ("ho:chop_tam_giac", "rot:chop_tam_giac_xoay"):
        r[cid] = {
            "facts": ["hình chóp S.ABC", "đáy ABC là tam giác vuông tại A", "AB = 3", "AC = 4",
                      "SA vuông góc với đáy", "SA = 5"],
            "determination": ("Right triangle ABC (right angle at A, legs 3 and 4) is fixed up to congruence; "
                              "SA ⊥ (ABC) at A with |SA| = 5 puts S on the normal through A at distance 5 "
                              "(two mirror positions). The configuration is unique up to congruence "
                              "(reflections included); volume is congruence-invariant."),
            "oracle": {"the_tich_khoi": str(v)}, "hand": "V = (1/3)(1/2·3·4)·5 = 10",
        }
    A, B, C, D, S = V(0, 0, 0), V(3, 0, 0), V(3, 4, 0), V(0, 4, 0), V(0, 0, 6)
    r["ho:chop_chu_nhat"] = {
        "facts": ["hình chóp S.ABCD", "đáy ABCD là hình chữ nhật", "AB = 3", "AD = 4",
                  "SA vuông góc với mặt phẳng đáy", "SA = 6"],
        "determination": ("Rectangle ABCD with AB = 3, AD = 4 is fixed up to congruence; SA ⊥ (ABCD) at A with "
                          "|SA| = 6 fixes S up to reflection in the base plane."),
        "oracle": {"v": str(O.volume_from_interior_point(
            [S, A, B, C, D], [(1, 2, 3, 4), (0, 1, 2), (0, 2, 3), (0, 3, 4), (0, 4, 1)]))},
        "hand": "V = (1/3)(3·4)·6 = 24",
    }
    for cid in ("ho:lang_tru_tam_giac", "rigid:prism_text_translate_swap"):
        r[cid] = {
            "facts": ["lăng trụ đứng ABC.DEF", "đáy ABC là tam giác vuông tại A", "AB = 3", "AC = 4",
                      "Cạnh bên AD = 5"],
            "determination": ("Right prism: the top face is the base translated by a vector ⊥ base of length "
                              "|AD| = 5; the right triangle (legs 3, 4) is fixed up to congruence; the "
                              "translation direction is fixed up to sign. Unique up to congruence."),
            "oracle": {"the_tich_lang_tru": str(O.volume_from_interior_point(*prism(
                [V(0, 0, 0), V(3, 0, 0), V(0, 4, 0)], V(0, 0, 5))))},
            "hand": "V = (1/2·3·4)·5 = 30",
        }
    r["ho:hop_chu_nhat"] = {
        "facts": ["hình hộp chữ nhật ABCD.A'B'C'D'", "AB = 3", "AD = 4", "AA' = 5"],
        "determination": "A cuboid is fixed up to congruence by its three edge lengths at one vertex.",
        "oracle": {"V": str(O.volume_from_interior_point(*prism(
            [V(0, 0, 0), V(3, 0, 0), V(3, 4, 0), V(0, 4, 0)], V(0, 0, 5))))},
        "hand": "V = 3·4·5 = 60",
    }
    r["ho:lang_tru_day_vuong"] = {
        "facts": ["hình lăng trụ đứng", "đáy là hình vuông cạnh 3", "chiều cao bằng 7"],
        "determination": ("Unnamed single solid: a right prism over a square of side 3 with height 7 is fixed "
                          "up to congruence."),
        "oracle": {"V": str(O.volume_from_interior_point(*prism(
            [V(0, 0, 0), V(3, 0, 0), V(3, 3, 0), V(0, 3, 0)], V(0, 0, 7))))},
        "hand": "V = 3²·7 = 63",
    }
    r["ho:lap_phuong"] = {
        "facts": ["hình lập phương ABCD.A'B'C'D'", "cạnh bằng 4"],
        "determination": "A cube is fixed up to congruence by one edge length (all edges equal by type).",
        "oracle": {"V": str(O.volume_from_interior_point(*prism(
            [V(0, 0, 0), V(4, 0, 0), V(4, 4, 0), V(0, 4, 0)], V(0, 0, 4))))},
        "hand": "V = 4³ = 64",
    }
    # Coordinate rows: the text fixes every point absolutely.
    A, B, C, D, S = V(0, 0, 0), V(6, 0, 0), V(6, 6, 0), V(0, 6, 0), V(0, 0, 6)
    vol = O.volume_from_interior_point([S, A, B, C, D], [(1, 2, 3, 4), (0, 1, 2), (0, 2, 3), (0, 3, 4), (0, 4, 1)])
    # section z = 3: the edges SA..SD cut at their midpoints (S at z=6, base at z=0)
    mid = [O.V(*(F(p[i] + S[i], 2) for i in range(3))) for p in (A, B, C, D)]
    r["gold:p1_chop_thiet_dien_khoang_cach"] = {
        "facts": ["đáy ABCD là hình vuông", "A(0;0;0)", "B(6;0;0)", "C(6;6;0)", "D(0;6;0)", "S(0;0;6)",
                  "(α): z = 3"],
        "determination": "Every point and the cutting plane are given by coordinates/equation: fixed absolutely.",
        "consistency": {"square_sides_sq": [str(O.distance_sq_points(p, q)) for p, q in ((A, B), (B, C), (C, D), (D, A))],
                        "square_right_angle_at_B": O.perpendicular(O.sub(A, B), O.sub(C, B))},
        "oracle": {"the_volume_sabcd": str(vol),
                   "area_T": str(polygon_area_xy([(m[0], m[1]) for m in mid])),
                   "dist_S_BD": rad_sqrt(dist_sq_point_line(S, B, D))},
        "hand": "V = (1/3)·36·6 = 72; T = square of side 3 at mid-height, area 9; d(S,BD)² = 3888/72 = 54 → 3√6",
    }
    base = [(0, 0), (8, 0), (8, 6), (4, 2), (0, 6)]
    r["gold:p2_chop_day_ngu_giac_lom"] = {
        "facts": ["ngũ giác LÕM nằm trong mặt phẳng Oxy", "M(0;0;0)", "N(8;0;0)", "P(8;6;0)", "Q(4;2;0)",
                  "R(0;6;0)", "S(3;3;9)", "thứ tự quanh biên"],
        "determination": ("All vertices given by coordinates in boundary order: fixed absolutely. The custodian "
                          "oracle's volume is convex-only, so the base area is the shoelace sum (valid for any "
                          "simple polygon) and V = (1/3)·area·height with S at height 9 above z = 0."),
        "consistency": {"turn_signs_MNPQR": turn_signs(base), "non_convex": len(set(turn_signs(base))) > 1},
        "oracle": {"V_S_MNPQR": str(pyramid_volume(polygon_area_xy([(F(x), F(y)) for x, y in base]), F(9)))},
        "hand": "shoelace area 32 (non-convex pentagon), height 9 → V = (1/3)·32·9 = 96",
    }
    r["gold:p4_hinh_tru_the_tich_va_xung_quanh"] = {
        "facts": ["O(0;0;0)", "K(0;0;10)", "A(6;0;0) nằm trên đường tròn đáy tâm O"],
        "determination": "Axis OK and the rim point A are given: r = |OA| = 6, h = |OK| = 10, fixed absolutely.",
        "oracle": {"V": radical(36 * 10, 1, 1), "Sxq": radical(2 * 6 * 10, 1, 1)},
        "hand": "V = π·6²·10 = 360π; Sxq = 2π·6·10 = 120π",
    }
    r["gold:p5_hinh_non_the_tich_va_xung_quanh"] = {
        "facts": ["S(0;0;12)", "O(0;0;0)", "A(5;0;0) nằm trên đường tròn đáy"],
        "determination": "Apex, base centre and rim point given: r = 5, h = 12, l = 13, fixed absolutely.",
        "oracle": {"the_tich_khoi_non": radical(F(25 * 12, 3), 1, 1),
                   "dien_tich_xung_quanh_hinh_non": radical(5 * 13, 1, 1)},
        "hand": "V = (1/3)π·25·12 = 100π; l = √(25+144) = 13; Sxq = π·5·13 = 65π",
    }
    r["gold:p6_thiet_dien_elip_cua_hinh_tru"] = {
        "facts": ["O(0;0;0)", "K(0;0;24)", "A(5;0;0)", "(α): 2x − z + 12 = 0"],
        "determination": ("Cylinder r = 5, axis z ∈ [0, 24]; plane z = 2x + 12 meets it for x ∈ [−5, 5], "
                          "z ∈ [2, 22] ⊂ [0, 24]: a full ellipse. Fixed absolutely."),
        "oracle": {"dien_tich_elip_e": radical(25, 5, 1)},
        "hand": ("semi-minor b = r = 5; cos of the angle between (α) and the base = |n·k|/|n| = 1/√5 with "
                 "n = (2,0,−1) ⇒ semi-major a = r·√5 = 5√5; area = π·a·b = 25√5·π"),
    }
    r["gold:p7_thiet_dien_elip_cua_hinh_non"] = {
        "facts": ["S(0;0;12)", "O(0;0;0)", "A(6;0;0)", "(β): x + z − 9 = 0"],
        "determination": ("Cone radius(z) = (12 − z)/2 on 0 ≤ z ≤ 12; plane z = 9 − x. Intersection projected "
                          "to Oxy: 3(x−1)² + 4y² = 12, x ∈ [−1, 3] ⇒ z ∈ [6, 10]: a full ellipse on the "
                          "upper nappe. Fixed absolutely."),
        "oracle": {"dien_tich_E": radical(2, 6, 1)},
        "hand": ("projected semi-axes 2 (x) and √3 (y); the plane tilts x by √(1+1²) = √2 ⇒ true semi-axes "
                 "2√2 and √3 ⇒ area = π·2√2·√3 = 2√6·π"),
    }
    M, N, P = V(1, 0, 2), V(4, 0, 2), V(5, 2, 4)
    Q = O.add(M, O.sub(P, N))
    r["demo:n1_thoi_dinh_thu_tu"] = {
        "facts": ["hình thoi MNPQ", "M(1; 0; 2)", "N(4; 0; 2)", "P(5; 2; 4)", "ba đỉnh liên tiếp"],
        "determination": ("Three consecutive vertices given; a rhombus is a parallelogram, so Q = M + P − N = "
                          "(2,2,4). Consistency: |MN|² = 9 = |NP|² (the data is a rhombus). Fixed absolutely."),
        "consistency": {"MN_sq": str(O.distance_sq_points(M, N)), "NP_sq": str(O.distance_sq_points(N, P))},
        "oracle": {"dist_q_mp": rad_sqrt(dist_sq_point_line(Q, M, P))},
        "hand": "MQ × MP = (0,6,−6), |·|² = 72, |MP|² = 24 ⇒ d² = 3 ⇒ √3",
    }
    A, B, C, A2 = V(0, 0, 0), V(4, 0, 0), V(0, 4, 0), V(1, 1, 3)
    t = O.sub(A2, A)
    B2, C2 = O.add(B, t), O.add(C, t)
    I = O.V(*(F(B2[i] + C2[i], 2) for i in range(3)))
    r["demo:n2_lang_tru_xien_hai_vecto"] = {
        "facts": ["lăng trụ ABC.A'B'C'", "A(0; 0; 0)", "B(4; 0; 0)", "C(0; 4; 0)", "A'(1; 1; 3)",
                  "AA', BB', CC' đôi một song song và bằng nhau", "I là trung điểm của B'C'"],
        "determination": ("Equal parallel lateral edges ⇒ B' = B + AA', C' = C + AA'; I = midpoint of B'C'. "
                          "Fixed absolutely."),
        "oracle": {"khoang_cach_A_B_prime_I": rad_sqrt(dist_sq_point_line(A, B2, I))},
        "hand": "B'(5,1,3), I(3,3,3); B'A × B'I = (6,6,−12), |·|² = 216, |B'I|² = 8 ⇒ d² = 27 ⇒ 3√3",
    }
    A, B, D, A2 = V(0, 0, 0), V(3, 0, 0), V(0, 4, 0), V(0, 0, 6)
    C, B2, C2 = V(3, 4, 0), V(3, 0, 6), V(3, 4, 6)
    Mt = O.V(*(F(C[i] + C2[i], 2) for i in range(3)))
    r["demo:t3_hop_tinh_tien_day_chuyen"] = {
        "facts": ["hình hộp chữ nhật ABCD.A'B'C'D'", "AB = 3", "AD = 4", "AA' = 6", "M là trung điểm của cạnh CC'"],
        "determination": ("Cuboid fixed up to congruence by AB, AD, AA'; M is a midpoint (constructed); the "
                          "distance from A to line B'M is congruence-invariant."),
        "oracle": {"khoang_cach_a_b_prime_m": rad_sqrt(dist_sq_point_line(A, B2, Mt))},
        "hand": "B'(3,0,6), M(3,4,3); B'A × B'M = (24,−9,−12), |·|² = 801, |B'M|² = 25 ⇒ d = √801/5 = 3√89/5",
    }
    A, B, D, C, S = V(0, 0, 0), V(4, 0, 0), V(0, 2, 0), V(4, 2, 0), V(0, 0, 4)
    I = V(2, 1, 0)
    H = V(2, 0, 0)  # projection of I onto plane (SAB) = {y = 0} in this realisation
    r["demo:t4_mat_xich_trong_chuoi_sau"] = {
        "facts": ["hình chóp S.ABCD", "đáy ABCD là hình bình hành", "AB = 4", "AD = 2", "AB vuông góc với AD",
                  "SA vuông góc với mặt phẳng đáy", "SA = 4", "I là giao điểm của AC và BD",
                  "H là hình chiếu vuông góc của I lên mặt phẳng (SAB)"],
        "determination": ("Parallelogram with AB ⊥ AD is a rectangle, fixed up to congruence by AB = 4, AD = 2; "
                          "SA ⊥ base at A with |SA| = 4 fixes S up to reflection; I and H are constructions; "
                          "|HC| is congruence-invariant."),
        "check": {"I_is_midpoint_of_AC": O.V(*(F(A[i] + C[i], 2) for i in range(3))) == I,
                  "H_on_plane_SAB": O.coplanar(H, S, A, B),
                  "IH_perp_plane_SAB": (O.perpendicular(O.sub(I, H), O.sub(B, A))
                                        and O.perpendicular(O.sub(I, H), O.sub(S, A)))},
        "oracle": {"khoang_cach_hc": rad_sqrt(O.distance_sq_points(H, C))},
        "hand": "H(2,0,0), C(4,2,0) ⇒ |HC|² = 8 ⇒ 2√2",
    }
    return r


# ── served values and slice facts (product side) ────────────────────────────

def _served(cid: str, row: dict, M) -> dict:
    from app.simulation.semantic_program.contract import SemanticProgramSpec
    from app.simulation.semantic_program.request_contract import RequestContract
    ct = RequestContract.model_validate(row["contract"])
    raw = SemanticProgramSpec.model_validate(row["program"])
    # The route completes formation before anything runs (route.py: hoan_thien_dung_hinh), so the
    # slice is analysed on the completed program; served values are also read on the raw one.
    sp = M.hoan_thien_dung_hinh(raw, ct).spec
    chung = M._nhan_chung(ct, sp)
    res = M._chay(sp)
    d = sp.model_dump(mode="json", exclude_none=True)

    def gia_tri(v):
        if type(v).__name__ == "Radical":
            return {"he": str(F(v.he)), "can": v.can, "mu": v.mu}
        g = M._gia_tri(v)
        return None if g is None else str(F(g))

    served = {w: gia_tri(res.final_memory.get(n)) for w, n in chung.items()}
    raw_mem = M._chay(raw).final_memory
    raw_chung = M._nhan_chung(ct, raw)
    if {w: gia_tri(raw_mem.get(n)) for w, n in raw_chung.items()} != served:
        raise SystemExit(f"{cid}: formation completion changed a served value")
    closure = M._bao_dong(d, set(chung.values()))
    writes = {}
    for s in res.trace:
        if s.target:
            writes[s.target] = writes.get(s.target, 0) + 1
    multi = sorted(n for n in closure if writes.get(n, 0) > 1)
    # Writers per name, grouping a statement's own sub-steps: `section_edge` steps belong to the
    # `construct_section` step of the same target that closes them (one statement instance).
    hanh_dong = {}
    for s in res.trace:
        if s.target and s.action != "section_edge":
            hanh_dong.setdefault(s.target, []).append(s.action)
    multi_instance = sorted(n for n in closure if len(hanh_dong.get(n, ())) > 1)
    nhan = ("source_fact_id", "model_assumption", "provenance")
    lits = [{"at": f"decl.{m['name']}", "value": m["initial_value"], **{k: m[k] for k in nhan if k in m}}
            for m in d["memory_declarations"] if m["name"] in closure and m.get("initial_value") is not None]
    for i, s in enumerate(d["statements"]):
        if M._dinh_nghia(s) & closure:
            found: list = []
            _literals(s, f"stmt[{i}].{s['kind']}", found)
            lits += [{**x, **{k: s[k] for k in nhan if k in s}} for x in found]
    chi_de = _text_only_invariants(ct.problem_text or "")
    for x in lits:
        x["role_hypothesis"] = _role(x, d, chi_de, cid)
    return {"served": served, "closure_multi_write": multi, "closure_multi_instance": multi_instance,
            "closure_literals": lits,
            "never_written_in_trace": sorted(n for n in closure if writes.get(n, 0) == 0),
            "text": ct.problem_text}


def _text_only_invariants(text: str) -> tuple:
    """The product's four text builders with NO contract — `_van_ban(None, text)` reads the text alone."""
    from app.simulation.semantic_program.plane_equation import bat_bien_mat_phang
    from app.simulation.semantic_program.point_coordinate import bat_bien_toa_do
    from app.simulation.semantic_program.segment_relation import bat_bien_chia_doan, bat_bien_do_dai
    return (bat_bien_do_dai(None, text) + bat_bien_chia_doan(None, text)
            + bat_bien_mat_phang(None, text) + bat_bien_toa_do(None, text))


def _role(x: dict, d: dict, inv, cid: str) -> str:
    """HYPOTHESIS for Task 5 (plan's literal roles): SOURCE_DATUM when a text-only invariant pins the
    same entity to the same value; LAYOUT_FRONTIER for template vertices of a C1 row; else NO_ROLE."""
    from app.simulation.semantic_program.source_entities import dinh_danh_thuc_the
    at = x["at"]
    if at.startswith("decl."):
        ten = dinh_danh_thuc_the(at[5:])[0]
        for i in inv:
            if i.kind == "point_coordinate" and [dinh_danh_thuc_the(p)[0] for p in i.points] == [ten]:
                if [F(str(c)) for c in i.coefficients] == [F(str(c)) for c in x["value"]]:
                    return "SOURCE_DATUM (point_coordinate, same entity, same value)"
                return "NO_ROLE (text gives this point a DIFFERENT coordinate)"
        return ("LAYOUT_FRONTIER (template vertex; C1 validates it against the text constraints)"
                if not cid.startswith(("gold:", "demo:n")) else "NO_ROLE")
    if ".construct_plane_from_equation." in at:
        i = int(at.split("]")[0].split("[")[1])
        s = d["statements"][i]
        he = [F(str(s[k])) for k in ("a", "b", "c", "d")]
        for v in inv:
            if v.kind == "plane_equation" and v.coefficients:
                g = [F(str(c)) for c in v.coefficients]
                k = next((g[j] / he[j] for j in range(4) if he[j] != 0), None)
                if k and all(g[j] == k * he[j] for j in range(4)):
                    return "SOURCE_DATUM (plane_equation, proportional coefficients)"
        return "NO_ROLE"
    return "NO_ROLE (unclassified literal)"


def _literals(node, where: str, out: list) -> None:
    """Every literal a statement carries: LiteralExpr values, divide_segment ratios, plane-equation
    coefficients, declare_point coordinates (names are not literals)."""
    if isinstance(node, list):
        for i, v in enumerate(node):
            _literals(v, f"{where}[{i}]", out)
        return
    if not isinstance(node, dict):
        return
    k = node.get("kind")
    if k == "literal":
        out.append({"at": where, "value": node.get("value")})
        return
    for key, v in node.items():
        if (key == "ratio" or (k == "construct_plane_from_equation" and key in ("a", "b", "c", "d"))
                or (k == "declare_point" and key == "at")):
            out.append({"at": f"{where}.{key}", "value": v})
        elif isinstance(v, (dict, list)):
            _literals(v, f"{where}.{key}", out)


def main() -> None:
    if OUT.exists():
        raise SystemExit(f"refusing to overwrite {OUT}")
    sys.path.insert(0, str(ROOT / "backend"))
    M = _load("w14census", W14 / "assumption_census.py")
    corpus = {r["id"]: r for r in json.loads((W14 / "assumption_corpus" / "CORPUS.json").read_text(encoding="utf-8"))["rows"]}
    expected = rows()
    out = []
    for cid, ex in expected.items():
        sv = _served(cid, corpus[cid], M)
        spans = {f: sv["text"].find(f) for f in ex["facts"]}
        match = {w: (sv["served"].get(w) == v) for w, v in ex["oracle"].items()}
        route = "C0 (source-pinned slice)" if cid.startswith(("gold:", "demo:n")) else "C1 (template determination)"
        out.append({
            "id": cid, "facts_stated": ex["facts"],
            "fact_spans_in_text": spans, "facts_not_found_verbatim": sorted(f for f, i in spans.items() if i < 0),
            "determination": ex["determination"], **({"consistency": ex["consistency"]} if "consistency" in ex else {}),
            **({"construction_check": ex["check"]} if "check" in ex else {}),
            "oracle": ex["oracle"], "hand_derivation": ex["hand"], "served": sv["served"],
            "oracle_equals_served": match, "all_equal": all(match.values()),
            "closure_names_written_more_than_once": sv["closure_multi_write"],
            "closure_names_defined_by_more_than_one_statement_instance": sv["closure_multi_instance"],
            "single_reaching_definition_per_name": not sv["closure_multi_instance"],
            "closure_names_never_written_in_trace": sv["never_written_in_trace"],
            "closure_literals": sv["closure_literals"],
            "every_literal_has_a_role": all(not x["role_hypothesis"].startswith("NO_ROLE")
                                            for x in sv["closure_literals"]),
            "expected_w15_route_hypothesis": route,
        })
    OUT.write_text(json.dumps({
        "check": "W15_GOLD_ROW_VERIFICATION", "model_calls": 0,
        "oracle": "docs/evaluation/geometry/custodian/geometry_oracle.py (fractions only) + hand derivations",
        "rows": out,
        "summary": {"rows": len(out), "all_oracle_equal": sum(1 for x in out if x["all_equal"]),
                    "all_facts_found_verbatim": sum(1 for x in out if not x["facts_not_found_verbatim"]),
                    "rows_with_multi_write_in_closure": [x["id"] for x in out if x["closure_names_written_more_than_once"]],
                    "rows_with_multi_instance_definitions": [x["id"] for x in out
                                                              if not x["single_reaching_definition_per_name"]],
                    "rows_with_a_literal_without_role": [x["id"] for x in out if not x["every_literal_has_a_role"]],
                    "note": ("(iv)/(v) are hypotheses for Task 5: section_edge sub-steps are grouped with the "
                             "construct_section step that closes them; roles use the product's text builders "
                             "called WITHOUT the contract (text only).")},
    }, ensure_ascii=False, indent=2, default=str) + "\n", encoding="utf-8", newline="\n")
    print(OUT.name, len(out), "rows;", sum(1 for x in out if x["all_equal"]), "oracle == served")


if __name__ == "__main__":
    main()
