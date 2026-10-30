import json, collections
h=json.load(open('corpus-head.json')); m=json.load(open('corpus-main.json')); p=json.load(open('corpus-pre.json'))
c=collections.Counter(); rows=[]
for k,v in h.items():
    if v['own_run']: continue
    for nm,b in (('main',m),('pre',p)):
        if b[k]['code'] != v['code']:
            c[(nm,b[k]['code'],v['code'])]+=1; rows.append((nm,v['file'],b[k]['code'],v['code']))
print(len(h), c)
for r in sorted(set(rows)): print(r)
json.dump(rows, open('corpus-diff.json','w'), indent=0)
