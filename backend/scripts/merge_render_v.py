# -*- coding: utf-8 -*-
"""Gộp `renderer_V` của PHA B vào artifact lượt đo. **0 API call.**

    pha A (backend, tốn quota)  →  envelopes/ + PROVENANCE.json
    pha B (trình duyệt, 0 call) →  renderer_v.json
    file này                    →  cập nhật v2.renderer_V + reliability_v2

VÌ SAO TÁCH: pha B chạy được nhiều lần mà không tiêu quota. Bắt nó ghi thẳng
vào `sealed_cases.json` là cho một script trình duyệt quyền sửa artifact của
lượt đo — và một lần chạy nhầm thì không lấy lại được.

BỐN CỔNG TỪ CHỐI, tất cả đều là điều kiện PASS trong task:

  1. thiếu `PROVENANCE.json`      → lô envelope không tự khai được nguồn
  2. provenance lệch artifact     → gộp kết quả của lượt ĐO KHÁC vào đây
  3. `faultcheck_red != true`     → guard chưa chứng minh đỏ được ⇒ vô giá trị
  4. thiếu viewport               → soát không đủ bề rộng

Cổng 3 là cái dễ bị bỏ qua nhất và cũng là cái đắt nhất khi bỏ qua: bài học đã
lặp HAI LẦN trong wave này là *`status=ok` không phải bằng chứng*.

    python backend/scripts/merge_render_v.py --dir docs/evaluation/.../results
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from reliability_v2 import chi_so_case, tong_hop  # noqa: E402

#: Bốn bề rộng đã chốt ở các bản nghiệm thu trước — đổi danh sách này là đổi
#: nghĩa của `V`, nên nó nằm ở đây chứ không rải trong script trình duyệt.
VIEWPORT_BAT_BUOC = ("desktop_1920x1080", "laptop_1536x864",
                     "school_1366x768", "tablet_768x900")


class TuChoi(Exception):
    """Từ chối gộp. Gộp bừa còn tệ hơn không gộp: nó tạo ra một con số."""


def kiem_provenance(prov: dict, bao_cao: dict) -> None:
    """Lô envelope có ĐÚNG là của lượt đo này không."""
    for khoa in ("measured_system_candidate", "sealed_fingerprint", "chay_luc"):
        if prov.get(khoa) != bao_cao.get(khoa):
            raise TuChoi(
                f"provenance lệch ở '{khoa}': envelope khai "
                f"{prov.get(khoa)!r}, artifact khai {bao_cao.get(khoa)!r}. "
                "Đây là hai lượt đo khác nhau."
            )


def kiem_bao_cao_pha_b(pha_b: dict) -> None:
    if pha_b.get("faultcheck_red") is not True:
        raise TuChoi(
            "`faultcheck_red` không phải true — guard chưa được chứng minh là "
            "đỏ được. Một bản soát chưa từng đỏ không chứng minh gì cả."
        )
    thieu = [v for v in VIEWPORT_BAT_BUOC if v not in (pha_b.get("viewports") or [])]
    if thieu:
        raise TuChoi(f"thiếu viewport {thieu} — soát không đủ bề rộng")


def gop(thu_muc: Path) -> dict:
    cases_p = thu_muc / "sealed_cases.json"
    sum_p = thu_muc / "sealed_summary.json"
    prov_p = thu_muc / "envelopes" / "PROVENANCE.json"
    phab_p = thu_muc / "renderer_v.json"

    for p in (cases_p, sum_p, phab_p):
        if not p.exists():
            raise TuChoi(f"thiếu {p.name}")
    if not prov_p.exists():
        raise TuChoi(
            "thiếu envelopes/PROVENANCE.json — lô envelope không tự khai được "
            "nguồn gốc, nên không phân biệt được với một thư mục chép tay."
        )

    cases = json.loads(cases_p.read_text(encoding="utf-8"))
    bao_cao = json.loads(sum_p.read_text(encoding="utf-8"))
    prov = json.loads(prov_p.read_text(encoding="utf-8"))
    pha_b = json.loads(phab_p.read_text(encoding="utf-8"))

    kiem_provenance(prov, bao_cao)
    kiem_bao_cao_pha_b(pha_b)

    ket = pha_b.get("ket_qua") or {}
    da_gop = 0
    for r in cases:
        cid = r.get("case_id")
        v2 = r.get("v2") or {}
        # Chỉ điền cho ca CÓ envelope. Ca không phát được thì `V` là None —
        # mẫu số của `V` là số ca có `B`, không phải N.
        if cid not in (prov.get("case_ids") or []):
            continue
        render_ok = ket.get(cid)
        if render_ok is None:
            continue
        r["v2"] = chi_so_case(
            source_id=v2.get("source_id"),
            semantic=r.get("semantic"),
            cham=r.get("cham"),
            replay_ok=v2.get("replay_R"),
            render_ok=bool(render_ok),
        )
        da_gop += 1

    bao_cao["reliability_v2"] = tong_hop([r["v2"] for r in cases if r.get("v2")])
    bao_cao["reliability_v2"]["pha_b"] = {
        "da_gop": da_gop,
        "so_envelope": prov.get("so_envelope"),
        "faultcheck_red": True,
        "viewports": pha_b.get("viewports"),
    }

    cases_p.write_text(json.dumps(cases, ensure_ascii=False, indent=2) + "\n",
                       encoding="utf-8")
    sum_p.write_text(json.dumps(bao_cao, ensure_ascii=False, indent=2) + "\n",
                     encoding="utf-8")
    return {"da_gop": da_gop, "V": bao_cao["reliability_v2"]["V_renderer"]}


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--dir", required=True, help="thư mục artifact của lượt đo")
    a = p.parse_args()
    try:
        r = gop(Path(a.dir))
    except TuChoi as e:
        print(f"TỪ CHỐI GỘP: {e}", file=sys.stderr)
        return 2
    print(f"Đã gộp {r['da_gop']} case · V = {r['V']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
