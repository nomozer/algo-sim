# -*- coding: utf-8 -*-
"""W14 Track B + 5a — cổng giả định ba trạng thái và chính sách tin cậy tường minh.

`PROVEN_SAFE` chỉ đến từ chứng chỉ có kiểu (C0 / C1); `DEPENDENT_ON_UNSTATED_ASSUMPTION`
(W14 gọi là `UNSAFE` — W15 đổi tên theo đề bài W15, cùng sức mạnh khẳng định) chỉ đến từ
một phản ví dụ hợp lệ; còn lại `UNDETERMINED`. Cả hai trạng thái sau đều TỪ CHỐI. Một
phép dò không thấy đổi đáp số KHÔNG phải chứng minh an toàn. 0 lượt gọi model.

W14 Task 5 kết luận `ASSUMPTION_POLICY_INCOMPLETE` nên các test cổng mang `xfail(strict)`.
W15 đã đạt luật SHIP đăng ký trước (`runs/w15-assumption-closure/diagnostics/
ASSUMPTION_MECHANISM_DECISION_W15.json`) và nối cổng vào route: mọi dấu xfail đã gỡ.
"""
from __future__ import annotations

import ast
import copy
import importlib
import json
import uuid
from fractions import Fraction
from pathlib import Path

import pytest

from app.simulation.semantic_program.route import verify_and_compile
from tests.geometry import route_cases as W

APP = Path(__file__).resolve().parents[2] / "app"
MA_GIA_DINH = {"ASSUMPTION_DETERMINES_ANSWER", "ASSUMPTION_INVARIANCE_UNPROVEN"}
PHU_THUOC = "DEPENDENT_ON_UNSTATED_ASSUMPTION"


def _gate():
    return importlib.import_module("app.simulation.semantic_program.assumption_gate")


def _nguon_de():
    return importlib.import_module("app.simulation.semantic_program.grounding_gate").NguonDe


def _bi_tu_choi_vi_gia_dinh(out, ma: str | None = None):
    assert not out.servable, (out.stage_reached, out.reason_code)
    assert out.stage_reached == "assumption", (out.stage_reached, out.reason_code, out.details)
    assert out.reason_code in ({ma} if ma else MA_GIA_DINH), out.reason_code
    assert out.assumption_enforced is True, "từ chối theo cổng chỉ trong vùng khối đa diện (U3)"


def _chay_tu_choi(ca):
    ct, raw = ca()
    _sp, out, _sc = W.chay(ct, raw)
    _bi_tu_choi_vi_gia_dinh(out)


# ── AC1: phép dò kênh giả định của W12 ──────────────────────────────────────

def _kenh(channel: str):
    ct, raw = W.kenh_gia_dinh(channel)
    _sp, out, _sc = W.chay(ct, raw)
    _bi_tu_choi_vi_gia_dinh(out, "ASSUMPTION_DETERMINES_ANSWER")
    assert "AD" in out.reason_subjects, out.reason_subjects


def test_kenh_layout_derived_bi_tu_choi():
    _kenh("layout_derived")


def test_kenh_model_assumption_bi_tu_choi():
    _kenh("model_assumption")


# ── Ca đối kháng: mỗi ca LỌT thiết kế M2E cũ (Task 5 Step 1) ────────────────

def test_kich_thuoc_thieu_bi_che_boi_XY_length_gia_dinh():
    """(1) `AD_length = 5` LAYOUT_DERIVED che chỗ thiếu AD.

    Grounding hôm nay đã chặn kênh này (`MODEL_ASSUMPTION_TYPE_NOT_ALLOWED`) — phần
    đầu là GUARD. Phần sau gọi THẲNG cổng: luật hợp lệ của phản ví dụ không được
    coi một literal giả định là ràng buộc, nên kết quả không bao giờ là PROVEN_SAFE.
    """
    ct, raw = W.ca_xy_length_gia_dinh()
    _sp, out, _sc = W.chay(ct, raw)
    assert not out.servable, out.stage_reached
    kq = _gate().danh_gia_doc_lap(ct, W.spec_cua(raw))
    assert kq.status in (PHU_THUOC, "UNDETERMINED"), kq


def test_moi_phep_nhieu_bi_loai_van_thieu_du_kien():
    """(2) Phép dò W12 dưới phép quay hữu tỉ 3-D: mọi phép nhiễu theo trục phá AB/AC."""
    _chay_tu_choi(W.ca_xoay_thieu_AD)


def test_bang_chung_cua_canh_khac_khong_che_chieu_cao():
    """(3) Số "4" của cạnh đáy không được làm bằng chứng cho chiều cao tự đặt bằng 4."""
    _chay_tu_choi(W.ca_canh_khac_che_chieu_cao)


def test_thieu_kich_thuoc_trong_khung_xien():
    """(4) Lăng trụ xiên: vectơ tịnh tiến (cạnh bên/chiều cao) do chương trình tự đặt."""
    _chay_tu_choi(W.ca_lang_tru_xien)


def test_phu_thuoc_ma_bon_phep_nhieu_khong_thay():
    """(5) Chân đường cao tự đặt; d(S, BC) phụ thuộc nó, phép co giãn toàn cục không tách được."""
    _chay_tu_choi(W.ca_chan_duong_cao_an)


def test_het_ngan_sach_khong_thanh_an_toan(monkeypatch):
    """(6) Hết ngân sách chạy lại ⇒ UNDETERMINED, không bao giờ PROVEN_SAFE.

    Ngân sách 0 (không phải 1): một lượt chạy tham chiếu của C1 có thể nằm gọn
    trong ngân sách 1, khi ấy không có gì "hết". Chỉ C0 — không cần chạy lại —
    được phép an toàn ở ngân sách 0.
    """
    G = _gate()
    monkeypatch.setattr(G, "NGAN_SACH_CHAY_LAI", 0)
    ct, raw = W.kenh_gia_dinh("layout_derived")
    assert G.danh_gia_doc_lap(ct, W.spec_cua(raw)).status == "UNDETERMINED"
    _t, ct = W.chop_tam_giac()
    kq = G.danh_gia_doc_lap(ct, W.spec_cua(W.chuong_trinh(ct)))
    assert kq.status == "UNDETERMINED" or kq.certificate == "C0", kq


def test_hop_dong_san_pham_thieu_de_bi_tu_choi():
    """(7) Gọi mặc định (không khai `nguon`) với đề rỗng ⇒ từ chối, không gửi sửa."""
    from app.ai import pipeline as PL

    _t, ct = W.chop_tam_giac()
    out = verify_and_compile(W.hop_dong_khong_de(ct), W.spec_cua(W.chuong_trinh(ct)))
    assert not out.servable, (out.stage_reached, out.reason_code)
    assert out.stage_reached == "grounding", out.stage_reached
    assert out.reason_code == "SOURCE_TEXT_MISSING", out.reason_code
    assert "SOURCE_TEXT_MISSING" in PL.KHONG_SUA_NGUON


def test_hai_dap_so_mot_phu_thuoc_gia_dinh():
    """Review Focus 4: một đáp số được chứng nhận, một phụ thuộc giả định ⇒ từ chối CẢ bài."""
    _chay_tu_choi(W.ca_hai_dap_so_mot_phu_thuoc)


# ── Giới hạn chứng chỉ C0/C1 ────────────────────────────────────────────────

def test_dong_dang_nhung_nhan_them_vo_huong_gia_dinh():
    """(8) Cấu hình khớp tham chiếu, nhưng đáp số nhân |AM| với M tự đặt."""
    ct, raw = W.ca_nhan_vo_huong_gia_dinh()
    _sp, out, _sc = W.chay(ct, raw)
    _bi_tu_choi_vi_gia_dinh(out)
    assert _gate().danh_gia_doc_lap(ct, W.spec_cua(raw)).certificate != "C1"


def test_bo_mot_phu_thuoc_khoi_do_thi(monkeypatch):
    """(9) Bảng toán hạng thiếu một trường ⇒ bao đóng KHÔNG đầy đủ ⇒ không chứng chỉ."""
    G = _gate()
    bang = copy.deepcopy(G.TOAN_HANG)
    kind = next(k for k, v in bang.items() if "of" in v)
    bang[kind] = tuple(f for f in bang[kind] if f != "of")
    monkeypatch.setattr(G, "TOAN_HANG", bang)
    _t, ct = W.chop_tam_giac()
    kq = G.danh_gia_doc_lap(ct, W.spec_cua(W.chuong_trinh(ct)))
    assert kq.status == "UNDETERMINED", kq
    assert any("CLOSURE_INCOMPLETE" in d for d in kq.details), kq.details
    assert G.kieu_ir_chua_phu(), "phép kiểm phủ của bảng phải đỏ khi thiếu một trường"


def test_bang_toan_hang_phu_moi_kieu_IR():
    assert _gate().kieu_ir_chua_phu() == []


def _p01_voi_quan_he(bien_the: str, de_im_lang: bool = False):
    from app.simulation.semantic_program.request_contract import InputFact

    _t, ct = W.lang_tru_tam_giac()
    raw = W.chuong_trinh(ct)
    if de_im_lang:   # W15: cùng payload, đề KHÔNG nói "đứng" — chỉ hợp đồng còn AD ⊥ (ABC)
        from tests.geometry import test_source_grounding_closure as T

        ct = W.hop_dong(T.PRISM_TEXT.replace("lăng trụ đứng", "lăng trụ"), T._prism_payload())
    rels = []
    facts = list(ct.input_facts)
    for r in ct.geometric_relations:
        if r.kind != "perpendicular_line_plane":
            rels.append(r)
        elif bien_the == "khong_nguon":
            rels.append(r.model_copy(update={"source_fact_id": None}))
        elif bien_the == "gia_dinh":
            rels.append(r.model_copy(update={"model_assumption": True}))
        else:  # trỏ tới một InputFact `claimed`
            facts.append(InputFact(fact_id="f_claimed", label="cạnh bên vuông góc đáy",
                                   values=("AD ⊥ (ABC)",), provenance="claimed"))
            rels.append(r.model_copy(update={"source_fact_id": "f_claimed"}))
    return ct.model_copy(update={"geometric_relations": tuple(rels),
                                 "input_facts": tuple(facts)}), raw


@pytest.mark.parametrize("bien_the", ["khong_nguon", "gia_dinh", "claimed"])
def test_quan_he_khong_duoc_nguon_xac_nhan(bien_the):
    """(10) Quan hệ có kiểu không được nguồn đề xác nhận ⇒ C1 không được cấp.

    W15 (R2, plan-review): fixture W14 viết đề "lăng trụ đứng ABC.DEF" — tức đề CÓ nói
    AD ⊥ (ABC), server đọc được độc lập, nên C1 qua tiền đề server là đúng; khẳng định
    gốc đã lẫn chú thích với nguồn. Thực chất của (10) — một quan hệ mô hình KHÔNG được
    nguồn xác nhận không bao giờ làm nền cho C1, dù chú thích là gì — giữ nguyên trên CÙNG
    fixture với chữ "đứng" bị gỡ (đề im lặng). Biến thể thứ tư (`claimed` + đề nói "đứng"):
    `test_assumption_certificate::test_claimed_ma_de_noi_lang_tru_dung_C1_chi_qua_tien_de_server`.
    """
    ct, raw = _p01_voi_quan_he(bien_the, de_im_lang=True)
    kq = _gate().danh_gia_doc_lap(ct, W.spec_cua(raw))
    assert kq.certificate != "C1", (bien_the, kq)
    assert kq.status in (PHU_THUOC, "UNDETERMINED"), (bien_the, kq)


def test_hai_dap_so_mot_ngoai_pham_vi_chung_chi():
    """(11) Thể tích (PHEP_DO_C1) + cos² góc (ngoài phạm vi) ⇒ từ chối CẢ bài."""
    _chay_tu_choi(W.ca_hai_dap_so_mot_ngoai_pham_vi)


# ── Chính sách tin cậy tường minh (Task 5a) ────────────────────────────────

def test_fixture_tin_cay_phai_khai_tuong_minh():
    NguonDe = _nguon_de()
    _t, ct = W.chop_tam_giac()
    out = verify_and_compile(W.hop_dong_khong_de(ct), W.spec_cua(W.chuong_trinh(ct)),
                             nguon=NguonDe.FIXTURE_TIN_CAY)
    assert out.servable, (out.stage_reached, out.reason_code)
    assert out.source_check == "UNCHECKED_TRUSTED_FIXTURE"


def test_tuyen_san_pham_khong_dung_fixture_tin_cay():
    assert hasattr(_nguon_de(), "FIXTURE_TIN_CAY")
    tep = [APP / "main.py", *sorted((APP / "ai").rglob("*.py")), *sorted((APP / "api").rglob("*.py"))]
    dung = [str(f.relative_to(APP)) for f in tep if f.exists()
            and "FIXTURE_TIN_CAY" in f.read_text(encoding="utf-8")]
    assert dung == [], dung


def test_khong_ma_nao_dung_NguonDe_tu_chuoi():
    """`NguonDe(<giá trị lúc chạy>)` ở đâu trong `app/` là một lối bypass tiềm tàng."""
    assert hasattr(_nguon_de(), "CAN_DE")
    vi_pham = []
    for f in sorted(APP.rglob("*.py")):
        for n in ast.walk(ast.parse(f.read_text(encoding="utf-8"))):
            if (isinstance(n, ast.Call) and getattr(n.func, "id", None) == "NguonDe"
                    and n.args):
                vi_pham.append(f"{f.relative_to(APP)}:{n.lineno}")
    assert vi_pham == [], vi_pham


def test_yeu_cau_san_pham_khong_bat_duoc_bypass(monkeypatch):
    """Thân request, header và đầu ra mô hình đều không bật được chính sách tin cậy."""
    from fastapi.testclient import TestClient

    from app.ai import pipeline as PL
    from app.main import app
    from app.persistence.db import init_db
    from app.simulation.semantic_program import route as R

    NguonDe = _nguon_de()
    thay: list = []
    goc = R.verify_and_compile

    def gian_diep(contract, spec, **kw):
        thay.append((kw.get("nguon", NguonDe.CAN_DE), contract.problem_text))
        return goc(contract, spec, **kw)

    monkeypatch.setattr(R, "verify_and_compile", gian_diep)
    monkeypatch.setenv("GEMINI_API_KEY", "khoa-gia")
    monkeypatch.delenv("GEOMETRY_COMPILER_MODE", raising=False)
    init_db()
    _t, ct = W.chop_tam_giac()
    chen = W.chop_tam_giac_payload() | {
        "nguon": "FIXTURE_TIN_CAY", "trusted": True,
        "source_check": "UNCHECKED_TRUSTED_FIXTURE", "problem_text": ""}
    tra_loi: list[str] = []

    async def fake_transport(*_a, **_k):
        tra_loi.append(tra_loi[-1])
        return tra_loi.pop(0)

    monkeypatch.setattr(PL, "call_gemini", fake_transport)
    for than_them, header, phan_tich in (
        ({"nguon": "FIXTURE_TIN_CAY", "trusted": True}, {}, W.chop_tam_giac_payload()),
        ({}, {"X-Nguon": "FIXTURE_TIN_CAY", "X-Trusted-Fixture": "1"}, W.chop_tam_giac_payload()),
        ({}, {}, chen),
    ):
        tra_loi[:] = [json.dumps(phan_tich), json.dumps(W.chuong_trinh(ct), default=str)]
        de = W.CHOP_TAM_GIAC_TEXT + f" (W14 bypass {uuid.uuid4().hex[:8]})"
        r = TestClient(app).post("/api/analyze", headers=header,
                                 json={"input": {"type": "text", "content": de}} | than_them)
        assert r.status_code == 200, r.text
    assert len(thay) == 3, thay
    for nguon, de_thay in thay:
        assert nguon == NguonDe.CAN_DE, nguon
        assert de_thay, "hợp đồng sản phẩm phải mang đề"


# ── GUARD: không từ chối oan (xanh hôm nay, phải xanh sau cổng) ─────────────

def test_chuyen_dong_cung_khong_doi_dap_so():
    from tests.geometry import test_source_grounding_closure as T

    ct = T._contract(T.PRISM_TEXT, T._prism_payload())

    def tinh_tien_doi_truc(p):
        x, y, z = (Fraction(str(c)) for c in p)
        return [str(y + 7), str(x - 2), str(z + 1)]

    _sp, out, _sc = W.chay(ct, W.doi_toa_do(T._program_with_height_5(), tinh_tien_doi_truc))
    assert out.servable, (out.stage_reached, out.reason_code)
    assert str(out.final_memory["the_tich_lang_tru"]) == "30"


GOLD_PHUC_VU = ("p1_chop_thiet_dien_khoang_cach", "p2_chop_day_ngu_giac_lom",
                "p4_hinh_tru_the_tich_va_xung_quanh", "p5_hinh_non_the_tich_va_xung_quanh",
                "p6_thiet_dien_elip_cua_hinh_tru", "p7_thiet_dien_elip_cua_hinh_non")
CA_DUONG = [("ho", h) for h in sorted(W.HO)] + [("gold", c) for c in GOLD_PHUC_VU]


@pytest.mark.parametrize("nhom,ten", CA_DUONG, ids=[f"{n}:{t}" for n, t in CA_DUONG])
def test_kich_thuoc_co_GIVEN_khong_bi_tu_choi_oan(nhom, ten):
    if nhom == "ho":
        _t, ct = W.HO[ten]()
        _sp, out, _sc = W.chay(ct)
    else:
        _t, ct, raw = W.gold(ten)
        _sp, out, _sc = W.chay(ct, raw)
    assert out.servable, (ten, out.stage_reached, out.reason_code, out.details[:3])


def test_khung_xoay_huu_ti_cua_ho_duoc_ho_tro():
    """Một đề sáu họ viết tay trong hệ trục XOAY hữu tỉ vẫn phải được phục vụ (AC2)."""
    _t, ct = W.chop_tam_giac()
    _sp, out, _sc = W.chay(ct, W.doi_toa_do(W.chuong_trinh(ct), W._xoay))
    assert out.servable, (out.stage_reached, out.reason_code)
    assert str(out.final_memory["the_tich_khoi"]) == "10"


def test_ngoai_vung_da_dien_chi_ghi_trang_thai_khong_tu_choi():
    """Quyết định U3: đề KHÔNG nêu khối đa diện theo từ vựng đóng (đoạn EF có độ dài 10…) ⇒
    cổng vẫn tính và route ghi trạng thái, nhưng không từ chối — hành vi và các cổng cũ giữ
    nguyên; mối nguy kích thước tự đặt ngoài vùng là một OPEN_ISSUE, không phải một an toàn."""
    from app.simulation.semantic_program.request_contract import RequestContract
    from tests.geometry import test_segment_relation_consistency as SRC

    r = SRC._r3()
    rc = SRC._hd(RequestContract.model_validate(r["request_contract"]))
    out = verify_and_compile(rc, W.spec_cua(SRC._voi_t(r, "1/5")))
    assert out.servable, (out.stage_reached, out.reason_code, out.details)
    assert (out.assumption_enforced, out.assumption_status) == (False, "UNDETERMINED")
