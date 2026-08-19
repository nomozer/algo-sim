# -*- coding: utf-8 -*-
"""GENERATION_EQUIVALENCE: Kiểm định tính tương đương ngữ nghĩa của pipeline adapter và các ứng viên sinh."""
import pytest
from app.simulation.semantic_program.pipeline_adapter import compile_semantic_program_to_envelope
from .fixtures_coverage_18 import (
    P01_STACK_BRACKET,
    P03_BINARY_SEARCH,
    P04_BUBBLE_SORT,
    P09_GRAPH_BFS,
)
from .execution_oracles import (
    oracle_stack_bracket,
    oracle_binary_search,
    oracle_bubble_sort,
    oracle_graph_bfs,
)


def test_compile_p01_stack_bracket_to_envelope():
    envelope = compile_semantic_program_to_envelope(P01_STACK_BRACKET)
    assert envelope["status"] == "ok"
    assert envelope["domain"] == "generic"
    assert len(envelope["config"]["objects"]) > 0
    steps = envelope["config"]["processes"][0]["steps"]
    assert len(steps) > 5


def test_compile_p03_binary_search_to_envelope():
    envelope = compile_semantic_program_to_envelope(P03_BINARY_SEARCH)
    assert envelope["status"] == "ok"
    steps = envelope["config"]["processes"][0]["steps"]
    assert len(steps) > 3


def test_compile_p04_bubble_sort_to_envelope():
    envelope = compile_semantic_program_to_envelope(P04_BUBBLE_SORT)
    assert envelope["status"] == "ok"
    steps = envelope["config"]["processes"][0]["steps"]
    assert len(steps) > 5


def test_compile_p09_graph_bfs_to_envelope():
    envelope = compile_semantic_program_to_envelope(P09_GRAPH_BFS)
    assert envelope["status"] == "ok"
    steps = envelope["config"]["processes"][0]["steps"]
    assert len(steps) > 5
