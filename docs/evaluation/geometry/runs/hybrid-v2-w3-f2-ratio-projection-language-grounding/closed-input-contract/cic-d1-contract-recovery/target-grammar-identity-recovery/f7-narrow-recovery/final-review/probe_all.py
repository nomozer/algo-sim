import sys, json, collections
sys.dont_write_bytecode=True
T=r'D:/Documents/projects/algo-sim/.superpowers/worktrees/w3-f2-f7-final-t3-4e7fe91d'; TG=r'D:/Documents/projects/algo-sim/.superpowers/worktrees/w3-f2-f7-final-t3-4e7fe91d/docs/evaluation/geometry/runs/hybrid-v2-w3-f2-ratio-projection-language-grounding/closed-input-contract/cic-d1-contract-recovery/target-grammar-identity-recovery'
sys.path[:0]=[T+'/backend', TG+'/tools']
from observe import observe   # blocks sockets on import
import socket
try:
    socket.create_connection(('127.0.0.1',9)); print('SOCKET NOT BLOCKED')
except RuntimeError as e: print('socket blocked:', e)
tot=collections.Counter(); bad=[]
for src in (TG+'/cases.json', TG+'/f7-narrow-recovery/cases.json'):
    C=json.load(open(src,encoding='utf-8'))
    C = C['cases'] if 'cases' in C else C
    it = C.items() if isinstance(C,dict) else [(c.get('id'),c) for c in C]
    for k,c in it:
        p=c.get('payload')
        if not isinstance(p,dict): continue
        o=observe(p)
        for n in ('a3','pl','a4'):
            st,code=o[n]['status'],o[n]['code']; tot[(n,st)]+=1
            if st=='EXCEPTION' or code in ('ADAPTER_INTERNAL_ERROR','ROUTE_INTERNAL_ERROR'): bad.append((src[-30:],k,n,st,code))
print(dict(tot)); print('internal/exception:',len(bad)); [print(b) for b in bad[:20]]
