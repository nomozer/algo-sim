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
