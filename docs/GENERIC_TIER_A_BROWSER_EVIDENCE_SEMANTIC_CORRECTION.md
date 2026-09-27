# Generic Tier-A browser evidence semantic correction

**Wave:** `GENERIC_TIER_A_BROWSER_EVIDENCE_SEMANTIC_CORRECTION`

**Date:** 2026-09-27

**Corrects:** `CLOSE_GENERIC_TIER_A_BROWSER_EVIDENCE_BEFORE_CUBOID_MERGE`

**Final decision:** `PRODUCT_REGRESSION_FOUND`

## Correction

The earlier closure report cannot support its merge-ready conclusion. Its browser runner did not assert raw-token leakage, uncaught exceptions, unexpected unbounded objects, answer absence on refusal, or negative behavior at the mobile viewport. Those required fields are absent from the committed `BROWSER_EVIDENCE.json` rather than passing with a measured zero.

The missing raw-token check masks a product-visible regression in all four audited families. The frozen positive Scene3D events contain learner narration with internal underscore identifiers:

| Family | Leaking steps | Examples | Verdict |
|---|---:|---|---|
| Triangular pyramid | 3 | `dien_tich_day_ABC`, `the_tich_khoi_chop`, `the_tich_khoi` | FAIL |
| Triangular prism | 3 | `S_ABC`, `the_tich_lang_tru` | FAIL |
| Rectangular pyramid | 2 | `S_ABCD` | FAIL |
| Cross-section | 4 | `alpha_plane`, `the_volume_sabcd`, `area_T`, `dist_S_BD` | FAIL |

This is browser-visible, not merely transport metadata. The backend assignment fallback interpolates `stmt.target_var` into the event explanation; `narrationAt` returns that explanation unchanged; `Scene3DExplorer` renders it directly in `.geo3d-buoc-loi`.

## Machine evidence

- Artifact: `docs/evaluation/geometry/generic-tier-a-browser-semantic-correction-20260927/RAW_TOKEN_AUDIT.json`
- Artifact SHA-256: `3e9e18cb890dce272788bfc077b19010c3c689e68ed63562a214c2b3cb693b6b`
- Audited head: `26479cc724b15af43c0488864a851117f91724cc`
- Corrected evidence commit: `7cee042c9a539f89970722ac56eb9f490d5e753b`
- Product commit remains: `2822beb389f8bdb253f26b8c6d6db1860d184cc6`
- Product tree remains: `72516eb576a173a0b987beff684e4e2c6a9669e5ea370828bbd9245447eb369b`
- Application LLM calls: `0`

## Root cause and stop condition

Root cause is the absence of a mandatory learner-surface translation at the event narration boundary. Some compiler paths already emit display formulas, but the generic interpreter fallback uses the stable target identifier, and the frontend intentionally renders the event explanation as authoritative text without sanitization.

No product code, candidate identity, cache version, prompt, schema, or historical artifact was changed by this correction. Per the task stop condition, product repair and evidence recapture are deferred until the root cause is reviewed. The prior `MERGE_READY` classification is superseded; the Cuboid merge is not ready on this evidence.
