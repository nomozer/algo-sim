# -*- coding: utf-8 -*-
"""Span-audited conservative surface canonicalizer (`slm-verified-normalizer/1`).

Operates strictly *upstream* of SLM extraction and Source Gate (`registry.kiem_nguon`)
inside opt-in ``HYBRID_ROUTE_MODE=local-slm`` (`/6` ``compact_clause``). Every rule:
  - Preserves original text, span, proposed replacement, rule ID, and validation status.
  - Refuses / leaves intact ambiguous Vietnamese diacritic typos (`TYPO_REQUIRES_CONFIRMATION`)
    instead of guessing user intent (`§6.C2`).
  - Never touches negations (`không vuông góc`), conditionals (`Nếu ... thì`), or singular
    underspecified references (`cạnh bên bằng ...` on non-regular pyramids).
  - Never alters sentence boundaries (`.`) or invents dimensions.
"""

from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Any

from app.ai.local_geometry_parser import normalize_problem_text

SLM_VERIFIED_NORMALIZER_VERSION = "slm-verified-normalizer/1"

_TYPO_CHECKS: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("TYPO_VUONG_GOC_TONE", re.compile(r"\bvuôg\s+g[oóòỏõọ]c\b|\bvuông\s+goc\b", re.IGNORECASE | re.UNICODE)),
    ("TYPO_CHOP_TONE", re.compile(r"\b(?:hình|khối)\s+chop\b", re.IGNORECASE | re.UNICODE)),
    ("TYPO_DEN_TONE", re.compile(r"\bchóp\s+(?:tam\s+giác\s+|tứ\s+giác\s+)?đên\b", re.IGNORECASE | re.UNICODE)),
    ("TYPO_TRUNG_DIEM", re.compile(r"\btrung\s+điêm\b", re.IGNORECASE | re.UNICODE)),
    ("TYPO_LANG_TRU", re.compile(r"\blăng\s+tru\b", re.IGNORECASE | re.UNICODE)),
)

_CONDITIONAL_MARKER_RE = re.compile(r"\b(?:nếu|khi|giả\s+sử)\b", re.IGNORECASE | re.UNICODE)
_NEGATED_SPAN_RE = re.compile(
    r"\b(?:không|chẳng|chưa)\s+(?:hề\s+)?(?:vuông\s+góc|vuông|cắt|song\s+song|bằng|đều|cân|trùng|thuộc|nằm\s+trong)\b"
    r"|\bkhông\s+phải\b",
    re.IGNORECASE | re.UNICODE,
)
_SOLID_TOKEN_RE = re.compile(r"\b([A-Z][0-9]*'*)\.([A-Z][0-9']*){3,6}\b")
_QTY_CHAR = r"[^\s,.;:!?]+"


@dataclass(frozen=True)
class VerifiedNormalizationStep:
    rule_id: str
    original_span: tuple[int, int]
    original_excerpt: str
    normalized_excerpt: str
    validation_result: str
    ambiguity_status: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "rule_id": self.rule_id,
            "original_span": [self.original_span[0], self.original_span[1]],
            "original_excerpt": self.original_excerpt,
            "normalized_excerpt": self.normalized_excerpt,
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


def _apply_safe_sub(
    cur: str,
    *,
    rule_id: str,
    pattern: re.Pattern[str],
    repl: Any,
    steps: list[VerifiedNormalizationStep],
    count: int = 0,
    skip_if_cond_or_neg: bool = False,
) -> str:
    """Apply a regex substitution only where it touches neither conditionals nor negations."""
    matches = list(pattern.finditer(cur))
    if not matches:
        return cur
    if count > 0:
        matches = matches[:count]

    out_parts: list[str] = []
    last = 0
    changed_any = False
    for m in matches:
        s0, s1 = m.start(), m.end()
        excerpt = m.group(0)
        # Check sentence around match for conditional/negation safety if requested
        if skip_if_cond_or_neg:
            sent_start = max(cur.rfind(".", 0, s0), cur.rfind(";", 0, s0), cur.rfind("?", 0, s0)) + 1
            sent_end_candidates = [idx for idx in (cur.find(".", s1), cur.find(";", s1), cur.find("?", s1)) if idx != -1]
            sent_end = min(sent_end_candidates) if sent_end_candidates else len(cur)
            sent_slice = cur[sent_start:sent_end]
            if _CONDITIONAL_MARKER_RE.search(sent_slice) or _NEGATED_SPAN_RE.search(excerpt):
                steps.append(
                    VerifiedNormalizationStep(
                        rule_id=rule_id,
                        original_span=(s0, s1),
                        original_excerpt=excerpt,
                        normalized_excerpt=excerpt,
                        validation_result="REJECTED_CONSERVATIVE",
                        ambiguity_status="AMBIGUOUS_REQUIRES_CONFIRMATION",
                    )
                )
                continue
        replacement = repl(m) if callable(repl) else m.expand(repl)
        if replacement == excerpt:
            continue
        out_parts.append(cur[last:s0])
        out_parts.append(replacement)
        last = s1
        changed_any = True
        steps.append(
            VerifiedNormalizationStep(
                rule_id=rule_id,
                original_span=(s0, s1),
                original_excerpt=excerpt,
                normalized_excerpt=replacement,
                validation_result="VALIDATED_MEANING_PRESERVING",
                ambiguity_status="UNAMBIGUOUS",
            )
        )
    if not changed_any:
        return cur
    out_parts.append(cur[last:])
    return "".join(out_parts)


def _implicit_solid_base_in_sentence(sent: str) -> str | None:
    m = _SOLID_TOKEN_RE.search(sent)
    if not m:
        return None
    left, right = m.group(0).split(".", 1)
    # Pyramid S.ABC -> apex len 1, base = right
    if len(re.findall(r"[A-Z][0-9]*'*", left)) == 1 and len(re.findall(r"[A-Z][0-9]*'*", right)) >= 3:
        return right
    # Prism ABC.A'B'C' -> base = left
    if len(re.findall(r"[A-Z][0-9]*'*", left)) >= 3:
        return left
    return None


def normalize_for_slm_grounding(raw_text: str) -> VerifiedNormalizationResult:
    """Apply conservative, span-audited Vietnamese geometry surface canonicalization."""
    norm0 = normalize_problem_text(raw_text or "")
    steps: list[VerifiedNormalizationStep] = []
    ambiguity_flags: list[dict[str, Any]] = []

    # 1. Typo detection guard (§6.C2): detect and NEVER auto-rewrite
    for tag, pat in _TYPO_CHECKS:
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
            normalizer_version=SLM_VERIFIED_NORMALIZER_VERSION,
            original_text=raw_text or "",
            canonical_text=norm0,
            changed=False,
            typo_detected=True,
            ambiguity_flags=tuple(ambiguity_flags),
            steps=(),
        )

    cur = norm0
    # VN01: Whitespace inside parens / around punctuation / explicit degree word
    cur = _apply_safe_sub(
        cur,
        rule_id="VN01_PARENS",
        pattern=re.compile(r"\(\s+([A-Z0-9']+)\s*\)|\(\s*([A-Z0-9']+)\s+\)"),
        repl=lambda m: f"({m.group(1) or m.group(2)})",
        steps=steps,
    )
    cur = _apply_safe_sub(
        cur,
        rule_id="VN01_SOLID_DOT_SPACE",
        pattern=re.compile(r"\b([A-Z][0-9]*'*)\s*\.\s+([A-Z][0-9']*(?:[A-Z0-9']*){2,})\b"),
        repl=lambda m: f"{m.group(1)}.{m.group(2)}",
        steps=steps,
    )
    cur = _apply_safe_sub(
        cur,
        rule_id="VN01_PUNCT_SPACE",
        pattern=re.compile(r"\s+([,.;:!?])"),
        repl=lambda m: m.group(1),
        steps=steps,
    )
    cur = _apply_safe_sub(
        cur,
        rule_id="VN01_DEG_WORD",
        pattern=re.compile(r"(\d+)\s*độ\b", re.IGNORECASE | re.UNICODE),
        repl=lambda m: f"{m.group(1)}°",
        steps=steps,
    )

    # VN02: Non-mathematical conversational / textbook prefix ending in ':'
    cur = _apply_safe_sub(
        cur,
        rule_id="VN02_CONV_PREFIX",
        pattern=re.compile(
            r"^\s*(?:(?:Em\s+đang|Mình\s+đang|Nhờ|Chào|Xin\s+hỏi|Thưa\s+thầy|Thưa\s+cô|Cho\s+(?:em|mình)\s+hỏi|Bài\s+tập(?:\s+hình)?(?:\s+\d+)?|Câu\s+\d+|Ví\s+dụ(?:\s+\d+)?)[^:.!?]{0,100}[:])\s*(?:bài\s+cho\s+|đề\s+cho\s+)?",
            re.IGNORECASE | re.UNICODE,
        ),
        repl="Cho ",
        steps=steps,
        count=1,
    )
    cur = _apply_safe_sub(
        cur,
        rule_id="VN02_DEDUP_OPENER",
        pattern=re.compile(r"^\s*Cho\s+(?:cho|xét|bài\s+cho)\s+", re.IGNORECASE | re.UNICODE),
        repl="Cho ",
        steps=steps,
        count=1,
    )
    cur = _apply_safe_sub(
        cur,
        rule_id="VN02_CASE_OPENER",
        pattern=re.compile(r"^\s*Cho\s+(Hình|Khối|Lăng)\s+", re.UNICODE),
        repl=lambda m: f"Cho {m.group(1).lower()} ",
        steps=steps,
        count=1,
    )

    # VN03: Solid openers ("Trong hình chóp..." / "Xét hình..." / "Cho chóp..." / bare "lăng trụ đứng...")
    cur = _apply_safe_sub(
        cur,
        rule_id="VN03_TRONG_XET",
        pattern=re.compile(r"^\s*(?:Trong|Xét)\s+(hình|khối|lăng)\s+", re.IGNORECASE | re.UNICODE),
        repl=lambda m: f"Cho {m.group(1).lower()} ",
        steps=steps,
        count=1,
    )
    cur = _apply_safe_sub(
        cur,
        rule_id="VN03_BARE_CHOP",
        pattern=re.compile(r"^Cho\s+chóp\s+", re.IGNORECASE | re.UNICODE),
        repl="Cho hình chóp ",
        steps=steps,
        count=1,
    )
    cur = _apply_safe_sub(
        cur,
        rule_id="VN03_BARE_PRISM",
        pattern=re.compile(r"^(?:Cho\s+)?(lăng\s+trụ\s+(?:đứng|đều)\b)", re.IGNORECASE | re.UNICODE),
        repl=lambda m: f"Cho hình {m.group(1).lower()}",
        steps=steps,
        count=1,
    )

    # VN04: Inverted / elliptical base assignments
    cur = _apply_safe_sub(
        cur,
        rule_id="VN04_NHAN_SHAPE_POLY_DAY",
        pattern=re.compile(
            rf"nhận\s+(hình\s+vuông|hình\s+chữ\s+nhật|hình\s+thoi|tam\s+giác\s+(?:đều|vuông(?:\s+cân)?(?:\s+tại\s+[A-Z0-9']+)?))\s+([A-Z0-9']+)\s+(?:có\s+)?(?:(?:độ\s+dài\s+)?cạnh\s+(?:bằng\s+)?({_QTY_CHAR})\s+)?làm\s+(?:mặt\s+)?đáy",
            re.IGNORECASE | re.UNICODE,
        ),
        repl=lambda m: f"có đáy {m.group(2)} là {m.group(1)}" + (f" cạnh {m.group(3)}" if m.group(3) else ""),
        steps=steps,
        skip_if_cond_or_neg=True,
    )
    cur = _apply_safe_sub(
        cur,
        rule_id="VN04_NHAN_POLY_SHAPE",
        pattern=re.compile(
            rf"nhận\s+([A-Z0-9']+)\s+làm\s+(?:đáy\s+là\s+)?(hình\s+vuông|hình\s+chữ\s+nhật|hình\s+thoi|tam\s+giác\s+(?:đều|vuông(?:\s+tại\s+[A-Z0-9']+)?))(?:\s+(?:có\s+)?cạnh\s*(?:bằng\s+)?({_QTY_CHAR}))?",
            re.IGNORECASE | re.UNICODE,
        ),
        repl=lambda m: f"có đáy {m.group(1)} là {m.group(2)}" + (f" cạnh {m.group(3)}" if m.group(3) else ""),
        steps=steps,
        skip_if_cond_or_neg=True,
    )
    # Implicit base name from same-sentence solid notation ("... S.ABCD nhận hình vuông cạnh a làm đáy [ABCD]" / "... ABC.A'B'C' nhận tam giác đều cạnh 2a làm đáy")
    def _repl_implicit_base(m: re.Match[str]) -> str:
        prefix = m.group(1)
        shape = m.group(2)
        side = m.group(3)
        explicit_poly = m.group(4)
        base_poly = explicit_poly or _implicit_solid_base_in_sentence(prefix)
        if not base_poly:
            return m.group(0)
        return f"{prefix} có đáy {base_poly} là {shape}" + (f" cạnh {side}" if side else "")

    cur = _apply_safe_sub(
        cur,
        rule_id="VN04_NHAN_IMPLICIT_BASE",
        pattern=re.compile(
            rf"((?:chóp|lăng\s+trụ\s+đứng)\s+[A-Z0-9']+\.[A-Z0-9']+),?\s+nhận\s+(hình\s+vuông|tam\s+giác\s+đều|hình\s+chữ\s+nhật|hình\s+thoi)(?:\s+(?:có\s+)?cạnh\s*(?:bằng\s+)?({_QTY_CHAR}))?\s+làm\s+(?:mặt\s+)?đáy(?:\s+([A-Z0-9']+))?",
            re.IGNORECASE | re.UNICODE,
        ),
        repl=_repl_implicit_base,
        steps=steps,
        skip_if_cond_or_neg=True,
    )
    cur = _apply_safe_sub(
        cur,
        rule_id="VN04_SOLID_BASE_MISSING_DAY_WORD",
        pattern=re.compile(
            r"((?:chóp|lăng\s+trụ(?:\s+đứng)?)\s+[A-Z0-9']+\.([A-Z0-9']+))\s+có\s+\2\s+là\s+(hình\s+vuông|hình\s+chữ\s+nhật|hình\s+thoi|tam\s+giác)",
            re.IGNORECASE | re.UNICODE,
        ),
        repl=r"\1 có đáy \2 là \3",
        steps=steps,
    )
    cur = _apply_safe_sub(
        cur,
        rule_id="VN04_MAT_DAY_DO_DAI",
        pattern=re.compile(
            rf"(?:mặt\s+)?đáy\s+([A-Z0-9']+)\s+là\s+(tam\s+giác\s+đều|hình\s+vuông)\s+độ\s+dài\s+cạnh\s+(?:bằng\s+)?({_QTY_CHAR})",
            re.IGNORECASE | re.UNICODE,
        ),
        repl=r"đáy \1 là \2 cạnh \3",
        steps=steps,
    )
    cur = _apply_safe_sub(
        cur,
        rule_id="VN04_DAY_DEU_CANH",
        pattern=re.compile(rf"\b(đ|Đ)áy\s+([A-Z0-9']+)\s+đều\s+cạnh\s+({_QTY_CHAR})", re.UNICODE),
        repl=lambda m: f"{m.group(1)}áy {m.group(2)} là tam giác đều cạnh {m.group(3)}",
        steps=steps,
    )
    cur = _apply_safe_sub(
        cur,
        rule_id="VN04_REG_PYR_BASE",
        pattern=re.compile(
            rf"(chóp\s+(?:tam\s+giác\s+|tứ\s+giác\s+)?đều\s+[A-Z0-9']+\.[A-Z0-9']+),?\s*(?:có\s+)?đáy\s+[A-Z0-9']+\s+(?:có\s+)?cạnh\s*(?:bằng\s+|=|là\s+)?({_QTY_CHAR})",
            re.IGNORECASE | re.UNICODE,
        ),
        repl=r"\1 có cạnh đáy bằng \2",
        steps=steps,
    )

    # VN05: Universal lateral edges, contrastive non-conditional "thì", synonyms
    cur = _apply_safe_sub(
        cur,
        rule_id="VN05_ALL_LATERAL",
        pattern=re.compile(
            rf"(?:tất\s+cả\s+)?(?:các\s+|mọi\s+)?cạnh\s+bên\s+đều\s+(?:có\s+độ\s+dài\s+)?(?:bằng|dài)\s+({_QTY_CHAR})",
            re.IGNORECASE | re.UNICODE,
        ),
        repl=r"các cạnh bên bằng \1",
        steps=steps,
        skip_if_cond_or_neg=True,
    )
    cur = _apply_safe_sub(
        cur,
        rule_id="VN05_LAT_EDGE_DO_DAI",
        pattern=re.compile(
            rf"cạnh\s+bên\s+([A-Z0-9']+)\s+có\s+độ\s+dài\s+bằng\s+({_QTY_CHAR})",
            re.IGNORECASE | re.UNICODE,
        ),
        repl=r"\1=\2",
        steps=steps,
        skip_if_cond_or_neg=True,
    )
    cur = _apply_safe_sub(
        cur,
        rule_id="VN05_CON_THI",
        pattern=re.compile(
            r",\s*còn\s+([A-Z0-9']+)\s+thì\s+(vuông\s+góc\s+(?:với\s+)?|=)",
            re.IGNORECASE | re.UNICODE,
        ),
        repl=lambda m: f", {m.group(1)} {m.group(2)}",
        steps=steps,
        skip_if_cond_or_neg=True,
    )
    cur = _apply_safe_sub(
        cur,
        rule_id="VN05_DONG_THOI",
        pattern=re.compile(r",?\s*đồng\s+thời\s+(?:cạnh\s+bên\s+|độ\s+dài\s+đoạn\s+)?", re.IGNORECASE | re.UNICODE),
        repl=", ",
        steps=steps,
        skip_if_cond_or_neg=True,
    )
    cur = _apply_safe_sub(
        cur,
        rule_id="VN05_THANG_DUNG",
        pattern=re.compile(r"thẳng\s+đứng\s+vuông\s+góc", re.IGNORECASE | re.UNICODE),
        repl="vuông góc",
        steps=steps,
    )
    cur = _apply_safe_sub(
        cur,
        rule_id="VN05_NAM_TRONG_FACE_PERP",
        pattern=re.compile(
            r"([Mm]ặt\s+bên\s+[A-Z0-9']+)\s+(?:là\s+tam\s+giác\s+)?đều\s+và\s+nằm\s+trong\s+mặt\s+phẳng\s+vuông\s+góc\s+với\s+(?:mặt\s+)?đáy\s+([A-Z0-9']+)",
            re.UNICODE,
        ),
        repl=r"\1 là tam giác đều và vuông góc với đáy \2",
        steps=steps,
        skip_if_cond_or_neg=True,
    )
    cur = _apply_safe_sub(
        cur,
        rule_id="VN05_GOC_TAO_BOI",
        pattern=re.compile(r"góc\s+tạo\s+bởi\s+", re.IGNORECASE | re.UNICODE),
        repl="góc giữa ",
        steps=steps,
    )
    cur = _apply_safe_sub(
        cur,
        rule_id="VN05_DO_DUOC",
        pattern=re.compile(r"đo\s+được\s+(?=\d)", re.IGNORECASE | re.UNICODE),
        repl="bằng ",
        steps=steps,
    )
    cur = _apply_safe_sub(
        cur,
        rule_id="VN05_BIET_CENTROID",
        pattern=re.compile(
            r"\bBiết\s+([A-Z][0-9']*)\s+là\s+trọng\s+tâm\s+tam\s+giác\s+([A-Z0-9']+)\s+và\s+",
            re.UNICODE,
        ),
        repl=r"Gọi \1 là trọng tâm tam giác \2, ",
        steps=steps,
        skip_if_cond_or_neg=True,
    )
    cur = _apply_safe_sub(
        cur,
        rule_id="VN05_DAT_MID",
        pattern=re.compile(
            r"Đặt\s+([A-Z][0-9']*)\s+là\s+điểm\s+chính\s+giữa\s+(?:cạnh\s+)?([A-Z0-9']+)\s+trong\s+(hình\s+chóp\s+[A-Z0-9']+\.[A-Z0-9']+)\.",
            re.UNICODE,
        ),
        repl=r"Cho \3, gọi \1 là trung điểm \2.",
        steps=steps,
    )
    cur = _apply_safe_sub(
        cur,
        rule_id="VN05_DUONG_CAO_VDI",
        pattern=re.compile(
            r"Đường\s+cao\s+([A-Z0-9']+)\s+vuông\s+góc\s+với\s+(\([A-Z0-9']+\))\s+với\s+độ\s+dài\s+([A-Z0-9']+=[^\s,.;]+)",
            re.UNICODE,
        ),
        repl=r"\1 vuông góc với \2, \3",
        steps=steps,
    )
    cur = _apply_safe_sub(
        cur,
        rule_id="VN05_DO_DAI_SEG_BANG",
        pattern=re.compile(
            rf"(?:độ\s+dài\s+(?:đoạn\s+(?:thẳng\s+)?)?|cạnh\s+)([A-Z0-9']{{2,4}})\s+(?:có\s+độ\s+dài\s+)?bằng\s+({_QTY_CHAR})",
            re.IGNORECASE | re.UNICODE,
        ),
        repl=r"\1=\2",
        steps=steps,
        skip_if_cond_or_neg=True,
    )
    cur = _apply_safe_sub(
        cur,
        rule_id="VN05_CHIEU_CAO_PRISM",
        pattern=re.compile(r",\s*chiều\s+cao\s+([A-Z0-9']+=[^\s,.;]+)", re.IGNORECASE | re.UNICODE),
        repl=r", \1",
        steps=steps,
    )
    cur = _apply_safe_sub(
        cur,
        rule_id="VN05_SEG_BANG",
        pattern=re.compile(
            rf"(?<![A-Za-zÀ-Ỹà-ỹ0-9'/])([A-Z][0-9']*'?[A-Z][0-9']*'?)(?!/)\s+(?:có\s+độ\s+dài\s+)?bằng\s+(?!\d+\s*°)({_QTY_CHAR})",
            re.UNICODE,
        ),
        repl=r"\1=\2",
        steps=steps,
        skip_if_cond_or_neg=True,
    )
    cur = _apply_safe_sub(
        cur,
        rule_id="VN05_YEU_CAU_GOAL",
        pattern=re.compile(r"Yêu\s+cầu\s+(?:xác\s+định|tính)\b", re.IGNORECASE | re.UNICODE),
        repl="Tính",
        steps=steps,
    )
    cur = _apply_safe_sub(
        cur,
        rule_id="VN05_HAY_TIM_GOAL",
        pattern=re.compile(
            r"\b(?:Hãy\s+(?:xác\s+định|tìm|tính)|Tìm)\s+(?=thể\s+tích|khoảng\s+cách|góc|diện\s+tích|độ\s+dài|tỉ\s+số)",
            re.IGNORECASE | re.UNICODE,
        ),
        repl="Tính ",
        steps=steps,
    )
    cur = _apply_safe_sub(
        cur,
        rule_id="VN05_GOAL_DA_CHO",
        pattern=re.compile(r"thể\s+tích\s+của\s+khối\s+(chóp|lăng\s+trụ|hộp)\s+đã\s+cho", re.IGNORECASE | re.UNICODE),
        repl=r"thể tích khối \1",
        steps=steps,
    )

    return VerifiedNormalizationResult(
        normalizer_version=SLM_VERIFIED_NORMALIZER_VERSION,
        original_text=raw_text or "",
        canonical_text=cur,
        changed=(cur != norm0),
        typo_detected=False,
        ambiguity_flags=(),
        steps=tuple(steps),
    )


__all__ = [
    "SLM_VERIFIED_NORMALIZER_VERSION",
    "VerifiedNormalizationResult",
    "VerifiedNormalizationStep",
    "normalize_for_slm_grounding",
]
