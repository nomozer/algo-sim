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
from app.simulation.semantic_program import simulation_state as G

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
        if j.get('theorem') == 'COPLANAR_TRACE_INTERSECTION':
            if not trace_holds(sec, plane, st, j, by):
                bad.append((e['step_index'], 'trace', j))
            continue
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


def trace_holds(sec, plane, st, j, by):
    """Run `scene3d-causal-pedagogical-integrity`: a trace-method reason re-checked from the scene's own coordinates —
    every derived point lies on the cutting plane, on its face plane and on its edge line; both endpoints of the edge lie
    on the line through the two points the trace names; auxiliary points are exactly the off-segment derived points."""
    q = lambda v: [Fraction(str(x)) for x in v]                                  # noqa: E731
    solid = next(by[d] for d in sec['depends'] if by[d]['type'] == 'solid')
    vs = [q(v) for v in solid['vertices']]
    sub = lambda u, v: [u[i] - v[i] for i in range(3)]                           # noqa: E731
    cr = lambda u, v: (u[1] * v[2] - u[2] * v[1], u[2] * v[0] - u[0] * v[2], u[0] * v[1] - u[1] * v[0])  # noqa: E731
    dot = lambda u, v: sum(u[i] * v[i] for i in range(3))                       # noqa: E731
    p0, n = q(plane['point']), q(plane['normal'])
    td = st.get('trace_derivation') or {}
    if not td.get('verified_exact') or j.get('verified_exact') is not True:
        return False
    derived = {d['index']: q(d['xyz']) for d in td['derivations']}
    for d in td['derivations']:
        x, f, (u, w) = q(d['xyz']), solid['faces'][d['face']], d['edge']
        nf = cr(sub(vs[f[1]], vs[f[0]]), sub(vs[f[2]], vs[f[0]]))
        if dot(n, sub(x, p0)) or dot(nf, sub(x, vs[f[0]])) or any(cr(sub(x, vs[u]), sub(vs[w], vs[u]))):
            return False
    def pos(ref):
        if 'vertex' in ref:
            return vs[ref['vertex']]
        if 'id' in ref:
            return q(by[ref['id']]['xyz'])
        return derived[ref['derived']]
    thr = [pos(r) for r in td['through']]
    a, b = q(st['a']), q(st['b'])
    if len(thr) == 2 and any(any(cr(sub(x, thr[0]), sub(thr[1], thr[0]))) for x in (a, b)):
        return False
    poly = [q(p) for p in sec['polygon']]
    off = [q(d['xyz']) for d in td['derivations'] if not (d['on_edge_segment'] and q(d['xyz']) in poly)]
    return sorted(off) == sorted(q(x['xyz']) for x in j.get('auxiliary_points') or ())


@pytest.mark.parametrize('cid', SERVED)
def test_every_emitted_justification_holds_exactly(cid):
    bad, _seen = violations(scene(cid))
    assert bad == []


def test_justifications_are_emitted_where_the_theorem_applies_and_only_there():
    # parallel-to-base cut: all three lateral intersections are parallel to base edges
    assert violations(scene('TP1.canon.area'))[1] == 3
    # perpendicular cut of the same pyramid: only the face whose base edge is parallel to the cut has the PARALLEL
    # reason. Superseded count (run `scene3d-causal-pedagogical-integrity`): this asserted `seen == 1` when no other
    # reason existed; the remaining edges now carry an exactly re-checked trace-method reason.
    sc = scene('TP3.canon.area')
    th = [(e.get('details') or {}).get('justification', {}).get('theorem') for e in sc['events'] if e.get('justification_text')]
    assert th.count('PARALLEL_LINE_PLANE_INTERSECTION') == 1 and violations(sc)[0] == []


def _synthetic(edge_in_plane: bool):
    """Geometry-layer objects: unit square face ABCD (z=0). Cutting plane y = 0 ⇒ the section edge lies ON the face edge
    AB, which is IN the plane (so "(α) ∥ AB" would be false; CD ∥ AB off the plane is the valid witness); or y = 1/2."""
    solid = {'id': 'k', 'type': 'solid', 'sources': list('ABCD'),
             'vertices': [['0', '0', '0'], ['1', '0', '0'], ['1', '1', '0'], ['0', '1', '0']], 'faces': [[0, 1, 2, 3]]}
    if edge_in_plane:
        plane = {'id': 'p', 'type': 'plane3', 'point': ['0', '0', '0'], 'normal': ['0', '1', '0']}
        step = {'face_index': 0, 'a': ['0', '0', '0'], 'b': ['1', '0', '0']}
    else:
        plane = {'id': 'p', 'type': 'plane3', 'point': ['0', '1/2', '0'], 'normal': ['0', '1', '0']}
        step = {'face_index': 0, 'a': ['0', '1/2', '0'], 'b': ['1', '1/2', '0']}
    return [solid, plane, {'id': 's', 'type': 'section', 'sources': ['k', 'p'], 'steps': [step]}]


def _edge(objects):
    G._canh_song_song_thiet_dien(objects)
    return objects[2]['steps'][0].get('parallel_face_edge')


def test_edge_lying_in_the_cutting_plane_is_never_the_witness():
    assert _edge(_synthetic(edge_in_plane=True)) in (None, [2, 3])                # never AB = [0, 1]: AB ⊂ (α)
    assert _edge(_synthetic(edge_in_plane=False)) in ([0, 1], [2, 3])


def test_inconsistent_face_index_gets_no_claim():
    # review M1: the step names face 0 (z = 0) but its edge lies at z = 1 — the face index is not trusted
    o = _synthetic(edge_in_plane=False)
    o[2]['steps'][0].update(a=['0', '1/2', '1'], b=['1', '1/2', '1'])
    assert _edge(o) is None
    # the cutting plane parallel to the face (z = 1 vs face z = 0): no intersection line, no claim
    o = _synthetic(edge_in_plane=False)
    o[1].update(point=['0', '0', '1'], normal=['0', '0', '1'])
    o[2]['steps'][0].update(a=['0', '1/2', '1'], b=['1', '1/2', '1'])
    assert _edge(o) is None


def test_presentation_layer_carries_but_never_computes():
    # scene3d imports no geometry (test_scene3d.py); without the geometry layer's fact it says nothing
    sec = {'id': 's', 'type': 'section', 'depends': ['k', 'p'], 'steps': [{'face_index': 0, 'a': [], 'b': []}]}
    by = {'k': {'id': 'k', 'type': 'solid', 'vertex_ids': list('ABCD'), 'faces': [[0, 1, 2, 3]]},
          'p': {'id': 'p', 'type': 'plane3', 'notation': '(α)'}, **{c: {'id': c, 'notation': c} for c in 'ABCD'}}
    assert S._ly_do_canh_thiet_dien({'details': {'canh': 0}}, sec, by) is None
    sec['steps'][0]['parallel_face_edge'] = [2, 3]
    assert S._ly_do_canh_thiet_dien({'details': {'canh': 0}}, sec, by)['line'] == 'CD'


def test_off_plane_mutant_is_caught_on_the_in_plane_edge(monkeypatch):
    _mutant(monkeypatch, 'if any(cheo(d, hieu(y, x))) or not vo(n, hieu(x, p0)):', 'if any(cheo(d, hieu(y, x))):')
    assert _edge(_synthetic(edge_in_plane=True)) == [0, 1]                        # the mutant claims (α) ∥ AB ⊂ (α)


def _mutant(monkeypatch, old, new):
    src = textwrap.dedent(inspect.getsource(G._canh_song_song_thiet_dien))
    assert src.count(old) == 1, old
    ns = dict(vars(G))
    exec(compile(src.replace(old, new), '<mutant>', 'exec'), ns)
    monkeypatch.setattr(G, '_canh_song_song_thiet_dien', ns['_canh_song_song_thiet_dien'])


def test_dropping_the_parallel_check_is_caught(monkeypatch):
    _mutant(monkeypatch, 'if any(cheo(d, hieu(y, x))) or not vo(n, hieu(x, p0)):', 'if not vo(n, hieu(x, p0)):')
    bad = [b for cid in ('TP3.canon.area', 'CB2.canon.area', 'HB1.canon.area', 'TP1.canon.area') for b in violations(scene(cid))[0]]
    assert bad, 'mutant produced only valid justifications'
