"""Source-only canonical V2 extraction; transport is injected, never installed here."""
from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
import hashlib
import json
import re
from typing import Any, Callable, Mapping, Protocol

from app.ai.fact_extraction import _TuChoiAI, build_request, parse_response
from app.ai.function_calling import LiveAIDisabled
from app.simulation.geometry_functions.registry import _phu_dinh, _vai_tro_tai, _vi_tri, chuan_hoa
from app.simulation.geometry_functions.typed_fact_next import (
    CANDIDATE_RELATIONS,
    DESCRIBED_POINT_FIELDS,
    GOAL_OPERAND_SHAPES,
    MISSING_ROLES,
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
    "Chỉ trích dữ kiện theo lược đồ typed-fact-next/2 (schema_version='typed-fact-next/2'); chép nguyên văn từng ký tự "
    "của problem_text và mọi quote từ đề gốc (kể cả khi đề gõ nhầm chính tả; không diễn đạt lại, không tự sửa chữ, "
    "không thêm/bớt khoảng trắng). length_unit là 'a' nếu độ dài trong đề chứa tham số a, ngược lại là '1'. "
    "Không tính toán, không chọn phép dựng, không sinh toạ độ hoặc mã. Không biến mệnh đề phủ định, điều kiện "
    "('nếu … thì') hay mệnh đề yêu cầu chứng minh thành premises.\n"
    "Quy ước chuỗi khoá=giá_trị trên wire: các mảng args, operands, target, params, constraints và vertex_bindings là "
    "mảng chuỗi dạng 'khoá=giá_trị' cho toán hạng đơn (ví dụ 'side=2', 'vertex=A', 'point=@h1', 'section_id=sec1') "
    "hoặc 'khoá=P1,P2,...' phân tách bằng dấu phẩy cho danh sách nhãn điểm (ví dụ 'vertices=A,B,C,D', 'line=S,A', "
    "'segment=S,@o1'); bỏ qua các trường tuỳ chọn không dùng (không điền chuỗi rỗng).\n"
    "1. solids: solid_type thuộc {pyramid, prism, cylinder, cone, sphere, cone_frustum}. pyramid ghi notation dạng "
    "Đỉnh.Đáy (S.ABC, S.ABCD; tứ diện ABCD ghi A.BCD); prism ghi Đáy1.Đáy2 (ABC.A'B'C', ABCD.A'B'C'D'); khối tròn xoay "
    "không đặt tên ghi notation='()' (tham số center, apex_or_top, rim_point, radius, height, circumscribes, inscribed_in "
    "ghi vào solids.params dạng 'radius=2', 'circumscribes=s1'; vertex_bindings chỉ dùng khi nhiều khối khác tên đỉnh "
    "chung dạng 'local=canonical').\n"
    "2. premises (gán solid_id của khối chứa giả thiết; mọi quote trong premises PHẢI chứa cả từ khoá vị từ hình học lẫn "
    "tên các đỉnh/khối liên quan): chỉ dùng kind chuẩn và đúng khoá trong args: "
    "regular_pyramid ['apex=S','base=A,B,C,...']; "
    "right_prism ['base=A,B,C','top=A\\',B\\',C\\''] (dùng cho lăng trụ đứng/đều, hình hộp chữ nhật, hình lập phương — "
    "chỉ thêm regular_polygon/rectangle/segment_length cho mặt hoặc cạnh đề thực sự nêu); "
    "regular_polygon ['vertices=A,B,C,...', tuỳ chọn 'side=2'] (dùng cho tam giác đều, hình vuông, lục giác đều — ví dụ "
    "quote='đáy ABCD là hình vuông cạnh 2'; hình vuông KHÔNG BAO GIỜ khai rectangle; cạnh của nó ghi vào side của chính "
    "premise này, KHÔNG tách thành segment_length 'cạnh 2'); "
    "rectangle ['vertices=A,B,C,D'] (chỉ khi đề nêu hình chữ nhật); "
    "right_angle ['vertex=A','rays=B,C'] (vertex là đỉnh góc vuông, rays là 2 điểm trên 2 cạnh góc vuông); "
    "segment_length ['segment=S,A','value=2'] (dùng cho mọi độ dài cạnh/đoạn có tên 2 mút như SA=2, AA'=5, MM'=5 — không ghi "
    "thành height); "
    "height ['value=2', tuỳ chọn 'solid=s1'] (chỉ khi đề nêu chữ chiều cao/đường cao bằng số mà không ghi theo đoạn 2 mút); "
    "equal_length ['segment_a=S,A','segment_b=S,B']; "
    "perpendicular_line_plane ['line=S,A','plane=A,B,C,...'] (dùng cho 'SA vuông góc (ABCD)'); "
    "perpendicular_lines ['line1=S,A','line2=B,C']; "
    "face_perpendicular_base ['face=S,A,B','base=A,B,C,...']; "
    "altitude ['apex=S','foot=H', tuỳ chọn 'solid=s1'] (chỉ dùng khi đề nêu chữ 'đường cao'/'chiều cao' gắn với chân H, "
    "quote PHẢI bao gồm cả tên khối lẫn cụm đường cao; KHÔNG tự suy altitude từ câu 'SA vuông góc với (ABCD)'); "
    "midpoint ['point=M','segment=A,B']; divide_segment ['point=M','segment=A,B','ratio=2'] (đúng hướng tỉ số); "
    "centroid ['point=G','polygon=A,B,C']; "
    "orthogonal_projection ['point=A','image=H','plane=S,B,C']; "
    "orthogonal_projection_line ['point=A','image=H','line=S,B']; "
    "intersect_line_line ['point=O','line1=A,C','line2=B,D']; "
    "intersect_line_plane ['point=I','line=S,M','plane=A,B,C'].\n"
    "3. described_points: CHỈ dùng cho điểm đề MÔ TẢ mà KHÔNG đặt tên chữ cái (ví dụ 'trung điểm của SC', 'hình chiếu "
    "vuông góc của B lên mặt phẳng (SAC)', 'giao điểm của AC và BD', 'trực tâm của tam giác SBC', 'tâm đường tròn ngoại "
    "tiếp tam giác ABC'); TUYỆT ĐỐI KHÔNG đưa điểm đã được đặt tên (như 'Gọi M là trung điểm của AB', 'H là hình chiếu...') "
    "vào described_points — điểm có tên bắt buộc khai ở premises và tham chiếu trực tiếp bằng nhãn chữ cái (M, H). "
    "Điểm không tên khai trong described_points với quote nguyên văn cụm mô tả, kind thuộc {midpoint, centroid, orthocenter, "
    "circumcenter, orthogonal_projection, orthogonal_projection_line, intersect_line_line, intersect_line_plane} và "
    "operands tương ứng (midpoint: ['segment=S,C']; centroid/orthocenter/circumcenter: ['polygon=S,B,C'] 3 đỉnh tam "
    "giác; orthogonal_projection: ['point=B','plane=S,A,C']; orthogonal_projection_line: ['point=A','line=S,B']; "
    "intersect_line_line: ['line1=A,C','line2=B,D']; intersect_line_plane: ['line=S,M','plane=A,B,C']). Tại chỗ dùng "
    "điểm không tên đó (math_goals.target, derived_sections.through_point, hoặc toán hạng điểm của described_points khác) "
    "thì ghi '@' + described_id (ví dụ '@m1') và quote của mục tiêu/mặt cắt dùng '@id' PHẢI bao hàm nguyên văn quote mô tả "
    "điểm đó. Không tự đặt tên đỉnh mới; vẫn trích đầy đủ kể cả khi hai điểm mô tả nối với nhau hoặc lồng nhau.\n"
    "4. derived_sections: plane_name không kèm ngoặc ('P', 'Q', 'α'). Mặt cắt đi qua 1 điểm (nhãn đỉnh hoặc "
    "@described_id) kèm 1 quan hệ ⇒ through_point_parallel_plane (điền through_point, params=['parallel_plane=A,B,C'] "
    "với ĐÚNG 3 nhãn đại diện mặt phẳng, ví dụ mặt (ABCD) ghi 'parallel_plane=A,B,C'), "
    "through_point_perpendicular_line (điền through_point, params=['perpendicular_line=S,A']), hoặc "
    "through_point_parallel_two_lines (điền through_point, params=['parallel_line_a=A,B','parallel_line_b=C,D']). "
    "Mặt cắt cho bằng tổ hợp quan hệ giữa các nhãn đỉnh (chứa cạnh/điểm, song song đường thẳng, vuông góc mặt phẳng) "
    "⇒ plane_kind='constrained', bỏ trống through_point và params, khai đủ các ràng buộc trong constraints dạng "
    "'contains_points=A,B' (1..4 nhãn), 'parallel_to_line=B,C' (2 nhãn), 'perpendicular_to_plane=S,C,D' (3..4 nhãn). "
    "Mặt cắt gọi bằng ĐÚNG ba nhãn điểm đã có (ví dụ 'cắt bởi mặt phẳng (MNP)') ⇒ plane_kind='constrained', "
    "plane_name='α', constraints=['contains_points=M,N,P'] (chỉ một ràng buộc này, không thêm quan hệ đề không nói), "
    "stated_intersections=[]; giao điểm của mặt đó với một đường thẳng (kể cả nằm ngoài đoạn) khai ở premises bằng "
    "intersect_line_plane, không khai ở stated_intersections. "
    "stated_intersections chỉ khai khi đề nêu rõ cạnh bị cắt.\n"
    "5. simulation_goals & math_goals: khi unresolved rỗng, mỗi khối chính trong solids PHẢI có 1 mục tiêu trong "
    "simulation_goals với kind='construct_object', target_solid_id trỏ tới solid_id của khối đó, quote nguyên văn cụm "
    "khai khối hoặc yêu cầu vẽ/mô phỏng (kể cả khi đề chỉ hỏi tính toán; nếu đề yêu cầu xác định/tìm thiết diện đã khai "
    "ở derived_sections thì dùng kind='construct_plane_section' với target_section_id='sec1'; nếu đề chỉ yêu cầu vẽ/mô "
    "phỏng thì để math_goals=[]). Câu hỏi tính toán ghi vào math_goals: kind='measurement' LUÔN điền solid_id của khối ở "
    "mức mục tiêu (không đặt solid_id cạnh toán hạng khác trong target), "
    "goal_type thuộc {distance, angle, volume, area, lateral_area, radius}; độ dài đoạn thẳng dùng goal_type='distance' "
    "với target=['segment=S,@o1']; khoảng cách điểm–mặt/đường dùng target=['point=@h1','plane=S,C,D'] hoặc "
    "['point=@h1','line=S,C']; góc dùng target=['line=A,@m1','plane=A,B,C,D'] hoặc ['line1=...','line2=...']; "
    "thể tích khối dùng target=['solid_id=s1']; diện tích thiết diện dùng target=['section_id=sec1']; diện tích đa giác "
    "dùng target=['polygon=A,B,@m1'].\n"
    "6. unresolved: chỉ dùng cho mệnh đề không thể biểu diễn trung thực vào lược đồ mà không đoán — mơ hồ nhiều cách "
    "hiểu (kind='ambiguous'), thiếu toán hạng/tên đỉnh/kích thước bắt buộc (kind='missing_operand'), thuật ngữ lạ "
    "(kind='unrecognized_term'), hoặc khái niệm ngoài lược đồ như toạ độ Oxyz, hình chóp cụt đa diện, cực trị min/max, "
    "quỹ tích/tập hợp điểm, phép biến hình, điểm đối xứng, bài toán thực tế vận tốc/thời gian (kind='unsupported') ⇒ "
    "ghi quote nguyên văn mệnh đề gây vướng, missing_roles thuộc {source_point, target_line_or_plane, relation_kind, "
    "solid_notation, dimension, goal_object}, candidate_relations (tối đa 3) thuộc {orthogonal_projection, intersection, "
    "midpoint, centroid, perpendicular, parallel, angle, distance}. Nếu đề nhắc tới mặt phẳng/đường thẳng/điểm đích hoặc "
    "kích thước cần dùng mà KHÔNG nêu tên hay giá trị ('góc giữa SB và mặt phẳng', 'hình chiếu vuông góc của A' không nói "
    "lên đâu, 'hình vuông' không có cạnh khi phải tính) thì ghi unresolved kind='missing_operand' — tuyệt đối không tự "
    "điền tên hay số. subject_ref chỉ điền khi là đúng 1 nhãn đỉnh nằm "
    "nguyên văn trong quote đó. Nếu chưa khai được khối hợp lệ có tên đỉnh thì để solids=[], premises=[], "
    "simulation_goals=[], math_goals=[]. Đề rõ ngữ pháp hình học nhưng mâu thuẫn số học hoặc mặt phẳng ràng buộc chưa "
    "đủ xác định duy nhất thì KHÔNG đưa vào unresolved — vẫn trích đầy đủ để bộ kiểm tất định từ chối."
)

_RELATION_EMPTY_ARRAY_DEFAULTS = (
    "pairs", "face_a", "face_b", "entity_a", "entity_b", "member_refs", "anchor_refs",
)
_SOLID_CORE_KEYS = ("solid_id", "solid_type", "notation", "quote")
_SECTION_CORE_KEYS = ("section_id", "plane_name", "target_solid_id", "plane_kind", "quote")
_SECTION_DIRECT_OPT_KEYS = ("through_point", "constraints", "stated_intersections")
_RELATION_CORE_KEYS = ("relation_id", "kind", "quote")
_SIM_GOAL_CORE_KEYS = ("goal_id", "kind", "quote")
_SIM_GOAL_DIRECT_OPT_KEYS = ("target_solid_id", "target_section_id")
_MATH_GOAL_CORE_KEYS = ("goal_id", "kind", "quote")
_MATH_GOAL_DIRECT_OPT_KEYS = ("goal_type", "solid_id")
_DESCRIBED_CORE_KEYS = ("described_id", "kind", "quote")
_FORBIDDEN_KV_NAMES = frozenset({"quote", "problem_text", "source_references"})
_LIST_VALUED_KV_KEYS = frozenset({
    *(k for m in (*_ARGS_LOI.values(), *_ARGS_GOC_VUONG) for k, sh in m.items() if sh.startswith("refs")),
    *(k for k, sh in GOAL_OPERAND_SHAPES.items() if sh.startswith("refs")),
    *(k for m in DESCRIBED_POINT_FIELDS.values() for k, sh in m.items() if sh != "pt"),
    "equation_coeffs", "parallel_plane", "perpendicular_line", "parallel_line_a", "parallel_line_b",
    "face_a", "face_b", "entity_a", "entity_b", "member_refs", "anchor_refs", "target_refs",
})


def _obj(props: dict[str, Any], required: list[str]) -> dict[str, Any]:
    return {"type": "OBJECT", "properties": props, "required": required, "propertyOrdering": list(props)}


def _typed_fact_next_v2_response_schema() -> dict[str, Any]:
    # ponytail: flat-item ordered wire schema (~2.8KB, <=4 optional props/object, 0 regex/bound DFAs) avoids Gemini FSM limit;
    # Python parse_typed_fact_next_v2 enforces all exact regex/enum/arity invariants fail-closed post-decode.
    s = {"type": "STRING"}
    s_arr = {"type": "ARRAY", "items": s}

    solid_item = _obj(
        {
            "solid_id": s,
            "solid_type": s,
            "notation": s,
            "quote": s,
            "vertex_bindings": s_arr,
            "params": s_arr,
        },
        ["solid_id", "solid_type", "notation", "quote"],
    )
    premise_item = _obj(
        {"kind": s, "args": s_arr, "quote": s, "solid_id": s},
        ["kind", "args", "quote"],
    )
    dp_item = _obj(
        {"described_id": s, "kind": s, "operands": s_arr, "quote": s},
        ["described_id", "kind", "operands", "quote"],
    )
    sec_item = _obj(
        {
            "section_id": s,
            "plane_name": s,
            "target_solid_id": s,
            "plane_kind": s,
            "through_point": s,
            "constraints": s_arr,
            "stated_intersections": {
                "type": "ARRAY",
                "items": _obj({"edge": s_arr, "point": s, "quote": s}, ["edge", "quote"]),
            },
            "params": s_arr,
            "quote": s,
        },
        ["section_id", "plane_name", "target_solid_id", "plane_kind", "quote"],
    )
    rel_item = _obj({"relation_id": s, "kind": s, "params": s_arr, "quote": s}, ["relation_id", "kind", "quote"])
    sg_item = _obj(
        {"goal_id": s, "kind": s, "target_solid_id": s, "target_section_id": s, "params": s_arr, "quote": s},
        ["goal_id", "kind", "quote"],
    )
    mg_item = _obj(
        {
            "goal_id": s,
            "kind": s,
            "goal_type": s,
            "solid_id": s,
            "target": s_arr,
            "params": s_arr,
            "quote": s,
        },
        ["goal_id", "kind", "quote"],
    )
    unres_item = _obj(
        {
            "unresolved_id": s,
            "kind": s,
            "subject_ref": s,
            "missing_roles": s_arr,
            "candidate_relations": s_arr,
            "quote": s,
        },
        ["unresolved_id", "kind", "quote"],
    )
    return _obj(
        {
            "schema_version": s,
            "problem_text": s,
            "length_unit": s,
            "solids": {"type": "ARRAY", "items": solid_item},
            "premises": {"type": "ARRAY", "items": premise_item},
            "described_points": {"type": "ARRAY", "items": dp_item},
            "derived_sections": {"type": "ARRAY", "items": sec_item},
            "relations": {"type": "ARRAY", "items": rel_item},
            "simulation_goals": {"type": "ARRAY", "items": sg_item},
            "math_goals": {"type": "ARRAY", "items": mg_item},
            "unresolved": {"type": "ARRAY", "items": unres_item},
        },
        ["schema_version", "problem_text", "length_unit", "solids", "premises", "simulation_goals", "math_goals"],
    )


def _pack_kv_strings(mapping: Mapping[str, Any], *, pair_keys: tuple[str, ...] = ()) -> list[str]:
    out: list[str] = []
    for k, v in mapping.items():
        if v is None:
            continue
        if k in pair_keys and isinstance(v, (list, tuple)):
            if v:
                out.append(f"{k}=" + ";".join(f"{a},{b}" for a, b in v))
        elif isinstance(v, (list, tuple)):
            out.append(f"{k}=" + ",".join(str(x) for x in v))
        else:
            out.append(f"{k}={v}")
    return out


def to_wire_typed_fact_next_v2(canonical: Mapping[str, Any]) -> dict[str, Any]:
    """Losslessly pack a canonical `typed-fact-next/2` dict into the compact Gemini wire `responseSchema` shape."""
    src = deepcopy(dict(canonical))
    wire: dict[str, Any] = {
        "schema_version": src.get("schema_version", TYPED_FACT_NEXT_V2_SCHEMA_VERSION),
        "problem_text": src["problem_text"],
        "length_unit": src.get("length_unit") or "1",
        "solids": [],
        "premises": [],
    }
    for s in src.get("solids") or ():
        ws: dict[str, Any] = {
            "solid_id": s["solid_id"],
            "solid_type": s.get("solid_type", "pyramid"),
            "notation": s["notation"],
            "quote": s["quote"],
        }
        if s.get("vertex_bindings"):
            vb = s["vertex_bindings"]
            ws["vertex_bindings"] = (
                [f"{k}={v}" for k, v in vb.items()] if isinstance(vb, dict) else list(vb)
            )
        extra = {k: v for k, v in s.items() if k not in (*_SOLID_CORE_KEYS, "vertex_bindings")}
        if params := _pack_kv_strings(extra):
            ws["params"] = params
        wire["solids"].append(ws)

    for p in src.get("premises") or ():
        wp: dict[str, Any] = {
            "kind": p["kind"],
            "args": _pack_kv_strings(p.get("args") or {}) if isinstance(p.get("args"), Mapping) else list(p.get("args") or ()),
            "quote": p["quote"],
        }
        if p.get("solid_id") is not None:
            wp["solid_id"] = p["solid_id"]
        wire["premises"].append(wp)

    if src.get("described_points"):
        wire["described_points"] = []
        for dp in src["described_points"]:
            ops = {k: v for k, v in dp.items() if k not in (*_DESCRIBED_CORE_KEYS, "operands")}
            wire["described_points"].append({
                "described_id": dp["described_id"],
                "kind": dp["kind"],
                "operands": dp["operands"] if "operands" in dp else _pack_kv_strings(ops),
                "quote": dp["quote"],
            })

    if "derived_sections" in src:
        wire["derived_sections"] = []
        for sec in src.get("derived_sections") or ():
            wsec: dict[str, Any] = {k: sec[k] for k in _SECTION_CORE_KEYS if k in sec}
            wsec.setdefault("plane_name", "α")
            if sec.get("through_point") is not None:
                wsec["through_point"] = sec["through_point"]
            if sec.get("constraints"):
                wsec["constraints"] = [
                    f"{c['kind']}={','.join(str(x) for x in c['operands'])}" if isinstance(c, Mapping) else str(c)
                    for c in sec["constraints"]
                ]
            if sec.get("stated_intersections"):
                wsec["stated_intersections"] = [
                    {ik: iv for ik, iv in si.items() if iv is not None} for si in sec["stated_intersections"]
                ]
            extra = {k: v for k, v in sec.items() if k not in (*_SECTION_CORE_KEYS, *_SECTION_DIRECT_OPT_KEYS, "params")}
            if params := _pack_kv_strings(extra, pair_keys=("declared_boundary",)):
                wsec["params"] = params
            wire["derived_sections"].append(wsec)

    if "relations" in src:
        wire["relations"] = []
        for rel in src.get("relations") or ():
            wrel: dict[str, Any] = {k: rel[k] for k in _RELATION_CORE_KEYS}
            extra = {k: v for k, v in rel.items() if k not in (*_RELATION_CORE_KEYS, "params") and v != []}
            if params := _pack_kv_strings(extra, pair_keys=("pairs",)):
                wrel["params"] = params
            wire["relations"].append(wrel)

    wire["simulation_goals"] = []
    for sg in src.get("simulation_goals") or ():
        wsg: dict[str, Any] = {k: sg[k] for k in _SIM_GOAL_CORE_KEYS}
        for k in _SIM_GOAL_DIRECT_OPT_KEYS:
            if sg.get(k) is not None:
                wsg[k] = sg[k]
        extra = {k: v for k, v in sg.items() if k not in (*_SIM_GOAL_CORE_KEYS, *_SIM_GOAL_DIRECT_OPT_KEYS, "params") and v != []}
        if params := _pack_kv_strings(extra):
            wsg["params"] = params
        wire["simulation_goals"].append(wsg)

    wire["math_goals"] = []
    for mg in src.get("math_goals") or ():
        wmg: dict[str, Any] = {k: mg[k] for k in _MATH_GOAL_CORE_KEYS}
        for k in _MATH_GOAL_DIRECT_OPT_KEYS:
            if mg.get(k) is not None:
                wmg[k] = mg[k]
        if mg.get("target"):
            t = mg["target"]
            wmg["target"] = _pack_kv_strings(t) if isinstance(t, Mapping) else list(t)
        extra = {
            k: v for k, v in mg.items()
            if k not in (*_MATH_GOAL_CORE_KEYS, *_MATH_GOAL_DIRECT_OPT_KEYS, "target", "params")
        }
        if params := _pack_kv_strings(extra):
            wmg["params"] = params
        wire["math_goals"].append(wmg)

    if src.get("unresolved"):
        wire["unresolved"] = [
            {k: v for k, v in u.items() if v is not None} for u in src["unresolved"]
        ]
    return wire


def _strip_none_keys(item: dict[str, Any], blank_opt_keys: tuple[str, ...] = ()) -> dict[str, Any]:
    return {
        k: v for k, v in item.items()
        if v is not None and not (k in blank_opt_keys and isinstance(v, str) and not v.strip())
    }


def _split_csv_tokens(rhs: str, label: str) -> list[str]:
    parts = [tok.strip() for tok in rhs.split(",")]
    if not rhs.strip() or any(not tok for tok in parts):
        raise TypedFactNextValidationError("INVALID_TYPED_FACT_NEXT", f"Malformed comma-separated list for {label!r}.")
    return parts


def _unpack_kv_strings(entries: Any, *, pair_keys: tuple[str, ...] = ()) -> dict[str, Any]:
    if not isinstance(entries, list):
        raise TypedFactNextValidationError("INVALID_TYPED_FACT_NEXT", "Expected list of 'key=value' entries.")
    unpacked: dict[str, Any] = {}
    for raw_entry in entries:
        if not isinstance(raw_entry, str):
            raise TypedFactNextValidationError("INVALID_TYPED_FACT_NEXT", "KV wire entry must be a 'key=value' string.")
        name, sep, rhs = raw_entry.partition("=")
        name = name.strip()
        rhs = rhs.strip()
        if not sep or not name or not rhs or name in _FORBIDDEN_KV_NAMES:
            raise TypedFactNextValidationError("INVALID_TYPED_FACT_NEXT", f"Invalid KV wire entry {raw_entry!r}.")
        if name in unpacked:
            raise TypedFactNextValidationError("INVALID_TYPED_FACT_NEXT", f"Duplicate KV wire key {name!r}.")
        if name in pair_keys:
            pairs = []
            for seg in rhs.split(";"):
                toks = _split_csv_tokens(seg, name)
                if len(toks) != 2:
                    raise TypedFactNextValidationError("INVALID_TYPED_FACT_NEXT", f"Pair entry {name!r} needs 2 refs.")
                pairs.append(toks)
            unpacked[name] = pairs
        elif name in _LIST_VALUED_KV_KEYS:
            unpacked[name] = _split_csv_tokens(rhs, name)
        else:
            unpacked[name] = rhs
    return unpacked


def _merge_unpacked_params(target: dict[str, Any], field: str, *, pair_keys: tuple[str, ...] = ()) -> None:
    if field not in target:
        return
    extra = _unpack_kv_strings(target.pop(field), pair_keys=pair_keys)
    overlap = set(extra) & set(target)
    if overlap:
        raise TypedFactNextValidationError("INVALID_TYPED_FACT_NEXT", f"Conflicting keys in {field}: {sorted(overlap)}.")
    target.update(extra)


def _unpack_constraints(raw_constraints: Any) -> Any:
    if not isinstance(raw_constraints, list):
        return raw_constraints
    out = []
    for item in raw_constraints:
        if isinstance(item, dict):
            out.append(_strip_none_keys(item))
            continue
        if not isinstance(item, str):
            raise TypedFactNextValidationError("INVALID_DERIVED_SECTION", "Plane constraint must be string or object.")
        kind, sep, rhs = item.partition("=")
        if not sep:
            kind, sep, rhs = item.partition(":")
        kind = kind.strip()
        if not sep or not kind:
            raise TypedFactNextValidationError("INVALID_DERIVED_SECTION", f"Malformed plane constraint {item!r}.")
        out.append({"kind": kind, "operands": _split_csv_tokens(rhs, kind)})
    return out


def _normalize_transport_payload(data: Any) -> Any:
    """Unpack compact wire `'key=value'` lists and canonicalize placeholders into `typed-fact-next/2` shape."""
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
            _merge_unpacked_params(s_clean, "params")
            if "vertex_bindings" in s_clean:
                vb = s_clean["vertex_bindings"]
                if isinstance(vb, list):
                    vb_dict: dict[str, str] = {}
                    for entry in vb:
                        if isinstance(entry, str):
                            loc, sep, can = entry.partition("=")
                            loc, can = loc.strip(), can.strip()
                            if not sep or not loc or not can:
                                raise TypedFactNextValidationError(
                                    "INVALID_TYPED_FACT_NEXT", f"Invalid vertex_bindings entry {entry!r}."
                                )
                        elif (
                            isinstance(entry, dict)
                            and isinstance(entry.get("local"), str)
                            and isinstance(entry.get("canonical"), str)
                        ):
                            loc, can = entry["local"], entry["canonical"]
                        else:
                            raise TypedFactNextValidationError(
                                "INVALID_TYPED_FACT_NEXT", "vertex_bindings entry must be 'local=canonical'."
                            )
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
            p_clean = _strip_none_keys(p, ("solid_id",))
            if isinstance(p_clean.get("args"), list):
                p_clean["args"] = _unpack_kv_strings(p_clean["args"])
            elif isinstance(p_clean.get("args"), dict):
                p_clean["args"] = _strip_none_keys(p_clean["args"])
            norm_premises.append(p_clean)
        out["premises"] = norm_premises

    if isinstance(out.get("derived_sections"), list):
        norm_sections = []
        for sec in out["derived_sections"]:
            if not isinstance(sec, dict):
                norm_sections.append(sec)
                continue
            sec_clean = _strip_none_keys(sec, ("through_point",))
            _merge_unpacked_params(sec_clean, "params", pair_keys=("declared_boundary",))
            if "constraints" in sec_clean:
                sec_clean["constraints"] = _unpack_constraints(sec_clean["constraints"])
            if sec_clean.get("constraints") == [] and sec_clean.get("plane_kind") != "constrained":
                sec_clean.pop("constraints", None)
            if "stated_intersections" not in sec_clean:
                sec_clean["stated_intersections"] = []
            elif isinstance(sec_clean["stated_intersections"], list):
                sec_clean["stated_intersections"] = [
                    _strip_none_keys(si, ("point",)) if isinstance(si, dict) else si
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
            rel_clean = _strip_none_keys(rel)
            _merge_unpacked_params(rel_clean, "params", pair_keys=("pairs",))
            rel_clean = {
                k: v for k, v in rel_clean.items()
                if not (k in _RELATION_EMPTY_ARRAY_DEFAULTS and v == [])
            }
            norm_rels.append(rel_clean)
        out["relations"] = norm_rels

    if isinstance(out.get("simulation_goals"), list):
        norm_sgs = []
        for sg in out["simulation_goals"]:
            if not isinstance(sg, dict):
                norm_sgs.append(sg)
                continue
            sg_clean = _strip_none_keys(sg, ("target_solid_id", "target_section_id"))
            _merge_unpacked_params(sg_clean, "params")
            if (
                sg_clean.get("kind") == "construct_object"
                and "target_section_id" in sg_clean
                and "target_solid_id" not in sg_clean
            ):
                sg_clean["kind"] = "construct_plane_section"
            if sg_clean.get("style_role") == "primary":
                sg_clean.pop("style_role", None)
            if sg_clean.get("target_refs") == []:
                sg_clean.pop("target_refs", None)
            norm_sgs.append(sg_clean)
        out["simulation_goals"] = norm_sgs

    solids_list = out.get("solids") if isinstance(out.get("solids"), list) else []
    has_derived_solid = any(
        isinstance(sg, dict) and sg.get("kind") == "construct_derived_solid"
        for sg in (out.get("simulation_goals") if isinstance(out.get("simulation_goals"), list) else ())
    )
    single_solid_id = (
        solids_list[0].get("solid_id").strip()
        if len(solids_list) == 1
        and isinstance(solids_list[0], dict)
        and isinstance(solids_list[0].get("solid_id"), str)
        and solids_list[0].get("solid_id").strip()
        and not has_derived_solid
        else None
    )

    if isinstance(out.get("math_goals"), list):
        norm_mgs = []
        for mg in out["math_goals"]:
            if not isinstance(mg, dict):
                norm_mgs.append(mg)
                continue
            mg_clean = _strip_none_keys(mg, ("goal_type", "solid_id"))
            _merge_unpacked_params(mg_clean, "params")
            if isinstance(mg_clean.get("target"), list):
                mg_clean["target"] = _unpack_kv_strings(mg_clean["target"])
            elif isinstance(mg_clean.get("target"), dict):
                mg_clean["target"] = _strip_none_keys(mg_clean["target"])
            if mg_clean.get("target") == {} and mg_clean.get("kind") != "measurement":
                mg_clean.pop("target", None)
            if (
                single_solid_id is not None
                and mg_clean.get("kind") == "measurement"
                and "solid_id" not in mg_clean
                and isinstance(mg_clean.get("target"), dict)
                and "solid" not in mg_clean["target"]
                and "solid_id" not in mg_clean["target"]
            ):
                mg_clean["solid_id"] = single_solid_id
            norm_mgs.append(mg_clean)
        out["math_goals"] = norm_mgs

    if "described_points" in out:
        if not out["described_points"]:
            out.pop("described_points", None)
        elif isinstance(out["described_points"], list):
            norm_dps = []
            for dp in out["described_points"]:
                if not isinstance(dp, dict):
                    norm_dps.append(dp)
                    continue
                dp_clean = _strip_none_keys(dp)
                _merge_unpacked_params(dp_clean, "operands")
                norm_dps.append(dp_clean)
            out["described_points"] = norm_dps

    if "unresolved" in out:
        if not out["unresolved"]:
            out.pop("unresolved", None)
        elif isinstance(out["unresolved"], list):
            norm_unres = []
            for u in out["unresolved"]:
                if not isinstance(u, dict):
                    norm_unres.append(u)
                    continue
                u_clean = _strip_none_keys(u, ("subject_ref",))
                u_clean.setdefault("missing_roles", [])
                u_clean.setdefault("candidate_relations", [])
                if isinstance(u_clean["missing_roles"], list):
                    u_clean["missing_roles"] = [r for r in u_clean["missing_roles"] if r in MISSING_ROLES]
                if isinstance(u_clean["candidate_relations"], list):
                    u_clean["candidate_relations"] = [
                        r for r in u_clean["candidate_relations"] if r in CANDIDATE_RELATIONS
                    ][:3]
                norm_unres.append(u_clean)
            out["unresolved"] = norm_unres

    return _repair_observed_wire_shapes(out)


# ── C26: exact, meaning-preserving repairs of wire shapes OBSERVED in live Gemini Run 3 ───────────────────────────────
# Each repair only re-files what the source states verbatim into the slot the contract expects; quotes stay verbatim
# substrings of `problem_text` and every repaired item still goes through the Source Gate. Anything not uniquely
# determined is left untouched (and fails closed downstream).

#: "M là trung điểm của AB" / "Gọi N là …": the clause NAMES the point (a premise), it does not describe an unnamed one.
_NAMED_CLAUSE_RE = re.compile(r"^\s*(?:[Gg]ọi\s+)?(?P<label>[A-Z][0-9]*'*)\s+là\s+")
#: described kind → (premise kind, the premise arg that carries the named point); operand keys are shared.
_NAMED_POINT_PREMISE = {
    "midpoint": ("midpoint", "point"),
    "centroid": ("centroid", "point"),
    "intersect_line_line": ("intersect_line_line", "point"),
    "intersect_line_plane": ("intersect_line_plane", "point"),
    "orthogonal_projection": ("orthogonal_projection", "image"),
    "orthogonal_projection_line": ("orthogonal_projection_line", "image"),
}
_SIDE_CLAUSE_RE = re.compile(r"^cạnh\s+(?P<value>\S+)$")
_SEGMENT_EQ_RE = re.compile(r"^\s*(?P<lhs>[A-Z0-9']+)\s*=\s*(?P<value>\S+?)\s*$")


def _replace_refs(value: Any, mapping: Mapping[str, str]) -> Any:
    if isinstance(value, str):
        return mapping.get(value.strip(), value)
    if isinstance(value, list):
        return [_replace_refs(v, mapping) for v in value]
    if isinstance(value, dict):
        return {k: (v if k == "quote" else _replace_refs(v, mapping)) for k, v in value.items()}
    return value


def _named_described_points_to_premises(out: dict[str, Any], single_solid_id: str | None) -> None:
    """A described point whose quote names it ("M là trung điểm của AB") becomes the matching premise; refs `@id` to it
    become the label. Unconvertible kinds (orthocenter/circumcenter have no premise) and refs still pointing at an
    unconverted described point are left as they are."""
    dps = out.get("described_points")
    premises = out.get("premises")
    if not isinstance(dps, list) or not isinstance(premises, list):
        return
    mapping: dict[str, str] = {}
    pending = [dp for dp in dps if isinstance(dp, dict)]
    changed = True
    while changed:
        changed = False
        for dp in list(pending):
            m = _NAMED_CLAUSE_RE.match(str(dp.get("quote") or ""))
            spec = _NAMED_POINT_PREMISE.get(dp.get("kind"))
            if not m or spec is None or not isinstance(dp.get("described_id"), str):
                continue
            kind, point_key = spec
            fields = DESCRIBED_POINT_FIELDS[dp["kind"]]
            if set(fields) - set(dp) or any(k in dp for k in (point_key, "point") if k not in fields):
                continue
            args = {k: _replace_refs(dp[k], mapping) for k in fields}
            flat = [x for v in args.values() for x in (v if isinstance(v, list) else [v])]
            if any(isinstance(x, str) and x.strip().startswith("@") for x in flat):
                continue                                  # depends on a described point not (yet) converted
            label = m.group("label")
            args[point_key] = label
            premise = {"kind": kind, "args": args, "quote": dp["quote"]}
            if single_solid_id is not None:
                premise["solid_id"] = single_solid_id
            if not any(isinstance(p, dict) and p.get("kind") == kind and (p.get("args") or {}) == args
                       for p in premises):
                premises.append(premise)
            mapping[f"@{dp['described_id'].strip()}"] = label
            pending.remove(dp)
            changed = True
    if not mapping:
        return
    out["described_points"] = [_replace_refs(dp, mapping) for dp in pending]
    if not out["described_points"]:
        out.pop("described_points")
    for key in ("math_goals", "derived_sections", "relations", "simulation_goals"):
        if isinstance(out.get(key), list):
            out[key] = [_replace_refs(item, mapping) for item in out[key]]


def _polygon_edges(vertices: list[str]) -> set[frozenset[str]]:
    return {frozenset((vertices[i], vertices[(i + 1) % len(vertices)])) for i in range(len(vertices))}


def _repair_square_premises(out: dict[str, Any], text: str) -> None:
    premises = out.get("premises")
    if not isinstance(premises, list):
        return

    def verts(p: dict[str, Any]) -> list[str] | None:
        v = (p.get("args") or {}).get("vertices")
        return v if isinstance(v, list) and all(isinstance(x, str) for x in v) else None

    # "hình vuông" filed as `rectangle`: a square is the regular quadrilateral of the contract.
    kept: list[Any] = []
    for p in premises:
        q = str(p.get("quote") or "") if isinstance(p, dict) else ""
        if (isinstance(p, dict) and p.get("kind") == "rectangle" and "hình vuông" in q and "chữ nhật" not in q
                and (v := verts(p)) and len(v) == 4):
            if any(isinstance(o, dict) and o.get("kind") == "regular_polygon" and set(verts(o) or ()) == set(v)
                   for o in premises):
                continue                                  # duplicate of the regular_polygon already filed
            p = {**p, "kind": "regular_polygon"}
        kept.append(p)
    premises[:] = kept

    for p in premises:
        if not (isinstance(p, dict) and p.get("kind") == "regular_polygon" and (v := verts(p))):
            continue
        q = str(p.get("quote") or "")
        name = "".join(v)
        # the polygon's quote must name it: take the immediately preceding "(đáy) ABCD là " of the same clause
        if name not in q and q and text.count(q) == 1:
            start = text.index(q)
            for prefix in (f"đáy {name} là ", f"{name} là "):
                if text[:start].endswith(prefix):
                    p["quote"] = q = prefix + q
                    break
        # "hình vuông cạnh 2" split into a side-less polygon + a bare "cạnh 2" length on one of its edges
        for s in list(premises):
            if not (isinstance(s, dict) and s.get("kind") == "segment_length"):
                continue
            sm = _SIDE_CLAUSE_RE.match(str(s.get("quote") or ""))
            seg = (s.get("args") or {}).get("segment")
            if not sm or not isinstance(seg, list) or frozenset(seg) not in _polygon_edges(v):
                continue
            value = str((s.get("args") or {}).get("value"))
            if value != sm.group("value"):
                continue
            side = (p.get("args") or {}).get("side")
            if side is None:
                for sep in (" ", ", "):
                    joined = q + sep + s["quote"]
                    if joined in text:
                        p["args"] = {**p["args"], "side": value}
                        p["quote"] = q = joined
                        premises.remove(s)
                        break
            elif str(side) == value and s["quote"] in q:
                premises.remove(s)                         # restates the side the polygon already carries


def _repair_restated_premises(out: dict[str, Any], text: str, single_solid_id: str | None) -> None:
    premises = out.get("premises")
    if not isinstance(premises, list):
        return
    perp = {frozenset((p.get("args") or {}).get("line") or ()) for p in premises
            if isinstance(p, dict) and p.get("kind") == "perpendicular_line_plane"}
    seg_quotes = {p.get("quote") for p in premises if isinstance(p, dict) and p.get("kind") == "segment_length"}
    solids = [s for s in out.get("solids") or () if isinstance(s, dict)]
    labels = sorted({tok for s in solids for tok in re.findall(r"[A-Z][0-9]*'*", str(s.get("notation") or ""))},
                    key=len, reverse=True)
    kept: list[Any] = []
    for p in premises:
        if not isinstance(p, dict):
            kept.append(p)
            continue
        q = str(p.get("quote") or "")
        args = p.get("args") or {}
        if p.get("kind") == "altitude" and "đường cao" not in q and "chiều cao" not in q:
            if frozenset((args.get("apex"), args.get("foot"))) in perp:
                continue                                   # an inference from "SA ⊥ (ABCD)", not a stated altitude
        if p.get("kind") == "height" and (m := _SEGMENT_EQ_RE.match(q)) and str(args.get("value")) == m.group("value"):
            if q in seg_quotes:
                continue                                   # "AA' = 2" already filed as the segment it names
            lhs, toks = m.group("lhs"), []
            while lhs:
                tok = next((t for t in labels if lhs.startswith(t)), None)
                if tok is None:
                    break
                toks.append(tok)
                lhs = lhs[len(tok):]
            if not lhs and len(toks) == 2 and toks[0] != toks[1]:
                p = {**p, "kind": "segment_length", "args": {"segment": toks, "value": m.group("value")}}
        if (p.get("kind") == "altitude" and single_solid_id is not None and solids
                and not any(str(s.get("notation")) in q for s in solids)):
            sq = str(solids[0].get("quote") or "")
            if sq and text.count(sq) == 1 and text.count(q) == 1:
                a, b = text.index(sq), text.index(q)
                span = text[a:b + len(q)]
                if a < b and not re.search(r"[.?!;]\s", span):
                    p = {**p, "quote": span}               # bind "đường cao SA" to the one solid of its sentence
        kept.append(p)
    premises[:] = kept


def _repair_simulation_goal_target_refs(out: dict[str, Any]) -> None:
    """Canonicalize `simulation_goals[*].vertex`/`point` -> `target_refs` only when verbatim-grounded in `sg.quote`."""
    goals = out.get("simulation_goals")
    if not isinstance(goals, list):
        return
    for sg in goals:
        if not isinstance(sg, dict) or sg.get("kind") not in ("construct_object", "highlight_geometry") or "target_refs" in sg:
            continue
        extra = [k for k in ("vertex", "point") if k in sg]
        if len(extra) != 1 or not isinstance(val := sg[extra[0]], str) or not val.strip():
            continue
        tok = val.strip()
        lbl = tok.split("::")[-1]
        q = str(sg.get("quote") or "")
        if tok.startswith("@") or (lbl and re.search(rf"(?<![\w']){re.escape(lbl)}(?![\w'])", q)):
            sg.pop(extra[0])
            sg["target_refs"] = [tok]


def _repair_observed_wire_shapes(out: dict[str, Any]) -> dict[str, Any]:
    text = out.get("problem_text")
    if not isinstance(text, str):
        return out
    solids = [s for s in out.get("solids") or () if isinstance(s, dict)]
    single = (solids[0].get("solid_id") if len(solids) == 1 and isinstance(solids[0].get("solid_id"), str) else None)
    _named_described_points_to_premises(out, single)
    _repair_square_premises(out, text)
    _repair_restated_premises(out, text, single)
    _repair_simulation_goal_target_refs(out)
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
        if "source_references" not in raw:
            raw = _repair_observed_wire_shapes(deepcopy(raw))
            references = tuple(_check_quotes(raw, problem_text))
        payload = parse_typed_fact_next_v2(raw).model_copy(update={"problem_text": problem_text})
        _check_premise_roles(payload, problem_text)
    except (TypedFactNextValidationError, _TuChoiAI) as exc:
        return ExtractionResult(None, exc.code, diagnostics)
    except Exception:
        return ExtractionResult(None, "EXTRACTOR_INTERNAL_ERROR", diagnostics)
    diagnostics["validation"] = "SCHEMA_AND_SOURCE_IDENTITY/QUOTE_VALID"
    return ExtractionResult(payload, None, diagnostics, references)
