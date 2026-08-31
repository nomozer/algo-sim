# -*- coding: utf-8 -*-
"""CĂN THỨC ĐI TRỌN CHUỖI — từ IR tới JSON renderer đọc. **0 API call.**

    Semantic Program → thẩm định → thực thi → SimulationState → Scene3D → JSON

─── VÌ SAO CẦN CA NÀY, DÙ MIỀN SỐ ĐÃ CÓ TEST RIÊNG ─────────────────────────

`test_radical_domain` chứng minh `√2` tính đúng. `test_radical_distance` chứng
minh engine đo ra nó và cổng chấm được. Cả hai đều dừng TRƯỚC biên JSON — và
biên ấy là chỗ hỏng thật sự đã xảy ra một lần: `assign` từ `measure` ghi một
`Fraction` vào `details`, `json.dumps` VỠ, và cả lượt đo mất trắng sau khi đã
chạy xong (ghi ở `simulation_state._json_an_toan`).

Một kiểu số MỚI đi qua đúng biên ấy. Nên câu hỏi ở đây không phải *"tính đúng
không"* mà *"có ra khỏi được hệ không"* — và nó phải hỏi bằng cách đi hết đường
sản phẩm, không phải bằng cách gọi hàm serialize một mình.

Đây cũng là bằng chứng thay cho một lượt live (`§20`): đường đi tất định, kết
quả biết trước, 0 token.
"""
from __future__ import annotations

import json
from fractions import Fraction

from app.simulation.geometry.radical import radical
from app.simulation.semantic_program.interpreter import SemanticProgramInterpreter
from app.simulation.semantic_program.scene3d import build_scene3d
from app.simulation.semantic_program.simulation_state import build_simulation_state
from app.simulation.semantic_program.validator import validate_semantic_program

#: Chương trình nhỏ nhất cho ra một khoảng cách VÔ TỈ.
#:
#: A(1,1,1) tới mặt (P): x+y+z = 0  ⇒  d² = 9/3 = 3  ⇒  d = √3.
#: Toạ độ nguyên, mặt qua ba điểm nguyên — không có gì tinh vi, và đó là điểm:
#: căn thức xuất hiện từ hình học THPT tầm thường nhất, không phải từ ca biên.
CHUONG_TRINH = {
    "spec_version": "1.0",
    "simulation_id": "geometry.radical_e2e",
    "title": "Khoảng cách từ một điểm tới mặt phẳng",
    "description": "Đo khoảng cách từ A tới mặt phẳng qua ba điểm.",
    "pedagogical_intent": "Cho thấy khoảng cách là một số đo dựng ra được.",
    "memory_declarations": [
        {"name": "A", "type": "point3", "initial_value": [1, 1, 1],
         "model_assumption": "điểm cần đo, chọn theo đề"},
        {"name": "M", "type": "point3", "initial_value": [0, 0, 0],
         "model_assumption": "gốc toạ độ"},
        {"name": "N", "type": "point3", "initial_value": [1, -1, 0],
         "model_assumption": "điểm thứ hai của mặt phẳng"},
        {"name": "K", "type": "point3", "initial_value": [1, 0, -1],
         "model_assumption": "điểm thứ ba của mặt phẳng"},
        {"name": "P", "type": "plane3"},
        {"name": "d", "type": "float"},
    ],
    "statements": [
        {"kind": "construct_plane", "target_var": "P", "through": ["M", "N", "K"],
         "label": "Dựng mặt phẳng (MNK)"},
        {"kind": "assign", "target_var": "d",
         "expr": {"kind": "measure", "quantity": "distance", "of": "A", "wrt": "P"},
         "label": "Đo khoảng cách từ A tới (MNK)"},
    ],
    "obligations": [],
}


def _chay():
    val = validate_semantic_program(CHUONG_TRINH)
    assert val.ok, val.error
    kq = SemanticProgramInterpreter().execute(val.spec)
    return val.spec, kq


def test_ket_qua_trong_bo_nho_la_CAN_THUC_chinh_xac():
    _, kq = _chay()
    assert kq.final_memory["d"] == radical(1, 3), f"đo ra {kq.final_memory['d']}"


def test_dai_luong_can_thuc_VAO_DUOC_canh_3d():
    """Bộ lọc `la_dai_luong_do` phải nhận `Radical`.

    Quên nhánh ấy thì `d = √3` tính đúng, chấm đúng, rồi **không hiện lên màn
    hình** — mô phỏng chạy xong mà học sinh không thấy đáp số.
    """
    spec, kq = _chay()
    state = build_simulation_state(spec, kq)
    so_do = [o for o in state["scene"]["objects"] if o["type"] == "quantity"]
    assert len(so_do) == 1, f"số đo không vào cảnh: {so_do}"


def test_JSON_mang_CA_cau_truc_lan_chuoi_hien_thi():
    """`exact` là NGUỒN, `value` là DẪN XUẤT — bộ chấm cần cấu trúc, người đọc
    cần chữ. Chỉ phát một trong hai là buộc bên kia phải đoán."""
    spec, kq = _chay()
    o = [x for x in build_simulation_state(spec, kq)["scene"]["objects"]
         if x["type"] == "quantity"][0]
    assert o["value"] == "√3"
    assert o["exact"] == {"kind": "radical", "coefficient": "1", "radicand": 3}


def test_scene3d_serialize_duoc_bang_json_dumps():
    """Biên đã hỏng MỘT LẦN với `Fraction`. Một kiểu số mới đi qua đúng chỗ ấy.

    `json.dumps` trên toàn cảnh, không trên riêng số đo: hỏng thật thì hỏng ở
    chỗ số đo nằm lẫn trong cấu trúc lớn, không ở chỗ ta gọi serialize nó.
    """
    spec, kq = _chay()
    canh = build_scene3d(build_simulation_state(spec, kq))
    chuoi = json.dumps(canh, ensure_ascii=False)
    assert "√3" in chuoi
    assert "radical" in chuoi
    # …và đọc ngược lại được, không mất mát.
    lai = json.loads(chuoi)
    assert isinstance(lai, dict)


def test_KHONG_co_so_thap_phan_nao_trong_canh():
    """Chốt cuối của `§18`: một `1.732…` trong cảnh nghĩa là float đã lẻn vào
    đường đúng đắn, và mọi phép so BẰNG phía sau mất nghĩa."""
    spec, kq = _chay()
    chuoi = json.dumps(build_scene3d(build_simulation_state(spec, kq)), ensure_ascii=False)
    import re

    # Bỏ qua `visual_transform` — đó là KHÔNG GIAN TRÌNH BÀY, được phép làm
    # tròn (xem `scene3d.BIEN_DOI_DONG_NHAT`). Hai miền khác bản chất, và trộn
    # chúng là mời sai số vào chỗ không được phép sai.
    canh = json.loads(chuoi)
    for o in canh.get("objects", []):
        o.pop("visual_transform", None)
    lai = json.dumps(canh, ensure_ascii=False)
    assert not re.search(r"\d\.\d", lai), "số thập phân lọt vào cảnh hình học"


def test_HOI_QUY_khoang_cach_huu_ti_van_ra_chuoi_phan_so():
    """`d = 2` phải ra `"2"`, không phải `"2√1"` — hợp đồng cũ không đổi."""
    ct = json.loads(json.dumps(CHUONG_TRINH))
    ct["memory_declarations"][0]["initial_value"] = [2, 0, 0]
    ct["statements"][1]["expr"] = {"kind": "measure", "quantity": "distance",
                                   "of": "A", "wrt": "M"}
    val = validate_semantic_program(ct)
    assert val.ok, val.error
    kq = SemanticProgramInterpreter().execute(val.spec)
    assert kq.final_memory["d"] == Fraction(2)
    o = [x for x in build_simulation_state(val.spec, kq)["scene"]["objects"]
         if x["type"] == "quantity"][0]
    assert o["value"] == "2"
    assert o["exact"] == {"kind": "rational", "value": "2"}
