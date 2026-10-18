"""Independent, stdlib-only Fraction oracle. No engine imports or provider calls.

Run directly to verify corpus.json. --author writes this author's artifacts first.
"""
from fractions import Fraction as F
from pathlib import Path
import hashlib
import json
import sys

ROOT = Path(__file__).resolve().parent
CASES = []
FACTS = {}
EXPECTED = {}


def vec(a, b):
    return tuple(F(y) - F(x) for x, y in zip(a, b))


def dot(a, b):
    return sum(x * y for x, y in zip(a, b))


def cross(a, b):
    return (a[1]*b[2]-a[2]*b[1], a[2]*b[0]-a[0]*b[2], a[0]*b[1]-a[1]*b[0])


def midpoint(a, b):
    return tuple((F(x)+F(y))/2 for x, y in zip(a, b))


def centroid(*p):
    return tuple(sum(F(q[i]) for q in p)/len(p) for i in range(3))


def length2(a, b):
    v = vec(a, b)
    return dot(v, v)


def line_distance2(p, a, b):
    v, w = vec(a, b), vec(a, p)
    c = cross(v, w)
    return dot(c, c)/dot(v, v)


def plane_distance2(p, a, b, c):
    n = cross(vec(a, b), vec(a, c))
    return dot(vec(a, p), n)**2/dot(n, n)


def segment_distance2(p, a, b):
    v, w = vec(a, b), vec(a, p)
    t = max(F(0), min(F(1), dot(w, v)/dot(v, v)))
    q = tuple(F(x)+t*y for x, y in zip(a, v))
    return length2(p, q)


def triangle_area2(a, b, c):
    n = cross(vec(a, b), vec(a, c))
    return dot(n, n)/4


def parallelogram_area2(a, b, d):
    n = cross(vec(a, b), vec(a, d))
    return dot(n, n)


def tetra_volume2(a, b, c, d):
    return (dot(vec(a, b), cross(vec(a, c), vec(a, d)))/6)**2


def prism_volume2(a, b, c, ap):
    return (dot(vec(a, ap), cross(vec(a, b), vec(a, c)))/2)**2


def angle_cos2(a, b, p, q, r):
    v, n = vec(a, b), cross(vec(p, q), vec(p, r))
    return 1-dot(v, n)**2/(dot(v, v)*dot(n, n))


def fact(kind, quote, role='premise', **kw):
    return dict(kind=kind, role=role, quotes=[quote], **kw)


def req(intent, quantity, target, quote, disposition='answer', numeric=None, cosine=False):
    oracle = None if numeric is None else {('cos_squared' if cosine else 'value_squared'): str(F(numeric))}
    return dict(intent=intent, quantity=quantity, target=target, source_quote=quote, disposition=disposition, oracle=oracle)


def add(cid, split, family, text, labels, facts, requests, notes):
    for i, f in enumerate(facts, 1):
        f['id'] = f'f{i}'
    for i, r in enumerate(requests, 1):
        r['rid'] = f'r{i}'
        if r['oracle'] is not None:
            EXPECTED[(cid, r['rid'])] = dict(r['oracle'])
        if not any(f.get('rid') == r['rid'] for f in facts):
            target = dict(r['target'])
            kind = 'unsupported' if r['disposition'] in ('unsupported', 'capability_gap') else 'question'
            fields = dict(target, quantity=r['quantity'], rid=r['rid'])
            if r['disposition'] == 'ambiguous':
                fields.update(ambiguous=True, reason=notes)
            if kind == 'unsupported':
                fields['reason'] = notes
            facts.append(fact(kind, r['source_quote'], role='question', **fields))
    for i, f in enumerate(facts, 1):
        f['id'] = f'f{i}'
        for quote in f['quotes']:
            assert quote in text, (cid, quote)
    for r in requests:
        assert r['source_quote'] in text
    CASES.append(dict(id=cid, split=split, structure_id=family, source_text=text,
                      n_source_requests=len(requests), entities=labels, requests=requests,
                      semantic_notes=notes))
    FACTS[cid] = dict(facts=facts)


# Development structures are intentionally distinct from the heldout contrast families.
A=(0,0,0); B=(6,0,0); C=(6,8,0); D=(0,8,0); E=(0,0,10); G=(6,8,10)
add('dev01','dev','dev_rectangular_box_diagonal',
    'Một hộp chữ nhật ABCD.EFGH có AB = 6, BC = 8, AE = 10. Tính độ dài AG và diện tích mặt ABCD.',
    list('ABCDEFGH'), [fact('solid','hộp chữ nhật ABCD.EFGH',solid='ABCD.EFGH',solid_type='cuboid'),
    fact('length','AB = 6',points=['A','B'],value='6',measure='segment'),fact('length','BC = 8',points=['B','C'],value='8',measure='segment'),fact('length','AE = 10',points=['A','E'],value='10',measure='segment')],
    [req('calculate','length',dict(points=['A','G']),'độ dài AG',numeric=length2(A,G)),req('calculate','area',dict(points=list('ABCD')),'diện tích mặt ABCD',numeric=parallelogram_area2(A,B,D))],
    'Standard corresponding vertex order of a rectangular box; two distinct requested quantities.')
O=(0,0,0); P=(2,0,0); Q=(0,3,0); R=(0,0,6)
add('dev02','dev','dev_triorthogonal_tetrahedron',
    'Tứ diện OPQR có OP, OQ, OR đôi một vuông góc; OP = 2, OQ = 3, OR = 6. Hãy tính thể tích OPQR và khoảng cách từ O đến mặt phẳng (PQR).',list('OPQR'),
    [fact('solid','Tứ diện OPQR',solid='OPQR',solid_type='tetrahedron'),fact('perpendicular','OP, OQ, OR đôi một vuông góc',points_a=['O','P'],points_b=['O','Q']),fact('perpendicular','OP, OQ, OR đôi một vuông góc',points_a=['O','P'],points_b=['O','R']),fact('perpendicular','OP, OQ, OR đôi một vuông góc',points_a=['O','Q'],points_b=['O','R'])]+[fact('length',f'O{x} = {v}',points=['O',x],value=str(v),measure='segment') for x,v in [('P',2),('Q',3),('R',6)]],
    [req('calculate','volume',dict(solid='OPQR'),'thể tích OPQR',numeric=tetra_volume2(O,P,Q,R)),req('calculate','distance',dict(points_a=['O'],points_b=list('PQR')),'khoảng cách từ O đến mặt phẳng (PQR)',numeric=plane_distance2(O,P,Q,R))],
    'All three orthogonality premises are explicit; volume is squared in oracle storage.')
A=(0,0,0); B=(4,0,0); C=(4,4,0); D=(0,4,0); S=(0,0,3)
add('dev03','dev','dev_square_corner_altitude',
    'Cho chóp S.ABCD, đáy ABCD là hình vuông cạnh 4; SA là đường cao của chóp và SA = 3. Tính diện tích tam giác SBC.',list('SABCD'),
    [fact('solid','chóp S.ABCD',solid='S.ABCD',solid_type='pyramid'),fact('polygon_shape','đáy ABCD là hình vuông cạnh 4',solid='S.ABCD',points=list('ABCD'),shape='square'),fact('length','đáy ABCD là hình vuông cạnh 4',solid='S.ABCD',points=list('ABCD'),value='4',measure='base_edge'),fact('altitude','SA là đường cao của chóp',solid='S.ABCD',points=['S','A']),fact('length','SA = 3',points=['S','A'],value='3',measure='segment')],
    [req('calculate','area',dict(points=['S','B','C']),'diện tích tam giác SBC',numeric=triangle_area2(S,B,C))],
    'Altitude ownership belongs to S.ABCD and its foot is A.')
A=(0,0,0); B=(6,0,0); C=(0,8,0); S=(0,0,5); M=midpoint(B,C)
add('dev04','dev','dev_named_midpoint_opposite_edge',
    'Trong chóp S.ABC, tam giác ABC vuông tại A, AB = 6, AC = 8. SA vuông góc (ABC), SA = 5. Gọi M là trung điểm BC. Tính SM.',list('SABCM'),
    [fact('solid','chóp S.ABC',solid='S.ABC',solid_type='pyramid'),fact('right_angle','tam giác ABC vuông tại A',points=list('ABC'),at='A'),fact('length','AB = 6',points=['A','B'],value='6',measure='segment'),fact('length','AC = 8',points=['A','C'],value='8',measure='segment'),fact('perpendicular','SA vuông góc (ABC)',points_a=['S','A'],points_b=list('ABC')),fact('length','SA = 5',points=['S','A'],value='5',measure='segment'),fact('point_def','M là trung điểm BC',point='M',point_kind='midpoint',points=['B','C'])],
    [req('calculate','length',dict(points=['S','M']),'Tính SM',numeric=length2(S,M))],
    'Named midpoint is defined by the source and retained as M.')
A=(0,0,0); B=(9,0,0); C=(0,12,0); S=(0,0,7); K=centroid(A,B,C)
add('dev05','dev','dev_unnamed_base_centroid',
    'Chóp S.ABC có đáy ABC vuông tại A, AB = 9, AC = 12, SA vuông góc đáy và SA = 7. Tính khoảng cách từ trọng tâm tam giác ABC đến mặt phẳng (SAB).',list('SABC'),
    [fact('solid','Chóp S.ABC',solid='S.ABC',solid_type='pyramid'),fact('right_angle','ABC vuông tại A',points=list('ABC'),at='A'),fact('length','AB = 9',points=['A','B'],value='9',measure='segment'),fact('length','AC = 12',points=['A','C'],value='12',measure='segment'),fact('perpendicular','SA vuông góc đáy',points_a=['S','A'],points_b=list('ABC')),fact('length','SA = 7',points=['S','A'],value='7',measure='segment')],
    [req('calculate','distance',dict(point_kind='centroid',points=list('ABC'),points_b=list('SAB')),'khoảng cách từ trọng tâm tam giác ABC đến mặt phẳng (SAB)',numeric=plane_distance2(K,S,A,B))],
    'No name is invented for the centroid; the operands are ABC.')
A=(0,0,0); B=(3,0,0); C=(0,4,0); P=(6,0,0)
add('dev06','dev','dev_extension_named_line',
    'Tam giác ABC vuông tại A có AB = 3, AC = 4. P thuộc tia AB và AP = 6. Đặt d là đường thẳng BC. Tính khoảng cách từ P đến d.',list('ABCP'),
    [fact('polygon_shape','Tam giác ABC',points=list('ABC'),shape='triangle'),fact('right_angle','ABC vuông tại A',points=list('ABC'),at='A'),fact('length','AB = 3',points=['A','B'],value='3',measure='segment'),fact('length','AC = 4',points=['A','C'],value='4',measure='segment'),fact('point_def','P thuộc tia AB và AP = 6',point='P',points=['A','B'],reason='P is on ray AB at distance 6 from A'),fact('length','AP = 6',points=['A','P'],value='6',measure='segment'),fact('intersection_line','d là đường thẳng BC',points=['B','C'],reason='The name d denotes the infinite line BC')],
    [req('calculate','distance',dict(points_a=['P'],points_b=['B','C']),'khoảng cách từ P đến d',numeric=line_distance2(P,B,C))],
    'd is an infinite line, not the finite edge BC; P lies beyond B.')
add('dev07','dev','dev_projection_construction',
    'Cho tứ diện T.ABC với TA vuông góc mặt phẳng (ABC). Hãy dựng H là hình chiếu vuông góc của B lên đường thẳng TC, rồi giải thích vì sao BH vuông góc TC.',list('TABCH'),
    [fact('solid','tứ diện T.ABC',solid='T.ABC',solid_type='tetrahedron'),fact('perpendicular','TA vuông góc mặt phẳng (ABC)',points_a=['T','A'],points_b=list('ABC')),fact('projection','dựng H là hình chiếu vuông góc của B lên đường thẳng TC',rid='r1',point='B',at='H',points=['T','C'])],
    [req('construct','projection',dict(point='B',at='H',points=['T','C']),'dựng H là hình chiếu vuông góc của B lên đường thẳng TC',disposition='capability_gap'),req('explain','perpendicular',dict(points_a=['B','H'],points_b=['T','C']),'giải thích vì sao BH vuông góc TC',disposition='capability_gap')],
    'Construction and explanation are separate obligations; definition of orthogonal projection suffices mathematically, but these are outside numerical-answer scope.')
add('dev08','dev','dev_unresolved_deictic',
    'Với hình chóp ở bài trước, tính khoảng cách từ đỉnh đó đến mặt đáy.',[],[],
    [req('calculate','distance',dict(description='Khoảng cách từ đỉnh đó đến mặt đáy của hình chóp ở bài trước'),'tính khoảng cách từ đỉnh đó đến mặt đáy',disposition='missing_source')],
    'Previous exercise and labels are absent; do not infer them from context outside this text.')
add('dev09','dev','dev_conditional_square_pyramid',
    'Cho chóp P.ABCD có đáy là hình vuông cạnh 6. Nếu PA là đường cao và PA = 4 thì hãy tính thể tích P.ABCD.',list('PABCD'),
    [fact('solid','chóp P.ABCD',solid='P.ABCD',solid_type='pyramid'),fact('polygon_shape','đáy là hình vuông cạnh 6',solid='P.ABCD',points=list('ABCD'),shape='square'),fact('length','đáy là hình vuông cạnh 6',solid='P.ABCD',points=list('ABCD'),value='6',measure='base_edge'),fact('altitude','PA là đường cao',role='condition',solid='P.ABCD',points=['P','A']),fact('length','PA = 4',role='condition',points=['P','A'],value='4',measure='segment')],
    [req('calculate','volume',dict(solid='P.ABCD'),'hãy tính thể tích P.ABCD',numeric=F(6*6*4,3)**2)],
    'The answer is conditional on the stated antecedent, not an unconditional altitude assertion.')
add('dev10','dev','dev_negated_regular_assumption',
    'Cho chóp S.ABCD có đáy ABCD là hình vuông cạnh 2 và SA = 5. Không giả sử chóp đều, cũng không biết chân đường cao. Có thể xác định duy nhất thể tích S.ABCD không?',list('SABCD'),
    [fact('solid','chóp S.ABCD',solid='S.ABCD',solid_type='pyramid'),fact('polygon_shape','đáy ABCD là hình vuông cạnh 2',solid='S.ABCD',points=list('ABCD'),shape='square'),fact('length','đáy ABCD là hình vuông cạnh 2',solid='S.ABCD',points=list('ABCD'),value='2',measure='base_edge'),fact('length','SA = 5',points=['S','A'],value='5',measure='segment'),fact('unsupported','Không giả sử chóp đều, cũng không biết chân đường cao',reason='Explicitly denies regularity as an assumption; altitude is unspecified')],
    [req('calculate','volume',dict(solid='S.ABCD'),'Có thể xác định duy nhất thể tích S.ABCD không?',disposition='missing_source')],
    'A lateral segment is not a height; no unique volume follows. Negation must not become regular=true.')
add('dev11','dev','dev_cylinder_curved_surface',
    'Một hình trụ tròn xoay có bán kính đáy 3 và chiều cao 5. Tính diện tích mặt xung quanh hình trụ.',[],
    [fact('unsupported','hình trụ tròn xoay có bán kính đáy 3 và chiều cao 5',reason='Curved cylinder lies outside the polyhedral geometry target')],
    [req('calculate','unsupported',dict(description='Diện tích mặt xung quanh hình trụ tròn xoay bán kính 3, chiều cao 5'),'Tính diện tích mặt xung quanh hình trụ',disposition='unsupported')],
    'Preserve the cylinder surface-area obligation; do not substitute a prism or silently return a polyhedral area.')
add('dev12','dev','dev_prove_not_premise',
    'Cho tứ diện ABCD. M và N lần lượt là trung điểm AB và AC. Chứng minh MN song song BC; sau đó mô phỏng việc kéo D trong khi A, B, C cố định.',list('ABCDMN'),
    [fact('solid','tứ diện ABCD',solid='ABCD',solid_type='tetrahedron'),fact('point_def','M và N lần lượt là trung điểm AB và AC',point='M',point_kind='midpoint',points=['A','B']),fact('point_def','M và N lần lượt là trung điểm AB và AC',point='N',point_kind='midpoint',points=['A','C'])],
    [req('prove','parallel',dict(points_a=['M','N'],points_b=['B','C']),'Chứng minh MN song song BC',disposition='capability_gap'),req('simulate','motion',dict(description='Kéo D với A, B, C cố định trong tứ diện ABCD'),'mô phỏng việc kéo D trong khi A, B, C cố định',disposition='capability_gap')],
    'Parallelism is the conclusion to prove, never a given. Simulation is a second request.')
