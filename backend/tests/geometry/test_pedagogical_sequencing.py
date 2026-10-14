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
    topo = getattr(hop_dong_to_po_da_khai((N(fn='prism', args=N(base=base, top=top), quotes=(quote,)),)),
                   'solid_topology', None)
    assert (getattr(topo, 'solid_kind', None) == 'prism') is declared
    if declared:
        assert topo.base_cycle == tuple(base) and topo.correspondence == tuple(zip(base, top))
