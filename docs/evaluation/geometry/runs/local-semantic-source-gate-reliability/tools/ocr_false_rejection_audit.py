"""Was the OCR fidelity gate wrong to hold images whose critical facts were all recovered? Reads receipts only.

Inputs (previous run, OCR code unchanged since): local_ocr_*.json (after the reread fix) and the frozen manifest.
Per held image: each flagged span is checked against the agent reference (is its text, as read, present in the
reference? a "false alarm" if yes); the statement outside the critical facts is diffed word by word against the
reference to find UNFLAGGED differences; the diagram block is compared with the agent's diagram reading.
No acceptance rule is changed by this audit.  Run from backend/.
"""
from __future__ import annotations

import difflib
import json
import re
import unicodedata
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

RUN = Path(__file__).resolve().parents[1]
PRIOR = RUN.parent / "controlled-vision-real-image-validation"
PRIME = str.maketrans({"’": "'", "′": "'", "`": "'", "´": "'", "º": "°", "⁰": "°"})


def norm(s: str) -> str:
    return re.sub(r"\s+", " ", unicodedata.normalize("NFC", s or "").translate(PRIME)).strip()


HEADER = re.compile(r"^\s*(?:Câu|Bài)?\s*\d+\s*[.:]\s*", re.IGNORECASE)


def words(s: str) -> list[str]:
    """Words after dropping the exam header and spacing around punctuation / '=' (layout noise, not reading errors)."""
    t = HEADER.sub("", norm(s))
    t = re.sub(r"\s*([,.;:=()])\s*", r"\1 ", t)
    return re.findall(r"[^\s]+", t)


def main() -> int:
    items = {i["case_id"]: i for i in json.loads((PRIOR / "new_in_scope_image_manifest.json").read_text(encoding="utf-8"))["items"]}
    rows = []
    for part in ("development", "frozen_external_evaluation"):
        for c in json.loads((PRIOR / f"local_ocr_{part}.json").read_text(encoding="utf-8"))["cases"]:
            item = items[c["case_id"]]
            ref_stmt = norm(item["statement"])
            ref_all = norm(item["ground_truth_text"])
            flagged = []
            for s in c["review_spans"]:
                txt = norm(s.get("text") or "")
                if not txt:
                    continue
                core = txt.strip(".,;:")
                flagged.append({"text": s.get("text"), "reason": s.get("reason"), "blocking": s.get("blocking"),
                                "present_in_reference": bool(core) and core.replace(" ", "") in ref_all.replace(" ", "")})
            ocr_stmt_words, ref_words = words(c["ocr_text"].split("\n")[0]), words(ref_stmt)
            sm = difflib.SequenceMatcher(a=ref_words, b=ocr_stmt_words, autojunk=False)
            unflagged = []
            flagged_texts = {norm(f["text"]).strip(".,;:") for f in flagged}
            for op, a0, a1, b0, b1 in sm.get_opcodes():
                if op == "equal":
                    continue
                got = " ".join(ocr_stmt_words[b0:b1])
                if any(ft and ft in got for ft in flagged_texts):
                    continue
                unflagged.append({"op": op, "reference": " ".join(ref_words[a0:a1]), "ocr": got})
            math_unflagged = [u for u in unflagged if re.search(r"[A-Z0-9√°=⊥'()]", u["reference"] + u["ocr"])]
            all_facts = c["all_critical_facts_recovered"]
            reasons = set(c["blocking_reasons"] or [])
            verdict = ("NOT_A_FALSE_REJECTION_FACT_MISSING" if not all_facts else
                       "CORRECT_HOLD_UNFLAGGED_MATH_DIFFERENCES" if math_unflagged else
                       "HOLD_ONLY_FOR_DIAGRAM_REFERENCE" if reasons == {"DIAGRAM_FACTS_UNVERIFIED"} else
                       "HOLD_WITH_FLAGGED_SPANS_ALL_FALSE_ALARMS" if flagged and all(f["present_in_reference"] for f in flagged if f["blocking"]) else
                       "HOLD_WITH_GENUINE_FLAGGED_ERRORS")
            rows.append({"case_id": c["case_id"], "partition": part, "all_critical_facts_recovered": all_facts,
                         "blocking_reasons": sorted(reasons), "diagram_classification": c["diagram_classification"],
                         "agent_diagram_reading": item["diagram_dependency_by_agent_reading"],
                         "flagged_spans": flagged, "blocking_flags": sum(bool(f["blocking"]) for f in flagged),
                         "blocking_flags_that_were_false_alarms": sum(bool(f["blocking"]) and f["present_in_reference"] for f in flagged),
                         "unflagged_statement_differences": unflagged[:20], "unflagged_math_differences": math_unflagged[:12],
                         "verdict": verdict})
    held_full = [r for r in rows if r["all_critical_facts_recovered"]]
    out = {"run_id": RUN.name, "generated_at_utc": datetime.now(timezone.utc).isoformat(),
           "source": "controlled-vision local_ocr_*.json (after reread fix) vs agent references (AGENT_TRANSCRIBED_UNVERIFIED)",
           "question": "Among images with every critical fact recovered, was holding them for confirmation a false rejection?",
           "images": len(rows), "images_with_all_critical_facts": len(held_full),
           "verdicts_among_all_facts_images": dict(Counter(r["verdict"] for r in held_full)),
           "blocking_flags_total": sum(r["blocking_flags"] for r in rows),
           "blocking_flags_false_alarms": sum(r["blocking_flags_that_were_false_alarms"] for r in rows),
           "every_image_references_a_diagram": all("DIAGRAM_FACTS_UNVERIFIED" in r["blocking_reasons"] for r in rows),
           "policy_decision": "NO_GATE_CHANGE: no image is shown to be safely acceptable as a whole; see verdicts",
           "limits": ["agent references, not human-verified", "word diff is a proxy: reading-order and spacing noise is included",
                      "'present in reference' cannot tell which occurrence a short token belongs to"],
           "cases": rows}
    (RUN / "ocr_false_rejection_audit.json").write_text(json.dumps(out, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: out[k] for k in ("images_with_all_critical_facts", "verdicts_among_all_facts_images", "blocking_flags_total",
                                          "blocking_flags_false_alarms", "every_image_references_a_diagram")}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
