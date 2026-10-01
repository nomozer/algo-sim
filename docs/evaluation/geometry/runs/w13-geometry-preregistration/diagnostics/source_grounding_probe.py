# -*- coding: utf-8 -*-
"""W13 Phase 7 probe: which length phrasings does the CURRENT source reader accept?

Read-only and offline (0 model calls). It calls the readers already in the product:
  * segment_relation.do_dai_trong_de       (segment lengths the source states)
  * grounding_gate._bang_chung_do_dai      (W12 GIVEN source evidence for one length)
  * literal_extractor.extract_literals     (literal candidates)
It changes nothing and never overwrites a result: a later wave passes its own output
path. Run from backend/:
  PYTHONIOENCODING=utf-8 .venv/Scripts/python.exe \
    ../docs/evaluation/geometry/runs/w13-geometry-preregistration/diagnostics/source_grounding_probe.py \
    <new output .json>
"""
from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from fractions import Fraction
from pathlib import Path

HERE = Path(__file__).resolve()
BACKEND = HERE.parents[6] / "backend"
sys.path.insert(0, str(BACKEND))

from app.simulation.semantic_program import grounding_gate as G  # noqa: E402
from app.simulation.semantic_program import literal_extractor as L  # noqa: E402
from app.simulation.semantic_program import segment_relation as S  # noqa: E402

# (id, text, declared length name, declared value, phrasing class)
CASES = [
    ("eq_plain", "Cho hình chóp S.ABC có AB = 5.", "AB_length", Fraction(5), "AB = 5"),
    ("eq_bang", "Cho hình chóp S.ABC có AB bằng 5.", "AB_length", Fraction(5), "AB bằng 5"),
    ("dai_cm", "Cho hình chóp S.ABC có AB dài 5 cm.", "AB_length", Fraction(5), "AB dài 5 cm"),
    ("do_dai_doan_bang", "Cho hình chóp S.ABC có độ dài đoạn AB bằng 5.", "AB_length", Fraction(5),
     "độ dài đoạn AB bằng 5"),
    ("canh_co_do_dai", "Cho hình chóp S.ABC có cạnh AB có độ dài 5.", "AB_length", Fraction(5),
     "cạnh AB có độ dài 5"),
    ("doan_co_do_dai", "Cho hình chóp S.ABC có đoạn AB có độ dài 5.", "AB_length", Fraction(5),
     "đoạn AB có độ dài 5"),
    ("prime_ascii", "Cho lăng trụ ABC.A'B'C' có AA' = 5.", "AA_prime_length", Fraction(5), "AA' = 5"),
    ("prime_unicode", "Cho lăng trụ ABC.A′B′C′ có AA′ = 5.", "AA_prime_length", Fraction(5), "AA′ = 5"),
    ("decimal_dot", "Cho hình chóp S.ABC có AB = 2.5.", "AB_length", Fraction(5, 2), "AB = 2.5"),
    ("decimal_comma", "Cho hình chóp S.ABC có AB = 2,5.", "AB_length", Fraction(5, 2), "AB = 2,5"),
    ("fraction", "Cho hình chóp S.ABC có AB = 5/2.", "AB_length", Fraction(5, 2), "AB = 5/2"),
    ("radical", "Cho hình chóp S.ABC có AB = 2√3.", "AB_length", "2√3", "AB = 2√3"),
    ("radical_fraction", "Cho hình chóp S.ABC có AB = 3√2/2.", "AB_length", "3√2/2", "AB = 3√2/2"),
    ("unit_space", "Cho hình chóp S.ABC có AB = 5 cm.", "AB_length", Fraction(5), "AB = 5 cm"),
    ("unit_glued", "Cho hình chóp S.ABC có AB = 5cm.", "AB_length", Fraction(5), "AB = 5cm"),
    ("chain_equal", "Cho hình chóp S.ABC có AB = AC = 5.", "AC_length", Fraction(5), "AB = AC = 5"),
    ("chain_equal_first", "Cho hình chóp S.ABC có AB = AC = 5.", "AB_length", Fraction(5),
     "AB = AC = 5 → khai AB = 5"),
    ("radical_wrong_segment", "Cho hình chóp S.ABC có AB = 2√3.", "AC_length", "2√3",
     "AB = 2√3 nhưng khai AC = 2√3"),
    ("regular_edge", "Cho tứ diện đều ABCD cạnh 5.", "AB_length", Fraction(5), "tứ diện đều ABCD cạnh 5"),
    ("regular_base", "Cho hình chóp tam giác đều S.ABC có cạnh đáy bằng 5.", "AB_length", Fraction(5),
     "chóp tam giác đều, cạnh đáy bằng 5"),
    ("cube_edge_other_segment", "Cho hình lập phương ABCD.A'B'C'D' có cạnh bằng 5.", "CC_prime_length",
     Fraction(5), "lập phương cạnh 5 → CC′ (topology-derived)"),
    ("box_derived", "Cho hình hộp chữ nhật ABCD.A'B'C'D' có AB = 3, AD = 4, AA' = 5.", "CD_length",
     Fraction(3), "hộp chữ nhật AB = 3 → CD (topology-derived)"),
    ("wrong_segment_same_number", "Cho hình chóp S.ABC có AB = 5, SA = 7.", "AC_length", Fraction(5),
     "AB = 5 nhưng khai AC = 5"),
    ("standalone_wrong_segment", "Cho hình chóp S.ABC có AB dài 5 cm.", "AC_length", Fraction(5),
     "AB dài 5 cm nhưng khai AC = 5"),
    ("value_absent", "Cho hình chóp S.ABC có AB = 5.", "AB_length", Fraction(7), "AB = 5 nhưng khai AB = 7"),
]


def _jsonable(x):
    if isinstance(x, Fraction):
        return str(x)
    if isinstance(x, (frozenset, set)):
        return sorted(_jsonable(v) for v in x)
    if isinstance(x, dict):
        return {str(_jsonable(k)): _jsonable(v) for k, v in x.items()}
    if isinstance(x, (list, tuple)):
        return [_jsonable(v) for v in x]
    return x


def run() -> dict:
    rows = []
    for cid, text, name, value, phrasing in CASES:
        lengths = S.do_dai_trong_de(text)
        err, evidence, reason = G._bang_chung_do_dai(text, name, value, None)
        rows.append({
            "id": cid,
            "phrasing": phrasing,
            "text": text,
            "declared": {"name": name, "value": _jsonable(value)},
            "do_dai_trong_de": {"-".join(sorted(k)): str(v) for k, v in lengths.items()},
            "given_evidence_error": err,
            "given_evidence": _jsonable(evidence),
            "given_evidence_reason": reason,
            "literals": [f"{c.kind}:{c.source_text}" for c in L.extract_literals(text)],
        })
    head = subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True,
                          cwd=BACKEND).stdout.strip()
    return {
        "probe": "W13_SOURCE_GROUNDING_PHRASING_PROBE",
        "measurement_class": "OFFLINE_READER_PROBE",
        "model_calls": 0,
        "git_head": head,
        "probe_sha256": hashlib.sha256(HERE.read_bytes().replace(b"\r\n", b"\n")).hexdigest(),
        "probe_sha256_basis": "LF-normalised content (= git blob content), so a CRLF checkout hashes the same",
        "readers": ["segment_relation.do_dai_trong_de", "grounding_gate._bang_chung_do_dai",
                    "literal_extractor.extract_literals"],
        "rows": rows,
    }


if __name__ == "__main__":
    out = Path(sys.argv[1]) if len(sys.argv) > 1 else HERE.with_name("SOURCE_GROUNDING_PHRASING_PROBE.json")
    if out.exists():
        raise SystemExit(f"refusing to overwrite {out}; pass a new output path")
    out.write_text(json.dumps(run(), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(out)
