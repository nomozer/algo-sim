#!/usr/bin/env bash
# regular-square-pyramid-w03 (copy of the w02 script; outputs go to the W3 run, W2 artifacts untouched) — authoritative browser measurement, 0 model calls. Run from the ROOT of a clean detached
# worktree whose path contains a space (cwd). Logs go to $LOGS (outside the worktree, so the tree stays clean).
# usage: bash w02_measure.sh <python> <logs dir>
set -u
PY="$1"; LOGS="$2"; M=$(git rev-parse HEAD); S=${M:0:8}
RUN=docs/evaluation/geometry/runs/regular-square-pyramid-w03
export PYTHONIOENCODING=utf-8 PYTHONDONTWRITEBYTECODE=1
mkdir -p "$LOGS"
step() { local name="$1"; shift; { echo "# cwd: <worktree '$(pwd)'> @ $M; $*"; date -u +%FT%TZ; "$@"; echo "exit=$?"; } > "$LOGS/${name}_${S}.log" 2>&1; tail -1 "$LOGS/${name}_${S}.log"; }
echo "status_before=$(git status --porcelain | wc -l)"
step FIXTURES bash -c "cd backend && $PY scripts/freeze_evaluation_candidate.py --verify && $PY scripts/lock_cache_identity.py --verify && $PY scripts/generate_generic_tier_a_fixtures.py --out ../$RUN/inputs"
grep -q "^exit=0$" "$LOGS/FIXTURES_${S}.log" || { echo "STOP: candidate/cache verify or fixtures failed"; exit 1; }
step BROWSER_SUITE node frontend/scripts/compiler-scene-replay.mjs --suite frontend/scripts/generic-tier-a-scenarios.json --fixture-root $RUN/inputs --ra $RUN/results --screenshots $RUN/images
step W02_PROBE node frontend/scripts/w02-closure-probe.mjs --fixture-root $RUN/inputs --ra $RUN/results --anh $RUN/images --bo-qua-build
step OCCLUSION bash -c "cd backend && $PY scripts/measure_scene3d_occlusion.py --fixture-root ../$RUN/inputs --browser ../$RUN/results/BROWSER_EVIDENCE.json --expectations ../docs/evaluation/geometry/runs/20260928-cross-family-hidden-line-occlusion-oracle-and-formation-repair/inputs/human_expected_visibility.json --camera-preimages ../docs/evaluation/geometry/runs/w09-verify-cleanup/inputs/REGISTERED_CAMERA_PREIMAGES.json --declared-camera-change W10_PEDAGOGICAL_CAMERA_CHOSEN_FROM_SCENE_METRICS --registered-fixture-root ../docs/evaluation/geometry/runs/20260928-cross-family-hidden-line-occlusion-oracle-and-formation-repair/inputs --pending-human-review --output ../$RUN/results/OCCLUSION_MEASUREMENT.json"
step PLAYBACK timeout --signal=KILL 2400 node frontend/scripts/scene3d-playback-check.mjs --theo-ho --lap-orbit 5 --fixture-root $RUN/inputs --ra $RUN/images --bo-qua-build
mv $RUN/images/PLAYBACK_EVIDENCE.json $RUN/results/PLAYBACK_EVIDENCE.json  # same move as W1
step EVIDENCE_BUILDER bash -c "cd backend && $PY scripts/build_scene3d_visual_evidence.py --run-dir ../$RUN --browser ../$RUN/results/BROWSER_EVIDENCE.json --measurement ../$RUN/results/OCCLUSION_MEASUREMENT.json --fixture-root ../$RUN/inputs --expectations ../docs/evaluation/geometry/runs/20260928-cross-family-hidden-line-occlusion-oracle-and-formation-repair/inputs/human_expected_visibility.json --playback ../$RUN/results/PLAYBACK_EVIDENCE.json"
echo "status_after (run outputs only expected):"; git status --porcelain | grep -v "^?? $RUN/\| $RUN/" | head
