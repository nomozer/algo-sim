import copy, json, sys
sys.path.insert(0, ".")
import pytest
import tests.semantic_program.test_memory_declaration_contract_alignment as T

class MP:
    def __init__(self): self._u = []
    def setattr(self, obj, name, val=None, raising=True):
        if isinstance(obj, str):
            mod, attr = obj.rsplit(".", 1); import importlib; o = importlib.import_module(mod); val = name; name = attr; obj = o
        self._u.append((obj, name, getattr(obj, name))); setattr(obj, name, val)
    def setenv(self, k, v): import os; os.environ[k] = v
    def delenv(self, k, raising=True): import os; os.environ.pop(k, None)
    def setitem(self, d, k, v): d[k] = v
    def undo(self):
        for o, n, v in reversed(self._u): setattr(o, n, v)
mp = MP()
p1 = T._prog(T.CA_P1)
env = T._envelope(mp, T.CA_P1, [json.dumps(p1, ensure_ascii=False)])
mp.undo()
sc = env["scene3d"]
print("now", T._bam(sc))
cu = copy.deepcopy(sc)
sec = next(o for o in cu["objects"] if o["type"] == "section")
doi = []
for e in cu["events"]:
    if e["action"] == "EXTEND":
        doi.append(e["display_label"]); e["display_label"] = sec["label"]
print("labels", doi)
print("old-labels hash", T._bam(cu), "expected", T.SCENE_START[T.CA_P1])
