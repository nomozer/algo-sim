# -*- coding: utf-8 -*-
"""M17 W2B-PATCH — sinh artifact review (thị giác + tổng kết bản vá).

Đọc `visual/captures.json` do `frontend/scripts/capture-w2b-patch.mjs` sinh
(Chrome THẬT), ghép với PHÁN QUYẾT CỦA NGƯỜI xem từng PNG. Assertion tự động
chỉ HỖ TRỢ — không tự nâng REAL_VISUAL (§9, giữ nguyên luật của RC1 §E).

    python scripts/w2b_patch_artifacts.py --out ../docs/evaluation/m17/w2b-patch
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

# Phán quyết sau khi XEM ẢNH (desktop 1440 + narrow 768). Mỗi mục nêu bằng
# chứng QUAN SÁT ĐƯỢC, không chấm đạt chỉ vì assertion xanh.
REVIEW: dict[str, dict] = {
    "wp1-L3-avg-empty-markers": {
        "finding": "L3", "status": "REAL_VISUAL",
        "note": "Hai ô thiếu dữ liệu hiện '— trống —' in nghiêng, PHÂN BIỆT rõ "
                "với số 0 (bảng không có ô 0 nào); Inspector và bước cuối cùng "
                "ghi 'Trung bình của Điểm kiểm tra = 8.25' — đúng 4 ô có dữ "
                "liệu (8+9.5+7+8.5)/4, KHÔNG phải (…)/6. Cả hai viewport giống "
                "nhau, không tràn ngang.",
    },
    "wp2-L4-five-stage-pipeline": {
        "finding": "L4", "status": "REAL_VISUAL",
        "note": "Chỉ báo quy trình hiện ĐỦ 5 bước có đánh số (1. Lọc → 2. Chọn "
                "cột → 3. Sắp xếp giảm dần → 4. Lấy 3 dòng → 5. Tính trung "
                "bình). Ở bước 1/32 KHÔNG bước nào được đánh dấu và Inspector "
                "ghi 'Kết quả hiện dần theo từng bước…' (không lộ đáp án); ở "
                "bước 32/32 cả 5 bước có dấu ✓, còn đúng 3 dòng An/Dũng/Lan, "
                "hai dòng bị cắt mang nhãn 'Không lấy', kết quả 'Trung bình "
                "của Điểm = 8.5'. Cột không chọn bị gạch ngang + mờ. Ở 768px "
                "chỉ báo tự xuống dòng, bảng không tràn trang.",
    },
    "wp3-L5-missing-table": {
        "finding": "L5", "status": "REAL_VISUAL",
        "note": "Tiêu đề 'CHƯA ĐỦ DỮ KIỆN'; nội dung đòi CUNG CẤP BẢNG kèm ví "
                "dụ cụ thể; gợi ý 'Bổ sung dữ liệu còn thiếu vào đề rồi gửi "
                "lại'. KHÔNG còn câu xui tách truy vấn — đúng bản chất lỗi.",
    },
    "wp4-L6-two-queries": {
        "finding": "L6", "status": "REAL_VISUAL",
        "note": "Tiêu đề 'TÁCH THÀNH TỪNG YÊU CẦU' + gợi ý 'Mỗi lần hỏi một "
                "yêu cầu (giữ nguyên dữ liệu)' — GIỮ NGUYÊN như trước bản vá, "
                "đúng cho ca bảng ĐÃ có mà đề hỏi hai truy vấn độc lập.",
    },
    "wp5-stage-shortfall": {
        "finding": "L4", "status": "REAL_VISUAL",
        "defect_found_here": True,
        "note": "LỖI CHỈ REVIEW ẢNH MỚI THẤY (unit + SSR đều xanh): lần chụp "
                "đầu, thông điệp 'chưa dựng được 2 bước' lại đội tiêu đề 'TÁCH "
                "THÀNH TỪNG YÊU CẦU' và gợi ý 'Mỗi lần hỏi một yêu cầu' — lời "
                "khuyên SAI, vì đề vốn là MỘT truy vấn nhiều bước, tách ra "
                "không giúp gì. Nguyên nhân gốc: notice chọn tiêu đề chỉ theo "
                "`failure_category`, mà `semantic_incomplete` nay gộp hai ca "
                "cần lời khuyên ngược nhau. Đã sửa: thêm mã "
                "`PIPELINE_STAGE_INCOMPLETE`, notice đọc `error_code` trước. "
                "Ảnh sau khi sửa: tiêu đề 'CHƯA DỰNG ĐỦ CÁC BƯỚC', gợi ý 'Nêu "
                "rõ từng bước cần làm rồi gửi lại'.",
    },
}

CRITERIA = ("EMPTY_MARKER_DISTINCT_FROM_ZERO", "PIPELINE_STAGES_VISIBLE",
            "PROGRESSIVE_REVEAL_PASS", "REFUSAL_TITLE_MATCHES_CAUSE",
            "LAYOUT_PASS", "RESPONSIVE_PASS")


def build(captures: dict) -> dict:
    by_fixture: dict[str, list[dict]] = {}
    for rec in captures["records"]:
        by_fixture.setdefault(rec["fixture"], []).append(rec)

    fixtures = []
    for fid, recs in by_fixture.items():
        rv = REVIEW.get(fid)
        if rv is None:
            raise SystemExit(f"Thiếu phán quyết NGƯỜI cho fixture {fid}")
        auto = {
            "no_horizontal_overflow": all(
                not r["audit"]["page_overflows_horizontally"] for r in recs),
            "no_clipped_elements": all(r["audit"]["clipped_elements"] == 0 for r in recs),
            "no_phantom_stroke_none": all(
                r["audit"]["phantom_stroke_none"] == 0 for r in recs),
            "viewports": sorted({r["viewport"] for r in recs}),
            "images": len(recs),
        }
        fixtures.append({
            "fixture": fid, "finding": rv["finding"], "status": rv["status"],
            "human_note": rv["note"],
            "defect_found_during_review": rv.get("defect_found_here", False),
            "automated_support": auto,
            "png": sorted(r["png"] for r in recs),
        })

    statuses = {f["status"] for f in fixtures}
    return {
        "wave": "M17 W2B-PATCH §E — review thị giác CÓ MỤC TIÊU",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "renderer": "database + learner notice",
        "criteria": list(CRITERIA),
        "scope_note": (
            "CHỈ chụp lại phần bản vá động tới (ô trống, pipeline nhiều tầng, ba "
            "thông điệp từ chối). 42 ảnh toàn danh mục của RC1 §E KHÔNG chạy "
            "lại vì cấu trúc renderer các family khác không đổi."
        ),
        "measurement_note": (
            "Viewport đặt TRƯỚC khi trang dựng, nạp lại trang cho từng viewport "
            "— KHÔNG lặp lại artefact phép đo VIS-003 của RC1 §E1."
        ),
        "reading_note": (
            "`engine.result_rows`/`engine.aggregate` trong captures.json là "
            "trạng thái engine ĐÃ TÍNH SẴN (engine tất định tính một lần khi "
            "init), KHÔNG phải bằng chứng 'đã hiển thị'. Việc hé lộ dần được "
            "kiểm bằng MẮT trên ảnh initial/mid/final."
        ),
        "images_total": len(captures["records"]),
        "verdict": "REAL_VISUAL" if statuses == {"REAL_VISUAL"} else sorted(statuses),
        "fixtures": sorted(fixtures, key=lambda f: f["fixture"]),
    }


def write_md(out: Path, data: dict) -> None:
    L = [f"# {data['wave']}", "",
         f"- Renderer: **{data['renderer']}** · ảnh **{data['images_total']}** "
         f"· phán quyết chung: **{data['verdict']}**",
         f"- Phạm vi: {data['scope_note']}",
         f"- Phép đo: {data['measurement_note']}",
         f"- Cách đọc số: {data['reading_note']}", "",
         "| Fixture | Finding | Trạng thái | Ảnh | Lỗi phát hiện khi review |",
         "|---|---|---|---|---|"]
    for f in data["fixtures"]:
        L.append(f"| `{f['fixture']}` | {f['finding']} | **{f['status']}** | "
                 f"{f['automated_support']['images']} | "
                 f"{'CÓ' if f['defect_found_during_review'] else '—'} |")
    L += ["", "## Quan sát của người review", ""]
    for f in data["fixtures"]:
        L.append(f"### {f['fixture']} — {f['status']}")
        L.append(f["human_note"])
        a = f["automated_support"]
        L.append("")
        L.append(f"*Assertion hỗ trợ (trình duyệt thật):* tràn ngang "
                 f"{'KHÔNG' if a['no_horizontal_overflow'] else 'CÓ'} · phần tử "
                 f"bị cắt {'0' if a['no_clipped_elements'] else '>0'} · "
                 f"stroke=none (token ma) "
                 f"{'0' if a['no_phantom_stroke_none'] else '>0'} · viewport "
                 f"{', '.join(a['viewports'])}.")
        L.append("")
    (out / "w2b_patch_visual_review.md").write_text("\n".join(L) + "\n", encoding="utf-8")


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--out", default="../docs/evaluation/m17/w2b-patch")
    args = p.parse_args()
    out = Path(args.out).resolve()
    captures = json.loads((out / "visual" / "captures.json").read_text(encoding="utf-8"))
    data = build(captures)
    (out / "w2b_patch_visual_review.json").write_text(
        json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    write_md(out, data)
    print(f"Verdict: {data['verdict']} · {data['images_total']} ảnh · "
          f"{len(data['fixtures'])} fixture")
    return 0


if __name__ == "__main__":
    sys.exit(main())
