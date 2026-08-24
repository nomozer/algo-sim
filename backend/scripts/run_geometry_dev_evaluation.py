# -*- coding: utf-8 -*-
"""Runner DEV hình học — đo AI có sinh được Geometry Program đúng không.

    đề (văn xuôi) → analyze → RequestContract → sinh IR → validate
                  → interpreter → checker → ORACLE ĐỘC LẬP

**KHÔNG sửa `run_sealed_evaluation.py`.** Cái đó thuộc miền Tin học và mang con
dấu của lượt SEALED #1; đụng vào nó là làm bẩn một artifact đã đóng.

⚠️ ĐÂY LÀ TẬP DEV, KHÔNG phải benchmark. Nó **được nhìn**, và hệ **được sửa**
theo nó. Số của nó không bao giờ là số held-out của luận văn — held-out phải do
custodian chọn bằng seed của GVHD.

## Vì sao phải ép skill từ phía harness

`pipeline.stage_semantic_program` **hardcode** `load_skill("semantic_program")`
(`pipeline.py:483`) — prompt của miền Tin học. Không file nào trong `app/` tham
chiếu `geometry_program_generator.md`.

Nên runner **bọc `load_skill` từ ngoài**, cùng khuôn proxy đã dùng ở
`run_sealed_evaluation`. Đây là quyết định có chủ đích, không phải mẹo:

- Phase 5 chỉ đo **năng lực sinh**, không đo **định tuyến sản phẩm**.
- Cho sản phẩm tự route sang hình học là một quyết định vận hành riêng, phải
  đi kèm bằng chứng — mà bằng chứng ấy chính là thứ lượt đo này sắp tạo ra.
  Route trước rồi mới đo là đảo ngược thứ tự.

⇒ **Sản phẩm hiện KHÔNG phục vụ hình học**, và lượt đo này không làm nó phục vụ.

## Oracle bám vào đâu

Custodian **không được đoán tên biến của LLM**. Nên `oracle_result` khai theo
**tên NGHĨA VỤ** (`{"volume": "2/3"}`), runner tra nghĩa vụ cùng loại trong hợp
đồng server đã đóng băng để biết đối tượng nào cần chấm, rồi gọi oracle độc lập.
Cùng hợp đồng với `_cham` của miền Tin học, và cùng lý do.
"""
from __future__ import annotations

import argparse
import asyncio
import importlib.util
import json
import os
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
BACKEND = ROOT / "backend"
sys.path.insert(0, str(BACKEND))
sys.path.insert(0, str(Path(__file__).resolve().parent))

GEO = ROOT / "docs" / "evaluation" / "geometry"
DEV = GEO / "dev" / "cases.json"
ORACLE_PY = GEO / "custodian" / "geometry_oracle.py"

#: Skill hình học. Ép vào chỗ `pipeline` đang gọi `"semantic_program"`.
SKILL_HINH_HOC = "geometry_program_generator"

#: Miền truyền thẳng cho `stage_semantic_analyze` (Wave 2). Nhập từ nguồn chứ
#: không viết chuỗi trần: đổi tên miền ở `domain_profile` mà runner còn giữ
#: chuỗi cũ thì lượt đo lặng lẽ chạy bằng prompt Tin học — đúng lỗi Phase 5.
from app.simulation.semantic_program.domain_profile import (  # noqa: E402
    DOMAIN_HINH_HOC,
)

#: Trần lượt logic. DẪN từ call graph: analyze ≤2 · semantic_analyze 1 ·
#: semantic_program ≤3 ⇒ 6/case. 10 case ⇒ 60, cộng đệm transient ⇒ 80.
#: KHÔNG dùng trần 13/case của miền Tin học: runner này không chạy classify,
#: simulate hay one-route recovery, nên mượn trần ấy là xin thừa quota.
TRAN_LOGIC = 60
TRAN_HTTP = 80


class DungSach(Exception):
    """Dừng có chủ đích, không phải sự cố."""


def _bat_buoc_live() -> None:
    if os.environ.get("ALLOW_LIVE_AI") != "1":
        raise DungSach(
            "Thiếu ALLOW_LIVE_AI=1. Lượt này TIÊU QUOTA THẬT — "
            f"trần {TRAN_LOGIC} lượt logic / {TRAN_HTTP} lần thử HTTP."
        )


def _nap_oracle():
    spec = importlib.util.spec_from_file_location("geometry_oracle", ORACLE_PY)
    mod = importlib.util.module_from_spec(spec)
    sys.modules["geometry_oracle"] = mod
    spec.loader.exec_module(mod)
    return mod


# ── chấm bằng ORACLE ĐỘC LẬP ──────────────────────────────────────────────
def cham_oracle(case: dict, contract, final_memory: dict | None) -> dict[str, Any]:
    """So kết quả máy với `oracle_result` — bám theo NGHĨA VỤ, không theo tên biến.

    Trả `verdict ∈ {PASS, FAIL, UNGRADED, NO_RESULT}`. `UNGRADED` khi đề không
    khai khoá nào trùng tên nghĩa vụ, hoặc hợp đồng không có nghĩa vụ loại ấy —
    **không** phải `FAIL`: nhầm hai cái là biến "không chấm được" thành "sai".
    """
    from fractions import Fraction

    if final_memory is None:
        return {"verdict": "NO_RESULT", "ly_do": "chương trình không chạy ra kết quả"}

    mong = case.get("oracle_result") or {}
    obls = {o.kind: o for o in (contract.obligations if contract else [])}
    cham_duoc = [k for k in mong if k in obls]
    if not cham_duoc:
        return {"verdict": "UNGRADED",
                "ly_do": f"không nghĩa vụ nào khớp khoá oracle {sorted(mong)}"}

    lech: list[str] = []
    for kind in cham_duoc:
        ob = obls[kind]
        may = final_memory.get(ob.witness) if ob.witness else None
        de = mong[kind]
        if isinstance(de, bool):
            # Quan hệ: checker server-owned đã trả `None` khi thoả. Ở đây chỉ
            # đối chiếu kỳ vọng của đề với việc chương trình có khẳng định nó.
            if bool(may) != de:
                lech.append(f"{kind}: máy={may!r}, đề mong {de!r}")
        else:
            try:
                if may is None or Fraction(str(may)) != Fraction(str(de)):
                    lech.append(f"{kind}: máy={may!r}, đề mong {de!r}")
            except (ValueError, ZeroDivisionError, TypeError):
                lech.append(f"{kind}: không so được máy={may!r} với {de!r}")
    return {"verdict": "FAIL" if lech else "PASS", "lech": lech,
            "da_cham": cham_duoc}


# ── một case ──────────────────────────────────────────────────────────────
async def chay_mot_case(case: dict, api_key: str) -> dict[str, Any]:
    from app.ai import gemini, pipeline
    from app.simulation.semantic_program.route import verify_and_compile

    import api_usage_log as AU
    import reliability_v2 as RV

    de = case["problem_text"]
    ra: dict[str, Any] = {
        "case_id": case["case_id"],
        "problem": de,
        "chu_de": case.get("chu_de"),
        "expected_obligations": case.get("expected_obligations", []),
        "generated_program": None,
        # Đầu ra THÔ khi IR bị từ chối. PHASE 5 có 4 bài trượt G1 và không bài
        # nào để lại thứ mô hình thật sự viết — phân tích phải dựng lại từ chuỗi
        # lỗi Pydantic, tức đọc dấu vết thay vì đọc vật chứng.
        "generated_raw": None,
        "obligations_declared": [],
        "schema_pass": False,
        "semantic_pass": False,
        "executable": False,
        "oracle_pass": None,
        "failure_layer": None,
        "failure_code": None,
        "failure_reason": None,
    }

    # ÉP SKILL HÌNH HỌC + BỌC BỘ GHI. Cả hai khôi phục trong `finally`: bỏ sót
    # thì case sau chạy qua một `load_skill`/`call_gemini` bọc chồng nhiều lớp.
    goc_load = pipeline.load_skill
    goc_call = pipeline.call_gemini

    def _load(ten: str) -> str:
        return goc_load(SKILL_HINH_HOC if ten == "semantic_program" else ten)

    ghi = AU.GhiNhanApi()

    # ─── VÌ SAO THÂN NẰM TRONG MỘT HÀM CON ───────────────────────────────
    #
    # Bản trước có `return ra` NGAY TRONG `try`, và ba dòng hậu xử lý nằm SAU
    # `finally` — nên mọi bài trượt sớm **không bao giờ** được gán
    # `obligation_match`. Đo được trên chính artifact PHASE 5: 4 bài trượt G1
    # thiếu hẳn khoá ấy, và `tong_ket` che mất vì nó dùng `.get()`.
    #
    # Hàm con làm cho "thoát sớm" và "hậu xử lý" không còn tranh nhau một lối
    # ra. Hình dạng artifact vì thế ỔN ĐỊNH trên MỌI đường — điều kiện để một
    # bộ chấm downstream đọc nó mà không phải phòng thủ từng khoá.
    async def _than() -> None:
        # ─── WAVE 2: TRUYỀN MIỀN, KHÔNG DÙNG BỘ NHẬN MIỀN ─────────────────
        #
        # Lượt Phase 5 đầu chỉ ép skill ở `semantic_program`; `analyze` vẫn là
        # prompt Tin học với enum 19 nghĩa vụ, và 3/6 chương trình hợp lệ khai
        # nghĩa vụ Tin học cho bài hình học. Đây là chỗ vá.
        #
        # Truyền THẲNG `hinh_hoc` chứ không gọi `detect_domain`: bộ nhận miền
        # là một SUY ĐOÁN, và một phép đo không được phụ thuộc vào suy đoán —
        # nếu nó đoán sai một bài thì số của bài đó nói về bộ nhận miền chứ
        # không nói về hệ sinh. (`test_geometry_wave2` vẫn khoá riêng rằng bộ
        # nhận miền bắt đúng cả 10 bài này.)
        contract, err = await pipeline.stage_semantic_analyze(
            de, api_key, domain=DOMAIN_HINH_HOC
        )
        if contract is None:
            ra.update(failure_layer=0, failure_code="contract_failure",
                      failure_reason=err,
                      generated_raw=ghi.tho_cuoi("semantic_analyze"))
            return
        ra["obligations_declared"] = sorted({o.kind for o in contract.obligations})

        spec, serr = await pipeline.stage_semantic_program(de, {}, api_key, contract)
        if spec is None:
            hong = serr or ""
            la_schema = "validation error" in hong and "SemanticProgramSpec" in hong
            ra.update(
                schema_pass=not la_schema,
                failure_layer=2 if la_schema else 3,
                failure_code="semantic_program_invalid",
                failure_reason=hong,
                generated_raw=ghi.tho_cuoi("semantic_program"),
            )
            return
        ra["schema_pass"] = True
        ra["semantic_pass"] = True
        ra["generated_program"] = spec.model_dump(mode="json")

        outcome = verify_and_compile(contract, spec)
        ra["executable"] = bool(outcome.executable)
        if not outcome.executable:
            ra.update(failure_layer=4 if outcome.stage_reached == "execution" else 6,
                      failure_code=outcome.error_code,
                      failure_reason=outcome.reason)
        cham = cham_oracle(case, contract, outcome.final_memory)
        ra["oracle"] = cham
        ra["oracle_pass"] = (True if cham["verdict"] == "PASS"
                             else False if cham["verdict"] == "FAIL" else None)

    pipeline.load_skill = _load
    pipeline.call_gemini = ghi.boc(goc_call)
    try:
        await _than()
    except gemini.BudgetExceeded:
        raise
    except Exception as e:  # noqa: BLE001 — hỏng một case không được giết cả lượt
        ra.update(failure_layer=1, failure_code=type(e).__name__,
                  failure_reason=str(e)[:400])
    finally:
        pipeline.load_skill = goc_load
        pipeline.call_gemini = goc_call

    ra["obligation_match"] = RV.obligation_match(
        ra["expected_obligations"], ra["obligations_declared"]
    )
    # Độ trễ THEO TỪNG BÀI. Tổng của cả lượt không thay được: một bài chậm gấp
    # mười vì đi hết ba vòng sửa là thông tin, còn trung bình thì che nó đi.
    ra["do_tre"] = ghi.do_tre()
    return ra


async def _main(args) -> int:
    from app.ai import gemini, telemetry

    _bat_buoc_live()
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise DungSach("Thiếu GEMINI_API_KEY (backend/.env).")

    cases = json.loads(DEV.read_text(encoding="utf-8"))["cases"]
    print(f"DEV HÌNH HỌC: {len(cases)} bài — ĐƯỢC NHÌN, không phải held-out")
    print(f"Skill ép: {SKILL_HINH_HOC} · model {gemini.MODEL}")
    print(f"Ngân sách: {TRAN_LOGIC} logic / {TRAN_HTTP} HTTP\n")

    budget = gemini.ApiBudget(max_api_calls=TRAN_HTTP, max_logical_calls=TRAN_LOGIC)
    gemini.set_budget(budget)
    # Bộ đếm token là TOÀN CỤC trong tiến trình. Không xoá thì con số của lượt
    # này cộng dồn cả những gì đã chạy trước trong cùng tiến trình — và một con
    # số chi phí sai theo chiều CAO cũng vô dụng như sai theo chiều thấp.
    telemetry.reset_usage()
    ket: list[dict] = []
    dung_som = None
    try:
        for i, c in enumerate(cases, 1):
            print(f"[{i}/{len(cases)}] {c['case_id']}", flush=True)
            ket.append(await chay_mot_case(c, api_key))
    except gemini.BudgetExceeded as e:
        dung_som = f"BUDGET_EXHAUSTED: {e}"
        print(f"\n{dung_som}")
    finally:
        gemini.set_budget(None)

    bao = tong_ket(ket, len(cases), dung_som, gemini.MODEL, budget)
    out = Path(args.out_dir)
    out.mkdir(parents=True, exist_ok=True)
    (out / "geometry_dev_results.json").write_text(
        json.dumps({"tom_tat": bao, "cases": ket}, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8")
    print("\n── KẾT QUẢ (DEV, không phải held-out) ──")
    for k in ("G1_schema", "G2_semantic", "A_executable", "O_oracle"):
        print(f"  {k:14} {bao[k]['tu_so']}/{bao[k]['mau_so']}")
    print(f"  obligation khớp {bao['obligation_match']['khop_hoan_toan']}"
          f"/{bao['obligation_match']['mau_so']}")
    cp = bao["chi_phi"]
    if cp["do_duoc"]:
        print(f"  chi phí        {cp['luot_logic']}/{cp['tran_logic']} lượt "
              f"logic · {cp['request_http']}/{cp['tran_http']} HTTP · "
              f"{cp['tong_token']} token")
        ut = cp["uoc_tinh_chi_phi"]
        print(f"  ước tính       "
              + (f"~${ut['usd']:.4f} (chặn trên, giá {ut['ngay_tra_gia']})"
                 if ut["uoc_tinh_duoc"] else ut["ly_do"]))
        print(f"  độ trễ         {cp['do_tre'].get('tong_giay', 0)}s tổng · "
              f"chậm nhất {cp['do_tre'].get('cham_nhat_giay', 0)}s")
    return 0


def tong_ket(ket: list[dict], n: int, dung_som: str | None, model: str,
             budget=None) -> dict:
    """ĐẾM THÔ, không phần trăm — mẫu số 10 < 20, `RELIABILITY_EVALUATION_PLAN
    §3.3` cấm chia.

    `budget` THÊM Ở WAVE 2 và mặc định `None` để test cũ gọi bốn tham số vẫn
    chạy. Lượt Phase 5 đầu **không ghi số lượt API** — artifact không có
    `token`/`calls`, nên báo cáo phải ước lượng "20–34 lượt logic" mà không xác
    nhận được. Đó là lỗi của runner, và đây là chỗ trả nợ: một lượt đo không
    ghi được nó tiêu bao nhiêu thì không tái lập được chi phí.
    """
    import api_usage_log as AU
    import reliability_v2 as RV

    def dem(k: str) -> dict:
        co = [r for r in ket if r.get(k) is not None]
        return {"tu_so": sum(1 for r in co if r[k]), "mau_so": len(co),
                "chua_do": len(ket) - len(co)}

    om = [r["obligation_match"] for r in ket if r.get("obligation_match")]
    return {
        "khai": "TẬP DEV — được nhìn, hệ được sửa theo nó. KHÔNG phải số "
                "held-out của luận văn.",
        "N": len(ket), "N_planned": n, "hoan_tat": len(ket) == n and not dung_som,
        "dung_som": dung_som, "model": model,
        "G1_schema": dem("schema_pass"),
        "G2_semantic": dem("semantic_pass"),
        "A_executable": dem("executable"),
        "O_oracle": dem("oracle_pass"),
        "obligation_match": RV._gop_obligation_match(
            [{"obligation_match": m} for m in om]),
        "phan_bo_that_bai": _phan_bo(ket),
        "chi_phi": AU.bao_cao(model, budget),
    }


def _phan_bo(ket: list[dict]) -> dict[str, int]:
    ra: dict[str, int] = {}
    for r in ket:
        t = r.get("failure_layer")
        ten = "di_tron_duong" if t is None else f"lop_{t}"
        ra[ten] = ra.get(ten, 0) + 1
    return dict(sorted(ra.items(), key=lambda kv: -kv[1]))


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--out-dir", default=str(GEO / "dev-results"))
    args = p.parse_args()
    try:
        from dotenv import load_dotenv

        load_dotenv(BACKEND / ".env")
    except ImportError:
        pass
    try:
        return asyncio.run(_main(args))
    except DungSach as e:
        print(f"DỪNG: {e}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
