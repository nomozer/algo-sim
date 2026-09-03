# -*- coding: utf-8 -*-
"""DỮ KIỆN ĐỀ VÔ HƯỚNG PHẢI NHÌN THẤY ĐƯỢC. **0 lượt gọi model.**

    `SCALAR_FACT_VISIBILITY`, 2026-09-04.

─── CỔNG KHÔNG THOẢ MÃN ĐƯỢC MÀ WAVE NÀY ĐÓNG ─────────────────────────────

`learner_surface` luật (2): mọi khai báo có `source_fact_id` phải nhìn thấy
được. Nhìn thấy được = có `visual_bindings` **hoặc** có mặt trên cảnh 3D.

Trong miền hình học cả ba lối đều bị bịt:

  ① thẻ văn phạm CẤM mô hình khai binding (*"không khai gì thêm để hiển thị"*);
  ② `grammar_card("hinh_hoc")` **không phơi** `visual_bindings` — mô hình không
     biết trường ấy tồn tại;
  ③ interpreter nạp `initial_value` NGUYÊN VĂN, nên `IA = 6` nằm trong bộ nhớ
     dưới dạng `str "6"`, mà `la_dai_luong_do` chỉ nhận `Fraction | Radical`.

⇒ **Không một dữ kiện đề vô hướng nào** qua được cổng, bất kể mô hình viết gì.
`ball_1` của probe V2: toán đúng tuyệt đối, `R = 6`, `V = 288π` đã kiểm,
`servable = False`.

─── VÌ SAO CHUẨN HOÁ CHỨ KHÔNG DẠY CỔNG ĐỌC CHUỖI ─────────────────────────

Cổng **đang nói thật**: `build_scene` dùng CHÍNH vị từ ấy để quyết cái gì thành
`quantity`, nên giá trị đó thật sự không có trên cảnh. Nới riêng cổng sẽ cho nó
xanh trong khi cảnh vẫn trống — một cổng fail-open.
"""
from __future__ import annotations

import json
from fractions import Fraction as F
from pathlib import Path

import pytest

from app.simulation.semantic_program.contract import SemanticProgramSpec
from app.simulation.semantic_program.geometry_exec import (
    chuan_hoa_dai_luong,
    la_dai_luong_do,
)
from app.simulation.semantic_program.obligations import Obligation
from app.simulation.semantic_program.request_contract import RequestContract
from app.simulation.semantic_program.route import verify_and_compile
from app.simulation.semantic_program.simulation_state import build_scene

PROBE = (Path(__file__).resolve().parents[3]
         / "docs/evaluation/geometry/curved-ergonomics-v2-run2"
         / "cases/ball_1/final.json")

_VB = {"containers": [], "pointers": [], "value_boxes": []}


def _md(n, t, iv=None, fact=None, ass=None) -> dict:
    d = {"name": n, "type": t}
    if iv is not None:
        d["initial_value"] = iv
    if fact:
        d["source_fact_id"] = fact
    if ass:
        d["model_assumption"] = ass
    return d


def _chuong_trinh_doan(vo_huong: dict | None) -> dict:
    """Hai điểm đề cho + đo khoảng cách. KHÔNG dùng hình cong — bản vá phải
    tổng quát, không phải một miếng vá riêng cho khối cầu."""
    decls = [
        _md("A", "point3", [0, 0, 0], "diem_a"),
        _md("B", "point3", [3, 0, 0], "diem_b", "Đặt B trên Ox để AB = 3"),
        _md("d", "float"),
    ]
    # Hình dạng hợp đồng lấy theo ca THẬT (`ball_1`): fact của một điểm mang
    # TÊN điểm, fact của một độ dài mang chính con số. Bịa một hình dạng khác
    # là đo một thứ đường sản phẩm không bao giờ gặp.
    if vo_huong:
        decls.insert(2, vo_huong)
    return {
        "spec_version": "1.0", "title": "Khoảng cách giữa hai điểm",
        "description": "Đo khoảng cách AB từ hai điểm đề cho.",
        "pedagogical_intent": "Thấy khoảng cách dẫn từ toạ độ.",
        "memory_declarations": decls,
        "statements": [{
            "kind": "assign", "target_var": "d",
            "expr": {"kind": "measure", "quantity": "distance",
                     "of": "A", "wrt": "B"}}],
        "visual_bindings": _VB,
    }


def _hop_dong(gt=None) -> RequestContract:
    """Hợp đồng hai điểm; `gt` khác `None` thì thêm mục độ dài mang ĐÚNG giá
    trị ấy — cổng xuất xứ đối chiếu `initial_value` với giá trị của mục, nên
    hai bên phải khớp y như đường sản phẩm."""
    facts = [
        {"fact_id": "diem_a", "label": "Điểm A", "values": ["A"],
         "provenance": "confirmed"},
        {"fact_id": "diem_b", "label": "Điểm B", "values": ["B"],
         "provenance": "confirmed"},
    ]
    if gt is not None:
        facts.append({"fact_id": "ab_len", "label": "Độ dài AB",
                      "values": [gt], "provenance": "confirmed"})
    return RequestContract(
        problem_text="Cho A(0;0;0) và B(3;0;0), biết AB = 3. Tính khoảng cách AB.",
        input_facts=facts,
        obligations=(Obligation(kind="distance", container="A",
                                params={"witness": "d", "wrt": "B"}),))


def _chay(spec_raw: dict, contract: RequestContract):
    return verify_and_compile(contract, SemanticProgramSpec.model_validate(spec_raw))


# ══ §20 · HỒI QUY CỔNG KHÔNG THOẢ MÃN ĐƯỢC — KHÔNG RIÊNG KHỐI CẦU ═════════
def test_S0_cong_KHONG_THOA_MAN_DUOC_da_dong():
    """Ca này ĐỎ dưới hành vi TRƯỚC wave: một dữ kiện đề vô hướng, khai đúng
    cách IR cho phép, KHÔNG `visual_bindings`, KHÔNG vật 3D giả — vẫn phải
    nhìn thấy được.

    Không dùng hình cong: nếu bản vá chỉ cứu khối cầu thì nó là một miếng vá,
    không phải một bản sửa.
    """
    kq = _chay(_chuong_trinh_doan(_md("AB_len", "float", 3, "ab_len")),
               _hop_dong(3))
    assert kq.executable, f"{kq.stage_reached}: {kq.reason}"
    assert kq.servable, f"vẫn không phục vụ được: {kq.reason}"
    assert la_dai_luong_do(kq.final_memory["AB_len"], "float")


# ══ S1 · S2 — SỐ NGUYÊN VÀ HỮU TỈ ════════════════════════════════════════
#: §10 — bốn dạng dữ kiện SGK hay gặp nhất, cộng hai dạng hữu tỉ.
#:
#: ⚠️ KHÔNG có biến thể `"6"` viết dạng chuỗi ở đây, và đó là quan sát chứ
#: không phải thiếu sót: cổng **grounding** chuẩn hoá `initial_value` của khai
#: báo nhưng KHÔNG chuẩn hoá giá trị của mục dữ kiện, nên `"6"` khai gặp `"6"`
#: trong hợp đồng vẫn báo lệch. Đó là hành vi CÓ TRƯỚC wave này (grounding đọc
#: `spec`, không đọc bộ nhớ) và không thuộc phạm vi bản vá — ghi lại để lần sau
#: không ai tưởng bản vá gây ra.
@pytest.mark.parametrize("iv,mong", [
    (6, F(6)), (13, F(13)), (8, F(8)), (2, F(2)),
    ("3/2", F(3, 2)), ("-7/3", F(-7, 3)),
])
def test_S1_S2_vo_huong_de_cho_thanh_dai_luong(iv, mong):
    kq = _chay(_chuong_trinh_doan(_md("gt", "float", iv, "ab_len")),
               _hop_dong(iv))
    assert kq.servable, f"{kq.stage_reached}: {kq.reason}"
    assert kq.final_memory["gt"] == mong
    assert la_dai_luong_do(kq.final_memory["gt"], "float")


def test_S2b_kieu_int_cung_di_qua():
    """`KIEU_DAI_LUONG` gồm cả `int`; đừng chỉ chữa `float`."""
    kq = _chay(_chuong_trinh_doan(_md("n", "int", 8, "ab_len")),
               _hop_dong(8))
    assert kq.servable and kq.final_memory["n"] == F(8)


# ══ S3 — BA_1 ĐI TRỌN ĐƯỜNG SẢN PHẨM ═════════════════════════════════════
def test_S3_ball_1_cua_probe_V2_nay_SERVABLE():
    """Chương trình + hợp đồng lấy NGUYÊN VĂN từ artifact `run2`.

    TRƯỚC: `postconditions_pass=True`, `learner_surface` từ chối,
    `servable=False`. Artifact giữ nguyên; đây là một lượt chấm lại tất định.
    """
    from app.simulation.geometry.radical import display

    r = json.loads(PROBE.read_text(encoding="utf-8"))
    kq = _chay(r["chuong_trinh"],
               RequestContract.model_validate(r["request_contract"]))
    assert kq.executable and kq.servable, f"{kq.stage_reached}: {kq.reason}"
    assert kq.stage_reached == "served"
    so = {display(v) for v in kq.final_memory.values()
          if type(v).__name__ in ("Fraction", "Radical")}
    assert {"6", "288π"} <= so, so


# ══ S4 — KHỐI ĐA DIỆN, KHÔNG DÍNH HÌNH CONG ══════════════════════════════
def test_S4_da_dien_voi_du_kien_vo_huong():
    """Tứ diện vuông cạnh 2, dữ kiện đề `a = 2`. `V = 4/3`."""
    raw = {
        "spec_version": "1.0", "title": "Thể tích tứ diện vuông",
        "description": "Dựng tứ diện từ bốn đỉnh đề cho rồi đo thể tích.",
        "pedagogical_intent": "Thấy thể tích dẫn từ toạ độ đỉnh.",
        "memory_declarations": [
            _md("O", "point3", [0, 0, 0], "tu_dien"),
            _md("A", "point3", [2, 0, 0], "tu_dien", "OA trên Ox, OA = 2"),
            _md("B", "point3", [0, 2, 0], "tu_dien", "OB trên Oy, OB = 2"),
            _md("C", "point3", [0, 0, 2], "tu_dien", "OC trên Oz, OC = 2"),
            _md("a", "float", 2, "canh_a"),
            _md("K", "solid"), _md("V", "float")],
        "statements": [
            {"kind": "construct_solid", "target_var": "K",
             "vertices": ["O", "A", "B", "C"],
             "faces": [[0, 1, 2], [0, 1, 3], [0, 2, 3], [1, 2, 3]]},
            {"kind": "assign", "target_var": "V",
             "expr": {"kind": "measure", "quantity": "volume", "of": "K"}}],
        "visual_bindings": _VB,
    }
    ct = RequestContract(
        problem_text="Cho tứ diện OABC có OA, OB, OC đôi một vuông góc và "
                     "OA = OB = OC = 2. Tính thể tích khối OABC.",
        input_facts=[
            {"fact_id": "tu_dien", "label": "Tứ diện OABC",
             "values": ["O", "A", "B", "C"], "provenance": "confirmed"},
            {"fact_id": "canh_a", "label": "Độ dài cạnh", "values": [2],
             "provenance": "confirmed"}],
        obligations=(Obligation(kind="volume", container="K",
                                params={"witness": "V"}),))
    kq = _chay(raw, ct)
    assert kq.executable and kq.servable, f"{kq.stage_reached}: {kq.reason}"
    assert kq.final_memory["V"] == F(4, 3)
    assert kq.final_memory["a"] == F(2)


# ══ S5 — VÔ HƯỚNG NỘI BỘ KHÔNG BỊ ĐÒI HIỆN ═══════════════════════════════
def test_S5_vo_huong_NOI_BO_khong_bi_doi_hien():
    """§6/§11 — bất biến nhắm tới là *dữ kiện đề vô hướng → nhìn thấy được*,
    KHÔNG phải *mọi vô hướng → bắt buộc hiện*. Luật (2) neo vào
    `source_fact_id`, và bản vá này không đụng vào đó.

    ⚠️ Một vô hướng nội bộ **không thể** mang `initial_value` — cổng xuất xứ
    đã bác *"có initial_value nhưng thiếu source_fact_id"* từ trước. Nên vô
    hướng nội bộ thật sự là loại **được TÍNH RA**, và ca này dùng đúng loại đó.
    """
    raw = _chuong_trinh_doan(_md("AB_len", "float", 3, "ab_len"))
    raw["memory_declarations"].append(_md("d2", "float"))
    raw["statements"].append({
        "kind": "assign", "target_var": "d2",
        "expr": {"kind": "measure", "quantity": "distance",
                 "of": "B", "wrt": "A"}})
    kq = _chay(raw, _hop_dong(3))
    assert kq.servable, f"{kq.stage_reached}: {kq.reason}"
    # `d2` không có `source_fact_id` ⇒ không bị luật (2) đòi; nó vẫn lên cảnh
    # như một đại lượng, nhưng đó là quyền của cảnh, không phải nghĩa vụ.
    assert "d2" in kq.final_memory


def test_S5b_chuan_hoa_la_chuyen_BIEU_DIEN_khong_phai_chuyen_HIEN():
    """Đơn vị: `chuan_hoa_dai_luong` chỉ nhìn KIỂU KHAI, không nhìn
    `source_fact_id`. Trộn hai câu ấy lại chính là nguồn của cả lỗi này."""
    hh = dict(mien_hinh_hoc=True)
    assert chuan_hoa_dai_luong("float", "5/2", **hh) == F(5, 2)
    assert chuan_hoa_dai_luong("int", 7, **hh) == F(7)
    # Kiểu KHÔNG phải đại lượng thì không đụng tới.
    assert chuan_hoa_dai_luong("point3", [1, 2, 3], **hh) == [1, 2, 3]
    assert chuan_hoa_dai_luong("bool", "6", **hh) == "6"
    assert chuan_hoa_dai_luong("float", None, **hh) is None
    # NGOÀI miền hình học: không đụng một giá trị nào — `int` ở IR Tin học là
    # CHỈ SỐ, và một chỉ số hữu tỉ không phải một chỉ số.
    assert chuan_hoa_dai_luong("int", 0, mien_hinh_hoc=False) == 0
    assert isinstance(chuan_hoa_dai_luong("int", 0, mien_hinh_hoc=False), int)


# ══ S6 — VÔ HƯỚNG HỎNG: FAIL CLOSED ══════════════════════════════════════
@pytest.mark.parametrize("xau", ["abc", "", "2x", "6.5.1"])
def test_S6_vo_huong_KHONG_DOC_DUOC_van_bi_tu_choi(xau):
    """§12 — không fail-open. Đọc không được thì giữ nguyên chuỗi, vẫn vô
    hình, và cổng vẫn từ chối. Ép nó thành 0 là biến 'không đọc được' thành
    một con số."""
    # Mục dữ kiện mang ĐÚNG chuỗi ấy, nên cổng xuất xứ cho qua và ca đi tới
    # `learner_surface` — đúng cổng ta muốn đo. Để lệch giá trị thì nó chết ở
    # grounding, và phép thử không còn nói gì về cổng bề mặt.
    kq = _chay(_chuong_trinh_doan(_md("xau", "float", xau, "ab_len")),
               _hop_dong(xau))
    assert not kq.servable, f"chuỗi hỏng {xau!r} lọt qua cổng"
    assert isinstance((kq.final_memory or {}).get("xau", ""), str)


def test_S6b_bool_khong_bi_nuot_thanh_so():
    """`bool` là subclass của `int`; một cờ trôi vào chỗ số đo là lỗi im lặng
    nhất."""
    assert chuan_hoa_dai_luong("float", True, mien_hinh_hoc=True) is True
    assert chuan_hoa_dai_luong("int", False, mien_hinh_hoc=True) is False


# ══ S7 — KHÔNG RÒ ĐỊNH DANH MÁY LÊN BỀ MẶT HỌC SINH ══════════════════════
def test_S7_nhan_hien_thi_KHONG_phai_dinh_danh_may():
    """§14 — học sinh không được nhìn thấy `AB_len_raw_id`."""
    spec_raw = _chuong_trinh_doan(_md("AB_len_raw_id", "float", 3, "ab_len"))
    kq = _chay(spec_raw, _hop_dong(3))
    assert kq.servable
    canh = build_scene(SemanticProgramSpec.model_validate(spec_raw),
                       kq.final_memory)
    o = next(x for x in canh["objects"] if x["id"] == "AB_len_raw_id")
    assert o["label"] and o["label"] != "AB_len_raw_id"
    assert "AB_len_raw_id" not in o["label"]


# ══ S8 — KHÔNG ĐÒI `visual_bindings` ═════════════════════════════════════
def test_S8_khong_ca_nao_can_visual_bindings():
    """`GEOMETRY_MODEL_AUTHORED_VISUAL_BINDINGS_REQUIRED = NO`. Và thẻ hình
    học vẫn KHÔNG phơi trường ấy — bản vá không được lén mở nó ra."""
    from app.simulation.semantic_program.grammar_card import grammar_card

    spec_raw = _chuong_trinh_doan(_md("AB_len", "float", 3, "ab_len"))
    assert spec_raw["visual_bindings"] == _VB, "ca thử phải KHÔNG có binding"
    assert _chay(spec_raw, _hop_dong(3)).servable
    assert "visual_bindings" not in grammar_card("hinh_hoc")


# ══ S9 — KHÔNG DỰNG VẬT 3D GIẢ CHO MỘT VÔ HƯỚNG ══════════════════════════
def test_S9_vo_huong_len_canh_nhu_DAI_LUONG_khong_phai_vat_the():
    """`SCALAR_FAKE_3D_OBJECTS = 0` — `SA = 6` không được thành một điểm hay
    một lưới trên cảnh."""
    spec_raw = _chuong_trinh_doan(_md("AB_len", "float", 3, "ab_len"))
    kq = _chay(spec_raw, _hop_dong(3))
    canh = build_scene(SemanticProgramSpec.model_validate(spec_raw),
                       kq.final_memory)
    o = next(x for x in canh["objects"] if x["id"] == "AB_len")
    assert o["type"] == "quantity", o
    assert "xyz" not in o and "vertices" not in o and "faces" not in o, o


# ══ S10 — R0 KHÔNG NHÚC NHÍCH ════════════════════════════════════════════
def test_S10_diem_BIA_van_bi_bac():
    """Bản vá không được thành cửa sau cho toạ độ bịa: một vô hướng hiện được
    KHÔNG làm một điểm vô căn cứ trở nên có căn cứ."""
    from app.simulation.semantic_program.grounding_gate import check_grounding

    spec_raw = _chuong_trinh_doan(_md("AB_len", "float", 3, "ab_len"))
    spec_raw["memory_declarations"].append(
        _md("P_bia", "point3", [9, 9, 9]))          # không nguồn, không giả thiết
    g = check_grounding(_hop_dong(3),
                        SemanticProgramSpec.model_validate(spec_raw))
    assert not g.ok and any("P_bia" in x for x in g.unresolved)


def test_S10b_vo_huong_bia_cung_bi_bac():
    """Chiều còn lại: một vô hướng KHAI có `source_fact_id` trỏ vào mục KHÔNG
    tồn tại trong hợp đồng vẫn phải bị bác."""
    from app.simulation.semantic_program.grounding_gate import check_grounding

    spec_raw = _chuong_trinh_doan(_md("x", "float", 42, "khong_co_muc_nay"))
    g = check_grounding(_hop_dong(), SemanticProgramSpec.model_validate(spec_raw))
    assert not g.ok


# ══ MỘT NGUỒN SỰ THẬT ════════════════════════════════════════════════════
def test_hai_nguoi_doc_dung_CHUNG_mot_vi_tu():
    """`build_scene` và `learner_surface` phải cùng hỏi `la_dai_luong_do`.
    Hai bản `isinstance` song song sẽ trôi khỏi nhau đúng vào ngày thêm một
    kiểu số mới — và khi ấy cổng nói 'có trên hình' còn cảnh không vẽ."""
    import inspect

    from app.simulation.semantic_program import learner_surface, simulation_state

    for mod in (learner_surface, simulation_state):
        assert "la_dai_luong_do" in inspect.getsource(mod), mod.__name__


def test_kieu_khai_KHONG_bi_doi_boi_chuan_hoa():
    """§5 — chuẩn hoá biểu diễn runtime, KHÔNG đổi kiểu ngữ nghĩa đã khai."""
    spec_raw = _chuong_trinh_doan(_md("AB_len", "float", 3, "ab_len"))
    spec = SemanticProgramSpec.model_validate(spec_raw)
    assert {d.name: d.type for d in spec.memory_declarations}["AB_len"] == "float"
    kq = _chay(spec_raw, _hop_dong(3))
    assert isinstance(kq.final_memory["AB_len"], F)
