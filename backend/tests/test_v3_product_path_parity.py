# -*- coding: utf-8 -*-
"""V3_PRODUCT_PATH_PARITY — runner V3 chấm ở SAI TẦNG. **0 lượt gọi model.**

    `docs/V3_PRODUCT_PATH_PARITY_CORRECTION.md`, 2026-09-05.

Runner V3 đọc đại lượng từ `outcome.envelope["scene3d"]` sau khi gọi
`verify_and_compile`. Nhưng `route` **cố ý** không dựng `scene3d` — hướng phụ
thuộc một chiều, và `test_scene3d.py` cấm mọi module dưới `app/simulation`
import nó. Người dựng cảnh là `pipeline._dung_scene3d`, chạy SAU route.

Hệ quả: phép chiếu ấy trả **rỗng cho mọi ca**, nên `dap_so_khop` không bao giờ
True được — kể cả với một chương trình đúng hoàn toàn. Đúng một ca của V3 chạy
tới được tầng ấy (`c7a`), và nó bị chấm sai vì lý do này.

Thẩm quyền đúng cho ĐÁP SỐ là `acceptance_verdict.trich_ket_qua` →
`outcome.final_memory`. Nó đã có sẵn trong scorer; runner chỉ không gọi.
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

import pytest

GOC = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(GOC / "scripts"))

REPO = GOC.parent
OUT = REPO / "docs" / "evaluation" / "geometry" / "curved-acceptance-v3"
CV3 = REPO / "docs" / "evaluation" / "geometry" / "curved-v3"
DINH_CHINH = CV3 / "V3_PRODUCT_PATH_PARITY_CORRECTION.json"

#: Băm artifact NGUỒN của lượt V3. Chúng là bằng chứng lịch sử và **không được
#: đổi** — bản đính chính là một lớp MỚI đặt cạnh, không phải một bản ghi đè.
#:
#: ⚠️ BẢNG NÀY LÀ **BẢN GHI LỊCH SỬ**, KHÔNG PHẢI PHÉP KIỂM BẤT BIẾN
#: (`V3_THESIS_EVIDENCE_ALIGNMENT_REPAIR`, 2026-09-20).
#:
#: Đây đúng là những con số `V3_PRODUCT_PATH_PARITY_CORRECTION.json` và
#: `docs/CURVED_V3_LIVE_ACCEPTANCE.md` đã công bố 2026-09-05. Chúng **không được
#: sửa** — sửa là viết lại bằng chứng đã xuất bản. `test_02` đối chiếu bảng này
#: với artifact đính chính, và đó là vai trò duy nhất của nó.
#:
#: Nhưng chúng **không dùng để kiểm tính bất biến của nội dung được**: chúng
#: được đo trên BYTE THÔ của một bản checkout cụ thể. Kho đặt
#: `core.autocrlf = true` và không có `.gitattributes`, nên git viết CRLF ra đĩa
#: trong khi blob giữ LF ⇒ byte thô phụ thuộc LƯỢT CHECKOUT, không phụ thuộc
#: nội dung. Đo được: cùng commit `58770bb`, `manifest.json` ở cây nguồn là LF
#: còn ở worktree mới là CRLF — hai giá trị băm khác nhau cho một tệp không hề
#: đổi. Phép kiểm bất biến vì thế nằm ở `BAM_NOI_DUNG` bên dưới.
BAM_NGUON = {
    "attribution.json":
        "280a3fe1290305b5c21deea4c035bf0a423ce280cc975a9c34839df411d85610",
    "curved_acceptance.json":
        "70d47a9542561209ce5f4f0d50184e638866eca27f49f8594eb6b6e4e05a49b5",
    "manifest.json":
        "b2a454f0b285c5f1061798a52dc367efcba5ebb3d0a4f30da6eb0e38776c146a",
    "stage_8a_one_shot.json":
        "f3439fb6db1d568b3ac2723ad52b6a58358bc9786012dffdff4a0fc4122f53bb",
}

#: BĂM NỘI DUNG — của **bản đã commit** (blob, LF). Đây mới là thứ nói được câu
#: *"artifact V3 không đổi một byte"* ở MỌI cây làm việc.
#:
#: Bốn tệp nguồn V3 có ĐÚNG MỘT commit (`85b584c`, 2026-09-05) và chưa bao giờ
#: bị sửa — `test_23` chứng minh lại điều đó thẳng từ `git cat-file`. Nên bảng
#: này không phải một snapshot mới; nó là cùng một bằng chứng, đo đúng cách.
#:
#: `manifest.json` trùng ở cả hai bảng vì khi ghi 2026-09-05 nó tình cờ đang là
#: LF trên đĩa — và chính sự trùng khớp bộ phận ấy làm bộ test xanh ở cây nguồn
#: mà đỏ ở mọi worktree mới, suốt từ 2026-09-05.
#:
#: Cách chuẩn hoá lấy đúng tiền lệ đã có trong kho:
#: `tests/geometry/test_phase7b_baseline_immutable.py::_bam`.
BAM_NOI_DUNG = {
    "attribution.json":
        "7f84686a9d31b7c90f21f8a95bffe718f0d353a5ed10a66f9069d60154faf6ef",
    "curved_acceptance.json":
        "8e6f5924297d24373746bb4bebca3b3d389a69b2beb229a68cda894ccf6e1134",
    "manifest.json":
        "b2a454f0b285c5f1061798a52dc367efcba5ebb3d0a4f30da6eb0e38776c146a",
    "stage_8a_one_shot.json":
        "8166f3d2935079c8e263850007f3600d9031dbc5b03fdeac8de751217a0d265f",
}
CANDIDATE_V3 = ("a696200e8f8c668c82a1675eab09b4e1845e3c499edaf90c95790f108"
                "fe244c2")


def _bam(p: Path) -> str:
    """Băm NỘI DUNG, chuẩn hoá xuống dòng trước — xem ghi chú ở `BAM_NGUON`.

    Cùng công thức với `tests/geometry/test_phase7b_baseline_immutable.py::_bam`;
    một cách chuẩn hoá cho mọi phép kiểm bất biến của bằng chứng, không hai.
    """
    return hashlib.sha256(p.read_bytes().replace(b"\r\n", b"\n")).hexdigest()


@pytest.fixture(scope="module")
def dc():
    assert DINH_CHINH.exists(), "chưa sinh artifact đính chính"
    return json.loads(DINH_CHINH.read_text(encoding="utf-8"))


# ══ ① ARTIFACT NGUỒN GIỮ NGUYÊN ═══════════════════════════════════════════
@pytest.mark.parametrize("ten,bam", sorted(BAM_NOI_DUNG.items()))
def test_01_artifact_V3_goc_KHONG_doi_mot_byte(ten, bam):
    assert _bam(OUT / ten) == bam, (
        f"{ten} đã đổi — artifact V3 là bằng chứng lịch sử của một candidate "
        f"không còn tồn tại; đính chính phải là một LỚP MỚI đặt cạnh")


def test_02_dinh_chinh_ghi_dung_bam_nguon(dc):
    for ten, bam in BAM_NGUON.items():
        assert dc["source_artifact_hashes"][ten] == bam, ten


# ══ ② REPLAY DÙNG ĐÚNG CANDIDATE CŨ ═══════════════════════════════════════
def test_03_replay_chay_tren_candidate_V3_CU(dc):
    assert dc["replay_measured_system_hash"] == CANDIDATE_V3
    assert dc["old_candidate_hash"] == CANDIDATE_V3
    assert dc["replay_dung_candidate_cu"] is True
    assert dc["replay_measured_system_files"] == 89


def test_04_candidate_HIEN_TAI_khong_duoc_dung_lam_nen_replay(dc):
    """Tiêm ⑨ — candidate hiện tại KHÁC candidate V3; lẫn lộn là vô hiệu."""
    import freeze_evaluation_candidate as F

    hien_tai, _n = F.measured_system_hash()
    assert hien_tai != CANDIDATE_V3, (
        "candidate hiện tại trùng candidate V3 — test này mất ý nghĩa")
    assert dc["replay_measured_system_hash"] != hien_tai


# ══ ③ 0 LƯỢT GỌI ══════════════════════════════════════════════════════════
def test_05_khong_luot_goi_model_nao(dc):
    assert dc["application_llm_calls"] == 0
    assert dc["physical_api_attempts"] == 0
    assert dc["provider_guard_trips"] == 0, (
        "guard đã bị chạm — nghĩa là có đường gọi model trong replay")


# ══ ④ HAI ĐƯỜNG, VÀ CHÚNG KHÁC NHAU ═══════════════════════════════════════
def test_06_route_KHONG_dung_scene3d_con_pipeline_thi_CO():
    """Gốc rễ, đo bằng AST chứ không bằng lời."""
    import ast

    r = ast.parse((GOC / "app" / "simulation" / "semantic_program"
                   / "route.py").read_text(encoding="utf-8"))
    ten_route = {n.id for n in ast.walk(r) if isinstance(n, ast.Name)} | {
        n.attr for n in ast.walk(r) if isinstance(n, ast.Attribute)}
    assert "build_scene3d" not in ten_route, (
        "`route` KHÔNG được dựng scene3d — hướng phụ thuộc một chiều")

    p = ast.parse((GOC / "app" / "ai" / "pipeline.py").read_text(
        encoding="utf-8"))
    ten_pipe = {n.id for n in ast.walk(p) if isinstance(n, ast.Name)} | {
        n.attr for n in ast.walk(p) if isinstance(n, ast.Attribute)}
    assert "_dung_scene3d" in ten_pipe and "build_scene3d" in ten_pipe


def test_07_legacy_projection_tai_hien_quantity_list_RONG(dc):
    """Tiêm ⑦ — bỏ bước scene composition ⇒ đúng con số gốc quay lại."""
    c7 = [h for h in dc["per_case"] if h["case_id"] == "c7a"][0]
    assert c7["legacy_dai_luong_from_route_envelope"] == []
    assert c7["original_scene3d"] is False
    assert c7["original_exact_match"] is False


def test_08_product_path_chay_them_scene_composition(dc):
    c7 = [h for h in dc["per_case"] if h["case_id"] == "c7a"][0]
    assert len(c7["replay_scene_quantities"]) == 3
    assert c7["replay_scene3d"] is True


# ══ ⑤ THẨM QUYỀN ĐÁP SỐ ═══════════════════════════════════════════════════
def test_09_dap_so_doc_tu_final_memory_KHONG_tu_scene3d(dc):
    """Tiêm ⑧ — Scene3D là bằng chứng HIỂN THỊ, không phải thẩm quyền toán."""
    for h in dc["per_case"]:
        if h.get("exact_result_authority") is not None:
            assert h["exact_result_authority"] == "outcome.final_memory", h


def test_10_c7a_dung_TRON_ba_dap_so(dc):
    c7 = [h for h in dc["per_case"] if h["case_id"] == "c7a"][0]
    assert set(c7["expected"]) == {"13", "100π", "65π"}
    assert set(c7["expected"]) <= set(c7["replay_dai_luong_final_memory"])
    assert c7["replay_exact_match"] is True


def test_11_c7a_KHONG_servable_vi_verification_gap(dc):
    """Đúng hoàn toàn về toán mà VẪN không servable — và đó là lỗi HỆ.

    `distance` trên `curved_solid` không chứng thực được, nên route trả
    `postcondition_violated` / `verification_gap`. Đây là cùng hình dạng với
    `duong_4_he_hut_verification` của certifier.
    """
    c7 = [h for h in dc["per_case"] if h["case_id"] == "c7a"][0]
    assert c7["replay_executable"] is True
    assert c7["replay_servable"] is False
    assert c7["replay_failure_category"] == "verification_gap"
    assert c7["replay_verdict_pinned_scorer"] == "SYSTEM_VERIFICATION_FAILURE"


def test_12_hai_bo_phan_lop_LECH_va_dieu_do_duoc_GHI_RA(dc):
    """Bộ 7 lớp của runner mù với `servable`; ghi cả hai thay vì chọn im lặng."""
    x = dc["phan_lop_hai_tham_quyen_LECH_NHAU"]
    assert x["c7a_runner"] == "CORRECT_EXECUTABLE_IR"
    assert x["c7a_pinned_scorer"] == "SYSTEM_VERIFICATION_FAILURE"
    assert "4f7cae90" in x["tham_quyen_chon"]


# ══ ⑥ PHẠM VI ĐÍNH CHÍNH ══════════════════════════════════════════════════
def test_13_chi_MOT_ca_doi(dc):
    assert dc["cases_changed"] == ["c7a"]
    assert sum(1 for h in dc["per_case"] if h["verdict_changed"]) == 1


def test_14_moi_ca_khac_tai_hien_Y_NGUYEN(dc):
    for h in dc["per_case"]:
        if h["case_id"] == "c7a":
            continue
        assert h["verdict_changed"] is False, h["case_id"]
        if h.get("replay_executable") is not None:
            assert h["replay_executable"] == h["original_executable"], h["case_id"]


def test_15_verdict_tong_KHONG_doi(dc):
    tv = dc["threshold_verdict"]
    assert tv["GENERAL_CURVED_SYNTHESIS_ACCEPTANCE"].startswith("FAIL")
    for k in ("BALL", "CYLINDER", "CONE"):
        assert tv[f"PRODUCT_PROMOTION_ELIGIBLE_{k}"] == "NO"


def test_16_pham_vi_hieu_luc_khai_dung_hai_cot_hong(dc):
    v = dc["validity_scope"]
    assert v["V3_GENERATION_EVIDENCE_VALID"] is True
    assert v["V3_GROUNDING_EVIDENCE_VALID"] is True
    assert v["V3_EXACT_SCORING_VALID"] is False
    assert v["V3_SCENE3D_SCORING_VALID"] is False


def test_17_artifact_tu_khai_la_LOP_DINH_CHINH(dc):
    """Tên và nội dung phải nói rõ: không phải một lượt V3 mới."""
    assert dc["loai_artifact"] == "CORRECTION_LAYER"
    assert "KHÔNG phải một lượt V3 mới" in dc["khai"]
    assert dc["measurement_class"].startswith("INTERNAL_ONE_SHOT_ACCEPTANCE")
    assert "OPERATOR_WAIVED" in dc["evaluator"]


def test_18_con_dau_V3_khong_doi(dc):
    dau = json.loads((CV3 / "V3_SEAL.json").read_text(encoding="utf-8"))
    assert dc["case_set_hash"] == dau["case_set_hash"]
    assert dc["pool_hash"] == dau["pool_hash"]
    assert dc["seed"] == dau["seed"] == 5324284654432805119


# ══ ⑲ PHÉP ĐO BẤT BIẾN PHẢI ĐỘC LẬP VỚI LƯỢT CHECKOUT ═════════════════════
#
# `V3_THESIS_EVIDENCE_ALIGNMENT_REPAIR` (2026-09-20). `test_01` ĐỎ trong mọi
# worktree mới mà XANH ở cây nguồn — cùng một commit, hai phán quyết. Nguyên
# nhân: `core.autocrlf = true`, không `.gitattributes`, nên git viết CRLF ra đĩa
# trong khi blob giữ LF. Byte thô đo LƯỢT CHECKOUT, không đo nội dung.
#
# Bốn test dưới đây khoá đúng lớp lỗi ấy lại.
def _lf(p: Path) -> bytes:
    return p.read_bytes().replace(b"\r\n", b"\n")


@pytest.mark.parametrize("ten", sorted(BAM_NOI_DUNG))
def test_19_artifact_nguon_KHONG_con_CR_sau_chuan_hoa(ten):
    """Chuẩn hoá phải khử SẠCH `\\r\\n`; còn `\\r` lẻ là một lớp khác, phải lộ ra."""
    assert b"\r" not in _lf(OUT / ten), (
        f"{ten} còn ký tự CR sau chuẩn hoá — tệp có `\\r` không đi kèm `\\n`, "
        "chuẩn hoá hai dòng không đủ")


@pytest.mark.parametrize("ten", sorted(BAM_NOI_DUNG))
def test_20_bam_KHONG_doi_khi_xuong_dong_doi(ten, tmp_path):
    """CỬA SỔ CHỨNG: cùng nội dung, hai kiểu xuống dòng ⇒ CÙNG một băm.

    Đây là phép kiểm mà bản cũ thiếu, và thiếu nó là lý do bộ test phán quyết
    theo cây làm việc thay vì theo bằng chứng.
    """
    goc = _lf(OUT / ten)
    lf, crlf = tmp_path / "lf.json", tmp_path / "crlf.json"
    lf.write_bytes(goc)
    crlf.write_bytes(goc.replace(b"\n", b"\r\n"))

    assert _bam(lf) == _bam(crlf) == BAM_NOI_DUNG[ten]


@pytest.mark.parametrize("ten", sorted(BAM_NOI_DUNG))
def test_21_bam_VAN_bat_duoc_mot_byte_NOI_DUNG_doi(ten, tmp_path):
    """Chuẩn hoá KHÔNG được làm phép đo mù: đổi một byte nội dung phải ĐỎ."""
    goc = _lf(OUT / ten)
    sua = tmp_path / "sua.json"
    sua.write_bytes(goc.replace(b"{", b"{ ", 1))

    assert _bam(sua) != BAM_NOI_DUNG[ten]


def _blob(rel: str) -> bytes:
    import subprocess

    return subprocess.run(["git", "-C", str(REPO), "cat-file", "-p", f"HEAD:{rel}"],
                          capture_output=True, check=True).stdout


@pytest.mark.parametrize("ten", sorted(BAM_NOI_DUNG))
def test_22_bam_NOI_DUNG_khop_ban_DA_COMMIT(ten):
    """`BAM_NOI_DUNG` phải là băm của blob, không phải của một bản checkout.

    Đọc thẳng qua `git cat-file` nên phép kiểm này không đi qua đĩa — nó là thứ
    duy nhất trong tệp không thể bị `core.autocrlf` làm lệch.
    """
    rel = (OUT / ten).relative_to(REPO).as_posix()
    assert hashlib.sha256(_blob(rel)).hexdigest() == BAM_NOI_DUNG[ten]


@pytest.mark.parametrize("ten", sorted(BAM_NGUON))
def test_23_ban_ghi_LICH_SU_dung_la_phep_do_CRLF_cua_cung_noi_dung(ten):
    """Chứng minh hai bảng mô tả CÙNG MỘT tệp, chỉ khác cách đo.

    Nếu `BAM_NGUON[ten]` không phải băm của bản CRLF **lẫn** bản LF của blob,
    thì giả thuyết *"chỉ là lượt checkout"* SAI và artifact V3 đã thật sự bị
    sửa — khi ấy đây là một lớp lỗi khác hẳn và phải dừng lại điều tra.
    """
    rel = (OUT / ten).relative_to(REPO).as_posix()
    lf = _blob(rel)
    crlf = lf.replace(b"\n", b"\r\n")
    do_duoc = {hashlib.sha256(lf).hexdigest(), hashlib.sha256(crlf).hexdigest()}

    assert BAM_NGUON[ten] in do_duoc, (
        f"{ten}: băm lịch sử không giải thích được bằng LF hay CRLF của nội "
        "dung đã commit — artifact có thể đã bị sửa thật")


def test_24_PHAM_VI_dang_ky_khong_duoc_thu_hep():
    """Bỏ một tệp khỏi bảng đăng ký là cách LÀM XANH mà không sửa gì.

    Test parametrize theo chính bảng ấy, nên xoá một mục chỉ làm ÍT ca đi chứ
    không ĐỎ. Ghim tập tên lại, và ghim cả với artifact đính chính + thư mục
    thật trên đĩa, để phạm vi không co lại trong im lặng.
    """
    mong = {"attribution.json", "curved_acceptance.json", "manifest.json",
            "stage_8a_one_shot.json"}
    assert set(BAM_NOI_DUNG) == mong
    assert set(BAM_NGUON) == mong
    tren_dia = {p.name for p in OUT.glob("*.json")}
    assert mong <= tren_dia, f"thiếu artifact trên đĩa: {sorted(mong - tren_dia)}"
