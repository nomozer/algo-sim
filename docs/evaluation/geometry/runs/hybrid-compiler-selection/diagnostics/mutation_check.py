"""Kiểm đột biến nhánh B (hybrid-compiler-selection): mỗi lỗi cài sẵn PHẢI làm ít nhất một test đỏ. 0 API call. Chạy từ backend/."""
import sys

sys.path.insert(0, ".")
import pytest
from app.ai import function_route as FR
from app.simulation.geometry_functions import planner as PL

T = "tests/geometry/test_hybrid_compiler_selection.py"


def m(ten):
    def dk(f):
        f.ten = ten
        return f
    return dk


@m("điều phải chứng minh dùng làm giả thiết")
def m1(p):
    goc = PL.lap_ke_hoach

    def sai(raw):
        raw = {"facts": [dict(f, role="premise") if f.get("role") == "prove" else f for f in raw["facts"]]}
        return goc(raw)
    p.setattr(PL, "lap_ke_hoach", sai)
    p.setattr(FR, "run_fact_route", FR.run_fact_route)


@m("không kiểm mệnh đề phủ định sau khi dựng")
def m2(p):
    goc = PL.lap_ke_hoach

    def sai(raw):
        k = goc(raw)
        k.negated = []
        return k
    p.setattr(PL, "lap_ke_hoach", sai)


@m("mặt ⊥ mặt bất kỳ ánh xạ thành mặt bên ⊥ đáy (bỏ tiền điều kiện)")
def m3(p):
    goc = PL._anh_xa

    def sai(f, k, ten, deu, khoi_cua, phat):
        if f.kind == "perpendicular" and len(f.points_a) >= 3 and len(f.points_b) >= 3:
            return phat(f.id, "face_perpendicular_base", {"face": f.points_a[:3], "base": f.points_b}, list(f.quotes), "sai")
        return goc(f, k, ten, deu, khoi_cua, phat)
    p.setattr(PL, "_anh_xa", sai)


@m("'cạnh bên' của chóp KHÔNG đều vẫn gán cho SA")
def m4(p):
    goc = PL._do_dai

    def sai(f, q, deu, khoi_cua, phat):
        if f.measure == "lateral_edge":
            kh = khoi_cua(f.solid, f)
            return phat(f.id, "segment_length", {"segment": [kh.dinh or kh.day[0], kh.day[0]], "value": f.value}, q, "sai")
        return goc(f, q, deu, khoi_cua, phat)
    p.setattr(PL, "_do_dai", sai)


@m("hình không duy nhất: không chẩn đoán (để nguyên UNDERDETERMINED)")
def m5(p):
    p.setattr(FR, "_hinh_khong_duy_nhat", lambda k, thieu: None)


@m("bỏ từ chối mệnh đề điều kiện")
def m6(p):
    goc = PL.lap_ke_hoach

    def sai(raw):
        raw = {"facts": [dict(f, role="premise") if f.get("role") == "condition" else f for f in raw["facts"]]}
        return goc(raw)
    p.setattr(PL, "lap_ke_hoach", sai)


@m("bỏ mở rộng định nghĩa chóp đều ⇒ đáy đều")
def m7(p):
    goc = PL._doc_khoi

    def sai(f):
        kh = goc(f)
        if kh.loai == "pyramid":
            kh.deu = False
        return kh
    p.setattr(PL, "_doc_khoi", sai)


@m("điều phải chứng minh không kiểm trên hình (luôn coi là đúng)")
def m8(p):
    goc = FR.run_fact_route

    def sai(text, facts):
        r = goc(text, {"facts": [f for f in facts["facts"] if f.get("role") != "prove"]})
        return r
    p.setattr(FR, "run_fact_route", sai)


class Plug:
    def __init__(self, f):
        self.f = f

    def pytest_configure(self, config):
        self.p = pytest.MonkeyPatch()
        self.f(self.p)

    def pytest_unconfigure(self, config):
        self.p.undo()


bad = 0
for f in (m1, m2, m3, m4, m5, m6, m7, m8):
    rc = pytest.main([T, "-q", "-p", "no:cacheprovider", "--no-header", "-x", "--tb=no"], plugins=[Plug(f)])
    print(f"MUTATION {f.__name__} ({f.ten}): {'CAUGHT' if rc != 0 else 'NOT CAUGHT'}", flush=True)
    bad += rc == 0
print("ALL CAUGHT" if not bad else f"{bad} NOT CAUGHT")
