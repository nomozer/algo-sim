#!/usr/bin/env bash
# cuboid-merge gates (pattern of cuboid-acceptance/diagnostics/cacc_gates.sh) — run from the ROOT of a clean detached
# worktree at the commit under review; 0 model calls. Docs-only run: no product byte may move; candidate, cache, mode
# and model surface verify; historical evidence byte-identical; the old history-split check is run and its result kept
# as it is, then the 25 intended lines are checked by diff; docs audit and docs tests.
# usage: bash cmerge_gates.sh <verification sha> <run start sha> <candidate product commit>
set -u
M="$1"; START="$2"; PROD="$3"
PY=D:/Documents/projects/algo-sim/backend/.venv/Scripts/python.exe
export PYTHONIOENCODING=utf-8 PYTHONDONTWRITEBYTECODE=1
RUN=docs/evaluation/geometry/runs/cuboid-merge
echo "# cuboid-merge gates at $(git rev-parse HEAD) (clean detached worktree), start $START, product commit $PROD — 0 model calls"
echo "## git status (before)"; git status --porcelain | wc -l
echo "## product bytes (backend/app, frontend/src) changed since $START / since $PROD"
echo "changed: $(git diff --name-only "$START" "$M" -- backend/app frontend/src | wc -l) / $(git diff --name-only "$PROD" "$M" -- backend/app frontend/src | wc -l)"
echo "## candidate verify"; (cd backend && "$PY" scripts/freeze_evaluation_candidate.py --verify); echo "exit=$?"
echo "## cache identity verify"; (cd backend && "$PY" scripts/lock_cache_identity.py --verify); echo "exit=$?"
echo "## CACHE_VERSION"; grep -n 'CACHE_VERSION = ' backend/app/main.py
echo "## DEFAULT_MODE"; grep -n 'CHE_DO_MAC_DINH = ' backend/app/simulation/geometry_compiler/routing.py
S="backend/app/ai/skills backend/app/simulation/semantic_program/contract.py backend/app/simulation/semantic_program/grammar_card.py backend/app/simulation/product_capability.py docs/schemas frontend/src/simulations/domains/semantic/semantic_program.schema.json"
echo "## model surface changed since $START: $(git diff --name-only "$START" "$M" -- $S | wc -l)"
echo "## docs/evaluation changed since $START outside this run (allowed: docs/evaluation/README.md, the living navigation)"
git diff --name-status "$START" "$M" -- docs/evaluation ":(exclude)$RUN" | sed 's/^/  /'
echo "changed: $(git diff --name-only "$START" "$M" -- docs/evaluation ":(exclude)$RUN" | wc -l)"
echo "## docs/legacy changed since $START: $(git diff --name-only "$START" "$M" -- docs/legacy | wc -l)"
echo "## historical reports at the docs root changed since $START"
n=0; t=0; for f in $(grep -o '](\.\./\.\./docs/[A-Z0-9_]*\.md)\|](\.\./[A-Z0-9_]*\.md)' docs/evaluation/HISTORICAL_REPORTS.md | sed 's/^](//; s/)$//; s|^\.\./\.\./docs/|docs/|; s|^\.\./|docs/|' | sort -u); do
  t=$((t+1)); [ -n "$(git diff --name-only "$START" "$M" -- "$f")" ] && { echo "  changed: $f"; n=$((n+1)); }; done
echo "catalogued links changed: $n of $t (the living docs/EVIDENCE_INDEX.md linked from the catalogue introduction may change)"
echo "## old check, result kept as is: split_history_cfr.py --verify"
(cd backend && "$PY" ../docs/evaluation/geometry/runs/cuboid-final-review/diagnostics/split_history_cfr.py --verify); echo "exit=$?"
echo "## scope of that result: cuboid-acceptance/diagnostics/split_scope_cacc.py 903e874c"
"$PY" docs/evaluation/geometry/runs/cuboid-acceptance/diagnostics/split_scope_cacc.py 903e874c; echo "exit=$?"
echo "## git diff --check $START..$M (captured *.log excluded)"; git diff --check "$START" "$M" -- . ':(exclude)*.log'; echo "exit=$?"
echo "## docs audit"; "$PY" backend/scripts/audit_docs_information_architecture.py 2>&1 | tail -12; echo "exit=${PIPESTATUS[0]}"
echo "## docs tests (pytest)"
(cd backend && "$PY" -m pytest -q tests/geometry/test_docs_information_architecture.py tests/test_current_state_identity.py \
  tests/geometry/test_thesis_acceptance_matrix.py tests/semantic_program/test_evaluation_candidate.py 2>&1 | tail -2)
echo "## docs tests (vitest)"
(cd frontend && npx vitest run src/code-index-sync.test.ts src/rules-hygiene.test.ts src/certification-sweep.test.ts 2>&1 \
  | sed 's/\x1b\[[0-9;]*m//g' | grep -E '^ *(Test Files|Tests) |FAIL')
echo "## git status (after)"; git status --porcelain | wc -l; git status --porcelain | head -10
