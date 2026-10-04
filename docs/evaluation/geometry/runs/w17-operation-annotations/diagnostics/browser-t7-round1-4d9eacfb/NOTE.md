# Task 7 browser round 1 — 4d9eacfb (diagnostic, not acceptance evidence)

The first real-browser round of W17. It ran on the detached scratch worktree `D:/tmp/w17-t7` at
4d9eacfb, with the committed suite and 25 fixtures generated there (0 model calls). Every
family failed. Before any fix, each failure was classified by cause:

| Cause | Kind | Fixed in |
|---|---|---|
| `ANNOTATION_MISSING` (S(ABC), AB = 3): a crowded base label had all four side positions taken | product | 2c7d4134 (corners), then 240ecba5 (rings 6/12/18 px) |
| Refusal card: the hint repeated the backend message; a CONSTRUCTION refusal was labelled "dữ kiện không truy được về đề bài" | product | 2c7d4134 |
| `CAUSAL_CANVAS_ROLE_HUE`: the blue "đang xét" border of the selected quantity's label counted as a drawn figure hue | measurement | ca6c4107 (DOM labels masked, as point labels since W12) |
| `SECTION_FILL_DISTINGUISHABLE` min ΔE 2.8: a fill sample under the 90 %-opaque area label | measurement | ca6c4107 (samples under DOM labels excluded) |
| `TOGGLE_CHANGED_CAMERA`, `SELECTION_MOVED_CAMERA`: 1e-14 ULP damping compared by bytes | measurement | ca6c4107 (`cameraMotion` ≤ `CAMERA_SETTLE_TOLERANCE`) |
| `CANVAS_NOT_RESTORED` (cuboid, mobile): neutral frame captured mid-transition | measurement | ca6c4107 (frames at rest), proven by `../browser-t7-diag-cuboid-mobile-4d9eacfb/` |

- `BROWSER_EVIDENCE.json` and `SUITE.log` are copied unchanged from the scratch output.
- `screenshots/` holds only the four captures that show the product defects.
- The full screenshot set stayed in the scratch folder; it is listed in `../TEMP_FILE_INVENTORY.json`.
