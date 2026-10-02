# -*- coding: utf-8 -*-
"""NA-05 (W13): bộ test MẶC ĐỊNH không được đọc đường dẫn tuyệt đối ngoài kho.

Bằng chứng nằm ngoài kho (raw model output không được commit — AGENTS §4) chỉ
được đọc trong test gắn `@pytest.mark.external_evidence`, và test ấy lấy đường
dẫn từ biến môi trường chứ không ghi cứng. Quét AST các lời gọi đọc tệp có đối
số là hằng chuỗi tuyệt đối — một đường dẫn cá nhân lọt vào suite mặc định thì
T3 chỉ xanh trên đúng máy giữ tệp ấy.
"""
import ast
import re
from pathlib import Path

TESTS = Path(__file__).resolve().parent
_TUYET_DOI = re.compile(r"^(?:[A-Za-z]:[\\/]|/tmp/|/home/|/Users/)")
_HAM_DOC = {"Path", "open", "PurePath", "WindowsPath", "PosixPath"}


def _co_dau_external(fn: ast.AST) -> bool:
    return any("external_evidence" in ast.unparse(d)
               for d in getattr(fn, "decorator_list", []))


def _vi_pham(path: Path) -> list[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    bo_qua = {id(n) for fn in ast.walk(tree)
              if isinstance(fn, ast.FunctionDef) and _co_dau_external(fn)
              for n in ast.walk(fn)}
    ra = []
    for node in ast.walk(tree):
        if id(node) in bo_qua or not isinstance(node, ast.Call):
            continue
        ten = getattr(node.func, "id", None) or getattr(node.func, "attr", None)
        if ten not in _HAM_DOC:
            continue
        for a in node.args:
            if (isinstance(a, ast.Constant) and isinstance(a.value, str)
                    and _TUYET_DOI.match(a.value)):
                ra.append(f"{path.relative_to(TESTS).as_posix()}:{node.lineno}: {a.value}")
    return ra


def test_bo_test_mac_dinh_khong_doc_duong_dan_ngoai_kho():
    vi_pham = [v for p in sorted(TESTS.rglob("test_*.py")) for v in _vi_pham(p)]
    assert vi_pham == [], vi_pham
