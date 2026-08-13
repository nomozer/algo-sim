# -*- coding: utf-8 -*-
"""WAVE 2A — BÁO CÁO PHỦ CHƯƠNG TRÌNH, SINH TỪ DỮ LIỆU.

Chạy từ `backend/`:
    .venv/Scripts/python.exe scripts/curriculum_benchmark_report.py [--json <path>]

Thước đo CHÍNH là **số ĐƠN VỊ CHƯƠNG TRÌNH được phủ**, không phải số case: một
đơn vị có 12 case cùng kiểu không phủ hơn một đơn vị có 3 case đủ dạng.

Báo cáo tách bạch ba thứ mà trộn lại sẽ nói dối:
  · case Tin học CÔNG KHAI  → tính vào phủ chương trình;
  · fixture ENGINE nội bộ    → chứng minh DSL chạy, KHÔNG tính vào phủ;
  · case NGOÀI PHẠM VI       → chứng minh từ chối trung thực, KHÔNG tính vào phủ.

Trạng thái năng lực DẪN XUẤT từ registry lúc chạy, nên thêm một target mới thì
báo cáo tự đổi mà không phải sửa case nào.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.evaluation.curriculum_schema import capability_status, unit_codes  # noqa: E402
from app.evaluation.datasets import NEW_POOLS, POOLS as ALL_POOLS  # noqa: E402
from app.evaluation.metamorphic import variants  # noqa: E402
from app.evaluation.product_scope import ProductScope, scope_of  # noqa: E402
from app.simulation.catalog import CATALOG  # noqa: E402

#: Pool CHỊU luật kết nạp — đúng tập mà phủ chương trình được phép đọc.
#: `regression` (30 case lịch sử) đứng ngoài: nó bị đóng băng và không có trường
#: neo, nên đưa vào chỉ làm loãng mẫu số chứ không thêm phủ nào.
#: `m16` PHẢI có mặt: bỏ nó ra là bỏ 68 case catalog-wide, và bản báo cáo đầu
#: tiên đã báo T12.CD4 "mỏng" chỉ vì không nhìn thấy pool ấy.
POOLS = {name: pool for name, pool in ALL_POOLS.items()
         if name in NEW_POOLS or name == "thesis"}


def _head() -> str:
    try:
        return subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()
    except Exception:
        return "(không phải kho git)"


def _items(pool: list) -> list:
    return pool


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", default="../docs/evaluation/m20/curriculum-benchmark.json")
    args = ap.parse_args()

    known = frozenset(CATALOG.keys())
    by_unit: dict[str, list] = defaultdict(list)
    scope_counts: Counter[str] = Counter()
    status_counts: Counter[str] = Counter()
    family_counts: Counter[str] = Counter()
    complexity_counts: Counter[str] = Counter()
    seen: set[str] = set()
    metamorphic_total = 0
    unanchored: list[str] = []

    for pool_name, mod in POOLS.items():
        for item in _items(mod):
            if item.id in seen:
                continue
            seen.add(item.id)
            scope = scope_of(item.id)
            scope_counts[scope.value] += 1
            if scope is not ProductScope.PUBLIC_THPT_INFORMATICS:
                continue
            status = capability_status(item.expect_simulation_id, known)
            status_counts[status.value] += 1
            metamorphic_total += len(variants(item.text))
            codes = unit_codes(item.curriculum_area)
            if codes:
                for code in codes:
                    by_unit[code].append(item)
            else:
                unanchored.append(item.id)
            if item.capability_family:
                family_counts[item.capability_family] += 1
            complexity_counts[item.complexity] += 1

    # W4 — JOIN target ↔ đơn vị chương trình, DẪN XUẤT chứ không chép tay.
    # Catalog ghi neo bằng số BÀI ("T10 CĐ5 · T11CS B17"), benchmark ghi bằng mã
    # CHỦ ĐỀ ("T10.CD5") — hai hệ ký hiệu khác nhau, join thẳng là bịa. Cầu nối
    # có sẵn trong dữ liệu: mỗi case đã khai CẢ mã đơn vị LẪN target nó nhắm tới.
    target_units: dict[str, list[str]] = {}
    for sid in sorted(known):
        codes = sorted({c for unit, items in by_unit.items() for i in items
                        if i.expect_simulation_id == sid for c in [unit]})
        target_units[sid] = codes
    khong_neo = [sid for sid, c in target_units.items() if not c]

    units = sorted(by_unit)
    print(f"HEAD {_head()[:8]}")
    print(f"\nĐƠN VỊ CHƯƠNG TRÌNH ĐƯỢC PHỦ: {len(units)}")
    print(f"{'đơn vị':22} {'case':>5}  {'≥3 case?':>9}")
    thin = []
    for u in units:
        n = len(by_unit[u])
        ok = "đủ" if n >= 3 else "MỎNG"
        if n < 3:
            thin.append(u)
        print(f"  {u:20} {n:>5}  {ok:>9}")

    print(f"\nPHÂN LOẠI PHẠM VI (mọi pool, {sum(scope_counts.values())} case):")
    for k, v in scope_counts.most_common():
        print(f"  {k:28} {v}")

    print("\nTRẠNG THÁI NĂNG LỰC (dẫn xuất từ registry, chỉ case công khai):")
    for k, v in status_counts.most_common():
        print(f"  {k:28} {v}")

    print(f"\nHỌ NĂNG LỰC: {len(family_counts)} · ĐỘ PHỨC TẠP: "
          f"{dict(sorted(complexity_counts.items()))}")
    print(f"BIẾN THỂ METAMORPHIC sinh được: {metamorphic_total}")
    co_neo = len(target_units) - len(khong_neo)
    print(f"\nTARGET CÓ BẰNG CHỨNG PHỦ CHƯƠNG TRÌNH: {co_neo}/{len(target_units)}")
    if khong_neo:
        print(f"  ⚠️ chưa có case nào neo tới: {', '.join(khong_neo)}")
    if thin:
        print(f"\n⚠️ ĐƠN VỊ MỎNG (<3 case), cần bổ sung ở W2A: {', '.join(thin)}")

    out = Path(args.json)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps({
        "head": _head(),
        "generatedAt": datetime.now(timezone.utc).isoformat(),
        "tool": "curriculum_benchmark_report.py",
        "toolVersion": "1",
        "environment": {"python": sys.version.split()[0], "targets": len(known)},
        "unitsCovered": len(units),
        "unitCaseCounts": {u: len(by_unit[u]) for u in units},
        "targetUnits": target_units,
        "targetsWithoutCurriculumEvidence": khong_neo,
        "thinUnits": thin,
        "unanchoredCases": unanchored,
        "scopeCounts": dict(scope_counts),
        "capabilityStatus": dict(status_counts),
        "capabilityFamilies": dict(family_counts),
        "complexity": dict(complexity_counts),
        "metamorphicVariants": metamorphic_total,
    }, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n→ {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
