# Browser acceptance (P4)

## Setup

- **Source:** clean detached worktree `t3-b1b2` at `4ec36db9`. Product `af670aa6` is unchanged since then; `git status --porcelain` was empty before and after every run.
- **Servers:** Claude's own servers only, all stopped afterwards (private Vite dep cache):
  - dev server on `127.0.0.1:3115`;
  - `vite preview` on `127.0.0.1:4173`.
- **Not touched:** Codex's server on 3117.
- **Browser:** Chrome headless, SwiftShader. Non-local requests aborted; `/api/health` and `/api/auth/me` stubbed.
- 0 model calls.

| Check | Viewports | Result | Receipt (`verification/browser/`) |
|---|---|---|---|
| Official Visual suite | 1440×900, 390×844 | FAIL, product findings F1, F2 only (OFFICIAL_SUITE_RESULTS.md) | `../../visual/official-suite-run2/` |
| Adapter /4 consumer (`check-adapter4-browser.mjs`, 47-case offline export, byte-identical to the integrated one) | 1440, 390 | **`FRONTEND_CONSUMER_ACCEPTANCE_PASS`**: 94 rows (44 SERVED, 50 REFUSED), 0 errors, `tree_clean: true` | `adapter4/receipt.json` |
| Refusal surface (`certify-refusal-surface.mjs`, production build) | 1600×900 | **ĐẠT 21/21**, 0 console errors: label, no scene, no technical code, a way back, broken envelopes never blank the page | `refusal/refusal-surface.json` |
| Scene3D orbit gate (`scene3d-orbit-gate.mjs`) | gate default | **ĐẠT**: p1, p6, p7 449° about Z, snap 0, allocations 0 | `orbit-gate/` |
| Owner screens: names, coincident points, hidden edges, Mode A / B | 1440, 390 | 12 screenshots, 0 page errors | `owner-visual/` (+ `receipt.json`) |
| Owner screens: refusals | 1440, 390 | 6 screenshots; technical codes visible: none; diagnostics drawer: none; canvas: 0 | `owner-refusal/` (+ `receipt.json`) |

## Screens prepared for owner visual approval

All are full product pages (not cropped canvases), each in a `-1440` and a `-390` file.

| File | Shows | Read from the receipt |
|---|---|---|
| `owner-visual/plane-name-P-*.png` | Sample `cau-cat-mat-phang`, «Hình phụ» on | Plane label `(P)` (was `(HUW)`); step label "Đường tròn giao của (S) và (P)" |
| `owner-visual/section-named-cycle-*.png` | Sample `thiet-dien-chop` | Plane `(MNP)`; the fourth section vertex has no name, so the section is named by its construction sentence "Thiết diện của S.ABCD cắt bởi (MNP)", not a cycle through an id |
| `owner-visual/section-unnamed-vertices-*.png` | Adapter /4 `CORPUS-DEV01-construct` | Section "Thiết diện bởi (α)"; unnamed intersection points unlabeled |
| `owner-visual/coincident-points-*.png` | Adapter /4 `PERP-square-third` | Coincident identity label `A ≡ H ≡ H1`; section with all named vertices keeps its cycle "Thiết diện MNPQ" |
| `owner-visual/hidden-edges-mode-a-*.png` | Sample `the-tich-chop`, Mode A | Dashed hidden edges; no final-answer label |
| `owner-visual/mode-b-reveal-*.png` | Same sample, «Phân tích toán học» open | `V(S.ABCD) = 16/3`, `d(S, (ABC)) = 4` under «Kết quả toán học» |
| `owner-refusal/refusal-*.png` | `GEO-contradictory-length` (geometric refusal "DỮ KIỆN MÂU THUẪN"), `NEG-missing-height`, `NEG-negated-plane` | Title, plain explanation, "Dừng ở bước / Loại vấn đề"; no code, no drawer |

## Observations for the owner's visual review (not changed)

**Construction points labelled in `cau-cat-mat-phang`.**
- The regenerated offline sample now labels the construction points U and W next to H; the stale sample showed only H.
- Its plane, drawn through H, U, W, appears as a small dotted triangle, so its `(P)` tag is in the DOM but hard to see at this zoom.
- This sample's program uses free layout points that the default route would refuse (`ASSUMPTION_INVARIANCE_UNPROVEN`, cache probe). It exists only as an offline sample.

**Given points in Mode B.** On the offline samples, «Quan hệ & Chứng chỉ kiểm chứng» lists every given point as "A = hệ trục do đề chọn". The wording is inherited.
