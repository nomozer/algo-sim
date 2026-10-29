"""Reviewer-3 adversarial probes (new, built from committed fixtures). NEG = must be REFUSED (typed, non-internal) on
every route; POS = must not be newly scope-refused (vs `base`)."""
from copy import deepcopy
import re


def say(p, s):
    p['problem_text'] = p['problem_text'].rstrip() + ' ' + s
    return s


def rename(value, mapping):
    def one(s):
        if s in mapping: return mapping[s]
        for old, new in mapping.items():
            s = re.sub(rf'(^|-){re.escape(old)}::', rf'\g<1>{new}::', s)
        return s
    if isinstance(value, dict): return {one(k): rename(v, mapping) for k, v in value.items()}
    if isinstance(value, list): return [rename(v, mapping) for v in value]
    return one(value) if isinstance(value, str) else value


def probes(F):
    P = []
    def add(name, expect, base=None):
        def deco(fn):
            P.append((name, expect, fn, base)); return fn
        return deco
    sup = lambda: deepcopy(F.SUP)
    QV = 'Tính thể tích hình chóp S.ABCD.'

    def mg(p, **kw):
        g = {'goal_id': f'x{len(p["math_goals"])}', 'kind': 'measurement', 'quote': QV, **kw}
        p['math_goals'].append(g); return p

    # ── baseline controls ──────────────────────────────────────────────────────────────
    add('SUP.base', 'POS')(sup)
    @add('SUP.dist_s1_list_control', 'POS')
    def _(): return mg(sup(), goal_type='distance', solid_id='s1', target={'segment': ['S', 'C']})

    # ── measurement operand forms (string chains escape label ownership?) ─────────────
    @add('M.str_segment_target_solid_id', 'NEG')
    def _(): return mg(sup(), goal_type='distance', target={'solid_id': 's1', 'segment': 'TA'})
    @add('M.str_segment_target_solid', 'NEG')
    def _(): return mg(sup(), goal_type='distance', target={'solid': 's1', 'segment': 'TA'})
    @add('M.str_segment_target_notation', 'NEG')
    def _(): return mg(sup(), goal_type='distance', target={'solid': 'S.ABCD', 'segment': 'TA'})
    @add('M.str_segment_goal_solid_id', 'NEG')
    def _(): return mg(sup(), goal_type='distance', solid_id='s1', target={'segment': 'TA'})
    @add('M.str_plane_point_target_solid_id', 'NEG')
    def _(): return mg(sup(), goal_type='distance', target={'solid_id': 's1', 'point': 'S', 'plane': 'TBC'})
    @add('M.str_line_angle_target_solid_id', 'NEG')
    def _(): return mg(sup(), goal_type='angle', target={'solid_id': 's1', 'line': 'TC', 'plane': ['A', 'B', 'C']})
    @add('M.str_polygon_area_target_solid_id', 'NEG')
    def _(): return mg(sup(), goal_type='area', target={'solid_id': 's1', 'polygon': 'TBC'})
    @add('M.list_segment_target_solid_id_foreign', 'NEG')
    def _(): return mg(sup(), goal_type='distance', target={'solid_id': 's1', 'segment': ['T', 'A']})
    @add('M.plane1_plane2_scope_s1_foreign', 'NEG')
    def _(): return mg(sup(), goal_type='angle', solid_id='s1', target={'plane1': ['T', 'A', 'B'], 'plane2': ['A', 'B', 'C']})
    @add('M.plane1_plane2_scope_s1_control', 'POS')
    def _(): return mg(sup(), goal_type='angle', solid_id='s1', target={'plane1': ['S', 'A', 'B'], 'plane2': ['A', 'B', 'C']})
    @add('M.qualified_nonvertex_same_ns', 'NEG')
    def _(): return mg(sup(), goal_type='distance', solid_id='s1', target={'segment': ['s1::T', 's1::A']})
    @add('M.segment_None_entry', 'NEG')
    def _(): return mg(sup(), goal_type='distance', solid_id='s1', target={'segment': None, 'solid': 's1'})
    @add('M.target_solid_list', 'NEG')
    def _(): return mg(sup(), goal_type='volume', target={'solid': ['s1']})
    @add('M.target_solid_bool', 'NEG')
    def _(): return mg(sup(), goal_type='volume', target={'solid': True})
    @add('M.target_solid_id_int', 'NEG')
    def _(): return mg(sup(), goal_type='volume', target={'solid': 's1', 'solid_id': 7})
    @add('M.target_section_id_dict', 'NEG')
    def _(): return mg(sup(), goal_type='area', target={'section_id': {'a': 1}})
    @add('M.target_solid_trailing_space', 'NEG')
    def _(): return mg(sup(), goal_type='volume', target={'solid': 's2 '})
    @add('M.target_unknown_scope_key_ghost', 'NEG')
    def _(): return mg(sup(), goal_type='volume', target={'solid': 's1', 'solid_b': 'ghost'})
    @add('M.target_solids_list_key_ghost', 'NEG')
    def _(): return mg(sup(), goal_type='volume', target={'solid': 's1', 'solids': ['ghost']})

    # ── fields without meaning for the math-goal kind (Owner D-D: no silent ignore) ─────
    @add('K.measure_with_parent_solid_id_other', 'NEG')
    def _(): return mg(sup(), goal_type='volume', solid_id='s1', target={'solid': 's1'}, parent_solid_id='s2')
    @add('K.measure_with_numerator_other', 'NEG')
    def _(): return mg(sup(), goal_type='volume', solid_id='s1', target={'solid': 's1'}, numerator_solid_id='s2')
    @add('K.ratio_with_target_solid_id_ghost', 'NEG')
    def _():
        p = sup(); p['math_goals'].append({'goal_id': 'r', 'kind': 'volume_ratio', 'numerator_solid_id': 's1',
                                           'denominator_solid_id': 's2', 'quote': QV, 'target': {'solid_id': 'ghost'}})
        return p
    @add('K.ratio_with_target_solid_other', 'NEG')
    def _():
        p = sup(); p['math_goals'].append({'goal_id': 'r', 'kind': 'volume_ratio', 'numerator_solid_id': 's1',
                                           'denominator_solid_id': 's2', 'quote': QV, 'target': {'solid': 'T.ABCD', 'segment': ['T', 'A']}})
        return p
    @add('K.ratio_with_parent_cut_ghostless', 'NEG')
    def _():
        p = sup(); p['math_goals'].append({'goal_id': 'r', 'kind': 'volume_ratio', 'numerator_solid_id': 's1',
                                           'denominator_solid_id': 's2', 'quote': QV, 'parent_solid_id': 's2', 'cut_solid_id': 's1'})
        return p
    @add('K.residual_with_numerator', 'NEG')
    def _():
        p = deepcopy(F.A3DEV['A3-DEV-01']['payload'])
        g = next(x for x in p['math_goals'] if x['kind'] == 'residual_volume'); g['numerator_solid_id'] = 'main_pyramid'
        return p
    @add('K.ratio_goal_type_with_target', 'NEG')
    def _():
        p = sup(); p['math_goals'].append({'goal_id': 'r', 'kind': 'volume_ratio', 'numerator_solid_id': 's1',
                                           'denominator_solid_id': 's2', 'quote': QV, 'goal_type': 'volume', 'target': {'solid': 'ghost'}})
        return p
    @add('K.construct_object_with_derived_solid_id', 'NEG')
    def _():
        p = sup(); p['simulation_goals'][0]['derived_solid_id'] = 'ghost'; return p
    @add('K.construct_object_with_apex_ref_foreign', 'NEG')
    def _():
        p = sup(); p['simulation_goals'][0]['apex_ref'] = 'T'; return p
    @add('K.construct_object_target_refs_foreign_solid', 'NEG')
    def _():
        p = sup(); p['simulation_goals'][0]['target_refs'] = ['s2']; return p
    @add('K.construct_object_target_refs_foreign_label', 'NEG')
    def _():
        p = sup(); p['simulation_goals'][0]['target_refs'] = ['T']; return p
    @add('K.sequence_target_solid_s2_refs_S', 'NEG')
    def _():
        p = sup(); p['simulation_goals'].append({'goal_id': 'q', 'kind': 'construction_sequence', 'quote': QV,
                                                 'target_solid_id': 's2', 'target_refs': ['S']}); return p
    @add('K.highlight_target_s1_refs_s2_qualified', 'NEG')
    def _():
        p = sup(); p['simulation_goals'].append({'goal_id': 'h', 'kind': 'highlight_geometry', 'quote': QV,
                                                 'target_solid_id': 's1', 'target_refs': ['s2::T']}); return p
    @add('K.highlight_ref_unknown_label', 'NEG')
    def _():
        p = sup(); p['simulation_goals'].append({'goal_id': 'h', 'kind': 'highlight_geometry', 'quote': QV,
                                                 'target_refs': ['Z']}); return p
    @add('K.highlight_ref_notation_alias', 'POS')
    def _():
        p = sup(); p['simulation_goals'].append({'goal_id': 'h', 'kind': 'highlight_geometry', 'quote': QV,
                                                 'target_refs': ['S.ABCD']}); return p
    @add('K.highlight_ref_cross_solid_unscoped_control', 'POS')
    def _():
        p = sup(); p['simulation_goals'].append({'goal_id': 'h', 'kind': 'highlight_geometry', 'quote': QV,
                                                 'target_refs': ['s1::S', 's2::T', 's2']}); return p

    # ── relations, every kind ──────────────────────────────────────────────────────────
    def rel(p, **kw):
        p.setdefault('relations', []).append({'relation_id': f'r{len(p.get("relations", []))}', 'quote': QV, **kw}); return p
    @add('R.containment_solid_s1_member_s2_q', 'NEG')
    def _(): return rel(sup(), kind='containment', solid_id='s1', container_ref='s1::SA', member_ref='s2::T')
    @add('R.containment_whole_s2_vs_solid_s1', 'NEG')
    def _(): return rel(sup(), kind='containment', solid_id='s1', container_ref='s2', member_ref='A')
    @add('R.containment_whole_s2_member_S', 'NEG')
    def _(): return rel(sup(), kind='containment', container_ref='s2', member_ref='S')
    @add('R.containment_chain_foreign_unqualified', 'NEG')
    def _(): return rel(sup(), kind='containment', solid_id='s1', container_ref='TA', member_ref='A')
    @add('R.containment_chain_qualified_other', 'NEG')
    def _(): return rel(sup(), kind='containment', solid_id='s1', container_ref='s2::TA', member_ref='A')
    @add('R.containment_container_notation_alias', 'POS')
    def _(): return rel(sup(), kind='containment', container_ref='S.ABCD', member_ref='A')
    @add('R.containment_container_unknown_id_like', 'NEG')
    def _(): return rel(sup(), kind='containment', container_ref='ghost_solid', member_ref='A')
    @add('R.parallel_solid_a_s1_entity_T', 'NEG')
    def _(): return rel(sup(), kind='parallel', solid_a='s1', solid_b='s1', entity_a=['T', 'A'], entity_b=['S', 'B'])
    @add('R.parallel_solid_a_vs_solid_id', 'NEG')
    def _(): return rel(sup(), kind='parallel', solid_id='s1', solid_a='s2', entity_a=['A', 'B'], entity_b=['C', 'D'])
    @add('R.perpendicular_solid_id_s2_entity_S', 'NEG')
    def _(): return rel(sup(), kind='perpendicular', solid_id='s2', entity_a=['S', 'A'], entity_b=['A', 'B', 'C'])
    @add('R.perpendicular_solid_ghost', 'NEG')
    def _(): return rel(sup(), kind='perpendicular', solid_id='ghost', entity_a=['S', 'A'], entity_b=['A', 'B', 'C'])
    @add('R.perpendicular_section_id_ghost', 'NEG')
    def _(): return rel(sup(), kind='perpendicular', section_id='ghost', entity_a=['S', 'A'], entity_b=['A', 'B', 'C'])
    @add('R.perpendicular_valid_control', 'POS')
    def _(): return rel(sup(), kind='perpendicular', solid_id='s1', entity_a=['S', 'A'], entity_b=['A', 'B', 'C'])
    @add('R.coordinate_frame_anchor_foreign', 'NEG')
    def _(): return rel(sup(), kind='coordinate_frame', solid_id='s1', frame_id='root', anchor_refs=['T', 'A', 'B'])
    @add('R.coordinate_frame_anchor_q_other', 'NEG')
    def _(): return rel(sup(), kind='coordinate_frame', solid_id='s1', frame_id='root', anchor_refs=['s2::A', 'B', 'C'])
    @add('R.shared_faces_face_a_q_other', 'NEG')
    def _(): return rel(sup(), kind='shared_faces', solid_a='s1', solid_b='s2', face_a=['s2::A', 's2::B', 's2::C'], face_b=['A', 'B', 'C'])
    @add('R.shared_faces_face_b_not_of_b', 'NEG')
    def _(): return rel(sup(), kind='shared_faces', solid_a='s1', solid_b='s2', face_a=['S', 'A', 'B'], face_b=['S', 'A', 'B'])
    @add('R.shared_faces_valid_control', 'POS')
    def _(): return rel(sup(), kind='shared_faces', solid_a='s1', solid_b='s2', face_a=['A', 'B', 'C'], face_b=['A', 'B', 'C'])
    @add('R.shared_vertices_nonvertex_q', 'NEG')
    def _(): return rel(sup(), kind='shared_vertices', pairs=[['s1::T', 's2::T']])
    @add('R.shared_vertices_solid_a_vs_pair', 'NEG')
    def _(): return rel(sup(), kind='shared_vertices', solid_a='s2', solid_b='s1', pairs=[['s1::A', 's2::A']])
    @add('R.shared_vertices_valid_control', 'POS')
    def _(): return rel(sup(), kind='shared_vertices', pairs=[['s1::A', 's2::A'], ['s1::B', 's2::B']])

    # section_membership on A3-DEV-01 (single solid + derived)
    d1 = lambda: deepcopy(F.A3DEV['A3-DEV-01']['payload'])
    @add('R.section_membership_solid_ghost', 'NEG')
    def _():
        p = d1(); p['relations'][1]['solid_id'] = 'ghost'; return p
    @add('R.section_membership_member_unknown', 'NEG')
    def _():
        p = d1(); p['relations'][1]['member_refs'] = ['main_pyramid::Q']; return p
    @add('R.section_membership_solid_derived_child', 'POS', d1)
    def _():
        p = d1(); p['relations'][1]['solid_id'] = 'top_pyramid'; return p
    @add('R.containment_container_derived_child', 'POS', d1)
    def _():
        p = d1(); p['relations'][0]['solid_id'] = 'main_pyramid'; return p

    # ── hyphenated ids ────────────────────────────────────────────────────────────────
    def hy(mapping):
        p = rename(sup(), mapping)
        for i, x in ((2, 's1'), (4, 's2')):
            seg = p['premises'][i]['args']['segment']
            p['premises'][i]['args']['segment'] = [f'{mapping[x]}::{seg[0]}', f'{mapping[x]}::{seg[1]}']
        return p
    add('H.ids_like_edges_S-A_T-A', 'POS', sup)(lambda: hy({'s1': 'S-A', 's2': 'T-A'}))
    add('H.ids_many_hyphens', 'POS', sup)(lambda: hy({'s1': 'a-b-c-d', 's2': 'x--y'}))
    add('H.ids_equal_labels_S_T', 'POS', sup)(lambda: hy({'s1': 'S', 's2': 'T'}))
    add('H.ids_trailing_hyphen', 'POS', sup)(lambda: hy({'s1': 's1-', 's2': '-s2'}))
    @add('H.ids_like_edges_cross_scope', 'NEG')
    def _():
        p = hy({'s1': 'S-A', 's2': 'T-A'}); p['math_goals'][0]['solid_id'] = 'T-A'; return p
    @add('H.ids_like_edges_qualified_foreign_ref', 'NEG')
    def _():
        p = hy({'s1': 'S-A', 's2': 'T-A'}); p['premises'][2]['args']['segment'] = ['T-A::T', 'S-A::A']; return p
    @add('H.dotted_id_unqualified_control', 'POS', sup)
    def _(): return rename(sup(), {'s1': 's.1'})
    @add('H.colon_id_unqualified_control', 'POS', sup)
    def _(): return rename(sup(), {'s1': 's:1'})

    def dev07():
        return deepcopy(F.A3DEV['A3-DEV-07']['payload'])
    def dev07h(new):
        p = rename(dev07(), {'pyr_sabc': new})
        for sec in p['derived_sections']:
            if sec.get('named_intersections'):
                sec['named_intersections'] = {f'{new}::{k.split("-")[0]}-{new}::{k.split("-")[1]}': v
                                              for k, v in sec['named_intersections'].items()}
        return p
    add('H.dev07_qualified_keys_uppercase_hyphen_id', 'POS', dev07)(lambda: dev07h('Q-S-A'))
    add('H.dev07_qualified_keys_id_S-B', 'POS', dev07)(lambda: dev07h('S-B'))
    @add('H.dev07_key_with_foreign_ns', 'NEG')
    def _():
        p = dev07h('Q-S-A')
        sec = next(s for s in p['derived_sections'] if s.get('named_intersections'))
        k, v = next(iter(sec['named_intersections'].items()))
        a, b = k.split('::')[1].split('-')[0], k.split('::')[-1]
        sec['named_intersections'] = {f'ghost-x::{a}-Q-S-A::{b}': v, **{kk: vv for kk, vv in list(sec['named_intersections'].items())[1:]}}
        return p
    @add('H.dev07_key_ambiguous_three_parts', 'NEG')
    def _():
        p = dev07()
        sec = next(s for s in p['derived_sections'] if s.get('named_intersections'))
        k, v = next(iter(sec['named_intersections'].items()))
        sec['named_intersections'] = {f'{k}-C': v}
        return p

    # ── derived-solid ancestry on demo5 (two pyramids, section of pyr_s) ──────────────────
    def d5(parent=True):
        p = deepcopy(F.SIM['demo5-selection-and-highlighting']['payload'])
        q = 'mặt phẳng (α) qua M song song với (ABCD) cắt SB, SC, SD'
        g = {'goal_id': 'dg', 'kind': 'construct_derived_solid', 'derived_solid_id': 'top', 'target_section_id': 'sec_hl',
             'apex_ref': 'S', 'quote': q}
        if parent: g['parent_solid_id'] = 'pyr_s'
        p['simulation_goals'].append(g); return p
    add('D.d5_with_derived_control', 'POS', lambda: deepcopy(F.SIM['demo5-selection-and-highlighting']['payload']))(d5)
    @add('D.residual_parent_other_implicit_parent', 'NEG')
    def _():
        p = d5(False); p['math_goals'].append({'goal_id': 'res', 'kind': 'residual_volume', 'parent_solid_id': 'pyr_t',
                                               'cut_solid_id': 'top', 'quote': p['math_goals'][0]['quote']}); return p
    @add('D.residual_parent_other_explicit', 'NEG')
    def _():
        p = d5(); p['math_goals'].append({'goal_id': 'res', 'kind': 'residual_volume', 'parent_solid_id': 'pyr_t',
                                          'cut_solid_id': 'top', 'quote': p['math_goals'][0]['quote']}); return p
    @add('D.residual_parent_is_cut_itself', 'NEG')
    def _():
        p = d5(); p['math_goals'].append({'goal_id': 'res', 'kind': 'residual_volume', 'parent_solid_id': 'top',
                                          'cut_solid_id': 'top', 'quote': p['math_goals'][0]['quote']}); return p
    @add('D.residual_primary_cut_not_contained', 'NEG')
    def _():
        p = d5(); p['math_goals'].append({'goal_id': 'res', 'kind': 'residual_volume', 'parent_solid_id': 'pyr_s',
                                          'cut_solid_id': 'pyr_t', 'quote': p['math_goals'][0]['quote']}); return p
    @add('D.residual_parent_derived_cut_primary', 'NEG')
    def _():
        p = d5(); p['math_goals'].append({'goal_id': 'res', 'kind': 'residual_volume', 'parent_solid_id': 'top',
                                          'cut_solid_id': 'pyr_s', 'quote': p['math_goals'][0]['quote']}); return p
    @add('D.residual_valid_control', 'POS')
    def _():
        p = d5(); p['math_goals'].append({'goal_id': 'res', 'kind': 'residual_volume', 'parent_solid_id': 'pyr_s',
                                          'cut_solid_id': 'top', 'quote': p['math_goals'][0]['quote']}); return p
    @add('D.derived_parent_vs_section_solid', 'NEG')
    def _():
        p = d5(); p['simulation_goals'][-1]['parent_solid_id'] = 'pyr_t'; return p
    @add('D.derived_apex_other_solid_T', 'NEG')
    def _():
        p = d5(); p['simulation_goals'][-1]['apex_ref'] = 'T'; return p
    @add('D.derived_apex_other_solid_qualified', 'NEG')
    def _():
        p = d5(); p['simulation_goals'][-1]['apex_ref'] = 'pyr_t::T'; return p
    @add('D.derived_target_refs_foreign', 'NEG')
    def _():
        p = d5(); p['simulation_goals'][-1]['target_refs'] = ['T']; return p
    @add('D.highlight_target_pyr_t_ref_derived', 'NEG')
    def _():
        p = d5(); p['simulation_goals'][0]['target_solid_id'] = 'pyr_t'; p['simulation_goals'][0]['target_refs'] = ['top']; return p
    @add('D.highlight_target_derived_ref_M', 'POS', d5)
    def _():
        p = d5(); p['simulation_goals'][0]['target_solid_id'] = 'top'; p['simulation_goals'][0]['target_refs'] = ['M']; return p
    @add('D.measure_scope_derived_foreign_label', 'NEG')
    def _():
        p = d5(); p['math_goals'].append({'goal_id': 'dm', 'kind': 'measurement', 'goal_type': 'distance', 'solid_id': 'top',
                                          'target': {'segment': ['T', 'C']}, 'quote': p['math_goals'][0]['quote']}); return p
    @add('D.measure_area_section_scope_derived', 'POS', d5)
    def _():
        p = d5(); p['math_goals'].append({'goal_id': 'dm', 'kind': 'measurement', 'goal_type': 'area',
                                          'target': {'section_id': 'sec_hl', 'solid_id': 'top'}, 'quote': p['math_goals'][0]['quote']}); return p
    @add('D.ratio_derived_vs_other_primary_control', 'POS', d5)
    def _():
        p = d5(); p['math_goals'].append({'goal_id': 'rr', 'kind': 'volume_ratio', 'numerator_solid_id': 'top',
                                          'denominator_solid_id': 'pyr_t', 'quote': p['math_goals'][0]['quote']}); return p
    return P
