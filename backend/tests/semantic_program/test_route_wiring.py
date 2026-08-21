# -*- coding: utf-8 -*-
"""Route sinh ngữ nghĩa ĐI QUA `run_pipeline` thật (bất biến #22).

VÌ SAO PHẢI CÓ FILE NÀY: trước 2026-08-21 mọi mảnh của route đều có test riêng
và đều xanh, nhưng `stage_semantic_program` KHÔNG CÓ MỘT AI GỌI. Từng mảnh đúng
không cộng lại thành một đường đi đúng — và một benchmark chạy trên chuỗi tự
dựng riêng thì đo một hệ khác với hệ mà luận văn mô tả.

Ba điều được khoá ở đây, không điều nào suy ra được từ điều nào:

1. **SHADOW không đổi đầu ra một bit.** Bật route ở chế độ quan sát mà người học
   nhận được thứ khác đi thì đó không còn là quan sát.
2. **SERVE trả đúng envelope ngữ nghĩa**, và nó chỉ tới lượt khi
   `execution_authority_gate` cho qua.
3. **`executable` tách `servable`.** Đây là chỗ hai tỉ lệ của luận văn tách
   nhau; gộp lại là tự bịa một con số không tồn tại.
"""
from __future__ import annotations

import asyncio
import json

import pytest

from app.ai import pipeline
from app.evaluation.m16_offline_scripts import _analysis
from app.simulation.semantic_program.analyze_contract import build_request_contract
from app.simulation.semantic_program.route import verify_and_compile

from .fixtures_coverage_18 import P02_FIND_MAX, P11_TREE_PREORDER

#: Dãy đúng bằng `initial_value` của `arr` trong P02 — P2 đòi truy được về đề.
DAY_SO = [12, 45, 67, 23, 89, 34]

ANALYZE_PAYLOAD = {
    "input_facts": [
        {"id": "day_so", "kind": "array", "label": "dãy số đề cho",
         "value": [str(v) for v in DAY_SO]},
    ],
    "obligations": [
        {"kind": "extremum", "container": "arr", "witness": "max_val", "cmp": "max"},
    ],
    "prescribed_procedure": None,
}


def _spec_co_provenance():
    """P02 + `source_fact_id`. Fixture gốc có trước P2 nên không mang provenance."""
    spec = P02_FIND_MAX.model_copy(deep=True)
    spec.memory_declarations[0] = spec.memory_declarations[0].model_copy(
        update={"source_fact_id": "day_so"}
    )
    return spec


def _contract():
    return build_request_contract(ANALYZE_PAYLOAD)


def _fake(responses):
    async def f(api_key, system_prompt, user_text, response_schema=None,
                temperature=0.2, image=None):
        assert responses, "gọi nhiều hơn scripted"
        return responses.pop(0)
    return f


def _kich_ban():
    """4 lượt: analyze · classify · semantic_analyze · semantic_program."""
    return [
        json.dumps(_analysis(goal="Tìm số lớn nhất của dãy", ownership="algorithmic")),
        json.dumps({"status": "ok", "simulation_id": "generic.rule_scene",
                    "reason": None}),
        json.dumps(ANALYZE_PAYLOAD),
        _spec_co_provenance().model_dump_json(),
    ]


class _Thu:
    """Observer THỤ ĐỘNG — chỉ thu, không đổi gì (bất biến #22)."""

    def __init__(self):
        self.events: list[tuple[str, dict]] = []

    def emit(self, name, data):
        self.events.append((name, data))

    def dau_tien(self, name):
        for n, kw in self.events:
            if n == name:
                return kw
        return None


def _chay(monkeypatch, *, semantic_route, observer=None):
    monkeypatch.setattr(pipeline, "call_gemini", _fake(_kich_ban()))
    return asyncio.run(pipeline.run_pipeline(
        "Tìm giá trị lớn nhất trong dãy 12 45 67 23 89 34",
        "khoa-gia", observer=observer, semantic_route=semantic_route,
    ))


# ── 1. Tầng tất định, không cần LLM ──────────────────────────────
def test_contract_hop_le_va_chuong_trinh_dung_thi_phat_duoc():
    kq = verify_and_compile(_contract(), _spec_co_provenance())
    assert kq.executable and kq.servable, (
        f"stage={kq.stage_reached} code={kq.error_code} chi_tiet={kq.details}"
    )
    assert kq.stage_reached == "served"
    assert kq.frame_count and kq.frame_count > 1
    # Trạng thái cuối phải đi kèm MỌI phán quyết đã chạy được — nó là thứ duy
    # nhất đem so được với ground truth. Rơi mất nó thì benchmark chấm 0/40 mà
    # vẫn xanh lè, sau khi đã tiêu hết quota.
    assert kq.final_memory and kq.final_memory.get("max_val") == 89


def test_thieu_provenance_thi_P2_chan_truoc_khi_chay():
    """Chương trình chạy được nhưng dữ liệu không truy về đề ⇒ chặn TRƯỚC execute."""
    kq = verify_and_compile(_contract(), P02_FIND_MAX)  # fixture gốc, không có id
    assert not kq.executable and not kq.servable
    assert kq.error_code == "input_not_grounded"
    assert kq.stage_reached == "grounding"


def test_gia_tri_bia_bi_tu_choi_du_dung_dinh_dang():
    """P2 ghim ĐÚNG MỤC NÀO, không phải 'trông giống dữ liệu đề'."""
    payload = json.loads(json.dumps(ANALYZE_PAYLOAD))
    payload["input_facts"][0]["value"] = ["1", "2", "3"]
    kq = verify_and_compile(build_request_contract(payload), _spec_co_provenance())
    assert kq.error_code == "input_not_grounded"
    assert any("89" in d for d in kq.details), kq.details


def test_analyze_tra_chuoi_van_khop_duoc_voi_IR_tra_so():
    """Hồi quy: schema JSON không có kiểu 'số hoặc chuỗi'. Thiếu bậc chuẩn hoá
    thì P2 từ chối 100% chương trình đúng, và từ chối CÂM."""
    c = _contract()
    assert c.input_facts[0].values == tuple(DAY_SO), (
        "giá trị đề cho phải về dạng số, không phải chuỗi"
    )


def test_nghia_vu_khong_co_checker_la_verification_gap_chu_khong_phai_capability():
    """`structural_traversal` chưa có checker server-owned — mức YẾU.

    Phải dùng đề CÂY thật: nghĩa vụ này chỉ hợp với `tree_node`, gắn nó lên một
    mảng thì rơi vào nhánh "kiểu không hợp" và không kiểm được điều đang kiểm.
    """
    spec = P11_TREE_PREORDER.model_copy(deep=True)
    spec.memory_declarations[0] = spec.memory_declarations[0].model_copy(
        update={"source_fact_id": "cay"}
    )
    payload = {
        "input_facts": [
            {"id": "cay", "kind": "tree_node", "label": "cây nhị phân đề cho",
             "value": ["A", "B", "C"]},
        ],
        "obligations": [
            {"kind": "structural_traversal", "container": "tree_root",
             "witness": "order"},
        ],
    }
    kq = verify_and_compile(build_request_contract(payload), spec)
    assert kq.executable is True, (
        "máy chạy xong bài này rồi — khai `executable=False` là báo cáo sai "
        f"năng lực của chính mình (stage={kq.stage_reached}, {kq.details})"
    )
    assert kq.servable is False, "chưa kiểm chứng được thì không phát canonical"
    assert kq.error_code == "semantic_verification_unavailable"
    assert kq.failure_category == "verification_gap"
    assert kq.envelope is not None, "mức yếu vẫn dựng được mô phỏng, chỉ không phát"
    assert kq.final_memory is not None, "đã chạy xong thì phải có trạng thái cuối"


# ── 2. Qua production orchestration ──────────────────────────────
def test_off_giu_nguyen_hanh_vi_cu(monkeypatch):
    """Mặc định phải y hệt trước khi có route — không tốn lượt LLM nào thêm."""
    monkeypatch.setattr(pipeline, "call_gemini", _fake(_kich_ban()[:2]))
    env = asyncio.run(pipeline.run_pipeline(
        "Tìm giá trị lớn nhất trong dãy 12 45 67 23 89 34", "khoa-gia",
    ))
    assert env["status"] == "unsupported"


def test_shadow_khong_doi_dau_ra_mot_bit(monkeypatch):
    thu = _Thu()
    shadow = _chay(monkeypatch, semantic_route="shadow", observer=thu)
    monkeypatch.setattr(pipeline, "call_gemini", _fake(_kich_ban()[:2]))
    off = asyncio.run(pipeline.run_pipeline(
        "Tìm giá trị lớn nhất trong dãy 12 45 67 23 89 34", "khoa-gia",
    ))
    assert shadow == off, "SHADOW đổi đầu ra ⇒ không còn là quan sát"
    # …nhưng bằng chứng thì vẫn phải thu được.
    ghi = thu.dau_tien("semantic_route")
    assert ghi is not None and ghi["servable"] is True, ghi


def test_shadow_VAN_chay_khi_classifier_chon_module_chuyen_biet(monkeypatch):
    """ĐIỂM QUAN TRỌNG NHẤT: route sinh KHÔNG được phụ thuộc classifier legacy.

    Nếu semantic attempt chỉ chạy trong nhánh `generic.rule_scene` thì một
    held-out case bị classifier chọn nhầm một specialized target sẽ khiến route
    sinh không bao giờ được thử. Claim A khi ấy tụt xuống thành "hệ sinh được
    mô phỏng cho những bài mà classifier không nhận" — một claim về CLASSIFIER,
    không phải về route sinh.

    Ở đây classifier chọn `algorithm.find_max` (module chuyên biệt có thật).
    Hai điều phải cùng đúng: semantic vẫn chạy trọn, VÀ người học vẫn nhận
    envelope của module chuyên biệt.
    """
    from app.evaluation.m16_offline_scripts import _algo_cfg

    kich_ban = [
        json.dumps(_analysis(goal="Tìm số lớn nhất của dãy", ownership="algorithmic")),
        json.dumps({"status": "ok", "simulation_id": "algorithm.find_max",
                    "reason": None}),
        json.dumps(ANALYZE_PAYLOAD),
        _spec_co_provenance().model_dump_json(),
    ]
    du_phong = _algo_cfg(DAY_SO)

    async def f(api_key, system_prompt, user_text, response_schema=None,
                temperature=0.2, image=None):
        return kich_ban.pop(0) if kich_ban else du_phong

    monkeypatch.setattr(pipeline, "call_gemini", f)
    thu = _Thu()
    env = asyncio.run(pipeline.run_pipeline(
        "Tìm giá trị lớn nhất trong dãy 12 45 67 23 89 34", "khoa-gia",
        observer=thu, semantic_route="shadow",
    ))

    ghi = thu.dau_tien("semantic_route")
    assert ghi is not None, (
        "route sinh KHÔNG được thử vì classifier chọn module chuyên biệt — "
        "claim A khi ấy đo classifier chứ không đo route sinh"
    )
    assert ghi["servable"] is True, ghi
    # …và module chuyên biệt vẫn là thứ được trả cho người học.
    assert env["status"] == "ok"
    assert env["simulation_id"] == "algorithm.find_max"


def test_serve_KHONG_gianh_cho_cua_module_chuyen_biet(monkeypatch):
    """Ranh giới phạm vi: route sinh phục vụ CHỖ TRỐNG, không thay 24 module."""
    from app.evaluation.m16_offline_scripts import _algo_cfg

    kich_ban = [
        json.dumps(_analysis(goal="Tìm số lớn nhất của dãy", ownership="algorithmic")),
        json.dumps({"status": "ok", "simulation_id": "algorithm.find_max",
                    "reason": None}),
        json.dumps(ANALYZE_PAYLOAD),
        _spec_co_provenance().model_dump_json(),
    ]
    du_phong = _algo_cfg(DAY_SO)

    async def f(api_key, system_prompt, user_text, response_schema=None,
                temperature=0.2, image=None):
        return kich_ban.pop(0) if kich_ban else du_phong

    monkeypatch.setattr(pipeline, "call_gemini", f)
    env = asyncio.run(pipeline.run_pipeline(
        "Tìm giá trị lớn nhất trong dãy 12 45 67 23 89 34", "khoa-gia",
        semantic_route="serve",
    ))
    assert env["simulation_id"] == "algorithm.find_max", (
        "route sinh đã giành chỗ của một module chuyên biệt"
    )


def test_serve_tra_envelope_ngu_nghia(monkeypatch):
    env = _chay(monkeypatch, semantic_route="serve")
    assert env["status"] == "ok"
    assert env["simulation_id"] == "generic.semantic_program"
    assert env["source"] == "semantic_program"
    assert env["config"]["frames"], "envelope không mang chuỗi khung"


def test_authority_gate_van_chan_khi_khong_ai_so_huu_ket_qua(monkeypatch):
    """R0 không bị nới: có interpreter KHÔNG có nghĩa là nhận mọi đề."""
    monkeypatch.setattr(pipeline, "call_gemini", _fake([
        json.dumps(_analysis(goal="Bài không rõ nguồn kết quả", ownership="mo_ho")),
        json.dumps({"status": "ok", "simulation_id": "generic.rule_scene",
                    "reason": None}),
    ]))
    env = asyncio.run(pipeline.run_pipeline(
        "Đề mơ hồ", "khoa-gia", semantic_route="serve",
    ))
    assert env["status"] == "unsupported"


@pytest.mark.parametrize("che_do", ["shadow", "serve"])
def test_route_ton_dung_hai_luot_llm(monkeypatch, che_do):
    """Khoá CHI PHÍ: hơn hai lượt là ngân sách Task 12 sai, và sai âm thầm."""
    dem = {"n": 0}
    goc = _fake(_kich_ban())

    async def dem_goi(*a, **kw):
        dem["n"] += 1
        return await goc(*a, **kw)

    monkeypatch.setattr(pipeline, "call_gemini", dem_goi)
    asyncio.run(pipeline.run_pipeline(
        "Tìm giá trị lớn nhất trong dãy 12 45 67 23 89 34", "khoa-gia",
        semantic_route=che_do,
    ))
    assert dem["n"] == 4, "analyze + classify + semantic_analyze + semantic_program"
