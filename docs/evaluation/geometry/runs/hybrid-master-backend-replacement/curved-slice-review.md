# Independent review of the curved slice on /4: `INDEPENDENT_CURVED_SLICE_REVIEW_READY` (round 3)

- **Reviewer:** a fresh-context subagent.
- **Conditions:** read-only; 0 provider calls; targeted test files only.
- **Probes:** they stayed in the session scratch directory, `curved-review/probe1–5.py`, 97 cases in all.

| round | commit | verdict | findings | fix |
|---|---|---|---|---|
| 1 | `e58d319a` | NOT_READY | **B1:** the centre/top/rim roles were not grounded; a rim on the other base gave 100π instead of 36π. **B2:** a value was read without its clause ending ("3 lần chiều cao"). **B3:** a height or radius belonging to another object was accepted. **M1:** the certificate's claim was too broad. | `38e1a0bf`: role binding, notation check, height span tied to the solid's quote, M1 wording corrected. 11 reproductions locked. |
| 2 | `38e1a0bf` | NOT_READY | The noun blacklist was incomplete and still served wrong values: a second cone, a section circle, a sector, an object before the kind word, an unread qualifier, an unwritten "(N)". | `face0fc1`: the whole quote must parse in a **closed clause grammar**, an allowlist. 6 more reproductions locked. Two over-refusals fixed. |
| 3 | `face0fc1` | **READY** | 0 BLOCKER, 0 MAJOR. **All 19 earlier false serves are refused.** Every served value matches a hand oracle, including 3√2/2 → 9π√2, (T) total area 20π, and cone a → πa³√3/3. | Minor: "bán kính bằng 0" was reported as `UNGROUNDED_VALUE`. It now keeps `NON_POSITIVE_LENGTH` (test added). |

## Accepted minors (safe, typed refusals)

- **Over-refusals:** decimals ("2,5"); "bán kính đáy bằng 3 cm"; "… và có đáy là đường tròn tâm O"; a cylinder rim written without "tâm X"; a top label absent from the text.
- **Label/symbol collision:** a point named R together with "R = 3". The intended reading is served.

## Verified as unchanged

- Polyhedral grounding: every curved change is gated on `curved_solid`.
- Route A's provider surface.
- LLM_ONLY: `pipeline.py`, skills, contract and grammar card are untouched; `CACHE_VERSION` is 131.
- The Owner-registered curved controls.
- Kind dispatch happens only in `geometry/curved.py`.
- The held-out authoring rules do not favour Hybrid.
