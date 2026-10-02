# -*- coding: utf-8 -*-
"""W14 Task 11 — the cross-section sub-steps are unchanged by S4 (0 model calls).

Pairs the formation steps that focus a `section` object in the w12 and w14
cross-section fixtures, in order. Every field is compared exactly except three
that S4 changes by construction: `step_index` (solid-formation steps are inserted
before the section), `formation_roles` (new metadata) and `visible_ids`, whose
difference must be exactly the objects S4 inserted (present in w14, absent in w12).
Run from the repository root:
  backend/.venv/Scripts/python.exe docs/evaluation/geometry/runs/w14-generic-formation-assumption/diagnostics/section_substeps_compare.py
"""
from __future__ import annotations

import json
from pathlib import Path

HERE = Path(__file__).resolve()
ROOT = HERE.parents[6]
RUNS = ROOT / "docs/evaluation/geometry/runs"
W12 = RUNS / "w12-pedagogical-grounding-closure/inputs/fixtures/cross_section_positive.json"
W14 = RUNS / "w14-generic-formation-assumption/inputs/fixtures/cross_section_positive.json"
OUT = HERE.with_name("SECTION_SUBSTEPS_W12_W14.json")
S4_CHANGED = ("step_index", "formation_roles", "visible_ids")


def _scene(p: Path) -> dict:
    return json.loads(p.read_text(encoding="utf-8"))["envelope"]["scene3d"]


def _section_steps(scene: dict) -> list[dict]:
    sec = {o["id"] for o in scene["objects"] if o.get("type") == "section"}
    return [s for s in scene["formation"]["steps"] if sec & set(s.get("focus_ids", []))]


def compare(old: dict, new: dict) -> dict:
    inserted = {o["id"] for o in new["objects"]} - {o["id"] for o in old["objects"]}
    a, b = _section_steps(old), _section_steps(new)
    pairs = []
    for x, y in zip(a, b):
        fields = sorted((set(x) | set(y)) - set(S4_CHANGED))
        extra = sorted(set(y["visible_ids"]) - set(x["visible_ids"]))
        pairs.append({
            "w12_step": x["step_index"], "w14_step": y["step_index"],
            "unequal_fields": [k for k in fields if x.get(k) != y.get(k)],
            "visible_ids_added": extra,
            "visible_ids_removed": sorted(set(x["visible_ids"]) - set(y["visible_ids"])),
            "added_are_s4_objects": set(extra) <= inserted,
        })
    same = (len(a) == len(b) and all(not p["unequal_fields"] and not p["visible_ids_removed"]
                                     and p["added_are_s4_objects"] for p in pairs))
    return {"fields_changed_by_s4": list(S4_CHANGED), "s4_inserted_objects": sorted(inserted),
            "section_steps": {"w12": len(a), "w14": len(b)}, "pairs": pairs,
            "verdict": "SECTION_SUBSTEPS_UNCHANGED" if same else "SECTION_SUBSTEPS_CHANGED"}


def main() -> None:
    report = compare(_scene(W12), _scene(W14))
    OUT.write_text(json.dumps({
        "check": "W14_SECTION_SUBSTEPS_UNCHANGED", "model_calls": 0,
        "w12_fixture": W12.relative_to(ROOT).as_posix(), "w14_fixture": W14.relative_to(ROOT).as_posix(),
        **report,
    }, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(OUT.name, report["verdict"])


if __name__ == "__main__":
    main()
