# Learner diagnostics (P3)

Product commit `0645de46`, frontend only.

## Before

`UnsupportedNotice` (`frontend/src/components/SimulationWorkspace.tsx`) rendered a collapsed `<details><summary>Chi tiết chẩn đoán</summary>` panel on geometric refusals. Inside it:
- the technical code `reason_code ?? error_code` (e.g. `CURVED_PLANE_DOES_NOT_CUT`);
- the raw `reason`.

The drawer came from `7ce563b3` (2026-10-22), in the Visual branch's ancestry. That commit also loosened two tests so they stripped `<details>` before asserting. The owner's uncommitted root work contains the same drawer; it was not touched.

## After

The drawer is removed. The learner keeps:
- the semantic title (`GEOMETRY_REFUSAL_TEXT`, e.g. "KHÔNG CÓ GIAO TUYẾN");
- the human-readable explanation (`learner_reason`, or the cleaned cut explanation);
- "Dừng ở bước" / "Loại vấn đề".

The technical codes stay available to developers in:
- the envelope / API response (`reason_code`, `error_code`, `reason`, `failure_category`);
- the backend logs;
- test evidence.

## Tests

**RED:** 10 failures on the old code (`verification/red-green/p3-red.txt`).

`final-quality.test.tsx`:
- The sphere case and the cylinder/cone cases now assert on the **whole** rendered notice: no `CURVED_`, no `<details>`, no "Chi tiết chẩn đoán".
- New `it.each` over six geometric codes, as `reason_code` and as `error_code`: the notice shows `learner_reason` and contains neither the code nor the technical reason text.

`hybrid-preview-contract.test.tsx`: the 25 refusal fixtures assert `not.toContain(env.reason_code)` on the whole notice again; the `<details>` stripping is gone.

**GREEN:** 83/83 across the two files plus `ui-hygiene.test.ts` (`verification/red-green/p3-green.txt`).
