# Baseline audit

2026-10-28, Asia/Bangkok. git fetch origin exited 0.
Root active branch main; HEAD = main = origin/main =
d7a94d3cd4bbdea3df99e383bec78425fcc8bf1c; git status --porcelain emitted no changes.
Git warned that global ignore and two pytest cache directories were unreadable. They are untouched.
Existing worktrees were inventoried before creation; none changed or removed.
Isolated research branch: research/hybrid-v2-wave2-source-gate-language-generalization.
Worktree: .superpowers/worktrees/source-gate-language-generalization, from clean main.
Initial worktree creation required sandbox escalation for Git ref writes; subsequent creation completed.

Baseline freeze --verify using root backend/.venv/Scripts/python.exe: MATCH,
118 measured files, 84ccf653441d1bd54f352756b9a5e917ee02a9ea11a83ac60585dfc585f3f99f.
System Python lacks fastapi; use existing project venv (no installation).
Registry18 / Planner17 / Engine14 / Adapter4 / certificate1 / CACHE130 / LLM_ONLY / Hybrid opt-in.
Historical Wave2 is not integrated into main. Read-only source commit:
ecdc26b012c8ce80d53524a98dc75cdcb020079d, branch research/hybrid-v2-independent-vietnamese-section-holdout-wave2.
Historical result: 5/48 served correct, 43 false refusals, 48/48 negatives refused, 33 correct reasons,
0/96 genuine wrong-served, exact agreement5/5. Raw and corrected runs remain separate.
See results/historical-integrity.json for byte verification when complete.

Pre-flight: CORE; current milestone opt-in Hybrid V2 research; thesis relevance Vietnamese 3D geometry input.
Expected changes: Registry only in product; targeted tests/pins, fixture identity tooling, candidate manifest,
this run and living evidence/code indexes in support.
Contract impact: expanded closed language subset, Registry identity bump; all geometry algorithms excluded.
Duplicate risk: avoid second ratio parser/solver; dependency-cycle risk none (existing Registry ownership).
Smallest implementation: add syntax to current source reader and strict whole-premise validation.
Excluded: W2-M4/M5, Radical/kernel/planner/engine/adapter/frontend/OCR/prompts/routing/O4/R1.
Stop conditions are in plan.md. No live calls, merge, push or cleanup authorized.
