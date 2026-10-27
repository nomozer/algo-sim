"""Run `hybrid-v2-planner-premerge-review` (/16) and `hybrid-v2-source-kind-consistency` (/17):
- /16: a solid KIND word written without the solid's symbol must be true of the cut solid the gate validated (`_loai_cum_dung`).
- /17 (OWNER DECISION `SOURCE_CONTRADICTION_MUST_FAIL_CLOSED`): a solid KIND phrase written WITH a solid symbol must also be
  true of that solid (`_khoi_khop`, `_cum_goi_khoi`, `_ten_khoi_khop`). No provider calls.
"""
from copy import deepcopy
import importlib.util
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
RUN = ROOT / "docs/evaluation/geometry/runs/hybrid-v2-planner-premerge-review"
SYM_RUN = ROOT / "docs/evaluation/geometry/runs/hybrid-v2-source-kind-consistency"

_spec = importlib.util.spec_from_file_location("premerge_adversarial", RUN / "tools/adversarial.py")
A = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(A)

_sym_spec = importlib.util.spec_from_file_location("source_kind_symbol_cases", SYM_RUN / "tools/symbol_cases.py")
S = importlib.util.module_from_spec(_sym_spec)
_sym_spec.loader.exec_module(S)


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


@pytest.mark.parametrize("rid,ask", [("right-base", "hình lập phương ABC.A'B'C'"), ("right-base", "hình chóp ABC.A'B'C'"),
                                     ("cuboid-base", "hình lập phương ABCD.A'B'C'D'")])
@pytest.mark.parametrize("clause", [_area, _section], ids=["area", "section"])
def test_correct_symbol_with_contradicting_kind_word_is_refused(clause, rid, ask):
    """OWNER DECISION `SOURCE_CONTRADICTION_MUST_FAIL_CLOSED` (run `hybrid-v2-source-kind-consistency`, I-1)."""
    r = A._run(clause(rid, ask))
    assert (r["status"], r["code"]) == ("REFUSED", "SOURCE_OBJECT_MISMATCH"), r


@pytest.mark.parametrize("cid,build,expect,cls", S.CASES, ids=[c[0] for c in S.CASES])
def test_symbol_and_kind_consistency_suite(cid, build, expect, cls):
    """31-case symbol + kind consistency suite (generic/specific compatible, contradictory specific/family, multi-solid,
    fact-order permutation, volume asks, and 4x4x4 cuboid without a cube premise)."""
    r = A._run(build())
    assert r["status"] == expect, (cid, cls, r["code"], r["reason"])
    if expect == "REFUSED":
        assert r["code"] == "SOURCE_OBJECT_MISMATCH", (cid, r)


def test_volume_ratio_and_residual_volume_reject_contradictory_kind_with_correct_symbol():
    """`_ten_khoi_khop` and `_ds_khoi_khop` also check `_loai_cum_dung` when a kind phrase precedes the symbol."""
    from app.simulation.geometry_functions import registry as RG

    khoi = {"S.MNP": frozenset("MNP"), "S.ABC": frozenset("ABC")}
    m_ok = RG._CUM_HOI["ask_volume_ratio"][0][0].search("tỉ số thể tích của khối chóp S.MNP và khối chóp S.ABC")
    assert m_ok and RG._CUM_HOI["ask_volume_ratio"][0][1](m_ok, type("A", (), {"numerator_solid": "S.MNP", "denominator_solid": "S.ABC"})(), khoi)

    m_bad = RG._CUM_HOI["ask_volume_ratio"][0][0].search("tỉ số thể tích của khối lập phương S.MNP và khối chóp S.ABC")
    assert m_bad and not RG._CUM_HOI["ask_volume_ratio"][0][1](m_bad, type("A", (), {"numerator_solid": "S.MNP", "denominator_solid": "S.ABC"})(), khoi)

    m_res_bad = RG._CUM_HOI["ask_residual_volume"][0][0].search(
        "thể tích phần còn lại của hình lập phương S.ABC sau khi cắt bỏ khối chóp S.MNP")
    assert m_res_bad and not RG._CUM_HOI["ask_residual_volume"][0][1](
        m_res_bad, type("A", (), {"original_solid": "S.ABC", "subtracted_solids": ["S.MNP"]})(), khoi)

    m_sub_bad = RG._CUM_HOI["ask_residual_volume"][0][0].search(
        "thể tích phần còn lại của hình chóp S.ABC sau khi cắt bỏ khối lăng trụ S.MNP")
    assert m_sub_bad and not RG._CUM_HOI["ask_residual_volume"][0][1](
        m_sub_bad, type("A", (), {"original_solid": "S.ABC", "subtracted_solids": ["S.MNP"]})(), khoi)
