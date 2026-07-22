# -*- coding: utf-8 -*-
"""M17-RC1 §E — sinh artifact audit thị giác.

Ma trận renderer SINH TỪ REGISTRY (không viết tay). Phán quyết REAL/PARTIAL/
BROKEN do NGƯỜI xem ảnh chấm — assertion tự động chỉ là bằng chứng hỗ trợ,
KHÔNG tự nâng lên REAL_VISUAL (§9).

    python scripts/visual_stress_artifacts.py --out ../docs/evaluation/m17/rc1
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.catalog_conformance import ai_reachable_ids  # noqa: E402
from app.simulation.catalog import CATALOG  # noqa: E402

STATUSES = ("REAL_VISUAL", "PARTIAL_VISUAL", "BROKEN_VISUAL", "VISUAL_COVERAGE_GAP")

# Phán quyết của NGƯỜI REVIEW sau khi xem toàn bộ PNG (§9). Ghi kèm lý do —
# không chấm REAL_VISUAL chỉ vì assertion xanh.
REVIEW: dict[str, dict] = {
    "network": {
        "status": "PARTIAL_VISUAL",
        "criteria": {
            "STRUCTURE_CLEAR": True, "STATE_CLEAR": True, "MECHANISM_CLEAR": True,
            "PANEL_CORRECT": True, "TERMINOLOGY_CORRECT": True, "LAYOUT_PASS": True,
            "RESPONSIVE_PASS": False, "PROGRESSIVE_REVEAL_PASS": True,
        },
        "note": (
            "Sau bản sửa nhãn: mọi cạnh hiện rõ (không tái phát phantom token), "
            "nhãn dài xuống dưới nút nên không còn bị nút cắt ngang, hàng đợi/"
            "ngăn xếp đúng biến thể, thứ tự thăm hiện dần, đích không tới được "
            "không bị dựng đường giả. HẠ ĐIỂM vì lỗi layout DÙNG CHUNG ở viewport "
            "hẹp (xem VIS-003), không phải lỗi của renderer này."
        ),
    },
    "tree": {
        "status": "PARTIAL_VISUAL",
        "criteria": {
            "STRUCTURE_CLEAR": True, "STATE_CLEAR": True, "MECHANISM_CLEAR": True,
            "PANEL_CORRECT": True, "TERMINOLOGY_CORRECT": True, "LAYOUT_PASS": True,
            "RESPONSIVE_PASS": False, "PROGRESSIVE_REVEAL_PASS": True,
        },
        "note": (
            "Regression bản sửa nhãn dài VR1 GIỮ NGUYÊN: cạnh trái/phải rõ, nhãn "
            "11 nút tiếng Việt không chồng nút, canvas co giãn, ngăn xếp/hàng đợi "
            "đúng biến thể, thứ tự duyệt hiện dần. Cây một nút và cây lệch sâu "
            "đều đúng. HẠ ĐIỂM vì VIS-003 (layout hẹp dùng chung)."
        ),
    },
    "generic": {
        "status": "PARTIAL_VISUAL",
        "criteria": {
            "STRUCTURE_CLEAR": True, "STATE_CLEAR": True, "MECHANISM_CLEAR": True,
            "PANEL_CORRECT": True, "TERMINOLOGY_CORRECT": True, "LAYOUT_PASS": False,
            "RESPONSIVE_PASS": False, "PROGRESSIVE_REVEAL_PASS": True,
        },
        "note": (
            "Sau hai bản sửa: nhãn dài so le nên không còn dồn thành khối chữ "
            "không đọc được; badge kỹ thuật GENERIC đã thay bằng 'MÔ PHỎNG THEO "
            "MÔ TẢ'. VẪN CHẬT khi nhiều nhãn rất dài nằm cùng hàng ngang — đọc "
            "được nhưng sát nhau; không sửa thêm được nếu không đụng `state.pos` "
            "(§10 cấm sửa engine state). Engine authenticity GIỮ NGUYÊN PARTIAL — "
            "audit thị giác KHÔNG nâng hạng; tiêu đề không giả nhận diện thuật "
            "toán, phụ đề nói rõ 'Mô phỏng tổng quát (AI tự dựng)'."
        ),
    },
    "algorithm": {
        "status": "PARTIAL_VISUAL",
        "criteria": {
            "STRUCTURE_CLEAR": True, "STATE_CLEAR": True, "MECHANISM_CLEAR": True,
            "PANEL_CORRECT": True, "TERMINOLOGY_CORRECT": True, "LAYOUT_PASS": True,
            "RESPONSIVE_PASS": False, "PROGRESSIVE_REVEAL_PASS": True,
        },
        "note": (
            "Cột mảng, con trỏ bước, mã giả và tường thuật đồng bộ; số âm/thập "
            "phân và nhãn tên tiếng Việt hiển thị đúng; binary search thu hẹp "
            "khoảng rõ. HẠ ĐIỂM vì VIS-003."
        ),
    },
    "binary": {
        "status": "PARTIAL_VISUAL",
        "criteria": {
            "STRUCTURE_CLEAR": True, "STATE_CLEAR": True, "MECHANISM_CLEAR": True,
            "PANEL_CORRECT": True, "TERMINOLOGY_CORRECT": True, "LAYOUT_PASS": True,
            "RESPONSIVE_PASS": False, "PROGRESSIVE_REVEAL_PASS": True,
        },
        "note": "Hàng trọng số/bit và bảng chia-lấy-dư rõ. HẠ ĐIỂM vì VIS-003.",
    },
    "logic": {
        "status": "PARTIAL_VISUAL",
        "criteria": {
            "STRUCTURE_CLEAR": True, "STATE_CLEAR": True, "MECHANISM_CLEAR": True,
            "PANEL_CORRECT": True, "TERMINOLOGY_CORRECT": True, "LAYOUT_PASS": True,
            "RESPONSIVE_PASS": False, "PROGRESSIVE_REVEAL_PASS": True,
        },
        "note": (
            "Cổng, dây nối và bảng chân trị rõ; and_gate là module khám phá "
            "(không timeline) nên chỉ có ảnh initial — đúng hợp đồng. HẠ ĐIỂM vì "
            "VIS-003."
        ),
    },
}

LEDGER = [
    {
        "id": "VIS-001", "renderer": "network", "severity": "BROKEN_VISUAL",
        "found": "Nhãn tiếng Việt dài ĐÈ LÊN nút — chữ bị chính hình tròn cắt ngang.",
        "evidence": "5 chồng lấn node-label đo trong Chrome, cả desktop lẫn hẹp; "
                    "ảnh before: visual/before/graph-vietnamese-long-labels-*.png",
        "root_cause": "`<text>` luôn căn giữa TRONG nút r=16 nên nhãn dài tràn hai bên.",
        "fix": "Nhãn dài (>3 ký tự) vẽ DƯỚI nút, giữ id trong nút — cùng quy ước "
               "renderer cây; vòng bố cục co lại và canvas cao thêm để đủ chỗ.",
        "scope": "traverse-module.tsx (chỉ trình bày; KHÔNG đụng engine state)",
        "status": "FIXED",
    },
    {
        "id": "VIS-002", "renderer": "generic", "severity": "BROKEN_VISUAL",
        "found": "Nhãn dài của các đối tượng cùng hàng ngang dồn thành khối chữ "
                 "không đọc được; badge hiển thị 'GENERIC' cho học sinh.",
        "evidence": "1 chồng lấn label-label + thuật ngữ GENERIC ở 12/12 capture "
                    "generic; ảnh before: visual/before/… (chụp trước bản sửa).",
        "root_cause": "Mọi nhãn dùng chung một đường cơ sở; badge lấy thẳng "
                      "`mod.domain.toUpperCase()`.",
        "fix": "So le đường cơ sở cho nhãn dài (>8 ký tự) theo thứ tự khai báo; "
               "badge ánh xạ sang tiếng Việt ('MÔ PHỎNG THEO MÔ TẢ').",
        "scope": "generic/ui.tsx + SimulationWorkspace.tsx (trình bày; engine "
                 "state.pos KHÔNG đụng)",
        "status": "FIXED",
    },
    {
        "id": "VIS-003", "renderer": "*(dùng chung)*", "severity": "BROKEN_VISUAL",
        "found": "Ở viewport hẹp (768px), panel bên phải KHÔNG xuống dòng mà giữ "
                 "nguyên cột — workspace bị cắt: tiêu đề, canvas, panel trạng "
                 "thái, tường thuật và nút 'Đặt lại' đều mất phần bên phải.",
        "evidence": "visual/tree/tree-vietnamese-11-nodes-mid-narrow.png · "
                    "visual/network/graph-vietnamese-long-labels-mid-narrow.png "
                    "(và mọi renderer ở viewport hẹp).",
        "root_cause": "Layout hai cột của app shell chưa có điểm ngắt responsive; "
                      "đây là CSS DÙNG CHUNG, không thuộc renderer nào.",
        "fix": None,
        "scope": "app shell CSS — ảnh hưởng CẢ 6 renderer",
        "status": "OPEN_BLOCKING",
        "why_not_fixed": (
            "Đúng điều kiện dừng §13: 'shared layout fix cần thay đổi kiến trúc "
            "lớn'. Sửa điểm ngắt responsive của app shell chạm mọi màn hình (kể "
            "cả Home/Library/History ngoài phạm vi §E) và theo §10 phải chụp lại "
            "TOÀN BỘ renderer. Báo trước, xin quyết định phạm vi."
        ),
    },
]


def build_matrix(captures: dict) -> list[dict]:
    by_renderer: dict[str, dict] = defaultdict(
        lambda: {"targets": [], "families": set(), "fixtures": defaultdict(list),
                 "shots": 0, "viewports": set()})
    for rec in captures["records"]:
        r = by_renderer[rec["renderer_id"]]
        r["fixtures"][rec["fixture_kind"]].append(rec["fixture_id"])
        r["shots"] += len(rec["captures"])
        for c in rec["captures"]:
            r["viewports"].add(c["viewport"])
        if rec["target_id"] and rec["target_id"] not in r["targets"]:
            r["targets"].append(rec["target_id"])

    rows = []
    for sid in ai_reachable_ids():           # DẪN XUẤT từ registry
        spec = CATALOG[sid]
        by_renderer[spec.domain]["families"].update(
            m.family_id.value for m in spec.family_memberships)
        by_renderer[spec.domain].setdefault("all_targets", [])
    for rid in sorted(by_renderer):
        d = by_renderer[rid]
        registry_targets = sorted(
            sid for sid in ai_reachable_ids() if CATALOG[sid].domain == rid)
        review = REVIEW.get(rid, {"status": "VISUAL_COVERAGE_GAP", "criteria": {}, "note": ""})
        rows.append({
            "renderer_id": rid,
            "families": sorted(d["families"]),
            "targets_in_registry": registry_targets,
            "targets_covered_by_fixture": sorted(d["targets"]),
            "canonical_fixtures": sorted(d["fixtures"].get("canonical", [])),
            "boundary_fixtures": sorted(d["fixtures"].get("boundary", [])),
            "stress_fixtures": sorted(d["fixtures"].get("stress", [])),
            "refusal_fixtures": sorted(d["fixtures"].get("refusal", [])),
            "viewport_coverage": sorted(d["viewports"]),
            "screenshot_count": d["shots"],
            "review_status": review["status"],
            "criteria": review.get("criteria", {}),
            "reviewer_note": review.get("note", ""),
        })
    return rows


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--out", default="../docs/evaluation/m17/rc1")
    args = p.parse_args()
    out = Path(args.out)
    captures = json.loads((out / "visual" / "captures.json").read_text(encoding="utf-8"))
    rows = build_matrix(captures)

    counts = {s: sum(1 for r in rows if r["review_status"] == s) for s in STATUSES}
    shots = sum(r["screenshot_count"] for r in rows)
    desktop = sum(1 for rec in captures["records"] for c in rec["captures"]
                  if c["viewport"] == "desktop")
    narrow = shots - desktop
    blocking = [x for x in LEDGER if x["status"].startswith("OPEN")]

    metrics = {
        "renderer_count": len(rows),
        "renderer_reviewed": sum(1 for r in rows if r["review_status"] != "VISUAL_COVERAGE_GAP"),
        "visual_fixture_count": len(captures["records"]),
        "screenshot_count": shots,
        "desktop_count": desktop,
        "narrow_viewport_count": narrow,
        "REAL_VISUAL": counts["REAL_VISUAL"],
        "PARTIAL_VISUAL": counts["PARTIAL_VISUAL"],
        "BROKEN_VISUAL": counts["BROKEN_VISUAL"],
        "VISUAL_COVERAGE_GAP": counts["VISUAL_COVERAGE_GAP"],
        "issues_found": len(LEDGER),
        "issues_fixed": sum(1 for x in LEDGER if x["status"] == "FIXED"),
        "blocking_issues_remaining": len(blocking),
    }

    (out / "visual_renderer_matrix.json").write_text(json.dumps(
        {"schema_version": "1", "generated_at": datetime.now(timezone.utc).isoformat(),
         "note": "Renderer DẪN XUẤT từ registry (ai_reachable). Phán quyết do "
                 "người xem ảnh chấm — assertion tự động không tự nâng REAL_VISUAL.",
         "renderers": rows}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    (out / "visual_stress_review.json").write_text(json.dumps(
        {"schema_version": "1", "run_label": "rc1-e-visual-stress",
         "generated_at": datetime.now(timezone.utc).isoformat(),
         "viewports": captures["viewports"], "metrics": metrics,
         "renderers": rows, "failure_ledger": LEDGER}, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8")

    md = [
        "# M17-RC1 §E — Audit thị giác toàn danh mục",
        "",
        "Chụp trên **Chrome thật** qua CDP (không SSR, không framework E2E), hai",
        "viewport, kèm assertion chạy trong trình duyệt. Phán quyết REAL/PARTIAL/",
        "BROKEN do **người xem ảnh** chấm — assertion xanh KHÔNG tự thành REAL.",
        "",
        f"- Renderer: **{metrics['renderer_count']}** (đã review "
        f"{metrics['renderer_reviewed']}) · fixture **{metrics['visual_fixture_count']}**",
        f"- Ảnh: **{metrics['screenshot_count']}** "
        f"(desktop {metrics['desktop_count']} · hẹp {metrics['narrow_viewport_count']})",
        f"- REAL **{metrics['REAL_VISUAL']}** · PARTIAL **{metrics['PARTIAL_VISUAL']}** · "
        f"BROKEN **{metrics['BROKEN_VISUAL']}** · GAP **{metrics['VISUAL_COVERAGE_GAP']}**",
        f"- Lỗi: tìm **{metrics['issues_found']}** · sửa **{metrics['issues_fixed']}** · "
        f"còn chặn **{metrics['blocking_issues_remaining']}**",
        "",
        "| Renderer | Family | Target | canonical/boundary/stress | Ảnh | Trạng thái |",
        "|---|---|---|---|---|---|",
    ]
    for r in rows:
        md.append(
            f"| `{r['renderer_id']}` | {', '.join(r['families'])} | "
            f"{len(r['targets_covered_by_fixture'])}/{len(r['targets_in_registry'])} | "
            f"{len(r['canonical_fixtures'])}/{len(r['boundary_fixtures'])}/"
            f"{len(r['stress_fixtures'])} | {r['screenshot_count']} | "
            f"**{r['review_status']}** |")
    md += ["", "## Nhận xét người review", ""]
    for r in rows:
        md.append(f"### `{r['renderer_id']}` — {r['review_status']}")
        fail = [k for k, v in r["criteria"].items() if not v]
        md.append(f"- Tiêu chí chưa đạt: {', '.join(fail) if fail else 'không'}")
        md += [f"- {r['reviewer_note']}", ""]
    (out / "visual_stress_review.md").write_text("\n".join(md) + "\n", encoding="utf-8")

    led = ["# M17-RC1 §E — Failure ledger thị giác", "",
           f"Tìm **{metrics['issues_found']}** · sửa **{metrics['issues_fixed']}** · "
           f"còn chặn **{metrics['blocking_issues_remaining']}**", ""]
    for x in LEDGER:
        led += [f"## {x['id']} — {x['renderer']} · {x['severity']} · **{x['status']}**", "",
                f"- **Hiện tượng:** {x['found']}",
                f"- **Bằng chứng:** {x['evidence']}",
                f"- **Nguyên nhân:** {x['root_cause']}",
                f"- **Bản sửa:** {x['fix'] or '— (chưa sửa)'}",
                f"- **Phạm vi:** {x['scope']}"]
        if x.get("why_not_fixed"):
            led.append(f"- **Vì sao chưa sửa:** {x['why_not_fixed']}")
        led.append("")
    (out / "visual_failure_ledger.md").write_text("\n".join(led) + "\n", encoding="utf-8")

    print(f"renderer {metrics['renderer_count']} · fixture {metrics['visual_fixture_count']} · "
          f"ảnh {metrics['screenshot_count']} (desktop {desktop}/hẹp {narrow})")
    print(f"REAL {metrics['REAL_VISUAL']} · PARTIAL {metrics['PARTIAL_VISUAL']} · "
          f"BROKEN {metrics['BROKEN_VISUAL']} · GAP {metrics['VISUAL_COVERAGE_GAP']}")
    print(f"lỗi {metrics['issues_found']} · sửa {metrics['issues_fixed']} · "
          f"còn chặn {metrics['blocking_issues_remaining']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
