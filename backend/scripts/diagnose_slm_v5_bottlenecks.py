# -*- coding: utf-8 -*-
"""Phase A Root-Cause Isolation & Gold TypedFactNext /2 Intervention (AXO HYBRID /6).

Runs 100% offline (`ALLOW_LIVE_AI = "0"`, `GEMINI_API_KEY = ""`, `external_ai_calls = 0`)
against untouched /5 code (`463c6b040`) across DEV_CALIBRATION_16, SLM_INDEPENDENT_HOLDOUT_40
(`HISTORICAL_DIAGNOSTIC`), and S2-F-S07 to capture all 14 pipeline diagnostic layers plus
Test A (Local Parser), Test B (/5 minimal_ops Qwen3-0.6B), Test C_raw (Gold on raw source),
and Test C_canon (Gold on span-audited surface-canonicalized source, preserving typos).
"""

from __future__ import annotations

from collections import Counter
from datetime import datetime, timezone
import importlib.util
import json
import os
from pathlib import Path
import re
import sys
import time
from typing import Any

os.environ["ALLOW_LIVE_AI"] = "0"
os.environ["GEMINI_API_KEY"] = ""
os.environ.pop("HYBRID_ROUTE_MODE", None)

ROOT = Path(__file__).resolve().parents[2]
BACKEND = ROOT / "backend"
RUN5_DIR = ROOT / "docs/evaluation/geometry/runs/slm-local-geometry-understanding"
OUT_DIR = ROOT / "docs/evaluation/geometry/runs/specialized-geometry-extraction-slm-optimization"

if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))
if str(BACKEND / "scripts") not in sys.path:
    sys.path.insert(0, str(BACKEND / "scripts"))


def _load_mod(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, str(path))
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


ESC = _load_mod("_eval_slm_v5_mod", BACKEND / "scripts" / "evaluate_slm_campaign.py")

# Re-enforce offline state after imports
os.environ["ALLOW_LIVE_AI"] = "0"
os.environ["GEMINI_API_KEY"] = ""

from app.ai import adaptive_input_router as AIR  # noqa: E402
from app.ai.adapter4_route import run_typed_fact_next_v2_route  # noqa: E402
from app.ai.hybrid_offline import hybrid_offline_policy, run_hybrid_offline  # noqa: E402
from app.ai.local_geometry_parser import clear_local_geometry_parser_cache, normalize_problem_text, parse_geometry_problem_locally  # noqa: E402
from app.ai.local_slm_extractor import (  # noqa: E402
    _build_minimal_ops_messages,
    MINIMAL_OPS_JSON_SCHEMA,
    index_source_clauses,
    validate_and_lower_minimal_ops,
)
from app.ai.local_slm_runtime import DEFAULT_LOCAL_SLM_MODEL_KEY, LocalSlmRuntime  # noqa: E402
from app.ai.typed_fact_next_extraction import ReplayExtractor, _normalize_transport_payload, to_wire_typed_fact_next_v2  # noqa: E402


# ---------------------------------------------------------------------------
# Span-audited conservative surface canonicalizer (for Test C_canon ablation;
# NEVER rewrites diacritic typos like "vuôg", "vuông goc", or "Hình chop")
# ---------------------------------------------------------------------------
def _surface_canonicalize(text: str) -> tuple[str, list[dict[str, Any]], list[str]]:
    cur = normalize_problem_text(text or "")
    applied: list[dict[str, Any]] = []
    typo_flags: list[str] = []

    typo_checks = (
        ("TYPO_VUONG_GOC_TONE", r"\bvuông\s+goc\b|\bvuôg\s+góc\b"),
        ("TYPO_CHOP_TONE", r"\b(?:hình|khối)\s+chop\b"),
        ("TYPO_DEN_TONE", r"\bđên\b"),
    )
    for tag, pat in typo_checks:
        if re.search(pat, cur, re.IGNORECASE):
            typo_flags.append(tag)
    if typo_flags:
        return cur, applied, typo_flags

    def _sub(rule_id: str, pattern: str, repl: Any, *, count: int = 0, flags: int = re.IGNORECASE) -> None:
        nonlocal cur
        nxt = re.sub(pattern, repl, cur, count=count, flags=flags)
        if nxt != cur:
            applied.append({"rule_id": rule_id, "before": cur, "after": nxt})
            cur = nxt

    _sub("VN01_PARENS", r"\(\s*([A-Z0-9']+)\s*\)", r"(\1)", flags=0)
    _sub("VN01_PUNCT_SPACE", r"\s+([,.;:!?])", r"\1", flags=0)
    _sub("VN01_DEG_WORD", r"(\d+)\s*độ\b", r"\1°")
    _sub(
        "VN02_CONV_PREFIX",
        r"^\s*(?:Em đang ôn tập[^:]+:|Nhờ Axo giải giúp bài này:|Thưa thầy,\s*|Cho mình hỏi bài này với:|Bài tập hình \d+:)\s*(?:bài\s+cho\s+)?",
        "Cho ",
        count=1,
    )
    _sub("VN02_DEDUP_CHO", r"^\s*Cho\s+(?:cho|xét)\s+", "Cho ", count=1)
    _sub(
        "VN03_TRONG_XET",
        r"^\s*(?:Trong|Xét)\s+(hình|khối|lăng)\s+",
        lambda m: f"Cho {m.group(1).lower()} ",
        count=1,
    )
    _sub("VN03_BARE_CHOP", r"^Cho\s+chóp\s+", "Cho hình chóp ", count=1)
    _sub("VN03_BARE_PRISM", r"^(?:Cho\s+)?(lăng\s+trụ\s+(?:đứng|đều)\b)", r"Cho hình \1", count=1)
    _sub(
        "VN04_NHAN_SHAPE_POLY_DAY",
        r"nhận\s+(hình\s+vuông|hình\s+chữ\s+nhật|tam\s+giác\s+(?:đều|vuông(?:\s+tại\s+[A-Z0-9']+)?))\s+([A-Z0-9']+)\s+(?:có\s+)?(?:độ\s+dài\s+)?cạnh\s+(?:bằng\s+)?([^\s,.;]+)\s+làm\s+(?:mặt\s+)?đáy",
        r"có đáy \2 là \1 cạnh \3",
    )
    _sub(
        "VN04_NHAN_POLY_SHAPE",
        r"nhận\s+([A-Z0-9']+)\s+làm\s+(hình\s+vuông|hình\s+chữ\s+nhật)\s+cạnh\s+([^\s,.;]+)",
        r"có đáy \1 là \2 cạnh \3",
    )
    _sub(
        "VN04_NHAN_IMPLICIT_TRI",
        r"(lăng\s+trụ\s+đứng\s+([A-Z0-9']+)\.([A-Z0-9']+))\s+nhận\s+(tam\s+giác\s+đều)\s+cạnh\s+([^\s,.;]+)\s+làm\s+đáy",
        r"\1 có đáy \2 là \4 cạnh \5",
    )
    _sub(
        "VN04_NHAN_IMPLICIT_SQ",
        r"(chóp\s+[A-Z0-9']+\.([A-Z0-9']+))\s+nhận\s+(hình\s+vuông)\s+cạnh\s+([^\s,.;]+)\s+làm\s+đáy\s+\2",
        r"\1 có đáy \2 là \3 cạnh \4",
    )
    _sub(
        "VN04_BARE_CO_ABCD_SQ",
        r"(chóp\s+[A-Z0-9']+\.([A-Z0-9']+))\s+có\s+\2\s+là\s+(hình\s+vuông)\s+cạnh\s+([^\s,.;]+)",
        r"\1 có đáy \2 là \3 cạnh \4",
    )
    _sub(
        "VN04_MAT_DAY_DO_DAI",
        r"(?:mặt\s+)?đáy\s+([A-Z0-9']+)\s+là\s+(tam\s+giác\s+đều)\s+độ\s+dài\s+cạnh\s+([^\s,.;]+)",
        r"đáy \1 là \2 cạnh \3",
    )
    _sub(
        "VN04_DAY_DEU_CANH",
        r"\b(đ|Đ)áy\s+([A-Z0-9']+)\s+đều\s+cạnh\s+([^\s,.;]+)",
        lambda m: f"{m.group(1)}áy {m.group(2)} là tam giác đều cạnh {m.group(3)}",
    )
    _sub(
        "VN04_REG_PYR_BASE",
        r"(chóp\s+(?:tam\s+giác\s+|tứ\s+giác\s+)?đều\s+[A-Z0-9']+\.[A-Z0-9']+),?\s*(?:có\s+)?đáy\s+[A-Z0-9']+\s+(?:có\s+)?cạnh\s+(?:bằng\s+|=)?([^\s,.;]+)",
        r"\1 có cạnh đáy bằng \2",
    )
    _sub(
        "VN05_ALL_LATERAL",
        r"(?:tất\s+cả\s+)?(?:các\s+)?cạnh\s+bên\s+đều\s+(?:bằng|dài)\s+([^\s,.;]+)",
        r"cạnh bên bằng \1",
    )
    _sub("VN05_CANC_DO_DAI", r"cạnh\s+bên\s+([A-Z0-9']+)\s+có\s+độ\s+dài\s+bằng\s+([^\s,.;]+)", r"\1=\2")
    _sub(
        "VN05_CON_THI",
        r",\s*còn\s+([A-Z0-9']+)\s+thì\s+(vuông\s+góc\s+(?:với\s+)?|\=)",
        lambda m: f", {m.group(1)} {m.group(2)}",
    )
    _sub("VN05_DONG_THOI", r",?\s*đồng\s+thời\s+(?:cạnh\s+bên\s+|độ\s+dài\s+đoạn\s+)?", ", ")
    _sub("VN05_THANG_DUNG", r"thẳng\s+đứng\s+vuông\s+góc", "vuông góc")
    _sub(
        "VN05_NAM_TRONG_FACE",
        r"(Mặt\s+bên\s+[A-Z0-9']+)\s+(?:là\s+tam\s+giác\s+)?đều\s+và\s+nằm\s+trong\s+mặt\s+phẳng\s+vuông\s+góc\s+với\s+(?:mặt\s+)?đáy\s+([A-Z0-9']+)",
        r"\1 là tam giác đều và vuông góc với đáy \2",
    )
    _sub("VN05_GOC_TAO_BOI", r"góc\s+tạo\s+bởi\s+", "góc giữa ")
    _sub("VN05_DO_DUOC", r"đo\s+được\s+(?=\d)", "bằng ")
    _sub(
        "VN05_BIET_CENTROID",
        r"\bBiết\s+([A-Z][0-9']*)\s+là\s+trọng\s+tâm\s+tam\s+giác\s+([A-Z]+)\s+và\s+",
        r"Gọi \1 là trọng tâm tam giác \2, ",
    )
    _sub(
        "VN05_DAT_MID",
        r"Đặt\s+([A-Z][0-9']*)\s+là\s+điểm\s+chính\s+giữa\s+(?:cạnh\s+)?([A-Z0-9']+)\s+trong\s+(hình\s+chóp\s+[A-Z0-9']+\.[A-Z0-9']+)\.",
        r"Cho \3, gọi \1 là trung điểm \2.",
    )
    _sub("VN05_DO_DAI_DOAN_BANG", r"(?:độ\s+dài\s+(?:đoạn\s+)?|cạnh\s+)([A-Z0-9']+)\s+(?:có\s+độ\s+dài\s+)?bằng\s+([^\s,.;]+)", r"\1=\2")
    _sub("VN05_DUONG_CAO_SA_VUONG", r"Đường\s+cao\s+([A-Z0-9']+)\s+vuông\s+góc\s+với\s+(\([A-Z0-9']+\))\s+với\s+độ\s+dài\s+([A-Z0-9']+=[^\s,.;]+)", r"\1 vuông góc với \2, \3")
    _sub("VN05_CHIEU_CAO_PRISM", r",\s*chiều\s+cao\s+([A-Z0-9']+=[^\s,.;]+)", r", \1")
    _sub("VN05_SEG_BANG", r"\b([A-Z][0-9']*'?[A-Z][0-9']*'?)\s+bằng\s+([^\s,.;]+)", r"\1=\2")
    _sub("VN05_YEU_CAU", r"Yêu\s+cầu\s+(?:xác\s+định|tính)\b", "Tính")
    _sub("VN05_HAY_TIM", r"\b(?:Hãy\s+(?:xác\s+định|tìm|tính)|Tìm)\s+(?=thể\s+tích|khoảng\s+cách|góc|diện\s+tích|độ\s+dài)", "Tính ")
    _sub("VN05_GOAL_DA_CHO", r"thể\s+tích\s+của\s+khối\s+(chóp|lăng\s+trụ|hộp)\s+đã\s+cho", lambda m: f"thể tích khối {m.group(1)}")
    return cur, applied, typo_flags


def _mk_gold(
    text: str,
    *,
    solid: tuple[str, str, str],
    premises: list[tuple[str, dict[str, Any], str]],
    goals: list[tuple[str, str, dict[str, Any], str]],
    unit: str = "a",
) -> dict[str, Any]:
    return {
        "schema_version": "typed-fact-next/2",
        "problem_text": text,
        "length_unit": unit,
        "solids": [{"solid_id": "s1", "solid_type": solid[0], "notation": solid[1], "quote": solid[2]}],
        "premises": [{"kind": k, "args": a, "quote": q, "solid_id": "s1"} for k, a, q in premises],
        "relations": [],
        "derived_sections": [],
        "simulation_goals": [{"goal_id": "sg1", "kind": "construct_object", "target_solid_id": "s1", "quote": solid[2]}],
        "math_goals": [
            {"goal_id": f"q{i+1}", "kind": gk, "goal_type": gt, "target": tgt, "solid_id": "s1", "quote": gq}
            for i, (gk, gt, tgt, gq) in enumerate(goals)
        ],
    }


def _find_q(text: str, *candidates: str) -> str:
    for cand in candidates:
        if cand in text:
            return cand
    return text


def build_gold_payload(case_id: str, text: str) -> dict[str, Any]:
    """Hand-authored, verbatim-grounded Gold TypedFactNext /2 specs for all 38 DEV_CAL+HOLDOUT positives."""
    specs: dict[str, tuple[tuple[str, str, str], list[tuple[str, dict[str, Any], str]], list[tuple[str, str, dict[str, Any], str]], str]] = {
        # --- DEV_CALIBRATION_16 positives (10) ---
        "cal_p01_pyramid_vol": (
            ("pyramid", "S.ABC", _find_q(text, "Cho hình chóp S.ABC")),
            [
                ("regular_polygon", {"vertices": ["A", "B", "C"], "side": "a"}, _find_q(text, "đáy ABC là tam giác đều cạnh a", "đáy ABC đều cạnh a")),
                ("perpendicular_line_plane", {"line": ["S", "A"], "plane": ["A", "B", "C"]}, _find_q(text, "SA vuông góc (ABC)")),
                ("segment_length", {"segment": ["S", "A"], "value": "2a"}, _find_q(text, "SA=2a")),
            ],
            [("measurement", "volume", {"solid_id": "s1"}, _find_q(text, "Tính thể tích khối chóp S.ABC."))],
            "a",
        ),
        "cal_p02_dist_split": (
            ("pyramid", "S.ABC", _find_q(text, "Cho hình chóp S.ABC", "Xét hình chóp S.ABC.")),
            [
                ("regular_polygon", {"vertices": ["A", "B", "C"], "side": "a"}, _find_q(text, "Tam giác ABC đều có cạnh bằng a.", "Tam giác ABC đều có cạnh bằng a")),
                ("perpendicular_line_plane", {"line": ["S", "A"], "plane": ["A", "B", "C"]}, _find_q(text, "Đường thẳng SA vuông góc với mặt phẳng (ABC)", "SA vuông góc với mặt phẳng (ABC)")),
                ("segment_length", {"segment": ["S", "A"], "value": "2a"}, _find_q(text, "độ dài đoạn SA bằng 2a.", "SA=2a")),
            ],
            [("measurement", "distance", {"point": "A", "plane": ["S", "B", "C"]}, _find_q(text, "Tính khoảng cách từ A đến mặt phẳng (SBC).", "Hãy xác định khoảng cách từ A đến mặt phẳng (SBC)."))],
            "a",
        ),
        "cal_p03_sq_pyramid_angle": (
            ("pyramid", "S.ABCD", _find_q(text, "Cho chóp S.ABCD", "Khối chóp S.ABCD")),
            [
                ("regular_polygon", {"vertices": ["A", "B", "C", "D"], "side": "a"}, _find_q(text, "có đáy ABCD là hình vuông cạnh a", "nhận ABCD làm hình vuông cạnh a.")),
                ("perpendicular_line_plane", {"line": ["S", "A"], "plane": ["A", "B", "C", "D"]}, _find_q(text, "Cạnh SA vuông góc với đáy", "SA vuông góc với đáy")),
                ("line_plane_angle", {"line": ["S", "C"], "plane": ["A", "B", "C", "D"], "value": "45", "unit": "deg"}, _find_q(text, "góc giữa SC và (ABCD) bằng 45°", "góc tạo bởi SC và (ABCD) đo được 45 độ.")),
            ],
            [("measurement", "volume", {"solid_id": "s1"}, _find_q(text, "Tính thể tích khối chóp S.ABCD."))],
            "a",
        ),
        "cal_p04_midpoint_dist": (
            ("pyramid", "S.ABC", _find_q(text, "Cho hình chóp S.ABC", "Đặt M là điểm chính giữa cạnh SC trong hình chóp S.ABC.")),
            [
                ("midpoint", {"point": "M", "segment": ["S", "C"]}, _find_q(text, "M là trung điểm SC", "Đặt M là điểm chính giữa cạnh SC")),
                ("right_angle", {"vertex": "B", "rays": ["A", "C"]}, _find_q(text, "Tam giác đáy ABC vuông tại B")),
                ("segment_length", {"segment": ["A", "B"], "value": "a"}, _find_q(text, "AB=a")),
                ("segment_length", {"segment": ["B", "C"], "value": "a√3"}, _find_q(text, "BC=a√3")),
                ("perpendicular_line_plane", {"line": ["S", "A"], "plane": ["A", "B", "C"]}, _find_q(text, "SA vuông góc mặt đáy (ABC)")),
                ("segment_length", {"segment": ["S", "A"], "value": "a"}, _find_q(text, "SA=a")),
            ],
            [("measurement", "distance", {"point": "M", "plane": ["A", "B", "C"]}, _find_q(text, "Tính khoảng cách từ M đến (ABC)."))],
            "a",
        ),
        "cal_p05_regular_pyr_vol": (
            ("pyramid", "S.ABC", _find_q(text, "Cho hình chóp tam giác đều S.ABC")),
            [
                ("regular_pyramid", {"apex": "S", "base": ["A", "B", "C"]}, _find_q(text, "Cho hình chóp tam giác đều S.ABC")),
                ("regular_polygon", {"vertices": ["A", "B", "C"], "side": "a"}, _find_q(text, "Cho hình chóp tam giác đều S.ABC có cạnh đáy là a", "có cạnh đáy là a")),
                ("segment_length", {"segment": ["S", "A"], "value": "a"}, _find_q(text, "cạnh bên bằng a", "tất cả các cạnh bên đều bằng a.")),
            ],
            [("measurement", "volume", {"solid_id": "s1"}, _find_q(text, "Tính thể tích khối chóp S.ABC."))],
            "a",
        ),
        "cal_p06_right_prism": (
            ("prism", "ABC.A'B'C'", _find_q(text, "Cho hình lăng trụ đứng ABC.A'B'C'", "Xét lăng trụ đứng ABC.A'B'C'.")),
            [
                ("right_prism", {"base": ["A", "B", "C"], "top": ["A'", "B'", "C'"]}, _find_q(text, "Cho hình lăng trụ đứng ABC.A'B'C'", "Xét lăng trụ đứng ABC.A'B'C'.")),
                ("regular_polygon", {"vertices": ["A", "B", "C"], "side": "a"}, _find_q(text, "Đáy ABC là tam giác đều cạnh a", "Đáy ABC đều cạnh a")),
                ("segment_length", {"segment": ["A", "A'"], "value": "a√3"}, _find_q(text, "AA'=a√3", "cạnh bên AA' có độ dài bằng a√3.")),
            ],
            [("measurement", "volume", {"solid_id": "s1"}, _find_q(text, "Tính thể tích của khối lăng trụ ABC.A'B'C'.", "Tìm thể tích của khối lăng trụ ABC.A'B'C'."))],
            "a",
        ),
        "cal_p07_face_perp_base": (
            ("pyramid", "S.ABCD", _find_q(text, "Cho hình chóp S.ABCD", "Hình chóp S.ABCD")),
            [
                ("regular_polygon", {"vertices": ["A", "B", "C", "D"], "side": "a"}, _find_q(text, "có đáy ABCD là hình vuông cạnh a", "nhận hình vuông cạnh a làm đáy ABCD.")),
                ("regular_polygon", {"vertices": ["S", "A", "B"]}, _find_q(text, "Mặt bên SAB là tam giác đều", "Mặt bên SAB đều")),
                ("face_perpendicular_base", {"face": ["S", "A", "B"], "base": ["A", "B", "C", "D"]}, _find_q(text, "Mặt bên SAB là tam giác đều và vuông góc với đáy ABCD.", "Mặt bên SAB đều và nằm trong mặt phẳng vuông góc với đáy ABCD.")),
            ],
            [("measurement", "volume", {"solid_id": "s1"}, _find_q(text, "Tính thể tích khối chóp S.ABCD."))],
            "a",
        ),
        "cal_p08_s2_f_typo": (
            ("pyramid", "S.ABCD", _find_q(text, "Cho hình chóp S.ABCD")),
            [
                ("regular_polygon", {"vertices": ["A", "B", "C", "D"], "side": "a"}, _find_q(text, "đáy ABCD là hình vuông cạnh a")),
                ("perpendicular_line_plane", {"line": ["S", "A"], "plane": ["A", "B", "C", "D"]}, _find_q(text, "SA vuôg góc với đáy")),
                ("segment_length", {"segment": ["S", "A"], "value": "2a"}, _find_q(text, "SA = 2a")),
            ],
            [("measurement", "volume", {"solid_id": "s1"}, _find_q(text, "Tính thể tích khối chóp S.ABCD."))],
            "a",
        ),
        "cal_p09_dihedral_dist": (
            ("pyramid", "S.ABCD", _find_q(text, "Cho hình chóp S.ABCD", "Cho chóp S.ABCD")),
            [
                ("regular_polygon", {"vertices": ["A", "B", "C", "D"], "side": "a"}, _find_q(text, "có đáy ABCD là hình vuông cạnh a.", "ABCD là hình vuông cạnh a.")),
                ("perpendicular_line_plane", {"line": ["S", "A"], "plane": ["A", "B", "C", "D"]}, _find_q(text, "Đường thẳng SA vuông góc với mặt phẳng đáy (ABCD)")),
                ("plane_plane_angle", {"plane1": ["S", "B", "C"], "plane2": ["A", "B", "C", "D"], "value": "60", "unit": "deg"}, _find_q(text, "góc giữa (SBC) và (ABCD) là 60°.", "góc giữa (SBC) và (ABCD) là 60 độ.")),
            ],
            [("measurement", "distance", {"point": "A", "plane": ["S", "B", "C"]}, _find_q(text, "Tính khoảng cách từ A đến (SBC)."))],
            "a",
        ),
        "cal_p10_conversational": (
            ("pyramid", "S.ABC", _find_q(text, "cho hình chóp S.ABC", "Cho hình chóp S.ABC")),
            [
                ("right_angle", {"vertex": "A", "rays": ["B", "C"]}, _find_q(text, "đáy ABC vuông tại A")),
                ("segment_length", {"segment": ["A", "B"], "value": "a"}, _find_q(text, "AB=a")),
                ("segment_length", {"segment": ["A", "C"], "value": "2a"}, _find_q(text, "AC=2a.")),
                ("perpendicular_line_plane", {"line": ["S", "A"], "plane": ["A", "B", "C"]}, _find_q(text, "Cạnh SA vuông góc với đáy")),
                ("segment_length", {"segment": ["S", "A"], "value": "3a"}, _find_q(text, "SA=3a.")),
            ],
            [("measurement", "volume", {"solid_id": "s1"}, _find_q(text, "Tính thể tích khối chóp S.ABC.", "Tìm thể tích khối chóp S.ABC."))],
            "a",
        ),
        # --- HOLDOUT_40 positives (28) ---
        "slm_h01_natural_pyramid_vol": (
            ("pyramid", "S.ABC", _find_q(text, "Cho khối chóp S.ABC")),
            [
                ("regular_polygon", {"vertices": ["A", "B", "C"], "side": "a"}, _find_q(text, "đáy ABC là tam giác đều cạnh a.", "mặt đáy ABC là tam giác đều độ dài cạnh a.")),
                ("perpendicular_line_plane", {"line": ["S", "A"], "plane": ["A", "B", "C"]}, _find_q(text, "Đường thẳng SA vuông góc đáy")),
                ("segment_length", {"segment": ["S", "A"], "value": "3a"}, _find_q(text, "SA=3a", "SA bằng 3a.")),
            ],
            [("measurement", "volume", {"solid_id": "s1"}, _find_q(text, "Tính thể tích khối chóp S.ABC."))],
            "a",
        ),
        "slm_h02_square_base_alt_order": (
            ("pyramid", "S.ABCD", _find_q(text, "Cho hình chóp S.ABCD", "Xét hình chóp S.ABCD")),
            [
                ("regular_polygon", {"vertices": ["A", "B", "C", "D"], "side": "2a"}, _find_q(text, "có đáy ABCD là hình vuông cạnh 2a.", "nhận hình vuông ABCD có cạnh 2a làm đáy.")),
                ("perpendicular_line_plane", {"line": ["S", "A"], "plane": ["A", "B", "C", "D"]}, _find_q(text, "cạnh bên SA vuông góc với (ABCD)")),
                ("segment_length", {"segment": ["S", "A"], "value": "a"}, _find_q(text, "SA=a.")),
            ],
            [("measurement", "volume", {"solid_id": "s1"}, _find_q(text, "Tính thể tích của khối chóp đã cho."))],
            "a",
        ),
        "slm_h03_right_isosceles_dist": (
            ("pyramid", "S.ABC", _find_q(text, "Cho hình chóp S.ABC", "Trong hình chóp S.ABC")),
            [
                ("right_angle", {"vertex": "A", "rays": ["B", "C"]}, _find_q(text, "tam giác đáy ABC vuông cân tại A")),
                ("equal_length", {"segment_a": ["A", "B"], "segment_b": ["A", "C"]}, _find_q(text, "tam giác đáy ABC vuông cân tại A")),
                ("segment_length", {"segment": ["A", "B"], "value": "a"}, _find_q(text, "AB=a")),
                ("perpendicular_line_plane", {"line": ["S", "A"], "plane": ["A", "B", "C"]}, _find_q(text, "SA vuông góc với mặt phẳng (ABC)", "còn SA thì vuông góc với mặt phẳng (ABC)")),
                ("segment_length", {"segment": ["S", "A"], "value": "a√2"}, _find_q(text, "SA=a√2.")),
            ],
            [("measurement", "distance", {"point": "A", "plane": ["S", "B", "C"]}, _find_q(text, "Tính khoảng cách từ A tới mặt phẳng (SBC).", "Hãy tìm khoảng cách từ A tới mặt phẳng (SBC)."))],
            "a",
        ),
        "slm_h04_right_prism_mnp": (
            ("prism", "MNP.M'N'P'", _find_q(text, "Cho khối lăng trụ đứng MNP.M'N'P'", "Cho Khối lăng trụ đứng MNP.M'N'P'", "Khối lăng trụ đứng MNP.M'N'P'")),
            [
                ("right_prism", {"base": ["M", "N", "P"], "top": ["M'", "N'", "P'"]}, _find_q(text, "Cho khối lăng trụ đứng MNP.M'N'P'", "Cho Khối lăng trụ đứng MNP.M'N'P'", "Khối lăng trụ đứng MNP.M'N'P'")),
                ("right_angle", {"vertex": "M", "rays": ["N", "P"]}, _find_q(text, "đáy MNP là tam giác vuông tại M")),
                ("segment_length", {"segment": ["M", "N"], "value": "a"}, _find_q(text, "MN=a")),
                ("segment_length", {"segment": ["M", "P"], "value": "2a"}, _find_q(text, "MP=2a")),
                ("segment_length", {"segment": ["M", "M'"], "value": "3a"}, _find_q(text, "MM'=3a.", "chiều cao MM'=3a.")),
            ],
            [("measurement", "volume", {"solid_id": "s1"}, _find_q(text, "Tính thể tích khối lăng trụ MNP.M'N'P'."))],
            "a",
        ),
        "slm_h05_regular_square_pyramid": (
            ("pyramid", "S.MNPQ", _find_q(text, "Cho hình chóp tứ giác đều S.MNPQ")),
            [
                ("regular_pyramid", {"apex": "S", "base": ["M", "N", "P", "Q"]}, _find_q(text, "Cho hình chóp tứ giác đều S.MNPQ")),
                ("regular_polygon", {"vertices": ["M", "N", "P", "Q"], "side": "a"}, _find_q(text, "Cho hình chóp tứ giác đều S.MNPQ có cạnh đáy bằng a", "Cho hình chóp tứ giác đều S.MNPQ, đáy MNPQ có cạnh bằng a")),
                ("segment_length", {"segment": ["S", "M"], "value": "a"}, _find_q(text, "cạnh bên SM=a.")),
            ],
            [("measurement", "volume", {"solid_id": "s1"}, _find_q(text, "Tính thể tích khối chóp S.MNPQ.", "Hãy tính thể tích khối chóp S.MNPQ."))],
            "a",
        ),
        "slm_h06_regular_tri_pyramid_dist": (
            ("pyramid", "S.ABC", _find_q(text, "Cho Hình chóp tam giác đều S.ABC", "Cho hình chóp tam giác đều S.ABC", "Hình chóp tam giác đều S.ABC")),
            [
                ("regular_pyramid", {"apex": "S", "base": ["A", "B", "C"]}, _find_q(text, "Cho Hình chóp tam giác đều S.ABC", "Cho hình chóp tam giác đều S.ABC", "Hình chóp tam giác đều S.ABC")),
                ("regular_polygon", {"vertices": ["A", "B", "C"], "side": "a"}, _find_q(text, "Cho Hình chóp tam giác đều S.ABC có cạnh đáy bằng a", "Cho hình chóp tam giác đều S.ABC có cạnh đáy bằng a", "Hình chóp tam giác đều S.ABC có cạnh đáy bằng a", "có đáy ABC cạnh a")),
                ("segment_length", {"segment": ["S", "A"], "value": "2a"}, _find_q(text, "cạnh bên bằng 2a", "các cạnh bên đều dài 2a.")),
            ],
            [("measurement", "distance", {"point": "A", "plane": ["S", "B", "C"]}, _find_q(text, "Tính khoảng cách từ điểm A đến mặt phẳng (SBC).", "Tìm khoảng cách từ điểm A đến mặt phẳng (SBC)."))],
            "a",
        ),
        "slm_h07_conversational_student": (
            ("pyramid", "S.ABCD", _find_q(text, "cho hình chóp S.ABCD", "Cho hình chóp S.ABCD")),
            [
                ("regular_polygon", {"vertices": ["A", "B", "C", "D"], "side": "a"}, _find_q(text, "đáy ABCD là hình vuông cạnh a.")),
                ("perpendicular_line_plane", {"line": ["S", "A"], "plane": ["A", "B", "C", "D"]}, _find_q(text, "SA vuông góc với đáy (ABCD)")),
                ("segment_length", {"segment": ["S", "A"], "value": "a√3"}, _find_q(text, "SA=a√3.")),
            ],
            [("measurement", "distance", {"point": "A", "plane": ["S", "B", "C"]}, _find_q(text, "Tính khoảng cách từ A đến (SBC)."))],
            "a",
        ),
        "slm_h08_textbook_label_prefix": (
            ("pyramid", "S.ABC", _find_q(text, "Cho hình chóp S.ABC", "xét hình chóp S.ABC")),
            [
                ("right_angle", {"vertex": "B", "rays": ["A", "C"]}, _find_q(text, "tam giác ABC vuông tại B")),
                ("segment_length", {"segment": ["A", "B"], "value": "a"}, _find_q(text, "AB=a")),
                ("segment_length", {"segment": ["B", "C"], "value": "a√3"}, _find_q(text, "BC=a√3.")),
                ("perpendicular_line_plane", {"line": ["S", "A"], "plane": ["A", "B", "C"]}, _find_q(text, "SA vuông góc với (ABC)")),
                ("segment_length", {"segment": ["S", "A"], "value": "2a"}, _find_q(text, "SA=2a.")),
            ],
            [("measurement", "volume", {"solid_id": "s1"}, _find_q(text, "Tính thể tích khối chóp S.ABC."))],
            "a",
        ),
        "slm_h09_polite_rectangle_base": (
            ("pyramid", "S.ABCD", _find_q(text, "Cho hình chóp S.ABCD", "bài cho hình chóp S.ABCD")),
            [
                ("rectangle", {"vertices": ["A", "B", "C", "D"]}, _find_q(text, "đáy ABCD là hình chữ nhật")),
                ("segment_length", {"segment": ["A", "B"], "value": "a"}, _find_q(text, "AB=a")),
                ("segment_length", {"segment": ["A", "D"], "value": "2a"}, _find_q(text, "AD=2a.")),
                ("perpendicular_line_plane", {"line": ["S", "A"], "plane": ["A", "B", "C", "D"]}, _find_q(text, "Cạnh SA vuông góc với mặt đáy")),
                ("segment_length", {"segment": ["S", "A"], "value": "a√5"}, _find_q(text, "SA=a√5.")),
            ],
            [("measurement", "volume", {"solid_id": "s1"}, _find_q(text, "Tính thể tích khối chóp S.ABCD.", "Yêu cầu xác định thể tích khối chóp S.ABCD."))],
            "a",
        ),
        "slm_h10_colloquial_prism": (
            ("prism", "ABC.A'B'C'", _find_q(text, "hình lăng trụ đứng ABC.A'B'C'", "lăng trụ đứng ABC.A'B'C'")),
            [
                ("right_prism", {"base": ["A", "B", "C"], "top": ["A'", "B'", "C'"]}, _find_q(text, "hình lăng trụ đứng ABC.A'B'C'", "lăng trụ đứng ABC.A'B'C'")),
                ("regular_polygon", {"vertices": ["A", "B", "C"], "side": "2a"}, _find_q(text, "lăng trụ đứng ABC.A'B'C' có đáy ABC là tam giác đều cạnh 2a", "lăng trụ đứng ABC.A'B'C' nhận tam giác đều cạnh 2a làm đáy")),
                ("segment_length", {"segment": ["A", "A'"], "value": "a"}, _find_q(text, "AA'=a.", "độ dài cạnh bên AA' bằng a.")),
            ],
            [("measurement", "volume", {"solid_id": "s1"}, _find_q(text, "Tính thể tích lăng trụ ABC.A'B'C'."))],
            "a",
        ),
        "slm_h11_cuboid_paraphrase": (
            ("prism", "ABCD.A'B'C'D'", _find_q(text, "Cho hình hộp chữ nhật ABCD.A'B'C'D'", "Xét hình hộp chữ nhật ABCD.A'B'C'D'")),
            [
                ("right_prism", {"base": ["A", "B", "C", "D"], "top": ["A'", "B'", "C'", "D'"]}, _find_q(text, "Cho hình hộp chữ nhật ABCD.A'B'C'D'", "Xét hình hộp chữ nhật ABCD.A'B'C'D'")),
                ("rectangle", {"vertices": ["A", "B", "C", "D"]}, _find_q(text, "Cho hình hộp chữ nhật ABCD.A'B'C'D'", "Xét hình hộp chữ nhật ABCD.A'B'C'D'")),
                ("segment_length", {"segment": ["A", "B"], "value": "a"}, _find_q(text, "AB=a")),
                ("segment_length", {"segment": ["A", "D"], "value": "2a"}, _find_q(text, "AD=2a")),
                ("segment_length", {"segment": ["A", "A'"], "value": "3a"}, _find_q(text, "AA'=3a.")),
            ],
            [("measurement", "volume", {"solid_id": "s1"}, _find_q(text, "Tính thể tích của khối hộp ABCD.A'B'C'D'.", "Hãy xác định thể tích của khối hộp ABCD.A'B'C'D'."))],
            "a",
        ),
        "slm_h12_line_plane_angle_45": (
            ("pyramid", "S.ABC", _find_q(text, "Cho hình chóp S.ABC")),
            [
                ("right_angle", {"vertex": "B", "rays": ["A", "C"]}, _find_q(text, "đáy ABC là tam giác vuông tại B")),
                ("segment_length", {"segment": ["A", "B"], "value": "a"}, _find_q(text, "AB=a")),
                ("segment_length", {"segment": ["B", "C"], "value": "a"}, _find_q(text, "BC=a.")),
                ("perpendicular_line_plane", {"line": ["S", "A"], "plane": ["A", "B", "C"]}, _find_q(text, "Cạnh SA vuông góc với mặt đáy")),
                ("line_plane_angle", {"line": ["S", "C"], "plane": ["A", "B", "C"], "value": "45", "unit": "deg"}, _find_q(text, "góc giữa SC với mặt đáy (ABC) bằng 45°.")),
            ],
            [("measurement", "volume", {"solid_id": "s1"}, _find_q(text, "Tính thể tích khối chóp S.ABC."))],
            "a",
        ),
        "slm_h13_line_plane_angle_60": (
            ("pyramid", "S.ABCD", _find_q(text, "Cho hình chóp S.ABCD", "Xét hình chóp S.ABCD")),
            [
                ("regular_polygon", {"vertices": ["A", "B", "C", "D"], "side": "a"}, _find_q(text, "đáy ABCD là hình vuông cạnh a")),
                ("perpendicular_line_plane", {"line": ["S", "A"], "plane": ["A", "B", "C", "D"]}, _find_q(text, "SA vuông góc với (ABCD).")),
                ("line_plane_angle", {"line": ["S", "D"], "plane": ["A", "B", "C", "D"], "value": "60", "unit": "deg"}, _find_q(text, "góc giữa đường thẳng SD và mặt đáy (ABCD) bằng 60°.")),
            ],
            [("measurement", "volume", {"solid_id": "s1"}, _find_q(text, "Tính thể tích khối chóp S.ABCD."))],
            "a",
        ),
        "slm_h14_face_perp_base_split": (
            ("pyramid", "S.ABCD", _find_q(text, "Cho Hình chóp S.ABCD", "Hình chóp S.ABCD")),
            [
                ("regular_polygon", {"vertices": ["A", "B", "C", "D"], "side": "2a"}, _find_q(text, "đáy ABCD là hình vuông cạnh 2a.")),
                ("regular_polygon", {"vertices": ["S", "A", "B"]}, _find_q(text, "Mặt bên SAB là tam giác đều")),
                ("face_perpendicular_base", {"face": ["S", "A", "B"], "base": ["A", "B", "C", "D"]}, _find_q(text, "Mặt bên SAB là tam giác đều và vuông góc với đáy ABCD.")),
            ],
            [("measurement", "volume", {"solid_id": "s1"}, _find_q(text, "Tính thể tích khối chóp S.ABCD."))],
            "a",
        ),
        "slm_h15_plane_plane_angle_30": (
            ("pyramid", "S.ABC", _find_q(text, "Cho hình chóp S.ABC")),
            [
                ("regular_polygon", {"vertices": ["A", "B", "C"], "side": "2a"}, _find_q(text, "đáy ABC là tam giác đều cạnh 2a.")),
                ("perpendicular_line_plane", {"line": ["S", "A"], "plane": ["A", "B", "C"]}, _find_q(text, "Đường thẳng SA vuông góc với (ABC)")),
                ("plane_plane_angle", {"plane1": ["S", "B", "C"], "plane2": ["A", "B", "C"], "value": "30", "unit": "deg"}, _find_q(text, "góc giữa hai mặt phẳng (SBC) và (ABC) bằng 30°.", "góc giữa hai mặt phẳng (SBC) và (ABC) đo được 30°.")),
            ],
            [("measurement", "distance", {"point": "A", "plane": ["S", "B", "C"]}, _find_q(text, "Tính khoảng cách từ A đến (SBC)."))],
            "a",
        ),
        "slm_h16_cube_2a": (
            ("prism", "ABCD.A'B'C'D'", _find_q(text, "Cho hình lập phương ABCD.A'B'C'D' có cạnh bằng 2a.")),
            [
                ("right_prism", {"base": ["A", "B", "C", "D"], "top": ["A'", "B'", "C'", "D'"]}, _find_q(text, "Cho hình lập phương ABCD.A'B'C'D' có cạnh bằng 2a.")),
                ("regular_polygon", {"vertices": ["A", "B", "C", "D"], "side": "2a"}, _find_q(text, "Cho hình lập phương ABCD.A'B'C'D' có cạnh bằng 2a.")),
                ("segment_length", {"segment": ["A", "A'"], "value": "2a"}, _find_q(text, "Cho hình lập phương ABCD.A'B'C'D' có cạnh bằng 2a.")),
            ],
            [("measurement", "volume", {"solid_id": "s1"}, _find_q(text, "Tính thể tích khối lập phương ABCD.A'B'C'D'."))],
            "a",
        ),
        "slm_h17_midpoint_distance": (
            ("pyramid", "S.ABC", _find_q(text, "Cho hình chóp S.ABC")),
            [
                ("right_angle", {"vertex": "A", "rays": ["B", "C"]}, _find_q(text, "đáy ABC vuông tại A")),
                ("segment_length", {"segment": ["A", "B"], "value": "a"}, _find_q(text, "AB=a")),
                ("segment_length", {"segment": ["A", "C"], "value": "2a"}, _find_q(text, "AC=2a.")),
                ("perpendicular_line_plane", {"line": ["S", "A"], "plane": ["A", "B", "C"]}, _find_q(text, "SA vuông góc với (ABC)")),
                ("segment_length", {"segment": ["S", "A"], "value": "2a"}, _find_q(text, "SA=2a.")),
                ("midpoint", {"point": "M", "segment": ["B", "C"]}, _find_q(text, "Gọi M là trung điểm của cạnh BC.")),
            ],
            [("measurement", "distance", {"point": "M", "plane": ["S", "A", "B"]}, _find_q(text, "Tính khoảng cách từ M đến mặt phẳng (SAB)."))],
            "a",
        ),
        "slm_h18_midpoint_height": (
            ("pyramid", "S.ABCD", _find_q(text, "Cho hình chóp S.ABCD", "Xét hình chóp S.ABCD")),
            [
                ("regular_polygon", {"vertices": ["A", "B", "C", "D"], "side": "a"}, _find_q(text, "đáy ABCD là hình vuông cạnh a")),
                ("perpendicular_line_plane", {"line": ["S", "A"], "plane": ["A", "B", "C", "D"]}, _find_q(text, "SA vuông góc với đáy")),
                ("segment_length", {"segment": ["S", "A"], "value": "a"}, _find_q(text, "SA=a.")),
                ("midpoint", {"point": "N", "segment": ["S", "D"]}, _find_q(text, "Gọi N là trung điểm của đoạn SD.")),
            ],
            [("measurement", "distance", {"point": "N", "plane": ["A", "B", "C", "D"]}, _find_q(text, "Tính khoảng cách từ điểm N đến mặt phẳng (ABCD)."))],
            "a",
        ),
        "slm_h19_centroid_altitude": (
            ("pyramid", "S.ABC", _find_q(text, "Cho hình chóp S.ABC")),
            [
                ("regular_polygon", {"vertices": ["A", "B", "C"], "side": "a"}, _find_q(text, "đáy ABC là tam giác đều cạnh a.")),
                ("centroid", {"point": "G", "polygon": ["A", "B", "C"]}, _find_q(text, "Gọi G là trọng tâm tam giác ABC", "Biết G là trọng tâm tam giác ABC")),
                ("perpendicular_line_plane", {"line": ["S", "G"], "plane": ["A", "B", "C"]}, _find_q(text, "SG vuông góc với (ABC)")),
                ("segment_length", {"segment": ["S", "G"], "value": "2a"}, _find_q(text, "SG=2a.")),
            ],
            [("measurement", "volume", {"solid_id": "s1"}, _find_q(text, "Tính thể tích khối chóp S.ABC."))],
            "a",
        ),
        "slm_h20_skew_lines_distance": (
            ("pyramid", "S.ABCD", _find_q(text, "Cho Hình chóp S.ABCD", "Hình chóp S.ABCD")),
            [
                ("regular_polygon", {"vertices": ["A", "B", "C", "D"], "side": "2a"}, _find_q(text, "đáy ABCD là hình vuông cạnh 2a")),
                ("perpendicular_line_plane", {"line": ["S", "A"], "plane": ["A", "B", "C", "D"]}, _find_q(text, "SA vuông góc với (ABCD)")),
                ("segment_length", {"segment": ["S", "A"], "value": "2a"}, _find_q(text, "SA=2a.")),
            ],
            [("measurement", "distance", {"line1": ["S", "A"], "line2": ["C", "D"]}, _find_q(text, "Tính khoảng cách giữa hai đường thẳng SA và CD."))],
            "a",
        ),
        "slm_h21_orthoproj_line_seg": (
            ("pyramid", "S.ABC", _find_q(text, "Cho hình chóp S.ABC")),
            [
                ("regular_polygon", {"vertices": ["A", "B", "C"], "side": "a"}, _find_q(text, "đáy ABC là tam giác đều cạnh a")),
                ("perpendicular_line_plane", {"line": ["S", "A"], "plane": ["A", "B", "C"]}, _find_q(text, "SA vuông góc với (ABC)")),
                ("segment_length", {"segment": ["S", "A"], "value": "a"}, _find_q(text, "SA=a.")),
                ("orthogonal_projection_line", {"point": "A", "image": "H", "line": ["S", "B"]}, _find_q(text, "Gọi H là hình chiếu vuông góc của A lên SB.")),
            ],
            [("measurement", "distance", {"segment": ["A", "H"]}, _find_q(text, "Tính độ dài đoạn AH."))],
            "a",
        ),
        "slm_h22_rect_pyramid_dist": (
            ("pyramid", "S.ABCD", _find_q(text, "Cho hình chóp S.ABCD")),
            [
                ("rectangle", {"vertices": ["A", "B", "C", "D"]}, _find_q(text, "đáy ABCD là hình chữ nhật")),
                ("segment_length", {"segment": ["A", "B"], "value": "a"}, _find_q(text, "AB=a")),
                ("segment_length", {"segment": ["A", "D"], "value": "a√3"}, _find_q(text, "AD=a√3")),
                ("perpendicular_line_plane", {"line": ["S", "A"], "plane": ["A", "B", "C", "D"]}, _find_q(text, "SA vuông góc với (ABCD)")),
                ("segment_length", {"segment": ["S", "A"], "value": "2a"}, _find_q(text, "SA=2a.")),
            ],
            [("measurement", "distance", {"point": "B", "plane": ["S", "A", "D"]}, _find_q(text, "Tính khoảng cách từ B đến mặt phẳng (SAD)."))],
            "a",
        ),
        "slm_h23_ocr_extra_spaces": (
            ("pyramid", "S.ABC", _find_q(text, "Cho hình chóp S.ABC")),
            [
                ("regular_polygon", {"vertices": ["A", "B", "C"], "side": "2a"}, _find_q(text, "đáy ABC là tam giác đều cạnh 2a", "đáy ABC đều cạnh 2a")),
                ("perpendicular_line_plane", {"line": ["S", "A"], "plane": ["A", "B", "C"]}, _find_q(text, "SA vuông góc với (ABC)", "SA vuông góc với ( ABC )")),
                ("segment_length", {"segment": ["S", "A"], "value": "3a"}, _find_q(text, "SA=3a", "SA = 3a")),
            ],
            [("measurement", "volume", {"solid_id": "s1"}, _find_q(text, "Tính thể tích khối chóp S.ABC."))],
            "a",
        ),
        "slm_h24_ocr_missing_tone_goc": (
            ("pyramid", "S.ABCD", _find_q(text, "Cho hình chóp S.ABCD")),
            [
                ("regular_polygon", {"vertices": ["A", "B", "C", "D"], "side": "a"}, _find_q(text, "đáy ABCD là hình vuông cạnh a")),
                ("perpendicular_line_plane", {"line": ["S", "A"], "plane": ["A", "B", "C", "D"]}, _find_q(text, "SA vuông goc với (ABCD)")),
                ("segment_length", {"segment": ["S", "A"], "value": "a"}, _find_q(text, "SA=a.")),
            ],
            [("measurement", "volume", {"solid_id": "s1"}, _find_q(text, "Tính thể tích khối chóp S.ABCD."))],
            "a",
        ),
        "slm_h25_paraphrase_perp_conj": (
            ("pyramid", "S.ABC", _find_q(text, "Cho hình chóp S.ABC")),
            [
                ("right_angle", {"vertex": "B", "rays": ["A", "C"]}, _find_q(text, "đáy ABC là tam giác vuông cân tại B")),
                ("equal_length", {"segment_a": ["B", "A"], "segment_b": ["B", "C"]}, _find_q(text, "đáy ABC là tam giác vuông cân tại B")),
                ("segment_length", {"segment": ["A", "B"], "value": "2a"}, _find_q(text, "AB=2a.", "độ dài AB bằng 2a.")),
                ("perpendicular_line_plane", {"line": ["S", "A"], "plane": ["A", "B", "C"]}, _find_q(text, "Cạnh SA vuông góc với (ABC)", "Cạnh SA thẳng đứng vuông góc với (ABC)")),
                ("segment_length", {"segment": ["S", "A"], "value": "a"}, _find_q(text, "SA=a.")),
            ],
            [("measurement", "distance", {"point": "B", "plane": ["S", "A", "C"]}, _find_q(text, "Tính khoảng cách từ B đến (SAC)."))],
            "a",
        ),
        "slm_h26_ocr_missing_tone_chop": (
            ("pyramid", "S.ABC", _find_q(text, "Hình chop S.ABC", "Cho Hình chop S.ABC")),
            [
                ("right_angle", {"vertex": "A", "rays": ["B", "C"]}, _find_q(text, "đáy ABC là tam giác vuông tại A")),
                ("segment_length", {"segment": ["A", "B"], "value": "3a"}, _find_q(text, "AB=3a")),
                ("segment_length", {"segment": ["A", "C"], "value": "4a"}, _find_q(text, "AC=4a")),
                ("perpendicular_line_plane", {"line": ["S", "A"], "plane": ["A", "B", "C"]}, _find_q(text, "SA vuông góc với (ABC)")),
                ("segment_length", {"segment": ["S", "A"], "value": "5a"}, _find_q(text, "SA=5a.")),
            ],
            [("measurement", "volume", {"solid_id": "s1"}, _find_q(text, "Tính thể tích khối chóp S.ABC."))],
            "a",
        ),
        "slm_h27_rhombus_base_60": (
            ("pyramid", "S.ABCD", _find_q(text, "Cho hình chóp S.ABCD")),
            [
                ("rhombus", {"vertices": ["A", "B", "C", "D"], "side": "a"}, _find_q(text, "đáy ABCD là hình thoi cạnh a")),
                ("vertex_angle", {"vertex": "A", "rays": ["B", "D"], "value": "60", "unit": "deg"}, _find_q(text, "góc BAD bằng 60°.", "góc BAD bằng 60 độ.")),
                ("perpendicular_line_plane", {"line": ["S", "A"], "plane": ["A", "B", "C", "D"]}, _find_q(text, "Cạnh SA vuông góc với mặt phẳng (ABCD)")),
                ("segment_length", {"segment": ["S", "A"], "value": "a"}, _find_q(text, "SA=a.")),
            ],
            [("measurement", "volume", {"solid_id": "s1"}, _find_q(text, "Tính thể tích khối chóp S.ABCD."))],
            "a",
        ),
        "slm_h28_split_dist_3a_4a": (
            ("pyramid", "S.ABC", _find_q(text, "Cho hình chóp S.ABC", "Xét hình chóp S.ABC.")),
            [
                ("regular_polygon", {"vertices": ["A", "B", "C"], "side": "3a"}, _find_q(text, "Đáy ABC là tam giác đều cạnh 3a.")),
                ("perpendicular_line_plane", {"line": ["S", "A"], "plane": ["A", "B", "C"]}, _find_q(text, "Đường thẳng SA vuông góc với (ABC)")),
                ("segment_length", {"segment": ["S", "A"], "value": "4a"}, _find_q(text, "SA=4a.", "độ dài SA bằng 4a.")),
            ],
            [("measurement", "distance", {"point": "A", "plane": ["S", "B", "C"]}, _find_q(text, "Tính khoảng cách từ A đến mặt phẳng (SBC).", "Hãy tính khoảng cách từ A đến mặt phẳng (SBC)."))],
            "a",
        ),
        "S2-F-S07": (
            ("pyramid", "S.ABCD", _find_q(text, "Cho hình chop S.ABCD")),
            [
                ("regular_polygon", {"vertices": ["A", "B", "C", "D"], "side": "2"}, _find_q(text, "đáy ABCD là hình vuông cạnh 2")),
                ("perpendicular_line_plane", {"line": ["S", "A"], "plane": ["A", "B", "C", "D"]}, _find_q(text, "SA vuông góc với mặt phẳng (ABCD)")),
                ("segment_length", {"segment": ["S", "A"], "value": "2"}, _find_q(text, "SA = 2.")),
            ],
            [("measurement", "volume", {"solid_id": "s1"}, _find_q(text, "Tính thể tích khối chóp S.ABCD."))],
            "1",
        ),
    }
    solid, premises, goals, unit = specs[case_id]
    return _mk_gold(text, solid=solid, premises=premises, goals=goals, unit=unit)


def _install_diag_capture(runtime: LocalSlmRuntime) -> dict[str, Any]:
    capture: dict[str, Any] = {"messages": None, "inf": None}
    orig = runtime.chat_completion_json

    def _wrapped(**kwargs: Any) -> Any:
        capture["messages"] = kwargs.get("messages")
        try:
            res = orig(**kwargs)
        except Exception as exc:
            if "10013" in str(exc) or "LOCAL_SLM_PROCESS_CRASHED" in str(getattr(exc, "reason_code", "")):
                time.sleep(0.5)
                res = orig(**kwargs)
            else:
                raise
        capture["inf"] = res
        return res

    runtime.chat_completion_json = _wrapped  # type: ignore[method-assign]
    return capture


def _diagnose_case(
    case_id: str,
    split: str,
    expect_serve: bool,
    oracle: str | None,
    raw_text: str,
    runtime: LocalSlmRuntime,
    capture: dict[str, Any],
) -> dict[str, Any]:
    # 1. Original source & Test A (Local Parser -> existing pipeline)
    clear_local_geometry_parser_cache()
    t0 = time.perf_counter()
    lp = parse_geometry_problem_locally(raw_text)
    t_lp = round((time.perf_counter() - t0) * 1000.0, 2)
    t_rta0 = time.perf_counter()
    test_a = AIR.route_text_input(raw_text, allow_live_ai=False)
    t_rta = round((time.perf_counter() - t_rta0) * 1000.0, 2)
    a_ok, a_got, a_ce = (
        ESC._grade_positive(test_a.status, test_a.response, oracle)
        if expect_serve and oracle
        else (test_a.status != "SERVED", ESC._extract_answer_str(test_a.response), 0)
    )

    # 2. Test B (Qwen3-0.6B minimal_ops -> /5 Validator -> existing pipeline)
    clear_local_geometry_parser_cache()
    capture["messages"] = None
    capture["inf"] = None
    t_b0 = time.perf_counter()
    test_b = AIR.route_text_input_local_slm(
        raw_text,
        model_key=DEFAULT_LOCAL_SLM_MODEL_KEY,
        strategy="minimal_ops",
        runtime=runtime,
        allow_download=False,
    )
    t_b = round((time.perf_counter() - t_b0) * 1000.0, 2)
    b_rd = (test_b.response or {}).get("route_d") or {}
    b_env = b_rd.get("slm_grounding_envelope") or {}
    b_ref = b_rd.get("refusal") or {}
    b_ok, b_got, b_ce = (
        ESC._grade_positive(test_b.status, test_b.response, oracle)
        if expect_serve and oracle
        else (test_b.status != "SERVED", ESC._extract_answer_str(test_b.response), 0)
    )

    # Reuse exact inference captured from test_b; only run counterfactual direct SLM call when router skipped SLM on a failed positive (h01, h03)
    norm_text = normalize_problem_text(raw_text)
    clauses = index_source_clauses(norm_text)
    messages = capture["messages"] or _build_minimal_ops_messages(norm_text, clauses, lp)
    inf = capture["inf"]
    raw_slm_json = inf.parsed_json if inf is not None else None
    val_diag = None
    lowered_canon = None
    sg_after_val = None
    if inf is None and expect_serve and not b_ok and not b_env.get("slm_invoked"):
        inf = runtime.chat_completion_json(
            messages=messages,
            json_schema=MINIMAL_OPS_JSON_SCHEMA,
            schema_name="slm_minimal_ops_diag",
            model_key=DEFAULT_LOCAL_SLM_MODEL_KEY,
            allow_download=False,
        )
        raw_slm_json = inf.parsed_json
    if raw_slm_json is not None:
        lowered_canon, val_diag = validate_and_lower_minimal_ops(
            norm_text=norm_text,
            clauses=clauses,
            raw_slm_json=raw_slm_json,
            local_parser_payload=lp.payload,
        )
        if lowered_canon is not None:
            rt_sg = run_typed_fact_next_v2_route(lowered_canon)
            sg_after_val = {"status": rt_sg.status, "code": rt_sg.code, "reason": rt_sg.reason}

    # 3. Test C_raw and Test C_canon (Gold TypedFactNext /2 on positives)
    c_raw: dict[str, Any] | None = None
    c_canon: dict[str, Any] | None = None
    canon_text = raw_text
    applied_rules: list[dict[str, Any]] = []
    typo_flags: list[str] = []
    if expect_serve and oracle:
        pol = hybrid_offline_policy({"HYBRID_ROUTE_D_PREVIEW": "1"})
        gold_raw_pay = build_gold_payload(case_id, raw_text)
        canon_raw = _normalize_transport_payload(to_wire_typed_fact_next_v2(gold_raw_pay))
        res_raw = run_hybrid_offline(raw_text, ReplayExtractor({raw_text: canon_raw}), policy=pol)
        r_rd = res_raw.response.get("route_d") or {}
        raw_ok, raw_got, raw_ce = ESC._grade_positive(r_rd.get("status", "REFUSED"), res_raw.response, oracle)
        c_raw = {
            "status": r_rd.get("status"),
            "ok": raw_ok,
            "answer": raw_got,
            "continuity_errors": raw_ce,
            "refusal": r_rd.get("refusal"),
            "planner": r_rd.get("planner"),
            "failure_stage": res_raw.receipt.get("failure_stage"),
        }

        canon_text, applied_rules, typo_flags = _surface_canonicalize(raw_text)
        gold_can_pay = build_gold_payload(case_id, canon_text)
        canon_norm = _normalize_transport_payload(to_wire_typed_fact_next_v2(gold_can_pay))
        res_can = run_hybrid_offline(canon_text, ReplayExtractor({canon_text: canon_norm}), policy=pol)
        c_rd = res_can.response.get("route_d") or {}
        can_ok, can_got, can_ce = ESC._grade_positive(c_rd.get("status", "REFUSED"), res_can.response, oracle)
        c_canon = {
            "canonical_text": canon_text,
            "applied_rules": [r["rule_id"] for r in applied_rules],
            "typo_flags": typo_flags,
            "status": c_rd.get("status"),
            "ok": can_ok,
            "answer": can_got,
            "continuity_errors": can_ce,
            "refusal": c_rd.get("refusal"),
            "planner": c_rd.get("planner"),
            "failure_stage": res_can.receipt.get("failure_stage"),
        }

    # Layer latencies breakdown
    tel_b = test_b.telemetry.to_dict()
    return {
        "case_id": case_id,
        "split": split,
        "expect_serve": expect_serve,
        "oracle": oracle,
        # Layer 1-3: source & Local Parser
        "layer_01_original_source": raw_text,
        "layer_02_local_parser": {
            "status": lp.status,
            "reason_code": lp.reason_code,
            "source_coverage": lp.source_coverage.to_dict(),
        },
        "layer_03_router_completeness": {
            "test_a_chosen_route": test_a.telemetry.chosen_route,
            "test_a_status": test_a.status,
            "test_a_ok": a_ok,
            "test_a_answer": a_got,
            "test_b_chosen_route": tel_b.get("chosen_route"),
            "test_b_slm_invoked": bool(b_env.get("slm_invoked")),
        },
        # Layer 4-7: SLM IO & Validator
        "layer_04_slm_input_chars": sum(len(m["content"]) for m in messages),
        "layer_05_raw_slm_output": raw_slm_json,
        "layer_06_parsed_ops": (raw_slm_json or {}).get("ops") if raw_slm_json else None,
        "layer_07_grounding_validator": val_diag,
        # Layer 8-13: Lowering, Source Gate, Planner, Kernel, Scene3D, Final Refusal
        "layer_08_lowered_typed_facts": lowered_canon,
        "layer_09_source_gate": sg_after_val or b_ref,
        "layer_10_planner": b_rd.get("planner"),
        "layer_11_exact_kernel": {"status": test_b.status, "ok": b_ok, "answer": b_got},
        "layer_12_scene3d_continuity_errors": b_ce,
        "layer_13_final_refusal_code": b_ref.get("code") or b_ref.get("reason_code"),
        "layer_14_stage_latencies_ms": {
            "local_parse_ms": t_lp,
            "test_a_total_ms": t_rta,
            "test_b_total_ms": t_b,
            "slm_infer_ms": b_env.get("inference_time_ms") or (inf.inference_time_ms if inf else None),
            "slm_prompt_tokens": inf.prompt_tokens if inf else None,
            "slm_completion_tokens": inf.completion_tokens if inf else None,
        },
        "test_a": {"status": test_a.status, "ok": a_ok, "answer": a_got, "code": test_a.receipt.get("code")},
        "test_b": {"status": test_b.status, "ok": b_ok, "answer": b_got, "code": b_ref.get("code") or test_b.receipt.get("code")},
        "test_c_gold_raw": c_raw,
        "test_c_gold_canon": c_canon,
    }


def _attribute_root_cause(row: dict[str, Any]) -> dict[str, Any]:
    cid = row["case_id"]
    if not row["expect_serve"] or row["test_b"]["ok"]:
        return {
            "case_id": cid,
            "status": "SOLVED_BY_V5" if row["expect_serve"] else "NEGATIVE_REFUSED",
            "primary_failure_layer": "NONE",
            "secondary_failure_layer": "NONE",
            "gold_raw_outcome": (row["test_c_gold_raw"] or {}).get("status", "N/A"),
            "gold_canon_outcome": (row["test_c_gold_canon"] or {}).get("status", "N/A"),
            "slm_only_solvable": True if row["expect_serve"] else False,
            "downstream_or_canon_required": False,
            "confidence": "HIGH",
            "evidence": f"Test B ok={row['test_b']['ok']}",
            "recommended_action": "Keep behavior intact",
        }

    lp = row["layer_02_local_parser"]
    b_slm_inv = row["layer_03_router_completeness"]["test_b_slm_invoked"]
    val = row["layer_07_grounding_validator"] or {}
    g_raw = row["test_c_gold_raw"] or {}
    g_can = row["test_c_gold_canon"] or {}
    raw_slm = row["layer_05_raw_slm_output"] or {}
    ops = raw_slm.get("ops") or []
    typo_flags = (row["test_c_gold_canon"] or {}).get("typo_flags") or []
    val_status = str(val.get("grounding_status") or "")
    b_code = str(row["layer_13_final_refusal_code"] or "")
    raw_ref_code = str(((g_raw.get("refusal") or {}).get("code")) or "")

    # Classify precisely from 14-layer evidence + Test C_raw / C_canon
    if typo_flags:
        return {
            "case_id": cid,
            "status": "FAILED",
            "primary_failure_layer": "SOURCE_TYPO_UNSUPPORTED_BY_CLOSED_GATE",
            "secondary_failure_layer": "SLM_GROUNDING" if val_status != "GROUNDED_AND_LOWERED" else "SOURCE_GATE",
            "gold_raw_outcome": f"REFUSED:{raw_ref_code}",
            "gold_canon_outcome": f"REFUSED:{((g_can.get('refusal') or {}).get('code'))}",
            "slm_only_solvable": False,
            "downstream_or_canon_required": True,
            "confidence": "HIGH",
            "evidence": f"Source has diacritic typo {typo_flags}; Source Gate refuses {raw_ref_code} even with Gold TypedFacts.",
            "recommended_action": "Flag ambiguity / request user confirmation; NEVER silently auto-rewrite typos.",
        }

    if not b_slm_inv:
        # SLM was never called by /5 router!
        return {
            "case_id": cid,
            "status": "FAILED",
            "primary_failure_layer": "ROUTER_PREMATURE_SHORT_CIRCUIT",
            "secondary_failure_layer": "SURFACE_GRAMMAR_SYNTAX" if not g_raw.get("ok") and g_can.get("ok") else "LOCAL_PARSER_COVERAGE",
            "gold_raw_outcome": f"{g_raw.get('status')}:{raw_ref_code or g_raw.get('answer')}",
            "gold_canon_outcome": f"{g_can.get('status')}:{g_can.get('answer') or ((g_can.get('refusal') or {}).get('code'))}",
            "slm_only_solvable": bool(g_raw.get("ok")),
            "downstream_or_canon_required": not bool(g_raw.get("ok")),
            "confidence": "HIGH",
            "evidence": f"Local Parser returned {lp['status']}/{lp['reason_code']}; /5 router chose {row['layer_03_router_completeness']['test_b_chosen_route']} and skipped SLM.",
            "recommended_action": "Allow SLM fallback on partial-regex LOCAL_PARSE_AMBIGUOUS / contrastive CONDITIONAL_CLAUSE + verified normalization.",
        }

    if val_status == "GROUNDED_AND_LOWERED":
        # SLM + Validator succeeded, then Source Gate / downstream rejected
        if g_raw.get("ok"):
            return {
                "case_id": cid,
                "status": "FAILED",
                "primary_failure_layer": "VALID_OP_MISQUOTED_FOR_SOURCE_GATE",
                "secondary_failure_layer": "SLM_PARTIAL_OR_FRAGILE_QUOTE",
                "gold_raw_outcome": f"SERVED:{g_raw.get('answer')}",
                "gold_canon_outcome": f"SERVED:{g_can.get('answer')}",
                "slm_only_solvable": False,
                "downstream_or_canon_required": True,
                "confidence": "HIGH",
                "evidence": f"/5 select_clean_quote or missing premise caused Source Gate {b_code}, whereas Gold on RAW source SERVED ({g_raw.get('answer')}).",
                "recommended_action": "Fix select_source_gate_compatible_quote for role-bound predicates + cover full premise spans.",
            }
        else:
            # Even Gold on raw failed Source Gate, but Gold on canon passed!
            return {
                "case_id": cid,
                "status": "FAILED",
                "primary_failure_layer": "SURFACE_SYNTAX_OUTSIDE_SOURCE_GATE_GRAMMAR",
                "secondary_failure_layer": "SLM_OMISSION_OR_FRAGMENT" if len(ops) < 2 else "LOWERING_QUOTE_SELECTION",
                "gold_raw_outcome": f"REFUSED:{raw_ref_code}",
                "gold_canon_outcome": f"{g_can.get('status')}:{g_can.get('answer') or ((g_can.get('refusal') or {}).get('code'))}",
                "slm_only_solvable": False,
                "downstream_or_canon_required": True,
                "confidence": "HIGH",
                "evidence": f"Gold TypedFacts failed Source Gate on raw text ({raw_ref_code}) vs canonicalized ({g_can.get('status')}, rules={g_can.get('applied_rules')}).",
                "recommended_action": "Apply audited Verified Normalizer before Source Gate & extraction.",
            }

    # Grounding Validator rejected raw SLM output -> genuine SLM extraction error (possibly compounded by surface syntax)
    rej = val.get("rejected_ops") or []
    if g_raw.get("ok"):
        primary = "SLM_EXTRACTION_ERROR"
        secondary = "NONE"
        need_canon = False
    elif g_can.get("ok"):
        primary = "SLM_EXTRACTION_ERROR"
        secondary = f"SURFACE_SYNTAX_GAP ({raw_ref_code})"
        need_canon = True
    else:
        primary = "SLM_EXTRACTION_AND_DOWNSTREAM_GAP"
        secondary = raw_ref_code
        need_canon = True

    return {
        "case_id": cid,
        "status": "FAILED",
        "primary_failure_layer": primary,
        "secondary_failure_layer": secondary,
        "gold_raw_outcome": f"{g_raw.get('status')}:{raw_ref_code or g_raw.get('answer')}",
        "gold_canon_outcome": f"{g_can.get('status')}:{g_can.get('answer') or ((g_can.get('refusal') or {}).get('code'))}",
        "slm_only_solvable": bool(g_raw.get("ok")),
        "downstream_or_canon_required": need_canon,
        "confidence": "HIGH",
        "evidence": f"Validator status={val_status}, rejected={rej[:2]}, SLM ops_count={len(ops)}.",
        "recommended_action": "Replace minimal_ops with clause-level compact slot-filling + closed entity GBNF" + (" + verified normalizer." if need_canon else "."),
    }


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    rt = LocalSlmRuntime(threads=6, allow_download=False)
    capture = _install_diag_capture(rt)
    try:
        rows: list[dict[str, Any]] = []
        # 1. DEV_CALIBRATION_16
        for c in ESC.DEV_CALIBRATION_16:
            r = _diagnose_case(
                c["id"],
                "DEV_CALIBRATION_16",
                c["kind"] == "positive",
                c.get("oracle"),
                c["text"],
                rt,
                capture,
            )
            print(f"[DIAG] {c['id']:32s} A={r['test_a']['ok']} B={r['test_b']['ok']} C_raw={(r['test_c_gold_raw'] or {}).get('ok')} C_can={(r['test_c_gold_canon'] or {}).get('ok')}", flush=True)
            rows.append(r)
        # 2. HOLDOUT_40 (labeled explicitly HISTORICAL_DIAGNOSTIC)
        hm = json.loads((RUN5_DIR / "independent_slm_holdout_manifest.json").read_text(encoding="utf-8"))
        for item in hm["items"]:
            r = _diagnose_case(
                item["case_id"],
                "HOLDOUT_40_HISTORICAL_DIAGNOSTIC",
                item["expected_outcome"] == "SERVED",
                item.get("oracle"),
                item["problem_text"],
                rt,
                capture,
            )
            print(f"[DIAG] {item['case_id']:32s} A={r['test_a']['ok']} B={r['test_b']['ok']} C_raw={(r['test_c_gold_raw'] or {}).get('ok')} C_can={(r['test_c_gold_canon'] or {}).get('ok')}", flush=True)
            rows.append(r)
        # 3. S2-F-S07
        s2_cases = json.loads((ROOT / "docs/evaluation/geometry/runs/hybrid-master-backend-replacement/s2-student-language-pilot-corpus.json").read_text(encoding="utf-8"))["cases"]
        s2_s07 = next(c for c in s2_cases if (c.get("id") or c.get("case_id")) == "S2-F-S07_typo_tone")
        r = _diagnose_case(
            "S2-F-S07",
            "S2_INCOMPLETE",
            True,
            "8/3",
            s2_s07["problem_text"],
            rt,
            capture,
        )
        print(f"[DIAG] S2-F-S07                         A={r['test_a']['ok']} B={r['test_b']['ok']} C_raw={(r['test_c_gold_raw'] or {}).get('ok')} C_can={(r['test_c_gold_canon'] or {}).get('ok')}", flush=True)
        rows.append(r)
    finally:
        rt.shutdown()

    pos_rows = [r for r in rows if r["expect_serve"]]
    neg_rows = [r for r in rows if not r["expect_serve"]]
    holdout_pos = [r for r in rows if r["split"] == "HOLDOUT_40_HISTORICAL_DIAGNOSTIC" and r["expect_serve"]]
    holdout_neg = [r for r in rows if r["split"] == "HOLDOUT_40_HISTORICAL_DIAGNOSTIC" and not r["expect_serve"]]
    cal_pos = [r for r in rows if r["split"] == "DEV_CALIBRATION_16" and r["expect_serve"]]

    rc_matrix = [_attribute_root_cause(r) for r in pos_rows]
    rc_counts = dict(Counter(m["primary_failure_layer"] for m in rc_matrix if m["status"] == "FAILED"))
    holdout_failed_matrix = [m for m in rc_matrix if m["case_id"].startswith("slm_h") and m["status"] == "FAILED"]
    holdout_rc_counts = dict(Counter(m["primary_failure_layer"] for m in holdout_failed_matrix))

    # Partition breakdown on HOLDOUT_40 positives
    h40_parser_solved = [r["case_id"] for r in holdout_pos if not r["layer_03_router_completeness"]["test_b_slm_invoked"] and r["test_a"]["ok"]]
    h40_router_skipped_failed = [r["case_id"] for r in holdout_pos if not r["layer_03_router_completeness"]["test_b_slm_invoked"] and not r["test_a"]["ok"]]
    h40_slm_invoked_pos = [r["case_id"] for r in holdout_pos if r["layer_03_router_completeness"]["test_b_slm_invoked"]]
    h40_slm_rescued = [r["case_id"] for r in holdout_pos if r["layer_03_router_completeness"]["test_b_slm_invoked"] and r["test_b"]["ok"]]
    h40_slm_failed = [r["case_id"] for r in holdout_pos if r["layer_03_router_completeness"]["test_b_slm_invoked"] and not r["test_b"]["ok"]]
    h40_validator_rejected = [
        r["case_id"]
        for r in holdout_pos
        if r["layer_03_router_completeness"]["test_b_slm_invoked"]
        and not r["test_b"]["ok"]
        and (r["layer_07_grounding_validator"] or {}).get("grounding_status") != "GROUNDED_AND_LOWERED"
    ]
    h40_downstream_sg_rejected = [
        r["case_id"]
        for r in holdout_pos
        if r["layer_03_router_completeness"]["test_b_slm_invoked"]
        and not r["test_b"]["ok"]
        and (r["layer_07_grounding_validator"] or {}).get("grounding_status") == "GROUNDED_AND_LOWERED"
    ]

    cal_p02 = next(r for r in cal_pos if r["case_id"] == "cal_p02_dist_split")
    slm_h28 = next(r for r in holdout_pos if r["case_id"] == "slm_h28_split_dist_3a_4a")
    h28_vs_p02_analysis = {
        "cal_p02_text": cal_p02["layer_01_original_source"],
        "slm_h28_text": slm_h28["layer_01_original_source"],
        "cal_p02_oracle": cal_p02["oracle"],
        "slm_h28_oracle": slm_h28["oracle"],
        "shared_template_signature": {
            "solid": "pyramid(S.ABC)",
            "base": "regular_polygon(ABC, equilateral)",
            "altitude": "perpendicular_line_plane(SA, ABC)",
            "goal": "distance(A, plane(SBC))",
            "surface_pattern": "Xét hình chóp S.ABC. [Tam giác] đáy ABC ... cạnh [s]. Đường thẳng SA vuông góc ... và SA = [h]. Hãy ... khoảng cách từ A đến mặt phẳng (SBC).",
        },
        "parameter_substitution": {"side": "a -> 3a", "height": "2a -> 4a"},
        "conclusion": "ISOMORPHIC_PARAMETER_TEMPLATE_CLONE — slm_h28 cannot be treated as independent evidence of solving an unseen geometric family.",
    }

    summary = {
        "DEV_CALIBRATION_16_POS": {
            "total": len(cal_pos),
            "test_a_det_v145": sum(1 for r in cal_pos if r["test_a"]["ok"]),
            "test_b_v5_minimal_ops": sum(1 for r in cal_pos if r["test_b"]["ok"]),
            "test_c_gold_raw": sum(1 for r in cal_pos if (r["test_c_gold_raw"] or {}).get("ok")),
            "test_c_gold_canon": sum(1 for r in cal_pos if (r["test_c_gold_canon"] or {}).get("ok")),
        },
        "HOLDOUT_40_HISTORICAL_DIAGNOSTIC_POS": {
            "total": len(holdout_pos),
            "test_a_det_v145": sum(1 for r in holdout_pos if r["test_a"]["ok"]),
            "test_b_v5_minimal_ops": sum(1 for r in holdout_pos if r["test_b"]["ok"]),
            "test_c_gold_raw": sum(1 for r in holdout_pos if (r["test_c_gold_raw"] or {}).get("ok")),
            "test_c_gold_canon": sum(1 for r in holdout_pos if (r["test_c_gold_canon"] or {}).get("ok")),
            "partition_v5": {
                "parser_self_solved_count": len(h40_parser_solved),
                "parser_self_solved_ids": h40_parser_solved,
                "router_premature_skip_failed_count": len(h40_router_skipped_failed),
                "router_premature_skip_failed_ids": h40_router_skipped_failed,
                "slm_invoked_positive_count": len(h40_slm_invoked_pos),
                "slm_rescued_positive_count": len(h40_slm_rescued),
                "slm_rescued_positive_ids": h40_slm_rescued,
                "slm_invoked_failed_count": len(h40_slm_failed),
                "slm_invoked_validator_rejected_count": len(h40_validator_rejected),
                "slm_invoked_validator_rejected_ids": h40_validator_rejected,
                "slm_invoked_downstream_sg_rejected_count": len(h40_downstream_sg_rejected),
                "slm_invoked_downstream_sg_rejected_ids": h40_downstream_sg_rejected,
                "slm_invoked_negative_count": sum(1 for r in holdout_neg if r["layer_03_router_completeness"]["test_b_slm_invoked"]),
            },
            "holdout_18_failed_primary_layers": holdout_rc_counts,
        },
        "ALL_39_POSITIVES": {
            "total": len(pos_rows),
            "test_a_det_v145": sum(1 for r in pos_rows if r["test_a"]["ok"]),
            "test_b_v5_minimal_ops": sum(1 for r in pos_rows if r["test_b"]["ok"]),
            "test_c_gold_raw": sum(1 for r in pos_rows if (r["test_c_gold_raw"] or {}).get("ok")),
            "test_c_gold_canon": sum(1 for r in pos_rows if (r["test_c_gold_canon"] or {}).get("ok")),
            "primary_failure_layer_counts": rc_counts,
        },
        "ALL_18_NEGATIVES": {
            "total": len(neg_rows),
            "test_a_refused": sum(1 for r in neg_rows if r["test_a"]["ok"]),
            "test_b_refused": sum(1 for r in neg_rows if r["test_b"]["ok"]),
        },
        "slm_h28_vs_cal_p02_structural_relation": h28_vs_p02_analysis,
    }

    payload = {
        "schema": "slm-gold-intervention-results/1",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "baseline_head": "463c6b0408e192a19ff1f25a1bff2a6c94e4e75f",
        "external_ai_calls": 0,
        "summary": summary,
        "root_cause_matrix": rc_matrix,
        "diagnostic_rows": rows,
    }
    (OUT_DIR / "SLM_GOLD_INTERVENTION_RESULTS.json").write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(summary, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
