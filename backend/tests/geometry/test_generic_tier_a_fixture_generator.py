from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
GENERATOR = ROOT / "backend" / "scripts" / "generate_generic_tier_a_fixtures.py"


def _sha256(path: Path) -> str:
    # Blob content: recorded hashes are LF; a core.autocrlf checkout writes CRLF.
    return hashlib.sha256(path.read_bytes().replace(b"\r\n", b"\n")).hexdigest()


def test_cross_section_fixture_preserves_verifiable_measurement_provenance(tmp_path: Path):
    subprocess.run(
        [sys.executable, str(GENERATOR), "--out", str(tmp_path)],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    fixture = json.loads(
        (tmp_path / "fixtures" / "cross_section_positive.json").read_text(encoding="utf-8")
    )

    source_path = ROOT / fixture["source_artifact_path"]
    canonical_path = ROOT / fixture["canonical_fixture_path"]
    assert source_path.is_file()
    assert fixture["source_sha256"] == _sha256(source_path)
    assert canonical_path.is_file()
    assert fixture["canonical_fixture_sha256"] == _sha256(canonical_path)
    assert fixture["application_llm_calls"] == 0

    manifest = json.loads((tmp_path / "FIXTURE_MANIFEST.json").read_text(encoding="utf-8"))
    # W12: + one `_ungrounded` negative per family (a GIVEN the text does not state).
    # W15: + one `_assumption` negative per family (the text loses a dimension the program
    # keeps by layout) — three refusal kinds per family in the browser suite.
    # W17: + `cube_system_cause` (valid text, injected contract — refusal cause CONSTRUCTION), and the
    # §15.1 pair on one two-plane text: `cross_section_wrong_plane` (refused) / `_correct_plane` (served).
    # W18 (§16): + five point-construction cases on the gold p1 text — three refused at
    # `construction_binding` (midpoint and projection mismatch, unverified), two served (witness).
    # regular-square-pyramid-w01: + five regular-square-pyramid cases (served S1; refused at assumption,
    # grounding, construction_binding, and by the kernel for a zero base edge).
    assert len(manifest["fixtures"]) == 37
    assert {"w18_midpoint_mismatch.json", "w18_projection_mismatch.json", "w18_unverified.json",
            "w18_midpoint_plane_distance.json", "w18_projection_line.json"} <= set(manifest["fixtures"])
    system = json.loads((tmp_path / "fixtures" / "cube_system_cause.json").read_text(encoding="utf-8"))
    assert "cạnh bằng 4" in system["problem_text"] and system["envelope"]["refusal_cause"] == "CONSTRUCTION"
    sai = json.loads((tmp_path / "fixtures" / "cross_section_wrong_plane.json").read_text(encoding="utf-8"))
    dung = json.loads((tmp_path / "fixtures" / "cross_section_correct_plane.json").read_text(encoding="utf-8"))
    assert sai["problem_text"] == dung["problem_text"] and "(β) cắt khối chóp" in sai["problem_text"]
    assert (sai["envelope"]["reason_code"], dung["envelope"]["status"]) == ("CONSTRUCTION_NOT_TEXT_BOUND", "ok")
    assert {
        name.removesuffix("_non_positive.json").removesuffix("_positive.json").removesuffix("_negative.json")
        .removesuffix("_ungrounded.json").removesuffix("_assumption.json").removesuffix("_system_cause.json")
        .removesuffix("_wrong_plane.json").removesuffix("_correct_plane.json")
        .removesuffix("_wrong_centre.json")
        for name in manifest["fixtures"] if not name.startswith("w18_")  # wave cases, not a family
    } == {
        "triangular_pyramid", "triangular_prism", "rectangular_pyramid",
        "cuboid", "cube", "cross_section", "regular_square_pyramid",
    }
    for name in [n for n in manifest["fixtures"] if n.endswith("_ungrounded.json")]:
        negative = json.loads((tmp_path / "fixtures" / name).read_text(encoding="utf-8"))
        envelope = negative["envelope"]
        assert envelope["status"] == "unsupported", name
        assert envelope["reason_code"] == "GIVEN_VALUE_NOT_IN_SOURCE", name
        assert "scene3d" not in envelope and "final_memory" not in envelope, name
        assert negative["removed_from_text"] not in negative["problem_text"], name
        assert "_" not in envelope["learner_reason"], name
    for name in [n for n in manifest["fixtures"] if n.endswith("_assumption.json")]:
        negative = json.loads((tmp_path / "fixtures" / name).read_text(encoding="utf-8"))
        envelope = negative["envelope"]
        assert (envelope["status"], envelope["stage_reached"]) == ("unsupported", "assumption"), name
        assert envelope["reason_code"] == ("ASSUMPTION_INVARIANCE_UNPROVEN" if name.startswith("cross_section")
                                           else "ASSUMPTION_DETERMINES_ANSWER"), name
        assert "scene3d" not in envelope and "final_memory" not in envelope, name
        assert negative["removed_from_text"] not in negative["problem_text"], name
        assert "_" not in envelope["learner_reason"], name


def test_w17_de_am_do_dai_khong_duong_phai_ghi_so_ay_trong_chinh_de():
    """W17 · ảnh lập phương "cạnh 4" bị từ chối: `_zero_ab` chỉ thay chuỗi "AB = 3", mà đề lập
    phương ghi "cạnh bằng 4" — đề không đổi (V = 64 hợp lệ) trong khi hợp đồng mang AB = 0. Fixture
    âm "độ dài không dương" phải GHI số ≤ 0 trong chính đề, đọc được bằng bộ đọc của server."""
    sys.path.insert(0, str(ROOT / "backend"))
    from app.simulation.semantic_program.segment_relation import do_dai_trong_de
    from app.simulation.semantic_program.shape_constraint import doc_rang_buoc
    from scripts import generate_generic_tier_a_fixtures as GEN

    for ten, factory in (("triangular_pyramid", GEN._pyramid_control_contract),
                         ("triangular_prism", GEN._prism_p01_contract),
                         ("rectangular_pyramid", GEN._rect_pyramid_contract),
                         ("cuboid", GEN._cuboid_contract), ("cube", GEN._cube_contract)):
        goc = factory()[0]
        text, _contract = GEN._zero_ab(goc, factory()[1])
        assert text != goc, ten
        khong_duong = any(v <= 0 for v in do_dai_trong_de(text).values()) or any(
            r.kind == "cube_edge" and r.value is not None and r.value <= 0 for r in doc_rang_buoc(text))
        assert khong_duong, (ten, text)
