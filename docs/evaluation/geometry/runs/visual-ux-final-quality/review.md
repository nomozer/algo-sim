# Bounded independent review

Reviewer: `/root/independent_quality_review` (fresh context, read-only).

Initial product reviewed: `7ce563b30488571180e167e50689e501531e7baa` against source `f6a8e30fb70d377c5a8a97db476ebd4d7c090336`.

One confirmed must-fix: `CURVED_PLANE_DOES_NOT_CUT` is shared by sphere, cylinder and cone refusal producers. A sphere-only explanation would falsely describe failed cylinder/cone cuts. Two new regression tests reproduced this error. Fixed by retaining the backend's human explanation and removing exact structured code tokens only from the main explanation; raw reason/code remain in diagnostics. No backend changes.

Correction review at `56328b17462e9c4e903dc17687da07243d06846d`: **INDEPENDENT_REVIEW_PASS**, no remaining confirmed findings. Reviewer independently ran 63 focused tests (4 files), inspected the recorded 1178-test/build pass, the cut-reason change, and the initial camera bounds correction. The enclosing radial box corners contain the full curved surfaces; cone bounds expand only at the base and retain the apex. The in-progress final browser receipt showed seven served scenes, equal initial/reset cameras, no rendering errors, and passing normal/x-ray depth checks. Final browser completion and authoritative T3 are separate acceptance gates.

Review limits: actual section fill geometry is tested against a synthetic opaque wall with independently established ray order; this is not an exhaustive oracle for every solid/camera combination. Verified mapping gaps use generic labels rather than expose internal identifiers. No whole-repository audit, live AI, merge or push.
