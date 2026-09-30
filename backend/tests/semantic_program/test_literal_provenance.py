# -*- coding: utf-8 -*-
"""P1 — literal của đề phải neo được về span, và `analyze` không được bịa thêm.

Bốn ca ở `test_bon_ca_bat_buoc_cua_wave` là bốn ca vNext §3 nêu đích danh. Ca
thứ nhất là ca ĐÃ QUAN SÁT ĐƯỢC trong sản phẩm, không phải giả định: probe
2026-08-23 trên đề chuỗi ngoặc trả `analysis.data[0].values = null` trong khi
`notes` của chính lượt đó ghi *"Đề bài cung cấp ví dụ cụ thể là chuỗi '{[()]}'"*.
"""
from app.simulation.semantic_program.analyze_contract import build_request_contract
from app.simulation.semantic_program.literal_extractor import (
    extract_literals,
    gia_tri_kem_ky_tu,
    verify_candidate,
)

DE_STACK = "Kiểm tra tính hợp lệ của chuỗi đóng mở ngoặc bằng Stack với chuỗi {[()]}."
DE_MANG = "Cho mảng [3, 1, 4], hãy tìm phần tử lớn nhất."
DE_SCALAR = "Với n = 10, tính tổng các số từ 1 đến n."


def _payload(fid: str, kind: str, label: str, value=None) -> dict:
    muc = {"id": fid, "kind": kind, "label": label}
    if value is not None:
        muc["value"] = value
    return {"input_facts": [muc], "obligations": []}


# ── §2 — extractor ────────────────────────────────────────────────────────────


def test_moi_literal_trich_duoc_deu_tu_chung_minh_duoc():
    """BẤT BIẾN P1: cắt lại `text[start:end]` phải tái tạo đúng giá trị."""
    for de in (DE_STACK, DE_MANG, DE_SCALAR, 'Đếm nguyên âm trong xâu "hello".'):
        cands = extract_literals(de)
        assert cands, f"không trích được literal nào từ: {de}"
        for c in cands:
            assert de[c.source_start : c.source_end] == c.source_text
            assert verify_candidate(c, de), f"{c.source_text!r} không tự chứng minh được"


def test_so_cuoi_cau_truoc_dau_cham_van_la_literal():
    """W12: `(?![\\w.])` bỏ mọi số đứng trước dấu chấm câu — *"có cạnh bằng 4."*
    ra `4` "không có trong đề" (P1 `claimed`), và từ W12 cổng grounding ĐỌC P1.
    Số thập phân vẫn đọc nguyên khối, không vỡ thành hai số."""
    so = [x for x in extract_literals("Cho hình lập phương ABCD.A'B'C'D' có cạnh bằng 4.")
          if x.kind in ("int", "float")]
    assert [(x.normalized_value, x.source_text) for x in so] == [((4,), "4")]
    assert [x.normalized_value for x in extract_literals("SA = 1.5.")] == [(1.5,)]
    assert [x.source_text for x in extract_literals("bán kính 2.5 và cạnh 3.")] == ["2.5", "3"]


def test_dau_phay_cua_ten_diem_khong_phai_dau_nhay_mo_chuoi():
    """W12: `AA' = 5 … ABCD.A'` từng đọc thành MỘT chuỗi trong nháy đơn nuốt
    luôn số 5 ⇒ `AA' = 5` ra "không có trong đề". Dấu phẩy dính chữ hoa là ký
    hiệu điểm; chuỗi trong nháy mở sau khoảng trắng/dấu câu vẫn đọc như cũ."""
    de = "Cho hình hộp chữ nhật ABCD.A'B'C'D' có AB = 3, AD = 4, AA' = 5. Tính thể tích."
    assert [(c.kind, c.source_text) for c in extract_literals(de)] == [
        ("int", "3"), ("int", "4"), ("int", "5")]
    assert [c.normalized_value for c in extract_literals("Đếm nguyên âm trong xâu 'hello'.")] == [
        ("hello",)]


def test_so_thap_phan_viet_bang_dau_phay_van_chung_minh_duoc():
    """W12: đề Việt viết `2,5`; `analyze` khai `2.5`. Extractor không đọc dấu
    phẩy thập phân (đọc thì `A(1,2,3)` vỡ), nên P1 kết tội `2.5` "không có
    trong đề" — và từ W12 lời kết tội ấy là một lời TỪ CHỐI. Dấu phẩy nằm trong
    một dãy số (`1,2,3`) thì không phải dấu thập phân."""
    from app.simulation.semantic_program.literal_extractor import (
        gia_tri_khong_chung_minh_duoc as p1,
    )

    de = "Cho mặt cầu bán kính R = 2,5 cm."
    assert p1((2.5,), extract_literals(de), de) == ()
    toa_do = "Cho A(1,2,3) và B(0;0;0)."
    assert p1((1.2,), extract_literals(toa_do), toa_do) == (1.2,)
    assert p1((3.5,), extract_literals(de), de) == (3.5,)


def test_ten_diem_viet_chi_so_duoi_van_chung_minh_duoc():
    """W12: đề viết `A₁`, `analyze` khai `A1` — cùng một tên (chuẩn hoá NFKC,
    như dấu phẩy `′`). Không có bậc này, một mục ĐẶT TÊN điểm bị coi là số liệu
    bịa và toạ độ ghim vào nó bị từ chối oan (ca `e8` của gold affordance)."""
    from app.simulation.semantic_program.literal_extractor import (
        gia_tri_khong_chung_minh_duoc as p1,
    )

    de = "Cho hình trụ có hai đáy là hai đường tròn tâm A₁ và tâm A₂."
    assert p1(("A1", "A2"), extract_literals(de), de) == ()
    assert p1(("A3",), extract_literals(de), de) == ("A3",)


def test_extractor_tat_dinh():
    """Cùng đề ⇒ cùng kết quả. Không phụ thuộc model, mạng hay thời điểm."""
    assert extract_literals(DE_STACK) == extract_literals(DE_STACK)


def test_mang_duoc_doc_nguyen_khoi_khong_vo_thanh_so_le():
    """`[3, 1, 4]` là MỘT mảng, không phải ba số rời — ưu tiên khớp dài nhất."""
    cands = extract_literals(DE_MANG)
    assert [c.kind for c in cands] == ["array"]
    assert cands[0].normalized_value == (3, 1, 4)


def test_gan_vo_huong_giu_ten_lam_goi_y():
    cands = extract_literals(DE_SCALAR)
    n = [c for c in cands if c.label_hint == "n"]
    assert len(n) == 1 and n[0].normalized_value == (10,)


def test_chuoi_mo_rong_ra_ky_tu_de_bai_quet_chuoi_khong_truot_vi_hinh_dang():
    (c,) = extract_literals(DE_STACK)
    assert gia_tri_kem_ky_tu(c) == ("{[()]}", "{", "[", "(", ")", "]", "}")


def test_span_sai_thi_verify_do():
    """Guard phải ĐỎ ĐƯỢC — một guard chưa từng đỏ là guard chưa được chứng minh."""
    (c,) = extract_literals(DE_STACK)
    assert not verify_candidate(c.model_copy(update={"source_start": c.source_start + 1}), DE_STACK)
    assert not verify_candidate(c.model_copy(update={"normalized_value": ("[[[]]]",)}), DE_STACK)


# ── §3 — merge ────────────────────────────────────────────────────────────────


def test_bon_ca_bat_buoc_cua_wave():
    # 1. Ca đã quan sát: analyze trả rỗng, đề có literal ⇒ hợp đồng VẪN có nó.
    c = build_request_contract(_payload("s", "str", "chuỗi ngoặc"), DE_STACK)
    f = c.fact("s")
    assert f.provenance == "extracted"
    assert "{[()]}" in f.values
    assert DE_STACK[f.source_start : f.source_end] == "{[()]}"

    # 2. Mảng giữ đúng phần tử.
    c = build_request_contract(_payload("a", "array", "mảng"), DE_MANG)
    assert c.fact("a").values == (3, 1, 4)

    # 3. Vô hướng giữ đúng giá trị, và khớp đúng NHÃN chứ không lấy số đầu tiên.
    c = build_request_contract(_payload("n", "int", "n"), DE_SCALAR)
    assert c.fact("n").values == (10,)

    # 4. analyze bịa giá trị đề không có ⇒ bị bắt, kèm đúng thủ phạm.
    c = build_request_contract(_payload("a", "array", "mảng", ["5", "3", "9"]), DE_MANG)
    f = c.fact("a")
    assert f.provenance == "claimed"
    assert set(f.unproven_values) == {5, 9}  # 3 có thật trong [3, 1, 4]


def test_gia_tri_dung_that_thi_duoc_xac_nhan_chu_khong_bi_trach():
    c = build_request_contract(_payload("a", "array", "mảng", ["3", "1", "4"]), DE_MANG)
    f = c.fact("a")
    assert f.provenance == "confirmed" and f.unproven_values == ()


def test_khong_co_de_thi_khong_ket_luan_gi():
    """Đường gọi cũ (không truyền `problem_text`) giữ nguyên hành vi trước vNext."""
    c = build_request_contract(_payload("a", "array", "mảng", ["7"]))
    f = c.fact("a")
    assert f.provenance == "unchecked" and f.unproven_values == ()
    assert f.values == (7,)


def test_kind_khong_co_cu_phap_literal_thi_khong_bi_doan_bua():
    """Đồ thị/cây mô tả bằng văn xuôi KHÔNG bị extractor lấp bừa một con số."""
    de = "Cho đồ thị gồm 5 đỉnh A, B, C, D, E và duyệt theo chiều rộng từ A."
    c = build_request_contract(_payload("g", "graph", "đồ thị"), de)
    f = c.fact("g")
    assert f.values == () and f.provenance == "confirmed"


def test_nhan_rut_tu_van_xuoi_khong_bi_tu_choi_oan():
    """Tên đỉnh là dữ liệu thật của đề dù không phải literal có cú pháp."""
    de = "Cho đồ thị gồm các đỉnh A, B, C và duyệt theo chiều rộng từ A."
    c = build_request_contract(_payload("g", "set", "đỉnh", ["A", "B", "C"]), de)
    assert c.fact("g").provenance == "confirmed"
