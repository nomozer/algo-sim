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


def _sha(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


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
            "fingerprint": hashlib.sha256(dev_path.read_bytes()).hexdigest(),
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
        if lech:
            print("CANDIDATE LỆCH so với bản đã đóng băng:", ", ".join(lech))
            print("Nếu lệch vì một kết quả SEALED thì đây là VI PHẠM luật con dấu (§7.4).")
            return 1
        print("Candidate khớp bản đã đóng băng.")
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
    print(f"  SEALED            {moi['sealed']['trang_thai']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
