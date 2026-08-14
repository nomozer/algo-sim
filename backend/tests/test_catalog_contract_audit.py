"""Soát hợp đồng sinh đặc tả cho CẢ 23 target — dẫn từ nguồn, không bảng tay.

─── VÌ SAO ────────────────────────────────────────────────────────────────

`web.style_model` là ca THỨ BA cùng một mẫu hỏng trong M20: hai bản sao của một
sự thật, không ai khoá. Ở đó validator và UI nhận `headingSize`/`headingColor`
còn schema đưa cho LLM thì không, nên **mọi bài CSS do AI sinh mất hẳn bài học
phân cấp** — bản mẫu dạy được, bài AI sinh thì không.

Mẫu hỏng ấy tổng quát được, nên gác nó ở mức catalog thay vì vá từng target.

⚠️ KHÔNG dựng bảng 23 dòng viết tay (NHIỆM VỤ 11): mọi khẳng định ở đây đọc
`CATALOG` — thêm target mới là tự động bị soát, không phải nhớ thêm một dòng.
"""
from __future__ import annotations

import pytest

from app.simulation.catalog import CATALOG

#: Target KHÔNG đi qua đường sinh của LLM — khai kèm lý do, chỉ được NGẮN ĐI.
#: Rỗng nghĩa là mọi target công khai đều AI-sinh được; nếu sau này có ngoại lệ
#: thì nó phải có tên và lý do ở đây, không được lặng lẽ vắng schema.
NOT_AI_GENERATABLE: dict[str, str] = {}


def _schema_of(spec):
    return getattr(spec, "config_schema", None)


def test_catalog_khong_rong_va_du_target():
    """Cổng khớp-rỗng: một CATALOG rỗng làm MỌI khẳng định dưới đạt vô nghĩa."""
    assert len(CATALOG) >= 23, f"CONTRACT_SOURCE_EMPTY: catalog chỉ có {len(CATALOG)} target"
    assert "web.style_model" in CATALOG, "mất target đã biết ⇒ nguồn sai"


@pytest.mark.parametrize("sim_id", sorted(CATALOG))
def test_moi_target_co_schema_cho_LLM(sim_id):
    """Vắng schema = LLM không sinh nổi target ấy. Phải khai rõ, không im lặng."""
    if sim_id in NOT_AI_GENERATABLE:
        assert len(NOT_AI_GENERATABLE[sim_id]) > 30, f"{sim_id}: lý do quá ngắn để kiểm"
        return
    schema = _schema_of(CATALOG[sim_id])
    assert schema, f"{sim_id}: không có config_schema ⇒ đường sinh không tả nổi target này"
    assert schema.get("properties"), f"{sim_id}: schema không khai trường nào"


#: PHÁT HIỆN CỦA BẢN SOÁT — schema KHÔNG khai `additionalProperties: False`.
#:
#: Nặng nhẹ khác ca `web.style_model`: ở đó một NĂNG LỰC ĐANG CÓ không tả nổi
#: qua đường sinh (mất hẳn bài học). Ở đây validator vẫn fail-closed, nên spec
#: sai bị TỪ CHỐI chứ không lọt — cái mất là một lượt phân tích hỏng, im lặng
#: với người dùng và tốn một lượt API.
#:
#: Ghi ra thay vì sửa 22 schema trong một lượt: đóng hợp đồng ở tầng schema đổi
#: thứ LLM nhận ⇒ phải bump `CACHE_VERSION` và chạy lại đánh giá định tuyến.
#: Đó là một wave riêng, không phải việc kèm.
#: ⚠️ Danh sách chỉ được NGẮN ĐI. `web.style_model` KHÔNG có ở đây vì nó đã đóng
#: — tức mẫu đúng đã tồn tại trong kho để chép theo.
SCHEMA_CHUA_DONG: tuple[str, ...] = (
    "algorithm.binary_search", "algorithm.bounded_control_flow", "algorithm.bubble_sort",
    "algorithm.count_if", "algorithm.find_max", "algorithm.find_min",
    "algorithm.insertion_sort", "algorithm.linear_search", "algorithm.scan",
    "algorithm.selection_sort", "algorithm.sum_if",
    "binary.base_conversion", "binary.character_encoding", "binary.decimal_to_binary",
    "database.relational_table_query", "generic.rule_scene",
    "logic.and_gate", "logic.boolean_dag",
    "network.graph_traversal", "network.packet_routing", "network.protocol_encapsulation",
    "tree.traversal",
)


@pytest.mark.parametrize("sim_id", sorted(CATALOG))
def test_schema_dong_khong_mo_duong_tu_do(sim_id):
    """`additionalProperties: False` là thứ giữ hợp đồng ĐÓNG ở tầng schema."""
    if sim_id in NOT_AI_GENERATABLE:
        return
    dong = _schema_of(CATALOG[sim_id]).get("additionalProperties") is False
    if sim_id in SCHEMA_CHUA_DONG:
        assert not dong, (
            f"{sim_id} đã đóng schema rồi — xoá khỏi SCHEMA_CHUA_DONG "
            "(nợ chỉ được ngắn đi, và mục đã trả mà quên xoá cũng ĐỎ)"
        )
        return
    assert dong, f"{sim_id}: schema không đóng ⇒ LLM điền được trường validator sẽ từ chối"


def test_no_schema_chua_dong_khong_duoc_phinh_them():
    """Trần cứng: 22 lúc dựng cổng. Thêm một dòng là tự khai vừa tạo nợ mới."""
    assert len(SCHEMA_CHUA_DONG) <= 22, "nợ schema phình ra so với lúc dựng cổng"
    assert "web.style_model" not in SCHEMA_CHUA_DONG, (
        "web.style_model là MẪU ĐÚNG đã đóng — không được đưa vào nợ"
    )


@pytest.mark.parametrize("sim_id", sorted(CATALOG))
def test_moi_target_co_validator_that(sim_id):
    """Schema mô tả cái LLM ĐƯỢC PHÉP nói; validator mới là thứ PHÁN QUYẾT.

    Có schema mà không có validator nghĩa là hợp đồng chỉ tồn tại trên giấy.
    """
    spec = CATALOG[sim_id]
    fn = getattr(spec, "validate", None)
    assert callable(fn), f"{sim_id}: không có validator ⇒ hợp đồng không ai thực thi"


@pytest.mark.parametrize("sim_id", sorted(CATALOG))
def test_target_khai_du_dinh_danh_de_truy_nguon(sim_id):
    """Mỗi target phải truy được về miền và executor — nếu không thì một lệch
    hợp đồng sau này không tìm ra chủ sở hữu để sửa."""
    spec = CATALOG[sim_id]
    assert getattr(spec, "domain", None), f"{sim_id}: thiếu domain"
    assert getattr(spec, "executor_id", None), f"{sim_id}: thiếu executor_id"


def test_danh_sach_khong_sinh_duoc_chi_duoc_NGAN_DI():
    """Cùng kỉ luật với `KNOWN_GAPS`: một ngoại lệ không có trần sẽ lớn dần cho
    tới khi luật không còn nghĩa."""
    assert NOT_AI_GENERATABLE == {}, (
        "có target công khai không sinh được qua LLM — nếu đúng ý thì giữ, "
        "nhưng phải cập nhật cả báo cáo phạm vi khoá luận"
    )


def test_doi_chung_duong_cong_bat_duoc_schema_mo():
    """Một cổng chưa từng đỏ là cổng chưa được chứng minh."""
    gia = {"type": "object", "additionalProperties": True, "properties": {"x": {}}}
    assert gia.get("additionalProperties") is not False, "phép kiểm không phân biệt được"


def test_doi_chung_duong_cong_bat_duoc_schema_rong():
    gia = {"type": "object", "additionalProperties": False, "properties": {}}
    assert not gia.get("properties"), "phép kiểm không bắt được schema rỗng"
