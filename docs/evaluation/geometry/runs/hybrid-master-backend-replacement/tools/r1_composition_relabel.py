"""Fifteenth continuation (correction): re-label the thirteenth-continuation R-1 probe positives with the runner's
`composition_label`. C13 reported "9/9 DISCOVERED_FUNCTION_COMPOSITION" from the planner's own `search_telemetry`, which
counts as planner-made the step that only builds the point the extraction described (C15 review MAJOR-1).

Same rows, same gold, same route as `r1_described_point_probe.py` (its definitions are executed up to its run loop);
offline, 0 provider calls. Usage: r1_composition_relabel.py [out.json]
"""
import collections, json, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
_src = (HERE / 'r1_described_point_probe.py').read_text(encoding='utf-8')
_MARK = 'rows = [run(r) for r in ROWS]'
assert _src.count(_MARK) == 1, 'probe layout changed: re-check what is reused'
NS = {'__file__': str(HERE / 'r1_described_point_probe.py'), '__name__': 'r1_probe_defs'}
exec(compile(_src[:_src.index(_MARK)], 'r1_described_point_probe.py', 'exec'), NS)    # definitions only
sys.path.insert(0, str(NS['ROOT'] / 'backend' / 'scripts'))
import run_s2_student_language_pilot as R  # noqa: E402

out = []
for r in NS['ROWS']:
    if r['want'] is None or r['id'] in ('D1', 'D2'):
        continue
    route = NS['run_hybrid_offline'](r['text'], NS['ReplayExtractor']({r['text']: r['payload']}),
                                     policy=NS['POLICY']).response['route_d']
    planner = route.get('planner') or {}
    tel = planner.get('search_telemetry') or {}
    own = set(tel.get('planner_originated_steps') or ())
    steps = [{k: c.get(k) for k in ('id', 'fn', 'args')} for c in planner.get('calls') or () if c.get('id') in own]
    row = {'technical_failure': False, 'end_to_end_correct': route['status'] == 'SERVED',
           'expected': {'outcome': 'SERVED'}, 'observed': {'status': route['status']}, 'raw_extraction': r['payload'],
           'search': {'classification': tel.get('classification'), 'planner_steps': steps}, 'attribution': None}
    out.append({'id': r['id'], 'planner_label': tel.get('classification'), 'composition_label': R.composition_label(row),
                'planner_steps': [s['fn'] for s in steps],
                'beyond_description': [s['fn'] for s in R._beyond_description(steps, r['payload'])]})
    print(f"{r['id']:5s} {str(tel.get('classification')):34s} → {out[-1]['composition_label']:26s} {out[-1]['beyond_description']}")
summary = {'planner_label': dict(collections.Counter(x['planner_label'] for x in out)),
           'composition_label': dict(collections.Counter(x['composition_label'] for x in out))}
print(summary)
if len(sys.argv) > 1:
    with open(sys.argv[1], 'x', encoding='utf-8', newline='\n') as f:
        json.dump({'classification': 'IMPLEMENTER_AUTHORED_DEVELOPMENT_DIAGNOSTIC', 'provider_calls': 0,
                   'corrects': 'r1-described-point-probe-r2.json (planner self-label DISCOVERED_FUNCTION_COMPOSITION)',
                   'summary': summary, 'rows': out}, f, ensure_ascii=False, indent=1)
        f.write('\n')
