import json
from copy import deepcopy
C = json.load(open('cases_probe.json', encoding='utf-8'))
n2 = C['O.own.pyr1.MB']['payload']; a01 = C['D.top.vol']['payload']
def vol(base, t, gsid=None, gid='m_vol_pyr1'):
    p = deepcopy(base)
    for g in p['math_goals']:
        if g['goal_id'] == gid:
            g['target'] = t
            if gsid: g['solid_id'] = gsid
    return p
X = {
 'E.n2.vol.solid1_id2': vol(n2, {'solid': 'pyr1', 'solid_id': 'pyr2'}),
 'E.n2.vol.goal2_solid1': vol(n2, {'solid': 'pyr1'}, 'pyr2'),
 'E.n2.vol.goal1_solid_notation': vol(n2, {'solid': 'S.ABC'}, 'pyr1'),
 'E.n2.vol.goal2_notation1': vol(n2, {'solid': 'S.ABC'}, 'pyr2'),
 'E.n2.vol.id_only_goal2': vol(n2, {'solid_id': 'pyr1'}, 'pyr2'),
 'E.a01.vol.top_main': vol(a01, {'solid': 'top_pyramid', 'solid_id': 'main_pyramid'}, gid='q'),
 'E.a01.area.goal_top_sec': vol(a01, {'section_id': 'sec_alpha'}, 'top_pyramid', gid='math_sec_area'),
}
json.dump({k: {'payload': v} for k, v in X.items()}, open('cases_extra.json', 'w', encoding='utf-8'), ensure_ascii=False)
