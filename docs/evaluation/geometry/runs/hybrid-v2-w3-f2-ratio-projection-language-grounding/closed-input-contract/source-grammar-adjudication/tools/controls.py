"""Source-grammar adjudication controls (append-only; refuses to overwrite).

  controls.py build                      -> pending-source-grammar-controls.json + supported-positive-controls.json
  controls.py run <backend> <controls> <out.json>
      runs every case of <controls> through Adapter /3, Planner and Adapter /4 of the backend tree <backend>
      (offline, ALLOW_LIVE_AI=0) and records status/code/answers/source authority. No verdict is inferred here.
"""
import ast, hashlib, json, os, socket, subprocess, sys
from copy import deepcopy
from pathlib import Path

U = Path(__file__).resolve().parents[1]; CIC = U.parent
V1_COMMIT = '4b361c47ce484a95416ea336b1bdfb264138a005'          # verbatim checkpoint holding the v1 test file
V1_TEST = 'backend/tests/geometry/test_closed_input_contract.py'
GIVEN = ('Cho hình chóp K.PQR có đáy PQR là tam giác vuông tại P, PQ = 3, PR = 4. '
         'KP vuông góc với (PQR) và KP = 6.')


def digest(p): return hashlib.sha256(Path(p).read_bytes().replace(b'\r\n', b'\n')).hexdigest()
def write(path, data):
    with Path(path).open('x', encoding='utf-8', newline='\n') as f: f.write(json.dumps(data, ensure_ascii=False, indent=2) + '\n')


def v1_payloads(root):
    """Re-create the four v1 inputs from the committed v1 test source (fresh_pyramid + the four scope edits)."""
    src = subprocess.check_output(['git', '-C', str(root), 'show', f'{V1_COMMIT}:{V1_TEST}'], text=True, encoding='utf-8')
    fn = next(n for n in ast.parse(src).body if isinstance(n, ast.FunctionDef) and n.name == 'fresh_pyramid')
    ns = {}; exec(compile(ast.Module([fn], []), V1_TEST, 'exec'), ns)
    out = {}
    for scope in ('id', 'notation', 'nested_id', 'goal_id'):      # same edits as v1 test_fresh_geometry_positive_scope_aliases
        p = ns['fresh_pyramid'](); goal = p['math_goals'][0]
        if scope == 'notation': goal['target'] = {'solid': 'K.PQR'}
        elif scope == 'nested_id': goal['target'] = {'solid_id': 'alpha-1'}
        elif scope == 'goal_id': goal['solid_id'] = 'alpha-1'
        out[scope] = p
    return out, hashlib.sha256(src.encode('utf-8')).hexdigest()


def build():
    root = CIC.parents[5]
    recorded = json.loads((CIC / 'source-control-analysis.json').read_text(encoding='utf-8'))['payloads']
    v1, v1_sha = v1_payloads(root)
    assert v1 == recorded, 'v1 test inputs differ from source-control-analysis.json'
    write(U / 'pending-source-grammar-controls.json', {
        'registration': 'W3F2-CIC-PENDING-SOURCE-GRAMMAR-CONTROLS/1',
        'status': 'PENDING_SOURCE_GRAMMAR_SUPPORT',
        'not_acceptance_evidence': True,
        'expected_unchanged': {'status': 'SERVED', 'answer_coef': '12', 'routes': ['a3', 'pl', 'a4']},
        'origin': {'commit': V1_COMMIT, 'file': V1_TEST, 'file_sha256_lf': v1_sha,
                   'tests': [f'{V1_TEST}::test_fresh_geometry_positive_scope_aliases[{s}]' for s in v1],
                   'inputs_equal_to': 'closed-input-contract/source-control-analysis.json#payloads'},
        'reason': 'Source Gate grammar does not read a named construction request ("Dựng hình chóp K.PQR") in the '
                  'request text: QUESTION_CONTEXT_UNSUPPORTED; see owner-adjudication-addendum.md',
        'cases': recorded})
    supported = {}
    for scope, p0 in recorded.items():
        p = deepcopy(p0)
        p['problem_text'] = GIVEN + ' Tính thể tích hình chóp K.PQR.'
        p['simulation_goals'][0]['quote'] = 'Cho hình chóp K.PQR'
        supported[scope] = p
    write(U / 'supported-positive-controls.json', {
        'registration': 'W3F2-CIC-SUPPORTED-POSITIVE-CONTROLS/1',
        'derived_from': 'pending-source-grammar-controls.json (same solids, premises, goals, scopes)',
        'changes': ['problem_text: request sentence "Dựng hình chóp K.PQR. Tính thể tích hình chóp K.PQR." -> '
                    '"Tính thể tích hình chóp K.PQR."',
                    'simulation_goals[0].quote: "Dựng hình chóp K.PQR." -> "Cho hình chóp K.PQR" (the given clause)'],
        'wording_source': 'inputs/recovery-supplementary.json#control (locked; construct_object quotes the given clause, '
                          'volume asked as "Tính thể tích hình chóp S.ABCD.")',
        'oracle': {'answer_coef': '12', 'derivation': 'right triangle PQR at P: area = 3*4/2 = 6; KP ⊥ (PQR), KP = 6 is the '
                   'height; V = 6*6/3 = 12 (Fraction)'},
        'cases': supported})
    print(json.dumps({'pending': digest(U / 'pending-source-grammar-controls.json'),
                      'supported': digest(U / 'supported-positive-controls.json'), 'v1_test_sha256_lf': v1_sha}))


def run(backend, controls, out):
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

    def a4(p):                                     # same conversion as tests/geometry/test_scope_census_closure.py::a4
        q = deepcopy(p)
        try: q = convert_v1_to_v2(q, 'adapter3') if q.get('derived_sections') else {**q, 'schema_version': 'typed-fact-next/2'}
        except TypedFactNextValidationError as e: return SimpleNamespace(status='REFUSED', code=e.code, reason=e.detail)
        return run_typed_fact_next_v2_route(q)
    routes = {'a3': lambda p: A.run_typed_fact_next_route(deepcopy(p)),
              'pl': lambda p: run_typed_fact_next_planner_route(deepcopy(p)), 'a4': a4}
    cases = json.loads(Path(controls).read_text(encoding='utf-8'))['cases']
    git = lambda *a: subprocess.check_output(['git', '-C', str(backend), *a], text=True).strip()
    results = {}
    for name, p in cases.items():
        results[name] = {}
        for r, f in routes.items():
            x = f(p)
            results[name][r] = {'status': x.status, 'code': x.code, 'reason': x.reason,
                                'answer_coef': {k: v.get('coef') for k, v in (getattr(x, 'answer_exact', None) or {}).items()},
                                'source_authority': (getattr(x, 'source_verification', None) or {}).get('authority')}
    write(out, {'backend': str(backend), 'head': git('rev-parse', 'HEAD'),
                'backend_app_dirty': bool(git('status', '--porcelain', '--', 'app')),
                'controls': Path(controls).name, 'controls_sha256_lf': digest(controls),
                'live_provider_calls': 0, 'results': results})


if __name__ == '__main__':
    build() if sys.argv[1] == 'build' else run(*sys.argv[2:5])
