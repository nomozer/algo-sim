# -*- coding: utf-8 -*-
"""NGHĨA VỤ NỐI VỚI VẬT QUA XUẤT XỨ DỮ KIỆN. **0 lượt gọi model.**

    `OBLIGATION_CONTAINER_NAME_BINDING`, 2026-09-06.

Đề đặt cho vật DẪN XUẤT một cái nhãn — *"cắt hình nón theo đường tròn (t)"* —
rồi hỏi số đo của nhãn ấy. `analyze` chép nhãn vào `obligation.container`, còn
lượt sinh chương trình đặt cho vật một cái tên mô tả (`duong_tron_t`). Hai lượt
LLM, hai cách gọi cùng một vật, **cả hai đều đúng luật được giao**.

Trước bản này, việc nối hai cách gọi ấy rơi hết vào **ba lưới CHÍNH TẢ**, và ba
lưới ấy nối được hay không là chuyện may rủi của cách đặt tên:

    e5  container `(j)`  · chương trình khai đúng `(j)`   → trúng thẳng
    e1  container `(u)`  · chương trình khai `u`          → lưới ③ (`ten_loi`)
    e4  container `(t)`  · chương trình khai `duong_tron_t` → **KHÔNG lưới nào**

`ten_loi('duong_tron_t')` trả `tront` (nó gỡ phụ tố `duong_` rồi dán `tron` vào
`t`), nên e4 bị bác *"container '(t)' chưa khai báo"* trong khi chương trình đã
tính đúng `15`.

Fixture là chương trình **mô hình thật sự sinh** trong lượt A/B
`ab-v1-20260905T164514Z` (arm B), không sửa một byte — trích riêng sang
`docs/evaluation/geometry/obligation-container-binding/` để artifact lượt A/B
gốc giữ nguyên. Sản phẩm vẫn ở baseline **A**; B chỉ là fixture phát triển.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from app.simulation.geometry.radical import display, is_exact_number
from app.simulation.semantic_program import coverage_gate as CG
from app.simulation.semantic_program.contract import SemanticProgramSpec
from app.simulation.semantic_program.coverage_gate import (
    RANG_BUOC_MO_HO,
    THIEU_KHAI_BAO,
    check_structural_coverage,
)
from app.simulation.semantic_program.request_contract import RequestContract
from app.simulation.semantic_program.route import verify_and_compile

GOC = Path(__file__).resolve().parents[3]
CA = GOC / "docs/evaluation/geometry/obligation-container-binding/cases"


def _nap(cid: str):
    """Nạp ca từ **`raw_candidate`** — bản NGUYÊN VĂN mô hình sinh.

    ⚠️ Không dùng `chuong_trinh` (bản đã parse trong artifact A/B): lượt ấy chạy
    trên lược đồ CŨ, nơi `AssignStmt` chưa có ô `source_fact_id`, nên bản đã
    parse **đã mất** chính lời khai mà wave này đi tìm. Đọc bản thô là điều
    kiện để nói *"e4 nguyên văn"* mà không nói sai.
    """
    d = json.loads((CA / f"{cid}.json").read_text(encoding="utf-8"))
    return (RequestContract.model_validate(d["request_contract"]),
            SemanticProgramSpec.model_validate(d["chuong_trinh_tho"]), d)


def _tho(d) -> dict:
    """Bản THÔ của chương trình — bản sao, sửa thoải mái.

    ⚠️ Phải sửa `source_fact_id` ở đây chứ KHÔNG trên spec đã parse: phép nâng
    `_nang_xuat_xu_cau_lenh` chạy một lần lúc parse rồi chở lời khai sang khai
    báo, nên sửa lại câu lệnh sau đó không còn tác dụng.
    """
    return json.loads(json.dumps(d["chuong_trinh_tho"]))


def _dai_luong(oc) -> dict[str, str]:
    return {k: display(v) for k, v in (oc.final_memory or {}).items()
            if is_exact_number(v)}


@pytest.fixture
def e4():
    """Ca hỏng: container `(t)`, chương trình khai `duong_tron_t`."""
    return _nap("e4")


@pytest.fixture
def e1():
    """Ca qua nhờ CHÍNH TẢ: `ten_loi('(u)') == ten_loi('u')`."""
    return _nap("e1")


@pytest.fixture
def e5():
    """Ca qua vì mô hình chép thẳng nhãn `(j)` làm tên biến."""
    return _nap("e5")


def _sua_ratio(spec: SemanticProgramSpec) -> SemanticProgramSpec:
    """Sửa ĐÚNG MỘT token: `ratio` của `T` từ `5/2` về `5/7`.

    ─── VÌ SAO CẦN, VÀ VÌ SAO NÓ KHÔNG PHẢI VIỆC CỦA WAVE NÀY ─────────────

    Mở được cổng phủ thì e4 lộ ra khiếm khuyết THỨ HAI, độc lập hẳn với việc
    nối tên: `divide_segment(a, b, ratio)` là `a + ratio·(b−a)`, tức `ratio`
    là THAM SỐ `t`. Đề cho `PT = 20`, `PQ = 28` ⇒ `t = 20/28 = 5/7`. Mô hình
    viết `5/2` — quy ước *"chia đoạn theo tỉ số 5:2"*. Với `5/2` thì
    `T = (0,0,−42)`, nằm NGOÀI khối, và kernel bác đúng:
    `CURVED_PLANE_DOES_NOT_CUT`.

    Đây là lỗi MÔ HÌNH, không phải lỗi hệ — và nó cùng lớp với khiếm khuyết
    đã ghi cho `c9b` ở `CURVED_SECTION_RADIUS_PATH_ADJUDICATION` (*"`ratio
    9/6` là `t`, đúng phải `3/5`"*). Ở đó cổng phủ cũng **che** lỗi thứ hai;
    wave này gỡ tấm che, nên lỗi hiện ra là TIẾN BỘ chứ không phải hồi quy.

    `RequestContract` giữ NGUYÊN VĂN — chỉ chương trình được sửa một token.
    """
    raw = json.loads(spec.model_dump_json())
    for st in raw["statements"]:
        if st.get("target_var") == "T":
            st["expr"]["ratio"] = "5/7"
    return SemanticProgramSpec.model_validate(raw)


def _doi_ten(spec: SemanticProgramSpec, cu: str, moi: str) -> SemanticProgramSpec:
    """Đổi tên một vật NHẤT QUÁN khắp chương trình, giữ nguyên nghĩa toán học."""
    raw = json.loads(spec.model_dump_json())

    def di(x):
        if isinstance(x, dict):
            return {k: (moi if (isinstance(v, str) and v == cu) else di(v))
                    for k, v in x.items()}
        if isinstance(x, list):
            return [di(v) for v in x]
        return x

    return SemanticProgramSpec.model_validate(di(raw))


# ══ A · TÁI HIỆN — lượt bác cũ, và nó bác vì ĐÂU ═══════════════════════════
def test_A1_ba_luoi_chinh_ta_deu_truot_tren_e4(e4):
    """Chứng minh nguyên nhân, không chỉ chứng minh triệu chứng.

    Nếu bản vá được viết vì một lý do khác (vd "dấu ngoặc"), test này vẫn phải
    đúng: ba lưới chính tả trượt là **sự thật độc lập** với bản vá.
    """
    from app.simulation.semantic_program.domain_profile import (
        geometry_symbol_key, khop_ten_doi_tuong, ten_loi,
    )
    _, spec, _ = e4
    ten = {m.name for m in spec.memory_declarations}
    assert "(t)" not in ten                       # container VẮNG MẶT
    assert ten_loi("(t)") == "t"
    assert ten_loi("duong_tron_t") == "tront"     # ← phụ tố `duong_` dán `tron`
    assert geometry_symbol_key("(t)") is None     # ngoặc trượt mẫu ký hiệu
    assert khop_ten_doi_tuong("(t)", ten) is None


def test_A2_gia_thuyet_container_khong_phai_dinh_danh_BI_BAC(e5):
    """`(j)` cũng không phải định danh, mà e5 **served**.

    Nên "container có dấu ngoặc" KHÔNG phải nguyên nhân. Giữ test này để bản
    sửa sau không quay lại chữa dấu ngoặc.
    """
    rc, spec, _ = e5
    assert rc.obligations[0].container == "(j)"
    assert verify_and_compile(rc, spec).stage_reached == "served"


def test_A3_bo_net_xuat_xu_thi_e4_BAC_LAI_nhu_artifact(e4, monkeypatch):
    """PHÉP TIÊM: khôi phục resolver cũ ⇒ bản vá phải đỏ trở lại.

    Guard chưa từng đỏ là guard chưa được chứng minh.
    """
    rc, spec, d = e4
    monkeypatch.setattr(CG, "_xuat_xu_neu_ten", lambda *a, **k: False)
    r = check_structural_coverage(rc, spec)
    assert not r.ok
    assert [c.ly_do for c in r.chan_doan] == [THIEU_KHAI_BAO]
    # …và đúng lượt bác đã ghi trong artifact A/B.
    assert d["ket_qua_luot_ab"]["error_code"] == "requested_operation_uncovered"


# ══ B · E4 NGUYÊN VĂN ĐƯỢC PHỤC VỤ, ĐÁP SỐ ĐÚNG ════════════════════════════
def test_B1_e4_nguyen_van_qua_duoc_BINDING_roi_lo_loi_MO_HINH(e4):
    """e4 NGUYÊN VĂN: cổng phủ thôi bác, và lỗi thứ hai hiện ra đúng chỗ.

    Đây là kết quả thật, không phải "served". Wave này gỡ tấm che; thứ nằm
    dưới tấm che là một lỗi MÔ HÌNH độc lập, và nó fail-closed đúng tầng.
    """
    rc, spec, _ = e4
    assert check_structural_coverage(rc, spec).ok        # ← binding đã thông
    oc = verify_and_compile(rc, spec)
    assert oc.stage_reached == "execution"               # ← không còn coverage
    assert any("CURVED_PLANE_DOES_NOT_CUT" in d for d in (oc.details or []))


def test_B2_e4_ban_kinh_dung_bang_15_sau_MOT_token(e4):
    """21 · (20/28) = 15 — kernel tính lại từ HÌNH, không tin số khai.

    Hợp đồng NGUYÊN VĂN; chương trình sửa đúng một token `ratio` (xem
    `_sua_ratio`). Không có bản vá binding thì delta này KHÔNG cứu được ca —
    `test_B2b` chứng minh điều đó.
    """
    rc, spec, _ = e4
    oc = verify_and_compile(rc, _sua_ratio(spec))
    assert oc.stage_reached == "served", oc.details
    assert _dai_luong(oc)["ban_kinh_t"] == "15"


def test_B2b_chi_sua_ratio_thoi_thi_VAN_bac_neu_khong_co_net_moi(e4, monkeypatch):
    """PHÉP TIÊM: tắt net ⓪b ⇒ delta `ratio` một mình không đủ.

    Tách bạch hai nguyên nhân: cái nào chữa cái gì.
    """
    rc, spec, _ = e4
    monkeypatch.setattr(CG, "_xuat_xu_neu_ten", lambda *a, **k: False)
    oc = verify_and_compile(rc, _sua_ratio(spec))
    assert oc.stage_reached == "structural_coverage"


def test_B3_e4_noi_dung_vat_va_ghi_ro_bang_chung(e4):
    rc, spec, _ = e4
    r = check_structural_coverage(rc, spec)
    assert r.ok
    assert r.ten_da_hoa_giai == {"(t)": "duong_tron_t"}
    assert any("xuất xứ dữ kiện" in s for s in r.symbol_reconciled)


# ══ C · KHÔNG ĐỔI PHÁN QUYẾT CỦA CHƯƠNG TRÌNH ĐANG QUA ═════════════════════
def test_C1_e1_giu_nguyen_luoi_cu(e1):
    """e1 vẫn nối bằng lưới ③. Net mới là LƯỚI CUỐI, không giành chỗ."""
    rc, spec, _ = e1
    r = check_structural_coverage(rc, spec)
    assert r.ok and r.ten_da_hoa_giai == {"(u)": "u"}
    assert any("phụ tố kiểu" in s for s in r.symbol_reconciled)
    assert _dai_luong(verify_and_compile(rc, spec))["ban_kinh_u"] == "5"


def test_C2_e5_khong_can_luoi_nao(e5):
    rc, spec, _ = e5
    r = check_structural_coverage(rc, spec)
    assert r.ok and r.ten_da_hoa_giai == {}
    assert _dai_luong(verify_and_compile(rc, spec))["ban_kinh_j"] == "40"


# ══ D · PHÂN BIỆT ĐƯỢC HAI VẬT CÙNG KIỂU ══════════════════════════════════
def test_D1_hai_duong_tron_cung_ton_tai_van_noi_dung_cai(e4):
    """Thêm một đường tròn thứ hai (cắt ở cao độ khác) — `(t)` vẫn trỏ đúng.

    Nếu phép nối chỉ dựa vào *"có đúng một vật đúng kiểu"* thì test này đỏ.
    """
    rc, spec, _ = e4
    raw = json.loads(spec.model_dump_json())
    raw["memory_declarations"] += [
        {"name": "T2", "type": "point3"},
        {"name": "mp2", "type": "plane3"},
        {"name": "duong_tron_s", "type": "circle3"},
        {"name": "ban_kinh_s", "type": "float"},
    ]
    raw["statements"] += [
        {"kind": "construct_point", "target_var": "T2",
         "expr": {"kind": "divide_segment", "a": "P", "b": "Q", "ratio": "2"}},
        {"kind": "assign", "target_var": "mp2",
         "expr": {"kind": "plane_perpendicular_to_line",
                  "point": "T2", "line": "line_pq"}},
        {"kind": "assign", "target_var": "duong_tron_s",
         "expr": {"kind": "intersect_plane_curved",
                  "solid": "non", "plane": "mp2"}},
        {"kind": "assign", "target_var": "ban_kinh_s",
         "expr": {"kind": "measure", "quantity": "radius", "of": "duong_tron_s"}},
    ]
    spec2 = SemanticProgramSpec.model_validate(raw)
    r = check_structural_coverage(rc, spec2)
    assert r.ok
    assert r.ten_da_hoa_giai == {"(t)": "duong_tron_t"}


def test_D2_witness_do_NHAM_duong_tron_thi_bi_bac(e4):
    """Witness của nghĩa vụ `(t)` trỏ sang đường tròn KHÁC ⇒ không đủ bằng chứng."""
    rc, spec, _ = e4
    raw = json.loads(spec.model_dump_json())
    raw["memory_declarations"] += [
        {"name": "T2", "type": "point3"},
        {"name": "mp2", "type": "plane3"},
        {"name": "duong_tron_s", "type": "circle3"},
    ]
    raw["statements"] = raw["statements"][:-1] + [
        {"kind": "construct_point", "target_var": "T2",
         "expr": {"kind": "divide_segment", "a": "P", "b": "Q", "ratio": "2"}},
        {"kind": "assign", "target_var": "mp2",
         "expr": {"kind": "plane_perpendicular_to_line",
                  "point": "T2", "line": "line_pq"}},
        {"kind": "assign", "target_var": "duong_tron_s",
         "expr": {"kind": "intersect_plane_curved",
                  "solid": "non", "plane": "mp2"}},
        # witness của `(t)` đo đường tròn `s` — SAI VẬT
        {"kind": "assign", "target_var": "ban_kinh_t",
         "expr": {"kind": "measure", "quantity": "radius", "of": "duong_tron_s"}},
    ]
    r = check_structural_coverage(rc, SemanticProgramSpec.model_validate(raw))
    assert not r.ok
    assert r.ten_da_hoa_giai == {}


def test_D3_vat_dung_kieu_nhung_KHONG_lien_he_nghia_vu_thi_khong_noi(e4):
    """Đường tròn có thật, đúng kiểu, được đo — nhưng câu lệnh dựng nó viện một
    dữ kiện KHÔNG nêu `(t)`. Không bằng chứng ⇒ không nối."""
    rc, _, d = e4
    raw = _tho(d)
    for st in raw["statements"]:
        if st.get("target_var") == "duong_tron_t":
            st["source_fact_id"] = "mat_phang_vuong_goc_pq"   # dữ kiện KHÁC
    r = check_structural_coverage(rc, SemanticProgramSpec.model_validate(raw))
    assert not r.ok
    assert [c.ly_do for c in r.chan_doan] == [THIEU_KHAI_BAO]


def test_D4_khong_co_source_fact_id_thi_khong_noi(e4):
    """Gỡ xuất xứ ⇒ mất bằng chứng ⇒ bác. Bằng chứng phải CÓ, không suy đoán."""
    rc, _, d = e4
    raw = _tho(d)
    for st in raw["statements"]:
        if st.get("target_var") == "duong_tron_t":
            st.pop("source_fact_id", None)
    r = check_structural_coverage(rc, SemanticProgramSpec.model_validate(raw))
    assert not r.ok


def test_D5_hai_vat_cung_vien_mot_du_kien_thi_MO_HO(e4):
    """Hai đường tròn cùng viện dữ kiện nêu `(t)`, cùng được witness đo ⇒ hệ
    KHÔNG chọn hộ."""
    rc, spec, _ = e4
    raw = json.loads(spec.model_dump_json())
    raw["memory_declarations"] += [{"name": "duong_tron_s", "type": "circle3"}]
    fid = "mat_phang_cat_non_theo_duong_tron_t"
    raw["statements"] = raw["statements"][:-1] + [
        {"kind": "assign", "target_var": "duong_tron_s", "source_fact_id": fid,
         "expr": {"kind": "intersect_plane_curved",
                  "solid": "non", "plane": "mat_phang_cat"}},
        {"kind": "assign", "target_var": "ban_kinh_t",
         "expr": {"kind": "measure", "quantity": "radius", "of": "duong_tron_t"}},
        {"kind": "assign", "target_var": "ban_kinh_t2",
         "expr": {"kind": "measure", "quantity": "radius", "of": "duong_tron_s"}},
    ]
    raw["memory_declarations"] += [{"name": "ban_kinh_t2", "type": "float"}]
    rc2 = rc.model_copy(update={"obligations": (
        rc.obligations[0].model_copy(
            update={"params": {"witness": "ban_kinh_t"}}),)})
    raw2 = json.loads(json.dumps(raw))
    for st in raw2["statements"]:
        if st.get("target_var") == "ban_kinh_t2":
            st["target_var"] = "ban_kinh_t"          # cùng witness, hai chủ thể
    r = check_structural_coverage(rc2, SemanticProgramSpec.model_validate(raw2))
    assert not r.ok
    assert RANG_BUOC_MO_HO in [c.ly_do for c in r.chan_doan]


# ══ E · KHÔNG NỚI PHẢN VÍ DỤ ĐÃ ĐĂNG KÝ ═══════════════════════════════════
def test_E1_ten_vang_mat_va_KHONG_du_kien_nao_neu_thi_van_bac(e4):
    """Phản ví dụ gốc của net ⓪: hợp đồng gọi tên một vật chương trình chưa
    dựng. Không dữ kiện nào nêu tên ấy ⇒ nối là chọn hộ ⇒ vẫn bác."""
    rc, spec, _ = e4
    rc2 = rc.model_copy(update={"obligations": (
        rc.obligations[0].model_copy(update={"container": "hinh_lang_tru"}),)})
    r = check_structural_coverage(rc2, spec)
    assert not r.ok
    assert [c.ly_do for c in r.chan_doan] == [THIEU_KHAI_BAO]


def test_E2_container_da_tro_vat_hop_le_thi_GIU_danh_tinh(e4):
    """`(t)` đổi thành `non` — tên CÓ chủ và chủ hợp kiểu cho `volume`.

    Net mới chỉ chạy khi container VẮNG MẶT, nên nó không được cướp một danh
    tính đã đúng.
    """
    rc, spec, _ = e4
    rc2 = rc.model_copy(update={"obligations": (
        rc.obligations[0].model_copy(
            update={"kind": "volume", "container": "non",
                    "params": {"witness": "the_tich"}}),)})
    raw = json.loads(spec.model_dump_json())
    raw["memory_declarations"] += [{"name": "the_tich", "type": "float"}]
    raw["statements"] += [
        {"kind": "assign", "target_var": "the_tich",
         "expr": {"kind": "measure", "quantity": "volume", "of": "non"}}]
    r = check_structural_coverage(rc2, SemanticProgramSpec.model_validate(raw))
    assert r.ok
    assert "non" not in r.ten_da_hoa_giai        # không hoà giải: vốn đã đúng


def test_E3_luong_do_lech_thi_khong_noi(e4):
    """Witness đo `area`, nghĩa vụ hỏi `radius` ⇒ không nối."""
    rc, spec, _ = e4
    raw = json.loads(spec.model_dump_json())
    for st in raw["statements"]:
        if st.get("target_var") == "ban_kinh_t":
            st["expr"]["quantity"] = "area"
    r = check_structural_coverage(rc, SemanticProgramSpec.model_validate(raw))
    assert not r.ok


def test_E4_chu_the_sai_kieu_thi_khong_noi(e4):
    """Witness đo `radius` trên một ĐIỂM ⇒ kiểu không hợp ⇒ không nối."""
    rc, spec, _ = e4
    raw = json.loads(spec.model_dump_json())
    for st in raw["statements"]:
        if st.get("target_var") == "ban_kinh_t":
            st["expr"]["of"] = "T"
    r = check_structural_coverage(rc, SemanticProgramSpec.model_validate(raw))
    assert not r.ok


# ══ F · NHIỀU NGHĨA VỤ — BINDING ĐỘC LẬP ══════════════════════════════════
def test_F1_volume_va_radius_giu_binding_rieng(e4):
    """`volume(non)` và `radius((t))` cùng lúc: mỗi nghĩa vụ giữ chủ thể của nó.

    Bí danh rò sang nghĩa vụ anh em là lỗi `c7a` đã trả giá một lần.
    """
    rc, spec, _ = e4
    raw = json.loads(spec.model_dump_json())
    raw["memory_declarations"] += [{"name": "the_tich", "type": "float"}]
    raw["statements"] += [
        {"kind": "assign", "target_var": "the_tich",
         "expr": {"kind": "measure", "quantity": "volume", "of": "non"}}]
    ob_r = rc.obligations[0]
    rc2 = rc.model_copy(update={"obligations": (
        ob_r,
        ob_r.model_copy(update={"kind": "volume", "container": "non",
                                "params": {"witness": "the_tich"}}))})
    spec2 = _sua_ratio(SemanticProgramSpec.model_validate(raw))
    r = check_structural_coverage(rc2, spec2)
    assert r.ok
    assert r.ten_da_hoa_giai == {"(t)": "duong_tron_t"}
    oc = verify_and_compile(rc2, spec2)
    assert oc.stage_reached == "served", oc.details
    dl = _dai_luong(oc)
    assert dl["ban_kinh_t"] == "15"
    assert dl["the_tich"] == "4116π"          # (1/3)·π·21²·28


# ══ G · CỔNG PHỦ VÀ HẬU ĐIỀU KIỆN NÓI CÙNG MỘT ĐIỀU ═══════════════════════
def test_G1_hau_dieu_kien_cham_dung_vat_ma_cong_phu_da_noi(e4):
    """C₂ dùng lại `ten_da_hoa_giai` của C₁a — một thẩm quyền, hai consumer."""
    rc, spec, _ = e4
    oc = verify_and_compile(rc, _sua_ratio(spec))
    assert oc.stage_reached == "served", oc.details
    kiem = list(oc.constraints_checked or [])
    assert "radius((t))" in kiem
    assert "radius((t))" in list(oc.constraints_verified or [])


def test_G2_khong_co_binding_thi_C2_khong_tu_bia_ra(e4):
    """Bác ở C₁a thì không tới C₂ — không có đường vòng nào chấm hộ."""
    rc, _, d = e4
    raw = _tho(d)
    for st in raw["statements"]:
        if st.get("target_var") == "duong_tron_t":
            st.pop("source_fact_id", None)
    oc = verify_and_compile(rc, SemanticProgramSpec.model_validate(raw))
    assert oc.stage_reached == "structural_coverage"


# ══ H · Ý NGHĨA GIỮ NGUYÊN THÌ KẾT QUẢ GIỮ NGUYÊN ═════════════════════════
def test_H1_doi_ten_nhat_quan_khong_doi_ket_qua(e4):
    """`duong_tron_t` → `c_1`: cách xa nhãn `(t)` hơn nữa, nhưng xuất xứ vẫn nối."""
    rc, spec, _ = e4
    spec2 = _doi_ten(_sua_ratio(spec), "duong_tron_t", "c_1")
    oc = verify_and_compile(rc, spec2)
    assert oc.stage_reached == "served", oc.details
    assert _dai_luong(oc)["ban_kinh_t"] == "15"


def test_H2_doi_thu_tu_khai_bao_khong_doi_ket_qua(e4):
    rc, spec, _ = e4
    raw = json.loads(_sua_ratio(spec).model_dump_json())
    raw["memory_declarations"] = list(reversed(raw["memory_declarations"]))
    oc = verify_and_compile(rc, SemanticProgramSpec.model_validate(raw))
    assert oc.stage_reached == "served", oc.details
    assert _dai_luong(oc)["ban_kinh_t"] == "15"


# ══ I · BỀ MẶT MÔ HÌNH KHÔNG ĐỔI — điều kiện để giữ PRODUCT_VARIANT = A ════
def test_I1_AssignStmt_KHONG_moc_them_o_nao_cho_mo_hinh():
    """Phép nâng chạy ở BIÊN PARSE, không phải bằng cách mời mô hình viết thêm.

    Nếu ai đó "đơn giản hoá" bằng cách thêm `source_fact_id` vào `AssignStmt`
    thì `responseSchema` và thẻ văn phạm đổi theo, thẻ sản phẩm thôi khớp
    `card_A.txt` đã đóng băng, và wave 0-quota này bỗng nhận một thay đổi
    affordance chưa ai đo. Test này đỏ trước khi điều đó lọt.
    """
    from app.simulation.semantic_program.contract import AssignStmt
    assert set(AssignStmt.model_fields) == {"kind", "target_var", "expr"}


def test_I2_the_van_pham_san_pham_van_KHOP_BYTE_voi_card_A():
    from app.simulation.semantic_program.grammar_card import grammar_card
    card_a = (GOC / "docs/evaluation/geometry/operation-affordance-ab-v1"
              / "card_A.txt").read_text(encoding="utf-8")
    assert grammar_card("hinh_hoc") == card_a


def test_I3_nang_xuat_xu_CHI_dien_cho_trong(e4):
    """Khai báo đã có xuất xứ thì lời khai ở câu lệnh KHÔNG được ghi đè.

    Hai lời khai khác nhau về cùng một vật là chuyện fail-closed, không phải
    chuyện chọn hộ — cùng luật `_nang_declare_point` áp cho toạ độ.
    """
    _, _, d = e4
    raw = _tho(d)
    for m in raw["memory_declarations"]:
        if m["name"] == "duong_tron_t":
            m["source_fact_id"] = "ban_kinh_day"        # đã có chủ
    spec = SemanticProgramSpec.model_validate(raw)
    giu = {m.name: m.source_fact_id for m in spec.memory_declarations}
    assert giu["duong_tron_t"] == "ban_kinh_day"        # KHÔNG bị đè


def test_I4_nang_xuat_xu_khong_de_ra_khai_bao_moi(e4):
    """`assign` vào một tên chưa khai thì phép nâng im lặng — không tự đẻ khai báo."""
    _, _, d = e4
    raw = _tho(d)
    raw["statements"].append(
        {"kind": "assign", "target_var": "chua_khai", "source_fact_id": "ban_kinh_day",
         "expr": {"kind": "measure", "quantity": "radius", "of": "duong_tron_t"}})
    truoc = {m["name"] for m in raw["memory_declarations"]}
    spec = SemanticProgramSpec.model_validate(raw)
    assert {m.name for m in spec.memory_declarations} == truoc
