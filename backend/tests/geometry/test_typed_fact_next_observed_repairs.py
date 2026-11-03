"""C26 — exact repairs of wire shapes observed in live Gemini Run 3 (0 provider calls).

Every repair re-files only what the source states verbatim; every positive repair has an adversarial twin that must be
left untouched (and therefore still fail closed downstream). The last test replays the 64 captured Run 3 extractions.
"""
from copy import deepcopy
import json
from pathlib import Path

import pytest

from app.ai.typed_fact_next_extraction import _normalize_transport_payload, extract_typed_fact_next_v2, ReplayExtractor

BASE = ("Cho hình chóp S.ABCD có đáy ABCD là hình vuông cạnh 2, SA vuông góc với mặt phẳng (ABCD) và SA = 2. ")
SOLID = {"solid_id": "s1", "solid_type": "pyramid", "notation": "S.ABCD", "quote": "hình chóp S.ABCD"}
SQUARE = {"kind": "regular_polygon", "args": {"vertices": ["A", "B", "C", "D"], "side": "2"},
          "quote": "đáy ABCD là hình vuông cạnh 2", "solid_id": "s1"}
PERP = {"kind": "perpendicular_line_plane", "args": {"line": ["S", "A"], "plane": ["A", "B", "C", "D"]},
        "quote": "SA vuông góc với mặt phẳng (ABCD)", "solid_id": "s1"}
SA = {"kind": "segment_length", "args": {"segment": ["S", "A"], "value": "2"}, "quote": "SA = 2", "solid_id": "s1"}
SG = [{"goal_id": "sg1", "kind": "construct_object", "target_solid_id": "s1", "quote": "hình chóp S.ABCD"}]


def wire(text, premises, described=None, math_goals=None, solids=None):
    solids = deepcopy(solids or [SOLID])
    sg = [{**SG[0], "quote": solids[0]["quote"]}]
    out = {"schema_version": "typed-fact-next/2", "problem_text": text, "length_unit": "1",
           "solids": solids, "premises": deepcopy(premises), "derived_sections": [],
           "relations": [], "simulation_goals": sg, "math_goals": deepcopy(math_goals or [])}
    if described is not None:
        out["described_points"] = deepcopy(described)
    return out


def quotes(v):
    if isinstance(v, dict):
        for k, x in v.items():
            if k == "quote":
                yield x
            yield from quotes(x)
    elif isinstance(v, list):
        for x in v:
            yield from quotes(x)


def norm(w):
    out = _normalize_transport_payload(deepcopy(w))
    assert all(q in w["problem_text"] for q in quotes(out)), "a repair produced a non-verbatim quote"
    return out


# ── named vs described points ───────────────────────────────────────────────────────────────────────────────────────

KC02 = BASE + ("Gọi M là trung điểm của AB. Gọi N là trung điểm của SC. Tính khoảng cách từ tâm đường tròn ngoại "
               "tiếp tam giác ABN đến mặt phẳng (ABCD).")


def kc02_wire():
    return wire(KC02, [SQUARE, PERP, SA], described=[
        {"described_id": "m1", "kind": "midpoint", "quote": "M là trung điểm của AB", "segment": ["A", "B"]},
        {"described_id": "m2", "kind": "midpoint", "quote": "N là trung điểm của SC", "segment": ["S", "C"]},
        {"described_id": "m3", "kind": "circumcenter", "quote": "tâm đường tròn ngoại tiếp tam giác ABN",
         "polygon": ["A", "B", "@m2"]}],
        math_goals=[{"goal_id": "mg1", "kind": "measurement", "goal_type": "distance", "solid_id": "s1",
                     "target": {"point": "@m3", "plane": ["A", "B", "C", "D"]},
                     "quote": "Tính khoảng cách từ tâm đường tròn ngoại tiếp tam giác ABN đến mặt phẳng (ABCD)"}])


def test_a_point_the_source_names_becomes_a_premise_and_its_refs_become_the_label():
    out = norm(kc02_wire())
    mids = {p["args"]["point"]: p["args"]["segment"] for p in out["premises"] if p["kind"] == "midpoint"}
    assert mids == {"M": ["A", "B"], "N": ["S", "C"]}
    assert [d["described_id"] for d in out["described_points"]] == ["m3"]
    assert out["described_points"][0]["polygon"] == ["A", "B", "N"]
    assert extract_typed_fact_next_v2(KC02, ReplayExtractor({KC02: out})).code is None


def test_an_unnamed_or_unconvertible_described_point_is_left_alone():
    text = BASE + "Gọi O là tâm đường tròn ngoại tiếp tam giác SBC. Tính khoảng cách từ trung điểm của SB đến (SCD)."
    w = wire(text, [SQUARE, PERP, SA], described=[
        {"described_id": "o1", "kind": "circumcenter", "quote": "O là tâm đường tròn ngoại tiếp tam giác SBC",
         "polygon": ["S", "B", "C"]},
        {"described_id": "d1", "kind": "midpoint", "quote": "trung điểm của SB", "segment": ["S", "B"]}])
    out = norm(w)
    assert out["described_points"] == w["described_points"]          # no premise kind for a circumcenter; unnamed stays
    assert [p for p in out["premises"] if p["kind"] in ("midpoint", "circumcenter")] == []


def test_a_named_point_depending_on_an_unconverted_described_point_is_not_converted():
    text = BASE + "Gọi O là tâm đường tròn ngoại tiếp tam giác SBC. Gọi K là trung điểm của SO."
    w = wire(text, [SQUARE, PERP, SA], described=[
        {"described_id": "o1", "kind": "circumcenter", "quote": "O là tâm đường tròn ngoại tiếp tam giác SBC",
         "polygon": ["S", "B", "C"]},
        {"described_id": "k1", "kind": "midpoint", "quote": "K là trung điểm của SO", "segment": ["S", "@o1"]}])
    out = norm(w)
    assert out["described_points"] == w["described_points"]
    assert not any(p["kind"] == "midpoint" for p in out["premises"])


# ── square / side ───────────────────────────────────────────────────────────────────────────────────────────────────

SPLIT_SQUARE = {"kind": "regular_polygon", "args": {"vertices": ["A", "B", "C", "D"]}, "quote": "đáy ABCD là hình vuông",
                "solid_id": "s1"}
BARE_SIDE = {"kind": "segment_length", "args": {"segment": ["A", "B"], "value": "2"}, "quote": "cạnh 2", "solid_id": "s1"}


def test_a_split_square_side_is_merged_into_one_verbatim_polygon_premise():
    out = norm(wire(BASE, [SPLIT_SQUARE, BARE_SIDE, PERP, SA]))
    assert out["premises"][0] == SQUARE and BARE_SIDE not in out["premises"]


def test_a_square_filed_as_rectangle_is_the_regular_quadrilateral_and_duplicates_drop():
    rect = {**SPLIT_SQUARE, "kind": "rectangle"}
    assert norm(wire(BASE, [rect, BARE_SIDE, PERP, SA]))["premises"][0] == SQUARE
    assert [p["kind"] for p in norm(wire(BASE, [SQUARE, rect, PERP, SA]))["premises"]].count("rectangle") == 0


def test_a_real_rectangle_and_non_adjacent_or_conflicting_sides_are_left_alone():
    text = "Cho hình chóp S.ABCD có đáy ABCD là hình chữ nhật, SA = 2, cạnh 2 nằm trên AB."
    rect = {"kind": "rectangle", "args": {"vertices": ["A", "B", "C", "D"]}, "quote": "đáy ABCD là hình chữ nhật",
            "solid_id": "s1"}
    assert norm(wire(text, [rect]))["premises"] == [rect]
    far = "Cho hình chóp S.ABCD có đáy ABCD là hình vuông, SA = 2 và cạnh 2 là SA."
    w = wire(far, [SPLIT_SQUARE, BARE_SIDE])
    assert norm(w)["premises"] == w["premises"]                       # "cạnh 2" is not adjacent to the square clause
    conflict = wire(BASE.replace("cạnh 2", "cạnh 2") + "Cạnh AB bằng 3.",
                    [SQUARE, {**BARE_SIDE, "args": {"segment": ["A", "B"], "value": "3"}, "quote": "cạnh 2"}])
    assert len(norm(conflict)["premises"]) == 2                       # a different value is never silently dropped


def test_a_polygon_quote_missing_its_name_takes_only_the_adjacent_naming_clause():
    w = wire(BASE, [{**SQUARE, "quote": "hình vuông cạnh 2"}, PERP, SA])
    assert norm(w)["premises"][0]["quote"] == "đáy ABCD là hình vuông cạnh 2"


# ── restated premises ───────────────────────────────────────────────────────────────────────────────────────────────

def test_an_altitude_inferred_from_a_perpendicular_drops_but_a_stated_one_binds_to_its_solid():
    inferred = {"kind": "altitude", "args": {"apex": "S", "foot": "A"}, "quote": "SA vuông góc với mặt phẳng (ABCD)",
                "solid_id": "s1"}
    assert inferred not in norm(wire(BASE, [SQUARE, PERP, inferred, SA]))["premises"]
    text = "Cho hình chóp S.ABCD có đáy ABCD là hình vuông cạnh 2, đường cao SA = 2. Tính thể tích khối chóp S.ABCD."
    stated = {"kind": "altitude", "args": {"apex": "S", "foot": "A"}, "quote": "đường cao SA", "solid_id": "s1"}
    out = norm(wire(text, [SQUARE, stated, SA]))
    assert out["premises"][1]["quote"] == "hình chóp S.ABCD có đáy ABCD là hình vuông cạnh 2, đường cao SA"
    other_sentence = "Cho hình chóp S.ABCD có đáy ABCD là hình vuông cạnh 2. Biết đường cao SA = 2."
    out2 = norm(wire(other_sentence, [SQUARE, stated, SA]))
    assert out2["premises"][1]["quote"] == "đường cao SA"           # never across a sentence boundary


def test_a_height_written_as_a_named_segment_is_that_segment():
    text = "Cho hình lập phương MNPQ.M'N'P'Q' có MM' = 5. Tính thể tích khối lập phương MNPQ.M'N'P'Q'."
    cube = {"solid_id": "s1", "solid_type": "prism", "notation": "MNPQ.M'N'P'Q'", "quote": "hình lập phương MNPQ.M'N'P'Q'"}
    h = {"kind": "height", "args": {"value": "5", "solid": "s1"}, "quote": "MM' = 5", "solid_id": "s1"}
    out = norm(wire(text, [h], solids=[cube]))
    assert out["premises"] == [{**h, "kind": "segment_length", "args": {"segment": ["M", "M'"], "value": "5"}}]
    plain = {"kind": "height", "args": {"value": "5"}, "quote": "chiều cao bằng 5", "solid_id": "s1"}
    assert norm(wire("Cho hình lập phương MNPQ.M'N'P'Q' có chiều cao bằng 5.", [plain], solids=[cube]))["premises"] == [plain]


def test_gold_shaped_payloads_are_untouched():
    w = wire(KC02, [SQUARE, PERP, SA, {"kind": "midpoint", "args": {"point": "N", "segment": ["S", "C"]},
                                       "quote": "Gọi N là trung điểm của SC", "solid_id": "s1"}],
             described=[{"described_id": "h1", "kind": "circumcenter", "quote": "tâm đường tròn ngoại tiếp tam giác ABN",
                         "polygon": ["A", "B", "N"]}])
    assert norm(w) == w


# ── captured live Run 3 replay (offline, contaminated development data: a regression guard, not generalization) ──────

ROOT = Path(__file__).resolve().parents[3]
LIVE = ROOT / "docs/evaluation/geometry/runs/hybrid-live-validation/live-pilots-8853c4b0"


@pytest.mark.skipif(not LIVE.is_dir(), reason="Run 3 receipts absent")
def test_captured_run3_replay_serves_no_wrong_math_and_no_negative():
    import sys
    sys.path.insert(0, str(ROOT / "backend" / "scripts"))
    import run_s2_student_language_pilot as R

    specs = R.default_c21_pilot_specs()
    wrong, served_negative, false_refusals = [], [], []
    for study, fn in {"K-1": "k1-live.jsonl", "S-2": "s2-live.jsonl", "R-1": "r1-live.jsonl"}.items():
        cases = {c["id"]: c for c in json.loads(Path(specs[study]["corpus_path"]).read_text(encoding="utf-8"))["cases"]}
        for line in (LIVE / fn).read_text(encoding="utf-8").splitlines():
            row = json.loads(line)
            if row.get("type") != "row" or row.get("raw_extraction") is None:
                continue
            case = cases[row["case_id"]]
            obs, _ = R.observe(case["problem_text"],
                               ReplayExtractor({case["problem_text"]: _normalize_transport_payload(row["raw_extraction"])}))
            exp = row["expected"]
            if obs["status"] == "SERVED" and exp["outcome"] != "SERVED":
                served_negative.append(row["case_id"])
            if obs["status"] == "SERVED" and (obs.get("answers") != exp.get("expected_answers")
                                              or not obs.get("certificate_verified")):
                wrong.append(row["case_id"])
            if exp["outcome"] == "SERVED" and obs["status"] != "SERVED":
                false_refusals.append(row["case_id"])
    assert wrong == [] and served_negative == []
    assert len(false_refusals) <= 1, false_refusals                     # Run 3 live: 20/39; f60ae29e replay: 17/39
