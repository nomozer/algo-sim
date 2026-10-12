"""Read-only checkout review probes: expected safety/positive behavior, no provider."""
import pytest
from tests.geometry.test_question_local_givens import run
from tests.geometry import hybrid_compiler_benchmark as HB
from app.ai.function_route import run_fact_route, run_function_route
from app.simulation.geometry_functions.planner import lap_ke_hoach


@pytest.mark.parametrize('arm', ['A', 'B'])
@pytest.mark.parametrize('sentence', [
    'Tính SC. Tính SC khi SA = 5.',
    'Tính SC. Tính SC nếu SA = 5.',
    'Tính SC. Tính SC sau khi thay SA thành 5.',
    'Tính SC. SA = 5.',
    'Tính SC. SA song song với (ABCD).',
])
def test_every_changed_question_context_is_refused(arm, sentence):
    r = run(sentence, arm)
    assert r.status == 'REFUSED', (r.status, r.code, r.answers, bool(r.scene3d))


@pytest.mark.parametrize('arm', ['A', 'B'])
@pytest.mark.parametrize('kind', ['perpendicular', 'base_side'])
def test_local_fact_cannot_replace_an_omitted_original_shape_fact(arm, kind):
    text, facts = HB._square()
    if kind == 'perpendicular':
        sentence = 'Tính SC, biết SB vuông góc với (ABCD).'
        local = HB._f('local', 'perpendicular', 'SB vuông góc với (ABCD)',
                      points_a=['S', 'B'], points_b=list('ABCD'))
        retained = facts[:2] + facts[3:]
    else:
        sentence = 'Tính SC, biết đáy ABCD là hình vuông cạnh 4.'
        local = HB._f('local', 'polygon_shape', 'đáy ABCD là hình vuông cạnh 4',
                      points=list('ABCD'), shape='square', value='4')
        retained = facts[:1] + facts[2:]
    r = run(sentence, arm, [local], base=(text, retained))
    assert r.status == 'REFUSED', (r.status, r.code, r.answers, bool(r.scene3d))


@pytest.mark.parametrize('arm', ['A', 'B'])
def test_construction_request_has_the_same_context_obligation(arm):
    text, facts = HB._square()
    mid = HB._mid('mid', 'M', 'S', 'C')
    sentence = 'Vẽ thiết diện của hình chóp S.ABCD cắt bởi (MAB), biết SA = 5.'
    section = HB._f('section', 'section', sentence, solid='S.ABCD', points=list('MAB'))
    source = ' '.join(text + mid['quotes'] + [sentence])
    payload = {'facts': facts + [mid, section]}
    r = (run_fact_route(source, payload) if arm == 'B' else
         run_function_route(source, {'calls': lap_ke_hoach(payload, source).calls}))
    assert r.status == 'REFUSED', (r.status, r.code, bool(r.scene3d))


@pytest.mark.parametrize('arm', ['A', 'B'])
def test_matching_canonical_square_side_still_serves(arm):
    r = run('Tính SC, biết AB = 2.', arm)
    assert r.status == 'SERVED', (r.status, r.code, r.reason)


def test_auxiliary_short_quote_cannot_hide_later_assumption():
    text, facts = HB._square()
    clean = 'Tính khoảng cách từ S đến BD.'
    source = ' '.join(text) + ' ' + clean + ' SA = 5.'
    question = HB._ask('q', clean, 'distance', points_a=['S'], points_b=list('BD'))
    r = run_fact_route(source, {'facts': facts + [question]})
    assert r.status == 'REFUSED', (r.status, r.code, r.answers, bool(r.scene3d))


@pytest.mark.parametrize('arm', ['A', 'B'])
@pytest.mark.parametrize('sentence', ['Tính SC, biết SA = 6/2.', 'Tính SC, biết AS vuông góc với (ABC).'])
def test_supported_matching_controls(arm, sentence):
    r = run(sentence, arm)
    assert r.status == 'SERVED', (r.status, r.code, r.reason)
    assert HB.answer_square(r.answers['q']) == 17
