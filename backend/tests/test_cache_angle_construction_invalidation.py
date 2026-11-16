# -*- coding: utf-8 -*-
"""CACHE_VERSION 132 → 133 (semantic-to-scene3d-verified-simulation): a served angle now carries `angle_construction`.

A Route D row written under `132:route-d` holds an envelope WITHOUT the construction; under 133 it must MISS so the
learner never gets the old scene back from the cache. The fresh envelope for the same text carries the construction.
"""
from __future__ import annotations

import json

from app import main as main_module
from app.ai.adaptive_input_router import route_text_input
from app.main import SUPPORTED_VERSIONS, _cache_lookup, _served_route_d
from app.persistence.db import SessionLocal, SimulationCache, init_db

TEXT = ("Cho hình chóp S.ABCD có đáy ABCD là hình vuông cạnh a, SA vuông góc với mặt phẳng đáy và SA = a. "
        "Tính góc giữa đường thẳng SC và mặt phẳng (ABCD).")


def test_version_pair():
    assert main_module.CACHE_VERSION == "142" and main_module.ROUTE_D_CACHE_POLICY == "142:route-d"


def test_row_written_under_132_misses_and_the_new_scene_carries_the_construction():
    fresh = route_text_input(TEXT, allow_live_ai=False).response
    quantity = next(o for o in fresh["envelope"]["scene3d"]["objects"] if o["type"] == "quantity")
    assert quantity["angle_construction"]["relation"] == "line_plane"
    old = json.loads(json.dumps(fresh))
    for o in old["envelope"]["scene3d"]["objects"]:
        o.pop("angle_construction", None)                       # what a 132 row holds
    key = "angle-construction-invalidation-probe"
    init_db()
    with SessionLocal() as s:
        s.query(SimulationCache).filter_by(key=key).delete()
        s.add(SimulationCache(key=key, problem_text=TEXT, simulation_id="generic.semantic_program",
                              envelope_json=json.dumps(old, ensure_ascii=False), dsl_version=next(iter(SUPPORTED_VERSIONS)),
                              policy_version="132:route-d"))
        s.commit()
        try:
            assert _cache_lookup(s, key, main_module.ROUTE_D_CACHE_POLICY) is None
            row = s.query(SimulationCache).filter_by(key=key).first()
            row.policy_version = main_module.ROUTE_D_CACHE_POLICY     # control: the same row under 133 is a HIT
            s.commit()
            assert _served_route_d(_cache_lookup(s, key, main_module.ROUTE_D_CACHE_POLICY)) is not None
        finally:
            s.query(SimulationCache).filter_by(key=key).delete()
            s.commit()
