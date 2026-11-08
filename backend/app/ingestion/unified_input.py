"""Điều phối chuẩn bị đầu vào thống nhất (Ảnh · PDF scan · PDF text · DOCX · Văn bản kèm tệp).

Hợp đồng (§9–§18):
- Chỉ chạy SAU KHI học sinh bấm "Dựng hình" (`POST /api/input/prepare`).
- Mọi loại tệp đi qua: xác thực magic bytes -> trích xuất đặc thù theo định dạng ->
  phát hiện vùng bài / chọn bài theo ngữ cảnh -> kiểm tra độ đầy đủ -> chỉ gọi VLM khi
  thực sự cần -> trả văn bản bài toán sạch để nối thẳng vào tuyến Hybrid `/4` (`POST /api/analyze`).
- Không tự đoán bài đầu tiên khi có nhiều bài độc lập; không cắt mất hình vẽ hoặc ký hiệu nhỏ;
  luôn giữ fallback về ảnh đầy đủ đã chuẩn hóa khi vùng cắt có nguy cơ thiếu dữ kiện.
"""

from __future__ import annotations

import hashlib
import os
import re
import time
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field, replace
from typing import Any, Literal

from app.ingestion.document_reader import (
    InputPrepareRejected,
    TextProblemCandidate,
    UserComposerDirective,
    decode_attachment_base64,
    extract_docx_structured,
    extract_pdf_structured,
    merge_supplemental_text,
    parse_user_composer_instruction,
    render_pdf_page_normalized,
    select_text_candidate,
    sniff_input_file_kind,
    split_text_into_problems,
)
from app.ingestion.image import ImageRejected, NormalizedImage, normalize_image
from app.ingestion.image_extraction import (
    FLAG_MESSAGES,
    REJECTION_MESSAGES,
    _THAM_CHIEU_HINH,
    ExtractionResult,
    extract_problem_from_image,
)
from app.ingestion.region_detector import (
    CandidateProblemRegion,
    RegionDetectionResult,
    detect_problem_regions,
)
from app.simulation.semantic_program.domain_profile import DOMAIN_HINH_HOC, detect_domain

UNIFIED_INPUT_SCHEMA = "unified-input-prepare/1"
MAX_PREPARE_ATTACHMENTS = 10
MAX_TOTAL_ATTACHMENT_BYTES = 25 * 1024 * 1024


class LiveVisionDisabledError(RuntimeError):
    code = "LIVE_AI_DISABLED"


class MissingVisionKeyError(RuntimeError):
    code = "MISSING_API_KEY"


@dataclass(frozen=True)
class UnifiedCandidateItem:
    candidate_id: str
    label: str
    preview_snippet: str = ""
    preview_data_url: str | None = None
    page_number: int | None = None
    has_figure: bool = False
    problem_text: str | None = None
    source_attachment_ids: tuple[str, ...] = ()
    source_bbox: tuple[float, float, float, float] | None = None

    def to_dict(self) -> dict[str, Any]:
        out: dict[str, Any] = {
            "candidate_id": self.candidate_id,
            "label": self.label,
            "preview_snippet": self.preview_snippet,
            "preview_data_url": self.preview_data_url,
            "page_number": self.page_number,
            "has_figure": self.has_figure,
            "problem_text": self.problem_text,
            "source_attachment_ids": list(self.source_attachment_ids),
        }
        if self.source_bbox is not None:
            out["source_bbox"] = list(self.source_bbox)
        return out


@dataclass(frozen=True)
class UnifiedPrepareOutcome:
    status: Literal["ready", "needs_selection", "needs_confirmation", "rejected"]
    source_kind: Literal["image", "pdf", "docx"]
    problem_text: str = ""
    learner_message: str | None = None
    reason_code: str | None = None
    flag_messages: tuple[str, ...] = ()
    uncertain_tokens: tuple[dict[str, Any], ...] = ()
    missing_regions: tuple[str, ...] = ()
    candidates: tuple[UnifiedCandidateItem, ...] = ()
    provenance: dict[str, Any] = field(default_factory=dict)
    metrics: dict[str, Any] = field(default_factory=dict)
    request_id: str | None = None

    def to_dict(self) -> dict[str, Any]:
        prov = dict(self.provenance)
        if self.request_id is not None and "request_id" not in prov:
            prov["request_id"] = self.request_id
        out: dict[str, Any] = {
            "schema": UNIFIED_INPUT_SCHEMA,
            "status": self.status,
            "source_kind": self.source_kind,
            "problem_text": self.problem_text,
            "learner_message": self.learner_message,
            "reason_code": self.reason_code,
            "flag_messages": list(self.flag_messages),
            "uncertain_tokens": list(self.uncertain_tokens),
            "missing_regions": list(self.missing_regions),
            "candidates": [c.to_dict() for c in self.candidates],
            "provenance": prov,
            "metrics": dict(self.metrics),
        }
        if self.request_id is not None:
            out["request_id"] = self.request_id
        return out


def _require_vision_key(api_key: str | None) -> str:
    if os.getenv("ALLOW_LIVE_AI") == "0":
        raise LiveVisionDisabledError("Chế độ trích xuất trực tiếp đang tắt (ALLOW_LIVE_AI=0).")
    if not api_key:
        raise MissingVisionKeyError("Thiếu GEMINI_API_KEY để đọc ảnh/trang scan.")
    return api_key


def _text_candidates_to_items(
    pool: list[TextProblemCandidate],
    *,
    parent_bbox: tuple[float, float, float, float] | None = None,
) -> tuple[UnifiedCandidateItem, ...]:
    n = max(1, len(pool))
    bx, by, bw, bh = parent_bbox if parent_bbox is not None else (0.0, 0.0, 1.0, 1.0)
    band_h = round(bh / n, 4)
    items: list[UnifiedCandidateItem] = []
    for idx, c in enumerate(pool):
        y_start = round(by + idx * band_h, 4)
        h_cur = round(bh - idx * band_h, 4) if idx == n - 1 else band_h
        items.append(
            UnifiedCandidateItem(
                candidate_id=c.candidate_id,
                label=c.label,
                preview_snippet=c.preview_snippet,
                preview_data_url=None,
                page_number=c.page_number,
                has_figure=c.has_figure,
                problem_text=c.problem_text,
                source_bbox=(bx, y_start, bw, max(0.01, h_cur)),
            )
        )
    return tuple(items)


def _region_candidates_to_items(
    regions: tuple[CandidateProblemRegion, ...],
    *,
    page_number: int | None = None,
    id_prefix: str = "",
) -> tuple[UnifiedCandidateItem, ...]:
    items: list[UnifiedCandidateItem] = []
    for r in regions:
        cid = f"{id_prefix}{r.region_id}" if id_prefix else r.region_id
        page_note = f" · Trang {page_number}" if page_number is not None else ""
        items.append(
            UnifiedCandidateItem(
                candidate_id=cid,
                label=f"{r.label}{page_note}",
                preview_snippet=(
                    "Vùng đề kèm hình minh họa" if r.has_figure else "Vùng văn bản bài toán"
                ),
                preview_data_url=r.preview_data_url,
                page_number=page_number,
                has_figure=r.has_figure,
                problem_text=None,
                source_bbox=r.normalized_bbox,
            )
        )
    return tuple(items)


def _finalize_text_problem(
    chosen: TextProblemCandidate,
    directive: UserComposerDirective,
    *,
    source_kind: Literal["image", "pdf", "docx"],
    provenance_base: dict[str, Any],
    metrics_base: dict[str, Any],
    t0: float,
) -> UnifiedPrepareOutcome:
    merged = merge_supplemental_text(chosen.problem_text, directive)
    elapsed_ms = round((time.perf_counter() - t0) * 1000.0, 2)
    metrics = {**metrics_base, "processing_ms": elapsed_ms}
    prov = {
        **provenance_base,
        "selected_candidate_id": chosen.candidate_id,
        "selected_page": chosen.page_number or provenance_base.get("selected_page"),
        "has_associated_figure": chosen.has_figure or bool(provenance_base.get("has_associated_figure")),
        "file_extracted_text_length": len(chosen.problem_text),
        "supplemental_merged": bool(directive.supplemental_text) and merged != chosen.problem_text,
        "user_directive_applied": bool(
            directive.target_page
            or directive.target_problem_number
            or directive.target_problem_index
            or directive.topic_keywords
            or directive.supplemental_text
        ),
    }

    if len(merged.strip()) < 10:
        return UnifiedPrepareOutcome(
            status="rejected",
            source_kind=source_kind,
            learner_message="Nội dung trích xuất từ tệp quá ngắn hoặc chưa có lời đề bài toán.",
            reason_code="EMPTY_PROBLEM_CONTENT",
            provenance=prov,
            metrics=metrics,
        )

    if detect_domain(merged) != DOMAIN_HINH_HOC:
        return UnifiedPrepareOutcome(
            status="rejected",
            source_kind=source_kind,
            problem_text=merged,
            learner_message=REJECTION_MESSAGES["UNSUPPORTED_PROBLEM"],
            reason_code="UNSUPPORTED_PROBLEM",
            provenance=prov,
            metrics=metrics,
        )

    return UnifiedPrepareOutcome(
        status="ready",
        source_kind=source_kind,
        problem_text=merged,
        provenance=prov,
        metrics=metrics,
    )


async def _process_normalized_visual_page(
    norm_img: NormalizedImage,
    directive: UserComposerDirective,
    *,
    source_kind: Literal["image", "pdf", "docx"],
    raw_input_bytes: int,
    api_key: str | None,
    cache_version: str | None,
    selected_candidate_id: str | None,
    page_number: int | None,
    extra_provenance: dict[str, Any],
    t0: float,
) -> UnifiedPrepareOutcome:
    """Xử lý một trang ảnh chuẩn hóa qua phát hiện vùng CV nhẹ -> VLM khi cần -> hậu kiểm."""
    region_sel_id: str | None = None
    id_prefix = f"p{page_number}:" if page_number is not None else ""
    if selected_candidate_id:
        if id_prefix and selected_candidate_id.startswith(id_prefix):
            region_sel_id = selected_candidate_id[len(id_prefix) :]
        elif selected_candidate_id.startswith("region-"):
            region_sel_id = selected_candidate_id

    region_res: RegionDetectionResult = detect_problem_regions(
        norm_img,
        target_problem_index=directive.target_problem_index,
        selected_region_id=region_sel_id,
    )

    uncropped_bytes = len(region_res.full_image.data)
    prov_common: dict[str, Any] = {
        **extra_provenance,
        "selected_page": page_number,
        "desk_trimmed": region_res.desk_trimmed,
        "deskew_applied": region_res.deskew_applied,
        "skew_angle_deg": region_res.skew_angle_deg,
        "enhanced_low_light": region_res.quality.enhanced_low_light,
        "is_low_light": region_res.quality.is_low_light,
        "used_crop": region_res.used_crop,
        "used_fallback_full_image": region_res.used_fallback_full_image,
        "has_associated_figure": region_res.has_associated_figure,
        "completeness_confidence": region_res.completeness_confidence,
        "selected_bbox": region_res.selected_bbox.normalized(
            region_res.full_image.width, region_res.full_image.height
        ),
        "candidate_region_count": len(region_res.candidates),
    }

    # 1. Ảnh trắng trơn / tối đen hoàn toàn -> từ chối ngay, 0 lượt gọi AI!
    if region_res.quality.is_blank_or_unreadable:
        return UnifiedPrepareOutcome(
            status="rejected",
            source_kind=source_kind,
            learner_message=REJECTION_MESSAGES["IMAGE_NOT_READABLE"],
            reason_code="IMAGE_NOT_READABLE",
            provenance=prov_common,
            metrics={
                "vlm_calls": 0,
                "used_vlm": False,
                "raw_input_bytes": raw_input_bytes,
                "vlm_payload_bytes": 0,
                "uncropped_baseline_bytes": uncropped_bytes,
                "processing_ms": round((time.perf_counter() - t0) * 1000.0, 2),
            },
        )

    # 2. Có nhiều vùng bài toán tách biệt rõ và chưa có chỉ dẫn chọn bài -> chạm chọn 1 bước, 0 lượt gọi VLM!
    if region_res.ambiguous_multi_problem and len(region_res.candidates) >= 2 and not selected_candidate_id:
        msg = (
            f"Không tìm thấy vùng Bài {directive.target_problem_number} trong ảnh. Em chạm chọn vùng bài muốn dựng nhé."
            if directive.target_problem_number is not None
            else f"Ảnh có {len(region_res.candidates)} vùng bài toán độc lập. Em chạm chọn vùng bài muốn dựng nhé."
        )
        return UnifiedPrepareOutcome(
            status="needs_selection",
            source_kind=source_kind,
            learner_message=msg,
            reason_code="MULTIPLE_PROBLEMS_DETECTED",
            candidates=_region_candidates_to_items(
                region_res.candidates, page_number=page_number, id_prefix=id_prefix
            ),
            provenance=prov_common,
            metrics={
                "vlm_calls": 0,
                "used_vlm": False,
                "raw_input_bytes": raw_input_bytes,
                "vlm_payload_bytes": 0,
                "uncropped_baseline_bytes": uncropped_bytes,
                "processing_ms": round((time.perf_counter() - t0) * 1000.0, 2),
            },
        )

    # 3. Gọi VLM trên ảnh vùng đề đã chuẩn bị (có fallback tự động 1 lần về ảnh gốc nếu vùng crop bị thiếu).
    vkey = _require_vision_key(api_key)
    vlm_calls = 0
    vlm_bytes = 0
    used_fallback = region_res.used_fallback_full_image
    used_crop = region_res.used_crop

    ext_res: ExtractionResult = await extract_problem_from_image(
        region_res.prepared_image, vkey, cache_version=cache_version
    )
    if not ext_res.cached:
        vlm_calls += 1
    vlm_bytes += len(region_res.prepared_image.data)

    # Nếu vùng crop tự động bị VLM báo mất vùng (`missing_regions`) hoặc không đọc được, thử lại đúng 1 lần trên ảnh đầy đủ (§13, §14).
    need_full_retry = (
        used_crop
        and not used_fallback
        and region_res.prepared_image.sha256 != region_res.full_image.sha256
        and (
            bool(ext_res.extraction.missing_regions)
            or ext_res.assessment.rejection_code in ("IMAGE_NOT_READABLE", "MISSING_PROBLEM_TEXT")
        )
    )
    if need_full_retry:
        ext_res = await extract_problem_from_image(
            region_res.full_image, vkey, cache_version=cache_version
        )
        if not ext_res.cached:
            vlm_calls += 1
        vlm_bytes += len(region_res.full_image.data)
        used_fallback = True
        used_crop = region_res.desk_trimmed

    prov_common["used_crop"] = used_crop
    prov_common["used_fallback_full_image"] = used_fallback
    prov_common["vision_cached"] = ext_res.cached
    prov_common["has_associated_figure"] = (
        prov_common["has_associated_figure"] or ext_res.extraction.has_diagram
    )
    prov_common["extraction_confidence"] = ext_res.extraction.confidence
    prov_common["extracted_named_points"] = list(ext_res.extraction.named_points)
    prov_common["extracted_named_lines"] = list(ext_res.extraction.named_lines)
    prov_common["extracted_named_planes"] = list(ext_res.extraction.named_planes)
    prov_common["extracted_named_solids"] = list(ext_res.extraction.named_solids)
    prov_common["diagram_observations"] = list(ext_res.extraction.diagram_observations)
    prov_common["text_diagram_conflicts"] = list(ext_res.extraction.text_diagram_conflicts)

    metrics_now = {
        "vlm_calls": vlm_calls,
        "used_vlm": True,
        "raw_input_bytes": raw_input_bytes,
        "vlm_payload_bytes": vlm_bytes,
        "uncropped_baseline_bytes": uncropped_bytes,
    }

    assessment = ext_res.assessment
    raw_uncertain = tuple(t.model_dump() for t in ext_res.extraction.uncertain_tokens)
    raw_missing = tuple(ext_res.extraction.missing_regions)
    raw_flags = tuple(
        FLAG_MESSAGES[f]
        for f in (
            ("UNCERTAIN_TOKENS",) if ext_res.extraction.uncertain_tokens else ()
        )
        + (("MISSING_REGIONS",) if ext_res.extraction.missing_regions else ())
        + (("LOW_CONFIDENCE",) if ext_res.extraction.confidence < 0.7 else ())
        if f in FLAG_MESSAGES
    )

    # 4. Trường hợp ảnh chỉ có hình vẽ (`MISSING_PROBLEM_TEXT`) nhưng học sinh đã gõ đầy đủ lời đề trong ô nhập (§4)!
    if assessment.status == "rejected":
        if assessment.rejection_code == "MISSING_PROBLEM_TEXT" and directive.is_standalone_problem:
            return UnifiedPrepareOutcome(
                status="ready",
                source_kind=source_kind,
                problem_text=directive.raw_text,
                provenance={
                    **prov_common,
                    "diagram_paired_with_user_text": True,
                    "user_directive_applied": True,
                },
                metrics={
                    **metrics_now,
                    "processing_ms": round((time.perf_counter() - t0) * 1000.0, 2),
                },
            )
        rej_code = assessment.rejection_code or "IMAGE_NOT_READABLE"
        return UnifiedPrepareOutcome(
            status="rejected",
            source_kind=source_kind,
            problem_text=assessment.problem_text,
            learner_message=REJECTION_MESSAGES.get(rej_code, REJECTION_MESSAGES["IMAGE_NOT_READABLE"]),
            reason_code=rej_code,
            flag_messages=raw_flags,
            uncertain_tokens=raw_uncertain,
            missing_regions=raw_missing,
            provenance=prov_common,
            metrics={
                **metrics_now,
                "processing_ms": round((time.perf_counter() - t0) * 1000.0, 2),
            },
        )

    # 5. Kiểm tra xem văn bản VLM chép ra có chứa nhiều bài toán viết sát nhau (`Bài 1: ... Bài 2: ...`) không.
    split_cands = split_text_into_problems(
        assessment.problem_text,
        page_number=page_number,
        has_figure=prov_common["has_associated_figure"],
    )
    if len(split_cands) >= 2:
        chosen_txt, pool_txt, ambig_msg = select_text_candidate(
            split_cands, directive, selected_candidate_id
        )
        if chosen_txt is None:
            return UnifiedPrepareOutcome(
                status="needs_selection",
                source_kind=source_kind,
                learner_message=ambig_msg,
                reason_code="MULTIPLE_PROBLEMS_DETECTED",
                candidates=_text_candidates_to_items(
                    pool_txt, parent_bbox=prov_common.get("selected_bbox")
                ),
                provenance=prov_common,
                metrics={
                    **metrics_now,
                    "processing_ms": round((time.perf_counter() - t0) * 1000.0, 2),
                },
            )
        target_text = merge_supplemental_text(chosen_txt.problem_text, directive)
    else:
        target_text = merge_supplemental_text(assessment.problem_text, directive)

    prov_common["supplemental_merged"] = (
        bool(directive.supplemental_text) and target_text != assessment.problem_text
    )
    prov_common["user_directive_applied"] = bool(
        directive.target_page
        or directive.target_problem_number
        or directive.target_problem_index
        or directive.topic_keywords
        or directive.supplemental_text
    )

    # 6. Nếu có ký hiệu không chắc chắn hoặc cờ cần người học xác nhận (§16, §17), chỉ hiện khung xác nhận gọn cho văn bản đó.
    if assessment.requires_confirmation:
        flags = [FLAG_MESSAGES[f] for f in assessment.review_flags if f in FLAG_MESSAGES]
        return UnifiedPrepareOutcome(
            status="needs_confirmation",
            source_kind=source_kind,
            problem_text=target_text,
            learner_message=flags[0] if flags else "Có ký hiệu đọc chưa chắc chắn — em kiểm tra nhanh trước khi dựng.",
            reason_code="EXTRACTION_NEEDS_CONFIRMATION",
            flag_messages=tuple(flags),
            uncertain_tokens=tuple(t.model_dump() for t in ext_res.extraction.uncertain_tokens),
            missing_regions=tuple(ext_res.extraction.missing_regions),
            provenance=prov_common,
            metrics={
                **metrics_now,
                "processing_ms": round((time.perf_counter() - t0) * 1000.0, 2),
            },
        )

    return UnifiedPrepareOutcome(
        status="ready",
        source_kind=source_kind,
        problem_text=target_text,
        provenance=prov_common,
        metrics={
            **metrics_now,
            "processing_ms": round((time.perf_counter() - t0) * 1000.0, 2),
        },
    )


async def _prepare_single_attachment(
    *,
    content: str,
    declared_mime: str | None = None,
    filename: str | None = None,
    user_text: str | None = None,
    selected_candidate_id: str | None = None,
    api_key: str | None = None,
    cache_version: str | None = None,
) -> UnifiedPrepareOutcome:
    """Xử lý chuẩn bị trên một tệp đính kèm đơn lẻ."""
    t0 = time.perf_counter()
    raw = decode_attachment_base64(content)
    raw_len = len(raw)
    kind, actual_mime = sniff_input_file_kind(raw, declared_mime, filename)
    directive = parse_user_composer_instruction(user_text)

    # Nếu ứng viên đã có sẵn `problem_text` từ bước tách văn bản trước đó, vẫn chạy lại trên tệp để xác thực tất định
    # theo `selected_candidate_id` (không tin mù dữ liệu client sửa, 0 lượt gọi VLM cho PDF text / DOCX).

    # ── NHÁNH A: ẢNH ĐỀ BÀI ──────────────────────────────────────────────────
    if kind == "image":
        try:
            norm = normalize_image(raw, actual_mime)
        except ImageRejected as err:
            raise InputPrepareRejected(err.code, str(err)) from err
        return await _process_normalized_visual_page(
            norm,
            directive,
            source_kind="image",
            raw_input_bytes=raw_len,
            api_key=api_key,
            cache_version=cache_version,
            selected_candidate_id=selected_candidate_id,
            page_number=None,
            extra_provenance={"source_mime": actual_mime},
            t0=t0,
        )

    # ── NHÁNH B & C: PDF (TEXT LAYER HOẶC SCAN) ──────────────────────────────
    if kind == "pdf":
        # Kiểm tra nếu người dùng vừa chọn 1 trang scan từ danh sách gợi ý (`pdf-scan-page-K` hoặc `pK:region-M`).
        chosen_scan_page: int | None = directive.target_page
        if selected_candidate_id:
            if selected_candidate_id.startswith("pdf-scan-page-"):
                try:
                    chosen_scan_page = int(selected_candidate_id.rsplit("-", 1)[-1])
                except ValueError:
                    chosen_scan_page = directive.target_page
            elif selected_candidate_id.startswith("p") and ":" in selected_candidate_id:
                p_head = selected_candidate_id.split(":", 1)[0]
                if p_head[1:].isdigit():
                    chosen_scan_page = int(p_head[1:])

        pdf_info = extract_pdf_structured(raw, target_page=chosen_scan_page)
        text_pages = [p for p in pdf_info.pages if p.kind == "text"]
        scan_pages = [p for p in pdf_info.pages if p.kind == "scanned"]

        all_text_candidates: list[TextProblemCandidate] = []
        for tp in text_pages:
            all_text_candidates.extend(
                split_text_into_problems(tp.text, page_number=tp.page_number, has_figure=tp.has_figure)
            )

        geo_text_candidates = [c for c in all_text_candidates if c.is_geometry]

        # Ưu tiên tuyệt đối text layer khi có bài hình học đọc được (0 lượt gọi VLM, 0 trang rasterize!).
        if geo_text_candidates or (all_text_candidates and not scan_pages):
            chosen_txt, pool_txt, ambig_msg = select_text_candidate(
                all_text_candidates, directive, selected_candidate_id
            )
            prov_pdf = {
                "source_mime": actual_mime,
                "page_count": pdf_info.page_count,
                "inspected_pages": list(pdf_info.inspected_pages),
                "rasterized_pages": [],
                "used_crop": False,
                "used_fallback_full_image": False,
            }
            metrics_pdf = {
                "vlm_calls": 0,
                "used_vlm": False,
                "raw_input_bytes": raw_len,
                "vlm_payload_bytes": 0,
                "uncropped_baseline_bytes": 0,
            }
            if chosen_txt is None:
                return UnifiedPrepareOutcome(
                    status="needs_selection",
                    source_kind="pdf",
                    learner_message=ambig_msg,
                    reason_code="MULTIPLE_PROBLEMS_DETECTED",
                    candidates=_text_candidates_to_items(pool_txt),
                    provenance=prov_pdf,
                    metrics={
                        **metrics_pdf,
                        "processing_ms": round((time.perf_counter() - t0) * 1000.0, 2),
                    },
                )
            return _finalize_text_problem(
                chosen_txt,
                directive,
                source_kind="pdf",
                provenance_base=prov_pdf,
                metrics_base=metrics_pdf,
                t0=t0,
            )

        # Trang scan: chỉ rasterize đúng trang cần thiết (§10.B).
        if not scan_pages:
            return UnifiedPrepareOutcome(
                status="rejected",
                source_kind="pdf",
                learner_message="Tệp PDF trống hoặc không có nội dung bài toán hình học đọc được.",
                reason_code="EMPTY_PROBLEM_CONTENT",
                provenance={
                    "source_mime": actual_mime,
                    "page_count": pdf_info.page_count,
                    "rasterized_pages": [],
                },
                metrics={
                    "vlm_calls": 0,
                    "used_vlm": False,
                    "raw_input_bytes": raw_len,
                    "vlm_payload_bytes": 0,
                    "uncropped_baseline_bytes": 0,
                    "processing_ms": round((time.perf_counter() - t0) * 1000.0, 2),
                },
            )

        # Nếu có >= 2 trang scan mà chưa chỉ định trang, yêu cầu chọn trang để không gửi toàn bộ PDF cho VLM (§10.B).
        if len(scan_pages) >= 2 and chosen_scan_page is None:
            page_items: list[UnifiedCandidateItem] = []
            for sp in scan_pages[:12]:
                page_items.append(
                    UnifiedCandidateItem(
                        candidate_id=f"pdf-scan-page-{sp.page_number}",
                        label=f"Trang {sp.page_number} (bản scan)",
                        preview_snippet="Chạm để đọc và trích xuất đề bài ở trang này",
                        preview_data_url=None,
                        page_number=sp.page_number,
                        has_figure=True,
                        problem_text=None,
                    )
                )
            return UnifiedPrepareOutcome(
                status="needs_selection",
                source_kind="pdf",
                learner_message=(
                    f"Tệp PDF dạng scan có {len(scan_pages)} trang nội dung. "
                    "Em chạm chọn trang chứa đề bài cần dựng (hoặc gõ 'trang X' vào ô nhập) nhé."
                ),
                reason_code="MULTIPLE_SCANNED_PAGES",
                candidates=tuple(page_items),
                provenance={
                    "source_mime": actual_mime,
                    "page_count": pdf_info.page_count,
                    "rasterized_pages": [],
                },
                metrics={
                    "vlm_calls": 0,
                    "used_vlm": False,
                    "raw_input_bytes": raw_len,
                    "vlm_payload_bytes": 0,
                    "uncropped_baseline_bytes": 0,
                    "processing_ms": round((time.perf_counter() - t0) * 1000.0, 2),
                },
            )

        target_sp = scan_pages[0]
        page_img = render_pdf_page_normalized(raw, target_sp.page_number)
        return await _process_normalized_visual_page(
            page_img,
            directive,
            source_kind="pdf",
            raw_input_bytes=raw_len,
            api_key=api_key,
            cache_version=cache_version,
            selected_candidate_id=selected_candidate_id,
            page_number=target_sp.page_number,
            extra_provenance={
                "source_mime": actual_mime,
                "page_count": pdf_info.page_count,
                "rasterized_pages": [target_sp.page_number],
            },
            t0=t0,
        )

    # ── NHÁNH D: DOCX (PARAGRAPH + TABLE + OMML + EMBEDDED MEDIA) ────────────
    docx_res = extract_docx_structured(raw)

    if docx_res.has_unreadable_ole_equation and docx_res.formula_count == 0:
        return UnifiedPrepareOutcome(
            status="rejected",
            source_kind="docx",
            learner_message=(
                "Tệp Word chứa công thức nhị phân cũ (MathType/OLE) không thể đọc chính xác các ký hiệu. "
                "Em hãy xuất tệp sang PDF hoặc chụp ảnh vùng đề để tránh mất dữ kiện toán học."
            ),
            reason_code="DOCX_UNREADABLE_EQUATION",
            provenance={
                "source_mime": actual_mime,
                "formula_count": docx_res.formula_count,
                "embedded_figure_count": len(docx_res.embedded_figures),
            },
            metrics={
                "vlm_calls": 0,
                "used_vlm": False,
                "raw_input_bytes": raw_len,
                "vlm_payload_bytes": 0,
                "uncropped_baseline_bytes": 0,
                "processing_ms": round((time.perf_counter() - t0) * 1000.0, 2),
            },
        )

    # Trường hợp DOCX chỉ dán ảnh chụp đề (không có chữ hoặc chữ quá ngắn < 10 ký tự).
    if len(docx_res.full_text.strip()) < 10 and docx_res.embedded_figures:
        first_fig = docx_res.embedded_figures[0]
        try:
            fig_norm = normalize_image(first_fig.raw_bytes, None)
        except ImageRejected as err:
            raise InputPrepareRejected(err.code, str(err)) from err
        return await _process_normalized_visual_page(
            fig_norm,
            directive,
            source_kind="docx",
            raw_input_bytes=raw_len,
            api_key=api_key,
            cache_version=cache_version,
            selected_candidate_id=selected_candidate_id,
            page_number=None,
            extra_provenance={
                "source_mime": actual_mime,
                "embedded_figure_count": len(docx_res.embedded_figures),
                "docx_image_fallback": True,
            },
            t0=t0,
        )

    if not docx_res.full_text.strip():
        return UnifiedPrepareOutcome(
            status="rejected",
            source_kind="docx",
            learner_message="Tệp .docx không có nội dung văn bản bài toán nào đọc được.",
            reason_code="EMPTY_PROBLEM_CONTENT",
            provenance={"source_mime": actual_mime},
            metrics={
                "vlm_calls": 0,
                "used_vlm": False,
                "raw_input_bytes": raw_len,
                "vlm_payload_bytes": 0,
                "uncropped_baseline_bytes": 0,
                "processing_ms": round((time.perf_counter() - t0) * 1000.0, 2),
            },
        )

    has_docx_fig = len(docx_res.embedded_figures) > 0
    docx_candidates = split_text_into_problems(
        docx_res.full_text,
        page_number=None,
        has_figure=has_docx_fig,
    )
    chosen_docx, pool_docx, ambig_docx = select_text_candidate(
        docx_candidates, directive, selected_candidate_id
    )
    prov_docx = {
        "source_mime": actual_mime,
        "formula_count": docx_res.formula_count,
        "embedded_figure_count": len(docx_res.embedded_figures),
        "has_associated_figure": has_docx_fig,
        "used_crop": False,
        "used_fallback_full_image": False,
    }
    metrics_docx = {
        "vlm_calls": 0,
        "used_vlm": False,
        "raw_input_bytes": raw_len,
        "vlm_payload_bytes": 0,
        "uncropped_baseline_bytes": 0,
    }
    if chosen_docx is None:
        return UnifiedPrepareOutcome(
            status="needs_selection",
            source_kind="docx",
            learner_message=ambig_docx,
            reason_code="MULTIPLE_PROBLEMS_DETECTED",
            candidates=_text_candidates_to_items(pool_docx),
            provenance=prov_docx,
            metrics={
                **metrics_docx,
                "processing_ms": round((time.perf_counter() - t0) * 1000.0, 2),
            },
        )

    return _finalize_text_problem(
        chosen_docx,
        directive,
        source_kind="docx",
        provenance_base=prov_docx,
        metrics_base=metrics_docx,
        t0=t0,
    )


_EXPLICIT_PROBLEM_HEADER_RE = re.compile(
    r"^\s*(?:bài(?:\s+toán)?|câu|ví\s+dụ|problem)\s*(\d+|[ivx]+)\b[:.)\s-]*",
    re.IGNORECASE,
)
_SOLID_OPENING_RE = re.compile(
    r"\bcho\s+(?:hình\s+chóp|khối\s+chóp|tứ\s+diện|khối\s+tứ\s+diện|hình\s+lăng\s+trụ|khối\s+lăng\s+trụ|"
    r"hình\s+hộp|khối\s+hộp|hình\s+lập\s+phương|khối\s+lập\s+phương|hình\s+nón|khối\s+nón|"
    r"hình\s+trụ|khối\s+trụ|mặt\s+cầu|khối\s+cầu|tam\s+giác|hình\s+vuông|hình\s+chữ\s+nhật|hình\s+thang|hình\s+bình\s+hành)\b",
    re.IGNORECASE,
)
_QUESTION_GOAL_RE = re.compile(
    r"(?:\b(?:tính|xác\s+định|chứng\s+minh|tìm|hỏi|dựng\s+thiết\s+diện|tính\s+thể\s+tích|"
    r"tính\s+khoảng\s+cách|tính\s+góc|tính\s+diện\s+tích|tính\s+bán\s+kính|tỉ\s+số\s+thể\s+tích)\b|\?)",
    re.IGNORECASE,
)
_CONTINUATION_GEOMETRY_CUE_RE = re.compile(
    r"\b(?:tính|chứng\s+minh|xác\s+định|tìm|khoảng\s+cách|thể\s+tích|góc\s+giữa|diện\s+tích|bán\s+kính|"
    r"trung\s+điểm|trọng\s+tâm|hình\s+chiếu|vuông\s+góc|song\s+song|mặt\s+phẳng|đường\s+thẳng|"
    r"cạnh\s+bên|cạnh\s+đáy|thiết\s+diện|giao\s+tuyến|giao\s+điểm)\b",
    re.IGNORECASE,
)
_NON_GEOMETRY_DOMAIN_CUE_RE = re.compile(
    r"\b(?:mảng|thuật\s+toán|quy\s+hoạch\s+động|cây\s+nhị\s+phân|đồ\s+thị\s+có\s+hướng|"
    r"phản\s+ứng\s+hóa\s+học|điện\s+trở|dao\s+động\s+điều\s+hòa)\b",
    re.IGNORECASE,
)


def _norm_compare_line(s: str) -> str:
    return re.sub(r"[\s,.;:!?-]+", " ", s.strip().lower()).strip()


def _split_clauses_or_lines(text: str) -> list[str]:
    lines: list[str] = []
    for raw_line in text.splitlines():
        cleaned = raw_line.strip()
        if not cleaned:
            continue
        parts = [p.strip() for p in re.split(r"(?<=[.?!])\s+", cleaned) if p.strip()]
        lines.extend(parts if parts else [cleaned])
    return lines


def _segments_have_overlap(seg_a: str, seg_b: str) -> bool:
    na = _norm_compare_line(seg_a)
    nb = _norm_compare_line(seg_b)
    if not na or not nb:
        return False
    if len(na) >= 12 and (na in nb or nb in na):
        return True
    clauses_a = [_norm_compare_line(c) for c in _split_clauses_or_lines(seg_a) if len(_norm_compare_line(c)) >= 10]
    clauses_b = [_norm_compare_line(c) for c in _split_clauses_or_lines(seg_b) if len(_norm_compare_line(c)) >= 10]
    return bool(set(clauses_a) & set(clauses_b))


def merge_overlapping_problem_segments(segments: Sequence[str]) -> tuple[str, bool]:
    """Ghép các đoạn đề từ nhiều ảnh theo đúng thứ tự, khử các dòng/mệnh đề trùng lặp ở ranh giới."""
    cleaned_segs = [s.strip() for s in segments if s and s.strip()]
    if not cleaned_segs:
        return "", False
    if len(cleaned_segs) == 1:
        return cleaned_segs[0], False

    deduplicated = False
    acc_clauses: list[str] = []
    acc_norms: list[str] = []

    for seg in cleaned_segs:
        seg_norm = _norm_compare_line(seg)
        joined_acc_norm = " ".join(acc_norms)
        if acc_norms and seg_norm and seg_norm in joined_acc_norm:
            deduplicated = True
            continue
        if acc_norms and joined_acc_norm and joined_acc_norm in seg_norm:
            deduplicated = True
            acc_clauses = _split_clauses_or_lines(seg)
            acc_norms = [_norm_compare_line(c) for c in acc_clauses]
            continue

        seg_clauses = _split_clauses_or_lines(seg)
        seg_clause_norms = [_norm_compare_line(c) for c in seg_clauses]

        # Kiểm tra khớp hậu tố của acc với tiền tố của seg.
        overlap_k = 0
        max_k = min(len(acc_norms), len(seg_clause_norms))
        for k in range(max_k, 0, -1):
            if acc_norms[-k:] == seg_clause_norms[:k]:
                overlap_k = k
                break

        if overlap_k > 0:
            deduplicated = True
            for c, cn in zip(seg_clauses[overlap_k:], seg_clause_norms[overlap_k:]):
                if cn and cn not in acc_norms:
                    acc_clauses.append(c)
                    acc_norms.append(cn)
        else:
            for c, cn in zip(seg_clauses, seg_clause_norms):
                if cn and len(cn) >= 12 and cn in acc_norms:
                    deduplicated = True
                    continue
                acc_clauses.append(c)
                acc_norms.append(cn)

    return "\n".join(acc_clauses).strip(), deduplicated


def _has_problem_question_or_goal(text: str) -> bool:
    return bool(_QUESTION_GOAL_RE.search(text or ""))


def _is_complete_standalone_problem(text: str) -> bool:
    if not text or len(text.strip()) < 20:
        return False
    return bool(_SOLID_OPENING_RE.search(text)) and _has_problem_question_or_goal(text)


def _extract_problem_header_label(text: str, *, fallback_index: int, filename: str | None = None) -> str:
    m = _EXPLICIT_PROBLEM_HEADER_RE.match(text or "")
    suffix = f" ({filename})" if filename else ""
    if m:
        raw_head = m.group(0).strip().rstrip(":.-)")
        return f"{raw_head}{suffix}"
    return f"Bài {fallback_index}{suffix}"


@dataclass(frozen=True)
class _TextSegmentUnit:
    attachment_id: str
    source_attachment_ids: tuple[str, ...]
    order_index: int
    filename: str | None
    source_kind: Literal["image", "pdf", "docx"]
    problem_text: str
    has_figure: bool
    needs_confirmation: bool
    flag_messages: tuple[str, ...]
    uncertain_tokens: tuple[dict[str, Any], ...]
    missing_regions: tuple[str, ...]
    provenance: dict[str, Any]


def _are_independent_problem_units(units: Sequence[_TextSegmentUnit]) -> bool:
    """Phân định nhiều ảnh là các bài độc lập (§10.3) hay các phần của cùng 1 bài (§10.1)."""
    if len(units) < 2:
        return False

    # Nếu bất kỳ cặp đoạn nào trùng lặp một phần văn bản -> chụp chồng lấn của cùng 1 bài (kể cả khi bị đảo thứ tự).
    for i in range(len(units)):
        for j in range(i + 1, len(units)):
            if _segments_have_overlap(units[i].problem_text, units[j].problem_text):
                return False

    # Nếu các đoạn mở đầu bằng nhãn Bài/Câu/Ví dụ tường minh có số hiệu khác nhau.
    explicit_nums: list[str] = []
    for u in units:
        m_curr = _EXPLICIT_PROBLEM_HEADER_RE.match(u.problem_text)
        if m_curr:
            explicit_nums.append(m_curr.group(1).lower())
    if len(set(explicit_nums)) >= 2:
        return True
    if explicit_nums and len(explicit_nums) < len(units):
        # Nếu một đoạn có nhãn Bài X còn đoạn kia cũng là một bài hoàn chỉnh độc lập -> các bài độc lập.
        if sum(1 for u in units if _is_complete_standalone_problem(u.problem_text)) >= 2:
            return True

    # Nếu có >= 2 đoạn mà mỗi đoạn đều tự giới thiệu khối hình ("Cho hình ...") VÀ tự có câu hỏi ("Tính...") -> các bài độc lập.
    standalone_count = sum(1 for u in units if _is_complete_standalone_problem(u.problem_text))
    if standalone_count >= 2:
        return True

    return False


_PURE_QUESTION_START_RE = re.compile(
    r"^\s*(?:[a-d]\s*[).:-]\s*)?(?:tính|xác\s+định|chứng\s+minh|tìm|hỏi|dựng\s+thiết\s+diện)\b",
    re.IGNORECASE,
)


def _segment_semantic_role(text: str) -> int:
    """Xác định vai trò ngữ nghĩa của mảnh đề thuộc cùng một bài toán:
    - `0`: Mở đầu đề bài (`Cho hình chóp...`, `Cho lăng trụ...`, `Bài 1: Cho...`).
    - `1`: Giả thiết tiếp nối / dựng điểm trung gian (`Gọi M là trung điểm...`, `Biết cạnh bên...`).
    - `2`: Phần câu hỏi / yêu cầu kết thúc (`Tính thể tích...`, `a) Tính...`, `b) Tính khoảng cách...`).
    """
    cleaned = (text or "").strip()
    if _SOLID_OPENING_RE.search(cleaned):
        return 0
    if _PURE_QUESTION_START_RE.match(cleaned):
        return 2
    if _has_problem_question_or_goal(cleaned) and len(_split_clauses_or_lines(cleaned)) <= 1:
        return 2
    return 1


def _has_forward_boundary_overlap(first_text: str, second_text: str) -> bool:
    """Kiểm tra hậu tố của `first_text` có trùng với tiền tố của `second_text` hay không."""
    c1 = [_norm_compare_line(c) for c in _split_clauses_or_lines(first_text) if _norm_compare_line(c)]
    c2 = [_norm_compare_line(c) for c in _split_clauses_or_lines(second_text) if _norm_compare_line(c)]
    if not c1 or not c2:
        return False
    max_k = min(len(c1), len(c2))
    for k in range(max_k, 0, -1):
        if c1[-k:] == c2[:k] and any(len(tok) >= 10 for tok in c1[-k:]):
            return True
    return False


def _order_same_problem_units(
    units: Sequence[_TextSegmentUnit],
) -> tuple[list[_TextSegmentUnit], bool]:
    """Sắp xếp các mảnh của cùng 1 bài toán theo vai trò ngữ nghĩa + chồng lấn biên + `order_index` (§6.F)."""
    if len(units) <= 1:
        return list(units), False

    initial = list(units)
    # 1. Sắp theo (vai trò ngữ nghĩa 0 -> 1 -> 2, order_index).
    ordered = sorted(
        initial,
        key=lambda u: (_segment_semantic_role(u.problem_text), u.order_index),
    )

    # 2. Nếu hai mảnh liền kề có cùng vai trò nhưng mảnh sau có hậu tố khớp tiền tố mảnh trước (chụp chồng lấn ngược),
    # đảo cặp đó để câu nối khớp đúng chiều.
    n = len(ordered)
    for i in range(n - 1):
        a, b = ordered[i], ordered[i + 1]
        if (
            _segment_semantic_role(a.problem_text) == _segment_semantic_role(b.problem_text)
            and not _has_forward_boundary_overlap(a.problem_text, b.problem_text)
            and _has_forward_boundary_overlap(b.problem_text, a.problem_text)
        ):
            ordered[i], ordered[i + 1] = b, a

    reordered = [u.attachment_id for u in ordered] != [u.attachment_id for u in initial]
    return ordered, reordered


_TEXT_POINT_TOKEN_RE = re.compile(r"\b([A-Z][0-9']?)\b")


def _extract_point_labels_from_text(text: str) -> list[str]:
    """Trích xuất tập nhãn điểm viết hoa (vd: `S`, `A`, `B`, `C`, `D`, `A'`, `M`, `H`, `O`) xuất hiện trong lời đề."""
    found: list[str] = []
    # Cũng tách các cụm đỉnh nối liền như `S.ABCD`, `ABC.A'B'C'`, `(SBC)`, `SA`, `SB`
    for token in re.findall(r"[A-Z][A-Z0-9'.]*", text or ""):
        parts = [p for p in token.split(".") if p]
        for part in parts:
            for m in re.finditer(r"[A-Z][0-9']*", part):
                pt = m.group(0)
                if pt not in found:
                    found.append(pt)
    for m in _TEXT_POINT_TOKEN_RE.finditer(text or ""):
        pt = m.group(1)
        if pt not in found:
            found.append(pt)
    return found


def _build_diagram_text_link(
    final_text: str,
    text_units: Sequence[_TextSegmentUnit],
    diagram_provenances: Mapping[str, dict[str, Any]],
) -> dict[str, Any]:
    """Đối chiếu nhãn điểm, đường thẳng, mặt phẳng và quan sát từ hình vẽ với văn bản đề toán (§6.H)."""
    diag_points: list[str] = []
    diag_lines: list[str] = []
    diag_planes: list[str] = []
    diag_solids: list[str] = []
    diag_obs: list[str] = []
    diag_conflicts: list[str] = []

    all_provs = [u.provenance for u in text_units] + list(diagram_provenances.values())
    for p in all_provs:
        for pt in p.get("extracted_named_points") or ():
            s = str(pt).strip()
            if s and s not in diag_points:
                diag_points.append(s)
        for ln in p.get("extracted_named_lines") or ():
            s = str(ln).strip()
            if s and s not in diag_lines:
                diag_lines.append(s)
        for pl in p.get("extracted_named_planes") or ():
            s = str(pl).strip()
            if s and s not in diag_planes:
                diag_planes.append(s)
        for sol in p.get("extracted_named_solids") or ():
            s = str(sol).strip()
            if s and s not in diag_solids:
                diag_solids.append(s)
        for ob in p.get("diagram_observations") or ():
            s = str(ob).strip()
            if s and s not in diag_obs:
                diag_obs.append(s)
        for cf in p.get("text_diagram_conflicts") or ():
            s = str(cf).strip()
            if s and s not in diag_conflicts:
                diag_conflicts.append(s)

    text_points = _extract_point_labels_from_text(final_text)
    text_points_set = set(text_points)
    matched_points = [pt for pt in diag_points if pt in text_points_set]
    unreferenced_points = [pt for pt in diag_points if pt not in text_points_set]

    if not diag_points:
        alignment = "no_explicit_diagram_labels"
    elif len(matched_points) == len(diag_points):
        alignment = "aligned"
    elif matched_points:
        alignment = "partial"
    else:
        alignment = "disjoint"

    return {
        "text_point_labels": text_points,
        "diagram_named_points": diag_points,
        "diagram_named_lines": diag_lines,
        "diagram_named_planes": diag_planes,
        "diagram_named_solids": diag_solids,
        "matched_points_in_text": matched_points,
        "unreferenced_diagram_points": unreferenced_points,
        "diagram_observations": diag_obs,
        "text_diagram_conflicts": diag_conflicts,
        "diagram_vertex_alignment": alignment,
    }


def _stamp_single_outcome(
    outcome: UnifiedPrepareOutcome,
    *,
    attachment_id: str,
    request_id: str | None,
) -> UnifiedPrepareOutcome:
    stamped_candidates = tuple(
        replace(
            c,
            source_attachment_ids=c.source_attachment_ids or (attachment_id,),
        )
        for c in outcome.candidates
    )
    prov = dict(outcome.provenance)
    if "source_attachment_ids" not in prov:
        prov["source_attachment_ids"] = [attachment_id]
    if request_id is not None:
        prov["request_id"] = request_id
    return replace(
        outcome,
        candidates=stamped_candidates,
        provenance=prov,
        request_id=request_id,
    )


async def prepare_unified_input(
    *,
    content: str | None = None,
    declared_mime: str | None = None,
    filename: str | None = None,
    attachments: Sequence[Mapping[str, Any]] | None = None,
    request_id: str | None = None,
    user_text: str | None = None,
    selected_candidate_id: str | None = None,
    api_key: str | None = None,
    cache_version: str | None = None,
) -> UnifiedPrepareOutcome:
    """Điểm vào thống nhất cho 1 hoặc nhiều tệp đính kèm khi người học bấm "Dựng hình"."""
    t0 = time.perf_counter()

    # 1. Tương thích ngược với luồng 1 tệp truyền thống (`attachments` trống hoặc không gửi).
    if attachments is None:
        if not content:
            raise InputPrepareRejected("EMPTY_ATTACHMENT_PAYLOAD", "Thiếu dữ liệu tệp đính kèm.")
        single_out = await _prepare_single_attachment(
            content=content,
            declared_mime=declared_mime,
            filename=filename,
            user_text=user_text,
            selected_candidate_id=selected_candidate_id,
            api_key=api_key,
            cache_version=cache_version,
        )
        return _stamp_single_outcome(single_out, attachment_id="att-1", request_id=request_id)

    if len(attachments) == 0:
        if content:
            single_out = await _prepare_single_attachment(
                content=content,
                declared_mime=declared_mime,
                filename=filename,
                user_text=user_text,
                selected_candidate_id=selected_candidate_id,
                api_key=api_key,
                cache_version=cache_version,
            )
            return _stamp_single_outcome(single_out, attachment_id="att-1", request_id=request_id)
        raise InputPrepareRejected("EMPTY_ATTACHMENT_PAYLOAD", "Danh sách tệp đính kèm trống.")

    if len(attachments) > MAX_PREPARE_ATTACHMENTS:
        raise InputPrepareRejected(
            "TOO_MANY_ATTACHMENTS",
            f"Chỉ hỗ trợ tối đa {MAX_PREPARE_ATTACHMENTS} tệp đính kèm trong một lần chuẩn bị.",
        )

    # Kiểm tra trùng `attachment_id` và chuẩn hóa thứ tự `order_index`.
    seen_ids: set[str] = set()
    indexed_attachments: list[tuple[int, int, Mapping[str, Any]]] = []
    for idx, att in enumerate(attachments):
        aid = str(att.get("attachment_id") or "").strip()
        if not aid:
            raise InputPrepareRejected("INVALID_ATTACHMENT_ID", "Thiếu attachment_id cho tệp đính kèm.")
        if aid in seen_ids:
            raise InputPrepareRejected("DUPLICATE_ATTACHMENT_ID", f"Trùng lặp attachment_id: {aid}.")
        seen_ids.add(aid)
        order_idx = int(att.get("order_index", idx))
        indexed_attachments.append((order_idx, idx, att))

    indexed_attachments.sort(key=lambda item: (item[0], item[1]))
    ordered_attachments = [item[2] for item in indexed_attachments]

    # Xác thực kích thước và định dạng của toàn bộ tệp đính kèm trước khi xử lý.
    total_raw_bytes = 0
    decoded_cache: dict[str, tuple[bytes, Literal["image", "pdf", "docx"], str]] = {}
    for att in ordered_attachments:
        aid = str(att["attachment_id"]).strip()
        raw_bytes = decode_attachment_base64(str(att.get("content") or ""))
        total_raw_bytes += len(raw_bytes)
        if total_raw_bytes > MAX_TOTAL_ATTACHMENT_BYTES:
            raise InputPrepareRejected(
                "TOTAL_ATTACHMENTS_TOO_LARGE",
                "Tổng dung lượng các tệp đính kèm vượt quá giới hạn 25 MB.",
            )
        kind, actual_mime = sniff_input_file_kind(
            raw_bytes,
            att.get("mime_type"),
            att.get("filename"),
        )
        decoded_cache[aid] = (raw_bytes, kind, actual_mime)

    # Nếu chỉ có đúng 1 phần tử trong `attachments`, giữ nguyên hành vi 1 tệp kèm `source_attachment_ids`.
    if len(ordered_attachments) == 1:
        only_att = ordered_attachments[0]
        only_id = str(only_att["attachment_id"]).strip()
        inner_sel = selected_candidate_id
        if inner_sel and inner_sel.startswith(f"{only_id}:"):
            inner_sel = inner_sel[len(only_id) + 1 :]
            if inner_sel == "problem-1":
                inner_sel = None
        single_out = await _prepare_single_attachment(
            content=str(only_att.get("content") or ""),
            declared_mime=only_att.get("mime_type"),
            filename=only_att.get("filename"),
            user_text=user_text,
            selected_candidate_id=inner_sel,
            api_key=api_key,
            cache_version=cache_version,
        )
        return _stamp_single_outcome(single_out, attachment_id=only_id, request_id=request_id)

    # ── LUỒNG ĐA ẢNH / ĐA TỆP (`len(ordered_attachments) >= 2`) ───────────────
    directive = parse_user_composer_instruction(user_text)

    # Nếu `selected_candidate_id` chỉ định rõ một `attachment_id` cụ thể (`{aid}:{inner_id}`),
    # xác định xem có phải người học vừa chọn 1 bài từ danh sách `needs_selection` đa ảnh không.
    targeted_att_id: str | None = None
    targeted_inner_id: str | None = None
    if selected_candidate_id and ":" in selected_candidate_id:
        prefix, rest = selected_candidate_id.split(":", 1)
        if prefix in seen_ids:
            targeted_att_id = prefix
            targeted_inner_id = None if rest == "problem-1" else rest

    seen_image_hashes: dict[str, str] = {}
    duplicate_Target_map: dict[str, list[str]] = {}
    deduplicated_attachment_ids: list[str] = []
    diagram_only_ids: list[str] = []
    diagram_only_provenance: dict[str, dict[str, Any]] = {}
    multi_problem_candidates: list[UnifiedCandidateItem] = []
    text_units: list[_TextSegmentUnit] = []

    total_vlm_calls = 0
    total_vlm_payload_bytes = 0
    total_uncropped_bytes = 0
    any_used_vlm = False
    primary_source_kind: Literal["image", "pdf", "docx"] = decoded_cache[
        str(ordered_attachments[0]["attachment_id"]).strip()
    ][1]

    for pos, att in enumerate(ordered_attachments):
        aid = str(att["attachment_id"]).strip()
        # Nếu người học đã chọn đích danh một bài ở `targeted_att_id` khác, bỏ qua việc gọi VLM trên các ảnh bài độc lập khác.
        if targeted_att_id is not None and aid != targeted_att_id:
            continue

        raw_bytes, kind, actual_mime = decoded_cache[aid]
        if kind == "image":
            try:
                norm = normalize_image(raw_bytes, actual_mime)
            except ImageRejected as err:
                raise InputPrepareRejected(err.code, str(err)) from err
            if norm.sha256 in seen_image_hashes:
                orig_id = seen_image_hashes[norm.sha256]
                duplicate_Target_map.setdefault(orig_id, []).append(aid)
                deduplicated_attachment_ids.append(aid)
                continue
            seen_image_hashes[norm.sha256] = aid

        inner_sel_for_att = targeted_inner_id if aid == targeted_att_id else None
        out = await _prepare_single_attachment(
            content=str(att.get("content") or ""),
            declared_mime=att.get("mime_type"),
            filename=att.get("filename"),
            user_text=user_text if targeted_att_id == aid else None,
            selected_candidate_id=inner_sel_for_att,
            api_key=api_key,
            cache_version=cache_version,
        )

        m = out.metrics
        total_vlm_calls += int(m.get("vlm_calls", 0))
        total_vlm_payload_bytes += int(m.get("vlm_payload_bytes", 0))
        total_uncropped_bytes += int(m.get("uncropped_baseline_bytes", 0))
        any_used_vlm = any_used_vlm or bool(m.get("used_vlm"))

        # Phân loại kết quả từng tệp:
        if out.status == "rejected":
            # Ảnh chỉ có hình vẽ (`MISSING_PROBLEM_TEXT`): giữ lại để ghép với ảnh chữ cùng bài (§10.1, §13.5).
            if out.reason_code == "MISSING_PROBLEM_TEXT":
                diagram_only_ids.append(aid)
                diagram_only_provenance[aid] = out.provenance
                continue

            # Trường hợp mảnh đề tiếp nối (vd: chỉ chứa câu hỏi "Tính khoảng cách từ A đến (SBC)...")
            # bị bộ nhận miền đơn lẻ đánh dấu `UNSUPPORTED_PROBLEM` vì phần "Cho hình chóp..." nằm ở ảnh trước:
            cand_text = (out.problem_text or "").strip()
            if (
                out.reason_code == "UNSUPPORTED_PROBLEM"
                and len(cand_text) >= 10
                and _CONTINUATION_GEOMETRY_CUE_RE.search(cand_text)
                and not _NON_GEOMETRY_DOMAIN_CUE_RE.search(cand_text)
            ):
                ext_conf = float(out.provenance.get("extraction_confidence", 0.9))
                needs_conf = bool(
                    out.uncertain_tokens
                    or out.missing_regions
                    or ext_conf < 0.7
                )
                text_units.append(
                    _TextSegmentUnit(
                        attachment_id=aid,
                        source_attachment_ids=(aid,),
                        order_index=int(att.get("order_index", pos)),
                        filename=att.get("filename"),
                        source_kind=out.source_kind,
                        problem_text=cand_text,
                        has_figure=bool(out.provenance.get("has_associated_figure")),
                        needs_confirmation=needs_conf,
                        flag_messages=out.flag_messages,
                        uncertain_tokens=out.uncertain_tokens,
                        missing_regions=out.missing_regions,
                        provenance=out.provenance,
                    )
                )
                continue

            # Các lỗi từ chối thực sự (ảnh mờ không đọc được, ngoài miền, rỗng): fail-closed ngay!
            prov_rej = {
                **out.provenance,
                "failed_attachment_id": aid,
                "source_attachment_ids": [aid],
            }
            return replace(
                out,
                provenance=prov_rej,
                metrics={
                    "vlm_calls": total_vlm_calls,
                    "used_vlm": any_used_vlm,
                    "raw_input_bytes": total_raw_bytes,
                    "vlm_payload_bytes": total_vlm_payload_bytes,
                    "uncropped_baseline_bytes": total_uncropped_bytes,
                    "processing_ms": round((time.perf_counter() - t0) * 1000.0, 2),
                },
                request_id=request_id,
            )

        if out.status == "needs_selection":
            att_label = att.get("filename") or f"Ảnh {pos + 1}"
            for c in out.candidates:
                prefixed_id = c.candidate_id if c.candidate_id.startswith(f"{aid}:") else f"{aid}:{c.candidate_id}"
                multi_problem_candidates.append(
                    UnifiedCandidateItem(
                        candidate_id=prefixed_id,
                        label=f"{c.label} · {att_label}",
                        preview_snippet=c.preview_snippet,
                        preview_data_url=c.preview_data_url,
                        page_number=c.page_number,
                        has_figure=c.has_figure,
                        problem_text=c.problem_text,
                        source_attachment_ids=(aid,),
                        source_bbox=c.source_bbox,
                    )
                )
            continue

        # `status` là `ready` hoặc `needs_confirmation`:
        text_units.append(
            _TextSegmentUnit(
                attachment_id=aid,
                source_attachment_ids=(aid,),
                order_index=int(att.get("order_index", pos)),
                filename=att.get("filename"),
                source_kind=out.source_kind,
                problem_text=out.problem_text.strip(),
                has_figure=bool(out.provenance.get("has_associated_figure")),
                needs_confirmation=(out.status == "needs_confirmation"),
                flag_messages=out.flag_messages,
                uncertain_tokens=out.uncertain_tokens,
                missing_regions=out.missing_regions,
                provenance=out.provenance,
            )
        )

    # Gắn các `attachment_id` ảnh trùng lặp vào `source_attachment_ids` của đơn vị gốc tương ứng.
    if duplicate_Target_map:
        updated_units: list[_TextSegmentUnit] = []
        for u in text_units:
            dups = duplicate_Target_map.get(u.attachment_id, [])
            if dups:
                updated_units.append(
                    replace(u, source_attachment_ids=tuple(list(u.source_attachment_ids) + dups))
                )
            else:
                updated_units.append(u)
        text_units = updated_units

    common_metrics = {
        "vlm_calls": total_vlm_calls,
        "used_vlm": any_used_vlm,
        "raw_input_bytes": total_raw_bytes,
        "vlm_payload_bytes": total_vlm_payload_bytes,
        "uncropped_baseline_bytes": total_uncropped_bytes,
    }

    # Trường hợp 0: Không có đoạn văn bản nào mà chỉ toàn ảnh hình vẽ (`diagram_only_ids`).
    if not text_units and not multi_problem_candidates:
        if diagram_only_ids and directive.is_standalone_problem:
            return UnifiedPrepareOutcome(
                status="ready",
                source_kind=primary_source_kind,
                problem_text=directive.raw_text,
                provenance={
                    "source_attachment_ids": list(diagram_only_ids),
                    "diagram_attachment_ids": list(diagram_only_ids),
                    "has_associated_figure": True,
                    "diagram_paired_with_user_text": True,
                    "user_directive_applied": True,
                },
                metrics={
                    **common_metrics,
                    "processing_ms": round((time.perf_counter() - t0) * 1000.0, 2),
                },
                request_id=request_id,
            )
        return UnifiedPrepareOutcome(
            status="rejected",
            source_kind=primary_source_kind,
            learner_message=REJECTION_MESSAGES["MISSING_PROBLEM_TEXT"],
            reason_code="MISSING_PROBLEM_TEXT",
            provenance={
                "source_attachment_ids": list(diagram_only_ids),
                "diagram_attachment_ids": list(diagram_only_ids),
                "has_associated_figure": bool(diagram_only_ids),
            },
            metrics={
                **common_metrics,
                "processing_ms": round((time.perf_counter() - t0) * 1000.0, 2),
            },
            request_id=request_id,
        )

    # Trường hợp 1: Có ít nhất một tệp chứa nhiều bài (`multi_problem_candidates` khác rỗng).
    if multi_problem_candidates:
        combined_candidates: list[UnifiedCandidateItem] = list(multi_problem_candidates)
        for idx, u in enumerate(text_units):
            combined_candidates.append(
                UnifiedCandidateItem(
                    candidate_id=f"{u.attachment_id}:problem-1",
                    label=_extract_problem_header_label(
                        u.problem_text, fallback_index=idx + 1, filename=u.filename
                    ),
                    preview_snippet=u.problem_text[:140],
                    preview_data_url=None,
                    page_number=None,
                    has_figure=u.has_figure,
                    problem_text=u.problem_text,
                    source_attachment_ids=u.source_attachment_ids,
                )
            )
        all_sids = [str(a["attachment_id"]).strip() for a in ordered_attachments]
        return UnifiedPrepareOutcome(
            status="needs_selection",
            source_kind=primary_source_kind,
            learner_message=(
                f"Phát hiện {len(combined_candidates)} bài toán trong các ảnh đã gửi. "
                "Em chạm chọn bài muốn dựng nhé."
            ),
            reason_code="MULTIPLE_PROBLEMS_DETECTED",
            candidates=tuple(combined_candidates),
            provenance={
                "source_attachment_ids": all_sids,
                "diagram_attachment_ids": list(diagram_only_ids),
                "has_associated_figure": any(c.has_figure for c in combined_candidates) or bool(diagram_only_ids),
            },
            metrics={
                **common_metrics,
                "processing_ms": round((time.perf_counter() - t0) * 1000.0, 2),
            },
            request_id=request_id,
        )

    # Trường hợp 2: Nhiều ảnh thuộc các bài toán độc lập (§10.3).
    if targeted_att_id is None and _are_independent_problem_units(text_units):
        # Kiểm tra nếu người học đã chọn bằng `selected_candidate_id` không có prefix hoặc chỉ dẫn `Bài X` trong ô nhập:
        chosen_unit: _TextSegmentUnit | None = None
        if selected_candidate_id:
            for u in text_units:
                if selected_candidate_id in (u.attachment_id, f"{u.attachment_id}:problem-1"):
                    chosen_unit = u
                    break
        elif directive.target_problem_index is not None and 0 <= directive.target_problem_index < len(text_units):
            chosen_unit = text_units[directive.target_problem_index]

        if chosen_unit is None:
            indep_candidates: list[UnifiedCandidateItem] = []
            for idx, u in enumerate(text_units):
                indep_candidates.append(
                    UnifiedCandidateItem(
                        candidate_id=f"{u.attachment_id}:problem-1",
                        label=_extract_problem_header_label(
                            u.problem_text, fallback_index=idx + 1, filename=u.filename
                        ),
                        preview_snippet=u.problem_text[:140],
                        preview_data_url=None,
                        page_number=None,
                        has_figure=u.has_figure or bool(diagram_only_ids),
                        problem_text=u.problem_text,
                        source_attachment_ids=u.source_attachment_ids,
                    )
                )
            all_sids = [str(a["attachment_id"]).strip() for a in ordered_attachments]
            return UnifiedPrepareOutcome(
                status="needs_selection",
                source_kind=primary_source_kind,
                learner_message=(
                    f"Phát hiện {len(indep_candidates)} bài toán độc lập từ các ảnh đã đính kèm. "
                    "Em chạm chọn đúng bài muốn dựng nhé."
                ),
                reason_code="MULTIPLE_PROBLEMS_DETECTED",
                candidates=tuple(indep_candidates),
                provenance={
                    "source_attachment_ids": all_sids,
                    "diagram_attachment_ids": list(diagram_only_ids),
                    "has_associated_figure": any(u.has_figure for u in text_units) or bool(diagram_only_ids),
                    "multi_image_mode": "independent_problems",
                },
                metrics={
                    **common_metrics,
                    "processing_ms": round((time.perf_counter() - t0) * 1000.0, 2),
                },
                request_id=request_id,
            )

        text_units = [chosen_unit]

    # Trường hợp 3: Một bài toán trải trên nhiều ảnh (hoặc 1 bài đã chọn + ảnh hình vẽ đi kèm, §10.1).
    upload_order_ids = [u.attachment_id for u in text_units]
    ordered_text_units, semantic_reordered = _order_same_problem_units(text_units)
    merged_raw_text, deduplicated_overlap = merge_overlapping_problem_segments(
        [u.problem_text for u in ordered_text_units]
    )
    final_text = merge_supplemental_text(merged_raw_text, directive)

    source_ids_ordered: list[str] = []
    for u in ordered_text_units:
        for sid in u.source_attachment_ids:
            if sid not in source_ids_ordered:
                source_ids_ordered.append(sid)
    if targeted_att_id is None:
        for did in diagram_only_ids:
            if did not in source_ids_ordered:
                source_ids_ordered.append(did)

    has_figure_combined = any(u.has_figure for u in ordered_text_units) or bool(diagram_only_ids)
    combined_flags: list[str] = []
    combined_uncertain: list[dict[str, Any]] = []
    combined_missing: list[str] = []
    for u in ordered_text_units:
        for f in u.flag_messages:
            if f not in combined_flags:
                combined_flags.append(f)
        for ut in u.uncertain_tokens:
            combined_uncertain.append(ut)
        for mr in u.missing_regions:
            if mr not in combined_missing:
                combined_missing.append(mr)

    # Nếu đề bài có hình vẽ đi kèm (từ cùng ảnh hoặc ảnh hình vẽ rời) VÀ lời đề phụ thuộc hình vẽ ("như hình vẽ"),
    # bật cờ `AMBIGUOUS_DIAGRAM` để yêu cầu người học xác nhận phần giả thiết chỉ có trên hình (§6.H).
    needs_diagram_conf = False
    if has_figure_combined and any(cue in final_text.lower() for cue in _THAM_CHIEU_HINH):
        ambig_msg = FLAG_MESSAGES["AMBIGUOUS_DIAGRAM"]
        if ambig_msg not in combined_flags:
            combined_flags.append(ambig_msg)
        needs_diagram_conf = True

    active_diagram_provs = diagram_only_provenance if targeted_att_id is None else {}
    diagram_text_link = _build_diagram_text_link(final_text, ordered_text_units, active_diagram_provs)

    prov_combined: dict[str, Any] = {
        "source_attachment_ids": source_ids_ordered,
        "upload_order_attachment_ids": upload_order_ids,
        "semantic_reordered": semantic_reordered,
        "diagram_attachment_ids": list(diagram_only_ids) if targeted_att_id is None else [],
        "deduplicated_attachment_ids": deduplicated_attachment_ids,
        "deduplicated_overlap": deduplicated_overlap or bool(deduplicated_attachment_ids),
        "has_associated_figure": has_figure_combined,
        "diagram_text_link": diagram_text_link,
        "multi_image_merged": len(ordered_text_units) > 1 or bool(diagram_only_ids) or bool(deduplicated_attachment_ids),
        "supplemental_merged": bool(directive.supplemental_text) and final_text != merged_raw_text,
    }
    if targeted_att_id is not None:
        prov_combined["selected_candidate_id"] = selected_candidate_id

    if detect_domain(final_text) != DOMAIN_HINH_HOC:
        return UnifiedPrepareOutcome(
            status="rejected",
            source_kind=primary_source_kind,
            problem_text=final_text,
            learner_message=REJECTION_MESSAGES["UNSUPPORTED_PROBLEM"],
            reason_code="UNSUPPORTED_PROBLEM",
            provenance=prov_combined,
            metrics={
                **common_metrics,
                "processing_ms": round((time.perf_counter() - t0) * 1000.0, 2),
            },
            request_id=request_id,
        )

    # Kiểm tra độ đầy đủ của đề ghép từ nhiều ảnh (§10.1): nếu vẫn thiếu phần câu hỏi/yêu cầu, không tự suy diễn mà trả `needs_confirmation`.
    if not _has_problem_question_or_goal(final_text):
        incomplete_msg = (
            "Đề bài ghép từ các ảnh hiện chưa có câu hỏi hoặc yêu cầu cần tính/chứng minh. "
            "Em kiểm tra và bổ sung phần còn thiếu trước khi dựng hình nhé."
        )
        if incomplete_msg not in combined_flags:
            combined_flags.insert(0, incomplete_msg)
        missing_q = "Thiếu câu hỏi hoặc yêu cầu kết thúc đề bài"
        if missing_q not in combined_missing:
            combined_missing.append(missing_q)
        return UnifiedPrepareOutcome(
            status="needs_confirmation",
            source_kind=primary_source_kind,
            problem_text=final_text,
            learner_message=incomplete_msg,
            reason_code="INCOMPLETE_MULTI_IMAGE_PROBLEM",
            flag_messages=tuple(combined_flags),
            uncertain_tokens=tuple(combined_uncertain),
            missing_regions=tuple(combined_missing),
            provenance=prov_combined,
            metrics={
                **common_metrics,
                "processing_ms": round((time.perf_counter() - t0) * 1000.0, 2),
            },
            request_id=request_id,
        )

    # Bảo toàn trạng thái `needs_confirmation` nếu bất kỳ ảnh thành phần nào có độ tin cậy thấp hoặc ký hiệu chưa chắc chắn (§13.11).
    if any(u.needs_confirmation for u in ordered_text_units) or needs_diagram_conf or combined_uncertain or combined_missing:
        lead_msg = (
            combined_flags[0]
            if combined_flags
            else "Có ký hiệu đọc chưa chắc chắn trong các ảnh đã chụp — em kiểm tra nhanh trước khi dựng."
        )
        return UnifiedPrepareOutcome(
            status="needs_confirmation",
            source_kind=primary_source_kind,
            problem_text=final_text,
            learner_message=lead_msg,
            reason_code="EXTRACTION_NEEDS_CONFIRMATION",
            flag_messages=tuple(combined_flags),
            uncertain_tokens=tuple(combined_uncertain),
            missing_regions=tuple(combined_missing),
            provenance=prov_combined,
            metrics={
                **common_metrics,
                "processing_ms": round((time.perf_counter() - t0) * 1000.0, 2),
            },
            request_id=request_id,
        )

    return UnifiedPrepareOutcome(
        status="ready",
        source_kind=primary_source_kind,
        problem_text=final_text,
        provenance=prov_combined,
        metrics={
            **common_metrics,
            "processing_ms": round((time.perf_counter() - t0) * 1000.0, 2),
        },
        request_id=request_id,
    )
