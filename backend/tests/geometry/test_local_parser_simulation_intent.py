"""Rule 7b of the deterministic local parser reads simulation-only requests in one shared grammar (/11).

Simulation-only ⇒ exactly one `construct_object` on the named declared solid and NO math goal. The request must name one
declared solid (label set, or the only solid of that kind, or the figure); anything else stays unparsed. Positive cases go
through the real Source Gate / planner / engine from the parser payload alone (no SLM).
"""

import random

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
PRISM = "Cho lăng trụ đứng ABC.A'B'C' có đáy là tam giác đều cạnh a, AA' = 2a. "


def parse(text):
    return parse_geometry_problem_locally(text, use_cache=False)


def served(text, payload):
    r = run_hybrid_offline(text, ReplayExtractor({text: payload}), policy=POLICY, timeout_seconds=30)
    return (r.response.get("route_d") or {}).get("status")


POSITIVE = [
    (CUBE, "Hãy mô phỏng hình lập phương."), (CUBE, "Vẽ hình lập phương ABCD.A'B'C'D'."), (CUBE, "Mô phỏng hình lập phương đó."),
    (CUBE, "Biểu diễn khối lập phương đã cho."), (CUBE, "Hãy dựng hình 3D."), (CUBE, "Dựng hình theo giả thiết trên."),
    (CUBE, "Chỉ cần vẽ hình, không cần tính toán."), (CUBE, "Hiển thị hình lập phương này."),
    (BOX, "Mô phỏng hình hộp chữ nhật này."), (BOX, "Hãy cho em xem hình hộp chữ nhật."),
    (REG_PYR, "Hãy dựng hình chóp đều đó."), (PYR, "Vẽ hình chóp S.ABCD."), (PYR, "Em hãy vẽ giúp em hình chóp."),
    (REG_TET, "Hãy mô phỏng tứ diện đều ABCD."), (PRISM, "Biểu diễn khối lăng trụ đã cho."),
]


@pytest.mark.parametrize("base,command", POSITIVE)
def test_simulation_only_request_is_parsed_and_served_without_math_goal(base, command):
    lp = parse(base + command)
    assert lp.status == "LOCAL_PARSE_COMPLETE", (lp.status, lp.reason_code)
    p = lp.payload
    assert p["math_goals"] == []                                   # never a fabricated metric query
    assert [g["kind"] for g in p["simulation_goals"]] == ["construct_object"]
    assert p["simulation_goals"][0]["target_solid_id"] == p["solids"][0]["solid_id"]
    assert p["simulation_goals"][0]["quote"] in base + command
    assert served(base + command, p) == "SERVED"


def test_request_followed_by_question_keeps_the_question():
    text = CUBE + "Hãy mô phỏng hình lập phương và tính khoảng cách giữa hai đường thẳng AA' và BD."
    lp = parse(text)
    assert lp.status == "LOCAL_PARSE_COMPLETE" and len(lp.payload["math_goals"]) == 1
    assert served(text, lp.payload) == "SERVED"


NEGATIVE = [
    CUBE + "Không mô phỏng hình lập phương.",
    CUBE + "Đừng dựng hình lập phương này.",
    "Nếu ABCD.A'B'C'D' là hình lập phương cạnh a thì hãy vẽ hình lập phương.",
    PYR + "Vẽ hình chóp S.MNPQ.",                                    # label mismatch
    "Cho hình chóp M.PQR có đáy PQR là tam giác đều cạnh 2, MP vuông góc với đáy, MP = 2. Vẽ hình chóp S.ABCD.",
    CUBE + "Hãy mô phỏng hình cầu.",
    "Mô phỏng hình đó.",                                             # no declared solid
    CUBE + "Vẽ một hình bất kỳ khác hình lập phương.",
]


@pytest.mark.parametrize("text", NEGATIVE)
def test_unsafe_request_is_not_a_simulation_goal(text):
    lp = parse(text)
    goals = (lp.payload or {}).get("simulation_goals") or []
    assert lp.status != "LOCAL_PARSE_COMPLETE" or not goals or (lp.payload and served(text, lp.payload) != "SERVED")


def test_two_solids_and_unlabelled_deixis_is_not_resolved_by_guess():
    text = ("Cho hình chóp S.ABC có đáy là tam giác đều cạnh 2 và hình lập phương MNPQ.M'N'P'Q' cạnh 1. Hãy dựng hình đó.")
    lp = parse(text)
    assert lp.status != "LOCAL_PARSE_COMPLETE" or not (lp.payload or {}).get("simulation_goals")


@pytest.mark.parametrize("seed", range(6))
def test_metamorphic_case_spacing_punctuation(seed):
    rnd = random.Random(seed)
    words = ["Hãy", "mô", "phỏng", "hình", "lập", "phương"]
    words = [w.upper() if rnd.random() < 0.3 else (w.lower() if rnd.random() < 0.5 else w) for w in words]
    # "!" is excluded on purpose: the Source Gate's sentence end does not take it (documented limitation, outside the
    # owner-approved narrow change)
    command = (" " * rnd.randint(1, 2)).join(words) + rnd.choice([".", "", " ."])
    lp = parse(CUBE + command)
    assert lp.status == "LOCAL_PARSE_COMPLETE" and lp.payload["math_goals"] == []
