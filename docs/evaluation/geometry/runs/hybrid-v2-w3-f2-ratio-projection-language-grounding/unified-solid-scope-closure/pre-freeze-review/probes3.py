"""Reviewer-3 probes, part 3: S8 identity vs fallback on the same construction, ratio target on fully-served fixture,
curved hyphen ids, curved relation silent ignore."""
from copy import deepcopy


def say(p, s):
    p['problem_text'] = p['problem_text'].rstrip() + ' ' + s
    return s


def probes(F):
    P = []
    def add(name, expect, base=None):
        def deco(fn):
            P.append((name, expect, fn, base)); return fn
        return deco

    def supm(frame=None):
        p = deepcopy(F.SUP)
        q = say(p, 'Gọi M là trung điểm của SB. Tính độ dài MB.')
        p['premises'].append({'kind': 'point_is_midpoint', 'solid_id': 's1', 'args': {'point': 'M', 'segment': ['S', 'B']},
                              'quote': 'Gọi M là trung điểm của SB.'})
        if frame:
            p['solids'][0]['coordinate_frame_id'] = frame
        return p
    def goal(p, target, **kw):
        p['math_goals'].append({'goal_id': 'mm', 'kind': 'measurement', 'goal_type': 'distance', 'quote': 'Tính độ dài MB.',
                                'target': target, **kw}); return p
    add('S8.sup_M_control', 'POS', lambda: deepcopy(F.SUP))(supm)
    add('S8.sup_M_frame_fallback_control', 'POS', supm)(lambda: supm('f1'))
    add('S8.sup_M_s2_identity_path', 'NEG')(lambda: goal(supm(), {'solid_id': 's2', 'segment': ['M', 'B']}))
    add('S8.sup_M_s2_fallback_path', 'NEG')(lambda: goal(supm('f1'), {'solid_id': 's2', 'segment': ['M', 'B']}))
    add('S8.sup_M_s2_goal_level_fallback', 'NEG')(lambda: goal(supm('f1'), {'segment': ['M', 'B']}, solid_id='s2'))
    add('S8.sup_M_s1_fallback_control', 'POS', lambda: supm('f1'))(lambda: goal(supm('f1'), {'solid_id': 's1', 'segment': ['M', 'B']}))
    @add('S8.sup_M_containment_whole_s2_fallback', 'NEG')
    def _():
        p = supm('f1'); p['relations'] = [{'relation_id': 'rc', 'kind': 'containment', 'container_ref': 's2', 'member_ref': 'M',
                                           'quote': 'Gọi M là trung điểm của SB.'}]; return p
    @add('S8.sup_M_containment_whole_s2_identity', 'NEG')
    def _():
        p = supm(); p['relations'] = [{'relation_id': 'rc', 'kind': 'containment', 'container_ref': 's2', 'member_ref': 'M',
                                       'quote': 'Gọi M là trung điểm của SB.'}]; return p
    add('M.str_segment_target_s1_fallback', 'NEG')(lambda: goal(supm('f1'), {'solid_id': 's1', 'segment': 'TA'}))

    # ratio target on a fixture every route serves (demo5: pyr_s/pyr_t ratio)
    d5 = lambda: deepcopy(F.SIM['demo5-selection-and-highlighting']['payload'])
    add('B.demo5_base', 'POS')(d5)
    @add('K.demo5_ratio_target_solid_id_ghost', 'NEG')
    def _():
        p = d5(); p['math_goals'][0]['target'] = {'solid_id': 'ghost'}; return p
    @add('K.demo5_ratio_target_solid_ghost', 'NEG')
    def _():
        p = d5(); p['math_goals'][0]['target'] = {'solid': 'ghost'}; return p
    @add('K.demo5_ratio_with_cut_solid', 'NEG')
    def _():
        p = d5(); p['math_goals'][0]['cut_solid_id'] = 'pyr_t'; return p
    @add('K.demo5_highlight_with_derived_solid_id_ghost', 'NEG')
    def _():
        p = d5(); p['simulation_goals'][0]['derived_solid_id'] = 'ghost'; return p

    # curved: hyphen in multi-solid ids
    def cyl2(sid):
        p = deepcopy(F.SIM['demo6a-curved-cylinder-sections']['payload'])
        q = say(p, "Cho hình trụ có tâm đáy dưới P, tâm đáy trên Q, điểm B trên đường tròn đáy dưới, bán kính đáy R = 1 và chiều cao h = 2.")
        p['solids'].append({'solid_id': sid, 'solid_type': 'cylinder', 'notation': 'P.Q', 'center': 'P', 'apex_or_top': 'Q',
                            'rim_point': 'B', 'radius': '1', 'height': '2', 'quote': q})
        return p
    add('C.two_cyl_underscore_control', 'POS')(lambda: cyl2('cyl_b'))
    add('C.two_cyl_hyphen', 'POS', lambda: cyl2('cyl_b'))(lambda: cyl2('cyl-b'))
    def cone_h(sid):
        p = deepcopy(F.SIM['demo6b-curved-cone-frustum-cut']['payload'])
        import json
        return json.loads(json.dumps(p).replace('"cone_main"', json.dumps(sid)))
    add('C.cone_single_hyphen_id', 'POS', lambda: deepcopy(F.SIM['demo6b-curved-cone-frustum-cut']['payload']))(lambda: cone_h('cone-main'))
    add('C.cone_single_multi_hyphen_id', 'POS', lambda: deepcopy(F.SIM['demo6b-curved-cone-frustum-cut']['payload']))(lambda: cone_h('S-O-cone'))

    # curved relations: silently ignored?
    def cone2():
        p = deepcopy(F.SIM['demo6b-curved-cone-frustum-cut']['payload'])
        q = say(p, 'Cho hình nón đỉnh T, tâm đáy P, điểm B thuộc đường tròn đáy, bán kính đáy R = 1, chiều cao h = 2.')
        p['solids'].append({'solid_id': 'cone_b', 'solid_type': 'cone', 'notation': 'T.P', 'center': 'P', 'apex_or_top': 'T',
                            'rim_point': 'B', 'radius': '1', 'height': '2', 'quote': q})
        return p
    @add('C.cone_shared_vertices_apexes_claimed_equal', 'NEG')
    def _():
        p = cone2(); p['relations'] = [{'relation_id': 'rs', 'kind': 'shared_vertices', 'pairs': [['cone_main::S', 'cone_b::T']],
                                        'quote': 'Tính thể tích'}]; return p
    @add('C.cone_containment_whole_main_member_T', 'NEG')
    def _():
        p = cone2(); p['relations'] = [{'relation_id': 'rc', 'kind': 'containment', 'container_ref': 'cone_main', 'member_ref': 'T',
                                        'quote': 'Tính thể tích'}]; return p
    @add('C.cone_relation_quote_not_in_text', 'NEG')
    def _():
        p = cone2(); p['relations'] = [{'relation_id': 'rp', 'kind': 'perpendicular', 'solid_id': 'cone_main',
                                        'entity_a': ['S', 'O'], 'entity_b': ['O', 'A'], 'quote': 'không có trong đề'}]; return p
    return P
