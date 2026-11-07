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

import os
import time
from dataclasses import dataclass, field
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

    def to_dict(self) -> dict[str, Any]:
        return {
            "candidate_id": self.candidate_id,
            "label": self.label,
            "preview_snippet": self.preview_snippet,
            "preview_data_url": self.preview_data_url,
            "page_number": self.page_number,
            "has_figure": self.has_figure,
            "problem_text": self.problem_text,
        }


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

    def to_dict(self) -> dict[str, Any]:
        return {
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
            "provenance": dict(self.provenance),
            "metrics": dict(self.metrics),
        }


def _require_vision_key(api_key: str | None) -> str:
    if os.getenv("ALLOW_LIVE_AI") == "0":
        raise LiveVisionDisabledError("Chế độ trích xuất trực tiếp đang tắt (ALLOW_LIVE_AI=0).")
    if not api_key:
        raise MissingVisionKeyError("Thiếu GEMINI_API_KEY để đọc ảnh/trang scan.")
    return api_key


def _text_candidates_to_items(pool: list[TextProblemCandidate]) -> tuple[UnifiedCandidateItem, ...]:
    return tuple(
        UnifiedCandidateItem(
            candidate_id=c.candidate_id,
            label=c.label,
            preview_snippet=c.preview_snippet,
            preview_data_url=None,
            page_number=c.page_number,
            has_figure=c.has_figure,
            problem_text=c.problem_text,
        )
        for c in pool
    )


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

    metrics_now = {
        "vlm_calls": vlm_calls,
        "used_vlm": True,
        "raw_input_bytes": raw_input_bytes,
        "vlm_payload_bytes": vlm_bytes,
        "uncropped_baseline_bytes": uncropped_bytes,
    }

    assessment = ext_res.assessment

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
                candidates=_text_candidates_to_items(pool_txt),
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


async def prepare_unified_input(
    *,
    content: str,
    declared_mime: str | None = None,
    filename: str | None = None,
    user_text: str | None = None,
    selected_candidate_id: str | None = None,
    api_key: str | None = None,
    cache_version: str | None = None,
) -> UnifiedPrepareOutcome:
    """Điểm vào thống nhất cho mọi tệp đính kèm khi người học bấm "Dựng hình"."""
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
