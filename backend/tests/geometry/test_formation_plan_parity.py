# -*- coding: utf-8 -*-
"""W14 Task 3 — đặc tả HÔM NAY của năm cấu hình đã có chuỗi dựng hình đủ: chóp đáy
chữ nhật, chóp đáy vuông, hộp chữ nhật, lập phương, lăng trụ đứng đáy vuông.

Golden chụp TRƯỚC mọi sửa sản phẩm của W14 (commit riêng, trước bước bổ sung dựng
hình). Khi dựng hình chuyển sang MỘT bước bổ sung chung (Task 4), năm cấu hình này
phải giống hệt về ngữ nghĩa (R2): cùng câu lệnh khối (từng byte), cùng dãy vật dựng
hình theo (loại, tập đỉnh) kể cả thứ tự, cùng các bước (loại bước + vật trọng tâm),
cùng đáp số chính xác; nhãn chỉ được khác đúng các delta Q1 đã khai. ID máy được phép
khác (Q1: `canh_ben_SB` → `canh_ben_S_B`), nên golden không chứa ID vật nào.

Ghi golden (từ chối ghi đè), từ `backend/`:
    PYTHONIOENCODING=utf-8 .venv/Scripts/python.exe -m tests.geometry.test_formation_plan_parity
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from tests.geometry import route_cases as W

GOLDEN = Path(__file__).resolve().parent / "fixtures" / "formation_parity"
HO_PARITY = {
    "rect_pyramid_rectangle": W.chop_chu_nhat,
    "rect_pyramid_square": W.chop_vuong,
    "cuboid": W.hop_chu_nhat,
    "cube": W.lap_phuong,
    "square_prism": W.lang_tru_day_vuong,
}
#: Delta nhãn DUY NHẤT được khai (Q1, câu trả lời của người dùng 2026-10-01): họ hộp
#: viết hoa nhãn đáy trên. Không có delta nào cho hai chóp.
_DAY_TREN = {"đáy trên A′B′C′D′": "Đáy trên A′B′C′D′"}
W14_DECLARED_LABEL_DELTAS = {"cuboid": _DAY_TREN, "cube": _DAY_TREN, "square_prism": _DAY_TREN}


def _vat(o: dict) -> list:
    return [o["type"], sorted(W.dinh_cua(o)), o.get("label")]


def chup(ten: str) -> dict:
    """Một cấu hình qua đúng route sản phẩm → dạng so sánh được (không ID máy)."""
    _t, ct = HO_PARITY[ten]()
    sp, out, sc = W.chay(ct)
    assert out.servable, (ten, out.stage_reached, out.reason_code)
    by_id = {o["id"]: o for o in sc["objects"]}
    da_hien: set[str] = set()
    vat = []
    for s in sc["formation"]["steps"]:
        for i in s["visible_ids"]:
            if i not in da_hien:
                da_hien.add(i)
                if by_id[i]["type"] != "quantity":
                    vat.append(_vat(by_id[i]))
    witness = sorted(w for o in ct.obligations if (w := (o.params or {}).get("witness")))
    return {
        "solid_statement": next(s for s in sp.model_dump(mode="json", exclude_none=True)["statements"]
                                if s["kind"] == "construct_solid"),
        "formation_objects": vat,
        "steps": [{"semantic_kind": s["semantic_kind"], "focus": [_vat(by_id[i]) for i in s["focus_ids"]]}
                  for s in sc["formation"]["steps"]],
        "witnesses": {w: str(out.final_memory[w]) for w in witness},
    }


def _golden(ten: str) -> Path:
    return GOLDEN / f"{ten}.json"


def _cau(x) -> str:
    return json.dumps(x, sort_keys=True, ensure_ascii=False)


@pytest.mark.parametrize("ten", sorted(HO_PARITY))
def test_ho_da_du_giu_nguyen_ngu_nghia_dung_hinh(ten):
    cu = json.loads(_golden(ten).read_text(encoding="utf-8"))
    moi = chup(ten)
    delta = W14_DECLARED_LABEL_DELTAS.get(ten, {})
    nhan_cu = [v[2] for v in cu["formation_objects"]]
    assert all(k in nhan_cu for k in delta), ("delta khai mà golden không có", ten, delta)
    assert _cau(moi["solid_statement"]) == _cau(cu["solid_statement"]), ten
    assert [v[:2] for v in moi["formation_objects"]] == [v[:2] for v in cu["formation_objects"]], ten
    for n, m in zip(nhan_cu, (v[2] for v in moi["formation_objects"])):
        assert m in (n, delta.get(n, n)), (ten, n, m)  # trước Task 4: n; sau: đúng delta khai
    assert ([(s["semantic_kind"], [f[:2] for f in s["focus"]]) for s in moi["steps"]]
            == [(s["semantic_kind"], [f[:2] for f in s["focus"]]) for s in cu["steps"]]), ten
    assert moi["witnesses"] == cu["witnesses"], ten


if __name__ == "__main__":
    GOLDEN.mkdir(parents=True, exist_ok=True)
    for ten in sorted(HO_PARITY):
        f = _golden(ten)
        if f.exists():
            raise SystemExit(f"từ chối ghi đè {f}")
        f.write_text(json.dumps({"schema_version": "w14-formation-parity/1", "family": ten,
                                 "captured_before": "W14 Task 4 (shape-class completion pass)",
                                 **chup(ten)}, ensure_ascii=False, indent=2) + "\n",
                     encoding="utf-8", newline="\n")
        print(f.name)
