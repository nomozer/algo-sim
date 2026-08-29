# -*- coding: utf-8 -*-
"""PHASE 7A.2 — ĐÓNG BĂNG GIAO THỨC ĐÁNH GIÁ. **0 API call.**

Pha này **không** nâng năng lực hệ: không sửa `backend/app`, không sửa prompt,
không sửa DSL. Nó sửa **bộ đo**, và ba việc:

    ① tách `obligation_match` thành DỰNG và KIỂM — hai tập rời nhau
    ② kỳ vọng ra khỏi mã bộ đo, vào file có lịch sử Git và có người phán
    ③ đóng băng bốn chỉ số còn lại (`served` · `oracle` ·
      `construction_validity` · `stability`)

VÌ SAO ĐÁNG MỘT PHA RIÊNG: `PHASE_7A_1_REPORT §5` ghi lại một con số `0/3` mà
**nguyên nhân là kỳ vọng của người đo**, không phải lỗi mô hình. Kỳ vọng ấy
nằm ngay trong mã runner nên không ai tra được nó đã đổi lúc nào, và nó trộn
một **mệnh lệnh dựng** (`"Hãy dựng mặt phẳng (PMN)"`) vào tập **kiểm**. Sửa
bằng lời hứa thì lần sau lặp lại; sửa bằng test thì không.
"""
from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import pytest

from app.simulation.semantic_program.obligations import OBLIGATION_KINDS

GOC = Path(__file__).resolve().parents[3]
SCRIPTS = GOC / "backend" / "scripts"
GEO = GOC / "docs" / "evaluation" / "geometry"
KY_VONG = GEO / "expectations"

#: Tám nghĩa vụ hình học — cùng danh sách `test_geometry_dev_set` dùng.
TAM_NGHIA_VU = {
    "point_on_line", "point_on_plane", "parallel", "perpendicular",
    "coplanar", "distance", "angle", "volume",
}


def _nap(ten: str):
    spec = importlib.util.spec_from_file_location(ten, SCRIPTS / f"{ten}.py")
    assert spec and spec.loader
    m = importlib.util.module_from_spec(spec)
    sys.modules[ten] = m
    spec.loader.exec_module(m)
    return m


@pytest.fixture(scope="module")
def GE():
    return _nap("geometry_expectations")


@pytest.fixture(scope="module")
def PILOT(GE):
    return GE.nap("pilot")


@pytest.fixture(scope="module")
def CASES(PILOT):
    return {c["case_id"]: c for c in PILOT["cases"]}


# ══ ① HAI TẬP RỜI NHAU ═══════════════════════════════════════════════════
def test_moi_de_khai_CA_HAI_tap_du_mot_tap_rong(CASES):
    """Bỏ trống ≠ khai rỗng. Bỏ trống thì không biết người soạn đã cân nhắc
    chưa; khai `[]` là một phán quyết ghi lại được."""
    for ma, c in CASES.items():
        assert "construction_obligations" in c, f"{ma}: thiếu tập DỰNG"
        assert "verification_obligations" in c, f"{ma}: thiếu tập KIỂM"


def test_nghia_vu_KIEM_deu_nam_trong_taxonomy(CASES):
    for ma, c in CASES.items():
        for o in c["verification_obligations"]:
            assert o["kind"] in OBLIGATION_KINDS, f"{ma}: {o['kind']!r} ngoài taxonomy"
            assert o["kind"] in TAM_NGHIA_VU, f"{ma}: {o['kind']!r} không phải hình học"


def test_nghia_vu_DUNG_KHONG_duoc_viet_bang_ngon_ngu_cua_tap_KIEM(CASES):
    """Cổng chống GỘP LẠI.

    Đây là chỗ lỗi cũ sẽ quay về: ai đó thấy `(PMN)` cần được kiểm sẽ viết
    `point_on_plane` vào tập dựng, và hai tập lại thành một. Vật dựng khai
    bằng **tên + kiểu IR**, nghĩa vụ kiểm khai bằng **kind**; trộn hai từ vựng
    là dấu hiệu sớm nhất của việc gộp.
    """
    for ma, c in CASES.items():
        for o in c["construction_obligations"]:
            assert o["ten_trong_de"] not in OBLIGATION_KINDS, (
                f"{ma}: vật dựng {o['ten_trong_de']!r} đang mang tên một nghĩa vụ kiểm")
            assert o["kieu"] not in OBLIGATION_KINDS, (
                f"{ma}: `kieu` phải là kiểu IR (point3/line3/plane3…), "
                f"nhận {o['kieu']!r} — đó là một `kind`")


def test_moi_nghia_vu_deu_co_LY_DO(CASES):
    """Lý do không viết ra được ⇒ đó là kỳ vọng của người đo, không phải yêu
    cầu của đề. Điều kiện ⑨ của Phase 6.8."""
    for ma, c in CASES.items():
        for o in c["construction_obligations"] + c["verification_obligations"]:
            assert len((o.get("ly_do") or "").strip()) >= 20, (
                f"{ma}: một nghĩa vụ có `ly_do` rỗng hoặc quá ngắn để kiểm lại")


def test_tap_DUNG_rong_thi_phai_ghi_VI_SAO_rong(CASES):
    """Rỗng vì đề không ra lệnh dựng, hay rỗng vì quên soạn? Hai thứ khác nhau
    và chỉ ghi chú mới phân biệt được."""
    for ma, c in CASES.items():
        if not c["construction_obligations"]:
            assert c.get("ghi_chu_dung"), f"{ma}: tập DỰNG rỗng mà không ghi lý do"


# ══ ② NGUỒN KỲ VỌNG ══════════════════════════════════════════════════════
def test_pilot_KHAI_THANG_rang_ky_vong_do_nguoi_do_dat(PILOT):
    """Không giấu điểm yếu. Pilot chấm BỘ ĐO nên người đo phán được; điều phải
    có là **khai ra**, để số của nó không bị đọc như số held-out."""
    nd = PILOT["nguoi_danh_gia"]
    assert nd["loai"] == "nguoi_do"
    assert "KHÔNG BAO GIỜ là số luận văn" in nd["khai_han_che"]


def test_HELD_OUT_bi_CAM_dung_ky_vong_cua_nguoi_do(GE, tmp_path):
    """Cổng thật, không phải đoạn văn.

    Trên pilot, một kỳ vọng sai lộ ra sau 8 lượt. Trên held-out chỉ có MỘT
    lượt (`HOLDOUT_PROTOCOL §2`), nên cùng lỗi ấy sẽ đi thẳng vào luận văn.
    """
    d = json.loads((KY_VONG / "pilot.json").read_text(encoding="utf-8"))
    d["tap"] = "holdout"
    (tmp_path / "holdout.json").write_text(
        json.dumps(d, ensure_ascii=False), encoding="utf-8")
    with pytest.raises(ValueError, match="KHÔNG được dùng kỳ vọng do người đo"):
        GE.nap("holdout", thu_muc=tmp_path)


def test_ky_vong_TU_KHAI_khong_sinh_tu_dau_ra_mo_hinh(GE, PILOT, tmp_path):
    assert PILOT["sinh_tu_model_output"] is False
    d = json.loads((KY_VONG / "pilot.json").read_text(encoding="utf-8"))
    d["sinh_tu_model_output"] = True
    (tmp_path / "pilot.json").write_text(
        json.dumps(d, ensure_ascii=False), encoding="utf-8")
    with pytest.raises(ValueError, match="tautology"):
        GE.nap("pilot", thu_muc=tmp_path)


@pytest.mark.parametrize("ten", ["measure_geometry_stability", "run_phase7a_pilot"])
def test_runner_KHONG_con_giu_ky_vong_trong_ma_nguon(ten):
    """Hồi quy trực tiếp: kỳ vọng quay lại nằm cạnh đề là quay lại tình trạng
    người viết bộ đo sửa được thước ngay trong lượt đang đo."""
    src = (SCRIPTS / f"{ten}.py").read_text(encoding="utf-8")
    # Bắt KHAI BÁO (`"nghia_vu_mong_doi": [...]`), không bắt việc GHI LẠI giá
    # trị đã nạp vào bản ghi artifact — bản ghi phải giữ khoá ấy thì ba vòng đo
    # trước mới còn đọc được.
    assert '"nghia_vu_mong_doi": [' not in src, (
        f"{ten}: kỳ vọng lại được khai trong mã — phải nằm ở expectations/*.json")


def test_MOI_de_cua_pilot_deu_co_ky_vong_TRUOC_khi_chay():
    """Cổng chống *"đo rồi mới soạn"*.

    Thiếu kỳ vọng thì `_ky_vong_cua` nổ — nhưng nó nổ **giữa lượt live**, sau
    khi đã tiêu call. Test này bắt cùng lỗi ấy với 0 call, ở chỗ rẻ.
    """
    pilot = _nap("run_phase7a_pilot")
    ge = _nap("geometry_expectations")
    co = {c["case_id"] for c in ge.nap("pilot")["cases"]}
    thieu = [b["id"] for b in pilot.BAI_PILOT if b["id"] not in co]
    assert not thieu, f"đề chưa có kỳ vọng: {thieu}"


def test_runner_KHONG_tu_dat_mac_dinh_khi_thieu_ky_vong():
    """Thiếu ⇒ DỪNG. Chấm bằng tập rỗng thì `verification_match` tự động False
    cho mọi lượt, và con số ấy đổ lỗi cho mô hình một thiếu sót của bộ đo."""
    m = _nap("measure_geometry_stability")
    with pytest.raises(KeyError, match="soạn kỳ vọng TRƯỚC khi đo"):
        m._ky_vong_cua("de-khong-ton-tai")


def test_bo_do_KHONG_ghi_vao_thu_muc_ky_vong():
    """Bộ đo chỉ ĐỌC kỳ vọng. Một runner ghi được vào đó là một runner sửa được
    thước sau khi thấy số."""
    for f in SCRIPTS.glob("*.py"):
        src = f.read_text(encoding="utf-8")
        if "expectations" not in src:
            continue
        assert "write_text" not in src or f.name != "geometry_expectations.py", (
            f"{f.name}: module kỳ vọng không được ghi file")


# ══ ③a PHÉP SO CỦA NGHĨA VỤ DỰNG ═════════════════════════════════════════
def test_dung_THEM_vat_KHONG_bi_tru_diem(GE):
    """Bất đối xứng CÓ CHỦ ĐÍCH so với tập kiểm.

    Muốn có giao tuyến `d` thì phải dựng vài điểm trung gian đề không gọi tên.
    Trừ điểm ở đó là phạt mô hình vì đã làm đúng phép dựng hình.
    """
    spec = _spec_gia(["Q", "R_phu", "T_phu"])
    m = GE.khop_dung([{"ten_trong_de": "Q", "kieu": "point3", "ly_do": "x" * 30}],
                     spec)
    assert m["khop_hoan_toan"] is True
    assert m["thua_dung"] == ["R_phu", "T_phu"], "vật thừa vẫn phải QUAN TRẮC được"


def test_thieu_MOT_vat_la_LECH(GE):
    spec = _spec_gia(["Q"])
    m = GE.khop_dung(
        [{"ten_trong_de": "Q", "kieu": "point3", "ly_do": "x" * 30},
         {"ten_trong_de": "d", "kieu": "line3", "ly_do": "x" * 30}], spec)
    assert m["khop_hoan_toan"] is False and m["thieu"] == ["d"]


def test_ba_trang_thai_KHONG_phai_hai(GE):
    """`None` ở hai chỗ khác nhau, và cả hai KHÁC `False`."""
    khong_ra_lenh = GE.khop_dung([], _spec_gia(["Q"]))
    assert khong_ra_lenh["khop_hoan_toan"] is None
    assert "không áp dụng" in khong_ra_lenh["vi_sao"]

    khong_co_ct = GE.khop_dung(
        [{"ten_trong_de": "Q", "kieu": "point3", "ly_do": "x" * 30}], None)
    assert khong_co_ct["khop_hoan_toan"] is None
    assert "không chấm được" in khong_co_ct["vi_sao"]


def test_ten_CHUONG_TRINH_khac_ten_DE_van_khop(GE):
    """Mô hình tự đặt tên. Bộ đo hoà giải bằng LƯỚI SẢN PHẨM, không đoán chính
    tả — cùng lưới mà bốn cổng đang dùng từ Phase 6.7.1/7A.1."""
    m = GE.khop_dung(
        [{"ten_trong_de": "(PMN)", "kieu": "plane3", "ly_do": "x" * 30}],
        _spec_gia(["plane_PMN"], kieu="plane3"))
    assert m["khop_hoan_toan"] is True
    assert m["da_dung"]["(PMN)"] == "plane_PMN"


def test_vat_KHAI_SAN_khong_tinh_la_DUNG(GE):
    """Khai `initial_value` rồi gọi đó là dựng thì `construction_validity` mất
    nghĩa. Hai chỉ số đứng trên CÙNG một khái niệm 'được dựng'."""
    spec = _spec_gia([])
    spec["memory_declarations"] = [
        {"name": "Q", "type": "point3",
         "initial_value": {"x": "0", "y": "0", "z": "0"}}]
    m = GE.khop_dung([{"ten_trong_de": "Q", "kieu": "point3", "ly_do": "x" * 30}],
                     spec)
    assert m["khop_hoan_toan"] is False, "vật khai sẵn không phải vật đã dựng"


# ══ ③b PHÉP SO CỦA NGHĨA VỤ KIỂM — GIỮ NGUYÊN ════════════════════════════
def test_kiem_van_so_BANG_DUNG_khong_phai_chua_du(GE):
    """Chỉ số ③b **không đổi định nghĩa** ở pha này, chỉ đổi tên và đổi nguồn
    kỳ vọng. Khai thừa vẫn là lệch."""
    assert GE.khop_kiem(["distance"], ["distance", "volume"])["khop_hoan_toan"] is False
    assert GE.khop_kiem(["distance"], ["distance"])["khop_hoan_toan"] is True


def test_kiem_MUON_ham_cua_reliability_v2_khong_viet_lai(GE):
    """Hai bản sao sẽ trôi khỏi nhau đúng lúc cần so hai vòng đo."""
    rv = _nap("reliability_v2")
    assert (GE.khop_kiem(["a"], ["b"]) == rv.obligation_match(["a"], ["b"]))


# ══ HỒI QUY TRÊN ARTIFACT THẬT ═══════════════════════════════════════════
def test_ca_3_PMN_ky_vong_da_sua_thi_KIEM_khop(GE, CASES):
    """Hiện trường thật, `phase7a-pilot-sau-71/3-pmn-giao-tuyen-lan1`.

    Hợp đồng khai đúng `{point_on_line}`; kỳ vọng CŨ đòi thêm `point_on_plane`
    nên ghi `False`. Không sửa một ký tự nào của artifact — chỉ sửa cái thước.
    """
    d = _artifact("phase7a-pilot-sau-71", "3-pmn-giao-tuyen-lan1")
    assert d["ban_ghi"]["obligation_match"] is False, "số CŨ, giữ để so"

    m = GE.khop_kiem(GE.kinds_kiem(CASES["3-pmn-giao-tuyen"]),
                     d["ban_ghi"]["nghia_vu_kinds"])
    assert m["khop_hoan_toan"] is True
    assert m["thua"] == [] and m["thieu"] == []


def test_ca_3_PMN_DUNG_du_sau_vat_de_ra_lenh(GE, CASES):
    """Và đây là thứ chỉ số cũ **không nhìn thấy**: sáu vật đề bảo dựng đều đã
    được dựng, kể cả khi mô hình đặt tên khác (`(PMN)` → `plane_PMN`)."""
    d = _artifact("phase7a-pilot-sau-71", "3-pmn-giao-tuyen-lan1")
    m = GE.khop_dung(GE.vat_phai_dung(CASES["3-pmn-giao-tuyen"]),
                     d["generated_program"])
    assert m["thieu"] == [], f"chưa dựng: {m['thieu']}"
    assert m["khop_hoan_toan"] is True
    assert set(m["da_dung"]) == {"M", "N", "P", "(PMN)", "d", "Q"}


def test_bai_chi_TINH_thi_DUNG_la_KHONG_AP_DUNG(GE, CASES):
    """`2-the-tich` không có động từ dựng nào ⇒ `None`, không phải `False`.
    Khối S.ABCD là DỮ KIỆN; việc nó được dựng hay khai sẵn là câu hỏi của ④."""
    d = _artifact("phase7a-pilot-sau-71", "2-the-tich-lan1")
    m = GE.khop_dung(GE.vat_phai_dung(CASES["2-the-tich"]), d["generated_program"])
    assert m["khop_hoan_toan"] is None


def test_lan_DOI_THUOC_duoc_khai_kem_SO_CU(CASES):
    """Luật `PHASE7_METRIC_CONTRACT §4`: đổi định nghĩa sau khi thấy số thì
    phải nói ra kèm số cũ. Ở đây kỳ vọng của bài 3 đã đổi, nên phải có vết."""
    ls = CASES["3-pmn-giao-tuyen"].get("lich_su_doi")
    assert ls, "kỳ vọng bài 3 đã đổi mà không có `lich_su_doi`"
    d = ls[0]
    assert d["gia_tri_cu"] == ["point_on_line", "point_on_plane"]
    assert d["gia_tri_moi"] == ["point_on_line"]
    assert d["so_cu"] and d["vong_do_anh_huong"]


# ══ ③ ĐÓNG BĂNG BỐN CHỈ SỐ CÒN LẠI ═══════════════════════════════════════
_HD = GEO / "PHASE7_METRIC_CONTRACT.md"
_DONG_BANG = ("served", "oracle", "construction_validity", "stability")


@pytest.mark.parametrize("chi_so", _DONG_BANG)
def test_bon_chi_so_dong_bang_van_co_mat_trong_hop_dong(chi_so):
    """Đóng băng nghĩa là ĐỊNH NGHĨA không đổi, không phải file không đổi.

    Test này bắt được ca mất hẳn một chỉ số. Nó **không** bắt được ca sửa tinh
    vi bên trong định nghĩa — thứ ấy phải đọc diff, và `§6` nói rõ ai được đổi.
    """
    src = _HD.read_text(encoding="utf-8")
    assert f"`{chi_so}`" in src


def test_hop_dong_KHAI_moc_dong_bang_va_luat_doi():
    src = _HD.read_text(encoding="utf-8")
    assert "## 6. ĐÓNG BĂNG" in src, "hợp đồng chưa khai mốc đóng băng"
    for chi_so in _DONG_BANG:
        assert chi_so in src.split("## 6. ĐÓNG BĂNG")[1]


def test_hop_dong_da_TACH_DOI_chi_so_3():
    src = _HD.read_text(encoding="utf-8")
    assert "construction_match" in src and "verification_match" in src
    assert "③a" in src and "③b" in src


# ══ CỔNG CHỐNG TRÔI CHO HELD-OUT (fire khi tập thật xuất hiện) ═══════════
def test_neu_da_co_holdout_thi_moi_bai_trong_pool_deu_co_ky_vong(GE):
    pool = GEO / "holdout" / "pool.json"
    f = KY_VONG / "holdout.json"
    if not (pool.exists() and f.exists()):
        pytest.skip("chưa có pool.json/holdout.json thật")
    d = GE.nap("holdout")
    co = {c["case_id"] for c in d["cases"]}
    # CHỈ bài `accepted`. Pool cố ý GIỮ LẠI bài bị loại kèm lý do — xoá chúng
    # là loại im lặng, mà loại im lặng là một dạng chọn tập. Nhưng bài bị loại
    # nằm NGOÀI tập đo, nên đòi kỳ vọng cho chúng là đòi soạn kỳ vọng cho thứ
    # sẽ không bao giờ được chấm.
    thieu = [c["case_id"] for c in json.loads(pool.read_text(encoding="utf-8"))["cases"]
             if c.get("status", "accepted") == "accepted" and c["case_id"] not in co]
    assert not thieu, f"pool có bài chưa soạn kỳ vọng: {thieu}"


def test_neu_da_co_holdout_thi_o_tang_A_phai_khop_BANG_O(GE):
    f = KY_VONG / "holdout.json"
    if not f.exists():
        pytest.skip("chưa có holdout.json thật")
    sh = _nap("seal_geometry_holdout")
    for c in GE.nap("holdout")["cases"]:
        o = c.get("slot")
        if not (o or "").startswith("A"):
            continue
        assert sh.BANG_O[o][0] in GE.kinds_kiem(c), (
            f"{c['case_id']}: ô {o} đòi {sh.BANG_O[o][0]!r} mà kỳ vọng không có")


# ══ tiện ích ═════════════════════════════════════════════════════════════
def _artifact(thu_muc: str, ten: str) -> dict:
    return json.loads((GEO / thu_muc / f"{ten}.json").read_text(encoding="utf-8"))


def _spec_gia(dung: list[str], kieu: str = "point3") -> dict:
    """Chương trình tối thiểu hợp lệ, mọi vật đều sinh bằng `construct_point`.

    Dựng bằng `midpoint` của hai điểm đã khai — phép dựng rẻ nhất mà vẫn là
    phép dựng thật, nên `dependency_graph` thấy được cạnh phụ thuộc.
    """
    goc = [{"name": n, "type": "point3",
            "initial_value": {"x": "0", "y": str(i), "z": "0"}}
           for i, n in enumerate(("_G1", "_G2"))]
    return {
        "spec_version": "1.0",
        "title": "spec giả cho test bộ đo",
        "memory_declarations": goc + [{"name": n, "type": kieu} for n in dung],
        "statements": [
            {"kind": "construct_point", "target_var": n,
             "expr": {"kind": "midpoint", "a": "_G1", "b": "_G2"}}
            for n in dung
        ],
    }
