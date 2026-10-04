# -*- coding: utf-8 -*-
"""W19 — sinh docs/evaluation/HISTORICAL_REPORTS.md: danh sách ĐÓNG các báo cáo wave nằm ở gốc docs/.

Chạy từ gốc kho:  backend/.venv/Scripts/python.exe <run>/diagnostics/build_report_catalog.py
Một dòng / báo cáo: chủ đề (luật tên tất định bên dưới, khớp đầu tiên thắng), tiêu đề H1, ngày commit đầu, wave và
CORRECTED_BY nếu EVIDENCE_INDEX đăng ký báo cáo ấy. Báo cáo = mọi docs/*.md không thuộc 11 tài liệu chuẩn tắc và
không thuộc danh sách tài liệu dự án (cùng hai tập mà audit_docs_information_architecture.py dùng).
Danh sách đóng: wave mới viết báo cáo trong thư mục run của nó, không thêm file vào gốc docs/.
"""
from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[6]
sys.path.insert(0, str(ROOT / "backend" / "scripts"))
import audit_docs_information_architecture as A  # noqa: E402

CHU_DE = [
    ("Khoá luận: nghiệm thu, kết quả, phát hành", r"^(THESIS_|FINAL_|PRODUCT_|DISPLAY_NAME_|RESEARCH_GAP)"),
    ("Đề bài từ ảnh", r"^(PHOTO_|VISION_|IMAGE_|C0[1-3]_|B02_|REAL_PHOTO)"),
    ("Compiler tất định và các họ hình", r"^(PRIMITIVE_|SECOND_FAMILY|PRISM_|GENERIC_|CUBOID_|RECTANGULAR_|GEOMETRY_FACT|"
     r"MISSING_FAMILY|SCHEMA_SYNC|REMOTE_MAIN)"),
    ("Hình cong và nghiệm thu V3", r"(CURVED|^V3_|OBLIQUE|CENTER_RADIUS|RADIUS|SCALAR_AXIS|ELLIPSE|CONE_|CYLINDER|SPHERE)"),
    ("Đo chính xác, khối lõm, thiết diện, mặt phẳng", r"^(NONCONVEX_|SECTION_|EXACT_|ANGLE_|PLANE_|VOLUME_|FRAME_|SPATIAL_)"),
    ("Scene3D, mô phỏng và trình bày", r"^(SCENE3D_|SIMULATION_|GEOMETRIC_DEPENDENCY|REACT_|PRESENTATION_|PEDAGOGICAL_|W4B)"),
    ("Tổng hợp chương trình, analyze, đo live", r"^(SYNTHESIS_|MULTICASE_|MODEL_|AUDIT_|MINIMAL_|CARD_|ANALYZE_|"
     r"STRUCTURED_|SEGMENT_|POINT_|DERIVED_|OBLIGATION_|DIVIDE_|RATIO_|OPERAND_|FRESH_|RETRY_|COMPLETION_|N04_|G4_|"
     r"BENCHMARK_|SMALL_|SAFE_|ACCEPTANCE_|PROVENANCE_|MECHANISM_|CACHE_|SEMANTIC_|VERIFICATION_|NAME_|TRANSLATION_)"),
    ("Tài liệu, phạm vi, vận hành kho", r"^(DOCS_|POST_WAVE|DOCKER_|SCOPE_|CURRENT_ARCH|CLASSROOM_|W12_|LEGACY_|STATUS_)"),
]


def git(*a: str) -> str:
    return subprocess.run(["git", "-c", "core.quotePath=false", *a], cwd=ROOT, capture_output=True, text=True,
                          encoding="utf-8", check=True).stdout


def main() -> int:
    giu = {Path(s["canonical_path"]).name for s in A.CANONICAL_DOMAINS.values()} | set(A.PROJECT_DOCS)
    bao_cao = sorted(p.name for p in (ROOT / "docs").glob("*.md") if p.name not in giu)
    ev = (ROOT / "docs" / "EVIDENCE_INDEX.md").read_text(encoding="utf-8")
    dang_ky: dict[str, tuple[str, str]] = {}
    for blk in ev.split("## WAVE_ID = ")[1:]:
        wave = blk.splitlines()[0].strip()
        rep = re.search(r"\*\*REPORT:\*\*\s*`?(docs/[^\s`]+\.md)", blk)
        cor = re.search(r"\*\*CORRECTED_BY:\*\*\s*`?([A-Z0-9_\-]+)", blk)
        if rep:
            dang_ky[Path(rep.group(1)).name] = (wave, cor.group(1) if cor and cor.group(1) != "NONE" else "")
    nhom: dict[str, list[str]] = {t: [] for t, _ in CHU_DE} | {"Khác": []}
    for n in bao_cao:
        stem = n[:-3]
        t = next((t for t, rx in CHU_DE if re.search(rx, stem)), "Khác")
        tieu_de = next((l.lstrip("# ").strip() for l in (ROOT / "docs" / n).read_text(encoding="utf-8").splitlines()
                        if l.startswith("#")), "")
        tieu_de = tieu_de.replace("|", "\\|")[:110]
        ngay = git("log", "--diff-filter=A", "--follow", "--format=%as", "--", f"docs/{n}").split()[-1:] or ["?"]
        wave, cor = dang_ky.get(n, ("", ""))
        nhom[t].append(f"| [`{stem}`](../{n}) | {tieu_de} | {ngay[0]} | {wave or '—'} | {cor or '—'} |")
    out = [
        "# HISTORICAL_REPORTS — báo cáo wave ở gốc `docs/` (danh sách đóng)",
        "",
        "> Sinh bởi `docs/evaluation/geometry/runs/w19-docs-organization/diagnostics/build_report_catalog.py` (W19).",
        "> Các báo cáo này là **evidence đã đóng băng**: giữ nguyên nội dung và đường dẫn (AGENTS.md §4) — đọc chúng",
        "> như bằng chứng *tại thời điểm đo*. Đính chính đi bằng wave mới và chuỗi `CORRECTED_BY` ở",
        "> [`../EVIDENCE_INDEX.md`](../EVIDENCE_INDEX.md); cột *Đính chính bởi* chép từ đó.",
        ">",
        "> **Danh sách đóng.** Từ W19, `audit_docs_information_architecture.py` (`audit_docs_layout`) từ chối mọi file",
        "> `docs/*.md` không thuộc 11 tài liệu chuẩn tắc, danh sách tài liệu dự án, hoặc bảng này. Wave mới viết",
        "> `REPORT.md`/`HANDOFF.md` trong thư mục run của nó (`docs/evaluation/geometry/runs/<run>/`, đặt tên theo",
        "> [`RUN_NAMING.md`](RUN_NAMING.md)). Chủ đề xếp bằng luật tên tất định — là chỗ bắt đầu tìm, không phải phân loại",
        "> học thuật.",
        "",
        f"Tổng: **{len(bao_cao)}** báo cáo · đăng ký trong EVIDENCE_INDEX: **{sum(1 for n in bao_cao if n in dang_ky)}**.",
        "",
    ]
    for t, rows in nhom.items():
        if not rows:
            continue
        out += [f"## {t} ({len(rows)})", "", "| Báo cáo | Tiêu đề | Thêm vào kho | Wave (EVIDENCE_INDEX) | Đính chính bởi |",
                "|---|---|---|---|---|", *rows, ""]
    (ROOT / "docs" / "evaluation" / "HISTORICAL_REPORTS.md").write_text("\n".join(out), encoding="utf-8", newline="\n")
    print({t: len(r) for t, r in nhom.items()}, "total", len(bao_cao))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
