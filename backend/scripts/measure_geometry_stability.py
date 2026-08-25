# -*- coding: utf-8 -*-
"""PHASE 6.7 — ĐO ĐỘ ỔN ĐỊNH sinh chương trình hình học. **TIÊU QUOTA THẬT.**

    ALLOW_LIVE_AI=1 python scripts/measure_geometry_stability.py --k 5

Ba đề cố định × `k` lượt ĐỘC LẬP. **Không sửa gì, không vá gì giữa chừng** —
mục tiêu không phải tăng điểm mà là biết hệ hiện tại ổn định tới đâu.

─── VÌ SAO GỌI `run_pipeline` CHỨ KHÔNG GỌI HTTP ──────────────────────────

`run_pipeline` LÀ đường sản phẩm; `main.py` chỉ bọc thêm HTTP và cache. Gọi
thẳng nó có hai cái lợi cho một lượt ĐO:

· **Không có cache nào để dính** — mạnh hơn "dọn cache trước mỗi lượt", vì
  không có đường nào cho một kết quả cũ quay lại.
· **Bắt được `RequestContract` và `SemanticProgramSpec`** — hai thứ telemetry
  không phát ra, mà lại chính là "model output" cần ghi riêng.

Bọc `stage_semantic_analyze`/`stage_semantic_program` từ NGOÀI, cùng khuôn proxy
mà `run_geometry_dev_evaluation` đã dùng cho `load_skill`. Bọc để ĐỌC, không đổi
giá trị trả về — nếu đổi thì đo một hệ khác với hệ đang chạy.

─── ORACLE ĐỘC LẬP, VÀ VÌ SAO NÓ SO QUAN HỆ CHỨ KHÔNG SO TOẠ ĐỘ ──────────

Mô hình TỰ CHỌN hệ trục. Nên đáp án phải là thứ không đổi theo hệ trục:

    bài 1   `M` nằm trên đường `SA`                       — vị ngữ
    bài 2   thể tích = 12                                 — đại lượng (đề cho số)
    bài 3   `Q` là TRUNG ĐIỂM `AD`                        — quan hệ

Bài 3 tính tay: đáy cạnh 4, `S(0,0,5)` ⇒ `P(2,0,0) M(2,0,5/2) N(0,2,5/2)`;
pháp tuyến `(PMN) = (-5,-5,0)`; giao `z=0` cho phương `(-1,1,0)`; cắt `AD`
(`x=0`) tại `t=2` ⇒ `Q` là trung điểm `AD`. Tỉ lệ ấy đúng với MỌI hệ trục.
"""
from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
import time
from fractions import Fraction
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1]
ROOT = BACKEND.parent
sys.path.insert(0, str(BACKEND))

RA = ROOT / "docs" / "evaluation" / "geometry" / "stability-6.7"

#: Trần MỖI LƯỢT. Dẫn từ call graph như runner DEV: analyze ≤2 ·
#: semantic_analyze 1 · semantic_program ≤3 ⇒ 6, cộng đệm transient.
TRAN_LOGIC, TRAN_HTTP = 8, 12

BAI = [
    {
        "id": "1-trung-diem",
        "de": ("Cho hình chóp S.ABCD có đáy ABCD là hình vuông cạnh 2. Gọi M "
               "là trung điểm của cạnh SA. Hãy dựng điểm M và chỉ ra rằng M "
               "nằm trên đường thẳng SA."),
        "nghia_vu_mong_doi": ["point_on_line"],
        "oracle": "M_tren_SA",
    },
    {
        "id": "2-the-tich",
        "de": ("Cho hình chóp S.ABCD có đáy ABCD là hình vuông cạnh 3, SA "
               "vuông góc với mặt phẳng đáy và SA = 4. Tính thể tích khối "
               "chóp S.ABCD."),
        "nghia_vu_mong_doi": ["volume"],
        "oracle": "the_tich_12",
    },
    {
        "id": "3-pmn-giao-tuyen",
        "de": ("Cho hình chóp S.ABCD có đáy ABCD là hình vuông cạnh 4, SA "
               "vuông góc với mặt phẳng đáy và SA=5. Gọi M, N lần lượt là "
               "trung điểm của SB, SD; P là trung điểm của AB. Hãy dựng mặt "
               "phẳng (PMN), xác định giao tuyến d của hai mặt phẳng (PMN) và "
               "(ABCD), đồng thời xác định giao điểm Q=d∩AD."),
        "nghia_vu_mong_doi": ["point_on_line", "point_on_plane"],
        "oracle": "Q_trung_diem_AD",
    },
]


class Ghi:
    def __init__(self) -> None:
        self.su_kien: list[tuple[str, dict]] = []

    def emit(self, t: str, d: dict) -> None:
        self.su_kien.append((t, d))

    def lay(self, t: str) -> list[dict]:
        return [d for k, d in self.su_kien if k == t]


# ══ ORACLE — ĐỘC LẬP, so QUAN HỆ ═════════════════════════════════════════
def _v(x):
    """Giá trị trong `final_memory` đã serialize; đọc lại thành Fraction."""
    if isinstance(x, dict) and {"x", "y", "z"} <= set(x):
        return tuple(Fraction(str(x[k])) for k in ("x", "y", "z"))
    return None


def cham_oracle(ten: str, fm: dict) -> tuple[bool | None, str]:
    """Trả `(đạt, giải thích)`. `None` = KHÔNG CHẤM ĐƯỢC, khác hẳn `False`."""
    if not fm:
        return None, "không có final_memory"

    if ten == "the_tich_12":
        for k, val in fm.items():
            if isinstance(val, str):
                try:
                    if Fraction(val) == 12:
                        return True, f"{k} = 12"
                except (ValueError, ZeroDivisionError):
                    continue
        so = {k: v for k, v in fm.items() if isinstance(v, str)}
        return False, f"không biến nào bằng 12 · số đã đo: {so}"

    if ten == "M_tren_SA":
        # `M` là trung điểm `SA` ⇒ M - S = A - M. So QUAN HỆ, không so toạ độ.
        diem = {k: p for k, p in ((k, _v(v)) for k, v in fm.items()) if p}
        for ten_m, m in diem.items():
            for ten_s, s in diem.items():
                for ten_a, a in diem.items():
                    if len({ten_m, ten_s, ten_a}) < 3:
                        continue
                    if all(m[i] - s[i] == a[i] - m[i] for i in range(3)):
                        return True, f"{ten_m} là trung điểm {ten_s}{ten_a}"
        return False, f"không cặp nào có trung điểm · điểm: {sorted(diem)}"

    if ten == "Q_trung_diem_AD":
        diem = {k: p for k, p in ((k, _v(v)) for k, v in fm.items()) if p}
        for tq in [k for k in diem if k.upper().startswith("Q")]:
            q = diem[tq]
            for ta in [k for k in diem if k.upper().rstrip("_0123456789") == "A"]:
                for td in [k for k in diem if k.upper().rstrip("_0123456789") == "D"]:
                    a, d = diem[ta], diem[td]
                    if all(2 * q[i] == a[i] + d[i] for i in range(3)):
                        return True, f"{tq} là trung điểm {ta}{td}"
        return False, f"Q không là trung điểm AD · điểm: {sorted(diem)}"

    return None, f"oracle lạ: {ten}"


# ══ MỘT LƯỢT ═════════════════════════════════════════════════════════════
async def mot_luot(bai: dict, lan: int, api_key: str) -> dict:
    from app.ai import gemini, pipeline, telemetry

    bat = {}
    goc_an, goc_ct = pipeline.stage_semantic_analyze, pipeline.stage_semantic_program

    async def an(*a, **k):
        r = await goc_an(*a, **k)
        bat["contract"] = r[0]
        return r

    async def ct(*a, **k):
        r = await goc_ct(*a, **k)
        bat["spec"] = r[0]
        return r

    pipeline.stage_semantic_analyze, pipeline.stage_semantic_program = an, ct
    gemini.set_budget(gemini.ApiBudget(max_api_calls=TRAN_HTTP,
                                       max_logical_calls=TRAN_LOGIC))
    telemetry.reset_usage()
    ghi = Ghi()
    t0 = time.time()
    try:
        env = await pipeline.run_pipeline(bai["de"], api_key, observer=ghi,
                                          semantic_route="serve")
    except Exception as e:  # noqa: BLE001 — lượt đo, muốn thấy cả sự cố
        env = {"status": "EXCEPTION", "reason": f"{type(e).__name__}: {e}"}
    finally:
        gemini.set_budget(None)
        pipeline.stage_semantic_analyze = goc_an
        pipeline.stage_semantic_program = goc_ct

    sr = (ghi.lay("semantic_route") or [{}])[-1]
    hd = bat.get("contract")
    kinds = sorted({ob.kind for ob in hd.obligations}) if hd else []
    mong = sorted(bai["nghia_vu_mong_doi"])
    fm = sr.get("final_memory") or {}
    dat, vi_sao = cham_oracle(bai["oracle"], fm)

    ban_ghi = {
        "case_id": bai["id"], "lan": lan,
        "do_tre_giay": round(time.time() - t0, 1),
        "stage_reached": sr.get("stage_reached"),
        "executable": sr.get("executable"),
        "servable": sr.get("servable"),
        "error_code": sr.get("error_code"),
        "failure_category": sr.get("failure_category"),
        "reason": sr.get("reason"),
        "details": sr.get("details"),
        "so_nghia_vu": len(hd.obligations) if hd else 0,
        "nghia_vu_kinds": kinds,
        "nghia_vu_mong_doi": mong,
        # KHỚP HOÀN TOÀN, không "có giao nhau": đề hỏi hai loại mà hợp đồng chỉ
        # khai một thì nửa còn lại không ai kiểm.
        "obligation_match": kinds == mong,
        "oracle_dat": dat, "oracle_vi_sao": vi_sao,
        "envelope_status": env.get("status"),
        "envelope_id": env.get("simulation_id"),
        "co_scene3d": bool(env.get("scene3d")),
        "so_doi_tuong_canh": len((env.get("scene3d") or {}).get("objects") or []),
        "so_buoc_phat_lai": len((env.get("scene3d") or {}).get("events") or []),
        "so_lan_thu_sinh": len(ghi.lay("semantic_program_attempt")),
        "thu_that_bai": [d.get("message", "")[:400]
                         for d in ghi.lay("semantic_program_attempt")
                         if not d.get("ok")],
    }
    # MODEL OUTPUT ghi RIÊNG — hợp đồng và chương trình là thứ phải đọc lại được
    # khi phân loại, và không telemetry nào phát chúng ra.
    RA.mkdir(parents=True, exist_ok=True)
    (RA / f"{bai['id']}-lan{lan}.json").write_text(json.dumps({
        "ban_ghi": ban_ghi,
        "request_contract": hd.model_dump(mode="json") if hd else None,
        "generated_program": (bat["spec"].model_dump(mode="json")
                              if bat.get("spec") else None),
        "final_memory": fm,
    }, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return ban_ghi


async def _main(k: int) -> int:
    if os.environ.get("ALLOW_LIVE_AI") != "1":
        print(f"Thiếu ALLOW_LIVE_AI=1 — lượt này tiêu quota thật "
              f"({len(BAI)}×{k} lượt, trần {TRAN_LOGIC} logic mỗi lượt).")
        return 2
    try:
        from dotenv import load_dotenv

        load_dotenv(BACKEND / ".env")
    except ImportError:
        pass
    key = os.environ.get("GEMINI_API_KEY")
    if not key:
        print("Thiếu GEMINI_API_KEY")
        return 2

    from app.ai import gemini
    from app.runtime_identity import runtime_identity

    rt = runtime_identity()
    print(f"sha={rt['git_sha'][:12]} cache={rt['cache_version']} "
          f"model={gemini.MODEL} skill={rt['skills']['tong'][:8]} "
          f"card={rt['skills']['grammar_card'][:8]}")
    print(f"{len(BAI)} đề × {k} lượt · KHÔNG sửa gì giữa chừng\n")

    tat_ca: list[dict] = []
    for bai in BAI:
        for lan in range(1, k + 1):
            r = await mot_luot(bai, lan, key)
            tat_ca.append(r)
            dau = "✅" if r["servable"] else "❌"
            print(f"{dau} {bai['id']:<18} lần {lan}/{k} · {r['do_tre_giay']:>5}s "
                  f"· {str(r['stage_reached']):<21} nv={r['so_nghia_vu']} "
                  f"khớp={r['obligation_match']} oracle={r['oracle_dat']}")
        print()

    RA.mkdir(parents=True, exist_ok=True)
    (RA / "tong_hop.json").write_text(
        json.dumps({"k": k, "runs": tat_ca}, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8")

    print("── TỔNG HỢP ──")
    for bai in BAI:
        r = [x for x in tat_ca if x["case_id"] == bai["id"]]
        sv = sum(1 for x in r if x["servable"])
        ora = sum(1 for x in r if x["oracle_dat"] is True)
        om = sum(1 for x in r if x["obligation_match"])
        print(f"  {bai['id']:<18} served {sv}/{k} · oracle {ora}/{k} · "
              f"obligation_match {om}/{k}")
    return 0


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--k", type=int, default=5)
    raise SystemExit(asyncio.run(_main(p.parse_args().k)))
