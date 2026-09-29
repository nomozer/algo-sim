"""Crop bằng chứng cạnh khuất (w10): chứa TRỌN hai đầu mút, kèm metadata.

Crop cũ cắt 128 px quanh MỘT điểm chứng — ảnh w09 của cạnh AB không cho thấy
cạnh ấy bắt đầu/kết thúc ở đâu, nên người duyệt không đọc được nét khuất.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "backend" / "scripts"))
import build_scene3d_visual_evidence as B  # noqa: E402

PREIMAGES = (ROOT / "docs/evaluation/geometry/runs/w09-verify-cleanup"
             / "inputs/REGISTERED_CAMERA_PREIMAGES.json")
FIXTURE = (ROOT / "docs/evaluation/geometry/runs/w10-pedagogical-playback"
           / "inputs/fixtures/rectangular_pyramid_positive.json")


def test_crop_box_contains_both_endpoints_with_margin_and_stays_in_the_image():
    box = B.crop_box((100.0, 50.0), (400.0, 300.0), (1422, 804), margin=24, min_size=96)
    assert box[0] <= 100 - 24 and box[1] <= 50 - 24 and box[2] >= 400 + 24 and box[3] >= 300 + 24
    edge = B.crop_box((5.0, 5.0), (30.0, 10.0), (200, 200), margin=24, min_size=96)
    assert edge[0] == 0 and edge[1] == 0 and edge[2] - edge[0] >= 96 and edge[3] - edge[1] >= 96
    assert B.crop_box((150.0, 20.0), (190.0, 30.0), (200, 200), margin=24, min_size=96)[2] == 200


def test_main_sheet_cells_crop_the_stage_not_the_whole_page():
    # Ảnh mobile 780 px cho khung 390 CSS px: tỉ lệ ẢNH là 2 dù renderer khai dpr 1.
    record = {"viewport": {"width": 390},
              "canvas_boxes": {"neutral_final": {"x": 25, "y": 40, "w": 340, "h": 418}},
              "camera_snapshots": {"neutral_final": {"snapshot": {"device_pixel_ratio": 1}}}}
    assert B.image_scale(record, 780) == 2
    assert B.stage_box(record, "neutral_final", (780, 1688)) == (50, 80, 730, 1076)
    # hộp theo trạng thái vắng ⇒ dùng hộp chung; không hộp nào ⇒ không cắt
    assert B.stage_box({"canvas_box": {"x": 0, "y": 0, "w": 10, "h": 10}}, "rotated_neutral", (50, 50)) \
        == (0, 0, 10, 50)
    assert B.stage_box({}, "neutral_final", (50, 50)) is None


def test_oracle_screen_point_maps_to_image_pixels_through_css():
    # renderer dpr 1, ảnh ×2: điểm (100, 50) của canvas ở hộp (25, 195) → (250, 490)
    assert B.to_image_px({"x": 25, "y": 195}, (100.0, 50.0), 1.0, 2.0) == (250.0, 490.0)
    # renderer dpr 2, ảnh ×2: toạ độ oracle đã là điểm ảnh vật lý của canvas
    assert B.to_image_px({"x": 25, "y": 195}, (200.0, 100.0), 2.0, 2.0) == (250.0, 490.0)


def test_edge_records_carry_the_review_metadata():
    scene = json.loads(FIXTURE.read_text(encoding="utf-8"))["envelope"]["scene3d"]
    snapshot = json.loads(next(p["snapshot_json"] for p in json.loads(PREIMAGES.read_text(encoding="utf-8"))
                               ["preimages"] if p["scenario_id"] == "rectangular_pyramid"))
    product = {"visible_edge_ids": [], "hidden_edge_ids": ["khoi_chop::edge:A-B"], "mixed_edge_ids": [],
               "dash_signature": {"khoi_chop::edge:A-B": ["HIDDEN_DASHED"]},
               "duplicate_visual_owner_ids": []}
    oracle = {"visible_edge_ids": [], "hidden_edge_ids": ["khoi_chop::edge:A-B"], "mixed_edge_ids": []}
    [rec] = B.edge_records(scene, snapshot, product, oracle, expected={"khoi_chop::edge:A-B": "HIDDEN"})
    assert rec["machine_edge_id"] == "khoi_chop::edge:A-B"
    assert rec["display_label"] == "AB"
    assert rec["expected_visibility"] == "HIDDEN" and rec["observed_visibility"] == "HIDDEN"
    assert rec["oracle_visibility"] == "HIDDEN" and rec["oracle_agreement"] is True
    assert rec["visual_owner_count"] == 1 and rec["dash_signature"] == ["HIDDEN_DASHED"]
    assert len(rec["endpoints_px"]) == 2


def _anh(path: Path, size: tuple[int, int], color: str) -> Path:
    from PIL import Image
    path.parent.mkdir(parents=True, exist_ok=True)
    Image.new("RGB", size, color).save(path)
    return path


def _ban_ghi(tmp: Path, viewport: str, width_css: int, size: tuple[int, int], steps: int) -> dict:
    shots = {s: str(_anh(tmp / viewport / f"{s}.png", size, c)) for s, c in
             (("neutral_final", "white"), ("causal_selected", "orange"), ("rotated_neutral", "gray"))}
    return {"viewport": {"id": viewport, "width": width_css}, "screenshots": shots,
            "canvas_boxes": {s: {"x": 10, "y": 100, "w": 900, "h": 400} for s in shots},
            "formation": {"steps": [
                {"index": k, "learner_text": f"Bước dựng số {k}",
                 "screenshot": str(_anh(tmp / viewport / f"f{k}.png", size, "white"))}
                for k in range(steps)]}}


def test_w11_family_sheet_keeps_every_required_state_at_native_resolution(tmp_path):
    """Review W10-H8: phụ lục formation quá nhỏ để đọc. Sheet của MỘT họ giữ
    trung tính, causal, xoay, mobile và MỌI bước formation ở độ phân giải gốc
    (không thu nhỏ), có dải chú giải và nhãn chữ lớn cho từng ô."""
    desktop = _ban_ghi(tmp_path, "desktop", 1400, (1400, 800), steps=5)
    mobile = _ban_ghi(tmp_path, "mobile", 390, (780, 1600), steps=1)
    meta = B.family_sheet("triangular_pyramid", {"desktop": desktop, "mobile": mobile},
                          tmp_path / "images")
    from PIL import Image
    sheet = Image.open(tmp_path / "images" / "triangular-pyramid" / "SHEET.png")
    assert [c["state"] for c in meta["cells"]][:4] == [
        "desktop/neutral_final", "desktop/causal_selected", "desktop/rotated_neutral", "mobile/neutral_final"]
    assert [c["state"] for c in meta["cells"]][4:] == [f"desktop/formation/{k}" for k in range(5)]
    # Ô desktop: crop bỏ thanh điều hướng trên cùng, KHÔNG thu nhỏ bề ngang.
    assert all(c["scale"] == 1.0 for c in meta["cells"])
    assert sheet.width >= 2 * 1400 and meta["legend"] and meta["label_font_px"] >= 24
    assert meta["cells"][4]["label"].endswith("Bước dựng số 0")


def test_w11_overview_is_only_an_index_of_the_six_families(tmp_path):
    meta = {f: {"sheet": f"images/{B.family_dir(f)}/SHEET.png", "thumbnail": None}
            for f in ("triangular_pyramid", "triangular_prism", "rectangular_pyramid",
                      "cuboid", "cube", "cross_section")}
    index = B.overview_index(meta, tmp_path / "images")
    assert (tmp_path / "images" / "overview" / "INDEX.png").exists()
    assert [r["family_dir"] for r in index["families"]] == [
        "triangular-pyramid", "triangular-prism", "rectangular-pyramid", "cuboid", "cube", "cross-section"]
    assert index["role"] == "INDEX_ONLY"


def test_oracle_disagreement_is_recorded_not_hidden():
    scene = json.loads(FIXTURE.read_text(encoding="utf-8"))["envelope"]["scene3d"]
    snapshot = json.loads(json.loads(PREIMAGES.read_text(encoding="utf-8"))["preimages"][0]["snapshot_json"])
    product = {"visible_edge_ids": ["khoi_chop::edge:A-B"], "hidden_edge_ids": [], "mixed_edge_ids": [],
               "dash_signature": {}, "duplicate_visual_owner_ids": ["khoi_chop::edge:A-B"]}
    oracle = {"visible_edge_ids": [], "hidden_edge_ids": ["khoi_chop::edge:A-B"], "mixed_edge_ids": []}
    [rec] = B.edge_records(scene, snapshot, product, oracle, expected={})
    assert rec["oracle_agreement"] is False
    assert rec["visual_owner_count"] == ">=2"
    assert rec["expected_visibility"] is None
