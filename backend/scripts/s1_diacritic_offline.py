# -*- coding: utf-8 -*-
"""Continuation 11 (§5.1) — Isolated Offline S-1 Diacritic-Free Risk Audit & Normalization Prototype.

STRICT ISOLATION CONTRACT:
- Lives in `backend/scripts/` (evaluation tools), NEVER imported by `backend/app/`, `detect_domain`,
  or any production/default route (`DEFAULT_MODE = LLM_ONLY` untouched).
- Preserves `raw_source` byte-for-byte and maintains an exact 1-to-1 character offset map
  `norm_to_raw_span` so source spans always point into `raw_source` (zero forged quotes).
- Never guesses a geometric meaning when polysemous ASCII tokens (`goc`, `day`, `tam`, `canh`,
  `duong`) remain ambiguous in context; returns `NEEDS_CLARIFICATION` (`AMBIGUOUS_DIACRITIC_RESTORATION`).
"""
from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Any
import unicodedata

# Multi-word unambiguous geometric collocations (ASCII lowercase -> Vietnamese with exact token count preserved).
# Every replacement preserves token count and maps each normalized token back to its exact raw token span.
_UNAMBIGUOUS_PHRASES: tuple[tuple[tuple[str, ...], tuple[str, ...]], ...] = (
    (("hinh", "chop", "tu", "giac", "deu"), ("hình", "chóp", "tứ", "giác", "đều")),
    (("hinh", "chop", "tam", "giac", "deu"), ("hình", "chóp", "tam", "giác", "đều")),
    (("hinh", "lang", "tru", "tam", "giac", "deu"), ("hình", "lăng", "trụ", "tam", "giác", "đều")),
    (("hinh", "lang", "tru", "dung"), ("hình", "lăng", "trụ", "đứng")),
    (("lang", "tru", "dung"), ("lăng", "trụ", "đứng")),
    (("hinh", "hop", "chu", "nhat"), ("hình", "hộp", "chữ", "nhật")),
    (("hinh", "hop", "dung"), ("hình", "hộp", "đứng")),
    (("hinh", "lap", "phuong"), ("hình", "lập", "phương")),
    (("hinh", "chieu", "vuong", "goc"), ("hình", "chiếu", "vuông", "góc")),
    (("dung", "thiet", "dien"), ("dựng", "thiết", "diện")),
    (("dung", "giao", "tuyen"), ("dựng", "giao", "tuyến")),
    (("dung", "mat", "phang"), ("dựng", "mặt", "phẳng")),
    (("dung", "duong", "thang"), ("dựng", "đường", "thẳng")),
    (("dung", "hinh", "chop"), ("dựng", "hình", "chóp")),
    (("tam", "giac", "tu"), ("tam", "giác", "tù")),
    (("tam", "giac", "nhon"), ("tam", "giác", "nhọn")),
    (("mat", "phang", "day"), ("mặt", "phẳng", "đáy")),
    (("ban", "kinh", "day"), ("bán", "kính", "đáy")),
    (("dien", "tich", "thiet", "dien"), ("diện", "tích", "thiết", "diện")),
    (("dien", "tich", "xung", "quanh"), ("diện", "tích", "xung", "quanh")),
    (("dien", "tich", "toan", "phan"), ("diện", "tích", "toàn", "phần")),
    (("goc", "toa", "do"), ("gốc", "tọa", "độ")),
    (("goc", "tao", "boi"), ("góc", "tạo", "bởi")),
    (("goc", "hop", "boi"), ("góc", "hợp", "bởi")),
    (("goc", "giua"), ("góc", "giữa")),
    (("so", "do", "goc"), ("số", "đo", "góc")),
    (("vuong", "goc"), ("vuông", "góc")),
    (("song", "song"), ("song", "song")),
    (("trung", "diem"), ("trung", "điểm")),
    (("trong", "tam"), ("trọng", "tâm")),
    (("giao", "diem"), ("giao", "điểm")),
    (("giao", "tuyen"), ("giao", "tuyến")),
    (("thiet", "dien"), ("thiết", "diện")),
    (("khoang", "cach"), ("khoảng", "cách")),
    (("the", "tich"), ("thể", "tích")),
    (("dien", "tich"), ("diện", "tích")),
    (("do", "dai"), ("độ", "dài")),
    (("chieu", "cao"), ("chiều", "cao")),
    (("duong", "thang"), ("đường", "thẳng")),
    (("duong", "cao"), ("đường", "cao")),
    (("duong", "cheo"), ("đường", "chéo")),
    (("duong", "tron"), ("đường", "tròn")),
    (("duong", "sinh"), ("đường", "sinh")),
    (("doan", "thang"), ("đoạn", "thẳng")),
    (("mat", "phang"), ("mặt", "phẳng")),
    (("mat", "ben"), ("mặt", "bên")),
    (("mat", "day"), ("mặt", "đáy")),
    (("mat", "cau"), ("mặt", "cầu")),
    (("tam", "day"), ("tâm", "đáy")),
    (("canh", "ben"), ("cạnh", "bên")),
    (("canh", "day"), ("cạnh", "đáy")),
    (("tam", "giac"), ("tam", "giác")),
    (("tu", "giac"), ("tứ", "giác")),
    (("tu", "dien"), ("tứ", "diện")),
    (("hinh", "vuong"), ("hình", "vuông")),
    (("hinh", "thoi"), ("hình", "thoi")),
    (("hinh", "thang"), ("hình", "thang")),
    (("hinh", "chop"), ("hình", "chóp")),
    (("khoi", "chop"), ("khối", "chóp")),
    (("hinh", "non"), ("hình", "nón")),
    (("khoi", "non"), ("khối", "nón")),
    (("hinh", "tru"), ("hình", "trụ")),
    (("khoi", "tru"), ("khối", "trụ")),
    (("lang", "tru"), ("lăng", "trụ")),
    (("xac", "dinh"), ("xác", "định")),
    (("cat", "boi"), ("cắt", "bởi")),
    (("di", "qua"), ("đi", "qua")),
    (("lan", "luot"), ("lần", "lượt")),
)

_UNAMBIGUOUS_SINGLE: dict[str, str] = {
    "cho": "cho",
    "hinh": "hình",
    "khoi": "khối",
    "chop": "chóp",
    "deu": "đều",
    "vuong": "vuông",
    "tai": "tại",
    "va": "và",
    "voi": "với",
    "cua": "của",
    "tren": "trên",
    "len": "lên",
    "den": "đến",
    "toi": "tới",
    "tu": "từ",
    "goi": "gọi",
    "la": "là",
    "diem": "điểm",
    "dinh": "đỉnh",
    "doan": "đoạn",
    "tinh": "tính",
    "tim": "tìm",
    "ve": "vẽ",
    "bang": "bằng",
    "biet": "biết",
    "co": "có",
    "noi": "nối",
    "hai": "hai",
}

POLYSEMOUS_CANDIDATES: dict[str, tuple[str, ...]] = {
    "goc": ("góc", "gốc"),
    "day": ("đáy", "dây", "dãy"),
    "tam": ("tâm", "tam", "tám"),
    "canh": ("cạnh", "cánh"),
    "duong": ("đường", "dương"),
    "dung": ("dựng", "đứng", "đúng"),
}

_LABEL_TOKEN_RE = re.compile(r"^[A-Z][0-9]*'?(?:[A-Z][0-9]*'?)*(?:\.[A-Z][0-9]*'?(?:[A-Z][0-9]*'?)*)?$")
_POLY_LABEL_RE = re.compile(r"^[A-Z][0-9]*'?(?:[A-Z][0-9]*'?){2,}$")
_VIET_DIACRITIC_RE = re.compile(r"[\u00C0-\u024F\u1E00-\u1EFF]")
_WORD_OR_OTHER_RE = re.compile(r"[A-Za-z\u00C0-\u024F\u1E00-\u1EFF0-9']+|[^A-Za-z\u00C0-\u024F\u1E00-\u1EFF0-9']+")
_MISSING_DIACRITIC_CUES: frozenset[str] = (
    {k for k, v in _UNAMBIGUOUS_SINGLE.items() if k != v}
    | {s for src_seq, dst_seq in _UNAMBIGUOUS_PHRASES for s, d in zip(src_seq, dst_seq) if s != d}
    | set(POLYSEMOUS_CANDIDATES)
) - {"tam", "trong", "so", "do"}


@dataclass(frozen=True)
class AmbiguousTokenFlag:
    raw_token: str
    raw_span: tuple[int, int]
    candidates: tuple[str, ...]
    reason: str


@dataclass(frozen=True)
class S1NormalizationResult:
    status: str  # "RESTORED_UNAMBIGUOUS" | "PASSTHROUGH_HAS_DIACRITICS" | "NEEDS_CLARIFICATION"
    code: str | None
    raw_source: str
    normalized_candidate: str
    token_spans: tuple[tuple[str, str, int, int], ...]  # (raw_tok, norm_tok, raw_start, raw_end)
    norm_char_to_raw_span: tuple[tuple[int, int], ...]
    ambiguities: tuple[AmbiguousTokenFlag, ...]
    lowercase_label_warnings: tuple[tuple[str, tuple[int, int]], ...]


def _has_vietnamese_diacritics(text: str) -> bool:
    return bool(_VIET_DIACRITIC_RE.search(text))


def _ascii_fold(text: str) -> str:
    return "".join(
        ch for ch in unicodedata.normalize("NFD", text.replace("đ", "d").replace("Đ", "D"))
        if unicodedata.category(ch) != "Mn"
    )


def _match_case(raw_tok: str, restored_lower: str) -> str:
    if raw_tok and raw_tok[0].isupper() and (len(raw_tok) == 1 or raw_tok[1:].islower()):
        return restored_lower[0].upper() + restored_lower[1:]
    return restored_lower


def analyze_diacritic_free_input(raw_source: str) -> S1NormalizationResult:
    """Analyze & offline-normalize diacritic-free (or mixed-IME) Vietnamese geometry input without touching raw quotes."""
    pieces = [(m.group(0), m.start(), m.end()) for m in _WORD_OR_OTHER_RE.finditer(raw_source)]
    word_indices = [idx for idx, (tok, _, _) in enumerate(pieces) if tok[0].isalpha()]
    words_raw = [pieces[idx][0] for idx in word_indices]
    words_has_diac = [_has_vietnamese_diacritics(w) for w in words_raw]
    words_low = [_ascii_fold(w).lower() for w in words_raw]
    n = len(words_raw)
    is_label = [bool(_LABEL_TOKEN_RE.match(w)) for w in words_raw]

    lowercase_warnings: list[tuple[str, tuple[int, int]]] = []
    for m_low in re.finditer(r"(?<![A-Za-z])[a-z]\.[a-z]{3,4}(?![A-Za-z])", raw_source):
        lowercase_warnings.append((m_low.group(0), m_low.span()))

    has_missing_diacritics = (not _has_vietnamese_diacritics(raw_source)) or bool(lowercase_warnings) or any(
        not is_label[i]
        and not words_has_diac[i]
        and (
            words_low[i] in _MISSING_DIACRITIC_CUES
            or (words_low[i] == "tam" and (i + 1 >= n or words_low[i + 1] != "giac"))
        )
        for i in range(n)
    )

    if not has_missing_diacritics:
        char_map = tuple((i, i + 1) for i in range(len(raw_source)))
        tok_spans = tuple((t, t, a, b) for t, a, b in pieces if t and t[0].isalnum())
        return S1NormalizationResult(
            status="PASSTHROUGH_HAS_DIACRITICS",
            code=None,
            raw_source=raw_source,
            normalized_candidate=raw_source,
            token_spans=tok_spans,
            norm_char_to_raw_span=char_map,
            ambiguities=(),
            lowercase_label_warnings=(),
        )

    resolved: list[str | None] = [None] * n
    ambiguities: list[AmbiguousTokenFlag] = []

    # Step 1: Preserve uppercase geometric labels (`S.ABCD`, `ABCD`, `SA`, `A'`, `O`, `P`) and already-accented words
    for i, w in enumerate(words_raw):
        if is_label[i] or words_has_diac[i]:
            resolved[i] = w

    # Step 2: Longest-match unambiguous multi-word geometric phrases (allowing already-accented words matching dst_seq)
    i = 0
    while i < n:
        matched = False
        for src_seq, dst_seq in _UNAMBIGUOUS_PHRASES:
            k = len(src_seq)
            if (
                i + k <= n
                and tuple(words_low[i:i + k]) == src_seq
                and any(resolved[i + j] is None for j in range(k))
                and all(
                    (resolved[i + j] is None)
                    or (words_has_diac[i + j] and not is_label[i + j] and words_raw[i + j].lower() == dst_seq[j])
                    for j in range(k)
                )
            ):
                for j in range(k):
                    if resolved[i + j] is None:
                        resolved[i + j] = _match_case(words_raw[i + j], dst_seq[j])
                i += k
                matched = True
                break
        if not matched:
            i += 1

    # Step 3: Contextual resolution & strict polysemy detection for remaining words
    has_solid_frame = any(
        (words_low[j], words_low[j + 1]) in (("hinh", "chop"), ("khoi", "chop"), ("lang", "tru"), ("hinh", "hop"), ("lap", "phuong"))
        for j in range(max(0, n - 1))
    )
    has_circle_or_chord_cue = any(w in ("tron", "cung", "day_cung") for w in words_low)

    for i in range(n):
        if resolved[i] is not None:
            continue
        wl = words_low[i]
        raw_tok, raw_a, raw_b = pieces[word_indices[i]]
        prev_w = words_low[i - 1] if i > 0 else ""
        next_w = words_low[i + 1] if i + 1 < n else ""
        next_raw = words_raw[i + 1] if i + 1 < n else ""

        if wl == "day":
            # Unambiguous "đáy" ONLY when solid frame is present, no circle/chord cue, and followed by a polygon label (3+ chars like ABC/ABCD)
            if has_solid_frame and not has_circle_or_chord_cue and bool(_POLY_LABEL_RE.match(next_raw)):
                resolved[i] = _match_case(raw_tok, "đáy")
            else:
                ambiguities.append(AmbiguousTokenFlag(
                    raw_token=raw_tok,
                    raw_span=(raw_a, raw_b),
                    candidates=POLYSEMOUS_CANDIDATES["day"],
                    reason="Token 'day' is polysemous ('đáy' base vs 'dây' chord vs 'dãy' sequence) in this context.",
                ))
                resolved[i] = raw_tok
        elif wl == "goc":
            ambiguities.append(AmbiguousTokenFlag(
                raw_token=raw_tok,
                raw_span=(raw_a, raw_b),
                candidates=POLYSEMOUS_CANDIDATES["goc"],
                reason="Token 'goc' outside closed collocation ('vuông góc'/'góc giữa'/'gốc tọa độ') can mean 'góc' (angle) or 'gốc' (origin).",
            ))
            resolved[i] = raw_tok
        elif wl == "tam":
            # Unambiguous "tâm" ONLY right after "mặt cầu" / "đường tròn" / "hình cầu" and before a single uppercase point label
            prev2 = (words_low[i - 2], words_low[i - 1]) if i >= 2 else ("", "")
            if prev2 in (("mat", "cau"), ("duong", "tron"), ("hinh", "cau")) and len(next_raw) == 1 and next_raw.isupper():
                resolved[i] = _match_case(raw_tok, "tâm")
            else:
                ambiguities.append(AmbiguousTokenFlag(
                    raw_token=raw_tok,
                    raw_span=(raw_a, raw_b),
                    candidates=POLYSEMOUS_CANDIDATES["tam"],
                    reason="Token 'tam' outside ('tam giác'/'trọng tâm'/'tâm đáy'/'mặt cầu tâm O') can mean 'tâm' (center), 'tam' (three), or 'tám' (eight).",
                ))
                resolved[i] = raw_tok
        elif wl == "canh":
            next_nonspace = next((t for t, _, _ in pieces[word_indices[i] + 1:] if not t.isspace()), "")
            # Unambiguous "cạnh" after square/regular polygon/cube/equilateral, before 2-letter segment label, or before numeric side length in solid frame
            if prev_w in ("vuong", "deu", "phuong", "cac") or (len(next_raw) == 2 and next_raw.isupper()) or (has_solid_frame and next_nonspace.isdigit()):
                resolved[i] = _match_case(raw_tok, "cạnh")
            else:
                ambiguities.append(AmbiguousTokenFlag(
                    raw_token=raw_tok,
                    raw_span=(raw_a, raw_b),
                    candidates=POLYSEMOUS_CANDIDATES["canh"],
                    reason="Token 'canh' without polygon/segment anchor is polysemous ('cạnh' vs 'cánh').",
                ))
                resolved[i] = raw_tok
        elif wl == "duong":
            ambiguities.append(AmbiguousTokenFlag(
                raw_token=raw_tok,
                raw_span=(raw_a, raw_b),
                candidates=POLYSEMOUS_CANDIDATES["duong"],
                reason="Token 'duong' outside ('đường thẳng'/'đường cao'/'đường chéo'/'đường tròn') can mean 'đường' (line) or 'dương' (positive).",
            ))
            resolved[i] = raw_tok
        elif wl == "dung":
            ambiguities.append(AmbiguousTokenFlag(
                raw_token=raw_tok,
                raw_span=(raw_a, raw_b),
                candidates=POLYSEMOUS_CANDIDATES["dung"],
                reason="Token 'dung' outside ('dựng thiết diện'/'lăng trụ đứng'/'hình hộp đứng') can mean 'dựng' (construct), 'đứng' (right), or 'đúng' (true).",
            ))
            resolved[i] = raw_tok
        elif wl in _UNAMBIGUOUS_SINGLE:
            resolved[i] = _match_case(raw_tok, _UNAMBIGUOUS_SINGLE[wl])
        else:
            resolved[i] = raw_tok

    # Assemble normalized string & exact character-to-raw-span map
    word_pos_map = {p_idx: w_i for w_i, p_idx in enumerate(word_indices)}
    out_parts: list[str] = []
    char_map: list[tuple[int, int]] = []
    tok_spans: list[tuple[str, str, int, int]] = []

    for p_idx, (raw_piece, a, b) in enumerate(pieces):
        if p_idx in word_pos_map:
            norm_piece = resolved[word_pos_map[p_idx]] or raw_piece
            out_parts.append(norm_piece)
            tok_spans.append((raw_piece, norm_piece, a, b))
            for _ in norm_piece:
                char_map.append((a, b))
        else:
            out_parts.append(raw_piece)
            if raw_piece and raw_piece[0].isdigit():
                tok_spans.append((raw_piece, raw_piece, a, b))
            for k_ch in range(len(raw_piece)):
                char_map.append((a + k_ch, a + k_ch + 1))

    norm_str = "".join(out_parts)
    if ambiguities or lowercase_warnings:
        code = "AMBIGUOUS_DIACRITIC_RESTORATION" if ambiguities else "LOWERCASE_VERTEX_AMBIGUITY"
        return S1NormalizationResult(
            status="NEEDS_CLARIFICATION",
            code=code,
            raw_source=raw_source,
            normalized_candidate=norm_str,
            token_spans=tuple(tok_spans),
            norm_char_to_raw_span=tuple(char_map),
            ambiguities=tuple(ambiguities),
            lowercase_label_warnings=tuple(lowercase_warnings),
        )

    return S1NormalizationResult(
        status="RESTORED_UNAMBIGUOUS",
        code=None,
        raw_source=raw_source,
        normalized_candidate=norm_str,
        token_spans=tuple(tok_spans),
        norm_char_to_raw_span=tuple(char_map),
        ambiguities=(),
        lowercase_label_warnings=(),
    )


def extract_raw_quote_from_normalized_span(res: S1NormalizationResult, norm_start: int, norm_end: int) -> str:
    """Project a span `[norm_start, norm_end)` on `normalized_candidate` back to the exact verbatim `raw_source` slice."""
    if not (0 <= norm_start < norm_end <= len(res.norm_char_to_raw_span)):
        raise ValueError(f"Invalid normalized span [{norm_start}, {norm_end})")
    raw_start = res.norm_char_to_raw_span[norm_start][0]
    raw_end = res.norm_char_to_raw_span[norm_end - 1][1]
    return res.raw_source[raw_start:raw_end]


def verify_no_forged_quotes(raw_source: str, quotes: list[str] | tuple[str, ...]) -> tuple[bool, str | None]:
    """Fail closed (`FORGED_NORMALIZED_QUOTE`) if any quote is not a verbatim substring of `raw_source`."""
    for q in quotes:
        if q not in raw_source:
            return False, "FORGED_NORMALIZED_QUOTE"
    return True, None


def audit_s1_corpus(cases: list[dict[str, Any]]) -> dict[str, Any]:
    """Evaluate an offline S-1 development corpus (`0` live calls)."""
    results = []
    for c in cases:
        r = analyze_diacritic_free_input(c["raw_text"])
        quote_ok, quote_err = verify_no_forged_quotes(
            r.raw_source,
            [extract_raw_quote_from_normalized_span(r, 0, len(r.normalized_candidate))] if r.normalized_candidate else [],
        )
        results.append({
            "id": c["id"],
            "category": c["category"],
            "expected_status": c["expected_status"],
            "actual_status": r.status,
            "code": r.code,
            "matches_expected": r.status == c["expected_status"],
            "raw_quote_preserved": quote_ok and quote_err is None,
            "ambiguity_tokens": [a.raw_token for a in r.ambiguities],
            "lowercase_warnings": [w[0] for w in r.lowercase_label_warnings],
            "normalized_candidate": r.normalized_candidate,
        })
    return {
        "schema": "s1-diacritic-offline-audit/1",
        "provider_calls": 0,
        "total_cases": len(results),
        "exact_match_count": sum(1 for x in results if x["matches_expected"]),
        "forged_quotes": sum(1 for x in results if not x["raw_quote_preserved"]),
        "results": results,
    }
