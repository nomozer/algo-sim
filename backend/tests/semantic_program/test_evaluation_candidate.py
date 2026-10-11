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
CANDIDATE = BENCH / "EVALUATION_CANDIDATE.json"


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


def test_verify_without_a_frozen_manifest_is_refused(tmp_path, monkeypatch, manifest):
    fz = _freeze_module()
    monkeypatch.setattr(fz, "OUT", tmp_path / "missing.json")
    monkeypatch.setattr(fz, "build", lambda: manifest)
    monkeypatch.setattr(fz.sys, "argv", ["freeze", "--verify"])
    assert fz.main() == 2


# ── PRODUCT IDENTITY (review I2, 2026-10-11) ────────────────────────────────────────────────────────────────
# `3b6104e3` narrowed `product_commit_sha` to MEASURED_SYSTEM_PATHS, so a renderer fix under `frontend/src`
# (outside `domains/semantic`) no longer turned --verify red — the W12 incident class. The rule is now named in
# the manifest: product paths minus test-only harness files. A manifest without a rule name is verified with the
# legacy rule it was frozen under, so no historical identity changes. Every case below commits for real in a
# throwaway git repository; nothing is simulated.
import subprocess  # noqa: E402

_REPO_FILES = {
    "backend/app/core.py": "x = 1\n",
    "frontend/src/simulations/domains/semantic/route.ts": "export const r = 1;\n",
    "frontend/src/simulations/domains/geometry/scene3d-view.tsx": "export const v = 1;\n",
    "frontend/src/simulations/domains/geometry/scene3d-view.test.ts": "it('x', () => {});\n",
    "frontend/src/simulations/domains/geometry/scene3d-section-fixture.json": "{}\n",
    "frontend/src/test-setup.ts": "export {};\n",
    "docs/note.md": "n\n",
}


def _commit(root, changes: dict[str, str | None], msg: str) -> str:
    for rel, text in changes.items():
        p = root / rel
        if text is None:
            p.unlink()
        else:
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(text, encoding="utf-8")
    git = ["git", "-C", str(root), "-c", "user.name=t", "-c", "user.email=t@example.invalid"]
    subprocess.run([*git, "add", "-A"], check=True, capture_output=True)
    subprocess.run([*git, "commit", "-q", "-m", msg], check=True, capture_output=True)
    return subprocess.run([*git, "rev-parse", "HEAD"], check=True, capture_output=True, text=True).stdout.strip()


@pytest.fixture
def repo(tmp_path, monkeypatch):
    """(freeze module rooted at a fresh repo, repo path, first commit)."""
    fz = _freeze_module()
    root = tmp_path / "repo"
    root.mkdir()
    subprocess.run(["git", "init", "-q", str(root)], check=True)
    first = _commit(root, dict(_REPO_FILES), "product")
    monkeypatch.setattr(fz, "ROOT", root)
    return fz, root, first


def _frozen(fz, manifest, rule="current"):
    """Real manifest skeleton + identity computed in the throwaway repo (build() needs the real backend)."""
    h, n = fz.measured_system_hash()
    m = {**manifest, "product_commit_sha": fz.product_commit(None if rule is None else fz.PRODUCT_COMMIT_RULE),
         "measured_system": {**manifest["measured_system"], "tree_hash": h, "so_file": n}}
    m.pop("product_commit_rule", None)
    if rule is not None:
        m["product_commit_rule"] = fz.PRODUCT_COMMIT_RULE
    return m


def _verify(fz, monkeypatch, tmp_path, frozen, current) -> int:
    out = tmp_path / "candidate.json"
    out.write_text(json.dumps(frozen), encoding="utf-8")
    monkeypatch.setattr(fz, "OUT", out)
    monkeypatch.setattr(fz, "build", lambda: current)
    monkeypatch.setattr(fz.sys, "argv", ["freeze", "--verify"])
    return fz.main()


def test_I2_1_test_only_commit_keeps_product_identity(repo):
    fz, root, first = repo
    _commit(root, {"frontend/src/simulations/domains/geometry/scene3d-view.test.ts": "it('y', () => {});\n",
                   "frontend/src/test-setup.ts": "export const s = 1;\n"}, "test only")
    assert fz.product_commit(fz.PRODUCT_COMMIT_RULE) == first


def test_I2_2_backend_production_change_moves_identity(repo, manifest, monkeypatch, tmp_path):
    fz, root, first = repo
    frozen = _frozen(fz, manifest)
    second = _commit(root, {"backend/app/core.py": "x = 2\n"}, "backend fix")
    assert fz.product_commit(fz.PRODUCT_COMMIT_RULE) == second != first
    assert _verify(fz, monkeypatch, tmp_path, frozen, _frozen(fz, manifest)) == 1


def test_I2_3_renderer_production_change_is_caught_W12(repo, manifest, monkeypatch, tmp_path, capsys):
    """W12: renderer-only fix ⇒ tree hash unchanged (renderer is not in MEASURED_SYSTEM_PATHS) but identity moves."""
    fz, root, first = repo
    frozen = _frozen(fz, manifest)
    second = _commit(root, {"frontend/src/simulations/domains/geometry/scene3d-view.tsx": "export const v = 2;\n"},
                     "renderer fix")
    current = _frozen(fz, manifest)
    assert current["measured_system"]["tree_hash"] == frozen["measured_system"]["tree_hash"]
    assert current["product_commit_sha"] == second != first
    assert _verify(fz, monkeypatch, tmp_path, frozen, current) == 1
    assert "product_commit_sha" in capsys.readouterr().out


def test_I2_4_renderer_fixture_only_change_keeps_identity(repo):
    fz, root, first = repo
    _commit(root, {"frontend/src/simulations/domains/geometry/scene3d-section-fixture.json": '{"a": 1}\n'},
            "fixture only")
    assert fz.product_commit(fz.PRODUCT_COMMIT_RULE) == first


def test_I2_5_missing_or_changed_measured_file_is_caught(repo, manifest, monkeypatch, tmp_path):
    fz, root, _ = repo
    frozen = _frozen(fz, manifest)
    (root / "frontend/src/simulations/domains/semantic/route.ts").unlink()  # uncommitted: content hash, not git
    current = {**frozen, "measured_system": {**frozen["measured_system"],
                                             "tree_hash": fz.measured_system_hash()[0],
                                             "so_file": fz.measured_system_hash()[1]}}
    assert current["measured_system"]["so_file"] == frozen["measured_system"]["so_file"] - 1
    assert _verify(fz, monkeypatch, tmp_path, frozen, current) == 1


def test_I2_6_verify_on_the_right_candidate_passes(repo, manifest, monkeypatch, tmp_path):
    fz, root, _ = repo
    _commit(root, {"frontend/src/simulations/domains/geometry/scene3d-view.test.ts": "it('z', () => {});\n"}, "t")
    frozen = _frozen(fz, manifest)
    assert _verify(fz, monkeypatch, tmp_path, frozen, _frozen(fz, manifest)) == 0


@pytest.mark.parametrize("field", ["product_commit_sha", "tree_hash", "product_commit_rule"])
def test_I2_7_verify_on_an_altered_candidate_fails(repo, manifest, monkeypatch, tmp_path, field):
    fz, _, _ = repo
    frozen = _frozen(fz, manifest)
    if field == "tree_hash":
        frozen["measured_system"] = {**frozen["measured_system"], "tree_hash": "0" * 64}
    elif field == "product_commit_rule":
        frozen["product_commit_rule"] = "made-up-rule/9"
    else:
        frozen[field] = "0" * 40
    assert _verify(fz, monkeypatch, tmp_path, frozen, _frozen(fz, manifest)) != 0


def test_I2_legacy_manifest_is_verified_with_its_own_rule(repo, manifest, monkeypatch, tmp_path):
    """A manifest frozen before the rule had a name keeps its identity: a later test-only commit moved the legacy
    product commit, and verifying it with the legacy rule must reproduce exactly that commit."""
    fz, root, _ = repo
    _commit(root, {"frontend/src/simulations/domains/geometry/scene3d-view.test.ts": "it('w', () => {});\n"}, "t")
    legacy = _frozen(fz, manifest, rule=None)
    assert "product_commit_rule" not in legacy
    assert legacy["product_commit_sha"] != fz.product_commit(fz.PRODUCT_COMMIT_RULE)
    assert _verify(fz, monkeypatch, tmp_path, legacy, _frozen(fz, manifest)) == 0


def test_I2_every_historical_candidate_reproduces_under_its_recorded_rule():
    """No historical identity changes: each committed EVALUATION_CANDIDATE.json version re-derives its own
    product_commit_sha at its own commit."""
    fz = _freeze_module()
    rel = "docs/evaluation/semantic-benchmark/EVALUATION_CANDIDATE.json"
    versions = fz._git("log", "--format=%H", "--", rel).split()
    checked = 0
    for v in versions:
        try:
            m = json.loads(fz._git("show", f"{v}:{rel}"))
        except json.JSONDecodeError:
            continue
        if not m.get("product_commit_sha"):
            continue
        assert fz.product_commit(m.get("product_commit_rule"), rev=m["commit"]) == m["product_commit_sha"], v
        checked += 1
    assert checked >= 61


def test_I2_test_only_files_are_never_imported_by_product_code():
    """The exclusion is by name; this keeps it honest — no product module may import an excluded file."""
    import fnmatch

    src = ROOT / "frontend" / "src"
    files = [p for p in src.rglob("*") if p.is_file() and p.suffix in (".ts", ".tsx", ".json")]
    fz = _freeze_module()

    def excluded(p):
        rel = p.relative_to(ROOT).as_posix()
        return any(fnmatch.fnmatch(rel, g.replace("**/", "*")) for g in fz.TEST_ONLY_GLOBS)

    hidden = [p for p in files if excluded(p) and not p.name.endswith((".test.ts", ".test.tsx"))]
    assert hidden, "expected fixture/setup files to exist"
    product = [p for p in files if not excluded(p) and p.suffix in (".ts", ".tsx")]
    offenders = [(q.name, p.name) for p in hidden for q in product
                 if p.stem in q.read_text(encoding="utf-8")]
    assert offenders == []
