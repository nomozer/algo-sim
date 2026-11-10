# -*- coding: utf-8 -*-
"""Gate 3 TDD & Regression Suite: Verified Image-to-Geometry Pipeline (`Section VI`, Gate D).

Covers:
1. Fail-closed `verify_ocr_input_fidelity` & `reconcile_dual_ocr_texts` hardening:
   - Dual-OCR agreement MUST NOT bypass `has_diagram=True` (mixed text + diagram) or `is_handwritten=True`.
   - Diagram-reference phrases (`như hình bên`, `tham khảo hình bên`, `xem hình vẽ`, `ghi trên hình`) block text-only OCR.
   - Shared dual-OCR corruptions (degree `600°`, vertex comma `S,ABCD`, digit-in-polygon `S.A8CD`, stacked fraction line-break)
     fail closed at the Input Fidelity Gate (`0` corrupted OCR inputs reaching Exact Kernel).
2. Four distinct input pipelines (`Text`, `Printed image`, `Handwritten image`, `Mixed text + diagram`).
3. Recorded/Mock Vision fallback (`Image -> Vision -> Verified Transcription -> Local Parser -> Planner -> Exact Kernel -> Scene3D`),
   `TypedFactNext` fallback when outside local parser grammar, OCR-vs-Vision conflict confirmation (`VISION_NEEDS_CONFIRMATION`),
   and safe rejection of diagram-only / multi-problem / incomplete inputs (`ALLOW_LIVE_AI = 0`, `0` live Gemini calls).
4. Cached 38-image external corpus verification (`0` Git-tracked unverified images, `0 MB` VietOCR-HW default import bloat,
   and `ORACLE_TEXT_DOWNSTREAM_REPLAY` strictly separated from raw OCR accuracy).
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import subprocess
import sys

import pytest

from app.ai.adaptive_input_router import (
    LOCAL_OCR_PRODUCTION_STATUS,
    reconcile_dual_ocr_texts,
    route_edited_text_input,
    route_image_or_prepare_outcome,
    route_text_input,
    verify_ocr_input_fidelity,
)
from app.ai.local_geometry_parser import LOCAL_PARSE_COMPLETE
from app.ai.typed_fact_next_extraction import ReplayExtractor
from app.simulation.geometry_functions.construction_continuity import validate_construction_continuity

ROOT = Path(__file__).resolve().parents[3]
EXT_MANIFEST_PATH = (
    ROOT
    / "docs"
    / "evaluation"
    / "geometry"
    / "runs"
    / "real-world-printed-handwriting-acquisition"
    / "external_image_corpus_manifest.json"
)
EXT_CACHE_DIR = ROOT / ".superpowers" / "external_image_cache"


def test_dual_ocr_agreement_never_bypasses_mixed_diagram_handwritten_or_shared_symbol_corruption():
    clean_text = (
        "Cho hình chóp S.ABCD có đáy ABCD là hình vuông cạnh a, "
        "SA ⊥ (ABCD) và SA = 2a. Tính thể tích khối chóp S.ABCD."
    )
    # Slight prime/format variation where dual-OCR reconciliation would run in `route_image_or_prepare_outcome`
    primary_ocr = (
        "Cho hình lăng trụ đứng ABCD.A'B°C'D' có đáy ABCD là hình vuông cạnh a, "
        "AA' = 2a. Tính thể tích khối lăng trụ ABCD.A'B'C'D'."
    )
    secondary_ocr = (
        "Cho hinh lang tru dung ABCD.A'B'C'D' co day ABCD la hinh vuong canh a, "
        "AA' = 2a. Tinh the tich khoi lang tru ABCD.A'B'C'D'."
    )

    # 1) Mixed text + diagram (`has_diagram=True`) MUST NOT bypass Vision via dual-OCR reconciliation!
    rec_diag = reconcile_dual_ocr_texts(primary_ocr, secondary_ocr, has_diagram=True)
    assert rec_diag["reconciled"] is False

    prep_rejected = {
        "status": "rejected",
        "source_kind": "image",
        "reason_code": "LIVE_AI_DISABLED",
        "candidates": [{"candidate_id": "r1", "has_figure": True}],
        "metrics": {"vlm_calls": 0, "processing_ms": 5.0},
    }
    out_diag = route_image_or_prepare_outcome(
        prep_rejected,
        allow_live_ai=False,
        local_ocr_text=primary_ocr,
        secondary_ocr_text=secondary_ocr,
        allow_verified_local_ocr=True,
        has_diagram=True,
    )
    assert out_diag.telemetry.chosen_route != "LOCAL_OCR_VERIFIED_ZERO_AI"
    assert out_diag.status != "SERVED"

    # 2) Handwritten modality (`is_handwritten=True`) MUST NOT bypass Vision via local OCR alone
    fid_hw = verify_ocr_input_fidelity(clean_text, secondary_ocr_text=clean_text, is_handwritten=True)
    assert fid_hw["fidelity_passed"] is False
    assert "diagram_dependency_and_cross_engine" in fid_hw["failed_checks"]

    # 3) Real VMMU diagram-reference phrases (`như hình bên`, `tham khảo hình bên`, `xem hình vẽ`, `ghi trên hình`)
    for phrase in ("(như hình bên)", "(tham khảo hình bên)", "(xem hình vẽ)", "chiều cao ghi trên hình"):
        txt_with_diag_ref = (
            f"Cho hình chóp S.ABCD có đáy ABCD là hình vuông cạnh a, SA ⊥ (ABCD) và SA = 2a {phrase}. "
            "Tính thể tích khối chóp S.ABCD."
        )
        fid_ref = verify_ocr_input_fidelity(txt_with_diag_ref, secondary_ocr_text=txt_with_diag_ref)
        assert fid_ref["fidelity_passed"] is False, f"Diagram phrase {phrase!r} must block text-only OCR"

    # 4) Shared dual-OCR corruptions (both OCR engines output the same corrupted math symbol!)
    shared_corruptions = [
        # Degree `60°` misread as `600°` by both OCR engines
        "Cho hình chóp S.ABCD có đáy ABCD là hình vuông cạnh a, SA ⊥ (ABCD) và SB tạo với mặt phẳng (ABCD) một góc 600°. Tính thể tích khối chóp S.ABCD.",
        # Solid dot misread as comma `S,ABCD`
        "Cho hình chóp S,ABCD có đáy ABCD là hình vuông cạnh a, SA ⊥ (ABCD) và SA = 2a. Tính thể tích khối chóp S,ABCD.",
        # Italic vertex `B` misread as `8` inside polygon `S.A8CD`
        "Cho hình chóp S.A8CD có đáy A8CD là hình vuông cạnh a, SA ⊥ (A8CD) và SA = 2a. Tính thể tích khối chóp S.A8CD.",
        # Stacked fraction linearized with horizontal bar line
        "Cho hình chóp S.ABCD có đáy ABCD là hình vuông cạnh a, SA ⊥ (ABCD) và SA =\na√2\n---\n2\nTính thể tích khối chóp S.ABCD.",
    ]
    for corrupt_txt in shared_corruptions:
        rec_shared = reconcile_dual_ocr_texts(corrupt_txt, corrupt_txt)
        assert rec_shared["reconciled"] is False, f"Shared corruption slipped past dual-OCR gate: {corrupt_txt!r}"
        fid_shared = verify_ocr_input_fidelity(corrupt_txt, secondary_ocr_text=corrupt_txt)
        assert fid_shared["fidelity_passed"] is False, f"Shared corruption slipped past fidelity gate: {corrupt_txt!r}"


def test_four_distinct_input_routes_and_recorded_vision_fallback_to_scene3d():
    # Pipeline 1: Text input -> Local Parser -> Hybrid /4 (0 AI calls, Gate 1 + Gate 2 composition)
    text_problem = (
        "Cho hình chóp S.ABCD có đáy ABCD là hình thoi cạnh a, góc BAD bằng 60°, "
        "SA ⊥ (ABCD) và SC tạo với mặt phẳng đáy một góc 45°. Tính thể tích khối chóp S.ABCD."
    )
    out_t = route_text_input(text_problem, allow_live_ai=False)
    assert out_t.status == "SERVED"
    assert out_t.telemetry.chosen_route == "LOCAL_DETERMINISTIC_HYBRID"
    assert out_t.telemetry.total_provider_calls == 0
    assert list(out_t.response["route_d"]["answers"].values()) == ["a³/2"]
    assert validate_construction_continuity(out_t.response["envelope"]["scene3d"]) == []

    # Pipeline 2: Printed self-contained image (no diagram) with verified clean dual-OCR -> 0 AI calls
    clean_printed_ocr = (
        "Cho hình chóp S.ABCD có đáy ABCD là hình thang vuông tại A và B, "
        "AD = 2a, BC = a, AB = a, SA ⊥ (ABCD) và SA = a√3. Tính thể tích khối chóp S.ABCD."
    )
    out_p = route_image_or_prepare_outcome(
        {"status": "rejected", "source_kind": "image", "reason_code": "LIVE_AI_DISABLED", "metrics": {"vlm_calls": 0}},
        allow_live_ai=False,
        local_ocr_text=clean_printed_ocr,
        secondary_ocr_text=clean_printed_ocr,
        allow_verified_local_ocr=True,
        has_diagram=False,
    )
    assert out_p.status == "SERVED"
    assert out_p.telemetry.chosen_route == "LOCAL_OCR_VERIFIED_ZERO_AI"
    assert out_p.telemetry.total_provider_calls == 0
    assert list(out_p.response["route_d"]["answers"].values()) == ["a³√3/2"]

    # Pipeline 3: Handwritten image (`hd_a_6043187` real corrupted VietOCR-HW output vs Recorded Vision fallback)
    recorded_vietocr_hw_b1 = (
        "Cho hình lăng trụ đứng ABC-ABC có đáy ABC lội tam giác vuông tại B, "
        "AB=a; AC=aV7, góc giữa đường thẳng Bố với mặt phẳng đây = 60 Tính thể tích của khối lặng trụ 2/2/2/2"
    )
    assert verify_ocr_input_fidelity(recorded_vietocr_hw_b1)["fidelity_passed"] is False

    recorded_vision_b1 = {
        "status": "ready",
        "source_kind": "image",
        "problem_text": (
            "Cho hình lăng trụ đứng ABC.A'B'C' có đáy ABC là tam giác vuông tại B, "
            "AB = a ; AC = a√3 , góc giữa đường thẳng BC' với mặt phẳng đáy = 60°. Tính thể tích của khối lăng trụ"
        ),
        "provenance": {"extraction_method": "vlm", "verification_mode": "RECORDED_REPLAY_VERIFIED"},
        "metrics": {"vlm_calls": 1, "processing_ms": 120.0},
    }
    out_hw_vis = route_image_or_prepare_outcome(
        recorded_vision_b1,
        allow_live_ai=False,
        local_ocr_text=recorded_vietocr_hw_b1,
        has_diagram=True,
    )
    assert out_hw_vis.status == "SERVED"
    assert out_hw_vis.telemetry.chosen_route == "VISION_THEN_LOCAL_DETERMINISTIC"
    assert out_hw_vis.telemetry.gemini_vision_calls == 1
    assert out_hw_vis.telemetry.gemini_typed_fact_calls == 0
    assert list(out_hw_vis.response["route_d"]["answers"].values()) == ["a³√3"]
    assert validate_construction_continuity(out_hw_vis.response["envelope"]["scene3d"]) == []

    # Pipeline 4: Vision -> TypedFactNext fallback (when Vision transcription uses phrasing outside Local Parser grammar),
    # plus OCR-vs-Vision conflict confirmation (`VISION_NEEDS_CONFIRMATION`) + user edit confirmation loop (`0` new Vision calls),
    # plus diagram-only / multi-problem safe rejection (`LOCAL_CV_REJECTED_OR_SELECTION`).
    unparsed_vision_text = (
        "Cho hình chóp S.ABC có đáy ABC là tam giác đều cạnh a, SA ⊥ (ABC), SA = a, "
        "mặt bên (SBC) hợp ngữ cảnh hiếm chưa có trong parser cục bộ. Tính thể tích khối chóp S.ABC."
    )
    mock_tfn_payload = {
        "schema_version": "typed-fact-next/2",
        "problem_text": unparsed_vision_text,
        "length_unit": "a",
        "solids": [
            {
                "solid_id": "s1",
                "solid_type": "pyramid",
                "notation": "S.ABC",
                "quote": "Cho hình chóp S.ABC",
            }
        ],
        "premises": [],
        "relations": [],
        "derived_sections": [],
        "simulation_goals": [{"goal_id": "sg1", "kind": "construct_object", "target_solid_id": "s1", "quote": "Cho hình chóp S.ABC"}],
        "math_goals": [{"goal_id": "q1", "kind": "measurement", "goal_type": "volume", "target": {"solid_id": "s1"}, "quote": "Tính thể tích khối chóp S.ABC"}],
        "unresolved": [
            {
                "unresolved_id": "u1",
                "kind": "unrecognized_term",
                "quote": "mặt bên (SBC) hợp ngữ cảnh hiếm chưa có trong parser cục bộ",
                "missing_roles": ["relation_kind"],
                "candidate_relations": [],
            }
        ],
    }
    out_vis_ai = route_image_or_prepare_outcome(
        {
            "status": "ready",
            "source_kind": "image",
            "problem_text": unparsed_vision_text,
            "provenance": {"extraction_method": "vlm"},
            "metrics": {"vlm_calls": 1, "processing_ms": 95.0},
        },
        fallback_typed_fact_extractor=ReplayExtractor({unparsed_vision_text: mock_tfn_payload}),
        allow_live_ai=True,
    )
    assert out_vis_ai.telemetry.chosen_route == "VISION_THEN_AI_FALLBACK"
    assert out_vis_ai.telemetry.gemini_vision_calls == 1
    assert out_vis_ai.telemetry.gemini_typed_fact_calls == 1

    # OCR vs Vision numeric conflict (`SA = 3a` vs `SA = 8a`) -> `VISION_NEEDS_CONFIRMATION`
    ocr_conflict_txt = "Cho hình chóp S.ABCD có đáy ABCD là hình vuông cạnh a, SA ⊥ (ABCD) và SA = 3a. Tính thể tích khối chóp S.ABCD."
    vis_conflict_txt = "Cho hình chóp S.ABCD có đáy ABCD là hình vuông cạnh a, SA ⊥ (ABCD) và SA = 8a. Tính thể tích khối chóp S.ABCD."
    out_conf = route_image_or_prepare_outcome(
        {
            "status": "ready",
            "source_kind": "image",
            "problem_text": vis_conflict_txt,
            "provenance": {"extraction_method": "vlm"},
            "metrics": {"vlm_calls": 1, "processing_ms": 80.0},
        },
        allow_live_ai=False,
        local_ocr_text=ocr_conflict_txt,
    )
    assert out_conf.status == "NEEDS_CONFIRMATION"
    assert out_conf.telemetry.chosen_route == "VISION_NEEDS_CONFIRMATION"

    # Learner confirms `SA = 3a` via `route_edited_text_input` -> `0` new Vision calls, `0` TypedFactNext calls!
    out_edited = route_edited_text_input(ocr_conflict_txt, previous_vision_calls=1, allow_live_ai=False)
    assert out_edited.status == "SERVED"
    assert out_edited.telemetry.total_provider_calls == 0
    assert list(out_edited.response["route_d"]["answers"].values()) == ["a³"]

    # Diagram-only image rejection -> `LOCAL_CV_REJECTED_OR_SELECTION`
    out_diag_only = route_image_or_prepare_outcome(
        {
            "status": "rejected",
            "source_kind": "image",
            "reason_code": "DIAGRAM_WITHOUT_STATEMENT",
            "metrics": {"vlm_calls": 0, "processing_ms": 4.0},
        },
        allow_live_ai=False,
    )
    assert out_diag_only.status == "REJECTED"
    assert out_diag_only.telemetry.chosen_route == "LOCAL_CV_REJECTED_OR_SELECTION"
    assert out_diag_only.telemetry.total_provider_calls == 0


def test_vietocr_hw_stays_unloaded_by_default_and_external_corpus_oracle_downstream_replay():
    assert LOCAL_OCR_PRODUCTION_STATUS == "LOCAL_OCR_DIAGNOSTIC_ONLY"
    assert "onnxruntime" not in sys.modules or not any("vietocr" in m.lower() for m in sys.modules)

    assert EXT_MANIFEST_PATH.exists()
    manifest = json.loads(EXT_MANIFEST_PATH.read_text(encoding="utf-8"))
    assert manifest["total_distinct_external_images"] == 38

    # Verify zero external images are tracked in Git
    git_ls = subprocess.run(
        ["git", "ls-files", ".superpowers/external_image_cache"],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
        check=False,
    )
    assert git_ls.stdout.strip() == ""

    if EXT_CACHE_DIR.exists():
        for item in manifest["items"]:
            img_p = EXT_CACHE_DIR / item["filename"]
            assert img_p.exists(), f"Missing cached external image {item['filename']}"
            assert hashlib.sha256(img_p.read_bytes()).hexdigest() == item["original_file_sha256"]

    # Evaluate `ORACLE_TEXT_DOWNSTREAM_REPLAY` (explicitly NOT raw OCR!) on all 17 complete statements
    served_ids: dict[str, str] = {}
    missing_dim_ids: list[str] = []
    for item in manifest["items"]:
        if not item.get("has_complete_problem"):
            continue
        for idx, stmt in enumerate(item.get("verbatim_problem_texts", []), 1):
            key = f"{item['image_id']}#{idx}"
            out = route_text_input(stmt, allow_live_ai=False)
            assert out.telemetry.total_provider_calls == 0
            if out.status == "SERVED":
                ans = next(iter(out.response["route_d"]["answers"].values()))
                served_ids[key] = ans
                assert out.telemetry.local_parse_status == LOCAL_PARSE_COMPLETE
                assert validate_construction_continuity(out.response["envelope"]["scene3d"]) == []
            else:
                rc = (out.response.get("envelope") or {}).get("reason_code")
                if rc == "MISSING_DIMENSION":
                    missing_dim_ids.append(key)

    # Gate 1 + Gate 2 promoted `ext_prt_01_hd_q_5259753#1` ("a³√3/3") and `ext_hw_b1_01_hd_a_6043187#1` ("a³√3")
    # alongside `ext_prt_03_hd_q_7907931#2` ("a³/4") and `ext_prt_09_vmmu_page_r4#1` ("2").
    # Run `real-world-end-to-end-reliability` showed the two former `MISSING_DIMENSION` refusals were FALSE refusals:
    # d(C, (ABB'A')) = CB = AB = 6 (published key D. 6) and d(B, (SAC)) = BO = a√2/2 do not depend on the unstated height.
    # They are now served with a height-invariance certificate and an illustrative scene -> 6/17 solved, 0 wrong-served.
    assert served_ids == {
        "ext_prt_01_hd_q_5259753#1": "a³√3/3",
        "ext_prt_02_hd_q_7922924#1": "6",
        "ext_prt_03_hd_q_7907931#1": "a√2/2",
        "ext_prt_03_hd_q_7907931#2": "a³/4",
        "ext_prt_04_hd_q_8436784#1": "1/2",
        "ext_prt_05_hd_q_7451806#1": "6/5",
        "ext_prt_06_hd_q_1084979#1": "a√15/5",
        "ext_prt_07_hd_q_7958052#1": "4,7",
        "ext_prt_09_vmmu_page_r4#1": "2",
        "ext_prt_11_vmmu_page_r10#1": "30°",
        "ext_prt_12_vmmu_page_r11#1": "2√3",
        "ext_hw_b1_01_hd_a_6043187#1": "a³√3",
    }
    assert sorted(missing_dim_ids) == []
