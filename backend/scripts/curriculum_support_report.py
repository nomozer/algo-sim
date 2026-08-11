# -*- coding: utf-8 -*-
"""W4B-3A — BẢNG HỖ TRỢ THEO CHƯƠNG TRÌNH, sinh từ registry.

Khác `catalog_runtime_matrix.py` (hướng KĨ SƯ: target nào, executor nào) và khác
`after-matrix` (hướng SẢN PHẨM: mỗi target cho học sinh làm gì). Bảng này hướng
GIÁO VIÊN: mỗi ĐƠN VỊ KIẾN THỨC của chương trình được hỗ trợ tới đâu, và hỗ trợ
theo KIỂU nào.

Nguồn DUY NHẤT: `app.simulation.coverage.KNOWLEDGE_UNITS`. Không viết tay dòng
nào ở đây — sửa phân loại thì sửa registry rồi chạy lại.

RANH GIỚI PHẢI GIỮ (COVERAGE §O): "chương trình có chủ đề này" KHÁC "AlgoSim có
một cơ chế mô phỏng có nghĩa sư phạm cho nó". Bảng in cả hai cột chính là để
không ai đọc nhầm cột này thành cột kia.

    python scripts/curriculum_support_report.py [--json <out.json>] [--md <out.md>]
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.simulation.coverage import (  # noqa: E402
    KNOWLEDGE_UNITS,
    CoverageStatus,
    SupportKind,
    curriculum_support_rows,
)

_KIND_LABEL = {
    SupportKind.SUPPORTED_INTERACTIVE: "Học sinh ĐỔI được mô hình, engine tính lại",
    SupportKind.SUPPORTED_TRACE: "Đi từng bước tất định (có thể có cam kết được chấm)",
    SupportKind.SUPPORTED_BOUNDED_ARTIFACT: "Sửa thuộc tính trong miền ĐÓNG của một sản phẩm",
    SupportKind.SUPPORTED_EXPLANATION: "Chỉ trình bày/giải thích",
    SupportKind.PARTIAL: "Có phần — giới hạn khai tường minh",
    SupportKind.UNSUPPORTED: "Chưa/cố ý không hỗ trợ",
    SupportKind.NOT_SIMULATION_SUITABLE: "Không nên mô phỏng (mô phỏng ở đây là trang trí)",
}


def build() -> dict:
    rows = curriculum_support_rows()
    kinds = Counter(r["support_kind"] for r in rows)
    in_scope = [u for u in KNOWLEDGE_UNITS if u.status is not CoverageStatus.OUT_OF_SCOPE]
    unfinished = sorted(
        u.unit_id for u in in_scope
        if u.support_kind in (SupportKind.PARTIAL, SupportKind.UNSUPPORTED)
    )
    return {
        "units": len(rows),
        "in_scope_units": len(in_scope),
        "by_support_kind": {k.value: kinds.get(k.value, 0) for k in SupportKind},
        "unfinished_in_scope": unfinished,
        # Nhãn này KHÔNG được tự nâng cấp: nó chỉ đổi khi `unfinished` rỗng.
        "claim": "CURRICULUM_SUPPORT_PARTIAL" if unfinished else "CURRICULUM_SUPPORT_COMPLETE",
        "rows": rows,
    }


def to_md(report: dict) -> str:
    lines = [
        "# W4B-3A — BẢNG HỖ TRỢ THEO CHƯƠNG TRÌNH",
        "",
        "**Sinh từ nguồn** bởi `backend/scripts/curriculum_support_report.py` đọc",
        "`app/simulation/coverage.py`. Đừng sửa tay: sửa registry rồi chạy lại.",
        "",
        "> **Đọc đúng hai cột.** `Phủ` trả lời *mục này đã ship tới đâu*; `Kiểu hỗ trợ`",
        "> trả lời *học sinh thật sự làm được gì*. Một mục chỉ bấm-Tiến-để-xem và một",
        "> mục học sinh đổi được mô hình đều hiện `SUPPORTED` ở cột thứ nhất — đó là lý",
        "> do có cột thứ hai.",
        "",
        "> **Ranh giới không được xoá:** *chương trình có chủ đề này* ≠ *AlgoSim có một",
        "> cơ chế mô phỏng có nghĩa sư phạm cho nó*. Không đơn vị nào được nâng hạng chỉ",
        "> vì có target trùng tên (COVERAGE §O5).",
        "",
        f"**{report['units']} đơn vị kiến thức** · trong phạm vi: **{report['in_scope_units']}** · "
        f"tuyên bố hiện hành: **`{report['claim']}`**",
        "",
        "## Đếm theo kiểu hỗ trợ",
        "",
        "| Kiểu | Nghĩa | Số đơn vị |",
        "|---|---|---|",
    ]
    for k in SupportKind:
        lines.append(f"| `{k.value}` | {_KIND_LABEL[k]} | {report['by_support_kind'][k.value]} |")
    lines += [
        "",
        f"Còn dang dở trong phạm vi ({len(report['unfinished_in_scope'])}): "
        + (", ".join(f"`{u}`" for u in report["unfinished_in_scope"]) or "—"),
        "",
        "## Từng đơn vị",
        "",
        "| Đơn vị | Nhãn | Neo chương trình | Phủ | Kiểu hỗ trợ | Bằng chứng |",
        "|---|---|---|---|---|---|",
    ]
    for r in report["rows"]:
        ev = r["support_evidence"].replace("|", "\\|")
        lines.append(
            f"| `{r['unit_id']}` | {r['label']} | {r['curriculum_anchor']} | "
            f"{r['coverage_status']} | **{r['support_kind']}** | {ev} |"
        )
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--json")
    ap.add_argument("--md")
    a = ap.parse_args()
    report = build()
    if a.json:
        Path(a.json).parent.mkdir(parents=True, exist_ok=True)
        Path(a.json).write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    if a.md:
        Path(a.md).parent.mkdir(parents=True, exist_ok=True)
        Path(a.md).write_text(to_md(report), encoding="utf-8")
    print(f"{report['units']} đơn vị · claim = {report['claim']}")
    for k, n in report["by_support_kind"].items():
        if n:
            print(f"  {k:<28} {n}")
    if report["unfinished_in_scope"]:
        print("  dang dở:", ", ".join(report["unfinished_in_scope"]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
