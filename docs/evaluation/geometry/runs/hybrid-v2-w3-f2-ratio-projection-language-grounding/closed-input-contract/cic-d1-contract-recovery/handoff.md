# Handoff — CIC-D1 recovery: NOT_READY (stopped before freeze)

Read `report.md`, `pre-freeze-review.md`, `corrections.md`, `gate-d.json`, `publication-exception-proposal.json`.
The research tree is clean at the commit holding this file. Main/origin `996f114b`. No merge, push or cleanup.

- Open MAJOR findings: F1 (grammar widening for scope-only targets) and F2 (/1 vs /2 alias distinctness).
  Fixing them is a product change in `typed_fact_next.py`. It needs Owner direction on F1 (refuse, or register an alias).
  After any edit, preregister RED again; the cases in `pre-freeze-review/cases_*.json` are a ready probe corpus.
- Publication: `check_publication_safety.py --range 996f114b..HEAD` stays BLOCKED until the Owner writes
  `APPROVED_BY_USER` for the two proposed entries (or decides otherwise). Agents never write that value.
- Run the entire backend pytest only from a clean tree. Raw full logs contain a pytest thread-exception
  traceback, so commit only digests (see `gate-d-full-backend-pytest.summary.txt`).
- Use the current preview fixture set `hybrid-v2-backend-generalization/fixtures-adapter-2-named-plane`. Older sets differ on main too.
- Worktrees kept: `w3-f2-main-baseline-996f114b`, `w3-f2-pre-cic-5e44d5da` (detached, no node_modules junction).
  Reviewer scratch: `D:/tmp/cic-d1-pre-freeze-review/` (copied into `pre-freeze-review/`).
- Not run: Wave 3 replay, T0/T1/T2, freeze, Full T3, final review. Freeze identity checks are `PENDING_NEW_FREEZE`.
