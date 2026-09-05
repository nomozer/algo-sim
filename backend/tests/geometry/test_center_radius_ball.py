# -*- coding: utf-8 -*-
"""KHỐI CẦU KHAI BẰNG TÂM + BÁN KÍNH. **0 lượt gọi model.**

    `CENTER_RADIUS_CURVED_CONSTRUCTION_FOUNDATION`, 2026-09-04.

Ba điểm neo KHÔNG diễn đạt nổi lớp bài *"mặt cầu tâm O bán kính r"*: không phép
dựng nào sinh một ĐIỂM từ một điểm và một ĐỘ DÀI, nên mô hình buộc phải bịa một
điểm vành và grounding từ chối đúng (`UNANCHORED_DERIVED_ASSUMPTION`, ca
`ball_2`). Để engine tự dựng điểm ấy cũng bất khả — định lý ba bình phương hữu
tỉ nói `r² = 7` không có điểm vành hữu tỉ nào.

Wave mở ô `radius` nhận **TÊN một đại lượng**, không nhận một con số.
"""
from __future__ import annotations

import json
from fractions import Fraction
from pathlib import Path

import pytest

from app.simulation.geometry.curved import (
    ERR_BAN_KINH_NGOAI_MIEN,
    KHOI_CONG,
    CurvedSolid,
    binh_phuong_ban_kinh,
)
from app.simulation.geometry.exact import GeometryError, Vec3
from app.simulation.geometry.radical import display, is_exact_number, radical
from app.simulation.semantic_program.contract import SemanticProgramSpec
from app.simulation.semantic_program.obligations import Obligation
from app.simulation.semantic_program.request_contract import RequestContract
from app.simulation.semantic_program.route import verify_and_compile

GOC = Path(__file__).resolve().parents[3]

#: Ba giá trị của §5 — hữu tỉ · phân số · CĂN THỨC. Cái thứ ba là chỗ mẹo
#: `radius_sq` phát huy: bán kính vô tỉ mà bình phương vẫn hữu tỉ.
BA_BAN_KINH = [
    (13, "13", "8788π/3"),
    ("5/2", "5/2", "125π/6"),
    ("√3", "√3", "4π√3"),
]


def _ct(gt, tam="O", bk="r", khoi="S") -> RequestContract:
    return RequestContract(
        problem_text=f"Cho mặt cầu tâm {tam} bán kính {gt}. Tính bán kính và thể tích.",
        input_facts=[
            {"fact_id": "tam", "label": f"tâm {tam}", "values": [tam],
             "provenance": "confirmed"},
            {"fact_id": "bk", "label": "bán kính", "values": [gt],
             "provenance": "confirmed"},
        ],
        obligations=(
            Obligation(kind="radius", container=khoi, params={"witness": "R"}),
            Obligation(kind="volume", container=khoi, params={"witness": "V"}),
        ))


def _spec(gt, tam="O", bk="r", khoi="S", **doi) -> SemanticProgramSpec:
    d = {
        "title": "Mặt cầu tâm và bán kính cho trước",
        "memory_declarations": [
            {"name": tam, "type": "point3", "initial_value": [0, 0, 0],
             "source_fact_id": "tam"},
            {"name": bk, "type": "float", "initial_value": gt,
             "source_fact_id": "bk"},
            {"name": khoi, "type": "curved_solid"},
            {"name": "R", "type": "float"},
            {"name": "V", "type": "float"},
        ],
        "statements": [
            {"kind": "construct_curved_solid", "target_var": khoi,
             "curved_kind": "ball", "anchor": tam, "radius": bk},
            {"kind": "assign", "target_var": "R",
             "expr": {"kind": "measure", "quantity": "radius", "of": khoi}},
            {"kind": "assign", "target_var": "V",
             "expr": {"kind": "measure", "quantity": "volume", "of": khoi}},
        ],
    }
    d.update(doi)
    return SemanticProgramSpec.model_validate(d)


def _dl(oc) -> dict[str, str]:
    return {k: display(v) for k, v in (oc.final_memory or {}).items()
            if is_exact_number(v)}


# ══ A · BIỂU ĐẠT ĐƯỢC ═════════════════════════════════════════════════════
@pytest.mark.parametrize("gt,mong_r,mong_v", BA_BAN_KINH)
def test_A1_ba_gia_tri_ban_kinh_deu_chay_dung(gt, mong_r, mong_v):
    oc = verify_and_compile(_ct(gt), _spec(gt))
    assert oc.servable, oc.details
    assert _dl(oc)["R"] == mong_r
    assert _dl(oc)["V"] == mong_v


def test_A2_doi_TEN_diem_va_bien_khong_doi_hanh_vi():
    """Giải pháp phải áp cho mọi bài cùng cấu trúc, không bám tên nào."""
    a = verify_and_compile(_ct(13), _spec(13))
    b = verify_and_compile(
        _ct(13, tam="I", bk="ban_kinh", khoi="mat_cau"),
        _spec(13, tam="I", bk="ban_kinh", khoi="mat_cau"))
    assert a.servable and b.servable
    for x in (a, b):
        assert (_dl(x)["R"], _dl(x)["V"]) == ("13", "8788π/3")


def test_A3_ma_san_pham_KHONG_chua_id_ca_do_hay_gia_tri_test():
    """Không template theo bài: quét AST + văn bản mã sản phẩm."""
    import ast

    goc = GOC / "backend" / "app"
    cam = ("ball_2", "ball_1", "cylinder_2", "circumsphere", "8788")
    xau = []
    for f in goc.rglob("*.py"):
        cay = ast.parse(f.read_text(encoding="utf-8"))
        # Docstring KHÔNG phải mã: nhắc tên một ca đo trong lời giải thích là
        # ghi lại BẰNG CHỨNG, còn template là một chuỗi được DÙNG trong logic.
        tho = {id(n) for m in ast.walk(cay)
               if isinstance(m, (ast.Module, ast.ClassDef, ast.FunctionDef,
                                 ast.AsyncFunctionDef))
               and (d := ast.get_docstring(m, clean=False)) is not None
               for n in [m.body[0].value]}
        for n in ast.walk(cay):
            if isinstance(n, ast.Constant) and isinstance(n.value, str)                     and id(n) not in tho:
                for c in cam:
                    if c in n.value:
                        xau.append(f"{f.relative_to(goc)}:{n.lineno}: {c}")
    assert xau == [], xau


def test_A4_PROBLEM_FAMILY_SPECIAL_CASES_va_CURVED_TEMPLATES_deu_0():
    """Không nhánh nào rẽ theo tên hình ngoài thẩm quyền `curved.py`."""
    import re

    goc = GOC / "backend" / "app" / "simulation"
    nhanh = re.compile(
        r'(?:if|elif|while)\b[^\n]*(?:==|!=|\bin\b)[^\n]*'
        r'["\'](?:ball|cylinder|cone)["\']')
    pham = sorted(f.relative_to(goc).as_posix()
                  for f in goc.rglob("*.py") if nhanh.search(
                      f.read_text(encoding="utf-8")))
    assert pham == ["geometry/curved.py"], pham


# ══ B · TUYẾN ĐẦY ĐỦ ══════════════════════════════════════════════════════
def test_B_tuyen_day_du_cho_de_mat_cau_tam_O_ban_kinh_13():
    """Đề §7B, đúng từng ô nghiệm thu."""
    oc = verify_and_compile(_ct(13), _spec(13))
    assert oc.stage_reached == "served"
    assert oc.servable is True
    assert _dl(oc)["R"] == "13"
    assert _dl(oc)["V"] == "8788π/3"
    assert oc.total_steps and oc.total_steps > 0
    cfg = (oc.envelope or {})["config"]
    assert len(cfg["frames"]) == oc.total_steps

    from app.ai.pipeline import _dung_scene3d
    canh = _dung_scene3d(_spec(13), _ct(13))
    assert canh and canh["objects"] and canh["events"]


# ══ C · R0 ════════════════════════════════════════════════════════════════
def test_C1_tam_va_ban_kinh_co_xuat_xu_thi_duoc_nhan():
    assert verify_and_compile(_ct(13), _spec(13)).servable


def test_C2_source_fact_khong_ton_tai_bi_grounding_tu_choi():
    khai = [dict(d) for d in _spec(13).model_dump(mode="json")["memory_declarations"]]
    for k in khai:
        if k["name"] == "r":
            k["source_fact_id"] = "khong_co_that"
    oc = verify_and_compile(_ct(13), _spec(13, memory_declarations=khai))
    assert not oc.servable
    assert oc.stage_reached == "grounding"


def test_C3_ban_kinh_khong_khop_du_kien_de_bi_tu_choi():
    """Bán kính khai `99` trong khi đề cho `13` — grounding phải bắt."""
    khai = [dict(d) for d in _spec(13).model_dump(mode="json")["memory_declarations"]]
    for k in khai:
        if k["name"] == "r":
            k["initial_value"] = 99
    oc = verify_and_compile(_ct(13), _spec(13, memory_declarations=khai))
    assert not oc.servable and oc.stage_reached == "grounding"


def test_C4_diem_PHU_thieu_xuat_xu_VAN_bi_tu_choi():
    """Lỗ cũ của `ball_2` phải tiếp tục đóng: bản vá KHÔNG mở cửa cho toạ độ
    phụ do mô hình tự khai."""
    khai = [dict(d) for d in _spec(13).model_dump(mode="json")["memory_declarations"]]
    khai.append({"name": "P_bia", "type": "point3", "initial_value": [13, 0, 0],
                 "model_assumption": "một điểm trên mặt cầu"})
    oc = verify_and_compile(_ct(13), _spec(13, memory_declarations=khai))
    assert not oc.servable
    assert oc.stage_reached == "grounding"
    assert "UNANCHORED_DERIVED_ASSUMPTION" in " ".join(oc.details) or \
        oc.error_code == "input_not_grounded"


def test_C5_o_radius_nhan_TEN_chu_khong_nhan_MOT_CON_SO():
    """R0 ở tầng lược đồ: đưa thẳng một số vào `radius` phải hỏng."""
    with pytest.raises(Exception):
        _spec(13, statements=[
            {"kind": "construct_curved_solid", "target_var": "S",
             "curved_kind": "ball", "anchor": "O", "radius": 13}])


# ══ D · TƯƠNG THÍCH NGƯỢC ═════════════════════════════════════════════════
def test_D1_khoi_cau_theo_anchor_rim_point_van_chay_y_nguyen():
    s = CurvedSolid("ball", Vec3(Fraction(0), Fraction(0), Fraction(0)), None,
                    Vec3(Fraction(6), Fraction(0), Fraction(0)))
    assert s.radius_sq == 36


def test_D2_tru_va_non_NAY_NHAN_radius_va_van_doi_dung_mot_truc():
    """⚠️ **ĐẢO CHIỀU 2026-09-05** — `CURVED_CONSTRUCTION_GROUNDING_FOUNDATION`.

    Bản trước khẳng định `khai_bang_ban_kinh is False` cho trụ/nón và gọi đó là
    một quyết định PHẠM VI: *"trụ/nón đã có đường diễn đạt chạy được, nới thêm
    là mở một bề mặt chưa ai đo"*.

    Lượt V3 held-out đo và chứng minh câu ấy SAI (`docs/CURVED_V3_LIVE_ACCEPTANCE.md`
    §8b): đường duy nhất cho trụ/nón là `rim_point` — một điểm trên vành đáy —
    mà đề SGK **không bao giờ đặt tên** cho điểm ấy, nên grounding gate chặn
    mọi cách khai nó, kể cả cách DỰNG bằng `translate`. 0/6 ca trụ+nón đi qua.

    Một test khoá một quyết định phạm vi thì phải đổi khi phạm vi đổi — điều
    không được đổi là **luật**: trục vẫn do ĐÚNG MỘT nguồn xác định.
    """
    for k in ("cylinder", "cone"):
        assert KHOI_CONG[k].khai_bang_ban_kinh is True
        # Trục do `apex_or_top` — hợp lệ.
        SemanticProgramSpec.model_validate({
            "title": "trụ khai bằng bán kính",
            "memory_declarations": [
                {"name": "O", "type": "point3", "initial_value": [0, 0, 0]},
                {"name": "T", "type": "point3", "initial_value": [0, 0, 2]},
                {"name": "r", "type": "float", "initial_value": 3},
                {"name": "K", "type": "curved_solid"}],
            "statements": [{"kind": "construct_curved_solid",
                            "target_var": "K", "curved_kind": k,
                            "anchor": "O", "apex_or_top": "T",
                            "radius": "r"}]})
        # Nhưng KHÔNG trục thì vẫn hỏng — luật cũ giữ nguyên.
        with pytest.raises(Exception):
            SemanticProgramSpec.model_validate({
                "title": "trụ thiếu trục",
                "memory_declarations": [
                    {"name": "O", "type": "point3", "initial_value": [0, 0, 0]},
                    {"name": "r", "type": "float", "initial_value": 3},
                    {"name": "K", "type": "curved_solid"}],
                "statements": [{"kind": "construct_curved_solid",
                                "target_var": "K", "curved_kind": k,
                                "anchor": "O", "radius": "r"}]})


def test_D3_khai_CA_HAI_hoac_KHONG_CAI_NAO_deu_hong():
    for them in ({"rim_point": "P", "radius": "r"}, {}):
        with pytest.raises(Exception):
            SemanticProgramSpec.model_validate({
                "title": "khai bán kính mập mờ",
                "memory_declarations": [
                    {"name": "O", "type": "point3", "initial_value": [0, 0, 0]},
                    {"name": "P", "type": "point3", "initial_value": [1, 0, 0]},
                    {"name": "r", "type": "float", "initial_value": 3},
                    {"name": "S", "type": "curved_solid"}],
                "statements": [{"kind": "construct_curved_solid",
                                "target_var": "S", "curved_kind": "ball",
                                "anchor": "O", **them}]})


def test_D4_chuong_trinh_LICH_SU_van_parse():
    KHOA = ("chuong_trinh", "semantic_program")

    def quet(x, ra):
        if isinstance(x, dict):
            for k, v in x.items():
                if k in KHOA and isinstance(v, dict) and \
                        isinstance(v.get("statements"), list):
                    ra.append(v)
                quet(v, ra)
        elif isinstance(x, list):
            for v in x:
                quet(v, ra)

    dem = 0
    for f in (GOC / "docs/evaluation/geometry").rglob("*.json"):
        ra: list = []
        try:
            quet(json.loads(f.read_text(encoding="utf-8")), ra)
        except (json.JSONDecodeError, RecursionError):
            continue
        for ct in ra:
            SemanticProgramSpec.model_validate(ct)
            dem += 1
    assert dem >= 40, f"chỉ đọc được {dem} chương trình lịch sử"


# ══ E · MIỀN SỐ + CHECKER ═════════════════════════════════════════════════
@pytest.mark.parametrize("r,q", [
    (13, Fraction(169)), (Fraction(5, 2), Fraction(25, 4)),
    (radical(1, 3), Fraction(3)),
])
def test_E1_binh_phuong_ban_kinh_dung(r, q):
    assert binh_phuong_ban_kinh(r) == q


@pytest.mark.parametrize("r", [radical(2, 1, 1), 0, -3])
def test_E2_ngoai_mien_thi_TU_CHOI_co_ma_cau_truc(r):
    with pytest.raises(GeometryError) as e:
        binh_phuong_ban_kinh(r)
    assert e.value.code == ERR_BAN_KINH_NGOAI_MIEN


def test_E3_checker_doc_HINH_chu_khong_tin_witness_chuong_trinh_khai():
    """Khai sai đáp số thì hậu điều kiện phải bắt — checker tính lại từ khối."""
    khai = [dict(d) for d in _spec(13).model_dump(mode="json")["memory_declarations"]]
    khai.append({"name": "R_sai", "type": "float", "initial_value": 99})
    oc = verify_and_compile(
        RequestContract(
            problem_text="Cho mặt cầu tâm O bán kính 13. Tính bán kính.",
            input_facts=[
                {"fact_id": "tam", "label": "tâm O", "values": ["O"],
                 "provenance": "confirmed"},
                {"fact_id": "bk", "label": "bán kính", "values": [13],
                 "provenance": "confirmed"}],
            obligations=(Obligation(kind="radius", container="S",
                                    params={"witness": "R_sai"}),)),
        _spec(13, memory_declarations=khai))
    assert not oc.servable, "khai đáp án mà vẫn phục vụ là thủng C₁b/C₂"


# ══ F · TRACE VÀ SCENE3D ══════════════════════════════════════════════════
def test_F1_mot_phep_dung_ball_la_DUNG_MOT_buoc():
    from app.simulation.semantic_program.interpreter import (
        SemanticProgramInterpreter)

    res = SemanticProgramInterpreter(max_steps=500).execute(_spec(13))
    dung = [b for b in res.trace
            if getattr(b, "action", None) == "construct_curved_solid"]
    assert len(dung) == 1


def test_F2_scene_mang_tam_va_ban_kinh_CHINH_XAC_khong_mang_mesh():
    from app.ai.pipeline import _dung_scene3d

    canh = _dung_scene3d(_spec(13), _ct(13))
    qc = next(o for o in canh["objects"] if o["id"] == "S")
    assert qc["anchor"] == ["0", "0", "0"]
    assert qc["radius_sq"] == "169"          # chuỗi phân số chính xác
    assert qc["rim_point"] is None
    for cam in ("vertices", "faces", "mesh", "triangles"):
        assert cam not in qc, f"payload ngữ nghĩa mang {cam} — tessellation rò"


def test_F3_producer_va_depends_truy_ve_tam_VA_bien_ban_kinh():
    from app.ai.pipeline import _dung_scene3d

    canh = _dung_scene3d(_spec(13), _ct(13))
    qc = next(o for o in canh["objects"] if o["id"] == "S")
    assert set(qc["depends"]) == {"O", "r"}, qc["depends"]
    sk = next(e for e in canh["events"] if e["object"] == "S")
    assert set(sk["depends"]) == {"O", "r"}


def test_F4_chon_ket_qua_cho_bao_dong_day_du():
    from app.ai.pipeline import _dung_scene3d

    canh = _dung_scene3d(_spec(13), _ct(13))
    theo = {o["id"]: o for o in canh["objects"]}

    def closure(start):
        tham, hd = set(), list(theo.get(start, {}).get("depends") or [])
        while hd:
            x = hd.pop(0)
            if x in tham or x == start:
                continue
            tham.add(x)
            hd.extend(theo.get(x, {}).get("depends") or [])
        return tham

    assert {"S", "O", "r"} <= closure("V") | {"V"}
    assert closure("S") == {"O", "r"}
