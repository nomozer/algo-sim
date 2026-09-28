"""Bề mặt HỌC SINH của cảnh 3D trên sáu family đo (w10).

Envelope dựng thật bằng `generate_generic_tier_a_fixtures.py` (0 lượt gọi
model). Test ánh xạ family → kỳ vọng; mã sản phẩm KHÔNG được rẽ nhánh theo
family: tên khối phải suy từ topology, kết quả cuối từ cấu trúc chương trình.
"""
from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
GENERATOR = ROOT / "backend" / "scripts" / "generate_generic_tier_a_fixtures.py"
FAMILIES = ["triangular_pyramid", "triangular_prism", "rectangular_pyramid",
            "cuboid", "cube", "cross_section"]
SOLID_NOUN = {
    "triangular_pyramid": ("Hình chóp", "Khối chóp"),
    "rectangular_pyramid": ("Hình chóp", "Khối chóp"),
    "cross_section": ("Hình chóp", "Khối chóp"),
    "triangular_prism": ("Lăng trụ",),
    "cuboid": ("Hình hộp chữ nhật",),
    "cube": ("Hình lập phương",),
}
GENERIC = ("Đại lượng đo", "Khối đa diện dựng từ", "Tiếp tục lời giải hình học",
           "Ghi nhận giá trị vừa tính được", "Khởi tạo các điểm theo cấu trúc",
           "nạp trạng thái ban đầu của bộ nhớ", "bố trí tất định")
RAW_POINT = re.compile(r"\(\s*-?\d+(?:/\d+)?\s*,\s*-?\d+(?:/\d+)?\s*,\s*-?\d+(?:/\d+)?\s*\)")
LEARNER_FIELDS = ("label", "notation", "reference", "role", "display_label")


@pytest.fixture(scope="module")
def scenes(tmp_path_factory) -> dict[str, dict]:
    out = tmp_path_factory.mktemp("fixtures")
    subprocess.run([sys.executable, str(GENERATOR), "--out", str(out)], cwd=ROOT,
                   check=True, capture_output=True, text=True)
    return {family: json.loads((out / "fixtures" / f"{family}_positive.json")
                               .read_text(encoding="utf-8"))["envelope"]["scene3d"]
            for family in FAMILIES}


def _learner_strings(scene: dict) -> list[str]:
    strings = [str(o.get(f)) for o in scene["objects"] if o.get("render") != "non_visual"
               for f in LEARNER_FIELDS if o.get(f)]
    strings += [str(o["formula"]["text"]) for o in scene["objects"] if o.get("formula")]
    strings += [e.get("learner_text") or "" for e in scene["events"]]
    return strings


@pytest.mark.parametrize("family", FAMILIES)
def test_no_machine_or_generic_text_on_the_learner_surface(scenes, family):
    leaks = [s for s in _learner_strings(scenes[family])
             if "_" in s or any(g in s for g in GENERIC) or RAW_POINT.search(s)]
    assert not leaks, leaks


@pytest.mark.parametrize("family", FAMILIES)
def test_solid_is_named_by_its_kind(scenes, family):
    solids = [o for o in scenes[family]["objects"] if o["type"] == "solid"]
    assert solids
    for solid in solids:
        assert solid["label"].startswith(SOLID_NOUN[family]), solid["label"]
        assert solid["role"] and not solid["role"].startswith("Khối đa diện dựng từ")


@pytest.mark.parametrize("family", FAMILIES)
def test_final_answer_is_shown_once(scenes, family):
    scene = scenes[family]
    last = scene["formation"]["steps"][-1]
    by_id = {o["id"]: o for o in scene["objects"]}
    shown = [by_id[i] for i in last["readout_ids"] if by_id[i].get("render") == "readout"]
    finals = [e for e in scene["events"] if e["semantic_kind"] == "FINAL_RESULT"]
    assert finals, "no conclusion step"
    assert finals[-1]["step_index"] == scene["events"][-1]["step_index"]
    for event in finals:
        assert by_id[event["object"]].get("render") == "readout"
        # The answer and every alias of it: ONE row (not `V(khối) = n` + `V = n`).
        rows = [o["label"] for o in shown
                if event["object"] in (o["id"], o.get("alias_of"))]
        assert len(rows) == 1, rows
    assert not any(e["learner_text"].startswith("Ghi nhận") for e in scene["events"])


@pytest.mark.parametrize("family", FAMILIES)
def test_segment_on_a_solid_edge_points_to_the_canonical_owner(scenes, family):
    """Một cạnh, MỘT nét: đoạn thẳng trùng cạnh khối (theo TÊN đầu mút) trỏ về
    cạnh chuẩn của khối, để renderer không vẽ hai nét chồng lên nhau (w09: SA
    hiện nét đứt xanh của đoạn thẳng đè lên cạnh S-A của khối)."""
    scene = scenes[family]
    owners = {frozenset(e["endpoint_ids"]): e["edge_id"]
              for o in scene["objects"] if o["type"] == "solid"
              for e in o.get("edge_ownership", [])}
    segments = [o for o in scene["objects"] if o["type"] == "segment3"]
    on_edge = [o for o in segments if frozenset(o.get("endpoint_ids") or ()) in owners]
    for seg in on_edge:
        assert seg.get("boundary_edge_ids") == [owners[frozenset(seg["endpoint_ids"])]], seg["id"]
    for seg in segments:
        if seg not in on_edge:
            assert not seg.get("boundary_edge_ids"), seg["id"]


def test_section_completion_is_a_construction_and_named_from_the_scene(scenes):
    scene = scenes["cross_section"]
    section = next(o for o in scene["objects"] if o["type"] == "section")
    assert "(T)" not in section["label"]
    done = [e for e in scene["events"] if e["object"] == section["id"] and e["action"] != "EXTEND"]
    assert done and all(e["semantic_kind"] == "GEOMETRY_CONSTRUCTION" for e in done)
    steps = scene["formation"]["steps"]
    at = done[0]["step_index"]
    progress = next(p for p in steps[at]["geometry_progress"] if p["object_id"] == section["id"])
    assert progress["closed"] is True and progress["fill_visible"] is True
    # Bước khép lại phải ĐỔI được thứ học sinh thấy: nối cạnh cuối là viền kín,
    # còn mặt thiết diện chỉ tô ở bước khép (w10: bước ấy từng trùng hình bước trước).
    before = next(p for p in steps[at - 1]["geometry_progress"] if p["object_id"] == section["id"])
    assert before["fill_visible"] is False
