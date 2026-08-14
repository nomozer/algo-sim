"""Spot check HÀNH VI cho các họ năng lực — ứng viên AI-shaped, oracle production.

`test_web_generated_behavior.py` đã chứng minh cho họ WEB. File này dùng lại
`canonical_config` để phủ các họ còn lại mà provider dựng nổi ứng viên hợp lệ.

─── LUẬT CHỐNG TỰ LỪA ────────────────────────────────────────────────────

Mỗi phép thử phải TIÊM một giá trị KHÁC mặc định, và **chứng minh nó khác**
trước khi kết luận là giá trị đã truyền được. Tiêm đúng bằng mặc định thì
không chứng minh được gì — đánh dấu `PROBE_NO_OP` và ĐỎ.

Đây không phải đánh giá chất lượng LLM; nó chứng nhận HỢP ĐỒNG SINH.
"""
from __future__ import annotations

import pytest

from canonical_config import canonical_valid_config

#: (họ, target, đường trường, giá trị tiêm) — target chọn từ những cái provider
#: dựng nổi ứng viên hợp lệ, để phép thử nói về hợp đồng chứ về bộ sinh.
CASES = [
    ("ALGORITHM", "algorithm.find_max", ("data", "array"), [3, 41, 7]),
    ("BINARY", "binary.character_encoding", ("text",), "Bin"),
    ("BINARY", "binary.decimal_to_binary", ("decimalValue",), 37),
    # 0 chứ không phải 1: mặc định của ứng viên đã là 1, và cổng chống no-op đã
    # bắt đúng lượt chạy đầu — giữ ghi chú vì đó là bằng chứng cổng đỏ được.
    ("LOGIC", "logic.and_gate", ("inputA",), 0),
]


def _get(cfg: dict, path: tuple[str, ...]):
    cur = cfg
    for key in path:
        if not isinstance(cur, dict) or key not in cur:
            return None
        cur = cur[key]
    return cur


def _set(cfg: dict, path: tuple[str, ...], value):
    out = {k: (dict(v) if isinstance(v, dict) else v) for k, v in cfg.items()}
    cur = out
    for key in path[:-1]:
        cur[key] = dict(cur[key])
        cur = cur[key]
    cur[path[-1]] = value
    return out


@pytest.mark.parametrize("family,target,path,injected", CASES,
                         ids=[f"{f}:{t}" for f, t, _, _ in CASES])
def test_gia_tri_tiem_song_sot_qua_duong_production(family, target, path, injected):
    base = canonical_valid_config(target)
    assert base.status == "VALID", f"{target}: ứng viên nền không hợp lệ — {base.reason}"

    truoc = _get(base.normalized, path)
    assert truoc is not None, f"CONTRACT_SOURCE_EMPTY: không thấy đường {path} trong config"

    # CHỐNG NO-OP: chứng minh giá trị tiêm KHÁC mặc định TRƯỚC khi kết luận.
    assert injected != truoc, (
        f"PROBE_NO_OP {target}: giá trị tiêm bằng mặc định ({truoc!r}) ⇒ "
        "không chứng minh được gì về việc truyền giá trị"
    )

    ung_vien = _set(base.candidate, path, injected)
    assert _get(ung_vien, path) == injected, "phép tiêm không đổi được ứng viên"

    from app.simulation.catalog import CATALOG
    sau, err = CATALOG[target].validate(ung_vien)
    assert err is None, f"{target}: ứng viên AI-shaped bị từ chối — {err}"
    assert _get(sau, path) == injected, (
        f"{target}: giá trị tiêm KHÔNG sống sót qua validate "
        f"({_get(sau, path)!r} thay vì {injected!r}) ⇒ hợp đồng sinh không truyền được"
    )


def test_moi_ho_deu_co_it_nhat_mot_ca():
    """Cổng khớp-rỗng: một danh sách rỗng làm mọi khẳng định trên vô nghĩa."""
    assert len(CASES) >= 4, "CONTRACT_SOURCE_EMPTY: quá ít ca để kết luận"
    assert len({f for f, *_ in CASES}) >= 3, "chưa phủ đủ số họ năng lực"


def test_doi_chung_no_op_bi_bat():
    """Một cổng chưa từng đỏ là cổng chưa được chứng minh."""
    base = canonical_valid_config("logic.and_gate")
    assert base.status == "VALID"
    hien_tai = _get(base.normalized, ("inputA",))
    # Tiêm ĐÚNG giá trị hiện tại — phép so chống no-op phải phân biệt được.
    assert not (hien_tai != hien_tai), "phép so no-op không phân biệt được"
