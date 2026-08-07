# -*- coding: utf-8 -*-
"""M8-PRE (S1): pool đề MỚI — và bằng chứng baseline lịch sử KHÔNG bị đụng.

Điều quan trọng nhất ở file này: `test_dataset_lich_su_van_dong_bang` — mọi case
mới PHẢI nằm ngoài DATASET, nếu không số liệu M7.13/M7.14/M7.14T mất khả năng
so sánh. (test_evaluation.py::test_dataset_du_30_de_3_nhom khoá số lượng; ở đây
khoá thêm rằng các pool mới KHÔNG rò rỉ vào đó.)
"""

from app.evaluation.dataset import DATASET
from app.evaluation.datasets import (
    COMPLEXITY_LEVELS,
    NEW_POOLS,
    POOLS,
    RESULT_MODES,
    check_admission,
    get_pool,
)
from app.evaluation.datasets.thesis import FLAGSHIP_IDS, FLAGSHIP_ITEMS
from app.evaluation.harness import select_suite


def test_dataset_lich_su_van_dong_bang():
    """Case mới KHÔNG được chèn vào baseline hồi quy."""
    assert len(DATASET) == 30
    historical = {it.id for it in DATASET}
    for name, pool in NEW_POOLS.items():
        new_ids = {it.id for it in pool}
        assert not (new_ids & historical), f"pool {name} rò rỉ vào DATASET"


def test_moi_case_moi_qua_duoc_luat_ket_nap():
    """Rationale mơ hồ → loại case. Luật kết nạp phải được THỰC THI, không chỉ ghi trong docs."""
    errs: list[str] = []
    for pool in NEW_POOLS.values():
        for item in pool:
            errs += check_admission(item)
    assert not errs, "Vi phạm luật kết nạp:\n" + "\n".join(errs)


def test_metadata_moi_la_optional_baseline_giu_mac_dinh():
    """30 case lịch sử không khai metadata → giữ mặc định, không vỡ."""
    it = DATASET[0]
    assert it.complexity == "L1"
    assert it.result_mode is None
    assert it.learning_objective == "" and it.pedagogical_rationale == ""
    assert it.curriculum_area is None


def test_flagship_khong_mutate_dataset_lich_su():
    """Bộ flagship gắn nhãn cho case lịch sử bằng BẢN SAO (dataclasses.replace).
    Item gốc trong DATASET phải vẫn mang giá trị mặc định — nếu không, benchmark
    lịch sử đã bị sửa ngầm."""
    by_id = {it.id: it for it in DATASET}
    for hid in ("a-and", "a-packet", "d-webbuild", "c-geo-complex"):
        origin = by_id[hid]
        assert origin.complexity == "L1", f"{hid} trong DATASET bị sửa"
        assert origin.result_mode is None, f"{hid} trong DATASET bị sửa"
        assert origin.pedagogical_rationale == ""
    # nhưng bản flagship thì CÓ nhãn đúng
    flag = {it.id: it for it in FLAGSHIP_ITEMS}
    assert flag["a-packet"].complexity == "L2"
    assert flag["c-geo-complex"].result_mode == "unsupported"
    assert flag["a-and"] is not by_id["a-and"]


def test_flagship_dung_12_case_va_khong_trung():
    assert len(FLAGSHIP_IDS) == 12
    assert len(set(FLAGSHIP_IDS)) == 12
    assert [it.id for it in FLAGSHIP_ITEMS] == list(FLAGSHIP_IDS)


def test_flagship_phu_du_cac_tinh_chat_bat_buoc():
    """Bộ flagship phải chứng minh các tính chất KHÁC NHAU, không nhồi biến thể logic."""
    ids = set(FLAGSHIP_IDS)
    assert "cap-bubble" in ids                    # sắp xếp (lỗ hổng bằng chứng cũ)
    assert "c-geo-complex" in ids                 # từ chối trung thực (capability_gap)
    assert "xd-order-workflow" in ids             # luồng dữ liệu chạy được (S2)
    assert "d-webstatic" in ids                   # trung thực scene-mode (tĩnh vẫn tĩnh)
    assert {"a-and", "b-xor"} <= ids              # cặp specialized ↔ generic CÓ CHỦ ĐÍCH
    # không nhồi biến thể boolean: đúng 2 case boolean trong flagship
    boolean_like = ids & {"a-and", "b-xor", "b-or", "b-not", "b-and3", "b-xor2", "b-orlamp"}
    assert len(boolean_like) == 2

    modes = {it.result_mode for it in FLAGSHIP_ITEMS if it.result_mode}
    assert "executable_simulation" in modes
    assert "interactive_visualization" in modes
    # practice_activity CHƯA có producer → không được tuyên bố trong flagship
    assert "practice_activity" not in modes


def test_flagship_co_L3_va_khong_toan_L1():
    levels = [it.complexity for it in FLAGSHIP_ITEMS]
    assert "L3" in levels, "flagship phải có ít nhất một cảnh đa giai đoạn"
    assert "L4" in levels or any(it.group == "unsupported" for it in FLAGSHIP_ITEMS)
    assert levels.count("L1") < len(levels) / 2, "flagship không được toàn case nguyên tử"


def test_sorting_co_bang_chung_trong_capability_pool():
    """Trước M8-PRE: bubble_sort/insertion_sort có engine nhưng KHÔNG case nào."""
    expected = {it.expect_simulation_id for it in get_pool("capability")}
    assert "algorithm.bubble_sort" in expected
    assert "algorithm.insertion_sort" in expected


def test_metadata_trong_vung_gia_tri_hop_le():
    for pool in NEW_POOLS.values():
        for it in pool:
            assert it.complexity in COMPLEXITY_LEVELS
            assert it.result_mode in RESULT_MODES


def test_select_suite_loc_duoc_tren_pool_moi():
    """Harness KHÔNG cần sửa: select_suite đã nhận pool inject sẵn."""
    pool = get_pool("capability")
    assert select_suite("full", pool) == pool
    l3 = select_suite("L3", pool)
    assert l3 and all("L3" in it.tags for it in l3)
    assert select_suite("smoke_v2", pool)


def test_pools_dang_ky_du():
    # M16 Task 4: pool "m16" (catalog-wide eval) đăng ký thêm vào POOLS.
    assert set(POOLS) == {"regression", "curriculum", "capability", "cross_domain", "thesis", "m16"}
    assert get_pool("regression") is DATASET


# ── W4B-1B — độ phủ target TƯỜNG MINH cho catalog ────────────────────────────
# Reconciliation W4B-1B: inventory runtime (không phải grep) cho 19/22 target có
# `expect_simulation_id`. Hai ca dưới đóng hai lỗ; lỗ thứ ba
# (`binary.base_conversion`) CỐ Ý để mở — xem artifact w4b1b, nó vướng mâu thuẫn
# chính sách với ba ca từ chối hex/bát phân đang tồn tại.
W4B1B_NEW_CASES = {
    "cur-t11-selection-sort": "algorithm.selection_sort",
    "cur-t11-graph-traversal-bfs": "network.graph_traversal",
}


def test_w4b1b_ca_moi_nam_dung_pool_mutable_va_khong_dung_baseline():
    """Ca mới phải ở `curriculum` — KHÔNG chèn vào regression/m16 frozen."""
    curriculum_ids = {it.id for it in get_pool("curriculum")}
    for case_id in W4B1B_NEW_CASES:
        assert case_id in curriculum_ids, f"{case_id} không nằm ở pool curriculum"
    frozen = {it.id for it in DATASET} | {it.id for it in get_pool("m16")}
    assert not (set(W4B1B_NEW_CASES) & frozen), "ca mới rò rỉ vào pool đóng băng"


def test_w4b1b_ca_moi_du_hop_dong_va_target_co_that_trong_catalog():
    """id duy nhất · target có thật · learning_objective không rỗng."""
    from app.simulation.catalog import CATALOG

    catalog_ids = set(CATALOG)
    by_id: dict[str, list[str]] = {}
    for name, pool in POOLS.items():
        for it in pool:
            by_id.setdefault(it.id, []).append(name)

    for case_id, target in W4B1B_NEW_CASES.items():
        item = next(it for it in get_pool("curriculum") if it.id == case_id)
        assert item.expect_simulation_id == target
        assert target in catalog_ids, f"{target} không có trong catalog"
        assert item.group == "specialized"
        assert len(item.learning_objective.strip()) >= 10
        assert item.text.strip(), "prompt rỗng"
        # id không được trùng với bất kỳ ca nào ở pool khác
        assert by_id[case_id] == ["curriculum"], f"{case_id} trùng id ở {by_id[case_id]}"


def test_w4b1b_runner_chon_duoc_dung_ca_bang_case_id():
    """§G — CHÍNH code path của `live.py`: get_pool → select_suite → lọc theo id.

    Chứng minh OFFLINE (0 API call): `live.py` từ chối chạy khi thiếu
    `ALLOW_LIVE_AI`, nên không thể dùng CLI để chứng minh selection mà không
    tiêu quota. Ở đây gọi đúng ba bước mà `live.py:265-268` gọi.

    Ràng buộc thật của CLI, khoá luôn ở đây: `--case` lọc SAU `--suite`, và
    suite mặc định `smoke` không chọn gì từ `curriculum` — nên lệnh đúng phải là
    `--dataset curriculum --suite full --case <id>`.
    """
    pool = get_pool("curriculum")
    for case_id in W4B1B_NEW_CASES:
        chosen = [it for it in select_suite("full", pool) if it.id == case_id]
        assert len(chosen) == 1, f"--suite full --case {case_id} không resolve đúng 1 ca"
        # và đúng cái bẫy: suite mặc định KHÔNG chọn được
        assert not [it for it in select_suite("smoke", pool) if it.id == case_id], (
            "ca curriculum không nên tự nhiên nằm trong suite smoke"
        )


def test_w4b1b_do_phu_target_tuong_minh_dung_bang_so_thuc():
    """Khoá con số THẬT, không phải nhãn mong muốn."""
    from app.simulation.catalog import CATALOG

    catalog_ids = set(CATALOG)
    covered = {it.expect_simulation_id for pool in POOLS.values() for it in pool
               if it.expect_simulation_id}
    explicit = catalog_ids & covered
    missing = catalog_ids - covered
    assert len(catalog_ids) == 22
    assert len(explicit) == 21, f"độ phủ tường minh {len(explicit)}/22, thiếu {sorted(missing)}"
    assert missing == {"binary.base_conversion"}, (
        "chỉ base_conversion được phép còn thiếu — xem artifact W4B-1B"
    )
