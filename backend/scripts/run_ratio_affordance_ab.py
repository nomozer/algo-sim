# -*- coding: utf-8 -*-
"""A/B ghép cặp cho `DIVIDE_SEGMENT_RATIO_AFFORDANCE_AB`.

**TIÊU QUOTA THẬT.** `ALLOW_LIVE_AI=1` + `GEMINI_API_KEY` trong `backend/.env`.

    MEASUREMENT_CLASS = DEVELOPMENT_SYNTHESIS_AB   ·   HELD_OUT_CLAIM = NO

─── KHÁC `run_affordance_ab.py` Ở ĐÚNG MỘT ĐIỀU: ANALYZE = 0 ───────────

Runner kia gọi `analyze` một lượt mỗi đề rồi chia hợp đồng cho hai arm. Ở đây
hợp đồng **cố định trong `gold_ratio_ab.CORPUS`** và đã kiểm tất định (gold
4/4 `served`). Nhờ vậy phép đo hỏi đúng một câu — *"cho CÙNG một hợp đồng, thẻ
nào làm mô hình soạn đúng hơn"* — và không tiêu lượt gọi nào cho tầng trích
xuất mà wave này không đụng tới.

Hệ quả phải khai khi báo số: kết quả này đo **riêng tầng tổng hợp**. Chi phí
toàn pipeline (có `analyze`, có vòng sửa) **CHƯA ĐO**.

─── ONE-SHOT LÀ CẤU HÌNH CỦA RUNNER, KHÔNG PHẢI CỦA SẢN PHẨM ───────────

Mỗi arm sinh đúng một ứng viên: hạ `MAX_SEMANTIC_PROGRAM_ATTEMPTS` **trong
tiến trình runner**. Hằng số sản phẩm không đổi, và `test_runner_ratio_ab`
chứng minh điều đó tại biên gọi provider bằng stub.
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
for p in (str(BACKEND), str(BACKEND / "scripts")):
    if p not in sys.path:
        sys.path.insert(0, p)

from gold_ratio_ab import (  # noqa: E402
    CA_DOI_CHUNG, CA_MUC_TIEU, CONTRACT_HASH, CORPUS, CORPUS_HASH, GOLD_HASH,
    ORACLE_HASH, RA, _bam,
)
from run_affordance_ab import Quan  # noqa: E402  (tái dùng, không chép)

from app.simulation.semantic_program.segment_relation import (  # noqa: E402
    bat_bien_chia_doan,
)

#: 4 đề × 2 arm × 1 lượt tổng hợp. Analyze = 0, repair trong phép đo = 0.
MAX_LOGICAL = 8
#: Dẫn xuất, không đặt tay — `MAX_ATTEMPTS` là trần retry của transport.
def _tran_vat_ly() -> int:
    from app.ai import gemini as G
    return MAX_LOGICAL * G.MAX_ATTEMPTS


#: Trần token **theo LƯỢT GỌI**, không theo tổng — sửa đúng giới hạn mà
#: `DIVIDE_SEGMENT_RATIO_AFFORDANCE_AB` §6 đã ghi: guard cũ kiểm tổng nên nó
#: chặn được việc BẮT ĐẦU một cặp, mà không cắt được giữa cặp, và cặp cuối
#: đẩy tổng vượt trần (47 303/40 000).
#:
#: Đặt từ telemetry lịch sử: lượt ấy tiêu 47 303 cho 8 lượt ⇒ ~5 913/lượt.
#: `7_500` để dư đầu, và ngân sách một lượt chạy = `7_500 × 2 × số ca`.
TOKEN_PER_CALL = 7_500
TOKEN_CEILING = 40_000          # trần TOÀN CORPUS, giữ cho test cũ
NR, NO = "NOT_REACHED", "NOT_OBSERVED"


def _h(t: str) -> str:
    return hashlib.sha256(t.encode("utf-8")).hexdigest()


def lich_chay(i: int) -> tuple[str, str]:
    """Luân phiên thứ tự trong cặp — khoá TRƯỚC khi xem kết quả."""
    return ("A", "B") if i % 2 == 0 else ("B", "A")


class NganSach:
    """Đếm lượt VẬT LÝ ở biên `call_gemini` và chặn khi vượt trần."""

    def __init__(self, tran: int) -> None:
        self.tran, self.physical = tran, 0
        self.theo_stage: dict[str, int] = {}

    def ghi(self, stage: str) -> None:
        self.physical += 1
        self.theo_stage[stage] = self.theo_stage.get(stage, 0) + 1
        if self.physical > self.tran:
            raise RuntimeError(f"VƯỢT TRẦN VẬT LÝ {self.tran}")


# ══ CHẤM ═════════════════════════════════════════════════════════════════
def _lenh_sinh(spec: dict, ten: str | None) -> dict | None:
    if not ten:
        return None
    for st in spec.get("statements", []):
        if st.get("target_var") == ten:
            return st
    return None


def _bieu_thuc(st: dict | None) -> dict:
    return (st or {}).get("expr") or {}


def cham(ca: dict, spec: dict | None, out: Any, canh_ok: bool) -> dict[str, Any]:
    """Chấm ĐÚNG VỊ TRÍ trước, cách dựng sau.

    `POSITION_CORRECT` đọc **đáp số** — một ĐỘ DÀI, nên nó bất biến với hệ trục
    mô hình tự chọn. Đó là lý do corpus không cho toạ độ: so toạ độ thô sẽ chấm
    trượt một chương trình đúng chỉ vì nó đặt hình ở chỗ khác.

    `DIVIDE_SEGMENT_USED` và `T_CORRECT` là **thông tin phụ**: cách dựng tương
    đương về toán (vd `midpoint` cho ca đối chứng) vẫn đúng vị trí, và luật
    quyết định không đòi mô hình phải dùng đúng một phép.
    """
    c: dict[str, Any] = {}
    w = ca["witness"]
    mong = ca["exact_expected_results"][w]

    if spec is None:
        c.update({k: NO for k in ("DIVIDE_SEGMENT_USED", "T_WRITTEN",
                                  "T_EXPECTED_FOR_ORDER", "OPERAND_ORDER")})
        c["T_CORRECT"] = NO
        c["SCHEMA_VALIDATION_RESULT"] = "FAIL"
        for k in ("GROUNDING_RESULT", "COVERAGE_RESULT", "RUNTIME_RESULT",
                  "SOURCE_INVARIANT_RESULT", "POSTCONDITIONS_RESULT",
                  "SCENE3D_RESULT"):
            c[k] = NR
        c["POSITION_CORRECT"] = NR
        c["SERVABLE"] = "FAIL"
        return c

    c["SCHEMA_VALIDATION_RESULT"] = "PASS"
    # ─── Truy: điểm được hỏi ← câu lệnh sinh nó ───────────────────────────
    st = _lenh_sinh(spec, ca["diem_duoc_hoi"])
    e = _bieu_thuc(st)
    la_ds = e.get("kind") == "divide_segment"
    c["DIVIDE_SEGMENT_USED"] = la_ds
    c["PRODUCER_KIND"] = e.get("kind") or (st or {}).get("kind") or NO
    if la_ds:
        a, b, t = e.get("a"), e.get("b"), str(e.get("ratio"))
        thu_tu = f"{a}->{b}"
        c["OPERAND_ORDER"] = thu_tu
        c["T_WRITTEN"] = t
        # ⚠️ Tra `t` đúng theo chiều THỰC TẾ chương trình viết, không theo một
        # chiều giả định. Ca `r3` cố ý bất đối xứng để bắt lỗi ấy.
        mong_t = ca["t_theo_thu_tu"].get(thu_tu)
        c["T_EXPECTED_FOR_ORDER"] = mong_t or NO
        c["T_CORRECT"] = (NO if mong_t is None else
                          ("PASS" if t == mong_t else "FAIL"))
    else:
        c.update({"OPERAND_ORDER": NO, "T_WRITTEN": NO,
                  "T_EXPECTED_FOR_ORDER": NO, "T_CORRECT": NO})

    stage = out.stage_reached
    c["GROUNDING_RESULT"] = "FAIL" if stage == "grounding" else (
        NR if stage in ("ir_static",) else "PASS")
    c["COVERAGE_RESULT"] = ("FAIL" if stage == "structural_coverage" else
                            (NR if stage in ("ir_static", "grounding") else "PASS"))
    c["RUNTIME_RESULT"] = ("FAIL" if stage == "execution" else
                           ("PASS" if out.executable else NR))
    # ─── TẦNG BẤT BIẾN NGUỒN — nằm GIỮA execution và postconditions ────────
    #
    # `SEGMENT_RELATION_*` dựng nó, và nó hỏi câu khác hẳn hậu điều kiện:
    # *"hình dựng ra có đúng dữ kiện đề cho không"*. Gộp vào
    # `POSTCONDITIONS_RESULT` thì một chương trình bị bác vì SAI VỊ TRÍ ĐIỂM
    # sẽ bị đọc thành "hậu điều kiện hỏng" — hai kết luận khác nhau.
    _truoc_nguon = ("semantic_program", "ir_static", "grounding",
                    "structural_coverage", "execution")
    c["SOURCE_INVARIANT_RESULT"] = ("FAIL" if stage == "source_invariant" else
                                    (NR if stage in _truoc_nguon else "PASS"))
    c["POSTCONDITIONS_RESULT"] = ("PASS" if out.servable else
                                  ("FAIL" if stage == "postconditions" else NR))
    c["SERVABLE"] = "PASS" if out.servable else "FAIL"
    if out.servable:
        mem = {k: str(v) for k, v in (out.final_memory or {}).items()}
        c["ANSWER_OBSERVED"] = mem.get(w, NO)
        c["POSITION_CORRECT"] = "PASS" if mem.get(w) == mong else "FAIL"
    else:
        c["ANSWER_OBSERVED"] = NR
        c["POSITION_CORRECT"] = NR
    c["SCENE3D_RESULT"] = ("PASS" if canh_ok else
                           ("FAIL" if out.servable else NR))
    return c


# ══ MỘT ARM ══════════════════════════════════════════════════════════════
async def chay_arm(ca, contract, the: str, api_key) -> dict[str, Any]:
    from app.ai import pipeline
    from app.ai.telemetry import usage_report
    from app.simulation.semantic_program import grammar_card as GC
    from app.simulation.semantic_program.domain_profile import DOMAIN_HINH_HOC
    from app.simulation.semantic_program.route import verify_and_compile

    def _chup() -> dict:
        return {s: dict(v) for s, v in usage_report().items()}

    truoc = _chup()
    q = Quan()
    goc = GC.grammar_card
    GC.grammar_card = lambda domain=None: the       # type: ignore[assignment]
    try:
        spec, err = await pipeline.stage_semantic_program(
            ca["problem_text"], {}, api_key, contract,
            domain=DOMAIN_HINH_HOC, observer=q)
    finally:
        GC.grammar_card = goc                       # type: ignore[assignment]
    sau = _chup()

    #: Token CỦA RIÊNG arm này = hiệu bộ đếm quanh lượt gọi.
    #: `total_tokens` là `totalTokenCount` của API và ĐÃ gồm thoughts, nên
    #: tổng dùng thẳng nó; các thành phần chỉ để quan sát, KHÔNG cộng lại.
    tk: dict[str, int] = {}
    for s, v in sau.items():
        for k, n in v.items():
            tk[k] = tk.get(k, 0) + n - truoc.get(s, {}).get(k, 0)

    raw = q.raw_dau()
    ra: dict[str, Any] = {"card_hash": _h(the), "card_bytes": len(the.encode()),
                          "raw_candidate": raw, "loi": err, "tokens": tk}
    spec_json = None
    if spec is not None:
        spec_json = spec.model_dump(mode="json")
    elif raw:
        try:
            spec_json = json.loads(raw)
        except Exception:                                         # noqa: BLE001
            spec_json = None
    ra["chuong_trinh"] = spec_json

    class _Rong:
        stage_reached, executable, servable = "semantic_program", False, False
        error_code, details, final_memory = "semantic_program_invalid", [], {}

    out, canh_ok = _Rong(), False
    if spec is not None:
        out = verify_and_compile(contract, spec)
        try:
            canh = pipeline._dung_scene3d(spec, contract) or {}
            canh_ok = bool(out.servable and canh.get("objects"))
            ra["scene3d_objects"] = len(canh.get("objects", []))
        except Exception as e:                                    # noqa: BLE001
            ra["scene3d_loi"] = f"{type(e).__name__}: {str(e)[:200]}"
    ra.update(stage=out.stage_reached, servable=bool(out.servable),
              error_code=out.error_code,
              details=[str(x)[:300] for x in (out.details or [])],
              final_memory={k: str(v) for k, v in (out.final_memory or {}).items()})
    ra["cham"] = cham(ca, spec_json if spec is not None else spec_json,
                      out, canh_ok)
    if spec is None and spec_json is not None:
        ra["cham"]["SCHEMA_VALIDATION_RESULT"] = "FAIL"
    return ra


async def main_async(args) -> int:
    from acceptance_integrity import kiem_moi_truong, moi_truong_hien_tai
    from app.ai import gemini as G
    from app.ai import pipeline as PL
    from app.simulation.semantic_program.request_contract import RequestContract

    if os.environ.get("ALLOW_LIVE_AI") != "1":
        print("ALLOW_LIVE_AI != 1 — từ chối tiêu quota.")
        return 2
    api_key = os.environ.get("GEMINI_API_KEY")
    print(f"GEMINI_API_KEY: {'PRESENT' if api_key else 'ABSENT'}")
    if not api_key:
        return 2

    ra_dir = Path(args.ra).resolve() if getattr(args, "ra", None) else RA
    globals()["RA"] = ra_dir            # mọi chỗ ghi artifact dùng chung một biến
    card_A = (ra_dir / "card_A.txt").read_text(encoding="utf-8")
    card_B = (ra_dir / "card_B.txt").read_text(encoding="utf-8")
    THE = {"A": card_A, "B": card_B}
    if _h(card_A) == _h(card_B):
        print("THẺ A ≡ THẺ B — không có gì để đo.")
        return 2

    tran_vl = _tran_vat_ly()
    ns = NganSach(tran_vl)
    moi_truong = moi_truong_hien_tai()
    goc_call = G.call_gemini

    async def dem(*a, **kw):
        from app.ai.telemetry import current_stage
        try:
            ns.ghi(str(current_stage()))
        except RuntimeError:
            raise
        except Exception:                                         # noqa: BLE001
            ns.ghi("?")
        return await goc_call(*a, **kw)

    ca_chay = [c for c in CORPUS
               if not args.ca or c["case_id"] in args.ca.split(",")]
    # ─── NGÂN SÁCH THEO LƯỢT CHẠY, không theo corpus ───────────────────────
    #
    # Chạy 2 ca thì trần là 4 lượt, không phải 8. Trần corpus giữ nguyên làm
    # chặn ngoài; trần lượt chạy mới là thứ thật sự gác.
    logic_lan_nay = 2 * len(ca_chay)
    token_lan_nay = TOKEN_PER_CALL * logic_lan_nay
    run_id = datetime.now(timezone.utc).strftime("ratio-ab-%Y%m%dT%H%M%SZ")
    lich = {c["case_id"]: lich_chay(i) for i, c in enumerate(CORPUS)}
    dang_ky = json.loads((ra_dir / "registration.json").read_text(encoding="utf-8"))
    manifest = {
        "run_id": run_id,
        "measurement_class": "DEVELOPMENT_SYNTHESIS_AB",
        "held_out_claim": False,
        "analyze_live_calls": 0,
        "analyze_source": "HOP_DONG_CO_DINH trong gold_ratio_ab.CORPUS",
        "card_A_hash": _h(card_A), "card_A_bytes": len(card_A.encode()),
        "card_B_hash": _h(card_B), "card_B_bytes": len(card_B.encode()),
        "card_delta_bytes": len(card_B.encode()) - len(card_A.encode()),
        "corpus_hash": CORPUS_HASH, "contract_hash": CONTRACT_HASH,
        "oracle_hash": ORACLE_HASH, "gold_hash": GOLD_HASH,
        "policy_hash": _bam(dang_ky),
        "runner_hash": _h(Path(__file__).read_text(encoding="utf-8")),
        "gold_module_hash": _h((BACKEND / "scripts" / "gold_ratio_ab.py")
                               .read_text(encoding="utf-8")),
        "model_provider": "google-generativelanguage-v1beta",
        "model_name": G.MODEL, "model_version_or_snapshot": "",
        "reproducibility": "LIMITED — model gọi bằng ALIAS, không phải snapshot",
        "repair_calls_configured": 0,
        "product_repair_limit_unchanged": PL.MAX_SEMANTIC_PROGRAM_ATTEMPTS,
        "transport_max_attempts": G.MAX_ATTEMPTS,
        "logical_budget": logic_lan_nay,
        "logical_budget_corpus": MAX_LOGICAL,
        "physical_budget": tran_vl,
        "token_ceiling_observed": token_lan_nay,
        "token_per_call_budget": TOKEN_PER_CALL,
        "cases_in_run": [c["case_id"] for c in ca_chay],
        "token_fields_reported": ["prompt_tokens", "candidates_tokens",
                                  "cached_content_tokens", "thoughts_tokens",
                                  "total_tokens"],
        "token_total_formula": ("total_tokens = totalTokenCount cua API (DA gom "
                                "thoughts). KHONG cong prompt+candidates+thoughts "
                                "de tranh dem trung; cached la TAP CON cua prompt."),
        "case_order": {k: list(v) for k, v in lich.items()},
        "moi_truong": moi_truong,
        "started_at": datetime.now(timezone.utc).isoformat(),
    }
    ra_dir.mkdir(parents=True, exist_ok=True)
    (ra_dir / f"manifest_{run_id}.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"MANIFEST trước lượt gọi đầu → manifest_{run_id}.json")
    print(f"  A={manifest['card_A_hash'][:16]}… ({manifest['card_A_bytes']}B)"
          f"  B={manifest['card_B_hash'][:16]}… ({manifest['card_B_bytes']}B)"
          f"  Δ={manifest['card_delta_bytes']:+d}B")
    print(f"  corpus={CORPUS_HASH[:16]}…  contract={CONTRACT_HASH[:16]}…")
    print(f"  lịch={manifest['case_order']}")
    print(f"  ngân sách lượt này: logic {logic_lan_nay} · vật lý {tran_vl}"
          f" · token {token_lan_nay} ({TOKEN_PER_CALL}/lượt)\n")

    G.call_gemini = dem                             # type: ignore[assignment]
    PL.call_gemini = dem                            # type: ignore[assignment]
    goc_tran = PL.MAX_SEMANTIC_PROGRAM_ATTEMPTS
    PL.MAX_SEMANTIC_PROGRAM_ATTEMPTS = 1            # ONE-SHOT, chỉ ở runner
    kq: list[dict[str, Any]] = []
    hoan_tat, ly_do_dung = True, None
    try:
        from app.ai.telemetry import total_tokens
        for i, c in enumerate(ca_chay):
            # ─── KIỂM NGÂN SÁCH TRƯỚC MỖI CẶP ───────────────────────────
            con_logic = logic_lan_nay - 2 * i
            if con_logic < 2 or ns.physical + 2 > tran_vl:
                hoan_tat, ly_do_dung = False, "NGAN_SACH_LUOT_GOI"
                break
            # DỰ TRỮ ĐỦ CHO CẢ CẶP trước khi bắt đầu nó — đó là điều bản trước
            # không làm, nên nó vượt trần đúng ở cặp cuối.
            if total_tokens() + 2 * TOKEN_PER_CALL > token_lan_nay:
                hoan_tat, ly_do_dung = False, "TRAN_TOKEN"
                break
            print(f"── {c['case_id']} ({c['feature']})", flush=True)
            kiem_moi_truong(moi_truong, nhan=c["case_id"])
            # ─── GẮN SOURCE INVARIANT NHƯ ĐƯỜNG SẢN PHẨM ──────────────────
            #
            # `build_request_contract` gắn chúng ở biên đóng băng hợp đồng
            # (`analyze_contract`), nhưng runner dựng hợp đồng CỐ ĐỊNH nên
            # không đi qua biên ấy. Không gắn thì cổng bất biến nguồn — thứ
            # `SEGMENT_RELATION_*` vừa dựng — sẽ KHÔNG chạy, và phép đo sẽ báo
            # `served` cho đúng lớp chương trình mà sản phẩm đang từ chối.
            _rc = RequestContract.model_validate(c["request_contract"])
            _bt = bat_bien_chia_doan(_rc, _rc.problem_text)
            contract = _rc.model_copy(update={
                "source_invariants": tuple(_rc.source_invariants or ()) + _bt})
            r: dict[str, Any] = {"case_id": c["case_id"],
                                 "thu_tu": list(lich[c["case_id"]]),
                                 "request_contract": c["request_contract"]}
            arms = {}
            for arm in lich[c["case_id"]]:
                arms[arm] = await chay_arm(c, contract, THE[arm], api_key)
                a = arms[arm]["cham"]
                print(f"   [{arm}] vị trí={a.get('POSITION_CORRECT')}"
                      f" t={a.get('T_WRITTEN')}→{a.get('T_EXPECTED_FOR_ORDER')}"
                      f"({a.get('T_CORRECT')})"
                      f" stage={arms[arm]['stage']}"
                      f" servable={arms[arm]['servable']}"
                      f" tok={arms[arm]['tokens'].get('total_tokens')}")
            r["arms"] = arms
            kq.append(r)
    except Exception as e:                                        # noqa: BLE001
        hoan_tat, ly_do_dung = False, f"{type(e).__name__}: {str(e)[:300]}"
        print(f"DỪNG: {ly_do_dung}")
    finally:
        G.call_gemini = goc_call                    # type: ignore[assignment]
        PL.call_gemini = goc_call                   # type: ignore[assignment]
        PL.MAX_SEMANTIC_PROGRAM_ATTEMPTS = goc_tran

    from app.ai.telemetry import total_tokens, usage_report
    try:
        tk = {"theo_stage": usage_report(), "tong": total_tokens()}
    except Exception:                                             # noqa: BLE001
        tk = {}
    logic = sum(v.get("calls", 0) for v in (tk.get("theo_stage") or {}).values())
    out = {"manifest": {**manifest,
                        "finished_at": datetime.now(timezone.utc).isoformat(),
                        "logical_calls_used_telemetry": logic,
                        "physical_attempts_used": ns.physical,
                        "physical_by_stage": ns.theo_stage,
                        "run_status": "COMPLETE" if hoan_tat else "INCOMPLETE",
                        "stop_reason": ly_do_dung,
                        "cases_done": [r["case_id"] for r in kq],
                        "cases_planned": [c["case_id"] for c in ca_chay]},
           "tokens": tk, "ket_qua": kq}
    (ra_dir / f"ratio_ab_{run_id}.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nLOGICAL={logic}/{logic_lan_nay}  PHYSICAL={ns.physical}/{tran_vl}"
          f"  TOKENS={tk.get('tong')}/{token_lan_nay}")
    print(f"RUN_STATUS={'COMPLETE' if hoan_tat else 'INCOMPLETE'}"
          f"{'' if hoan_tat else '  ly_do=' + str(ly_do_dung)}")
    print(f"→ {ra_dir / f'ratio_ab_{run_id}.json'}")
    return 0 if hoan_tat else 3


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--ca", default=None)
    p.add_argument("--ra", default=None,
                   help="thư mục artifact (mặc định: divide-segment-ratio-ab)")
    try:
        from dotenv import load_dotenv

        load_dotenv(BACKEND / ".env")
    except ImportError:
        pass
    return asyncio.run(main_async(p.parse_args()))


if __name__ == "__main__":
    raise SystemExit(main())
