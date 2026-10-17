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

# Heldout family H1: a point outside an edge makes line and segment answers differ.
A=(0,0,0); B=(4,0,0); C=(4,4,0); D=(0,4,0); E=(0,0,4); Fp=(4,0,4); G=(4,4,4); H=(0,4,4); X=(8,0,0)
cube_facts=[fact('solid','lập phương ABCD.EFGH cạnh 4',solid='ABCD.EFGH',solid_type='cube'),fact('length','lập phương ABCD.EFGH cạnh 4',solid='ABCD.EFGH',value='4',measure='edge'),fact('point_def','X thuộc tia AB và AX = 8',point='X',points=['A','B'],reason='X lies on ray AB at distance 8 from A'),fact('length','AX = 8',points=['A','X'],value='8',measure='segment')]
for num, tail, request in [
    (1,'Gọi d là đường thẳng BH. Tính khoảng cách từ X đến d.',req('calculate','distance',dict(points_a=['X'],points_b=['B','H']),'khoảng cách từ X đến d',numeric=line_distance2(X,B,H))),
    (2,'Tính khoảng cách ngắn nhất từ X đến đoạn thẳng BH.',req('calculate','distance',dict(points_a=['X'],points_b=['B','H'],domain='segment'),'khoảng cách ngắn nhất từ X đến đoạn thẳng BH',numeric=segment_distance2(X,B,H))),
    (3,'So sánh khoảng cách từ X đến đường thẳng BH với khoảng cách từ X đến đoạn BH: hãy tính cả hai.',None)]:
    fs=[dict(f) for f in cube_facts]
    if num==1:
        fs.append(fact('intersection_line','d là đường thẳng BH',points=['B','H'],reason='Named infinite line'))
    rs=[request] if request else [req('calculate','distance',dict(points_a=['X'],points_b=['B','H']),'khoảng cách từ X đến đường thẳng BH',numeric=line_distance2(X,B,H)),req('calculate','distance',dict(points_a=['X'],points_b=['B','H'],domain='segment'),'khoảng cách từ X đến đoạn BH',numeric=segment_distance2(X,B,H))]
    add(f'held{num:02}','heldout','held_cube_external_line_segment','Cho lập phương ABCD.EFGH cạnh 4. X thuộc tia AB và AX = 8. '+tail,list('ABCDEFGHX'),fs,rs,'Line BH extends beyond B; the nearest point of the segment is B. Exact segment semantics must be preserved.')

# H2: regular hexagonal prism, area/volume and an unnamed midpoint.
# Use a rational affine embedding with sqrt(3) factored analytically: hex area^2=27*a^4/4.
for num, tail, rs in [
    (4,'Tính thể tích ABCDEF.A′B′C′D′E′F′.', [req('calculate','volume',dict(solid='ABCDEF.A′B′C′D′E′F′'),'thể tích ABCDEF.A′B′C′D′E′F′',numeric=F(27*2**4*5**2,4))]),
    (5,'Tính diện tích đáy ABCDEF và độ dài AA′.',[req('calculate','area',dict(points=list('ABCDEF')),'diện tích đáy ABCDEF',numeric=F(27*2**4,4)),req('calculate','length',dict(points=['A','A′']),'độ dài AA′',numeric=F(25))]),
    (6,'Tính khoảng cách từ trung điểm AA′ đến mặt phẳng (ABCDEF).',[req('calculate','distance',dict(point_kind='midpoint',points=['A','A′'],points_b=list('ABCDEF')),'khoảng cách từ trung điểm AA′ đến mặt phẳng (ABCDEF)',numeric=F(25,4))])]:
    add(f'held{num:02}','heldout','held_regular_hexagonal_prism','Lăng trụ đứng ABCDEF.A′B′C′D′E′F′ có đáy là lục giác đều cạnh 2, chiều cao bằng 5. '+tail,list('ABCDEF')+[x+'′' for x in 'ABCDEF'],
    [fact('solid','Lăng trụ đứng ABCDEF.A′B′C′D′E′F′',solid='ABCDEF.A′B′C′D′E′F′',solid_type='prism',right=True),fact('polygon_shape','đáy là lục giác đều cạnh 2',solid='ABCDEF.A′B′C′D′E′F′',points=list('ABCDEF'),shape='regular_hexagon'),fact('length','đáy là lục giác đều cạnh 2',solid='ABCDEF.A′B′C′D′E′F′',points=list('ABCDEF'),value='2',measure='base_edge'),fact('length','chiều cao bằng 5',solid='ABCDEF.A′B′C′D′E′F′',value='5',measure='height')],rs,
    'Rightness and base shape are independent properties. Six-label plane denotes the entire base; unnamed midpoint receives no fabricated label.')

# H3: multiple solids whose base and altitude ownership must not leak.
common='Hai khối chóp P.ABCD và Q.EFGH có đáy ABCD là hình chữ nhật với AB = 3, BC = 4; đáy EFGH là hình vuông cạnh 6. PA là đường cao của P.ABCD, PA = 8; QE là đường cao của Q.EFGH, QE = 2. '
multi_facts=[fact('solid','chóp P.ABCD',solid='P.ABCD',solid_type='pyramid'),fact('solid','Q.EFGH',solid='Q.EFGH',solid_type='pyramid'),fact('polygon_shape','đáy ABCD là hình chữ nhật',solid='P.ABCD',points=list('ABCD'),shape='rectangle'),fact('polygon_shape','đáy EFGH là hình vuông cạnh 6',solid='Q.EFGH',points=list('EFGH'),shape='square'),fact('length','AB = 3',points=['A','B'],value='3',measure='segment'),fact('length','BC = 4',points=['B','C'],value='4',measure='segment'),fact('length','hình vuông cạnh 6',solid='Q.EFGH',points=list('EFGH'),value='6',measure='base_edge'),fact('altitude','PA là đường cao của P.ABCD',solid='P.ABCD',points=['P','A']),fact('altitude','QE là đường cao của Q.EFGH',solid='Q.EFGH',points=['Q','E']),fact('length','PA = 8',points=['P','A'],value='8',measure='segment'),fact('length','QE = 2',points=['Q','E'],value='2',measure='segment')]
for num, tail, rs in [
    (7,'Tính thể tích của từng khối chóp.',[req('calculate','volume',dict(solid='P.ABCD'),'thể tích của từng khối chóp',numeric=F(32)**2),req('calculate','volume',dict(solid='Q.EFGH'),'thể tích của từng khối chóp',numeric=F(24)**2)]),
    (8,'Chỉ tính thể tích Q.EFGH; không tính thể tích P.ABCD.',[req('calculate','volume',dict(solid='Q.EFGH'),'Chỉ tính thể tích Q.EFGH',numeric=F(24)**2)]),
    (9,'Giải thích vì sao không được dùng PA làm chiều cao của Q.EFGH; tính diện tích EFGH.',[req('explain','unsupported',dict(description='Vì sao PA không phải chiều cao của Q.EFGH'),'Giải thích vì sao không được dùng PA làm chiều cao của Q.EFGH',disposition='capability_gap'),req('calculate','area',dict(points=list('EFGH')),'tính diện tích EFGH',numeric=F(36)**2)])]:
    add(f'held{num:02}','heldout','held_two_pyramids_ownership',common+tail,list('PABCDQEFGH'),[dict(f) for f in multi_facts],rs,'All dimensions belong to the explicitly named solid. In held08 the negative command excludes a P.ABCD request. For the rectangle, consecutive edge order follows the listed sides.')

# H4: centroid and midpoint on a non-right tetrahedron with a rectangular-base embedding.
A=(0,0,0); B=(6,0,0); C=(0,6,0); T=(3,3,6); M=midpoint(A,B); N=centroid(A,B,C)
common='Tứ diện TABC có tam giác ABC vuông cân tại A, AB = AC = 6. O là trung điểm BC; TO vuông góc (ABC) và TO = 6. '
tf=[fact('solid','Tứ diện TABC',solid='TABC',solid_type='tetrahedron'),fact('right_angle','tam giác ABC vuông cân tại A',points=list('ABC'),at='A'),fact('equal_lengths','AB = AC = 6',points_a=['A','B'],points_b=['A','C']),fact('length','AB = AC = 6',points=['A','B'],value='6',measure='segment'),fact('length','AB = AC = 6',points=['A','C'],value='6',measure='segment'),fact('point_def','O là trung điểm BC',point='O',point_kind='midpoint',points=['B','C']),fact('perpendicular','TO vuông góc (ABC)',points_a=['T','O'],points_b=list('ABC')),fact('length','TO = 6',points=['T','O'],value='6',measure='segment')]
add('held10','heldout','held_tetra_barycentric_targets',common+'M là trung điểm AB. Tính TM.',list('TABCOM'),[dict(f) for f in tf]+[fact('point_def','M là trung điểm AB',point='M',point_kind='midpoint',points=['A','B'])],[req('calculate','length',dict(points=['T','M']),'Tính TM',numeric=length2(T,M))],'Named edge midpoint in a tetrahedron whose altitude foot is the opposite-edge midpoint.')
add('held11','heldout','held_tetra_barycentric_targets',common+'Tính khoảng cách từ trung điểm AB đến đường thẳng TO.',list('TABCO'),[dict(f) for f in tf],[req('calculate','distance',dict(point_kind='midpoint',points=['A','B'],points_b=['T','O']),'khoảng cách từ trung điểm AB đến đường thẳng TO',numeric=line_distance2(M,T,(3,3,0)))],'Unnamed midpoint uses AB operands, not an invented M.')
add('held12','heldout','held_tetra_barycentric_targets',common+'G là trọng tâm tam giác ABC. Tính TG và thể tích TABC.',list('TABCOG'),[dict(f) for f in tf]+[fact('point_def','G là trọng tâm tam giác ABC',point='G',point_kind='centroid',points=list('ABC'))],[req('calculate','length',dict(points=['T','G']),'Tính TG',numeric=length2(T,N)),req('calculate','volume',dict(solid='TABC'),'thể tích TABC',numeric=tetra_volume2(A,B,C,T))],'Centroid and altitude foot O differ; do not collapse them.')

# H5: oblique triangular prism: lateral edge is NOT height.
A=(0,0,0); B=(4,0,0); C=(0,3,0); Ap=(3,0,4); Bp=(7,0,4); Cp=(3,3,4)
common='Lăng trụ ABC.A′B′C′ có đáy ABC vuông tại A, AB = 4, AC = 3. Hình chiếu vuông góc của A′ lên (ABC) là H nằm trên đoạn AB, AH = 3; A′H = 4. '
pf=[fact('solid','Lăng trụ ABC.A′B′C′',solid='ABC.A′B′C′',solid_type='prism'),fact('right_angle','đáy ABC vuông tại A',points=list('ABC'),at='A'),fact('length','AB = 4',points=['A','B'],value='4',measure='segment'),fact('length','AC = 3',points=['A','C'],value='3',measure='segment'),fact('projection','Hình chiếu vuông góc của A′ lên (ABC) là H',point='A′',at='H',points=list('ABC')),fact('point_def','H nằm trên đoạn AB, AH = 3',point='H',points=['A','B'],reason='H lies on segment AB at distance 3 from A'),fact('length','AH = 3',points=['A','H'],value='3',measure='segment'),fact('length','A′H = 4',points=['A′','H'],value='4',measure='segment')]
for num, tail, rs in [
    (13,'Tính cạnh bên AA′ và thể tích ABC.A′B′C′.',[req('calculate','length',dict(points=['A','A′']),'cạnh bên AA′',numeric=length2(A,Ap)),req('calculate','volume',dict(solid='ABC.A′B′C′'),'thể tích ABC.A′B′C′',numeric=prism_volume2(A,B,C,Ap))]),
    (14,'Tính góc giữa AA′ và (ABC).',[req('calculate','angle',dict(points_a=['A','A′'],points_b=list('ABC')),'góc giữa AA′ và (ABC)',numeric=angle_cos2(A,Ap,A,B,C),cosine=True)]),
    (15,'Tính diện tích mặt bên ABB′A′.',[req('calculate','area',dict(points=['A','B','B′','A′']),'diện tích mặt bên ABB′A′',numeric=parallelogram_area2(A,B,Ap))])]:
    add(f'held{num:02}','heldout','held_oblique_prism_edge_height',common+tail,['A','B','C','A′','B′','C′','H'],[dict(f) for f in pf],rs,'Projection data fixes an oblique prism. AA′=5 while prism height=4; do not infer right=true.')

# H6: complete four-label planes and a section polygon.
A=(0,0,0); B=(6,0,0); C=(6,6,0); D=(0,6,0); E=(0,0,6); Fp=(6,0,6); G=(6,6,6); H=(0,6,6)
common='Cho lập phương ABCD.EFGH có cạnh 6. '
cf=[fact('solid','lập phương ABCD.EFGH có cạnh 6',solid='ABCD.EFGH',solid_type='cube'),fact('length','lập phương ABCD.EFGH có cạnh 6',solid='ABCD.EFGH',value='6',measure='edge')]
for num, tail, rs in [
    (16,'Tính khoảng cách từ B đến mặt phẳng (ACGE).',[req('calculate','distance',dict(points_a=['B'],points_b=list('ACGE')),'khoảng cách từ B đến mặt phẳng (ACGE)',numeric=plane_distance2(B,A,C,G))]),
    (17,'Tính cos² của góc giữa AG và mặt phẳng (ABFE).',[req('calculate','angle',dict(points_a=['A','G'],points_b=list('ABFE')),'cos² của góc giữa AG và mặt phẳng (ABFE)',numeric=angle_cos2(A,G,A,B,Fp),cosine=True)]),
    (18,'Mặt phẳng (ACGE) cắt khối lập phương theo tứ giác ACGE. Tính diện tích thiết diện đó.',[req('calculate','area',dict(solid='ABCD.EFGH',points=list('ACGE')),'diện tích thiết diện đó',numeric=parallelogram_area2(A,C,E))])]:
    fs=[dict(f) for f in cf]
    if num==18:
        fs.append(fact('section','Mặt phẳng (ACGE) cắt khối lập phương theo tứ giác ACGE',solid='ABCD.EFGH',points=list('ACGE')))
    add(f'held{num:02}','heldout','held_cube_four_label_planes',common+tail,list('ABCDEFGH'),fs,rs,'All four source plane labels must survive extraction. For the angle the oracle stores cos squared, not the angle in degrees.')

# H7: separate clauses, intersection definitions, construction and interaction requests.
common='Cho chóp V.KLMN với đáy KLMN là hình chữ nhật, KL = 8, LM = 6, VK vuông góc (KLMN), VK = 4. I là giao điểm KM và LN. '
vf=[fact('solid','chóp V.KLMN',solid='V.KLMN',solid_type='pyramid'),fact('polygon_shape','đáy KLMN là hình chữ nhật',solid='V.KLMN',points=list('KLMN'),shape='rectangle'),fact('length','KL = 8',points=['K','L'],value='8',measure='segment'),fact('length','LM = 6',points=['L','M'],value='6',measure='segment'),fact('perpendicular','VK vuông góc (KLMN)',points_a=['V','K'],points_b=list('KLMN')),fact('length','VK = 4',points=['V','K'],value='4',measure='segment'),fact('point_def','I là giao điểm KM và LN',point='I',point_kind='intersect_line_line',points_a=['K','M'],points_b=['L','N'])]
K=(0,0,0); L=(8,0,0); M=(8,6,0); N=(0,6,0); V=(0,0,4); I=(4,3,0)
add('held19','heldout','held_rectangle_intersection_workflow',common+'Dựng J là hình chiếu của I lên VK; tính VI.',list('VKLMNIJ'),[dict(f) for f in vf]+[fact('projection','Dựng J là hình chiếu của I lên VK',rid='r1',point='I',at='J',points=['V','K'])],[req('construct','projection',dict(point='I',at='J',points=['V','K']),'Dựng J là hình chiếu của I lên VK',disposition='capability_gap'),req('calculate','length',dict(points=['V','I']),'tính VI',numeric=length2(V,I))],'Projection construction and a computable segment must remain separate requests.')
add('held20','heldout','held_rectangle_intersection_workflow',common+'Tính thể tích V.KLMN. Cho phép người xem xoay mô hình quanh VK và giải thích I nằm ở đâu trong đáy.',list('VKLMNI'),[dict(f) for f in vf],[req('calculate','volume',dict(solid='V.KLMN'),'Tính thể tích V.KLMN',numeric=F(8*6*4,3)**2),req('interact','motion',dict(description='Người xem xoay mô hình quanh VK'),'Cho phép người xem xoay mô hình quanh VK',disposition='capability_gap'),req('explain','point_location',dict(point='I',points=list('KLMN')),'giải thích I nằm ở đâu trong đáy',disposition='capability_gap')],'Three explicit obligations; the interactive command is not a numerical angle question.')
add('held21','heldout','held_rectangle_intersection_workflow',common+'Nếu U là giao điểm của đường thẳng VI với mặt phẳng (KLMN), hãy dựng U rồi chứng minh U trùng I.',list('VKLMNIU'),[dict(f) for f in vf]+[fact('point_def','U là giao điểm của đường thẳng VI với mặt phẳng (KLMN)',role='condition',point='U',point_kind='intersect_line_plane',points_a=['V','I'],points_b=list('KLMN'))],[req('construct','intersection',dict(point='U',points_a=['V','I'],points_b=list('KLMN')),'hãy dựng U',disposition='capability_gap'),req('prove','coincidence',dict(points=['U','I']),'chứng minh U trùng I',disposition='capability_gap')],'Conditional intersection definition must keep its role; the requested coincidence is not a premise.')

# H8: abstention contrasts without fabricated inputs or contradictory repair.
add('held22','heldout','held_abstention_boundary',
    'Cho lăng trụ đứng ABC.A′B′C′, đáy ABC là tam giác đều cạnh 4. Tính thể tích lăng trụ.', ['A','B','C','A′','B′','C′'],
    [fact('solid','lăng trụ đứng ABC.A′B′C′',solid='ABC.A′B′C′',solid_type='prism',right=True),fact('polygon_shape','đáy ABC là tam giác đều cạnh 4',solid='ABC.A′B′C′',points=list('ABC'),shape='equilateral_triangle'),fact('length','đáy ABC là tam giác đều cạnh 4',solid='ABC.A′B′C′',points=list('ABC'),value='4',measure='base_edge')],
    [req('calculate','volume',dict(solid='ABC.A′B′C′'),'Tính thể tích lăng trụ',disposition='missing_source')],
    'Base area is fixed but prism height is absent; right prism does not mean all edges equal.')
add('held23','heldout','held_abstention_boundary',
    'Hai chóp S.ABC và T.DEF có đáy là tam giác đều cạnh 3; mỗi chóp đều có chiều cao 4. Tính thể tích của chóp đó.',list('SABCTDEF'),
    [fact('solid','chóp S.ABC',solid='S.ABC',solid_type='pyramid'),fact('solid','T.DEF',solid='T.DEF',solid_type='pyramid')]+[f for solid, pts in [('S.ABC',list('ABC')),('T.DEF',list('DEF'))] for f in [fact('polygon_shape','đáy là tam giác đều cạnh 3',solid=solid,points=pts,shape='equilateral_triangle'),fact('length','đáy là tam giác đều cạnh 3',solid=solid,points=pts,value='3',measure='base_edge'),fact('length','mỗi chóp đều có chiều cao 4',solid=solid,value='4',measure='height')]],
    [req('calculate','volume',dict(description='Thể tích của chóp đó: S.ABC hoặc T.DEF'),'Tính thể tích của chóp đó',disposition='ambiguous')],
    'The singular deictic target has two equally salient solids even though their numeric volumes happen to coincide. The adverb đều means each, not regular pyramid.')
add('held24','heldout','held_abstention_boundary',
    'Cho chóp Z.ABCD có đáy ABCD là hình vuông. Gọi đường cong c là giao tuyến của mặt cầu tâm Z với mặt phẳng (ABCD). Hãy dựng c và tính độ dài c.',list('ZABCD'),
    [fact('solid','chóp Z.ABCD',solid='Z.ABCD',solid_type='pyramid'),fact('polygon_shape','đáy ABCD là hình vuông',solid='Z.ABCD',points=list('ABCD'),shape='square'),fact('unsupported','đường cong c là giao tuyến của mặt cầu tâm Z với mặt phẳng (ABCD)',reason='Sphere-plane curved intersection, radius absent')],
    [req('construct','unsupported',dict(description='Đường cong c là giao tuyến mặt cầu tâm Z với mặt phẳng ABCD'),'Hãy dựng c',disposition='unsupported'),req('calculate','unsupported',dict(description='Độ dài đường cong c là giao tuyến mặt cầu tâm Z với mặt phẳng ABCD'),'tính độ dài c',disposition='unsupported')],
    'Preserve both curved-intersection obligations; no sphere radius is supplied and no polygonal approximation is permitted.')


def verify():
    corpus = json.loads((ROOT/'corpus.json').read_text(encoding='utf-8'))
    assert corpus['schema'] == 'semantic-extraction-corpus/2'
    assert corpus['independence'] == 'INDEPENDENT_AI_AUTHORED_NOT_HUMAN_VALIDATED'
    assert len(corpus['cases']) == 36
    observed = {}
    for case in corpus['cases']:
        assert case['n_source_requests'] == len(case['requests'])
        for request in case['requests']:
            if request['oracle'] is not None:
                observed[(case['id'],request['rid'])] = request['oracle']
    assert observed == EXPECTED, 'Numeric mismatch or missing independent oracle'
    split_families = {}
    for case in corpus['cases']:
        old = split_families.setdefault(case['structure_id'], case['split'])
        assert old == case['split'], 'Related structures cross split boundary'
    assert sum(c['split']=='dev' for c in corpus['cases']) == 12
    assert sum(c['split']=='heldout' for c in corpus['cases']) == 24
    print(json.dumps({'cases':len(corpus['cases']), 'requests':sum(c['n_source_requests'] for c in corpus['cases']), 'numeric_requests':len(observed), 'dev':12, 'heldout':24, 'families':len(split_families)}, sort_keys=True))


def author():
    (ROOT/'corpus.json').write_text(json.dumps(dict(schema='semantic-extraction-corpus/2',independence='INDEPENDENT_AI_AUTHORED_NOT_HUMAN_VALIDATED',cases=CASES),ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    (ROOT/'gold_facts.json').write_text(json.dumps(dict(cases=FACTS),ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    note = '''# Independent authoring record

Status: INDEPENDENT_AI_AUTHORED_NOT_HUMAN_VALIDATED.

The author received only the task instructions and schema. The author did not read repository files, existing corpora, extraction prompts, engine code, prior outputs, or model results, and made no network or provider calls. New files were written only in this inputs directory. This is independent AI authorship, not human validation or independent human ground truth.

The development split contains 12 single-case structure families: rectangular-box diagonal, triorthogonal tetrahedron, corner-altitude square pyramid, named opposite-edge midpoint, unnamed base centroid, named infinite line beyond an edge, projection construction, unresolved prior-exercise context, conditional volume, explicitly absent regularity/height, curved cylinder, and proof plus simulation.

The 24 fresh heldout cases comprise eight three-case families. held01–03 contrast infinite line versus finite segment with an external point; held04–06 cover regular hexagonal right-prism quantities; held07–09 isolate two-solid base/height ownership and negative commands; held10–12 contrast named/unnamed midpoint and centroid in an altitude-foot tetrahedron; held13–15 use an oblique prism to distinguish lateral edge from height; held16–18 preserve four-label planes and section polygons; held19–21 separate construction/calculation/interaction/explanation/conditional proof; held22–24 cover absent height, deictic ambiguity despite equal numerical answers, and unsupported curved intersections. Every related contrast or paraphrase stays inside its split. Concept vocabulary overlaps by design; concrete construction families do not cross the split.

Oracles are squared values for length, distance, area and volume, and squared cosines for line-plane angles. All arithmetic uses Python stdlib Fraction. Independent explicit coordinates establish Euclidean metric quantities; triangle areas use cross products, volumes use determinants, infinite-line and plane distances use projections, and finite-segment distance clamps the projection parameter. The regular hexagon is decomposed into six equilateral triangles; its squared area is 27*a^4/4, an exact rational identity. No floating-point approximation or engine behavior is used. Non-numeric, unsupported, ambiguous and missing-source requests have null oracle. Construction/explanation/proof/interaction/simulation are annotated capability_gap to preserve their obligation without claiming numerical engine support.

Gold facts preserve literal source quotations, premise/condition/question roles, source labels, explicit solid ownership, and annotation-only request IDs. Named definitions retain their source names; unnamed midpoints/centroids introduce none. Plane operands retain all supplied labels. A segment carries domain=segment. A solid volume's source symbol is always retained. Explicit negatives do not create positive facts; comparative requests are decomposed into separately addressable quantities. Fractions are exact strings; oracle values are never asserted for missing information. No coordinates appear in gold facts.

The oracle verifier reads only the newly authored corpus.json, computes all numeric results independently from its own Fraction constructions, verifies counts and split-family separation, and compares every numeric result. Parent review is deferred until prompt freeze; no heldout source text was sent in the completion message.
'''
    (ROOT/'authoring.md').write_text(note, encoding='utf-8')


if __name__ == '__main__':
    if '--author' in sys.argv:
        author()
    verify()
    for filename in ('corpus.json','gold_facts.json','oracle.py','authoring.md'):
        print(filename, hashlib.sha256((ROOT/filename).read_bytes()).hexdigest())
