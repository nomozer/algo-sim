# -*- coding: utf-8 -*-
"""W20 self-review F3 — how often do stored programs declare a point by coordinates AND construct the same name?
0 model calls, read-only.

§17 refuses a text-relation target whose definition chain carries coordinates, including coordinates that a later
construction overwrites (LABELS row L16). If real model outputs commonly used a coordinate placeholder before the
construction, the rule would refuse answers that were served correctly. This scan reads every JSON file under docs/,
backend/tests, frontend/src and frontend/scripts (files up to 8 MB), collects every distinct program (an object with
`memory_declarations` and `statements` lists) and lists the programs where a `point3` with a non-seed value (a declared
value or a `declare_point`) is also the target of a point construction (`construct_point`, or `assign` with a
point-producing expression). A seed is None or an empty container, as in `grounding_gate._is_seed`.
Writes `LITERAL_THEN_CONSTRUCT_SCAN.json` next to this file; refuses to overwrite. Run from the repository root.
"""
from __future__ import annotations

import json
import subprocess
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[5]
OUT = HERE / "LITERAL_THEN_CONSTRUCT_SCAN.json"
SINH_DIEM = {"midpoint", "divide_segment", "project_onto", "intersect_line_plane", "intersect_line_line", "translate"}


def _seed(v) -> bool:
    return v is None or (isinstance(v, (list, tuple, dict)) and not v)


def _chuong_trinh(o):
    if isinstance(o, dict):
        if isinstance(o.get("memory_declarations"), list) and isinstance(o.get("statements"), list):
            yield o
        for v in o.values():
            yield from _chuong_trinh(v)
    elif isinstance(o, list):
        for v in o:
            yield from _chuong_trinh(v)


def _lenh(sts):
    for s in sts or []:
        if isinstance(s, dict):
            yield s
            for k in ("body", "then_body", "else_body"):
                yield from _lenh(s.get(k))


def main() -> None:
    if OUT.exists():
        raise SystemExit(f"refusing to overwrite {OUT}")
    da, so_tep, trung = set(), 0, []
    for goc in ("docs", "backend/tests", "frontend/src", "frontend/scripts"):
        for p in sorted((ROOT / goc).rglob("*.json")):
            if p.stat().st_size > 8_000_000:
                continue
            try:
                o = json.loads(p.read_text(encoding="utf-8"))
            except (ValueError, UnicodeDecodeError):
                continue
            so_tep += 1
            for g in _chuong_trinh(o):
                khoa = json.dumps(g, sort_keys=True, ensure_ascii=False)
                if khoa in da:
                    continue
                da.add(khoa)
                lit = {m.get("name") for m in g["memory_declarations"]
                       if isinstance(m, dict) and m.get("type") == "point3" and not _seed(m.get("initial_value"))}
                lit |= {s.get("target_var") for s in _lenh(g["statements"])
                        if s.get("kind") == "declare_point" and not _seed(s.get("at"))}
                dung = {s.get("target_var") for s in _lenh(g["statements"]) if s.get("kind") in ("construct_point", "assign")
                        and isinstance(s.get("expr"), dict) and s["expr"].get("kind") in SINH_DIEM}
                if hai := sorted(x for x in lit & dung if x):
                    trung.append({"file": p.relative_to(ROOT).as_posix(), "names": hai})
    head = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True).stdout.strip()
    OUT.write_text(json.dumps({"scan": "W20_LITERAL_THEN_CONSTRUCT", "measured_at_commit": head, "model_calls": 0,
                               "json_files_read": so_tep, "distinct_programs": len(da),
                               "programs_declaring_and_constructing_the_same_point": len(trung), "hits": trung},
                              ensure_ascii=False, indent=1) + "\n", encoding="utf-8", newline="\n")
    print(so_tep, "files |", len(da), "distinct programs |", len(trung), "hits:", trung)


if __name__ == "__main__":
    main()
