"""Attacks against the B1 fix (_vai_doan_ok). Usage: probes6.py <backend_root>. Offline, 0 provider calls."""
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.argv = [sys.argv[0], sys.argv[1], os.devnull]
src = open(os.path.join(HERE, 'probes.py'), encoding='utf-8').read().split('P = {}')[0]
ns = {}; exec(compile(src, 'probes.py', 'exec'), ns); mk, seg = ns['mk'], ns['seg']
src4 = open(os.path.join(HERE, 'probes4.py'), encoding='utf-8').read().split('for name, p in')[0]
ns4 = {}; exec(compile(src4, 'probes4.py', 'exec'), ns4); reg = ns4['payload']
from app.ai.adapter4_route import run_typed_fact_next_v2_route


def add(prem):
    return lambda q: q.insert(len(q) - 1, prem)


def perp(line, plane, quote):
    return {'kind': 'perpendicular_line_plane', 'args': {'line': line, 'plane': plane}, 'quote': quote, 'solid_id': 's1'}


def drop(kind):
    return lambda q: q.__setitem__(slice(None), [x for x in q if x['kind'] != kind])


def chain(*fs):
    return lambda q: [f(q) for f in fs]


DP = "DD'"
P = {}
# A: circular — the "chiều cao SA" quote reused as evidence of SA ⊥ base, on a REGULAR pyramid (inconsistent)
a = reg('chiều cao SA = 3', ['S', 'A'], '3'); a['premises'].insert(3, perp(['S', 'A'], ['A', 'B', 'C', 'D'], 'chiều cao SA = 3'))
P['A_regular_circular_perp_quote'] = a
# B: quad pyramid, NO ⊥ in text, height named SE; SE ⊥ quoted by the height clause (genuine reading) vs explicit twin
QPT = ('đường thẳng SD vuông góc với mặt phẳng (DEFG), ', '')
P['B_genuine_height_SE_from_quote'] = mk('QP1.voi_so_do.area', [QPT, ('độ dài SD = 15', 'chiều cao SE = 17')],
                                         chain(drop('perpendicular_line_plane'), lambda q: seg(q, ['S', 'D'], ['S', 'E'], '17'),
                                               add(perp(['S', 'E'], ['D', 'E', 'F', 'G'], 'chiều cao SE = 17'))))
P['B_twin_explicit_SE_perp'] = mk('QP1.voi_so_do.area',
                                  [('đường thẳng SD vuông góc với mặt phẳng (DEFG)', 'đường thẳng SE vuông góc với mặt phẳng (DEFG)'),
                                   ('độ dài SD = 15', 'độ dài SE = 17')],
                                  chain(drop('perpendicular_line_plane'), lambda q: seg(q, ['S', 'D'], ['S', 'E'], '17'),
                                        add(perp(['S', 'E'], ['D', 'E', 'F', 'G'], 'đường thẳng SE vuông góc với mặt phẳng (DEFG)'))))
# C: SD ⊥ stated AND SE ⊥ smuggled via the height quote (inconsistent: two perpendiculars from S)
P['C_two_perps_via_height_quote'] = mk('QP1.voi_so_do.area', [('độ dài SD = 15', 'chiều cao SE = 17')],
                                       chain(lambda q: seg(q, ['S', 'D'], ['S', 'E'], '17'), add(perp(['S', 'E'], ['D', 'E', 'F', 'G'], 'chiều cao SE = 17'))))
# D: oblique prism text with right_prism payload
P['D_xien_chieu_cao_DDp'] = mk('RP1.voi_so_do.area', [('lăng trụ đứng', 'lăng trụ xiên'), (f'độ dài {DP} = 9', f'chiều cao {DP} = 9')])
P['D_xien_canh_ben_DDp'] = mk('RP1.voi_so_do.area', [('lăng trụ đứng', 'lăng trụ xiên'), (f'độ dài {DP} = 9', f'cạnh bên {DP} = 9')])
P['D_xien_plain_DDp'] = mk('RP1.voi_so_do.area', [('lăng trụ đứng', 'lăng trụ xiên')])
P['D_unqualified_chieu_cao_DDp'] = mk('RP1.voi_so_do.area', [('lăng trụ đứng', 'lăng trụ'), (f'độ dài {DP} = 9', f'chiều cao {DP} = 9')])
P['D_unqualified_plain'] = mk('RP1.voi_so_do.area', [('lăng trụ đứng', 'lăng trụ')])
# E: cube top edge / face diagonal named lateral / height
P['E_cube_canh_ben_top_edge'] = mk('CB1.biet_mat_day.area', [(f'cạnh bên {DP} = 8', "cạnh bên D'E' = 8")], lambda q: seg(q, ['D', "D'"], ["D'", "E'"]))
P['E_cube_chieu_cao_top_edge'] = mk('CB1.biet_mat_day.area', [(f'cạnh bên {DP} = 8', "chiều cao D'E' = 8")], lambda q: seg(q, ['D', "D'"], ["D'", "E'"]))
P['E_cube_canh_ben_face_diag'] = mk('CB1.biet_mat_day.area', [(f'cạnh bên {DP} = 8', "cạnh bên DE' = 8")], lambda q: seg(q, ['D', "D'"], ['D', "E'"]))
P['E_cube_chieu_cao_reversed'] = mk('CB1.biet_mat_day.area', [(f'cạnh bên {DP} = 8', "chiều cao D'D = 8")], lambda q: seg(q, ['D', "D'"], ["D'", 'D']))
# F: role prefixes combined / chained (SD ⊥ stated)
P['F_do_dai_chieu_cao_SE'] = mk('QP1.voi_so_do.area', [('độ dài SD = 15', 'độ dài chiều cao SE = 17')], lambda q: seg(q, ['S', 'D'], ['S', 'E'], '17'))
P['F_voi_chieu_cao_SE_bang'] = mk('QP1.voi_so_do.area', [('độ dài SD = 15', 'với chiều cao SE bằng 17')], lambda q: seg(q, ['S', 'D'], ['S', 'E'], '17'))
P['F_so_do_chieu_cao_SE'] = mk('QP1.voi_so_do.area', [('độ dài SD = 15', 'số đo chiều cao SE = 17')], lambda q: seg(q, ['S', 'D'], ['S', 'E'], '17'))
P['F_chain_SD_eq_SE_both'] = mk('QP1.voi_so_do.area', [('độ dài SD = 15', 'chiều cao SD = SE = 15')],
                                add({'kind': 'segment_length', 'args': {'segment': ['S', 'E'], 'value': '15'}, 'quote': 'chiều cao SD = SE = 15', 'solid_id': 's1'}))
P['F_chain_SD_eq_SE_only_SD'] = mk('QP1.voi_so_do.area', [('độ dài SD = 15', 'chiều cao SD = SE = 15')])
P['F_chain_SE_eq_SD_only_SD'] = mk('QP1.voi_so_do.area', [('độ dài SD = 15', 'chiều cao SE = SD = 15')])
P['F_chain_DE_eq_SD'] = mk('QP1.voi_so_do.area', [('có số đo DE = 7', 'có số đo DE = 7'), ('độ dài SD = 15', 'chiều cao SD = DG = 15')])
P['F_canh_ben_chieu_cao_SE'] = mk('QP1.voi_so_do.area', [('độ dài SD = 15', 'cạnh bên chiều cao SE = 17')], lambda q: seg(q, ['S', 'D'], ['S', 'E'], '17'))
# H: height claim outside the prefix
P['H_SE_la_chieu_cao'] = mk('QP1.voi_so_do.area', [('độ dài SD = 15', 'SE là chiều cao của hình chóp, SE = 17')], lambda q: seg(q, ['S', 'D'], ['S', 'E'], '17'))
P['H_SE_eq_la_chieu_cao'] = mk('QP1.voi_so_do.area', [('độ dài SD = 15', 'SE = 17 là chiều cao')], lambda q: seg(q, ['S', 'D'], ['S', 'E'], '17'))
P['H_chieu_cao_la_SE'] = mk('QP1.voi_so_do.area', [('độ dài SD = 15', 'chiều cao là SE = 17')], lambda q: seg(q, ['S', 'D'], ['S', 'E'], '17'))
P['H_duong_cao_SE'] = mk('QP1.voi_so_do.area', [('độ dài SD = 15', 'đường cao SE = 17')], lambda q: seg(q, ['S', 'D'], ['S', 'E'], '17'))
P['H_separate_sentence'] = mk('QP1.voi_so_do.area', [('độ dài SD = 15.', 'độ dài SE = 17. Chiều cao của hình chóp là SE.')], lambda q: seg(q, ['S', 'D'], ['S', 'E'], '17'))
# G: height foot H = midpoint of DE (not a base vertex)
GT = ('đường thẳng SD vuông góc với mặt phẳng (DEFG)', 'H là trung điểm của DE, đường thẳng SH vuông góc với mặt phẳng (DEFG)')


def gprem(q):
    for x in q:
        if x['kind'] == 'perpendicular_line_plane':
            x['args']['line'] = ['S', 'H']; x['quote'] = 'đường thẳng SH vuông góc với mặt phẳng (DEFG)'
    q.insert(1, {'kind': 'midpoint', 'args': {'point': 'H', 'segment': ['D', 'E']}, 'quote': 'H là trung điểm của DE', 'solid_id': 's1'})


P['G_ctl_chieu_cao_SH'] = mk('QP1.voi_so_do.area', [GT, ('độ dài SD = 15', 'chiều cao SH = 15')], chain(gprem, lambda q: seg(q, ['S', 'D'], ['S', 'H'])))
P['G_ctl_plain_SH'] = mk('QP1.voi_so_do.area', [GT, ('độ dài SD = 15', 'độ dài SH = 15')], chain(gprem, lambda q: seg(q, ['S', 'D'], ['S', 'H'])))
P['G_atk_chieu_cao_SD'] = mk('QP1.voi_so_do.area', [GT, ('độ dài SD = 15', 'chiều cao SD = 15')], gprem)
P['G_atk_chieu_cao_SE'] = mk('QP1.voi_so_do.area', [GT, ('độ dài SD = 15', 'chiều cao SE = 15')], chain(gprem, lambda q: seg(q, ['S', 'D'], ['S', 'E'])))
P['G_atk_canh_ben_SH'] = mk('QP1.voi_so_do.area', [GT, ('độ dài SD = 15', 'cạnh bên SH = 15')], chain(gprem, lambda q: seg(q, ['S', 'D'], ['S', 'H'])))
# J: right prism, other edges named height / lateral
P['J_prism_chieu_cao_DEp'] = mk('RP1.voi_so_do.area', [(f'độ dài {DP} = 9', "chiều cao DE' = 13")], lambda q: seg(q, ['D', "D'"], ['D', "E'"], '13'))
P['J_prism_chieu_cao_EEp'] = mk('RP1.voi_so_do.area', [(f'độ dài {DP} = 9', "chiều cao EE' = 9")], lambda q: seg(q, ['D', "D'"], ['E', "E'"]))
P['J_prism_chieu_cao_DE_base'] = mk('RP1.voi_so_do.area', [('có số đo DE = 5', 'chiều cao DE = 5')])

for name, p in P.items():
    try:
        r = run_typed_fact_next_v2_route(p)
        row = (r.status, r.code, getattr(r, 'answer_exact', None) if r.status == 'SERVED' else (r.reason or '')[:70])
    except Exception as e:  # noqa: BLE001
        row = ('EXC', type(e).__name__, str(e)[:70])
    print(f'{name:32s}', *row)
