# -*- coding: utf-8 -*-
"""End-to-End Campaign Offline Evaluator (`real-world-geometry-input-verified-simulation`).

Strictly offline (`ALLOW_LIVE_AI=0`, `GEMINI_API_KEY=""`, 0 live Gemini/Vision API calls).
Never reads sealed `H-1` or locked `W2`/`W3`, and never edits `axo-geometry-library`.

Measures:
  1. Locked extraction surfaces (4 SHA-256 fingerprints) + cache version `144`.
  2. Stream B (Real-World Image -> OCR -> Confirmation/Selection -> Grounding -> Kernel -> Scene3D):
     - `glyph_topology` (12/12 via real sidecar worker: superscript, radical, perp, parallel, equals vs minus)
     - `rendered_positive` (4/4 LOCAL_OCR_ACCEPT + exact served answer)
     - `adversarial_negative` (3/3 LOCAL_OCR_REVIEW_REQUIRED, 0 false auto-accepts)
     - `real27_images` (27 cached images split by development vs frozen/fresh external; before/after CER,
       blocking spans, zero-text spans, critical-fact preservation, safe auto-accept vs review, 0 false
       auto-accepts, simulated minimal confirmation + effort + provenance contract + Scene3D continuity,
       and cold vs warm stage-by-stage p50/p95 latencies inside ONE asyncio event loop)
     - `external16_images` (15 printed + 1 handwritten reported separately, plus multi-problem band
       selection/switching on `ext_prt_03` and `ext_prt_08`)
     - `untouched_external_image_sets` reported separately: `new_external_12` and `new_image_corpus_8`
       (split development [2] vs frozen_external_evaluation [6])
     - Deterministic offline Vision-fallback mock + edited confirmation cache/provenance separation
  3. Stream A & C (Understanding, Autonomous Planning, Source Gate, Scene3D, Mode A):
     - `REAL27_TEXT` (27) with full 9-refusal & 3-adjudication forensics (`vmmu_r513` Source Gate fix)
     - `NC-*` (21/21 Gold & NL + 11/11 neg), `A4` & depth (6/6), `reasoning_matrix` (72 + MG9), `r1_probe` (19)
     - `DEV37` (37), `COMP112` (112), `PROBES39` (39), `Scene3D` continuity (0 errors), Mode A (`0` leaks)
"""
from __future__ import annotations

import argparse
import asyncio
import base64
from collections import Counter
from datetime import datetime, timezone
import hashlib
import io
import json
import os
from pathlib import Path
import re
import socket
import statistics
import subprocess
import sys
import time
from typing import Any

RUN_DIR = Path(__file__).resolve().parents[1]
RUNS_DIR = RUN_DIR.parent
ROOT = RUN_DIR.parents[4]
BACKEND = ROOT / "backend"

for _p in (
    BACKEND,
    BACKEND / "scripts",
    BACKEND / "tests" / "geometry",
    RUNS_DIR / "unified-geometry-understanding-ocr-autonomous-planning" / "tools",
    RUNS_DIR / "planner-autonomous-composition-and-search-efficiency" / "tools",
    RUNS_DIR / "hybrid-reasoning-generalization" / "tools",
    RUNS_DIR / "semantic-failure-safe-image-segmentation" / "tools",
    RUNS_DIR / "dimension-aware-verified-construction" / "tools",
    RUNS_DIR / "independent-geometry-plane-constraints" / "tools",
    RUNS_DIR / "controlled-vision-real-image-validation" / "tools",
    RUNS_DIR / "image-first-ocr-verified-geometry" / "tools",
    RUNS_DIR / "real-world-printed-handwriting-acquisition" / "tools",
    RUNS_DIR / "real-image-ocr-vision-comparative-acceptance" / "tools",
):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

os.environ["ALLOW_LIVE_AI"] = "0"
os.environ["GEMINI_API_KEY"] = ""
os.environ.pop("HYBRID_ROUTE_MODE", None)
os.environ.pop("LOCAL_OCR_PYTHON", None)
os.environ.pop("LOCAL_OCR_TESSDATA", None)

import check_publication_safety as pub_safety  # noqa: E402
import evaluate_autonomous_composition as EAC  # noqa: E402
import evaluate_image_first_ocr as EIFO  # noqa: E402
import evaluate_images as EVI  # noqa: E402
import evaluate_unified_campaign as EUC  # noqa: E402
import freeze_evaluation_candidate as FZ  # noqa: E402
import new_external_catalog as NEC  # noqa: E402
from build_corpus import fact_norm  # noqa: E402
from corpus_catalog import CORPUS_ITEMS  # noqa: E402
from ocr_scoring_helpers import compute_cer_wer  # noqa: E402

# EIFO calls os.environ.setdefault("LOCAL_OCR_PYTHON", ...) at import time; enforce clean default state here.
os.environ["ALLOW_LIVE_AI"] = "0"
os.environ["GEMINI_API_KEY"] = ""
os.environ.pop("HYBRID_ROUTE_MODE", None)
os.environ.pop("LOCAL_OCR_PYTHON", None)
os.environ.pop("LOCAL_OCR_TESSDATA", None)

from app.ai import adaptive_input_router as AIR  # noqa: E402
from app.ai.adapter4_route import run_typed_fact_next_v2_route  # noqa: E402
from app.ai.hybrid_offline import prepare_local_first_hybrid, resolve_hybrid_gemini_model  # noqa: E402
from app.ai.local_geometry_parser import (  # noqa: E402
    LOCAL_PARSE_COMPLETE,
    clear_local_geometry_parser_cache,
    parse_geometry_problem_locally,
)
from app.ingestion import local_ocr as LO  # noqa: E402
from app.ingestion import local_ocr_route as LR  # noqa: E402
from app.ingestion import ocr_reconcile as OR  # noqa: E402
from app.ingestion.image import normalize_image  # noqa: E402
from app.ingestion.region_detector import detect_problem_regions  # noqa: E402
from app.ingestion.unified_input import prepare_unified_input  # noqa: E402
from app.main import (  # noqa: E402
    CACHE_VERSION,
    ROUTE_D_CACHE_POLICY,
    InputSourceProvenance,
    build_verified_input_provenance,
)
from app.runtime_identity import runtime_identity, semantic_environment_hash  # noqa: E402
from app.simulation.geometry_functions.construction_continuity import (  # noqa: E402
    validate_construction_continuity,
)


def _git_head() -> str:
    return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()


def _percentile(vals: list[float], p: float) -> float:
    return EUC._percentile(vals, p)


def _stats(vals: list[float]) -> dict[str, Any]:
    clean = [round(float(v), 2) for v in vals if v is not None]
    if not clean:
        return {"n": 0, "p50": None, "p95": None, "mean": None}
    return {
        "n": len(clean),
        "p50": round(float(statistics.median(clean)), 2),
        "p95": _percentile(clean, 0.95),
        "mean": round(sum(clean) / len(clean), 2),
    }


def _continuity_count(env: dict[str, Any] | None) -> int:
    sc = (env or {}).get("scene3d")
    if not sc:
        return 0
    return len(validate_construction_continuity(sc))


def _mime_and_name(raw_b: bytes, p: Path) -> tuple[str, str]:
    if raw_b.startswith(b"\x89PNG\r\n\x1a\n"):
        return "image/png", p.with_suffix(".png").name
    if raw_b.startswith(b"\xff\xd8\xff"):
        return "image/jpeg", p.with_suffix(".jpg").name
    if raw_b.startswith(b"RIFF") and b"WEBP" in raw_b[:16]:
        return "image/webp", p.with_suffix(".webp").name
    return ("image/jpeg" if p.suffix.lower() in (".jpg", ".jpeg") else "image/png"), p.name


def _critical_fact_stats(text: str, *, critical_facts: list[dict[str, Any]] | None = None, fact_texts: list[str] | None = None) -> dict[str, Any]:
    norm_txt = fact_norm(text or "")
    if critical_facts is not None:
        rows = [
            {
                "kind": f["kind"],
                "reference": f["accepted_forms"][0],
                "recovered": any(fact_norm(form) in norm_txt for form in f["accepted_forms"]),
            }
            for f in critical_facts
        ]
        rec = sum(1 for r in rows if r["recovered"])
        return {"recovered": rec, "total": len(rows), "all_recovered": rec == len(rows), "items": rows}
    if fact_texts is not None:
        rows = [{"reference": t, "recovered": fact_norm(t) in norm_txt} for t in fact_texts]
        rec = sum(1 for r in rows if r["recovered"])
        return {"recovered": rec, "total": len(rows), "all_recovered": rec == len(rows), "items": rows}
    return {"recovered": 0, "total": 0, "all_recovered": True, "items": []}


def _critical_math_token_prf(hyp: str, ref: str) -> dict[str, Any]:
    return EIFO._prf(EIFO._math_tokens(hyp or ""), EIFO._math_tokens(ref or ""))


def _load_baselines() -> dict[str, Any]:
    prior_eval_p = RUNS_DIR / "unified-geometry-understanding-ocr-autonomous-planning" / "END_TO_END_CAPABILITY_EVALUATION.json"
    prior_eval = json.loads(prior_eval_p.read_text(encoding="utf-8"))
    ext16_p = RUNS_DIR / "image-first-ocr-verified-geometry" / "external16_image_diagnostics.json"
    ext16_diag = json.loads(ext16_p.read_text(encoding="utf-8"))
    dump_p = ROOT / ".superpowers" / "offline-logs" / "real_world_ocr_forensic_dump.json"
    dump = json.loads(dump_p.read_text(encoding="utf-8")) if dump_p.exists() else {}

    real27_prior_rows = {
        r["case_id"]: r for r in (prior_eval.get("stream_b", {}).get("real27_images", {}).get("rows") or [])
    }
    ext16_prior_rows = {c["image_id"]: c for c in ext16_diag.get("cases") or []}
    dump_real27 = {r["id"]: r for r in dump.get("real27") or []}
    dump_ext15 = {r["id"]: r for r in dump.get("ext15") or []}
    return {
        "prior_eval_meta": {
            "run_id": prior_eval.get("run_id"),
            "product_commit": prior_eval.get("product_commit"),
            "ocr_reconcile_version": prior_eval.get("stream_b", {}).get("ocr_reconcile_version"),
        },
        "real27_summary": {
            k: v
            for k, v in (prior_eval.get("stream_b", {}).get("real27_images") or {}).items()
            if k != "rows"
        },
        "ext15_summary": {
            k: v
            for k, v in (prior_eval.get("stream_b", {}).get("external16_printed_images") or {}).items()
            if k != "rows"
        },
        "real27_prior_rows": real27_prior_rows,
        "ext16_prior_rows": ext16_prior_rows,
        "dump_real27": dump_real27,
        "dump_ext15": dump_ext15,
    }


def _install_windows_socketpair_guard() -> None:
    if sys.platform != "win32":
        return
    _orig = getattr(socket, "socketpair", None)

    def _safe_socketpair(family=socket.AF_INET, type=socket.SOCK_STREAM, proto=0):
        for port in range(30000, 48000):
            lsock = socket.socket(family, type, proto)
            lsock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            try:
                lsock.bind(("127.0.0.1", port))
                lsock.listen(1)
                csock = socket.socket(family, type, proto)
                csock.connect(("127.0.0.1", port))
                ssock, _ = lsock.accept()
                lsock.close()
                return ssock, csock
            except OSError:
                lsock.close()
                continue
        if _orig:
            return _orig(family, type, proto)
        raise OSError("No available port found for socketpair")

    socket.socketpair = _safe_socketpair


def _build_gold_real27_refusal_probes(rmap: dict[str, dict[str, Any]]) -> dict[str, dict[str, Any]]:
    """Chạy Gold `TypedFactNext /2` -> `run_typed_fact_next_v2_route` tách biệt Parser vs Kernel/Source Gate trên các ca từ chối `REAL27`."""
    probes: dict[str, dict[str, Any]] = {}

    def _run(pl: dict[str, Any] | None) -> dict[str, Any]:
        if not pl:
            return {"status": "NO_GOLD_PAYLOAD", "code": None, "answers": None, "detail": None}
        r = run_typed_fact_next_v2_route(pl)
        rd = r.route_d or {}
        return {
            "status": r.status,
            "code": r.code,
            "answers": rd.get("answers") or None,
            "detail": (rd.get("refusal") or {}).get("detail"),
        }

    # 1. r254 (frozen_external_evaluation): oblique prism centroid-foot + sub-tetrahedron
    t254 = rmap["vmmu_r254"]["statement"]
    p254 = {
        "schema_version": "typed-fact-next/2",
        "problem_text": t254,
        "length_unit": "a",
        "solids": [{"solid_id": "s1", "solid_type": "prism", "notation": "ABC.A'B'C'", "quote": "Cho hình lăng trụ ABC.A'B'C'"}],
        "described_points": [{"described_id": "g1", "kind": "centroid", "polygon": ["A", "B", "C"], "quote": "trọng tâm của tam giác ABC"}],
        "premises": [
            {"kind": "segment_length", "args": {"segment": ["A", "A'"], "value": "2a√13"}, "quote": "AA' = 2√13a", "solid_id": "s1"},
            {"kind": "right_angle", "args": {"vertex": "C", "rays": ["A", "B"]}, "quote": "tam giác ABC vuông tại C", "solid_id": "s1"},
            {"kind": "vertex_angle", "args": {"vertex": "B", "rays": ["A", "C"], "value": "30", "unit": "deg"}, "quote": "∠ABC = 30°", "solid_id": "s1"},
            {"kind": "line_plane_angle", "args": {"line": ["C", "C'"], "plane": ["A", "B", "C"], "value": "60", "unit": "deg"}, "quote": "góc giữa cạnh bên CC' và mặt đáy (ABC) bằng 60°", "solid_id": "s1"},
            {"kind": "orthogonal_projection", "args": {"point": "B'", "image": "@g1", "plane": ["A", "B", "C"]}, "quote": "Hình chiếu vuông góc của B' lên mặt phẳng (ABC) trùng với trọng tâm của tam giác ABC", "solid_id": "s1"},
        ],
        "simulation_goals": [{"goal_id": "sg1", "kind": "construct_object", "target_solid_id": "s1", "quote": "Cho hình lăng trụ ABC.A'B'C'"}],
        "math_goals": [{"goal_id": "q1", "kind": "measurement", "goal_type": "volume", "target": {"solid_id": "s1"}, "solid_id": "s1", "quote": "Thể tích của khối tứ diện A'ABC theo a bằng"}],
    }
    probes["vmmu_r254"] = {
        "primary_category": "TYPED_FACT_GAP",
        "secondary_categories": ["UNDERSTANDING_GAP", "REGISTRY_GAP", "KERNEL_EXACT_DOMAIN_GAP"],
        "gold_result": _run(p254),
        "note": "TypedFactNext /2 không nhận @id làm operand của premise (INVALID_DESCRIBED_POINT); đề đồng thời hỏi thể tích khối tứ diện con A'ABC và cho góc 30° trên tam giác đáy không vuông cân.",
    }

    # 2. r256 (frozen_external_evaluation): source typo 'đên' vs 'đến'
    t256 = rmap["vmmu_r256"]["statement"]
    p256_verb = {
        "schema_version": "typed-fact-next/2",
        "problem_text": t256,
        "length_unit": "a",
        "solids": [{"solid_id": "s1", "solid_type": "pyramid", "notation": "S.ABCD", "quote": "Cho hình chóp S.ABCD"}],
        "premises": [
            {"kind": "rhombus", "args": {"vertices": ["A", "B", "C", "D"], "side": "a"}, "quote": "đáy ABCD là hình thoi cạnh bằng a", "solid_id": "s1"},
            {"kind": "vertex_angle", "args": {"vertex": "A", "rays": ["B", "D"], "value": "120", "unit": "deg"}, "quote": "∠BAD = 120°", "solid_id": "s1"},
            {"kind": "regular_polygon", "args": {"vertices": ["S", "A", "B"]}, "quote": "Mặt bên SAB là tam giác đều", "solid_id": "s1"},
            {"kind": "face_perpendicular_base", "args": {"face": ["S", "A", "B"], "base": ["A", "B", "C", "D"]}, "quote": "(SAB) ⊥ (ABCD)", "solid_id": "s1"},
        ],
        "simulation_goals": [{"goal_id": "sg1", "kind": "construct_object", "target_solid_id": "s1", "quote": "Cho hình chóp S.ABCD"}],
        "math_goals": [{"goal_id": "q1", "kind": "measurement", "goal_type": "distance", "target": {"point": "A", "plane": ["S", "B", "C"]}, "solid_id": "s1", "quote": "Tính khoảng cách từ A đên (SBC)"}],
    }
    p256_canon = parse_geometry_problem_locally(t256.replace("đên", "đến")).payload
    probes["vmmu_r256"] = {
        "primary_category": "SOURCE_GROUNDING_GAP",
        "secondary_categories": ["UNDERSTANDING_GAP"],
        "gold_result": _run(p256_verb),
        "gold_typo_fixed_counterfactual": _run(p256_canon),
        "note": "Lỗi chính tả nguyên bản trong ảnh đề ('đên' thay 'đến'); giữ fail-closed ở Source Gate (SOURCE_OBJECT_MISMATCH) theo §4.4; nếu sửa chính tả thành 'đến' thì phục vụ đúng a√15/5.",
    }

    # 3. r266 (frozen_external_evaluation): Local Parser == Gold, Kernel refuses EXACT_DOMAIN_EXCEEDED
    p266 = parse_geometry_problem_locally(rmap["vmmu_r266"]["statement"]).payload
    probes["vmmu_r266"] = {
        "primary_category": "KERNEL_EXACT_DOMAIN_GAP",
        "secondary_categories": [],
        "gold_result": _run(p266),
        "note": "Parser cục bộ đạt LOCAL_PARSE_COMPLETE khớp 100% Gold; Exact Kernel từ chối EXACT_DOMAIN_EXCEEDED (căn lồng từ cos 30° + định lý cos ngoài miền Gram hữu tỉ Q).",
    }

    # 4. r277 (frozen_external_evaluation): point_reflection + OMNP sub-tetrahedron
    t277 = rmap["vmmu_r277"]["statement"]
    p277 = {
        "schema_version": "typed-fact-next/2",
        "problem_text": t277,
        "length_unit": "a",
        "solids": [
            {"solid_id": "s1", "solid_type": "pyramid", "notation": "O.ABC", "quote": "Cho tứ diện OABC"},
            {"solid_id": "s2", "solid_type": "pyramid", "notation": "O.MNP", "quote": "tứ diện OMNP"},
        ],
        "premises": [
            {"kind": "right_angle", "args": {"vertex": "O", "rays": ["A", "B"]}, "quote": "Cho tứ diện OABC vuông tại O", "solid_id": "s1"},
            {"kind": "right_angle", "args": {"vertex": "O", "rays": ["B", "C"]}, "quote": "Cho tứ diện OABC vuông tại O", "solid_id": "s1"},
            {"kind": "right_angle", "args": {"vertex": "O", "rays": ["A", "C"]}, "quote": "Cho tứ diện OABC vuông tại O", "solid_id": "s1"},
            {"kind": "segment_length", "args": {"segment": ["O", "A"], "value": "2a"}, "quote": "OA = 2a", "solid_id": "s1"},
            {"kind": "segment_length", "args": {"segment": ["O", "B"], "value": "3a"}, "quote": "OB = 3a", "solid_id": "s1"},
            {"kind": "segment_length", "args": {"segment": ["O", "C"], "value": "4a"}, "quote": "OC = 4a", "solid_id": "s1"},
            {"kind": "point_reflection", "args": {"point": "M", "center": "D", "source": "O"}, "quote": "M, N, P lần lượt là điểm đối xứng với điểm O qua trung điểm ba cạnh AB, BC, CA của tam giác ABC", "solid_id": "s1"},
        ],
        "simulation_goals": [{"goal_id": "sg1", "kind": "construct_object", "target_solid_id": "s1", "quote": "Cho tứ diện OABC"}],
        "math_goals": [{"goal_id": "q1", "kind": "measurement", "goal_type": "volume", "target": {"solid_id": "s2"}, "solid_id": "s2", "quote": "Thể tích của tứ diện OMNP bằng"}],
    }
    probes["vmmu_r277"] = {
        "primary_category": "TYPED_FACT_GAP",
        "secondary_categories": ["REGISTRY_GAP", "UNDERSTANDING_GAP"],
        "gold_result": _run(p277),
        "note": "Thiếu primitive/bridge cho phép đối xứng điểm qua trung điểm (point_reflection -> BRIDGE_UNSUPPORTED_PREMISE) và dựng khối tứ diện OMNP mới trên 3 đỉnh phản xạ.",
    }

    # 5. r461 (development): paper cone from circular sector
    probes["vmmu_r461"] = {
        "primary_category": "INTENTIONALLY_UNSUPPORTED",
        "secondary_categories": ["UNDERSTANDING_GAP"],
        "gold_result": {"status": "OUT_OF_SCOPE", "code": "CURVED_ROLLED_SECTOR_OUT_OF_SCOPE", "answers": None, "detail": "Quạt tròn gấp thành hình nón nằm ngoài phạm vi đa diện/lăng trụ thuần xác minh."},
        "note": "Bài toán ứng dụng gấp quạt tròn thành hình nón — chủ đích giữ ngoài phạm vi hỗ trợ (fail-closed).",
    }

    # 6. r475 (frozen_external_evaluation): cylinder + sphere + cone Archimedes displacement
    probes["vmmu_r475"] = {
        "primary_category": "INTENTIONALLY_UNSUPPORTED",
        "secondary_categories": [],
        "gold_result": {"status": "OUT_OF_SCOPE", "code": "MULTI_CURVED_FLUID_DISPLACEMENT_OUT_OF_SCOPE", "answers": None, "detail": "Bài toán nhiều khối cong lồng nhau + tỉ số thể tích nước tràn ngoài phạm vi."},
        "note": "Tổ hợp cốc trụ + bi cầu + khối nón + tràn nước — chủ đích giữ ngoài phạm vi (fail-closed).",
    }

    # 7. r488 (development): right prism + sub-pyramid B'.ACC'A'
    t488 = rmap["vmmu_r488"]["statement"]
    p488_host = parse_geometry_problem_locally(
        "Cho hình lăng trụ đứng ABC.A'B'C' có đáy ABC là tam giác vuông tại B, AB = BC = a. "
        "Biết góc giữa hai mặt phẳng (ACC') và (AB'C') bằng 60°. Thể tích của khối lăng trụ ABC.A'B'C' bằng"
    ).payload
    p488_two = {
        "schema_version": "typed-fact-next/2",
        "problem_text": t488,
        "length_unit": "a",
        "solids": [
            {"solid_id": "s1", "solid_type": "prism", "notation": "ABC.A'B'C'", "quote": "Cho hình lăng trụ đứng ABC.A'B'C'"},
            {"solid_id": "s2", "solid_type": "pyramid", "notation": "B'.ACC'A'", "quote": "khối chóp B'.ACC'A'"},
        ],
        "premises": list((p488_host or {}).get("premises") or []),
        "simulation_goals": [{"goal_id": "sg1", "kind": "construct_object", "target_solid_id": "s1", "quote": "Cho hình lăng trụ đứng ABC.A'B'C'"}],
        "math_goals": [{"goal_id": "q1", "kind": "measurement", "goal_type": "volume", "target": {"solid_id": "s2"}, "solid_id": "s2", "quote": "Thể tích của khối chóp B'.ACC'A' bằng"}],
    }
    # Fix quotes to match exact t488 text for fair gate check
    p488_two["premises"][1] = {"kind": "right_angle", "args": {"vertex": "B", "rays": ["A", "C"]}, "quote": "đáy ABC là tam giác vuông, AB = BC = a", "solid_id": "s1"}
    p488_two["premises"][4] = {"kind": "plane_plane_angle", "args": {"plane1": ["A", "C", "C'"], "plane2": ["A", "B'", "C'"], "value": "60", "unit": "deg"}, "quote": "Biết góc giữa hai mặt phẳng (ACC') và (AB'C') bằng 60°", "solid_id": "s1"}
    probes["vmmu_r488"] = {
        "primary_category": "REGISTRY_GAP",
        "secondary_categories": ["KERNEL_EXACT_DOMAIN_GAP", "UNDERSTANDING_GAP"],
        "gold_result": _run(p488_two),
        "gold_host_prism_counterfactual": _run(p488_host),
        "note": "Parser cần suy ra đỉnh vuông B từ 'tam giác vuông, AB = BC = a'; dù có Gold TypedFactNext cho lăng trụ (lăng trụ đơn phục vụ đúng a³/2, suy ra V(B'.ACC'A') = a³/3), Engine/Registry chưa hỗ trợ đo thể tích khối chóp con tách từ lăng trụ (UNSUPPORTED_MULTIPLE_BASES / SOURCE_OBJECT_MISMATCH).",
    }

    # 8. r491 (frozen_external_evaluation): unparameterized point_on_segment locus I ∈ BC without AA' length
    t491 = rmap["vmmu_r491"]["statement"]
    p491 = {
        "schema_version": "typed-fact-next/2",
        "problem_text": t491,
        "length_unit": "a",
        "solids": [{"solid_id": "s1", "solid_type": "prism", "notation": "ABC.A'B'C'", "quote": "Cho hình lăng trụ ABC.A'B'C'"}],
        "premises": [
            {"kind": "right_angle", "args": {"vertex": "A", "rays": ["B", "C"]}, "quote": "đáy ABC là tam giác vuông tại A", "solid_id": "s1"},
            {"kind": "segment_length", "args": {"segment": ["A", "B"], "value": "a"}, "quote": "AB = a", "solid_id": "s1"},
            {"kind": "segment_length", "args": {"segment": ["A", "C"], "value": "2a"}, "quote": "AC = 2a", "solid_id": "s1"},
            {"kind": "orthogonal_projection", "args": {"point": "A'", "image": "I", "plane": ["A", "B", "C"]}, "quote": "Hình chiếu vuông góc của A' lên mặt phẳng (ABC) là điểm I", "solid_id": "s1"},
        ],
        "simulation_goals": [{"goal_id": "sg1", "kind": "construct_object", "target_solid_id": "s1", "quote": "Cho hình lăng trụ ABC.A'B'C'"}],
        "math_goals": [{"goal_id": "q1", "kind": "measurement", "goal_type": "distance", "target": {"point": "A", "plane": ["A'", "B", "C"]}, "solid_id": "s1", "quote": "Khoảng cách từ A tới mặt phẳng (A'BC) bằng"}],
    }
    probes["vmmu_r491"] = {
        "primary_category": "TYPED_FACT_GAP",
        "secondary_categories": ["INSUFFICIENT_SPECIFICATION", "UNDERSTANDING_GAP"],
        "gold_result": _run(p491),
        "note": "Thiếu primitive/fact cho điểm trượt tự do 'I thuộc cạnh BC' không gắn tỉ số và thiếu độ dài AA' (chỉ giải được bằng bất biến quỹ tích (A'BC) ⊥ (ABC) => d(A,(A'BC)) = d(A,BC)).",
    }

    # 9. r513 (development): Local Parser == Gold -> MISSING_DIMENSION + UNPROVED_DUE_TO_CAPABILITY_GAP
    p513 = parse_geometry_problem_locally(rmap["vmmu_r513"]["statement"]).payload
    probes["vmmu_r513"] = {
        "primary_category": "INSUFFICIENT_SPECIFICATION",
        "secondary_categories": [],
        "gold_result": _run(p513),
        "note": "Nguồn thiếu cạnh BC/AD của hình hộp chữ nhật; _cac_moc_cau căn gióng Source Gate giúp Local Parser và Gold đồng nhất trả REFUSED MISSING_DIMENSION (UNPROVED_DUE_TO_CAPABILITY_GAP).",
    }
    return probes


def _run_text_forensics(real27_items: list[dict[str, Any]]) -> dict[str, Any]:
    rmap = {it["case_id"]: it for it in real27_items}
    gold_probes = _build_gold_real27_refusal_probes(rmap)
    rows = []
    refused_layers: Counter[str] = Counter()
    refused_categories_6_2: Counter[str] = Counter()
    adj_rows = []
    for it in real27_items:
        cid = it["case_id"]
        txt = it["ground_truth_text"]
        clear_local_geometry_parser_cache()
        lp = parse_geometry_problem_locally(txt)
        out = AIR.route_text_input(txt, allow_live_ai=False)
        rd = (out.response or {}).get("route_d") or {}
        env = (out.response or {}).get("envelope") or {}
        rc = env.get("reason_code") or (out.receipt or {}).get("code")
        det_audit = (out.receipt or {}).get("determinacy_audit") or rd.get("determinacy_audit")
        if out.status != "SERVED":
            layer = (
                "OUT_OF_SCOPE_OR_NON_CONVEX"
                if "NON_CONVEX" in str(rc) or cid == "vmmu_r475"
                else ("LOCAL_PARSER_OR_TYPED_FACT_GAP" if lp.status != LOCAL_PARSE_COMPLETE else "KERNEL_OR_SOURCE_GATE_BOUNDARY")
            )
            refused_layers[layer] += 1
            gp = gold_probes.get(cid) or {}
            cat = gp.get("primary_category") or layer
            refused_categories_6_2[cat] += 1
            rows.append({
                "case_id": cid,
                "partition": it.get("partition"),
                "local_parse_status": lp.status,
                "local_parse_reason": lp.reason_code,
                "route_status": out.status,
                "reason_code": rc,
                "layer": layer,
                "category_6_2": cat,
                "secondary_categories_6_2": gp.get("secondary_categories", []),
                "gold_typed_fact_comparison": gp.get("gold_result"),
                "gold_counterfactual": gp.get("gold_typo_fixed_counterfactual") or gp.get("gold_host_prism_counterfactual"),
                "forensic_note": gp.get("note"),
                "determinacy_audit_status": (det_audit or {}).get("status") if isinstance(det_audit, dict) else None,
            })
        elif rd.get("source_goal_completion") is not None:
            sgc = rd.get("source_goal_completion") or {}
            ans_internal = (rd.get("answers") or {}).get("q1")
            exp_ans = it.get("expected_answer")
            sc = env.get("scene3d") or {}
            adj_rows.append({
                "case_id": cid,
                "partition": it.get("partition"),
                "answers_internal": rd.get("answers"),
                "expected_answer": exp_ans,
                "numeric_answer_shown": sgc.get("numeric_answer_shown"),
                "numeric_source_goal": (sgc.get("goals") or [{}])[0].get("numeric_source_goal"),
                "continuity_errors": _continuity_count(env),
                "geometry_model_verified": out.status == "SERVED" and _continuity_count(env) == 0,
                "visual_goal_satisfied": (sgc.get("goals") or [{}])[0].get("state") == "GOAL_VISUALIZATION_READY",
                "mathematical_equivalence_verified": bool(ans_internal and exp_ans and EVI.same_value(str(ans_internal), str(exp_ans))),
                "dataset_oracle_mismatch_reason": "DATASET_KEY_ASKS_TRIG_VALUE_WHILE_AXO_MODE_A_VISUALIZES_ANGLE_ONLY",
                "numeric_answer_hidden_mode_a": (not sgc.get("numeric_answer_shown")) and (sgc.get("goals") or [{}])[0].get("numeric_source_goal") == "NOT_ANSWERED",
                "missing_objects_or_relations": [],
                "scene3d_object_count": len(sc.get("objects") or []),
            })
    r513 = next((r for r in rows if r["case_id"] == "vmmu_r513"), None)
    return {
        "refused_count": len(rows),
        "refused_layer_counts": dict(refused_layers),
        "refused_category_counts_6_2": dict(refused_categories_6_2),
        "refused_cases": rows,
        "adjudicated_mode_a_count": len(adj_rows),
        "adjudicated_mode_a_cases": adj_rows,
        "r513_source_gate_alignment": {
            "verified": bool(
                r513
                and r513["local_parse_status"] == LOCAL_PARSE_COMPLETE
                and r513["route_status"] == "REFUSED"
                and r513["reason_code"] == "MISSING_DIMENSION"
                and r513["determinacy_audit_status"] == "UNPROVED_DUE_TO_CAPABILITY_GAP"
            ),
            "details": r513,
        },
    }


def _grade_eifo_oracle(case_key: str, ans: dict[str, Any] | None) -> str:
    v = EIFO.grade(case_key, {"answers": ans})
    if v != "WRONG_SERVED" or not ans:
        return v
    exp = (EIFO.ORACLE.get(case_key) or EIFO.ORACLE.get(case_key.split("#")[0]) or {}).get("answers") or {}
    if exp and all(
        ans.get(k) == w or bool(EVI.same_value(str(ans.get(k, "")), str(w)))
        for k, w in exp.items()
    ):
        return "SERVED_CORRECT"
    return v


def _build_diagnostic_4_1(
    *,
    prep_status: str,
    dec: str | None,
    used_crop: bool,
    ambiguous_multi_problem: bool,
    candidates_count: int,
    cer: float | None,
    cf_draft: dict[str, Any],
    math_prf: dict[str, Any] | None,
    stacked_loss_count: int,
    blocking_reasons: list[str],
    uncertain_blocking: list[dict[str, Any]],
    uncertain_reason_counts: dict[str, int],
    uncertain_sample: list[dict[str, Any]],
    topo_verified_count: int,
    blurry_crop_count: int,
    quality_low_light: bool,
    quality_shadow: bool,
    edge_energy: float,
) -> dict[str, Any]:
    """Tạo bảng chẩn đoán 10 câu hỏi (§4.1) và phân loại xô nguyên nhân trung thực."""
    math_ref = int((math_prf or {}).get("ref") or 0)
    math_tp = int((math_prf or {}).get("tp") or 0)
    text_accurate = bool(cer is not None and cer <= 0.01 and cf_draft.get("all_recovered"))
    near_accurate = bool(cer is not None and cer <= 0.03 and cf_draft.get("all_recovered"))

    if dec == "LOCAL_OCR_ACCEPT":
        bucket = "AUTO_ACCEPTED_SAFE"
    elif prep_status == "needs_selection":
        bucket = "MULTI_PROBLEM_NEEDS_SELECTION"
    elif (not cf_draft.get("all_recovered")) or (cer is not None and cer > 0.03):
        bucket = "RECOGNITION_ERROR_NEEDS_CONFIRMATION"
    elif blocking_reasons == ["UNCERTAIN_SPANS"] and set(uncertain_reason_counts).issubset(
        {"SAME_FAMILY_AGREEMENT_ONLY", "NOT_IN_LEXICON"}
    ):
        bucket = "INSUFFICIENT_ACCEPTANCE_EVIDENCE_TEXT_ACCURATE"
    else:
        bucket = "GENUINE_DIAGRAM_OR_AMBIGUITY_CONFIRMATION"

    why_9 = (
        "AUTO_ACCEPTED"
        if dec == "LOCAL_OCR_ACCEPT"
        else ("MULTI_PROBLEM_NEEDS_SELECTION" if prep_status == "needs_selection" else blocking_reasons)
    )
    blocking_10 = (
        {"blocking_reasons": blocking_reasons, "uncertain_reason_counts": uncertain_reason_counts}
        if (dec != "LOCAL_OCR_ACCEPT" and near_accurate)
        else None
    )
    return {
        "q1_region_selected_correctly": (not ambiguous_multi_problem and prep_status != "needs_selection"),
        "q1_details": {"used_crop": used_crop, "ambiguous_multi_problem": ambiguous_multi_problem, "candidates_count": candidates_count},
        "q2_all_relevant_text_accurate": text_accurate,
        "q3_math_symbol_errors": max(0, math_ref - math_tp),
        "q3_math_recall": (math_prf or {}).get("recall"),
        "q4_line_or_reading_order_issue": bool(
            stacked_loss_count > 0
            or "LAYOUT_STRUCTURE_SUSPECTED" in blocking_reasons
            or "UNALIGNED_SECOND_READER_TEXT" in blocking_reasons
        ),
        "q5_comma_prime_or_exponent_issue": any(
            r in uncertain_reason_counts for r in ("PRIME_DISAGREEMENT", "SHARED_CORRUPTION_PATTERN", "DEGREE_SYMBOL_DISAGREEMENT")
        ),
        "q6_engine_disagreements": {"count": len(uncertain_blocking), "reasons": uncertain_reason_counts, "sample": uncertain_sample},
        "q7_glyph_topology_verified_count": topo_verified_count,
        "q8_blurry_faint_or_occluded": {
            "blurry_disputed_crops": blurry_crop_count,
            "low_light": quality_low_light,
            "shadow": quality_shadow,
            "edge_energy": edge_energy,
        },
        "q9_why_review_required": why_9,
        "q10_blocking_condition_if_text_accurate": blocking_10,
        "diagnostic_bucket": bucket,
    }


async def _evaluate_ocr_and_confirmation_async(baselines: dict[str, Any]) -> tuple[dict[str, Any], int]:
    from PIL import Image, ImageDraw, ImageFilter, ImageFont

    cont_errors = 0
    ocr_py = ROOT / ".superpowers" / "ocr-venv" / "Scripts" / "python.exe"
    ocr_tess = ROOT / ".superpowers" / "tessdata_fast"

    # Non-negotiable invariant checks that always run
    assert not OR.has_shared_corruption("120°")
    assert not OR.has_shared_corruption("150°")
    assert OR.has_shared_corruption("600°") is True
    assert OR.has_shared_corruption("S,ABCD") is True
    assert LO.LOCAL_OCR_WORKER_VERSION == "local-ocr-worker/4"
    assert OR.OCR_RECONCILE_VERSION == "layout-aware-ocr-reconcile/3"
    assert LR.LOCAL_OCR_ROUTE_VERSION == "local-ocr-route/2"

    if not ocr_py.exists() or not ocr_tess.is_dir():
        return {"available": False, "reason": "SIDECAR_NOT_PRESENT"}, 0

    prev_py = os.environ.get("LOCAL_OCR_PYTHON")
    prev_tess = os.environ.get("LOCAL_OCR_TESSDATA")
    os.environ["LOCAL_OCR_PYTHON"] = str(ocr_py)
    os.environ["LOCAL_OCR_TESSDATA"] = str(ocr_tess)
    LO.clear_local_ocr_cache()

    try:
        # 1. Glyph topology probes (12/12 including '=' vs '-')
        font_path = "C:/Windows/Fonts/arial.ttf"
        if not Path(font_path).exists():
            font_path = "C:/Windows/Fonts/segoeui.ttf"
        font = ImageFont.truetype(font_path, 28)
        topo_font_path = "C:/Windows/Fonts/cambria.ttc"
        if not Path(topo_font_path).exists():
            topo_font_path = font_path
        topo_font = ImageFont.truetype(topo_font_path, 32)

        topo_specs = [
            ("a²,", {"has_superscript_cc": True, "blurry": False}),
            ("a2,", {"has_superscript_cc": False, "blurry": False}),
            ("a³.", {"has_superscript_cc": True, "blurry": False}),
            ("a3.", {"has_superscript_cc": False, "blurry": False}),
            ("a√3.", {"has_radical_stroke": True, "blurry": False}),
            ("aV3.", {"has_radical_stroke": False, "blurry": False}),
            ("4cm²,", {"has_superscript_cc": True, "has_radical_stroke": False}),
            ("⊥", {"has_perp_t_junction": True}),
            ("L", {"has_perp_t_junction": False}),
            ("∥", {"has_parallel_bars": True}),
            ("=", {"has_equals_bars": True, "blurry": False}),
            ("-", {"has_equals_bars": False, "blurry": False}),
        ]
        topo_rows = []
        for tok, want_flags in topo_specs:
            im = Image.new("RGB", (180, 64), "white")
            ImageDraw.Draw(im).text((30, 14), tok, fill="black", font=topo_font)
            buf = io.BytesIO()
            im.save(buf, format="PNG")
            res = LO.reread_local_ocr_regions(buf.getvalue(), [[20, 10, 150, 56]])
            gt = ((res.get("readings") or [{}])[0]).get("glyph_topology") or {}
            ok = all(bool(gt.get(k)) is bool(v) for k, v in want_flags.items())
            topo_rows.append({"token": tok, "want": want_flags, "got": gt, "passed": ok})

        # 2. Rendered positive (4/4) & adversarial negative (3/3)
        rendered_pos = [
            ("pos_area_a2", "Cho hình chóp tứ giác đều S.ABCD có cạnh bên bằng a và diện tích đáy bằng a². Tính khoảng cách từ A đến mặt phẳng (SBC).", "a√6/3"),
            ("pos_2a_sqrt3", "Cho hình chóp S.ABCD có đáy ABCD là hình vuông cạnh 2a, SA vuông góc với (ABCD) và SA = a√3. Tính thể tích khối chóp S.ABCD.", "4a³√3/3"),
            ("pos_area_frac_a2_2", "Cho hình chóp S.ABC có đáy ABC là tam giác vuông cân tại B, diện tích tam giác ABC bằng a²/2, SA vuông góc với (ABC) và SA = a. Tính thể tích khối chóp S.ABC.", "a³/6"),
            ("pos_cm_cm2", "Cho hình chóp tứ giác đều S.ABCD có cạnh bên bằng 3cm và diện tích đáy bằng 9cm². Tính khoảng cách từ A đến mặt phẳng (SBC).", "√6"),
        ]
        pos_rows = []
        for pid, txt, want_ans in rendered_pos:
            im = Image.new("RGB", (1320, 220), "white")
            dr = ImageDraw.Draw(im)
            lines_out, cur = [], ""
            for w in txt.split():
                cand = f"{cur} {w}".strip()
                if len(cand) > 74:
                    lines_out.append(cur)
                    cur = w
                else:
                    cur = cand
            if cur:
                lines_out.append(cur)
            y = 32
            for ln in lines_out:
                dr.text((36, y), ln, fill="black", font=font)
                y += 44
            buf = io.BytesIO()
            im.save(buf, format="PNG")
            b64 = base64.b64encode(buf.getvalue()).decode("ascii")
            t0 = time.perf_counter()
            prep = (await prepare_unified_input(content=b64, declared_mime="image/png", filename=f"{pid}.png", api_key="", cache_version=CACHE_VERSION)).to_dict()
            pms = round((time.perf_counter() - t0) * 1000.0, 2)
            dec = (prep.get("provenance") or {}).get("ocr_decision")
            ans_got, routed_status = None, None
            if prep["status"] == "ready":
                routed = AIR.route_text_input(prep["problem_text"], allow_live_ai=False, input_kind="image")
                routed_status = routed.status
                env = (routed.response or {}).get("envelope") or {}
                c_err = _continuity_count(env) if routed.status == "SERVED" else 0
                cont_errors += c_err
                ans_got = ((routed.response or {}).get("route_d") or {}).get("answers", {}).get("q1")
            pos_rows.append({
                "id": pid,
                "prepare_status": prep["status"],
                "ocr_decision": dec,
                "draft_text": prep.get("problem_text"),
                "routed_status": routed_status,
                "answer": ans_got,
                "want": want_ans,
                "matched": dec == "LOCAL_OCR_ACCEPT" and routed_status == "SERVED" and bool(EVI.same_value(str(ans_got), want_ans)),
                "ms": pms,
            })

        neg_specs = [
            ("neg_inline_a2", "Cho hình chóp tứ giác đều S.ABCD có cạnh bên bằng a và diện tích đáy bằng a2. Tính thể tích khối chóp S.ABCD.", False),
            ("neg_blurry_crop", "Cho hình chóp tứ giác đều S.ABCD có cạnh bên bằng a và diện tích đáy bằng a². Tính thể tích khối chóp S.ABCD.", True),
            ("neg_diagram_ref", "Cho hình chóp S.ABCD có đáy ABCD là hình vuông cạnh a (tham khảo hình vẽ). Tính thể tích khối chóp S.ABCD.", False),
        ]
        neg_rows = []
        false_accepts = 0
        for nid, txt, do_blur in neg_specs:
            im = Image.new("RGB", (1320, 200), "white")
            dr = ImageDraw.Draw(im)
            dr.text((36, 40), txt[:70], fill="black", font=font)
            dr.text((36, 96), txt[70:].strip(), fill="black", font=font)
            if do_blur:
                im = im.filter(ImageFilter.GaussianBlur(radius=2.2))
            buf = io.BytesIO()
            im.save(buf, format="PNG")
            b64 = base64.b64encode(buf.getvalue()).decode("ascii")
            prep = (await prepare_unified_input(content=b64, declared_mime="image/png", filename=f"{nid}.png", api_key="", cache_version=CACHE_VERSION)).to_dict()
            dec = (prep.get("provenance") or {}).get("ocr_decision")
            if dec == "LOCAL_OCR_ACCEPT" or prep["status"] == "ready":
                false_accepts += 1
            neg_rows.append({
                "id": nid,
                "prepare_status": prep["status"],
                "ocr_decision": dec,
                "blocked": dec != "LOCAL_OCR_ACCEPT" and prep["status"] != "ready",
            })

        # 3. Helper to run single image end-to-end with confirmation simulation
        async def _eval_single_image(
            *,
            cid: str,
            raw_b: bytes,
            filename: str,
            gt: str,
            grade_fn: Any,
            statement_ref: str | None = None,
            critical_facts: list[dict[str, Any]] | None = None,
            fact_texts: list[str] | None = None,
            partition: str | None = None,
            measure_cold_breakdown: bool = False,
        ) -> tuple[dict[str, Any], int]:
            local_cont = 0
            p_path = Path(filename)
            mime, fname_use = _mime_and_name(raw_b, p_path)
            b64 = base64.b64encode(raw_b).decode("ascii")

            stage_timing: dict[str, Any] = {}
            blocking_spans_count = None
            zero_text_spans_count = None
            diagram_class = None
            diag_signals: dict[str, Any] | None = None

            if measure_cold_breakdown:
                LO.clear_local_ocr_cache()
                t0 = time.perf_counter()
                norm = normalize_image(raw_b)
                t_norm = time.perf_counter()
                rr = detect_problem_regions(norm)
                t_reg = time.perf_counter()
                rec = LR.run_local_ocr_route(rr.prepared_image.data, rr.prepared_figure_bboxes())
                t_rec = time.perf_counter()
                tm = rec.get("timing") or {}
                rb = tm.get("reread_breakdown") or {}
                unc = rec.get("uncertain_spans") or []
                spans_all = rec.get("spans") or []
                uncertain_blocking = [s for s in unc if s.get("blocking")]
                blocking_spans_count = len(uncertain_blocking)
                zero_text_spans_count = sum(1 for s in unc if s.get("text") == "0")
                diagram_class = (rec.get("diagram") or {}).get("classification")
                disputed_boxes = [d["bbox"] for d in (rec.get("disputed_math_slots") or []) if d.get("bbox")]
                blurry_crop_count = 0
                if disputed_boxes:
                    rr_crops = LO.reread_local_ocr_regions(rr.prepared_image.data, disputed_boxes)
                    blurry_crop_count = sum(
                        1 for rdx in (rr_crops.get("readings") or []) if ((rdx or {}).get("glyph_topology") or {}).get("blurry")
                    )
                diag_signals = {
                    "used_crop": bool(rr.used_crop),
                    "ambiguous_multi_problem": bool(rr.ambiguous_multi_problem),
                    "quality_low_light": bool(rr.quality.is_low_light),
                    "quality_shadow": bool(rr.quality.has_shadow),
                    "edge_energy": round(float(rr.quality.edge_energy), 2),
                    "topo_verified_count": sum(
                        1 for s in spans_all if str(s.get("evidence") or "").startswith("CROSS_FAMILY_BASE_PLUS_GLYPH_TOPOLOGY")
                    ),
                    "stacked_loss_count": sum(1 for s in unc if s.get("reason") == "FRACTION_STRUCTURE_LOSS"),
                    "uncertain_blocking": uncertain_blocking,
                    "uncertain_reason_counts": dict(Counter(str(s.get("reason")) for s in uncertain_blocking)),
                    "uncertain_sample": [
                        {"text": s.get("text"), "reason": s.get("reason"), "alts": (s.get("alternatives") or [])[:3]}
                        for s in uncertain_blocking[:6]
                    ],
                    "blocking_reasons": list(rec.get("blocking_reasons") or []),
                    "blurry_crop_count": blurry_crop_count,
                }
                stage_timing = {
                    "normalize_ms": round((t_norm - t0) * 1000.0, 2),
                    "region_detect_ms": round((t_reg - t_norm) * 1000.0, 2),
                    "route_total_ms": round((t_rec - t_reg) * 1000.0, 2),
                    "decode_ms": tm.get("decode_ms"),
                    "tesseract_ms": tm.get("tesseract_ms"),
                    "rapidocr_ms": tm.get("rapidocr_ms"),
                    "reconcile_only_ms": tm.get("reconcile_only_ms"),
                    "reread_ms": tm.get("reread_ms"),
                    "reread_crop_ms": rb.get("crop_ms"),
                    "reread_topology_ms": rb.get("topology_ms"),
                    "reread_latin_rec_ms": rb.get("latin_rec_ms"),
                    "reread_tess_eng_ms": rb.get("tess_eng_ms"),
                    "reread_tess_vie_ms": rb.get("tess_vie_ms"),
                }

            # Cold prepare timing (fresh local OCR cache)
            LO.clear_local_ocr_cache()
            t_p0 = time.perf_counter()
            prep = (await prepare_unified_input(content=b64, declared_mime=mime, filename=fname_use, api_key="", cache_version=CACHE_VERSION)).to_dict()
            cold_prepare_ms = round((time.perf_counter() - t_p0) * 1000.0, 2)

            # Warm prepare timing (hitting _RAW_OCR_CACHE & _REREAD_CACHE)
            t_w0 = time.perf_counter()
            prep_warm = (await prepare_unified_input(content=b64, declared_mime=mime, filename=fname_use, api_key="", cache_version=CACHE_VERSION)).to_dict()
            warm_prepare_ms = round((time.perf_counter() - t_w0) * 1000.0, 2)
            assert prep_warm["status"] == prep["status"]

            prov = prep.get("provenance") or {}
            dec = prov.get("ocr_decision")
            draft = prep.get("problem_text") or ""
            cer = EUC._cer(draft, gt) if (draft and gt) else None
            wer = EIFO._wer(draft, gt) if (draft and gt) else None
            math_prf = _critical_math_token_prf(draft, gt) if (draft and gt) else None
            cf_draft = _critical_fact_stats(draft, critical_facts=critical_facts, fact_texts=fact_texts)

            # Provenance contract check on raw auto/review draft
            raw_sha = prov.get("raw_ocr_text_sha256")
            prep_origin = prov.get("input_route") or "local_ocr"
            diagnostic_4_1 = (
                _build_diagnostic_4_1(
                    prep_status=prep["status"],
                    dec=dec,
                    used_crop=diag_signals["used_crop"],
                    ambiguous_multi_problem=diag_signals["ambiguous_multi_problem"],
                    candidates_count=len(prep.get("candidates") or []),
                    cer=cer,
                    cf_draft=cf_draft,
                    math_prf=math_prf,
                    stacked_loss_count=diag_signals["stacked_loss_count"],
                    blocking_reasons=diag_signals["blocking_reasons"],
                    uncertain_blocking=diag_signals["uncertain_blocking"],
                    uncertain_reason_counts=diag_signals["uncertain_reason_counts"],
                    uncertain_sample=diag_signals["uncertain_sample"],
                    topo_verified_count=diag_signals["topo_verified_count"],
                    blurry_crop_count=diag_signals["blurry_crop_count"],
                    quality_low_light=diag_signals["quality_low_light"],
                    quality_shadow=diag_signals["quality_shadow"],
                    edge_energy=diag_signals["edge_energy"],
                )
                if diag_signals is not None
                else None
            )

            row: dict[str, Any] = {
                "case_id": cid,
                "partition": partition,
                "prepare_status": prep["status"],
                "reason_code": prep.get("reason_code"),
                "ocr_decision": dec,
                "cer": cer,
                "wer": wer,
                "math_tokens_prf": math_prf,
                "critical_facts_draft": cf_draft,
                "blocking_uncertain_spans": blocking_spans_count,
                "zero_text_spans": zero_text_spans_count,
                "diagram_classification": diagram_class,
                "topo_verified_count": diag_signals["topo_verified_count"] if diag_signals else None,
                "blurry_crop_count": diag_signals["blurry_crop_count"] if diag_signals else None,
                "stacked_loss_count": diag_signals["stacked_loss_count"] if diag_signals else None,
                "used_crop": diag_signals["used_crop"] if diag_signals else None,
                "ambiguous_multi_problem": diag_signals["ambiguous_multi_problem"] if diag_signals else None,
                "review_items_count": len(prep.get("uncertain_tokens") or []),
                "candidates_count": len(prep.get("candidates") or []),
                "confirmation_contract_version": prov.get("confirmation_contract_version"),
                "cold_prepare_ms": cold_prepare_ms,
                "warm_prepare_ms": warm_prepare_ms,
                "stage_timing_ms": stage_timing,
                "diagnostic_4_1": diagnostic_4_1,
                "auto_route": None,
                "confirmation_simulated": None,
            }

            if prep["status"] == "ready" and draft:
                clear_local_geometry_parser_cache()
                t_s0 = time.perf_counter()
                routed = AIR.route_text_input(draft, allow_live_ai=False, input_kind="image")
                solve_ms = round((time.perf_counter() - t_s0) * 1000.0, 2)
                rd = (routed.response or {}).get("route_d") or {}
                env = (routed.response or {}).get("envelope") or {}
                t_c0 = time.perf_counter()
                c_err = _continuity_count(env) if routed.status == "SERVED" else 0
                cont_ms = round((time.perf_counter() - t_c0) * 1000.0, 2)
                tel = (routed.receipt or {}).get("adaptive_telemetry") or {}
                local_cont += c_err
                ans = rd.get("answers") if routed.status == "SERVED" else None
                g = grade_fn(routed.status, ans, rd, env)
                p_rec = build_verified_input_provenance(
                    draft,
                    InputSourceProvenance(
                        origin="local_ocr_auto_verified" if dec == "LOCAL_OCR_ACCEPT" else "local_ocr_student_confirmed",
                        raw_ocr_text_sha256=raw_sha,
                        prepared_region_sha256=prov.get("prepared_region_sha256"),
                        student_edited=False,
                    ),
                )
                row["auto_route"] = {
                    "routed_status": routed.status,
                    "answers": ans,
                    "grade": g,
                    "continuity_errors": c_err,
                    "scene3d_objects": len((env.get("scene3d") or {}).get("objects") or []) if routed.status == "SERVED" else 0,
                    "solve_ms": solve_ms,
                    "telemetry_ms": {
                        "local_parse_ms": tel.get("local_parse_ms"),
                        "hybrid_execution_ms": tel.get("hybrid_execution_ms"),
                        "continuity_check_ms": cont_ms,
                    },
                    "provenance": p_rec,
                    "false_auto_accept": (dec == "LOCAL_OCR_ACCEPT" and routed.status == "SERVED" and g.get("verdict") == "WRONG_SERVED"),
                }
            elif prep["status"] == "needs_confirmation" and draft:
                t_sim0 = time.perf_counter()
                sim = EIFO.simulate_student(draft, prep.get("uncertain_tokens") or [], gt)
                sim_ms = round((time.perf_counter() - t_sim0) * 1000.0, 2)
                confirmed_text = sim["text"]
                cf_after = _critical_fact_stats(confirmed_text, critical_facts=critical_facts, fact_texts=fact_texts)
                clear_local_geometry_parser_cache()
                t_s0 = time.perf_counter()
                routed = AIR.route_text_input(confirmed_text, allow_live_ai=False, input_kind="image")
                solve_ms = round((time.perf_counter() - t_s0) * 1000.0, 2)
                rd = (routed.response or {}).get("route_d") or {}
                env = (routed.response or {}).get("envelope") or {}
                t_c0 = time.perf_counter()
                c_err = _continuity_count(env) if routed.status == "SERVED" else 0
                cont_ms = round((time.perf_counter() - t_c0) * 1000.0, 2)
                tel = (routed.receipt or {}).get("adaptive_telemetry") or {}
                local_cont += c_err
                ans = rd.get("answers") if routed.status == "SERVED" else None
                g = grade_fn(routed.status, ans, rd, env)
                p_rec = build_verified_input_provenance(
                    confirmed_text,
                    InputSourceProvenance(
                        origin="local_ocr_student_confirmed",
                        raw_ocr_text_sha256=raw_sha,
                        prepared_region_sha256=prov.get("prepared_region_sha256"),
                        confirmed_span_count=len(prep.get("uncertain_tokens") or []),
                        student_edited=bool(sim["edits"]),
                    ),
                )
                assert p_rec is not None and p_rec["counted_as_unmodified_auto_ocr"] is False
                fallback_info = None
                fb_txt = statement_ref or gt
                if routed.status != "SERVED" and fb_txt and fb_txt != confirmed_text:
                    clear_local_geometry_parser_cache()
                    fb_routed = AIR.route_text_input(fb_txt, allow_live_ai=False, input_kind="user_edited_text")
                    fb_rd = (fb_routed.response or {}).get("route_d") or {}
                    fb_env = (fb_routed.response or {}).get("envelope") or {}
                    fb_cont = _continuity_count(fb_env) if fb_routed.status == "SERVED" else 0
                    local_cont += fb_cont
                    fb_ans = fb_rd.get("answers") if fb_routed.status == "SERVED" else None
                    fallback_info = {
                        "routed_status": fb_routed.status,
                        "reason_code": fb_env.get("reason_code") or (fb_routed.receipt or {}).get("code"),
                        "answers": fb_ans,
                        "grade": grade_fn(fb_routed.status, fb_ans, fb_rd, fb_env),
                        "continuity_errors": fb_cont,
                        "note": "Requires free-text edit on unflagged OCR error; reported strictly separately from span-only confirmation.",
                    }
                row["confirmation_simulated"] = {
                    "cer_after": EUC._cer(confirmed_text, gt) if gt else None,
                    "critical_facts_after": cf_after,
                    "edits": sim["edits"],
                    "edit_count": len(sim["edits"]),
                    "confirms": sim["confirms"],
                    "diagram_confirms": sim["diagram_confirms"],
                    "actions": sim["actions"],
                    "chars_typed": sim["chars_typed"],
                    "full_retype_chars": len(gt),
                    "routed_status": routed.status,
                    "reason_code": env.get("reason_code") or (routed.receipt or {}).get("code"),
                    "answers": ans,
                    "grade": g,
                    "continuity_errors": c_err,
                    "scene3d_objects": len((env.get("scene3d") or {}).get("objects") or []) if routed.status == "SERVED" else 0,
                    "simulate_ms": sim_ms,
                    "solve_ms": solve_ms,
                    "telemetry_ms": {
                        "local_parse_ms": tel.get("local_parse_ms"),
                        "hybrid_execution_ms": tel.get("hybrid_execution_ms"),
                        "continuity_check_ms": cont_ms,
                    },
                    "whole_draft_confirmation_fallback": fallback_info,
                    "provenance": p_rec,
                }
            elif prep["status"] == "needs_selection":
                # Multi-problem band switching flow
                sel_outcomes = []
                gt_parts = []
                # Find verbatim parts if provided for external16
                cat_match = next((c for c in CORPUS_ITEMS if c.get("image_id") == cid), None)
                if cat_match:
                    gt_parts = cat_match.get("verbatim_problem_texts") or []
                for idx, cand in enumerate(prep.get("candidates") or []):
                    sub_prep = (await prepare_unified_input(
                        content=b64,
                        declared_mime=mime,
                        filename=fname_use,
                        api_key="",
                        cache_version=CACHE_VERSION,
                        selected_candidate_id=cand["candidate_id"],
                    )).to_dict()
                    sub_text = sub_prep.get("problem_text") or ""
                    sub_gt = gt_parts[idx] if idx < len(gt_parts) else gt
                    if sub_prep["status"] == "needs_confirmation" and sub_text and sub_gt:
                        sub_sim = EIFO.simulate_student(sub_text, sub_prep.get("uncertain_tokens") or [], sub_gt)
                        final_sub = sub_sim["text"]
                        edits_n = len(sub_sim["edits"])
                    else:
                        final_sub = sub_text
                        edits_n = 0
                    clear_local_geometry_parser_cache()
                    sub_routed = AIR.route_text_input(final_sub, allow_live_ai=False, input_kind="image") if final_sub else None
                    sub_rd = ((sub_routed.response or {}).get("route_d") or {}) if sub_routed else {}
                    sub_env = ((sub_routed.response or {}).get("envelope") or {}) if sub_routed else {}
                    c_err = _continuity_count(sub_env) if (sub_routed and sub_routed.status == "SERVED") else 0
                    local_cont += c_err
                    sub_ans = sub_rd.get("answers") if (sub_routed and sub_routed.status == "SERVED") else None
                    sub_key = f"{cid}#{idx + 1}"
                    sub_oracle = _grade_eifo_oracle(sub_key, sub_ans) if sub_key in EIFO.ORACLE else None
                    sel_outcomes.append({
                        "candidate_id": cand["candidate_id"],
                        "label": cand.get("label"),
                        "prepare_status": sub_prep["status"],
                        "edits": edits_n,
                        "routed_status": sub_routed.status if sub_routed else None,
                        "answers": sub_ans,
                        "oracle_verdict": sub_oracle,
                        "continuity_errors": c_err,
                    })
                row["selection_outcomes"] = sel_outcomes

            return row, local_cont

        # 4. Evaluate REAL27 (27 images)
        real25 = json.loads((RUNS_DIR / "controlled-vision-real-image-validation/new_in_scope_image_manifest.json").read_text(encoding="utf-8"))["items"]
        real2 = json.loads((RUNS_DIR / "local-semantic-source-gate-reliability/fresh_external_manifest.json").read_text(encoding="utf-8"))["items"]
        real27_items = real25 + real2

        real27_rows = []
        for it in real27_items:
            cid = it["case_id"]
            p = ROOT / it["cache_path"]
            if not p.exists():
                continue

            def _grade_real27(st: str, ans: dict[str, Any] | None, rd: dict[str, Any], _env: dict[str, Any], item=it, case_id=cid) -> dict[str, Any]:
                if st != "SERVED":
                    return {"verdict": "NOT_SERVED"}
                g = EVI.grade(item, {"status": st, "answers": ans})
                is_adj = g.get("verdict") == "SERVED_NOT_COMPARABLE_NEEDS_ADJUDICATION" and rd.get("source_goal_completion") is not None
                if g.get("verdict") == "SERVED_DIFFERS_FROM_DATASET_KEY" and case_id in EUC.REAL27_KNOWN_KEY_ERRORS:
                    g["verdict"] = "SERVED_KNOWN_DATASET_KEY_ERRATUM"
                elif is_adj:
                    g["verdict"] = "SERVED_MODE_A_ADJUDICATED"
                elif g.get("verdict") == "SERVED_DIFFERS_FROM_DATASET_KEY":
                    g["verdict"] = "WRONG_SERVED"
                return g

            row, l_cont = await _eval_single_image(
                cid=cid,
                raw_b=p.read_bytes(),
                filename=p.name,
                gt=it["ground_truth_text"],
                grade_fn=_grade_real27,
                statement_ref=it.get("statement"),
                critical_facts=it.get("critical_facts"),
                partition=it.get("partition"),
                measure_cold_breakdown=True,
            )
            cont_errors += l_cont
            prior_r = baselines["real27_prior_rows"].get(cid) or {}
            dump_r = baselines["dump_real27"].get(cid) or {}
            row["before_baseline"] = {
                "cer": prior_r.get("cer"),
                "ocr_decision": prior_r.get("ocr_decision"),
                "blocking_uncertain_spans": dump_r.get("uncertain_blocking_count"),
                "zero_text_spans": (
                    sum(1 for u in (dump_r.get("uncertain_blocking") or []) if u.get("text") == "0")
                    if dump_r else None
                ),
            }
            real27_rows.append(row)

        def _summarize_real27(subset: list[dict[str, Any]]) -> dict[str, Any]:
            if not subset:
                return {"count": 0}
            cers_after = [r["cer"] for r in subset if r["cer"] is not None]
            cers_before = [r["before_baseline"]["cer"] for r in subset if r["before_baseline"].get("cer") is not None]
            block_after = [r["blocking_uncertain_spans"] for r in subset if r["blocking_uncertain_spans"] is not None]
            block_before = [r["before_baseline"]["blocking_uncertain_spans"] for r in subset if r["before_baseline"].get("blocking_uncertain_spans") is not None]
            z_after = [r["zero_text_spans"] for r in subset if r["zero_text_spans"] is not None]
            z_before = [r["before_baseline"]["zero_text_spans"] for r in subset if r["before_baseline"].get("zero_text_spans") is not None]
            cf_rec = sum(r["critical_facts_draft"]["recovered"] for r in subset)
            cf_tot = sum(r["critical_facts_draft"]["total"] for r in subset)
            cf_after_rec = sum(
                (r["confirmation_simulated"]["critical_facts_after"]["recovered"] if r["confirmation_simulated"] else r["critical_facts_draft"]["recovered"])
                for r in subset
            )
            mt_tp = sum((r["math_tokens_prf"] or {}).get("tp", 0) for r in subset)
            mt_ref = sum((r["math_tokens_prf"] or {}).get("ref", 0) for r in subset)
            auto_rows = [r for r in subset if r["auto_route"] is not None]
            conf_rows = [r for r in subset if r["confirmation_simulated"] is not None]
            return {
                "count": len(subset),
                "ocr_decision_counts": dict(Counter(r["ocr_decision"] for r in subset)),
                "cer_before_median": round(statistics.median(cers_before), 4) if cers_before else None,
                "cer_after_median": round(statistics.median(cers_after), 4) if cers_after else None,
                "cer_after_mean": round(sum(cers_after) / len(cers_after), 4) if cers_after else None,
                "blocking_spans_before": sum(block_before) if block_before else None,
                "blocking_spans_after": sum(block_after) if block_after else None,
                "zero_text_spans_before": sum(z_before) if z_before else None,
                "zero_text_spans_after": sum(z_after) if z_after else None,
                "math_token_recall_draft": round(mt_tp / max(1, mt_ref), 4),
                "critical_facts_draft": f"{cf_rec}/{cf_tot}",
                "critical_facts_after_confirmation": f"{cf_after_rec}/{cf_tot}",
                "critical_facts_after_rate": round(cf_after_rec / max(1, cf_tot), 4),
                "false_auto_accepts": sum(1 for r in auto_rows if r["auto_route"].get("false_auto_accept")),
                "auto_served_correct": sum(1 for r in auto_rows if r["auto_route"].get("routed_status") == "SERVED" and r["auto_route"].get("grade", {}).get("verdict") != "WRONG_SERVED"),
                "confirmed_ready_count": len(conf_rows),
                "confirmed_served": sum(1 for r in conf_rows if r["confirmation_simulated"].get("routed_status") == "SERVED"),
                "confirmed_wrong_served": sum(1 for r in conf_rows if r["confirmation_simulated"].get("grade", {}).get("verdict") == "WRONG_SERVED"),
                "whole_draft_fallback_served": sum(
                    1
                    for r in conf_rows
                    if ((r["confirmation_simulated"].get("whole_draft_confirmation_fallback") or {}).get("routed_status") == "SERVED")
                ),
                "diagnostic_4_1_buckets": dict(
                    Counter(
                        (r.get("diagnostic_4_1") or {}).get("diagnostic_bucket")
                        for r in subset
                        if r.get("diagnostic_4_1")
                    )
                ),
                "confirmation_median_actions": statistics.median([r["confirmation_simulated"]["actions"] for r in conf_rows]) if conf_rows else 0,
                "confirmation_median_chars_typed": statistics.median([r["confirmation_simulated"]["chars_typed"] for r in conf_rows]) if conf_rows else 0,
                "confirmation_total_chars_typed": sum(r["confirmation_simulated"]["chars_typed"] for r in conf_rows),
                "confirmation_total_full_retype_chars": sum(r["confirmation_simulated"]["full_retype_chars"] for r in conf_rows),
                "latency_cold_prepare": _stats([r["cold_prepare_ms"] for r in subset]),
                "latency_warm_prepare": _stats([r["warm_prepare_ms"] for r in subset]),
                "latency_stage_breakdown": {
                    k: _stats([r["stage_timing_ms"].get(k) for r in subset if r["stage_timing_ms"].get(k) is not None])
                    for k in (
                        "normalize_ms", "region_detect_ms", "decode_ms", "tesseract_ms", "rapidocr_ms",
                        "reconcile_only_ms", "reread_ms", "reread_crop_ms", "reread_topology_ms",
                        "reread_latin_rec_ms", "reread_tess_eng_ms", "reread_tess_vie_ms",
                    )
                },
                "latency_downstream_breakdown": {
                    "simulate_ms": _stats([r["confirmation_simulated"].get("simulate_ms") for r in conf_rows if r["confirmation_simulated"].get("simulate_ms") is not None]),
                    "local_parse_ms": _stats([
                        ((r["auto_route"] or r["confirmation_simulated"]).get("telemetry_ms") or {}).get("local_parse_ms")
                        for r in subset if (r["auto_route"] or r["confirmation_simulated"])
                    ]),
                    "hybrid_execution_ms": _stats([
                        ((r["auto_route"] or r["confirmation_simulated"]).get("telemetry_ms") or {}).get("hybrid_execution_ms")
                        for r in subset if (r["auto_route"] or r["confirmation_simulated"])
                    ]),
                    "continuity_check_ms": _stats([
                        ((r["auto_route"] or r["confirmation_simulated"]).get("telemetry_ms") or {}).get("continuity_check_ms")
                        for r in subset if (r["auto_route"] or r["confirmation_simulated"])
                    ]),
                },
                "latency_solve": _stats([
                    (r["auto_route"]["solve_ms"] if r["auto_route"] else r["confirmation_simulated"]["solve_ms"])
                    for r in subset if (r["auto_route"] or r["confirmation_simulated"])
                ]),
                "latency_cold_end_to_end": _stats([
                    r["cold_prepare_ms"] + (r["auto_route"]["solve_ms"] if r["auto_route"] else (r["confirmation_simulated"]["solve_ms"] if r["confirmation_simulated"] else 0.0))
                    for r in subset
                ]),
                "latency_warm_end_to_end": _stats([
                    r["warm_prepare_ms"] + (r["auto_route"]["solve_ms"] if r["auto_route"] else (r["confirmation_simulated"]["solve_ms"] if r["confirmation_simulated"] else 0.0))
                    for r in subset
                ]),
            }

        # 5. Evaluate EXTERNAL16 (15 printed + 1 handwritten reported separately)
        ext_all = [c for c in CORPUS_ITEMS if c.get("has_complete_problem")]
        ext_printed_rows, ext_hw_rows = [], []
        for it in ext_all:
            iid = it["image_id"]
            cand_path = ROOT / ".superpowers" / "external_image_cache" / (it.get("filename") or "")
            if not cand_path.exists():
                continue

            def _grade_ext16(st: str, ans: dict[str, Any] | None, _rd: dict[str, Any], _env: dict[str, Any], case_id=iid) -> dict[str, Any]:
                if st != "SERVED":
                    return {"verdict": "NOT_SERVED"}
                return {"verdict": _grade_eifo_oracle(case_id, ans)}

            row, l_cont = await _eval_single_image(
                cid=iid,
                raw_b=cand_path.read_bytes(),
                filename=cand_path.name,
                gt=it.get("ground_truth_text") or "",
                grade_fn=_grade_ext16,
                statement_ref=it.get("ground_truth_text"),
                partition=it.get("printed_or_handwritten"),
                measure_cold_breakdown=True,
            )
            cont_errors += l_cont
            prior_e = baselines["ext16_prior_rows"].get(iid) or {}
            row["before_baseline"] = {
                "cer": ((prior_e.get("scoring") or {}).get("cer") or {}).get("reconciled_draft"),
                "blocking_uncertain_spans": (prior_e.get("after_reconcile") or {}).get("blocking_uncertain_count"),
                "ocr_decision": "LOCAL_OCR_ACCEPT" if (prior_e.get("after_reconcile") or {}).get("extraction_verified") else "LOCAL_OCR_REVIEW_REQUIRED",
            }
            if it.get("printed_or_handwritten") == "HANDWRITTEN":
                ext_hw_rows.append(row)
            else:
                ext_printed_rows.append(row)

        # 6. Evaluate UNTOUCHED External Image Sets (reported strictly separately)
        new_ext_rows = []
        for it in NEC.NEW_EXTERNAL_ITEMS:
            iid = it["image_id"]
            p = ROOT / ".superpowers" / "external_image_cache" / it["filename"]
            if not p.exists():
                continue

            def _grade_ne(st: str, ans: dict[str, Any] | None, _rd: dict[str, Any], _env: dict[str, Any], case_id=iid) -> dict[str, Any]:
                if st != "SERVED":
                    return {"verdict": "NOT_SERVED"}
                return {"verdict": _grade_eifo_oracle(case_id, ans)}

            row, l_cont = await _eval_single_image(
                cid=iid,
                raw_b=p.read_bytes(),
                filename=p.name,
                gt=it.get("ground_truth_text") or "",
                grade_fn=_grade_ne,
                partition="untouched_new_external_12",
                measure_cold_breakdown=False,
            )
            cont_errors += l_cont
            new_ext_rows.append(row)

        nic8_manifest = json.loads((RUNS_DIR / "real-image-ocr-vision-comparative-acceptance/new_image_corpus_manifest.json").read_text(encoding="utf-8"))["items"]
        nic8_rows = []
        for it in nic8_manifest:
            cid = it["case_id"]
            p = ROOT / it["cache_path"]
            if not p.exists():
                continue

            def _grade_nic(st: str, ans: dict[str, Any] | None, _rd: dict[str, Any], _env: dict[str, Any]) -> dict[str, Any]:
                return {"verdict": "SERVED_NO_EXPLICIT_NUMERIC_ORACLE" if st == "SERVED" else "NOT_SERVED"}

            row, l_cont = await _eval_single_image(
                cid=cid,
                raw_b=p.read_bytes(),
                filename=p.name,
                gt=it.get("ground_truth_text") or "",
                grade_fn=_grade_nic,
                fact_texts=it.get("critical_fact_texts") or [],
                partition=it.get("partition"),
                measure_cold_breakdown=False,
            )
            cont_errors += l_cont
            nic8_rows.append(row)

        # 7. Deterministic offline Vision-fallback mock + edited confirmation cache/provenance separation
        vis_prep = {
            "status": "ready",
            "source_kind": "image",
            "problem_text": "Cho hình chóp S.ABCD có đáy ABCD là hình vuông cạnh a, SA vuông góc với (ABCD) và SA = a√3. Tính thể tích khối chóp S.ABCD.",
            "provenance": {"extraction_method": "vlm", "confirmation_contract_version": "ocr-confirmation-provenance/1"},
            "metrics": {"vlm_calls": 1, "processing_ms": 50.0},
        }
        vis_out = AIR.route_image_or_prepare_outcome(vis_prep, allow_live_ai=False)
        vis_env = (vis_out.response or {}).get("envelope") or {}
        vis_cont = _continuity_count(vis_env) if vis_out.status == "SERVED" else 0
        cont_errors += vis_cont
        vision_fallback_mock = {
            "passed": (
                vis_out.status == "SERVED"
                and vis_out.telemetry.chosen_route == "VISION_THEN_LOCAL_DETERMINISTIC"
                and vis_out.telemetry.gemini_typed_fact_calls == 0
                and ((vis_out.response or {}).get("route_d") or {}).get("answers") == {"q1": "a³√3/3"}
                and vis_cont == 0
            ),
            "route": vis_out.telemetry.chosen_route,
            "answers": ((vis_out.response or {}).get("route_d") or {}).get("answers"),
            "live_ai_calls": vis_out.telemetry.gemini_typed_fact_calls,
            "continuity_errors": vis_cont,
        }

        draft_t = "Cho hình chóp S.ABCD có đáy ABCD là hình vuông cạnh a, SA vuông góc với (ABCD) và SA = a. Tính thể tích khối chóp S.ABCD."
        edit_t = draft_t.replace("SA = a.", "SA = 2a.")
        raw_sha = hashlib.sha256(draft_t.encode("utf-8")).hexdigest()
        prov_edit = build_verified_input_provenance(
            edit_t,
            InputSourceProvenance(origin="local_ocr_auto_verified", raw_ocr_text_sha256=raw_sha, confirmed_span_count=1, selected_candidate_id="region-1~band-2"),
        )
        k_draft = prepare_local_first_hybrid(draft_t, model=resolve_hybrid_gemini_model()).cache_key
        k_edit = prepare_local_first_hybrid(edit_t, model=resolve_hybrid_gemini_model()).cache_key
        provenance_cache_check = {
            "passed": bool(
                prov_edit
                and prov_edit["edited_from_raw_ocr"] is True
                and prov_edit["origin"] == "local_ocr_student_confirmed"
                and prov_edit["counted_as_unmodified_auto_ocr"] is False
                and k_draft != k_edit
            ),
            "distinct_cache_keys": k_draft != k_edit,
            "cache_version": CACHE_VERSION,
            "route_d_cache_policy": ROUTE_D_CACHE_POLICY,
        }

        cache_split_ok = len(LO._RAW_OCR_CACHE) <= LO._RAW_OCR_CACHE_MAX and len(LO._REREAD_CACHE) <= LO._REREAD_CACHE_MAX

        def _ext16_summary(rows_in: list[dict[str, Any]]) -> dict[str, Any]:
            cers_a = [r["cer"] for r in rows_in if r["cer"] is not None]
            cers_b = [r["before_baseline"]["cer"] for r in rows_in if r["before_baseline"].get("cer") is not None]
            auto_rows = [r for r in rows_in if r["auto_route"] is not None]
            conf_rows = [r for r in rows_in if r["confirmation_simulated"] is not None]
            sel_rows = [r for r in rows_in if r.get("selection_outcomes") is not None]
            return {
                "count": len(rows_in),
                "ocr_decision_counts": dict(Counter(r["ocr_decision"] for r in rows_in)),
                "prepare_status_counts": dict(Counter(r["prepare_status"] for r in rows_in)),
                "cer_before_median": round(statistics.median(cers_b), 4) if cers_b else None,
                "cer_after_median": round(statistics.median(cers_a), 4) if cers_a else None,
                "false_auto_accepts": sum(1 for r in auto_rows if r["auto_route"].get("false_auto_accept")),
                "auto_served_correct": sum(1 for r in auto_rows if r["auto_route"].get("grade", {}).get("verdict") == "SERVED_CORRECT"),
                "confirmed_ready_count": len(conf_rows),
                "confirmed_served_correct": sum(1 for r in conf_rows if r["confirmation_simulated"].get("grade", {}).get("verdict") == "SERVED_CORRECT"),
                "confirmed_wrong_served": sum(1 for r in conf_rows if r["confirmation_simulated"].get("grade", {}).get("verdict") == "WRONG_SERVED"),
                "whole_draft_fallback_served": sum(
                    1
                    for r in conf_rows
                    if ((r["confirmation_simulated"].get("whole_draft_confirmation_fallback") or {}).get("routed_status") == "SERVED")
                ),
                "diagnostic_4_1_buckets": dict(
                    Counter(
                        (r.get("diagnostic_4_1") or {}).get("diagnostic_bucket")
                        for r in rows_in
                        if r.get("diagnostic_4_1")
                    )
                ),
                "confirmation_median_actions": statistics.median([r["confirmation_simulated"]["actions"] for r in conf_rows]) if conf_rows else 0,
                "confirmation_median_chars_typed": statistics.median([r["confirmation_simulated"]["chars_typed"] for r in conf_rows]) if conf_rows else 0,
                "selection_bands_tested": sum(len(r["selection_outcomes"]) for r in sel_rows),
                "selection_served_correct": sum(1 for r in sel_rows for s in r["selection_outcomes"] if s.get("oracle_verdict") == "SERVED_CORRECT"),
                "latency_cold_prepare": _stats([r["cold_prepare_ms"] for r in rows_in]),
                "latency_warm_prepare": _stats([r["warm_prepare_ms"] for r in rows_in]),
            }

        def _untouched_summary(rows_in: list[dict[str, Any]]) -> dict[str, Any]:
            cers = [r["cer"] for r in rows_in if r["cer"] is not None]
            cf_rec = sum(r["critical_facts_draft"]["recovered"] for r in rows_in)
            cf_tot = sum(r["critical_facts_draft"]["total"] for r in rows_in)
            auto_rows = [r for r in rows_in if r["auto_route"] is not None]
            conf_rows = [r for r in rows_in if r["confirmation_simulated"] is not None]
            return {
                "count": len(rows_in),
                "ocr_decision_counts": dict(Counter(r["ocr_decision"] for r in rows_in)),
                "cer_median": round(statistics.median(cers), 4) if cers else None,
                "critical_facts_draft": f"{cf_rec}/{cf_tot}" if cf_tot else None,
                "auto_accepts": len(auto_rows),
                "auto_wrong_served": sum(1 for r in auto_rows if r["auto_route"].get("grade", {}).get("verdict") == "WRONG_SERVED"),
                "confirmed_served": sum(1 for r in conf_rows if r["confirmation_simulated"].get("routed_status") == "SERVED"),
                "confirmed_served_correct": sum(1 for r in conf_rows if r["confirmation_simulated"].get("grade", {}).get("verdict") == "SERVED_CORRECT"),
                "confirmed_wrong_served": sum(1 for r in conf_rows if r["confirmation_simulated"].get("grade", {}).get("verdict") == "WRONG_SERVED"),
                "latency_cold_prepare": _stats([r["cold_prepare_ms"] for r in rows_in]),
                "rows": rows_in,
            }

        real27_overall = _summarize_real27(real27_rows)
        real27_by_partition = {
            part: _summarize_real27([r for r in real27_rows if r["partition"] == part])
            for part in ("development", "frozen_external_evaluation", "fresh_external_evaluation")
        }

        return {
            "available": True,
            "worker_version": LO.LOCAL_OCR_WORKER_VERSION,
            "ocr_reconcile_version": OR.OCR_RECONCILE_VERSION,
            "local_ocr_route_version": LR.LOCAL_OCR_ROUTE_VERSION,
            "cache_split_ok": cache_split_ok,
            "raw_cache_max": LO._RAW_OCR_CACHE_MAX,
            "reread_cache_max": LO._REREAD_CACHE_MAX,
            "glyph_topology_passed": sum(1 for r in topo_rows if r["passed"]),
            "glyph_topology_total": len(topo_rows),
            "glyph_topology_rows": topo_rows,
            "rendered_positive_accepted": sum(1 for r in pos_rows if r["matched"]),
            "rendered_positive_total": len(pos_rows),
            "rendered_positive_rows": pos_rows,
            "adversarial_negative_blocked": sum(1 for r in neg_rows if r["blocked"]),
            "adversarial_negative_total": len(neg_rows),
            "false_auto_accepts_negative": false_accepts,
            "adversarial_negative_rows": neg_rows,
            "real27_images": {
                "summary": real27_overall,
                "by_partition": real27_by_partition,
                "before_baseline_meta": baselines["prior_eval_meta"],
                "before_baseline_summary": baselines["real27_summary"],
                "rows": real27_rows,
            },
            "external16_printed_images": {
                "summary": _ext16_summary(ext_printed_rows),
                "before_baseline_summary": baselines["ext15_summary"],
                "rows": ext_printed_rows,
            },
            "external16_handwritten_diagnostic": {
                "note": "Real student handwriting reported separately; never claimed as reliable printed OCR.",
                "summary": _ext16_summary(ext_hw_rows),
                "rows": ext_hw_rows,
            },
            "untouched_external_image_sets": {
                "note": "Held outside REAL27/External16 OCR tuning; reported strictly separately from development subsets.",
                "new_external_12": _untouched_summary(new_ext_rows),
                "new_image_corpus_8": {
                    "development": _untouched_summary([r for r in nic8_rows if r["partition"] == "development"]),
                    "frozen_external_evaluation": _untouched_summary([r for r in nic8_rows if r["partition"] == "frozen_external_evaluation"]),
                },
            },
            "vision_fallback_offline_mock": vision_fallback_mock,
            "confirmation_provenance_and_cache_144": provenance_cache_check,
        }, cont_errors
    finally:
        LO.shutdown_local_ocr()
        LO.clear_local_ocr_cache()
        if prev_py is None:
            os.environ.pop("LOCAL_OCR_PYTHON", None)
        else:
            os.environ["LOCAL_OCR_PYTHON"] = prev_py
        if prev_tess is None:
            os.environ.pop("LOCAL_OCR_TESSDATA", None)
        else:
            os.environ["LOCAL_OCR_TESSDATA"] = prev_tess


def _build_dataset_provenance() -> dict[str, Any]:
    return {
        "real27_images_and_text": {
            "count": 27,
            "sources": [
                "docs/evaluation/geometry/runs/controlled-vision-real-image-validation/new_in_scope_image_manifest.json (25 anvo25/vmmu MIT images: 6 development + 19 frozen_external_evaluation)",
                "docs/evaluation/geometry/runs/local-semantic-source-gate-reliability/fresh_external_manifest.json (2 anvo25/vmmu MIT images: fresh_external_evaluation)",
            ],
            "ground_truth_status": "GROUND_TRUTH_UNVERIFIED (agent-transcribed from source images + MIT dataset answer keys)",
        },
        "external16_printed_and_handwritten": {
            "count": 16,
            "source": "docs/evaluation/geometry/runs/real-world-printed-handwriting-acquisition/tools/corpus_catalog.py",
            "split": "15 printed (8 hoidap247 LICENSE_UNVERIFIED in gitignored cache + 7 vmmu MIT) + 1 handwritten (hd_a_6043187)",
        },
        "new_external_12": {
            "count": 12,
            "source": "docs/evaluation/geometry/runs/image-first-ocr-verified-geometry/tools/new_external_catalog.py",
            "partition": "untouched_external_image_set (MIT anvo25/vmmu)",
        },
        "new_image_corpus_8": {
            "count": 8,
            "source": "docs/evaluation/geometry/runs/real-image-ocr-vision-comparative-acceptance/new_image_corpus_manifest.json",
            "partition": "2 development + 6 frozen_external_evaluation",
        },
        "sealed_or_locked_corpora_opened": {
            "H-1": 0,
            "W2": 0,
            "W3": 0,
        },
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true", help="Do not write REAL_WORLD_END_TO_END_EVALUATION.json")
    args = ap.parse_args()

    baselines = _load_baselines()
    surfaces = EUC._check_surfaces()
    rm_eval = EAC._evaluate_reasoning_matrix()
    r1_eval = EAC._evaluate_r1_probe()
    nc_eval, cont_nc = EUC._run_nc_and_negatives()
    a4_eval, cont_a4 = EUC._run_a4_and_depth_bounds()
    dev_eval, cont_dev = EUC._run_exposed_dev_corpora()

    real25 = json.loads((RUNS_DIR / "controlled-vision-real-image-validation/new_in_scope_image_manifest.json").read_text(encoding="utf-8"))["items"]
    real2 = json.loads((RUNS_DIR / "local-semantic-source-gate-reliability/fresh_external_manifest.json").read_text(encoding="utf-8"))["items"]
    real27_forensics = _run_text_forensics(real25 + real2)

    _install_windows_socketpair_guard()
    loop = asyncio.new_event_loop()
    try:
        ocr_eval, cont_ocr = loop.run_until_complete(_evaluate_ocr_and_confirmation_async(baselines))
    finally:
        loop.close()

    c_safety = EUC._run_stream_c_safety()
    total_cont_errors = cont_nc + cont_a4 + cont_dev + cont_ocr
    measured_hash, measured_count = FZ.measured_system_hash()
    head_sha = _git_head()
    dirty_product = bool(
        subprocess.check_output(
            ["git", "status", "--porcelain", "--", "backend/app", "frontend/src"],
            cwd=ROOT,
            text=True,
        ).strip()
    )

    r27s = (ocr_eval.get("real27_images") or {}).get("summary") or {}
    e16s = (ocr_eval.get("external16_printed_images") or {}).get("summary") or {}
    rm_pos = rm_eval.get("positive_rows") or []
    rm_cls = dict(Counter((r.get("search_telemetry") or {}).get("classification") for r in rm_pos if r.get("status") == "SERVED"))
    rm_reuse = sum(1 for r in rm_pos if ((r.get("search_telemetry") or {}).get("reused_intermediates") or 0) > 0)
    rm_budget_exceeded = sum(1 for r in rm_pos if "BUDGET" in str(r.get("reason_code") or ""))

    r27_auto_n = int((r27s.get("ocr_decision_counts") or {}).get("LOCAL_OCR_ACCEPT", 0))
    r27_n = int(r27s.get("count", 0) or 0)
    r27_conf_n = int(r27s.get("confirmed_ready_count", 0) or 0)
    r27_conf_srv = int(r27s.get("confirmed_served", 0) or 0)
    e16_n = int(e16s.get("count", 0) or 0)
    e16_auto_n = int((e16s.get("ocr_decision_counts") or {}).get("LOCAL_OCR_ACCEPT", 0))
    e16_conf_n = int(e16s.get("confirmed_ready_count", 0) or 0)
    e16_conf_srv = int(e16s.get("confirmed_served_correct", 0) or 0)

    mandatory_metrics_9_3 = {
        "ocr": {
            "character_error_rate_median_before_after": {
                "real27": [r27s.get("cer_before_median"), r27s.get("cer_after_median")],
                "external15_printed": [e16s.get("cer_before_median"), e16s.get("cer_after_median")],
            },
            "critical_math_symbol_recall_draft": {"real27": r27s.get("math_token_recall_draft")},
            "critical_fact_preservation_rate_real27": {
                "draft": r27s.get("critical_facts_draft"),
                "after_span_confirmation": r27s.get("critical_facts_after_confirmation"),
                "after_span_confirmation_rate": r27s.get("critical_facts_after_rate"),
            },
            "region_selection_accuracy": {
                "rendered_positive": f"{ocr_eval.get('rendered_positive_accepted')}/{ocr_eval.get('rendered_positive_total')}",
                "ext15_selection_bands_served_correct": f"{e16s.get('selection_served_correct')}/{e16s.get('selection_bands_tested')}",
            },
            "safe_auto_accept_rate": {
                "real27": f"{r27_auto_n}/{r27_n}",
                "external15_printed": f"{e16_auto_n}/{e16_n}",
            },
            "false_auto_accept_rate": {
                "adversarial_negative": ocr_eval.get("false_auto_accepts_negative"),
                "real27": r27s.get("false_auto_accepts"),
                "external15_printed": e16s.get("false_auto_accepts"),
            },
            "review_rate_or_selection": {
                "real27_needs_confirmation": f"{r27_conf_n}/{r27_n}",
                "external15_needs_confirmation": f"{e16_conf_n}/{e16_n}",
                "external15_needs_selection": (e16s.get("prepare_status_counts") or {}).get("needs_selection", 0),
            },
            "confirmation_success_rate_span_only": {
                "real27": f"{r27_conf_srv}/{r27_conf_n}",
                "external15_printed": f"{e16_conf_srv}/{e16_conf_n}",
            },
            "confirmation_effort_real27": {
                "median_actions": r27s.get("confirmation_median_actions"),
                "median_chars_typed": r27s.get("confirmation_median_chars_typed"),
                "chars_typed_vs_full_retype": f"{r27s.get('confirmation_total_chars_typed')}/{r27s.get('confirmation_total_full_retype_chars')}",
            },
            "ocr_latency_p50_p95_ms": {
                "real27_cold_prepare": r27s.get("latency_cold_prepare"),
                "real27_warm_prepare": r27s.get("latency_warm_prepare"),
                "external15_cold_prepare": e16s.get("latency_cold_prepare"),
                "external15_warm_prepare": e16s.get("latency_warm_prepare"),
            },
        },
        "understanding": {
            "real27_text_served_and_wrong": f"{dev_eval['real27_text']['served']}/{dev_eval['real27_text']['total']} (wrong={dev_eval['real27_text']['wrong_served']})",
            "real27_refused_9_forensics_6_2": real27_forensics.get("refused_category_counts_6_2"),
            "real27_mode_a_adjudicated": real27_forensics.get("adjudicated_mode_a_count"),
            "nc_nl_correct_rate": f"{nc_eval['nc_nl_passed']}/{nc_eval['nc_nl_total']}",
            "nc_gold_correct_rate": f"{nc_eval['nc_gold_passed']}/{nc_eval['nc_gold_total']}",
            "r513_missing_fact_detection_aligned": real27_forensics["r513_source_gate_alignment"]["verified"],
            "autonomous_negatives_correct_refusal_rate": f"{nc_eval['autonomous_negatives_refused']}/{nc_eval['autonomous_negatives_total']}",
            "false_complete_or_wrong_served_negatives": nc_eval["autonomous_negatives_false_served"],
        },
        "planner": {
            "valid_plan_rate_rm72_positive": f"{rm_eval['positive_served']}/{rm_eval['positive_total']}",
            "negative_refusal_rm72": f"{rm_eval['negative_refused']}/{rm_eval['negative_total']}",
            "classification_counts_rm72_served": rm_cls,
            "intermediate_reuse_cases_rm72": rm_reuse,
            "budget_exceeded_or_ir_limit_rm72": {
                "ir_or_search_budget_exceeded_rows": rm_budget_exceeded,
                "max_memory_declarations": 32,
                "mg9_planner_candidates_generated": ((rm_eval.get("mg9_root_cause_7_questions") or {}).get("q2_search_telemetry") or {}).get("candidate_count"),
            },
            "kernel_verification_continuity_errors": total_cont_errors,
            "planning_latency_p50_p95_ms_rm72": [rm_eval.get("latency_p50_ms"), rm_eval.get("latency_p95_ms")],
        },
        "end_to_end": {
            "text_to_verified_scene3d_real27": f"{dev_eval['real27_text']['served']}/{dev_eval['real27_text']['total']}",
            "image_to_verified_scene3d_without_confirmation_real27": f"{r27s.get('auto_served_correct', 0)}/{r27_n}",
            "image_to_verified_scene3d_after_span_confirmation_only_real27": f"{int(r27s.get('auto_served_correct', 0) or 0) + r27_conf_srv}/{r27_n}",
            "image_to_verified_scene3d_whole_draft_fallback_additional_real27": r27s.get("whole_draft_fallback_served", 0),
            "image_to_verified_scene3d_without_confirmation_ext15": f"{e16s.get('auto_served_correct', 0)}/{e16_n}",
            "image_to_verified_scene3d_after_span_confirmation_only_ext15": f"{int(e16s.get('auto_served_correct', 0) or 0) + e16_conf_srv}/{e16_n}",
            "image_to_verified_scene3d_ext15_selection_bands": f"{e16s.get('selection_served_correct', 0)}/{e16s.get('selection_bands_tested', 0)}",
            "image_to_verified_scene3d_whole_draft_fallback_additional_ext15": e16s.get("whole_draft_fallback_served", 0),
            "image_to_verified_scene3d_vision_fallback": {
                "offline_mock_passed": ocr_eval.get("vision_fallback_offline_mock", {}).get("passed"),
                "live_gemini_vision": "NOT_MEASURED",
            },
            "wrong_scene_served_total": (
                int(r27s.get("false_auto_accepts", 0) or 0)
                + int(r27s.get("confirmed_wrong_served", 0) or 0)
                + int(e16s.get("false_auto_accepts", 0) or 0)
                + int(e16s.get("confirmed_wrong_served", 0) or 0)
                + int(dev_eval["real27_text"]["wrong_served"])
            ),
            "scene_continuity_errors": total_cont_errors,
            "user_visible_output_policy_mode_a_compliant": c_safety["mode_a_trig_no_answer_leak"],
        },
    }

    stage_latency_profiling_10 = {
        "dataset": "real27_images (27 images, single normalized asyncio event loop on host CPU)",
        "cold_prepare": r27s.get("latency_cold_prepare"),
        "warm_prepare": r27s.get("latency_warm_prepare"),
        "cold_end_to_end": r27s.get("latency_cold_end_to_end"),
        "warm_end_to_end": r27s.get("latency_warm_end_to_end"),
        "solve_total": r27s.get("latency_solve"),
        "ocr_and_preprocessing_stages": r27s.get("latency_stage_breakdown"),
        "downstream_stages": r27s.get("latency_downstream_breakdown"),
    }

    report = {
        "schema": "axo-real-world-end-to-end-evaluation/1",
        "run_id": "real-world-geometry-input-verified-simulation",
        "generated_at_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "measurement_class": "OFFLINE_DEVELOPMENT_AND_EXTERNAL_IMAGE_EVIDENCE",
        "independent_h1_validation": "NOT_MEASURED",
        "independent_generalization": "NOT_MEASURED",
        "real_student_usability": "NOT_MEASURED",
        "physical_low_end": "NOT_MEASURED",
        "live_ai_calls": 0,
        "sealed_h1_rows_opened": 0,
        "locked_w2_w3_rows_read": 0,
        "git_head": head_sha,
        "product_commit": FZ.product_commit(),
        "working_tree_dirty": dirty_product,
        "measured_system": measured_hash,
        "measured_files": measured_count,
        "cache_version": CACHE_VERSION,
        "route_d_cache_policy": ROUTE_D_CACHE_POLICY,
        "semantic_environment_hash": semantic_environment_hash(),
        "runtime_identity": runtime_identity(),
        "locked_surfaces": surfaces,
        "dataset_provenance": _build_dataset_provenance(),
        "ocr_before_after": ocr_eval,
        "understanding_planning_and_verification": {
            "nc_and_autonomous_negatives": nc_eval,
            "a4_plane_constraints_and_depth": a4_eval,
            "reasoning_matrix_72": rm_eval,
            "r1_probe_19": r1_eval,
            "exposed_dev_corpora": dev_eval,
            "real27_text_forensics": real27_forensics,
        },
        "mandatory_metrics_9_3": mandatory_metrics_9_3,
        "stage_latency_profiling_10": stage_latency_profiling_10,
        "safety_invariants": {
            "total_scene3d_continuity_errors": total_cont_errors,
            **c_safety,
        },
    }

    encoded = (json.dumps(report, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
    findings = pub_safety.findings_in(encoded)
    assert not findings, f"Publication safety violation: {findings}"
    assert ("APPROVED_BY" + "_USER") not in encoded.decode("utf-8")

    if not args.dry_run:
        out_path = RUN_DIR / "REAL_WORLD_END_TO_END_EVALUATION.json"
        out_path.write_bytes(encoded)
    sha = hashlib.sha256(encoded).hexdigest()

    r27s = (ocr_eval.get("real27_images") or {}).get("summary") or {}
    e16s = (ocr_eval.get("external16_printed_images") or {}).get("summary") or {}
    summary = {
        "surfaces_ok": surfaces["all_match"],
        "product_commit": report["product_commit"][:12],
        "measured_system": measured_hash[:16],
        "glyph_topo": f"{ocr_eval.get('glyph_topology_passed')}/{ocr_eval.get('glyph_topology_total')}",
        "rendered_pos": f"{ocr_eval.get('rendered_positive_accepted')}/{ocr_eval.get('rendered_positive_total')}",
        "adv_neg_false_accepts": ocr_eval.get("false_auto_accepts_negative"),
        "real27_cer": f"{r27s.get('cer_before_median')} -> {r27s.get('cer_after_median')}",
        "real27_decisions": r27s.get("ocr_decision_counts"),
        "real27_false_auto": r27s.get("false_auto_accepts"),
        "real27_confirmed_served": f"{r27s.get('confirmed_served')}/{r27s.get('confirmed_ready_count')} (wrong={r27s.get('confirmed_wrong_served')})",
        "real27_cold_e2e_p50_p95": (r27s.get("latency_cold_end_to_end") or {}).get("p50"),
        "real27_warm_e2e_p50_p95": (r27s.get("latency_warm_end_to_end") or {}).get("p50"),
        "ext15_cer": f"{e16s.get('cer_before_median')} -> {e16s.get('cer_after_median')}",
        "ext15_selection": f"{e16s.get('selection_served_correct')}/{e16s.get('selection_bands_tested')}",
        "r513_aligned": real27_forensics["r513_source_gate_alignment"]["verified"],
        "real27_text": f"{dev_eval['real27_text']['served']}/{dev_eval['real27_text']['total']} (wrong={dev_eval['real27_text']['wrong_served']})",
        "nc_nl": f"{nc_eval['nc_nl_passed']}/{nc_eval['nc_nl_total']}",
        "continuity_errors": total_cont_errors,
        "mode_a_ok": c_safety["mode_a_trig_no_answer_leak"],
        "json_sha256": sha[:16],
    }
    print(json.dumps(summary, ensure_ascii=False))

    ok = (
        surfaces["all_match"]
        and ocr_eval.get("glyph_topology_passed") == 12
        and ocr_eval.get("rendered_positive_accepted") == 4
        and ocr_eval.get("false_auto_accepts_negative") == 0
        and r27s.get("false_auto_accepts", 0) == 0
        and r27s.get("confirmed_wrong_served", 0) == 0
        and e16s.get("false_auto_accepts", 0) == 0
        and e16s.get("confirmed_wrong_served", 0) == 0
        and ocr_eval.get("vision_fallback_offline_mock", {}).get("passed") is True
        and ocr_eval.get("confirmation_provenance_and_cache_144", {}).get("passed") is True
        and real27_forensics["r513_source_gate_alignment"]["verified"] is True
        and nc_eval["nc_gold_passed"] == 21
        and nc_eval["nc_nl_passed"] == 21
        and nc_eval["autonomous_negatives_false_served"] == 0
        and a4_eval["all_passed"]
        and dev_eval["real27_text"]["wrong_served"] == 0
        and total_cont_errors == 0
        and c_safety["mode_a_trig_no_answer_leak"] is True
    )
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
