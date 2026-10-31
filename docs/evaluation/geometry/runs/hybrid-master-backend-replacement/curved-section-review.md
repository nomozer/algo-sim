# Independent review of curved sections and the cone ratio on /4: `INDEPENDENT_CURVED_SECTION_REVIEW_READY` (round 3)

- **Reviewer:** a fresh-context subagent.
- **Conditions:** read-only; 0 provider calls; targeted tests only.
- **Probes:** `section-review/p1–p10` in the session scratch directory. They were not copied here.

| round | commit | verdict | findings | fix |
|---|---|---|---|---|
| 1 | `5dc812ed` | NOT_READY | **B1:** with two sections, a derived cone whose quote names no plane, or starts mid-sentence, bound to the wrong section (27/64 served for 1/8). **M1:** a ratio with unit a crashed with KeyError. **M2:** a shape word contradicting the section kind was served. **m1–m4:** notation not checked; axial certificate re-derived from the layout; transition-layer wording; freeze pending. | `140ead7a`. Quotes must start a sentence; with two sections the derived cone must name its plane; shape words and `section_shape` must agree with the section kind; a written notation must be this solid's; the axial plane must contain the axis (kernel predicate); a ratio stays dimensionless. |
| 2 | `140ead7a` | NOT_READY | **B2:** two sections with the same plane name; both readings were served. | `bfe8912f`: duplicate section plane names are refused as `AMBIGUOUS_REFERENCE`. |
| 3 | `bfe8912f` | **READY** | 0 BLOCKER. Every earlier reproduction is refused, and all served values match hand oracles. The only MAJOR was process: the candidate freeze was pending. | Re-frozen in the next commit. |

## Accepted minors (safe, typed refusals)

- Two **unnamed** sections both default to "α" and are refused as ambiguous.
- `_dau_cau` accepts ":" as a clause start, and `_vi_tri` checks the first occurrence only. SOURCE_PREMISE_UNREAD covers both today.
- Mixed-case shape words are accepted; this is harmless.

## Deliberate difference from Adapter /3 (not a gap)

Adapter /3's own cone fixture (`C.cone_base`) asks for "tỉ số thể tích" **without a direction**. Adapter /3 serves 1/8 by assuming small : original. /4 refuses a ratio whose order the text does not state, because an inverted ratio is a wrong answer.
