"""Independent F7 reviewer probe. usage: probe.py <backend_dir> <cases_parent_json> <out_json> [--revert-f7]
Zero network: sockets blocked before importing product code."""
import json, os, socket, sys, inspect, textwrap
from copy import deepcopy
from types import SimpleNamespace

def _deny(*a, **k): raise RuntimeError('network blocked by reviewer probe')
socket.socket.connect = _deny; socket.create_connection = _deny; socket.getaddrinfo = _deny
os.environ.pop('ALLOW_LIVE_AI', None)

backend, cases_path, out_path = sys.argv[1:4]; out_path = os.path.abspath(out_path)
REVERT = '--revert-f7' in sys.argv
os.chdir(backend); sys.path.insert(0, backend)

from app.ai import adapter3_simulation as A
from app.ai.adapter4_route import run_typed_fact_next_v2_route
from app.ai.function_route import run_typed_fact_next_planner_route
from app.simulation.geometry_functions import typed_fact_next as T

if REVERT:  # reproduce 1b1a9ed2: drop the terminal F7 else
    src = textwrap.dedent(inspect.getsource(A._Adapter3Compiler._compile_derived_solids_and_goals))
    i = src.index('else:  # F7'); i = src.rindex(chr(10), 0, i) + 1
    j = src.index('(mg.goal_id,))', i) + len('(mg.goal_id,))') + 1
    src = src[:i] + src[j:]
    assert 'BRIDGE_UNSUPPORTED_MEASUREMENT' not in src and 'F7' not in src
    ns = dict(vars(A)); exec(compile(src, '<revert>', 'exec'), ns)
    A._Adapter3Compiler._compile_derived_solids_and_goals = ns['_compile_derived_solids_and_goals']

def a3(p): return A.run_typed_fact_next_route(deepcopy(p))
def pl(p): return run_typed_fact_next_planner_route(deepcopy(p))
def a4(p):
    q = deepcopy(p)
    try:
        q = T.convert_v1_to_v2(q, 'adapter3') if q.get('derived_sections') else {**q, 'schema_version': 'typed-fact-next/2'}
    except T.TypedFactNextValidationError as e:
        return SimpleNamespace(status='REFUSED', code=e.code, reason=e.detail)
    return run_typed_fact_next_v2_route(q)
ROUTES = {'a3': a3, 'pl': pl, 'a4': a4}

def schema(p):
    try: T.parse_typed_fact_next(deepcopy(p)); return None
    except T.TypedFactNextValidationError as e: return e.code

def run(p):
    out = {'schema': schema(p)}
    for n, f in ROUTES.items():
        try:
            r = f(p)
            ans = getattr(r, 'answer_exact', None)
            out[n] = [r.status, r.code, json.dumps(ans, sort_keys=True, default=str) if ans else None,
                      (getattr(r, 'reason', '') or '')[:160],
                      bool(getattr(r, 'answers', None) or getattr(r, 'scene3d', None)) if r.status != 'SERVED' else None]
        except BaseException as e:  # an escaping exception is itself a finding
            out[n] = ['EXCEPTION', type(e).__name__, None, str(e)[:160], None]
    return out

PARENT = json.loads(open(cases_path, encoding='utf-8').read())
F7 = json.loads(open(cases_path.replace('cases.json', 'f7-narrow-recovery/cases.json'), encoding='utf-8').read())
cases = {('P:' + k): v['payload'] for k, v in PARENT.items()}
cases.update({('F7:' + k): v['payload'] for k, v in F7.items()})

ALTS = {'distance': [['segment'], ['point', 'plane'], ['point', 'line'], ['line1', 'line2'], ['line', 'plane'], ['plane1', 'plane2']],
        'angle': [['line', 'plane'], ['line1', 'line2'], ['plane1', 'plane2']],
        'volume': [['solid'], ['solid_id']], 'radius': [['solid'], ['section_id']], 'lateral_area': [['solid']],
        'area': [['polygon'], ['section_id'], ['solid']]}

def target(alt, sid, notation, sec, v):
    a, b, c, d = v[:4]
    vals = {'segment': [a, b], 'point': a, 'plane': [b, c, d], 'line': [a, b], 'line1': [a, b], 'line2': [c, d],
            'plane1': [a, b, c], 'plane2': [b, c, d], 'polygon': [b, c, d], 'solid': sid, 'solid_id': sid, 'section_id': sec}
    return {k: vals[k] for k in alt}

BASES = {  # base key, solid id, notation, section, 4 vertex labels (point first, off the plane)
    'prism': ('G.distance.segment.plain', None, None, None, ['A', "A'", "B'", "C'"]),
    'pyr': ('S.demo1.area.section', None, None, 'sec_alpha', ['S', 'A', 'B', 'C']),
    'pyr_derived': ('D.top.vol', 'top_pyramid', None, 'sec_alpha', ['S', 'A', 'B', 'C']),
    'cyl': ('K.cyl.radius.solid', None, None, 'sec_parallel', ['O', "O'", 'A', 'O']),
    'cone': ('K.cone.radius.solid', None, None, None, None),
    'sph': ('K.sph.radius.solid', None, None, None, None),
}
for name, (bk, sid_over, _n, sec, verts) in BASES.items():
    if bk not in PARENT: continue
    base = PARENT[bk]['payload']
    s0 = base['solids'][0]
    sid = sid_over or s0['solid_id']; notation = s0['notation']
    if verts is None:
        verts = [x for x in (s0.get('center'), s0.get('apex_or_top'), s0.get('rim_point')) if x] * 4
    if sec is None and base.get('derived_sections'): sec = base['derived_sections'][0]['section_id']
    for gt, alts in ALTS.items():
        for alt in alts:
            if 'section_id' in alt and not sec: continue
            for sidmode in ('none', 'goal_sid'):
                for mult in ('single', 'append'):
                    t = target(alt, sid, notation, sec, verts)
                    g = {'goal_id': 'qx', 'kind': 'measurement', 'goal_type': gt, 'target': t,
                         'quote': base['math_goals'][0]['quote']}
                    if sidmode == 'goal_sid' and not ({'solid', 'solid_id'} & set(alt)): g['solid_id'] = sid
                    elif sidmode == 'goal_sid': continue
                    p = deepcopy(base)
                    p['math_goals'] = [*p['math_goals'], g] if mult == 'append' else [g]
                    cases[f'M:{name}.{gt}.{"+".join(alt)}.{sidmode}.{mult}'] = p
            if alt == ['solid']:  # notation spelling of the solid
                p = deepcopy(base); p['math_goals'] = [{'goal_id': 'qx', 'kind': 'measurement', 'goal_type': gt,
                    'target': {'solid': notation}, 'quote': base['math_goals'][0]['quote']}]
                cases[f'M:{name}.{gt}.notation.single'] = p
# Mixed curved + polyhedral payload: radius of the prism next to a cylinder
if 'K.cyl.radius.solid' in PARENT and 'V.radius.solid' in PARENT:
    p = deepcopy(PARENT['K.cyl.radius.solid']['payload'])
    pr = PARENT['V.radius.solid']['payload']
    p['solids'] = p['solids'] + pr['solids']
    for gt in ('radius', 'lateral_area', 'volume'):
        q = deepcopy(p); q['math_goals'] = [{'goal_id': 'qx', 'kind': 'measurement', 'goal_type': gt,
                                              'target': {'solid': 'pr'}, 'quote': p['math_goals'][0]['quote']}]
        cases[f'M:mixed_cyl_prism.{gt}.solid_pr'] = q

res = {k: run(p) for k, p in sorted(cases.items())}
json.dump({'revert_f7': REVERT, 'backend': backend, 'results': res}, open(out_path, 'w', encoding='utf-8'),
          ensure_ascii=False, indent=0, sort_keys=True)
print(len(res), 'cases written', out_path)
