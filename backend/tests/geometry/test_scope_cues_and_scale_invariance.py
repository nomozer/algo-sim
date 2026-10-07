# -*- coding: utf-8 -*-
"""WAVE 3 — bảng manh mối phải PHỦ tập đề, và oracle phải BẤT BIẾN THANG.

Hai lỗi do lượt xác nhận POSTFIX_V1 chỉ ra, cả hai đều ở phía hệ/bộ đo.

① `hp_a03_007` chết ở cổng phạm vi **2/2 lượt**. Đề nói *"Chứng minh MPNQ là
   **hình bình hành**"* — không có chữ "song song" nào — nên bảng manh mối
   không tới được nghĩa vụ `parallel`, `co_duong_thuc_thi` trả False, và cổng
   chặn. Trớ trêu: chính bài ấy đã mang `phep_chuyen` ghi rõ
   `parallelogram(M,P,N,Q) ⇒ MP ∥ NQ và PN ∥ MQ`. **Bộ đo biết phép tương
   đương, còn cổng thì không.**

② `hp_a11_027-lan2` bị chấm *"hệ nhận một diễn giải SAI"* — cáo buộc nặng
   nhất có thể. Đọc trạng thái cuối thì chương trình ĐÚNG: nó chọn thang
   `a = 25` (thang nhỏ nhất làm cả `a` lẫn `3a/5` nguyên), và `12/25 = 12/25`.
   Đề để `a` TỰ DO; `a = 1` là quy ước sống trong `phep_chuyen` của bộ đo.

─── VÌ SAO TEST ① DẪN TỪ POOL, KHÔNG CHÉP TAY ────────────────────────────

Một danh sách manh mối viết tay sẽ lệch khỏi tập đề đúng ở bài tiếp theo.
Test dưới quét **mọi bài `accepted` của pool** và đòi manh mối tới được đúng
nghĩa vụ mà `oracle_result` khai. Thêm đề mới mà quên dạy cách nói của nó là
ĐỎ ngay, không phải đỏ ở một lượt đo đã tiêu quota.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from app.simulation.semantic_program.domain_profile import (
    DOMAIN_TIN_HOC,
    _MANH_MOI_NGHIA_VU,
    co_duong_thuc_thi,
    detect_domain,
    nghia_vu_ung_vien,
)
from app.simulation.semantic_program.geometry_obligations import (
    GEOMETRY_CHECKERS,
)

ROOT = Path(__file__).resolve().parents[3]
GEO = ROOT / "docs" / "evaluation" / "geometry"


def _pool_tang_a() -> list[dict]:
    p = json.loads((GEO / "holdout" / "pool.json").read_text(encoding="utf-8"))
    return [c for c in p["cases"]
            if c.get("status", "accepted") == "accepted" and c.get("oracle_result")]


def test_manh_moi_PHU_moi_bai_tang_A_cua_pool():
    """Dẫn từ dữ liệu, không từ danh sách. Đây là test đã bắt `hp_a03_007`."""
    thieu = [(c["case_id"], c["slot"], next(iter(c["oracle_result"])))
             for c in _pool_tang_a()
             if next(iter(c["oracle_result"]))
             not in nghia_vu_ung_vien(c["problem_text"])]
    assert not thieu, f"bảng manh mối không tới được nghĩa vụ: {thieu}"


@pytest.mark.parametrize("de", [
    "Cho tứ diện ABCD. Gọi M, N, P, Q lần lượt là trung điểm của AB, CD, BC, "
    "AD. Chứng minh MPNQ là hình bình hành.",
    "Cho hình chóp S.ABCD. Chứng minh tứ giác MNPQ là hình thoi.",
    "Cho hình lăng trụ ABC.A'B'C'. Chứng minh ABB'A' là hình chữ nhật.",
])
def test_HINH_BINH_HANH_va_ho_hang_deu_toi_duoc_parallel(de):
    """Hình bình hành · thoi · chữ nhật · vuông đều có hai cặp cạnh đối song
    song **theo định nghĩa SGK** — không phải một định lý phải chứng minh."""
    assert "parallel" in nghia_vu_ung_vien(de), de
    assert co_duong_thuc_thi(de, "hinh_hoc"), de


@pytest.mark.parametrize("de", [
    "Viết chương trình tính diện tích hình chữ nhật.",
    "Viết chương trình kiểm tra một tứ giác có phải hình vuông không.",
    "Cho mảng các hình bình hành, viết thuật toán đếm số hình có diện tích lớn "
    "hơn 10.",
])
def test_tu_vung_MOI_khong_keo_de_TIN_HOC_sang_hinh_hoc(de):
    """Nửa kia của phép mở: thêm `hình chữ nhật`/`hình vuông` vào manh mối mà
    kéo nhầm đề Tin học thì đổi một lỗi lấy một lỗi khác."""
    assert detect_domain(de) == DOMAIN_TIN_HOC, de
    assert not co_duong_thuc_thi(de, detect_domain(de)), de


def test_moi_khoa_manh_moi_deu_co_CHECKER():
    """Thêm manh mối cho nghĩa vụ không có checker là MỞ NĂNG LỰC lén."""
    assert set(_MANH_MOI_NGHIA_VU) <= set(GEOMETRY_CHECKERS)


# ══ ② ORACLE BẤT BIẾN THANG ══════════════════════════════════════════════
def _dev():
    import importlib.util
    import sys
    if "_devrun" in sys.modules:
        return sys.modules["_devrun"]
    d = ROOT / "backend" / "scripts" / "run_geometry_dev_evaluation.py"
    spec = importlib.util.spec_from_file_location("_devrun", d)
    m = importlib.util.module_from_spec(spec)
    sys.modules["_devrun"] = m
    spec.loader.exec_module(m)
    return m


def _bo(kind: str, container: str, witness: str, fact_id: str, gt: str):
    from app.simulation.semantic_program.obligations import Obligation
    from app.simulation.semantic_program.request_contract import (
        InputFact, RequestContract,
    )
    return RequestContract(
        obligations=(Obligation(kind=kind, container=container,
                                params={"witness": witness}),),
        input_facts=(InputFact(fact_id=fact_id, label=fact_id, values=[gt]),))


def _hien_truong(thang: int) -> dict:
    """Đúng hình của `hp_a11_027` ở một thang bất kỳ: tam giác SAB vuông tại
    S với AB = thang, SA = 3·thang/5 ⇒ d(S,(ABC)) = 12·thang/25."""
    from fractions import Fraction as F
    from app.simulation.geometry.exact import Plane3, Vec3
    V = Vec3.of
    s = F(thang, 25)
    return {"A": V(-9 * s, 0, 0), "B": V(16 * s, 0, 0), "S": V(0, 0, 12 * s),
            "ABC": Plane3(V(0, 0, 0), V(0, 0, 1)),
            "kq": 12 * s}


@pytest.mark.parametrize("thang", [25, 50, 5])
def test_thang_KHAC_a1_van_duoc_cham_DUNG(thang):
    """Đề để `a` tự do, prompt bảo mô hình tự chọn hệ trục — nên nó cũng tự
    chọn thang. So giá trị tuyệt đối là chấm *mô hình có tình cờ chọn a = 1
    không*, không chấm hình học."""
    DEV = _dev()
    case = {"oracle_result": {"distance": "12/25"}}
    hd = _bo("distance", "ABC", "kq", "ab_length", "a")
    r = DEV.cham_oracle(case, hd, _hien_truong(thang))
    assert r["verdict"] == "PASS", r


def test_thang_a1_van_dung_nhu_cu():
    DEV = _dev()
    from fractions import Fraction as F
    case = {"oracle_result": {"distance": "12/25"}}
    hd = _bo("distance", "ABC", "kq", "ab_length", "a")
    fm = _hien_truong(25)
    fm["kq"] = F(12, 25) * 1          # thang a = 1 ⇒ giá trị đúng bằng đáp án
    fm |= {k: v for k, v in _hien_truong(1).items() if k != "kq"}
    assert DEV.cham_oracle(case, hd, fm)["verdict"] == "PASS"


def test_SAI_THAT_van_bi_bat():
    """Phép chuẩn hoá thang KHÔNG được nuốt một kết quả sai thật."""
    DEV = _dev()
    case = {"oracle_result": {"distance": "12/25"}}
    hd = _bo("distance", "ABC", "kq", "ab_length", "a")
    fm = _hien_truong(25)
    fm["kq"] = 13                      # sai, không phải chuyện thang
    assert DEV.cham_oracle(case, hd, fm)["verdict"] == "FAIL"


def test_KHONG_suy_duoc_thang_thi_UNGRADED_khong_phai_FAIL():
    """Không chấm được ≠ sai. Gộp hai cái là biến giới hạn của bộ đo thành
    cáo buộc về mô hình — đã xảy ra ba lần trong dự án này."""
    DEV = _dev()
    case = {"oracle_result": {"distance": "12/25"}}
    hd = _bo("distance", "ABC", "kq", "khong_ro", "a")   # fact_id không nêu đoạn
    fm = _hien_truong(25)
    assert DEV.cham_oracle(case, hd, fm)["verdict"] == "UNGRADED"
