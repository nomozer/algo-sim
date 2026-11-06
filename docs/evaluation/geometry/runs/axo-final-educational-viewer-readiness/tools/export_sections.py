"""Export existing independent-oracle-checked /4 sections for presenter regression; no provider."""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[6]
sys.path.insert(0, str(ROOT / "backend"))
from tests.geometry import test_hybrid4_three_point_plane_sections as T

rows = []
for name, build in T.SERVED_CASES.items():
    solid, prem, plane, vertices, edges, plane_xyz = build()
    env, route = T.run(solid, prem, plane)
    assert route["status"] == "SERVED", name
    oracle = T.oracle_section(vertices, edges, plane_xyz)
    section = next(o for o in env["scene3d"]["objects"] if o["type"] == "section")
    assert len(section["polygon"]) == oracle["vertices"]
    rows.append({"id": name, "scene": env["scene3d"]})
out = Path(__file__).resolve().parents[1] / "section-fixtures.json"
assert not out.exists(), "fresh output required"
out.write_text(json.dumps(rows, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(json.dumps({"scenes": len(rows), "vertex_counts": sorted({len(o["polygon"]) for r in rows for o in r["scene"]["objects"] if o["type"] == "section"}), "provider_calls": 0}))
