# -*- coding: utf-8 -*-
"""One assertion for "this test's cache premise still holds", shared by every invalidation test.

Each campaign used to pin the then-current value (`assert M.CACHE_VERSION == "147"`) in its own file, so every bump
edited ~30 test files and the pins said nothing the lock does not: `tests/test_cache_identity.py` already binds
`CACHE_VERSION` to the measured surface in `cache_identity.lock.json`. What a historical test owns is narrower —
the live policy is at least the version it introduced, so rows written before it MISS — and that is what this checks.
"""
from __future__ import annotations


def assert_cache_policy_at_least(introduced: str | int) -> None:
    """The live Route D policy is `CACHE_VERSION:route-d` and `CACHE_VERSION >= introduced`."""
    from app import main as M

    assert int(M.CACHE_VERSION) >= int(introduced), (M.CACHE_VERSION, introduced)
    assert M.ROUTE_D_CACHE_POLICY == f"{M.CACHE_VERSION}:route-d"


def assert_route_d_row_misses(old_policy: str) -> None:
    """A row written under `old_policy` MISSES in the product's Route D lookup; one under the live policy HITS."""
    from types import SimpleNamespace

    from app import main as M

    class _Session:
        def __init__(self, row):
            self.row = row

        def query(self, _model):
            return self

        def filter_by(self, **_k):
            return self

        def first(self):
            return self.row

    def row(policy):
        return SimpleNamespace(policy_version=policy, dsl_version=next(iter(M.SUPPORTED_VERSIONS)))

    assert M._cache_lookup(_Session(row(old_policy)), "k", M.ROUTE_D_CACHE_POLICY) is None
    live = row(M.ROUTE_D_CACHE_POLICY)
    assert M._cache_lookup(_Session(live), "k", M.ROUTE_D_CACHE_POLICY) is live
