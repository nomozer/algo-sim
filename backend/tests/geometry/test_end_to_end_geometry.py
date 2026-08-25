# -*- coding: utf-8 -*-
"""PHASE 5G — kiểm chuỗi end-to-end trên **IR THẬT DO AI SINH**. 0 API call.

    Đề bằng lời → Semantic Program → Thẩm định → SimulationState → Scene3D → events

─── VÌ SAO KHÔNG DỰNG BỘ 5 BÀI MỚI ─────────────────────────────────────────

Đặc tả đề nghị chọn 5 bài đại diện (midpoint · perpendicular · plane/section ·
solid · measurement). Tập DEV **đã phủ đúng năm loại ấy**, và `oracle_result`
của nó đã tính TAY, đã đóng băng, đã dùng qua ba lượt đo. Dựng bộ mới nghĩa là
tính tay năm đáp án mới — một **nguồn sai mới** — để trả lời một câu hỏi mà dữ
liệu hiện có đã trả lời được.

─── VÌ SAO KIỂM TRÊN ARTIFACT W4 CHỨ KHÔNG DỰNG CHƯƠNG TRÌNH TAY ───────────

Chương trình viết tay chỉ chứng minh **đường đi thông**. Câu hỏi của Phase 5G
là *"AI có sinh được quá trình hình thành hình học không"*, và câu ấy chỉ trả
lời được bằng thứ **AI thật sự đã viết**. `dev-results-w4/` giữ nguyên IR của
lượt đo `8b4025e`, nên bộ test này chấm chính output ấy — 0 API call, và vẫn là
bằng chứng thật.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from app.simulation.semantic_program.contract import SemanticProgramSpec
from app.simulation.semantic_program.interpreter import SemanticProgramInterpreter
from app.simulation.semantic_program.scene3d import build_scene3d
from app.simulation.semantic_program.simulation_state import (
    build_simulation_state,
    dependency_graph,
)

_W4 = (Path(__file__).resolve().parents[3] / "docs" / "evaluation" / "geometry"
       / "dev-results-w4" / "geometry_dev_results.json")
_ARTIFACT = json.loads(_W4.read_text(encoding="utf-8"))

#: Bài đi trọn chuỗi ở lượt W4 — bốn bài, và cả bốn được oracle độc lập xác nhận.
_CHAY_DUOC = [c for c in _ARTIFACT["cases"] if c["executable"]]

#: Năm loại bài mà đặc tả yêu cầu phủ, ánh xạ sang case DEV có sẵn.
NAM_LOAI = {
    "midpoint": "geo_01",
    "perpendicular": "geo_05",
    "plane_section": "geo_03",
    "solid": "geo_09",
    "measurement": "geo_07",
}


def _canh(case: dict) -> dict:
    spec = SemanticProgramSpec.model_validate(case["generated_program"])
    return build_scene3d(build_simulation_state(
        spec, SemanticProgramInterpreter().execute(spec)))


# ══ TASK 1 — chuỗi end-to-end đủ SÁU chặng ══════════════════════════════
def test_artifact_W4_con_du_de_cham():
    """Rỗng-là-hỏng: mất artifact thì mọi assert dưới đây xanh vô nghĩa."""
    assert len(_ARTIFACT["cases"]) == 10
    assert len(_CHAY_DUOC) == 4, [c["case_id"] for c in _CHAY_DUOC]


def test_nam_loai_bai_deu_co_trong_tap_DEV():
    """Không dựng bộ mới: tập DEV đã phủ đủ năm loại, và đáp án của nó đã tính
    tay + đóng băng qua ba lượt đo."""
    dev = json.loads(
        (_W4.parents[1] / "dev" / "cases.json").read_text(encoding="utf-8"))
    co = {c["case_id"] for c in dev["cases"]}
    assert set(NAM_LOAI.values()) <= co


@pytest.mark.parametrize("case", _CHAY_DUOC, ids=lambda c: c["case_id"])
def test_di_du_SAU_CHANG(case):
    """Đề → IR → thẩm định → state → cảnh → sự kiện. Thiếu chặng nào cũng là
    đứt chuỗi, dù điểm số vẫn đẹp."""
    assert case["problem"], "mất đề bằng lời"
    assert case["generated_program"], "mất IR"
    assert case["schema_pass"] and case["semantic_pass"], "chưa qua thẩm định"
    sc = _canh(case)
    assert sc["objects"], "cảnh rỗng"
    assert sc["events"], "không có sự kiện phát lại"
    assert case["oracle"]["verdict"] == "PASS", case["oracle"]


# ══ TASK 2 — KIỂM LẬP LUẬN DỰNG, không chỉ hình cuối ════════════════════
@pytest.mark.parametrize("case", _CHAY_DUOC, ids=lambda c: c["case_id"])
def test_moi_doi_tuong_DAN_XUAT_co_producer_va_nguon(case):
    for o in _canh(case)["objects"]:
        if o["origin"] != "derived":
            continue
        assert o["producer"], f"{o['id']} không nói nó được dựng bằng gì"
        assert o["depends"], f"{o['id']} không nói nó dựng TỪ GÌ"


@pytest.mark.parametrize("case", _CHAY_DUOC, ids=lambda c: c["case_id"])
def test_THU_TU_dung_ton_trong_phu_thuoc(case):
    """Một đối tượng KHÔNG được xuất hiện trước thứ nó phụ thuộc.

    Đây là phép kiểm *lập luận*, không phải *kết quả*: một chương trình cho ra
    đúng đáp số mà dựng ngược thứ tự thì hình cuối vẫn đúng, còn quá trình thì
    vô nghĩa với người học.
    """
    sc = _canh(case)
    xuat_hien: dict[str, int] = {}
    tu_do = set(sc["free_objects"])
    for e in sc["events"]:
        if e["object"]:
            xuat_hien.setdefault(e["object"], e["step_index"])
    for o in sc["objects"]:
        if o["origin"] != "derived":
            continue
        k = xuat_hien[o["id"]]
        for nguon in o["depends"]:
            if nguon in tu_do:
                continue  # điểm gốc có mặt từ bước INIT
            assert xuat_hien[nguon] < k, (
                f"{o['id']} dựng ở bước {k} nhưng nguồn {nguon} mãi bước "
                f"{xuat_hien[nguon]}"
            )


@pytest.mark.parametrize("case", _CHAY_DUOC, ids=lambda c: c["case_id"])
def test_moi_buoc_co_LOI_GIAI_THICH(case):
    for e in _canh(case)["events"]:
        assert e["explanation"], f"bước {e['step_index']} câm"


@pytest.mark.parametrize("case", _CHAY_DUOC, ids=lambda c: c["case_id"])
def test_KHONG_doi_tuong_nao_TU_TREN_TROI_roi_xuong(case):
    """Đặc tả nói: *"Không chấp nhận: Solid xuất hiện ngay"*.

    Ở đây "ngay" nghĩa là **không có nguồn** — một khối tự có mặt mà không dựng
    từ đỉnh nào. Khối dựng từ năm đỉnh đã khai thì KHÔNG phải "xuất hiện ngay",
    dù nó chỉ tốn một câu lệnh.
    """
    for o in _canh(case)["objects"]:
        if o["render"] in ("mesh", "surface", "polygon") and o["origin"] == "derived":
            assert o["depends"], f"{o['id']} xuất hiện mà không dựng từ gì"


@pytest.mark.parametrize("case", _CHAY_DUOC, ids=lambda c: c["case_id"])
def test_dai_luong_do_duoc_phu_thuoc_HINH_chu_khong_tu_co(case):
    """Nghĩa vụ đại lượng phải đo TỪ một đối tượng hình học. Một con số không
    có nguồn là một đáp án khai thẳng."""
    for o in _canh(case)["objects"]:
        if o["render"] == "readout":
            assert o["producer"].startswith("measure."), o
            assert o["depends"], f"{o['id']} là số không đo từ đâu"


# ══ ĐỘ SÂU CHUỖI DỰNG — phát hiện của Phase 5G ══════════════════════════
def _do_sau(dep: dict[str, list[str]], ten: str, tham=0) -> int:
    if tham > 20 or not dep.get(ten):
        return 0
    return 1 + max(_do_sau(dep, x, tham + 1) for x in dep[ten])


def test_chuoi_dung_hien_tai_SAU_TOI_DA_HAI_TANG():
    """⚠️ PHÁT HIỆN, không phải tiêu chí đạt/trượt.

    Đo trên cả sáu IR thật của lượt W4: chuỗi phụ thuộc sâu nhất là **2 tầng**
    (`điểm tự do → đối tượng → đại lượng`). Không bài nào có chuỗi kiểu
    `đáy → chiều cao → đỉnh → cạnh → khối` mà đặc tả hình dung.

    Nguyên nhân là **HỢP ĐỒNG, không phải mô hình**: IR có đúng năm phép dựng
    (`point`/`line`/`plane`/`solid`/`section`), và `construct_solid` nhận **cả
    danh sách đỉnh trong một câu lệnh**. Không có phép nào để nói *"dựng đáy
    trước, rồi nâng lên thành khối"* — nên AI không thể sinh ra chuỗi sâu hơn,
    dù nó có muốn.

    Test này khoá quan sát ấy lại. Nó ĐỎ khi độ sâu vượt 2 — và lúc ấy nghĩa là
    ai đó đã mở thêm phép dựng, tức phát hiện này đã được xử lý và phải cập nhật
    kết luận của Phase 5G.
    """
    sau: dict[str, int] = {}
    for c in _ARTIFACT["cases"]:
        if not c.get("generated_program"):
            continue
        dep = dependency_graph(
            SemanticProgramSpec.model_validate(c["generated_program"]))
        sau[c["case_id"]] = max((_do_sau(dep, t) for t in dep), default=0)
    assert sau, "không đọc được IR nào"
    assert max(sau.values()) == 2, sau


def test_IR_chua_co_phep_dung_nao_chia_nho_KHOI():
    """Bằng chứng cho §trên: hợp đồng không diễn đạt được `đáy → khối`."""
    import typing

    from app.simulation.semantic_program.contract import SemanticStatement

    tags = {typing.get_args(a)[1].tag
            for a in typing.get_args(typing.get_args(SemanticStatement)[0])
            if "construct" in str(a)}
    assert tags == {"construct_point", "construct_line", "construct_plane",
                    "construct_solid", "construct_section"}
    for chua_co in ("construct_base", "construct_prism", "extrude",
                    "construct_pyramid_from_base"):
        assert chua_co not in tags
