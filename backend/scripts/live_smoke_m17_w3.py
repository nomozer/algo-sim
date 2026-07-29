# -*- coding: utf-8 -*-
"""M17 W3-LIVE — LIVE SMOKE `binary.character_encoding` (6 case × 2 lượt).

Câu hỏi DUY NHẤT của checkpoint: đường chạy THẬT
    đề tiếng Việt → LLM phân tích → phân loại target → candidate spec
    → validator → engine tất định
có đứng vững với LLM thật không. KHÔNG kiểm lại phép tính, renderer hay Chrome —
những phần đó đã có bằng chứng offline + visual tại baseline 472314e.

GIỚI HẠN PHẢI GHI RÕ (không được đọc thành PASS ngầm):
1. Engine tất định của W3 nằm ở FRONTEND (`domains/binary/encoding-module.tsx`,
   dùng lại `toBase()` của base_conversion). Backend CỐ Ý không có engine mã hoá
   (xem `simulation/character_encoding.py`). Vì vậy runner này KHÔNG chạy được
   engine: nó kiểm ĐỊNH TUYẾN + CANDIDATE SPEC + VALIDATOR + KHÔNG RÒ KẾT QUẢ.
   Harness FE duy nhất (`capture-w3-encoding.mjs`) chạy Chrome — checkpoint cấm.
2. Runner chạy IN-PROCESS (không qua container). Danh tính runtime là của chính
   tiến trình này — không thể stale image, nhưng cũng KHÔNG nói gì về container.

QUAN SÁT THỤ ĐỘNG: ngoài `AttemptObserver`, runner bọc `pipeline.call_gemini`
bằng một wrapper CHỈ GHI (delegate nguyên vẹn sang `gemini.call_gemini`) để lấy
RAW candidate TRƯỚC validator — §5 đòi chấm cả raw lẫn validated, mà observer
sản phẩm không phơi raw. Wrapper không đổi tham số, không đổi thứ tự, không nuốt
lỗi; gỡ ra ở `finally`.

OPT-IN: ALLOW_LIVE_AI=1.

Chạy:
    ALLOW_LIVE_AI=1 python scripts/live_smoke_m17_w3.py [--max-http 45] [--runs 2]
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.ai import gemini  # noqa: E402
from app.ai import pipeline  # noqa: E402
from app.ai.gemini import ApiBudget, BudgetExceeded, MODEL, load_skill  # noqa: E402
from app.evaluation.observer import AttemptObserver  # noqa: E402
from app.runtime_identity import runtime_identity  # noqa: E402
from app.simulation.catalog import CATALOG  # noqa: E402
from app.simulation.mechanisms import (  # noqa: E402
    analyze_exposed_values,
    canonical_mechanism,
)
from app.simulation.character_encoding import (  # noqa: E402
    ENCODINGS,
    FORBIDDEN_SPEC_KEYS,
    SPEC_VERSION,
)
from app.validation.character_encoding import validate_character_encoding_config  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
# Ghi ĐÈ artifact baseline là điều CẤM (W3-LIVE PARTIAL phải giữ nguyên để so
# sánh). Rerun của W3-LIVE-C1 truyền `--out-dir docs/evaluation/m17/w3-live-c1`.
OUT_DIR = ROOT / "docs" / "evaluation" / "m17" / "w3-live"
OUT_JSON = OUT_DIR / "character_encoding_live_smoke.json"
OUT_JSONL = OUT_DIR / "responses.jsonl"


def _set_out_dir(rel: str | None) -> None:
    global OUT_DIR, OUT_JSON, OUT_JSONL
    if not rel:
        return
    OUT_DIR = ROOT / rel
    stem = ("character_encoding_live_rerun"
            if OUT_DIR.name.endswith("-c1") else "character_encoding_live_smoke")
    OUT_JSON = OUT_DIR / f"{stem}.json"
    OUT_JSONL = OUT_DIR / "responses.jsonl"

TARGET = "binary.character_encoding"
DEC2BIN = "binary.decimal_to_binary"
GENERIC = "generic.rule_scene"
MAX_HTTP = 45
RUNS = 2

# Khoá KẾT QUẢ cấm nằm trong candidate. PHẢI TÁCH THEO TARGET — bài học từ chính
# lượt chạy đầu: bộ khoá của character_encoding từng bị áp cho MỌI route, nên
# `decimalValue` (INPUT HỢP LỆ của binary.decimal_to_binary) bị chấm là "rò kết
# quả" và LIVE-ENC-4 FAIL oan. Rò kết quả là khái niệm THEO HỢP ĐỒNG CỦA TARGET,
# không phải một danh sách từ khoá dùng chung.
_UNIVERSAL_LEAK_KEYS = {
    "trace", "timeline", "steps", "result", "results", "rows", "output",
    "final_answer", "finalAnswer", "narration", "renderer",
}
_CHARENC_LEAK_KEYS = set(FORBIDDEN_SPEC_KEYS) | _UNIVERSAL_LEAK_KEYS | {
    "code_point", "codePoint", "code_points", "ascii_code", "asciiCode",
    "decimal", "decimal_value", "decimalValue", "binary_value", "binaryValue",
    "division_steps", "divisionSteps", "quotient", "remainder",
}


def _leak_contract_for(route) -> set:
    """Hợp đồng rò-kết-quả theo TARGET. Ngoài character_encoding chỉ áp bộ
    R0 dùng chung (trace/timeline/kết quả) — không áp từ vựng của target khác."""
    return _CHARENC_LEAK_KEYS if route == TARGET else _UNIVERSAL_LEAK_KEYS

# Ký tự tiếng Việt phải giữ NGUYÊN precomposed: U+1EBF, KHÔNG phải "e" + dấu.
E_ACUTE = "ế"
EMOJI = "\U0001f600"

CASES = [
    {
        "id": "LIVE-ENC-1",
        "label": "ASCII một ký tự",
        "prompt": "Mô phỏng mã ASCII của ký tự A.",
        "expect_status": "ok",
        "expect_route": TARGET,
        "expect_text": "A",
        "expect_encoding": "ascii",
        "expect_code_points": [0x41],
    },
    {
        "id": "LIVE-ENC-2",
        "label": "ASCII chuỗi",
        "prompt": "Mô phỏng quá trình mã hóa chuỗi Tin bằng bảng mã ASCII.",
        "expect_status": "ok",
        "expect_route": TARGET,
        "expect_text": "Tin",
        "expect_encoding": "ascii",
        "expect_code_points": [0x54, 0x69, 0x6E],
    },
    {
        "id": "LIVE-ENC-3",
        "label": "Unicode BMP",
        "prompt": f"Mô phỏng Unicode code point của ký tự {E_ACUTE} và chuyển mã đó sang nhị phân.",
        "expect_status": "ok",
        "expect_route": TARGET,
        "expect_text": E_ACUTE,
        "expect_encoding": "unicode_codepoint",
        "expect_code_points": [0x1EBF],
    },
    {
        "id": "LIVE-ENC-4",
        "label": "Ranh giới phân loại với SỐ",
        "prompt": "Đổi số 65 sang nhị phân.",
        "expect_status": "ok",
        "expect_route": DEC2BIN,
        "expect_text": None,
        "expect_encoding": None,
        "expect_code_points": None,
    },
    {
        "id": "LIVE-ENC-5",
        "label": "Thiếu dữ kiện",
        "prompt": "Hãy mô phỏng mã hóa ký tự.",
        "expect_status": "refuse",
        "expect_route": None,
        "expect_text": None,
        "expect_encoding": None,
        "expect_code_points": None,
    },
    {
        "id": "LIVE-ENC-6",
        "label": "Ngoài phạm vi BMP (emoji)",
        "prompt": f"Mô phỏng Unicode của emoji {EMOJI} và chuyển sang nhị phân.",
        "expect_status": "refuse",
        "expect_route": None,
        "expect_text": None,
        "expect_encoding": None,
        "expect_code_points": None,
    },
]

_INFRA_MARKERS = (
    "All connection attempts failed", "getaddrinfo", "Temporary failure in name resolution",
    "Connection refused", "SSLError", "timed out", "Name or service not known",
    "Network is unreachable", "ProxyError",
)


def _git_sha() -> str:
    try:
        return subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True,
                              text=True, check=True, cwd=ROOT).stdout.strip()
    except Exception:
        return "unknown"


def _is_infra_error(err) -> bool:
    """Lỗi MẠNG ≠ hành vi sản phẩm. Bẫy đã sập ở W2C: mạng hỏng ⇒ không mô phỏng
    nào được dựng ⇒ mọi assertion 'phải từ chối' thoả mãn RỖNG."""
    return isinstance(err, str) and any(m.lower() in err.lower() for m in _INFRA_MARKERS)


def _network_reachable(host: str = "generativelanguage.googleapis.com") -> tuple[bool, str]:
    import socket
    try:
        socket.getaddrinfo(host, 443, proto=socket.IPPROTO_TCP)
        return True, ""
    except Exception as err:
        return False, f"{type(err).__name__}: {err}"


def _code_points(text) -> list[int] | None:
    """Python lặp chuỗi theo CODE POINT — cùng ngữ nghĩa `Array.from` ở FE."""
    if not isinstance(text, str):
        return None
    return [ord(ch) for ch in text]


def _cp_labels(cps) -> list[str] | None:
    return None if cps is None else [f"U+{cp:04X}" for cp in cps]


def _leak_keys_in(obj, route) -> list[str]:
    contract = _leak_contract_for(route)
    return sorted(k for k in obj if k in contract) if isinstance(obj, dict) else []


def _extra_keys_in(obj) -> list[str]:
    allowed = {"spec_version", "text", "encoding", "notes"}
    return sorted(set(obj) - allowed) if isinstance(obj, dict) else []


# ── Wrapper CHỈ GHI quanh call_gemini (harness, không phải production) ────────
class RawRecorder:
    """Ghi lại raw response từng stage. Delegate NGUYÊN VẸN — không đổi tham số,
    không nuốt lỗi, không thêm/bớt request."""

    def __init__(self) -> None:
        self.calls: list[dict] = []
        self._skills = {name: load_skill(name) for name in ("analyze", "classify", "simulate")}

    def _stage_of(self, system_prompt: str) -> str:
        for name, body in self._skills.items():
            if system_prompt == body:
                return name
        return "unknown"

    def wrap(self, original):
        async def recording(api_key, system_prompt, user_text, response_schema=None,
                            temperature=0.2, image=None):
            stage = self._stage_of(system_prompt)
            raw = await original(api_key, system_prompt, user_text, response_schema,
                                 temperature, image)
            try:
                parsed = json.loads(raw)
            except Exception:
                parsed = None
            self.calls.append({"stage": stage, "temperature": temperature,
                               "raw_text": raw, "parsed": parsed})
            return raw
        return recording

    def raw_simulate_candidates(self) -> list:
        return [c["parsed"] for c in self.calls if c["stage"] == "simulate"]

    def stage_temperatures(self) -> dict:
        return {c["stage"]: c["temperature"] for c in self.calls}


async def _run_once(case: dict, run_id: int, api_key: str, budget: ApiBudget) -> dict:
    obs = AttemptObserver()
    rec_raw = RawRecorder()
    original = pipeline.call_gemini
    pipeline.call_gemini = rec_raw.wrap(original)

    before = budget.http_requests
    started = datetime.now(timezone.utc)
    envelope, err = None, None
    try:
        envelope = await pipeline.run_pipeline(case["prompt"], api_key,
                                               pattern_store=None, observer=obs)
    except BudgetExceeded:
        raise
    except Exception as e:      # cạn lượt simulate → RuntimeError = TỪ CHỐI, không crash
        err = str(e)
    finally:
        pipeline.call_gemini = original
    ended = datetime.now(timezone.utc)

    env = envelope if isinstance(envelope, dict) else {}
    status = env.get("status")
    route = env.get("simulation_id")
    validated = env.get("config")
    raw_candidates = rec_raw.raw_simulate_candidates()
    raw_last = raw_candidates[-1] if raw_candidates else None

    rec: dict = {
        "case_id": case["id"],
        "case_label": case["label"],
        "run_id": run_id,
        "prompt": case["prompt"],
        "timestamp": started.isoformat(),
        "duration_seconds": round((ended - started).total_seconds(), 2),
        "provider": "google-gemini",
        "model": MODEL,
        "runtime_head": _git_sha(),
        "cache_version": runtime_identity()["cache_version"],
        "http_requests": budget.http_requests - before,
        "transient_hits": budget.transient_hits,
        "stage_temperatures": rec_raw.stage_temperatures(),
        "pipeline_error": err,
        # ── analyze (W3-LIVE-C1: bằng chứng CƠ CHẾ, thiếu ở lượt baseline) ──
        "analyze_prescribed_raw": (obs.analyze() or {}).get("prescribed_procedure"),
        "analyze_prescribed_canonical": (obs.analyze() or {}).get("canonical_prescribed"),
        "analyze_result_ownership": (obs.analyze() or {}).get("result_ownership"),
        # ── raw (TRƯỚC validator) ──
        "raw_classify_target": (obs.classify() or {}).get("simulation_id"),
        "raw_classify_status": (obs.classify() or {}).get("status"),
        "raw_candidate": raw_last,
        "raw_candidate_attempts": len(raw_candidates),
        "raw_candidate_leak_keys": _leak_keys_in(raw_last, route or case["expect_route"]),
        "raw_candidate_extra_keys": _extra_keys_in(raw_last) if route == TARGET else [],
        "raw_text": raw_last.get("text") if isinstance(raw_last, dict) else None,
        "raw_code_points": _cp_labels(_code_points(
            raw_last.get("text") if isinstance(raw_last, dict) else None)),
        # ── validated (SAU validator) ──
        "final_status": status,
        "final_route": route,
        "final_family": sorted({m.family_id.value
                                for m in CATALOG[route].family_memberships})
                        if route in CATALOG else [],
        "validated_candidate": validated,
        "validated_text": validated.get("text") if isinstance(validated, dict) else None,
        "validated_encoding": validated.get("encoding") if isinstance(validated, dict) else None,
        "validated_code_points": _cp_labels(_code_points(
            validated.get("text") if isinstance(validated, dict) else None)),
        "validated_leak_keys": _leak_keys_in(validated, route or case["expect_route"]),
        "failure_category": env.get("failure_category"),
        "error_code": env.get("error_code"),
        "learner_message": env.get("learner_reason") or env.get("reason"),
        "simulate_attempts": obs.simulate_attempts(),
        "gates_fired": [g for g in obs.gates() if g.get("fired")],
        # ── engine handoff: KHÔNG chạy được từ backend (xem docstring) ──
        "engine_handoff": "NOT_EXECUTED_BACKEND_HAS_NO_ENGINE",
        "engine_handoff_reason": (
            "Engine tất định của binary.character_encoding nằm ở FRONTEND; backend "
            "cố ý chỉ kiểm định. Harness FE duy nhất chạy Chrome — checkpoint cấm."
        ),
    }

    # Kiểm lại validator ĐỘC LẬP trên chính config envelope trả về.
    if isinstance(validated, dict) and route == TARGET:
        revalidated, verr = validate_character_encoding_config(validated)
        rec["validator_recheck_pass"] = revalidated is not None
        rec["validator_recheck_error"] = verr
    else:
        rec["validator_recheck_pass"] = None
        rec["validator_recheck_error"] = None

    _judge(case, rec)
    return rec


def _judge(case: dict, rec: dict) -> None:
    """Gán verdict + 7 chỉ số semantic fidelity (§6). Safe failure KHÔNG bao giờ
    bị gộp với unsafe acceptance."""
    flags = {
        "semantic_loss": False,
        "fabricated_input": False,
        "result_leakage": False,
        "generic_leak": False,
        "unsafe_acceptance": False,
        "wrong_target_acceptance": False,
        "safe_failure": False,
        # W3-LIVE-C1 §10 — case ĐƯỢC HỖ TRỢ bị chính mechanism gate chặn.
        "mechanism_gate_failure": False,
    }
    why: list[str] = []
    status, route = rec["final_status"], rec["final_route"]
    if case["expect_status"] == "ok" and rec.get("error_code") == "gate_mechanism_ownership":
        flags["mechanism_gate_failure"] = True

    # Lỗi hạ tầng: KHÔNG BAO GIỜ thành bằng chứng sản phẩm.
    if status is None and _is_infra_error(rec["pipeline_error"]):
        rec["verdict"] = "INFRA_ERROR"
        rec["verdict_reasons"] = [f"không gọi được API: {rec['pipeline_error']}"]
        rec["flags"] = flags
        rec["root_cause"] = ["TRANSPORT_FAILURE"]
        return

    # Rò kết quả tính theo RAW candidate (validator từ chối vẫn tính là LLM đã rò).
    if rec["raw_candidate_leak_keys"] or rec["validated_leak_keys"]:
        flags["result_leakage"] = True
        why.append(f"rò kết quả trong candidate: "
                   f"{rec['raw_candidate_leak_keys'] or rec['validated_leak_keys']}")
    if route == GENERIC:
        flags["generic_leak"] = True
        why.append("rơi về generic.rule_scene")

    if case["expect_status"] == "ok":
        if status != "ok":
            flags["safe_failure"] = True
            why.append(f"status={status} (mong ok) — thất bại AN TOÀN, không dựng sai")
            verdict = "FAIL_SAFE"
        elif route != case["expect_route"]:
            flags["wrong_target_acceptance"] = True
            why.append(f"route={route} (mong {case['expect_route']})")
            verdict = "FAIL"
        else:
            verdict = "PASS"
            if case["expect_text"] is not None:
                got_cps = _code_points(rec["validated_text"])
                if rec["validated_text"] != case["expect_text"]:
                    flags["semantic_loss"] = True
                    why.append(f"text={rec['validated_text']!r} (mong {case['expect_text']!r})")
                    verdict = "FAIL"
                elif got_cps != case["expect_code_points"]:
                    flags["semantic_loss"] = True
                    why.append(f"code point {_cp_labels(got_cps)} "
                               f"(mong {_cp_labels(case['expect_code_points'])})")
                    verdict = "FAIL"
                if rec["validated_encoding"] != case["expect_encoding"]:
                    flags["semantic_loss"] = True
                    why.append(f"encoding={rec['validated_encoding']} "
                               f"(mong {case['expect_encoding']})")
                    verdict = "FAIL"
            if rec["validator_recheck_pass"] is False:
                why.append(f"validator kiểm lại TRƯỢT: {rec['validator_recheck_error']}")
                verdict = "FAIL"
            if flags["result_leakage"]:
                verdict = "FAIL"
    else:
        # Case PHẢI từ chối.
        if status == "ok":
            flags["unsafe_acceptance"] = True
            why.append(f"dựng mô phỏng ({route}) cho đề phải từ chối")
            verdict = "UNSAFE_ACCEPTANCE"
            if isinstance(rec["validated_candidate"], dict) and rec["validated_text"]:
                flags["fabricated_input"] = True
                why.append(f"tự bịa dữ kiện: text={rec['validated_text']!r}, "
                           f"encoding={rec['validated_encoding']}")
        elif flags["generic_leak"]:
            verdict = "FAIL"
        else:
            verdict = "PASS"
            why.append(f"từ chối an toàn · category={rec['failure_category']} "
                       f"· code={rec['error_code']}")
    rec["verdict"] = verdict
    rec["verdict_reasons"] = why
    rec["flags"] = flags
    rec["root_cause"] = _root_cause(case, rec, flags)


def _root_cause(case: dict, rec: dict, flags: dict) -> list[str]:
    if rec.get("verdict") in ("PASS",):
        return []
    causes: list[str] = []
    if flags["wrong_target_acceptance"] or flags["generic_leak"]:
        causes.append("CLASSIFICATION_ERROR")
    if flags["semantic_loss"] or flags["result_leakage"]:
        causes.append("SPEC_SYNTHESIS_ERROR")
    if flags["fabricated_input"]:
        causes.append("INPUT_SUFFICIENCY_ERROR")
    if rec.get("validator_recheck_pass") is False:
        causes.append("VALIDATOR_ERROR")
    if rec.get("verdict") == "FAIL_SAFE" and not causes:
        causes.append("MODEL_VARIABILITY")
    return causes or ["UNKNOWN"]


def _summarize(records: list[dict], runs: int, aborted) -> tuple[str, list[str], dict]:
    """Phân loại theo ĐÚNG tiêu chí §8: safe failure / model không ổn định →
    PARTIAL; chỉ chấp nhận SAI mới là FAILED."""
    verdicts = [r["verdict"] for r in records]
    agg = {k: sum(1 for r in records if r["flags"][k])
           for k in ("semantic_loss", "fabricated_input", "result_leakage",
                     "generic_leak", "unsafe_acceptance", "wrong_target_acceptance",
                     "safe_failure", "mechanism_gate_failure")}
    hard_fail = (agg["unsafe_acceptance"] or agg["generic_leak"]
                 or agg["result_leakage"] or agg["fabricated_input"]
                 or agg["wrong_target_acceptance"] or "FAIL" in verdicts)
    if aborted or len(records) < len(CASES) * runs or "INFRA_ERROR" in verdicts:
        overall = "W3_LIVE_BLOCKED"
    elif hard_fail:
        overall = "W3_LIVE_FAILED"
    elif all(v == "PASS" for v in verdicts):
        overall = "W3_LIVE_VERIFIED"
    else:
        overall = "W3_LIVE_PARTIAL"
    return overall, verdicts, agg


def _rescore() -> int:
    """Chấm LẠI artifact đã có — KHÔNG gọi API, không chạy thêm case.

    Dùng khi phát hiện phép đo của harness sai (không phải khi kết quả xấu):
    dữ liệu live giữ NGUYÊN VĂN, chỉ verdict/flag được tính lại."""
    if not OUT_JSON.exists():
        print(f"Chưa có artifact để chấm lại: {OUT_JSON}")
        return 1
    artifact = json.loads(OUT_JSON.read_text(encoding="utf-8"))
    records = artifact["records"]
    by_id = {c["id"]: c for c in CASES}
    before = [r["verdict"] for r in records]

    for rec in records:
        case = by_id[rec["case_id"]]
        route = rec["final_route"] or case["expect_route"]
        rec["raw_candidate_leak_keys"] = _leak_keys_in(rec["raw_candidate"], route)
        rec["raw_candidate_extra_keys"] = (
            _extra_keys_in(rec["raw_candidate"]) if rec["final_route"] == TARGET else [])
        rec["validated_leak_keys"] = _leak_keys_in(rec["validated_candidate"], route)
        _judge(case, rec)

    runs = max(1, artifact.get("cases_run", len(records)) // len(CASES))
    overall, verdicts, agg = _summarize(records, runs, artifact.get("aborted"))
    artifact["metrics"] = {
        "pass": verdicts.count("PASS"), "fail": verdicts.count("FAIL"),
        "fail_safe": verdicts.count("FAIL_SAFE"),
        "unsafe_acceptance_verdict": verdicts.count("UNSAFE_ACCEPTANCE"),
        "infra_error": verdicts.count("INFRA_ERROR"), **agg,
    }
    artifact["classification"] = overall
    artifact["rescore"] = {
        "applied_at": datetime.now(timezone.utc).isoformat(),
        "api_calls_used": 0,
        "reason": (
            "Harness defect: bộ khoá rò-kết-quả của binary.character_encoding bị áp "
            "cho MỌI route, nên `decimalValue` — INPUT HỢP LỆ của "
            "binary.decimal_to_binary — bị chấm là rò kết quả và LIVE-ENC-4 FAIL oan; "
            "lỗi này lật phân loại tổng thể từ PARTIAL sang FAILED. Đã tách hợp đồng "
            "rò-kết-quả theo TARGET và chấm lại trên CHÍNH dữ liệu live đã thu."
        ),
        "verdicts_before": before,
        "verdicts_after": [r["verdict"] for r in records],
        "data_unchanged": "Mọi trường live (prompt/raw/validated/http/timestamp) giữ nguyên văn.",
    }
    OUT_JSON.write_text(json.dumps(artifact, ensure_ascii=False, indent=2) + "\n",
                        encoding="utf-8")
    with OUT_JSONL.open("w", encoding="utf-8") as fh:
        for r in records:
            fh.write(json.dumps(r, ensure_ascii=False) + "\n")
    print(f"RESCORED (0 API call) · {before} → {[r['verdict'] for r in records]}")
    print(f"{overall} · {verdicts.count('PASS')}/{len(records)} PASS → {OUT_JSON}")
    return 0


async def _probe_analyze() -> int:
    """W3-LIVE-C1 §2 — CHẨN ĐOÁN: analyze thật sự phát `prescribed_procedure` nào
    cho ba case bị chặn? Gọi THẲNG `stage_analyze` (1 HTTP/case), KHÔNG chạy
    classify/simulate — root cause phải được ĐO, không suy.

    Cần đo vì `analyze_exposed_values()` KHÔNG chứa `character_code_mapping`:
    enum đóng chỉ cho phép `binary_positional_weights` / `non_binary_base` /
    `none`, nên cơ chế mà target sở hữu là BẤT KHẢ PHÁT."""
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("CHƯA có GEMINI_API_KEY.")
        return 1
    reachable, net_err = _network_reachable()
    if not reachable:
        print(f"BỊ CHẶN: không có mạng ({net_err}).")
        return 2

    budget = ApiBudget(max_api_calls=6, max_attempts=2)
    gemini.set_budget(budget)
    rows = []
    try:
        for case in CASES[:3]:               # ENC-1, ENC-2, ENC-3
            before = budget.http_requests
            analysis = await pipeline.stage_analyze(case["prompt"], api_key)
            raw = analysis.get("prescribed_procedure")
            row = {
                "case_id": case["id"],
                "prompt": case["prompt"],
                "prescribed_procedure_raw": raw,
                "prescribed_canonical": canonical_mechanism(raw),
                "requested_mechanisms": analysis.get("requested_mechanisms"),
                "result_ownership": analysis.get("result_ownership"),
                "http_requests": budget.http_requests - before,
            }
            rows.append(row)
            print(f"{case['id']}: prescribed={row['prescribed_canonical']!r} "
                  f"requested={row['requested_mechanisms']} "
                  f"ownership={row['result_ownership']}", flush=True)
    except BudgetExceeded as e:
        print(f"BUDGET: {e}")
    finally:
        gemini.set_budget(None)

    payload = {
        "probe": "W3-LIVE-C1 §2 analyze root-cause",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "git_sha": _git_sha(), "provider": "google-gemini", "model": MODEL,
        "analyze_temperature": 0.1,
        "http_used": budget.http_requests,
        "analyze_exposed_positional": [
            v for v in analyze_exposed_values() if v.startswith("positional_representation.")
        ],
        "w3_owned_mechanisms": ["positional_representation.character_code_mapping"],
        "rows": rows,
    }
    print("\n" + json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


async def _main(argv) -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--max-http", type=int, default=MAX_HTTP)
    p.add_argument("--runs", type=int, default=RUNS)
    p.add_argument("--out-dir", default=None,
                   help="thư mục artifact (mặc định w3-live; rerun C1 truyền w3-live-c1)")
    args = p.parse_args(argv)
    _set_out_dir(args.out_dir)

    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("CHƯA có GEMINI_API_KEY.")
        return 1

    cap = min(MAX_HTTP, max(1, args.max_http))
    reachable, net_err = _network_reachable()
    if not reachable:
        print(f"BỊ CHẶN: không có mạng ra ngoài ({net_err}). Không tiêu ngân sách.")
        return 2

    # max_attempts=2 ⇒ 1 lần đầu + ĐÚNG 1 retry TRANSPORT (checkpoint §3).
    budget = ApiBudget(max_api_calls=cap, max_attempts=2)
    gemini.set_budget(budget)
    records: list[dict] = []
    aborted = None
    try:
        for case in CASES:
            for run_id in range(1, args.runs + 1):
                print(f"→ {case['id']} run{run_id} …", flush=True)
                rec = await _run_once(case, run_id, api_key, budget)
                records.append(rec)
                print(f"   {rec['verdict']} · http={rec['http_requests']} "
                      f"· status={rec['final_status']} · route={rec['final_route']} "
                      f"· text={rec['validated_text']!r}", flush=True)
    except BudgetExceeded as e:
        aborted = f"BUDGET: chạm trần {cap} HTTP — dừng, KHÔNG nâng trần. ({e})"
        print(aborted)
    finally:
        gemini.set_budget(None)

    overall, verdicts, agg = _summarize(records, args.runs, aborted)

    artifact = {
        "wave": "M17 W3-LIVE",
        "target": TARGET,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "git_sha": _git_sha(),
        "provider": "google-gemini",
        "model": MODEL,
        "api_endpoint": "https://generativelanguage.googleapis.com/v1beta/models/"
                        f"{MODEL}:generateContent",
        "sampling": {"analyze_temperature": 0.1, "classify_temperature": 0.0,
                     "simulate_temperature": 0.1,
                     "transport_max_attempts": budget.max_attempts,
                     "simulate_validation_retries": 3},
        "spec_version": SPEC_VERSION,
        "encodings": list(ENCODINGS),
        "runner_process_identity": runtime_identity(),
        "runtime_mode": "IN_PROCESS (không qua container Docker)",
        "http_budget": cap,
        "http_used": budget.http_requests,
        "transient_hits": budget.transient_hits,
        "retry_requests": budget.retry_requests,
        "aborted": aborted,
        "cases_expected": len(CASES) * args.runs,
        "cases_run": len(records),
        "metrics": {
            "pass": verdicts.count("PASS"),
            "fail": verdicts.count("FAIL"),
            "fail_safe": verdicts.count("FAIL_SAFE"),
            "unsafe_acceptance_verdict": verdicts.count("UNSAFE_ACCEPTANCE"),
            "infra_error": verdicts.count("INFRA_ERROR"),
            **agg,
        },
        "classification": overall,
        "limitations": [
            "Engine tất định của W3 ở FRONTEND — runner KHÔNG chạy engine; "
            "engine_handoff = NOT_EXECUTED. Bằng chứng engine là offline "
            "(encoding-module.test.tsx) + REAL_SIMULATION audit tại 472314e.",
            "Runner chạy IN-PROCESS; không nói gì về container Docker.",
            "6 case × 2 lượt là SMOKE — không phải benchmark độ chính xác tổng quát "
            "trên mọi đề tiếng Việt.",
        ],
        "records": records,
    }
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(artifact, ensure_ascii=False, indent=2) + "\n",
                        encoding="utf-8")
    with OUT_JSONL.open("w", encoding="utf-8") as fh:
        for r in records:
            fh.write(json.dumps(r, ensure_ascii=False) + "\n")

    print(f"\n{overall} · HTTP {budget.http_requests}/{cap} · "
          f"{verdicts.count('PASS')}/{len(records)} PASS → {OUT_JSON}")
    return 0


def main() -> int:
    # Chấm lại KHÔNG gọi API ⇒ không cần opt-in live.
    if "--rescore" in sys.argv[1:]:
        return _rescore()
    if "--probe-analyze" in sys.argv[1:]:
        if os.getenv("ALLOW_LIVE_AI") != "1":
            print("TỪ CHỐI: probe gọi API thật, cần ALLOW_LIVE_AI=1.")
            return 1
        return asyncio.run(_probe_analyze())
    if os.getenv("ALLOW_LIVE_AI") != "1":
        print("TỪ CHỐI: cần ALLOW_LIVE_AI=1.")
        return 1
    return asyncio.run(_main(sys.argv[1:]))


if __name__ == "__main__":
    sys.exit(main())
