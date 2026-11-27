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
import sys
import typing
from pathlib import Path

import pytest

from app.main import CACHE_VERSION
from app.simulation.semantic_program.contract import SPEC_VERSION
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
    # (/13) Không còn primitive hiển thị container: tập đã đóng băng phải là tập RỖNG (không phải trường vắng).
    hien_tai: list[str] = []
    assert manifest["visual_primitive_set"]["hash"] == _sha(
        json.dumps(hien_tai, ensure_ascii=False)
    )
    assert manifest["visual_primitive_set"]["primitives"] == []      # (/13) bản cũ đòi `graph_view` — đã gỡ


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
    """Phân tách rõ Historical Freeze Integrity và Current Product Core Preservation (Phương án 1).

    - Nhóm A (Historical Freeze): xác minh snapshot trong EVALUATION_CANDIDATE.json khớp
      tuyệt đối với Git tree tại đúng commit nguồn (`600f5105d`) và khớp Git HEAD.
    - Nhóm B (Current Product Core): xác minh 0 thay đổi trong vùng lõi đánh giá
      (`backend/app/simulation/`, `backend/app/ai/`, `frontend/src/simulations/domains/semantic/`)
      so với mốc lịch sử, đồng thời xác nhận chế độ strict `--verify` VẪN phát hiện và báo lỗi
      khi mã sản phẩm hiện tại (vd: `backend/app/accounts/` hoặc Landing) khác bản đóng băng.
    """
    fz = _freeze_module()

    # Nhóm A: Toàn vẹn lịch sử tại commit nguồn (không chỉnh sửa working tree)
    hist = fz.verify_historical_candidate()
    assert hist["verdict"] == "PASS", hist
    assert hist["actual_historical_tree_hash"] == manifest["measured_system"]["tree_hash"]
    assert hist["actual_historical_so_file"] == manifest["measured_system"]["so_file"]
    assert hist["provenance_matches_head"] is True

    # Nhóm B: Bảo vệ vùng lõi Geometry/AI/Semantic và tính trung thực của strict `--verify`
    diff = fz.diff_measured_system_vs_commit(manifest["commit"])
    assert diff["core_evaluation_changed"] == [], (
        "Phát hiện thay đổi trong vùng lõi Geometry/AI/Semantic so với bản đóng băng "
        f"{manifest.get('commit_ngan')}: {diff['core_evaluation_changed']}. "
        "Mọi thay đổi lõi đánh giá bắt buộc quy trình đánh giá/benchmark và đóng băng mới."
    )

    hien_tai, so_file = fz.measured_system_hash()
    if hien_tai != manifest["measured_system"]["tree_hash"] or so_file != manifest["measured_system"]["so_file"]:
        # Xác nhận mọi file lệch đều nằm ngoài vùng lõi đánh giá (vd: tầng accounts)
        assert diff["all_diff"], "Hash lệch nhưng diff rỗng — bất nhất tính toán."
        # Strict `--verify` tuyệt đối không được trả PASS giả khi cây hiện tại khác candidate lịch sử
        strict_cmd = subprocess.run(
            [sys.executable, str(ROOT / "backend" / "scripts" / "freeze_evaluation_candidate.py"), "--verify"],
            cwd=ROOT, capture_output=True, text=True,
        )
        assert strict_cmd.returncode != 0, (
            "Strict --verify phải trả mã lỗi khác 0 khi mã sản phẩm hiện tại khác candidate lịch sử!"
        )


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
        "backend/app/ai/route_policy.py",
        "backend/app/ai/hybrid_offline.py",
        "backend/app/ai/typed_fact_next_extraction.py",
        "backend/app/ai/adapter4_route.py",
        "backend/app/ai/gemini.py",
        "backend/app/ai/skills/transcribe.md",
        "backend/app/simulation/geometry_functions/planner.py",
        "backend/app/simulation/geometry_functions/registry.py",
        "backend/app/simulation/geometry_functions/engine.py",
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
        # The manifest is UTF-8 Vietnamese text: decode explicitly, not with the console code page.
        shown = subprocess.run(["git", "-C", str(ROOT), "show", f"{v}:{rel}"], capture_output=True, encoding="utf-8")
        try:
            m = json.loads(shown.stdout)
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


# ── GATE A: HISTORICAL FREEZE VERIFICATION & NEGATIVE GUARDS (PHẦN V) ────────────────────────────────────────

_HISTORICAL_REPO_FILES = {
    "backend/app/accounts/router.py": "def login(): return 'v1'\n",
    "backend/app/simulation/geometry/kernel.py": "KERNEL = 1\n",
    "backend/app/ai/route_policy.py": "MODE = 'HYBRID'\n",
    "frontend/src/components/LandingView.tsx": "export const Landing = () => 'v1';\n",
    "frontend/src/simulations/domains/semantic/route.ts": "export const r = 1;\n",
    "frontend/src/simulations/domains/semantic/semantic_program.schema.json": '{"type":"object"}\n',
    "docs/schemas/semantic_program.schema.json": '{"schema":"v1"}\n',
    "docs/evaluation/semantic-benchmark/dev/cases.json": '{"cases":[{"id":"c1"},{"id":"c2"}]}\n',
}


def _make_historical_manifest(fz, root: Path, commit_sha: str, manifest_template: dict) -> dict:
    h, n = fz.measured_system_hash_at_commit(commit_sha)
    schema_text = (root / "docs/schemas/semantic_program.schema.json").read_text(encoding="utf-8")
    dev_bytes = fz.bam_noi_dung(root / "docs/evaluation/semantic-benchmark/dev/cases.json")
    return {
        **manifest_template,
        "commit": commit_sha,
        "commit_ngan": commit_sha[:9],
        "product_commit_sha": fz.product_commit(fz.PRODUCT_COMMIT_RULE, rev=commit_sha),
        "product_commit_rule": fz.PRODUCT_COMMIT_RULE,
        "cay_lam_viec_sach": True,
        "measured_system": {
            "paths": list(fz.MEASURED_SYSTEM_PATHS),
            "so_file": n,
            "tree_hash": h,
        },
        "schema_semantic_program": {
            "duong_dan": "docs/schemas/semantic_program.schema.json",
            "hash": fz._sha(schema_text),
        },
        "dev": {
            "duong_dan": "docs/evaluation/semantic-benchmark/dev/cases.json",
            "so_case": 2,
            "fingerprint": hashlib.sha256(dev_bytes).hexdigest(),
        },
    }


@pytest.fixture
def historical_repo(tmp_path, monkeypatch, manifest):
    """Throwaway Git repo có sẵn 1 commit lịch sử đã đóng băng + 1 commit manifest committed."""
    fz = _freeze_module()
    root = tmp_path / "hist_repo"
    root.mkdir()
    subprocess.run(["git", "init", "-q", str(root)], check=True)
    frozen_sha = _commit(root, dict(_HISTORICAL_REPO_FILES), "freeze base")
    monkeypatch.setattr(fz, "ROOT", root)
    cand_rel = "docs/evaluation/semantic-benchmark/EVALUATION_CANDIDATE.json"
    cand_path = root / cand_rel
    cand_data = _make_historical_manifest(fz, root, frozen_sha, manifest)
    _commit(root, {cand_rel: json.dumps(cand_data, ensure_ascii=False, indent=2) + "\n"}, "record candidate")
    monkeypatch.setattr(fz, "OUT", cand_path)
    return fz, root, frozen_sha, cand_path, cand_data


class TestHistoricalFreezeVerificationAndNegativeGuards:
    def test_valid_historical_candidate_passes_after_approved_landing_and_accounts_changes_while_strict_verify_fails(
        self, historical_repo, monkeypatch, tmp_path
    ):
        """§5.1 & §5.2: Thay đổi Landing + Accounts không làm hỏng --verify-historical, còn --verify strict vẫn báo lệch."""
        fz, root, frozen_sha, cand_path, cand_data = historical_repo

        # Commit thay đổi Landing & Admin accounts sau mốc đóng băng
        _commit(
            root,
            {
                "backend/app/accounts/router.py": "def login(): return 'v2-admin-username'\n",
                "frontend/src/components/LandingView.tsx": "export const Landing = () => 'v2-about';\n",
            },
            "feat: landing cutover and admin auth",
        )

        res = fz.verify_historical_candidate(cand_path)
        assert res["verdict"] == "PASS"
        assert res["exit_code"] == 0
        assert res["recorded_commit"] == frozen_sha
        assert res["actual_historical_tree_hash"] == cand_data["measured_system"]["tree_hash"]
        assert res["actual_historical_so_file"] == cand_data["measured_system"]["so_file"]
        assert res["provenance_matches_head"] is True

        # Core evaluation paths hoàn toàn nguyên vẹn; chỉ có backend/app/accounts/router.py đổi trong MEASURED_SYSTEM_PATHS
        diff = fz.diff_measured_system_vs_commit(frozen_sha)
        assert diff["core_evaluation_changed"] == []
        assert diff["changed"] == ["backend/app/accounts/router.py"]

        # Strict `--verify` PHẢI trả != 0 (không được ẩn sự khác biệt của current tree)
        current_built = _frozen(fz, cand_data)
        assert _verify(fz, monkeypatch, tmp_path, cand_data, current_built) == 1

    def test_altered_tree_hash_fails_historical_verification(self, historical_repo, tmp_path):
        fz, _, _, _, cand_data = historical_repo
        bad = {**cand_data, "measured_system": {**cand_data["measured_system"], "tree_hash": "f" * 64}}
        p = tmp_path / "bad_hash.json"
        p.write_text(json.dumps(bad), encoding="utf-8")
        res = fz.verify_historical_candidate(p, check_git_provenance=False)
        assert res["verdict"] == "FAIL"
        assert res["exit_code"] == 1
        assert "measured_system.tree_hash" in res["mismatches"]

    def test_altered_file_count_fails_historical_verification(self, historical_repo, tmp_path):
        fz, _, _, _, cand_data = historical_repo
        bad = {
            **cand_data,
            "measured_system": {**cand_data["measured_system"], "so_file": cand_data["measured_system"]["so_file"] + 1},
        }
        p = tmp_path / "bad_count.json"
        p.write_text(json.dumps(bad), encoding="utf-8")
        res = fz.verify_historical_candidate(p, check_git_provenance=False)
        assert res["verdict"] == "FAIL"
        assert res["exit_code"] == 1
        assert "measured_system.so_file" in res["mismatches"]

    def test_nonexistent_commit_fails_historical_verification(self, historical_repo, tmp_path):
        fz, _, _, _, cand_data = historical_repo
        missing_sha = "a" * 40
        bad = {**cand_data, "commit": missing_sha, "commit_ngan": missing_sha[:9]}
        p = tmp_path / "missing_commit.json"
        p.write_text(json.dumps(bad), encoding="utf-8")
        res = fz.verify_historical_candidate(p, check_git_provenance=False)
        assert res["verdict"] == "FAIL"
        assert res["exit_code"] == 2
        assert "commit_not_found" in res["mismatches"]

    @pytest.mark.parametrize(
        "corruptor",
        [
            "invalid_json",
            "dirty_tree_flag",
            "missing_measured_system",
            "short_commit_mismatch",
            "unknown_rule",
        ],
    )
    def test_invalid_metadata_fails_historical_verification(self, historical_repo, tmp_path, corruptor):
        fz, _, _, _, cand_data = historical_repo
        p = tmp_path / f"corrupt_{corruptor}.json"
        if corruptor == "invalid_json":
            p.write_text("{not valid json", encoding="utf-8")
        elif corruptor == "dirty_tree_flag":
            p.write_text(json.dumps({**cand_data, "cay_lam_viec_sach": False}), encoding="utf-8")
        elif corruptor == "missing_measured_system":
            d = dict(cand_data)
            d.pop("measured_system", None)
            p.write_text(json.dumps(d), encoding="utf-8")
        elif corruptor == "short_commit_mismatch":
            p.write_text(json.dumps({**cand_data, "commit_ngan": "deadbeef0"}), encoding="utf-8")
        else:
            p.write_text(json.dumps({**cand_data, "product_commit_rule": "unknown-rule/99"}), encoding="utf-8")

        res = fz.verify_historical_candidate(p, check_git_provenance=False)
        assert res["verdict"] == "FAIL"
        assert res["exit_code"] != 0

    def test_simultaneous_commit_and_hash_tampering_caught_by_git_head_provenance(self, historical_repo):
        """§3.3 & §5.1: Sửa ĐỒNG THỜI cả commit lẫn tree_hash trong file tracked trên working tree vẫn bị phát hiện."""
        fz, root, _, cand_path, cand_data = historical_repo

        # Tạo một commit thứ hai hợp lệ rồi ghi đè file candidate bằng cả commit lẫn hash mới (tự nhất quán nhưng giả mạo working tree)
        second_sha = _commit(root, {"backend/app/accounts/router.py": "def login(): return 'tampered'\n"}, "later")
        forged = _make_historical_manifest(fz, root, second_sha, cand_data)
        cand_path.write_text(json.dumps(forged, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

        # Nếu bỏ qua provenance thì file giả mạo tự khớp commit second_sha, NHƯNG với provenance mặc định PHẢI FAIL!
        res = fz.verify_historical_candidate(cand_path, check_git_provenance=True)
        assert res["verdict"] == "FAIL"
        assert res["exit_code"] == 1
        assert res["provenance_checked"] is True
        assert res["provenance_matches_head"] is False
        assert "manifest_modified_vs_head" in res["mismatches"]

    def test_unreadable_git_object_fails_clearly(self, historical_repo, monkeypatch):
        fz, _, _, cand_path, _ = historical_repo

        def _boom(*args):
            raise fz.HistoricalVerificationError("git_object_unreadable", "simulated corrupt pack")

        monkeypatch.setattr(fz, "_git_bytes", _boom)
        res = fz.verify_historical_candidate(cand_path, check_git_provenance=False)
        assert res["verdict"] == "FAIL"
        assert res["exit_code"] == 2
        assert "git_object_unreadable" in res["mismatches"]

    def test_core_geometry_or_ai_modification_detected_by_core_preservation_guard(self, historical_repo):
        """§5.2: Mọi sửa đổi trong backend/app/simulation/ hoặc backend/app/ai/ phải bị phát hiện."""
        fz, root, frozen_sha, _, _ = historical_repo
        (root / "backend/app/simulation/geometry/kernel.py").write_text("KERNEL = 999\n", encoding="utf-8")
        (root / "backend/app/ai/route_policy.py").write_text("MODE = 'TAMPERED'\n", encoding="utf-8")

        diff = fz.diff_measured_system_vs_commit(frozen_sha)
        assert "backend/app/simulation/geometry/kernel.py" in diff["core_evaluation_changed"]
        assert "backend/app/ai/route_policy.py" in diff["core_evaluation_changed"]

    def test_mutually_exclusive_cli_flags_rejected(self, historical_repo, monkeypatch):
        fz, _, _, _, _ = historical_repo
        monkeypatch.setattr(fz.sys, "argv", ["freeze", "--verify", "--verify-historical"])
        assert fz.main() == 2

    def test_nested_git_worktree_compatibility_without_mutating_working_tree(self, historical_repo, tmp_path):
        """§5.3: --verify-historical hoạt động chính xác từ một Git worktree lồng sâu nhiều cấp."""
        fz, root, frozen_sha, _, cand_data = historical_repo
        nested_wt = tmp_path / "deep" / "nested" / "wt-check"
        nested_wt.parent.mkdir(parents=True, exist_ok=True)
        subprocess.run(
            ["git", "-C", str(root), "worktree", "add", "--detach", str(nested_wt), "HEAD"],
            check=True, capture_output=True, text=True,
        )
        try:
            # Sửa file không thuộc lõi trong nested worktree -> working tree bẩn nhưng historical verification vẫn PASS!
            (nested_wt / "backend/app/accounts/router.py").write_text("def login(): return 'wt-edit'\n", encoding="utf-8")
            wt_cand = nested_wt / "docs/evaluation/semantic-benchmark/EVALUATION_CANDIDATE.json"
            old_root, old_out = fz.ROOT, fz.OUT
            fz.ROOT = nested_wt
            fz.OUT = wt_cand
            try:
                res = fz.verify_historical_candidate()
                assert res["verdict"] == "PASS", res
                assert res["recorded_commit"] == frozen_sha
                assert res["actual_historical_tree_hash"] == cand_data["measured_system"]["tree_hash"]
                assert res["provenance_matches_head"] is True
                # Working tree trong nested worktree không bị checkout đè
                assert (nested_wt / "backend/app/accounts/router.py").read_text(encoding="utf-8") == "def login(): return 'wt-edit'\n"
            finally:
                fz.ROOT, fz.OUT = old_root, old_out
        finally:
            subprocess.run(
                ["git", "-C", str(root), "worktree", "remove", "--force", str(nested_wt)],
                check=False, capture_output=True,
            )


class TestIntegratedCandidateLineageAndIsolation:
    """Phase 12 — Kiểm chứng bảo toàn lịch sử 4978ac01f, danh tính integrated candidate mới,
    cách ly approval/template PENDING, chống fallback ngầm và từ chối giả mạo."""

    PRIOR_ARCHIVE = (
        ROOT
        / "docs"
        / "evaluation"
        / "geometry"
        / "runs"
        / "integrated-security-release"
        / "prior-EVALUATION_CANDIDATE-4978ac01f.json"
    )
    RUN_LOGS = (
        ROOT
        / "docs"
        / "evaluation"
        / "geometry"
        / "runs"
        / "integrated-security-release"
        / "logs"
    )

    def test_preserved_historical_4978ac01f_archive_is_byte_identical_and_verifies(self, tmp_path):
        fz = _freeze_module()
        expected_bytes = subprocess.check_output(
            ["git", "-C", str(ROOT), "show", "f2cc62b1e:docs/evaluation/semantic-benchmark/EVALUATION_CANDIDATE.json"]
        )
        assert self.PRIOR_ARCHIVE.is_file()
        assert self.PRIOR_ARCHIVE.read_bytes().replace(b"\r\n", b"\n") == expected_bytes

        res = fz.verify_historical_candidate(self.PRIOR_ARCHIVE, check_git_provenance=True)
        assert res["verdict"] == "PASS", res
        assert res["recorded_commit"] == "4978ac01f3240d08ae259d532edcc83c2c5af5e4"
        assert res["actual_historical_tree_hash"] == "7bd85b6e2c8719e4fb6192e362ce17505588081623c90514dda0a83e88b4dd04"
        assert res["actual_historical_so_file"] == 127
        assert res["provenance_matches_head"] is True

        # Bản lưu lịch sử bị chỉnh sửa dù chỉ 1 trường phải FAIL
        orig = json.loads(self.PRIOR_ARCHIVE.read_text(encoding="utf-8"))
        tampered = tmp_path / "tampered-4978.json"
        tampered.write_text(
            json.dumps({**orig, "measured_system": {**orig["measured_system"], "tree_hash": "0" * 64}}),
            encoding="utf-8",
        )
        bad_res = fz.verify_historical_candidate(tampered, check_git_provenance=False)
        assert bad_res["verdict"] == "FAIL"
        assert "measured_system.tree_hash" in bad_res["mismatches"]

    def test_integrated_candidate_has_distinct_identity_clean_tree_and_core_unchanged(self, manifest):
        fz = _freeze_module()
        prior = json.loads(self.PRIOR_ARCHIVE.read_text(encoding="utf-8"))
        assert manifest["commit"] != prior["commit"]
        assert manifest["measured_system"]["tree_hash"] != prior["measured_system"]["tree_hash"]
        assert manifest["cay_lam_viec_sach"] is True
        assert manifest["cache_version"] == CACHE_VERSION == "158"

        diff = fz.diff_measured_system_vs_commit(prior["commit"])
        assert diff["core_evaluation_changed"] == []

        res = fz.verify_historical_candidate(CANDIDATE, check_git_provenance=True)
        assert res["verdict"] == "PASS", res
        assert res["provenance_matches_head"] is True

    def test_historical_approval_and_pending_or_forged_templates_refused_on_integrated_runtime(self, monkeypatch):
        from scripts import run_s2_student_language_pilot as R

        specs = R.default_c21_pilot_specs()
        k1_corpus = Path(specs["K-1"]["corpus_path"]).read_bytes().replace(b"\r\n", b"\n")
        k1_template_path = Path(specs["K-1"]["template_path"])

        # 1. Approval mang measured_system lịch sử 4978ac01f phải bị từ chối trên integrated runtime
        prior_k1 = json.loads((self.RUN_LOGS / "prior-k1-owner-approval.template.json").read_text(encoding="utf-8"))
        assert prior_k1["measured_system"] == "7bd85b6e2c8719e4fb6192e362ce17505588081623c90514dda0a83e88b4dd04"
        forged_hist_approved = {k: v for k, v in prior_k1.items() if k != "owner_decision"} | {
            "owner_decision": "APPROVED_BY_USER",
            "paid_project_confirmed": True,
        }
        with pytest.raises(R.LiveRefused, match="measured_system"):
            R.check_approval_terms(k1_corpus, forged_hist_approved)

        # 2. Bản template PENDING hiện hành không bao giờ chạy được live ngay cả khi có ALLOW_LIVE_AI=1
        monkeypatch.setenv("ALLOW_LIVE_AI", "1")
        monkeypatch.setenv("GEMINI_API_KEY", "test-offline-guard-placeholder-not-a-key")
        with pytest.raises(R.LiveRefused, match="neither APPROVED_BY_USER"):
            R.authorize_live(Path(specs["K-1"]["corpus_path"]), k1_template_path)

        cur_k1 = json.loads(k1_template_path.read_text(encoding="utf-8"))
        assert cur_k1["owner_decision"] == "PENDING_OWNER_DECISION" and cur_k1["paid_project_confirmed"] is False
        with pytest.raises(R.LiveRefused, match="paid project"):
            R.check_approval_terms(k1_corpus, cur_k1)

        # 3. Các dạng giả mạo model / budget / corpus bị từ chối rõ ràng
        valid_shape = {k: v for k, v in cur_k1.items() if k != "owner_decision"} | {"paid_project_confirmed": True}
        for bad_patch, err_match in (
            ({"model": "gemini-9.9-fake"}, "model"),
            ({"max_requests": 999}, "max_requests"),
            ({"max_usd": -1.0}, "max_usd"),
            ({"max_usd": 0.001}, "exceeds max_usd"),
            ({"corpus_sha256": "0" * 64}, "corpus hash"),
        ):
            with pytest.raises(R.LiveRefused, match=err_match):
                R.check_approval_terms(k1_corpus, {**valid_shape, **bad_patch})

    def test_cache_identity_lock_detects_tampered_hash_in_isolation(self, tmp_path):
        import importlib.util

        lock_script = ROOT / "backend" / "scripts" / "lock_cache_identity.py"
        spec = importlib.util.spec_from_file_location("lock_cache_identity", lock_script)
        lock_mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(lock_mod)

        real_lock = json.loads(lock_mod.KHOA.read_text(encoding="utf-8"))
        assert real_lock["cache_version"] == CACHE_VERSION == "158"
        tampered = tmp_path / "tampered.lock.json"
        tampered.write_text(
            json.dumps({**real_lock, "semantic_environment_hash": "f" * 64}),
            encoding="utf-8",
        )
        old_lock_file = lock_mod.KHOA
        lock_mod.KHOA = tampered
        try:
            old_argv = list(sys.argv)
            sys.argv = ["lock_cache_identity.py", "--verify"]
            try:
                assert lock_mod.main() == 1
            finally:
                sys.argv = old_argv
        finally:
            lock_mod.KHOA = old_lock_file

