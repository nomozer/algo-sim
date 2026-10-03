# -*- coding: utf-8 -*-
"""W16 — build the W16 adversarial corpus from its hand labels (0 model calls).

`LABELS.json` (same directory) names, per row, a builder over the W16 RED tests in
`backend/tests/geometry/test_assumption_certificate.py`. This script only turns labels into
(contract, program) pairs; `../assumption_census_w16.py` measures them. Refuses to overwrite.
Run from the repository root:
  backend/.venv/Scripts/python.exe docs/evaluation/geometry/runs/w16-premerge-closure/diagnostics/assumption_corpus_w16/build_corpus.py
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve()
ROOT = HERE.parents[7]
LABELS = HERE.with_name("LABELS.json")
OUT = HERE.with_name("CORPUS.json")
sys.path.insert(0, str(ROOT / "backend"))
sys.path.insert(0, str(ROOT / "backend" / "scripts"))

from app.simulation.semantic_program.validator import validate_semantic_program  # noqa: E402
from tests.geometry import test_assumption_certificate as X  # noqa: E402

TEXT = {"biet_chieu_cao": X.NEN_T1 + X.DAY_T1 + ", cạnh bên SA vuông góc với đáy. Tính thể tích khối chóp "
                                                "S.ABC, biết chiều cao của khối chóp bằng 5."}
BUILDERS = {
    "mp_sai": lambda cid, _a: X.MP_SAI_THUC_THE[cid](),
    "mp_dung": lambda cid, _a: X.MP_DUNG_THUC_THE[cid](),
    "mp_gioi_han": lambda _c, _a: X._p1_mat_phang(
        X.HAI_MP, [("alpha_plane", (0, 0, 1, -3)), ("beta_plane", (0, 0, 1, -2))], "alpha_plane"),
    "t1_muc_tieu": lambda cid, _a: X._t1_cau(X.MUC_TIEU_THANH_TIEN_DE[cid]),
    "t1_gia_thiet": lambda cid, _a: X._t1_cau(X.GIA_THIET_GIU_NGUYEN[cid]),
    "t1_khong_khai_thac": lambda cid, _a: X._t1_cau(X.KHONG_KHAI_THAC_DUOC[cid]),
    "t1_text": lambda _c, arg: X._t1_cau(TEXT[arg]),
    "guard": lambda _c, arg: X.BON_NHANH[arg](),
    "t1": lambda _c, _a: X._t1(),
}


def _sha_lf(p: Path) -> str:
    return hashlib.sha256(p.read_bytes().replace(b"\r\n", b"\n")).hexdigest()


def main() -> None:
    if OUT.exists():
        raise SystemExit(f"refusing to overwrite {OUT}")
    rows = []
    for cid, l in json.loads(LABELS.read_text(encoding="utf-8"))["rows"].items():
        ct, raw = BUILDERS[l["builder"]](cid, l.get("arg"))
        v = validate_semantic_program(raw)
        ok = bool(v.ok and v.spec is not None)
        rows.append({"id": cid, "group": l["group"], "label": l["label"], "expect": l["expect"],
                     "reason": l["reason"], "contract": ct.model_dump(mode="json"),
                     "program": v.spec.model_dump(mode="json", exclude_none=True) if ok else raw,
                     "program_schema_ok": ok})
    OUT.write_text(json.dumps({"corpus": "W16_ADVERSARIAL_ADDENDUM", "model_calls": 0,
                               "labels_sha256_lf": _sha_lf(LABELS), "rows": rows},
                              ensure_ascii=False, indent=1) + "\n", encoding="utf-8", newline="\n")
    print(f"{OUT.name}: {len(rows)} rows; schema-invalid programs: "
          f"{[r['id'] for r in rows if not r['program_schema_ok']]}")


if __name__ == "__main__":
    main()
