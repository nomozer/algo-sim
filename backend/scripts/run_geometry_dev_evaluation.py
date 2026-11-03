# -*- coding: utf-8 -*-
"""Runner DEV hình học — đo AI có sinh được Geometry Program đúng không.

    đề (văn xuôi) → analyze → RequestContract → sinh IR → validate
                  → interpreter → checker → ORACLE ĐỘC LẬP

Runner SEALED của miền Tin học (`run_sealed_evaluation.py`, mang con dấu lượt SEALED #1) đã gỡ ở repo-cleanup;
bằng chứng của lượt ấy giữ nguyên trong `docs/evaluation/semantic-benchmark/`.

⚠️ ĐÂY LÀ TẬP DEV, KHÔNG phải benchmark. Nó **được nhìn**, và hệ **được sửa**
theo nó. Số của nó không bao giờ là số held-out của luận văn — held-out phải do
custodian chọn bằng seed của GVHD.

## Vì sao phải ép skill từ phía harness

`pipeline.stage_semantic_program` **hardcode** `load_skill("semantic_program")`
(`pipeline.py:483`) — prompt của miền Tin học. Không file nào trong `app/` tham
chiếu `geometry_program_generator.md`.

Nên runner **bọc `load_skill` từ ngoài**, cùng khuôn proxy runner SEALED (đã gỡ) từng dùng. Đây là quyết định có chủ đích, không phải mẹo:

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
#: semantic_program ≤3 ⇒ 6/case; cộng đệm transient ⇒ 8 HTTP/case.
#: KHÔNG dùng trần 13/case của miền Tin học: runner này không chạy classify,
#: simulate hay one-route recovery, nên mượn trần ấy là xin thừa quota.
#:
#: Nhân theo SỐ BÀI chứ không viết cứng: tập held-out có 20 bài, và một con số
#: cứng `60` sẽ làm lượt ấy đứt giữa chừng ở bài thứ mười — nhìn hệt như hệ
#: hỏng. n=10 ra đúng 60/80, tức trần đã duyệt cho DEV không đổi một đơn vị.
TRAN_LOGIC_MOI_CASE = 6
TRAN_HTTP_MOI_CASE = 8

HOLDOUT = GEO / "holdout" / "cases.json"
HOLDOUT_SEAL = GEO / "holdout" / "HOLDOUT_SEAL.json"


class DungSach(Exception):
    """Dừng có chủ đích, không phải sự cố."""


def _bat_buoc_live(n: int) -> None:
    if os.environ.get("ALLOW_LIVE_AI") != "1":
        raise DungSach(
            "Thiếu ALLOW_LIVE_AI=1. Lượt này TIÊU QUOTA THẬT — "
            f"trần {TRAN_LOGIC_MOI_CASE * n} lượt logic / "
            f"{TRAN_HTTP_MOI_CASE * n} lần thử HTTP cho {n} bài."
        )


def _kiem_con_dau(cases: list[dict]) -> None:
    """Chạy held-out CHỈ khi tập đề *và* hệ thống vẫn đúng bản đã niêm phong.

    Hai điều kiện, hai lý do khác nhau:

    · `seal_hash` — tập đề không bị đổi sau khi đã thấy kết quả lượt trước.
    · `measured_system_hash` — hệ không bị sửa **giữa lúc niêm phong và lúc
      chạy**. Đây là chỗ biến lời hứa *"không sửa hợp đồng theo từng bài"*
      thành thứ đối chiếu được: sửa xong rồi chạy thì runner từ chối, thay vì
      để con số đi vào báo cáo mang tiếng "held-out".

    Lối thoát duy nhất là **niêm phong lại** — tức khai ra rằng đây là lượt
    khác, trên một hệ khác. Đúng như vậy thì tập ấy đã thành DEV.
    """
    if not HOLDOUT_SEAL.exists():
        raise DungSach(
            f"Không có con dấu {HOLDOUT_SEAL}. Không có con dấu trong lịch sử "
            "thì không chứng minh được tập đề không bị sửa sau khi thấy kết quả."
        )
    seal = json.loads(HOLDOUT_SEAL.read_text(encoding="utf-8"))

    import seal_geometry_holdout as SH

    if (bam := SH._bam(cases)) != seal.get("seal_hash"):
        raise DungSach(
            f"TẬP ĐỀ LỆCH CON DẤU: {bam[:16]}… ≠ {str(seal.get('seal_hash'))[:16]}…"
        )
    hien, so_file = SH._bam_he_thong()
    if hien != seal.get("measured_system_hash"):
        raise DungSach(
            "HỆ ĐÃ ĐỔI SAU KHI NIÊM PHONG — "
            f"{hien[:16]}… ({so_file} file) ≠ "
            f"{str(seal.get('measured_system_hash'))[:16]}… "
            f"({seal.get('measured_system_files')} file).\n"
            "Chạy tiếp thì con số KHÔNG còn là held-out: hệ đã được sửa sau khi "
            "tập đề được chốt. Muốn đo bản mới thì niêm phong lại tập KHÁC."
        )
    print(f"CON DẤU KHỚP · seed {seal.get('seed')} ({seal.get('nguon_seed')}) "
          f"· niêm phong {seal.get('niem_phong_luc')}")


def _nap_oracle():
    spec = importlib.util.spec_from_file_location("geometry_oracle", ORACLE_PY)
    mod = importlib.util.module_from_spec(spec)
    sys.modules["geometry_oracle"] = mod
    spec.loader.exec_module(mod)
    return mod


# ── chấm bằng ORACLE ĐỘC LẬP ──────────────────────────────────────────────
_MAU_DOAN = __import__("re").compile(r"(?<![A-Za-z])([A-Z])([A-Z])(?![A-Za-z])")


def _thang_do(fm: dict, contract) -> "Fraction | None":
    """Thang mà CHƯƠNG TRÌNH đã chọn cho ký hiệu tự do của đề, hoặc `None`.

    ─── VÌ SAO CẦN, ĐO ĐƯỢC 2026-08-29 ───────────────────────────────────

    `hp_a11_027` được phục vụ với `distance = 12` trong khi oracle mong
    `12/25`, và bộ chấm gọi đó là *"hệ nhận một diễn giải SAI"* — cáo buộc
    nặng nhất có thể. Đọc trạng thái cuối thì thấy chương trình ĐÚNG:
    `A(-9,0,0) B(16,0,0)` ⇒ AB = 25; `S(0,0,12)` ⇒ SA = 15 = 3·25/5;
    SA² + SB² = 625 = AB² (vuông tại S); d(S,(ABC)) = 12. Nó chọn thang
    `a = 25` — thang nhỏ nhất làm cả `a` lẫn `3a/5` nguyên.

    `12/25` là giá trị khi **chuẩn hoá a = 1**, một quy ước sống trong
    `phep_chuyen` của BỘ ĐO chứ không có trong đề. Đề để `a` tự do, và
    prompt bảo mô hình tự chọn hệ trục — nên nó cũng tự chọn thang.

    Cả **5/5** ô đo lường của pool (A11×2, A12, A14×2) đều có `a` tự do, nên
    so giá trị tuyệt đối là phép so KHÔNG HỢP LỆ với tất cả: nó chấm *mô
    hình có tình cờ chọn a = 1 không*, không chấm hình học.

    Cách suy thang: đề khai một dữ kiện mà GIÁ TRỊ là ký hiệu trần (`'a'`),
    và `fact_id` của nó gọi tên đoạn (`ab_length`). Độ dài đoạn ấy trong bộ
    nhớ chương trình chính là thang. Không suy ra được ⇒ `None` ⇒ KHÔNG CHẤM
    ĐƯỢC, không phải sai.
    """
    from fractions import Fraction

    for f in (getattr(contract, "input_facts", None) or []):
        gt = [str(v).strip() for v in (getattr(f, "values", None) or [])]
        if len(gt) != 1 or len(gt[0]) != 1 or not gt[0].isalpha():
            continue                      # chỉ nhận ký hiệu TRẦN, vd `a`
        m = _MAU_DOAN.search(str(getattr(f, "fact_id", "")).upper())
        if not m:
            continue
        p1, p2 = fm.get(m.group(1)), fm.get(m.group(2))
        if p1 is None or p2 is None:
            continue
        try:
            d2 = (p2 - p1).dot(p2 - p1)
            r = Fraction(d2).limit_denominator(10**9)
            # Độ dài phải HỮU TỈ, nếu không thang không biểu diễn được.
            for cand in (Fraction(int(r.numerator ** 0.5 + 0.5),
                                  int(r.denominator ** 0.5 + 0.5)),):
                if cand * cand == r:
                    return cand
        except Exception:  # noqa: BLE001
            continue
    return None


def _co_thang_tu_do(contract) -> bool:
    """Đề có để một ký hiệu độ dài TỰ DO không (`AB = a`)?

    Chỉ khi CÓ thì so giá trị tuyệt đối mới vô nghĩa. Đề cố định số (*"cạnh
    bằng 2"*) vẫn so tuyệt đối được, và một lệch ở đó là SAI THẬT — không
    được nới thành "không chấm được".
    """
    for f in (getattr(contract, "input_facts", None) or []):
        gt = [str(v).strip() for v in (getattr(f, "values", None) or [])]
        if len(gt) == 1 and len(gt[0]) == 1 and gt[0].isalpha():
            return True
    return False


def _bool_hoac_nguyen(x):
    """`"true"`/`"false"` (chuỗi) → `bool`. Giữ nguyên mọi thứ khác.

    `pool.oracle_result` sinh từ dòng `ĐÁP ÁN:` của gói chép, nên quan hệ nằm
    ở đó dưới dạng CHUỖI. Không chuẩn hoá thì nhánh boolean không bao giờ
    chạy — xem khối chú thích trong `cham_oracle`.
    """
    if isinstance(x, str) and x.strip().lower() in ("true", "false"):
        return x.strip().lower() == "true"
    return x


def _CHECKER_QUAN_HE() -> set[str]:
    from app.simulation.semantic_program.coverage_gate import _QUAN_HE_HINH_HOC
    return set(_QUAN_HE_HINH_HOC)


def _cham_bang_checker(kind: str, fm: dict, ob, ten_da_hoa_giai=None):
    """`None` ⇒ thoả · `True`/chuỗi ⇒ vi phạm · `False` ⇒ KHÔNG chấm được.

    ─── THẨM QUYỀN VỀ TÊN, KHÔNG HOÀ GIẢI LẦN THỨ TÁM (V3 §1) ────────────

    Bản trước tự gọi `khop_ky_hieu`. Ở V3 điều đó chấm oan `hp_a04_011` hai
    lượt: hợp đồng gọi mặt phẳng `(SMN)`, bộ nhớ gọi `SMN`, `khop_ky_hieu`
    không bóc được ngoặc — trong khi C₁a giải đúng bằng lưới TOPOLOGY (vật nào
    dựng từ {S, M, N}), và C₂ của hệ đã kiểm `parallel(AC)` ĐẠT.

    Nay hỏi `resolved_names` do route phát ra. `khop_ky_hieu` chỉ còn là lưới
    DỰ PHÒNG cho artifact cũ chưa có trường ấy — không phải nguồn thứ hai.
    """
    from app.simulation.semantic_program.domain_profile import khop_ky_hieu
    from app.simulation.semantic_program.geometry_obligations import (
        GEOMETRY_CHECKERS,
    )
    fn = GEOMETRY_CHECKERS.get(kind)
    if fn is None:
        return False
    try:
        snap = dict(fm)
        ten_can = [getattr(ob, "container", None), getattr(ob, "witness", None)]
        ten_can += [v for v in (getattr(ob, "params", None) or {}).values()
                    if isinstance(v, str)]
        for ten in ten_can:
            if not ten or ten in snap:
                continue
            thay = (ten_da_hoa_giai or {}).get(ten)
            if thay is None:
                thay = khop_ky_hieu(ten, set(snap))
            if thay is not None and thay in snap:
                snap[ten] = snap[thay]
        msg = fn(snap, ob)
    except Exception:  # noqa: BLE001 — lượt đo, không được ném ra ngoài
        return False
    if msg is None:
        return None
    import re as _re
    if _re.search(r"không hợp lệ|thiếu|không tìm thấy|chưa có", str(msg), _re.I):
        return False                      # không chấm được ≠ sai
    return str(msg)


def cham_oracle(case: dict, contract, final_memory: dict | None,
                ten_da_hoa_giai: dict | None = None) -> dict[str, Any]:
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
    #: "Không chấm được" phải là hạng RIÊNG. Gộp vào `lech` là biến một giới
    #: hạn của bộ đo thành một cáo buộc về mô hình — đã xảy ra ba lần.
    khong_cham: list[str] = []
    for kind in cham_duoc:
        ob = obls[kind]
        may = final_memory.get(ob.witness) if ob.witness else None
        de = _bool_hoac_nguyen(mong[kind])
        # ─── NGHĨA VỤ QUAN HỆ HỎI CHECKER, KHÔNG SO GIÁ TRỊ ─────────────────
        #
        # Đo được 2026-08-29 (xác nhận postfix): `pool.oracle_result` lưu quan
        # hệ dưới dạng CHUỖI `"true"`, nên `isinstance(de, bool)` là False và
        # nhánh số học chạy `Fraction("true")` ⇒ luôn *"không so được"*. Mọi
        # nghĩa vụ `parallel`/`perpendicular`/`point_on_*`/`coplanar` vì thế
        # KHÔNG BAO GIỜ chấm đúng được — 9/14 ô tầng A của `BANG_O`.
        #
        # Sửa đúng tầng: quan hệ được chứng minh bằng **checker server-owned**
        # chạy lại tính chất từ trạng thái cuối, quy ước `None` ⇒ thoả. So
        # `final_memory[witness]` với một hằng là đọc nhầm hợp đồng ngay từ
        # đầu — witness của quan hệ là ĐỐI TƯỢNG THỨ HAI, không phải kết quả.
        loi_ck = (_cham_bang_checker(kind, final_memory, ob, ten_da_hoa_giai)
                  if isinstance(de, bool) and kind in _CHECKER_QUAN_HE()
                  else False)
        if loi_ck is not False:
            # Checker chấm được ⇒ nó là nguồn sự thật. `None` ⇒ thoả.
            thoa = loi_ck is None
            if thoa is not de:
                lech.append(f"{kind}: checker nói {thoa}, đề mong {de}")
        elif isinstance(de, bool):
            # RƠI VỀ so boolean khi checker không chấm được. Giữ đường cũ cho
            # chương trình thật sự khai một boolean vào witness — bỏ nó đi là
            # đổi hợp đồng, không phải sửa lỗi.
            # Quan hệ: checker server-owned đã trả `None` khi thoả. Ở đây chỉ
            # đối chiếu kỳ vọng của đề với việc chương trình có khẳng định nó.
            if bool(may) != de:
                lech.append(f"{kind}: máy={may!r}, đề mong {de!r}")
        else:
            try:
                if may is None:
                    lech.append(f"{kind}: máy={may!r}, đề mong {de!r}")
                elif Fraction(str(may)) != Fraction(str(de)):
                    # BẤT BIẾN THANG trước khi kết luận SAI. Xem `_thang_do`.
                    bac = {"distance": 1, "volume": 3}.get(kind, 0)
                    s = _thang_do(final_memory, contract) if bac else None
                    if s and Fraction(str(may)) / s ** bac == Fraction(str(de)):
                        pass                       # đúng, chỉ khác thang
                    elif bac and s is None and _co_thang_tu_do(contract):
                        khong_cham.append(
                            f"{kind}: máy={may!r}, đề mong {de!r} ở thang "
                            "a=1 — thang chương trình chọn không suy ra được")
                    else:
                        lech.append(f"{kind}: máy={may!r}, đề mong {de!r}")
            except (ValueError, ZeroDivisionError, TypeError):
                lech.append(f"{kind}: không so được máy={may!r} với {de!r}")
    if lech:
        return {"verdict": "FAIL", "lech": lech, "khong_cham": khong_cham,
                "da_cham": cham_duoc}
    if khong_cham:
        return {"verdict": "UNGRADED", "khong_cham": khong_cham,
                "ly_do": "; ".join(khong_cham)[:200], "da_cham": cham_duoc}
    return {"verdict": "PASS", "lech": [], "da_cham": cham_duoc}


def _hop_dong_ra_json(contract) -> dict[str, Any]:
    """`RequestContract` → JSON quan trắc. KHÔNG có tầng chấm nào đọc nó.

    Ghi ĐỦ hai thứ mà chẩn đoán cần và PHASE 5 lượt 2 không có:

      · `facts` kèm `fact_id` — để đối chiếu với `source_fact_id` trong IR.
        Kèm luôn `provenance`/`unproven_values` vì P1 phân biệt "đề có thật" với
        "`analyze` tự khai", và hai thứ ấy dẫn tới hai kết luận khác nhau.
      · `obligations` kèm `container` + `witness` — tên THẬT mà C₁a đối chiếu.
        Không có nó thì "witness lệch tên" mãi là suy đoán.

    `contract is None` không tới đây được (đường gọi đã chặn), nhưng hợp đồng
    RỖNG thì tới — và phải ghi ra `{"facts": [], "obligations": []}` chứ không
    phải `None`: "đề không cho dữ kiện nào" là một quan sát, khác hẳn "không
    ghi lại được".
    """
    return {
        "facts": [
            {
                "fact_id": f.fact_id,
                "label": f.label,
                "values": list(f.values),
                "provenance": f.provenance,
                "unproven_values": list(f.unproven_values),
            }
            for f in contract.input_facts
        ],
        "obligations": [
            {
                "kind": o.kind,
                "container": o.container,
                "witness": o.witness,
                "params": dict(o.params),
            }
            for o in contract.obligations
        ],
    }


async def chay_mot_case(*_a, **_kw):
    raise DungSach('LLM_ONLY dev evaluation runner retired in Hybrid cutover')


def build_retired_summary(n: int = 0) -> dict[str, Any]:
    from app.ai import gemini

    return tong_ket([], n, "LLM_ONLY_RETIRED", gemini.MODEL)


def tong_ket(ket: list[dict], n: int, dung_som: str | None, model: str,
             budget=None, ghi=None, held_out: bool = False) -> dict:
    """ĐẾM THÔ, không phần trăm — mẫu số 10 < 20, `RELIABILITY_EVALUATION_PLAN
    §3.3` cấm chia. (Tập held-out có N=20 nên **được** chia; phép chia ấy thuộc
    về báo cáo, không thuộc về đây — runner chỉ đếm.)

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
        "khai": ("TẬP HELD-OUT đã niêm phong — con dấu và băm hệ thống đều đã "
                 "đối chiếu trước khi chạy. Chạy MỘT LƯỢT."
                 if held_out else
                 "TẬP DEV — được nhìn, hệ được sửa theo nó. KHÔNG phải số "
                 "held-out của luận văn."),
        "held_out": held_out,
        "N": len(ket), "N_planned": n, "hoan_tat": len(ket) == n and not dung_som,
        "dung_som": dung_som, "model": model,
        "G1_schema": dem("schema_pass"),
        "G2_semantic": dem("semantic_pass"),
        "A_executable": dem("executable"),
        "O_oracle": dem("oracle_pass"),
        "obligation_match": RV._gop_obligation_match(
            [{"obligation_match": m} for m in om]),
        "phan_bo_that_bai": _phan_bo(ket),
        # `ghi` PHẢI truyền vào, không được bỏ. Lượt Phase 5 (2026-08-25) gọi
        # `bao_cao(model, budget)` thiếu tham số thứ ba, nên `do_tre` cấp lượt
        # in ra `0s` trong khi độ trễ thật là 639s. Dữ liệu không mất — `do_tre`
        # từng bài vẫn đủ — nhưng con số SAI in ra màn hình lúc chạy là thứ dễ
        # bị chép lại nhất.
        "chi_phi": AU.bao_cao(model, budget, ghi),
        "neo": neo_kho_ma(),
    }


def neo_kho_ma() -> dict[str, Any]:
    """Artifact phải TỰ NÓI nó đo bản mã nào. Trước bản này thì không.

    Thiếu khối này, `geometry_dev_results.json` chỉ có điểm số và không có cách
    nào buộc điểm ấy vào một commit — người đọc sau ba tháng không tái lập được,
    và cũng không biết cây có bẩn lúc chạy hay không.

    ─── VÌ SAO GHI HAI PHẠM VI BẨN, KHÔNG CHỌN MỘT ──────────────────────────

    `bẩn` có hai nghĩa và chúng KHÔNG trùng nhau:

      · `dirty_toan_kho`     — mọi thứ `git status` thấy. Bao gồm cả wave khác
                               đang chạy song song, `docs/`, artifact tự sinh.
      · `dirty_he_duoc_do`   — chỉ `MEASURED_SYSTEM_PATHS`. Đây mới là thứ
                               quyết định phép đo có tái lập được không.

    `evidence.mjs` đã chốt nguyên tắc ấy từ trước và viết thẳng lý do:
    *"sửa một file `docs/` rồi đo thì phép đo vẫn tái lập được, nên gọi nó là
    bẩn sẽ làm cảnh báo mất giá trị và người ta thôi đọc"*. Còn
    `freeze_evaluation_candidate.cay_lam_viec_sach` lại soi TOÀN KHO — hai chỗ
    trong cùng kho nói hai nghĩa khác nhau cho cùng một chữ.

    Runner **không đứng về phe nào**: nó ghi cả hai con số và để người đọc
    artifact tự phán. Chọn phe ở đây là sửa một cổng trong lúc chính cổng ấy
    đang chặn mình — dù lập luận có đúng, thời điểm cũng làm nó thành động cơ.
    """
    import freeze_evaluation_candidate as FZ
    from app.main import CACHE_VERSION

    toan = [d for d in FZ._git("status", "--porcelain").splitlines() if d.strip()]
    he_do = [
        d for d in toan
        if any(d[3:].strip().startswith(p) for p in FZ.MEASURED_SYSTEM_PATHS)
    ]
    bam, so_file = FZ.measured_system_hash()
    return {
        "commit": FZ._git("rev-parse", "HEAD"),
        "commit_ngan": FZ._git("rev-parse", "--short", "HEAD"),
        "nhanh": FZ._git("rev-parse", "--abbrev-ref", "HEAD"),
        "cache_version": CACHE_VERSION,
        "measured_system_hash": bam,
        "measured_system_so_file": so_file,
        "dirty_toan_kho": [d[3:].strip() for d in toan],
        "dirty_he_duoc_do": [d[3:].strip() for d in he_do],
        "sach_toan_kho": not toan,
        "sach_he_duoc_do": not he_do,
        "khai": "Điểm số trong artifact này CHỈ có nghĩa với `measured_system_hash` "
                "ở trên. Cây bẩn ngoài hệ được đo không làm hỏng tính tái lập; "
                "cây bẩn TRONG hệ được đo thì có.",
    }


def _phan_bo(ket: list[dict]) -> dict[str, int]:
    ra: dict[str, int] = {}
    for r in ket:
        t = r.get("failure_layer")
        ten = "di_tron_duong" if t is None else f"lop_{t}"
        ra[ten] = ra.get(ten, 0) + 1
    return dict(sorted(ra.items(), key=lambda kv: -kv[1]))
