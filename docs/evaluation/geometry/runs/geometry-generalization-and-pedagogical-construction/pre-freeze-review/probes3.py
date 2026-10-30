"""Try the height role-drop probes as typed-fact-next/1 on planner and Adapter /3. Usage: probes3.py <backend_root>"""
import json, os, socket, sys
sys.path.insert(0, sys.argv[1]); sys.dont_write_bytecode = True
os.environ['ALLOW_LIVE_AI'] = '0'
socket.socket.connect = lambda *a, **k: (_ for _ in ()).throw(RuntimeError('OFFLINE_ONLY'))
from app.ai.function_route import run_typed_fact_next_planner_route
from app.ai.adapter3_simulation import run_typed_fact_next_route
d = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'probes2-inputs.json'), encoding='utf-8'))
for k, p in d.items():
    p = {**p, 'schema_version': 'typed-fact-next/1'}
    for n, fn in (('pl', run_typed_fact_next_planner_route), ('a3', run_typed_fact_next_route)):
        try:
            r = fn(json.loads(json.dumps(p))); print(k, n, r.status, r.code, getattr(r, 'answer_exact', None) if r.status == 'SERVED' else (r.reason or '')[:90])
        except Exception as e: print(k, n, 'EXC', type(e).__name__, str(e)[:90])
