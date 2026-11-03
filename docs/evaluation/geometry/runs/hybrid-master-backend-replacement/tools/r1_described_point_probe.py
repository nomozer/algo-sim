"""Thirteenth continuation (R-1): do the eleventh-continuation compositions run END TO END on Hybrid `/4`?

Each row is raw source text plus a hand-authored `typed-fact-next/2` gold extraction that declares the unnamed point the
text describes in `described_points` and references it as `@id`. Every row runs the production opt-in path
`run_hybrid_offline` (verbatim-quote validation → bridge → Source Gate → planner → exact engine → Adapter /4) — the
same planner, Registry and engine as route B; no flat-route call, no adapter of its own. Oracles are hand coordinates
below, never read from the system. Also: the two C12 named controls, D1/D2, and adversarial extractions that must
refuse. IMPLEMENTER_AUTHORED_DEVELOPMENT_DIAGNOSTIC, offline, 0 provider calls. Usage: r1_described_point_probe.py [out]

Hand oracles. b22: A(0,0,0) B(2,0,0) C(2,2,0) D(0,2,0) S(0,0,2). b34: A(0,0,0) B(3,0,0) C(3,3,0) D(0,3,0) S(0,0,4).
- C1a/C4 (b34): H = foot of A on SD = (0, 48/25, 36/25); CH² = 9 + (27/25)² + (36/25)² = 306/25 ⇒ CH = 3√34/5; d(H,(ABCD)) = 36/25.
- C1b (b22): H = foot of A on (SBC) (x + z = 2) = (1,0,1); HB × HD = (2,2,2) ⇒ area √3.
- C2 (b22): O = (1,1,0); d(O, x + z = 2) = 1/√2 = √2/2.
- C3 (b22): M = (1,1,1); (SBD): x + y + z = 2 ⇒ I = (2/3,2/3,2/3); BI ∥ (−2,1,1) ⇒ sin² = 1/6, cos² = 5/6.
- C5 (b34): (SBC): 4x + 3z = 12; through H: 4x + 3z = 108/25; trapezoid with parallel sides 3 and 48/25 at distance 9/5
  ⇒ area 1107/250.
- C6a (b22): through (0,0,1) ⊥ SC: x + y − z = −1; quadrilateral (0,0,1) (1/2,0,3/2) (1/3,1/3,5/3) (0,1/2,3/2) ⇒ √3/6.
- C6b (b22): K = foot of O on SC = (4/3,4/3,2/3); plane x + y − 2z = 4/3; pentagon, xy-projection 40/27, cos = 2/√6
  ⇒ 20√6/27.
- C7: prism A(0,0,0) B(3,0,0) C(0,4,0) A'(0,0,4); foot of A on A'B = (48/25,0,36/25); CH² = 544/25 ⇒ 4√34/5.
- D1 (b22): midpoint of SC (1,1,1) projected on (ABCD) = (1,1,0); C(2,2,0) ⇒ √2. D2 (b22): (0,0,1)–(2,1,0) ⇒ √6.
"""
import collections, copy, json, os, socket, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[5]
sys.path.insert(0, str(ROOT / 'backend'))
os.environ['ALLOW_LIVE_AI'] = '0'
def _offline(*_a, **_k): raise RuntimeError('OFFLINE_ONLY')
socket.socket.connect = _offline; socket.create_connection = _offline

from app.ai.hybrid_offline import hybrid_offline_policy, run_hybrid_offline  # noqa: E402
from app.ai.typed_fact_next_extraction import ReplayExtractor  # noqa: E402

POLICY = hybrid_offline_policy({'HYBRID_ROUTE_D_PREVIEW': '1'})


def base(side, sa):
    sents = ['Cho hình chóp S.ABCD.', f'Đáy ABCD là hình vuông cạnh {side}.', 'SA vuông góc với (ABCD).', f'SA = {sa}.']
    prem = [{'kind': 'regular_polygon', 'args': {'vertices': list('ABCD'), 'side': str(side)},
             'quote': f'Đáy ABCD là hình vuông cạnh {side}', 'solid_id': 's1'},
            {'kind': 'perpendicular_line_plane', 'args': {'line': ['S', 'A'], 'plane': list('ABCD')},
             'quote': 'SA vuông góc với (ABCD)', 'solid_id': 's1'},
            {'kind': 'segment_length', 'args': {'segment': ['S', 'A'], 'value': str(sa)}, 'quote': f'SA = {sa}',
             'solid_id': 's1'}]
    return ' '.join(sents) + ' ', prem


def payload(text, premises, goals=(), sections=(), described=(), solid=('pyramid', 'S.ABCD', 'Cho hình chóp S.ABCD')):
    out = {'schema_version': 'typed-fact-next/2', 'problem_text': text, 'length_unit': '1',
           'solids': [{'solid_id': 's1', 'solid_type': solid[0], 'notation': solid[1], 'quote': solid[2]}],
           'premises': list(premises), 'derived_sections': list(sections), 'relations': [],
           'simulation_goals': [{'goal_id': 'sg1', 'kind': 'construct_object', 'target_solid_id': 's1', 'quote': solid[2]}],
           'math_goals': list(goals)}
    if described:
        out['described_points'] = list(described)
    return out


def G(gid, goal_type, target, quote):
    return {'goal_id': gid, 'kind': 'measurement', 'goal_type': goal_type, 'target': target, 'quote': quote,
            'solid_id': 's1'}


def DP(did, kind, quote, **ops):
    return {'described_id': did, 'kind': kind, 'quote': quote, **ops}


def SEC(through, quote, **plane):
    return {'section_id': 'sec1', 'plane_name': 'P', 'target_solid_id': 's1', 'quote': quote, 'through_point': through,
            'stated_intersections': [], **plane}


AREA_Q = 'Xác định thiết diện của hình chóp S.ABCD cắt bởi (P) và tính diện tích thiết diện đó'
b22, P22 = base(2, 2)
b34, P34 = base(3, 4)
S_MID = 'Gọi M là trung điểm của SC.'
S_O = 'Gọi O là giao điểm của AC và BD.'
MID_M = {'kind': 'midpoint', 'args': {'point': 'M', 'segment': ['S', 'C']}, 'quote': 'Gọi M là trung điểm của SC', 'solid_id': 's1'}
INT_O = {'kind': 'intersect_line_line', 'args': {'point': 'O', 'line1': ['A', 'C'], 'line2': ['B', 'D']},
         'quote': 'Gọi O là giao điểm của AC và BD', 'solid_id': 's1'}
H_SD = DP('h1', 'orthogonal_projection_line', 'hình chiếu vuông góc của A lên SD', point='A', line=['S', 'D'])


def row(rid, text, p, want, analogue):
    return {'id': rid, 'text': text, 'payload': p, 'want': want, 'c11_analogue': analogue}


ROWS = []
t = b34 + 'Tính độ dài đoạn thẳng nối điểm C với hình chiếu vuông góc của A lên SD.'
ROWS.append(row('C1a', t, payload(t, P34, [G('q1', 'distance', {'segment': ['C', '@h1']},
                'Tính độ dài đoạn thẳng nối điểm C với hình chiếu vuông góc của A lên SD')], described=[H_SD]),
                {'q1': '3√34/5'}, 'C1a-unhinted-proj-line-length'))
t = b22 + 'Tính diện tích tam giác tạo bởi B, D và hình chiếu vuông góc của A lên (SBC).'
ROWS.append(row('C1b', t, payload(t, P22, [G('q1', 'area', {'polygon': ['@h1', 'B', 'D']},
                'Tính diện tích tam giác tạo bởi B, D và hình chiếu vuông góc của A lên (SBC)')],
                described=[DP('h1', 'orthogonal_projection', 'hình chiếu vuông góc của A lên (SBC)', point='A',
                              plane=['S', 'B', 'C'])]), {'q1': '√3'}, 'C1b-unhinted-proj-plane-area'))
t = b22 + 'Tính khoảng cách từ giao điểm của AC và BD đến mặt phẳng (SBC).'
ROWS.append(row('C2', t, payload(t, P22, [G('q1', 'distance', {'point': '@o1', 'plane': ['S', 'B', 'C']},
                'Tính khoảng cách từ giao điểm của AC và BD đến mặt phẳng (SBC)')],
                described=[DP('o1', 'intersect_line_line', 'giao điểm của AC và BD', line1=['A', 'C'], line2=['B', 'D'])]),
                {'q1': '√2/2'}, 'C2-unhinted-inter-line-line-dist-plane'))
t = b22 + S_MID + ' Tính góc giữa đường thẳng nối điểm B với giao điểm của AM và (SBD) và mặt phẳng (ABCD).'
ROWS.append(row('C3', t, payload(t, [*P22, MID_M], [G('q1', 'angle', {'line': ['B', '@i1'], 'plane': list('ABCD')},
                'Tính góc giữa đường thẳng nối điểm B với giao điểm của AM và (SBD) và mặt phẳng (ABCD)')],
                described=[DP('i1', 'intersect_line_plane', 'giao điểm của AM và (SBD)', line=['A', 'M'],
                              plane=['S', 'B', 'D'])]), {'q1': '5/6'}, 'C3-unhinted-inter-line-plane-angle-line-plane'))
t = b34 + ('Tính độ dài đoạn thẳng nối điểm C với hình chiếu vuông góc của A lên SD. Tính khoảng cách từ hình chiếu '
           'vuông góc của A lên SD đến mặt phẳng (ABCD).')
ROWS.append(row('C4', t, payload(t, P34, [
    G('q1', 'distance', {'segment': ['C', '@h1']}, 'Tính độ dài đoạn thẳng nối điểm C với hình chiếu vuông góc của A lên SD'),
    G('q2', 'distance', {'point': '@h1', 'plane': list('ABCD')},
      'Tính khoảng cách từ hình chiếu vuông góc của A lên SD đến mặt phẳng (ABCD)')], described=[H_SD]),
    {'q1': '3√34/5', 'q2': '36/25'}, 'C4-multi-goal-shared-proj-line-reuse'))
q5 = 'Mặt phẳng (P) đi qua hình chiếu vuông góc của A lên SD và song song với mặt phẳng (SBC)'
t = b34 + q5 + '. ' + AREA_Q + '.'
ROWS.append(row('C5', t, payload(t, P34, [G('q1', 'area', {'section_id': 'sec1'}, AREA_Q)],
                [SEC('@h1', q5, plane_kind='through_point_parallel_plane', parallel_plane=['S', 'B', 'C'])],
                described=[H_SD]), {'q1': '1107/250'}, 'C5-flagship-unhinted-proj-line-parallel-plane-section-area'))
q6 = 'Mặt phẳng (P) đi qua trung điểm của SA và vuông góc với SC'
t = b22 + q6 + '. ' + AREA_Q + '.'
ROWS.append(row('C6a', t, payload(t, P22, [G('q1', 'area', {'section_id': 'sec1'}, AREA_Q)],
                [SEC('@m1', q6, plane_kind='through_point_perpendicular_line', perpendicular_line=['S', 'C'])],
                described=[DP('m1', 'midpoint', 'trung điểm của SA', segment=['S', 'A'])]),
                {'q1': '√3/6'}, 'C6a-unhinted-midpoint-perp-line-section-area'))
q6b = 'Mặt phẳng (P) đi qua hình chiếu vuông góc của O lên SC và vuông góc với SO'
t = b22 + S_O + ' ' + q6b + '. ' + AREA_Q + '.'
ROWS.append(row('C6b', t, payload(t, [*P22, INT_O], [G('q1', 'area', {'section_id': 'sec1'}, AREA_Q)],
                [SEC('@k1', q6b, plane_kind='through_point_perpendicular_line', perpendicular_line=['S', 'O'])],
                described=[DP('k1', 'orthogonal_projection_line', 'hình chiếu vuông góc của O lên SC', point='O',
                              line=['S', 'C'])]), {'q1': '20√6/27'}, 'C6b-unhinted-proj-line-perp-derived-SO-section-area'))
t = ("Cho hình lăng trụ đứng ABC.A'B'C'. Đáy ABC là tam giác vuông tại A. AB = 3, AC = 4, AA' = 4. Tính độ dài đoạn "
     "thẳng nối điểm C với hình chiếu vuông góc của A lên A'B.")
prism = [{'kind': 'right_prism', 'args': {'base': list('ABC'), 'top': ["A'", "B'", "C'"]},
          'quote': "Cho hình lăng trụ đứng ABC.A'B'C'", 'solid_id': 's1'},
         {'kind': 'right_angle', 'args': {'vertex': 'A', 'rays': ['B', 'C']}, 'quote': 'Đáy ABC là tam giác vuông tại A',
          'solid_id': 's1'},
         {'kind': 'segment_length', 'args': {'segment': ['A', 'B'], 'value': '3'}, 'quote': 'AB = 3', 'solid_id': 's1'},
         {'kind': 'segment_length', 'args': {'segment': ['A', 'C'], 'value': '4'}, 'quote': 'AC = 4', 'solid_id': 's1'},
         {'kind': 'segment_length', 'args': {'segment': ['A', "A'"], 'value': '4'}, 'quote': "AA' = 4", 'solid_id': 's1'}]
ROWS.append(row('C7', t, payload(t, prism, [G('q1', 'distance', {'segment': ['C', '@h1']},
                "Tính độ dài đoạn thẳng nối điểm C với hình chiếu vuông góc của A lên A'B")],
                described=[DP('h1', 'orthogonal_projection_line', "hình chiếu vuông góc của A lên A'B", point='A',
                              line=["A'", 'B'])], solid=('prism', "ABC.A'B'C'", "Cho hình lăng trụ đứng ABC.A'B'C'")),
                {'q1': '4√34/5'}, 'C7-prism-unhinted-proj-line-length'))
# named controls (C12 N1/N2) — no described point
t = b22 + 'Tính khoảng cách từ A đến đường thẳng SC.'
ROWS.append(row('N1', t, payload(t, P22, [G('q1', 'distance', {'point': 'A', 'line': ['S', 'C']},
                'Tính khoảng cách từ A đến đường thẳng SC')]), {'q1': '2√6/3'}, 'C12 N1'))
# D1 nested and D2 two described operands (the contract represents them; see the report for their status)
t = b22 + 'Tính độ dài đoạn thẳng nối điểm C với hình chiếu vuông góc của trung điểm SC lên (ABCD).'
ROWS.append(row('D1', t, payload(t, P22, [G('q1', 'distance', {'segment': ['C', '@h1']},
                'Tính độ dài đoạn thẳng nối điểm C với hình chiếu vuông góc của trung điểm SC lên (ABCD)')],
                described=[DP('h1', 'orthogonal_projection', 'hình chiếu vuông góc của trung điểm SC lên (ABCD)',
                              point='@m1', plane=list('ABCD')), DP('m1', 'midpoint', 'trung điểm SC', segment=['S', 'C'])]),
                {'q1': '√2'}, 'D1-nested-two-level-unnamed-descriptor'))
t = b22 + 'Tính độ dài đoạn thẳng nối trung điểm của SA với trung điểm của BC.'
ROWS.append(row('D2', t, payload(t, P22, [G('q1', 'distance', {'segment': ['@m1', '@m2']},
                'Tính độ dài đoạn thẳng nối trung điểm của SA với trung điểm của BC')],
                described=[DP('m1', 'midpoint', 'trung điểm của SA', segment=['S', 'A']),
                           DP('m2', 'midpoint', 'trung điểm của BC', segment=['B', 'C'])]),
                {'q1': '√6'}, 'D2-dual-unnamed-point-endpoints-in-binary-goal'))


def adv(rid, base_id, mutate, why):
    src = next(r for r in ROWS if r['id'] == base_id)
    p = copy.deepcopy(src['payload'])
    mutate(p)
    return {'id': rid, 'text': src['text'], 'payload': p, 'want': None, 'c11_analogue': why}


ADV = [
    adv('X1_role_swap', 'C1a', lambda p: p['described_points'][0].update(point='D', line=['S', 'A']),
        'operands swapped (D onto SA) under the same quote'),
    adv('X2_wrong_kind', 'C2', lambda p: p['described_points'][0].update(kind='intersect_line_plane', line=['A', 'C'],
                                                                        plane=['B', 'D', 'S'], line1=None, line2=None),
        'intersection of lines read as line–plane'),
    adv('X3_quote_elsewhere', 'C1a', lambda p: p['described_points'][0].update(quote='SA = 4'),
        'describing quote is not the phrase in the goal'),
    adv('X4_target_swapped', 'C2', lambda p: p['math_goals'][0]['target'].update(plane=['A', 'B', 'C', 'D']),
        'distance to (ABCD) instead of (SBC)'),
    adv('X5_invented_described', 'N1', lambda p: (p['math_goals'][0]['target'].update(point='@h1'),
                                                  p.update(described_points=[DP('h1', 'midpoint', 'đường thẳng SC',
                                                                                segment=['S', 'C'])])),
        'a described point the text does not describe'),
    adv('X6_section_wrong_desc', 'C5', lambda p: p['described_points'][0].update(point='S', line=['A', 'D']),
        'through-point description changed (S onto AD)'),
]
for a in ADV:
    for k in ('line1', 'line2'):
        for d in a['payload'].get('described_points', []):
            if d.get(k) is None:
                d.pop(k, None)


def run(r):
    out = run_hybrid_offline(r['text'], ReplayExtractor({r['text']: r['payload']}), policy=POLICY)
    route = out.response['route_d']
    got = {k: v.get('coef') for k, v in (route.get('answer_exact') or {}).items()} if route['status'] == 'SERVED' else None
    tel = (route.get('planner') or {}).get('search_telemetry') or {}
    return {'id': r['id'], 'c11_analogue': r['c11_analogue'], 'status': route['status'],
            'code': out.response['envelope'].get('reason_code'), 'answers': got, 'want': r['want'],
            'correct': r['want'] is not None and got == r['want'],
            'search_classification': tel.get('classification'),
            'functions': [c.get('fn') for c in route.get('source_provenance') or []]}


rows = [run(r) for r in ROWS] + [run(a) for a in ADV]
for x in rows:
    print(f"{x['id']:24s} {x['status']:8s} {str(x['code']):34s} {str(x['answers']):40s} "
          f"{'OK' if x['correct'] else ('SAFE' if x['want'] is None and x['status'] != 'SERVED' else '--')} "
          f"{x['search_classification']}")
summary = collections.Counter('ADVERSARIAL_SERVED' if x['want'] is None and x['status'] == 'SERVED'
                              else 'ADVERSARIAL_REFUSED' if x['want'] is None
                              else 'SERVED_CORRECT' if x['correct'] else 'WRONG_SERVED' if x['status'] == 'SERVED'
                              else 'REFUSED' for x in rows)
print(dict(summary))
if len(sys.argv) > 1:
    import subprocess
    head = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip()
    dirty = bool(subprocess.check_output(['git', 'status', '--porcelain', '--', 'backend/app'], cwd=ROOT, text=True).strip())
    with open(sys.argv[1], 'x', encoding='utf-8', newline='\n') as f:
        json.dump({'classification': 'IMPLEMENTER_AUTHORED_DEVELOPMENT_DIAGNOSTIC', 'provider_calls': 0,
                   'path': 'run_hybrid_offline (production opt-in /4)', 'identity': {'head': head, 'product_uncommitted': dirty},
                   'summary': dict(summary), 'rows': rows,
                   'cases': [{k: r[k] for k in ('id', 'text', 'payload', 'want')} for r in (*ROWS, *ADV)]},
                  f, ensure_ascii=False, indent=1)
        f.write('\n')
