"""Read-only capability probe at the preregistered expansion base. No provider imports/calls."""
from __future__ import annotations

import copy
import json
import sys
from collections import Counter
from fractions import Fraction as F
from pathlib import Path

ROOT = Path(__file__).resolve().parents[6]
sys.path.insert(0, str(ROOT / "backend"))

from app.ai.function_route import run_function_route
from app.simulation.geometry import kernel as K, metric
from app.simulation.geometry.exact import Line3, Plane3, Vec3
from app.simulation.geometry_functions.registry import REGISTRY, TuChoi, doc_ke_hoach


def main() -> None:
    fixtures = ROOT / "backend/tests/geometry/fixtures"
    base = json.loads((fixtures / "geometry_expansion_cases.json").read_text(encoding="utf8"))["cases"][0]
    initial = run_function_route(base["text"], {"calls": base["calls"]})
    assert initial.status == "SERVED"

    # This foot is unique. Independent Gram algebra: plane x+z=1; G=diag(1,1,2),
    # D=(0,1,0); signed value=-1, dual normal=(1,0,1/2), norm squared=3/2.
    gram = metric.Metric(((F(1), F(0), F(0)), (F(0), F(1), F(0)), (F(0), F(0), F(2))))
    with metric.using(gram):
        foot = K.project_point_onto_plane(Vec3.of(0, 1, 0), Plane3(Vec3.of(1, 0, 0), Vec3.of(1, 0, 1)))
        assert foot == Vec3.of(F(2, 3), 1, F(1, 3))
        line_foot = K.project_point_onto_line(Vec3.of(0, 1, 0), Line3(Vec3.of(0, 0, 0), Vec3.of(1, 1, 0)))
        assert line_foot == Vec3.of(F(1, 2), F(1, 2), 0)

    q = "H là hình chiếu vuông góc của D lên (SBC)"
    calls = copy.deepcopy(base["calls"])
    calls.append({"id": "projection_probe", "fn": "orthogonal_projection",
                  "args": {"point": "D", "plane": ["S", "B", "C"], "image": "H"},
                  "source": {"quote": q}})
    result = run_function_route(base["text"] + " " + q + ".", {"calls": calls})
    assert result.status == "REFUSED" and result.code == "UNDERDETERMINED_POINT"

    missing = ["intersect_line_line", "intersect_line_plane", "intersect_plane_plane", "construct_section",
               "project_point_onto_line", "rhombus", "trapezoid", "divide_segment"]
    for name in missing:
        assert name not in REGISTRY
        try:
            doc_ke_hoach({"calls": [{"id": "probe", "fn": name, "args": {}, "source": {"quote": "probe"}}]})
        except TuChoi as exc:
            assert exc.code == "SCHEMA_INVALID"
        else:
            raise AssertionError(name)

    frozen = ROOT / "docs/evaluation/geometry/runs/hybrid-ab-pilot-readiness/fake-provider/verified/FULL_AB/manifest.json"
    manifest = json.loads(frozen.read_text(encoding="utf8"))
    scenes = [r for r in manifest["rows"] if r["sample"] == 1 and r["route"].get("scene3d")]
    unbound = [(r["case_id"], r["arm"], d) for r in scenes
               for d in r["route"]["scene3d"].get("diagnostics", []) if str(d).startswith("ANNOTATION_UNBOUND")]
    print(json.dumps({"schema": "geometry_capability_probe/1", "registry_count": len(REGISTRY),
                      "registry": sorted(REGISTRY), "missing_library_entries": missing,
                      "unique_projection": {"kernel_matches_independent_foot": True,
                                            "plane_foot_chart": ["2/3", "1", "1/3"],
                                            "line_foot_chart": ["1/2", "1/2", "0"],
                                            "function_route_status": result.status, "function_route_code": result.code},
                      "annotation_audit": {"scope": "frozen fake FULL sample1 only; no rerun",
                                           "served_scenes": len(scenes), "unbound_count": len(unbound),
                                           "reason_counts": dict(Counter(d.split(": ", 1)[-1] for _, _, d in unbound)),
                                           "case_arms": sorted(set((c, a) for c, a, _ in unbound)),
                                           "classification": "DISPLAY_ANCHOR_GAP_NOT_MATH_ERROR"},
                      "live_gemini_calls": 0}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
