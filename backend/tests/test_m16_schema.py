# -*- coding: utf-8 -*-
"""M16 Task 1 (W1) — schema/contract case đánh giá M16 + khóa integrity frozen
dataset (30 case DATASET). Nguồn yêu cầu: .superpowers/sdd/m16-task-1-brief.md.
"""

from __future__ import annotations

from app.evaluation.dataset import DATASET, EvalItem
from app.evaluation.m16_schema import (
    M16_DATASET_VERSION,
    M16Archetype,
    M16Expectation,
    check_m16_admission,
    frozen_dataset_fingerprint,
)
from app.simulation.descriptor import FamilyId

# PIN — tính MỘT LẦN bằng chính frozen_dataset_fingerprint(), tại M16 Task 1,
# với DATASET 30 case ở trạng thái commit c93a7a4 (M15 close). Chính sách dự
# án: DATASET 30 case KHÔNG BAO GIỜ được sửa nội dung (dataset.py docstring +
# docs/CURRENT_STATE.md) — vì vậy hằng số này KHÔNG có quy trình "cập nhật hợp
# lệ" theo nghĩa thông thường. Nếu test dưới đây đỏ, mặc định đó là DATASET đã
# bị sửa ngoài ý muốn (bug) — không phải việc chạy lại
# frozen_dataset_fingerprint() rồi dán đè giá trị mới. Cách tái tính (CHỈ dùng
# nếu một milestone tương lai CHÍNH THỨC được duyệt đổi DATASET — điều policy
# hiện tại cấm): gọi app.evaluation.m16_schema.frozen_dataset_fingerprint()
# sau khi thay đổi, dán giá trị mới vào đây kèm ghi chú milestone/lý do.
_FROZEN_FINGERPRINT_PIN = "86e5a31db6d5a11c677dad95842e5ed6eaafc3b373afea651c49ef5258021dbf"


def _valid_base_kwargs(item_id: str, group: str = "specialized") -> dict:
    """Kwargs EvalItem thoả luật kết nạp CŨ (check_admission) — cô lập vi phạm
    M16 khỏi vi phạm luật cũ trong các test admission dưới đây."""
    return dict(
        id=item_id,
        text="Đề mẫu cho test admission M16.",
        group=group,
        expect_simulation_id=None if group == "unsupported" else "algorithm.bubble_sort",
        learning_objective="Học sinh hiểu cơ chế X qua mô phỏng trực quan.",
        pedagogical_rationale=(
            "Mô phỏng cơ chế ẩn so sánh-đổi-chỗ từng bước, trực quan hơn hẳn "
            "text/ảnh/video/quiz vì học sinh thấy trực tiếp trạng thái đổi chỗ."
        ),
        capability_family="sorting_movement",
        curriculum_area="T11CS.CD6",
        complexity="L1",
        result_mode="unsupported" if group == "unsupported" else "executable_simulation",
    )


def test_m16_archetype_dong_6_gia_tri():
    assert {a.value for a in M16Archetype} == {
        "explicit_positive",
        "paraphrase_positive",
        "valid_boundary",
        "near_miss_gap",
        "cross_family_recovery",
        "authority_control",
    }
    assert len(M16Archetype) == 6


def test_m16_dataset_version_hang_so():
    assert M16_DATASET_VERSION == "m16-v1"


def test_admission_bat_loi_expected_family_la():
    exp = M16Expectation(
        archetype=M16Archetype.EXPLICIT_POSITIVE,
        expected_family="khong_ton_tai_family",
        expected_initial_route="algorithm.bubble_sort",
        expected_gate=None,
        expected_error_code=None,
        analyze_mechanism_expected=None,
    )
    item = EvalItem(**_valid_base_kwargs("t-family-la"), m16=exp)
    errs = check_m16_admission(item)
    assert any("expected_family" in e for e in errs), errs


def test_admission_bat_loi_positive_thieu_route():
    exp = M16Expectation(
        archetype=M16Archetype.EXPLICIT_POSITIVE,
        expected_family=FamilyId.COMPARISON_SORT.value,
        expected_initial_route=None,
        expected_gate=None,
        expected_error_code=None,
        analyze_mechanism_expected=None,
    )
    item = EvalItem(**_valid_base_kwargs("t-positive-no-route"), m16=exp)
    errs = check_m16_admission(item)
    assert any("expected_initial_route" in e for e in errs), errs


def test_admission_positive_group_unsupported_khong_bat_buoc_route():
    """archetype positive nhưng group=unsupported (vd recovery thất bại → honest
    gap) — brief: bắt buộc route CHỈ 'với group supported'."""
    exp = M16Expectation(
        archetype=M16Archetype.CROSS_FAMILY_RECOVERY,
        expected_family=FamilyId.COMPARISON_SORT.value,
        expected_initial_route=None,
        expected_gate="route_mechanism",
        expected_error_code="route_mechanism_family_mismatch",
        analyze_mechanism_expected=None,
        notes="Route sau reclassify vẫn mismatch family — honest gap.",
    )
    item = EvalItem(**_valid_base_kwargs("t-recovery-fail", group="unsupported"), m16=exp)
    errs = check_m16_admission(item)
    assert not any("expected_initial_route" in e for e in errs), errs


def test_admission_bat_loi_mechanism_ngoai_2_family_exposed():
    exp = M16Expectation(
        archetype=M16Archetype.EXPLICIT_POSITIVE,
        expected_family=FamilyId.GRAPH_TRAVERSAL.value,
        expected_initial_route="network.packet_routing",
        expected_gate=None,
        expected_error_code=None,
        analyze_mechanism_expected="graph_traversal.unweighted_hop_bfs",
    )
    item = EvalItem(**_valid_base_kwargs("t-mech-outside"), m16=exp)
    errs = check_m16_admission(item)
    assert any("analyze_mechanism_expected" in e for e in errs), errs


def test_admission_mechanism_hop_le_cho_2_family_exposed():
    cases = (
        (FamilyId.COMPARISON_SORT.value, "comparison_sort.adjacent_compare_swap"),
        (
            FamilyId.POSITIONAL_REPRESENTATION.value,
            "positional_representation.binary_positional_weights",
        ),
    )
    for i, (family, mech) in enumerate(cases):
        exp = M16Expectation(
            archetype=M16Archetype.EXPLICIT_POSITIVE,
            expected_family=family,
            expected_initial_route="algorithm.bubble_sort",
            expected_gate=None,
            expected_error_code=None,
            analyze_mechanism_expected=mech,
        )
        item = EvalItem(**_valid_base_kwargs(f"t-mech-ok-{i}"), m16=exp)
        errs = check_m16_admission(item)
        assert not any("analyze_mechanism_expected" in e for e in errs), errs


def test_admission_bat_loi_unsupported_thieu_gate_lan_notes():
    exp = M16Expectation(
        archetype=M16Archetype.NEAR_MISS_GAP,
        expected_family=FamilyId.COMPARISON_SORT.value,
        expected_initial_route=None,
        expected_gate=None,
        expected_error_code=None,
        analyze_mechanism_expected=None,
        notes="",
    )
    item = EvalItem(**_valid_base_kwargs("t-unsupported-no-reason", group="unsupported"), m16=exp)
    errs = check_m16_admission(item)
    assert any("expected_gate" in e and "notes" in e for e in errs), errs


def test_admission_unsupported_co_gate_hoac_notes_thi_qua():
    exp_gate = M16Expectation(
        archetype=M16Archetype.NEAR_MISS_GAP,
        expected_family=FamilyId.COMPARISON_SORT.value,
        expected_initial_route=None,
        expected_gate="mechanism",
        expected_error_code="gate_mechanism_ownership",
        analyze_mechanism_expected=None,
    )
    item_gate = EvalItem(
        **_valid_base_kwargs("t-unsupported-gate", group="unsupported"), m16=exp_gate
    )
    assert check_m16_admission(item_gate) == []

    exp_notes = M16Expectation(
        archetype=M16Archetype.NEAR_MISS_GAP,
        expected_family=FamilyId.COMPARISON_SORT.value,
        expected_initial_route=None,
        expected_gate=None,
        expected_error_code=None,
        analyze_mechanism_expected=None,
        notes="Đề vượt DSL v1 — không có primitive biểu diễn được yêu cầu.",
    )
    item_notes = EvalItem(
        **_valid_base_kwargs("t-unsupported-notes", group="unsupported"), m16=exp_notes
    )
    assert check_m16_admission(item_notes) == []


def test_admission_thieu_m16_la_vi_pham():
    item = EvalItem(**_valid_base_kwargs("t-no-m16"))
    errs = check_m16_admission(item)
    assert any("m16" in e for e in errs), errs


def test_admission_ke_thua_luat_cu():
    """Vi phạm luật kết nạp CŨ (pedagogical_rationale mơ hồ) vẫn bị bắt qua
    check_m16_admission — hàm mới BỔ SUNG, không thay thế luật cũ."""
    kwargs = _valid_base_kwargs("t-old-rule-violation")
    kwargs["pedagogical_rationale"] = "qua loa"
    exp = M16Expectation(
        archetype=M16Archetype.EXPLICIT_POSITIVE,
        expected_family=FamilyId.COMPARISON_SORT.value,
        expected_initial_route="algorithm.bubble_sort",
        expected_gate=None,
        expected_error_code=None,
        analyze_mechanism_expected=None,
    )
    item = EvalItem(**kwargs, m16=exp)
    errs = check_m16_admission(item)
    assert any("pedagogical_rationale" in e for e in errs), errs


def test_evalitem_cu_khong_m16_van_dung_duoc():
    """Backward: EvalItem không khai m16 vẫn tạo được bình thường, mặc định None."""
    item = EvalItem("z-backward", "Đề không có m16.", "specialized", "algorithm.find_max")
    assert item.m16 is None


def test_dataset_lich_su_khong_bi_sua_qua_fingerprint():
    assert len(DATASET) == 30
    assert frozen_dataset_fingerprint() == _FROZEN_FINGERPRINT_PIN
