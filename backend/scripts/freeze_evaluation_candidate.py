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

    python scripts/freeze_evaluation_candidate.py           # ghi manifest
    python scripts/freeze_evaluation_candidate.py --verify  # so, thoát != 0 khi lệch
"""
from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

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
    "frontend/src/simulations/domains/generic/semantic_program.schema.json",
)

_BO_QUA = ("__pycache__", ".pyc", ".pyo")


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
        # Cây phải SẠCH thì `commit` ở trên mới thật sự định danh được bản đang
        # đo. Loại trừ đúng một file: chính manifest này, vì nó được sinh ra
        # trong lúc kiểm — con gà và quả trứng, không phải sự trôi.
        "cay_lam_viec_sach": all(
            "EVALUATION_CANDIDATE.json" in d
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
                "Niêm phong bằng scripts/seal_benchmark.py."
            ),
        },
    }


def main() -> int:
    moi = build()
    verify = "--verify" in sys.argv

    if verify:
        if not OUT.exists():
            print("Chưa có EVALUATION_CANDIDATE.json — chạy không có --verify trước.")
            return 2
        cu = json.loads(OUT.read_text(encoding="utf-8"))
        lech = [
            k for k in ("cache_version", "spec_version_ir")
            if cu.get(k) != moi.get(k)
        ]
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
