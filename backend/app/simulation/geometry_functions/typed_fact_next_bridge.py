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
    CONSTRUCTED_OUTPUTS,
    DESCRIBED_GOAL_KEYS,
    DESCRIBED_POINT_FIELDS,
    is_described_ref,
    canonical_vertex_ref,
    clarification_record,
    measurement_scope,
    _derived_parents,
    resolve_solid_name,
    scope_records,
    split_edge_key,
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
                        _check_qualified_refs(split_edge_key(edge), solids, owned)
                _check_qualified_refs(item, solids, owned)
    elif isinstance(value, (list, tuple)):
        for item in value:
            _check_qualified_refs(item, solids, owned)
    elif isinstance(value, str) and "::" in value:
        try:
            sid, label = parse_qualified_ref(value)
        except TypedFactNextValidationError as e:
            raise TuChoi(e.code, e.detail) from None
        if sid not in solids and not any(sid in scopes for scopes in (owned or {}).values()):
            raise TuChoi("UNKNOWN_SOLID_ID", f"tham chiếu tới khối chưa khai {sid!r}")
        canonical = solids[sid].canonical_vertex(label) if sid in solids else label
        if (sid not in solids or label not in solids[sid].local_vertices()) and sid not in (owned or {}).get(canonical, set()):
            raise TuChoi("UNKNOWN_VERTEX_REF", f"{value!r} không phải đỉnh của khối đã khai")


def _pham_vi_khoi(named: Any, sid: str | None, solids: dict[str, Any], fid: str) -> str | None:
    """A solid-valued operand (id or notation) never overrides a declared scope; an explicit scope must exist."""
    if sid is not None and sid not in solids:
        raise TuChoi("UNKNOWN_SOLID_ID", f"{fid}: phạm vi khối {sid!r} chưa được khai báo", (fid,))
    if named is None:
        return sid
    resolved = [s for s, solid in solids.items() if named in (s, solid.notation)]
    if named == "()" and len(resolved) > 1 and sid is not None:
        if sid not in resolved:
            raise TuChoi("SOURCE_OBJECT_MISMATCH", f"{fid}: khối trong toán hạng khác phạm vi đã khai", (fid,))
        return sid
    if len(resolved) != 1:
        if sid is None:     # no scope claim to contradict: the planner refuses the unknown solid (locked UNKNOWN_SOLID)
            return None
        raise TuChoi("UNKNOWN_SOLID_ID", f"{fid}: khối {named!r} không xác định duy nhất", (fid,))
    if sid is not None and sid != resolved[0]:
        raise TuChoi("SOURCE_OBJECT_MISMATCH", f"{fid}: khối trong toán hạng khác phạm vi đã khai", (fid,))
    return resolved[0]


def _kiem_pham_vi_tien_de(p: TypedFactNextPayload, solids: dict[str, Any]) -> list[dict[str, Any]]:
    """Prove single-solid premise ownership before translation erases scope; never default an explicit scope."""
    import re
    from .registry import chuan_hoa

    owners: dict[str, set[str]] = {}
    vertices: dict[str, set[str]] = {}
    for sid, solid in solids.items():
        for local in solid.local_vertices():
            label = solid.canonical_vertex(local)
            owners.setdefault(label, set()).add(sid)
            vertices.setdefault(label, set()).add(sid)

    def identity(ref, scope=None):
        try:
            return canonical_vertex_ref(p, ref, scope)
        except TypedFactNextValidationError as e:
            raise TuChoi(e.code, e.detail) from None

    desc_by_id = {d.described_id: d for d in getattr(p, "described_points", ())}

    def _desc_leaf_refs(ref: str, seen: set[str] | None = None) -> list[str]:
        if not is_described_ref(ref):
            return [ref]
        did = ref.strip()[1:]
        d = desc_by_id.get(did)
        if d is None or (seen and did in seen):
            return []
        nxt_seen = (seen or set()) | {did}
        raw = [*d.point_operands(), *(d.plane or ()), *(d.polygon or ())]
        return [leaf for x in raw for leaf in _desc_leaf_refs(x, nxt_seen)]

    def ref_owners(ref, scope=None):
        if is_described_ref(ref):
            leaf_sets = [owners.get(identity(leaf, scope), set()) for leaf in _desc_leaf_refs(ref)]
            return set.intersection(*leaf_sets) if leaf_sets and all(leaf_sets) else set()
        return owners.get(identity(ref, scope), set())
    outputs = CONSTRUCTED_OUTPUTS
    new_names = {_ref(prem.args[outputs[prem.kind]]) for prem in p.premises
                 if prem.kind in outputs and isinstance(prem.args.get(outputs[prem.kind]), str)
                 and not is_described_ref(prem.args[outputs[prem.kind]])}
    # A secondary vertex-subset pyramid (`B'.ACC'A'`, `A'.ABC`, `O.MNP`, `M.ABC`) borrows vertices/outputs from its host solid.
    host_vertex_sets = {
        sid: ({s.canonical_vertex(v) for v in s.local_vertices()} | new_names)
        for sid, s in solids.items()
    }
    solid_local_canon = {sid: {s.canonical_vertex(v) for v in s.local_vertices()} for sid, s in solids.items()}
    derived_subsolids = {
        sid for sid, s in solids.items()
        if s.solid_type == "pyramid" and any(
            h_sid != sid
            and solid_local_canon[sid] <= host_vertex_sets[h_sid]
            and (
                solids[h_sid].solid_type != "pyramid"
                or len(solid_local_canon[h_sid]) > len(solid_local_canon[sid])
                or (bool(solid_local_canon[sid] & new_names) and not (solid_local_canon[h_sid] & new_names))
            )
            for h_sid in solids
        )
    }
    anchored_spheres: dict[str, str] = {}
    for sid, s in solids.items():
        host = s.circumscribes or getattr(s, "inscribed_in", None)
        if host in solids:
            anchored_spheres[sid] = host
    for relation in p.relations:
        if relation.kind in ("circumscribes", "inscribed_in") and relation.solid_a in solids and relation.solid_b in solids:
            anchored_spheres[relation.solid_a] = relation.solid_b
    for sph_id, host_id in anchored_spheres.items():
        if solids[sph_id].center:
            owners.setdefault(solids[sph_id].canonical_vertex(solids[sph_id].center), set()).add(host_id)
    shared_faces = set()
    for relation in p.relations:
        if (relation.kind == 'shared_faces' and relation.solid_a in solids and relation.solid_b in solids
                and _refs(relation.face_a) == _refs(relation.face_b)
                and set(_refs(relation.face_a)) <= set(solids[relation.solid_a].local_vertices())
                and set(_refs(relation.face_b)) <= set(solids[relation.solid_b].local_vertices())
                and chuan_hoa(relation.quote) in chuan_hoa(p.problem_text)):
            shared_faces.add(frozenset((relation.solid_a, relation.solid_b)))
    circumscribed = {frozenset((sph_id, host_id)) for sph_id, host_id in anchored_spheres.items()}
    records = []
    for i, prem in enumerate(p.premises, 1):
        fid = f"p{i}"
        sid = _pham_vi_khoi(prem.args.get('solid'), prem.solid_id, solids, fid)
        # Reuse the schema's typed reference fields, not arbitrary strings or *_id keys.
        schema = _ARGS_LOI.get(prem.kind, {})
        if prem.kind in ('right_angle','base_is_right_triangle'):
            schema = next(s for s in _ARGS_GOC_VUONG if set(prem.args) <= set(s))
        refs = [(key, ref) for key, shape in schema.items() if shape.startswith('ref') and key in prem.args
                for ref in (prem.args[key] if shape.startswith('refs') else [prem.args[key]])]
        for _key, ref in refs:
            if is_described_ref(ref):
                continue
            explicit, label = parse_qualified_ref(ref)
            if explicit is not None and explicit not in solids:
                raise TuChoi('UNKNOWN_SOLID_ID', f'{fid}: khối {explicit!r} chưa được khai báo', (fid,))
            if explicit is not None and sid is not None and explicit != sid:
                raise TuChoi('SOURCE_OBJECT_MISMATCH', f'{fid}: toán hạng có scope khác premise', (fid,))
            if explicit is not None and identity(ref, sid) not in vertices and label not in new_names:
                raise TuChoi('UNKNOWN_VERTEX_REF', f'{fid}: tham chiếu {ref!r} không được khai báo', (fid,))
        records.append((prem, fid, sid, refs))
    for sec in p.derived_sections:
        for cut in getattr(sec, 'stated_intersections', ()):
            if cut.point and all(sec.target_solid_id in ref_owners(x, sec.target_solid_id) for x in cut.edge):
                owners.setdefault(identity(cut.point, sec.target_solid_id), set()).add(sec.target_solid_id)

        for edge, point in getattr(sec, 'named_intersections', {}).items():
            if all(sec.target_solid_id in ref_owners(x, sec.target_solid_id) for x in split_edge_key(edge)):
                owners.setdefault(identity(point, sec.target_solid_id), set()).add(sec.target_solid_id)

    def common(refs, scope=None):
        sets = [ref_owners(ref, scope) & ({parse_qualified_ref(ref)[0]} if '::' in ref else set(solids))
                for _key, ref in refs]
        return set.intersection(*sets) if sets else set()

    # Dependency order may differ from source order; a scope never manufactures an operand's ownership.
    for _ in range(len(records) + len(p.relations) + 1):
        changed = False
        for prem, _fid, sid, refs in records:
            output = outputs.get(prem.kind)
            if not output or not isinstance(prem.args.get(output), str) or is_described_ref(prem.args[output]):
                continue
            candidates = common([(key, ref) for key, ref in refs if key != output], sid)
            if sid is not None:
                candidates &= {sid}
            label = identity(prem.args[output], sid)
            if label in vertices:
                # A shared-face or derived vertex-subset subsolid may name a point constructed on its parent solid.
                # An existing foreign vertex is only reused for a fresh host output when the foreign vertex lives solely on derived subsolids.
                candidates = {
                    s for s in candidates
                    if s in vertices[label]
                    or (vertices[label] <= derived_subsolids and s not in derived_subsolids)
                    or (output == 'point' and any(frozenset((s, other)) in (shared_faces | circumscribed) for other in vertices[label]))
                }
            before = set(owners.get(label, set()))
            owners.setdefault(label, set()).update(candidates)
            changed |= before != owners[label]
        for rel in p.relations:
            if (
                rel.kind == "tangent_to"
                and getattr(rel, "contact_ref", None)
                and rel.solid_b in solids
                and all(rel.solid_b in ref_owners(x, rel.solid_b) for x in rel.entity_b)
            ):
                c_ns, _ = parse_qualified_ref(rel.contact_ref)
                if c_ns is not None and c_ns != rel.solid_b:
                    continue
                c_lbl = identity(rel.contact_ref, rel.solid_b)
                existing = owners.get(c_lbl)
                if not existing or rel.solid_b in existing:
                    before = set(owners.get(c_lbl, set()))
                    owners.setdefault(c_lbl, set()).update({x for x in (rel.solid_a, rel.solid_b) if x in solids})
                    changed |= before != owners[c_lbl]
        if not changed:
            break
    checked = []
    for prem, fid, sid, refs in records:
        candidates = common(refs, sid)
        known = [ref_owners(ref, sid) for _key, ref in refs if ref_owners(ref, sid)]
        if sid is not None and any(sid not in ref_owners(ref, sid) for _key, ref in refs):
            raise TuChoi('SOURCE_OBJECT_MISMATCH', f'{fid}: toán hạng/điểm dựng không thuộc phạm vi {sid!r}', (fid,))
        if sid is None and known and not set.intersection(*known):
            raise TuChoi('SOURCE_OBJECT_MISMATCH', f'{fid}: premise trộn thực thể của nhiều khối', (fid,))
        if sid is None and len(candidates) > 1:
            non_sub = candidates - derived_subsolids
            if len(non_sub) == 1:
                candidates = non_sub
        if sid is None and len(candidates) > 1:
            named = {s for s in candidates if re.search(rf"(?<![\w']){re.escape(solids[s].notation)}(?![\w'])",
                                                       chuan_hoa(prem.quote))}
            if len(named) != 1:
                raise TuChoi('AMBIGUOUS_REFERENCE', f'{fid}: thiếu phạm vi khối không mơ hồ', (fid,))
            candidates = named
        checked.append({'premise_id':fid,'declared_solid_id':prem.solid_id,'resolved_solid_ids':sorted({sid} if sid else candidates),
                        'vertices':sorted({ref.strip() if is_described_ref(ref) else _ref(ref) for _key, ref in refs}),'quote':prem.quote})
    # S8: every other scoped object of `scope_records` (sections, relation sides, simulation and measurement goals) is
    # bound by the same constructed-point ownership: an unqualified operand owned only by other solids contradicts its
    # scope. Unowned labels (unnamed section points, undeclared names) stay the routes' own refusals.
    parents = _derived_parents(p)
    sections = {sec.section_id: sec for sec in p.derived_sections}
    for goal in p.simulation_goals:
        if goal.kind != 'construct_derived_solid':
            continue
        sec = sections[goal.target_section_id]
        members = [goal.apex_ref, sec.through_point, *getattr(sec, 'named_intersections', {}).values(),
                   *(cut.point for cut in getattr(sec, 'stated_intersections', ()))]
        for ref in members:
            if ref and not is_described_ref(ref) and sec.target_solid_id in ref_owners(ref, sec.target_solid_id):
                owners.setdefault(identity(ref, sec.target_solid_id), set()).add(goal.derived_solid_id)
    for kind, where, scope, refs, _strict in scope_records(p):
        base = parents.get(scope, scope)
        if kind == 'premise':
            continue
        for ref in refs:
            ns, label = parse_qualified_ref(ref)
            own = ref_owners(ref, base)
            claimed = ns or scope
            if claimed is not None and own and claimed not in own:
                raise TuChoi('SOURCE_OBJECT_MISMATCH', f'{where}: toán hạng {ref!r} không thuộc phạm vi {claimed!r}', (where,))
            if kind == 'relation' and ns is None and not own:
                raise TuChoi('UNKNOWN_VERTEX_REF', f'{where}: tham chiếu {ref!r} không được khai báo', (where,))
    _check_qualified_refs(p.model_dump(), solids, owners)
    return checked


def _operand(t: dict[str, Any], key: str, n: int) -> list[str] | None:
    """DISTINCT labels of one goal operand: a line / segment exactly two, a plane (n = 3) three or more — a face may be
    named by all its vertices, (ABCD), as premises already may. Every plane label reaches the engine, which checks they
    are coplanar and that the three it measures with are not collinear (`kiem_mat_viet`). A repeated label is degenerate."""
    v = t.get(key)
    refs = _refs(v) if isinstance(v, (list, tuple)) and (len(v) >= n if n == 3 else len(v) == n) else None
    return refs if refs is not None and len(set(refs)) == len(refs) else None


def _mo_ta_phang(p: TypedFactNextPayload) -> dict[str, dict[str, Any]]:
    """R-1 (layer 1): described id → the planner's description of that unnamed point, `{"point_kind", "points"}` with the
    labels flat in the Registry descriptor contract's input order — so the SAME planner, Source Gate and engine read it
    (no second path). Resolves topologically in DAG order (supporting any Registry descriptor or `POINT_DEFINITIONS`
    and nested/line-endpoint `arg_items` up to depth 2)."""
    import copy
    import re
    from .registry import PlanningContract, _P1, chuan_hoa, descriptor_contracts

    by_id = {d.described_id: d for d in getattr(p, "described_points", ())}
    memo: dict[str, dict[str, Any]] = {}

    def _build(d_id: str, stack: set[str]) -> dict[str, Any]:
        if d_id in memo:
            return memo[d_id]
        if d_id in stack or d_id not in by_id:
            raise TuChoi("BRIDGE_UNSUPPORTED_DESCRIBED_POINT", f"@{d_id}: điểm được mô tả không hợp lệ", (d_id,))
        d = by_id[d_id]
        dcs = [c for c in descriptor_contracts(d.kind) if isinstance(c, PlanningContract)]
        if not dcs:
            raise TuChoi("UNSUPPORTED_CAPABILITY", f"@{d.described_id}: chưa có hợp đồng cho {d.kind}", (d.described_id,))
        ops_refs = [x for x in d.point_operands() if is_described_ref(x)]
        if not ops_refs:
            labels = [x for k, shape in DESCRIBED_POINT_FIELDS[d.kind].items()
                      for x in ([getattr(d, k)] if shape == "pt" else getattr(d, k))]
            res = {"point_kind": d.kind, "points": _refs(labels), "quote": d.quote}
            memo[d_id] = res
            return res
        new_stack = stack | {d_id}
        children: dict[str, dict[str, Any]] = {}
        for ref in ops_refs:
            sub = _build(ref.strip()[1:], new_stack)
            if "point_tree" in sub:
                raise TuChoi("BRIDGE_UNSUPPORTED_DESCRIBED_POINT",
                             f"@{d.described_id}: chỉ hỗ trợ điểm mô tả lồng tối đa 2 tầng", (d.described_id,))
            if chuan_hoa(sub["quote"]) not in chuan_hoa(d.quote):
                raise TuChoi("SOURCE_OBJECT_MISMATCH",
                             f"@{d.described_id}: cụm mô tả {sub['quote']!r} không nằm trong {d.quote!r}",
                             (d.described_id,))
            inner_dcs = [c for c in descriptor_contracts(sub["point_kind"])
                         if isinstance(c, PlanningContract) and isinstance(c.phrase, str)]
            if not inner_dcs or not any(re.fullmatch(c.phrase.replace("{P}", _P1), chuan_hoa(sub["quote"]), re.I)
                                        for c in inner_dcs):
                raise TuChoi("BRIDGE_UNSUPPORTED_DESCRIBED_POINT",
                             f"@{d.described_id}: điểm được mô tả qua một điểm được mô tả khác chưa có chứng chỉ nguồn",
                             (d.described_id,))
            children[ref] = sub
        if (d.kind in ("orthogonal_projection", "orthogonal_projection_line") and is_described_ref(d.point)
                and (d.kind == "orthogonal_projection" or not any(is_described_ref(x) for x in d.line))):
            inner = children[d.point]
            target_labels = list(d.plane if d.kind == "orthogonal_projection" else d.line)
            res = {
                "point_kind": d.kind,
                "points": _refs(target_labels),
                "point_tree": copy.deepcopy({"point_kind": inner["point_kind"], "points": list(inner["points"])}),
                "quote": d.quote,
            }
            memo[d_id] = res
            return res
        arg_items: list[Any] = []
        named_points: list[str] = []
        for k, shape in DESCRIBED_POINT_FIELDS[d.kind].items():
            vals = [getattr(d, k)] if shape == "pt" else list(getattr(d, k))
            for v in vals:
                if is_described_ref(v):
                    sub = children[v]
                    arg_items.append({"point_kind": sub["point_kind"], "points": list(sub["points"])})
                else:
                    lbl = _ref(v)
                    arg_items.append(lbl)
                    named_points.append(lbl)
        res = {
            "point_kind": d.kind,
            "points": named_points,
            "point_tree": {"arg_items": arg_items},
            "quote": d.quote,
        }
        memo[d_id] = res
        return res

    return {d.described_id: _build(d.described_id, set()) for d in getattr(p, "described_points", ())}


def _mo_ta_cua(ref: str, mo_ta: dict[str, dict[str, Any]], consumer_quote: str, where: str) -> dict[str, Any]:
    """The description of `@id`, whose describing phrase must lie inside the quote of what uses it (provenance: the
    phrase the Source Gate reads in that quote is the one the extractor declared)."""
    import copy
    from .registry import chuan_hoa

    d = mo_ta.get(ref.strip()[1:])
    if d is None:
        raise TuChoi("UNKNOWN_DERIVED_REFERENCE", f"{where}: điểm mô tả {ref!r} không được khai", (where,))
    if chuan_hoa(d["quote"]) not in chuan_hoa(consumer_quote):
        raise TuChoi("SOURCE_OBJECT_MISMATCH", f"{where}: cụm mô tả {d['quote']!r} không nằm trong câu dùng nó", (where,))
    res: dict[str, Any] = {"point_kind": d["point_kind"], "points": list(d["points"])}
    if "point_tree" in d:
        res["point_tree"] = copy.deepcopy(d["point_tree"])
    return res


def _cau_hoi_mo_ta(g, mo_ta: dict[str, dict[str, Any]]) -> dict[str, Any] | None:
    """A measurement goal with one or more described point operands → route B's described question (`point_kind`/
    `point_tree` for legacy single-slot goals, or `goal_trees` for derived-line and multi-described goals)."""
    t = g.target
    used = [(k, x) for k in DESCRIBED_GOAL_KEYS if k in t
            for x in (t[k] if isinstance(t[k], (list, tuple)) else [t[k]]) if is_described_ref(x)]
    if not used:
        return None
    keys = set(t) - {"solid", "solid_id"}
    if len(used) == 1:
        key, ref = used[0]
        desc = _mo_ta_cua(ref, mo_ta, g.quote, g.goal_id)
        has_arg_items = isinstance(desc.get("point_tree"), dict) and "arg_items" in desc["point_tree"]
        if (
            not has_arg_items
            and not (g.goal_type == "distance" and keys in ({"point", "line"}, {"line", "plane"}) and key == "line")
            and not (g.goal_type == "distance" and keys == {"line1", "line2"})
        ):
            rest = lambda k: [_ref(x) for x in t[k] if not is_described_ref(x)]      # noqa: E731
            if g.goal_type == "distance" and keys == {"point", "plane"}:
                return {"quantity": "distance", **desc, "points_b": _refs(t["plane"])}
            if g.goal_type == "distance" and keys == {"point", "line"} and key == "point":
                return {"quantity": "distance", **desc, "points_b": _refs(t["line"])}
            if g.goal_type == "distance" and keys == {"segment"}:
                return {"quantity": "length", **desc, "points_b": rest("segment")}
            if g.goal_type == "angle" and keys == {"line", "plane"} and key == "line":
                return {"quantity": "angle", **desc, "points_a": rest("line"), "points_b": _refs(t["plane"])}
            if g.goal_type == "angle" and keys == {"line1", "line2"} and key in ("line1", "line2"):
                other = "line2" if key == "line1" else "line1"
                return {"quantity": "angle", **desc, "points_a": rest(key), "points_b": _refs(t[other])}
            if g.goal_type == "area" and keys == {"polygon"} and len(t["polygon"]) == 3:
                return {"quantity": "area", **desc, "points_b": rest("polygon")}
            raise TuChoi("BRIDGE_UNSUPPORTED_DESCRIBED_POINT", f"{g.goal_id}: điểm được mô tả ở toán hạng {key!r} của "
                         f"{g.goal_type} chưa có hợp đồng mục tiêu", (g.goal_id,))

    def node_of(val: str):
        return _mo_ta_cua(val, mo_ta, g.quote, g.goal_id) if is_described_ref(val) else _ref(val)

    def plane_pts(key: str) -> list[str]:
        raw = t.get(key)
        if not isinstance(raw, (list, tuple)) or any(is_described_ref(x) for x in raw):
            raise TuChoi("BRIDGE_UNSUPPORTED_DESCRIBED_POINT",
                         f"{g.goal_id}: điểm được mô tả ở toán hạng mặt phẳng {key!r} chưa có hợp đồng", (g.goal_id,))
        pts = _refs(raw)
        if len(pts) < 3 or len(set(pts)) != len(pts):
            raise TuChoi("INVALID_MATH_GOAL", f"{g.goal_id}: mặt phẳng {key!r} thiếu đỉnh phân biệt", (g.goal_id,))
        return pts

    def line_items(key: str) -> list[Any]:
        raw = t.get(key)
        if not isinstance(raw, (list, tuple)) or len(raw) != 2 or len({x.strip() for x in raw}) != 2:
            raise TuChoi("INVALID_MATH_GOAL", f"{g.goal_id}: đường {key!r} cần hai đầu mút phân biệt", (g.goal_id,))
        return [node_of(x) for x in raw]

    if g.goal_type == "distance" and keys == {"point", "line"}:
        return {"quantity": "distance", "goal_trees": {"mode": "distance_point_line", "point": node_of(t["point"]), "line": line_items("line")}}
    if g.goal_type == "distance" and keys == {"line", "plane"}:
        return {"quantity": "distance", "goal_trees": {"mode": "distance_line_plane", "line": line_items("line"), "plane": plane_pts("plane")}}
    if g.goal_type == "distance" and keys == {"point", "plane"}:
        return {"quantity": "distance", "goal_trees": {"mode": "distance_point_plane", "point": node_of(t["point"]), "plane": plane_pts("plane")}}
    if g.goal_type == "distance" and keys == {"line1", "line2"}:
        return {"quantity": "distance", "goal_trees": {"mode": "distance_lines", "line1": line_items("line1"), "line2": line_items("line2")}}
    if g.goal_type == "distance" and keys == {"segment"}:
        return {"quantity": "length", "goal_trees": {"mode": "length", "points": line_items("segment")}}
    if g.goal_type == "angle" and keys == {"line", "plane"}:
        return {"quantity": "angle", "goal_trees": {"mode": "angle_line_plane", "line": line_items("line"), "plane": plane_pts("plane")}}
    if g.goal_type == "angle" and keys == {"line1", "line2"}:
        return {"quantity": "angle", "goal_trees": {"mode": "angle_lines", "line1": line_items("line1"), "line2": line_items("line2")}}
    if g.goal_type == "area" and keys == {"polygon"} and len(t["polygon"]) == 3:
        raw_poly = t["polygon"]
        if len({x.strip() for x in raw_poly}) != 3:
            raise TuChoi("INVALID_MATH_GOAL", f"{g.goal_id}: tam giác cần ba đỉnh phân biệt", (g.goal_id,))
        return {"quantity": "area", "goal_trees": {"mode": "area", "polygon": [node_of(x) for x in raw_poly]}}
    raise TuChoi("BRIDGE_UNSUPPORTED_DESCRIBED_POINT",
                 f"{g.goal_id}: mục tiêu {g.goal_type} với điểm được mô tả chưa có hợp đồng mục tiêu", (g.goal_id,))


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


def _la_mat_qua_ba_diem(sec: DerivedPlaneSectionSpec | DerivedPlaneSectionSpecV2) -> bool:
    """A `/2` plane given ONLY as "contains these three named points" — the plane (MNP), no relation to ground."""
    cs = getattr(sec, "constraints", ())
    return (sec.plane_kind == "constrained" and len(cs) == 1 and cs[0].kind == "contains_points"
            and len(cs[0].operands) == 3 and not any(is_described_ref(p) for p in cs[0].operands))


def _ten_mat_khai(sec: DerivedPlaneSectionSpec | DerivedPlaneSectionSpecV2) -> str:
    """The plane name the scene must display: a three-point plane is its three points `(MNP)`."""
    return "".join(_refs(sec.constraints[0].operands)) if _la_mat_qua_ba_diem(sec) else sec.plane_name


def _mat_fact(sec: DerivedPlaneSectionSpec | DerivedPlaneSectionSpecV2, solids: dict[str, Any],
              asked: list[str], mo_ta: dict[str, dict[str, Any]] | None = None,
              extra_quotes: tuple[str, ...] | list[str] = ()) -> dict[str, Any]:
    """The section fact's PLANE (shared by `/1` and `/2`). A described through-point (R-1) becomes route B's described
    point of a relation plane: `point_kind` + `points` instead of `point`."""
    if sec.plane_kind == "constrained":                # C17: the stated relations only — witnesses are the planner's
        if any(is_described_ref(p) for c in sec.constraints if c.kind != "contains_points" for p in c.operands):
            raise TuChoi("BRIDGE_UNSUPPORTED_DESCRIBED_POINT", f"{sec.section_id}: điểm mô tả trong ràng buộc mặt chưa hỗ trợ",
                         (sec.section_id,))
        if _la_mat_qua_ba_diem(sec):
            # "(MNP)": the plane IS its three named points — the planner's three-point section (same fact as `/1`); the
            # Source Gate grounds "cắt bởi (MNP)" in the quote, the engine proves the points distinct and not collinear
            # and computes the bounded section (an exterior line–plane intersection is never a vertex).
            pts = _refs(sec.constraints[0].operands)
            if len(set(pts)) != 3:
                raise TuChoi("DEGENERATE_POINTS", f"{sec.section_id}: ({''.join(pts)}) không xác định một mặt phẳng",
                             (sec.section_id,))
            return {"id": sec.section_id, "kind": "section", "role": "question" if asked else "premise",
                    "quotes": [sec.quote, *asked], "solid": solids[sec.target_solid_id].notation, "points": pts}
        quote_ctx = "\n".join([sec.quote, *extra_quotes])
        cs_out: list[dict[str, Any]] = []
        for c in sec.constraints:
            if c.kind == "contains_points" and any(is_described_ref(p) for p in c.operands):
                items = [
                    _mo_ta_cua(p, mo_ta or {}, quote_ctx, sec.section_id) if is_described_ref(p) else _ref(p)
                    for p in c.operands
                ]
                cs_out.append({
                    "kind": c.kind,
                    "points": [x for x in items if isinstance(x, str)],
                    "point_items": items,
                })
            else:
                cs_out.append({"kind": c.kind, "points": _refs(c.operands)})
        explicit_pname = (
            getattr(sec, "plane_name", None)
            if (not hasattr(sec, "model_fields_set") or "plane_name" in sec.model_fields_set)
            else None
        )
        f = {"id": sec.section_id, "kind": "section", "role": "question" if asked else "premise",
             "quotes": [sec.quote, *asked], "solid": solids[sec.target_solid_id].notation,
             "plane_constraints": cs_out}
        if explicit_pname is not None:
            f["plane_name"] = explicit_pname
        return f
    rel = _PLANE_RELATION.get(sec.plane_kind)
    if rel is None:
        raise TuChoi("BRIDGE_UNSUPPORTED_PLANE_KIND", f"{sec.section_id}: mặt {sec.plane_kind} chưa có phép dựng của planner",
                     (sec.section_id,))
    qua = (_mo_ta_cua(sec.through_point, mo_ta or {}, sec.quote, sec.section_id) if is_described_ref(sec.through_point)
           else {"point": _ref(sec.through_point)})
    f: dict[str, Any] = {"id": sec.section_id, "kind": "section", "role": "question" if asked else "premise",
                         "quotes": [sec.quote, *asked], "solid": solids[sec.target_solid_id].notation,
                         **qua, "plane_relation": rel}
    explicit_pname = (
        getattr(sec, "plane_name", None)
        if (not hasattr(sec, "model_fields_set") or "plane_name" in sec.model_fields_set)
        else None
    )
    if explicit_pname is not None:
        import re as _re
        if not _re.fullmatch(r"(?:[A-Z][0-9]*'?|[α-ω]'?)", str(explicit_pname)):
            raise TuChoi("SOURCE_OBJECT_MISMATCH", f"{sec.section_id}: tên mặt đã khai không khớp mặt được Source Gate xác minh", (sec.section_id,))
        f["plane_name"] = explicit_pname
    if rel == "parallel":
        f["points_b"] = _refs(sec.parallel_plane)
    elif rel == "perpendicular":
        f["points_b"] = _refs(sec.perpendicular_line)
    else:
        f.update(points_a=_refs(sec.parallel_line_a), points_b=_refs(sec.parallel_line_b))
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
    if getattr(sec, "plane_kind", None) == "constrained":
        con_pat = re.compile(
            rf"(?:(?:mặt\s+phẳng|mp)\s*)?\((?P<ten>{re.escape(str(ten))})\)\s*(?:là\s+mặt\s+phẳng\s+)?(?:(?:đi\s+)?qua|chứa)\b",
            re.IGNORECASE,
        )
        cac_mau = (*cac_mau, con_pat)
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
            seen_spans.add((cs, ce))
            cands.append(sent)
    if len(cands) == 1:
        return cands
    # An imperative "(Hãy) dựng mặt phẳng (P) …" that restates the ONE declarative definition word for word is the same
    # plane, not a second reading. Any other set of candidates stays ambiguous: none is chosen (the Source Gate refuses).
    # (This rule was meant to skip imperatives, but a literal BACKSPACE byte stood where `\b` was written, so it never
    # fired; skipping them outright would also refuse a text whose only definition is the imperative.)
    menh_lenh = re.compile(r"^\s*(?:hãy\s+)?dựng\s+", re.IGNORECASE)
    khai = [s for s in cands if not menh_lenh.match(s)]
    if len(khai) == 1 and all(menh_lenh.sub("", s).casefold() == khai[0].casefold() for s in cands if s not in khai):
        return khai
    return []


def _section_fact_v2(sec: DerivedPlaneSectionSpecV2, solids: dict[str, Any], asked: list[str],
                     problem_text: str | None = None, mo_ta: dict[str, dict[str, Any]] | None = None) -> dict[str, Any]:
    """`/2`: stated intersections are the stated cuts (names aligned, None = stated but unnamed); the planner may derive
    the vertex of an UNSTATED lateral edge where a closed boundary is required (D6); a declared boundary is verified."""
    extra = _v2_plane_def_quotes(sec, problem_text)
    f = _mat_fact(sec, solids, asked, mo_ta, extra_quotes=extra)
    if _la_mat_qua_ba_diem(sec):
        # The engine derives every vertex of a three-point section; stated cuts / a declared boundary have no carrier on
        # that function yet — refused, never silently dropped.
        if sec.stated_intersections or sec.declared_boundary is not None:
            raise TuChoi("UNSUPPORTED_CAPABILITY", f"{sec.section_id}: giao điểm/biên khai sẵn trên mặt qua ba điểm chưa hỗ trợ",
                         (sec.section_id,))
        return f
    if extra:
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
    named = {frozenset(_refs(split_edge_key(k))): v for k, v in sec.named_intersections.items()}
    if not edges and named:                              # the names the payload gives define the stated cuts, in its order
        edges = [tuple(_refs(split_edge_key(k))) for k in sec.named_intersections]
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


#: Curved sections the planner executes (bridge /2, registry /24); every other plane kind of a curved solid is refused.
_MAT_CAT_CONG = ("parallel_to_base_at_distance", "parallel_to_base_at_ratio", "axial_section")
#: A solid WITHOUT an axis (a sphere) is cut by a plane placed from its centre (seventh continuation).
_MAT_CAT_TAM = ("at_distance_from_center", "through_center")


def _phan_cong(p: TypedFactNextPayload, solids: dict[str, Any]) -> list[dict[str, Any]]:
    """ONE solid of revolution (composites are refused before): its sections, the small cone a parallel section cuts off,
    and every goal, as planner facts (internal `curved_part`). Pure translation: nothing is read from the text here — the
    Source Gate binds each to its quote. An axis is required for a section (`KHOI_CONG.co_truc`): a sphere has none."""
    from app.simulation.geometry.curved import KHOI_CONG, LOAI_TU_NGUON

    (s,) = p.solids
    kc = KHOI_CONG[LOAI_TU_NGUON[s.solid_type]]
    out: list[dict[str, Any]] = []
    secs = {x.section_id: x for x in p.derived_sections}
    names = [x.plane_name for x in p.derived_sections]
    if len(set(names)) != len(names):       # one name, two planes: every binding would be a guess (review round 2, B2)
        raise TuChoi("AMBIGUOUS_REFERENCE", f"hai thiết diện cùng tên mặt phẳng {sorted({n for n in names if names.count(n) > 1})}",
                     tuple(x.section_id for x in p.derived_sections))
    for x in p.derived_sections:
        if x.target_solid_id != s.solid_id or x.plane_kind not in (_MAT_CAT_CONG if kc.co_truc else _MAT_CAT_TAM):
            raise TuChoi("BRIDGE_UNSUPPORTED_CURVED", f"{x.section_id}: thiết diện {x.plane_kind} của khối tròn xoay này chưa "
                         "có trên planner", (x.section_id,))
        if (x.distance_from_center is not None) != (x.plane_kind == "at_distance_from_center") or (
                not kc.co_truc and (x.distance_from_base or x.ratio_from_apex or x.through_point)):
            raise TuChoi("SOURCE_OBJECT_MISMATCH", f"{x.section_id}: trường của thiết diện mâu thuẫn với loại mặt phẳng "
                         f"{x.plane_kind}", (x.section_id,))     # review 7: contradicting fields are refused, not dropped
        if x.section_shape not in (None, "polygon" if x.plane_kind == "axial_section" else "circle"):
            raise TuChoi("SOURCE_OBJECT_MISMATCH", f"{x.section_id}: hình dạng {x.section_shape} mâu thuẫn với loại thiết diện "
                         f"{x.plane_kind}", (x.section_id,))     # review M2: the payload's own fields must agree
        if x.through_point and is_described_ref(x.through_point):
            raise TuChoi("BRIDGE_UNSUPPORTED_DESCRIBED_POINT",
                         f"{x.section_id}: thiết diện của khối tròn xoay qua điểm mô tả chưa có trên planner",
                         (x.section_id,))
        out.append({"id": x.section_id, "kind": "section", "role": "premise", "quotes": [x.quote], "solid": s.notation,
                    "curved_part": {"role": "section", "kind": x.plane_kind, "plane": x.plane_name,
                                    "distance": x.distance_from_center if kc.co_truc is False else x.distance_from_base,
                                    "ratio": x.ratio_from_apex,
                                    "point": _ref(x.through_point) if x.through_point else None}})
    nho: set[str] = set()
    for g in p.simulation_goals:
        if g.kind != "construct_derived_solid":
            continue
        sec = secs.get(g.target_section_id or "")
        if sec is None or sec.plane_kind == "axial_section" or (g.parent_solid_id or s.solid_id) != s.solid_id:
            raise TuChoi("BRIDGE_UNSUPPORTED_DERIVED_SOLID", f"{g.goal_id}: khối con chỉ là khối nón nhỏ cắt bởi mặt phẳng song "
                         "song đáy", (g.goal_id,))
        nho.add(g.derived_solid_id)
        out.append({"id": g.goal_id, "kind": "solid", "role": "premise", "quotes": [g.quote], "solid": s.notation,
                    "curved_part": {"role": "derived", "section": sec.section_id, "derived": g.derived_solid_id,
                                    "apex": _ref(g.apex_ref)}})
    for g in p.math_goals:
        q = {"id": g.goal_id, "kind": "question", "role": "question", "quotes": [g.quote], "solid": s.notation}
        if g.kind in ("volume_ratio", "residual_volume"):
            pair = ((g.numerator_solid_id, g.denominator_solid_id) if g.kind == "volume_ratio"
                    else (g.parent_solid_id, g.cut_solid_id))
            if set(pair) - {s.solid_id, *nho}:
                raise TuChoi("UNKNOWN_SOLID_ID", f"{g.goal_id}: khối {sorted(set(pair) - {s.solid_id, *nho})} không có", (g.goal_id,))
            out.append({**q, "quantity": g.kind, "curved_part": {"role": "ask", "pair": list(pair)}})
        elif g.kind == "measurement" and g.goal_type in ("area", "radius") and "section_id" in g.target:
            if g.target["section_id"] not in secs:
                raise TuChoi("INVALID_MATH_GOAL", f"{g.goal_id}: thiết diện {g.target['section_id']!r} không có", (g.goal_id,))
            out.append({**q, "quantity": g.goal_type, "curved_part": {"role": "ask", "section": g.target["section_id"]}})
        elif (g.kind == "measurement" and g.goal_type in ("volume", "area", "lateral_area", "radius")
              and set(g.target) <= {"solid", "solid_id"} and measurement_scope(p, g) == s.solid_id):
            out.append({**q, "quantity": g.goal_type})
        elif any(is_described_ref(x) for k in DESCRIBED_GOAL_KEYS if k in g.target
                 for x in (g.target[k] if isinstance(g.target[k], (list, tuple)) else [g.target[k]])):
            raise TuChoi("BRIDGE_UNSUPPORTED_DESCRIBED_POINT",
                         f"{g.goal_id}: mục tiêu của khối tròn xoay với điểm mô tả chưa có trên planner",
                         (g.goal_id,))
        else:
            raise TuChoi("BRIDGE_UNSUPPORTED_CURVED", f"{g.goal_id}: mục tiêu {g.kind}/{g.goal_type} của khối tròn xoay chưa có "
                         "trên planner", (g.goal_id,))
    return out


def _output_policies_from_payload(p: TypedFactNextPayload) -> dict[str, dict[str, Any]]:
    return {
        g.goal_id: {
            **({"requested_unit": g.requested_unit} if getattr(g, "requested_unit", None) else {}),
            **({"rounding": dict(g.rounding)} if getattr(g, "rounding", None) else {}),
            "quote": g.quote,
        }
        for g in p.math_goals
        if getattr(g, "requested_unit", None) or getattr(g, "rounding", None)
    }


def _ket_cau_noi(p: TypedFactNextPayload, facts: list[dict[str, Any]], version: str, scoped: Any) -> dict[str, Any]:
    khong = [g.goal_id for g in p.simulation_goals if g.kind in _NO_NEW_FACT_GOALS]
    return {"facts": facts, "bridge": {"version": version, "goals_without_new_facts": khong,
                                       "scope_validation_version": "typed-fact-next-scope/1",
                                       "validated_premise_scopes": scoped,
                                       "declared_length_unit": p.length_unit,
                                       "declared_plane_names": {s.section_id: _ten_mat_khai(s) for s in p.derived_sections},
                                       "output_policies": _output_policies_from_payload(p),
                                       "problem_text": p.problem_text}}


def bridge_v2(raw: dict[str, Any]) -> dict[str, Any]:
    """`typed-fact-next/2` → planner facts (run `hybrid-contract-v2`). The same pure translation as `/1` except sections."""
    try:
        p = parse_typed_fact_next_v2(raw)
    except TypedFactNextValidationError as e:
        raise TuChoi(e.code, e.detail) from None
    if p.unresolved:
        # SL-2: the extractor reported what it could not read. Existing codes (flat contract parity): `ambiguous` facts are
        # AMBIGUOUS_FACT, the `unsupported` escape is OUT_OF_SCOPE. An `incomplete`/`ambiguous` goal that merely embeds an
        # `unsupported` operand span is a consequence of that capability gap, not a student-answerable ambiguity.
        unsup = [x for x in p.unresolved if x.kind == "unsupported"]
        clarifiable = [
            x
            for x in p.unresolved
            if x.kind != "unsupported"
            and not any((u0.quote and u0.quote in x.quote) or (u0.subject_ref and u0.subject_ref == x.subject_ref) for u0 in unsup)
        ]
        u = clarifiable[0] if clarifiable else p.unresolved[0]
        raise TuChoi("OUT_OF_SCOPE" if u.kind == "unsupported" else "AMBIGUOUS_FACT",
                     f"{u.unresolved_id}: {u.kind} — không đoán cách hiểu", tuple(x.unresolved_id for x in p.unresolved),
                     data={"clarification": clarification_record(u, p.problem_text)})
    return _bridge(p, _section_fact_v2, BRIDGE_V2_VERSION, v2=True)


def _bridge(p: TypedFactNextPayload, section_fact, version: str, v2: bool) -> dict[str, Any]:
    facts: list[dict[str, Any]] = []
    solids = {s.solid_id: s for s in p.solids}
    scoped = _kiem_pham_vi_tien_de(p, solids)  # semantic ownership precedes every capability refusal/fallback
    mo_ta = _mo_ta_phang(p)                     # R-1: described points (`/2` only; `/1` declares none)
    curved = {s.solid_id for s in p.solids if s.solid_type not in ("pyramid", "prism")}
    poly_solids = [x for x in solids.values() if x.solid_type in ("pyramid", "prism")]
    poly_ids = {x.solid_id for x in poly_solids}
    constructed_outs = {
        _ref(prem.args[CONSTRUCTED_OUTPUTS[prem.kind]])
        for prem in p.premises
        if prem.kind in CONSTRUCTED_OUTPUTS
        and isinstance(prem.args.get(CONSTRUCTED_OUTPUTS[prem.kind]), str)
        and not is_described_ref(prem.args[CONSTRUCTED_OUTPUTS[prem.kind]])
    }
    poly_root_solids = [
        x for x in poly_solids
        if not (
            x.solid_type == "pyramid"
            and any(
                h is not x
                and {x.canonical_vertex(v) for v in x.local_vertices()}
                <= ({h.canonical_vertex(v) for v in h.local_vertices()} | constructed_outs)
                and (h.solid_type != "pyramid" or len(h.local_vertices()) > len(x.local_vertices()))
                for h in poly_solids
            )
        )
    ]
    sphere_anchor: dict[str, tuple[str, str, list[str]]] = {}
    for s in p.solids:
        if s.circumscribes is not None:
            sphere_anchor[s.solid_id] = ("circumscribes", s.circumscribes, [])
        elif getattr(s, "inscribed_in", None) is not None:
            sphere_anchor[s.solid_id] = ("inscribed_in", s.inscribed_in, [])
    for r in p.relations:
        if r.kind in ("circumscribes", "inscribed_in") and r.solid_a and r.solid_b:
            prev_q = sphere_anchor[r.solid_a][2] if r.solid_a in sphere_anchor else []
            extra_q = [*prev_q, *([r.quote] if r.quote != solids[r.solid_a].quote and r.quote not in prev_q else [])]
            sphere_anchor[r.solid_a] = (r.kind, r.solid_b, extra_q)
    if curved and (not v2 or (not poly_ids and any(r.kind not in ("circumscribes", "inscribed_in") for r in p.relations))):
        raise TuChoi("BRIDGE_UNSUPPORTED_CURVED", f"{sorted(curved)}: thiết diện hay quan hệ của khối tròn xoay chưa có trên "
                     "planner", tuple(sorted(curved)))
    from .registry import CIRCUMSCRIBED_NAME_PATTERN, CURVED_NAME_PATTERN
    import re as _re_cong

    if bad := sorted(
        s.solid_id for s in p.solids
        if s.solid_id in curved
        and not _re_cong.fullmatch(
            CIRCUMSCRIBED_NAME_PATTERN if s.solid_id in sphere_anchor else CURVED_NAME_PATTERN,
            s.notation,
        )
    ):
        raise TuChoi("BRIDGE_UNSUPPORTED_CURVED", f"{bad}: ký hiệu khối tròn xoay này chưa diễn đạt được trên planner",
                     tuple(bad))              # a capability gap, not an extraction error (Wave 3 W3-N45/N46 reason lock)
    from ..geometry import curved as CV

    axial_hosts = [
        s.solid_id for s in p.solids
        if s.solid_type in CV.LOAI_TU_NGUON and CV.KHOI_CONG[CV.LOAI_TU_NGUON[s.solid_type]].co_truc
    ]
    is_standalone_curved = v2 and len(p.solids) == 1 and len(curved) == 1 and not sphere_anchor
    is_poly_sphere_composite = (
        v2
        and bool(poly_ids)
        and bool(curved)
        and all(cid in sphere_anchor and sphere_anchor[cid][1] in poly_ids for cid in curved)
        and all(sec.target_solid_id in poly_ids for sec in p.derived_sections)
    )
    is_axial_sphere_composite = (
        v2
        and not poly_ids
        and len(axial_hosts) == 1
        and len(curved) >= 2
        and all(cid == axial_hosts[0] or (cid in sphere_anchor and sphere_anchor[cid][1] == axial_hosts[0]) for cid in curved)
        and not p.derived_sections
        and not any(g.kind == "construct_derived_solid" for g in p.simulation_goals)
    )
    if curved and not (is_standalone_curved or is_poly_sphere_composite or is_axial_sphere_composite):
        raise TuChoi("BRIDGE_UNSUPPORTED_CURVED_COMPOSITE", f"{sorted(curved)}: khối tròn xoay cùng khối khác trong một bài "
                     "chưa có chứng chỉ quan hệ trên planner", tuple(sorted(curved)))
    unnamed_curved = [s.solid_id for s in p.solids if s.solid_id in curved and s.notation == "()"]
    curved_sym: dict[str, str] = {}
    for s in p.solids:
        if s.solid_id in curved:
            if len(unnamed_curved) > 1 and s.notation == "()" and s.solid_id in sphere_anchor:
                rk, hid, _eq = sphere_anchor[s.solid_id]
                curved_sym[s.solid_id] = f"({'out' if rk == 'circumscribes' else 'in'}:{solids[hid].notation})"
            else:
                curved_sym[s.solid_id] = s.notation
    for s in p.solids:
        if s.solid_type == "cone_frustum":
            raise TuChoi("BRIDGE_UNSUPPORTED_CURVED", f"{s.solid_id}: khối {s.solid_type} chưa có trên planner", (s.solid_id,))
        if any(a != b for a, b in s.vertex_bindings.items()) or s.coordinate_frame_id != "root":
            raise TuChoi("BRIDGE_UNSUPPORTED_QUALIFIED_IDENTITY", f"{s.solid_id}: hai điểm khác nhau mang cùng nhãn — TypedFact "
                         "định danh điểm bằng nhãn", (s.solid_id,))
        if s.solid_id in curved:
            curved_info = {"kind": s.solid_type, "center": s.center, "top": s.apex_or_top, "rim": s.rim_point,
                           "radius": s.radius, "height": s.height}
            s_quotes = [s.quote]
            if s.solid_id in sphere_anchor:
                rel_kind, host_id, extra_q = sphere_anchor[s.solid_id]
                curved_info[rel_kind] = curved_sym.get(host_id, solids[host_id].notation)
                s_quotes.extend(extra_q)
            facts.append({"id": s.solid_id, "kind": "solid", "role": "premise", "quotes": s_quotes,
                          "solid": curved_sym[s.solid_id], "curved": curved_info})
            continue
        facts.append({"id": s.solid_id, "kind": "solid", "role": "premise", "quotes": [s.quote], "solid": s.notation,
                      "solid_type": s.solid_type})
    theo_ten = {s.notation: f for s, f in zip(p.solids, facts)}
    used_fact_ids = (
        {f["id"] for f in facts}
        | {sec.section_id for sec in p.derived_sections}
        | {g.goal_id for g in p.simulation_goals}
        | {g.goal_id for g in p.math_goals}
    )

    def _alloc_fact_id(preferred: str, prefix: str) -> str:
        cand = preferred if preferred not in used_fact_ids else f"{prefix}_{preferred}"
        idx = 2
        while cand in used_fact_ids:
            cand = f"{prefix}_{preferred}_{idx}"
            idx += 1
        used_fact_ids.add(cand)
        return cand

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
        elif k == "parallelogram":
            f = {"kind": "polygon_shape", "points": _refs(a["vertices"]), "shape": "parallelogram"}
        elif k == "rhombus":
            f = {
                "kind": "polygon_shape",
                "points": _refs(a["vertices"]),
                "shape": "rhombus",
                **({"value": str(a["side"])} if a.get("side") is not None else {}),
            }
        elif k in ("trapezoid", "isosceles_trapezoid"):
            f = {
                "kind": "polygon_shape",
                "points": _refs(a["vertices"]),
                "shape": k,
                "points_a": _refs(a["base_a"]),
                "points_b": _refs(a["base_b"]),
            }
        elif k in ("right_angle", "base_is_right_triangle"):
            at = _ref(a["right_at"] if "vertices" in a else a["vertex"])
            f = {"kind": "right_angle", "at": at,
                 "points": [x for x in _refs(a["vertices"]) if x != at] if "vertices" in a else _refs(a["rays"])}
        elif k == "segment_length":
            f = {"kind": "length", "measure": "segment", "points": _refs(a["segment"]), "value": str(a["value"])}
        elif k == "height":
            sid = a.get("solid") or prem.solid_id
            sol = solids.get(sid or "")
            if sol is None and sid is None and len(poly_root_solids) == 1:
                sol = poly_root_solids[0]
            f = {"kind": "length", "measure": "height",
                 "solid": curved_sym.get(sol.solid_id, sol.notation) if sol else sid,
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
            if sol is None and sid is None and len(poly_root_solids) == 1:
                sol = poly_root_solids[0]
            f = {"kind": "altitude", "points": [_ref(a["apex"]), _ref(a["foot"])],
                 "solid": sol.notation if sol else sid}
        elif k in ("midpoint", "point_is_midpoint"):
            f = {"kind": "point_def", "point_kind": "midpoint", "point": _ref(a["point"]), "points": _refs(a["segment"])}
        elif k in ("divide_segment", "point_divides_segment"):
            f = {"kind": "point_def", "point_kind": "divide_segment", "point": _ref(a["point"]),
                 "points": _refs(a["segment"]), "value": str(a["ratio"])}
        elif k in ("centroid", "point_is_centroid"):
            f = {"kind": "point_def", "point_kind": "centroid", "point": _ref(a["point"]), "points": _refs(a["polygon"])}
        elif k in ("orthogonal_projection", "point_is_foot", "orthogonal_projection_line"):
            target_key = "line" if k == "orthogonal_projection_line" else "plane"
            prem_slots: dict[str, Any] = {}
            f = {"kind": "projection", "points": _refs(a[target_key])}
            if is_described_ref(a["point"]):
                prem_slots["point"] = mo_ta[a["point"].strip()[1:]]
            else:
                f["point"] = _ref(a["point"])
            if is_described_ref(a["image"]):
                prem_slots["image"] = mo_ta[a["image"].strip()[1:]]
            else:
                f["at"] = _ref(a["image"])
            if prem_slots:
                f["goal_trees"] = {"premise_slots": prem_slots}
        elif k == "point_reflection":
            prem_slots = {}
            f = {"kind": "point_reflection", "at": _ref(a["image"])}
            if is_described_ref(a["point"]):
                prem_slots["point"] = mo_ta[a["point"].strip()[1:]]
            else:
                f["point"] = _ref(a["point"])
            if is_described_ref(a["center"]):
                prem_slots["center"] = mo_ta[a["center"].strip()[1:]]
            else:
                f["points"] = [_ref(a["center"])]
            if prem_slots:
                f["goal_trees"] = {"premise_slots": prem_slots}
        elif k == "intersect_line_line":
            f = {"kind": "point_def", "point_kind": "intersect_line_line", "point": _ref(a["point"]),
                 "points_a": _refs(a["line1"]), "points_b": _refs(a["line2"])}
        elif k == "intersect_line_plane":
            f = {"kind": "point_def", "point_kind": "intersect_line_plane", "point": _ref(a["point"]),
                 "points_a": _refs(a["line"]), "points_b": _refs(a["plane"])}
        elif k == "line_plane_angle":
            f = {"kind": "line_plane_angle", "points_a": _refs(a["line"]), "points_b": _refs(a["plane"]),
                 "value": str(a["value"]), **({"angle_unit": str(a["unit"])} if a.get("unit") else {})}
        elif k == "plane_plane_angle":
            f = {"kind": "plane_plane_angle", "points_a": _refs(a["plane1"]), "points_b": _refs(a["plane2"]),
                 "value": str(a["value"]), **({"angle_unit": str(a["unit"])} if a.get("unit") else {})}
        elif k == "dihedral_angle":
            f = {"kind": "dihedral_angle", "point": _ref(a["point_a"]), "points": _refs(a["edge"]),
                 "at": _ref(a["point_b"]), "value": str(a["value"]),
                 **({"angle_unit": str(a["unit"])} if a.get("unit") else {})}
        elif k == "line_line_angle":
            f = {"kind": "line_line_angle", "points_a": _refs(a["line1"]), "points_b": _refs(a["line2"]),
                 "value": str(a["value"]), **({"angle_unit": str(a["unit"])} if a.get("unit") else {})}
        elif k == "vertex_angle":
            f = {"kind": "vertex_angle", "at": _ref(a["vertex"]), "points": _refs(a["rays"]),
                 "value": str(a["value"]), **({"angle_unit": str(a["unit"])} if a.get("unit") else {})}
        elif k == "face_area":
            f = {"kind": "polygon_area", "points": _refs(a["polygon"]), "value": str(a["value"]),
                 **({"shape": str(a["shape"])} if a.get("shape") and a.get("shape") != "polygon" else {})}
        elif k == "solid_volume":
            sid = a.get("solid") or prem.solid_id
            sol = solids.get(sid or "")
            if sol is None and sid is None and len(poly_root_solids) == 1:
                sol = poly_root_solids[0]
            f = {"kind": "solid_volume",
                 "solid": curved_sym.get(sol.solid_id, sol.notation) if sol else sid,
                 "value": str(a["value"])}
        elif k == "segment_ratio":
            f = {"kind": "segment_ratio", "points_a": _refs(a["segment_a"]), "points_b": _refs(a["segment_b"]),
                 "value": str(a["ratio"])}
        else:
            raise TuChoi("BRIDGE_UNSUPPORTED_PREMISE", f"{fid}: giả thiết {k!r} chưa có ánh xạ sang TypedFact", (fid,))
        facts.append({"id": _alloc_fact_id(fid, "prem"), "role": "premise", "quotes": q, **f})

    for r in p.relations:
        if r.kind == "coordinate_frame" and r.frame_id == "root":
            continue                                       # one root chart is what TypedFact always uses
        if r.kind == "perpendicular":
            facts.append({"id": _alloc_fact_id(r.relation_id, "rel"), "kind": "perpendicular", "role": "premise", "quotes": [r.quote],
                          "points_a": _refs(r.entity_a), "points_b": _refs(r.entity_b)})
            continue
        if r.kind == "shared_vertices" and all(_ref(x) == _ref(y) for x, y in r.pairs):
            continue                                       # identity bindings: shared labels ARE the shared points
        if r.kind == "shared_faces" and _refs(r.face_a) == _refs(r.face_b):
            continue
        if r.kind in ("circumscribes", "inscribed_in"):
            continue
        if r.kind == "tangent_to":
            facts.append({
                "id": _alloc_fact_id(r.relation_id, "rel"),
                "kind": "projection",
                "role": "premise",
                "quotes": [r.quote],
                "solid": curved_sym.get(r.solid_a, solids[r.solid_a].notation),
                "curved_part": {
                    "role": "tangent_plane",
                    "plane": _refs(r.entity_b),
                    "point": _ref(r.contact_ref) if getattr(r, "contact_ref", None) is not None else None,
                },
            })
            continue
        raise TuChoi("BRIDGE_UNSUPPORTED_RELATION", f"{r.relation_id}: quan hệ {r.kind} chưa diễn đạt được trong TypedFact",
                     (r.relation_id,))

    if is_standalone_curved:       # curved sections, the small cone and their goals (registry /24)
        return _ket_cau_noi(p, facts + _phan_cong(p, solids), version, scoped)
    asked = {}
    for g in p.simulation_goals:
        if g.kind == "construct_plane_section":
            asked.setdefault(g.target_section_id, []).append(g.quote)
        elif g.kind == "construct_intersection_line":
            # `/2` additive: the planner's existing `intersection_line` question (the facts route has served it since
            # hybrid-v2); the Source Gate grounds both planes in the quote, the engine proves the line exists and is unique.
            pa, pb = ([_ref(x) for x in pl] for pl in g.target_planes)
            facts.append({"id": g.goal_id, "kind": "intersection_line", "role": "question", "quotes": [g.quote],
                          "points_a": pa, "points_b": pb})
    sec_area_asked: dict[str, list[str]] = {}
    for g in p.math_goals:
        if g.goal_type == "area" and isinstance(g.target, dict) and "section_id" in g.target:
            sec_area_asked.setdefault(g.target["section_id"], []).append(g.quote)
    for sec in p.derived_sections:
        sec_asked = list(asked.get(sec.section_id, []))
        if not sec_asked and v2 and _la_mat_qua_ba_diem(sec) and "thiết diện" not in sec.quote.casefold():
            sec_asked = list(sec_area_asked.get(sec.section_id, []))
        facts.append(
            section_fact(sec, solids, sec_asked, p.problem_text, mo_ta)
            if v2 else section_fact(sec, solids, sec_asked)
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
        elif v2 and g.kind == "length_ratio":
            facts.append({**q, "quantity": "length_ratio",
                          "points_a": _refs(g.numerator_segment), "points_b": _refs(g.denominator_segment)})
        elif v2 and g.kind == "area_ratio":
            facts.append({**q, "quantity": "area_ratio",
                          "points_a": _refs(g.numerator_polygon), "points_b": _refs(g.denominator_polygon)})
        elif (is_poly_sphere_composite or is_axial_sphere_composite) and g.kind == "measurement" and measurement_scope(p, g) in curved:
            if set(g.target) <= {"solid", "solid_id"} and g.goal_type in ("volume", "area", "lateral_area", "radius"):
                msid = measurement_scope(p, g)
                facts.append({**q, "quantity": g.goal_type, "solid": curved_sym.get(msid, solids[msid].notation)})
            elif any(is_described_ref(x) for k in DESCRIBED_GOAL_KEYS if k in g.target
                     for x in (g.target[k] if isinstance(g.target[k], (list, tuple)) else [g.target[k]])):
                raise TuChoi("BRIDGE_UNSUPPORTED_DESCRIBED_POINT",
                             f"{g.goal_id}: mục tiêu của khối tròn xoay với điểm mô tả chưa có trên planner",
                             (g.goal_id,))
            else:
                raise TuChoi("BRIDGE_UNSUPPORTED_CURVED", f"{g.goal_id}: mục tiêu {g.kind}/{g.goal_type} của khối tròn xoay chưa có "
                             "trên planner", (g.goal_id,))
        elif g.goal_type == "volume" and measurement_scope(p, g) in solids:
            # F6: a notation / canonical alias names the same solid (validated by the schema policy, S2/S3)
            facts.append({**q, "quantity": "volume",
                          "solid": solids[measurement_scope(p, g)].notation})
        elif g.goal_type == "area" and "section_id" in g.target:
            sec = next((s for s in p.derived_sections if s.section_id == g.target["section_id"]), None)
            if sec is None:
                raise TuChoi("INVALID_MATH_GOAL", f"{g.goal_id}: thiết diện {g.target['section_id']!r} không có trong dữ kiện", (g.goal_id,))
            g_solid = g.solid_id or g.target.get("solid_id") or g.target.get("solid")
            if g_solid is not None:
                g_solid = resolve_solid_name(p, g_solid) or g_solid        # F6: notation alias of a declared solid
                if g_solid not in solids:
                    raise TuChoi("UNKNOWN_SOLID_ID", f"{g.goal_id}: khối {g_solid!r} không có", (g.goal_id,))
                if g_solid != sec.target_solid_id:
                    raise TuChoi("SOURCE_OBJECT_MISMATCH", f"{g.goal_id}: khối {g_solid!r} không khớp khối của thiết diện {sec.section_id!r}", (g.goal_id,))
            extra = _v2_plane_def_quotes(sec, p.problem_text) if v2 else []
            f = _mat_fact(sec, solids, [], mo_ta, extra_quotes=extra)
            if _la_mat_qua_ba_diem(sec) or (
                sec.plane_kind == "constrained" and any(is_described_ref(op) for c in sec.constraints for op in c.operands)
            ):     # "diện tích thiết diện đó": the plane is named where the section is stated
                q["quotes"] = list(dict.fromkeys([g.quote, sec.quote, *extra]))
            facts.append({**q, "quantity": "area", **{k: f[k] for k in ("solid", "point", "point_kind", "points",
                                                                         "point_tree", "plane_relation", "points_b",
                                                                         "points_a", "plane_name",
                                                                         "plane_constraints") if k in f}})
        elif v2 and (described := _cau_hoi_mo_ta(g, mo_ta)) is not None:
            facts.append({**q, **described})
        elif v2 and g.goal_type == "area" and isinstance(g.target, dict) and "polygon" in g.target:
            facts.append({**q, "quantity": "area", "points": _refs(g.target["polygon"])})
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
                                       "declared_plane_names": {s.section_id: _ten_mat_khai(s) for s in p.derived_sections},
                                       "output_policies": _output_policies_from_payload(p),
                                       "problem_text": p.problem_text}}


def quantity_premise_provenance(p: Any) -> list[dict[str, Any]]:
    """Extract `SOURCE_QUANTITY` dimension & span provenance for all quantity premises in `p` without rewriting premises."""
    from app.simulation.geometry.expression import FactRole, parse_quantity_expr
    from .typed_fact_next import parse_typed_fact_next_v2, premise_slot_dimension

    if isinstance(p, dict):
        p = parse_typed_fact_next_v2(p)

    records: list[dict[str, Any]] = []
    text = p.problem_text or ""
    for idx, prem in enumerate(p.premises, 1):
        fid = f"p{idx}"
        q_pos = text.find(prem.quote)
        for field_name in ("value", "side", "ratio"):
            if field_name not in prem.args or prem.args[field_name] is None:
                continue
            slot_dim = premise_slot_dimension(prem.kind, field_name)
            if slot_dim is None:
                continue
            raw_val = str(prem.args[field_name])
            in_q = prem.quote.rfind(raw_val)
            base_off = (q_pos + in_q) if (q_pos >= 0 and in_q >= 0) else 0
            qexpr = parse_quantity_expr(
                raw_val,
                base_offset=base_off,
                allow_signed=False,
                allow_unit=False,
                role=FactRole.SOURCE_QUANTITY,
            )
            records.append({
                "premise_id": fid,
                "kind": prem.kind,
                "field": field_name,
                "slot_dimension": slot_dim.name,
                "role": qexpr.provenance.role.value,
                "original_expr": qexpr.provenance.original_expr,
                "normalized_expr": qexpr.provenance.normalized_expr,
                "source_span": list(qexpr.provenance.source_span),
                "operand_spans": [[k, s, e] for k, s, e in qexpr.provenance.operand_spans],
            })
    return records
