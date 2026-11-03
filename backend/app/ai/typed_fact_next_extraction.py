"""Source-only canonical V2 extraction; transport is injected, never installed here."""
from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
import hashlib
import json
import re
from typing import Any, Callable, Mapping, Protocol

from app.ai.fact_extraction import _TuChoiAI, build_request, parse_response
from app.ai.function_calling import LiveAIDisabled, _openapi
from app.simulation.geometry_functions.registry import _phu_dinh, _vai_tro_tai, _vi_tri, chuan_hoa
from app.simulation.geometry_functions.typed_fact_next import (
    GOAL_OPERAND_SHAPES,
    TYPED_FACT_NEXT_V2_SCHEMA_VERSION,
    TypedFactNextPayloadV2,
    TypedFactNextValidationError,
    _ARGS_GOC_VUONG,
    _ARGS_LOI,
    parse_typed_fact_next_v2,
)


class Extractor(Protocol):
    def extract(self, source_text: str) -> dict[str, Any] | None: ...


@dataclass(frozen=True)
class SourceReference:
    """Every exact half-open code-point occurrence of one extracted quote. Locates text; certifies no premise."""
    path: tuple[str | int, ...]
    spans: tuple[tuple[int, int], ...]


@dataclass(frozen=True)
class ExtractionResult:
    payload: TypedFactNextPayloadV2 | None
    code: str | None
    diagnostics: dict[str, Any]
    source_references: tuple[SourceReference, ...] = ()


class ReplayExtractor:
    def __init__(self, outputs: Mapping[str, dict[str, Any]]) -> None:
        self.outputs = deepcopy(outputs)

    def extract(self, source_text: str) -> dict[str, Any] | None:
        return deepcopy(self.outputs.get(source_text))


TYPED_FACT_NEXT_SYSTEM_INSTRUCTION = (
    "Chỉ trích dữ kiện theo lược đồ typed-fact-next/2; chép nguyên văn từng ký tự của problem_text và mọi quote "
    "(kể cả khi đề có lỗi gõ chữ; không diễn đạt lại, không thêm/bớt khoảng trắng). length_unit là 'a' nếu độ dài chứa "
    "tham số a, ngược lại là '1'. Không tính toán, không chọn phép dựng, không sinh toạ độ hoặc mã. "
    "Không biến mệnh đề phủ định, điều kiện ('nếu … thì') hay điều phải chứng minh thành premise.\n"
    "1. solids: pyramid ghi notation dạng Đỉnh.Đáy (S.ABC, S.ABCD; tứ diện ABCD ghi A.BCD); prism ghi Đáy1.Đáy2 "
    "(ABC.A'B'C', ABCD.A'B'C'D'); khối tròn xoay không đặt tên ghi notation='()'.\n"
    "2. premises (gán solid_id của khối chứa giả thiết): chỉ dùng kind chuẩn và đúng khoá args: "
    "regular_pyramid {apex, base}; right_prism {base, top} (lăng trụ đứng/đều, hình hộp chữ nhật, hình lập phương — "
    "chỉ thêm regular_polygon/rectangle/segment_length cho mặt hoặc cạnh đề thực sự nêu); "
    "regular_polygon {vertices, side?}; rectangle {vertices}; right_angle {vertex, rays} (vertex là đỉnh góc vuông, "
    "rays gồm 2 điểm trên 2 cạnh); segment_length {segment, value}; height {value, solid?}; "
    "equal_length {segment_a, segment_b}; perpendicular_line_plane {line, plane}; perpendicular_lines {line1, line2}; "
    "face_perpendicular_base {face, base}; altitude {apex, foot, solid?} (quote gồm cả tên khối và cụm đường cao nếu "
    "cùng câu); midpoint {point, segment}; divide_segment {point, segment, ratio}; centroid {point, polygon}; "
    "orthogonal_projection {point, image, plane}; orthogonal_projection_line {point, image, line}; "
    "intersect_line_line {point, line1, line2}; intersect_line_plane {point, line, plane}.\n"
    "3. described_points: điểm đề MÔ TẢ mà không đặt tên (midpoint: segment; centroid/orthocenter trực tâm/"
    "circumcenter tâm đường tròn ngoại tiếp tam giác: polygon 3 đỉnh; orthogonal_projection: point, plane; "
    "orthogonal_projection_line: point, line; intersect_line_line: line1, line2; intersect_line_plane: line, plane) ⇒ "
    "khai trong described_points với quote nguyên văn cụm mô tả và ghi '@' + described_id tại toán hạng điểm của "
    "math_goals.target, derived_sections.through_point hoặc described_points khác; không tự đặt tên đỉnh mới, không "
    "thêm điểm phụ đề không nhắc tới.\n"
    "4. derived_sections: plane_name không kèm ngoặc (P, Q, α). Mặt cắt qua 1 điểm (nhãn đỉnh hoặc @described_id) và "
    "song song 1 mặt / vuông góc 1 đường / song song 2 đường ⇒ through_point_parallel_plane (through_point, "
    "parallel_plane 3 nhãn), through_point_perpendicular_line (through_point, perpendicular_line 2 nhãn), hoặc "
    "through_point_parallel_two_lines. Mặt cắt cho bằng tổ hợp quan hệ giữa các nhãn đỉnh (chứa cạnh/điểm, song song "
    "đường, vuông góc mặt) ⇒ plane_kind='constrained', through_point=null, khai đúng các ràng buộc trong constraints "
    "(contains_points 1..4 nhãn, parallel_to_line 2 nhãn, perpendicular_to_plane 3..4 nhãn). stated_intersections chỉ "
    "chứa giao điểm đề nêu.\n"
    "5. simulation_goals & math_goals: lược đồ simulation-first — mọi đề hợp lệ (khi unresolved rỗng) PHẢI có "
    "simulation_goals (mặc định kind='construct_object', target_solid_id trỏ tới khối đã khai, quote nguyên văn mệnh đề "
    "khai khối hoặc câu yêu cầu vẽ/mô phỏng), kể cả khi đề chỉ hỏi tính toán; không bịa math_goals khi đề chỉ yêu cầu "
    "vẽ/mô phỏng. Câu hỏi tính toán ghi vào math_goals: kind='measurement' đặt solid_id ở mức mục tiêu (không đặt "
    "solid_id cạnh toán hạng khác trong target), goal_type thuộc {distance, angle, volume, area, lateral_area, radius} "
    "(độ dài đoạn thẳng dùng goal_type='distance' với target={segment:[A,B]}; thể tích khối dùng target={solid_id:...}; "
    "diện tích thiết diện dùng target={section_id:...}; diện tích đa giác dùng target={polygon:[...]}).\n"
    "6. unresolved: mệnh đề mơ hồ nhiều cách hiểu (ambiguous), thiếu toán hạng/tên đỉnh/kích thước bắt buộc "
    "(missing_operand), thuật ngữ lạ (unrecognized_term), hoặc yêu cầu ngoài phạm vi như toạ độ Oxyz, quỹ tích, cực "
    "trị, tổ hợp chưa hỗ trợ (unsupported) ⇒ ghi vào unresolved với quote nguyên văn mệnh đề gây vướng, missing_roles "
    "và candidate_relations phù hợp (subject_ref chỉ điền khi là đúng một nhãn đỉnh nằm nguyên văn trong quote đó); "
    "nếu chưa khai được khối hợp lệ thì để solids=[] và simulation_goals=[]. Dữ kiện mâu thuẫn số học hoặc mặt phẳng "
    "ràng buộc chưa đủ duy nhất nhưng rõ ngữ pháp hình học thì vẫn trích đầy đủ, không đưa vào unresolved."
)

_CANONICAL_PREMISE_KINDS = (
    "regular_pyramid", "right_prism", "regular_polygon", "rectangle", "right_angle",
    "segment_length", "height", "equal_length", "perpendicular_line_plane", "perpendicular_lines",
    "face_perpendicular_base", "altitude", "midpoint", "divide_segment", "centroid",
    "orthogonal_projection", "orthogonal_projection_line", "intersect_line_line", "intersect_line_plane",
)

_RELATION_EMPTY_ARRAY_DEFAULTS = (
    "pairs", "face_a", "face_b", "entity_a", "entity_b", "member_refs", "anchor_refs",
)


def _shape_openapi_property(shapes: set[str]) -> dict[str, Any]:
    if all(s.startswith("refs") for s in shapes):
        mins = [int(s[4:].rstrip("=")) for s in shapes]
        exact = len(shapes) == 1 and next(iter(shapes)).endswith("=")
        prop: dict[str, Any] = {
            "type": "ARRAY",
            "items": {"type": "STRING", "minLength": 1},
            "minItems": min(mins),
            "nullable": True,
        }
        if exact:
            prop["maxItems"] = min(mins)
        return prop
    return {"type": "STRING", "minLength": 1, "nullable": True}


def _typed_fact_next_v2_response_schema() -> dict[str, Any]:
    raw = TypedFactNextPayloadV2.model_json_schema()
    schema = _openapi({k: v for k, v in raw.items() if k != "$defs"}, raw.get("$defs", {}))
    props = schema["properties"]
    props["schema_version"]["enum"] = [TYPED_FACT_NEXT_V2_SCHEMA_VERSION]
    props["length_unit"]["description"] = (
        "Đơn vị độ dài: 'a' nếu độ dài trong đề chứa tham số a (như a, 2a, a√3), ngược lại ghi '1'."
    )

    solid_item = props["solids"]["items"]
    solid_item["required"] = ["solid_id", "solid_type", "notation", "quote"]
    solid_item["properties"]["vertex_bindings"] = {
        "type": "ARRAY",
        "nullable": True,
        "description": "Ánh xạ đỉnh cục bộ sang đỉnh chuẩn khi nhiều khối dùng chung đỉnh khác tên; để trống nếu cùng tên.",
        "items": {
            "type": "OBJECT",
            "properties": {
                "local": {"type": "STRING", "minLength": 1},
                "canonical": {"type": "STRING", "minLength": 1},
            },
            "required": ["local", "canonical"],
        },
    }

    arg_shapes: dict[str, set[str]] = {}
    for mapping in (*_ARGS_LOI.values(), *_ARGS_GOC_VUONG):
        for key, shape in mapping.items():
            arg_shapes.setdefault(key, set()).add(shape.rstrip("?"))
    premise_item = props["premises"]["items"]
    premise_item["properties"]["kind"]["description"] = (
        "Loại giả thiết chuẩn: " + ", ".join(_CANONICAL_PREMISE_KINDS) + "."
    )
    premise_item["properties"]["args"] = {
        "type": "OBJECT",
        "properties": {k: _shape_openapi_property(arg_shapes[k]) for k in sorted(arg_shapes)},
    }

    sec_item = props["derived_sections"]["items"]
    sec_item["properties"]["plane_name"]["description"] = "Tên mặt phẳng cắt không kèm ngoặc, ví dụ P, Q, α."

    mg_item = props["math_goals"]["items"]
    mg_item["properties"]["target"] = {
        "type": "OBJECT",
        "nullable": True,
        "properties": {k: _shape_openapi_property({sh}) for k, sh in sorted(GOAL_OPERAND_SHAPES.items())},
    }
    return schema


def _strip_none_keys(item: dict[str, Any]) -> dict[str, Any]:
    return {k: v for k, v in item.items() if v is not None}


def _normalize_transport_payload(data: Any) -> Any:
    """Canonicalize Gemini constrained-decoding null/default placeholders into `typed-fact-next/2` input shape."""
    if not isinstance(data, dict) or data.get("schema_version") != TYPED_FACT_NEXT_V2_SCHEMA_VERSION:
        return data
    out = deepcopy(data)
    if "length_unit" in out and out["length_unit"] is None:
        out.pop("length_unit", None)

    for list_key in ("solids", "premises", "derived_sections", "relations", "simulation_goals", "math_goals"):
        if list_key in out and out[list_key] is None:
            out[list_key] = []

    if isinstance(out.get("solids"), list):
        norm_solids = []
        for s in out["solids"]:
            if not isinstance(s, dict):
                norm_solids.append(s)
                continue
            s_clean = _strip_none_keys(s)
            if "vertex_bindings" in s_clean:
                vb = s_clean["vertex_bindings"]
                if isinstance(vb, list):
                    vb_dict: dict[str, str] = {}
                    for pair in vb:
                        if (
                            not isinstance(pair, dict)
                            or not isinstance(pair.get("local"), str)
                            or not isinstance(pair.get("canonical"), str)
                        ):
                            raise TypedFactNextValidationError(
                                "INVALID_TYPED_FACT_NEXT", "vertex_bindings entry must have string local and canonical."
                            )
                        loc, can = pair["local"], pair["canonical"]
                        if loc in vb_dict and vb_dict[loc] != can:
                            raise TypedFactNextValidationError(
                                "INVALID_TYPED_FACT_NEXT", f"Duplicate conflicting vertex binding for {loc!r}."
                            )
                        vb_dict[loc] = can
                    s_clean["vertex_bindings"] = vb_dict
                if s_clean["vertex_bindings"] == {}:
                    s_clean.pop("vertex_bindings", None)
            if s_clean.get("coordinate_frame_id") == "root":
                s_clean.pop("coordinate_frame_id", None)
            norm_solids.append(s_clean)
        out["solids"] = norm_solids

    if isinstance(out.get("premises"), list):
        norm_premises = []
        for p in out["premises"]:
            if not isinstance(p, dict):
                norm_premises.append(p)
                continue
            p_clean = _strip_none_keys(p)
            if isinstance(p_clean.get("args"), dict):
                p_clean["args"] = _strip_none_keys(p_clean["args"])
            norm_premises.append(p_clean)
        out["premises"] = norm_premises

    if isinstance(out.get("derived_sections"), list):
        norm_sections = []
        for sec in out["derived_sections"]:
            if not isinstance(sec, dict):
                norm_sections.append(sec)
                continue
            sec_clean = _strip_none_keys(sec)
            if sec_clean.get("constraints") == [] and sec_clean.get("plane_kind") != "constrained":
                sec_clean.pop("constraints", None)
            if "stated_intersections" not in sec_clean:
                sec_clean["stated_intersections"] = []
            elif isinstance(sec_clean["stated_intersections"], list):
                sec_clean["stated_intersections"] = [
                    _strip_none_keys(si) if isinstance(si, dict) else si
                    for si in sec_clean["stated_intersections"]
                ]
            norm_sections.append(sec_clean)
        out["derived_sections"] = norm_sections

    if isinstance(out.get("relations"), list):
        norm_rels = []
        for rel in out["relations"]:
            if not isinstance(rel, dict):
                norm_rels.append(rel)
                continue
            rel_clean = {
                k: v for k, v in rel.items()
                if v is not None and not (k in _RELATION_EMPTY_ARRAY_DEFAULTS and v == [])
            }
            norm_rels.append(rel_clean)
        out["relations"] = norm_rels

    if isinstance(out.get("simulation_goals"), list):
        norm_sgs = []
        for sg in out["simulation_goals"]:
            if not isinstance(sg, dict):
                norm_sgs.append(sg)
                continue
            sg_clean = _strip_none_keys(sg)
            if sg_clean.get("style_role") == "primary":
                sg_clean.pop("style_role", None)
            if sg_clean.get("target_refs") == []:
                sg_clean.pop("target_refs", None)
            norm_sgs.append(sg_clean)
        out["simulation_goals"] = norm_sgs

    if isinstance(out.get("math_goals"), list):
        norm_mgs = []
        for mg in out["math_goals"]:
            if not isinstance(mg, dict):
                norm_mgs.append(mg)
                continue
            mg_clean = _strip_none_keys(mg)
            if isinstance(mg_clean.get("target"), dict):
                mg_clean["target"] = _strip_none_keys(mg_clean["target"])
                if mg_clean["target"] == {} and mg_clean.get("kind") != "measurement":
                    mg_clean.pop("target", None)
            norm_mgs.append(mg_clean)
        out["math_goals"] = norm_mgs

    if "described_points" in out:
        if not out["described_points"]:
            out.pop("described_points", None)
        elif isinstance(out["described_points"], list):
            out["described_points"] = [
                _strip_none_keys(dp) if isinstance(dp, dict) else dp for dp in out["described_points"]
            ]

    if "unresolved" in out:
        if not out["unresolved"]:
            out.pop("unresolved", None)
        elif isinstance(out["unresolved"], list):
            norm_unres = []
            for u in out["unresolved"]:
                if not isinstance(u, dict):
                    norm_unres.append(u)
                    continue
                u_clean = _strip_none_keys(u)
                u_clean.setdefault("missing_roles", [])
                u_clean.setdefault("candidate_relations", [])
                norm_unres.append(u_clean)
            out["unresolved"] = norm_unres

    return out


def build_typed_fact_next_v2_request(source_text: str) -> dict[str, Any]:
    request = build_request(source_text)
    request["generationConfig"]["responseSchema"] = _typed_fact_next_v2_response_schema()
    request["systemInstruction"]["parts"][0]["text"] = TYPED_FACT_NEXT_SYSTEM_INSTRUCTION
    return request


def typed_fact_next_surface_fingerprint() -> str:
    """SHA-256 fingerprint of the exact `typed-fact-next/2` system instruction, schema and generationConfig."""
    framing = {k: v for k, v in build_typed_fact_next_v2_request("").items() if k != "contents"}
    return hashlib.sha256(json.dumps(framing, ensure_ascii=False, sort_keys=True).encode("utf-8")).hexdigest()


class HybridTransportTimeout(TimeoutError):
    """Raised when the live Hybrid product route exhausts its per-attempt or overall deadline."""


class TransportExtractor:
    """One source-only request using the existing provider framing and response parser."""

    def __init__(self, transport: Callable[[dict[str, Any]], Any]) -> None:
        self.transport = transport

    def extract(self, source_text: str) -> dict[str, Any]:
        request = build_typed_fact_next_v2_request(source_text)
        try:
            body = self.transport(request)
        except LiveAIDisabled:
            raise _TuChoiAI("LIVE_AI_DISABLED", "live AI disabled") from None
        except HybridTransportTimeout:
            raise _TuChoiAI("HYBRID_DEADLINE_EXCEEDED", "transport timed out") from None
        except Exception:
            raise _TuChoiAI("PROVIDER_ERROR", "transport failed") from None
        return _normalize_transport_payload(parse_response(body, {}))


def _occurrences(source_text: str, quote: str) -> tuple[tuple[int, int], ...]:
    spans, start = [], source_text.find(quote)
    while start != -1:                                        # overlapping occurrences count too: none is chosen
        spans.append((start, start + len(quote)))
        start = source_text.find(quote, start + 1)
    return tuple(spans)


def _check_quotes(value: Any, source_text: str, path: tuple[str | int, ...] = (),
                  found: list[SourceReference] | None = None) -> list[SourceReference]:
    """Reject non-verbatim quotes; record raw (pre-normalization) occurrences in `found`."""
    found = [] if found is None else found
    if isinstance(value, dict):
        for key, item in value.items():
            if key == "quote":
                if not isinstance(item, str) or not item or item not in source_text:
                    raise _TuChoiAI("QUOTE_NOT_IN_SOURCE", "quote is not verbatim source")
                found.append(SourceReference((*path, key), _occurrences(source_text, item)))
            _check_quotes(item, source_text, (*path, key), found)
    elif isinstance(value, (list, tuple)):
        for index, item in enumerate(value):
            _check_quotes(item, source_text, (*path, index), found)
    return found


def _check_premise_roles(payload: TypedFactNextPayloadV2, source_text: str) -> None:
    source = chuan_hoa(source_text)
    codes = {"GOAL": "GOAL_CLAUSE_NOT_PREMISE", "CONDITIONAL": "CONDITIONAL_CLAUSE",
             "QUESTION": "QUESTION_CLAUSE_NOT_PREMISE"}
    for premise in payload.premises:
        quote = chuan_hoa(premise.quote)
        start, end = _vi_tri(source, quote)
        # Check inside a broad quote too, so its own "Nếu" / "Chứng minh" cannot hide the role.
        for position in [start, *(start + m.start() for m in re.finditer(r"\S+", source[start:end])), end - 1]:
            if code := codes.get(_vai_tro_tai(source, position)):
                raise _TuChoiAI(code, "premise has a non-premise source role")
        if _phu_dinh(source, start, quote):
            raise _TuChoiAI("NEGATED_CLAUSE", "premise source is negated")


def extract_typed_fact_next_v2(problem_text: str, extractor: Extractor) -> ExtractionResult:
    """Validate source identity, canonical shape and verbatim quotes, without planning geometry.

    Semantic completeness and geometry verification belong to the existing /4 route's Registry gate.
    """
    diagnostics = {"validation": "NOT_VALIDATED", "semantic_gate": "NOT_EXECUTED"}
    try:
        raw = extractor.extract(problem_text)
        if raw is None:
            return ExtractionResult(None, "NO_RECORDED_EXTRACTION", diagnostics)
        if not isinstance(raw, dict) or raw.get("schema_version") != TYPED_FACT_NEXT_V2_SCHEMA_VERSION:
            return ExtractionResult(None, "SCHEMA_VERSION_MISMATCH", diagnostics)
        # Validate before NonEmptyText strips whitespace in the canonical model.
        if raw.get("problem_text") != problem_text:
            return ExtractionResult(None, "REPLAY_SOURCE_IDENTITY_MISMATCH", diagnostics)
        references = tuple(_check_quotes(raw, problem_text))
        payload = parse_typed_fact_next_v2(raw).model_copy(update={"problem_text": problem_text})
        _check_premise_roles(payload, problem_text)
    except (TypedFactNextValidationError, _TuChoiAI) as exc:
        return ExtractionResult(None, exc.code, diagnostics)
    except Exception:
        return ExtractionResult(None, "EXTRACTOR_INTERNAL_ERROR", diagnostics)
    diagnostics["validation"] = "SCHEMA_AND_SOURCE_IDENTITY/QUOTE_VALID"
    return ExtractionResult(payload, None, diagnostics, references)
