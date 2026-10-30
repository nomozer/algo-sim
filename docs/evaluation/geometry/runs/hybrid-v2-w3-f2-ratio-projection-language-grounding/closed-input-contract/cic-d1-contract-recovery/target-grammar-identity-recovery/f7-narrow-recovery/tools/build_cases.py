"""Build the F7/R1/R2 preregistered inputs from frozen committed sources only; writes cases.json once (x mode)."""
from copy import deepcopy
import json
from pathlib import Path

HERE = Path(__file__).resolve().parents[1]
PARENT = HERE.parent
CASES = json.loads((PARENT / 'cases.json').read_text(encoding='utf-8'))
GREEN = json.loads((PARENT / 'observed-green.json').read_text(encoding='utf-8'))['results']
PROBES = json.loads((PARENT / 'pre-freeze-review' / 'probes.json').read_text(encoding='utf-8'))
REVIEW = json.loads((PARENT / 'pre-freeze-review' / 'out-head.json').read_text(encoding='utf-8'))
CAP = 'BRIDGE_UNSUPPORTED_MEASUREMENT'
ROUTES = ('a3', 'pl', 'a4')
out = {}


def add(name, cls, payload, source, schema=None, routes=None, answer=None, note=''):
    out[name] = {'class': cls, 'source': source, 'payload': payload, 'expected_schema': schema,
                 'expected_routes': routes, 'expected_a3_answer': answer, 'note': note}


def refused(code, routes=ROUTES): return {r: ['REFUSED', code] for r in routes}


def goal(base, gt, target, append=False):
    p = deepcopy(CASES[base]['payload'])
    g = {'goal_id': 'qx', 'kind': 'measurement', 'goal_type': gt, 'target': target, 'quote': p['math_goals'][0]['quote']}
    p['math_goals'] = [*p['math_goals'], g] if append else [g]
    return p


def setgoal(p, target, sid=None):
    p = deepcopy(p); g = p['math_goals'][-1]; g['target'] = target
    g.pop('solid_id', None)
    if sid: g['solid_id'] = sid
    return p


# F7: valid registered radius/lateral_area targets on polyhedra -> typed capability refusal on every route.
for k in ['V.radius.solid', 'V.radius.solid.goal_sid', 'V.radius.notation', 'V.radius.notation.goal_sid',
          'V.lateral_area.solid', 'V.lateral_area.solid.goal_sid', 'V.lateral_area.notation',
          'V.lateral_area.notation.goal_sid']:
    add('F7.prism.' + k[2:], 'F7', deepcopy(CASES[k]['payload']), f'cases.json:{k}', routes=refused(CAP))
demo = CASES['S.demo1.area.section']['payload']
py, sec = demo['solids'][0]['solid_id'], demo['derived_sections'][0]['section_id']
# Amendment 1 (red.json): pl refuses this base earlier (existing oracle), so pl keeps the base outcome.
PYR = {**refused(CAP), 'pl': [GREEN['S.demo1.area.section']['pl']['status'], GREEN['S.demo1.area.section']['pl']['code']]}
add('F7.pyr.radius.solid', 'F7', goal('S.demo1.area.section', 'radius', {'solid': py}), 'S.demo1.area.section+radius', routes=PYR)
add('F7.pyr.radius.section_id', 'F7', goal('S.demo1.area.section', 'radius', {'section_id': sec}), 'S.demo1.area.section+radius(section)', routes=PYR)
add('F7.pyr.lateral_area.solid', 'F7', goal('S.demo1.area.section', 'lateral_area', {'solid': py}), 'S.demo1.area.section+lateral_area', routes=PYR)
# Mixed goal list: one unsupported goal refuses the whole payload, no partial answers (all-or-nothing contract).
top = CASES['D.top.vol']['payload']['solids'][0]['solid_id']
add('F7.multi.pyr_vol_plus_radius', 'F7', goal('D.top.vol', 'radius', {'solid': top}, append=True), 'D.top.vol+radius', routes={'a3': ['REFUSED', CAP]})
pr = CASES['V.radius.solid']['payload']['solids'][0]['solid_id']
add('F7.multi.prism_distance_plus_lateral', 'F7', goal('G.distance.segment.plain', 'lateral_area', {'solid': pr}, append=True), 'G.distance.segment.plain+lateral_area', routes={'a3': ['REFUSED', CAP]})

# F7 negatives: invalid input keeps its semantic code before any capability decision.
for k in ['V.radius.solid_id', 'V.radius.both', 'V.radius.unknown', 'V.radius.unknown.goal_sid',
          'V.lateral_area.solid_id', 'V.lateral_area.unknown']:
    if k in CASES:
        code = GREEN[k]['schema1']
        add('F7NEG.' + k[2:], 'F7_NEGATIVE', deepcopy(CASES[k]['payload']), f'cases.json:{k}', schema=code, routes=refused(code))
add('F7NEG.radius.malformed_blank', 'F7_NEGATIVE', goal('V.radius.solid', 'radius', {'solid': '  '}), 'V.radius.solid blank operand',
    schema='INVALID_MATH_GOAL', routes=refused('INVALID_MATH_GOAL'))

# Controls: existing frozen exact oracle (observed-green.json, product 6a09c06a), all three routes.
for k in ['G.distance.segment.plain', 'S.demo1.area.section', 'D.top.vol',
          'K.cyl.volume.solid', 'K.cyl.radius.solid', 'K.cyl.lateral_area.solid',
          'K.cone.volume.solid', 'K.cone.radius.solid', 'K.cone.lateral_area.solid',
          'K.sph.volume.solid', 'K.sph.radius.solid', 'K.sph.lateral_area.solid']:
    g = GREEN[k]
    add('CTRL.' + k, 'CONTROL', deepcopy(CASES[k]['payload']), f'cases.json:{k}', schema=g['schema1'],
        routes={r: [g[r]['status'], g[r]['code']] for r in ROUTES}, answer=g['a3']['answer'])

# Disclosed, unchanged limitation: registered area {solid} on polyhedra is refused INVALID_MATH_GOAL on a3 (not F7).
add('LIMIT.prism.area.solid', 'LIMIT', goal('V.radius.solid', 'area', {'solid': pr}), 'V.radius.solid+area(solid)',
    routes={'a3': ['REFUSED', 'INVALID_MATH_GOAL']}, note='pre-existing typed refusal, recorded limitation, not changed')
add('LIMIT.pyr.area.solid', 'LIMIT', goal('S.demo1.area.section', 'area', {'solid': py}), 'S.demo1.area.section+area(solid)',
    routes={'a3': ['REFUSED', 'INVALID_MATH_GOAL']}, note='pre-existing typed refusal, recorded limitation, not changed')

# R1: namespace / ownership -> canonical identity -> distinctness. First refusal layer: payload schema.
add('R1.unknown_ns_repeat', 'R1', setgoal(PROBES['F2.ws.tab'], {'segment': ['ghost::A', 'A']}), 'probes:F2.ws.tab',
    schema='UNKNOWN_SOLID_ID', routes=refused('UNKNOWN_SOLID_ID'))
add('R1.unknown_ns_repeat_rev', 'R1', setgoal(PROBES['F2.ws.tab'], {'segment': ['A', 'ghost::A']}), 'probes:F2.ws.tab',
    schema='UNKNOWN_SOLID_ID', routes=refused('UNKNOWN_SOLID_ID'))
add('R1.foreign_owner_repeat', 'R1', setgoal(PROBES['F2.two.pr_vs_other_B'], {'segment': ['pr::B', 'B']}, sid='other'),
    'probes:F2.two.pr_vs_other_B', schema='SOURCE_OBJECT_MISMATCH', routes=refused('SOURCE_OBJECT_MISMATCH'))
add('R1.same_point_alias', 'R1', setgoal(PROBES['F2.two.pr_vs_other_B'], {'segment': ['pr::B', 'B']}, sid='pr'),
    'probes:F2.two.pr_vs_other_B', schema='INVALID_MATH_GOAL', routes=refused('INVALID_MATH_GOAL'))
for k in ['F2.pyr.pyr1D_vs_pyr2D', 'F2.pyr.pyr1D_vs_S']:
    add('R1.' + k[3:], 'R1_POSITIVE', deepcopy(PROBES[k]), f'probes:{k}', schema=None,
        routes={'a3': ['SERVED', None]}, answer=REVIEW[k]['a3']['answer'],
        note='distinct identities sharing a label (pyr1D_vs_pyr2D) / valid multi-solid reference')

# R2: two root solids plus a derived solid of main_pyramid; the second root binds S -> T.
D2 = deepcopy(PROBES['F2.der.ctrl_SM_top'])
D2['solids'].append({'solid_id': 'other', 'solid_type': 'pyramid', 'notation': 'S.EFG', 'quote': 'Cho hình chóp S.ABCD',
                     'vertex_bindings': {'S': 'T'}})
for name, target, sid, code in [
        ('R2.derived_scoped_constructed', {'segment': ['S', 'M']}, 'top_pyramid', None),
        ('R2.derived_qualified_constructed', {'segment': ['top_pyramid::S', 'M']}, None, None),
        ('R2.derived_vs_other_root', {'segment': ['top_pyramid::S', 'other::S']}, None, None),
        ('R2.derived_alias_of_parent', {'segment': ['top_pyramid::S', 'main_pyramid::S']}, None, 'INVALID_MATH_GOAL'),
        ('R2.scoped_alias_of_parent', {'segment': ['S', 'main_pyramid::S']}, 'top_pyramid', 'INVALID_MATH_GOAL'),
        ('R2.unscoped_ambiguous', {'segment': ['S', 'M']}, None, 'AMBIGUOUS_REFERENCE')]:
    add(name, 'R2' if code else 'R2_POSITIVE', setgoal(D2, target, sid), 'probes:F2.der.ctrl_SM_top + root other',
        schema=code, routes=refused(code) if code else None)
add('R2.single_root_control', 'R2_POSITIVE', deepcopy(PROBES['F2.der.ctrl_SM_top']), 'probes:F2.der.ctrl_SM_top',
    schema=None, routes={'a3': ['SERVED', None]}, answer=REVIEW['F2.der.ctrl_SM_top']['a3']['answer'])

with (HERE / 'cases.json').open('x', encoding='utf-8', newline='\n') as f:
    json.dump(out, f, ensure_ascii=False, indent=1, sort_keys=True)
    f.write('\n')
print(len(out), sorted({c['class'] for c in out.values()}))
