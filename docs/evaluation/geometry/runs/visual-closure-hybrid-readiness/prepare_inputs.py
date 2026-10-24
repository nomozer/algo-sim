"""Rebind existing official inputs to a frontend-only candidate; never change an oracle."""
import hashlib
import json
import subprocess
import sys
from pathlib import Path

RUN = Path(__file__).resolve().parent
ROOT = RUN.parents[4]
OLD = RUN.parent / "visual-hybrid-final-corrections" / "visual" / "inputs"
OUT = RUN / "visual" / (sys.argv[1] if len(sys.argv) > 1 else "inputs")
assert not OUT.exists(), "Fresh inputs only"
candidate = json.loads((ROOT / "docs/evaluation/semantic-benchmark/EVALUATION_CANDIDATE.json").read_text(encoding="utf-8"))
product = candidate["product_commit_sha"]
tree = candidate["measured_system"]["tree_hash"]
assert subprocess.check_output(["git", "diff", "1a4a0b93", "--name-only", "--", "backend/app"], cwd=ROOT).strip() == b""
OUT.mkdir(parents=True)
(OUT / "fixtures").mkdir()
def write(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
def sha(data):
    return hashlib.sha256(data).hexdigest()
manifest = json.loads((OLD / "FIXTURE_MANIFEST.json").read_text(encoding="utf-8"))
suite = json.loads((OLD / "suite.json").read_text(encoding="utf-8"))
records = []
for name, record in manifest["fixtures"].items():
    original = json.loads((OLD / "fixtures" / name).read_text(encoding="utf-8"))
    rebound = {**original, "product_commit_sha": product, "product_tree_sha": tree}
    assert rebound.get("envelope") == original.get("envelope")
    write(OUT / "fixtures" / name, rebound)
    data = (OUT / "fixtures" / name).read_bytes()
    record.update(sha256=sha(data), bytes=len(data))
    records.append({"fixture": name, "envelope_unchanged": True})
manifest.update(product_commit_sha=product, product_tree_sha=tree)
suite.update(product_commit_sha=product, product_tree_sha=tree, task_id="VISUAL_CLOSURE_HYBRID_READINESS")
write(OUT / "FIXTURE_MANIFEST.json", manifest)
write(OUT / "suite.json", suite)
old_suite = json.loads((OLD / "suite.json").read_text(encoding="utf-8"))
assert suite["scenarios"] == old_suite["scenarios"]
assert suite["viewports"] == old_suite["viewports"]
write(RUN / ("input-rebinding.json" if OUT.name == "inputs" else f"{OUT.name}-rebinding.json"), {"source": str(OLD.relative_to(ROOT)), "product": product,
    "geometry_envelopes_changed": 0, "oracle_expectations_changed": 0, "fixtures": records})
print(f"Rebound {len(records)} inputs; geometry and oracle unchanged")
