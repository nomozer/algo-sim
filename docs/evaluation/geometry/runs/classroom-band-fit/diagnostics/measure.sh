#!/usr/bin/env bash
# classroom-band-fit — browser measurement on the final candidate, 0 model calls. Adapted from
# runs/phone-landscape-layout/diagnostics/measure.sh. Steps: candidate/cache verify + fixtures, build, the classroom band
# probe (3 roles x 8 viewports), the phone/landscape probe for scenes WITHOUT a band (regression), the full Tier-A suite
# once over all eight families (no --ho filter), scene controls (W02), panels (W04), focus mode (W05).
# Not rerun (see plan.md §4): occlusion measurement, playback, evidence builder — renderer, camera fit and canvas sizing
# are untouched and the no-band layout is measured by the phone/landscape probe.
# Images: JSON first. Official probes write screenshots under $LOGS (outside the repo, not evidence); only the class band
# probe writes three after-images into the run (cases chosen before the run, plan.md §3).
# Run from the ROOT of a clean detached worktree whose path contains a space; logs go to $LOGS (outside the worktree).
# usage: tr -d '\r' < measure.sh | bash -s -- <python> <logs dir>
set -u
PY="$1"; LOGS="$2"; M=$(git rev-parse HEAD); S=${M:0:8}
RUN=docs/evaluation/geometry/runs/classroom-band-fit
HO=triangular_pyramid,rectangular_pyramid,triangular_prism,cuboid,cube,cross_section,regular_square_pyramid,regular_triangular_pyramid
POL="--anh-che-do toi-thieu"
IMG="$LOGS/images"
export PYTHONIOENCODING=utf-8 PYTHONDONTWRITEBYTECODE=1
mkdir -p "$LOGS" "$IMG"
step() { local name="$1"; shift; { echo "# cwd: <worktree '$(pwd)'> @ $M; $*"; date -u +%FT%TZ; "$@"; echo "exit=$?"; date -u +%FT%TZ; } > "$LOGS/${name}_${S}.log" 2>&1; tail -2 "$LOGS/${name}_${S}.log" | head -1; }
echo "status_before=$(git status --porcelain | wc -l)"
step fixtures bash -c "cd backend && $PY scripts/freeze_evaluation_candidate.py --verify && $PY scripts/lock_cache_identity.py --verify && $PY scripts/generate_generic_tier_a_fixtures.py --out ../$RUN/inputs"
grep -q "^exit=0$" "$LOGS/fixtures_${S}.log" || { echo "STOP: candidate/cache verify or fixtures failed"; exit 1; }
step build bash -c "cd frontend && npm run build"
step class_band timeout --signal=KILL 2400 node $RUN/diagnostics/probe-class-band-v2.mjs "$(pwd)" frontend/dist $RUN/results/CLASS_BAND_PROBE.json --fixture $RUN/inputs/fixtures/regular_square_pyramid_positive.json --shots $RUN/images/class-band --shot-cases student_live:landscape_640,teacher_live:landscape_640,student_live:portrait_small
step mobile_layout timeout --signal=KILL 2400 node frontend/scripts/check-mobile-layout.mjs --fixture-root $RUN/inputs --ra $RUN/results --anh "$IMG/mobile" --bo-qua-build $POL
step suite node frontend/scripts/compiler-scene-replay.mjs --suite frontend/scripts/generic-tier-a-scenarios.json --fixture-root $RUN/inputs --ra $RUN/results --screenshots "$IMG" --bo-qua-build $POL
step scene_controls timeout --signal=KILL 2400 node frontend/scripts/check-scene-controls.mjs --ho $HO --fixture-root $RUN/inputs --ra $RUN/results --anh "$IMG" --bo-qua-build $POL
step panels timeout --signal=KILL 2400 node frontend/scripts/check-panels.mjs --ho $HO --fixture-root $RUN/inputs --ra $RUN/results --anh "$IMG/review" --bo-qua-build $POL
step focus_mode timeout --signal=KILL 2400 node frontend/scripts/check-focus-mode.mjs --ho $HO --fixture-root $RUN/inputs --ra $RUN/results --anh "$IMG/focus" --bo-qua-build $POL
echo "images in run: $(find $RUN/images -name '*.png' 2>/dev/null | wc -l) · outside repo: $(find "$IMG" -name '*.png' 2>/dev/null | wc -l)"
echo "status_after (run outputs only expected):"; git status --porcelain | grep -v "^?? $RUN/\| $RUN/" | head
