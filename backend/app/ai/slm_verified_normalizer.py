# -*- coding: utf-8 -*-
"""Span-audited conservative surface canonicalizer (`slm-verified-normalizer/2`).

Operates strictly *upstream* of SLM extraction and Source Gate (`registry.kiem_nguon`)
inside opt-in ``HYBRID_ROUTE_MODE=local-slm`` (`/6` & `/7` ``compact_clause``). Every rule:
  - Preserves 10-field span-audited provenance (original text, original span in
    source text, original clause ID, normalized text, rule ID, original entity refs,
    scope, polarity, semantic equivalence evidence, and validation status).
  - Refuses / leaves intact ambiguous Vietnamese diacritic typos (`TYPO_REQUIRES_CONFIRMATION`)
    instead of guessing user intent (`§6.C2`).
  - Never turns conditionals (`Nếu ... thì`, `Khi ...`, `Giả sử ...`), negations
    (`không vuông góc`), or singular underspecified references (`cạnh bên bằng ...`
    on non-regular pyramids) into universal or affirmative premises.
  - Supports ``normalizer_version="v1"`` (exact `/6` rule table for Config B ablations)
    and ``normalizer_version="v2"`` (default `/7` deterministic language closure).
"""

from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Any

from app.ai.local_geometry_parser import normalize_problem_text

SLM_VERIFIED_NORMALIZER_V1_VERSION = "slm-verified-normalizer/1"
SLM_VERIFIED_NORMALIZER_VERSION = "slm-verified-normalizer/2"
SLM_VERIFIED_NORMALIZER_V3_VERSION = "slm-verified-normalizer/3"

_TYPO_CHECKS: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("TYPO_VUONG_GOC_TONE", re.compile(r"\bvuôg\s+g[oóòỏõọ]c\b|\bvuông\s+goc\b", re.IGNORECASE | re.UNICODE)),
    ("TYPO_CHOP_TONE", re.compile(r"\b(?:hình|khối)\s+chop\b", re.IGNORECASE | re.UNICODE)),
    ("TYPO_DEN_TONE", re.compile(r"\bchóp\s+(?:tam\s+giác\s+|tứ\s+giác\s+)?đên\b", re.IGNORECASE | re.UNICODE)),
    ("TYPO_TRUNG_DIEM", re.compile(r"\btrung\s+điêm\b", re.IGNORECASE | re.UNICODE)),
    ("TYPO_LANG_TRU", re.compile(r"\blăng\s+tru\b", re.IGNORECASE | re.UNICODE)),
)

_TYPO_CHECKS_V2_EXTRA: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("TYPO_MAT_PHANG_TONE", re.compile(r"\bmặt\s+phăng\b", re.IGNORECASE | re.UNICODE)),
    ("TYPO_TU_DIEN_DEU_TONE", re.compile(r"\btứ\s+diên\s+(?:đêu|đều)\b|\btứ\s+diện\s+đêu\b", re.IGNORECASE | re.UNICODE)),
)

_CONDITIONAL_MARKER_RE = re.compile(r"\b(?:nếu|khi|giả\s+sử)\b", re.IGNORECASE | re.UNICODE)
_NEGATED_SPAN_RE = re.compile(
    r"\b(?:không|chẳng|chưa)\s+(?:hề\s+)?(?:vuông\s+góc|vuông|cắt|song\s+song|bằng|đều|cân|trùng|thuộc|nằm\s+trong|dài)\b"
    r"|\bkhông\s+phải\b",
    re.IGNORECASE | re.UNICODE,
)
_SOLID_TOKEN_V1_RE = re.compile(r"\b([A-Z][0-9]*'*)\.([A-Z][0-9']*){3,6}\b")
_SOLID_TOKEN_RE = re.compile(r"(?<![A-Z0-9'])((?:[A-Z][0-9]*'*){1,6})\.((?:[A-Z][0-9]*'*){3,6})(?![A-Z0-9'])")
_ENTITY_REF_RE = re.compile(r"(?<![A-Za-zÀ-Ỹà-ỹ0-9'])([A-Z][0-9]*'*(?:\.[A-Z0-9']+|[A-Z0-9']*))(?![A-Za-zÀ-Ỹà-ỹ0-9'])")
_QTY_CHAR = r"[^\s,.;:!?]+"


@dataclass(frozen=True)
class VerifiedNormalizationStep:
    rule_id: str
    original_span: tuple[int, int]
    original_excerpt: str
    normalized_excerpt: str
    validation_result: str
    ambiguity_status: str
    original_clause_id: int = 0
    original_entity_refs: tuple[str, ...] = ()
    scope: str = "LOCAL_CLAUSE"
    polarity: str = "AFFIRMATIVE"
    semantic_equivalence_evidence: str = "deterministic_surface_equivalence"

    def to_dict(self) -> dict[str, Any]:
        return {
            "rule_id": self.rule_id,
            "transformation_rule_id": self.rule_id,
            "original_text": self.original_excerpt,
            "original_span": [self.original_span[0], self.original_span[1]],
            "original_clause_id": self.original_clause_id,
            "normalized_text": self.normalized_excerpt,
            "original_excerpt": self.original_excerpt,
            "normalized_excerpt": self.normalized_excerpt,
            "original_entity_refs": list(self.original_entity_refs),
            "scope": self.scope,
            "polarity": self.polarity,
            "semantic_equivalence_evidence": self.semantic_equivalence_evidence,
            "validation_status": self.validation_result,
            "validation_result": self.validation_result,
            "ambiguity_status": self.ambiguity_status,
        }


@dataclass(frozen=True)
class VerifiedNormalizationResult:
    normalizer_version: str
    original_text: str
    canonical_text: str
    changed: bool
    typo_detected: bool
    ambiguity_flags: tuple[dict[str, Any], ...]
    steps: tuple[VerifiedNormalizationStep, ...]

    def to_provenance_dict(self) -> dict[str, Any]:
        return {
            "normalizer_version": self.normalizer_version,
            "changed": self.changed,
            "typo_detected": self.typo_detected,
            "ambiguity_flags": list(self.ambiguity_flags),
            "applied_rule_ids": [s.rule_id for s in self.steps if s.validation_result == "VALIDATED_MEANING_PRESERVING"],
            "steps": [s.to_dict() for s in self.steps],
        }


def _clause_id_for_orig_pos(norm0: str, orig_pos: int) -> int:
    """Return 0-based sentence/clause index in baseline text for an original offset."""
    prefix = norm0[: max(0, min(orig_pos, len(norm0)))]
    return len(re.findall(r"[.?!;\n]+", prefix))


def _update_pos_map(pos_map: list[int], edits: list[tuple[int, int, str]]) -> list[int]:
    """Map current string character positions monotonically back to `norm0` positions."""
    if not edits:
        return pos_map
    new_map: list[int] = []
    last = 0
    for s0, s1, repl in edits:
        new_map.extend(pos_map[last:s0])
        orig_s0 = pos_map[s0]
        orig_s1 = pos_map[s1]
        k = len(repl)
        if k > 0:
            new_map.append(orig_s0)
            for j in range(1, k):
                interp = orig_s0 + round((orig_s1 - orig_s0) * j / k)
                new_map.append(interp)
        last = s1
    new_map.extend(pos_map[last:])
    return new_map


def _sentence_bounds(text: str, s0: int, s1: int) -> tuple[int, int]:
    """Return real sentence start/end around `text[s0:s1]`, ignoring dots inside `S.ABC` or `A.B'C'`."""
    boundary_re = re.compile(r"(?:[;?!]|(?<![A-Z0-9'])\.(?![A-Z0-9'])|\.(?=\s|$))")
    sent_start = 0
    for bm in boundary_re.finditer(text, 0, s0):
        sent_start = bm.end()
    m_end = boundary_re.search(text, s1)
    sent_end = m_end.start() if m_end else len(text)
    return sent_start, sent_end


def _apply_safe_sub(
    cur: str,
    *,
    norm0: str,
    pos_map: list[int],
    rule_id: str,
    pattern: re.Pattern[str],
    repl: Any,
    steps: list[VerifiedNormalizationStep],
    count: int = 0,
    skip_if_cond_or_neg: bool = False,
    skip_if_sentence_neg: bool = False,
    scope: str = "LOCAL_CLAUSE",
    evidence: str = "deterministic_surface_equivalence",
) -> tuple[str, list[int]]:
    """Apply a regex substitution while tracking exact original spans and rejecting conditionals/negations."""
    matches = list(pattern.finditer(cur))
    if not matches:
        return cur, pos_map
    if count > 0:
        matches = matches[:count]

    out_parts: list[str] = []
    edits: list[tuple[int, int, str]] = []
    last = 0
    changed_any = False
    for m in matches:
        s0, s1 = m.start(), m.end()
        excerpt = m.group(0)
        orig_s0 = pos_map[s0]
        orig_s1 = pos_map[s1]
        orig_excerpt = norm0[orig_s0:orig_s1] or excerpt
        clause_id = _clause_id_for_orig_pos(norm0, orig_s0)
        ent_refs = tuple(dict.fromkeys(_ENTITY_REF_RE.findall(orig_excerpt)))

        sent_start, sent_end = _sentence_bounds(cur, s0, s1)
        sent_slice = cur[sent_start:sent_end]

        if skip_if_cond_or_neg:
            if _CONDITIONAL_MARKER_RE.search(sent_slice) or _NEGATED_SPAN_RE.search(excerpt):
                steps.append(
                    VerifiedNormalizationStep(
                        rule_id=rule_id,
                        original_span=(orig_s0, orig_s1),
                        original_excerpt=orig_excerpt,
                        normalized_excerpt=orig_excerpt,
                        validation_result="REJECTED_CONSERVATIVE",
                        ambiguity_status="AMBIGUOUS_REQUIRES_CONFIRMATION",
                        original_clause_id=clause_id,
                        original_entity_refs=ent_refs,
                        scope=scope,
                        polarity="CONDITIONAL_OR_NEGATIVE",
                        semantic_equivalence_evidence="blocked_by_conditional_or_negation_guard",
                    )
                )
                continue
        if skip_if_sentence_neg and _NEGATED_SPAN_RE.search(sent_slice):
            steps.append(
                VerifiedNormalizationStep(
                    rule_id=rule_id,
                    original_span=(orig_s0, orig_s1),
                    original_excerpt=orig_excerpt,
                    normalized_excerpt=orig_excerpt,
                    validation_result="REJECTED_CONSERVATIVE",
                    ambiguity_status="AMBIGUOUS_REQUIRES_CONFIRMATION",
                    original_clause_id=clause_id,
                    original_entity_refs=ent_refs,
                    scope=scope,
                    polarity="NEGATIVE",
                    semantic_equivalence_evidence="blocked_by_sentence_negation_guard",
                )
            )
            continue

        replacement = repl(m) if callable(repl) else m.expand(repl)
        if replacement == excerpt:
            continue
        out_parts.append(cur[last:s0])
        out_parts.append(replacement)
        edits.append((s0, s1, replacement))
        last = s1
        changed_any = True
        steps.append(
            VerifiedNormalizationStep(
                rule_id=rule_id,
                original_span=(orig_s0, orig_s1),
                original_excerpt=orig_excerpt,
                normalized_excerpt=replacement,
                validation_result="VALIDATED_MEANING_PRESERVING",
                ambiguity_status="UNAMBIGUOUS",
                original_clause_id=clause_id,
                original_entity_refs=ent_refs,
                scope=scope,
                polarity="AFFIRMATIVE",
                semantic_equivalence_evidence=evidence,
            )
        )
    if not changed_any:
        return cur, pos_map
    out_parts.append(cur[last:])
    new_cur = "".join(out_parts)
    new_map = _update_pos_map(pos_map, edits)
    return new_cur, new_map


def _implicit_solid_base_in_sentence(sent: str, *, use_v2: bool = True) -> str | None:
    rx = _SOLID_TOKEN_RE if use_v2 else _SOLID_TOKEN_V1_RE
    m = rx.search(sent)
    if not m:
        return None
    left, right = m.group(0).split(".", 1)
    if len(re.findall(r"[A-Z][0-9]*'*", left)) == 1 and len(re.findall(r"[A-Z][0-9]*'*", right)) >= 3:
        return right
    if len(re.findall(r"[A-Z][0-9]*'*", left)) >= 3:
        return left
    return None


def _is_matching_prism_lateral_edge(seg: str, sentence: str) -> bool:
    """True only when `seg` pairs a base vertex and its corresponding prime vertex on a declared prism."""
    pts = re.findall(r"[A-Z][0-9]*'*", seg)
    if len(pts) != 2:
        return False
    m_solid = _SOLID_TOKEN_RE.search(sentence)
    if not m_solid:
        return False
    left, right = m_solid.group(0).split(".", 1)
    lpts = re.findall(r"[A-Z][0-9]*'*", left)
    rpts = re.findall(r"[A-Z][0-9]*'*", right)
    if len(lpts) < 3 or len(lpts) != len(rpts):
        return False
    return any({a, b} == {pts[0], pts[1]} for a, b in zip(lpts, rpts))


def _unused_point_label(text: str, preferred: tuple[str, ...] = ("G", "I", "K", "P", "Q", "H", "M", "N")) -> str:
    """Pick a single uppercase point letter guaranteed absent from `text`."""
    used = set(re.findall(r"[A-Z][0-9]*'*", text))
    for cand in preferred:
        if cand not in used and not any(u.startswith(cand) for u in used):
            return cand
    return "P0"


# ── /15 composition rules (`VN12`–`VN17`, run `grounded-geometry-language-recovery`) ──────────────────────────────────
# Each rule rewrites one closed Vietnamese construction into a canonical form the local parser AND the Source Gate already
# read and verify ("IJ, IK, IL đôi một vuông góc", "SA = 4 và SA vuông góc với đáy", "đường cao SA = 4", "Vẽ hình.", "Cho …
# có …. Tính …"). Nothing is inferred: a rule leaves the text unchanged when its precondition (one matching solid, equal
# list lengths, the same segment on both sides, no yes/no question) does not hold, and `_apply_safe_sub` blocks it in a
# conditional or negated sentence. The Source Gate then verifies the canonical text exactly as it verifies typed input.
_SEG = r"[A-Z][0-9]*'?[A-Z][0-9]*'?"
_VAL = r"(?:(?:\d+(?:,\d+)?(?:√\d+)?|√\d+)a?|a)(?![\w'√])"
_SEG_LIST = rf"{_SEG}(?:\s*,\s*{_SEG})*(?:\s*,?\s*và\s+{_SEG})"
_VAL_LIST = rf"{_VAL}(?:\s*,\s*{_VAL})*(?:\s*,?\s*và\s+{_VAL})"
_PERP_PAIRWISE = r"(?:đôi\s+một\s+vuông\s+góc(?:\s+với\s+nhau)?|vuông\s+góc\s+(?:với\s+nhau\s+)?từng\s+đôi(?:\s+một)?)"
_PERP_TARGET = r"(?:(?:mặt\s+phẳng\s+)?\([A-Z][0-9]*'?(?:[A-Z][0-9]*'?){2,3}\)|mặt\s+phẳng\s+đáy|(?:mặt\s+)?đáy)"
_SOLID_PHRASE = (r"(?:(?:khối|hình)\s+)?(?:tứ\s+diện|chóp|lăng\s+trụ(?:\s+đứng)?)(?:\s+(?:tam\s+giác|tứ\s+giác))?"
                 r"\s+[A-Z][0-9]*'?(?:\.?[A-Z][0-9]*'?)+")
_YES_NO_RE = re.compile(r"\bcó\b[^.?!]*\bkhông\s*\??\s*$|\bphải\s+không\b|\bhay\s+không\b", re.IGNORECASE)


def _items(s: str, item: str) -> list[str]:
    return re.findall(item, s)


def _tetra_labels(text: str) -> list[str]:
    return [m.replace(".", "") for m in re.findall(r"(?i:tứ\s+diện)\s+([A-Z]\.?[A-Z]{3})(?![A-Z0-9'])", text)]


def _declared_solids(text: str) -> set[str]:
    return {m.replace(".", "") for m in re.findall(
        r"(?i:tứ\s+diện|chóp|lăng\s+trụ(?:\s+đứng)?|hình\s+hộp(?:\s+chữ\s+nhật)?|lập\s+phương)\s+"
        r"([A-Z][0-9]*'?(?:\.?[A-Z][0-9]*'?){3,7})(?![A-Z0-9'])", text)}


def _apply_v15_composition(
    cur: str,
    *,
    norm0: str,
    pos_map: list[int],
    steps: list[VerifiedNormalizationStep],
) -> tuple[str, list[int]]:
    """`VN12`–`VN17`: closed compositional constructions → canonical premises / requests (see block comment above)."""
    text = cur

    # VN12a "ba cạnh xuất phát từ (đỉnh) P đôi một vuông góc" in the ONE declared tetrahedron that contains P
    def _repl_edges_from(m: re.Match[str]) -> str:
        p = m["p"]
        tets = sorted({t for t in _tetra_labels(text) if p in t})
        if len(tets) != 1:
            return m.group(0)
        others = [x for x in re.findall(r"[A-Z][0-9]*'?", tets[0]) if x != p]
        return f"{p}{others[0]}, {p}{others[1]}, {p}{others[2]} đôi một vuông góc"

    cur, pos_map = _apply_safe_sub(
        cur, norm0=norm0, pos_map=pos_map, rule_id="VN12_EDGES_FROM_VERTEX_PAIRWISE_PERP",
        pattern=re.compile(rf"(?:ba|các)\s+cạnh\s+(?:xuất\s+phát\s+)?từ\s+(?:đỉnh\s+)?(?P<p>[A-Z][0-9]*'?)\s+{_PERP_PAIRWISE}",
                           re.UNICODE),
        repl=_repl_edges_from, steps=steps, skip_if_cond_or_neg=True, scope="LOCAL_ENTITY",
        evidence="three_edges_from_one_vertex_of_the_declared_tetrahedron")

    # VN12b "các góc XPY, YPZ, ZPX (đều) (là góc) vuông" — three angles at P covering the three pairs of {X, Y, Z}
    def _repl_right_angles(m: re.Match[str]) -> str:
        angs = re.findall(r"([A-Z])([A-Z])([A-Z])", m["angs"])
        if len(angs) != 3 or len({a[1] for a in angs}) != 1:
            return m.group(0)
        p = angs[0][1]
        pairs = {frozenset((a[0], a[2])) for a in angs}
        legs = sorted({x for pr in pairs for x in pr})
        if len(pairs) != 3 or len(legs) != 3 or p in legs:
            return m.group(0)
        return f"{p}{legs[0]}, {p}{legs[1]}, {p}{legs[2]} đôi một vuông góc"

    cur, pos_map = _apply_safe_sub(
        cur, norm0=norm0, pos_map=pos_map, rule_id="VN12_THREE_RIGHT_ANGLES_AT_VERTEX",
        pattern=re.compile(r"(?:các|ba)\s+góc\s+(?P<angs>[A-Z]{3}\s*,\s*[A-Z]{3}\s*,?\s*(?:và\s+)?[A-Z]{3})\s+"
                           r"(?:đều\s+)?(?:là\s+)?(?:(?:các\s+)?góc\s+)?vuông(?![\w])", re.UNICODE),
        repl=_repl_right_angles, steps=steps, skip_if_cond_or_neg=True, scope="LOCAL_ENTITY",
        evidence="three_right_angles_at_one_vertex")

    # VN13 one segment, two predicates (length and perpendicularity) — the SAME segment carries both
    def _len_perp(seg: str, val: str, tgt: str) -> str:
        return f"{seg} = {val} và {seg} vuông góc với {tgt}"

    cur, pos_map = _apply_safe_sub(
        cur, norm0=norm0, pos_map=pos_map, rule_id="VN13_SEG_LENGTH_AND_PERP",
        pattern=re.compile(rf"(?:cạnh\s+(?:bên\s+)?)?(?P<s>{_SEG})\s+(?:dài|có\s+độ\s+dài)\s+(?:bằng\s+|là\s+)?(?P<v>{_VAL})"
                           rf"\s+và\s+vuông\s+góc\s+với\s+(?P<t>{_PERP_TARGET})", re.UNICODE),
        repl=lambda m: _len_perp(m["s"], m["v"], m["t"]), steps=steps, skip_if_cond_or_neg=True,
        scope="LOCAL_ENTITY", evidence="coordinated_predicates_of_one_segment")
    cur, pos_map = _apply_safe_sub(
        cur, norm0=norm0, pos_map=pos_map, rule_id="VN13_SEG_PERP_AND_LENGTH",
        pattern=re.compile(rf"(?:cạnh\s+(?:bên\s+)?)?(?P<s>{_SEG})\s+(?:vừa\s+)?vuông\s+góc\s+với\s+(?P<t>{_PERP_TARGET})"
                           rf"\s*(?:,\s*)?(?:và|vừa|đồng\s+thời)\s+(?:có\s+)?(?:độ\s+dài|dài)\s+(?:bằng\s+|là\s+)?(?P<v>{_VAL})",
                           re.UNICODE),
        repl=lambda m: f"{m['s']} vuông góc với {m['t']} và {m['s']} = {m['v']}", steps=steps,
        skip_if_cond_or_neg=True, scope="LOCAL_ENTITY", evidence="coordinated_predicates_of_one_segment")

    def _repl_same_seg_eq(m: re.Match[str]) -> str:
        if m["s"] != m["s2"]:
            return m.group(0)
        return f"{m['s']} vuông góc với {m['t']} và {m['s']} = {m['v']}"

    cur, pos_map = _apply_safe_sub(
        cur, norm0=norm0, pos_map=pos_map, rule_id="VN13_SEG_PERP_DONG_THOI_EQ",
        pattern=re.compile(rf"(?P<s>{_SEG})\s+vuông\s+góc\s+với\s+(?P<t>{_PERP_TARGET})\s*,\s*đồng\s+thời\s+"
                           rf"(?P<s2>{_SEG})\s*=\s*(?P<v>{_VAL})", re.UNICODE),
        repl=_repl_same_seg_eq, steps=steps, skip_if_cond_or_neg=True, scope="LOCAL_ENTITY",
        evidence="coordinated_predicates_of_one_segment")

    def _repl_altitude_named(m: re.Match[str]) -> str:
        s2 = m.groupdict().get("s2")
        if s2 is not None and s2 != m["s"]:
            return m.group(0)
        return f"đường cao {m['s']} = {m['v']}"

    cur, pos_map = _apply_safe_sub(
        cur, norm0=norm0, pos_map=pos_map, rule_id="VN13_SEG_IS_ALTITUDE_WITH_LENGTH",
        pattern=re.compile(rf"(?P<s>{_SEG})\s+là\s+(?:đường\s+cao|chiều\s+cao)\s*(?:(?:,\s*|\s+và\s+)(?P<s2>{_SEG})\s*=\s*"
                           rf"|\s+(?:dài|có\s+độ\s+dài|bằng)\s+(?:là\s+)?)(?P<v>{_VAL})", re.UNICODE),
        repl=_repl_altitude_named, steps=steps, skip_if_cond_or_neg=True, scope="LOCAL_ENTITY",
        evidence="named_altitude_with_its_length")
    cur, pos_map = _apply_safe_sub(
        cur, norm0=norm0, pos_map=pos_map, rule_id="VN13_ALTITUDE_IS_SEG_WITH_LENGTH",
        pattern=re.compile(rf"đường\s+cao\s+(?:của\s+(?:hình|khối)\s+chóp\s+)?là\s+(?P<s>{_SEG})\s*(?:,\s*|\s+và\s+)"
                           rf"(?P<s2>{_SEG})\s*=\s*(?P<v>{_VAL})", re.UNICODE),
        repl=_repl_altitude_named, steps=steps, skip_if_cond_or_neg=True, scope="LOCAL_ENTITY",
        evidence="named_altitude_with_its_length")

    # VN13c "chiều cao (hình) chóp bằng V và chân đường cao trùng với (điểm) P" — apex of the ONE declared pyramid with P
    def _repl_height_foot(m: re.Match[str]) -> str:
        pyr = [x for x in re.findall(r"chóp\s+([A-Z][0-9]*'?)\.([A-Z][0-9]*'?(?:[A-Z][0-9]*'?){2,5})", text)
               if m["p"] in re.findall(r"[A-Z][0-9]*'?", x[1])]
        if len(pyr) != 1:
            return m.group(0)
        return f"đường cao {pyr[0][0]}{m['p']} = {m['v']}"

    cur, pos_map = _apply_safe_sub(
        cur, norm0=norm0, pos_map=pos_map, rule_id="VN13_PYRAMID_HEIGHT_WITH_FOOT",
        pattern=re.compile(rf"chiều\s+cao\s+(?:của\s+)?(?:(?:hình|khối)\s+)?chóp\s+(?:bằng|là)\s+(?P<v>{_VAL})\s+và\s+"
                           r"chân\s+đường\s+cao\s+trùng\s+với\s+(?:điểm\s+)?(?P<p>[A-Z][0-9]*'?)(?![\w'])", re.UNICODE),
        repl=_repl_height_foot, steps=steps, skip_if_cond_or_neg=True, scope="LOCAL_ENTITY",
        evidence="pyramid_altitude_from_its_stated_foot")

    # VN14 values distributed over a list, in order; unequal lengths ⇒ unchanged (never guessed)
    def _assign(segs: list[str], vals: list[str]) -> str | None:
        return ", ".join(f"{s} = {v}" for s, v in zip(segs, vals)) if len(segs) == len(vals) >= 2 else None

    def _repl_respective(m: re.Match[str]) -> str:
        segs, vals = _items(m["segs"], _SEG), _items(m["vals"], _VAL)
        out = _assign(segs, vals)
        if out is None:
            return m.group(0)
        if m.groupdict().get("legs"):
            # "hai cạnh góc vuông X, Y" is dropped only when the text states the right angle at their common vertex
            common = set(segs[0]) & set(segs[1]) if len(segs) == 2 else set()
            if len(common) != 1 or not re.search(
                    rf"vuông(?:\s+cân)?\s+(?:tại|ở)\s+{re.escape(next(iter(common)))}(?![\w'])", text):
                return m.group(0)
        mid = m.groupdict().get("mid")
        return f"{m['segs']} đôi một vuông góc, {out}" if mid else out

    resp = r"(?:lần\s+lượt|tương\s+ứng|theo\s+thứ\s+tự)"
    cur, pos_map = _apply_safe_sub(
        cur, norm0=norm0, pos_map=pos_map, rule_id="VN14_RESPECTIVE_VALUES",
        pattern=re.compile(
            rf"(?:(?P<legs>hai\s+cạnh\s+góc\s+vuông)\s+|(?:độ\s+dài|các\s+cạnh|các\s+đoạn(?:\s+thẳng)?|ba\s+cạnh|hai\s+cạnh)\s+)?"
            rf"(?P<segs>{_SEG_LIST}|{_SEG}(?:\s*,\s*{_SEG})+)"
            rf"(?:\s+(?P<mid>{_PERP_PAIRWISE}))?\s*(?:,\s*|\s+và\s+)?(?:\s*có\s+)?"
            rf"(?:\s*(?:độ\s+dài|dài))?\s*(?:{resp}\s+(?:là\s+|bằng\s+)?|(?:là|bằng)\s+{resp}\s+)"
            rf"(?P<vals>{_VAL_LIST}|{_VAL}(?:\s*,\s*{_VAL})+)", re.UNICODE),
        repl=_repl_respective, steps=steps, skip_if_cond_or_neg=True, scope="LOCAL_ENTITY_LIST",
        evidence="ordered_list_value_alignment_with_equal_lengths")
    cur, pos_map = _apply_safe_sub(
        cur, norm0=norm0, pos_map=pos_map, rule_id="VN14_LIST_LENGTHS_IN_ORDER",
        pattern=re.compile(
            rf"(?:(?P<legs>hai\s+cạnh\s+góc\s+vuông)\s+)?(?P<segs>{_SEG}(?:\s*,\s*|\s+và\s+){_SEG})\s+(?:dài|có\s+độ\s+dài)\s+"
            rf"(?P<vals>{_VAL}(?:\s*,\s*|\s+và\s+){_VAL})(?![\w'])", re.UNICODE),
        repl=_repl_respective, steps=steps, skip_if_cond_or_neg=True, scope="LOCAL_ENTITY_LIST",
        evidence="two_segments_two_lengths_in_order")

    # VN15 "chiều cao (của) (hình/khối) lăng trụ (đứng …) bằng/là/= V" → the form the parser reads
    cur, pos_map = _apply_safe_sub(
        cur, norm0=norm0, pos_map=pos_map, rule_id="VN15_PRISM_HEIGHT_FORM",
        pattern=re.compile(r"chiều\s+cao\s+(?:của\s+)?(?:(?:hình|khối)\s+)?lăng\s+trụ(?:\s+đứng)?"
                           r"(?:\s+[A-Z][0-9]*'?(?:\.?[A-Z][0-9]*'?)+)?\s*(?:bằng|là|=)\s*(?=" + _VAL + ")", re.UNICODE),
        repl="chiều cao của lăng trụ là ", steps=steps, skip_if_cond_or_neg=True, scope="LOCAL_ENTITY",
        evidence="prism_height_surface_form")

    # VN16 a sentence that is only a bare drawing request, when exactly one solid is declared
    def _repl_bare_request(m: re.Match[str]) -> str:
        return f"{m['pre']}Vẽ hình." if len(_declared_solids(text)) == 1 else m.group(0)

    cur, pos_map = _apply_safe_sub(
        cur, norm0=norm0, pos_map=pos_map, rule_id="VN16_BARE_SIMULATION_REQUEST",
        pattern=re.compile(r"(?P<pre>(?:^|(?<=[.!?;])\s*))(?:em\s+)?(?:hãy\s+)?(?:mô\s+phỏng|dựng(?:\s+hình)?|vẽ(?:\s+hình)?)"
                           r"(?:\s+(?:giúp|cho)\s+(?:em|mình|tôi))?(?:\s+theo\s+(?:lời\s+)?đề(?:\s+bài)?)?"
                           r"(?:\s+(?:nhé|nha|ạ|với))?\s*[.!]?\s*$", re.IGNORECASE | re.UNICODE | re.MULTILINE),
        repl=_repl_bare_request, steps=steps, skip_if_cond_or_neg=True, scope="REQUEST",
        evidence="bare_request_bound_to_the_only_declared_solid")

    # VN17 a request whose object is followed by the solid and its premises → "Cho <solid> <lead> P. <request>."
    def _repl_question_first(m: re.Match[str]) -> str:
        if _YES_NO_RE.search(m.group(0)) or re.search(r"\bthay\s+đổi\b|\bbất\s+kì\b|\bbất\s+kỳ\b", m.group(0)):
            return m.group(0)
        req, obj, prep, solid, lead, prem = m["req"], m["obj"].strip(), m["prep"], m["solid"], m["lead"], m["prem"].strip()
        asked = f"{obj} {solid}" if not prep else obj
        req_c = req[0].upper() + req[1:]
        return f"Cho {solid} {lead} {prem}. {req_c} {asked}."

    cur, pos_map = _apply_safe_sub(
        cur, norm0=norm0, pos_map=pos_map, rule_id="VN17_QUESTION_FIRST_WITH_PREMISES",
        pattern=re.compile(
            rf"(?:^|(?<=[.!?]\s))(?P<req>(?:(?:em\s+)?hãy\s+)?(?:tính|tìm|xác\s+định|cho\s+biết))\s+"
            rf"(?P<obj>(?:thể\s+tích|diện\s+tích|độ\s+dài|khoảng\s+cách)[^.!?]*?)\s*,?\s*(?:(?P<prep>của|trong)\s+)?"
            rf"(?P<solid>{_SOLID_PHRASE})\s*,?\s+(?P<lead>có|biết(?:\s+rằng)?|với)\s+(?P<prem>[^.!?]+?)\s*[.!]?\s*$",
            re.IGNORECASE | re.UNICODE | re.MULTILINE),
        repl=_repl_question_first, steps=steps, skip_if_cond_or_neg=True, scope="SENTENCE_ORDER",
        evidence="question_first_sentence_reordered_premises_first")
    return cur, pos_map


def _apply_v3_pre_closure(
    cur: str,
    *,
    norm0: str,
    pos_map: list[int],
    steps: list[VerifiedNormalizationStep],
) -> tuple[str, list[int]]:
    """Pre-v2 AXO HYBRID /9 closure rules (`VN06`–`VN11`), strictly non-conditional & non-negated."""
    cur, pos_map = _apply_v15_composition(cur, norm0=norm0, pos_map=pos_map, steps=steps)
    cur, pos_map = _apply_safe_sub(
        cur, norm0=norm0, pos_map=pos_map,
        rule_id="VN06_STRIP_COURTESY_HEADER_COLON",
        pattern=re.compile(
            r"^(?:Thưa\s+(?:thầy|cô|bạn)[^:]{0,40}|Câu\s+hỏi[^:]{0,40}|Bài\s+(?:toán|tập)[^:]{0,30}|Nhờ\s+giải[^:]{0,30}):\s*(?=(?:Cho|Một|Hình|Lăng|Tứ)\b)",
            re.IGNORECASE | re.UNICODE,
        ),
        repl="",
        steps=steps,
        count=1,
        skip_if_cond_or_neg=True,
        scope="TYPOGRAPHY",
        evidence="strip_conversational_prefix_header",
    )
    # Guard whole-text safety for structural reordering (`Nếu`, negation)
    # 1. Question-first reordering (`VN10`): "... , biết <SOLID is ...>?"
    cur, pos_map = _apply_safe_sub(
        cur, norm0=norm0, pos_map=pos_map,
        rule_id="VN10_QUESTION_FIRST_DISTANCE",
        pattern=re.compile(
            r"^(?:Hỏi\s+)?(?:điểm\s+)?([A-Z][0-9']*'?)\s+cách\s+(?:mặt\s+phẳng\s+)?\(([A-Z0-9']{3,6})\)\s+(?:một\s+khoảng\s+)?(?:bằng\s+)?bao\s+nhiêu\s*,\s*biết\s+((?:[A-Z][0-9']*'?){3,6}\.(?:[A-Z][0-9']*'?){3,6})\s+là\s+(hình\s+lập\s+phương|hình\s+hộp\s+chữ\s+nhật)(?:\s+có)?\s+cạnh(?:\s+bằng)?\s+([^\s,.;:!?]+)\s*\??$",
            re.IGNORECASE | re.UNICODE,
        ),
        repl=r"Cho \4 \3 có cạnh bằng \5. Tính khoảng cách từ điểm \1 đến mặt phẳng (\2).",
        steps=steps,
        count=1,
        skip_if_cond_or_neg=True,
        scope="CLAUSE_REORDER",
        evidence="canonical_premise_before_question",
    )

    def _repl_q_first_general(m: re.Match[str]) -> str:
        goal_part = m.group(1).strip().rstrip(".? ")
        prem_part = m.group(2).strip().rstrip(".? ")
        prem_part = re.sub(r"^(?:hãy\s+)?cho\s+", "", prem_part, flags=re.IGNORECASE | re.UNICODE)
        if not re.match(r"^(?:Tứ\s+diện|Hình\s+|Cho\s+)", prem_part, re.IGNORECASE | re.UNICODE):
            return m.group(0)
        if not re.match(r"^Cho\s+", prem_part, re.IGNORECASE | re.UNICODE) and not re.match(r"^Tứ\s+diện\b", prem_part, re.IGNORECASE | re.UNICODE):
            prem_part = f"Cho {prem_part[0].lower()}{prem_part[1:]}"
        return f"{prem_part}. Tính {goal_part}."

    cur, pos_map = _apply_safe_sub(
        cur, norm0=norm0, pos_map=pos_map,
        rule_id="VN10_QUESTION_FIRST_GENERAL",
        pattern=re.compile(
            r"^(?:Hãy\s+)?(?:tính|tìm|xác\s+định)\s+([^.?!]+?)\s*,\s*biết\s+(?:rằng\s+)?([^?!]+?(?:hình\s+chóp|lăng\s+trụ|hình\s+hộp|hình\s+lập\s+phương|tứ\s+diện)[^?!]+?)\s*[.?]?\s*$",
            re.IGNORECASE | re.UNICODE,
        ),
        repl=_repl_q_first_general,
        steps=steps,
        count=1,
        skip_if_cond_or_neg=True,
        scope="CLAUSE_REORDER",
        evidence="canonical_premise_before_question",
    )

    # 2. Casual question forms handled BEFORE v2 `VN05_SEG_BANG` eats `bằng mấy`
    cur, pos_map = _apply_safe_sub(
        cur, norm0=norm0, pos_map=pos_map,
        rule_id="VN10_BANG_MAY",
        pattern=re.compile(
            r"(?:,\s*thì\s+|\s+thì\s+|\.\s*)(?:độ\s+dài\s+)?(?:đoạn\s+(?:thẳng\s+)?)?([A-Z][0-9']*'?[A-Z][0-9']*'?)\s+(?:dài\s+)?(?:bằng|là)\s+mấy\s*\??(?=\s*$)",
            re.IGNORECASE | re.UNICODE,
        ),
        repl=r". Tính độ dài đoạn \1.",
        steps=steps,
        skip_if_cond_or_neg=True,
        scope="GOAL_MARKER",
        evidence="casual_colloquial_bang_may_to_tinh",
    )
    cur, pos_map = _apply_safe_sub(
        cur, norm0=norm0, pos_map=pos_map,
        rule_id="VN07_SEMICOLON_TO_COMMA",
        pattern=re.compile(r"\s*;\s*(?=[A-Z]|hệ\s+|SA|OA|AB|OB|góc|cạnh|đáy)", re.UNICODE),
        repl=", ",
        steps=steps,
        skip_if_cond_or_neg=True,
        scope="TYPOGRAPHY",
        evidence="normalize_semicolon_clause_separator",
    )
    cur, pos_map = _apply_safe_sub(
        cur, norm0=norm0, pos_map=pos_map,
        rule_id="VN10_DUONG_CHEO_DAI_BAO_NHIEU",
        pattern=re.compile(
            r"\bĐường\s+chéo\s+([A-Z][0-9']*'?[A-Z][0-9']*'?)\s+(?:có\s+độ\s+dài\s+)?dài\s+bao\s+nhiêu\s*\??",
            re.IGNORECASE | re.UNICODE,
        ),
        repl=r"Tính độ dài đoạn \1.",
        steps=steps,
        skip_if_cond_or_neg=True,
        scope="GOAL_MARKER",
        evidence="colloquial_diagonal_length_question",
    )

    # 3. `VN06` Implicit openers & compact shorthands
    cur, pos_map = _apply_safe_sub(
        cur, norm0=norm0, pos_map=pos_map,
        rule_id="VN06_IMPLICIT_MOT_HINH",
        pattern=re.compile(
            r"^(?:Một|Cho\s+một)\s+(hình\s+(?:chóp|lăng\s+trụ|hộp|lập\s+phương)|lăng\s+trụ(?:\s+đứng|\s+đều)?)\b",
            re.IGNORECASE | re.UNICODE,
        ),
        repl=lambda m: f"Cho {m.group(1)[0].lower()}{m.group(1)[1:]}",
        steps=steps,
        count=1,
        skip_if_cond_or_neg=True,
        scope="SOLID_OPENER",
        evidence="canonical_solid_opener_cho",
    )
    cur, pos_map = _apply_safe_sub(
        cur, norm0=norm0, pos_map=pos_map,
        rule_id="VN06_IMPLICIT_BARE_SOLID",
        pattern=re.compile(
            r"^(Hình\s+(?:chóp|lăng\s+trụ|hộp|lập\s+phương)|hình\s+(?:chóp|lăng\s+trụ|hộp|lập\s+phương)|Lăng\s+trụ(?:\s+đứng|\s+đều)?)\b",
            re.UNICODE,
        ),
        repl=lambda m: f"Cho {m.group(1)[0].lower()}{m.group(1)[1:]}",
        steps=steps,
        count=1,
        skip_if_cond_or_neg=True,
        scope="SOLID_OPENER",
        evidence="canonical_solid_opener_cho",
    )
    cur, pos_map = _apply_safe_sub(
        cur, norm0=norm0, pos_map=pos_map,
        rule_id="VN06_SOLID_SEP_DAY",
        pattern=re.compile(
            r"((?:[A-Z][0-9]*'*){1,6}\.(?:[A-Z][0-9]*'*){3,6})(?:\s*:\s*|\s+(?=đáy\b|mặt\s+đáy\b))",
            re.UNICODE,
        ),
        repl=r"\1 có ",
        steps=steps,
        count=1,
        skip_if_cond_or_neg=True,
        scope="SOLID_OPENER",
        evidence="explicit_co_connector_after_solid",
    )
    cur, pos_map = _apply_safe_sub(
        cur, norm0=norm0, pos_map=pos_map,
        rule_id="VN06_BA_KICH_THUOC",
        pattern=re.compile(r"\bcó\s+ba\s+kích\s+thước\s+(?=[A-Z])", re.IGNORECASE | re.UNICODE),
        repl="có ",
        steps=steps,
        skip_if_cond_or_neg=True,
        scope="LOCAL_CLAUSE",
        evidence="cuboid_three_dimensions_shorthand",
    )
    cur, pos_map = _apply_safe_sub(
        cur, norm0=norm0, pos_map=pos_map,
        rule_id="VN06_VOI_DIMENSIONS",
        pattern=re.compile(
            r"((?:[A-Z][0-9]*'*){3,6}\.(?:[A-Z][0-9]*'*){3,6})\s+với\s+(?=[A-Z][0-9']*'?[A-Z][0-9']*'?=)",
            re.UNICODE,
        ),
        repl=r"\1 có ",
        steps=steps,
        skip_if_cond_or_neg=True,
        scope="LOCAL_CLAUSE",
        evidence="prism_dimensions_co_connector",
    )

    def _repl_chained_eq(m: re.Match[str]) -> str:
        segs = [m.group(1), m.group(2)]
        if m.group(3):
            segs.append(m.group(3))
        val = m.group(4)
        # Reject if val looks like another 2-vertex segment (all caps >=2) rather than scalar
        if re.fullmatch(r"(?:[A-Z][0-9']*'?){2,}", val):
            return m.group(0)
        return ", ".join(f"{s} = {val}" for s in segs)

    cur, pos_map = _apply_safe_sub(
        cur, norm0=norm0, pos_map=pos_map,
        rule_id="VN06_CHAINED_SEGMENT_EQ",
        pattern=re.compile(
            r"(?<![A-Z0-9'])([A-Z][0-9']*'?[A-Z][0-9']*'?)\s*=\s*([A-Z][0-9']*'?[A-Z][0-9']*'?)(?:\s*=\s*([A-Z][0-9']*'?[A-Z][0-9']*'?))?\s*=\s*([^\s,.;:!?]+)",
            re.UNICODE,
        ),
        repl=_repl_chained_eq,
        steps=steps,
        skip_if_cond_or_neg=True,
        scope="LOCAL_ENTITY",
        evidence="expand_chained_segment_equality",
    )

    def _repl_cube_canh(m: re.Match[str]) -> str:
        prefix = m.group(1).strip()
        val = m.group(2)
        if not re.search(r"(?:\d|a|√)", val):
            return m.group(0)
        return f"{prefix} có cạnh bằng {val}"

    cur, pos_map = _apply_safe_sub(
        cur, norm0=norm0, pos_map=pos_map,
        rule_id="VN06_CUBE_CANH_BANG",
        pattern=re.compile(
            r"((?:hình\s+lập\s+phương|hình\s+vuông|tam\s+giác\s+đều|lục\s+giác\s+đều)\s+(?:[A-Z0-9'.]+))\s+(?:có\s+)?cạnh\s+(?!bên\b|đáy\b|bằng\b|=)([^\s,.;:!?]+)(?!\s*(?:bằng|=))",
            re.IGNORECASE | re.UNICODE,
        ),
        repl=_repl_cube_canh,
        steps=steps,
        skip_if_cond_or_neg=True,
        scope="LOCAL_ENTITY",
        evidence="explicit_co_canh_bang",
    )

    # 4. `VN07` clause cleanups (mp(SBC), mặt phẳng SBC, filler 'cạnh bên' before perpendicularity, semicolon split)
    cur, pos_map = _apply_safe_sub(
        cur, norm0=norm0, pos_map=pos_map,
        rule_id="VN07_MP_PAREN",
        pattern=re.compile(
            r"(?<![A-Za-zÀ-Ỹà-ỹ])(?:mp\s*\(\s*([A-Z0-9']{3,6})\s*\)|mặt\s+phẳng\s+([A-Z0-9']{3,6}))(?![A-Za-zÀ-Ỹà-ỹ0-9'])",
            re.IGNORECASE | re.UNICODE,
        ),
        repl=r"mặt phẳng (\1\2)",
        steps=steps,
        skip_if_cond_or_neg=True,
        scope="ENTITY_SYNTAX",
        evidence="canonical_parenthesized_plane",
    )
    cur, pos_map = _apply_safe_sub(
        cur, norm0=norm0, pos_map=pos_map,
        rule_id="VN07_CANH_BEN_PERP_PREFIX",
        pattern=re.compile(
            r",\s*cạnh\s+bên\s+([A-Z][0-9']*'?[A-Z][0-9']*'?)\s*(?:⊥|vuông\s+góc)",
            re.UNICODE,
        ),
        repl=lambda m: f", {m.group(1)} vuông góc" if "⊥" not in m.group(0) else f", {m.group(1)} ⊥",
        steps=steps,
        skip_if_cond_or_neg=True,
        scope="LOCAL_CLAUSE",
        evidence="remove_redundant_canh_ben_before_perp",
    )

    def _repl_canh_ben_prism(m: re.Match[str]) -> str:
        seg = m.group(1)
        val = m.group(2)
        s_a, s_b = _sentence_bounds(cur, m.start(), m.end())
        sent = cur[s_a:s_b]
        if re.search(r"lăng\s+trụ\s+(?:đứng|đều)|hộp\s+chữ\s+nhật|lập\s+phương", sent, re.IGNORECASE) and _is_matching_prism_lateral_edge(seg, sent):
            return f"{seg} = {val}"
        return m.group(0)

    cur, pos_map = _apply_safe_sub(
        cur, norm0=norm0, pos_map=pos_map,
        rule_id="VN06_RIGHT_PRISM_CANH_BEN",
        pattern=re.compile(r"\bcạnh\s+bên\s+([A-Z][0-9']*'?[A-Z][0-9']*'?)\s*=\s*([^\s,.;:!?]+)", re.IGNORECASE | re.UNICODE),
        repl=_repl_canh_ben_prism,
        steps=steps,
        skip_if_cond_or_neg=True,
        scope="PRISM_LATERAL_EDGE",
        evidence="right_prism_named_lateral_edge",
    )

    # 5. `VN08` Construction imperatives ("Lấy trung điểm ...", "Hãy dựng hình chiếu ...")
    cur, pos_map = _apply_safe_sub(
        cur, norm0=norm0, pos_map=pos_map,
        rule_id="VN08_LAY_PT_LA_TRUNG_DIEM",
        pattern=re.compile(
            r"\bLấy\s+([A-Z][0-9']*'?)\s+là\s+trung\s+điểm\b",
            re.UNICODE,
        ),
        repl=r"Gọi \1 là trung điểm",
        steps=steps,
        skip_if_cond_or_neg=True,
        scope="AUXILIARY_POINT",
        evidence="imperative_lay_point_la_trung_diem_to_goi",
    )
    cur, pos_map = _apply_safe_sub(
        cur, norm0=norm0, pos_map=pos_map,
        rule_id="VN08_LAY_TRUNG_DIEM",
        pattern=re.compile(
            r"\bLấy\s+trung\s+điểm\s+(?:của\s+)?(?:(?:đoạn\s+thẳng|đoạn|cạnh)\s+)?([A-Z][0-9']*'?[A-Z][0-9']*'?)\s*(?:,\s*)?(?:rồi|sau\s+đó)?\s*đặt\s+tên\s+(?:nó\s+)?là\s+([A-Z][0-9']*'?)\b",
            re.IGNORECASE | re.UNICODE,
        ),
        repl=r"Gọi \2 là trung điểm của cạnh \1",
        steps=steps,
        skip_if_cond_or_neg=True,
        scope="AUXILIARY_POINT",
        evidence="imperative_midpoint_to_canonical_goi",
    )

    def _repl_dung_hinh_chieu(m: re.Match[str]) -> str:
        src_p = m.group(1)
        tgt = m.group(2)
        img_p = m.group(3)
        tail = m.group(4).strip()
        if tail:
            tail = re.sub(r"^(?:và|rồi|sau\s+đó)\s+", "", tail, flags=re.IGNORECASE | re.UNICODE).strip()
            tail = f" {tail[0].upper()}{tail[1:]}" if tail else ""
        return f"Gọi {img_p} là hình chiếu vuông góc của {src_p} lên {tgt}.{tail}"

    cur, pos_map = _apply_safe_sub(
        cur, norm0=norm0, pos_map=pos_map,
        rule_id="VN08_DUNG_HINH_CHIEU",
        pattern=re.compile(
            r"\b(?:Hãy\s+)?(?:dựng|kẻ|hạ)\s+hình\s+chiếu\s+vuông\s+góc\s+của\s+(?:điểm\s+)?([A-Z][0-9']*'?)\s+(?:lên|trên|xuống)\s+(đường\s+thẳng\s+[A-Z0-9']{2,4}|mặt\s+phẳng\s*\([A-Z0-9']{3,6}\))\s*,\s*gọi\s+(?:điểm\s+đó\s+)?là\s+([A-Z][0-9']*'?)(?:\s*,\s*(?:rồi|sau\s+đó)|\s+(?:rồi|sau\s+đó))?\s*(.*?)$",
            re.IGNORECASE | re.UNICODE,
        ),
        repl=_repl_dung_hinh_chieu,
        steps=steps,
        skip_if_cond_or_neg=True,
        scope="AUXILIARY_POINT",
        evidence="imperative_projection_to_canonical_goi",
    )
    return cur, pos_map


def _apply_v3_post_closure(
    cur: str,
    *,
    norm0: str,
    pos_map: list[int],
    steps: list[VerifiedNormalizationStep],
) -> tuple[str, list[int]]:
    """Post-v2 AXO HYBRID /9 closure rules (`VN07`, `VN09`, `VN10`, `VN11`)."""
    # Resolve remaining bare `mặt đáy` / `đáy` in perpendicularity or angle-to-base when base is unique
    base_lbl = _implicit_solid_base_in_sentence(cur, use_v2=True)
    m_sol_all = _SOLID_TOKEN_RE.search(cur)
    solid_lbl = m_sol_all.group(0) if m_sol_all else None
    if base_lbl:
        cur, pos_map = _apply_safe_sub(
            cur, norm0=norm0, pos_map=pos_map,
            rule_id="VN06_IMPLICIT_BASE_LABEL_SHAPE",
            pattern=re.compile(
                r"\bđáy\s+(hình\s+(?:vuông|chữ\s+nhật|thoi|bình\s+hành)|tam\s+giác(?:\s+(?:vuông|đều|cân|vuông\s+cân))?)\b(?!\s+[A-Z])",
                re.UNICODE,
            ),
            repl=rf"đáy {base_lbl} là \1",
            steps=steps,
            skip_if_cond_or_neg=True,
            scope="SOLID_BASE",
            evidence="bind_unique_solid_base_label_to_shape",
        )
        cur, pos_map = _apply_safe_sub(
            cur, norm0=norm0, pos_map=pos_map,
            rule_id="VN07_IMPLICIT_MAT_DAY_PERP",
            pattern=re.compile(
                r"(?i:\bvuông\s+góc\s+(?:với\s+)?(?:mặt\s+đáy|đáy)\b)(?!\s*\(?[A-Z])",
                re.UNICODE,
            ),
            repl=f"vuông góc với ({base_lbl})",
            steps=steps,
            skip_if_cond_or_neg=True,
            scope="SOLID_BASE",
            evidence="resolve_unique_base_in_perpendicular",
        )
        cur, pos_map = _apply_safe_sub(
            cur, norm0=norm0, pos_map=pos_map,
            rule_id="VN07_IMPLICIT_MAT_DAY_GOAL",
            pattern=re.compile(
                r"((?i:\b(?:và|với|tạo\s+với)\s+))(?i:mặt\s+đáy|đáy)\b(?!\s*\(?[A-Z])",
                re.UNICODE,
            ),
            repl=rf"\1mặt phẳng ({base_lbl})",
            steps=steps,
            skip_if_cond_or_neg=True,
            scope="SOLID_BASE",
            evidence="resolve_unique_base_in_goal_or_angle",
        )
    if solid_lbl:
        cur, pos_map = _apply_safe_sub(
            cur, norm0=norm0, pos_map=pos_map,
            rule_id="VN06_IMPLICIT_VOLUME_SOLID",
            pattern=re.compile(
                r"(?i:\b(thể\s+tích\s+(?:khối\s+)?(?:chóp|lăng\s+trụ|hộp|tứ\s+diện)))(?=\s*(?:[.,;?!]|$))",
                re.UNICODE,
            ),
            repl=rf"\1 {solid_lbl}",
            steps=steps,
            skip_if_cond_or_neg=True,
            scope="GOAL_MARKER",
            evidence="bind_unique_solid_notation_to_volume_goal",
        )
    cur, pos_map = _apply_safe_sub(
        cur, norm0=norm0, pos_map=pos_map,
        rule_id="VN07_DUONG_CHEO_TO_DUONG_THANG",
        pattern=re.compile(
            r"(?i:\bđường\s+chéo\s+)([A-Z][0-9']*'?[A-Z][0-9']*'?)(?=\s*(?:và|với)\s+(?:mặt\s+phẳng|\())",
            re.UNICODE,
        ),
        repl=r"đường thẳng \1",
        steps=steps,
        skip_if_cond_or_neg=True,
        scope="GOAL_MARKER",
        evidence="diagonal_segment_between_angle_operands",
    )

    # `VN10` Colloquial goal stems & `VN11` trig goal canonicalization
    cur, pos_map = _apply_safe_sub(
        cur, norm0=norm0, pos_map=pos_map,
        rule_id="VN10_HOI_CACH_MAT_PHANG",
        pattern=re.compile(
            r"\bHỏi\s+điểm\s+([A-Z][0-9']*'?)\s+cách\s+mặt\s+phẳng\s*\(([A-Z0-9']{3,6})\)\s+(?:một\s+khoảng\s+)?bằng\s+bao\s+nhiêu\s*\??",
            re.IGNORECASE | re.UNICODE,
        ),
        repl=r"Tính khoảng cách từ điểm \1 đến mặt phẳng (\2).",
        steps=steps,
        skip_if_cond_or_neg=True,
        scope="GOAL_MARKER",
        evidence="colloquial_cach_to_khoang_cach",
    )
    cur, pos_map = _apply_safe_sub(
        cur, norm0=norm0, pos_map=pos_map,
        rule_id="VN10_KC_BAO_NHIEU_VAY_A",
        pattern=re.compile(
            r"\bkhoảng\s+cách\s+từ\s+([A-Z][0-9']*'?)\s+(?:tới|đến)\s+mặt\s+phẳng\s*\(([A-Z0-9']{3,6})\)\s+(?:là|bằng)\s+bao\s+nhiêu(?:\s+vậy\s+ạ)?\s*\??",
            re.IGNORECASE | re.UNICODE,
        ),
        repl=r"Tính khoảng cách từ \1 đến mặt phẳng (\2).",
        steps=steps,
        skip_if_cond_or_neg=True,
        scope="GOAL_MARKER",
        evidence="colloquial_toi_bao_nhieu_to_tinh",
    )
    cur, pos_map = _apply_safe_sub(
        cur, norm0=norm0, pos_map=pos_map,
        rule_id="VN10_TAO_VOI_GOC",
        pattern=re.compile(
            r"\bĐường\s+thẳng\s+([A-Z][0-9']*'?[A-Z][0-9']*'?)\s+tạo\s+với\s+mặt\s+phẳng\s*\(([A-Z0-9']{3,6})\)\s+một\s+góc\s+bằng\s+bao\s+nhiêu(?:\s*độ)?\s*\??",
            re.IGNORECASE | re.UNICODE,
        ),
        repl=r"Tính góc giữa đường thẳng \1 và mặt phẳng (\2).",
        steps=steps,
        skip_if_cond_or_neg=True,
        scope="GOAL_MARKER",
        evidence="colloquial_tao_voi_mot_goc_to_tinh_goc",
    )
    cur, pos_map = _apply_safe_sub(
        cur, norm0=norm0, pos_map=pos_map,
        rule_id="VN11_COS2_TO_COSIN",
        pattern=re.compile(
            r"\bcos(?:\s*²|\s*\^\s*2)\s+(?:của\s+)?góc\s+(?=giữa|tạo\s+bởi)",
            re.IGNORECASE | re.UNICODE,
        ),
        repl="cosin góc ",
        steps=steps,
        skip_if_cond_or_neg=True,
        scope="GOAL_MARKER",
        evidence="canonical_cos2_question_to_cosin",
    )
    cur, pos_map = _apply_safe_sub(
        cur, norm0=norm0, pos_map=pos_map,
        rule_id="VN09_SPLIT_ENUM_GOALS",
        pattern=re.compile(r"\s+[a-d]\)\s*(?=(?:Tính|Tìm|Xác\s+định)\b)", re.UNICODE),
        repl=" ",
        steps=steps,
        skip_if_cond_or_neg=True,
        scope="MULTI_GOAL",
        evidence="drop_enumerator_before_standalone_goal",
    )
    cur, pos_map = _apply_safe_sub(
        cur, norm0=norm0, pos_map=pos_map,
        rule_id="VN09_SPLIT_COORDINATED_GOALS",
        pattern=re.compile(
            r"(?:,\s*(?:và|rồi(?:\s+suy\s+ra)?|sau\s+đó)?\s*|\s+(?:rồi(?:\s+suy\s+ra)?|sau\s+đó)\s+)(?=(?:tính|diện\s+tích|khoảng\s+cách|thể\s+tích|góc)\b)",
            re.IGNORECASE | re.UNICODE,
        ),
        repl=lambda m: ". " if "tính" in m.group(0).lower() else ". ",
        steps=steps,
        skip_if_cond_or_neg=True,
        scope="MULTI_GOAL",
        evidence="split_coordinated_multi_goals",
    )
    # Ensure split sentences starting directly with `diện tích`/`khoảng cách`/`thể tích`/`góc` have `Tính `
    # STRICT GUARD: only when sentence has NO value assignment (`là 60°`, `bằng 2`, `= 3`)!
    cur, pos_map = _apply_safe_sub(
        cur, norm0=norm0, pos_map=pos_map,
        rule_id="VN09_CAPITALIZE_SPLIT_GOALS",
        pattern=re.compile(
            r"(\.\s+)(?:tính\s+(?=diện\s+tích|khoảng\s+cách|thể\s+tích|góc|độ\s+dài|[A-Z])|(?![^.]*?(?:\bbằng\b|\blà\b|=)\s*[^\s.]*(?:\d|°|√|\ba\b))(diện\s+tích\s+tam\s+giác|khoảng\s+cách\s+từ|thể\s+tích\s+|góc\s+giữa))",
            re.IGNORECASE | re.UNICODE,
        ),
        repl=lambda m: f". Tính {m.group(2)}" if m.group(2) else ". Tính ",
        steps=steps,
        skip_if_cond_or_neg=True,
        scope="MULTI_GOAL",
        evidence="ensure_explicit_tinh_on_split_goals",
    )
    # Expand shorthand `Tính SC`, `Tính BD'` (protect `SC²`, `SA+SB`, etc.)
    cur, pos_map = _apply_safe_sub(
        cur, norm0=norm0, pos_map=pos_map,
        rule_id="VN09_SHORTHAND_TINH_SEG",
        pattern=re.compile(
            r"\bTính\s+([A-Z][0-9']*'?[A-Z][0-9']*'?)(?=\s*(?:[.,;?!]|$))(?![²^0-9])",
            re.UNICODE,
        ),
        repl=r"Tính độ dài đoạn \1",
        steps=steps,
        skip_if_cond_or_neg=True,
        scope="GOAL_MARKER",
        evidence="expand_shorthand_tinh_segment_to_length",
    )

    # Resolve unambiguous 2-line anaphora ("hai đường thẳng đó", "Ngoài ra, hai đường thẳng này hợp với nhau một góc bao nhiêu?")
    m_two_lines = re.search(
        r"hai\s+đường\s+thẳng\s+([A-Z][0-9']*'?[A-Z][0-9']*'?)\s+và\s+([A-Z][0-9']*'?[A-Z][0-9']*'?)",
        cur,
        re.IGNORECASE | re.UNICODE,
    )
    if m_two_lines:
        l1, l2 = m_two_lines.group(1), m_two_lines.group(2)
        cur, pos_map = _apply_safe_sub(
            cur, norm0=norm0, pos_map=pos_map,
            rule_id="VN09_ANAPHORA_TWO_LINES_GOALS",
            pattern=re.compile(
                r"(?:Ngoài\s+ra\s*,\s*)?hai\s+đường\s+thẳng\s+(?:đó|này)\s+hợp\s+với\s+nhau\s+một\s+góc\s+bao\s+nhiêu\s*\??",
                re.IGNORECASE | re.UNICODE,
            ),
            repl=f"Tính góc giữa hai đường thẳng {l1} và {l2}.",
            steps=steps,
            skip_if_cond_or_neg=True,
            scope="ANAPHORA_RESOLUTION",
            evidence="unique_immediately_preceding_line_pair",
        )
        cur, pos_map = _apply_safe_sub(
            cur, norm0=norm0, pos_map=pos_map,
            rule_id="VN09_ANAPHORA_TWO_LINES_NAME",
            pattern=re.compile(r"\bhai\s+đường\s+thẳng\s+(?:đó|này)\b", re.IGNORECASE | re.UNICODE),
            repl=f"hai đường thẳng {l1} và {l2}",
            steps=steps,
            skip_if_cond_or_neg=True,
            scope="ANAPHORA_RESOLUTION",
            evidence="unique_immediately_preceding_line_pair",
        )

    # `VN09` Described centroid / face-center / foot-distance equivalents
    def _repl_centroid_from_to(m: re.Match[str]) -> str:
        tri, pt = m.group(1), m.group(2)
        if pt in re.findall(r"[A-Z][0-9]*'*", tri):
            return m.group(0)
        g_lbl = _unused_point_label(cur)
        return f"Gọi {g_lbl} là trọng tâm tam giác {tri}. Tính độ dài đoạn {g_lbl}{pt}"

    def _repl_centroid_to_from(m: re.Match[str]) -> str:
        pt, tri = m.group(1), m.group(2)
        if pt in re.findall(r"[A-Z][0-9]*'*", tri):
            return m.group(0)
        g_lbl = _unused_point_label(cur)
        return f"Gọi {g_lbl} là trọng tâm tam giác {tri}. Tính độ dài đoạn {pt}{g_lbl}"

    cur, pos_map = _apply_safe_sub(
        cur, norm0=norm0, pos_map=pos_map,
        rule_id="VN09_CENTROID_DISTANCE_TO_NAMED",
        pattern=re.compile(
            r"\bTính\s+khoảng\s+cách\s+từ\s+trọng\s+tâm\s+(?:của\s+)?tam\s+giác\s+([A-Z0-9']{3,6})\s+(?:đến|tới)\s+(?:(?:đỉnh|điểm)\s+)?([A-Z][0-9']*'?)\b",
            re.IGNORECASE | re.UNICODE,
        ),
        repl=_repl_centroid_from_to,
        steps=steps,
        skip_if_cond_or_neg=True,
        scope="DERIVED_POINT",
        evidence="introduce_fresh_named_centroid_for_distance",
    )
    cur, pos_map = _apply_safe_sub(
        cur, norm0=norm0, pos_map=pos_map,
        rule_id="VN09_CENTROID_DISTANCE_TO_NAMED_REV",
        pattern=re.compile(
            r"\bTính\s+khoảng\s+cách\s+từ\s+(?:(?:đỉnh|điểm)\s+)?([A-Z][0-9']*'?)\s+(?:đến|tới)\s+trọng\s+tâm\s+(?:của\s+)?tam\s+giác\s+([A-Z0-9']{3,6})\b",
            re.IGNORECASE | re.UNICODE,
        ),
        repl=_repl_centroid_to_from,
        steps=steps,
        skip_if_cond_or_neg=True,
        scope="DERIVED_POINT",
        evidence="introduce_fresh_named_centroid_for_distance",
    )

    if re.search(r"lăng\s+trụ\s+(?:đứng|đều)|hộp\s+chữ\s+nhật|lập\s+phương", cur, re.IGNORECASE):
        def _repl_face_center(m: re.Match[str]) -> str:
            pt = m.group(1)
            face = m.group(2)
            verts = re.findall(r"[A-Z][0-9]*'*", face)
            if len(verts) != 4:
                return m.group(0)
            o_lbl = _unused_point_label(cur, ("O", "I", "K", "P", "Q"))
            return f"Gọi {o_lbl} là trung điểm của cạnh {verts[0]}{verts[2]}. Tính độ dài đoạn {pt}{o_lbl}"

        cur, pos_map = _apply_safe_sub(
            cur, norm0=norm0, pos_map=pos_map,
            rule_id="VN09_RIGHT_PRISM_FACE_CENTER",
            pattern=re.compile(
                r"(?i:\bTính\s+khoảng\s+cách\s+từ\s+(?:(?:đỉnh|điểm)\s+)?)([A-Z][0-9']*'?)(?i:\s+(?:đến|tới)\s+tâm\s+(?:của\s+)?mặt\s+bên\s+)((?:[A-Z][0-9]*'*){4})(?![A-Za-zÀ-Ỹà-ỹ0-9'])",
                re.UNICODE,
            ),
            repl=_repl_face_center,
            steps=steps,
            skip_if_cond_or_neg=True,
            scope="DERIVED_POINT",
            evidence="center_of_rectangular_side_face_is_diagonal_midpoint",
        )

    cur, pos_map = _apply_safe_sub(
        cur, norm0=norm0, pos_map=pos_map,
        rule_id="VN09_PROJECTION_FOOT_DISTANCE",
        pattern=re.compile(
            r"\bTính\s+độ\s+dài\s+đoạn(?:\s+thẳng)?\s+nối\s+([A-Z][0-9']*'?)\s+với\s+chân\s+đường\s+vuông\s+góc\s+hạ\s+từ\s+\1\s+(?:xuống|lên)\s+mặt\s+phẳng\s*\(([A-Z0-9']{3,6})\)",
            re.IGNORECASE | re.UNICODE,
        ),
        repl=r"Tính khoảng cách từ \1 đến mặt phẳng (\2)",
        steps=steps,
        skip_if_cond_or_neg=True,
        scope="GOAL_MARKER",
        evidence="distance_to_orthogonal_foot_equals_point_plane_distance",
    )
    # Clean stray double punctuation like `..`
    cur, pos_map = _apply_safe_sub(
        cur, norm0=norm0, pos_map=pos_map,
        rule_id="VN06_CLEAN_DOUBLE_PUNCT",
        pattern=re.compile(r"\.\s*\."),
        repl=".",
        steps=steps,
        scope="TYPOGRAPHY",
        evidence="deduplicate_sentence_period",
    )
    return cur, pos_map


def normalize_for_slm_grounding(
    raw_text: str,
    *,
    normalizer_version: str = "v2",
) -> VerifiedNormalizationResult:
    """Apply conservative, span-audited Vietnamese geometry surface canonicalization.

    Pass ``normalizer_version="v1"`` for frozen AXO HYBRID /6, ``"v2"`` (default)
    for AXO HYBRID /7, or ``"v3"`` for AXO HYBRID /9 deterministic language closure.
    """
    norm_req = str(normalizer_version or "v2").strip().lower()
    use_v3 = norm_req in ("v3", "3", SLM_VERIFIED_NORMALIZER_V3_VERSION)
    use_v2 = use_v3 or (norm_req not in ("v1", "1", SLM_VERIFIED_NORMALIZER_V1_VERSION))
    out_ver = (
        SLM_VERIFIED_NORMALIZER_V3_VERSION
        if use_v3
        else (SLM_VERIFIED_NORMALIZER_VERSION if use_v2 else SLM_VERIFIED_NORMALIZER_V1_VERSION)
    )

    norm0 = normalize_problem_text(raw_text or "")
    steps: list[VerifiedNormalizationStep] = []
    ambiguity_flags: list[dict[str, Any]] = []

    # 1. Typo detection guard (§6.C2): detect and NEVER auto-rewrite
    checks = _TYPO_CHECKS + (_TYPO_CHECKS_V2_EXTRA if use_v2 else ())
    for tag, pat in checks:
        for m in pat.finditer(norm0):
            ambiguity_flags.append(
                {
                    "code": "TYPO_REQUIRES_CONFIRMATION",
                    "tag": tag,
                    "excerpt": m.group(0),
                    "span": [m.start(), m.end()],
                }
            )
    if ambiguity_flags:
        return VerifiedNormalizationResult(
            normalizer_version=out_ver,
            original_text=raw_text or "",
            canonical_text=norm0,
            changed=False,
            typo_detected=True,
            ambiguity_flags=tuple(ambiguity_flags),
            steps=(),
        )

    cur = norm0
    pos_map = list(range(len(norm0) + 1))

    if use_v3:
        cur, pos_map = _apply_v3_pre_closure(cur, norm0=norm0, pos_map=pos_map, steps=steps)

    # VN01: Whitespace inside parens / around punctuation / explicit degree word
    cur, pos_map = _apply_safe_sub(
        cur, norm0=norm0, pos_map=pos_map,
        rule_id="VN01_PARENS",
        pattern=re.compile(r"\(\s+([A-Z0-9']+)\s*\)|\(\s*([A-Z0-9']+)\s+\)"),
        repl=lambda m: f"({m.group(1) or m.group(2)})",
        steps=steps,
        scope="TYPOGRAPHY",
        evidence="strip_redundant_paren_spaces",
    )
    cur, pos_map = _apply_safe_sub(
        cur, norm0=norm0, pos_map=pos_map,
        rule_id="VN01_SOLID_DOT_SPACE",
        pattern=re.compile(r"\b([A-Z][0-9]*'*)\s*\.\s+([A-Z][0-9']*(?:[A-Z0-9']*){2,})\b"),
        repl=lambda m: f"{m.group(1)}.{m.group(2)}",
        steps=steps,
        scope="TYPOGRAPHY",
        evidence="normalize_solid_dot_notation",
    )
    cur, pos_map = _apply_safe_sub(
        cur, norm0=norm0, pos_map=pos_map,
        rule_id="VN01_PUNCT_SPACE",
        pattern=re.compile(r"\s+([,.;:!?])"),
        repl=lambda m: m.group(1),
        steps=steps,
        scope="TYPOGRAPHY",
        evidence="normalize_punctuation_spacing",
    )
    cur, pos_map = _apply_safe_sub(
        cur, norm0=norm0, pos_map=pos_map,
        rule_id="VN01_DEG_WORD",
        pattern=re.compile(r"(\d+)\s*độ\b", re.IGNORECASE | re.UNICODE),
        repl=lambda m: f"{m.group(1)}°",
        steps=steps,
        scope="TYPOGRAPHY",
        evidence="morphological_degree_unit_equivalence",
    )

    # VN02: Non-mathematical conversational / polite classroom / textbook openers
    if use_v2:
        cur, pos_map = _apply_safe_sub(
            cur, norm0=norm0, pos_map=pos_map,
            rule_id="VN02_THUA_THAY_OPENER",
            pattern=re.compile(
                r"^\s*(?:(?:Dạ|Em\s+chào|Chào)\s+)?Thưa\s+(?:thầy|cô)(?:\s+(?:ạ|ơi))?\s*[,:]\s*(?:(?:bài\s+(?:toán\s+)?|đề\s+)?(?:cho|hỏi)\s+)?",
                re.IGNORECASE | re.UNICODE,
            ),
            repl="Cho ",
            steps=steps,
            count=1,
            scope="CONVERSATIONAL_OPENER",
            evidence="strip_non_mathematical_vocative_opener",
        )
    cur, pos_map = _apply_safe_sub(
        cur, norm0=norm0, pos_map=pos_map,
        rule_id="VN02_CONV_PREFIX",
        pattern=re.compile(
            r"^\s*(?:(?:Em\s+đang|Mình\s+đang|Nhờ|Chào|Xin\s+hỏi|Thưa\s+thầy|Thưa\s+cô|Cho\s+(?:em|mình)\s+hỏi|Bài\s+tập(?:\s+hình)?(?:\s+\d+)?|Câu\s+\d+|Ví\s+dụ(?:\s+\d+)?)[^:.!?]{0,100}[:])\s*(?:bài\s+cho\s+|đề\s+cho\s+)?",
            re.IGNORECASE | re.UNICODE,
        ),
        repl="Cho ",
        steps=steps,
        count=1,
        scope="CONVERSATIONAL_OPENER",
        evidence="strip_non_mathematical_prefix_before_colon",
    )
    cur, pos_map = _apply_safe_sub(
        cur, norm0=norm0, pos_map=pos_map,
        rule_id="VN02_DEDUP_OPENER",
        pattern=re.compile(r"^\s*Cho\s+(?:cho|xét|bài\s+cho)\s+", re.IGNORECASE | re.UNICODE),
        repl="Cho ",
        steps=steps,
        count=1,
        scope="CONVERSATIONAL_OPENER",
        evidence="deduplicate_problem_opener",
    )
    cur, pos_map = _apply_safe_sub(
        cur, norm0=norm0, pos_map=pos_map,
        rule_id="VN02_CASE_OPENER",
        pattern=re.compile(r"^\s*Cho\s+(Hình|Khối|Lăng|Tứ)\s+", re.UNICODE),
        repl=lambda m: f"Cho {m.group(1).lower()} ",
        steps=steps,
        count=1,
        scope="CONVERSATIONAL_OPENER",
        evidence="normalize_noun_case_after_opener",
    )

    # VN03: Solid openers
    cur, pos_map = _apply_safe_sub(
        cur, norm0=norm0, pos_map=pos_map,
        rule_id="VN03_TRONG_XET",
        pattern=re.compile(r"^\s*(?:Trong|Xét)\s+(hình|khối|lăng)\s+", re.IGNORECASE | re.UNICODE),
        repl=lambda m: f"Cho {m.group(1).lower()} ",
        steps=steps,
        count=1,
        scope="SOLID_DECLARATION",
        evidence="canonical_solid_declaration_opener",
    )
    if use_v2:
        cur, pos_map = _apply_safe_sub(
            cur, norm0=norm0, pos_map=pos_map,
            rule_id="VN03_XET_TU_DIEN",
            pattern=re.compile(r"^\s*(?:Trong|Xét)\s+(tứ\s+diện(?:\s+đều)?)\s+", re.IGNORECASE | re.UNICODE),
            repl=lambda m: f"Cho {m.group(1).lower()} ",
            steps=steps,
            count=1,
            scope="SOLID_DECLARATION",
            evidence="canonical_tetrahedron_declaration_opener",
        )
    cur, pos_map = _apply_safe_sub(
        cur, norm0=norm0, pos_map=pos_map,
        rule_id="VN03_BARE_CHOP",
        pattern=re.compile(r"^Cho\s+chóp\s+", re.IGNORECASE | re.UNICODE),
        repl="Cho hình chóp ",
        steps=steps,
        count=1,
        scope="SOLID_DECLARATION",
        evidence="insert_implicit_hinh_noun_before_chop",
    )
    cur, pos_map = _apply_safe_sub(
        cur, norm0=norm0, pos_map=pos_map,
        rule_id="VN03_BARE_PRISM",
        pattern=re.compile(r"^(?:Cho\s+)?(lăng\s+trụ\s+(?:đứng|đều)\b)", re.IGNORECASE | re.UNICODE),
        repl=lambda m: f"Cho hình {m.group(1).lower()}",
        steps=steps,
        count=1,
        scope="SOLID_DECLARATION",
        evidence="insert_implicit_hinh_noun_before_lang_tru",
    )
    if use_v2:
        cur, pos_map = _apply_safe_sub(
            cur, norm0=norm0, pos_map=pos_map,
            rule_id="VN03_SOLID_COMMA_DAY",
            pattern=re.compile(
                r"(hình\s+(?:chóp|lăng\s+trụ(?:\s+đứng|\s+đều)?)\s+(?:[A-Z][0-9]*'*)+\.(?:[A-Z][0-9]*'*)+)\s*,\s*(?=(?:mặt\s+)?đáy\b)",
                re.IGNORECASE | re.UNICODE,
            ),
            repl=r"\1 có ",
            steps=steps,
            skip_if_cond_or_neg=True,
            scope="BASE_POLYGON",
            evidence="canonical_solid_to_base_connector",
        )

    # VN04: Inverted / elliptical base assignments
    cur, pos_map = _apply_safe_sub(
        cur, norm0=norm0, pos_map=pos_map,
        rule_id="VN04_NHAN_SHAPE_POLY_DAY",
        pattern=re.compile(
            rf"nhận\s+(hình\s+vuông|hình\s+chữ\s+nhật|hình\s+thoi|tam\s+giác\s+(?:đều|vuông(?:\s+cân)?(?:\s+tại\s+[A-Z0-9']+)?))\s+([A-Z0-9']+)\s+(?:có\s+)?(?:(?:độ\s+dài\s+)?cạnh\s+(?:bằng\s+)?({_QTY_CHAR})\s+)?làm\s+(?:mặt\s+)?đáy",
            re.IGNORECASE | re.UNICODE,
        ),
        repl=lambda m: f"có đáy {m.group(2)} là {m.group(1)}" + (f" cạnh {m.group(3)}" if m.group(3) else ""),
        steps=steps,
        skip_if_cond_or_neg=True,
        scope="BASE_POLYGON",
        evidence="nhan_shape_poly_lam_day_equivalence",
    )
    cur, pos_map = _apply_safe_sub(
        cur, norm0=norm0, pos_map=pos_map,
        rule_id="VN04_NHAN_POLY_SHAPE",
        pattern=re.compile(
            rf"nhận\s+([A-Z0-9']+)\s+làm\s+(?:đáy\s+là\s+)?(hình\s+vuông|hình\s+chữ\s+nhật|hình\s+thoi|tam\s+giác\s+(?:đều|vuông(?:\s+cân)?(?:\s+tại\s+[A-Z0-9']+)?))(?:\s+(?:có\s+)?cạnh\s*(?:bằng\s+)?({_QTY_CHAR}))?",
            re.IGNORECASE | re.UNICODE,
        ),
        repl=lambda m: f"có đáy {m.group(1)} là {m.group(2)}" + (f" cạnh {m.group(3)}" if m.group(3) else ""),
        steps=steps,
        skip_if_cond_or_neg=True,
        scope="BASE_POLYGON",
        evidence="nhan_poly_lam_shape_equivalence",
    )

    def _repl_implicit_base(m: re.Match[str]) -> str:
        prefix = m.group(1)
        shape = m.group(2)
        side = m.group(3)
        explicit_poly = m.group(4)
        base_poly = explicit_poly or _implicit_solid_base_in_sentence(prefix, use_v2=use_v2)
        if not base_poly:
            return m.group(0)
        return f"{prefix} có đáy {base_poly} là {shape}" + (f" cạnh {side}" if side else "")

    impl_base_rx = (
        rf"((?:(?:hình|khối)\s+)?(?:chóp|lăng\s+trụ(?:\s+đứng|\s+đều)?)\s+(?:[A-Z][0-9]*'*)+\.(?:[A-Z][0-9]*'*)+),?\s+nhận\s+(hình\s+vuông|tam\s+giác\s+(?:đều|vuông(?:\s+cân)?(?:\s+tại\s+[A-Z0-9']+)?)|hình\s+chữ\s+nhật|hình\s+thoi)(?:\s+(?:có\s+)?cạnh\s*(?:bằng\s+)?({_QTY_CHAR}))?\s+làm\s+(?:mặt\s+)?đáy(?:\s+([A-Z0-9']+))?"
        if use_v2
        else rf"((?:chóp|lăng\s+trụ\s+đứng)\s+[A-Z0-9']+\.[A-Z0-9']+),?\s+nhận\s+(hình\s+vuông|tam\s+giác\s+đều|hình\s+chữ\s+nhật|hình\s+thoi)(?:\s+(?:có\s+)?cạnh\s*(?:bằng\s+)?({_QTY_CHAR}))?\s+làm\s+(?:mặt\s+)?đáy(?:\s+([A-Z0-9']+))?"
    )
    cur, pos_map = _apply_safe_sub(
        cur, norm0=norm0, pos_map=pos_map,
        rule_id="VN04_NHAN_IMPLICIT_BASE",
        pattern=re.compile(impl_base_rx, re.IGNORECASE | re.UNICODE),
        repl=_repl_implicit_base,
        steps=steps,
        skip_if_cond_or_neg=True,
        scope="BASE_POLYGON",
        evidence="bind_base_vertices_from_same_clause_solid_notation",
    )
    cur, pos_map = _apply_safe_sub(
        cur, norm0=norm0, pos_map=pos_map,
        rule_id="VN04_SOLID_BASE_MISSING_DAY_WORD",
        pattern=re.compile(
            r"((?:chóp|lăng\s+trụ(?:\s+đứng)?)\s+[A-Z0-9']+\.([A-Z0-9']+))\s+có\s+\2\s+là\s+(hình\s+vuông|hình\s+chữ\s+nhật|hình\s+thoi|tam\s+giác)",
            re.IGNORECASE | re.UNICODE,
        ),
        repl=r"\1 có đáy \2 là \3",
        steps=steps,
        scope="BASE_POLYGON",
        evidence="insert_missing_day_role_noun_for_explicit_base",
    )
    cur, pos_map = _apply_safe_sub(
        cur, norm0=norm0, pos_map=pos_map,
        rule_id="VN04_MAT_DAY_DO_DAI",
        pattern=re.compile(
            rf"(?:mặt\s+)?đáy\s+([A-Z0-9']+)\s+là\s+(tam\s+giác\s+đều|hình\s+vuông)\s+độ\s+dài\s+cạnh\s+(?:bằng\s+)?({_QTY_CHAR})",
            re.IGNORECASE | re.UNICODE,
        ),
        repl=r"đáy \1 là \2 cạnh \3",
        steps=steps,
        scope="BASE_EDGES",
        evidence="compact_side_length_descriptor",
    )
    cur, pos_map = _apply_safe_sub(
        cur, norm0=norm0, pos_map=pos_map,
        rule_id="VN04_DAY_DEU_CANH",
        pattern=re.compile(rf"\b(đ|Đ)áy\s+([A-Z0-9']+)\s+đều\s+cạnh\s+({_QTY_CHAR})", re.UNICODE),
        repl=lambda m: f"{m.group(1)}áy {m.group(2)} là tam giác đều cạnh {m.group(3)}",
        steps=steps,
        scope="BASE_POLYGON",
        evidence="expand_elliptical_triangular_base_noun",
    )
    cur, pos_map = _apply_safe_sub(
        cur, norm0=norm0, pos_map=pos_map,
        rule_id="VN04_REG_PYR_BASE",
        pattern=re.compile(
            rf"(chóp\s+(?:tam\s+giác\s+|tứ\s+giác\s+)?đều\s+[A-Z0-9']+\.[A-Z0-9']+),?\s*(?:(?:có|với)\s+)?(?:mặt\s+)?đáy(?:\s+[A-Z0-9']+)?\s+(?:có\s+)?cạnh\s*(?:bằng\s+|=|là\s+)?(?!bên\b)({_QTY_CHAR})",
            re.IGNORECASE | re.UNICODE,
        ) if use_v2 else re.compile(
            rf"(chóp\s+(?:tam\s+giác\s+|tứ\s+giác\s+)?đều\s+[A-Z0-9']+\.[A-Z0-9']+),?\s*(?:có\s+)?đáy\s+[A-Z0-9']+\s+(?:có\s+)?cạnh\s*(?:bằng\s+|=|là\s+)?({_QTY_CHAR})",
            re.IGNORECASE | re.UNICODE,
        ),
        repl=r"\1 có cạnh đáy bằng \2",
        steps=steps,
        skip_if_cond_or_neg=True,
        scope="BASE_EDGES",
        evidence="canonical_regular_pyramid_base_edge",
    )

    # VN05 Group A: Universal Quantifiers (NEVER match singular "cạnh bên" or partial quantifiers)
    if use_v2:
        all_lat_rx = re.compile(
            rf"(?<![\w])(?:tất\s+cả\s+(?:các\s+)?|mọi\s+|mỗi\s+|các\s+)cạnh\s+bên(?:\s+đều)?\s+(?:có\s+độ\s+dài\s+)?(?:=|bằng|dài)\s*({_QTY_CHAR})"
            rf"|(?<![\w])cạnh\s+bên\s+đều\s+(?:có\s+độ\s+dài\s+)?(?:=|bằng|dài)\s*({_QTY_CHAR})",
            re.IGNORECASE | re.UNICODE,
        )

        def _repl_all_lat(m: re.Match[str]) -> str:
            pre = cur[: m.start()].lower()
            if re.search(r"(?:một\s+số|vài|một\s+vài|trong|hai|ba|bốn)\s+$", pre):
                return m.group(0)
            return f"các cạnh bên bằng {m.group(1) or m.group(2)}"

        cur, pos_map = _apply_safe_sub(
            cur, norm0=norm0, pos_map=pos_map,
            rule_id="VN05_ALL_LATERAL",
            pattern=all_lat_rx,
            repl=_repl_all_lat,
            steps=steps,
            skip_if_cond_or_neg=True,
            skip_if_sentence_neg=True,
            scope="LATERAL_EDGES",
            evidence="universal_lateral_edge_quantifier_to_canonical_plural",
        )
        cur, pos_map = _apply_safe_sub(
            cur, norm0=norm0, pos_map=pos_map,
            rule_id="VN05_TETRA_ALL_EDGES",
            pattern=re.compile(
                rf"(tứ\s+diện\s+đều\s+(?:[A-Z][0-9]*'*){{4}})\s+(?:có|với)\s+(?:tất\s+cả\s+(?:các\s+)?|các\s+|mọi\s+|mỗi\s+)cạnh(?:\s+đều)?\s+(?:có\s+độ\s+dài\s+)?(?:=|bằng|dài)\s*({_QTY_CHAR})",
                re.IGNORECASE | re.UNICODE,
            ),
            repl=r"\1 có cạnh bằng \2",
            steps=steps,
            skip_if_cond_or_neg=True,
            skip_if_sentence_neg=True,
            scope="ALL_SOLID_EDGES",
            evidence="regular_tetrahedron_universal_edge_quantifier",
        )
    else:
        cur, pos_map = _apply_safe_sub(
            cur, norm0=norm0, pos_map=pos_map,
            rule_id="VN05_ALL_LATERAL",
            pattern=re.compile(
                rf"(?:tất\s+cả\s+)?(?:các\s+|mọi\s+)?cạnh\s+bên\s+đều\s+(?:có\s+độ\s+dài\s+)?(?:bằng|dài)\s+({_QTY_CHAR})",
                re.IGNORECASE | re.UNICODE,
            ),
            repl=r"các cạnh bên bằng \1",
            steps=steps,
            skip_if_cond_or_neg=True,
            scope="LATERAL_EDGES",
        )

    cur, pos_map = _apply_safe_sub(
        cur, norm0=norm0, pos_map=pos_map,
        rule_id="VN05_LAT_EDGE_DO_DAI",
        pattern=re.compile(
            rf"cạnh\s+bên\s+([A-Z0-9']+)\s+có\s+độ\s+dài\s+bằng\s+({_QTY_CHAR})",
            re.IGNORECASE | re.UNICODE,
        ),
        repl=r"\1=\2",
        steps=steps,
        skip_if_cond_or_neg=True,
        scope="LOCAL_ENTITY",
        evidence="canonical_named_segment_length_assignment",
    )

    # VN05 Group C: Contrastive non-conditional "còn <SEG> thì ..."
    if use_v2:
        cur, pos_map = _apply_safe_sub(
            cur, norm0=norm0, pos_map=pos_map,
            rule_id="VN05_CON_THI",
            pattern=re.compile(
                r",\s*còn\s+(?:(?:cạnh(?:\s+bên)?|đoạn(?:\s+thẳng)?)\s+)?([A-Z][0-9]*'*[A-Z][0-9]*'*)\s+thì\s+(?:(vuông\s+góc\s+(?:với\s+)?)|(?:có\s+độ\s+dài\s+)?(?:=|bằng|dài)\s*(?=[a-zA-Z0-9√]))",
                re.IGNORECASE | re.UNICODE,
            ),
            repl=lambda m: f", {m.group(1)} {m.group(2)}" if m.group(2) else f", {m.group(1)}=",
            steps=steps,
            skip_if_cond_or_neg=True,
            skip_if_sentence_neg=True,
            scope="CONTRASTIVE_FACT",
            evidence="non_conditional_contrastive_conjunction_con_thi",
        )
    else:
        cur, pos_map = _apply_safe_sub(
            cur, norm0=norm0, pos_map=pos_map,
            rule_id="VN05_CON_THI",
            pattern=re.compile(
                r",\s*còn\s+([A-Z0-9']+)\s+thì\s+(vuông\s+góc\s+(?:với\s+)?|=)",
                re.IGNORECASE | re.UNICODE,
            ),
            repl=lambda m: f", {m.group(1)} {m.group(2)}",
            steps=steps,
            skip_if_cond_or_neg=True,
            scope="CONTRASTIVE_FACT",
        )

    cur, pos_map = _apply_safe_sub(
        cur, norm0=norm0, pos_map=pos_map,
        rule_id="VN05_DONG_THOI",
        pattern=re.compile(r",?\s*đồng\s+thời\s+(?:cạnh\s+bên\s+|độ\s+dài\s+đoạn\s+)?", re.IGNORECASE | re.UNICODE),
        repl=", ",
        steps=steps,
        skip_if_cond_or_neg=True,
        scope="CLAUSE_CONNECTOR",
        evidence="canonical_additive_clause_connector",
    )
    cur, pos_map = _apply_safe_sub(
        cur, norm0=norm0, pos_map=pos_map,
        rule_id="VN05_THANG_DUNG",
        pattern=re.compile(r"thẳng\s+đứng\s+vuông\s+góc", re.IGNORECASE | re.UNICODE),
        repl="vuông góc",
        steps=steps,
        scope="LOCAL_ENTITY",
        evidence="remove_pleonastic_vertical_modifier",
    )

    # VN05 Group B: Face-plane & base-plane perpendicularity (ONLY 3+ vertex face/triangle, NEVER 2-vertex line)
    if use_v2:
        cur, pos_map = _apply_safe_sub(
            cur, norm0=norm0, pos_map=pos_map,
            rule_id="VN05_SPLIT_MAT_BEN_CLAUSE",
            pattern=re.compile(
                r"(đáy\s+[A-Z0-9']{3,}\s+là\s+(?:hình\s+vuông|hình\s+chữ\s+nhật|hình\s+thoi|tam\s+giác(?:\s+đều|\s+vuông(?:\s+cân)?)?)(?:\s+cạnh\s+" + _QTY_CHAR + r")?)\s*,\s*(mặt\s+bên\s+(?:[A-Z][0-9]*'*){3,}\b)",
                re.IGNORECASE | re.UNICODE,
            ),
            repl=lambda m: f"{m.group(1)}. {m.group(2)[0].upper()}{m.group(2)[1:]}",
            steps=steps,
            skip_if_cond_or_neg=True,
            skip_if_sentence_neg=True,
            scope="FACE_PLANE",
            evidence="split_comma_joined_lateral_face_clause_to_sentence",
        )
        cur, pos_map = _apply_safe_sub(
            cur, norm0=norm0, pos_map=pos_map,
            rule_id="VN05_NAM_VUONG_GOC_FACE",
            pattern=re.compile(
                r"((?:[Mm]ặt\s+bên|[Tt]am\s+giác)\s+(?:[A-Z][0-9]*'*){3,}[^.;!?]*?)\s+nằm\s+vuông\s+góc\s+với\s+((?:mặt\s+phẳng\s+|mặt\s+)?đáy(?:\s*\(?(?:[A-Z][0-9]*'*){3,}\)?)?)",
                re.UNICODE,
            ),
            repl=r"\1 và nằm trong mặt phẳng vuông góc với \2",
            steps=steps,
            skip_if_cond_or_neg=True,
            skip_if_sentence_neg=True,
            scope="FACE_PLANE",
            evidence="face_nam_vuong_goc_to_nam_trong_mat_phang_vuong_goc",
        )
        cur, pos_map = _apply_safe_sub(
            cur, norm0=norm0, pos_map=pos_map,
            rule_id="VN05_NAM_TRONG_FACE_PERP",
            pattern=re.compile(
                r"([Mm]ặt\s+bên\s+[A-Z0-9']+)\s+(?:là\s+tam\s+giác\s+)?đều\s+và\s+nằm\s+trong\s+mặt\s+phẳng\s+vuông\s+góc\s+với\s+(?:mặt(?:\s+phẳng)?\s+)?đáy\s+\(?([A-Z0-9']{3,})\)?",
                re.UNICODE,
            ),
            repl=r"\1 là tam giác đều và vuông góc với đáy \2",
            steps=steps,
            skip_if_cond_or_neg=True,
            skip_if_sentence_neg=True,
            scope="FACE_PLANE",
            evidence="canonical_equilateral_face_perpendicular_base",
        )
        cur, pos_map = _apply_safe_sub(
            cur, norm0=norm0, pos_map=pos_map,
            rule_id="VN05_VUONG_GOC_MAT_DAY_PAREN",
            pattern=re.compile(
                r"vuông\s+góc(?:\s+với)?\s+mặt(?:\s+phẳng)?\s+đáy\s+(\([A-Z0-9']{3,}\))",
                re.IGNORECASE | re.UNICODE,
            ),
            repl=r"vuông góc với \1",
            steps=steps,
            skip_if_cond_or_neg=True,
            skip_if_sentence_neg=True,
            scope="LOCAL_CLAUSE",
            evidence="canonical_perpendicular_base_parenthesized_plane",
        )
    else:
        cur, pos_map = _apply_safe_sub(
            cur, norm0=norm0, pos_map=pos_map,
            rule_id="VN05_NAM_TRONG_FACE_PERP",
            pattern=re.compile(
                r"([Mm]ặt\s+bên\s+[A-Z0-9']+)\s+(?:là\s+tam\s+giác\s+)?đều\s+và\s+nằm\s+trong\s+mặt\s+phẳng\s+vuông\s+góc\s+với\s+(?:mặt\s+)?đáy\s+([A-Z0-9']+)",
                re.UNICODE,
            ),
            repl=r"\1 là tam giác đều và vuông góc với đáy \2",
            steps=steps,
            skip_if_cond_or_neg=True,
            scope="FACE_PLANE",
            evidence="canonical_equilateral_face_perpendicular_base",
        )

    cur, pos_map = _apply_safe_sub(
        cur, norm0=norm0, pos_map=pos_map,
        rule_id="VN05_GOC_TAO_BOI",
        pattern=re.compile(r"góc\s+tạo\s+bởi\s+", re.IGNORECASE | re.UNICODE),
        repl="góc giữa ",
        steps=steps,
        scope="LOCAL_CLAUSE",
        evidence="synonym_angle_between_planes_or_lines",
    )
    cur, pos_map = _apply_safe_sub(
        cur, norm0=norm0, pos_map=pos_map,
        rule_id="VN05_DO_DUOC",
        pattern=re.compile(r"đo\s+được\s+(?=\d)", re.IGNORECASE | re.UNICODE),
        repl="bằng ",
        steps=steps,
        scope="LOCAL_CLAUSE",
        evidence="synonym_angle_value_assignment",
    )
    cur, pos_map = _apply_safe_sub(
        cur, norm0=norm0, pos_map=pos_map,
        rule_id="VN05_BIET_CENTROID",
        pattern=re.compile(
            r"\bBiết\s+([A-Z][0-9']*)\s+là\s+trọng\s+tâm\s+tam\s+giác\s+([A-Z0-9']+)\s+và\s+",
            re.UNICODE,
        ),
        repl=r"Gọi \1 là trọng tâm tam giác \2, ",
        steps=steps,
        skip_if_cond_or_neg=True,
        scope="LOCAL_ENTITY",
        evidence="canonical_centroid_clause_opener",
    )
    cur, pos_map = _apply_safe_sub(
        cur, norm0=norm0, pos_map=pos_map,
        rule_id="VN05_DAT_MID",
        pattern=re.compile(
            r"Đặt\s+([A-Z][0-9']*)\s+là\s+điểm\s+chính\s+giữa\s+(?:cạnh\s+)?([A-Z0-9']+)\s+trong\s+(hình\s+chóp\s+[A-Z0-9']+\.[A-Z0-9']+)\.",
            re.UNICODE,
        ),
        repl=r"Cho \3, gọi \1 là trung điểm \2.",
        steps=steps,
        scope="LOCAL_ENTITY",
        evidence="reorder_declared_solid_before_midpoint",
    )
    cur, pos_map = _apply_safe_sub(
        cur, norm0=norm0, pos_map=pos_map,
        rule_id="VN05_DUONG_CAO_VDI",
        pattern=re.compile(
            r"Đường\s+cao\s+([A-Z0-9']+)\s+vuông\s+góc\s+với\s+(\([A-Z0-9']+\))\s+với\s+độ\s+dài\s+([A-Z0-9']+=[^\s,.;]+)",
            re.UNICODE,
        ),
        repl=r"\1 vuông góc với \2, \3",
        steps=steps,
        scope="LOCAL_ENTITY",
        evidence="split_altitude_relation_and_length",
    )

    # VN05 Group E: Compound orthogonal projection onto midpoint ("Hình chiếu ... lên đáy (KLM) là trung điểm I của KL")
    if use_v2:
        cur, pos_map = _apply_safe_sub(
            cur, norm0=norm0, pos_map=pos_map,
            rule_id="VN05_PROJ_MIDPOINT",
            pattern=re.compile(
                r"[Hh]ình\s+chiếu(?:\s+vuông\s+góc)?\s+của\s+([A-Z][0-9]*'*)\s+(?:lên|trên)\s+(?:(?:mặt\s+phẳng|mặt)\s+đáy|mặt\s+phẳng|đáy)\s*\(([A-Z0-9']{3,})\)\s+(?:là|trùng\s+với)\s+trung\s+điểm\s+([A-Z][0-9]*'*)\s+của\s+(?:cạnh\s+|đoạn(?:\s+thẳng)?\s+)?([A-Z0-9']{2,})",
                re.UNICODE,
            ),
            repl=r"Gọi \3 là trung điểm của \4. Hình chiếu vuông góc của \1 lên mặt phẳng (\2) là \3",
            steps=steps,
            skip_if_cond_or_neg=True,
            skip_if_sentence_neg=True,
            scope="PROJECTION_COMPOUND",
            evidence="decompose_projection_onto_midpoint_into_atomic_clauses",
        )

    cur, pos_map = _apply_safe_sub(
        cur, norm0=norm0, pos_map=pos_map,
        rule_id="VN05_DO_DAI_SEG_BANG",
        pattern=re.compile(
            rf"(?:độ\s+dài\s+(?:đoạn\s+(?:thẳng\s+)?)?|cạnh\s+)([A-Z0-9']{{2,4}})\s+(?:có\s+độ\s+dài\s+)?bằng\s+({_QTY_CHAR})",
            re.IGNORECASE | re.UNICODE,
        ),
        repl=r"\1=\2",
        steps=steps,
        skip_if_cond_or_neg=True,
        scope="LOCAL_ENTITY",
        evidence="compact_named_segment_equality",
    )

    if use_v2:
        def _repl_prism_height(m: re.Match[str]) -> str:
            seg = m.group(2)
            qty = m.group(3)
            s_a, s_b = _sentence_bounds(cur, m.start(), m.end())
            sent = cur[s_a:s_b]
            if re.search(r"lăng\s+trụ\s+(?:đứng|đều)", sent, re.IGNORECASE) and _is_matching_prism_lateral_edge(seg, sent):
                return f", {seg}={qty}"
            return m.group(0)

        cur, pos_map = _apply_safe_sub(
            cur, norm0=norm0, pos_map=pos_map,
            rule_id="VN05_CHIEU_CAO_PRISM",
            pattern=re.compile(
                rf"(\s*,\s*|\s+và\s+|\s+với\s+)chiều\s+cao\s+([A-Z][0-9]*'*[A-Z][0-9]*'*)=({_QTY_CHAR})",
                re.IGNORECASE | re.UNICODE,
            ),
            repl=_repl_prism_height,
            steps=steps,
            skip_if_cond_or_neg=True,
            scope="PRISM_HEIGHT",
            evidence="right_prism_lateral_height_edge_equivalence",
        )
    else:
        cur, pos_map = _apply_safe_sub(
            cur, norm0=norm0, pos_map=pos_map,
            rule_id="VN05_CHIEU_CAO_PRISM",
            pattern=re.compile(r",\s*chiều\s+cao\s+([A-Z0-9']+=[^\s,.;]+)", re.IGNORECASE | re.UNICODE),
            repl=r", \1",
            steps=steps,
            scope="PRISM_HEIGHT",
        )

    cur, pos_map = _apply_safe_sub(
        cur, norm0=norm0, pos_map=pos_map,
        rule_id="VN05_SEG_BANG",
        pattern=re.compile(
            rf"(?<![A-Za-zÀ-Ỹà-ỹ0-9'/])([A-Z][0-9']*'?[A-Z][0-9']*'?)(?!/)\s+(?:có\s+độ\s+dài\s+)?bằng\s+(?!\d+\s*°)({_QTY_CHAR})",
            re.UNICODE,
        ),
        repl=r"\1=\2",
        steps=steps,
        skip_if_cond_or_neg=True,
        scope="LOCAL_ENTITY",
        evidence="compact_segment_bang_to_equals",
    )
    cur, pos_map = _apply_safe_sub(
        cur, norm0=norm0, pos_map=pos_map,
        rule_id="VN05_YEU_CAU_GOAL",
        pattern=re.compile(r"Yêu\s+cầu\s+(?:xác\s+định|tính)\b", re.IGNORECASE | re.UNICODE),
        repl="Tính",
        steps=steps,
        scope="GOAL_MARKER",
        evidence="canonical_goal_verb",
    )
    cur, pos_map = _apply_safe_sub(
        cur, norm0=norm0, pos_map=pos_map,
        rule_id="VN05_HAY_TIM_GOAL",
        pattern=re.compile(
            r"\b(?:Hãy\s+(?:xác\s+định|tìm|tính)|Tìm)\s+(?=thể\s+tích|khoảng\s+cách|góc|diện\s+tích|độ\s+dài|tỉ\s+số)",
            re.IGNORECASE | re.UNICODE,
        ),
        repl="Tính ",
        steps=steps,
        scope="GOAL_MARKER",
        evidence="canonical_goal_verb",
    )
    cur, pos_map = _apply_safe_sub(
        cur, norm0=norm0, pos_map=pos_map,
        rule_id="VN05_GOAL_DA_CHO",
        pattern=re.compile(r"thể\s+tích\s+của\s+khối\s+(chóp|lăng\s+trụ|hộp|tứ\s+diện)\s+đã\s+cho", re.IGNORECASE | re.UNICODE),
        repl=r"thể tích khối \1",
        steps=steps,
        scope="GOAL_MARKER",
        evidence="compact_goal_noun_phrase",
    )

    if use_v3:
        cur, pos_map = _apply_v3_post_closure(cur, norm0=norm0, pos_map=pos_map, steps=steps)

    return VerifiedNormalizationResult(
        normalizer_version=out_ver,
        original_text=raw_text or "",
        canonical_text=cur,
        changed=(cur != norm0),
        typo_detected=False,
        ambiguity_flags=(),
        steps=tuple(steps),
    )


__all__ = [
    "SLM_VERIFIED_NORMALIZER_V1_VERSION",
    "SLM_VERIFIED_NORMALIZER_V3_VERSION",
    "SLM_VERIFIED_NORMALIZER_VERSION",
    "VerifiedNormalizationResult",
    "VerifiedNormalizationStep",
    "normalize_for_slm_grounding",
]
