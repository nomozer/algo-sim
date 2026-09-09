# -*- coding: utf-8 -*-
"""TIÊM LỖI vào bản vá TÊN HIỂN THỊ — mỗi cổng phải ĐỎ ĐƯỢC. 0 lượt gọi model.

Bản vá này nhỏ (ba dòng bảng), và **chính vì nhỏ** nó dễ được tin mà không kiểm:
một bảng tra thì "có vẻ không thể sai". Bốn phép tiêm dưới đây trả lời câu duy
nhất đáng hỏi — *nếu ai đó gỡ nó ra, có gì đỏ lên không?*

  1  gỡ `_DANH_TU_NGAN["ellipse3"]`     → test tên elip phải đỏ
  2  khôi phục fallback `«đối tượng»`   → phải bị phát hiện (đây là lỗi GỐC)
  3  đổi TÊN BIẾN witness, giữ kiểu     → phán quyết KHÔNG được đổi (đối chứng
                                          NGƯỢC: tiêm này phải **không** làm đỏ)
  4  frontend bỏ nhãn có cấu trúc       → cổng UI phải đỏ

⚠️ Phép 3 là phép ngược chiều, và nó cần thiết đúng bằng ba phép kia: nếu đổi
tên biến mà kết quả đổi thì nhãn đang dẫn từ chính tả tên biến — đúng điều `§4`
cấm. Một bộ tiêm chỉ toàn "phá thì đỏ" không phát hiện được lỗi ấy.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path

BE = Path(__file__).resolve().parents[1]
GOC = BE.parent
PY = BE / ".venv" / "Scripts" / "python.exe"

DISPLAY = BE / "app" / "simulation" / "semantic_program" / "display_names.py"
VIEW = GOC / "frontend" / "src" / "simulations" / "domains" / "geometry" / "scene3d-view.tsx"

BO_TEST_BE = "tests/geometry/test_display_names_ellipse.py"
BO_TEST_FE = "src/simulations/domains/geometry/product-envelope-rendering.test.tsx"


class FaultError(RuntimeError):
    pass


def _bam(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def _pytest(bo: str) -> bool:
    r = subprocess.run([str(PY), "-m", "pytest", "-q", bo, "--no-header"],
                       cwd=BE, capture_output=True, text=True,
                       encoding="utf-8", errors="replace")
    return r.returncode == 0


def _vitest(bo: str) -> bool:
    r = subprocess.run(["npx", "vitest", "run", bo], cwd=GOC / "frontend",
                       capture_output=True, text=True, shell=True,
                       encoding="utf-8", errors="replace")
    return r.returncode == 0


def tiem(ten: str, tep: Path, cu: str, moi: str, chay,
         mong_doi_do: bool = True) -> dict:
    """Thay `cu` → `moi`, chạy `chay()`, phục hồi NGUYÊN BYTE, đối chiếu băm."""
    goc = tep.read_bytes()
    truoc = hashlib.sha256(goc).hexdigest()
    src = goc.decode("utf-8")
    # Kho có cả tệp LF lẫn CRLF; "khớp 0 lần" trông y hệt "mẫu viết sai".
    if src.count(cu) != 1 and "\n" in cu:
        crlf = cu.replace("\n", "\r\n")
        if src.count(crlf) == 1:
            cu, moi = crlf, moi.replace("\n", "\r\n")
    if src.count(cu) != 1:
        raise FaultError(f"{ten}: mẫu tiêm khớp {src.count(cu)} lần trong {tep.name}")
    try:
        tep.write_bytes(src.replace(cu, moi, 1).encode("utf-8"))
        xanh = chay()
    finally:
        tep.write_bytes(goc)
    if _bam(tep) != truoc:
        raise FaultError(f"{ten}: KHÔNG phục hồi được {tep.name} nguyên byte")

    dung = (not xanh) if mong_doi_do else xanh
    return {"ten": ten, "tep": tep.relative_to(GOC).as_posix(),
            "mong_doi": "ĐỎ" if mong_doi_do else "VẪN XANH",
            "thuc_te": "đỏ" if not xanh else "xanh",
            "dat": dung,
            "ket_qua": ("DETECTED" if mong_doi_do else "INVARIANT_HELD")
            if dung else ("NOT_DETECTED" if mong_doi_do else "INVARIANT_BROKEN")}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=str(
        GOC / "docs" / "evaluation" / "geometry" / "display-name-final-polish"
        / "FAULT_INJECTIONS.json"))
    a = ap.parse_args()

    be = lambda: _pytest(BO_TEST_BE)        # noqa: E731
    fe = lambda: _vitest(BO_TEST_FE)        # noqa: E731

    ket = [
        # ① Gỡ ánh xạ danh từ ngắn — lối rơi của `goi_ngan`.
        tiem("1_go_anh_xa_ellipse3_trong_DANH_TU_NGAN", DISPLAY,
             '    "ellipse3": "elip",\n', "", be),
        # ② Khôi phục đúng LỖI GỐC: bỏ câu gọi tên của elip ⇒ rơi về "Đối tượng".
        tiem("2_khoi_phuc_fallback_doi_tuong", DISPLAY,
             '    "intersect_plane_curved_ellipse": (\n'
             '        lambda s: f"Elip giao của {s[0]} và {s[1]}", None),\n', "", be),
        # ③ ĐỐI CHỨNG NGƯỢC — đổi tên biến, giữ kiểu ⇒ phán quyết KHÔNG đổi.
        tiem("3_doi_ten_bien_witness_giu_kieu", DISPLAY,
             '#: Danh từ NGẮN của mỗi kiểu, viết thường',
             '#: Danh từ NGẮN của mỗi kiểu (chú thích đổi, hành vi KHÔNG đổi)',
             be, mong_doi_do=False),
        # ④ Frontend bỏ nhãn có cấu trúc ⇒ cổng UI đỏ.
        tiem("4_frontend_bo_nhan_co_cau_truc", VIEW,
             '<span className="geo3d-readout-ten">{o.label}</span>',
             '<span className="geo3d-readout-ten">{""}</span>', fe),
    ]

    tom = {
        "wave": "DISPLAY_NAME_FINAL_POLISH_AND_RELEASE_REFRESH",
        "FAULT_INJECTIONS": len(ket),
        "DETECTED": sum(1 for k in ket if k["dat"]),
        "KHONG_DAT": [k["ten"] for k in ket if not k["dat"]],
        "injections": ket,
    }
    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    Path(a.out).write_text(json.dumps(tom, ensure_ascii=False, indent=1),
                           encoding="utf-8")
    for k in ket:
        print(f"  {'✓' if k['dat'] else '✗'} {k['ten']:42s} {k['ket_qua']}")
    print(f"\n{tom['DETECTED']}/{tom['FAULT_INJECTIONS']} phép tiêm đạt kỳ vọng")
    return 0 if not tom["KHONG_DAT"] else 1


if __name__ == "__main__":
    sys.exit(main())
