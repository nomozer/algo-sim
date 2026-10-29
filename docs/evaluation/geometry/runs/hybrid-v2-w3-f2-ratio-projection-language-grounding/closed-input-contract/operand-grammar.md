# Operand grammar

Canonical point = one LABEL or sid::LABEL parsed by parse_qualified_ref. A point never accepts a list/object.
segment/line/line1/line2 = JSON list of exactly two distinct references; plane/plane1/plane2/polygon = list of at least three distinct references.
Python tuples produced/accepted by internal schema adapters share the same sequence grammar; strings are never sequences of refs.
No per-character parsing. Containment vertex chains retain their separate, explicit split_vertex_chain grammar.
Solid names are resolved uniquely by declared id/local notation/canonical notation; section/solid ids must be strings.
The snapshot records allowed target alternatives and scope keys. Scope keys may accompany geometric operands only as validated ownership assertions.
Malformed shapes/unknown keys/inapplicable target alternatives: INVALID_MATH_GOAL, never an internal error.
