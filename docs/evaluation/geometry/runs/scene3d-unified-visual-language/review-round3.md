# Independent review round 3

Reviewer: separate read-only agent (no edits, no subagents). Scope: measurement changes after round 2 (harness override fix, runtime probe, validator), receipts A-complete/B-complete/C-complete/final at product `36dfccef9bb3f5bff3e802aece7083a0e747df72`, survey-validity register. Committed product bytes equal round-2 bytes modulo CRLF→LF (`core.autocrlf=true`; working-copy sha256 view `9889e39b…`, roles `cedde764…`).

Verdict: no Critical; two Important; four Minor.

1. Important (I1): baseline `tokens.css` substitution was a no-op — `global.css` pulls it via CSS `@import`, which Vite inlines without plugin `transform`; built CSS of baseline-complete carried `#0075de`, not `#2563eb`, while the receipt listed the substitution. Likely zero pixel impact (tree item / legend swatch closed in captured states), but a false provenance claim.
2. Important (I2): `public-non-thiet-dien-truc` axial section `td` is a `polygon3` with no `surface_role`/`formation_roles` (pre-metadata public sample). Final rendered it as plane lilac `d6b6f6`/0.055 while the same construction tagged `AUXILIARY_SURFACE` (family09/10) renders section amber `ffc857`/0.38. Metadata-driven, not hardcoded, but a cross-scene inconsistency hidden because validate.py used the same classification.
3. Minor: survey-validity stale (pending arms already existed; `enforce:'pre'` already in b53ff305; old fixture has 33 rows; `focused/` unlisted). AUXILIARY_SURFACE fills excluded from material check. Shell check was set-membership only. Reset-tolerance amendment disclosed only in code.

Confirmed by reviewer: override effective at runtime (pre-TS, single module, count = 1, live constant equals proposal; A `122d5360`, C `fe7267d0`, B = final `91d9a368` on compact proposals JSON); arms comparable (same harness/fixture/source/checkout, camera identity vs baseline at absolute 1e-9); material checks non-vacuous (37 shell, 11 section observations/arm); reset deltas are float jitter (~4e-10 relative, no camera code in diff); curved repeat-pixel nondeterminism pre-exists; depth/X-ray probes, panel overlap, role stability and warm-orbit reuse pass.

Dispositions:
- I1: harness substitutes baseline tokens at the `global.css` importer, requires every baseline substitution exactly once and the built CSS to carry each changed custom property (whitespace-normalized). New arm `before/`; first attempt failed closed on a CRLF/LF comparison artefact and wrote no receipt.
- I2: product fix `24e1a9dbe24a5abf965ae268ce89097b67060a53` — `vaiTroMien` resolves every non-base `polygon3` to section like `circle3`/`ellipse3`; RED (lilac 0.055) then GREEN test in `scene3d-unified-materials.test.ts`.
- Minor: register rewritten; `is_section` covers AUXILIARY_SURFACE and metadata-free polygons; shells checked against independently derived primary/secondary roles; amendments go to the report.
- Product changed ⇒ all arms re-measured at `24e1a9db` (before, survey-A/B/C, final-v2/v3) and round 4 required.

Declined: aesthetics, readability, human approval, T3/freeze, merge readiness. No merge authorization.
