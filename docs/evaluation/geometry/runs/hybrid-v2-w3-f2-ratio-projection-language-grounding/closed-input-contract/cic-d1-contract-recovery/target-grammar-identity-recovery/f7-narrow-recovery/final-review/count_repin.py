import json,sys
d=json.load(open(sys.argv[1],encoding='utf-8'))['results']
cells=[(k,n) for k,v in d.items() if isinstance(v,dict) for n in ('a3','pl','a4') if isinstance(v.get(n),dict) and v[n].get('code')=='ADAPTER_INTERNAL_ERROR']
print(len(cells)); [print(c) for c in cells]
