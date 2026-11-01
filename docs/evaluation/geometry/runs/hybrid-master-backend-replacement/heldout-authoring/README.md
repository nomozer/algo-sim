# Held-out authoring package (for an independent author)

**Status:** `AUTHORING_INDEPENDENCE = NOT_ESTABLISHED`. No author has been named, and the implementer has written **no** case. This folder holds instructions and a template only.

## Who may author

A person who did not build or tune the system: the Owner, or a teacher the Owner nominates.
- Not the implementer, and not an AI agent of this repository.
- They must not see system outputs for any draft case before the corpus is frozen.
- They must be named in the Owner GO.

## What to write: 60 problems (protocol §2)

**45 expected-serve.** These are natural Vietnamese grade 11–12 solid-geometry problems.
- Each asks at least one exact quantity. Problems that only ask to construct are excluded.
- Kinds:
  - `distance` (lengths count as distances);
  - `angle_cos_sq` (cos² of an angle) or `angle_cos`;
  - `volume`, `area`, `lateral_area`, `radius`;
  - `volume_ratio`, `residual_volume`.
- Spread the problems over pyramids, prisms, cuboids, cubes **and curved solids**: spheres, cylinders and cones, with π answers. Also spread them over section-with-measure, distance, angle and volume questions. Each stratum needs at least 3 problems, or it is reported as `INSUFFICIENT_N`.

**15 expected-refuse.** Give each a `refusal_class` of `OUT_OF_DOMAIN`, `CONTRADICTORY_DATA` or `MISSING_DATA` (5 each). Do not write proof requests ("Chứng minh …"): they are out of scope.

**Exclude:**
- symbolic units such as "cạnh a"; use numbers;
- images;
- any text copied or adapted from this repository.

## Oracle rules

- Compute every answer **by hand or with a CAS independent of this repository, before any system run.**
- Write exact values: `"8/3"`, `"2√6/3"`, `"36π"`, `"√3/4"`. Never decimals: the harness refuses them. For `angle_cos_sq`, write cos² itself.
- List every quantity the problem asks, but write **each distinct value once**. If two asked distances are both 12, write `["12"]` (review n2).
- Do not ask for a plain volume together with a volume ratio or remaining volume in the same problem. Systems may show auxiliary volumes as targets, and the strict rule would then fail a correct answer (review n1). Ask for them in separate problems.
- Record the premise sentences that must be read, so failures can be attributed.
- **π with a radical:** write π **before** the square root: `"4π√2"`, not `"4√2π"`. The second form is not in the `parse_exact` grammar, and the harness refuses it before any run.
- **Curved surfaces (fixed before any corpus, the same for both arms).** The scorer reads each shown value by its producer kind, and in both arms the exact kernel measures a solid's surface only as its curved surface.
  - The **surface area of a sphere** ("diện tích mặt cầu") goes under `lateral_area`, because a sphere's curved surface is its whole surface, 4πR².
  - The **lateral area** of a cylinder or cone also goes under `lateral_area`.
  - **Do not ask** for the total surface area ("diện tích toàn phần") of a cylinder or cone. Neither arm shows it under a scorable kind, so a correct answer could not be scored. Ask for the lateral area, volume or radius instead.

## Format and freeze

1. Fill in `corpus-template.json`. Do not include a `dry_run` field.
2. Run `backend/scripts/run_paired_route_evaluation.py --corpus corpus.json --manifest`. It validates the corpus, prints `corpus_sha256` and the runtime identity, and runs the contamination scan. An exact match fails. Near matches are listed for the author to check.
3. Put the corpus hash, the author's name, the harness hash and the measured-system hash in the Owner approval file. Record them in a protocol amendment as well.
   - The approval must also state `corpus_author`, `authoring_independence` and `evaluator_independence`. Criterion 7 reads them; a run without them is a certain NO-GO.
   - `--manifest` prints the hashes of the tree it runs in. Run it in the tree that will make the live run, after the last harness change (fourteenth continuation: the harness changed, so hashes printed before then do not bind).
   - One approval file allows one live run. A stopped or interrupted run is not resumed; a re-run needs a new approval file.
4. After the first live request the corpus is immutable. Errata go to an amendment and are reported. Every observed case becomes development data for later runs; a new blind run needs a new corpus.
