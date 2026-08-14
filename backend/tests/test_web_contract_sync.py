"""Hợp đồng `web.style_model` phải KHỚP qua cả ba tầng.

─── VÌ SAO CÓ FILE NÀY ────────────────────────────────────────────────────

Cùng một danh sách thuộc tính CSS sống ở ba nơi, chép tay cả ba:

    app/validation/simulation.py   `_WEB_NUMERIC`   ← NGUỒN: miền validator nhận
    app/simulation/catalog.py      schema           ← thứ LLM ĐƯỢC BIẾT là có
    frontend/.../web/props.ts      `NUMERIC_RANGE`  ← ô điều khiển của học sinh

Và chúng ĐÃ LỆCH: `headingSize`/`headingColor` có ở validator và ở UI, nhưng
KHÔNG có trong schema đưa cho LLM. Hệ quả không phải lỗi vặt — mọi bài CSS do
AI sinh không bao giờ nói được về kiểu chữ của `<h1>`, tức mất đúng bài học
phân cấp (`.trang h1` khác `.trang p`) mà bản mẫu dựng ra để dạy. Bản mẫu làm
được, bài AI sinh thì không.

Không cổng nào bắt được: cross-lock BE↔FE hiện có khoá *family/mechanism*, chứ
không khoá *miền giá trị thuộc tính*.

─── LUẬT ─────────────────────────────────────────────────────────────────

Trường vừa LLM-ĐIỀN vừa HỌC-SINH-SỬA thì cả ba tầng phải khớp cả TÊN lẫn MIỀN.
Trường dẫn xuất/nội bộ được phép vắng ở schema LLM — nhưng phải khai rõ, và có
đối chứng dương chứng minh cổng hiểu bất đối xứng CỐ Ý ấy.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

from app.simulation.catalog import CATALOG
from app.validation.simulation import _WEB_DEFAULT_STYLE, _WEB_NUMERIC

REPO = Path(__file__).resolve().parents[2]
PROPS_TS = REPO / "frontend" / "src" / "simulations" / "domains" / "web" / "props.ts"


def _llm_style_schema() -> dict:
    """Schema `style` ĐÚNG như đường sinh đặc tả nhận được."""
    spec = CATALOG["web.style_model"]
    schema = spec.config_schema if hasattr(spec, "config_schema") else None
    if schema is None:  # pragma: no cover — hình dạng đổi thì phải ĐỎ, không đoán
        pytest.fail("CONTRACT_SOURCE_EMPTY: không lấy được config_schema của web.style_model")
    props = schema.get("properties", {}).get("style", {}).get("properties")
    if not props:
        pytest.fail("CONTRACT_SOURCE_EMPTY: schema LLM không có nhánh style.properties")
    return props


def _frontend_numeric() -> dict[str, tuple[int, int]]:
    """`NUMERIC_RANGE` của frontend, đọc thẳng từ nguồn TS."""
    src = PROPS_TS.read_text(encoding="utf-8")
    block = re.search(r"export const NUMERIC_RANGE = \{(.*?)\n\} as const;", src, re.S)
    if not block:
        pytest.fail("CONTRACT_SOURCE_EMPTY: không thấy NUMERIC_RANGE trong props.ts")
    out: dict[str, tuple[int, int]] = {}
    for m in re.finditer(r"(\w+):\s*\{[^}]*?min:\s*(-?\d+),\s*max:\s*(-?\d+)", block.group(1)):
        out[m.group(1)] = (int(m.group(2)), int(m.group(3)))
    if not out:
        pytest.fail("CONTRACT_SOURCE_EMPTY: NUMERIC_RANGE không đọc ra trường nào")
    return out


def test_ba_nguon_deu_khong_rong():
    """Cổng khớp-rỗng là cổng vô nghĩa — chứng minh đã nhìn thấy dữ liệu thật."""
    assert len(_WEB_NUMERIC) >= 4, "validator không khai đủ thuộc tính số"
    assert len(_llm_style_schema()) >= 5, "schema LLM quá ít trường để tin"
    assert len(_frontend_numeric()) >= 4, "frontend không khai đủ thuộc tính số"


def test_thuoc_tinh_so_khop_ten_va_mien_qua_ca_ba_tang():
    llm = _llm_style_schema()
    fe = _frontend_numeric()

    thieu_o_llm = sorted(set(_WEB_NUMERIC) - set(llm))
    assert not thieu_o_llm, (
        f"validator nhận {thieu_o_llm} nhưng schema LLM KHÔNG có ⇒ "
        "bài do AI sinh không bao giờ dùng được năng lực này"
    )
    thieu_o_fe = sorted(set(_WEB_NUMERIC) - set(fe))
    assert not thieu_o_fe, f"validator nhận {thieu_o_fe} nhưng học sinh không có ô điều khiển"

    for name, (lo, hi) in _WEB_NUMERIC.items():
        assert llm[name].get("minimum") == lo and llm[name].get("maximum") == hi, (
            f"{name}: validator [{lo}, {hi}] ≠ schema LLM "
            f"[{llm[name].get('minimum')}, {llm[name].get('maximum')}]"
        )
        assert fe[name] == (lo, hi), f"{name}: validator [{lo}, {hi}] ≠ frontend {fe[name]}"


def test_truong_mau_cung_phai_co_mat_o_schema_llm():
    """`headingColor` không phải số nên cổng số ở trên không chạm tới nó."""
    llm = _llm_style_schema()
    mau = {k for k in _WEB_DEFAULT_STYLE if k not in _WEB_NUMERIC}
    assert mau, "CONTRACT_SOURCE_EMPTY: không suy ra được trường màu nào"
    thieu = sorted(mau - set(llm))
    assert not thieu, f"trường màu {thieu} validator nhận nhưng schema LLM không phơi"


def test_schema_llm_khong_phoi_truong_validator_tu_choi():
    """Chiều ngược lại: phơi thứ validator không nhận thì spec AI sinh ra sẽ bị
    từ chối — im lặng với người dùng, tốn một lượt API."""
    llm = set(_llm_style_schema())
    nhan_duoc = set(_WEB_NUMERIC) | set(_WEB_DEFAULT_STYLE)
    thua = sorted(llm - nhan_duoc)
    assert not thua, f"schema LLM phơi {thua} nhưng validator không nhận"


def test_doi_chung_duong_cong_bat_duoc_khi_thieu_mot_truong():
    """LỖI A của ma trận: gỡ `headingSize` khỏi schema ⇒ phải ĐỎ.

    Một cổng chưa từng đỏ là một cổng chưa được chứng minh. Dựng lại đúng trạng
    thái đã tồn tại trong kho trước bản vá này.
    """
    llm_thieu = {k: v for k, v in _llm_style_schema().items() if k != "headingSize"}
    thieu = sorted(set(_WEB_NUMERIC) - set(llm_thieu))
    assert thieu == ["headingSize"], "phép so không phát hiện được thiếu sót ⇒ cổng vô nghĩa"


def test_doi_chung_duong_cong_bat_duoc_khi_lech_mien():
    """LỖI B: đổi miền ở MỘT tầng ⇒ phải ĐỎ."""
    fe_lech = dict(_frontend_numeric())
    fe_lech["headingSize"] = (16, 999)
    assert fe_lech["headingSize"] != _WEB_NUMERIC["headingSize"], (
        "phép so miền không phân biệt được ⇒ cổng vô nghĩa"
    )


def test_doi_chung_am_truong_noi_bo_duoc_phep_vang():
    """LỖI F: trường DẪN XUẤT/NỘI BỘ vắng ở schema LLM là ĐÚNG.

    Chứng minh cổng hiểu bất đối xứng CỐ Ý, chứ không phải đòi mọi tầng giống
    hệt nhau. `selected` là trạng thái chọn của học sinh — do runtime sinh, LLM
    không có việc gì phải điền.
    """
    llm = set(_llm_style_schema())
    assert "selected" not in llm, "trường runtime bị phơi nhầm ra schema LLM"
    assert "selected" not in _WEB_NUMERIC and "selected" not in _WEB_DEFAULT_STYLE


def test_descriptor_artifact_con_tuoi():
    """Artifact sinh-từ-nguồn phải được sinh lại sau khi schema đổi."""
    path = REPO / "frontend" / "src" / "simulations" / "capability-descriptors.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    assert data, "CONTRACT_SOURCE_EMPTY: descriptor rỗng"
    assert "web.style_model" in json.dumps(data), "descriptor không nhắc web.style_model"
