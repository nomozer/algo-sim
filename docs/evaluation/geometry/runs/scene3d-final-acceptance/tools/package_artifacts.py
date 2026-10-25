"""Pin the completed development evidence package without changing existing artifacts."""
import hashlib
import json
from pathlib import Path

RUN = Path(__file__).resolve().parents[1]
ROOT = RUN.parents[4]
OUT = RUN / "artifact-manifest.json"
if OUT.exists():
    raise SystemExit("Fresh output required")
files = sorted(p for p in RUN.rglob("*") if p.is_file() and p != OUT and "__pycache__" not in p.parts)
files += [ROOT / p for p in [
    "frontend/scripts/section-role-oracle.mjs", "frontend/scripts/section-role-oracle-v2.mjs",
    "frontend/scripts/section-role-oracle-v2.node-test.mjs", "frontend/scripts/section-role-browser-probe.mjs",
    "frontend/scripts/rescore-section-roles.mjs", "frontend/scripts/scene3d-motion-probe.mjs",
    "docs/CODE_INDEX.md", "docs/EVIDENCE_INDEX.md"]]
rows = []
for p in files:
    raw = p.read_bytes()
    row = {"path": p.relative_to(ROOT).as_posix(), "bytes": len(raw), "sha256_worktree_bytes": hashlib.sha256(raw).hexdigest()}
    if p.suffix != ".png":
        row["sha256_lf_normalized"] = hashlib.sha256(raw.replace(b"\r\n", b"\n")).hexdigest()
    rows.append(row)
manifest = {"schema": "scene3d-artifact-manifest/1", "basis": "worktree raw bytes; text LF hash supplied for Git normalization; binary PNG bytes unchanged",
            "product": "b8b3311b", "candidate": "c84e8620", "human_visual_approved": "PENDING", "files": rows}
OUT.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
print(json.dumps({"files": len(rows), "bytes": sum(x["bytes"] for x in rows)}))
