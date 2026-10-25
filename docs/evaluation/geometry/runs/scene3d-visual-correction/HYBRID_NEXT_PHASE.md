# Hybrid — what is still missing to replace `LLM_ONLY`

**Hybrid production: NO-GO.** Nothing in this campaign changes that. The default stays `LLM_ONLY` with
`RESPONSE_CONTRACT=flat`, `ALLOW_LIVE_AI=0`, 0 model calls, and `CACHE_VERSION` 129 (verified in `backend/app/main.py`;
not bumped, because the change is UI-only). The 27 publication exceptions are not approved.

## 1. What this campaign did and did not touch

- **Frontend presentation only.** The product commits touch `frontend/src` only. `backend/app` is unchanged, so the
  measured system hash stays `ee474c81…`, and geometry, provenance, registry, planner, engine and Adapter /4 are
  byte-identical.
- **R0 kept.** The renderer computes no geometry fact, coordinate, name or answer, and the scene JSON is unchanged by
  building, selecting or rotating (`geometry_unchanged` 52/52 in the browser). The cap-rim dedupe compares backend
  numbers that already exist. It infers nothing.
- **Rendering is not support.** Drawing a cylinder, cone or sphere correctly does not make that family supported by
  route D. The 18-family capability matrix is unchanged: **0 FULL_E2E_VERIFIED, 9 PARTIAL, 7 RENDER_ONLY,
  2 UNSUPPORTED** (`../visual-b3-sphere-integration/UPDATED_18_FAMILY_CAPABILITY_MATRIX.md`).

## 2. Route D gates (`docs/MIGRATION_CHECKLIST.md` §2; read there, not copied as live state)

| Gate | Status there | Still needed |
|---|---|---|
| D-01 default route untouched | PROVED | Declare the wiring gate when route D is connected |
| D-02 cache identity per route | PARTIAL | A route-D cache only once it is served through `/api/analyze` |
| D-03 per-request config | PROVED | — |
| D-04 extraction contract | flat = product, v3 NO-GO | A **new pre-registered held-out set** before any surface change |
| D-05 correct mathematics | PROVED on the current corpus | Independent expectations for every new family |
| D-06 fail-closed | PROVED | — |
| D-07 adapter envelope | PROVED for preview | The frontend reads `route_d`; never shown as "proven" |
| D-08 API behind a flag | PROVED for preview | Owner approval to serve route D via `/api/analyze` or a real provider |
| D-09 observability | PROVED | — |
| D-10 presentation only from certificates | **OPEN** | Right-angle marks by segment name, `maTranKhung` self-defence, `length_unit`, goal observations, `verification_gap` (`HYBRID_PREVIEW_FRONTEND_CONTRACT.md` §9). The blocker "the Scene3D branch owns the renderer" can be lifted once this branch is decided |
| D-11 paired live measurement vs `LLM_ONLY` | NOT_STARTED | Owner GO, budget + stop rule, `MEASUREMENT_CLASS`, `HELD_OUT_CLAIM`, `EVALUATOR_INDEPENDENCE` |
| D-12 rollback | PARTIAL | Depends on D-02 |
| D-13 enablement decision | NO-GO | All of the above plus the Owner's decision |

## 3. Recommended order after this visual work

1. **Owner decisions on this branch** (`FINAL_OWNER_HANDOFF.md`):
   - F2 hue gate;
   - curved-occlusion convention;
   - human visual approval.
2. **D-10 on the decided renderer.** Present only certified facts: route-D right-angle marks, units, `verification_gap`.
   This is the part of Hybrid that depends on Scene3D.
3. **D-04.** A new pre-registered held-out extraction set. Without it, nothing can be claimed about extraction quality.
4. **Family coverage.** Move PARTIAL families to FULL_E2E one at a time, each through facts → source gate → planner →
   exact engine → Adapter /4 → browser, with independent expectations.
5. **D-08 / D-02 / D-12, then D-11.** Serve behind the flag through `/api/analyze`, isolate the cache, prove rollback,
   then run the paired live measurement against `LLM_ONLY`. Every live step needs an explicit Owner GO.
6. **D-13.** The Owner's decision.
