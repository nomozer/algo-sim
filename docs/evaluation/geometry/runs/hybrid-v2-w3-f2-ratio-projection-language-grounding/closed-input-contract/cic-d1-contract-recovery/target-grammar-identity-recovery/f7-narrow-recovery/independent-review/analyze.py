import json, collections, sys
L = lambda f: json.load(open(f, encoding='utf-8'))['results']
H, R, M = L('out-head.json'), L('out-revert.json'), L('out-main.json')
INT = {'ADAPTER_INTERNAL_ERROR', 'ROUTE_INTERNAL_ERROR', 'KeyError', 'EXCEPTION'}
def bad(v): return v[0] == 'EXCEPTION' or v[1] in INT
print('== internal/exception at HEAD (schema-valid only flagged *)')
for k, v in H.items():
    for r in ('a3', 'pl', 'a4'):
        if bad(v[r]): print('*' if v['schema'] is None else ' ', k, r, v[r][:2], v[r][3][:100], '| main:', M[k][r][:2], '| 1b1a:', R[k][r][:2])
print('== HEAD vs 1b1a9ed2 diffs')
cnt = collections.Counter()
for k in H:
    for r in ('a3', 'pl', 'a4'):
        if H[k][r][:3] != R[k][r][:3]:
            cnt[(r, tuple(R[k][r][:2]), tuple(H[k][r][:2]))] += 1
for x, n in sorted(cnt.items()): print(n, x)
print('== served->refused or answer change HEAD vs revert / HEAD vs main')
for base, B in (('revert', R), ('main', M)):
    for k in H:
        for r in ('a3', 'pl', 'a4'):
            if B[k][r][0] == 'SERVED' and (H[k][r][0] != 'SERVED' or H[k][r][2] != B[k][r][2]):
                print(base, k, r, B[k][r][:3], '->', H[k][r][:3])
print('== refused with leaked answers/scene at HEAD')
for k, v in H.items():
    for r in ('a3', 'pl', 'a4'):
        if v[r][0] == 'REFUSED' and v[r][4]: print(k, r, v[r][:2])
print('== HEAD SERVED but main REFUSED (new serves)')
for k in H:
    for r in ('a3','pl','a4'):
        if H[k][r][0]=='SERVED' and M[k][r][0]!='SERVED': print(k, r, M[k][r][:2])
