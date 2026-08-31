# -*- coding: utf-8 -*-
"""FRESH PROBE — 6 đề tươi, đo MA SÁT TỔNG HỢP sau khi dọn thiên lệch prompt.

    đề tiếng Việt → Semantic Program → thẩm định → grounding
                  → thực thi tất định → đối chiếu ORACLE

⚠️ **TIÊU QUOTA THẬT.** `ALLOW_LIVE_AI=1` + `GEMINI_API_KEY`. Trần cứng 12 lượt
(6 đề × [1 tổng hợp + tối đa 1 sửa]). Chạy ĐÚNG MỘT LẦN, không rerun.

─── CÂU HỎI, VÀ NÓ HẸP HƠN CÂU CỦA MATRIX ─────────────────────────────────

Matrix hỏi *"đề mới có cần code mới không"*. Đây hỏi:

    HỢP ĐỒNG RÕ HƠN CÓ LÀM GIẢM MA SÁT TỔNG HỢP KHÔNG?

Nên sáu đề cố ý nằm TRONG năng lực IR: không mặt cong, không quỹ tích, không
Oxyz. Một đề ngoài năng lực sẽ fail-closed đúng và **không nói gì** về câu hỏi.

─── HAI KHÁC BIỆT SO VỚI HARNESS MATRIX, CẢ HAI CÓ CHỦ ĐÍCH ───────────────

**① CỔNG TRUNG THỰC BẬT THẬT.** Matrix gọi `check_grounding(RequestContract(),
spec)` — hợp đồng RỖNG, tức `problem_text` rỗng, tức `la_ten_nguon` trả
"chưa kiểm được" và hai chốt trung thực **không bao giờ nổ**. Ở đây hợp đồng
mang đề bài, nên `HONESTY_FAILURES` là con số đo được chứ không phải một ô
luôn bằng 0.

**② TRẦN 2 LƯỢT/ĐỀ CƯỠNG CHẾ Ở BIÊN GỌI**, không nhờ hằng số của pipeline
(`MAX_SEMANTIC_PROGRAM_ATTEMPTS = 3`). Đếm ở chỗ gửi đi, và **dừng TRƯỚC khi
gửi** — chạm trần thì lượt ấy không tiêu token nào.

─── ĐIỀU BỘ ĐO KHÔNG LÀM ──────────────────────────────────────────────────

Không sửa chương trình mô hình sinh. Không gợi ý. Không chạy lại đề đã hỏng.
Không sửa code giữa các đề. Không đè artifact lượt cũ — đó là tính năng.
"""
from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
import os
import subprocess
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
from app.simulation.semantic_program.grounding_gate import (  # noqa: E402
    ERR_RUA_NANG_LUC,
    ERR_THIEU_NGUOI_DUNG,
    check_grounding,
)
from app.simulation.semantic_program.interpreter import (  # noqa: E402
    SemanticProgramInterpreter,
)
from app.simulation.semantic_program.ir_static_check import kiem_tinh  # noqa: E402
from app.simulation.semantic_program.request_contract import (  # noqa: E402
    RequestContract,
)
from scripts.fresh_probe_cases import CASES, check_contamination  # noqa: E402

TRAN_TOAN_PROBE = 12
TRAN_MOI_DE = 2

_HONESTY = {ERR_RUA_NANG_LUC, ERR_THIEU_NGUOI_DUNG}


def _mong_doi(dap_so):
    """Oracle tính tay → giá trị so được với kernel."""
    loai, v = dap_so
    return Fraction(v) if loai == "rational" else radical(v[0], v[1])


def _bang(a, b) -> bool:
    if a is None or b is None:
        return False
    if isinstance(a, Radical) or isinstance(b, Radical):
        return a == b
    try:
        return Fraction(a) == Fraction(b)
    except (TypeError, ValueError):
        return False


class _Nhat:
    """Ghi từng lượt: sự kiện, chương trình thô, token mỗi lượt."""

    def __init__(self) -> None:
        self.events: list[dict] = []
        self.raws: list[str] = []
        self.tokens_moi_luot: list[int] = []

    def __call__(self, ten: str, **kw) -> None:
        if ten == "semantic_program_attempt":
            self.events.append({"attempt_index": kw.get("n", 0),
                                "ok": kw.get("ok"), "gate": kw.get("gate"),
                                "repairable": kw.get("repairable", True),
                                "error": kw.get("message")})


def _phan_loai(su_kien: list[dict], stage: str, ma_loi: str | None) -> str:
    """Bệnh của lượt hỏng — dùng CÙNG từ vựng với AUDIT để so được.

    Thứ tự hẹp-trước-rộng, cùng lý do như `audit_synthesis_failures.KHUON`.
    """
    if ma_loi in _HONESTY:
        return "HONESTY"
    van = " ".join(str(e.get("error") or "") for e in su_kien)
    if "VECTƠ CÓ HƯỚNG" in van or "sai kiểu" in van and "angle_cos" in van:
        return "PROMPT_BIAS"
    if stage == "SYNTHESIS" and ("schema" in van or "validation error" in van):
        return "SCHEMA"
    if "IR_" in van:
        return "UNSUPPORTED_IR"
    return {"GROUNDING": "GROUNDING", "STATIC": "STATIC_VALIDATION",
            "EXEC": "RUNTIME"}.get(stage, "OTHER")


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

    ghi: dict = {"case_id": case["id"], "hinh_dang": case["hinh_dang"],
                 "do_sau": case["do_sau"], "so_nghia_vu": case["so_nghia_vu"],
                 "nham": case["nham"]}

    PL.call_gemini = dem_call
    try:
        # ⚠️ `DOMAIN_HINH_HOC`, KHÔNG phải chuỗi `"geometry"`.
        #
        # `program_skill_for` so với `"hinh_hoc"`; một chuỗi khác rơi vào nhánh
        # `else` và trả `"semantic_program"` — PROMPT TIN HỌC. Cả
        # `run_generalization_matrix.py` lẫn `probe_dihedral_synthesis.py` đều
        # truyền `"geometry"`, nên hai tuyến đo ấy đo hình học bằng prompt Tin
        # học mà không ai biết. Xem `FRESH_PROBE_REPORT.md §0`.
        #
        # Đây đúng là con bug mà docstring của `stage_semantic_program` đã kể
        # một lần — *"đề hình học được viết chương trình bằng prompt Tin học,
        # và trượt ở chỗ trông như mô hình kém trong khi thật ra ta đưa nhầm
        # đề bài cho nó"* — nay quay lại ở BỘ ĐO thay vì ở sản phẩm.
        spec, loi = await PL.stage_semantic_program(
            case["de"], {}, api_key, domain=DOMAIN_HINH_HOC, observer=nhat)
    except RuntimeError as e:
        loi, spec = str(e), None
    finally:
        PL.call_gemini = goc

    u = (usage_report() or {}).get("semantic_program") or {}
    ghi.update({
        "logical_calls": dem["http"], "attempts": dem["attempted"],
        "one_shot": dem["attempted"] == 1,
        "input_tokens": u.get("prompt_tokens", 0),
        "output_tokens": u.get("candidates_tokens", 0),
        "total_tokens": total_tokens(),
        "tokens_per_attempt": nhat.tokens_moi_luot,
        "latency_s": round(time.monotonic() - bat_dau, 2),
        "attempts_log": nhat.events,
        "programs": nhat.raws,
    })

    if spec is None:
        ma = None
        for e in nhat.events:
            for h in _HONESTY:
                if h in str(e.get("error") or ""):
                    ma = h
        return {**ghi, "class": "FAIL_AFTER_REPAIR", "stage": "SYNTHESIS",
                "error": loi,
                "taxonomy": _phan_loai(nhat.events, "SYNTHESIS", ma),
                "honesty_repair_calls": sum(
                    1 for e in nhat.events if e.get("repairable") is False
                    and e["attempt_index"] < dem["attempted"] - 1)}

    ghi["statements"] = [s.kind for s in spec.statements]
    ghi["angle_measures"] = sorted({
        getattr(st.expr, "quantity", "") for st in spec.statements
        if getattr(getattr(st, "expr", None), "kind", "") == "measure"
    } - {""})

    # ── GROUNDING với ĐỀ BÀI — cổng trung thực bật thật ─────────────────
    hd = RequestContract(problem_text=case["de"])
    g = check_grounding(hd, spec)
    ghi["grounding_pass"] = g.ok
    if not g.ok:
        return {**ghi, "class": "FAIL_AFTER_REPAIR", "stage": "GROUNDING",
                "error": "; ".join(g.unresolved[:4]),
                "error_code": g.error_code,
                "taxonomy": _phan_loai(nhat.events, "GROUNDING", g.error_code)}

    t = kiem_tinh(spec)
    ghi["static_pass"] = t.ok
    if not t.ok:
        return {**ghi, "class": "FAIL_AFTER_REPAIR", "stage": "STATIC",
                "error": t.phan_hoi()[:400],
                "taxonomy": _phan_loai(nhat.events, "STATIC", None)}

    # ── THỰC THI — 0 token từ đây ───────────────────────────────────────
    try:
        kq = SemanticProgramInterpreter().execute(spec)
    except Exception as e:  # noqa: BLE001 — bộ đo phải ghi được MỌI kiểu hỏng
        return {**ghi, "class": "SYSTEM_FAILURE", "stage": "EXEC",
                "error": f"{type(e).__name__}: {e}",
                "taxonomy": "RUNTIME", "system_bug_suspected": True}

    mem = getattr(kq, "memory", {}) or {}
    mong = _mong_doi(case["dap_so"])
    trung = [k for k, v in mem.items() if _bang(v, mong)]
    ghi["oracle"] = str(mong)
    ghi["bien_khop_oracle"] = trung
    dung = bool(trung)
    if "dap_so_phu" in case:
        mong2 = _mong_doi(case["dap_so_phu"])
        trung2 = [k for k, v in mem.items() if _bang(v, mong2)]
        ghi["oracle_phu"] = str(mong2)
        ghi["bien_khop_oracle_phu"] = trung2
        dung = dung and bool(trung2)

    return {**ghi,
            "class": ("ONE_SHOT_CORRECT" if dung and ghi["one_shot"]
                      else "REPAIRED_CORRECT" if dung
                      else "EXECUTABLE_BUT_INCORRECT"),
            "stage": "DONE",
            "taxonomy": None if dung else "WRONG_ANSWER"}


def _niem_phong(ra: Path) -> dict:
    """§13 — niêm phong TRƯỚC khi gọi model.

    Niêm phong sau khi chạy thì nó chỉ mô tả thứ đã xảy ra. Niêm phong trước
    là một lời cam kết: bộ đề, đáp án tính tay và danh tính runtime đã cố định
    trước khi thấy một token nào của mô hình.
    """
    goc = Path(__file__).resolve().parents[1]
    prompt = goc / "app" / "ai" / "skills" / "geometry_program_generator.md"
    from app.main import CACHE_VERSION
    from app.simulation.semantic_program.grammar_card import grammar_card

    the = grammar_card("hinh_hoc")
    dau = {
        "khai": "FRESH PROBE §13 — niêm phong TRƯỚC khi gọi model. Bộ đề, "
                "oracle tính tay và danh tính runtime cố định từ đây.",
        "niem_phong_luc": datetime.now(timezone.utc).isoformat(),
        "commit": subprocess.run(["git", "rev-parse", "HEAD"],
                                 capture_output=True, text=True,
                                 cwd=goc).stdout.strip(),
        "cay_sach": not subprocess.run(
            ["git", "status", "--porcelain"], capture_output=True, text=True,
            cwd=goc).stdout.strip(),
        "cache_version": CACHE_VERSION,
        "prompt_hash": hashlib.sha256(prompt.read_bytes()).hexdigest()[:16],
        "prompt_bytes": len(prompt.read_bytes()),
        "the_van_pham_hash": hashlib.sha256(
            the.encode("utf-8")).hexdigest()[:16],
        "the_van_pham_bytes": len(the.encode("utf-8")),
        "hard_cap": TRAN_TOAN_PROBE,
        "tran_moi_de": TRAN_MOI_DE,
        "so_de": len(CASES),
        "de_hash": hashlib.sha256(
            json.dumps([c["de"] for c in CASES], ensure_ascii=False)
            .encode("utf-8")).hexdigest()[:16],
        "oracle_hash": hashlib.sha256(
            json.dumps([str(c["dap_so"]) for c in CASES], ensure_ascii=False)
            .encode("utf-8")).hexdigest()[:16],
        "nhiem_cheo": check_contamination(),
        "cases": [{"id": c["id"], "hinh_dang": c["hinh_dang"],
                   "do_sau": c["do_sau"], "so_nghia_vu": c["so_nghia_vu"],
                   "nham": c["nham"], "de": c["de"],
                   "kiem_tay": c["kiem_tay"]} for c in CASES],
    }
    (ra / "SEAL.json").write_text(
        json.dumps(dau, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    return dau


async def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--out-dir",
                   default="../docs/evaluation/geometry/fresh-probe")
    p.add_argument("--chi-niem-phong", action="store_true",
                   help="chỉ niêm phong, KHÔNG gọi model (0 call)")
    a = p.parse_args()

    ra = Path(a.out_dir).resolve()
    ra.mkdir(parents=True, exist_ok=True)
    dich = ra / "probe.json"
    if dich.exists():
        print(f"✗ {dich} đã có — bộ đo TỪ CHỐI đè lượt cũ.")
        return 3

    dau = _niem_phong(ra)
    print(f"━━ NIÊM PHONG ━━\n  commit {dau['commit'][:8]} · "
          f"cây sạch {dau['cay_sach']} · CACHE_VERSION {dau['cache_version']}\n"
          f"  prompt {dau['prompt_bytes']}B ({dau['prompt_hash']}) · "
          f"thẻ {dau['the_van_pham_bytes']}B ({dau['the_van_pham_hash']})\n"
          f"  {dau['so_de']} đề ({dau['de_hash']}) · trần {dau['hard_cap']}")
    if dau["nhiem_cheo"]:
        print("✗ NHIỄM CHÉO với pool holdout — dừng, KHÔNG tiêu call:")
        for x in dau["nhiem_cheo"]:
            print(f"    {x}")
        return 4
    print("  nhiễm chéo: SẠCH")
    if a.chi_niem_phong:
        print(f"\n→ {ra / 'SEAL.json'} (chỉ niêm phong, 0 call)")
        return 0

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

    ket, da_dung = [], 0
    for c in CASES:
        con_lai = TRAN_TOAN_PROBE - da_dung
        if con_lai <= 0:
            print(f"\n━━ {c['id']} — DỪNG: chạm trần {TRAN_TOAN_PROBE}")
            ket.append({"case_id": c["id"], "class": "NOT_RUN",
                        "error": "chạm trần toàn probe"})
            continue
        print(f"\n━━ {c['id']} ({c['hinh_dang']}) ━━")
        r = await _mot_de(c, key, con_lai)
        da_dung += r.get("logical_calls", 0)
        ket.append(r)
        print(f"  {r.get('class')} · gọi {r.get('logical_calls')} · "
              f"token {r.get('total_tokens')} · {r.get('taxonomy') or ''}")
        if r.get("error"):
            print(f"    {' '.join(str(r['error']).split())[:160]}")

    def dem(*lop) -> int:
        return sum(1 for r in ket if r.get("class") in lop)

    def bo(khoa) -> int:
        return sum(r.get(khoa, 0) or 0 for r in ket)

    dung = dem("ONE_SHOT_CORRECT", "REPAIRED_CORRECT")
    mot_lan = dem("ONE_SHOT_CORRECT")
    tax = [r.get("taxonomy") for r in ket]
    goi = bo("logical_calls")
    tong_tok = bo("total_tokens")
    tok_sua = sum(sum(r.get("tokens_per_attempt", [])[1:]) for r in ket)

    bao = {
        "khai": "FRESH PROBE — 6 đề tươi, đo ma sát tổng hợp sau khi dọn "
                "thiên lệch prompt. Chạy MỘT lần, không rerun.",
        "chayLuc": datetime.now(timezone.utc).isoformat(),
        "seal": {k: dau[k] for k in
                 ("commit", "cache_version", "prompt_hash", "prompt_bytes",
                  "the_van_pham_hash", "the_van_pham_bytes", "de_hash",
                  "oracle_hash", "hard_cap")},
        "hard_cap": TRAN_TOAN_PROBE, "logical_calls_used": goi,
        "one_shot_correct": mot_lan,
        "repaired_correct": dem("REPAIRED_CORRECT"),
        "correct_within_budget": dung,
        "executable_but_incorrect": dem("EXECUTABLE_BUT_INCORRECT"),
        "fail_after_repair": dem("FAIL_AFTER_REPAIR"),
        "system_failure": dem("SYSTEM_FAILURE"),
        "schema_failures": tax.count("SCHEMA"),
        "prompt_bias_failures": tax.count("PROMPT_BIAS"),
        "honesty_failures": tax.count("HONESTY"),
        "unsupported_ir_failures": tax.count("UNSUPPORTED_IR"),
        "honesty_repair_calls": bo("honesty_repair_calls"),
        "total_input_tokens": bo("input_tokens"),
        "total_output_tokens": bo("output_tokens"),
        "total_tokens": tong_tok,
        "repair_token_share": (round(tok_sua / tong_tok, 3)
                               if tong_tok else None),
        "tokens_per_correct_executable_ir": (round(tong_tok / dung)
                                             if dung else None),
        "tokens_per_one_shot_correct_ir": (round(tong_tok / mot_lan)
                                           if mot_lan else None),
        "average_calls_per_success": (round(goi / dung, 2) if dung else None),
        "cases": ket,
    }
    dich.write_text(json.dumps(bao, ensure_ascii=False, indent=1) + "\n",
                    encoding="utf-8")

    print(f"\n━━ KẾT QUẢ ━━")
    print(f"  one-shot đúng      {mot_lan}/{len(CASES)}")
    print(f"  đúng trong ngân sách {dung}/{len(CASES)}")
    print(f"  hỏng sau sửa       {dem('FAIL_AFTER_REPAIR')}/{len(CASES)}")
    print(f"  lỗi hệ             {dem('SYSTEM_FAILURE')}/{len(CASES)}")
    print(f"  schema {tax.count('SCHEMA')} · thiên lệch "
          f"{tax.count('PROMPT_BIAS')} · trung thực {tax.count('HONESTY')} · "
          f"ngoài IR {tax.count('UNSUPPORTED_IR')}")
    print(f"  gọi {goi}/{TRAN_TOAN_PROBE} · token {tong_tok} · "
          f"sửa chiếm {bao['repair_token_share']}")
    print(f"\n→ {dich}")
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
