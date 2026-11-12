# -*- coding: utf-8 -*-
"""Image-first OCR (run `image-first-ocr-verified-geometry`): đối chiếu OCR theo bố cục, tuyến OCR local,
và nhãn câu hỏi con trong Parser/Source Gate. Không cần engine OCR thật (dữ liệu OCR tổng hợp có hộp bao)."""
from __future__ import annotations

import asyncio
import base64
import io

import pytest

from app.ingestion import local_ocr_route as LR
from app.ingestion.ocr_reconcile import has_shared_corruption, norm_math, reconcile_local_ocr
from app.ai.adaptive_input_router import compare_ocr_and_vision_facts


@pytest.mark.parametrize("phrase,left,right", [("cạnh", "2a", "a"), ("chiều cao bằng", "3a", "2a")])
def test_vision_comparison_detects_worded_dimension_conflict(phrase, left, right):
    before = f"Cho hình chóp S.ABCD có đáy là hình vuông {phrase} {left}, SA = a√3. Tính thể tích khối chóp."
    after = before.replace(f"{phrase} {left}", f"{phrase} {right}")
    comparison = compare_ocr_and_vision_facts(before, after)
    assert comparison["has_conflict"] is True
    assert comparison["requires_user_confirmation"] is True
    assert "NUMERIC_ASSIGNMENT_CONFLICT" in comparison["conflict_codes"]


def test_vision_comparison_allows_reordered_equivalent_measurements():
    comparison = compare_ocr_and_vision_facts(
        "Cho hình chóp S.ABCD có cạnh đáy 2a và chiều cao 3a. Tính thể tích khối chóp.",
        "Cho hình chóp S.ABCD có chiều cao 3a và cạnh đáy 2a. Tính thể tích khối chóp.",
    )
    assert comparison["has_conflict"] is False


def test_vision_comparison_ignores_omitted_exam_header_number():
    text = "Cho hình chóp S.ABCD có cạnh đáy 2a và chiều cao 3a. Tính thể tích khối chóp."
    assert compare_ocr_and_vision_facts("Câu 1: " + text, text)["has_conflict"] is False
    assert compare_ocr_and_vision_facts(text, text.replace("2a", "2 a"))["has_conflict"] is False


def test_vision_comparison_retains_binding_between_worded_dimension_and_value():
    comparison = compare_ocr_and_vision_facts(
        "Cho hình chóp S.ABCD có cạnh đáy 2a và chiều cao 3a. Tính thể tích khối chóp.",
        "Cho hình chóp S.ABCD có cạnh đáy 3a và chiều cao 2a. Tính thể tích khối chóp.",
    )
    assert comparison["requires_user_confirmation"] is True


def _line(words: list[str], y: int, *, x0: int = 10, h: int = 30, cw: int = 14, conf: float = 95.0, gaps=None):
    out, x = [], x0
    for i, w in enumerate(words):
        wid = max(cw, cw * len(w))
        out.append({"text": w, "conf": conf, "bbox": [x, y, x + wid, y + h]})
        x += wid + (gaps[i] if gaps else cw)
    return {"text": " ".join(words), "conf": conf, "bbox": [x0, y, x - cw, y + h], "words": out}


def _raw(rapid_lines, tess_lines, w=1200, h=400):
    return {
        "width": w,
        "height": h,
        "engines": {
            "rapidocr": {"engine_version": "rapidocr test", "lines": rapid_lines},
            "tesseract": {"engine_version": "tesseract test", "lines": tess_lines},
        },
    }


def test_cross_family_agreement_verifies_and_diacritics_restored():
    r = [_line(["Cho", "hình", "chóp", "S.ABCD", "có", "đáy", "là", "tam", "giác,", "SA", "=", "a√3."], 10)]
    t = [_line(["Cho", "hình", "chóp", "S.ABCD", "có", "đáy", "là", "tam", "giác,", "SA", "=", "a√3."], 10)]
    rec = reconcile_local_ocr(_raw(r, t), min_agreeing_families=2)
    assert rec["extraction_verified"] is True, rec["blocking_reasons"]
    assert rec["draft_text"] == "Cho hình chóp S.ABCD có đáy là tam giác, SA = a√3."
    assert rec["used_ground_truth"] is False


def test_rapid_skeleton_plus_tess_diacritics_restore_vietnamese_without_ground_truth():
    # RapidOCR bỏ nguyên âm có dấu ("cnh", "mt"); Tesseract giữ dấu nhưng sai một dấu ("mật"); từ vựng ngữ pháp khôi phục.
    r = [_line(["cnh", "a,", "vuông", "góc", "vói", "mt", "đáy"], 10)]
    t = [_line(["cạnh", "a,", "vuông", "góc", "với", "mật", "day"], 10)]
    rec = reconcile_local_ocr(_raw(r, t), min_agreeing_families=2)
    assert rec["draft_text"] == "cạnh a, vuông góc với mặt đáy"
    # "a," chỉ được một họ... không: cả hai họ cùng đọc "a," ⇒ đã xác minh
    assert rec["extraction_verified"] is True, rec["uncertain_spans"]


def test_tam_giac_not_rewritten_to_tam_trong():
    r = [_line(["trọng", "tâm", "tam", "giác", "SBC."], 10)]
    t = [_line(["trong", "tâm", "tam", "giác", "SBC."], 10)]
    rec = reconcile_local_ocr(_raw(r, t), min_agreeing_families=2)
    assert "tam giác SBC." in rec["draft_text"]
    assert "tâm tâm" not in rec["draft_text"]


def test_math_disagreement_is_uncertain_with_alternatives_and_offsets():
    r = [_line(["góc", "60°,", "SA", "=", "a√3."], 10)]
    t = [_line(["góc", "602,", "SA", "=", "a3."], 10)]
    rec = reconcile_local_ocr(_raw(r, t), min_agreeing_families=2)
    assert rec["extraction_verified"] is False
    unc = {s["text"]: s for s in rec["uncertain_spans"]}
    assert "60°," in unc and unc["60°,"]["reason"] == "DEGREE_SYMBOL_DISAGREEMENT"
    assert "a√3." in unc and unc["a√3."]["reason"] == "RADICAL_DISAGREEMENT"
    for s in rec["uncertain_spans"]:
        assert rec["draft_text"][s["start"]:s["end"]] == s["text"]


def test_same_family_agreement_is_not_enough_under_two_family_policy():
    # Hai bộ đọc họ Paddle cùng "CC" (khung phát hiện chung cắt mất dấu ′); Tesseract đọc khác ⇒ chưa xác minh.
    r = [_line(["cạnh", "CC"], 10)]
    t = [_line(["cạnh", "CC'"], 10)]
    raw = _raw(r, t)
    slot = "L1:S2"
    one = reconcile_local_ocr(raw, adjudications={slot: {"rapidocr_latin_rec": "CC"}}, min_agreeing_families=1)
    two = reconcile_local_ocr(raw, adjudications={slot: {"rapidocr_latin_rec": "CC"}}, min_agreeing_families=2)
    assert any(s["text"] == "CC" and s["status"] == "verified" for s in one["spans"])
    bad = [s for s in two["uncertain_spans"] if s["kind"] == "math"]
    assert bad and bad[0]["reason"] == "SAME_FAMILY_AGREEMENT_ONLY"


def _reread_bleed(r, t, label, crop_reading):
    """Reconcile with a reread whose padded crop of `label` also caught the next glyph (`crop_reading`)."""
    raw = _raw(r, t)
    first = reconcile_local_ocr(raw, min_agreeing_families=2)
    slot = next(d["slot_key"] for d in first["disputed_math_slots"] if d["readings"].get("rapidocr") == label)
    adj = {slot: {"rapidocr_latin_rec": crop_reading, "tesseract_eng_line": crop_reading}}
    return reconcile_local_ocr(raw, adjudications=adj, min_agreeing_families=2)


def test_reread_crop_bleeding_into_next_token_does_not_duplicate_it():
    # Tesseract garbles the label; both rereads of the padded label crop also read the "=" next to it.
    r = [_line(["cạnh", "a√3,", "SA", "=", "a", "và"], 10)]
    t = [_line(["cạnh", "a√3,", "S4", "=", "a", "và"], 10)]
    rec = _reread_bleed(r, t, "SA", "SA =")
    assert "SA = a" in rec["draft_text"], rec["draft_text"]
    assert rec["draft_text"].count("=") == 1
    assert not any(s["status"] == "verified" and s["text"] == "SA=" for s in rec["spans"])


def test_reread_crop_bleeding_from_previous_token_is_trimmed():
    r = [_line(["góc", "(", "SBC", ")", "bằng", "60°."], 10)]
    t = [_line(["góc", "(", "5BC", ")", "bằng", "60°."], 10)]
    rec = _reread_bleed(r, t, "SBC", "( SBC")
    assert rec["draft_text"].count("(") == 1, rec["draft_text"]


def test_reread_reading_without_whitespace_is_not_trimmed():
    # "SA=" read as ONE token is not evidence of a neighbouring glyph; the slot must not silently become "SA".
    r = [_line(["cạnh", "a√3,", "SA", "=", "a", "và"], 10)]
    t = [_line(["cạnh", "a√3,", "S4", "=", "a", "và"], 10)]
    rec = _reread_bleed(r, t, "SA", "SA=")
    assert rec["draft_text"].count("=") == 2 or any(s["text"].startswith("SA") and s["status"] == "uncertain" for s in rec["spans"])


def test_shared_corruption_agreement_still_uncertain():
    assert has_shared_corruption("aV3") and has_shared_corruption("S,ABCD") and has_shared_corruption("600°")
    assert not has_shared_corruption("2BC") and not has_shared_corruption("A1B1C1")
    r = [_line(["SA", "=", "aV3."], 10)]
    t = [_line(["SA", "=", "aV3."], 10)]
    rec = reconcile_local_ocr(_raw(r, t), min_agreeing_families=2)
    assert any(s["reason"] == "SHARED_CORRUPTION_PATTERN" for s in rec["uncertain_spans"])
    assert rec["extraction_verified"] is False


def test_unit_superscript_normalized_not_a_new_fact():
    assert norm_math("12(cm2)") == norm_math("12(cm²)") == "12(cm²)"
    assert norm_math("m3") == "m³" and norm_math("AM2") == "AM2"


def test_stacked_fraction_in_stem_blocks_and_suggests_structure():
    r = [_line(["Tính", "tỉ", "số"], 10), _line(["KC"], 2, x0=300, h=16), _line(["KB"], 24, x0=300, h=16)]
    t = [_line(["Tính", "tỉ", "số"], 10)]
    rec = reconcile_local_ocr(_raw(r, t), min_agreeing_families=2)
    st = [s for s in rec["uncertain_spans"] if s["reason"] == "FRACTION_STRUCTURE_LOSS"]
    assert st and st[0]["text"] == "KC/KB" and st[0]["blocking"] is True
    assert "LAYOUT_STRUCTURE_SUSPECTED" in rec["blocking_reasons"]


def test_choice_region_uncertainty_does_not_block_stem():
    r = [_line(["Cho", "hình", "chóp", "S.ABCD."], 10), _line(["A.", "6√2."], 60), _line(["B.", "3√2."], 60, x0=300)]
    t = [_line(["Cho", "hình", "chóp", "S.ABCD."], 10), _line(["A.", "6/2."], 60), _line(["B.", "32."], 60, x0=300)]
    rec = reconcile_local_ocr(_raw(r, t), min_agreeing_families=2)
    assert rec["uncertain_spans"] and all(not s["blocking"] for s in rec["uncertain_spans"])
    assert rec["extraction_verified"] is True
    assert rec["draft_text"].splitlines()[1].startswith("A. 6√2.")


@pytest.mark.parametrize(
    "stem,figs,diag,expected",
    [
        (["Cho", "hình", "chóp", "S.ABC", "(tham", "khảo", "hình", "bên)."], [], [], "DIAGRAM_REFERENCED_BY_TEXT"),
        (["Cho", "hình", "chóp", "S.ABC."], [[600, 100, 900, 380]], ["SA=3"], "DIAGRAM_HAS_MEASUREMENTS"),
        (["Cho", "hình", "chóp", "S.ABC."], [[600, 100, 900, 380]], [], "DIAGRAM_PRESENT_UNREAD"),
        (["Cho", "hình", "chóp", "S.ABC."], [[600, 100, 900, 380]], ["S", "B"], "DIAGRAM_LABELS_ONLY_CONSISTENT"),
    ],
)
def test_diagram_dependency_classification(stem, figs, diag, expected):
    r = [_line(stem, 10)] + [_line([d], 150 + 40 * i, x0=650) for i, d in enumerate(diag)]
    t = [_line(stem, 10)]
    rec = reconcile_local_ocr(_raw(r, t), figure_bboxes=[tuple(f) for f in figs], min_agreeing_families=2)
    assert rec["diagram"]["classification"] == expected
    assert rec["diagram"]["blocking"] == (expected != "DIAGRAM_LABELS_ONLY_CONSISTENT")


# ── Tuyến OCR local trong /api/input/prepare ────────────────────────────────────────────────────────────────────

def _png_bytes() -> bytes:
    from PIL import Image, ImageDraw

    img = Image.new("RGB", (900, 260), "white")
    d = ImageDraw.Draw(img)
    for i in range(3):
        for j in range(18):
            d.rectangle((40 + 42 * j, 40 + 26 * i, 70 + 42 * j, 56 + 26 * i), fill="black")
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def _fake_rec(verified: bool) -> dict:
    r = [_line(["Cho", "hình", "lập", "phương", "ABCD.A'B'C'D'", "cạnh", "2."], 10),
         _line(["Tính", "độ", "dài", "AC'."], 60)]
    t = [_line(["Cho", "hình", "lập", "phương", "ABCD.A'B'C'D'", "cạnh", "2." if verified else "Z."], 10),
         _line(["Tính", "độ", "dài", "AC'."], 60)]
    rec = reconcile_local_ocr(_raw(r, t), min_agreeing_families=2)
    rec.update(ok=True, solve_text=LR._reflow(rec["draft_text"]), uncertain_ratio=0.1, low_quality=False,
               timing={"total_ms": 1.0}, raw_ocr={})
    return rec


@pytest.mark.parametrize("verified", [True, False])
def test_prepare_routes_local_ocr_without_any_ai(monkeypatch, verified):
    from app.ingestion import unified_input as U

    monkeypatch.setenv("ALLOW_LIVE_AI", "0")
    monkeypatch.setattr(LR, "run_local_ocr_route", lambda data, figs: _fake_rec(verified))

    async def _no_vision(*a, **k):  # pragma: no cover - phải không được gọi
        raise AssertionError("Vision must not be called")

    monkeypatch.setattr(U, "extract_problem_from_image", _no_vision)
    out = asyncio.run(U.prepare_unified_input(content=base64.b64encode(_png_bytes()).decode(), declared_mime="image/png", filename="de.png")).to_dict()
    assert out["metrics"]["vlm_calls"] == 0
    if verified:
        assert out["status"] == "ready"
        assert out["provenance"]["input_route"] == "LOCAL_OCR_VERIFIED"
        assert out["problem_text"].startswith("Cho hình lập phương ABCD.A'B'C'D' cạnh 2.")
    else:
        assert out["status"] == "needs_confirmation"
        assert out["provenance"]["input_route"] == "LOCAL_OCR_NEEDS_CONFIRMATION"
        toks = [t for t in out["uncertain_tokens"] if t["kind"] != "diagram"]
        assert toks and toks[0]["source"] == "local_ocr"
        t0 = toks[0]
        assert out["problem_text"][t0["span_start"]:t0["span_end"]] == t0["token"]
        assert "LIVE_AI_DISABLED" not in (out["learner_message"] or "")


def test_prepare_without_local_ocr_keeps_previous_live_ai_disabled_contract(monkeypatch):
    from app.ingestion import unified_input as U

    monkeypatch.setenv("ALLOW_LIVE_AI", "0")
    monkeypatch.delenv("LOCAL_OCR_PYTHON", raising=False)
    with pytest.raises(U.LiveVisionDisabledError):
        asyncio.run(U.prepare_unified_input(content=base64.b64encode(_png_bytes()).decode(), declared_mime="image/png", filename="de.png"))


# ── Nhãn câu hỏi con "a." / "b." (lỗi Parser chặn đề đã trích xuất đúng) ────────────────────────────────────────

_BASE = ("Câu 4: Cho hình chóp S.ABCD có đáy là hình vuông cạnh a, SA vuông góc với mặt đáy và SB tạo với đáy "
         "một góc 60°, G là trọng tâm tam giác SBC.")


def test_subquestion_labels_are_scaffolding_and_both_goals_solved(monkeypatch):
    from app.ai.adaptive_input_router import route_text_input

    monkeypatch.setenv("ALLOW_LIVE_AI", "0")
    text = _BASE + "\na. Tính thể tích khối chóp S.ABCD.\nb. Tính khoảng cách từ điểm G đến mặt phẳng (SBD)."
    out = route_text_input(text, allow_live_ai=False, input_kind="image")
    assert out.telemetry.local_parse_status == "LOCAL_PARSE_COMPLETE"
    answers = (out.response or {}).get("route_d", {}).get("answers")
    # Độc lập: SA = a·tan60° = a√3; V = a³√3/3; d(G,(SBD)) = (a/3)/√(7/3) = a√21/21.
    assert answers == {"q1": "a³√3/3", "q2": "a√21/21"}


def test_subquestion_label_does_not_hide_unread_question_words(monkeypatch):
    from app.ai.local_geometry_parser import parse_geometry_problem_locally

    text = _BASE + "\na. Tính thể tích khối chóp S.ABCD.\nb. Nhân đôi kết quả rồi tính khoảng cách từ điểm G đến mặt phẳng (SBD)."
    assert parse_geometry_problem_locally(text).status != "LOCAL_PARSE_COMPLETE"
