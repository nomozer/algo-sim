# Independent pre-freeze review — READY for this gate (0 BLOCKER, 0 MAJOR, 3 MINOR, 5 NOTE)

A fresh-context subagent of this session reviewed research HEAD `e18bccc4` (product `6a09c06a`) against `main`
`996f114b`, pre-CIC `5e44d5da` and the start head `df475f06`, which it reproduced in memory by reverting the two
product hunks. It was read-only on the repository, made 0 provider calls (sockets blocked), and wrote its own probes
outside the tree. Its scripts and raw outputs are copied verbatim into `pre-freeze-review/`; the SHA-256 list is in
`pre-freeze-review-files.sha256`. The harness blocked the reviewer from writing a report file, so its findings are
transcribed here. R1 and R2 were re-checked against `pre-freeze-review/survivors.txt`.

**READY applies only to this review gate.** Overall status stays `NOT_READY`: publication is
`BLOCKED_PENDING_OWNER_DECISION` and F7 is unresolved. There is no replay, T0/T1/T2, freeze or Full T3.

| id | sev | finding | evidence |
|---|---|---|---|
| R1 | MINOR | **The check order "known namespace / ownership before repeated identity" is not covered by any test.** Mutant `M_identity_before_scope` survives both new suites. It changes the mandated code on every surface: `{"segment":["ghost::A","A"]}` gives `UNKNOWN_SOLID_ID` on HEAD and `INVALID_MATH_GOAL` under the mutant. `["pr::B","B"]` with goal `solid_id: other` gives `SOURCE_OBJECT_MISMATCH` on HEAD and `INVALID_MATH_GOAL` under the mutant. Both fail closed. | `survivors.txt`, `mut-M_identity_before_scope.log` |
| R2 | MINOR | **The derived-parent mapping in `canonical_vertex_ref` is not covered by any test.** Mutants `M_no_derived_parent_ns` and `M_no_derived_parent_scope` survive. Every frozen derived-solid case has a single root solid, so the label fallback hides the difference. With a second root solid, the code changes between `INVALID_MATH_GOAL` and `AMBIGUOUS_REFERENCE`. All outcomes fail closed. | `survivors.txt`, `mut-M_no_derived_parent_*.log` |
| R3 | MINOR | **The label fallback ignores constructed points.** In the shared-base fixture, `["D","pyr2::D"]` is refused as `INVALID_MATH_GOAL`, but the reference is genuinely ambiguous (`main` a3 returns `AMBIGUOUS_REFERENCE`). A constructed `D1` that collides with a bound `D1` gives `INVALID_MATH_GOAL`, where `main` gave `INCONSISTENT_FACTS`. Only the refusal code differs and nothing is served. This is narrower than the contract §5 wording for ambiguous references. | `table.txt` `F2.pyr.D_unscoped_vs_pyr2D`, `F2.cb.*`; `diff.txt` |
| R4 | NOTE | The schema raises `AMBIGUOUS_REFERENCE` only for list operands. An ambiguous `point` operand passes the schema and is then refused `AMBIGUOUS_REFERENCE` on every route. | `table.txt` |
| R5 | NOTE | The `EVIDENCE_INDEX` classification and `technical-checks.md` still said "clean compatibility/review pending" after Gate D. The index line is updated in this commit. `technical-checks.md` is a dated checkpoint and is left unchanged; `gate-d.json` and `run.json` carry the later state. | — |
| R6 | NOTE | `baseline_11` comes from a targeted run of only those 11 tests at `5e44d5da`, not a full baseline. The log hashes and the failure lists match, so "baseline-matched" means exactly that. | worktree-local logs |
| R7 | NOTE | Two distinct identities that sit at the same point (pyr1 midpoint D vs pyr2 apex D) are served as 0, the same as on `main`. That is correct math: §5 defines identity by symbol, not by coordinates. With DA = 3a the same pair gives `2a`. | `extra-head.txt` |
| R8 | NOTE | Pre-existing: a non-injective `vertex_bindings` is not refused at the schema. A scoped `["A","B"]` is now `INVALID_MATH_GOAL` where a3 gave `INVALID_VERTEX_BINDING`. Fails closed. | `table.txt` `F2.noninj.*` |

What held:
- **F1 grammar is closed exactly.** All 49,146 key subsets × goal types were checked against an expected table built from the Owner decision, not from runtime constants: 0 mismatches (`exhaustive_f1.json`).
- **122 new probes × 3 trees × 5 surfaces (schema /1, schema /2, a3, pl, a4):**
  - No unregistered shape is served on HEAD.
  - No refused output carries a scene or answers, and no probe raised an exception.
  - No registered control is newly refused.
  - The only newly served shape is curved `volume {solid_id}`, which is registered, disclosed and from `4b361c47`.
- **Corpus sweep, 1,999 committed payloads, isolated against `df475f06`.** Newly refused outside the run's own cases: earlier adversarial probes, the disclosed `C.volume.solid_and_solid_id`, and 2 payloads that also contain an unregistered goal. No registered positive is newly refused.
- **Duplicate aliases that `main` served as 0 are now `INVALID_MATH_GOAL` on all routes.** This covers:
  - whitespace and Unicode-space variants;
  - shared-base `pyr1::A` vs `pyr2::A`;
  - bound aliases in segment, line, plane and polygon;
  - derived-parent aliases;
  - cylinder centre and cone apex aliases.
- **Semantic checks run before capability checks.** Every F1/F2 negative gets its semantic code on pl and a4, never a `BRIDGE_UNSUPPORTED_*` code.
- **Mutants were killed by behaviour.** Failing tests per mutant: raw-label 8, segment-only 26, no-ambiguity 1, unscoped-only 20, F1 superset 191, F1 `solid_id` alias 82. The only survivors are R1 and R2.
- **F7 is neither worse nor hidden.** `prism-f7-head.json` equals `prism-f7-main.json` apart from the head hash.
- **Scope and immutability:**
  - Only `typed_fact_next.py` changed in product code.
  - The six locked V2 files are unchanged against both `df475f06` and `main`.
  - `CACHE_VERSION` is 130.
  - No historical evidence file was modified, deleted or renamed.
- **Reviewer re-runs:** locked V2 232/232; supplementary suites 2,442 passed and 6 skipped.
- **Gate D receipts are honest.** The raw-log hash and the 11-node list match, and no receipt claims an overall PASS or zero internal errors globally.
