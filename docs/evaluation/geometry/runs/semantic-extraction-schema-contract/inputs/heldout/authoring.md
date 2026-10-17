# Fresh held-out corpus — authoring record

Label: **INDEPENDENT_AI_AUTHORED_NOT_HUMAN_VALIDATED**

## Isolation

- Author: an isolated AI agent working only from its own knowledge of Vietnamese
  high-school solid geometry (Toán 11–12, hình học không gian).
- Read: nothing in the repository. The only filesystem actions were creating
  this output directory, listing it (it was empty), and writing the three files
  `corpus.json`, `oracle.py` and `authoring.md`. One fault-injection run of a
  copy of `oracle.py` was done in the session scratchpad, outside the repository.
- Not read: no prompts, schemas, code, docs, tests, or earlier corpora. The web
  was not used and no model/API call was made.
- The output format follows only the specification in the task message.

## Families (8 × 3, contiguous)

| family | cases | what varies |
|---|---|---|
| `cube_segment_and_point_plane` | h01–h03 | ASCII vs Unicode primes, symbolic edge a, point–line distance, squared-length request (unsupported) |
| `box_diagonal_and_volume` | h04–h06 | minimal pair with the height removed (missing_source), line–plane angle, area of a named rectangle |
| `regular_square_pyramid` | h07–h09 | height given vs lateral edge given, named centre O, plane–plane angle, triangle area |
| `perpendicular_edge_square_pyramid` | h10–h12 | skew-line distance, right triangle stated in words, SA length omitted (one request still answerable, one missing) |
| `right_triangular_prism` | h13–h15 | right / equilateral / isosceles-right base, prism plus sub-pyramid volumes |
| `tetrahedron_metrics` | h16–h18 | trirectangular, regular (a), DA ⊥ (ABC) with a max request and an explanation request |
| `square_prism_dihedral_and_subsolid` | h19–h21 | angle vs explicit cos² form, sub-tetrahedron volume, cube plus pyramid with an ambiguous "mặt bên" |
| `perpendicular_edge_equilateral_pyramid` | h22–h24 | line vs finite segment (minimal pair), circumscribed sphere (curved, unsupported) |

## Counts

- Cases: 24 (split `heldout`), families: 8
- Requests: 49, of which 23 cases have at least 2 requests (h18 and h21 have 3)
- Numeric oracles: 40 (31 `value_squared`, 9 `cos_squared`)
- Dispositions: answer 40 · unsupported 5 · missing_source 3 · ambiguous 1
  (non-numeric total 9)
- Curved-solid cases: 1 (h24)
- Cases with two solids or a solid plus a sub-solid: h15, h20, h21, h24

## Oracle

`oracle.py` (stdlib `fractions` only) builds explicit coordinates for every
figure. Irrational lengths are folded into a diagonal Gram metric (for example y
scaled by √3 for an equilateral base, z scaled by √7 for a derived height), so
every measure is computed exactly in ℚ from Gram determinants. It also checks
the stated data (edge lengths, right angles), shows that the missing_source
answers really depend on the omitted length, shows that the ambiguous reading
gives two different values, and checks the structural invariants (counts,
contiguous families, unique rids, quotes being substrings, target labels being
listed entities). `python oracle.py` prints a JSON summary and exits 0. A
deliberately wrong value injected into a scratch copy made it fail.
Values with the symbol a use a = 1.
