# -*- coding: utf-8 -*-
"""W14 Task 5 Step 2 — đóng băng corpus gắn nhãn của cổng giả định (0 lượt gọi model).

Nhãn tay ở `LABELS.json` (viết trước khi bất kỳ cơ chế nào chạy). Script này chỉ
VẬT HOÁ hợp đồng + chương trình của đúng các hàng đã gắn nhãn từ các nhà máy ca có
sẵn, để census chạy trên đầu vào cố định; nó không đọc, không đổi nhãn. Từ chối ghi đè.
Chạy từ gốc kho:
  backend/.venv/Scripts/python.exe docs/evaluation/geometry/runs/w14-generic-formation-assumption/diagnostics/assumption_corpus/build_corpus.py
"""
from __future__ import annotations

import hashlib
import json
import sys
from fractions import Fraction
from pathlib import Path

HERE = Path(__file__).resolve()
BACKEND = HERE.parents[7] / "backend"
sys.path.insert(0, str(BACKEND))

from app.simulation.semantic_program.request_contract import RequestContract  # noqa: E402
from app.simulation.semantic_program.validator import validate_semantic_program  # noqa: E402
from scripts import build_geometry_samples as B  # noqa: E402
from scripts import replay_demo_cases as RD  # noqa: E402
from scripts import replay_negative_boundaries as RNB  # noqa: E402
from tests.geometry import test_assumption_gate as A  # noqa: E402
from tests.geometry import test_source_grounding_closure as T  # noqa: E402
from tests.geometry import w14_cases as W  # noqa: E402

LABELS = HERE.with_name("LABELS.json")
OUT = HERE.with_name("CORPUS.json")
#: Hàng `gold:` PHÁT LẠI chương trình đã lưu của lượt đo khoá luận — khai nguồn theo
#: đúng luật của guard chống nhiễm bẩn corpus nghiệm thu (`test_A5_…`): đề của chúng
#: đến từ artifact có thật dưới `thesis-final-acceptance/`, không phải bài phát triển mới.
NGUON_GOLD = "docs/evaluation/geometry/thesis-final-acceptance/CORPUS.json"


def _tinh_tien_doi_truc(p):
    """Cùng phép dời hình của `test_chuyen_dong_cung_khong_doi_dap_so`."""
    x, y, z = (Fraction(str(c)) for c in p)
    return [str(y + 7), str(x - 2), str(z + 1)]


def _ca() -> dict[str, tuple]:
    r: dict[str, tuple] = {}
    for ch in ("given_length", "layout_derived", "model_assumption"):
        r[f"ac1_{ch}"] = W.kenh_gia_dinh(ch)
    r["adv1_xy_length_gia_dinh"] = W.ca_xy_length_gia_dinh()
    r["adv2_xoay_thieu_AD"] = W.ca_xoay_thieu_AD()
    r["adv3_canh_khac_che_chieu_cao"] = W.ca_canh_khac_che_chieu_cao()
    r["adv4_lang_tru_xien"] = W.ca_lang_tru_xien()
    r["adv5_chan_duong_cao_an"] = W.ca_chan_duong_cao_an()
    _t, ct = W.chop_tam_giac()
    r["adv7_thieu_de"] = (W.hop_dong_khong_de(ct), W.chuong_trinh(ct))
    r["rf4_hai_dap_so_mot_phu_thuoc"] = W.ca_hai_dap_so_mot_phu_thuoc()
    r["adv8_nhan_vo_huong_gia_dinh"] = W.ca_nhan_vo_huong_gia_dinh()
    for b in ("khong_nguon", "gia_dinh", "claimed"):
        r[f"adv10_quan_he_{b}"] = A._p01_voi_quan_he(b)
    r["adv11_hai_dap_so_mot_ngoai_pham_vi"] = W.ca_hai_dap_so_mot_ngoai_pham_vi()
    for ten, f in W.HO.items():
        _t, ct = f()
        r[f"ho:{ten}"] = (ct, W.chuong_trinh(ct))
    _t, ct = W.chop_tam_giac()
    r["rot:chop_tam_giac_xoay"] = (ct, W.doi_toa_do(W.chuong_trinh(ct), W._xoay))
    r["rigid:prism_text_translate_swap"] = (T._contract(T.PRISM_TEXT, T._prism_payload()),
                                            W.doi_toa_do(T._program_with_height_5(), _tinh_tien_doi_truc))
    for cid in sorted(RNB.doc_de_bai()):
        _t, ct, raw = W.gold(cid)
        r[f"gold:{cid}"] = (ct, raw)
    for art, cid, _vai, _ky in RD.DEMO:
        c = RD._tim(art, cid) or {}
        r[f"demo:{cid}"] = (RequestContract.model_validate(c["analyze"]["raw_request_contract"]),
                            c["normalized_program"])
    for sid, _nhom, fn in B.BAI_MAU:
        r[f"mau:{sid}"] = (None, fn())
    return r


def _chuong_trinh(raw: dict) -> tuple[dict, bool]:
    v = validate_semantic_program(raw)
    if v.ok and v.spec is not None:
        return v.spec.model_dump(mode="json", exclude_none=True), True
    return json.loads(json.dumps(raw, default=str)), False


def main() -> None:
    if OUT.exists():
        raise SystemExit(f"refusing to overwrite {OUT}")
    nhan_bytes = LABELS.read_bytes()
    nhan = json.loads(nhan_bytes)["rows"]
    ca = _ca()
    thua, thieu = sorted(set(ca) - set(nhan)), sorted(set(nhan) - set(ca))
    if thua or thieu:
        raise SystemExit(f"labels and cases disagree: unlabelled={thua} missing={thieu}")
    rows = []
    for cid in sorted(ca):
        ct, raw = ca[cid]
        prog, schema_ok = _chuong_trinh(raw)
        rows.append({"id": cid, **nhan[cid],
                     **({"source_artifact_path": NGUON_GOLD} if cid.startswith("gold:") else {}),
                     "contract": None if ct is None else ct.model_dump(mode="json"),
                     "program": prog, "program_schema_ok": schema_ok})
    OUT.write_text(json.dumps({
        "corpus": "W14_ASSUMPTION_CORPUS", "model_calls": 0,
        "labels_sha256": hashlib.sha256(nhan_bytes.replace(b"\r\n", b"\n")).hexdigest(),
        "labels_sha256_basis": "git_blob_lf (LF-normalised LABELS.json)",
        "rows": rows,
    }, ensure_ascii=False, indent=1) + "\n", encoding="utf-8", newline="\n")
    print(OUT, len(rows))


if __name__ == "__main__":
    main()
