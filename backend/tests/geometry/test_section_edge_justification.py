"""W4 · the "why" of a section edge is emitted only when exactly verified.

An independent checker re-reads every emitted justification from the scene's own point coordinates: the named edge XY
must be parallel to the section edge, and X must lie off the cutting plane (so XY ∥ the plane). Mutants that drop either
condition from the product must make the checker fail."""
from copy import deepcopy
from fractions import Fraction
import inspect
import json
import re
import textwrap
from pathlib import Path

import pytest

from app.ai.adapter4_route import run_typed_fact_next_v2_route
from app.simulation.semantic_program import scene3d as S

RUN = Path(__file__).resolve().parents[3] / 'docs/evaluation/geometry/runs/geometry-generalization-and-pedagogical-construction'
CASES = json.loads((RUN / 'dev-corpus/cases.json').read_text(encoding='utf-8'))
SERVED = sorted(k for k, c in CASES.items() if c['class'] in ('CANON', 'VARIANT') and k.endswith('.area'))


def scene(cid):
    r = run_typed_fact_next_v2_route(deepcopy(CASES[cid]['payload']))
    assert r.status == 'SERVED', (cid, r.code)
    return r.scene3d


def violations(sc):
    """Independent re-check; returns the justifications that do not hold."""
    q = lambda v: [Fraction(str(x)) for x in v]                                  # noqa: E731
    by = {o['id']: o for o in sc['objects']}
    pos = {}
    for o in sc['objects']:
        if o['type'] == 'point3':
            for k in ('display_label', 'notation', 'label'):
                if o.get(k):
                    pos[o[k]] = q(o['xyz'])
    bad, seen = [], 0
    for e in sc['events']:
        j = (e.get('details') or {}).get('justification')
        if not e.get('justification_text'):
            continue
        seen += 1
        sec = by[e['object']]
        plane = next(by[d] for d in sec['depends'] if by[d]['type'] == 'plane3')
        st = sec['steps'][e['details']['canh']]
        a, b = q(st['a']), q(st['b'])
        names = re.findall(r"[A-Z][0-9]*[′']?", j['line'])
        if len(names) != 2 or any(n not in pos for n in names) or not j.get('verified_exact'):
            bad.append((e['step_index'], 'unresolved', j)); continue
        x, y = pos[names[0]], pos[names[1]]
        d = [b[i] - a[i] for i in range(3)]; v = [y[i] - x[i] for i in range(3)]
        cross = (d[1] * v[2] - d[2] * v[1], d[2] * v[0] - d[0] * v[2], d[0] * v[1] - d[1] * v[0])
        p0, n = q(plane['point']), q(plane['normal'])
        off = sum(n[i] * (x[i] - p0[i]) for i in range(3))
        if any(cross) or off == 0 or '_' in e['justification_text']:
            bad.append((e['step_index'], j['line'], any(cross), off))
    return bad, seen


@pytest.mark.parametrize('cid', SERVED)
def test_every_emitted_justification_holds_exactly(cid):
    bad, _seen = violations(scene(cid))
    assert bad == []


def test_justifications_are_emitted_where_the_theorem_applies_and_only_there():
    # parallel-to-base cut: all three lateral intersections are parallel to base edges
    assert violations(scene('TP1.canon.area'))[1] == 3
    # perpendicular cut of the same pyramid: only the face whose base edge is parallel to the cut is justified
    assert violations(scene('TP3.canon.area'))[1] == 1


def _synthetic(edge_in_plane: bool):
    """Unit square face ABCD (z=0) of a solid. Cutting plane y = 0 ⇒ the section edge lies ON the face edge AB, which is
    IN the plane (so "(α) ∥ AB" would be false; CD ∥ AB off the plane is the valid witness); or y = 1/2 ⇒ edge ∥ AB."""
    pts = {'A': ['0', '0', '0'], 'B': ['1', '0', '0'], 'C': ['1', '1', '0'], 'D': ['0', '1', '0']}
    by = {k: {'id': k, 'type': 'point3', 'notation': k} for k in pts}
    by['k'] = {'id': 'k', 'type': 'solid', 'vertex_ids': list(pts), 'vertices': list(pts.values()), 'faces': [[0, 1, 2, 3]]}
    if edge_in_plane:
        by['p'] = {'id': 'p', 'type': 'plane3', 'notation': '(α)', 'point': ['0', '0', '0'], 'normal': ['0', '1', '0']}
        step = {'face_index': 0, 'a': ['0', '0', '0'], 'b': ['1', '0', '0']}
    else:
        by['p'] = {'id': 'p', 'type': 'plane3', 'notation': '(α)', 'point': ['0', '1/2', '0'], 'normal': ['0', '1', '0']}
        step = {'face_index': 0, 'a': ['0', '1/2', '0'], 'b': ['1', '1/2', '0']}
    sec = {'id': 's', 'type': 'section', 'depends': ['k', 'p'], 'steps': [step]}
    return {'details': {'canh': 0}}, sec, by


def test_edge_lying_in_the_cutting_plane_is_never_the_witness():
    j = S._ly_do_canh_thiet_dien(*_synthetic(edge_in_plane=True))
    assert j is None or j['line'] != 'AB'                                          # AB ⊂ (α): never "(α) ∥ AB"
    j = S._ly_do_canh_thiet_dien(*_synthetic(edge_in_plane=False))
    assert j and j['line'] in ('AB', 'CD') and j['verified_exact']


def test_inconsistent_face_index_gets_no_claim():
    # review M1: the step names face 0 (z = 0) but its edge lies at z = 1 — the face index is not trusted
    e, sec, by = _synthetic(edge_in_plane=False)
    sec['steps'][0].update(a=['0', '1/2', '1'], b=['1', '1/2', '1'])
    assert S._ly_do_canh_thiet_dien(e, sec, by) is None
    # the cutting plane parallel to the face (z = 1 vs face z = 0): no intersection line, no claim
    e, sec, by = _synthetic(edge_in_plane=False)
    by['p'].update(point=['0', '0', '1'], normal=['0', '0', '1'])
    sec['steps'][0].update(a=['0', '1/2', '1'], b=['1', '1/2', '1'])
    assert S._ly_do_canh_thiet_dien(e, sec, by) is None


def test_off_plane_mutant_is_caught_on_the_in_plane_edge(monkeypatch):
    _mutant(monkeypatch, 'if any(cheo(d, hieu(y, x))) or not vo(n, hieu(x, p0)):', 'if any(cheo(d, hieu(y, x))):')
    assert S._ly_do_canh_thiet_dien(*_synthetic(edge_in_plane=True))['line'] == 'AB'   # the mutant claims (α) ∥ AB ⊂ (α)


def _mutant(monkeypatch, old, new):
    src = textwrap.dedent(inspect.getsource(S._ly_do_canh_thiet_dien))
    assert src.count(old) == 1, old
    ns = dict(vars(S))
    exec(compile(src.replace(old, new), '<mutant>', 'exec'), ns)
    monkeypatch.setattr(S, '_ly_do_canh_thiet_dien', ns['_ly_do_canh_thiet_dien'])


def test_dropping_the_parallel_check_is_caught(monkeypatch):
    _mutant(monkeypatch, 'if any(cheo(d, hieu(y, x))) or not vo(n, hieu(x, p0)):', 'if not vo(n, hieu(x, p0)):')
    bad = [b for cid in ('TP3.canon.area', 'CB2.canon.area', 'HB1.canon.area', 'TP1.canon.area') for b in violations(scene(cid))[0]]
    assert bad, 'mutant produced only valid justifications'
