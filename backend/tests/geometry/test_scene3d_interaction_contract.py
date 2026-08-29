# -*- coding: utf-8 -*-
"""Hợp đồng TƯƠNG TÁC của Scene3D — bốn trường mới. 0 API call.

Chạy một chương trình THẬT qua interpreter rồi soi cảnh, chứ không dựng cảnh
bằng tay: bốn trường này phải rơi ra từ dữ liệu hệ đã có (`sources`,
`producer`, `origin`, nghĩa vụ của hợp đồng), và một fixture viết tay sẽ xanh
kể cả khi phép dẫn xuất hỏng.

Ranh giới mà cả file này khoá: **không trường nào trong bốn trường ấy đi vào
phép tính**. Chúng là dữ liệu trình bày. Kernel, checker và mọi cổng đọc
`GeometryState`; nếu một ngày nào đó một cổng đọc `display_group` thì một thay
đổi thẩm mỹ sẽ đổi được phán quyết.
"""
from __future__ import annotations

from app.simulation.semantic_program.interpreter import SemanticProgramInterpreter
from app.simulation.semantic_program.obligations import Obligation
from app.simulation.semantic_program.request_contract import RequestContract
from app.simulation.semantic_program.scene3d import (
    BIEN_DOI_DONG_NHAT,
    build_scene3d,
)
from app.simulation.semantic_program.simulation_state import build_simulation_state
from app.simulation.semantic_program.validator import validate_semantic_program


def _diem(ten: str, xyz) -> dict:
    return {"name": ten, "type": "point3", "initial_value": list(xyz),
            "model_assumption": f"chọn {ten}"}


#: Tứ diện `S.ABC` + trung điểm M của AB + thể tích. §11 đòi đúng hình dạng
#: này: đỉnh · cạnh · mặt · vật phụ trợ · phụ thuộc · timeline.
DECLS = [
    _diem("A", (0, 0, 0)), _diem("B", (1, 0, 0)),
    _diem("C", (0, 1, 0)), _diem("S", (0, 0, 1)),
    {"name": "M", "type": "point3"},
    {"name": "chop", "type": "solid"},
    {"name": "V", "type": "float", "initial_value": 0},
]
STMTS = [
    {"kind": "construct_point", "target_var": "M", "label": "M",
     "expr": {"kind": "midpoint", "a": "A", "b": "B"}},
    {"kind": "construct_solid", "target_var": "chop", "label": "S.ABC",
     "vertices": ["A", "B", "C", "S"],
     "faces": [[0, 1, 2], [0, 1, 3], [1, 2, 3], [0, 2, 3]]},
    {"kind": "assign", "target_var": "V",
     "expr": {"kind": "measure", "quantity": "volume", "of": "chop"}},
]
HOP_DONG = RequestContract(obligations=(
    Obligation(kind="volume", container="chop", params={"witness": "V"}),))


def _canh():
    val = validate_semantic_program({
        "simulation_id": "geometry.demo", "title": "Tứ diện S.ABC",
        "description": "Dựng trung điểm rồi đo thể tích",
        "pedagogical_intent": "Cho thấy thứ tự dựng hình",
        "memory_declarations": DECLS, "statements": STMTS, "obligations": []})
    assert val.ok, val.error
    ket = SemanticProgramInterpreter().execute(val.spec)
    return build_scene3d(build_simulation_state(val.spec, ket, HOP_DONG))


def _theo_id(canh):
    return {o["id"]: o for o in canh["objects"]}


# ══ A · bốn trường có mặt trên MỌI thực thể ══════════════════════════════
def test_A_moi_thuc_the_co_du_bon_truong():
    canh = _canh()
    assert canh["objects"], "cảnh rỗng thì test không kiểm được gì"
    for o in canh["objects"]:
        assert "parent" in o
        assert isinstance(o["display_group"], list) and o["display_group"]
        assert o["visual_transform"] == BIEN_DOI_DONG_NHAT
        assert isinstance(o["source"], dict)


# ══ B · parent là CHỨA ĐỰNG, depends là DỰNG TỪ ═════════════════════════
def test_B_parent_khong_pha_depends():
    o = _theo_id(_canh())
    # Đỉnh NẰM TRONG khối, nhưng không phụ thuộc khối.
    assert o["A"]["parent"] == "chop"
    assert "chop" not in o["A"]["depends"]
    # Khối phụ thuộc các đỉnh — chiều ngược lại của cùng cặp vật.
    assert set(o["chop"]["depends"]) >= {"A", "B", "C", "S"}
    # M dựng TỪ A, B nhưng không NẰM TRONG chúng.
    assert o["M"]["depends"] == ["A", "B"]
    assert o["M"]["parent"] in (None, "chop")


def test_B2_hai_khoi_cung_nhan_mot_dinh_thi_KHONG_gan_cha():
    """Mơ hồ ⇒ không cha. Gán bừa vào một trong hai là nói sai cấu trúc."""
    from app.simulation.semantic_program.scene3d import _cha

    objs = [
        {"id": "A", "type": "point3", "depends": []},
        {"id": "k1", "type": "solid", "depends": ["A", "B"]},
        {"id": "k2", "type": "solid", "depends": ["A", "C"]},
    ]
    assert _cha(objs).get("A") is None


# ══ C · nhóm hiển thị DẪN XUẤT, ổn định ═════════════════════════════════
def test_C_nhom_hien_thi_dan_xuat_tu_vai_tro():
    o = _theo_id(_canh())
    assert "given" in o["A"]["display_group"]          # điểm đề cho / hệ trục
    assert "construction" in o["M"]["display_group"]   # dựng ra
    assert "solid" in o["chop"]["display_group"]
    assert "measurement" in o["V"]["display_group"]
    # `target` đọc từ NGHĨA VỤ CỦA ĐỀ, không phải từ chương trình tự khai.
    assert "target" in o["chop"]["display_group"]
    assert "target" in o["V"]["display_group"]
    assert "target" not in o["M"]["display_group"]


def test_C2_khong_co_hop_dong_thi_khong_co_nhom_target():
    """Không biết đề hỏi gì ⇒ không nhóm nào tên `target`. Không đoán."""
    val = validate_semantic_program({
        "simulation_id": "geometry.demo", "title": "Tứ diện S.ABC",
        "description": "Mô tả", "pedagogical_intent": "Ý đồ",
        "memory_declarations": DECLS, "statements": STMTS, "obligations": []})
    ket = SemanticProgramInterpreter().execute(val.spec)
    canh = build_scene3d(build_simulation_state(val.spec, ket))
    assert all("target" not in o["display_group"] for o in canh["objects"])


def test_C3_nhom_on_dinh_giua_hai_lan_dung():
    a = {o["id"]: o["display_group"] for o in _canh()["objects"]}
    b = {o["id"]: o["display_group"] for o in _canh()["objects"]}
    assert a == b


# ══ D · biến đổi trình bày mặc định là ĐỒNG NHẤT THỨC ═══════════════════
def test_D_server_luon_phat_dong_nhat_thuc():
    """Bung hình là thao tác của NGƯỜI XEM. Server không bao giờ phát sẵn."""
    for o in _canh()["objects"]:
        assert o["visual_transform"]["translate"] == [0, 0, 0]
        assert o["visual_transform"]["scale"] == 1


def test_D2_bien_doi_trinh_bay_la_SO_khong_phai_chuoi_phan_so():
    """Hai KHÔNG GIAN, hai cách viết số — và trộn chúng đã làm sập khung 3D.

    Toạ độ hình học là chuỗi phân số CHÍNH XÁC (`"1/2"`). Khoảng dịch trình
    bày là SỐ THƯỜNG: nó chưa bao giờ là một mệnh đề toán, nên làm tròn nó
    không sai gì; ép nó thành phân số thì phía kia sinh `"0.244949"` và bộ
    phân tích phân số ném — đúng cái demo tay đã bắt được.
    """
    for o in _canh()["objects"]:
        for x in o["visual_transform"]["translate"]:
            assert isinstance(x, (int, float)) and not isinstance(x, bool), x
        assert isinstance(o["visual_transform"]["scale"], (int, float))
    # Toạ độ HÌNH HỌC thì vẫn phải là chuỗi phân số — không bị kéo theo.
    o = _theo_id(_canh())
    assert o["M"]["xyz"] == ["1/2", "0", "0"]


# ══ G · xuất xứ đủ để SOI, không hơn ════════════════════════════════════
def test_G_xuat_xu_giu_duoc_ba_mau():
    o = _theo_id(_canh())
    assert o["A"]["source"].get("assumption")            # do người giải chọn
    assert o["M"]["source"].get("instruction") == "construct_point.midpoint"
    assert o["V"]["source"].get("instruction") == "measure.volume"
    # KHÔNG chở prompt: mỗi mẩu xuất xứ phải ngắn.
    for x in _canh()["objects"]:
        assert all(len(str(v)) < 200 for v in x["source"].values())


# ══ §11 · DEMO END-TO-END — sáu thao tác đều có dữ liệu ═════════════════
def test_demo_du_du_lieu_cho_sau_thao_tac():
    canh = _canh()
    o = _theo_id(canh)

    # select / inspect
    assert o["M"]["label"] and o["M"]["type"] and o["M"]["producer"]
    # hide / show / isolate — cần nhóm
    assert {g for x in canh["objects"] for g in x["display_group"]} >= {
        "given", "construction", "solid", "measurement", "target"}
    # explode — cần cha hoặc nhóm
    assert any(x["parent"] for x in canh["objects"])
    # dependency highlight — cần đồ thị
    assert o["V"]["depends"] == ["chop"]
    # playback — cần timeline một-đối-một với bước
    b = [e["step_index"] for e in canh["events"]]
    assert b == sorted(b) and len(b) == len(set(b))
    assert any(e["object"] == "M" for e in canh["events"])
    # kéo hợp lệ — cần biết vật nào TỰ DO
    assert set(canh["free_objects"]) == {"A", "B", "C", "S"}


def test_toa_do_van_la_PHAN_SO_CHINH_XAC_sau_khi_them_bon_truong():
    """Bốn trường mới không được kéo theo một `float` nào vào cảnh."""
    o = _theo_id(_canh())
    assert o["M"]["xyz"] == ["1/2", "0", "0"]
    assert o["V"]["value"] == "1/6"
