# -*- coding: utf-8 -*-
"""Khoá EVALUATION CANDIDATE — danh tính bản được đo (spec §7.3, §7.4).

Ý nghĩa của mốc này: SEALED chỉ có giá trị khi biết **đo bản nào**. Không có nó
thì sau khi thấy số, mọi câu "à lúc đó taxonomy còn khác" đều không kiểm chứng
được — và đó chính là cách một benchmark mất giá trị mà không ai nhận ra.

Test này ĐỎ khi taxonomy / tập primitive / schema / DEV đổi mà candidate không
được đóng băng lại. Nếu lệch **vì một kết quả SEALED** thì đó là vi phạm luật
con dấu: DEV được phép làm thay đổi hệ, SEALED chỉ được phép làm thay đổi KẾT
LUẬN của luận văn.
"""
import hashlib
import json
import os
import typing
from pathlib import Path

import pytest

from app.main import CACHE_VERSION
from app.simulation.semantic_program.contract import (
    SPEC_VERSION,
    VisualContainerBinding,
)
from app.simulation.semantic_program.obligations import OBLIGATION_KINDS

ROOT = Path(__file__).resolve().parents[3]
BENCH = ROOT / "docs" / "evaluation" / "semantic-benchmark"
CANDIDATE = Path(os.environ.get("ALGOSIM_TEST_CANDIDATE", BENCH / "EVALUATION_CANDIDATE.json"))


def _sha(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


@pytest.fixture(scope="module")
def manifest() -> dict:
    assert CANDIDATE.exists(), (
        "Thiếu EVALUATION_CANDIDATE.json — chạy "
        "backend/scripts/freeze_evaluation_candidate.py"
    )
    return json.loads(CANDIDATE.read_text(encoding="utf-8"))


def test_cache_version_khop_nguon(manifest):
    assert manifest["cache_version"] == CACHE_VERSION


def test_spec_version_ir_khop_nguon(manifest):
    assert manifest["spec_version_ir"] == SPEC_VERSION


def test_taxonomy_khong_troi_khoi_ban_da_dong_bang(manifest):
    hien_tai = {k: sorted(v) for k, v in sorted(OBLIGATION_KINDS.items())}
    assert manifest["taxonomy"]["hash"] == _sha(
        json.dumps(hien_tai, ensure_ascii=False, sort_keys=True)
    ), (
        "Taxonomy đã đổi sau khi đóng băng candidate. Nếu đổi vì một case SEALED "
        "⇒ VI PHẠM luật con dấu (§7.4). Nếu đổi từ DEV trước khi seal ⇒ đóng băng "
        "lại candidate."
    )


def test_tap_primitive_khong_troi(manifest):
    hien_tai = sorted(
        typing.get_args(VisualContainerBinding.model_fields["primitive"].annotation)
    )
    assert manifest["visual_primitive_set"]["hash"] == _sha(
        json.dumps(hien_tai, ensure_ascii=False)
    )
    assert "graph_view" in manifest["visual_primitive_set"]["primitives"]


def test_schema_khong_troi(manifest):
    schema = ROOT / "docs" / "schemas" / "semantic_program.schema.json"
    assert manifest["schema_semantic_program"]["hash"] == _sha(
        schema.read_text(encoding="utf-8")
    )


def test_dev_fingerprint_khong_troi(manifest):
    """Băm NỘI DUNG, không băm cách lưu — dùng CHUNG hàm với script đóng băng.

    Băm `read_bytes()` thô ở đây thì test đỏ trên Windows sau mỗi lần git
    chuyển LF → CRLF, mà nội dung không đổi một ký tự. Xem `bam_noi_dung`.
    """
    bam_noi_dung = _freeze_module().bam_noi_dung

    dev = BENCH / "dev" / "cases.json"
    assert manifest["dev"]["fingerprint"] == \
        hashlib.sha256(bam_noi_dung(dev)).hexdigest()
    assert manifest["dev"]["so_case"] == 20


def test_fingerprint_GIONG_NHAU_giua_LF_va_CRLF(tmp_path):
    """Điều kiện sống của cả cơ chế đóng băng: **tái lập được trên máy khác**.

    Đo được 2026-08-24: `dev/cases.json` có 283 dòng CRLF trên đĩa trong khi
    git lưu LF, và hai bản băm ra hai giá trị khác nhau. Cổng đóng băng lúc ấy
    báo *"hệ được đo đã trôi"* dù không ai đụng vào — một báo động giả mà nếu
    quen mắt thì lần trôi THẬT cũng bị bỏ qua.
    """
    bam_noi_dung = _freeze_module().bam_noi_dung

    noi_dung = '{\n  "a": 1,\n  "b": [2, 3]\n}\n'
    lf = tmp_path / "lf.json"
    crlf = tmp_path / "crlf.json"
    lf.write_bytes(noi_dung.encode("utf-8"))
    crlf.write_bytes(noi_dung.replace("\n", "\r\n").encode("utf-8"))

    assert lf.read_bytes() != crlf.read_bytes(), "hai file phải khác byte thô"
    assert bam_noi_dung(lf) == bam_noi_dung(crlf), \
        "cùng nội dung mà băm khác nhau ⇒ fingerprint không tái lập được"


def test_gia_tri_LF_la_gia_tri_DUNG__manifest_cu_van_khop(manifest):
    """Chuẩn hoá về LF, không về CRLF — vì LF là thứ git lưu.

    Nhờ vậy mọi manifest đã ghi TRƯỚC bản vá vẫn khớp, không phải viết lại lịch
    sử. Chọn chiều ngược lại sẽ làm hỏng mọi artifact đã đóng băng.
    """
    bam_noi_dung = _freeze_module().bam_noi_dung

    dev = (BENCH / "dev" / "cases.json")
    assert bam_noi_dung(dev) == dev.read_bytes().replace(b"\r\n", b"\n")


# ── MÃ SẢN PHẨM, không chỉ hợp đồng ──────────────────────────────
# Năm fingerprint ở trên khoá HỢP ĐỒNG (taxonomy · primitive · schema · DEV ·
# CACHE_VERSION). Chúng hoàn toàn MÙ trước việc sửa `pipeline.py`, `route.py`,
# interpreter, validator, hay bất kỳ checker nào — tức mù trước đúng loại thay
# đổi mà sự cố "route chưa từng được nối" đã cho thấy là có thật.
#
# Không có test này thì câu "hệ được đo = <commit>" chỉ là một nhãn trong báo
# cáo, không phải mệnh đề máy kiểm được.


def _freeze_module():
    import importlib.util

    p = ROOT / "backend" / "scripts" / "freeze_evaluation_candidate.py"
    spec = importlib.util.spec_from_file_location("freeze_evaluation_candidate", p)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def test_ma_san_pham_khong_troi_khoi_ban_da_dong_bang(manifest):
    fz = _freeze_module()
    hien_tai, so_file = fz.measured_system_hash()
    assert manifest["measured_system"]["tree_hash"] == hien_tai, (
        "MÃ SẢN PHẨM của hệ được đo đã đổi sau khi đóng băng candidate. Xem "
        f"`git diff {manifest.get('commit_ngan')} HEAD -- "
        + " ".join(fz.MEASURED_SYSTEM_PATHS) + "`. Đổi vì một case SEALED ⇒ VI "
        "PHẠM luật con dấu (§7.4)."
    )
    assert manifest["measured_system"]["so_file"] == so_file


def test_tap_duong_dan_do_KHONG_lan_bo_do_vao(manifest):
    """Harness phải nằm NGOÀI, nếu không thì thêm một test là candidate đỏ và
    người ta sẽ đóng băng lại candidate cho xong — làm hỏng chính con dấu."""
    fz = _freeze_module()
    for p in fz.MEASURED_SYSTEM_PATHS:
        assert not p.startswith("backend/tests"), p
        assert not p.startswith("backend/scripts"), p
        assert not p.startswith("docs"), p
    assert "backend/app" in fz.MEASURED_SYSTEM_PATHS, (
        "thiếu mã production backend thì cổng này không khoá được gì"
    )


def test_ma_san_pham_bao_trum_dung_cac_module_cua_route():
    """Đường dẫn khai theo NGUYÊN TẮC ('backend/app' là sản phẩm), nhưng vẫn
    phải khẳng định nó thật sự phủ các module lõi — khai đúng mà quét sót thì
    cổng xanh giả."""
    fz = _freeze_module()
    phu = {f.relative_to(ROOT).as_posix() for f in fz._measured_system_files()}
    for bat_buoc in (
        "backend/app/ai/pipeline.py",
        "backend/app/ai/gemini.py",
        # Hai prompt của ĐƯỜNG SẢN PHẨM. `semantic_program.md`/
        # `semantic_analyze.md` là prompt của miền Tin học — sau
        # `LEGACY_INFORMATICS_REMOVAL` không lượt nào gửi chúng nữa, nên khai
        # chúng ở đây là khai một cổng canh một cánh cửa không còn ai đi qua.
        "backend/app/ai/skills/geometry_analyze.md",
        "backend/app/ai/skills/geometry_program_generator.md",
        "backend/app/simulation/semantic_program/route.py",
        "backend/app/simulation/semantic_program/interpreter.py",
        "backend/app/simulation/semantic_program/validator.py",
        "backend/app/simulation/semantic_program/grounding_gate.py",
        "backend/app/simulation/semantic_program/coverage_gate.py",
        "backend/app/simulation/semantic_program/postconditions.py",
        # `execution_authority_gate.py` đã gỡ cùng đường Tin học. Thứ thay nó
        # trên đường hình học là `domain_profile.co_duong_thuc_thi`.
        "backend/app/simulation/semantic_program/domain_profile.py",
        "backend/app/simulation/semantic_program/ir_static_check.py",
        "backend/app/simulation/semantic_program/hoisting.py",
        "backend/app/simulation/geometry/kernel.py",
    ):
        assert bat_buoc in phu, f"cổng mã sản phẩm KHÔNG phủ {bat_buoc}"


def test_khong_quet_pycache():
    fz = _freeze_module()
    assert not any("__pycache__" in str(f) for f in fz._measured_system_files()), (
        "quét bytecode ⇒ hash đổi theo lần chạy, cổng thành nhiễu rồi bị tắt"
    )


def test_candidate_ghi_dung_commit_va_cay_sach(manifest):
    """Cây bẩn ⇒ trường `commit` không định danh được bản đang đo."""
    assert manifest["cay_lam_viec_sach"] is True, (
        "Candidate được đóng băng trên cây làm việc BẨN — commit ghi trong đó "
        "không định danh được bản thật sự đem đo."
    )
    assert len(manifest["commit"]) == 40


def test_explicit_branch_verification_is_read_only(tmp_path, monkeypatch, manifest):
    """An opt-in must verify real hashes without rewriting the frozen A/B file."""
    fz = _freeze_module()
    target = tmp_path / "branch.json"
    target.write_text(json.dumps(manifest), encoding="utf-8")
    before = target.read_bytes()
    monkeypatch.setenv("ALGOSIM_TEST_CANDIDATE", str(target))
    monkeypatch.setattr(fz, "build", lambda: manifest)
    monkeypatch.setattr(fz.sys, "argv", ["freeze", "--verify"])
    assert fz.main() == 0
    assert target.read_bytes() == before


def test_explicit_branch_verification_rejects_drift(tmp_path, monkeypatch, manifest):
    fz = _freeze_module()
    target = tmp_path / "branch.json"
    target.write_text(json.dumps(manifest), encoding="utf-8")
    changed = {**manifest, "measured_system": {**manifest["measured_system"], "tree_hash": "0" * 64}}
    monkeypatch.setenv("ALGOSIM_TEST_CANDIDATE", str(target))
    monkeypatch.setattr(fz, "build", lambda: changed)
    monkeypatch.setattr(fz.sys, "argv", ["freeze", "--verify"])
    assert fz.main() == 1


def test_explicit_branch_verification_rejects_missing(tmp_path, monkeypatch, manifest):
    fz = _freeze_module()
    monkeypatch.setenv("ALGOSIM_TEST_CANDIDATE", str(tmp_path / "missing.json"))
    monkeypatch.setattr(fz, "build", lambda: manifest)
    monkeypatch.setattr(fz.sys, "argv", ["freeze", "--verify"])
    assert fz.main() == 2


def test_branch_test_identity_cannot_freeze(tmp_path, monkeypatch, manifest):
    fz = _freeze_module()
    target = tmp_path / "branch.json"
    legacy = tmp_path / "legacy.json"
    legacy.write_text("frozen", encoding="utf-8")
    monkeypatch.setenv("ALGOSIM_TEST_CANDIDATE", str(target))
    monkeypatch.setattr(fz, "OUT", legacy)
    monkeypatch.setattr(fz, "build", lambda: manifest)
    monkeypatch.setattr(fz.sys, "argv", ["freeze"])
    assert fz.main() == 2
    assert not target.exists()
    assert legacy.read_text(encoding="utf-8") == "frozen"


def test_product_provenance_uses_measured_paths_not_renderer_tests(monkeypatch):
    fz = _freeze_module()
    calls = []
    original = fz._git
    def traced(*args):
        calls.append(args)
        return original(*args)
    monkeypatch.setattr(fz, "_git", traced)
    fz.build()
    assert ("log", "-1", "--format=%H", "--", *fz.MEASURED_SYSTEM_PATHS) in calls
