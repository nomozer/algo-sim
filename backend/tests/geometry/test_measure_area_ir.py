# -*- coding: utf-8 -*-
"""`measure area` đi HẾT đường IR — schema → thẩm định tĩnh → interpreter →
cảnh. **0 API call.**

─── VÌ SAO KHÔNG ĐỦ NẾU CHỈ TEST KERNEL ───────────────────────────────────

`area_polygon` đúng mà không có ai gọi được nó thì diện tích vẫn **không tồn
tại** với hệ — đúng bài học `distance_sq_skew_lines` đã dạy: kernel có sẵn phép
tính từ đầu, cầu nối chưa nối, và `hp_b01_032` chết hai lượt ở Phase 7B với câu
*"cặp đối tượng không hợp lệ"*.

Nên file này đo **đường**, không đo công thức: một chương trình viết bằng đúng
từ vựng mà mô hình sẽ dùng, chạy qua interpreter thật, ra đại lượng thật, rồi
lên tới cảnh với một cái tên học sinh đọc được.

─── R0 GIỮ NGUYÊN ─────────────────────────────────────────────────────────

Chương trình chỉ nói *"đo diện tích của hình này"*. Không ô nào điền được một
con số — giá trị do `geometry/measure.py` tính.
"""
from __future__ import annotations

from fractions import Fraction as F

import pytest

from app.simulation.geometry.radical import Radical, display, radical
from app.simulation.semantic_program.contract import SemanticProgramSpec
from app.simulation.semantic_program.interpreter import SemanticProgramInterpreter
from app.simulation.semantic_program.ir_static_check import kiem_tinh
from app.simulation.semantic_program.measure_contract import BANG_PHEP_DO


def _spec(statements: list[dict], them: list[dict] | None = None) -> dict:
    """Hộp 1×1×1 + bốn đỉnh mặt đáy. Toạ độ hữu tỉ, do đề đặt — không kết quả."""
    return {
        "spec_version": "1.0",
        "title": "Diện tích hình phẳng",
        "description": "Dựng một hình phẳng rồi đo diện tích của nó.",
        "pedagogical_intent": "Thấy diện tích là hệ quả của hình đã dựng.",
        "memory_declarations": [
            {"name": "A", "type": "point3", "initial_value": [0, 0, 0]},
            {"name": "B", "type": "point3", "initial_value": [1, 0, 0]},
            {"name": "C", "type": "point3", "initial_value": [1, 1, 1]},
            {"name": "D", "type": "point3", "initial_value": [0, 1, 1]},
            {"name": "hop", "type": "solid", "initial_value": {
                "vertices": [[0, 0, 0], [2, 0, 0], [2, 2, 0], [0, 2, 0],
                             [0, 0, 2], [2, 0, 2], [2, 2, 2], [0, 2, 2]],
                "faces": [[0, 3, 2, 1], [4, 5, 6, 7], [0, 1, 5, 4],
                          [1, 2, 6, 5], [2, 3, 7, 6], [3, 0, 4, 7]],
            }},
            # Vật DỰNG RA và đại lượng ĐO ĐƯỢC đều phải khai kiểu trước — đó
            # là hợp đồng của IR, không phải chi tiết của test. Đại lượng khai
            # `float` theo đúng quy ước hiện hành (`measure` trả `ExactNumber`,
            # `float` là ô kiểu mà hợp đồng dành cho nó).
            {"name": "tudiac", "type": "polygon3"},
            {"name": "tg", "type": "polygon3"},
            {"name": "td", "type": "section"},
            *[{"name": n, "type": "float"}
              for n in ("S", "V", "S_ABCD", "S_td")],
            *(them or []),
        ],
        "statements": statements,
        "visual_bindings": {"containers": [], "pointers": [], "value_boxes": []},
    }


def _chay(raw: dict):
    return SemanticProgramInterpreter().execute(
        SemanticProgramSpec.model_validate(raw))


def _canh(raw: dict) -> dict:
    """Chạy rồi chiếu sang cảnh — `build_scene(spec, memory)`, hai đối số."""
    from app.simulation.semantic_program.simulation_state import build_scene

    spec = SemanticProgramSpec.model_validate(raw)
    return build_scene(spec, SemanticProgramInterpreter().execute(spec).final_memory)


# ══ I1 · ĐA GIÁC ═════════════════════════════════════════════════════════
def test_I1_area_tren_polygon3_chay_het_duong():
    """Tứ giác `ABCD` nghiêng ⇒ `S = √2`. Kiểm tay: đáy `AB = 1`, cạnh bên
    `BC = √2`, hai cạnh vuông góc."""
    kq = _chay(_spec([
        {"kind": "construct_polygon", "target_var": "tudiac",
         "vertices": ["A", "B", "C", "D"], "label": "ABCD"},
        {"kind": "assign", "target_var": "S_ABCD",
          "expr": {"kind": "measure", "quantity": "area", "of": "tudiac"}},
    ]))
    s = kq.final_memory["S_ABCD"]
    assert s == radical(1, 2) and display(s) == "√2"
    assert isinstance(s, Radical), "đại lượng vô tỉ KHÔNG được rơi về float"


def test_I1b_tam_giac_cho_dai_luong_HUU_TI():
    """`A(0,0,0) B(1,0,0) D(0,1,1)` ⇒ `|AB × AD| = |(0,-1,1)| = √2` ⇒
    `S = √2/2`. Kiểm tay, không chép từ máy."""
    kq = _chay(_spec([
        {"kind": "construct_polygon", "target_var": "tg",
         "vertices": ["A", "B", "D"]},
        {"kind": "assign", "target_var": "S",
         "expr": {"kind": "measure", "quantity": "area", "of": "tg"}},
    ]))
    assert kq.final_memory["S"] == radical(F(1, 2), 2)
    assert display(kq.final_memory["S"]) == "√2/2"


# ══ I2 · THIẾT DIỆN ══════════════════════════════════════════════════════
def test_I2_area_tren_section_chay_het_duong():
    """Lục giác đều cạnh √2 cắt hộp 2×2×2 ⇒ `S = 3√3`. Cùng ca với
    `test_A5`, nhưng đi qua IR — hai tầng, hai phép đo, một đáp số."""
    kq = _chay(_spec(
        [{"kind": "construct_section", "target_var": "td",
          "solid": "hop", "plane": "mp", "label": "thiết diện"},
         {"kind": "assign", "target_var": "S_td",
           "expr": {"kind": "measure", "quantity": "area", "of": "td"}}],
        them=[{"name": "mp", "type": "plane3", "initial_value": {
            "through": [[2, 0, 1], [0, 2, 1], [1, 0, 2]]}}],
    ))
    s = kq.final_memory["S_td"]
    assert display(s) == "3√3", f"kiểm tay: lục giác đều cạnh √2 ⇒ 3√3, có {display(s)}"


# ══ I3 · KIỂU SAI BỊ CHẶN Ở THẨM ĐỊNH TĨNH ═══════════════════════════════
@pytest.mark.parametrize("kieu,ten", [("solid", "hop"), ("point3", "A")])
def test_I3_area_tren_kieu_SAI_bi_chan_TINH(kieu, ten):
    """Chặn ở tầng TĨNH, không để rơi xuống runtime.

    Lỗi runtime **không** được gửi ngược cho mô hình sửa, nên nó giết cả ca;
    lỗi tĩnh thì được. `solid` là ca đáng kể: "diện tích toàn phần một khối" là
    một đại lượng khác, và tổng diện tích các mặt rơi đúng vào tổng nhiều căn
    thức mà miền số từ chối.
    """
    raw = _spec([{"kind": "assign", "target_var": "S",
                  "expr": {"kind": "measure", "quantity": "area", "of": ten}}])
    kq = kiem_tinh(SemanticProgramSpec.model_validate(raw))
    assert not kq.ok, f"`area` trên '{kieu}' lọt qua thẩm định tĩnh"
    assert any(ten == i.object_id for i in kq.issues)


def test_I3b_area_KHONG_nhan_wrt():
    """`area` là phép đo một toán hạng. Bảng là thẩm quyền — validator sinh
    câu *"Chỉ volume, area đo trên một đối tượng"* từ chính nó."""
    assert not BANG_PHEP_DO["area"].hai_toan_hang
    assert BANG_PHEP_DO["area"].kieu_of == ("polygon3", "section", "circle3")
    assert BANG_PHEP_DO["area"].kieu_wrt == ()


def test_I3c_area_hop_le_thi_tham_dinh_tinh_CHO_QUA():
    """Nửa còn lại của I3 — một cổng chỉ biết nói KHÔNG là một cổng hỏng."""
    for ten, dung in (("tudiac", {"kind": "construct_polygon",
                                  "target_var": "tudiac",
                                  "vertices": ["A", "B", "C", "D"]}),):
        raw = _spec([dung, {"kind": "assign", "target_var": "S",
                            "expr": {"kind": "measure", "quantity": "area",
                                     "of": ten}}])
        assert kiem_tinh(SemanticProgramSpec.model_validate(raw)).ok


# ══ I4 · ĐẠI LƯỢNG LÊN TỚI CẢNH, CÓ TÊN ĐỌC ĐƯỢC ═════════════════════════
def test_I4_dai_luong_len_canh_voi_ten_hoc_sinh_doc_duoc():
    """`§20` — backend sở hữu tên. Không `id` trần, không bảng ở frontend."""
    canh = _canh(_spec([
        {"kind": "construct_polygon", "target_var": "tudiac",
         "vertices": ["A", "B", "C", "D"], "label": "ABCD"},
        {"kind": "assign", "target_var": "S_ABCD", "label": "diện tích ABCD",
         "expr": {"kind": "measure", "quantity": "area", "of": "tudiac"}},
    ]))
    vat = next(o for o in canh["objects"] if o["id"] == "S_ABCD")
    assert vat["type"] == "quantity"
    assert vat["label"] and vat["label"] != "S_ABCD", "nhãn rơi về `id`"
    assert vat["exact"] == {"kind": "radical", "coefficient": "1",
                            "radicand": 2}, "cấu trúc chính xác không tới cảnh"
    assert "pi" not in vat["exact"], "số không chứa π mà dây lại có `pi`"


def test_I4b_ten_mac_dinh_khi_mo_hinh_KHONG_dat_nhan():
    """Không nhãn thì backend vẫn phải trả một CÂU — `_CACH_GOI` dựng nó từ
    phép đo, và ký hiệu là `S(…)`, cùng họ với `V(…)`."""
    canh = _canh(_spec([
        {"kind": "construct_polygon", "target_var": "tudiac",
         "vertices": ["A", "B", "C", "D"], "label": "ABCD"},
        {"kind": "assign", "target_var": "S_ABCD",
          "expr": {"kind": "measure", "quantity": "area", "of": "tudiac"}},
    ]))
    vat = next(o for o in canh["objects"] if o["id"] == "S_ABCD")
    assert "iện tích" in vat["label"], vat["label"]
    assert vat["notation"] and vat["notation"].startswith("S("), vat["notation"]
    assert vat["label"] != "S_ABCD"


# ══ I5 · XUẤT XỨ / VẾT ═══════════════════════════════════════════════════
def test_I5_phep_do_sinh_MOT_buoc_vet_va_khai_xuat_xu():
    kq = _chay(_spec([
        {"kind": "construct_polygon", "target_var": "tudiac",
         "vertices": ["A", "B", "C", "D"], "label": "ABCD"},
        {"kind": "assign", "target_var": "S",
          "expr": {"kind": "measure", "quantity": "area", "of": "tudiac"}},
    ]))
    buoc = [t for t in kq.trace if t.target == "S"]
    assert len(buoc) == 1, "phép đo phải là ĐÚNG một bước học sinh nhìn thấy"
    # `assign` — `measure` là BIỂU THỨC, câu lệnh chở nó là `assign`. Bất biến
    # #31 (`frame k ⇔ trace[k]`) giữ nguyên: một câu lệnh, một khung.
    assert buoc[0].action == "assign"
    assert buoc[0].tier1_narration, "bước đo không có lời kể cho học sinh"
    assert {"S", "tudiac"} <= set(kq.final_memory)


def test_I5b_producer_noi_dung_phep_do():
    canh = _canh(_spec([
        {"kind": "construct_polygon", "target_var": "tudiac",
         "vertices": ["A", "B", "C", "D"]},
        {"kind": "assign", "target_var": "S",
          "expr": {"kind": "measure", "quantity": "area", "of": "tudiac"}},
    ]))
    vat = next(o for o in canh["objects"] if o["id"] == "S")
    assert vat["producer"] == "measure.area"
    # `sources` ở tầng `simulation_state`; `scene3d` đổi tên nó thành `depends`
    # khi dựng payload renderer. Đo ở đúng tầng đang gọi, không đoán tên.
    assert vat["sources"] == ["tudiac"]
    assert vat["origin"] == "derived" and vat["synthetic"] is False


# ══ I6 · TUYẾN `readout` CŨ KHÔNG ĐỔI ════════════════════════════════════
def test_I6_area_di_dung_tuyen_readout_nhu_volume():
    """Đại lượng đo được không vẽ lên khung nhưng PHẢI hiện lên — nó là câu
    trả lời của bài. `area` dùng lại đúng tuyến `quantity → readout` mà
    `volume`/`distance` đã đi; không có loại vẽ mới nào ra đời ở wave này.
    """
    from app.simulation.semantic_program.scene3d import RENDER_HINT
    canh = _canh(_spec([
        {"kind": "construct_polygon", "target_var": "tudiac",
         "vertices": ["A", "B", "C", "D"]},
        {"kind": "assign", "target_var": "S",
          "expr": {"kind": "measure", "quantity": "area", "of": "tudiac"}},
        {"kind": "assign", "target_var": "V",
          "expr": {"kind": "measure", "quantity": "volume", "of": "hop"}},
    ]))
    loai = {o["id"]: o["type"] for o in canh["objects"]}
    assert loai["S"] == loai["V"] == "quantity"
    assert RENDER_HINT["quantity"] == "readout"
