# Preregistration — F1/F2 continuation

Locked before product edits at df475f06. Development security regression, not a blind holdout; 0 provider calls.
Registration.json fixes all six measurement kinds and every registered alternative independently of runtime tables.
Cases.json includes all 442 unregistered shapes from prior reviewer probes, registered route controls and explicit identity negatives/positives.
F1: unregistered key sets -> INVALID_MATH_GOAL at child schema and both versions before any route. No radius/area/lateral_area solid_id alias; no redundant solid+solid_id.
F2: repeated resolved identity in each segment/line/plane/polygon -> INVALID_MATH_GOAL. Same unqualified/qualified, reversed, bound root aliases, prime, hyphen, constructed and derived identities included. Unknown namespace -> UNKNOWN_SOLID_ID; malformed/Unicode prime operands -> existing INVALID_MATH_GOAL (no new alias); ambiguous root binding -> AMBIGUOUS_REFERENCE.
Positive identities retain schema acceptance. Registered controls retain exact RED route outcomes; volume solid_id stays registered even where historical route support differed. No locked V2 code changes.
Supplementary mixed solid+solid_id tests previously expecting SOURCE_OBJECT_MISMATCH will now require INVALID_MATH_GOAL because their shape is unregistered, including different solid ids. Prior evidence remains unchanged.
Mutation oracles must pass on real code and fail by behavioral assertion on each mutant, separately at child/payload schema, ownership preflight and route ordering. Source inspection only applies the fault, never determines killed status.
F6: independently check all refused outputs for absence of scene/answers; restore removed assertion.
F7 prism radius/lateral_area internal errors, if reproduced on all checkpoints, remain unresolved explicit limitations outside geometry scope; no global zero-internal/PASS claim.
Four source grammar diagnostics remain PENDING_SOURCE_GRAMMAR_SUPPORT. Publication remains BLOCKED_PENDING_OWNER_DECISION. No Wave3 replay/freeze/T3 while blocked.
