"""Versioned TypedFactNext (`typed-fact-next/1`) contract for simulation-first orchestration.

Coexists with the frozen `TypedFact` (`typed-facts/2`) contract in `planner.py` without modifying it.
"""

from __future__ import annotations

import re
from typing import Annotated, Any, ClassVar, Literal

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, model_validator

from app.simulation.geometry_functions.registry import Label
from app.simulation.semantic_program.measure_contract import NGHIA_VU_DO

MathGoalType = Literal[*tuple(NGHIA_VU_DO)]

TYPED_FACT_NEXT_SCHEMA_VERSION = "typed-fact-next/1"
TYPED_FACT_NEXT_V2_SCHEMA_VERSION = "typed-fact-next/2"

NonEmptyText = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]
IdentifierStr = Annotated[
    str,
    StringConstraints(strip_whitespace=True, pattern=r"^[A-Za-z0-9_.:-]+$"),
]

_PYRAMID_NOTATION_RE = re.compile(r"^(?P<apex>[A-Z][A-Z0-9']*)\.(?P<base>[A-Z0-9']+)$")
_PRISM_NOTATION_RE = re.compile(r"^(?P<b1>[A-Z0-9']+)\.(?P<b2>[A-Z0-9']+)$")
_VERTEX_TOKEN_RE = re.compile(r"[A-Z][0-9']*")
_QUALIFIED_REF_RE = re.compile(
    r"^(?:(?P<solid_id>[A-Za-z0-9_-]+)::)?(?P<label>[A-Z][A-Z0-9']*)$"
)


class TypedFactNextValidationError(ValueError):
    """Structured fail-closed validation error for `typed-fact-next/1`."""

    def __init__(self, code: str, detail: str) -> None:
        super().__init__(f"{code}: {detail}")
        self.code = code
        self.detail = detail


def split_vertex_chain(chain: str) -> tuple[str, ...]:
    """Split a polygon vertex chain like `ABCD` or `A'B'C'` into individual vertex labels."""
    tokens = _VERTEX_TOKEN_RE.findall(chain.strip())
    if not tokens or "".join(tokens) != chain.strip():
        raise TypedFactNextValidationError(
            "INVALID_VERTEX_CHAIN",
            f"Cannot parse vertex chain {chain!r}.",
        )
    return tuple(tokens)


def parse_qualified_ref(ref: str) -> tuple[str | None, str]:
    """Parse an optional solid-qualified vertex reference (`solid_id::label` or `label`)."""
    m = _QUALIFIED_REF_RE.match(ref.strip())
    if not m:
        raise TypedFactNextValidationError(
            "INVALID_QUALIFIED_REF",
            f"Invalid vertex reference {ref!r}; expected 'LABEL' or 'solid_id::LABEL'.",
        )
    return m.group("solid_id"), m.group("label")


# Closed input contract: the runtime authority; run-local JSON is its preregistered snapshot.
KIND_ALLOWED_FIELDS = {'math_goal': {'volume_ratio': ['denominator_solid_id', 'goal_id', 'kind', 'numerator_solid_id', 'quote'],
               'residual_volume': ['cut_solid_id', 'goal_id', 'kind', 'parent_solid_id', 'quote'],
               'measurement': ['goal_id', 'goal_type', 'kind', 'quote', 'solid_id', 'target']},
 'simulation_goal': {'construct_object': ['goal_id',
                                          'kind',
                                          'quote',
                                          'style_role',
                                          'target_refs',
                                          'target_solid_id'],
                     'construct_plane_section': ['goal_id',
                                                 'kind',
                                                 'quote',
                                                 'style_role',
                                                 'target_refs',
                                                 'target_section_id',
                                                 'target_solid_id'],
                     'construct_derived_solid': ['apex_ref',
                                                 'derived_solid_id',
                                                 'goal_id',
                                                 'kind',
                                                 'parent_solid_id',
                                                 'quote',
                                                 'style_role',
                                                 'target_refs',
                                                 'target_section_id'],
                     'highlight_geometry': ['goal_id',
                                            'kind',
                                            'quote',
                                            'style_role',
                                            'target_refs',
                                            'target_section_id',
                                            'target_solid_id'],
                     'construction_sequence': ['goal_id',
                                               'kind',
                                               'quote',
                                               'style_role',
                                               'target_refs',
                                               'target_solid_id']},
 'relation': {'containment': ['container_ref',
                              'kind',
                              'member_ref',
                              'quote',
                              'relation_id',
                              'section_id',
                              'solid_id'],
              'shared_vertices': ['kind',
                                  'pairs',
                                  'quote',
                                  'relation_id',
                                  'section_id',
                                  'solid_a',
                                  'solid_b',
                                  'solid_id'],
              'shared_faces': ['face_a',
                               'face_b',
                               'kind',
                               'quote',
                               'relation_id',
                               'section_id',
                               'solid_a',
                               'solid_b',
                               'solid_id'],
              'parallel': ['entity_a',
                           'entity_b',
                           'kind',
                           'quote',
                           'relation_id',
                           'section_id',
                           'solid_a',
                           'solid_b',
                           'solid_id'],
              'perpendicular': ['entity_a',
                                'entity_b',
                                'kind',
                                'quote',
                                'relation_id',
                                'section_id',
                                'solid_a',
                                'solid_b',
                                'solid_id'],
              'section_membership': ['kind', 'member_refs', 'quote', 'relation_id', 'section_id', 'solid_id'],
              'coordinate_frame': ['anchor_refs',
                                   'frame_id',
                                   'kind',
                                   'quote',
                                   'relation_id',
                                   'section_id',
                                   'solid_id']}}
GOAL_OPERAND_SHAPES = {'point': 'ref',
 'segment': 'refs2=',
 'line': 'refs2=',
 'line1': 'refs2=',
 'line2': 'refs2=',
 'plane': 'refs3',
 'plane1': 'refs3',
 'plane2': 'refs3',
 'polygon': 'refs3',
 'solid': 'solid_name',
 'solid_id': 'id',
 'section_id': 'id'}
GOAL_TARGET_ALTERNATIVES = {'distance': [['segment'],
              ['point', 'plane'],
              ['point', 'line'],
              ['line1', 'line2'],
              ['line', 'plane'],
              ['plane1', 'plane2']],
 'angle': [['line', 'plane'], ['line1', 'line2'], ['plane1', 'plane2']],
 'volume': [['solid'], ['solid_id']],
 'radius': [['solid'], ['section_id']],
 'lateral_area': [['solid']],
 'area': [['polygon'], ['section_id'], ['solid']]}

_KIND_GROUPS = {"MathGoalSpec": ("math_goal", "INVALID_MATH_GOAL"),
                "SimulationGoalSpec": ("simulation_goal", "INVALID_SIMULATION_GOAL"),
                "GeometricRelationSpec": ("relation", "INVALID_RELATION_SPEC")}


def _validate_goal_target(goal) -> None:
    target = goal.target
    alternatives = GOAL_TARGET_ALTERNATIVES[goal.goal_type]
    scopes = {"solid", "solid_id"}
    allowed = set().union(*(set(a) for a in alternatives)) | scopes
    if set(target) - allowed:
        raise TypedFactNextValidationError("INVALID_MATH_GOAL", f"{goal.goal_id}: unexpected target keys {sorted(set(target) - allowed)}")
    for key, value in target.items():
        shape = GOAL_OPERAND_SHAPES[key]
        valid = isinstance(value, str) and bool(value.strip()) if shape == "solid_name" else _hinh_dung(value, shape)
        if not valid or shape.startswith("refs") and len(set(value)) != len(value):
            raise TypedFactNextValidationError("INVALID_MATH_GOAL", f"{goal.goal_id}: malformed operand {key!r}, expected {shape}")
    operands = set(target) - scopes
    if operands and set(target) & scopes:   # CIC-D1 (locked V2 grammar): ownership is MathGoalSpec.solid_id, never a target key
        raise TypedFactNextValidationError("INVALID_MATH_GOAL", f"{goal.goal_id}: scope keys {sorted(set(target) & scopes)} "
                                           "beside target operands; declare the goal's solid_id")
    if operands:
        valid = any(operands == set(a) for a in alternatives)
    else:
        valid = any(set(target) == set(a) for a in alternatives)
    if not valid:
        raise TypedFactNextValidationError("INVALID_MATH_GOAL", f"{goal.goal_id}: inapplicable target for {goal.goal_type}")


def measurement_scope(p, goal) -> str | None:
    """Resolve the ONE validated scope without deleting the original target/provenance."""
    sections = {s.section_id: s.target_solid_id for s in p.derived_sections}
    return (goal.solid_id or goal.target.get("solid_id") or resolve_solid_name(p, goal.target.get("solid"))
            or sections.get(goal.target.get("section_id")))


class ClosedNextModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    @model_validator(mode="before")
    @classmethod
    def _closed_kind_fields(cls, value):
        policy = _KIND_GROUPS.get(cls.__name__)  # S4: one per-kind field applicability authority
        if policy and isinstance(value, dict) and value.get("kind") in KIND_ALLOWED_FIELDS[policy[0]]:
            unexpected = set(value) - set(KIND_ALLOWED_FIELDS[policy[0]][value["kind"]])
            if unexpected:
                raise TypedFactNextValidationError(policy[1], f"{value['kind']}: inapplicable fields {sorted(unexpected)}")
        return value


class SolidSpec(ClosedNextModel):
    """Declaration of a 3D solid with local-to-canonical vertex bindings."""

    solid_id: IdentifierStr
    solid_type: Literal["pyramid", "prism", "cylinder", "cone", "sphere", "cone_frustum"] = "pyramid"
    center: NonEmptyText | None = None
    apex_or_top: NonEmptyText | None = None
    rim_point: NonEmptyText | None = None
    radius: NonEmptyText | None = None
    height: NonEmptyText | None = None
    notation: NonEmptyText
    quote: NonEmptyText
    vertex_bindings: dict[Label, Label] = Field(default_factory=dict)
    coordinate_frame_id: IdentifierStr = "root"

    @model_validator(mode="after")
    def _validate_notation(self) -> "SolidSpec":
        if self.solid_type == "pyramid":
            apex, base = self.apex_and_base()
            if len(base) < 3 or apex in base or len(set(base)) != len(base):
                raise TypedFactNextValidationError(
                    "INVALID_SOLID_NOTATION",
                    f"Pyramid notation {self.notation!r} must have a distinct apex and >=3 distinct base vertices.",
                )

        elif self.solid_type == "prism":
            b1, b2 = self.prism_bases()
            if len(b1) < 3 or len(b1) != len(b2) or set(b1) & set(b2):
                raise TypedFactNextValidationError(
                    "INVALID_SOLID_NOTATION",
                    f"Prism notation {self.notation!r} must have two disjoint congruent-length base cycles of >=3 vertices.",
                )
        local_set = set(self.local_vertices())
        for local_v in self.vertex_bindings:
            if local_v not in local_set:
                raise TypedFactNextValidationError(
                    "INVALID_VERTEX_BINDING",
                    f"Solid {self.solid_id!r} binds vertex {local_v!r} not present in {self.notation!r}.",
                )
        return self

    def apex_and_base(self) -> tuple[str, tuple[str, ...]]:
        m = _PYRAMID_NOTATION_RE.match(self.notation)
        if not m:
            raise TypedFactNextValidationError(
                "INVALID_SOLID_NOTATION",
                f"Invalid pyramid notation {self.notation!r}.",
            )
        apex = m.group("apex")
        base = split_vertex_chain(m.group("base"))
        return apex, base

    def prism_bases(self) -> tuple[tuple[str, ...], tuple[str, ...]]:
        m = _PRISM_NOTATION_RE.match(self.notation)
        if not m:
            raise TypedFactNextValidationError(
                "INVALID_SOLID_NOTATION",
                f"Invalid prism notation {self.notation!r}.",
            )
        return split_vertex_chain(m.group("b1")), split_vertex_chain(m.group("b2"))

    def local_vertices(self) -> tuple[str, ...]:
        if self.solid_type == "pyramid":
            apex, base = self.apex_and_base()
            return (apex, *base)
        if self.solid_type not in ("pyramid", "prism"):
            return tuple(v for v in (self.center, self.apex_or_top, self.rim_point) if v is not None)
        b1, b2 = self.prism_bases()
        return (*b1, *b2)

    def canonical_vertex(self, local_label: str) -> str:
        return self.vertex_bindings.get(local_label, local_label)


#: Argument shape of every premise kind a route compiles (run `hybrid-contract-v2`, P1): "ref" = one vertex reference,
#: "refs<n>" = a list of at least / exactly n references ("refs2=" exact), "value" = an exact number written as text or
#: integer, "id" = a solid id; a trailing "?" marks an optional argument. A premise with a known kind and a wrong shape is
#: an INPUT error refused here, before any route compiles it. Unknown kinds stay the routes' own capability refusal.
_ARGS_LOI = {
    "regular_pyramid": {"apex": "ref", "base": "refs3"},
    "right_prism": {"base": "refs3", "top": "refs3"},
    "regular_polygon": {"vertices": "refs3", "side": "value?"},
    "rectangle": {"vertices": "refs4="},
    "segment_length": {"segment": "refs2=", "value": "value"},
    "height": {"value": "value", "solid": "id?"},
    "equal_length": {"segment_a": "refs2=", "segment_b": "refs2="},
    "perpendicular_line_plane": {"line": "refs2=", "plane": "refs3"},
    "perpendicular_lines": {"line1": "refs2=", "line2": "refs2="},
    "face_perpendicular_base": {"face": "refs3", "base": "refs3"},
    "altitude": {"apex": "ref", "foot": "ref", "solid": "id?"},
    "midpoint": {"point": "ref", "segment": "refs2="},
    "divide_segment": {"point": "ref", "segment": "refs2=", "ratio": "value"},
    "centroid": {"point": "ref", "polygon": "refs3"},
    "orthogonal_projection": {"point": "ref", "image": "ref", "plane": "refs3"},
    "orthogonal_projection_line": {"point": "ref", "image": "ref", "line": "refs2="},
    "intersect_line_line": {"point": "ref", "line1": "refs2=", "line2": "refs2="},
    "intersect_line_plane": {"point": "ref", "line": "refs2=", "plane": "refs3"},
}
for _alias, _goc in (("base_is_square", "regular_polygon"), ("base_is_equilateral_triangle", "regular_polygon"),
                     ("base_is_regular_polygon", "regular_polygon"), ("base_is_rectangle", "rectangle"),
                     ("equal_segments", "equal_length"), ("line_perp_plane", "perpendicular_line_plane"),
                     ("line_perp_line", "perpendicular_lines"), ("plane_perp_base", "face_perpendicular_base"),
                     ("point_is_midpoint", "midpoint"), ("point_divides_segment", "divide_segment"),
                     ("point_is_centroid", "centroid"), ("point_is_foot", "orthogonal_projection")):
    _ARGS_LOI[_alias] = _ARGS_LOI[_goc]
#: Right angle: two closed alternatives, by which keys are present.
_ARGS_GOC_VUONG = ({"vertices": "refs3=", "right_at": "ref"}, {"vertex": "ref", "rays": "refs2="})


def _hinh_dung(value: Any, shape: str) -> bool:
    if shape == "ref":
        return isinstance(value, str) and _QUALIFIED_REF_RE.match(value.strip()) is not None
    if shape.startswith("refs"):
        n, exact = int(shape[4:].rstrip("=")), shape.endswith("=")
        return (isinstance(value, (list, tuple)) and all(_hinh_dung(x, "ref") for x in value)
                and (len(value) == n if exact else len(value) >= n))
    if shape == "value":
        return isinstance(value, int) and not isinstance(value, bool) or isinstance(value, str) and bool(value.strip())
    return isinstance(value, str) and re.fullmatch(r"[A-Za-z0-9_.:-]+", value) is not None      # "id"


def _kiem_args(kind: str, args: dict[str, Any]) -> None:
    mau = (_ARGS_LOI.get(kind),) if kind not in ("right_angle", "base_is_right_triangle") else _ARGS_GOC_VUONG
    if mau == (None,):
        return
    for m in mau:
        if set(args) <= set(m) and all(
                _hinh_dung(args[k], s.rstrip("?")) if k in args and (args[k] is not None or not s.endswith("?"))
                else s.endswith("?") for k, s in m.items()):
            return
    raise TypedFactNextValidationError(
        "INVALID_PREMISE_ARGS", f"Premise {kind!r} needs args {[dict(m) for m in mau]}, got {sorted(args)}.")


class PremiseSpec(ClosedNextModel):
    """Grounded geometric premise supporting solid-qualified references."""

    kind: NonEmptyText
    args: dict[str, Any] = Field(default_factory=dict)
    quote: NonEmptyText
    solid_id: IdentifierStr | None = None

    @model_validator(mode="after")
    def _validate_args(self) -> "PremiseSpec":
        _kiem_args(self.kind, self.args)
        return self


class _PlaneSectionBase(ClosedNextModel):
    """The cutting plane of a section (shared by `/1` and `/2`): which plane, through what, in which solid."""

    section_id: IdentifierStr
    plane_name: NonEmptyText = "α"
    target_solid_id: IdentifierStr
    plane_kind: Literal[
        "through_point_parallel_plane",
        "through_point_perpendicular_line",
        "through_point_parallel_two_lines",
        "parallel_to_base_at_distance",
        "parallel_to_base_at_ratio",
        "plane_equation",
        "axial_section",
    ]
    through_point: NonEmptyText | None = None
    distance_from_base: NonEmptyText | None = None
    ratio_from_apex: NonEmptyText | None = None
    equation_coeffs: tuple[NonEmptyText, NonEmptyText, NonEmptyText, NonEmptyText] | None = None
    section_shape: Literal["polygon", "circle", "ellipse"] | None = None
    parallel_plane: tuple[NonEmptyText, NonEmptyText, NonEmptyText] | None = None
    perpendicular_line: tuple[NonEmptyText, NonEmptyText] | None = None
    parallel_line_a: tuple[NonEmptyText, NonEmptyText] | None = None
    parallel_line_b: tuple[NonEmptyText, NonEmptyText] | None = None
    quote: NonEmptyText

    @model_validator(mode="after")
    def _validate_plane_definition(self) -> "_PlaneSectionBase":
        if self.plane_kind in (
            "through_point_parallel_plane",
            "through_point_perpendicular_line",
            "through_point_parallel_two_lines",
        ):
            if not self.through_point:
                raise TypedFactNextValidationError(
                    "INVALID_DERIVED_SECTION",
                    f"Section {self.section_id!r} ({self.plane_kind}) requires 'through_point'.",
                )
            parse_qualified_ref(self.through_point)
        elif self.plane_kind == "parallel_to_base_at_distance":
            if not self.distance_from_base:
                raise TypedFactNextValidationError(
                    "INVALID_DERIVED_SECTION",
                    f"Section {self.section_id!r} requires 'distance_from_base'.",
                )
        elif self.plane_kind == "parallel_to_base_at_ratio":
            if not self.ratio_from_apex:
                raise TypedFactNextValidationError(
                    "INVALID_DERIVED_SECTION",
                    f"Section {self.section_id!r} requires 'ratio_from_apex'.",
                )
        elif self.plane_kind == "plane_equation":
            if self.equation_coeffs is None or len(self.equation_coeffs) != 4:
                raise TypedFactNextValidationError(
                    "INVALID_DERIVED_SECTION",
                    f"Section {self.section_id!r} requires 4-element 'equation_coeffs'.",
                )
        if self.plane_kind == "through_point_parallel_plane":
            if self.parallel_plane is None or len(self.parallel_plane) != 3:
                raise TypedFactNextValidationError(
                    "INVALID_DERIVED_SECTION",
                    f"Section {self.section_id!r} requires a 3-point 'parallel_plane'.",
                )
            for p in self.parallel_plane:
                parse_qualified_ref(p)
        elif self.plane_kind == "through_point_perpendicular_line":
            if self.perpendicular_line is None or len(self.perpendicular_line) != 2:
                raise TypedFactNextValidationError(
                    "INVALID_DERIVED_SECTION",
                    f"Section {self.section_id!r} requires a 2-point 'perpendicular_line'.",
                )
            for p in self.perpendicular_line:
                parse_qualified_ref(p)
        elif self.plane_kind == "through_point_parallel_two_lines":
            if (
                self.parallel_line_a is None
                or self.parallel_line_b is None
                or len(self.parallel_line_a) != 2
                or len(self.parallel_line_b) != 2
            ):
                raise TypedFactNextValidationError(
                    "INVALID_DERIVED_SECTION",
                    f"Section {self.section_id!r} requires 2-point 'parallel_line_a' and 'parallel_line_b'.",
                )
            for p in (*self.parallel_line_a, *self.parallel_line_b):
                parse_qualified_ref(p)
        return self


class DerivedPlaneSectionSpec(_PlaneSectionBase):
    """`/1` section: `cut_edges` keeps the reading of the route that receives it (bridge: the edges the source STATES are
    cut; Adapter /3: the complete boundary) — never reinterpreted; `/2` separates the two."""

    cut_edges: tuple[tuple[NonEmptyText, NonEmptyText], ...] = ()
    named_intersections: dict[str, Label] = Field(default_factory=dict)

    @model_validator(mode="after")
    def _validate_cuts(self) -> "DerivedPlaneSectionSpec":
        for u, v in self.cut_edges:
            parse_qualified_ref(u)
            parse_qualified_ref(v)
        for key in self.named_intersections:                 # one edge "U-V" of two references, nothing else (S5)
            try:
                split_edge_key(key)
            except TypedFactNextValidationError:
                raise TypedFactNextValidationError(
                    "INVALID_DERIVED_SECTION", f"Section {self.section_id!r}: named intersection key {key!r} is not 'U-V'.") from None
        return self


class StatedIntersectionSpec(ClosedNextModel):
    """`/2` (1)+(4): ONE intersection the source states — the edge it says is cut, the name it gives the point (None: the
    source states the cut but names no point), and the quote that states it (inside the section's quote)."""

    edge: tuple[NonEmptyText, NonEmptyText]
    point: Label | None = None
    quote: NonEmptyText

    @model_validator(mode="after")
    def _validate_edge(self) -> "StatedIntersectionSpec":
        a, b = (parse_qualified_ref(x) for x in self.edge)
        if a == b:
            raise TypedFactNextValidationError("INVALID_DERIVED_SECTION", f"Stated intersection on a degenerate edge {self.edge}.")
        return self


class DerivedPlaneSectionSpecV2(_PlaneSectionBase):
    """`typed-fact-next/2` section (run `hybrid-contract-v2`): inputs say only what the source says. The section boundary,
    its derived vertices and its closure certificate are ENGINE outputs. `declared_boundary` is an author's claim (cyclic
    order of edges) that is always verified, never trusted. There is no input flag that waives the closure proof: whether
    a closed boundary is required follows from the goals (a derived solid needs it)."""

    stated_intersections: tuple[StatedIntersectionSpec, ...] = ()
    declared_boundary: tuple[tuple[NonEmptyText, NonEmptyText], ...] | None = None

    @model_validator(mode="after")
    def _validate_statements(self) -> "DerivedPlaneSectionSpecV2":
        def bad(detail: str) -> TypedFactNextValidationError:
            return TypedFactNextValidationError("INVALID_DERIVED_SECTION", f"Section {self.section_id!r}: {detail}")

        canh = [frozenset(parse_qualified_ref(x) for x in s.edge) for s in self.stated_intersections]
        if len(set(canh)) != len(canh):
            raise bad("an edge is stated twice")
        ten = [s.point for s in self.stated_intersections if s.point]
        if len(set(ten)) != len(ten):
            raise bad("two stated intersections carry the same name")
        if any(s.quote not in self.quote for s in self.stated_intersections):
            raise bad("a stated intersection's quote is not inside the section's quote")
        if self.declared_boundary is not None:
            vong = [frozenset(parse_qualified_ref(x) for x in e) for e in self.declared_boundary]
            if len(vong) < 3 or len(set(vong)) != len(vong) or any(len(e) != 2 for e in vong):
                raise bad("a declared boundary is a cycle of at least 3 distinct edges")
        return self


class GeometricRelationSpec(ClosedNextModel):
    """Explicit structural or multi-solid geometric relation."""

    relation_id: IdentifierStr
    kind: Literal[
        "containment",
        "shared_vertices",
        "shared_faces",
        "parallel",
        "perpendicular",
        "section_membership",
        "coordinate_frame",
    ]
    quote: NonEmptyText
    container_ref: NonEmptyText | None = None
    member_ref: NonEmptyText | None = None
    pairs: tuple[tuple[NonEmptyText, NonEmptyText], ...] = ()
    solid_a: IdentifierStr | None = None
    face_a: tuple[NonEmptyText, ...] = ()
    solid_b: IdentifierStr | None = None
    face_b: tuple[NonEmptyText, ...] = ()
    entity_a: tuple[NonEmptyText, ...] = ()
    entity_b: tuple[NonEmptyText, ...] = ()
    solid_id: IdentifierStr | None = None
    section_id: IdentifierStr | None = None
    member_refs: tuple[NonEmptyText, ...] = ()
    frame_id: IdentifierStr | None = None
    anchor_refs: tuple[NonEmptyText, ...] = ()

    @model_validator(mode="after")
    def _validate_relation_fields(self) -> "GeometricRelationSpec":
        if self.kind == "containment":
            if not self.container_ref or not self.member_ref:
                raise TypedFactNextValidationError(
                    "INVALID_RELATION_SPEC",
                    f"Relation {self.relation_id!r} ('containment') requires 'container_ref' and 'member_ref'.",
                )
        elif self.kind == "shared_vertices":
            if not self.pairs:
                raise TypedFactNextValidationError(
                    "INVALID_RELATION_SPEC",
                    f"Relation {self.relation_id!r} ('shared_vertices') requires non-empty 'pairs'.",
                )
            for a, b in self.pairs:
                sa, _ = parse_qualified_ref(a)
                sb, _ = parse_qualified_ref(b)
                if not sa or not sb:
                    raise TypedFactNextValidationError(
                        "INVALID_RELATION_SPEC",
                        f"Relation {self.relation_id!r} ('shared_vertices') requires solid-qualified refs ('solid_id::V').",
                    )
        elif self.kind == "shared_faces":
            if (
                not self.solid_a
                or not self.solid_b
                or len(self.face_a) < 3
                or len(self.face_a) != len(self.face_b)
            ):
                raise TypedFactNextValidationError(
                    "INVALID_RELATION_SPEC",
                    f"Relation {self.relation_id!r} ('shared_faces') requires 'solid_a', 'solid_b', and matching >=3-vertex 'face_a'/'face_b'.",
                )
        elif self.kind in ("parallel", "perpendicular"):
            if len(self.entity_a) < 2 or len(self.entity_b) < 2:
                raise TypedFactNextValidationError(
                    "INVALID_RELATION_SPEC",
                    f"Relation {self.relation_id!r} ({self.kind!r}) requires >=2-point 'entity_a' and 'entity_b'.",
                )
        elif self.kind == "section_membership":
            if not self.section_id or not self.member_refs:
                raise TypedFactNextValidationError(
                    "INVALID_RELATION_SPEC",
                    f"Relation {self.relation_id!r} ('section_membership') requires 'section_id' and 'member_refs'.",
                )
        elif self.kind == "coordinate_frame":
            if not self.solid_id or not self.frame_id:
                raise TypedFactNextValidationError(
                    "INVALID_RELATION_SPEC",
                    f"Relation {self.relation_id!r} ('coordinate_frame') requires 'solid_id' and 'frame_id'.",
                )
        return self


class SimulationGoalSpec(ClosedNextModel):
    """Primary simulation goal driving Scene3D construction, highlighting, and step sequencing."""

    goal_id: IdentifierStr
    kind: Literal[
        "construct_object",
        "construct_plane_section",
        "construct_derived_solid",
        "highlight_geometry",
        "construction_sequence",
    ]
    quote: NonEmptyText
    target_solid_id: IdentifierStr | None = None
    target_section_id: IdentifierStr | None = None
    derived_solid_id: IdentifierStr | None = None
    parent_solid_id: IdentifierStr | None = None
    apex_ref: NonEmptyText | None = None
    target_refs: tuple[NonEmptyText, ...] = ()
    style_role: Literal[
        "primary",
        "section",
        "derived_solid",
        "shared_geometry",
        "auxiliary",
    ] = "primary"

    @model_validator(mode="after")
    def _validate_simulation_goal(self) -> "SimulationGoalSpec":
        if self.kind == "construct_object" and not self.target_solid_id:
            raise TypedFactNextValidationError(
                "INVALID_SIMULATION_GOAL",
                f"Simulation goal {self.goal_id!r} ('construct_object') requires 'target_solid_id'.",
            )
        if self.kind == "construct_plane_section" and not self.target_section_id:
            raise TypedFactNextValidationError(
                "INVALID_SIMULATION_GOAL",
                f"Simulation goal {self.goal_id!r} ('construct_plane_section') requires 'target_section_id'.",
            )
        if self.kind == "construct_derived_solid":
            if not self.derived_solid_id or not self.target_section_id or not self.apex_ref:
                raise TypedFactNextValidationError(
                    "INVALID_SIMULATION_GOAL",
                    f"Simulation goal {self.goal_id!r} ('construct_derived_solid') requires 'derived_solid_id', 'target_section_id', and 'apex_ref'.",
                )
        if self.kind == "highlight_geometry" and not self.target_refs:
            raise TypedFactNextValidationError(
                "INVALID_SIMULATION_GOAL",
                f"Simulation goal {self.goal_id!r} ('highlight_geometry') requires non-empty 'target_refs'.",
            )
        return self


class MathGoalSpec(ClosedNextModel):
    """Optional certified auxiliary mathematical goal."""

    goal_id: IdentifierStr
    kind: Literal["volume_ratio", "residual_volume", "measurement"]
    quote: NonEmptyText
    numerator_solid_id: IdentifierStr | None = None
    denominator_solid_id: IdentifierStr | None = None
    parent_solid_id: IdentifierStr | None = None
    cut_solid_id: IdentifierStr | None = None
    goal_type: MathGoalType | None = None
    target: dict[str, Any] = Field(default_factory=dict)
    solid_id: IdentifierStr | None = None

    @model_validator(mode="after")
    def _validate_math_goal(self) -> "MathGoalSpec":
        if self.kind == "volume_ratio":
            if not self.numerator_solid_id or not self.denominator_solid_id:
                raise TypedFactNextValidationError(
                    "INVALID_MATH_GOAL",
                    f"Math goal {self.goal_id!r} ('volume_ratio') requires 'numerator_solid_id' and 'denominator_solid_id'.",
                )
        elif self.kind == "residual_volume":
            if not self.parent_solid_id or not self.cut_solid_id:
                raise TypedFactNextValidationError(
                    "INVALID_MATH_GOAL",
                    f"Math goal {self.goal_id!r} ('residual_volume') requires 'parent_solid_id' and 'cut_solid_id'.",
                )
        elif self.kind == "measurement":
            if not self.goal_type or not self.target:
                raise TypedFactNextValidationError(
                    "INVALID_MATH_GOAL",
                    f"Math goal {self.goal_id!r} ('measurement') requires 'goal_type' and 'target'.",
                )
            _validate_goal_target(self)
        return self


class DerivedObjectIdentity(ClosedNextModel):
    """Deterministic identity record for an automatically derived geometric object."""

    derived_id: NonEmptyText
    kind: Literal["plane", "section_vertex", "section_polygon", "section_circle", "section_ellipse", "derived_solid"]
    internal_symbol: NonEmptyText
    display_label: NonEmptyText
    reference_text: NonEmptyText
    notation: str | None = None
    anonymous_in_source: bool = True
    dependencies: tuple[str, ...] = ()
    provenance: dict[str, Any] = Field(default_factory=dict)


class TypedFactNextPayload(ClosedNextModel):
    """Top-level `typed-fact-next/1` simulation-first contract payload."""

    _VERSION: ClassVar[str] = TYPED_FACT_NEXT_SCHEMA_VERSION
    schema_version: str
    problem_text: NonEmptyText
    length_unit: Literal["1", "a"] | None = None
    solids: tuple[SolidSpec, ...] = ()
    premises: tuple[PremiseSpec, ...] = ()
    derived_sections: tuple[DerivedPlaneSectionSpec, ...] = ()
    relations: tuple[GeometricRelationSpec, ...] = ()
    simulation_goals: tuple[SimulationGoalSpec, ...] = ()
    math_goals: tuple[MathGoalSpec, ...] = ()

    @model_validator(mode="after")
    def _validate_payload(self) -> "TypedFactNextPayload":
        if self.schema_version != self._VERSION:
            raise TypedFactNextValidationError(
                "SCHEMA_VERSION_MISMATCH",
                f"Expected schema_version={self._VERSION!r}, got {self.schema_version!r}.",
            )
        if not self.solids:
            raise TypedFactNextValidationError(
                "EMPTY_SOLIDS",
                "TypedFactNextPayload requires at least one declared solid.",
            )
        if not self.simulation_goals:
            raise TypedFactNextValidationError(
                "EMPTY_SIMULATION_GOALS",
                "TypedFactNextPayload is simulation-first and requires at least one simulation_goal.",
            )
        solid_ids: set[str] = set()
        for solid in self.solids:
            if solid.solid_id in solid_ids:
                raise TypedFactNextValidationError(
                    "DUPLICATE_SOLID_ID",
                    f"Duplicate solid_id {solid.solid_id!r}.",
                )
            solid_ids.add(solid.solid_id)

        section_ids: set[str] = set()
        for sec in self.derived_sections:
            if sec.section_id in section_ids:
                raise TypedFactNextValidationError(
                    "DUPLICATE_SECTION_ID",
                    f"Duplicate section_id {sec.section_id!r}.",
                )
            if sec.target_solid_id not in solid_ids:
                raise TypedFactNextValidationError(
                    "UNKNOWN_SOLID_ID",
                    f"Derived section {sec.section_id!r} references unknown solid {sec.target_solid_id!r}.",
                )
            section_ids.add(sec.section_id)

        sim_goal_ids: set[str] = set()
        derived_solid_ids: set[str] = set()
        for g in self.simulation_goals:
            if g.goal_id in sim_goal_ids:
                raise TypedFactNextValidationError(
                    "DUPLICATE_GOAL_ID",
                    f"Duplicate simulation goal_id {g.goal_id!r}.",
                )
            sim_goal_ids.add(g.goal_id)
            if g.kind == "construct_derived_solid" and g.derived_solid_id:
                if g.derived_solid_id in solid_ids or g.derived_solid_id in derived_solid_ids:
                    raise TypedFactNextValidationError(
                        "DUPLICATE_SOLID_ID",
                        f"Derived solid ID {g.derived_solid_id!r} collides with an existing solid ID.",
                    )
                derived_solid_ids.add(g.derived_solid_id)

        all_solid_ids = solid_ids | derived_solid_ids
        for g in self.simulation_goals:
            if g.target_solid_id and g.target_solid_id not in all_solid_ids:
                raise TypedFactNextValidationError(
                    "UNKNOWN_SOLID_ID",
                    f"Simulation goal {g.goal_id!r} references unknown solid {g.target_solid_id!r}.",
                )
            if g.target_section_id and g.target_section_id not in section_ids:
                raise TypedFactNextValidationError(
                    "UNKNOWN_SECTION_ID",
                    f"Simulation goal {g.goal_id!r} references unknown section {g.target_section_id!r}.",
                )

        math_goal_ids: set[str] = set()
        for mg in self.math_goals:
            if mg.goal_id in math_goal_ids or mg.goal_id in sim_goal_ids:
                raise TypedFactNextValidationError(
                    "DUPLICATE_GOAL_ID",
                    f"Duplicate math goal_id {mg.goal_id!r}.",
                )
            math_goal_ids.add(mg.goal_id)
            if mg.numerator_solid_id and mg.numerator_solid_id not in all_solid_ids:
                raise TypedFactNextValidationError(
                    "UNKNOWN_SOLID_ID",
                    f"Math goal {mg.goal_id!r} references unknown numerator solid {mg.numerator_solid_id!r}.",
                )
            if mg.denominator_solid_id and mg.denominator_solid_id not in all_solid_ids:
                raise TypedFactNextValidationError(
                    "UNKNOWN_SOLID_ID",
                    f"Math goal {mg.goal_id!r} references unknown denominator solid {mg.denominator_solid_id!r}.",
                )
            if mg.parent_solid_id and mg.parent_solid_id not in all_solid_ids:
                raise TypedFactNextValidationError(
                    "UNKNOWN_SOLID_ID",
                    f"Math goal {mg.goal_id!r} references unknown parent solid {mg.parent_solid_id!r}.",
                )
            if mg.cut_solid_id and mg.cut_solid_id not in all_solid_ids:
                raise TypedFactNextValidationError(
                    "UNKNOWN_SOLID_ID",
                    f"Math goal {mg.goal_id!r} references unknown cut solid {mg.cut_solid_id!r}.",
                )
        _validate_declared_solid_scope(self, all_solid_ids)
        _validate_goal_identities(self)
        return self


def _solid_aliases(solid: SolidSpec) -> set[str]:
    """Names a solid answers to: its id, its notation and its notation with vertex bindings applied (Adapter /3's name)."""
    names = {solid.solid_id, solid.notation}
    if solid.solid_type == "pyramid":
        apex, base = solid.apex_and_base()
        names.add(f"{solid.canonical_vertex(apex)}.{''.join(map(solid.canonical_vertex, base))}")
    elif solid.solid_type == "prism":
        b1, b2 = solid.prism_bases()
        names.add(f"{''.join(map(solid.canonical_vertex, b1))}.{''.join(map(solid.canonical_vertex, b2))}")
    return names


#: Operand keys of a measurement goal `target` (S11). `plane1`/`plane2` are contract-level: no route reads them yet.
GOAL_OPERAND_KEYS = ("segment", "point", "plane", "line", "line1", "line2", "polygon", "plane1", "plane2")
#: The argument naming the point a premise constructs; that point inherits its producer's solid.
CONSTRUCTED_OUTPUTS = {"midpoint": "point", "point_is_midpoint": "point", "divide_segment": "point",
                       "point_divides_segment": "point", "centroid": "point", "point_is_centroid": "point",
                       "intersect_line_line": "point", "intersect_line_plane": "point",
                       "orthogonal_projection": "image", "point_is_foot": "image", "orthogonal_projection_line": "image"}


def split_edge_key(key: str) -> tuple[str, str]:
    """An `U-V` edge key → its two references (S5). Labels never contain `-`, solid ids may: the split is the unique `-`
    with a reference on both sides; none or several refuse."""
    text = key.strip()
    cuts = [i for i, ch in enumerate(text) if ch == "-" and _QUALIFIED_REF_RE.match(text[:i].strip())
            and _QUALIFIED_REF_RE.match(text[i + 1:].strip())]
    if len(cuts) != 1:
        raise TypedFactNextValidationError("INVALID_DERIVED_SECTION", f"edge key {key!r} is not 'U-V'")
    return text[:cuts[0]].strip(), text[cuts[0] + 1:].strip()


def _chain_refs(chain: str) -> list[str]:
    """A containment chain `SA` or `solid_id::SA` → one reference per vertex (S5)."""
    sid, sep, labels = chain.rpartition("::")
    return [f"{sid}::{x}" if sep else x for x in split_vertex_chain(labels)]


def resolve_solid_name(p: "TypedFactNextPayload", name: Any) -> str | None:
    """The one solid (primary by id/notation/canonical notation, or declared derived id) a name denotes, else None."""
    if not isinstance(name, str):
        return None
    hits = [s.solid_id for s in p.solids if name in _solid_aliases(s)]
    hits += [g.derived_solid_id for g in p.simulation_goals if g.kind == "construct_derived_solid" and g.derived_solid_id == name]
    return hits[0] if len(hits) == 1 else None


def _derived_parents(p: "TypedFactNextPayload") -> dict[str, str]:
    sections = {s.section_id: s.target_solid_id for s in p.derived_sections}
    return {g.derived_solid_id: g.parent_solid_id or sections.get(g.target_section_id)
            for g in p.simulation_goals if g.kind == "construct_derived_solid" and g.derived_solid_id}


def canonical_vertex_ref(p: "TypedFactNextPayload", ref: str, scope: str | None = None) -> str:
    """Declared root-chart identity only; constructed/derived membership is still proved by S8 before capability."""
    ns, label = parse_qualified_ref(ref)
    solids = {s.solid_id: s for s in p.solids}
    parents = _derived_parents(p)
    ns = parents.get(ns, ns)
    solid = solids.get(ns or parents.get(scope, scope))
    if solid is not None:
        return solid.canonical_vertex(label)
    identities = {s.canonical_vertex(label) for s in p.solids if label in s.local_vertices()}
    if len(identities) > 1:
        raise TypedFactNextValidationError("AMBIGUOUS_REFERENCE", f"tham chiếu {ref!r} có nhiều danh tính")
    return next(iter(identities), label)


def _validate_goal_identities(p: "TypedFactNextPayload") -> None:
    for goal in p.math_goals:
        if goal.kind != "measurement":
            continue
        scope = measurement_scope(p, goal)
        for key, refs in goal.target.items():
            if GOAL_OPERAND_SHAPES[key].startswith("refs"):
                identities = [canonical_vertex_ref(p, ref, scope) for ref in refs]
                if len(set(identities)) != len(identities):
                    raise TypedFactNextValidationError("INVALID_MATH_GOAL", f"{goal.goal_id}: repeated identity in {key!r}")


def constructed_names(p: "TypedFactNextPayload") -> set[str]:
    """Labels the payload itself introduces as constructed points (premise outputs, named section points)."""
    names = {parse_qualified_ref(prem.args[out])[1] for prem in p.premises
             if (out := CONSTRUCTED_OUTPUTS.get(prem.kind)) and isinstance(prem.args.get(out), str)}
    for sec in p.derived_sections:
        names.update(getattr(sec, "named_intersections", {}).values())
        names.update(s.point for s in getattr(sec, "stated_intersections", ()) if s.point)
    return names


def scope_records(p: "TypedFactNextPayload") -> list[tuple[str, str, str | None, list[str], bool]]:
    """Every scoped object of a (validated) payload as `(kind, where, scope, references, strict)` — the ONE enumeration
    the schema (S5/S6/S7) and the Bridge ownership check (S8) iterate. `strict`: every label must be a vertex of the scope."""
    sections = {s.section_id: s for s in p.derived_sections}
    parents = _derived_parents(p)
    recs: list[tuple[str, str, str | None, list[str], bool]] = []
    for i, prem in enumerate(p.premises, 1):
        if prem.kind in ("right_angle", "base_is_right_triangle"):
            shape = next((s for s in _ARGS_GOC_VUONG if set(prem.args) <= set(s)), {})
        else:
            shape = _ARGS_LOI.get(prem.kind, {})
        refs =[r for key, s in shape.items() if s.startswith("ref") and key in prem.args
                for r in (prem.args[key] if s.startswith("refs") else [prem.args[key]]) if isinstance(r, str)]
        recs.append(("premise", f"p{i}", prem.solid_id or resolve_solid_name(p, prem.args.get("solid")), refs, False))
    for sec in p.derived_sections:
        refs = [x for x in (sec.through_point, *(sec.parallel_plane or ()), *(sec.perpendicular_line or ()),
                            *(sec.parallel_line_a or ()), *(sec.parallel_line_b or ())) if x]
        refs += [x for e in getattr(sec, "cut_edges", ()) for x in e]
        refs += [x for k in getattr(sec, "named_intersections", {}) for x in split_edge_key(k)]
        refs += [x for s in getattr(sec, "stated_intersections", ()) for x in s.edge]
        refs += [x for e in (getattr(sec, "declared_boundary", None) or ()) for x in e]
        recs.append(("section", sec.section_id, sec.target_solid_id, refs, False))
    ids = {s.solid_id for s in p.solids} | set(parents) | set(sections)
    for r in p.relations:
        # A containment's container is a vertex chain or a whole solid (then it is the members' scope, not a reference).
        whole = r.container_ref if r.container_ref in ids else None
        single = r.solid_id or (sections[r.section_id].target_solid_id if r.section_id in sections else None) or whole
        recs.append(("relation", r.relation_id, r.solid_a or r.solid_id,
                     [*r.face_a, *r.entity_a, *(a for a, _b in r.pairs)], r.kind == "shared_faces"))
        recs.append(("relation", r.relation_id, r.solid_b or r.solid_id,
                     [*r.face_b, *r.entity_b, *(b for _a, b in r.pairs)], r.kind == "shared_faces"))
        recs.append(("relation", r.relation_id, single,
                     [*(_chain_refs(r.container_ref) if r.container_ref and not whole else ()),
                      *([r.member_ref] if r.member_ref else ()), *r.member_refs, *r.anchor_refs], r.kind == "coordinate_frame"))
    for g in p.simulation_goals:
        section = sections.get(g.target_section_id)
        scope = parents.get(g.derived_solid_id) if g.kind == "construct_derived_solid" else \
            g.target_solid_id or (section.target_solid_id if section else None)
        refs = [x for x in (g.apex_ref, *g.target_refs) if x and x not in ids]
        recs.append(("simulation_goal", g.goal_id, scope, refs, False))
    for mg in p.math_goals:
        if mg.kind != "measurement":
            continue
        t = mg.target
        sec = sections.get(t["section_id"]) if isinstance(t.get("section_id"), str) else None
        scope = measurement_scope(p, mg)
        refs = [x for k in GOAL_OPERAND_KEYS if k in t for x in (t[k] if isinstance(t[k], (list, tuple)) else [t[k]])]
        recs.append(("math_goal", mg.goal_id, scope, refs, False))
    return recs


def _validate_declared_solid_scope(p: "TypedFactNextPayload", known: set[str]) -> None:
    """ONE declared-solid-scope policy (runs `.../unified-solid-scope` and `.../unified-solid-scope-closure`).

    It runs inside the payload model, so every TypedFactNext route (Adapter /3 polyhedral and curved, Adapter /4, the
    planner route) applies it before dispatch, capability refusal or fallback. It decides what declarations prove; rule
    ids S1–S11 are listed in the run's `architecture-amendment.md` and are enforced field by field against the
    mechanical census (`schema-field-inventory.json`). Absent optional scope never fires a rule and is never replaced
    by a default. Ownership through constructed points is the Bridge's (`_kiem_pham_vi_tien_de`, S8)."""
    solids = {s.solid_id: s for s in p.solids}
    sections = {s.section_id: s for s in p.derived_sections}
    parents = _derived_parents(p)
    built = constructed_names(p)
    owners_of: dict[str, set[str]] = {}
    for sid, spec in solids.items():
        for v in {*spec.local_vertices(), *map(spec.canonical_vertex, spec.local_vertices())}:
            owners_of.setdefault(v, set()).add(sid)

    def refuse(code: str, where: str, detail: str):
        raise TypedFactNextValidationError(code, f"{where}: {detail}")

    def declared(sid: Any, where: str) -> str | None:                                   # S1
        if sid is not None and (not isinstance(sid, str) or sid not in known):
            refuse("UNKNOWN_SOLID_ID", where, f"khối {sid!r} chưa được khai báo")
        return sid

    def named(name: Any, scope: str | None, where: str) -> str | None:                  # S2
        if name is None:
            return None
        hits = [s for s, spec in solids.items() if name in _solid_aliases(spec)] or [n for n in known if n == name] \
            if isinstance(name, str) else []
        if len(hits) != 1:
            refuse("UNKNOWN_SOLID_ID" if scope is not None else "UNKNOWN_SOLID", where,
                   f"khối {name!r} không xác định duy nhất")
        return hits[0]

    def one_solid(where: str, *sids: str | None) -> str | None:                         # S3
        found = {s for s in sids if s is not None}
        if len(found) > 1:
            refuse("SOURCE_OBJECT_MISMATCH", where, f"một đối tượng mang các khối khác nhau {sorted(found)}")
        return next(iter(found), None)

    def section_of(sec_id: Any, where: str, code: str = "UNKNOWN_SECTION_ID") -> str | None:   # S9
        if sec_id is None:
            return None
        if not isinstance(sec_id, str):
            refuse("INVALID_MATH_GOAL", where, f"thiết diện {sec_id!r} không phải định danh")      # S11
        if sec_id not in sections:
            refuse(code, where, f"thiết diện {sec_id!r} chưa được khai báo")
        return sections[sec_id].target_solid_id

    def family(scope: str | None) -> set[str]:
        return {scope, parents[scope]} if scope in parents else {scope}

    for i, prem in enumerate(p.premises, 1):
        where = f"p{i}"
        scope = declared(prem.solid_id, where)
        one_solid(where, scope, named(prem.args.get("solid"), scope, where))
    for r in p.relations:
        for sid in (r.solid_id, r.solid_a, r.solid_b):
            declared(sid, r.relation_id)
        if r.solid_id is not None:
            one_solid(r.relation_id, r.solid_id, r.solid_a)
            one_solid(r.relation_id, r.solid_id, r.solid_b)
        if r.section_id is not None:
            one_solid(r.relation_id, r.solid_id, section_of(r.section_id, r.relation_id))
        if r.container_ref in known:                                                       # S3: whole-solid container
            one_solid(r.relation_id, r.solid_id, r.container_ref)
    for g in p.simulation_goals:
        declared(g.parent_solid_id, g.goal_id)
        if g.target_section_id in sections:
            one_solid(g.goal_id, g.parent_solid_id if g.kind == "construct_derived_solid" else g.target_solid_id,
                      sections[g.target_section_id].target_solid_id)
        for token in g.target_refs:                                                        # S3/S9 for id tokens
            if g.target_solid_id is not None and token in known and g.target_solid_id not in family(token):
                refuse("SOURCE_OBJECT_MISMATCH", g.goal_id, f"{token!r} nằm ngoài phạm vi {g.target_solid_id!r}")
            if g.target_solid_id is not None and token in sections and \
                    sections[token].target_solid_id not in family(g.target_solid_id):
                refuse("SOURCE_OBJECT_MISMATCH", g.goal_id, f"thiết diện {token!r} không thuộc {g.target_solid_id!r}")
        for token in [x for x in (g.apex_ref, *g.target_refs) if x and x not in known and x not in sections]:   # S10
            if not _QUALIFIED_REF_RE.match(token) or parse_qualified_ref(token)[1] not in {*owners_of, *built}:
                refuse("UNKNOWN_VERTEX_REF", g.goal_id, f"{token!r} không chỉ tới đối tượng nào đã khai")
    for mg in p.math_goals:
        if mg.kind in ("volume_ratio", "residual_volume"):
            if mg.kind == "residual_volume" and mg.cut_solid_id in parents:              # S3: a derived cut's ancestry
                one_solid(mg.goal_id, mg.parent_solid_id, parents[mg.cut_solid_id])
            continue
        t = mg.target
        for key in GOAL_OPERAND_KEYS:                                                    # S11
            v = t.get(key)
            if v is not None and not (isinstance(v, str) or isinstance(v, (list, tuple)) and all(isinstance(x, str) for x in v)):
                refuse("INVALID_MATH_GOAL", mg.goal_id, f"toán hạng {key!r} không phải tham chiếu")
        scope = declared(mg.solid_id, mg.goal_id)
        nested = declared(t.get("solid_id"), mg.goal_id)
        one_solid(mg.goal_id, scope, nested, named(t.get("solid"), scope or nested, mg.goal_id),
                  section_of(t.get("section_id"), mg.goal_id))

    for _kind, where, scope, refs, strict in scope_records(p):
        for ref in refs:
            ns, label = parse_qualified_ref(ref)                                         # S5 grammar
            if ns is not None:
                declared(ns, where)
                if scope is not None and ns not in family(scope):                         # S5
                    refuse("SOURCE_OBJECT_MISMATCH", where, f"tham chiếu {ref!r} khác phạm vi khối {scope!r}")
            base = parents.get(scope, scope)
            stray = [label] if strict and base in solids and base not in owners_of.get(label, set()) else []
            if stray:                                                                    # S6
                refuse("SOURCE_OBJECT_MISMATCH", where, f"{stray} không phải đỉnh của khối {base!r}")
            if ns is None and base in solids and label in owners_of and base not in owners_of[label] \
                    and label not in built:                                              # S7
                refuse("SOURCE_OBJECT_MISMATCH", where, f"{label!r} chỉ là đỉnh của khối khác, không thuộc {base!r}")


class TypedFactNextPayloadV2(TypedFactNextPayload):
    """`typed-fact-next/2` (run `hybrid-contract-v2`, owner D1): `/1` with the section split into stated intersections
    and an optional declared boundary. Everything else keeps the `/1` shape and cross-reference checks."""

    _VERSION: ClassVar[str] = TYPED_FACT_NEXT_V2_SCHEMA_VERSION
    derived_sections: tuple[DerivedPlaneSectionSpecV2, ...] = ()


def parse_typed_fact_next(raw: dict[str, Any] | TypedFactNextPayload) -> TypedFactNextPayload:
    """Validate and parse a `typed-fact-next/1` payload with fail-closed error reporting. Never reads `/2`."""
    return _parse(TypedFactNextPayload, raw)


def parse_typed_fact_next_v2(raw: dict[str, Any] | TypedFactNextPayloadV2) -> TypedFactNextPayloadV2:
    """Validate and parse a `typed-fact-next/2` payload with fail-closed error reporting. Never reads `/1`."""
    return _parse(TypedFactNextPayloadV2, raw)


def convert_v1_to_v2(raw: dict[str, Any], route: str | None) -> dict[str, Any]:
    """`/1 → /2` ONLY for a payload whose route is declared, because `/1.cut_edges` means different things per route:
    `bridge` — the edges the source states are cut (+ their names); `adapter3` — the complete boundary, so it becomes a
    `declared_boundary` (verified, never trusted) and only NAMED intersections become stated ones (an Adapter /3 payload
    carries no record of which unnamed cuts the text states — re-author them, do not guess). Anything else refuses."""
    if route not in ("bridge", "adapter3"):
        raise TypedFactNextValidationError("ROUTE_LABEL_REQUIRED",
                                           f"`/1` cut_edges has no route-free meaning; route must be 'bridge' or 'adapter3', got {route!r}.")
    p = parse_typed_fact_next(raw)
    out = p.model_dump(mode="json", exclude_none=True, exclude_unset=True)
    out["schema_version"] = TYPED_FACT_NEXT_V2_SCHEMA_VERSION
    for sec, d in zip(p.derived_sections, out["derived_sections"]):
        named = {frozenset(parse_qualified_ref(x) for x in split_edge_key(k)): (list(split_edge_key(k)), v)
                 for k, v in sec.named_intersections.items()}
        if route == "bridge":
            edges = [list(e) for e in sec.cut_edges] or [ends for ends, _v in named.values()]
            stated = [{"edge": e, "point": named.get(frozenset(parse_qualified_ref(x) for x in e), (None, None))[1],
                       "quote": sec.quote} for e in edges]
        else:
            stated = [{"edge": ends, "point": v, "quote": sec.quote} for ends, v in named.values()]
            if sec.cut_edges:
                d["declared_boundary"] = [list(e) for e in sec.cut_edges]
        d.pop("cut_edges", None)
        d.pop("named_intersections", None)
        d["stated_intersections"] = stated
    return out


def _parse(model: type[TypedFactNextPayload], raw: Any) -> TypedFactNextPayload:
    if type(raw) is model:                        # exact type: a `/2` model is never accepted as `/1` (subclass)
        raw = raw.model_dump(exclude_unset=True)
    if not isinstance(raw, dict):
        raise TypedFactNextValidationError(
            "INVALID_TYPED_FACT_NEXT",
            "TypedFactNext payload must be a JSON object.",
        )
    version = raw.get("schema_version")
    if version != model._VERSION:
        raise TypedFactNextValidationError(
            "SCHEMA_VERSION_MISMATCH",
            f"Expected schema_version={model._VERSION!r}, got {version!r}.",
        )
    try:
        return model.model_validate(raw)
    except TypedFactNextValidationError:
        raise
    except Exception as exc:
        errors = getattr(exc, "errors", None)
        if callable(errors):
            for item in errors():
                inner = (item.get("ctx") or {}).get("error")
                if isinstance(inner, TypedFactNextValidationError):
                    raise inner from exc
        raise TypedFactNextValidationError(
            "INVALID_TYPED_FACT_NEXT",
            str(exc),
        ) from exc
