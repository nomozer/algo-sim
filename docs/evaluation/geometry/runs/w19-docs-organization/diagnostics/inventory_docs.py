# -*- coding: utf-8 -*-
"""W19 — inventory tài liệu và artifact (chỉ đọc kho; ghi đúng một file JSON).

Chạy từ gốc kho:
    backend/.venv/Scripts/python.exe docs/evaluation/geometry/runs/w19-docs-organization/diagnostics/inventory_docs.py \
        --base 6d0e6321 --out docs/evaluation/geometry/runs/w19-docs-organization/inventory/INVENTORY.json

Đối tượng (brief §3): *.md ở gốc kho · mọi file trong docs/** ngoài docs/evaluation/** · mỗi thư mục run của
docs/evaluation/** (một dòng / thư mục, kèm git tree id) · kế hoạch/ledger/output ngoài docs · thư mục tạm.
Mọi số đọc tại commit `--base` (trạng thái TRƯỚC khi W19 di chuyển gì). Quyết định lấy từ bảng QUYET_DINH
(luật R1–R12 của kế hoạch W19); file không có trong bảng nhận quyết định theo luật mặc định của vùng.
Không đọc nội dung file nhạy cảm (.env, .secrets, settings*.json*): chỉ ghi có/không.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[6]
HOME = Path(os.path.expanduser("~"))
TEXT = {".md", ".json", ".py", ".mjs", ".js", ".ts", ".tsx", ".txt", ".yml", ".yaml", ".toml", ".csv", ".html", ".css"}

CANONICAL = {f"docs/{n}" for n in (
    "README.md", "RULES.md", "ARCHITECTURE_MAP.md", "CURRENT_STATE.md", "STATUS_LEDGER.md", "CODE_INDEX.md",
    "ROADMAP.md", "OPEN_ISSUES.md", "MIGRATION_CHECKLIST.md", "AI_CONTEXT_BUNDLE.md", "EVIDENCE_INDEX.md")}
PROJECT = {f"docs/{n}" for n in (
    "CORRECTNESS.md", "COVERAGE.md", "DESIGN_BRIEF.md", "OPERATIONS.md", "DEMO_RUNBOOK.md", "TEST_TIERS.md",
    "POST_THESIS_BACKLOG.md")}

TH = "docs/research/thesis/"
LG = "docs/legacy/"
# old path -> (decision, type, destination, reason)
QUYET_DINH: dict[str, tuple[str, str, str, str]] = {}
for n in ("THESIS_DRAFT", "THESIS_ARCHITECTURE", "THESIS_DEMO", "THESIS_REFERENCES", "THESIS_CITATION_MATRIX",
          "THESIS_REFERENCE_NEEDS", "THESIS_FIGURE_CAPTURE_PLAN", "THESIS_SUBMISSION_CHECKLIST"):
    QUYET_DINH[f"docs/{n}.md"] = ("MOVE", "RESEARCH_WRITING", f"{TH}{n}.md",
                                  "R5: bản thảo/tài liệu khoá luận, không phải báo cáo wave; ra khỏi gốc docs")
for n in ("CHAPTER_4_RESULTS_AND_DISCUSSION.md", "CHAPTER_5_CONCLUSION_AND_LIMITATIONS.md", "RELATED_WORK_DRAFT.md",
          "references_geometry_systems.bib"):
    QUYET_DINH[f"docs/thesis/{n}"] = ("MOVE", "RESEARCH_WRITING", f"{TH}{n}", "R5: gom phân khu khoá luận")
QUYET_DINH["docs/research/PUBLICATION_READINESS_ASSESSMENT.md"] = (
    "MOVE", "RESEARCH_WRITING", "docs/research/paper/PUBLICATION_READINESS_ASSESSMENT.md", "R5: phân khu bài báo")
QUYET_DINH["docs/geometry/GEOMETRY_CURRICULUM_COVERAGE.md"] = (
    "MOVE", "RESEARCH_WRITING", "docs/research/GEOMETRY_CURRICULUM_COVERAGE.md",
    "R5: bằng chứng tuyên bố phủ chương trình (dùng chung); reader test cập nhật đường dẫn")
for n in ("CAPABILITY_GAP_AUDIT", "CURRENT_SYSTEM_MAPPING", "GEOMETRY_ARCHITECTURE_GAP_REPORT", "GEOMETRY_ROADMAP",
          "MIGRATION_PLAN", "PHASE6_SIMULATION_SEMANTICS_REPORT", "SIMULATION_FOUNDATION_AUDIT",
          "SIMULATION_STATE_DESIGN"):
    QUYET_DINH[f"docs/geometry/{n}.md"] = (
        "ARCHIVE", "ARCHIVED_DECISION", f"{LG}geometry/{n}.md",
        "R4: kế hoạch/thiết kế/soát của giai đoạn chuyển đề 2026-08-24..09-02; đã được thay bởi ma trận năng lực v2 "
        "và tài liệu chuẩn tắc")
for n in ("NEXT_VERTICAL_SLICE_DECISION", "CUBOID_CUBE_CONTRACT_DECISION"):
    QUYET_DINH[f"docs/architecture/{n}.md"] = (
        "ARCHIVE", "ARCHIVED_DECISION", f"{LG}architecture/{n}.md",
        "R4: quyết định đã thực thi (2026-09-25/26), không ai tham chiếu; thư mục architecture/ chỉ giữ contract + snapshot")
QUYET_DINH["docs/REPOSITORY_MAP.md"] = (
    "ARCHIVE", "ARCHIVED_DECISION", f"{LG}REPOSITORY_MAP.md",
    "R4: bản đồ vị trí viết 2026-08-23, trước khi đổi đề; vai trò nay thuộc docs/README.md + CODE_INDEX")
QUYET_DINH["docs/THESIS_READINESS.md"] = (
    "MERGE", "RESEARCH_WRITING", f"{LG}research/THESIS_READINESS.md",
    "R6: bảng tuyên bố hiện hành gộp vào docs/research/CLAIM_EVIDENCE_MAP.md; bản gốc (nhật ký tuyên bố/đính chính "
    "tới W18) giữ nguyên byte ở legacy")
QUYET_DINH["docs/research/CLAIM_TO_EVIDENCE_MAP.md"] = (
    "MERGE", "RESEARCH_WRITING", f"{LG}research/CLAIM_TO_EVIDENCE_MAP.md",
    "R6: snapshot 2026-09-10 (lớp bằng chứng) gộp vào bản đồ duy nhất; bản gốc giữ nguyên byte ở legacy")
QUYET_DINH["docs/thesis/CLAIM_EVIDENCE_MATRIX.md"] = (
    "MERGE", "RESEARCH_WRITING", f"{LG}research/CLAIM_EVIDENCE_MATRIX.md",
    "R6: ma trận 29 tuyên bố 2026-09-09 gộp vào bản đồ duy nhất; bản gốc giữ nguyên byte ở legacy")
for p in ("plans/2026-07-15-m10-3d-ped-protocol-encapsulation.md", "plans/2026-07-16-m13-generic-semantic-soundness.md",
          "plans/2026-07-18-m14-capability-family-formalization.md",
          "plans/2026-07-18-m15-public-capability-contract-formalization.md",
          "plans/2026-07-19-m16-comprehensive-llm-evaluation.md", "plans/2026-08-17-w13-bo-hinh-thuc-hoi-dap.md",
          "plans/2026-08-20-semantic-program-generative-route.md",
          "specs/2026-07-15-m10-3d-ped-protocol-encapsulation-design.md", "specs/2026-07-15-m9-ux3-home-preview-design.md",
          "specs/2026-07-16-m13-generic-semantic-soundness-design.md", "specs/2026-07-16-m13-semantic-matrix.md",
          "specs/2026-07-17-m14-capability-family-formalization-design.md",
          "specs/2026-07-18-m15-public-capability-contract-formalization-design.md",
          "specs/2026-07-19-m16-comprehensive-llm-evaluation-design.md", "specs/2026-07-19-m16-evaluation-audit.md",
          "specs/2026-07-21-m17-lite-proposal.md", "specs/2026-07-21-m17-wave2a-tree-traversal.md",
          "specs/2026-08-20-semantic-program-generative-route-design.md"):
    QUYET_DINH[f"docs/superpowers/{p}"] = (
        "ARCHIVE", "ARCHIVED_DECISION", f"{LG}superpowers/{p}",
        "R4: kế hoạch/spec của skill cho milestone đã đóng (M9–M17, W13 cũ, semantic route); đáng giữ để truy vết")

# file ở thư mục con đã giữ chỗ, có vai trò khác mặc định
GIU: dict[str, tuple[str, str]] = {
    "docs/architecture/ASSUMPTION_CERTIFICATE_AMENDMENT.md": ("CURRENT_PROJECT", "contract sống; mã sản phẩm trích đường dẫn"),
    "docs/architecture/OCCLUSION_AND_SCENE_IDENTITY_AMENDMENT.md": ("CURRENT_PROJECT", "contract occlusion/scene identity"),
    "docs/architecture/GENERIC_GEOMETRY_FOUNDATION_PREREGISTRATION.md": ("EXPERIMENT_PROTOCOL", "R1: tiền đăng ký W13, run w13 trích"),
    "docs/architecture/GEOMETRY_CAPABILITY_AND_NON_ABSOLUTE_AUDIT.md": ("EXECUTION_EVIDENCE", "R1: snapshot kiểm kê W13"),
    "docs/architecture/geometry_capability_matrix_v2.json": ("EXECUTION_EVIDENCE", "R1: snapshot v2 — thẩm quyền theo tầng"),
    "docs/architecture/ARCHITECTURE_CAPABILITY_MATRIX.md": ("EXECUTION_EVIDENCE", "R1: snapshot v1 (2026-09-25), v2 trích là bất biến"),
    "docs/architecture/architecture_capability_matrix.json": ("EXECUTION_EVIDENCE", "R1: snapshot v1, bất biến"),
    "docs/research/RECTANGULAR_BASE_PYRAMID_COMPILER_VERTICAL_SLICE.md": ("EXECUTION_EVIDENCE", "R1: báo cáo wave đặt ở research/ từ đầu; giữ đường dẫn, ghi ngoại lệ"),
    "docs/research/RELATED_WORK_SEARCH_PROTOCOL.md": ("EXPERIMENT_PROTOCOL", "phương pháp dùng chung"),
    "docs/research/HYBRID_ARCHITECTURE_EVALUATION_PROTOCOL.md": ("EXPERIMENT_PROTOCOL", "tiền đăng ký đánh giá lai"),
    "docs/research/hybrid_architecture_evaluation_manifest.json": ("EXPERIMENT_PROTOCOL", "manifest của protocol trên"),
    "docs/research/LLM_ONLY_PAIRED_BASELINE_COLLECTION_PREREGISTRATION.md": ("EXPERIMENT_PROTOCOL", "tiền đăng ký baseline"),
    "docs/research/llm_only_paired_baseline_registry.json": ("EXPERIMENT_PROTOCOL", "registry; script collect_llm_only_paired_baseline.py đọc"),
    "docs/research/RESEARCH_GAP_AND_CONTRIBUTIONS.md": ("RESEARCH_WRITING", "khoảng trống + đóng góp (dùng chung)"),
    "docs/research/LITERATURE_COMPARISON_MATRIX.md": ("RESEARCH_WRITING", "ma trận so sánh tài liệu"),
    "docs/research/SYSTEMATIC_LITERATURE_GAP_SYNTHESIS.md": ("RESEARCH_WRITING", "tổng hợp tài liệu có hệ thống"),
    "docs/research/systematic_literature_evidence_matrix.json": ("RESEARCH_WRITING", "dữ liệu máy của tổng hợp trên"),
    "docs/research/systematic_literature_search_log.json": ("RESEARCH_WRITING", "nhật ký tìm kiếm"),
    "docs/schemas/semantic_program.schema.json": ("CURRENT_PROJECT", "sinh bởi export_semantic_program_schema.py; candidate đọc"),
    "docs/legacy/RULES_v0.3.md": ("ARCHIVED_DECISION", "đã ở legacy; frontend rules-hygiene.test.ts ghim"),
}


def git(*a: str) -> str:
    return subprocess.run(["git", "-c", "core.quotePath=false", *a], cwd=ROOT, capture_output=True, text=True,
                          encoding="utf-8", check=True).stdout


def doc(p: str) -> str:
    """Đọc từ cây làm việc: main() đã kiểm cây làm việc khớp `--base` cho mọi file được theo dõi."""
    try:
        return (ROOT / p).read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return ""


def tieu_de(p: str) -> str:
    if not p.endswith(".md"):
        return Path(p).suffix.lstrip(".").upper() or "FILE"
    for line in doc(p).splitlines():
        if line.startswith("#"):
            return line.lstrip("# ").strip()[:160]
    return ""


def vung(p: str) -> str:
    if p.startswith("docs/evaluation/"):
        return "frozen_evidence"
    if p.startswith("backend/app/") or (p.startswith("frontend/src/") and ".test." not in p):
        return "product_code"
    if p.startswith("backend/tests/") or ".test." in p or p.endswith(".node-test.mjs"):
        return "tests"
    if p.startswith(("backend/scripts/", "frontend/scripts/", "scripts/", ".claude/hooks/")):
        return "scripts_tools"
    if "/" not in p:
        return "root_entry"
    if p.startswith("docs/"):
        return "docs"
    return "other"


def tham_chieu(targets: list[str], tracked: list[str]) -> dict[str, dict[str, list[str]]]:
    dem = defaultdict(int)
    for t in tracked:
        dem[Path(t).name] += 1
    khoa = {}
    for t in targets:
        b = Path(t).name
        khoa[b if dem[b] == 1 else t[len("docs/"):] if t.startswith("docs/") else t] = t
    pat = re.compile(r"(?<![A-Za-z0-9_./-])(?:[A-Za-z0-9_./-]*/)?(" + "|".join(
        re.escape(k) for k in sorted(khoa, key=len, reverse=True)) + r")(?![A-Za-z0-9_])")
    out: dict[str, dict[str, set[str]]] = {t: defaultdict(set) for t in targets}
    for src in tracked:
        if Path(src).suffix.lower() not in TEXT:
            continue
        for m in pat.finditer(doc(src)):
            t = khoa[m.group(1)]
            if t != src:
                out[t][vung(src)].add(src)
    return {t: {k: sorted(v) for k, v in r.items()} for t, r in out.items()}


def loai_bao_cao(name: str) -> str:
    if re.search(r"PREREGISTRATION|PROTOCOL", name):
        return "EXPERIMENT_PROTOCOL"
    if re.search(r"DECISION|DESIGN|CONTRACT|POLICY|PLAN\b", name):
        return "ARCHIVED_DECISION"
    return "EXECUTION_EVIDENCE"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    base = git("rev-parse", a.base).strip()
    # Cây làm việc phải bằng `base` cho mọi file được theo dõi (trừ thay đổi bảo tồn của user: favicon xoá).
    lech = [l for l in git("diff", "--name-only", base).splitlines() if l and l != "frontend/public/favicon.svg"]
    if lech:
        raise SystemExit(f"cây làm việc lệch {base[:8]}: {lech[:5]} — chạy inventory trước mọi di chuyển")
    tracked = [t for t in git("ls-tree", "-r", "--name-only", base).splitlines() if t]
    blobs = {}
    for line in git("ls-tree", "-r", base).splitlines():
        meta, path = line.split("\t", 1)
        blobs[path] = meta.split()[2]
    ev = doc("docs/EVIDENCE_INDEX.md")
    ledger = doc("docs/STATUS_LEDGER.md")

    targets = sorted(t for t in tracked if (t.startswith("docs/") and not t.startswith("docs/evaluation/"))
                     or ("/" not in t and t.endswith(".md")))
    refs = tham_chieu([t for t in targets if Path(t).suffix.lower() in TEXT | {".bib"}], tracked)
    rows = []
    for p in targets:
        r = refs.get(p, {})
        ref_count = {k: len(v) for k, v in r.items()}
        ref_mau = {k: v[:4] for k, v in r.items() if k != "docs"}
        if p in QUYET_DINH:
            dec, typ, dest, why = QUYET_DINH[p]
            auth = "docs/research/CLAIM_EVIDENCE_MAP.md" if dec == "MERGE" else dest
        elif p in CANONICAL:
            dec, typ, dest, why, auth = "KEEP", "CURRENT_PROJECT", p, "R2: tài liệu chuẩn tắc (11 domain), đường dẫn bị khoá bởi audit/hook/bootstrap", p
        elif p in PROJECT:
            dec, typ, dest, why, auth = "KEEP", "CURRENT_PROJECT", p, "R2/R3: tài liệu dự án hiện hành ở gốc docs (đường dẫn bị test/hook/mã ghim hoặc là chỉ dẫn vận hành)", p
        elif p in GIU:
            typ, why = GIU[p]
            dec, dest, auth = "KEEP", p, p
        elif "/" not in p:
            typ = "CURRENT_PROJECT"
            dec, dest, auth = "KEEP", p, p
            why = {"README.md": "entry point gốc", "AGENTS.md": "entry point agent (luật)",
                   "DESIGN.md": "token UI; CSS và test trích"}.get(p, "tài liệu gốc kho")
        elif p.startswith("docs/thesis_figures/"):
            dest = TH + "figures/" + p[len("docs/thesis_figures/"):]
            dec, typ, auth = "MOVE", "RESEARCH_WRITING", dest
            why = "R5: hình của khoá luận (nguồn SVG/PNG + nhật ký chụp) theo bản thảo"
        elif re.fullmatch(r"docs/[^/]+\.md", p):
            typ = loai_bao_cao(Path(p).stem)
            dec, dest = "KEEP", p
            reg = f"docs/{Path(p).name}" in ev or f"docs/{Path(p).name}" in ledger
            auth = "docs/EVIDENCE_INDEX.md" if reg else "docs/evaluation/HISTORICAL_REPORTS.md"
            why = ("R1: báo cáo/hồ sơ wave = evidence đã đóng băng; giữ nội dung + đường dẫn, vào catalog "
                   "docs/evaluation/HISTORICAL_REPORTS.md")
        else:
            dec, typ, dest, auth, why = "REVIEW_REQUIRED", "UNKNOWN", p, p, "không khớp luật nào"
        text = doc(p) if p.endswith(".md") else ""
        reg_ev = p in ev
        if typ == "EXECUTION_EVIDENCE":
            value = "HIGH" if reg_ev else "MEDIUM"
            repro = "ARTIFACTS_IN_REPO" if "docs/evaluation/" in text else "NARRATIVE_ONLY"
        elif typ in ("RESEARCH_WRITING", "EXPERIMENT_PROTOCOL"):
            value, repro = "HIGH", "N/A_WRITING" if typ == "RESEARCH_WRITING" else "PROTOCOL"
        elif typ == "ARCHIVED_DECISION":
            value, repro = "MEDIUM_HISTORY", "N/A"
        else:
            value, repro = "HIGH_OPERATIONAL", "N/A"
        rows.append({"path": p, "title": tieu_de(p), "type": typ, "decision": dec, "destination": dest,
                     "authority_or_replacement": auth, "reason": why, "blob_at_base": blobs.get(p),
                     "referenced_by_count": ref_count, "referenced_by_sample": ref_mau,
                     "registered_in_evidence_index": reg_ev, "research_value": value, "reproducibility": repro,
                     "audience": "AGENT_DEVELOPER" if typ == "CURRENT_PROJECT" else
                     ("THESIS_READER" if typ == "RESEARCH_WRITING" else "EVALUATOR")})

    # docs/evaluation: một dòng / thư mục run
    trees = {}
    for line in git("ls-tree", "-r", "-d", base, "--", "docs/evaluation").splitlines():
        meta, path = line.split("\t", 1)
        trees[path] = meta.split()[2]
    nhom = defaultdict(list)
    for t in tracked:
        if not t.startswith("docs/evaluation/"):
            continue
        parts = t.split("/")
        sau = 4 if parts[2] == "geometry" and len(parts) > 4 and parts[3] in ("runs", "photo-problem-to-scene") else 3
        # thư mục run ở độ sâu `sau`; file nằm thẳng trong thư mục cha của tầng ấy gom theo thư mục cha
        key = "/".join(parts[:sau + 1]) if len(parts) > sau + 1 else "/".join(parts[:-1]) + "/*"
        nhom[key].append(t)
    runs = []
    for k, files in sorted(nhom.items()):
        if k.endswith("/*"):
            dau = hashlib.sha256("".join(f"{f} {blobs[f]}\n" for f in sorted(files)).encode()).hexdigest()
            kind, ident = "LOOSE_FILES_IN_DIRECTORY", f"sha256(path blob list)={dau}"
        else:
            kind, ident = "RUN_DIRECTORY", f"git tree {trees[k]}"
        runs.append({"path": k, "kind": kind, "files": len(files), "identity_at_base": ident,
                     "type": "EXECUTION_EVIDENCE",
                     "decision": "KEEP", "reason": "R1: artifact đóng băng — giữ nội dung và đường dẫn",
                     "registered_in_evidence_index_or_ledger": (k in ev) or (k in ledger)})

    # ngoài docs: kế hoạch, ledger, output bị ignore
    nhay_cam = {".secrets", "backend/.env", ".claude/settings.local.json"}
    ignored = [l[3:].rstrip("/") for l in git("status", "--ignored", "--porcelain=v1").splitlines()
               if l.startswith("!! ") and not re.search(r"node_modules|__pycache__|\.venv|/dist|\.pytest_cache|\.pyc$", l)]
    ngoai = []
    for p in ignored:
        cls = ("SENSITIVE_NOT_READ" if p in nhay_cam else
               "LOCAL_AGENT_INSTRUCTIONS" if p == "CLAUDE.md" else
               "PLAN_LEDGER" if p == ".superpowers" else
               "USER_DATA" if p.startswith("backend/algosim.db") or p == "data" else
               "TOOL_STATE" if "impeccable" in p or p == ".claude/skills" else
               "REPRODUCIBLE_OUTPUT_KEPT" if p.endswith((".xml", "telemetry.json")) else
               "UNKNOWN")
        ngoai.append({"path": p, "class": cls, "decision": "KEEP",
                      "note": "git-ignored; ngoài phạm vi xoá của W19 (không phải file W19 tạo)"})
    sdd = ROOT / ".superpowers" / "sdd"
    if sdd.is_dir():
        ngoai.append({"path": ".superpowers/sdd/*", "class": "PLAN_LEDGER", "decision": "KEEP",
                      "entries": sorted(x.name for x in sdd.iterdir())})
    plans = HOME / ".claude" / "plans"
    if plans.is_dir():
        ngoai.append({"path": str(plans).replace("\\", "/") + "/*.md", "class": "PLAN_FILES", "decision": "KEEP",
                      "entries": sorted(x.name for x in plans.glob("*.md"))})

    # thư mục tạm
    tmp = []
    for d in sorted(Path("D:/tmp").iterdir(), key=lambda x: x.name):
        n = d.name
        cls = ("W19_TEMP" if n.startswith("w19-") else
               "SENSITIVE_NOT_READ" if "settings" in n else "UNKNOWN_EARLIER_WAVE")
        info = {"path": f"D:/tmp/{n}", "kind": "DIR" if d.is_dir() else "FILE", "class": cls,
                "decision": "DELETE_AT_END" if cls == "W19_TEMP" else "KEEP",
                "mtime_utc": datetime.fromtimestamp(d.stat().st_mtime, timezone.utc).strftime("%Y-%m-%d")}
        if d.is_dir():
            g = [x for x in (d / ".git", d / "algo-sim" / ".git") if x.exists()]
            info["contains_git"] = [str(x).replace("\\", "/") for x in g]
        tmp.append(info)
    lac = Path("D:/Documents/projects/docs/evaluation/geometry/holdout/COVERAGE_MATRIX.md")
    if lac.exists():
        tmp.append({"path": str(lac).replace("\\", "/"), "kind": "FILE", "class": "STRAY_OUTPUT_OUTSIDE_REPO",
                    "decision": "VERIFY_THEN_DELETE_IF_DUPLICATE",
                    "compare_with": "docs/evaluation/geometry/holdout/COVERAGE_MATRIX.md"})

    tong = defaultdict(int)
    for r in rows:
        tong[f"{r['decision']}:{r['type']}"] += 1
    kq = {"schema_version": "w19-docs-inventory/1", "base_commit": base,
           "rules": "plan C:/Users/Bunny/.claude/plans/w19-docs-organization.md § Rulings R1–R12",
           "counts": {"docs_and_root_files": len(rows), "evaluation_groups": len(runs),
                      "evaluation_files": sum(r["files"] for r in runs), "outside_docs": len(ngoai),
                      "temp_entries": len(tmp), "by_decision_type": dict(sorted(tong.items())),
                      "review_required": sum(1 for r in rows if r["decision"] == "REVIEW_REQUIRED")},
           "docs": rows, "evaluation": runs, "outside_docs": ngoai, "temp": tmp}
    out = ROOT / a.out
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(kq, ensure_ascii=False, indent=1) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps(kq["counts"], ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
