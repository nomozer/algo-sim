# -*- coding: utf-8 -*-
"""Freeze an unseen, disjoint, rights-cleared (`MIT`, `anvo25/vmmu`) image evaluation set
BEFORE any OCR or geometry evaluation in `student-ready-geometry-simulation-input-reliability`.

Strictly 0 AI/LLM/Vision calls. Uses sequential, rate-paced HTTP requests (`1.2s` sleep,
honoring `Retry-After` on 429/5xx). Never prints OCR text or image contents to stdout;
saves selected PNGs into gitignored `.superpowers/external_image_cache/student-ready-unseen-vmmu/`
and writes metadata/hashes only to `frozen_unseen_vmmu20_manifest.json`.
"""
from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import io
import json
import os
from pathlib import Path
import re
import time
import urllib.error
import urllib.request

ROOT = Path(__file__).resolve().parents[6]
RUN_DIR = Path(__file__).resolve().parents[1]
EXT_CACHE = ROOT / ".superpowers" / "external_image_cache"
DEST_CACHE = EXT_CACHE / "student-ready-unseen-vmmu"
TESSDATA = Path(os.environ.get("LOCAL_OCR_TESSDATA") or str(ROOT / ".superpowers" / "tessdata_fast"))
OUT_PATH = RUN_DIR / "frozen_unseen_vmmu20_manifest.json"

_SOLID_KW_RE = re.compile(
    r"hình\s+chóp|khối\s+chóp|lăng\s+trụ|tứ\s+diện|hình\s+hộp|lập\s+phương"
    r"|hình\s+nón|khối\s+nón|hình\s+trụ|khối\s+trụ|mặt\s+cầu|khối\s+cầu",
    re.IGNORECASE | re.UNICODE,
)
_POLY_KW_RE = re.compile(
    r"hình\s+chóp|khối\s+chóp|lăng\s+trụ|tứ\s+diện|hình\s+hộp|lập\s+phương",
    re.IGNORECASE | re.UNICODE,
)
_OXYZ_OR_CALC_KW_RE = re.compile(
    r"oxyz|tọa\s+độ\s+không\s+gian|véc\s*-?\s*tơ|vectơ|tích\s+phân|nguyên\s+hàm|hàm\s+số|đạo\s+hàm|cực\s+trị|số\s+phức|logarit",
    re.IGNORECASE | re.UNICODE,
)

# Uncached row ranges within full_vqa Math [240..695]
_UNCACHED_GAP_RANGES = [(240, 299), (300, 456), (474, 528), (540, 695)]


def _collect_prior_used() -> tuple[set[str], set[str], set[str]]:
    runs_dir = ROOT / "docs" / "evaluation" / "geometry" / "runs"
    used_qids: set[str] = set()
    used_shas: set[str] = set()
    used_names: set[str] = set()
    for fp in runs_dir.rglob("*"):
        if RUN_DIR in fp.parents or fp == OUT_PATH:
            continue
        if fp.suffix not in (".json", ".py", ".md"):
            continue
        txt = fp.read_text(encoding="utf-8", errors="ignore")
        for m in re.findall(r"Math_\d+_test_\d+_question_\d+", txt):
            used_qids.add(m)
        for m in re.findall(r"\b[0-9a-f]{64}\b", txt):
            used_shas.add(m)
        for m in re.findall(r"external_image_cache[/\\]([^\s\"'`,)]+)", txt):
            used_names.add(Path(m.replace("\\", "/")).name)
    return used_qids, used_shas, used_names


_LAST_HTTP_TS = 0.0


def _http_get_bytes(url: str, timeout: int = 20, retries: int = 5) -> bytes:
    global _LAST_HTTP_TS
    last_err: Exception | None = None
    for attempt in range(retries):
        elapsed = time.monotonic() - _LAST_HTTP_TS
        if elapsed < 1.2:
            time.sleep(1.2 - elapsed)
        _LAST_HTTP_TS = time.monotonic()
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0", "Connection": "close"})
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return r.read()
        except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError) as exc:
            last_err = exc
            wait_s = 15.0 * (1.5 ** attempt)
            if isinstance(exc, urllib.error.HTTPError):
                if exc.code not in (429, 500, 502, 503, 504):
                    raise
                ra = exc.headers.get("Retry-After") if exc.headers else None
                if ra:
                    try:
                        wait_s = max(1.5, float(ra))
                    except ValueError:
                        pass
            print(f"HTTP retry {attempt + 1}/{retries} after {type(exc).__name__}; sleep {wait_s:.1f}s", flush=True)
            time.sleep(wait_s)
    assert last_err is not None
    raise last_err


def _iter_gap_offsets() -> list[tuple[int, int]]:
    batches: list[tuple[int, int]] = []
    for lo, hi in _UNCACHED_GAP_RANGES:
        off = lo
        while off <= hi:
            length = min(25, hi - off + 1)
            batches.append((off, length))
            off += length
    return batches


def _screen_bytes(
    api,
    raw: bytes,
    meta: dict,
    used_shas: set[str],
    poly_priority: list[dict],
    curved_or_mixed: list[dict],
) -> bool:
    from PIL import Image

    sha = hashlib.sha256(raw).hexdigest()
    if sha in used_shas:
        return False
    with Image.open(io.BytesIO(raw)) as im:
        w, h = im.size
        api.SetImage(im.convert("RGB"))
        txt = api.GetUTF8Text() or ""
    if not _SOLID_KW_RE.search(txt):
        return True
    if _OXYZ_OR_CALC_KW_RE.search(txt):
        return True
    item = {
        **meta,
        "raw_bytes": raw,
        "sha256": sha,
        "bytes": len(raw),
        "width": w,
        "height": h,
    }
    if _POLY_KW_RE.search(txt):
        poly_priority.append({**item, "screen_bucket": "polyhedron_3d"})
    else:
        curved_or_mixed.append({**item, "screen_bucket": "curved_or_mixed_solid"})
    return True


def main() -> int:
    import tesserocr
    from tesserocr import PSM

    used_qids, used_shas, used_names = _collect_prior_used()

    local_by_qid: dict[str, Path] = {}
    for p in sorted(EXT_CACHE.rglob("*")):
        if not (p.is_file() and p.suffix.lower() in (".png", ".jpg", ".jpeg") and "Math_" in p.name):
            continue
        if DEST_CACHE in p.parents:
            continue
        qm = re.search(r"Math_(\d+)_test_(\d+)_question_(\d+)", p.name)
        if qm:
            local_by_qid.setdefault(qm.group(0), p)

    api = tesserocr.PyTessBaseAPI(path=str(TESSDATA), lang="vie", psm=PSM.AUTO)
    poly_priority: list[dict] = []
    curved_or_mixed: list[dict] = []
    seen_qids: set[str] = set()
    scanned_count = 0
    hf_rows_fetched = 0
    http_errors = 0

    # 1. Include the 3 known already-cached unused solid-geometry QIDs directly (0 HTTP calls).
    known_local_solid = {
        "Math_0113_test_019_question_44": 289,
        "Math_0362_test_070_question_45": 462,
        "Math_0391_test_079_question_38": 686,
    }
    for qid, approx_row in known_local_solid.items():
        lp = local_by_qid.get(qid)
        if lp is None or qid in used_qids or lp.name in used_names:
            continue
        seen_qids.add(qid)
        qm = re.search(r"Math_(\d+)_test_(\d+)_question_(\d+)", lp.name)
        pm = re.search(r"_page_(\d+)_", lp.name)
        dm = re.search(r"(Math_\d+_test_\d+_question_\d+.*)", lp.name)
        rm = re.match(r"r(\d+)_", lp.name)
        scanned_count += 1
        _screen_bytes(
            api,
            lp.read_bytes(),
            {
                "source_kind": "local_cache_unused",
                "row_idx": int(rm.group(1)) if rm else approx_row,
                "split": "full_vqa",
                "dataset_id": dm.group(1) if dm else lp.name,
                "qid": qid,
                "math_id": qm.group(1),
                "test_id": qm.group(2),
                "question_number": int(qm.group(3)),
                "page_number": int(pm.group(1)) if pm else None,
            },
            used_shas,
            poly_priority,
            curved_or_mixed,
        )
    print(
        f"Local unused pre-check: scanned={scanned_count} poly={len(poly_priority)} curved={len(curved_or_mixed)}",
        flush=True,
    )

    def _scan_split_batches(split: str, batches: list[tuple[int, int]]) -> None:
        nonlocal scanned_count, hf_rows_fetched, http_errors
        for off, length in batches:
            if len(poly_priority) >= 22:
                break
            url = (
                "https://datasets-server.huggingface.co/rows"
                f"?dataset=anvo25/vmmu&config=default&split={split}&offset={off}&length={length}"
            )
            try:
                data = json.loads(_http_get_bytes(url, timeout=25).decode("utf-8"))
            except Exception as exc:
                http_errors += 1
                print(f"WARN: skipped {split} offset={off} length={length} ({type(exc).__name__})", flush=True)
                continue
            rows = data.get("rows") or []
            hf_rows_fetched += len(rows)
            for entry in rows:
                if len(poly_priority) >= 22:
                    break
                r_idx = int(entry["row_idx"])
                row = entry.get("row") or {}
                if row.get("subject") != "Math":
                    continue
                ds_id = str(row.get("ID") or "")
                qm = re.search(r"Math_(\d+)_test_(\d+)_question_(\d+)", ds_id)
                if not qm:
                    continue
                qid = qm.group(0)
                if qid in used_qids or qid in seen_qids or qid in local_by_qid:
                    continue
                seen_qids.add(qid)
                src_url = (row.get("image") or {}).get("src") or ""
                if not src_url:
                    continue
                try:
                    raw = _http_get_bytes(src_url, timeout=25)
                except Exception as exc:
                    http_errors += 1
                    print(f"WARN: img fetch failed row={r_idx} ({type(exc).__name__})", flush=True)
                    continue
                pm = re.search(r"_page_(\d+)_", ds_id)
                scanned_count += 1
                _screen_bytes(
                    api,
                    raw,
                    {
                        "source_kind": f"hf_{split}_uncached",
                        "row_idx": r_idx,
                        "split": split,
                        "dataset_id": ds_id,
                        "qid": qid,
                        "math_id": qm.group(1),
                        "test_id": qm.group(2),
                        "question_number": int(qm.group(3)),
                        "page_number": int(pm.group(1)) if pm else None,
                    },
                    used_shas,
                    poly_priority,
                    curved_or_mixed,
                )
            print(
                f"Progress {split} off={off}: scanned={scanned_count} poly={len(poly_priority)} curved={len(curved_or_mixed)}",
                flush=True,
            )

    # 2. Scan uncached full_vqa Math gaps [240..695]
    _scan_split_batches("full_vqa", _iter_gap_offsets())

    # 3. Top up from random_subset_ocr [0..209] only if total < 20
    if len(poly_priority) + len(curved_or_mixed) < 20:
        _scan_split_batches("random_subset_ocr", [(off, min(25, 210 - off)) for off in range(0, 210, 25)])

    # Deterministic selection capped at 20 items: diverse test_id first, prioritizing polyhedron_3d.
    selected_raw: list[dict] = []
    used_tests: set[str] = set()
    for pool in (poly_priority, curved_or_mixed):
        for it in pool:
            if len(selected_raw) >= 20:
                break
            if it["test_id"] not in used_tests and it not in selected_raw:
                used_tests.add(it["test_id"])
                selected_raw.append(it)
        for it in pool:
            if len(selected_raw) >= 20:
                break
            if it not in selected_raw:
                selected_raw.append(it)

    DEST_CACHE.mkdir(parents=True, exist_ok=True)
    manifest_items = []
    for idx, it in enumerate(selected_raw, 1):
        out_name = f"r{it['row_idx']}_{it['dataset_id']}"
        out_file = DEST_CACHE / out_name
        out_file.write_bytes(it["raw_bytes"])
        rel_path = str(out_file.relative_to(ROOT)).replace("\\", "/")
        manifest_items.append({
            "case_id": f"unseen_vmmu_{idx:02d}",
            "dataset": "anvo25/vmmu",
            "split": it["split"],
            "hf_row_idx": it["row_idx"],
            "source_origin": it["source_kind"],
            "license_status": "MIT_DECLARED_BY_DATASET_PUBLISHER",
            "dataset_id": it["dataset_id"],
            "qid": it["qid"],
            "test_id": it["test_id"],
            "question_number": it["question_number"],
            "page_number": it["page_number"],
            "cache_path": rel_path,
            "sha256": it["sha256"],
            "file_size_bytes": it["bytes"],
            "image_width": it["width"],
            "image_height": it["height"],
            "screen_bucket": it["screen_bucket"],
            "partition": "frozen_unseen_vmmu20",
            "disjoint_from_all_prior_runs": True,
            "image_committed_to_git": False,
            "ground_truth_status": "GROUND_TRUTH_UNVERIFIED",
        })

    manifest = {
        "schema": "algosim-unseen-vmmu20-manifest/1",
        "run_id": "student-ready-geometry-simulation-input-reliability",
        "frozen_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": "FROZEN_BEFORE_ANY_TUNING_OR_FINAL_EVAL",
        "ground_truth_authority": "NONE_GROUND_TRUTH_UNVERIFIED",
        "independent_ground_truth_validation": "NOT_MEASURED",
        "sealed_h1_touched": False,
        "locked_w2_w3_touched": False,
        "pool_statistics": {
            "hf_rows_metadata_fetched": hf_rows_fetched,
            "images_scanned_for_solid_screening": scanned_count,
            "http_errors_skipped": http_errors,
            "screened_polyhedron_3d": len(poly_priority),
            "screened_curved_or_mixed": len(curved_or_mixed),
            "selected_count": len(manifest_items),
        },
        "items": manifest_items,
    }
    OUT_PATH.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("FROZEN:", OUT_PATH, flush=True)
    print("STATS:", json.dumps(manifest["pool_statistics"]), flush=True)
    for it in manifest_items:
        print(
            f"  {it['case_id']} row={it['hf_row_idx']} bucket={it['screen_bucket']} "
            f"test={it['test_id']} origin={it['source_origin']} sha={it['sha256'][:12]}",
            flush=True,
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
