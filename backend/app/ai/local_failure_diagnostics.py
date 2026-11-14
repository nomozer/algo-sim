"""Clause-level failure localization of the local-first route (run `semantic-failure-safe-image-segmentation`).

DIAGNOSTICS ONLY: nothing here produces a fact, changes a decision or reaches the planner. It reads what the parser,
the Source Gate and the hybrid route already decided and answers WHERE the information was first lost, which layer
detected it and which layer decided the refusal — separating the ROOT CAUSE from the TERMINAL reason (e.g. root
`UNRECOGNIZED_RELATION`, terminal `LIVE_AI_DISABLED`).

Clause types are read from closed lexical cues (a label for the diagnosis, never a geometric fact). Refusal codes are
grouped with the product's one canonical grouping (`hybrid_preview.classify_refusal`), not a second code system.
Computed on refusals only; spans are offsets into the normalized text the parser read.
"""
from __future__ import annotations

import re
from typing import Any

DIAGNOSTICS_VERSION = "local-failure-diagnostics/1"

_LBL = r"[A-Z][0-9]*['′]?"
_TYPES: tuple[tuple[str, re.Pattern[str]], ...] = tuple((name, re.compile(pat, re.IGNORECASE)) for name, pat in (
    ("MULTIPLE_CHOICE_OPTIONS", r"^\s*[A-D]\s*[.)]\s"),
    ("NON_PROBLEM_TEXT", r"\b(?:trang\s+\d+|mã\s+đề|hết\s*$)"),
    ("PROOF_REQUEST", r"chứng\s+minh"),
    ("CONSTRUCTION_GOAL", r"(?:xác\s+định|dựng|vẽ|tìm)\s+(?:\S+\s+){0,3}?(?:thiết\s+diện|giao\s+tuyến|giao\s+điểm|hình\s+chiếu|đoạn\s+vuông\s+góc\s+chung)"),
    ("MEASUREMENT_GOAL", r"(?:tính|tìm|bằng\s+bao\s+nhiêu|là\s*:?\s*$|bằng\s*:?\s*$)|(?:thể\s+tích|diện\s+tích|khoảng\s+cách|độ\s+dài|tỉ\s+số|bán\s+kính|côsin|cosin)[^.]*(?:bằng|là)\s*:?\s*$"),
    ("PLANE_DEFINITION", r"(?:gọi\s+\([^)]+\)\s+là\s+mặt\s+phẳng|mặt\s+phẳng\s+\([^)]+\)\s+(?:đi\s+qua|qua|chứa)|qua\s+" + _LBL + r"\s+(?:kẻ|dựng)\s+mặt\s+phẳng)"),
    ("POINT_DEFINITION", r"(?:gọi|lấy)\s+(?:điểm\s+)?" + _LBL + r"(?:\s*,\s*" + _LBL + r")*\s+(?:là|lần\s+lượt|thuộc|trên)|" + _LBL + r"\s+là\s+(?:trung\s+điểm|trọng\s+tâm|hình\s+chiếu|giao\s+điểm|chân)|sao\s+cho"),
    ("GEOMETRIC_OBJECT_DECLARATION", r"(?:cho|xét)\s+(?:hình|khối)\s+(?:chóp|lăng\s+trụ|hộp|lập\s+phương|tứ\s+diện)|^\s*(?:hình|khối)\s+(?:chóp|lăng\s+trụ|hộp|lập\s+phương|tứ\s+diện)"),
    ("PERPENDICULAR_RELATION", r"vuông\s+góc|⊥"),
    ("PARALLEL_RELATION", r"song\s+song|∥"),
    ("LENGTH_ANGLE_CONSTRAINT", r"=|\bbằng\s+\S*\d|°|\bgóc\b"),
    ("GEOMETRIC_PROPERTY", r"\b(?:là\s+)?(?:hình\s+vuông|hình\s+chữ\s+nhật|hình\s+thoi|hình\s+thang|hình\s+bình\s+hành|tam\s+giác\s+(?:đều|vuông|cân)|lục\s+giác|đều|cân\s+tại|vuông\s+tại)\b"),
    ("INCIDENCE_RELATION", r"\b(?:thuộc|nằm\s+trên|nằm\s+trong|đi\s+qua|cắt)\b"),
    ("FIGURE_REFERENCE", r"hình\s+vẽ|tham\s+khảo\s+hình|như\s+hình"),
))
#: root cause of a clause the parser could not read, by its primary type
_ROOT_OF_TYPE = {
    "PROOF_REQUEST": "UNRECOGNIZED_GOAL", "CONSTRUCTION_GOAL": "UNRECOGNIZED_GOAL", "MEASUREMENT_GOAL": "UNRECOGNIZED_GOAL",
    "PLANE_DEFINITION": "UNRECOGNIZED_GEOMETRIC_ENTITY", "POINT_DEFINITION": "UNRECOGNIZED_GEOMETRIC_ENTITY",
    "GEOMETRIC_OBJECT_DECLARATION": "UNRECOGNIZED_GEOMETRIC_ENTITY",
    "PERPENDICULAR_RELATION": "UNRECOGNIZED_RELATION", "PARALLEL_RELATION": "UNRECOGNIZED_RELATION",
    "LENGTH_ANGLE_CONSTRAINT": "UNRECOGNIZED_RELATION", "GEOMETRIC_PROPERTY": "UNRECOGNIZED_RELATION",
    "INCIDENCE_RELATION": "UNRECOGNIZED_RELATION", "FIGURE_REFERENCE": "INCOMPLETE_FACT_EXTRACTION",
    "MULTIPLE_CHOICE_OPTIONS": "INCOMPLETE_FACT_EXTRACTION", "NON_PROBLEM_TEXT": "INCOMPLETE_FACT_EXTRACTION",
}
#: precedence when several clauses are unread: the earliest definitional loss explains later goals
_PRIORITY = ("UNSUPPORTED_GOAL_FUNCTION", "FREE_POINT_UNDERDETERMINED", "UNSUPPORTED_POINT_CONSTRUCTION",
             "DESCRIBED_POINT_IN_PREMISE_UNSUPPORTED", "UNRESOLVED_REFERENCE", "UNRECOGNIZED_GEOMETRIC_ENTITY",
             "UNRECOGNIZED_RELATION", "INCOMPLETE_FACT_EXTRACTION", "UNRECOGNIZED_GOAL")
#: (compositional-semantics-simulation-goals) clause shapes the parser deliberately leaves unread, each with its own cause:
#: a point only said to lie ON an object (no ratio, no distance) is not unique; a reflection is no registered construction;
#: an UNNAMED described point standing as a premise operand ("… trùng với trọng tâm của tam giác ABC") is outside R-1.
_FREE_POINT = re.compile(r"(?<![\w'])[A-Z][0-9]*'?\s+(?:là\s+(?:một\s+)?điểm\s+(?:di\s+động\s+)?)?(?:thuộc|nằm\s+trên)\s+"
                         r"(?:cạnh|đoạn(?:\s+thẳng)?|đường\s+thẳng|tia)\s+[A-Z][0-9]*'?[A-Z]", re.IGNORECASE)
_FIXES_POSITION = re.compile(r"sao\s+cho|th[ỏo]a\s+mãn|cách\s|=|\btỉ\s+số|trung\s+điểm", re.IGNORECASE)
_REFLECTION = re.compile(r"đối\s+xứng", re.IGNORECASE)
_DESCRIBED_IN_PREMISE = re.compile(r"trùng\s+với\s+(?:trung\s+điểm|trọng\s+tâm|trực\s+tâm|tâm|giao\s+điểm)(?:\s+của)?\s", re.IGNORECASE)
_SCALE_LENGTH = re.compile(r"(?:=|bằng|cạnh|dài|cao)\s*(?:\d|√|a\b|\d*a\b)", re.IGNORECASE)


def _clause_root(text: str) -> str | None:
    """A specific cause for an unread clause shape, or None (then the lexical type decides)."""
    if _REFLECTION.search(text):
        return "UNSUPPORTED_POINT_CONSTRUCTION"
    if _DESCRIBED_IN_PREMISE.search(text):
        return "DESCRIBED_POINT_IN_PREMISE_UNSUPPORTED"
    if (m := _FREE_POINT.search(text)) and not _FIXES_POSITION.search(text, m.end()):
        return "FREE_POINT_UNDERDETERMINED"
    return None
_GOAL_TYPES = {"PROOF_REQUEST", "CONSTRUCTION_GOAL", "MEASUREMENT_GOAL"}
#: a trigonometric value OF an angle is asked: understood, but output-policy/1 serves the angle (cos²) only
_GOAL_FUNCTION = re.compile(r"(?<!\w)(?:côsin|cosin|cos|sin|sin|tang|tan|tg|côtang|cotang|cot|cotg)\s+(?:của\s+)?góc", re.IGNORECASE)
_CLAUSE_STATUS = {"MAPPED_FACT": "RECOGNIZED", "MAPPED_GOAL": "RECOGNIZED", "BENIGN_DISCOURSE": "NON_PROBLEM_OR_DISCOURSE",
                  "UNPARSED_FACT_CANDIDATE": "UNRECOGNIZED", "UNPARSED_GOAL_CANDIDATE": "UNRECOGNIZED",
                  "UNRESOLVED_REFERENCE": "UNRESOLVED_REFERENCE"}
#: canonical refusal group → (root cause, layer that owns it)
_GROUP_ROOT = {
    "CAPABILITY": ("PLANNER_COMPOSITION_UNSUPPORTED", "PLANNER"), "MISSING_DATA": ("INSUFFICIENT_CONSTRAINTS", "SOURCE_FACTS"),
    "INVALID_DATA": ("GEOMETRIC_DEGENERACY", "KERNEL"), "SOURCE_UNVERIFIED": ("SOURCE_PROVENANCE_MISSING", "SOURCE_GATE"),
    "RESULT_UNVERIFIED": ("CONSTRUCTION_VERIFICATION_FAILED", "KERNEL"), "INCONCLUSIVE": ("CONSTRUCTION_VERIFICATION_FAILED", "KERNEL"),
    "EXTRACTION_FAILED": ("INCOMPLETE_FACT_EXTRACTION", "PARSER"), "INTEGRITY": ("INTERNAL_ERROR", "RUNTIME"),
}


_REQUEST_VERB = re.compile(r"^\s*(?:hãy\s+)?(?P<v>xác\s+định|dựng|vẽ|tìm|tính|chứng\s+minh)(?!\w)", re.IGNORECASE)


def clause_types(text: str) -> list[str]:
    """Every lexical type cue of one clause, most specific first (a label for the diagnosis only). A clause that OPENS
    with a request verb is a goal whatever its object ("Xác định trung điểm của SA" asks, it does not define)."""
    body = re.sub(r"^\s*(?:Câu|Bài)\s*\d+\s*[.:)]\s*", "", text, flags=re.IGNORECASE)
    types = [name for name, pat in _TYPES if pat.search(body)]
    if (m := _REQUEST_VERB.match(body)) and not (types and types[0] in _GOAL_TYPES):
        v = m["v"].lower()
        types.insert(0, "PROOF_REQUEST" if v.startswith("chứng") else "MEASUREMENT_GOAL" if v == "tính" else "CONSTRUCTION_GOAL")
    return types or ["UNKNOWN"]


def _labels(text: str) -> set[str]:
    out: set[str] = set()
    for m in re.finditer(r"(?<![\w'′])(?:[A-Z][0-9]*['′]?){1,8}(?![\w'′])", text):
        out |= {x.replace("′", "'") for x in re.findall(r"[A-Z][0-9]*['′]?", m.group())}
    return out


def _plane_names(text: str) -> set[str]:
    return set(re.findall(r"\(([A-Z]|[α-ω])['′]?\)", text))


def diagnose_clauses(source_coverage: dict[str, Any]) -> list[dict[str, Any]]:
    """One record per clause: span, parser verdict, lexical types, labels, plane names, unresolved plane names."""
    clauses = list(source_coverage.get("clauses") or [])
    defined_planes: dict[str, str] = {}                            # plane name → id of the clause that defines it
    for c in clauses:
        for name in _plane_names(c["text"]):
            if re.search(rf"\({re.escape(name)}['′]?\)\s*(?:là\s+mặt\s+phẳng\s+)?(?:đi\s+qua|qua|chứa|song\s+song|vuông\s+góc)|"
                         rf"(?:dựng|kẻ|gọi)\s+(?:mặt\s+phẳng\s+)?\({re.escape(name)}['′]?\)", c["text"], re.IGNORECASE):
                defined_planes.setdefault(name, f"c{c['index']}")
    unread_ids = {f"c{c['index']}" for c in clauses if _CLAUSE_STATUS.get(c.get("classification")) in ("UNRECOGNIZED", "UNRESOLVED_REFERENCE")}
    out = []
    for c in clauses:
        types = clause_types(c["text"])
        status = _CLAUSE_STATUS.get(c.get("classification"), "UNKNOWN")
        names = _plane_names(c["text"])
        unresolved = sorted(names - set(defined_planes)) if types[0] in _GOAL_TYPES else []
        # a goal on a plane whose own definition clause was not read depends on that loss; it is not the root cause
        depends = sorted({defined_planes[n] for n in names if n in defined_planes and defined_planes[n] in unread_ids}
                         - {f"c{c['index']}"})
        root = None
        # a comma-joined part the parser could not read (`UNREAD_SUBCLAUSE@<offset>`): the cause is read from that part
        subs = [(int(m.group(1)), m.group(2)) for n in c.get("notes") or ()
                if (m := re.match(r"UNREAD_SUBCLAUSE@(\d+):(.*)", str(n)))]
        cause_text = " ".join(t for _o, t in subs) or c["text"]
        if status in ("UNRECOGNIZED", "UNRESOLVED_REFERENCE"):
            sub_types = clause_types(cause_text) if subs else types
            root = ("UNSUPPORTED_GOAL_FUNCTION" if types[0] in _GOAL_TYPES and _GOAL_FUNCTION.search(c["text"]) else
                    _clause_root(cause_text) or
                    ("UNRESOLVED_REFERENCE" if (unresolved or status == "UNRESOLVED_REFERENCE") else
                     "DEPENDS_ON_UNREAD_CLAUSE" if depends and types[0] in _GOAL_TYPES else
                     _ROOT_OF_TYPE.get(sub_types[0], "INCOMPLETE_FACT_EXTRACTION")))
        out.append({"clause_id": f"c{c['index']}", "start_offset": c["start"], "end_offset": c["end"],
                    "parser_classification": c.get("classification"), "semantic_status": status,
                    "clause_type": types[0], "clause_type_cues": types, "role": "GOAL" if types[0] in _GOAL_TYPES else "PREMISE",
                    "labels": sorted(_labels(c["text"])), "plane_names": sorted(_plane_names(c["text"])),
                    "unresolved_plane_names": unresolved, "downstream_dependency": depends, "failure_reason": root,
                    **({"unread_subclause_offsets": [o for o, _t in subs]} if subs else {}),
                    "_text": c["text"]})
    return out


def diagnose(*, parse_status: str, parse_reason: str | None, fallback_reason: str | None, source_coverage: dict[str, Any],
             terminal_code: str | None, fallback_allowed: bool, planner: dict | None = None,
             unresolved_kinds: list[str] | None = None) -> dict[str, Any]:
    """Root cause / responsible layers of one local-first refusal. `terminal_code` is what the response reports."""
    from app.ai.hybrid_preview import classify_refusal

    clauses = diagnose_clauses(source_coverage)
    lost = [c for c in clauses if c["failure_reason"] and c["failure_reason"] != "DEPENDS_ON_UNREAD_CLAUSE"]
    rec = {"diagnostics_version": DIAGNOSTICS_VERSION, "terminal_reason": terminal_code, "parse_status": parse_status,
           "clauses_total": len(clauses), "clauses_recognized": sum(c["semantic_status"] == "RECOGNIZED" for c in clauses),
           "clauses_unrecognized": len(lost), "clauses_dependent_on_unread": sum(c["failure_reason"] == "DEPENDS_ON_UNREAD_CLAUSE" for c in clauses),
           "clauses": clauses}
    fb = fallback_reason or ""
    if lost:                                                       # the parser dropped (or could not bind) a clause
        root = min((c["failure_reason"] for c in lost), key=_PRIORITY.index)
        rec.update(root_cause=root, first_loss_layer="PARSER", detected_by="PARSER_COVERAGE",
                   root_clause_ids=[c["clause_id"] for c in lost if c["failure_reason"] == root])
    elif fb.startswith("SOURCE_GATE_MISMATCH:"):                   # parser claimed coverage; the gate found what it missed
        code = fb.split(":")[1]
        # the parser emitted a fact the source does not ground: a goal not asked / a request not answered is a GOAL
        # extraction fault, an unread premise or question part an incomplete extraction, anything else a fact whose
        # quote does not carry it (value, object, plane, predicate)
        root = ("UNRECOGNIZED_GOAL" if code in ("NOT_ASKED_IN_SOURCE", "REQUEST_NOT_ANSWERED", "SOURCE_GOAL_UNREAD") else
                "INCOMPLETE_FACT_EXTRACTION" if code in ("QUESTION_CONTEXT_UNSUPPORTED", "SOURCE_PREMISE_UNREAD") else
                "SOURCE_PROVENANCE_MISSING")
        if code == "SOURCE_PREMISE_UNREAD" and re.search(r"hình\s+(?:vẽ|bên)", fb, re.IGNORECASE):
            root = "DIAGRAM_DEPENDENT_FACT"            # the unread premise defers its data to the figure
        if root == "UNRECOGNIZED_GOAL" and any(c["role"] == "GOAL" and _GOAL_FUNCTION.search(c.get("_text", "")) for c in clauses):
            root = "UNSUPPORTED_GOAL_FUNCTION"          # the parser kept the angle and dropped the function the gate saw
        rec.update(root_cause=root, first_loss_layer="PARSER", detected_by="SOURCE_GATE", source_gate_code=code)
    elif fb.startswith("SCHEMA_VALIDATION_FAILED:"):
        rec.update(root_cause="INCOMPLETE_FACT_EXTRACTION", first_loss_layer="PARSER", detected_by="TYPED_FACT_SCHEMA",
                   schema_code=fb.split(":")[1])
    elif parse_reason == "INCOMPLETE_SOLID_OR_GOAL":
        has_goal = any(c["role"] == "GOAL" and c["semantic_status"] == "RECOGNIZED" for c in clauses)
        rec.update(root_cause="UNRECOGNIZED_GOAL" if not has_goal else "UNRECOGNIZED_GEOMETRIC_ENTITY",
                   first_loss_layer="PARSER", detected_by="PARSER_COVERAGE")
    elif parse_status in ("LOCAL_PARSE_COMPLETE", "LOCAL_PARSE_AMBIGUOUS") and terminal_code:
        if terminal_code == "AMBIGUOUS_FACT" or parse_status == "LOCAL_PARSE_AMBIGUOUS":
            kinds = set(unresolved_kinds or ())
            rec.update(root_cause="INSUFFICIENT_CONSTRAINTS" if kinds and kinds <= {"missing_operand"} else "QUESTION_PREMISE_AMBIGUITY",
                       first_loss_layer="NONE", detected_by="PARSER", unresolved_kinds=sorted(kinds))
        elif terminal_code == "OUT_OF_SCOPE" and any(c["clause_type"] == "PROOF_REQUEST" for c in clauses):
            rec.update(root_cause="UNSUPPORTED_GOAL_KIND", first_loss_layer="NONE", detected_by="PARSER")   # a proof: read, not served
        else:
            group = classify_refusal(terminal_code, planner).group
            root, layer = _GROUP_ROOT.get(group, ("CONSTRUCTION_VERIFICATION_FAILED", "KERNEL"))
            if terminal_code == "INCONSISTENT_FACTS":
                root = "SOURCE_CONFLICT"
            if terminal_code.startswith("BRIDGE_UNSUPPORTED"):
                layer = "TYPED_FACTS_BRIDGE"
            # an angle asked of a figure the source fixes only up to similarity (no length at all): the data are complete
            # for the angle, the planner has no scale normalisation — a capability gap, not missing data
            if (terminal_code == "MISSING_DIMENSION"
                    and any(c["role"] == "GOAL" and re.search(r"\bgóc\b", c.get("_text", ""), re.IGNORECASE) for c in clauses)
                    and not any(_SCALE_LENGTH.search(c.get("_text", "")) for c in clauses)):
                root, layer = "SCALE_NORMALIZATION_UNSUPPORTED", "PLANNER"
            if terminal_code == "MISSING_DIMENSION" and root == "SCALE_NORMALIZATION_UNSUPPORTED":
                group = "CAPABILITY"
            rec.update(root_cause=root, first_loss_layer="NONE", detected_by=layer, refusal_group=group)
    else:
        rec.update(root_cause="INCOMPLETE_FACT_EXTRACTION", first_loss_layer="PARSER", detected_by="PARSER")
    for c in clauses:
        c.pop("_text", None)                            # offsets identify the clause; the text is not repeated
    rec["decided_by"] = "ROUTER_FAIL_CLOSED" if terminal_code == "LIVE_AI_DISABLED" else (
        "HYBRID_ROUTE" if parse_status in ("LOCAL_PARSE_COMPLETE", "LOCAL_PARSE_AMBIGUOUS") else "ROUTER")
    rec["fallback"] = ("LOCAL_PROVIDER_FALLBACK_DISABLED" if not fallback_allowed and terminal_code == "LIVE_AI_DISABLED"
                       else "NOT_REQUIRED" if rec["decided_by"] == "HYBRID_ROUTE" else "ALLOWED")
    return rec
