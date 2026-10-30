# Preregistration: premise-sentence generalization (W4 Phase F, slice 1)

Locked at `e5dc3d28` before any product edit; development security regression, not a blind holdout; 0 provider calls.

- **Corpus:** `dev-corpus/cases.json`, built by `tools/build_dev_cases.py`, LF SHA-256 `17b66cae38b99d3faee2da5fbb34d538d2b47d9e42ec6fd983726c2c90449992`. Its 70 cases are authored independently of the Wave 3 text, with their own labels, values and ratios.
  - 18 CANON: phrasings the pre-W4 product serves.
  - 42 VARIANT: the same facts written with textbook connectors and lexical forms.
  - 10 NEGATIVE: one tamper each — value, solid qualifier, conditional, disjunction, wrong height edge, cube side, wrong right-angle vertex.
- **Route:** Adapter /4 `run_typed_fact_next_v2_route`, the Wave 3 route.
- **Oracle (metamorphic):** a VARIANT passes only if it is SERVED with an `answer_exact` identical to its CANON twin, and that twin is itself served on the same tree. A NEGATIVE passes only if it is not served. A CANON passes only if it is served.
- **RED** (`red-baseline.json`, `e5dc3d28`):
  - CANON 18/18 (all pass);
  - VARIANT 6/42 pass (only TP3, the perpendicular-line slice);
  - NEGATIVE 10/10 pass.
- **GREEN target:**
  - VARIANT 42/42, CANON 18/18 and NEGATIVE 10/10;
  - no change to the locked 96, the 203 probes, Wave 3 negatives 72/72, or 0 wrong-served.
- **Design constraint:** extend the closed SG-3 clause grammar (`registry._phan_tich_cau` regexes) and the two-line slice's atomic solid forms with number-free lexical/connector variants only.
  - Every clause must still map 1-to-1 to a validated call.
  - Values stay bound by labels or by the base clause.
  - A solid qualifier ("tam giác"/"tứ giác") must agree with the base vertex count.
- **Generator correction before lock:** RP2 originally used a plane containing its own through-point line, a geometry error in the generator, and was refused with `LINE_CONTAINED_IN_PLANE`. It was fixed to (PP', PR) before this lock.
- **Wave 3 use:** measured afterwards as `POST_FEEDBACK_DEVELOPMENT_REGRESSION` only; it is not used for tuning.
