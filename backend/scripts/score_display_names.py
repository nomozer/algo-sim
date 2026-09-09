# -*- coding: utf-8 -*-
"""CHẤM TÊN HIỂN THỊ của 12 đại lượng, 7 ca dương. 0 lượt gọi model.

─── VÌ SAO PHẢI CÓ MỘT BỘ CHẤM RIÊNG ───────────────────────────────────────

`DISPLAY_NAME_PASS = 10/12` được bàn giao qua ba wave mà **chưa lần nào có phép
đo tự động** — nó là một con số đọc bằng mắt trên ảnh chụp. Một con số như thế
không nói được *đại lượng nào* hỏng, và không đỏ lên khi có cái thứ ba hỏng.

Bộ chấm này ghi **từng đại lượng** với đủ bốn thứ mà `§3` đòi: kiểu ngữ nghĩa
thật, tên biến do chương trình đặt, nhãn hiện tại, và phán quyết. Bốn thứ ấy
tách nhau có chủ đích — nhãn sai vì *thiếu ánh xạ KIỂU* và nhãn sai vì *mô hình
đặt tên biến xấu* là hai bệnh khác nhau, và gộp lại thì không phân biệt được.

─── ĐIỀU BỘ CHẤM NÀY KHÔNG LÀM ─────────────────────────────────────────────

Nó **không** chấm đáp số. Giá trị vẫn do `doi_chieu_ket_qua_cuoi.py` và oracle
đối chiếu — một bộ đo vừa chấm tên vừa chấm số thì một bản vá tên có thể làm
đổi phán quyết về số mà không ai thấy.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

BE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BE))
sys.path.insert(0, str(BE / "scripts"))
GOC = BE.parent

FIXTURES = (GOC / "docs" / "evaluation" / "geometry"
            / "product-ui-result-rendering" / "fixtures")
OUT_MAC_DINH = GOC / "docs" / "evaluation" / "geometry" / "display-name-final-polish"

#: Chuỗi TỐ CÁO — có mặt trong nhãn là hỏng, không cần biết ngữ cảnh.
#:
#: `«đối tượng»` và `Đối tượng` là lối rơi cuối của `display_names`: chúng chỉ
#: xuất hiện khi một KIỂU không có trong bảng danh từ. Đó là lý do chúng đáng
#: bị chặn thẳng thay vì chấm bằng cảm nhận — chúng là **dấu vết của một lỗ
#: trong bảng**, không phải một cách diễn đạt kém.
DAU_HIEU_PLACEHOLDER = ("«đối tượng»", "Đối tượng", "đối tượng»",
                        "undefined", "null", "None")

#: Định danh KỸ THUẬT không được lọt lên bề mặt học sinh (`ARCHITECTURE_MAP §2`).
#: Dẫn từ chính `MemoryType` để bảng này không phải bản chép tay thứ hai.
def _kieu_ky_thuat() -> tuple[str, ...]:
    import typing

    from app.simulation.semantic_program.contract import MemoryType

    return tuple(typing.get_args(MemoryType))


def _doc_fixture(ref: str | None = None) -> list[dict[str, Any]]:
    """Fixture trên đĩa, hoặc **tại một ref git**.

    ⚠️ `--from-git` tồn tại để nền ĐO LẠI ĐƯỢC. Nếu nền chỉ là một tệp đã ghi
    trước khi vá thì nó không còn kiểm được — ai cũng có thể sửa nó, và không
    có gì buộc nó khớp với mã lúc ấy. Đọc từ git thì nền dựng lại được từ đúng
    commit, bao nhiêu lần cũng thế.
    """
    import subprocess

    ra: list[dict[str, Any]] = []
    for p in sorted(FIXTURES.glob("p*.json")):
        if ref is None:
            ra.append(json.loads(p.read_text(encoding="utf-8")))
            continue
        r = subprocess.run(
            ["git", "show", f"{ref}:{p.relative_to(GOC).as_posix()}"],
            cwd=GOC, capture_output=True, text=True, encoding="utf-8")
        if r.returncode == 0:
            ra.append(json.loads(r.stdout))
    return ra


def _kieu_theo_ten(fx: dict) -> dict[str, str]:
    """`{id của vật: kiểu}` — tra qua `depends`, KHÔNG qua khớp chuỗi nhãn.

    Bản đầu khớp nội dung trong guillemet với `label` của vật; nó trả `None`
    cho **mọi** hàng, vì thứ nằm trong guillemet là `reference` (cách gọi
    ngắn), không phải `label`. Hai trường khác nhau có chủ đích — xem
    `display_names.ten_hien_thi`. `depends` là liên kết CÓ CẤU TRÚC, nên nó
    đúng cả khi cách hành văn đổi.
    """
    return {str(o.get("id")): str(o.get("type"))
            for o in (fx["envelope"].get("scene3d") or {}).get("objects", [])}


def _ten_bien_trong_chuong_trinh(case_id: str) -> dict[str, str]:
    """`{tên biến: kiểu}` đọc từ CHƯƠNG TRÌNH đã đóng băng của lượt đo.

    Tên biến là thứ MÔ HÌNH đặt (`dien_tich_E`, `S_thiet_dien`…). Nó được ghi
    lại để chứng minh phán quyết **không** dựa vào chính tả của nó (`§4`).
    """
    run = (GOC / "docs" / "evaluation" / "geometry" / "thesis-final-acceptance"
           / "thesis-final-20260908T160224Z")
    ra: dict[str, str] = {}
    for f in ("stage_a_first_attempt.json", "stage_b_recovery.json"):
        for c in json.loads((run / f).read_text(encoding="utf-8"))["cases"]:
            if c["id"] != case_id or not c.get("chuong_trinh"):
                continue
            for d in c["chuong_trinh"].get("memory_declarations", []):
                ra[d["name"]] = d.get("type", "?")
    return ra


def cham(ref: str | None = None) -> dict[str, Any]:
    ky_thuat = _kieu_ky_thuat()
    hang: list[dict[str, Any]] = []

    for fx in _doc_fixture(ref):
        cid = fx["case_id"]
        kieu_cua = _kieu_theo_ten(fx)
        bien = _ten_bien_trong_chuong_trinh(cid)
        objs = (fx["envelope"].get("scene3d") or {}).get("objects", [])

        for o in objs:
            if o.get("render") != "readout":
                continue
            nhan = str(o.get("label") or "")

            # Vật mà đại lượng này NÓI VỀ — đọc từ `depends` (liên kết có cấu
            # trúc), không từ chuỗi trong guillemet.
            phu_thuoc = [d for d in (o.get("depends") or [])]
            noi_ve = phu_thuoc[0] if phu_thuoc else None
            kieu_that = kieu_cua.get(noi_ve or "")
            trong_ngoac = re.search(r"«([^»]*)»", nhan)

            do = [d for d in DAU_HIEU_PLACEHOLDER if d in nhan]
            lo_ky_thuat = [k for k in ky_thuat if k in nhan]
            dat = not do and not lo_ky_thuat and bool(nhan.strip())

            hang.append({
                "case_id": cid,
                "obligation_kind": o.get("producer"),
                "kieu_doi_tuong_that": kieu_that,
                "vat_duoc_nhac": noi_ve,
                "cum_trong_guillemet": trong_ngoac.group(1) if trong_ngoac else None,
                "ten_bien_chuong_trinh_dat": o.get("id"),
                "moi_ten_bien_cua_ca": sorted(bien),
                "nhan_hien_tai": nhan,
                "gia_tri_hien_thi": o.get("value"),
                "placeholder_tim_thay": do,
                "dinh_danh_ky_thuat_lo": lo_ky_thuat,
                "PASS": dat,
            })

    dat = sum(1 for h in hang if h["PASS"])
    return {
        "khai": "Chấm TÊN HIỂN THỊ. KHÔNG chấm đáp số — giá trị do "
                "`doi_chieu_ket_qua_cuoi.py` và oracle đối chiếu.",
        "QUANTITIES": len(hang),
        "DISPLAY_NAME_PASS": f"{dat}/{len(hang)}",
        "PLACEHOLDER_DISPLAY_NAMES": sum(
            1 for h in hang if h["placeholder_tim_thay"]),
        "TECHNICAL_IDENTIFIERS_LEAKED": sum(
            1 for h in hang if h["dinh_danh_ky_thuat_lo"]),
        "FAIL_CASES": sorted({h["case_id"] for h in hang if not h["PASS"]}),
        "quantities": hang,
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=None)
    ap.add_argument("--label", default="BASELINE")
    ap.add_argument("--from-git", default=None,
                    help="chấm fixture TẠI một ref git — để nền đo lại được")
    a = ap.parse_args()

    kq = cham(getattr(a, "from_git", None))
    kq["label"] = a.label
    kq["fixture_source"] = a.from_git or "working tree"
    out = Path(a.out) if a.out else OUT_MAC_DINH / f"{a.label}.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(kq, ensure_ascii=False, indent=1), encoding="utf-8")

    for h in kq["quantities"]:
        print(f"  {'✓' if h['PASS'] else '✗'} {h['case_id']:36s} "
              f"{str(h['kieu_doi_tuong_that']):13s} {h['nhan_hien_tai']}"
              f"  = {h['gia_tri_hien_thi']}")
    print(f"\n  DISPLAY_NAME_PASS = {kq['DISPLAY_NAME_PASS']}")
    print(f"  PLACEHOLDER_DISPLAY_NAMES = {kq['PLACEHOLDER_DISPLAY_NAMES']}")
    print(f"  ghi: {out.relative_to(GOC).as_posix()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
