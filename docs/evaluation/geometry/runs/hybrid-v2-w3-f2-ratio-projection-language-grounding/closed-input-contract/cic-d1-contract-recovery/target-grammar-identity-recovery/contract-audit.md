# Read-only contract audit

Three full-SHA observations are in observed-red/main/pre.json and their SHA-256 in red.json. 656 identical authored inputs ran on all three checkpoints before product edits. Source hashes are also recorded there. Current `_validate_goal_target` adds both scope keys to its union, then scope-only membership accepts any nonempty subset of them when any registered scope alternative exists. That admits 43 unexpected target shapes at the current payload boundary.

| kind | exact registered key alternatives |
|---|---|
| distance | segment; point+plane; point+line; line1+line2; line+plane; plane1+plane2 |
| angle | line+plane; line1+line2; plane1+plane2 |
| volume | solid; solid_id |
| radius | solid; section_id |
| lateral_area | solid |
| area | polygon; section_id; solid |

All other key combinations, including solid+solid_id and section+solid, are invalid. Ownership for geometric operands belongs at goal.solid_id, not beside the operand.

Volume solid_id is schema-valid on main 996f114b and pre-CIC 5e44d5da as well as research HEAD. Their curved Adapter /3 refuses INVALID_MATH_GOAL_TARGET; HEAD serves exact volume (all cylinder/cone/sphere controls). This existing route delta came from adapter3 measurement_scope use in 4b361c47, not a new grammar alternative. Owner Decision A preserves registration and current valid behavior: retain it and explicitly disclose; this continuation adds no capability and no adapter edit.

Current raw-string distinctness misses 21 identity negatives; /1 can serve 0 through fallback while /2 refuses later. Existing canonical_vertex/parse_qualified_ref define root identity. Different solid bindings stay distinct; identical root symbols intentionally share identity under existing contract. Constructed/derived membership is still proven by S8 before any capability/fallback; schema must not invent ownership or coordinates.

The locked target test at 82097186 was read with git show. Current test file equals main; earlier multi-label-plane capability evolution differs from 82097186 and is preserved, with its existing engine refusal test. This continuation does not alter this file or any locked expected code.

F7 independently reproduces on main, pre-CIC and HEAD: valid prism radius/lateral_area solid and notation forms reach ADAPTER_INTERNAL_ERROR (KeyError ask2). Unsupported geometry capability remains an unresolved pre-existing safety limitation; do not call global no-internal or Gate A across all known inputs PASS.

F6 git diff 11816921^..11816921 confirms removed no-scene/no-answers assertion. pyr::M became a supported constructed identity; replacing it with undeclared pyr::Z was appropriate. Restore assertion on every refusal, with the existing positive constructed-point test retained.
