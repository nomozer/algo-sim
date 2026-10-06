#!/usr/bin/env bash
# regular-square-pyramid-w04 (copy of w03_gates.sh; RUN points at the W4 run) identity and integrity gates (pattern of w20-cleanup-premerge/diagnostics/w20_gates.sh) — run from the ROOT of a clean
# detached worktree (cwd), 0 model calls.
# usage: bash w04_gates.sh <verification sha> <wave start sha> <python>   (CRLF checkout: pipe through tr -d "\r")
set -u
M="$1"; START="$2"; PY="$3"
export PYTHONIOENCODING=utf-8 PYTHONDONTWRITEBYTECODE=1
RUN=docs/evaluation/geometry/runs/regular-square-pyramid-w04
echo "# regular-square-pyramid-w04 verification gates at $M (clean detached worktree, path with a space), 0 model calls"
echo "## git status (before)"; git status --porcelain | wc -l
echo "## HEAD"; git rev-parse HEAD
echo "## candidate verify"; (cd backend && "$PY" scripts/freeze_evaluation_candidate.py --verify); echo "exit=$?"
echo "## cache identity verify"; (cd backend && "$PY" scripts/lock_cache_identity.py --verify); echo "exit=$?"
echo "## schema export x2 (idempotence: the two mirrors byte-identical, git status unchanged)"
for i in 1 2; do
  (cd backend && "$PY" scripts/export_semantic_program_schema.py > /dev/null); echo "export_exit=$?"
  a=$(sha256sum docs/schemas/semantic_program.schema.json | cut -d' ' -f1)
  b=$(sha256sum frontend/src/simulations/domains/semantic/semantic_program.schema.json | cut -d' ' -f1)
  echo "$a $b  (run $i)"
done
echo "git status after export: $(git status --porcelain | wc -l) changed"
echo "## DEFAULT_MODE"
grep -n 'CHE_DO_MAC_DINH = ' backend/app/simulation/geometry_compiler/routing.py
echo "routing.py changed since $START: $(git diff --name-only "$START" "$M" -- backend/app/simulation/geometry_compiler/routing.py | wc -l)"
echo "geometry_compiler referenced from app/ai or main.py (non-comment): $(grep -rn --include=*.py geometry_compiler backend/app/ai backend/app/main.py | grep -v '^[^:]*:[0-9]*:\s*#' | wc -l)"
echo "FIXTURE_TIN_CAY referenced from app/ai, app/main.py, app/api: $(grep -rn --include=*.py FIXTURE_TIN_CAY backend/app/ai backend/app/main.py backend/app/api 2>/dev/null | wc -l)"
echo "## model surface: prompts, grammar card, schemas, capability changed since $START"
S="backend/app/ai/skills backend/app/simulation/semantic_program/contract.py backend/app/simulation/semantic_program/grammar_card.py backend/app/simulation/product_capability.py docs/schemas frontend/src/simulations/domains/semantic/semantic_program.schema.json"
git diff --name-only "$START" "$M" -- $S | sed 's/^/  changed: /'; echo "model-surface files changed: $(git diff --name-only "$START" "$M" -- $S | wc -l)"
echo "## CACHE_VERSION"; grep -n 'CACHE_VERSION = ' backend/app/main.py
echo "## historical evidence byte-identical since $START (tracked docs/evaluation outside the W4 run folder)"
git diff --name-status "$START" "$M" -- docs/evaluation ":(exclude)$RUN" | sed 's/^/  /'
echo "changed outside the W4 run: $(git diff --name-only "$START" "$M" -- docs/evaluation ":(exclude)$RUN" | wc -l) (allowed: the living candidate registry and divergence declaration)"
echo "## historical reports at the docs root (catalogued in docs/evaluation/HISTORICAL_REPORTS.md) changed since $START"
n=0; for f in $(grep -o '](\.\./\.\./docs/[A-Z0-9_]*\.md)\|](\.\./[A-Z0-9_]*\.md)' docs/evaluation/HISTORICAL_REPORTS.md | sed 's/^](//; s/)$//; s|^\.\./\.\./docs/|docs/|; s|^\.\./|docs/|' | sort -u); do
  [ -n "$(git diff --name-only "$START" "$M" -- "$f")" ] && { echo "  changed: $f"; n=$((n+1)); }; done
echo "catalogued reports changed: $n of $(grep -o '](\.\./\.\./docs/[A-Z0-9_]*\.md)\|](\.\./[A-Z0-9_]*\.md)' docs/evaluation/HISTORICAL_REPORTS.md | sort -u | wc -l)"
echo "## git diff --check $START..$M (captured *.log excluded: verbatim tool output may carry trailing spaces)"
git diff --check "$START" "$M" -- . ':(exclude)*.log'; echo "exit=$?"
echo "## docs audit"; "$PY" backend/scripts/audit_docs_information_architecture.py 2>&1 | tail -12; echo "exit=${PIPESTATUS[0]}"
echo "## node harness tests"
node --test frontend/scripts/*.node-test.mjs 2>&1 | grep -E '^(ℹ|#) (tests|pass|fail|skipped)'  # TTY prints ℹ, a pipe prints TAP #
echo "## git status (after)"; git status --porcelain | wc -l; git status --porcelain | head -20
