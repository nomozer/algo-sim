"""Build `schema-field-inventory.json`: the mechanical field list (backend/tests/geometry/scope_field_census.py) joined
with the semantic classification below. Fails if a mechanically discovered field has no classification, or if the
classification names a field the models no longer have. Usage (worktree root): python build_inventory.py"""
import json, sys
from pathlib import Path

HERE = Path(__file__).resolve().parents[1]; ROOT = HERE.parents[5]
sys.path[:0] = [str(ROOT / 'backend'), str(ROOT / 'backend/tests/geometry')]
import scope_field_census as C  # noqa: E402

ALL = 'adapter3(polyhedral, curved, legacy), adapter4, planner route, bridge'
TEST = 'backend/tests/geometry/test_scope_census_closure.py'
# category: SOLID_DEFINITION | SOLID_SCOPE | SOLID_OPERAND | VERTEX_REF | EDGE_KEY | SECTION_REF | DEFINITION_ID | METADATA
# Scope-bearing categories need: rules (ids of `_validate_declared_solid_scope` / Bridge ownership), tests, codes.
SCOPE = {'SOLID_SCOPE', 'SOLID_OPERAND', 'VERTEX_REF', 'EDGE_KEY', 'SECTION_REF'}
def s(category, owner, rules, pos, neg, codes): return dict(category=category, owner=owner, rules=rules, entry_points=ALL,
                                                             positive_test=pos, negative_test=neg, refusal_codes=codes)
def meta(note='no scope semantics'): return dict(category='METADATA', note=note)
def ident(note): return dict(category='DEFINITION_ID', note=note)

REF = lambda owner, pos, neg: s('VERTEX_REF', owner, ['S5', 'S7', 'S8'], pos, neg,
                                ['INVALID_QUALIFIED_REF', 'UNKNOWN_SOLID_ID', 'SOURCE_OBJECT_MISMATCH'])
CLASS = {
    'TypedFactNextPayload.schema_version': meta(), 'TypedFactNextPayload.problem_text': meta(),
    'TypedFactNextPayload.length_unit': meta(), 'TypedFactNextPayload.solids': meta('container'),
    'TypedFactNextPayload.premises': meta('container'), 'TypedFactNextPayload.derived_sections': meta('container'),
    'TypedFactNextPayload.relations': meta('container'), 'TypedFactNextPayload.simulation_goals': meta('container'),
    'TypedFactNextPayload.math_goals': meta('container'),
    'SolidSpec.solid_id': dict(category='SOLID_DEFINITION', note='defines a scope; DUPLICATE_SOLID_ID; hyphens legal (S5 tokenizer)',
                               rules=['S5'], positive_test='test_f1_hyphenated_ids_serve_on_every_route',
                               negative_test='test_f1_hyphenated_scope_violations_refuse'),
    'SolidSpec.solid_type': meta(), 'SolidSpec.notation': dict(category='SOLID_DEFINITION', note='alias source (S2)'),
    'SolidSpec.vertex_bindings': dict(category='SOLID_DEFINITION', note='canonical alias + vertex ownership source'),
    'SolidSpec.center': dict(category='SOLID_DEFINITION', note='curved vertex label definition (ownership source)'),
    'SolidSpec.apex_or_top': dict(category='SOLID_DEFINITION', note='curved vertex label definition'),
    'SolidSpec.rim_point': dict(category='SOLID_DEFINITION', note='curved vertex label definition'),
    'SolidSpec.radius': meta('value'), 'SolidSpec.height': meta('value'), 'SolidSpec.quote': meta(),
    'SolidSpec.coordinate_frame_id': meta('frame id, not a solid'),
    'PremiseSpec.kind': meta(), 'PremiseSpec.quote': meta(), 'PremiseSpec.args': meta('container; keys classified by shape below'),
    'PremiseSpec.solid_id': s('SOLID_SCOPE', 'premise', ['S1', 'S3', 'S5', 'S8'], 'test_premise_scope_controls_serve',
                              'test_premise_scope_violations_refuse', ['UNKNOWN_SOLID_ID', 'SOURCE_OBJECT_MISMATCH']),
    'MathGoalSpec.goal_id': ident('goal id'), 'MathGoalSpec.kind': meta(), 'MathGoalSpec.quote': meta(),
    'MathGoalSpec.goal_type': meta(), 'MathGoalSpec.target': meta('container; keys classified below'),
    'MathGoalSpec.numerator_solid_id': s('SOLID_OPERAND', 'ratio goal', ['S1'], 'test_ratio_residual_controls_serve',
                                         'test_ratio_residual_scope_refused', ['UNKNOWN_SOLID_ID']),
    'MathGoalSpec.denominator_solid_id': s('SOLID_OPERAND', 'ratio goal', ['S1'], 'test_ratio_residual_controls_serve',
                                           'test_ratio_residual_scope_refused', ['UNKNOWN_SOLID_ID']),
    'MathGoalSpec.parent_solid_id': s('SOLID_OPERAND', 'residual goal', ['S1'], 'test_ratio_residual_controls_serve',
                                      'test_ratio_residual_scope_refused', ['UNKNOWN_SOLID_ID']),
    'MathGoalSpec.cut_solid_id': s('SOLID_OPERAND', 'residual goal', ['S1'], 'test_ratio_residual_controls_serve',
                                   'test_ratio_residual_scope_refused', ['UNKNOWN_SOLID_ID']),
    'MathGoalSpec.solid_id': s('SOLID_SCOPE', 'measurement goal (ratio/residual: Owner decision A)', ['S1', 'S3', 'S4'],
                               'test_measurement_scope_controls_serve', 'test_measurement_scope_violations_refuse',
                               ['UNKNOWN_SOLID_ID', 'SOURCE_OBJECT_MISMATCH', 'INVALID_MATH_GOAL']),
    'MathGoalSpec.target.solid': s('SOLID_OPERAND', 'measurement goal', ['S2', 'S3'], 'test_measurement_scope_controls_serve',
                                   'test_measurement_scope_violations_refuse', ['UNKNOWN_SOLID_ID', 'UNKNOWN_SOLID', 'SOURCE_OBJECT_MISMATCH']),
    'MathGoalSpec.target.solid_id': s('SOLID_SCOPE', 'measurement goal', ['S1', 'S3'], 'test_measurement_scope_controls_serve',
                                      'test_measurement_scope_violations_refuse', ['UNKNOWN_SOLID_ID', 'SOURCE_OBJECT_MISMATCH']),
    'MathGoalSpec.target.section_id': s('SECTION_REF', 'measurement goal', ['S9', 'S11'], 'test_measurement_scope_controls_serve',
                                        'test_f5_malformed_targets_refuse_typed', ['UNKNOWN_SECTION_ID', 'INVALID_MATH_GOAL', 'SOURCE_OBJECT_MISMATCH']),
    **{f'MathGoalSpec.target.{k}': s('VERTEX_REF', 'measurement goal', ['S5', 'S7', 'S8', 'S11'], 'test_measurement_scope_controls_serve',
                                     'test_measurement_operand_violations_refuse', ['SOURCE_OBJECT_MISMATCH', 'UNKNOWN_SOLID_ID', 'INVALID_MATH_GOAL'])
       for k in ('segment', 'point', 'plane', 'line', 'line1', 'line2', 'polygon')},
    'GeometricRelationSpec.relation_id': ident('relation id'), 'GeometricRelationSpec.kind': meta(),
    'GeometricRelationSpec.quote': meta(), 'GeometricRelationSpec.frame_id': meta('frame id, not a solid'),
    **{f'GeometricRelationSpec.{k}': s('SOLID_SCOPE', 'relation (every kind)', ['S1', 'S3'], 'test_relation_controls_serve',
                                       'test_relation_scope_violations_refuse_every_kind', ['UNKNOWN_SOLID_ID', 'SOURCE_OBJECT_MISMATCH'])
       for k in ('solid_id', 'solid_a', 'solid_b')},
    'GeometricRelationSpec.section_id': s('SECTION_REF', 'section_membership relation', ['S9'], 'test_relation_controls_serve',
                                          'test_relation_scope_violations_refuse_every_kind', ['UNKNOWN_SECTION_ID', 'SOURCE_OBJECT_MISMATCH']),
    **{f'GeometricRelationSpec.{k}': REF('relation side a (solid_a or solid_id)', 'test_relation_controls_serve',
                                         'test_relation_scope_violations_refuse_every_kind') for k in ('face_a', 'entity_a')},
    **{f'GeometricRelationSpec.{k}': REF('relation side b (solid_b or solid_id)', 'test_relation_controls_serve',
                                         'test_relation_scope_violations_refuse_every_kind') for k in ('face_b', 'entity_b')},
    'GeometricRelationSpec.pairs': REF('pair[0] side a, pair[1] side b', 'test_relation_controls_serve',
                                       'test_relation_scope_violations_refuse_every_kind'),
    **{f'GeometricRelationSpec.{k}': REF('relation solid_id (section_membership: the section solid)', 'test_relation_controls_serve',
                                         'test_relation_scope_violations_refuse_every_kind')
       for k in ('container_ref', 'member_ref', 'member_refs', 'anchor_refs')},
    'SimulationGoalSpec.goal_id': ident('goal id'), 'SimulationGoalSpec.kind': meta(), 'SimulationGoalSpec.quote': meta(),
    'SimulationGoalSpec.style_role': meta(),
    'SimulationGoalSpec.derived_solid_id': dict(category='SOLID_DEFINITION', note='defines a derived solid; DUPLICATE_SOLID_ID'),
    'SimulationGoalSpec.target_solid_id': s('SOLID_SCOPE', 'simulation goal (every kind)', ['S1', 'S3', 'S9'],
                                            'test_simulation_goal_controls_serve', 'test_simulation_goal_scope_violations_refuse_every_kind',
                                            ['UNKNOWN_SOLID_ID', 'SOURCE_OBJECT_MISMATCH']),
    'SimulationGoalSpec.parent_solid_id': s('SOLID_SCOPE', 'construct_derived_solid only (Owner D-A)', ['S1', 'S3', 'S4'],
                                            'test_simulation_goal_controls_serve', 'test_parent_solid_id_outside_derived_solid_refused',
                                            ['UNKNOWN_SOLID_ID', 'SOURCE_OBJECT_MISMATCH', 'INVALID_SIMULATION_GOAL']),
    'SimulationGoalSpec.target_section_id': s('SECTION_REF', 'simulation goal', ['S9'], 'test_simulation_goal_controls_serve',
                                              'test_simulation_goal_scope_violations_refuse_every_kind', ['UNKNOWN_SECTION_ID', 'SOURCE_OBJECT_MISMATCH']),
    'SimulationGoalSpec.apex_ref': REF('derived solid parent', 'test_simulation_goal_controls_serve', 'test_f4_curved_ownership_refuses'),
    'SimulationGoalSpec.target_refs': dict(REF('simulation goal scope', 'test_simulation_goal_controls_serve',
                                               'test_simulation_goal_scope_violations_refuse_every_kind'),
                                           rules=['S5', 'S7', 'S8', 'S10'],
                                           refusal_codes=['UNKNOWN_VERTEX_REF', 'UNKNOWN_SOLID_ID', 'SOURCE_OBJECT_MISMATCH']),
    **{f'{m}.{k}': v for m in ('DerivedPlaneSectionSpec', 'DerivedPlaneSectionSpecV2') for k, v in {
        'section_id': ident('section id'), 'plane_name': meta(), 'quote': meta(), 'plane_kind': meta(),
        'distance_from_base': meta('value'), 'ratio_from_apex': meta('value'), 'equation_coeffs': meta('values'),
        'section_shape': meta(),
        'target_solid_id': s('SOLID_SCOPE', 'section', ['S1', 'S5', 'S8'], 'test_section_scope_controls_serve',
                             'test_section_scope_violations_refuse', ['UNKNOWN_SOLID_ID', 'SOURCE_OBJECT_MISMATCH']),
        **{k2: REF('section target solid', 'test_section_scope_controls_serve', 'test_section_scope_violations_refuse')
           for k2 in ('through_point', 'parallel_plane', 'perpendicular_line', 'parallel_line_a', 'parallel_line_b')}}.items()},
    'DerivedPlaneSectionSpec.cut_edges': REF('section target solid', 'test_section_scope_controls_serve', 'test_section_scope_violations_refuse'),
    'DerivedPlaneSectionSpec.named_intersections': s('EDGE_KEY', 'section target solid (keys: U-V edges, hyphenated ids legal)',
                                                     ['S5', 'S8'], 'test_f1_hyphenated_ids_serve_on_every_route', 'test_section_scope_violations_refuse',
                                                     ['INVALID_DERIVED_SECTION', 'UNKNOWN_SOLID_ID', 'SOURCE_OBJECT_MISMATCH']),
    'DerivedPlaneSectionSpecV2.stated_intersections': meta('container of StatedIntersectionSpec'),
    'DerivedPlaneSectionSpecV2.declared_boundary': REF('section target solid', 'test_section_scope_controls_serve', 'test_section_scope_violations_refuse'),
    'StatedIntersectionSpec.edge': REF('section target solid', 'test_section_scope_controls_serve', 'test_section_scope_violations_refuse'),
    'StatedIntersectionSpec.point': dict(category='DEFINITION_ID', note='names a constructed section point (ownership source)'),
    'StatedIntersectionSpec.quote': meta(),
}
for model in ('TypedFactNextPayloadV2',):
    for k in [k for k in CLASS if k.startswith('TypedFactNextPayload.')]:
        CLASS[k.replace('TypedFactNextPayload.', f'{model}.')] = CLASS[k]
SHAPES = {'ref': REF('premise scope', 'test_premise_scope_controls_serve', 'test_premise_scope_violations_refuse'),
          'id': s('SOLID_OPERAND', 'premise (height/altitude solid)', ['S2', 'S3'], 'test_premise_scope_controls_serve',
                  'test_premise_scope_violations_refuse', ['UNKNOWN_SOLID_ID', 'UNKNOWN_SOLID', 'SOURCE_OBJECT_MISMATCH']),
          'value': meta('value')}

VERSION = sys.argv[1] if len(sys.argv) > 1 else ''      # '' = original; 'v2' = preregistration-amendment-1 (F7)
if VERSION == 'v2':
    for k in ('MathGoalSpec.parent_solid_id', 'MathGoalSpec.cut_solid_id'):
        CLASS[k] = {**CLASS[k], 'rules': ['S1', 'S3'], 'negative_test': 'test_residual_cut_must_descend_from_parent',
                    'refusal_codes': ['UNKNOWN_SOLID_ID', 'SOURCE_OBJECT_MISMATCH']}
fields = C.field_paths(); kinds = C.kinds(); out = {}; missing = []
for path, ann in fields.items():
    if path.startswith('PremiseSpec.args['):
        shape = ann.rstrip('?=').rstrip('0123456789')
        shape = 'ref' if shape.startswith('ref') else shape
        out[path] = {**SHAPES[shape], 'shape': ann}
    elif path in CLASS:
        out[path] = {**CLASS[path], 'annotation': ann[:120]}
    else:
        missing.append(path)
stale = sorted(set(CLASS) - set(fields))
assert not missing and not stale, {'unclassified': missing, 'stale': stale}
doc = {'schema': 'SCHEMA_FIELD_INVENTORY/1', 'generator': 'backend/tests/geometry/scope_field_census.py + tools/build_inventory.py',
       'scope_categories': sorted(SCOPE), 'kinds': kinds, 'test_file': TEST, 'fields': out,
       'counts': {'fields': len(out), 'scope_bearing': sum(v['category'] in SCOPE for v in out.values())}}
with (HERE / f"schema-field-inventory{'-' + VERSION if VERSION else ''}.json").open('x', encoding='utf-8', newline='\n') as f:
    f.write(json.dumps(doc, ensure_ascii=False, indent=1) + '\n')
print(json.dumps(doc['counts']))
