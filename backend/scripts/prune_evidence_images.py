# -*- coding: utf-8 -*-
"""regular-triangular-pyramid-w01 · E — CHÍNH SÁCH LƯU ẢNH của một run đo trình duyệt. 0 lượt gọi model.

Bộ đo (`compiler-scene-replay.mjs`, các đầu dò W02/W04/W05, `scene3d-playback-check.mjs`) chụp mọi trạng thái nó kiểm
— nhiều phép kiểm đọc điểm ảnh, nên CHỤP vẫn là một phần của phép kiểm. Thứ đổi ở đây là thứ được LƯU vào run sau khi
mọi phép kiểm và bộ dựng bằng chứng đã chạy (W5 lưu 768 ảnh, phần lớn là trạng thái đạt không ai cần xem lại):

  · ảnh bộ dựng bằng chứng ĐỌC (`results/EVIDENCE_IMAGE_INPUTS.json`) và ảnh nó SINH (sheet, phim, mục lục, crop cạnh
    khuất) — oracle thị giác bắt buộc, giữ;
  · ảnh trong tập duyệt CHỌN TRƯỚC khi đo (`inputs/REVIEW_SET.json`: mỗi mục một yêu cầu/lỗi), giữ;
  · MỌI ảnh của một họ có lượt nào thất bại (bộ suite hay đầu dò) — giữ trọn để chẩn đoán;
  · còn lại: bỏ khỏi run, nhưng sha256 + kích thước từng ảnh bỏ vẫn ghi ở `results/IMAGE_POLICY.json` (quan sát không
    mất dấu, chỉ không xuất bản).

`--dry-run` chỉ ghi chính sách, không xoá. Không bao giờ chạm run khác (đường dẫn phải nằm dưới `--run-dir`).

usage: python prune_evidence_images.py --run-dir <run> --commit <sha> --candidate <hash> [--dry-run]
"""
from __future__ import annotations

import argparse
import fnmatch
import hashlib
import json
import re
import struct
from pathlib import Path

#: Thư mục ảnh của một họ (`evidence_dir` của kịch bản suite) ⇐ id họ.
def _thu_muc_ho(ho: str) -> str:
    return ho.replace("_", "-")


def _kich_thuoc_png(p: Path) -> tuple[int, int] | None:
    dau = p.read_bytes()[:24]
    if dau[:8] != b"\x89PNG\r\n\x1a\n":
        return None
    return struct.unpack(">II", dau[16:24])


def _sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def _doc(p: Path) -> dict:
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else {}


#: exact-dimensions — lỗi MÔI TRƯỜNG (trang/CDP không sẵn sàng) không phải lỗi phép kiểm sản phẩm: nó không giữ trọn ảnh
#: của cả họ. Cùng mẫu với `frontend/scripts/capture-policy.phanLoaiLoi`.
_MOI_TRUONG = re.compile(r"POLL_TIMEOUT|CDP_TIMEOUT|WS_OPEN_TIMEOUT|TEXTAREA_NOT_READY|SUBMIT_NOT|net::ERR")


def _hong_san_pham(r: dict) -> bool:
    return r.get("pass") is not True and not _MOI_TRUONG.search(str(r.get("run_error") or ""))


def ho_that_bai(results: Path) -> set[str]:
    """Họ có ít nhất một lượt KHÔNG đạt vì PHÉP KIỂM (không vì môi trường) ở suite hay ở một đầu dò."""
    hong: set[str] = set()
    for ho, rec in (_doc(results / "BROWSER_EVIDENCE.json").get("scenarios") or {}).items():
        lan = [*(rec.get("positive") or {}).values(),
               *(v for k in ("negative", "served") for kieu in (rec.get(k) or {}).values() for v in kieu.values())]
        if any(_hong_san_pham(r) for r in lan) or (not rec.get("pass") and not lan):
            hong.add(ho)
    for ten in ("W02_CLOSURE_PROBE.json", "W04_PANELS_PROBE.json", "W05_FOCUS_PROBE.json", "PLAYBACK_EVIDENCE.json"):
        for r in _doc(results / ten).get("runs") or []:
            if r.get("family") and _hong_san_pham(r):
                hong.add(r["family"])
    return hong


def viewport_that(results: Path) -> dict[tuple[str, str], dict]:
    """(thư mục họ, khổ) → khung nhìn CSS mà đầu dò W05 đo được trên trang (khung xin có thể khác khung thật)."""
    ra = {}
    for r in _doc(results / "W05_FOCUS_PROBE.json").get("runs") or []:
        if isinstance(r.get("viewport"), dict) and r.get("family") and r.get("kind"):
            ra[(_thu_muc_ho(r["family"]), r["kind"])] = r["viewport"]
    return ra


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--run-dir", required=True, type=Path)
    ap.add_argument("--commit", required=True)
    ap.add_argument("--candidate", required=True)
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()
    run = a.run_dir.resolve()
    anh, results = run / "images", run / "results"
    dau_vao = set(_doc(results / "EVIDENCE_IMAGE_INPUTS.json").get("images") or [])
    crops = _doc(results / "HIDDEN_EDGE_CROPS.json")
    dau_ra = {c["path"] for c in crops.get("crops") or []}
    dau_ra |= {m.get("sheet") for m in (crops.get("family_sheets") or {}).values()}
    dau_ra |= {(m.get("filmstrip") or {}).get("filmstrip") for m in (crops.get("family_sheets") or {}).values()}
    dau_ra |= {"images/overview/INDEX.png"}
    duyet = _doc(run / "inputs" / "REVIEW_SET.json").get("items") or []
    hong = ho_that_bai(results)
    thu_muc_hong = {_thu_muc_ho(h) for h in hong}
    vp = viewport_that(results)
    giu, bo = [], []
    for p in sorted(anh.rglob("*.png")):
        rel = p.relative_to(run).as_posix()
        phan = rel.split("/")
        ho = next((x for x in phan[1:-1] if x not in ("focus", "review", "negative", "served", "playback",
                                                        "formation", "hidden-edges")), None)
        kho = next((x for x in phan if x in ("desktop", "mobile", "low")), None)
        ly_do, yeu_cau = None, None
        if rel in dau_vao:
            ly_do, yeu_cau = "oracle_input", "đầu vào bắt buộc của bộ dựng bằng chứng thị giác (sheet/phim/crop)"
        elif rel in dau_ra:
            ly_do, yeu_cau = "builder_output", "đầu ra của bộ dựng bằng chứng (sheet, phim, mục lục, crop cạnh khuất)"
        elif m := next((m for m in duyet if fnmatch.fnmatch(rel, m["path"])), None):
            ly_do, yeu_cau = "review", m["requirement"]
        elif ho in thu_muc_hong:
            ly_do, yeu_cau = "failure", f"họ {ho} có lượt không đạt — giữ trọn ảnh để chẩn đoán"
        muc = {"path": rel, "family_dir": ho, "state": p.stem, "viewport": kho,
               "viewport_css_measured": vp.get((ho, kho)), "image_px": _kich_thuoc_png(p),
               "sha256": _sha(p), "bytes": p.stat().st_size}
        if ly_do:
            giu.append({**muc, "reason": ly_do, "requirement": yeu_cau})
        else:
            bo.append(muc)
    if not a.dry_run:
        for m in bo:
            (run / m["path"]).unlink()
    results.mkdir(parents=True, exist_ok=True)
    (results / "IMAGE_POLICY.json").write_text(json.dumps({
        "schema_version": "image-policy/1",
        "commit": a.commit, "candidate": a.candidate, "dry_run": a.dry_run,
        "rule": "kept = oracle inputs + builder outputs + pre-registered review set + every image of a failed family; "
                "pruned images are recorded (sha256, bytes) but not published",
        "failed_families": sorted(hong),
        "kept": giu, "kept_count": len(giu),
        "pruned_count": len(bo), "pruned_bytes": sum(m["bytes"] for m in bo), "pruned": bo,
    }, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(f"kept {len(giu)} · pruned {len(bo)} ({sum(m['bytes'] for m in bo) // 1024} KiB)"
          f"{' [dry-run]' if a.dry_run else ''} · failed families: {sorted(hong) or 'none'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
