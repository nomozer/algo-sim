"""Kiểm đột biến (ai-function-route): mỗi lỗi cài sẵn PHẢI làm ít nhất một test đỏ. 0 API call. Chạy từ backend/."""
import sys
from fractions import Fraction

sys.path.insert(0, ".")
import pytest
from app.ai import function_calling as FC
from app.simulation.geometry_functions import engine as EN, registry as RG

T = "tests/geometry/test_ai_function_route.py"


def m(ten):
    def dk(f):
        f.ten = ten
        return f
    return dk


@m("vai trò mệnh đề bị bỏ (điều phải chứng minh / 'nếu' thành dữ kiện)")
def m1(p):
    p.setattr(RG, "_vai_tro", lambda de, vt: None)


@m("phủ định chỉ xét trong quote (như cổng v1)")
def m2(p):
    p.setattr(RG, "_phu_dinh", lambda de, vt, q: any(x in q.lower() for x in RG.PHU_DINH))


@m("bỏ kiểm tham chiếu mặt phẳng")
def m3(p):
    p.setattr(RG, "_co_mat", lambda quotes, mp, cho_day=True: True)


@m("bỏ kiểm vai trò điểm (ảnh hình chiếu)")
def m4(p):
    p.setattr(RG, "_co_diem_rieng", lambda quotes, ten, mp: True)


@m("bỏ tiền điều kiện chuẩn hoá đường cao/hình chiếu")
def m5(p):
    goc = EN._Dung._rang_buoc_vuong

    def long(self):
        for c in self.of("perpendicular_line_plane"):
            yield c, tuple(c.args.line), list(c.args.plane), "perpendicular_foot_at_", None
        for c in self.of("altitude"):
            k = self.khoi[c.args.solid]
            yield c, (c.args.apex, c.args.foot), list(k.base), "altitude_normalized_to_perpendicular_foot_at_", c.args.foot
        for c in self.of("orthogonal_projection"):
            yield c, (c.args.point, c.args.image), list(c.args.plane), "orthogonal_projection_normalized_to_perpendicular_foot_at_", c.args.image
    p.setattr(EN._Dung, "_rang_buoc_vuong", long)


@m("mặt bên ⊥ đáy: chân luôn tại trung điểm (giả định thay vì dẫn xuất)")
def m6(p):
    goc = EN._Dung._dat_ngoai_day

    def sai(self, ten, chan, h2, luat, calls):
        if luat.startswith("face_perpendicular_base") and not isinstance(chan, str):
            day = [v for v in self.pts if self.trong_day(v)]
            a, b = sorted(day)[:2]
            chan = tuple((self.pts[a][i] + self.pts[b][i]) / 2 for i in range(2))
        return goc(self, ten, chan, h2, luat, calls)
    p.setattr(EN._Dung, "_dat_ngoai_day", sai)


@m("bỏ kiểm đồng bậc độ dài ký hiệu")
def m7(p):
    p.setattr(EN, "_don_vi", lambda calls: "a" if any(RG.doc_so(getattr(c.args, f))[1] for c in calls
                                                       for f in c.spec.value_fields if getattr(c.args, f)) else None)


@m("định lý hai đường: nhận MỘT đường vuông góc")
def m8(p):
    goc = EN._Dung._hai_duong_cat_nhau

    def long(self):
        for c in self.of("perpendicular_lines"):
            L = c.args.line1
            p_, q = (L[0], L[1]) if L[0] not in self.pts else (L[1], L[0])
            if p_ not in self.pts and self.trong_day(q):
                h2, cs = self._chieu_cao(p_, q, [k.name for k in self.khoi.values() if k.apex == p_])
                self._dat_ngoai_day(p_, q, h2, "line_perpendicular_to_two_intersecting_lines_foot_at_" + q, {c.id} | cs)
                return True
        return False
    p.setattr(EN._Dung, "_hai_duong_cat_nhau", long)


@m("bỏ căn giá trị theo nhãn đoạn")
def m9(p):
    p.setattr(RG, "_so_neo", lambda quotes, seg: [])


@m("adapter thực thi phản hồi bị cắt (MAX_TOKENS)")
def m10(p):
    goc = FC.parse_response

    def sai(body, diag):
        for c in body.get("candidates") or []:
            if c.get("finishReason") == "MAX_TOKENS":
                c["finishReason"] = "STOP"
        return goc(body, diag)
    p.setattr(FC, "parse_response", sai)


@m("adapter cho chế độ AUTO")
def m11(p):
    p.setattr(FC, "MODES", ("ANY", "VALIDATED", "AUTO", "NONE", "any"))


@m("bỏ phát hiện mâu thuẫn độ dài giữa các nguồn")
def m12(p):
    goc = EN._Dung.do_dai

    def long(self, x, y, _suy=True):
        try:
            return goc(self, x, y, _suy)
        except RG.TuChoi:
            return [(Fraction(1), ())]
    p.setattr(EN._Dung, "do_dai", long)


class Plug:
    def __init__(self, f):
        self.f = f

    def pytest_configure(self, config):
        self.p = pytest.MonkeyPatch()
        self.f(self.p)

    def pytest_unconfigure(self, config):
        self.p.undo()


bad = 0
for f in (m1, m2, m3, m4, m5, m6, m7, m8, m9, m10, m11, m12):
    rc = pytest.main([T, "-q", "-p", "no:cacheprovider", "--no-header", "-x", "--tb=no"], plugins=[Plug(f)])
    print(f"MUTATION {f.__name__} ({f.ten}): {'CAUGHT' if rc != 0 else 'NOT CAUGHT'}", flush=True)
    bad += rc == 0
print("ALL CAUGHT" if not bad else f"{bad} NOT CAUGHT")
