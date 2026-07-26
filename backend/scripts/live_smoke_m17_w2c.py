# -*- coding: utf-8 -*-
"""M17 W2C — LIVE SMOKE `algorithm.bounded_control_flow` (4 case / trần 12 HTTP).

Chạy 4 prompt tiếng Việt qua production `run_pipeline` THẬT (gemini-2.5-flash)
với `AttemptObserver` + `ApiBudget` (trần CỨNG 12). Không sửa production, không
repair, không retry thêm, không chạy lại đến khi đẹp.

GIỚI HẠN PHẢI GHI RÕ: engine tất định của luồng điều khiển sống ở FRONTEND
(`core/program.ts`) — envelope backend KHÔNG chứa trace. Vì vậy live smoke kiểm
**định tuyến + tính hợp lệ của spec + không rò kết quả**, còn "chạy đúng" đã
chứng minh offline (20 test `program.test.ts` + 40 test `test_program_spec.py`).
Để vẫn trả lời được "spec này có ra đúng đáp số không", runner dựng một ORACLE
ĐỘC LẬP nhỏ (hàm `_oracle` dưới đây) — nó là HARNESS, không phải production, và
cố tình viết tách khỏi `core/program.ts` để hai bên không cùng sai một kiểu.

OPT-IN: ALLOW_LIVE_AI=1.

Chạy:
    ALLOW_LIVE_AI=1 python scripts/live_smoke_m17_w2c.py [--max-http 12]
"""

from __future__ import annotations

import asyncio
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.ai import gemini  # noqa: E402
from app.ai.gemini import ApiBudget, BudgetExceeded, MODEL  # noqa: E402
from app.ai import pipeline  # noqa: E402
from app.evaluation.observer import AttemptObserver  # noqa: E402
from app.runtime_identity import runtime_identity  # noqa: E402
from app.simulation.catalog import CATALOG  # noqa: E402
from app.simulation.program_spec import structures_present  # noqa: E402
from app.validation.program import validate_program_config  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "docs" / "evaluation" / "m17" / "w2c" / "bounded_control_flow_live_smoke.json"
TARGET = "algorithm.bounded_control_flow"
GENERIC = "generic.rule_scene"
MAX_HTTP = 12

CASES = [
    {
        "id": "live-cf1-assign-branch",
        "prompt": "Cho x = -2. Nếu x lớn hơn 0 thì gán y bằng 1, ngược lại gán y bằng -1. "
                  "Hãy mô phỏng chương trình từng bước.",
        "expect_status": "ok", "expect_route": TARGET,
        "require_structures": ["assign", "branch"],
        "expect_final": {"y": -1},
    },
    {
        "id": "live-cf2-bounded-while",
        "prompt": "Ban đầu x bằng 1. Trong khi x nhỏ hơn 5, mỗi lượt tăng x thêm 1. "
                  "Hãy mô phỏng sự thay đổi của x qua từng vòng lặp.",
        "expect_status": "ok", "expect_route": TARGET,
        "require_structures": ["assign", "loop"],
        "expect_final": {"x": 5},
    },
    {
        "id": "live-cf3-insufficient",
        "prompt": "Hãy mô phỏng một vòng lặp while.",
        "expect_status": "unsupported", "expect_route": None,
        "require_structures": [], "expect_final": None,
    },
    {
        "id": "live-cf4-unsupported-recursion",
        "prompt": "Hãy mô phỏng hàm đệ quy tính giai thừa của n.",
        "expect_status": "not_ok", "expect_route": None,
        "require_structures": [], "expect_final": None,
    },
]


# ── ORACLE ĐỘC LẬP (harness, KHÔNG phải production) ─────────────
def _oracle(cfg: dict, max_steps: int = 400) -> tuple[dict | None, str]:
    """Diễn giải ProgramSpec đã validate → môi trường biến cuối.

    Viết TÁCH khỏi `core/program.ts` có chủ đích: nếu hai bên cùng sai một kiểu
    thì phép đối chiếu vô nghĩa."""
    env = {v["name"]: (v["int_value"] if v["type"] == "integer" else v["bool_value"])
           for v in cfg["variables"]}
    ex = {e["id"]: e for e in cfg["expressions"]}
    st = {s["id"]: s for s in cfg["statements"]}
    budget = [max_steps]

    def ev(eid):
        n = ex[eid]
        k = n["kind"]
        if k == "int":
            return n["int_value"]
        if k == "bool":
            return n["bool_value"]
        if k == "var":
            return env[n["name"]]
        if k == "unary":
            v = ev(n["operand"])
            return (not v) if n["op"] == "not" else -v
        if k == "logic":
            left = ev(n["left"])
            if n["op"] == "and":
                return bool(left) and bool(ev(n["right"]))
            return bool(left) or bool(ev(n["right"]))
        left, right = ev(n["left"]), ev(n["right"])
        if k == "compare":
            return {"==": left == right, "!=": left != right, "<": left < right,
                    "<=": left <= right, ">": left > right, ">=": left >= right}[n["op"]]
        if n["op"] == "+":
            return left + right
        if n["op"] == "-":
            return left - right
        if n["op"] == "*":
            return left * right
        if right == 0:
            return 0
        return left // right if n["op"] == "//" else left % right

    def run(ids) -> str | None:
        for sid in ids:
            if budget[0] <= 0:
                return "limit_reached"
            budget[0] -= 1
            s = st[sid]
            if s["kind"] == "assign":
                env[s["target"]] = ev(s["value"])
            elif s["kind"] == "output":
                ev(s["value"])
            elif s["kind"] == "if":
                body = s["then_body"] if ev(s["condition"]) else s["else_body"]
                r = run(body)
                if r:
                    return r
            else:
                it = 0
                while ev(s["condition"]):
                    if it >= s["max_iterations"] or budget[0] <= 0:
                        return "limit_reached"
                    it += 1
                    budget[0] -= 1
                    r = run(s["body"])
                    if r:
                        return r
        return None

    try:
        stop = run(cfg["main"])
    except Exception as err:  # oracle không được làm hỏng cả lượt chạy
        return None, f"oracle_error: {err}"
    return env, stop or "completed"


def _git_sha() -> str:
    try:
        return subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True,
                              check=True, cwd=ROOT).stdout.strip()
    except Exception:
        return "unknown"


def _leaks_tech(text) -> bool:
    """Thông điệp học sinh KHÔNG được lộ token kỹ thuật / JSON path / enum."""
    if not isinstance(text, str):
        return False
    import re
    bad = ("program_version", "then_body", "else_body", "max_iterations", "statements",
           "expressions", "insufficient_specification", "capability_gap",
           "input_insufficient", "InputKind", TARGET, "$.", "{", "}", "schema", "Traceback")
    return any(b in text for b in bad) or re.search(r"\b[a-z]+_[a-z_]{3,}\b", text) is not None


_INFRA_MARKERS = (
    "All connection attempts failed", "getaddrinfo", "Temporary failure in name resolution",
    "Connection refused", "SSLError", "timed out", "Name or service not known",
    "Network is unreachable", "ProxyError",
)


def _is_infra_error(err) -> bool:
    """Lỗi MẠNG/HẠ TẦNG ≠ hành vi sản phẩm."""
    return isinstance(err, str) and any(m.lower() in err.lower() for m in _INFRA_MARKERS)


def _network_reachable(host: str = "generativelanguage.googleapis.com", port: int = 443) -> tuple[bool, str]:
    """Chặn TRƯỚC khi đốt ngân sách: không có mạng thì đừng chạy case nào."""
    # Dùng phân giải tên (thất bại NHANH) chứ không mở kết nối: ở môi trường bị
    # chặn egress, `create_connection` có thể treo hàng phút vì gói tin bị nuốt.
    import socket
    try:
        socket.getaddrinfo(host, port, proto=socket.IPPROTO_TCP)
        return True, ""
    except Exception as err:
        return False, f"{type(err).__name__}: {err}"


async def _run_case(case, api_key, budget) -> dict:
    obs = AttemptObserver()
    before = budget.http_requests
    envelope, err = None, None
    try:
        envelope = await pipeline.run_pipeline(case["prompt"], api_key,
                                               pattern_store=None, observer=obs)
    except BudgetExceeded:
        raise
    except Exception as e:      # validator cạn lượt → RuntimeError (từ chối, không phải crash)
        err = str(e)
    http = budget.http_requests - before

    env = envelope if isinstance(envelope, dict) else {}
    status = env.get("status")
    route = env.get("simulation_id")
    cfg = env.get("config")
    learner = env.get("learner_reason") or env.get("reason")

    rec = {
        "id": case["id"], "prompt": case["prompt"],
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "model": MODEL, "provider": "google-gemini",
        "http_requests": http,
        "pipeline_status": status, "pipeline_error": err,
        "route": route,
        "family": sorted({m.family_id.value for m in CATALOG[route].family_memberships})
                  if route in CATALOG else [],
        "generic_fallback": route == GENERIC,
        "failure_category": env.get("failure_category"),
        "error_code": env.get("error_code"),
        "executor_invoked": False,   # engine tất định nằm ở FE; backend không chạy
        "learner_message": learner,
        "learner_message_leaks_tech": _leaks_tech(learner),
        "simulate_attempts": obs.simulate_attempts() if hasattr(obs, "simulate_attempts") else None,
    }

    # ── spec: hợp lệ theo NGỮ PHÁP ĐÓNG + không rò kết quả ──
    if isinstance(cfg, dict):
        revalidated, verr = validate_program_config(cfg)
        present = structures_present(cfg)
        rec["spec_summary"] = {
            "variables": [v["name"] for v in cfg.get("variables", [])],
            "statement_kinds": [s.get("kind") for s in cfg.get("statements", [])],
            "structures_present": [k for k, on in present.items() if on],
            "statement_count": len(cfg.get("statements", [])),
        }
        rec["validator_pass"] = revalidated is not None
        rec["validator_error"] = verr
        rec["result_leak_keys"] = sorted(
            k for k in cfg
            if k in {"trace", "steps", "environment", "final_environment",
                     "result", "iterations", "output_values"})
        missing = [s for s in case["require_structures"] if not present.get(s)]
        rec["missing_structures"] = missing
        if revalidated is not None:
            final_env, stop = _oracle(revalidated)
            rec["oracle_final_env"] = final_env
            rec["oracle_completion"] = stop
    else:
        rec["spec_summary"] = None
        rec["validator_pass"] = None
        rec["result_leak_keys"] = []
        rec["missing_structures"] = list(case["require_structures"])

    # ── PHÁN QUYẾT ──
    # BẪY ĐÃ SẬP MỘT LẦN: khi mạng hỏng, `run_pipeline` ném lỗi kết nối ⇒ KHÔNG
    # có mô phỏng nào được dựng ⇒ mọi assertion "phải từ chối" thoả mãn RỖNG và
    # case từ chối được chấm PASS. Lỗi hạ tầng KHÔNG BAO GIỜ được thành bằng
    # chứng sản phẩm — bắt riêng trước mọi phán quyết khác.
    if status is None and _is_infra_error(err):
        rec["verdict"] = "INFRA_ERROR"
        rec["verdict_reasons"] = [f"không gọi được API: {err}"]
        return rec

    verdict, why = "PASS", []
    if case["expect_status"] == "ok":
        if status != "ok":
            verdict, _ = "FAIL_SAFE", why.append(f"status={status} (mong ok)")
        elif route != case["expect_route"]:
            verdict, _ = "FAIL", why.append(f"route={route}")
        elif not rec["validator_pass"]:
            verdict, _ = "FAIL", why.append("spec không qua validator khi kiểm lại")
        elif rec["missing_structures"]:
            verdict, _ = "FAIL", why.append(f"thiếu cấu trúc {rec['missing_structures']}")
        elif rec["result_leak_keys"]:
            verdict, _ = "FAIL", why.append(f"spec mang kết quả {rec['result_leak_keys']}")
        else:
            exp = case["expect_final"] or {}
            got = rec.get("oracle_final_env") or {}
            wrong = {k: (v, got.get(k)) for k, v in exp.items() if got.get(k) != v}
            if wrong:
                verdict, _ = "FAIL", why.append(f"đáp số lệch {wrong}")
    else:
        if status == "ok":
            verdict, _ = "UNSAFE_ACCEPTANCE", why.append("dựng mô phỏng cho đề phải từ chối")
        elif rec["generic_fallback"]:
            verdict, _ = "FAIL", why.append("rơi về generic")
        elif case["id"] == "live-cf3-insufficient" and \
                rec["failure_category"] != "insufficient_specification":
            verdict, _ = "FAIL", why.append(f"failure_category={rec['failure_category']}")
        elif rec["learner_message_leaks_tech"]:
            verdict, _ = "FAIL", why.append("thông điệp học sinh lộ token kỹ thuật")
    rec["verdict"] = verdict
    rec["verdict_reasons"] = why
    return rec


async def _main() -> int:
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("CHƯA có GEMINI_API_KEY."); return 1
    argv = sys.argv[1:]
    cap = MAX_HTTP
    if "--max-http" in argv:
        cap = min(MAX_HTTP, max(1, int(argv[argv.index("--max-http") + 1])))

    reachable, net_err = _network_reachable()
    budget = ApiBudget(max_api_calls=cap)
    gemini.set_budget(budget)
    results, aborted = [], None
    if not reachable:
        # Không tiêu một đơn vị ngân sách nào cho một lượt chạy không thể có
        # bằng chứng. Báo BỊ CHẶN, không báo FAIL — sản phẩm chưa được kiểm.
        gemini.set_budget(None)
        artifact = {
            "wave": "M17 W2C-LIVE", "target": TARGET,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "git_sha": _git_sha(), "model": MODEL, "provider": "google-gemini",
            "runner_process_identity": runtime_identity(),
            "http_budget": cap, "http_used": 0,
            "aborted": f"KHÔNG CÓ MẠNG RA NGOÀI: {net_err}",
            "metrics": {"cases": 0, "pass": 0, "fail": 0, "unsafe_acceptance": 0,
                        "generic_leak": 0, "result_leak": 0, "semantic_loss": 0},
            "classification": "W2C_LIVE_BLOCKED_NO_NETWORK",
            "note": "KHÔNG có bằng chứng live nào được thu thập. Đây là giới hạn MÔI "
                    "TRƯỜNG (egress bị chặn), KHÔNG phải kết quả của sản phẩm. Không "
                    "được đọc thành PASS, cũng không được đọc thành FAIL.",
            "cases": [],
        }
        OUT.parent.mkdir(parents=True, exist_ok=True)
        OUT.write_text(json.dumps(artifact, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(f"BỊ CHẶN: không có mạng ra ngoài ({net_err}). Không chạy case nào, "
              f"không tiêu ngân sách. → {OUT}")
        return 2
    try:
        for case in CASES:
            print(f"→ {case['id']} …", flush=True)
            rec = await _run_case(case, api_key, budget)
            results.append(rec)
            print(f"   {rec['verdict']} · http={rec['http_requests']} · "
                  f"status={rec['pipeline_status']} · route={rec['route']}", flush=True)
    except BudgetExceeded as e:
        aborted = f"BUDGET: chạm trần {cap} HTTP — dừng, KHÔNG nâng budget. ({e})"
        print(aborted)
    finally:
        gemini.set_budget(None)

    verdicts = [r["verdict"] for r in results]
    unsafe = sum(1 for v in verdicts if v == "UNSAFE_ACCEPTANCE")
    leak = sum(1 for r in results if r["generic_fallback"])
    if aborted or len(results) < len(CASES):
        overall = "W2C_LIVE_INCOMPLETE"
    elif unsafe or "FAIL" in verdicts:
        overall = "W2C_LIVE_FAIL"
    elif all(v == "PASS" for v in verdicts):
        overall = "W2C_LIVE_PASS"
    else:
        overall = "W2C_LIVE_PARTIAL"

    artifact = {
        "wave": "M17 W2C-LIVE",
        "target": TARGET,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "git_sha": _git_sha(),
        "model": MODEL,
        "provider": "google-gemini",
        "runner_process_identity": runtime_identity(),
        "http_budget": cap,
        "http_used": budget.http_requests,
        "aborted": aborted,
        "metrics": {
            "cases": len(results),
            "pass": verdicts.count("PASS"),
            "fail_safe": verdicts.count("FAIL_SAFE"),
            "fail": verdicts.count("FAIL"),
            "unsafe_acceptance": unsafe,
            "generic_leak": leak,
            "result_leak": sum(1 for r in results if r.get("result_leak_keys")),
            "semantic_loss": sum(1 for r in results if r.get("missing_structures")
                                 and r.get("pipeline_status") == "ok"),
        },
        "classification": overall,
        "note": "Engine tất định của luồng điều khiển nằm ở FRONTEND (core/program.ts) nên "
                "envelope backend KHÔNG có trace: live smoke kiểm ĐỊNH TUYẾN + SPEC HỢP LỆ + "
                "KHÔNG RÒ KẾT QUẢ; đáp số đối chiếu bằng ORACLE ĐỘC LẬP trong harness. "
                "Chạy đúng từng bước đã chứng minh offline.",
        "cases": results,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(artifact, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"\n{overall} · HTTP {budget.http_requests}/{cap} → {OUT}")
    return 0


def main() -> int:
    if os.getenv("ALLOW_LIVE_AI") != "1":
        print("TỪ CHỐI: cần ALLOW_LIVE_AI=1.")
        return 1
    return asyncio.run(_main())


if __name__ == "__main__":
    sys.exit(main())
