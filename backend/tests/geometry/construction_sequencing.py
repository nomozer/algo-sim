"""Learner-facing construction order of a served scene — contract O1–O4, O6 of run `pedagogical-construction-sequencing`.

Reads only the scene payload (objects, formation steps, events). No product import, no geometry: order and typed fields.
O5 (math invariance) compares two runs and lives in `scripts/measure_construction_sequencing.py`.
"""
from __future__ import annotations

SOLID_FORMATION = ("CONSTRUCT_BASE", "CONSTRUCT_HEIGHT", "CONSTRUCT_TRANSLATED_FACE", "CONSTRUCT_LATERAL_BOUNDARY")
ORDER = {"PYRAMID_LIKE": ("CONSTRUCT_BASE", "CONSTRUCT_LATERAL_BOUNDARY", "CLOSE_SOLID"),
         "PRISM_LIKE": ("CONSTRUCT_BASE", "CONSTRUCT_TRANSLATED_FACE", "CONSTRUCT_LATERAL_BOUNDARY", "CLOSE_SOLID")}
KEYWORD = {"construct_point.midpoint": "trung điểm", "construct_point.translate": "vectơ",
           "construct_point.project_onto": "hình chiếu", "construct_point.intersect_line_line": "giao",
           "construct_point.intersect_line_plane": "giao"}


def first_steps(scene):
    first = {}
    for st in scene["formation"]["steps"]:
        for i in st["visible_ids"]:
            first.setdefault(i, st["step_index"])
    return first


def closure(scene, ids):
    objs = {o["id"]: o for o in scene["objects"]}
    seen, todo = set(), list(ids)
    while todo:
        i = todo.pop()
        if i in seen or i not in objs:
            continue
        seen.add(i)
        todo += objs[i]["depends"]
    return seen


def check(scene):
    """→ {rule: [violations]} for O1–O4 (empty lists = pass)."""
    objs = {o["id"]: o for o in scene["objects"]}
    first = first_steps(scene)
    v = {"O1": [], "O2": [], "O3": [], "O4": []}
    for i, k in first.items():
        late = [d for d in objs[i]["depends"] if d in first and first[d] >= k > 0]
        if late:
            v["O1"].append(f"{i}@{k} before {late}")
    formation = [o["id"] for o in scene["objects"] if set(o.get("formation_roles") or ()) & set(SOLID_FORMATION)]
    for s in (o for o in scene["objects"] if o["type"] == "solid"):
        k_close = first.get(s["id"])
        allowed = closure(scene, [s["id"], *formation])
        for o in scene["objects"]:
            if (o.get("producer") and o["type"] in ("point3", "vector3", "line3", "plane3") and o["id"] not in allowed
                    and o["id"] in first and first[o["id"]] <= k_close):
                v["O2"].append(f"{o['id']}@{first[o['id']]} before solid {s['id']}@{k_close}")
        want = ORDER.get(s.get("shape_class") or "")
        # each required role at its OWN step, in order (review K1: a step carrying two roles does not count)
        seen = [(st["step_index"], r) for st in scene["formation"]["steps"] if st["step_index"] <= k_close
                for r in st["formation_roles"] if want and r in want]
        if want is None:
            v["O3"].append(f"{s['id']}: solid not classified ({s.get('shape_class')})")
        elif [r for _, r in seen] != list(want) or len({k for k, _ in seen}) != len(seen):
            v["O3"].append(f"{s['id']}: formation roles {seen} != {list(want)} at distinct steps")
    events = {e["step_index"]: e for e in scene["events"]}
    for o in scene["objects"]:
        kw = KEYWORD.get(o.get("producer") or "")
        if o["type"] != "point3" or kw is None or o["id"] not in first:
            continue
        text = events[first[o["id"]]]["learner_text"]
        names = [o.get("notation")] + [objs[d].get("notation") for d in o["depends"] if d in objs]
        direction = (o.get("producer") != "construct_point.translate"
                     or f"vectơ {names[1]}{names[0]}" in text)           # review K2: vectơ (base → new point)
        if kw not in text.lower() or any(n and n not in text for n in names) or not direction:
            v["O4"].append(f"{o['id']}: {text!r} lacks {kw!r}, operands {names} or direction")
    return v
