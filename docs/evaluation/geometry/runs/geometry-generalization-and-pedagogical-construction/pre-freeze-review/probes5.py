"""Pre-existing analog: 'cạnh bên XY' / 'đường chéo XY' prefixes on a base edge. Usage: probes5.py <backend_root>"""
import json, os, socket, sys
sys.argv = [sys.argv[0], sys.argv[1], os.devnull]
src = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'probes.py'), encoding='utf-8').read().split('P = {}')[0]
ns = {}; exec(compile(src, 'probes.py', 'exec'), ns); mk = ns['mk']
from app.ai.adapter4_route import run_typed_fact_next_v2_route
for name, p in {'canh_ben_DG_quad': mk('QP1.canon.area', [('DG = 10', 'cạnh bên DG = 10')]),
                'duong_cheo_DG_quad': mk('QP1.canon.area', [('DG = 10', 'đường chéo DG = 10')]),
                'chieu_cao_DG_quad': mk('QP1.canon.area', [('DG = 10', 'chiều cao DG = 10')])}.items():
    try:
        r = run_typed_fact_next_v2_route(p); print(name, r.status, r.code, getattr(r, 'answer_exact', None) if r.status == 'SERVED' else '')
    except Exception as e: print(name, 'EXC', type(e).__name__, str(e)[:80])
