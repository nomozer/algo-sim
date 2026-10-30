# Final independent review: READY (0 BLOCKER, 0 MAJOR); integration still gated on one Owner decision

**Who and what:** a fresh-context subagent of this session reviewed `e5dc3d28..738ac241`.

**Conditions:**
- Read-only: `git status` was clean before and after, and 0 provider calls were made.
- The base comparison used `git archive e5dc3d28 backend/app`.
- Copied probes, outputs and receipts are in `final-review/`. Hashes of every review file are in `final-review-files.sha256`, keyed by relative name. Five scripts embed a local path and `served_scenes.json` is 2.7 MB; those six, plus the scanner's registry snapshot `exc-e5dc.json`, are hashed but stay local.

## Findings

| id | sev | finding | disposition |
|---|---|---|---|
| F1 | MINOR | `pre-freeze-review-files.sha256` holds absolute local paths (Windows user name, session scratch dir), and `pre-freeze-review/probes.py:12` hardcodes the worktree path. The scanner has no local-path rule. Main already carries 69 files with such paths. No credential is involved. | **Disclosed for the Owner.** It is already in branch history, which is not rewritten. This review's own hash list uses relative names only. The W3-F2 practice of treating local-path disclosure as an Owner call is kept; see `handoff.md`. |
| F2 | MINOR | The run's `frozen-evaluation-candidate.json` was overwritten in place at `182a7785`, replacing the earlier W4 freeze record from `84c61334` (product `e4e97758`, `aa745132…`). Only the in-place update of `candidate_divergence.json` was disclosed. | **Disclosed here.** The branch is unpublished, git history keeps `84c61334`, and `tiers.json` `order_note` describes the re-freeze. The `84c61334` record is superseded because its product was changed by `61ade29e`. |
| F3 | NOTE | `full-t3.json` says T3 attempt 1 had "no exit code", but the local `full-t3.exit` says `exit=1`. The `test_R1_B…[registry_v2_sha256]` failure shows `REGISTRY_V2_NOT_COMMITTED` without WinError 1455 text, so its attribution to the paging-file error is inferred. `test_G4` does show 1455. | **Corrected here.** Attempt 1 exited 1 and is invalid either way. Only attempt 2 (exit 0, clean) is counted. |
| F4 | NOTE | No committed Wave 3 receipt sits at the final product `61ade29e`. `regression-green3.json` was measured with the product uncommitted; the clean re-run at `e4e97758` predates `61ade29e`. | **Closed by this review.** A clean re-run at `738ac241` (`final-review/regression-rev.json`, `final-review/wave3-rev.json`) reproduces the result case for case. |
| F5 | NOTE | Wording drift. The `candidate_divergence.json` `reason` says the "why" is attached in `scene3d.py`; since `61ade29e`, the exact check lives in `simulation_state.py` and `scene3d.py` only carries it. `main.py` has no comment for 130→131 the way some earlier bumps did; the rationale is in `test_api.py`, `CURRENT_STATE` and `test_cache_section_justification_invalidation.py`. | **Corrected here.** The divergence JSON is not rewritten. |
| F6 | NOTE | While the tool menu is open, ←/→ step the scene. Home/End are safe because the menu calls `preventDefault`. | Accepted. Recorded as a UX limitation in `handoff.md`. |
| F7 | NOTE | Some textbook phrasings written by the reviewer that agree with their payload are still refused: mid-sentence "trong không gian,", an unlabelled "với đáy là …", and the cube with "thỏa mãn mặt đáy". | Accepted. This is a coverage limit; the gate fails closed. |

## What held

| area | result |
|---|---|
| Architecture | The product diff is limited to the SG-3 grammar plus `_vai_doan_ok`, `simulation_state._canh_song_song_thiet_dien`, `scene3d._ly_do_canh_thiet_dien`, `CACHE_VERSION`, and three frontend files with regenerated samples. `scene3d.py` imports are unchanged. There is no new planner, engine, renderer or timeline. Keys use the same `setStep` path as the buttons. The 2D controls are not mounted on the 3D canvas, so keys are not handled twice. |
| Source grounding | 51 new adversarial probes, run differentially against base. Every negative is refused on W4. Three probes are newly served (B6, D4, E4); each is consistent with its text and equal to its canonical answer. The pre-existing N1 (B2 "cạnh bên DF") is now refused. Positive controls are served. |
| Exact "why" | Independent determinant/minor checker over the dev scene, samples, served fixtures, and 63 live-served scenes (226 edges, 210 whys): 0 bad. No justification is placed on a non-EXTEND event. A planted false claim is caught. The pedagogy metrics re-run is identical to the committed file. |
| Coverage | Wave 3 67/72 served-correct, 72/72 negatives, 62/72 reasons, 0 wrong-served, 17 transitions. Locked 96/96. 203 probes: 0 served negatives, 0 internal errors. All 144 case rows match `wave3-green3.json`. Historical run directories are untouched. |
| Candidate identity | `--verify` exits 0 at `738ac241` and at T3 `25028584` (118 files, `54b5b565…`). Only tests and docs changed after `61ade29e`. The divergence chain is consistent. Every T0, T1, T2 and T3 receipt hash matches its local log. |
| Pedagogy / frontend | Geometry vitest plus the preview contract: 920 passed. Targeted backend: 132 passed. The rubric is honestly labelled as proxy evidence. |
| Publication | Range `e5dc3d28..HEAD`: exactly one violation, blob `24d45cd6`, `PENDING_OWNER_DECISION`, verdict BLOCKED. Its key line is byte-identical to main `0f726dfb`:395. Head scan: W4 has 104 violations, all pending, 0 unexcepted; pre-W4 main has 105, including 1 unexcepted. There are 0 `Co-Authored-By` trailers. |
