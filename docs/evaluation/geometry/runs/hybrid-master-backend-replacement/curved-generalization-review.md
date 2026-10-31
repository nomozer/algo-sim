# Independent adversarial review: seventh continuation (c3bc1f67..d9d11b60)

The review covers the base-centre grammar, the general apex ratio k, sphere sections, the multi-section refusal, the
`CURVED_WORDING_UNSUPPORTED` reclassification, and the registered-control transition layers.

**Reviewer.** An independent subagent that did not write the code. It ran offline, made 0 provider calls and edited no
tracked files. Its scratch scripts stay outside the repository.

## Verdicts

| Round | Commit reviewed | BLOCKER | MAJOR | Verdict |
|---|---|---|---|---|
| 1 | 6e0a6c2c | 0 | 5 (M1–M5) | NOT_READY |
| 2 | 8b057c0a | 0 | 2 (R2-M1, R2-M2) | NOT_READY |
| 3 | d9d11b60 | 0 | 0 | **READY** |

The findings and their fixes are listed in `registered-curved-controls-audit.md`, in the sections "Independent review
round 1" and "round 2". Every finding has a reproducer locked in `backend/tests/geometry/test_route_d_curved_grammar.py`
(`REVIEW_1`) with its exact refusal code.

## Final-pass evidence from round 3

- **Earlier attacks re-run.** The reviewer re-ran every earlier attack (about 110 payloads) and all four probes. There was
  no WRONG_SERVED, no REFUSED_OTHER_CODE and no exception.
- **Served answers checked by hand.** All 27 SERVED outcomes were checked by hand. Examples:
  - MS/SO = 1/3 ⇒ π;
  - OM/SO = 1/4 ⇒ 81π/16;
  - "tỉ lệ 1/3 tính từ O" ⇒ 4π;
  - a sphere with d = 3/2 and R = 5 ⇒ 91π/4.
- **Openers cannot overlap.** No quote can parse as both a solid sentence and a section sentence, because their opening
  words are disjoint.
- **Source text in the binder.** `_DE_NGUON` is set and reset together with `_GOI_NGUON`. Outside the gate, both are empty
  and a section question binds nothing, so it refuses.

## Open minors (not blocking; recorded)

- **Point named like the plane.** A point named like the plane ("tại P" with plane (P)) is served. The value is correct;
  the point label and the plane name are separate namespaces.
- **"tỉ lệ k tính từ đỉnh S".** It is read as SM/SO, and "tỉ số" is refused as ambiguous. This waits on Owner ruling P-3.
- **Rim on the upper base of a cylinder.** A true rim-on-upper-base statement is refused as `SOURCE_OBJECT_MISMATCH` and
  not as a capability gap. This behaviour predates the continuation.
- **No Full T3 claim yet.** The candidate must be re-frozen before a Full T3 pass is claimed.

## Regression replay at d9d11b60 (`inventory-phase-k.json`, `wave3-phase-k.json`)

| Set | Result |
|---|---|
| Wave 3 | 67/72 positives served correctly; 72/72 negatives refused (62 with the correct reason); 0 wrong-served; 0 transitions |
| Locked 96 | 96/96, 0 transitions |
| 203 probes | 0 wrong-served, 0 new failures. The 12 curved probes move only REFUSED → REFUSED, as recorded in the audit. |
| Full backend suite | 16129 passed; 11 failed. All 11 are candidate-identity pins that only the re-freeze clears; 0 other failures |
