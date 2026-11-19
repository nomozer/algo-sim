# -*- coding: utf-8 -*-
"""Deterministic canonical JSON serialization and SHA-256 digests for construction graphs."""
from __future__ import annotations

import hashlib
import json
from typing import Any

from .construction_graph import ConstructionProofGraph, PresentationStepGraph


def canonical_json_dumps(payload: Any) -> str:
    return json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False).replace("\r\n", "\n") + "\n"


def serialize_proof_graph(graph: ConstructionProofGraph) -> str:
    return canonical_json_dumps(graph.to_dict())


def serialize_presentation_graph(graph: PresentationStepGraph) -> str:
    return canonical_json_dumps(graph.to_dict())


def graph_sha256(graph: ConstructionProofGraph) -> str:
    return hashlib.sha256(serialize_proof_graph(graph).encode("utf-8")).hexdigest()


def presentation_sha256(graph: PresentationStepGraph) -> str:
    return hashlib.sha256(serialize_presentation_graph(graph).encode("utf-8")).hexdigest()
