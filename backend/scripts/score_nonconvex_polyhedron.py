# -*- coding: utf-8 -*-
"""Bộ chấm cho `NONCONVEX_POLYHEDRON_MODEL_DISCOVERABILITY`.

Cắm vào `run_curved_end_to_end` qua `registration.scorer_module`. Xuất đúng hai
hàm runner tìm: `cham_analyze` và `cham_synthesis`.

─── NGUYÊN TẮC: CHẤM THEO HÌNH HỌC, KHÔNG THEO CHÍNH TẢ ──────────────────

Bảng mặt có **nhiều cách viết đúng cho cùng một khối**: đảo chiều một mặt,
xoay vòng thứ tự đỉnh trong một mặt, đổi thứ tự các mặt, thậm chí đặt tên biến
khác. `dinh_huong_bien` của kernel tự định hướng lại, nên mọi biến thể ấy cho
**cùng một khối và cùng một thể tích**. Bộ chấm phải chấp nhận đúng tập ấy —
ghim chính tả là chấm sai một chương trình đúng, và kho này đã trả giá cho lỗi
ấy một lần (`PLANE_CONSTRUCTION_CORRECT = FAIL` cho mặt phẳng đúng từng hệ số).

Nên `FACE_TABLE_VALID` được quyết bằng **bốn bất biến tổ hợp**, không bằng so
chuỗi:

    · đúng MỘT mặt gồm trọn năm đỉnh đáy, và chu trình của nó là chu trình đáy
    · năm mặt còn lại mỗi mặt = một CẠNH ĐÁY + đỉnh S
    · mỗi cạnh vô hướng thuộc ĐÚNG hai mặt   (biên kín)
    · không mặt nào lặp đỉnh

Ba giá trị chấm giữ nguyên nghĩa đã đăng ký: `PASS` / `FAIL` khi có dữ liệu ·
**`NOT_CAPTURED`** khi bộ đo không giữ được thứ cần để phán · `NOT_REACHED`
khi tầng ấy chưa chạy.
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

from gold_nonconvex_polyhedron import (  # noqa: E402
    CANH_DAY, DINH_DAY, TOA_DO,
)

NOT_CAPTURED = "NOT_CAPTURED"
#: Nội dung fact CHỈ đọc được từ raw của tầng `semantic_analyze`.
NGUON_DU_CHAM_FACT = ("RAW_ANALYZE",)

#: Toạ độ → tên chuẩn. Mô hình được đặt tên biến tuỳ ý; thứ neo là TOẠ ĐỘ.
_THEO_TOA_DO = {tuple(v): k for k, v in TOA_DO.items()}


def _so(x) -> float | None:
    try:
        if isinstance(x, str) and "/" in x:
            a, b = x.split("/", 1)
            return float(a) / float(b)
        return float(x)
    except (TypeError, ValueError):
        return None


def _tuple3(v) -> tuple | None:
    if not isinstance(v, (list, tuple)) or len(v) != 3:
        return None
    xs = [_so(x) for x in v]
    return None if any(x is None for x in xs) else tuple(xs)


def cham_analyze(ct: dict | None, nguon: str = "KHONG_CO",
                 so_fact_quan_sat: int | None = None) -> dict[str, Any]:
    """Hợp đồng do mô hình trích — chấm theo DỮ KIỆN ĐỀ, không theo tên biến.

    ⚠️ Không quan sát được ≠ sai: nguồn không mang nội dung fact ⇒ mọi chiều
    về fact ghi `NOT_CAPTURED`. Đây là đính chính đã trả giá ở
    `PROVENANCE_AFFORDANCE_AB_4_LUOT` và ở lượt elip cuối.
    """
    if not ct:
        return {"ANALYZE_CONTRACT_CORRECT": NOT_CAPTURED,
                "NGUON_HOP_DONG": nguon, "ly_do": "không có hợp đồng"}
    obs = ct.get("obligations") or []
    ob_v = [o for o in obs if o.get("kind") == "volume"]
    ra: dict[str, Any] = {
        "NGUON_HOP_DONG": nguon,
        "SO_FACT": len(ct.get("input_facts") or []) or so_fact_quan_sat,
        "OBLIGATION_KINDS": sorted({o.get("kind") for o in obs}),
        "CO_NGHIA_VU_VOLUME": bool(ob_v),
        "CONTAINER_KHAI": [o.get("container") for o in ob_v],
        "WITNESS_KHAI": [o.get("witness") or (o.get("params") or {}).get("witness")
                         for o in ob_v],
    }
    # ── Chiều NGHĨA VỤ: đọc được từ mọi nguồn ────────────────────────────
    #
    # Container phải trỏ ĐÚNG vật được hỏi — khối chóp. Chuẩn hoá bỏ dấu chấm
    # và ngoặc rồi hạ chữ: `S.ABCDE` · `(S.ABCDE)` · `SABCDE` · `chop` đều là
    # cùng một vật nếu nó gom đủ sáu chữ cái. Cùng lưới mà
    # `OBLIGATION_CONTAINER_NAME_BINDING` đã dựng.
    def _khop_container(c: str) -> bool:
        k = "".join(ch for ch in str(c).upper() if ch.isalpha())
        return set("SABCDE") <= set(k) if k else False

    ra["ANALYZE_OBLIGATION_CORRECT"] = (
        "PASS" if (ob_v and any(_khop_container(o.get("container", ""))
                                for o in ob_v)) else "FAIL")
    ra["CO_WITNESS"] = bool([w for w in ra["WITNESS_KHAI"] if w])

    # ── Chiều FACT: chỉ đọc được từ raw analyze ─────────────────────────
    if nguon not in NGUON_DU_CHAM_FACT:
        for k in ("CO_DU_SAU_DIEM", "DIEM_THIEU", "CO_TU_LOM",
                  "KHONG_TU_THEM_DU_KIEN", "ANALYZE_FACTS_CORRECT",
                  "ANALYZE_CONTRACT_CORRECT"):
            ra[k] = NOT_CAPTURED
        return ra

    tho = json.dumps(ct.get("input_facts") or [], ensure_ascii=False)
    kh = tho.replace(" ", "")
    thieu = [t for t, xyz in TOA_DO.items()
             if f"({xyz[0]},{xyz[1]},{xyz[2]})" not in kh
             and f"[{xyz[0]},{xyz[1]},{xyz[2]}]" not in kh]
    ra["DIEM_THIEU"] = thieu
    ra["CO_DU_SAU_DIEM"] = not thieu
    ra["CO_TU_LOM"] = ("lõm" in tho.lower()) or ("lom" in tho.lower())
    # Không tự thêm dữ kiện hình học: đề KHÔNG nói vuông góc, không nói
    # đường cao, không nói mặt phẳng nào khác. Mô hình khai thêm là đang
    # tự phát minh giả thiết.
    bia = [w for w in ("vuông góc", "vuong goc", "song song", "trung điểm",
                       "đường cao", "duong cao") if w in tho.lower()]
    ra["KHONG_TU_THEM_DU_KIEN"] = not bia
    ra["DU_KIEN_BIA"] = bia
    ra["ANALYZE_FACTS_CORRECT"] = "PASS" if (
        ra["CO_DU_SAU_DIEM"] and ra["KHONG_TU_THEM_DU_KIEN"]) else "FAIL"
    ra["ANALYZE_CONTRACT_CORRECT"] = (
        "PASS" if (ra["ANALYZE_FACTS_CORRECT"] == "PASS"
                   and ra["ANALYZE_OBLIGATION_CORRECT"] == "PASS") else "FAIL")
    return ra


def _ten_theo_toa_do(spec: dict) -> dict[str, str]:
    """Biến `point3` của mô hình → tên chuẩn `A..E,S`, neo bằng TOẠ ĐỘ.

    Mô hình được đặt tên tuỳ ý; ghim tên là chấm chính tả. Nếu nó đặt đúng
    `A..S` thì ánh xạ là đồng nhất, và ô `TEN_TRUNG_DE` ghi lại điều đó.
    """
    ra: dict[str, str] = {}
    for d in spec.get("memory_declarations") or []:
        if d.get("type") != "point3":
            continue
        t = _tuple3(d.get("initial_value"))
        if t is not None and t in _THEO_TOA_DO:
            ra[str(d.get("name"))] = _THEO_TOA_DO[t]
    return ra


def _mat_chuan(faces, dinh_ct: list[str], anh_xa: dict[str, str]):
    """Bảng mặt của mô hình → danh sách mặt bằng TÊN CHUẨN, hoặc `None`.

    `construct_solid.faces` nhận **cả tên đỉnh lẫn chỉ số**; biên chuẩn hoá của
    hệ quy về chỉ số trước khi Pydantic kiểm, nên raw của mô hình có thể ở cả
    hai dạng. Bộ chấm phải đọc được cả hai — đọc một dạng là chấm FAIL cho một
    chương trình đúng viết theo dạng kia.
    """
    ra = []
    for m in faces or []:
        if not isinstance(m, (list, tuple)):
            return None
        mat = []
        for x in m:
            if isinstance(x, bool):
                return None
            if isinstance(x, int):
                if not 0 <= x < len(dinh_ct):
                    return None
                ten = dinh_ct[x]
            else:
                ten = str(x)
            mat.append(anh_xa.get(ten, ten))
        ra.append(mat)
    return ra


def cham_bang_mat(mat_chuan) -> dict[str, Any]:
    """Bốn bất biến tổ hợp. Không so chuỗi, không ghim chiều, không ghim thứ tự."""
    ra: dict[str, Any] = {}
    if not mat_chuan:
        return {"FACE_TABLE_VALID": "FAIL", "ly_do": "không có bảng mặt"}

    ra["SO_MAT"] = len(mat_chuan)
    ra["KHONG_LAP_DINH"] = all(len(set(m)) == len(m) for m in mat_chuan)

    day = [m for m in mat_chuan if set(m) == set(DINH_DAY)]
    ra["CO_DUNG_MOT_MAT_DAY"] = len(day) == 1
    # Chu trình đáy phải TRÙNG chu trình đề cho — xoay vòng và đảo chiều đều
    # là cùng một chu trình, nên so bằng TẬP CẠNH.
    ra["CHU_TRINH_DAY_DUNG"] = bool(day) and (
        frozenset(frozenset((day[0][i], day[0][(i + 1) % len(day[0])]))
                  for i in range(len(day[0]))) == CANH_DAY)

    ben = [m for m in mat_chuan if set(m) != set(DINH_DAY)]
    ra["SO_MAT_BEN"] = len(ben)
    canh_ben = set()
    ben_ok = True
    for m in ben:
        if len(m) != 3 or "S" not in m:
            ben_ok = False
            continue
        con = [x for x in m if x != "S"]
        if len(con) != 2 or frozenset(con) not in CANH_DAY:
            ben_ok = False
            continue
        canh_ben.add(frozenset(con))
    ra["MAT_BEN_DEU_LA_CANH_DAY_CONG_S"] = ben_ok and len(ben) == 5
    ra["PHU_DU_NAM_CANH_DAY"] = canh_ben == set(CANH_DAY)

    # Biên KÍN: mỗi cạnh vô hướng thuộc đúng hai mặt.
    dem: dict[frozenset, int] = {}
    for m in mat_chuan:
        for i in range(len(m)):
            e = frozenset((m[i], m[(i + 1) % len(m)]))
            if len(e) != 2:
                continue
            dem[e] = dem.get(e, 0) + 1
    ra["BIEN_KIN"] = bool(dem) and all(v == 2 for v in dem.values())
    ra["CANH_LECH"] = sorted(tuple(sorted(e)) for e, v in dem.items() if v != 2)

    ra["FACE_TABLE_VALID"] = "PASS" if all((
        ra["KHONG_LAP_DINH"], ra["CO_DUNG_MOT_MAT_DAY"],
        ra["CHU_TRINH_DAY_DUNG"], ra["MAT_BEN_DEU_LA_CANH_DAY_CONG_S"],
        ra["PHU_DU_NAM_CANH_DAY"], ra["BIEN_KIN"])) else "FAIL"
    return ra


def cham_synthesis(spec: dict | None) -> dict[str, Any]:
    """Chấm chính chương trình mô hình sinh — §6 của brief."""
    if not spec:
        return {"SYNTHESIS_SCORED": False}
    khai = {m.get("name"): m for m in (spec.get("memory_declarations") or [])}
    stmts = spec.get("statements") or []

    def _expr(s):
        return (s or {}).get("expr") or {}

    khoi = next((s for s in stmts if s.get("kind") == "construct_solid"), None)
    do = next((s for s in stmts
               if _expr(s).get("kind") == "measure"
               and _expr(s).get("quantity") == "volume"), None)

    anh_xa = _ten_theo_toa_do(spec)
    ra: dict[str, Any] = {
        "SYNTHESIS_SCORED": True,
        "SO_KHAI": len(khai),
        "SO_LENH": len(stmts),
        "KIND_DA_DUNG": sorted({s.get("kind") for s in stmts if s.get("kind")}),
        "USES_CONSTRUCT_SOLID": khoi is not None,
        "USES_MEASURE_VOLUME": do is not None,
        # Sáu điểm neo bằng TOẠ ĐỘ, không bằng tên.
        "DIEM_KHOP_TOA_DO": sorted(set(anh_xa.values())),
        "CO_DU_SAU_DINH": set(anh_xa.values()) == set(DINH_DAY) | {"S"},
        "TEN_TRUNG_DE": all(k == v for k, v in anh_xa.items()),
    }

    # ── Điểm phải GROUNDED, không phải hằng số trời rơi ─────────────────
    ra["DIEM_CO_XUAT_XU"] = sorted(
        n for n in anh_xa
        if (khai.get(n) or {}).get("source_fact_id")
        or (khai.get(n) or {}).get("model_assumption"))
    ra["MOI_DIEM_CO_XUAT_XU"] = len(ra["DIEM_CO_XUAT_XU"]) == len(anh_xa)

    # ── ĐƯỜNG TẮT: khai thẳng đáp số thay vì dựng ──────────────────────
    #
    # Hai lối: gán hằng vào biến kết quả, hoặc khai `initial_value` cho nó.
    dich = (do or {}).get("target_var")
    hang = [s for s in stmts
            if s.get("kind") == "assign" and _expr(s).get("kind") == "literal"]
    ra["CO_GAN_HANG_SO"] = bool(hang)
    ra["KET_QUA_KHAI_SAN"] = bool(
        dich and (khai.get(dich) or {}).get("initial_value") is not None)
    ra["KHONG_DUONG_TAT"] = not (ra["CO_GAN_HANG_SO"] or ra["KET_QUA_KHAI_SAN"])

    # ── BẢNG MẶT ────────────────────────────────────────────────────────
    if khoi is None:
        ra["FACE_TABLE_VALID"] = "FAIL"
        ra["ly_do_bang_mat"] = "không có `construct_solid`"
    else:
        dinh_ct = [str(x) for x in (khoi.get("vertices") or [])]
        ra["SO_DINH_KHAI"] = len(dinh_ct)
        mc = _mat_chuan(khoi.get("faces"), dinh_ct, anh_xa)
        if mc is None:
            ra["FACE_TABLE_VALID"] = "FAIL"
            ra["ly_do_bang_mat"] = "bảng mặt không đọc được"
        else:
            ra["BANG_MAT_CHUAN"] = mc
            ra.update(cham_bang_mat(mc))

    # ── Phép đo trỏ ĐÚNG CHỦ THỂ ────────────────────────────────────────
    ra["DO_DUNG_CHU_THE"] = bool(
        do and khoi and _expr(do).get("of") == khoi.get("target_var"))
    ra["MEASURE_QUANTITY"] = _expr(do).get("quantity") if do else None

    ra["SYNTHESIS_STRUCTURE_CORRECT"] = "PASS" if all((
        ra["USES_CONSTRUCT_SOLID"], ra["USES_MEASURE_VOLUME"],
        ra["CO_DU_SAU_DINH"], ra["MOI_DIEM_CO_XUAT_XU"],
        ra["KHONG_DUONG_TAT"], ra["DO_DUNG_CHU_THE"],
        ra.get("FACE_TABLE_VALID") == "PASS")) else "FAIL"
    return ra
