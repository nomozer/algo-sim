import json,sys
base=sys.argv[1]
cases=json.load(open(base+'/cases.json',encoding='utf-8'))
d=json.load(open(base+'/observed-red.json',encoding='utf-8'))['results']
cs = cases['cases'] if isinstance(cases,dict) and 'cases' in cases else cases
items = cs.items() if isinstance(cs,dict) else [(c.get('id') or c.get('name'),c) for c in cs]
ctrl=[k for k,c in items if c.get('class') in ('CONTROL','IDENTITY_CONTROL')]
cells=[(k,n) for k in ctrl for n in ('a3','pl','a4') if d.get(k,{}).get(n,{}).get('code')=='ADAPTER_INTERNAL_ERROR']
print(len(ctrl),'controls;',len(cells),'remapped cells'); [print(c) for c in cells]
