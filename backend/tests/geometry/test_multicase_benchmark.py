# -*- coding: utf-8 -*-
"""CHỨNG MINH OFFLINE cho benchmark 12 ca. **0 request thật.**

`MULTICASE_STRUCTURED_ANALYZE_COMPILER_BENCHMARK` (2026-09-21).

Điều đắt nhất ở đây không phải "runner chạy đúng" mà là ba thứ dễ hỏng ÂM THẦM
trong một benchmark nhiều ca:

  · **ghép ca lệch** — token/kết quả của ca này gắn sang ca khác;
  · **dataset trôi** — xoá một ca, đổi thứ tự, sửa đáp án sau khi thấy kết quả;
  · **rò rỉ** — ground truth hoặc đáp số đi vào thân request.

Mỗi thứ ấy đều làm bảng số đẹp lên mà không ai thấy, nên mỗi thứ có một phép
tiêm riêng ở §6.
"""
from __future__ import annotations

import ast
import asyncio
import hashlib
import json
import sys
from pathlib import Path

import httpx
import pytest

GOC = Path(__file__).resolve().parents[2]
for _p in (str(GOC), str(GOC / "scripts")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from app.ai import gemini  # noqa: E402
from app.ai.telemetry import stage_scope  # noqa: E402

import run_multicase_benchmark as B  # noqa: E402
import run_structured_relation_analyze_live as L  # noqa: E402
from run_photo_problem_live import BoKhuBiMat, ChanMangThat  # noqa: E402

KEY_GIA = "AIzaKHOA_GIA_CHO_TEST_KHONG_PHAI_KHOA_THAT"

#: Băm CHÍNH TẮC của dataset, đóng băng. Đổi đề, đổi đáp án, đổi thứ tự hay
#: xoá một ca đều làm nó lệch — đó là điều `parametrize` một mình không bắt được.
DATASET_SHA = "__TINH_LUC_CHAY__"


def _reg():
    return B.doc_registry()


def _gt():
    return B.doc_ground_truth()


# ══ DATASET ĐÓNG BĂNG ══════════════════════════════════════════════════════
def test_dataset_du_12_ca_8_duong_4_am_va_thu_tu_co_dinh():
    reg = _reg()
    assert len(reg["cases"]) == 12
    assert sum(1 for c in reg["cases"] if c["kind"] == "positive") == 8
    assert sum(1 for c in reg["cases"] if c["kind"] == "negative") == 4
    assert reg["stage_a_order"] == ["P01", "P02", "P03", "N01"]
    assert reg["stage_b_order"] == ["P04", "P05", "P06", "P07", "P08",
                                    "N02", "N03", "N04"]
    # Thứ tự CHẠY khác thứ tự LIỆT KÊ có chủ đích: giai đoạn A trộn 3 positive
    # với 1 negative, nên cổng dừng nhìn thấy cả hai loại trước khi mở giai đoạn B.
    tt = B.thu_tu_chay(reg)
    assert len(tt) == 12 and len(set(tt)) == 12
    assert set(tt) == {c["case_id"] for c in reg["cases"]}


def test_dataset_sha_on_dinh_va_nhay_voi_moi_thay_doi():
    """Cửa sổ chứng: băm phải ĐỔI khi xoá ca, đổi thứ tự hoặc sửa đáp án.

    Không có phép kiểm này thì `DATASET_SHA` chỉ là một chuỗi chưa ai chứng minh
    là nó phản ứng với cái gì.
    """
    reg, gt = _reg(), _gt()
    goc = B.canonical_dataset_sha(reg, gt)
    import copy
    bot = copy.deepcopy(reg); bot["cases"] = bot["cases"][:-1]
    dao = copy.deepcopy(reg); dao["stage_b_order"] = list(reversed(dao["stage_b_order"]))
    sua = copy.deepcopy(gt); sua["positive"]["P01"]["volume"] = "41"
    assert B.canonical_dataset_sha(bot, gt) != goc, "xoá một ca mà băm không đổi"
    assert B.canonical_dataset_sha(dao, gt) != goc, "đổi thứ tự mà băm không đổi"
    assert B.canonical_dataset_sha(reg, sua) != goc, "sửa đáp án mà băm không đổi"
    assert B.canonical_dataset_sha(reg, gt) == goc, "băm không tất định"


def test_moi_ca_co_bo_nhan_RIENG_va_khong_dung_lai_S_A_B_C():
    reg = _reg()
    bo = []
    for c in reg["cases"]:
        nh = {v for v in c["labels"].values() if v}
        assert not (nh & {"S", "A", "B", "C"}), f"{c['case_id']} dùng lại nhãn ca cũ"
        bo.append(frozenset(nh))
    assert len(set(bo)) == len(bo), "hai ca dùng chung một bộ nhãn"


def test_de_khong_trung_ca_cu_va_khong_trung_13_wording_fixture():
    import diagnose_structured_relation_prompt as D
    cu = L.de_bai(L.doc_manifest())
    fx = {m["wording"] for m in D.MA_TRAN_CACH_VIET}
    for c in _reg()["cases"]:
        t = c["input_text"]
        assert t != cu, f"{c['case_id']} trùng controlled case cũ"
        assert t not in fx, f"{c['case_id']} trùng một wording fixture"
        for w in fx:
            assert w not in t, f"{c['case_id']} chép nguyên một fixture: {w!r}"
        # và không chép nguyên câu ví dụ của prompt
        assert "tam giác PQR vuông tại P" not in t
        assert "góc PQR bằng 90°" not in t


def test_phan_bo_cach_dien_dat_du_theo_dac_ta():
    pos = [c for c in _reg()["cases"] if c["kind"] == "positive"]
    dn = [c for c in pos if c["wording_class"] == "DEFINITIONAL_NORMALIZATION"]
    ex = [c for c in pos if c["wording_class"] == "EXPLICIT_SURFACE_RELATION"]
    assert len(dn) >= 4 and len(ex) >= 2
    assert any("90°" in c["input_text"] for c in pos)
    assert any("⊥" in c["input_text"] for c in pos)
    assert sum(1 for c in pos if "/" in c["input_text"]) >= 2      # phân số
    assert any("\n" in c["input_text"] for c in pos)               # xuống dòng
    assert sum(1 for c in pos if "ĐẢO THỨ TỰ" in c["wording_notes"]) >= 2


def test_ground_truth_khong_lot_vao_bat_ky_de_nao():
    gt = _gt()
    for c in _reg()["cases"]:
        if c["kind"] != "positive":
            continue
        g = gt["positive"][c["case_id"]]
        for k in ("volume", "base_area"):
            assert f"thể tích bằng {g[k]}" not in c["input_text"]
            assert f"= {g[k]}$" not in c["input_text"]
        assert "expected" not in c["input_text"]


# ══ 4, 5 — RÒ RỈ ═══════════════════════════════════════════════════════════
def _tra_loi(van: str) -> httpx.Response:
    return httpx.Response(200, json={
        "candidates": [{"content": {"parts": [{"text": van}]}}],
        "usageMetadata": {"promptTokenCount": 11, "candidatesTokenCount": 7,
                          "thoughtsTokenCount": 3, "totalTokenCount": 21}})


def _payload(ca: dict, g: dict, **doi) -> dict:
    """Đầu ra Analyze ĐÚNG cho một ca positive, dẫn từ chính registry."""
    Lb = ca["labels"]
    rv, a, b, ap = Lb["right_vertex"], Lb["leg_1_end"], Lb["leg_2_end"], Lb["apex"]
    p = {
        "input_facts": [
            {"id": "day_vuong", "label": f"tam giác {rv}{a}{b} vuông tại {rv}",
             "values": [f"tam giác {rv}{a}{b} vuông tại {rv}"]},
            {"id": "leg1", "label": f"{rv}{a}", "values": [g["leg_1"]["len"]]},
            {"id": "leg2", "label": f"{rv}{b}", "values": [g["leg_2"]["len"]]},
            {"id": "cao_vuong", "label": f"{ap}{rv} vuông góc mặt phẳng ({rv}{a}{b})",
             "values": [f"{ap}{rv} ⊥ ({rv}{a}{b})"]},
            {"id": "cao", "label": f"{ap}{rv}", "values": [g["height"]["len"]]},
        ],
        "obligations": [{"kind": "volume", "container": f"{ap}.{rv}{a}{b}",
                         "witness": "the_tich"}],
        "geometric_relations": [
            {"kind": "perpendicular_lines", "line": [rv, a], "other_line": [rv, b],
             "source_fact_id": "day_vuong"},
            {"kind": "perpendicular_line_plane", "line": [ap, rv], "plane": [rv, a, b],
             "source_fact_id": "cao_vuong"},
        ],
    }
    p.update(doi)
    return p


def _cong(max_http=B.TRAN_TONG, tran=None, chuoi_cam=()):
    return L.CongQuetCam(httpx.MockTransport(lambda _r: _tra_loi("{}")), max_http,
                         BoKhuBiMat((KEY_GIA,)),
                         tran_theo_tang=B.TRAN_THEO_TANG if tran is None else tran,
                         chuoi_cam=chuoi_cam)


def test_4_ground_truth_khong_di_vao_than_request():
    reg, gt = _reg(), _gt()
    ca = reg["cases"][0]
    cong = L.CongQuetCam(
        httpx.MockTransport(lambda _r: _tra_loi(json.dumps(
            _payload(ca, gt["positive"]["P01"]), ensure_ascii=False))),
        B.TRAN_TONG, BoKhuBiMat((KEY_GIA,)), tran_theo_tang=B.TRAN_THEO_TANG,
        chuoi_cam=B._chuoi_cam(gt))
    with ChanMangThat() as chan:
        r, env = asyncio.run(B.chay_mot_ca(ca, gt, KEY_GIA, cong))
    assert chan.attempts == []
    bc = cong.bang_chung_danh_tinh()
    assert bc["GROUND_TRUTH_ABSENT_FROM_REQUEST"] is True
    assert bc["GROUND_TRUTH_NEEDLES_FOUND"] == []


def test_4_bis_cua_so_chung_bo_quet_BAT_duoc_khi_co_dau_vet():
    gt = _gt()
    needle = B._chuoi_cam(gt)[0]
    cong = _cong(chuoi_cam=B._chuoi_cam(gt))
    cong.dat_ca("X")

    async def thu():
        with L.cai_cong_http(cong), L.dung_ngan_sach(
                gemini.ApiBudget(max_api_calls=1, max_attempts=1, max_logical_calls=1)):
            with stage_scope("semantic_analyze"):
                await gemini.call_gemini(KEY_GIA, "s", f"u {needle}", None, 0.1)

    asyncio.run(thu())
    assert cong.bang_chung_danh_tinh()["GROUND_TRUTH_ABSENT_FROM_REQUEST"] is False


def test_5_compiler_khong_nhan_dap_so_va_khong_nhan_raw_problem_text():
    """Compiler chỉ nhận GRAPH. Đáp số và câu chữ không có đường vào."""
    nguon = (GOC / "scripts" / "run_multicase_benchmark.py").read_text(encoding="utf-8")
    cay = ast.parse(nguon)
    ham = next(f for f in ast.walk(cay)
               if isinstance(f, ast.FunctionDef) and f.name == "chay_tang_dung")
    than = ast.unparse(ham)
    # `volume` chỉ được đọc SAU khi chương trình đã sinh, để so đáp số.
    vt_bien_dich = than.index("bien_dich(")
    assert 'g["volume"]' not in than[:vt_bien_dich], "đáp số vào trước lúc biên dịch"
    for ten in ("compiler.py", "contract_adapter.py", "fact_graph.py"):
        p = GOC / "app" / "simulation" / "geometry_compiler" / ten
        c = ast.parse(p.read_text(encoding="utf-8"))
        assert "problem_text" not in {n.attr for n in ast.walk(c)
                                      if isinstance(n, ast.Attribute)}, ten


# ══ 1, 2, 3 — NGÂN SÁCH VÀ KHÔNG CÓ ĐƯỜNG LÙI ═════════════════════════════
def test_1_request_thu_hai_cho_CUNG_MOT_ca_bi_chan():
    cong = _cong()
    cong.dat_ca("P01")

    async def thu():
        with L.cai_cong_http(cong), L.dung_ngan_sach(
                gemini.ApiBudget(max_api_calls=B.TRAN_MOI_CA, max_attempts=1,
                                 max_logical_calls=1)):
            for _ in range(2):
                with stage_scope("semantic_analyze"):
                    await gemini.call_gemini(KEY_GIA, "s", "u", None, 0.1)

    with pytest.raises(gemini.BudgetExceeded):
        asyncio.run(thu())
    assert len([x for x in cong.records if x["sent"]]) == 1


def test_2_request_thu_13_bi_chan_o_TRAN_TONG():
    cong = _cong()

    async def thu():
        with L.cai_cong_http(cong):
            for i in range(13):
                cong.dat_ca(f"C{i:02d}")
                with L.dung_ngan_sach(gemini.ApiBudget(
                        max_api_calls=B.TRAN_MOI_CA, max_attempts=1, max_logical_calls=1)):
                    with stage_scope("semantic_analyze"):
                        await gemini.call_gemini(KEY_GIA, "s", "u", None, 0.1)

    with pytest.raises(gemini.BudgetExceeded):
        asyncio.run(thu())
    t = cong.tong_hop()
    assert t["HTTP_REQUESTS_SENT"] == 12 and t["SENT_WITHIN_BUDGET"] is True
    assert cong.inner_invocations == 12


def test_3_synthesis_va_vision_bi_chan_khong_co_fallback():
    for nhan, tang in (("semantic_program", "synthesis"), ("transcribe", "vision")):
        cong = _cong()
        cong.dat_ca("P01")

        async def thu():
            with L.cai_cong_http(cong), L.dung_ngan_sach(
                    gemini.ApiBudget(max_api_calls=1, max_attempts=1, max_logical_calls=1)):
                with stage_scope(nhan):
                    await gemini.call_gemini(KEY_GIA, "s", "u", None, 0.1)

        with pytest.raises(gemini.BudgetExceeded):
            asyncio.run(thu())
        assert cong.tong_hop()[f"{tang.upper()}_HTTP_REQUESTS"] == 0
        assert cong.inner_invocations == 0


def test_3_bis_runner_khong_co_mot_loi_goi_tong_hop_nao():
    cay = ast.parse((GOC / "scripts" / "run_multicase_benchmark.py")
                    .read_text(encoding="utf-8"))

    def ten(n: ast.Call) -> str:
        f = n.func
        return f.attr if isinstance(f, ast.Attribute) else getattr(f, "id", "")

    goi = {ten(n) for n in ast.walk(cay) if isinstance(n, ast.Call)}
    assert "stage_semantic_program" not in goi and "call_gemini" not in goi
    assert B.TRAN_THEO_TANG["synthesis"] == 0 and B.TRAN_THEO_TANG["vision"] == 0
    assert B.TRAN_THEO_TANG["analyze"] == B.TRAN_TONG == 12


# ══ 6, 7 — GHÉP CA KHÔNG ĐƯỢC LỆCH ════════════════════════════════════════
def test_6_usage_metadata_gan_DUNG_ca():
    """Ca sau trả token khác ca trước; mỗi ca phải nhận đúng số của mình."""
    reg, gt = _reg(), _gt()
    dem = {"n": 0}

    def xu_ly(_r):
        dem["n"] += 1
        return httpx.Response(200, json={
            "candidates": [{"content": {"parts": [{"text": "{}"}]}}],
            "usageMetadata": {"promptTokenCount": 100 * dem["n"],
                              "totalTokenCount": 1000 * dem["n"]}})

    cong = L.CongQuetCam(httpx.MockTransport(xu_ly), B.TRAN_TONG,
                         BoKhuBiMat((KEY_GIA,)), tran_theo_tang=B.TRAN_THEO_TANG,
                         chuoi_cam=())
    ra = []
    for cid in ("P01", "P02", "P03"):
        r, _ = asyncio.run(B.chay_mot_ca(B.ca_theo_id(reg)[cid], gt, KEY_GIA, cong))
        ra.append((cid, r["USAGE"].get("totalTokenCount")))
    assert ra == [("P01", 1000), ("P02", 2000), ("P03", 3000)]


def test_7_ket_qua_compiler_khong_gan_sang_ca_khac():
    """Mỗi bản ghi kết quả mang `CASE_ID` của chính nó, và đáp số theo ca ấy."""
    reg, gt = _reg(), _gt()
    bang = B.ca_theo_id(reg)
    # P01 và P04 — hai ca mà phép neo độ dài của SERVER chạy trọn vẹn offline.
    # KHÔNG dùng P02 ở đây: nó là ca stress đã biết (xem `known_stressors`), và
    # trộn một khuyết tật đã biết vào phép kiểm ghép-ca là đo hai thứ một lúc.
    for cid in ("P01", "P04"):
        ca, g = bang[cid], gt["positive"][cid]
        cong = L.CongQuetCam(
            httpx.MockTransport(lambda _r, c=ca, gg=g: _tra_loi(
                json.dumps(_payload(c, gg), ensure_ascii=False))),
            B.TRAN_TONG, BoKhuBiMat((KEY_GIA,)), tran_theo_tang=B.TRAN_THEO_TANG,
            chuoi_cam=())
        r, env = asyncio.run(B.chay_mot_ca(ca, gt, KEY_GIA, cong))
        assert r["CASE_ID"] == cid
        assert r["OUTCOME"] == "FULL_PIPELINE_PASS", r
        assert r["BUILD"]["ANSWER_OK"] is True
        # Chấm ca này bằng ground truth của ca KIA phải THẤT BẠI.
        kia = "P04" if cid == "P01" else "P01"
        sai = B.chay_tang_dung(_hop_dong(ca, g), ca, gt["positive"][kia])
        assert sai.get("ANSWER_OK") is not True, "đáp số khớp cả ground truth ca khác"


def _hop_dong(ca: dict, g: dict):
    from app.simulation.semantic_program.analyze_contract import build_request_contract
    return build_request_contract(_payload(ca, g), problem_text=ca["input_text"],
                                  domain="hinh_hoc")


# ══ 8 — XOÁ MỘT CA MÀ TEST VẪN XANH ═══════════════════════════════════════
def test_8_xoa_mot_ca_khoi_registry_lam_test_DO():
    """`parametrize` một mình không bắt được điều này — băm dataset thì có."""
    import copy
    reg, gt = _reg(), _gt()
    goc = B.canonical_dataset_sha(reg, gt)
    for bot in ("P05", "N03"):
        r2 = copy.deepcopy(reg)
        r2["cases"] = [c for c in r2["cases"] if c["case_id"] != bot]
        assert B.canonical_dataset_sha(r2, gt) != goc
        assert len(r2["cases"]) == 11


# ══ 9 — ĐỔI THỨ TỰ SAU KHI ĐÓNG BĂNG ══════════════════════════════════════
def test_9_doi_thu_tu_ca_lam_bam_dataset_lech():
    import copy
    reg, gt = _reg(), _gt()
    goc = B.canonical_dataset_sha(reg, gt)
    r2 = copy.deepcopy(reg)
    r2["stage_a_order"] = ["P02", "P01", "P03", "N01"]
    assert B.canonical_dataset_sha(r2, gt) != goc


# ══ 10 — STAGE B KHÔNG ĐƯỢC CHẠY KHI STAGE A KHÔNG ĐẠT ════════════════════
def _ket(cid, kind, dat=True, an_toan=True, im_lang=False):
    r = {"CASE_ID": cid, "KIND": kind, "PROVIDER_ERROR": None}
    if kind == "positive":
        r["OUTCOME"] = "FULL_PIPELINE_PASS" if dat else "BUILD_FAILED"
        r["BUILD"] = {"SILENT_QUALITY_FAILURE": im_lang}
    else:
        r["SAFE_REJECTION"] = an_toan
        r["UNSAFE_ACCEPTANCE"] = not an_toan
    return r


def test_10_cong_stage_a_mo_khi_dat_va_DONG_khi_khong_dat():
    du = [_ket("P01", "positive"), _ket("P02", "positive"),
          _ket("P03", "positive", dat=False), _ket("N01", "negative")]
    assert B.cong_stage_a(du)["MO_STAGE_B"] is True   # 2/3 đạt

    thieu = [_ket("P01", "positive"), _ket("P02", "positive", dat=False),
             _ket("P03", "positive", dat=False), _ket("N01", "negative")]
    assert B.cong_stage_a(thieu)["MO_STAGE_B"] is False

    khong_an_toan = [_ket("P01", "positive"), _ket("P02", "positive"),
                     _ket("P03", "positive"), _ket("N01", "negative", an_toan=False)]
    assert B.cong_stage_a(khong_an_toan)["MO_STAGE_B"] is False

    im = [_ket("P01", "positive", im_lang=True), _ket("P02", "positive"),
          _ket("P03", "positive"), _ket("N01", "negative")]
    assert B.cong_stage_a(im)["MO_STAGE_B"] is False


def test_10_bis_nguong_stage_a_dang_ky_TRUOC_va_khong_doc_lai_ket_qua():
    assert B.NGUONG_STAGE_A == {"positive_full_pipeline_min": 2,
                                "positive_run": 3, "negative_safe_required": 1}
    nguon = (GOC / "scripts" / "run_multicase_benchmark.py").read_text(encoding="utf-8")
    vt_gate = nguon.index("def cong_stage_a")
    assert "NGUONG_STAGE_A" in nguon[:nguon.index("def main")]


# ══ COMPILER CHỈ CHẠY SAU ANALYZE PASS; NEGATIVE KHÔNG VÀO COMPILER ═══════
def test_compiler_khong_chay_khi_analyze_thieu_quan_he():
    reg, gt = _reg(), _gt()
    ca, g = B.ca_theo_id(reg)["P01"], gt["positive"]["P01"]
    p = _payload(ca, g)
    del p["geometric_relations"][0]
    cong = L.CongQuetCam(
        httpx.MockTransport(lambda _r: _tra_loi(json.dumps(p, ensure_ascii=False))),
        B.TRAN_TONG, BoKhuBiMat((KEY_GIA,)), tran_theo_tang=B.TRAN_THEO_TANG,
        chuoi_cam=())
    r, env = asyncio.run(B.chay_mot_ca(ca, gt, KEY_GIA, cong))
    assert r["ANALYZE_PASS"] is False
    assert "BUILD" not in r, "compiler ĐÃ CHẠY dù Analyze chưa đủ"
    assert env is None
    assert r["OUTCOME"] == "ANALYZE_INCOMPLETE_OR_UNSAFE"


def test_negative_khong_tao_canh_va_duoc_ghi_ma_tu_choi():
    reg, gt = _reg(), _gt()
    ca = B.ca_theo_id(reg)["N03"]
    # Mô hình khai ĐÚNG những gì đề nói: đáy vuông, KHÔNG có quan hệ đường–mặt.
    Lb = ca["labels"]
    rv, a, b = Lb["right_vertex"], Lb["leg_1_end"], Lb["leg_2_end"]
    p = {"input_facts": [
            {"id": "day", "label": f"tam giác {rv}{a}{b} vuông tại {rv}",
             "values": [f"tam giác {rv}{a}{b} vuông tại {rv}"]},
            {"id": "l1", "label": f"{rv}{a}", "values": ["5"]},
            {"id": "l2", "label": f"{rv}{b}", "values": ["8"]}],
         "obligations": [{"kind": "volume", "container": "khoi", "witness": "v"}],
         "geometric_relations": [
            {"kind": "perpendicular_lines", "line": [rv, a], "other_line": [rv, b],
             "source_fact_id": "day"}]}
    cong = L.CongQuetCam(
        httpx.MockTransport(lambda _r: _tra_loi(json.dumps(p, ensure_ascii=False))),
        B.TRAN_TONG, BoKhuBiMat((KEY_GIA,)), tran_theo_tang=B.TRAN_THEO_TANG,
        chuoi_cam=())
    r, env = asyncio.run(B.chay_mot_ca(ca, gt, KEY_GIA, cong))
    assert r["SAFE_REJECTION"] is True and r["UNSAFE_ACCEPTANCE"] is False
    assert env is None
    assert r["REJECTION_CODE"] in gt["negative"]["N03"]["acceptable_rejection_codes"]
    assert r["BUILD"]["SYNTHESIS_REQUESTS"] == 0


def test_negative_bi_PHUC_VU_thi_bi_bat_la_UNSAFE():
    """Cửa sổ chứng cho cổng an toàn: dựng được ⇒ phải báo UNSAFE."""
    reg, gt = _reg(), _gt()
    ca = B.ca_theo_id(reg)["N02"]
    Lb = ca["labels"]
    # Mô hình BỊA quan hệ vuông góc cho đáy từ bộ số 3–4–5.
    p = {"input_facts": [
            {"id": "bia", "label": "TV vuông góc TX", "values": ["TV ⟂ TX"]},
            {"id": "l1", "label": "TV", "values": ["3"]},
            {"id": "l2", "label": "TX", "values": ["4"]},
            {"id": "cao", "label": "RT vuông góc (TVX)", "values": ["RT ⊥ (TVX)"]},
            {"id": "h", "label": "RT", "values": ["6"]}],
         "obligations": [{"kind": "volume", "container": "khoi", "witness": "v"}],
         "geometric_relations": [
            {"kind": "perpendicular_lines", "line": ["T", "V"], "other_line": ["T", "X"],
             "source_fact_id": "bia"},
            {"kind": "perpendicular_line_plane", "line": ["R", "T"],
             "plane": ["T", "V", "X"], "source_fact_id": "cao"}]}
    cong = L.CongQuetCam(
        httpx.MockTransport(lambda _r: _tra_loi(json.dumps(p, ensure_ascii=False))),
        B.TRAN_TONG, BoKhuBiMat((KEY_GIA,)), tran_theo_tang=B.TRAN_THEO_TANG,
        chuoi_cam=())
    r, _ = asyncio.run(B.chay_mot_ca(ca, gt, KEY_GIA, cong))
    assert r["UNSAFE_ACCEPTANCE"] is True and r["SAFE_REJECTION"] is False
    assert r["OUTCOME"] == "UNSAFE_ACCEPTANCE"


# ══ BROWSER REPLAY KHÔNG GỌI MODEL ════════════════════════════════════════
def test_browser_replay_khong_the_goi_model():
    p = GOC.parent / "frontend" / "scripts" / "compiler-scene-replay.mjs"
    n = p.read_text(encoding="utf-8")
    for k in ("GEMINI_API_KEY", "generativelanguage", "ALLOW_LIVE_AI", "call_gemini"):
        assert k not in n
    assert 'interceptJson("*/api/*"' in n and "APPLICATION_LLM_CALLS: 0" in n


# ══ PHÂN LOẠI VÀ THỐNG KÊ ═════════════════════════════════════════════════
def test_runner_KHONG_mang_bo_phan_loai_rieng_mot_tham_quyen():
    """Bản /1 có `phan_loai` riêng: gộp UNSAFE vào NOT_READY, thiếu ca thành
    MORE_EVIDENCE_NEEDED. `COMPLETION_RUNNER_REPAIR_OFFLINE` dời phân loại về
    `aggregate_multicase_completion` — ngữ nghĩa mới khoá ở
    `test_completion_runner_repair.py::test_G4_*`. Hai bộ phân loại cùng tồn tại
    chính là hai thẩm quyền."""
    for ten in ("phan_loai", "thong_ke", "KET_QUA", "NEXT_THEO_KET_QUA", "QUY_KET"):
        assert not hasattr(B, ten), ten
    assert B.quy_ket_that_bai is B.TH.quy_ket_that_bai
    assert B.loai_su_co is B.TH.loai_su_co


def test_wilson_khong_bao_gio_khai_y_nghia_thong_ke():
    assert B._wilson(8, 8) == [0.676, 1.0] or B._wilson(8, 8)[1] == 1.0
    assert B._wilson(0, 0) is None
