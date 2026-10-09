# -*- coding: utf-8 -*-
"""G05 real-model pilot — bộ chấm CHÍNH XÁC (G1) và phân loại kết cục (G3). offline · **0 API call**.

─── G1 · VÌ SAO KHÔNG DÙNG `Fraction(str(...))` ────────────────────────────────
`final_memory` giữ `Radical(he, can, mu)` chính tắc; bộ chấm cũ (`run_geometry_dev_evaluation.cham_oracle`) gọi
`Fraction(str(may))` ⇒ mọi đáp số có căn bị chấm FAIL "không so được" — đổ lỗi cho mô hình một thiếu sót của bộ đo
(`runs/real-model-e2e-readiness/report.md` §4 G1). Ở đây mọi số — nhãn `"3√3/4"`, `Fraction`, `int`, `Radical`, hay chuỗi
hiển thị — về CÙNG một khoá chính xác `(mu, dấu, giá trị²)`; so khoá, không so chuỗi, không dung sai float.
`float` không phải số chính xác ⇒ `None` (KHÔNG chấm được), không phải `False`.

─── G3 · THỨ TỰ PHÂN LOẠI ────────────────────────────────────────────────────
lỗi provider > dừng lượt > lỗi công cụ > thất bại TRƯỚC khi có IR (analyze/program) > kết cục route.
"Từ chối đúng" chỉ khi một cổng TẤT ĐỊNH sau IR (hoặc cổng phạm vi) từ chối đề phải từ chối; timeout, lỗi API, lỗi
hệ thống, lỗi lược đồ của mô hình KHÔNG BAO GIỜ là từ chối đúng.
"""
from __future__ import annotations

import re
from fractions import Fraction
from typing import Any

CATEGORIES = ("SERVED_CORRECT", "SERVED_WRONG", "REFUSED_CORRECT", "REFUSED_WRONG", "PROVIDER_ERROR",
              "PARSER_SCHEMA_ERROR", "TOOL_ERROR", "UNGRADABLE", "RUN_STOPPED", "NOT_RUN")
#: Chặng mà ở đó chưa có chương trình thực thi được: hỏng ở đây là hỏng của bước SINH, không phải phán quyết của cổng.
TRUOC_IR = (None, "semantic_analyze", "semantic_program")

_SO = re.compile(r"^(?P<dau>[-−])?(?P<he>\d+(?:/\d+)?)?(?P<pi>π)?(?:√(?P<can>\d+))?(?:/(?P<mau>\d+))?$")


def gia_tri_nhan(s: str) -> tuple[int, int, Fraction]:
    """Chuỗi số chính xác (`18√3`, `3√3/4`, `√3`, `2/3`, `12`, `2π`) → `(mu, dấu, giá trị²)`. Sai dạng ⇒ `ValueError`."""
    m = _SO.match(s.strip().replace(" ", ""))
    if not m or not (m["he"] or m["can"] or m["pi"]):
        raise ValueError(f"không phải số chính xác: {s!r}")
    he = Fraction(m["he"] or 1) / Fraction(m["mau"] or 1)
    bp = he * he * int(m["can"] or 1)
    dau = 0 if bp == 0 else (-1 if m["dau"] else 1)
    return (1 if m["pi"] else 0), dau, bp


def khoa_chinh_xac(x: Any) -> tuple[int, int, Fraction] | None:
    """Giá trị máy → khoá chính xác, hoặc `None` khi KHÔNG phải số chính xác (float, bool, vật thể…)."""
    from app.simulation.geometry.radical import Radical

    if isinstance(x, bool) or x is None:
        return None
    if isinstance(x, Radical):
        bp = x.he * x.he * x.can
        return x.mu, (0 if bp == 0 else (1 if x.he > 0 else -1)), bp
    if isinstance(x, (int, Fraction)):
        q = Fraction(x)
        return 0, (q > 0) - (q < 0), q * q
    if isinstance(x, str):
        try:
            return gia_tri_nhan(x)
        except ValueError:
            return None
    return None


def bang_nhau(may: Any, nhan: str) -> bool | None:
    """`True`/`False` khi so được CHÍNH XÁC; `None` khi giá trị máy không phải số chính xác. Nhãn hỏng ⇒ `ValueError`."""
    mong = gia_tri_nhan(nhan)
    k = khoa_chinh_xac(may)
    return None if k is None else k == mong


def bang_nhau_binh_phuong(v2: Fraction, nhan: str) -> bool:
    """Một đại lượng DƯƠNG cho bằng bình phương `v2` có bằng nhãn không (oracle công thức sách)."""
    return gia_tri_nhan(nhan) == (0, 1, Fraction(v2))


def binh_phuong(nhan: str) -> Fraction:
    mu, _d, bp = gia_tri_nhan(nhan)
    if mu:
        raise ValueError(f"kích thước có π: {nhan!r}")
    return bp


def chieu_cao_binh_phuong(case: dict) -> Fraction | None:
    """h² mà ĐỀ cố định (chiều cao, hoặc cạnh bên: lăng trụ đứng ⇒ = h; chóp đều ⇒ l² − R²). `None` = đề không cho."""
    d, b2, k = case["dims"], binh_phuong(case["base_side"]), case["k"]
    if "height" in d:
        return binh_phuong(d["height"])
    if "lateral" in d:
        l2 = binh_phuong(d["lateral"])
        if case["family"] == "prism":
            return l2
        r2 = b2 if k == 6 else b2 / 3                       # bán kính ngoại tiếp² của lục giác / tam giác đều
        return l2 - r2
    return None


def v2_cong_thuc(case: dict) -> Fraction:
    """V² theo CÔNG THỨC SÁCH, chỉ từ kích thước của đề — không chạm mã sản phẩm."""
    b2, k = binh_phuong(case["base_side"]), case["k"]
    if case["family"] == "tetrahedron":
        return b2 ** 3 / 72                                  # V = a³/(6√2)
    s2 = {6: Fraction(27, 4), 3: Fraction(3, 16)}[k] * b2 * b2   # diện tích đáy²: (3√3/2 b²)², (√3/4 b²)²
    h2 = chieu_cao_binh_phuong(case)
    return s2 * h2 if case["family"] == "prism" else s2 * h2 / 9


def phan_loai(expect: str, rec: dict) -> dict:
    """Một lượt → một hạng trong `CATEGORIES`, kèm chi tiết. `expect` = `served:<số>` | `refused[:<chặng>[:…]]`."""
    duong = expect.startswith("served:")
    chang_nhan = expect.split(":")[1] if expect.startswith("refused:") else None
    ra = {"category": None, "detail": None, "ground": None, "label_stage_match": None}
    if rec.get("provider_errors"):
        ra.update(category="PROVIDER_ERROR", detail=rec["provider_errors"][-1])
    elif rec.get("run_stop"):
        ra.update(category="RUN_STOPPED", detail=rec["run_stop"])
    elif rec.get("su_co"):
        ra.update(category="TOOL_ERROR", detail=rec["su_co"])
    elif rec.get("envelope_status") == "ok" and rec.get("servable"):
        if not duong:
            ra.update(category="SERVED_WRONG", detail="đề phải từ chối nhưng được phục vụ")
        else:
            eq = bang_nhau(rec.get("value"), expect.split(":", 1)[1])
            ra.update(category={True: "SERVED_CORRECT", False: "SERVED_WRONG", None: "UNGRADABLE"}[eq],
                      detail=f"máy={rec.get('value')!s} nhãn={expect.split(':', 1)[1]}")
    elif rec.get("stage_reached") in TRUOC_IR:
        ra.update(category="PARSER_SCHEMA_ERROR", detail=f"{rec.get('stage_reached')}: {rec.get('error_code')}")
    elif duong:
        ra.update(category="REFUSED_WRONG", ground=rec.get("stage_reached"),
                  detail=f"{rec.get('stage_reached')}: {rec.get('error_code')}")
    else:
        ra.update(category="REFUSED_CORRECT", ground=rec.get("stage_reached"),
                  detail=f"{rec.get('stage_reached')}: {rec.get('error_code')}",
                  label_stage_match=(chang_nhan == rec.get("stage_reached")) if chang_nhan else None)
    return ra
