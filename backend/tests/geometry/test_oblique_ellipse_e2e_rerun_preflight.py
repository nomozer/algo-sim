# -*- coding: utf-8 -*-
"""`OBLIQUE_ELLIPSE_FRESH_E2E_RERUN` — tiền kiểm §4 + replay §5. 0 lượt gọi.

Wave DỪNG TRƯỚC PROVIDER. §4 nói rõ điều kiện dừng — *"nếu gold hoặc đường
radius trực tiếp chưa đạt, kết thúc trước provider và báo blocker tất định"* —
và đường ấy **chưa đạt**, vì một lỗi trong mã sản phẩm chứ không phải vì
fixture.

─── VÌ SAO DỪNG LÀ ĐÚNG, KHÔNG PHẢI QUÁ CẨN THẬN ──────────────────────────

§10 bắt phải **chứng minh bằng chữ ký** rằng hình trụ có đường hợp lệ
`radius + height` trước khi rút ca, rồi mới đọc được việc mô hình tự bịa
`rim_point` là *"lựa chọn của chương trình, không phải yêu cầu của hệ"*.

Phép đo dưới đây **bác chính tiền đề ấy** cho phép giao elip: hình trụ khai
bằng `(bán kính, chiều cao)` **không bao giờ** cắt ra được elip. Chạy lượt live
với một tiền đề sai thì mọi kết luận về `rim_point` mất giá trị — đúng lớp lỗi
*"bộ đo không nằm trên đường chạy thật"* mà kho này đã trả giá hai lần.
"""
from __future__ import annotations

import copy
import json
import sys
from fractions import Fraction as F
from pathlib import Path

import pytest

from app.simulation.geometry import curved as CV
from app.simulation.geometry.exact import GeometryError, Plane3, Vec3
from app.simulation.geometry.radical import display, is_exact_number
from app.simulation.semantic_program.contract import SemanticProgramSpec
from app.simulation.semantic_program.plane_equation import bat_bien_mat_phang
from app.simulation.semantic_program.request_contract import RequestContract
from app.simulation.semantic_program.route import verify_and_compile

GOC = Path(__file__).resolve().parents[2]
if str(GOC / "scripts") not in sys.path:
    sys.path.insert(0, str(GOC / "scripts"))

from gold_oblique_ellipse_fresh import (  # noqa: E402
    GOLD, PROBLEM_TEXT, REQUEST_CONTRACT_GOLD, WITNESS,
)

DAP_SO = "16π√5"
MP = {"kind": "construct_plane_from_equation", "target_var": "alpha",
      "a": 2, "b": 0, "c": -1, "d": 10, "label": "(α)"}


def v(x, y, z) -> Vec3:
    return Vec3(F(x), F(y), F(z))


def _hd(voi_bat_bien: bool = True) -> RequestContract:
    c = RequestContract.model_validate(REQUEST_CONTRACT_GOLD)
    if voi_bat_bien:
        c = c.model_copy(update={
            "source_invariants": tuple(c.source_invariants or ())
            + bat_bien_mat_phang(c, PROBLEM_TEXT)})
    return c


def _gold_phep_moi(**doi_mp) -> dict:
    """Gold, mặt phẳng dựng bằng `construct_plane_from_equation`."""
    g = copy.deepcopy(GOLD)
    g["memory_declarations"] = [d for d in g["memory_declarations"]
                                if d["name"] not in ("P1", "P2", "P3")]
    lenh = dict(MP)
    lenh.update(doi_mp)
    g["statements"] = [lenh if s.get("kind") == "construct_plane" else s
                       for s in g["statements"]]
    return g


def _chay(p: dict, voi_bat_bien: bool = True):
    return verify_and_compile(_hd(voi_bat_bien),
                              SemanticProgramSpec.model_validate(p))


def _dap_so(kq) -> str | None:
    dl = {k: display(x) for k, x in (kq.final_memory or {}).items()
          if is_exact_number(x)}
    return dl.get(WITNESS)


# ══ §4 · GOLD ĐI TRỌN ĐƯỜNG ═════════════════════════════════════════════
def test_01_gold_bang_phep_moi_di_tron_duong():
    kq = _chay(_gold_phep_moi())
    assert kq.servable, (kq.error_code, kq.stage_reached)
    assert kq.stage_reached == "served"
    assert _dap_so(kq) == DAP_SO
    assert kq.source_invariant_stats["checked"] == 1
    assert kq.source_invariant_stats["passed"] == 1
    assert kq.source_invariant_stats["violated"] == 0


def test_02_trace_va_scene3d_cua_gold():
    from app.ai.pipeline import _dung_scene3d

    canh = _dung_scene3d(
        SemanticProgramSpec.model_validate(_gold_phep_moi()), _hd()) or {}
    vat = {str(o.get("id")): o for o in canh.get("objects", [])}
    assert vat["alpha"]["type"] == "plane3"
    assert vat["alpha"]["producer"] == "construct_plane_from_equation"
    assert any(o.get("type") == "ellipse3" for o in vat.values())
    buoc = [e for e in canh["events"] if e.get("object") == "alpha"]
    assert len(buoc) == 1 and buoc[0]["action"] == "CREATE"
    assert "2x - z + 10 = 0" in buoc[0]["explanation"]


# ══ §4 · BẢY PHẢN VÍ DỤ ═════════════════════════════════════════════════
def test_03_pv1_sai_d__cung_dien_tich_nhung_SAI_VI_TRI():
    """`2x − z + 11 = 0` song song ⇒ elip BẰNG HỆT. Chỉ bất biến nguồn bắt."""
    kq = _chay(_gold_phep_moi(d=11))
    assert not kq.servable
    assert kq.source_invariant_stats["violated"] == 1
    assert _dap_so(kq) == DAP_SO          # đáp số ĐÚNG — đó là điểm của ca này


def test_04_pv2_mat_phang_suy_bien():
    with pytest.raises(Exception) as e:
        SemanticProgramSpec.model_validate(_gold_phep_moi(a=0, b=0, c=0, d=5))
    assert "(0, 0, 0)" in str(e.value)


def test_05_pv3_sai_he_so():
    assert not _chay(_gold_phep_moi(a=3)).servable


def test_06_pv4_mat_phang_SONG_SONG_truc():
    """`x = 3` ∥ trục Oz ⇒ giao là cặp đường sinh, NGOÀI bao đóng v1."""
    s = CV.CurvedSolid("cylinder", v(0, 0, 0), v(0, 0, 20), None, F(16))
    with pytest.raises(GeometryError) as e:
        CV.intersect_plane_curved_ellipse(
            s, Plane3.from_equation(F(1), F(0), F(0), F(-3)))
    assert e.value.code == CV.ERR_ELIP_NGOAI_BAO_DONG
    assert "SONG SONG" in str(e.value)


def test_07_pv5_elip_VUOT_hai_day():
    """Trụ thấp ⇒ elip bị đáy cắt. Đây là ca `CROSSES_CAP` ĐÚNG."""
    s = CV.CurvedSolid("cylinder", v(0, 0, 0), v(0, 0, 4), None, F(16))
    with pytest.raises(GeometryError) as e:
        CV.intersect_plane_curved_ellipse(
            s, Plane3.from_equation(F(2), F(0), F(-1), F(2)))
    assert e.value.code == CV.ERR_ELIP_CAT_DAY


def test_08_pv6_diem_vanh_KHONG_co_xuat_xu():
    """Điểm vành bịa ⇒ grounding từ chối. Lớp `ball_2`, có sẵn từ trước."""
    from app.simulation.semantic_program.grounding_gate import check_grounding

    g = _gold_phep_moi()
    g["memory_declarations"] = [d for d in g["memory_declarations"]
                                if d["name"] != "r"]
    g["memory_declarations"].append(
        {"name": "P_rim", "type": "point3", "initial_value": [4, 0, 0],
         "model_assumption": "Chọn một điểm trên vành đáy dưới."})
    for s in g["statements"]:
        if s.get("kind") == "construct_curved_solid":
            s.pop("radius", None)
            s["rim_point"] = "P_rim"
    r = check_grounding(_hd(), SemanticProgramSpec.model_validate(g))
    assert not r.ok
    assert r.error_code == "UNANCHORED_DERIVED_ASSUMPTION"


# ══ §4 · PHẢN VÍ DỤ ⑦ — ĐƯỜNG `radius + height` TRỰC TIẾP ═══════════════
#
# ⚠️ ĐÂY LÀ CHỖ WAVE DỪNG LẠI. Hai khẳng định, đo riêng, đừng trộn.
def test_09_pv7a_khai_chieu_cao_bang_HANG__grounding_tu_choi_DUNG():
    """Đề cho tâm đáy trên là ĐIỂM, không cho chiều cao. `h = 20` không neo được.

    Đây KHÔNG phải lỗi — grounding hỏi đúng câu *"anh lấy số 20 ở đâu ra"*, và
    `(0,0,20)` là một TOẠ ĐỘ, không phải một độ dài đề cho. Ghi lại để phân
    biệt với lỗi thật ở test sau.
    """
    from app.simulation.semantic_program.grounding_gate import check_grounding

    g = _gold_phep_moi()
    g["memory_declarations"] = [d for d in g["memory_declarations"]
                                if d["name"] != "Oprime"]
    g["memory_declarations"].append(
        {"name": "h", "type": "float", "initial_value": 20,
         "source_fact_id": "tam_day_tren"})
    for s in g["statements"]:
        if s.get("kind") == "construct_curved_solid":
            s.pop("apex_or_top", None)
            s["height"] = "h"
    r = check_grounding(_hd(), SemanticProgramSpec.model_validate(g))
    assert not r.ok
    assert any(x.startswith("h|") and "không có trong mục" in x
               for x in r.unjustified_literals)


def test_10_pv7b_tru_khai_bang_radius_height_CAT_RA_elip_y_HET_hai_diem():
    """⚠️ **KHẲNG ĐỊNH ĐÃ ĐẢO CHIỀU, 2026-09-07** —
    `CURVED_SCALAR_AXIS_SCALE_REPAIR`.

    Bản trước tên là `…_KHONG_cat_ra_elip` và **khoá đúng một lỗi**: hình trụ
    khai bằng `(bán kính, chiều cao)` luôn bị `CURVED_ELLIPSE_CROSSES_CAP`.
    Nó tự khai sẽ đỏ khi lỗi được sửa, và nó đã đỏ — làm đúng việc của nó cho
    tới lúc bị bác bằng một bản vá.

    ─── LỖI ĐÃ ĐƯỢC PROBE TÌM RA THẾ NÀO (giữ lại làm lịch sử) ────────────

    `OBLIQUE_ELLIPSE_FRESH_E2E_RERUN` dừng trước provider vì §4 đòi đường
    `radius + height` phải đi được. Đo ra:

        L    = (tâm − anchor)·u / (u·u)
        tren = 1 − L                      ← chỉ đúng khi |u| = h

    `huong_truc` trả `truc` (`|u| = h`) ở nhánh ĐIỂM nhưng vectơ ĐƠN VỊ ở
    nhánh VÔ HƯỚNG, nên `L` là **tỉ lệ** ở nhánh đầu và **khoảng cách tuyệt
    đối** ở nhánh sau: `L = 10` ⇒ `tren = −9`.

    Nay phép kiểm đáy trên hỏi `h − duoi ≥ h_half` bằng số hữu tỉ thuần
    (`_con_cho_toi_day_tren`), nên hai cách khai cho **cùng một** phán quyết.
    Test này giữ nguyên tiền đề *"hai khối bằng nhau về hình"* — nó là thứ làm
    khẳng định có nghĩa — và đổi kết luận.
    """
    A = CV.CurvedSolid("cylinder", v(0, 0, 0), v(0, 0, 20), None, F(16))
    B = CV.CurvedSolid("cylinder", v(0, 0, 0), None, None, F(16),
                       height_sq_khai=F(400))
    assert A.radius_sq == B.radius_sq == F(16)
    assert A.height_sq == B.height_sq == F(400)
    assert A.huong_truc.cross(B.huong_truc).is_zero()

    mp = Plane3.from_equation(F(2), F(0), F(-1), F(10))
    eA = CV.intersect_plane_curved_ellipse(A, mp)
    eB = CV.intersect_plane_curved_ellipse(B, mp)
    assert display(CV.dien_tich_elip(eA)) == DAP_SO
    assert display(CV.dien_tich_elip(eB)) == DAP_SO
    assert eA.center == eB.center
    assert eA.semi_major_sq == eB.semi_major_sq
    assert eA.semi_minor_sq == eB.semi_minor_sq


def test_11_doi_chung__duong_TRON_dung_o_CA_HAI_nhanh():
    """Khoanh vùng: chỉ phép ELIP hỏng, `intersect_plane_curved` thì không."""
    A = CV.CurvedSolid("cylinder", v(0, 0, 0), v(0, 0, 20), None, F(16))
    B = CV.CurvedSolid("cylinder", v(0, 0, 0), None, None, F(16),
                       height_sq_khai=F(400))
    ngang = Plane3.from_equation(F(0), F(0), F(1), F(-10))
    assert CV.intersect_plane_curved(A, ngang).radius_sq == F(16)
    assert CV.intersect_plane_curved(B, ngang).radius_sq == F(16)


def test_12_moi_chieu_cao_deu_PARITY_hai_nhanh():
    """Bản trước khẳng định *"nhánh vô hướng đóng với MỌI chiều cao"* — đúng
    lúc ấy, sai từ khi có bản vá. Nay hỏi câu mạnh hơn: **cùng phán quyết**.

    Không chỉ *"cả hai cùng ra elip"* — với `h` nhỏ thì cả hai phải cùng TỪ
    CHỐI, và đó mới là parity. Một bản vá chỉ mở nhánh vô hướng mà quên phép
    kiểm sẽ xanh ở nửa đầu và đỏ ở nửa sau.
    """
    mp = Plane3.from_equation(F(2), F(0), F(-1), F(10))
    for h2 in (F(100), F(400), F(1600), F(2500)):
        h = CV.sqrt_rational(h2)
        A = CV.CurvedSolid("cylinder", v(0, 0, 0), v(0, 0, h), None, F(16))
        B = CV.CurvedSolid("cylinder", v(0, 0, 0), None, None, F(16),
                           height_sq_khai=h2)
        ra = []
        for s_ in (A, B):
            try:
                ra.append(display(CV.dien_tich_elip(
                    CV.intersect_plane_curved_ellipse(s_, mp))))
            except GeometryError as e:
                ra.append(e.code)
        assert ra[0] == ra[1], (h2, ra)


# ══ §10 · TIỀN ĐỀ CỦA GIẢ THUYẾT ĐIỂM VÀNH — BỊ BÁC ═════════════════════
def test_13_tien_de_cua_gia_thuyet_diem_vanh_NAY_DUNG():
    """⚠️ **KHẲNG ĐỊNH ĐÃ ĐẢO CHIỀU**, cùng wave với `test_10`.

    Bản trước ghi rằng `height` **vắng** ở `_TOAN_HANG_LENH` và `O_TEN`, nên
    §10 của brief lượt ấy — *"chứng minh bằng chữ ký rằng `radius + height` là
    đường hợp lệ"* — **thất bại**, và lượt live phải dừng.

    `CURVED_SCALAR_AXIS_SCALE_REPAIR` đóng cả hai: một dòng thêm vào
    `_TOAN_HANG_LENH` làm `O_TEN` (dẫn xuất) và thẻ văn phạm (dẫn xuất tiếp)
    tự đúng theo. Nay tiền đề ấy ĐỨNG, và lượt live mở lại được.
    """
    from app.simulation.semantic_program.hoisting import O_TEN
    from app.simulation.semantic_program.ir_static_check import _TOAN_HANG_LENH

    o = _TOAN_HANG_LENH["construct_curved_solid"]
    ht = next(t for t in o if t[0] == "height")
    assert ht == ("height", ("scalar", "float", "int"), False)
    # `O_TEN` DẪN XUẤT — không chép tay, nên nó tự có.
    assert O_TEN["construct_curved_solid"]["height"] == (
        ("scalar", "float", "int"), False)
    # …và runtime vẫn đọc nó, y như trước.
    import inspect

    from app.simulation.semantic_program import geometry_exec as GE

    assert 'getattr(node, "height", None)' in inspect.getsource(
        GE.exec_construct_curved_solid)


def test_14_duong_hop_le_KHONG_bia_diem__hai_tam_co_ten_va_radius():
    """Đường gold: `anchor` + `apex_or_top` (cả hai đề đặt tên) + `radius`."""
    g = _gold_phep_moi()
    lenh = next(s for s in g["statements"]
                if s["kind"] == "construct_curved_solid")
    assert lenh["anchor"] == "O" and lenh["apex_or_top"] == "Oprime"
    assert lenh["radius"] == "r" and "rim_point" not in lenh
    assert _chay(g).servable


# ══ §5 · REPLAY LỊCH SỬ ═════════════════════════════════════════════════
def test_15_replay_lich_su_giu_nguyen_ket_qua():
    from replay_plane_from_equation import (
        hop_dong, minimal_delta, nap,
    )
    from app.simulation.semantic_program.ir_static_check import kiem_tinh

    tho, phan_tich = nap()
    hd = hop_dong(phan_tich)

    a1 = json.loads(tho[1])
    assert any(s["kind"] == "construct_plane_from_equation"
               for s in a1["statements"])          # PLANE_OPERATION
    s1 = SemanticProgramSpec.model_validate(a1)     # SCHEMA_VALID
    assert kiem_tinh(s1).ok                         # STATIC_VALID

    kq1 = verify_and_compile(hd, s1)
    assert not kq1.servable                         # RIM_POINT_FAILURE
    assert kq1.stage_reached == "grounding"

    delta, ly_do = minimal_delta(tho[1])
    assert len(ly_do) == 2                          # MINIMAL_DELTA_FIELDS
    kqd = verify_and_compile(
        hd, SemanticProgramSpec.model_validate(json.loads(delta)))
    assert kqd.servable                             # MINIMAL_DELTA_SERVABLE
    dl = {k: display(x) for k, x in (kqd.final_memory or {}).items()
          if is_exact_number(x)}
    assert dl.get("dien_tich_E") == DAP_SO

    a2 = SemanticProgramSpec.model_validate(json.loads(tho[2]))
    kq2 = verify_and_compile(hd, a2)
    assert not kq2.servable                         # ATTEMPT_2_GROUNDING
    assert kq2.stage_reached == "grounding"


# ══ §2 · DANH TÍNH ══════════════════════════════════════════════════════
def test_16_the_van_pham_co_du_nam_thu_wave_doi():
    from app.simulation.semantic_program.grammar_card import grammar_card

    the = grammar_card("hinh_hoc")
    for pat in ("construct_plane_from_equation",
                "intersect_plane_curved_ellipse",
                "ellipse3",
                "t = m/(m+n)",
                "Xuất xứ:"):
        assert pat in the, pat
    assert "area(of:tên<polygon3|section|circle3|ellipse3>)" in the
    # ⚠️ Bất đối xứng cũ ĐÃ ĐÓNG (`CURVED_SCALAR_AXIS_SCALE_REPAIR`): bản
    # trước `radius?` có kiểu + vai trò còn `height?:tên` trần. Nay cả hai
    # dẫn từ CÙNG một dòng của `_TOAN_HANG_LENH`.
    dong = next(d for d in the.splitlines()
                if "construct_curved_solid:" in d)
    assert "radius?:tên<scalar|float|int>[" in dong
    assert "height?:tên<scalar|float|int>[" in dong


def test_17_danh_tinh_on_dinh_trong_wave():
    from app.main import CACHE_VERSION
    from app.runtime_identity import semantic_environment_fingerprint

    # ⚠️ Cập nhật theo `CURVED_SCALAR_AXIS_SCALE_REPAIR` (2026-09-07): lượt
    # đo của wave NÀY đã đóng, nên ô ghim chuyển sang danh tính hiện hành.
    # ⚠️ 91 → 92 (`NONCONVEX_POLYHEDRON_VOLUME_FOUNDATION`, cùng ngày). Bump ấy
    # KHÔNG đụng bề mặt mô hình — năm băm dưới đây giữ nguyên từng byte, và
    # chúng mới là thứ ô này bảo vệ.
    # ⚠️ 92 → 93 (`POINT_COORDINATE_SOURCE_INVARIANT`, 2026-09-08). Bump ấy
    # cũng KHÔNG đụng bề mặt mô hình — năm băm dưới đây giữ nguyên từng byte,
    # và chúng mới là thứ ô này bảo vệ.
    # ⚠️ 94 → 95 (`DISPLAY_NAME_FINAL_POLISH_AND_RELEASE_REFRESH`, 2026-09-10):
    #    bump vì NỘI DUNG envelope `ok` đổi (nhãn `ellipse3`), **không** vì
    #    bề mặt mô hình — năm băm model-facing giữ nguyên từng byte, và
    #    chúng mới là thứ ô này bảo vệ.
    assert CACHE_VERSION == "95"
    fp = semantic_environment_fingerprint()
    mong = {
        "prompts": "55ac1ca6a6df92ce",
        # ⚠️ cc105e4f → 6cbba188 (wave nón). Ghim giá trị HIỆN HÀNH:
        # ô này nói về hệ đang chạy, không về một lượt đo đông cứng.
        "grammar_card": "6cbba1885b2073fa",
        "synthesis_schema": "08dae8dc5a90bcae",
        "analyze_schema": "515001b503af5c7c",
        "capability": "72edf39f6c10220d",
    }
    for k, b in mong.items():
        assert fp[k].startswith(b), (k, fp[k][:16])
