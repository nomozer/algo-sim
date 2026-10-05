#!/usr/bin/env bash
# cuboid-acceptance identity, integrity and docs gates (pattern of cuboid-final-review/diagnostics/cfr_gates.sh) — run
# from the ROOT of a clean detached worktree at the documentation commit; 0 model calls. This run changes docs only,
# so the gates check that: no product byte moved (against the run start and against the candidate's product commit),
# the candidate and cache verify, the model surface and the default mode are unchanged, historical evidence is
# byte-identical, the docs audit and docs tests pass, and every §5 invariant pointer resolves.
# usage: bash cacc_gates.sh <verification sha> <run start sha> <candidate product commit>
set -u
M="$1"; START="$2"; PROD="$3"
PY=D:/Documents/projects/algo-sim/backend/.venv/Scripts/python.exe
export PYTHONIOENCODING=utf-8 PYTHONDONTWRITEBYTECODE=1
RUN=docs/evaluation/geometry/runs/cuboid-acceptance
echo "# cuboid-acceptance gates at $M (clean detached worktree), start $START, candidate product commit $PROD — 0 model calls"
echo "## git status (before)"; git status --porcelain | wc -l
echo "## HEAD"; git rev-parse HEAD
echo "## product bytes: backend/app + frontend/src changed since $START"
git diff --name-status "$START" "$M" -- backend/app frontend/src | sed 's/^/  /'
echo "changed: $(git diff --name-only "$START" "$M" -- backend/app frontend/src | wc -l)"
echo "## product bytes: backend/app + frontend/src changed since the candidate's product commit $PROD"
git diff --name-status "$PROD" "$M" -- backend/app frontend/src | sed 's/^/  /'
echo "changed: $(git diff --name-only "$PROD" "$M" -- backend/app frontend/src | wc -l)"
echo "## candidate verify"; (cd backend && "$PY" scripts/freeze_evaluation_candidate.py --verify); echo "exit=$?"
echo "## cache identity verify"; (cd backend && "$PY" scripts/lock_cache_identity.py --verify); echo "exit=$?"
echo "## CACHE_VERSION"; grep -n 'CACHE_VERSION = ' backend/app/main.py
echo "## DEFAULT_MODE"; grep -n 'CHE_DO_MAC_DINH = ' backend/app/simulation/geometry_compiler/routing.py
echo "## model surface (prompts, grammar card, schemas, capability) changed since $START"
S="backend/app/ai/skills backend/app/simulation/semantic_program/contract.py backend/app/simulation/semantic_program/grammar_card.py backend/app/simulation/product_capability.py docs/schemas frontend/src/simulations/domains/semantic/semantic_program.schema.json"
echo "changed: $(git diff --name-only "$START" "$M" -- $S | wc -l)"
echo "## schema mirrors byte-identical"
sha256sum docs/schemas/semantic_program.schema.json frontend/src/simulations/domains/semantic/semantic_program.schema.json | cut -d' ' -f1 | uniq | wc -l
echo "## docs/evaluation changed since $START outside this run (expected 0)"
git diff --name-status "$START" "$M" -- docs/evaluation ":(exclude)$RUN" | sed 's/^/  /'
echo "changed: $(git diff --name-only "$START" "$M" -- docs/evaluation ":(exclude)$RUN" | wc -l)"
echo "## docs/legacy changed since $START (expected 0)"; echo "changed: $(git diff --name-only "$START" "$M" -- docs/legacy | wc -l)"
echo "## historical reports at the docs root (docs/evaluation/HISTORICAL_REPORTS.md) changed since $START"
n=0; t=0; for f in $(grep -o '](\.\./\.\./docs/[A-Z0-9_]*\.md)\|](\.\./[A-Z0-9_]*\.md)' docs/evaluation/HISTORICAL_REPORTS.md | sed 's/^](//; s/)$//; s|^\.\./\.\./docs/|docs/|; s|^\.\./|docs/|' | sort -u); do
  t=$((t+1)); [ -n "$(git diff --name-only "$START" "$M" -- "$f")" ] && { echo "  changed: $f"; n=$((n+1)); }; done
echo "catalogued links changed: $n of $t (the living docs/EVIDENCE_INDEX.md linked from the catalogue introduction is expected to change)"
echo "## verbatim history split of cuboid-final-review"
(cd backend && "$PY" ../docs/evaluation/geometry/runs/cuboid-final-review/diagnostics/split_history_cfr.py --verify); echo "exit=$?"
echo "## git diff --check $START..$M (captured *.log excluded)"
git diff --check "$START" "$M" -- . ':(exclude)*.log'; echo "exit=$?"
echo "## ARCHITECTURE_MAP §5 pointers (inventory_docs_cfr.invariant_pointers)"
"$PY" - <<'PYEOF'
import importlib.util
p = "docs/evaluation/geometry/runs/cuboid-final-review/diagnostics/inventory_docs_cfr.py"
s = importlib.util.spec_from_file_location("inv", p); m = importlib.util.module_from_spec(s); s.loader.exec_module(m)
rows = m.invariant_pointers(m.tracked("."))
bad = [r for r in rows if r["files_missing"]]
print(f"rows {len(rows)}, rows with a missing file {len(bad)}")
for r in bad: print(" ", r)
PYEOF
echo "## docs audit"; "$PY" backend/scripts/audit_docs_information_architecture.py 2>&1 | tail -12; echo "exit=${PIPESTATUS[0]}"
echo "## docs tests (pytest: docs information architecture, CURRENT_STATE identity, thesis acceptance matrix, evaluation candidate)"
(cd backend && "$PY" -m pytest -q tests/geometry/test_docs_information_architecture.py tests/test_current_state_identity.py \
  tests/geometry/test_thesis_acceptance_matrix.py tests/semantic_program/test_evaluation_candidate.py 2>&1 | tail -3)
echo "## docs tests (vitest: code-index sync, rules hygiene, certification sweep)"
(cd frontend && npx vitest run src/code-index-sync.test.ts src/rules-hygiene.test.ts src/certification-sweep.test.ts 2>&1 \
  | sed 's/\x1b\[[0-9;]*m//g' | grep -E '^ *(Test Files|Tests) |FAIL')
echo "## git status (after)"; git status --porcelain | wc -l; git status --porcelain | head -10
