# -*- coding: utf-8 -*-
"""NGHĨA VỤ TRÊN CHỦ THỂ VÔ HƯỚNG — `scalar_accumulation` + vị từ vô hướng.

VÌ SAO MỞ (2026-08-24), và vì sao đó KHÔNG phải cứu một ca: đo cơ học trên
chính `OBLIGATION_KINDS` cho thấy **0/10 nghĩa vụ nhận được một chủ thể vô
hướng** — toàn bộ taxonomy hình dạng *container*. Trong khi vòng lặp tích luỹ
trên một biên số (`S = 1+2+…+n`, `1×2×…×n`, `S = 1³+…+n³`) và câu hỏi đúng/sai
trên một số ("n chẵn hay lẻ") là hai kiến trúc cơ bản nhất của chương trình Tin
học 10. Khoảng trống của HỢP ĐỒNG, chứng minh được mà không cần nhìn đề nào.

ĐIỀU BỘ TEST NÀY PHẢI GIỮ: mở chiều vô hướng KHÔNG được biến oracle thành "tin
lời chương trình". Hai tập ĐÓNG (`op`, `term`) là chỗ ranh giới ấy được cưỡng
chế — ra ngoài tập thì câu trả lời trung thực là *mức yếu*, không phải *sai*.
"""
import pytest

from app.simulation.semantic_program.obligations import (
    OBLIGATION_KINDS,
    TERM_TRANSFORMS,
    Obligation,
)
from app.simulation.semantic_program.postconditions import (
    KhongKiemChungDuoc,
    _predicate_verdict,
    _scalar_accumulation,
)


def _ob(container="n", **params):
    return Obligation(kind="scalar_accumulation", container=container, params=params)


def _obp(container="n", **params):
    return Obligation(kind="predicate_verdict", container=container, params=params)


# ── Khoảng trống đã đóng ───────────────────────────────────────────────────


def test_truoc_khi_mo_thi_KHONG_nghia_vu_nao_nhan_chu_the_vo_huong():
    """Bất biến ngược: nay phải có ít nhất một, nếu không việc mở là vô nghĩa."""
    vo_huong = {"int", "float"}
    nhan = [k for k, mien in OBLIGATION_KINDS.items() if vo_huong & set(mien)]
    assert sorted(nhan) == ["predicate_verdict", "scalar_accumulation"]


# ── `scalar_accumulation`: đáp án KIỂM TAY ────────────────────────────────


@pytest.mark.parametrize(
    "n,op,term,dung",
    [
        (10, "sum", "identity", 55),      # 10·11/2
        (100, "sum", "identity", 5050),   # Gauss
        (5, "product", "identity", 120),  # 5!
        (3, "sum", "cube", 36),           # 1+8+27
        (4, "sum", "square", 30),         # 1+4+9+16
        (1, "sum", "identity", 1),        # biên nhỏ nhất
    ],
)
def test_tinh_lai_doc_lap_khop_dap_an_kiem_tay(n, op, term, dung):
    snap = {"n": n, "S": dung}
    assert _scalar_accumulation(snap, _ob(op=op, term=term, witness="S")) is None


@pytest.mark.parametrize("sai", [50, 56, 0, -55])
def test_khai_SAI_thi_bi_bat(sai):
    snap = {"n": 10, "S": sai}
    msg = _scalar_accumulation(snap, _ob(op="sum", witness="S"))
    assert msg and "tính lại độc lập" in msg


def test_so_thuc_co_dung_sai_bit_cuoi():
    """`1 + 1/2 + 1/3` tích luỹ theo thứ tự khác cho sai số bit khác nhau.

    Kết tội một chương trình vì bit cuối là kết tội sai — nên checker có dung
    sai, và dung sai ấy phải ĐỦ HẸP để vẫn bắt được sai thật.
    """
    dung = sum(1 / k for k in range(1, 6))
    assert _scalar_accumulation({"n": 5, "S": dung + 1e-13},
                                _ob(op="sum", term="reciprocal", witness="S")) is None
    assert _scalar_accumulation({"n": 5, "S": dung + 0.01},
                                _ob(op="sum", term="reciprocal", witness="S"))


@pytest.mark.parametrize("term", ["fibonacci", "giai_thua", "bat_ky", None])
def test_so_hang_NGOAI_tap_dong_thi_YEU_chu_khong_ket_toi(term):
    """Đóng là điều kiện của tính độc lập.

    Mở cho một số hạng bất kỳ thì checker phải ĐÁNH GIÁ biểu thức của chương
    trình — tức chạy lại chính nó, và oracle mất nghĩa ngay tại đó. Câu trả lời
    trung thực khi ấy là "tôi không kiểm được", không phải "bạn sai".
    """
    if term is None:
        pytest.skip("thiếu `term` mặc định về identity — đã có test riêng")
    with pytest.raises(KhongKiemChungDuoc):
        _scalar_accumulation({"n": 5, "S": 1}, _ob(op="sum", term=term, witness="S"))


@pytest.mark.parametrize("op", ["count", "max", "min", "trung_binh", None])
def test_phep_gop_NGOAI_sum_product_thi_YEU(op):
    with pytest.raises(KhongKiemChungDuoc):
        _scalar_accumulation({"n": 5, "S": 1}, _ob(op=op, witness="S"))


def test_tap_so_hang_van_DONG():
    assert TERM_TRANSFORMS == {"identity", "square", "cube", "reciprocal"}


def test_bien_nho_hon_moc_bat_dau_thi_NGHIA_VU_VO_HIEU():
    """`n = 0` với biên bắt đầu 1: tổng rỗng ra 0, và so witness với 0 đọc y như
    "đáp án của bạn sai". Phải nói rõ nghĩa vụ vô hiệu — cùng bài học với
    `_nghia_vu_vo_hieu` đã ghi từ SEALED `T11CS-C6-041`."""
    msg = _scalar_accumulation({"n": 0, "S": 0}, _ob(op="sum", witness="S"))
    assert msg and "VÔ HIỆU" in msg


def test_witness_khong_phai_so_thi_bi_bat():
    assert _scalar_accumulation({"n": 5, "S": "mười lăm"}, _ob(op="sum", witness="S"))


# ── Vị từ trên chủ thể VÔ HƯỚNG ───────────────────────────────────────────


@pytest.mark.parametrize(
    "n,pred,khai,mong_vi_pham",
    [
        (10, "even", True, False),
        (10, "even", False, True),
        (7, "even", True, True),
        (7, "odd", True, False),
        (10, "gt", True, False),   # ngưỡng dưới
        (3, "gt", True, True),
    ],
)
def test_vi_tu_vo_huong_dung_tap_PREDS_co_san(n, pred, khai, mong_vi_pham):
    ob = _obp(pred=pred, witness="r", threshold=5)
    msg = _predicate_verdict({"n": n, "r": khai}, ob)
    assert bool(msg) is mong_vi_pham, msg


def test_vi_tu_vo_huong_NGOAI_tap_thi_YEU():
    """"Năm nhuận" không nằm trong tập sơ cấp — và KHÔNG được thêm vào.

    Thêm một checker cho mỗi vị từ có tên là biến oracle thành từ điển thuật
    toán. Câu trả lời đúng là `verification_gap`: chạy được, chưa chứng minh
    được, không phát canonical.
    """
    with pytest.raises(KhongKiemChungDuoc):
        _predicate_verdict({"n": 2024, "r": True}, _obp(pred="nam_nhuan", witness="r"))


def test_chu_the_TAP_HOP_van_di_duong_cu():
    """Mở chiều vô hướng không được cướp đường của chủ thể tập hợp."""
    ob = _obp(container="s", pred="balanced_delimiters", witness="r")
    assert _predicate_verdict({"s": list("{[()]}"), "r": True}, ob) is None
    assert _predicate_verdict({"s": list("([)]"), "r": True}, ob)
