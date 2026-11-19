# -*- coding: utf-8 -*-
"""Experimental isolated prototype for AXO CONSTRUCTION /1.

Provides `verified-construction-graph/1`, `presentation-step-graph/1`,
`construction-operator/1`, `dynamic-construction-planner/1`, a `Scene3D`
compatibility bridge, and a read-only `Model 2` readiness interface without
modifying `backend/app/**` or `frontend/**`.
"""
from __future__ import annotations

PROTOTYPE_STATUS = "RESEARCH_PROTOTYPE_NON_PRODUCTION"
VERIFIED_CONSTRUCTION_GRAPH_SCHEMA = "verified-construction-graph/1"
PRESENTATION_STEP_GRAPH_SCHEMA = "presentation-step-graph/1"
CONSTRUCTION_OPERATOR_SCHEMA = "construction-operator/1"
DYNAMIC_PLANNER_VERSION = "dynamic-construction-planner/1"
EXACT_VERIFIER_VERSION = "construction-exact-verifier/1"
SCENE3D_BRIDGE_VERSION = "construction-scene3d-bridge/1"
MODEL2_INTERFACE_SCHEMA = "model2-action-interface/1"

__all__ = [
    "CONSTRUCTION_OPERATOR_SCHEMA",
    "DYNAMIC_PLANNER_VERSION",
    "EXACT_VERIFIER_VERSION",
    "MODEL2_INTERFACE_SCHEMA",
    "PRESENTATION_STEP_GRAPH_SCHEMA",
    "PROTOTYPE_STATUS",
    "SCENE3D_BRIDGE_VERSION",
    "VERIFIED_CONSTRUCTION_GRAPH_SCHEMA",
]
