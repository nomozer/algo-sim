# -*- coding: utf-8 -*-
"""CACHE_VERSION 135 → 136 (run `target-invariant-regular-solid-semantics`).

This run TIGHTENS a guard (the similarity normalisation now refuses a figure with ≥ 2 independent height anchors, whose
sign branches it had not explored) and changes served envelopes (a regular tetrahedron without side, GEO-BE-001 display
names). The Route D key does not see any of that, so every row written under `135:route-d` must MISS; the same row
under the current policy is a HIT (no revalidation on read — hence the bump).
"""
from __future__ import annotations

import json

from app import main as main_module
from app.main import SUPPORTED_VERSIONS, _cache_lookup, _served_route_d
from app.persistence.db import SessionLocal, SimulationCache, init_db


def test_version_pair():
    assert main_module.CACHE_VERSION == "141" and main_module.ROUTE_D_CACHE_POLICY == "141:route-d"


def test_a_row_written_under_135_misses():
    body = {"route_d": {"status": "SERVED"}, "envelope": {"simulation_id": "generic.semantic_program"}}
    key = "target-invariance-invalidation-probe"
    init_db()
    with SessionLocal() as s:
        s.query(SimulationCache).filter_by(key=key).delete()
        s.add(SimulationCache(key=key, problem_text="probe", simulation_id="generic.semantic_program",
                              envelope_json=json.dumps(body), dsl_version=next(iter(SUPPORTED_VERSIONS)),
                              policy_version="135:route-d"))
        s.commit()
        try:
            assert _cache_lookup(s, key, main_module.ROUTE_D_CACHE_POLICY) is None
            s.query(SimulationCache).filter_by(key=key).update({"policy_version": main_module.ROUTE_D_CACHE_POLICY})
            s.commit()
            assert _served_route_d(_cache_lookup(s, key, main_module.ROUTE_D_CACHE_POLICY)) is not None
        finally:
            s.query(SimulationCache).filter_by(key=key).delete()
            s.commit()
