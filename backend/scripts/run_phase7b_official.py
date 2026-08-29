# -*- coding: utf-8 -*-
"""PHASE 7B — LƯỢT ĐO CHÍNH THỨC. **TIÊU QUOTA THẬT.**

    ALLOW_LIVE_AI=1 python scripts/run_phase7b_official.py          # chạy
    python scripts/run_phase7b_official.py --tien-kiem              # 0 call
    python scripts/run_phase7b_official.py --cham-lai               # 0 call

20 bài ĐÃ NIÊM PHONG × `k = 3` lượt độc lập. Trần 360 lượt logic / 480 HTTP.

─── "MỘT LƯỢT CHÍNH THỨC" NGHĨA LÀ GÌ ─────────────────────────────────────

Một lượt = 20 bài × 3 lần lặp, theo đúng hợp đồng metric/ngân sách/retry đã
đóng băng. Ba việc **không** phải là "chạy lại benchmark":

· retry HTTP theo policy đã đăng ký trước (timeout, 5xx, 429);
· TIẾP TỤC sau khi tiến trình chết — cùng `run_id`, cùng seed, cùng tập bài;
· chấm lại artifact đã ghi (`--cham-lai`, 0 call).

Ba việc **là** vi phạm: gọi lại một lượt ĐÃ HOÀN TẤT vì kết quả xấu; xoá hay
ghi đè output thô để thử lại; thêm retry sau khi thấy held-out trượt.

─── VÌ SAO TIẾP TỤC ĐƯỢC MÀ KHÔNG GỌI LẠI ────────────────────────────────

`measure_geometry_stability.mot_luot` ghi `{case_id}-lan{n}.json` **ngay sau
khi lượt ấy xong**, chứ không gom cuối buổi. Nên sự có mặt của file chính là
bằng chứng bền của một lượt đã hoàn tất, và bộ chạy chỉ cần BỎ QUA nó. Không
có bảng trạng thái thứ hai để mà lệch.

Hệ quả phải nói ra: file *có mặt* ⇒ lượt ấy **không bao giờ** được gọi lại
trong cùng `run_id`. Muốn đo lại thì phải niêm phong một tập khác, và nói ra
rằng đây là lượt khác.

─── VÌ SAO GỌI `run_pipeline` CHỨ KHÔNG GỌI `/api` ────────────────────────

Cache analyze khoá theo *text đã chuẩn hoá + CACHE_VERSION*. Đi qua HTTP thì
ba lần lặp của cùng một đề sẽ **sập vào một kết quả cached** — `k = 3` biến
thành `k = 1` mà không cổng nào kêu, và độ ổn định đo được sẽ là 3/3 với mọi
bài. Gọi thẳng `run_pipeline` thì **không có đường nào cho kết quả cũ quay
lại**; đó là bảo đảm mạnh hơn "dọn cache trước mỗi lượt".

─── CÁI FILE NÀY CỐ Ý *KHÔNG* LÀM ────────────────────────────────────────

Không sửa hệ được đo, không đổi kỳ vọng, không đổi seed, không rút lại, không
thêm retry. `_kiem_truoc_khi_chay` chạy TRƯỚC lời gọi model đầu tiên và từ
chối cả lượt nếu một mắt xích danh tính lệch.
"""
from __future__ import annotations

import argparse
import asyncio
import importlib.util
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1]
ROOT = BACKEND.parent
GEO = ROOT / "docs" / "evaluation" / "geometry"
sys.path.insert(0, str(BACKEND))
sys.path.insert(0, str(BACKEND / "scripts"))

K_CHOT = 3
#: Trần MỖI LƯỢT, dẫn từ call graph (analyze ≤2 · semantic_analyze 1 ·
#: semantic_program ≤3 = 6 logic; +đệm transient = 8 HTTP). Trần TỔNG là
#: 20 × 3 × (6, 8) = (360, 480) — đúng con số ở `HOLDOUT_BUDGET_APPROVAL.md`.
TRAN_LOGIC_MOI_LUOT, TRAN_HTTP_MOI_LUOT = 6, 8
RA = GEO / "phase7b-official"


class Dung(Exception):
    """Dừng có chủ đích, không phải sự cố."""


def _nap(ten: str, duong: Path):
    spec = importlib.util.spec_from_file_location(ten, duong)
    m = importlib.util.module_from_spec(spec)
    sys.modules[ten] = m
    spec.loader.exec_module(m)
    return m


M = _nap("measure_geometry_stability",
         BACKEND / "scripts" / "measure_geometry_stability.py")
SH = _nap("seal_geometry_holdout",
          BACKEND / "scripts" / "seal_geometry_holdout.py")
DEV = _nap("run_geometry_dev_evaluation",
           BACKEND / "scripts" / "run_geometry_dev_evaluation.py")


# ══ ① KIỂM DANH TÍNH TRƯỚC LỜI GỌI MODEL ĐẦU TIÊN ════════════════════════
def _kiem_truoc_khi_chay(cases: list[dict], seal: dict) -> list[str]:
    """Mọi mắt xích danh tính, kiểm TRƯỚC khi tiêu đồng quota nào.

    Kiểm sau thì đã muộn: quota đã tiêu, và một lượt chạy trên hệ đã đổi thì
    con số của nó không gắn với bản nào cả — không sửa được bằng cách nào
    ngoài chạy lại, mà chạy lại chính là thứ giao thức cấm.
    """
    loi: list[str] = []
    if SH._bam(cases) != seal.get("seal_hash"):
        loi.append("cases.json LỆCH con dấu")
    if seal.get("seed") != 82917341:
        loi.append(f"seed lệch: {seal.get('seed')}")
    if len(cases) != 20:
        loi.append(f"{len(cases)} bài, phải là 20")
    if len({c["slot"] for c in cases}) != 20:
        loi.append("không phủ đủ 20/20 ô")
    he, so = SH._bam_he_thong()
    if he != seal.get("measured_system_hash"):
        loi.append(f"HỆ ĐÃ ĐỔI sau khi niêm phong: {he[:12]}… "
                   f"≠ {str(seal.get('measured_system_hash'))[:12]}…")
    for ten, khoa in (("PHASE7_METRIC_CONTRACT.md", "metric_contract_hash"),
                      ("CAPABILITY_BOUNDARY.md", "capability_boundary_hash"),
                      ("expectations/holdout.json", "expectation_hash")):
        if SH._bam_tai_lieu(ten) != seal.get(khoa):
            loi.append(f"{ten} lệch con dấu ({khoa})")
    if seal.get("k") != K_CHOT:
        loi.append(f"k lệch: {seal.get('k')} ≠ {K_CHOT}")
    ns = seal.get("budget") or {}
    if (ns.get("logic"), ns.get("http")) != (360, 480):
        loi.append(f"ngân sách lệch: {ns}")
    import subprocess
    ban = subprocess.run(["git", "status", "--porcelain"], cwd=ROOT,
                         capture_output=True, text=True).stdout.strip()
    if ban:
        loi.append("CÂY LÀM VIỆC BẨN — artifact sẽ không truy ngược được "
                   f"commit ({len(ban.splitlines())} file)")
    return loi


def _danh_tinh_runtime() -> dict:
    from app.runtime_identity import runtime_identity
    from app.ai import gemini
    r = runtime_identity()
    return {"git_sha": r["git_sha"], "cache_version": r["cache_version"],
            "skill_hash": r["skills"]["tong"],
            "grammar_card": r["skills"]["grammar_card"],
            "model": gemini.MODEL}


# ══ ② BỘ CHẤM ORACLE THEO POOL ═══════════════════════════════════════════
_CASE_THEO_ID: dict[str, dict] = {}


def cham_oracle(case_id: str, fm: dict, hd=None):
    """Ba trạng thái, KHÔNG gộp: đạt · sai · không chấm được.

    `DEV.cham_oracle` trả `UNGRADED` khi hợp đồng không khai nghĩa vụ nào
    trùng khoá oracle của đề. Ép nó thành `False` là biến *"không chấm
    được"* thành *"mô hình sai"* — hai câu khác hẳn nhau khi đọc một
    benchmark, và cái nhầm ấy luôn nghiêng về phía làm hệ trông tệ hơn thật.
    """
    c = _CASE_THEO_ID[case_id]
    if not c.get("oracle_result"):
        return None, "ô tầng B — chấm bằng TỪ CHỐI TRUNG THỰC, không bằng oracle"
    r = DEV.cham_oracle(c, hd, fm)
    v = r["verdict"]
    return ({"PASS": True, "FAIL": False}.get(v), f"{v}: {r.get('ly_do') or r.get('lech')}")


# ══ ③ CHẠY ═══════════════════════════════════════════════════════════════
async def _chay(cases: list[dict], seal: dict, k: int) -> dict:
    from app.ai import gemini

    key = os.environ.get("GEMINI_API_KEY")
    if not key:
        raise Dung("Thiếu GEMINI_API_KEY trong backend/.env")

    tong_logic = tong_http = 0
    da_co = 0
    ket: list[dict] = []
    for i, c in enumerate(cases, 1):
        for lan in range(1, k + 1):
            f = RA / f"{c['case_id']}-lan{lan}.json"
            if f.exists():
                # TIẾP TỤC, không gọi lại. Sự có mặt của file là bằng chứng
                # bền của một lượt đã hoàn tất — xem docstring §tiếp tục.
                r = json.loads(f.read_text(encoding="utf-8"))["ban_ghi"]
                ket.append(r)
                tong_logic += r.get("logical_calls") or 0
                tong_http += r.get("http_requests") or 0
                da_co += 1
                continue
            if tong_logic + TRAN_LOGIC_MOI_LUOT > 360 or \
                    tong_http + TRAN_HTTP_MOI_LUOT > 480:
                raise Dung(f"CHẠM TRẦN TỔNG: {tong_logic} logic / {tong_http} "
                           "HTTP — dừng trước khi vượt, không dừng sau.")
            bai = {"id": c["case_id"], "de": c["problem_text"],
                   "oracle": c["case_id"]}
            r = await M.mot_luot(bai, lan, key)
            ket.append(r)
            tong_logic += r.get("logical_calls") or 0
            tong_http += r.get("http_requests") or 0
            print(f"{'✅' if r['servable'] else '❌'} [{i:>2}/{len(cases)}] "
                  f"{c['case_id']:<14} {c['slot']} lần {lan}/{k} · "
                  f"{r['do_tre_giay']:>5}s · {str(r['stage_reached']):<20} "
                  f"oracle={r['oracle_dat']} kiểm={r['verification_match']} "
                  f"dựng={r['construction_match']} · "
                  f"{tong_logic}/360 logic {tong_http}/480 HTTP", flush=True)
    return {"ket": ket, "tong_logic": tong_logic, "tong_http": tong_http,
            "da_co_san": da_co}


def _manifest(cases, seal, k, rid) -> dict:
    return {
        "OFFICIAL_RUN_ID": rid,
        "khai": "LƯỢT ĐO CHÍNH THỨC PHASE 7B. Append-only. Không ghi đè.",
        "seed": seal["seed"], "nguon_seed": seal["nguon_seed"],
        "seal_hash": seal["seal_hash"],
        "measured_system_hash": seal["measured_system_hash"],
        "expectation_hash": seal["expectation_hash"],
        "metric_contract_hash": seal["metric_contract_hash"],
        "capability_boundary_hash": seal["capability_boundary_hash"],
        "k": k, "budget": {"logic": 360, "http": 480},
        "case_ids": [c["case_id"] for c in cases],
        "runtime": _danh_tinh_runtime(),
        "bat_dau": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    }


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--tien-kiem", action="store_true",
                   help="Chỉ kiểm danh tính rồi thoát. 0 API call.")
    p.add_argument("--cham-lai", action="store_true",
                   help="Chấm lại artifact đã ghi. 0 API call.")
    p.add_argument("--k", type=int, default=K_CHOT)
    p.add_argument("--out-dir", default=None)
    a = p.parse_args()
    if a.out_dir:
        globals()["RA"] = Path(a.out_dir) if Path(a.out_dir).is_absolute() \
            else ROOT / a.out_dir

    seal = json.loads((GEO / "holdout" / "HOLDOUT_SEAL.json").read_text(encoding="utf-8"))
    cj = json.loads((GEO / "holdout" / "cases.json").read_text(encoding="utf-8"))
    cases = cj["cases"] if isinstance(cj, dict) else cj
    _CASE_THEO_ID.update({c["case_id"]: c for c in cases})

    loi = _kiem_truoc_khi_chay(cases, seal)
    print("── TIỀN KIỂM ──")
    for x in loi:
        print("  ⛔", x)
    print(f"  {'FAIL — KHÔNG CHẠY' if loi else 'PASS — 12/12 mắt xích khớp'}")
    if loi:
        return 2
    if a.tien_kiem:
        return 0

    # Nối bộ đo vào tập chính thức. `RUN_ID` để artifact tự khai nó thuộc
    # lượt nào; `TRAN_*` hạ về đúng hợp đồng đã đóng băng (6/8), thấp hơn
    # trần 8/12 mà Phase 6.7 dùng.
    rid = f"phase7b-official-{seal['seed']}"
    M.RA, M.RUN_ID = RA, rid
    # TẬP KỲ VỌNG phải trỏ `holdout`, không để nguyên `pilot`.
    #
    # `_ky_vong_cua` đọc `TAP_KY_VONG` ở cấp module và cache lại. Quên dòng
    # này thì mọi bài held-out ném `KeyError` (may) — hoặc tệ hơn, nếu id
    # tình cờ trùng thì nó chấm ③a/③b bằng kỳ vọng CỦA BÀI KHÁC và con số đi
    # thẳng vào báo cáo mà không cổng nào kêu.
    M.TAP_KY_VONG = "holdout"
    M._KY_VONG_CACHE.clear()
    M.TRAN_LOGIC, M.TRAN_HTTP = TRAN_LOGIC_MOI_LUOT, TRAN_HTTP_MOI_LUOT
    M.cham_oracle = cham_oracle
    M.BAI = [{"id": c["case_id"], "de": c["problem_text"],
              "oracle": c["case_id"]} for c in cases]

    if not a.cham_lai and os.environ.get("ALLOW_LIVE_AI") != "1":
        print(f"\nThiếu ALLOW_LIVE_AI=1 — {len(cases)}×{a.k} lượt TIÊU QUOTA "
              "THẬT (trần 360 logic / 480 HTTP).")
        return 2
    try:
        from dotenv import load_dotenv
        load_dotenv(BACKEND / ".env")
    except ImportError:
        pass

    RA.mkdir(parents=True, exist_ok=True)
    mf = RA / "RUN_MANIFEST.json"
    if not mf.exists():
        mf.write_text(json.dumps(_manifest(cases, seal, a.k, rid),
                                 ensure_ascii=False, indent=2) + "\n",
                      encoding="utf-8")
        print(f"\nRUN_MANIFEST ghi lần đầu · {rid}")
    else:
        cu = json.loads(mf.read_text(encoding="utf-8"))
        if cu["seal_hash"] != seal["seal_hash"] or cu["seed"] != seal["seed"]:
            print("⛔ MANIFEST CŨ khai một tập KHÁC — đây không phải cùng lượt.")
            return 2
        print(f"\nTIẾP TỤC lượt {cu['OFFICIAL_RUN_ID']} (bắt đầu {cu['bat_dau']})")

    try:
        r = asyncio.run(_chay(cases, seal, a.k))
    except Dung as e:
        print(f"DỪNG: {e}", file=sys.stderr)
        return 2
    print(f"\n── XONG · {len(r['ket'])} bản ghi "
          f"({r['da_co_san']} có sẵn, {len(r['ket']) - r['da_co_san']} mới) ──")
    print(f"   {r['tong_logic']}/360 logic · {r['tong_http']}/480 HTTP")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
