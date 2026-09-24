# -*- coding: utf-8 -*-
"""ẢNH → TẦNG A (provider giả) → VĂN BẢN → TẦNG B THẬT → scene3d. 0 lượt gọi mạng.

PHOTO_PROBLEM_TO_SCENE_END_TO_END §5 tầng B, §6, §9 "Semantic/renderer".

Điều được chứng minh ở đây là **không có pipeline thứ hai**: văn bản rút từ ảnh
đi qua `run_pipeline` y như một đề gõ tay. TẦNG B không bị giả — provider của nó
PHÁT LẠI byte đã đóng băng của lượt `thesis-final` (đối chiếu `raw_sha256`), nên
hợp đồng, chương trình, vòng sửa, kernel, checker và scene3d đều là mã sản phẩm
đang chạy.

⚠️ Đây là bằng chứng FIXTURE. Nó KHÔNG chứng minh một provider thật đọc được
một ảnh thật — xem báo cáo wave.
"""

from __future__ import annotations

import asyncio
import io
import json
import sys
from pathlib import Path

import pytest
from PIL import Image

from app.ingestion import image_extraction as ie
from app.ingestion.image import normalize_image

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import replay_demo_cases as RD  # noqa: E402
import replay_negative_boundaries as R  # noqa: E402

#: Một ca cho mỗi họ §2 cần phủ: chóp + mặt phẳng cắt, cầu, trụ, nón.
CA_DUONG = [
    ("p1_chop_thiet_dien_khoang_cach", "chóp + thiết diện"),
    ("p3_mat_cau_va_thiet_dien_tron", "cầu + mặt phẳng cắt"),
    ("p4_hinh_tru_the_tich_va_xung_quanh", "trụ"),
    ("p5_hinh_non_the_tich_va_xung_quanh", "nón"),
]


@pytest.fixture(scope="module")
def de_bai() -> dict[str, str]:
    return R.doc_de_bai()


def _doc_anh(monkeypatch, de: str, **thay):
    """TẦNG A với provider giả trả đúng đề — rồi phán quyết TẤT ĐỊNH thật."""
    ban = {
        "problem_text_verbatim": de, "problem_text_normalized": de, "math_expressions": [],
        "named_points": [], "named_lines": [], "named_planes": [], "named_solids": [],
        "given_relations": [], "has_diagram": False, "diagram_observations": [],
        "text_diagram_conflicts": [], "uncertain_tokens": [], "missing_regions": [],
        "confidence": 0.95, **thay,
    }

    async def fake(*a, **k):
        return json.dumps(ban, ensure_ascii=False)

    monkeypatch.setattr(ie, "call_gemini", fake)
    buf = io.BytesIO()
    Image.new("RGB", (64, 48), (255, 255, 255)).save(buf, format="PNG")
    return asyncio.run(ie.extract_problem_from_image(
        normalize_image(buf.getvalue()), "khoa-gia", cache_version=None))


def _phat_lai_theo_thu_tu(monkeypatch, cid: str, text: str) -> dict:
    """Phát lại TỪNG lượt gọi TẦNG B theo đúng thứ tự đã ghi — kể cả lượt SỬA.

    ⚠️ Không dùng `R.replay_case` cho ca dương: nó ánh xạ mỗi chặng tới MỘT bản
    ghi, và `p3` được phục vụ SAU một lượt sửa (`repair_1`). Thẩm quyền phát lại
    theo thứ tự nằm ở `replay_negative_boundaries.ProviderPhatLaiTheoThuTu`.
    """
    from app.ai import pipeline

    prov = R.ProviderPhatLaiTheoThuTu(R.doc_raw_theo_thu_tu(cid))
    monkeypatch.setattr(pipeline, "call_gemini", prov)
    with R.NetworkGuard() as g:
        env = asyncio.run(pipeline.run_pipeline(text, "REPLAY_KHONG_PHAI_KEY", semantic_route="serve"))
    return {"env": env, "calls": prov.calls, "con_lai": prov.con_lai(), "cham_mang": list(g.attempts)}


@pytest.mark.parametrize("cid, ho", CA_DUONG)
def test_van_ban_rut_tu_anh_DUNG_DUOC_canh_bang_pipeline_hien_co(monkeypatch, de_bai, cid, ho):
    de = de_bai[cid]
    kq = _doc_anh(monkeypatch, de)
    assert kq.assessment.status == "ready_for_review" and not kq.assessment.requires_confirmation
    assert kq.assessment.problem_text == de

    r = _phat_lai_theo_thu_tu(monkeypatch, cid, kq.assessment.problem_text)
    assert r["cham_mang"] == []
    assert r["con_lai"] == {"semantic_analyze": 0, "semantic_program": 0}, (ho, r["calls"])
    env = r["env"]
    assert env["status"] == "ok", (ho, env.get("stage_reached"), env.get("error_code"))
    canh = env.get("scene3d") or {}
    assert canh.get("objects"), f"{ho}: scene3d rỗng"
    assert canh.get("events"), f"{ho}: không có trace dựng"


def test_ca_ngoai_nang_luc_van_bi_TU_CHOI_dung_tang(monkeypatch, de_bai):
    """Khối tròn xoay tổng quát: đọc ảnh thành công KHÔNG làm hệ hứa dựng được."""
    cid = "n1_khoi_tron_xoay_tong_quat"
    kq = _doc_anh(monkeypatch, de_bai[cid])
    r = R.replay_case(cid, kq.assessment.problem_text)
    assert r["contract_fields"]["status"] == "unsupported"
    assert r["contract_fields"]["error_code"]
    assert r["contract_fields"]["learner_reason_present"]


def test_du_kien_KHONG_co_trong_de_bi_cong_grounding_chan():
    """Nguồn gốc dữ kiện được giữ ở TẦNG B bằng cổng đã có, không bằng trường mới."""
    c = RD._tim("name-contract-probe", "n4_giao_duong_mat_roi_do")
    r = RD._chay(c, co_grounding=True)
    assert r["ok"] is False and r["dung_o"] == "GROUNDING"


def test_scene_rong_KHONG_bao_gio_duoc_bay_ra(monkeypatch):
    """`pipeline._dung_scene3d` trả `None` cho cảnh rỗng — tiêm cảnh rỗng để thấy nó chặn."""
    from app.ai import pipeline
    from app.simulation.semantic_program import scene3d as scene3d_mod
    from app.simulation.semantic_program.request_contract import RequestContract
    from app.simulation.semantic_program.validator import validate_semantic_program

    c = RD._tim("name-contract-probe", "n2_lang_tru_xien_hai_vecto")
    spec = validate_semantic_program(c["normalized_program"]).spec
    hd = RequestContract.model_validate(c["analyze"]["raw_request_contract"])

    that = pipeline._dung_scene3d(spec, hd)
    assert that and that["objects"], "tiền điều kiện: ca này phải dựng được cảnh"

    monkeypatch.setattr(scene3d_mod, "build_scene3d", lambda *a, **k: {"objects": [], "events": []})
    assert pipeline._dung_scene3d(spec, hd) is None


def test_anh_chi_co_hinh_KHONG_toi_duoc_tang_B(monkeypatch):
    kq = _doc_anh(monkeypatch, "", has_diagram=True,
                  diagram_observations=["Hình chóp tứ giác S.ABCD, đáy là hình bình hành."])
    assert kq.assessment.status == "rejected"
    assert kq.assessment.rejection_code == "MISSING_PROBLEM_TEXT"
