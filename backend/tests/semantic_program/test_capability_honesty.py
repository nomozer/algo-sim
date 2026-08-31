# -*- coding: utf-8 -*-
"""CHỐNG RỬA NĂNG LỰC — thực thể tự bịa không được thành sự thật. **0 API call.**

─── LỖ NÓ BỊT ─────────────────────────────────────────────────────────────

GENERALIZATION MATRIX, `gm_10` hỏi **bán kính mặt cầu ngoại tiếp** — runtime
không có mặt cầu. Mô hình:

    declare_point P_opposite = [2,2,2]   model_assumption: "đỉnh đối diện…"
    P = midpoint(A, P_opposite)          ← tâm mặt cầu
    R = distance(P, A)                   ← √3, ĐÚNG

Đáp số đúng, và đó chính là chỗ nguy hiểm: học sinh thấy một "mô phỏng" của
bài mặt cầu mà trong đó không có mặt cầu nào. Mô hình tự giải rồi **giấu định
lý vào toạ độ** của một điểm nó bịa ra; `model_assumption` hợp thức hoá.

─── RANH GIỚI, VÀ ĐÂY LÀ PHẦN KHÓ ────────────────────────────────────────

Không được cấm mô hình CHỌN TOẠ ĐỘ. Đặt `A=(0,0,0)`, `B=(1,0,0)` cho một tam
giác đề cho là mô hình hoá hợp lệ, và cấm nó là giết mọi bài hình học.

Luật đúng: `model_assumption` chỉ nói về **cách đặt** một vật ĐỀ ĐÃ NÊU. Một
vật SUY RA thì phải được DỰNG bằng một phép của IR — lúc ấy kernel tính toạ
độ, và điều được khẳng định trở thành điều kiểm chứng được.

─── GIỚI HẠN CÒN LẠI, KHAI THẲNG ─────────────────────────────────────────

Cổng này chặn thực thể **tự bịa** (không có trong đề). Nó KHÔNG chặn được ca
đề có nhắc tên — *"Gọi H là hình chiếu của A"* — rồi mô hình khai `H` bằng toạ
độ tính tay: `H` có trong đề nên qua được. Ca ấy còn hàng rào khác (bộ chấm
tính lại đại lượng từ hình), nhưng hàng rào ấy yếu hơn, và nói thẳng ra ở đây
đúng hơn là để một con số 100% che nó đi.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from app.simulation.semantic_program.analyze_contract import build_request_contract
from app.simulation.semantic_program.grounding_gate import (
    ERR_RUA_NANG_LUC,
    ERR_THIEU_NGUOI_DUNG,
    check_grounding,
)
from app.simulation.semantic_program.source_entities import (
    la_ten_nguon,
    nhan_hinh_hoc,
)
from app.simulation.semantic_program.validator import validate_semantic_program

DE_CHOP = ("Cho hình chóp S.ABCD có đáy ABCD là hình vuông cạnh 2, SA vuông "
           "góc với mặt phẳng đáy và SA = 2. Tính khoảng cách từ điểm B đến "
           "mặt phẳng (SAC).")


def _hd(de: str = DE_CHOP):
    return build_request_contract({"obligations": [], "input_facts": []},
                                  problem_text=de)


def _diem(ten: str, xyz: list, ly_do: str = "chọn theo hệ trục") -> dict:
    return {"kind": "declare_point", "target_var": ten, "at": xyz,
            "model_assumption": ly_do}


def _ct(stmts: list[dict], decls: list[dict] | None = None) -> dict:
    return {
        "spec_version": "1.0", "simulation_id": "geometry.honesty",
        "title": "Kiểm chống rửa năng lực",
        "description": "Thực thể tự bịa không được thành sự thật.",
        "pedagogical_intent": "Cho thấy điều khẳng định phải kiểm chứng được.",
        "memory_declarations": decls or [], "statements": stmts,
    }


def _cham(ct: dict, de: str = DE_CHOP):
    v = validate_semantic_program(ct)
    assert v.ok, v.error
    return check_grounding(_hd(de), v.spec)


# ══ ① BỘ TRÍCH TÊN NGUỒN ════════════════════════════════════════════════
def test_trich_dung_dinh_tu_de():
    assert nhan_hinh_hoc(DE_CHOP) == frozenset("SABCD")


def test_trich_ca_dau_PHAY_TREN():
    de = "Cho hình lập phương ABCD.A'B'C'D' có cạnh bằng 2."
    assert nhan_hinh_hoc(de) == frozenset(
        {"A", "B", "C", "D", "A'", "B'", "C'", "D'"})


def test_TU_TIENG_VIET_khong_thanh_dinh():
    """`Tính`, `Cho`, `Gọi` bắt đầu bằng chữ hoa — không được thành nhãn.

    Sót một chữ ở đây là mở đúng một lối lách: một điểm tên `T` sẽ neo được vào
    chính chữ "Tính" trong đề.
    """
    de = "Tính khoảng cách. Cho hình chóp. Gọi M là trung điểm."
    assert nhan_hinh_hoc(de) == {"M"}


@pytest.mark.parametrize("ten, mong", [
    ("A", True), ("S", True), ("point_A", True), ("vertex_B", True),
    ("P_opposite", False), ("X", False), ("H", False), ("O", False),
    ("T1", False), ("helper_7", False), ("tam_mat_cau", False),
])
def test_neo_nguon_theo_DE_khong_theo_hinh_dang_ten(ten, mong):
    """§11 — guard phải theo NGUỒN, không theo tên. Đổi `P_opposite` thành
    `X`/`H`/`O` không được lách qua."""
    assert la_ten_nguon(ten, DE_CHOP) is mong


def test_de_RONG_thi_khong_ket_luan():
    """Hợp đồng dựng tay không có đề để đối chiếu — cùng quy ước
    `provenance="unchecked"`. Kết luận FAIL ở đó là phạt một đường gọi hợp lệ."""
    assert la_ten_nguon("P_opposite", "") is True


# ══ ② CHỨNG CỨ DƯƠNG — không được giết bài hợp lệ (§13) ═════════════════
def test_diem_NGUON_khai_toa_do_van_QUA():
    """Chọn hệ trục cho các đỉnh ĐỀ CHO là mô hình hoá hợp lệ."""
    g = _cham(_ct([_diem("A", [0, 0, 0]), _diem("B", [2, 0, 0]),
                   _diem("C", [2, 2, 0]), _diem("D", [0, 2, 0]),
                   _diem("S", [0, 0, 2])]))
    assert g.ok, g.unresolved


def test_lang_tru_va_lap_phuong_cung_QUA():
    de = ("Cho lăng trụ đứng ABC.A'B'C' có đáy ABC vuông tại B với AB = 2 và "
          "AA' = 2. Tính khoảng cách từ A' đến mặt phẳng (ABC).")
    g = _cham(_ct([_diem("A", [0, 0, 0]), _diem("B", [2, 0, 0]),
                   _diem("C", [2, 2, 0]), _diem("A_prime", [0, 0, 2])]), de)
    assert g.ok, g.unresolved


def test_diem_DUNG_RA_bang_phep_dung_van_QUA():
    """Điểm phụ hợp lệ: DỰNG bằng `midpoint`, kernel tính toạ độ."""
    g = _cham(_ct(
        [_diem("A", [0, 0, 0]), _diem("B", [2, 0, 0]), _diem("C", [2, 2, 0]),
         {"kind": "construct_point", "target_var": "M",
          "expr": {"kind": "midpoint", "a": "A", "b": "B"}}],
        [{"name": "M", "type": "point3"}]))
    assert g.ok, g.unresolved


def test_hinh_chieu_va_giao_diem_bang_phep_dung_van_QUA():
    g = _cham(_ct(
        [_diem("A", [0, 0, 0]), _diem("B", [2, 0, 0]), _diem("C", [2, 2, 0]),
         _diem("S", [0, 0, 2]),
         {"kind": "construct_plane", "target_var": "P",
          "through": ["A", "B", "C"]},
         {"kind": "construct_point", "target_var": "H",
          "expr": {"kind": "project_onto", "point": "S", "target": "P"}}],
        [{"name": "P", "type": "plane3"}, {"name": "H", "type": "point3"}]))
    assert g.ok, g.unresolved


# ══ ③ RỬA NĂNG LỰC — mọi hình dạng đều bị chặn (§12) ════════════════════
def _rua(ten: str, xyz: list, ly_do: str):
    """Khuôn tấn công: khai một thực thể SUY RA bằng toạ độ thô."""
    return _cham(_ct([_diem("A", [0, 0, 0]), _diem("B", [2, 0, 0]),
                      _diem(ten, xyz, ly_do)]))


@pytest.mark.parametrize("ten", ["P_opposite", "X", "H", "O", "T1", "helper_7",
                                 "tam_mat_cau", "center"])
def test_DOI_TEN_van_bi_chan(ten):
    """§11 — không hard-code `P_opposite`. Cùng khuôn, tên nào cũng chặn."""
    g = _rua(ten, [2, 2, 2], "điểm phụ tôi cần")
    assert not g.ok, f"tên '{ten}' lách qua được"
    assert g.error_code == ERR_RUA_NANG_LUC


@pytest.mark.parametrize("ly_do, xyz", [
    ("tâm mặt cầu ngoại tiếp hình chóp", [1, 1, 1]),      # A · mặt cầu
    ("trung điểm của AB", [1, 0, 0]),                      # B · trung điểm
    ("chân đường vuông góc hạ từ S", [0, 0, 0]),           # C · hình chiếu
    ("giao điểm của AC và BD", [1, 1, 0]),                 # D · giao điểm
    ("đỉnh của hình nón nội tiếp", [1, 1, 3]),             # E · mặt cong
])
def test_MOI_KIEU_giau_dap_an_deu_bi_chan(ly_do, xyz):
    """Năm khuôn của §12. Điều chung: một KẾT LUẬN được khai thành toạ độ.

    `model_assumption` chỉ được nói về CÁCH ĐẶT một vật đề đã nêu — không được
    nói *"tôi suy ra còn có vật này nữa"*.
    """
    g = _rua("K", xyz, ly_do)
    assert not g.ok and g.error_code == ERR_RUA_NANG_LUC


def test_thong_diep_CHI_DUONG_dung_de_di():
    g = _rua("P_opposite", [2, 2, 2], "đỉnh đối diện")
    loi = " ".join(g.unresolved)
    assert "không có trong đề" in loi
    assert "DỰNG" in loi, "từ chối mà không nói phải làm gì"


def test_gan_them_source_fact_id_bia_KHONG_lach_duoc():
    """CỬA SAU: khai báo có `source_fact_id` không giải được sẽ được HẠ CẤP
    sang kênh giả thiết. Nếu chốt neo nguồn chỉ đứng ở nhánh "không có fid"
    thì thêm đúng một trường bịa là qua — cửa sau rộng bằng chính cổng."""
    d = _diem("P_opposite", [2, 2, 2], "đỉnh đối diện")
    d["source_fact_id"] = "khong_he_ton_tai"
    g = _cham(_ct([_diem("A", [0, 0, 0]), _diem("B", [2, 0, 0]), d]))
    assert not g.ok, "gắn fid bịa lách được qua cổng"
    assert g.error_code == ERR_RUA_NANG_LUC


def test_diem_NGUON_kem_fid_bia_van_QUA():
    """Đối chứng của ca trên — hạ cấp vẫn phải hoạt động cho điểm CÓ nguồn.
    Không có ca này thì bản vá trên có thể chỉ đơn giản là đóng cả nhánh."""
    d = _diem("B", [2, 0, 0], "chọn theo hệ trục")
    d["source_fact_id"] = "canh_day_khong_co_trong_hop_dong"
    g = _cham(_ct([_diem("A", [0, 0, 0]), d]))
    assert g.ok, g.unresolved


# ══ ④ REPLAY gm_10 — chương trình THẬT (§10) ════════════════════════════
_MATRIX = (Path(__file__).resolve().parents[3] / "docs" / "evaluation"
           / "geometry" / "generalization-matrix" / "matrix.json")
DE_GM10 = ("Cho hình chóp S.ABCD có đáy ABCD là hình vuông cạnh 2, SA vuông "
           "góc với mặt phẳng đáy và SA = 2. Tính bán kính mặt cầu ngoại tiếp "
           "hình chóp S.ABCD.")


def test_gm10_replay_bi_chan_DUNG_LY_DO():
    """Chương trình mô hình THẬT đã viết, không phải fixture ta dựng cho vừa.

    Phải chết vì `UNANCHORED_DERIVED_ASSUMPTION`, KHÔNG phải chết tình cờ vì
    grounding thiếu fact — đó là phân biệt giữa "đã chặn" và "may mà hỏng".
    """
    assert _MATRIX.exists(), "artifact matrix mất — ca này mất đối tượng"
    d = json.loads(_MATRIX.read_text(encoding="utf-8"))
    c = next(x for x in d["cases"] if x["case_id"] == "gm_10_ngoai_nang_luc")
    v = validate_semantic_program(json.loads(c["programs"][-1]))
    assert v.ok, v.error

    # Hợp đồng có ĐỦ fact mà chương trình tham chiếu, để lý do duy nhất còn lại
    # là rửa năng lực chứ không phải thiếu neo dữ liệu.
    fids = sorted({d0.source_fact_id for d0 in v.spec.memory_declarations
                   if d0.source_fact_id})
    hd = build_request_contract(
        {"obligations": [],
         "input_facts": [{"id": f, "label": f} for f in fids]},
        problem_text=DE_GM10)
    g = check_grounding(hd, v.spec)
    assert not g.ok, "chương trình rửa năng lực vẫn qua được cổng"
    assert g.error_code == ERR_RUA_NANG_LUC, (
        f"chặn nhưng SAI LÝ DO: {g.error_code}")
    assert any("P_opposite" in u for u in g.unresolved)


def test_gm10_KHONG_bi_chan_khi_KHONG_co_de():
    """Đối chứng: bỏ đề đi thì cổng thôi kết luận — chứng minh phép chặn đến
    TỪ ĐỀ, không từ một luật ngầm nào khác."""
    d = json.loads(_MATRIX.read_text(encoding="utf-8"))
    c = next(x for x in d["cases"] if x["case_id"] == "gm_10_ngoai_nang_luc")
    v = validate_semantic_program(json.loads(c["programs"][-1]))
    fids = sorted({d0.source_fact_id for d0 in v.spec.memory_declarations
                   if d0.source_fact_id})
    hd = build_request_contract(
        {"obligations": [], "input_facts": [{"id": f, "label": f} for f in fids]},
        problem_text="")
    assert check_grounding(hd, v.spec).ok


# ══ ④b HỆ QUẢ KHÔNG CÓ NGƯỜI DỰNG — §6 ═════════════════════════════════
DE_GOI_M = (DE_CHOP[:-1] + " Gọi M là trung điểm của SA và gọi H là hình "
            "chiếu của A lên (SBD).")


def test_de_TANG_TEN_cho_diem_phu_thi_van_phai_DUNG():
    """Lỗ mà chốt ⑤ một mình không bịt: `M` CÓ trong đề, nên "không có trong
    đề bài" không áp được — nhưng khai `M = [0,0,1]` vẫn là giấu một phép
    trung điểm vào một con số."""
    g = _cham(_ct([_diem("A", [0, 0, 0]), _diem("S", [0, 0, 2]),
                   _diem("M", [0, 0, 1], "trung điểm SA")]), DE_GOI_M)
    assert not g.ok, "điểm phụ đề nêu vẫn khai được bằng toạ độ"
    assert g.error_code == ERR_THIEU_NGUOI_DUNG
    assert any("dựng" in u.lower() for u in g.unresolved)


def test_cung_diem_do_neu_DUNG_RA_thi_QUA():
    """Đối chứng bắt buộc: cùng đề, cùng tên `M`, khác mỗi chỗ ai tính toạ độ."""
    g = _cham(_ct(
        [_diem("A", [0, 0, 0]), _diem("S", [0, 0, 2]),
         {"kind": "construct_point", "target_var": "M",
          "expr": {"kind": "midpoint", "a": "A", "b": "S"}}],
        [{"name": "M", "type": "point3"}]), DE_GOI_M)
    assert g.ok, g.unresolved


def test_DINH_cua_hinh_khong_bi_nham_la_he_qua():
    """`S`, `A`, `B`… là DỮ KIỆN của hình, không phải hệ quả — chốt ⑥ không
    được chạm vào chúng, nếu không mọi bài đều chết."""
    from app.simulation.semantic_program.source_entities import nhan_suy_ra
    assert nhan_suy_ra(DE_GOI_M) == {"M", "H"}
    g = _cham(_ct([_diem("S", [0, 0, 2]), _diem("A", [0, 0, 0]),
                   _diem("B", [2, 0, 0])]), DE_GOI_M)
    assert g.ok, g.unresolved


def test_gioi_thieu_NHIEU_diem_mot_menh_de():
    from app.simulation.semantic_program.source_entities import nhan_suy_ra
    de = "Gọi M, N lần lượt là trung điểm của AB và CD. Tính MN."
    assert {"M", "N"} <= nhan_suy_ra(de)


# ══ ⑤ VỊ TRÍ TRONG PIPELINE (§22) ══════════════════════════════════════
def test_chan_TRUOC_khi_thuc_thi_khong_phai_sau():
    """Cổng phải chặn ở tầng grounding — tầng 1, TRƯỚC thực thi.

    Vì sao vị trí là một khẳng định cần khoá: chặn SAU khi chạy nghĩa là
    chương trình rửa năng lực đã kịp sinh trace và đáp số. Lúc ấy mọi thứ hạ
    nguồn — telemetry, phân loại thất bại, và nhất là bộ nhớ của người đọc báo
    cáo — đã ghi nhận một lượt "chạy được". `stage_reached` là chỗ duy nhất
    phân biệt hai điều đó, nên nó phải được khẳng định chứ không suy diễn.
    """
    from app.simulation.semantic_program.route import verify_and_compile

    ct = _ct([_diem("A", [0, 0, 0]), _diem("B", [2, 0, 0]),
              _diem("P_opposite", [2, 2, 2], "đỉnh đối diện")])
    v = validate_semantic_program(ct)
    assert v.ok, v.error
    kq = verify_and_compile(_hd(), v.spec)
    assert kq.stage_reached == "grounding", (
        f"chặn ở '{kq.stage_reached}' — muộn hơn grounding là đã chạy rồi")
    assert kq.executable is False and kq.servable is False
    assert any(ERR_RUA_NANG_LUC in d for d in kq.details), kq.details


# ══ ⑥ HỒI QUY: gộp khai báo vẫn chạy (§14) ══════════════════════════════
def test_gop_khai_bao_KHONG_hoi_quy():
    """`declare_point` + một khai báo cùng tên vẫn gộp, và vẫn qua cổng."""
    g = _cham(_ct([_diem("A", [0, 0, 0]), _diem("B", [2, 0, 0])],
                  [{"name": "A", "type": "point3"}]))
    assert g.ok, g.unresolved
