# -*- coding: utf-8 -*-
"""Deterministic OCR, math-token, polygon, and Windows RSS scoring helpers for:
`ALGOSIM — REAL-WORLD GEOMETRY DATA ACQUISITION, HANDWRITTEN OCR & EVIDENCE RECONCILIATION`."""
from __future__ import annotations

import ctypes
from ctypes import wintypes
import math
import os
import re
from typing import Any

from app.ai.adaptive_input_router import extract_structured_math_tokens


def get_process_rss_mb() -> float:
    """Return current process WorkingSetSize in MiB on Windows (fallback 0.0 if unavailable)."""
    if os.name == "nt":
        class PROCESS_MEMORY_COUNTERS(ctypes.Structure):
            _fields_ = [
                ("cb", wintypes.DWORD),
                ("PageFaultCount", wintypes.DWORD),
                ("PeakWorkingSetSize", ctypes.c_size_t),
                ("WorkingSetSize", ctypes.c_size_t),
                ("QuotaPeakPagedPoolUsage", ctypes.c_size_t),
                ("QuotaPagedPoolUsage", ctypes.c_size_t),
                ("QuotaPeakNonPagedPoolUsage", ctypes.c_size_t),
                ("QuotaNonPagedPoolUsage", ctypes.c_size_t),
                ("PagefileUsage", ctypes.c_size_t),
                ("PeakPagefileUsage", ctypes.c_size_t),
            ]

        counters = PROCESS_MEMORY_COUNTERS()
        counters.cb = ctypes.sizeof(PROCESS_MEMORY_COUNTERS)
        k32 = ctypes.windll.kernel32
        k32.GetCurrentProcess.restype = ctypes.c_void_p
        psapi = ctypes.windll.psapi
        psapi.GetProcessMemoryInfo.argtypes = [ctypes.c_void_p, ctypes.c_void_p, wintypes.DWORD]
        psapi.GetProcessMemoryInfo.restype = wintypes.BOOL
        handle = k32.GetCurrentProcess()
        ok = psapi.GetProcessMemoryInfo(
            handle, ctypes.byref(counters), counters.cb
        )
        if ok:
            return round(counters.WorkingSetSize / (1024.0 * 1024.0), 2)
    return 0.0


def levenshtein_distance(seq_a: list[Any] | str, seq_b: list[Any] | str) -> int:
    if seq_a == seq_b:
        return 0
    la, lb = len(seq_a), len(seq_b)
    if la == 0:
        return lb
    if lb == 0:
        return la
    prev = list(range(lb + 1))
    for i, ca in enumerate(seq_a, start=1):
        curr = [i] + [0] * lb
        for j, cb in enumerate(seq_b, start=1):
            cost = 0 if ca == cb else 1
            curr[j] = min(curr[j - 1] + 1, prev[j] + 1, prev[j - 1] + cost)
        prev = curr
    return prev[lb]


def normalize_ws(text: str) -> str:
    return re.sub(r"\s+", " ", (text or "").strip())


def compute_cer_wer(pred: str, gt: str) -> dict[str, float]:
    gt_norm = normalize_ws(gt)
    pred_norm = normalize_ws(pred)
    if not gt_norm:
        empty_ok = 0.0 if not pred_norm else 1.0
        return {
            "cer": empty_ok,
            "wer": empty_ok,
            "vietnamese_word_accuracy": round(1.0 - empty_ok, 4),
        }
    c_dist = levenshtein_distance(pred_norm, gt_norm)
    cer = round(c_dist / max(1, len(gt_norm)), 4)

    gt_words = gt_norm.split(" ")
    pred_words = pred_norm.split(" ")
    w_dist = levenshtein_distance(pred_words, gt_words)
    wer = round(w_dist / max(1, len(gt_words)), 4)
    vn_word_acc = round(max(0.0, 1.0 - wer), 4)
    return {
        "cer": cer,
        "wer": wer,
        "vietnamese_word_accuracy": vn_word_acc,
    }


_PRIME_TOKEN_RE = re.compile(r"\b[A-Z]'")
_POINT_LABEL_RE = re.compile(r"(?<![A-Za-z])[A-Z]'?(?![a-z])")
_FRACTION_RE = re.compile(r"(?:[0-9a-zA-Z√]+\s*/\s*[0-9a-zA-Z√]+)")


def _f1_or_exact(gt_set: set[str], pred_set: set[str]) -> dict[str, Any]:
    if not gt_set:
        return {
            "gt_count": 0,
            "pred_count": len(pred_set),
            "matched_count": 0,
            "recall": None,
            "exact_match": len(pred_set) == 0,
            "gt_tokens": [],
            "pred_tokens": sorted(pred_set),
        }
    matched = gt_set & pred_set
    return {
        "gt_count": len(gt_set),
        "pred_count": len(pred_set),
        "matched_count": len(matched),
        "recall": round(len(matched) / len(gt_set), 4),
        "exact_match": gt_set == pred_set,
        "gt_tokens": sorted(gt_set),
        "pred_tokens": sorted(pred_set),
    }


def score_math_tokens(pred: str, gt: str) -> dict[str, Any]:
    """Score math symbol preservation across all 7 categories required by Section VI.3.2."""
    gt_tok = extract_structured_math_tokens(gt or "")
    pr_tok = extract_structured_math_tokens(pred or "")

    gt_norm = (gt or "").replace("′", "'").replace("’", "'")
    pr_norm = (pred or "").replace("′", "'").replace("’", "'")

    gt_primes = set(_PRIME_TOKEN_RE.findall(gt_norm))
    pr_primes = set(_PRIME_TOKEN_RE.findall(pr_norm))

    gt_rads = set(gt_tok["radicals"])
    pr_rads = set(pr_tok["radicals"])

    gt_fracs = {re.sub(r"\s+", "", m) for m in _FRACTION_RE.findall(gt_norm)}
    pr_fracs = {re.sub(r"\s+", "", m) for m in _FRACTION_RE.findall(pr_norm)}

    gt_assign = {f"{k}={v}" for k, v in gt_tok["assignments"].items()} | set(gt_tok["angles_degrees"])
    pr_assign = {f"{k}={v}" for k, v in pr_tok["assignments"].items()} | set(pr_tok["angles_degrees"])

    gt_points = set(_POINT_LABEL_RE.findall(gt_norm))
    pr_points = set(_POINT_LABEL_RE.findall(pr_norm))

    gt_planes = set(gt_tok["planes"])
    pr_planes = set(pr_tok["planes"])

    gt_solids = set(gt_tok["solids"])
    pr_solids = set(pr_tok["solids"])

    gt_rels = set(gt_tok["relations"])
    pr_rels = set(pr_tok["relations"])

    all_gt = (
        {f"solid:{x}" for x in gt_solids}
        | {f"plane:{x}" for x in gt_planes}
        | {f"prime:{x}" for x in gt_primes}
        | {f"rad:{x}" for x in gt_rads}
        | {f"frac:{x}" for x in gt_fracs}
        | {f"assign:{x}" for x in gt_assign}
        | {f"rel:{x}" for x in gt_rels}
    )
    all_pr = (
        {f"solid:{x}" for x in pr_solids}
        | {f"plane:{x}" for x in pr_planes}
        | {f"prime:{x}" for x in pr_primes}
        | {f"rad:{x}" for x in pr_rads}
        | {f"frac:{x}" for x in pr_fracs}
        | {f"assign:{x}" for x in pr_assign}
        | {f"rel:{x}" for x in pr_rels}
    )

    has_solid_opener = bool(
        re.search(
            r"(?i)\b(?:cho|xét)\s+(?:hình|khối|tứ\s+diện|mặt\s+cầu|hình\s+nón|hình\s+trụ)",
            pr_norm,
        )
    )
    has_question = bool(
        re.search(
            r"(?i)(?:\btính\b|\btìm\b|\bxác\s+định\b|\bchứng\s+minh\b|\bbằng\s+bao\s+nhiêu\b|\bđã\s+cho\s+bằng\b|\?)",
            pr_norm,
        )
    )

    overall = _f1_or_exact(all_gt, all_pr)
    any_symbol_corruption = not overall["exact_match"]

    return {
        "overall_math_tokens": overall,
        "prime_notation": _f1_or_exact(gt_primes, pr_primes),
        "radicals": _f1_or_exact(gt_rads, pr_rads),
        "fractions": _f1_or_exact(gt_fracs, pr_fracs),
        "numeric_assignments": _f1_or_exact(gt_assign, pr_assign),
        "point_labels": _f1_or_exact(gt_points, pr_points),
        "plane_notation": _f1_or_exact(gt_planes, pr_planes),
        "solids": _f1_or_exact(gt_solids, pr_solids),
        "relations": _f1_or_exact(gt_rels, pr_rels),
        "problem_completeness": {
            "has_opener": has_solid_opener,
            "has_question": has_question,
            "complete_structure_preserved": has_solid_opener and has_question,
        },
        "has_math_symbol_error": any_symbol_corruption,
    }


def eval_exact_coord(expr: Any) -> float:
    if isinstance(expr, (int, float)):
        return float(expr)
    s = str(expr).strip()
    if "/" in s and "sqrt" not in s and "√" not in s:
        n, d = s.split("/", 1)
        return float(n) / float(d)
    s_py = re.sub(r"√(\d+)", r"math.sqrt(\1)", s)
    s_py = s_py.replace("sqrt(", "math.sqrt(")
    return float(eval(s_py, {"__builtins__": {}, "math": math}))


def polygon_3d_coplanar_and_convex(pts: list[tuple[float, float, float]]) -> bool:
    if len(pts) < 3:
        return False
    p0, p1, p2 = pts[0], pts[1], pts[2]
    u = (p1[0] - p0[0], p1[1] - p0[1], p1[2] - p0[2])
    v = (p2[0] - p0[0], p2[1] - p0[1], p2[2] - p0[2])
    nx = u[1] * v[2] - u[2] * v[1]
    ny = u[2] * v[0] - u[0] * v[2]
    nz = u[0] * v[1] - u[1] * v[0]
    norm = math.sqrt(nx * nx + ny * ny + nz * nz)
    if norm < 1e-8:
        return False
    normal = (nx / norm, ny / norm, nz / norm)
    for p in pts[3:]:
        w = (p[0] - p0[0], p[1] - p0[1], p[2] - p0[2])
        if abs(w[0] * normal[0] + w[1] * normal[1] + w[2] * normal[2]) > 1e-5:
            return False
    signs: list[int] = []
    m = len(pts)
    for i in range(m):
        a, b, c = pts[i], pts[(i + 1) % m], pts[(i + 2) % m]
        e1 = (b[0] - a[0], b[1] - a[1], b[2] - a[2])
        e2 = (c[0] - b[0], c[1] - b[1], c[2] - b[2])
        cx = e1[1] * e2[2] - e1[2] * e2[1]
        cy = e1[2] * e2[0] - e1[0] * e2[2]
        cz = e1[0] * e2[1] - e1[1] * e2[0]
        dot_n = cx * normal[0] + cy * normal[1] + cz * normal[2]
        if abs(dot_n) > 1e-6:
            signs.append(1 if dot_n > 0 else -1)
    return bool(signs) and len(set(signs)) == 1
