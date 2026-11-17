# -*- coding: utf-8 -*-
"""Đối chiếu OCR theo bố cục (layout-aware) giữa nhiều bộ đọc local, KHÔNG dùng ground truth.

Đầu vào: kết quả thô `local-ocr-raw/1` (mỗi engine: dòng + từ + hộp bao + độ tin cậy thô) và,
tuỳ chọn, các lượt đọc lại (adjudication) trên vùng tranh chấp. Đầu ra: bản đề nháp kèm từng
khoảng (span) có vị trí ký tự, hộp bao nguồn trên ảnh, trạng thái `verified` / `uncertain`,
phương án thay thế và lý do. Nguyên tắc:

1. Hai bộ đọc cùng ra một chuỗi KHÔNG tự động là đúng: chuỗi khớp mẫu hỏng chung (`aV7`,
   `S,ABCD`, `600°`…) vẫn bị đánh dấu chưa chắc chắn.
2. Token toán (nhãn đỉnh, số, ký hiệu, quan hệ) chỉ `verified` khi ≥ 2 bộ đọc KHÁC NHAU cho ra
   đúng cùng chuỗi chuẩn hoá. Không có phép chọn "ký hiệu hợp lý hơn" nhờ Parser.
3. Từ tiếng Việt (văn xuôi) được khôi phục dấu từ hai nguồn bổ sung nhau — Tesseract giữ dấu,
   RapidOCR giữ phụ âm/ký tự Latin — đối chiếu bằng khung phụ âm và từ vựng sinh từ ngữ pháp
   Parser (`ocr_lexicon.py`). Không khôi phục được duy nhất ⇒ `uncertain`.
4. Bố cục 2 chiều bị nghi mất (phân số tầng, dòng chữ nhỏ chồng lên dòng chính) ⇒ `uncertain`
   loại cấu trúc; không tự ghép tử/mẫu.
5. Chữ nằm trong vùng hình vẽ được tách riêng thành token hình; hình có số đo/ký hiệu riêng hoặc
   đề nói "như hình vẽ" ⇒ dữ kiện hình CHƯA xác minh.
"""
from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass, field
from typing import Any, Iterable

from app.ingestion.ocr_lexicon import LEXICON_BIGRAMS, LEXICON_COUNTS, LEXICON_UNIGRAMS

OCR_RECONCILE_VERSION = "layout-aware-ocr-reconcile/3"
_SYLLABLE_RE = re.compile(r"(?:ngh|ng|gh|gi|kh|nh|ph|qu|th|tr|ch|b|c|d|g|h|k|l|m|n|p|r|s|t|v|x)?[aeiouy]{1,3}(?:ch|ng|nh|c|m|n|p|t)?")

# Mẫu hỏng chung đã ghi nhận trên ảnh thật (dual_ocr_fidelity_receipt của run trước) — áp lên
# token ĐÃ đồng thuận để đồng thuận sai không lọt.
_SHARED_CORRUPTION_RE = re.compile(
    r"(?:[0-9a-z][Vv]\d|=\s*[Vv]\d|^[Vv]\d"  # √ đọc thành V
    r"|^[A-Z],[A-Z]{3,6}$|^[A-Z]{3,6}-[A-Z]{3,6}$"  # S,ABCD · ABC-ABC
    r"|\([0-9][A-Z]{2,}\)|\.[0-9][A-Z]{2,}|[A-Z][0-9][A-Z]{2,}"  # (4BC) · S.4BC · S.A8CD (giữ nguyên 2BC, A1B1C1)
    r"|(?:[2-9]\d{2}|1[89]\d|\d{4,})[°º]"  # >= 180°, vd 600° / 600º (° đọc thành 0); góc tù 100°..179° hợp lệ
    r"|(?<![^\W\d_])[a-z][23”\"](?![^\W_])"  # a2 · a3 · 2a2 · 27√13a3/2 · a” (mất số mũ trên)
    r"|[€#!§¢£¥©®™«»„“”Œ]"  # ký tự rác
    r"|\.\.\.)"
)
_MATH_CHAR_RE = re.compile(r"[0-9√°⊥∥∠△'′=+<>^/\[\]π²³]")
_LABELISH_RE = re.compile(r"^[A-Z][A-Z0-9'′.;,]*$")
_VAR_RE = re.compile(r"^[abchxyzkr][.,;:]?$")
_DIAGRAM_LABEL_LINE_RE = re.compile(r"^(?:[A-Z][0-9]?['′]{0,2}\s*){1,3}$")
_CHOICE_START_RE = re.compile(r"^\s*[AB]\s*[.):](?:\s|\S|$)")
_OPTION_MARKER_TOKEN_RE = re.compile(r"^\s*\(?([A-D])\s*[.,):]?$")
_OPTION_PREFIX_RE = re.compile(r"^\s*\(?[A-D]\s*[.,):]\s*(?:\S|$)")
_HEADER_RE = re.compile(r"^\s*(?:Câu|Cau|Bài|Bai|Cu)\s*\d", re.IGNORECASE)
_DIAGRAM_DEPENDENCY_RE = re.compile(
    r"(?:hình\s+vẽ\s+bên|như\s+hình\s+(?:vẽ|bên)|trong\s+hình\s+vẽ|ở\s+hình\s+bên|hình\s+bên"
    r"|tham\s+khảo\s+hình|xem\s+hình|ghi\s+trên\s+hình|như\s+hình)",
    re.IGNORECASE,
)
_PUNCT_EDGE = ".,;:!?"
READER_FAMILY = {
    "rapidocr": "paddle",
    "rapidocr_latin_rec": "paddle",
    "tesseract": "tesseract",
    "tesseract_eng_line": "tesseract",
    "tesseract_vie_line": "tesseract",
}


def strip_marks(s: str) -> str:
    s = unicodedata.normalize("NFD", (s or "").replace("đ", "d").replace("Đ", "D"))
    return unicodedata.normalize("NFC", "".join(c for c in s if not unicodedata.combining(c)))


def skeleton(word: str) -> str:
    base = strip_marks(word.lower())
    return "".join(c for c in base if c.isalpha() and c not in "aeiouy")


def _base_letters(word: str) -> str:
    return "".join(c for c in strip_marks(word.lower()) if c.isalpha())


def _format_unit_superscripts(tok: str) -> str:
    """Chuẩn hoá hiển thị chỉ số trên cho đơn vị diện tích/thể tích (`cm2` -> `cm²`, `m3` -> `m³`) và `º`->`°`, không đụng đại số (`a2`)."""
    t = re.sub(r"(?<![^\W\d_])([cdkm]?m)2(?![0-9])", r"\1²", tok)
    t = re.sub(r"(?<![^\W\d_])([cdkm]?m)3(?![0-9])", r"\1³", t)
    return re.sub(r"(?<=\d)º", "°", t)


def norm_math(tok: str) -> str:
    t = unicodedata.normalize("NFC", tok or "")
    for a in ("′", "’", "‘", "`", "´", "ʼ"):
        t = t.replace(a, "'")
    t = t.replace("º", "°").replace("˚", "°").replace("∘", "°")
    t = re.sub(r"(?<=[A-Z0-9'′])\s*·\s*(?=[A-Z])", ".", t)
    t = re.sub(r"\s+", "", t)
    # Đơn vị diện tích/thể tích: chỉ số trên bị đọc thành chữ số thường (cm2 ↔ cm², mm2 ↔ mm²) — chuẩn hoá về dạng chỉ số trên.
    t = _format_unit_superscripts(t)
    return t.strip(_PUNCT_EDGE)


def is_mathlike(tok: str) -> bool:
    t = (tok or "").strip()
    if not t:
        return False
    core = t.strip(_PUNCT_EDGE + "()")
    if not core:
        return False
    if _MATH_CHAR_RE.search(core):
        return True
    if _VAR_RE.match(t.strip("()")):
        return True
    if _LABELISH_RE.match(core):
        return True
    # "mp(SAC)", "(SBD)": phần trong ngoặc là nhãn
    if re.search(r"\([A-Z][A-Z0-9'′]*\)", t):
        return True
    return False


def _is_prose_word(tok: str) -> bool:
    raw_core = (tok or "").strip(_PUNCT_EDGE + "()")
    core = raw_core.lower()
    return (
        bool(core)
        and bool(re.fullmatch(r"[a-zà-ỹđ]+", core))
        and bool(re.search(r"[a-zà-ỹđ]", raw_core))  # có chữ thường: "AB", "SA" là nhãn, không phải văn xuôi
        and not _VAR_RE.match(core)
    )


def has_shared_corruption(tok: str) -> bool:
    return bool(_SHARED_CORRUPTION_RE.search(norm_math(tok)))


@dataclass
class Word:
    text: str
    bbox: tuple[int, int, int, int]
    conf: float | None
    reader: str


@dataclass
class Span:
    span_id: str
    text: str
    status: str  # verified | uncertain
    kind: str  # prose | math | structure | noise
    bbox: tuple[int, int, int, int] | None
    reason: str | None = None
    alternatives: list[str] = field(default_factory=list)
    readings: dict[str, str] = field(default_factory=dict)
    evidence: str = ""
    start: int = -1
    end: int = -1
    line_id: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "span_id": self.span_id,
            "text": self.text,
            "status": self.status,
            "kind": self.kind,
            "bbox": list(self.bbox) if self.bbox else None,
            "reason": self.reason,
            "alternatives": list(self.alternatives),
            "readings": dict(self.readings),
            "evidence": self.evidence,
            "start": self.start,
            "end": self.end,
            "line_id": self.line_id,
        }


def _union(boxes: Iterable[tuple[int, int, int, int]]) -> tuple[int, int, int, int] | None:
    bs = [b for b in boxes if b]
    if not bs:
        return None
    return (min(b[0] for b in bs), min(b[1] for b in bs), max(b[2] for b in bs), max(b[3] for b in bs))


def _xoverlap(a, b) -> float:
    inter = max(0, min(a[2], b[2]) - max(a[0], b[0]))
    return inter / float(max(1, min(a[2] - a[0], b[2] - b[0])))


def _yoverlap(a, b) -> float:
    inter = max(0, min(a[3], b[3]) - max(a[1], b[1]))
    return inter / float(max(1, min(a[3] - a[1], b[3] - b[1])))


def _center_in(box, region, pad: int = 2) -> bool:
    cx, cy = (box[0] + box[2]) / 2.0, (box[1] + box[3]) / 2.0
    return region[0] - pad <= cx <= region[2] + pad and region[1] - pad <= cy <= region[3] + pad


def _line_words(line: dict[str, Any], reader: str) -> list[Word]:
    ws = line.get("words") or []
    if ws:
        return [Word(str(w["text"]), tuple(int(v) for v in w["bbox"]), w.get("conf"), reader) for w in ws if str(w.get("text", "")).strip()]
    # Không có hộp từng từ: chia đều hộp dòng theo số ký tự (đánh dấu nguồn ước lượng).
    toks = str(line.get("text", "")).split()
    if not toks:
        return []
    x0, y0, x1, y1 = (int(v) for v in line["bbox"])
    total = sum(len(t) + 1 for t in toks)
    out, cur = [], float(x0)
    for t in toks:
        w = (x1 - x0) * (len(t) + 1) / float(total)
        out.append(Word(t, (int(cur), y0, int(cur + w), y1), line.get("conf"), reader))
        cur += w
    return out


def _split_pair(w: Word, left_part: str, right_part: str) -> list[Word]:
    x0, y0, x1, y1 = w.bbox
    total = max(1, len(left_part) + len(right_part))
    split_x = x0 + max(1, min(x1 - x0 - 1, int(round((x1 - x0) * len(left_part) / float(total)))))
    return [
        Word(left_part, (x0, y0, split_x, y1), w.conf, w.reader),
        Word(right_part, (split_x, y0, x1, y1), w.conf, w.reader),
    ]


_LEXICON_SKELETONS: frozenset[str] = frozenset(
    sk for w in LEXICON_UNIGRAMS if (sk := skeleton(w)) and len(sk) >= 2
)


def _split_glued_words(words: list[Word]) -> list[Word]:
    """Tách từ dính trước bước đối chiếu (`phẳng(ABCD)`, `ABCD.A'B'C'D'có`, `B,SA`, `AA'=`, `⊥(ABCD)`), giữ nguyên `S,ABCD` và `S.A8CD`."""
    out: list[Word] = []
    for w in words:
        t = w.text
        # 1. prose+(MATH) hoặc khung phụ âm dính (MATH) (`phẳng(ABCD)`, `phng(A'BC)`).
        m_pm = re.fullmatch(r"([a-zà-ỹđ]{2,})(\([A-Z][A-Z0-9'′]{1,6}\)[.,;:!?]*)", t)
        if m_pm:
            prose_part, math_part = m_pm.group(1), m_pm.group(2)
            base_p = strip_marks(prose_part).lower()
            if prose_part.lower() in LEXICON_UNIGRAMS or _SYLLABLE_RE.fullmatch(base_p) or base_p in _LEXICON_SKELETONS:
                out.extend(_split_pair(w, prose_part, math_part))
                continue
        # 2. Nhãn khối/mặt dính từ văn xuôi (`ABCD.A'B'C'D'có`, `CA'và`).
        m_mp = re.fullmatch(r"(\(?[A-Z][A-Z0-9'′.]{1,15}\)?)(?<!\.)([a-zà-ỹđ]{2,}[.,;:!?]*)", t)
        if m_mp:
            math_part, prose_part = m_mp.group(1), m_mp.group(2)
            p_core = prose_part.rstrip(_PUNCT_EDGE).lower()
            base_p = strip_marks(p_core)
            has_geom_struct = (
                "." in math_part
                or "'" in math_part
                or "′" in math_part
                or len(re.findall(r"[A-Z]", math_part)) >= 2
            )
            if has_geom_struct and not re.search(r"\d", math_part) and (
                p_core in LEXICON_UNIGRAMS or _SYLLABLE_RE.fullmatch(base_p)
            ):
                out.extend(_split_pair(w, math_part, prose_part))
                continue
        # 3. `⊥(ABCD)` / `∥(ABCD)` bị dính.
        m_rel = re.fullmatch(r"([⊥∥])(\(?[A-Z][A-Z0-9'′]{1,7}\)?[.,;:!?]*)", t)
        if m_rel:
            out.extend(_split_pair(w, m_rel.group(1), m_rel.group(2)))
            continue
        # 4. `AA'=` / `54=` — chỉ tách khi bên phải là `=` (nằm trên token nguồn, không chạm reread reading).
        m_eq = re.fullmatch(r"([A-Z0-9'′]{2,})(=.*)", t)
        if m_eq:
            out.extend(_split_pair(w, m_eq.group(1), m_eq.group(2)))
            continue
        # 5. `BC(` dính dấu ngoặc chú thích cuối.
        m_lp = re.fullmatch(r"([A-Z][A-Z0-9'′]{1,5})(\()", t)
        if m_lp:
            out.extend(_split_pair(w, m_lp.group(1), m_lp.group(2)))
            continue
        # 6. `a,BC`, `2a,SA`, `B,SA` — bảo toàn tuyệt đối `S,ABCD` / `S,ABC` (>= 3 chữ cái sau `,`).
        if not re.fullmatch(r"[A-Z],[A-Z]{3,6}[.,;:!?]*", t) and not re.fullmatch(r"\d+,\d+[.,;:!?]*", t):
            m_cm = re.fullmatch(
                r"((?:\d*[a-z](?:[²³]|√\d+)?|[A-Z][A-Z0-9'′]{1,6})),(\(?[A-Z][A-Z0-9'′]{1,6}\)?(?:/[A-Z0-9'′]+)?[.,;:!?]*)",
                t,
            )
            if m_cm:
                out.extend(_split_pair(w, m_cm.group(1) + ",", m_cm.group(2)))
                continue
            m_pt_seg = re.fullmatch(r"([A-Z][0-9]?['′]?),([A-Z][0-9]?['′]?[A-Z][0-9]?['′]?[.,;:!?]*)", t)
            if m_pt_seg:
                out.extend(_split_pair(w, m_pt_seg.group(1) + ",", m_pt_seg.group(2)))
                continue
        out.append(w)
    return out


def _merge_math_fragments(words: list[Word]) -> list[Word]:
    """Gộp các mảnh token toán bị bộ phát hiện tách bởi khoảng trắng giả (`ABC.A' B'C'`, `S.A BC.`, `ABCD· A'B'C'D'`)."""
    out: list[Word] = []
    for w in words:
        if out:
            p = out[-1]
            h = max(1, min(p.bbox[3] - p.bbox[1], w.bbox[3] - w.bbox[1]))
            gap = w.bbox[0] - p.bbox[2]
            cdot_cont = p.text.endswith("·") and bool(re.match(r"^[A-Z]['′A-Z0-9]*", w.text)) and gap < 0.65 * h
            if cdot_cont:
                out[-1] = Word(p.text[:-1] + "." + w.text, _union([p.bbox, w.bbox]), p.conf, p.reader)
                continue
            prime_cont = bool(re.search(r"['′]$", p.text)) and bool(re.match(r"^[A-Z]['′]", w.text))
            tight_caps = (
                gap < 0.35 * h
                and (
                    bool(re.search(r"[A-Z0-9'′]$", p.text))
                    or (bool(re.search(r"[A-Z'′]\.$", p.text)) and len(re.findall(r"[A-Z]", w.text)) >= 2)
                )
                and bool(re.match(r"^[A-Z0-9'′(]", w.text))
                and not _is_prose_word(p.text) and not _is_prose_word(w.text)
            )
            if prime_cont or tight_caps:
                out[-1] = Word(p.text + w.text, _union([p.bbox, w.bbox]), p.conf, p.reader)
                continue
        out.append(w)
    return out


def _slot_text(slot: dict[str, list[Word]]) -> str:
    """Bản đọc chính của một ô (RapidOCR, nếu không có thì Tesseract)."""
    return " ".join(w.text for w in sorted(slot["R"] or slot["T"], key=lambda w: w.bbox[0]))


def _trim_neighbour_bleed(reading: str, prev_text: str, next_text: str) -> str:
    """Ảnh cắt có đệm để đọc lại một ô có thể dính glyph của ô kề (`SA` đọc thành `SA =` khi `=` đứng sát).

    Chỉ bỏ một từ đầu/cuối TÁCH BẰNG KHOẢNG TRẮNG và trùng đúng bản đọc chính của ô kề phía đó; nếu không, giữ nguyên.
    Một token dính liền (`SA=`) không phải bằng chứng glyph hàng xóm nên không bị cắt.
    """
    parts = reading.split()
    if len(parts) >= 2 and next_text and norm_math(parts[-1]) == norm_math(next_text) and parts[-1].strip():
        parts.pop()
    if len(parts) >= 2 and prev_text and norm_math(parts[0]) == norm_math(prev_text) and parts[0].strip():
        parts.pop(0)
    return " ".join(parts)


_VI_VALID_CHARS = frozenset(
    "abcdefghijklmnopqrstuvwxyz"
    "àáảãạăắằẳẵặâấầẩẫậèéẻẽẹêếềểễệìíỉĩịòóỏõọôốồổỗộơớờởỡợùúủũụưứừửữựỳýỷỹỵđ"
)
_LEXICON_ASCII_BASES: frozenset[str] = frozenset(strip_marks(w.lower()) for w in LEXICON_UNIGRAMS)


def _compatible_horn_or_junk(r_core: str, t_core: str) -> bool:
    """Chấp nhận `t_core` (có trong từ vựng từ Tesseract `vie`) khi `r_core` mất/biến dạng nét móc (`tir`←`từ`, `lλn`←`lần`) nhưng khớp âm đầu & vần."""
    if not r_core or not t_core or t_core not in LEXICON_UNIGRAMS or len(t_core) < 2:
        return False
    r_b = strip_marks(r_core.lower())
    t_b = strip_marks(t_core.lower())
    if not r_b or not t_b or r_b[0] != t_b[0]:
        return False
    has_junk = any(ch not in _VI_VALID_CHARS for ch in r_core.lower())
    if has_junk:
        r_clean_sk = "".join(c for c in r_b if c in "bcdfghjklmnpqrstvwxz")
        t_clean_sk = "".join(c for c in t_b if c in "bcdfghjklmnpqrstvwxz")
        return r_clean_sk == t_clean_sk
    # Trường hợp móc của `ư`/`ơ` bị RapidOCR đọc nhầm thành `r` ở cuối (`tir` vs `từ`) khi `r_core` không phải một chữ có nghĩa khác.
    if (
        r_core.isascii()
        and r_b not in _LEXICON_ASCII_BASES
        and any(ch in t_core.lower() for ch in "ưứừửữựơớờởỡợ")
        and r_b.endswith("r")
        and t_b[-1] in "uo"
        and abs(len(r_b) - len(t_b)) <= 1
        and re.sub(r"[^bcdfghjklmnpqrstvwxz]", "", r_b[:-1]) == re.sub(r"[^bcdfghjklmnpqrstvwxz]", "", t_b)
    ):
        return True
    return False


def _restore_prose(r_txt: str, t_txt: str, prev_word: str, next_word: str) -> tuple[str | None, str]:
    """Khôi phục một từ văn xuôi từ R (giữ phụ âm/chữ Latin) + T (giữ dấu). Trả (từ, bằng_chứng) hoặc (None, lý do)."""
    r_core = r_txt.lower().strip(_PUNCT_EDGE + "()")
    t_core = t_txt.lower().strip(_PUNCT_EDGE + "()")
    if not r_core and not t_core:
        return None, "EMPTY"
    sk_r = skeleton(r_core) if r_core else None
    sk_t = skeleton(t_core) if t_core else None
    sk = sk_r if sk_r is not None else sk_t
    cands = [w for w in LEXICON_UNIGRAMS if skeleton(w) == sk] if sk is not None else []
    if r_core:
        r_letters = _base_letters(r_core)
        cands = [w for w in cands if _is_subsequence(r_letters, _base_letters(w))]
    if t_core:
        narrowed = [w for w in cands if _base_letters(w) == _base_letters(t_core)]
        if narrowed:
            cands = narrowed
    t_ok = bool(t_core) and t_core in LEXICON_UNIGRAMS and (
        not r_core or sk_r == sk_t or _is_subsequence(_base_letters(r_core), _base_letters(t_core))
    )
    r_ok = bool(r_core) and r_core in LEXICON_UNIGRAMS and (
        not t_core or sk_t == sk_r or _is_subsequence(_base_letters(t_core), _base_letters(r_core))
    )
    pool = set(cands) | ({t_core} if t_ok else set()) | ({r_core} if r_ok else set())
    ctx = sorted(w for w in pool if f"{prev_word} {w}" in LEXICON_BIGRAMS or f"{w} {next_word}" in LEXICON_BIGRAMS)
    if len(ctx) == 1 and len(pool) > 1:
        return ctx[0], "LEXICON_BIGRAM_CONTEXT"
    if t_ok:
        return t_core, "TESS_LEXICON_SKELETON_MATCH" if r_core else "TESS_LEXICON_SINGLE_READER"
    if r_ok:
        return r_core, "RAPID_LEXICON_COMPATIBLE" if t_core else "RAPID_LEXICON_SINGLE_READER"
    if _compatible_horn_or_junk(r_core, t_core):
        return t_core, "TESS_LEXICON_ONSET_CODA_MATCH"
    if len(cands) == 1:
        return cands[0], "LEXICON_UNIQUE_SKELETON"
    if len(cands) > 1:
        ranked = sorted(cands, key=lambda w: -LEXICON_COUNTS.get(w, 0))
        top, second = LEXICON_COUNTS.get(ranked[0], 0), LEXICON_COUNTS.get(ranked[1], 0)
        if top > 0 and top >= 3 * max(1, second):
            return ranked[0], "LEXICON_FREQUENCY_PRIOR"
        return None, "AMBIGUOUS_DIACRITIC_RESTORATION"
    # Ngoài từ vựng ngữ pháp: T là âm tiết tiếng Việt hợp lệ và khớp khung phụ âm của R.
    if t_core and r_core and sk_t == sk_r and _SYLLABLE_RE.fullmatch(_base_letters(t_core)) and _is_subsequence(_base_letters(r_core), _base_letters(t_core)):
        return t_core, "TESS_SYLLABLE_SKELETON_MATCH"
    return None, "NOT_IN_LEXICON"


def _is_subsequence(small: str, big: str) -> bool:
    it = iter(big)
    return all(c in it for c in small)


def _classify_math_disagreement(values: list[str]) -> str:
    joined = " ".join(values)
    if any("°" in v for v in values) and not all("°" in v for v in values):
        return "DEGREE_SYMBOL_DISAGREEMENT"
    if any("√" in v for v in values) and not all("√" in v for v in values):
        return "RADICAL_DISAGREEMENT"
    if any(re.search(r"[²³^]", v) for v in values) and len({(v.count("²"), v.count("³"), v.count("^")) for v in values}) > 1:
        return "EXPONENT_SUPERSCRIPT_DISAGREEMENT"
    if any("'" in v for v in values) and len({v.count("'") for v in values}) > 1:
        return "PRIME_DISAGREEMENT"
    if re.search(r"[⊥∥]", joined):
        return "RELATION_SYMBOL_DISAGREEMENT"
    if all(re.fullmatch(r"[0-9.,]+", v) for v in values if v):
        return "DIGIT_DISAGREEMENT"
    return "MATH_TOKEN_DISAGREEMENT"


def _join_primes(text: str) -> str:
    t = re.sub(r"(?<=['′])\s+(?=[A-Z]['′])", "", text)
    t = re.sub(r"\(\s*([A-Z0-9'′\s]+?)\s*\)", lambda m: "(" + re.sub(r"\s+", "", m.group(1)) + ")", t)
    return t


def _slot_is_math(r_txt: str, t_txt: str) -> bool:
    src = r_txt or t_txt
    if not src:
        return False
    core = src.strip(_PUNCT_EDGE + "()")
    # R đọc "c"/"k"/"m" (mất nguyên âm có dấu) còn T là từ tiếng Việt có dấu cùng khung phụ âm ⇒ văn xuôi.
    if (
        r_txt and re.fullmatch(r"[a-z]{1,4}", core) and t_txt and _is_prose_word(t_txt)
        and re.search(r"[à-ỹđ]", t_txt.lower()) and skeleton(t_txt) == skeleton(r_txt)
    ):
        return False
    # R chỉ còn vài chữ đầu của một từ có dấu ("M" ← "Một"): chữ R là dãy con của T và T là văn xuôi có dấu.
    if (
        r_txt and re.fullmatch(r"[A-Za-z][a-z]{0,3}", core) and t_txt and _is_prose_word(t_txt)
        and re.search(r"[à-ỹđ]", t_txt.lower()) and len(core) < len(t_txt.strip(_PUNCT_EDGE + "()"))
        and _is_subsequence(_base_letters(core), _base_letters(t_txt)) and _base_letters(core)[:1] == _base_letters(t_txt)[:1]
    ):
        return False
    if _is_prose_word(src):
        return False
    if is_mathlike(src):
        return True
    return bool(t_txt and not _is_prose_word(t_txt) and is_mathlike(t_txt))


def _assign_row_clusters(text_lines: list[dict[str, Any]], med_h: float) -> list[dict[str, Any]]:
    """Nhóm các dòng theo cụm hàng bằng chồng lấn dọc `_yoverlap >= 0.35`, rồi sắp từ trên xuống dưới, trái sang phải."""
    if not text_lines:
        return []
    sorted_lines = sorted(
        text_lines,
        key=lambda l: ((l["bbox"][1] + l["bbox"][3]) / 2.0, l["bbox"][0]),
    )
    clusters: list[dict[str, Any]] = []
    for ln in sorted_lines:
        b = ln["bbox"]
        cy = (b[1] + b[3]) / 2.0
        placed = False
        for cl in clusters:
            cb = cl["box"]
            c_cy = (cb[1] + cb[3]) / 2.0
            y_ov = _yoverlap(cb, b)
            x_ov = _xoverlap(cb, b)
            if y_ov >= 0.35 or (abs(cy - c_cy) <= 0.38 * med_h and x_ov < 0.3):
                cl["lines"].append(ln)
                cl["box"] = _union([cb, b]) or cb
                placed = True
                break
        if not placed:
            clusters.append({"box": b, "lines": [ln]})
    clusters.sort(key=lambda cl: (cl["box"][1] + cl["box"][3]) / 2.0)
    out: list[dict[str, Any]] = []
    for row_idx, cl in enumerate(clusters):
        row_lines = sorted(cl["lines"], key=lambda l: l["bbox"][0])
        for ln in row_lines:
            ln["_row"] = row_idx
            out.append(ln)
    return out


def _math_unicode_richness(val: str) -> int:
    return sum(1 for ch in val if ch in "²³√⊥∥°∠△π")


def _verify_base_plus_glyph_topology(
    best_val: str,
    readings: dict[str, str],
    r_words: list[Word],
    meta: dict[str, Any] | None,
) -> tuple[bool, str | None]:
    """Xác minh tự động có kiểm chứng hình học (`CROSS_FAMILY_BASE_PLUS_GLYPH_TOPOLOGY`):
    CHỈ bật khi có `glyph_topology` thật từ sidecar (không nhòe ⇒ từ chối), RapidOCR word conf ≥ 82,
    và hình học điểm ảnh khớp ký hiệu (`²`, `³`, `√`, `⊥`, `∥`, `=`) hoặc định danh chữ hoa đồng đẳng."""
    if not meta or not isinstance(meta.get("glyph_topology"), dict):
        return False, None
    topo = meta["glyph_topology"]
    if topo.get("blurry", True):
        return False, None
    if not r_words or any(w.conf is None or float(w.conf) < 82.0 for w in r_words):
        return False, None
    rap_main = norm_math(readings.get("rapidocr") or "")
    rap_lat = norm_math(readings.get("rapidocr_latin_rec") or "")
    tess_raw = [v for r, v in readings.items() if READER_FAMILY.get(r) == "tesseract" and (v or "").strip()]
    tess_vals = [norm_math(v) for v in tess_raw if norm_math(v)]

    # Định danh hình học chỉ gồm chữ hoa (`^[A-Z'.()]+$`, >= 2 chữ cái, không chữ số):
    # Cả RapidOCR chính + RapidOCR Latin rec khớp y nguyên VÀ Tesseract chỉ lệch homoglyph serif kinh điển (4↔A, 8↔B, "↔'),
    # giữ nguyên từng dấu nháy trên và dấu chấm khối (`ABCD.A'B'C'D'`, `(ABB'A')`, `ABC`).
    if (
        re.fullmatch(r"[A-Z'.()]+", best_val)
        and len(re.findall(r"[A-Z]", best_val)) >= 2
        and not has_shared_corruption(best_val)
        and rap_main == best_val
        and rap_lat == best_val
        and tess_raw
    ):
        for raw_tv in tess_raw:
            t_canon = norm_math(
                unicodedata.normalize("NFC", raw_tv)
                .replace('"', "'")
                .replace("”", "'")
                .replace("“", "'")
                .replace("4", "A")
                .replace("8", "B")
            )
            if t_canon == best_val:
                return True, "CROSS_FAMILY_UPPER_HOMOGLYPH_PARITY"

    if best_val == "=":
        if not topo.get("has_equals_bars") or rap_main != "=":
            return False, None
        # Nếu một bộ đọc thấy toán tử/ký tự khác incompatible (`<`, `>`, `+`, chữ cái, chữ số) ⇒ giữ review.
        incompatible = any(
            re.search(r"[A-Za-z0-9<>+≠≤≥⊥∥√]", v.strip())
            for v in tess_raw
        )
        if incompatible:
            return False, None
        has_bar_tess = any(
            bool(re.fullmatch(r"(?:=|[—–\-]{1,3}|'{1,2}|:|~_~)", v.strip()))
            for v in tess_raw
        )
        if has_bar_tess or (float(min(w.conf for w in r_words)) >= 88.0 and not tess_raw):
            return True, "CROSS_FAMILY_BASE_PLUS_GLYPH_TOPOLOGY:equals_parallel_bars"
        return False, None

    if not any(ch in best_val for ch in ("²", "³", "√", "⊥", "∥")):
        return False, None
    if ("²" in best_val or "³" in best_val) and not topo.get("has_superscript_cc"):
        return False, None
    if "³" in best_val and topo.get("superscript_digit_hint") == "2":
        return False, None
    if "√" in best_val and not topo.get("has_radical_stroke"):
        return False, None
    if "⊥" in best_val and not topo.get("has_perp_t_junction"):
        return False, None
    if "∥" in best_val and not topo.get("has_parallel_bars"):
        return False, None

    # Không dùng `rapidocr_latin_rec` (vốn thiếu glyph √, ⊥, ∥, ²) để phủ quyết giá trị chuẩn của `rapidocr`.
    if best_val not in (rap_main, rap_lat):
        return False, None
    if not tess_vals:
        return False, None

    if best_val == "⊥":
        if any(tv in ("⊥", "L", "T", "_", "|", "_|_", "l", "1", "/.") for tv in tess_vals):
            return True, "CROSS_FAMILY_BASE_PLUS_GLYPH_TOPOLOGY:perp_t_junction"
        return False, None
    if best_val == "∥":
        if any(tv in ("∥", "//", "||", "|") for tv in tess_vals):
            return True, "CROSS_FAMILY_BASE_PLUS_GLYPH_TOPOLOGY:parallel_bars"
        return False, None

    # Đối chiếu phần chữ/số nền trên các biểu thức chứa ², ³, √.
    best_with_23 = best_val.replace("²", "2").replace("³", "3").replace("√", "")
    best_no_exp = best_val.replace("²", "").replace("³", "").replace("√", "")
    for tv in tess_vals:
        tv_norm = tv.replace("²", "2").replace("³", "3")
        if "√" in best_val:
            tv_norm = re.sub(r"(?:[Vv][\\/]?|√)(?=\d)", "", tv_norm)
        if tv_norm == best_with_23:
            return True, "CROSS_FAMILY_BASE_PLUS_GLYPH_TOPOLOGY:superscript_or_radical_exact_base"
        # Cho phép Tesseract làm rơi hoặc đọc méo duy nhất ký tự chỉ số trên (`a²` -> `a`, `at`, `a'`, `aỶ`, `a?/2`, `4cm”`, `a³` -> `aŠ`/`a®`) khi không xung đột số mũ '2' vs '3'.
        if "²" in best_val or "³" in best_val:
            wrong_digit = "3" if "²" in best_val else "2"
            tv_stripped = re.sub(r"[²³”’'°ŠỶ?^®]", "", tv)
            if best_no_exp and tv_stripped == best_no_exp and not re.search(rf"{wrong_digit}(?:/|$)", tv_norm):
                return True, "CROSS_FAMILY_BASE_PLUS_GLYPH_TOPOLOGY:superscript_cc_and_base"
    # Khi Tesseract đọc mất cả chữ số mũ ở dạng `"a3."` / `"a."` trên `²`/`³`, kiểm thêm `rapidocr_latin_rec` nếu có xác nhận đúng chữ số mũ
    if ("²" in best_val or "³" in best_val) and rap_lat == best_with_23:
        if any(re.sub(r"[²³”’'°ŠỶ?^®]", "", tv) == best_no_exp for tv in tess_vals):
            return True, "CROSS_FAMILY_BASE_PLUS_GLYPH_TOPOLOGY:superscript_base_and_latin_digit"
    return False, None


def _has_prose_words(txt: str) -> bool:
    """Ít nhất 2 từ có chữ thường (`>=2` ký tự) — câu hỏi/đề bài thật, không bao giờ là nhãn đỉnh trên hình."""
    return sum(1 for w in re.findall(r"[A-Za-zÀ-ỹĐđ]{2,}", txt or "") if any(ch.islower() for ch in w)) >= 2


def _detect_choice_bands(lines: list[dict[str, Any]], med_h: float) -> list[tuple[float, float]]:
    """Tìm dải y của phương án trắc nghiệm (A/B/C/D) sau dòng đề mở đầu, gồm cả trường hợp hộp `[A-D].` tách rời."""
    ordered = sorted(lines, key=lambda l: ((l["bbox"][1] + l["bbox"][3]) / 2.0, l["bbox"][0]))
    if not ordered:
        return []
    # Nhóm thô các hộp có cùng y để nhận diện hàng chứa ≥2 nhãn lựa chọn (`A.` + `B.` hoặc `C.` + `D.`).
    rows: list[list[dict[str, Any]]] = []
    for l in ordered:
        cy = (l["bbox"][1] + l["bbox"][3]) / 2.0
        if rows and abs(cy - ((rows[-1][0]["bbox"][1] + rows[-1][0]["bbox"][3]) / 2.0)) <= 0.70 * max(1.0, med_h):
            rows[-1].append(l)
        else:
            rows.append([l])

    def row_is_option(row: list[dict[str, Any]]) -> bool:
        if any(_CHOICE_START_RE.match(str(l.get("text", ""))) for l in row):
            return True
        punct_cd = any(re.match(r"^\s*[CD]\s*[.):](?:\s|\S|$)", str(l.get("text", ""))) for l in row)
        if punct_cd:
            return True
        letters = set()
        for l in row:
            tok = str(l.get("text", "")).strip()
            head = tok.split()[0] if tok.split() else ""
            m = re.match(r"^\s*\(?([A-D])\s*[.,):]", head)
            if m:
                letters.add(m.group(1))
        return len(letters) >= 2

    bands: list[tuple[float, float]] = []
    started: float | None = None
    seen_stem = False
    for row in rows:
        row_y0 = min(l["bbox"][1] for l in row)
        row_txt = " ".join(str(l.get("text", "")).strip() for l in row)
        if _HEADER_RE.match(row_txt):
            if started is not None:
                bands.append((started, row_y0 - 1))
                started = None
            seen_stem = True
            continue
        if started is None and seen_stem and row_is_option(row):
            started = row_y0 - 4
        if _has_prose_words(row_txt):
            seen_stem = True
    if started is not None:
        bands.append((started, float("inf")))
    return bands


def reconcile_local_ocr(
    raw: dict[str, Any],
    *,
    region_bbox: tuple[int, int, int, int] | None = None,
    figure_bboxes: Iterable[tuple[int, int, int, int]] = (),
    adjudications: dict[str, dict[str, str]] | None = None,
    min_agreeing_families: int = 1,
    adjudication_meta: dict[str, dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Đối chiếu RapidOCR (khung dòng/thứ tự đọc) với Tesseract (dấu tiếng Việt) theo hộp bao.

    `adjudications`: `{slot_key: {reader: text}}` — lượt đọc lại vùng tranh chấp bằng bộ nhận dạng
    khác. `min_agreeing_families`: số HỌ engine tối thiểu phải cùng đọc ra token toán (1 = hai bộ đọc
    khác nhau bất kỳ; 2 = phải có cả họ Paddle và họ Tesseract).
    """
    engines = raw.get("engines") or {}
    rap = engines.get("rapidocr") or {}
    tes = engines.get("tesseract") or {}
    img_w, img_h = int(raw.get("width") or 0), int(raw.get("height") or 0)
    figs = [tuple(int(v) for v in b) for b in figure_bboxes]
    if img_w and img_h:
        # Khối "hình" phủ quá nửa ảnh là phân khối nhầm (trang chữ viết tay dày) — không dùng để tách chữ.
        figs = [f for f in figs if (f[2] - f[0]) * (f[3] - f[1]) <= 0.5 * img_w * img_h]
    adjudications = adjudications or {}
    adjudication_meta = adjudication_meta or {}

    def in_region(b) -> bool:
        return region_bbox is None or _center_in(b, region_bbox, pad=6)

    r_lines_all = [ln for ln in rap.get("lines") or [] if ln.get("text", "").strip() and in_region(ln["bbox"])]
    t_words_all = [w for ln in tes.get("lines") or [] for w in _split_glued_words(_line_words(ln, "tesseract")) if in_region(w.bbox)]

    all_h = sorted((ln["bbox"][3] - ln["bbox"][1]) for ln in r_lines_all if ln.get("bbox")) or [20]
    med_h_all = all_h[len(all_h) // 2]
    pre_choice_bands = _detect_choice_bands(r_lines_all, med_h_all)

    def _in_bands(b, txt: str, bands: list[tuple[float, float]], h_ref: float) -> bool:
        cy = (b[1] + b[3]) / 2.0
        pad = 0.70 * h_ref if (txt and (len(norm_math(txt)) <= 12 and is_mathlike(txt) or bool(_OPTION_PREFIX_RE.match(txt)))) else 0.0
        return any(lo - pad <= cy <= hi for lo, hi in bands)

    diagram_tokens: list[dict[str, Any]] = []
    text_lines: list[dict[str, Any]] = []
    kept_in_fig_boxes: list[tuple[int, int, int, int]] = []
    for ln in r_lines_all:
        b = tuple(int(v) for v in ln["bbox"])
        txt = ln["text"].strip()
        in_fig = any(_center_in(b, f) for f in figs)
        is_choice_line = bool(_OPTION_PREFIX_RE.match(txt)) or _in_bands(b, txt, pre_choice_bands, med_h_all)
        is_prose_line = _has_prose_words(txt)
        if not is_choice_line and not is_prose_line and (in_fig or (figs and _DIAGRAM_LABEL_LINE_RE.match(txt))):
            diagram_tokens.append({"text": txt, "bbox": list(b), "reader": "rapidocr", "in_figure_block": in_fig})
            continue
        if in_fig:
            kept_in_fig_boxes.append(b)
        text_lines.append({**ln, "bbox": b})

    heights = sorted(l["bbox"][3] - l["bbox"][1] for l in text_lines) or [20]
    med_h = heights[len(heights) // 2]
    text_lines = _assign_row_clusters(text_lines, med_h)

    # Vùng phương án trắc nghiệm trên các dòng đề đã tách hình (nhất quán với `pre_choice_bands`).
    choice_bands = _detect_choice_bands(text_lines, med_h)

    def in_choice(b, txt: str = "") -> bool:
        return _in_bands(b, txt, choice_bands, med_h)

    assigned: dict[int, list[Word]] = {i: [] for i in range(len(text_lines))}
    t_unassigned: list[Word] = []
    for w in t_words_all:
        word_in_kept_text = any(_yoverlap(w.bbox, kb) >= 0.45 and _xoverlap(w.bbox, kb) >= 0.15 for kb in kept_in_fig_boxes) or in_choice(w.bbox, w.text)
        if any(_center_in(w.bbox, f) for f in figs) and not word_in_kept_text:
            continue
        best, best_ov = None, 0.0
        for i, l in enumerate(text_lines):
            ov = _yoverlap(w.bbox, l["bbox"])
            if ov >= 0.5 and l["bbox"][0] - 12 <= (w.bbox[0] + w.bbox[2]) / 2.0 <= l["bbox"][2] + 12 and ov > best_ov:
                best, best_ov = i, ov
        if best is None:
            t_unassigned.append(w)
        else:
            assigned[best].append(w)

    spans: list[Span] = []
    layout_flags: list[dict[str, Any]] = []
    sid = 0

    stacked: set[int] = set()
    merged_into: dict[int, int] = {}
    fraction_of: dict[int, tuple[str, str, Any]] = {}
    for i, a in enumerate(text_lines):
        ah = a["bbox"][3] - a["bbox"][1]
        for j, b in enumerate(text_lines):
            if j <= i:
                continue
            bh = b["bbox"][3] - b["bbox"][1]
            short_a, short_b = len(norm_math(a["text"])) <= 8, len(norm_math(b["text"])) <= 8
            vertical_stack = (
                _xoverlap(a["bbox"], b["bbox"]) >= 0.5
                and abs(b["bbox"][1] - a["bbox"][3]) <= 0.6 * max(ah, bh)
                and short_a and short_b
                and is_mathlike(a["text"]) and is_mathlike(b["text"])
            )
            small_inside = (
                (ah < 0.75 * med_h or bh < 0.75 * med_h)
                and 0.15 <= _yoverlap(a["bbox"], b["bbox"]) < 0.6
                and abs(((a["bbox"][1] + a["bbox"][3]) - (b["bbox"][1] + b["bbox"][3])) / 2.0) > 0.25 * med_h
                and (short_a or short_b)
            )
            if vertical_stack or small_inside:
                stacked.update((i, j))
                bb = _union([a["bbox"], b["bbox"]])
                if vertical_stack and i not in fraction_of and i not in merged_into and j not in merged_into and j not in fraction_of:
                    top, bot = (i, j) if (a["bbox"][1] + a["bbox"][3]) <= (b["bbox"][1] + b["bbox"][3]) else (j, i)
                    merged_into[bot] = top
                    fraction_of[top] = (text_lines[top]["text"].strip(), text_lines[bot]["text"].strip(), bb)
                layout_flags.append({
                    "flag": "FRACTION_STRUCTURE_SUSPECTED" if vertical_stack else "SUBLINE_OVERLAP_SUSPECTED",
                    "lines": [a["text"], b["text"]],
                    "bbox": list(bb or ()),
                    "in_choice_region": bool(bb and in_choice(bb)),
                    "line_index": [i, j],
                })

    # Dòng phụ chồng lấn chỉ vì là tử/mẫu của một phân số đã gom ⇒ không gắn cờ trùng.
    _frac_lines = set(merged_into) | set(fraction_of)
    layout_flags = [
        f for f in layout_flags
        if not (f["flag"] == "SUBLINE_OVERLAP_SUSPECTED" and set(f["line_index"]) & _frac_lines)
    ]
    stacked = {k for f in layout_flags for k in f["line_index"]}

    line_records: list[dict[str, Any]] = []
    prime_probe_slots: list[dict[str, Any]] = []
    for li, line in enumerate(text_lines):
        line_id = f"L{li + 1}"
        choice_line = in_choice(line["bbox"], line.get("text", ""))
        if li in merged_into:
            continue
        if li in fraction_of:
            top_t, bot_t, fbox = fraction_of[li]
            rbox = tuple(fbox) if fbox else line["bbox"]
            choice_line = in_choice(rbox, f"{top_t}/{bot_t}")
            sid += 1
            frac = f"{norm_math(top_t)}/{norm_math(bot_t)}"
            sp = Span(f"sp{sid}", frac, "uncertain", "choice" if choice_line else "structure", rbox,
                      "FRACTION_STRUCTURE_LOSS", [frac, f"{top_t} {bot_t}"], {"rapidocr": f"{top_t} | {bot_t}"},
                      evidence="layout-fraction", line_id=line_id)
            line_records.append({"line_id": line_id, "bbox": list(rbox), "spans": [sp], "choice": choice_line,
                                 "row": line["_row"]})
            spans.append(sp)
            continue
        r_words = _merge_math_fragments(_split_glued_words(_line_words(line, "rapidocr")))
        t_words = sorted(assigned[li], key=lambda w: w.bbox[0])
        # Gộp âm tiết văn xuôi bị RapidOCR tách đôi (vd: "M" + "t" khi Tesseract đọc "Một") hoặc lặp ký tự đầu ("t" + "trụ").
        merged_r: list[Word] = []
        ki = 0
        while ki < len(r_words):
            rw = r_words[ki]
            if ki + 1 < len(r_words):
                nxt_r = r_words[ki + 1]
                comb_skel = skeleton(rw.text + nxt_r.text)
                if comb_skel and any(
                    _is_prose_word(tw.text)
                    and _xoverlap(rw.bbox, tw.bbox) >= 0.3
                    and _xoverlap(nxt_r.bbox, tw.bbox) >= 0.3
                    and skeleton(tw.text) == comb_skel
                    for tw in t_words
                ):
                    merged_r.append(Word(rw.text + nxt_r.text, _union([rw.bbox, nxt_r.bbox]), min(rw.conf, nxt_r.conf), rw.reader))
                    ki += 2
                    continue
                nxt_core = nxt_r.text.lower().strip(_PUNCT_EDGE)
                if (
                    len(rw.text) == 1
                    and rw.text.islower()
                    and nxt_r.bbox[0] - rw.bbox[2] <= 6
                    and nxt_core in LEXICON_UNIGRAMS
                    and nxt_core.startswith(rw.text.lower())
                    and any(_xoverlap(nxt_r.bbox, tw.bbox) >= 0.5 and tw.text.lower().strip(_PUNCT_EDGE) == nxt_core for tw in t_words)
                ):
                    merged_r.append(Word(nxt_r.text, _union([rw.bbox, nxt_r.bbox]), nxt_r.conf, nxt_r.reader))
                    ki += 2
                    continue
            merged_r.append(rw)
            ki += 1
        r_words = merged_r

        slots_by_r: list[dict[str, list[Word]]] = [{"R": [rw], "T": []} for rw in r_words]
        t_only: list[dict[str, list[Word]]] = []
        for tw in t_words:
            covered = [k for k, rw in enumerate(r_words) if _xoverlap(rw.bbox, tw.bbox) >= 0.35]
            if len(covered) >= 2:
                rem = tw.text.strip()
                while len(covered) >= 2:
                    r0 = norm_math(r_words[covered[0]].text)
                    rm = norm_math(rem)
                    if r0 and rm.startswith(r0) and len(rm) > len(r0):
                        k0 = covered.pop(0)
                        # Cắt đúng số ký tự đầu không tính khoảng trắng tương ứng r0
                        cut, seen = 0, 0
                        while cut < len(rem) and seen < len(r0):
                            if not rem[cut].isspace():
                                seen += 1
                            cut += 1
                        slots_by_r[k0]["T"].append(Word(rem[:cut].strip(), r_words[k0].bbox, tw.conf, tw.reader))
                        rem = rem[cut:].strip()
                    else:
                        break
                while len(covered) >= 2:
                    r1 = norm_math(r_words[covered[-1]].text)
                    rm = norm_math(rem)
                    if r1 and rm.endswith(r1) and len(rm) > len(r1):
                        k1 = covered.pop()
                        cut, seen = len(rem), 0
                        while cut > 0 and seen < len(r1):
                            cut -= 1
                            if not rem[cut].isspace():
                                seen += 1
                        slots_by_r[k1]["T"].append(Word(rem[cut:].strip(), r_words[k1].bbox, tw.conf, tw.reader))
                        rem = rem[:cut].strip()
                    else:
                        break
                if len(covered) == 1 and rem:
                    k_last = covered[0]
                    slots_by_r[k_last]["T"].append(Word(rem, r_words[k_last].bbox, tw.conf, tw.reader))
                continue
            best_k, best_ov, total = None, 0.0, 0.0
            for k, rw in enumerate(r_words):
                inter = max(0, min(rw.bbox[2], tw.bbox[2]) - max(rw.bbox[0], tw.bbox[0]))
                ov = inter / float(max(1, tw.bbox[2] - tw.bbox[0]))
                total += ov
                if ov > best_ov:
                    best_k, best_ov = k, ov
            if best_k is not None and (best_ov >= 0.3 or total >= 0.5):
                slots_by_r[best_k]["T"].append(tw)
            else:
                t_only.append({"R": [], "T": [tw]})
        slots = sorted(slots_by_r + t_only, key=lambda g: min(w.bbox[0] for w in g["R"] + g["T"]))

        line_spans: list[Span] = []
        for si, g in enumerate(slots):
            rs = sorted(g["R"], key=lambda w: w.bbox[0])
            ts = sorted(g["T"], key=lambda w: w.bbox[0])
            r_txt = " ".join(w.text for w in rs)
            t_txt = " ".join(w.text for w in ts)
            box = _union([w.bbox for w in rs]) if rs else _union([w.bbox for w in ts])
            key = f"{line_id}:S{si + 1}"
            sid += 1
            span_id = f"sp{sid}"
            readings: dict[str, str] = {}
            if r_txt:
                readings["rapidocr"] = r_txt
            if t_txt:
                readings["tesseract"] = t_txt
            for reader, val in (adjudications.get(key) or {}).items():
                if val and str(val).strip():
                    readings[reader] = _trim_neighbour_bleed(
                        str(val).strip(),
                        _slot_text(slots[si - 1]) if si > 0 else "",
                        _slot_text(slots[si + 1]) if si + 1 < len(slots) else "",
                    )

            def emit(text, status, kind, reason=None, alts=None, evidence=""):
                line_spans.append(Span(span_id, text, status, kind, box, reason, list(alts or []), readings, evidence or key, line_id=line_id))
                if choice_line:
                    line_spans[-1].kind = "choice" if kind in ("math", "prose") else kind

            # Chỉ dấu câu (một bộ đọc) — không mang dữ kiện.
            if r_txt and not r_txt.strip(_PUNCT_EDGE + " ") and not t_txt.strip(_PUNCT_EDGE + " "):
                emit(r_txt.strip(), "verified", "punct", evidence="PUNCTUATION_ONLY")
                continue

            if not rs and ts:
                alnum = sum(ch.isalnum() for ch in t_txt)
                core = t_txt.lower().strip(_PUNCT_EDGE + "()")
                lexical = core in LEXICON_UNIGRAMS
                if alnum <= 2 or (not is_mathlike(t_txt) and not lexical):
                    line_spans.append(Span(span_id, t_txt, "dropped", "noise", box, "SINGLE_READER_NOISE", readings=readings, line_id=line_id))
                    continue
                if lexical and not is_mathlike(t_txt):
                    emit(core, "verified", "prose", evidence="TESS_LEXICON_SINGLE_READER")
                    continue
                emit(t_txt, "uncertain", "math", "SINGLE_READER_TOKEN", [t_txt])
                continue

            if _slot_is_math(r_txt, t_txt):
                display = _join_primes(r_txt)
                trail = display[len(display.rstrip(_PUNCT_EDGE + " ")):].strip()
                r_norm = norm_math(r_txt)
                r_is_upper_label = bool(r_norm and _LABELISH_RE.match(r_norm))
                votes: dict[str, set[str]] = {}
                for reader, val in readings.items():
                    nv = norm_math(val)
                    if r_is_upper_label and nv.upper() == r_norm:
                        nv = r_norm
                    votes.setdefault(nv, set()).add(reader)
                ranked = sorted(
                    votes.items(),
                    key=lambda kv: (
                        not (
                            len(kv[1]) >= 2
                            and len({READER_FAMILY.get(r, r) for r in kv[1]}) >= min_agreeing_families
                            and not has_shared_corruption(kv[0])
                        ),
                        has_shared_corruption(kv[0]),
                        -_math_unicode_richness(kv[0]),
                        -len({READER_FAMILY.get(r, r) for r in kv[1]}),
                        -len(kv[1]),
                        "rapidocr" not in kv[1],
                    ),
                )
                best_val, best_readers = ranked[0]
                families = {READER_FAMILY.get(r, r) for r in best_readers}
                # Các lượt đọc lại (`rapidocr_latin_rec`, `tesseract_eng_line`, `tesseract_vie_line`) dùng chung một vùng cắt đơn từ;
                # khi bản đọc chính `rapidocr` khác đi (vd `ABCD` vs `ABCE`, `AB` vs `1B`), bắt buộc phải xác nhận thay vì tự tin quá mức.
                primary_agrees = (not r_norm) or ("rapidocr" in best_readers)
                agreed = len(best_readers) >= 2 and len(families) >= min_agreeing_families and primary_agrees
                second_families = {READER_FAMILY.get(r, r) for r in ranked[1][1]} if len(ranked) > 1 else set()
                tie = (
                    len(ranked) > 1
                    and len(ranked[1][1]) == len(best_readers)
                    and len(second_families) >= len(families)
                )
                corrupt = has_shared_corruption(best_val)
                primed_votes = [
                    k for k in votes
                    if "'" in k and k.replace("'", "") == best_val
                ]
                prime_drop_conflict = (
                    min_agreeing_families >= 2
                    and "'" not in best_val
                    and bool(re.fullmatch(r"[A-Z]{2,4}", best_val))
                    and bool(primed_votes)
                )
                topo_ok, topo_ev = (
                    _verify_base_plus_glyph_topology(best_val, readings, rs, adjudication_meta.get(key))
                    if (not agreed and not corrupt and not prime_drop_conflict and best_val)
                    else (False, None)
                )
                if agreed and not tie and not corrupt and not prime_drop_conflict and best_val:
                    disp_fmt = _format_unit_superscripts(display)
                    text_out = disp_fmt if norm_math(display) == best_val else best_val + trail
                    emit(text_out, "verified", "math",
                         evidence="CROSS_READER_AGREEMENT:" + "+".join(sorted(best_readers)) + "|families=" + "+".join(sorted(families)))
                    if (
                        not adjudications
                        and box
                        and "'" not in best_val
                        and bool(re.fullmatch(r"[A-Z]{2,3}", best_val))
                        and ts
                        and min(w.conf for w in ts) < 85.0
                    ):
                        prime_probe_slots.append({"slot_key": key, "bbox": list(box), "readings": dict(readings)})
                elif topo_ok and topo_ev:
                    disp_fmt = _format_unit_superscripts(display)
                    text_out = disp_fmt if norm_math(display) == best_val else best_val + trail
                    emit(text_out, "verified", "math", evidence=topo_ev)
                else:
                    alts = [v for v, _ in ranked if v]
                    if r_norm and r_norm not in alts:
                        alts.append(r_norm)
                    for pv in primed_votes:
                        if pv not in alts:
                            alts.insert(0, pv)
                    if re.fullmatch(r"([A-Z])\1", best_val):
                        prime_alt = f"{best_val}'"
                        if prime_alt not in alts:
                            alts.insert(0, prime_alt)
                    if len(readings) == 1:
                        reason = "SINGLE_READER_MATH_TOKEN"
                    elif agreed and corrupt:
                        reason = "SHARED_CORRUPTION_PATTERN"
                    elif len(best_readers) >= 2 and len(families) < min_agreeing_families:
                        reason = "SAME_FAMILY_AGREEMENT_ONLY"
                    elif prime_drop_conflict:
                        reason = "PRIME_DISAGREEMENT"
                    else:
                        reason = _classify_math_disagreement(list(votes))
                    if r_norm and not has_shared_corruption(r_norm) and (
                        (not primary_agrees and not ("'" in best_val and best_val.replace("'", "") == r_norm))
                        or (r_is_upper_label and best_val.replace("'", "") != r_norm)
                    ):
                        suggestion = _format_unit_superscripts(_join_primes(display))
                        if best_val and best_val not in alts:
                            alts.append(best_val)
                    else:
                        suggestion = _join_primes(display) if norm_math(display) == best_val or not best_val else best_val + trail
                    emit(suggestion, "uncertain", "math", reason, alts[:5])
                continue

            # Văn xuôi.
            r_toks, t_toks = r_txt.split(), t_txt.split()
            r_clean = r_txt.lower().strip(_PUNCT_EDGE)
            t_clean = t_txt.lower().strip(_PUNCT_EDGE)
            if r_txt and t_txt and r_clean == t_clean:
                if r_clean in LEXICON_UNIGRAMS or strip_marks(r_clean) == r_clean:
                    emit(r_txt, "verified", "prose", evidence="EXACT_TWO_READER_AGREEMENT")
                    continue
                same_base = [w for w in LEXICON_UNIGRAMS if _base_letters(w) == _base_letters(r_clean)]
                if not same_base:
                    emit(r_txt, "verified", "prose", evidence="EXACT_TWO_READER_AGREEMENT")
                    continue
            pairs = list(zip(r_toks, t_toks)) if len(r_toks) == len(t_toks) else [(r_txt, t_txt)]
            words_out, unresolved = [], []
            for pi, (rw, tw) in enumerate(pairs):
                prev_w = words_out[-1] if words_out else (line_spans[-1].text.split()[-1] if line_spans and line_spans[-1].text.split() else "")
                nxt = r_toks[pi + 1] if pi + 1 < len(r_toks) else ""
                restored, ev = _restore_prose(rw, tw, prev_w.lower().strip(_PUNCT_EDGE), nxt.lower().strip(_PUNCT_EDGE))
                if restored is None and (len(rw.split()) > 1 or len(tw.split()) > 1):
                    ev = "MULTIWORD_SLOT_MISMATCH"
                src = rw or tw
                trail = src[len(src.rstrip(_PUNCT_EDGE + ")")):]
                lead = src[: len(src) - len(src.lstrip("("))]
                if restored is None:
                    unresolved.append((rw, tw, ev))
                    words_out.append(tw or rw)
                else:
                    cap = src.lstrip("(")[:1].isupper()
                    words_out.append(lead + (restored[:1].upper() + restored[1:] if cap else restored) + trail)
            text_out = " ".join(words_out)
            if unresolved:
                alts = [a for a in dict.fromkeys([tw for _, tw, _ in unresolved] + [rw for rw, _, _ in unresolved]) if a]
                emit(text_out, "uncertain", "prose", unresolved[0][2], alts[:4])
            else:
                emit(text_out, "verified", "prose", evidence="DIACRITIC_RESTORED")

        if li in stacked and li not in fraction_of:
            sid += 1
            line_spans.append(Span(f"sp{sid}", "", "uncertain", "choice" if choice_line else "structure", line["bbox"], "FRACTION_STRUCTURE_LOSS",
                                   [], {"rapidocr": line["text"]}, evidence="layout", line_id=line_id))
        # Bắt lỗi chữ số đọc nhầm từ ký hiệu góc trong ngữ cảnh `4BC = 30°` / `8BC = 60°`.
        for si_chk, sp_chk in enumerate(line_spans):
            m_ang = re.fullmatch(r"([0-9][A-Z]{2})[.,;:]*", sp_chk.text.strip())
            if sp_chk.status == "verified" and m_ang and not choice_line:
                look = [s.text.strip() for s in line_spans[si_chk + 1:si_chk + 4] if s.status != "dropped" and s.text.strip()]
                if (
                    len(look) >= 2
                    and look[0].lower() in ("=", "bằng")
                    and bool(re.match(r"^\d+(?:[.,]\d+)?[°º]", look[1]))
                ):
                    core_tok = m_ang.group(1)
                    sp_chk.status = "uncertain"
                    sp_chk.reason = "SHARED_CORRUPTION_PATTERN"
                    sp_chk.alternatives = [f"∠{core_tok[1:]}", f"∠A{core_tok[1:]}", sp_chk.text] + [
                        a for a in sp_chk.alternatives if a not in (sp_chk.text, f"∠{core_tok[1:]}", f"∠A{core_tok[1:]}")
                    ]
        line_records.append({"line_id": line_id, "bbox": list(line["bbox"]), "spans": line_spans, "choice": choice_line,
                             "row": line["_row"]})
        spans.extend(line_spans)
    # Gom mọi mảnh phương án trắc nghiệm trong cùng dải `choice_band` về hàng của phương án mở đầu ("A."/"B.").
    for lo, hi in choice_bands:
        band_recs = [
            r for r in line_records
            if r["choice"] and lo - 0.70 * med_h <= (r["bbox"][1] + r["bbox"][3]) / 2.0 <= hi
        ]
        if band_recs:
            anchor = [r for r in band_recs if r["spans"] and _CHOICE_START_RE.match(r["spans"][0].text)]
            target_row = (anchor[0] if anchor else band_recs[0])["row"]
            for r in band_recs:
                r["row"] = target_row
    line_records.sort(key=lambda r: (r["row"], r["bbox"][0]))

    extra_unknown = [
        w for w in t_unassigned
        if not any(_center_in(w.bbox, f) for f in figs)
        and (is_mathlike(w.text) and sum(ch.isalnum() for ch in w.text) >= 2
             or w.text.lower().strip(_PUNCT_EDGE) in LEXICON_UNIGRAMS)
    ]

    # Lắp bản nháp: các dòng cùng dải hàng ghép trên một dòng văn bản.
    out_lines: list[str] = []
    pos = 0
    cur_row = None
    cur_parts: list[str] = []
    cur_struct: list[Span] = []

    def flush():
        nonlocal pos, cur_parts, cur_struct
        if cur_row is None:
            return
        line_text = " ".join(cur_parts)
        out_lines.append(line_text)
        pos += 1
        cur_parts, cur_struct = [], []

    line_start = 0
    for rec in line_records:
        if rec["row"] != cur_row:
            if cur_row is not None:
                text_len = len(" ".join(cur_parts))
                for sp in cur_struct:
                    sp.start, sp.end = line_start, line_start + text_len
                pos = line_start + text_len
                flush()
            cur_row = rec["row"]
            line_start = pos
        for sp in rec["spans"]:
            if sp.status == "dropped":
                continue
            if sp.kind == "structure" and not sp.text:
                cur_struct.append(sp)
                continue
            offset = line_start + len(" ".join(cur_parts)) + (1 if cur_parts else 0)
            sp.start = offset
            sp.end = offset + len(sp.text)
            cur_parts.append(sp.text)
    if cur_row is not None:
        text_len = len(" ".join(cur_parts))
        for sp in cur_struct:
            sp.start, sp.end = line_start, line_start + text_len
        pos = line_start + text_len
        flush()
    draft = "\n".join(out_lines)

    def blocking_span(s: Span) -> bool:
        return s.status == "uncertain" and s.kind not in ("choice",) and not (s.kind == "structure" and s.bbox and in_choice(s.bbox))

    uncertain = [s for s in spans if s.status == "uncertain"]
    blocking_spans = [s for s in uncertain if blocking_span(s)]
    stem_text = "\n".join(
        " ".join(sp.text for sp in rec["spans"] if sp.status != "dropped" and not (sp.kind == "structure" and not sp.text))
        for rec in line_records if not rec["choice"]
    )
    diag_has_measure = any(re.search(r"\d|°|=|√|⊥|∥", t["text"]) for t in diagram_tokens)
    phrase = bool(_DIAGRAM_DEPENDENCY_RE.search(stem_text))
    if phrase:
        diagram_class = "DIAGRAM_REFERENCED_BY_TEXT"
    elif diag_has_measure:
        diagram_class = "DIAGRAM_HAS_MEASUREMENTS"
    elif figs and not diagram_tokens:
        diagram_class = "DIAGRAM_PRESENT_UNREAD"
    elif figs or diagram_tokens:
        labels = {re.sub(r"\s+", "", t["text"]).replace("′", "'") for t in diagram_tokens}
        draft_labels = set(re.findall(r"[A-Z][0-9]?'{0,2}", norm_math(stem_text.replace("′", "'"))))
        consistent = labels and all(all(p in draft_labels for p in re.findall(r"[A-Z][0-9]?'{0,2}", lab)) for lab in labels)
        diagram_class = "DIAGRAM_LABELS_ONLY_CONSISTENT" if consistent else "DIAGRAM_LABELS_UNMATCHED"
    else:
        diagram_class = "NO_DIAGRAM"
    diagram_blocking = diagram_class in ("DIAGRAM_REFERENCED_BY_TEXT", "DIAGRAM_HAS_MEASUREMENTS", "DIAGRAM_PRESENT_UNREAD", "DIAGRAM_LABELS_UNMATCHED")

    blocking: list[str] = []
    if not r_lines_all:
        blocking.append("NO_TEXT_DETECTED")
    if not tes.get("lines"):
        blocking.append("SECOND_READER_MISSING")
    if blocking_spans:
        blocking.append("UNCERTAIN_SPANS")
    if any(not f["in_choice_region"] for f in layout_flags):
        blocking.append("LAYOUT_STRUCTURE_SUSPECTED")
    if diagram_blocking:
        blocking.append("DIAGRAM_FACTS_UNVERIFIED")
    if extra_unknown:
        blocking.append("UNALIGNED_SECOND_READER_TEXT")

    if "NO_TEXT_DETECTED" in blocking or len(draft.strip()) < 10:
        ocr_decision = "LOCAL_OCR_REJECT_UNREADABLE"
    elif not blocking:
        ocr_decision = "LOCAL_OCR_ACCEPT"
    else:
        ocr_decision = "LOCAL_OCR_REVIEW_REQUIRED"

    return {
        "schema": OCR_RECONCILE_VERSION,
        "draft_text": draft,
        "lines": [{"line_id": r["line_id"], "bbox": r["bbox"], "choice": r["choice"], "span_ids": [s.span_id for s in r["spans"]]} for r in line_records],
        "spans": [s.to_dict() for s in spans],
        "uncertain_spans": [{**s.to_dict(), "blocking": blocking_span(s)} for s in uncertain],
        "disputed_math_slots": [
            {"slot_key": s.evidence, "bbox": list(s.bbox), "readings": s.readings}
            for s in uncertain if s.kind in ("math", "choice") and s.evidence and ":S" in s.evidence and s.bbox
        ] + (prime_probe_slots if "'" in draft else []),
        "layout_flags": layout_flags,
        "choice_bands": [[lo, None if hi == float("inf") else hi] for lo, hi in choice_bands],
        "diagram": {
            "figure_bboxes": [list(f) for f in figs],
            "tokens": diagram_tokens,
            "classification": diagram_class,
            "blocking": diagram_blocking,
        },
        "unaligned_second_reader_words": [{"text": w.text, "bbox": list(w.bbox)} for w in extra_unknown],
        "readers": {
            name: {"engine_version": e.get("engine_version"), "model": e.get("model"), "ms": e.get("ms"), "error": e.get("error")}
            for name, e in engines.items()
        },
        "policy": {"min_agreeing_families": min_agreeing_families},
        "extraction_verified": not blocking,
        "ocr_decision": ocr_decision,
        "blocking_reasons": blocking,
        "used_ground_truth": False,
    }


def reconcile_with_adjudication(
    raw: dict[str, Any],
    reread_fn,
    *,
    region_bbox: tuple[int, int, int, int] | None = None,
    figure_bboxes: Iterable[tuple[int, int, int, int]] = (),
    min_agreeing_families: int = 1,
) -> dict[str, Any]:
    """Hai pha: đối chiếu → đọc lại các vùng toán tranh chấp (`reread_fn(boxes) -> list[dict]`) → đối chiếu lại."""
    first = reconcile_local_ocr(raw, region_bbox=region_bbox, figure_bboxes=figure_bboxes, min_agreeing_families=min_agreeing_families)
    disputes = first["disputed_math_slots"]
    if not disputes:
        first["adjudication"] = {"requested": 0, "readers": []}
        return first
    rr = reread_fn([d["bbox"] for d in disputes]) or {}
    readings = rr.get("readings") or []
    adj: dict[str, dict[str, str]] = {}
    adj_meta: dict[str, dict[str, Any]] = {}
    readers_seen: set[str] = set()
    for d, rd in zip(disputes, readings):
        clean = {k: v for k, v in (rd or {}).items() if not k.endswith("_error") and isinstance(v, str)}
        readers_seen.update(clean)
        adj[d["slot_key"]] = clean
        if isinstance(rd, dict):
            meta_entry = {
                k: rd[k]
                for k in ("glyph_topology", "tesseract_eng_line_conf", "tesseract_vie_line_conf")
                if k in rd
            }
            if meta_entry:
                adj_meta[d["slot_key"]] = meta_entry
    second = reconcile_local_ocr(
        raw, region_bbox=region_bbox, figure_bboxes=figure_bboxes,
        adjudications=adj, min_agreeing_families=min_agreeing_families,
        adjudication_meta=adj_meta,
    )
    second["adjudication"] = {
        "requested": len(disputes),
        "unique_requested": rr.get("unique_requested", len(disputes)),
        "cache_hits": rr.get("cache_hits", 0),
        "readers": sorted(readers_seen),
        "ok": bool(rr.get("ok")),
        "ms": rr.get("total_ms"),
        "worker_ms": rr.get("worker_ms"),
        "timings": rr.get("timings"),
        "resolved": len(disputes) - len(second["disputed_math_slots"]),
    }
    return second
