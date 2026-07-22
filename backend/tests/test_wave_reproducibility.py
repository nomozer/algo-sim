# -*- coding: utf-8 -*-
"""M17-RC1 §R1+§E — HAI CHẾ ĐỘ chạy lại wave, không trộn.

Lỗi gốc (RC1-C phát hiện): generator chạy lại hôm nay đọc registry MỚI NHẤT nên
sinh số của Wave 2A thay vì số đã công bố của Wave 1.

Lỗi THỨ HAI (chính tôi mắc ở bản §R1 đầu): gộp "tái lập lịch sử" với "chạy lại
theo chính sách hiện tại" vào một test byte-identical rồi dán xfail. Như vậy là
ghi "cổng mới từ chối fixture cũ" thành lỗi tái lập — sai bản chất, và xfail
che mất một thay đổi CÓ CHỦ ĐÍCH.

- ``historical_reproduction`` (scripts/historical_reproduction.py): worktree +
  generator + fixture LỊCH SỬ → byte-identical. Cần git, không chạy trong
  pytest thường.
- ``current_policy_replay`` (đây): đầu vào lịch sử BẤT BIẾN + pipeline HIỆN
  TẠI → kết quả ĐƯỢC PHÉP đổi, sản phẩm là *migration report*.

Test dưới đây khoá chế độ 2 và khoá tính bất biến của snapshot. KHÔNG có
assert byte-identical ở đây — đó là việc của chế độ 1.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from app.evaluation.authenticity_artifacts import run_offline_audit
from app.evaluation.wave_replay import CHANGE_KINDS, build_migration_report
from app.evaluation.wave_snapshots import (
    FROZEN_WAVES,
    GENERATOR_VERSION,
    snapshot_for,
)

_WAVE_DIR = Path(__file__).resolve().parents[2] / "docs" / "evaluation" / "m17"


def _published(wave_id: str) -> dict:
    return json.loads(
        (_WAVE_DIR / wave_id / "authenticity_results.json").read_text(encoding="utf-8"))


# ── ảnh chụp đầu vào: đủ và bất biến ─────────────────────────────
@pytest.mark.parametrize("wave_id", FROZEN_WAVES)
def test_snapshot_khai_du_truong_bat_buoc(wave_id):
    snap = snapshot_for(wave_id)
    assert snap is not None, f"{wave_id}: thiếu input_snapshot.json"
    assert snap.input_snapshot_id and snap.git_commit
    assert snap.generator_version == GENERATOR_VERSION
    assert snap.case_count > 0 and snap.target_count > 0 and snap.family_count > 0
    assert snap.artifact_sha256, "thiếu khoá nội dung artifact"
    for c in snap.cases:
        assert c.analysis, f"{c.case_id}: snapshot thiếu analysis (không replay được)"


@pytest.mark.parametrize("wave_id", FROZEN_WAVES)
def test_snapshot_khop_artifact_da_cong_bo(wave_id):
    """Ảnh chụp phải mô tả ĐÚNG wave nó đi kèm (không lệch case/target)."""
    snap, pub = snapshot_for(wave_id), _published(wave_id)
    assert list(snap.case_ids) == [r["case_id"] for r in pub["data"]["case_records"]]
    assert list(snap.target_ids) == sorted(pub["data"]["target_classifications"])
    assert snap.git_commit == pub["run_meta"]["git_commit"]


@pytest.mark.parametrize("wave_id", FROZEN_WAVES)
def test_artifact_da_cong_bo_con_nguyen_ven(wave_id):
    """Khoá nội dung: file đã commit phải khớp SHA-256 ghi trong snapshot.
    Đỏ ở đây = ai đó SỬA bằng chứng lịch sử."""
    import hashlib

    snap = snapshot_for(wave_id)
    for name, sha in sorted(snap.artifact_sha256.items()):
        p = _WAVE_DIR / wave_id / name
        assert p.exists(), f"{wave_id}/{name}: mất file đã công bố"
        assert hashlib.sha256(p.read_bytes()).hexdigest() == sha, (
            f"{wave_id}/{name}: nội dung đã ĐỔI so với lúc công bố")


# ── chế độ 2: current_policy_replay ──────────────────────────────
@pytest.mark.parametrize("wave_id", FROZEN_WAVES)
def test_replay_dung_dau_vao_lich_su_khong_ro_fixture_song(wave_id):
    """Replay phải dùng ĐÚNG đầu vào đã đóng băng — registry/fixture hiện tại
    không được rò vào (đó chính là lỗi gốc §R1)."""
    snap = snapshot_for(wave_id)
    records = run_offline_audit(snap)
    assert [r.case_id for r in records] == list(snap.case_ids)
    assert [r.archetype for r in records] == [c.archetype for c in snap.cases]
    ghi = {g["gate"] for r in records for g in r.gates}
    assert ghi <= snap.gate_names, f"cổng mới lọt vào bản ghi: {ghi - snap.gate_names}"


@pytest.mark.parametrize("wave_id", FROZEN_WAVES)
def test_migration_report_giai_thich_duoc_moi_thay_doi(wave_id):
    """Kết quả ĐƯỢC PHÉP đổi — nhưng mỗi thay đổi phải quy được về một chính
    sách mới CÓ CHỦ ĐÍCH. Thay đổi không giải thích được là tín hiệu hồi quy
    thật, phải điều tra."""
    snap = snapshot_for(wave_id)
    rep = build_migration_report(snap, _published(wave_id))
    assert rep["mode"] == "current_policy_replay"
    assert set(rep["change_counts"]) == set(CHANGE_KINDS)
    assert sum(rep["change_counts"].values()) == rep["case_count"]
    assert rep["unexplained_changes"] == [], (
        f"{wave_id}: thay đổi KHÔNG quy được về chính sách mới nào: "
        f"{rep['unexplained_changes']}")
    for e in rep["changed_cases"]:
        assert e["change_kind"] in CHANGE_KINDS
        if e["change_kind"] == "blocked_by_new_gate":
            assert e["changed_gate_or_policy"], f"{e['case_id']}: thiếu cổng gây đổi"
            assert e["historical_fixture_violates_current_contract"]


def test_wave_dang_mo_van_doc_registry_song():
    """Wave chưa đóng băng KHÔNG có snapshot → generator đọc trạng thái hiện
    tại như trước (quy trình thường ngày không đổi)."""
    assert snapshot_for("wave2a") is None
    assert snapshot_for("khong-ton-tai") is None
