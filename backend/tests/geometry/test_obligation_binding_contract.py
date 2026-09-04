# -*- coding: utf-8 -*-
"""HỢP ĐỒNG BUỘC TÊN giữa nghĩa vụ và vật được đo. **0 lượt gọi model.**

    `BALL_CENTER_RADIUS_EXPRESSIVENESS_DESIGN`, 2026-09-04.

Wave này KHÔNG mở năng lực toán học nào: mặt cầu ngoại tiếp vốn đã diễn đạt
được bằng IR hiện có. Nó đóng hai lỗ HỢP ĐỒNG mà một lượt đo thật đã phơi ra
(`docs/SMALL_DEVELOPMENT_PROBE.md`):

  ① cổng phủ đọc `memory_declarations` rồi coi đó là toàn bộ chương trình, nên
    mọi vật dựng bằng `construct_*` mà mô hình không khai đều VÔ HÌNH với nó —
    trong khi runtime và `kiem_tinh` đều thấy chúng;
  ② không có luật nào nối `obligation.container` với vật thật sự mang số đo,
    khi vật ấy là vật DẪN XUẤT mà đề không đặt tên.

Fixture là artifact `circumsphere` THẬT, không phải chương trình viết lại cho
vừa: `docs/evaluation/geometry/probe-contract-waves-2`.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from app.simulation.geometry.radical import display, is_exact_number
from app.simulation.semantic_program import coverage_gate as CG
from app.simulation.semantic_program.contract import SemanticProgramSpec
from app.simulation.semantic_program.coverage_gate import (
    KIEU_KHONG_HOP,
    LY_DO_CHAN_DOAN,
    RANG_BUOC_MO_HO,
    RANG_BUOC_THIEU,
    THIEU_KHAI_BAO,
    check_structural_coverage,
)
from app.simulation.semantic_program.obligations import Obligation
from app.simulation.semantic_program.request_contract import RequestContract
from app.simulation.semantic_program.route import verify_and_compile

GOC = Path(__file__).resolve().parents[3]
CA_CONG = GOC / "docs/evaluation/geometry/probe-contract-waves-2/cases/circumsphere/final.json"
CA_TRU = GOC / "docs/evaluation/geometry/probe-contract-waves/cases/cylinder_2/final.json"


def _nap(duong: Path):
    d = json.loads(duong.read_text(encoding="utf-8"))
    return (RequestContract.model_validate(d["request_contract"]),
            SemanticProgramSpec.model_validate(d["chuong_trinh"]), d)


@pytest.fixture
def circumsphere():
    """Chương trình mô hình THẬT SỰ viết, không sửa một byte."""
    return _nap(CA_CONG)


def _dai_luong(oc) -> dict[str, str]:
    return {k: display(v) for k, v in (oc.final_memory or {}).items()
            if is_exact_number(v)}


# ══ A · DỰNG LẠI LƯỢT BÁC CŨ, RỒI CHỨNG MINH NÓ ĐÃ ĐÓNG ═══════════════════
def test_A1_khong_co_net_witness_thi_van_bac_DUNG_NHU_artifact(
        circumsphere, monkeypatch):
    """Tiêm lại trạng thái TRƯỚC bản vá: bỏ net ⓪ đi thì lượt bác cũ trở lại.

    Không có phép tiêm này thì `test_A2` chỉ chứng minh "hôm nay xanh", chứ
    không chứng minh **cái gì** làm nó xanh — và một guard chưa từng đỏ là một
    guard chưa được chứng minh.
    """
    ct, spec, d = circumsphere
    monkeypatch.setattr(CG, "_do_theo_witness", lambda _: {})
    oc = verify_and_compile(ct, spec)

    assert oc.stage_reached == "structural_coverage"
    assert oc.error_code == d["error_code"] == "requested_operation_uncovered"
    assert oc.details == d["details"]  # y hệt chuỗi artifact đã ghi
    assert not oc.servable


def test_A2_chuong_trinh_NGUYEN_VAN_cua_mo_hinh_chay_toi_served(circumsphere):
    """R = √3, không sửa chương trình, không thêm khai báo, không đổi tên.

    Đây là toàn bộ mục tiêu wave: mô hình đã viết một chương trình ĐÚNG, và
    hệ phải phục vụ được nó mà không đòi thêm boilerplate.
    """
    ct, spec, d = circumsphere
    oc = verify_and_compile(ct, spec)

    assert oc.servable, oc.details
    assert oc.stage_reached == "served"
    assert _dai_luong(oc)["R"] == "√3" == d["mong"][0]


def test_A3_noi_ten_qua_WITNESS_va_ghi_lai_duong_da_noi(circumsphere):
    """Ánh xạ phải ghi rõ nối bằng lưới nào — nếu không thì lượt đo sau không
    phân biệt được "hợp đồng khớp sẵn" với "hệ phải ra tay"."""
    ct, spec, _ = circumsphere
    kq = check_structural_coverage(ct, spec)

    assert kq.ok
    assert kq.ten_da_hoa_giai == {"OABC": "circumsphere"}
    assert any("witness đo" in d for d in kq.symbol_reconciled)


def test_A4_vat_dung_ra_ma_KHONG_khai_van_nhin_thay_duoc(circumsphere):
    """Lỗ ①. Mô hình chỉ khai `OABC` và `R`; quả cầu đến từ `construct_*`."""
    from app.simulation.semantic_program.ir_static_check import bang_ky_hieu

    _, spec, _ = circumsphere
    khai = {d.name for d in spec.memory_declarations}
    bang = bang_ky_hieu(spec)

    assert "circumsphere" not in khai, "tiền đề hỏng — mô hình đã khai rồi"
    assert bang["circumsphere"] == "curved_solid"
    assert bang["OABC"] == "solid", "khai báo tường minh phải THẮNG"


# ══ B · BỐN BỆNH, BỐN MÃ — không phân loại bằng chuỗi tiếng Việt ═══════════
_DIEM = [{"name": t, "type": "point3", "initial_value": v,
          "source_fact_id": "f"}
         for t, v in (("P", [0, 0, 0]), ("Q", [2, 0, 0]), ("Rr", [0, 2, 0]),
                      ("S", [0, 0, 2]))]
_DINH = ["P", "Q", "Rr", "S"]
_MAT = [["P", "Q", "Rr"], ["P", "Q", "S"], ["P", "Rr", "S"], ["Q", "Rr", "S"]]


def _ct(kind: str, container: str, witness: str = "V") -> RequestContract:
    return RequestContract(
        problem_text="Cho tứ diện PQRS. Tính thể tích.",
        input_facts=[{"fact_id": "f", "label": "Tứ diện PQRS",
                      "values": ["PQRS"], "provenance": "confirmed"}],
        obligations=(Obligation(kind=kind, container=container,
                                params={"witness": witness}),))


def _spec(khai: list[dict], stmts: list[dict]) -> SemanticProgramSpec:
    return SemanticProgramSpec.model_validate({
        "title": "Kiểm hợp đồng buộc tên",
        "memory_declarations": _DIEM + khai, "statements": stmts})


_DUNG_KHOI = {"kind": "construct_solid", "target_var": "khoi",
              "vertices": _DINH, "faces": _MAT}
_DO_KHOI = {"kind": "assign", "target_var": "V",
            "expr": {"kind": "measure", "quantity": "volume", "of": "khoi"}}


def _ly_do(kq) -> list[str]:
    return [c.ly_do for c in kq.chan_doan]


def test_B1_container_VANG_MAT_la_THIEU_KHAI_BAO():
    """Đề gọi tên một vật chương trình chưa dựng. Net ⓪ KHÔNG được cứu ca này."""
    kq = check_structural_coverage(
        _ct("volume", "hinh_lang_tru"),
        _spec([{"name": "V", "type": "float"}], [_DUNG_KHOI, _DO_KHOI]))

    assert not kq.ok
    assert _ly_do(kq) == [THIEU_KHAI_BAO]
    assert "khoi" in kq.chan_doan[0].ung_vien


def test_B2_container_CO_nhung_SAI_KIEU_va_khong_go_duoc_la_KIEU_KHONG_HOP():
    """`cylinder_2` THẬT: đo `radius` trên một `section`.

    Net ⓪ chạy (tên có, sai kiểu) nhưng KHÔNG nối được, vì chủ thể phép đo
    cũng sai kiểu. Cổng vẫn bác — đây là ca chứng minh net ⓪ không phải cửa sau.
    """
    ct, spec, _ = _nap(CA_TRU)
    kq = check_structural_coverage(ct, spec)

    assert not kq.ok
    assert _ly_do(kq) == [KIEU_KHONG_HOP]
    assert kq.chan_doan[0].kieu_container == "section"
    assert kq.chan_doan[0].kieu_chap_nhan == ["circle3", "curved_solid"]


def test_B3_noi_duoc_NHIEU_vat_thi_fail_closed():
    """Hai phép đo cùng lượng, cùng witness, hai chủ thể hợp lệ ⇒ mơ hồ.

    Hệ KHÔNG chọn hộ, kể cả khi cả hai đều đúng kiểu.
    """
    khoi2 = {**_DUNG_KHOI, "target_var": "khoi2"}
    do2 = {"kind": "assign", "target_var": "V",
           "expr": {"kind": "measure", "quantity": "volume", "of": "khoi2"}}
    # `PQRS` khai kiểu KHÔNG nhận được `volume` ⇒ net ⓪ được phép chạy.
    kq = check_structural_coverage(
        _ct("volume", "PQRS"),
        _spec([{"name": "V", "type": "float"},
               {"name": "PQRS", "type": "polygon3"}],
              [_DUNG_KHOI, khoi2, _DO_KHOI, do2]))

    assert not kq.ok
    assert _ly_do(kq) == [RANG_BUOC_MO_HO]
    assert sorted(kq.chan_doan[0].ung_vien) == ["khoi", "khoi2"]


def test_B4_witness_khong_co_producer_la_RANG_BUOC_THIEU():
    kq = check_structural_coverage(
        _ct("volume", "khoi"),
        _spec([{"name": "V", "type": "float", "initial_value": 8}],
              [_DUNG_KHOI]))

    assert not kq.ok
    assert _ly_do(kq) == [RANG_BUOC_THIEU]


def test_B5_moi_ma_chan_doan_deu_thuoc_bang_da_khai():
    """Mã lạ lọt vào là tầng sau phân loại trượt trong im lặng."""
    for duong in (CA_CONG, CA_TRU):
        ct, spec, _ = _nap(duong)
        for c in check_structural_coverage(ct, spec).chan_doan:
            assert c.ly_do in LY_DO_CHAN_DOAN


# ══ C · KHÔNG ĐẶC CÁCH CHO KHỐI CONG ══════════════════════════════════════
def test_C1_da_dien_thuong_KHONG_doi_hanh_vi():
    """Đường đa diện vốn xanh phải xanh y như cũ, kể cả tên khớp sẵn."""
    oc = verify_and_compile(
        _ct("volume", "khoi"),
        _spec([{"name": "V", "type": "float"}], [_DUNG_KHOI, _DO_KHOI]))

    assert oc.servable, oc.details
    assert _dai_luong(oc)["V"] == "4/3"


def test_C2_TRU_di_dung_duong_thi_served_khong_can_net_nao():
    """Cùng đề `cylinder_2`, nhưng dùng `intersect_plane_curved` như thẻ khai.

    Chứng minh hai điều cùng lúc: từ vựng khối cong ĐỦ để giải bài ấy, và bản
    vá không hề ưu ái hình cầu — trụ đi qua cùng một cổng.
    """
    ct = RequestContract(
        problem_text="Hình trụ, mặt phẳng vuông góc trục tại trung điểm.",
        input_facts=[{"fact_id": "f", "label": "Trụ", "values": ["5"],
                      "provenance": "confirmed"}],
        obligations=(Obligation(kind="radius", container="C",
                                params={"witness": "r"}),))
    spec = SemanticProgramSpec.model_validate({
        "title": "Bán kính thiết diện của trụ",
        "memory_declarations": [
            {"name": "O", "type": "point3", "initial_value": [0, 0, 0],
             "source_fact_id": "f"},
            {"name": "Op", "type": "point3", "initial_value": [0, 0, 8],
             "source_fact_id": "f"},
            {"name": "A", "type": "point3", "initial_value": [5, 0, 0],
             "source_fact_id": "f"},
            {"name": "r", "type": "float"},
        ],
        "statements": [
            {"kind": "construct_curved_solid", "target_var": "tru",
             "curved_kind": "cylinder", "anchor": "O", "apex_or_top": "Op",
             "rim_point": "A"},
            {"kind": "construct_point", "target_var": "M",
             "expr": {"kind": "midpoint", "a": "O", "b": "Op"}},
            {"kind": "construct_line", "target_var": "truc",
             "through_a": "O", "through_b": "Op"},
            {"kind": "assign", "target_var": "mp",
             "expr": {"kind": "plane_perpendicular_to_line", "point": "M",
                      "line": "truc"}},
            {"kind": "assign", "target_var": "C",
             "expr": {"kind": "intersect_plane_curved", "solid": "tru",
                      "plane": "mp"}},
            {"kind": "assign", "target_var": "r",
             "expr": {"kind": "measure", "quantity": "radius", "of": "C"}},
        ]})
    oc = verify_and_compile(ct, spec)

    assert oc.servable, oc.details
    assert _dai_luong(oc)["r"] == "5"
    # Tên đã khớp sẵn ⇒ KHÔNG lưới nào phải ra tay.
    assert check_structural_coverage(ct, spec).ten_da_hoa_giai == {}


def test_C3_khong_co_nhanh_nao_theo_curved_kind():
    """Quét MÃ: không được có nhánh `ball`/`cylinder`/`cone` trong hai cổng."""
    import inspect

    from app.simulation.semantic_program import postconditions as PC

    for mod in (CG, PC):
        src = inspect.getsource(mod)
        # `curved_kind` xuất hiện trong bảng dẫn xuất là bình thường; điều cấm
        # là SO SÁNH với một loại cụ thể.
        for xau in ('== "ball"', '== "cylinder"', '== "cone"',
                    '"ball" ==', 'curved_kind ==',):
            assert xau not in src, f"{mod.__name__} đặc cách theo loại khối"


# ══ D · KHÔNG NỚI THỨ KHÁC ════════════════════════════════════════════════
def test_D1_R0_grounding_KHONG_bi_noi():
    """Điểm có toạ độ mà không có xuất xứ vẫn phải chết ở grounding.

    Chính lượt 1 của `circumsphere` chết ở đây, và nó PHẢI tiếp tục chết.
    """
    khai = [dict(d) for d in _DIEM]
    khai[0].pop("source_fact_id")
    spec = SemanticProgramSpec.model_validate({
        "title": "Thiếu xuất xứ",
        "memory_declarations": khai + [{"name": "V", "type": "float"}],
        "statements": [_DUNG_KHOI, _DO_KHOI]})
    oc = verify_and_compile(_ct("volume", "khoi"), spec)

    assert not oc.servable
    assert oc.stage_reached == "grounding"


def test_D2_chuong_trinh_LICH_SU_van_parse():
    """Mọi chương trình đã ghi trong artifact phải còn đọc được.

    Wave này không đổi lược đồ IR; test đứng đây để nếu ai đó đổi, nó đỏ.
    """
    # CHỈ chương trình đã được CHẤP NHẬN một lần. Artifact cố ý giữ cả ứng viên
    # thô HỎNG LƯỢC ĐỒ (`REPAIR_FRAGMENT_COMPLETENESS` sinh ra để giữ chúng),
    # nên "mọi dict trông giống chương trình" là tiền đề sai: quét kiểu ấy bắt
    # phải một `construct_point.expr = arith` mà mô hình từng viết sai, rồi đỏ
    # vì một lỗi KHÔNG phải của wave này. Hai khoá dưới là chỗ runner ghi bản
    # ĐÃ parse — chúng phải parse lại được, hôm nay và mọi hôm sau.
    KHOA = ("chuong_trinh", "semantic_program")

    def _quet(x, ra: list) -> None:
        if isinstance(x, dict):
            for k, v in x.items():
                if k in KHOA and isinstance(v, dict) and \
                        isinstance(v.get("statements"), list):
                    ra.append(v)
                _quet(v, ra)
        elif isinstance(x, list):
            for v in x:
                _quet(v, ra)

    dem = 0
    for f in (GOC / "docs/evaluation/geometry").rglob("*.json"):
        ra: list = []
        try:
            _quet(json.loads(f.read_text(encoding="utf-8")), ra)
        except (json.JSONDecodeError, RecursionError):
            continue
        for ct in ra:
            SemanticProgramSpec.model_validate(ct)
            dem += 1
    # Sàn để phép quét không thể "xanh vì không tìm thấy gì". 42 bản ở lượt
    # dựng test; sàn đặt dưới một chút để thêm artifact không làm đỏ oan.
    assert dem >= 40, f"chỉ đọc được {dem} chương trình lịch sử — quét hỏng?"
