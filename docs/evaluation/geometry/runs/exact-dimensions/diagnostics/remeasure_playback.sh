#!/usr/bin/env bash
# exact-dimensions — attempt 3: playback crashed in attempt 2 (fe83c46e) on a harness bug — chatLuongGocNhin handed
# world-space NUMBERS to the product's fraction-string parser (cauTrucGocNhin). Fixed by parsing the chart scene and
# mapping the parsed points (diemTheGioi). Rerun ONLY playback and the evidence builder that reads it; suite and
# occlusion of attempt 2 stand (they never call this function). Same worktree, moved to the fix commit.
# usage: tr -d '\r' < remeasure_playback.sh | bash -s -- <python> <logs dir>
set -u
PY="$1"; LOGS="$2"; M=$(git rev-parse HEAD); S=${M:0:8}
RUN=docs/evaluation/geometry/runs/exact-dimensions
POL="--anh-che-do toi-thieu --review-set $RUN/inputs/REVIEW_SET.json"
export PYTHONIOENCODING=utf-8 PYTHONDONTWRITEBYTECODE=1
mkdir -p "$LOGS"
step() { local name="$1"; shift; { echo "# cwd: <worktree '$(pwd)'> @ $M; $*"; date -u +%FT%TZ; "$@"; echo "exit=$?"; date -u +%FT%TZ; } > "$LOGS/${name}_${S}.log" 2>&1; tail -2 "$LOGS/${name}_${S}.log" | head -1; }
rm -rf $RUN/images/regular-triangular-pyramid/playback $RUN/results/PLAYBACK_EVIDENCE.json $RUN/results/EVIDENCE_IMAGE_INPUTS.json $RUN/results/HIDDEN_EDGE_CROPS.json $RUN/images/regular-triangular-pyramid/hidden-edges
step playback timeout --signal=KILL 1200 node frontend/scripts/scene3d-playback-check.mjs --families regular_triangular_pyramid --theo-ho --lap-orbit 5 --fixture-root $RUN/inputs --ra $RUN/images --bo-qua-build $POL
mv $RUN/images/PLAYBACK_EVIDENCE.json $RUN/results/PLAYBACK_EVIDENCE.json
step evidence bash -c "cd backend && $PY scripts/build_scene3d_visual_evidence.py --run-dir ../$RUN --browser ../$RUN/results/BROWSER_EVIDENCE.json --measurement ../$RUN/results/OCCLUSION_MEASUREMENT.json --fixture-root ../$RUN/inputs --expectations ../docs/evaluation/geometry/runs/20260928-cross-family-hidden-line-occlusion-oracle-and-formation-repair/inputs/human_expected_visibility.json --playback ../$RUN/results/PLAYBACK_EVIDENCE.json"
echo "images on disk: $(find $RUN/images -name '*.png' 2>/dev/null | wc -l)"
echo "status_after (run outputs only expected):"; git status --porcelain | grep -v "^?? $RUN/\| $RUN/" | head
