# -*- coding: utf-8 -*-
"""Sinh `PHASE7B_READINESS_REPORT.md` — ảnh chụp trạng thái. **0 API call.**

    python scripts/report_holdout_readiness.py            # in ra
    python scripts/report_holdout_readiness.py --md       # ghi báo cáo

─── VÌ SAO SINH RA CHỨ KHÔNG VIẾT TAY ────────────────────────────────────

Báo cáo này mang **băm** và **số đếm**. Viết tay thì nó đúng đúng một lần —
lần viết — rồi trôi ngay ở commit sau, và một báo cáo sẵn sàng nói sai về mức
sẵn sàng còn tệ hơn không có báo cáo. Mọi con số ở đây **dẫn từ nguồn**:
`app.main.CACHE_VERSION`, `runtime_identity`, `freeze_evaluation_candidate`,
`seal_geometry_holdout`, `holdout_coverage_matrix`.

Khác `PHASE7B_READINESS.md` — file ấy là **phân tích blocker** do người viết
(vì sao rào tồn tại, ba đường đi, cái giá từng đường). File này là **ảnh chụp
số**. Hai vai khác nhau, đừng gộp.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1]
GOC = BACKEND.parent
GEO = GOC / "docs" / "evaluation" / "geometry"
RA = GEO / "PHASE7B_READINESS_REPORT.md"

if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))


def _nap(ten: str):
    spec = importlib.util.spec_from_file_location(
        f"_rp_{ten}", Path(__file__).resolve().parent / f"{ten}.py")
    assert spec and spec.loader
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def _bam(p: Path) -> str:
    if not p.exists():
        return "THIẾU_FILE"
    return hashlib.sha256(
        p.read_text(encoding="utf-8").replace("\r\n", "\n").encode()).hexdigest()


def _chay(*lenh: str) -> str:
    try:
        return subprocess.run(lenh, cwd=GOC, capture_output=True, text=True,
                              check=True).stdout.strip()
    except Exception:  # noqa: BLE001
        return "unknown"


def thu_thap() -> dict:
    SH, MT = _nap("seal_geometry_holdout"), _nap("holdout_coverage_matrix")
    FZ = _nap("freeze_evaluation_candidate")
    from app.runtime_identity import runtime_identity

    rt = runtime_identity()
    pool_f = GEO / "holdout" / "pool.json"
    cases = (json.loads(pool_f.read_text(encoding="utf-8")).get("cases") or []
             if pool_f.exists() else [])
    m = MT.ma_tran(cases)

    theo_tt: dict[str, list[str]] = {}
    for c in cases:
        theo_tt.setdefault(c.get("status", "accepted"), []).append(c["case_id"])

    he_bam, he_so = FZ.measured_system_hash()
    kv = GEO / "expectations" / "holdout.json"
    return {
        "luc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "git_sha": _chay("git", "rev-parse", "HEAD"),
        "cay_sach": _chay("git", "status", "--porcelain") == "",
        "cache_version": rt["cache_version"],
        "skill_hash": rt["skills"]["tong"],
        "prompt_hash": rt["skills"]["grammar_card"],
        "measured_system_hash": he_bam, "measured_system_files": he_so,
        "metric_contract_hash": _bam(GEO / "PHASE7_METRIC_CONTRACT.md"),
        "capability_boundary_hash": _bam(GEO / "CAPABILITY_BOUNDARY.md"),
        "holdout_protocol_hash": _bam(GEO / "HOLDOUT_PROTOCOL.md"),
        "pool_hash": _bam(pool_f),
        "expectation_ton_tai": kv.exists(), "expectation_hash": _bam(kv),
        "seal_ton_tai": (GEO / "holdout" / "HOLDOUT_SEAL.json").exists(),
        "so_case": len(cases), "theo_trang_thai": theo_tt,
        "accepted": len(theo_tt.get("accepted", [])),
        "o_trong": m["o_trong"], "theo_o": m["theo_o"],
        "bang_o": m["bang_o"],
        "cases": cases,
        "k": SH.K_CHOT,
        "budget": (len(SH.BANG_O) * SH.K_CHOT * SH.LOGIC_MOI_LUOT,
                   len(SH.BANG_O) * SH.K_CHOT * SH.HTTP_MOI_LUOT),
    }


def blockers(d: dict) -> list[str]:
    b: list[str] = []
    if d["accepted"] < 40:
        b.append(f"POOL — {d['accepted']}/40 bài `accepted`. "
                 f"Thiếu **{40 - d['accepted']}** bài.")
    if d["o_trong"]:
        b.append(f"ĐỘ PHỦ — {len(d['o_trong'])}/20 ô trống: "
                 f"{' '.join(d['o_trong'])}")
    if not d["expectation_ton_tai"]:
        b.append("EXPECTATION — chưa có `expectations/holdout.json` "
                 "(chỉ soạn được SAU khi pool có bài accepted).")
    b.append("SEED — chưa có. Số nguyên do GVHD cấp; người đo chọn seed thì "
             "người đo chọn được cả tập.")
    b.append(f"NGÂN SÁCH — {d['budget'][0]} logic / {d['budget'][1]} HTTP "
             f"(k={d['k']}) chưa được duyệt.")
    if not d["cay_sach"]:
        b.append("CÂY LÀM VIỆC BẨN — niêm phong đòi cây sạch.")
    return b


def _md(d: dict) -> str:
    b = blockers(d)
    o = ["# PHASE 7B — BÁO CÁO SẴN SÀNG", "",
         "> Sinh bằng `scripts/report_holdout_readiness.py`. **0 API call.**",
         "> Mọi số dẫn từ nguồn — đừng sửa tay, chạy lại.",
         f"> Chụp lúc `{d['luc']}`.", "",
         "```", f"READY_FOR_PHASE7B:  {'YES' if not b else 'NO'}", "```", "",
         "---", "", "## 1. Environment", "", "```",
         f"git_sha                  : {d['git_sha']}",
         f"cây sạch                 : {'có' if d['cay_sach'] else 'KHÔNG'}",
         f"cache_version            : {d['cache_version']}",
         f"skill_hash               : {d['skill_hash']}",
         f"prompt_hash (grammar)    : {d['prompt_hash']}",
         f"measured_system_hash     : {d['measured_system_hash']}  "
         f"({d['measured_system_files']} file)",
         f"metric_contract_hash     : {d['metric_contract_hash']}",
         f"capability_boundary_hash : {d['capability_boundary_hash']}",
         f"holdout_protocol_hash    : {d['holdout_protocol_hash']}",
         f"pool_hash                : {d['pool_hash']}", "```", "",
         "⚠️ `git_sha` ở trên là **của lúc chụp**, không phải của HEAD hiện tại —",
         "commit kế tiếp làm nó cũ đi. **Chạy lại script ngay trước khi niêm",
         "phong**, đừng đọc bản cũ.", "",
         "⚠️ `runtime_doctor` **không** nằm ở đây: nó so **git SHA**, nên *mọi*",
         "commit — kể cả commit sửa tài liệu — làm nó FAIL lại. Nó là bước **áp",
         "chót** ngay trước `seal`, không phải một ô tick giữ mãi.", "",
         "---", "", "## 2. Dataset", "",
         f"**`accepted`: {d['accepted']}/40**", ""]

    o += ["| Trạng thái | Số bài | `case_id` |", "|---|--:|---|"]
    for tt, ds in sorted(d["theo_trang_thai"].items()):
        o.append(f"| `{tt}` | {len(ds)} | {', '.join(ds)} |")
    if not d["theo_trang_thai"]:
        o.append("| *(chưa có bài nào)* | 0 | — |")

    o += ["", "### Độ phủ 20 ô", "", "| Ô | Nghĩa vụ | Số bài | |",
          "|---|---|--:|---|"]
    for oo, (nv, mota) in d["bang_o"].items():
        n = len(d["theo_o"].get(oo, []))
        o.append(f"| **{oo}** | `{nv or '—'}` | {n} | "
                 f"{'✅' if n else '⛔'} {mota} |")

    o += ["", "### Bài bị loại / chờ phán", "",
          "| `case_id` | `status` | `reason` |", "|---|---|---|"]
    co = False
    for c in d["cases"]:
        if c.get("status", "accepted") != "accepted":
            co = True
            o.append(f"| `{c['case_id']}` | `{c['status']}` | "
                     f"{(c.get('reason') or '')[:190]} |")
    if not co:
        o.append("| *(không có)* | — | — |")

    o += ["", "---", "", "## 3. Metric — năm chỉ số đã đóng băng", "",
          "Định nghĩa ở `PHASE7_METRIC_CONTRACT §2`, đóng băng ở `§6` (Phase",
          "7A.2). **Chưa chỉ số nào có giá trị** — chúng chỉ sinh ra từ một lượt",
          "chạy thật, và lượt ấy chưa xảy ra.", "",
          "| | Chỉ số | Đơn vị | Trạng thái |", "|---|---|---|---|",
          "| ① | `served` | `x/k` mỗi đề | chưa đo |",
          "| ② | `oracle` | `x/k` · **ba trạng thái**, `None` ≠ `False` | chưa đo |",
          "| ③a | `construction_match` | `x/k'` · `k'` = số lượt **chấm được** | **chưa từng đo lần nào** |",
          "| ③b | `verification_match` | `x/k` · so **bằng đúng** | chưa đo |",
          "| ④ | `construction_validity` | 4 số rời, **không gộp** | chưa đo |",
          "| ⑤ | `stability` | `x/k` + **phân bố** | chưa đo · cần `k = 3` |", "",
          f"`k = {d['k']}` · ngân sách `{d['budget'][0]}` logic / "
          f"`{d['budget'][1]}` HTTP — chốt ở `HOLDOUT_K_FINAL.md`.", "",
          "⚠️ ③a **chưa từng được đo trong bất kỳ lượt nào**, kể cả DEV. Con số",
          "đầu tiên của nó phải đến từ một lượt chạy thật — không được điền bằng",
          "cách chấm lại artifact cũ rồi gọi đó là kết quả.", "",
          "---", "", "## 4. Expectation", "",
          f"- Tồn tại: **{'CÓ' if d['expectation_ton_tai'] else 'CHƯA'}**",
          f"- `expectation_hash`: `{d['expectation_hash']}`",
          f"- Con dấu `HOLDOUT_SEAL.json`: "
          f"**{'CÓ' if d['seal_ton_tai'] else 'CHƯA'}**", "",
          "Expectation chỉ soạn **sau** khi pool có bài `accepted` — soạn trước",
          "là soạn kỳ vọng cho những bài chưa biết có nhận được không.", "",
          "---", "", "## 5. Blockers", ""]
    o += [f"{i}. {x}" for i, x in enumerate(b, 1)] or ["*(không còn)*"]
    o += ["", "Phân tích từng rào — vì sao tồn tại, ba đường đi, cái giá từng",
          "đường: [`PHASE7B_READINESS.md`](PHASE7B_READINESS.md) và",
          "[`HOLDOUT_ACQUISITION_LOG.md`](HOLDOUT_ACQUISITION_LOG.md).", ""]
    return "\n".join(o) + "\n"


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--md", action="store_true", help="Ghi PHASE7B_READINESS_REPORT.md")
    a = p.parse_args()
    d = thu_thap()
    b = blockers(d)
    if a.md:
        RA.write_text(_md(d), encoding="utf-8")
        print(f"Đã ghi {RA}")
    print(f"READY_FOR_PHASE7B: {'YES' if not b else 'NO'}")
    print(f"accepted: {d['accepted']}/40 · ô trống: {len(d['o_trong'])}/20")
    for x in b:
        print("  ⛔", x)
    return 0 if not b else 1


if __name__ == "__main__":
    raise SystemExit(main())
