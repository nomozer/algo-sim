# -*- coding: utf-8 -*-
"""BIÊN VẬN CHUYỂN — envelope thành công LUÔN `json.dumps` được. **0 API call.**

─── BUG NÓ KHOÁ ──────────────────────────────────────────────────────────

GENERALIZATION MATRIX (2026-08-31) phơi ra: `visual_adapter` đặt THẲNG giá trị
bộ nhớ vào `value_box.value` — `Vec3` với biến hình học, `Fraction`/`Radical`
với số đo. `main.py` serialize envelope để GHI CACHE, tức **sau khi mọi cổng đã
nói PASS**. Học sinh đợi hết một lượt pipeline rồi nhận 500 không địa chỉ.

Nặng hơn vẻ ngoài: prompt DẠY mô hình gắn `visual_bindings` cho witness của mỗi
nghĩa vụ, nên một chương trình hình học **đúng** gần như chắc chắn rơi vào đây.

─── BỐN TẦNG KIỂM, CỐ Ý KHÔNG GỘP ────────────────────────────────────────

  ① `transport.py` một mình     — bảng kiểu, fail-closed, lồng nhau
  ② adapter → envelope          — chỗ bug thật sự sống
  ③ đường CACHE                 — tái dựng đúng thao tác từng 500
  ④ replay artifact matrix      — chương trình THẬT mô hình đã sinh

Chỉ có ① thì xanh mà sản phẩm vẫn vỡ: bug không nằm ở serializer, nó nằm ở chỗ
KHÔNG AI GỌI serializer.
"""
from __future__ import annotations

import json
from fractions import Fraction
from pathlib import Path

import pytest

from app.simulation.geometry.exact import Line3, Plane3, Vec3
from app.simulation.geometry.radical import radical
from app.simulation.semantic_program.interpreter import SemanticProgramInterpreter
from app.simulation.semantic_program.pipeline_adapter import (
    compile_semantic_program_to_envelope,
)
from app.simulation.semantic_program.transport import (
    ERR_KIEU_LA,
    TransportTypeError,
    check_envelope_transport,
    to_display,
    to_transport,
    transport_pair,
)
from app.simulation.semantic_program.validator import validate_semantic_program

V = Vec3.of
F = Fraction


# ══ ① THẨM QUYỀN SERIALIZE ══════════════════════════════════════════════
@pytest.mark.parametrize("x", [None, True, False, 0, 7, -3, 1.5, "", "abc"])
def test_JSON_native_di_thang_khong_boc(x):
    """Một `int` trong `value_box` của bài Tin học phải VẪN là `int`.

    Bọc nó thành dict "cho đồng bộ" là phá hợp đồng frontend đang có, và thêm
    một hình dạng thứ hai cho cùng một thứ.
    """
    assert to_transport(x) is x or to_transport(x) == x
    assert transport_pair(x) == (x, None)


def test_fraction_giu_CHINH_XAC_khong_thanh_float():
    d = to_transport(F(3, 5))
    assert d["kind"] == "rational" and d["value"] == "3/5"
    assert d["display"] == "3/5"
    assert "0.6" not in json.dumps(d)


def test_radical_giu_CAU_TRUC():
    d = to_transport(radical(F(3, 5), 2))
    assert d["kind"] == "radical"
    assert d["coefficient"] == "3/5" and d["radicand"] == 2
    assert d["display"] == "3√2/5"


def test_vec3_thanh_CAU_TRUC_thanh_phan_CHINH_XAC():
    d = to_transport(V(F(1, 2), 3, F(-4, 5)))
    assert d["kind"] == "vec3"
    assert d["components"] == ["1/2", "3", "-4/5"], "toạ độ mất tính chính xác"
    # KHÔNG được là ba số float — đó là thứ phân biệt hệ này với bộ vẽ hình.
    assert all(isinstance(c, str) for c in d["components"])


def test_line3_va_plane3_co_duong_ra():
    ln = to_transport(Line3.through(V(0, 0, 0), V(1, 0, 0)))
    pl = to_transport(Plane3(V(0, 0, 0), V(0, 0, 1)))
    assert ln["kind"] == "line3" and pl["kind"] == "plane3"
    json.dumps([ln, pl])


def test_LONG_NHAU_duoc_chuyen_het():
    """§9 — không chỉ tầng ngoài cùng."""
    x = {"a": [{"b": (F(1, 2), radical(1, 2))}, [V(1, 2, 3)]]}
    d = to_transport(x)
    json.dumps(d)          # chết ở đây nghĩa là còn sót một tầng
    assert d["a"][0]["b"][0]["kind"] == "rational"
    assert d["a"][0]["b"][1]["kind"] == "radical"
    assert d["a"][1][0]["kind"] == "vec3"


def test_khoa_dict_ve_CHUOI():
    """JSON không có khoá không-chuỗi — một khoá `Fraction` chết y như giá trị."""
    d = to_transport({F(1, 2): 1})
    json.dumps(d)
    assert list(d) == ["1/2"]


class _La:
    pass


def test_kieu_LA_thi_FAIL_CLOSED_khong_roi_ve_str():
    """`str(value)` che mất hợp đồng kiểu: nó biến một lỗi thiết kế thành một
    chuỗi trông hợp lệ, và lần sau không ai biết dữ liệu mất hình dạng ở đâu."""
    for f in (to_transport, to_display):
        with pytest.raises(TransportTypeError) as e:
            f(_La())
        assert ERR_KIEU_LA in str(e.value)
        assert "_La" in str(e.value), "thông điệp không nói kiểu nào thiếu"


def test_display_la_SCALAR_cho_moi_kieu_runtime():
    """Frontend làm `String(v)` trên `value_box.value` và từng `items[i]` — một
    dict ở đó in ra `[object Object]`."""
    for x, mong in [(F(3, 5), "3/5"), (radical(F(1, 2), 2), "√2/2"),
                    (V(1, 2, 3), "(1, 2, 3)")]:
        assert to_display(x) == mong
        assert isinstance(to_display(x), str)


# ══ ② ADAPTER → ENVELOPE (chỗ bug thật sự sống) ═════════════════════════
def _chuong_trinh(binding_kieu: str = "point") -> dict:
    """Chương trình hình học có `value_box` gắn vào ĐÚNG thứ từng làm vỡ."""
    ct = {
        "spec_version": "1.0", "simulation_id": "geometry.transport",
        "title": "Đo khoảng cách rồi hiện lên màn hình",
        "description": "Dựng mặt phẳng, đo khoảng cách, gắn hộp giá trị.",
        "pedagogical_intent": "Cho thấy số đo phải hiện ra được.",
        "memory_declarations": [
            {"name": "P", "type": "plane3"}, {"name": "d", "type": "float"},
        ],
        "statements": [
            {"kind": "declare_point", "target_var": "A", "at": [1, 1, 1],
             "model_assumption": "điểm cần đo"},
            {"kind": "declare_point", "target_var": "M", "at": [0, 0, 0],
             "model_assumption": "gốc"},
            {"kind": "declare_point", "target_var": "N", "at": [1, -1, 0],
             "model_assumption": "điểm thứ hai"},
            {"kind": "declare_point", "target_var": "K", "at": [1, 0, -1],
             "model_assumption": "điểm thứ ba"},
            {"kind": "construct_plane", "target_var": "P",
             "through": ["M", "N", "K"]},
            {"kind": "assign", "target_var": "d",
             "expr": {"kind": "measure", "quantity": "distance",
                      "of": "A", "wrt": "P"}},
        ],
        "visual_bindings": {"containers": [], "pointers": [], "value_boxes": []},
    }
    hop = {"point": {"box_id": "b_A", "var_ref": "A", "label": "A"},
           "so_do": {"box_id": "b_d", "var_ref": "d", "label": "d"}}
    ct["visual_bindings"]["value_boxes"] = [hop[binding_kieu]]
    return ct


@pytest.mark.parametrize("kieu, mong_kind", [
    ("point", "vec3"),          # `Vec3` — biến hình học
    ("so_do", "radical"),       # `Radical` — số đo vô tỉ (√3)
])
def test_envelope_THAT_serialize_duoc(kieu, mong_kind):
    """Ca từng 500. Dựng envelope bằng đúng đường sản phẩm rồi `json.dumps`."""
    v = validate_semantic_program(_chuong_trinh(kieu))
    assert v.ok, v.error
    env = compile_semantic_program_to_envelope(v.spec)
    json.dumps(env, ensure_ascii=False)      # ← dòng từng ném TypeError

    hop = [o for f in env["config"]["frames"] for o in f["objects"]
           if o["type"] == "value_box"]
    assert hop, "không có hộp giá trị nào — ca kiểm không chạm được chỗ cần chạm"
    cuoi = hop[-1]
    assert isinstance(cuoi["value"], (str, int, float)), \
        "`value` phải là SCALAR — frontend làm String(v)"
    assert cuoi.get("exact", {}).get("kind") == mong_kind, \
        "cấu trúc chính xác không đi kèm"


def test_gia_tri_JSON_native_KHONG_moc_them_exact():
    """Bài Tin học: `value_box` gắn một `int` thì không được đẻ ra `exact`."""
    ct = {
        "spec_version": "1.0", "simulation_id": "algo.x",
        "title": "Đếm phần tử", "description": "Đếm rồi hiện số.",
        "pedagogical_intent": "Cho thấy biến đếm đổi giá trị.",
        "memory_declarations": [{"name": "m", "type": "int", "initial_value": 3}],
        "statements": [{"kind": "assign", "target_var": "m",
                        "expr": {"kind": "literal", "value": 5}}],
        "visual_bindings": {"containers": [], "pointers": [],
                            "value_boxes": [{"box_id": "b", "var_ref": "m",
                                             "label": "m"}]},
    }
    v = validate_semantic_program(ct)
    assert v.ok, v.error
    env = compile_semantic_program_to_envelope(v.spec)
    hop = [o for f in env["config"]["frames"] for o in f["objects"]
           if o["type"] == "value_box"][-1]
    assert hop["value"] == 5 and "exact" not in hop


# ══ CỔNG ════════════════════════════════════════════════════════════════
def test_cong_bat_duoc_envelope_ban():
    assert check_envelope_transport({"a": 1, "b": ["x", None]}) is None
    loi = check_envelope_transport({"v": Fraction(1, 2)})
    assert loi is not None and ERR_KIEU_LA in loi


def test_route_co_goi_cong_truoc_learner_surface():
    """Thứ tự quan trọng: vận chuyển hỏng thì bề mặt học sinh vô nghĩa."""
    from tests.source_scan import con_du, than_ma

    src = than_ma(
        Path(__file__).resolve().parents[2] / "app" / "simulation"
        / "semantic_program" / "route.py")
    assert con_du(src, "check_envelope_transport", 2000)
    assert (src.index("check_envelope_transport(envelope)")
            < src.index("check_learner_surface(contract")), \
        "cổng vận chuyển phải chạy TRƯỚC cổng bề mặt"


# ══ ③ ĐƯỜNG CACHE — tái dựng đúng thao tác từng 500 ═════════════════════
def test_duong_CACHE_ghi_va_doc_lai_duoc():
    """`main.py` làm `json.dumps(envelope)` để ghi cache rồi `json.loads` khi
    đọc lại. Kiểm cả hai chiều, không mock mất bước gây lỗi."""
    v = validate_semantic_program(_chuong_trinh("so_do"))
    env = compile_semantic_program_to_envelope(v.spec)

    blob = json.dumps(env, ensure_ascii=False)        # ghi cache
    lai = json.loads(blob)                            # đọc lại
    assert lai["config"]["title"] == env["config"]["title"]
    hop = [o for f in lai["config"]["frames"] for o in f["objects"]
           if o["type"] == "value_box"][-1]
    assert hop["exact"]["kind"] == "radical"
    assert hop["exact"]["radicand"] == 3               # d = √3
    assert hop["value"] == "√3"


# ══ ④ REPLAY ARTIFACT MATRIX — chương trình THẬT mô hình đã sinh ════════
_MATRIX = (Path(__file__).resolve().parents[3] / "docs" / "evaluation"
           / "geometry" / "generalization-matrix" / "matrix.json")


def _chuong_trinh_chay_duoc() -> list[tuple[str, dict]]:
    if not _MATRIX.exists():
        return []
    d = json.loads(_MATRIX.read_text(encoding="utf-8"))
    ra = []
    for c in d["cases"]:
        for raw in reversed(c.get("programs") or []):
            try:
                v = validate_semantic_program(json.loads(raw))
            except Exception:  # noqa: BLE001
                continue
            if v.ok:
                ra.append((c["case_id"], json.loads(raw)))
                break
    return ra


def test_MOI_chuong_trinh_AI_sinh_deu_serialize_duoc():
    """§12 — replay artifact, 0 token. Đây là ca gần sản phẩm nhất: chương
    trình do mô hình thật viết, không phải fixture ta tự dựng cho vừa."""
    ct = _chuong_trinh_chay_duoc()
    assert len(ct) >= 5, f"chỉ replay được {len(ct)} chương trình — artifact hỏng?"
    hong = []
    for cid, payload in ct:
        v = validate_semantic_program(payload)
        try:
            SemanticProgramInterpreter().execute(v.spec)
        except Exception:  # noqa: BLE001
            continue        # không chạy được là chuyện của matrix, không phải của biên này
        try:
            env = compile_semantic_program_to_envelope(v.spec)
            json.dumps(env, ensure_ascii=False)
        except Exception as e:  # noqa: BLE001
            hong.append(f"{cid}: {type(e).__name__}: {e}")
    assert not hong, "envelope không serialize được:\n" + "\n".join(hong)
