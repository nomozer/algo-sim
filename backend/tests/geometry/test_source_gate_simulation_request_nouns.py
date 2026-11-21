"""Source Gate reads a simulation request that names a declared solid by ANY kind word the gate can verify (/11).

Before /11 `_VAT_MO_PHONG` read only "hình (chóp|lăng trụ)", so "Hãy mô phỏng hình lập phương." with correct facts and a
correct `construct_object` goal was refused (SOURCE_PREMISE_UNREAD). A specific kind word or modifier is a claim: it is read
only when `_loai_cum_dung` proves it from the validated calls. Negations, conditionals, undeclared or wrong-kind solids,
curved solids and wrong labels stay unread.
"""

import copy

import pytest

from app.ai.hybrid_offline import hybrid_offline_policy, run_hybrid_offline
from app.ai.local_geometry_parser import parse_geometry_problem_locally
from app.ai.typed_fact_next_extraction import ReplayExtractor

POLICY = hybrid_offline_policy({"HYBRID_ROUTE_D_PREVIEW": "1"})
CUBE = "Cho hình lập phương ABCD.A'B'C'D' cạnh a. "
BOX = "Cho hình hộp chữ nhật ABCD.A'B'C'D' có AB = 2, AD = 3, AA' = 4. "
REG_PYR = "Cho hình chóp tứ giác đều S.ABCD có cạnh đáy bằng a và cạnh bên bằng 2a. "
PYR = "Cho hình chóp S.ABCD có đáy ABCD là hình vuông cạnh a, SA vuông góc với (ABCD), SA = a. "
REG_TET = "Cho tứ diện đều ABCD cạnh a. "
TET = "Cho tứ diện OABC có OA, OB, OC đôi một vuông góc và OA = a, OB = 2a, OC = 3a. "
PRISM = "Cho lăng trụ đứng ABC.A'B'C' có đáy là tam giác đều cạnh a, AA' = 2a. "


def gate(base: str, command: str) -> tuple[str | None, str | None]:
    """Facts from the deterministic parser on `base + 'Hãy mô phỏng hình.'`; only the command (and its quote) changes."""
    lp = parse_geometry_problem_locally(base + "Hãy mô phỏng hình.", use_cache=False)
    assert lp.payload is not None, lp.status
    text = base + command
    p = copy.deepcopy(lp.payload)
    p["problem_text"] = text
    p["simulation_goals"][0]["quote"] = command.rstrip(".")
    r = run_hybrid_offline(text, ReplayExtractor({text: p}), policy=POLICY, timeout_seconds=30)
    rd = r.response.get("route_d") or {}
    return rd.get("status"), (rd.get("refusal") or {}).get("code")


@pytest.mark.parametrize("base,command", [
    (CUBE, "Hãy mô phỏng hình lập phương."),
    (CUBE, "Vẽ hình lập phương ABCD.A'B'C'D'."),
    (CUBE, "Mô phỏng hình lập phương đó."),
    (CUBE, "Biểu diễn hình lập phương đã cho."),
    (CUBE, "Hiển thị khối lập phương này."),
    (CUBE, "Hãy dựng hình 3D."),
    (CUBE, "Dựng hình theo giả thiết trên."),
    (CUBE, "Chỉ cần vẽ hình, không cần tính toán."),
    (BOX, "Hãy mô phỏng hình hộp chữ nhật."),
    (BOX, "Mô phỏng hình hộp chữ nhật này."),
    (REG_PYR, "Hãy dựng hình chóp đều đó."),
    (REG_PYR, "Vẽ hình chóp tứ giác đều S.ABCD."),
    (PYR, "Vẽ hình chóp S.ABCD."),
    (PYR, "hãy MÔ PHỎNG hình chóp."),
    (REG_TET, "Hãy mô phỏng tứ diện đều ABCD."),
    (REG_TET, "Mô phỏng tứ diện."),
    (TET, "Hãy mô phỏng tứ diện OABC."),
    (PRISM, "Biểu diễn khối lăng trụ đã cho."),
    (PRISM, "Hãy vẽ hình lăng trụ đứng ABC.A'B'C'."),
])
def test_request_naming_a_verified_declared_solid_is_read(base, command):
    assert gate(base, command) == ("SERVED", None)


@pytest.mark.parametrize("base,command", [
    (BOX, "Hãy mô phỏng hình lập phương."),           # claim false: the box is not a cube
    (PYR, "Hãy dựng hình chóp đều đó."),               # claim false: SA ⊥ base, not a regular pyramid
    (TET, "Hãy mô phỏng tứ diện đều OABC."),           # claim false
    (PYR, "Vẽ hình chóp S.MNPQ."),                     # wrong labels
    (CUBE, "Vẽ hình chóp S.ABCD."),                    # kind not declared
    (CUBE, "Hãy mô phỏng hình cầu."),                  # curved, not declared
    (CUBE, "Không mô phỏng hình lập phương."),         # negation
    (CUBE, "Đừng dựng hình lập phương này."),          # negation
    (CUBE, "Vẽ một hình bất kỳ khác hình lập phương."),
    (CUBE, "Nếu cạnh bằng 2 thì hãy vẽ hình lập phương."),
])
def test_unverifiable_or_negated_request_stays_unread(base, command):
    status, _code = gate(base, command)
    assert status != "SERVED"


@pytest.mark.parametrize("variant", ["Hãy mô phỏng hình lập phương.", "hãy mô phỏng hình lập phương", "HÃY MÔ PHỎNG HÌNH LẬP PHƯƠNG.",
                                     "Hãy  mô  phỏng  hình  lập  phương .", "Em hãy mô phỏng hình lập phương giúp em."])
def test_case_spacing_and_politeness_metamorphic(variant):
    assert gate(CUBE, variant) == ("SERVED", None)
