"""cuboid-final-review — full docs inventory (task 1). Read-only; writes ../inventory/DOCS_INVENTORY.json.

Covers every tracked file under docs/ plus AGENTS.md, README.md and DESIGN.md: one row per file outside the
evaluation subtrees, one row per evaluation subtree (file count + git tree id at HEAD), and the git-ignored
leftovers under docs/. Referrers are counted from every tracked text file of the repository; a referrer is
"frozen" when its own class is FROZEN_KEEP or KEEP_ARCHITECTURAL_HISTORY, "living" otherwise (code included).

    cd backend && PYTHONIOENCODING=utf-8 .venv/Scripts/python.exe \
        ../docs/evaluation/geometry/runs/cuboid-final-review/diagnostics/inventory_docs_cfr.py [--check]

--check prints the metrics without writing.
"""
from __future__ import annotations

import hashlib
import json
import re
import subprocess
import sys
from collections import Counter, defaultdict
from pathlib import Path, PurePosixPath
from urllib.parse import unquote

ROOT = Path(__file__).resolve().parents[6]
RUN = "docs/evaluation/geometry/runs/cuboid-final-review"
OUT = ROOT / RUN / "inventory" / "DOCS_INVENTORY.json"
CLASSES = ("KEEP_CURRENT", "KEEP_RESEARCH", "KEEP_ARCHITECTURAL_HISTORY", "MERGE_INTO_CANONICAL",
           "DELETE_VERIFIED_DUPLICATE", "DELETE_ABANDONED_OUT_OF_SCOPE", "DELETE_REPRODUCIBLE_TEMP",
           "REVIEW_REQUIRED", "FROZEN_KEEP")
FROZEN_CLASSES = {"FROZEN_KEEP", "KEEP_ARCHITECTURAL_HISTORY"}
TEXT_EXT = {".md", ".py", ".ts", ".tsx", ".mjs", ".js", ".cjs", ".json", ".yml", ".yaml", ".toml", ".txt",
            ".html", ".css", ".sh", ".ps1", ".cfg", ".ini", ".bib", ".svg"}
INFORMATICS = re.compile(r"Tin học|bubble_sort|domains/(?:algorithm|binary|logic|network|tree|database|web|generic)\b"
                         r"|simulation/dsl|\bcatalog\.py|validation/(?:program|simulation|character_encoding)")

# Hand classification of every file outside the evaluation subtrees (class, reason, action). Keys ending in "/"
# apply to every file under that prefix; the longest matching key wins.
_SPLIT = "informatics-era part moved verbatim to docs/legacy/{} (HISTORY_SPLIT.json); pointer left in place"
HAND: dict[str, tuple[str, str, str]] = {
    "AGENTS.md": ("KEEP_CURRENT", "agent entry point; rules read by audit and tests", "wave-numbering pointer (task 3)"),
    "README.md": ("KEEP_CURRENT", "repository README of the geometry thesis (13 sections, current)", "none"),
    "DESIGN.md": ("KEEP_CURRENT", "UI token file (Notion-style analysis) read by the design tooling", "none"),
    "docs/README.md": ("KEEP_CURRENT", "docs portal (canonical domain)", "living-docs update (task 8)"),
    "docs/AI_CONTEXT_BUNDLE.md": ("KEEP_CURRENT", "session handoff (canonical domain)", "living-docs update (task 8)"),
    "docs/CURRENT_STATE.md": ("KEEP_CURRENT", "state + identity lock (canonical domain)", "living-docs update (task 8)"),
    "docs/EVIDENCE_INDEX.md": ("KEEP_CURRENT", "evidence lookup + CORRECTED_BY chain", "living-docs update (task 8)"),
    "docs/ROADMAP.md": ("KEEP_CURRENT", "canonical next action and backlog", "living-docs update (task 8)"),
    "docs/OPEN_ISSUES.md": ("KEEP_CURRENT", "issue register (canonical domain)",
                            "two new issues (T1 scripts, invariant pointers); dated audit lines on two compiler issues"),
    "docs/RULES.md": ("KEEP_CURRENT", "rules (canonical domain)", "reading item 7 points at the current coverage "
                      "authorities; wave-numbering pointer (task 3)"),
    "docs/ARCHITECTURE_MAP.md": ("KEEP_CURRENT", "running-system map, numbered invariants (canonical domain)",
                                 _SPLIT.format("ARCHITECTURE_MAP_INFORMATICS_ERA.md") + "; §7 rewritten as pointers to "
                                 "the current extension authorities; dated note on the stale invariant locks of §5"),
    "docs/CODE_INDEX.md": ("KEEP_CURRENT", "module index (canonical domain)", "94 entries of removed code and the "
                           "two ⛔ sections §0h/§0i moved verbatim to docs/legacy/CODE_INDEX_REMOVED_ENTRIES.md; §0j "
                           "traceability index kept with a pointer"),
    "docs/STATUS_LEDGER.md": ("KEEP_CURRENT", "status ledger (canonical domain); §0-2026-08-24 and §6 current",
                              _SPLIT.format("STATUS_LEDGER_INFORMATICS_ERA.md") + "; navigation note at the top"),
    "docs/MIGRATION_CHECKLIST.md": ("KEEP_CURRENT", "20 gates for the default switch (canonical domain)",
                                    "two dead evidence paths corrected; dated audit lines on GATE-11/12 (router and "
                                    "fallback exist opt-in; statuses left to the migration wave)"),
    "docs/CORRECTNESS.md": ("KEEP_CURRENT", "correctness principles; §1, §1a, §2, §2b, §4, §7 current",
                            _SPLIT.format("CORRECTNESS_INFORMATICS_ERA.md")),
    "docs/COVERAGE.md": ("KEEP_CURRENT", "pedagogical principles §2 and levels §5 are cited by code",
                         _SPLIT.format("COVERAGE_INFORMATICS_ERA.md") + "; new §1 points at the current coverage and "
                         "forbidden-claim authorities"),
    "docs/DESIGN_BRIEF.md": ("KEEP_CURRENT", "UI/UX brief; rules §3, §5–§7, §9 current, cited by product code",
                             _SPLIT.format("DESIGN_BRIEF_INFORMATICS_ERA.md") + "; dated banner and flow note"),
    "docs/OPERATIONS.md": ("KEEP_CURRENT", "contributor operations", "three examples naming removed files replaced"),
    "docs/DEMO_RUNBOOK.md": ("KEEP_CURRENT", "demo runbook of the geometry product", "none"),
    "docs/TEST_TIERS.md": ("KEEP_CURRENT", "test tiers", "dated note: 8/10 T1 scripts point at removed domains "
                           "(ISSUE-OPS-T1-DOMAIN-SCRIPTS-STALE)"),
    "docs/POST_THESIS_BACKLOG.md": ("KEEP_CURRENT", "post-thesis ideas; 2026-09-02 debts and 2026-09-09 directions "
                                    "current", _SPLIT.format("POST_THESIS_BACKLOG_INFORMATICS_ERA.md")),
    "docs/architecture/README.md": ("KEEP_CURRENT", "navigation of contracts vs immutable snapshots", "none"),
    "docs/architecture/ASSUMPTION_CERTIFICATE_AMENDMENT.md": ("KEEP_CURRENT", "contract in force (W15, §15–§17), "
                                                              "cited by product code", "none"),
    "docs/architecture/OCCLUSION_AND_SCENE_IDENTITY_AMENDMENT.md": ("KEEP_CURRENT", "contract in force", "none"),
    "docs/architecture/GENERIC_GEOMETRY_FOUNDATION_PREREGISTRATION.md": ("FROZEN_KEEP", "preregistration W13→W14, "
                                                                         "immutable (architecture/README)", "none"),
    "docs/architecture/GEOMETRY_CAPABILITY_AND_NON_ABSOLUTE_AUDIT.md": ("FROZEN_KEEP", "W13 snapshot at bf5a7907, "
                                                                        "immutable", "none"),
    "docs/architecture/geometry_capability_matrix_v2.json": ("FROZEN_KEEP", "W13 snapshot data", "none"),
    "docs/architecture/ARCHITECTURE_CAPABILITY_MATRIX.md": ("FROZEN_KEEP", "v1 snapshot 2026-09-25, immutable", "none"),
    "docs/architecture/architecture_capability_matrix.json": ("FROZEN_KEEP", "v1 snapshot data", "none"),
    "docs/research/README.md": ("KEEP_CURRENT", "research navigation", "note on the machine-local links of the two "
                                "sealed preregistrations"),
    "docs/research/CLAIM_EVIDENCE_MAP.md": ("KEEP_CURRENT", "the single claim ↔ evidence ↔ limit authority", "none"),
    "docs/research/GEOMETRY_CURRICULUM_COVERAGE.md": ("KEEP_RESEARCH", "curriculum coverage evidence, read by "
                                                      "test_curriculum_coverage.py", "none"),
    "docs/research/RESEARCH_GAP_AND_CONTRIBUTIONS.md": ("KEEP_RESEARCH", "research gap and contributions", "none"),
    "docs/research/LITERATURE_COMPARISON_MATRIX.md": ("KEEP_RESEARCH", "related-work comparison", "none"),
    "docs/research/SYSTEMATIC_LITERATURE_GAP_SYNTHESIS.md": ("KEEP_RESEARCH", "literature synthesis (patched four "
                                                             "times, a living research document)",
                                                             "four machine-local file:/// links made relative"),
    "docs/research/systematic_literature_evidence_matrix.json": ("KEEP_RESEARCH", "data of the synthesis", "none"),
    "docs/research/systematic_literature_search_log.json": ("KEEP_RESEARCH", "search log of the synthesis", "none"),
    "docs/research/RELATED_WORK_SEARCH_PROTOCOL.md": ("KEEP_RESEARCH", "survey method record (2026-09-10)",
                                                      "pointer to THESIS_REFERENCES.md updated to its W19 location"),
    "docs/research/HYBRID_ARCHITECTURE_EVALUATION_PROTOCOL.md": ("FROZEN_KEEP", "preregistration; bytes kept, its "
                                                                 "4 machine-local links documented in research/README",
                                                                 "none"),
    "docs/research/hybrid_architecture_evaluation_manifest.json": ("FROZEN_KEEP", "data of the preregistration", "none"),
    "docs/research/LLM_ONLY_PAIRED_BASELINE_COLLECTION_PREREGISTRATION.md": ("FROZEN_KEEP", "sealed preregistration; "
                                                                             "bytes kept, 5 machine-local links "
                                                                             "documented in research/README", "none"),
    "docs/research/llm_only_paired_baseline_registry.json": ("FROZEN_KEEP", "registry read by "
                                                             "collect_llm_only_paired_baseline.py", "none"),
    "docs/research/RECTANGULAR_BASE_PYRAMID_COMPILER_VERTICAL_SLICE.md": ("FROZEN_KEEP", "wave report placed here by "
                                                                          "its wave; exception in research/README",
                                                                          "none"),
    "docs/research/thesis/": ("KEEP_RESEARCH", "thesis drafts, references, citation rules and figures", "none"),
    "docs/research/thesis/RELATED_WORK_DRAFT.md": ("REVIEW_REQUIRED", "a second related-work text beside THESIS_DRAFT "
                                                   "§1.8; merging them is rewriting thesis prose, which this task may "
                                                   "not do — the author decides which text the thesis keeps", "none"),
    "docs/research/thesis/THESIS_ARCHITECTURE.md": ("KEEP_RESEARCH", "architecture snapshot 2026-09-02 for the design "
                                                    "chapter; the running system is ARCHITECTURE_MAP", "none"),
    "docs/research/paper/": ("KEEP_RESEARCH", "publication readiness assessment 2026-09-10", "none"),
    "docs/legacy/": ("KEEP_ARCHITECTURAL_HISTORY", "superseded document kept for traceability (legacy/README); "
                     "relative links inside point at the old locations — documented exception", "none"),
    "docs/legacy/README.md": ("KEEP_CURRENT", "navigation of the legacy folder", "table of the seven new companions"),
    "docs/schemas/semantic_program.schema.json": ("KEEP_CURRENT", "generated schema mirror, locked by "
                                                  "test_schema_sync.py", "none"),
    "docs/evaluation/README.md": ("KEEP_CURRENT", "evaluation navigation", "latest-run row (task 8)"),
    "docs/evaluation/RUN_NAMING.md": ("KEEP_CURRENT", "run naming rule", "wave numbering per work (task 3)"),
    "docs/evaluation/HISTORICAL_REPORTS.md": ("KEEP_CURRENT", "closed catalogue of the root reports", "none"),
    "docs/evaluation/AUDIT_ARTIFACT_MANIFEST.md": ("FROZEN_KEEP", "W4B-0 audit artifact manifest", "none"),
}


def git(*args: str) -> str:
    return subprocess.run(["git", *args], cwd=ROOT, capture_output=True, text=True, encoding="utf-8",
                          check=True).stdout


def tracked(*paths: str) -> list[str]:
    return [p for p in git("ls-files", "-z", "--", *paths).split("\0") if p]


def group_of(path: str) -> str | None:
    """Evaluation subtree that owns `path` (one row per subtree), or None for a per-file row."""
    parts = path.split("/")
    if parts[:2] != ["docs", "evaluation"] or len(parts) <= 3:
        return None
    if parts[2] == "geometry":
        if len(parts) == 4:
            return None                                         # top-level geometry report: per-file row
        if parts[3] == "runs":
            return "/".join(parts[:5]) + "/"
        return "/".join(parts[:4]) + "/"
    return "/".join(parts[:3]) + "/"


def catalogued() -> set[str]:
    text = (ROOT / "docs/evaluation/HISTORICAL_REPORTS.md").read_text(encoding="utf-8")
    return {f"docs/{n}" for n in re.findall(r"^\| \[`[^`]+`\]\(\.\./([A-Za-z0-9_\-]+\.md)\) \|", text, re.M)}


def hand(path: str) -> tuple[str, str, str] | None:
    keys = [k for k in HAND if path == k or (k.endswith("/") and path.startswith(k))]
    return HAND[max(keys, key=len)] if keys else None


def classify(path: str, catalog: set[str]) -> tuple[str, str, str]:
    if (h := hand(path)) is not None:
        return h
    if path in catalog:
        return ("FROZEN_KEEP", "historical wave report at the docs root, row of the closed catalog "
                "docs/evaluation/HISTORICAL_REPORTS.md (bytes and path kept)", "none")
    if path.startswith("docs/evaluation/geometry/") and path.count("/") == 3:
        return ("FROZEN_KEEP", "geometry-phase report or acceptance record (2026-08-24 … 09), cited by "
                "EVIDENCE_INDEX / reports; bytes and path kept", "none")
    return ("REVIEW_REQUIRED", "not classified by hand", "classify")


LINK = re.compile(r"\]\(\s*<?([^)\s>]+)>?(?:\s+\"[^\"]*\")?\s*\)")
REPO_PATH = re.compile(r"(?<![\w./\-])((?:docs|backend|frontend)/[^\s`'\"()<>\[\]{}|,;*]+)")


def resolve(src: str, target: str) -> str | None:
    t = unquote(target.split("#", 1)[0].split("?", 1)[0])
    if not t or re.match(r"^[a-z][a-z0-9+.\-]*:", t, re.I):
        return None
    base = PurePosixPath(src).parent
    parts: list[str] = []
    for seg in (base / t).parts:
        if seg == "..":
            if not parts:
                return "<outside-repo>"
            parts.pop()
        elif seg != ".":
            parts.append(seg)
    return "/".join(parts)


def exists(p: str, files: set[str], dirs: set[str]) -> bool:
    """Tracked at HEAD (so the user's unstaged deletion of a tracked file is not a dead pointer), or on disk."""
    p = p.rstrip("/")
    return p in files or p in dirs or (ROOT / p).exists()


def invariant_pointers(every: list[str]) -> list[dict]:
    """ARCHITECTURE_MAP §5: per numbered invariant, the files its 'enforced at' / 'test' cells name, split by whether a
    tracked file with that basename still exists."""
    names = {PurePosixPath(p).name for p in every}
    text = (ROOT / "docs/ARCHITECTURE_MAP.md").read_text(encoding="utf-8")
    sec = text.split("## 5. Bất biến", 1)[1].split("\n## ", 1)[0]
    out = []
    for row in re.findall(r"^\| (\d+) \|(.*)$", sec, re.M):
        cells = row[1].split("|")
        toks = []
        for t in re.findall(r"`([^`]+)`", "|".join(cells[1:])):
            t = re.split(r"::| ", t)[0]
            b = PurePosixPath(t).name
            if re.fullmatch(r"test_\w+", b):
                b += ".py"
            if re.search(r"\.(py|ts|tsx|mjs|md|json)$", b) and "*" not in b:
                toks.append(b)
        toks = list(dict.fromkeys(toks))
        out.append({"invariant": int(row[0]), "files_live": [b for b in toks if b in names],
                    "files_missing": [b for b in toks if b not in names]})
    return out


def main() -> int:
    catalog = catalogued()
    every = tracked(".")
    files = set(every)
    dirs = {"/".join(f.split("/")[:i]) for f in every for i in range(1, f.count("/") + 1)}
    scope = [p for p in tracked("docs", "AGENTS.md", "README.md", "DESIGN.md") if not p.startswith(RUN + "/")]

    rows: dict[str, dict] = {}
    groups: dict[str, list[str]] = defaultdict(list)
    for p in scope:
        if (g := group_of(p)) is not None:
            groups[g].append(p)
            continue
        cls, reason, action = classify(p, catalog)
        rows[p] = {"path": p, "kind": "file", "class": cls, "reason": reason, "action": action}

    file_class = {p: r["class"] for p, r in rows.items()}
    for g, members in groups.items():
        for m in members:
            file_class[m] = "FROZEN_KEEP"

    # Referrers: links, repo paths and unique ALLCAPS stems in every tracked text file.
    stems = Counter(PurePosixPath(p).stem for p in every)
    stem_target = {PurePosixPath(p).stem: p for p in rows
                   if stems[PurePosixPath(p).stem] == 1 and re.fullmatch(r"[A-Z][A-Z0-9_]{5,}", PurePosixPath(p).stem)}
    stem_re = re.compile(r"\b(" + "|".join(sorted(map(re.escape, stem_target), key=len, reverse=True)) + r")\b")
    refs: dict[str, set[str]] = defaultdict(set)
    dead: dict[str, list[str]] = defaultdict(list)
    local: dict[str, list[str]] = defaultdict(list)
    dead_paths: dict[str, list[str]] = defaultdict(list)
    markers: Counter = Counter()
    for src in every:
        if src.startswith(RUN + "/") or PurePosixPath(src).suffix.lower() not in TEXT_EXT:
            continue
        fp = ROOT / src
        try:
            if fp.stat().st_size > 5_000_000:
                continue
            text = fp.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        hits: set[str] = set()
        for t in LINK.findall(text):
            if t.lower().startswith("file:///"):
                if src in rows:
                    local[src].append(t)
                m = re.search(r"/algo-sim/(.+)$", unquote(t))
                if m:
                    hits.add(m.group(1))
                continue
            r = resolve(src, t)
            if r is None:
                continue
            hits.add(r.rstrip("/"))
            if src in rows and src.endswith(".md") and not exists(r, files, dirs):
                dead[src].append(t)
        for m in REPO_PATH.findall(text):
            m = re.sub(r"(::[\w.]+|:[\w\-]+)$", "", m.rstrip(".:"))     # `file.py::symbol`, `file.py:12-30`
            hits.add(m.rstrip("/"))
            if (src in rows and src.endswith(".md") and not re.search(r"[<{…]|\.\.\.|NNN|XX|[-_]$", m)
                    and not exists(m, files, dirs)):
                dead_paths[src].append(m)
        hits.update(stem_target[s] for s in set(stem_re.findall(text)))
        for h in hits:
            if h != src:
                refs[h].add(src)
        if src in rows and src.endswith(".md"):
            markers[src] = len(INFORMATICS.findall(text))

    def split(target: str) -> dict:
        living = sorted(r for r in refs.get(target, ()) if file_class.get(r, "KEEP_CURRENT") not in FROZEN_CLASSES)
        frozen = sorted(r for r in refs.get(target, ()) if file_class.get(r, "KEEP_CURRENT") in FROZEN_CLASSES)
        return {"living_count": len(living), "living": living[:12], "frozen_count": len(frozen), "frozen_sample": frozen[:4]}

    out_rows = []
    for p, r in sorted(rows.items()):
        blob = git("rev-parse", f"HEAD:{p}").strip()
        r.update({
            "group": ("root (catalogued report)" if p in catalog else
                      "root" if p.count("/") <= 1 else "/".join(p.split("/")[:3]) + "/"),
            "git_blob": blob,
            "bytes": (ROOT / p).stat().st_size,
            "referrers": split(p),
        })
        if p.endswith(".md"):
            r.update({"dead_relative_links": sorted(set(dead[p])), "machine_local_links": len(local[p]),
                      "dead_repo_path_mentions": sorted(set(dead_paths[p]))[:40],
                      "dead_repo_path_mentions_count": len(set(dead_paths[p])),
                      "informatics_markers": markers[p]})
        out_rows.append(r)
    out_groups = []
    for g, members in sorted(groups.items()):
        out_groups.append({
            "path": g, "kind": "group", "class": "FROZEN_KEEP", "file_count": len(members),
            "git_tree": git("rev-parse", f"HEAD:{g.rstrip('/')}").strip(),
            "reason": ("frozen run folder (plan, report, handoff, manifest, evidence) — immutable after commit"
                       if "/runs/" in g else "historical evaluation evidence of one wave or measurement — "
                       "immutable after commit (AGENTS.md §4); byte-identical copies across waves are intended "
                       "(each wave is self-contained)"),
            "action": "none",
        })

    covered = {r["path"] for r in out_rows} | {m for ms in groups.values() for m in ms}
    assert covered == set(scope), "inventory must cover every file exactly once"
    temp = []
    for line in git("status", "--ignored", "--porcelain", "-z", "--", "docs").split("\0"):
        if line.startswith("!! "):
            d = line[3:]
            listing = sorted(str(q.relative_to(ROOT)).replace("\\", "/") for q in (ROOT / d).rglob("*") if q.is_file())
            temp.append({"path": d, "kind": "ignored", "class": "DELETE_REPRODUCIBLE_TEMP",
                         "reason": "git-ignored interpreter cache inside docs/; regenerated on the next import",
                         "files": [{"path": q, "sha256": hashlib.sha256((ROOT / q).read_bytes()).hexdigest()}
                                   for q in listing]})

    counts = Counter(r["class"] for r in out_rows)
    summary = {
        "files_in_scope": len(scope),
        "per_file_rows": len(out_rows),
        "group_rows": len(out_groups),
        "files_in_groups": sum(g["file_count"] for g in out_groups),
        "by_class_per_file": dict(sorted(counts.items())),
        "catalogued_root_reports": len(catalog),
        "living_md_with_dead_relative_links": sorted(r["path"] for r in out_rows if r.get("dead_relative_links")
                                                     and r["class"] not in FROZEN_CLASSES),
        "living_md_with_machine_local_links": sorted(r["path"] for r in out_rows if r.get("machine_local_links")
                                                     and r["class"] not in FROZEN_CLASSES),
        "ignored_leftovers_in_docs": [t["path"] for t in temp],
    }
    doc = {
        "schema_version": "docs-inventory/1",
        "run_id": "cuboid-final-review",
        "base_commit": git("rev-parse", "HEAD").strip(),
        "classes": list(CLASSES),
        "frozen_referrer_rule": "a referrer counts as frozen when its own class is FROZEN_KEEP or "
                                "KEEP_ARCHITECTURAL_HISTORY; code and every other file count as living",
        "summary": summary,
        "files": out_rows,
        "groups": out_groups,
        "ignored_leftovers": temp,
        "architecture_map_invariant_pointers": invariant_pointers(every),
    }
    if "--check" in sys.argv:
        print(json.dumps(summary, ensure_ascii=False, indent=1))
        for r in out_rows:
            if r["class"] not in FROZEN_CLASSES and r["path"].endswith(".md"):
                print(f"{r['class'][:14]:14} L{r['referrers']['living_count']:>3} F{r['referrers']['frozen_count']:>4} "
                      f"dead{len(r['dead_relative_links']):>3} loc{r['machine_local_links']:>2} "
                      f"dp{r['dead_repo_path_mentions_count']:>4} inf{r['informatics_markers']:>4}  {r['path']}")
        return 0
    OUT.write_text(json.dumps(doc, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(f"wrote {OUT.relative_to(ROOT)}: {len(out_rows)} files + {len(out_groups)} groups "
          f"({summary['files_in_groups']} files) = {summary['files_in_scope']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
