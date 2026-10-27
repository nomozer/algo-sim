"""Run `hybrid-v2-planner-premerge-review`: a solid KIND word written without the solid's symbol must be true of the cut
solid the gate validated (registry /16, `_loai_cum_dung`). Before, only a pyramid-like / prism-like split was checked, so
"thiết diện của hình lập phương với (P)" was served for a triangular prism, "tứ diện" for S.ABCD, "lăng trụ đứng" for an
oblique prism (reproduced on candidate ca0bb5f2, `results/red-before.json`). No provider calls.
"""
from copy import deepcopy
import importlib.util
from pathlib import Path

import pytest

RUN = Path(__file__).resolve().parents[3] / "docs/evaluation/geometry/runs/hybrid-v2-planner-premerge-review"
_spec = importlib.util.spec_from_file_location("premerge_adversarial", RUN / "tools/adversarial.py")
A = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(A)


def _area(rid, word):
    return A._edit(A.ROW[rid], A._prism_area(rid, A.PRISMS[rid]), A._prism_area(rid, word))


def _section(rid, word):
    return A._edit(A.ROW[rid], A._prism_sec(rid, A.PRISMS[rid]), A._prism_sec(rid, word))


KIND_ONLY = [(rid, w, e) for rid, t in A.KIND_ONLY.items() for w, e in t.items()]


@pytest.mark.parametrize("rid,word,expect", KIND_ONLY, ids=lambda x: str(x))
@pytest.mark.parametrize("clause", [_area, _section], ids=["area", "section"])
def test_kind_only_wording_must_be_true_of_the_cut_solid(clause, rid, word, expect):
    r = A._run(clause(rid, word))
    assert r["status"] == expect, (r["code"], r["reason"])
    if expect == "REFUSED":
        assert r["code"] == "SOURCE_OBJECT_MISMATCH", r


def test_provider_order_and_renaming_do_not_change_the_kind_decision():
    for rid, word, expect in (("right-base", "hình lập phương", "REFUSED"), ("cube-diagonal", "hình lập phương", "SERVED")):
        row = A._edit(_area(rid, word), A._prism_sec(rid, A.PRISMS[rid]), A._prism_sec(rid, word))
        row["payload"]["facts"].reverse()
        assert A._run(row)["status"] == expect
    rid = "renamed-changed-reversed"
    row = A._edit(A.ROW[rid], A._prism_area(rid, "lăng trụ đứng DEF.D'E'F'"), A._prism_area(rid, "hình lập phương"))
    assert A._run(row)["status"] == "REFUSED"


def test_pyramid_kind_words_and_volume_path():
    rows = {r["id"]: r for r in A.pyramid_cases() + A.volume_cases()}
    bad = {k: (r["status"], r["code"]) for k, r in rows.items() if r["status"] != r["expect"]}
    assert not bad, bad
    assert rows["pyr4|area|tứ diện"]["status"] == "REFUSED"          # S.ABCD is not a tetrahedron
    assert rows["pyr3|area|tứ diện"]["status"] == "SERVED"           # S.ABC is one


def test_outside_the_gate_a_specific_kind_cannot_be_verified():
    from app.simulation.geometry_functions import registry as RG
    assert RG._loai_cum_dung("lăng trụ", "ABC.A'B'C'", ())            # generic: structure suffices
    assert not RG._loai_cum_dung("hình lập phương", "ABCD.A'B'C'D'", ())   # specific: no validated calls -> refuse
    # the gate's calls do not outlive the gate run (independent review MINOR 1)
    assert A._run(A.ROW["cube-diagonal"])["status"] == "SERVED"
    assert RG._GOI_NGUON.get() == ()
    assert not RG._loai_cum_dung("hình lập phương", "ABCD.A'B'C'D'")


@pytest.mark.xfail(strict=True, reason="OWNER_DECISION: a correct solid symbol outranks a contradicting kind word "
                                        "(test_solid_symbol_outranks_the_solid_word, run hybrid-semantic-hardening)")
@pytest.mark.parametrize("rid,ask", [("right-base", "hình lập phương ABC.A'B'C'"), ("right-base", "hình chóp ABC.A'B'C'"),
                                     ("cuboid-base", "hình lập phương ABCD.A'B'C'D'")])
def test_correct_symbol_with_contradicting_kind_word_is_still_served(rid, ask):
    assert A._run(_area(rid, ask))["status"] == "REFUSED"
