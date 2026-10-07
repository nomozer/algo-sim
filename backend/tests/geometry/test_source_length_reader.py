# -*- coding: utf-8 -*-
"""W14 Track C — MỘT từ vựng từ nối cho độ dài đoạn (`=` · `bằng` · `dài` · `có độ dài`).

W13 NA-57: bộ đọc độ dài (`segment_relation`) và nhãn bằng chứng GIVEN
(`grounding_gate._NHAN_TRUOC`) dùng hai từ vựng khác nhau, nên "AB dài 5 cm" không
gắn đoạn nào ở phía nhãn và con số 5 thành bằng chứng cho MỌI đoạn. Cùng gốc với
"cạnh AB có độ dài 5". `_bang_chung_do_dai` còn riêng tư — test gọi nguyên trạng.
0 lượt gọi model.
"""
from __future__ import annotations

import json
from fractions import Fraction
from pathlib import Path

import pytest

from app.simulation.semantic_program import grounding_gate as G
from app.simulation.semantic_program.segment_relation import do_dai_trong_de

ROOT = Path(__file__).resolve().parents[3]
PROBE_W13 = (ROOT / "docs" / "evaluation" / "geometry" / "runs" / "w13-geometry-preregistration"
             / "diagnostics" / "SOURCE_GROUNDING_PHRASING_PROBE.json")
#: Hai hàng W13 mà W14 ĐĂNG KÝ là sẽ đổi (Task 6 Step 4); mọi hàng khác giữ nguyên.
#: regular-square-pyramid-w05: thêm hai hàng chuỗi bằng nhau — đúng hàng backlog §4 của tiền đăng ký (`AB = AC = 5`:
#: "chuỗi bằng nhau = cùng một giá trị cho mọi đoạn"), `ISSUE-ARCH-SOURCE-LENGTH-CHAINED-EQUALITY`. Hành vi mới khoá ở
#: `test_w05_chuoi_bang_nhau_doi_dang_ky`; artifact W13 không sửa.
DOI_DANG_KY_W05 = {"chain_equal", "chain_equal_first"}
#: regular-triangular-pyramid-w01 (§18.3): độ dài căn của đề là MỘT con số — ba hàng căn nay đọc được độ dài; lỗi và
#: bằng chứng GIVEN không đổi. Hành vi mới khoá ở `test_rtp_do_dai_can_doi_dang_ky`; artifact W13 không sửa.
DOI_DANG_KY_RTP = {"radical", "radical_fraction", "radical_wrong_segment"}
DOI_DANG_KY = {"dai_cm", "standalone_wrong_segment"} | DOI_DANG_KY_W05 | DOI_DANG_KY_RTP
DAI_CM = "Cho hình chóp S.ABC có AB dài 5 cm."
MAU_THUAN = "SOURCE_EVIDENCE_CONFLICT"


def _hang_w13() -> list[dict]:
    rows = json.loads(PROBE_W13.read_text(encoding="utf-8"))["rows"]
    assert len(rows) == 25, len(rows)
    return rows


def _gia_tri(v: str) -> Fraction | str:
    """Giá trị khai của probe: `"5/2"` → Fraction; căn (`"2√3"`) giữ chuỗi như probe."""
    return v if "√" in v else Fraction(v)


def test_dai_cm_sai_doan_bi_tu_choi():
    assert G._bang_chung_do_dai(DAI_CM, "AC_length", Fraction(5), None)[0] == MAU_THUAN


def test_dai_cm_dung_doan_duoc_nhan():
    assert G._bang_chung_do_dai(DAI_CM, "AB_length", Fraction(5), None)[0] is None
    assert do_dai_trong_de(DAI_CM) == {frozenset({"A", "B"}): Fraction(5)}


def test_co_do_dai_sai_doan_bi_tu_choi():
    """Review Focus 5: bộ đọc ① đọc được AB = 5, nhưng nhãn ③ chỉ biết `=`/`bằng`,
    nên con số 5 bị coi là số đứng một mình và thành bằng chứng cho AC."""
    de = "Cho hình chóp S.ABC có cạnh AB có độ dài 5."
    assert G._bang_chung_do_dai(de, "AC_length", Fraction(5), None)[0] == MAU_THUAN


def test_nhan_sai_doan_that_bai_dong():
    de = "Cho hình chóp S.ABC có AB = 5."
    assert G._bang_chung_do_dai(de, "AC_length", Fraction(5), None)[0] == MAU_THUAN


@pytest.mark.parametrize("de", [
    "Cho hình chóp S.ABC có AB dài hơn 5.",
    "Cho hình chóp S.ABC có AB dài gấp 2 lần SC.",
], ids=["dai_hon", "dai_gap"])
def test_so_khong_dung_ngay_sau_tu_noi_thi_khong_doc(de):
    """Không so khớp mờ: giá trị phải đứng NGAY sau từ nối."""
    assert do_dai_trong_de(de) == {}


def test_bang_chung_doan_gan_voi_cap_dau_mut():
    """`bang_chung_doan(de, (X, Y), v)` — bằng chứng gắn ĐÚNG đoạn, không theo tên bộ nhớ."""
    assert G.bang_chung_doan(DAI_CM, ("A", "B"), Fraction(5))
    assert G.bang_chung_doan(DAI_CM, ("B", "A"), Fraction(5))
    assert not G.bang_chung_doan(DAI_CM, ("A", "C"), Fraction(5))
    assert not G.bang_chung_doan("Cho hình chóp S.ABC có AB = 5.", ("A", "C"), Fraction(5))
    assert G.bang_chung_doan("Cho lăng trụ ABC.A′B′C′ có AA′ = 5.", ("A", "A_prime"), Fraction(5))


def test_mau_tru_truc_xien_neu_du_ban_kinh():
    """Q3 (W14): đáp số của bài mẫu offline `tru-truc-xien` dùng bán kính OA = √5 —
    đề phải GHI bán kính ấy (bằng chứng gắn đúng đoạn OA); đáp số không đổi."""
    from app.simulation.semantic_program.contract import SemanticProgramSpec
    from app.simulation.semantic_program.interpreter import SemanticProgramInterpreter
    from scripts import build_geometry_samples as B

    prog = B.chuong_trinh_tru_truc_xien()
    assert G.bang_chung_doan(prog["description"], ("O", "A"), "√5"), prog["description"]
    mem = SemanticProgramInterpreter().execute(SemanticProgramSpec.model_validate(prog)).final_memory
    assert (str(mem["V"]), str(mem["Sxq"])) == ("15π", "6π√5")


@pytest.mark.parametrize("row", [r for r in _hang_w13() if r["id"] not in DOI_DANG_KY],
                         ids=lambda r: r["id"])
def test_cach_viet_cu_khong_doi(row):
    """GUARD: mọi hàng W13 ngoài các hàng đăng ký đổi (`DOI_DANG_KY`) giữ nguyên (độ dài đọc được, lỗi, bằng chứng)."""
    text = row["text"]
    loi, bang_chung, _ly_do = G._bang_chung_do_dai(
        text, row["declared"]["name"], _gia_tri(row["declared"]["value"]), None)
    do_dai = {"-".join(sorted(k)): str(v) for k, v in do_dai_trong_de(text).items()}
    assert (do_dai, loi, bang_chung) == (
        row["do_dai_trong_de"], row["given_evidence_error"], row["given_evidence"])


@pytest.mark.parametrize("row", [r for r in _hang_w13() if r["id"] in DOI_DANG_KY_RTP], ids=lambda r: r["id"])
def test_rtp_do_dai_can_doi_dang_ky(row):
    """§18.3: `AB = 2√3` gắn AB ↦ 2√3 (W13: không đọc); lỗi + bằng chứng GIVEN như probe W13."""
    text = row["text"]
    loi, bang_chung, _ly_do = G._bang_chung_do_dai(
        text, row["declared"]["name"], _gia_tri(row["declared"]["value"]), None)
    do_dai = {"-".join(sorted(k)): str(v) for k, v in do_dai_trong_de(text).items()}
    assert do_dai == {"A-B": text.split("AB = ")[1].rstrip(".")}
    assert (loi, bang_chung) == (row["given_evidence_error"], row["given_evidence"])


@pytest.mark.parametrize("row", [r for r in _hang_w13() if r["id"] in DOI_DANG_KY_W05], ids=lambda r: r["id"])
def test_w05_chuoi_bang_nhau_doi_dang_ky(row):
    """`AB = AC = 5`: CẢ HAI đoạn đọc được độ dài 5; khai AB = 5 hay AC = 5 đều có bằng chứng ở chính con số 5."""
    text = row["text"]
    loi, bang_chung, _ly_do = G._bang_chung_do_dai(
        text, row["declared"]["name"], _gia_tri(row["declared"]["value"]), None)
    do_dai = {"-".join(sorted(k)): str(v) for k, v in do_dai_trong_de(text).items()}
    assert do_dai == {"A-B": "5", "A-C": "5"}
    assert loi is None
    assert bang_chung["span_text"] == "5" and text[slice(*bang_chung["span"])] == "5"
