"""Post-implementation offline wording holdout. Replay payloads do not measure live extraction accuracy."""
import json
import os
import sys
from pathlib import Path

os.environ["ALLOW_LIVE_AI"] = "0"
ROOT = Path(__file__).resolve().parents[6]
sys.path.insert(0, str(ROOT / "backend"))
from tests.geometry import test_hybrid4_three_point_plane_sections as T
from app.ai.hybrid_offline import run_hybrid_offline
from app.ai.typed_fact_next_extraction import ReplayExtractor, TYPED_FACT_NEXT_SYSTEM_INSTRUCTION

rows = []
for apex, base, pts, side, height in [("O", "KLMN", "UVW", 6, 3), ("T", "EFGH", "XYZ", 3, 7)]:
    solid, premises = T.square_pyramid(apex, base, side, height)
    premises += [T.midpoint(pts[i], apex, base[i]) for i in range(3)]
    for reverse in (False, True):
        prem = list(reversed(premises)) if reverse else premises
        for kind, phrase in [
            ("named_plane", f"cắt bởi mặt phẳng ({pts})"),
            ("section_by", f"cắt bởi ({pts})"),
            ("three_points", f"cắt bởi mặt phẳng đi qua ba điểm {', '.join(pts)}"),
            ("three_points_named", f"cắt bởi mặt phẳng ({pts}) đi qua ba điểm {', '.join(pts)}"),
        ]:
            quote = f"Xác định thiết diện của hình chóp {apex}.{base} {phrase}"
            _, payload = T._payload(solid, prem, list(pts))
            text = ". ".join([s for s, _ in prem] + [quote, T.AREA_Q]) + "."
            payload["problem_text"] = text
            payload["derived_sections"][0]["quote"] = quote
            payload["simulation_goals"][1]["quote"] = quote
            out = run_hybrid_offline(text, ReplayExtractor({text: payload}), policy=T.POLICY).response
            route, env = out["route_d"], out["envelope"]
            status = route["status"]
            row = {"family": "pyramid", "notation": solid["notation"], "wording": kind,
                   "reversed_premises": reverse, "status": status,
                   "classification": "CORRECTLY_SERVED" if status == "SERVED" else "INCORRECTLY_REFUSED"}
            if status == "SERVED":
                sec = next(o for o in env["scene3d"]["objects"] if o["type"] == "section")
                assert len(sec["polygon"]) == 4
                row["section_vertices"] = len(sec["polygon"])
            else:
                row["reason"] = route.get("refusal", {}).get("code", "UNKNOWN")
            rows.append(row)
out = Path(__file__).resolve().parents[1] / (Path(sys.argv[1]).name if len(sys.argv) > 1 else "wording-holdout.json")
assert not out.exists(), "fresh output required"
result = {"provider_calls": 0, "live_extraction_accuracy": "NOT_MEASURED", "prompt_changed": False,
          "prompt_three_point_rule_present": "contains_points=M,N,P" in TYPED_FACT_NEXT_SYSTEM_INSTRUCTION,
          "rows": rows}
out.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(json.dumps({"served": sum(r["status"] == "SERVED" for r in rows), "refused": sum(r["status"] != "SERVED" for r in rows), "total": len(rows), "provider_calls": 0}))
