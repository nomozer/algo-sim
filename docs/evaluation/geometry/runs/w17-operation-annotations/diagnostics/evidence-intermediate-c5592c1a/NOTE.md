# Acceptance evidence of the intermediate candidate d4a24eba — measured at c5592c1a (superseded)

This is a complete acceptance measurement. It was taken at the measurement commit c5592c1a on
the first freeze of the wave, candidate `d4a24eba…` (product commit add4afb0), and committed in
f07b0d24. Every gate passed:

- browser suite attempt 2:
  - 12/12 positives;
  - 40/40 negatives;
  - 2/2 served correct plane;
- occlusion: pass, `HUMAN_REVIEW_PENDING`;
- playback: 12/12;
- builder: 64 crops, 0 oracle disagreements;
- T3 `FULL_PRODUCT_GATE_PASS`: pytest 6928/0, vitest 1044/1044;
- identity gates: all pass.

The final whole-branch self-review then found three Important defects in `backend/app`
(red 01b0c27c, fix d3817d5f). The fixed product was frozen again as `d63d6fd4…` (921015b6).
Following the brief ("Nếu phát hiện lỗi sau freeze, sửa và tái đo trên candidate cuối"), every
acceptance run was repeated on that final candidate. The run folder's `results/`, `images/`
and `inputs/` now hold that final measurement.

What this folder keeps, unchanged except for the move:

| Path | Content |
|---|---|
| `results/` | the four result files of the c5592c1a measurement |
| `inputs/FIXTURE_MANIFEST.json` | the fixture manifest of that measurement |
| `logs/` | every captured log of that measurement, including the interrupted browser attempt 1 |

The images and fixtures of the c5592c1a measurement are the ones committed in f07b0d24. To
inspect them, run `git show f07b0d24:<path>` or check out that commit in a worktree. The later
measurement overwrote them in place.
