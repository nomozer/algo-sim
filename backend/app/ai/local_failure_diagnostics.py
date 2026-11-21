"""Clause-level failure localization and orthogonal taxonomy of the local-first route.

DIAGNOSTICS ONLY: nothing here produces a fact, changes a decision or reaches the planner. It reads what the parser,
the Source Gate, the Exact Kernel determinacy audit, and the hybrid route already decided and answers:
  1. WHERE information was first lost (`first_loss_layer`, `detected_by`, `root_clause_ids`),
  2. WHICH of the 5 orthogonal dimensions owns the refusal (`failure_dimension`, `taxonomy_class`), and
  3. WHETHER mathematical non-uniqueness was certified (`determinacy_status`, `determinacy_scope_note`, `witness_kind`).

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
_FREE_POINT = re.compile(r"(?<![\w'])[A-Z][0-9]*'?\s+(?:là\s+(?:một\s+)?điểm\s+(?:di\s+động\s+)?)?(?:thuộc|nằm\s+trên)\s+"
                         r"(?:cạnh|đoạn(?:\s+thẳng)?|đường\s+thẳng|tia)\s+[A-Z][0-9]*'?[A-Z]", re.IGNORECASE)
_FIXES_POSITION = re.compile(r"sao\s+cho|th[ỏo]a\s+mãn|cách\s|=|\btỉ\s+số|trung\s+điểm", re.IGNORECASE)
_REFLECTION = re.compile(r"đối\s+xứng", re.IGNORECASE)
_DESCRIBED_IN_PREMISE = re.compile(r"trùng\s+với\s+(?:trung\s+điểm|trọng\s+tâm|trực\s+tâm|tâm|giao\s+điểm)(?:\s+của)?\s", re.IGNORECASE)
_SCALE_LENGTH = re.compile(r"(?:=|bằng|cạnh|dài|cao)\s*(?:\d|√|a\b|\d*a\b)", re.IGNORECASE)
_SUBPHRASE_SPLIT = re.compile(r"[,;]|\s+\bvà\b\s+", re.IGNORECASE)
_TRAILING_FIG_NOTE = re.compile(r"\s*\([^)]*(?:tham\s+khảo|hình\s+vẽ|hình\s+bên)[^)]*\)\s*$", re.IGNORECASE)
_EXAM_PREFIX = re.compile(r"^\s*(?:Câu|Bài)\s*\d+\s*[.:)]\s*", re.IGNORECASE)


def _clause_root(text: str) -> str | None:
    """A specific cause for an unread clause shape, or None (then the lexical type decides)."""
    if _REFLECTION.search(text):
        return "UNSUPPORTED_POINT_CONSTRUCTION"
    if _DESCRIBED_IN_PREMISE.search(text):
        return "DESCRIBED_POINT_IN_PREMISE_UNSUPPORTED"
    if (m := _FREE_POINT.search(text)) and not _FIXES_POSITION.search(text, m.end()):
        return "FREE_POINT_UNDERDETERMINED"
    return None


def _unread_value_subphrases(clause_text: str, clause_start: int, notes: list[Any]) -> list[str]:
    """Slice the syntactic subphrase(s) inside `clause_text` containing each `UNREAD_VALUE@<offset>`."""
    out: list[str] = []
    for n in notes:
        m = re.match(r"UNREAD_VALUE@(\d+):(.*)", str(n))
        if not m:
            continue
        rel = int(m.group(1)) - clause_start
        if not (0 <= rel < len(clause_text)):
            continue
        # Partition clause_text into subphrases around ',', ';', and ' và '
        spans: list[tuple[int, int]] = []
        last = 0
        for sp in _SUBPHRASE_SPLIT.finditer(clause_text):
            spans.append((last, sp.start()))
            last = sp.end()
        spans.append((last, len(clause_text)))
        picked = next(((a, b) for a, b in spans if a <= rel <= b), (0, len(clause_text)))
        seg = clause_text[picked[0]:picked[1]]
        seg = _EXAM_PREFIX.sub("", seg)
        seg = _TRAILING_FIG_NOTE.sub("", seg).strip(" ,;.")
        m_co = re.search(r"\bcó\s+", seg, re.IGNORECASE)
        if m_co and picked[0] == 0 and (rel - picked[0]) >= m_co.end():
            seg = seg[m_co.end():].strip(" ,;.")
        if seg and seg not in out:
            out.append(seg)
    return out


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
        depends = sorted({defined_planes[n] for n in names if n in defined_planes and defined_planes[n] in unread_ids}
                         - {f"c{c['index']}"})
        root = None
        notes = list(c.get("notes") or ())
        subs = [(int(m.group(1)), m.group(2)) for n in notes
                if (m := re.match(r"UNREAD_SUBCLAUSE@(\d+):(.*)", str(n)))]
        val_phrases = _unread_value_subphrases(c["text"], int(c["start"]), notes) if not subs else []
        cause_text = " ".join(t for _o, t in subs) or (" ; ".join(val_phrases) if val_phrases else c["text"])
        vals = [str(n).split(":", 1)[1] for n in notes if str(n).startswith("UNREAD_VALUE@")]
        if status in ("UNRECOGNIZED", "UNRESOLVED_REFERENCE") and vals and not subs:
            root = _clause_root(" ".join(val_phrases or vals)) or "INCOMPLETE_FACT_EXTRACTION"
        elif status in ("UNRECOGNIZED", "UNRESOLVED_REFERENCE"):
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
                    "_text": c["text"], "_cause": cause_text if (subs or val_phrases) else c["text"]})
    return out


_ENTITY_UNRESOLVED_ROOTS = frozenset({
    "UNRESOLVED_REFERENCE",
    "UNRECOGNIZED_GEOMETRIC_ENTITY",
    "DESCRIBED_POINT_IN_PREMISE_UNSUPPORTED",
    "QUESTION_PREMISE_AMBIGUITY",
})
_INPUT_INCOMPLETE_ROOTS = frozenset({
    "INCOMPLETE_FACT_EXTRACTION",
    "UNRECOGNIZED_RELATION",
    "UNRECOGNIZED_GOAL",
    "SOURCE_PROVENANCE_MISSING",
    "DIAGRAM_DEPENDENT_FACT",
})
_CONTRADICTORY_ROOTS = frozenset({"SOURCE_CONFLICT", "GEOMETRIC_DEGENERACY"})


def _orthogonal_classification(
    root_cause: str,
    terminal_code: str | None,
    determinacy_audit: dict[str, Any] | None,
) -> dict[str, Any]:
    """Map `(root_cause, terminal_code, determinacy_audit)` to the 5 orthogonal dimensions and 6 canonical taxonomy states."""
    det = determinacy_audit if isinstance(determinacy_audit, dict) else {}
    det_status_in = det.get("status")
    witness = det.get("witness_kind")
    unconsumed = list(det.get("unconsumed_constraint_ids") or [])
    note = det.get("scope_note")

    if root_cause in _ENTITY_UNRESOLVED_ROOTS:
        return {
            "failure_dimension": "SEMANTIC_COMPLETENESS",
            "taxonomy_class": "SEMANTIC_ENTITY_UNRESOLVED",
            "determinacy_status": "NOT_EVALUATED_SEMANTIC_INCOMPLETE",
            "determinacy_scope_note": note or "Còn đối tượng, điểm mô tả hoặc tham chiếu trong đề chưa được phân giải.",
        }
    if root_cause in _INPUT_INCOMPLETE_ROOTS:
        return {
            "failure_dimension": "SEMANTIC_COMPLETENESS",
            "taxonomy_class": "SEMANTIC_INPUT_INCOMPLETE",
            "determinacy_status": "NOT_EVALUATED_SEMANTIC_INCOMPLETE",
            "determinacy_scope_note": note or "Còn mệnh đề, số đo hoặc câu hỏi trong đề chưa được trích xuất đầy đủ.",
        }
    if root_cause in _CONTRADICTORY_ROOTS:
        return {
            "failure_dimension": "CONTRADICTORY_CONSTRAINTS",
            "taxonomy_class": "CONTRADICTORY_CONSTRAINTS",
            "determinacy_status": "NO_VALID_REALIZATION",
            "determinacy_scope_note": "Các giả thiết đã xác minh mâu thuẫn nhau hoặc làm hình suy biến (0 mô hình hợp lệ).",
        }
    if root_cause == "INTERNAL_ERROR":
        return {
            "failure_dimension": "INFRASTRUCTURE_AVAILABILITY",
            "taxonomy_class": "INFRASTRUCTURE_UNAVAILABLE",
            "determinacy_status": "NOT_EVALUATED_INFRASTRUCTURE",
            "determinacy_scope_note": "Lỗi kỹ thuật hoặc cấu hình vận hành.",
        }
    if root_cause == "INSUFFICIENT_CONSTRAINTS" or terminal_code in ("PLANE_NOT_UNIQUE", "FIGURE_NOT_UNIQUE"):
        if witness == "NO_VALID_VARIATION_CONSTRUCTED" and terminal_code not in ("PLANE_NOT_UNIQUE", "FIGURE_NOT_UNIQUE"):
            return {
                "failure_dimension": "MATHEMATICAL_DETERMINACY",
                "taxonomy_class": "MATHEMATICALLY_UNDERDETERMINED",
                "determinacy_status": "UNPROVED_NO_VALID_VARIATION",
                "determinacy_scope_note": note or "Chưa dựng được cặp mô hình biến thiên hợp lệ để chứng minh tính bất định hay chỉ lỗi năng lực.",
                "witness_kind": witness,
                "unconsumed_constraint_ids": unconsumed,
            }
        return {
            "failure_dimension": "MATHEMATICAL_DETERMINACY",
            "taxonomy_class": "MATHEMATICALLY_UNDERDETERMINED",
            "determinacy_status": "PROVED_UNDERDETERMINED",
            "determinacy_scope_note": note or "Đã chứng minh tồn tại nhiều cấu hình hợp lệ cho kết quả hoặc hình khác nhau.",
            **({"witness_kind": witness} if witness else {}),
            **({"unconsumed_constraint_ids": unconsumed} if det else {}),
        }

    # IMPLEMENTATION_CAPABILITY (`CAPABILITY_UNSUPPORTED`)
    if terminal_code == "EXACT_DOMAIN_EXCEEDED":
        d_status = "PROVED_DETERMINATE_EXACT_DOMAIN_EXCEEDED"
        d_note = note or "Hình xác định nhưng số đo hoặc tích vô hướng vượt ngoài miền đại số hữu tỉ/căn bậc hai hiện tại."
    elif det_status_in == "UNPROVED_DUE_TO_CAPABILITY_GAP" or root_cause in (
        "UNSUPPORTED_DEDUCTION",
        "SHAPE_FREEDOM_UNCERTIFIED",
        "FREE_POINT_UNDERDETERMINED",
        "UNSUPPORTED_POINT_CONSTRUCTION",
    ):
        d_status = "UNPROVED_DUE_TO_CAPABILITY_GAP"
        d_note = note or (
            "Hệ chưa có đủ phép dựng hoặc chứng chỉ suy diễn để kết luận tính xác định duy nhất của bài toán."
        )
    else:
        d_status = "NOT_EVALUATED_KNOWN_CAPABILITY_BOUNDARY"
        d_note = note or "Yêu cầu nằm ngoài tập phép dựng hoặc dạng đầu ra đã đăng ký của hệ."
    return {
        "failure_dimension": "IMPLEMENTATION_CAPABILITY",
        "taxonomy_class": "CAPABILITY_UNSUPPORTED",
        "determinacy_status": d_status,
        "determinacy_scope_note": d_note,
        **({"witness_kind": witness} if witness else {}),
        **({"unconsumed_constraint_ids": unconsumed} if det else {}),
    }


def diagnose(*, parse_status: str, parse_reason: str | None, fallback_reason: str | None, source_coverage: dict[str, Any],
             terminal_code: str | None, fallback_allowed: bool, planner: dict | None = None,
             unresolved_kinds: list[str] | None = None,
             determinacy_audit: dict[str, Any] | None = None) -> dict[str, Any]:
    """Root cause / responsible layers / orthogonal taxonomy of one local-first refusal."""
    from app.ai.hybrid_preview import classify_refusal

    clauses = diagnose_clauses(source_coverage)
    lost = [c for c in clauses if c["failure_reason"] and c["failure_reason"] != "DEPENDS_ON_UNREAD_CLAUSE"]
    rec: dict[str, Any] = {
        "diagnostics_version": DIAGNOSTICS_VERSION,
        "terminal_reason": terminal_code,
        "parse_status": parse_status,
        "clauses_total": len(clauses),
        "clauses_recognized": sum(c["semantic_status"] == "RECOGNIZED" for c in clauses),
        "clauses_unrecognized": len(lost),
        "clauses_dependent_on_unread": sum(c["failure_reason"] == "DEPENDS_ON_UNREAD_CLAUSE" for c in clauses),
        "clauses": clauses,
    }
    fb = fallback_reason or ""
    det_status = (determinacy_audit or {}).get("status") if isinstance(determinacy_audit, dict) else None
    det_witness = (determinacy_audit or {}).get("witness_kind") if isinstance(determinacy_audit, dict) else None

    if lost:                                                       # the parser dropped (or could not bind) a clause
        root = min((c["failure_reason"] for c in lost), key=_PRIORITY.index)
        rec.update(root_cause=root, first_loss_layer="PARSER", detected_by="PARSER_COVERAGE",
                   root_clause_ids=[c["clause_id"] for c in lost if c["failure_reason"] == root])
    elif fb.startswith("SOURCE_GATE_MISMATCH:"):                   # parser claimed coverage; the gate found what it missed
        code = fb.split(":")[1]
        root = ("UNRECOGNIZED_GOAL" if code in ("NOT_ASKED_IN_SOURCE", "REQUEST_NOT_ANSWERED", "SOURCE_GOAL_UNREAD") else
                "INCOMPLETE_FACT_EXTRACTION" if code in ("QUESTION_CONTEXT_UNSUPPORTED", "SOURCE_PREMISE_UNREAD") else
                "SOURCE_PROVENANCE_MISSING")
        if code == "SOURCE_PREMISE_UNREAD" and re.search(r"hình\s+(?:vẽ|bên)", fb, re.IGNORECASE):
            root = "DIAGRAM_DEPENDENT_FACT"
        if root == "UNRECOGNIZED_GOAL" and any(c["role"] == "GOAL" and _GOAL_FUNCTION.search(c.get("_text", "")) for c in clauses):
            root = "UNSUPPORTED_GOAL_FUNCTION"
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
            if kinds == {"unsupported"}:
                rec.update(root_cause="UNSUPPORTED_GOAL_KIND", first_loss_layer="NONE", detected_by="PARSER",
                           unresolved_kinds=sorted(kinds))
            elif det_status == "PROVED_UNDERDETERMINED":
                rec.update(root_cause="INSUFFICIENT_CONSTRAINTS", first_loss_layer="NONE", detected_by="PARSER",
                           unresolved_kinds=sorted(kinds))
            elif det_status == "UNPROVED_DUE_TO_CAPABILITY_GAP" and det_witness != "NO_VALID_VARIATION_CONSTRUCTED":
                if kinds and kinds <= {"missing_operand"} and det_witness != "UNRESOLVED_SEMANTIC_OPERAND":
                    rec.update(root_cause="UNSUPPORTED_DEDUCTION", first_loss_layer="NONE", detected_by="ENGINE",
                               unresolved_kinds=sorted(kinds), refusal_group="CAPABILITY")
                else:
                    rec.update(root_cause="QUESTION_PREMISE_AMBIGUITY", first_loss_layer="NONE", detected_by="PARSER",
                               unresolved_kinds=sorted(kinds))
            else:
                rec.update(root_cause="INSUFFICIENT_CONSTRAINTS" if kinds and kinds <= {"missing_operand"} else "QUESTION_PREMISE_AMBIGUITY",
                           first_loss_layer="NONE", detected_by="PARSER", unresolved_kinds=sorted(kinds))
        elif terminal_code == "OUT_OF_SCOPE" and any(c["clause_type"] == "PROOF_REQUEST" for c in clauses):
            rec.update(root_cause="UNSUPPORTED_GOAL_KIND", first_loss_layer="NONE", detected_by="PARSER")
        elif (
            terminal_code in ("MISSING_DIMENSION", "UNDERDETERMINED_POINT", "FOOT_NOT_DETERMINED")
            and det_status == "UNPROVED_DUE_TO_CAPABILITY_GAP"
            and det_witness != "NO_VALID_VARIATION_CONSTRUCTED"
        ):
            is_shape_uncert = (
                det_witness == "CONSTANT_ACROSS_SAMPLED_REALIZATIONS_UNPROVED_INVARIANCE"
                or (
                    terminal_code == "MISSING_DIMENSION"
                    and any(c["role"] == "GOAL" and re.search(r"\bgóc\b", c.get("_text", ""), re.IGNORECASE) for c in clauses)
                    and not any(_SCALE_LENGTH.search(c.get("_text", "")) for c in clauses)
                )
            )
            root = "SHAPE_FREEDOM_UNCERTIFIED" if is_shape_uncert else "UNSUPPORTED_DEDUCTION"
            layer = "PLANNER" if is_shape_uncert else "ENGINE"
            rec.update(root_cause=root, first_loss_layer="NONE", detected_by=layer, refusal_group="CAPABILITY")
        else:
            group = classify_refusal(
                terminal_code,
                planner,
                details={"determinacy_audit": determinacy_audit} if determinacy_audit else None,
            ).group
            root, layer = _GROUP_ROOT.get(group, ("CONSTRUCTION_VERIFICATION_FAILED", "KERNEL"))
            if terminal_code == "INCONSISTENT_FACTS":
                root = "SOURCE_CONFLICT"
            elif terminal_code == "FIGURE_NOT_UNIQUE":
                root, layer = "INSUFFICIENT_CONSTRAINTS", "SOURCE_FACTS"
            if terminal_code.startswith("BRIDGE_UNSUPPORTED"):
                layer = "TYPED_FACTS_BRIDGE"
            if (determinacy_audit is None and terminal_code == "MISSING_DIMENSION"
                    and any(c["role"] == "GOAL" and re.search(r"\bgóc\b", c.get("_text", ""), re.IGNORECASE) for c in clauses)
                    and not any(_SCALE_LENGTH.search(c.get("_text", "")) for c in clauses)):
                root, layer, group = "SHAPE_FREEDOM_UNCERTIFIED", "PLANNER", "CAPABILITY"
            rec.update(root_cause=root, first_loss_layer="NONE", detected_by=layer, refusal_group=group)
    else:
        rec.update(root_cause="INCOMPLETE_FACT_EXTRACTION", first_loss_layer="PARSER", detected_by="PARSER")

    rec.update(_orthogonal_classification(rec["root_cause"], terminal_code, determinacy_audit))
    rec["learner_summary"] = learner_summary(rec["root_cause"], [c for c in clauses if c["clause_id"] in
                                                                (rec.get("root_clause_ids") or ())])
    for c in clauses:
        c.pop("_text", None)                            # offsets identify the clause; the text is not repeated
        c.pop("_cause", None)
    rec["decided_by"] = "ROUTER_FAIL_CLOSED" if terminal_code in ("LIVE_AI_DISABLED", "MISSING_API_KEY") else (
        "HYBRID_ROUTE" if parse_status in ("LOCAL_PARSE_COMPLETE", "LOCAL_PARSE_AMBIGUOUS") else "ROUTER")
    rec["fallback"] = (
        "LOCAL_PROVIDER_FALLBACK_DISABLED" if not fallback_allowed and terminal_code == "LIVE_AI_DISABLED"
        else "LOCAL_PROVIDER_KEY_MISSING" if terminal_code == "MISSING_API_KEY"
        else "NOT_REQUIRED" if rec["decided_by"] == "HYBRID_ROUTE"
        else "ALLOWED"
    )
    return rec


_LEARNER_OF_ROOT = {
    "UNRECOGNIZED_GEOMETRIC_ENTITY": "Hệ thống chưa đọc được một điểm hoặc một đối tượng hình học trong đề.",
    "UNRESOLVED_REFERENCE": "Đề nhắc tới một điểm hoặc mặt phẳng mà hệ thống chưa tìm thấy chỗ định nghĩa.",
    "DESCRIBED_POINT_IN_PREMISE_UNSUPPORTED": "Đề mô tả một điểm chưa được đặt tên; hệ thống chưa đọc được điểm đó.",
    "FREE_POINT_UNDERDETERMINED": "Một điểm trong đề di động hoặc chỉ được nêu thuộc một đối tượng; hệ thống chưa hỗ trợ kiểm chứng trên điểm tự do này.",
    "UNSUPPORTED_POINT_CONSTRUCTION": "Đề dùng một phép dựng điểm mà hệ thống chưa hỗ trợ.",
    "UNRECOGNIZED_RELATION": "Hệ thống chưa đọc được một quan hệ hoặc số đo trong giả thiết của đề.",
    "INCOMPLETE_FACT_EXTRACTION": "Hệ thống chưa đọc hết các dữ kiện trong đề.",
    "SOURCE_PROVENANCE_MISSING": "Hệ thống chưa đối chiếu được một dữ kiện với câu chữ của đề.",
    "DIAGRAM_DEPENDENT_FACT": "Đề lấy dữ kiện từ hình vẽ; hệ thống chỉ đọc được phần chữ của đề.",
    "UNRECOGNIZED_GOAL": "Hệ thống chưa xác định được đề hỏi gì.",
    "UNSUPPORTED_GOAL_FUNCTION": "Đề hỏi một đại lượng của góc mà hệ thống chưa tính được.",
    "UNSUPPORTED_GOAL_KIND": "Đề yêu cầu chứng minh; hệ thống chỉ dựng hình và tính các đại lượng.",
    "INSUFFICIENT_CONSTRAINTS": "Đề chưa cho đủ dữ kiện để dựng hình duy nhất.",
    "SHAPE_FREEDOM_UNCERTIFIED": "Các giả thiết chưa cố định duy nhất hình dạng, và hệ thống chưa chứng minh được kết quả không đổi.",
    "UNSUPPORTED_DEDUCTION": "Hệ thống đã đọc các giả thiết của đề nhưng chưa hỗ trợ suy diễn tất định từ tổ hợp quan hệ này.",
    "QUESTION_PREMISE_AMBIGUITY": "Một phần của đề có thể hiểu theo nhiều cách; hệ thống chưa chọn thay em.",
    "PLANNER_COMPOSITION_UNSUPPORTED": "Bài này cần một phép dựng mà hệ thống chưa hỗ trợ.",
    "GEOMETRIC_DEGENERACY": "Các dữ kiện trong đề cho một hình suy biến.",
    "SOURCE_CONFLICT": "Các dữ kiện trong đề mâu thuẫn nhau.",
}
_EXCERPT_MAX = 120
_CAPABILITY_ROOTS = frozenset({"UNSUPPORTED_POINT_CONSTRUCTION", "PLANNER_COMPOSITION_UNSUPPORTED", "UNSUPPORTED_GOAL_FUNCTION",
                               "UNSUPPORTED_GOAL_KIND", "DIAGRAM_DEPENDENT_FACT", "SHAPE_FREEDOM_UNCERTIFIED",
                               "UNSUPPORTED_DEDUCTION", "INSUFFICIENT_CONSTRAINTS", "GEOMETRIC_DEGENERACY",
                               "SOURCE_CONFLICT", "FREE_POINT_UNDERDETERMINED"})


def learner_summary(root: str, root_clauses: list[dict[str, Any]]) -> dict[str, Any]:
    """Learner-safe summary of one refusal: a Vietnamese sentence for the root cause and the learner's own words the
    system did not read (at most three excerpts, each cut to `_EXCERPT_MAX`). No code, id or offset is in the text."""
    excerpts = []
    for c in root_clauses[:3]:
        t = re.sub(r"\s+", " ", c.get("_cause") or c.get("_text") or "").strip(" ,;.")
        if t:
            excerpts.append(t if len(t) <= _EXCERPT_MAX else t[:_EXCERPT_MAX - 1].rstrip() + "…")
    return {"message": _LEARNER_OF_ROOT.get(root, "Hệ thống chưa hiểu hết đề bài này."), "unread_excerpts": excerpts,
            # a valid problem refused for a capability gap is never the learner's to fix (W17 §15.3)
            "rewrite_may_help": root not in _CAPABILITY_ROOTS}
