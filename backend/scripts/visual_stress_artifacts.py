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
REVIEW: dict[str, dict] = {}

_FULL_PASS = {
    "STRUCTURE_CLEAR": True, "STATE_CLEAR": True, "MECHANISM_CLEAR": True,
    "PANEL_CORRECT": True, "TERMINOLOGY_CORRECT": True, "LAYOUT_PASS": True,
    "RESPONSIVE_PASS": True, "PROGRESSIVE_REVEAL_PASS": True,
}

REVIEW.update({
    "network": {
        "status": "REAL_VISUAL", "criteria": dict(_FULL_PASS),
        "note": (
            "Mọi cạnh hiện rõ ở CẢ hai viewport (không tái phát phantom token — "
            "kiểm computed stroke thật trong Chrome). Sau VIS-001: nhãn tiếng Việt "
            "dài nằm DƯỚI nút, không còn bị nút cắt ngang. BFS dùng hàng đợi, DFS "
            "dùng ngăn xếp, cùng topology cho thấy khác biệt rõ; đồ thị có chu "
            "trình không lặp vô hạn; đích không tới được KHÔNG bị dựng đường giả; "
            "đồ thị có hướng và đồ thị dày vẫn đọc được; kết quả hiện dần."
        ),
    },
    "tree": {
        "status": "REAL_VISUAL", "criteria": dict(_FULL_PASS),
        "note": (
            "Regression bản sửa nhãn dài VR1 GIỮ NGUYÊN: cạnh trái/phải rõ, nhãn "
            "11 nút tiếng Việt không chồng nút, canvas co giãn, ngăn xếp/hàng đợi "
            "đúng biến thể, thứ tự duyệt hiện dần, đường đang đi nổi bật. Cây một "
            "nút và cây lệch sâu đều đúng. Viewport hẹp đầy đủ, không cắt."
        ),
    },
    "generic": {
        "status": "PARTIAL_VISUAL",
        "criteria": {**_FULL_PASS, "LAYOUT_PASS": False},
        "note": (
            "Sau VIS-002 + bản so le BA hàng: ba nhãn dài trên cùng một đường "
            "ngang đã tách rời và đọc được; badge kỹ thuật GENERIC thay bằng 'MÔ "
            "PHỎNG THEO MÔ TẢ'. GIỮ PARTIAL vì §8: với nhãn CỰC dài và NHIỀU đối "
            "tượng hơn số hàng so le, bố cục vẫn có thể chật — không sửa thêm "
            "được nếu không đụng `state.pos` (§1 cấm sửa engine state). Hạn chế "
            "này KHÔNG che nút/trạng thái và KHÔNG làm sai cơ chế. Engine "
            "authenticity GIỮ NGUYÊN PARTIAL — audit thị giác không nâng hạng; "
            "tiêu đề không giả nhận diện thuật toán, phụ đề ghi rõ 'Mô phỏng tổng "
            "quát (AI tự dựng)'."
        ),
    },
    "algorithm": {
        "status": "REAL_VISUAL", "criteria": dict(_FULL_PASS),
        "note": (
            "Cột mảng, con trỏ bước, mã giả và tường thuật đồng bộ engine; số âm "
            "và thập phân hiển thị đúng; nhãn tên tiếng Việt không tràn; binary "
            "search thu hẹp khoảng rõ; kết quả chỉ hiện ở bước cuối."
        ),
    },
    "binary": {
        "status": "REAL_VISUAL", "criteria": dict(_FULL_PASS),
        "note": (
            "Hàng trọng số và ô bit rõ; bảng chia-lấy-dư của đổi cơ số tổng quát "
            "đọc được ở cả hai viewport; giá trị lớn (2026₁₀ → hex) không tràn."
        ),
    },
    "logic": {
        "status": "REAL_VISUAL", "criteria": dict(_FULL_PASS),
        "note": (
            "Cổng, dây nối và bảng chân trị rõ; mạch ba cổng lồng nhau đọc được. "
            "and_gate là module KHÁM PHÁ (không timeline) nên chỉ có ảnh initial "
            "— đúng hợp đồng, không phải thiếu ảnh."
        ),
    },
})


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
        "id": "VIS-003", "renderer": "*(dùng chung)*", "severity": "NOT_A_DEFECT",
        "found": "NGHI NGỜ ban đầu: ở viewport 768px, panel phải không xuống dòng "
                 "nên workspace bị cắt (tiêu đề, canvas, panel, tường thuật, nút "
                 "'Đặt lại').",
        "evidence": "Chẩn đoán DOM THẬT (diagnose-responsive.mjs) trên CẢ 4 route "
                    "dùng chung app shell, hai viewport: scrollWidth 758 ≤ "
                    "clientWidth 768 · 0 nút bị cắt · 0 nội dung bị tổ tiên cắt · "
                    "0 min-width cứng vượt viewport. before/VIS-003/ và "
                    "after/VIS-003/ cho cùng kết quả.",
        "root_cause": "LỖI TRONG PHÉP ĐO CỦA TÔI, không phải lỗi sản phẩm: script "
                      "audit đổi viewport SAU khi trang đã dựng ở 1440px, nên ảnh "
                      "ra khung 768 nhưng bố cục vẫn của 1440 — trông y hệt bị cắt. "
                      "App shell THỰC SỰ có responsive đúng.",
        "fix": "Sửa PHÉP ĐO: đặt viewport TRƯỚC rồi mới nạp trang (viewport thành "
               "vòng ngoài); bổ sung assertion page_overflow_x, clipped_content "
               "(bị tổ tiên cắt), rigid_min_width và key_elements vào audit. "
               "KHÔNG đổi một dòng CSS/layout production nào.",
        "scope": "frontend/scripts/visual-stress-audit.mjs (chỉ công cụ đo)",
        "status": "NOT_A_DEFECT_MEASUREMENT_ARTEFACT",
        "findings": [
            "audit runner TRƯỚC ĐÂY đổi viewport SAU khi trang đã dựng ở 1440px",
            "vì vậy ảnh 768px KHÔNG phản ánh layout responsive thật",
            "chẩn đoán DOM chứng minh: không page overflow, không clipping, "
            "không rigid min-width (cả 4 route × 2 viewport, before và after)",
            "production CSS/layout KHÔNG cần sửa",
            "runner đã sửa thành viewport-before-navigation + reload",
            "đã bổ sung assertion responsive (page_overflow_x, clipped_content, "
            "rigid_min_width, key_elements)",
        ],
        "why_not_fixed": (
            "Không có gì để sửa trong sản phẩm. Ghi lại đầy đủ thay vì xoá, vì đây "
            "là cảnh báo về chính phương pháp audit: ảnh chụp có thể phản ánh sai "
            "hiện thực nếu quy trình đo sai, và tôi đã suýt sửa app shell theo một "
            "lỗi không tồn tại."
        ),
    },
    {
        "id": "VIS-004", "renderer": "generic", "severity": "PARTIAL_VISUAL",
        "found": "Ba nhãn tiếng Việt dài trên cùng một đường ngang vẫn sát nhau sau "
                 "bản so le HAI hàng của VIS-002.",
        "evidence": "visual/generic/generic-vietnamese-labels-*-*.png (trước bản so "
                    "le ba hàng).",
        "root_cause": "So le hai hàng ⇒ với ba đối tượng, hai trong số đó vẫn dùng "
                      "chung một đường cơ sở.",
        "fix": "Nâng lên BA hàng so le và đẩy nhãn RA XA điểm (lên trên khi nhãn ở "
               "trên, xuống dưới khi đã lật) nên chữ không chồng marker. Trình bày "
               "thuần — `state.pos` không đụng.",
        "scope": "generic/ui.tsx",
        "status": "FIXED_PARTIAL",
        "why_not_fixed": (
            "Vẫn giữ PARTIAL_VISUAL theo §8: nhãn CỰC dài với số đối tượng nhiều "
            "hơn số hàng so le thì vẫn chật. Không che nút/trạng thái, không làm "
            "sai cơ chế ⇒ không chặn."
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

    # §11 — PROVENANCE RUNTIME. Tuyệt đối KHÔNG ghi kết quả doctor cũ thành một
    # lần xác minh MỚI tại HEAD này: nói "đã xác minh" khi chưa chạy là bịa bằng
    # chứng. Ghi đúng ba việc: đã xác minh Ở ĐÂU, vì sao không chạy lại, và vì
    # sao kết quả cũ vẫn còn hiệu lực (backend/catalog không đổi trong range).
    runtime_provenance = {
        "verified_at_commit": "e9ec370",
        "verified_result": "PASS",
        "verified_identity": {
            "sha": "b977a94923eb", "cache_version": "17",
            "family_count": 9, "target_count": 19, "catalog_hash": "0adecafd0d49",
        },
        "revalidated_at_this_head": False,
        "this_head": "fa9c21d (RC1-E1)",
        "why_not_revalidated": (
            "Docker Desktop không khả dụng khi đóng RC1-E — không có runtime "
            "response nào để đối chiếu."
        ),
        "why_previous_result_still_applies": (
            "backend/app và catalog KHÔNG đổi một dòng trong range RC1-E "
            "(e9ec370..fa9c21d): `git diff -- backend/app` rỗng. Toàn bộ thay đổi "
            "là frontend + script đo + artifact."
        ),
        "claim_boundary": (
            "Đây là runtime parity ĐÃ XÁC MINH TẠI BASELINE TRƯỚC checkpoint, "
            "KHÔNG phải một lần xác minh mới tại HEAD fa9c21d."
        ),
    }

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
        "issues_fixed": sum(1 for x in LEDGER if x["status"].startswith("FIXED")),
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
         "runtime_provenance": runtime_provenance,
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
        "### Provenance runtime",
        "",
        f"- Đã xác minh tại **{runtime_provenance['verified_at_commit']}**: "
        f"**{runtime_provenance['verified_result']}** "
        f"(`sha={runtime_provenance['verified_identity']['sha']}` · "
        f"cache={runtime_provenance['verified_identity']['cache_version']} · "
        f"family={runtime_provenance['verified_identity']['family_count']} · "
        f"target={runtime_provenance['verified_identity']['target_count']})",
        f"- Chạy lại tại HEAD này (`{runtime_provenance['this_head']}`): "
        f"**KHÔNG** — {runtime_provenance['why_not_revalidated']}",
        f"- Vì sao vẫn hiệu lực: {runtime_provenance['why_previous_result_still_applies']}",
        f"- **Ranh giới:** {runtime_provenance['claim_boundary']}",
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
