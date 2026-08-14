"""Parity mẫu↔AI ở mức TRƯỜNG NĂNG LỰC — bất biến chí mạng của đề tài.

─── HỎI GÌ ───────────────────────────────────────────────────────────────

    Trường mà một config ĐÃ VALIDATE mang theo, LLM có khai được không?

Không khai được nghĩa là bản mẫu công khai dạy được một thứ mà bài do AI sinh
**không bao giờ nói tới được**. Cổng này đã bắt được đúng lỗi ấy hai lần:

  1. `headingSize`/`headingColor` — validator và UI nhận, schema LLM thiếu.
  2. Nặng hơn: schema web còn mô tả hợp đồng CHẾT (`content`) trong khi validator
     đã chuyển sang `heading`+`paragraph` và fail-closed ⇒ **mọi** spec web do AI
     sinh đều bị từ chối. Sửa ở `1490f69`, `CACHE_VERSION` 30→31.

Nên nó ở lại kho như cổng thường trực, không phải một lượt soát.

─── NGUỒN ỨNG VIÊN, CÓ THỨ TỰ VÀ CÓ XUẤT XỨ ──────────────────────────────

  1. `CANONICAL_CONFIG` — khi bộ dẫn-từ-schema dựng nổi ứng viên hợp lệ.
  2. `PUBLIC_SAMPLE_DERIVED` — nền lấy từ mẫu công khai đang chạy, cho target
     cần cấu trúc nhất quán tham chiếu (bảng kiểu cột đóng, đồ thị cạnh trỏ nút
     thật) mà (1) không bịa nổi.
  3. `NO_TRUSTWORTHY_AI_CANDIDATE` — khai thẳng, và target ấy được SKIP CÓ TÊN
     chứ không lặng lẽ tính là đạt.

Validator production là ORACLE ở mọi nhánh. Không có đường nào để một ứng viên
"được coi là hợp lệ" mà chưa đi qua cổng thật.
"""
from __future__ import annotations

import copy

import pytest

from app.simulation.catalog import CATALOG
from canonical_config import canonical_valid_config
from test_generated_behavior_db_network import DB_BASE, NET_BASE

WEB_BASE = {
    "heading": "Trang của em",
    "paragraph": "Đoạn văn giới thiệu ngắn.",
    "style": {
        "backgroundColor": "#bfdbfe", "headingColor": "#1f2937", "headingSize": 28,
        "color": "#1f2937", "fontSize": 20, "padding": 16, "borderRadius": 8,
    },
}

#: Nền CẤU TRÚC từ mẫu công khai. Ràng buộc trường vẫn thuộc validator/schema —
#: ở đây chỉ có hình dạng, không có luật.
PUBLIC_BASES = {
    "database.relational_table_query": DB_BASE,
    "network.packet_routing": NET_BASE,
    "web.style_model": WEB_BASE,
}

#: DERIVED_RUNTIME — trường do ENGINE/ĐỊNH TUYẾN đặt, KHÔNG phải LLM điền.
#: Vắng ở schema LLM là ĐÚNG. Đây là bất đối xứng cố ý mà cổng phải hiểu; nếu
#: không nó sẽ đòi mọi tầng giống hệt nhau và tự biến mình thành vô nghĩa.
#: ⚠️ Miễn trừ phải NHỎ, CÓ TÊN, CÓ TRẦN — một danh sách phình dần sẽ nuốt chính
#: cái luật nó xin miễn.
DERIVED_RUNTIME = {
    "algorithm_id": "target do CỔNG ĐỊNH TUYẾN chọn từ đề bài, không phải do LLM khai trong config",
    "normalizations": "danh sách chuẩn hoá do chính validator sinh ra trong lúc làm sạch bảng",
}


def _llm_fields(sim_id: str) -> set[str]:
    schema = getattr(CATALOG[sim_id], "config_schema", None) or {}
    return set((schema.get("properties") or {}).keys())


def _validated(sim_id: str) -> tuple[dict | None, str]:
    """Config đã qua validator production, kèm XUẤT XỨ của ứng viên."""
    got = canonical_valid_config(sim_id)
    if got.status == "VALID":
        return got.normalized, "CANONICAL_CONFIG"
    base = PUBLIC_BASES.get(sim_id)
    if base is not None:
        cfg, err = CATALOG[sim_id].validate(copy.deepcopy(base))
        if not err and cfg:
            return cfg, "PUBLIC_SAMPLE_DERIVED"
    return None, "NO_TRUSTWORTHY_AI_CANDIDATE"


def test_quan_sat_duoc_dung_tap_target():
    """Cổng khớp-rỗng + đúng danh tính: 0 target hoặc thiếu target đã biết thì
    mọi khẳng định dưới đều đạt một cách vô nghĩa."""
    assert len(CATALOG) >= 23, f"CONTRACT_SOURCE_EMPTY: catalog chỉ có {len(CATALOG)}"
    for known in ("web.style_model", "algorithm.find_max", "network.packet_routing"):
        assert known in CATALOG, f"mất target đã biết {known} ⇒ nguồn sai"
    phu = [t for t in CATALOG if _validated(t)[0] is not None]
    assert len(phu) >= 8, f"chỉ dựng được ứng viên cho {len(phu)} target — quá ít để kết luận"


@pytest.mark.parametrize("sim_id", sorted(CATALOG))
def test_moi_truong_da_validate_deu_khai_duoc_o_schema_LLM(sim_id):
    """BẤT BIẾN: trường của một config HỢP LỆ phải nằm trong schema LLM."""
    cfg, source = _validated(sim_id)
    if cfg is None:
        pytest.skip(f"{sim_id}: {source} — bộ sinh chưa dựng nổi ứng viên, ghi nhận chứ không giả đạt")

    llm = _llm_fields(sim_id)
    assert llm, f"CONTRACT_SOURCE_EMPTY: {sim_id} không có trường nào trong schema LLM"

    thieu = sorted(set(cfg) - llm - set(DERIVED_RUNTIME))
    assert not thieu, (
        f"{sim_id} [{source}]: trường {thieu} có trong config ĐÃ VALIDATE nhưng KHÔNG "
        f"có trong schema LLM ⇒ bài do AI sinh không tả nổi năng lực này"
    )


def test_danh_sach_derived_chi_duoc_ngan_di():
    """Trần cứng: hai mục lúc dựng cổng. Thêm một dòng ở đây là tự khai vừa miễn
    một trường đáng lẽ LLM phải khai được."""
    assert set(DERIVED_RUNTIME) == {"algorithm_id", "normalizations"}
    for k, v in DERIVED_RUNTIME.items():
        assert len(v) > 40, f"{k}: lý do quá ngắn để kiểm được"


def test_moi_target_phu_deu_ghi_xuat_xu():
    """Không target nào 'đạt' mà giấu chỗ lấy ứng viên."""
    hop_le = {"CANONICAL_CONFIG", "PUBLIC_SAMPLE_DERIVED", "NO_TRUSTWORTHY_AI_CANDIDATE"}
    for t in CATALOG:
        assert _validated(t)[1] in hop_le, f"{t}: xuất xứ không hợp lệ"


def test_doi_chung_duong_go_mot_truong_khoi_schema_bi_bat():
    """LỖI A — gỡ một trường lõi khỏi schema LLM ⇒ phải ĐỎ.

    Dựng lại đúng hình dạng lỗi đã có thật trong kho, để chứng minh phép so này
    đỏ được. Một cổng chưa từng đỏ là một cổng chưa được chứng minh.
    """
    cfg, _ = _validated("web.style_model")
    assert cfg is not None, "không lấy được config web đã validate"
    llm_thieu = _llm_fields("web.style_model") - {"heading"}
    assert sorted(set(cfg) - llm_thieu - set(DERIVED_RUNTIME)) == ["heading"], (
        "phép so không phát hiện được trường bị gỡ ⇒ cổng vô nghĩa"
    )


def test_doi_chung_am_ung_vien_bi_tu_choi_khong_duoc_tinh():
    """LỖI B — ứng viên validator từ chối KHÔNG được tính là bằng chứng parity."""
    cfg, err = CATALOG["network.packet_routing"].validate({"nodes": [], "links": []})
    assert err is not None and cfg is None, "config rỗng vẫn lọt qua validator"


def test_doi_chung_hop_dong_web_chet_khong_quay_lai():
    """LỖI C — hình dạng `content` cũ phải bị TỪ CHỐI ở cả hai tầng.

    Khoá bản vá `1490f69`: schema LLM không được quay lại mô tả hợp đồng chết.
    """
    assert "content" not in _llm_fields("web.style_model"), "hợp đồng `content` đã chết quay lại schema"
    assert "heading" in _llm_fields("web.style_model"), "schema mất trường `heading` hiện hành"
    _, err = CATALOG["web.style_model"].validate({"content": "một khối chữ", "style": {}})
    assert err is not None, "validator vẫn nhận hợp đồng `content` cũ"
