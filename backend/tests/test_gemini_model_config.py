# -*- coding: utf-8 -*-
"""`GEMINI_MODEL` — đổi model phải TƯỜNG MINH, và phải đi vào artifact.

VÌ SAO CẦN KHOÁ: model là **một phần danh tính của hệ được đo**
(`model_target` trong seal manifest). Hai cách hỏng, ngược chiều nhau, đều
khiến một lượt đo không còn diễn giải được:

  (a) mặc định TRÔI — ai đó đổi hằng số cho tiện, và mọi lượt sau chạy model
      khác mà artifact vẫn đọc như cũ;
  (b) env KHÔNG có tác dụng — người chạy tưởng đã A/B xong, thực ra hai lượt
      cùng một model.

`MODEL` được đọc **lúc nạp module**, nên `monkeypatch.setenv` rồi đọc lại thuộc
tính sẽ xanh oan — phải nạp lại module.

Nhưng `importlib.reload(gemini)` là **cái bẫy thứ ba**, và nó đã cắn thật khi
viết file này: reload thay chính `sys.modules["app.ai.gemini"]`, nên mọi module
khác đang giữ tham chiếu tới `gemini.BudgetExceeded` cũ bỗng bắt hụt lớp ngoại
lệ — `test_live_budget.py` đỏ, mà đỏ ở một file không liên quan gì. Nên ở đây
nạp một **BẢN SAO RIÊNG** dưới tên khác; `app.ai.gemini` không bị đụng.
"""
from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

from app.ai import gemini

_GEMINI_PY = Path(gemini.__file__)


def _nap_ban_sao():
    """Nạp `gemini.py` thành một module RIÊNG, không ghi đè bản dùng chung."""
    spec = importlib.util.spec_from_file_location("_gemini_ban_sao", _GEMINI_PY)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


#: Model của lượt đo chính thức #1 (`4e13e2b`, SEALED `7e5df014…`). Đổi mặc
#: định mà không đổi dòng này là ĐỎ — và đó là mục đích: con số cũ gắn với model
#: cũ, đổi ngầm thì không ai truy lại được.
MODEL_LUOT_1 = "gemini-2.5-flash"


def test_mac_dinh_van_la_model_cua_luot_do_1(monkeypatch):
    """Mặc định KHÔNG được đổi ngầm theo một lần nâng cấp."""
    monkeypatch.delenv("GEMINI_MODEL", raising=False)
    mod = _nap_ban_sao()
    assert mod.MODEL == MODEL_LUOT_1, (
        f"mặc định nay là {mod.MODEL!r}, không còn là model của lượt #1. "
        "Nếu đổi có chủ đích thì sửa cả `MODEL_LUOT_1` và khai vào "
        "`RUN2_PROTOCOL §7b` — số cũ gắn với model cũ."
    )


def test_env_that_su_co_tac_dung(monkeypatch):
    """Không có nhánh này thì một lượt A/B có thể chạy hai lần cùng model."""
    monkeypatch.setenv("GEMINI_MODEL", "gemini-3.7-flash")
    mod = _nap_ban_sao()
    assert mod.MODEL == "gemini-3.7-flash"


def test_nap_ban_sao_KHONG_dung_toi_module_dung_chung(monkeypatch):
    """Chính cái bẫy đã cắn lúc viết file này — giữ nó lại làm guard.

    `importlib.reload` thay module trong `sys.modules`, và mọi `except
    gemini.BudgetExceeded` ở nơi khác lập tức bắt hụt vì lớp ngoại lệ đã là một
    đối tượng khác. Triệu chứng: `test_live_budget.py` đỏ vì một test cấu hình
    model.
    """
    import sys

    truoc = sys.modules["app.ai.gemini"]
    loai_ngoai_le_truoc = gemini.BudgetExceeded
    monkeypatch.setenv("GEMINI_MODEL", "gemini-3.1-pro-preview")
    _nap_ban_sao()
    assert sys.modules["app.ai.gemini"] is truoc
    assert gemini.BudgetExceeded is loai_ngoai_le_truoc


def test_URL_goi_dung_model_dang_cau_hinh():
    """Đọc được `MODEL` mà URL vẫn hardcode thì env chỉ là trang trí."""
    import inspect

    src = inspect.getsource(gemini)
    assert "{MODEL}:generateContent" in src, \
        "URL không còn nội suy MODEL — env sẽ không tới được request"

    # Tên model được phép xuất hiện ĐÚNG MỘT LẦN: làm giá trị mặc định của
    # `os.getenv`. Lần thứ hai nghĩa là có một đường gọi bỏ qua `MODEL`.
    ma = [d for d in src.splitlines()
          if MODEL_LUOT_1 in d and not d.strip().startswith("#")]
    assert len(ma) == 1, (
        f"tên model xuất hiện {len(ma)} lần trong mã (ngoài comment): {ma}. "
        "Chỉ được có một, ở giá trị mặc định của `os.getenv`."
    )
    assert "os.getenv" in ma[0]


def test_runner_ghi_model_vao_artifact():
    """Artifact không ghi model thì hai lượt A/B đọc y hệt nhau."""
    import importlib.util
    from pathlib import Path

    runner_path = Path(__file__).resolve().parents[1] / "scripts" / "run_sealed_evaluation.py"
    spec = importlib.util.spec_from_file_location("rn_model_check", runner_path)
    rn = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(rn)

    class _NganSachGia:
        logical_calls = 0
        http_requests = 0
        retry_requests = 0

    bao = rn._tong_ket([], 20, {"commit_ngan": "x", "cache_version": "37"},
                       "van_tay", _NganSachGia(), None)
    assert bao["model"] == gemini.MODEL
    assert bao["model"] != "KHONG_XAC_DINH"
