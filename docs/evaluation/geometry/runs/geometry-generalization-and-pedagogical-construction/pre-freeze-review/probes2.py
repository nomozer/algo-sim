"""Second round: 'chiều cao XY = n' role-drop probes, cross-route (Adapter /4, planner, Adapter /3). Usage: probes2.py <backend_root> <out.json>."""
import json, os, socket, sys
sys.path.insert(0, sys.argv[1]); sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); sys.dont_write_bytecode = True
os.environ['ALLOW_LIVE_AI'] = '0'
def _off(*a, **k): raise RuntimeError('OFFLINE_ONLY')
socket.socket.connect = _off; socket.create_connection = _off
sys.argv_saved = sys.argv; sys.argv = [sys.argv[0], sys.argv[1], os.devnull]
import importlib.util
spec = importlib.util.spec_from_file_location('pb', os.path.join(os.path.dirname(os.path.abspath(__file__)), 'probes.py'))
# reuse mk/seg helpers without re-running probes.py's main loop: exec only the helper part
src = open(spec.origin, encoding='utf-8').read().split('P = {}')[0]
ns = {}; exec(compile(src, spec.origin, 'exec'), ns)
mk, seg = ns['mk'], ns['seg']
from app.ai.adapter4_route import run_typed_fact_next_v2_route
from app.ai.function_route import run_typed_fact_next_planner_route
from app.ai.adapter3_simulation import run_typed_fact_next_route
from app.simulation.geometry_functions.typed_fact_next import TypedFactNextValidationError


def drop_perp(q):
    q[:] = [x for x in q if x['kind'] != 'perpendicular_line_plane']


P = {
    # QP1: SD ⊥ (DEFG) stated; "chiều cao SE = 17" -> SE is called the height (impossible). Height-dependent answer.
    'c5_QP1_thoa_man_chieu_cao_SE': mk('QP1.thoa_man.area', [('và cạnh SD = 15', 'và chiều cao SE = 17')], lambda q: seg(q, ['S', 'D'], ['S', 'E'], '17')),
    'c5b_QP1_voi_so_do_chieu_cao_SE': mk('QP1.voi_so_do.area', [('độ dài SD = 15', 'chiều cao SE = 17')], lambda q: seg(q, ['S', 'D'], ['S', 'E'], '17')),
    'c5c_QP1_canon_co_chieu_cao_SG': mk('QP1.canon.area', [('và SD = 15', 'và chiều cao SG = 18')], lambda q: seg(q, ['S', 'D'], ['S', 'G'], '18')),
    # TP2: plane ∥ SP, PR through N on SQ: height-dependent
    'c9_TP2_tg_day_chieu_cao_SQ': mk('TP2.tg_day.area', [('chiều cao SP = 14a', 'chiều cao SQ = 15a')], lambda q: seg(q, ['S', 'P'], ['S', 'Q'], '15a')),
    'c9b_TP2_tg_day_chieu_cao_SR': mk('TP2.tg_day.area', [('chiều cao SP = 14a', 'chiều cao SR = 15a')], lambda q: seg(q, ['S', 'P'], ['S', 'R'], '15a')),
    # no perpendicular stated at all, height named on SE (payload keeps no ⊥) -> apex undetermined
    'c7_QP1_no_perp_chieu_cao_SE': mk('QP1.voi_so_do.area', [('đường thẳng SD vuông góc với mặt phẳng (DEFG), ', ''), ('độ dài SD = 15', 'chiều cao SE = 17')],
                                      lambda q: (drop_perp(q), seg(q, ['S', 'D'], ['S', 'E'], '17'))),
    # control: consistent "chiều cao SD = 15" (= canon answer expected)
    'ctl_QP1_chieu_cao_SD': mk('QP1.voi_so_do.area', [('độ dài SD = 15', 'chiều cao SD = 15')]),
    'ctl_QP1_canon': mk('QP1.canon.area'),
    'ctl_TP2_tg_day': mk('TP2.tg_day.area'),
}


def run(fn, p):
    try:
        r = fn(json.loads(json.dumps(p)))
        st = r.status
        ans = getattr(r, 'answer_exact', None) if st == 'SERVED' else None
        return {'status': st, 'code': r.code, 'answer': ans, 'reason': (r.reason or '')[:140]}
    except TypedFactNextValidationError as e:
        return {'status': 'REFUSED', 'code': e.code, 'answer': None, 'reason': str(e)[:140]}
    except Exception as e:  # noqa: BLE001
        return {'status': 'EXCEPTION', 'code': type(e).__name__, 'answer': None, 'reason': str(e)[:140]}


out = {}
for k, p in P.items():
    out[k] = {'a4': run(run_typed_fact_next_v2_route, p), 'pl': run(run_typed_fact_next_planner_route, p), 'a3': run(run_typed_fact_next_route, p)}
json.dump(out, open(sys.argv_saved[2], 'w', encoding='utf-8'), ensure_ascii=False, indent=1, default=str)
for k, v in out.items():
    print(k)
    for n in ('a4', 'pl', 'a3'):
        print(f"   {n} {v[n]['status']:9s} {str(v[n]['code']):36s} {v[n]['answer']} {v[n]['reason'][:80] if v[n]['status'] != 'SERVED' else ''}")
