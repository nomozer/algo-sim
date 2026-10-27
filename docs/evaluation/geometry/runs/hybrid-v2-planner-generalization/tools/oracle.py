"""Independent DEV prism oracle: rational Euclidean edge clipping and vector area.

No product imports, float arithmetic, engine layout or planner anchor selection.
Input coordinates explicitly realize the source premises at unit a=1 when symbolic.
"""
from fractions import Fraction as F
from functools import cmp_to_key


def _sub(a, b):
    return tuple(x - y for x, y in zip(a, b))


def _dot(a, b):
    return sum(x * y for x, y in zip(a, b))


def _cross(a, b):
    return (a[1]*b[2]-a[2]*b[1], a[2]*b[0]-a[0]*b[2], a[0]*b[1]-a[1]*b[0])


def section(geometry):
    """Return ordered exact cut vertices, squared area and whether a genuine interior cut exists."""
    pts = {k: tuple(map(F, v)) for k, v in geometry['points'].items()}
    base, top = geometry['base'], geometry['top']
    n = _sub(pts[geometry['line'][1]], pts[geometry['line'][0]])
    if _dot(n, n) == 0:
        raise ValueError('degenerate normal line')
    p = pts[geometry['point']]
    signed = {k: _dot(_sub(v, p), n) for k, v in pts.items()}
    edges = [(layer[i], layer[(i+1) % len(layer)]) for layer in (base, top) for i in range(len(layer))]
    edges += list(zip(base, top))
    cut = set()
    for a, b in edges:
        pa, pb, sa, sb = pts[a], pts[b], signed[a], signed[b]
        if sa == 0:
            cut.add(pa)
        if sb == 0:
            cut.add(pb)
        if sa * sb < 0:
            t = sa / (sa-sb)
            cut.add(tuple(x+t*(y-x) for x, y in zip(pa, pb)))
    ordered = sorted(cut)
    area_sq = F(0)
    if len(ordered) >= 3:
        center = tuple(sum(v[i] for v in ordered)/len(ordered) for i in range(3))
        # Dropping a nonzero normal component is injective on this plane; polar ordering is purely rational.
        drop = next(i for i, x in enumerate(n) if x)
        axes = [i for i in range(3) if i != drop]
        def polar(v):
            return tuple(v[i]-center[i] for i in axes)
        def compare(a, b):
            u, v = polar(a), polar(b)
            hu = int(u[1] < 0 or (u[1] == 0 and u[0] < 0))
            hv = int(v[1] < 0 or (v[1] == 0 and v[0] < 0))
            turn = u[0]*v[1]-u[1]*v[0]
            return hu-hv if hu != hv else (-1 if turn > 0 else 1 if turn < 0 else 0)
        ordered.sort(key=cmp_to_key(compare))
        vector_area = tuple(sum(_cross(v, ordered[(i+1) % len(ordered)])[j]
                                for i, v in enumerate(ordered))/2 for j in range(3))
        area_sq = _dot(vector_area, vector_area)
    signs = [signed[k] for k in base+top]
    return {'vertices': [[str(x) for x in v] for v in ordered], 'area_squared': str(area_sq),
            'interior_cut': any(s > 0 for s in signs) and any(s < 0 for s in signs)}
