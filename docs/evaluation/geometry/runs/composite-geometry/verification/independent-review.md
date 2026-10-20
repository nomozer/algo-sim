# Independent review — `composite-geometry` (Wave 2C)

Reviewer: fresh read-only subagent `1946805e-14f5-4e61-ac88-fce0d3e864f4` (no implementation history; no file or Git
state modified; scratch reproductions kept outside the repository).

## Round 0 (Codex session, recorded here for continuity)

Target: candidate `503c9d6e1b4bf60a54b1179b6299598b27b0d8f7` (product `739a833a1cdaff2a6b03a5bcc3df075dc6c0235f`).
Reviewer finding reported in the interrupted Codex session (verbatim transcript not available in this repository):
**BLOCKER** — a direct `regular_pyramid` call on a derived sub-pyramid was served when its quadrilateral base was a
non-square rectangle. Reproduced as RED in `regular-blocker-red.stdout.log` (`[6-False]` SERVED), fixed in
`deeb1748b2d00cafdae74dacef0fec026cf5ff47`.

Root cause: `_Dung._dung_khong` validated `regular_pyramid` only by equal lateral edges, which puts the foot at the base
circumcentre; every rectangle is cyclic. Derived solids skip the root apex-over-centre construction, so nothing else
checked the base. On the planner route the same flag also emits `regular_polygon` on the derived base, which was already
checked — only the direct route was exploitable (`regular-blocker-red.stdout.log`: planner-route tests PASS on the old
engine). Fix: regular pyramid ⇔ exactly regular base (`_canh_da_giac_deu`) ∧ equal lateral edges ∧ apex off the plane.

## Round 1

Target: `af26fd03ad9b18b258cd5fedb5e7b216b346762d` (product `deeb1748`, tree `cbec8970…`).
Verdict: **PASS_WITH_FINDINGS**. BLOCKER: none (previous blocker fixed on both routes; rectangle, rhombus, crossed
order, degenerate, non-coplanar, oblique apex, forged `regular_polygon` and root path all refuse; valid square, hexagon,
concave derived base and tetrahedral children served with hand-checked values).

- IMPORTANT-1: `_mat_ben_vuong_goc_day` used the first solid in key order instead of `self.root` ⇒ relabelling refused a
  valid composite problem (ABC served V² = 1, XYZ refused `UNSUPPORTED_PLANE`). Safe refusal, label dependence.
- IMPORTANT-2 (pre-existing): `regular_polygon` did not check planarity; a regular tetrahedron's skew SABC passed as a
  square and was served.
- MINOR-1: `_hai_duong_cat_nhau` passed derived-solid heights. M2–M7: cosmetic / scope notes (see below).

Fixed in `050bb35377b40146d4862afe050a40228821a758` (RED `review2-red.stdout.log`, GREEN `review2-green.stdout.log`).

## Round 2

Target: freeze `962b97237246b65bb2d4abc6ebed9bc5b971f5fd` (product `050bb353`, tree
`3e6c403cff0e2c4ae96c4a541f97ecbe92f1efd821e08d5fdb1572d4ee823ab9`).
Verdict: **INDEPENDENT_REVIEW_PASS**. BLOCKER none, IMPORTANT none. `test_composite_geometry.py` 42 passed; targeted
regression set 423 passed. All round-1 reproductions re-run with identical outcomes except the skew square, now REFUSED.
Planarity guard short-circuits before any division; triangle/square/hexagon regular bases still served (8/9, 7168/9, 144).

Carried-over MINOR (not fixed, no correctness impact):

- The forged skew square and a crossed root regular base order refuse as `ENGINE_SELF_CHECK_FAILED` (the premise was
  consumed by the construction) rather than `INCONSISTENT_FACTS`; fail-closed but attribution is imprecise.
- M3 `hop_dong_to_po_da_khai` returns a per-solid map for any multi-solid plan; values unchanged (0 changed rows).
- M4 `_kiem_mat_chung` accepts one closed wording; other "mặt chung" phrasing over-refuses.
- M5 bases whose first three vertices are collinear refuse `COLLINEAR_POINTS` (conservative).
- M6 test/corpus rename probe also rewrites "Cho"; still served.
- M7 volume certificates are issued only for composite plans.

Measurement after round 2 is on `9285075ae9b932fbbe4430ef60acb5855a0b677d` (docs-only after `962b9723`; same tree).
