"""D-10 (run `hybrid-v2-nl-certificates-e2e`): a point–line distance is PRESENTED as the asked d(P, line), not as the
derived foot segment d(P, H). Presentation only: the value, the foot, the witness and the subjects are unchanged and the
numerical authority stays in the deterministic backend. Expected values come from the independent oracle of
`hybrid_compiler_benchmark`, never from engine output. Authored DEV tests (not an independent holdout)."""
from __future__ import annotations

import json
from fractions import Fraction as F

from app.ai.function_route import _dich_khoang_cach_diem_duong
from tests.geometry import hybrid_compiler_benchmark as HB
from tests.geometry.test_hybrid_goal_decomposition import _dist, _problem

S, B, D, O = HB.S, HB.B, HB.D, HB.O


def _result(r):
    objs = {o["id"]: o for o in r.scene3d["objects"]}
    q = next(o for o in objs.values() if o.get("producer") == "measure.distance")
    ev = next(e for e in r.scene3d["events"] if e.get("object") == q["id"])
    return objs, q, ev


def _served(case):
    r = HB.run(case, "facts")
    assert r.status == "SERVED", (r.code, r.reason)
    return r


def test_result_is_named_by_the_asked_line():
    r = _served(_problem(_dist("Tính khoảng cách từ S đến BD.", "S", "BD")))
    objs, q, ev = _result(r)
    assert (q["notation"], q["reference"], q["label"]) == ("d(S, BD)", "d(S, BD)", "Khoảng cách giữa S và BD")
    assert q["formula"]["text"] == "d(S, BD) = √11" and ev["learner_text"].endswith("d(S, BD) = √11.")
    assert HB.answer_square(r.answers["q"]) == HB.dist2_point_line(S, B, D)
    # the foot stays a construction step that explains d = SH; it is not the goal's name
    foot = next(e for e in r.scene3d["events"] if e.get("object") == "H")
    assert foot["learner_text"] == "Dựng H: hình chiếu của S lên BD, nên d(S, BD) = SH."
    assert "H" not in q["notation"] and q["annotation"]["subject_ids"] == ["S", "H"]    # segment still drawn S–H
    assert r.scene3d["formation"]["steps"][ev["step_index"]]["learner_text"] == ev["learner_text"]
    # the answer appears only in the readout: construction steps never carry it (Mode A hides, Mode B shows once)
    assert "√11" not in json.dumps([e["learner_text"] for e in r.scene3d["events"] if e is not ev])


def test_renamed_points_and_foot_label_clash():
    t, n, q_ = HB._v(0, 0, 3), HB._v(2, 0, 0), HB._v(0, 2, 0)
    r = _served(_problem(_dist("Tính khoảng cách từ T đến NQ.", "T", "NQ"), base=HB._square("TMNPQ")))
    _, q, _ = _result(r)
    assert q["notation"] == "d(T, NQ)"
    assert HB.answer_square(r.answers["q"]) == HB.dist2_point_line(t, n, q_)
    # H already names another point of the text ⇒ the foot is H1, the asked quantity still reads d(S, BD)
    r = _served(_problem(HB._mid("f5", "H", "S", "C"), _dist("Tính khoảng cách từ S đến BD.", "S", "BD")))
    objs, q, _ = _result(r)
    assert r.planner["auxiliary"][0]["label"] == "H1" and q["notation"] == "d(S, BD)"
    assert objs["H1"]["role"] == "Điểm dựng phụ" or objs["H1"]["perpendicular_witness"]["from"] == "S"


def test_point_on_the_line_is_zero_and_never_misnamed():
    r = _served(_problem(HB._ill("f5", "O", "AC", "BD"), _dist("Tính khoảng cách từ O đến BD.", "O", "BD")))
    _, q, _ = _result(r)
    assert r.answers["q"] == "0" and q["notation"] in ("d(O, BD)", "d(O, H)")


def test_two_goals_each_named_by_its_own_line():
    r = _served(_problem(_dist("Tính khoảng cách từ S đến BD.", "S", "BD", fid="q"),
                         _dist("Tính khoảng cách từ C đến SB.", "C", "SB", fid="r")))
    names = sorted(o["notation"] for o in r.scene3d["objects"] if o.get("producer") == "measure.distance")
    assert names == ["d(C, SB)", "d(S, BD)"]


def _scene(r):
    return json.loads(json.dumps(r.scene3d))


def test_no_witness_or_wrong_foot_keeps_the_original_wording():
    """Nothing is inferred: without a verified perpendicular witness from that very point the result is not renamed."""
    r = _served(_problem(_dist("Tính khoảng cách từ S đến BD.", "S", "BD")))
    aux = tuple(r.planner["auxiliary"])
    for tamper in (lambda h: h.pop("perpendicular_witness"), lambda h: h["perpendicular_witness"].update({"from": "A"})):
        c = _scene(r)
        tamper(next(o for o in c["objects"] if o["id"] == "H"))
        c["objects"] = [o for o in c["objects"]]
        before = json.dumps(c, sort_keys=True)
        # the scene carries the renamed result already; rebuild the unrenamed one to feed the presenter
        q = next(o for o in c["objects"] if o.get("producer") == "measure.distance")
        q["notation"] = "d(S, H)"
        _dich_khoang_cach_diem_duong(c, aux)
        assert q["notation"] == "d(S, H)", before


def test_refusal_carries_no_scene_and_no_answer():
    r = HB.run(_problem(_dist("Tính khoảng cách từ S đến BC.", "S", "BD")), "facts")
    assert r.status == "REFUSED" and not r.scene3d and not r.answers
