# -*- coding: utf-8 -*-
"""regular-square-pyramid-w03 — cache evidence by rows. 0 model calls.

Question: would an envelope served under CACHE_VERSION 113 (W2 head fe68b4ca) still be returned from the cache after
W3, although W3 serves that request with different content? W3's only backend change is H-W2-2 (the segment whose
length the problem asks for is built before the answer — `formation._doan_duoc_hoi`).

Rows = the W2 corpus `../../regular-square-pyramid-w02/diagnostics/cache_proof_corpus_w02.json` (read only) + W3 rows
built here: the construction-binding corpus programs that measure a point-to-point distance as the answer
(`tests/geometry/test_construction_binding.py::CA`, served or refused before W3 — both kept), and a point-to-line
control.

`envelopes` and `prove` are the W1 script's own functions (imported by path, not copied). Modes:
  corpus --out <json>
  envelopes --backend <backend dir> --corpus <json> --out <json>
  prove --before <json> --after <json> --out <json>      (DATABASE_URL=sqlite:///<scratch>/w03_w01_cache_proof.db)
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve()
REPO = HERE.parents[6]
RUNS = HERE.parents[2]
spec = importlib.util.spec_from_file_location("proof_w01", RUNS / "regular-square-pyramid-w01" / "diagnostics"
                                              / "proof_cache_row_w01.py")
P1 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(P1)


def corpus(out: Path) -> None:
    P1._khong_ghi_de(out)
    sys.path.insert(0, str(REPO / "backend"))
    from tests.geometry import test_construction_binding as CB

    rows = json.loads((RUNS / "regular-square-pyramid-w02" / "diagnostics" / "cache_proof_corpus_w02.json")
                      .read_text(encoding="utf-8"))["rows"]
    for ca in sorted(CB.CA):
        contract, program = CB.CA[ca]()
        rows.append({"id": f"CB_{ca}", "label": "probe:construction_binding_corpus",
                     "contract": contract.model_dump(mode="json"), "program": program})
    contract, program = CB._p1(CB._van("B10_proj_line_ok"), [CB._duong("BD", "B", "D")], "S", "BD")
    rows.append({"id": "P_point_to_line_control", "label": "probe:served_before_w3",
                 "contract": contract.model_dump(mode="json"), "program": program})
    out.write_text(json.dumps({"source": "W2 cache_proof_corpus_w02.json + construction-binding corpus "
                                         "(test_construction_binding.CA) + point-to-line control (this script)",
                               "rows": rows}, ensure_ascii=False, indent=1) + "\n", encoding="utf-8", newline="\n")
    print(out, len(rows), "rows")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="mode", required=True)
    c = sub.add_parser("corpus")
    c.add_argument("--out", type=Path, required=True)
    e = sub.add_parser("envelopes")
    e.add_argument("--backend", type=Path, required=True)
    e.add_argument("--corpus", type=Path, required=True)
    e.add_argument("--out", type=Path, required=True)
    p = sub.add_parser("prove")
    p.add_argument("--before", type=Path, required=True)
    p.add_argument("--after", type=Path, required=True)
    p.add_argument("--out", type=Path, required=True)
    a = ap.parse_args()
    if a.mode == "corpus":
        corpus(a.out)
    elif a.mode == "envelopes":
        P1.envelopes(a.backend.resolve(), a.corpus, a.out)
    else:
        # W1 `prove` names its fields after W1; rename them so this file reads "before = W2 head under CACHE_VERSION
        # 113, after = W3". Values are untouched.
        tam = a.out.with_suffix(".tmp.json")
        P1.prove(a.before, a.after, tam)
        txt = tam.read_text(encoding="utf-8")
        for cu, moi in (('"before_w01"', '"before_w03"'), ('"w01_envelope_differs"', '"w03_envelope_differs"'),
                        ('"cached_before_w01"', '"cached_before_w03"'), ('"w01"', '"w03"'),
                        ('"W01_CACHE_ROW_PROOF"', '"W03_CACHE_ROW_PROOF"'), ("served before W1", "served before W3"),
                        ("although W1 now builds", "although W3 now builds"), ("unchanged under W1", "unchanged under W3")):
            txt = txt.replace(cu, moi)
        P1._khong_ghi_de(a.out)
        a.out.write_text(txt, encoding="utf-8", newline="\n")
        tam.unlink()
