# -*- coding: utf-8 -*-
"""M17-RC1 §D — sinh artifact SEMANTIC COMPLETENESS.

Probe DẪN XUẤT TỪ REGISTRY chính sách (`FAMILY_OPERATION_POLICY` +
`FAMILY_MECHANISMS`), KHÔNG viết tay danh sách ca:

- family `single` có ≥2 cơ chế → probe "xin TẤT CẢ cơ chế" ⇒ phải BLOCKED
  (ca A: 4 kiểu duyệt cây · ca C: 2 thuật toán sắp xếp · ca D: BFS+DFS đều là
  thể hiện của luật này, tự sinh);
- family `multiple`/`pipeline` → probe cùng dạng ⇒ phải PASS (ca B: đóng gói
  PDU — nhiều thao tác nối tiếp KHÔNG phải xung đột);
- mọi family → probe MỘT cơ chế ⇒ phải PASS (ca E: chống chặn oan).

Thêm family/cơ chế mới ⇒ probe tự xuất hiện, không phải sửa script.

    python scripts/semantic_completeness_report.py --json <out.json> [--md <out.md>]
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.runtime_identity import runtime_identity  # noqa: E402
from app.simulation.completeness_gate import (  # noqa: E402
    check_represented_coverage,
    check_requested_combination,
    completeness_report,
)
from app.simulation.mechanisms import (  # noqa: E402
    FAMILY_MECHANISMS,
    analyze_exposed_values,
    canonical_mechanism,
    mechanism_family,
)
from app.simulation.operation_policy import (  # noqa: E402
    FAMILY_OPERATION_POLICY,
    SINGLE,
    VARIANT_MECHANISM,
)

BLOCKED = "BLOCKED"
PASS = "PASS"


def analyze_expressible_families() -> set[str]:
    """Family mà analyze CÓ THỂ phát tín hiệu cơ chế.

    RANH GIỚI của chính báo cáo này (RC1-C đo được): probe dưới đây nạp THẲNG id
    cơ chế vào gate, nên chỉ chứng minh "cho trước analyze, gate quyết đúng" —
    KHÔNG chứng minh "analyze nói được điều đó". Family ngoài tập này thì gate
    KHÔNG BAO GIỜ nhận được dữ liệu ở đời thực (bằng chứng: case
    rc1c-scan-max-and-min trả ok và bỏ im lặng một nửa)."""
    return {
        mechanism_family(canonical_mechanism(v))
        for v in analyze_exposed_values()
        if canonical_mechanism(v)
    }


def _analysis(mechs: list[str]) -> dict:
    """Analyze TỐI THIỂU — chỉ trường gate đọc. Gate deterministic given
    analyze, không đọc text đề nên probe không cần đề thật."""
    return {"requested_mechanisms": list(mechs), "result_ownership": "provided"}


def _probe(probe_id: str, family: str, mechs: list[str], expect: str) -> dict:
    """Chạy MỘT probe qua gate THẬT (cả 2 pha), trả bản ghi máy-đọc."""
    fams = {family}
    analysis = _analysis(mechs)
    owned = set(mechs)

    phase1 = check_requested_combination(analysis, fams)
    if phase1 is not None:
        code, message, evidence = phase1
        rep = completeness_report(analysis, fams, owned, None, BLOCKED)
        rep["unsupported_combinations"] = evidence["unsupported_combinations"]
        decision, phase, error_code = BLOCKED, "requested_combination", code.value
    else:
        # PHA 2 mô phỏng spec đã validate: dựng config biểu diễn cơ chế ĐẦU TIÊN
        # (đúng hiện thực — spec single-variant chỉ mang một variant).
        cfg = _config_representing(family, mechs[0]) if mechs else {}
        phase2 = check_represented_coverage(analysis, fams, owned, cfg)
        if phase2 is not None:
            code, message, _ = phase2
            rep = completeness_report(analysis, fams, owned, cfg, BLOCKED)
            decision, phase, error_code = BLOCKED, "represented_coverage", code.value
        else:
            rep = completeness_report(analysis, fams, owned, cfg, PASS)
            decision, phase, error_code, message = PASS, None, None, None

    return {
        "probe_id": probe_id,
        "family_id": family,
        "expected_decision": expect,
        "actual_decision": decision,
        "match": decision == expect,
        "blocking_phase": phase,
        "error_code": error_code,
        "learner_message_present": bool(message),
        **rep,
    }


def _config_representing(family: str, mechanism: str) -> dict:
    """Config tối thiểu khiến spec biểu diễn ĐÚNG `mechanism` — tra ngược bảng
    dữ liệu variant→mechanism, không đoán chữ."""
    for variant, mech in VARIANT_MECHANISM.get(family, {}).items():
        if mech == mechanism:
            return {"variant": variant}
    return {}


def build_probes() -> list[dict]:
    probes: list[dict] = []
    expressible = analyze_expressible_families()
    for fid, pol in FAMILY_OPERATION_POLICY.items():
        fam = fid.value
        reachable = fam in expressible
        mechs = sorted(FAMILY_MECHANISMS.get(fid, ()))
        if not mechs:
            continue
        # E — một thao tác: KHÔNG BAO GIỜ được chặn (chống chặn oan).
        p = _probe(f"{fam}::single-operation", fam, mechs[:1], PASS)
        p["analyze_expressible"] = reachable
        probes.append(p)
        if len(mechs) < 2:
            continue
        # A/C/D vs B — xin TẤT CẢ cơ chế của family.
        expect = BLOCKED if pol.cardinality == SINGLE else PASS
        p = _probe(f"{fam}::all-mechanisms", fam, mechs, expect)
        p["analyze_expressible"] = reachable
        probes.append(p)
    return probes


def _policy_rows() -> list[dict]:
    expressible = analyze_expressible_families()
    return [
        {
            "family_id": fid.value,
            "analyze_expressible": fid.value in expressible,
            "operation_cardinality": pol.cardinality,
            "max_operations": pol.max_operations,
            "mechanism_count": len(FAMILY_MECHANISMS.get(fid, ())),
            "mutually_exclusive_groups": [sorted(g) for g in pol.mutually_exclusive],
            "supported_combinations": [sorted(g) for g in pol.supported_combinations],
            "note": pol.note,
        }
        for fid, pol in FAMILY_OPERATION_POLICY.items()
    ]


def build_report(payload: dict) -> str:
    s = payload["summary"]
    lines = [
        "# M17-RC1 §D — Semantic Completeness",
        "",
        "**Bất biến:** `status=ok` ⟹ `dropped_requirements` rỗng. Đề hỏi nhiều thao",
        "tác mà family chỉ dựng được một → TỪ CHỐI TRUNG THỰC, không âm thầm chọn một.",
        "",
        "Probe **sinh từ registry chính sách** — thêm family/cơ chế thì probe tự có.",
        "",
        f"- Family có chính sách: **{s['family_count']}/{s['family_count']}**",
        f"- Probe: **{s['probe_count']}** · khớp kỳ vọng **{s['matched']}**"
        f" · lệch **{s['mismatched']}**",
        f"- Chặn đúng (multi-operation): **{s['blocked']}** ·"
        f" chặn oan (single-operation): **{s['false_blocks']}**",
        f"- ok mà còn dropped_requirements: **{s['ok_with_dropped']}** (phải là 0)",
        f"- Kết luận: **{'PASS' if payload['ok'] else 'FAIL'}**",
        "",
        "> **Ranh giới của chính báo cáo này** (đo được ở RC1-C, không phải suy đoán).",
        "> Probe nạp THẲNG id cơ chế vào gate ⇒ chỉ chứng minh *cho trước analyze,",
        "> gate quyết đúng* — KHÔNG chứng minh *analyze nói được điều đó*. Chỉ",
        f"> **{s['families_analyze_expressible']}/{s['family_count']}** family có cơ chế",
        "> nằm trong `analyze_exposed_values()`; family ngoài đó thì gate không bao",
        "> giờ nhận được dữ liệu ở đời thực. Bằng chứng: case `rc1c-scan-max-and-min`",
        "> (single_pass_scan) trả `ok` và bỏ im lặng một nửa yêu cầu.",
        "",
        "## Chính sách theo family",
        "",
        "| Family | Cardinality | max | #cơ chế | analyze nói được? | Ghi chú |",
        "|---|---|---|---|---|---|",
    ]
    for r in payload["policies"]:
        lines.append(
            f"| `{r['family_id']}` | {r['operation_cardinality']} | "
            f"{r['max_operations']} | {r['mechanism_count']} | "
            f"{'có' if r['analyze_expressible'] else '**KHÔNG**'} | {r['note'] or '—'} |"
        )
    lines += ["", "## Probe", "",
              "| Probe | Kỳ vọng | Thực tế | Pha chặn | error_code | dropped |",
              "|---|---|---|---|---|---|"]
    for p in payload["probes"]:
        lines.append(
            f"| `{p['probe_id']}` | {p['expected_decision']} | "
            f"{'✓ ' if p['match'] else '✗ '}{p['actual_decision']} | "
            f"{p['blocking_phase'] or '—'} | `{p['error_code'] or '—'}` | "
            f"{len(p['dropped_requirements'])} |"
        )
    return "\n".join(lines) + "\n"


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--json", default=None)
    p.add_argument("--md", default=None)
    args = p.parse_args()

    probes = build_probes()
    mismatched = [p for p in probes if not p["match"]]
    false_blocks = [
        p for p in probes
        if p["expected_decision"] == PASS and p["actual_decision"] == BLOCKED
    ]
    ok_with_dropped = [
        p for p in probes
        if p["actual_decision"] == PASS and p["dropped_requirements"]
    ]
    ok = not (mismatched or ok_with_dropped)

    payload = {
        "schema_version": "1",
        "run_label": "rc1-semantic-completeness",
        "source_identity": runtime_identity(),
        "invariant": "status=ok ⟹ dropped_requirements == []",
        "summary": {
            "family_count": len(FAMILY_OPERATION_POLICY),
            "families_analyze_expressible": len(analyze_expressible_families()),
            "probe_count": len(probes),
            "matched": len(probes) - len(mismatched),
            "mismatched": len(mismatched),
            "blocked": sum(1 for p in probes if p["actual_decision"] == BLOCKED),
            "false_blocks": len(false_blocks),
            "ok_with_dropped": len(ok_with_dropped),
        },
        "policies": _policy_rows(),
        "probes": probes,
        "violations": {
            "expectation_mismatch": [p["probe_id"] for p in mismatched],
            "false_block": [p["probe_id"] for p in false_blocks],
            "ok_with_dropped_requirements": [p["probe_id"] for p in ok_with_dropped],
        },
        "ok": ok,
    }

    if args.json:
        Path(args.json).parent.mkdir(parents=True, exist_ok=True)
        Path(args.json).write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
                                   encoding="utf-8")
        print(f"Artifact: {args.json}")
    if args.md:
        Path(args.md).parent.mkdir(parents=True, exist_ok=True)
        Path(args.md).write_text(build_report(payload), encoding="utf-8")
        print(f"Report:   {args.md}")

    print(f"Probe: {len(probes)} · lệch {len(mismatched)} · chặn oan "
          f"{len(false_blocks)} · ok-mà-sót {len(ok_with_dropped)} · "
          f"{'PASS' if ok else 'FAIL'}")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
