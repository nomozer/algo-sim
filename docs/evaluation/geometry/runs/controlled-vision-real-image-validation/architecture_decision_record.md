# Architecture decision: image input route

Status: **`ARCHITECTURE_DECISION_PENDING_LIVE_EVIDENCE`** — keep **local-first with span confirmation** as the
production route. Do not switch to Vision-first. Adaptive Hybrid is the candidate to test once a live comparison is
authorised. Supersedes nothing; the previous record
([real-image-ocr-vision-comparative-acceptance](../real-image-ocr-vision-comparative-acceptance/architecture_decision_record.md))
reached the same provisional conclusion on weaker evidence.

## Evidence (this run, candidate `c53be83db`, 25 rendered VMMU solid-geometry crops)

| finding | value | class |
|---|---|---|
| Critical premise/goal facts recovered by local OCR, evaluation split | 124/136 (91%); 12/19 images complete | VERIFIED FACT against agent references |
| Images the fidelity gate accepted automatically | 0/25 | VERIFIED FACT |
| Wrong-served against the dataset key (all routes) | 0 of 4 served | VERIFIED FACT |
| Served after confirmation, no symbol edited | 3/25 (`r476`, `r273`, `r492`) | VERIFIED FACT, scripted confirmation |
| Statements the solver finishes **from the agent's own transcription** with no AI | 6/23 polyhedron items (4 correct, 2 refused) | VERIFIED FACT, diagnostic |
| Refusals on verified text owned by the local parser / Source Gate / kernel | 12 / 5 / 1 (+1 clarification) | VERIFIED FACT |
| Live Vision quality, cost or latency | — | NOT_MEASURED, `BLOCKED_PENDING_OWNER_APPROVAL` |

## Why this decision

1. **Recognition is not the main bottleneck for polyhedron images; parsing is.** Even with a perfect transcription,
   17 of 23 polyhedron statements cannot be solved without an AI extractor. A better OCR or a Vision reader alone
   would not raise the zero-AI solve rate above 4/23 on this corpus. *(INFERENCE from the transcription diagnostic.)*
2. **The local gate is safe and conservative.** It accepted nothing automatically, and nothing was served wrong.
   12 evaluation images had every critical fact right but were still held for confirmation, mostly with
   `DIAGRAM_FACTS_UNVERIFIED` plus `UNCERTAIN_SPANS`. The cost is confirmation burden, not wrong answers.
3. **Vision-first is unproven and has known costs:** a provider call per image, no offline use, and image bytes leave
   the device. No measurement here shows it reads Vietnamese math notation better than the local pair.

## Counter-evidence and risks

- Confirmation burden is total: every image needs the student. Burden in real use is not measured (no students).
- The corpus is one dataset of rendered crops, chosen with a Tesseract keyword screen. It has no photographs, no
  handwriting and no multi-problem pages, so it may flatter local OCR.
- The served answers were confirm-only. Images whose spans need real edits all stopped at the parser.

## Conditions for revisiting

| switch to | requires |
|---|---|
| Adaptive Hybrid in production | Owner-authorised live run on the frozen manifest. Vision must recover critical facts at least as well as local OCR on the same images, with 0 wrong-served, and solve more of the 17 parser-incomplete items through the live extractor, at an accepted USD/image and latency |
| Vision-first | All of the above, and Vision must also beat local OCR on recognition. Offline use and privacy must be explicitly given up |
| Less confirmation | A measured false-acceptance bound on a larger, independently transcribed corpus before relaxing `DIAGRAM_FACTS_UNVERIFIED` or span blocking |

## Highest-value next step

Close the **local parser / Source Gate coverage gap** using the case specifications in
[`geometry_capability_gap_backlog.json`](geometry_capability_gap_backlog.json), developing only on
development-split items and moving any evaluation item used into development. In parallel, obtain the Owner's
decision on a bounded live Vision run, which would measure the same 25 images.
