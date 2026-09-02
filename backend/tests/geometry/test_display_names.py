# -*- coding: utf-8 -*-
"""THẨM QUYỀN TÊN HIỂN THỊ — kiểu KHAI thắng, và `id` không bao giờ là tên.

Hai lỗ được đóng ở đây, cả hai đo được ở
`GEOMETRY_ARCHITECTURE_EXPRESSIVENESS_AUDIT`:

  G1 §5  `label` rơi về `id` khi mô hình không đặt tên ⇒ học sinh đọc
         `khoang_cach_hs √22` trên màn hình.
  G2 §19 `vector3` mất kiểu ở `build_scene` (dùng chung `Vec3` với `point3`)
         ⇒ frontend phải đọc `producer` để đoán ngược.

Mỗi ca dưới đây phải ĐỎ khi ai đó quay lại cách cũ, không chỉ khi kết quả xấu
đi — nên chúng khoá **bất biến**, không khoá đúng một câu tiếng Việt: cách hành
văn là quyết định trình bày và được phép đổi, còn *"tên không phải là id"* thì
không.
"""
from __future__ import annotations

import pytest

from app.simulation.semantic_program.contract import SemanticProgramSpec
from app.simulation.semantic_program.display_names import ten_hien_thi
from app.simulation.semantic_program.interpreter import SemanticProgramInterpreter
from app.simulation.semantic_program.scene3d import build_scene3d
from app.simulation.semantic_program.simulation_state import build_simulation_state
from app.simulation.semantic_program.source_entities import ky_hieu_toan


def _canh(ct: dict) -> dict[str, dict]:
    spec = SemanticProgramSpec.model_validate(ct)
    st = build_simulation_state(spec, SemanticProgramInterpreter().execute(spec))
    return {o["id"]: o for o in build_scene3d(st)["objects"]}


def _diem(*ten_va_toa):
    return [{"name": n, "type": "point3", "initial_value": v}
            for n, v in ten_va_toa]


# ══ 1. KIỂU KHAI LÀ THẨM QUYỀN (§20) ═════════════════════════════════════
CT_VECTO = {
    "spec_version": "1.0", "title": "Vectơ và góc có dấu",
    "memory_declarations": _diem(("A", [0, 0, 0]), ("B", [1, 0, 0]),
                                 ("C", [0, 1, 0]))
    + [{"name": "u", "type": "vector3"}, {"name": "v", "type": "vector3"},
       {"name": "g", "type": "float"}],
    "statements": [
        {"kind": "assign", "target_var": "u",
         "expr": {"kind": "vector_from_points", "from_point": "A", "to_point": "B"}},
        {"kind": "assign", "target_var": "v",
         "expr": {"kind": "vector_from_points", "from_point": "A", "to_point": "C"}},
        {"kind": "assign", "target_var": "g",
         "expr": {"kind": "measure", "quantity": "angle_cos", "of": "u", "wrt": "v"}},
    ],
}


@pytest.fixture(scope="module")
def vt() -> dict[str, dict]:
    return _canh(CT_VECTO)


def test_diem_va_vecto_CUNG_la_Vec3_o_runtime_nhung_KHAC_kieu_trong_canh(vt):
    """Ca trung tâm của G2.

    `point3` và `vector3` dùng chung lớp `Vec3`, nên phân loại bằng
    `isinstance` cho ra **cùng một kiểu** cho hai thứ khác hẳn nhau. Ca này đỏ
    ngay khi ai đó quay về phân loại theo lớp runtime.
    """
    assert vt["A"]["type"] == "point3"
    assert vt["u"]["type"] == "vector3"
    assert vt["v"]["type"] == "vector3"


def test_vecto_KHONG_hien_thanh_mot_diem_cua_hinh(vt):
    """`xyz` của một vectơ là THÀNH PHẦN, không phải toạ độ một điểm.

    Vẽ nó như một chấm là đặt lên hình một vật không tồn tại trong bài — đo
    được: `vector_AA′` hiện thành chấm đỏ ở (1,1,3), nơi không có điểm nào.
    """
    assert vt["u"]["render"] == "non_visual"
    assert vt["A"]["render"] == "point_marker"


def test_vecto_VAN_di_het_pipeline_du_khong_ve(vt):
    """`non_visual` là *"không có hình"*, KHÔNG phải *"bị loại khỏi cảnh"*.

    Vật vẫn phải chọn được, soi được, và mang đủ xuất xứ — nếu không thì bản
    sửa chỉ đổi một khiếm khuyết (vẽ sai) lấy một khiếm khuyết khác (biến mất).
    """
    u = vt["u"]
    assert u["producer"] == "vector_from_points"
    assert u["depends"] == ["A", "B"]
    assert "xyz" in u


# ══ 2. TÊN HIỂN THỊ (§22) ════════════════════════════════════════════════
CT_DAY_DU = {
    "spec_version": "1.0", "title": "Chóp, hình chiếu, khoảng cách và thể tích",
    "memory_declarations": _diem(("A", [0, 0, 0]), ("B", [2, 0, 0]),
                                 ("C", [2, 2, 0]), ("D", [0, 2, 0]),
                                 ("S", [0, 0, 2]))
    + [{"name": n, "type": t} for n, t in [
        ("M", "point3"), ("H", "point3"), ("I", "point3"),
        ("ac", "line3"), ("bd", "line3"), ("day", "plane3"),
        ("chop", "solid"), ("kc", "float"), ("V", "float")]],
    "statements": [
        {"kind": "construct_point", "target_var": "M",
         "expr": {"kind": "midpoint", "a": "S", "b": "C"}},
        {"kind": "construct_line", "target_var": "ac",
         "through_a": "A", "through_b": "C"},
        {"kind": "construct_line", "target_var": "bd",
         "through_a": "B", "through_b": "D"},
        {"kind": "construct_point", "target_var": "I",
         "expr": {"kind": "intersect_line_line", "line_a": "ac", "line_b": "bd"}},
        {"kind": "construct_plane", "target_var": "day",
         "through": ["A", "B", "C"]},
        {"kind": "construct_point", "target_var": "H",
         "expr": {"kind": "project_onto", "point": "S", "target": "day"}},
        {"kind": "construct_solid", "target_var": "chop",
         "vertices": ["A", "B", "C", "D", "S"],
         "faces": [["A", "B", "C", "D"], ["S", "A", "B"], ["S", "B", "C"],
                   ["S", "C", "D"], ["S", "D", "A"]]},
        {"kind": "assign", "target_var": "kc",
         "expr": {"kind": "measure", "quantity": "distance",
                  "of": "S", "wrt": "day"}},
        {"kind": "assign", "target_var": "V",
         "expr": {"kind": "measure", "quantity": "volume", "of": "chop"}},
    ],
}


@pytest.fixture(scope="module")
def dd() -> dict[str, dict]:
    return _canh(CT_DAY_DU)


@pytest.mark.parametrize("ten,phai_nhac", [
    ("M", ("S", "C")),        # trung điểm
    ("I", ("AC", "BD")),      # giao điểm hai đường
    ("H", ("S",)),            # hình chiếu
    ("kc", ("S",)),           # khoảng cách
    ("V", ()),                # thể tích
    ("A", ()),                # vật gốc, chương trình KHÔNG đặt tên
])
def test_moi_vat_co_ten_doc_duoc_va_nhac_dung_toan_hang(dd, ten, phai_nhac):
    """Không khoá đúng một câu — khoá **tính chất** của câu.

    Cách hành văn là quyết định trình bày, được phép đổi. Ba điều dưới đây thì
    không: tên phải khác rỗng, phải khác `id` thô, và phải gọi tên đúng những
    toán hạng đã sinh ra vật.
    """
    nhan = dd[ten]["label"]
    assert nhan and nhan.strip()
    assert nhan != ten or ky_hieu_toan(ten) is not None
    for k in phai_nhac:
        assert k in nhan, f"tên của '{ten}' không nhắc toán hạng '{k}': {nhan!r}"


def test_dai_luong_do_KHONG_con_mang_ten_bien_IR(dd):
    """Ca nghiệm thu bắt buộc của G1.

    Trước bản này `label` của một `quantity` **luôn** bằng `id`, vì
    `_provenance` ghi thẳng `label: None` rồi `build_scene` lùi về `id`. Đó là
    đường mà `khoang_cach_hs` và `the_tich_sabcd` đi lên màn hình.
    """
    for ten in ("kc", "V"):
        assert dd[ten]["label"] != ten
        assert dd[ten]["type"] == "quantity"


def test_gia_tri_CHINH_XAC_khong_bi_ten_goi_dong_toi(dd):
    """Đổi siêu dữ liệu, KHÔNG đổi toán học. `V(S.ABCD)` của chóp đáy 2×2 cao
    2 là `8/3`; khoảng cách từ `S` tới đáy là `2`."""
    assert dd["V"]["exact"] == {"kind": "rational", "value": "8/3"}
    assert dd["kc"]["exact"] == {"kind": "rational", "value": "2"}


# ══ 3. KÝ HIỆU NGẮN (§10) ════════════════════════════════════════════════
def test_ky_hieu_ghep_tu_ky_hieu_cua_toan_hang(dd):
    """Ký hiệu dựng ĐỆ QUY từ ký hiệu toán hạng, đáy ở các điểm gốc."""
    assert dd["A"]["notation"] == "A"
    assert dd["ac"]["notation"] == "AC"
    assert dd["day"]["notation"] == "(ABC)"
    assert dd["kc"]["notation"] == "d(S, (ABC))"


def test_thieu_MOT_ky_hieu_toan_hang_thi_HONG_CA(dd):
    """Fail-closed, và đây là ca chứng minh nó.

    `chop` trong hợp đồng này KHÔNG được mô hình đặt nhãn, và không phép ghép
    nào dựng lại được ký hiệu `S.ABCD` — thứ tự đỉnh–đáy không suy ra từ bảng
    mặt. Nên `V(…)` thiếu toán hạng, và câu trả lời đúng là **không có ký
    hiệu**, không phải `V(chop)` hay `V(?)`.

    `(M?P)` trông như một ký hiệu thật và tệ hơn hẳn không có ký hiệu nào.
    """
    assert dd["chop"]["notation"] is None
    assert dd["V"]["notation"] is None
    # …nhưng TÊN thì vẫn phải có: hai vai độc lập nhau.
    assert dd["V"]["label"] != "V"


def test_nhan_mo_hinh_dat_ĐƯỢC_nhan_la_ky_hieu_khi_no_dung_la_ky_hieu():
    """Bù lại ca trên: mô hình đặt `label: "S.ABCD"` thì đó LÀ ký hiệu chuẩn
    của khối, và `V(S.ABCD)` ghép được. Phân biệt không bằng độ dài mà bằng
    `ky_hieu_toan` — `S.ABCD` là nhãn hình học, `thiết diện` thì không."""
    ct = {**CT_DAY_DU, "statements": [
        {**s, "label": "S.ABCD"} if s.get("target_var") == "chop" else s
        for s in CT_DAY_DU["statements"]
    ]}
    canh = _canh(ct)
    assert canh["chop"]["notation"] == "S.ABCD"
    assert canh["V"]["notation"] == "V(S.ABCD)"


def test_ky_hieu_toan_tu_choi_ten_bien():
    """Thẩm quyền ở `source_entities`, và nó phải nói KHÔNG với tên biến."""
    assert ky_hieu_toan("A") == "A"
    assert ky_hieu_toan("B_prime") == "B'"
    assert ky_hieu_toan("point_A") == "A"
    for xau in ("khoang_cach_hs", "the_tich_sabcd", "plane_MNP",
                "pyramid_S_ABCD", "vector_AA_prime", "V_AMNP"):
        assert ky_hieu_toan(xau) is None, f"{xau!r} không phải ký hiệu toán"


# ══ 4. KHÔNG RÒ ĐỊNH DANH — QUÉT TỔNG QUÁT (§23) ═════════════════════════
@pytest.mark.parametrize("ct", [CT_VECTO, CT_DAY_DU])
def test_KHONG_vat_nao_lay_id_lam_ten_hien_thi(ct):
    """Guard TỔNG QUÁT, không liệt kê ba cái tên đã biết.

    Luật: `label` được phép trùng `id` **chỉ khi** `id` ấy vốn là một ký hiệu
    toán (`A`, `M`, `A'`) — lúc ấy nó không phải định danh máy rò rỉ, nó là ký
    hiệu học sinh đọc trên bảng. Mọi trường hợp khác là fallback về `id`.
    """
    xau = [
        f"{o['id']} → {o['label']!r}"
        for o in _canh(ct).values()
        if o["label"] == o["id"] and ky_hieu_toan(o["id"]) is None
    ]
    assert not xau, "định danh máy lọt vào `label`:\n" + "\n".join(xau)


def test_ten_hien_thi_khong_bao_gio_tra_id_ke_ca_khi_khong_biet_gi():
    """Bậc cuối cùng phải là MÔ TẢ KIỂU, không phải `id`.

    Vật không nhãn, không phép dựng, kiểu lạ — vẫn phải ra một cái tên. Đây là
    chỗ fallback cũ trả `id`, và là chỗ dễ lặng lẽ quay lại nhất.
    """
    ra = ten_hien_thi({
        "khoang_cach_hs": {"type": "quantity", "producer": None,
                           "sources": [], "label": None},
        "x_la_gi": {"type": "kieu_chua_co", "producer": None,
                    "sources": [], "label": None},
    })
    assert ra["khoang_cach_hs"]["label"] == "Đại lượng đo"
    assert ra["khoang_cach_hs"]["notation"] is None
    assert ra["x_la_gi"]["label"] == "Đối tượng"


def test_vong_phu_thuoc_KHONG_lam_treo_luot_dung_canh():
    """Đồ thị là DAG theo hợp đồng, nhưng một vòng ở đây là đệ quy vô hạn giữa
    lúc dựng cảnh — mất cả lượt chạy chứ không phải một nhãn xấu. Chặn bằng cấu
    trúc, không bằng lời hứa của tầng trên."""
    ra = ten_hien_thi({
        "a": {"type": "point3", "producer": "construct_point.midpoint",
              "sources": ["b", "b"], "label": None},
        "b": {"type": "point3", "producer": "construct_point.midpoint",
              "sources": ["a", "a"], "label": None},
    })
    assert set(ra) == {"a", "b"}


# ══ 5. BỐN VAI HIỂN THỊ — và ranh giới giữa chúng ════════════════════════
#
# Thêm 2026-09-03 (`DISPLAY_NAME_AUTHORITY_LEFTOVER`). Hai vấn đề cùng một gốc:
# frontend giữ một bảng `producer → tiếng Việt` thứ hai, và câu của vật này
# nhúng NGUYÊN TÊN của vật kia nên đọc ra mơ hồ.

CT_CHUOI = {
    "spec_version": "1.0", "title": "Chuỗi hai tầng dẫn xuất",
    "memory_declarations": _diem(("A", [0, 0, 0]), ("B", [2, 0, 0]),
                                 ("C", [1, 3, 0]), ("M", [1, 1, 5]))
    + [{"name": n, "type": t} for n, t in [
        ("sc", "line3"), ("mpb", "plane3"), ("abc", "plane3"),
        ("gt", "line3"), ("kc", "float")]],
    "statements": [
        {"kind": "construct_line", "target_var": "sc",
         "through_a": "A", "through_b": "C"},
        # Tầng 1 — vật KHÔNG có ký hiệu toán nào dẫn ra được.
        {"kind": "assign", "target_var": "mpb",
         "expr": {"kind": "plane_perpendicular_to_line",
                  "point": "B", "line": "sc"}},
        # Mô hình ĐẶT TÊN cho mặt này, nên tên và vai trò tách ra được.
        {"kind": "construct_plane", "target_var": "abc",
         "through": ["A", "B", "C"], "label": "(ABC)"},
        # Tầng 2 — nhắc lại vật tầng 1 bên trong câu của mình.
        {"kind": "assign", "target_var": "gt",
         "expr": {"kind": "intersect_plane_plane",
                  "plane_a": "mpb", "plane_b": "abc"}},
        {"kind": "assign", "target_var": "kc",
         "expr": {"kind": "measure", "quantity": "distance",
                  "of": "M", "wrt": "mpb"}},
    ],
}


@pytest.fixture(scope="module")
def ch() -> dict[str, dict]:
    return _canh(CT_CHUOI)


def test_bon_truong_luon_co_mat(ch):
    """`label` · `notation` · `reference` · `role`. Ba trong bốn không bao giờ
    vắng; `notation` thì được phép `None`."""
    for o in ch.values():
        assert o["label"] and o["reference"] and o["role"]
        assert "notation" in o


def test_reference_KHONG_BAO_GIO_la_mot_cau_long(ch):
    """Cách gọi ngắn dựng từ ký hiệu hoặc danh từ theo kiểu — không nhúng cụm
    từ, nên đệ quy dừng ở MỘT tầng và không có câu dài vô hạn."""
    for o in ch.values():
        assert "«" not in o["reference"], o["reference"]
        # Không dài hơn tên của chính nó: `reference` là bản NGẮN, theo định
        # nghĩa. (Bằng nhau là hợp lệ — khi tên vốn đã ngắn.)
        assert len(o["reference"]) <= len(o["label"])


def test_cau_LONG_NHAU_co_cau_truc_KHONG_MO_HO(ch):
    """Ca nghiệm thu của vấn đề thứ hai.

    Trước bản này: *"Giao tuyến của Mặt phẳng qua B và vuông góc với SC và
    (ABC)"* — ba chữ "và", không tách được đâu là hết toán hạng thứ nhất.
    Nay toán hạng nhiều chữ được BỌC, nên tách được bằng cấu trúc.
    """
    nhan = ch["gt"]["label"]
    assert "«" in nhan and "»" in nhan
    # Đúng MỘT toán hạng được bọc — cái không có ký hiệu. `(ABC)` có ký hiệu
    # nên để trần.
    assert nhan.count("«") == 1
    assert "(ABC)" in nhan


def test_role_KHONG_lap_lai_ten(ch):
    """*"Vật này là gì"* nằm dưới tên. Lặp lại y hệt thì không thêm thông tin
    nào, chỉ chiếm chỗ — nên khi tên ĐÃ là câu mô tả, vai trò lùi về danh từ
    theo kiểu."""
    assert ch["mpb"]["role"] == "Mặt phẳng"
    assert ch["mpb"]["label"] != ch["mpb"]["role"]
    # Ngược lại: mặt `(ABC)` mang KÝ HIỆU làm tên, nên vai trò còn chỗ để nói
    # phép dựng — hai dòng bổ sung nhau thay vì lặp nhau.
    assert ch["abc"]["label"] == "(ABC)"
    assert ch["abc"]["role"].startswith("Mặt phẳng qua")


def test_KHONG_bia_ky_hieu_khi_khong_co__nhung_van_doc_duoc(ch):
    """`MISSING_NOTATION_FAILS_TO_NULL` + `LEARNER_DESCRIPTION_STILL_AVAILABLE`."""
    assert ch["mpb"]["notation"] is None
    assert ch["gt"]["notation"] is None
    for ten in ("mpb", "gt"):
        assert len(ch[ten]["label"]) > 5
        assert ch[ten]["label"] != ten


@pytest.mark.parametrize("ten", ["sc", "mpb", "abc", "gt", "kc"])
def test_KHONG_truong_hien_thi_nao_la_id_tho(ch, ten):
    """Guard tổng quát, không liệt kê tên cụ thể: `label`/`reference`/`role`
    được phép trùng `id` chỉ khi `id` vốn là một ký hiệu toán."""
    for truong in ("label", "reference", "role"):
        gt = ch[ten][truong]
        assert gt != ten or ky_hieu_toan(ten) is not None, f"{truong} = id thô"


def test_producer_VAN_CON_cho_che_do_ky_thuat(ch):
    """`producer` là xuất xứ nội bộ và phải còn — chế độ chi tiết của giáo viên
    đọc nó. Điều bị cấm là **frontend dịch nó** thành tiếng người học, không
    phải sự tồn tại của nó.

    Ca này đỏ nếu ai đó gỡ `producer` khỏi cảnh để "cho sạch", và lúc ấy chế độ
    giáo viên mất dữ liệu thật.
    """
    assert ch["mpb"]["producer"] == "plane_perpendicular_to_line"
    assert ch["gt"]["depends"] == ["abc", "mpb"]
    # …và tên người-đọc-được KHÔNG cần `producer` để dựng ra: nó đã nằm sẵn
    # trong envelope.
    assert "plane_perpendicular_to_line" not in ch["mpb"]["label"]
