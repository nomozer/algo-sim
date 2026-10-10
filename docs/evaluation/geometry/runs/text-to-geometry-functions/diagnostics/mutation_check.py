"""Kiểm đột biến cho test text-to-functions: mỗi đột biến PHẢI làm ít nhất một test đỏ. Chạy từ backend/."""
import sys
from fractions import Fraction

sys.path.insert(0, ".")
import pytest
from app.simulation.geometry_functions import engine as EN, registry as RG

T = "tests/geometry/test_text_to_geometry_functions.py"


def m_foot_centre(m):
    goc = EN._Dung._dat_ngoai_day
    def sai(self, ten, chan, h2, luat, calls):
        if luat.startswith("perpendicular"):
            base = [p for p in self.pts if self.trong_day(p)]
            o = tuple(sum(self.pts[p][i] for p in base) / len(base) for i in range(3))
            self.pts["__o"] = o
            return goc(self, ten, "__o", h2, luat, calls)
        return goc(self, ten, chan, h2, luat, calls)
    m.setattr(EN._Dung, "_dat_ngoai_day", sai)


def m_no_verify(m):
    m.setattr(EN._Dung, "kiem", lambda self: None)


def m_no_predicate(m):
    m.setattr(RG, "REGISTRY", {k: RG.FunctionSpec(v.name, v.args, v.kind, v.description, (), v.value_fields)
                               for k, v in RG.REGISTRY.items()})


def m_hex_sign(m):
    goc = EN.regular_polygon_chart
    def sai(k, s2):
        p, G = goc(k, s2)
        return (p, ((G[0][0], -G[0][1]), (-G[1][0], G[1][1]))) if k == 6 else (p, G)
    m.setattr(EN, "regular_polygon_chart", sai)


def m_plan_order(m):
    m.setattr(EN, "_key", lambda c: 0)


def m_value_not_checked(m):
    goc = RG.binh_phuong
    m.setattr(RG, "so_trong", lambda q: [Fraction(-1)])
    m.setattr(RG, "kiem_nguon", lambda calls, text: None)


class Plug:
    def __init__(self, f):
        self.f = f
    def pytest_configure(self, config):
        self.m = pytest.MonkeyPatch()
        self.f(self.m)
    def pytest_unconfigure(self, config):
        self.m.undo()


bad = 0
for f in (m_foot_centre, m_no_verify, m_no_predicate, m_hex_sign, m_plan_order, m_value_not_checked):
    rc = pytest.main([T, "-q", "-p", "no:cacheprovider", "--no-header", "-x", "--tb=no"], plugins=[Plug(f)])
    caught = rc != 0
    bad += not caught
    print(f"MUTATION {f.__name__}: {'CAUGHT' if caught else 'NOT CAUGHT'}", flush=True)
print("ALL CAUGHT" if not bad else f"{bad} NOT CAUGHT")
