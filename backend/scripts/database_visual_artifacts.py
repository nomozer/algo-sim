# -*- coding: utf-8 -*-
"""M17 W2B-VR — sinh artifact review thị giác renderer database.

Đọc `visual/captures.json` (chỉ record database), phán quyết REAL/PARTIAL/BROKEN
do NGƯỜI xem toàn bộ PNG chấm — assertion tự động chỉ hỗ trợ, KHÔNG tự nâng
REAL_VISUAL (§9).

    python scripts/database_visual_artifacts.py --out ../docs/evaluation/m17/rc1
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

RENDERER = "database"
CRITERIA = (
    "TABLE_STRUCTURE_CLEAR", "CURRENT_STATE_CLEAR", "FILTER_MECHANISM_CLEAR",
    "PROJECTION_CLEAR", "SORT_MECHANISM_CLEAR", "AGGREGATE_CLEAR",
    "PROGRESSIVE_REVEAL_PASS", "TERMINOLOGY_CORRECT", "LAYOUT_PASS",
    "RESPONSIVE_PASS",
)

# Phán quyết người review sau khi xem TỪNG PNG (desktop + 768). Mỗi mục nêu rõ
# bằng chứng quan sát được, không chấm REAL chỉ vì assertion xanh.
REVIEW: dict[str, dict] = {
    "vrdb1-filter-projection": {
        "status": "REAL_VISUAL", "n_a": (),
        "note": "Bảng nguồn hiện đủ 8 hàng; hàng đang xét (▶ Đang xét) và giữ "
                "(✓ Giữ) phân biệt bằng icon+chữ+màu, không chỉ màu; cột không "
                "chọn CHỈ mờ SAU bước chọn cột; kết quả hiện dần.",
    },
    "vrdb2-stable-sort-desc": {
        "status": "REAL_VISUAL", "n_a": (),
        "note": "Lọc tổ B còn 3 hàng; sau sắp xếp giảm dần Bùi Linh 9 trước, "
                "Trần Bình và Phạm Dũng CÙNG 8 giữ NGUYÊN thứ tự gốc (Bình "
                "trước Dũng) — sắp xếp ổn định quan sát được; Inspector ghi "
                "'Sắp xếp: Điểm giảm dần (ổn định)'.",
    },
    "vrdb3-count-after-filter": {
        "status": "REAL_VISUAL", "n_a": ("PROJECTION_CLEAR", "SORT_MECHANISM_CLEAR"),
        "note": "Lọc tổ A (3 hàng giữ, còn lại ✕ Loại gạch ngang mờ); "
                "accumulator đếm 1→2→3 hiện dần ở giai đoạn tích luỹ; COUNT cuối "
                "KHÔNG lộ ở bước đọc hàng.",
    },
    "vrdb4-avg-empty-cells": {
        "status": "REAL_VISUAL", "n_a": ("FILTER_MECHANISM_CLEAR",
                                         "PROJECTION_CLEAR", "SORT_MECHANISM_CLEAR"),
        "note": "Ô trống hiện '— trống —' in nghiêng, PHÂN BIỆT rõ với 0; bước "
                "tích luỹ nêu 'ô Điểm kiểm tra còn trống → bỏ qua, không tính là "
                "0'; AVG = 8 (=(8+10+6)/3 trên 3 hàng hợp lệ), KHÔNG phải "
                "(8+0+10+0+6)/5.",
    },
    "vrdb5-combined-pipeline": {
        "status": "REAL_VISUAL", "n_a": (),
        "note": "Năm tầng trong MỘT truy vấn: 3 hàng '✓ Giữ' đầu, 3 hàng '— "
                "Không lấy' (limit cắt) mờ — phân biệt rõ với 'Loại' của lọc; "
                "AVG = 8.9167 dùng nhãn 'Điểm'; hiểu được đây là một pipeline.",
    },
    "vrdb6-boundary-wide": {
        "status": "REAL_VISUAL", "n_a": ("AGGREGATE_CLEAR",),
        "note": "12 hàng × 8 cột, nhãn tiếng Việt dài, số âm/thập phân, ô trống. "
                "Ở 768px bảng CUỘN NGANG trong khung riêng, trang KHÔNG tràn "
                "ngang; căn cột đúng; lọc + sắp xếp theo cột chênh lệch (số âm) "
                "quan sát được.",
    },
    "vrdb8-missing-table": {
        "status": "REAL_VISUAL", "n_a": ("*",), "refusal": True,
        "note": "Thông báo 'CHƯA ĐỦ DỮ KIỆN' đúng bản chất; hướng dẫn cung cấp "
                "cột và các hàng; KHÔNG dựng bảng mẫu; không lộ JSON/schema/mã "
                "lỗi.",
    },
    "vrdb9-join-unsupported": {
        "status": "REAL_VISUAL", "n_a": ("*",), "refusal": True,
        "note": "Thông báo 'NGOÀI DANH MỤC MÔ PHỎNG'; nói rõ chỉ hỗ trợ MỘT "
                "bảng; không generic fallback; không hiện lỗi SQL kỹ thuật.",
    },
    "vrdb10-two-queries": {
        "status": "REAL_VISUAL", "n_a": ("*",), "refusal": True,
        "note": "Thông báo 'TÁCH THÀNH TỪNG YÊU CẦU' (không phải 'NGOÀI DANH "
                "MỤC' hay 'CHƯA ĐỦ DỮ KIỆN'); yêu cầu tách thành hai truy vấn; "
                "KHÔNG lộ chữ ký goal / id kỹ thuật; không âm thầm chạy một COUNT.",
    },
}

LEDGER = [
    {"id": "VDB-1", "severity": "BROKEN_VISUAL", "status": "FIXED",
     "found": "Badge miền lộ 'DATABASE' cho học sinh.",
     "fix": "Thêm ánh xạ domainBadge 'database' → 'TRUY VẤN BẢNG'.",
     "scope": "SimulationWorkspace.tsx (trình bày)"},
    {"id": "VDB-2", "severity": "BROKEN_VISUAL", "status": "FIXED",
     "found": "Giữ/loại chỉ phân biệt bằng MÀU — không nhãn chữ (§7).",
     "fix": "Thêm cột trạng thái với badge icon SVG + chữ (✓ Giữ / ✕ Loại / ▶ "
            "Đang xét / — Không lấy) + viền; icon dùng component (guard "
            "ui-hygiene cấm ký tự Unicode).",
     "scope": "table-module.tsx (trình bày)"},
    {"id": "VDB-3", "severity": "BROKEN_VISUAL", "status": "FIXED",
     "found": "Cột không được chọn mờ NGAY TỪ bước 0, trước giai đoạn chiếu.",
     "fix": "Chỉ mờ cột non-projected SAU khi cursor đã qua bước projection "
            "(đọc stagesReached từ trace).",
     "scope": "table-module.tsx (trình bày)"},
    {"id": "VDB-4", "severity": "BROKEN_VISUAL", "status": "FIXED",
     "found": "Ô trống trong tổng hợp trông Y HỆT hàng được tính → hiểu nhầm "
              "ô trống = 0.",
     "fix": "Ô trống hiện '— trống —' in nghiêng; bước tích luỹ nêu rõ 'bỏ "
            "qua, không tính là 0'.",
     "scope": "table-module.tsx (trình bày)"},
    {"id": "VDB-5", "severity": "BROKEN_VISUAL", "status": "FIXED",
     "found": "Sắp xếp KHÔNG quan sát được — bảng luôn giữ thứ tự gốc.",
     "fix": "Sau bước sắp xếp, hiển thị hàng theo thứ tự ĐÃ SẮP (đọc "
            "sort.detail.after từ trace); limit hiện hàng bị cắt với nhãn "
            "'Không lấy'. Renderer KHÔNG tự sắp.",
     "scope": "table-module.tsx (trình bày; engine trace không đổi)"},
    {"id": "VDB-6", "severity": "BROKEN_VISUAL", "status": "FIXED",
     "found": "Tường thuật + panel + Inspector lộ id cột kỹ thuật ('diem_kt', "
              "'diem') thay vì nhãn.",
     "fix": "Renderer dựng tường thuật learner-facing TỪ structured detail + "
            "nhãn cột; aggLabel/Inspector dùng nhãn. Engine narration giữ "
            "nguyên (chỉ để explain/debug, không hiển thị).",
     "scope": "table-module.tsx (trình bày; engine trace không đổi)"},
    {"id": "VDB-7", "severity": "BROKEN_VISUAL", "status": "FIXED",
     "found": "Thông báo 'hai truy vấn độc lập' hiện tiêu đề 'CHƯA ĐỦ DỮ KIỆN' "
              "— sai bản chất (đề không thiếu dữ kiện, chỉ hỏi hai việc).",
     "fix": "UnsupportedNotice thêm nhánh failure_category='semantic_incomplete' "
            "→ tiêu đề 'TÁCH THÀNH TỪNG YÊU CẦU'.",
     "scope": "SimulationWorkspace.tsx (trình bày dùng chung)"},
]


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--out", default="../docs/evaluation/m17/rc1")
    args = p.parse_args()
    out = Path(args.out)
    caps = json.loads((out / "visual" / "captures.json").read_text(encoding="utf-8"))
    db = [r for r in caps["records"] if r["renderer_id"] == RENDERER]

    shots = sum(len(r["captures"]) for r in db)
    desktop = sum(1 for r in db for c in r["captures"] if c["viewport"] == "desktop")
    narrow = shots - desktop
    counts = {"REAL_VISUAL": 0, "PARTIAL_VISUAL": 0, "BROKEN_VISUAL": 0, "VISUAL_COVERAGE_GAP": 0}
    rows = []
    for r in db:
        rv = REVIEW.get(r["fixture_id"], {"status": "VISUAL_COVERAGE_GAP", "note": "", "n_a": ()})
        counts[rv["status"]] += 1
        na = set(rv.get("n_a", ()))
        crit = {c: ("N/A" if ("*" in na or c in na) else True) for c in CRITERIA}
        rows.append({
            "fixture_id": r["fixture_id"], "title": r["title"],
            "kind": r["fixture_kind"], "screenshots": len(r["captures"]),
            "viewports": sorted({c["viewport"] for c in r["captures"]}),
            "review_status": rv["status"], "criteria": crit,
            "reviewer_note": rv["note"], "is_refusal": rv.get("refusal", False),
        })

    blockers = [x for x in LEDGER if x["status"].startswith("OPEN")]
    metrics = {
        "fixtures": len(db), "screenshots": shots,
        "desktop_screenshots": desktop, "narrow_screenshots": narrow,
        "issues_found": len(LEDGER),
        "issues_fixed": sum(1 for x in LEDGER if x["status"].startswith("FIXED")),
        "blockers_remaining": len(blockers),
        "REAL_VISUAL": counts["REAL_VISUAL"], "PARTIAL_VISUAL": counts["PARTIAL_VISUAL"],
        "BROKEN_VISUAL": counts["BROKEN_VISUAL"], "VISUAL_COVERAGE_GAP": counts["VISUAL_COVERAGE_GAP"],
    }
    payload = {
        "schema_version": "1", "run_label": "w2b-vr-database-visual",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "renderer_id": RENDERER, "target_id": "database.relational_table_query",
        "note": "Chụp Chrome thật qua CDP (không SSR). Phán quyết do người xem "
                "toàn bộ PNG chấm; assertion tự động không tự nâng REAL_VISUAL.",
        "metrics": metrics, "fixtures": rows,
    }
    (out / "database_visual_review.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    md = [
        "# M17 W2B-VR — Review thị giác `database.relational_table_query`", "",
        "Chụp trên **Chrome thật** qua CDP (không SSR), hai viewport. Phán quyết "
        "REAL/PARTIAL/BROKEN do **người xem toàn bộ PNG** chấm.", "",
        f"- Fixture: **{metrics['fixtures']}** · ảnh: **{metrics['screenshots']}** "
        f"(desktop {desktop} · hẹp {narrow})",
        f"- REAL **{metrics['REAL_VISUAL']}** · PARTIAL **{metrics['PARTIAL_VISUAL']}** · "
        f"BROKEN **{metrics['BROKEN_VISUAL']}** · GAP **{metrics['VISUAL_COVERAGE_GAP']}**",
        f"- Lỗi: tìm **{metrics['issues_found']}** · sửa **{metrics['issues_fixed']}** · "
        f"còn chặn **{metrics['blockers_remaining']}**", "",
        "| Fixture | Loại | Ảnh | Trạng thái |", "|---|---|---|---|",
    ]
    for r in rows:
        md.append(f"| `{r['fixture_id']}` | {r['kind']} | {r['screenshots']} | "
                  f"**{r['review_status']}** |")
    md += ["", "## Nhận xét từng fixture", ""]
    for r in rows:
        na = [k for k, v in r["criteria"].items() if v == "N/A"]
        md += [f"### `{r['fixture_id']}` — {r['review_status']}",
               f"- N/A: {', '.join(na) if na else 'không'}",
               f"- {r['reviewer_note']}", ""]
    (out / "database_visual_review.md").write_text("\n".join(md) + "\n", encoding="utf-8")

    led = ["# M17 W2B-VR — Failure ledger thị giác `database`", "",
           f"Tìm **{metrics['issues_found']}** · sửa **{metrics['issues_fixed']}** · "
           f"còn chặn **{metrics['blockers_remaining']}**", "",
           "Mọi bản sửa chỉ chạm lớp TRÌNH BÀY — engine trace/executor/spec KHÔNG "
           "đổi. Ảnh trước: `visual/database/before/` · sau: `visual/database/after/`.",
           ""]
    for x in LEDGER:
        led += [f"## {x['id']} — {x['severity']} · **{x['status']}**",
                f"- **Hiện tượng:** {x['found']}",
                f"- **Bản sửa:** {x['fix']}",
                f"- **Phạm vi:** {x['scope']}", ""]
    (out / "database_visual_failure_ledger.md").write_text("\n".join(led) + "\n", encoding="utf-8")

    print(f"fixture {metrics['fixtures']} · ảnh {shots} (desktop {desktop}/hẹp {narrow})")
    print(f"REAL {counts['REAL_VISUAL']} · PARTIAL {counts['PARTIAL_VISUAL']} · "
          f"BROKEN {counts['BROKEN_VISUAL']} · GAP {counts['VISUAL_COVERAGE_GAP']}")
    print(f"lỗi {metrics['issues_found']} · sửa {metrics['issues_fixed']} · "
          f"chặn {metrics['blockers_remaining']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
