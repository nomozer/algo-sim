"""CIC-D1 registered cases (append-only; refuses to overwrite).

  cases.py build                  -> cases.json (concrete payloads; built once from the locked prism fixture and A3-DEV-02)
  cases.py run <backend> <out>    -> every case through Adapter /3, Planner and Adapter /4 of <backend> (offline)

/2 prism payloads reach Adapter /3 and the Planner relabelled as /1 (same fields); /1 payloads reach Adapter /4 the way
tests/geometry/test_scope_census_closure.py::a4 does. No verdict is inferred here.
"""
import hashlib, json, os, socket, subprocess, sys
from copy import deepcopy
from pathlib import Path

U = Path(__file__).resolve().parents[1]; RUN = U.parents[1]; ROOT = RUN.parents[4]
def digest(p): return hashlib.sha256(Path(p).read_bytes().replace(b'\r\n', b'\n')).hexdigest()
def write(path, data):
    with Path(path).open('x', encoding='utf-8', newline='\n') as f: f.write(json.dumps(data, ensure_ascii=False, indent=2) + '\n')
INVALID = {r: ['REFUSED', 'INVALID_MATH_GOAL'] for r in ('a3', 'pl', 'a4')}
MISMATCH = {r: ['REFUSED', 'SOURCE_OBJECT_MISMATCH'] for r in ('a3', 'pl', 'a4')}


def build():
    sys.path[:0] = [str(ROOT / 'backend'), str(ROOT / 'backend/tests/geometry')]
    from test_typed_fact_next_v2_distance_bridge import _prism            # locked fixture (82097186 lineage)
    asks = {'distance_point_plane': ("Tính khoảng cách từ A' đến mặt phẳng (ABC).", 'distance', {'point': "A'", 'plane': ['A', 'B', 'C']}),
            'distance_segment': ("Tính độ dài B'C.", 'distance', {'segment': ["B'", 'C']}),
            'angle_line_plane': ("Tính góc giữa B'C và mặt phẳng (ABC).", 'angle', {'line': ["B'", 'C'], 'plane': ['A', 'B', 'C']}),
            'area_polygon': ('Tính diện tích tam giác ABC.', 'area', {'polygon': ['A', 'B', 'C']})}
    scopes = {'solid': {'solid': 'pr'}, 'solid_id': {'solid_id': 'pr'}, 'solid_notation': {'solid': "ABC.A'B'C'"},
              'solid_and_solid_id': {'solid': 'pr', 'solid_id': 'pr'}}
    cases = {}
    def prism(quote, goal_type, target, goal_solid_id=None):
        p = _prism(ask=(quote, target)); g = p['math_goals'][0]; g['goal_type'] = goal_type
        if goal_solid_id: g['solid_id'] = goal_solid_id
        return p
    for an, (q, gt, t) in asks.items():
        for sn, s in scopes.items():
            cases[f'F.{an}.{sn}'] = {'class': 'NEG_LOCKED_GRAMMAR', 'payload': prism(q, gt, {**t, **s}), 'expected': INVALID}
        cases[f'C.{an}.no_scope'] = {'class': 'CONTROL_UNCHANGED', 'payload': prism(q, gt, t)}
        cases[f'C.{an}.goal_solid_id'] = {'class': 'CONTROL_UNCHANGED', 'payload': prism(q, gt, t, 'pr')}
    vq = "Tính thể tích khối lăng trụ ABC.A'B'C'."
    for vn, t in {'solid': {'solid': 'pr'}, 'solid_id': {'solid_id': 'pr'}, 'solid_and_solid_id': {'solid': 'pr', 'solid_id': 'pr'}}.items():
        cases[f'C.volume.{vn}'] = {'class': 'CONTROL_UNCHANGED', 'payload': prism(vq, 'volume', t)}
    corpus = json.loads((RUN.parent / 'typedfact-next-adapter3-simulation/corpus-dev.json').read_text(encoding='utf-8'))
    base = deepcopy(next(c for c in corpus['cases'] if c['case_id'] == 'A3-DEV-02')['payload'])
    base['problem_text'] += ' Gọi M là trung điểm của SB. Tính độ dài MB.'           # same as test_closed_input_contract.legacy_m
    base['premises'].append({'kind': 'point_is_midpoint', 'solid_id': 'pyr1', 'args': {'point': 'M', 'segment': ['S', 'B']},
                             'quote': 'Gọi M là trung điểm của SB.'})
    def n2(goal_sid, seg, extra=None):
        p = deepcopy(base); g = {'goal_id': 'mb', 'kind': 'measurement', 'goal_type': 'distance', 'quote': 'Tính độ dài MB.',
                                 'target': {'segment': seg, **(extra or {})}}
        if goal_sid: g['solid_id'] = goal_sid
        p['math_goals'].append(g); return p
    cases['N2v2.goal_solid_id'] = {'class': 'NEG_OWNERSHIP', 'payload': n2('pyr2', ['M', 'B']), 'expected': MISMATCH}
    cases['N2v2.goal_solid_id_qualified'] = {'class': 'NEG_OWNERSHIP', 'payload': n2('pyr2', ['pyr2::M', 'B']), 'expected': MISMATCH}
    cases['N2v2.qualified_namespace'] = {'class': 'NEG_OWNERSHIP', 'payload': n2(None, ['pyr2::M', 'B']), 'expected': MISMATCH}
    cases['N2v2.control_own_point'] = {'class': 'POS_OWNERSHIP_CONTROL', 'payload': n2('pyr1', ['M', 'B']),
        'expected': {'a3': ['SERVED', None], 'pl': ['REFUSED', 'BRIDGE_UNSUPPORTED_QUALIFIED_IDENTITY'],
                     'a4': ['REFUSED', 'BRIDGE_UNSUPPORTED_QUALIFIED_IDENTITY']},
        'oracle': {'goal': 'mb', 'coef': '√5/2', 'dim': 1, 'unit': 'a',
                   'derivation': 'AB = a, SA = 2a, SA ⊥ (ABC) ⇒ SB² = a² + 4a² = 5a²; M midpoint of SB ⇒ MB = (√5/2)·a'}}
    for sn in ('solid_id', 'solid'):                                               # historical v1 N2 inputs, kept verbatim
        for q in (False, True):
            cases[f'N2v1.target_{sn}.{"qualified" if q else "unqualified"}'] = {
                'class': 'HISTORICAL_V1_SUPERSEDED', 'payload': n2(None, ['pyr2::M' if q else 'M', 'B'], {sn: 'pyr2'}),
                'v1_expected': MISMATCH, 'locked_contract_expected': INVALID}
    write(U / 'cases.json', {'registration': 'W3F2-CIC-D1-CASES/1', 'locked_test':
        'backend/tests/geometry/test_typed_fact_next_v2_distance_bridge.py::test_malformed_distance_target_is_refused[target8]',
        'control_rule': 'CONTROL_UNCHANGED cases must give the same (status, code, answer) after the fix as at RED (research HEAD 1490e3cd)',
        'cases': cases})
    print(digest(U / 'cases.json'), len(cases))


def run(backend, out):
    backend = Path(backend).resolve(); sys.path.insert(0, str(backend)); sys.dont_write_bytecode = True
    os.environ['ALLOW_LIVE_AI'] = '0'
    def offline(*_a, **_k): raise RuntimeError('OFFLINE_ONLY')
    socket.socket.connect = offline; socket.create_connection = offline
    from types import SimpleNamespace
    from app.ai import adapter3_simulation as A
    from app.ai.adapter4_route import run_typed_fact_next_v2_route
    from app.ai.function_route import run_typed_fact_next_planner_route
    from app.simulation.geometry_functions.typed_fact_next import TypedFactNextValidationError, convert_v1_to_v2
    assert Path(A.__file__).resolve().is_relative_to(backend), A.__file__
    def v1(p): return {**deepcopy(p), 'schema_version': 'typed-fact-next/1'}
    def a4(p):
        q = deepcopy(p)
        if q['schema_version'].endswith('/1'):
            try: q = convert_v1_to_v2(q, 'adapter3') if q.get('derived_sections') else {**q, 'schema_version': 'typed-fact-next/2'}
            except TypedFactNextValidationError as e: return SimpleNamespace(status='REFUSED', code=e.code, reason=e.detail)
        return run_typed_fact_next_v2_route(q)
    routes = {'a3': lambda p: A.run_typed_fact_next_route(v1(p)), 'pl': lambda p: run_typed_fact_next_planner_route(v1(p)), 'a4': a4}
    reg = json.loads((U / 'cases.json').read_text(encoding='utf-8'))
    git = lambda *a: subprocess.check_output(['git', '-C', str(backend), *a], text=True).strip()
    results = {}
    for name, c in reg['cases'].items():
        results[name] = {}
        for r, f in routes.items():
            try: x = f(c['payload'])
            except Exception as e: results[name][r] = {'status': 'EXCEPTION', 'code': type(e).__name__, 'reason': str(e)[:200]}; continue
            results[name][r] = {'status': x.status, 'code': x.code, 'reason': x.reason,
                                'answer': {k: [v.get('coef'), v.get('dim'), v.get('unit')] for k, v in (getattr(x, 'answer_exact', None) or {}).items()}}
    write(out, {'backend': str(backend), 'head': git('rev-parse', 'HEAD'), 'backend_app_dirty': bool(git('status', '--porcelain', '--', 'app')),
                'cases_sha256_lf': digest(U / 'cases.json'), 'live_provider_calls': 0, 'results': results})


if __name__ == '__main__':
    build() if sys.argv[1] == 'build' else run(*sys.argv[2:4])
