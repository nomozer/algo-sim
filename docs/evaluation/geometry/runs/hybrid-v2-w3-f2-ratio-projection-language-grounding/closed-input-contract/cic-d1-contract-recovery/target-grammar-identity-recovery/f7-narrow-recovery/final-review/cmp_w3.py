import json,sys
a=json.load(open(sys.argv[1],encoding='utf-8')); b=json.load(open(sys.argv[2],encoding='utf-8'))
print('identity committed', a['identity']); print('identity mine', b['identity'])
for k in set(a)|set(b):
    if k in ('identity','task'): continue
    if a.get(k)!=b.get(k): print('DIFF key', k)
print('cases equal', a['cases']==b['cases'], len(a['cases']))
