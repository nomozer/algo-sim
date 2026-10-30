"""Adversarial SG-3 grammar probes on Adapter /4. Usage: probes.py <backend_root> <out.json>. Offline, 0 provider calls."""
import json, os, socket, sys
from copy import deepcopy
ROOT = sys.argv[1]
sys.path.insert(0, ROOT); sys.dont_write_bytecode = True
os.environ['ALLOW_LIVE_AI'] = '0'
def _off(*a, **k): raise RuntimeError('OFFLINE_ONLY')
socket.socket.connect = _off; socket.create_connection = _off
from app.ai.adapter4_route import run_typed_fact_next_v2_route
from app.simulation.geometry_functions.typed_fact_next import TypedFactNextValidationError

CASES = json.load(open(r'D:/Documents/projects/algo-sim/.superpowers/worktrees/w4-geometry-pedagogy/docs/evaluation/geometry/runs/'
                       r'geometry-generalization-and-pedagogical-construction/dev-corpus/cases.json', encoding='utf-8'))


def mk(base, reps=(), prem=None):
    """Text replacements applied to problem_text and every quote; prem(list) mutates premises in place."""
    p = deepcopy(CASES[base]['payload'])
    def r(s):
        for a, b in reps:
            s = s.replace(a, b)
        return s
    p['problem_text'] = r(p['problem_text'])
    for coll in ('premises', 'solids', 'derived_sections', 'simulation_goals', 'math_goals'):
        for x in p.get(coll, []):
            if 'quote' in x:
                x['quote'] = r(x['quote'])
    if prem:
        prem(p['premises'])
    return p


def seg(prems, old, new_seg=None, value=None):
    for x in prems:
        if x['kind'] == 'segment_length' and x['args']['segment'] == old:
            if new_seg: x['args']['segment'] = new_seg
            if value: x['args']['value'] = value
            return
    raise KeyError(old)


def right_at(prems, v, verts=None):
    for x in prems:
        if x['kind'] == 'right_angle':
            x['args']['right_at'] = v
            if verts: x['args']['vertices'] = verts


P = {}
# (c) "chiều cao XY = n" where XY cannot be the height (SD ⊥ base is stated) -> inconsistent, must not serve
P['c1_height_SE_pyr'] = mk('TP1.tg_day.area', [('chiều cao SD = 12', 'chiều cao SE = 12')], lambda q: seg(q, ['S', 'D'], ['S', 'E']))
P['c1_height_SE_pyr_section'] = mk('TP1.tg_day.section', [('chiều cao SD = 12', 'chiều cao SE = 12')], lambda q: seg(q, ['S', 'D'], ['S', 'E']))
P['c2_height_SF_canon_style'] = mk('TP1.canon.area', [('và SD = 12', 'và chiều cao SF = 13')], lambda q: seg(q, ['S', 'D'], ['S', 'F'], '13'))
# prism: the height named as a face diagonal / base edge
P['c3_height_DEp_prism'] = mk('RP1.voi_so_do.area', [("độ dài DD' = 9", "chiều cao DE' = 13")], lambda q: seg(q, ['D', "D'"], ['D', "E'"], '13'))
P['c4_height_EF_prism_base'] = mk('RP1.voi_so_do.area', [("có số đo DE = 5", "chiều cao DE = 5")])
P['c5_height_SE_quad'] = mk('QP1.thoa_man.area', [('và cạnh SD = 15', 'và chiều cao SE = 17')], lambda q: seg(q, ['S', 'D'], ['S', 'E'], '17'))
P['c6_sodo_SE'] = mk('TP1.voi_so_do.area', [('độ dài SD = 12', 'số đo SE = 12')], lambda q: seg(q, ['S', 'D'], ['S', 'E']))  # literal: SE length (consistent)
# (d) "vuông ở X": wrong vertex via first-match of tại|ở
P['d1_can_o_E_vuong_o_D'] = mk('TP1.voi_so_do.area', [('tam giác vuông ở D', 'tam giác cân ở E vuông ở D')], lambda q: right_at(q, 'E'))
P['d1b_can_tai_E_vuong_tai_D'] = mk('TP1.canon.area', [('tam giác vuông tại D', 'tam giác cân tại E vuông tại D')], lambda q: right_at(q, 'E'))
P['d2_vuong_o_E_payload_D'] = mk('TP1.voi_so_do.area', [('vuông ở D', 'vuông ở E')])
P['d3_tgday_vuong_o_E_payload_D'] = mk('TP1.tg_day.area', [('vuông tại D', 'vuông ở E')])
P['d4_prism_vuong_o_F_payload_D'] = mk('RP1.voi_so_do.area', [('vuông ở D', 'vuông ở F')])
# (f) qualifier mismatch on the base noun
P['f1_tugiac_day_3v'] = mk('TP1.voi_so_do.area', [('với mặt đáy DEF', 'với tứ giác đáy DEF')])
P['f2_tgday_4v_rect'] = mk('QP1.voi_so_do.area', [('với tứ giác đáy DEFG', 'với tam giác đáy DEFG')])
P['f3_tugiac_day_vuong_tai'] = mk('TP1.tg_day.area', [('tam giác đáy DEF vuông', 'tứ giác đáy DEF vuông')])
P['f4_chop_tamgiac_4v'] = mk('QP1.thoa_man.area', [('hình chóp tứ giác S.DEFG', 'hình chóp tam giác S.DEFG')])
P['f5_tgday_hinhvuong'] = mk('CB1.voi_day.area', [('với đáy DEFG', 'với tam giác đáy DEFG')])
P['f6_tgday_rect_cuboid'] = mk('HB1.voi_so_do.area', [('với tứ giác đáy DEFG', 'với tam giác đáy DEFG')])
P['f7_lp_tugiac_day_prism3'] = mk('RP1.tg_day.area', [('tam giác đáy DEF', 'tứ giác đáy DEF')])
# (b) hidden conditional / disjunction / hypothesis with new connectors
P['b1_thoaman_neu'] = mk('TP1.thoa_man.area', [('thỏa mãn DE = 6', 'thỏa mãn nếu DE = 6')])
P['b2_biet_hoac'] = mk('TP1.thoa_man.area', [('biết DF = 8', 'biết DF = 8 hoặc DF = 9')])
P['b3_voi_mat_day_gia_su'] = mk('TP1.voi_so_do.area', [('đường thẳng SD vuông góc', 'giả sử đường thẳng SD vuông góc')])
P['b4_biet_rang_neu'] = mk('TP1.thoa_man.area', [('biết DF = 8', 'biết rằng nếu DF = 8')])
P['b5_thoaman_khi'] = mk('TP1.thoa_man.area', [('thỏa mãn DE = 6', 'thỏa mãn DE = 6 khi')])
P['b6_trong_kg_gia_su'] = mk('TP1.tg_day.area', [('Trong không gian, cho', 'Trong không gian, giả sử cho')])
P['b7_thoaman_khong'] = mk('TP1.thoa_man.area', [('thỏa mãn DE = 6', 'không thỏa mãn DE = 6')])
P['b8_biet_DE_khac'] = mk('TP1.thoa_man.area', [('biết DF = 8', 'biết DF ≠ 8')])
P['b9_neu_biet'] = mk('TP1.thoa_man.area', [('biết DF = 8', 'nếu biết DF = 8')])
P['b10_thoaman_mid_hoac'] = mk('TP1.thoa_man.area', [('thỏa mãn DE = 6', 'thỏa mãn DE = 6 hoặc thỏa mãn DE = 7')])
P['b11_trong_kg_twice'] = mk('TP1.tg_day.area', [('Trong không gian, cho', 'Trong không gian, Trong không gian, cho')])
P['b12_voi_day_sau_so'] = mk('TP1.voi_so_do.area', [('độ dài SD = 12', 'độ dài SD = 12 với đáy là tam giác khác')])
P['b13_biet_sau_so_no_comma'] = mk('TP1.thoa_man.area', [('thỏa mãn DE = 6, biết DF = 8', 'thỏa mãn DE = 6 biết DF = 8 sai')])
P['b14_thoa_man_trailing'] = mk('TP1.thoa_man.area', [('và cạnh SD = 12', 'và cạnh SD = 12 thỏa mãn')])
# (a) wrong-segment binding
P['a1_value_swap_DE_DF'] = mk('TP1.voi_so_do.area', [], lambda q: (seg(q, ['D', 'E'], value='8'), seg(q, ['D', 'F'], value='6')))
P['a2_chain_eq'] = mk('TP1.tg_day.area', [('chiều cao SD = 12', 'chiều cao SD = SE = 12')])
P['a3_chain_eq_SE'] = mk('TP1.tg_day.area', [('chiều cao SD = 12', 'chiều cao SE = SD = 12')], lambda q: seg(q, ['S', 'D'], ['S', 'E']))
P['a4_cube_side_on_top'] = mk('CB1.biet_mat_day.area', [('biết mặt đáy DEFG', "biết mặt đáy D'E'F'G'")])
P['a5_sodo_angle_word'] = mk('TP1.voi_so_do.area', [('có số đo DE = 6', 'có số đo góc DE = 6')])
P['a6_chieu_cao_of_face'] = mk('TP1.voi_so_do.area', [('độ dài SD = 12', 'chiều cao SD = 12 của tam giác SDE')])
# controls (must be served, same as canon twin)
P['ctl_TP1_canon'] = mk('TP1.canon.area')
P['ctl_TP1_tg_day'] = mk('TP1.tg_day.area')
P['ctl_RP1_canon'] = mk('RP1.canon.area')
P['ctl_QP1_canon'] = mk('QP1.canon.area')

out = {}
for k, p in P.items():
    try:
        r = run_typed_fact_next_v2_route(p)
        out[k] = {'status': r.status, 'code': r.code, 'answer': (r.answer_exact if r.status == 'SERVED' else None), 'reason': (r.reason or '')[:160]}
    except TypedFactNextValidationError as e:
        out[k] = {'status': 'REFUSED', 'code': e.code, 'answer': None, 'reason': str(e)[:160]}
    except Exception as e:  # noqa: BLE001
        out[k] = {'status': 'EXCEPTION', 'code': type(e).__name__, 'answer': None, 'reason': str(e)[:160]}
json.dump(out, open(sys.argv[2], 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
for k, v in out.items():
    print(f"{k:32s} {v['status']:9s} {str(v['code']):40s} {v['answer']}")
