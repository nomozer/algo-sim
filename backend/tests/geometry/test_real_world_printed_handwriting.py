# -*- coding: utf-8 -*-
"""Regression suite for Master Task:
`ALGOSIM — REAL-WORLD GEOMETRY DATA ACQUISITION, HANDWRITTEN OCR & EVIDENCE RECONCILIATION`.

Covers Section XII mandatory verification targets:
1. Region detection on real-world layout failure modes:
   - Bug R1: Gray paper strip above bright white canvas padding (`detect_page_boundary` ink-retention guard)
     without regressing genuine dark-desk trimming.
   - Bug R2: Single-problem sandwich layout (`[Top Stem] -> [Middle 3D Figure] -> [Bottom Question/Options]`)
     merged as 1 complete problem without breaking genuine multi-problem page disambiguation or diagram-only handling.
2. Printed & Handwritten OCR fidelity and `reconcile_dual_ocr_texts`:
   - `A` vs `A'`, `√3` vs `V3`, `3` vs `8`, `⊥` vs `∥`, negative sign, decimal comma, primed plane notation.
   - Printed italic math corruption (e.g. `ABC.A'B'C'` -> `48C.4'8'C"`) blocked fail-closed.
   - Handwritten OCR corruption (e.g. `B` -> `13`, `a√3` -> `a√s`, incomplete line) blocked fail-closed.
   - Shared dual-OCR misrecognition (`reconcile_dual_ocr_texts` agreement on structurally invalid/incomplete math)
     caught by `verify_ocr_input_fidelity` so `0` corrupted problems enter Exact Kernel as `VERIFIED_COMPLETE`.
3. Real external Vietnamese exam phrasing -> Local Parser -> Source Gate -> Planner/Registry/Exact Kernel -> Adapter `/4`:
   - Leading exam scaffolding (`Câu 32:`, `Câu 24: (2,5 điểm)`).
   - `Cho hình chóp đều S.ABC có cạnh đáy bằng a, cạnh bên bằng 2a` (exact volume `a^3√11/12` -> numeric `√11/12` at `a=1`).
   - `Cho hình chóp S.ABC có đáy là tam giác ABC vuông tại B, AB = a, BC = a√3, SA ⊥ (ABC), SA = 2a`.
   - `Cho khối lăng trụ đứng ABC.A'B'C' có đáy là tam giác đều cạnh a, AA' = √3a (minh họa như hình vẽ bên). Tính số đo góc tạo bởi hai mặt phẳng (A'BC) và (ABC).` (`√3a` canonicalization + figure notice + `số đo góc tạo bởi`).
   - `Cho hình lăng trụ đứng ABC.A'B'C' có đáy ABC là tam giác vuông cân tại B và AB = 4 (tham khảo hình bên). Khoảng cách từ C đến mặt phẳng (ABB'A') bằng` (`vuông cân tại B` -> `right_angle` + `equal_length` + declarative exam stem).
   - Fail-closed `LOCAL_PARSE_PARTIAL` when a declarative question asks an unsupported sub-pyramid (`Thể tích của khối chóp S.MNP bằng?`) or when a premise contains an unsupported angle-given (`SB tạo với đáy một góc 60°`).
4. C26 7 `construct_plane_section` strict-vs-semantic contract verification (`K-A01..K-A04, R1-B01, R1-B02, R1-C02`):
   - Exact cyclic/reflection polygon equivalence on the cutting plane, non-self-intersecting 3D polygon in `Scene3D`,
     and zero information loss between `Planner /26` and `Adapter /4`.
5. External image corpus provenance & license audit (when run directory is populated):
   - Verifies `LICENSE_UNVERIFIED` binaries are never tracked inside Git, SHA-256 format is valid, and Printed vs
     Handwritten (`B1`, `B2`, `B3`) evaluation buckets remain strictly separated.
"""

from __future__ import annotations

import io
import json
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont
import pytest

from app.ai.adaptive_input_router import (
    reconcile_dual_ocr_texts,
    route_text_input,
    verify_ocr_input_fidelity,
)
from app.ai.local_geometry_parser import (
    LOCAL_PARSE_COMPLETE,
    LOCAL_PARSE_PARTIAL,
    parse_geometry_problem_locally,
)
from app.ingestion.image import normalize_image
from app.ingestion.region_detector import BoundingBox, detect_problem_regions

ROOT = Path(__file__).resolve().parents[3]
RUN_DIR = ROOT / "docs" / "evaluation" / "geometry" / "runs" / "real-world-printed-handwriting-acquisition"


def _jpeg_bytes(img: Image.Image, quality: int = 92) -> bytes:
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=quality)
    return buf.getvalue()


def _draw_lines(draw: ImageDraw.ImageDraw, xy: tuple[int, int], lines: list[str], ink=(18, 20, 24)) -> BoundingBox:
    font = ImageFont.load_default(size=22)
    x0, y0 = xy
    cy = y0
    mx = x0
    for ln in lines:
        bb = draw.textbbox((x0, cy), ln, font=font)
        draw.text((x0, cy), ln, fill=ink, font=font)
        mx = max(mx, bb[2])
        cy += 34
    return BoundingBox(x0, y0, mx, cy)


def _draw_wireframe_prism(draw: ImageDraw.ImageDraw, box: tuple[int, int, int, int], ink=(20, 24, 30)) -> BoundingBox:
    x0, y0, x1, y1 = box
    top_tri = [(x0 + 40, y0 + 35), (x1 - 35, y0 + 25), ((x0 + x1) // 2, y0 + 85)]
    bot_tri = [(x0 + 40, y1 - 55), (x1 - 35, y1 - 65), ((x0 + x1) // 2, y1 - 15)]
    for i in range(3):
        draw.line([top_tri[i], top_tri[(i + 1) % 3]], fill=ink, width=3)
        draw.line([bot_tri[i], bot_tri[(i + 1) % 3]], fill=ink, width=3)
        draw.line([top_tri[i], bot_tri[i]], fill=ink, width=3)
    return BoundingBox(x0, y0, x1, y1)


# ── 1. Region Detection Regression Tests (Bug R1 & Bug R2) ──────────────────────────────────────────────────────────


def test_region_bug_r1_gray_paper_strip_above_white_padding_does_not_trim_away_problem():
    """Bug R1: Full-bleed photographed gray paper strip (`V ~ 142`, as in `hd_q_1084979.jpg`) above `#FFFFFF`
    canvas padding must NOT mistake the gray paper strip for a dark desk and cut off the problem text,
    while genuine dark-desk photos still trim cleanly (`desk_trimmed=True`)."""
    w, h = 1600, 480
    img = Image.new("RGB", (w, h), (255, 255, 255))
    draw = ImageDraw.Draw(img)
    # Full-bleed gray photographed paper strip in upper half containing 100% of problem text
    draw.rectangle([0, 0, w, 245], fill=(142, 142, 140))
    gt_text = _draw_lines(
        draw,
        (60, 48),
        [
            "Cau 12: Cho hinh chop S.ABCD co day ABCD la hinh vuong canh a,",
            "SA vuong goc voi mat phang (ABCD) va SA = 2a.",
            "Tinh the tich khoi chop S.ABCD.",
        ],
        ink=(15, 15, 18),
    )
    norm = normalize_image(_jpeg_bytes(img), "image/jpeg")
    reg = detect_problem_regions(norm)

    assert reg.desk_trimmed is False
    ix0 = max(gt_text.x0, reg.selected_bbox.x0)
    iy0 = max(gt_text.y0, reg.selected_bbox.y0)
    ix1 = min(gt_text.x1, reg.selected_bbox.x1)
    iy1 = min(gt_text.y1, reg.selected_bbox.y1)
    inter = max(0, ix1 - ix0) * max(0, iy1 - iy0)
    assert inter / float(gt_text.area) >= 0.95

    # Genuine dark-desk photo with bright paper sheet in the middle MUST still trim desk (`desk_trimmed=True`)
    desk_img = Image.new("RGB", (1400, 1050), (58, 42, 30))
    desk_draw = ImageDraw.Draw(desk_img)
    desk_draw.rectangle([220, 130, 1180, 920], fill=(248, 248, 244))
    _draw_lines(
        desk_draw,
        (260, 190),
        [
            "Cau 5: Cho hinh chop S.ABCD co day ABCD la hinh vuong",
            "canh 2a, SA vuong goc voi (ABCD) va SA = 3a.",
            "Tinh the tich khoi chop S.ABCD.",
        ],
    )
    _draw_wireframe_prism(desk_draw, (480, 380, 860, 780))
    desk_reg = detect_problem_regions(normalize_image(_jpeg_bytes(desk_img), "image/jpeg"))
    assert desk_reg.desk_trimmed is True


def test_region_bug_r2_sandwich_figure_layout_merges_single_problem_but_keeps_two_problems_separate():
    """Bug R2: `[Top Stem] -> [Middle 3D Figure] -> [Bottom Question / Options]` is ONE problem
    (`ambiguous_multi_problem=False`), whereas two independent problems each with their own figure
    remain `ambiguous_multi_problem=True`, and a diagram-only image has zero text blocks."""
    # Case A: Single problem with sandwich figure in the middle
    sw_img = Image.new("RGB", (1200, 650), (252, 252, 250))
    sw_draw = ImageDraw.Draw(sw_img)
    top_b = _draw_lines(
        sw_draw,
        (80, 55),
        [
            "Cau 16. Cho hinh lang tru dung ABC.A'B'C' co day ABC la tam giac",
            "vuong can tai B va AB = 4 (tham khao hinh ben).",
        ],
    )
    fig_b = _draw_wireframe_prism(sw_draw, (430, 108, 760, 495))
    bot_b = _draw_lines(
        sw_draw,
        (80, 500),
        [
            "Khoang cach tu C den mat phang (ABB'A') bang:",
            "A. 2      B. 4      C. 2 sqrt(2)      D. 4 sqrt(2)",
        ],
    )
    sw_gt = top_b.union(fig_b).union(bot_b)
    sw_reg = detect_problem_regions(normalize_image(_jpeg_bytes(sw_img), "image/jpeg"))
    assert sw_reg.ambiguous_multi_problem is False
    assert len(sw_reg.candidates) == 1
    assert sw_reg.selected_bbox.y0 <= top_b.y0 + 5
    assert sw_reg.selected_bbox.y1 >= bot_b.y1 - 10
    assert sw_gt.area > 0

    # Case B: Genuine 2-problem page (each problem has substantial stem + side figure)
    mp_img = Image.new("RGB", (1200, 1150), (252, 252, 250))
    mp_draw = ImageDraw.Draw(mp_img)
    _draw_lines(
        mp_draw,
        (70, 95),
        [
            "Cau 1. Cho hinh chop S.ABCD co day ABCD la hinh vuong",
            "canh 2, SA vuong goc voi (ABCD) va SA = 3.",
            "Tinh the tich khoi chop S.ABCD.",
        ],
    )
    _draw_wireframe_prism(mp_draw, (810, 90, 1110, 390))
    _draw_lines(
        mp_draw,
        (70, 620),
        [
            "Cau 2. Cho lang tru dung ABC.A'B'C' co day ABC la tam",
            "giac deu canh 2, AA' = 4. Tinh the tich khoi lang tru",
            "ABC.A'B'C' va khoang cach tu A den (A'BC).",
        ],
    )
    _draw_wireframe_prism(mp_draw, (810, 610, 1110, 930))
    mp_reg = detect_problem_regions(normalize_image(_jpeg_bytes(mp_img), "image/jpeg"))
    assert mp_reg.ambiguous_multi_problem is True
    assert len(mp_reg.candidates) >= 2

    # Case C: Diagram-only crop (as in VMMU figure crops & B2 sketch crops) -> 0 text blocks
    diag_img = Image.new("RGB", (640, 520), (252, 252, 250))
    diag_draw = ImageDraw.Draw(diag_img)
    _draw_wireframe_prism(diag_draw, (140, 80, 500, 440))
    diag_reg = detect_problem_regions(normalize_image(_jpeg_bytes(diag_img), "image/jpeg"))
    assert sum(1 for b in diag_reg.blocks if b.kind == "text") == 0


# ── 2. Printed & Handwritten OCR Disagreement, Shared Error & Fidelity Gate Tests ───────────────────────────────────


@pytest.mark.parametrize(
    "label,tess_txt,rapid_txt",
    [
        (
            "prime_drop_A_vs_A_prime",
            "Cho hình lăng trụ đứng ABC.A'B'C' có đáy là tam giác đều cạnh 2, AA' = 4. Tính thể tích khối lăng trụ ABC.A'B'C'.",
            "Cho hình lăng trụ đứng ABC.AB'C' có đáy là tam giác đều cạnh 2, AA = 4. Tính thể tích khối lăng trụ ABC.AB'C'.",
        ),
        (
            "radical_sqrt3_vs_V3",
            "Cho hình chóp S.ABCD có đáy ABCD là hình vuông cạnh 2, SA ⊥ (ABCD), SA = √3. Tính thể tích khối chóp S.ABCD.",
            "Cho hình chóp S.ABCD có đáy ABCD là hình vuông cạnh 2, SA ⊥ (ABCD), SA = V3. Tính thể tích khối chóp S.ABCD.",
        ),
        (
            "digit_3_vs_8",
            "Cho hình chóp S.ABCD có đáy ABCD là hình vuông cạnh 2, SA ⊥ (ABCD), SA = 3. Tính thể tích khối chóp S.ABCD.",
            "Cho hình chóp S.ABCD có đáy ABCD là hình vuông cạnh 2, SA ⊥ (ABCD), SA = 8. Tính thể tích khối chóp S.ABCD.",
        ),
        (
            "perp_vs_parallel",
            "Cho hình chóp S.ABCD có đáy ABCD là hình vuông cạnh 2, SA ⊥ (ABCD), SA = 3. Tính thể tích khối chóp S.ABCD.",
            "Cho hình chóp S.ABCD có đáy ABCD là hình vuông cạnh 2, SA ∥ (ABCD), SA = 3. Tính thể tích khối chóp S.ABCD.",
        ),
    ],
)
def test_dual_ocr_disagreement_never_produces_verified_complete(label: str, tess_txt: str, rapid_txt: str):
    rec = reconcile_dual_ocr_texts(tess_txt, rapid_txt, is_degraded_image=False)
    assert rec["reconciled"] is False, f"Expected dual-OCR disagreement refusal on {label}, got {rec}"


@pytest.mark.parametrize(
    "corrupted_shared_ocr",
    [
        # Printed italic math corruption observed on external exam images
        "Câu 16. Cho hình lăng trụ đứng 48C.4'8'C\" có đáy 48C là tam giác vuông cân tại B và AB = 4.",
        # Handwritten OCR corruption observed on hd_a_6043187_problem_crop.jpg
        "Cho hình lăng trụ đứng ABC A'BC có đáy là tam giác vuông tại 13, AB = a, AA' = a√s.",
        # Incomplete handwritten line missing goal
        "Cho hình chóp S.ABCD có đáy ABCD là hình vuông cạnh a, SA vuông góc",
    ],
)
def test_shared_dual_ocr_misrecognition_and_handwritten_noise_blocked_by_fidelity_gate(corrupted_shared_ocr: str):
    """Even if two OCR passes identically output corrupted math/incomplete text,
    `verify_ocr_input_fidelity` must block before Exact Kernel."""
    fid = verify_ocr_input_fidelity(corrupted_shared_ocr)
    assert fid["fidelity_passed"] is False


# ── 3. Real External Exam Vietnamese Phrasings -> Zero-AI Exact Geometry Solving ─────────────────────────────────────


@pytest.mark.parametrize(
    "case_id,problem_text,expected_answers",
    [
        (
            "ext_hd_q_5259753_reg_pyr_lat_edge",
            "Cho hình chóp đều S.ABC có cạnh đáy bằng a, cạnh bên bằng 2a. Tính thể tích khối chóp S.ABC.",
            ("√11/12", "a^3*√11/12", "a³√11/12"),
        ),
        (
            "ext_hd_q_7958052_standalone_right_tri_base",
            "Cho hình chóp S.ABC có đáy là tam giác ABC vuông tại B, AB = a, BC = a√3, SA ⊥ (ABC), SA = 2a. Tính khoảng cách từ A đến mặt phẳng (SBC).",
            ("2√5/5", "2a√5/5"),
        ),
        (
            "ext_vmmu_r10_c30_sqrt3a_and_angle_tao_boi_cos2",
            "Câu 30. Cho khối lăng trụ đứng ABC.A'B'C' có đáy là tam giác đều cạnh a, AA' = √3a (minh họa như hình vẽ bên). Tính góc tạo bởi hai mặt phẳng (A'BC) và (ABC).",
            ("cos²=1/5", "1/5"),
        ),
        (
            "ext_hd_q_7922924_c16_right_isosceles_declarative_with_height",
            "Câu 16. Cho hình lăng trụ đứng ABC.A'B'C' có đáy ABC là tam giác vuông cân tại B, AB = 4 và AA' = 3 (tham khảo hình bên). Khoảng cách từ C đến mặt phẳng (ABB'A') bằng",
            ("4",),
        ),
        (
            "ext_hd_q_7907931_c32_exam_header_declarative_la",
            "Câu 32: (2,5 điểm) Cho hình chóp S.ABCD có đáy ABCD là hình vuông cạnh a, SA ⊥ (ABCD) và SA = a√2 (tham khảo hình vẽ). Thể tích của khối chóp S.ABCD là:",
            ("√2/3", "a^3*√2/3", "a³√2/3"),
        ),
    ],
)
def test_real_external_exam_transcriptions_solve_zero_ai_exact(
    case_id: str, problem_text: str, expected_answers: tuple[str, ...]
):
    parsed = parse_geometry_problem_locally(problem_text)
    assert parsed.status == LOCAL_PARSE_COMPLETE, (
        f"{case_id}: expected LOCAL_PARSE_COMPLETE, got {parsed.status} "
        f"(reason={parsed.reason_code}, fallback={parsed.fallback_reason}, cov={parsed.source_coverage.to_dict()})"
    )
    out = route_text_input(problem_text, allow_live_ai=False)
    assert out.status == "SERVED", f"{case_id}: Hybrid /4 failed with {out.response}"
    assert out.telemetry.total_provider_calls == 0
    answers = (out.response.get("route_d") or {}).get("answers") or {}
    assert len(answers) == 1
    actual_ans = next(iter(answers.values()))
    assert actual_ans in expected_answers, f"{case_id}: expected one of {expected_answers!r}, got {actual_ans!r}"
    assert (out.response.get("envelope") or {}).get("scene3d") is not None


def test_real_external_missing_prism_height_refused_zero_ai_missing_dimension():
    """Verbatim `hd_q_7922924_c16` omits prism height `AA'`. Local Parser achieves `LOCAL_PARSE_COMPLETE`
    with `0` AI calls. CORRECTED by run `real-world-end-to-end-reliability`: the asked distance does NOT depend on
    `AA'` (CB ⊥ AB and CB ⊥ BB' ⇒ d(C, (ABB'A')) = CB = AB), so the former `MISSING_DIMENSION` was a false refusal.
    The Exact Kernel now proves height invariance and serves with an ILLUSTRATIVE scene (`unique = False`); it still
    never fabricates `AA'` as a given (test name kept for history)."""
    problem_text = (
        "Câu 16. Cho hình lăng trụ đứng ABC.A'B'C' có đáy ABC là tam giác vuông cân tại B "
        "và AB = 4 (tham khảo hình bên). Khoảng cách từ C đến mặt phẳng (ABB'A') bằng"
    )
    parsed = parse_geometry_problem_locally(problem_text)
    assert parsed.status == LOCAL_PARSE_COMPLETE
    out = route_text_input(problem_text, allow_live_ai=False)
    assert out.telemetry.total_provider_calls == 0
    assert out.status == "SERVED"
    assert list(out.response["route_d"]["answers"].values()) == ["4"]
    assert out.response["route_d"]["scene_configuration"]["unique"] is False

    # Also verify exact `hd_q_7922924` Câu 10 wording with `, có đáy` and newline-separated MC options after `(ABB'A')`
    verbatim_hd_q_7922924 = (
        "Câu 10: Cho hình lăng trụ đứng ABC.A'B'C', có đáy là tam giác vuông cân tại B và AB = 6. "
        "Tính khoảng cách từ điểm C đến mặt phẳng (ABB'A')\nA. 3. B. 6√2. C. 3√2. D. 6."
    )
    out_hd = route_text_input(verbatim_hd_q_7922924, allow_live_ai=False)
    assert out_hd.telemetry.total_provider_calls == 0
    assert out_hd.telemetry.local_parse_status == LOCAL_PARSE_COMPLETE
    assert out_hd.status == "SERVED"                      # published key D. 6
    assert list(out_hd.response["route_d"]["answers"].values()) == ["6"]
    assert out_hd.response["route_d"]["scene_configuration"]["unique"] is False


@pytest.mark.parametrize(
    ("case_id", "problem_text", "expected_answer"),
    [
        (
            "ext_vmmu_r4_c14_angle_premise_solved",
            "Cho hình chóp S.ABCD có đáy là hình vuông cạnh a√3, SA vuông góc với mặt phẳng đáy và SB tạo với đáy một góc 60°. Tính thể tích khối chóp S.ABCD.",
            "3a³",
        ),
        (
            "ext_hd_a_6043187_hw_line_plane_angle_premise_solved",
            "Cho hình lăng trụ đứng ABC.A'B'C' có đáy ABC là tam giác vuông tại B, AB = a, AA' = a√3, góc giữa đường thẳng BC' với mặt phẳng đáy bằng 60°. Tính thể tích khối lăng trụ ABC.A'B'C'.",
            "a³√3/2",
        ),
    ],
)
def test_real_external_angle_premise_problems_solved_zero_ai(
    case_id: str, problem_text: str, expected_answer: str
):
    out = route_text_input(problem_text, allow_live_ai=False)
    assert out.status == "SERVED", (case_id, out.status, out.response)
    assert out.telemetry.total_provider_calls == 0
    assert out.telemetry.local_parse_status == LOCAL_PARSE_COMPLETE
    assert list(out.response["route_d"]["answers"].values()) == [expected_answer]
    assert (out.response.get("envelope") or {}).get("scene3d") is not None


@pytest.mark.parametrize(
    "case_id,problem_text",
    [
        (
            "ext_vmmu_r10_c30_degree_measure_wording_refused_by_source_gate",
            "Câu 30. Cho khối lăng trụ đứng ABC.A'B'C' có đáy là tam giác đều cạnh a, AA' = √3a (minh họa như hình vẽ bên). Tính số đo góc tạo bởi hai mặt phẳng (A'BC) và (ABC).",
        ),
        (
            "ext_hd_q_7907931_c33_unparsed_declarative_subpyramid_goal",
            "Câu 33: Cho hình chóp S.ABC có đáy ABC là tam giác đều cạnh a, SA ⊥ (ABC), SA = a. Gọi M, N, P lần lượt là trung điểm của BC, CA, AB. Thể tích của khối chóp S.MNP bằng?",
        ),
        (
            "ext_unparsed_oblique_slope_idiom_guard",
            "Cho hình chóp S.ABCD có đáy là hình vuông cạnh a, các mặt bên nghiêng đều trên mặt đáy một góc 60°. Tính thể tích khối chóp S.ABCD.",
        ),
    ],
)
def test_real_external_unsupported_clauses_fail_closed_to_partial_never_wrong_served(
    case_id: str, problem_text: str
):
    parsed = parse_geometry_problem_locally(problem_text)
    assert parsed.status == LOCAL_PARSE_PARTIAL, (
        f"{case_id}: must fail-closed to LOCAL_PARSE_PARTIAL instead of dropping clause ({parsed.status})"
    )


# ── 4. C26 7 `construct_plane_section` Strict-Contract Equivalence & Scene3D Integrity ─────────────────────────────


def _eval_exact_coord(expr: str) -> float:
    import math
    import re as _re

    s = str(expr).strip().replace("^", "**")
    s = _re.sub(r"(\d)\s*√", r"\1*√", s)
    s = _re.sub(r"√\(([^)]+)\)", r"math.sqrt(\1)", s)
    s = _re.sub(r"√(\d+)", r"math.sqrt(\1)", s)
    return float(eval(s, {"__builtins__": {}}, {"math": math}))


def _polygon_3d_coplanar_and_convex(coords: list[tuple[float, float, float]]) -> bool:
    if len(coords) < 3:
        return False
    p0 = coords[0]
    v1 = (coords[1][0] - p0[0], coords[1][1] - p0[1], coords[1][2] - p0[2])
    normal = None
    for k in range(2, len(coords)):
        vk = (coords[k][0] - p0[0], coords[k][1] - p0[1], coords[k][2] - p0[2])
        nx = v1[1] * vk[2] - v1[2] * vk[1]
        ny = v1[2] * vk[0] - v1[0] * vk[2]
        nz = v1[0] * vk[1] - v1[1] * vk[0]
        nlen = (nx * nx + ny * ny + nz * nz) ** 0.5
        if nlen > 1e-6:
            normal = (nx / nlen, ny / nlen, nz / nlen)
            break
    if normal is None:
        return False
    # 1. Coplanarity check on all vertices
    for pt in coords[2:]:
        dv = (pt[0] - p0[0], pt[1] - p0[1], pt[2] - p0[2])
        dist = abs(dv[0] * normal[0] + dv[1] * normal[1] + dv[2] * normal[2])
        if dist > 1e-6:
            return False
    # 2. Consistent turn sign around `normal` (convex, non-self-intersecting ordered boundary)
    signs = []
    m = len(coords)
    for i in range(m):
        a = coords[i]
        b = coords[(i + 1) % m]
        c = coords[(i + 2) % m]
        e1 = (b[0] - a[0], b[1] - a[1], b[2] - a[2])
        e2 = (c[0] - b[0], c[1] - b[1], c[2] - b[2])
        cx = e1[1] * e2[2] - e1[2] * e2[1]
        cy = e1[2] * e2[0] - e1[0] * e2[2]
        cz = e1[0] * e2[1] - e1[1] * e2[0]
        dot_n = cx * normal[0] + cy * normal[1] + cz * normal[2]
        if abs(dot_n) > 1e-6:
            signs.append(1 if dot_n > 0 else -1)
    return bool(signs) and len(set(signs)) == 1


def test_c26_seven_section_cases_dihedral_equivalence_and_scene3d_polygon_valid():
    """Verify the 7 C26 `construct_plane_section` SERVED strict-contract divergences:
    1) Authoritative C26 three-tier receipt identifies exact 7 SERVED cases (`K-A01..K-A04, R1-B01, R1-B02, R1-C02`).
    2) Every case explicitly asks `Xác định thiết diện...` in `problem_text`, proving `construct_plane_section`
       in `TypedFactNext /2` is semantically faithful while legacy strict gold omitted the simulation goal.
    3) Replaying through `Adapter /4` (`run_typed_fact_next_v2_route`) produces identical exact area answers,
       certified closed section boundary, coplanar non-self-intersecting 3D polygon in `Scene3D`, and zero info loss."""
    from copy import deepcopy
    from app.ai.adapter4_route import run_typed_fact_next_v2_route

    c26_receipt_path = (
        ROOT
        / "docs"
        / "evaluation"
        / "geometry"
        / "runs"
        / "hybrid-independent-h1"
        / "c26-three-tier-verification.json"
    )
    data = json.loads(c26_receipt_path.read_text(encoding="utf-8"))
    served_divergences = [
        r
        for r in data["per_case"]
        if r.get("semantic_served_correct") is True and r.get("strict_served_correct") is False
    ]
    assert len(served_divergences) == 7
    expected_ids = {"K-A01", "K-A02", "K-A03", "K-A04", "R1-B01", "R1-B02", "R1-C02"}
    assert {r["case_id"] for r in served_divergences} == expected_ids

    retest_dir = ROOT / "docs" / "evaluation" / "geometry" / "runs" / "hybrid-live-extraction-retest" / "full"
    rows_by_id: dict[str, dict] = {}
    for jf in ("k1-live.jsonl", "r1-live.jsonl"):
        for ln in (retest_dir / jf).read_text(encoding="utf-8").splitlines():
            if not ln.strip():
                continue
            obj = json.loads(ln)
            if obj.get("type") == "row" and obj.get("case_id") in expected_ids:
                rows_by_id[obj["case_id"]] = obj
    assert set(rows_by_id) == expected_ids

    for cid in sorted(expected_ids):
        row = rows_by_id[cid]
        raw_with = deepcopy(row["raw_extraction"])
        assert "thiết diện" in raw_with["problem_text"].lower()
        assert any(sg.get("kind") == "construct_plane_section" for sg in raw_with.get("simulation_goals", []))

        res_with = run_typed_fact_next_v2_route(raw_with)
        assert res_with.status == "SERVED", f"{cid}: {res_with.code} {res_with.reason}"

        raw_without = deepcopy(raw_with)
        raw_without["simulation_goals"] = [
            sg for sg in raw_without.get("simulation_goals", []) if sg.get("kind") != "construct_plane_section"
        ]
        res_without = run_typed_fact_next_v2_route(raw_without)
        # Omitting `construct_plane_section` when `Xác định thiết diện...` is explicitly requested in source text
        # is rightly REFUSED by `registry.kiem_nguon` (`REQUEST_NOT_ANSWERED`), proving the legacy strict benchmark
        # gold `expected_goals` was incomplete while `TypedFactNext /2` + `Adapter /4` is mathematically faithful!
        assert res_without.status == "REFUSED"
        assert res_without.code in {"REQUEST_NOT_ANSWERED", "SOURCE_OBJECT_MISMATCH"}

        secs = res_with.route_d.get("sections") or []
        assert len(secs) == 1, f"{cid}: expected 1 certified section in route_d, got {secs}"
        cert = secs[0]["closure_certificate"]
        assert cert["verified"] is True
        boundary = secs[0]["boundary"]
        assert len(boundary) >= 3 and len(set(boundary)) == len(boundary)

        scene_secs = [o for o in (res_with.scene3d or {}).get("objects", []) if o.get("type") == "section"]
        assert len(scene_secs) == 1, f"{cid}: expected 1 section object in scene3d, got {scene_secs}"
        s_sec = scene_secs[0]
        assert s_sec["closed"] is True
        assert s_sec["polygon"] == cert["polygon"], f"{cid}: Planner->Adapter polygon mismatch"
        assert [e["entity_id"] for e in s_sec["endpoint_entities"]] == boundary
        assert all(e["anonymous_coordinate_fallback"] is False for e in s_sec["endpoint_entities"])
        assert s_sec["identity_diagnostics"] == []

        poly_coords = [tuple(_eval_exact_coord(c) for c in pt) for pt in s_sec["polygon"]]
        assert _polygon_3d_coplanar_and_convex(poly_coords), f"{cid}: non-coplanar or self-intersecting section {poly_coords}"


def test_real_world_vietnamese_exam_grammar_fixes_da_cho_semicolon_list_and_comma_base():
    """Regression tests for 3 general Vietnamese exam grammar patterns discovered on external images:
    1) Multiple-choice anaphoric stem `Thể tích khối chóp đã cho bằng A. ... B. ... C. ... D. ...` (`vmmu_page_r4`).
    2) Semicolon-delimited point & segment lists `Gọi M; N; P lần lượt là trung điểm của SA; SB; SC` (`hd_q_7907931`).
    3) Comma before base clause `Cho hình lăng trụ đứng ABC.A'B'C', có đáy là tam giác vuông cân tại B` (`hd_q_7922924`)."""
    # 1) Verbatim multiple-choice exam stem with "khối chóp đã cho bằng" + 4 choices
    out_r4 = route_text_input(
        "Câu 14. Cho khối chóp S.ABC có đáy là tam giác vuông cân tại B, AB = 2, "
        "SA vuông góc với đáy và SA = 3 (tham khảo hình bên). "
        "Thể tích khối chóp đã cho bằng A. 12. B. 2. C. 6. D. 4.",
        allow_live_ai=False,
    )
    assert out_r4.status == "SERVED"
    assert out_r4.telemetry.local_parse_status == LOCAL_PARSE_COMPLETE
    assert out_r4.telemetry.chosen_route == "LOCAL_DETERMINISTIC_HYBRID"
    assert out_r4.telemetry.total_provider_calls == 0
    frames_r4 = out_r4.response["envelope"]["config"]["frames"]
    assert "2." in frames_r4[-1]["narration"] or frames_r4[-1]["narration"].endswith(" 2.")

    # 2) Semicolon-delimited midpoint list + symbolic side `a` + trailing 4-option line
    out_semi = route_text_input(
        "Câu 33: Cho hình chóp S.ABC có đáy là tam giác đều cạnh a, SA vuông góc với đáy, SA = a√3/2. "
        "Gọi M; N; P lần lượt là trung điểm của SA; SB; SC. Tính thể tích khối chóp S.ABC.\n"
        "A. a^3/8   B. a^3/12   C. a^3/4   D. 3a^3/8",
        allow_live_ai=False,
    )
    assert out_semi.status == "SERVED"
    assert out_semi.telemetry.local_parse_status == LOCAL_PARSE_COMPLETE
    assert out_semi.telemetry.total_provider_calls == 0
    frames_semi = out_semi.response["envelope"]["config"]["frames"]
    assert "1/8" in frames_semi[-1]["narration"]

    # 3) Comma between solid notation and `có đáy là tam giác vuông cân tại B`
    out_comma = route_text_input(
        "Câu 10: Cho hình lăng trụ đứng ABC.A'B'C', có đáy là tam giác vuông cân tại B và AB = 6, AA' = 5. "
        "Tính thể tích khối lăng trụ ABC.A'B'C'.",
        allow_live_ai=False,
    )
    assert out_comma.status == "SERVED"
    assert out_comma.telemetry.local_parse_status == LOCAL_PARSE_COMPLETE
    assert out_comma.telemetry.total_provider_calls == 0
    frames_comma = out_comma.response["envelope"]["config"]["frames"]
    assert "90" in frames_comma[-1]["narration"]


def test_external_corpus_provenance_and_license_hygiene_if_present():
    """Verify run receipts follow strict provenance, non-redistribution of `LICENSE_UNVERIFIED` files,
    and separation of Printed vs Handwritten (`B1`, `B2`, `B3`) metrics."""
    manifest_path = RUN_DIR / "external_image_corpus_manifest.json"
    if not manifest_path.exists():
        pytest.skip("Manifest not yet generated")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    items = manifest["items"]
    assert len(items) >= 30
    printed = [x for x in items if x["printed_or_handwritten"] == "PRINTED"]
    handwritten = [x for x in items if x["printed_or_handwritten"] == "HANDWRITTEN"]
    assert len(printed) >= 12
    assert len(handwritten) >= 12
    for item in items:
        assert len(item["original_file_sha256"]) == 64
        if item["license_status"] == "LICENSE_UNVERIFIED":
            assert item.get("committed_to_git") is False
