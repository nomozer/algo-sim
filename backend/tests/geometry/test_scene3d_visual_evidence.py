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
    # W12: ảnh PHẦN TỬ của bảng lời giải — nhỏ hơn trang, dùng nguyên.
    shots.update({s: str(_anh(tmp / viewport / f"{s}.png", (600, 300), "white")) for s in
                  ("solution_neutral_final", "solution_causal_selected", "solution_expanded")})
    return {"viewport": {"id": viewport, "width": width_css}, "screenshots": shots,
            "canvas_boxes": {s: {"x": 10, "y": 100, "w": 900, "h": 400} for s in shots},
            "formation": {"steps": [
                {"index": k, "learner_text": f"Bước dựng số {k}",
                 "screenshot": str(_anh(tmp / viewport / f"f{k}.png", size, "white"))}
                for k in range(steps)]}}


#: W16: lời từ chối giả lập — vài dòng chữ đen trong hộp lời (`refusal_message_box`, px CSS).
HOP_LOI = {"x": 50, "y": 400, "w": 300, "h": 200}


def _tu_choi(images: Path, family_dir: str, kind: str, vp: str, *, trang: bool = False,
             loai_tren_duong: str | None = None) -> dict:
    """Bản ghi âm đúng khuôn bộ chạy W15: `negative[kind][viewport]`, ảnh ở
    `<họ>/negative/<loại>/<viewport>/refusal.png`. `trang`: ảnh chụp trắng (không chữ)."""
    from PIL import Image, ImageDraw
    path = images / family_dir / "negative" / (loai_tren_duong or kind) / vp / "refusal.png"
    path.parent.mkdir(parents=True, exist_ok=True)
    image = Image.new("RGB", (780, 1200), "white")
    if not trang:
        font, _ = B._font(28)
        draw = ImageDraw.Draw(image)
        for k in range(5):
            draw.text((110, 820 + 60 * k), "Đề bài chưa cho độ dài AB, hệ không đoán", fill="black", font=font)
    image.save(path)
    return {"viewport": {"id": vp, "width": 390}, "pass": True, "screenshot": str(path),
            "refusal_message_box": dict(HOP_LOI),
            "observed": {"canvas": False, "unsupported": {"learner_reason": "Đề bài chưa cho độ dài AB."}}}


def _kich_ban_du(tmp: Path, family_dir: str = "triangular-pyramid", steps: int = 3) -> dict:
    """Kịch bản ĐỦ mọi ô của sheet một họ, đúng khuôn dữ liệu bộ chạy hiện tại (W15)."""
    images = tmp / "images"
    return {"positive": {"desktop": _ban_ghi(tmp, "desktop", 1400, (1400, 800), steps=steps),
                         "mobile": _ban_ghi(tmp, "mobile", 390, (780, 1600), steps=1)},
            "negative": {kind: {vp: _tu_choi(images, family_dir, kind, vp) for vp in ("desktop", "mobile")}
                         for kind in ("ungrounded_source", "assumption", "topology_kernel")}}


def test_w12_family_sheet_keeps_every_required_state_at_native_resolution(tmp_path):
    """Review W10-H8: phụ lục formation quá nhỏ để đọc. Sheet của MỘT họ giữ
    trung tính, causal, xoay, mobile, BẢNG LỜI GIẢI, lời TỪ CHỐI (W12) và MỌI
    bước dựng ở độ phân giải gốc (không thu nhỏ), có dải chú giải và nhãn lớn.

    W16: fixture âm theo khuôn THẬT của bộ chạy (`negative[kind][viewport]`, W15) — khuôn cũ
    `negative[viewport]` là lý do builder ra ba ô trắng mà test này vẫn xanh."""
    meta = B.family_sheet("triangular_pyramid", _kich_ban_du(tmp_path), tmp_path / "images")
    from PIL import Image
    sheet = Image.open(tmp_path / "images" / "triangular-pyramid" / "SHEET.png")
    assert [c["state"] for c in meta["cells"]] == [
        "desktop/neutral_final", "desktop/causal_selected", "desktop/rotated_neutral", "mobile/neutral_final",
        "desktop/solution_neutral_final", "desktop/solution_causal_selected",
        "mobile/solution_neutral_final", "mobile/solution_expanded",
    ] + [f"negative/{k}/{vp}" for k in ("ungrounded_source", "assumption", "topology_kernel")
         for vp in ("desktop", "mobile")] + [f"desktop/geometry_step/{k}" for k in range(3)]
    # Ô desktop: crop bỏ thanh điều hướng trên cùng, KHÔNG thu nhỏ bề ngang;
    # ảnh phần tử và lời từ chối dùng NGUYÊN khung.
    assert all(c["scale"] == 1.0 for c in meta["cells"])
    panel = next(c for c in meta["cells"] if c["state"] == "desktop/solution_neutral_final")
    assert panel["crop_box_px"] == [0, 0, 600, 300]
    assert sheet.width >= 2 * 1400 and meta["legend"] and meta["label_font_px"] >= 24
    assert "XANH = đang xét" in meta["legend"] and "cam đậm = dữ kiện số" in meta["legend"]
    # Vật đã dựng giữ MÀU KIỂU ở khung trung tính (mặt phẳng tím, thiết diện hổ
    # phách...) — chú giải không được hứa "trung tính" (w12, sheet e115eede),
    # và mỗi dòng phải nằm trọn trong bề ngang sheet (bản cũ bị cắt ở mép phải).
    assert "TRUNG TÍNH = đã dựng" not in meta["legend"] and "thiết diện hổ phách" in meta["legend"]
    phong, _ = B._font(B.LABEL_PX - 2)
    assert all(16 + phong.getlength(dong) <= sheet.width for dong in meta["legend"].split("\n"))
    buoc = [c for c in meta["cells"] if c["state"].startswith("desktop/geometry_step/")]
    assert buoc[0]["label"].startswith("Bước dựng 1/3")
    assert buoc[0]["label"].endswith("Bước dựng số 0")


# ── W16 · §14.5 — ô từ chối: đúng loại × viewport, đọc được; thiếu ảnh ⇒ THẤT BẠI ──────

def test_w16_moi_loai_tu_choi_moi_viewport_mot_o_dung_nguon_dung_chu_thich(tmp_path):
    meta = B.family_sheet("triangular_pyramid", _kich_ban_du(tmp_path), tmp_path / "images")
    am = [c for c in meta["cells"] if c["state"].startswith("negative/")]
    assert len(am) == 6
    for c in am:
        _n, kind, vp = c["state"].split("/")
        assert c["source"].endswith(f"triangular-pyramid/negative/{kind}/{vp}/refusal.png"), c
        assert c["crop_box_px"] is not None
        assert c["label"].startswith(vp.capitalize()) and B.TEN_TU_CHOI[kind] in c["label"], c["label"]
    nhan = {c["label"].split(" · ", 1)[1] for c in am}
    assert len(nhan) == 3, nhan                                  # ba loại, ba chú thích khác nhau
    assert not any(k in c["label"] for c in am for k in ("ungrounded_source", "topology_kernel", "_"))


def test_w16_thieu_anh_bat_ky_thi_that_bai_khong_thay_o_trang(tmp_path):
    import pytest
    kb = _kich_ban_du(tmp_path)
    Path(kb["positive"]["mobile"]["screenshots"]["neutral_final"]).unlink()
    Path(kb["negative"]["assumption"]["desktop"]["screenshot"]).unlink()
    with pytest.raises(B.ThieuAnhBangChung) as e:
        B.family_sheet("triangular_pyramid", kb, tmp_path / "images")
    assert "mobile/neutral_final" in str(e.value) and "negative/assumption/desktop" in str(e.value)


def test_w16_thieu_ca_mot_loai_tu_choi_thi_that_bai(tmp_path):
    import pytest
    kb = _kich_ban_du(tmp_path)
    del kb["negative"]["topology_kernel"]
    with pytest.raises(B.ThieuAnhBangChung, match="negative/topology_kernel"):
        B.family_sheet("triangular_pyramid", kb, tmp_path / "images")


def test_w16_anh_tu_choi_trang_khong_doc_duoc_thi_that_bai(tmp_path):
    import pytest
    kb = _kich_ban_du(tmp_path)
    kb["negative"]["ungrounded_source"]["mobile"] = _tu_choi(tmp_path / "images", "triangular-pyramid",
                                                             "ungrounded_source", "mobile", trang=True)
    with pytest.raises(B.ThieuAnhBangChung, match="negative/ungrounded_source/mobile"):
        B.family_sheet("triangular_pyramid", kb, tmp_path / "images")


def test_w16_ban_ghi_tu_choi_tro_sai_loai_hoac_co_canvas_thi_that_bai(tmp_path):
    import pytest
    kb = _kich_ban_du(tmp_path)
    kb["negative"]["assumption"]["mobile"] = _tu_choi(tmp_path / "images", "triangular-pyramid", "assumption",
                                                      "mobile", loai_tren_duong="topology_kernel")
    with pytest.raises(B.ThieuAnhBangChung, match="negative/assumption/mobile"):
        B.family_sheet("triangular_pyramid", kb, tmp_path / "images")
    kb = _kich_ban_du(tmp_path / "b")
    kb["negative"]["assumption"]["desktop"]["observed"]["canvas"] = True
    with pytest.raises(B.ThieuAnhBangChung, match="negative/assumption/desktop"):
        B.family_sheet("triangular_pyramid", kb, tmp_path / "b" / "images")


def test_w16_loai_tu_choi_la_bi_bao_loi(tmp_path):
    import pytest
    kb = _kich_ban_du(tmp_path)
    kb["negative"]["mystery_kind"] = kb["negative"]["assumption"]
    with pytest.raises(KeyError, match="mystery_kind"):
        B.family_sheet("triangular_pyramid", kb, tmp_path / "images")


# ── W17 · §15.5 — ô của các phép đo W17 trên sheet: loại từ chối THÊM (chỉ ở họ khai nó), ca
# phục vụ thêm, ảnh tắt nhãn và ảnh khôi phục nhân quả khi bộ chạy đã ĐO chúng ───────────────

def _them_w17(kb: dict, tmp: Path, family_dir: str = "cross-section") -> dict:
    images = tmp / "images"
    kb["negative"]["construction_mismatch"] = {vp: _tu_choi(images, family_dir, "construction_mismatch", vp)
                                               for vp in ("desktop", "mobile")}
    kb["served"] = {"correct_plane": {vp: {"pass": True, "screenshot": str(_anh(
        images / family_dir / "served" / "correct_plane" / vp / "served.png", (780, 1200), "white"))}
        for vp in ("desktop", "mobile")}}
    for vp, rec in kb["positive"].items():
        rec["annotation_toggle"] = {"pass": True}
        rec["causal_restore"] = {"pass": True}
        for s in ("annotations_off", "causal_restored"):
            rec["screenshots"][s] = str(_anh(tmp / vp / f"{s}.png", (780, 1200), "white"))
    return kb


def test_w17_o_do_W17_co_mat_khi_bo_chay_da_do(tmp_path):
    meta = B.family_sheet("cross_section", _them_w17(_kich_ban_du(tmp_path, "cross-section"), tmp_path),
                          tmp_path / "images")
    trang = [c["state"] for c in meta["cells"]]
    for state in ("desktop/annotations_off", "desktop/causal_restored", "mobile/annotations_off",
                  "mobile/causal_restored", "negative/construction_mismatch/desktop",
                  "negative/construction_mismatch/mobile", "served/correct_plane/desktop",
                  "served/correct_plane/mobile"):
        assert state in trang, (state, trang)
    nhan = {c["state"]: c["label"] for c in meta["cells"]}
    assert B.TEN_TU_CHOI_W17["construction_mismatch"] in nhan["negative/construction_mismatch/mobile"]
    assert B.TEN_PHUC_VU["correct_plane"] in nhan["served/correct_plane/desktop"]
    assert not any("_" in nhan_xem for nhan_xem in nhan.values()), nhan


def test_w17_ho_khong_khai_loai_W17_khong_can_o_ay(tmp_path):
    meta = B.family_sheet("triangular_pyramid", _kich_ban_du(tmp_path), tmp_path / "images")
    assert not any(c["state"].startswith(("served/", "negative/construction_mismatch", "negative/system_cause"))
                   or c["state"].endswith(("annotations_off", "causal_restored")) for c in meta["cells"])


def test_w17_da_do_ma_thieu_anh_thi_that_bai(tmp_path):
    import pytest
    kb = _them_w17(_kich_ban_du(tmp_path, "cross-section"), tmp_path)
    Path(kb["positive"]["mobile"]["screenshots"]["causal_restored"]).unlink()
    Path(kb["served"]["correct_plane"]["desktop"]["screenshot"]).unlink()
    with pytest.raises(B.ThieuAnhBangChung) as e:
        B.family_sheet("cross_section", kb, tmp_path / "images")
    assert "mobile/causal_restored" in str(e.value) and "served/correct_plane/desktop" in str(e.value)
    kb = _them_w17(_kich_ban_du(tmp_path / "b", "cross-section"), tmp_path / "b")
    kb["served"]["mystery"] = kb["served"]["correct_plane"]
    with pytest.raises(KeyError, match="mystery"):
        B.family_sheet("cross_section", kb, tmp_path / "b" / "images")


def test_w16_dai_phim_thieu_anh_buoc_dung_thi_that_bai(tmp_path):
    import pytest
    rec = _ban_ghi_w14(tmp_path)
    Path(rec["formation"]["steps"][2]["screenshot"]).unlink()
    with pytest.raises(B.ThieuAnhBangChung, match="geometry_step/2"):
        B.filmstrip("triangular_pyramid", {"positive": {"desktop": rec}}, tmp_path / "images")


_VAI_W14 = [["DECLARE_ENTITIES"], ["CONSTRUCT_BASE"], ["CONSTRUCT_HEIGHT", "CONSTRUCT_LATERAL_BOUNDARY"],
            ["CONSTRUCT_LATERAL_BOUNDARY"], ["CLOSE_SOLID"]]


def _ban_ghi_w14(tmp: Path) -> dict:
    rec = _ban_ghi(tmp, "desktop", 1400, (1400, 800), steps=len(_VAI_W14))
    for s, vai in zip(rec["formation"]["steps"], _VAI_W14):
        s["formation_roles"] = vai
        s["learner_text"] = ("Dựng chiều cao SA vuông góc với mặt phẳng đáy rồi nối đỉnh S với "
                             "mọi đỉnh của đáy để thấy rõ các cạnh bên trước khi khép khối")
    return rec


def test_w14_filmstrip_names_roles_in_vietnamese_and_every_line_fits(tmp_path):
    """W12-H1/H2 nhìn được bằng mắt: dải phim desktop trái → phải, chú thích là tên
    vai trò TIẾNG VIỆT + lời kể, không token máy, mỗi dòng nằm trọn trong ô của nó."""
    film = B.filmstrip("triangular_pyramid", {"positive": {"desktop": _ban_ghi_w14(tmp_path)}},
                       tmp_path / "images")
    from PIL import Image
    strip = Image.open(film["filmstrip"])
    assert strip.width == len(_VAI_W14) * B.FILM_CELL_W
    assert [c.split(" — ")[0] for c in film["captions"]] == [
        "Bước dựng 1/5 · các điểm dữ kiện", "Bước dựng 2/5 · đáy", "Bước dựng 3/5 · đường cao, cạnh bên",
        "Bước dựng 4/5 · cạnh bên", "Bước dựng 5/5 · khép khối"]
    phong, _ = B._font(film["font_px"])
    for cau, dong in zip(film["captions"], film["caption_lines"]):
        assert not any(t in cau for t in ("CONSTRUCT_", "CLOSE_", "DECLARE_")), cau
        assert " ".join(dong) == cau
        assert len(dong) > 1 and all(12 + phong.getlength(d) <= B.FILM_CELL_W - 12 for d in dong), dong


def test_w14_sheet_step_labels_carry_role_names_and_unknown_roles_are_refused(tmp_path):
    rec = _ban_ghi_w14(tmp_path)
    # W16: sheet đòi ĐỦ mọi ô (thiếu ⇒ thất bại), nên kịch bản mang đủ mobile + ba loại âm.
    kb = _kich_ban_du(tmp_path / "du")
    kb["positive"]["desktop"] = rec
    meta = B.family_sheet("triangular_pyramid", kb, tmp_path / "images")
    nhan = [c["label"] for c in meta["cells"] if c["state"].startswith("desktop/geometry_step/")]
    assert nhan[2].startswith("Bước dựng 3/5 · đường cao, cạnh bên — ")
    assert not any("CONSTRUCT_" in n or "CLOSE_" in n for n in nhan)
    rec["formation"]["steps"][1]["formation_roles"] = ["CONSTRUCT_SPACESHIP"]
    import pytest
    with pytest.raises(KeyError, match="CONSTRUCT_SPACESHIP"):
        B.filmstrip("triangular_pyramid", {"positive": {"desktop": rec}}, tmp_path / "images2")


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
