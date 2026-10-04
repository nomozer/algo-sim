#!/usr/bin/env bash
# W18 identity gates — run from the worktree ROOT (cwd), 0 model calls.
# usage: bash w18_gates.sh <measurement sha> <wave base sha>
set -u
M="$1"; BASE="$2"
PY=D:/Documents/projects/algo-sim/backend/.venv/Scripts/python.exe
export PYTHONIOENCODING=utf-8 PYTHONDONTWRITEBYTECODE=1
echo "# W18 verification gates at $M in '<WT_ROOT>/w18 space/algo-sim' (clean detached worktree, path with a space), 0 model calls"
echo "## git status (before)"; git status --porcelain | wc -l
echo "## HEAD"; git rev-parse HEAD
echo "## candidate verify"; (cd backend && "$PY" scripts/freeze_evaluation_candidate.py --verify); echo "exit=$?"
echo "## cache identity verify"; (cd backend && "$PY" scripts/lock_cache_identity.py --verify); echo "exit=$?"
echo "## schema export x2"
for i in 1 2; do
  (cd backend && "$PY" scripts/export_semantic_program_schema.py > /dev/null); echo "export_exit=$?"
  a=$(sha256sum docs/schemas/semantic_program.schema.json | cut -d' ' -f1)
  b=$(sha256sum frontend/src/simulations/domains/semantic/semantic_program.schema.json | cut -d' ' -f1)
  echo "$a $b  (run $i)"
done
echo "git diff after export: $(git status --porcelain | wc -l) changed"
echo "## DEFAULT_MODE"
grep -n 'CHE_DO_MAC_DINH = ' backend/app/simulation/geometry_compiler/routing.py
echo "routing.py changed since $BASE: $(git diff --name-only "$BASE" "$M" -- backend/app/simulation/geometry_compiler/routing.py | wc -l)"
echo "geometry_compiler referenced from app/ai or main.py (non-comment): $(grep -rn --include=*.py geometry_compiler backend/app/ai backend/app/main.py | grep -v '^[^:]*:[0-9]*:\s*#' | wc -l)"
echo "FIXTURE_TIN_CAY referenced from app/ai, app/main.py, app/api: $(grep -rn --include=*.py FIXTURE_TIN_CAY backend/app/ai backend/app/main.py backend/app/api 2>/dev/null | wc -l)"
echo "## model surface: prompts, grammar card, schemas, capability changed since $BASE"
git diff --name-only "$BASE" "$M" -- backend/app/ai/skills backend/app/simulation/semantic_program/contract.py backend/app/simulation/semantic_program/grammar_card.py backend/app/simulation/product_capability.py docs/schemas frontend/src/simulations/domains/semantic/semantic_program.schema.json | sed 's/^/  changed: /'; echo "model-surface files changed: $(git diff --name-only "$BASE" "$M" -- backend/app/ai/skills backend/app/simulation/semantic_program/contract.py backend/app/simulation/semantic_program/grammar_card.py backend/app/simulation/product_capability.py docs/schemas frontend/src/simulations/domains/semantic/semantic_program.schema.json | wc -l)"
echo "## CACHE_VERSION"; grep -n 'CACHE_VERSION = ' backend/app/main.py
echo "## git diff --check $BASE..$M (captured *.log excluded: verbatim pytest/npm output may carry trailing spaces)"
git diff --check "$BASE" "$M" -- . ':(exclude)*.log'; echo "exit=$?"
echo "## node harness tests"
node --test frontend/scripts/*.node-test.mjs 2>&1 | grep -E '^ℹ (tests|pass|fail|skipped)'
echo "## git status (after)"; git status --porcelain | wc -l
