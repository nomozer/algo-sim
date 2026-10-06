# -*- coding: utf-8 -*-
"""regular-square-pyramid-w04 — cache evidence by rows. 0 model calls.

Question: would an envelope served under CACHE_VERSION 114 (pre-W4 head f3db0f6f) still be returned from the cache
after W4, although W4 serves that request with different content? W4's backend changes: a segment lying on a solid
edge yields its stroke to that edge (`segments_on_edges` → `boundary_edge_ids` + `edge_span`, ce44eb38) and the
narration names objects by their problem symbol (`ten_trong_loi_ke`, 270cae4e).

Rows = the W3 corpus `../../regular-square-pyramid-w03/diagnostics/cache_proof_corpus_w03.json` (read only) + the
SM control (M midpoint of SA, the asked segment SM lies on edge SA — `tests/geometry/test_regular_square_pyramid_w04`).

`envelopes` and `prove` are the W1 script's own functions (imported by path, not copied). Modes:
  corpus --out <json>
  envelopes --backend <backend dir> --corpus <json> --out <json>
  prove --before <json> --after <json> --out <json>      (DATABASE_URL=sqlite:///<scratch>/w04_cache_proof.db)
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
    from tests.geometry import test_regular_square_pyramid_w04 as T4

    rows = json.loads((RUNS / "regular-square-pyramid-w03" / "diagnostics" / "cache_proof_corpus_w03.json")
                      .read_text(encoding="utf-8"))["rows"]
    contract, program = CB._p1(T4.VAN_SM, [CB._mid("M", "S", "A")], "S", "M")
    rows.append({"id": "SM_on_edge_SA", "label": "probe:segment_on_solid_edge",
                 "contract": contract.model_dump(mode="json"), "program": program})
    out.write_text(json.dumps({"source": "W3 cache_proof_corpus_w03.json + SM-on-edge control (this script)",
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
        # W1 `prove` names its fields after W1; rename them so this file reads "before = pre-W4 head under
        # CACHE_VERSION 114, after = W4". Values are untouched.
        tam = a.out.with_suffix(".tmp.json")
        P1.prove(a.before, a.after, tam)
        txt = tam.read_text(encoding="utf-8")
        for cu, moi in (('"before_w01"', '"before_w04"'), ('"w01_envelope_differs"', '"w04_envelope_differs"'),
                        ('"cached_before_w01"', '"cached_before_w04"'), ('"w01"', '"w04"'),
                        ('"W01_CACHE_ROW_PROOF"', '"W04_CACHE_ROW_PROOF"'), ("served before W1", "served before W4"),
                        ("although W1 now builds", "although W4 now builds"), ("unchanged under W1", "unchanged under W4")):
            txt = txt.replace(cu, moi)
        P1._khong_ghi_de(a.out)
        a.out.write_text(txt, encoding="utf-8", newline="\n")
        tam.unlink()
