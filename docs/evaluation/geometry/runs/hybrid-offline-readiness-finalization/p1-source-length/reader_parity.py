# Reader parity: run with PYTHONPATH=<backend of the tree under test>. Reads every committed problem text in the repo
# corpora and prints, per text, what the source readers derive. Same input list for both trees.
# usage: python reader_parity.py <repoRootForCorpora> <out.jsonl>
import json, pathlib, subprocess, sys
from types import SimpleNamespace

from app.simulation.semantic_program.segment_relation import do_dai_trong_de
from app.simulation.semantic_program.refusal_cause import do_dai_de_ghi_khong_duong
from app.simulation.semantic_program.shape_constraint import phan_chua_doc

root, out = pathlib.Path(sys.argv[1]), sys.argv[2]
KEYS = {"problem_text", "text", "de", "problem", "de_bai", "source_text", "input_text", "question"}
files = subprocess.run(["git", "-C", str(root), "ls-files", "*.json"], capture_output=True, text=True).stdout.split()
texts = set()

def walk(o):
    if isinstance(o, dict):
        for k, v in o.items():
            if k in KEYS and isinstance(v, str) and 8 <= len(v) <= 4000 and any(c.isupper() for c in v):
                texts.add(v)
            walk(v)
    elif isinstance(o, list):
        for v in o:
            walk(v)

for f in files:
    p = root / f
    if p.stat().st_size > 30_000_000:
        continue
    try:
        walk(json.loads(p.read_text(encoding="utf-8")))
    except Exception:
        pass

with open(out, "w", encoding="utf-8") as fh:
    for t in sorted(texts):
        r = do_dai_de_ghi_khong_duong(SimpleNamespace(problem_text=t))
        fh.write(json.dumps({
            "text": t,
            "lengths": sorted(("".join(sorted(k)), str(v)) for k, v in do_dai_trong_de(t).items()),
            "nonpositive": r and {"subjects": r["reason_subjects"], "cause": r["refusal_cause"]},
            "unread": list(phan_chua_doc(t)),
        }, ensure_ascii=False, sort_keys=True) + "\n")
print(len(texts), "texts")
