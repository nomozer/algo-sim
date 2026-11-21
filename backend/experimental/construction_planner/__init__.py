# -*- coding: utf-8 -*-
"""Experimental isolated prototype for AXO CONSTRUCTION /1 & /2.

Provides `verified-construction-graph/1`, `presentation-step-graph/1`,
`construction-operator/1`, `dynamic-construction-planner/1` & `/2`,
`construction-exact-verifier/1` & `/2`, a `Scene3D` compatibility bridge,
geometry invariance utilities, verified-input Source Gate bridge, controlled
integration adapter, and a read-only `Model 2` readiness interface + deterministic
selector without modifying `backend/app/**` or `frontend/**`.
"""
from __future__ import annotations

PROTOTYPE_STATUS = "RESEARCH_PROTOTYPE_NON_PRODUCTION"
VERIFIED_CONSTRUCTION_GRAPH_SCHEMA = "verified-construction-graph/1"
PRESENTATION_STEP_GRAPH_SCHEMA = "presentation-step-graph/1"
CONSTRUCTION_OPERATOR_SCHEMA = "construction-operator/1"
DYNAMIC_PLANNER_VERSION = "dynamic-construction-planner/1"
DYNAMIC_PLANNER_V2_VERSION = "dynamic-construction-planner/2"
EXACT_VERIFIER_VERSION = "construction-exact-verifier/1"
EXACT_VERIFIER_V2_VERSION = "construction-exact-verifier/2"
BENCHMARK_EVALUATOR_V2_VERSION = "construction-benchmark-evaluator/2"
SCENE3D_BRIDGE_VERSION = "construction-scene3d-bridge/1"
PRESENTATION_VALIDATOR_VERSION = "presentation-step-validator/1"
MODEL2_INTERFACE_SCHEMA = "model2-action-interface/1"
MODEL2_DETERMINISTIC_SELECTOR_VERSION = "model2-deterministic-selector/1"
VERIFIED_INPUT_BRIDGE_VERSION = "verified-typed-facts-bridge/1"
INTEGRATION_ADAPTER_VERSION = "dynamic-construction-integration-adapter/1"

__all__ = [
    "BENCHMARK_EVALUATOR_V2_VERSION",
    "CONSTRUCTION_OPERATOR_SCHEMA",
    "DYNAMIC_PLANNER_V2_VERSION",
    "DYNAMIC_PLANNER_VERSION",
    "EXACT_VERIFIER_V2_VERSION",
    "EXACT_VERIFIER_VERSION",
    "INTEGRATION_ADAPTER_VERSION",
    "MODEL2_DETERMINISTIC_SELECTOR_VERSION",
    "MODEL2_INTERFACE_SCHEMA",
    "PRESENTATION_STEP_GRAPH_SCHEMA",
    "PRESENTATION_VALIDATOR_VERSION",
    "PROTOTYPE_STATUS",
    "SCENE3D_BRIDGE_VERSION",
    "VERIFIED_CONSTRUCTION_GRAPH_SCHEMA",
    "VERIFIED_INPUT_BRIDGE_VERSION",
]
