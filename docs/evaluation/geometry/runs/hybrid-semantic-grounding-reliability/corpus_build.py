"""Builds `corpus.json` for run `hybrid-semantic-grounding-reliability` (no `app` import, no model).

Each case = Vietnamese source text + an AUTHORED Typed Facts extraction + the author's semantic label:
  expect        SERVE (every request answerable and the extraction answers all of them) | REFUSE
  requests      for SERVE: one oracle request per question fact id (exact value from `oracle.py`)
  source_requests  how many requests the SOURCE makes (multi-goal completeness), independent of the extraction
  refuse_codes  the registered acceptable refusal codes for a REFUSE case (anything else = wrong-code refusal)
  mechanism     which preregistered fix the case exercises (M1–M4), or "none" (measured, not targeted)
  extraction    "faithful" (facts say what the source says) or the kind of extraction error simulated

Authored facts measure the deterministic gate + planner + engine, NOT the LLM. Live extraction is NOT_MEASURED.
    python corpus_build.py      # writes corpus.json; refuses to overwrite a different file
"""
from __future__ import annotations

import json
import sys
from copy import deepcopy
from pathlib import Path

HERE = Path(__file__).resolve().parent

PYR_TEXT = "Cho hình chóp S.ABCD. Đáy ABCD là hình vuông cạnh 2. SA vuông góc với (ABCD). SA = 3."
PYR = [
    {"id": "f1", "kind": "solid", "role": "premise", "quotes": ["Cho hình chóp S.ABCD."], "solid": "S.ABCD", "solid_type": "pyramid"},
    {"id": "f2", "kind": "polygon_shape", "role": "premise", "quotes": ["Đáy ABCD là hình vuông cạnh 2."],
     "points": ["A", "B", "C", "D"], "shape": "square", "value": "2"},
    {"id": "f3", "kind": "perpendicular", "role": "premise", "quotes": ["SA vuông góc với (ABCD)."],
     "points_a": ["S", "A"], "points_b": ["A", "B", "C", "D"]},
    {"id": "f4", "kind": "length", "role": "premise", "quotes": ["SA = 3."], "points": ["S", "A"], "measure": "segment", "value": "3"},
]
CUBE_TEXT = "Cho hình lập phương ABCD.A'B'C'D' cạnh 2."
CUBE = [
    {"id": "f1", "kind": "solid", "role": "premise", "quotes": [CUBE_TEXT], "solid": "ABCD.A'B'C'D'", "solid_type": "cube"},
    {"id": "f2", "kind": "length", "role": "premise", "quotes": [CUBE_TEXT], "solid": "ABCD.A'B'C'D'", "measure": "edge", "value": "2"},
]
FIG = {"pyramid": (PYR_TEXT, PYR), "cube": (CUBE_TEXT, CUBE)}


def _labels(s):
    out = []
    for ch in s:
        if ch == "'":
            out[-1] += "'"
        else:
            out.append(ch)
    return out


# ── question facts (quote = the sentence or clause that asks) ───────────────────────────────────────────────────────
def q_desc_plane(qid, quote, seg, plane):
    return {"id": qid, "kind": "question", "role": "question", "quotes": [quote], "quantity": "distance",
            "point_kind": "midpoint", "points": _labels(seg), "points_b": _labels(plane)}
def q_desc_line(qid, quote, seg, line):
    return {"id": qid, "kind": "question", "role": "question", "quotes": [quote], "quantity": "distance",
            "point_kind": "midpoint", "points": _labels(seg), "points_b": _labels(line)}
def q_desc_ref(qid, quote, seg, ref):
    return {"id": qid, "kind": "question", "role": "question", "quotes": [quote], "quantity": "distance",
            "point_kind": "midpoint", "points": _labels(seg), "line_ref": ref}
def q_desc_len(qid, quote, seg, target):
    return {"id": qid, "kind": "question", "role": "question", "quotes": [quote], "quantity": "length",
            "point_kind": "midpoint", "points": _labels(seg), "points_b": [target]}
def q_dist(qid, quote, p, target):
    return {"id": qid, "kind": "question", "role": "question", "quotes": [quote], "quantity": "distance",
            "points_a": [p], "points_b": _labels(target)}
def q_len(qid, quote, seg):
    return {"id": qid, "kind": "question", "role": "question", "quotes": [quote], "quantity": "length", "points": _labels(seg)}
def q_vol(qid, quote, solid="S.ABCD"):
    return {"id": qid, "kind": "question", "role": "question", "quotes": [quote], "quantity": "volume", "solid": solid}
def inter(fid, quote, p1, p2):
    return {"id": fid, "kind": "intersection_line", "role": "premise", "quotes": [quote],
            "points_a": _labels(p1), "points_b": _labels(p2)}
def mid(fid, quote, name, seg):
    return {"id": fid, "kind": "point_def", "role": "premise", "quotes": [quote], "point": name,
            "point_kind": "midpoint", "points": _labels(seg)}
def proj(fid, quote, p, onto, at, role="premise"):
    return {"id": fid, "kind": "projection", "role": role, "quotes": [quote], "point": p, "points": _labels(onto), "at": at}


# ── oracle requests ─────────────────────────────────────────────────────────────────────────────────────────────────
def r_pp(rid, p, plane): return {"id": rid, "q": "dist_point_plane", "point": p, "plane": _labels(plane)}
def r_pl(rid, p, line): return {"id": rid, "q": "dist_point_line", "point": p, "line": ["named", _labels(line)]}
def r_pg(rid, p, a, b): return {"id": rid, "q": "dist_point_line", "point": p, "line": ["planes", _labels(a), _labels(b)]}
def r_len(rid, a, b): return {"id": rid, "q": "length", "a": a, "b": b}
def r_vol(rid): return {"id": rid, "q": "volume_pyramid", "apex": "S", "base": ["A", "B", "C", "D"]}
MSC = ["mid", "S", "C"]

CASES = []


def case(cid, group, sentence, facts, expect, *, figure="pyramid", requests=(), source_requests=1, refuse_codes=(),
         mechanism="none", extraction="faithful", note=""):
    text, premise = FIG[figure]
    CASES.append({"id": cid, "group": group, "figure": figure, "text": f"{text} {sentence}",
                  "payload": {"facts": deepcopy(premise) + facts}, "expect": expect, "requests": list(requests),
                  "source_requests": source_requests, "refuse_codes": list(refuse_codes), "mechanism": mechanism,
                  "extraction": extraction, "note": note})


# A — semantic equivalence: same request, different wording; faithful extraction ⇒ must serve
s = "Tính khoảng cách từ trung điểm của SC đến (SAB)."
case("A01-desc-plane-imperative", "A", s, [q_desc_plane("q", s, "SC", "SAB")], "SERVE", requests=[r_pp("q", MSC, "SAB")])
s = "Khoảng cách từ trung điểm của SC đến (SAB) bằng bao nhiêu?"
case("A02-desc-plane-bao-nhieu", "A", s, [q_desc_plane("q", s, "SC", "SAB")], "SERVE", requests=[r_pp("q", MSC, "SAB")])
s = "Tìm khoảng cách từ trung điểm của SC tới mặt phẳng (SAB)."
case("A03-desc-plane-tim-toi-mp", "A", s, [q_desc_plane("q", s, "SC", "SAB")], "SERVE", requests=[r_pp("q", MSC, "SAB")])
s1, s2 = "Gọi M là trung điểm SC.", "Tính khoảng cách từ M đến (SAB)."
case("A04-named-midpoint-then-ask", "A", f"{s1} {s2}", [mid("f5", s1, "M", "SC"), q_dist("q", s2, "M", "SAB")], "SERVE",
     requests=[r_pp("q", MSC, "SAB")])
s = "Tính độ dài đoạn nối trung điểm của SC với A."
case("A05-desc-length", "A", s, [q_desc_len("q", s, "SC", "A")], "SERVE", requests=[r_len("q", MSC, "A")])
s = "Tính độ dài đoạn nối A với trung điểm của SC."
case("A06-desc-length-reversed", "A", s, [q_desc_len("q", s, "SC", "A")], "SERVE", requests=[r_len("q", MSC, "A")],
     mechanism="M3", note="reported false refusal (operand order)")
s = "Độ dài đoạn nối trung điểm của SC với A bằng bao nhiêu?"
case("A07-desc-length-bao-nhieu", "A", s, [q_desc_len("q", s, "SC", "A")], "SERVE", requests=[r_len("q", MSC, "A")],
     mechanism="M3", note="reported false refusal (question form)")
s = "Độ dài đoạn nối điểm A với trung điểm của cạnh SC bằng bao nhiêu?"
case("A08-desc-length-reversed-bao-nhieu", "A", s, [q_desc_len("q", s, "SC", "A")], "SERVE", requests=[r_len("q", MSC, "A")],
     mechanism="M3")
s = "Tính khoảng cách từ C đến (SAB)."
case("A09-named-plane", "A", s, [q_dist("q", s, "C", "SAB")], "SERVE", requests=[r_pp("q", "C", "SAB")])
s = "Khoảng cách từ điểm C tới mặt phẳng (SAB) bằng bao nhiêu?"
case("A10-named-plane-bao-nhieu", "A", s, [q_dist("q", s, "C", "SAB")], "SERVE", requests=[r_pp("q", "C", "SAB")])
s = "Tính khoảng cách từ A đến SC."
case("A11-named-line", "A", s, [q_dist("q", s, "A", "SC")], "SERVE", requests=[r_pl("q", "A", "SC")])
s = "Khoảng cách từ A đến đường thẳng SC bằng bao nhiêu?"
case("A12-named-line-bao-nhieu", "A", s, [q_dist("q", s, "A", "SC")], "SERVE", requests=[r_pl("q", "A", "SC")])
s = "Điểm nằm chính giữa S và C cách (SAB) bao xa?"
case("A13-paraphrase-chinh-giua", "A", s, [q_desc_plane("q", s, "SC", "SAB")], "SERVE", requests=[r_pp("q", MSC, "SAB")],
     note="free paraphrase outside every closed grammar: a refusal here is a measured false refusal, not targeted")
s = "Cho tôi xem A cách đường thẳng SC bao xa."
case("A14-paraphrase-bao-xa", "A", s, [q_dist("q", s, "A", "SC")], "SERVE", requests=[r_pl("q", "A", "SC")],
     note="free paraphrase, not targeted")

# B — semantic contrast: near-identical wording, different request; the extraction types the NEAR request
s = "Tính bình phương độ dài đoạn nối trung điểm của SC với A."
case("B01-squared-length", "B", s, [q_desc_len("q", s, "SC", "A")], "REFUSE",
     refuse_codes=["NOT_ASKED_IN_SOURCE", "SOURCE_OBJECT_MISMATCH", "QUESTION_CONTEXT_UNSUPPORTED"], extraction="drops a modifier")
s = "Tính hai lần khoảng cách từ trung điểm của SC đến (SAB)."
case("B02-twice-distance", "B", s, [q_desc_plane("q", s, "SC", "SAB")], "REFUSE",
     refuse_codes=["NOT_ASKED_IN_SOURCE", "QUESTION_CONTEXT_UNSUPPORTED"], extraction="drops a modifier")
s = "Tính khoảng cách từ trung điểm của SC đến đoạn BD."
case("B03-segment-not-line", "B", s, [q_desc_line("q", s, "SC", "BD")], "REFUSE", refuse_codes=["SOURCE_OBJECT_MISMATCH"],
     extraction="types a segment as a line")
s = "Tìm hình chiếu vuông góc của A lên SC."
case("B04-projection-not-distance", "B", s, [q_dist("q", s, "A", "SC")], "REFUSE",
     refuse_codes=["SOURCE_OBJECT_MISMATCH", "NOT_ASKED_IN_SOURCE"], extraction="types a projection request as a distance")
s = "Dựng hình chiếu H của A lên SC."
case("B05-construct-projection", "B", s, [proj("f5", s, "A", "SC", "H")], "SERVE", source_requests=1,
     note="construction-only request (no value): SERVE means a construction scene with no answer; "
          "ISSUE-ARCH-CONSTRUCTION-WORDING-BREADTH — measured, not targeted")
s = "Gọi H là hình chiếu của A lên SC."
case("B06-define-projection", "B", s, [proj("f5", s, "A", "SC", "H")], "SERVE", source_requests=0,
     note="a definition, no request: construction scene, no answer")
s = "Tính khoảng cách từ trung điểm của SC đến (SAB) khi M thay đổi trên SC."
case("B07-varying-point", "B", s, [q_desc_plane("q", s, "SC", "SAB")], "REFUSE",
     refuse_codes=["NOT_ASKED_IN_SOURCE", "QUESTION_CONTEXT_UNSUPPORTED", "CONDITIONAL_CLAUSE", "UNKNOWN_LABEL"],
     extraction="drops a scope modifier")

# C — entity / reference grounding
s = "Tính khoảng cách từ trung điểm của SC đến (SABC)."
case("C01-four-label-nonplane-desc", "C", s, [q_desc_plane("q", s, "SC", "SAB")], "REFUSE",
     refuse_codes=["SOURCE_OBJECT_MISMATCH"], mechanism="M2", extraction="shortens (SABC) to (SAB)",
     note="reported false serve: S, A, B, C are not coplanar")
s = "Tính khoảng cách từ D đến (SABC)."
case("C02-four-label-nonplane-named", "C", s, [q_dist("q", s, "D", "SAB")], "REFUSE",
     refuse_codes=["SOURCE_OBJECT_MISMATCH"], mechanism="M2", extraction="shortens (SABC) to (SAB)")
s = "Tính khoảng cách từ trung điểm của SC đến (ABCD)."
case("C03-four-label-base-desc", "C", s, [q_desc_plane("q", s, "SC", "ABC")], "SERVE", requests=[r_pp("q", MSC, "ABCD")],
     mechanism="M2", extraction="names the base by three of its labels",
     note="must stay served: (ABCD) is the declared base, so three of its labels name the same plane")
s = "Tính khoảng cách từ S đến (ABCD)."
case("C04-four-label-base-named", "C", s, [q_dist("q", s, "S", "ABCD")], "SERVE", requests=[r_pp("q", "S", "ABCD")],
     mechanism="M2")
s = "Tính khoảng cách từ trung điểm của SC đến (SACD)."
case("C05-four-label-nonplane-other", "C", s, [q_desc_plane("q", s, "SC", "SAD")], "REFUSE",
     refuse_codes=["SOURCE_OBJECT_MISMATCH"], mechanism="M2", extraction="shortens (SACD) to (SAD)")
s = "Tính khoảng cách từ trung điểm của SC đến (SAB)."
case("C06-wrong-target-plane", "C", s, [q_desc_plane("q", s, "SC", "SAD")], "REFUSE", refuse_codes=["SOURCE_OBJECT_MISMATCH"],
     extraction="wrong plane")
case("C07-wrong-described-point", "C", s, [q_desc_plane("q", s, "SB", "SAB")], "REFUSE", refuse_codes=["SOURCE_OBJECT_MISMATCH"],
     extraction="wrong descriptor operands")
s1, s2 = "Tìm giao tuyến của (SAB) và (SCD).", "Tính khoảng cách từ trung điểm của SC đến giao tuyến của (SAB) và (SCD)."
case("C08-result-line-pyramid", "C", f"{s1} {s2}", [inter("g", s1, "SAB", "SCD"), q_desc_ref("q", s2, "SC", "g")], "SERVE",
     requests=[r_pg("q", MSC, "SAB", "SCD")], source_requests=2,
     note="source asks to find the intersection line too; the line is constructed and shown, its value-free request is answered by construction")
s1, s2 = "Tìm giao tuyến của (ABB') và (BCC').", "Tính khoảng cách từ trung điểm của A'C' đến giao tuyến của (ABB') và (BCC')."
case("C09-result-line-cube", "C", f"{s1} {s2}", [inter("g", s1, "ABB'", "BCC'"), q_desc_ref("q", s2, "A'C'", "g")], "SERVE",
     figure="cube", requests=[r_pg("q", ["mid", "A'", "C'"], "ABB'", "BCC'")], source_requests=2, mechanism="M4",
     note="ISSUE-ARCH-LINE-REF-PREMISE-GRAMMAR-CUBE: cube premise outside the closed line_ref premise grammar")
s1, s2 = "Tìm giao tuyến của (ABC) và (A'B'C').", "Tính khoảng cách từ trung điểm của AC' đến giao tuyến của (ABC) và (A'B'C')."
case("C10-result-line-cube-parallel", "C", f"{s1} {s2}", [inter("g", s1, "ABC", "A'B'C'"), q_desc_ref("q", s2, "AC'", "g")],
     "REFUSE", figure="cube", refuse_codes=["PARALLEL_NO_INTERSECTION", "PARALLEL_PLANES"], mechanism="M4",
     note="deviation D-1 of goal-directed-function-discovery: right refusal, wrong code before the fix")
s = "Tính khoảng cách từ trung điểm của C'D' đến (ABB'A')."
case("C11-cube-lateral-face-four-labels", "C", s, [q_desc_plane("q", s, "C'D'", "ABB'")], "SERVE", figure="cube",
     requests=[r_pp("q", ["mid", "C'", "D'"], "ABB'A'")], mechanism="M2", extraction="names a lateral face by three labels",
     note="must stay served: (ABB'A') is a face of the declared cube")
s = "Tính khoảng cách từ trung điểm của C'D' đến (ABC'D')."
case("C12-cube-diagonal-plane-four-labels", "C", s, [q_desc_plane("q", s, "C'D'", "ABC'")], "SERVE", figure="cube",
     requests=[r_pp("q", ["mid", "C'", "D'"], "ABC'D'")], mechanism="M2",
     note="(ABC'D') is a real plane but not a declared face; serving needs a coplanarity proof the gate does not have")

# D — multi-goal completeness
s = "Tính khoảng cách từ trung điểm của SC đến (SAB) và độ dài SC."
case("D01-two-asks-one-extracted", "D", s, [q_desc_plane("q", s, "SC", "SAB")], "REFUSE", source_requests=2,
     refuse_codes=["REQUEST_NOT_ANSWERED"], mechanism="M1", extraction="drops the second request")
case("D02-two-asks-both-extracted", "D", s, [q_desc_plane("q1", s, "SC", "SAB"), q_len("q2", s, "SC")], "SERVE",
     source_requests=2, requests=[r_pp("q1", MSC, "SAB"), r_len("q2", "S", "C")], mechanism="M1")
s = "Tính khoảng cách từ trung điểm của SC đến (SAB), sau đó tính thể tích khối chóp S.ABCD."
case("D03-then-volume-one-extracted", "D", s, [q_desc_plane("q", s, "SC", "SAB")], "REFUSE", source_requests=2,
     refuse_codes=["REQUEST_NOT_ANSWERED"], mechanism="M1", extraction="drops the follow-up request")
case("D04-then-volume-both-extracted", "D", s, [q_desc_plane("q1", s, "SC", "SAB"), q_vol("q2", s)], "SERVE",
     source_requests=2, requests=[r_pp("q1", MSC, "SAB"), r_vol("q2")], mechanism="M1")
s1, s2 = "Tính khoảng cách từ trung điểm của SC đến (SAB).", "Sau đó tính thể tích khối chóp S.ABCD."
case("D05-next-sentence-volume-one-extracted", "D", f"{s1} {s2}", [q_desc_plane("q", s1, "SC", "SAB")], "REFUSE",
     source_requests=2, refuse_codes=["REQUEST_NOT_ANSWERED"], mechanism="M1", extraction="drops the second sentence")
case("D06-next-sentence-volume-both-extracted", "D", f"{s1} {s2}", [q_desc_plane("q1", s1, "SC", "SAB"), q_vol("q2", s2)],
     "SERVE", source_requests=2, requests=[r_pp("q1", MSC, "SAB"), r_vol("q2")], mechanism="M1")
s = "Tính khoảng cách từ C đến (SAB) và AC."
case("D07-named-trailing-object", "D", s, [q_dist("q", s, "C", "SAB")], "REFUSE", source_requests=2,
     refuse_codes=["REQUEST_NOT_ANSWERED"], mechanism="M1", extraction="drops a listed object")
s = "Tính khoảng cách từ C đến (SAB) và độ dài SC."
case("D08-named-two-asks-one-extracted", "D", s, [q_dist("q", s, "C", "SAB")], "REFUSE", source_requests=2,
     refuse_codes=["REQUEST_NOT_ANSWERED"], mechanism="M1", extraction="drops the second request")
case("D09-named-two-asks-both-extracted", "D", s, [q_dist("q1", s, "C", "SAB"), q_len("q2", s, "SC")], "SERVE",
     source_requests=2, requests=[r_pp("q1", "C", "SAB"), r_len("q2", "S", "C")], mechanism="M1")
s = "Tính SC và thể tích khối chóp S.ABCD."
case("D10-length-and-volume-one-extracted", "D", s, [q_len("q", s, "SC")], "REFUSE", source_requests=2,
     refuse_codes=["REQUEST_NOT_ANSWERED"], mechanism="M1", extraction="drops the second request")
case("D11-length-and-volume-both-extracted", "D", s, [q_len("q1", s, "SC"), q_vol("q2", s)], "SERVE", source_requests=2,
     requests=[r_len("q1", "S", "C"), r_vol("q2")], mechanism="M1")
s = "Tính khoảng cách từ trung điểm của SC đến (SAB) rồi suy ra thể tích khối chóp S.ABCD."
case("D12-roi-suy-ra-one-extracted", "D", s, [q_desc_plane("q", s, "SC", "SAB")], "REFUSE", source_requests=2,
     refuse_codes=["REQUEST_NOT_ANSWERED", "QUESTION_CONTEXT_UNSUPPORTED"], mechanism="M1", extraction="drops the follow-up")
s1, s2 = "Tính khoảng cách từ trung điểm của SC đến (SAB).", "Tính khoảng cách từ trung điểm của SC đến BD."
case("D13-two-sentences-both-extracted", "D", f"{s1} {s2}", [q_desc_plane("q1", s1, "SC", "SAB"), q_desc_line("q2", s2, "SC", "BD")],
     "SERVE", source_requests=2, requests=[r_pp("q1", MSC, "SAB"), r_pl("q2", MSC, "BD")])
case("D14-two-sentences-one-extracted", "D", f"{s1} {s2}", [q_desc_plane("q1", s1, "SC", "SAB")], "REFUSE", source_requests=2,
     refuse_codes=["REQUEST_NOT_ANSWERED"], mechanism="M1", extraction="drops the second sentence")
s = "Tính khoảng cách từ A đến SC và thể tích khối chóp S.ABCD."
case("D15-aux-line-and-volume-one-extracted", "D", s, [q_dist("q", s, "A", "SC")], "REFUSE", source_requests=2,
     refuse_codes=["REQUEST_NOT_ANSWERED"], mechanism="M1", extraction="drops the second request (auxiliary distance path)")

# E — negative / adversarial (faithful or flawed extraction; the source does not license an answer)
s = "Nếu SA = 3 thì tính khoảng cách từ trung điểm của SC đến (SAB)."
case("E01-conditional", "E", s, [q_desc_plane("q", s, "SC", "SAB")], "REFUSE", refuse_codes=["CONDITIONAL_CLAUSE"])
s = "Khoảng cách từ trung điểm của SC đến (SAB) không phải là 2."
case("E02-negated", "E", s, [q_desc_plane("q", s, "SC", "SAB")], "REFUSE",
     refuse_codes=["NEGATED_CLAUSE", "NOT_ASKED_IN_SOURCE", "QUESTION_CONTEXT_UNSUPPORTED"])
s = "Chứng minh rằng khoảng cách từ trung điểm của SC đến (SAB) bằng 1."
case("E03-proof-goal", "E", s, [q_desc_plane("q", s, "SC", "SAB")], "REFUSE", refuse_codes=["GOAL_CLAUSE_NOT_PREMISE"])
s = "Tính khoảng cách từ trung điểm của SC đến (SAB), làm tròn đến hàng phần trăm."
case("E04-rounding", "E", s, [q_desc_plane("q", s, "SC", "SAB")], "REFUSE", refuse_codes=["QUESTION_CONTEXT_UNSUPPORTED"])
s = "Tính khoảng cách từ trung điểm của SC đến (SAB) và diện tích toàn phần của hình chóp."
case("E05-unsupported-second-quantity", "E", s, [q_desc_plane("q", s, "SC", "SAB")], "REFUSE", source_requests=2,
     refuse_codes=["REQUEST_NOT_ANSWERED", "QUESTION_CONTEXT_UNSUPPORTED"], mechanism="M1",
     extraction="drops an unsupported request")
s = "SB = 5. Tính khoảng cách từ trung điểm của SC đến (SAB)."
case("E06-contradiction", "E", s, [{"id": "f9", "kind": "length", "role": "premise", "quotes": ["SB = 5."], "points": ["S", "B"],
                                    "measure": "segment", "value": "5"}, q_desc_plane("q", s.split(". ", 1)[1], "SC", "SAB")],
     "REFUSE", refuse_codes=["INCONSISTENT_FACTS"])
s = "Tính khoảng cách từ trung điểm của SC đến (SAB)."
case("E07-quote-not-in-source", "E", s, [q_desc_plane("q", "Tính khoảng cách từ trung điểm của SC đến (SBC).", "SC", "SAB")],
     "REFUSE", refuse_codes=["QUOTE_NOT_IN_SOURCE"], extraction="invented quote")
s = "Tính khoảng cách từ trung điểm của SE đến (SAB)."
case("E08-unknown-label", "E", s, [q_desc_plane("q", s, "SE", "SAB")], "REFUSE", refuse_codes=["UNKNOWN_LABEL"])
s = "Hãy chỉ ra rằng khoảng cách từ trung điểm của SC đến (SAB) bằng 1."
case("E09-show-that", "E", s, [q_desc_plane("q", s, "SC", "SAB")], "REFUSE", refuse_codes=["GOAL_CLAUSE_NOT_PREMISE"])
s = "Tính khoảng cách từ trung điểm của SC đến (SAB). Tính lại khi SA = 5."
case("E10-changed-scope-follow-up", "E", s, [q_desc_plane("q", "Tính khoảng cách từ trung điểm của SC đến (SAB).", "SC", "SAB")],
     "REFUSE", source_requests=2, refuse_codes=["QUESTION_CONTEXT_UNSUPPORTED", "QUESTION_LOCAL_GIVEN_CONFLICT",
                                                "REQUEST_NOT_ANSWERED", "CONDITIONAL_CLAUSE"])


def main() -> int:
    ids = [c["id"] for c in CASES]
    assert len(ids) == len(set(ids))
    for c in CASES:
        qids = [f["id"] for f in c["payload"]["facts"] if f["kind"] == "question"]
        if c["expect"] == "SERVE":
            assert sorted(r["id"] for r in c["requests"]) == sorted(qids), c["id"]
    out = {"run": "hybrid-semantic-grounding-reliability", "status": "PREREGISTERED_DEVELOPMENT_NOT_HELD_OUT",
           "author": "implementing agent (same as fixer) — see preregistration.md; unseen split authored separately",
           "cases": CASES}
    text = json.dumps(out, ensure_ascii=False, indent=1) + "\n"
    target = HERE / "corpus.json"
    if target.exists() and target.read_text(encoding="utf-8") != text:
        print("corpus.json exists with different content — refusing to overwrite", file=sys.stderr)
        return 1
    target.write_text(text, encoding="utf-8")
    print(f"{len(CASES)} cases")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
