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


def test_10_pv7b_LOI_THAT__tru_khai_bang_radius_height_KHONG_cat_ra_elip():
    """⛔ **CỔNG GAP — test này PHẢI ĐỎ khi lỗi được sửa.**

    Cùng MỘT hình trụ, hai cách khai, hai kết quả khác nhau:

        (A) hai điểm  `anchor=(0,0,0)`, `apex=(0,0,20)`, `r²=16` → ELIP, 16π√5
        (B) vô hướng  `anchor=(0,0,0)`, `r²=16`, `h²=400`       → TỪ CHỐI

    Hai khối **bằng nhau về hình**: `radius_sq` 16 = 16, `height_sq` 400 = 400,
    trục cùng phương Oz. Nên (B) phải cho đúng thứ (A) cho.

    ─── GỐC LỖI: MỘT BIỂU THỨC, `curved.py` ────────────────────────────────

        L    = (tâm − anchor)·u / (u·u)
        tren = 1 − L                      ← chỉ đúng khi |u| = h

    `huong_truc` trả `truc` (|u| = h) ở nhánh ĐIỂM, nhưng
    `HUONG_TRUC_CANONICAL` (|u| = 1) ở nhánh VÔ HƯỚNG. Nên `L` là **tỉ lệ**
    (0…1) ở nhánh đầu và **khoảng cách tuyệt đối** (0…h) ở nhánh sau:

        (A) L = 1/2  → tren = 1/2   ✅
        (B) L = 10   → tren = −9    ⇒ `tren < 0` ⇒ CURVED_ELLIPSE_CROSSES_CAP

    `duoi_sq = L²·|u|²` **đúng ở cả hai nhánh** (= 100), nên chỉ phép kiểm đáy
    TRÊN hỏng — và hỏng theo hướng **fail-closed**: từ chối oan, không bao giờ
    trả đáp số sai.

    ⚠️ Đây đúng lớp lỗi mà docstring `_ti_le_truc` trong chính file ấy đã
    cảnh báo — *"khai bằng ĐIỂM |u| = h ⇒ L đã LÀ tỉ lệ; khai bằng VÔ HƯỚNG
    |u| = 1 ⇒ L là KHOẢNG CÁCH tuyệt đối"* — nhưng cảnh báo ấy viết cho đường
    ĐƯỜNG TRÒN, và `intersect_plane_curved_ellipse` (thêm sau) không áp phép
    đổi thang. Đường tròn vẫn đúng ở cả hai nhánh: `test_11` đối chứng.

    Hệ quả: nhánh vô hướng **không bao giờ** cắt ra elip — `L > 1` thì
    `tren < 0`, còn `L < 1` thì `tren_sq = tren²·1` quá nhỏ so với `h_half_sq`.
    Tức một cách khai mà THẺ VĂN PHẠM có quảng cáo lại đóng hoàn toàn với phép
    elip.

    WAVE NÀY KHÔNG SỬA: §14 cấm đụng mã sản phẩm trong lúc đo.
    """
    A = CV.CurvedSolid("cylinder", v(0, 0, 0), v(0, 0, 20), None, F(16))
    B = CV.CurvedSolid("cylinder", v(0, 0, 0), None, None, F(16),
                       height_sq_khai=F(400))
    # Hai khối BẰNG NHAU về hình — tiền đề của khẳng định.
    assert A.radius_sq == B.radius_sq == F(16)
    assert A.height_sq == B.height_sq == F(400)
    assert A.huong_truc.cross(B.huong_truc).is_zero()

    mp = Plane3.from_equation(F(2), F(0), F(-1), F(10))
    e = CV.intersect_plane_curved_ellipse(A, mp)
    assert display(CV.dien_tich_elip(e)) == DAP_SO

    with pytest.raises(GeometryError) as ex:
        CV.intersect_plane_curved_ellipse(B, mp)
    assert ex.value.code == CV.ERR_ELIP_CAT_DAY, (
        "Lỗi đã được sửa ⇒ XOÁ test này và mở lại lượt live "
        "(OBLIQUE_ELLIPSE_FRESH_E2E_RERUN)")


def test_11_doi_chung__duong_TRON_dung_o_CA_HAI_nhanh():
    """Khoanh vùng: chỉ phép ELIP hỏng, `intersect_plane_curved` thì không."""
    A = CV.CurvedSolid("cylinder", v(0, 0, 0), v(0, 0, 20), None, F(16))
    B = CV.CurvedSolid("cylinder", v(0, 0, 0), None, None, F(16),
                       height_sq_khai=F(400))
    ngang = Plane3.from_equation(F(0), F(0), F(1), F(-10))
    assert CV.intersect_plane_curved(A, ngang).radius_sq == F(16)
    assert CV.intersect_plane_curved(B, ngang).radius_sq == F(16)


def test_12_he_qua__khong_co_chieu_cao_nao_di_duoc_o_nhanh_vo_huong():
    """Không phải một ca xui: nhánh vô hướng đóng với MỌI chiều cao thật."""
    mp = Plane3.from_equation(F(2), F(0), F(-1), F(10))
    for h2 in (F(400), F(100), F(1600), F(2500)):
        B = CV.CurvedSolid("cylinder", v(0, 0, 0), None, None, F(16),
                           height_sq_khai=h2)
        with pytest.raises(GeometryError):
            CV.intersect_plane_curved_ellipse(B, mp)


# ══ §10 · TIỀN ĐỀ CỦA GIẢ THUYẾT ĐIỂM VÀNH — BỊ BÁC ═════════════════════
def test_13_tien_de_cua_gia_thuyet_diem_vanh_KHONG_dung_cho_phep_elip():
    """§10 đòi chứng minh `radius + height` là đường hợp lệ TRƯỚC khi rút ca.

    Chứng minh ấy **thất bại** cho phép elip, nên câu *"bịa `rim_point` là lựa
    chọn của chương trình chứ không phải yêu cầu của hệ"* CHƯA đứng được. Với
    bài này, đường hợp lệ duy nhất không-bịa-điểm là **hai tâm có tên +
    `radius`** — đúng đường gold.
    """
    from app.simulation.semantic_program.hoisting import O_TEN
    from app.simulation.semantic_program.ir_static_check import _TOAN_HANG_LENH

    # `height` KHÔNG được kiểm kiểu tĩnh, và KHÔNG là ô tên với bộ nâng.
    o = _TOAN_HANG_LENH["construct_curved_solid"]
    assert not any(t[0] == "height" for t in o)
    assert "height" not in O_TEN["construct_curved_solid"]
    # …nhưng RUNTIME có đọc nó — nên đây là ô SỐNG mà tầng tĩnh không canh.
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
    # `radius` có vai trò in ra; `height` thì KHÔNG — ghi lại bất đối xứng.
    dong = next(d for d in the.splitlines()
                if "construct_curved_solid:" in d)
    assert "radius?:tên<scalar|float|int>[" in dong
    assert "height?:tên " in dong or dong.rstrip().endswith("height?:tên")


def test_17_danh_tinh_on_dinh_trong_wave():
    from app.main import CACHE_VERSION
    from app.runtime_identity import semantic_environment_fingerprint

    assert CACHE_VERSION == "89"
    fp = semantic_environment_fingerprint()
    mong = {
        "prompts": "55ac1ca6a6df92ce",
        "grammar_card": "285292feed07e603",
        "synthesis_schema": "6ccef3230c003d61",
        "analyze_schema": "515001b503af5c7c",
        "capability": "4b1e2f80a5a4bf26",
    }
    for k, b in mong.items():
        assert fp[k].startswith(b), (k, fp[k][:16])
