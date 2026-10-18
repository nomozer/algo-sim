"""Synthetic runtime boundary, never a corpus outcome or a geometric timeout refusal."""
import os
import subprocess
import sys
import itertools
import re

import pytest

from app.simulation.geometry_functions.registry import _SAU_HOP_LE, _vung_hoi


def test_question_tail_has_bounded_runtime_on_long_rejected_and_accepted_text():
    code = '''
import time
from app.simulation.geometry_functions.registry import _SAU_HOP_LE, _bo_cum, _vung_hoi
start = time.perf_counter()
for n in (40, 256, 4096, 16384):
    for space in (" ", "\\u00a0", "\\u2003", "\\t"):
        assert _SAU_HOP_LE.match(space*n + "x") is None
        assert _SAU_HOP_LE.match(space*n + ".") is not None
for suffix in (" và cùng"*1000 + " x", ",;:"*1000 + " x", " và " + " "*128 + "(XYZ)."):
    assert _SAU_HOP_LE.match(suffix) is None
source = "Tính độ dài AB và góc giữa CD với mặt phẳng đáy (EFGH)."
assert _vung_hoi(source, source.index("độ dài"), source.index(" và")) is None
assert time.perf_counter() - start < 2
'''
    try:
        result = subprocess.run([sys._base_executable, "-B", "-c", code], capture_output=True, text=True,
                                env={**os.environ, "PYTHONPATH": os.pathsep.join(sys.path)}, timeout=8)
    except subprocess.TimeoutExpired:
        pytest.fail("Question-tail grammar exceeded the 8-second synthetic watchdog")
    assert result.returncode == 0, result.stderr


@pytest.mark.parametrize("tail", [".", "?", "", " và cùng .", "\u00a0và\u2003.",
                                 " (đơn vị: cm).", " theo a.", " biết AB = 3."])
def test_accepted_tail_forms_keep_their_language(tail):
    assert _SAU_HOP_LE.match(tail) is not None


@pytest.mark.parametrize("tail", [" x", " (kết quả nhân đôi).", " (đơn vị: một nửa cm).", " lên đáy.",
                                 " song song với CD.", " khi M thay đổi.", " (", " SC.SA"])
def test_unread_or_incomplete_tail_stays_rejected(tail):
    assert _SAU_HOP_LE.match(tail) is None


@pytest.mark.parametrize("source", ["Tính bình phương độ dài AB.", "Tính độ dài AB + CD.", "Tính độ dài AB lên đáy."])
def test_wrong_or_modified_operand_stays_rejected(source):
    a = source.index("độ dài")
    assert _vung_hoi(source, a, a + len("độ dài AB")) is None


def test_separator_change_preserves_legacy_match_boundaries_on_short_strings():
    old = re.compile(_SAU_HOP_LE.pattern.replace(r"[\s,;:]++", r"[\s,;:]+"), _SAU_HOP_LE.flags)
    for tokens in itertools.product((" ", "\u00a0", ",", "và", "x", ".", "?", "theo a"), repeat=4):
        text = "".join(tokens)
        a, b = old.match(text), _SAU_HOP_LE.match(text)
        assert (a.span() if a else None) == (b.span() if b else None), text
