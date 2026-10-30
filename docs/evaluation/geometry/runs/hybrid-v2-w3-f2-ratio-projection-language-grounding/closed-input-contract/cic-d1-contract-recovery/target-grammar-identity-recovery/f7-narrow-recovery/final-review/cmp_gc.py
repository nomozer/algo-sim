import json,sys
for n in ('gate-c.json','probes203.json'):
    a=json.load(open(sys.argv[1]+'/'+n,encoding='utf-8')); b=json.load(open(sys.argv[2]+'/mine-'+n,encoding='utf-8'))
    print(n, 'committed head', a['head'][:8], 'mine', b['head'][:8], 'cases equal', a['cases']==b['cases'], {k:(a[k],b[k]) for k in a if k not in ('cases','head') and a[k]!=b[k]})
