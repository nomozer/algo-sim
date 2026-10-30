"""Run adversarial v2 payloads through Adapter /4 on a given backend tree. Offline. usage: runner.py <backend_root> <inputs.json> <out.json>"""
import json, os, socket, sys
os.environ['ALLOW_LIVE_AI'] = '0'
def _off(*a, **k): raise RuntimeError('OFFLINE_ONLY')
socket.socket.connect = _off; socket.create_connection = _off
sys.dont_write_bytecode = True
sys.path.insert(0, sys.argv[1])
from app.ai.adapter4_route import run_typed_fact_next_v2_route
from app.simulation.geometry_functions.typed_fact_next import TypedFactNextValidationError
cases = json.load(open(sys.argv[2], encoding='utf-8'))
out = {}
for cid, p in cases.items():
    try:
        r = run_typed_fact_next_v2_route(json.loads(json.dumps(p)))
        out[cid] = [r.status, r.code, str(getattr(r, 'answer_exact', None)) if r.status == 'SERVED' else None]
    except TypedFactNextValidationError as e:
        out[cid] = ['REFUSED', e.code, None]
    except Exception as e:  # noqa
        out[cid] = ['EXCEPTION', type(e).__name__ + ':' + str(e)[:120], None]
json.dump(out, open(sys.argv[3], 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print('done', len(out))
