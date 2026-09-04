# -*- coding: utf-8 -*-
"""ĐỒ THỊ PHỤ THUỘC CỦA VẬT DẪN XUẤT. **0 lượt gọi model.**

    `GEOMETRIC_DEPENDENCY_VISIBILITY_BRIDGE`, 2026-09-04.

`dependency_graph` lọc cạnh qua `memory_declarations` — bảng trả lời *"chương
trình KHAI những gì"*, trong khi câu cần hỏi là *"chương trình CÓ những vật
nào"*. `construct_*` ghi thẳng `memory[target_var]` mà không đòi khai báo, nên
**mọi cạnh trỏ tới một vật dẫn xuất đều bị lọc mất**.

Đây là consumer THỨ BA của cùng câu hỏi mà `OBLIGATION_BINDING_CONTRACT` đã bịt
cho cổng phủ bằng `bang_ky_hieu`; wave đó bỏ sót nó.

Fixture là artifact THẬT (`probe-contract-waves-2`), không phải chương trình
viết lại cho vừa.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from app.simulation.geometry.radical import display, is_exact_number
from app.simulation.semantic_program import ir_static_check as IRS
from app.simulation.semantic_program.contract import SemanticProgramSpec
from app.simulation.semantic_program.ir_static_check import bang_ky_hieu
from app.simulation.semantic_program.request_contract import RequestContract
from app.simulation.semantic_program.route import verify_and_compile
from app.simulation.semantic_program.simulation_state import dependency_graph

GOC = Path(__file__).resolve().parents[3]
CA_CONG = GOC / "docs/evaluation/geometry/probe-contract-waves-2/cases/circumsphere/final.json"
CA_TRU = GOC / "docs/evaluation/geometry/probe-contract-waves/cases/cylinder_2/final.json"


def _nap(duong: Path):
    d = json.loads(duong.read_text(encoding="utf-8"))
    return (RequestContract.model_validate(d["request_contract"]),
            SemanticProgramSpec.model_validate(d["chuong_trinh"]), d)


@pytest.fixture
def cau():
    """Chương trình `circumsphere` mô hình đã viết, nguyên văn."""
    return _nap(CA_CONG)


@pytest.fixture
def canh(cau):
    from app.ai.pipeline import _dung_scene3d

    ct, spec, _ = cau
    return _dung_scene3d(spec, ct)


# ══ A · ĐÚNG NHỮNG CẠNH ĐÃ MẤT ════════════════════════════════════════════
#: Đo được trước bản vá — bốn cạnh này biến mất, và cả bốn đều trỏ tới một vật
#: DẪN XUẤT. Vật chỉ phụ thuộc điểm tự do thì không hề hấn gì, nên lỗi trông
#: như "chỉ vài chỗ" trong khi nó cắt đúng xương sống của chuỗi dựng.
CANH_DA_MAT = {
    "D": {"A_prime", "vec_OC"},
    "M": {"D", "O"},
    "circumsphere": {"M", "O"},
    "R": {"circumsphere"},
}


@pytest.mark.parametrize("ten,mong", sorted(CANH_DA_MAT.items()))
def test_A_canh_dan_xuat_da_tro_lai(cau, ten, mong):
    _, spec, _ = cau
    assert set(dependency_graph(spec).get(ten, [])) == mong


def test_A2_khong_cong_them_canh_nao_ngoai_phu_thuoc_tho(cau):
    """Bản vá NỚI tập lọc, không đổi thuật toán thu thập cạnh.

    Đồ thị sau lọc phải là tập con của đồ thị thô `_phu_thuoc` — nếu lớn hơn
    thì cạnh đến từ chỗ khác, và hàm này đã lặng lẽ thành nguồn sự thật thứ hai.
    """
    from app.simulation.semantic_program.coverage_gate import _phu_thuoc

    _, spec, _ = cau
    tho = _phu_thuoc(spec.statements, frozenset())
    for ten, nguon in dependency_graph(spec).items():
        assert set(nguon) <= set(tho.get(ten, ())), ten


# ══ B · BẤT BIẾN TOÀN CỤC ═════════════════════════════════════════════════
def test_B1_moi_canh_deu_la_TEN_CO_THAT(cau):
    """Bất biến "không tên ma" GIỮ NGUYÊN — chỉ đổi tập dùng để kiểm nó."""
    _, spec, _ = cau
    co_that = set(bang_ky_hieu(spec))
    for ten, nguon in dependency_graph(spec).items():
        assert set(nguon) <= co_that, f"{ten} trỏ ra ngoài chương trình"


def test_B2_scene_object_depends_khong_thieu_canh_cua_su_kien(canh):
    """HỢP ĐỒNG HAI TRƯỜNG — hai miền KHÁC nhau, nên kiểm sau phép chiếu.

    `event.depends`  ← `_provenance.sources`: toán hạng TRỰC TIẾP của câu lệnh.
    `object.depends` ← `_phu_thuoc`: toán hạng **cộng** phụ thuộc ĐIỀU KHIỂN
                       (điều kiện `if`/`while` bao quanh) và cạnh BÍ DANH.

    Nên quan hệ đúng là **bao hàm**, không phải bằng nhau:
        event.depends ⊆ object.depends
    Đo trên toàn corpus lịch sử: 169 cặp, **0 vi phạm**; bằng nhau ở 157 cặp.
    12 cặp còn lại đều là vật BÍ DANH (`producer is None`) — tên hợp đồng được
    hoà giải lên một vật chương trình, không có câu lệnh sinh nên sự kiện của
    nó không mang toán hạng nào.
    """
    ev = {e["object"]: set(e.get("depends") or [])
          for e in canh["events"] if e.get("object")}
    for o in canh["objects"]:
        if o["id"] not in ev:
            continue  # vật tự do: không có sự kiện sinh
        assert ev[o["id"]] <= set(o.get("depends") or []), o["id"]


def test_B3_vat_co_PRODUCER_thi_hai_truong_khop_chinh_xac(canh):
    """Phép chiếu ở B2 hẹp lại đúng chỗ nó phải hẹp: vật do một câu lệnh sinh
    ra thì hai trường nói **cùng một điều**. Chỉ vật bí danh mới được lệch."""
    ev = {e["object"]: sorted(e.get("depends") or [])
          for e in canh["events"] if e.get("object")}
    for o in canh["objects"]:
        if o["id"] in ev and o.get("producer"):
            assert sorted(o.get("depends") or []) == ev[o["id"]], o["id"]


def test_B4_timeline_va_khung_khong_doi(cau):
    """13 bước, 13 khung, đúng thứ tự — wave này không được chạm timeline."""
    ct, spec, _ = cau
    oc = verify_and_compile(ct, spec)
    cfg = (oc.envelope or {})["config"]
    assert oc.total_steps == 13
    assert len(cfg["frames"]) == 13 == len(cfg["view_steps"])
    assert cfg["execution_truncated"] is False
    assert cfg["presentation_overflow"] is False


def test_B5_ket_qua_toan_hoc_va_kiem_chung_khong_doi(cau):
    ct, spec, _ = cau
    oc = verify_and_compile(ct, spec)
    assert oc.servable and oc.stage_reached == "served"
    dl = {k: display(v) for k, v in (oc.final_memory or {}).items()
          if is_exact_number(v)}
    assert dl["R"] == "√3"
    assert oc.constraints_verified == ["radius(OABC)"]
    assert oc.resolved_names == {"OABC": "circumsphere"}


def test_B6_su_kien_dung_thu_tu_va_khong_vat_nao_hien_truoc_producer(canh):
    """Vật xuất hiện đúng tại bước sinh ra nó, không sớm hơn."""
    idx = [e["step_index"] for e in canh["events"]]
    assert idx == sorted(idx) == list(range(13))
    sinh = {e["object"]: e["step_index"] for e in canh["events"] if e.get("object")}
    for e in canh["events"]:
        for p in e.get("depends") or []:
            if p in sinh:
                assert sinh[p] < e["step_index"], f"{p} sinh sau khi bị dùng"


# ══ C · KHÔNG NỚI THỨ KHÁC ════════════════════════════════════════════════
def test_C1_cylinder_2_van_KIEU_KHONG_HOP():
    from app.simulation.semantic_program.coverage_gate import (
        KIEU_KHONG_HOP, check_structural_coverage)

    ct, spec, _ = _nap(CA_TRU)
    kq = check_structural_coverage(ct, spec)
    assert not kq.ok
    assert [c.ly_do for c in kq.chan_doan] == [KIEU_KHONG_HOP]


def test_C2_R0_grounding_van_tu_choi_dung_luot_no_da_tu_choi(cau):
    """Lượt sửa THẬT của chính ca này chết ở grounding — phải tiếp tục chết.

    Dùng ứng viên thô đã ghi trong artifact chứ không dựng một chương trình
    hỏng cho vừa: bản dựng tay đầu tiên của test này bỏ `source_fact_id` của
    `O` và **vẫn xanh**, vì `(0,0,0)` là HẠT KHỞI TẠO được miễn. Tiền đề sai
    thì test canh nhầm chỗ.
    """
    ct, _, d = cau
    luot = [t for t in d["theo_luot"] if t.get("gate") == "grounding"]
    assert luot, "artifact phải còn giữ lượt bị grounding từ chối"
    hong = SemanticProgramSpec.model_validate_json(luot[0]["raw"])
    oc = verify_and_compile(ct, hong)
    assert not oc.servable
    assert oc.stage_reached == "grounding"
    assert oc.error_code == "input_not_grounded"


# ══ D · TIÊM LỖI — guard chưa từng đỏ là guard chưa được chứng minh ═══════
def test_D_khoi_phuc_bo_loc_CU_thi_canh_dan_xuat_bien_mat(cau, monkeypatch):
    """Dựng lại đúng bản trước bản vá: lọc bằng `memory_declarations`.

    Nếu bốn cạnh KHÔNG biến mất thì bài test ở nhóm A đang xanh vì lý do khác,
    và nó không còn canh được thứ nó sinh ra để canh.
    """
    _, spec, _ = cau
    monkeypatch.setattr(
        IRS, "bang_ky_hieu",
        lambda s: {d.name: d.type for d in (s.memory_declarations or ())})

    dep = dependency_graph(spec)
    assert dep["D"] == ["vec_OC"]          # mất A_prime
    assert dep["M"] == ["O"]               # mất D
    assert dep["circumsphere"] == ["O"]    # mất M
    assert dep["R"] == []                  # mất circumsphere — bấm vào đáp số
    for ten, mong in CANH_DA_MAT.items():  # và đúng bốn cạnh ấy sai
        assert set(dep.get(ten, [])) != mong
