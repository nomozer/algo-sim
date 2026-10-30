"""Reviewer-authored probes (new inputs, built from frozen base payloads). Writes probes.json next to this file."""
import json
from copy import deepcopy
from pathlib import Path

HERE = Path(__file__).parent
WT = Path('D:/Documents/projects/algo-sim/.superpowers/worktrees/w3-f2-ratio-projection-language-grounding')
RUN = WT / 'docs/evaluation/geometry/runs/hybrid-v2-w3-f2-ratio-projection-language-grounding/closed-input-contract/cic-d1-contract-recovery/target-grammar-identity-recovery'
C = json.loads((RUN / 'cases.json').read_text(encoding='utf-8'))
P = {}


def base(name):
    return deepcopy(C[name]['payload'])


def goal(p, gtype, target, sid=None, gid='rv', quote=None):
    p = deepcopy(p)
    g = {'goal_id': gid, 'kind': 'measurement', 'goal_type': gtype, 'target': target, 'quote': quote or 'Tính độ dài AB.'}
    if sid:
        g['solid_id'] = sid
    p['math_goals'] = [x for x in p.get('math_goals', []) if x.get('kind') != 'measurement' or x['goal_id'] != 'identity'] + [g]
    if g['quote'] not in p['problem_text']:
        p['problem_text'] += ' ' + g['quote']
    return p


PR = base('I.distinct'); PR['math_goals'] = []                 # prism pr ABC.A'B'C', 6-8-12
BOUND = base('I.bound_alias'); BOUND['math_goals'] = []        # pr binds A->X, B->Y
TWO = base('I.ambiguous'); TWO['math_goals'] = []              # pr + other(A->X)
PYR = base('I.constructed_distinct'); PYR['math_goals'] = [g for g in PYR['math_goals'] if g['goal_id'] != 'identity']
DER = base('I.derived_distinct'); DER['math_goals'] = [g for g in DER['math_goals'] if g['goal_id'] != 'identity']
CYL = base('K.cyl.radius.solid'); CYL['math_goals'] = []
CONE = base('K.cone.volume.solid_id'); CONE['math_goals'] = []
SPH = base('K.sph.area.section'); SPH['math_goals'] = []

# ---------- F1: unregistered target shapes not in the frozen 442 ----------
F1 = {
    'distance.point_line_plane': {'point': "A'", 'line': ['B', 'C'], 'plane': ['A', 'B', 'C']},
    'distance.segment_line1_line2': {'segment': ['A', 'B'], 'line1': ['A', 'B'], 'line2': ["A'", "C'"]},
    'distance.plane_plane1_plane2': {'plane': ['A', 'B', 'C'], 'plane1': ['A', 'B', 'C'], 'plane2': ["A'", "B'", "C'"]},
    'distance.point_plane1': {'point': "A'", 'plane1': ['A', 'B', 'C']},
    'distance.line_line1': {'line': ['A', 'B'], 'line1': ["A'", "C'"]},
    'distance.polygon': {'polygon': ['A', 'B', 'C']},
    'distance.point_only': {'point': "A'"},
    'angle.point_line': {'point': "A'", 'line': ['B', 'C']},
    'angle.line_plane_point': {'line': ["A'", 'B'], 'plane': ['A', 'B', 'C'], 'point': 'C'},
    'angle.polygon': {'polygon': ['A', 'B', 'C']},
    'area.segment': {'segment': ['A', 'B']},
    'area.polygon_point': {'polygon': ['A', 'B', 'C'], 'point': "A'"},
    'volume.polygon': {'polygon': ['A', 'B', 'C']},
    'volume.solid_polygon': {'solid': 'pr', 'polygon': ['A', 'B', 'C']},
    'lateral_area.polygon': {'polygon': ['A', 'B', 'C']},
    'radius.polygon': {'polygon': ['A', 'B', 'C']},
    'key.Solid_case': {'Solid': 'pr'},
    'key.solid_space': {'solid ': 'pr'},
    'key.section': {'section': 'sec'},
}
for name, t in F1.items():
    gtype = name.split('.')[0] if not name.startswith('key.') else 'volume'
    P[f'F1.pr.{name}'] = goal(PR, gtype, t)
    P[f'F1.pr.{name}.gsid'] = goal(PR, gtype, t, sid='pr')
# curved: scope-only aliases with goal-level solid_id too
for nm, bp, sid in (('cyl', CYL, 'cyl'), ('cone', CONE, 'cone_main'), ('sph', SPH, 'sph')):
    for gtype in ('radius', 'lateral_area', 'area'):
        P[f'F1.{nm}.{gtype}.solid_id.gsid'] = goal(bp, gtype, {'solid_id': sid}, sid=sid, quote='Tính.')
        P[f'F1.{nm}.{gtype}.solid+solid_id.gsid'] = goal(bp, gtype, {'solid': sid, 'solid_id': sid}, sid=sid, quote='Tính.')
    P[f'F1.{nm}.volume.solid+solid_id.gsid'] = goal(bp, 'volume', {'solid': sid, 'solid_id': sid}, sid=sid, quote='Tính.')
    # registered controls
    P[f'CTRL.{nm}.volume.solid_id'] = goal(bp, 'volume', {'solid_id': sid}, quote='Tính.')
    P[f'CTRL.{nm}.volume.solid_id.gsid'] = goal(bp, 'volume', {'solid_id': sid}, sid=sid, quote='Tính.')
    P[f'CTRL.{nm}.radius.solid'] = goal(bp, 'radius', {'solid': sid}, quote='Tính.')
P['F1.cyl.distance.solid_id'] = goal(CYL, 'distance', {'solid_id': 'cyl'}, quote='Tính.')
P['F1.cyl.radius.section_id+solid'] = goal(CYL, 'radius', {'section_id': 'sec_parallel', 'solid': 'cyl'}, quote='Tính.')

# ---------- F2: canonical identity ----------
ID = {
    # whitespace variants that the schema strips
    'ws.tab': (PR, {'segment': ['A', 'A\t']}, None),
    'ws.nbsp': (PR, {'segment': ['A', '\u00a0A']}, None),
    'ws.newline_q': (PR, {'segment': ['pr::A\n', 'A']}, None),
    'ws.both_qualified': (PR, {'segment': [' pr::A', 'pr::A ']}, 'pr'),
    'ws.em_space': (PR, {'segment': ['\u2003A', 'A']}, None),
    # scope-bound unqualified vs canonical name
    'bind.scoped_canonical': (BOUND, {'segment': ['X', 'A']}, 'pr'),
    'bind.scoped_canonical_rev': (BOUND, {'segment': ['A', 'X']}, 'pr'),
    'bind.plane4': (BOUND, {'point': "A'", 'plane': ['A', 'B', 'C', 'X']}, None),
    'bind.polygon4': (BOUND, {'polygon': ['X', 'B', 'C', 'A']}, None),
    'bind.line1': (BOUND, {'line1': ['Y', 'pr::B'], 'line2': ['A', 'C']}, None),
    'bind.distinct_ctrl': (BOUND, {'segment': ['X', 'Y']}, None),
    'bind.distinct_ctrl_scoped': (BOUND, {'segment': ['A', 'pr::B']}, 'pr'),
    # case of namespace
    'ns.upper': (PR, {'segment': ['A', 'PR::A']}, None),
    # derived
    'der.qual_parent_vs_unq': (DER, {'segment': ['main_pyramid::S', 'S']}, 'top_pyramid'),
    'der.qual_parent_vs_qual_der': (DER, {'segment': ['main_pyramid::S', 'top_pyramid::S']}, None),
    'der.qual_both_der_M': (DER, {'segment': ['top_pyramid::M', 'main_pyramid::M']}, None),
    'der.unscoped_S_vs_der': (DER, {'segment': ['S', 'top_pyramid::S']}, None),
    'der.plane_alias': (DER, {'point': 'S', 'plane': ['A', 'B', 'main_pyramid::A']}, 'top_pyramid'),
    'der.ctrl_SB_main': (DER, {'segment': ['S', 'B']}, 'main_pyramid'),
    'der.ctrl_SM_top': (DER, {'segment': ['S', 'M']}, 'top_pyramid'),
    # shared pyramids: pyr1::D constructed midpoint, pyr2::D apex bound to D1
    'pyr.D1_vs_pyr2D': (PYR, {'segment': ['D1', 'pyr2::D']}, None),
    'pyr.D_unscoped_vs_pyr2D': (PYR, {'segment': ['D', 'pyr2::D']}, None),
    'pyr.pyr1D_vs_pyr2D': (PYR, {'segment': ['pyr1::D', 'pyr2::D']}, None),
    'pyr.D_unscoped_vs_pyr1D': (PYR, {'segment': ['D', 'pyr1::D']}, None),
    'pyr.D_unscoped_vs_S': (PYR, {'segment': ['D', 'S']}, None),
    'pyr.pyr1D_vs_S': (PYR, {'segment': ['pyr1::D', 'pyr1::S']}, None),
    'pyr.scoped1_D_vs_S': (PYR, {'segment': ['D', 'S']}, 'pyr1'),
    'pyr.scoped2_D_vs_A': (PYR, {'segment': ['D', 'A']}, 'pyr2'),
    'pyr.scoped2_D_vs_D1': (PYR, {'segment': ['D', 'D1']}, 'pyr2'),
    'pyr.shared_A': (PYR, {'segment': ['pyr1::A', 'pyr2::A']}, None),
    'pyr.shared_B_C': (PYR, {'segment': ['pyr1::B', 'pyr2::C']}, None),
    'pyr.M_vs_pyr1M': (PYR, {'segment': ['M', 'pyr1::M']}, None),
    'pyr.S_vs_D1': (PYR, {'segment': ['S', 'D1']}, None),
    # curved
    'cyl.center_alias': (CYL, {'segment': ['O', 'cyl::O']}, None),
    'cyl.center_ctrl': (CYL, {'segment': ['O', "O'"]}, None),
    'cyl.rim_ctrl': (CYL, {'segment': ['O', 'A']}, 'cyl'),
    'cone.apex_alias': (CONE, {'segment': ['S', 'cone_upper::S']}, None),
    'cone.apex_ctrl': (CONE, {'segment': ['S', 'O']}, None),
    # two prisms
    'two.pr_vs_other_B': (TWO, {'segment': ['pr::B', 'other::B']}, None),
    'two.X_vs_otherA': (TWO, {'segment': ['X', 'other::A']}, None),
    'two.point_ambiguous': (TWO, {'point': 'A', 'plane': ["pr::A'", "pr::B'", "pr::C'"]}, None),
    'two.point_ambiguous_seg_ok': (TWO, {'point': 'A', 'line': ['pr::B', 'pr::C']}, None),
}
for name, (bp, t, sid) in ID.items():
    P[f'F2.{name}'] = goal(bp, 'distance', t, sid=sid)

# non-injective binding (two locals -> one canonical)
NI = deepcopy(PR); NI['solids'][0]['vertex_bindings'] = {'A': 'B'}
P['F2.noninj.scoped_AB'] = goal(NI, 'distance', {'segment': ['A', 'B']}, sid='pr')
P['F2.noninj.unscoped_AC'] = goal(NI, 'distance', {'segment': ['A', 'C']})
P['F2.noninj.unscoped_BC'] = goal(NI, 'distance', {'segment': ['B', 'C']})

# shared_vertices pairing two DIFFERENT canonical identities (S of pyr1 with D of pyr2)
SV = deepcopy(PYR)
SV['relations'][0]['pairs'].append(['pyr1::S', 'pyr2::D'])
P['F2.sv.S_vs_pyr2D'] = goal(SV, 'distance', {'segment': ['pyr1::S', 'pyr2::D']})

# constructed point whose label equals another solid's canonical bound name
CB = deepcopy(PYR)
CB['premises'].append({'kind': 'point_is_midpoint', 'solid_id': 'pyr1', 'args': {'point': 'D1', 'segment': ['S', 'C']},
                       'quote': 'Gọi D1 là trung điểm của SC.'})
CB['problem_text'] += ' Gọi D1 là trung điểm của SC.'
P['F2.cb.D1_vs_pyr2D'] = goal(CB, 'distance', {'segment': ['D1', 'pyr2::D']})
P['F2.cb.pyr1D1_vs_pyr2D'] = goal(CB, 'distance', {'segment': ['pyr1::D1', 'pyr2::D']})
P['F2.cb.D1_vs_S_scoped1'] = goal(CB, 'distance', {'segment': ['D1', 'S']}, sid='pyr1')

# constructed point in pr named like the canonical binding X of A
CX = deepcopy(BOUND)
CX['premises'].append({'kind': 'point_is_midpoint', 'args': {'point': 'X', 'segment': ['B', 'C']}, 'quote': 'Gọi X là trung điểm BC.'})
CX['problem_text'] += ' Gọi X là trung điểm BC.'
P['F2.cx.X_vs_prA'] = goal(CX, 'distance', {'segment': ['X', 'pr::A']})
P['F2.cx.X_vs_B'] = goal(CX, 'distance', {'segment': ['X', 'B']})

# premise-level duplicates (outside F2 owner scope; observe only)
DP = deepcopy(PR); DP['premises'].append({'kind': 'segment_length', 'args': {'segment': ['A', 'pr::A'], 'value': '5'}, 'quote': 'AA = 5.'})
DP['problem_text'] += ' AA = 5.'
P['OBS.premise_dup_segment'] = goal(DP, 'distance', {'segment': ['A', 'B']})

(HERE / 'probes.json').write_text(json.dumps(P, ensure_ascii=False, indent=1), encoding='utf-8')
print(len(P), 'probes')
