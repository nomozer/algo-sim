"""Rebind the official Visual suite inputs of `visual-closure-hybrid-readiness/visual/final-inputs` to the candidate
frozen in THIS tree; never change an oracle (derived from that run's `prepare_inputs.py`, kept unchanged).

The suite renders static fixture envelopes, so a backend change cannot reach it; what must not move is checked here:
every fixture envelope, every scenario, the viewports and every suite field except the candidate identity. Writes
`<run>/visual/official-inputs/` and `<run>/official-inputs-rebinding.json`; refuses to overwrite.
"""
import hashlib
import json
import sys
from pathlib import Path

RUN = Path(__file__).resolve().parent
ROOT = RUN.parents[4]
SRC = ROOT / "docs/evaluation/geometry/runs/visual-closure-hybrid-readiness/visual/final-inputs"
NAME = sys.argv[1] if len(sys.argv) > 1 else "official-inputs"   # one fresh folder per candidate
OUT = RUN / "visual" / NAME
assert not OUT.exists(), "fresh inputs only"
cand = json.loads((ROOT / "docs/evaluation/semantic-benchmark/EVALUATION_CANDIDATE.json").read_text(encoding="utf-8"))
product, tree = cand["product_commit_sha"], cand["measured_system"]["tree_hash"]
IDENTITY = {"product_commit_sha", "product_tree_sha", "task_id"}


def write(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


OUT.mkdir(parents=True)
(OUT / "fixtures").mkdir()
manifest = json.loads((SRC / "FIXTURE_MANIFEST.json").read_text(encoding="utf-8"))
suite = json.loads((SRC / "suite.json").read_text(encoding="utf-8"))
records = []
for name, record in manifest["fixtures"].items():
    original = json.loads((SRC / "fixtures" / name).read_text(encoding="utf-8"))
    rebound = {**original, "product_commit_sha": product, "product_tree_sha": tree}
    assert {k: v for k, v in rebound.items() if k not in IDENTITY} == {k: v for k, v in original.items() if k not in IDENTITY}
    write(OUT / "fixtures" / name, rebound)
    data = (OUT / "fixtures" / name).read_bytes()
    record.update(sha256=hashlib.sha256(data).hexdigest(), bytes=len(data))
    records.append({"fixture": name, "envelope_unchanged": rebound.get("envelope") == original.get("envelope")})
assert all(r["envelope_unchanged"] for r in records)
new_suite = {**suite, "product_commit_sha": product, "product_tree_sha": tree, "task_id": RUN.name.upper().replace("-", "_")}
assert {k: v for k, v in new_suite.items() if k not in IDENTITY} == {k: v for k, v in suite.items() if k not in IDENTITY}
manifest.update(product_commit_sha=product, product_tree_sha=tree)
write(OUT / "FIXTURE_MANIFEST.json", manifest)
write(OUT / "suite.json", new_suite)
write(RUN / f"{NAME}-rebinding.json", {
    "source": str(SRC.relative_to(ROOT)).replace("\\", "/"), "product_commit_sha": product, "product_tree_sha": tree,
    "geometry_envelopes_changed": 0, "oracle_expectations_changed": 0, "suite_fields_changed": sorted(IDENTITY),
    "fixtures": records})
print(f"Rebound {len(records)} inputs to {product[:8]} / {tree[:8]}; envelopes, scenarios and oracles unchanged")
