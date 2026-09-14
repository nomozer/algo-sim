# -*- coding: utf-8 -*-
"""Hợp đồng khai báo điểm: `at` vs `initial_value`. **0 lượt gọi model.**

    `docs/POINT_INITIALIZATION_CONTRACT_ALIGNMENT.md`, 2026-09-06.

IR có HAI ô chở toạ độ một điểm gốc, và chúng ở hai chỗ khác nhau:

    memory_declarations[].initial_value    — khai báo
    statements[declare_point].at           — câu lệnh

Đo được ở A/B `ab-v1-20260905T164514Z`, hai ca `e2` và `e6`: mô hình gửi
`{"name": "X", "type": "point3", "at": [0,0,0]}` — ô của CÂU LỆNH, đặt trong
KHAI BÁO. Pydantic mặc định `extra="ignore"` nên `at` **biến mất không dấu
vết**, khai báo còn `initial_value: null`, và lời từ chối cuối cùng là
*"có khai báo nhưng chưa có giá trị"* — **đúng sự thật, sai chỗ**. Mô hình đã
cho toạ độ; nó chỉ để nhầm ô, và không có cách nào biết.

Bộ test này khoá: chẩn đoán nêu đúng vị trí, tới được vòng sửa, và **không**
nới một milimét nào cổng xuất xứ.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

GOC = Path(__file__).resolve().parents[2]
for p in (str(GOC), str(GOC / "scripts")):
    if p not in sys.path:
        sys.path.insert(0, p)

from app.simulation.semantic_program.route import verify_and_compile  # noqa: E402
from app.simulation.semantic_program.validator import (  # noqa: E402
    _khoa_bi_bo_im_lang,
    _o_gia_tri_tho,
    validate_semantic_program,
)
from replay_point_initialization import (  # noqa: E402
    _nguon,
    chay,
    delta_1,
    delta_2,
)

VB = {"containers": [], "pointers": [], "value_boxes": []}
FID = "f_diem"


def _spec(decls, stmts):
    return {"spec_version": "1.0", "title": "Khai điểm",
            "description": "Kiểm hai ô chở toạ độ.",
            "pedagogical_intent": "Phân biệt khai báo với câu lệnh.",
            "memory_declarations": decls, "statements": stmts,
            "visual_bindings": VB}


def _hd(obl=()):
    from app.simulation.semantic_program.obligations import Obligation
    from app.simulation.semantic_program.request_contract import RequestContract

    return RequestContract(
        problem_text="Cho hai điểm A và B. Gọi M là trung điểm AB.",
        input_facts=[{"fact_id": FID, "label": "A và B là hai điểm đề cho",
                      "values": ["A", "B"], "provenance": "confirmed"}],
        obligations=tuple(Obligation(**o) for o in obl))


# ══ §2 · TÁI HIỆN trên chính raw candidate của mô hình ═══════════════════
@pytest.mark.parametrize("cid", ["e2", "e6"])
def test_R1_ban_GOC_bi_bac_o_VALIDATOR_voi_chan_doan_dung_cho(cid):
    raw, hd = _nguon(cid)
    r = chay("goc", raw, hd)
    assert r["validator_ok"] is False
    assert r["tang"] == "validator"
    loi = r["loi"]
    assert "memory_declarations[" in loi and ".at" in loi     # đường dẫn JSON
    assert "`at` là trường của `declare_point`" in loi        # chủ sở hữu
    assert "`initial_value`" in loi                           # ô chính tắc


def test_R2_e6_DELTA_1_MOT_MINH_da_du():
    """Nhầm ô là **toàn bộ** rào cản của `e6` — không cần delta nào khác."""
    raw, hd = _nguon("e6")
    d1, ghi = delta_1(raw)
    r = chay("delta_1", d1, hd)
    assert r["servable"] is True
    assert "400π" in set(r["bo_nho"].values())
    assert r["postconditions"] == "PASS" and r["scene3d"] == 8
    assert len(ghi) == 2                                   # đúng hai khai báo


def test_R3_e2_DELTA_1_mo_toi_GROUNDING__cong_ke_tiep_ghi_RIENG():
    """Một lỗi biến mất chỉ chứng minh delta xử lý được lỗi ấy."""
    raw, hd = _nguon("e2")
    d1, _ = delta_1(raw)
    r = chay("delta_1", d1, hd)
    assert r["validator_ok"] is True                       # ô đã đúng
    assert r["tang"] == "grounding"                        # cổng SAU mới bác
    assert "X: có initial_value nhưng thiếu source_fact_id" in r["loi"]
    assert r["servable"] is False


def test_R4_e2_DELTA_2_di_tron_khi_xuat_xu_CO_CAN_CU():
    raw, hd = _nguon("e2")
    d2, ghi = delta_2(raw, hd, "e2")
    r = chay("delta_2", d2, hd)
    assert r["servable"] is True and "121π" in set(r["bo_nho"].values())
    assert r["postconditions"] == "PASS" and r["scene3d"] == 12
    assert any("tru_co_tru_xy" in g for g in ghi)
    # ⚠️ Mục được chọn phải là mục GIỚI THIỆU X, không phải mục nói về Z.
    assert not any("z_tren_day_x" in g for g in ghi)


# ══ §4 · HAI Ô — tương đương khi cùng dữ kiện và cùng xuất xứ ════════════
def _hai_loi_khai():
    decls_iv = [
        {"name": "A", "type": "point3", "initial_value": [0, 0, 0],
         "source_fact_id": FID},
        {"name": "B", "type": "point3", "initial_value": [6, 0, 0],
         "source_fact_id": FID},
        {"name": "M", "type": "point3"}, {"name": "d", "type": "float"}]
    stmts = [
        {"kind": "construct_point", "target_var": "M",
         "expr": {"kind": "midpoint", "a": "A", "b": "B"}},
        {"kind": "assign", "target_var": "d",
         "expr": {"kind": "measure", "quantity": "distance", "of": "A",
                  "wrt": "M"}}]
    decls_dp = [{"name": "A", "type": "point3"}, {"name": "B", "type": "point3"},
                {"name": "M", "type": "point3"}, {"name": "d", "type": "float"}]
    stmts_dp = [
        {"kind": "declare_point", "target_var": "A", "at": [0, 0, 0],
         "source_fact_id": FID},
        {"kind": "declare_point", "target_var": "B", "at": [6, 0, 0],
         "source_fact_id": FID}] + stmts
    return _spec(decls_iv, stmts), _spec(decls_dp, stmts_dp)


def test_C1_initial_value_va_declare_point_at_CHO_KET_QUA_TUONG_DUONG():
    """Hai lối, cùng dữ kiện, cùng xuất xứ ⇒ cùng bộ nhớ và cùng đáp số."""
    a, b = _hai_loi_khai()
    hd = _hd([{"kind": "distance", "container": "A",
               "params": {"witness": "d", "wrt": "M"}}])
    ra, rb = verify_and_compile(hd, validate_semantic_program(a).spec), \
        verify_and_compile(hd, validate_semantic_program(b).spec)
    assert ra.executable and rb.executable
    ma = {k: str(v) for k, v in (ra.final_memory or {}).items()}
    mb = {k: str(v) for k, v in (rb.final_memory or {}).items()}
    assert ma == mb and ma["d"] == "3"


def test_C2_at_trong_KHAI_BAO_bi_bac__at_trong_CAU_LENH_thi_khong():
    a, b = _hai_loi_khai()
    hong = json.loads(json.dumps(a))
    hong["memory_declarations"][0]["at"] = hong["memory_declarations"][0].pop(
        "initial_value")
    assert validate_semantic_program(hong).ok is False
    assert validate_semantic_program(b).ok is True      # câu lệnh vẫn hợp lệ


def test_C3_co_CA_HAI_at_va_initial_value__luat_TUONG_MINH_khong_chon_ho():
    a, _ = _hai_loi_khai()
    ca_hai = json.loads(json.dumps(a))
    ca_hai["memory_declarations"][0]["at"] = [9, 9, 9]   # mâu thuẫn với iv
    v = validate_semantic_program(ca_hai)
    assert v.ok is False
    assert "ĐÃ có `initial_value`" in v.error and "bỏ `at`" in v.error
    # KHÔNG chọn hộ: lời từ chối không tự quyết ô nào thắng.
    assert "[9, 9, 9]" not in v.error


def test_C4_chan_doan_neu_DUONG_DAN_JSON_dung_chi_so():
    a, _ = _hai_loi_khai()
    h = json.loads(json.dumps(a))
    h["memory_declarations"][1]["at"] = [1, 2, 3]
    e = validate_semantic_program(h).error
    assert "memory_declarations[1].at" in e
    assert "memory_declarations[0]" not in e


def test_C5_chi_bao_khi_CO_DU_LIEU_BI_MAT__khong_bao_khoa_trang_tri():
    """Ranh giới của chẩn đoán, và nó hẹp có chủ đích.

    Bản đầu bác MỌI khoá lạ và bác oan 3/5 chương trình AI sinh trong artifact
    lịch sử — chúng đặt `label` trong khai báo. `label` là `Optional[str]`,
    một chuỗi TRANG TRÍ; bỏ nó không mất gì. `at` là `list[Any]`, một Ô GIÁ
    TRỊ THÔ; bỏ nó là mất toạ độ. Phép phân biệt dẫn từ annotation.
    """
    a, _ = _hai_loi_khai()

    trang_tri = json.loads(json.dumps(a))
    trang_tri["memory_declarations"][0]["label"] = "điểm A"
    assert validate_semantic_program(trang_tri).ok is True

    # Khoá KHÔNG ai sở hữu, MANG giá trị, và khai báo đang RỖNG ⇒ nuốt dữ kiện.
    bia = json.loads(json.dumps(a))
    bia["memory_declarations"][0].pop("initial_value")
    bia["memory_declarations"][0]["toa_do_bia"] = [1, 2, 3]
    e = validate_semantic_program(bia).error
    assert "toa_do_bia" in e and "Trường hợp lệ:" in e

    # Cùng khoá ấy nhưng khai báo ĐÃ có giá trị ⇒ không có gì mất, không bác.
    con_gt = json.loads(json.dumps(a))
    con_gt["memory_declarations"][0]["ghi_chu_rieng"] = "abc"
    assert validate_semantic_program(con_gt).ok is True


def test_C6_o_gia_tri_tho_DAN_XUAT_tu_annotation():
    from app.simulation.semantic_program.contract import MemoryDeclaration

    assert _o_gia_tri_tho(MemoryDeclaration) == "initial_value"


# ══ §4 · XUẤT XỨ KHÔNG ĐƯỢC NỚI — phản ví dụ ════════════════════════════
def test_P1_thieu_source_fact_id_van_bi_BAC():
    a, _ = _hai_loi_khai()
    h = json.loads(json.dumps(a))
    h["memory_declarations"][0].pop("source_fact_id")
    out = verify_and_compile(_hd(), validate_semantic_program(h).spec)
    assert out.stage_reached == "grounding"
    assert any("thiếu source_fact_id" in x for x in (out.details or []))


def test_P2_source_fact_id_KHONG_TON_TAI_van_bi_BAC():
    a, _ = _hai_loi_khai()
    h = json.loads(json.dumps(a))
    h["memory_declarations"][0]["source_fact_id"] = "khong_co_muc_nay"
    out = verify_and_compile(_hd(), validate_semantic_program(h).spec)
    assert out.stage_reached == "grounding"
    assert any("không có trong RequestContract" in x
               for x in (out.details or []))


def test_P3_diem_KHONG_XUAT_XU_bi_bac__con_muc_MANG_TEN_thi_khong_rang_buoc():
    """Ranh giới thật của cổng xuất xứ, đo bằng máy chứ không suy.

    ⚠️ Bản đầu của test này khẳng định *"điểm tự bịa bị bác"* bằng một điểm
    trỏ tới một mục dữ kiện CÓ THẬT — và nó **được phục vụ**. Tiền đề sai,
    không phải lỗ hệ: một mục mang TÊN (`values: ["A","B"]`) nói *"A và B là
    hai điểm đề cho"*, nó không nói chúng ở đâu. Toạ độ khi ấy là một lựa chọn
    HỆ QUY CHIẾU, đúng thứ `model_assumption` sinh ra để chở.

    Mục mang SỐ thì khác: `Tam: giá trị [10] không có trong mục 'f1'` — ở đó
    giá trị bị đối chiếu thật.

    Hành vi này **có từ trước wave** và không đổi: bản vá chỉ bác khoá lạ, mà
    khai báo dưới đây không có khoá lạ nào (`test_TIEM_4`).
    """
    a, _ = _hai_loi_khai()
    khong_nguon = json.loads(json.dumps(a))
    khong_nguon["memory_declarations"].append(
        {"name": "Kbia", "type": "point3", "initial_value": [7, 7, 7]})
    out = verify_and_compile(
        _hd(), validate_semantic_program(khong_nguon).spec)
    assert out.stage_reached == "grounding" and not out.servable
    assert any("Kbia" in x and "thiếu source_fact_id" in x
               for x in (out.details or []))

    co_nguon = json.loads(json.dumps(a))
    co_nguon["memory_declarations"].append(
        {"name": "Kbia", "type": "point3", "initial_value": [7, 7, 7],
         "source_fact_id": FID})
    assert verify_and_compile(
        _hd(), validate_semantic_program(co_nguon).spec).servable is True


def test_P3b_muc_MANG_SO_thi_toa_do_BI_DOI_CHIEU_that():
    """Nửa còn lại của ranh giới — nếu mất, `test_P3` sẽ đọc như một lời nới.

    ⚠️ Toạ độ phải KHÁC KHÔNG. `[0,0,0]` được miễn đối chiếu — nó không đóng
    góp thành phần nào để mà đối chiếu, và gốc toạ độ là lựa chọn hệ quy chiếu
    tự do. Bản đầu của test này dùng `[0,0,0]` nên nó đo phải đúng ca miễn, và
    xanh vì lý do sai.
    """
    from app.simulation.semantic_program.request_contract import RequestContract

    a, _ = _hai_loi_khai()
    h = json.loads(json.dumps(a))
    h["memory_declarations"][0]["initial_value"] = [5, 0, 0]
    h["memory_declarations"][0]["source_fact_id"] = "f_so"
    hd = RequestContract(
        problem_text="Cho hai điểm A và B. Gọi M là trung điểm AB.",
        input_facts=[
            {"fact_id": FID, "label": "A và B là hai điểm đề cho",
             "values": ["A", "B"], "provenance": "confirmed"},
            {"fact_id": "f_so", "label": "độ dài AB", "values": [6],
             "provenance": "confirmed"}],
        obligations=())
    out = verify_and_compile(hd, validate_semantic_program(h).spec)
    assert out.stage_reached == "grounding" and not out.servable
    assert any("không có trong mục" in x for x in (out.details or []))


def test_P4_diem_DAN_XUAT_hop_le_van_dung_va_do_duoc():
    a, _ = _hai_loi_khai()
    out = verify_and_compile(
        _hd([{"kind": "distance", "container": "A",
              "params": {"witness": "d", "wrt": "M"}}]),
        validate_semantic_program(a).spec)
    assert out.executable
    assert str((out.final_memory or {})["d"]) == "3"     # M dựng bằng midpoint


# ══ §4 · HỒI QUY ════════════════════════════════════════════════════════
@pytest.mark.parametrize("cid,mong", [("e1", "5"), ("e3", "9"), ("e5", "40")])
def test_H1_gold_e1_e3_e5_giu_nguyen_dap_so(cid, mong):
    from gold_affordance_ab import CA_MONG, chay_gold

    r = chay_gold(CA_MONG[cid])
    assert r["servable"] and r["exact_match"], r.get("details")
    assert mong in set(r["thuc_te"].values())


def test_H2_duong_thiet_dien_DA_DIEN_va_ca_NGOAI_MIEN_giu_hanh_vi():
    from gold_affordance_ab import CA_MONG, chay_gold

    da_dien = chay_gold(CA_MONG["e7"])
    assert da_dien["servable"] and da_dien["thuc_te"] == {"area": "18√3"}
    am = chay_gold(CA_MONG["e8"])
    assert not am["servable"]
    assert any("CURVED_SECTION_OUTSIDE_V1_CLOSURE" in x
               for x in am["details"])


# ══ §4 · CHẨN ĐOÁN PHẢI TỚI ĐƯỢC VÒNG SỬA (entrypoint sản phẩm) ═════════
def _chay_tong_hop(monkeypatch, raws):
    """Chạy `stage_semantic_program` thật; provider trả lần lượt `raws`."""
    import asyncio

    from app.ai import gemini as G
    from app.ai import pipeline as PL
    from app.simulation.semantic_program.domain_profile import DOMAIN_HINH_HOC

    goi: list[str] = []

    async def stub(api_key, system_prompt, user_text, schema=None,
                   temperature=0.2, image=None):
        goi.append(user_text)
        return raws[min(len(goi) - 1, len(raws) - 1)]

    monkeypatch.setattr(G, "call_gemini", stub)
    monkeypatch.setattr(PL, "call_gemini", stub)
    raw2, hd = _nguon("e6")
    spec, err = asyncio.run(PL.stage_semantic_program(
        "đề", {}, "stub-key", hd, domain=DOMAIN_HINH_HOC))
    return goi, spec, err


def test_D1_chan_doan_DI_VAO_prompt_sua_cua_luot_ke_tiep(monkeypatch):
    """Không đủ khi chẩn đoán chỉ đúng — nó phải TỚI được mô hình."""
    raw, hd = _nguon("e6")
    goi, spec, err = _chay_tong_hop(monkeypatch, [json.dumps(raw)])
    assert len(goi) >= 2, "không có lượt sửa nào"
    sua = goi[1]
    assert "memory_declarations[0].at" in sua
    assert "`at` là trường của `declare_point`" in sua
    assert "`initial_value`" in sua
    # Và chương trình thô của mô hình cũng đi kèm để nó tự đối chiếu.
    assert '"at": [0, 0, 0]' in sua or '"at":[0,0,0]' in sua


def test_D2_sua_dung_o_thi_luot_ke_tiep_DI_TRON(monkeypatch):
    """Vòng sửa khép được: lượt 2 gửi bản đã chuyển ô ⇒ chương trình hợp lệ."""
    raw, hd = _nguon("e6")
    d1, _ = delta_1(raw)
    goi, spec, err = _chay_tong_hop(
        monkeypatch, [json.dumps(raw), json.dumps(d1)])
    assert err is None and spec is not None
    out = verify_and_compile(hd, spec)
    assert out.servable and "400π" in {str(v) for v in
                                       (out.final_memory or {}).values()}


# ══ §5 · KẾT QUẢ ĐỐI CHIẾU A/B — biến thể sản phẩm là A ═════════════════
#
# Luật đăng ký của `MODEL_FACING_OPERATION_AFFORDANCE_ALIGNMENT` liệt SÁU điều
# kiện giữ B. Năm đạt; điều kiện *"B trả đúng ranh giới ở ca âm"* **không đạt**
# — `e8` không arm nào chạm tới bao đóng v1, cả hai chết ở lỗi xuất xứ điểm.
# Báo cáo wave ấy ghi nó là "ghi riêng" và vẫn nhận B; nhánh đăng ký nói khác:
# chưa đạt ⇒ đưa phần sản phẩm về A, giữ B làm ứng viên thử nghiệm.
#
# Lợi ích của B **không bị phủ nhận** (1/6 → 6/6, thắng 5 thua 0) và bằng chứng
# giữ nguyên byte trong `operation-affordance-ab-v1/`. Thứ bị hoàn là **cấu
# hình sản phẩm**, và chỉ nó.
def _the_C_local() -> str:
    return (GOC.parent / "docs" / "evaluation" / "geometry" /
            "minimal-card-fresh-confirmation" / "card_C.txt").read_text(
                encoding="utf-8")


def test_AB1_the_san_pham_GIU_hai_affordance_da_do_cua_C():
    """⚠️ Thẻ sản phẩm KHÔNG còn trùng byte `card_C`, và đó là ĐÚNG.

    `CURVED_MISSING_FAMILY_ROADMAP_AND_OBLIQUE_CYLINDER_ELLIPSE_FOUNDATION`
    (2026-09-07) thêm từ vựng elip. So byte thô từ nay chỉ nói *"thẻ đã đổi"* —
    câu vô ích, vì thẻ SẼ đổi mỗi lần mở năng lực. Câu còn giá trị hẹp hơn:
    **hai dòng đã đo có còn nguyên không**, và **phần chênh có chỉ là từ vựng
    không**.
    """
    from app.simulation.semantic_program.grammar_card import grammar_card

    the, C = grammar_card("hinh_hoc"), _the_C_local()
    for dong in (d for d in C.splitlines()
                 if "t = m/(m+n)" in d or d.strip().startswith("Xuất xứ:")):
        assert dong in the, f"mất một affordance đã đo: {dong[:60]}"
    mat = [d for d in C.splitlines() if d not in the.splitlines()]
    # ⚠️ Danh sách này là *"phần chênh được phép, và vì sao"* — mỗi mục là một
    # wave đã phân loại khoản chênh của nó, KHÔNG phải một chỗ nới cho tiện.
    #   · `type nhận đúng một trong` / `area(of:` / `diện tích một hình PHẲNG`
    #     — từ vựng elip (`CURVED_MISSING_FAMILY_…`);
    #   · `construct_curved_solid:` — ô `height` đi từ `tên` trần sang
    #     `tên<scalar|float|int>[…]` (`CURVED_SCALAR_AXIS_SCALE_REPAIR`).
    #     THUẦN đồng bộ schema–thẻ: mô tả đã nằm ở `contract.py` từ 2026-09-04.
    assert all(("type nhận đúng một trong" in d) or ("area(of:" in d)
               or ("diện tích một hình PHẲNG" in d)
               or ("construct_curved_solid:" in d) for d in mat), mat
    # Bản A cũ vẫn phải TÁI LẬP được — neo bằng chứng của ba wave A/B.
    A = (GOC.parent / "docs" / "evaluation" / "geometry" /
         "operation-affordance-ab-v1" / "card_A.txt").read_text(
             encoding="utf-8")
    assert len(A.encode("utf-8")) == 5472 and A != the


def test_AB2_ung_vien_B_van_TAI_LAP_duoc_tu_artifact():
    """Giữ B *trong bản thử nghiệm* — nếu artifact trôi thì bằng chứng mất."""
    import hashlib

    # Đọc dạng TEXT: trên Windows tệp lưu CRLF, còn thẻ gửi cho mô hình dùng
    # LF. So byte thô sẽ đo cái vỏ tệp thay vì đo nội dung thẻ.
    t = (GOC.parent / "docs" / "evaluation" / "geometry" /
         "operation-affordance-ab-v1" / "card_B.txt").read_text(
             encoding="utf-8")
    assert len(t.encode("utf-8")) == 5675
    assert hashlib.sha256(t.encode("utf-8")).hexdigest().startswith(
        "86134034116f9c07")
    assert "→circle3" in t and "curved_solid" in t.split("type nhận")[1][:200]


# ══ §5 · CACHE — kiểm bằng MỘT ROW THẬT, không bằng suy luận ════════════
def test_CA1_row_cache_baseline_VAN_HIT_sau_thay_doi():
    """Trường mà cache SO SÁNH là `policy_version`, không phải băm danh tính.

    Bản vá của wave này nằm ở **validator** — một tầng engine. `CACHE_VERSION`
    không đổi (81), nên một envelope `ok` đã cache của baseline vẫn hợp lệ để
    dùng lại. Và không envelope `ok` nào có thể sinh ra từ chương trình mà
    wave này bắt đầu bác: một khai báo `point3` nuốt mất toạ độ luôn chết ở
    `ir_static`, mà `main.py` chỉ cache khi `status == "ok"`.

    ⚠️ **ĐÍNH CHÍNH 2026-09-06 — `SEGMENT_RELATION_CONSISTENCY_VERIFICATION`.**
    Kết luận *"wave này không bump"* vẫn ĐÚNG cho wave này. Nhưng hằng số `81`
    ở dòng dưới từng đóng đinh một con số toàn cục, nên nó hết đúng ngay khi
    một wave SAU bump vì lý do của riêng nó — và wave ấy đã đến: cổng bất biến
    nguồn bác `served → từ chối`, mà `served` là thứ ĐƯỢC cache, nên bump là
    dọn rác thật. Phép kiểm giữ nguyên bản chất (*row ghi ở version hiện tại
    thì HIT*); chỉ thôi ghim một con số không thuộc về nó.
    """
    import json as _json

    from app import main as main_module
    from app.main import DSL_VERSION, _cache_key, _cache_lookup
    from app.persistence.db import SessionLocal, SimulationCache

    text = "Cho hai điểm A và B. Gọi M là trung điểm AB."
    key = _cache_key(text)
    env = {"status": "ok", "simulation_id": "generic.semantic_program"}
    with SessionLocal() as s:
        s.query(SimulationCache).filter_by(key=key).delete()
        s.add(SimulationCache(
            key=key, problem_text=text,
            simulation_id="generic.semantic_program",
            envelope_json=_json.dumps(env), dsl_version=DSL_VERSION,
            policy_version=main_module.CACHE_VERSION))
        s.commit()
        row = _cache_lookup(s, key)
        assert row is not None, "row baseline KHÔNG còn hit — cache đã hỏng"
        assert row.policy_version == main_module.CACHE_VERSION
        s.query(SimulationCache).filter_by(key=key).delete()
        s.commit()


def test_CA2_bam_danh_tinh_KHAC_truong_cache_so_sanh():
    """Hai thứ dễ lẫn: `semantic_environment_hash` nhận diện BẢN ĐO, còn cache
    sản phẩm so `policy_version`. Wave này không đụng cái nào."""
    import json as _json

    from app import main as main_module
    from app.runtime_identity import semantic_environment_hash

    khoa = _json.loads(
        (GOC / "cache_identity.lock.json").read_text(encoding="utf-8"))
    assert khoa["cache_version"] == main_module.CACHE_VERSION
    assert khoa["semantic_environment_hash"] == semantic_environment_hash()
    # ⚠️ Thẻ sản phẩm nay là **C** (2026-09-07) ⇒ băm thành phần `grammar_card`
    # đổi `e0fbbc84…` → `9685b06a…`. Đây là thành phần DUY NHẤT đổi trong lượt
    # áp dụng: prompts · synthesis_schema · analyze_schema · capability giữ
    # nguyên từng byte, và đó là bằng chứng máy cho câu "chỉ thẻ đổi".
    # ⚠️ BA thành phần đổi ở `CURVED_MISSING_FAMILY_ROADMAP_AND_OBLIQUE_
    # CYLINDER_ELLIPSE_FOUNDATION` (2026-09-07) — từ vựng hình học mới:
    #   grammar_card     9685b06a → 4b435fbb   (phép + kiểu mới trong thẻ)
    #   synthesis_schema 8c57c9de → d69661ce   (phép mới trong union ValueExpr)
    #   capability       85bd3167 → e0214b77   (`_CHU_KY` có thêm một hàng)
    # `prompts` và `analyze_schema` KHÔNG đổi: nghĩa vụ `area` đã có từ bump 78,
    # wave này chỉ nới tập KIỂU CHỦ THỂ của nó.
    # ⚠️ ĐÚNG BA thành phần ấy đổi LẦN NỮA ở `PLANE_FROM_EQUATION_REPRESENTATION`
    # (2026-09-07) — thêm câu lệnh `construct_plane_from_equation`:
    #   grammar_card     4b435fbb → 285292fe   (dòng lệnh mới trong thẻ)
    #   synthesis_schema d69661ce → 6ccef323   (tag mới trong union Statement)
    #   capability       e0214b77 → 4b1e2f80   (`_KIEU_DUNG` có thêm một hàng)
    # `prompts` và `analyze_schema` VẪN không đổi, và lần này câu ấy mang một
    # khẳng định riêng đáng ghi: bất biến `plane_equation` mà wave thêm là hợp
    # đồng **do SERVER sở hữu**, đọc từ câu văn của đề — nó không có mặt trong
    # lược đồ `analyze`, nên mô hình không được hỏi và không thể khai gì về nó.
    # ⚠️ `CURVED_SCALAR_AXIS_SCALE_REPAIR` (2026-09-07) đổi ĐÚNG HAI trong ba:
    #   grammar_card 285292fe → 2cc55280   (ô `height` nay có kiểu + vai trò)
    #   capability   4b1e2f80 → 72edf39f   (`_TOAN_HANG_LENH` thêm một ô)
    # `synthesis_schema` GIỮ NGUYÊN — lược đồ Pydantic vốn đã có ô `height`;
    # thứ đổi là những gì hệ KIỂM và những gì mô hình ĐỌC THẤY về ô ấy, không
    # phải hình dạng JSON nó được phép viết.
    # ⚠️ `CURVED_RADIUS_SLOT_AFFORDANCE_ADJUDICATION` (2026-09-07) đổi ĐÚNG
    # MỘT băm: `grammar_card` 2cc55280 → cc105e4f (dòng `Khối cong:`).
    # `capability` GIỮ NGUYÊN — wave không đụng `_CHU_KY`/`_KIEU_DUNG`/
    # `_TOAN_HANG_LENH`; nó chỉ NÓI RA một luật đã có.
    # ⚠️ `OBLIQUE_CONE_SECTION_FOUNDATION` (2026-09-08) đổi ĐÚNG HAI băm:
    #   grammar_card      cc105e4f → 6cbba188
    #   synthesis_schema  6ccef323 → 08dae8dc
    # Cùng MỘT nguyên nhân, và đó là điều đáng ghi: ô gợi ý `solid` của
    # `intersect_plane_curved_ellipse` nay nói *"hình trụ hoặc hình nón"*, và
    # chuỗi ấy là `description` của trường Pydantic — tức nó nằm ĐỒNG THỜI
    # trong thẻ văn phạm và trong lược đồ gửi đi. Một chuỗi, hai băm.
    # `capability` GIỮ NGUYÊN — wave không thêm phép, không thêm kiểu; nó mở
    # một NHÁNH KERNEL của phép đã có.
    assert khoa["components"]["grammar_card"].startswith("6cbba1885b2073fa")
    assert khoa["components"]["synthesis_schema"].startswith("08dae8dc5a90bcae")
    assert khoa["components"]["capability"].startswith("72edf39f6c10220d")
    # ⚠️ `PHOTO_PROBLEM_TO_SCENE_END_TO_END` (2026-09-13) đổi ĐÚNG MỘT băm:
    #   prompts  55ac1ca6 → c50c8c6b   (viết lại prompt ĐỌC ẢNH `transcribe.md`)
    # `grammar_card` · `synthesis_schema` · `analyze_schema` · `capability` GIỮ
    # NGUYÊN. Và `prompts` đổi không vì một prompt TẦNG B nào: dòng dưới dựng lại
    # giá trị cũ chỉ bằng cách trả riêng `transcribe.md` về `085cae6`.
    # ⚠️ `VISION_DIAGRAM_ONLY_PROVENANCE_GUARD_FIX` (2026-09-14) đổi ĐÚNG MỘT băm, lại vì `transcribe.md`:
    #   prompts  c50c8c6b → dceff16e   (luật 4 và 9: dữ kiện chỉ từ chữ; không lời đề thì để rỗng)
    # Bốn thành phần kia giữ nguyên; c50c8c6b dựng lại được chỉ bằng cách trả riêng file ấy về `d8ad614`.
    from tests.photo_problem_identity import (
        PROMPTS_TRUOC_PROVENANCE_GUARD,
        PROMPTS_TRUOC_WAVE,
        TRANSCRIBE_TAI_D8AD614,
        prompts_neu_transcribe_chua_doi,
        prompts_neu_transcribe_la,
    )

    assert khoa["components"]["prompts"].startswith("dceff16e4f6eb32c")
    assert prompts_neu_transcribe_la(TRANSCRIBE_TAI_D8AD614) == PROMPTS_TRUOC_PROVENANCE_GUARD
    assert prompts_neu_transcribe_chua_doi() == PROMPTS_TRUOC_WAVE
    assert khoa["components"]["analyze_schema"].startswith("515001b503af5c7c")


# ══ §4 · TIÊM LỖI ═══════════════════════════════════════════════════════
def test_TIEM_1_go_chan_doan_thi_loi_quay_ve_SAI_CHO(monkeypatch):
    """Khôi phục hành vi bỏ khoá im lặng ⇒ `e6` lại chết ở `ir_static`."""
    from app.simulation.semantic_program import validator as V

    monkeypatch.setattr(V, "_khoa_bi_bo_im_lang", lambda raw: None)
    raw, hd = _nguon("e6")
    r = chay("goc", raw, hd)
    assert r["validator_ok"] is True                     # lọt qua schema
    assert r["tang"] == "ir_static"
    assert "chưa có giá trị" in r["loi"]                 # chẩn đoán SAI CHỖ
    assert ".at" not in r["loi"]


def test_TIEM_2_go_phep_dan_xuat_o_gia_tri_thi_chan_doan_MAT_huong_sua(
        monkeypatch):
    from app.simulation.semantic_program import validator as V

    monkeypatch.setattr(V, "_o_gia_tri_tho", lambda m: None)
    a, _ = _hai_loi_khai()
    h = json.loads(json.dumps(a))
    h["memory_declarations"][0]["at"] = h["memory_declarations"][0].pop(
        "initial_value")
    e = V.validate_semantic_program(h).error
    assert "memory_declarations[0].at" in e              # vẫn nêu vị trí
    assert "chuyển giá trị ấy sang" not in e             # nhưng mất hướng sửa


def test_TIEM_3_go_phep_tra_chu_so_huu_thi_mat_CHO_NHAM(monkeypatch):
    from app.simulation.semantic_program import validator as V

    # Giữ "là ô giá trị" để chẩn đoán vẫn bắt, chỉ gỡ phần NÊU CHỦ SỞ HỮU.
    monkeypatch.setattr(V, "_chu_so_huu_truong", lambda k: ([], True))
    a, _ = _hai_loi_khai()
    h = json.loads(json.dumps(a))
    h["memory_declarations"][0]["at"] = [0, 0, 0]
    e = V.validate_semantic_program(h).error
    assert "memory_declarations[0].at" in e               # vẫn nêu vị trí
    assert "declare_point" not in e                       # mất chỗ nhầm


def test_TIEM_4_chan_doan_KHONG_bat_khi_chuong_trinh_dung():
    a, b = _hai_loi_khai()
    assert _khoa_bi_bo_im_lang(a) is None
    assert _khoa_bi_bo_im_lang(b) is None
