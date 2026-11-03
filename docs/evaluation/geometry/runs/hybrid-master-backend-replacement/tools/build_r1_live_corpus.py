"""Fifteenth continuation: build the R-1 live described-point pilot corpus (7 strata, 18 cases = 18 requests).

IMPLEMENTER-AUTHORED DEVELOPMENT TEXTS ⇒ a live run is `LIVE_DEVELOPMENT_PILOT`, never held-out. No text reuses one of
the thirteenth-continuation probe rows (`r1_described_point_probe.py` C1a..C7, D1, D2) or an S-2 text verbatim, but the
question FRAMES do ("Tính độ dài đoạn thẳng nối … với …", the section request sentence, "tam giác tạo bởi"), 12 of 18
texts share one premise sentence, and D01 reuses the C7 prism's base (review MINOR-3) — R1-G adds two paraphrases
outside those frames. Every SERVED oracle is a hand string in the `parse_exact` grammar, and the builder recomputes its
square (or cos²) from hand coordinates in exact fractions below — never from the system. D1 / D2 / the reflection case
expect the registered capability boundary (a typed refusal); their would-be values are in `boundary_value` only.

Hand coordinates. P(a, h): A(0,0,0) B(a,0,0) C(a,a,0) D(0,a,0) S(0,0,h).
- A01 P(4,4): M = mid SB = (2,0,2); (SCD): y + z = 4 ⇒ d = 2/√2 = √2.
- A02 P(4,4): (SAC): x = y; foot of B = (2,2,0); d(foot, SC) = |(2,2,−4) × (1,1,−1)| / √3 = 2√2/√3 = 2√6/3.
- A03 P(4,3): O = (2,2,0) ⇒ SO² = 17.
- A04 P(2,2): M = mid SC = (1,1,1); AM ∥ (1,1,1) vs z = 0 ⇒ sin² = 1/3, cos² = 2/3.
- A05 P(2,2): M = mid AB = (1,0,0); SC × SM = (−4,2,−2) ⇒ area = √24/2 = √6.
- B01 P(3,4): H = foot of A on SB = (48/25, 0, 36/25); plane z = 36/25 cuts at λ = 16/25 ⇒ square 48/25 ⇒ 2304/625.
- B02 P(4,2): N = mid SD = (0,2,1); plane ⊥ SA through N is z = 1 ⇒ λ = 1/2 ⇒ square 2 ⇒ 4.
- C01 P(2,4): M = mid SC = (1,1,2) ⇒ d(M,(ABCD)) = 2, BM² = 1 + 1 + 4 = 6.
- C02 P(2,2): O = (1,1,0); plane ∥ (SAB) (y = 0) through O is y = 1 ⇒ trapezoid (0,1,0) (2,1,0) (1,1,1) (0,1,1) ⇒ 3/2.
- D01 prism A(0,0,0) B(3,0,0) C(0,4,0) A'(0,0,2): mid BC = (3/2,2,0) ⇒ A'M² = 41/4.
- D02 S.MNPQ, M(0,0,0) N(2,0,0) P(2,2,0) Q(0,2,0) S(0,0,2): mid SP = (1,1,1); (SNQ): x + y + z = 2 ⇒ 1/√3 = √3/3.
- F01 (D1) P(2,2): mid SC (1,1,1) → foot on (ABCD) (1,1,0); d(·, SB) = |(1,1,−2) × (1,0,−1)|/√2 = √3/√2 = √6/2.
- F02 (D2) P(2,2): mid SB (1,0,1), O (1,1,0) ⇒ √2.

Offline, 0 provider calls. Usage: build_r1_live_corpus.py <out.json>   (refuses to overwrite)
"""
import json, re, sys
from fractions import Fraction as F

AREA_Q = 'Xác định thiết diện của hình chóp S.ABCD cắt bởi (P) và tính diện tích thiết diện đó'


def pyramid(a, h, solid='S.ABCD'):
    s, base = solid[0], solid[2:]
    text = (f'Cho hình chóp {solid} có đáy {base} là hình vuông cạnh {a}, {s}{base[0]} vuông góc với mặt phẳng ({base}) '
            f'và {s}{base[0]} = {h}. ')
    return text, [
        {'kind': 'regular_polygon', 'args': {'vertices': list(base), 'side': str(a)},
         'quote': f'đáy {base} là hình vuông cạnh {a}', 'solid_id': 's1'},
        {'kind': 'perpendicular_line_plane', 'args': {'line': [s, base[0]], 'plane': list(base)},
         'quote': f'{s}{base[0]} vuông góc với mặt phẳng ({base})', 'solid_id': 's1'},
        {'kind': 'segment_length', 'args': {'segment': [s, base[0]], 'value': str(h)}, 'quote': f'{s}{base[0]} = {h}',
         'solid_id': 's1'}]


def gold(text, premises, goals=(), sections=(), described=(), solid=('pyramid', 'S.ABCD', 'Cho hình chóp S.ABCD'),
         unresolved=()):
    out = {'schema_version': 'typed-fact-next/2', 'problem_text': text, 'length_unit': '1',
           'solids': [{'solid_id': 's1', 'solid_type': solid[0], 'notation': solid[1], 'quote': solid[2]}],
           'premises': list(premises), 'derived_sections': list(sections), 'relations': [],
           'simulation_goals': [{'goal_id': 'sg1', 'kind': 'construct_object', 'target_solid_id': 's1', 'quote': solid[2]}],
           'math_goals': list(goals)}
    if described:
        out['described_points'] = list(described)
    if unresolved:      # the honest exit refuses the whole payload: no facts accompany it (S-2 convention)
        out.update(solids=[], premises=[], derived_sections=[], simulation_goals=[], math_goals=[],
                   unresolved=list(unresolved))
    return out


def G(gid, goal_type, target, quote):
    return {'goal_id': gid, 'kind': 'measurement', 'goal_type': goal_type, 'target': target, 'quote': quote,
            'solid_id': 's1'}


def DP(did, kind, quote, **ops):
    return {'described_id': did, 'kind': kind, 'quote': quote, **ops}


def SEC(through, quote, **plane):
    return {'section_id': 'sec1', 'plane_name': 'P', 'target_solid_id': 's1', 'quote': quote, 'through_point': through,
            'stated_intersections': [], **plane}


def U(kind, quote, roles=(), relations=()):
    return {'unresolved_id': 'u1', 'kind': kind, 'quote': quote, 'missing_roles': list(roles),
            'candidate_relations': list(relations)}


# ── independent exact check of every hand oracle ────────────────────────────────────────────────────────────────────

def sub(p, q): return tuple(x - y for x, y in zip(p, q))
def dot(p, q): return sum(x * y for x, y in zip(p, q))
def cross(p, q): return (p[1] * q[2] - p[2] * q[1], p[2] * q[0] - p[0] * q[2], p[0] * q[1] - p[1] * q[0])
def mid(p, q): return tuple((x + y) / 2 for x, y in zip(p, q))


def foot_line(p, a, b):
    d = sub(b, a)
    t = dot(sub(p, a), d) / dot(d, d)
    return tuple(x + t * y for x, y in zip(a, d))


def dist2_point_plane(p, a, b, c):
    n = cross(sub(b, a), sub(c, a))
    return dot(sub(p, a), n) ** 2 / dot(n, n)


def dist2_point_line(p, a, b):
    d = sub(b, a)
    w = cross(sub(p, a), d)
    return dot(w, w) / dot(d, d)


def squared(s):
    m = re.fullmatch(r'(?P<p>\d+)?(?:√(?P<r>\d+))?(?:/(?P<q>\d+))?', s)
    assert m and (m['p'] or m['r']), s
    p, r, q = F(m['p'] or 1), F(m['r'] or 1), F(m['q'] or 1)
    return p * p * r / (q * q)


def pts(a, h):
    a, h = F(a), F(h)
    return {'A': (0, 0, 0), 'B': (a, 0, 0), 'C': (a, a, 0), 'D': (0, a, 0), 'S': (0, 0, h)}


def area2_triangle(p, q, r):
    w = cross(sub(q, p), sub(r, p))
    return dot(w, w) / 4


def area2_convex(poly):                    # fan of triangles from the first vertex; returns the square of the area
    w = (0, 0, 0)
    for q, r in zip(poly[1:], poly[2:]):
        c = cross(sub(q, poly[0]), sub(r, poly[0]))
        w = tuple(x + y for x, y in zip(w, c))
    return dot(w, w) / 4


def cos2_to_base(v):                       # cos² of the angle between v and the plane z = 0
    return 1 - F(v[2]) ** 2 / dot(v, v)


def cut(p, q, coord, value):               # the point of segment pq where coordinate `coord` equals `value`
    t = (value - p[coord]) / (q[coord] - p[coord])
    return tuple(x + t * (y - x) for x, y in zip(p, q))


def square_section_area2(a, h, z):         # pyramid P(a, h) cut by z = const: square of side a·(1 − z/h)
    return (a * (1 - F(z) / h)) ** 4


V = pts(4, 4)
H_B = (F(2), F(2), F(0))                                                      # foot of B on x = y
assert dot(sub(V['B'], H_B), (1, 1, 0)) == 0 and dot(sub(V['B'], H_B), (0, 0, 1)) == 0
W = pts(3, 4)
H_A = foot_line(W['A'], W['S'], W['B'])
P2, P24 = pts(2, 2), pts(2, 4)
O2 = mid(P2['A'], P2['C'])                                                 # AC ∩ BD of the square
PR = {'A': (0, 0, 0), 'B': (F(3), 0, 0), 'C': (0, F(4), 0), "A'": (0, 0, F(2))}
C02_POLY = [cut(P2['A'], P2['D'], 1, O2[1]), cut(P2['B'], P2['C'], 1, O2[1]), cut(P2['S'], P2['C'], 1, O2[1]),
            cut(P2['S'], P2['D'], 1, O2[1])]                              # plane y = y(O) ∥ (SAB): y = 0
CHECK = {
    'R1-A01': {'distance': [dist2_point_plane(mid(V['S'], V['B']), V['S'], V['C'], V['D'])]},
    'R1-A02': {'distance': [dist2_point_line(H_B, V['S'], V['C'])]},
    'R1-A03': {'distance': [dot(sub(pts(4, 3)['S'], (2, 2, 0)), sub(pts(4, 3)['S'], (2, 2, 0)))]},
    'R1-A04': {'angle_cos_sq': [cos2_to_base(sub(mid(P2['S'], P2['C']), P2['A']))]},
    'R1-A05': {'area': [area2_triangle(P2['S'], P2['C'], mid(P2['A'], P2['B']))]},
    'R1-B01': {'area': [square_section_area2(3, 4, H_A[2])]},
    'R1-B02': {'area': [square_section_area2(4, 2, mid(pts(4, 2)['S'], pts(4, 2)['D'])[2])]},   # plane ⊥ SA is z = const
    'R1-C01': {'distance': [mid(P24['S'], P24['C'])[2] ** 2,
                            dot(sub(P24['B'], mid(P24['S'], P24['C'])), sub(P24['B'], mid(P24['S'], P24['C'])))]},
    'R1-C02': {'area': [area2_convex(C02_POLY)]},
    'R1-D01': {'distance': [dot(sub(PR["A'"], mid(PR['B'], PR['C'])), sub(PR["A'"], mid(PR['B'], PR['C'])))]},
    'R1-D02': {'distance': [dist2_point_plane(mid(P2['S'], P2['C']), P2['S'], P2['B'], P2['D'])]},   # N→B, P→C, Q→D
    'R1-G01': {'angle_cos_sq': [cos2_to_base(sub(mid(P24['S'], P24['C']), P24['A']))]},
    'R1-G02': {'distance': [dist2_point_plane(mid(P2['S'], P2['B']), P2['S'], P2['C'], P2['D'])]},
}
assert H_A == (F(48, 25), 0, F(36, 25)), H_A
assert C02_POLY == [(0, 1, 0), (2, 1, 0), (1, 1, 1), (0, 1, 1)], C02_POLY
BOUNDARY = {'R1-F01': dist2_point_line((F(1), F(1), F(0)), P2['S'], P2['B']),          # foot of mid SC on (ABCD)
            'R1-F02': dot(sub(mid(P2['S'], P2['B']), O2), sub(mid(P2['S'], P2['B']), O2)),
            'R1-F03': dist2_point_plane(sub(tuple(2 * x for x in P2['C']), P2['A']), P2['S'], P2['B'], P2['D'])}


# ── cases ───────────────────────────────────────────────────────────────────────────────────────────────────────────

CASES = []


def case(cid, stratum, text, g, outcome, oracle=None, codes=(), **notes):
    e = {'outcome': outcome, 'is_ambiguous': outcome == 'CLARIFY'}
    if oracle is not None:
        e['oracle'] = oracle
    if codes:
        e['allowed_clarification_codes'] = list(codes)
    assert g['problem_text'] == text
    for q in (x['quote'] for k in ('premises', 'math_goals', 'described_points', 'derived_sections', 'unresolved',
                                   'simulation_goals', 'solids') for x in g.get(k) or ()):
        assert q in text, (cid, q)
    CASES.append({'id': cid, 'stratum': stratum, 'source': 'build_r1_live_corpus.py (new, implementer)',
                  'problem_text': text, 'gold_extraction': g, 'expected': e, **notes})


# R1-A: one unnamed described point in a measurement goal
t0, p = pyramid(4, 4)
q = 'Tính khoảng cách từ trung điểm của SB đến mặt phẳng (SCD)'
case('R1-A01', 'R1-A', t0 + q + '.', gold(t0 + q + '.', p, [G('q1', 'distance', {'point': '@m1', 'plane': list('SCD')}, q)],
     described=[DP('m1', 'midpoint', 'trung điểm của SB', segment=['S', 'B'])]), 'SERVED', {'distance': ['√2']},
     described_dependencies=['m1 = midpoint(SB)'])
q = 'Tính khoảng cách từ hình chiếu vuông góc của B lên mặt phẳng (SAC) đến đường thẳng SC'
case('R1-A02', 'R1-A', t0 + q + '.', gold(t0 + q + '.', p, [G('q1', 'distance', {'point': '@h1', 'line': ['S', 'C']}, q)],
     described=[DP('h1', 'orthogonal_projection', 'hình chiếu vuông góc của B lên mặt phẳng (SAC)', point='B',
                   plane=list('SAC'))]), 'SERVED', {'distance': ['2√6/3']},
     described_dependencies=['h1 = orthogonal_projection(B, (SAC))'])
t1, p1 = pyramid(4, 3)
q = 'Tính độ dài đoạn thẳng nối S với giao điểm của AC và BD'
case('R1-A03', 'R1-A', t1 + q + '.', gold(t1 + q + '.', p1, [G('q1', 'distance', {'segment': ['S', '@o1']}, q)],
     described=[DP('o1', 'intersect_line_line', 'giao điểm của AC và BD', line1=['A', 'C'], line2=['B', 'D'])]),
     'SERVED', {'distance': ['√17']}, described_dependencies=['o1 = AC ∩ BD'])
t2, p2 = pyramid(2, 2)
q = 'Tính góc giữa đường thẳng nối A với trung điểm của SC và mặt phẳng (ABCD)'
case('R1-A04', 'R1-A', t2 + q + '.', gold(t2 + q + '.', p2, [G('q1', 'angle', {'line': ['A', '@m1'], 'plane': list('ABCD')}, q)],
     described=[DP('m1', 'midpoint', 'trung điểm của SC', segment=['S', 'C'])]), 'SERVED', {'angle_cos_sq': ['2/3']},
     described_dependencies=['m1 = midpoint(SC)'])
q = 'Tính diện tích tam giác tạo bởi S, C và trung điểm của AB'
case('R1-A05', 'R1-A', t2 + q + '.', gold(t2 + q + '.', p2, [G('q1', 'area', {'polygon': ['S', 'C', '@m1']}, q)],
     described=[DP('m1', 'midpoint', 'trung điểm của AB', segment=['A', 'B'])]), 'SERVED', {'area': ['√6']},
     described_dependencies=['m1 = midpoint(AB)'])

# R1-B: an unnamed described point defines an auxiliary section plane
t3, p3 = pyramid(3, 4)
s = 'Mặt phẳng (P) đi qua hình chiếu vuông góc của A lên SB và song song với mặt phẳng (ABCD)'
txt = t3 + s + '. ' + AREA_Q + '.'
case('R1-B01', 'R1-B', txt, gold(txt, p3, [G('q1', 'area', {'section_id': 'sec1'}, AREA_Q)],
     [SEC('@h1', s, plane_kind='through_point_parallel_plane', parallel_plane=list('ABC'))],   # ≤ 3 labels name a plane
     described=[DP('h1', 'orthogonal_projection_line', 'hình chiếu vuông góc của A lên SB', point='A', line=['S', 'B'])]),
     'SERVED', {'area': ['2304/625']}, described_dependencies=['h1 = orthogonal_projection(A, SB)', '(P) ∋ h1, (P) ∥ (ABCD)'])
t4, p4 = pyramid(4, 2)
s = 'Mặt phẳng (P) đi qua trung điểm của SD và vuông góc với SA'
txt = t4 + s + '. ' + AREA_Q + '.'
case('R1-B02', 'R1-B', txt, gold(txt, p4, [G('q1', 'area', {'section_id': 'sec1'}, AREA_Q)],
     [SEC('@n1', s, plane_kind='through_point_perpendicular_line', perpendicular_line=['S', 'A'])],
     described=[DP('n1', 'midpoint', 'trung điểm của SD', segment=['S', 'D'])]), 'SERVED', {'area': ['4']},
     described_dependencies=['n1 = midpoint(SD)', '(P) ∋ n1, (P) ⊥ SA'])

# R1-C: one described point reused by two goals; a chain of several functions
t5, p5 = pyramid(2, 4)
qa = 'Tính khoảng cách từ trung điểm của SC đến mặt phẳng (ABCD)'
qb = 'Tính độ dài đoạn thẳng nối B với trung điểm của SC'
txt = t5 + qa + '. ' + qb + '.'
case('R1-C01', 'R1-C', txt, gold(txt, p5, [G('q1', 'distance', {'point': '@m1', 'plane': list('ABCD')}, qa),
                                          G('q2', 'distance', {'segment': ['B', '@m1']}, qb)],
     described=[DP('m1', 'midpoint', 'trung điểm của SC', segment=['S', 'C'])]), 'SERVED', {'distance': ['2', '√6']},
     described_dependencies=['m1 = midpoint(SC), shared by q1 and q2'])
s = 'Mặt phẳng (P) đi qua giao điểm của AC và BD và song song với mặt phẳng (SAB)'
txt = t2 + s + '. ' + AREA_Q + '.'
case('R1-C02', 'R1-C', txt, gold(txt, p2, [G('q1', 'area', {'section_id': 'sec1'}, AREA_Q)],
     [SEC('@o1', s, plane_kind='through_point_parallel_plane', parallel_plane=list('SAB'))],
     described=[DP('o1', 'intersect_line_line', 'giao điểm của AC và BD', line1=['A', 'C'], line2=['B', 'D'])]),
     'SERVED', {'area': ['3/2']}, described_dependencies=['o1 = AC ∩ BD', '(P) ∋ o1, (P) ∥ (SAB)'])

# R1-D: other solid, other labels, other order of the givens
txt = ("Cho hình lăng trụ đứng ABC.A'B'C' có đáy ABC là tam giác vuông tại A, AB = 3, AC = 4 và AA' = 2. "
       "Tính độ dài đoạn thẳng nối A' với trung điểm của BC.")
prism = [{'kind': 'right_prism', 'args': {'base': list('ABC'), 'top': ["A'", "B'", "C'"]},
          'quote': "Cho hình lăng trụ đứng ABC.A'B'C'", 'solid_id': 's1'},
         {'kind': 'right_angle', 'args': {'vertex': 'A', 'rays': ['B', 'C']}, 'quote': 'đáy ABC là tam giác vuông tại A',
          'solid_id': 's1'},
         {'kind': 'segment_length', 'args': {'segment': ['A', 'B'], 'value': '3'}, 'quote': 'AB = 3', 'solid_id': 's1'},
         {'kind': 'segment_length', 'args': {'segment': ['A', 'C'], 'value': '4'}, 'quote': 'AC = 4', 'solid_id': 's1'},
         {'kind': 'segment_length', 'args': {'segment': ['A', "A'"], 'value': '2'}, 'quote': "AA' = 2", 'solid_id': 's1'}]
q = "Tính độ dài đoạn thẳng nối A' với trung điểm của BC"
case('R1-D01', 'R1-D', txt, gold(txt, prism, [G('q1', 'distance', {'segment': ["A'", '@m1']}, q)],
     described=[DP('m1', 'midpoint', 'trung điểm của BC', segment=['B', 'C'])],
     solid=('prism', "ABC.A'B'C'", "Cho hình lăng trụ đứng ABC.A'B'C'")), 'SERVED', {'distance': ['√41/2']},
     described_dependencies=['m1 = midpoint(BC)'])
txt = ('Cho hình chóp S.MNPQ có SM = 2, SM vuông góc với mặt phẳng (MNPQ) và đáy MNPQ là hình vuông cạnh 2. '
       'Tính khoảng cách từ trung điểm của SP đến mặt phẳng (SNQ).')
_, pm = pyramid(2, 2, 'S.MNPQ')
q = 'Tính khoảng cách từ trung điểm của SP đến mặt phẳng (SNQ)'
case('R1-D02', 'R1-D', txt, gold(txt, [pm[2], pm[1], pm[0]], [G('q1', 'distance', {'point': '@k1', 'plane': list('SNQ')}, q)],
     described=[DP('k1', 'midpoint', 'trung điểm của SP', segment=['S', 'P'])],
     solid=('pyramid', 'S.MNPQ', 'Cho hình chóp S.MNPQ')), 'SERVED', {'distance': ['√3/3']},
     described_dependencies=['k1 = midpoint(SP); the vertex M is NOT the unnamed midpoint'])

# R1-E: the honest exit — the description does not determine one point
q = 'Tính độ dài đoạn thẳng nối C với trung điểm của một cạnh bên'
case('R1-E01', 'R1-E', t2 + q + '.', gold(t2 + q + '.', p2, unresolved=[
     U('ambiguous', 'trung điểm của một cạnh bên', ['source_point'], ['midpoint'])]), 'CLARIFY',
     codes=('AMBIGUOUS', 'MISSING_DATA'), why='four lateral edges, three different lengths (3, √6, √3)')
q = 'Tính khoảng cách từ hình chiếu vuông góc của A đến mặt phẳng (SCD)'
case('R1-E02', 'R1-E', t2 + q + '.', gold(t2 + q + '.', p2, unresolved=[
     U('missing_operand', 'hình chiếu vuông góc của A', ['target_line_or_plane'], ['orthogonal_projection'])]),
     'CLARIFY', codes=('MISSING_DATA', 'AMBIGUOUS'), why='projected onto what is not stated')

# R1-F: the registered boundary — D1 nested, D2 two described operands, a primitive the library lacks
q = 'Tính khoảng cách từ hình chiếu vuông góc của trung điểm của SC lên mặt phẳng (ABCD) đến đường thẳng SB'
case('R1-F01', 'R1-F', t2 + q + '.', gold(t2 + q + '.', p2, [G('q1', 'distance', {'point': '@h1', 'line': ['S', 'B']}, q)],
     described=[DP('h1', 'orthogonal_projection', 'hình chiếu vuông góc của trung điểm của SC lên mặt phẳng (ABCD)',
                   point='@m1', plane=list('ABCD')), DP('m1', 'midpoint', 'trung điểm của SC', segment=['S', 'C'])]),
     'REFUSED_UNSUPPORTED', boundary='D1 nested described point', boundary_value='√6/2')
q = 'Tính độ dài đoạn thẳng nối trung điểm của SB với giao điểm của AC và BD'
case('R1-F02', 'R1-F', t2 + q + '.', gold(t2 + q + '.', p2, [G('q1', 'distance', {'segment': ['@m1', '@o1']}, q)],
     described=[DP('m1', 'midpoint', 'trung điểm của SB', segment=['S', 'B']),
                DP('o1', 'intersect_line_line', 'giao điểm của AC và BD', line1=['A', 'C'], line2=['B', 'D'])]),
     'REFUSED_UNSUPPORTED', boundary='D2 two described operands', boundary_value='√2')
q = 'Tính khoảng cách từ điểm đối xứng với A qua C đến mặt phẳng (SBD)'
case('R1-F03', 'R1-F', t2 + q + '.', gold(t2 + q + '.', p2, unresolved=[U('unsupported', 'điểm đối xứng với A qua C')]),
     'REFUSED_UNSUPPORTED', boundary_value='2√3',
     boundary='a reflected point is no DescribedPointSpec kind (typed_fact_next.py), so it has no @-reference')

# R1-G: paraphrases outside the standard frames (C15 review MINOR-3) — the Source Gate may not read them; the expected
# outcome stays the mathematically right serve, so a refusal here is a measured deterministic false refusal
t5b, p5b = pyramid(2, 4)
q = 'Tính góc giữa đường thẳng đi qua A và trung điểm của SC với mặt phẳng (ABCD)'
case('R1-G01', 'R1-G', t5b + q + '.', gold(t5b + q + '.', p5b, [G('q1', 'angle', {'line': ['A', '@m1'],
                                                                                 'plane': list('ABCD')}, q)],
     described=[DP('m1', 'midpoint', 'trung điểm của SC', segment=['S', 'C'])]), 'SERVED', {'angle_cos_sq': ['1/3']},
     described_dependencies=['m1 = midpoint(SC)'], paraphrase='"đường thẳng đi qua A và …" for "đường thẳng nối A với …"')
q = 'Tính khoảng cách từ điểm chính giữa cạnh SB tới mặt phẳng (SCD)'
case('R1-G02', 'R1-G', t2 + q + '.', gold(t2 + q + '.', p2, [G('q1', 'distance', {'point': '@m1', 'plane': list('SCD')}, q)],
     described=[DP('m1', 'midpoint', 'điểm chính giữa cạnh SB', segment=['S', 'B'])]), 'SERVED', {'distance': ['√2/2']},
     described_dependencies=['m1 = midpoint(SB)'], paraphrase='"điểm chính giữa cạnh" for "trung điểm của", "tới" for "đến"')

for c in CASES:                                              # every hand oracle agrees with the exact coordinates
    e = c['expected']
    if c.get('boundary_value'):
        assert squared(c['boundary_value']) == BOUNDARY[c['id']], c['id']
    if e['outcome'] != 'SERVED':
        continue
    got = {k: sorted(F(v) if k == 'angle_cos_sq' else squared(v) for v in vs) for k, vs in e['oracle'].items()}
    want = {k: sorted(vs) for k, vs in CHECK[c['id']].items()}
    assert got == want, (c['id'], got, want)
assert len(CASES) == 18 and len({c['problem_text'] for c in CASES}) == 18 and set(CHECK) == {
    c['id'] for c in CASES if c['expected']['outcome'] == 'SERVED'}

if __name__ == '__main__':
    with open(sys.argv[1], 'x', encoding='utf-8', newline='\n') as f:
        json.dump({'schema': 'r1-live-pilot-corpus/1', 'study': 'R-1',
                   'measurement_class_if_run_live': 'LIVE_DEVELOPMENT_PILOT',
                   'author': 'implementer (agent), fifteenth continuation — not independent, not held-out',
                   'protocol': 'r1-live-pilot-protocol.md', 'cases': CASES}, f, ensure_ascii=False, indent=1)
        f.write('\n')
    print(f'{len(CASES)} cases written to {sys.argv[1]}')
