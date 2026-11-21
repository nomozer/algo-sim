# -*- coding: utf-8 -*-
"""Exposure of Holdout-7 against everything already seen (shared prior_corpus.py) — two tests:

1. string containment (the shared tool's rule, on normalised text);
2. template containment: vertex labels (uppercase tokens) → L and numbers → N on the RAW text, then normalised and
   containment again — catches "the same sentence with other labels or numbers", which string novelty does not.

usage (cwd = repo root): python check_exposure.py <manifest> <training_dir> <out.json>
"""
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, "docs/evaluation/geometry/harness/live-acceptance")
import prior_corpus as PC  # noqa: E402

man, tdir, out = Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3])
if out.exists():
    raise SystemExit(f"refusing to overwrite {out}")
cases = (lambda m: m["valid_cases"] + m["negative_cases"])(json.loads(man.read_text(encoding="utf-8")))

norm = PC.norm_text
PC.norm_text = lambda s: s  # collect the raw strings once; normalise below
raw_corpus = PC.collect(tdir)
PC.norm_text = norm
corpus = {norm(k): v for k, v in raw_corpus.items()}


def tmpl(s: str) -> str:
    s = re.sub(r"(?<![A-Za-zÀ-ỹ])[A-Z][A-Z0-9'′.]*(?![a-zà-ỹ])", "L", s)
    s = re.sub(r"\d+(?:[.,]\d+)?", "N", s)
    return norm(s)


hit = PC.exposed([c["original_input"] for c in cases], corpus)
blob_t = "\n".join(tmpl(k) for k in raw_corpus)
rows = [{"case_id": c["case_id"], "string_exposed": c["original_input"] in hit, "template_exposed": tmpl(c["original_input"]) in blob_t}
        for c in cases]
res = {"schema": "axo-holdout-exposure/1", "corpus_strings": len(corpus), "training_dir": str(tdir), "cases": len(cases),
       "string_exposed": sum(r["string_exposed"] for r in rows), "template_exposed": sum(r["template_exposed"] for r in rows),
       "string_exposed_ids": [r["case_id"] for r in rows if r["string_exposed"]],
       "template_exposed_ids": [r["case_id"] for r in rows if r["template_exposed"]], "rows": rows}
out.write_text(json.dumps(res, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
print({k: v for k, v in res.items() if k != "rows"})
