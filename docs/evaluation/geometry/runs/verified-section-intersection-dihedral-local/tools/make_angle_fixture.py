"""Regenerate frontend/src/simulations/domains/geometry/scene3d-angle-construction-fixtures.json from the served
envelopes (route_text_input, local-first, ALLOW_LIVE_AI=0). Run from backend/ after the angle contract changes."""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

os.environ["ALLOW_LIVE_AI"], os.environ["GEMINI_API_KEY"] = "0", ""
ROOT = Path(__file__).resolve().parents[6]
sys.path.insert(0, str(ROOT / "backend"))
from app.ai.adaptive_input_router import route_text_input  # noqa: E402
from app.main import CACHE_VERSION  # noqa: E402

P = "Cho hình chóp S.ABCD có đáy ABCD là hình vuông cạnh a, SA vuông góc với mặt phẳng đáy và SA = a. "
CASES = {
    "line_plane": P + "Tính góc giữa đường thẳng SC và mặt phẳng (ABCD).",
    "dihedral": P + "Tính góc giữa mặt phẳng (SBC) và mặt phẳng (ABCD).",
    "planes_60_not_120": P + "Tính góc giữa mặt phẳng (SBC) và mặt phẳng (SCD).",
    "skew": "Cho hình lập phương ABCD.A'B'C'D' có cạnh bằng a. Tính góc giữa hai đường thẳng AC và A'D.",
    "tetra": "Cho tứ diện đều ABCD có cạnh bằng a. Tính góc giữa đường thẳng AB và mặt phẳng (BCD).",
    "face_perp_altitude": ("Cho hình chóp S.ABCD có đáy ABCD là hình vuông cạnh a, tam giác SAB đều và nằm trong mặt phẳng "
                           "vuông góc với mặt phẳng đáy. Tính thể tích khối chóp S.ABCD."),
}
out = {"_generated_by": f"docs/evaluation/geometry/runs/verified-section-intersection-dihedral-local/tools/make_angle_fixture.py at CACHE_VERSION {CACHE_VERSION}",
       "cases": {k: {"text": t, "scene3d": route_text_input(t, allow_live_ai=False).response["envelope"]["scene3d"]} for k, t in CASES.items()}}
target = ROOT / "frontend/src/simulations/domains/geometry/scene3d-angle-construction-fixtures.json"
target.write_text(json.dumps(out, ensure_ascii=False, indent=1) + "\n", encoding="utf-8", newline="\n")
print("written", len(out["cases"]))
