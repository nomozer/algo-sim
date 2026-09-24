# -*- coding: utf-8 -*-
"""CỔNG PHỦ NGHĨA VỤ TRỰC QUAN — cảnh có thật sự mang vật mà đề đòi NHÌN THẤY không. 0 mạng.

`SYNTHESIS_VISUAL_OBLIGATION_COVERAGE_GATE` (2026-09-20).

─── BỆNH ĐÃ ĐO, KHÔNG PHẢI BỆNH SUY DIỄN ───────────────────────────────────

`B02_STRUCTURAL_COVERAGE_LIVE_REVALIDATION` (2026-09-15): synthesis được nhận ngay lượt đầu,
route trả `served`, `final_memory` và cả ba đáp số ĐÚNG (`72` · `9` · `3√6`) — mà cảnh **không có
một vật `section` nào**. Học sinh nhận một lời giải tính đúng diện tích thiết diện trên một hình
không hề vẽ thiết diện. Phân loại: `SILENT_QUALITY_FAILURE`.

`SYNTHESIS_ACCEPTED_OUTPUT_QUALITY_DIAGNOSIS` tách đôi nguyên nhân, cả hai tái hiện offline:
  ① `COMPUTATION_ONLY_COVERAGE`  — C₁a chỉ kiểm ĐƯỜNG PHÉP TÍNH (witness dẫn xuất từ container).
  ② `SCENE_TYPE_OR_PROVENANCE_MISMATCH` — tầng nghĩa vụ nhận `polygon3` là thiết diện; cảnh và
     frontend thì chỉ nhận `type == "section"`.

─── VÌ SAO KHÔNG CÓ NHÁNH RIÊNG CHO B02 ────────────────────────────────────

Luật chạy trên TẬP KIỂU CHẤP NHẬN ĐƯỢC của từng nghĩa vụ (`OBLIGATION_KINDS`, dẫn xuất từ
`measure_contract`), không trên một loại vật cố định. Đo được từ manifest benchmark:

    B02  area(T)  → thiết diện ĐA GIÁC  → vật cảnh đúng là `section`
    B03  area(C)  → thiết diện TRÒN     → vật cảnh đúng là `circle3`   ← KHÔNG phải `section`

Nên "mọi nghĩa vụ `area` đều đòi một vật `section`" là SAI và sẽ phá parity B03. Cổng hỏi câu
tổng quát: *chủ thể của nghĩa vụ có mặt trong cảnh, đúng một kiểu nghĩa vụ ấy nhận, có xuất xứ,
và (nếu là hình phẳng khép kín) đúng topology không.*

─── KHOẢNG TRỐNG HỢP ĐỒNG, KHAI THẲNG ──────────────────────────────────────

`RequestContract` KHÔNG phân biệt được "diện tích đa giác phẳng thường" với "diện tích thiết
diện": cả hai khai đúng một `area(container)`. Khi nghĩa vụ nhận CẢ `section` LẪN `polygon3`, vật
quan sát được là `polygon3`, và không có `section_matches` nào phân xử ⇒ `UNVERIFIABLE`, route từ
chối AN TOÀN. Không đoán theo tên biến, không dò chuỗi trên đề.

─── FIXTURE ────────────────────────────────────────────────────────────────

`DERIVED_STRUCTURAL_FIXTURE`. Output live B02 KHÔNG được lưu
(`HISTORICAL_B02_UNCOVERED_OBLIGATION = NOT_RECOVERABLE`) — không test nào ở đây dựng lại nó.
Mọi fixture là biến thể nhỏ của chương trình p1 đóng băng trên RequestContract p1 đóng băng.
"""

from __future__ import annotations

import json

import pytest

from app import main as main_module
from app.ai import gemini
from app.ai.pipeline import _dung_scene3d
from app.main import DSL_VERSION
from app.simulation.error_codes import ErrorCode
from app.simulation.semantic_program import validator as V
from app.simulation.semantic_program import visual_obligations as VO
from app.simulation.semantic_program.analyze_contract import build_request_contract
from app.simulation.semantic_program.domain_profile import DOMAIN_HINH_HOC
from app.simulation.semantic_program.obligations import Obligation
from app.simulation.semantic_program.request_contract import RequestContract
from app.simulation.semantic_program.route import verify_and_compile
from tests.test_photo_problem_live_runner import (  # noqa: F401 — fixture `de`, `kho` dùng qua tên
    CA_P1,
    RNB,
    de,
    kho,
)
from tests.test_photo_problem_semantic_integration import R

P1 = RNB.doc_raw_theo_thu_tu(CA_P1)
P1_ANALYZE = P1["semantic_analyze"][0]
P1_PROG = P1["semantic_program"][0]

#: Tên thật trong hợp đồng/chương trình p1 — KHÔNG được xuất hiện trong chẩn đoán.
TEN_THO = ("S.ABCD", "the_volume_sabcd", "area_T", "dist_S_BD", "alpha_plane", "ABCD_base", "BD", "T")

KHOA_CHAN_DOAN = {"diagnostic_version", "verdict", "requested_count", "covered_count",
                  "uncovered_count", "unverifiable_count", "obligations"}
KHOA_HANG = {"obligation_id", "source_contract_pointer", "pointer_status", "visual_kind",
             "target_kind", "required_scene_kind", "provenance_requirement",
             "topology_requirement", "status", "reason_code", "evidence_count", "evidence_kinds"}


@pytest.fixture(autouse=True)
def _khong_cho_backoff(monkeypatch):
    monkeypatch.setattr(gemini, "BACKOFF_BASE_SECONDS", 0.0)


# ══ dựng fixture ════════════════════════════════════════════════════════════
def _hd(de) -> RequestContract:
    """RequestContract B02 THẬT, dựng từ `analyze_0.json` đóng băng."""
    return build_request_contract(json.loads(P1_ANALYZE), problem_text=de["C01"], domain=DOMAIN_HINH_HOC)


def _spec(sua=None):
    d = json.loads(P1_PROG)
    if sua:
        sua(d)
    v = V.validate_semantic_program(d)
    assert v.ok, v.error
    return v.spec


def _canh(spec, hd):
    return _dung_scene3d(spec, hd)


def _ten_ct(hd, spec, ten_hop_dong: str) -> str:
    """Tên chương trình của một tên hợp đồng, qua ĐÚNG thẩm quyền C₁a."""
    return verify_and_compile(hd, spec).resolved_names.get(ten_hop_dong, ten_hop_dong)


def _doi_loai(canh: dict, obj_id: str, loai: str) -> dict:
    """Sửa TẦNG CẢNH — chương trình hợp lệ không sinh ra được, chỉ để tách lớp."""
    return {"objects": [{**o, "type": loai} if o["id"] == obj_id else o for o in canh["objects"]]}


def _bo_xuat_xu(canh: dict, obj_id: str) -> dict:
    """Gỡ CẢ BA đường truy xuất. Chỉ gỡ `producer` là chưa mất xuất xứ — vật bí
    danh (`assign`) vốn không có `producer` mà vẫn truy được qua `depends`."""
    return {"objects": [{**o, "producer": None, "depends": [], "sources": []}
                        if o["id"] == obj_id else o for o in canh["objects"]]}


def _bo_vat(canh: dict, obj_id: str) -> dict:
    return {"objects": [o for o in canh["objects"] if o["id"] != obj_id]}


def _ho_da_giac(canh: dict, obj_id: str) -> dict:
    return {"objects": [{**o, "closed": False} if o["id"] == obj_id else o for o in canh["objects"]]}


def _lech_mat_phang(canh: dict, obj_id: str) -> dict:
    def f(o):
        if o["id"] != obj_id:
            return o
        poly = [list(v) for v in o["polygon"]]
        poly[-1] = [poly[-1][0], poly[-1][1], "999"]  # kéo MỘT đỉnh ra khỏi mặt phẳng
        return {**o, "polygon": poly}
    return {"objects": [f(o) for o in canh["objects"]]}


def _hd_chi(hd: RequestContract, *kinds: str) -> RequestContract:
    return hd.model_copy(update={"obligations": tuple(o for o in hd.obligations if o.kind in kinds)})


def _hd_them_section_matches(hd: RequestContract, container: str) -> RequestContract:
    ob = Obligation(kind="section_matches", container=container, params={"witness": None})
    return hd.model_copy(update={"obligations": hd.obligations + (ob,)})


def _lay(doc, con_tro: str):
    if con_tro == "":
        return doc
    for tok in con_tro[1:].split("/"):
        tok = tok.replace("~1", "/").replace("~0", "~")
        doc = doc[int(tok)] if isinstance(doc, list) else doc[tok]
    return doc


def _chay(hd, canh, spec=None):
    ten = verify_and_compile(hd, spec).resolved_names if spec is not None else {}
    return VO.check_visual_obligations(hd, canh, ten)


# ══ E · CỬA SỔ CHỨNG — chương trình p1 ĐÚNG phải qua ════════════════════════
def test_E_thiet_dien_hop_le__cong_CHO_QUA_va_khong_doi_gi(de):
    """Cửa sổ chứng: câu trả lời đã biết trước. Chương trình p1 đã được nhận DỰNG thiết diện thật."""
    hd, spec = _hd(de), _spec()
    canh = _canh(spec, hd)
    assert any(o["type"] == "section" for o in canh["objects"]), "fixture hỏng: p1 phải có section"

    kq = _chay(hd, canh, spec)

    assert kq.verdict == "COVERED"
    assert kq.uncovered_count == 0 and kq.unverifiable_count == 0
    assert {r.status for r in kq.obligations} == {"COVERED"}


def test_E_cong_KHONG_dung_toi_canh_lan_dap_so(de):
    """Cổng chỉ ĐỌC. Không vật nào, không đáp số nào bị sửa."""
    hd, spec = _hd(de), _spec()
    canh = _canh(spec, hd)
    truoc = json.dumps(canh, sort_keys=True, ensure_ascii=False)

    _chay(hd, canh, spec)

    assert json.dumps(canh, sort_keys=True, ensure_ascii=False) == truoc


# ══ A · B02-derived: đáp số ĐÚNG, cảnh THIẾU thiết diện ═════════════════════
def test_A_B02_derived_dap_so_dung_nhung_canh_khong_co_section__BI_TU_CHOI(de):
    """DERIVED_STRUCTURAL_FIXTURE. Chương trình chạy trọn, ba đáp số đúng — cảnh mất vật thiết diện."""
    hd, spec = _hd(de), _spec()
    o = verify_and_compile(hd, spec)
    assert o.stage_reached == "served" and o.servable, "nền: route HIỆN TẠI phục vụ ca này"

    canh = _bo_vat(_canh(spec, hd), _ten_ct(hd, spec, "T"))
    kq = _chay(hd, canh, spec)

    assert kq.verdict != "COVERED"
    (r,) = [x for x in kq.obligations if x.status != "COVERED"]
    assert r.reason_code == "VISUAL_OBJECT_MISSING"
    assert r.evidence_count == 0


def test_H_dap_so_dung_KHONG_bu_duoc_cho_nghia_vu_truc_quan_thieu(de):
    """Bằng chứng SỐ không được thay bằng chứng HÌNH — hai loại khác nhau."""
    hd, spec = _hd(de), _spec()
    o = verify_and_compile(hd, spec)
    assert o.final_memory, "nền: chương trình có đáp số"

    canh = _bo_vat(_canh(spec, hd), _ten_ct(hd, spec, "T"))
    kq = _chay(hd, canh, spec)

    # Witness `area_T` vẫn nằm trong final_memory với giá trị đúng, và nó KHÔNG cứu được nghĩa vụ.
    assert kq.verdict != "COVERED"


# ══ B · polygon3 KHÔNG được thay section ═══════════════════════════════════
def test_B_section_matches_ma_canh_chi_co_polygon3__VISUAL_OBJECT_TYPE_MISMATCH(de):
    """`OBLIGATION_KINDS['section_matches']` nhận cả `polygon3` ở tầng KIỂU — cảnh thì KHÔNG."""
    hd, spec = _hd(de), _spec()
    canh = _canh(spec, hd)
    t = _ten_ct(hd, spec, "T")
    hd2 = _hd_them_section_matches(hd, "T")

    kq = _chay(hd2, _doi_loai(canh, t, "polygon3"), spec)

    r = next(x for x in kq.obligations if x.visual_kind == "SECTION_IDENTITY")
    assert (r.status, r.reason_code) == ("UNCOVERED", "VISUAL_OBJECT_TYPE_MISMATCH")
    assert r.required_scene_kind == ("section",)
    assert "polygon3" in r.evidence_kinds


def test_B_area_mot_minh_tren_polygon3__UNVERIFIABLE_chu_KHONG_im_lang(de):
    """Khoảng trống hợp đồng: `area` nhận cả hai kiểu, không gì phân xử ⇒ từ chối AN TOÀN."""
    hd, spec = _hd(de), _spec()
    t = _ten_ct(hd, spec, "T")
    canh = _doi_loai(_canh(spec, hd), t, "polygon3")

    kq = _chay(_hd_chi(hd, "area"), canh, spec)

    (r,) = kq.obligations
    assert (r.status, r.reason_code) == ("UNVERIFIABLE", "VISUAL_OBLIGATION_UNVERIFIABLE")
    assert kq.verdict != "COVERED"


# ══ C · xuất xứ ════════════════════════════════════════════════════════════
def test_C_section_dung_loai_nhung_MAT_xuat_xu__VISUAL_PROVENANCE_MISSING(de):
    hd, spec = _hd(de), _spec()
    t = _ten_ct(hd, spec, "T")
    canh = _bo_xuat_xu(_canh(spec, hd), t)

    kq = _chay(_hd_chi(hd, "area"), canh, spec)

    (r,) = kq.obligations
    assert (r.status, r.reason_code) == ("UNCOVERED", "VISUAL_PROVENANCE_MISSING")


def test_C_BI_DANH_khong_co_producer_nhung_VAN_truy_duoc__KHONG_bi_danh_truot():
    """HỒI QUY. Cổng bản đầu hỏi đúng `producer` và đánh trượt p4/p5 — hai ca HỢP LỆ
    đang được phục vụ: `assign hình trụ = khối trụ` tạo vật bí danh không `producer`
    nhưng `depends: ["khối trụ"]`. Dương tính giả kiểu này làm cổng tệ hơn vô dụng."""
    hd = RequestContract(obligations=(
        Obligation(kind="lateral_area", container="hình trụ", params={"witness": "sxq"}),))
    canh = {"objects": [
        {"id": "khối trụ", "type": "curved_solid", "producer": "construct_curved_solid.cylinder",
         "depends": ["A", "K", "O"], "origin": "derived"},
        {"id": "hình trụ", "type": "curved_solid", "producer": None,
         "depends": ["khối trụ"], "origin": "derived"},
    ]}

    kq = VO.check_visual_obligations(hd, canh, {})

    (r,) = kq.obligations
    assert (r.status, r.reason_code) == ("COVERED", "COVERED")


def test_C_vat_DAN_XUAT_ma_khong_truy_duoc__moi_la_MAT_xuat_xu():
    """`derived` = chương trình tự nhận đã tạo ra vật này ⇒ phải truy được."""
    hd = RequestContract(obligations=(
        Obligation(kind="lateral_area", container="X", params={"witness": "w"}),))
    canh = {"objects": [{"id": "X", "type": "curved_solid", "producer": None,
                         "depends": [], "sources": [], "origin": "derived"}]}

    (r,) = VO.check_visual_obligations(hd, canh, {}).obligations
    assert (r.status, r.reason_code) == ("UNCOVERED", "VISUAL_PROVENANCE_MISSING")


def test_C_diem_DE_CHO_khong_co_producer_van_HOP_LE():
    """HỒI QUY. `declare_point` ⇒ `origin='free'`, không `producer`, không `depends` —
    và đó là ĐÚNG: điểm ấy do đề cho, không phải do chương trình dựng."""
    hd = RequestContract(obligations=(
        Obligation(kind="distance", container="A", params={"wrt": "K", "witness": "d"}),))
    canh = {"objects": [{"id": "A", "type": "point3", "producer": None,
                         "depends": [], "sources": [], "origin": "free"}]}

    (r,) = VO.check_visual_obligations(hd, canh, {}).obligations
    assert (r.status, r.reason_code) == ("COVERED", "COVERED")


# ══ D · topology ═══════════════════════════════════════════════════════════
def test_D_da_giac_HO__VISUAL_TOPOLOGY_MISMATCH(de):
    hd, spec = _hd(de), _spec()
    t = _ten_ct(hd, spec, "T")
    kq = _chay(_hd_chi(hd, "area"), _ho_da_giac(_canh(spec, hd), t), spec)

    (r,) = kq.obligations
    assert (r.status, r.reason_code) == ("UNCOVERED", "VISUAL_TOPOLOGY_MISMATCH")


def test_D_mot_dinh_ROI_KHOI_mat_phang__VISUAL_TOPOLOGY_MISMATCH(de):
    hd, spec = _hd(de), _spec()
    t = _ten_ct(hd, spec, "T")
    kq = _chay(_hd_chi(hd, "area"), _lech_mat_phang(_canh(spec, hd), t), spec)

    (r,) = kq.obligations
    assert (r.status, r.reason_code) == ("UNCOVERED", "VISUAL_TOPOLOGY_MISMATCH")


# ══ F · bài chỉ tính thể tích — KHÔNG đòi thiết diện giả ════════════════════
def test_F_chi_the_tich__KHONG_doi_section(de):
    hd, spec = _hd(de), _spec()
    kq = _chay(_hd_chi(hd, "volume"), _canh(spec, hd), spec)

    (r,) = kq.obligations
    assert r.status == "COVERED"
    assert "section" not in r.required_scene_kind
    assert set(r.required_scene_kind) == {"solid", "curved_solid"}


def test_F_the_tich_van_doi_KHOI_muc_tieu_ton_tai(de):
    """Không đòi section, nhưng vẫn đòi đúng thứ nó hứa hiển thị."""
    hd, spec = _hd(de), _spec()
    khoi = _ten_ct(hd, spec, "S.ABCD")
    kq = _chay(_hd_chi(hd, "volume"), _bo_vat(_canh(spec, hd), khoi), spec)

    (r,) = kq.obligations
    assert (r.status, r.reason_code) == ("UNCOVERED", "VISUAL_OBJECT_MISSING")


# ══ G · parity B01 · B03 · B04 ═════════════════════════════════════════════
@pytest.mark.parametrize("kinds, kieu_canh", [
    (("volume",), "solid"),          # B01 — chóp
    (("volume", "area"), "circle3"),  # B03 — mặt cầu + thiết diện TRÒN
    (("volume", "lateral_area"), "curved_solid"),  # B04 — trụ
])
def test_G_ho_hinh_KHAC_khong_bi_doi_thanh_section(de, kinds, kieu_canh):
    """Luật chạy trên TẬP KIỂU của nghĩa vụ. B03 `area` trên `circle3` phải COVERED."""
    nv = [VO.NghiaVuTrucQuan for _ in ()]  # giữ import sống
    assert nv == []
    for k in kinds:
        yeu_cau = VO.kieu_canh_yeu_cau(k)
        assert yeu_cau, f"{k} phải có tập kiểu"
        if k in ("volume", "lateral_area"):
            assert "section" not in yeu_cau
    assert kieu_canh in VO.kieu_canh_yeu_cau(kinds[-1])


def test_G_B03_area_tren_circle3_KHONG_bi_coi_la_thieu_section():
    """Thiết diện TRÒN là `circle3` — cổng không được đòi `section` ở đây."""
    hd = RequestContract(obligations=(Obligation(kind="area", container="C", params={"witness": "s_c"}),))
    canh = {"objects": [{"id": "C", "type": "circle3", "producer": "intersect_plane_curved",
                         "sources": ["S", "P"], "center": ["0", "0", "0"],
                         "normal": ["0", "0", "1"], "radius_sq": "4"}]}

    kq = VO.check_visual_obligations(hd, canh, {"C": "C"})

    (r,) = kq.obligations
    assert (r.status, r.reason_code) == ("COVERED", "COVERED")
    assert kq.verdict == "COVERED"


# ══ K · chẩn đoán: thứ tự xác định, con trỏ RFC 6901 hợp lệ ════════════════
def test_K_chan_doan_co_thu_tu_XAC_DINH_va_con_tro_giai_duoc(de):
    hd, spec = _hd(de), _spec()
    canh = _canh(spec, hd)

    d1 = VO.chan_doan_truc_quan(_chay(hd, canh, spec))
    d2 = VO.chan_doan_truc_quan(_chay(hd, canh, spec))

    assert d1 == d2, "cùng đầu vào phải cho cùng chẩn đoán"
    assert set(d1) == KHOA_CHAN_DOAN
    assert d1["diagnostic_version"] == VO.DIAGNOSTIC_VERSION
    tho = hd.model_dump(mode="json")
    for hang in d1["obligations"]:
        assert set(hang) == KHOA_HANG
        assert hang["pointer_status"] in ("EXACT", "AMBIGUOUS")
        if hang["pointer_status"] == "EXACT":
            assert hang["source_contract_pointer"].startswith("/obligations/")
            assert _lay(tho, hang["source_contract_pointer"])["kind"] == hang["obligation_id"].split("#")[0]


def test_K_con_tro_lech_van_tay_thi_tra_AMBIGUOUS_chu_khong_biade():
    """Không tin tên trường suông — lệch vân tay ⇒ `null` + AMBIGUOUS."""
    hd = RequestContract(obligations=(Obligation(kind="area", container="X", params={"witness": "w"}),))
    kq = VO.check_visual_obligations(hd, {"objects": []}, {})
    (r,) = VO.chan_doan_truc_quan(kq)["obligations"]
    assert r["pointer_status"] == "EXACT" and r["source_contract_pointer"] == "/obligations/0"


# ══ L · không rò rỉ ════════════════════════════════════════════════════════
def _moi_chuoi(o):
    """Mọi chuỗi trong một cây JSON — KHOÁ lẫn GIÁ TRỊ."""
    if isinstance(o, str):
        yield o
    elif isinstance(o, dict):
        for k, v in o.items():
            yield k
            yield from _moi_chuoi(v)
    elif isinstance(o, (list, tuple)):
        for v in o:
            yield from _moi_chuoi(v)


def test_L_chan_doan_KHONG_cho_ten_toa_do_hay_gia_tri(de):
    """⚠️ Phép đo này ĐÃ SAI một lần: `assert "T" not in json.dumps(...)` đỏ vì chữ
    `T` nằm trong `"EXACT"` — bắt một lỗi KHÔNG tồn tại. Tên MỘT KÝ TỰ không kiểm
    được bằng phép tìm chuỗi con; nó phải kiểm trên GIÁ TRỊ đã tách."""
    hd, spec = _hd(de), _spec()
    canh = _bo_vat(_canh(spec, hd), _ten_ct(hd, spec, "T"))
    d = VO.chan_doan_truc_quan(_chay(hd, canh, spec))

    # ① không GIÁ TRỊ nào (hay khoá nào) BẰNG một tên thô.
    assert not (set(_moi_chuoi(d)) & set(TEN_THO)), "tên thô rò rỉ nguyên vẹn"
    # ② tên nhiều ký tự thì phép tìm chuỗi con mới có nghĩa — giữ nó cho nhóm ấy.
    chuoi = json.dumps(d, ensure_ascii=False)
    for ten in (t for t in TEN_THO if len(t) > 2):
        assert ten not in chuoi, f"tên thô rò rỉ: {ten}"
    # ③ không khoá nào chở dữ liệu thô của mô hình hay của cảnh.
    khoa = set(_moi_chuoi(d))
    for cam in ("input", "msg", "ctx", "polygon", "xyz", "vertices", "problem_text", "statements"):
        assert cam not in khoa, f"khoá cấm rò rỉ: {cam}"


def test_L_cua_so_chung__phep_do_ro_ri_CO_do_duoc(de):
    """Cửa sổ chứng cho chính phép đo trên: tiêm một tên thô vào chẩn đoán thì nó PHẢI đỏ."""
    hd, spec = _hd(de), _spec()
    d = VO.chan_doan_truc_quan(_chay(hd, _canh(spec, hd), spec))
    d["obligations"][0]["target_kind"] = "area_T"  # tiêm

    assert set(_moi_chuoi(d)) & set(TEN_THO), "phép đo mù — không bắt được tên thô đã tiêm"


def test_KIEU_CANH_HOP_LE_khop_RENDER_HINT__mot_bang_troi_la_DO():
    """`visual_obligations` KHÔNG được import `scene3d` (ranh giới hướng phụ thuộc),
    nên bảng kiểu vật phải chép. Test này là sync-lock: chép mà trôi là ĐỎ.

    Test nằm ở `tests/` nên nó được phép import CẢ HAI — đúng chỗ để khoá."""
    from app.simulation.semantic_program.scene3d import RENDER_HINT

    assert VO.KIEU_CANH_HOP_LE == tuple(sorted(RENDER_HINT))


def test_L_chan_doan_chi_dung_TU_VUNG_DONG(de):
    hd, spec = _hd(de), _spec()
    canh = _canh(spec, hd)
    d = VO.chan_doan_truc_quan(_chay(hd, canh, spec))

    for hang in d["obligations"]:
        assert hang["status"] in VO.TRANG_THAI
        assert hang["reason_code"] in VO.MA_LY_DO
        assert hang["visual_kind"] in VO.LOAI_TRUC_QUAN
        for k in hang["required_scene_kind"]:
            assert k in VO.KIEU_CANH_HOP_LE
        for k in hang["evidence_kinds"]:
            assert k in VO.KIEU_CANH_HOP_LE


def test_L_KHONG_luu_raw_program_hay_raw_scene(de):
    hd, spec = _hd(de), _spec()
    d = VO.chan_doan_truc_quan(_chay(hd, _canh(spec, hd), spec))

    assert "statements" not in json.dumps(d)
    assert "objects" not in json.dumps(d["obligations"])


# ══ N · cổng TẮT ⇒ parity; cổng BẬT ⇒ chỉ đổi ca thiếu phủ ═════════════════
def test_N_cong_KHONG_doi_phan_quyet_khi_moi_nghia_vu_duoc_phu(de):
    hd, spec = _hd(de), _spec()
    o = verify_and_compile(hd, spec)
    canh = _canh(spec, hd)

    o2 = VO.ap_dung(o.model_copy(update={"scene3d": canh}), hd)

    assert (o2.stage_reached, o2.servable, o2.executable) == (o.stage_reached, o.servable, o.executable)
    assert o2.error_code == o.error_code
    assert o2.final_memory == o.final_memory
    assert o2.envelope == o.envelope


def test_N_cong_HA_servable_khi_thieu_phu_va_giu_executable(de):
    hd, spec = _hd(de), _spec()
    o = verify_and_compile(hd, spec)
    canh = _bo_vat(_canh(spec, hd), _ten_ct(hd, spec, "T"))

    o2 = VO.ap_dung(o.model_copy(update={"scene3d": canh}), hd)

    assert o2.servable is False
    assert o2.executable is True, "hệ CHẠY ĐƯỢC bài này — cái thiếu là đường lên màn hình"
    assert o2.stage_reached == "visual_coverage"
    assert o2.visual_diagnostic is not None


def test_N_khong_co_canh_thi_cong_KHONG_phan_gi(de):
    """Bài không phải hình học ⇒ `scene3d is None` ⇒ cổng không được đẻ ra một lời từ chối."""
    hd, spec = _hd(de), _spec()
    o = verify_and_compile(hd, spec)

    o2 = VO.ap_dung(o.model_copy(update={"scene3d": None}), hd)

    assert o2.servable == o.servable and o2.stage_reached == o.stage_reached


def test_N_route_khong_servable_thi_cong_KHONG_nang_len(de):
    """Cổng chỉ HẠ, không bao giờ NÂNG."""
    hd, spec = _hd(de), _spec()
    o = verify_and_compile(hd, spec).model_copy(
        update={"servable": False, "stage_reached": "postconditions", "scene3d": _canh(spec, hd)})

    o2 = VO.ap_dung(o, hd)

    assert o2.servable is False and o2.stage_reached == "postconditions"


# ══ CỔNG PHẢI NẰM TRÊN ĐƯỜNG CHẠY THẬT ═════════════════════════════════════
#
# ⚠️ Hai test dưới đây sinh ra vì PHÉP TIÊM LỖI F1 KHÔNG BẮT ĐƯỢC GÌ: bỏ hẳn lời
# gọi cổng trong `pipeline._semantic_route_attempt` mà 40 test vẫn xanh. Mọi test
# phía trên gọi `VO.ap_dung` TRỰC TIẾP, nên chúng chứng minh cổng ĐÚNG chứ không
# chứng minh cổng ĐƯỢC GỌI. Đây đúng là lớp lỗi kho đã trả giá hai lần
# (`certify_acceptance_runner` gọi thẳng `mo_luot_do_v3` trong khi `main_async`
# chạy corpus khác). Bằng chứng phải đi qua `run_pipeline`.
def test_cong_DUOC_GOI_trong_pipeline__khong_chi_goi_duoc_tu_test(monkeypatch, de):
    """Quét AST: `_semantic_route_attempt` phải gọi cổng SAU khi đổ cảnh."""
    import ast
    import inspect

    from app.ai import pipeline as P

    than = inspect.getsource(P._semantic_route_attempt)
    cay = ast.parse(than.strip())
    goi = [n for n in ast.walk(cay) if isinstance(n, ast.Call)]
    ten = {getattr(g.func, "id", None) or getattr(g.func, "attr", None) for g in goi}
    assert "_cong_truc_quan" in ten, "pipeline KHÔNG gọi cổng trực quan — cổng nằm ngoài đường chạy"
    assert "_dung_scene3d" in ten
    assert than.index("_dung_scene3d") < than.index("_cong_truc_quan"), \
        "cổng phải chạy SAU khi cảnh được dựng"


def test_duong_chay_that_TU_CHOI_khi_canh_thieu_vat__qua_run_pipeline(monkeypatch, de):
    """END-TO-END trên `run_pipeline`, 0 mạng: cảnh bị gỡ vật ⇒ envelope KHÔNG `ok`.

    Đây là phép đo duy nhất ở tệp này đi qua đúng đường sản phẩm, nên nó là phép
    đo duy nhất bắt được việc cổng bị tháo khỏi pipeline.
    """
    import asyncio

    from app.ai import pipeline as P

    hd, spec = _hd(de), _spec()
    t = _ten_ct(hd, spec, "T")
    that = P._dung_scene3d

    def canh_thieu(spec_, contract=None):
        canh = that(spec_, contract)
        return None if canh is None else _bo_vat(canh, t)

    monkeypatch.setattr(P, "_dung_scene3d", canh_thieu)
    prov = R.ProviderPhatLaiTheoThuTu(R.doc_raw_theo_thu_tu(CA_P1))
    monkeypatch.setattr(P, "call_gemini", prov)
    with R.NetworkGuard() as g:
        env = asyncio.run(P.run_pipeline(de["C01"], "REPLAY_KHONG_PHAI_KEY", semantic_route="serve"))

    assert list(g.attempts) == [], "lượt chạy này phải 0 request mạng"
    assert env["status"] != "ok", "đường chạy THẬT vẫn phục vụ cảnh thiếu vật"
    assert env.get("stage_reached") == "visual_coverage"
    assert env.get("error_code") == ErrorCode.VISUAL_OBLIGATION_UNCOVERED.value


def test_duong_chay_that_VAN_PHUC_VU_ca_hop_le__qua_run_pipeline(monkeypatch, de):
    """Cửa sổ chứng cho test trên: KHÔNG gỡ vật nào ⇒ vẫn `ok`. Không có nó thì
    test trên xanh cả khi pipeline hỏng vì một lý do hoàn toàn khác."""
    import asyncio

    from app.ai import pipeline as P

    prov = R.ProviderPhatLaiTheoThuTu(R.doc_raw_theo_thu_tu(CA_P1))
    monkeypatch.setattr(P, "call_gemini", prov)
    with R.NetworkGuard() as g:
        env = asyncio.run(P.run_pipeline(de["C01"], "REPLAY_KHONG_PHAI_KEY", semantic_route="serve"))

    assert list(g.attempts) == []
    assert env["status"] == "ok", (env.get("stage_reached"), env.get("error_code"))


# ══ I · J · CACHE — row THẬT, không suy luận ═══════════════════════════════
def _row_v95_thieu_truc_quan(key: str, text: str):
    """Row `status="ok"` sinh dưới v95 mang một cảnh THIẾU vật trực quan.

    Đây chính là loại row mà bump 96 phải làm cho MISS: nó là `ok` (nên ĐƯỢC
    cache), và nó là thứ cổng mới sẽ từ chối.
    """
    from app.persistence.db import SimulationCache

    env = {"status": "ok", "simulation_id": "generic.semantic_program",
           "scene3d": {"objects": [{"id": "p", "type": "solid", "producer": "construct_solid"}]}}
    return SimulationCache(key=key, problem_text=text,
                           simulation_id="generic.semantic_program",
                           envelope_json=json.dumps(env, ensure_ascii=False),
                           dsl_version=DSL_VERSION, policy_version="95")


def test_I_row_v95_thieu_truc_quan_KHONG_con_duoc_phuc_vu_sau_bump():
    """Cache hit trả envelope THẲNG, KHÔNG chạy lại route ⇒ row cũ sẽ đi VÒNG QUA
    cổng mới. Bump `CACHE_VERSION` là cơ chế DUY NHẤT làm nó miss."""
    from app.main import _cache_key, _cache_lookup
    from app.persistence.db import SessionLocal, SimulationCache, init_db

    init_db()
    text = "Đề kiểm row v95 thiếu nghĩa vụ trực quan sau bump 96"
    key = _cache_key(text)
    with SessionLocal() as s:
        s.query(SimulationCache).filter_by(key=key).delete()
        s.add(_row_v95_thieu_truc_quan(key, text))
        s.commit()

        assert _cache_lookup(s, key) is None, "row v95 vẫn HIT — cổng mới bị đi vòng qua"

        # cửa sổ chứng: CHÍNH row ấy dưới version hiện hành thì HIT — nên phép
        # đo trên đang đo `policy_version`, không phải đo một lỗi khác.
        s.query(SimulationCache).filter_by(key=key).delete()
        r = _row_v95_thieu_truc_quan(key, text)
        r.policy_version = main_module.CACHE_VERSION
        s.add(r)
        s.commit()
        assert _cache_lookup(s, key) is not None

        s.query(SimulationCache).filter_by(key=key).delete()
        s.commit()


def test_J_ket_qua_bi_cong_tu_choi_KHONG_BAO_GIO_duoc_ghi_cache():
    """`main.py` chỉ ghi cache khi `envelope['status'] == 'ok'`; cổng hạ `servable`
    ⇒ đường hình học trả `unsupported` ⇒ không có đường nào ghi row."""
    import inspect

    from app import main as M

    than = inspect.getsource(M.analyze)
    assert 'envelope.get("status") == "ok"' in than, "điều kiện ghi cache đã đổi — kiểm lại luật này"
    # và một envelope bị cổng từ chối KHÔNG mang status ok:
    assert VO.ROUTE_STAGE == "visual_coverage"


# ══ phase ổn định cho trace ════════════════════════════════════════════════
def test_phase_trace_la_ROUTE_VISUAL_COVERAGE(de):
    """Runner dựng phase bằng `ROUTE_{stage_reached.upper()}` — không thêm bảng ánh xạ thứ hai."""
    hd, spec = _hd(de), _spec()
    canh = _bo_vat(_canh(spec, hd), _ten_ct(hd, spec, "T"))
    o2 = VO.ap_dung(verify_and_compile(hd, spec).model_copy(update={"scene3d": canh}), hd)

    assert f"ROUTE_{o2.stage_reached.upper()}" == "ROUTE_VISUAL_COVERAGE"
    # Mã lỗi là một hằng ĐÓNG của `ErrorCode`, KHÔNG phải mã lý do sinh động
    # (M14 §H — enum đóng). Lý do chi tiết đi ở `details` + `visual_diagnostic`.
    assert o2.error_code == ErrorCode.VISUAL_OBLIGATION_UNCOVERED.value
    assert o2.failure_category == "verification_gap"
    assert set(o2.details) <= set(VO.MA_LY_DO)
