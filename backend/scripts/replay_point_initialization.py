# -*- coding: utf-8 -*-
"""Replay `e2`/`e6` của A/B `ab-v1-20260905T164514Z`. **0 lượt gọi model.**

    `docs/POINT_INITIALIZATION_CONTRACT_ALIGNMENT.md`, 2026-09-06.

Ba bản cho mỗi ca, chạy qua **đúng đường sản phẩm**:

    goc        — raw candidate NGUYÊN VĂN của mô hình
    delta_1    — CHỈ đổi `at` → `initial_value` ở khai báo `point3`;
                 giữ nguyên toạ độ, tên, `source_fact_id` và mọi câu lệnh
    delta_2    — delta_1 + gắn `source_fact_id` cho những điểm còn thiếu,
                 CHỈ khi RequestContract thật sự có mục ấy

`delta_2` không phải "sửa cho đậu": nó là phép đo **cổng kế tiếp**. Một lỗi
biến mất chỉ chứng minh delta xử lý được lỗi ấy — cổng sau bác vì lý do gì thì
phải ghi riêng, không gộp vào cùng một kết luận.

Artifact gốc của mô hình **không bị đụng**; mọi bản dựng ở đây ghi vào thư mục
của wave.
"""
from __future__ import annotations

import copy
import json
import sys
from pathlib import Path
from typing import Any

GOC = Path(__file__).resolve().parents[1]
if str(GOC) not in sys.path:
    sys.path.insert(0, str(GOC))

from app.ai import pipeline  # noqa: E402
from app.simulation.semantic_program.obligations import Obligation  # noqa: E402
from app.simulation.semantic_program.request_contract import (  # noqa: E402
    RequestContract,
)
from app.simulation.semantic_program.route import verify_and_compile  # noqa: E402
from app.simulation.semantic_program.validator import (  # noqa: E402
    validate_semantic_program,
)

AB = (GOC.parent / "docs" / "evaluation" / "geometry" /
      "operation-affordance-ab-v1" / "ab_ab-v1-20260905T164514Z.json")
RA = GOC.parent / "docs" / "evaluation" / "geometry" / \
    "point-initialization-replay-v1"


def _nguon(cid: str) -> tuple[dict, RequestContract]:
    d = json.loads(AB.read_text(encoding="utf-8"))
    r = {x["case_id"]: x for x in d["ket_qua"]}[cid]
    rc = r["request_contract"]
    hd = RequestContract(
        problem_text=rc["problem_text"], input_facts=rc["input_facts"],
        obligations=tuple(Obligation(**o) for o in rc["obligations"]))
    return json.loads(r["arms"]["B"]["raw_candidate"]), hd


def delta_1(raw: dict) -> tuple[dict, list[str]]:
    """`at` → `initial_value` ở khai báo `point3`. Không đụng gì khác."""
    p, ghi = copy.deepcopy(raw), []
    for i, d in enumerate(p.get("memory_declarations", [])):
        if isinstance(d, dict) and "at" in d:
            d["initial_value"] = d.pop("at")
            ghi.append(f"memory_declarations[{i}].at → .initial_value "
                       f"({d['name']})")
    return p, ghi


#: Quy kết xuất xứ cho `delta_2` — TƯỜNG MINH, kèm căn cứ, không dò chuỗi.
#:
#: ⚠️ Bản đầu dò tự động: *"lấy mục nào có tên điểm trong nhãn"*. Với `e2` nó
#: chọn `z_tren_day_x` cho `X`, vì nhãn *"Điểm Z nằm trên đường tròn đáy tâm
#: X"* có chữ `X`. Mục ấy nói về **Z**, không nói `X` đặt ở đâu — một khớp
#: GIẢ cho ra kết quả đúng vì lý do sai. Đúng thứ luật *"chỉ gắn khi fact thực
#: sự hỗ trợ đối tượng"* cấm. Nên bảng này viết tay VÀ mang căn cứ, và mỗi
#: dòng phải đọc được như một lời biện minh.
_XUAT_XU: dict[str, dict[str, tuple[str, str, str]]] = {
    "e2": {
        # (fact_id, model_assumption, căn cứ)
        "X": ("tru_co_tru_xy",
              "X là một đầu trục, đặt tại gốc toạ độ",
              "Mục `tru_co_tru_xy` — *'Hình trụ có trục là đoạn thẳng XY'* — "
              "là mục GIỚI THIỆU X. Toạ độ (0,0,0) là một lựa chọn HỆ QUY "
              "CHIẾU, nên nó đi kèm `model_assumption`, đúng khuôn mà chính "
              "mô hình đã dùng cho Y và Z."),
    },
    "e6": {},   # mô hình đã gắn đủ xuất xứ; không cần delta nào thêm
}


def delta_2(raw: dict, hd: RequestContract, cid: str) -> tuple[dict, list[str]]:
    """delta_1 + xuất xứ cho điểm còn thiếu — theo bảng TƯỜNG MINH ở trên.

    Không có dòng trong bảng ⇒ để nguyên và để grounding bác. Cổng nào bác thì
    ghi riêng cổng ấy; gộp chúng lại là mất đúng phần thông tin cần dùng.
    """
    p, ghi = delta_1(raw)
    quy = _XUAT_XU.get(cid, {})
    co = {f.fact_id for f in hd.input_facts}
    for i, d in enumerate(p.get("memory_declarations", [])):
        if not (isinstance(d, dict) and d.get("type") == "point3"):
            continue
        if d.get("source_fact_id") or d.get("initial_value") is None:
            continue
        ten = d["name"]
        if ten not in quy:
            ghi.append(f"({ten}: không có quy kết nào — để nguyên, "
                       f"grounding sẽ bác)")
            continue
        fid, gt, can_cu = quy[ten]
        if fid not in co:
            raise SystemExit(
                f"{cid}: quy kết cho {ten} trỏ mục '{fid}' KHÔNG có trong "
                f"RequestContract — bảng `_XUAT_XU` đã trôi.")
        d["source_fact_id"] = fid
        d["model_assumption"] = gt
        ghi.append(f"memory_declarations[{i}] ({ten}): source_fact_id="
                   f"'{fid}' + model_assumption. CĂN CỨ: {can_cu}")
    return p, ghi


def chay(nhan: str, spec_json: dict, hd: RequestContract) -> dict[str, Any]:
    ra: dict[str, Any] = {"ban": nhan}
    val = validate_semantic_program(spec_json)
    ra["validator_ok"] = val.ok
    if not val.ok:
        ra.update(tang="validator", loi=str(val.error)[:700],
                  servable=False, exact=None, postconditions=None,
                  scene3d=None, bo_nho={})
        return ra
    out = verify_and_compile(hd, val.spec)
    mem = {k: str(v) for k, v in (out.final_memory or {}).items()}
    ra.update(tang=out.stage_reached, executable=bool(out.executable),
              servable=bool(out.servable), error_code=out.error_code,
              loi="; ".join(str(x)[:180] for x in (out.details or []))[:700],
              bo_nho={k: v for k, v in mem.items()
                      if not v.startswith(("Vec3", "Line3", "Plane3",
                                           "Curved", "Circle"))})
    ra["postconditions"] = "PASS" if out.servable else (
        "FAIL" if out.stage_reached == "postconditions" else "NOT_REACHED")
    try:
        canh = pipeline._dung_scene3d(val.spec, hd) or {}
        ra["scene3d"] = len(canh.get("objects", [])) if out.servable else None
    except Exception as e:                                        # noqa: BLE001
        ra["scene3d"] = f"{type(e).__name__}"
    return ra


def main() -> int:
    RA.mkdir(parents=True, exist_ok=True)
    mong = {"e2": "121π", "e6": "400π"}
    tong: dict[str, Any] = {}
    for cid in ("e2", "e6"):
        raw, hd = _nguon(cid)
        d1, g1 = delta_1(raw)
        d2, g2 = delta_2(raw, hd, cid)
        bans = [("goc", raw, []), ("delta_1", d1, g1), ("delta_2", d2, g2)]
        tong[cid] = {"mong_doi": mong[cid], "ban": []}
        print(f"\n{'='*78}\n{cid}")
        for nhan, sp, ghi in bans:
            r = chay(nhan, sp, hd)
            r["delta"] = ghi
            gt = set(r.get("bo_nho", {}).values())
            r["exact"] = ("PASS" if mong[cid] in gt else
                          ("FAIL" if r["servable"] else "NOT_REACHED"))
            tong[cid]["ban"].append(r)
            print(f"  {nhan:9} tầng={r['tang']:22} servable={r['servable']!s:5} "
                  f"exact={r['exact']:11} scene3d={r.get('scene3d')}")
            if ghi:
                for x in ghi:
                    print(f"            · {x}")
            if r.get("loi"):
                print(f"            └ {r['loi'][:220]}")
    (RA / "replay.json").write_text(
        json.dumps(tong, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n→ {RA / 'replay.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
