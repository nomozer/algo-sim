"""Source-only canonical V2 extraction; transport is injected, never installed here."""
from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
import re
from typing import Any, Callable, Mapping, Protocol

from app.ai.fact_extraction import _TuChoiAI, build_request, parse_response
from app.ai.function_calling import _openapi
from app.simulation.geometry_functions.registry import _phu_dinh, _vai_tro_tai, _vi_tri, chuan_hoa
from app.simulation.geometry_functions.typed_fact_next import (
    TYPED_FACT_NEXT_V2_SCHEMA_VERSION,
    TypedFactNextPayloadV2,
    TypedFactNextValidationError,
    parse_typed_fact_next_v2,
)


class Extractor(Protocol):
    def extract(self, source_text: str) -> dict[str, Any] | None: ...


@dataclass(frozen=True)
class ExtractionResult:
    payload: TypedFactNextPayloadV2 | None
    code: str | None
    diagnostics: dict[str, Any]


class ReplayExtractor:
    def __init__(self, outputs: Mapping[str, dict[str, Any]]) -> None:
        self.outputs = deepcopy(outputs)

    def extract(self, source_text: str) -> dict[str, Any] | None:
        return deepcopy(self.outputs.get(source_text))


class TransportExtractor:
    """One source-only request using the existing provider framing and response parser."""

    def __init__(self, transport: Callable[[dict[str, Any]], Any]) -> None:
        self.transport = transport

    def extract(self, source_text: str) -> dict[str, Any]:
        request = build_request(source_text)
        schema = TypedFactNextPayloadV2.model_json_schema()
        request["generationConfig"]["responseSchema"] = _openapi(
            {k: v for k, v in schema.items() if k != "$defs"}, schema.get("$defs", {}))
        request["systemInstruction"]["parts"][0]["text"] = (
            "Chỉ trích dữ kiện theo lược đồ typed-fact-next/2; giữ nguyên problem_text và mọi quote. "
            "Ghi đủ đối tượng, dữ kiện, mục tiêu dựng và câu hỏi của đề. Không tự thêm dữ kiện, "
            "không tính toán, không chọn phép dựng, không sinh toạ độ hoặc mã. "
            "Không biến phủ định, điều kiện hay điều phải chứng minh thành premise. "
            "stated_intersections chỉ chứa giao điểm đề nêu; không tự suy ra giao điểm còn lại.")
        try:
            body = self.transport(request)
        except Exception:
            raise _TuChoiAI("PROVIDER_ERROR", "transport failed") from None
        return parse_response(body, {})


def _check_quotes(value: Any, source_text: str) -> None:
    if isinstance(value, dict):
        for key, item in value.items():
            if key == "quote" and (not isinstance(item, str) or not item or item not in source_text):
                raise _TuChoiAI("QUOTE_NOT_IN_SOURCE", "quote is not verbatim source")
            _check_quotes(item, source_text)
    elif isinstance(value, (list, tuple)):
        for item in value:
            _check_quotes(item, source_text)


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
        _check_quotes(raw, problem_text)
        payload = parse_typed_fact_next_v2(raw).model_copy(update={"problem_text": problem_text})
        _check_premise_roles(payload, problem_text)
    except (TypedFactNextValidationError, _TuChoiAI) as exc:
        return ExtractionResult(None, exc.code, diagnostics)
    except Exception:
        return ExtractionResult(None, "EXTRACTOR_INTERNAL_ERROR", diagnostics)
    diagnostics["validation"] = "SCHEMA_AND_SOURCE_IDENTITY/QUOTE_VALID"
    return ExtractionResult(payload, None, diagnostics)
