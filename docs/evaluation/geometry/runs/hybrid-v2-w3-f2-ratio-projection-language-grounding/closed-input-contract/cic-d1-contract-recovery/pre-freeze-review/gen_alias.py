"""Alias-degenerate targets (qualified duplicate of an unqualified label): string-distinct, geometrically degenerate."""
import json
from copy import deepcopy
C = json.load(open('cases_probe.json', encoding='utf-8'))
base = C['G.distance.segment.plain']['payload']
T = {'seg_A_prA': ('distance', {'segment': ['A', 'pr::A']}, "Tính độ dài AA."),
     "seg_A'_prA'": ('distance', {'segment': ["A'", "pr::A'"]}, "Tính độ dài A'A'."),
     'seg_prA_prA': ('distance', {'segment': ['pr::A', 'pr::A']}, "Tính độ dài AA."),
     'pt_line_alias': ('distance', {'point': "A'", 'line': ['B', 'pr::B']}, "Tính khoảng cách từ A' đến đường thẳng BB."),
     'lines_alias': ('distance', {'line1': ['A', "A'"], 'line2': ['C', 'pr::C']}, "Tính khoảng cách giữa hai đường thẳng AA' và CC."),
     'angle_same_line': ('angle', {'line1': ["A'", 'B'], 'line2': ['pr::B', "pr::A'"]}, "Tính góc giữa hai đường thẳng A'B và BA'."),
     'angle_line_alias': ('angle', {'line1': ["A'", 'B'], 'line2': ['A', 'pr::A']}, "Tính góc giữa hai đường thẳng A'B và AA."),
     'angle_lp_alias': ('angle', {'line': ["B'", 'pr::B\''], 'plane': ['A', 'B', 'C']}, "Tính góc giữa đường thẳng B'B' và mặt phẳng (ABC)."),
     'area_poly_alias': ('area', {'polygon': ['A', 'B', 'pr::A']}, "Tính diện tích tam giác ABA."),
     'pt_plane_alias3': ('distance', {'point': "A'", 'plane': ['A', 'B', 'pr::B']}, "Tính khoảng cách từ A' đến mặt phẳng (ABB)."),
     'lp_alias': ('distance', {'line': ["B'", "pr::B'"], 'plane': ['A', 'B', 'C']}, "Tính khoảng cách giữa đường thẳng B'B' và mặt phẳng (ABC)."),
     }
out = {}
for k, (gt, t, q) in T.items():
    p = deepcopy(base); p['problem_text'] = p['problem_text'].rsplit(' Tính', 1)[0] + ' ' + q
    g = p['math_goals'][-1]; g.update(goal_type=gt, target=t, quote=q)
    out['ALIAS.' + k] = {'payload': p}
json.dump(out, open('cases_alias.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print(len(out))
