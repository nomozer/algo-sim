# -*- coding: utf-8 -*-
"""TypedFactNext (`typed-fact-next/1`) → planner `TypedFact` facts — a PURE translation (run `typedfactnext-planner-bridge`).

The bridge renames fields; it never reads the problem text, never adds a fact, never infers a relation. What `TypedFact`
cannot express is refused with a typed `BRIDGE_UNSUPPORTED_*` code — never routed to a different engine path. The facts
then go through the ONE planner (`lap_ke_hoach`), Source Gate (`kiem_nguon`) and engine of route B; every quote, number,
role and cut is re-checked there. Contract and decision: `docs/architecture/HYBRID_BACKEND_TARGET_ARCHITECTURE.md`.
"""
from __future__ import annotations

from functools import partial
from typing import Any

from .registry import TuChoi
from .typed_fact_next import (
    _ARGS_LOI,
    _ARGS_GOC_VUONG,
    DerivedPlaneSectionSpec,
    DerivedPlaneSectionSpecV2,
    TypedFactNextPayload,
    TypedFactNextValidationError,
    parse_qualified_ref,
    split_vertex_chain,
    parse_typed_fact_next,
    parse_typed_fact_next_v2,
)

BRIDGE_VERSION = "typed-fact-next-bridge/1"
#: `/2` bridge (run `hybrid-contract-v2`, owner D1/D5): stated intersections → stated cuts, D6 enabled, declared boundary.
BRIDGE_V2_VERSION = "typed-fact-next-bridge/2"

_PLANE_RELATION = {"through_point_parallel_plane": "parallel", "through_point_perpendicular_line": "perpendicular",
                   "through_point_parallel_two_lines": "parallel_two_lines"}
_REGULAR_SHAPE = {3: "equilateral_triangle", 4: "square", 6: "regular_hexagon"}
#: Goals that add no fact: a declared solid is already built (`construct_object`); highlight / sequence are presentation.
#: Recorded as such in the bridge receipt, never turned into a hidden fact.
_NO_NEW_FACT_GOALS = ("highlight_geometry", "construction_sequence", "construct_object")


def _ref(ref: str) -> str:
    """A vertex reference as a global label. Only identity bindings reach here (checked in `bridge`), so a solid-qualified
    reference `pyr::A` and `A` are the same point."""
    if not isinstance(ref, str):
        raise TuChoi("INVALID_TYPED_FACT_NEXT", "tham chiếu đỉnh phải là chuỗi")
    try:
        return parse_qualified_ref(ref)[1]
    except TypedFactNextValidationError as e:
        raise TuChoi(e.code, e.detail) from None


def _refs(xs) -> list[str]:
    if not isinstance(xs, (list, tuple)):
        raise TuChoi("INVALID_TYPED_FACT_NEXT", "các tham chiếu đỉnh phải là danh sách")
    return [_ref(x) for x in xs]


def _check_qualified_refs(value: Any, solids: dict[str, Any], owned: dict[str, set[str]] | None = None) -> None:
    """Check namespaces before translation erases them; source quotes are not references."""
    if isinstance(value, dict):
        for key, item in value.items():
            if key not in ("quote", "problem_text", "solid") and not key.endswith("_id"):
                if key == 'container_ref' and isinstance(item, str) and '::' in item:
                    sid, chain = item.split('::', 1)
                    try:
                        refs = [f'{sid}::{label}' for label in split_vertex_chain(chain)]
                    except TypedFactNextValidationError as e:
                        raise TuChoi(e.code, e.detail) from None
                    _check_qualified_refs(refs, solids, owned)
                    continue
                if key == "named_intersections":
                    for edge in item:
                        _check_qualified_refs(edge.split("-"), solids, owned)
                _check_qualified_refs(item, solids, owned)
    elif isinstance(value, (list, tuple)):
        for item in value:
            _check_qualified_refs(item, solids, owned)
    elif isinstance(value, str) and "::" in value:
        try:
            sid, label = parse_qualified_ref(value)
        except TypedFactNextValidationError as e:
            raise TuChoi(e.code, e.detail) from None
        if sid not in solids:
            raise TuChoi("UNKNOWN_SOLID_ID", f"tham chiếu tới khối chưa khai {sid!r}")
        if label not in solids[sid].local_vertices() and sid not in (owned or {}).get(label, set()):
            raise TuChoi("UNKNOWN_VERTEX_REF", f"{value!r} không phải đỉnh của khối đã khai")


def _kiem_pham_vi_tien_de(p: TypedFactNextPayload, solids: dict[str, Any]) -> list[dict[str, Any]]:
    """Prove single-solid premise ownership before translation erases scope; never default an explicit scope."""
    import re
    from .registry import chuan_hoa

    owners: dict[str, set[str]] = {}
    vertices: dict[str, set[str]] = {}
    for sid, solid in solids.items():
        for label in solid.local_vertices():
            owners.setdefault(label, set()).add(sid)
            vertices.setdefault(label, set()).add(sid)
    outputs = {"midpoint":"point", "point_is_midpoint":"point", "divide_segment":"point",
               "point_divides_segment":"point", "centroid":"point", "point_is_centroid":"point",
               "intersect_line_line":"point", "intersect_line_plane":"point",
               "orthogonal_projection":"image", "point_is_foot":"image", "orthogonal_projection_line":"image"}
    new_names = {_ref(prem.args[outputs[prem.kind]]) for prem in p.premises
                 if prem.kind in outputs and outputs[prem.kind] in prem.args}
    shared_faces = set()
    for relation in p.relations:
        if (relation.kind == 'shared_faces' and relation.solid_a in solids and relation.solid_b in solids
                and _refs(relation.face_a) == _refs(relation.face_b)
                and set(_refs(relation.face_a)) <= set(solids[relation.solid_a].local_vertices())
                and set(_refs(relation.face_b)) <= set(solids[relation.solid_b].local_vertices())
                and chuan_hoa(relation.quote) in chuan_hoa(p.problem_text)):
            shared_faces.add(frozenset((relation.solid_a, relation.solid_b)))
    records = []
    for i, prem in enumerate(p.premises, 1):
        fid = f"p{i}"
        sid = prem.solid_id
        if sid is not None and sid not in solids:
            raise TuChoi("UNKNOWN_SOLID_ID", f"{fid}: phạm vi khối {sid!r} chưa được khai báo", (fid,))
        if (named := prem.args.get('solid')) is not None:
            resolved = [s for s, solid in solids.items() if named in (s, solid.notation)]
            if len(resolved) != 1:
                raise TuChoi("UNKNOWN_SOLID_ID", f"{fid}: khối {named!r} không xác định duy nhất", (fid,))
            if sid is not None and sid != resolved[0]:
                raise TuChoi("SOURCE_OBJECT_MISMATCH", f"{fid}: khối trong toán hạng khác phạm vi premise", (fid,))
            sid = resolved[0]
        # Reuse the schema's typed reference fields, not arbitrary strings or *_id keys.
        schema = _ARGS_LOI.get(prem.kind, {})
        if prem.kind in ('right_angle','base_is_right_triangle'):
            schema = next(s for s in _ARGS_GOC_VUONG if set(prem.args) <= set(s))
        refs = [(key, ref) for key, shape in schema.items() if shape.startswith('ref') and key in prem.args
                for ref in (prem.args[key] if shape.startswith('refs') else [prem.args[key]])]
        for _key, ref in refs:
            explicit, label = parse_qualified_ref(ref)
            if explicit is not None and explicit not in solids:
                raise TuChoi('UNKNOWN_SOLID_ID', f'{fid}: khối {explicit!r} chưa được khai báo', (fid,))
            if explicit is not None and sid is not None and explicit != sid:
                raise TuChoi('SOURCE_OBJECT_MISMATCH', f'{fid}: toán hạng có scope khác premise', (fid,))
            if explicit is not None and label not in vertices and label not in new_names:
                raise TuChoi('UNKNOWN_VERTEX_REF', f'{fid}: tham chiếu {ref!r} không được khai báo', (fid,))
        records.append((prem, fid, sid, refs))
    for sec in p.derived_sections:
        for cut in getattr(sec, 'stated_intersections', ()):
            if cut.point and all(sec.target_solid_id in owners.get(_ref(x), set()) for x in cut.edge):
                owners.setdefault(cut.point, set()).add(sec.target_solid_id)

    def common(refs):
        sets = [owners.get(_ref(ref), set()) & ({parse_qualified_ref(ref)[0]} if '::' in ref else set(solids))
                for _key, ref in refs]
        return set.intersection(*sets) if sets else set()

    # Dependency order may differ from source order; a scope never manufactures an operand's ownership.
    for _ in range(len(records) + 1):
        changed = False
        for prem, _fid, sid, refs in records:
            output = outputs.get(prem.kind)
            if not output:
                continue
            candidates = common([(key, ref) for key, ref in refs if key != output])
            if sid is not None:
                candidates &= {sid}
            label = _ref(prem.args[output])
            if label in vertices:
                # A shared-face subsolid may name a point constructed on its parent's edge (e.g. a midpoint).
                # A projection's existing foreign foot is not a fresh point definition.
                candidates = {s for s in candidates if s in vertices[label] or output == 'point'
                              and any(frozenset((s, other)) in shared_faces for other in vertices[label])}
            before = set(owners.get(label, set()))
            owners.setdefault(label, set()).update(candidates)
            changed |= before != owners[label]
        if not changed:
            break
    checked = []
    for prem, fid, sid, refs in records:
        candidates = common(refs)
        known = [owners.get(_ref(ref), set()) for _key, ref in refs if owners.get(_ref(ref))]
        if sid is not None and any(sid not in owners.get(_ref(ref), set()) for _key, ref in refs):
            raise TuChoi('SOURCE_OBJECT_MISMATCH', f'{fid}: toán hạng/điểm dựng không thuộc phạm vi {sid!r}', (fid,))
        if sid is None and known and not set.intersection(*known):
            raise TuChoi('SOURCE_OBJECT_MISMATCH', f'{fid}: premise trộn thực thể của nhiều khối', (fid,))
        if sid is None and len(candidates) > 1:
            named = {s for s in candidates if re.search(rf"(?<![\w']){re.escape(solids[s].notation)}(?![\w'])",
                                                       chuan_hoa(prem.quote))}
            if len(named) != 1:
                raise TuChoi('AMBIGUOUS_REFERENCE', f'{fid}: thiếu phạm vi khối không mơ hồ', (fid,))
            candidates = named
        checked.append({'premise_id':fid,'declared_solid_id':prem.solid_id,'resolved_solid_ids':sorted({sid} if sid else candidates),
                        'vertices':sorted({_ref(ref) for _key, ref in refs}),'quote':prem.quote})
    return checked


def _operand(t: dict[str, Any], key: str, n: int) -> list[str] | None:
    """DISTINCT labels of one goal operand: a line / segment exactly two, a plane (n = 3) three or more — a face may be
    named by all its vertices, (ABCD), as premises already may. Every plane label reaches the engine, which checks they
    are coplanar and that the three it measures with are not collinear (`kiem_mat_viet`). A repeated label is degenerate."""
    v = t.get(key)
    refs = _refs(v) if isinstance(v, (list, tuple)) and (len(v) >= n if n == 3 else len(v) == n) else None
    return refs if refs is not None and len(set(refs)) == len(refs) else None


def _distance_question(g) -> dict[str, Any]:
    """`/2` distance target → the planner's existing question. Keys are exactly those the `/3` adapter already reads
    (`{point, plane}`, `{segment}`, `{line1, line2}`); anything else is refused, never guessed."""
    t = g.target
    pts = partial(_operand, t)
    if set(t) == {"point", "plane"} and isinstance(t["point"], str) and (pl := pts("plane", 3)):
        return {"quantity": "distance", "points_a": [_ref(t["point"])], "points_b": pl}
    if set(t) == {"segment"} and (seg := pts("segment", 2)):
        return {"quantity": "length", "points": seg}
    if set(t) == {"line1", "line2"} and (l1 := pts("line1", 2)) and (l2 := pts("line2", 2)):
        return {"quantity": "distance", "points_a": l1, "points_b": l2}
    # `{line, plane}` / `{plane1, plane2}` (run `hybrid-v2-nl-certificates-e2e`): the kernel measures both exactly (0 when
    # they meet). Same arity rule: a line is exactly two labels, a plane three or more.
    if set(t) == {"line", "plane"} and (ln := pts("line", 2)) and (pl := pts("plane", 3)):
        return {"quantity": "distance", "points_a": ln, "points_b": pl}
    if set(t) == {"plane1", "plane2"} and (p1 := pts("plane1", 3)) and (p2 := pts("plane2", 3)):
        return {"quantity": "distance", "points_a": p1, "points_b": p2}
    # `{point, line}` (run `hybrid-v2-backend-generalization`): the planner's point–line decomposition — the foot is built
    # on a fresh auxiliary label (`orthogonal_projection_line`) and checked by the engine; nothing is named here.
    if set(t) == {"point", "line"} and isinstance(t["point"], str) and (ln := pts("line", 2)):
        return {"quantity": "distance", "points_a": [_ref(t["point"])], "points_b": ln}
    raise TuChoi("INVALID_MATH_GOAL", f"{g.goal_id}: mục tiêu distance thiếu toán hạng hợp lệ", (g.goal_id,))


def _angle_question(g) -> dict[str, Any]:
    """`/2` angle target → the planner's existing angle question (answer: cos² — exact). Keys are those `/3` reads
    (`{line, plane}`, `{line1, line2}`) plus `{plane1, plane2}` for the dihedral question the planner already has. Same
    arity rule as distance (`_operand`): a line is exactly two distinct labels, a plane three or more — never truncated."""
    t = g.target
    pts = partial(_operand, t)
    if set(t) == {"line", "plane"} and (ln := pts("line", 2)) and (pl := pts("plane", 3)):
        return {"quantity": "angle", "points_a": ln, "points_b": pl}
    if set(t) == {"line1", "line2"} and (l1 := pts("line1", 2)) and (l2 := pts("line2", 2)):
        return {"quantity": "angle", "points_a": l1, "points_b": l2}
    if set(t) == {"plane1", "plane2"} and (p1 := pts("plane1", 3)) and (p2 := pts("plane2", 3)):
        return {"quantity": "angle", "points_a": p1, "points_b": p2}
    raise TuChoi("INVALID_MATH_GOAL", f"{g.goal_id}: mục tiêu angle thiếu toán hạng hợp lệ", (g.goal_id,))


def _mat_fact(sec: DerivedPlaneSectionSpec | DerivedPlaneSectionSpecV2, solids: dict[str, Any],
              asked: list[str]) -> dict[str, Any]:
    """The section fact's PLANE (shared by `/1` and `/2`)."""
    rel = _PLANE_RELATION.get(sec.plane_kind)
    if rel is None:
        raise TuChoi("BRIDGE_UNSUPPORTED_PLANE_KIND", f"{sec.section_id}: mặt {sec.plane_kind} chưa có phép dựng của planner",
                     (sec.section_id,))
    f: dict[str, Any] = {"id": sec.section_id, "kind": "section", "role": "question" if asked else "premise",
                         "quotes": [sec.quote, *asked], "solid": solids[sec.target_solid_id].notation,
                         "point": _ref(sec.through_point), "plane_relation": rel}
    if getattr(sec, "plane_name", None) is not None:
        import re as _re
        if not _re.fullmatch(r"(?:[A-Z][0-9]*'?|[α-ω]'?)", str(sec.plane_name)):
            raise TuChoi("SOURCE_OBJECT_MISMATCH", f"{sec.section_id}: tên mặt đã khai không khớp mặt được Source Gate xác minh", (sec.section_id,))
        f["plane_name"] = sec.plane_name
    if rel == "parallel":
        f["points_b"] = _refs(sec.parallel_plane)
    elif rel == "perpendicular":
        f["points_b"] = _refs(sec.perpendicular_line)
    else:
        f.update(points_a=_refs(sec.parallel_line_a), points_b=_refs(sec.parallel_line_b), plane_name=sec.plane_name)
    return f


def _v2_plane_def_quotes(sec: DerivedPlaneSectionSpec | DerivedPlaneSectionSpecV2, problem_text: str | None) -> list[str]:
    """When a `/2` section carries a declared `plane_name` whose definition is in a separate declarative source sentence
    from `sec.quote`, include that unique source sentence in the section fact's quotes so the Source Gate verifies both."""
    ten = getattr(sec, "plane_name", None)
    if not problem_text or not ten:
        return []
    import re
    from .registry import (
        _DIEM_TRUOC_HAI_DUONG,
        _DIEM_TRUOC_SONG_SONG,
        _DIEM_TRUOC_VUONG_DUONG,
        _QUA_HAI_DUONG,
        _QUA_SONG_SONG,
        _QUA_VUONG_DUONG,
        _bien_cau,
        chuan_hoa,
    )
    cac_mau = (_QUA_SONG_SONG, _DIEM_TRUOC_SONG_SONG, _QUA_VUONG_DUONG, _DIEM_TRUOC_VUONG_DUONG,
               _QUA_HAI_DUONG, _DIEM_TRUOC_HAI_DUONG)
    qn = chuan_hoa(sec.quote)
    if any(m["ten"] == ten for mau in cac_mau for m in mau.finditer(qn)):
        return []
    de = chuan_hoa(problem_text)
    cands: list[str] = []
    seen_spans: set[tuple[int, int]] = set()
    for mau in cac_mau:
        for m in mau.finditer(de):
            if m["ten"] != ten:
                continue
            cs, ce = _bien_cau(de, m.start())
            if (cs, ce) in seen_spans:
                continue
            sent = de[cs:ce].strip()
            if re.match(r"^\s*(?:hãy\s+)?dựng", sent, re.IGNORECASE):
                continue
            seen_spans.add((cs, ce))
            cands.append(sent)
    return [cands[0]] if len(cands) == 1 else []


def _section_fact_v2(sec: DerivedPlaneSectionSpecV2, solids: dict[str, Any], asked: list[str],
                     problem_text: str | None = None) -> dict[str, Any]:
    """`/2`: stated intersections are the stated cuts (names aligned, None = stated but unnamed); the planner may derive
    the vertex of an UNSTATED lateral edge where a closed boundary is required (D6); a declared boundary is verified."""
    f = _mat_fact(sec, solids, asked)
    if extra := _v2_plane_def_quotes(sec, problem_text):
        f["quotes"] = list(dict.fromkeys([*extra, *f["quotes"]]))
    f["cut_edges"] = [_refs(s.edge) for s in sec.stated_intersections]
    if any(s.point for s in sec.stated_intersections):
        f["cut_points"] = [s.point for s in sec.stated_intersections]
    f["derive_cuts"] = True
    if sec.declared_boundary is not None:
        f["boundary_edges"] = [_refs(e) for e in sec.declared_boundary]
    return f


def _section_fact(sec: DerivedPlaneSectionSpec, solids: dict[str, Any], asked: list[str]) -> dict[str, Any]:
    f = _mat_fact(sec, solids, asked)
    edges = [tuple(_refs(e)) for e in sec.cut_edges]
    named = {frozenset(_refs(k.split("-"))): v for k, v in sec.named_intersections.items()}
    if not edges and named:                              # the names the payload gives define the stated cuts, in its order
        edges = [tuple(_refs(k.split("-"))) for k in sec.named_intersections]
    if lac := [k for k in named if k not in {frozenset(e) for e in edges}]:
        raise TuChoi("BRIDGE_INCONSISTENT_SECTION", f"{sec.section_id}: giao điểm có tên trên cạnh không bị nêu là cắt {lac}",
                     (sec.section_id,))
    if edges:
        f["cut_edges"] = [list(e) for e in edges]
        if named:
            f["cut_points"] = [named.get(frozenset(e)) for e in edges]
    return f


def bridge(raw: dict[str, Any] | TypedFactNextPayload) -> dict[str, Any]:
    """`/1` → `{"facts": [...], "bridge": {...}}` for the planner, or `TuChoi` (typed, fail-closed)."""
    try:
        p = parse_typed_fact_next(raw)
    except TypedFactNextValidationError as e:
        raise TuChoi(e.code, e.detail) from None
    return _bridge(p, _section_fact, BRIDGE_VERSION, v2=False)


def bridge_v2(raw: dict[str, Any]) -> dict[str, Any]:
    """`typed-fact-next/2` → planner facts (run `hybrid-contract-v2`). The same pure translation as `/1` except sections."""
    try:
        p = parse_typed_fact_next_v2(raw)
    except TypedFactNextValidationError as e:
        raise TuChoi(e.code, e.detail) from None
    return _bridge(p, _section_fact_v2, BRIDGE_V2_VERSION, v2=True)


def _bridge(p: TypedFactNextPayload, section_fact, version: str, v2: bool) -> dict[str, Any]:
    facts: list[dict[str, Any]] = []
    solids = {s.solid_id: s for s in p.solids}
    for s in p.solids:
        if s.solid_type not in ("pyramid", "prism"):
            raise TuChoi("BRIDGE_UNSUPPORTED_CURVED", f"{s.solid_id}: khối {s.solid_type} chưa có trên planner", (s.solid_id,))
        if any(a != b for a, b in s.vertex_bindings.items()) or s.coordinate_frame_id != "root":
            raise TuChoi("BRIDGE_UNSUPPORTED_QUALIFIED_IDENTITY", f"{s.solid_id}: hai điểm khác nhau mang cùng nhãn — TypedFact "
                         "định danh điểm bằng nhãn", (s.solid_id,))
        facts.append({"id": s.solid_id, "kind": "solid", "role": "premise", "quotes": [s.quote], "solid": s.notation,
                      "solid_type": s.solid_type})
    scoped = _kiem_pham_vi_tien_de(p, solids)
    owned: dict[str, set[str]] = {}
    for record in scoped:
        for label in record['vertices']:
            owned.setdefault(label, set()).update(record['resolved_solid_ids'])
    _check_qualified_refs(p.model_dump(), solids, owned)
    theo_ten = {s.notation: f for s, f in zip(p.solids, facts)}

    for i, prem in enumerate(p.premises, 1):
        a, k, fid, q = prem.args, prem.kind, f"p{i}", [prem.quote]
        if k in ("regular_pyramid", "right_prism"):
            ten = f"{_ref(a['apex'])}.{''.join(_refs(a['base']))}" if k == "regular_pyramid" else \
                f"{''.join(_refs(a['base']))}.{''.join(_refs(a['top']))}"
            if ten not in theo_ten:
                raise TuChoi("UNKNOWN_SOLID", f"{fid}: {ten} không phải khối đã khai", (fid,))
            theo_ten[ten].update({"regular" if k == "regular_pyramid" else "right": True})
            theo_ten[ten]["quotes"] = [*theo_ten[ten]["quotes"], prem.quote]
            continue
        if k in ("regular_polygon", "base_is_square", "base_is_equilateral_triangle", "base_is_regular_polygon"):
            v = _refs(a["vertices"])
            f = {"kind": "polygon_shape", "points": v, "shape": _REGULAR_SHAPE.get(len(v), "regular_polygon")}
            if a.get("side") is not None:
                f["value"] = str(a["side"])
        elif k in ("rectangle", "base_is_rectangle"):
            f = {"kind": "polygon_shape", "points": _refs(a["vertices"]), "shape": "rectangle"}
        elif k in ("right_angle", "base_is_right_triangle"):
            at = _ref(a["right_at"] if "vertices" in a else a["vertex"])
            f = {"kind": "right_angle", "at": at,
                 "points": [x for x in _refs(a["vertices"]) if x != at] if "vertices" in a else _refs(a["rays"])}
        elif k == "segment_length":
            f = {"kind": "length", "measure": "segment", "points": _refs(a["segment"]), "value": str(a["value"])}
        elif k == "height":
            sid = a.get("solid") or prem.solid_id
            sol = solids.get(sid or "")
            if sol is None and sid is None and len(solids) == 1:
                sol = next(iter(solids.values()))
            f = {"kind": "length", "measure": "height", "solid": sol.notation if sol else sid,
                 "value": str(a["value"])}
        elif k in ("equal_length", "equal_segments"):
            f = {"kind": "equal_lengths", "points_a": _refs(a["segment_a"]), "points_b": _refs(a["segment_b"])}
        elif k in ("perpendicular_line_plane", "line_perp_plane"):
            f = {"kind": "perpendicular", "points_a": _refs(a["line"]), "points_b": _refs(a["plane"])}
        elif k in ("perpendicular_lines", "line_perp_line"):
            f = {"kind": "perpendicular", "points_a": _refs(a["line1"]), "points_b": _refs(a["line2"])}
        elif k in ("face_perpendicular_base", "plane_perp_base"):
            f = {"kind": "perpendicular", "points_a": _refs(a["face"]), "points_b": _refs(a["base"])}
        elif k == "altitude":
            sid = a.get("solid") or prem.solid_id
            sol = solids.get(sid or "")
            if sol is None and sid is None and len(solids) == 1:
                sol = next(iter(solids.values()))
            f = {"kind": "altitude", "points": [_ref(a["apex"]), _ref(a["foot"])],
                 "solid": sol.notation if sol else sid}
        elif k in ("midpoint", "point_is_midpoint"):
            f = {"kind": "point_def", "point_kind": "midpoint", "point": _ref(a["point"]), "points": _refs(a["segment"])}
        elif k in ("divide_segment", "point_divides_segment"):
            f = {"kind": "point_def", "point_kind": "divide_segment", "point": _ref(a["point"]),
                 "points": _refs(a["segment"]), "value": str(a["ratio"])}
        elif k in ("centroid", "point_is_centroid"):
            f = {"kind": "point_def", "point_kind": "centroid", "point": _ref(a["point"]), "points": _refs(a["polygon"])}
        elif k in ("orthogonal_projection", "point_is_foot"):
            f = {"kind": "projection", "point": _ref(a["point"]), "points": _refs(a["plane"]), "at": _ref(a["image"])}
        elif k == "orthogonal_projection_line":
            f = {"kind": "projection", "point": _ref(a["point"]), "points": _refs(a["line"]), "at": _ref(a["image"])}
        elif k == "intersect_line_line":
            f = {"kind": "point_def", "point_kind": "intersect_line_line", "point": _ref(a["point"]),
                 "points_a": _refs(a["line1"]), "points_b": _refs(a["line2"])}
        elif k == "intersect_line_plane":
            f = {"kind": "point_def", "point_kind": "intersect_line_plane", "point": _ref(a["point"]),
                 "points_a": _refs(a["line"]), "points_b": _refs(a["plane"])}
        else:
            raise TuChoi("BRIDGE_UNSUPPORTED_PREMISE", f"{fid}: giả thiết {k!r} chưa có ánh xạ sang TypedFact", (fid,))
        facts.append({"id": fid, "role": "premise", "quotes": q, **f})

    for r in p.relations:
        if r.kind == "coordinate_frame" and r.frame_id == "root":
            continue                                       # one root chart is what TypedFact always uses
        if r.kind == "perpendicular":
            facts.append({"id": r.relation_id, "kind": "perpendicular", "role": "premise", "quotes": [r.quote],
                          "points_a": _refs(r.entity_a), "points_b": _refs(r.entity_b)})
            continue
        if r.kind == "shared_vertices" and all(_ref(x) == _ref(y) for x, y in r.pairs):
            continue                                       # identity bindings: shared labels ARE the shared points
        if r.kind == "shared_faces" and _refs(r.face_a) == _refs(r.face_b):
            continue
        raise TuChoi("BRIDGE_UNSUPPORTED_RELATION", f"{r.relation_id}: quan hệ {r.kind} chưa diễn đạt được trong TypedFact",
                     (r.relation_id,))

    asked = {}
    for g in p.simulation_goals:
        if g.kind == "construct_plane_section":
            asked.setdefault(g.target_section_id, []).append(g.quote)
    for sec in p.derived_sections:
        facts.append(
            section_fact(sec, solids, asked.get(sec.section_id, []), p.problem_text)
            if v2 else section_fact(sec, solids, asked.get(sec.section_id, []))
        )

    derived = {}
    for g in p.simulation_goals:
        if g.kind != "construct_derived_solid":
            continue
        parent = solids.get(g.parent_solid_id or next(s.target_solid_id for s in p.derived_sections
                                                      if s.section_id == g.target_section_id))
        if parent is None or parent.solid_type != "pyramid":
            raise TuChoi("BRIDGE_UNSUPPORTED_DERIVED_SOLID", f"{g.goal_id}: khối dựng trên thiết diện chỉ cho hình chóp",
                         (g.goal_id,))
        sec = next((s for s in p.derived_sections if s.section_id == g.target_section_id), None)
        if sec is None or not (v2 or sec.cut_edges or sec.named_intersections):     # `/2`: unstated cuts may be derived
            raise TuChoi("BRIDGE_CUT_EDGES_NOT_STATED", f"{g.goal_id}: thiết diện {g.target_section_id} không nêu các cạnh bị "
                         "cắt — bridge không suy ra cạnh nào bị cắt", (g.goal_id,))
        derived[g.derived_solid_id] = g.goal_id
        facts.append({"id": g.goal_id, "kind": "solid", "role": "question", "quotes": [g.quote], "solid_type": "pyramid",
                      "point": _ref(g.apex_ref), "plane_ref": g.target_section_id})

    def solid_fact(sid: str | None, gid: str) -> str:
        if sid in derived:
            return derived[sid]
        if sid in solids:
            return sid
        raise TuChoi("UNKNOWN_SOLID_ID", f"{gid}: khối {sid!r} không có", (gid,))

    for g in p.math_goals:
        q = {"id": g.goal_id, "kind": "question", "role": "question", "quotes": [g.quote]}
        if g.kind == "volume_ratio":
            facts.append({**q, "quantity": "volume_ratio",
                          "solid_refs": [solid_fact(g.numerator_solid_id, g.goal_id), solid_fact(g.denominator_solid_id, g.goal_id)]})
        elif g.kind == "residual_volume":
            facts.append({**q, "quantity": "residual_volume",
                          "solid_refs": [solid_fact(g.parent_solid_id, g.goal_id), solid_fact(g.cut_solid_id, g.goal_id)]})
        elif g.goal_type == "volume" and (g.target.get("solid") or g.solid_id) in solids:
            facts.append({**q, "quantity": "volume", "solid": solids[g.target.get("solid") or g.solid_id].notation})
        elif g.goal_type == "area" and "section_id" in g.target:
            sec = next((s for s in p.derived_sections if s.section_id == g.target["section_id"]), None)
            if sec is None:
                raise TuChoi("INVALID_MATH_GOAL", f"{g.goal_id}: thiết diện {g.target['section_id']!r} không có trong dữ kiện", (g.goal_id,))
            g_solid = g.solid_id or g.target.get("solid_id") or g.target.get("solid")
            if g_solid is not None:
                if g_solid not in solids:
                    raise TuChoi("UNKNOWN_SOLID_ID", f"{g.goal_id}: khối {g_solid!r} không có", (g.goal_id,))
                if g_solid != sec.target_solid_id:
                    raise TuChoi("SOURCE_OBJECT_MISMATCH", f"{g.goal_id}: khối {g_solid!r} không khớp khối của thiết diện {sec.section_id!r}", (g.goal_id,))
            f = _mat_fact(sec, solids, [])
            facts.append({**q, "quantity": "area", **{k: f[k] for k in ("solid", "point", "plane_relation", "points_b",
                                                                         "points_a", "plane_name") if k in f}})
        elif v2 and g.goal_type == "distance":
            facts.append({**q, **_distance_question(g)})
        elif v2 and g.goal_type == "angle":
            facts.append({**q, **_angle_question(g)})
        else:
            raise TuChoi("BRIDGE_UNSUPPORTED_MEASUREMENT", f"{g.goal_id}: mục tiêu {g.kind}/{g.goal_type} chưa có ánh xạ",
                         (g.goal_id,))
    khong = [g.goal_id for g in p.simulation_goals if g.kind in _NO_NEW_FACT_GOALS]
    return {"facts": facts, "bridge": {"version": version, "goals_without_new_facts": khong,
                                       "scope_validation_version": "typed-fact-next-scope/1",
                                       "validated_premise_scopes": scoped,
                                       "declared_length_unit": p.length_unit,
                                       "declared_plane_names": {s.section_id: s.plane_name for s in p.derived_sections},
                                       "problem_text": p.problem_text}}
