"""Hybrid B compiler benchmark (run `hybrid-compiler-capability-audit`, 2026-10-11) — cases, verified Typed Facts and an
INDEPENDENT oracle. Not a test module (no `test_` prefix); `test_hybrid_compiler_benchmark.py` drives it.

Independence: the oracle never imports the engine, planner or kernel. It works on explicit Euclidean coordinates or on
squared edge lengths (Cayley–Menger) with `Fraction`, and compares SQUARED answers (volume², length², cos²) so every
check is exact. Expected outcomes are registered here from mathematics and the repository's refusal policy, before the
compiler is changed; they are never copied from engine output.

Each case: `id`, `tier`, `text` (sentences joined by a space), `facts` (verified Typed Facts, one per clause, quotes =
the clause sentence), `expect` = {"status": "SERVED", "answer_sq": {question_fact_id: Fraction}} or
{"status": "REFUSED", "refusal": class}. `gap` names the capability a SERVED-by-mathematics case is known to need.
"""
from __future__ import annotations

from fractions import Fraction as F

# ── independent oracle ────────────────────────────────────────────────────────────────────────────────────────────

Vec = tuple[F, F, F]


def _v(*xs) -> Vec:
    return tuple(F(x) for x in xs)  # type: ignore[return-value]


def sub(a: Vec, b: Vec) -> Vec:
    return (a[0] - b[0], a[1] - b[1], a[2] - b[2])


def dot(a: Vec, b: Vec) -> F:
    return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]


def cross(a: Vec, b: Vec) -> Vec:
    return (a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0])


def mid(a: Vec, b: Vec) -> Vec:
    return ((a[0] + b[0]) / 2, (a[1] + b[1]) / 2, (a[2] + b[2]) / 2)


def len2(a: Vec, b: Vec) -> F:
    d = sub(a, b)
    return dot(d, d)


def dist2_point_plane(p: Vec, a: Vec, b: Vec, c: Vec) -> F:
    n = cross(sub(b, a), sub(c, a))
    return dot(n, sub(p, a)) ** 2 / dot(n, n)


def dist2_point_line(p: Vec, a: Vec, b: Vec) -> F:
    d, w = sub(b, a), sub(p, a)
    return dot(w, w) - dot(w, d) ** 2 / dot(d, d)


def foot_on_line(p: Vec, a: Vec, b: Vec) -> Vec:
    d = sub(b, a)
    t = dot(sub(p, a), d) / dot(d, d)
    return (a[0] + t * d[0], a[1] + t * d[1], a[2] + t * d[2])


def intersect_line_plane(p: Vec, q: Vec, a: Vec, b: Vec, c: Vec) -> Vec:
    n = cross(sub(b, a), sub(c, a))
    d = sub(q, p)
    t = dot(n, sub(a, p)) / dot(n, d)
    return (p[0] + t * d[0], p[1] + t * d[1], p[2] + t * d[2])


def intersect_lines(p: Vec, q: Vec, r: Vec, s: Vec) -> Vec:
    """Coplanar, non-parallel lines PQ and RS (solved by least squares on the 3×2 system, exact)."""
    u, v, w = sub(q, p), sub(s, r), sub(r, p)
    uu, uv, vv, wu, wv = dot(u, u), dot(u, v), dot(v, v), dot(w, u), dot(w, v)
    t = (wu * vv - wv * uv) / (uu * vv - uv * uv)
    return (p[0] + t * u[0], p[1] + t * u[1], p[2] + t * u[2])


def cos2_line_plane(p: Vec, q: Vec, a: Vec, b: Vec, c: Vec) -> F:
    """cos² of the angle between line PQ and plane ABC = 1 − sin², sin² = (n·d)²/(|n|²|d|²)."""
    n, d = cross(sub(b, a), sub(c, a)), sub(q, p)
    return 1 - dot(n, d) ** 2 / (dot(n, n) * dot(d, d))


def cayley_menger_volume2(d2: dict[frozenset, F]) -> F:
    """Tetrahedron V² from the six SQUARED edge lengths (288·V² = det CM) — no coordinates at all."""
    pts = sorted({p for e in d2 for p in e})
    m = [[F(0)] + [F(1)] * 4] + [[F(1)] + [F(0) if i == j else d2[frozenset((pts[i], pts[j]))] for j in range(4)]
                                for i in range(4)]
    return _det(m) / 288


def _det(m: list[list[F]]) -> F:
    m = [row[:] for row in m]
    n, det = len(m), F(1)
    for c in range(n):
        p = next((r for r in range(c, n) if m[r][c] != 0), None)
        if p is None:
            return F(0)
        if p != c:
            m[c], m[p] = m[p], m[c]
            det = -det
        det *= m[c][c]
        for r in range(c + 1, n):
            f = m[r][c] / m[c][c]
            m[r] = [x - f * y for x, y in zip(m[r], m[c])]
    return det


# Square pyramid S.ABCD, side 2, SA ⊥ (ABCD), SA = 3 (Euclidean coordinates).
A, B, C, D, S = _v(0, 0, 0), _v(2, 0, 0), _v(2, 2, 0), _v(0, 2, 0), _v(0, 0, 3)
O = intersect_lines(A, C, B, D)


def oracle() -> dict[str, dict[str, F]]:
    """Squared answers per SERVED-by-mathematics case, computed only from the definitions above."""
    m_sa, m_sc = mid(S, A), mid(S, C)
    p = intersect_line_plane(S, D, m_sa, B, C)
    h9 = foot_on_line(p, B, D)
    k10 = intersect_lines(S, O, A, m_sc)
    i12 = intersect_lines(mid(S, B), mid(S, D), S, O)
    # regular triangular pyramid: base 2, lateral 3 (Cayley–Menger, no coordinates)
    tri = {frozenset(e): F(v) for e, v in [(("A", "B"), 4), (("B", "C"), 4), (("A", "C"), 4),
                                           (("S", "A"), 9), (("S", "B"), 9), (("S", "C"), 9)]}
    cube_a, cube_b, cube_d, cube_a1 = _v(0, 0, 0), _v(2, 0, 0), _v(0, 2, 0), _v(0, 0, 2)
    v_square = F(1, 3) * 4 * 3
    return {
        "B01": {"q": v_square ** 2},
        "B02": {"q": cayley_menger_volume2(tri)},
        "B03": {"q": dist2_point_plane(cube_a, cube_a1, cube_b, cube_d)},
        "B04": {"q": F(3) * 9},                                        # (√3 · 3)²: base area² 3 (Heron, side 2) × h² 9
        "B05": {"q": len2(S, O)},
        "B06": {"q": dist2_point_plane(m_sc, A, B, C)},
        "B07": {"q": dist2_point_line(A, S, B)},
        "B08": {"q": dist2_point_plane(A, S, B, C)},
        "B09": {"q": len2(p, h9)},
        "B10": {"q": len2(A, k10)},
        "B11": {"q": dist2_point_line(A, S, O)},
        "B12": {"q": len2(S, i12)},
        "B13": {"q": len2(p, h9)},
        "B14": {"q": len2(A, k10)},
        "B15": {"q": dist2_point_line(A, S, B)},
        "B16": {"q": len2(A, k10)},
        "B26": {"q": dist2_point_line(S, B, D)},
        "B27": {"q": dist2_point_plane(m_sc, S, A, B)},
        "B28": {"q": dist2_point_plane(O, S, C, D)},
        "B29": {"q": cos2_line_plane(S, C, A, B, C)},
        "B30": {"q": F(9) - len2(_v(0, 0, 0), _v(1, 1, 0))},        # SO² = lateral² − (half diagonal)²
    }


# ── cases (verified Typed Facts) ─────────────────────────────────────────────────────────────────────────────────

def _f(fid: str, kind: str, quote: str, role: str = "premise", **kw) -> dict:
    return {"id": fid, "kind": kind, "role": role, "quotes": [quote], **kw}


def _square(names: str = "SABCD") -> tuple[list[str], list[dict]]:
    s, a, b, c, d = names
    base = f"{a}{b}{c}{d}"
    q = [f"Cho hình chóp {s}.{base}.", f"Đáy {base} là hình vuông cạnh 2.", f"{s}{a} vuông góc với ({base}).", f"{s}{a} = 3."]
    facts = [_f("f1", "solid", q[0], solid=f"{s}.{base}", solid_type="pyramid"),
             _f("f2", "polygon_shape", q[1], points=list(base), shape="square", value="2"),
             _f("f3", "perpendicular", q[2], points_a=[s, a], points_b=list(base)),
             _f("f4", "length", q[3], points=[s, a], measure="segment", value="3")]
    return q, facts


def _ask(fid: str, quote: str, quantity: str, **kw) -> dict:
    return _f(fid, "question", quote, role="question", quantity=quantity, **kw)


def _mid(fid, p, a, b):
    return _f(fid, "point_def", f"Gọi {p} là trung điểm {a}{b}.", point=p, point_kind="midpoint", points=[a, b])


def _ill(fid, p, l1, l2):
    return _f(fid, "point_def", f"Gọi {p} là giao điểm của {l1} và {l2}.", point=p, point_kind="intersect_line_line",
              points_a=list(l1), points_b=list(l2))


def _ilp(fid, p, l, pl):
    return _f(fid, "point_def", f"Gọi {p} là giao điểm của {l} và ({pl}).", point=p, point_kind="intersect_line_plane",
              points_a=list(l), points_b=list(pl))


def _proj(fid, img, p, tgt):
    w = tgt if len(tgt) == 2 else f"({tgt})"
    return _f(fid, "projection", f"Gọi {img} là hình chiếu vuông góc của {p} lên {w}.", point=p, points=list(tgt), at=img)


def _case(cid, tier, quotes_facts, expect, gap=None):
    sentences, facts = quotes_facts
    return {"id": cid, "tier": tier, "text": " ".join(sentences), "facts": facts, "expect": expect, **({"gap": gap} if gap else {})}


def _with(base, *extra):
    q, f = base
    q, f = list(q), [dict(x) for x in f]
    for x in extra:
        q.append(x["quotes"][0])
        f.append(x)
    return q, f


def _served():
    return {"status": "SERVED"}


def _refused(cls: str):
    return {"status": "REFUSED", "refusal": cls}


def cases() -> list[dict]:
    sq = _square()
    out = [
        # T1 — simple constructions
        _case("B01", "simple", _with(sq, _ask("q", "Tính thể tích khối chóp S.ABCD.", "volume", solid="S.ABCD")), _served()),
        _case("B02", "simple", (["Cho hình chóp tam giác đều S.ABC có cạnh đáy bằng 2 và cạnh bên bằng 3.",
                                 "Tính thể tích khối chóp S.ABC."],
                                [_f("f1", "solid", "Cho hình chóp tam giác đều S.ABC",
                                    solid="S.ABC", solid_type="pyramid", regular=True),
                                 _f("f2", "length", "cạnh đáy bằng 2", solid="S.ABC", measure="base_edge", value="2"),
                                 _f("f3", "length", "cạnh bên bằng 3", solid="S.ABC", measure="lateral_edge", value="3"),
                                 _ask("q", "Tính thể tích khối chóp S.ABC.", "volume", solid="S.ABC")]), _served()),
        _case("B03", "simple", (["Cho hình lập phương ABCD.A'B'C'D' cạnh 2.", "Tính khoảng cách từ A đến (A'BD)."],
                                [_f("f1", "solid", "Cho hình lập phương ABCD.A'B'C'D' cạnh 2.", solid="ABCD.A'B'C'D'",
                                    solid_type="cube"),
                                 _f("f2", "length", "Cho hình lập phương ABCD.A'B'C'D' cạnh 2.", solid="ABCD.A'B'C'D'",
                                    measure="edge", value="2"),
                                 _ask("q", "Tính khoảng cách từ A đến (A'BD).", "distance", points_a=["A"],
                                      points_b=["A'", "B", "D"])]), _served()),
        _case("B04", "simple", (["Cho lăng trụ đứng ABC.A'B'C' có đáy là tam giác đều ABC cạnh 2.", "AA' = 3.",
                                 "Tính thể tích khối lăng trụ ABC.A'B'C'."],
                                [_f("f1", "solid", "Cho lăng trụ đứng ABC.A'B'C' có đáy là tam giác đều ABC cạnh 2.",
                                    solid="ABC.A'B'C'", solid_type="prism", right=True),
                                 _f("f2", "polygon_shape", "Cho lăng trụ đứng ABC.A'B'C' có đáy là tam giác đều ABC cạnh 2.",
                                    points=["A", "B", "C"], shape="equilateral_triangle", value="2"),
                                 _f("f3", "length", "AA' = 3.", points=["A", "A'"], measure="segment", value="3"),
                                 _ask("q", "Tính thể tích khối lăng trụ ABC.A'B'C'.", "volume", solid="ABC.A'B'C'")]),
              _served()),
        # T2 — two primitives
        _case("B05", "two_primitives", _with(sq, _ill("f5", "O", "AC", "BD"), _ask("q", "Tính độ dài SO.", "length",
                                                                                     points=["S", "O"])), _served()),
        _case("B06", "two_primitives", _with(sq, _mid("f5", "M", "S", "C"),
                                             _ask("q", "Tính khoảng cách từ M đến (ABCD).", "distance", points_a=["M"],
                                                  points_b=list("ABCD"))), _served()),
        _case("B07", "two_primitives", _with(sq, _proj("f5", "H", "A", "SB"), _ask("q", "Tính độ dài AH.", "length",
                                                                                     points=["A", "H"])), _served()),
        _case("B08", "two_primitives", _with(sq, _proj("f5", "H", "A", "SBC"), _ask("q", "Tính độ dài AH.", "length",
                                                                                      points=["A", "H"])), _served()),
        # T3 — midpoint → intersection → projection
        _case("B09", "chain", _with(sq, _mid("f5", "M", "S", "A"), _ilp("f6", "P", "SD", "MBC"), _proj("f7", "H", "P", "BD"),
                                    _ask("q", "Tính độ dài PH.", "length", points=["P", "H"])), _served()),
        _case("B10", "chain", _with(sq, _ill("f5", "O", "AC", "BD"), _mid("f6", "M", "S", "C"), _ill("f7", "K", "SO", "AM"),
                                    _ask("q", "Tính độ dài AK.", "length", points=["A", "K"])), _served()),
        # T4 — derived objects feeding the next construction
        _case("B11", "derived_input", _with(sq, _ill("f5", "O", "AC", "BD"), _proj("f6", "H", "A", "SO"),
                                            _ask("q", "Tính độ dài AH.", "length", points=["A", "H"])), _served()),
        _case("B12", "derived_input", _with(sq, _mid("f5", "M", "S", "B"), _mid("f6", "N", "S", "D"), _ill("f7", "O", "AC", "BD"),
                                            _ill("f8", "I", "MN", "SO"), _ask("q", "Tính độ dài SI.", "length",
                                                                               points=["S", "I"])), _served()),
        # T5 — order of presentation (forward references)
        _case("B13", "reordered", _with(sq, _proj("f7", "H", "P", "BD"), _ilp("f6", "P", "SD", "MBC"),
                                        _mid("f5", "M", "S", "A"), _ask("q", "Tính độ dài PH.", "length",
                                                                         points=["P", "H"])), _served()),
        _case("B14", "reordered", _with(sq, _ask("q", "Tính độ dài AK.", "length", points=["A", "K"]),
                                        _ill("f7", "K", "SO", "AM"), _mid("f6", "M", "S", "C"), _ill("f5", "O", "AC", "BD")),
              _served()),
        # T6 — renamed points and solid
        _case("B15", "renamed", _with(_square("TMNPQ"), _proj("f5", "K", "M", "TN"),
                                      _ask("q", "Tính độ dài MK.", "length", points=["M", "K"])), _served()),
        _case("B16", "renamed", _with(_square("VEFGH"), _ill("f5", "O", "EG", "FH"), _mid("f6", "X", "V", "G"),
                                      _ill("f7", "Y", "VO", "EX"), _ask("q", "Tính độ dài EY.", "length",
                                                                         points=["E", "Y"])), _served()),
        # T7 — missing data
        _case("B17", "missing_data", (sq[0][:3] + ["Tính thể tích khối chóp S.ABCD."],
                                      sq[1][:3] + [_ask("q", "Tính thể tích khối chóp S.ABCD.", "volume", solid="S.ABCD")]),
              _refused("underconstrained")),
        _case("B18", "missing_data", (["Cho hình chóp S.ABC.", "SA vuông góc với (ABC).", "SA = 3.",
                                       "Tính thể tích khối chóp S.ABC."],
                                      [_f("f1", "solid", "Cho hình chóp S.ABC.", solid="S.ABC", solid_type="pyramid"),
                                       _f("f2", "perpendicular", "SA vuông góc với (ABC).", points_a=["S", "A"],
                                          points_b=list("ABC")),
                                       _f("f3", "length", "SA = 3.", points=["S", "A"], measure="segment", value="3"),
                                       _ask("q", "Tính thể tích khối chóp S.ABC.", "volume", solid="S.ABC")]),
              _refused("underconstrained")),
        # T8 — contradictory data
        _case("B19", "contradictory", _with(sq, _f("f5", "length", "SB = 5.", points=["S", "B"], measure="segment", value="5"),
                                            _ask("q", "Tính thể tích khối chóp S.ABCD.", "volume", solid="S.ABCD")),
              _refused("contradictory")),
        _case("B20", "contradictory", _with(sq, _ill("f5", "O", "AC", "BD"), _mid("f6", "O", "A", "B"),
                                            _ask("q", "Tính độ dài SO.", "length", points=["S", "O"])),
              _refused("contradictory")),
        # T9 — several valid configurations
        _case("B21", "multi_config", (["Cho hình chóp S.ABCD.", "Đáy ABCD là hình vuông cạnh 2.",
                                       "Chiều cao của khối chóp S.ABCD bằng 3.", "Tính thể tích khối chóp S.ABCD."],
                                      [_f("f1", "solid", "Cho hình chóp S.ABCD.", solid="S.ABCD", solid_type="pyramid"),
                                       _f("f2", "polygon_shape", "Đáy ABCD là hình vuông cạnh 2.", points=list("ABCD"),
                                          shape="square", value="2"),
                                       _f("f3", "length", "Chiều cao của khối chóp S.ABCD bằng 3.", solid="S.ABCD",
                                          measure="height", value="3"),
                                       _ask("q", "Tính thể tích khối chóp S.ABCD.", "volume", solid="S.ABCD")]),
              _refused("figure_not_unique")),
        _case("B22", "multi_config", (["Cho hình chóp S.ABCD.", "Đáy ABCD là hình vuông cạnh 2.",
                                       "Chiều cao của khối chóp S.ABCD bằng 3.", "Tính khoảng cách từ A đến (SBC)."],
                                      [_f("f1", "solid", "Cho hình chóp S.ABCD.", solid="S.ABCD", solid_type="pyramid"),
                                       _f("f2", "polygon_shape", "Đáy ABCD là hình vuông cạnh 2.", points=list("ABCD"),
                                          shape="square", value="2"),
                                       _f("f3", "length", "Chiều cao của khối chóp S.ABCD bằng 3.", solid="S.ABCD",
                                          measure="height", value="3"),
                                       _ask("q", "Tính khoảng cách từ A đến (SBC).", "distance", points_a=["A"],
                                            points_b=list("SBC"))]),
              _refused("underconstrained")),
        # T10 — goals the library does not support
        _case("B23", "unsupported_goal", _with(sq, _mid("f5", "M", "S", "C"),
                                               _f("q", "unsupported", "Tính diện tích thiết diện của khối chóp cắt bởi (MAB).",
                                                  role="question", reason="thiết diện (cross-section) chưa có trong thư viện")),
              _refused("unsupported")),
        _case("B24", "unsupported_goal", (sq[0][:3] + ["Góc giữa SC và (ABCD) bằng 60°.", "Tính thể tích khối chóp S.ABCD."],
                                          sq[1][:3] + [_f("f4", "unsupported", "Góc giữa SC và (ABCD) bằng 60°.",
                                                          reason="góc cho trước — chưa có loại dữ kiện góc"),
                                                       _ask("q", "Tính thể tích khối chóp S.ABCD.", "volume", solid="S.ABCD")]),
              _refused("unsupported")),
        _case("B25", "unsupported_goal", _with(sq, _f("q", "unsupported", "Tính bán kính mặt cầu ngoại tiếp khối chóp S.ABCD.",
                                                      role="question", reason="mặt cầu ngoại tiếp chưa có trong thư viện")),
              _refused("unsupported")),
        # Library has the parts — composition / grammar
        # Pre-registered gap "distance point→line = orthogonal_projection_line + ask_length (no single ask function)",
        # closed by goal decomposition slice 1 (run `hybrid-goal-decomposition`); expectation unchanged.
        _case("B26", "composition", _with(sq, _ask("q", "Tính khoảng cách từ S đến BD.", "distance", points_a=["S"],
                                                   points_b=["B", "D"])), _served()),
        _case("B27", "composition", _with(sq, _f("q", "unsupported", "Tính khoảng cách từ trung điểm của SC đến (SAB).",
                                                 role="question",
                                                 reason="toán hạng là điểm dẫn xuất không có tên (trung điểm của SC)")),
              _served(), gap="unnamed derived operand: Typed Facts cannot name 'trung điểm của SC' inside a question"),
        _case("B28", "composition", _with(sq, _f("f5", "point_def", "Gọi O là tâm của hình vuông ABCD.", point="O",
                                                 point_kind="centroid", points=list("ABCD")),
                                          _ask("q", "Tính khoảng cách từ O đến (SCD).", "distance", points_a=["O"],
                                               points_b=list("SCD"))), _served(),
              gap="'tâm' of a square = centroid, but the centroid source keyword is only 'trọng tâm'"),
        _case("B29", "two_primitives", _with(sq, _ask("q", "Tính góc giữa SC và (ABCD).", "angle", points_a=["S", "C"],
                                                      points_b=list("ABCD"))), _served()),
        _case("B30", "two_primitives", (["Cho hình chóp tứ giác đều S.ABCD có cạnh đáy bằng 2 và cạnh bên bằng 3.",
                                         "Gọi O là giao điểm của AC và BD.", "Tính độ dài SO."],
                                        [_f("f1", "solid", "Cho hình chóp tứ giác đều S.ABCD",
                                            solid="S.ABCD", solid_type="pyramid", regular=True),
                                         _f("f2", "length", "cạnh đáy bằng 2", solid="S.ABCD", measure="base_edge", value="2"),
                                         _f("f3", "length", "cạnh bên bằng 3", solid="S.ABCD", measure="lateral_edge", value="3"),
                                         _ill("f4", "O", "AC", "BD"),
                                         _ask("q", "Tính độ dài SO.", "length", points=["S", "O"])]), _served()),
    ]
    ans = oracle()
    for c in out:
        if c["expect"]["status"] == "SERVED":
            c["expect"]["answer_sq"] = ans[c["id"]]["q"]
    return out


# ── answer parsing (engine display string → exact square) ─────────────────────────────────────────────────────────

def answer_square(s: str) -> F | None:
    """'6√13/13' → (6/13)²·13; 'cos²=8/17' → 8/17; '4' → 16. None if the string is not a plain exact number."""
    import re

    if s.startswith("cos²="):
        return F(s.split("=", 1)[1])
    m = re.fullmatch(r"(\d*)(?:√(\d+))?(?:/(\d+))?", s)
    if not m or not s:
        return None
    k = F(int(m[1]) if m[1] else 1, int(m[3]) if m[3] else 1)
    return k * k * (int(m[2]) if m[2] else 1)


#: Every refusal code of the B route, classified by meaning (complete: a code missing here is a harness bug, see the test).
REFUSAL_CLASS = {
    # Question-local source coverage, run question-local-givens: taxonomy only; case labels/oracle unchanged.
    "QUESTION_LOCAL_GIVEN_CONFLICT": "contradictory",
    "QUESTION_LOCAL_GIVEN_UNVERIFIED": "unsupported", "QUESTION_CONTEXT_UNSUPPORTED": "unsupported",
    # not enough given to fix the figure
    "UNDERDETERMINED_POINT": "underconstrained", "MISSING_DIMENSION": "underconstrained",
    "FOOT_NOT_DETERMINED": "underconstrained", "FIGURE_NOT_UNIQUE": "figure_not_unique",
    # givens conflict
    "INCONSISTENT_FACTS": "contradictory", "PRECONDITION_FAILED": "contradictory", "FOOT_NOT_IN_PLANE": "contradictory",
    "NON_HOMOGENEOUS_LENGTHS": "contradictory",
    # the library / compiler has no rule
    "OUT_OF_SCOPE": "unsupported", "UNSUPPORTED_CAPABILITY": "unsupported", "UNSUPPORTED_PLANE": "unsupported",
    "UNSUPPORTED_REGULAR_POLYGON": "unsupported", "UNSUPPORTED_MULTIPLE_HEIGHTS": "unsupported",
    "UNSUPPORTED_MULTIPLE_BASES": "unsupported", "UNSUPPORTED_CENTROID": "unsupported",
    "UNSUPPORTED_BASE_SHAPE": "unsupported", "REGULAR_PYRAMID_NEEDS_REGULAR_BASE": "unsupported",
    "PLAN_TOO_LARGE": "unsupported", "PROOF_UNVERIFIABLE": "unsupported",
    # source grounding / clause role
    "QUOTE_NOT_IN_SOURCE": "grounding", "UNKNOWN_LABEL": "grounding", "PREDICATE_NOT_IN_QUOTE": "grounding",
    "PLANE_NOT_IN_QUOTE": "grounding", "ROLE_NOT_IN_QUOTE": "grounding", "OBJECT_NOT_IN_QUOTE": "grounding",
    "AMBIGUOUS_VALUE_QUOTE": "grounding", "UNGROUNDED_VALUE": "grounding", "SOURCE_OBJECT_MISMATCH": "grounding",
    "CONDITIONAL_CLAUSE": "grounding", "NEGATED_CLAUSE": "grounding", "GOAL_CLAUSE_NOT_PREMISE": "grounding",
    "AMBIGUOUS_FACT": "grounding", "AMBIGUOUS_REFERENCE": "grounding",
    # added with goal decomposition slice 1 (run `hybrid-goal-decomposition`): auxiliary-point gate
    "AUXILIARY_LABEL_COLLISION": "grounding", "AUXILIARY_RULE_MISMATCH": "malformed",
    "NOT_ASKED_IN_SOURCE": "grounding",                    # added by the slice 1 independent review (hybrid-slice1-review)
    "QUESTION_CLAUSE_NOT_PREMISE": "grounding",            # added by the S0/section review (hybrid-slice-review)
    # added with the section / intersection-line slice (hybrid-section-slice): geometric preconditions of the request
    "PARALLEL_PLANES": "contradictory", "SECTION_EMPTY": "contradictory",
    # goal-directed section slice (goal-directed-section-planning): taxonomy only; case labels/oracle unchanged
    "PLANE_NOT_UNIQUE": "figure_not_unique", "DERIVED_PLANE_IS_REFERENCE": "contradictory",
    "SECTION_PLANE_IS_FACE": "contradictory", "AUXILIARY_ONLY_FUNCTION": "malformed",
    # malformed facts / plan
    "SCHEMA_INVALID": "malformed", "FACT_INCOMPLETE": "malformed", "UNKNOWN_SOLID": "malformed", "NO_SOLID": "malformed",
    "DUPLICATE_CALL_ID": "malformed", "DEPENDENCY_CYCLE": "dependency", "DANGLING_DEPENDENCY": "dependency",
    # system faults (never a correct answer to a geometry question)
    "ENGINE_SELF_CHECK_FAILED": "system", "ENGINE_IR_INVALID": "system", "ENGINE_EXECUTION_FAILED": "system",
    "SCENE_BUILD_FAILED": "system", "LIVE_AI_DISABLED": "system", "PROVIDER_ERROR": "system",
}
GROUNDING_CODES = {k for k, v in REFUSAL_CLASS.items() if v == "grounding"}


# ── the two evaluations ─────────────────────────────────────────────────────────────────────────────────────────

def run(case: dict, arm: str):
    """arm 'facts' = evaluation A (verified Typed Facts → compiler); 'pipeline' = evaluation B (Vietnamese text → fake
    provider → fact-extraction adapter → compiler). Neither touches the network."""
    import json

    if arm == "facts":
        from app.ai.function_route import run_fact_route

        return run_fact_route(case["text"], {"facts": case["facts"]})
    from app.ai import fact_extraction as FE

    def fake(payload):
        return {"candidates": [{"finishReason": "STOP", "content": {"parts": [
            {"text": json.dumps({"facts": case["facts"]}, ensure_ascii=False)}]}}],
            "usageMetadata": {"promptTokenCount": 1, "candidatesTokenCount": 1}}
    return FE.run_ai_fact_route(case["text"], fake)


def classify(case: dict, r) -> dict:
    """Outcome + diagnosis. outcome ∈ correct_served · wrong_served · correct_refusal · false_refusal · wrong_refusal_class.
    diagnosis (for anything not correct) ∈ missing_primitive · missing_composition · ungrounded_derivation ·
    dependency_failure · underconstrained_or_contradictory · wrong_answer · keyword_dependence."""
    exp = case["expect"]
    if r.status == "SERVED":
        got = {cid: answer_square(v) for cid, v in (r.answers or {}).items()}
        if exp["status"] == "SERVED" and got.get("q") == exp["answer_sq"]:
            return {"outcome": "correct_served", "code": None}
        return {"outcome": "wrong_served", "code": None, "diagnosis": "wrong_answer", "got": r.answers}
    cls = REFUSAL_CLASS.get(r.code, "UNCLASSIFIED")
    if exp["status"] == "REFUSED":
        ok = cls == exp["refusal"] or (exp["refusal"] == "underconstrained" and cls == "figure_not_unique")
        return {"outcome": "correct_refusal" if ok else "wrong_refusal_class", "code": r.code, "class": cls}
    gap = case.get("gap", "")
    diag = ("keyword_dependence" if "keyword" in gap else "missing_composition" if gap
            else "ungrounded_derivation" if cls == "grounding"
            else "dependency_failure" if cls == "dependency" or r.code == "UNDERDETERMINED_POINT"
            else "missing_primitive" if cls == "unsupported"
            else "underconstrained_or_contradictory" if cls in ("contradictory", "figure_not_unique") else "other")
    return {"outcome": "false_refusal", "code": r.code, "class": cls, "diagnosis": diag}
