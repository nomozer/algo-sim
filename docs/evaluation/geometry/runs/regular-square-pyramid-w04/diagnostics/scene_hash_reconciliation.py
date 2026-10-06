# -*- coding: utf-8 -*-
"""W4 — đối soát băm cảnh P1/P6 của `test_memory_declaration_contract_alignment` (H, I). 0 lượt gọi mạng.

Chạy từ `backend/` của cây cần đo:  python <file> dump <ra.json>   → ghi scene3d P1/P6 đúng như test H/I dựng.
                                    python <file> diff <a.json> <b.json> <ra.json> → liệt kê đường dẫn trường khác nhau.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path


def _dump(ra: str) -> None:
    sys.path.insert(0, str(Path.cwd()))
    import pytest
    from tests.semantic_program import test_memory_declaration_contract_alignment as T
    from app.ai import gemini

    out = {}
    with pytest.MonkeyPatch.context() as mp:
        mp.setattr(gemini, "BACKOFF_BASE_SECONDS", 0.0)
        p1 = T._prog(T.CA_P1)
        out["P1"] = T._envelope(mp, T.CA_P1, [json.dumps(p1, ensure_ascii=False)])["scene3d"]
        hong = T._c02_bi_loai_dan_xuat()
        sua = json.loads(json.dumps(hong))
        sua["memory_declarations"][0]["initial_value"] = sua["memory_declarations"][0].pop("at")
        out["P6"] = T._envelope(mp, T.CA_P6, [json.dumps(hong, ensure_ascii=False),
                                               json.dumps(sua, ensure_ascii=False)])["scene3d"]
    out["bam"] = {k: T._bam(out[k]) for k in ("P1", "P6")}
    Path(ra).write_text(json.dumps(out, ensure_ascii=False, indent=1, sort_keys=True, default=str), encoding="utf-8")
    print(out["bam"])


def _phang(o, p=""):
    if isinstance(o, dict):
        for k, v in o.items():
            yield from _phang(v, f"{p}.{k}")
    elif isinstance(o, list):
        for i, v in enumerate(o):
            yield from _phang(v, f"{p}[{i}]")
    else:
        yield p, o


def _diff(a: str, b: str, ra: str) -> None:
    A, B = (json.loads(Path(x).read_text(encoding="utf-8")) for x in (a, b))
    kq = {}
    for k in ("P1", "P6"):
        fa, fb = dict(_phang(A[k])), dict(_phang(B[k]))
        kq[k] = {
            "bam_truoc": A["bam"][k], "bam_sau": B["bam"][k],
            "so_vat": [len(A[k]["objects"]), len(B[k]["objects"])],
            "them": sorted(set(fb) - set(fa)),
            "xoa": sorted(set(fa) - set(fb)),
            "doi": [{"truong": p, "truoc": fa[p], "sau": fb[p]} for p in sorted(set(fa) & set(fb)) if fa[p] != fb[p]],
        }
    Path(ra).write_text(json.dumps(kq, ensure_ascii=False, indent=1), encoding="utf-8")
    for k, v in kq.items():
        print(k, "them", len(v["them"]), "xoa", len(v["xoa"]), "doi", len(v["doi"]))


if __name__ == "__main__":
    {"dump": _dump, "diff": _diff}[sys.argv[1]](*sys.argv[2:])
