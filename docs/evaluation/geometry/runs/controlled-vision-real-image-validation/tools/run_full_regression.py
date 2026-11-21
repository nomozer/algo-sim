"""Run the canonical offline gates for this run by reusing the previous run's runner unchanged.

Only the receipt directory and the publication-range base move to this run. Run from the worktree root with
the backend interpreter:  python docs/evaluation/geometry/runs/controlled-vision-real-image-validation/tools/run_full_regression.py --phase final
"""
from pathlib import Path
import sys

RUN = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RUN.parent / "real-image-ocr-vision-comparative-acceptance/tools"))
import run_regression  # noqa: E402

run_regression.RUN = RUN
run_regression.BASELINE = "44807b13bffe608153bc58e453a3bc9c37703485"  # report HEAD this run started from

if __name__ == "__main__":
    raise SystemExit(run_regression.main())
