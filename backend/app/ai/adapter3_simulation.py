# -*- coding: utf-8 -*-
"""Adapter /3 (`hybrid-simulation-adapter/3`) — Offline Research Simulation-First Orchestrator.

Consumes versioned `TypedFactNextPayload` (`typed-fact-next/1`), validates source grounding and
solid-qualified references, synthesizes unnamed section vertices and derived sub-solids on top
of the existing Wave 1–2C Geometry Functions Engine (`_Dung`) and Semantic Program Kernel, and
emits interactive `Scene3D` payloads as the primary output.

Coexists with `hybrid_preview.py` (`hybrid-preview-adapter/2`) without modifying it.
Default product mode (`LLM_ONLY`) and response contract (`flat`) remain untouched.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from fractions import Fraction
from itertools import combinations
import math
import re
from typing import Any

from app.simulation.geometry import kernel as K
from app.simulation.geometry import metric as _metric
from app.simulation.geometry.exact import GeometryError, Line3, Vec3
from app.simulation.geometry.predicates import (
    parallel_line_plane,
    parallel_planes,
    point_on_line,
)
from app.simulation.geometry.section import Polyhedron, kiem_mat_phang_don
from app.simulation.geometry_functions.engine import (
    BAC_DAI_LUONG,
    KetQuaTuyen,
    TuChoi,
    _binh_phuong,
    _Dung,
    _hien_thi_ky_hieu,
    _kiem_tren_hinh,
    dinh_dang,
    doc_ke_hoach,
    ir_name,
)
from app.simulation.geometry_functions.registry import (
    MAT_HAI_DUONG,
    MAT_SONG_SONG,
    MAT_VUONG_DUONG,
    binh_phuong,
    chuan_hoa,
    doc_so,
    nhan_cua_de,
    nhan_phu_da_dung,
    so_trong,
)
from app.simulation.geometry_functions.typed_fact_next import (
    _ARGS_LOI,
    resolve_solid_name,
    TYPED_FACT_NEXT_SCHEMA_VERSION,
    DerivedObjectIdentity,
    DerivedPlaneSectionSpec,
    GeometricRelationSpec,
    MathGoalSpec,
    PremiseSpec,
    SimulationGoalSpec,
    SolidSpec,
    TypedFactNextPayload,
    TypedFactNextValidationError,
    parse_qualified_ref,
    parse_typed_fact_next,
    measurement_scope,
)
from app.simulation.semantic_program.formation import hoan_thien_dung_hinh
from app.simulation.semantic_program.interpreter import SemanticProgramInterpreter
from app.simulation.semantic_program.request_contract import (
    PrismTopologySpec,
    PyramidTopologySpec,
    RequestContract,
)
from app.simulation.semantic_program.scene3d import build_scene3d
from app.simulation.semantic_program.simulation_state import build_simulation_state
from app.simulation.semantic_program.validator import validate_semantic_program

from app.ai.function_route import (
    _gan_nhan_chung_duong_cao_chinh_xac,
    _gan_nhan_chung_hinh_chieu,
    _ke_diem_dung,
)

ADAPTER_V3_VERSION = "hybrid-simulation-adapter/3"
ROUTE_D_SIMULATION_SCHEMA_VERSION = "hybrid-route-d-simulation/3"
HYBRID_PREVIEW_SCHEMA_VERSION = "hybrid-Flat-preview/1"


@dataclass
class Adapter3SimulationResult:
    """Structured result of Adapter /3 (`run_typed_fact_next_route`)."""

    status: str  # "SERVED" | "REFUSED"
    code: str | None = None
    reason: str | None = None
    failed_calls: tuple[str, ...] = ()
    scene3d: dict[str, Any] | None = None
    simulation_state: dict[str, Any] | None = None
    solids: list[dict[str, Any]] = field(default_factory=list)
    derived_identities: list[dict[str, Any]] = field(default_factory=list)
    verified_relations: list[dict[str, Any]] = field(default_factory=list)
    simulation_goals: list[dict[str, Any]] = field(default_factory=list)
    math_goals: list[dict[str, Any]] = field(default_factory=list)
    answers: dict[str, str] = field(default_factory=dict)
    answer_exact: dict[str, dict[str, Any]] = field(default_factory=dict)
    length_unit: str | None = None
    source_verification: dict[str, Any] | None = None
    points: dict[str, tuple[Fraction, Fraction, Fraction]] = field(default_factory=dict)
    metric: dict[str, Any] | None = None
    kernel_check: bool = False
    trace: list[dict[str, Any]] = field(default_factory=list)
    calls: list[dict[str, Any]] = field(default_factory=list)


def _alloc_labels(occupied: set[str], prefix: str, count: int = 1) -> list[str]:
    out: list[str] = []
    idx = 1
    while len(out) < count:
        cand = f"{prefix}{idx}"
        if cand not in occupied:
            occupied.add(cand)
            out.append(cand)
        idx += 1
    return out


def _verify_quote_in_problem(quote: str, problem_text: str, context_id: str) -> None:
    norm_text = chuan_hoa(problem_text)
    norm_quote = chuan_hoa(quote)
    if not norm_quote or norm_quote not in norm_text:
        raise TuChoi(
            "SOURCE_QUOTE_NOT_FOUND",
            f"{context_id}: trích dẫn {quote!r} không xuất hiện nguyên văn trong đề bài",
            (context_id,),
        )


def _verify_number_in_quote(value_str: str, quote: str, context_id: str) -> None:
    try:
        val, sym = doc_so(str(value_str))
    except Exception as exc:
        raise TuChoi(
            "INVALID_NUMBER_VALUE",
            f"{context_id}: giá trị {value_str!r} không đọc được ({exc})",
            (context_id,),
        ) from None
    nums = [(v, s) for _, v, s in so_trong(chuan_hoa(quote))]
    if (val, sym) not in nums:
        # Also allow ratio strings like "1/3" if numerator and denominator or ratio appear
        if "/" in str(value_str):
            parts = [Fraction(p) for p in str(value_str).split("/") if p.strip().isdigit()]
            raw_vals = [v for v, _ in nums]
            if len(parts) == 2 and all(p in raw_vals for p in parts):
                return
        raise TuChoi(
            "SOURCE_NUMBER_MISMATCH",
            f"{context_id}: giá trị {value_str!r} không khớp số nào trong trích dẫn {quote!r}",
            (context_id,),
        )


#: Source authority of a served Adapter /3 result (run `backend-hybrid-contract-unification`).
SOURCE_GATE_AUTHORITY = "registry.kiem_nguon"
LEGACY_SOURCE_AUTHORITY = "adapter3.substring_legacy"

# Capability gaps with an existing Adapter /3 implementation; semantic refusals are never fallback signals.
_LEGACY_BRIDGE_CAPABILITIES = frozenset({
    'BRIDGE_UNSUPPORTED_CURVED', 'BRIDGE_UNSUPPORTED_QUALIFIED_IDENTITY', 'BRIDGE_UNSUPPORTED_PLANE_KIND',
    'BRIDGE_UNSUPPORTED_PREMISE', 'BRIDGE_UNSUPPORTED_RELATION', 'BRIDGE_UNSUPPORTED_DERIVED_SOLID',
    'BRIDGE_CUT_EDGES_NOT_STATED', 'BRIDGE_UNSUPPORTED_MEASUREMENT',
})
_LEGACY_PLANNER_CAPABILITIES = frozenset({'UNSUPPORTED_CAPABILITY'})


def _shared_source_gate(payload: TypedFactNextPayload) -> dict[str, Any]:
    """ONE source authority where it can read the payload (run `backend-hybrid-contract-unification`): the stated facts of
    a polyhedral payload reach the Registry Source Gate (`kiem_nguon`) through the pure bridge and the planner — the path of
    `run_typed_fact_next_planner_route` minus the engine — before Adapter /3 builds anything. A gate refusal is Adapter /3's
    refusal, with the gate's code. A payload the bridge / planner cannot express has NO gate verdict: Adapter /3 still runs
    its legacy identity / quote / number checks only for enumerated capability gaps. All semantic/provenance refusals
    are terminal (Owner W3-F2 Adapter3 safety amendment); an unclassified refusal is never a fallback signal."""
    from app.simulation.geometry_functions.planner import lap_ke_hoach
    from app.simulation.geometry_functions.registry import kiem_nguon
    from app.simulation.geometry_functions.typed_fact_next_bridge import bridge

    try:
        facts = bridge(payload)["facts"]
    except TuChoi as exc:
        if exc.code not in _LEGACY_BRIDGE_CAPABILITIES:
            raise
        return {"authority": LEGACY_SOURCE_AUTHORITY, "gate_unavailable": exc.code}
    except (KeyError, TypeError):                        # bridge INPUT parsing only (run `hybrid-contract-v2`, P1)
        raise TuChoi("INVALID_TYPED_FACT_NEXT", "đối số giả thiết bị thiếu hoặc sai kiểu") from None
    try:
        k = lap_ke_hoach({"facts": facts}, payload.problem_text)    # a planner fault is ours: it reaches the boundary
    except TuChoi as exc:
        if exc.code not in _LEGACY_PLANNER_CAPABILITIES:
            raise
        return {"authority": LEGACY_SOURCE_AUTHORITY, "gate_unavailable": exc.code}
    read = tuple(q for g in (*k.goals, *k.negated) if g.get("call") for q in g["call"]["source"]["quotes"])
    kiem_nguon(doc_ke_hoach({"calls": k.calls}), payload.problem_text, tuple(k.auxiliary), read)
    return {"authority": SOURCE_GATE_AUTHORITY}


def _solid_faces(solid: SolidSpec, canonical_map: dict[str, str]) -> list[frozenset[str]]:
    if solid.solid_type == "pyramid":
        apex, base = solid.apex_and_base()
        c_apex = canonical_map[apex]
        c_base = [canonical_map[b] for b in base]
        faces = [frozenset(c_base)]
        n = len(c_base)
        for i in range(n):
            faces.append(frozenset((c_apex, c_base[i], c_base[(i + 1) % n])))
        return faces
    b1, b2 = solid.prism_bases()
    c_b1 = [canonical_map[b] for b in b1]
    c_b2 = [canonical_map[t] for t in b2]
    faces = [frozenset(c_b1), frozenset(c_b2)]
    n = len(c_b1)
    for i in range(n):
        j = (i + 1) % n
        faces.append(frozenset((c_b1[i], c_b1[j], c_b2[j], c_b2[i])))
    return faces


class _Adapter3Compiler:
    """Stateful compiler from `TypedFactNextPayload` to verified `_Dung` + `Scene3D`."""

    def __init__(self, payload: TypedFactNextPayload) -> None:
        self.payload = payload
        self.problem_text = payload.problem_text
        self.text_labels = nhan_cua_de(self.problem_text)
        self.occupied_labels: set[str] = set(self.text_labels)
        for ch in ("H", "X", "F", "I", "O", "K", "E", "G"):
            self.occupied_labels |= nhan_phu_da_dung(self.problem_text, ch)

        self.solid_specs: dict[str, SolidSpec] = {}
        self.solid_local_to_canonical: dict[str, dict[str, str]] = {}
        self.solid_canonical_name: dict[str, str] = {}
        self.solid_topology_contracts: dict[frozenset[str], RequestContract] = {}
        self.unqualified_map: dict[str, set[str]] = {}
        self.qualified_point_meta: dict[str, dict[str, Any]] = {}

        self.calls: list[dict[str, Any]] = []
        self.mat_phu: list[dict[str, Any]] = []
        self.ten_mat_phu: dict[str, str] = {}
        self.aux_hidden_points: set[str] = set()

        self.derived_identities: list[DerivedObjectIdentity] = []
        self.derived_by_id: dict[str, DerivedObjectIdentity] = {}
        self.derived_point_by_symbol: dict[str, DerivedObjectIdentity] = {}
        self.derived_solid_by_canonical: dict[str, DerivedObjectIdentity] = {}

        self.section_cycles: dict[str, tuple[str, ...]] = {}
        self.section_plane_triples: dict[str, tuple[str, str, str]] = {}
        self.section_call_ids: dict[str, str] = {}
        self.section_object_ids: dict[str, str] = {}
        self.section_plane_object_ids: dict[str, str] = {}
        self.section_cut_checks: list[dict[str, Any]] = []
        self.point_on_segment_provenance: dict[str, tuple[str, str]] = {}
        self._call_seq = 0

    def _next_call_id(self, prefix: str = "c") -> str:
        self._call_seq += 1
        return f"{prefix}{self._call_seq}"

    def _register_derived(self, item: DerivedObjectIdentity) -> None:
        if item.derived_id in self.derived_by_id:
            raise TuChoi(
                "DUPLICATE_DERIVED_ID",
                f"Trùng định danh đối tượng dẫn xuất {item.derived_id!r}",
                (item.derived_id,),
            )
        self.derived_by_id[item.derived_id] = item
        self.derived_identities.append(item)
        if item.kind == "section_vertex":
            self.derived_point_by_symbol[item.internal_symbol] = item
        elif item.kind == "derived_solid":
            self.derived_solid_by_canonical[item.internal_symbol] = item

    def _bind_local_point(self, solid_id: str | None, local_label: str, canonical_label: str) -> None:
        self.occupied_labels.add(local_label)
        self.occupied_labels.add(canonical_label)
        self.unqualified_map.setdefault(local_label, set()).add(canonical_label)
        if solid_id:
            self.solid_local_to_canonical.setdefault(solid_id, {})[local_label] = canonical_label
            if local_label != canonical_label:
                self.qualified_point_meta[canonical_label] = {
                    "binding": "SOLID_QUALIFIED_VERTEX",
                    "solid_id": solid_id,
                    "local_notation": local_label,
                    "canonical_symbol": canonical_label,
                    "qualified_ref": f"{solid_id}::{local_label}",
                }

    def resolve_ref(self, ref: str, default_solid_id: str | None = None, context_id: str = "ref") -> str:
        try:
            explicit_sid, label = parse_qualified_ref(ref)
        except TypedFactNextValidationError as exc:
            raise TuChoi(exc.code, exc.detail, (context_id,)) from None

        sid = explicit_sid or default_solid_id
        if default_solid_id is not None and default_solid_id not in self.solid_canonical_name:
            raise TuChoi('UNKNOWN_SOLID_ID', f'{context_id}: khối {default_solid_id!r} chưa được khai báo', (context_id,))
        if explicit_sid is not None and default_solid_id is not None and explicit_sid != default_solid_id:
            raise TuChoi('SOURCE_OBJECT_MISMATCH', f'{context_id}: tham chiếu khác phạm vi khối đã khai', (context_id,))
        if explicit_sid is not None:
            if explicit_sid not in self.solid_canonical_name:
                raise TuChoi(
                    "UNKNOWN_SOLID_ID",
                    f"{context_id}: khối {explicit_sid!r} trong tham chiếu {ref!r} chưa được khai báo",
                    (context_id,),
                )
            smap = self.solid_local_to_canonical.get(explicit_sid, {})
            if label not in smap:
                raise TuChoi(
                    "UNKNOWN_VERTEX_REF",
                    f"{context_id}: đỉnh {label!r} không thuộc phạm vi khối {explicit_sid!r}",
                    (context_id,),
                )
            return smap[label]

        if sid is not None:
            if label in self.solid_local_to_canonical.get(sid, {}):
                return self.solid_local_to_canonical[sid][label]
            derived = self.derived_by_id.get(label)
            if derived is not None and derived.provenance.get('parent_solid_id') == sid:
                return derived.internal_symbol
            raise TuChoi('SOURCE_OBJECT_MISMATCH', f'{context_id}: đỉnh {label!r} không thuộc phạm vi {sid!r}', (context_id,))

        cands = self.unqualified_map.get(label, set())
        if len(cands) > 1:
            raise TuChoi(
                "AMBIGUOUS_REFERENCE",
                f"{context_id}: tham chiếu không định danh khối {label!r} nhập nhằng giữa các đỉnh {sorted(cands)}",
                (context_id,),
            )
        if len(cands) == 1:
            return next(iter(cands))
        if label in self.derived_by_id:
            return self.derived_by_id[label].internal_symbol
        raise TuChoi(
            "UNKNOWN_LABEL",
            f"{context_id}: đỉnh {ref!r} chưa được khai báo trong khối hoặc giả thiết nào",
            (context_id,),
        )

    def _compile_solids(self) -> None:
        for solid in self.payload.solids:
            _verify_quote_in_problem(solid.quote, self.problem_text, solid.solid_id)
            local_verts = solid.local_vertices()
            for lv in local_verts:
                if lv not in self.text_labels:
                    raise TuChoi(
                        "UNKNOWN_LABEL",
                        f"{solid.solid_id}: đỉnh {lv!r} trong {solid.notation!r} không có trong đề bài",
                        (solid.solid_id,),
                    )
            smap: dict[str, str] = {}
            for lv in local_verts:
                cv = solid.canonical_vertex(lv)
                smap[lv] = cv
                self._bind_local_point(solid.solid_id, lv, cv)
            if len(set(smap.values())) != len(local_verts):
                raise TuChoi(
                    "INVALID_VERTEX_BINDING",
                    f"{solid.solid_id}: hai đỉnh cục bộ ánh xạ vào cùng một đỉnh chính tắc",
                    (solid.solid_id,),
                )
            self.solid_specs[solid.solid_id] = solid
            self.solid_local_to_canonical[solid.solid_id] = smap

            cid = self._next_call_id("solid")
            if solid.solid_type == "pyramid":
                apex, base = solid.apex_and_base()
                c_apex = smap[apex]
                c_base = [smap[b] for b in base]
                c_name = f"{c_apex}.{''.join(c_base)}"
                self.solid_canonical_name[solid.solid_id] = c_name
                self.calls.append(
                    {
                        "id": cid,
                        "fn": "pyramid",
                        "args": {"apex": c_apex, "base": c_base},
                        "source": {"quotes": [solid.quote, c_name]},
                    }
                )
                key = frozenset(map(ir_name, [c_apex, *c_base]))
                self.solid_topology_contracts[key] = RequestContract(
                    solid_topology=PyramidTopologySpec(apex=c_apex, base_cycle=tuple(c_base))
                )
            else:
                b1, b2 = solid.prism_bases()
                c_b1 = [smap[b] for b in b1]
                c_b2 = [smap[t] for t in b2]
                c_name = f"{''.join(c_b1)}.{''.join(c_b2)}"
                self.solid_canonical_name[solid.solid_id] = c_name
                self.calls.append(
                    {
                        "id": cid,
                        "fn": "prism",
                        "args": {"base": c_b1, "top": c_b2, "right": False},
                        "source": {"quotes": [solid.quote, c_name]},
                    }
                )
                key = frozenset(map(ir_name, [*c_b1, *c_b2]))
                self.solid_topology_contracts[key] = RequestContract(
                    solid_topology=PrismTopologySpec(
                        base_cycle=tuple(c_b1),
                        top_cycle=tuple(c_b2),
                        correspondence=tuple(zip(c_b1, c_b2)),
                        lateral_structure=None,
                    )
                )

    def _resolve_solid_canonical_name(self, solid_ref: str, context_id: str) -> str:
        if solid_ref in self.solid_canonical_name:
            return self.solid_canonical_name[solid_ref]
        for sid, cname in self.solid_canonical_name.items():
            if solid_ref == cname or solid_ref == self.solid_specs[sid].notation:
                return cname
        raise TuChoi(
            "UNKNOWN_SOLID_ID",
            f"{context_id}: không tìm thấy khối {solid_ref!r}",
            (context_id,),
        )

    def _scoped_solid_name(self, named: str | None, scope: str | None, context_id: str) -> str:
        """A solid-valued operand (id, canonical name or notation) never overrides the declared scope."""
        if scope is not None and scope not in self.solid_canonical_name:
            raise TuChoi("UNKNOWN_SOLID_ID", f"{context_id}: khối {scope!r} chưa được khai báo", (context_id,))
        name = self._resolve_solid_canonical_name(named or scope or "", context_id)
        if scope is not None and name != self.solid_canonical_name[scope]:
            raise TuChoi("SOURCE_OBJECT_MISMATCH", f"{context_id}: khối trong toán hạng khác phạm vi đã khai",
                         (context_id,))
        return name

    def _compile_premises(self) -> None:
        for idx, prem in enumerate(self.payload.premises, start=1):
            pid = f"p{idx}"
            _verify_quote_in_problem(prem.quote, self.problem_text, pid)
            sid = prem.solid_id
            if sid is not None and sid not in self.solid_specs:
                raise TuChoi(
                    "UNKNOWN_SOLID_ID",
                    f"{pid}: solid_id {sid!r} chưa được khai báo",
                    (pid,),
                )
            kind = prem.kind
            a = dict(prem.args)

            def R(ref: str) -> str:
                return self.resolve_ref(ref, sid, pid)

            def R_new(ref: str) -> str:
                explicit_sid, label = parse_qualified_ref(ref)
                if explicit_sid is not None and explicit_sid not in self.solid_specs:
                    raise TuChoi('UNKNOWN_SOLID_ID', f'{pid}: khối của điểm dựng chưa được khai báo', (pid,))
                if explicit_sid is not None and sid is not None and explicit_sid != sid:
                    raise TuChoi('SOURCE_OBJECT_MISMATCH', f'{pid}: điểm dựng khác phạm vi premise', (pid,))
                if label not in self.text_labels:
                    raise TuChoi(
                        "UNKNOWN_LABEL",
                        f"{pid}: điểm {label!r} không xuất hiện trong đề bài",
                        (pid,),
                    )
                target_sid = explicit_sid or sid
                if target_sid is None:
                    output = 'image' if kind in ('orthogonal_projection','point_is_foot','orthogonal_projection_line') else \
                             'foot' if kind == 'altitude' else 'point'
                    inputs = [r for key, shape in _ARGS_LOI[kind].items() if shape.startswith('ref') and key != output and key in a
                              for r in (a[key] if shape.startswith('refs') else [a[key]])]
                    owners = [{s for s, smap in self.solid_local_to_canonical.items()
                               if smap.get(parse_qualified_ref(r)[1]) == self.resolve_ref(r, None, pid)
                               and parse_qualified_ref(r)[0] in (None, s)} for r in inputs]
                    common = set.intersection(*owners) if owners else set()
                    if len(common) != 1:
                        raise TuChoi('AMBIGUOUS_REFERENCE', f'{pid}: không xác định duy nhất khối của điểm dựng', (pid,))
                    target_sid = next(iter(common))
                if target_sid and label in self.solid_local_to_canonical.get(target_sid, {}):
                    return self.solid_local_to_canonical[target_sid][label]
                foreign = {s for s, smap in self.solid_local_to_canonical.items() if smap.get(label) == label}
                shared = kind in ('midpoint','point_is_midpoint','divide_segment','point_divides_segment','centroid','point_is_centroid') and any(
                    rel.kind == 'shared_faces' and target_sid in (rel.solid_a, rel.solid_b)
                    and foreign.intersection((rel.solid_a, rel.solid_b)) for rel in self.payload.relations)
                if foreign and not shared:
                    raise TuChoi('SOURCE_OBJECT_MISMATCH', f'{pid}: điểm dựng đã thuộc khối khác', (pid,))
                self._bind_local_point(target_sid, label, label)
                return label

            if kind == "regular_pyramid":
                apex = R(a["apex"])
                base = [R(x) for x in a["base"]]
                self.calls.append(
                    {
                        "id": pid,
                        "fn": "regular_pyramid",
                        "args": {"apex": apex, "base": base},
                        "source": {"quotes": [prem.quote]},
                    }
                )
            elif kind == "right_prism":
                base = [R(x) for x in a["base"]]
                top = [R(x) for x in a["top"]]
                updated = False
                for existing in self.calls:
                    if (
                        existing["fn"] == "prism"
                        and existing["args"]["base"] == base
                        and existing["args"]["top"] == top
                    ):
                        existing["args"]["right"] = True
                        updated = True
                if not updated:
                    self.calls.append(
                        {
                            "id": pid,
                            "fn": "prism",
                            "args": {"base": base, "top": top, "right": True},
                            "source": {"quotes": [prem.quote]},
                        }
                    )
                key = frozenset(map(ir_name, [*base, *top]))
                self.solid_topology_contracts[key] = RequestContract(
                    solid_topology=PrismTopologySpec(
                        base_cycle=tuple(base),
                        top_cycle=tuple(top),
                        correspondence=tuple(zip(base, top)),
                        lateral_structure="right",
                    )
                )
            elif kind in ("regular_polygon", "base_is_square", "base_is_equilateral_triangle", "base_is_regular_polygon"):
                verts = [R(x) for x in a["vertices"]]
                side = a.get("side")
                if side is not None:
                    _verify_number_in_quote(str(side), prem.quote, pid)
                self.calls.append(
                    {
                        "id": pid,
                        "fn": "regular_polygon",
                        "args": {"vertices": verts, "side": str(side) if side is not None else None},
                        "source": {"quotes": [prem.quote]},
                    }
                )
            elif kind in ("rectangle", "base_is_rectangle"):
                verts = [R(x) for x in a["vertices"]]
                self.calls.append(
                    {
                        "id": pid,
                        "fn": "rectangle",
                        "args": {"vertices": verts},
                        "source": {"quotes": [prem.quote]},
                    }
                )
            elif kind in ("right_angle", "base_is_right_triangle"):
                if "vertices" in a:
                    verts = [R(x) for x in a["vertices"]]
                    vtx = R(a["right_at"])
                    rays = [v for v in verts if v != vtx]
                else:
                    vtx = R(a["vertex"])
                    rays = [R(x) for x in a["rays"]]
                self.calls.append(
                    {
                        "id": pid,
                        "fn": "right_angle",
                        "args": {"vertex": vtx, "rays": rays},
                        "source": {"quotes": [prem.quote]},
                    }
                )
            elif kind == "segment_length":
                seg = [R(x) for x in a["segment"]]
                val = str(a["value"])
                _verify_number_in_quote(val, prem.quote, pid)
                self.calls.append(
                    {
                        "id": pid,
                        "fn": "segment_length",
                        "args": {"segment": seg, "value": val},
                        "source": {"quotes": [prem.quote]},
                    }
                )
            elif kind in ("equal_length", "equal_segments"):
                seg_a = [R(x) for x in a["segment_a"]]
                seg_b = [R(x) for x in a["segment_b"]]
                self.calls.append(
                    {
                        "id": pid,
                        "fn": "equal_length",
                        "args": {"segment_a": seg_a, "segment_b": seg_b},
                        "source": {"quotes": [prem.quote]},
                    }
                )
            elif kind in ("perpendicular_line_plane", "line_perp_plane"):
                line = [R(x) for x in a["line"]]
                plane = [R(x) for x in a["plane"]]
                self.calls.append(
                    {
                        "id": pid,
                        "fn": "perpendicular_line_plane",
                        "args": {"line": line, "plane": plane},
                        "source": {"quotes": [prem.quote]},
                    }
                )
            elif kind in ("perpendicular_lines", "line_perp_line"):
                l1 = [R(x) for x in a["line1"]]
                l2 = [R(x) for x in a["line2"]]
                self.calls.append(
                    {
                        "id": pid,
                        "fn": "perpendicular_lines",
                        "args": {"line1": l1, "line2": l2},
                        "source": {"quotes": [prem.quote]},
                    }
                )
            elif kind in ("face_perpendicular_base", "plane_perp_base"):
                face = [R(x) for x in a["face"]]
                base = [R(x) for x in a["base"]]
                self.calls.append(
                    {
                        "id": pid,
                        "fn": "face_perpendicular_base",
                        "args": {"face": face, "base": base},
                        "source": {"quotes": [prem.quote]},
                    }
                )
            elif kind == "altitude":
                solid_name = self._scoped_solid_name(a.get("solid"), sid, pid)
                apex = R(a["apex"])
                foot = R_new(a["foot"])
                self.calls.append(
                    {
                        "id": pid,
                        "fn": "altitude",
                        "args": {"solid": solid_name, "apex": apex, "foot": foot},
                        "source": {"quotes": [prem.quote]},
                    }
                )
            elif kind == "height":
                solid_name = self._scoped_solid_name(a.get("solid"), sid, pid)
                val = str(a["value"])
                _verify_number_in_quote(val, prem.quote, pid)
                self.calls.append(
                    {
                        "id": pid,
                        "fn": "height",
                        "args": {"solid": solid_name, "value": val},
                        "source": {"quotes": [prem.quote]},
                    }
                )
            elif kind in ("midpoint", "point_is_midpoint"):
                seg = [R(x) for x in a["segment"]]
                pt = R_new(a["point"])
                self.point_on_segment_provenance[pt] = (seg[0], seg[1])
                self.calls.append(
                    {
                        "id": pid,
                        "fn": "midpoint",
                        "args": {"point": pt, "segment": seg},
                        "source": {"quotes": [prem.quote]},
                    }
                )
            elif kind in ("divide_segment", "point_divides_segment"):
                seg = [R(x) for x in a["segment"]]
                pt = R_new(a["point"])
                ratio = str(a["ratio"])
                _verify_number_in_quote(ratio, prem.quote, pid)
                self.point_on_segment_provenance[pt] = (seg[0], seg[1])
                self.calls.append(
                    {
                        "id": pid,
                        "fn": "divide_segment",
                        "args": {"point": pt, "segment": seg, "ratio": ratio},
                        "source": {"quotes": [prem.quote]},
                    }
                )
            elif kind in ("centroid", "point_is_centroid"):
                poly = [R(x) for x in a["polygon"]]
                pt = R_new(a["point"])
                self.calls.append(
                    {
                        "id": pid,
                        "fn": "centroid",
                        "args": {"point": pt, "polygon": poly},
                        "source": {"quotes": [prem.quote]},
                    }
                )
            elif kind in ("orthogonal_projection", "point_is_foot"):
                pt = R(a["point"])
                img = R_new(a["image"])
                plane = [R(x) for x in a["plane"]]
                self.calls.append(
                    {
                        "id": pid,
                        "fn": "orthogonal_projection",
                        "args": {"point": pt, "image": img, "plane": plane},
                        "source": {"quotes": [prem.quote]},
                    }
                )
            elif kind == "orthogonal_projection_line":
                pt = R(a["point"])
                img = R_new(a["image"])
                line = [R(x) for x in a["line"]]
                self.point_on_segment_provenance[img] = (line[0], line[1])
                self.calls.append(
                    {
                        "id": pid,
                        "fn": "orthogonal_projection_line",
                        "args": {"point": pt, "line": line, "image": img},
                        "source": {"quotes": [prem.quote]},
                    }
                )
            elif kind == "intersect_line_line":
                pt = R_new(a["point"])
                l1 = [R(x) for x in a["line1"]]
                l2 = [R(x) for x in a["line2"]]
                self.calls.append(
                    {
                        "id": pid,
                        "fn": "intersect_line_line",
                        "args": {"point": pt, "line1": l1, "line2": l2},
                        "source": {"quotes": [prem.quote]},
                    }
                )
            elif kind == "intersect_line_plane":
                pt = R_new(a["point"])
                line = [R(x) for x in a["line"]]
                plane = [R(x) for x in a["plane"]]
                self.point_on_segment_provenance[pt] = (line[0], line[1])
                self.calls.append(
                    {
                        "id": pid,
                        "fn": "intersect_line_plane",
                        "args": {"point": pt, "line": line, "plane": plane},
                        "source": {"quotes": [prem.quote]},
                    }
                )
            else:
                raise TuChoi(
                    "UNSUPPORTED_PREMISE_KIND",
                    f"{pid}: chưa hỗ trợ loại giả thiết {kind!r} trong Adapter /3",
                    (pid,),
                )

    def _compile_derived_sections(self) -> None:
        for sec in self.payload.derived_sections:
            _verify_quote_in_problem(sec.quote, self.problem_text, sec.section_id)
            if sec.plane_kind not in ("through_point_parallel_plane", "through_point_parallel_two_lines",
                                      "through_point_perpendicular_line"):
                raise TuChoi("UNSUPPORTED_PLANE_KIND", f"{sec.section_id}: mặt {sec.plane_kind} chưa có phép dựng trên khối "
                             "đa diện", (sec.section_id,))
            sid = sec.target_solid_id
            solid = self.solid_specs[sid]
            smap = self.solid_local_to_canonical[sid]
            solid_cname = self.solid_canonical_name[sid]

            p0 = self.resolve_ref(sec.through_point, sid, sec.section_id)
            x1, x2 = _alloc_labels(self.occupied_labels, "X", 2)
            self.aux_hidden_points.update((x1, x2))

            sec_call_id = self._next_call_id("sec")
            self.section_call_ids[sec.section_id] = sec_call_id

            if sec.plane_kind == "through_point_parallel_plane":
                assert sec.parallel_plane is not None
                q0, q1, q2 = (self.resolve_ref(p, sid, sec.section_id) for p in sec.parallel_plane)
                t1_id = self._next_call_id("tp")
                t2_id = self._next_call_id("tp")
                self.calls.append(
                    {
                        "id": t1_id,
                        "fn": "translate_point",
                        "args": {"point": p0, "vector": [q0, q1], "image": x1},
                        "source": {"quotes": [sec.quote]},
                    }
                )
                self.calls.append(
                    {
                        "id": t2_id,
                        "fn": "translate_point",
                        "args": {"point": p0, "vector": [q0, q2], "image": x2},
                        "source": {"quotes": [sec.quote]},
                    }
                )
                self.mat_phu.append(
                    {
                        "rule": MAT_SONG_SONG,
                        "point": p0,
                        "parallel_to": [q0, q1, q2],
                        "labels": [x1, x2],
                        "constructs": [t1_id, t2_id],
                        "targets": [sec_call_id],
                    }
                )
                self.ten_mat_phu[t1_id] = sec.plane_name
                plane_deps = (p0, q0, q1, q2)
            elif sec.plane_kind == "through_point_parallel_two_lines":
                assert sec.parallel_line_a is not None and sec.parallel_line_b is not None
                la = [self.resolve_ref(p, sid, sec.section_id) for p in sec.parallel_line_a]
                lb = [self.resolve_ref(p, sid, sec.section_id) for p in sec.parallel_line_b]
                t1_id = self._next_call_id("tp")
                t2_id = self._next_call_id("tp")
                self.calls.append(
                    {
                        "id": t1_id,
                        "fn": "translate_point",
                        "args": {"point": p0, "vector": la, "image": x1},
                        "source": {"quotes": [sec.quote]},
                    }
                )
                self.calls.append(
                    {
                        "id": t2_id,
                        "fn": "translate_point",
                        "args": {"point": p0, "vector": lb, "image": x2},
                        "source": {"quotes": [sec.quote]},
                    }
                )
                self.mat_phu.append(
                    {
                        "rule": MAT_HAI_DUONG,
                        "point": p0,
                        "lines": [la, lb],
                        "labels": [x1, x2],
                        "plane_name": sec.plane_name,
                        "constructs": [t1_id, t2_id],
                        "targets": [sec_call_id],
                    }
                )
                self.ten_mat_phu[t1_id] = sec.plane_name
                plane_deps = (p0, *la, *lb)
            else:
                assert sec.perpendicular_line is not None
                l0, l1 = (self.resolve_ref(p, sid, sec.section_id) for p in sec.perpendicular_line)
                all_solid_pts = [smap[v] for v in solid.local_vertices()]
                off_line = [v for v in all_solid_pts if v not in (l0, l1)]
                if len(off_line) < 2:
                    raise TuChoi(
                        "PLANE_NOT_UNIQUE",
                        f"{sec.section_id}: không đủ đỉnh ngoài đường {l0}{l1} để dựng mặt vuông góc",
                        (sec.section_id,),
                    )
                z1, z2 = off_line[0], off_line[1]
                f1, f2 = _alloc_labels(self.occupied_labels, "F", 2)
                self.aux_hidden_points.update((f1, f2))
                f1_id = self._next_call_id("fp")
                f2_id = self._next_call_id("fp")
                t1_id = self._next_call_id("tp")
                t2_id = self._next_call_id("tp")
                self.calls.append(
                    {
                        "id": f1_id,
                        "fn": "orthogonal_projection_line",
                        "args": {"point": z1, "line": [l0, l1], "image": f1},
                        "source": {"quotes": [sec.quote]},
                    }
                )
                self.calls.append(
                    {
                        "id": f2_id,
                        "fn": "orthogonal_projection_line",
                        "args": {"point": z2, "line": [l0, l1], "image": f2},
                        "source": {"quotes": [sec.quote]},
                    }
                )
                self.calls.append(
                    {
                        "id": t1_id,
                        "fn": "translate_point",
                        "args": {"point": p0, "vector": [f1, z1], "image": x1},
                        "source": {"quotes": [sec.quote]},
                    }
                )
                self.calls.append(
                    {
                        "id": t2_id,
                        "fn": "translate_point",
                        "args": {"point": p0, "vector": [f2, z2], "image": x2},
                        "source": {"quotes": [sec.quote]},
                    }
                )
                self.mat_phu.append(
                    {
                        "rule": MAT_VUONG_DUONG,
                        "point": p0,
                        "perpendicular_to": [l0, l1],
                        "chosen": [z1, z2],
                        "feet": [f1, f2],
                        "labels": [x1, x2],
                        "constructs": [f1_id, f2_id, t1_id, t2_id],
                        "targets": [sec_call_id],
                    }
                )
                self.ten_mat_phu[f1_id] = sec.plane_name
                plane_deps = (p0, l0, l1)

            plane_derived_id = f"plane:{sec.section_id}"
            self._register_derived(
                DerivedObjectIdentity(
                    derived_id=plane_derived_id,
                    kind="plane",
                    internal_symbol=f"mp_td_{sec_call_id}",
                    display_label=f"Mặt phẳng ({sec.plane_name})",
                    reference_text=f"mặt phẳng ({sec.plane_name})",
                    notation=f"({sec.plane_name})",
                    anonymous_in_source=False,
                    dependencies=plane_deps,
                    provenance={
                        "section_id": sec.section_id,
                        "plane_kind": sec.plane_kind,
                        "quote": sec.quote,
                    },
                )
            )

            self.calls.append(
                {
                    "id": sec_call_id,
                    "fn": "section",
                    "args": {"solid": solid_cname, "plane": [p0, x1, x2]},
                    "source": {"quotes": [sec.quote]},
                }
            )
            self.section_plane_triples[sec.section_id] = (p0, x1, x2)

            # Determine cut edges in cyclic order
            if sec.cut_edges:
                cut_edges = [
                    (
                        self.resolve_ref(u, sid, sec.section_id),
                        self.resolve_ref(v, sid, sec.section_id),
                    )
                    for u, v in sec.cut_edges
                ]
            elif solid.solid_type == "pyramid":
                apex, base = solid.apex_and_base()
                c_apex = smap[apex]
                cut_edges = [(c_apex, smap[b]) for b in base]
            else:
                b1, b2 = solid.prism_bases()
                cut_edges = [(smap[u], smap[v]) for u, v in zip(b1, b2)]

            cycle_pts: list[str] = []
            for u, v in cut_edges:
                edge_set = frozenset((u, v))
                p0_seg = self.point_on_segment_provenance.get(p0)
                if p0 in edge_set or (p0_seg is not None and frozenset(p0_seg) == edge_set):
                    cycle_pts.append(p0)
                    self.section_cut_checks.append(
                        {
                            "section_id": sec.section_id,
                            "point": p0,
                            "edge": (u, v),
                            "anonymous": False,
                        }
                    )
                    continue

                named_lbl = sec.named_intersections.get(f"{u}-{v}") or sec.named_intersections.get(
                    f"{v}-{u}"
                )
                if named_lbl is not None:
                    if named_lbl not in self.text_labels:
                        raise TuChoi(
                            "UNKNOWN_LABEL",
                            f"{sec.section_id}: giao điểm đặt tên {named_lbl!r} không có trong đề bài",
                            (sec.section_id,),
                        )
                    pt_sym = named_lbl
                    self._bind_local_point(sid, pt_sym, pt_sym)
                    anon = False
                    notation: str | None = pt_sym
                    disp = f"Điểm {pt_sym} (giao của {u}{v} và ({sec.plane_name}))"
                    ref_txt = f"điểm {pt_sym}"
                else:
                    (pt_sym,) = _alloc_labels(self.occupied_labels, "I", 1)
                    anon = True
                    notation = None
                    disp = f"Giao điểm của {u}{v} và ({sec.plane_name})"
                    ref_txt = f"giao điểm của {u}{v} và ({sec.plane_name})"

                derived_vtx_id = f"sec:{sec.section_id}:edge:{u}-{v}"
                self._register_derived(
                    DerivedObjectIdentity(
                        derived_id=derived_vtx_id,
                        kind="section_vertex",
                        internal_symbol=pt_sym,
                        display_label=disp,
                        reference_text=ref_txt,
                        notation=notation,
                        anonymous_in_source=anon,
                        dependencies=(plane_derived_id, u, v),
                        provenance={
                            "section_id": sec.section_id,
                            "edge": [u, v],
                            "plane_name": sec.plane_name,
                            "quote": sec.quote,
                        },
                    )
                )
                ip_call_id = self._next_call_id("ip")
                self.calls.append(
                    {
                        "id": ip_call_id,
                        "fn": "intersect_line_plane",
                        "args": {"point": pt_sym, "line": [u, v], "plane": [p0, x1, x2]},
                        "source": {"quotes": [sec.quote]},
                    }
                )
                self.point_on_segment_provenance[pt_sym] = (u, v)
                cycle_pts.append(pt_sym)
                self.section_cut_checks.append(
                    {
                        "section_id": sec.section_id,
                        "point": pt_sym,
                        "edge": (u, v),
                        "anonymous": anon,
                        "derived_id": derived_vtx_id,
                    }
                )

            if len(dict.fromkeys(cycle_pts)) < 3:
                raise TuChoi(
                    "DEGENERATE_DERIVED_SECTION",
                    f"{sec.section_id}: thiết diện dẫn xuất có ít hơn 3 đỉnh phân biệt",
                    (sec.section_id,),
                )
            self.section_cycles[sec.section_id] = tuple(cycle_pts)
            self._register_derived(
                DerivedObjectIdentity(
                    derived_id=f"section:{sec.section_id}",
                    kind="section_polygon",
                    internal_symbol=f"td_{sec_call_id}",
                    display_label=f"Thiết diện bởi ({sec.plane_name})",
                    reference_text=f"thiết diện bởi ({sec.plane_name})",
                    notation=None
                    if any(
                        self.derived_point_by_symbol.get(p)
                        and self.derived_point_by_symbol[p].anonymous_in_source
                        for p in cycle_pts
                    )
                    else "".join(cycle_pts),
                    anonymous_in_source=any(
                        bool(
                            self.derived_point_by_symbol.get(p)
                            and self.derived_point_by_symbol[p].anonymous_in_source
                        )
                        for p in cycle_pts
                    ),
                    dependencies=(plane_derived_id, solid_cname, *cycle_pts),
                    provenance={
                        "section_id": sec.section_id,
                        "target_solid_id": sid,
                        "plane_name": sec.plane_name,
                        "cycle_symbols": list(cycle_pts),
                        "quote": sec.quote,
                    },
                )
            )

    def _compile_derived_solids_and_goals(self) -> dict[str, str]:
        """Compile `construct_derived_solid` and optional `math_goals` into engine calls."""
        math_call_ids: dict[str, str] = {}
        for g in self.payload.simulation_goals:
            _verify_quote_in_problem(g.quote, self.problem_text, g.goal_id)
            if g.kind != "construct_derived_solid":
                continue
            assert g.derived_solid_id and g.target_section_id and g.apex_ref
            sec_id = g.target_section_id
            sec_spec = next(s for s in self.payload.derived_sections if s.section_id == sec_id)
            parent_sid = g.parent_solid_id or sec_spec.target_solid_id
            c_apex = self.resolve_ref(g.apex_ref, parent_sid, g.goal_id)
            cycle = self.section_cycles[sec_id]
            if c_apex in cycle:
                raise TuChoi(
                    "DEGENERATE_DERIVED_SOLID",
                    f"{g.goal_id}: đỉnh {c_apex!r} nằm trên chính thiết diện đáy {sec_id!r}",
                    (g.goal_id,),
                )
            c_name = f"{c_apex}.{''.join(cycle)}"
            self.solid_canonical_name[g.derived_solid_id] = c_name
            members = {c_apex, *cycle}
            # Derived scopes expose only their verified apex/boundary, not all vertices of the parent.
            self.solid_local_to_canonical[g.derived_solid_id] = {
                **{label: canonical for label, canonical in self.solid_local_to_canonical[parent_sid].items()
                   if canonical in members}, **{point: point for point in members}}
            cid = self._next_call_id("dsolid")
            self.calls.append(
                {
                    "id": cid,
                    "fn": "pyramid",
                    "args": {"apex": c_apex, "base": list(cycle)},
                    "source": {"quotes": [g.quote, c_name]},
                }
            )
            key = frozenset(map(ir_name, [c_apex, *cycle]))
            self.solid_topology_contracts[key] = RequestContract(
                solid_topology=PyramidTopologySpec(apex=c_apex, base_cycle=tuple(cycle))
            )
            has_anon = any(
                bool(
                    self.derived_point_by_symbol.get(p)
                    and self.derived_point_by_symbol[p].anonymous_in_source
                )
                for p in cycle
            )
            self._register_derived(
                DerivedObjectIdentity(
                    derived_id=f"solid:{g.derived_solid_id}",
                    kind="derived_solid",
                    internal_symbol=c_name,
                    display_label=(
                        f"Hình chóp cắt bởi ({sec_spec.plane_name}) chứa đỉnh {c_apex}"
                        if has_anon
                        else f"Hình chóp {c_name}"
                    ),
                    reference_text=(
                        f"hình chóp cắt bởi ({sec_spec.plane_name}) chứa đỉnh {c_apex}"
                        if has_anon
                        else f"hình chóp {c_name}"
                    ),
                    notation=None if has_anon else c_name,
                    anonymous_in_source=has_anon,
                    dependencies=(f"section:{sec_id}", c_apex, *cycle),
                    provenance={
                        "derived_solid_id": g.derived_solid_id,
                        "parent_solid_id": parent_sid,
                        "section_id": sec_id,
                        "apex": c_apex,
                        "base_cycle": list(cycle),
                        "quote": g.quote,
                    },
                )
            )

        # Ensure volume calls are emitted for solids referenced in volume_ratio / residual_volume
        volume_requested_solids: set[str] = set()
        for mg in self.payload.math_goals:
            _verify_quote_in_problem(mg.quote, self.problem_text, mg.goal_id)
            if mg.kind == "volume_ratio":
                assert mg.numerator_solid_id and mg.denominator_solid_id
                volume_requested_solids.add(
                    self._resolve_solid_canonical_name(mg.numerator_solid_id, mg.goal_id)
                )
                volume_requested_solids.add(
                    self._resolve_solid_canonical_name(mg.denominator_solid_id, mg.goal_id)
                )
            elif mg.kind == "residual_volume":
                assert mg.parent_solid_id and mg.cut_solid_id
                volume_requested_solids.add(
                    self._resolve_solid_canonical_name(mg.parent_solid_id, mg.goal_id)
                )
                volume_requested_solids.add(
                    self._resolve_solid_canonical_name(mg.cut_solid_id, mg.goal_id)
                )
            elif mg.kind == "measurement":
                sid = measurement_scope(self.payload, mg)
                t = mg.target
                cid = self._next_call_id("ask")
                math_call_ids[mg.goal_id] = cid
                if mg.goal_type == "volume":
                    sname = self._scoped_solid_name(t.get("solid"), sid, mg.goal_id)
                    self.calls.append(
                        {
                            "id": cid,
                            "fn": "ask_volume",
                            "args": {"solid": sname},
                            "source": {"quotes": [mg.quote]},
                        }
                    )
                elif mg.goal_type == "distance":
                    if "segment" in t:
                        seg = [self.resolve_ref(x, sid, mg.goal_id) for x in t["segment"]]
                        self.calls.append(
                            {
                                "id": cid,
                                "fn": "ask_length",
                                "args": {"segment": seg},
                                "source": {"quotes": [mg.quote]},
                            }
                        )
                    elif "point" in t and "plane" in t:
                        pt = self.resolve_ref(t["point"], sid, mg.goal_id)
                        pl = [self.resolve_ref(x, sid, mg.goal_id) for x in t["plane"]]
                        self.calls.append(
                            {
                                "id": cid,
                                "fn": "ask_distance_point_plane",
                                "args": {"point": pt, "plane": pl},
                                "source": {"quotes": [mg.quote]},
                            }
                        )
                    elif "line1" in t and "line2" in t:
                        l1 = [self.resolve_ref(x, sid, mg.goal_id) for x in t["line1"]]
                        l2 = [self.resolve_ref(x, sid, mg.goal_id) for x in t["line2"]]
                        self.calls.append(
                            {
                                "id": cid,
                                "fn": "ask_distance_lines",
                                "args": {"line1": l1, "line2": l2},
                                "source": {"quotes": [mg.quote]},
                            }
                        )
                    else:
                        raise TuChoi(
                            "INVALID_MATH_GOAL",
                            f"{mg.goal_id}: mục tiêu distance thiếu toán hạng hợp lệ",
                            (mg.goal_id,),
                        )
                elif mg.goal_type == "area":
                    if "section_id" in t:
                        sec_spec = next(
                            (
                                s
                                for s in self.payload.derived_sections
                                if s.section_id == t["section_id"]
                            ),
                            None,
                        )
                        if sec_spec is None:
                            raise TuChoi(
                                "UNKNOWN_SECTION_ID",
                                f"{mg.goal_id}: không tìm thấy thiết diện {t['section_id']!r}",
                                (mg.goal_id,),
                            )
                        # The goal's declared solid (Bridge order) must be the section's solid.
                        sname = self._scoped_solid_name(sid or t.get("solid_id") or t.get("solid"),
                                                        sec_spec.target_solid_id, mg.goal_id)
                        pl = list(self.section_plane_triples[sec_spec.section_id])
                        self.calls.append(
                            {
                                "id": cid,
                                "fn": "ask_section_area",
                                "args": {"solid": sname, "plane": pl},
                                "source": {"quotes": [mg.quote]},
                            }
                        )
                    elif "polygon" in t:
                        poly = [self.resolve_ref(x, sid, mg.goal_id) for x in t["polygon"]]
                        self.calls.append(
                            {
                                "id": cid,
                                "fn": "ask_area",
                                "args": {"polygon": poly},
                                "source": {"quotes": [mg.quote]},
                            }
                        )
                    else:
                        raise TuChoi(
                            "INVALID_MATH_GOAL",
                            f"{mg.goal_id}: mục tiêu area cần 'polygon' hoặc 'section_id'",
                            (mg.goal_id,),
                        )
                elif mg.goal_type == "angle":
                    if "line" in t and "plane" in t:
                        ln = [self.resolve_ref(x, sid, mg.goal_id) for x in t["line"]]
                        pl = [self.resolve_ref(x, sid, mg.goal_id) for x in t["plane"]]
                        self.calls.append(
                            {
                                "id": cid,
                                "fn": "ask_angle_line_plane",
                                "args": {"line": ln, "plane": pl},
                                "source": {"quotes": [mg.quote]},
                            }
                        )
                    elif "line1" in t and "line2" in t:
                        l1 = [self.resolve_ref(x, sid, mg.goal_id) for x in t["line1"]]
                        l2 = [self.resolve_ref(x, sid, mg.goal_id) for x in t["line2"]]
                        self.calls.append(
                            {
                                "id": cid,
                                "fn": "ask_angle_lines",
                                "args": {"line1": l1, "line2": l2},
                                "source": {"quotes": [mg.quote]},
                            }
                        )
                    else:
                        raise TuChoi(
                            "INVALID_MATH_GOAL",
                            f"{mg.goal_id}: mục tiêu angle cần ('line', 'plane') hoặc ('line1', 'line2')",
                            (mg.goal_id,),
                        )
                else:  # F7: no polyhedral ask exists (radius, lateral_area); never leave an id without a call
                    raise TuChoi("BRIDGE_UNSUPPORTED_MEASUREMENT", f"{mg.goal_id}: Adapter /3 chưa có phép đo "
                                 f"{mg.goal_type} cho khối đa diện", (mg.goal_id,))

        existing_vol_solids = {
            c["args"]["solid"] for c in self.calls if c["fn"] == "ask_volume"
        }
        for sname in sorted(volume_requested_solids - existing_vol_solids):
            cid = self._next_call_id("vcert")
            self.calls.append(
                {
                    "id": cid,
                    "fn": "ask_volume",
                    "args": {"solid": sname},
                    "source": {"quotes": [self.payload.solids[0].quote]},
                }
            )
        return math_call_ids

    def _validate_structural_relations(self) -> list[dict[str, Any]]:
        """Validate structural multi-solid relations (`shared_vertices`, `shared_faces`, `coordinate_frame`)."""
        certificates: list[dict[str, Any]] = []
        for rel in self.payload.relations:
            _verify_quote_in_problem(rel.quote, self.problem_text, rel.relation_id)
            if rel.kind == "shared_vertices":
                resolved_pairs: list[dict[str, str]] = []
                for ref_a, ref_b in rel.pairs:
                    ca = self.resolve_ref(ref_a, None, rel.relation_id)
                    cb = self.resolve_ref(ref_b, None, rel.relation_id)
                    if ca != cb:
                        raise TuChoi(
                            "SHARED_ENTITY_MISMATCH",
                            f"{rel.relation_id}: hai đỉnh khai báo chung ({ref_a!r} -> {ca!r}, {ref_b!r} -> {cb!r}) "
                            "không ánh xạ về cùng một điểm chính tắc",
                            (rel.relation_id,),
                        )
                    resolved_pairs.append({"ref_a": ref_a, "ref_b": ref_b, "canonical": ca})
                certificates.append(
                    {
                        "relation_id": rel.relation_id,
                        "kind": rel.kind,
                        "verified": True,
                        "details": {"pairs": resolved_pairs},
                    }
                )
            elif rel.kind == "shared_faces":
                assert rel.solid_a and rel.solid_b
                if rel.solid_a not in self.solid_specs or rel.solid_b not in self.solid_specs:
                    raise TuChoi(
                        "UNKNOWN_SOLID_ID",
                        f"{rel.relation_id}: khối trong shared_faces chưa được khai báo",
                        (rel.relation_id,),
                    )
                ca = tuple(self.resolve_ref(v, rel.solid_a, rel.relation_id) for v in rel.face_a)
                cb = tuple(self.resolve_ref(v, rel.solid_b, rel.relation_id) for v in rel.face_b)
                if frozenset(ca) != frozenset(cb):
                    raise TuChoi(
                        "SHARED_ENTITY_MISMATCH",
                        f"{rel.relation_id}: mặt {rel.face_a} của {rel.solid_a} ({ca}) khác mặt {rel.face_b} của {rel.solid_b} ({cb})",
                        (rel.relation_id,),
                    )
                faces_a = _solid_faces(
                    self.solid_specs[rel.solid_a], self.solid_local_to_canonical[rel.solid_a]
                )
                faces_b = _solid_faces(
                    self.solid_specs[rel.solid_b], self.solid_local_to_canonical[rel.solid_b]
                )
                if frozenset(ca) not in faces_a or frozenset(cb) not in faces_b:
                    raise TuChoi(
                        "SHARED_ENTITY_MISMATCH",
                        f"{rel.relation_id}: mặt chung {ca} không phải mặt biên hợp lệ của cả hai khối",
                        (rel.relation_id,),
                    )
                certificates.append(
                    {
                        "relation_id": rel.relation_id,
                        "kind": rel.kind,
                        "verified": True,
                        "details": {
                            "solid_a": rel.solid_a,
                            "solid_b": rel.solid_b,
                            "canonical_face": list(ca),
                        },
                    }
                )
            elif rel.kind == "coordinate_frame":
                assert rel.solid_id and rel.frame_id
                if rel.solid_id not in self.solid_specs:
                    raise TuChoi(
                        "UNKNOWN_SOLID_ID",
                        f"{rel.relation_id}: khối {rel.solid_id!r} chưa được khai báo",
                        (rel.relation_id,),
                    )
                spec_frame = self.solid_specs[rel.solid_id].coordinate_frame_id
                if rel.frame_id != spec_frame or rel.frame_id != "root":
                    raise TuChoi(
                        "COORDINATE_FRAME_DISCONNECTED",
                        f"{rel.relation_id}: hệ tọa độ {rel.frame_id!r} không gắn kết với hệ tọa độ gốc 'root'",
                        (rel.relation_id,),
                    )
                anchors = [
                    self.resolve_ref(r, rel.solid_id, rel.relation_id) for r in rel.anchor_refs
                ]
                certificates.append(
                    {
                        "relation_id": rel.relation_id,
                        "kind": rel.kind,
                        "verified": True,
                        "details": {
                            "solid_id": rel.solid_id,
                            "frame_id": rel.frame_id,
                            "anchors": anchors,
                        },
                    }
                )
        for sid, s in self.solid_specs.items():
            if s.coordinate_frame_id != "root":
                raise TuChoi(
                    "COORDINATE_FRAME_DISCONNECTED",
                    f"{sid}: hệ tọa độ {s.coordinate_frame_id!r} tách rời hệ tọa độ gốc 'root'",
                    (sid,),
                )
        return certificates

    def _certify_section_boundary(self, dung: _Dung, certificates: list[dict[str, Any]]) -> None:
        """Closure certificate (run `backend-hybrid-contract-unification`). Adapter /3 reads `/1.cut_edges` as the COMPLETE
        section boundary in cyclic order, so the cycle it built must BE the exact cross-section of the solid by the plane
        (`section.cross_section`; rotation / reversal allowed). A partial list — the bridge reading, the edges the source
        states are cut — or a crossed order is refused, never served as a smaller or self-intersecting polygon."""
        for sec in self.payload.derived_sections:
            cycle = self.section_cycles[sec.section_id]
            # one closure authority for every route (run `hybrid-contract-v2`): the engine's exact cross-section
            dung.chung_chi_khep_kin(self.solid_canonical_name[sec.target_solid_id],
                                    list(self.section_plane_triples[sec.section_id]), list(cycle), (sec.section_id,))
            certificates.append({"relation_id": f"closure:{sec.section_id}", "kind": "section_closure", "verified": True,
                                 "details": {"section_id": sec.section_id, "boundary": list(cycle),
                                             "rule": "cycle == cross_section(solid, plane) up to rotation/reversal"}})

    def _verify_geometric_relations_and_cuts(
        self, dung: _Dung, certificates: list[dict[str, Any]]
    ) -> None:
        """Verify cut-edge segment bounds $0 < t \\le 1$ and geometric relations on the built chart."""
        for check in self.section_cut_checks:
            pt = check["point"]
            u, v = check["edge"]
            if pt not in dung.pts or u not in dung.pts or v not in dung.pts:
                raise TuChoi(
                    "SECTION_NOT_CLOSED_ON_LATERAL_EDGES",
                    f"{check['section_id']}: không xác định được tọa độ giao điểm trên cạnh {u}{v}",
                    (check["section_id"],),
                )
            pu, pv, pp = dung.pts[u], dung.pts[v], dung.pts[pt]
            duv = tuple(pv[i] - pu[i] for i in range(3))
            dup = tuple(pp[i] - pu[i] for i in range(3))
            axis = next((i for i in range(3) if duv[i] != 0), None)
            if axis is None:
                raise TuChoi(
                    "DEGENERATE_LINE",
                    f"{check['section_id']}: cạnh {u}{v} suy biến",
                    (check["section_id"],),
                )
            t_param = Fraction(dup[axis], duv[axis])
            if any(dup[i] != t_param * duv[i] for i in range(3)) or not (
                Fraction(0) < t_param <= Fraction(1)
            ):
                raise TuChoi(
                    "SECTION_NOT_CLOSED_ON_LATERAL_EDGES",
                    f"{check['section_id']}: giao điểm {pt} trên đường thẳng {u}{v} có tỉ số t={t_param} nằm ngoài đoạn ({u}, {v}]",
                    (check["section_id"],),
                )
            check["ratio_t"] = str(t_param)

        # Verify section polygons have non-collinear vertices
        for sec_id, cycle in self.section_cycles.items():
            if len(set(cycle)) < 3:
                raise TuChoi(
                    "DEGENERATE_DERIVED_SECTION",
                    f"{sec_id}: thiết diện suy biến (các đỉnh trùng nhau)",
                    (sec_id,),
                )
            try:
                dung._plane(cycle[:3])
            except GeometryError as exc:
                raise TuChoi(
                    "DEGENERATE_DERIVED_SECTION",
                    f"{sec_id}: ba đỉnh thiết diện thẳng hàng ({exc})",
                    (sec_id,),
                ) from None

        # Verify remaining geometric relations (containment, parallel, perpendicular, section_membership)
        with _metric.using(dung.metric()):
            for rel in self.payload.relations:
                if rel.kind in ("shared_vertices", "shared_faces", "coordinate_frame"):
                    continue
                sid = rel.solid_id
                if rel.kind == "section_membership":
                    assert rel.section_id
                    if rel.section_id not in self.section_plane_triples:
                        raise TuChoi(
                            "UNKNOWN_SECTION_ID",
                            f"{rel.relation_id}: không tìm thấy thiết diện {rel.section_id!r}",
                            (rel.relation_id,),
                        )
                    plane = dung._plane(self.section_plane_triples[rel.section_id])
                    members = [
                        self.resolve_ref(m, sid, rel.relation_id) for m in rel.member_refs
                    ]
                    for m in members:
                        if m not in dung.pts or plane.signed_eval(Vec3(*dung.pts[m])) != 0:
                            raise TuChoi(
                                "INCONSISTENT_FACTS",
                                f"{rel.relation_id}: điểm {m!r} không thuộc mặt phẳng thiết diện {rel.section_id!r}",
                                (rel.relation_id,),
                            )
                    certificates.append(
                        {
                            "relation_id": rel.relation_id,
                            "kind": rel.kind,
                            "verified": True,
                            "details": {"section_id": rel.section_id, "members": members},
                        }
                    )
                elif rel.kind == "containment":
                    assert rel.container_ref and rel.member_ref
                    pt = self.resolve_ref(rel.member_ref, sid, rel.relation_id)
                    if pt not in dung.pts:
                        raise TuChoi(
                            "UNKNOWN_LABEL",
                            f"{rel.relation_id}: điểm {pt!r} chưa được dựng",
                            (rel.relation_id,),
                        )
                    # container_ref can be a segment "AB", a face "ABC", or a solid_id
                    if rel.container_ref in self.solid_specs:
                        s_verts = [
                            self.solid_local_to_canonical[rel.container_ref][v]
                            for v in self.solid_specs[rel.container_ref].local_vertices()
                        ]
                        ok = pt in s_verts or pt in dung.pts
                    else:
                        c_sid, c_chain = (
                            rel.container_ref.split("::", 1)
                            if "::" in rel.container_ref
                            else (sid, rel.container_ref)
                        )
                        from app.simulation.geometry_functions.typed_fact_next import (
                            split_vertex_chain,
                        )

                        chain_pts = [
                            self.resolve_ref(
                                f"{c_sid}::{x}" if c_sid else x, sid, rel.relation_id
                            )
                            for x in split_vertex_chain(c_chain)
                        ]
                        if len(chain_pts) == 2:
                            line = dung._line(chain_pts)
                            ok = point_on_line(Vec3(*dung.pts[pt]), line)
                        else:
                            plane = dung._plane(chain_pts[:3])
                            ok = plane.signed_eval(Vec3(*dung.pts[pt])) == 0
                    if not ok:
                        raise TuChoi(
                            "INCONSISTENT_FACTS",
                            f"{rel.relation_id}: quan hệ chứa đựng {rel.member_ref!r} trong {rel.container_ref!r} không thỏa",
                            (rel.relation_id,),
                        )
                    certificates.append(
                        {
                            "relation_id": rel.relation_id,
                            "kind": rel.kind,
                            "verified": True,
                            "details": {
                                "container": rel.container_ref,
                                "member": pt,
                            },
                        }
                    )
                elif rel.kind in ("parallel", "perpendicular"):
                    ea = [self.resolve_ref(x, sid, rel.relation_id) for x in rel.entity_a]
                    eb = [self.resolve_ref(x, sid, rel.relation_id) for x in rel.entity_b]
                    if rel.kind == "parallel":
                        if len(ea) == 2 and len(eb) == 2:
                            la, lb = dung._line(ea), dung._line(eb)
                            ok = la.direction.cross(lb.direction).is_zero()
                        elif len(ea) == 2 and len(eb) >= 3:
                            la, pb = dung._line(ea), dung._plane(eb[:3])
                            ok = parallel_line_plane(la, pb)
                        elif len(ea) >= 3 and len(eb) >= 3:
                            pa, pb = dung._plane(ea[:3]), dung._plane(eb[:3])
                            ok = parallel_planes(pa, pb)
                        else:
                            ok = False
                    else:
                        if len(ea) == 2 and len(eb) == 2:
                            ok = dung.g(dung._vec(ea[0], ea[1]), dung._vec(eb[0], eb[1])) == 0
                        elif len(ea) == 2 and len(eb) >= 3:
                            d = dung._vec(ea[0], ea[1])
                            ok = all(dung.g(d, dung._vec(eb[0], x)) == 0 for x in eb[1:])
                        else:
                            ok = False
                    if not ok:
                        raise TuChoi(
                            "INCONSISTENT_FACTS",
                            f"{rel.relation_id}: quan hệ {rel.kind} giữa {ea} và {eb} không thỏa trên hình đã dựng",
                            (rel.relation_id,),
                        )
                    certificates.append(
                        {
                            "relation_id": rel.relation_id,
                            "kind": rel.kind,
                            "verified": True,
                            "details": {"entity_a": ea, "entity_b": eb},
                        }
                    )

    def _compute_certified_math_goals(
        self,
        dung: _Dung,
        fm: dict[str, Any],
        hoi: dict[str, str],
        math_call_ids: dict[str, str],
        ky_hieu: str | None,
    ) -> tuple[list[dict[str, Any]], dict[str, str], dict[str, dict[str, Any]]]:
        from app.simulation.geometry.radical import Radical

        results: list[dict[str, Any]] = []
        answers: dict[str, str] = {}
        answer_exact: dict[str, dict[str, Any]] = {}

        def _exact_sqrt_fraction(q: Fraction, gid: str) -> Fraction:
            if q <= 0:
                raise TuChoi(
                    "ENGINE_SELF_CHECK_FAILED",
                    f"{gid}: tỉ số thể tích bình phương không dương ({q})",
                    (gid,),
                )
            num_root = math.isqrt(q.numerator)
            den_root = math.isqrt(q.denominator)
            if num_root * num_root != q.numerator or den_root * den_root != q.denominator:
                raise TuChoi(
                    "IRRATIONAL_VOLUME_RATIO",
                    f"{gid}: tỉ số thể tích không phải số hữu tỉ chính xác (r²={q})",
                    (gid,),
                )
            return Fraction(num_root, den_root)

        for mg in self.payload.math_goals:
            if mg.kind == "volume_ratio":
                assert mg.numerator_solid_id and mg.denominator_solid_id
                num_name = self._resolve_solid_canonical_name(mg.numerator_solid_id, mg.goal_id)
                den_name = self._resolve_solid_canonical_name(mg.denominator_solid_id, mg.goal_id)
                if num_name == den_name:
                    raise TuChoi(
                        "UNSUPPORTED_VOLUME_RATIO",
                        f"{mg.goal_id}: tỉ số thể tích cần hai khối phân biệt ({num_name})",
                        (mg.goal_id,),
                    )
                v2_num = dung.volume_certificates.get(num_name)
                v2_den = dung.volume_certificates.get(den_name)
                if v2_num is None or v2_den is None or v2_den == 0:
                    raise TuChoi(
                        "MISSING_VOLUME_CERTIFICATE",
                        f"{mg.goal_id}: thiếu chứng chỉ thể tích cho {num_name} hoặc {den_name}",
                        (mg.goal_id,),
                    )
                ratio = _exact_sqrt_fraction(Fraction(v2_num, v2_den), mg.goal_id)
                # Cross-check with kernel final_memory volumes
                k_num = fm.get("khoi_" + ir_name(num_name.replace(".", "_")))
                k_den = fm.get("khoi_" + ir_name(den_name.replace(".", "_")))
                val_str = str(ratio)
                exact_obj = {"coef": val_str, "dim": 0, "unit": None}
                answers[mg.goal_id] = val_str
                answer_exact[mg.goal_id] = exact_obj
                results.append(
                    {
                        "goal_id": mg.goal_id,
                        "kind": "volume_ratio",
                        "numerator_solid": num_name,
                        "denominator_solid": den_name,
                        "value_display": val_str,
                        "exact": exact_obj,
                        "certificate": {
                            "rule": "gram_chart_volume_squared_ratio",
                            "v2_numerator": str(v2_num),
                            "v2_denominator": str(v2_den),
                            "ratio_exact": val_str,
                            "kernel_solids_present": k_num is not None and k_den is not None,
                        },
                    }
                )
            elif mg.kind == "residual_volume":
                assert mg.parent_solid_id and mg.cut_solid_id
                parent_name = self._resolve_solid_canonical_name(mg.parent_solid_id, mg.goal_id)
                cut_name = self._resolve_solid_canonical_name(mg.cut_solid_id, mg.goal_id)
                if cut_name == parent_name:
                    raise TuChoi(
                        "NON_POSITIVE_RESIDUAL_VOLUME",
                        f"{mg.goal_id}: không thể cắt bỏ chính khối gốc {parent_name}",
                        (mg.goal_id,),
                    )
                v2_parent = dung.volume_certificates.get(parent_name)
                v2_cut = dung.volume_certificates.get(cut_name)
                if v2_parent is None or v2_cut is None or v2_parent == 0:
                    raise TuChoi(
                        "MISSING_VOLUME_CERTIFICATE",
                        f"{mg.goal_id}: thiếu chứng chỉ thể tích cho {parent_name} hoặc {cut_name}",
                        (mg.goal_id,),
                    )
                # Single mathematical authority (engine.py /9): outward half-space containment & shared boundary face
                _, _, orig_planes, _ = dung._mat_ngoai_khoi(dung.khoi[parent_name])
                s_labels, s_faces, _, _ = dung._mat_ngoai_khoi(dung.khoi[cut_name])
                for v_lb in s_labels:
                    pt = dung.pts[v_lb]
                    if any(
                        n[0] * pt[0] + n[1] * pt[1] + n[2] * pt[2] - d > 0
                        for n, d in orig_planes
                    ):
                        raise TuChoi(
                            "RESIDUAL_CONTAINMENT_UNPROVED",
                            f"{mg.goal_id}: đỉnh {v_lb} của khối {cut_name} nằm ngoài khối gốc {parent_name}",
                            (mg.goal_id,),
                        )
                if not any(
                    all(
                        n[0] * dung.pts[v_lb][0]
                        + n[1] * dung.pts[v_lb][1]
                        + n[2] * dung.pts[v_lb][2]
                        - d
                        == 0
                        for v_lb in sf
                    )
                    for sf in s_faces
                    for n, d in orig_planes
                ):
                    raise TuChoi(
                        "RESIDUAL_CONTAINMENT_UNPROVED",
                        f"{mg.goal_id}: khối cắt bỏ {cut_name} không chung mặt biên với khối gốc {parent_name}",
                        (mg.goal_id,),
                    )
                ratio_cut = _exact_sqrt_fraction(Fraction(v2_cut, v2_parent), mg.goal_id)
                complement_ratio = Fraction(1) - ratio_cut
                if complement_ratio <= 0:
                    raise TuChoi(
                        "INVALID_RESIDUAL_VOLUME",
                        f"{mg.goal_id}: thể tích phần cắt ({cut_name}) không nhỏ hơn thể tích khối gốc ({parent_name})",
                        (mg.goal_id,),
                    )
                # Find the kernel volume value for parent_name
                parent_ask_call = next(
                    (c for c in dung.of("ask_volume") if c.args.solid == parent_name),
                    None,
                )
                parent_v_raw = fm.get(hoi[parent_ask_call.id]) if parent_ask_call else None
                if isinstance(parent_v_raw, Radical):
                    res_val: Any = Radical(Fraction(parent_v_raw.he) * complement_ratio, parent_v_raw.can)
                elif isinstance(parent_v_raw, (int, Fraction)):
                    res_val = Fraction(parent_v_raw) * complement_ratio
                else:
                    raise TuChoi(
                        "MISSING_VOLUME_CERTIFICATE",
                        f"{mg.goal_id}: không đọc được giá trị thể tích gốc của {parent_name}",
                        (mg.goal_id,),
                    )
                expected_res_v2 = (complement_ratio**2) * v2_parent
                if _binh_phuong(res_val) != expected_res_v2:
                    raise TuChoi(
                        "ENGINE_SELF_CHECK_FAILED",
                        f"{mg.goal_id}: thể tích phần còn lại lệch chứng chỉ bình phương độc lập",
                        (mg.goal_id,),
                    )
                coef_str = dinh_dang(res_val)
                disp_str = _hien_thi_ky_hieu(res_val, 3, ky_hieu) if ky_hieu else coef_str
                exact_obj = {
                    "coef": coef_str,
                    "dim": 3 if ky_hieu else 0,
                    "unit": ky_hieu,
                }
                answers[mg.goal_id] = disp_str
                answer_exact[mg.goal_id] = exact_obj
                results.append(
                    {
                        "goal_id": mg.goal_id,
                        "kind": "residual_volume",
                        "parent_solid": parent_name,
                        "cut_solid": cut_name,
                        "complement_ratio": str(complement_ratio),
                        "value_display": disp_str,
                        "exact": exact_obj,
                        "certificate": {
                            "rule": "exact_complement_of_certified_cut_volume",
                            "cut_to_parent_ratio": str(ratio_cut),
                            "complement_ratio": str(complement_ratio),
                            "residual_volume_squared": str(expected_res_v2),
                            "containment_verified": True,
                            "shared_boundary_verified": True,
                        },
                    }
                )
            elif mg.kind == "measurement":
                cid = math_call_ids[mg.goal_id]
                kq_var = hoi[cid]
                v = fm.get(kq_var)
                fn_name = next(c.fn for c in dung.calls if c.id == cid)
                bac = BAC_DAI_LUONG[fn_name]
                he = dinh_dang(v)
                exact_obj = {
                    "coef": he,
                    "dim": bac if ky_hieu else 0,
                    "unit": ky_hieu if bac else None,
                }
                disp_str = (
                    f"cos²={he}"
                    if bac == 0
                    else (_hien_thi_ky_hieu(v, bac, ky_hieu) if ky_hieu else he)
                )
                answers[mg.goal_id] = disp_str
                answer_exact[mg.goal_id] = exact_obj
                results.append(
                    {
                        "goal_id": mg.goal_id,
                        "kind": "measurement",
                        "goal_type": mg.goal_type,
                        "call_id": cid,
                        "value_display": disp_str,
                        "exact": exact_obj,
                        "certificate": {
                            "rule": fn_name,
                            "kernel_var": kq_var,
                        },
                    }
                )
        return results, answers, answer_exact

    def _enrich_scene3d_and_goals(
        self, canh: dict[str, Any]
    ) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
        """Enrich Scene3D objects/events with derived-point & multi-solid provenance and resolve simulation goals."""
        by_id: dict[str, dict[str, Any]] = {o["id"]: o for o in canh["objects"]}

        # 1. Enrich unnamed derived section vertices so internal symbols (I1, I2...) never leak as user notation
        for sym, identity in self.derived_point_by_symbol.items():
            pid = ir_name(sym)
            obj = by_id.get(pid)
            if obj is None:
                continue
            obj["label"] = identity.display_label
            obj["display_label"] = identity.display_label
            obj["reference"] = identity.reference_text
            obj["notation"] = identity.notation  # None when anonymous_in_source is True
            obj["role"] = "Đỉnh thiết diện dẫn xuất"
            obj["synthetic"] = False
            obj["source"] = {
                **(obj.get("source") or {}),
                "binding": "DERIVED_SECTION_VERTEX",
                "derived_id": identity.derived_id,
                "anonymous_in_source": identity.anonymous_in_source,
                "edge": identity.provenance.get("edge"),
                "plane": f"({identity.provenance.get('plane_name', 'α')})",
                "dependencies": list(identity.dependencies),
            }
            for ev in canh.get("events", []):
                if ev.get("object") == pid and ev.get("action") == "CREATE":
                    txt = f"Xác định {identity.reference_text}."
                    ev["display_label"] = identity.display_label
                    ev["learner_text"] = txt
                    step_idx = ev.get("step_index")
                    steps = (canh.get("formation") or {}).get("steps") or []
                    if isinstance(step_idx, int) and 0 <= step_idx < len(steps):
                        steps[step_idx]["learner_text"] = txt

        # 2. Enrich unnamed derived sub-solids so internal vertex symbols do not leak in solid label/notation
        for cname, identity in self.derived_solid_by_canonical.items():
            sid_ir = "khoi_" + ir_name(cname.replace(".", "_"))
            obj = by_id.get(sid_ir)
            if obj is None:
                continue
            obj["label"] = identity.display_label
            obj["display_label"] = identity.display_label
            obj["reference"] = identity.reference_text
            obj["notation"] = identity.notation
            obj["role"] = "Khối đa diện dẫn xuất"
            obj["source"] = {
                **(obj.get("source") or {}),
                "binding": "DERIVED_SOLID",
                "derived_id": identity.derived_id,
                "anonymous_in_source": identity.anonymous_in_source,
                "dependencies": list(identity.dependencies),
            }
            for ev in canh.get("events", []):
                if ev.get("object") == sid_ir and ev.get("action") == "CREATE":
                    txt = (
                        f"Dựng {identity.reference_text} "
                        f"({len(obj.get('vertices') or [])} đỉnh, {len(obj.get('faces') or [])} mặt)."
                    )
                    ev["display_label"] = identity.display_label
                    ev["learner_text"] = txt
                    step_idx = ev.get("step_index")
                    steps = (canh.get("formation") or {}).get("steps") or []
                    if isinstance(step_idx, int) and 0 <= step_idx < len(steps):
                        steps[step_idx]["learner_text"] = txt

        # 3. Also scrub any segment3 / polygon3 / quantity objects that touched anonymous derived symbols
        anon_point_ids = {
            ir_name(sym): identity
            for sym, identity in self.derived_point_by_symbol.items()
            if identity.anonymous_in_source
        }
        if anon_point_ids:
            for obj in canh["objects"]:
                if obj["type"] == "segment3":
                    eids = obj.get("endpoint_ids") or []
                    if any(eid in anon_point_ids for eid in eids):
                        obj["notation"] = None
                        names = [
                            by_id.get(eid, {}).get("notation")
                            or by_id.get(eid, {}).get("reference")
                            or eid
                            for eid in eids
                        ]
                        obj["label"] = f"Đoạn nối {names[0]} và {names[1]}"
                        obj["display_label"] = obj["label"]
                        obj["reference"] = f"đoạn nối {names[0]} và {names[1]}"
                elif obj["type"] == "polygon3":
                    vids = obj.get("vertex_ids") or []
                    if any(vid in anon_point_ids for vid in vids):
                        obj["notation"] = None
                        obj["label"] = "Đa giác thiết diện dẫn xuất"
                        obj["display_label"] = obj["label"]
                        obj["reference"] = "đa giác thiết diện dẫn xuất"

        # 4. Enrich solid-qualified vertices (Slice B)
        for c_sym, meta in self.qualified_point_meta.items():
            pid = ir_name(c_sym)
            obj = by_id.get(pid)
            if obj is None:
                continue
            local_n = meta["local_notation"]
            sid = meta["solid_id"]
            solid_not = self.solid_specs[sid].notation if sid in self.solid_specs else c_sym
            obj["label"] = f"Đỉnh {c_sym} (đỉnh {local_n} của khối {solid_not})"
            obj["display_label"] = f"Đỉnh {c_sym}"
            obj["reference"] = f"đỉnh {c_sym} của khối {solid_not}"
            obj["notation"] = c_sym
            obj["source"] = {**(obj.get("source") or {}), **meta, "solid_notation": solid_not}

        # 5. Build resolved solid descriptors
        solid_descriptors: list[dict[str, Any]] = []
        for sid, s in self.solid_specs.items():
            cname = self.solid_canonical_name[sid]
            scene_oid = "khoi_" + ir_name(cname.replace(".", "_"))
            solid_descriptors.append(
                {
                    "solid_id": sid,
                    "solid_type": s.solid_type,
                    "notation": s.notation,
                    "canonical_notation": cname,
                    "coordinate_frame_id": s.coordinate_frame_id,
                    "local_to_canonical": dict(self.solid_local_to_canonical[sid]),
                    "scene_object_id": scene_oid,
                }
            )
        for cname, identity in self.derived_solid_by_canonical.items():
            scene_oid = "khoi_" + ir_name(cname.replace(".", "_"))
            solid_descriptors.append(
                {
                    "solid_id": identity.provenance["derived_solid_id"],
                    "solid_type": "pyramid",
                    "notation": identity.notation,
                    "canonical_notation": cname,
                    "coordinate_frame_id": "root",
                    "local_to_canonical": {},
                    "scene_object_id": scene_oid,
                    "derived_id": identity.derived_id,
                }
            )

        # 6. Resolve simulation goals
        sim_goal_outcomes: list[dict[str, Any]] = []
        for g in self.payload.simulation_goals:
            if g.kind == "construct_object":
                assert g.target_solid_id
                cname = self.solid_canonical_name[g.target_solid_id]
                oid = "khoi_" + ir_name(cname.replace(".", "_"))
                sim_goal_outcomes.append(
                    {
                        "goal_id": g.goal_id,
                        "kind": g.kind,
                        "status": "CONSTRUCTED" if oid in by_id else "MISSING",
                        "scene_object_ids": [oid],
                        "style_role": g.style_role,
                    }
                )
            elif g.kind == "construct_plane_section":
                assert g.target_section_id
                sec_cid = self.section_call_ids[g.target_section_id]
                sec_oid = self.section_object_ids.get(g.target_section_id, f"td_{sec_cid}")
                plane_oid = self.section_plane_object_ids.get(g.target_section_id, f"mp_td_{sec_cid}")
                vtx_oids = [ir_name(p) for p in self.section_cycles[g.target_section_id]]
                sim_goal_outcomes.append(
                    {
                        "goal_id": g.goal_id,
                        "kind": g.kind,
                        "status": "CONSTRUCTED" if sec_oid in by_id else "MISSING",
                        "scene_object_ids": [sec_oid, plane_oid, *vtx_oids],
                        "section_object_id": sec_oid,
                        "plane_object_id": plane_oid,
                        "section_vertex_ids": vtx_oids,
                        "style_role": g.style_role,
                    }
                )
            elif g.kind == "construct_derived_solid":
                assert g.derived_solid_id
                cname = self.solid_canonical_name[g.derived_solid_id]
                oid = "khoi_" + ir_name(cname.replace(".", "_"))
                sim_goal_outcomes.append(
                    {
                        "goal_id": g.goal_id,
                        "kind": g.kind,
                        "status": "CONSTRUCTED" if oid in by_id else "MISSING",
                        "scene_object_ids": [oid],
                        "derived_solid_id": g.derived_solid_id,
                        "style_role": g.style_role,
                    }
                )
            elif g.kind == "highlight_geometry":
                resolved_oids: list[str] = []
                for ref in g.target_refs:
                    if ref in self.solid_canonical_name:
                        cname = self.solid_canonical_name[ref]
                        resolved_oids.append("khoi_" + ir_name(cname.replace(".", "_")))
                    elif ref in self.section_call_ids:
                        sec_cid = self.section_call_ids[ref]
                        resolved_oids.append(self.section_object_ids.get(ref, f"td_{sec_cid}"))
                    elif ref in self.derived_by_id:
                        sym = self.derived_by_id[ref].internal_symbol
                        resolved_oids.append(
                            sym if sym in by_id else ir_name(sym)
                        )
                    else:
                        pt = self.resolve_ref(ref, g.target_solid_id, g.goal_id)
                        resolved_oids.append(ir_name(pt))
                for oid in resolved_oids:
                    if oid in by_id and "target" not in by_id[oid]["display_group"]:
                        by_id[oid]["display_group"].append("target")
                sim_goal_outcomes.append(
                    {
                        "goal_id": g.goal_id,
                        "kind": g.kind,
                        "status": "HIGHLIGHTED",
                        "scene_object_ids": resolved_oids,
                        "style_role": g.style_role,
                    }
                )
            elif g.kind == "construction_sequence":
                steps_out = [
                    {
                        "step_index": ev["step_index"],
                        "action": ev["action"],
                        "object_id": ev.get("object"),
                        "display_label": ev.get("display_label"),
                        "learner_text": ev.get("learner_text"),
                        "semantic_kind": ev.get("semantic_kind"),
                        "depends": list(ev.get("depends") or []),
                    }
                    for ev in canh.get("events", [])
                ]
                sim_goal_outcomes.append(
                    {
                        "goal_id": g.goal_id,
                        "kind": g.kind,
                        "status": "SEQUENCED",
                        "scene_object_ids": [
                            s["object_id"] for s in steps_out if s.get("object_id")
                        ],
                        "construction_steps": steps_out,
                        "style_role": g.style_role,
                    }
                )

        return solid_descriptors, sim_goal_outcomes

    def derived_sections_present(self) -> bool:
        return bool(self.payload.derived_sections)

    def _rebuild_folded_dung(self, phase1_dung: _Dung, ky_hieu: str | None) -> _Dung:
        aux_construct_ids = {
            cid for d in self.mat_phu for cid in d.get("constructs", [])
        }
        cut_points_map = {
            chk["point"]: chk for chk in self.section_cut_checks if "ratio_t" in chk
        }
        sec_cid_to_sec_id = {cid: sid for sid, cid in self.section_call_ids.items()}
        old_plane_to_cycle: dict[tuple[str, ...], list[str]] = {
            tuple(plane): list(self.section_cycles[sid][:3])
            for sid, plane in self.section_plane_triples.items()
        }

        folded_calls: list[dict[str, Any]] = []
        for c in self.calls:
            cid = c["id"]
            fn = c["fn"]
            if cid in aux_construct_ids:
                continue
            if fn == "intersect_line_plane" and c["args"]["point"] in cut_points_map:
                chk = cut_points_map[c["args"]["point"]]
                u, v = chk["edge"]
                t_str = chk["ratio_t"]
                if Fraction(t_str) == Fraction(1, 2):
                    folded_calls.append(
                        {
                            "id": cid,
                            "fn": "midpoint",
                            "args": {"point": chk["point"], "segment": [u, v]},
                            "source": c["source"],
                        }
                    )
                else:
                    folded_calls.append(
                        {
                            "id": cid,
                            "fn": "divide_segment",
                            "args": {
                                "point": chk["point"],
                                "segment": [u, v],
                                "ratio": t_str,
                            },
                            "source": c["source"],
                        }
                    )
                continue
            if fn in ("section", "ask_section_area"):
                old_pl = tuple(c["args"]["plane"])
                new_pl = old_plane_to_cycle.get(old_pl, list(old_pl))
                folded_calls.append(
                    {
                        "id": cid,
                        "fn": fn,
                        "args": {**c["args"], "plane": new_pl},
                        "source": c["source"],
                    }
                )
                continue
            folded_calls.append(c)

        parsed = doc_ke_hoach({"calls": folded_calls})
        d2 = _Dung(parsed, self.problem_text, ky_hieu)
        d2.thu_khoi()
        if len(d2.khoi) > 1 and not d2.composite:
            d2.composite = True
            d2.root = d2.khoi[phase1_dung.root.name]
        d2.bo_cuc_day()
        d2.giai_phu_thuoc()
        d2.mat_phu = []
        d2.ten_mat_phu = {}
        d2.kiem()
        d2.kiem_mat_cat()
        d2.volume_certificates = dict(phase1_dung.volume_certificates)
        return d2

    def _parse_curved_scalar(
        self, raw_val: str | None, quote: str, context_id: str, field_name: str
    ) -> tuple[Any, Fraction, bool]:
        from app.simulation.geometry import curved as CV
        from app.simulation.geometry.radical import parse_exact

        if not raw_val:
            raise TuChoi(
                "MISSING_CURVED_DIMENSION",
                f"{context_id}: thiếu tham số '{field_name}' của khối cong",
                (context_id,),
            )
        s = str(raw_val).strip()
        has_a = False
        if s.endswith("a") and len(s) > 1 and (s[:-1][-1].isdigit() or s[:-1][-1] == ")"):
            has_a = True
            s_num = s[:-1].rstrip("*").strip() or "1"
        elif s == "a":
            has_a = True
            s_num = "1"
        else:
            s_num = s
        ex = parse_exact(s_num)
        if ex is None:
            raise TuChoi(
                CV.ERR_BAN_KINH_NGOAI_MIEN,
                f"{context_id}: {field_name}={raw_val!r} không thuộc miền số chính xác",
                (context_id,),
            )
        try:
            sq = CV.binh_phuong_ban_kinh(ex)
        except GeometryError as exc:
            raise TuChoi(exc.code, f"{context_id}: {exc}", (context_id,)) from None
        _verify_number_in_quote(str(raw_val), quote, context_id)
        return ex, sq, bool(has_a)

    def _run_curved_route(self) -> Adapter3SimulationResult:
        from app.simulation.geometry import curved as CV
        from app.simulation.geometry.radical import (
            Radical,
            display as rad_display,
            multiply,
            sqrt_rational,
            times_rational,
        )
        PI = CV.PI

        decls: list[dict[str, Any]] = []
        stmts: list[dict[str, Any]] = []
        declared_names: set[str] = set()

        def add_decl(name: str, mtype: str, init_val: Any = None) -> None:
            if name not in declared_names:
                declared_names.add(name)
                decls.append({"name": name, "type": mtype, "initial_value": init_val})

        ky_hieu: str | None = "a" if self.payload.length_unit == "a" else None
        solid_meta: dict[str, dict[str, Any]] = {}
        section_meta: dict[str, dict[str, Any]] = {}

        for solid in self.payload.solids:
            _verify_quote_in_problem(solid.quote, self.problem_text, solid.solid_id)
            if solid.solid_type == "cone_frustum":
                raise TuChoi(
                    "CURVED_PRIMITIVE_BLOCKED_BY_KERNEL",
                    f"{solid.solid_id}: khối nón cụt độc lập không nằm trong KHOI_CONG; "
                    "hãy biểu diễn bằng hình nón gốc cắt bởi mặt phẳng song song với đáy",
                    (solid.solid_id,),
                )
            for lv in solid.local_vertices():
                if lv not in self.text_labels:
                    raise TuChoi(
                        "UNKNOWN_LABEL",
                        f"{solid.solid_id}: điểm {lv!r} không xuất hiện trong đề bài",
                        (solid.solid_id,),
                    )
            smap = {lv: solid.canonical_vertex(lv) for lv in solid.local_vertices()}
            self.solid_specs[solid.solid_id] = solid
            self.solid_local_to_canonical[solid.solid_id] = smap
            self.solid_canonical_name[solid.solid_id] = solid.notation

            r_val, r_sq, r_has_a = self._parse_curved_scalar(
                solid.radius, solid.quote, solid.solid_id, "radius"
            )
            if r_has_a:
                ky_hieu = "a"

            c_center = smap.get(solid.center, solid.center) if solid.center else None
            c_top = smap.get(solid.apex_or_top, solid.apex_or_top) if solid.apex_or_top else None
            c_rim = smap.get(solid.rim_point, solid.rim_point) if solid.rim_point else None

            center_var = ir_name(c_center) if c_center else f"tam_{solid.solid_id}"
            add_decl(center_var, "point3", [0, 0, 0])

            r_var = f"R_{solid.solid_id}" if len(self.payload.solids) > 1 else "R"
            add_decl(r_var, "float", rad_display(r_val))

            non_axial_kind = next(k for k, v in CV.KHOI_CONG.items() if not v.co_truc)
            curved_kind = solid.solid_type if solid.solid_type in CV.KHOI_CONG else non_axial_kind
            kc = CV.KHOI_CONG[curved_kind]
            co_dinh_nhon = kc.vai_dinh == "đỉnh"
            co_day_tren = kc.co_truc and not co_dinh_nhon
            top_var: str | None = None
            rim_var: str | None = None
            h_var: str | None = None
            h_val: Any = None
            h_sq: Fraction | None = None

            if kc.co_truc:
                h_val, h_sq, h_has_a = self._parse_curved_scalar(
                    solid.height, solid.quote, solid.solid_id, "height"
                )
                if h_has_a:
                    ky_hieu = "a"
                h_var = f"h_{solid.solid_id}" if len(self.payload.solids) > 1 else "h"
                add_decl(h_var, "float", rad_display(h_val))
                if c_top and isinstance(h_val, Fraction):
                    top_var = ir_name(c_top)
                    add_decl(top_var, "point3", [0, 0, str(h_val)])
                if c_rim and isinstance(r_val, Fraction):
                    rim_var = ir_name(c_rim)
                    add_decl(rim_var, "point3", [str(r_val), 0, 0])
            else:
                if c_rim and isinstance(r_val, Fraction):
                    rim_var = ir_name(c_rim)
                    add_decl(rim_var, "point3", [str(r_val), 0, 0])

            solid_var = f"khoi_{ir_name(solid.solid_id)}"
            add_decl(solid_var, "curved_solid", None)
            if kc.co_truc:
                suffix = f" {kc.vai_dinh} {c_top}" if co_dinh_nhon and c_top else (f" tâm {c_center}" if c_center else "")
                solid_label = f"{kc.danh_tu} tròn xoay {solid.notation}{suffix}"
            else:
                solid_label = f"Mặt cầu {solid.notation}" + (f" tâm {c_center}" if c_center else "")
            stmts.append(
                {
                    "kind": "construct_curved_solid",
                    "target_var": solid_var,
                    "curved_kind": curved_kind,
                    "anchor": center_var,
                    "apex_or_top": top_var,
                    "rim_point": rim_var,
                    "radius": None if rim_var else r_var,
                    "height": None if (not kc.co_truc or top_var) else h_var,
                    "label": solid_label,
                }
            )

            # Base circle & structural axis/generator segments for axial curved solids
            if kc.co_truc:
                mp_day_var = f"mp_day_{ir_name(solid.solid_id)}"
                day_var = f"duong_tron_day_{ir_name(solid.solid_id)}"
                add_decl(mp_day_var, "plane3", None)
                add_decl(day_var, "circle3", None)
                stmts.append(
                    {
                        "kind": "construct_plane_from_equation",
                        "target_var": mp_day_var,
                        "a": 0,
                        "b": 0,
                        "c": 1,
                        "d": 0,
                        "label": f"Mặt phẳng đáy ({c_center or 'O'})",
                    }
                )
                stmts.append(
                    {
                        "kind": "assign",
                        "target_var": day_var,
                        "expr": {
                            "kind": "intersect_plane_curved",
                            "solid": solid_var,
                            "plane": mp_day_var,
                        },
                    }
                )
                if co_day_tren and isinstance(h_val, Fraction):
                    mp_tren_var = f"mp_day_tren_{ir_name(solid.solid_id)}"
                    tren_var = f"duong_tron_day_tren_{ir_name(solid.solid_id)}"
                    add_decl(mp_tren_var, "plane3", None)
                    add_decl(tren_var, "circle3", None)
                    stmts.append(
                        {
                            "kind": "construct_plane_from_equation",
                            "target_var": mp_tren_var,
                            "a": 0,
                            "b": 0,
                            "c": 1,
                            "d": str(-h_val),
                            "label": f"Mặt phẳng đáy trên ({c_top or 'O′'})",
                        }
                    )
                    stmts.append(
                        {
                            "kind": "assign",
                            "target_var": tren_var,
                            "expr": {
                                "kind": "intersect_plane_curved",
                                "solid": solid_var,
                                "plane": mp_tren_var,
                            },
                        }
                    )
                if top_var:
                    truc_var = f"truc_{center_var}_{top_var}"
                    add_decl(truc_var, "segment3", None)
                    stmts.append(
                        {
                            "kind": "construct_segment",
                            "target_var": truc_var,
                            "endpoint_a": center_var,
                            "endpoint_b": top_var,
                            "label": f"Trục {c_center}{c_top}",
                        }
                    )
                if rim_var:
                    bk_var = f"ban_kinh_{center_var}_{rim_var}"
                    add_decl(bk_var, "segment3", None)
                    stmts.append(
                        {
                            "kind": "construct_segment",
                            "target_var": bk_var,
                            "endpoint_a": center_var,
                            "endpoint_b": rim_var,
                            "label": f"Bán kính đáy {c_center}{c_rim}",
                        }
                    )
                if co_dinh_nhon and top_var and rim_var:
                    ds_var = f"duong_sinh_{top_var}_{rim_var}"
                    add_decl(ds_var, "segment3", None)
                    stmts.append(
                        {
                            "kind": "construct_segment",
                            "target_var": ds_var,
                            "endpoint_a": top_var,
                            "endpoint_b": rim_var,
                            "label": f"Đường sinh {c_top}{c_rim}",
                        }
                    )

            solid_meta[solid.solid_id] = {
                "solid_var": solid_var,
                "solid_label": solid_label,
                "curved_kind": curved_kind,
                "center_var": center_var,
                "top_var": top_var,
                "rim_var": rim_var,
                "r_val": r_val,
                "r_sq": r_sq,
                "h_val": h_val,
                "h_sq": h_sq,
                "c_center": c_center,
                "c_top": c_top,
                "c_rim": c_rim,
            }

        for sec in self.payload.derived_sections:
            _verify_quote_in_problem(sec.quote, self.problem_text, sec.section_id)
            smeta = solid_meta[sec.target_solid_id]
            solid_var = smeta["solid_var"]
            curved_kind = smeta["curved_kind"]
            s_kc = CV.KHOI_CONG[curved_kind]
            r_val = smeta["r_val"]
            h_val = smeta["h_val"]

            if sec.plane_kind == "axial_section":
                if not s_kc.co_truc or not isinstance(r_val, Fraction) or not isinstance(h_val, Fraction):
                    raise TuChoi(
                        CV.ERR_NGOAI_BAO_DONG,
                        f"{sec.section_id}: thiết diện qua trục yêu cầu hình tròn xoay có bán kính và chiều cao hữu tỉ",
                        (sec.section_id,),
                    )
                a_var = smeta["rim_var"]
                if not a_var:
                    a_var = f"A_{ir_name(sec.section_id)}"
                    add_decl(a_var, "point3", [str(r_val), 0, 0])
                b_var = "B" if "B" not in declared_names else f"B_{ir_name(sec.section_id)}"
                add_decl(b_var, "point3", None)
                stmts.append(
                    {
                        "kind": "construct_point",
                        "target_var": b_var,
                        "expr": {
                            "kind": "divide_segment",
                            "a": a_var,
                            "b": smeta["center_var"],
                            "ratio": "2",
                        },
                        "label": "B",
                    }
                )
                sec_var = f"td_{ir_name(sec.section_id)}"
                add_decl(sec_var, "polygon3", None)
                if s_kc.vai_dinh == "đỉnh":
                    top_v = smeta["top_var"]
                    if not top_v:
                        top_v = f"S_{ir_name(sec.section_id)}"
                        add_decl(top_v, "point3", [0, 0, str(h_val)])
                    v_cycle = [top_v, a_var, b_var]
                    stmts.append(
                        {
                            "kind": "construct_polygon",
                            "target_var": sec_var,
                            "vertices": v_cycle,
                            "label": f"Thiết diện qua trục {smeta['c_top'] or 'S'}{smeta['c_rim'] or 'A'}B",
                        }
                    )
                else:
                    ap_var = "A_prime" if "A_prime" not in declared_names else f"A_prime_{ir_name(sec.section_id)}"
                    bp_var = "B_prime" if "B_prime" not in declared_names else f"B_prime_{ir_name(sec.section_id)}"
                    add_decl(ap_var, "point3", [str(r_val), 0, str(h_val)])
                    add_decl(bp_var, "point3", [str(-r_val), 0, str(h_val)])
                    v_cycle = [a_var, b_var, bp_var, ap_var]
                    stmts.append(
                        {
                            "kind": "construct_polygon",
                            "target_var": sec_var,
                            "vertices": v_cycle,
                            "label": "Thiết diện qua trục hình trụ",
                        }
                    )
                self.section_object_ids[sec.section_id] = sec_var
                self.section_plane_object_ids[sec.section_id] = sec_var
                self.section_cycles[sec.section_id] = tuple(v_cycle)
                section_meta[sec.section_id] = {
                    "sec_var": sec_var,
                    "mp_var": sec_var,
                    "shape": "polygon",
                    "ratio_from_apex": None,
                    "z_cut": None,
                }
                continue

            ratio_from_apex: Fraction | None = None
            z_cut: Fraction | None = None
            if sec.plane_kind == "parallel_to_base_at_distance":
                assert sec.distance_from_base is not None
                dist_val, _, _ = self._parse_curved_scalar(
                    sec.distance_from_base, sec.quote, sec.section_id, "distance_from_base"
                )
                if not isinstance(dist_val, Fraction):
                    raise TuChoi(
                        CV.ERR_NGOAI_BAO_DONG,
                        f"{sec.section_id}: khoảng cách mặt phẳng cắt phải hữu tỉ",
                        (sec.section_id,),
                    )
                z_cut = dist_val
                if isinstance(h_val, Fraction) and h_val != 0:
                    ratio_from_apex = Fraction(1) - (z_cut / h_val)
                a_c, b_c, c_c, d_c = "0", "0", "1", str(-z_cut)
            elif sec.plane_kind == "parallel_to_base_at_ratio":
                assert sec.ratio_from_apex is not None
                _verify_number_in_quote(sec.ratio_from_apex, sec.quote, sec.section_id)
                try:
                    rk = Fraction(sec.ratio_from_apex.strip())
                except Exception:
                    raise TuChoi(
                        CV.ERR_NGOAI_BAO_DONG,
                        f"{sec.section_id}: tỉ lệ cắt dọc trục phải hữu tỉ",
                        (sec.section_id,),
                    ) from None
                if not isinstance(h_val, Fraction) or rk <= 0 or rk >= 1:
                    raise TuChoi(
                        CV.ERR_NGOAI_BAO_DONG,
                        f"{sec.section_id}: tỉ lệ cắt dọc trục phải hữu tỉ trong khoảng (0, 1)",
                        (sec.section_id,),
                    )
                ratio_from_apex = rk
                z_cut = (Fraction(1) - rk) * h_val
                a_c, b_c, c_c, d_c = "0", "0", "1", str(-z_cut)
            else:
                assert sec.equation_coeffs is not None
                a_c, b_c, c_c, d_c = sec.equation_coeffs
                if Fraction(a_c) == 0 and Fraction(b_c) == 0 and Fraction(c_c) != 0:
                    z_cut = -Fraction(d_c) / Fraction(c_c)
                    if isinstance(h_val, Fraction) and h_val != 0:
                        ratio_from_apex = Fraction(1) - (z_cut / h_val)

            mp_var = f"mp_{ir_name(sec.section_id)}"
            sec_var = f"td_{ir_name(sec.section_id)}"
            shape = sec.section_shape or "circle"
            add_decl(mp_var, "plane3", None)
            add_decl(sec_var, "ellipse3" if shape == "ellipse" else "circle3", None)
            stmts.append(
                {
                    "kind": "construct_plane_from_equation",
                    "target_var": mp_var,
                    "a": a_c,
                    "b": b_c,
                    "c": c_c,
                    "d": d_c,
                    "label": f"Mặt phẳng ({sec.plane_name})",
                }
            )
            stmts.append(
                {
                    "kind": "assign",
                    "target_var": sec_var,
                    "expr": {
                        "kind": (
                            "intersect_plane_curved_ellipse"
                            if shape == "ellipse"
                            else "intersect_plane_curved"
                        ),
                        "solid": solid_var,
                        "plane": mp_var,
                    },
                }
            )
            self.section_object_ids[sec.section_id] = sec_var
            self.section_plane_object_ids[sec.section_id] = mp_var
            self.section_cycles[sec.section_id] = ()
            section_meta[sec.section_id] = {
                "sec_var": sec_var,
                "mp_var": mp_var,
                "shape": shape,
                "ratio_from_apex": ratio_from_apex,
                "z_cut": z_cut,
                "plane_name": sec.plane_name,
            }

        # Handle derived solids (e.g., upper cut cone from a parallel plane section on a parent cone)
        for g in self.payload.simulation_goals:
            _verify_quote_in_problem(g.quote, self.problem_text, g.goal_id)
            if g.kind == "construct_derived_solid":
                assert g.derived_solid_id and g.target_section_id
                parent_sid = g.parent_solid_id or next(
                    s.target_solid_id for s in self.payload.derived_sections if s.section_id == g.target_section_id
                )
                pmeta = solid_meta[parent_sid]
                p_kc = CV.KHOI_CONG[pmeta["curved_kind"]]
                sec_m = section_meta[g.target_section_id]
                rk = sec_m.get("ratio_from_apex")
                z_cut = sec_m.get("z_cut")
                if (
                    p_kc.vai_dinh != "đỉnh"
                    or rk is None
                    or z_cut is None
                    or not (Fraction(0) < rk < Fraction(1))
                ):
                    raise TuChoi(
                        "INVALID_DERIVED_SOLID",
                        f"{g.goal_id}: khối nón dẫn xuất yêu cầu mặt phẳng cắt song song đáy cắt phần trong của trục",
                        (g.goal_id,),
                    )
                o_cut_var = "O_prime" if "O_prime" not in declared_names else f"O_cat_{ir_name(g.derived_solid_id)}"
                r_cut_var = "r" if "r" not in declared_names else f"R_cat_{ir_name(g.derived_solid_id)}"
                upper_var = f"khoi_{ir_name(g.derived_solid_id)}"
                r_cut_val = times_rational(pmeta["r_val"], rk)
                add_decl(o_cut_var, "point3", [0, 0, str(z_cut)])
                add_decl(r_cut_var, "float", rad_display(r_cut_val))
                add_decl(upper_var, "curved_solid", None)
                top_v = pmeta["top_var"]
                if not top_v:
                    top_v = f"S_{ir_name(g.derived_solid_id)}"
                    add_decl(top_v, "point3", [0, 0, str(pmeta["h_val"])])
                stmts.append(
                    {
                        "kind": "construct_curved_solid",
                        "target_var": upper_var,
                        "curved_kind": pmeta["curved_kind"],
                        "anchor": o_cut_var,
                        "apex_or_top": top_v,
                        "rim_point": None,
                        "radius": r_cut_var,
                        "height": None,
                        "label": f"Hình nón nhỏ đỉnh {pmeta['c_top'] or 'S'} cắt bởi ({sec_m['plane_name']})",
                    }
                )
                self.solid_canonical_name[g.derived_solid_id] = g.derived_solid_id
                solid_meta[g.derived_solid_id] = {
                    "solid_var": upper_var,
                    "curved_kind": pmeta["curved_kind"],
                    "center_var": o_cut_var,
                    "top_var": top_v,
                    "rim_var": None,
                    "r_val": r_cut_val,
                    "r_sq": CV.binh_phuong_ban_kinh(r_cut_val),
                    "h_val": times_rational(pmeta["h_val"], rk),
                    "h_sq": CV.binh_phuong_ban_kinh(times_rational(pmeta["h_val"], rk)),
                    "c_center": o_cut_var,
                    "c_top": pmeta["c_top"],
                    "c_rim": None,
                    "parent_solid_id": parent_sid,
                    "ratio_from_apex": rk,
                }
                self._register_derived(
                    DerivedObjectIdentity(
                        derived_id=g.derived_solid_id,
                        kind="derived_solid",
                        internal_symbol=g.derived_solid_id,
                        display_label=f"Hình nón nhỏ đỉnh {pmeta['c_top'] or 'S'} cắt bởi ({sec_m['plane_name']})",
                        reference_text=f"hình nón nhỏ đỉnh {pmeta['c_top'] or 'S'} trên mặt phẳng ({sec_m['plane_name']})",
                        notation=None,
                        anonymous_in_source=True,
                        dependencies=(parent_sid, g.target_section_id),
                        provenance={
                            "derived_solid_id": g.derived_solid_id,
                            "parent_solid_id": parent_sid,
                            "section_id": g.target_section_id,
                            "ratio_from_apex": str(rk),
                        },
                    )
                )

        # Compile math_goals measurements into IR statements
        math_var_map: dict[str, str] = {}
        for mg in self.payload.math_goals:
            _verify_quote_in_problem(mg.quote, self.problem_text, mg.goal_id)
            if mg.kind == "measurement":
                assert mg.goal_type is not None
                if "section_id" in mg.target:
                    t_sec = mg.target["section_id"]
                    of_var = section_meta[t_sec]["sec_var"]
                elif (t_sid := measurement_scope(self.payload, mg)) in solid_meta:
                    of_var = solid_meta[t_sid]["solid_var"]
                else:
                    raise TuChoi(
                        "INVALID_MATH_GOAL_TARGET",
                        f"{mg.goal_id}: phép đo khối cong cần 'solid' hoặc 'section_id'",
                        (mg.goal_id,),
                    )
                kq_var = f"kq_{ir_name(mg.goal_id)}"
                add_decl(kq_var, "float", None)
                stmts.append(
                    {
                        "kind": "assign",
                        "target_var": kq_var,
                        "expr": {
                            "kind": "measure",
                            "quantity": mg.goal_type,
                            "of": of_var,
                        },
                    }
                )
                math_var_map[mg.goal_id] = kq_var

        program = {
            "program_id": "adapter3_curved_simulation",
            "title": self.problem_text[:120],
            "domain": "geometry",
            "memory_declarations": decls,
            "statements": stmts,
        }
        vr = validate_semantic_program(program)
        if not vr.ok:
            raise TuChoi(
                "ENGINE_IR_INVALID",
                f"IR khối cong sinh bởi Adapter /3 không qua thẩm định: {vr.error}",
            )
        try:
            ket = SemanticProgramInterpreter().execute(vr.spec)
        except GeometryError as exc:
            raise TuChoi(exc.code, str(exc)) from None
        except Exception as exc:  # noqa: BLE001
            code = getattr(exc, "code", None)
            if code:
                raise TuChoi(code, str(exc)) from None
            raise TuChoi("ENGINE_EXECUTION_FAILED", f"{type(exc).__name__}: {exc}") from None

        fm = ket.final_memory
        answers: dict[str, str] = {}
        answer_exact: dict[str, dict[str, Any]] = {}
        math_results: list[dict[str, Any]] = []
        dim_map = {"radius": 1, "distance": 1, "area": 2, "lateral_area": 2, "volume": 3, "angle": 0}

        for mg in self.payload.math_goals:
            if mg.kind == "measurement":
                assert mg.goal_type is not None
                kq_var = math_var_map[mg.goal_id]
                v = fm.get(kq_var)
                bac = dim_map[mg.goal_type]
                coef_str = rad_display(v)
                disp_str = f"{coef_str}{ky_hieu}^{bac}" if (ky_hieu and bac) else coef_str
                exact_obj = {
                    "coef": coef_str,
                    "dim": bac if ky_hieu else 0,
                    "unit": ky_hieu if bac else None,
                }
                answers[mg.goal_id] = disp_str
                answer_exact[mg.goal_id] = exact_obj
                math_results.append(
                    {
                        "goal_id": mg.goal_id,
                        "kind": "measurement",
                        "goal_type": mg.goal_type,
                        "value_display": disp_str,
                        "exact": exact_obj,
                        "certificate": {"rule": f"curved_measure_{mg.goal_type}", "kernel_var": kq_var},
                    }
                )
            elif mg.kind == "volume_ratio":
                assert mg.numerator_solid_id and mg.denominator_solid_id
                if mg.numerator_solid_id == mg.denominator_solid_id:
                    raise TuChoi("UNSUPPORTED_VOLUME_RATIO", f"{mg.goal_id}: hai khối trùng nhau", (mg.goal_id,))
                num_m = solid_meta[mg.numerator_solid_id]
                den_m = solid_meta[mg.denominator_solid_id]
                rk = num_m.get("ratio_from_apex")
                if rk is None or num_m.get("parent_solid_id") != mg.denominator_solid_id:
                    raise TuChoi("UNSUPPORTED_VOLUME_RATIO", f"{mg.goal_id}: không xác định được tỉ lệ đồng dạng dọc trục", (mg.goal_id,))
                ratio_val = rk ** 3
                v_num = CV.the_tich(fm[num_m["solid_var"]])
                v_den = CV.the_tich(fm[den_m["solid_var"]])
                if times_rational(v_den, ratio_val) != v_num:
                    raise TuChoi("ENGINE_SELF_CHECK_FAILED", f"{mg.goal_id}: tỉ số thể tích khối nón lệch kiểm chứng nhân ngược", (mg.goal_id,))
                coef_str = rad_display(ratio_val)
                exact_obj = {"coef": coef_str, "dim": 0, "unit": None}
                answers[mg.goal_id] = coef_str
                answer_exact[mg.goal_id] = exact_obj
                math_results.append(
                    {
                        "goal_id": mg.goal_id,
                        "kind": "volume_ratio",
                        "numerator_solid": mg.numerator_solid_id,
                        "denominator_solid": mg.denominator_solid_id,
                        "value_display": coef_str,
                        "exact": exact_obj,
                        "certificate": {
                            "rule": "axial_similarity_cubed_ratio",
                            "axis_ratio": str(rk),
                            "volume_ratio": coef_str,
                        },
                    }
                )
            elif mg.kind == "residual_volume":
                assert mg.parent_solid_id and mg.cut_solid_id
                if mg.parent_solid_id == mg.cut_solid_id:
                    raise TuChoi("NON_POSITIVE_RESIDUAL_VOLUME", f"{mg.goal_id}: khối cắt trùng khối gốc", (mg.goal_id,))
                parent_m = solid_meta[mg.parent_solid_id]
                cut_m = solid_meta[mg.cut_solid_id]
                rk = cut_m.get("ratio_from_apex")
                if rk is None or cut_m.get("parent_solid_id") != mg.parent_solid_id:
                    raise TuChoi("RESIDUAL_CONTAINMENT_UNPROVED", f"{mg.goal_id}: khối cắt không phải nón con cắt bởi mặt phẳng song song đáy", (mg.goal_id,))
                comp_ratio = Fraction(1) - (rk ** 3)
                if comp_ratio <= 0:
                    raise TuChoi("NON_POSITIVE_RESIDUAL_VOLUME", f"{mg.goal_id}: thể tích phần còn lại không dương", (mg.goal_id,))
                v_parent = CV.the_tich(fm[parent_m["solid_var"]])
                res_val = times_rational(v_parent, comp_ratio)
                # Cross-check against exact cone frustum formula: (1/3)*pi*h_frustum*(R^2 + R*r + r^2)
                R_sq = parent_m["r_sq"]
                r_sq = cut_m["r_sq"]
                R_r = sqrt_rational(R_sq * r_sq)
                h_frust = times_rational(sqrt_rational(parent_m["h_sq"]), Fraction(1) - rk)
                if isinstance(R_r, Fraction):
                    frust_direct = multiply(times_rational(h_frust, (R_sq + R_r + r_sq) * Fraction(1, 3)), PI)
                    if frust_direct != res_val:
                        raise TuChoi("ENGINE_SELF_CHECK_FAILED", f"{mg.goal_id}: thể tích nón cụt lệch công thức trực tiếp", (mg.goal_id,))
                coef_str = rad_display(res_val)
                disp_str = f"{coef_str}{ky_hieu}^3" if ky_hieu else coef_str
                exact_obj = {"coef": coef_str, "dim": 3 if ky_hieu else 0, "unit": ky_hieu}
                answers[mg.goal_id] = disp_str
                answer_exact[mg.goal_id] = exact_obj
                math_results.append(
                    {
                        "goal_id": mg.goal_id,
                        "kind": "residual_volume",
                        "parent_solid": mg.parent_solid_id,
                        "cut_solid": mg.cut_solid_id,
                        "complement_ratio": str(comp_ratio),
                        "value_display": disp_str,
                        "exact": exact_obj,
                        "certificate": {
                            "rule": "cone_frustum_parallel_cut_complement",
                            "axis_ratio": str(rk),
                            "complement_ratio": str(comp_ratio),
                            "direct_frustum_formula_verified": True,
                        },
                    }
                )

        state = build_simulation_state(vr.spec, ket, None)
        primary_curved_label = next(
            (m.get("solid_label") for m in solid_meta.values() if m.get("solid_label")),
            None,
        )

        def _clean_curved_text(val: Any) -> Any:
            if not isinstance(val, str):
                return val
            if primary_curved_label:
                val = re.sub(r"«[^»]*qua đại lượng»", primary_curved_label, val)
            val = re.sub(r",\s*(?:đi\s+)?qua đại lượng", "", val)
            val = re.sub(r"\bđi qua đại lượng\b", "", val).strip()
            return val

        for o in (state.get("scene") or {}).get("objects", []):
            oid = str(o.get("id") or "")
            if o.get("type") == "quantity" and not o.get("notation") and re.fullmatch(r"[a-zA-Z][a-zA-Z0-9₀-₉'’]*", oid):
                o["notation"] = oid
                if o.get("label") in (None, "", "Đại lượng đo"):
                    o["label"] = oid
                if o.get("reference") in (None, "", "đại lượng"):
                    o["reference"] = oid
            for fld in ("label", "display_label", "reference", "role"):
                if fld in o:
                    o[fld] = _clean_curved_text(o[fld])
        state["targets"] = list(math_var_map.values())
        canh = build_scene3d(state)
        for o in canh["objects"]:
            okind = o.get("type")
            oid = str(o.get("id") or "")
            if okind in ("circle3", "ellipse3") and not o.get("surface_role"):
                if "CONSTRUCT_BASE" in (o.get("formation_roles") or ()) or oid.startswith("duong_tron_day"):
                    o["surface_role"] = "BASE_REGION"
                else:
                    o["surface_role"] = "SECTION_REGION"
            elif okind == "quantity" and not o.get("notation") and re.fullmatch(r"[a-zA-Z][a-zA-Z0-9₀-₉'’]*", oid):
                o["notation"] = oid
                if o.get("label") in (None, "", "Đại lượng đo"):
                    o["label"] = oid
                if o.get("reference") in (None, "", "đại lượng"):
                    o["reference"] = oid
            for fld in ("label", "display_label", "reference", "role"):
                if fld in o:
                    o[fld] = _clean_curved_text(o[fld])
        for ev in canh.get("events", []):
            for fld in ("display_label", "learner_text"):
                if fld in ev:
                    ev[fld] = _clean_curved_text(ev[fld])
        for stp in (canh.get("formation") or {}).get("steps") or []:
            for fld in ("label", "learner_text"):
                if fld in stp:
                    stp[fld] = _clean_curved_text(stp[fld])
        by_id = {o["id"]: o for o in canh["objects"]}

        solid_descriptors = [
            {
                "solid_id": sid,
                "solid_type": s.solid_type,
                "notation": s.notation,
                "canonical_notation": s.notation,
                "coordinate_frame_id": s.coordinate_frame_id,
                "local_to_canonical": dict(self.solid_local_to_canonical[sid]),
                "scene_object_id": solid_meta[sid]["solid_var"],
            }
            for sid, s in self.solid_specs.items()
        ]
        for d in self.derived_identities:
            if d.kind == "derived_solid":
                solid_descriptors.append(
                    {
                        "solid_id": d.derived_id,
                        "solid_type": "cone",
                        "notation": d.notation,
                        "canonical_notation": d.internal_symbol,
                        "coordinate_frame_id": "root",
                        "local_to_canonical": {},
                        "scene_object_id": solid_meta[d.derived_id]["solid_var"],
                        "derived_id": d.derived_id,
                    }
                )

        sim_goal_outcomes: list[dict[str, Any]] = []
        for g in self.payload.simulation_goals:
            if g.kind == "construct_object":
                assert g.target_solid_id
                oid = solid_meta[g.target_solid_id]["solid_var"]
                sim_goal_outcomes.append(
                    {
                        "goal_id": g.goal_id,
                        "kind": g.kind,
                        "status": "CONSTRUCTED" if oid in by_id else "MISSING",
                        "scene_object_ids": [oid],
                        "style_role": g.style_role,
                    }
                )
            elif g.kind == "construct_plane_section":
                assert g.target_section_id
                sec_oid = self.section_object_ids[g.target_section_id]
                plane_oid = self.section_plane_object_ids[g.target_section_id]
                sim_goal_outcomes.append(
                    {
                        "goal_id": g.goal_id,
                        "kind": g.kind,
                        "status": "CONSTRUCTED" if sec_oid in by_id else "MISSING",
                        "scene_object_ids": [sec_oid, plane_oid],
                        "section_object_id": sec_oid,
                        "plane_object_id": plane_oid,
                        "section_vertex_ids": list(self.section_cycles.get(g.target_section_id, ())),
                        "style_role": g.style_role,
                    }
                )
            elif g.kind == "construct_derived_solid":
                assert g.derived_solid_id
                oid = solid_meta[g.derived_solid_id]["solid_var"]
                sim_goal_outcomes.append(
                    {
                        "goal_id": g.goal_id,
                        "kind": g.kind,
                        "status": "CONSTRUCTED" if oid in by_id else "MISSING",
                        "scene_object_ids": [oid],
                        "derived_solid_id": g.derived_solid_id,
                        "style_role": g.style_role,
                    }
                )
            elif g.kind == "highlight_geometry":
                resolved_oids = []
                for ref in g.target_refs:
                    if ref in solid_meta:
                        resolved_oids.append(solid_meta[ref]["solid_var"])
                    elif ref in self.section_object_ids:
                        resolved_oids.append(self.section_object_ids[ref])
                    elif ir_name(ref) in by_id:
                        resolved_oids.append(ir_name(ref))
                for oid in resolved_oids:
                    if oid in by_id and "target" not in by_id[oid]["display_group"]:
                        by_id[oid]["display_group"].append("target")
                sim_goal_outcomes.append(
                    {
                        "goal_id": g.goal_id,
                        "kind": g.kind,
                        "status": "HIGHLIGHTED",
                        "scene_object_ids": resolved_oids,
                        "style_role": g.style_role,
                    }
                )
            elif g.kind == "construction_sequence":
                steps_out = [
                    {
                        "step_index": ev["step_index"],
                        "action": ev["action"],
                        "object_id": ev.get("object"),
                        "display_label": ev.get("display_label"),
                        "learner_text": ev.get("learner_text"),
                        "semantic_kind": ev.get("semantic_kind"),
                        "depends": list(ev.get("depends") or []),
                    }
                    for ev in canh.get("events", [])
                ]
                sim_goal_outcomes.append(
                    {
                        "goal_id": g.goal_id,
                        "kind": g.kind,
                        "status": "SEQUENCED",
                        "scene_object_ids": [s["object_id"] for s in steps_out if s.get("object_id")],
                        "construction_steps": steps_out,
                        "style_role": g.style_role,
                    }
                )

        canh["simulation_contract"] = {
            "schema_version": ROUTE_D_SIMULATION_SCHEMA_VERSION,
            "adapter_version": ADAPTER_V3_VERSION,
            "contract_version": TYPED_FACT_NEXT_SCHEMA_VERSION,
            "solids": solid_descriptors,
            "derived_identities": [d.model_dump() for d in self.derived_identities],
            "verified_relations": [],
            "simulation_goals": sim_goal_outcomes,
            "math_goals": math_results,
        }
        pts_out = {
            k: (v.x, v.y, v.z) for k, v in fm.items() if hasattr(v, "x") and hasattr(v, "y") and hasattr(v, "z")
        }
        return Adapter3SimulationResult(
            status="SERVED",
            scene3d=canh,
            simulation_state=state,
            solids=solid_descriptors,
            derived_identities=[d.model_dump() for d in self.derived_identities],
            verified_relations=[],
            simulation_goals=sim_goal_outcomes,
            math_goals=math_results,
            answers=answers,
            answer_exact=answer_exact,
            length_unit=ky_hieu,
            points=pts_out,
            metric=None,
            kernel_check=True,
            trace=[],
            calls=stmts,
        )

    def _preflight_curved_relations(self) -> None:
        """Consume only existing structural identity/frame semantics; never ignore a geometric assertion."""
        solids = {solid.solid_id: solid for solid in self.payload.solids}
        for relation in self.payload.relations:
            _verify_quote_in_problem(relation.quote, self.problem_text, relation.relation_id)
            if relation.kind == "shared_vertices":
                for left, right in relation.pairs:
                    sa, a = parse_qualified_ref(left)
                    sb, b = parse_qualified_ref(right)
                    if solids[sa].canonical_vertex(a) != solids[sb].canonical_vertex(b):
                        raise TuChoi("SHARED_ENTITY_MISMATCH", f"{relation.relation_id}: hai đỉnh khác danh tính", (relation.relation_id,))
            elif relation.kind == "coordinate_frame":
                if relation.frame_id != "root" or solids[relation.solid_id].coordinate_frame_id != "root":
                    raise TuChoi("COORDINATE_FRAME_DISCONNECTED", f"{relation.relation_id}: hệ tọa độ không nối với root", (relation.relation_id,))
            else:
                raise TuChoi("BRIDGE_UNSUPPORTED_RELATION", f"{relation.relation_id}: chưa kiểm chứng quan hệ {relation.kind} trên khối cong", (relation.relation_id,))

    def run(self) -> Adapter3SimulationResult:
        if any(s.solid_type not in ("pyramid", "prism") for s in self.payload.solids):
            from app.simulation.geometry_functions.typed_fact_next_bridge import _kiem_pham_vi_tien_de
            try:
                # No Bridge/Source Gate reaches this route, and it reads no premise: validate their ownership first.
                _kiem_pham_vi_tien_de(self.payload, {s.solid_id: s for s in self.payload.solids})
                self._preflight_curved_relations()
                res = self._run_curved_route()
                if res.status == "SERVED":          # the planner has no curved solids: no shared gate verdict exists
                    res.source_verification = {"authority": LEGACY_SOURCE_AUTHORITY,
                                               "gate_unavailable": "BRIDGE_UNSUPPORTED_CURVED"}
                return res
            except TuChoi as exc:
                return Adapter3SimulationResult(
                    status="REFUSED",
                    code=exc.code,
                    reason=exc.reason,
                    failed_calls=exc.calls,
                )
        dung: _Dung | None = None
        try:
            source_verification = _shared_source_gate(self.payload)
            self._compile_solids()
            self._compile_premises()
            self._compile_derived_sections()
            math_call_ids = self._compile_derived_solids_and_goals()
            rel_certificates = self._validate_structural_relations()

            parsed_calls = doc_ke_hoach({"calls": self.calls})
            from app.simulation.geometry_functions.engine import _don_vi

            ky_hieu = _don_vi(parsed_calls)
            if self.payload.length_unit == "a":
                ky_hieu = "a"
            elif self.payload.length_unit == "1" and ky_hieu == "a":
                raise TuChoi(
                    "NON_HOMOGENEOUS_LENGTHS",
                    "length_unit='1' mâu thuẫn với độ dài chứa tham số 'a' trong giả thiết",
                )

            dung = _Dung(parsed_calls, self.problem_text, ky_hieu)
            dung.thu_khoi()
            # Ensure multi-solid configurations sharing the same base also trigger full composite verification & volume certificates
            if len(dung.khoi) > 1 and not dung.composite:
                dung.composite = True
                outputs = {
                    c.args.point
                    for c in dung.of(
                        "midpoint",
                        "centroid",
                        "divide_segment",
                        "intersect_line_line",
                        "intersect_line_plane",
                    )
                }
                outputs |= {
                    c.args.image
                    for c in dung.of(
                        "orthogonal_projection",
                        "orthogonal_projection_line",
                        "translate_point",
                    )
                }
                roots = [
                    k
                    for k in dung.khoi.values()
                    if not (set(k.base) | set(k.top) | {k.apex}) & outputs
                ]
                if roots:
                    dung.root = roots[0]

            dung.bo_cuc_day()
            dung.giai_phu_thuoc()
            self._certify_section_boundary(dung, rel_certificates)
            dung.mat_phu = self.mat_phu
            dung.ten_mat_phu = self.ten_mat_phu
            dung.kiem()
            dung.kiem_mat_cat()
            # Compute volume certificates for single-solid too when needed by math_goals
            if not dung.composite:
                for k in dung.khoi.values():
                    dung.volume_certificates[k.name] = dung._the_tich2_khoi(k)

            self._verify_geometric_relations_and_cuts(dung, rel_certificates)

            # Phase 2 IR folding: once `_Dung` has verified `mat_phu` (`MAT_SONG_SONG` / `MAT_VUONG_DUONG` / `MAT_HAI_DUONG`)
            # and certified the exact rational cut ratios $t_k \in (0, 1] \cap \mathbb{Q}$ on each cut edge, fold the
            # auxiliary plane-spanning points (`X1, X2, F1, F2`) and `intersect_line_plane` calls into exact edge divisions
            # (`midpoint` / `divide_segment`) and `section(solid, plane=cycle[:3])` so dummy auxiliary points do not clutter
            # `Scene3D` or exhaust `MAX_MEMORY_DECLARATIONS = 32`.
            if self.derived_sections_present():
                dung = self._rebuild_folded_dung(dung, ky_hieu)

            program, hoi = dung.bien_dich()
            # Match each derived section to its emitted `construct_section` and `construct_plane` statements
            sec_stmts = [
                st for st in program["statements"] if st.get("kind") == "construct_section"
            ]
            for idx_sec, sec in enumerate(self.payload.derived_sections):
                if idx_sec < len(sec_stmts):
                    sec_var = sec_stmts[idx_sec]["target_var"]
                    mp_var = sec_stmts[idx_sec]["plane"]
                    self.section_object_ids[sec.section_id] = sec_var
                    self.section_plane_object_ids[sec.section_id] = mp_var
                    for st in program["statements"]:
                        if st.get("kind") == "construct_plane" and st.get("target_var") == mp_var:
                            st["label"] = f"({sec.plane_name})"

            vr = validate_semantic_program(program)
            if not vr.ok:
                raise TuChoi(
                    "ENGINE_IR_INVALID",
                    f"IR sinh bởi Adapter /3 không qua thẩm định: {vr.error}",
                )
            to_po: Any = (
                next(iter(self.solid_topology_contracts.values()))
                if len(self.solid_topology_contracts) == 1
                else (self.solid_topology_contracts or None)
            )
            hoan_thien_res = hoan_thien_dung_hinh(vr.spec, to_po)
            spec = hoan_thien_res.spec
            if not validate_semantic_program(spec).ok:
                # If full multi-solid pedagogical segment expansion exceeds MAX_MEMORY_DECLARATIONS (32),
                # expand the root solid first and fall back to `vr.spec` if still over budget.
                root_key = frozenset(map(ir_name, [dung.root.apex, *dung.root.base])) if dung.root.apex else frozenset()
                root_to_po = self.solid_topology_contracts.get(root_key)
                root_spec = hoan_thien_dung_hinh(vr.spec, root_to_po).spec if root_to_po else vr.spec
                spec = root_spec if validate_semantic_program(root_spec).ok else vr.spec
            G = dung.metric()
            try:
                with _metric.using(G):
                    ket = SemanticProgramInterpreter().execute(spec)
            except Exception as exc:  # noqa: BLE001
                code = getattr(exc, "code", None)
                if code in {"PLANE_DOES_NOT_CUT", "PLANE_TOUCHES_VERTEX", "PLANE_TOUCHES_EDGE"}:
                    raise TuChoi(code, str(exc)) from None
                raise TuChoi("ENGINE_EXECUTION_FAILED", f"{type(exc).__name__}: {exc}") from None

            fm = ket.final_memory
            for c in dung.of("ask_volume"):
                expected = dung.volume_certificates.get(c.args.solid)
                if expected is not None and _binh_phuong(fm.get(hoi[c.id])) != expected:
                    raise TuChoi(
                        "ENGINE_SELF_CHECK_FAILED",
                        "thể tích thực thi khác chứng chỉ diện tích Gram × đường cao",
                        (c.id,),
                    )
            kernel_ok = all(
                (lambda v: v is not None and (v.x, v.y, v.z) == dung.pts[t])(fm.get(ir_name(t)))
                for t in dung.pts
            )
            if not kernel_ok:
                raise TuChoi(
                    "ENGINE_SELF_CHECK_FAILED",
                    "tọa độ điểm thực thi trong kernel khác bố cục engine",
                )
            if hong := [t for t in dung.sections if not fm[t].is_closed]:
                raise TuChoi(
                    "SECTION_EMPTY",
                    f"mặt phẳng không cắt khối thành một đa giác khép kín ({hong})",
                )

            math_results, answers, answer_exact = self._compute_certified_math_goals(
                dung, fm, hoi, math_call_ids, ky_hieu
            )

            # Build SimulationState and Scene3D
            with _metric.using(G):
                state = build_simulation_state(
                    spec,
                    ket,
                    to_po,
                    prefer_declared_plane_names=bool(self.mat_phu),
                )
                state["targets"] = [hoi[cid] for cid in math_call_ids.values() if cid in hoi]
                aux_ids = {ir_name(p) for p in self.aux_hidden_points}
                vai = {
                    o["id"]: o.get("role")
                    for o in state["scene"]["objects"]
                    if (o.get("producer") or "").startswith("construct_point.")
                }
                for obj in state["scene"]["objects"]:
                    if obj["id"] in aux_ids:
                        obj["role"] = "Điểm dựng phụ"
                        obj["synthetic"] = True
                        state["provenance"].setdefault(obj["id"], {})["binding"] = "AUXILIARY"
                canh = build_scene3d(state)
                _ke_diem_dung(canh, vai)
                _gan_nhan_chung_hinh_chieu(canh, spec, fm)
                _gan_nhan_chung_duong_cao_chinh_xac(canh, G, trace=dung.trace)

            solid_descriptors, sim_goal_outcomes = self._enrich_scene3d_and_goals(canh)

            canh["chart_metric"] = G.as_json()
            if ky_hieu:
                canh["length_unit"] = {
                    "symbol": ky_hieu,
                    "display_scale": f"{ky_hieu} = 1 đơn vị dựng",
                    "is_given": False,
                }
            canh["simulation_contract"] = {
                "schema_version": ROUTE_D_SIMULATION_SCHEMA_VERSION,
                "adapter_version": ADAPTER_V3_VERSION,
                "contract_version": TYPED_FACT_NEXT_SCHEMA_VERSION,
                "solids": solid_descriptors,
                "derived_identities": [d.model_dump() for d in self.derived_identities],
                "verified_relations": rel_certificates,
                "simulation_goals": sim_goal_outcomes,
                "math_goals": math_results,
                "source_verification": source_verification,
            }

            return Adapter3SimulationResult(
                status="SERVED",
                scene3d=canh,
                simulation_state=state,
                solids=solid_descriptors,
                derived_identities=[d.model_dump() for d in self.derived_identities],
                verified_relations=rel_certificates,
                source_verification=source_verification,
                simulation_goals=sim_goal_outcomes,
                math_goals=math_results,
                answers=answers,
                answer_exact=answer_exact,
                length_unit=ky_hieu,
                points=dict(dung.pts),
                metric=G.as_json(),
                kernel_check=True,
                trace=dung.trace,
                calls=self.calls,
            )
        except TuChoi as exc:
            return Adapter3SimulationResult(
                status="REFUSED",
                code=exc.code,
                reason=exc.reason,
                failed_calls=exc.calls,
                trace=dung.trace if dung else [],
                calls=self.calls,
            )


def run_typed_fact_next_route(
    raw_payload: dict[str, Any] | TypedFactNextPayload,
) -> Adapter3SimulationResult:
    """Validate a `typed-fact-next/1` payload and execute Adapter /3 offline simulation orchestration."""
    try:
        payload = parse_typed_fact_next(raw_payload)
    except TypedFactNextValidationError as exc:
        return Adapter3SimulationResult(
            status="REFUSED",
            code=exc.code,
            reason=exc.detail,
        )
    # Public boundary (run `hybrid-contract-v2`, P1): malformed input is refused by the schema above; a late input-shape
    # error keeps its own input code; anything else is OUR fault, recorded as a technical refusal — never shown as the
    # user's data error, never escaping as an exception.
    try:
        return _Adapter3Compiler(payload).run()
    except TypedFactNextValidationError as exc:
        return Adapter3SimulationResult(status="REFUSED", code=exc.code, reason=exc.detail)
    except Exception as exc:  # noqa: BLE001 — boundary record of an unexpected internal fault, typed, not a data verdict
        return Adapter3SimulationResult(status="REFUSED", code="ADAPTER_INTERNAL_ERROR",
                                        reason=f"{type(exc).__name__}: {exc}")


def build_adapter3_simulation_response(
    raw_payload: dict[str, Any] | TypedFactNextPayload,
) -> dict[str, Any]:
    """Build a preview-compatible (`hybrid-Flat-preview/1` + `route_d`) JSON envelope from Adapter /3."""
    problem_text = (
        raw_payload.problem_text
        if isinstance(raw_payload, TypedFactNextPayload)
        else str((raw_payload or {}).get("problem_text") or "")
    )
    res = run_typed_fact_next_route(raw_payload)
    refusal = (
        {"code": res.code, "detail": res.reason, "calls": list(res.failed_calls)}
        if res.status != "SERVED"
        else None
    )
    route_d_payload = {
        "schema_version": ROUTE_D_SIMULATION_SCHEMA_VERSION,
        "adapter_version": ADAPTER_V3_VERSION,
        "contract_version": TYPED_FACT_NEXT_SCHEMA_VERSION,
        "status": res.status,
        "refusal": refusal,
        "solids": res.solids,
        "derived_identities": res.derived_identities,
        "verified_relations": res.verified_relations,
        "source_verification": res.source_verification,
        "simulation_goals": res.simulation_goals,
        "math_goals": res.math_goals,
        "answers": res.answers,
        "answer_exact": res.answer_exact,
        "length_unit": res.length_unit,
        "scene3d": res.scene3d,
        "points": {k: [str(c) for c in v] for k, v in res.points.items()},
        "metric": res.metric,
        "kernel_check": res.kernel_check,
        "trace": res.trace,
        "calls": res.calls,
    }
    route_b_compat = {
        "status": res.status,
        "refusal": refusal,
        "answers": res.answers,
        "answer_exact": res.answer_exact,
        "length_unit": res.length_unit,
        "points": {k: [str(c) for c in v] for k, v in res.points.items()},
        "metric": res.metric,
        "kernel_check": res.kernel_check,
        "scene3d": res.scene3d,
        "planner": {
            "version": ADAPTER_V3_VERSION,
            "calls": res.calls,
            "trace": res.trace,
            "goal_checks": {},
            "negated_checks": {},
        },
        "trace": res.trace,
        "calls": res.calls,
    }
    return {
        "schema_version": HYBRID_PREVIEW_SCHEMA_VERSION,
        "adapter_version": ADAPTER_V3_VERSION,
        "contract_version": TYPED_FACT_NEXT_SCHEMA_VERSION,
        "problem_text": problem_text,
        "route_a": None,
        "route_b": route_b_compat,
        "route_d": route_d_payload,
        "comparison": {
            "status_pair": f"NONE_VS_{res.status}",
            "answer_agreement": "NOT_APPLICABLE",
            "scene3d_bucket": "ROUTE_B_ONLY" if res.scene3d else "NEITHER",
        },
    }
