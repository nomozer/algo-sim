# Preregistration — N1–N7

Locked before product edits on HEAD 5e44d5da. Development security regression, not a blind holdout. Offline only.
Baseline: preserve baseline-head.json (203 reviewer probes: 147 NEG, 56 POS; 34 served-negative probes, no internal results).
Local-main exploratory comparison already run: all 34 also served on main; N7 is a regression (main SERVED, HEAD UNKNOWN_SOLID_ID).
No rerun/re-authoring of the historical Wave 3 corpus/oracle or locked 96 development expectations.

## Outcomes locked here and in test_closed_input_contract.py

N1: malformed sequence/string/point shapes -> INVALID_MATH_GOAL across routes. Valid list+all scope aliases retain exact outcomes.
N2: unqualified or qualified constructed foreign M and foreign containment -> SOURCE_OBJECT_MISMATCH before capability fallback.
Valid A3-DEV-02 non-identity bindings retain exact oracle; semantic refusal never invokes legacy compilation.
N3: each model/kind rejects every explicitly supplied field outside its snapshot allowlist -> INVALID_MATH_GOAL / INVALID_SIMULATION_GOAL / INVALID_RELATION_SPEC.
Absent optional fields remain valid; inapplicable null/empty is explicit and invalid. Every allowed field gets a shape/ownership positive and applicable negative.
N4: curved unknown qualified labels -> UNKNOWN_VERTEX_REF; foreign ownership -> SOURCE_OBJECT_MISMATCH;
unsupported curved relations -> BRIDGE_UNSUPPORTED_RELATION, absent quote -> SOURCE_QUOTE_NOT_FOUND, contradictory identity -> SHARED_ENTITY_MISMATCH.
Curved base fixtures remain SERVED with their exact oracle. No new curved computation.
N5: unknown/inapplicable target keys -> INVALID_MATH_GOAL; solid_b/solids may not be ignored.
N6: census includes indirect partial/helper/key-set reads (plane1/plane2); schema/registry/consumer/route/test coverage gaps fail the gate.
N7: declared derived-solid highlight M -> SERVED with unchanged exact answers; ghost/unrelated scope -> typed refusal; hyphen renaming invariant.

All 147 NEG reviewer seeds must refuse with a typed non-internal code. POS controls retain baseline capability/source outcomes or improve N7;
no previously served valid control may be lost without Owner adjudication. New fixtures cover null/empty presence, malformed operands,
every kind-field combination, nested aliases, constructed qualified identity and curved/derived positives.

Required mutants: remove operand guard; iterate strings; remove per-kind allowlist; open target keys; bypass S8;
semantic fallback; bypass curved existence; bypass curved relation validation; bypass derived resolution. Each must kill an oracle.
Metamorphic: consistent hyphen renames preserve exact answers; foreign owner/unknown field/string replacement refuse.

Acceptance: GREEN + mutations + Gates A–D incl. locked 96/96, exact geometry/legacy/41 fixtures/cache/publication;
independent pre-freeze review before replay/T0/T1/T2/freeze/Full T3. Review BLOCKER/MAJOR or Gate A FAIL -> NOT_READY checkpoint, stop.
Freeze-dependent identity checks remain PENDING_NEW_FREEZE until a new candidate is frozen; no old Full T3 receipt reuse.
