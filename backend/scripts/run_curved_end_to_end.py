# -*- coding: utf-8 -*-
"""Xác nhận END-TO-END trên bài hình CONG — `CURVED_END_TO_END_FRESH_CONFIRMATION`.

**TIÊU QUOTA THẬT.** `ALLOW_LIVE_AI=1` + `GEMINI_API_KEY` trong `backend/.env`.

    MEASUREMENT_CLASS = DEVELOPMENT_CURVED_END_TO_END_CONFIRMATION
    HELD_OUT_CLAIM    = NO

─── KHÁC MỌI RUNNER A/B TRƯỚC Ở HAI ĐIỀU ──────────────────────────────────

Runner A/B dựng hợp đồng CỐ ĐỊNH và tắt vòng sửa, để hỏi đúng một câu hẹp.
Runner này làm ngược lại — nó gọi thẳng **`pipeline.run_pipeline`**, tức đúng
điểm vào của sản phẩm:

    analyze (LLM) → RequestContract → tổng hợp (LLM) → vòng sửa ≤3
      → ir_static · grounding · phủ · bất biến nguồn · runtime · hậu điều kiện
      → trace → Scene3D → envelope

Nên nó trả lời được câu mà bốn lượt của wave trước **cố ý** không hỏi: *đường
sản phẩm ĐẦY ĐỦ có phục vụ được bài này không.* Đổi lại, nó **không tách** được
đóng góp của từng tầng — đó là cái giá, và nó được khai ở đây chứ không giấu.

⚠️ Gọi thẳng `run_pipeline`, **không qua HTTP** — cùng lý do
`run_phase7a_pilot` và `measure_geometry_stability` làm vậy: không có cache nào
để một kết quả cũ lẻn về.

⚠️ Thẻ dùng cho lượt này là **thẻ SẢN PHẨM hiện hành**, không nạp từ file.
Runner khẳng định nó trùng byte với `card_C.txt` trước khi tiêu lượt gọi đầu —
nếu sản phẩm đã trôi khỏi Card C thì phép đo này không nói về Card C nữa.
"""
from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

BACKEND = Path(__file__).resolve().parents[1]
for _p in (str(BACKEND), str(BACKEND / "scripts")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from wave_counters import TU_API, BoDemWave  # noqa: E402

#: Gold module MẶC ĐỊNH. Một wave sau chạy đề khác thì **không** được sửa module
#: này: `PROBLEM_HASH`/`ORACLE_HASH`/`GOLD_HASH` của nó đã nằm trong artifact
#: BẤT BIẾN của lượt chạy trước, và đổi chúng là phá danh tính lượt đo ấy.
#: Đăng ký của wave mới khai `gold_module`, runner nạp theo.
GOLD_MAC_DINH = "gold_curved_end_to_end"


def _nap_gold(ten: str):
    """Nạp module đề+oracle+gold theo tên, kiểm đủ mặt trước khi dùng."""
    import importlib

    m = importlib.import_module(ten)
    thieu = [k for k in ("CASE_ID", "CONTAINER", "CONTRACT_GOLD_HASH",
                         "GOLD_HASH", "ORACLE", "ORACLE_HASH", "PROBLEM_HASH",
                         "PROBLEM_TEXT", "RA", "WITNESS")
             if not hasattr(m, k)]
    if thieu:
        raise RuntimeError(f"module gold {ten!r} thiếu: {', '.join(thieu)}")
    return m


from app.ai import gemini as G  # noqa: E402
from app.ai import pipeline as PL  # noqa: E402
from app.ai.gemini import ApiBudget  # noqa: E402

NR = "NOT_REACHED"


def _h(t: str) -> str:
    return hashlib.sha256(t.encode("utf-8")).hexdigest()


def _bam(o) -> str:
    return hashlib.sha256(
        json.dumps(o, ensure_ascii=False, sort_keys=True).encode("utf-8")
    ).hexdigest()


class Quan:
    """Observer THỤ ĐỘNG — giữ mọi sự kiện, không đổi một bit hành vi."""

    def __init__(self) -> None:
        self.su_kien: list[dict] = []

    def emit(self, loai: str, data: dict) -> None:
        self.su_kien.append({"loai": loai, **{
            k: (v if isinstance(v, (int, float, bool, type(None)))
                else str(v)[:20000]) for k, v in data.items()}})

    def loc(self, loai: str) -> list[dict]:
        return [e for e in self.su_kien if e["loai"] == loai]


# ══ CHẤM ═════════════════════════════════════════════════════════════════
def _lenh_sinh(spec: dict, ten: str) -> dict | None:
    for st in spec.get("statements", []):
        if st.get("target_var") == ten:
            return st
    return None


#: Nội dung fact CHỈ đọc được từ raw của tầng `semantic_analyze`. Mọi nguồn
#: khác chỉ mang **số đếm** và danh sách nghĩa vụ.
NGUON_DU_CHAM_FACT = ("RAW_ANALYZE",)
NOT_CAPTURED = "NOT_CAPTURED"


def cham_analyze(ct: dict | None, nguon: str = "KHONG_CO",
                 so_fact_quan_sat: int | None = None) -> dict[str, Any]:
    """Hợp đồng do MÔ HÌNH trích — chấm theo dữ kiện đề, không theo tên biến.

    ⚠️ **Không quan sát được ≠ sai.** Nếu nguồn hợp đồng không mang nội dung
    fact thì mọi chiều về fact ghi `NOT_CAPTURED`, và kết luận chung cũng vậy.
    Bản đầu của bộ chấm này trả `FAIL` trong đúng tình huống ấy — chấm trượt
    một tầng nó chưa từng nhìn thấy, cùng họ với lỗi `NOT_REACHED` mà
    `PROVENANCE_AFFORDANCE_AB_4_LUOT §6` đã đính chính một lần.
    """
    if not ct:
        return {"ANALYZE_CONTRACT_CORRECT": NOT_CAPTURED,
                "NGUON_HOP_DONG": nguon, "ly_do": "không có hợp đồng"}
    obs = ct.get("obligations") or []
    ob_radius = [o for o in obs if o.get("kind") == "radius"]
    ra: dict[str, Any] = {
        "NGUON_HOP_DONG": nguon,
        "SO_FACT": len(ct.get("input_facts") or []) or so_fact_quan_sat,
        "CO_NGHIA_VU_RADIUS": bool(ob_radius),
        "OBLIGATION_KINDS": sorted({o.get("kind") for o in obs}),
        "CONTAINER_KHAI": [o.get("container") for o in ob_radius],
        "WITNESS_KHAI": [o.get("witness") or (o.get("params") or {}).get("witness")
                         for o in ob_radius],
    }
    # ── Chiều NGHĨA VỤ: đọc được từ mọi nguồn ──────────────────────────
    ra["ANALYZE_OBLIGATION_CORRECT"] = (
        "PASS" if (ob_radius and any(str(o.get("container", "")).strip("() ")
                                     .lower() == "c" for o in ob_radius))
        else "FAIL")
    # ── Chiều FACT: chỉ đọc được từ raw analyze ────────────────────────
    if nguon not in NGUON_DU_CHAM_FACT:
        for k in ("CO_BAN_KINH_12", "CO_CHIEU_CAO_18", "CO_QUAN_HE_T",
                  "ANALYZE_FACTS_CORRECT", "ANALYZE_CONTRACT_CORRECT"):
            ra[k] = NOT_CAPTURED
        return ra
    tho = json.dumps(ct.get("input_facts") or [], ensure_ascii=False)
    ra["CO_BAN_KINH_12"] = "12" in tho
    ra["CO_CHIEU_CAO_18"] = "18" in tho
    ra["CO_QUAN_HE_T"] = ("1:2" in tho or "1 : 2" in tho)
    ra["ANALYZE_FACTS_CORRECT"] = "PASS" if all(
        (ra["CO_BAN_KINH_12"], ra["CO_CHIEU_CAO_18"],
         ra["CO_QUAN_HE_T"])) else "FAIL"
    ra["ANALYZE_CONTRACT_CORRECT"] = (
        "PASS" if (ra["ANALYZE_FACTS_CORRECT"] == "PASS"
                   and ra["ANALYZE_OBLIGATION_CORRECT"] == "PASS") else "FAIL")
    return ra


def cham_synthesis(spec: dict | None) -> dict[str, Any]:
    if not spec:
        return {"SYNTHESIS_SCORED": False}
    khai = {m.get("name"): m for m in (spec.get("memory_declarations") or [])}
    non = next((s for s in spec.get("statements") or []
                if s.get("kind") == "construct_curved_solid"), None)
    # Điểm chia đoạn: tìm câu lệnh dùng `divide_segment`.
    chia = next((s for s in spec.get("statements") or []
                 if ((s.get("expr") or {}).get("kind") == "divide_segment")), None)
    ex_chia = (chia or {}).get("expr") or {}
    giao = next((s for s in spec.get("statements") or []
                 if ((s.get("expr") or {}).get("kind")
                     == "intersect_plane_curved")), None)
    ten_giao = (giao or {}).get("target_var")
    do = next((s for s in spec.get("statements") or []
               if ((s.get("expr") or {}).get("kind") == "measure")
               and (s.get("expr") or {}).get("quantity") == "radius"), None)

    def _xuat_xu(ten):
        d = khai.get(ten) or {}
        if d.get("model_assumption"):
            return "ma"
        if d.get("source_fact_id"):
            return "sfid"
        return "THIEU"

    goc = [t for t, d in khai.items()
           if d.get("type") == "point3" and d.get("initial_value")]
    return {
        "SYNTHESIS_SCORED": True,
        "CURVED_CONSTRUCTION_OPERATOR": (non or {}).get("kind"),
        "CURVED_KIND": (non or {}).get("curved_kind"),
        "CURVED_KHAI_BANG": ("radius" if (non or {}).get("radius")
                             else ("rim_point" if (non or {}).get("rim_point")
                                   else None)),
        "SECTION_OPERATOR": (giao or {}).get("expr", {}).get("kind"),
        "SECTION_TARGET_TYPE": (khai.get(ten_giao) or {}).get("type"),
        "RATIO_WRITTEN": ex_chia.get("ratio"),
        "RATIO_OPERAND_ORDER": (f"{ex_chia.get('a')}->{ex_chia.get('b')}"
                                if ex_chia else None),
        "DIEM_CHIA_DO_LENH_TAO": bool(chia),
        "DIEM_CHIA_TEN": (chia or {}).get("target_var"),
        "MEASURE_OF": ((do or {}).get("expr") or {}).get("of"),
        "MEASURE_DUNG_CHU_THE": (
            ((do or {}).get("expr") or {}).get("of") == ten_giao
            if (do and ten_giao) else False),
        "DIEM_DAU_VAO_CO_XUAT_XU": {t: _xuat_xu(t) for t in goc},
        "PROVENANCE_DU": all(_xuat_xu(t) != "THIEU" for t in goc) if goc else False,
    }


#: Hai bộ chấm MẶC ĐỊNH ở trên hỏi những chiều của bài NÓN (`radius` của một
#: đường tròn, `ratio` của điểm chia). Một wave có hình khác thì khai
#: `scorer_module` trong đăng ký; module ấy xuất `cham_analyze` và/hoặc
#: `cham_synthesis` với cùng chữ ký, và thiếu cái nào thì rơi về bản ở đây.
def _nap_scorer(ten: str | None):
    if not ten:
        return cham_analyze, cham_synthesis
    import importlib

    m = importlib.import_module(ten)
    return (getattr(m, "cham_analyze", cham_analyze),
            getattr(m, "cham_synthesis", cham_synthesis))


def cham_ket_qua(outcome_evt: dict | None, env: dict | None,
                 dap_so_mong: str | None = None) -> dict[str, Any]:
    if not outcome_evt:
        return {k: NR for k in ("GROUNDING", "SOURCE_INVARIANTS", "RUNTIME",
                                "POSTCONDITIONS", "EXACT_ANSWER", "SCENE3D")}
    stage = outcome_evt.get("stage_reached")
    srv = bool(outcome_evt.get("servable"))
    fm = outcome_evt.get("final_memory")
    return {
        "STAGE": stage,
        "SERVABLE": srv,
        "ERROR_CODE": outcome_evt.get("error_code"),
        "DETAILS": outcome_evt.get("details"),
        "FINAL_MEMORY": fm,
        "EXACT_ANSWER_EXPECTED": dap_so_mong,
        "ENVELOPE_STATUS": (env or {}).get("status"),
    }


async def main_async(args) -> int:
    if os.environ.get("ALLOW_LIVE_AI") != "1":
        print("ALLOW_LIVE_AI != 1 — từ chối tiêu quota.")
        return 2
    api_key = os.environ.get("GEMINI_API_KEY")
    print(f"GEMINI_API_KEY: {'PRESENT' if api_key else 'ABSENT'}")
    if not api_key:
        return 2

    # ⚠️ `--ra` BẮT BUỘC khi chạy gold module khác mặc định: thư mục artifact
    # là nơi đọc `registration.json`, mà chính đăng ký ấy mới nói gold nào.
    ra_dir = (Path(args.ra).resolve() if getattr(args, "ra", None)
              else _nap_gold(GOLD_MAC_DINH).RA)
    ra_dir.mkdir(parents=True, exist_ok=True)
    dang_ky = json.loads((ra_dir / "registration.json").read_text(
        encoding="utf-8"))
    GM = _nap_gold(getattr(args, "gold", None)
                   or dang_ky.get("gold_module") or GOLD_MAC_DINH)
    cham_an, cham_synth = _nap_scorer(dang_ky.get("scorer_module"))
    (CASE_ID, CONTAINER, CONTRACT_GOLD_HASH, GOLD_HASH, ORACLE, ORACLE_HASH,
     PROBLEM_HASH, PROBLEM_TEXT, WITNESS) = (
        GM.CASE_ID, GM.CONTAINER, GM.CONTRACT_GOLD_HASH, GM.GOLD_HASH,
        GM.ORACLE, GM.ORACLE_HASH, GM.PROBLEM_HASH, GM.PROBLEM_TEXT,
        GM.WITNESS)

    # ─── THẺ SẢN PHẨM PHẢI CÒN LÀ CARD C ─────────────────────────────────
    from app.simulation.semantic_program.grammar_card import grammar_card
    the = grammar_card("hinh_hoc")
    card_hash = _h(the)
    mong = dang_ky["danh_tinh_he_duoc_do"]["card_C_sha256"]
    if card_hash != mong:
        print(f"THẺ SẢN PHẨM ĐÃ TRÔI khỏi Card C.\n  đăng ký: {mong}\n"
              f"  hiện tại: {card_hash}")
        return 2

    from app.ai.telemetry import reset_usage, total_tokens, usage_report
    reset_usage()

    ngan_sach = ApiBudget(
        max_logical_calls=dang_ky["ngan_sach"]["logical_application_call_limit"])
    G.set_budget(ngan_sach)
    bo_dem = BoDemWave(ngan_sach)
    goc_call = G.call_gemini

    # ─── GIỮ RAW CỦA TỪNG TẦNG, KỂ CẢ `analyze` ──────────────────────────
    #
    # Observer của sản phẩm phát `semantic_contract` với **số đếm** fact và
    # danh sách nghĩa vụ, nhưng KHÔNG phát nội dung fact và không phát raw của
    # `analyze`. Lượt chạy đầu tiên của wave này vì thế không chấm được tầng
    # analyze — bộ chấm đọc rỗng rồi kết luận FAIL, tức **chấm FAIL cho một
    # tầng nó không quan sát được**. Cùng họ với đính chính `NOT_REACHED` của
    # `PROVENANCE_AFFORDANCE_AB_4_LUOT`. Biên `call_gemini` là chỗ duy nhất
    # nhìn thấy raw ấy, nên nó được giữ ở đây.
    raw_theo_tang: dict[str, list[str]] = {}

    async def dem(*a, **kw):
        from app.ai.telemetry import current_stage
        ra = await goc_call(*a, **kw)
        st = str(current_stage())
        raw_theo_tang.setdefault(st, []).append(ra)
        bo_dem.ghi_ung_vien(TU_API, ghi_chu=st)
        return ra

    run_id = datetime.now(timezone.utc).strftime("curved-e2e-%Y%m%dT%H%M%SZ")
    manifest = {
        "run_id": run_id,
        "measurement_class": dang_ky["measurement_class"],
        "held_out_claim": dang_ky["held_out_claim"],
        "case_id": CASE_ID,
        "problem_sha256": PROBLEM_HASH,
        "oracle_sha256": ORACLE_HASH,
        "contract_gold_sha256": CONTRACT_GOLD_HASH,
        "gold_sha256": GOLD_HASH,
        "card_C_sha256": card_hash,
        "card_C_bytes": len(the.encode("utf-8")),
        "policy_sha256": _bam(dang_ky),
        "runner_sha256": _h(Path(__file__).read_text(encoding="utf-8")),
        "gold_module": GM.__name__,
        "scorer_module": dang_ky.get("scorer_module"),
        "gold_module_sha256": _h(
            (BACKEND / "scripts" / f"{GM.__name__}.py").read_text(
                encoding="utf-8")),
        "model_provider": "google-generativelanguage-v1beta",
        "model_name": G.MODEL,
        "model_version_or_snapshot": "",
        "reproducibility": "LIMITED — model gọi bằng ALIAS, không phải snapshot",
        "transport_max_attempts": G.MAX_ATTEMPTS,
        "product_repair_limit": PL.MAX_SEMANTIC_PROGRAM_ATTEMPTS,
        "logical_application_call_limit":
            dang_ky["ngan_sach"]["logical_application_call_limit"],
        "token_reservation_per_call":
            dang_ky["ngan_sach"]["token_reservation_per_call"],
        "token_ceiling_observed":
            dang_ky["ngan_sach"]["token_ceiling_observed"],
        "counter_semantics": "REPAIR_PROBE_COUNTER_DECOMPOSITION (2026-09-07)",
        "entrypoint": "app.ai.pipeline.run_pipeline (đường sản phẩm, KHÔNG qua HTTP)",
        "started_at": datetime.now(timezone.utc).isoformat(),
    }
    (ra_dir / f"manifest_{run_id}.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"MANIFEST trước lượt gọi đầu → manifest_{run_id}.json")
    print(f"  thẻ C={card_hash[:16]}… ({manifest['card_C_bytes']}B)")
    print(f"  đề={PROBLEM_HASH[:16]}…  oracle={ORACLE_HASH[:16]}…")
    print(f"  trần: logic {manifest['logical_application_call_limit']} · "
          f"token {manifest['token_ceiling_observed']}\n")

    quan = Quan()
    G.call_gemini = dem                             # type: ignore[assignment]
    PL.call_gemini = dem                            # type: ignore[assignment]
    env: dict | None = None
    ly_do_dung = None
    try:
        env = await PL.run_pipeline(PROBLEM_TEXT, api_key, observer=quan)
    except Exception as e:                                        # noqa: BLE001
        ly_do_dung = f"{type(e).__name__}: {str(e)[:400]}"
        print(f"DỪNG: {ly_do_dung}")
    finally:
        G.call_gemini = goc_call                    # type: ignore[assignment]
        PL.call_gemini = goc_call                   # type: ignore[assignment]
        G.set_budget(None)

    try:
        tk = {"theo_stage": usage_report(), "tong": total_tokens()}
    except Exception:                                             # noqa: BLE001
        tk = {}

    ung_vien = quan.loc("semantic_program_candidate")
    attempts = quan.loc("semantic_program_attempt")
    hop_dong = quan.loc("semantic_contract")
    tuyen = quan.loc("semantic_route")
    cuoi = tuyen[-1] if tuyen else None

    # ─── HỢP ĐỒNG DO `analyze` SINH ──────────────────────────────────────
    #
    # Nguồn ĐÚNG là raw của tầng `semantic_analyze`; hai nguồn còn lại chỉ là
    # dự phòng, và cả hai đều THIẾU nội dung fact — nên khi phải dùng chúng,
    # bộ chấm phải nói `NOT_CAPTURED`, không được nói `FAIL`.
    ct = None
    nguon_ct = "KHONG_CO"
    for raw in raw_theo_tang.get("semantic_analyze", []):
        try:
            ct = json.loads(raw)
            nguon_ct = "RAW_ANALYZE"
            break
        except Exception:                                         # noqa: BLE001
            continue
    if ct is None and env and isinstance(env.get("request_contract"), dict):
        ct, nguon_ct = env["request_contract"], "ENVELOPE"
    if ct is None and hop_dong:
        try:
            ct = {"obligations": json.loads(
                hop_dong[-1].get("obligations", "[]").replace("'", '"'))}
            nguon_ct = "SU_KIEN_DEM"
        except Exception:                                         # noqa: BLE001
            ct, nguon_ct = {"_tho": hop_dong[-1]}, "SU_KIEN_THO"

    spec_cuoi = None
    if env and isinstance(env.get("semantic_program"), dict):
        spec_cuoi = env["semantic_program"]
    if spec_cuoi is None:
        for e in reversed(ung_vien):
            try:
                spec_cuoi = json.loads(e.get("raw") or "")
                break
            except Exception:                                     # noqa: BLE001
                continue

    n_attempt = len(ung_vien)
    out = {
        "manifest": {
            **manifest,
            "finished_at": datetime.now(timezone.utc).isoformat(),
            "run_status": "COMPLETE" if ly_do_dung is None else "INCOMPLETE",
            "stop_reason": ly_do_dung,
            "bo_dem": bo_dem.bao_cao(),
            "logical_calls_used_telemetry": sum(
                v.get("calls", 0) for v in (tk.get("theo_stage") or {}).values()),
        },
        "tokens": tk,
        "su_kien": quan.su_kien,
        "raw_theo_tang": raw_theo_tang,
        "nguon_hop_dong": nguon_ct,
        "ung_vien_tho": ung_vien,
        "attempts": attempts,
        "request_contract": ct,
        "semantic_program_cuoi": spec_cuoi,
        "envelope": env,
        "cham": {
            "analyze": cham_an(
                ct, nguon_ct,
                so_fact_quan_sat=(hop_dong[-1].get("so_fact")
                                  if hop_dong else None)),
            "synthesis": cham_synth(spec_cuoi),
            "ket_qua": cham_ket_qua(
                cuoi, env,
                # Đáp số mong đợi đọc từ GOLD MODULE của lượt chạy —
                # `radius_c` cho bài nón, `area_display` cho bài elip.
                ORACLE.get("radius_c") or ORACLE.get("area_display")),
            "FIRST_ATTEMPT_SERVABLE": (n_attempt == 1
                                       and bool((cuoi or {}).get("servable"))),
            "EVENTUAL_SERVABLE": bool((cuoi or {}).get("servable")),
            "CANDIDATE_ATTEMPTS_QUAN_SAT": n_attempt,
            "REPAIR_ATTEMPTS": max(0, n_attempt - 1),
        },
    }
    (ra_dir / f"e2e_{run_id}.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")

    bd = bo_dem.bao_cao()
    print(f"\nBO_DEM  logical={bd['logical_application_calls']}"
          f"  physical={bd['physical_api_attempts']}"
          f"  candidate={bd['candidate_attempts']}"
          f"  retry={bd['phan_ra']['retry_requests']}")
    print(f"TOKENS  {tk.get('tong')}/{manifest['token_ceiling_observed']}")
    print(f"STAGE   {(cuoi or {}).get('stage_reached')}"
          f"  servable={(cuoi or {}).get('servable')}"
          f"  envelope={(env or {}).get('status')}")
    print(f"ATTEMPT {n_attempt} ứng viên · {max(0, n_attempt - 1)} lượt sửa")
    print(f"→ {ra_dir / f'e2e_{run_id}.json'}")
    return 0 if ly_do_dung is None else 3


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--ra", default=None,
                   help="thư mục artifact (mặc định: "
                        "curved-end-to-end-fresh-confirmation)")
    p.add_argument("--gold", default=None,
                   help="module đề+oracle+gold; mặc định đọc `gold_module` của "
                        f"registration.json, rồi tới {GOLD_MAC_DINH}")
    try:
        from dotenv import load_dotenv

        load_dotenv(BACKEND / ".env")
    except ImportError:
        pass
    return asyncio.run(main_async(p.parse_args()))


if __name__ == "__main__":
    raise SystemExit(main())
