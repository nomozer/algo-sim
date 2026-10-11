"""RED (strict xfail): a forward plane projection must not re-root the declared solid in the scene.

Independent review of geometry-library-expansion, 2026-10-11. In tetrahedron S.ABC (apex S declared),
"K là hình chiếu vuông góc của A lên (SBC)" is computed correctly (K = (3/8, 3/8, 1/4)), but the scene is
built as apex A over base SBC: "Đáy SBC", "Chiều cao AK", lateral edges from A. Cause: the function route
calls `build_simulation_state` without the declared solid topology, so `formation.lop_khoi` resolves the
four-way tetrahedron reading from the new `project_onto` IR alone. The square-pyramid oracles cannot see it
(one face reading). Remove the xfail in the wave that passes the declared topology to formation.
"""
from __future__ import annotations

import pytest

from tests.geometry import test_geometry_library_expansion as T

BASE = ["Cho hình chóp S.ABC.", "Đáy ABC là tam giác đều cạnh 2.", "SA vuông góc với (ABC).", "SA = 3."]
CALLS = [("pyramid", {"apex": "S", "base": list("ABC")}, BASE[0]),
         ("regular_polygon", {"vertices": list("ABC"), "side": "2"}, BASE[1]),
         ("perpendicular_line_plane", {"line": list("SA"), "plane": list("ABC")}, BASE[2]),
         ("segment_length", {"segment": list("SA"), "value": "3"}, BASE[3])]
FACTS = [{"kind": "solid", "solid": "S.ABC", "solid_type": "pyramid"},
         {"kind": "polygon_shape", "points": list("ABC"), "shape": "equilateral_triangle", "value": "2"},
         {"kind": "perpendicular", "points_a": list("SA"), "points_b": list("ABC")},
         {"kind": "length", "points": list("SA"), "measure": "segment", "value": "3"}]
PROJECTION = ("orthogonal_projection", {"point": "A", "plane": list("SBC"), "image": "K"},
              {"kind": "projection", "point": "A", "points": list("SBC"), "at": "K"},
              "Gọi K là hình chiếu vuông góc của A lên (SBC).")


@pytest.mark.xfail(strict=True, reason="REVIEW-2026-10-11: function route passes no solid topology to formation")
@pytest.mark.parametrize("arm", ["A", "B"])
def test_projection_onto_lateral_face_keeps_declared_apex(arm, monkeypatch):
    monkeypatch.setattr(T, "BASE", BASE)
    monkeypatch.setattr(T, "CALLS", CALLS)
    monkeypatch.setattr(T, "FACTS", FACTS)
    r, _ = T.run(arm, [PROJECTION], solid="S.ABC")
    assert r.status == "SERVED", (r.code, r.reason)
    assert T.scene_point(r, "K")["xyz"] == ["3/8", "3/8", "1/4"]  # the math is right; only the scene identity is wrong
    drawn = {o["display_label"] for o in r.scene3d["objects"] if o["type"] in ("polygon3", "segment3")}
    assert "Đáy SBC" not in drawn and "Chiều cao AK" not in drawn, drawn
    assert not any(label.startswith("Cạnh bên A") for label in drawn), drawn
