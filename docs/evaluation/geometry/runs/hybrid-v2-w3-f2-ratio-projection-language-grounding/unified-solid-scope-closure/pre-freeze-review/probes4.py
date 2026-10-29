"""Reviewer-3: independent re-reproduction of registered findings F1-F7 (built here, not the committed tests)."""
from copy import deepcopy
import json, re


def say(p, s):
    p['problem_text'] = p['problem_text'].rstrip() + ' ' + s
    return s


def probes(F):
    P = []
    def add(name, expect, base=None):
        def deco(fn):
            P.append((name, expect, fn, base)); return fn
        return deco
    sup = lambda: deepcopy(F.SUP)
    QV = 'Tính thể tích hình chóp S.ABCD.'

    # F1: hyphenated ids (valid control must serve; equal answers)
    def hy(a, b):
        p = json.loads(json.dumps(sup()).replace('"s1"', json.dumps(a)).replace('"s2"', json.dumps(b)))
        p['premises'][2]['args']['segment'] = [f'{a}::S', f'{a}::A']
        p['premises'][4]['args']['segment'] = [f'{b}::T', f'{b}::A']
        return p
    add('F1.pyr-1_pyr-2_qualified', 'POS', sup)(lambda: hy('pyr-1', 'pyr-2'))
    add('F1.pyr-1_scope_violation', 'NEG')(lambda: (lambda p: (p['math_goals'][0].__setitem__('solid_id', 'pyr-2'), p)[1])(hy('pyr-1', 'pyr-2')))
    # F2: relation kinds other than shared_faces / frame
    def rel(p, **kw):
        p['relations'] = [*p.get('relations', []), {'relation_id': 'rr', 'quote': 'SA vuông góc với (ABCD).', **kw}]; return p
    add('F2.perp_solid_id_s2_ops_s1_q', 'NEG')(lambda: rel(sup(), kind='perpendicular', solid_id='s2', entity_a=['s1::S', 's1::A'], entity_b=['s1::A', 's1::B', 's1::C']))
    add('F2.perp_solid_a_s2_ops_s1', 'NEG')(lambda: rel(sup(), kind='perpendicular', solid_a='s2', solid_b='s2', entity_a=['S', 'A'], entity_b=['A', 'B', 'C']))
    add('F2.shared_vertices_sides_s2_pair_s1', 'NEG')(lambda: rel(sup(), kind='shared_vertices', solid_a='s2', solid_b='s2', pairs=[['s1::A', 's2::A']]))
    add('F2.perp_valid_control', 'POS', sup)(lambda: rel(sup(), kind='perpendicular', solid_id='s1', entity_a=['S', 'A'], entity_b=['A', 'B', 'C', 'D']))
    # F3: simulation-goal targets / refs
    add('F3.highlight_s2_refs_s1', 'NEG')(lambda: (lambda p: (p['simulation_goals'].append({'goal_id': 'h', 'kind': 'highlight_geometry', 'quote': QV, 'target_solid_id': 's2', 'target_refs': ['S', 's1::A']}), p)[1])(sup()))
    add('F3.construct_object_parent_neq_target', 'NEG')(lambda: (lambda p: (p['simulation_goals'][0].__setitem__('parent_solid_id', 's2'), p)[1])(sup()))
    def d1(): return deepcopy(F.A3DEV['A3-DEV-01']['payload'])
    def d1two():
        p = d1(); q = say(p, 'Cho hình chóp T.ABCD.')
        p['solids'].append({'solid_id': 'other', 'solid_type': 'pyramid', 'notation': 'T.ABCD', 'quote': q}); return p
    add('F3.section_goal_target_other_solid', 'NEG')(lambda: (lambda p: (p['simulation_goals'][1].__setitem__('target_solid_id', 'other'), p)[1])(d1two()))
    add('F3.derived_goal_target_solid_id', 'NEG')(lambda: (lambda p: (p['simulation_goals'][2].__setitem__('target_solid_id', 'other'), p)[1])(d1two()))
    # F4: curved two cones
    def cone2():
        p = deepcopy(F.SIM['demo6b-curved-cone-frustum-cut']['payload'])
        q = say(p, 'Cho hình nón đỉnh T, tâm đáy P, điểm B thuộc đường tròn đáy, bán kính đáy R = 1, chiều cao h = 2.')
        p['solids'].append({'solid_id': 'cone_b', 'solid_type': 'cone', 'notation': 'T.P', 'center': 'P', 'apex_or_top': 'T',
                            'rim_point': 'B', 'radius': '1', 'height': '2', 'quote': q}); return p
    add('F4.cone_apex_other', 'NEG')(lambda: (lambda p: (p['simulation_goals'][2].__setitem__('apex_ref', 'T'), p)[1])(cone2()))
    add('F4.cone_perp_contradicting', 'NEG')(lambda: (lambda p: (p.__setitem__('relations', [{'relation_id': 'rp', 'kind': 'perpendicular', 'solid_id': 'cone_main', 'entity_a': ['T', 'P'], 'entity_b': ['S', 'O'], 'quote': 'Tính thể tích'}]), p)[1])(cone2()))
    add('F4.cone_highlight_other_refs', 'NEG')(lambda: (lambda p: (p['simulation_goals'].append({'goal_id': 'h', 'kind': 'highlight_geometry', 'target_solid_id': 'cone_b', 'target_refs': ['S', 'O'], 'quote': 'Tính thể tích'}), p)[1])(cone2()))
    # F5: internal errors -> typed
    cone1 = lambda: deepcopy(F.SIM['demo6b-curved-cone-frustum-cut']['payload'])
    add('F5.curved_target_notation_alias', 'POS', cone1)(lambda: (lambda p: (p['math_goals'][0].__setitem__('target', {'solid': 'S.O'}), p)[1])(cone1()))
    add('F5.curved_section_id_int', 'NEG')(lambda: (lambda p: (p['math_goals'][2].__setitem__('target', {'section_id': 5}), p)[1])(cone1()))
    add('F5.curved_section_id_unknown', 'NEG')(lambda: (lambda p: (p['math_goals'][2].__setitem__('target', {'section_id': 'nope'}), p)[1])(cone1()))
    add('F5.poly_target_point_dict', 'NEG')(lambda: (lambda p: (p['math_goals'].append({'goal_id': 'x', 'kind': 'measurement', 'goal_type': 'distance', 'quote': QV, 'target': {'point': {'a': 'S'}, 'plane': ['A', 'B', 'C']}}), p)[1])(sup()))
    # F6: A4 area target.solid notation alias
    d10 = lambda: deepcopy(F.A3DEV['A3-DEV-10']['payload'])
    add('F6.dev10_base', 'POS')(d10)
    add('F6.area_target_solid_notation', 'POS', d10)(lambda: (lambda p: (p['math_goals'][0]['target'].__setitem__('solid', "ABC.A'B'C'"), p)[1])(d10()))
    add('F6.area_target_solid_id', 'POS', d10)(lambda: (lambda p: (p['math_goals'][0]['target'].__setitem__('solid_id', 'prism_abc'), p)[1])(d10()))
    add('F6.volume_goal_notation', 'POS', sup)(lambda: (lambda p: (p['math_goals'][0]['target'].__setitem__('solid', 'S.ABCD'), p)[1])(sup()))
    # F7: residual ancestry (demo1: s_top cut from s_abcd)
    def demo1two():
        p = deepcopy(F.SIM['demo1-pyramid-derived-section']['payload']); q = say(p, 'Cho hình chóp T.ABCD.')
        p['solids'].append({'solid_id': 't_abcd', 'solid_type': 'pyramid', 'notation': 'T.ABCD', 'quote': q}); return p
    add('F7.residual_parent_other', 'NEG')(lambda: (lambda p: (p['math_goals'].append({'goal_id': 'r', 'kind': 'residual_volume', 'parent_solid_id': 't_abcd', 'cut_solid_id': 's_top', 'quote': p['math_goals'][1]['quote']}), p)[1])(demo1two()))
    add('F7.residual_valid_control', 'POS', demo1two)(lambda: (lambda p: (p['math_goals'].append({'goal_id': 'r', 'kind': 'residual_volume', 'parent_solid_id': 's_abcd', 'cut_solid_id': 's_top', 'quote': p['math_goals'][1]['quote']}), p)[1])(demo1two()))
    add('F7.ratio_cross_parent_valid', 'POS', demo1two)(lambda: (lambda p: (p['math_goals'].append({'goal_id': 'r', 'kind': 'volume_ratio', 'numerator_solid_id': 's_top', 'denominator_solid_id': 't_abcd', 'quote': p['math_goals'][1]['quote']}), p)[1])(demo1two()))
    return P
