"""Reviewer-3: F7 exact class (served at 9772ea37): residual parent = another primary that geometrically contains the cut."""
from copy import deepcopy
def say(p, s):
    p['problem_text'] = p['problem_text'].rstrip() + ' ' + s; return s
def probes(F):
    def two():
        p = deepcopy(F.SIM['demo1-pyramid-derived-section']['payload'])
        q = say(p, 'Cho hình chóp T.ABCD. TA vuông góc với (ABCD). TA = 4.')
        p['solids'].append({'solid_id': 't_abcd', 'solid_type': 'pyramid', 'notation': 'T.ABCD', 'quote': 'Cho hình chóp T.ABCD.'})
        p['premises'] += [{'kind': 'perpendicular_line_plane', 'solid_id': 't_abcd', 'args': {'line': ['T', 'A'], 'plane': ['A', 'B', 'C', 'D']}, 'quote': 'TA vuông góc với (ABCD).'},
                          {'kind': 'segment_length', 'solid_id': 't_abcd', 'args': {'segment': ['T', 'A'], 'value': '4'}, 'quote': 'TA = 4.'}]
        return p
    def res(parent):
        p = two(); p['math_goals'].append({'goal_id': 'r', 'kind': 'residual_volume', 'parent_solid_id': parent, 'cut_solid_id': 's_top',
                                           'quote': p['math_goals'][1]['quote']}); return p
    def hyres():
        import json
        p = res('t_abcd'); return json.loads(json.dumps(p).replace('"t_abcd"', '"t-abcd-1"').replace('"s_top"', '"s-top"').replace('"s_abcd"', '"s-abcd"'))
    return [('F7x.two_primary_control', 'POS', two, None),
            ('F7x.residual_parent_other_primary', 'NEG', lambda: res('t_abcd'), None),
            ('F7x.residual_parent_other_hyphen_ids', 'NEG', hyres, None),
            ('F7x.residual_parent_own_control', 'POS', lambda: res('s_abcd'), two)]
