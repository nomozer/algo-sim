"""Read-only probe: run with cwd = <checkout>/backend, argv[1] = repo root containing the CORPUS json."""
import json, sys, unicodedata
from copy import deepcopy
from pathlib import Path
sys.path.insert(0, ".")
from app.ai.function_route import run_fact_route
from tests.geometry import hybrid_compiler_benchmark as HB

def aux(qtext, quote=None):
    q, f = HB._with(HB._square(), HB._ask("q", quote or qtext, "distance", points_a=["S"], points_b=["B", "D"]))
    text = " ".join(q)
    if quote:
        text = text.replace(quote, qtext)
    r = run_fact_route(text, {"facts": f})
    return r.status, r.code, r.answers

AUX = [
    "Tính khoảng cách từ S đến BD.",
    "Tính bình phương khoảng cách từ S đến BD.",
    "Tính nửa khoảng cách từ S đến BD.",
    "Tính một nửa khoảng cách từ S đến BD.",
    "Tính bình phương của khoảng cách từ S đến BD.",
    "TÍNH BÌNH PHƯƠNG KHOẢNG CÁCH TỪ S ĐẾN BD.",
    unicodedata.normalize("NFD", "Tính bình phương khoảng cách từ S đến BD."),
    "Tính hai lần khoảng cách từ S đến BD.",
    "Tính căn bậc hai của khoảng cách từ S đến BD.",
    "Tính lập phương khoảng cách từ S đến BD.",
    "Tính nghịch đảo khoảng cách từ S đến BD.",
    "Tính một phần ba khoảng cách từ S đến BD.",
    "Tính 1/2 khoảng cách từ S đến BD.",
    "Tính gấp đôi khoảng cách từ S đến BD.",
    "Tính giá trị bình phương khoảng cách từ S đến BD.",
    "Tính bình  phương khoảng cách từ S đến BD.",
    "Tính khoảng cách từ S đến BD bình phương.",
    "Trong nửa mặt phẳng bờ BD chứa S, tính khoảng cách từ S đến BD.",
    "Xét nửa mặt phẳng bờ BD. Tính khoảng cách từ S đến BD.",
    "Tính bình phương độ dài SA và khoảng cách từ S đến BD.",
    "Tính khoảng cách từ S đến BD và nửa chu vi đáy.",
    "Hơn nữa, tính khoảng cách từ S đến BD.",
]
QUOTED_PART = [  # quote is only the bare phrase; modifier sits in the unquoted part of the sentence
    ("Tính bình phương khoảng cách từ S đến BD.", "khoảng cách từ S đến BD."),
    ("Tính nửa khoảng cách từ S đến BD.", "khoảng cách từ S đến BD."),
    ("Tính hai lần khoảng cách từ S đến BD.", "khoảng cách từ S đến BD."),
]

root = Path(sys.argv[1])
CORPUS = json.loads((root / "docs/evaluation/geometry/runs/goal-directed-planner-generalization-audit/next-slice-corpus.json").read_text(encoding="utf-8"))
GOAL = 'Tính khoảng cách từ M đến giao tuyến của (SAC) và (SBD).'

def lref(new, quote=None):
  try: return _lref(new, quote)
  except Exception as e: return ("EXC", type(e).__name__, str(e)[:80])
def _lref(new, quote=None):
    c = deepcopy(CORPUS['positive'][0])
    assert GOAL in c['text']
    c['text'] = c['text'].replace(GOAL, new)
    c['payload']['facts'][-1]['quotes'] = [quote or new]
    r = run_fact_route(c['text'], c['payload'])
    return r.status, r.code, r.answers

LREF = [
    (GOAL, None),
    ('Tính bình phương khoảng cách từ M đến giao tuyến của (SAC) và (SBD).', None),
    ('Tính bình phương khoảng cách từ M đến giao tuyến của (SAC) và (SBD).', 'khoảng cách từ M đến giao tuyến của (SAC) và (SBD).'),
    ('Tính nửa khoảng cách từ M đến giao tuyến của (SAC) và (SBD).', 'khoảng cách từ M đến giao tuyến của (SAC) và (SBD).'),
    ('Tính hai lần khoảng cách từ M đến giao tuyến của (SAC) và (SBD).', 'khoảng cách từ M đến giao tuyến của (SAC) và (SBD).'),
    ('Tìm khoảng cách từ M đến giao tuyến của (SAC) và (SBD).', None),
]

for t in AUX:
    print("AUX ", repr(t), aux(t))
for t, q in QUOTED_PART:
    print("AUXQ", repr(t), "quote=", repr(q), aux(t, q))
for t, q in LREF:
    print("LREF", repr(t), "quote=", repr(q), lref(t, q))
