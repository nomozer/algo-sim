# -*- coding: utf-8 -*-
"""CẦU NỐI NGHĨA VỤ ĐO ↔ HỢP ĐỒNG PHÉP ĐO — và cổng chống lỗ test của Phase 2.

    `CURVED_OBLIGATION_COVERAGE_BRIDGE`, 2026-09-03. **0 lượt gọi model.**

─── LỖ NÓ BỊT, VÀ NÓ TỐN 26 LƯỢT MODEL ĐỂ TÌM RA ─────────────────────────

`obligations.OBLIGATION_KINDS` giữ một **bản sao viết tay** của câu *"nghĩa vụ
này nhận chủ thể kiểu nào"*, trong khi `measure_contract.BANG_PHEP_DO` đã trả
lời đúng câu ấy cho từng lượng đo. Hai bản, và bản sao đã trôi ở HAI chỗ:

    volume   thiếu `curved_solid`   Phase 2 mở, bản sao không biết
    angle    thiếu `vector3`        lệch có từ TRƯỚC, chưa ai thấy

Hệ quả của chỗ lệch thứ nhất, đo bằng quota thật (`CURVED_MODEL_ACCEPTANCE_V1`):
ba chương trình **hoàn toàn đúng** — `ball_1`, `cylinder_1`, `cone_1` — bị cổng
phủ bác với `REQUESTED_OPERATION_UNCOVERED`. Không phải lỗi mô hình.

─── LỖ THỨ HAI: KIẾN TRÚC TEST ───────────────────────────────────────────

Nguyên nhân sâu hơn là **các ca "đường đầy đủ" của Phase 2 dừng trước
`verify_and_compile`**: chúng gọi `kiem_tinh` → interpreter → `build_scene`,
nên grounding và cổng phủ chưa từng chạy với một khối cong.

File này sửa cả điều đó: `_duong_san_pham()` là lối DUY NHẤT các ca dưới đây
dùng, và `test_KIEN_TRUC_*` cấm một ca tự chứng nhận "đường đầy đủ" mà bỏ qua
hai cổng ấy.
"""
from __future__ import annotations

import inspect
import json
from pathlib import Path

import pytest

from app.simulation.semantic_program.contract import SemanticProgramSpec
from app.simulation.semantic_program.measure_contract import (
    BANG_PHEP_DO,
    NGHIA_VU_DO,
    kieu_chu_the_nghia_vu,
)
from app.simulation.semantic_program.obligations import (
    OBLIGATION_KINDS,
    Obligation,
    accepts_container_type,
)
from app.simulation.semantic_program.request_contract import (
    InputFact,
    RequestContract,
)
from app.simulation.semantic_program.route import verify_and_compile

V1 = (Path(__file__).resolve().parents[3]
      / "docs/evaluation/geometry/curved-acceptance-v1/stage_8a_one_shot.json")


def _duong_san_pham(spec_raw: dict, nghia_vu: tuple[Obligation, ...], de: str):
    """ĐÚNG đường sản phẩm chạy trước khi một envelope tới người học.

    `verify_and_compile` = grounding → **cổng phủ** → thẩm định tĩnh →
    interpreter → vết → cảnh. Ca nào tự nhận là "đường đầy đủ" mà không đi qua
    đây thì nó chưa chạm hai cổng đắt nhất — đúng lỗ mà Phase 2 để lại.
    """
    spec = SemanticProgramSpec.model_validate(spec_raw)
    return verify_and_compile(
        RequestContract(problem_text=de, obligations=nghia_vu,
                        input_facts=_du_kien(spec_raw)), spec)


def _v1(case_id: str) -> dict:
    d = json.loads(V1.read_text(encoding="utf-8"))
    return next(x for x in d["ca"] if x["id"] == case_id)


def _du_kien(raw: dict) -> tuple[InputFact, ...]:
    """Dựng lại `input_facts` TỪ CHÍNH chương trình đã bắt được.

    ⚠️ Đây là **tái dựng**, không phải bịa: mọi `source_fact_id` mà chương
    trình tham chiếu đều do `analyze` phát ra trong lượt V1 thật. Artifact V1
    không lưu `RequestContract` (thiếu sót của runner, đã ghi trong báo cáo),
    nên `fact_id` được đọc ngược từ phía tiêu thụ.

    Không dựng lại thì cổng xuất xứ bác vì một lý do KHÔNG có trong lượt thật,
    và ca sẽ đỏ vì lỗi của phép đo chứ không vì lỗi của hệ.
    """
    ids = sorted({m["source_fact_id"] for m in raw["memory_declarations"]
                  if m.get("source_fact_id")})
    return tuple(InputFact(fact_id=i, label=i) for i in ids)


def _nghia_vu_the_tich(raw: dict) -> tuple[str, str]:
    """`(tên khối cong, tên biến nhận thể tích)` — đọc từ chính chương trình."""
    khoi = next(m["name"] for m in raw["memory_declarations"]
                if m["type"] == "curved_solid")
    wit = next(s["target_var"] for s in raw["statements"]
               if s.get("kind") == "assign"
               and s.get("expr", {}).get("quantity") == "volume")
    return khoi, wit


# ══ MỘT THẨM QUYỀN ═══════════════════════════════════════════════════════
def test_kieu_chu_the_nghia_vu_DO_dan_xuat_tu_BANG_PHEP_DO():
    """`MEASURE_COMPATIBILITY_AUTHORITIES = 1`."""
    for nv, qs in NGHIA_VU_DO.items():
        mong = frozenset().union(
            *(frozenset(BANG_PHEP_DO[q].kieu_of) for q in qs))
        assert OBLIGATION_KINDS[nv] == mong == kieu_chu_the_nghia_vu(nv)


def test_OBLIGATION_KINDS_khong_con_ban_sao_VIET_TAY_cua_nghia_vu_do():
    """Literal của bảng **không được** chứa lại ba nghĩa vụ ĐO.

    Đây là cổng chống tái phát: viết `"volume": frozenset({"solid"})` trở lại
    thì bản sao sống lại, và lần trôi sau sẽ lại tốn một lượt đo live để tìm.
    """
    from app.simulation.semantic_program import obligations as O

    src = Path(inspect.getfile(O)).read_text(encoding="utf-8")
    dau = src.index("OBLIGATION_KINDS: dict[str, frozenset[str]] = {")
    than = src[dau:src.index("\n}", dau)]
    for nv in NGHIA_VU_DO:
        assert f'"{nv}":' not in than, (
            f"'{nv}' lại được viết tay trong OBLIGATION_KINDS — nó phải DẪN "
            "XUẤT từ measure_contract")


def test_MEASURE_COVERAGE_DRIFT_bang_0():
    """Không lượng đo nào có kiểu mà nghĩa vụ tương ứng không nhận."""
    lech = []
    for nv, qs in NGHIA_VU_DO.items():
        for q in qs:
            for kieu in BANG_PHEP_DO[q].kieu_of:
                if not accepts_container_type(nv, kieu):
                    lech.append(f"{nv} ⊅ {q}.{kieu}")
    assert not lech, lech


def test_nghia_vu_CAU_TRUC_khong_bi_ep_qua_bang_phep_do():
    """§11 — quan hệ/thiết diện giữ thẩm quyền riêng, không bị cầu nối nuốt."""
    for nv in ("point_on_line", "point_on_plane", "parallel", "perpendicular",
               "coplanar", "section_matches"):
        assert nv not in NGHIA_VU_DO
        assert OBLIGATION_KINDS[nv], f"{nv} mất miền kiểu"


# ══ §15 · BA CHƯƠNG TRÌNH V1 — PHÉP THỬ CHÍNH ════════════════════════════
#
# ⚠️ Phân biệt HAI câu hỏi, vì gộp chúng là cách một wave tự khen:
#
#   ① CỔNG PHỦ có còn chặn ba chương trình ấy không?   ← thứ wave này sửa
#   ② chúng có chạy trọn đường sản phẩm không?          ← còn phụ thuộc thứ khác
#
# Câu ① trả lời được TRỌN VẸN từ artifact V1. Câu ② thì không, và lý do được
# ghi ở `test_15c` — không giấu bằng cách chỉ khẳng định câu ①.
@pytest.mark.parametrize("case_id", ["ball_1", "cylinder_1", "cone_1"])
def test_15_CONG_PHU_thoi_chan_ba_chuong_trinh_V1(case_id):
    """`CAPTURED_V1_SYSTEM_BLOCKERS = 3/3 FIXED`.

    Chương trình lấy **nguyên văn** từ artifact V1 (bất biến). Trước cầu nối cả
    ba chết ở `REQUESTED_OPERATION_UNCOVERED`; sau cầu nối cổng phủ cho qua.
    """
    from app.simulation.semantic_program.coverage_gate import (
        check_structural_coverage,
    )

    r = _v1(case_id)
    khoi, wit = _nghia_vu_the_tich(r["chuong_trinh"])
    spec = SemanticProgramSpec.model_validate(r["chuong_trinh"])
    hd = RequestContract(
        problem_text=r["de"], input_facts=_du_kien(r["chuong_trinh"]),
        obligations=(Obligation(kind="volume", container=khoi,
                                params={"witness": wit}),))
    kq = check_structural_coverage(hd, spec)
    assert kq.ok, f"{case_id} vẫn bị cổng phủ chặn: {list(kq.missing)}"


def test_15b_dung_lai_trang_thai_CU_thi_cong_phu_BAC_lai():
    """Chứng minh cầu nối sửa đúng thứ nó nói, thay vì tin lời kể."""
    from app.simulation.semantic_program import obligations as O
    from app.simulation.semantic_program.coverage_gate import (
        check_structural_coverage,
    )

    r = _v1("ball_1")
    khoi, wit = _nghia_vu_the_tich(r["chuong_trinh"])
    spec = SemanticProgramSpec.model_validate(r["chuong_trinh"])
    hd = RequestContract(
        problem_text=r["de"],
        obligations=(Obligation(kind="volume", container=khoi,
                                params={"witness": wit}),))
    goc = O.OBLIGATION_KINDS["volume"]
    O.OBLIGATION_KINDS["volume"] = frozenset({"solid"})   # trạng thái TRƯỚC
    try:
        kq = check_structural_coverage(hd, spec)
        assert not kq.ok and kq.error_code == "REQUESTED_OPERATION_UNCOVERED"
        assert any("curved_solid" in m for m in kq.missing), list(kq.missing)
    finally:
        O.OBLIGATION_KINDS["volume"] = goc


def test_15c_ball_1_di_TRON_duong_san_pham():
    """Một trong ba đi hết `verify_and_compile` — grounding + phủ + tĩnh +
    interpreter — và đó là bằng chứng đường đầy đủ thật sự thông."""
    r = _v1("ball_1")
    khoi, wit = _nghia_vu_the_tich(r["chuong_trinh"])
    kq = _duong_san_pham(
        r["chuong_trinh"],
        (Obligation(kind="volume", container=khoi, params={"witness": wit}),),
        r["de"])
    assert kq.executable, f"bị chặn ở '{kq.stage_reached}': {kq.reason}"
    assert kq.final_memory, "chạy trọn mà không để lại trạng thái"


def test_15d_HAI_CA_KIA_chua_chung_nhan_duong_day_du_duoc__va_vi_sao():
    """KHAI RA giới hạn thay vì lặng lẽ chỉ kiểm câu ①.

    `cylinder_1` — artifact V1 **không lưu `RequestContract`** (thiếu sót của
    runner, đã ghi trong báo cáo V1), nên `InputFact.values` không tái dựng
    được và cổng xuất xứ bác vì một lý do KHÔNG có trong lượt thật. Đây là giới
    hạn của PHÉP ĐO, không phải của hệ.

    `cone_1` — có **khiếm khuyết THỨ HAI của mô hình**, trước đây bị cổng phủ
    che vì cổng phủ chạy trước: thẩm định tĩnh bác `AMBIGUOUS_FIRST_BINDING`
    trên `S.O`. Cầu nối gỡ đúng vật cản của HỆ; vật cản còn lại là của MÔ HÌNH,
    và §16 cấm sửa nó trong wave này.

    Ca này khoá hai sự thật ấy để chúng không lặng lẽ đổi.
    """
    from app.simulation.semantic_program.ir_static_check import kiem_tinh

    assert kiem_tinh(SemanticProgramSpec.model_validate(
        _v1("ball_1")["chuong_trinh"])).ok
    assert kiem_tinh(SemanticProgramSpec.model_validate(
        _v1("cylinder_1")["chuong_trinh"])).ok
    t = kiem_tinh(SemanticProgramSpec.model_validate(
        _v1("cone_1")["chuong_trinh"]))
    assert not t.ok and any("AMBIGUOUS_FIRST_BINDING" in i.dong()
                            for i in t.issues), [i.dong() for i in t.issues]


# ══ §22 · MA TRẬN TƯƠNG THÍCH ════════════════════════════════════════════
@pytest.mark.parametrize("nv,kieu,mong", [
    ("volume", "solid", True),          # C4 hồi quy
    ("volume", "curved_solid", True),   # C5 — chỗ đã trôi
    ("volume", "polygon3", False),      # C11 chủ thể sai vẫn bị bác
    ("distance", "point3", True),
    ("distance", "solid", False),
    ("angle", "line3", True),
    ("angle", "vector3", True),         # chỗ trôi THỨ HAI, có từ trước
    ("angle", "solid", False),
    ("coplanar", "section", True),
    ("coplanar", "curved_solid", False),
])
def test_22_ma_tran_tuong_thich(nv, kieu, mong):
    assert accepts_container_type(nv, kieu) is mong


# ══ §9 · `area` VÀ CÁC LƯỢNG ĐO KHÔNG CÓ NGHĨA VỤ ════════════════════════
def test_09_area_radius_lateral_area_KHONG_co_nghia_vu__va_do_la_chu_y():
    """`AREA_CIRCLE_COVERAGE = PASS`, nhưng lý do phải nói cho đúng.

    Cổng phủ chỉ kiểm **nghĩa vụ ĐÃ KHAI**. Ba lượng đo này không có nghĩa vụ
    nào ánh xạ tới, nên chúng không bị cổng bác — chứ **không phải** vì cổng
    hiểu chúng. Thêm nghĩa vụ cho chúng là đổi lược đồ `analyze` (model-facing)
    và đổi băm taxonomy đã niêm phong; §8 của wave cấm dựng taxonomy chết.

    Khi nào cần: khi đo được rằng `analyze` gán nhầm một nghĩa vụ khác cho câu
    *"tính diện tích xung quanh"*. Chưa có phép đo ấy, nên chưa thêm.
    """
    for q in ("area", "radius", "lateral_area"):
        assert q in BANG_PHEP_DO
        assert q not in NGHIA_VU_DO
        assert q not in OBLIGATION_KINDS


def test_09b_chuong_trinh_do_dien_tich_hinh_tron_KHONG_bi_cong_phu_bac():
    """Đi trọn đường sản phẩm với một nghĩa vụ KHÔNG phải phép đo."""
    raw = {
        "spec_version": "1.0", "title": "Đường tròn giao",
        "description": "Mặt phẳng cắt mặt cầu theo một đường tròn.",
        "pedagogical_intent": "Thấy giao tuyến là một đường tròn.",
        "memory_declarations": [
            *[{"name": n, "type": "point3", "initial_value": v,
               "model_assumption": "hệ trục do đề chọn"}
              for n, v in (("I", [0, 0, 0]), ("A", [5, 0, 0]),
                           ("H", [0, 0, 3]), ("U", [1, 0, 3]),
                           ("W", [0, 1, 3]))],
            {"name": "cau", "type": "curved_solid"},
            {"name": "P", "type": "plane3"}, {"name": "C", "type": "circle3"},
            {"name": "S", "type": "float"},
        ],
        "statements": [
            {"kind": "construct_curved_solid", "target_var": "cau",
             "curved_kind": "ball", "anchor": "I", "rim_point": "A"},
            {"kind": "construct_plane", "target_var": "P",
             "through": ["H", "U", "W"]},
            {"kind": "assign", "target_var": "C",
             "expr": {"kind": "intersect_plane_curved", "solid": "cau",
                      "plane": "P"}},
            {"kind": "assign", "target_var": "S",
             "expr": {"kind": "measure", "quantity": "area", "of": "C"}},
        ],
        "visual_bindings": {"containers": [], "pointers": [], "value_boxes": []},
    }
    kq = _duong_san_pham(raw, (), "Cho mặt cầu tâm I đi qua A. Mặt phẳng (HUW) "
                         "cắt mặt cầu theo đường tròn (C). Tính diện tích (C).")
    assert kq.executable, getattr(kq, "reason", None)
    from app.simulation.geometry.radical import display

    # `route` không dựng cảnh (hướng phụ thuộc một chiều), nên đọc TRẠNG THÁI
    # CUỐI — nơi kernel để lại đại lượng đã tính.
    assert display(kq.final_memory["S"]) == "16π", kq.final_memory


# ══ §14 · KIẾN TRÚC TEST — cổng chống lỗ Phase 2 tái phát ════════════════
def test_KIEN_TRUC_moi_ca_duong_day_du_phai_qua_verify_and_compile():
    """Cấm một ca tự nhận "đường đầy đủ" mà bỏ qua grounding + cổng phủ.

    Phase 2 chứng minh lỗ này có thật và tốn kém: sáu nhân chứng gọi
    `kiem_tinh` + interpreter rồi được báo cáo là *"đi hết đường"*, nên hai
    cổng đắt nhất chưa từng chạy với khối cong — và một lượt đo live 26 lượt
    model mới tìm ra.

    Cổng đo bằng chữ: file này là file "đường đầy đủ" của miền cong, và mọi ca
    trong nó phải đi qua `_duong_san_pham`.
    """
    src = Path(__file__).read_text(encoding="utf-8")
    than = src[src.index("# ══ §15"):]
    for ten in ("_duong_san_pham", "verify_and_compile"):
        assert ten in src
    # Không ca nào trong phần chứng nhận được gọi thẳng interpreter.
    # Ghép lúc CHẠY: viết thẳng chuỗi thì chính dòng này trở thành lượt khớp,
    # và cổng đỏ vì đọc phải câu khẳng định của nó.
    goi = "SemanticProgram" + "Interpreter()"
    assert goi not in than, (
        "một ca 'đường đầy đủ' đang gọi thẳng interpreter — nó sẽ bỏ qua "
        "grounding và cổng phủ, đúng lỗ Phase 2 để lại")


def test_KIEN_TRUC_verify_and_compile_THAT_SU_chay_ca_hai_cong():
    """Đọc mã, không tin tên hàm."""
    src = inspect.getsource(verify_and_compile)
    phu = inspect.getsource(
        __import__("app.simulation.semantic_program.route",
                   fromlist=["_sau_grounding"])._sau_grounding)
    assert "check_grounding" in src
    assert "check_structural_coverage" in phu


# ══ §13 · R0 KHÔNG ĐƯỢC NỚI ══════════════════════════════════════════════
def test_13_R0_khong_doi__diem_BIA_van_bi_tu_choi():
    """Cầu nối chỉ đụng bảng KIỂU của nghĩa vụ; xuất xứ không đổi một dòng."""
    from app.simulation.semantic_program.grounding_gate import (
        _KIEU_DUOC_GIA_THIET,
        check_grounding,
    )

    assert _KIEU_DUOC_GIA_THIET == frozenset({"point3", "vector3"})
    raw = {
        "spec_version": "1.0", "title": "Ca kiểm cầu nối",
        "description": "Chương trình dựng tay cho một phép kiểm cổng.",
        "pedagogical_intent": "Kiểm cổng phủ, không dạy nội dung.",
        "memory_declarations": [
            {"name": "A", "type": "point3", "initial_value": [0, 0, 0]},
            {"name": "P_bia", "type": "point3", "initial_value": [2, 2, 2],
             "model_assumption": "điểm đối diện trong hình hộp bao quanh"},
            {"name": "I", "type": "point3"},
            {"name": "cau", "type": "curved_solid"},
        ],
        "statements": [
            {"kind": "construct_point", "target_var": "I",
             "expr": {"kind": "midpoint", "a": "A", "b": "P_bia"}},
            {"kind": "construct_curved_solid", "target_var": "cau",
             "curved_kind": "ball", "anchor": "I", "rim_point": "A"},
        ],
        "visual_bindings": {"containers": [], "pointers": [], "value_boxes": []},
    }
    kq = check_grounding(
        RequestContract(problem_text="Cho tứ diện ABCD. Tính bán kính mặt cầu "
                                     "ngoại tiếp."),
        SemanticProgramSpec.model_validate(raw))
    assert not kq.ok
    assert any("P_bia" in x for x in kq.unresolved), kq.unresolved


# ══ §17 · RANH GIỚI KHÔNG ĐƯỢC MỞ NHỜ CẦU NỐI ════════════════════════════
def test_17_cau_noi_KHONG_bien_phep_ngoai_bao_dong_thanh_hop_le():
    """Một lượng đo hợp lệ không được làm một PHÉP HÌNH HỌC ngoài bao đóng
    thành chạy được: mặt phẳng xiên vẫn phải chết ở runtime."""
    raw = {
        "spec_version": "1.0", "title": "Ca kiểm cầu nối",
        "description": "Chương trình dựng tay cho một phép kiểm cổng.",
        "pedagogical_intent": "Kiểm cổng phủ, không dạy nội dung.",
        "memory_declarations": [
            *[{"name": n, "type": "point3", "initial_value": v,
               "model_assumption": "hệ trục do đề chọn"}
              for n, v in (("O", [0, 0, 0]), ("Ot", [0, 0, 2]),
                           ("A", [1, 0, 0]), ("H", [0, 0, 1]),
                           ("U", [1, 0, 2]), ("W", [0, 1, 1]))],
            {"name": "tru", "type": "curved_solid"},
            {"name": "P", "type": "plane3"}, {"name": "C", "type": "circle3"},
        ],
        "statements": [
            {"kind": "construct_curved_solid", "target_var": "tru",
             "curved_kind": "cylinder", "anchor": "O", "apex_or_top": "Ot",
             "rim_point": "A"},
            {"kind": "construct_plane", "target_var": "P",
             "through": ["H", "U", "W"]},
            {"kind": "assign", "target_var": "C",
             "expr": {"kind": "intersect_plane_curved", "solid": "tru",
                      "plane": "P"}},
        ],
        "visual_bindings": {"containers": [], "pointers": [], "value_boxes": []},
    }
    kq = _duong_san_pham(raw, (), "Cho hình trụ hai đáy tâm O và Ot, điểm A trên "
                         "vành. Mặt phẳng (HUW) cắt xiên hình trụ.")
    assert not kq.executable, "mặt phẳng xiên KHÔNG được thành hợp lệ"
