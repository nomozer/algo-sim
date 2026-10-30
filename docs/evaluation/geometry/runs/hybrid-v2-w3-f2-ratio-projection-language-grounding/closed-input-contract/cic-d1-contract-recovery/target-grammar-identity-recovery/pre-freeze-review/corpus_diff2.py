import json, collections
h=json.load(open('corpus-head.json')); m=json.load(open('corpus-prev-emulated.json'))
c=collections.Counter(); rows=set()
for k,v in h.items():
    if m[k]['code'] != v['code']:
        c[(v['own_run'], str(m[k]['code']), str(v['code']))]+=1
        if not v['own_run']: rows.add((v['file'], str(m[k]['code']), str(v['code'])))
print(len(h), dict(c))
for r in sorted(rows): print(r)
