import sys, json; sys.path.insert(0, sys.argv[1])
from harness import *
for fid, p in fixtures():
    r = run3(p)
    print(fid, json.dumps(r), "| solids=", [(s["solid_id"], s.get("solid_type","pyramid"), s["notation"], bool(s.get("vertex_bindings"))) for s in p["solids"]])
