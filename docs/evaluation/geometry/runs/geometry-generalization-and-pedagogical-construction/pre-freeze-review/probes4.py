"""Regular pyramid: 'chiều cao SA = 3' (SA is a lateral edge; never the height). Usage: probes4.py <backend_root>"""
import json, os, socket, sys
sys.path.insert(0, sys.argv[1]); sys.dont_write_bytecode = True
os.environ['ALLOW_LIVE_AI'] = '0'
socket.socket.connect = lambda *a, **k: (_ for _ in ()).throw(RuntimeError('OFFLINE_ONLY'))
from app.ai.adapter4_route import run_typed_fact_next_v2_route
from app.simulation.geometry_functions.typed_fact_next import TypedFactNextValidationError

def payload(stmt, seg, val, extra=''):
    lead = 'Cho hình chóp đều S.ABCD'
    s1 = f'{lead} có đáy ABCD là hình vuông cạnh 2, {stmt}{extra}.'
    pt = 'Lấy điểm K trên cạnh AB sao cho AK = 1/2 AB'
    pl = 'Gọi (α) là mặt phẳng qua K, song song với hai đường thẳng SA và AD'
    q = 'Hãy tính diện tích thiết diện tạo bởi mặt phẳng (α) với hình chóp S.ABCD'
    return {'schema_version': 'typed-fact-next/2', 'problem_text': f'{s1} {pt}. {pl}. {q}.', 'length_unit': '1',
            'solids': [{'solid_id': 's1', 'solid_type': 'pyramid', 'notation': 'S.ABCD', 'quote': lead}],
            'premises': [{'kind': 'regular_pyramid', 'args': {'apex': 'S', 'base': ['A', 'B', 'C', 'D']}, 'quote': lead, 'solid_id': 's1'},
                         {'kind': 'base_is_square', 'args': {'vertices': ['A', 'B', 'C', 'D'], 'side': '2'}, 'quote': 'có đáy ABCD là hình vuông cạnh 2', 'solid_id': 's1'},
                         {'kind': 'segment_length', 'args': {'segment': seg, 'value': val}, 'quote': stmt, 'solid_id': 's1'},
                         {'kind': 'divide_segment', 'args': {'point': 'K', 'segment': ['A', 'B'], 'ratio': '1/2'}, 'quote': pt, 'solid_id': 's1'}],
            'derived_sections': [{'section_id': 'sec', 'plane_name': 'α', 'target_solid_id': 's1', 'through_point': 'K', 'plane_kind': 'through_point_parallel_two_lines',
                                  'parallel_line_a': ['S', 'A'], 'parallel_line_b': ['A', 'D'], 'quote': pl, 'stated_intersections': []}],
            'relations': [], 'simulation_goals': [{'goal_id': 'sg1', 'kind': 'construct_object', 'target_solid_id': 's1', 'quote': lead}],
            'math_goals': [{'goal_id': 'mg1', 'kind': 'measurement', 'goal_type': 'area', 'solid_id': 's1', 'target': {'section_id': 'sec'}, 'quote': q}]}

for name, p in {'ctl_canh_ben_SA_3': payload('cạnh bên SA = 3', ['S', 'A'], '3'),
                'ctl_SA_3': payload('SA = 3', ['S', 'A'], '3'),
                'atk_chieu_cao_SA_3': payload('chiều cao SA = 3', ['S', 'A'], '3'),
                'atk_so_do_SA_3': payload('số đo SA = 3', ['S', 'A'], '3')}.items():
    try:
        r = run_typed_fact_next_v2_route(p); print(name, r.status, r.code, getattr(r, 'answer_exact', None) if r.status == 'SERVED' else (r.reason or '')[:100])
    except TypedFactNextValidationError as e: print(name, 'REFUSED', e.code)
