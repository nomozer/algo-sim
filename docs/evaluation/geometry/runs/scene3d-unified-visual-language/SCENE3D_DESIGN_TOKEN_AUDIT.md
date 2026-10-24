# Scene3D design token audit

Source: actual root `DESIGN.md` (Notion Analysis, alpha) at verified campaign `f95596716912e5550ed079287221274b2d70f24c`, `docs/DESIGN_BRIEF.md` §§3.5/5, actual `frontend/src/styles/tokens.css`. Original DESIGN.md is preserved. It defines UI color/type/spacing, not WebGL materials, section alpha or geometric roles. Its sticker colors may encode simulation states per tokens.css, but are not an instruction to paint every surface with UI primary blue.

| Source token | UI meaning | Geometry meaning | Existing usage | Proposed mapping | Evidence | Decision |
|---|---|---|---|---|---|---|
| canvas / canvas-soft #ffffff / #f6f5f4 | white surface / warm paper | quiet stage | transparent WebGL above CSS | preserve stage | DESIGN colors; global.css | retain UI |
| primary #0075de; primary-active #005bab | action / focus / pressed | selected and newly constructed emphasis | causal blue #2563eb in roles.ts and CSS | primary for focus; width/marker/selected text as second channel | DESIGN; role tests | synchronize shared causal blue |
| secondary #213183 | inverted hero | no direct material equivalent | not geometric role | no automatic mapping to second solid | DESIGN overview | intentionally unused in scene |
| ink-secondary #31302e | secondary text | visible structural edge, given point | slate #1e293b / #374151 | warm charcoal | DESIGN text; scene3d-view MAU | shared structural ink |
| ink-muted #615d59; ink-quiet #716d69 | subdued readable text (quiet is existing accessibility extension) | hidden structural edge | same slate as visible, alpha .9 | quiet ink + lower alpha + dash, independent of selection | tokens.css accessibility rationale | geometry extension, not faint text |
| ink-faint #a39e98; hairline #e6e6e6 | graphic marks / chrome border | optional grid only | separate slate grid literals | faint grid; never object-label text | tokens.css; DESIGN_BRIEF §5 | do not use hairline for key edges |
| accent-sky #62aef0 | sticker | primary solid shell and given base | slate #647a96; amber polygon base | restrained translucent sky, shared polyhedral/curved policy | DESIGN accent; renderer inventory | Scene3D semantic extension |
| accent-teal #2a9d99 | sticker | secondary solid shell / auxiliary line | override #0d9488 and #0f766e | teal shell; teal-deep extension for readable auxiliary ink | DESIGN accent; inventory | stable roles from full scene, not visible index |
| accent-purple #d6b6f6; purple-deep #391c57 | sticker fill / deep accent | constructed plane / derived point | saturated #7c3aed plane / red #dc2626 point | light plane + deep outline; deep point | DESIGN accents | typed semantic roles |
| accent-orange #dd5b00 | sticker, processing | section outline | amber #f59e0b used for outline and fill and face | source orange outline; light amber #ffc857 fill extension | DESIGN accents; material inventory | separate fill/outline; unlit region |
| light amber #ffc857 (NEW EXTENSION) | none | section fill in every shape | polygon .45 vs circle/ellipse .28, lit | common .38 fill / .48 focus; unlit, single-pass | readability/alpha rationale below | proposed Scene3D extension, not claimed in DESIGN |
| orange-deep / intermediate orange | existing causal numerical roles | numeric given / intermediate | #c2410c / #fb923c | retain existing W12 numerical distinction | scene3d-roles.ts; role tests | existing extension retained |
| green / orange / error | status UI | not point/section correctness | no dedicated success/error in DESIGN | no inferred geometric correctness colors | DESIGN Semantic paragraph | preserve existing refusal UI |
| no source token | hover | no WebGL hover recolor exists | pointer cursor and UI hover | keep existing affordance; selected uses focus | view raycast handlers; CSS | no new interaction feature |
| no source token | disabled/hidden/faded | hidden omitted; unrelated causal objects faded | lamDiu .3; auxiliary .45 | centralize same factors; do not equate hidden with low alpha | interaction-state.isVisible; lamDiu | preserve semantics |

Alpha is per role, not a global reduction: shell remains lit for normals/depth cues; flat section/base/plane is unlit to keep semantic colors independent of lights. Flat DoubleSide sheets force one pass; shells keep their existing two-sided rendering and depth prepasses. Two independent layers at alpha a compose to 1-(1-a)^2; this is not corrected by choosing a darker palette. Section depthTest remains !xray, depthWrite false, render order 7, boundary at 8/10. CSS custom properties never enter Three.Color: numeric sRGB hex uses installed Three.js Color.setHex conversion into linear working space. Output renderer remains sRGB default; browser receipt records actual settings.

All source UI variables above exist in tokens.css. Existing role CSS copies are locked by role tests. Full unresolved-var scan and computed browser values are recorded by validation, not presumed from this table.
