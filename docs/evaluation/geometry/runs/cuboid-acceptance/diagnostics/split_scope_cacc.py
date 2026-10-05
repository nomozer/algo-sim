# -*- coding: utf-8 -*-
"""cuboid-acceptance — scope of the cuboid-final-review history split after this run's edits (read-only, 0 model calls).

`split_history_cfr.py --verify` checks three things against the BASE blobs (4048ff83) of seven living docs: (1) each
moved block is verbatim in its legacy companion, its pointer stub is in the living doc and the block is gone from it;
(2) the block hashes equal `inventory/HISTORY_SPLIT.json` — only reached when (1) and (3) pass; (3) every non-blank BASE
line is still in the living doc or in the companion. (3) holds only until a later run edits a BASE line of a living
doc, which replacing a stale pointer must do. This script runs (1) and (2) on their own and splits (3): every BASE
line now in neither file must be a line that the commits START..HEAD removed from that same doc (still readable
verbatim in git at START). Run from the ROOT of the checkout under test:
  <python> <this file> <run start sha>
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
import subprocess
import sys
from pathlib import Path

START = sys.argv[1]
ROOT = Path.cwd()
TOOL = ROOT / "docs/evaluation/geometry/runs/cuboid-final-review/diagnostics/split_history_cfr.py"
spec_ = importlib.util.spec_from_file_location("split_cfr", TOOL)
cfr = importlib.util.module_from_spec(spec_)
spec_.loader.exec_module(cfr)
assert cfr.ROOT.resolve() == ROOT.resolve(), (cfr.ROOT, ROOT)

record = json.loads(cfr.RECORD.read_text(encoding="utf-8"))
bad = 0
for source, spec in cfr.specs().items():
    L = cfr.base_lines(source)
    comp = (ROOT / spec["companion"]).read_text(encoding="utf-8")
    live = (ROOT / source).read_text(encoding="utf-8")
    b1 = 0
    hashes = []
    for s, e, _reason, stub in spec["blocks"]:
        text = "".join(L[s:e])
        hashes.append(hashlib.sha256(text.encode("utf-8")).hexdigest())
        b1 += (text not in comp) + (e - s > 1 and text in live) + (stub not in live)
    b2 = hashes != [b["sha256"] for b in record["sources"][source]["blocks"]]
    present = set(live.splitlines()) | set(comp.splitlines())
    lost = [ln.rstrip("\n") for ln in L if ln.strip() and ln.rstrip("\n") not in present]
    diff = subprocess.run(["git", "diff", "--no-color", "-U0", START, "HEAD", "--", source], cwd=ROOT,
                          capture_output=True, check=True).stdout.decode("utf-8")
    removed = {ln[1:] for ln in diff.splitlines() if ln.startswith("-") and not ln.startswith("---")}
    outside = [ln for ln in lost if ln not in removed]
    bad += b1 + b2 + len(outside)
    print(f"{source}: block checks failed {b1}/{3 * len(spec['blocks'])}, block hashes differ {int(b2)}, "
          f"BASE lines in neither file {len(lost)} (removed by {START[:8]}..HEAD: {len(lost) - len(outside)}, "
          f"other: {len(outside)})")
    for ln in outside:
        print("   NOT EXPLAINED:", ln[:120])
print("SPLIT_SCOPE", "OK" if bad == 0 else "FAIL")
raise SystemExit(1 if bad else 0)
