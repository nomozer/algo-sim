#!/usr/bin/env bash
# phone-landscape-layout — browser measurement of every family on the final candidate, 0 model calls. The full Tier-A
# suite runs ONCE over all eight families (no --ho filter, no merged partial results); the D5/landscape probe covers six
# viewports (390x844, 360x640, 844x390, 667x375, 1366x650, 1440x900); scene controls, panels, focus mode, occlusion, playback.
# Run from the ROOT of a clean detached worktree whose path contains a space; logs go to $LOGS (outside the worktree).
# Screenshots follow frontend/scripts/capture-policy.mjs, mode toi-thieu, with the review set chosen before the run.
# usage: tr -d '\r' < measure.sh | bash -s -- <python> <logs dir>
set -u
PY="$1"; LOGS="$2"; M=$(git rev-parse HEAD); S=${M:0:8}
RUN=docs/evaluation/geometry/runs/phone-landscape-layout
HO=triangular_pyramid,rectangular_pyramid,triangular_prism,cuboid,cube,cross_section,regular_square_pyramid,regular_triangular_pyramid
POL="--anh-che-do toi-thieu --review-set $RUN/inputs/REVIEW_SET.json"
OCC=docs/evaluation/geometry/runs/20260928-cross-family-hidden-line-occlusion-oracle-and-formation-repair/inputs
export PYTHONIOENCODING=utf-8 PYTHONDONTWRITEBYTECODE=1
mkdir -p "$LOGS"
step() { local name="$1"; shift; { echo "# cwd: <worktree '$(pwd)'> @ $M; $*"; date -u +%FT%TZ; "$@"; echo "exit=$?"; date -u +%FT%TZ; } > "$LOGS/${name}_${S}.log" 2>&1; tail -2 "$LOGS/${name}_${S}.log" | head -1; }
echo "status_before=$(git status --porcelain | wc -l)"
step fixtures bash -c "cd backend && $PY scripts/freeze_evaluation_candidate.py --verify && $PY scripts/lock_cache_identity.py --verify && $PY scripts/generate_generic_tier_a_fixtures.py --out ../$RUN/inputs"
grep -q "^exit=0$" "$LOGS/fixtures_${S}.log" || { echo "STOP: candidate/cache verify or fixtures failed"; exit 1; }
step build bash -c "cd frontend && npm run build"
step mobile_layout timeout --signal=KILL 2400 node frontend/scripts/check-mobile-layout.mjs --fixture-root $RUN/inputs --ra $RUN/results --anh $RUN/images/mobile --bo-qua-build $POL
step suite node frontend/scripts/compiler-scene-replay.mjs --suite frontend/scripts/generic-tier-a-scenarios.json --fixture-root $RUN/inputs --ra $RUN/results --screenshots $RUN/images --bo-qua-build $POL
step scene_controls timeout --signal=KILL 2400 node frontend/scripts/check-scene-controls.mjs --ho $HO --fixture-root $RUN/inputs --ra $RUN/results --anh $RUN/images --bo-qua-build $POL
step panels timeout --signal=KILL 2400 node frontend/scripts/check-panels.mjs --ho $HO --fixture-root $RUN/inputs --ra $RUN/results --anh $RUN/images/review --bo-qua-build $POL
step focus_mode timeout --signal=KILL 2400 node frontend/scripts/check-focus-mode.mjs --ho $HO --fixture-root $RUN/inputs --ra $RUN/results --anh $RUN/images/focus --bo-qua-build $POL
step occlusion bash -c "cd backend && $PY scripts/measure_scene3d_occlusion.py --fixture-root ../$RUN/inputs --browser ../$RUN/results/BROWSER_EVIDENCE.json --expectations ../$OCC/human_expected_visibility.json --camera-preimages ../docs/evaluation/geometry/runs/w09-verify-cleanup/inputs/REGISTERED_CAMERA_PREIMAGES.json --declared-camera-change W10_PEDAGOGICAL_CAMERA_CHOSEN_FROM_SCENE_METRICS --registered-fixture-root ../$OCC --pending-human-review --output ../$RUN/results/OCCLUSION_MEASUREMENT.json"
step playback timeout --signal=KILL 2400 node frontend/scripts/scene3d-playback-check.mjs --families $HO --theo-ho --lap-orbit 5 --fixture-root $RUN/inputs --ra $RUN/images --bo-qua-build $POL
mv $RUN/images/PLAYBACK_EVIDENCE.json $RUN/results/PLAYBACK_EVIDENCE.json
step evidence bash -c "cd backend && $PY scripts/build_scene3d_visual_evidence.py --run-dir ../$RUN --browser ../$RUN/results/BROWSER_EVIDENCE.json --measurement ../$RUN/results/OCCLUSION_MEASUREMENT.json --fixture-root ../$RUN/inputs --expectations ../$OCC/human_expected_visibility.json --playback ../$RUN/results/PLAYBACK_EVIDENCE.json"
echo "images on disk: $(find $RUN/images -name '*.png' 2>/dev/null | wc -l)"
echo "status_after (run outputs only expected):"; git status --porcelain | grep -v "^?? $RUN/\| $RUN/" | head
