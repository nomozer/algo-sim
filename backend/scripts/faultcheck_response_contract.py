# -*- coding: utf-8 -*-
"""TIÊM LỖI vào bản vá hợp đồng phản hồi — mỗi cổng phải ĐỎ ĐƯỢC.

Guard chưa từng đỏ là guard chưa được chứng minh (`ARCHITECTURE_MAP §8` #14).
Bảy phép tiêm, mỗi phép phá đúng MỘT thứ và đòi thấy một tập test đỏ:

  1  gỡ phán quyết ở `_semantic_route_attempt`   → `n1` mất tầng + mã
  2  gỡ ánh xạ `mã → thông điệp`                 → `n2` nhận lại lời khuyên sai
  3  đánh rơi `error_code` khi dựng envelope     → biên serialize
  4  đánh rơi `stage_reached` khi dựng envelope  → biên serialize
  5  cho adapter GHI ĐÈ mã của backend           → thẩm quyền bị tiếm
  6  frontend dò chuỗi thay vì đọc trường        → guard kiến trúc
  7  xoá một nhãn giai đoạn ở frontend           → bảng nhãn tụt lại

Phép tiêm sửa tệp THẬT rồi **phục hồi nguyên byte** trong `finally`; băm được
đối chiếu lại sau mỗi lượt, và lệch một byte là ném. Không phép tiêm nào được
để lại dấu vết — một bộ đo tự làm bẩn kho là một bộ đo không dùng lại được.
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

PIPELINE = BE / "app" / "ai" / "pipeline.py"
MESSAGES = BE / "app" / "learner_messages.py"
WORKSPACE = GOC / "frontend" / "src" / "components" / "SimulationWorkspace.tsx"

BO_TEST_BE = "tests/geometry/test_product_response_contract.py"
BO_TEST_FE = "src/components/refusal-contract.test.tsx"


class FaultError(RuntimeError):
    pass


def _bam(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def _chay_pytest(bo: str) -> bool:
    """`True` = xanh."""
    r = subprocess.run(
        [str(PY), "-m", "pytest", "-q", bo, "-x", "--no-header"],
        cwd=BE, capture_output=True, text=True, encoding="utf-8",
        errors="replace")
    return r.returncode == 0


def _chay_vitest(bo: str) -> bool:
    r = subprocess.run(
        ["npx", "vitest", "run", bo], cwd=GOC / "frontend",
        capture_output=True, text=True, shell=True, encoding="utf-8",
        errors="replace")
    return r.returncode == 0


def tiem(ten: str, tep: Path, cu: str, moi: str, chay) -> dict:
    """Thay `cu` → `moi` trong `tep`, chạy `chay()`, rồi phục hồi NGUYÊN BYTE."""
    goc_bytes = tep.read_bytes()
    bam_truoc = hashlib.sha256(goc_bytes).hexdigest()
    src = goc_bytes.decode("utf-8")
    # ⚠️ Kho này có cả tệp LF lẫn tệp CRLF. Mẫu viết bằng `\n` khớp 0 lần trên
    # tệp CRLF — và "0 lần" trông y hệt "mẫu viết sai", nên đã ăn mất thì giờ
    # nhiều lần. Thử cả hai kiểu xuống dòng thay vì đoán tệp nào là kiểu nào.
    if src.count(cu) != 1 and "\n" in cu:
        cu_crlf = cu.replace("\n", "\r\n")
        if src.count(cu_crlf) == 1:
            cu, moi = cu_crlf, moi.replace("\n", "\r\n")
    if src.count(cu) != 1:
        raise FaultError(
            f"{ten}: mẫu cần tiêm xuất hiện {src.count(cu)} lần trong "
            f"{tep.name} — phép tiêm không xác định được chỗ")
    try:
        tep.write_bytes(src.replace(cu, moi, 1).encode("utf-8"))
        xanh = chay()
    finally:
        tep.write_bytes(goc_bytes)
    if _bam(tep) != bam_truoc:
        raise FaultError(f"{ten}: KHÔNG phục hồi được {tep.name} nguyên byte")
    return {"ten": ten, "tep": tep.relative_to(GOC).as_posix(),
            "phat_hien": not xanh,
            "ket_qua": "DETECTED" if not xanh else "NOT_DETECTED"}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=str(
        GOC / "docs" / "evaluation" / "geometry"
        / "product-response-contract-alignment" / "FAULT_INJECTIONS.json"))
    a = ap.parse_args()

    be = lambda: _chay_pytest(BO_TEST_BE)          # noqa: E731
    fe = lambda: _chay_vitest(BO_TEST_FE)          # noqa: E731

    phep = [
        # ① Thẩm quyền TẠO tín hiệu — quay lại `return None` như trước bản vá.
        ("1_go_phan_quyet_semantic_program", PIPELINE,
         '        return hong_truoc_khi_dung_ir(\n'
         '            "semantic_program", ErrorCode.SEMANTIC_PROGRAM_INVALID, serr)',
         '        return None', be),
        # ② Ánh xạ `mã → thông điệp` ở thẩm quyền backend.
        ("2_go_anh_xa_ma_sang_thong_diep", MESSAGES,
         '_MSG_THEO_MA: dict[str, str] = {\n'
         '    "requested_operation_uncovered": _MSG_REQUESTED_OPERATION_UNCOVERED,\n}',
         '_MSG_THEO_MA: dict[str, str] = {}', be),
        # ③④ Biên dựng envelope đánh rơi trường.
        ("3_roi_error_code_khi_dung_envelope", PIPELINE,
         '        "error_code": getattr(outcome, "error_code", None) if outcome else None,',
         '        "error_code": None,', be),
        ("4_roi_stage_reached_khi_dung_envelope", PIPELINE,
         '        "stage_reached": getattr(outcome, "stage_reached", None) if outcome else None,',
         '        "stage_reached": None,', be),
        # ⑤ Adapter tiếm quyền phân loại của backend.
        ("5_adapter_ghi_de_ma_cua_backend", MESSAGES,
         '    return {**envelope, "learner_reason": learner_reason(envelope)}',
         '    return {**envelope, "learner_reason": learner_reason(envelope),\n'
         '            "error_code": "adapter_tu_dat"}', be),
        # ⑥ Frontend suy phân loại bằng dò chuỗi.
        ("6_frontend_do_chuoi_thay_vi_doc_truong", WORKSPACE,
         '  const ngoaiBaoDong =\n'
         '    unsupported.error_code === "requested_operation_uncovered";',
         '  const ngoaiBaoDong =\n'
         '    unsupported.reason.includes("không có đường tạo ra");', fe),
        # ⑦ Bảng nhãn frontend tụt lại sau taxonomy backend.
        ("7_xoa_mot_nhan_giai_doan", WORKSPACE,
         '  structural_coverage: "đối chiếu với các phép dựng hệ có",\n',
         '', be),
    ]

    ket = []
    for ten, tep, cu, moi, chay in phep:
        r = tiem(ten, tep, cu, moi, chay)
        ket.append(r)
        print(f"  {'✓' if r['phat_hien'] else '✗'} {ten:42s} {r['ket_qua']}")

    tong = {
        "wave": "PRODUCT_RESPONSE_CONTRACT_ALIGNMENT",
        "FAULT_INJECTIONS": len(ket),
        "DETECTED": sum(1 for r in ket if r["phat_hien"]),
        "NOT_DETECTED": [r["ten"] for r in ket if not r["phat_hien"]],
        "injections": ket,
    }
    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    Path(a.out).write_text(json.dumps(tong, ensure_ascii=False, indent=1),
                           encoding="utf-8")
    print(f"\n{tong['DETECTED']}/{tong['FAULT_INJECTIONS']} phép tiêm bị bắt")
    return 0 if not tong["NOT_DETECTED"] else 1


if __name__ == "__main__":
    sys.exit(main())
