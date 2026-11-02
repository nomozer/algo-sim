"""Continuation 19 §XI — the BACKEND output contract of Hybrid /4 on every group the corpora hold, through the production
opt-in path `run_hybrid_offline` (gold extractions, 0 provider calls). It checks JSON the frontend receives; it does not
show that a learner sees a correct rendering (no browser here).

Served rows must have: envelope status ok; route SERVED; engine VERIFIED with kernel_check; EVERY math goal of the
extraction answered; ≥ 1 scene object, each with id and type, point coordinates exact (no float); a construction trace;
no machine code (`UPPER_SNAKE`) or the envelope's simulation_id in learner-visible text (title, description, notes, object
labels). Non-served rows must carry a refusal code and no answer, and no scene answers.
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

_CODE = re.compile(r'\b[A-Z]{2,}(?:_[A-Z0-9]{2,})+\b')
_EXACT = re.compile(r"^-?[0-9]+(?:/[0-9]+)?$|√|π")


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


def learner_text(env):
    sc = env.get('scene3d') or {}
    yield from (str(env.get(k) or '') for k in ('title', 'description'))
    yield from (json.dumps(env.get('notes'), ensure_ascii=False),)
    for o in sc.get('objects') or ():
        yield from (str(o.get(k) or '') for k in ('label', 'display_label'))


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
        v += [] if all(isinstance(x, str) and _EXACT.search(x) for o in objs for x in o.get('xyz') or ()) else ['inexact_xyz']
        v += [] if route.get('construction_trace') else ['no_construction_trace']
        leaked = sorted({m for t in learner_text(env) for m in _CODE.findall(t)}
                        | ({env['simulation_id']} if env.get('simulation_id') and any(env['simulation_id'] in t
                                                                                         for t in learner_text(env)) else set()))
        v += [f'leaked:{leaked}'] if leaked else []
    else:
        v += [] if (route.get('refusal') or {}).get('code') else ['refusal_without_code']
        v += [] if not route.get('answer_exact') and not route.get('answers') else ['refusal_with_answers']
        v += [] if env.get('status') != 'ok' else ['refusal_envelope_ok']
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
    leak = json.loads(json.dumps(ok_env))
    leak['scene3d']['objects'][0]['label'] = 'PLANE_NOT_UNIQUE'
    leak['scene3d']['objects'][0]['xyz'] = ['0.3333', '0', '0']
    v = audit('', {'math_goals': [{'goal_id': 'q1'}]}, fake(leak, ok_route))['violations']
    assert 'inexact_xyz' in v and any(x.startswith('leaked') for x in v), v


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
