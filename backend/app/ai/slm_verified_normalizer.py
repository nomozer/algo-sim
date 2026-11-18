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


def normalize_for_slm_grounding(
    raw_text: str,
    *,
    normalizer_version: str = "v2",
) -> VerifiedNormalizationResult:
    """Apply conservative, span-audited Vietnamese geometry surface canonicalization.

    Pass ``normalizer_version="v1"`` to reproduce the frozen AXO HYBRID /6 rule table
    exact-for-exact in ablation comparisons; defaults to ``"v2"`` (AXO HYBRID /7 closure).
    """
    use_v2 = str(normalizer_version or "v2").strip().lower() not in ("v1", "1", "slm-verified-normalizer/1")
    out_ver = SLM_VERIFIED_NORMALIZER_VERSION if use_v2 else SLM_VERIFIED_NORMALIZER_V1_VERSION

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
    "SLM_VERIFIED_NORMALIZER_VERSION",
    "VerifiedNormalizationResult",
    "VerifiedNormalizationStep",
    "normalize_for_slm_grounding",
]
