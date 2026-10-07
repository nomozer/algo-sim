# exact-dimensions — visual review

Status: **NOT_APPROVED** (only the user may change this). Ten images, chosen before the measurement
(`inputs/REVIEW_SET.json`). Problem shown in R1–R6 and R9–R10: "Cho hình chóp tam giác đều S.ABC có cạnh đáy bằng 6,
chiều cao bằng 4. Tính thể tích khối chóp S.ABC." — the program lays it out on an axis chart, which the old product
refused.

| # | image | look for |
|---|---|---|
| R1 | `images/regular-triangular-pyramid/desktop/neutral_final.png` | the base looks equilateral, the apex stands over the centroid G — the true figure, not the chart |
| R2 | `images/regular-triangular-pyramid/desktop/rotated_neutral.png` | after the orbit: hidden edges dashed, visible edges solid, the figure keeps its shape |
| R3 | `images/regular-triangular-pyramid/mobile/neutral_final.png` | same on mobile |
| R4 | `images/regular-triangular-pyramid/desktop/detail_volume.png` | V = 1/3 · S(ABC) · SG with S(ABC) = 9√3, SG = 4, V = 12√3 |
| R5 | `images/regular-triangular-pyramid/desktop/selected_area.png` | selecting the base area highlights the base (D2 kept) |
| R6 | `images/regular-triangular-pyramid/desktop/formation/steps_panel_open.png` | construction steps: medians, centroid G, height SG |
| R7 | `images/regular-triangular-pyramid/served/regular_tetrahedron/desktop/served.png` | regular tetrahedron with edge 6: V = 18√2 |
| R8 | `images/regular-triangular-pyramid/negative/assumption/desktop/refusal.png` | missing height is refused; the wording says the system could not verify (reason less precise — open issue) |
| R9 | `images/focus/regular-triangular-pyramid/low/focus_layout.png` | low screen 1366×650, focused mode fits |
| R10 | `images/focus/regular-triangular-pyramid/mobile/focus_layout.png` | mobile layout; the blank band (D5) is still there — not a fix |

Oracle crops (built from R1–R3 and the mobile rotated view, endpoints projected by the independent oracle):
`images/regular-triangular-pyramid/hidden-edges/`.

Still pending from earlier packages: `runs/regular-triangular-pyramid-w01/REVIEW.md` (R1–R12) with the W5/W4
packages, and the D5 option.
