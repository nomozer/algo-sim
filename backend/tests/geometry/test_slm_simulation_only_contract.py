"""Compact-clause SLM contract for simulation-only sources (/11, no model call).

Before /11 the GBNF made a show request a goal clause whose only legal goals were metric, and `root` demanded >= 1 goal or
>= 1 unresolved item: AxoV9 emitted `goal:vol` for 'Hãy mô phỏng hình lập phương' (SLM20_ROOT_CAUSE_AUDIT.json).
"""

from app.ai.hybrid_offline import hybrid_offline_policy, run_hybrid_offline
from app.ai.local_slm_extractor import (
    V9_CLOSURE_MODE,
    build_compact_clause_context,
    build_compact_grammar_for_context,
    is_simulation_only_source,
    validate_and_lower_compact_clause,
)
from app.ai.typed_fact_next_extraction import ReplayExtractor

POLICY = hybrid_offline_policy({"HYBRID_ROUTE_D_PREVIEW": "1"})
SIM = "Cho hình lập phương ABCD.A'B'C'D' có cạnh bằng a. Hãy mô phỏng hình lập phương."
ASK = "Cho hình lập phương ABCD.A'B'C'D' có cạnh bằng a. Tính độ dài đoạn AC'."
BARE = "Cho hình lập phương ABCD.A'B'C'D' có cạnh bằng a."
RAW_FACTS = {"s": [0, "cube", "ABCD.A'B'C'D'", 1], "r": [{"c": 0, "p": "len", "a": "AA'", "q": "a"}], "g": [], "u": []}


def served(payload):
    text = payload["problem_text"]
    r = run_hybrid_offline(text, ReplayExtractor({text: payload}), policy=POLICY, timeout_seconds=30)
    return (r.response.get("route_d") or {}).get("status")


def test_simulation_only_source_detection():
    assert is_simulation_only_source(build_compact_clause_context(SIM))
    assert not is_simulation_only_source(build_compact_clause_context(ASK))
    assert not is_simulation_only_source(build_compact_clause_context(BARE))           # no explicit show request
    assert not is_simulation_only_source(build_compact_clause_context(BARE + " Không mô phỏng hình lập phương."))


def test_grammar_admits_goal_free_output_only_for_simulation_only():
    g_sim = build_compact_grammar_for_context(build_compact_clause_context(SIM), closure_mode=V9_CLOSURE_MODE)
    root = g_sim.splitlines()[0]
    assert '\\"g\\":[],\\"u\\":[]' in root and "goalc" not in g_sim          # no metric goal can be emitted
    g_ask = build_compact_grammar_for_context(build_compact_clause_context(ASK), closure_mode=V9_CLOSURE_MODE)
    assert "goalc" in g_ask and "goallistreq" in g_ask.splitlines()[0]        # questions unchanged


def test_goal_free_lowering_quotes_the_request_and_is_served():
    payload, diag = validate_and_lower_compact_clause(ctx=build_compact_clause_context(SIM), raw_slm_json=RAW_FACTS,
                                                      closure_mode=V9_CLOSURE_MODE)
    assert payload is not None, diag
    assert diag["multi_goal_status"] == "SIMULATION_ONLY" and payload["math_goals"] == []
    assert payload["simulation_goals"][0]["quote"] == "Hãy mô phỏng hình lập phương"
    assert served(payload) == "SERVED"


def test_goal_free_output_on_a_source_that_asks_still_refuses():
    payload, diag = validate_and_lower_compact_clause(ctx=build_compact_clause_context(ASK), raw_slm_json=RAW_FACTS,
                                                      closure_mode=V9_CLOSURE_MODE)
    assert payload is None and diag["grounding_status"] == "REJECTED_NO_GROUNDED_GOAL"


def test_right_angle_quote_is_the_clause_stating_it_at_the_vertex():
    """/10 Q10: AxoV9's raw output (SLM20 audit) was correct; the right-angle premise was quoted 'SA vuông góc với (ABC)'."""
    text = ("Cho hình chóp S.ABC có đáy ABC là tam giác vuông tại A, AB = a, AC = 2a, SA vuông góc với (ABC), SA = 2a. "
            "Hãy biểu diễn hình chóp và tính thể tích.")
    raw = {"s": [0, "pyr", "S.ABC", 0], "r": [{"c": 0, "p": "right_tri", "a": "ABC", "pt": "A"}, {"c": 0, "p": "len", "a": "AB", "q": "a"},
           {"c": 0, "p": "len", "a": "AC", "q": "2a"}, {"c": 0, "p": "perp_lp", "a": "SA", "b": "ABC"}, {"c": 0, "p": "len", "a": "SA", "q": "2a"}],
           "g": [{"c": 1, "t": "vol", "tgt": "S.ABC"}], "u": []}
    payload, diag = validate_and_lower_compact_clause(ctx=build_compact_clause_context(text), raw_slm_json=raw, closure_mode=V9_CLOSURE_MODE)
    assert payload is not None, diag
    right = next(p for p in payload["premises"] if p["kind"] == "right_angle")
    assert "vuông tại A" in right["quote"] and "vuông góc" not in right["quote"]
    assert served(payload) == "SERVED"


def test_a_fabricated_metric_goal_on_a_simulation_only_source_is_not_served():
    raw = {**RAW_FACTS, "g": [{"c": 1, "t": "vol", "tgt": "ABCD.A'B'C'D'"}]}
    payload, _diag = validate_and_lower_compact_clause(ctx=build_compact_clause_context(SIM), raw_slm_json=raw,
                                                       closure_mode=V9_CLOSURE_MODE)
    assert payload is None or served(payload) != "SERVED"
