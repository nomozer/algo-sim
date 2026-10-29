"""Generate probe cases (pure JSON, tree independent). Output: cases_probe.json"""
import json
from copy import deepcopy
from pathlib import Path
D = Path(__file__).parent
load = lambda n: json.loads((D / n).read_text(encoding='utf-8'))
PR, N2, A01, A10 = load('base_C.json'), load('base_N2v2.json'), load('base_A3-DEV-01.json'), load('base_A3-DEV-10.json')
CYL, CONE, SPH, DEMO1 = load('base_demo6a.json'), load('base_demo6b.json'), load('base_demo6c.json'), load('base_demo1.json')
cases = {}


def _lab(x): return x.split('::')[-1] if isinstance(x, str) else ''
def _j(v): return ''.join(map(_lab, v)) if isinstance(v, list) else _lab(v)


def question(gtype, t):
    """Source sentence that names the asked object, so the source gate does not reject a probe for its quote."""
    if not isinstance(t, dict):
        return None
    k = set(t) - {'solid', 'solid_id', 'foo', 'section_id'}
    g = lambda key: _j(t.get(key))
    if gtype == 'distance':
        if k == {'segment'}: return f'Tính độ dài {g("segment")}.'
        if k == {'point', 'plane'}: return f'Tính khoảng cách từ {g("point")} đến mặt phẳng ({g("plane")}).'
        if k == {'point', 'line'}: return f'Tính khoảng cách từ {g("point")} đến đường thẳng {g("line")}.'
        if k == {'line1', 'line2'}: return f'Tính khoảng cách giữa hai đường thẳng {g("line1")} và {g("line2")}.'
        if k == {'line', 'plane'}: return f'Tính khoảng cách giữa đường thẳng {g("line")} và mặt phẳng ({g("plane")}).'
        if k == {'plane1', 'plane2'}: return f'Tính khoảng cách giữa hai mặt phẳng ({g("plane1")}) và ({g("plane2")}).'
    if gtype == 'angle':
        if k == {'line', 'plane'}: return f'Tính góc giữa đường thẳng {g("line")} và mặt phẳng ({g("plane")}).'
        if k == {'line1', 'line2'}: return f'Tính góc giữa hai đường thẳng {g("line1")} và {g("line2")}.'
        if k == {'plane1', 'plane2'}: return f'Tính góc giữa hai mặt phẳng ({g("plane1")}) và ({g("plane2")}).'
    if gtype == 'area' and k == {'polygon'}: return f'Tính diện tích tam giác {g("polygon")}.'
    return None


def goal(base, gtype, target, gsid='__absent__', gid='q', keep_others=False, extra=None):
    p = deepcopy(base)
    same = [g['quote'] for g in base.get('math_goals', []) if g.get('goal_type') == gtype]
    qs = question(gtype, target)
    if p['problem_text'].startswith('Cho lăng trụ đứng ABC.A\'B\'C\'. Đáy'):     # prism base: replace its question
        p['problem_text'] = p['problem_text'].rsplit(' Tính', 1)[0]
    if qs:
        p['problem_text'] += ' ' + qs
    elif gtype == 'volume' and not same:
        qs = 'Tính thể tích khối đa diện.'; p['problem_text'] += ' ' + qs
    elif gtype in ('lateral_area', 'radius', 'area') and not same:
        qs = {'lateral_area': 'Tính diện tích xung quanh.', 'radius': 'Tính bán kính.', 'area': 'Tính diện tích toàn phần.'}[gtype]
        p['problem_text'] += ' ' + qs
    quote = qs or (same[0] if same else p['problem_text'].split('.')[0] + '.')
    q = {'goal_id': gid, 'kind': 'measurement', 'goal_type': gtype, 'target': target, 'quote': quote}
    if gsid != '__absent__':
        q['solid_id'] = gsid
    if extra:
        q.update(extra)
    others = [g for g in p.get('math_goals', []) if keep_others and g.get('goal_id') != gid]
    p['math_goals'] = others + [q]
    return p


def add(name, p, **kw): cases[name] = {'payload': p, **kw}


# ── 2. per-kind closed grammar on the prism ABC.A'B'C' (pr) ─────────────────────────────────────────────────────
ALT = {
    'distance': {'segment': {'segment': ["B'", 'C']}, 'point_plane': {'point': "A'", 'plane': ['A', 'B', 'C']},
                 'point_line': {'point': "A'", 'line': ['B', 'C']}, 'line1_line2': {'line1': ['A', "A'"], 'line2': ['B', 'C']},
                 'line_plane': {'line': ["B'", "C'"], 'plane': ['A', 'B', 'C']},
                 'plane1_plane2': {'plane1': ['A', 'B', 'C'], 'plane2': ["A'", "B'", "C'"]}},
    'angle': {'line_plane': {'line': ["B'", 'C'], 'plane': ['A', 'B', 'C']}, 'line1_line2': {'line1': ["A'", 'B'], 'line2': ['A', 'C']},
              'plane1_plane2': {'plane1': ["A'", 'B', 'C'], 'plane2': ['A', 'B', 'C']}},
    'area': {'polygon': {'polygon': ['A', 'B', 'C']}},
}
SCOPE_ADD = {'solid': {'solid': 'pr'}, 'solid_id': {'solid_id': 'pr'}, 'notation': {'solid': "ABC.A'B'C'"},
             'both': {'solid': 'pr', 'solid_id': 'pr'}, 'unknown_solid': {'solid': 'zz'}, 'unknown_solid_id': {'solid_id': 'zz'},
             'null_solid': {'solid': None}, 'null_solid_id': {'solid_id': None}, 'extra_key': {'foo': 1},
             'section_id': {'section_id': 'sec_x'}, 'solid_int': {'solid': 5}, 'solid_id_list': {'solid_id': ['pr']},
             'canonical_notation': {'solid': "ABC.A'B'C'"}, 'empty_solid': {'solid': ''}}
for gt, alts in ALT.items():
    for an, t in alts.items():
        add(f'G.{gt}.{an}.plain', goal(PR, gt, t), expect='SERVE_OR_CAPABILITY')
        add(f'G.{gt}.{an}.goal_sid', goal(PR, gt, t, 'pr'), expect='SERVE_OR_CAPABILITY')
        add(f'G.{gt}.{an}.goal_sid_null', goal(PR, gt, t, None), expect='INFO')
        add(f'G.{gt}.{an}.goal_sid_unknown', goal(PR, gt, t, 'zz'), expect='REFUSE')
        add(f'G.{gt}.{an}.qualified', goal(PR, gt, {k: (f'pr::{v}' if isinstance(v, str) else [f'pr::{x}' for x in v]) for k, v in t.items()}), expect='SERVE_OR_CAPABILITY')
        add(f'G.{gt}.{an}.foreign_ns', goal(PR, gt, {k: (f'zz::{v}' if isinstance(v, str) else [f'zz::{x}' for x in v]) for k, v in t.items()}), expect='REFUSE')
        for sn, s in SCOPE_ADD.items():
            add(f'G.{gt}.{an}.+{sn}', goal(PR, gt, {**t, **s}), expect='REFUSE')
            add(f'G.{gt}.{an}.+{sn}.goal_sid', goal(PR, gt, {**t, **s}, 'pr'), expect='REFUSE')
        # half alternatives / mixes
        keys = list(t)
        if len(keys) == 2:
            add(f'G.{gt}.{an}.half+solid', goal(PR, gt, {keys[0]: t[keys[0]], 'solid': 'pr'}), expect='REFUSE')
            add(f'G.{gt}.{an}.half+solid_id', goal(PR, gt, {keys[1]: t[keys[1]], 'solid_id': 'pr'}), expect='REFUSE')
# alias duplicates (S/A-prime vs qualified)
add('G.distance.segment.dup_qualified', goal(PR, 'distance', {'segment': ['A', 'pr::A']}), expect='REFUSE')
add('G.distance.point_plane.dup_qualified', goal(PR, 'distance', {'point': "A'", 'plane': ['A', 'B', 'pr::A']}), expect='REFUSE')
add('G.distance.point_plane.dup_qual4', goal(PR, 'distance', {'point': "A'", 'plane': ['A', 'B', 'C', 'pr::A']}), expect='REFUSE')
add('G.distance.segment.string', goal(PR, 'distance', {'segment': "B'C"}), expect='REFUSE')
add('G.distance.segment.three', goal(PR, 'distance', {'segment': ['A', 'B', 'C']}), expect='REFUSE')
add('G.distance.point.list', goal(PR, 'distance', {'point': ["A'"], 'plane': ['A', 'B', 'C']}), expect='REFUSE')
add('G.distance.point.int', goal(PR, 'distance', {'point': 5, 'plane': ['A', 'B', 'C']}), expect='REFUSE')
add('G.distance.nested_obj', goal(PR, 'distance', {'segment': [{'ref': 'A'}, 'B']}), expect='REFUSE')
add('G.distance.only_solid', goal(PR, 'distance', {'solid': 'pr'}), expect='REFUSE')
add('G.distance.only_solid_id', goal(PR, 'distance', {'solid_id': 'pr'}), expect='REFUSE')
add('G.distance.empty', goal(PR, 'distance', {}), expect='REFUSE')
add('G.distance.mixed_alts', goal(PR, 'distance', {'segment': ['A', 'B'], 'point': "A'", 'plane': ['A', 'B', 'C']}), expect='REFUSE')
add('G.angle.segment', goal(PR, 'angle', {'segment': ['A', 'B']}), expect='REFUSE')
add('G.angle.point_plane', goal(PR, 'angle', {'point': "A'", 'plane': ['A', 'B', 'C']}), expect='REFUSE')
# solid-valued on prism
for gt in ('volume', 'area', 'radius', 'lateral_area'):
    for tn, t in {'solid': {'solid': 'pr'}, 'solid_id': {'solid_id': 'pr'}, 'both': {'solid': 'pr', 'solid_id': 'pr'},
                  'notation': {'solid': "ABC.A'B'C'"}, 'notation+id': {'solid': "ABC.A'B'C'", 'solid_id': 'pr'},
                  'conflict': {'solid': 'pr', 'solid_id': 'zz'}, 'unknown': {'solid': 'zz'}, 'unknown_id': {'solid_id': 'zz'},
                  'extra': {'solid': 'pr', 'foo': 1}, 'segment+solid': {'solid': 'pr', 'segment': ['A', 'B']},
                  'null': {'solid': None}, 'int': {'solid': 3}, 'empty_str': {'solid': ''}}.items():
        add(f'V.{gt}.{tn}', goal(PR, gt, t), expect='INFO')
        add(f'V.{gt}.{tn}.goal_sid', goal(PR, gt, t, 'pr'), expect='INFO')
    add(f'V.{gt}.goal_sid_conflict', goal(PR, gt, {'solid': 'pr'}, 'zz'), expect='REFUSE')
# extra goal-level fields present as null (explicit-presence handling)
add('X.measurement.numerator_null', goal(PR, 'distance', ALT['distance']['segment'], extra={'numerator_solid_id': None}), expect='INFO')
add('X.measurement.parent_null', goal(PR, 'distance', ALT['distance']['segment'], extra={'parent_solid_id': None}), expect='INFO')
add('X.measurement.target_null', goal(PR, 'distance', None), expect='REFUSE')
add('X.measurement.goal_type_null_target_ok', goal(PR, None, ALT['distance']['segment']), expect='REFUSE')

# ── curved and section-based solid-valued goals ─────────────────────────────────────────────────────────────────
CUR = {'cyl': (CYL, 'cyl', "O.O'", 'sec_axial'), 'cone': (CONE, 'cone_main', 'S.O', 'sec_axial'), 'sph': (SPH, 'sph', '(S)', 'sec_sph')}
for cn, (base, sid, notation, sec) in CUR.items():
    for gt in ('volume', 'lateral_area', 'radius', 'area'):
        for tn, t in {'solid': {'solid': sid}, 'solid_id': {'solid_id': sid}, 'both': {'solid': sid, 'solid_id': sid},
                      'notation': {'solid': notation}, 'conflict': {'solid': sid, 'solid_id': 'zz'},
                      'section': {'section_id': sec}, 'section+solid': {'section_id': sec, 'solid': sid},
                      'section+solid_id': {'section_id': sec, 'solid_id': sid}, 'extra': {'solid': sid, 'foo': 1}}.items():
            add(f'K.{cn}.{gt}.{tn}', goal(base, gt, t), expect='INFO')
        add(f'K.{cn}.{gt}.section.goal_sid', goal(base, gt, {'section_id': sec}, sid), expect='INFO')
    add(f'K.{cn}.distance.segment+solid', goal(base, 'distance', {'segment': ['O', "O'"], 'solid': sid}), expect='REFUSE')
# pyramid section area (demo1, A3-DEV-10)
for bn, (base, sid, sec) in {'demo1': (DEMO1, 's_abcd', 'sec_alpha'), 'dev10': (A10, 'prism_abc', 'sec_prism')}.items():
    for tn, t in {'section': {'section_id': sec}, 'section+solid': {'section_id': sec, 'solid': sid},
                  'section+solid_id': {'section_id': sec, 'solid_id': sid}, 'section_unknown': {'section_id': 'nope'},
                  'section_int': {'section_id': 3}}.items():
        add(f'S.{bn}.area.{tn}', goal(base, 'area', t), expect='INFO')
    add(f'S.{bn}.area.section.goal_sid', goal(base, 'area', {'section_id': sec}, sid), expect='INFO')
    add(f'S.{bn}.area.section.goal_sid_conflict', goal(base, 'area', {'section_id': sec}, 'zz'), expect='REFUSE')

# ── 4. S8 ownership (A3-DEV-02 + M = midpoint SB in pyr1) ──────────────────────────────────────────────────────
def n2(target, gsid='__absent__', mprem=None):
    p = goal(N2, 'distance', target, gsid, gid='mb', keep_others=True)
    if mprem is not None:
        p['premises'][-1] = mprem
    return p
M1 = {'kind': 'point_is_midpoint', 'solid_id': 'pyr1', 'args': {'point': 'M', 'segment': ['S', 'B']}, 'quote': 'Gọi M là trung điểm của SB.'}
OWN = {
    'own.pyr1.MB': (n2({'segment': ['M', 'B']}, 'pyr1'), 'SERVE_OR_CAPABILITY'),
    'own.none.MB': (n2({'segment': ['M', 'B']}), 'SERVE_OR_CAPABILITY'),
    'own.pyr1.qualM': (n2({'segment': ['pyr1::M', 'B']}, 'pyr1'), 'SERVE_OR_CAPABILITY'),
    'own.none.qualM': (n2({'segment': ['pyr1::M', 'B']}), 'SERVE_OR_CAPABILITY'),
    'own.none.qualM_qualB1': (n2({'segment': ['pyr1::M', 'pyr1::B']}), 'SERVE_OR_CAPABILITY'),
    'neg.pyr2.MB': (n2({'segment': ['M', 'B']}, 'pyr2'), 'REFUSE'),
    'neg.pyr2.MA': (n2({'segment': ['M', 'A']}, 'pyr2'), 'REFUSE'),
    'neg.pyr2.MS': (n2({'segment': ['M', 'S']}, 'pyr2'), 'REFUSE'),
    'neg.pyr2.qual2M.qual2B': (n2({'segment': ['pyr2::M', 'pyr2::B']}), 'REFUSE'),
    'neg.pyr1.qual2B': (n2({'segment': ['M', 'pyr2::B']}, 'pyr1'), 'REFUSE'),
    'neg.pyr2.qual1M': (n2({'segment': ['pyr1::M', 'B']}, 'pyr2'), 'REFUSE'),
    'neg.pyr3.MB': (n2({'segment': ['M', 'B']}, 'pyr3'), 'REFUSE'),
    'neg.none.qual3M': (n2({'segment': ['pyr3::M', 'B']}), 'REFUSE'),
    'neg.pyr2.S_point_plane': (goal(N2, 'distance', {'point': 'S', 'plane': ['A', 'B', 'C']}, 'pyr2', gid='mb', keep_others=True), 'REFUSE'),
    'neg.pyr2.M_point_plane': (goal(N2, 'distance', {'point': 'M', 'plane': ['A', 'B', 'C']}, 'pyr2', gid='mb', keep_others=True), 'REFUSE'),
    'neg.pyr2.M_point_line': (goal(N2, 'distance', {'point': 'M', 'line': ['A', 'B']}, 'pyr2', gid='mb', keep_others=True), 'REFUSE'),
    'neg.pyr2.angle_M': (goal(N2, 'angle', {'line': ['M', 'A'], 'plane': ['A', 'B', 'C']}, 'pyr2', gid='mb', keep_others=True), 'REFUSE'),
    'neg.pyr1.D1': (goal(N2, 'distance', {'segment': ['pyr2::D', 'B']}, 'pyr1', gid='mb', keep_others=True), 'REFUSE'),
    'mixed.none.qual1M_qual2B': (n2({'segment': ['pyr1::M', 'pyr2::B']}), 'INFO'),
    'mixed.none.qual1M_qual2D': (n2({'segment': ['pyr1::M', 'pyr2::D']}), 'INFO'),
    'mixed.none.M_qual2D': (n2({'segment': ['M', 'pyr2::D']}), 'INFO'),
    # M constructed in pyr2 from pyr2-foreign S: the premise itself is wrong-scope
    'neg.premM_in_pyr2': (n2({'segment': ['M', 'B']}, 'pyr2', {**M1, 'solid_id': 'pyr2'}), 'REFUSE'),
    'neg.premM_qualified_foreign': (n2({'segment': ['M', 'B']}, '__absent__', {**M1, 'solid_id': None, 'args': {'point': 'M', 'segment': ['pyr2::S', 'B']}}), 'REFUSE'),
    'own.premM_unscoped': (n2({'segment': ['M', 'B']}, 'pyr1', {**{k: v for k, v in M1.items() if k != 'solid_id'}}), 'SERVE_OR_CAPABILITY'),
    'neg.premM_unscoped.pyr2': (n2({'segment': ['M', 'B']}, 'pyr2', {**{k: v for k, v in M1.items() if k != 'solid_id'}}), 'REFUSE'),
    'neg.premM_qual_pyr1.goal_pyr2': (n2({'segment': ['M', 'B']}, 'pyr2', {**M1, 'args': {'point': 'pyr1::M', 'segment': ['pyr1::S', 'pyr1::B']}}), 'REFUSE'),
    # centroid / projection constructed points
    'neg.centroid_pyr1.goal_pyr2': (n2({'segment': ['G', 'B']}, 'pyr2', {'kind': 'centroid', 'solid_id': 'pyr1', 'args': {'point': 'G', 'polygon': ['S', 'A', 'B']}, 'quote': 'Gọi M là trung điểm của SB.'}), 'REFUSE'),
}
for k, (p, e) in OWN.items():
    add('O.' + k, p, expect=e)
# derived solid scope (A3-DEV-01, top_pyramid = S.M...)
for k, (t, sid, e) in {'top.SM': ({'segment': ['S', 'M']}, 'top_pyramid', 'SERVE_OR_CAPABILITY'),
                       'top.SB': ({'segment': ['S', 'B']}, 'top_pyramid', 'REFUSE'),
                       'top.SA': ({'segment': ['S', 'A']}, 'top_pyramid', 'REFUSE'),
                       'top.MC': ({'segment': ['M', 'C']}, 'top_pyramid', 'REFUSE'),
                       'top.qualB': ({'segment': ['S', 'top_pyramid::B']}, None, 'REFUSE'),
                       'top.qualS': ({'segment': ['top_pyramid::S', 'M']}, None, 'SERVE_OR_CAPABILITY'),
                       'main.SB': ({'segment': ['S', 'B']}, 'main_pyramid', 'SERVE_OR_CAPABILITY'),
                       'main.qualtopS': ({'segment': ['top_pyramid::S', 'B']}, 'main_pyramid', 'INFO'),
                       'top.M_plane_ABC': ({'point': 'M', 'plane': ['A', 'B', 'C']}, 'top_pyramid', 'REFUSE'),
                       'top.vol': ({'solid': 'top_pyramid'}, None, 'INFO'),
                       'top.vol_id': ({'solid_id': 'top_pyramid'}, None, 'INFO'),
                       'top.vol_goal': ({'solid': 'top_pyramid'}, 'top_pyramid', 'INFO'),
                       'top.vol_conflict': ({'solid': 'top_pyramid'}, 'main_pyramid', 'REFUSE'),
                       }.items():
    gt = 'volume' if 'vol' in k else 'distance'
    add('D.' + k, goal(A01, gt, t, sid if sid is not None else '__absent__', keep_others=True), expect=e)
(D / 'cases_probe.json').write_text(json.dumps(cases, ensure_ascii=False, indent=1), encoding='utf-8')
print(len(cases))
