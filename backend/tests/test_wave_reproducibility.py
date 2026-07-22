# -*- coding: utf-8 -*-
"""M17-RC1 §R1 — lock TÁI LẬP ĐƯỢC của artifact wave đã đóng băng.

Lỗi đã phát hiện ở RC1-C: generator chạy lại HÔM NAY đọc registry MỚI NHẤT nên
sinh số của Wave 2A thay vì số đã công bố của Wave 1. Bằng chứng lịch sử không
tái lập được.

Test này KHÔNG chấp nhận "checkout đè output sai rồi coi là tái lập": nó sinh
lại THẬT từ `input_snapshot.json` rồi so SHA-256 với file đã commit.
"""

from __future__ import annotations

import hashlib
import json

import pytest

from app.evaluation.authenticity_artifacts import (
    build_authenticity_metrics,
    build_authenticity_report_md,
    build_authenticity_results,
    build_curriculum_coverage,
    build_gap_report_md,
    build_generic_leak_ledger_artifact,
    run_offline_audit,
)
from app.evaluation.wave_snapshots import (
    FROZEN_WAVES,
    GENERATOR_VERSION,
    snapshot_for,
)

SCHEMA_VERSION = "1"


def _regenerate(wave_id: str) -> dict[str, bytes]:
    """Sinh lại TOÀN BỘ artifact của wave từ ảnh chụp — đúng đường generator."""
    snap = snapshot_for(wave_id)
    assert snap is not None, f"{wave_id}: thiếu input_snapshot.json"
    records = run_offline_audit(snap)
    meta = {"git_commit": snap.git_commit, "generated_at": snap.generated_at}
    payloads = {
        "authenticity_results.json": build_authenticity_results(records, snap),
        "authenticity_metrics.json": build_authenticity_metrics(records, snap),
        "generic_leak_ledger.json": build_generic_leak_ledger_artifact(records, snap),
        "curriculum_coverage.json": build_curriculum_coverage(records, snap),
    }
    out: dict[str, bytes] = {}
    for name, data in payloads.items():
        payload = {"schema_version": SCHEMA_VERSION, "run_label": f"{wave_id}-offline",
                   "run_meta": meta, "data": data}
        out[name] = (json.dumps(payload, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
    out["simulation_authenticity_report.md"] = build_authenticity_report_md(
        records, snap).encode("utf-8")
    out["curriculum_gap_report.md"] = build_gap_report_md(records, snap).encode("utf-8")
    return out


@pytest.mark.xfail(
    strict=True,
    reason=(
        "M17-RC1 §R1 CHƯA ĐẠT — CHỜ QUYẾT ĐỊNH, không phải lỗi hạ tầng snapshot. "
        "Hạ tầng ĐÃ hoạt động: đầu vào lịch sử replay đúng (xem test bên dưới). "
        "Nhưng cổng §C2 (input sufficiency) TỪ CHỐI 33/55 case W0 và 43/68 case "
        "W1 — analyze stub lịch sử mô tả dữ liệu bằng lời mà không nêu giá trị "
        "cụ thể. Đây là THAY ĐỔI HÀNH VI PRODUCTION có thật, nên artifact lịch "
        "sử không thể tái lập cho tới khi chốt: (a) cổng §C2 đúng và bằng chứng "
        "lịch sử được tuyên bố superseded, hay (b) cổng §C2 quá chặt và phải "
        "nới. Cả hai đều cần live smoke §C2 (checkpoint này cấm chạy live). "
        "strict=True: khi nào chuyện này được giải quyết mà test lại XANH thì "
        "pytest sẽ báo đỏ, buộc phải xoá marker — không để nó mục ở đây."
    ),
)
@pytest.mark.parametrize("wave_id", FROZEN_WAVES)
def test_wave_sinh_lai_byte_identical(wave_id):
    """Sinh lại từ snapshot phải khớp TỪNG BYTE với artifact đã công bố.

    Đỏ ở đây nghĩa là bằng chứng lịch sử đã trôi THẬT — phải điều tra, không
    được cập nhật hash cho xanh."""
    snap = snapshot_for(wave_id)
    regenerated = _regenerate(wave_id)
    lech = []
    for name, expected_sha in sorted(snap.artifact_sha256.items()):
        assert name in regenerated, f"{wave_id}/{name}: generator không sinh ra file này"
        actual = hashlib.sha256(regenerated[name]).hexdigest()
        if actual != expected_sha:
            lech.append(name)
    assert lech == [], f"{wave_id}: {len(lech)} artifact KHÔNG tái lập được: {lech}"


@pytest.mark.parametrize("wave_id", FROZEN_WAVES)
def test_registry_hien_tai_khong_lam_doi_so_lich_su(wave_id):
    """Cốt lõi §R1: thêm target/family/cổng SAU wave không được làm đổi số của
    wave đó. Kiểm bằng chính snapshot (không phụ thuộc registry sống)."""
    from app.evaluation.authenticity_audit import classify_targets

    snap = snapshot_for(wave_id)
    records = run_offline_audit(snap)
    assert len(records) == snap.case_count
    # Replay dùng ĐÚNG đầu vào lịch sử, không rò fixture sống vào: prompt của
    # bản ghi phải khớp snapshot từng ký tự.
    assert [r.case_id for r in records] == list(snap.case_ids)
    assert [r.archetype for r in records] == [c.archetype for c in snap.cases]
    cls = classify_targets(records, list(snap.target_ids))
    assert set(cls) == set(snap.target_ids), (
        f"{wave_id}: phân loại chạm target ngoài wave (registry sống rò vào)")
    # cổng thêm sau (structure/input_sufficiency/completeness_*) VẪN CHẠY thật
    # trong pipeline nhưng KHÔNG được lọt vào bản ghi lịch sử.
    ghi = {g["gate"] for r in records for g in r.gates}
    assert ghi <= snap.gate_names, f"{wave_id}: cổng mới lọt vào bản ghi: {ghi - snap.gate_names}"


@pytest.mark.parametrize("wave_id", FROZEN_WAVES)
def test_snapshot_khai_du_truong_bat_buoc(wave_id):
    snap = snapshot_for(wave_id)
    assert snap.input_snapshot_id and snap.git_commit
    assert snap.generator_version == GENERATOR_VERSION
    assert snap.case_count > 0 and snap.target_count > 0 and snap.family_count > 0
    assert snap.artifact_sha256, "thiếu khoá nội dung artifact"
    for c in snap.cases:
        assert c.analysis, f"{c.case_id}: snapshot thiếu analysis (không replay được)"


def test_wave_dang_mo_van_doc_registry_song():
    """Wave chưa đóng băng KHÔNG có snapshot → generator đọc trạng thái hiện
    tại như trước (không làm hỏng quy trình thường ngày)."""
    assert snapshot_for("wave2a") is None
    assert snapshot_for("khong-ton-tai") is None
