"""Reviewer-3 probes, part 2: ratio/residual kind fields on valid ratio fixtures, S8 on the Adapter /3 legacy fallback
(non-identity bindings), curved route (two cones / two cylinders), dev07 baseline, derived highlight."""
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

    d1 = lambda: deepcopy(F.A3DEV['A3-DEV-01']['payload'])
    demo1 = lambda: deepcopy(F.SIM['demo1-pyramid-derived-section']['payload'])
    add('B.dev01_base', 'POS')(d1)
    add('B.demo1_base', 'POS')(demo1)
    add('B.dev07_base', 'POS')(lambda: deepcopy(F.A3DEV['A3-DEV-07']['payload']))
    add('B.dev02_base', 'POS')(lambda: deepcopy(F.A3DEV['A3-DEV-02']['payload']))

    def ratio(p):
        return next(g for g in p['math_goals'] if g['kind'] == 'volume_ratio')
    def resid(p):
        return next(g for g in p['math_goals'] if g['kind'] == 'residual_volume')
    for nm, fx in (('dev01', d1), ('demo1', demo1)):
        add(f'K.{nm}_ratio_target_solid_id_ghost', 'NEG')(lambda fx=fx: (lambda p: (ratio(p).update(target={'solid_id': 'ghost'}), p)[1])(fx()))
        add(f'K.{nm}_ratio_target_solid_other_notation', 'NEG')(lambda fx=fx: (lambda p: (ratio(p).update(target={'solid': 'Q.XYZ'}), p)[1])(fx()))
        add(f'K.{nm}_ratio_goal_type_volume', 'NEG')(lambda fx=fx: (lambda p: (ratio(p).update(goal_type='volume'), p)[1])(fx()))
        add(f'K.{nm}_ratio_with_parent_cut', 'NEG')(lambda fx=fx: (lambda p: (ratio(p).update(parent_solid_id=ratio(p)['numerator_solid_id'], cut_solid_id=ratio(p)['denominator_solid_id']), p)[1])(fx()))
        add(f'K.{nm}_ratio_target_segment_foreign', 'NEG')(lambda fx=fx: (lambda p: (ratio(p).update(target={'segment': ['Z', 'Q']}), p)[1])(fx()))
    @add('K.dev01_residual_with_denominator', 'NEG')
    def _():
        p = d1(); resid(p)['denominator_solid_id'] = 'top_pyramid'; return p
    @add('K.dev01_residual_target_solid_ghost', 'NEG')
    def _():
        p = d1(); resid(p)['target'] = {'solid': 'ghost'}; return p
    @add('K.dev01_measure_area_with_cut_solid', 'NEG')
    def _():
        p = d1(); next(g for g in p['math_goals'] if g['kind'] == 'measurement')['cut_solid_id'] = 'top_pyramid'; return p
    @add('K.dev01_derived_goal_with_target_refs_ghost_solid_like', 'NEG')
    def _():
        p = d1(); p['simulation_goals'][2]['target_refs'] = ['ghost_solid']; return p
    @add('K.dev01_section_goal_with_derived_solid_id', 'NEG')
    def _():
        p = d1(); p['simulation_goals'][1]['derived_solid_id'] = 'top_pyramid'; return p
    @add('K.dev01_section_goal_with_apex_ref_unknown', 'NEG')
    def _():
        p = d1(); p['simulation_goals'][1]['apex_ref'] = 'Z'; return p

    # ── S8 on the Adapter /3 legacy fallback (A3-DEV-02: non-identity binding D -> D1) ─────────────────
    def d2m():
        p = deepcopy(F.A3DEV['A3-DEV-02']['payload'])
        q = say(p, 'Gọi M là trung điểm của SB.')
        p['premises'].append({'kind': 'point_is_midpoint', 'solid_id': 'pyr1', 'args': {'point': 'M', 'segment': ['S', 'B']}, 'quote': q})
        return p
    add('S8.dev02_with_M_control', 'POS', lambda: deepcopy(F.A3DEV['A3-DEV-02']['payload']))(d2m)
    @add('S8.dev02_measure_target_solid_id_pyr2_M', 'NEG')
    def _():
        p = d2m(); q = say(p, 'Tính độ dài MB.')
        p['math_goals'].append({'goal_id': 'mm', 'kind': 'measurement', 'goal_type': 'distance', 'quote': q,
                                'target': {'solid_id': 'pyr2', 'segment': ['M', 'B']}}); return p
    @add('S8.dev02_measure_target_solid_pyr2_M', 'NEG')
    def _():
        p = d2m(); q = say(p, 'Tính độ dài MB.')
        p['math_goals'].append({'goal_id': 'mm', 'kind': 'measurement', 'goal_type': 'distance', 'quote': q,
                                'target': {'solid': 'D.ABC', 'segment': ['M', 'B']}}); return p
    @add('S8.dev02_measure_target_solid_pyr1_M_control', 'POS', d2m)
    def _():
        p = d2m(); q = say(p, 'Tính độ dài MB.')
        p['math_goals'].append({'goal_id': 'mm', 'kind': 'measurement', 'goal_type': 'distance', 'quote': q,
                                'target': {'solid_id': 'pyr1', 'segment': ['M', 'B']}}); return p
    @add('S8.dev02_containment_whole_pyr2_member_M', 'NEG')
    def _():
        p = d2m(); q = say(p, 'M thuộc khối D.ABC.')
        p['relations'].append({'relation_id': 'rc', 'kind': 'containment', 'container_ref': 'pyr2', 'member_ref': 'M', 'quote': q}); return p
    @add('S8.dev02_containment_solid_pyr2_member_M', 'NEG')
    def _():
        p = d2m(); q = say(p, 'M thuộc cạnh AB.')
        p['relations'].append({'relation_id': 'rc', 'kind': 'containment', 'solid_id': 'pyr2', 'container_ref': 'AB', 'member_ref': 'M', 'quote': q}); return p
    @add('S8.dev02_perpendicular_solid_pyr2_entity_M', 'NEG')
    def _():
        p = d2m(); q = say(p, 'MA vuông góc với AB.')
        p['relations'].append({'relation_id': 'rp', 'kind': 'perpendicular', 'solid_id': 'pyr2', 'entity_a': ['M', 'A'], 'entity_b': ['A', 'B'], 'quote': q}); return p
    @add('S8.dev02_highlight_target_pyr2_ref_M', 'NEG')
    def _():
        p = d2m()
        p['simulation_goals'].append({'goal_id': 'hm', 'kind': 'highlight_geometry', 'target_solid_id': 'pyr2', 'target_refs': ['M'],
                                      'quote': 'Dựng hai khối chóp'}); return p
    @add('S8.dev02_frame_pyr2_anchor_M', 'NEG')
    def _():
        p = d2m(); p['relations'][3]['anchor_refs'] = ['A', 'B', 'M']; return p

    # ── curved route ─────────────────────────────────────────────────────────────────────────────────
    def cone2():
        p = deepcopy(F.SIM['demo6b-curved-cone-frustum-cut']['payload'])
        q = say(p, 'Cho hình nón đỉnh T, tâm đáy P, điểm B thuộc đường tròn đáy, bán kính đáy R = 1, chiều cao h = 2.')
        p['solids'].append({'solid_id': 'cone_b', 'solid_type': 'cone', 'notation': 'T.P', 'center': 'P', 'apex_or_top': 'T',
                            'rim_point': 'B', 'radius': '1', 'height': '2', 'quote': q})
        return p
    cone1 = lambda: deepcopy(F.SIM['demo6b-curved-cone-frustum-cut']['payload'])
    add('C.cone_base', 'POS')(cone1)
    add('C.two_cones_control', 'POS', cone1)(cone2)
    def mg(p, i): return p['math_goals'][i]
    @add('C.cone_volume_goal_scope_other_cone', 'NEG')
    def _():
        p = cone2(); mg(p, 0)['solid_id'] = 'cone_b'; return p
    @add('C.cone_volume_target_solid_id_vs_solid', 'NEG')
    def _():
        p = cone2(); mg(p, 0)['target'] = {'solid': 'cone_main', 'solid_id': 'cone_b'}; return p
    @add('C.cone_volume_target_notation_alias', 'POS', cone1)
    def _():
        p = cone1(); mg(p, 0)['target'] = {'solid': 'S.O'}; return p
    @add('C.cone_volume_target_ghost', 'NEG')
    def _():
        p = cone1(); mg(p, 0)['target'] = {'solid': 'ghost'}; return p
    @add('C.cone_area_section_vs_solid_id', 'NEG')
    def _():
        p = cone2(); mg(p, 2)['target'] = {'section_id': 'sec_axial', 'solid_id': 'cone_b'}; return p
    @add('C.cone_area_unknown_section', 'NEG')
    def _():
        p = cone1(); mg(p, 2)['target'] = {'section_id': 'sec_ghost'}; return p
    @add('C.cone_derived_parent_other', 'NEG')
    def _():
        p = cone2(); p['simulation_goals'][2]['parent_solid_id'] = 'cone_b'; return p
    @add('C.cone_derived_apex_other', 'NEG')
    def _():
        p = cone2(); p['simulation_goals'][2]['apex_ref'] = 'T'; return p
    @add('C.cone_derived_apex_other_qualified', 'NEG')
    def _():
        p = cone2(); p['simulation_goals'][2]['apex_ref'] = 'cone_b::T'; return p
    @add('C.cone_derived_apex_unknown', 'NEG')
    def _():
        p = cone1(); p['simulation_goals'][2]['apex_ref'] = 'Z'; return p
    @add('C.cone_residual_parent_other', 'NEG')
    def _():
        p = cone2(); mg(p, 4)['parent_solid_id'] = 'cone_b'; return p
    @add('C.cone_ratio_goal_level_solid_id', 'NEG')
    def _():
        p = cone1(); mg(p, 3)['solid_id'] = 'cone_main'; return p
    @add('C.cone_highlight_target_main_ref_T', 'NEG')
    def _():
        p = cone2(); p['simulation_goals'].append({'goal_id': 'h', 'kind': 'highlight_geometry', 'target_solid_id': 'cone_main',
                                                    'target_refs': ['T'], 'quote': 'Tính thể tích'}); return p
    @add('C.cone_highlight_ref_q_nonvertex', 'NEG')
    def _():
        p = cone1(); p['simulation_goals'].append({'goal_id': 'h', 'kind': 'highlight_geometry',
                                                    'target_refs': ['cone_main::Z'], 'quote': 'Tính thể tích'}); return p
    @add('C.cone_highlight_ref_q_other_vertex', 'NEG')
    def _():
        p = cone2(); p['simulation_goals'].append({'goal_id': 'h', 'kind': 'highlight_geometry', 'target_solid_id': 'cone_main',
                                                    'target_refs': ['cone_b::T'], 'quote': 'Tính thể tích'}); return p
    @add('C.cone_highlight_control', 'POS', cone1)
    def _():
        p = cone1(); p['simulation_goals'].append({'goal_id': 'h', 'kind': 'highlight_geometry', 'target_solid_id': 'cone_main',
                                                    'target_refs': ['S', 'O', 'cone_upper', 'sec_cut'], 'quote': 'Tính thể tích'}); return p
    @add('C.cone_relation_frame_anchor_other', 'NEG')
    def _():
        p = cone2(); p['relations'] = [{'relation_id': 'rf', 'kind': 'coordinate_frame', 'solid_id': 'cone_main', 'frame_id': 'root',
                                        'anchor_refs': ['T'], 'quote': 'Tính thể tích'}]; return p
    @add('C.cone_relation_parallel_sides', 'NEG')
    def _():
        p = cone2(); p['relations'] = [{'relation_id': 'rp', 'kind': 'parallel', 'solid_a': 'cone_b', 'solid_b': 'cone_b',
                                        'entity_a': ['cone_main::S', 'cone_main::O'], 'entity_b': ['T', 'P'], 'quote': 'Tính thể tích'}]; return p
    @add('C.cone_relation_shared_vertices_nonvertex', 'NEG')
    def _():
        p = cone2(); p['relations'] = [{'relation_id': 'rs', 'kind': 'shared_vertices',
                                        'pairs': [['cone_main::Z', 'cone_b::T']], 'quote': 'Tính thể tích'}]; return p
    @add('C.cone_relation_containment_member_unknown_q', 'NEG')
    def _():
        p = cone1(); p['relations'] = [{'relation_id': 'rc', 'kind': 'containment', 'container_ref': 'cone_main',
                                        'member_ref': 'cone_main::Z', 'quote': 'Tính thể tích'}]; return p
    @add('C.cone_section_goal_target_solid_other', 'NEG')
    def _():
        p = cone2(); p['simulation_goals'][1]['target_solid_id'] = 'cone_b'; return p
    @add('C.cone_section_goal_parent_solid_id', 'NEG')
    def _():
        p = cone1(); p['simulation_goals'][1]['parent_solid_id'] = 'cone_main'; return p
    @add('C.cone_measure_with_parent_other', 'NEG')
    def _():
        p = cone2(); mg(p, 0)['parent_solid_id'] = 'cone_b'; return p
    @add('C.cone_premise_height_other', 'NEG')
    def _():
        p = cone2(); p['premises'] = [{'kind': 'height', 'solid_id': 'cone_main', 'args': {'value': '4', 'solid': 'cone_b'},
                                       'quote': 'chiều cao h = 4'}]; return p
    @add('C.cone_premise_segment_q_other', 'NEG')
    def _():
        p = cone2(); p['premises'] = [{'kind': 'segment_length', 'solid_id': 'cone_main', 'args': {'value': '2', 'segment': ['cone_b::T', 'cone_b::P']},
                                       'quote': 'chiều cao h = 2'}]; return p
    @add('C.cone_measure_str_segment_target_solid', 'NEG')
    def _():
        p = cone2(); p['math_goals'].append({'goal_id': 'ms', 'kind': 'measurement', 'goal_type': 'distance', 'quote': 'Tính thể tích',
                                             'target': {'solid_id': 'cone_main', 'segment': 'TP'}}); return p

    def cyl2():
        p = deepcopy(F.SIM['demo6a-curved-cylinder-sections']['payload'])
        q = say(p, "Cho hình trụ có tâm đáy dưới P, tâm đáy trên Q, điểm B trên đường tròn đáy dưới, bán kính đáy R = 1 và chiều cao h = 2.")
        p['solids'].append({'solid_id': 'cyl-b', 'solid_type': 'cylinder', 'notation': 'P.Q', 'center': 'P', 'apex_or_top': 'Q',
                            'rim_point': 'B', 'radius': '1', 'height': '2', 'quote': q})
        return p
    cyl1 = lambda: deepcopy(F.SIM['demo6a-curved-cylinder-sections']['payload'])
    add('C.cyl_base', 'POS')(cyl1)
    add('C.two_cyl_hyphen_control', 'POS', cyl1)(cyl2)
    @add('C.cyl_volume_goal_hyphen_other', 'NEG')
    def _():
        p = cyl2(); p['math_goals'][0]['solid_id'] = 'cyl-b'; return p
    @add('C.cyl_area_section_vs_goal_solid', 'NEG')
    def _():
        p = cyl2(); p['math_goals'][2]['solid_id'] = 'cyl-b'; return p
    @add('C.cyl_section_target_hyphen_goal_mismatch', 'NEG')
    def _():
        p = cyl2(); p['derived_sections'][0]['target_solid_id'] = 'cyl-b'; p['simulation_goals'][1]['target_solid_id'] = 'cyl'; return p
    @add('C.cyl_highlight_q_hyphen_other', 'NEG')
    def _():
        p = cyl2(); p['simulation_goals'].append({'goal_id': 'h', 'kind': 'highlight_geometry', 'target_solid_id': 'cyl',
                                                   'target_refs': ['cyl-b::P'], 'quote': 'Tính thể tích'}); return p
    @add('C.cyl_volume_target_notation_with_prime', 'POS', cyl1)
    def _():
        p = cyl1(); p['math_goals'][0]['target'] = {'solid': "O.O'"}; return p
    return P
