# -*- coding: utf-8 -*-
"""§3 + §8 — replay TRƯỚC/SAU cho `POINT_COORDINATE_SOURCE_INVARIANT`.

`APPLICATION_LLM_CALLS = 0`. Chạy được ở CẢ HAI trạng thái mã, nên số "trước"
và số "sau" đến từ **cùng một bộ đo** — khác bộ đo thì hai cột không so được.

    .venv/Scripts/python.exe scripts/replay_point_coordinate_invariant.py --nhan TRUOC
    .venv/Scripts/python.exe scripts/replay_point_coordinate_invariant.py --nhan SAU

Ca dùng lại **nguyên xi** ca lõm của
`NONCONVEX_POLYHEDRON_MODEL_DISCOVERABILITY` — cùng `PROBLEM_HASH`, cùng
`GOLD_HASH` — nên hai wave nói về cùng một vật.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1]
for _p in (str(BACKEND), str(BACKEND / "scripts")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from app.main import CACHE_VERSION  # noqa: E402
from app.simulation.semantic_program.analyze_contract import (  # noqa: E402
    gan_bat_bien_nguon,
)
from app.simulation.geometry.radical import display, is_exact_number  # noqa: E402
from app.simulation.semantic_program.contract import (  # noqa: E402
    SemanticProgramSpec,
)
from app.simulation.semantic_program.request_contract import (  # noqa: E402
    RequestContract,
)
from app.simulation.semantic_program.route import verify_and_compile  # noqa: E402

from gold_nonconvex_polyhedron import (  # noqa: E402
    GOLD, GOLD_HASH, PROBLEM_HASH, PROBLEM_TEXT, REQUEST_CONTRACT_GOLD, WITNESS,
)

RA = (BACKEND.parent / "docs" / "evaluation" / "geometry"
      / "point-coordinate-source-invariant")

#: Hợp đồng KIỂU LƯỢT LIVE — ba fact **kể chuyện**, không fact nào mang toạ độ.
#: Chép nguyên từ `raw_theo_tang.semantic_analyze` của artifact lượt live.
CT_KE_CHUYEN = {
    "problem_text": PROBLEM_TEXT,
    "input_facts": [
        {"fact_id": "khoi_chop", "label": "Hình dạng khối",
         "values": ["S.ABCDE là khối chóp"], "provenance": "confirmed"},
        {"fact_id": "day_ngu_giac_lom", "label": "Hình dạng đáy",
         "values": ["ABCDE là một ngũ giác lõm"], "provenance": "confirmed"},
        {"fact_id": "day_trong_mp_z0", "label": "Vị trí mặt đáy",
         "values": ["Đáy ABCDE nằm trong mặt phẳng z = 0"],
         "provenance": "confirmed"},
    ],
    "obligations": REQUEST_CONTRACT_GOLD["obligations"],
}


def _doi_diem(ten: str, xyz: list, **truong) -> dict:
    """Gold, đổi đúng một điểm. Mọi thứ khác giữ nguyên."""
    g = copy.deepcopy(GOLD)
    for m in g["memory_declarations"]:
        if m["name"] == ten:
            m["initial_value"] = xyz
            m.update(truong)
    return g


def _xuat_xu_chung(spec: dict, fid: str) -> dict:
    """Mọi điểm trỏ về CÙNG một fact — đúng như lượt live đã làm."""
    s = copy.deepcopy(spec)
    for m in s["memory_declarations"]:
        if m.get("type") == "point3":
            m.pop("model_assumption", None)
            m["source_fact_id"] = fid
    return s


def _bang_gia_dinh(spec: dict) -> dict:
    """Bỏ hẳn `source_fact_id`, thay bằng `model_assumption` — kênh tự do hệ
    trục. Đề ĐÃ cho toạ độ, nên lối này không được phép cứu một toạ độ sai."""
    s = copy.deepcopy(spec)
    for m in s["memory_declarations"]:
        if m.get("type") == "point3":
            m.pop("source_fact_id", None)
            m["model_assumption"] = "Chọn hệ trục Oxyz như trên."
    return s


#: Khi bật, gỡ đúng bất biến toạ độ khỏi hợp đồng — tái hiện trạng thái TRƯỚC
#: bản vá bằng CHÍNH bộ đo này. Hai cột "trước"/"sau" phải đến từ một nhạc cụ;
#: khác nhạc cụ thì chúng không so được, và bản đầu của replay này đã vấp đúng
#: chỗ ấy (nó dựng `RequestContract` thẳng nên không thấy bất biến nào).
BO_BAT_BIEN = False


def _hop_dong(ct: dict) -> RequestContract:
    """Hợp đồng đi qua **đúng biên đóng băng của sản phẩm**.

    ⚠️ Bản đầu của replay này dựng `RequestContract` THẲNG, nên nó không thấy
    bất biến nào và báo *"bản vá không đổi gì"* cho một bản vá đúng — đúng lớp
    lỗi *"một sửa chữa không nằm trên đường chạy thật"*. Chép danh sách bộ phát
    sang đây cũng sai: bản thứ hai sẽ quên bộ phát tiếp theo. Nên gọi CHUNG
    `gan_bat_bien_nguon`, thẩm quyền mà `build_request_contract` cũng gọi.
    """
    hd = gan_bat_bien_nguon(RequestContract.model_validate(ct), PROBLEM_TEXT)
    if BO_BAT_BIEN:
        from app.simulation.semantic_program.point_coordinate import (
            KIND, KIND_CHUA_GIAI,
        )
        hd = hd.model_copy(update={"source_invariants": tuple(
            b for b in (hd.source_invariants or ())
            if b.kind not in (KIND, KIND_CHUA_GIAI))})
    return hd


def chay(spec: dict, ct: dict) -> dict:
    kq = verify_and_compile(_hop_dong(ct),
                            SemanticProgramSpec.model_validate(spec))
    gt = {k: display(x) for k, x in (kq.final_memory or {}).items()
          if is_exact_number(x)}
    return {
        "servable": kq.servable,
        "stage_reached": kq.stage_reached,
        "error_code": kq.error_code,
        "the_tich": gt.get(WITNESS),
        "source_invariant_stats": dict(kq.source_invariant_stats or {}),
        "unjustified_literals": list(kq.unjustified_literals),
        "weak_kinds": list(kq.weak_kinds),
        "envelope_status": (kq.envelope or {}).get("status"),
        "details": [d[:180] for d in (kq.details or [])[:3]],
    }


def bang() -> dict:
    """Bốn ô của §3, cộng ba ca tái hiện thêm."""
    dung = GOLD
    B_sai = _doi_diem("B", [99, 7, 0])
    D_het_lom = _doi_diem("D", [3, 3, 0])

    o: dict[str, dict] = {}
    # ── BỐN Ô của bảng §3 ────────────────────────────────────────────────
    for nhan_ct, ct in (("fact_ke_chuyen", CT_KE_CHUYEN),
                        ("fact_co_toa_do", REQUEST_CONTRACT_GOLD)):
        fid = ("day_trong_mp_z0" if ct is CT_KE_CHUYEN else None)
        for nhan_sp, sp in (("toa_do_dung", dung), ("B_thanh_99_7_0", B_sai)):
            s = _xuat_xu_chung(sp, fid) if fid else sp
            o[f"{nhan_ct}__{nhan_sp}"] = chay(s, ct)

    # ── BA CA TÁI HIỆN THÊM ─────────────────────────────────────────────
    o["D_3_3_0__mat_phan_lom"] = chay(D_het_lom, REQUEST_CONTRACT_GOLD)
    # `source_fact_id` trỏ tới một fact CÓ THẬT nhưng không chứa toạ độ điểm ấy.
    o["xuat_xu_TRO_NHAM_fact"] = chay(
        _doi_diem("B", [99, 7, 0], source_fact_id="dinh_A"),
        REQUEST_CONTRACT_GOLD)
    # Khai sai bằng `model_assumption` trong khi đề ĐÃ cho toạ độ.
    o["model_assumption_che_toa_do_sai"] = chay(
        _bang_gia_dinh(B_sai), REQUEST_CONTRACT_GOLD)

    # ── CA PHẢI GIỮ NGUYÊN ──────────────────────────────────────────────
    o["BAO_TOAN__gold_fact_co_toa_do"] = o["fact_co_toa_do__toa_do_dung"]
    o["BAO_TOAN__gold_fact_ke_chuyen"] = o["fact_ke_chuyen__toa_do_dung"]
    return o


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--nhan", required=True, help="TRUOC | SAU")
    p.add_argument("--bo-bat-bien", action="store_true",
                   help="gỡ bất biến toạ độ — tái hiện trạng thái TRƯỚC vá")
    a = p.parse_args()

    global BO_BAT_BIEN
    BO_BAT_BIEN = bool(a.bo_bat_bien)
    o = bang()
    ra = {
        "khai": "Replay TAT DINH, 0 luot goi model.",
        "wave": "POINT_COORDINATE_SOURCE_INVARIANT",
        "nhan": a.nhan,
        "luc": datetime.now(timezone.utc).isoformat(),
        "cache_version": CACHE_VERSION,
        "bat_bien_toa_do_da_go": BO_BAT_BIEN,
        "ca": {"problem_sha256": PROBLEM_HASH, "gold_sha256": GOLD_HASH,
               "nguon": "gold_nonconvex_polyhedron (dung lai NGUYEN XI)"},
        "o": o,
        "TOM_TAT": {
            k: f"{'served' if v['servable'] else v['stage_reached']}"
               f" · V={v['the_tich']}"
            for k, v in o.items() if not k.startswith("BAO_TOAN")},
    }
    ra["sha256"] = hashlib.sha256(
        json.dumps(ra, ensure_ascii=False, sort_keys=True).encode("utf-8")
    ).hexdigest()

    RA.mkdir(parents=True, exist_ok=True)
    f = RA / f"REPLAY_{a.nhan}.json"
    if f.exists():
        print(f"⚠️  {f.name} da ton tai — KHONG ghi de artifact luot cu.")
    else:
        f.write_text(json.dumps(ra, ensure_ascii=False, indent=2),
                     encoding="utf-8")
        print("→", f)
    print(json.dumps(ra["TOM_TAT"], ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
