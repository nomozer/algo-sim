"""Independent causal / pedagogical audit of a Scene3D payload (run `scene3d-causal-pedagogical-integrity`).

It reads ONLY the serialized scene (`objects`, `events`, `formation.steps`, `free_objects`) — never the producer code —
and reports violations by kind. Used on Route D served scenes, regenerated catalogs and static fixtures alike.

Birth of an object = the first formation step whose `visible_ids` holds it (free objects: step 0). A visual object's
prerequisites are its `visible_prerequisites` when the producer states them, else its `depends`.
"""
from __future__ import annotations

import re
from collections import defaultdict
from typing import Any

NON_VISUAL = {"non_visual", "readout"}
GENERIC = re.compile(r"Ghi nhận giá trị vừa tính được|Đã tính toán thành công|^Kiểm tra hình học\.?$")
ANGLE_KINDS = {"angle_cos", "angle_cos_sq"}
PERP_RELATIONS = {"perpendicular_lines", "perpendicular_line_plane", "perpendicular_planes"}
SINK_TYPES = {"quantity", "section", "solid", "curved_solid", "polygon3", "segment3", "circle3", "ellipse3", "sphere3", "plane3"}


def _visual(o: dict) -> bool:
    return o.get("render") not in NON_VISUAL and o.get("type") not in ("quantity", "vector3", "scalar")


def audit(scene: dict) -> dict[str, Any]:
    objs = scene.get("objects") or []
    by = {}
    v: dict[str, list] = defaultdict(list)
    for o in objs:
        if o["id"] in by:
            v["DUPLICATE_OBJECT_ID"].append(o["id"])
        by[o["id"]] = o
    steps = (scene.get("formation") or {}).get("steps") or []
    events = scene.get("events") or []
    free = set(scene.get("free_objects") or ())
    birth: dict[str, int] = {x: 0 for x in free}
    for s in steps:
        for x in s.get("visible_ids") or ():
            birth.setdefault(x, s["step_index"])
            if x not in by:
                v["VISIBLE_ID_UNKNOWN"].append([s["step_index"], x])
        if not isinstance(s.get("readout_ids"), list):
            v["READOUT_IDS_MISSING"].append(s.get("step_index"))
        else:
            for x in s["readout_ids"]:
                if x not in by:
                    v["READOUT_ID_UNKNOWN"].append([s["step_index"], x])
    # references
    for o in objs:
        for key in ("depends", "visible_prerequisites", "computational_depends"):
            for x in o.get(key) or ():
                if x not in by:
                    v["UNRESOLVED_REFERENCE"].append([o["id"], key, x])
    # causal birth order of visual objects
    for o in objs:
        if not _visual(o):
            continue
        pre = o.get("visible_prerequisites") if o.get("visible_prerequisites") is not None else o.get("depends") or []
        for x in pre:
            p = by.get(x)
            if p is None:
                continue
            if not _visual(p):
                v["HIDDEN_MATH_VISUAL_DEPENDENCY"].append([o["id"], x])
                continue
            if o["id"] not in birth:
                continue
            if x not in birth:
                v["PREREQUISITE_NEVER_SHOWN"].append([o["id"], x])
            elif birth[x] > birth[o["id"]]:
                v["CAUSAL_BIRTH_ORDER"].append([o["id"], birth[o["id"]], x, birth[x]])
    # CREATE events
    created = defaultdict(list)
    for e in events:
        if e.get("action") == "CREATE" and e.get("object"):
            created[e["object"]].append(e["step_index"])
            members = ((e.get("details") or {}) if isinstance(e.get("details"), dict) else {}).get("objects") or ()
            if e["object"] not in by and not (members and all(m in by for m in members)):
                v["CREATE_UNKNOWN_OBJECT"].append(e["object"])      # a group event names its members in details.objects
            for x in e.get("visible_prerequisites") or e.get("depends") or ():
                if x in by and _visual(by[x]) and x in birth and birth[x] > e["step_index"]:
                    v["EVENT_PREREQUISITE_LATE"].append([e["object"], e["step_index"], x, birth[x]])
    # event birth (what a timeline consumer sees): free ⇒ 0; else the first event naming it as its object or as a member
    ev_birth: dict[str, int] = {x: 0 for x in free}
    for e in events:
        members = [e.get("object")] + list(((e.get("details") or {}) if isinstance(e.get("details"), dict) else {}).get("objects") or ())
        for x in members:
            if x:
                ev_birth.setdefault(x, e["step_index"])
    for e in events:
        if e.get("action") != "CREATE" or e.get("object") not in by:
            continue
        o = by[e["object"]]
        pre = o.get("visible_prerequisites") if o.get("visible_prerequisites") is not None else o.get("depends") or []
        for x in pre:
            if x in by and _visual(by[x]):
                if x not in ev_birth:
                    v["CAUSAL_BIRTH_ORDER"].append([e["object"], e["step_index"], x, "no CREATE event"])
                elif ev_birth[x] > e["step_index"]:
                    v["CAUSAL_BIRTH_ORDER"].append([e["object"], e["step_index"], x, ev_birth[x]])
    for x, ks in created.items():
        if len(ks) > 1:
            v["DUPLICATE_CREATE"].append([x, ks])
        o = by.get(x)
        if o is not None and _visual(o) and x in birth and x not in free and birth[x] < min(ks):
            v["SHOWN_BEFORE_CREATE"].append([x, birth[x], min(ks)])
    # dependency cycles
    graph = {o["id"]: [x for x in (o.get("depends") or ()) if x in by] for o in objs}
    state: dict[str, int] = {}

    def dfs(n, path):
        state[n] = 1
        for m in graph.get(n, ()):
            if state.get(m) == 1:
                v["DEPENDENCY_CYCLE"].append(path + [m])
            elif state.get(m) is None:
                dfs(m, path + [m])
        state[n] = 2
    for n in graph:
        if state.get(n) is None:
            dfs(n, [n])
    # orphans: a derived point / line no other object uses and that is not a sink or target
    def strings(x, out):
        if isinstance(x, str):
            out.add(x)
        elif isinstance(x, dict):
            for k, y in x.items():
                if k != "id":
                    strings(y, out)
        elif isinstance(x, list):
            for y in x:
                strings(y, out)
    used: set[str] = set()
    for o in objs:
        refs: set[str] = set()
        strings({k: val for k, val in o.items() if k not in ("id", "label", "display_label", "reference", "notation")}, refs)
        used |= refs - {o["id"]}
    orphans = [o["id"] for o in objs if o.get("type") in ("point3", "line3") and o["id"] not in free
               and o["id"] not in used and o.get("type") not in SINK_TYPES and "target" not in (o.get("display_group") or "")
               and o.get("origin") != "given"]
    flagged = set(scene.get("unused_auxiliary_ids") or ())
    # MEASURE semantics
    measures = []
    for e in events:
        if e.get("action") != "MEASURE":
            continue
        o = by.get(e.get("object")) or {}
        mq = e.get("measured_quantity") or o.get("measured_quantity")
        text = " ".join(str(e.get(k) or "") for k in ("explanation", "learner_text"))
        row = {"object": e.get("object"), "step": e["step_index"], "generic": bool(GENERIC.search(text)),
               "has_measured_quantity": mq is not None}
        if mq:
            rel, kind, val = mq.get("certified_relation"), mq.get("quantity_kind"), str(mq.get("value"))
            if rel in PERP_RELATIONS and not (kind in ANGLE_KINDS and val == "0"):
                v["PERPENDICULAR_CLAIM_WITHOUT_ZERO_ANGLE"].append(e.get("object"))
            if kind in ANGLE_KINDS and val == "0" and rel not in PERP_RELATIONS:
                v["ZERO_ANGLE_WITHOUT_PERPENDICULAR_RELATION"].append(e.get("object"))
            if kind == "distance" and rel in PERP_RELATIONS:
                v["DISTANCE_CLAIMS_PERPENDICULARITY"].append(e.get("object"))
        if row["generic"]:
            v["GENERIC_MEASURE_TEXT"].append(e.get("object"))
        measures.append(row)
    return {"violations": {k: val for k, val in v.items()}, "violation_count": sum(len(x) for x in v.values()),
            "objects": len(objs), "events": len(events), "steps": len(steps),
            "orphans_independent": orphans, "unused_auxiliary_flagged": sorted(flagged),
            "orphans_not_flagged": sorted(set(orphans) - flagged), "measures": measures}
