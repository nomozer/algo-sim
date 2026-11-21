# -*- coding: utf-8 -*-
"""Đóng băng EVALUATION CANDIDATE — danh tính của hệ tại thời điểm sắp đo.

VÌ SAO PHẢI CÓ: SEALED chỉ có nghĩa khi biết **đo bản nào**. Không có mốc này
thì sau khi thấy số, mọi câu "à lúc đó taxonomy còn khác" đều không kiểm chứng
được — và đó chính là cách một benchmark mất giá trị mà không ai nhận ra.

MỌI GIÁ TRỊ DẪN XUẤT TỪ NGUỒN, không chép tay: taxonomy và tập primitive băm
thẳng từ module Python, `CACHE_VERSION` đọc từ `app.main`, schema băm từ file đã
sinh. Chép tay thì manifest trôi khỏi mã đúng như bảng danh tính trong
`CURRENT_STATE.md` từng trôi.

LUẬT SAU KHI CHẠY (spec §7.4): **không sửa candidate vì kết quả SEALED.**
DEV được phép làm thay đổi hệ; SEALED chỉ được phép làm thay đổi KẾT LUẬN.

    python scripts/freeze_evaluation_candidate.py                    # ghi manifest
    python scripts/freeze_evaluation_candidate.py --verify           # so strict current HEAD/working tree vs manifest
    python scripts/freeze_evaluation_candidate.py --verify-historical # kiểm chứng snapshot lịch sử tại đúng Git commit ghi trong manifest
"""
from __future__ import annotations

import hashlib
import json
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if sys.stderr and hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

ROOT = Path(__file__).resolve().parents[2]
BENCH = ROOT / "docs" / "evaluation" / "semantic-benchmark"
OUT = BENCH / "EVALUATION_CANDIDATE.json"

sys.path.insert(0, str(ROOT / "backend"))

#: HỆ ĐƯỢC ĐO — tập đường dẫn mã SẢN PHẨM cấu thành nó.
#:
#: VÌ SAO CẦN (thêm 2026-08-22): năm fingerprint cũ (taxonomy · primitive ·
#: schema · DEV · CACHE_VERSION) **không đủ** để chứng minh "hệ được đo vẫn là
#: bản đã đóng băng". Sửa `pipeline.py`, `route.py`, interpreter, validator,
#: grounding/C₁a/C₁b/C₂ hay bất kỳ checker nào mà không đụng năm thứ kia thì
#: `--verify` vẫn XANH trong khi ngữ nghĩa hệ đã đổi — đúng loại lỗ mà sự cố
#: "route chưa từng được nối" đã cho thấy là có thật.
#:
#: Ranh giới chọn theo NGUYÊN TẮC, không theo phán đoán từng file: mọi thứ
#: trong `backend/app` là mã sản phẩm; `scripts/`, `tests/`, `docs/` là bộ đo.
#: Nhờ vậy harness được phép cứng cáp thêm mà candidate không phải đóng băng
#: lại, còn một dòng mã sản phẩm đổi là ĐỎ ngay.
MEASURED_SYSTEM_PATHS = (
    "backend/app",
    # Module 2D của route — thuộc bề mặt hợp đồng, không phải bộ đo.
    "frontend/src/simulations/domains/semantic",
    "frontend/src/simulations/domains/semantic/semantic_program.schema.json",
)

_BO_QUA = ("__pycache__", ".pyc", ".pyo")

#: DANH TÍNH SẢN PHẨM (`product_commit_sha`) — commit cuối chạm mã sản phẩm, KỂ CẢ renderer ngoài
#: MEASURED_SYSTEM_PATHS: sửa renderer không đổi `tree_hash` nhưng phải làm --verify đỏ (sự cố W12).
PRODUCT_PATHS = ("backend/app", "frontend/src")
#: Bộ đo NẰM TRONG cây sản phẩm. Chỉ đổi chúng thì sản phẩm được đo không đổi ⇒ không buộc đóng băng lại.
#: Phân loại theo tên; `test_I2_test_only_files_are_never_imported_by_product_code` giữ nó trung thực.
TEST_ONLY_GLOBS = (
    "frontend/src/**/*.test.ts",
    "frontend/src/**/*.test.tsx",
    "frontend/src/**/*fixture*.json",
    "frontend/src/test-setup.ts",
    "frontend/src/test-source.ts",
)
#: Tên luật GHI VÀO manifest. Manifest không có tên luật (mọi bản trước review I2, 2026-10-11) được kiểm bằng
#: luật cũ — `PRODUCT_PATHS` không loại gì — nên không định danh lịch sử nào đổi.
PRODUCT_COMMIT_RULE = "product-paths-excluding-test-only/1"


def product_commit(rule: str | None = PRODUCT_COMMIT_RULE, rev: str = "HEAD") -> str:
    """Commit cuối chạm sản phẩm tại `rev` theo `rule` (None = luật cũ). Luật lạ ⇒ ValueError."""
    if rule not in (None, PRODUCT_COMMIT_RULE):
        raise ValueError(f"luật danh tính sản phẩm không biết: {rule!r}")
    loai = [] if rule is None else [f":(exclude,glob){g}" for g in TEST_ONLY_GLOBS]
    return _git("log", "-1", "--format=%H", rev, "--", *PRODUCT_PATHS, *loai)


def _sha(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def bam_noi_dung(p: Path) -> bytes:
    """Băm NỘI DUNG một file, không băm cách nó được lưu.

    ⚠️ BẮT BUỘC CHUẨN HOÁ CRLF → LF, và đây không phải tinh chỉnh cho gọn.
    Đo được 2026-08-24: `docs/evaluation/semantic-benchmark/dev/cases.json` có
    **283 dòng CRLF** trên đĩa Windows trong khi git lưu bản LF. Hai bản băm ra
    hai giá trị khác nhau (`c5c8dd81` ↔ `8a3de7a3`) dù **không một ký tự nội
    dung nào đổi** — git chỉ vừa chuyển đổi lúc checkout.

    Hệ quả nếu không chuẩn hoá: clone lại kho trên máy khác cho fingerprint
    khác, và cổng đóng băng báo *"hệ được đo đã trôi"* trong khi không ai đụng
    vào. Với một cơ chế mà toàn bộ giá trị nằm ở chỗ **tái lập được**, đó là
    lỗi làm nó vô nghĩa.

    Giá trị LF là giá trị ĐÚNG: nó khớp thứ git lưu, nên mọi manifest đã ghi
    trước đây (`8a3de7a3`, `2ea8a3d0`…) **vẫn khớp** sau bản vá. Không phải
    viết lại lịch sử.

    File nhị phân có chuỗi `\\r\\n` sẽ bị đổi băm — nhưng đổi **tất định**, nên
    tính tái lập vẫn giữ. `MEASURED_SYSTEM_PATHS` hiện chỉ gồm `.py`, `.ts`,
    `.tsx`, `.json`, không có nhị phân nào.
    """
    return p.read_bytes().replace(b"\r\n", b"\n")


def _measured_system_files() -> list[Path]:
    ra: list[Path] = []
    for muc in MEASURED_SYSTEM_PATHS:
        p = ROOT / muc
        if p.is_file():
            ra.append(p)
        elif p.is_dir():
            ra.extend(
                f for f in p.rglob("*")
                if f.is_file() and not any(b in str(f) for b in _BO_QUA)
            )
    return sorted(ra)


def measured_system_hash() -> tuple[str, int]:
    """Băm NỘI DUNG mã sản phẩm — không dựa vào git, để chạy được cả trên cây bẩn.

    Trả `(hash, số file)`. Số file khai riêng vì thêm/xoá file là kiểu trôi mà
    người đọc nhận ra ngay, còn hash thì không nói được gì ngoài "khác".
    """
    h = hashlib.sha256()
    files = _measured_system_files()
    for f in files:
        h.update(f.relative_to(ROOT).as_posix().encode("utf-8"))
        h.update(b"\0")
        h.update(hashlib.sha256(bam_noi_dung(f)).digest())
    return h.hexdigest(), len(files)


#: Vùng lõi mô phỏng / AI / ngữ nghĩa — mọi chỉnh sửa trong các tiền tố này
#: so với bản đóng băng lịch sử làm mất hiệu lực tái sử dụng giả định không đổi
#: đối với lõi đánh giá và bắt buộc quy trình đánh giá/benchmark mới.
CORE_EVALUATION_PROTECTED_PREFIXES = (
    "backend/app/simulation/",
    "backend/app/ai/",
    "frontend/src/simulations/domains/semantic/",
)

_HEX40_RE = re.compile(r"^[0-9a-f]{40}$")
_HEX64_RE = re.compile(r"^[0-9a-f]{64}$")

SCOPE_DISCLAIMER_HISTORICAL = (
    "Verifies historical freeze snapshot integrity at its recorded Git commit only; "
    "does NOT assert that current HEAD/working tree matches the frozen candidate or "
    "inherits its benchmark measurements."
)
PROVENANCE_LIMITATION_TEXT = (
    "Git HEAD provenance verifies the candidate manifest in the working tree matches "
    "committed Git HEAD bytes (catching uncommitted simultaneous commit+hash rewrites). "
    "Defending against an actor authorized to rewrite committed Git history requires "
    "signed commits or external immutable attestation."
)


class HistoricalVerificationError(RuntimeError):
    """Lỗi khi truy xuất hoặc kiểm chứng bản đóng băng lịch sử từ Git object database."""

    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code


def _git_run(*args: str, text: bool = False) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["git", *args],
        cwd=ROOT,
        capture_output=True,
        text=text,
        encoding="utf-8" if text else None,
        errors="replace" if text else None,
    )


def _git_bytes(*args: str) -> bytes:
    res = _git_run(*args, text=False)
    if res.returncode != 0:
        err = (res.stderr or b"").decode("utf-8", errors="replace").strip()
        raise HistoricalVerificationError(
            "git_object_unreadable",
            f"Không đọc được Git object (`git {' '.join(args)}`): {err or f'exit={res.returncode}'}",
        )
    return res.stdout


def measured_system_hash_at_commit(
    rev: str,
    paths: tuple[str, ...] | list[str] = MEASURED_SYSTEM_PATHS,
) -> tuple[str, int]:
    """Băm NỘI DUNG các tệp đo đạc trực tiếp từ Git tree tại commit `rev`.

    Không checkout, không ghi working tree, không tạo worktree phụ; dùng chính
    quy tắc lọc `_BO_QUA`, sắp xếp thứ tự và chuẩn hóa CRLF → LF của freeze protocol.
    """
    if not rev or not isinstance(rev, str):
        raise HistoricalVerificationError("invalid_commit_ref", "Thiếu commit nguồn hợp lệ.")
    t_res = _git_run("cat-file", "-t", rev, text=True)
    if t_res.returncode != 0 or t_res.stdout.strip() != "commit":
        raise HistoricalVerificationError(
            "commit_not_found",
            f"Commit nguồn '{rev}' không tồn tại trong Git object database.",
        )
    if not paths:
        raise HistoricalVerificationError("invalid_measured_paths", "Danh sách measured_system.paths rỗng.")

    files: list[str] = []
    for muc in paths:
        ls_res = _git_run("ls-tree", "-r", "--name-only", rev, "--", muc, text=True)
        if ls_res.returncode != 0:
            raise HistoricalVerificationError(
                "git_tree_unreadable",
                f"Không đọc được Git tree tại '{rev}' cho đường dẫn '{muc}': {ls_res.stderr.strip()}",
            )
        for line in ls_res.stdout.splitlines():
            rel = line.strip()
            if rel and not any(b in rel for b in _BO_QUA):
                files.append(rel)

    files.sort()
    if not files:
        raise HistoricalVerificationError(
            "git_tree_empty",
            f"Không tìm thấy tệp đo đạc nào tại commit '{rev}'.",
        )

    h = hashlib.sha256()
    for rel in files:
        raw = _git_bytes("show", f"{rev}:{rel}").replace(b"\r\n", b"\n")
        h.update(rel.encode("utf-8"))
        h.update(b"\0")
        h.update(hashlib.sha256(raw).digest())
    return h.hexdigest(), len(files)


def diff_measured_system_vs_commit(
    rev: str,
    paths: tuple[str, ...] | list[str] = MEASURED_SYSTEM_PATHS,
) -> dict[str, list[str]]:
    """Liệt kê chính xác các file khác biệt trong `paths` giữa working tree hiện tại và commit `rev`.

    Phân tách rõ thay đổi trong vùng lõi đánh giá (`CORE_EVALUATION_PROTECTED_PREFIXES`)
    với các tầng sản phẩm ngoài vùng đánh giá (vd: `backend/app/accounts/`).
    """
    hist_files: set[str] = set()
    for muc in paths:
        ls_res = _git_run("ls-tree", "-r", "--name-only", rev, "--", muc, text=True)
        if ls_res.returncode != 0:
            raise HistoricalVerificationError(
                "git_tree_unreadable",
                f"Không đọc được Git tree tại '{rev}' cho '{muc}': {ls_res.stderr.strip()}",
            )
        for line in ls_res.stdout.splitlines():
            rel = line.strip()
            if rel and not any(b in rel for b in _BO_QUA):
                hist_files.add(rel)

    curr_map: dict[str, Path] = {}
    for muc in paths:
        p = ROOT / muc
        if p.is_file():
            rel = p.relative_to(ROOT).as_posix()
            if not any(b in rel for b in _BO_QUA):
                curr_map[rel] = p
        elif p.is_dir():
            for f in p.rglob("*"):
                if f.is_file() and not any(b in str(f) for b in _BO_QUA):
                    curr_map[f.relative_to(ROOT).as_posix()] = f

    curr_files = set(curr_map.keys())
    added = sorted(curr_files - hist_files)
    removed = sorted(hist_files - curr_files)
    changed: list[str] = []
    for rel in sorted(curr_files & hist_files):
        hist_bytes = _git_bytes("show", f"{rev}:{rel}").replace(b"\r\n", b"\n")
        curr_bytes = bam_noi_dung(curr_map[rel])
        if curr_bytes != hist_bytes:
            changed.append(rel)

    all_diff = sorted(set(added) | set(removed) | set(changed))
    core_changed = [
        rel for rel in all_diff
        if any(rel.startswith(prefix) for prefix in CORE_EVALUATION_PROTECTED_PREFIXES)
    ]
    return {
        "changed": changed,
        "added": added,
        "removed": removed,
        "all_diff": all_diff,
        "core_evaluation_changed": core_changed,
    }


def verify_historical_candidate(
    manifest_path: Path | None = None,
    *,
    check_git_provenance: bool = True,
) -> dict:
    """Kiểm chứng toàn vẹn bản đóng băng lịch sử trực tiếp trên Git tree nguồn.

    Không checkout/ghi working tree, không làm suy yếu `--verify` cho current tree.
    """
    target = manifest_path or OUT
    result: dict = {
        "mode": "verify-historical",
        "verdict": "FAIL",
        "exit_code": 2,
        "scope_disclaimer": SCOPE_DISCLAIMER_HISTORICAL,
        "provenance_limitation": PROVENANCE_LIMITATION_TEXT,
        "manifest_path": str(target),
        "manifest_sha256": None,
        "recorded_commit": None,
        "recorded_product_commit_sha": None,
        "product_commit_rule": None,
        "expected_tree_hash": None,
        "actual_historical_tree_hash": None,
        "expected_so_file": None,
        "actual_historical_so_file": None,
        "provenance_checked": False,
        "provenance_matches_head": None,
        "checks": {},
        "mismatches": [],
        "error": None,
    }

    if not target.is_file():
        result["error"] = "manifest_missing"
        result["mismatches"].append("manifest_missing")
        return result

    raw_manifest = bam_noi_dung(target)
    result["manifest_sha256"] = hashlib.sha256(raw_manifest).hexdigest()
    try:
        cu = json.loads(raw_manifest.decode("utf-8"))
    except Exception as exc:
        result["error"] = f"manifest_json_invalid: {exc}"
        result["mismatches"].append("manifest_json_invalid")
        return result

    if not isinstance(cu, dict):
        result["error"] = "manifest_not_object"
        result["mismatches"].append("manifest_not_object")
        return result

    commit = cu.get("commit")
    commit_short = cu.get("commit_ngan")
    ms = cu.get("measured_system")
    result["recorded_commit"] = commit
    result["recorded_product_commit_sha"] = cu.get("product_commit_sha")
    result["product_commit_rule"] = cu.get("product_commit_rule")

    # 1. Xác thực cấu trúc metadata bắt buộc
    meta_ok = (
        isinstance(commit, str)
        and bool(_HEX40_RE.match(commit))
        and (commit_short is None or (isinstance(commit_short, str) and commit.startswith(commit_short)))
        and cu.get("cay_lam_viec_sach") is True
        and isinstance(ms, dict)
        and isinstance(ms.get("paths"), list)
        and len(ms.get("paths")) > 0
        and all(isinstance(p, str) and bool(p.strip()) for p in ms.get("paths"))
        and isinstance(ms.get("tree_hash"), str)
        and bool(_HEX64_RE.match(ms.get("tree_hash")))
        and isinstance(ms.get("so_file"), int)
        and ms.get("so_file") > 0
        and bool(cu.get("cache_version"))
        and bool(cu.get("spec_version_ir"))
    )
    result["checks"]["metadata_valid"] = meta_ok
    if not meta_ok:
        result["error"] = "invalid_manifest_metadata"
        result["mismatches"].append("invalid_manifest_metadata")
        return result

    expected_hash = ms["tree_hash"]
    expected_files = ms["so_file"]
    paths = ms["paths"]
    result["expected_tree_hash"] = expected_hash
    result["expected_so_file"] = expected_files

    # 2. Kiểm tra provenance độc lập trong Git HEAD nếu manifest được track trong kho
    if check_git_provenance:
        try:
            rel_manifest = target.resolve().relative_to(ROOT.resolve()).as_posix()
        except ValueError:
            rel_manifest = None
        if rel_manifest:
            tracked = _git_run("ls-files", "--error-unmatch", rel_manifest, text=True)
            if tracked.returncode == 0:
                result["provenance_checked"] = True
                head_res = _git_run("show", f"HEAD:{rel_manifest}", text=False)
                if head_res.returncode == 0:
                    head_norm = head_res.stdout.replace(b"\r\n", b"\n")
                    matches_head = raw_manifest == head_norm
                    result["provenance_matches_head"] = matches_head
                    result["checks"]["git_head_provenance"] = matches_head
                    if not matches_head:
                        result["mismatches"].append("manifest_modified_vs_head")
                else:
                    result["provenance_matches_head"] = False
                    result["checks"]["git_head_provenance"] = False
                    result["mismatches"].append("git_head_manifest_unreadable")

    # 3. Truy xuất & băm lại measured_system trực tiếp từ Git tree của commit nguồn
    try:
        actual_hash, actual_files = measured_system_hash_at_commit(commit, paths)
    except HistoricalVerificationError as exc:
        result["checks"]["commit_exists"] = exc.code != "commit_not_found"
        result["error"] = f"{exc.code}: {exc}"
        result["mismatches"].append(exc.code)
        result["exit_code"] = 2 if exc.code in ("commit_not_found", "git_object_unreadable", "git_tree_unreadable") else 1
        return result

    result["checks"]["commit_exists"] = True
    result["actual_historical_tree_hash"] = actual_hash
    result["actual_historical_so_file"] = actual_files

    hash_ok = actual_hash == expected_hash
    files_ok = actual_files == expected_files
    result["checks"]["measured_tree_hash"] = hash_ok
    result["checks"]["measured_so_file"] = files_ok
    if not hash_ok:
        result["mismatches"].append("measured_system.tree_hash")
    if not files_ok:
        result["mismatches"].append("measured_system.so_file")

    # 4. Đối chiếu product_commit_sha theo đúng rule lịch sử tại commit nguồn
    if cu.get("product_commit_sha") is not None:
        try:
            derived_pc = product_commit(cu.get("product_commit_rule"), rev=commit)
            pc_ok = derived_pc == cu["product_commit_sha"]
        except ValueError as exc:
            pc_ok = False
            result["error"] = str(exc)
        result["checks"]["product_commit_sha"] = pc_ok
        if not pc_ok:
            result["mismatches"].append("product_commit_sha")

    # 5. Đối chiếu schema_semantic_program và dev/cases.json tại đúng commit lịch sử
    schema_info = cu.get("schema_semantic_program")
    if isinstance(schema_info, dict) and schema_info.get("duong_dan") and schema_info.get("hash"):
        try:
            schema_bytes = _git_bytes("show", f"{commit}:{schema_info['duong_dan']}")
            schema_text = schema_bytes.replace(b"\r\n", b"\n").decode("utf-8")
            schema_ok = _sha(schema_text) == schema_info["hash"]
        except HistoricalVerificationError as exc:
            schema_ok = False
            result["error"] = f"{exc.code}: {exc}"
            result["mismatches"].append(exc.code)
        result["checks"]["schema_hash"] = schema_ok
        if not schema_ok and "schema_semantic_program.hash" not in result["mismatches"]:
            result["mismatches"].append("schema_semantic_program.hash")

    dev_info = cu.get("dev")
    if isinstance(dev_info, dict) and dev_info.get("duong_dan") and dev_info.get("fingerprint"):
        try:
            dev_bytes = _git_bytes("show", f"{commit}:{dev_info['duong_dan']}").replace(b"\r\n", b"\n")
            dev_fp_ok = hashlib.sha256(dev_bytes).hexdigest() == dev_info["fingerprint"]
            dev_cases = json.loads(dev_bytes.decode("utf-8")).get("cases", [])
            dev_count_ok = (dev_info.get("so_case") is None) or (len(dev_cases) == dev_info.get("so_case"))
        except (HistoricalVerificationError, json.JSONDecodeError) as exc:
            dev_fp_ok = False
            dev_count_ok = False
            result["error"] = str(exc)
        result["checks"]["dev_fingerprint"] = dev_fp_ok
        result["checks"]["dev_case_count"] = dev_count_ok
        if not dev_fp_ok:
            result["mismatches"].append("dev.fingerprint")
        if not dev_count_ok:
            result["mismatches"].append("dev.so_case")

    if not result["mismatches"]:
        result["verdict"] = "PASS"
        result["exit_code"] = 0
    else:
        result["verdict"] = "FAIL"
        result["exit_code"] = 1
    return result


def _git(*args: str) -> str:
    return subprocess.run(
        ["git", *args], cwd=ROOT, capture_output=True, text=True
    ).stdout.strip()


def build() -> dict:
    from app.main import CACHE_VERSION
    from app.simulation.semantic_program.contract import (
        SPEC_VERSION,
        VisualContainerBinding,
    )
    from app.simulation.semantic_program.obligations import (
        AGGREGATE_OPS,
        OBLIGATION_KINDS,
        SEQUENCE_TRANSFORMS,
    )
    from app.simulation.semantic_program.postconditions import CHECKERS
    import typing

    taxonomy = {k: sorted(v) for k, v in sorted(OBLIGATION_KINDS.items())}
    primitives = sorted(
        typing.get_args(VisualContainerBinding.model_fields["primitive"].annotation)
    )
    schema_path = ROOT / "docs" / "schemas" / "semantic_program.schema.json"
    dev_path = BENCH / "dev" / "cases.json"

    return {
        "khai": (
            "Danh tính của hệ tại thời điểm ĐÓNG BĂNG để đánh giá. Không sửa file "
            "này vì kết quả SEALED — SEALED chỉ được phép làm thay đổi KẾT LUẬN."
        ),
        "dong_bang_luc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "commit": _git("rev-parse", "HEAD"),
        "commit_ngan": _git("rev-parse", "--short", "HEAD"),
        # Tách commit cuối thật sự đổi product khỏi HEAD tại lúc đóng băng (renderer tính, test/fixture không).
        "product_commit_sha": product_commit(),
        "product_commit_rule": PRODUCT_COMMIT_RULE,
        # Cây phải SẠCH thì `commit` ở trên mới thật sự định danh được bản đang
        # đo. Loại trừ đúng một file: chính manifest này, vì nó được sinh ra
        # trong lúc kiểm — con gà và quả trứng, không phải sự trôi.
        # Bỏ qua favicon.svg: thay đổi xoá file của người dùng được bảo tồn.
        # Bỏ qua chính freeze_evaluation_candidate.py nếu đang chạy.
        "cay_lam_viec_sach": all(
            "EVALUATION_CANDIDATE.json" in d or "favicon.svg" in d or "freeze_evaluation_candidate.py" in d
            for d in _git("status", "--porcelain").splitlines()
            if d.strip()
        ),
        "cache_version": CACHE_VERSION,
        "spec_version_ir": SPEC_VERSION,
        # Cái này mới làm câu "hệ được đo = <commit>" thành mệnh đề MÁY KIỂM
        # ĐƯỢC. Năm fingerprint dưới đây chỉ khoá HỢP ĐỒNG; cái này khoá MÃ.
        "measured_system": {
            "paths": list(MEASURED_SYSTEM_PATHS),
            "so_file": measured_system_hash()[1],
            "tree_hash": measured_system_hash()[0],
            "khai": (
                "Băm nội dung toàn bộ mã SẢN PHẨM của hệ được đo. Harness "
                "(scripts/tests/docs) KHÔNG nằm trong đây, nên bộ đo được phép "
                "cứng cáp thêm mà không phải đóng băng lại candidate."
            ),
        },
        "taxonomy": {
            "so_nghia_vu": len(taxonomy),
            "kinds": sorted(taxonomy),
            "aggregate_ops": sorted(AGGREGATE_OPS),
            "sequence_transforms": sorted(SEQUENCE_TRANSFORMS),
            "co_checker_server_owned": sorted(CHECKERS),
            "hash": _sha(json.dumps(taxonomy, ensure_ascii=False, sort_keys=True)),
        },
        "visual_primitive_set": {
            "so_primitive": len(primitives),
            "primitives": primitives,
            "hash": _sha(json.dumps(primitives, ensure_ascii=False)),
        },
        "schema_semantic_program": {
            "duong_dan": "docs/schemas/semantic_program.schema.json",
            "hash": _sha(schema_path.read_text(encoding="utf-8")),
        },
        "dev": {
            "duong_dan": "docs/evaluation/semantic-benchmark/dev/cases.json",
            "so_case": len(json.loads(dev_path.read_text(encoding="utf-8"))["cases"]),
            "fingerprint": hashlib.sha256(bam_noi_dung(dev_path)).hexdigest(),
        },
        "sealed": {
            "trang_thai": "CHUA_NIEM_PHONG" if not (BENCH / "sealed" / "cases.json").exists()
            else "DA_NIEM_PHONG",
            "ghi_chu": (
                "SEALED do nguồn ngoài cung cấp; agent viết hệ KHÔNG soạn nó. "
                "Tập của miền Tin học đã niêm phong và đã chạy; script niêm phong gỡ ở repo-cleanup, "
                "con dấu khoá bởi tests/semantic_program/test_benchmark_seal.py."
            ),
        },
    }


def main() -> int:
    argv = sys.argv[1:]
    verify = "--verify" in argv
    verify_historical = "--verify-historical" in argv
    as_json = "--json" in argv
    manifest_override: Path | None = None
    if "--manifest" in argv:
        idx = argv.index("--manifest")
        if idx + 1 >= len(argv):
            print("Thiếu đường dẫn sau --manifest.", file=sys.stderr)
            return 2
        manifest_override = Path(argv[idx + 1])

    if verify and verify_historical:
        print("Không dùng đồng thời --verify và --verify-historical.", file=sys.stderr)
        return 2

    if verify_historical:
        res = verify_historical_candidate(manifest_override)
        if as_json:
            print(json.dumps(res, ensure_ascii=False, indent=2))
        elif res["verdict"] == "PASS":
            print(
                f"Historical candidate khớp bản đã đóng băng tại commit {res['recorded_commit'][:9]} "
                f"(mã sản phẩm lịch sử: {res['actual_historical_so_file']} file, "
                f"{res['actual_historical_tree_hash'][:16]}…; "
                f"git_head_provenance={res['provenance_matches_head']})."
            )
            print(f"Lưu ý phạm vi: {res['scope_disclaimer']}")
        else:
            print(
                f"HISTORICAL CANDIDATE KHÔNG KHỚP ({res['verdict']}): "
                f"{', '.join(res['mismatches']) or res['error']}"
            )
            if res["error"]:
                print(f"Chi tiết: {res['error']}")
        return int(res["exit_code"])

    moi = build()

    if verify:
        if not OUT.exists():
            print("Chưa có EVALUATION_CANDIDATE.json — chạy không có --verify trước.")
            return 2
        cu = json.loads(OUT.read_text(encoding="utf-8"))
        lech = [
            k for k in ("cache_version", "spec_version_ir")
            if cu.get(k) != moi.get(k)
        ]
        # Kiểm bằng CHÍNH luật manifest đã đóng băng theo (vắng = luật cũ) — định danh lịch sử không đổi.
        if cu.get("product_commit_sha") is not None:
            try:
                pc = product_commit(cu.get("product_commit_rule"))
            except ValueError as e:
                print(f"{e} — không kiểm được danh tính sản phẩm.")
                return 2
            if cu["product_commit_sha"] != pc:
                lech.append("product_commit_sha")
        for nhom in ("taxonomy", "visual_primitive_set", "schema_semantic_program", "dev"):
            khoa = "hash" if nhom != "dev" else "fingerprint"
            if cu.get(nhom, {}).get(khoa) != moi.get(nhom, {}).get(khoa):
                lech.append(f"{nhom}.{khoa}")

        # MÃ SẢN PHẨM — kiểm riêng vì lời chẩn đoán của nó khác hẳn: bốn nhóm
        # trên nói "hợp đồng đổi", cái này nói "cài đặt đổi", và cái sau là thứ
        # `--verify` cũ hoàn toàn mù.
        ms_cu = (cu.get("measured_system") or {}).get("tree_hash")
        ms_moi = moi["measured_system"]["tree_hash"]
        if ms_cu is None:
            print(
                "Candidate được đóng băng TRƯỚC khi có `measured_system` — nó "
                "không chứng minh được mã sản phẩm còn nguyên. Đóng băng lại."
            )
            return 1
        if ms_cu != ms_moi:
            print("MÃ SẢN PHẨM ĐÃ ĐỔI so với bản đã đóng băng.")
            print(f"  đã đóng băng : {ms_cu[:16]}…  ({cu['measured_system'].get('so_file')} file)")
            print(f"  hiện tại     : {ms_moi[:16]}…  ({moi['measured_system']['so_file']} file)")
            commit = cu.get("commit_ngan") or cu.get("commit", "")[:7]
            if commit:
                print("\nXem đúng cái gì đổi:")
                print(f"  git diff --stat {commit} HEAD -- "
                      + " ".join(MEASURED_SYSTEM_PATHS))
            lech.append("measured_system.tree_hash")

        if lech:
            print("\nCANDIDATE LỆCH so với bản đã đóng băng:", ", ".join(lech))
            print("Nếu lệch vì một kết quả SEALED thì đây là VI PHẠM luật con dấu (§7.4).")
            return 1
        print(f"Candidate khớp bản đã đóng băng "
              f"(mã sản phẩm: {moi['measured_system']['so_file']} file, "
              f"{ms_moi[:16]}…).")
        return 0

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(moi, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Đã đóng băng: {OUT.relative_to(ROOT)}")
    print(f"  commit            {moi['commit_ngan']}  (cây sạch: {moi['cay_lam_viec_sach']})")
    print(f"  CACHE_VERSION     {moi['cache_version']}")
    print(f"  taxonomy          {moi['taxonomy']['so_nghia_vu']} nghĩa vụ · {moi['taxonomy']['hash'][:16]}")
    print(f"  primitive set     {moi['visual_primitive_set']['so_primitive']} · {moi['visual_primitive_set']['hash'][:16]}")
    print(f"  schema            {moi['schema_semantic_program']['hash'][:16]}")
    print(f"  DEV               {moi['dev']['so_case']} case · {moi['dev']['fingerprint'][:16]}")
    print(f"  MÃ SẢN PHẨM       {moi['measured_system']['so_file']} file · "
          f"{moi['measured_system']['tree_hash'][:16]}")
    print(f"  SEALED            {moi['sealed']['trang_thai']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
