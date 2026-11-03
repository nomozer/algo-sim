"""Twelfth continuation (§IV, §IX): can the `/4` extraction contract carry the goals the planner `/23` composes?

The eleventh-continuation matrix (`planner-recomposition-matrix.json`) ran every case through the FLAT `TypedFact` route
(`run_fact_route`, route B), whose question facts carry `point_kind` descriptors. The production opt-in path that both
live protocols measure is `/4` (`TypedFactNextPayloadV2` → bridge → the same planner). This probe asks the `/4` bridge
the same goal shapes: an unnamed descriptor point inside a goal operand or a section plane, against named controls.
It also tallies `search_telemetry` classes over every served gold row of `student_language_probe.py` on `/4`.

Hand oracles on the C1 chart A(0,0,0) B(2,0,0) C(2,2,0) D(0,2,0) S(0,0,2): d(A, SC) = |AS × SC| / |SC| = 4√2 / 2√3 =
2√6/3; K = foot of A on SD = (0,1,1); plane through K ∥ (SBC) is x + z = 1, its section is the quadrilateral
(1,0,0) (1,2,0) (0,1,1) (0,0,1) of area √2 + √2/2 = 3√2/2. Offline, 0 provider calls. Usage: route_d4_representation_probe.py [out.json]
"""
import collections, copy, json, os, socket, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[5]
sys.path.insert(0, str(ROOT / 'backend'))
os.environ['ALLOW_LIVE_AI'] = '0'
def _offline(*_a, **_k): raise RuntimeError('OFFLINE_ONLY')
socket.socket.connect = _offline; socket.create_connection = _offline

from app.ai.adapter4_route import run_typed_fact_next_v2_route  # noqa: E402

_src = (HERE / 'student_language_probe.py').read_text(encoding='utf-8')
NS = {'__file__': str(HERE / 'student_language_probe.py')}
exec(compile(_src[:_src.index('# ---- scoring')], 'student_language_probe.py', 'exec'), NS)   # definitions only
STD, c1, M, P = NS['STD'], NS['c1'], NS['M'], NS['P']


def payload(question, goal_type, target, premises=(), section=None):
    text = f'{STD} {question}'
    p = c1(text, 'Cho hình chóp S.ABCD', [M('mg1', goal_type, target, question.rstrip('.'))], extra=list(premises))
    if section is not None:
        p['derived_sections'] = [section]
    return p


Q_PROJ = 'Tính độ dài đoạn thẳng nối C với hình chiếu vuông góc của A lên SB.'
Q_MID = 'Tính khoảng cách từ trung điểm của SC đến mặt phẳng (ABCD).'
Q_TWO = 'Tính độ dài đoạn thẳng nối trung điểm của SA với trung điểm của BC.'
Q_PL = 'Tính khoảng cách từ A đến đường thẳng SC.'
SEC_UNNAMED = 'Mặt phẳng (P) đi qua hình chiếu vuông góc của A lên SD và song song với (SBC). Tính diện tích thiết diện của hình chóp cắt bởi (P).'
SEC_NAMED = ('Gọi K là hình chiếu vuông góc của A lên SD. Mặt phẳng (P) đi qua K và song song với (SBC). '
             'Tính diện tích thiết diện của hình chóp cắt bởi (P).')


def section(through, quote):
    return {'section_id': 'sec1', 'plane_name': 'P', 'target_solid_id': 's1', 'plane_kind': 'through_point_parallel_plane',
            'through_point': through, 'parallel_plane': ['S', 'B', 'C'], 'quote': quote}


def area(question, through, sec_quote, premises=()):
    text = f'{STD} {question}'
    p = c1(text, 'Cho hình chóp S.ABCD', [M('mg1', 'area', {'section_id': 'sec1'},
                                            'Tính diện tích thiết diện của hình chóp cắt bởi (P)')], extra=list(premises))
    p['derived_sections'] = [section(through, sec_quote)]
    return p


ROWS = [
    # (id, C11 matrix analogue, /4 payload, expected: refused code or exact coefficient)
    ('U1_unnamed_foot_in_segment', 'C1a', payload(Q_PROJ, 'distance', {
        'segment': ['C', {'kind': 'orthogonal_projection_line', 'point': 'A', 'line': ['S', 'B']}]}), 'INVALID_MATH_GOAL'),
    ('U2_unnamed_midpoint_point_plane', 'C2/E-like', payload(Q_MID, 'distance', {
        'point': {'kind': 'midpoint', 'segment': ['S', 'C']}, 'plane': list('ABCD')}), 'INVALID_MATH_GOAL'),
    ('U3_two_unnamed_endpoints', 'D2', payload(Q_TWO, 'distance', {
        'segment': [{'kind': 'midpoint', 'segment': ['S', 'A']}, {'kind': 'midpoint', 'segment': ['B', 'C']}]}),
     'INVALID_MATH_GOAL'),
    ('U4_unnamed_point_of_section_plane', 'C5', area(SEC_UNNAMED, 'hình chiếu vuông góc của A lên SD',
                                                      'Mặt phẳng (P) đi qua hình chiếu vuông góc của A lên SD và song song với (SBC)'),
     'INVALID_QUALIFIED_REF'),
    ('N1_named_point_line_control', 'B1', payload(Q_PL, 'distance', {'point': 'A', 'line': ['S', 'C']}), '2√6/3'),
    ('N2_named_section_point_control', 'C5 named', area(
        SEC_NAMED, 'K', 'Mặt phẳng (P) đi qua K và song song với (SBC)',
        [P('orthogonal_projection_line', 'Gọi K là hình chiếu vuông góc của A lên SD', point='A', image='K', line=['S', 'D'])]),
     '3√2/2'),
]

rows = []
for rid, analogue, p, want in ROWS:
    r = run_typed_fact_next_v2_route(p)
    tel = (r.planner or {}).get('search_telemetry') or {}
    got = (r.answer_exact.get('mg1') or {}).get('coef') if r.status == 'SERVED' else r.code
    rows.append({'id': rid, 'c11_analogue': analogue, 'status': r.status, 'code': r.code, 'got': got, 'expected': want,
                 'agrees': got == want, 'classification': tel.get('classification')})
    print(f"{rid:36s} {r.status:8s} {str(got):24s} {'OK' if got == want else 'MISMATCH'} {tel.get('classification')}")

tally = collections.Counter()
for c in NS['CASES']:
    gold = c['extractions'].get('gold')
    if gold:
        r = run_typed_fact_next_v2_route(gold)
        if r.status == 'SERVED':
            tally[((r.planner or {}).get('search_telemetry') or {}).get('classification')] += 1
print(dict(tally))
assert all(r['agrees'] for r in rows)

if len(sys.argv) > 1:
    import subprocess
    head = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip()
    with open(sys.argv[1], 'x', encoding='utf-8', newline='\n') as f:
        json.dump({'classification': 'IMPLEMENTER_AUTHORED_DEVELOPMENT_DIAGNOSTIC', 'provider_calls': 0,
                   'identity': {'head': head}, 'rows': rows,
                   'student_probe_gold_served_on_d4_by_search_class': dict(tally)}, f, ensure_ascii=False, indent=1)
        f.write('\n')
