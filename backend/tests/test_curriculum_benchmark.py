# -*- coding: utf-8 -*-
"""WAVE 2 — BENCHMARK CHƯƠNG TRÌNH HỌC LÀ THƯỚC ĐO CHÍNH.

Ba điều được khoá ở đây:

  1. **Tầng ổn định KHÔNG nói về hiện thực.** Case mô tả kiến thức và cơ chế;
     "hệ làm được chưa" phải DẪN XUẤT từ registry lúc chạy. Nhờ vậy thêm một
     target mới không buộc phải sửa benchmark.
  2. **Phép biến hình giữ nguyên phán quyết.** Đổi tên người, đổi thiết bị, đổi
     số, đảo dãy, thêm khoảng trắng — cơ chế không đổi thì phân loại không đổi.
  3. **Dataset 30 case cũ đổi VAI, không bị xoá.** Nó thành hồi quy sáng tác AI
     (`LEGACY_AI_COMPOSITION_REGRESSION`), không còn là thước đo phủ chương trình.
"""

from __future__ import annotations

import pytest

from app.evaluation.curriculum_schema import (
    CapabilityStatus,
    CurriculumClassification,
    DomainScope,
    Simulatability,
    capability_status,
    check_anchor,
    expected_outcome,
    unit_codes,
)
from app.evaluation.metamorphic import TRANSFORMS, variants
from app.evaluation.datasets.curriculum import CURRICULUM_ITEMS
from app.simulation.catalog import CATALOG

KNOWN = frozenset(CATALOG.keys())


# ── 1. TẦNG ỔN ĐỊNH vs TẦNG DẪN XUẤT ─────────────────────────────────────────

class TestTangOnDinh:
    def test_trang_thai_nang_luc_DAN_XUAT_tu_registry_khong_viet_tay(self):
        """Cùng một case, registry đổi thì kỳ vọng đổi theo — đó là cả điểm."""
        cls = CurriculumClassification(
            grade="12-ICT", domain_scope=DomainScope.THPT_INFORMATICS,
            simulatability=Simulatability.INTERACTIVE_MODEL)

        # Hôm nay: chưa có target màu RGB ⇒ phải từ chối trung thực.
        today = capability_status("web.rgb_color", KNOWN)
        assert today is CapabilityStatus.UNIMPLEMENTED
        assert expected_outcome(cls, today) == "capability_gap"

        # Ngày mai: giả lập registry ĐÃ có target ấy ⇒ cùng case đòi spec hợp lệ.
        tomorrow = capability_status("web.rgb_color", KNOWN | {"web.rgb_color"})
        assert tomorrow is CapabilityStatus.SUPPORTED
        assert expected_outcome(cls, tomorrow) == "valid_deterministic_spec"

    def test_ngoai_pham_vi_thi_TU_CHOI_du_he_co_nang_luc(self):
        """Phán quyết phạm vi đứng TRƯỚC năng lực: có làm được cũng không làm."""
        cls = CurriculumClassification(
            grade="10", domain_scope=DomainScope.OUT_OF_SCOPE,
            simulatability=Simulatability.INTERACTIVE_MODEL)
        st = capability_status("algorithm.find_max", KNOWN)
        assert st is CapabilityStatus.SUPPORTED
        assert expected_outcome(cls, st) == "refuse_out_of_scope"

    def test_chi_giai_thich_thi_KHONG_dung_mo_phong(self):
        for kind in (Simulatability.EXPLANATION_ONLY, Simulatability.NOT_SIMULATION_SUITABLE):
            cls = CurriculumClassification(
                grade="10", domain_scope=DomainScope.THPT_INFORMATICS, simulatability=kind)
            assert expected_outcome(cls, capability_status("algorithm.find_max", KNOWN)) \
                == "explanation_only"

    def test_boi_canh_mon_khac_KHONG_bi_xep_ngoai_pham_vi(self):
        """`ADJACENT_CONTEXT` tồn tại để không từ chối oan: "đếm số cây cao hơn
        2m" mang vỏ sinh học nhưng cơ chế là `count_if`."""
        cls = CurriculumClassification(
            grade="10", domain_scope=DomainScope.ADJACENT_CONTEXT,
            simulatability=Simulatability.MEANINGFUL_TRACE)
        assert expected_outcome(cls, capability_status("algorithm.count_if", KNOWN)) \
            == "valid_deterministic_spec"

    def test_case_khong_neo_target_thi_la_chua_ho_tro(self):
        assert capability_status(None, KNOWN) is CapabilityStatus.UNIMPLEMENTED


# ── 2. PHÉP BIẾN HÌNH ────────────────────────────────────────────────────────

class TestBienHinh:
    def test_moi_phep_deu_TAT_DINH(self):
        text = "Có 8 bạn: An 7,5; Bình 9; Chi 6. Đếm số bạn đạt từ 8 trở lên."
        for t in TRANSFORMS:
            assert t.apply(text) == t.apply(text), t.name

    def test_doi_ten_nguoi_khong_dung_toi_co_che(self):
        text = "Dãy điểm của An, Bình, Chi. Tìm điểm lớn nhất."
        got = dict(variants(text))["rename_people"]
        assert "An" not in got and "Minh" in got
        assert "lớn nhất" in got  # cơ chế còn nguyên

    def test_doi_so_GIU_NGUYEN_0_va_1(self):
        """Ở đề logic/nhị phân, 0 và 1 là GIÁ TRỊ BIT — đổi chúng là đổi cơ chế."""
        got = dict(variants("Cổng AND với đầu vào 1 và 0 cho đầu ra bằng 0."))
        assert "shift_numbers" not in got  # không có gì để đổi ⇒ không sinh biến thể

        got2 = dict(variants("Cho dãy 7, 9, 6. Tìm số lớn nhất."))["shift_numbers"]
        assert "8, 10, 7" in got2

    def test_dao_day_chi_dung_cho_day_tu_3_so(self):
        assert "reverse_sequence" not in dict(variants("Đổi 13 sang nhị phân."))
        got = dict(variants("Cho dãy 7, 9, 6, 10. Tìm số lớn nhất."))["reverse_sequence"]
        assert "10, 6, 9, 7" in got

    def test_bien_the_TRUNG_ban_goc_bi_loai(self):
        """Nếu giữ lại, con số phủ trông to hơn thực tế mà không kiểm thêm gì."""
        for name, text in variants("Cổng AND."):
            assert text != "Cổng AND.", name

    def test_moi_de_chuong_trinh_sinh_duoc_it_nhat_mot_bien_the(self):
        """Đề nào không biến hình được thì phép đo không nói gì về nó."""
        barren = [i.id for i in CURRICULUM_ITEMS if not variants(i.text)]
        assert barren == [], f"đề không sinh được biến thể nào: {barren}"


# ── 3. DATASET CŨ ĐỔI VAI ────────────────────────────────────────────────────

class TestDatasetCu:
    def test_dataset_30_case_van_con_va_duoc_khai_la_LEGACY(self):
        from app.evaluation.dataset import DATASET, LEGACY_AI_COMPOSITION_REGRESSION

        assert len(DATASET) == 30, "dataset lịch sử phải giữ nguyên để so sánh được"
        assert LEGACY_AI_COMPOSITION_REGRESSION is DATASET

    def test_benchmark_chuong_trinh_neo_vao_SGK_chu_khong_vao_target(self):
        """Mọi case chương trình phải có neo SGK. Không có neo thì nó không đo
        được phủ chương trình, chỉ đo được hệ tự chạy lại chính mình."""
        thieu = [i.id for i in CURRICULUM_ITEMS if not i.curriculum_area]
        assert thieu == [], f"case thiếu neo chương trình: {thieu}"

    def test_moi_case_chuong_trinh_khai_muc_tieu_hoc_tap(self):
        thieu = [i.id for i in CURRICULUM_ITEMS if not i.learning_objective.strip()]
        assert thieu == [], f"case thiếu mục tiêu học tập: {thieu}"


# ── 5. TRƯỜNG NEO PHẢI ĐẾM ĐƯỢC ──────────────────────────────────────────────

class TestTruongNeo:
    """Phép đo phủ chương trình đã sai HAI lần vì trường neo là văn xuôi.

    Cả hai lần đều sai theo hướng CÓ LỢI (14 đơn vị thay vì 8; T10.CD1 12 case
    thay vì 9), nên không có gì trong hệ tự lộ ra. Bốn test dưới khoá cả hai.
    """

    def _items_phai_co_neo(self):
        """Pool chịu luật kết nạp + mọi case ĐÃ khai neo ở bất kỳ pool nào.

        30 case `DATASET` lịch sử KHÔNG có trường neo và bị đóng băng có chủ đích
        (`datasets/__init__.py`) — bắt chúng ở đây là bắt sai đối tượng và sẽ
        đẩy người sửa tới chỗ phá baseline. Nhưng case lịch sử nào có khai neo
        thì vẫn phải khai đúng dạng.
        """
        from app.evaluation.datasets import NEW_POOLS, POOLS

        can_neo = {id(i) for pool in NEW_POOLS.values() for i in pool}
        out = []
        for pool in POOLS.values():
            for i in pool:
                if id(i) in can_neo or i.curriculum_area:
                    out.append(i)
        return out

    def test_moi_truong_neo_hoac_la_MA_hoac_tu_khai_KHONG_NEO(self):
        xau = sorted({f"{i.id}: {loi}" for i in self._items_phai_co_neo()
                      if (loi := check_anchor(i.curriculum_area))})
        assert xau == [], (
            "trường neo là văn xuôi — vừa không phải mã, vừa không khai "
            "NOT_ANCHORED, nên phép đếm phủ sẽ đếm nó như một đơn vị:\n"
            + "\n".join(xau))

    def test_khai_KHONG_NEO_thi_KHONG_ghi_cong_du_ben_trong_co_nhac_ma(self):
        """Đây chính là lỗi lần 2: câu giải thích ranh giới bị đọc thành tuyên bố phủ."""
        area = "NOT_ANCHORED — T10.CD1 chỉ phủ đổi sang NHỊ PHÂN; hệ 16 ngoài anchor"
        assert unit_codes(area) == ()
        assert check_anchor(area) is None  # hợp lệ, chỉ là không tính vào phủ

    def test_neo_GHEP_tinh_ca_hai_don_vi(self):
        assert unit_codes("T11.CD4 / T10.CD2") == ("T11.CD4", "T10.CD2")

    def test_neo_co_ghi_chu_trong_ngoac_van_tinh(self):
        assert unit_codes("T11CS.CD6 (biến thể sắp xếp — cơ chế chưa có engine)") \
            == ("T11CS.CD6",)

    def test_moi_don_vi_duoc_phu_phai_co_it_nhat_3_case(self):
        """Một đơn vị chỉ có 1 case không phủ được nó — nó chỉ chạm vào nó.

        Ngưỡng 3 là ngưỡng của §2A. Guard này khoá con số phủ khỏi việc tụt đi
        âm thầm khi ai đó xoá case hoặc đổi neo.
        """
        from collections import Counter

        from app.evaluation.datasets import NEW_POOLS, POOLS as ALL_POOLS
        from app.evaluation.product_scope import ProductScope, scope_of

        pools = {n: p for n, p in ALL_POOLS.items() if n in NEW_POOLS or n == "thesis"}
        dem: Counter[str] = Counter()
        thay: set[str] = set()
        for pool in pools.values():
            for i in pool:
                if i.id in thay:
                    continue
                thay.add(i.id)
                if scope_of(i.id) is not ProductScope.PUBLIC_THPT_INFORMATICS:
                    continue
                for code in unit_codes(i.curriculum_area):
                    dem[code] += 1

        mong = sorted(f"{u}={n}" for u, n in dem.items() if n < 3)
        assert mong == [], f"đơn vị chương trình mỏng (<3 case): {', '.join(mong)}"
        assert len(dem) >= 8, f"số đơn vị được phủ tụt xuống {len(dem)}"

    def test_W4_moi_target_deu_join_duoc_ve_don_vi_chuong_trinh(self):
        """Join target ↔ đơn vị phải DẪN XUẤT từ case, không chép tay.

        Catalog ghi neo bằng số BÀI ("T10 CĐ5 · T11CS B17"), benchmark ghi bằng
        mã CHỦ ĐỀ ("T10.CD5") — hai hệ ký hiệu khác nhau nên join thẳng là bịa.
        Cầu nối có sẵn: mỗi case khai CẢ mã đơn vị LẪN target.

        Ngoại lệ DUY NHẤT được phép, và phải nêu lý do: `binary.base_conversion`
        phủ cơ số 8/16, mà chính benchmark đã khai chúng NOT_ANCHORED (hợp đồng
        engine {2,8,10,16} rộng hơn neo SGK — SGK chỉ neo nhị phân).
        """
        from collections import defaultdict

        from app.evaluation.datasets import NEW_POOLS, POOLS as ALL_POOLS
        from app.simulation.catalog import CATALOG

        MIEN_TRU = {"binary.base_conversion"}

        pools = {n: p for n, p in ALL_POOLS.items() if n in NEW_POOLS or n == "thesis"}
        by_target: dict[str, set[str]] = defaultdict(set)
        thay: set[str] = set()
        for pool in pools.values():
            for i in pool:
                if i.id in thay or not i.expect_simulation_id:
                    continue
                thay.add(i.id)
                for code in unit_codes(i.curriculum_area):
                    by_target[i.expect_simulation_id].add(code)

        thieu = sorted(set(CATALOG) - set(by_target) - MIEN_TRU)
        assert thieu == [], (
            "target không có case benchmark nào neo tới ⇒ không nói được nó phủ "
            f"đơn vị chương trình nào: {thieu}")

        het_mien_tru = sorted(MIEN_TRU & set(by_target))
        assert het_mien_tru == [], (
            f"target nay ĐÃ có bằng chứng phủ — xoá khỏi MIEN_TRU: {het_mien_tru}")

        la = sorted(set(by_target) - set(CATALOG))
        assert la == [], f"case neo tới target không có trong catalog: {la}"

    def test_van_xuoi_thuan_bi_TU_CHOI(self):
        """Guard phải đỏ được — đây là dạng chuỗi đã gây ra cả hai lần đếm sai."""
        assert check_anchor("ngoài phạm vi công khai Tin học THPT — không anchor SGK")
        assert check_anchor("Ngoài chương trình Tin học (Toán hình)")
        assert check_anchor("NOT_ANCHORED")  # khai mà không nói vì sao
        assert check_anchor("") and check_anchor(None)


# ── 4. WAVE 2C — TÁCH FIXTURE NỘI BỘ KHỎI PHẠM VI SẢN PHẨM ───────────────────

class TestPhamViSanPham:
    """Case chứng minh ENGINE và case chứng minh SẢN PHẨM không được trộn số."""

    def test_moi_case_ngoai_Tin_hoc_deu_duoc_khai_va_co_LY_DO(self):
        import re

        from app.evaluation.datasets import capability, cross_domain, m16_catalog, thesis
        from app.evaluation.product_scope import ProductScope, reason_of, scope_of

        # Dấu hiệu bề mặt của môn khác — dùng để PHÁT HIỆN, không dùng để phán.
        other_subject = re.compile(
            r"tam giác|hình học|diện tích|chu vi|quang hợp|phản ứng|hoá học|"
            r"vật lí|quỹ tích|đường cao", re.IGNORECASE)

        undeclared: list[str] = []
        # `m16_catalog` PHẢI có mặt: nó là pool catalog-wide lớn nhất và chính nó
        # chứa case dựng tam giác — bỏ ra là guard không bao giờ chạm tới.
        for mod in (cross_domain, capability, thesis, m16_catalog):
            for value in vars(mod).values():
                if not (isinstance(value, list) and value and hasattr(value[0], "id")):
                    continue
                for item in value:
                    if not other_subject.search(item.text):
                        continue
                    if scope_of(item.id) is ProductScope.PUBLIC_THPT_INFORMATICS:
                        undeclared.append(f"{item.id}: {item.text[:60]}")
                    else:
                        assert reason_of(item.id), f"{item.id}: khai loại mà không nói vì sao"

        assert undeclared == [], (
            "case mang bề mặt môn khác nhưng vẫn tính là nội dung Tin học công khai:\n"
            + "\n".join(undeclared))

    def test_fixture_noi_bo_KHONG_duoc_tinh_vao_phu_chuong_trinh(self):
        """Phủ chương trình chỉ đếm case Tin học công khai. Nếu một fixture engine
        lọt vào, con số phủ nói dối theo hướng có lợi."""
        from app.evaluation.product_scope import ProductScope, scope_of

        lot = [i.id for i in CURRICULUM_ITEMS
               if scope_of(i.id) is not ProductScope.PUBLIC_THPT_INFORMATICS]
        assert lot == [], f"fixture nội bộ nằm trong pool chương trình: {lot}"

    def test_ly_do_phai_noi_ve_NOI_DUNG_khong_phai_ve_cho_dat_file(self):
        from app.evaluation.product_scope import SCOPE_OVERRIDES

        for case_id, (_, reason) in SCOPE_OVERRIDES.items():
            assert len(reason) > 60, f"{case_id}: lý do quá ngắn để kiểm chứng"
            for lazy in ("nằm trong pool", "vốn ở", "theo lịch sử"):
                assert lazy not in reason, f"{case_id}: lý do né nội dung"
