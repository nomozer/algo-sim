# -*- coding: utf-8 -*-
"""Vòng đệm chẩn đoán phải GIỮ ĐƯỢC JSON — kể cả khi lượt chạy là hình học.

─── VÌ SAO TỒN TẠI, ĐO ĐƯỢC Ở LƯỢT LIVE 2026-08-25 ────────────────────────────

Sau khi deploy đúng bản, đề hình học đơn giản chạy trọn và trả envelope `ok` kèm
`scene3d`. Rồi `GET /api/diagnostics/semantic` trả **500**:

    ValueError: [TypeError("'Fraction' object is not iterable"),
                 TypeError('vars() argument must have __dict__ attribute')]

Thủ phạm là `_emit(observer, "semantic_route", ..., final_memory=...)`. Bộ nhớ
cuối của interpreter hình học chứa `Fraction`, `Vec3`, `Line3`, `Plane3`; và
`final_memory` **phải** nằm đó — comment tại chỗ phát nói rõ nó là thứ DUY NHẤT
đem so được với ground truth độc lập, thiếu nó thì benchmark chấm 0 case.

Nên lỗi này có một hình dạng đặc biệt hiểm: `semantic_route` chỉ phát
`final_memory` khi route đi đủ xa, tức **công cụ chẩn đoán mù đúng vào lúc hình
học CHẠY ĐƯỢC**. Lượt hỏng thì đọc được vết, lượt chạy được thì 500 — ngược hẳn
với thứ ta cần khi đang đo một miền mới.

Quy ước chuyển đổi lấy đúng của `scene3d` (*"mọi số là chuỗi phân số CHÍNH
XÁC"*): `Fraction` → chuỗi `"5/2"`, không hoá float. Vòng đệm là công cụ chẩn
đoán, nên nó KHÔNG được phép tự giết mình vì một kiểu dữ liệu lạ.
"""

import json
from fractions import Fraction

import pytest
from fastapi.testclient import TestClient

from app.ai.route_trace import DiagnosticObserver, lan_gan_nhat, xoa_het
from app.main import app
from app.simulation.geometry.exact import Line3, Plane3, Vec3

client = TestClient(app)


@pytest.fixture(autouse=True)
def kho_sach():
    xoa_het()
    yield
    xoa_het()


def _bo_nho_hinh_hoc() -> dict:
    """Đúng hình dạng `final_memory` mà interpreter hình học trả về."""
    A = Vec3.of(0, 0, 0)
    B = Vec3.of(4, 0, 0)
    return {
        "A": A,
        "B": B,
        "M": Vec3.of(2, 0, Fraction(5, 2)),
        "AB_line": Line3.through(A, B),
        "plane_ABCD": Plane3.through(A, B, Vec3.of(4, 4, 0)),
        "khoang_cach": Fraction(5, 2),
        "canh": 4,
    }


def test_ban_ghi_mang_Fraction_van_dumps_duoc():
    obs = DiagnosticObserver("Cho hình chóp S.ABCD…")
    obs.emit("semantic_route", {
        "stage_reached": "served",
        "executable": True,
        "final_memory": _bo_nho_hinh_hoc(),
    })
    obs.ket_thuc({"status": "ok", "simulation_id": "generic.semantic_program"})

    # Nếu vòng đệm còn giữ `Fraction` thô thì đây là chỗ nổ.
    json.dumps(lan_gan_nhat(1), ensure_ascii=False)


def test_Fraction_thanh_chuoi_phan_so_CHINH_XAC_khong_hoa_float():
    """`5/2` phải ra `"5/2"`. Hoá `2.5` là mất tính chính xác hữu tỉ — đúng thứ
    lõi hình học tồn tại để giữ."""
    obs = DiagnosticObserver("đề")
    obs.emit("semantic_route", {"final_memory": {"d": Fraction(5, 2)}})
    obs.ket_thuc(None)

    ban_ghi = lan_gan_nhat(1)[0]
    assert ban_ghi["su_kien"][0]["data"]["final_memory"]["d"] == "5/2"


def test_doi_tuong_hinh_hoc_giu_duoc_TUNG_TOA_DO():
    """`Vec3` → dict toạ độ, không phải một chuỗi `repr` đọc không ra."""
    obs = DiagnosticObserver("đề")
    obs.emit("semantic_route", {"final_memory": {"M": Vec3.of(2, 0, Fraction(5, 2))}})
    obs.ket_thuc(None)

    M = lan_gan_nhat(1)[0]["su_kien"][0]["data"]["final_memory"]["M"]
    assert M == {"x": "2", "y": "0", "z": "5/2"}


def test_kieu_LA_hoac_khong_dumps_duoc_thi_ve_repr_chu_KHONG_nem():
    """Công cụ chẩn đoán không được tự giết mình vì một kiểu chưa ai lường."""
    class KieuLa:
        __slots__ = ("v",)

        def __init__(self):
            self.v = 1

        def __repr__(self):
            return "<KieuLa>"

    obs = DiagnosticObserver("đề")
    obs.emit("semantic_route", {"final_memory": {"x": KieuLa()}})
    obs.ket_thuc(None)

    json.dumps(lan_gan_nhat(1), ensure_ascii=False)


def test_endpoint_chan_doan_KHONG_500_khi_luot_hinh_hoc_chay_duoc(monkeypatch):
    """Test HỒI QUY của chính sự cố: trước bản vá, đây là 500."""
    monkeypatch.setenv("SEMANTIC_TELEMETRY", "1")
    obs = DiagnosticObserver("Cho hình chóp S.ABCD…")
    obs.emit("semantic_route", {
        "stage_reached": "served",
        "final_memory": _bo_nho_hinh_hoc(),
    })
    obs.ket_thuc({"status": "ok", "simulation_id": "generic.semantic_program"})

    res = client.get("/api/diagnostics/semantic")
    assert res.status_code == 200, res.text
    assert res.json()["ban_ghi"][0]["su_kien"][0]["data"]["final_memory"]["khoang_cach"] == "5/2"
