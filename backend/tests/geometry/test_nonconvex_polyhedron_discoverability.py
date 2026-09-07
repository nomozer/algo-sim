# -*- coding: utf-8 -*-
"""`NONCONVEX_POLYHEDRON_MODEL_DISCOVERABILITY` — bộ đo. **0 lượt gọi model.**

Wave trước đóng phần HỆ (`SYSTEM_EXPRESSIBLE`, `DETERMINISTICALLY_CORRECT`).
Wave này hỏi ô còn lại: **mô hình có tự viết nổi BẢNG MẶT của một khối chóp
đáy lõm không?**

Bộ test ở đây **không** chấm mô hình — nó chấm **bộ đo**, trước khi bộ đo được
phép tiêu quota. Bài học đã trả giá hai lần trong kho này: một bộ chấm tụt lại
sau hệ sẽ ghi `FAIL` cho một chương trình ĐÚNG, và một guard chưa từng đỏ là
guard chưa được chứng minh.
"""
from __future__ import annotations

import copy
import json
import sys
from fractions import Fraction as F
from pathlib import Path

import pytest

GOC = Path(__file__).resolve().parents[3]
_SC = GOC / "backend" / "scripts"
if str(_SC) not in sys.path:
    sys.path.insert(0, str(_SC))

from app.simulation.geometry.exact import Vec3  # noqa: E402
from app.simulation.geometry.section import (  # noqa: E402
    Polyhedron, kiem_mat_phang_don, the_tich_da_dien,
)

import gold_nonconvex_polyhedron as GM  # noqa: E402
import register_nonconvex_polyhedron as RG  # noqa: E402
from score_nonconvex_polyhedron import (  # noqa: E402
    cham_analyze, cham_bang_mat, cham_synthesis,
)

RA = (GOC / "docs" / "evaluation" / "geometry"
      / "nonconvex-polyhedron-model-discoverability")


def _json(ten: str) -> dict:
    p = RA / ten
    assert p.exists(), f"thiếu {ten} — chạy scripts/register_nonconvex_polyhedron.py"
    return json.loads(p.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def dang_ky() -> dict:
    return _json("registration.json")


@pytest.fixture(scope="module")
def gold_pf() -> dict:
    return _json("PREFLIGHT_GOLD.json")


@pytest.fixture(scope="module")
def scorer_pf() -> dict:
    return _json("PREFLIGHT_SCORER.json")


# ══ §3 · ORACLE — BỐN nguồn độc lập, kernel chỉ là một trong bốn ═════════
def test_01_oracle_45_tu_BON_nguon_doc_lap():
    """Nếu chỉ hỏi kernel thì bộ đo và hệ được đo là một — đo được cái gì."""
    xy = {k: (F(v[0]), F(v[1])) for k, v in GM.TOA_DO.items() if k != "S"}
    chu = GM.DINH_DAY

    # ① shoelace
    s = sum(xy[chu[i]][0] * xy[chu[(i + 1) % 5]][1]
            - xy[chu[(i + 1) % 5]][0] * xy[chu[i]][1] for i in range(5))
    assert abs(s) / 2 == 15

    # ② chia tam giác TAY: ABC + ACE − CDE
    def tg(p, q, r):
        return abs((q[0] - p[0]) * (r[1] - p[1])
                   - (q[1] - p[1]) * (r[0] - p[0])) / 2

    assert (tg(xy["A"], xy["B"], xy["C"]) + tg(xy["A"], xy["C"], xy["E"])
            - tg(xy["C"], xy["D"], xy["E"])) == 15

    # ③ signed-boundary viết RIÊNG, không gọi kernel
    V = {k: Vec3(F(v[0]), F(v[1]), F(v[2])) for k, v in GM.TOA_DO.items()}
    idx = {t: i for i, t in enumerate(GM.DINH)}
    mat = [tuple(idx[x] for x in m) for m in GM.MAT]
    pts = [V[t] for t in GM.DINH]
    goc = Vec3(F(0), F(0), F(0))
    tong = F(0)
    for m in mat:
        for i in range(1, len(m) - 1):
            u, v_, w = pts[m[0]] - goc, pts[m[i]] - goc, pts[m[i + 1]] - goc
            tong += u.dot(v_.cross(w))
    assert abs(tong) / 6 == 45

    # ④ kernel sản phẩm
    assert the_tich_da_dien(Polyhedron(tuple(pts), tuple(mat))) == 45
    assert GM.ORACLE["volume"] == GM.ORACLE["dap_so_hien_thi"] == "45"


def test_02_khoi_nam_TRON_trong_pham_vi_da_chung_minh():
    """Bao đóng v1 KHÔNG soát được hai mặt xuyên nhau, nên ca đo phải nằm
    trong phần soát được — nếu không, `45` là một con số ngoài bảo hành."""
    V = {k: Vec3(F(v[0]), F(v[1]), F(v[2])) for k, v in GM.TOA_DO.items()}
    idx = {t: i for i, t in enumerate(GM.DINH)}
    kh = Polyhedron(tuple(V[t] for t in GM.DINH),
                    tuple(tuple(idx[x] for x in m) for m in GM.MAT))
    kiem_mat_phang_don(kh)          # phẳng + đơn, không ném
    # Mặt bên KHÔNG xuyên nhau: hai cạnh đáy không kề thì rời nhau, nên hai
    # mặt bên chỉ gặp nhau ở S và ở đỉnh chung. Kiểm bằng chính tính ĐƠN của
    # đáy — mọi tia từ S cắt z=0 đúng một lần.
    assert len({tuple(GM.TOA_DO[t][:2]) for t in GM.DINH_DAY}) == 5
    assert GM.TOA_DO["S"][2] != 0


def test_03_hai_BAY_cho_hai_so_SAI_phan_biet_duoc():
    """`63` và `72` phải khác nhau và khác `45` — bộ chấm mới nói được mô
    hình hỏng KIỂU nào."""
    xy = {k: (F(v[0]), F(v[1])) for k, v in GM.TOA_DO.items() if k != "S"}

    def tg(p, q, r):
        return abs((q[0] - p[0]) * (r[1] - p[1])
                   - (q[1] - p[1]) * (r[0] - p[0])) / 2

    quat = sum(tg(xy["A"], xy[GM.DINH_DAY[i]], xy[GM.DINH_DAY[i + 1]])
               for i in range(1, 4))
    assert quat == 21 and quat * 9 / 3 == 63
    loi = ["A", "B", "C", "E"]
    s = sum(xy[loi[i]][0] * xy[loi[(i + 1) % 4]][1]
            - xy[loi[(i + 1) % 4]][0] * xy[loi[i]][1] for i in range(4))
    assert abs(s) / 2 == 24 and abs(s) / 2 * 9 / 3 == 72
    assert len({45, 63, 72}) == 3


def test_04_de_KHONG_lo_bang_mat_cho_mo_hinh():
    """Bảng mặt là thứ ĐANG ĐƯỢC ĐO. Lọt vào đề thì phép đo hỏi câu khác."""
    t = GM.PROBLEM_TEXT.lower()
    for cam in ("mặt bên", "mat ben", "faces", "bảng mặt", "sab", "sbc",
                "scd", "sde", "sea"):
        assert cam not in t, cam
    # …nhưng đề PHẢI cho thứ tự đỉnh quanh biên, nếu không bài vô nghĩa.
    assert "theo thứ tự quanh biên" in GM.PROBLEM_TEXT
    for d in GM.DINH:
        assert f"{d}(" in GM.PROBLEM_TEXT


# ══ §4 · TIỀN KIỂM GOLD ═════════════════════════════════════════════════
def test_05_gold_di_TRON_duong_san_pham(gold_pf):
    assert gold_pf["GOLD_PREFLIGHT"] == "PASS"
    assert gold_pf["servable"] is True
    assert gold_pf["stage_reached"] == "served"
    assert gold_pf["EXACT_VOLUME"] == "45"
    assert gold_pf["weak_kinds"] == []
    assert gold_pf["CHECKER_THAT_SU_CHAY"] is True
    assert gold_pf["trace"] == gold_pf["Scene3D"] == "PASS"
    assert gold_pf["SCENE3D_CONCAVITY_PRESERVED"] is True


def test_06_sau_phan_vi_du_deu_PASS(gold_pf):
    pv = gold_pf["phan_vi_du"]
    assert len(pv) == 6, sorted(pv)
    assert all(v == "PASS" for v in pv.values()), pv


def test_07_QUAT_lap_lom__the_tich_DUNG_ma_HINH_sai(gold_pf):
    """Phát hiện đáng ghi nhất của tiền kiểm, và nó ngược trực giác.

    Khai đáy bằng ba tam giác `ABC · ACD · ADE` vẫn cho biên KÍN và vẫn cho
    **`V = 45` ĐÚNG** — đó chính là điều công thức có dấu hứa. Nhưng ba tam
    giác ấy là thứ renderer VẼ, và `A-C-D` nằm NGOÀI đáy ⇒ phần lõm bị lấp.

    Nên ba chiều `EXACT_VOLUME` · `FACE_TABLE_VALID` ·
    `SCENE3D_CONCAVITY_PRESERVED` **không được gộp làm một**: ở đây chúng
    tách nhau, và một bộ chấm gộp chúng sẽ cho điểm tuyệt đối một chương
    trình vẽ sai hình.
    """
    assert gold_pf["phan_vi_du_do_duoc"]["①_dap_so_quat"] == "45"
    quat = cham_synthesis(RG._voi_mat(RG.MAT_QUAT))
    assert quat["FACE_TABLE_VALID"] == "FAIL"
    assert quat["CO_DUNG_MOT_MAT_DAY"] is False
    assert quat["BIEN_KIN"] is True          # biên KÍN, và vẫn sai hình
    assert RG._lom_con_nguyen(RG._canh(RG._voi_mat(RG.MAT_QUAT))) is False


def test_08_control_LOI_van_chay_dung(gold_pf):
    assert gold_pf["phan_vi_du_do_duoc"]["⑥_dap_so_loi"] == "72"


def test_09_ba_bang_mat_HONG_bi_bac_dung_TANG(gold_pf):
    do = gold_pf["phan_vi_du_do_duoc"]
    assert do["②_error"] == do["④_error"] == "semantic_program_invalid"
    # Đổi chu trình đáy ⇒ HÌNH khác ⇒ đáp số khác. `54`, không phải `45`.
    assert do["③_dap_so_doi_hinh"] not in (None, "45")


# ══ §5 · TIỀN KIỂM BỘ CHẤM — nó không được ghim CHÍNH TẢ ════════════════
def test_10_bo_cham_nhan_gold(scorer_pf):
    assert scorer_pf["SCORER_PREFLIGHT"] == "PASS"
    assert scorer_pf["SCORER_ACCEPTS_GOLD"] == "YES"


def test_11_bo_cham_BAT_BIEN_voi_cach_viet(scorer_pf):
    """Bảng mặt bằng CHỈ SỐ · tên biến khác đề · đảo chiều mọi mặt — cùng một
    khối, phải cùng một phán quyết. Ghim chính tả là chấm sai chương trình
    đúng, và kho này đã trả giá đúng một lần cho lỗi ấy."""
    assert scorer_pf["SCORER_INVARIANT_TO_NOTATION"] == "YES"
    assert scorer_pf["⑦ bảng mặt bằng CHỈ SỐ"]["FACE_TABLE_VALID"] == "PASS"
    assert scorer_pf["⑧ tên biến KHÁC đề"]["FACE_TABLE_VALID"] == "PASS"
    assert scorer_pf["⑧ tên biến KHÁC đề"]["TEN_TRUNG_DE"] is False
    assert scorer_pf["⑨ đảo chiều MỌI mặt"]["FACE_TABLE_VALID"] == "PASS"


def test_12_bo_cham_bac_ba_bang_mat_HONG(scorer_pf):
    assert scorer_pf["SCORER_REJECTS_WRONG_TABLE"] == "YES"
    assert scorer_pf["SCORER_CATCHES_SHORTCUT"] == "YES"


@pytest.mark.parametrize("xoay", range(5))
def test_13_XOAY_VONG_chu_trinh_day_van_PASS(xoay):
    """Đề cho `A→B→C→D→E`; mô hình có thể bắt đầu từ đỉnh khác. Cùng chu
    trình ⇒ cùng khối ⇒ phải PASS."""
    chu = GM.DINH_DAY[xoay:] + GM.DINH_DAY[:xoay]
    assert cham_bang_mat(RG._chop(chu))["FACE_TABLE_VALID"] == "PASS"


def test_14_bo_cham_doc_duoc_ca_TEN_lan_CHI_SO():
    """`construct_solid.faces` nhận cả hai dạng, nên bộ chấm phải đọc cả hai —
    đọc một dạng là chấm FAIL cho chương trình đúng viết theo dạng kia."""
    g = copy.deepcopy(GM.GOLD)
    idx = {t: i for i, t in enumerate(GM.DINH)}
    for s in g["statements"]:
        if s.get("kind") == "construct_solid":
            s["faces"] = [[idx[x] for x in m] for m in s["faces"]]
    assert cham_synthesis(g)["FACE_TABLE_VALID"] == "PASS"


def test_15_analyze_KHONG_QUAN_SAT_DUOC_khac_SAI():
    """Nguồn không mang nội dung fact ⇒ `NOT_CAPTURED`, KHÔNG phải `FAIL`.
    Đây là đính chính đã trả giá ở `PROVENANCE_AFFORDANCE_AB_4_LUOT`."""
    ct = {"obligations": [{"kind": "volume", "container": "S.ABCDE",
                           "params": {"witness": "V"}}]}
    r = cham_analyze(ct, nguon="SU_KIEN_DEM")
    assert r["ANALYZE_CONTRACT_CORRECT"] == "NOT_CAPTURED"
    assert r["CO_DU_SAU_DIEM"] == "NOT_CAPTURED"
    # …nhưng chiều NGHĨA VỤ đọc được từ mọi nguồn, nên nó vẫn phải phán.
    assert r["ANALYZE_OBLIGATION_CORRECT"] == "PASS"


def test_16_analyze_container_chap_moi_LOI_VIET_cung_vat():
    for c in ("S.ABCDE", "(S.ABCDE)", "SABCDE", "S.ABCDE "):
        ct = {"input_facts": [], "obligations": [
            {"kind": "volume", "container": c, "params": {"witness": "V"}}]}
        assert cham_analyze(ct)["ANALYZE_OBLIGATION_CORRECT"] == "PASS", c
    ct = {"input_facts": [], "obligations": [
        {"kind": "volume", "container": "ABC", "params": {"witness": "V"}}]}
    assert cham_analyze(ct)["ANALYZE_OBLIGATION_CORRECT"] == "FAIL"


# ══ §13 · TIÊM LỖI — guard chưa từng đỏ là guard chưa được chứng minh ═══
def test_TIEM_1_bo_kiem_bien_kin__bang_mat_HONG_lot_qua():
    mat = RG._chop(GM.DINH_DAY)[:-1]           # thiếu một mặt bên
    that = cham_bang_mat(mat)
    assert that["FACE_TABLE_VALID"] == "FAIL" and that["BIEN_KIN"] is False
    gia = dict(that, BIEN_KIN=True)
    assert all(gia[k] for k in ("KHONG_LAP_DINH", "CO_DUNG_MOT_MAT_DAY",
                                "CHU_TRINH_DAY_DUNG", "BIEN_KIN"))


def test_TIEM_2_bo_kiem_CHU_TRINH__day_sai_hinh_lot_qua():
    """Chu trình `A→B→D→C→E` cho một khối KHÁC (đo được: `V = 54`). Bỏ ô
    `CHU_TRINH_DAY_DUNG` thì ba bất biến còn lại đều xanh — nên ô ấy là thứ
    DUY NHẤT chặn được lớp lỗi này."""
    mat = RG._chop(["A", "B", "D", "C", "E"])
    r = cham_bang_mat(mat)
    assert r["FACE_TABLE_VALID"] == "FAIL"
    assert r["CHU_TRINH_DAY_DUNG"] is False
    assert r["BIEN_KIN"] is True
    assert r["CO_DUNG_MOT_MAT_DAY"] is True
    assert r["MAT_BEN_DEU_LA_CANH_DAY_CONG_S"] is False


def test_TIEM_3_bo_neo_TOA_DO__ten_bia_lot_qua():
    """Mô hình khai một điểm SAI toạ độ nhưng đúng tên: neo bằng tên thì lọt,
    neo bằng toạ độ thì không."""
    g = copy.deepcopy(GM.GOLD)
    for d in g["memory_declarations"]:
        if d["name"] == "D":
            d["initial_value"] = [3, 3, 0]      # hết lõm
    r = cham_synthesis(g)
    assert r["CO_DU_SAU_DINH"] is False
    assert "D" not in r["DIEM_KHOP_TOA_DO"]
    assert r["SYNTHESIS_STRUCTURE_CORRECT"] == "FAIL"


def test_TIEM_4_khai_thang_dap_so__KHONG_DUONG_TAT_do():
    r = cham_synthesis(RG._duong_tat())
    assert r["KHONG_DUONG_TAT"] is False
    assert r["USES_MEASURE_VOLUME"] is False
    assert r["SYNTHESIS_STRUCTURE_CORRECT"] == "FAIL"


def test_TIEM_5_diem_KHONG_xuat_xu_bi_bat():
    g = copy.deepcopy(GM.GOLD)
    for d in g["memory_declarations"]:
        d.pop("source_fact_id", None)
    r = cham_synthesis(g)
    assert r["MOI_DIEM_CO_XUAT_XU"] is False
    assert r["SYNTHESIS_STRUCTURE_CORRECT"] == "FAIL"


# ══ §8 · ĐĂNG KÝ KHOÁ TRƯỚC LƯỢT GỌI ĐẦU ═══════════════════════════════
def test_17_dang_ky_du_bon_nhan_bat_buoc(dang_ky):
    assert dang_ky["measurement_class"] == "DEVELOPMENT_DIAGNOSTIC"
    assert dang_ky["held_out_claim"] is False
    assert dang_ky["evaluator_independence"] == "OPERATOR_WAIVED"
    assert dang_ky["ngan_sach"]["logical_application_call_limit"] == 3
    # ⚠️ `token_reservation_per_call` THIẾU một lần trong wave trước và runner
    # chết TRƯỚC provider — không tiêu quota, nhưng mất một lượt dựng.
    assert dang_ky["ngan_sach"]["token_reservation_per_call"] == 8000
    assert dang_ky["ngan_sach"]["token_ceiling_observed"] == 25000


def test_18_ngan_sach_khop_BRIEF(dang_ky):
    ns = dang_ky["ngan_sach"]
    assert ns["ANALYZE_CALL_BUDGET"] == 1
    assert ns["INITIAL_SYNTHESIS_CALL_BUDGET"] == 1
    assert ns["REPAIR_CALL_BUDGET"] == 1
    assert (ns["ANALYZE_CALL_BUDGET"] + ns["INITIAL_SYNTHESIS_CALL_BUDGET"]
            + ns["REPAIR_CALL_BUDGET"]) == ns["logical_application_call_limit"]


def test_19_corpus_va_oracle_KHOA_bang_bam(dang_ky):
    assert dang_ky["ca"]["problem_sha256"] == GM.PROBLEM_HASH
    assert dang_ky["ca"]["oracle_sha256"] == GM.ORACLE_HASH
    assert dang_ky["ca"]["problem_text"] == GM.PROBLEM_TEXT
    h = dang_ky["hash_bo_do"]
    for k in ("gold_sha256", "gold_module_sha256", "scorer_module_sha256",
              "runner_sha256", "register_sha256", "contract_gold_sha256"):
        assert len(h[k]) == 64, k
    assert dang_ky["registration_sha256"]


def test_20_dang_ky_ghi_DANH_TINH_he_duoc_do(dang_ky):
    from app.main import CACHE_VERSION
    from app.runtime_identity import semantic_environment_fingerprint

    dt = dang_ky["danh_tinh_he_duoc_do"]
    assert dt["cache_version"] == CACHE_VERSION == "92"
    assert dt["NONCONVEX_POLYHEDRON_CAPABILITY"] == "foundation_only"
    fp = semantic_environment_fingerprint()
    for k, v in dt["model_facing"].items():
        assert fp[k] == v, k


def test_21_pham_vi_ket_luan_KHONG_hua_qua(dang_ky):
    """Một ca không nói gì về ổn định, và development probe không nâng được
    năng lực sản phẩm. Ghim để lời hứa không trôi khi viết báo cáo."""
    pv = dang_ky["pham_vi_ket_luan"]
    assert pv["STABILITY_UNDER_ACCEPTANCE"] == "NOT_MEASURED"
    assert pv["NONCONVEX_POLYHEDRON"] == "foundation_only"
    assert pv["PRODUCT_PROMOTION_ELIGIBLE"] == "NO"
    assert dang_ky["cases"] == 1
