import re, sys, unicodedata
from pathlib import Path
WT = Path(r"D:\Documents\projects\algo-sim\.superpowers\worktrees\local-first-geometry-understanding")
srcs = [WT / "backend/app/ai/local_geometry_parser.py", WT / "backend/app/simulation/geometry_functions/registry.py"]
text = "\n".join(p.read_text(encoding="utf-8") for p in srcs)
# only string literals
lits = re.findall(r'(?s)r?"(?:[^"\\\n]|\\.)*"|r?\'(?:[^\'\\\n]|\\.)*\'', text)
uni, bi = set(), set()
VI = re.compile(r"[a-zà-ỹđ]+")
for lit in lits:
    s = lit.lstrip("r")[1:-1]
    s = re.sub(r"\\[a-zA-Z]", " ", s)  # \s \b \w ...
    s = re.sub(r"[^A-Za-zÀ-ỹĐđ ]", " ", s)
    toks = [t.lower() for t in s.split()]
    toks = [t for t in toks if VI.fullmatch(t) and 1 <= len(t) <= 7]
    for t in toks:
        uni.add(t)
    for a, b in zip(toks, toks[1:]):
        bi.add(f"{a} {b}")
def is_vi_syllable(t):
    return bool(re.search(r"[à-ỹđ]", t)) or t in {"cho", "co", "la", "va", "khi", "goc"} or len(t) <= 4
_DIAC = re.compile(r"[à-ỹđ]")
_ascii_neighbours = set()
for b in bi:
    a, c = b.split()
    if _DIAC.search(a) and not _DIAC.search(c) and 2 <= len(c) <= 5:
        _ascii_neighbours.add(c)
    if _DIAC.search(c) and not _DIAC.search(a) and 2 <= len(a) <= 5:
        _ascii_neighbours.add(a)
def _strip(s):
    s = unicodedata.normalize("NFD", s.replace("đ", "d").replace("Đ", "D"))
    return "".join(c for c in s if not unicodedata.combining(c))
_SYL = re.compile(r"(?:ngh|ng|gh|gi|kh|nh|ph|qu|th|tr|ch|b|c|d|g|h|k|l|m|n|p|r|s|t|v|x)?[aeiouy]{1,3}(?:ch|ng|nh|c|m|n|p|t)?")
_accented_bases = {_strip(t) for t in uni if _DIAC.search(t)}
# Âm tiết KHÔNG dấu là từ thật trong từ vựng hình học phổ thông (danh sách chung, không lấy từ đề đánh giá):
# chúng trùng dạng bỏ dấu của từ khác (tam/tâm, trung/trùng, thang/thẳng…) nên không thể tự suy từ mã nguồn.
CURATED_ASCII_SYLLABLES = {
    "tam", "trung", "song", "cao", "hai", "ba", "cho", "khi", "theo", "sao", "nhau", "giao", "chia",
    "quanh", "quay", "tia", "xoay", "sinh", "thang", "thoi", "qua", "chu", "vi", "cung", "ta",
}
uni = sorted(
    t for t in uni
    if _DIAC.search(t) or (t in _ascii_neighbours and _SYL.fullmatch(t) and t not in _accented_bases)
)
uni = sorted(set(uni) | CURATED_ASCII_SYLLABLES)
from collections import Counter
_counts = Counter()
for lit in lits:
    s = re.sub(r"\\[a-zA-Z]", " ", lit.lstrip("r")[1:-1])
    s = re.sub(r"[^A-Za-zÀ-ỹĐđ ]", " ", s)
    _counts.update(t.lower() for t in s.split())
counts = {t: int(_counts.get(t, 0)) for t in uni}
bi = sorted(b for b in bi if all(re.search(r"[à-ỹđ]", w) or w in uni for w in b.split()))
print(len(uni), len(bi))
out = WT / "backend/app/ingestion/ocr_lexicon.py"
body = '# -*- coding: utf-8 -*-\n"""Từ vựng tiếng Việt cho khôi phục dấu khi đối chiếu OCR (sinh tự động, KHÔNG sửa tay).\n\nNguồn: chuỗi ký tự trong `backend/app/ai/local_geometry_parser.py` và\n`backend/app/simulation/geometry_functions/registry.py` (ngữ pháp mà Parser/Source Gate đọc được),\ntrích bởi `tools/build_ocr_lexicon.py` của run `image-first-ocr-verified-geometry`, cộng danh sách âm tiết không\ndấu chọn tay `CURATED_ASCII_SYLLABLES` (từ vựng hình học phổ thông). Không lấy từ bản chép đề hay ground truth\ncủa bất kỳ ảnh đánh giá nào.\n"""\n\n'
def _block(name, items):
    rows = "".join(f"    {x!r},\n" for x in items)
    return f"{name}: frozenset[str] = frozenset({{\n{rows}}})\n"
body += _block("LEXICON_UNIGRAMS", uni) + "\n" + _block("LEXICON_BIGRAMS", bi)
body += "\n#: Số lần xuất hiện trong chuỗi ngữ pháp — tiên nghiệm tần suất khi khôi phục dấu còn mơ hồ.\n"
body += "LEXICON_COUNTS: dict[str, int] = {\n" + "".join(f"    {k!r}: {v},\n" for k, v in sorted(counts.items())) + "}\n"
out.write_text(body, encoding="utf-8")
print("written", out)
