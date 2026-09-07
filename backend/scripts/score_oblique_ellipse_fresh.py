# -*- coding: utf-8 -*-
"""Bộ chấm cho `OBLIQUE_ELLIPSE_FRESH_END_TO_END_CONFIRMATION`.

Cắm vào `run_curved_end_to_end` qua `registration.scorer_module`. Xuất đúng hai
hàm mà runner tìm: `cham_analyze` và `cham_synthesis`.

Vì sao là module riêng chứ không nới hai bộ chấm mặc định: chúng hỏi những
chiều của **bài nón** (`radius` của một đường tròn, `ratio` của điểm chia đoạn).
Nới chúng để nhận thêm bài elip là dựng một bộ chấm biết hai bài — và bộ chấm
thứ ba sẽ nới lần nữa. Một wave, một bộ chấm; runner là thứ dùng chung.

Ba giá trị chấm giữ nguyên nghĩa đã đăng ký: `PASS` / `FAIL` khi có dữ liệu ·
**`NOT_CAPTURED`** khi bộ đo không giữ được thứ cần để phán · `NOT_REACHED` khi
tầng ấy chưa chạy.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

BACKEND = Path(__file__).resolve().parents[1]
for _p in (str(BACKEND), str(BACKEND / "scripts")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

NOT_CAPTURED = "NOT_CAPTURED"
#: Nội dung fact CHỈ đọc được từ raw của tầng `semantic_analyze`.
NGUON_DU_CHAM_FACT = ("RAW_ANALYZE",)


def cham_analyze(ct: dict | None, nguon: str = "KHONG_CO",
                 so_fact_quan_sat: int | None = None) -> dict[str, Any]:
    """Hợp đồng do mô hình trích — chấm theo DỮ KIỆN ĐỀ, không theo tên biến.

    ⚠️ Không quan sát được ≠ sai: nguồn không mang nội dung fact ⇒ mọi chiều về
    fact ghi `NOT_CAPTURED`.
    """
    if not ct:
        return {"ANALYZE_CONTRACT_CORRECT": NOT_CAPTURED,
                "NGUON_HOP_DONG": nguon, "ly_do": "không có hợp đồng"}
    obs = ct.get("obligations") or []
    ob_area = [o for o in obs if o.get("kind") == "area"]
    ra: dict[str, Any] = {
        "NGUON_HOP_DONG": nguon,
        "SO_FACT": len(ct.get("input_facts") or []) or so_fact_quan_sat,
        "OBLIGATION_KINDS": sorted({o.get("kind") for o in obs}),
        "CO_NGHIA_VU_AREA": bool(ob_area),
        "CONTAINER_KHAI": [o.get("container") for o in ob_area],
        "WITNESS_KHAI": [o.get("witness") or (o.get("params") or {}).get("witness")
                         for o in ob_area],
    }
    # ── Chiều NGHĨA VỤ: đọc được từ mọi nguồn ─────────────────────────────
    #
    # Container phải trỏ ĐÚNG vật được hỏi — elip `(E)`. Chuẩn hoá bỏ ngoặc và
    # hạ chữ, cùng lưới mà `OBLIGATION_CONTAINER_NAME_BINDING` đã dựng.
    ra["ANALYZE_OBLIGATION_CORRECT"] = (
        "PASS" if (ob_area and any(
            str(o.get("container", "")).strip("() ").lower() == "e"
            for o in ob_area)) else "FAIL")
    ra["CO_WITNESS"] = bool([w for w in ra["WITNESS_KHAI"] if w])

    # ── Chiều FACT: chỉ đọc được từ raw analyze ──────────────────────────
    if nguon not in NGUON_DU_CHAM_FACT:
        for k in ("CO_HAI_TAM", "CO_BAN_KINH_4", "CO_CHIEU_CAO_HOAC_TRUC",
                  "CO_PHUONG_TRINH_MP", "CO_VAT_DUOC_HOI_LA_ELIP",
                  "ANALYZE_FACTS_CORRECT", "ANALYZE_CONTRACT_CORRECT"):
            ra[k] = NOT_CAPTURED
        return ra

    tho = json.dumps(ct.get("input_facts") or [], ensure_ascii=False)
    kh = tho.replace(" ", "")
    ra["CO_HAI_TAM"] = ("(0,0,0)" in kh) and ("(0,0,20)" in kh)
    ra["CO_BAN_KINH_4"] = '"4"' in kh or ":4," in kh or "4]" in kh
    ra["CO_CHIEU_CAO_HOAC_TRUC"] = ("20" in kh)
    # Phương trình mặt phẳng: chấp cả `2x-z+10=0` lẫn lối viết có dấu cách.
    ra["CO_PHUONG_TRINH_MP"] = ("2x-z+10=0" in kh) or ("2x−z+10=0" in kh)
    ra["CO_VAT_DUOC_HOI_LA_ELIP"] = ("elip" in tho.lower()) or ("(E)" in tho)
    ra["ANALYZE_FACTS_CORRECT"] = "PASS" if all(
        (ra["CO_HAI_TAM"], ra["CO_BAN_KINH_4"], ra["CO_PHUONG_TRINH_MP"],
         ra["CO_VAT_DUOC_HOI_LA_ELIP"])) else "FAIL"
    ra["ANALYZE_CONTRACT_CORRECT"] = (
        "PASS" if (ra["ANALYZE_FACTS_CORRECT"] == "PASS"
                   and ra["ANALYZE_OBLIGATION_CORRECT"] == "PASS") else "FAIL")
    return ra


def cham_synthesis(spec: dict | None) -> dict[str, Any]:
    """Mười chiều của §8, chấm từ chính chương trình mô hình sinh."""
    if not spec:
        return {"SYNTHESIS_SCORED": False}
    khai = {m.get("name"): m for m in (spec.get("memory_declarations") or [])}
    stmts = spec.get("statements") or []

    def _expr(s):
        return (s or {}).get("expr") or {}

    tru = next((s for s in stmts
                if s.get("kind") == "construct_curved_solid"), None)
    mp = next((s for s in stmts if s.get("kind") == "construct_plane"), None)
    # ⚠️ LỐI THỨ HAI, thêm 2026-09-07 sau `PLANE_FROM_EQUATION_REPRESENTATION`.
    #
    # Bản trước chỉ biết `construct_plane` qua ba điểm, nên khi mô hình dùng
    # phép mới nó chấm `PLANE_CONSTRUCTION_CORRECT = FAIL` cho một chương
    # trình **dựng mặt phẳng ĐÚNG** — bộ đo tụt lại sau hệ đúng một wave.
    # Đo được ở `oblique-ellipse-after-axis-scale-repair` (lượt live đầu tiên
    # mô hình chọn phép ấy): hệ số `(2,0,−1,10)` khớp đề từng con số.
    mp_pt = next((s for s in stmts
                  if s.get("kind") == "construct_plane_from_equation"), None)
    giao = next((s for s in stmts
                 if _expr(s).get("kind") == "intersect_plane_curved_ellipse"),
                None)
    # Phép SAI mà mô hình dễ với tay tìm — ghi riêng để phân loại lỗi.
    giao_tron = next((s for s in stmts
                      if _expr(s).get("kind") == "intersect_plane_curved"), None)
    section = next((s for s in stmts if s.get("kind") == "construct_section"),
                   None)
    do = next((s for s in stmts
               if _expr(s).get("kind") == "measure"
               and _expr(s).get("quantity") == "area"), None)
    do_radius = next((s for s in stmts
                      if _expr(s).get("kind") == "measure"
                      and _expr(s).get("quantity") == "radius"), None)
    ten_E = (giao or {}).get("target_var")

    return {
        "SYNTHESIS_SCORED": True,
        # ① toán tử được chọn
        "OPERATOR_CHOSEN": (_expr(giao).get("kind") if giao else
                            (_expr(giao_tron).get("kind") if giao_tron else
                             ("construct_section" if section else None))),
        "OPERATOR_CORRECT": "PASS" if giao else "FAIL",
        # ② kiểu khai của kết quả
        "RESULT_TYPE_KHAI": (khai.get(ten_E) or {}).get("type") if ten_E else None,
        "RESULT_TYPE_CORRECT": (
            "PASS" if (khai.get(ten_E) or {}).get("type") == "ellipse3"
            else "FAIL"),
        # ③ dựng hình trụ
        "CYLINDER_KIND": (tru or {}).get("curved_kind"),
        # ⚠️ Hỏi CẢ HAI ô, không hỏi *"ô nào thắng"*: một ứng viên có thể khai
        # `anchor + apex_or_top` (point mode) rồi VẪN thêm `rim_point` để mã
        # hoá bán kính — đúng hình dạng đã đo ở lượt sau khi sửa thang trục.
        # Bản trước trả một chuỗi duy nhất nên hình dạng ấy đọc ra "rim_point"
        # và mất thông tin là khối vốn đã đủ hai điểm trục.
        "CYLINDER_KHAI_BANG": ("radius" if (tru or {}).get("radius")
                               else ("rim_point" if (tru or {}).get("rim_point")
                                     else None)),
        "DIRECT_RADIUS_USED": bool((tru or {}).get("radius")),
        "RIM_POINT_USED": bool((tru or {}).get("rim_point")),
        "HEIGHT_USED": bool((tru or {}).get("height")),
        "AXIS_TWO_POINTS": bool((tru or {}).get("anchor")
                                and (tru or {}).get("apex_or_top")),
        "RIM_POINT_GROUNDED": _rim_co_xuat_xu(khai, tru),
        "CYLINDER_CONSTRUCTION_CORRECT": (
            "PASS" if (tru and tru.get("curved_kind") == "cylinder"
                       and tru.get("anchor") and tru.get("apex_or_top"))
            else "FAIL"),
        # ④ dựng mặt phẳng — HAI lối, cả hai hợp lệ
        "PLANE_OPERATION": ("construct_plane_from_equation" if mp_pt
                            else ("construct_plane" if mp else None)),
        "PLANE_THROUGH": (mp or {}).get("through"),
        "PLANE_COEFFICIENTS": _he_so(mp_pt),
        "PLANE_COEFFICIENTS_CORRECT": _he_so_dung(mp_pt),
        "PLANE_CONSTRUCTION_CORRECT": (
            "PASS" if (_he_so_dung(mp_pt) == "PASS"
                       or (mp and len(mp.get("through") or []) == 3))
            else "FAIL"),
        # ⑤ producer của elip
        "ELLIPSE_PRODUCER_PRESENT": (
            "PASS" if (giao and ten_E
                       and (khai.get(ten_E) or {}).get("initial_value")
                       in (None, [])) else "FAIL"),
        # ⑥ đo đúng đại lượng, đúng chủ thể
        "MEASURE_QUANTITY": ("area" if do else ("radius" if do_radius else None)),
        "MEASURE_OF": _expr(do).get("of") if do else None,
        "MEASURE_DUNG_CHU_THE": bool(do and ten_E
                                     and _expr(do).get("of") == ten_E),
        # Ba điểm mặt phẳng có thoả phương trình `2x − z + 10 = 0` không —
        # chấm bằng SỐ HỌC trên toạ độ mô hình khai, không bằng chữ.
        "PLANE_POINTS_ON_EQUATION": _diem_thoa_phuong_trinh(khai, mp),
    }


def _he_so(mp_pt: dict | None) -> Any:
    """Bốn hệ số của `construct_plane_from_equation`, dạng chuỗi."""
    if not mp_pt:
        return None
    return [str(mp_pt.get(t)) for t in ("a", "b", "c", "d")]


def _he_so_dung(mp_pt: dict | None) -> str:
    """Hệ số có TỈ LỆ với `2x − z + 10 = 0` không — so chính xác, không so chữ.

    So TỈ LỆ chứ không so bằng: `−4x + 2z − 20 = 0` là **cùng một mặt phẳng**,
    và chấm nó FAIL sẽ là bộ đo hẹp hơn chính hệ (`plane_equation.tuong_duong`
    đã so tỉ lệ từ khi phép dựng ra đời).
    """
    if not mp_pt:
        return NOT_CAPTURED
    try:
        from app.simulation.semantic_program.plane_equation import tuong_duong

        return ("PASS" if tuong_duong(_he_so(mp_pt), ("2", "0", "-1", "10"))
                else "FAIL")
    except Exception:                                             # noqa: BLE001
        return NOT_CAPTURED


def _rim_co_xuat_xu(khai: dict, tru: dict | None) -> Any:
    """Điểm vành có neo về một mục dữ kiện không, hay chỉ `model_assumption`.

    Đây là ô phân biệt *"mô hình chọn nhầm cách khai"* với *"mô hình bịa dữ
    liệu"*. Cả hai đều trượt grounding, nhưng chúng là hai bệnh khác nhau.
    """
    ten = (tru or {}).get("rim_point")
    if not ten:
        return NOT_CAPTURED
    d = khai.get(ten) or {}
    return bool(d.get("source_fact_id"))


def _diem_thoa_phuong_trinh(khai: dict, mp: dict | None) -> Any:
    """`2x − z + 10 = 0` cho từng điểm mà `construct_plane` đi qua.

    Trả `NOT_CAPTURED` khi không đọc được toạ độ — mô hình có thể dựng ba điểm
    ấy bằng phép dựng thay vì khai thẳng, và khi ấy toạ độ chỉ có lúc chạy.
    """
    if not mp:
        return NOT_CAPTURED
    ra = {}
    for ten in (mp.get("through") or []):
        iv = (khai.get(ten) or {}).get("initial_value")
        if not (isinstance(iv, (list, tuple)) and len(iv) == 3):
            ra[ten] = NOT_CAPTURED
            continue
        try:
            from fractions import Fraction as F

            x, _y, z = (F(str(c)) for c in iv)
            ra[ten] = (2 * x - z + 10 == 0)
        except Exception:                                         # noqa: BLE001
            ra[ten] = NOT_CAPTURED
    return ra
