# 20260928-w09-verify-cleanup

Verification cleanup after the occlusion repair. Start with `REPORT.md`; the decision
fields are in `HANDOFF.md`, identity in `RUN.json`, file hashes in `MANIFEST.json`.

| Path | Content |
|---|---|
| `inputs/REGISTERED_CAMERA_PREIMAGES.json` | Snapshot strings whose sha256 equals each registered camera hash |
| `inputs/CANDIDATE_DIVERGENCE_CORRECTION.json` | Current candidate declaration (corrects the 20260927 one) |
| `results/VERIFICATION_SUMMARY.json` | Gate-by-gate machine summary |
| `results/BACKEND_FAILURE_RECONCILIATION.json` | Each reproduced backend failure → cause, repair, proving test, golden decision |
| `results/BROWSER_EVIDENCE.json` · `results/OCCLUSION_MEASUREMENT.json` | Authoritative browser run and oracle join |
| `images/` | `contact-sheet.png`, `crops/<family>/`, `screenshots/<family>/<viewport>/` (desktop, mobile, formation frames) |
| `diagnostics/` | Fresh failure inventory before any change, measurement attempts, detached logs |

`results/BROWSER_EVIDENCE.json` records screenshot paths relative to the measurement
worktree (`../w09-out/final4/images/...`); they map to `images/...` here and every one
is checked by sha256 in `MANIFEST.json`.
