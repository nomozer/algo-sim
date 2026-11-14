# -*- coding: utf-8 -*-
"""CACHE_VERSION 133 → 134 (verified-section-intersection-dihedral-local).

Under 133 the angle construction of (SBC)/(SCD) drew the 120° supplement of the 60° asked angle, and a pyramid volume
whose altitude the scene did not draw carried no altitude construction. A `133:route-d` row holding such an envelope must
MISS under 134; the fresh envelope draws the acute angle and carries the altitude.
"""
from __future__ import annotations

import json
from fractions import Fraction

from app import main as main_module
from app.ai.adaptive_input_router import route_text_input
from app.main import SUPPORTED_VERSIONS, _cache_lookup, _served_route_d
from app.persistence.db import SessionLocal, SimulationCache, init_db

P = "Cho hình chóp S.ABCD có đáy ABCD là hình vuông cạnh a, "
ANGLE = P + "SA vuông góc với mặt phẳng đáy và SA = a. Tính góc giữa mặt phẳng (SBC) và mặt phẳng (SCD)."
VOLUME = P + "tam giác SAB đều và nằm trong mặt phẳng vuông góc với mặt phẳng đáy. Tính thể tích khối chóp S.ABCD."


def test_version_pair():
    assert main_module.CACHE_VERSION == "136" and main_module.ROUTE_D_CACHE_POLICY == "136:route-d"


def test_fresh_envelopes_carry_the_acute_angle_and_the_altitude():
    sc = route_text_input(ANGLE, allow_live_ai=False).response["envelope"]["scene3d"]
    ac = next(o for o in sc["objects"] if o.get("angle_construction"))["angle_construction"]
    v = [Fraction(x) for x in ac["vertex"]]
    a, b = ([Fraction(x) - y for x, y in zip(arm["to"], v)] for arm in ac["arms"])
    assert sum(x * y for x, y in zip(a, b)) >= 0 and ac["angle_domain"] == "[0°, 90°]"
    sc = route_text_input(VOLUME, allow_live_ai=False).response["envelope"]["scene3d"]
    assert any(o.get("altitude_construction") for o in sc["objects"])


def test_row_written_under_133_misses():
    fresh = route_text_input(VOLUME, allow_live_ai=False).response
    old = json.loads(json.dumps(fresh))
    for o in old["envelope"]["scene3d"]["objects"]:
        o.pop("altitude_construction", None)                     # what a 133 row holds
    key = "dihedral-altitude-invalidation-probe"
    init_db()
    with SessionLocal() as s:
        s.query(SimulationCache).filter_by(key=key).delete()
        s.add(SimulationCache(key=key, problem_text=VOLUME, simulation_id="generic.semantic_program",
                              envelope_json=json.dumps(old, ensure_ascii=False), dsl_version=next(iter(SUPPORTED_VERSIONS)),
                              policy_version="133:route-d"))
        s.commit()
        try:
            assert _cache_lookup(s, key, main_module.ROUTE_D_CACHE_POLICY) is None
            row = s.query(SimulationCache).filter_by(key=key).first()
            row.policy_version = main_module.ROUTE_D_CACHE_POLICY      # control: the same row under 134 is a HIT
            s.commit()
            assert _served_route_d(_cache_lookup(s, key, main_module.ROUTE_D_CACHE_POLICY)) is not None
        finally:
            s.query(SimulationCache).filter_by(key=key).delete()
            s.commit()
