# -*- coding: utf-8 -*-
"""Ba bộ đếm của wave đo — khoá NGHĨA, không chỉ khoá giá trị.

**0 lượt gọi model thật.** Phải xanh TRƯỚC lượt live đầu tiên của
`MINIMAL_CARD_CONSOLIDATION_AND_FRESH_CONFIRMATION` — đó là điều kiện §2 của
brief, và lý do thì cụ thể: wave trước công bố `PHYSICAL_ATTEMPTS = 2` cho một
lượt chỉ phát **một** request, nên trước khi đo tiếp phải chứng minh bộ đếm mới
không lặp lại đúng lỗi ấy.

Bằng chứng mạnh nhất ở đây là `test_C1`: một ứng viên nạp **từ artifact** đi
qua trọn vòng xử lý mà `physical_api_attempts` **vẫn bằng 0**.
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

import pytest

GOC = Path(__file__).resolve().parents[2]
for p in (str(GOC), str(GOC / "scripts")):
    if p not in sys.path:
        sys.path.insert(0, p)

from app.ai.gemini import ApiBudget  # noqa: E402
from wave_counters import TU_API, TU_ARTIFACT, BoDemWave  # noqa: E402

RA_REPAIR = (GOC.parent / "docs/evaluation/geometry"
             / "point-initialization-repair-efficacy")
DINH_CHINH = RA_REPAIR / "COUNTER_CORRECTION.json"


@pytest.fixture()
def dc() -> dict:
    return json.loads(DINH_CHINH.read_text(encoding="utf-8"))


@pytest.fixture()
def bo_dem() -> BoDemWave:
    return BoDemWave(ApiBudget())


# ══ A. ARTIFACT NGUỒN KHÔNG ĐƯỢC SỬA ══════════════════════════════════════
#
# Đính chính chỉ có nghĩa khi nó còn trỏ đúng bản đã công bố. Sửa artifact
# nguồn mà quên đính chính ⇒ ĐỎ ở đây.
def test_A1_hash_artifact_nguon_khop(dc):
    for ten, mong_doi in dc["doi_tuong"]["artifact_nguon_sha256"].items():
        that = hashlib.sha256((RA_REPAIR / ten).read_bytes()).hexdigest()
        assert that == mong_doi, (
            f"{ten} đã đổi kể từ lúc phát hành đính chính.\n"
            f"  đăng ký: {mong_doi}\n  hiện tại: {that}")


def test_A2_gia_tri_cu_van_nguyen_ven_trong_artifact_nguon(dc):
    """Giữ nguyên bảng số gốc — đính chính viết BÊN TRÊN, không đè lên."""
    rec = json.loads(
        (RA_REPAIR / "repair_repair-20260906T212731Z.json").read_text(
            encoding="utf-8"))
    assert rec["manifest"]["physical_attempts"] == 2
    assert dc["bang_doi_chieu"]["truoc_dinh_chinh"]["physical_attempts"] == 2


def test_A3_bang_chung_doc_lap_van_noi_MOT_request(dc):
    """Telemetry đếm ở tầng transport, KHÔNG qua bộ đếm probe."""
    rec = json.loads(
        (RA_REPAIR / "repair_repair-20260906T212731Z.json").read_text(
            encoding="utf-8"))
    calls = rec["tokens"]["theo_stage"]["semantic_program"]["calls"]
    assert calls == 1
    assert dc["bang_chung_doc_lap"]["telemetry_calls"] == calls
    assert dc["bang_doi_chieu"]["sau_dinh_chinh"]["physical_api_attempts"] == 1
    assert dc["bang_doi_chieu"]["sau_dinh_chinh"]["candidate_attempts"] == 2


# ══ B. BA TRƯỜNG CÓ NGHĨA RIÊNG ═══════════════════════════════════════════
def test_B1_ba_truong_doc_lap_nhau(bo_dem):
    assert bo_dem.bao_cao()["logical_application_calls"] == 0
    assert bo_dem.bao_cao()["physical_api_attempts"] == 0
    assert bo_dem.bao_cao()["candidate_attempts"] == 0


def test_B2_hai_truong_dau_DAN_XUAT_tu_ApiBudget(bo_dem):
    """Không có thẩm quyền đếm thứ hai — sửa `ApiBudget` là hai trường đổi theo."""
    ng = bo_dem._budget
    ng.note_call()
    ng.note_request(is_retry=False)
    ng.note_request(is_retry=True)          # retry transport
    assert bo_dem.logical_application_calls == 1
    assert bo_dem.physical_api_attempts == 2, (
        "retry transport PHẢI tính vào physical_api_attempts")
    assert bo_dem.retry_requests == 1
    assert bo_dem.candidate_attempts == 0, (
        "retry không sinh thêm ứng viên nào")


def test_B3_khong_the_gan_tay_hai_truong_dan_xuat(bo_dem):
    for ten in ("logical_application_calls", "physical_api_attempts"):
        with pytest.raises(AttributeError):
            setattr(bo_dem, ten, 99)


def test_B4_nguon_ung_vien_la_tap_dong(bo_dem):
    with pytest.raises(ValueError):
        bo_dem.ghi_ung_vien("KHONG_CO_NGUON_NAY")


# ══ C. PHÉP CHỨNG MINH — ỨNG VIÊN TỪ ARTIFACT KHÔNG TÍNH LÀ REQUEST ══════
#
# Đây là điều kiện §2 của brief, và là đúng lỗ mà wave trước đã sa vào.
def test_C1_ung_vien_nap_tu_artifact_KHONG_tang_physical(bo_dem, tmp_path):
    nguon = tmp_path / "raw_candidate_nguon.json"
    nguon.write_text('{"spec_version": "1.0"}', encoding="utf-8")

    raw = nguon.read_text(encoding="utf-8")          # ← đọc file, không ra mạng
    bo_dem.ghi_ung_vien(TU_ARTIFACT, ghi_chu=nguon.name)

    r = bo_dem.bao_cao()
    assert r["candidate_attempts"] == 1
    assert r["physical_api_attempts"] == 0, (
        "một ứng viên đọc từ file KHÔNG được tính là request API — đây chính "
        "là lỗi mà REPAIR_PROBE_COUNTER_DECOMPOSITION đính chính")
    assert r["logical_application_calls"] == 0
    assert r["phan_ra"]["candidate_attempts_tu_artifact"] == 1
    assert json.loads(raw)["spec_version"] == "1.0"


@pytest.mark.anyio
async def test_C2_tai_hien_dung_hinh_dang_luot_repair(bo_dem):
    """Dựng lại lượt `repair-20260906T212731Z` bằng stub — ra ĐÚNG ba số mới.

    Hình dạng y hệt probe thật: lượt 0 trả raw lịch sử (không ra mạng), lượt 1
    gọi provider. Khác đúng một điều — bộ đếm mới không tính lượt 0 là request.
    """
    ng = bo_dem._budget

    async def call_gemini_gia(*_a, **_kw) -> str:
        ng.note_call()
        ng.note_request(is_retry=False)
        return '{"spec_version": "1.0", "da_sua": true}'

    async def provider(lan: int) -> str:
        if lan == 0:
            bo_dem.ghi_ung_vien(TU_ARTIFACT, ghi_chu="raw lịch sử")
            return '{"spec_version": "1.0", "hong": true}'
        ra = await call_gemini_gia()
        bo_dem.ghi_ung_vien(TU_API, ghi_chu="ứng viên sửa")
        return ra

    await provider(0)
    await provider(1)

    r = bo_dem.bao_cao()
    assert r == {
        "logical_application_calls": 1,
        "physical_api_attempts": 1,
        "candidate_attempts": 2,
        "phan_ra": {
            "candidate_attempts_tu_artifact": 1,
            "candidate_attempts_tu_api": 1,
            "candidate_attempts_theo_tang": {"raw lịch sử": 1,
                                             "ứng viên sửa": 1},
            "retry_requests": 0,
            "transient_hits": 0,
            "budget_aborted": False,
        },
        "dinh_nghia": r["dinh_nghia"],
    }


def test_C4_tong_ung_vien_LUON_di_kem_phan_ra_theo_tang(bo_dem):
    """Một wave end-to-end gọi model ở nhiều TẦNG khác nhau.

    `analyze` trả một HỢP ĐỒNG, `semantic_program` trả một CHƯƠNG TRÌNH. Đọc
    tổng như "số ứng viên chương trình" là đúng lớp hiểu nhầm mà đính chính
    này đi sửa — nên tổng không được đứng một mình.
    """
    bo_dem.ghi_ung_vien(TU_API, ghi_chu="semantic_analyze")
    for _ in range(3):
        bo_dem.ghi_ung_vien(TU_API, ghi_chu="semantic_program")
    r = bo_dem.bao_cao()
    assert r["candidate_attempts"] == 4
    assert r["phan_ra"]["candidate_attempts_theo_tang"] == {
        "semantic_analyze": 1, "semantic_program": 3}


@pytest.mark.anyio
async def test_C3_TIEM_LOI_dem_kieu_cu_thi_ra_so_da_cong_bo(bo_dem):
    """Tiêm lỗi: đếm ở MỌI lần gọi provider ⇒ tái hiện `2` đã công bố.

    Không có test này thì `test_C2` chỉ chứng minh 'số mới đúng', chứ không
    chứng minh 'số cũ sai VÌ LÝ DO NÀY'.
    """
    kieu_cu = {"physical": 0}

    async def provider(lan: int) -> None:
        kieu_cu["physical"] += 1          # ← lỗi: tăng TRƯỚC khi rẽ nhánh
        if lan == 0:
            return
        bo_dem._budget.note_call()
        bo_dem._budget.note_request(is_retry=False)

    await provider(0)
    await provider(1)

    assert kieu_cu["physical"] == 2, "tái hiện đúng con số đã công bố"
    assert bo_dem.physical_api_attempts == 1, "bộ đếm mới không lặp lại lỗi ấy"


# ══ D. RÀNG BUỘC CHO WAVE MỚI ════════════════════════════════════════════
def test_D1_wave_moi_bi_rang_buoc_dung_ba_dinh_nghia(dc):
    rb = dc["rang_buoc_cho_wave_moi"]
    assert rb["wave"] == "MINIMAL_CARD_CONSOLIDATION_AND_FRESH_CONFIRMATION"
    assert rb["khoa_bang"] == "backend/tests/geometry/test_counter_decomposition.py"
    assert Path(GOC / "tests/geometry/test_counter_decomposition.py").exists()
