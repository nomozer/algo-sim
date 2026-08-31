# -*- coding: utf-8 -*-
"""GENERALIZATION MATRIX — 10 đề chưa từng thấy, RUNTIME ĐÓNG BĂNG.

    đề tiếng Việt → Semantic Program → thẩm định → grounding
                  → thực thi tất định → đối chiếu ORACLE → Scene3D

⚠️ **TIÊU QUOTA THẬT.** `ALLOW_LIVE_AI=1` + `GEMINI_API_KEY`. Trần cứng 20 lượt.

─── CÂU HỎI ───────────────────────────────────────────────────────────────

    NEW PROBLEM REQUIRED NEW CODE = ?

Không phải *"mô hình giỏi không"*. Runtime, prompt, schema đóng băng suốt cả
matrix; nếu một đề chạy được thì nó chạy được bằng **đúng bộ từ vựng** mà chín
đề kia dùng, không có nhánh nào riêng cho nó.

─── VÌ SAO ĐỐI CHIẾU ORACLE TÍNH TAY, KHÔNG PHẢI CỔNG CHẤM ────────────────

`GEOMETRY_CHECKERS` tính lại đại lượng **từ cùng một kernel** đã tính ra nó —
dùng nó làm thước ở đây là hỏi engine tự chấm mình. Oracle ở
`generalization_matrix_cases.dap_so` tính TAY từ một hệ trục ghi sẵn, nên nó là
nguồn ĐỘC LẬP. Mô hình tự chọn hệ trục của nó, và đó là lý do mọi đề ghim thang
bằng số cụ thể: đáp số tuyệt đối mới so được.

─── ĐIỀU BỘ ĐO KHÔNG LÀM ──────────────────────────────────────────────────

Không sửa chương trình mô hình sinh ra. Không gợi ý. Không chạy lại đề đã hỏng.
Không sửa code giữa các đề — đó là bất biến quan trọng nhất của matrix (§12).
"""
from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
import os
import sys
import time
from datetime import datetime, timezone
from fractions import Fraction
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.ai import pipeline as PL  # noqa: E402
from app.ai.telemetry import reset_usage, total_tokens, usage_report  # noqa: E402
from app.simulation.geometry.radical import Radical, radical  # noqa: E402
from app.simulation.semantic_program.domain_profile import (  # noqa: E402
    DOMAIN_HINH_HOC,
)
from app.simulation.semantic_program.grounding_gate import check_grounding  # noqa: E402
from app.simulation.semantic_program.interpreter import (  # noqa: E402
    SemanticProgramInterpreter,
)
from app.simulation.semantic_program.ir_static_check import kiem_tinh  # noqa: E402
from app.simulation.semantic_program.request_contract import RequestContract  # noqa: E402
from app.simulation.semantic_program.scene3d import build_scene3d  # noqa: E402
from app.simulation.semantic_program.simulation_state import (  # noqa: E402
    build_simulation_state,
)
from scripts.generalization_matrix_cases import CASES  # noqa: E402

#: Trần CỨNG toàn matrix (§2). Chạm trần là dừng, không phải chạy chậm lại.
TRAN_TOAN_MATRIX = 20
#: Mỗi đề: 1 tổng hợp + tối đa 1 sửa.
TRAN_MOI_DE = 2


def _mong_doi(dap_so):
    """`dap_so` → giá trị `ExactNumber` để so BẰNG ĐÚNG."""
    if dap_so is None:
        return None
    loai, gt = dap_so
    return Fraction(gt) if loai == "rational" else radical(gt[0], gt[1])


class _Nhat:
    """Nhặt sự kiện từng lượt + chương trình thô. Quan sát THỤ ĐỘNG."""

    def __init__(self) -> None:
        self.events: list[dict] = []
        self.raws: list[str] = []
        self.tokens_moi_luot: list[int] = []

    def emit(self, event_type: str, data: dict) -> None:
        if event_type == "semantic_program_attempt":
            self.events.append({
                "attempt_index": data.get("n"), "ok": data.get("ok"),
                "gate": data.get("gate") or "schema",
                "error_message": (data.get("message") or "")[:600],
            })


def _phan_loai(gate: str | None, stage: str) -> str:
    """Taxonomy §10. Một failure chỉ được gọi SYNTHESIS khi chương trình THẬT SỰ
    sai — hệ chặn nhầm một chương trình hợp lệ là SYSTEM, không phải model."""
    if stage in ("RUNTIME", "SCENE"):
        return "RUNTIME"
    if stage == "ORACLE":
        return "CHECKER"
    if stage == "GROUNDING":
        return "GROUNDING"
    return {"ir_static": "STATIC_VALIDATION", "grounding": "GROUNDING",
            "schema": "SCHEMA"}.get(gate or "", "SYNTHESIS")


def _do_goc_nao(spec) -> list[str]:
    """§7 — mô hình chọn phép đo góc nào? Đọc từ chương trình, không đoán."""
    ra = []
    for st in spec.statements:
        e = getattr(st, "expr", None)
        if getattr(e, "kind", None) == "measure":
            q = getattr(e, "quantity", None)
            if q in ("angle_cos", "angle_cos_sq"):
                ra.append(q)
    return ra


def _so_do_cuoi(mem: dict):
    """Đại lượng đo được cuối cùng trong bộ nhớ — thứ đề hỏi.

    Lấy giá trị SỐ (không phải đối tượng hình học). Nhiều đại lượng thì trả hết
    và để phép so tìm cái khớp: mô hình có thể đo thêm bước trung gian, và phạt
    nó vì đo dư là chấm theo cách viết chứ không theo kết quả.
    """
    return {k: v for k, v in mem.items()
            if isinstance(v, (Fraction, Radical)) and not isinstance(v, bool)}


async def _mot_de(case: dict, api_key: str, con_lai: int) -> dict:
    reset_usage()
    dem = {"http": 0, "attempted": 0}
    nhat = _Nhat()
    bat_dau = time.monotonic()
    goc = PL.call_gemini

    async def dem_call(*a, **kw):
        dem["attempted"] += 1
        if dem["attempted"] > TRAN_MOI_DE or dem["http"] >= con_lai:
            raise RuntimeError("chạm trần — dừng TRƯỚC khi gửi, không tiêu token")
        dem["http"] += 1
        truoc = total_tokens()
        kq = await goc(*a, **kw)
        nhat.raws.append(kq if isinstance(kq, str) else repr(kq))
        nhat.tokens_moi_luot.append(total_tokens() - truoc)
        return kq

    ghi: dict = {"case_id": case["id"], "topology": case["topology"],
                 "do_sau": case["do_sau"], "so_nghia_vu": case["so_nghia_vu"],
                 "nang_luc": case["nang_luc"],
                 "ngoai_pham_vi": bool(case.get("ngoai_pham_vi"))}

    PL.call_gemini = dem_call
    try:
        # ⚠️ SỬA 2026-08-31 — KHÔNG hồi tố `matrix.json`.
        #
        # Dòng này từng truyền chuỗi `"geometry"`. `program_skill_for` so với
        # `"hinh_hoc"`, nên chuỗi ấy rơi vào nhánh `else` và trả
        # `"semantic_program"` — PROMPT TIN HỌC. Cả matrix đo hình học bằng
        # hợp đồng của môn khác, im lặng, không lỗi nào.
        #
        # `matrix.json` sinh RA TRƯỚC bản sửa này và **giữ nguyên** (điểm đóng
        # băng). Xem `generalization-matrix/ERRATUM.md`. Sửa ở đây để lượt SAU
        # đo đúng thứ nó tưởng đang đo, không để đổi lượt trước.
        spec, loi = await PL.stage_semantic_program(
            case["de"], {}, api_key, domain=DOMAIN_HINH_HOC, observer=nhat)
    except RuntimeError as e:
        loi, spec = str(e), None
    finally:
        PL.call_gemini = goc

    u = (usage_report() or {}).get("semantic_program") or {}
    ghi.update({
        "logical_calls": dem["http"], "attempts": dem["attempted"],
        "input_tokens": u.get("prompt_tokens", 0),
        "output_tokens": u.get("candidates_tokens", 0),
        "total_tokens": total_tokens(),
        "tokens_per_attempt": nhat.tokens_moi_luot,
        "latency_s": round(time.monotonic() - bat_dau, 2),
        "attempts_log": nhat.events,
        "programs": nhat.raws,
    })

    if spec is None:
        cuoi = nhat.events[-1]["gate"] if nhat.events else None
        return {**ghi, "class": "FAIL_AFTER_REPAIR", "stage": "SYNTHESIS",
                "error": loi, "taxonomy": _phan_loai(cuoi, "SYNTHESIS"),
                "system_bug_suspected": False}

    ghi["program_hash"] = hashlib.sha256(
        json.dumps(spec.model_dump(), ensure_ascii=False, sort_keys=True)
        .encode("utf-8")).hexdigest()[:16]
    ghi["statements"] = [s.kind for s in spec.statements]
    ghi["angle_measures"] = _do_goc_nao(spec)

    # ── GROUNDING — cùng cổng sản phẩm, không nới ───────────────────────
    g = check_grounding(RequestContract(), spec)
    ghi["grounding_pass"] = g.ok
    if not g.ok:
        return {**ghi, "class": "FAIL_AFTER_REPAIR", "stage": "GROUNDING",
                "error": "; ".join(g.unresolved[:4]),
                "taxonomy": "GROUNDING", "system_bug_suspected": False}

    t = kiem_tinh(spec)
    ghi["static_pass"] = t.ok
    if not t.ok:
        return {**ghi, "class": "FAIL_AFTER_REPAIR", "stage": "STATIC",
                "error": t.phan_hoi()[:400], "taxonomy": "STATIC_VALIDATION",
                "system_bug_suspected": False}

    # ── THỰC THI — 0 token từ đây ───────────────────────────────────────
    try:
        kq = SemanticProgramInterpreter().execute(spec)
    except Exception as e:  # noqa: BLE001
        return {**ghi, "class": "FAIL_AFTER_REPAIR", "stage": "RUNTIME",
                "runtime_reached": False,
                "error": f"{type(e).__name__}: {e}"[:400],
                "taxonomy": "RUNTIME", "system_bug_suspected": False}
    ghi["runtime_reached"] = True
    so_do = _so_do_cuoi(kq.final_memory)
    ghi["measured"] = {k: str(v) for k, v in so_do.items()}

    # ── ĐỐI CHIẾU ORACLE ────────────────────────────────────────────────
    mong = _mong_doi(case.get("dap_so"))
    if mong is None:
        # Đề NGOÀI năng lực mà lại chạy trót lọt ⇒ hệ đã dựng một thứ nó không
        # có quyền dựng. Đó là thất bại nặng nhất, không phải thành công.
        return {**ghi, "class": "EXECUTABLE_BUT_INCORRECT", "stage": "ORACLE",
                "error": "đề ngoài năng lực nhưng chương trình vẫn chạy",
                "taxonomy": "CHECKER", "system_bug_suspected": False}

    khop = [k for k, v in so_do.items() if v == mong]
    ghi["oracle_expected"] = str(mong)
    ghi["oracle_matched_var"] = khop[0] if khop else None
    if not khop:
        return {**ghi, "class": "EXECUTABLE_BUT_INCORRECT", "stage": "ORACLE",
                "error": f"không đại lượng nào bằng {mong}",
                "taxonomy": "CHECKER", "system_bug_suspected": False}

    # ── SCENE3D (§18) ───────────────────────────────────────────────────
    try:
        state = build_simulation_state(spec, kq)
        canh = build_scene3d(state)
        json.dumps(canh, ensure_ascii=False)
        ghi["scene3d_created"] = True
        ghi["scene_objects"] = len(canh.get("objects", []))
        ghi["trace_steps"] = len(state.get("timeline", []) or [])
    except Exception as e:  # noqa: BLE001
        return {**ghi, "class": "SYSTEM_FAILURE", "stage": "SCENE",
                "error": f"{type(e).__name__}: {e}"[:300],
                "taxonomy": "RUNTIME", "system_bug_suspected": True}

    ghi["class"] = ("ONE_SHOT_CORRECT" if dem["http"] == 1
                    else "REPAIRED_CORRECT")
    ghi["stage"] = "DONE"
    ghi["taxonomy"] = None
    ghi["system_bug_suspected"] = False
    return ghi


async def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--out-dir",
                   default="../docs/evaluation/geometry/generalization-matrix")
    a = p.parse_args()

    if os.getenv("ALLOW_LIVE_AI") != "1":
        print("✗ Cần ALLOW_LIVE_AI=1 — TIÊU QUOTA THẬT.")
        return 2
    try:
        from dotenv import load_dotenv

        load_dotenv(Path(__file__).resolve().parents[1] / ".env")
    except ImportError:
        pass
    key = os.getenv("GEMINI_API_KEY")
    if not key:
        print("✗ Thiếu GEMINI_API_KEY.")
        return 2

    ra = Path(a.out_dir).resolve()
    ra.mkdir(parents=True, exist_ok=True)
    dich = ra / "matrix.json"
    if dich.exists():
        print(f"✗ {dich} đã có — bộ đo TỪ CHỐI đè lượt cũ.")
        return 3

    import subprocess

    commit = subprocess.run(["git", "rev-parse", "--short", "HEAD"],
                            capture_output=True, text=True).stdout.strip()
    prompt_hash = hashlib.sha256(
        (Path(__file__).resolve().parents[1] / "app" / "ai" / "skills"
         / "geometry_program_generator.md").read_bytes()).hexdigest()[:16]
    from app.main import CACHE_VERSION

    ket, da_dung = [], 0
    for c in CASES:
        con_lai = TRAN_TOAN_MATRIX - da_dung
        if con_lai <= 0:
            print(f"\n━━ {c['id']} — DỪNG: chạm trần {TRAN_TOAN_MATRIX} lượt")
            ket.append({"case_id": c["id"], "class": "NOT_RUN",
                        "error": "chạm trần toàn matrix"})
            continue
        print(f"\n━━ {c['id']} ({c['topology']}) ━━")
        r = await _mot_de(c, key, con_lai)
        da_dung += r.get("logical_calls", 0)
        ket.append(r)
        print(f"  {r.get('class')} · gọi {r.get('logical_calls')} · "
              f"token {r.get('total_tokens')} · {r.get('taxonomy') or ''}")
        if r.get("error"):
            print(f"    {' '.join(str(r['error']).split())[:150]}")

    trong = [r for r in ket if not r.get("ngoai_pham_vi")
             and r.get("class") != "NOT_RUN"]
    dem = lambda k: sum(1 for r in trong if r.get("class") == k)  # noqa: E731
    ngoai = next((r for r in ket if r.get("ngoai_pham_vi")), None)
    dung = dem("ONE_SHOT_CORRECT") + dem("REPAIRED_CORRECT")

    bao = {
        "khai": "GENERALIZATION MATRIX — 10 đề chưa từng thấy, runtime đóng "
                "băng, không sửa code giữa các đề.",
        "chayLuc": datetime.now(timezone.utc).isoformat(),
        "frozen_commit": commit, "prompt_hash": prompt_hash,
        "cache_version": CACHE_VERSION,
        "hard_cap": TRAN_TOAN_MATRIX, "logical_calls_used": da_dung,
        "in_scope": len(trong),
        "one_shot_correct": dem("ONE_SHOT_CORRECT"),
        "repaired_correct": dem("REPAIRED_CORRECT"),
        "correct_within_budget": dung,
        "executable_but_incorrect": dem("EXECUTABLE_BUT_INCORRECT"),
        "fail_after_repair": dem("FAIL_AFTER_REPAIR"),
        "system_failure": dem("SYSTEM_FAILURE"),
        "out_of_scope_fail_closed": (
            ngoai is not None
            and ngoai.get("class") in ("FAIL_AFTER_REPAIR", "NOT_RUN")),
        "angle_cos_selected": sum(
            1 for r in ket if "angle_cos" in (r.get("angle_measures") or [])),
        "angle_cos_sq_selected": sum(
            1 for r in ket if "angle_cos_sq" in (r.get("angle_measures") or [])),
        "input_tokens": sum(r.get("input_tokens", 0) for r in ket),
        "output_tokens": sum(r.get("output_tokens", 0) for r in ket),
        "total_tokens": sum(r.get("total_tokens", 0) for r in ket),
        "tokens_per_correct_executable_ir": (
            round(sum(r.get("total_tokens", 0) for r in ket) / dung)
            if dung else None),
        "taxonomy": {r["case_id"]: r.get("taxonomy")
                     for r in ket if r.get("taxonomy")},
        "cases": ket,
    }
    dich.write_text(json.dumps(bao, ensure_ascii=False, indent=1) + "\n",
                    encoding="utf-8")
    print(f"\n→ {dich}")
    print(f"đúng trong ngân sách {dung}/{len(trong)} · one-shot "
          f"{bao['one_shot_correct']} · sửa {bao['repaired_correct']} · "
          f"gọi {da_dung}/{TRAN_TOAN_MATRIX} · token {bao['total_tokens']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
