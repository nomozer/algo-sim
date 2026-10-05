# -*- coding: utf-8 -*-
"""regular-square-pyramid-w02 — cache evidence by rows. 0 model calls.

Question: would an envelope served under CACHE_VERSION 112 (W1 head e821b9b5) still be returned from the cache after
W2, although W2 serves that request with different content?

Rows = the W1 corpus file `../../regular-square-pyramid-w01/diagnostics/cache_proof_corpus_w01_r2.json` (read only;
24 labelled rows + 2 probes) + W2 rows built here: the six older families' compiler programs (served before W2),
the coincidence prism (`test_regular_square_pyramid_w02.lang_tru_canh_tren_bang_chieu_cao`), and the regular pyramid
whose program names the slanted lateral edge `SA_length`.

`envelopes` and the sqlite `prove` step are the W1 script's own functions (imported by path, not copied); only the
DATABASE_URL guard name differs. Modes:
  corpus --out <json>
  envelopes --backend <backend dir> --corpus <json> --out <json>      (W1 `envelopes`)
  prove --before <json> --after <json> --out <json>                   (W1 `prove`; DATABASE_URL=sqlite:///<scratch>/w01_cache_proof.db)
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve()
REPO = HERE.parents[6]
W1 = HERE.parents[2] / "regular-square-pyramid-w01" / "diagnostics"
spec = importlib.util.spec_from_file_location("proof_w01", W1 / "proof_cache_row_w01.py")
P1 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(P1)


def corpus(out: Path) -> None:
    P1._khong_ghi_de(out)
    sys.path.insert(0, str(REPO / "backend"))
    from tests.geometry import test_regular_square_pyramid as T
    from tests.geometry import test_regular_square_pyramid_w02 as T2
    from tests.geometry import w14_cases as W

    rows = json.loads((W1 / "cache_proof_corpus_w01_r2.json").read_text(encoding="utf-8"))["rows"]
    for ho, f in sorted(W.HO.items()):
        _text, contract = f()
        rows.append({"id": f"F_{ho}", "label": "probe:family_served_before_w2",
                     "contract": contract.model_dump(mode="json"), "program": W.chuong_trinh(contract)})
    contract, program = T2.lang_tru_canh_tren_bang_chieu_cao()
    rows.append({"id": "P_prism_top_edge_equals_height", "label": "probe:served_before_w2",
                 "contract": contract.model_dump(mode="json"), "program": program})
    contract, program = T.CA["S4_side_lateral_volume"]()
    for m in program["memory_declarations"]:
        if m["name"] == "canh_ben":
            m["name"] = "SA_length"
    rows.append({"id": "P_regular_named_lateral_SA", "label": "probe:served_before_w2",
                 "contract": contract.model_dump(mode="json"), "program": program})
    out.write_text(json.dumps({"source": "W1 cache_proof_corpus_w01_r2.json + six families (w14_cases.HO, compiler "
                                         "programs) + two W2 probes (this script)", "rows": rows},
                              ensure_ascii=False, indent=1) + "\n", encoding="utf-8", newline="\n")
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
        # W1 `prove` names its fields after W1; rename them so this file reads "before = W1 head under CACHE_VERSION
        # 112, after = W2". Values are untouched.
        tam = a.out.with_suffix(".tmp.json")
        P1.prove(a.before, a.after, tam)
        txt = tam.read_text(encoding="utf-8")
        for cu, moi in (('"before_w01"', '"before_w02"'), ('"w01_envelope_differs"', '"w02_envelope_differs"'),
                        ('"cached_before_w01"', '"cached_before_w02"'), ('"w01"', '"w02"'),
                        ('"W01_CACHE_ROW_PROOF"', '"W02_CACHE_ROW_PROOF"'), ("served before W1", "served before W2"),
                        ("although W1 now builds", "although W2 now builds"), ("unchanged under W1", "unchanged under W2")):
            txt = txt.replace(cu, moi)
        P1._khong_ghi_de(a.out)
        a.out.write_text(txt, encoding="utf-8", newline="\n")
        tam.unlink()
