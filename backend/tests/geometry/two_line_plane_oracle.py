"""Research oracle: exact facet halfspaces, not the product's edge-section algorithm.

No product import. Chart incidence uses covectors; area uses the supplied Gram matrix.
Authorship is shared with the implementer; algorithm independence is not evaluator independence.
"""
from fractions import Fraction as F
from itertools import combinations


def fixture_model(family):
    """Independent chart and Gram contracts of the preregistered source fixtures, not Engine output."""
    if family in ('pyramid','triangular_pyramid'):
        base=list('ABCD' if family=='pyramid' else 'ABC')
        pts={'A':(0,0,0),'B':(1,0,0),'C':(1,1,0) if family=='pyramid' else (0,1,0),'S':(0,0,1)}
        if family=='pyramid': pts['D']=(0,1,0)
        faces=[base]+[['S',a,b] for a,b in zip(base,base[1:]+base[:1])]
    else:
        base=list('ABCD' if family=='cuboid' else 'ABC')
        pts={'A':(0,0,0),'B':(1,0,0),'C':(1,1,0) if family=='cuboid' else (0,1,0)}
        if family=='cuboid': pts['D']=(0,1,0)
        pts.update({k+"'":(p[0],p[1],1) for k,p in list(pts.items())})
        faces=[base,[k+"'" for k in base]]+[[a,b,b+"'",a+"'"] for a,b in zip(base,base[1:]+base[:1])]
    gram=((4,0,0),(0,16 if family=='cuboid' else 4,0),(0,0,9)) if family in ('pyramid','cuboid') else ((4,2,0),(2,4,0),(0,0,9))
    return pts,faces,gram


def sub(a, b):
    return tuple(F(x) - F(y) for x, y in zip(a, b))


def dot(a, b):
    return sum(x*y for x, y in zip(a, b))


def cross(a, b):
    return (a[1]*b[2]-a[2]*b[1], a[2]*b[0]-a[0]*b[2], a[0]*b[1]-a[1]*b[0])


def solve(rows, rhs):
    a = [[F(x) for x in row] + [F(y)] for row, y in zip(rows, rhs)]
    for j in range(3):
        pivot = next((i for i in range(j, 3) if a[i][j]), None)
        if pivot is None:
            return None
        a[j], a[pivot] = a[pivot], a[j]
        d = a[j][j]
        a[j] = [x/d for x in a[j]]
        for i in range(3):
            if i != j:
                d = a[i][j]
                a[i] = [x-d*y for x, y in zip(a[i], a[j])]
    return tuple(row[3] for row in a)


def section(points, faces, anchor, lines, gram=((1,0,0),(0,1,0),(0,0,1)), flip=False):
    pts = {k: tuple(map(F, v)) for k, v in points.items()}
    m = tuple(map(F, anchor))
    u, v = [sub(pts[b], pts[a]) for a, b in lines]
    if not any(u) or not any(v):
        return {"status": "DEGENERATE_LINE"}
    n = cross(u, v)
    if not any(n):
        return {"status": "PLANE_NOT_UNIQUE"}
    if flip:
        n = tuple(-x for x in n)
    d = dot(n, m)
    if any(dot(n, pts[a]) == d for a, _b in lines):
        return {"status": "LINE_CONTAINED_IN_PLANE"}
    halfspaces = []
    vertices = {k for face in faces for k in face}
    for face in faces:
        a, b, c = [pts[k] for k in face[:3]]
        f = cross(sub(b,a), sub(c,a))
        z = dot(f, a)
        signs = [dot(f, pts[k])-z for k in vertices]
        assert not (any(x>0 for x in signs) and any(x<0 for x in signs)), 'non-convex oracle input'
        if any(x>0 for x in signs):
            f, z = tuple(-x for x in f), -z
        halfspaces.append((f,z))
    signs = [dot(n, pts[k])-d for k in vertices]
    if sum(x==0 for x in signs)>=3 and not (any(x>0 for x in signs) and any(x<0 for x in signs)):
        return {"status": "SECTION_PLANE_IS_FACE"}
    found = set()
    for (a,x),(b,y) in combinations(halfspaces,2):
        p = solve((n,a,b),(d,x,y))
        if p is not None and all(dot(f,p)<=z for f,z in halfspaces):
            found.add(p)
    if len(found)<3:
        return {"status": "NO_POLYGON", "vertices": sorted(found)}
    axis = next(i for i,x in enumerate(n) if x)
    axes = [i for i in range(3) if i != axis]
    ordered = sorted(found, key=lambda p: tuple(p[i] for i in axes))
    def turn(a,b,c):
        x,y = axes
        return (b[x]-a[x])*(c[y]-b[y])-(b[y]-a[y])*(c[x]-b[x])
    def hull(seq):
        h=[]
        for p in seq:
            while len(h)>1 and turn(h[-2],h[-1],p)<=0:
                h.pop()
            h.append(p)
        return h
    ring = hull(ordered)[:-1]+hull(ordered[::-1])[:-1]
    area_vector = tuple(sum(cross(p,q)[i] for p,q in zip(ring,ring[1:]+ring[:1]))/2 for i in range(3))
    g = tuple(tuple(map(F,row)) for row in gram)
    determinant = dot(g[0],cross(g[1],g[2]))
    inverse_times_area = solve(g,area_vector)
    assert determinant>0 and inverse_times_area is not None
    area_sq = determinant*dot(area_vector,inverse_times_area)
    return {"status":"SERVED", "vertices":ring, "area_sq":area_sq, "normal":n, "offset":d}
