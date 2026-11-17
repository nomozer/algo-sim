# -*- coding: utf-8 -*-
"""Student-ready API contract & UX hygiene tests for campaign `student-ready-geometry-simulation-input-reliability`.

Verifies:
1. Zero machine IDs (`s1`, `s2`, `c1`, `q1`, `p1`, `d1`, `@d1`, `@orthocenter_1`), `snake_case`, JSON paths,
   braces, or raw exception names leak into student-facing `learner_reason` across refusal categories & `/api/analyze`.
2. `ocr-confirmation-provenance/1` (`/api/input/prepare`) & `verified-input-provenance/1` (`/api/analyze` with
   `input.source_provenance`), including whole-draft downgrade (`counted_as_unmodified_auto_ocr == False`).
3. Multi-problem page isolation on `ext_prt_03` (`needs_selection`, 2 candidates) & `ext_prt_08` (4 bands, 0 wrong-served).
4. `FE-4` `Scene3D` role-based auxiliary metadata (`CONSTRUCT_AUXILIARY_GEOMETRY` vs primary solid edges/faces).
"""
from __future__ import annotations

import base64
import hashlib
import io
import json
from pathlib import Path

from fastapi.testclient import TestClient
from PIL import Image, ImageDraw, ImageFont
import pytest

from app import main as M
from app.ai import adaptive_input_router as AIR
from app.ai.adapter4_route import run_typed_fact_next_v2_route
from app.ai.hybrid_preview import classify_refusal
from app.ai.local_geometry_parser import parse_geometry_problem_locally
from app.ingestion import local_ocr as LO
from app.learner_messages import (
    _MACHINE_TOKEN_RE,
    attach_learner_reason,
    learner_reason,
)
from tests.route_client import sign_in

ROOT = Path(__file__).resolve().parents[2]
RUNS_DIR = ROOT / "docs" / "evaluation" / "geometry" / "runs"

_POISONED_SUBJECTS = ["s1", "s2", "c1", "q1", "p1", "d1", "@d1", "@orthocenter_1", "snake_case", "{'raw': 1}"]


def _assert_clean_student_text(msg: str, ctx: str = "") -> None:
    assert isinstance(msg, str) and msg.strip(), f"Empty message for {ctx}"
    match = _MACHINE_TOKEN_RE.search(msg)
    assert match is None, f"Machine token {match.group(0)!r} leaked in {ctx}: {msg!r}"


def test_refusal_hygiene_zero_machine_token_leaks_across_categories(monkeypatch):
    envelopes = [
        {"status": "unsupported", "failure_category": "capability_gap", "reason_subjects": _POISONED_SUBJECTS},
        {
            "status": "unsupported",
            "failure_category": "insufficient_specification",
            "reason": "Thiếu s1 và @d1 (KeyError: snake_case) ở $.premises[0]",
        },
        {
            "status": "unsupported",
            "failure_category": "semantic_incomplete",
            "reason": "Đề chứa q1 và p1 chưa tách ở block_id",
        },
        {"status": "unsupported", "failure_category": "geometry_generation_failed", "reason_subjects": _POISONED_SUBJECTS},
        {"status": "unsupported", "failure_category": "verification_gap", "reason_subjects": _POISONED_SUBJECTS},
        {"status": "unsupported", "failure_category": "out_of_scope", "reason_subjects": _POISONED_SUBJECTS},
        {"status": "unsupported", "failure_category": "not_simulation_suitable", "reason_subjects": _POISONED_SUBJECTS},
        {
            "status": "unsupported",
            "reason_code": "NON_POSITIVE_LENGTH",
            "refusal_cause": "SOURCE",
            "failure_category": "geometry_generation_failed",
            "reason_subjects": [*_POISONED_SUBJECTS, "SA"],
        },
        {
            "status": "unsupported",
            "reason_code": "PLANE_DOES_NOT_CUT",
            "refusal_cause": "SOURCE",
            "failure_category": "geometry_generation_failed",
            "reason_subjects": [*_POISONED_SUBJECTS, "(α)"],
        },
        {
            "status": "unsupported",
            "reason_code": "CONSTRUCTION_NOT_TEXT_BOUND",
            "failure_category": "verification_gap",
            "reason_subjects": [*_POISONED_SUBJECTS, "(P)", "(Q)"],
        },
        {
            "status": "unsupported",
            "reason_code": "CONSTRUCTION_NOT_TEXT_BOUND",
            "stage_reached": "construction_binding",
            "failure_category": "verification_gap",
            "reason_subjects": [*_POISONED_SUBJECTS, "M là trung điểm SA", "M là trung điểm SB"],
        },
        {
            "status": "unsupported",
            "reason_code": "CONSTRUCTION_BINDING_UNVERIFIED",
            "failure_category": "verification_gap",
            "reason_subjects": [*_POISONED_SUBJECTS, "H"],
        },
        {
            "status": "unsupported",
            "reason_code": "CONSTRUCTION_REPLACED_BY_COORDINATES",
            "failure_category": "verification_gap",
            "reason_subjects": [*_POISONED_SUBJECTS, "H là hình chiếu của S", "được đặt bằng toạ độ"],
        },
        {
            "status": "unsupported",
            "reason_code": "GIVEN_VALUE_NOT_IN_SOURCE",
            "failure_category": "verification_gap",
            "reason_subjects": [*_POISONED_SUBJECTS, "AB"],
        },
        {
            "status": "unsupported",
            "reason_code": "ASSUMPTION_DETERMINES_ANSWER",
            "failure_category": "insufficient_specification",
            "reason_subjects": _POISONED_SUBJECTS,
        },
    ]

    for idx, env in enumerate(envelopes):
        msg = learner_reason(env)
        _assert_clean_student_text(msg, f"learner_reason[{idx}]")
        attached = attach_learner_reason(env)
        _assert_clean_student_text(attached["learner_reason"], f"attach[{idx}]")

    for code in ("EXACT_DOMAIN_EXCEEDED", "MISSING_DIMENSION", "NON_COPLANAR_POINTS", "QUOTE_NOT_IN_SOURCE", "OUT_OF_SCOPE"):
        cls = classify_refusal(code, problem_text="Cho hình chóp S.ABC có SA = 2a.")
        _assert_clean_student_text(cls.message, f"classify_refusal({code})")

    # Preserves valid mathematical symbols like SA, (α), AB while scrubbing poisoned tokens
    assert "SA" in learner_reason(envelopes[7])
    assert "(α)" in learner_reason(envelopes[8])
    assert "M là trung điểm SA" in learner_reason(envelopes[10])

    # End-to-end `/api/analyze` refusal must also have clean learner_reason
    monkeypatch.setenv("ALLOW_LIVE_AI", "0")
    monkeypatch.setenv("GEMINI_API_KEY", "")
    monkeypatch.setenv("HYBRID_ROUTE_MODE", "local-first")
    with TestClient(M.app) as raw_client:
        client = sign_in(raw_client)
        res = client.post(
            "/api/analyze",
            json={
                "input": {
                    "type": "text",
                    "content": "Cho hình chóp S.ABC có đáy ABC là tam giác đều. Tính thể tích khối chóp S.ABC.",
                }
            },
        )
    assert res.status_code == 200
    env_resp = res.json()["envelope"]
    assert env_resp["status"] == "unsupported"
    _assert_clean_student_text(env_resp["learner_reason"], "/api/analyze MISSING_DIMENSION")


def _configure_worker_env(monkeypatch: pytest.MonkeyPatch) -> bool:
    py = ROOT / ".superpowers" / "ocr-venv" / "Scripts" / "python.exe"
    tess = ROOT / ".superpowers" / "tessdata_fast"
    if not py.exists() or not tess.exists():
        return False
    monkeypatch.setenv("LOCAL_OCR_PYTHON", str(py))
    monkeypatch.setenv("LOCAL_OCR_TESSDATA", str(tess))
    monkeypatch.setenv("ALLOW_LIVE_AI", "0")
    monkeypatch.setenv("GEMINI_API_KEY", "")
    monkeypatch.setenv("HYBRID_ROUTE_MODE", "local-first")
    LO.clear_local_ocr_cache()
    return True


def _render_math_png_b64() -> str:
    img = Image.new("RGB", (1400, 220), "white")
    draw = ImageDraw.Draw(img)
    try:
        font = ImageFont.truetype("C:/Windows/Fonts/arial.ttf", 32)
    except OSError:
        font = ImageFont.load_default()
    draw.text((32, 35), "Cho hình chóp S.ABCD có đáy ABCD là hình vuông cạnh 2a.", fill="black", font=font)
    draw.text((32, 95), "Biết SA vuông góc với (ABCD) và SA = 3a. Tính thể tích khối chóp S.ABCD.", fill="black", font=font)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return base64.b64encode(buf.getvalue()).decode("ascii")


def test_ocr_confirmation_and_verified_input_provenance_contracts(monkeypatch):
    if not _configure_worker_env(monkeypatch):
        pytest.skip("Isolated OCR worker virtualenv not installed in worktree")
    try:
        b64 = _render_math_png_b64()
        with TestClient(M.app) as raw_client:
            client = sign_in(raw_client)
            prep_res = client.post(
                "/api/input/prepare",
                json={"content": b64, "mime_type": "image/png", "filename": "sample.png"},
            )
            assert prep_res.status_code == 200, prep_res.text
            prep = prep_res.json()
            prov = prep.get("provenance") or {}
            assert prov.get("confirmation_contract_version") == "ocr-confirmation-provenance/1"
            for key in ("raw_ocr_text_sha256", "prepared_text_sha256", "prepared_region_sha256"):
                val = prov.get(key)
                assert isinstance(val, str) and len(val) == 64 and all(c in "0123456789abcdef" for c in val.lower()), (key, val)

            canonical_text = (
                "Cho hình chóp S.ABCD có đáy ABCD là hình vuông cạnh 2a. "
                "Biết SA vuông góc với mặt phẳng (ABCD) và SA = 3a. "
                "Tính thể tích khối chóp S.ABCD."
            )
            raw_sha = hashlib.sha256(canonical_text.encode("utf-8")).hexdigest()
            reg_sha = prov["prepared_region_sha256"]

            # 1) Unmodified local_ocr_auto_verified
            r_auto = client.post(
                "/api/analyze",
                json={
                    "input": {
                        "type": "text",
                        "content": canonical_text,
                        "source_provenance": {
                            "origin": "local_ocr_auto_verified",
                            "raw_ocr_text_sha256": raw_sha,
                            "prepared_region_sha256": reg_sha,
                            "student_edited": False,
                            "confirmed_span_count": 0,
                        },
                    }
                },
            )
            assert r_auto.status_code == 200, r_auto.text
            ip_auto = r_auto.json()["input_provenance"]
            assert ip_auto["contract_version"] == "verified-input-provenance/1"
            assert ip_auto["origin"] == "local_ocr_auto_verified"
            assert ip_auto["edited_from_raw_ocr"] is False
            assert ip_auto["counted_as_unmodified_auto_ocr"] is True

            # 2) Span-confirmed student review
            edited_text = canonical_text.replace("SA = 3a.", "SA = 4a.")
            r_span = client.post(
                "/api/analyze",
                json={
                    "input": {
                        "type": "text",
                        "content": edited_text,
                        "source_provenance": {
                            "origin": "local_ocr_student_confirmed",
                            "raw_ocr_text_sha256": raw_sha,
                            "prepared_region_sha256": reg_sha,
                            "student_edited": True,
                            "confirmed_span_count": 2,
                        },
                    }
                },
            )
            assert r_span.status_code == 200, r_span.text
            ip_span = r_span.json()["input_provenance"]
            assert ip_span["origin"] == "local_ocr_student_confirmed"
            assert ip_span["confirmed_span_count"] == 2
            assert ip_span["edited_from_raw_ocr"] is True
            assert ip_span["counted_as_unmodified_auto_ocr"] is False

            # 3) Whole-draft edit claiming local_ocr_auto_verified MUST be downgraded by server
            r_downgrade = client.post(
                "/api/analyze",
                json={
                    "input": {
                        "type": "text",
                        "content": canonical_text.replace("SA = 3a.", "SA = 5a."),
                        "source_provenance": {
                            "origin": "local_ocr_auto_verified",
                            "raw_ocr_text_sha256": raw_sha,
                            "prepared_region_sha256": reg_sha,
                            "student_edited": False,
                            "confirmed_span_count": 0,
                        },
                    }
                },
            )
            assert r_downgrade.status_code == 200, r_downgrade.text
            ip_down = r_downgrade.json()["input_provenance"]
            assert ip_down["declared_origin"] == "local_ocr_auto_verified"
            assert ip_down["origin"] == "local_ocr_student_confirmed"
            assert ip_down["edited_from_raw_ocr"] is True
            assert ip_down["counted_as_unmodified_auto_ocr"] is False
    finally:
        LO.shutdown_local_ocr()


def test_multi_problem_page_isolation_ext_prt_03_and_ext_prt_08(monkeypatch):
    if not _configure_worker_env(monkeypatch):
        pytest.skip("Isolated OCR worker virtualenv not installed in worktree")
    ext03 = ROOT / ".superpowers" / "external_image_cache" / "hd_q_7907931.jpg"
    ext08 = ROOT / ".superpowers" / "external_image_cache" / "hd_q_7509702.jpg"
    assert ext03.exists() and ext08.exists()

    try:
        b03 = base64.b64encode(ext03.read_bytes()).decode("ascii")
        b08 = base64.b64encode(ext08.read_bytes()).decode("ascii")
        with TestClient(M.app) as raw_client:
            client = sign_in(raw_client)

            # ext_prt_03: 2 isolated problems (`text-p1-1`, `text-p1-2`)
            r03 = client.post(
                "/api/input/prepare",
                json={"content": b03, "mime_type": "image/jpeg", "filename": "hd_q_7907931.jpg"},
            )
            assert r03.status_code == 200, r03.text
            d03 = r03.json()
            assert d03["status"] == "needs_selection"
            cands03 = d03["candidates"]
            assert len(cands03) == 2
            cid0, cid1 = cands03[0]["candidate_id"], cands03[1]["candidate_id"]
            assert cid0 != cid1

            sub0 = client.post(
                "/api/input/prepare",
                json={
                    "content": b03,
                    "mime_type": "image/jpeg",
                    "filename": "hd_q_7907931.jpg",
                    "selected_candidate_id": cid0,
                },
            ).json()
            sub1 = client.post(
                "/api/input/prepare",
                json={
                    "content": b03,
                    "mime_type": "image/jpeg",
                    "filename": "hd_q_7907931.jpg",
                    "selected_candidate_id": cid1,
                },
            ).json()
            t0 = sub0.get("problem_text") or ""
            t1 = sub1.get("problem_text") or ""
            assert t0 and t1 and t0 != t1
            # Candidate 1 belongs to S.ABCD (Câu 32) without leaking Câu 33; Candidate 2 belongs to Câu 33 (S.ABC)
            assert "33" not in t0
            assert "32" not in t1

            # ext_prt_08: 4 bands, 0 wrong-served
            r08 = client.post(
                "/api/input/prepare",
                json={"content": b08, "mime_type": "image/jpeg", "filename": "hd_q_7509702.jpg"},
            )
            assert r08.status_code == 200, r08.text
            d08 = r08.json()
            assert d08["status"] == "needs_selection"
            cands08 = d08["candidates"]
            assert len(cands08) == 4
            for cand in cands08:
                sub = client.post(
                    "/api/input/prepare",
                    json={
                        "content": b08,
                        "mime_type": "image/jpeg",
                        "filename": "hd_q_7509702.jpg",
                        "selected_candidate_id": cand["candidate_id"],
                    },
                ).json()
                txt = sub.get("problem_text") or ""
                if txt and sub.get("status") != "needs_confirmation":
                    routed = AIR.route_text_input(txt, allow_live_ai=False, input_kind="image")
                    assert routed.status != "SERVED"
    finally:
        LO.shutdown_local_ocr()


def test_fe4_scene3d_auxiliary_role_metadata_distinguished_from_primary_solid():
    p25 = RUNS_DIR / "controlled-vision-real-image-validation" / "new_in_scope_image_manifest.json"
    rmap = {it["case_id"]: it["statement"] for it in json.loads(p25.read_text(encoding="utf-8"))["items"]}

    r254 = run_typed_fact_next_v2_route(parse_geometry_problem_locally(rmap["vmmu_r254"]).payload)
    assert r254.status == "SERVED"
    objs254 = {o["id"]: o for o in r254.scene3d["objects"]}
    for aux_id in ("G_mid_BC", "G", "doan_gt_p5"):
        obj = objs254[aux_id]
        assert obj["display_group"] == ["construction"]
        assert obj["formation_roles"] == ["CONSTRUCT_AUXILIARY_GEOMETRY"]
    assert objs254["day_ABC"]["formation_roles"] == ["CONSTRUCT_BASE"]
    assert objs254["canh_ben_A_A_prime"]["formation_roles"] == ["CONSTRUCT_LATERAL_BOUNDARY"]
    assert "solid" in objs254["khoi_ABC_A_primeB_primeC_prime"]["display_group"]

    r277 = run_typed_fact_next_v2_route(parse_geometry_problem_locally(rmap["vmmu_r277"]).payload)
    assert r277.status == "SERVED"
    objs277 = {o["id"]: o for o in r277.scene3d["objects"]}
    for aux_id in ("M1", "M2", "M3", "M", "N", "P"):
        obj = objs277[aux_id]
        assert obj["display_group"] == ["construction"]
        assert obj["formation_roles"] == ["CONSTRUCT_AUXILIARY_GEOMETRY"]
    assert objs277["khoi_O_ABC"]["formation_roles"] == ["CLOSE_SOLID"]


def test_stem_fraction_above_choice_band_and_subquestion_marker_hygiene():
    from app.ingestion.ocr_reconcile import reconcile_local_ocr

    raw_frac = {
        "width": 2480,
        "height": 420,
        "engines": {
            "rapidocr": {
                "lines": [
                    {"text": "Câu 26. Cho hình chóp tam giác đều S.ABC và có cạnh đáy bằng a, cạnh bên", "bbox": [137, 1, 1744, 71], "conf": 0.99},
                    {"text": "2a", "bbox": [256, 69, 326, 126], "conf": 0.99},
                    {"text": "bằng", "bbox": [137, 95, 253, 164], "conf": 0.98},
                    {"text": "(tham khảo hình vẽ bên). Góc giữa cạnh bên và mặt đáy bằng", "bbox": [336, 97, 1580, 163], "conf": 0.99},
                    {"text": "3", "bbox": [268, 139, 312, 191], "conf": 0.99},
                    {"text": "A.90°.", "bbox": [200, 196, 356, 252], "conf": 0.99},
                    {"text": "B.45°.", "bbox": [722, 198, 877, 252], "conf": 0.99},
                    {"text": "√2", "bbox": [360, 260, 440, 310], "conf": 0.99},
                    {"text": "2", "bbox": [380, 315, 420, 365], "conf": 0.99},
                ],
            },
            "tesseract": {
                "lines": [
                    {"text": "Câu 26. Cho hình chóp tam giác đều S.ABC và có cạnh đáy bằng a, cạnh bên", "bbox": [140, 5, 1740, 70], "conf": 95},
                    {"text": "bằng (tham khảo hình vẽ bên). Góc giữa cạnh bên và mặt đáy bằng", "bbox": [140, 96, 1575, 165], "conf": 95},
                    {"text": "A. 90°. B. 45°.", "bbox": [200, 198, 875, 250], "conf": 95},
                ],
            },
        },
    }
    res_frac = reconcile_local_ocr(raw_frac)
    frac_spans = [s for s in res_frac["spans"] if s.get("reason") == "FRACTION_STRUCTURE_LOSS"]
    assert any(s.get("text") == "2a/3" for s in frac_spans), frac_spans
    assert not any(s.get("text") == "√2/2" for s in frac_spans), frac_spans

    raw_subq = {
        "width": 1024,
        "height": 220,
        "engines": {
            "rapidocr": {
                "lines": [
                    {"text": "Cho hình chóp S.ABCD có đáy là hình vuông cạnh a, SA vuông góc với đáy.", "bbox": [20, 15, 980, 55], "conf": 0.99},
                    {"text": "b. Tính khoảng cách từ điểm s đến mặt phẳng (SBD).", "bbox": [20, 85, 860, 130], "conf": 0.99},
                ],
            },
            "tesseract": {
                "lines": [
                    {"text": "Cho hình chóp S.ABCD có đáy là hình vuông cạnh a, SA vuông góc với đáy.", "bbox": [20, 15, 980, 55], "conf": 96},
                    {"text": "b. Tính khoảng cách từ điểm s đến mặt phẳng (SBD).", "bbox": [20, 85, 860, 130], "conf": 96},
                ],
            },
        },
    }
    res_subq = reconcile_local_ocr(raw_subq)
    lv_spans = [s for s in res_subq["spans"] if s.get("reason") == "LOWERCASE_VERTEX_LABEL"]
    assert all(s.get("text") != "b." for s in lv_spans), lv_spans
    assert any(s.get("text") == "s" and s.get("alternatives") == ["S", "s"] for s in lv_spans), lv_spans
