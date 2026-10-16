"""Run `hybrid-semantic-grounding-reliability`: request coverage (M1), plane identity (M2), descriptor length wording
(M3) and the cube line_ref premise (M4), on the preregistered corpus (`runs/hybrid-semantic-grounding-reliability/
corpus.json`, exact values from its independent `oracle.py`). Real fact route, authored Typed Facts, no model.
"""
from __future__ import annotations

import json
from copy import deepcopy
from fractions import Fraction
from pathlib import Path

import pytest

from app.ai.function_route import run_fact_route
from app.simulation.geometry_functions.registry import _cung_mat, nhom_mat_nguon

RUN = Path(__file__).resolve().parents[3] / "docs/evaluation/geometry/runs/hybrid-semantic-grounding-reliability"
CORPUS = json.loads((RUN / "corpus.json").read_text(encoding="utf-8"))["cases"]
ORACLE = json.loads((RUN / "oracle.json").read_text(encoding="utf-8"))["values"]


def squared(v):
    from app.simulation.geometry.radical import Radical
    return Fraction(v.he) ** 2 * v.can if isinstance(v, Radical) else Fraction(v) ** 2


def run(case):
    return run_fact_route(case["text"], deepcopy(case["payload"]))


def check(case, r):
    if case["expect"] == "SERVE":
        assert r.status == "SERVED", (case["id"], r.code, r.reason)
        want = ORACLE[case["id"]]
        assert set(r.answers) == set(want), case["id"]
        for qid, v in want.items():
            assert squared(r.exec_result.final_memory[f"kq_{qid}"]) == Fraction(v), (case["id"], qid)
    else:
        assert r.status == "REFUSED", (case["id"], r.answers)
        assert r.code in case["refuse_codes"], (case["id"], r.code, r.reason)


#: Preregistered label kept, measured deviation: "diện tích toàn phần" is in no ask grammar, so request coverage cannot
#: name it; the case is still refused (asserted below), as NOT_ASKED_IN_SOURCE by the descriptor binder.
_DEVIATION = {"E05-unsupported-second-quantity": "refused NOT_ASKED_IN_SOURCE: an unsupported quantity is not a known ask phrase"}


@pytest.mark.parametrize("case", [pytest.param(c, marks=pytest.mark.xfail(strict=True, reason=_DEVIATION[c["id"]]))
                                  if c["id"] in _DEVIATION else c
                                  for c in CORPUS if c["mechanism"] != "none"], ids=lambda c: c["id"])
def test_targeted_case_meets_its_preregistered_label(case):
    check(case, run(case))


def test_historical_unread_second_ask_is_still_refused():
    """generalized-goal-entry row `unread-second-ask` keeps its refusal; only the code is now the specific one."""
    corpus = json.loads((RUN.parent / "generalized-goal-entry/corpus.json").read_text(encoding="utf-8"))
    case = next(c for c in corpus["negative"] if c["id"] == "unread-second-ask")
    r = run(case)
    assert (r.status, r.code) == ("REFUSED", "REQUEST_NOT_ANSWERED"), (r.code, r.answers)


@pytest.mark.parametrize("case", [c for c in CORPUS if c["expect"] == "REFUSE"], ids=lambda c: c["id"])
def test_no_case_the_source_does_not_license_is_served(case):
    assert run(case).status == "REFUSED", case["id"]


def test_written_plane_groups_are_collected_for_the_exact_engine_check():
    assert nhom_mat_nguon("Tính khoảng cách từ D đến (SABC).") == [list("SABC")]
    assert nhom_mat_nguon("mặt phẳng ABC'D' và (A'B'C'D')") == [["A", "B", "C'", "D'"], ["A'", "B'", "C'", "D'"]]
    assert nhom_mat_nguon("Cho hình chóp S.ABCD. Tính khoảng cách từ S đến (SAB).") == [list("SAB")]  # no solid-name group
    assert _cung_mat(frozenset("SABC"), list("SAB"))          # the gate still reads it as (SAB) …
    case = next(c for c in CORPUS if c["id"] == "C02-four-label-nonplane-named")
    r = run(case)                                               # … and the built figure refuses it: S, A, B, C not coplanar
    assert (r.status, r.code) == ("REFUSED", "SOURCE_OBJECT_MISMATCH") and "SABC" in r.reason


def test_an_asked_object_no_call_answers_is_refused_whatever_the_wording():
    """M1 is one rule over the shared ask inventory, not a list of follow-up words: the dropped request may be listed,
    joined by "sau đó", or stand in its own sentence."""
    base = next(c for c in CORPUS if c["id"] == "A01-desc-plane-imperative")
    for tail in (" và độ dài SC.", ", rồi tính độ dài SC.", ". Tiếp theo, tính thể tích khối chóp S.ABCD.",
                 ". Độ dài SC bằng bao nhiêu?"):
        c = deepcopy(base)
        c["text"] = c["text"][:-1] + tail
        if not tail.startswith("."):                                # the extracted ask quotes its whole sentence
            q = c["payload"]["facts"][-1]
            q["quotes"] = [q["quotes"][0][:-1] + tail]
        r = run(c)
        assert r.status == "REFUSED" and r.code == "REQUEST_NOT_ANSWERED", (tail, r.code, r.answers)
