"""cuboid-final-review — move informatics-era and removed-code sections of living docs, verbatim, into legacy companions.

Every block is cut from the BASE blob of its source (`git show BASE:<source>`), never from the working file, so the split
is reproducible and byte-verifiable:

    cd backend && PYTHONIOENCODING=utf-8 .venv/Scripts/python.exe \
        ../docs/evaluation/geometry/runs/cuboid-final-review/diagnostics/split_history_cfr.py --plan|--apply|--verify

--plan    list the blocks of every source (line ranges at BASE, sha256)
--apply   only while a source still equals its BASE blob: write it back with each block replaced by its stub, write the
          companion (header + every block verbatim, in BASE order) and ../inventory/HISTORY_SPLIT.json
--verify  recompute the blocks from BASE: sha256 equals the record; each block appears verbatim in its companion and no
          longer in the living doc, whose pointer stub is still there; every non-blank BASE line is still in the living
          doc or in the companion
"""
from __future__ import annotations

import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[6]
RUN = "docs/evaluation/geometry/runs/cuboid-final-review"
RECORD = ROOT / RUN / "inventory" / "HISTORY_SPLIT.json"
BASE = "4048ff83d14ad2a1fcd940d127590ca777dbc7cf"
DATE = "2026-10-05"
SPLIT_TOOL = f"{RUN}/diagnostics/split_history_cfr.py"


def git(*args: str) -> str:
    return subprocess.run(["git", *args], cwd=ROOT, capture_output=True, text=True, encoding="utf-8",
                          check=True).stdout


def base_lines(source: str) -> list[str]:
    raw = subprocess.run(["git", "show", f"{BASE}:{source}"], cwd=ROOT, capture_output=True, check=True).stdout
    return raw.decode("utf-8").splitlines(keepends=True)


def find(lines: list[str], pattern: str, start: int = 0) -> int:
    """0-based index of the first line at or after `start` matching `pattern` (regex, anchored at line start)."""
    rx = re.compile(pattern)
    for i in range(start, len(lines)):
        if rx.match(lines[i]):
            return i
    raise ValueError(f"anchor not found: {pattern!r}")


def section_end(lines: list[str], i: int) -> int:
    """Exclusive end of the markdown section whose heading is lines[i]: the next heading of the same or higher level."""
    level = len(lines[i]) - len(lines[i].lstrip("#"))
    for j in range(i + 1, len(lines)):
        m = re.match(r"(#+) ", lines[j])
        if m and len(m.group(1)) <= level:
            return j
    return len(lines)


# --- CODE_INDEX: entries whose subject no longer exists -------------------------------------------------------------

def _subject_exists(heading: str) -> bool | None:
    """Whether the first path named in an entry heading exists under any of the bases the index writes paths
    relative to (globs allowed); None when the heading names no path."""
    toks = [t.split("::")[0].strip() for t in re.findall(r"`([^`]+)`", heading)]
    toks = [t for t in toks if "/" in t or re.search(r"\.(py|ts|tsx|mjs|js|json|md|css)$", t)]
    if not toks:
        return None
    bases = ("", "backend/app/", "backend/", "frontend/src/", "frontend/src/simulations/", "frontend/")
    return any(any(ROOT.glob(b + toks[0])) for b in bases)


def code_index_blocks(lines: list[str]) -> list[tuple[int, int, str]]:
    blocks: list[tuple[int, int, str]] = []
    section = ""
    i = 0
    while i < len(lines):
        line = lines[i]
        if line.startswith("## "):
            section = line[3:]
            if line.startswith("## ⛔"):
                end = section_end(lines, i)
                blocks.append((i, end, "whole section about removed code (⛔)"))
                i = end
                continue
        if line.startswith("### ") and not section.startswith(("0", "⛔")):
            end = section_end(lines, i)
            heading = line.strip()
            marked = "⛔" in heading or "ĐÃ GỠ" in heading
            if marked or _subject_exists(heading) is False:
                blocks.append((i, end, "entry of removed code" + (" (heading marked removed)" if marked else "")))
                i = end
                continue
        i += 1
    return blocks


# --- block specs ----------------------------------------------------------------------------------------------------

def specs() -> dict[str, dict]:
    """Per source: companion path, why, and blocks as (start_index, end_index_exclusive, reason, stub)."""
    out: dict[str, dict] = {}

    # STATUS_LEDGER ---------------------------------------------------------------------------------------------------
    src = "docs/STATUS_LEDGER.md"
    L = base_lines(src)
    comp = "docs/legacy/STATUS_LEDGER_INFORMATICS_ERA.md"
    link = comp.removeprefix("docs/")
    s1, s0 = find(L, r"## 1\. Kiến trúc"), find(L, r"## 0\. KHOÁ PHẠM VI")
    t0 = find(L, r"### TÊN ĐỀ TÀI CANONICAL \(chốt 2026-08-18\)")
    t1 = find(L, r"### §0-2026-08-24")
    f0, f1 = find(L, r"## 4f\."), find(L, r"## 6\. ")
    nav = (
        f"> **Điều hướng ({DATE}, `cuboid-final-review`).** Khoá phạm vi hiện hành: **§0-2026-08-24** (dưới). Lịch sử\n"
        f"> các wave hình học: **§6**. Các bảng trạng thái của giai đoạn Tin học — §1 Kiến trúc & năng lực · §2 Tương tác\n"
        f"> theo miền · §3 Sản phẩm & lớp học · §4 Đo lường & chất lượng · §4b–§4e Wave 5–8 · §4f Wave 10 · §4g và các\n"
        f"> mục W12 · §4h vNext · §5 Phủ chương trình — cùng tên đề tài 2026-08-18 đã hết hiệu lực, được chuyển\n"
        f"> **nguyên văn** sang [`{link}`]({link}). Không thêm dòng mới vào các mục ấy.\n\n")
    out[src] = {"companion": comp, "why": "bảng trạng thái của sản phẩm Tin học (đã gỡ ở LEGACY_INFORMATICS_REMOVAL, "
                "2026-09-02) và tên đề tài 2026-08-18 đã hết hiệu lực từ §0-2026-08-24", "blocks": [
        (s1, s0, "status tables §1–§4e of the informatics product", nav),
        (t0, t1, "topic lock 2026-08-18, expired by §0-2026-08-24",
         L[t0].rstrip("\n") + " — HẾT HIỆU LỰC\n\n"
         f"> Thay bởi §0-2026-08-24 ngay dưới. Nguyên văn khoá phạm vi cũ: [`{link}`]({link}).\n\n"),
        (f0, f1, "status tables §4f–§4h, W12 sections and §5 of the informatics product", ""),
    ]}

    # COVERAGE --------------------------------------------------------------------------------------------------------
    src = "docs/COVERAGE.md"
    L = base_lines(src)
    comp = "docs/legacy/COVERAGE_INFORMATICS_ERA.md"
    link = comp.removeprefix("docs/")
    c1, c2 = find(L, r"## 1\. Nguồn chương trình"), find(L, r"## 2\. Nguyên tắc sư phạm")
    c3, c5 = find(L, r"## 3\. Ma trận"), find(L, r"## 5\. Mức độ phức tạp")
    c6 = find(L, r"## 6\. `practice_activity`")
    new1 = (
        "## 1. Độ phủ và tuyên bố hiện hành — đọc trước khi viết một con số độ phủ\n\n"
        "Từ đổi đề 2026-08-24 (`STATUS_LEDGER §0-2026-08-24`), độ phủ của sản phẩm và câu được/không được viết nằm ở:\n\n"
        "- [`research/GEOMETRY_CURRICULUM_COVERAGE.md`](research/GEOMETRY_CURRICULUM_COVERAGE.md) — độ phủ chương\n"
        "  trình hình học không gian THPT (`backend/tests/geometry/test_curriculum_coverage.py` đọc);\n"
        "- [`research/CLAIM_EVIDENCE_MAP.md`](research/CLAIM_EVIDENCE_MAP.md) §3 — **câu không được viết**, và mỗi\n"
        "  tuyên bố với bằng chứng, mức và giới hạn của nó;\n"
        "- năng lực sản phẩm: `backend/app/simulation/product_capability.py`; họ hình:\n"
        "  `docs/evaluation/geometry/missing-family-roadmap-refresh/CAPABILITY_MATRIX.json`.\n\n"
        "§2 (nguyên tắc sư phạm) và §5 (mức L1–L4) dưới đây giữ **nguyên văn** vì mã và tài liệu trích chúng theo số\n"
        "mục (§2.6, §2.7, §5). Phần của giai đoạn Tin học — nguồn SGK Tin học và tuyên bố cấm của nó (§1, §1b cũ),\n"
        "ma trận giá trị theo chủ đề (§3), phủ năng lực theo miền (§4, §4b), `practice_activity`, chủ đề không mô\n"
        f"phỏng, 2D/3D, bộ đề, flagship, tái sử dụng liên miền và đóng băng (§6–§12) — chép nguyên văn ở\n"
        f"[`{link}`]({link}) ({DATE}, `cuboid-final-review`).\n\n---\n\n")
    out[src] = {"companion": comp, "why": "nguồn SGK Tin học, ma trận và bộ đề của sản phẩm Tin học; độ phủ hiện hành "
                "ở research/GEOMETRY_CURRICULUM_COVERAGE.md và research/CLAIM_EVIDENCE_MAP.md §3", "blocks": [
        (c1, c2, "§1 and §1b: informatics textbook provenance and its claims", new1),
        (c3, c5, "§3, §4, §4b: value matrix and capability coverage of the informatics catalogue",
         f"## 3–4. (giai đoạn Tin học)\n\nMa trận giá trị theo chủ đề (§3) và phủ năng lực theo miền (§4, §4b): nguyên "
         f"văn ở [`{link}`]({link}).\n\n---\n\n"),
        (c6, len(L), "§6–§12 of the informatics catalogue",
         f"## 6–12. (giai đoạn Tin học)\n\n`practice_activity`, chủ đề không mô phỏng, Dijkstra, 2D/3D, bộ đề, flagship, "
         f"tái sử dụng liên miền, ngân sách object, đóng băng: nguyên văn ở [`{link}`]({link}).\n"),
    ]}

    # CORRECTNESS -----------------------------------------------------------------------------------------------------
    src = "docs/CORRECTNESS.md"
    L = base_lines(src)
    comp = "docs/legacy/CORRECTNESS_INFORMATICS_ERA.md"
    link = comp.removeprefix("docs/")
    p0, p1 = find(L, r"\*\*Precedent kiến trúc:\*\*"), find(L, r"## 2b\.")
    k3, k4 = find(L, r"## 3\. Taxonomy"), find(L, r"## 4\. Ba luật")
    k5, k7 = find(L, r"## 5\. Phân loại A/B/C"), find(L, r"## 7\. Chính sách kiểm thử")
    lv0 = find(L, r"- `live\.py` \*\*bắt buộc", k7)
    lv1 = find(L, r"Metric `gap_gate_recall`", k7)
    k8 = find(L, r"## 8\. Trạng thái known-gap")
    out[src] = {"companion": comp, "why": "tiền lệ, taxonomy, phân loại và chính sách của các miền Tin học đã gỡ; "
                "nguyên tắc chung (§1, §1a, §2, §2b, §4, §7) ở lại", "blocks": [
        (p0, p1, "§2 precedent: what-if branch of the removed algorithm domain",
         f"*Tiền lệ của giai đoạn Tin học (nhánh what-if của miền `algorithm`, đã gỡ): nguyên văn ở [`{link}`]({link}).*\n\n"),
        (k3, k4, "§3 PatchResult taxonomy of the removed generic DSL edit path",
         L[k3] + f"\n> Đường patch/edit (M7.14) và `InteractionFeedback` của miền generic đã gỡ cùng miền Tin học. Nguyên "
         f"văn mục này: [`{link}`]({link}) (`frontend/src/llm/client.ts` còn trích nó).\n\n"),
        (k5, k7, "§5 A/B/C classification and §6 node/edge claims of the informatics system",
         f"## 5–6. (giai đoạn Tin học)\n\nPhân loại A/B/C toàn hệ (§5) và giới hạn tuyên bố của node/edge generic (§6): "
         f"nguyên văn ở [`{link}`]({link}).\n\n"),
        (lv0, find(L, r"\s*$", find(L, r"  số liệu → full", lv0)) + 1, "§7: the removed live.py runner and its suites",
         "- Lượt gọi provider thật là opt-in (`ALLOW_LIVE_AI=1`), chạy bằng các script `backend/scripts/run_*` /\n"
         "  `probe_*`, với ngân sách và luật dừng đăng ký trước (`AGENTS.md`, *Đo lường có trần*). Runner `live.py`\n"
         f"  của giai đoạn Tin học đã gỡ: nguyên văn ở [`{link}`]({link}).\n\n"),
        (lv1, k8, "§7: gap_gate_recall metric of the removed capability gate", ""),
        (k8, len(L), "§8 known-gap roadmap and §9 binary_search policy",
         f"## 8–9. (giai đoạn Tin học)\n\nLộ trình known-gap của DSL (§8) và chính sách normalize-not-refuse của\n"
         f"`binary_search` (§9, `backend/app/main.py` còn trích): nguyên văn ở [`{link}`]({link}).\n"),
    ]}

    # POST_THESIS_BACKLOG ---------------------------------------------------------------------------------------------
    src = "docs/POST_THESIS_BACKLOG.md"
    L = base_lines(src)
    comp = "docs/legacy/POST_THESIS_BACKLOG_INFORMATICS_ERA.md"
    link = comp.removeprefix("docs/")
    b0, b1 = find(L, r"## Cam kết cơ chế"), find(L, r"## Các mục khác")
    m0 = find(L, r"- Môn học khác ngoài Tin học THPT", b1)
    out[src] = {"companion": comp, "why": "ý tưởng của sản phẩm Tin học (quyết định thuật toán trên sân khấu, đợt "
                "nâng trải nghiệm toàn danh mục 23 target) — phạm vi đã bỏ từ 2026-08-24", "blocks": [
        (b0, b1, "two informatics-era idea sections",
         f"*Hai mục ý tưởng của giai đoạn Tin học (cam kết cơ chế ở điểm quyết định thuật toán; đợt nâng trải nghiệm toàn "
         f"danh mục, 2026-08-16) — phạm vi đã bỏ từ 2026-08-24: nguyên văn ở [`{link}`]({link}).*\n\n"),
        (m0, m0 + 1, "scope line of the informatics topic",
         "- Chủ đề ngoài hình học không gian Toán 11–12 — `detect_domain` từ chối (fail closed).\n"),
    ]}

    # DESIGN_BRIEF ----------------------------------------------------------------------------------------------------
    src = "docs/DESIGN_BRIEF.md"
    L = base_lines(src)
    comp = "docs/legacy/DESIGN_BRIEF_INFORMATICS_ERA.md"
    link = comp.removeprefix("docs/")
    d0 = find(L, r"\*\*Tên đề tài:\*\*")
    d1 = find(L, r"> \*\*Câu một dòng", d0)
    n0 = find(L, r"\*\*Người học:\*\*")
    n1 = find(L, r"---", n0)
    w0, w1 = find(L, r"### Bố cục Workspace"), find(L, r"## 3\. Bảy ràng buộc")
    h4, h5 = find(L, r"## 4\. Hợp đồng hiển thị"), find(L, r"## 5\. Ngôn ngữ thị giác")
    h8, h9 = find(L, r"## 8\. Chỗ đang cần thiết kế"), find(L, r"## 9\. ")
    out[src] = {"companion": comp, "why": "mô tả sản phẩm, bố cục workspace, hợp đồng hiển thị theo miền và việc thiết "
                "kế của giai đoạn Tin học; các ràng buộc §3, ngôn ngữ thị giác, giọng văn và quy trình kiểm ở lại", "blocks": [
        (d0, d1, "§1: informatics topic and the browser-engine sentence",
         "**Tên đề tài:** *Nghiên cứu và xây dựng hệ thống mô phỏng 3D hình học không gian* (`STATUS_LEDGER\n"
         "§0-2026-08-24`).\n\n"
         "Học sinh **gõ đề hình học không gian bằng tiếng Việt** (hoặc chụp ảnh đề: hệ chép lại, học sinh duyệt/sửa trước\n"
         "khi gửi). LLM **chỉ đọc đề** và viết các bước dựng hình bằng **tên** của vật đã dựng — không bao giờ phán toạ\n"
         "độ. **Engine hình học tất định** ở máy chủ dựng hình chính xác và kiểm định; trình duyệt diễn hoạt từng bước\n"
         "trong Scene3D (`ARCHITECTURE_MAP.md` §1–§2).\n\n"),
        (n0, n1, "§1: informatics learners and catalogue scale",
         "**Người học:** học sinh THPT Việt Nam, Toán 11–12, phần hình học không gian. Không phải lập trình viên. **Mọi\n"
         "chữ trên màn hình là tiếng Việt.**\n\n"
         "**Quy mô hiện tại:** một mô phỏng sản phẩm (`generic.semantic_program`); họ hình được hỗ trợ:\n"
         "`backend/app/simulation/product_capability.py`.\n\n"
         f"*(Ba đoạn mô tả sản phẩm Tin học — tên đề tài 2026-08-18, người học môn Tin học, quy mô 19 mô phỏng / 6 miền —\n"
         f"nguyên văn ở [`{link}`]({link}).)*\n\n"),
        (w0, w1, "§2: workspace layout of the informatics stage",
         "### Bố cục Workspace\n\n"
         "Workspace là `Scene3DExplorer`: sân khấu 3D, dòng thời gian từng bước, vùng soi chi tiết của đại lượng đang\n"
         "chọn và lời giải (thu gọn mặc định) — mô tả và chủ sở hữu ở `CODE_INDEX.md` (miền hình học). Bảng bố cục hai\n"
         f"cột của giai đoạn Tin học: nguyên văn ở [`{link}`]({link}).\n\n---\n\n"),
        (h4, h5, "§4: display contracts of the removed domains",
         L[h4] + "\nHợp đồng hiển thị hiện hành của miền hình học: định danh cạnh, chủ sở hữu thị giác và nét khuất ở\n"
         "[`architecture/OCCLUSION_AND_SCENE_IDENTITY_AMENDMENT.md`](architecture/OCCLUSION_AND_SCENE_IDENTITY_AMENDMENT.md);\n"
         "bất biến khoá bằng test ở `ARCHITECTURE_MAP.md` §5 (#31, #35, #38, #39). Bảng hợp đồng theo bảy miền Tin học\n"
         f"và đoạn *Về 3D*: nguyên văn ở [`{link}`]({link}).\n\n---\n\n"),
        (h8, h9, "§8: design backlog of the informatics product",
         L[h8] + "\nYêu cầu giao diện đang chờ (chưa làm) ghi ở [`ROADMAP.md`](ROADMAP.md). Bảng việc thiết kế của giai "
         f"đoạn Tin học (cây, bảng/CSDL) và danh sách đóng băng của nó: nguyên văn ở [`{link}`]({link}).\n\n---\n\n"),
    ]}

    # ARCHITECTURE_MAP ------------------------------------------------------------------------------------------------
    src = "docs/ARCHITECTURE_MAP.md"
    L = base_lines(src)
    comp = "docs/legacy/ARCHITECTURE_MAP_INFORMATICS_ERA.md"
    link = comp.removeprefix("docs/")
    a0, a1 = find(L, r"\*\*Specialized ↔ Generic DSL\.\*\*"), find(L, r"\*\*Canonical ↔ Learner\.\*\*")
    e7, e8 = find(L, r"## 7\. Điểm mở rộng"), find(L, r"## 8\. Anti-pattern")
    t2, t10 = find(L, r"- \*\*Tầng 2 — pattern reuse\*\*"), find(L, r"## 10\. ")
    out[src] = {"companion": comp, "why": "trục specialized/DSL và interaction/edit, điểm mở rộng, tầng cache pattern "
                "reuse và hướng tương lai của hệ Tin học đã gỡ", "blocks": [
        (a0, a1, "§6: specialized/DSL and interaction/edit axes of the removed system",
         f"*Hai trục của hệ Tin học — specialized ↔ generic DSL, interaction ↔ edit (EditPolicy v1) — đã gỡ cùng mã:\n"
         f"nguyên văn ở [`{link}`]({link}).*\n\n"),
        (e7, e8, "§7: extension points of the removed system",
         L[e7] + "\n"
         "- **Năng lực hình học mới** (phép dựng, phép đo, quan hệ): mở IR — lược đồ\n"
         "  `backend/app/simulation/semantic_program/contract.py`, `ir_static_check.py`, cầu nối `geometry_exec.py`;\n"
         "  sinh lại hai bản lược đồ bằng `backend/scripts/export_semantic_program_schema.py` (`test_schema_sync.py`).\n"
         "  Lược đồ, thẻ văn phạm (`grammar_card.py`), prompt (`backend/app/ai/skills/*.md`) và bảng năng lực là bề mặt\n"
         "  mô hình: đổi chúng thì phải đo lại. Hỏi trước: thiếu năng lực thật, hay chỉ thiếu cách nói cho mô hình biết?\n"
         "- **Họ hình mới**: đi qua `backend/app/simulation/product_capability.py` và\n"
         "  `docs/evaluation/geometry/missing-family-roadmap-refresh/CAPABILITY_MATRIX.json` trước khi viết mã.\n"
         "- **Lý do từ chối mới**: mã lý do ở chặng sinh ra nó, câu cho người học ở `backend/app/learner_messages.py`, nhãn\n"
         "  ở `frontend/src/components/SimulationWorkspace.tsx`; không lộ định danh kĩ thuật\n"
         "  (`frontend/src/components/ui-hygiene.test.ts`).\n"
         "- **Điều khiển giao diện mới**: không khai năng lực thì không có điều khiển — vắng mặt, không mờ đi (chống\n"
         "  affordance rỗng, `DESIGN_BRIEF.md` §3.2).\n\n"
         f"Năm điểm mở rộng của hệ Tin học (`catalog.py`, manifest DSL, `dataset.py`, capability của `SimulationModule`,\n"
         f"renderer theo module): nguyên văn ở [`{link}`]({link}).\n\n"),
        (t2, t10, "§9: pattern-reuse tier and the M7.14 edit path",
         f"- *Tầng 2 (pattern reuse, `patterns.py`) và đường edit M7.14 đã gỡ cùng hệ Tin học: nguyên văn ở\n"
         f"  [`{link}`]({link}).*\n\n"),
        (t10, len(L), "§10: future directions of the informatics system",
         L[t10] + f"\nHướng phát triển hiện hành: [`ROADMAP.md`](ROADMAP.md) và [`POST_THESIS_BACKLOG.md`](POST_THESIS_BACKLOG.md). "
         f"Hai hướng của hệ Tin học (M7.15, `code_experiment`): nguyên văn ở [`{link}`]({link}).\n"),
    ]}

    # CODE_INDEX ------------------------------------------------------------------------------------------------------
    src = "docs/CODE_INDEX.md"
    L = base_lines(src)
    comp = "docs/legacy/CODE_INDEX_REMOVED_ENTRIES.md"
    out[src] = {"companion": comp, "why": "mục mô tả mã đã gỡ (miền Tin học, DSL, công cụ và module đã xoá); chỉ mục "
                "truy vết ngắn của mã đã gỡ vẫn ở §0j", "blocks": [
        (s, e, reason, "") for s, e, reason in code_index_blocks(L)]}
    return out


def companion_text(source: str, spec: dict, L: list[str], blob: str) -> str:
    back = "../" + source.removeprefix("docs/")
    head = (
        f"# {Path(source).name} — phần đã tách, chép nguyên văn\n\n"
        f"> Tách khỏi [`{source.removeprefix('docs/')}`]({back}) ở run `cuboid-final-review` ({DATE}): {spec['why']}.\n"
        f"> Nguồn: `{source}` tại commit `{BASE}` (blob `{blob}`). Mỗi khối dưới đây là **nguyên văn** (byte-identical)\n"
        f"> các dòng ghi trong chú thích của nó, theo thứ tự của bản gốc. Đây là lịch sử: không sửa, không thêm.\n"
        f"> Đường dẫn tương đối trong các khối viết cho thư mục `docs/`, nên từ `legacy/` chúng trỏ lệch một cấp\n"
        f"> (`README.md`). Kiểm lại: `{SPLIT_TOOL} --verify`.\n\n")
    parts = [head]
    for n, (s, e, reason, _stub) in enumerate(spec["blocks"], 1):
        text = "".join(L[s:e])
        parts.append(f"<!-- khối {n}/{len(spec['blocks'])} · dòng {s + 1}–{e} của bản gốc · {reason} · sha256 "
                     f"{hashlib.sha256(text.encode('utf-8')).hexdigest()} -->\n")
        parts.append(text if text.endswith("\n") else text + "\n")
        parts.append(f"<!-- hết khối {n} -->\n\n")
    return "".join(parts).rstrip("\n") + "\n"


def living_text(spec: dict, L: list[str]) -> str:
    out: list[str] = []
    cursor = 0
    for s, e, _reason, stub in sorted(spec["blocks"]):
        assert s >= cursor, "blocks overlap"
        out.extend(L[cursor:s])
        out.append(stub)
        cursor = e
    out.extend(L[cursor:])
    return "".join(out)


def main() -> int:
    mode = (sys.argv[1:] or ["--plan"])[0]
    allspecs = specs()
    record = {"schema_version": "history-split/1", "run_id": "cuboid-final-review", "base_commit": BASE,
              "tool": SPLIT_TOOL, "sources": {}}
    bad: list[str] = []
    for source, spec in allspecs.items():
        L = base_lines(source)
        blob = git("rev-parse", f"{BASE}:{source}").strip()
        blocks = []
        for s, e, reason, _stub in spec["blocks"]:
            text = "".join(L[s:e])
            blocks.append({"base_lines": [s + 1, e], "line_count": e - s, "reason": reason,
                           "heading": L[s].strip()[:120],
                           "sha256": hashlib.sha256(text.encode("utf-8")).hexdigest()})
        moved = sum(b["line_count"] for b in blocks)
        record["sources"][source] = {"base_blob": blob, "base_line_count": len(L), "companion": spec["companion"],
                                     "why": spec["why"], "moved_line_count": moved, "blocks": blocks}
        if mode == "--plan":
            print(f"{source}: {len(blocks)} blocks, {moved}/{len(L)} lines -> {spec['companion']}")
            for b in blocks:
                print(f"   {b['base_lines'][0]:>5}-{b['base_lines'][1]:<5} {b['line_count']:>4}  {b['heading'][:95]}")
        elif mode == "--apply":
            living = ROOT / source
            # the working copy may carry CRLF (core.autocrlf); git normalises it to the LF blob
            if living.read_bytes().replace(b"\r\n", b"\n") != "".join(L).encode("utf-8"):
                bad.append(f"{source}: not at its BASE blob — refusing to overwrite later edits")
                continue
            (ROOT / spec["companion"]).write_text(companion_text(source, spec, L, blob), encoding="utf-8", newline="\n")
            living.write_text(living_text(spec, L), encoding="utf-8", newline="\n")
        elif mode == "--verify":
            comp_text = (ROOT / spec["companion"]).read_text(encoding="utf-8")
            live_text = (ROOT / source).read_text(encoding="utf-8")
            for b, (s, e, _reason, stub) in zip(blocks, spec["blocks"]):
                text = "".join(L[s:e])
                if text not in comp_text:
                    bad.append(f"{source} lines {s + 1}-{e}: not verbatim in {spec['companion']}")
                if e - s > 1 and text in live_text:
                    bad.append(f"{source} lines {s + 1}-{e}: still in the living doc")
                if stub not in live_text:
                    bad.append(f"{source} lines {s + 1}-{e}: its pointer stub is missing from the living doc")
            present = set(live_text.splitlines()) | set(comp_text.splitlines())
            lost = [ln.rstrip("\n") for ln in L if ln.strip() and ln.rstrip("\n") not in present]
            if lost:
                bad.append(f"{source}: {len(lost)} BASE lines in neither file, first: {lost[0][:100]!r}")
    if mode == "--apply" and not bad:
        RECORD.write_text(json.dumps(record, ensure_ascii=False, indent=1) + "\n", encoding="utf-8", newline="\n")
    if mode == "--verify" and not bad:
        on_disk = json.loads(RECORD.read_text(encoding="utf-8"))
        for source, rec in record["sources"].items():
            if [b["sha256"] for b in on_disk["sources"][source]["blocks"]] != [b["sha256"] for b in rec["blocks"]]:
                bad.append(f"{source}: block hashes differ from {RECORD.name}")
    for b in bad:
        print("FAIL", b)
    if mode != "--plan":
        print("HISTORY_SPLIT", "FAIL" if bad else "OK", mode)
    return 1 if bad else 0


if __name__ == "__main__":
    raise SystemExit(main())
