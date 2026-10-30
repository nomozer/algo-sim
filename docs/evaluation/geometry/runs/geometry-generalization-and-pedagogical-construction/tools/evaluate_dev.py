"""Run the W4 dev corpus on Adapter /4 (the Wave 3 route) offline; print and optionally save outcomes."""
import json, os, socket, subprocess, sys
from pathlib import Path
W = Path(__file__).resolve().parents[1]; ROOT = W.parents[4]
sys.path.insert(0, str(ROOT / 'backend')); sys.dont_write_bytecode = True
os.environ['ALLOW_LIVE_AI'] = '0'
socket.socket.connect = lambda *a, **k: (_ for _ in ()).throw(RuntimeError('OFFLINE_ONLY'))
from app.ai.adapter4_route import run_typed_fact_next_v2_route
from app.simulation.geometry_functions.typed_fact_next import TypedFactNextValidationError
cases = json.loads((W / 'dev-corpus/cases.json').read_text(encoding='utf-8'))
rows = {}
for cid, c in cases.items():
    try:
        r = run_typed_fact_next_v2_route(json.loads(json.dumps(c['payload'])))
        rows[cid] = {'status': r.status, 'code': r.code, 'answer': getattr(r, 'answer_exact', None) if r.status == 'SERVED' else None,
                     'reason': (r.reason or '')[:200]}
    except TypedFactNextValidationError as e:
        rows[cid] = {'status': 'REFUSED', 'code': e.code, 'answer': None, 'reason': str(e)[:200]}
summary = {}
for cid, c in cases.items():
    r = rows[cid]
    if c['class'] == 'CANON':
        ok = r['status'] == 'SERVED'
    elif c['class'] == 'VARIANT':
        o = rows[c['oracle']]; ok = r['status'] == 'SERVED' and o['status'] == 'SERVED' and r['answer'] == o['answer']
    else:
        ok = r['status'] != 'SERVED'
    r['pass'] = ok
    summary.setdefault(c['class'], [0, 0]); summary[c['class']][0] += ok; summary[c['class']][1] += 1
for cid, r in rows.items():
    print(('PASS ' if r['pass'] else 'FAIL ') + cid, r['status'], r['code'], r['reason'][:110] if not r['pass'] else '')
print(json.dumps(summary))
if len(sys.argv) > 1:
    head = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip()
    with (W / sys.argv[1]).open('x', encoding='utf-8', newline='\n') as f:
        json.dump({'head': head, 'dirty_product': bool(subprocess.check_output(['git', 'status', '--porcelain', '--', 'backend/app'], cwd=ROOT, text=True).strip()),
                   'summary': summary, 'rows': rows, 'live_provider_calls': 0}, f, ensure_ascii=False, indent=1); f.write('\n')
