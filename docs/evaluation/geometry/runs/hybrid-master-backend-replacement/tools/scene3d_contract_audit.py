"""Continuation 19 §XI — the BACKEND output contract of Hybrid /4 on every group the corpora hold, through the production
opt-in path `run_hybrid_offline` (gold extractions, 0 provider calls). It checks JSON the frontend receives; it does not
show that a learner sees a correct rendering (no browser here).

Served rows must have: envelope status ok; route SERVED; engine VERIFIED with kernel_check; EVERY math goal of the
extraction answered (presence; values are the oracle's job); ≥ 1 scene object, each with id and type; every coordinate
field (`_COORDS`, list values) exact by `fullmatch` (no float); a construction trace. Non-served rows must carry a refusal
code and no answer. EVERY row (served or refused): no machine code (`UPPER_SNAKE`), entity id (`khoi_S_ABCD`) or the
envelope's simulation_id in any learner-visible field (`_VISIBLE`) of the envelope or route_d.
Not checked: a dropped SIMULATION goal, answer values, and plain sections through three named points (no corpus here
holds that group).
Groups: polyhedra/measures (S-2 gold), described points (R-1 gold), constraint planes / defined points / refusals /
clarifications (K-1 gold), curved solids (`curved_probe.CASES`), composite solids (`composite_relations_probe`).
Usage: scene3d_contract_audit.py [out.json]   (`OFFLINE_DETERMINISTIC_FIXTURE_TEST`, 0 provider calls)
"""
import collections, json, os, re, socket, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
RUN, ROOT = HERE.parent, HERE.parents[5]
sys.path[:0] = [str(ROOT / 'backend'), str(HERE)]
os.environ['ALLOW_LIVE_AI'] = '0'
def _offline(*_a, **_k): raise RuntimeError('OFFLINE_ONLY')
socket.socket.connect = _offline; socket.create_connection = _offline

_CODE = re.compile(r'\b[A-Z]{2,}(?:_[A-Z0-9]{2,})+\b'          # reason codes: PLANE_NOT_UNIQUE
                   r"|\b[A-Za-z][A-Za-z0-9]*_[A-Za-z0-9_]+\b")  # entity ids: khoi_S_ABCD, A_prime (review MINOR-5)
#: an exact value: digits, fractions, radicals, π, signs, sums — never a decimal point or an exponent (fullmatch)
_EXACT = re.compile(r"[0-9√π/+\-() ]+")
#: fields whose text a learner reads, anywhere in the envelope (served or refused)
_VISIBLE = {'label', 'display_label', 'learner_text', 'learner_reason', 'explanation', 'title', 'description', 'notes',
            'message', 'caption', 'reason', 'role', 'question'}        # review round 2 MINOR-D: reason, role, question
_COORDS = {'xyz', 'polygon', 'vertices_xyz', 'center_xyz', 'normal', 'point', 'endpoints'}


def corpora():
    for name, f in (('polyhedra (S-2)', 's2-student-language-pilot-corpus.json'), ('described points (R-1)', 'r1-live-pilot-corpus.json')):
        for c in json.loads((RUN / f).read_text(encoding='utf-8'))['cases']:
            if c.get('gold_extraction'):
                yield name, c['id'], c['problem_text'], c['gold_extraction']
    k1 = {'K-A': 'constraint planes (K-1)', 'K-B': 'refusals (K-1)', 'K-C': 'defined points (K-1)', 'K-D': 'refusals (K-1)',
          'K-E': 'clarifications (K-1)'}
    for c in json.loads((RUN / 'k1-live-pilot-corpus.json').read_text(encoding='utf-8'))['cases']:
        yield k1[c['stratum']], c['id'], c['problem_text'], c['gold_extraction']
    import curved_probe as CP
    for cid, fig, gt, q, _want in CP.CASES:
        p = CP.payload(fig, gt, q)
        yield 'curved solids', cid, p['problem_text'], p
    import composite_relations_probe as CR
    for cid, p, _want in CR.POSITIVE_CASES:
        yield 'composite solids', cid, p['problem_text'], p


def _walk(v, key=None, listed=False):
    if isinstance(v, dict):
        for k, x in v.items():
            yield from _walk(x, k)
    elif isinstance(v, list):
        for x in v:
            yield from _walk(x, key, True)
    else:
        yield key, v, listed


def learner_text(env):
    """Every string under a learner-visible key, anywhere in the envelope."""
    for k, v, _l in _walk(env):
        if k in _VISIBLE and isinstance(v, str):
            yield v


def coordinates(env):
    for k, v, listed in _walk(env.get('scene3d') or {}):
        if k in _COORDS and listed:                   # `point` is also a label elsewhere: coordinates are listed values
            yield v


def audit(text, payload, run):
    out = run(text, payload)
    env, route, rec = out.response['envelope'], out.response['route_d'], out.receipt
    served = route['status'] == 'SERVED'
    v = []
    if served:
        goals = {g['goal_id'] for g in payload.get('math_goals') or ()}
        objs = (env.get('scene3d') or {}).get('objects') or []
        v += [] if env.get('status') == 'ok' else ['envelope_not_ok']
        v += [] if rec['engine'].get('status') == 'VERIFIED' and rec['engine'].get('kernel_check') else ['not_verified']
        v += [] if goals <= set(route.get('answer_exact') or {}) else [f"goal_dropped:{sorted(goals - set(route.get('answer_exact') or {}))}"]
        v += [] if objs and all(o.get('id') and o.get('type') for o in objs) else ['scene_objects']
        v += [] if all(isinstance(x, str) and _EXACT.fullmatch(x) for x in coordinates(env)) else ['inexact_coordinate']
        v += [] if route.get('construction_trace') else ['no_construction_trace']
    else:
        v += [] if (route.get('refusal') or {}).get('code') else ['refusal_without_code']
        v += [] if not route.get('answer_exact') and not route.get('answers') else ['refusal_with_answers']
        v += [] if env.get('status') != 'ok' else ['refusal_envelope_ok']
    # served AND refused, envelope AND route_d (review MINOR-5, D) — but not the planner's engineering trace, nor
    # `route_d.sections[].vertices[].label`, which by contract is a scene-object ID reference the frontend matches with
    # `o.id === v.label` (hybrid-preview-adapter.ts `kiemSectionsCore`), not display text (`B_prime` is right there)
    texts = [*learner_text(env), *learner_text({k: v for k, v in route.items() if k not in ('planner', 'sections')})]
    leaked = sorted({m for t in texts for m in _CODE.findall(t)}
                    | ({env['simulation_id']} if env.get('simulation_id') and any(env['simulation_id'] in t for t in texts)
                       else set()))
    v += [f'leaked:{leaked}'] if leaked else []
    lat = rec.get('individual_source_gate_planner_engine_latency')
    return {'served': served, 'code': rec.get('code'), 'violations': v, 'stage_latency': lat,
            'planner_label': ((route.get('planner') or {}).get('search_telemetry') or {}).get('classification')}


def _selfcheck():
    """The audit sees what it must (a witness window, CLAUDE.md §4.3): planted faults are reported, a clean row is not."""
    from types import SimpleNamespace as NS

    def fake(env, route, engine=None):
        return lambda _t, _p: NS(response={'envelope': env, 'route_d': route},
                                 receipt={'engine': engine or {'status': 'VERIFIED', 'kernel_check': True}, 'code': None})
    ok_env = {'status': 'ok', 'simulation_id': 'sim_x', 'title': 'Hình chóp', 'scene3d': {'objects': [
        {'id': 'A', 'type': 'point3', 'label': 'Điểm A', 'xyz': ['0', '1/2', '√3']}]}}
    ok_route = {'status': 'SERVED', 'answer_exact': {'q1': {}}, 'construction_trace': [{}]}
    p = {'math_goals': [{'goal_id': 'q1'}, {'goal_id': 'q2'}]}
    assert audit('', {'math_goals': [{'goal_id': 'q1'}]}, fake(ok_env, ok_route))['violations'] == []
    assert any(v.startswith('goal_dropped') for v in audit('', p, fake(ok_env, ok_route))['violations'])
    one = {'math_goals': [{'goal_id': 'q1'}]}
    for plant, want in ((lambda e: e['scene3d']['objects'][0].update(label='PLANE_NOT_UNIQUE'), 'leaked'),
                        (lambda e: e['scene3d']['objects'][0].update(label='khoi_S_ABCD'), 'leaked'),
                        (lambda e: e['scene3d'].update(events=[{'learner_text': 'A_prime'}]), 'leaked'),
                        (lambda e: e['scene3d']['objects'][0].update(xyz=['0.3333', '0', '0']), 'inexact_coordinate'),
                        (lambda e: e['scene3d']['objects'][0].update(xyz=['0.5√2', '0', '0']), 'inexact_coordinate'),
                        (lambda e: e['scene3d'].update(sections=[{'polygon': [['0.5', '1', '0']]}]), 'inexact_coordinate'),
                        (lambda e: e['scene3d'].update(planes=[{'normal': ['0.5', '1', '0']}]), 'inexact_coordinate'),
                        (lambda e: e['scene3d']['objects'][0].update(endpoints=[['1', '0.5', '0']]), 'inexact_coordinate'),
                        (lambda e: e['scene3d']['objects'][0].update(role='SECTION_VERTEX'), 'leaked')):
        bad = json.loads(json.dumps(ok_env))
        plant(bad)
        assert any(x.startswith(want) for x in audit('', one, fake(bad, ok_route))['violations']), (want, bad)
    for refused, route in (({'status': 'unsupported', 'learner_reason': 'Lỗi SOURCE_OBJECT_MISMATCH'},
                             {'status': 'REFUSED', 'refusal': {'code': 'X'}}),
                            ({'status': 'unsupported', 'reason': 'PLANE_NOT_UNIQUE'}, {'status': 'REFUSED', 'refusal': {'code': 'X'}}),
                            ({'status': 'unsupported'}, {'status': 'REFUSED', 'refusal': {'code': 'X', 'clarification': {
                                'question': 'Bạn muốn nói khoi_S_ABCD?'}}})):
        v = audit('', one, fake(refused, route))['violations']
        assert any(x.startswith('leaked') for x in v), v


if __name__ == '__main__':
    _selfcheck()
    from app.ai.hybrid_offline import hybrid_offline_policy, run_hybrid_offline
    from app.ai.typed_fact_next_extraction import ReplayExtractor
    policy = hybrid_offline_policy({'HYBRID_ROUTE_D_PREVIEW': '1'})

    def run(text, payload):
        return run_hybrid_offline(text, ReplayExtractor({text: payload}), policy=policy)
    rows = [{'group': g, 'id': cid, **audit(text, p, run)} for g, cid, text, p in corpora()]
    by = collections.defaultdict(lambda: collections.Counter())
    for r in rows:
        by[r['group']]['served' if r['served'] else 'not_served'] += 1
        by[r['group']]['violations'] += bool(r['violations'])
    s = {'rows': len(rows), 'by_group': {k: dict(v) for k, v in by.items()},
         'violations': [{k: r[k] for k in ('group', 'id', 'violations')} for r in rows if r['violations']],
         'planner_labels_of_served': dict(collections.Counter(r['planner_label'] for r in rows if r['served']))}
    print(json.dumps(s, ensure_ascii=False, indent=1))
    if len(sys.argv) > 1:
        import subprocess
        head = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip()
        with open(sys.argv[1], 'x', encoding='utf-8', newline='\n') as f:
            json.dump({'classification': 'OFFLINE_DETERMINISTIC_FIXTURE_TEST', 'provider_calls': 0, 'head': head,
                       'summary': s, 'rows': rows}, f, ensure_ascii=False, indent=1)
            f.write('\n')
