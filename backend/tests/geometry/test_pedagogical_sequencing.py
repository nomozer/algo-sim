"""Learner-facing construction order of Hybrid scenes — run `pedagogical-construction-sequencing` (development split).

Contract O1–O4 in `construction_sequencing.py`; corpus `docs/.../pedagogical-construction-sequencing/inputs/corpus.json`.
"""
import json
import re

import pytest

from app.ai.function_route import run_fact_route
from tests.geometry.construction_sequencing import check
from tests.geometry.test_two_line_plane_section import CASES, problem


def served(i, variant=None):
    c = CASES[i]
    text, payload = problem(c['family'], c['mid'], c['lines'])
    if variant == 'rename':
        ren = str.maketrans('SABCDMP', 'TEFGKNQ')
        rename = lambda s: re.sub(r"(?<!\w)[A-Z][A-Z0-9'.]*(?!\w)", lambda m: m[0].translate(ren), s)
        text, payload = rename(text), json.loads(rename(json.dumps(payload, ensure_ascii=False)))
    elif variant == 'collision':
        text = text.replace('Gọi M', 'Gọi H').replace('qua M', 'qua H')
        payload = json.loads(json.dumps(payload, ensure_ascii=False).replace('"M"', '"H"')
                             .replace('Gọi M', 'Gọi H').replace('qua M', 'qua H'))
    r = run_fact_route(text, payload)
    assert r.status == 'SERVED', (r.code, r.reason)
    return r


@pytest.mark.parametrize('case', [(0, None), (18, None), (33, None), (0, 'rename'), (0, 'collision')],
                         ids=['pyramid', 'prism', 'cuboid', 'pyramid-rename', 'pyramid-midpoint-named-H'])
def test_learner_order_builds_the_solid_before_auxiliary_points(case):
    v = check(served(*case).scene3d)
    assert v == {'O1': [], 'O2': [], 'O3': [], 'O4': []}, v


def test_apex_projection_keeps_the_height_step():
    # review C1: the foot of the apex on the base is part of the solid's formation, not an auxiliary point after it
    from tests.geometry import hybrid_compiler_benchmark as HB
    q, f = HB._with(HB._square(), HB._proj('f5', 'H', 'S', 'ABCD'), HB._ask('q', 'Tính độ dài SH.', 'length', points=['S', 'H']))
    r = run_fact_route(' '.join(q), {'facts': f})
    assert r.status == 'SERVED' and r.answers == {'q': '3'}
    roles = [x for st in r.scene3d['formation']['steps'] for x in st['formation_roles']]
    assert roles.index('CONSTRUCT_BASE') < roles.index('CONSTRUCT_HEIGHT') < roles.index('CLOSE_SOLID')
    assert check(r.scene3d) == {'O1': [], 'O2': [], 'O3': [], 'O4': []}


def test_refusal_is_unchanged():
    c = CASES[3]
    r = run_fact_route(*problem(c['family'], c['mid'], c['lines']))
    assert r.status == 'REFUSED' and r.code == 'PLANE_NOT_UNIQUE' and not r.scene3d


def test_reorder_keeps_points_a_solid_needs_before_it():
    from app.simulation.geometry_functions.engine import thu_tu_su_pham
    blocks = [('A', [{'target_var': 'A'}]), ('M', [{'target_var': 'M', 'expr': {'a': 'A', 'b': 'B'}}]),
              ('N', [{'target_var': 'N', 'expr': {'a': 'A', 'b': 'C'}}]),
              ('X', [{'target_var': 'X', 'expr': {'point': 'N', 'vector': 'v'}}])]
    truoc, sau = thu_tu_su_pham(blocks, {'A', 'X'})         # the solid has vertex X built from N
    assert [t for t, _ in truoc] == ['A', 'N', 'X'] and [t for t, _ in sau] == ['M']


@pytest.mark.parametrize('fn', ['pyramid', 'regular_pyramid'])
def test_every_pyramid_call_declares_its_source_topology(fn):
    # found by the ordering-check split (benchmark-B02): `regular_pyramid` also builds a solid (`thu_khoi`)
    from types import SimpleNamespace as N
    from app.simulation.geometry_functions.engine import hop_dong_to_po_da_khai
    topo = hop_dong_to_po_da_khai((N(fn=fn, args=N(apex='S', base=['A', 'B', 'C']),
                                     quotes=('Cho hình chóp tam giác đều S.ABC',)),))
    assert topo is not None and topo.solid_topology.apex == 'S'


@pytest.mark.parametrize('quote,declared', [("Cho lăng trụ đứng ABC.A'B'C' có đáy là tam giác đều.", True),
                                            ("Cho hình hộp chữ nhật ABCD.A′B′C′D′.", True),
                                            ("Cho lăng trụ đứng có đáy là tam giác đều ABC.", False),
                                            ("Cho lăng trụ đứng ABC.A'B'D'.", False)])
def test_prism_topology_is_declared_only_from_source_notation(quote, declared):
    from types import SimpleNamespace as N
    from app.simulation.geometry_functions.engine import hop_dong_to_po_da_khai
    base, top = (['A', 'B', 'C', 'D'], ["A'", "B'", "C'", "D'"]) if 'ABCD' in quote else (['A', 'B', 'C'], ["A'", "B'", "C'"])
    topo = getattr(hop_dong_to_po_da_khai((N(fn='prism', args=N(base=base, top=top, right=True), quotes=(quote,)),)),
                   'solid_topology', None)
    assert (getattr(topo, 'solid_kind', None) == 'prism') is declared
    if declared:
        assert topo.base_cycle == tuple(base) and topo.correspondence == tuple(zip(base, top))


def test_an_oblique_prism_is_not_declared_right():
    from types import SimpleNamespace as N
    from app.simulation.geometry_functions.engine import hop_dong_to_po_da_khai
    c = N(fn='prism', args=N(base=['A', 'B', 'C'], top=["A'", "B'", "C'"], right=False), quotes=("Cho lăng trụ ABC.A’B’C’.",))
    assert hop_dong_to_po_da_khai((c,)).solid_topology.lateral_structure is None


def test_section_mab_orders_m_after_solid_and_never_fabricates_perpendicular_height():
    from tests.geometry import hybrid_compiler_benchmark as HB
    sec_q = 'Xác định thiết diện của hình chóp S.ABCD với (MAB).'
    ask_q = 'Tính diện tích thiết diện của hình chóp S.ABCD với (MAB).'
    q, f = HB._with(
        HB._square(),
        HB._mid('fm', 'M', 'S', 'C'),
        HB._f('fsec', 'section', sec_q, solid='S.ABCD', points=['M', 'A', 'B']),
        HB._ask('q', ask_q, 'area', solid='S.ABCD', points=['M', 'A', 'B']),
    )
    r = run_fact_route(' '.join(q), {'facts': f})
    assert r.status == 'SERVED', (r.code, r.reason)
    assert check(r.scene3d) == {'O1': [], 'O2': [], 'O3': [], 'O4': []}
    from tests.geometry.construction_sequencing import first_steps
    first = first_steps(r.scene3d)
    assert first['khoi_S_ABCD'] < first['M']
    by_id = {o['id']: o for o in r.scene3d['objects']}
    assert by_id['canh_ben_S_A'].get('perpendicular_witness') is not None

    # Dropping SA ⊥ (ABCD) leaves the metric section area underdetermined; Route D refuses rather than assuming SA ⊥ (ABCD).
    q_no_perp = [s for s in q if 'vuông góc' not in s]
    f_no_perp = [x for x in f if x['id'] != 'f3']
    r_no_perp = run_fact_route(' '.join(q_no_perp), {'facts': f_no_perp})
    assert r_no_perp.status == 'REFUSED' and not r_no_perp.scene3d


def test_valid_exterior_q_on_extended_sd_preserves_pedagogical_order():
    from fractions import Fraction as F
    from tests.geometry import hybrid_compiler_benchmark as HB
    q_base, f_base = HB._square()
    q_base[3] = 'SA = 4.'
    f_base[3]['quotes'] = ['SA = 4.']
    f_base[3]['value'] = '4'
    q, f = HB._with(
        (q_base, f_base),
        HB._f('fm', 'point_def', 'Gọi M là điểm thuộc cạnh SA sao cho SM = 3MA.',
              point='M', point_kind='divide_segment', points=['S', 'A'], value='3/4'),
        HB._mid('fn', 'N', 'S', 'B'),
        HB._f('fp', 'point_def', 'Gọi P là điểm thuộc cạnh SC sao cho SP = 3PC.',
              point='P', point_kind='divide_segment', points=['S', 'C'], value='3/4'),
        HB._ilp('fq', 'Q', 'SD', 'MNP'),
        HB._f('fsec', 'section', 'Xác định thiết diện của hình chóp S.ABCD với (MNP).',
              solid='S.ABCD', points=['M', 'N', 'P']),
        HB._ask('q', 'Tính độ dài SQ.', 'length', points=['S', 'Q']),
    )
    r = run_fact_route(' '.join(q), {'facts': f})
    assert r.status == 'SERVED', (r.code, r.reason)
    assert check(r.scene3d) == {'O1': [], 'O2': [], 'O3': [], 'O4': []}
    pts = {o['id']: [F(c) for c in o['xyz']] for o in r.scene3d['objects'] if o['type'] == 'point3'}
    s, d, q_pt = pts['S'], pts['D'], pts['Q']
    # Verify Q = S + (3/2)(D - S), strictly exterior beyond D (t = 3/2 > 1).
    assert [q_pt[i] - s[i] for i in range(3)] == [F(3, 2) * (d[i] - s[i]) for i in range(3)]


def test_contradictory_q_premises_are_refused_fail_closed():
    from tests.geometry import hybrid_compiler_benchmark as HB
    # Case 1: invalid segment division ratio t = 3/2 > 1 claimed as interior segment point.
    q1, f1 = HB._with(
        HB._square(),
        HB._f('fq', 'point_def', 'Lấy Q trên đoạn SD với tỉ số SQ/SD = 3/2.',
              point='Q', point_kind='divide_segment', points=['S', 'D'], value='3/2'),
        HB._ask('q', 'Tính độ dài SQ.', 'length', points=['S', 'Q']),
    )
    r1 = run_fact_route(' '.join(q1), {'facts': f1})
    assert r1.status == 'REFUSED' and r1.code == 'INVALID_RATIO' and not r1.scene3d

    # Case 2: M, N, P midpoints of SA, SB, SC force Q = SD ∩ (MNP) to be midpoint of SD, contradicting SQ = 6.
    q2, f2 = HB._with(
        HB._square(),
        HB._mid('fm', 'M', 'S', 'A'),
        HB._mid('fn', 'N', 'S', 'B'),
        HB._mid('fp', 'P', 'S', 'C'),
        HB._ilp('fq', 'Q', 'SD', 'MNP'),
        HB._f('flen', 'length', 'SQ = 6.', points=['S', 'Q'], measure='segment', value='6'),
        HB._ask('q', 'Tính độ dài SQ.', 'length', points=['S', 'Q']),
    )
    r2 = run_fact_route(' '.join(q2), {'facts': f2})
    assert r2.status == 'REFUSED' and not r2.scene3d

