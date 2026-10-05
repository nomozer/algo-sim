#!/usr/bin/env bash
# cuboid-acceptance — focused checks of the 24 rows of ARCHITECTURE_MAP §5 whose recorded enforcement pointers were
# stale (#1–#12, #14–#16, #18, #20–#26, #29; #9 and #12 point "như trên" at the dead pointers of #8 and #11).
# Run from the ROOT of a checkout (the authoritative run: a clean detached worktree); 0 model calls, 0 network.
#   part 1  old pointers of each row: still tracked, or the commit that deleted them
#   part 2  current pointers the reconciliation cites: file tracked and symbol present
#   part 3  focused pytest on the assertions cited per row
#   part 4  focused vitest (needs frontend/node_modules; --no-vitest skips it)
#   part 5  static probe for row #14: every backend/scripts/*.py that names the model or the pipeline, with the opt-in
#           it checks, whether it swaps `call_gemini` for a stub, and its call sites. A heuristic listing, read by hand:
#           a row with no opt-in, no stub and call sites is a candidate; 0 call sites does not prove a script model-free
# usage: bash invariant_checks_cacc.sh [--no-vitest]
set -u
PY=D:/Documents/projects/algo-sim/backend/.venv/Scripts/python.exe
export PYTHONIOENCODING=utf-8 PYTHONDONTWRITEBYTECODE=1
VITEST=1; [ "${1:-}" = "--no-vitest" ] && VITEST=0
echo "# cuboid-acceptance invariant checks at $(git rev-parse HEAD) — 0 model calls"
echo "## git status (before)"; git status --porcelain | wc -l

echo "## part 1 — old pointers (row · pattern · TRACKED path | absent + deleting commit)"
old() { r="$1"; shift; for b in "$@"; do
  t=$(git ls-files -- ":(glob)**/$b" | head -1)
  if [ -n "$t" ]; then echo "#$r  $b  TRACKED $t"
  else d=$(git log --diff-filter=D --format='%h %ad' --date=short -1 -- ":(glob)**/$b"); echo "#$r  $b  absent (deleted ${d:-NOT_FOUND})"; fi
done; }
sym() { r="$1"; shift; for s in "$@"; do
  n=$(git grep -l -w "$s" -- backend/app frontend/src ':(exclude)*.test.*' | wc -l)
  echo "#$r  symbol $s  in $n non-test source file(s)"; done; }
old 1 test_pipeline.py; sym 1 test_simulate_sinh_timeline_bi_chan FORBIDDEN
old 2 algorithms.test.ts generic.test.ts
old 3 patch.test.ts; sym 3 WorkspaceProps
old 4 manifest.py test_manifest.py
old 5 test_capability_boundary.py
old 6 test_reuse.py
old 7 patterns.py test_patterns.py
old 8 representation.py test_capability_boundary.py; sym 8 build_representation_plan check_semantic_compatibility
old 10 patch.test.ts registry.test.ts
old 11 patch.test.ts; sym 11 InteractionFeedback
sym 12 GenericState
old 14 evaluation/live.py test_live_budget.py
old 15 patch.py test_patch.py
old 16 renderer.ts SimulationWorkspace.tsx visual-mode.test.tsx render3d.test.tsx m8-acceptance.test.tsx
old 18 node-glyph.ts representation-policy-w4b2r.test.ts encap-render3d.test.tsx; sym 18 representationPolicyOf threeD
old 20 dsl/validator.py generic/validate.ts generic_engine.py generic/model.ts dsl-contract.json generate_dsl_contract.py \
  test_dsl.py test_generic_engine_m13.py test_manifest_providers.py test_m13_dijkstra_fixture.py test_m13_pattern_revalidate.py
old 21 computation_gate.py test_m13_routing.py datasets/capability.py
old 22 ai/pipeline.py evaluation/observer.py evaluation/harness.py m16_record.py m16_metrics.py m16_offline_scripts.py \
  test_eval_convergence.py test_eval_parity.py test_eval_side_effects.py test_m16_offline_eval.py
sym 22 AttemptObserver evaluate_item
old 23 mechanisms.py descriptor.py mechanism_gate.py test_mechanisms.py test_descriptor.py test_capability_descriptors.py \
  test_pipeline_mechanism_consistency.py test_mechanism_gate.py; sym 23 classify_with_one_route_recovery
old 24 state/store.ts SimulationControls.tsx algorithm/interaction-policy.ts explore-ownership-w4b3a.test.ts \
  secondary-actions-w4b2w.test.ts workspace-lifecycle.test.ts interaction-family-w1.test.tsx accept-w4b3a.mjs
sym 24 exploreOpen exploreEntry challengeOpen challengeEntry
old 25 'spec-drift-w4b4d.test.ts*' accept-experience-w4b4c.mjs; sym 25 specDrift currentConfig
old 26 experience-audit-w4b4a.test.ts condition-param.ts condition-param.test.ts
old 29 accounts/policy.py accounts/router.py AppSidebar.tsx test_auth_api.py test_classroom_api.py ux-shell.test.tsx \
  accept-classroom-m18.mjs

echo "## part 2 — current pointers (row · path::symbol)"
cur() { r="$1"; p="$2"; s="${3:-}"
  if ! git ls-files --error-unmatch -- "$p" >/dev/null 2>&1; then echo "#$r  MISSING_FILE $p"
  elif [ -n "$s" ] && ! git grep -q -F -- "$s" "$p"; then echo "#$r  MISSING_SYMBOL $p :: $s"
  else echo "#$r  ok $p${s:+ :: $s}"; fi; }
SP=backend/app/simulation/semantic_program; GEO=frontend/src/simulations/domains/geometry
cur 1 $SP/contract.py "class ConstructPointStmt"; cur 1 $SP/validator.py "def validate_semantic_program"
cur 1 $SP/geometry_exec.py; cur 1 $SP/pipeline_adapter.py "def compile_semantic_program_to_envelope"
cur 2 backend/app/simulation/geometry/exact.py; cur 2 $SP/interpreter.py
cur 2 docs/evaluation/geometry/custodian/geometry_oracle.py
cur 3 $GEO/interaction-state.ts "export function explode"; cur 3 $GEO/scene3d-model.ts "export function objectsAt"
cur 3 $GEO/Scene3DExplorer.tsx
cur 8 backend/app/simulation/semantic_program/domain_profile.py "def detect_domain"; cur 8 $SP/coverage_gate.py
cur 8 $SP/grounding_gate.py "def check_grounding"; cur 8 $SP/assumption_gate.py "def kiem_gia_dinh"
cur 8 $SP/construction_binding.py "def doi_chieu_phep_dung"; cur 8 backend/app/simulation/product_capability.py
cur 8 $SP/route.py "def verify_and_compile"
cur 9 $SP/geometry_obligations.py "GEOMETRY_CHECKERS = {"; cur 9 backend/app/learner_messages.py
cur 9 $SP/refusal_cause.py
cur 11 frontend/src/simulations/no-verdict.test.ts
cur 14 backend/conftest.py; cur 14 backend/scripts/run_geometry_dev_evaluation.py ALLOW_LIVE_AI
cur 21 $SP/coverage_gate.py
cur 22 backend/app/ai/pipeline.py "observer=None"; cur 22 backend/scripts/run_thesis_final_acceptance.py "pipeline.stage_semantic_program("
cur 22 backend/scripts/run_thesis_final_acceptance.py "verify_and_compile"
cur 29 backend/app/accounts/policy.py "def resolve_signup_role"; cur 29 backend/app/accounts/router.py "require_role"
cur 29 frontend/src/components/TopNav.tsx "export function itemsForRole"

echo "## part 3 — focused pytest"
G=tests/geometry; S=tests/semantic_program
(cd backend && "$PY" -m pytest -q \
  "$G/test_geometry_ir.py::test_R0_cau_lenh_dung_KHONG_co_truong_toa_do_ket_qua" \
  "$G/test_geometry_ir.py::test_R0_bieu_thuc_hinh_hoc_chi_nhan_TEN" \
  "$G/test_geometry_ir.py::test_R0_geometry_exec_khong_import_tang_AI" \
  "$G/test_refusal_truthful.py" \
  "$S/test_frame_state_invariant.py" \
  "$G/test_geometry_kernel.py::test_toa_do_la_HUU_TI_khong_phai_float" \
  "$G/test_geometry_kernel.py::test_dong_phang_o_ca_ma_FLOAT_TRA_LOI_SAI" \
  "$G/test_oracle_independence.py" \
  "$S/test_schema_sync.py" \
  "$G/test_geometry_route_independence.py" \
  "$G/test_geometry_coverage_gate.py" \
  "$S/test_coverage_gate_c1a.py" \
  "$G/test_assumption_gate.py" \
  "$G/test_construction_binding.py" \
  "$G/test_source_grounding_closure.py" \
  "$G/test_product_response_contract.py" \
  "$G/test_geometry_obligations.py" \
  "$G/test_geometry_ir.py::test_tham_chieu_ten_KHONG_KHAI_bi_VALIDATOR_bat_tinh" \
  "$G/test_geometry_ir.py::test_dung_SAI_KIEU_thi_hong" \
  "$G/test_geometry_ir.py::test_giao_duong_CHEO_NHAU_thi_chuong_trinh_HONG" \
  "$G/test_geometry_dev_runner.py::test_khong_co_ALLOW_LIVE_AI_thi_TU_CHOI" \
  "$G/test_holdout_protocol.py::test_khong_co_con_dau_thi_KHONG_chay_duoc" \
  tests/test_offline_guard.py \
  "tests/test_synthesis_repair_trace.py::test_F2_pipeline__final_memory_chuong_trinh_so_luot_GIONG_khi_co_observer" \
  "$G/test_thesis_runner_alignment.py" \
  tests/test_auth_api.py \
  tests/test_api.py::test_cache_version_9_cu_bi_invalidate_sau_bump_10 tests/test_api.py::test_khong_cache_ket_qua_unsupported 2>&1 \
  | grep -E 'passed|failed|error|FAILED|ERROR' | tail -20; exit "${PIPESTATUS[0]}"); echo "pytest_exit=$?"

if [ "$VITEST" = 1 ]; then
  echo "## part 4 — focused vitest"
  (cd frontend && npx vitest run src/simulations/no-verdict.test.ts src/simulations/registry.test.ts \
    src/simulations/domains/geometry/interaction-state.test.ts src/simulations/domains/geometry/scene3d-geometry-timeline.test.tsx \
    src/simulations/domains/geometry/semantic-dumb-frontend.test.ts src/simulations/domains/geometry/scene3d-occlusion-gates.test.ts \
    src/components/ux-shell.test.tsx src/components/canvas-first-shell.test.tsx src/llm/offline-guard.test.ts 2>&1 \
    | sed 's/\x1b\[[0-9;]*m//g' | grep -E '^ *(Test Files|Tests) |FAIL' ; exit "${PIPESTATUS[0]}"); echo "vitest_exit=$?"
fi

echo "## part 5 — row #14 static probe (script · opt-in tokens · call_gemini stubbed · call sites · loads backend/.env)"
for f in $(git grep -l "run_pipeline\|call_gemini\|genai\.\|GEMINI_API_KEY" -- 'backend/scripts/*.py'); do
  o=$(grep -o 'ALLOW_LIVE_AI\|"--live"\|--execute-live\|--confirm-live[a-z-]*' "$f" | sort -u | tr '\n' ' ')
  st=$(grep -c 'call_gemini = ' "$f")
  c=$(grep -c 'call_gemini(\|call_gemini_sync(\|generate_content(\|run_pipeline(\|stage_semantic_analyze(\|stage_semantic_program(\|AsyncHTTPTransport(' "$f")
  e=$(grep -c 'load_dotenv' "$f")
  echo "$(basename "$f")  opt-in=[${o% }]  stub=$st  calls=$c  dotenv=$e"
done | sort
echo "## git status (after)"; git status --porcelain | wc -l; git status --porcelain | head -10
