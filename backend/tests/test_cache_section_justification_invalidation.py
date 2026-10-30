# -*- coding: utf-8 -*-
"""CACHE_VERSION 130 -> 131: certified section-edge justifications (run `geometry-generalization-and-pedagogical-construction`).

The shared Scene3D builder now attaches `justification_text` + `details.justification` to a section edge whose parallel
relation it verifies exactly. The default LLM_ONLY route returns a cache hit's envelope as is, so a v130 row would keep
serving a scene without the "why" of its steps: it must MISS. 0 model calls.
"""
from types import SimpleNamespace

from app import main as main_module
from app.main import SUPPORTED_VERSIONS, _cache_lookup


class _Session:
    def __init__(self, row):
        self.row = row

    def query(self, _model):
        return self

    def filter_by(self, **_k):
        return self

    def first(self):
        return self.row


def _row(policy_version):
    return SimpleNamespace(policy_version=policy_version, dsl_version=next(iter(SUPPORTED_VERSIONS)))


def test_cache_version_is_131():
    assert main_module.CACHE_VERSION == "131"


def test_v130_row_misses_and_a_v131_row_hits():
    assert _cache_lookup(_Session(_row("130")), "k") is None
    hit = _row("131")
    assert _cache_lookup(_Session(hit), "k") is hit
