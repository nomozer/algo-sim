"""Automated pedagogical proxies over the served W4 dev corpus (Adapter /4). Offline; writes pedagogy-metrics.json once.
Proxies only: they show what the learner is SHOWN, not that students learn better."""
import json, os, re, sys
from collections import Counter
from pathlib import Path
W = Path(__file__).resolve().parents[1]; ROOT = W.parents[4]
sys.path.insert(0, str(ROOT / 'backend')); sys.dont_write_bytecode = True; os.environ['ALLOW_LIVE_AI'] = '0'
from app.ai.adapter4_route import run_typed_fact_next_v2_route
cases = json.loads((W / 'dev-corpus/cases.json').read_text(encoding='utf-8'))
rows = []
for cid, c in sorted(cases.items()):
    if c['class'] == 'NEGATIVE' or not cid.endswith('.area'):
        continue
    r = run_typed_fact_next_v2_route(c['payload'])
    if r.status != 'SERVED':
        continue
    ev = r.scene3d['events']; steps = r.scene3d['formation']['steps']
    ext = [e for e in ev if e['action'] == 'EXTEND']
    kinds = [e['semantic_kind'] for e in ev]
    order_ok = (ev[0]['action'] == 'INIT' and kinds[-1] == 'FINAL_RESULT'
                and min([i for i, e in enumerate(ev) if e['action'] == 'EXTEND'] or [len(ev)])
                > max([i for i, e in enumerate(ev) if (r.scene3d and any(o['id'] == e['object'] and o['type'] == 'plane3' for o in r.scene3d['objects']))] or [-1]))
    rows.append({'case': cid, 'geometry': c['geometry'], 'events': len(ev), 'formation_steps': len(steps),
                 'events_eq_formation': len(ev) == len(steps),
                 'every_step_has_learner_text': all((e.get('learner_text') or '').strip() for e in ev),
                 'no_machine_ids_in_text': not any(re.search(r'\b\w+_\w+\b', (e.get('learner_text') or '') + (e.get('justification_text') or '')) for e in ev),
                 'section_edge_steps': len(ext), 'justified_section_edge_steps': sum(bool(e.get('justification_text')) for e in ext),
                 'plane_before_edges_and_result_last': order_ok})
agg = {'cases': len(rows),
       'section_edge_steps': sum(r['section_edge_steps'] for r in rows),
       'justified_section_edge_steps': sum(r['justified_section_edge_steps'] for r in rows),
       'all_steps_narrated': all(r['every_step_has_learner_text'] for r in rows),
       'no_machine_ids': all(r['no_machine_ids_in_text'] for r in rows),
       'events_eq_formation_steps': all(r['events_eq_formation'] for r in rows),
       'teaching_order_ok': all(r['plane_before_edges_and_result_last'] for r in rows),
       'justified_by_geometry': dict(Counter(r['geometry'] for r in rows for _ in range(r['justified_section_edge_steps'])))}
with (W / 'pedagogy-metrics.json').open('x', encoding='utf-8', newline='\n') as f:
    json.dump({'scope': 'W4 dev corpus served .area cases, Adapter /4', 'aggregate': agg, 'rows': rows, 'live_provider_calls': 0}, f, ensure_ascii=False, indent=1); f.write('\n')
print(json.dumps(agg, ensure_ascii=False))
