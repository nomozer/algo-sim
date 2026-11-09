# plan — adaptive-local-ocr-fallback (Workstream A)

## PRE-FLIGHT (RULES §2)

```
Active branch:            feat/adaptive-local-ocr-fallback (worktree .superpowers/worktrees/adaptive-local-ocr-fallback)
HEAD:                     d79565b52ec19a7b1a75be28c09bb43cc0f6d146 (COMMON_BASE_SHA)
Working tree:             clean at start
Current milestone:        Hybrid /4 product; image ingestion is the optional text-acquisition step before /api/analyze
Task classification:      SUPPORTING (provider-load reduction on the image → problem-text step; no new learner function).
                          Shipping a second reading engine to production would be DEEP_HARDENING unless evidence
                          shows it is at least as accurate as the current Vision path — see stop conditions.
Thesis relevance:         R0 unchanged: OCR/Vision only produce problem TEXT the learner reviews; TypedFactNext path untouched.
Existing related modules: ingestion/image.py (normalize, SHA-256 of pixels), region_detector.py (page, deskew, layout,
                          crop + full-image fallback), image_extraction.py (Vision, EXTRACTION_CACHE, in-flight dedup,
                          provenance guard), unified_input.py (prepare, retry, multi-image dedup/order/needs_selection),
                          document_reader.py (PDF/DOCX text layer = 0 Vision), frontend ProblemInput.tsx (edit ⇒ no re-read).
Reusable:                 detect_problem_regions / RegionDetectionResult, extract_problem_from_image + EXTRACTION_CACHE,
                          assess_extraction, REJECTION_MESSAGES / FLAG_MESSAGES, needs_confirmation /
                          EXTRACTION_NEEDS_CONFIRMATION, detect_domain.
Source of truth:          code + tests above; corpora CORPUS.json (SYNTHETIC_RENDERED) + run-local symbol-stress set.
Files expected to change: backend/app/ingestion/{region_detector,unified_input}.py (only if evidence supports),
                          new backend test, this run directory, CODE_INDEX entry.
Contract/cache/history:   no change to TypedFactNext, Source Gate, /api/input/prepare, /api/image/extract shapes;
                          no prompt/schema change ⇒ CACHE_VERSION unchanged; backend/app touched ⇒ re-freeze candidate.
Duplicate risk:           high for "page/crop/dedup" logic — all already exists; do not re-implement.
Dependency-cycle risk:    none (ingestion only imports image/region/extraction/document_reader).
Scope-creep risk:         an OCR stack + gate + cross-engine voting is a multi-wave capability (RULES §3c).
Smallest sufficient impl: measure first; ship OCR only if it is verifiably at least as good; otherwise ship only the
                          provider-call reduction the evidence supports and keep OCR as a diagnostic tool.
Explicitly excluded:      torch-based engines (EasyOCR/VietOCR: PyTorch ≥ hundreds of MB in python:3.12-slim),
                          PaddleOCR runtime (paddlepaddle), system installs needing admin, live Gemini calls.
Stop conditions:          a shared contract must change ⇒ stop + proposal; OCR loses Vietnamese diacritics or math
                          symbols on the calibration set ⇒ no production OCR (verdict DIAGNOSTIC_ONLY/PREFERRED).
```

## §2b anti-duplication checklist

| check | result |
|---|---|
| exact names (`local_ocr`, `ocr`, `tesseract`, `rapidocr`) in backend/frontend | none in product code (`rg -n -i "ocr" backend/app` → 0 hits; frontend hits are substrings like `BuocRef`) |
| same responsibility, other names | page detection / deskew / crop / quality → `region_detector.py`; retry-on-full-image → `unified_input._process_normalized_visual_page`; multi-image SHA-256 dedup → `prepare_unified_input` (`seen_image_hashes`); identical-key concurrency → `image_extraction._dang_cho`; result cache → `EXTRACTION_CACHE`; edit preservation → `merge_supplemental_text` + `ProblemInput.tsx` (`extractedBatchRef`) |
| callers | `/api/input/prepare` → `prepare_unified_input`; `/api/image/extract` → `extract_problem_from_image`; `ingest_to_text` image branch |
| CODE_INDEX | ingestion entries at `### ingestion/*` + the local-first run table |
| reuse candidates | `RegionDetectionResult` (add one field, default False), the existing retry predicate, existing status/reason enums |

## Work plan

1. Benchmark (scratch venv): Tesseract 5.5.3 `vie` best/fast (tesserocr wheel, no admin), RapidOCR 3.10
   PP-OCRv6 small/medium + PP-OCRv5 latin (onnxruntime). Input = product `prepared_image`. Receipt by script.
2. Gate evaluated offline from OCR output only; thresholds grid-calibrated on the labelled set (not held out).
3. Investigate `class_09_diagram_only` 2nd Vision call → root cause in the crop-retry predicate.
4. Implement only what the evidence supports; RED-first + fault injection.
5. Vision calls before/after on the same image set (mock provider at the network boundary).
6. Gates, re-freeze candidate (separate commit), report + run.json.

## Post-flight

- reused: `detect_problem_regions`, retry predicate, `EXTRACTION_CACHE`, multi-image dedup, existing enums.
- created: one dataclass field `RegionDetectionResult.crop_holds_all_content`; one test file; two run tools.
- duplicate check result: no parallel implementation created.
