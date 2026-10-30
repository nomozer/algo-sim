"""Independent rerun of the locked 96-case Gate C scorer on a given tree; writes only to scratch."""
import importlib.util, json, os, socket, sys
def _deny(*a, **k): raise RuntimeError('network blocked')
socket.socket.connect = _deny; socket.create_connection = _deny; socket.getaddrinfo = _deny
os.environ.pop('ALLOW_LIVE_AI', None)
root, out = sys.argv[1], os.path.abspath(sys.argv[2])
RUN = os.path.join(root, 'docs/evaluation/geometry/runs/hybrid-v2-w3-f2-ratio-projection-language-grounding')
os.chdir(os.path.join(root, 'backend')); sys.path[:0] = [os.path.join(root, 'backend'), os.path.join(root, 'backend/tests/geometry')]
spec = importlib.util.spec_from_file_location('ev', os.path.join(RUN, 'tools/evaluate_development.py')); ev = importlib.util.module_from_spec(spec)
sys.modules['ev'] = ev; spec.loader.exec_module(ev)
oracle = json.load(open(os.path.join(RUN, 'inputs/oracle.json'), encoding='utf-8'))['cases']
rows = [ev.evaluate_case(c, oracle.get(c['id'])) for c in json.load(open(os.path.join(RUN, 'inputs/development.json'), encoding='utf-8'))['cases']]
s = {'match': sum(r['matches_expected'] for r in rows), 'total': len(rows), 'wrong_served': sum(r['outcome'] == 'WRONG_SERVED' for r in rows)}
json.dump({'summary': s, 'rows': [{k: r.get(k) for k in ('id', 'outcome', 'matches_expected', 'route_status', 'route_code')} for r in rows]}, open(out, 'w', encoding='utf-8'), indent=1)
print(s)
