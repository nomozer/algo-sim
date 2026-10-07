#!/usr/bin/env bash
# exact-dimensions — attempt 2: rerun ONLY the steps attempt 1 failed (suite, playback) and the two that read
# their output (occlusion, evidence), after the harness fix d4834d92 (attempt1/SUMMARY.json). Not rerun, kept valid:
# fixtures (generator unchanged), build (frontend/src unchanged ⇒ same dist), scene_controls, panels, focus_mode
# (all PASS at 3bbb8052; their code paths do not touch the fixed functions).
# Run from the ROOT of the same detached worktree, moved to the fix commit; logs go to $LOGS.
# usage: tr -d '\r' < remeasure.sh | bash -s -- <python> <logs dir>
set -u
PY="$1"; LOGS="$2"; M=$(git rev-parse HEAD); S=${M:0:8}
RUN=docs/evaluation/geometry/runs/exact-dimensions
HO=regular_triangular_pyramid
POL="--anh-che-do toi-thieu --review-set $RUN/inputs/REVIEW_SET.json"
export PYTHONIOENCODING=utf-8 PYTHONDONTWRITEBYTECODE=1
mkdir -p "$LOGS"
step() { local name="$1"; shift; { echo "# cwd: <worktree '$(pwd)'> @ $M; $*"; date -u +%FT%TZ; "$@"; echo "exit=$?"; date -u +%FT%TZ; } > "$LOGS/${name}_${S}.log" 2>&1; tail -2 "$LOGS/${name}_${S}.log" | head -1; }
# Attempt-1 outputs of the rerun steps go away first (recorded in attempt1/SUMMARY.json); probe outputs stay.
rm -rf $RUN/images/regular-triangular-pyramid $RUN/results/BROWSER_EVIDENCE.json $RUN/results/PLAYBACK_EVIDENCE.json \
  $RUN/results/OCCLUSION_MEASUREMENT.json $RUN/results/EVIDENCE_IMAGE_INPUTS.json $RUN/results/HIDDEN_EDGE_CROPS.json
step suite node frontend/scripts/compiler-scene-replay.mjs --suite frontend/scripts/generic-tier-a-scenarios.json --fixture-root $RUN/inputs --ra $RUN/results --screenshots $RUN/images --bo-qua-build --ho $HO $POL
step occlusion bash -c "cd backend && $PY scripts/measure_scene3d_occlusion.py --fixture-root ../$RUN/inputs --browser ../$RUN/results/BROWSER_EVIDENCE.json --expectations ../docs/evaluation/geometry/runs/20260928-cross-family-hidden-line-occlusion-oracle-and-formation-repair/inputs/human_expected_visibility.json --camera-preimages ../docs/evaluation/geometry/runs/w09-verify-cleanup/inputs/REGISTERED_CAMERA_PREIMAGES.json --declared-camera-change W10_PEDAGOGICAL_CAMERA_CHOSEN_FROM_SCENE_METRICS --registered-fixture-root ../docs/evaluation/geometry/runs/20260928-cross-family-hidden-line-occlusion-oracle-and-formation-repair/inputs --pending-human-review --output ../$RUN/results/OCCLUSION_MEASUREMENT.json"
step playback timeout --signal=KILL 1200 node frontend/scripts/scene3d-playback-check.mjs --families $HO --theo-ho --lap-orbit 5 --fixture-root $RUN/inputs --ra $RUN/images --bo-qua-build $POL
mv $RUN/images/PLAYBACK_EVIDENCE.json $RUN/results/PLAYBACK_EVIDENCE.json
step evidence bash -c "cd backend && $PY scripts/build_scene3d_visual_evidence.py --run-dir ../$RUN --browser ../$RUN/results/BROWSER_EVIDENCE.json --measurement ../$RUN/results/OCCLUSION_MEASUREMENT.json --fixture-root ../$RUN/inputs --expectations ../docs/evaluation/geometry/runs/20260928-cross-family-hidden-line-occlusion-oracle-and-formation-repair/inputs/human_expected_visibility.json --playback ../$RUN/results/PLAYBACK_EVIDENCE.json"
echo "images on disk: $(find $RUN/images -name '*.png' 2>/dev/null | wc -l)"
echo "status_after (run outputs only expected):"; git status --porcelain | grep -v "^?? $RUN/\| $RUN/" | head
