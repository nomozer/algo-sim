"""Image-to-Scene3D on the controlled-vision images with this run's candidate: the previous run's evaluator, unchanged,
with every receipt written HERE (its manifest and transcriptions are only read). Needs measured_app on :8767 in
local-first mode with ALLOW_LIVE_AI=0.  Run from backend/:  python <tools>/image_after.py api|summarize
"""
import sys
from pathlib import Path

RUN = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RUN.parent / "controlled-vision-real-image-validation/tools"))
import evaluate_images as EV  # noqa: E402

EV.E.RUN = RUN               # receipts and headers -> this run
if __name__ == "__main__":
    step = sys.argv[1]
    if step == "api":
        for part in ("development", "frozen_external_evaluation"):
            EV.api(part)
    else:
        raise SystemExit("summarize via image_before_after.py")
