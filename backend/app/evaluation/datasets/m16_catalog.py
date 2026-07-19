# -*- coding: utf-8 -*-
"""Pool M16 — bộ đề đánh giá ĐẦU-CUỐI toàn danh mục (design M16 §6).

Phủ 14 concrete target / 8 capability family với kỳ vọng CÓ CẤU TRÚC máy-đọc
(`m16=M16Expectation`, Task 1): family/route/gate/error_code/mechanism canonical.
Sáu archetype (M16Archetype): explicit_positive, paraphrase_positive,
valid_boundary, near_miss_gap, cross_family_recovery, authority_control.

NGUYÊN TẮC ĐẶT KỲ VỌNG (self-review đối chiếu classify.md/analyze.md + gate
pipeline THẬT, không đoán):
- Sorting (bubble/insertion): route ban đầu là TOKEN selector
  "algorithm.comparison_sort" (KHÔNG phải concrete id — token không bao giờ là
  envelope id); target thực dẫn xuất từ analyze_mechanism_expected.
- analyze_mechanism_expected CHỈ đặt cho comparison_sort + positional_representation
  (hai family DUY NHẤT có tín hiệu analyze-exposed — M15 claim boundary;
  check_m16_admission bắt lỗi nếu đặt cho family khác).
- Gate/error_code lấy NGUYÊN VĂN từ app/simulation/error_codes.py + hành vi
  pipeline.py đã đọc: mechanism gate (E4 tầng 1) → gate_mechanism_ownership;
  route-mismatch recovery fail-closed → route_mechanism_family_mismatch; nhánh
  computation gate trả capability_gap KHÔNG kèm error_code (→ expected_error_code
  = None).

M16_REFERENCED_CASES: registry THAM CHIẾU case pool cũ vào coverage matrix M16
(không chép text) — bằng chứng đã live-verified ở milestone trước.

KHÔNG sửa: dataset.py (frozen 30 case), 4 pool cũ (curriculum/capability/
cross_domain/thesis), harness, pipeline.
"""

from __future__ import annotations

from app.evaluation.dataset import EvalItem
from app.evaluation.m16_schema import M16Archetype, M16Expectation
from app.simulation.descriptor import FamilyId

# ── Archetype (rút gọn) ───────────────────────────────────────
EP = M16Archetype.EXPLICIT_POSITIVE
PP = M16Archetype.PARAPHRASE_POSITIVE
VB = M16Archetype.VALID_BOUNDARY
NM = M16Archetype.NEAR_MISS_GAP
CR = M16Archetype.CROSS_FAMILY_RECOVERY
AC = M16Archetype.AUTHORITY_CONTROL

# ── Family id (canonical) ─────────────────────────────────────
SPS = FamilyId.SINGLE_PASS_SCAN.value
IE = FamilyId.INTERVAL_ELIMINATION.value
CS = FamilyId.COMPARISON_SORT.value
BC = FamilyId.BOOLEAN_COMPOSITION.value
PR = FamilyId.POSITIONAL_REPRESENTATION.value
GT = FamilyId.GRAPH_TRAVERSAL.value
LP = FamilyId.LAYERED_PDU_TRANSFORM.value
SPR = FamilyId.STRUCTURAL_PROGRESSIVE_REPRESENTATION.value

# ── Mechanism canonical (namespaced) ──────────────────────────
MECH_BUBBLE = "comparison_sort.adjacent_compare_swap"
MECH_INSERT = "comparison_sort.shift_into_sorted_prefix"
MECH_PARTITION = "comparison_sort.partition_recursive"
MECH_BINW = "positional_representation.binary_positional_weights"
MECH_NONBIN = "positional_representation.non_binary_base"

# ── Token selector sorting (KHÔNG phải simulation_id) ──────────
SORT_TOKEN = "algorithm.comparison_sort"

# ── Error code (nguyên văn ErrorCode) ─────────────────────────
EC_ROUTE_MISMATCH = "route_mechanism_family_mismatch"
EC_MECH_OWN = "gate_mechanism_ownership"


def _item(
    *,
    id: str,
    text: str,
    group: str,
    archetype: M16Archetype,
    family: str,
    route: str | None,
    learning: str,
    rationale: str,
    cap_family: str,
    area: str,
    complexity: str,
    result_mode: str,
    expect: str | None = None,
    semantic: dict | None = None,
    mech: str | None = None,
    gate: str | None = None,
    error_code: str | None = None,
    algorithmic: bool = False,
    recovery: bool = False,
    live: bool = False,
    notes: str = "",
) -> EvalItem:
    """Dựng EvalItem + M16Expectation, gắn tag chuẩn (m16_offline luôn có;
    m16_catalog_live iff live_eligible)."""
    exp = M16Expectation(
        archetype=archetype,
        expected_family=family,
        expected_initial_route=route,
        expected_gate=gate,
        expected_error_code=error_code,
        analyze_mechanism_expected=mech,
        algorithmic_request=algorithmic,
        recovery_route_exists=recovery,
        live_eligible=live,
        notes=notes,
    )
    tags = ("m16_offline",) + (("m16_catalog_live",) if live else ())
    kwargs = dict(
        id=id,
        text=text,
        group=group,
        tags=tags,
        learning_objective=learning,
        pedagogical_rationale=rationale,
        capability_family=cap_family,
        curriculum_area=area,
        complexity=complexity,
        result_mode=result_mode,
        m16=exp,
    )
    if group != "unsupported":
        kwargs["expect_simulation_id"] = expect
    if semantic is not None:
        kwargs["semantic"] = semantic
    return EvalItem(**kwargs)


M16_ITEMS: list[EvalItem] = [
    # ══════════════════════════════════════════════════════════════════
    # PHỤ LỤC B §1 — 14/14 target × 2 supported positive (explicit + paraphrase)
    # ══════════════════════════════════════════════════════════════════

    # ── algorithm.find_max (single_pass_scan) ──
    _item(
        id="m16-findmax-explicit",
        text="Cho dãy 12, 7, 25, 9, 18, 3. Tìm phần tử lớn nhất trong dãy.",
        group="specialized", expect="algorithm.find_max", route="algorithm.find_max",
        archetype=EP, family=SPS,
        cap_family="single_pass_extreme", area="T11CS.CD6", complexity="L1",
        result_mode="executable_simulation",
        learning="Hiểu tìm cực đại là giữ một biến 'lớn nhất tạm' cập nhật qua từng phần tử.",
        rationale=(
            "Cơ chế ẩn: biến GIÁ TRỊ LỚN NHẤT TẠM sống sót qua từng vòng và chỉ đổi khi gặp "
            "phần tử lớn hơn. Học sinh thấy kết quả cuối nhưng không thấy biến đổi ở đâu; "
            "timeline cho xem từng lần so sánh và từng lần cập nhật cực đại."
        ),
    ),
    _item(
        id="m16-findmax-paraphrase",
        text=(
            "Sáu vận động viên cao 165, 172, 158, 180, 169, 174 cm. Lần lượt xét từng người "
            "và luôn GHI NHỚ người CAO NHẤT đã gặp cho tới hết danh sách để biết ai cao nhất."
        ),
        group="specialized", expect="algorithm.find_max", route="algorithm.find_max",
        archetype=PP, family=SPS, live=True,
        cap_family="single_pass_extreme", area="T11CS.CD6", complexity="L1",
        result_mode="executable_simulation",
        learning="Nhận ra cơ chế 'giữ cực đại chạy' qua MÔ TẢ thao tác, không qua tên hàm tìm max.",
        rationale=(
            "Cơ chế ẩn: DUY TRÌ giá trị lớn nhất chạy qua một lượt duyệt — đặc trưng của "
            "find_max. Đề diễn đạt bằng lời ('ghi nhớ người cao nhất đã gặp') để kiểm hệ định "
            "tuyến theo cơ chế duyệt-giữ-cực-trị, không theo từ khóa 'lớn nhất'."
        ),
    ),

    # ── algorithm.find_min (single_pass_scan) ──
    _item(
        id="m16-findmin-explicit",
        text="Cho dãy 45, 12, 78, 6, 33, 20. Tìm phần tử nhỏ nhất trong dãy.",
        group="specialized", expect="algorithm.find_min", route="algorithm.find_min",
        archetype=EP, family=SPS, live=True,
        cap_family="single_pass_extreme", area="T11CS.CD6", complexity="L1",
        result_mode="executable_simulation",
        learning="Hiểu tìm cực tiểu là đối ngẫu của tìm cực đại — giữ 'nhỏ nhất tạm'.",
        rationale=(
            "Cơ chế ẩn: biến NHỎ NHẤT TẠM chỉ đổi khi gặp phần tử nhỏ hơn; cùng khuôn duyệt "
            "một lượt như find_max nhưng đảo chiều so sánh. Timeline làm lộ từng lần cập nhật."
        ),
    ),
    _item(
        id="m16-findmin-paraphrase",
        text=(
            "Nhiệt độ sáu ngày lần lượt 18, 15, 21, 12, 19, 14 độ C. Duyệt lần lượt từng ngày "
            "và luôn nhớ giá trị THẤP NHẤT gặp được để tìm ngày lạnh nhất."
        ),
        group="specialized", expect="algorithm.find_min", route="algorithm.find_min",
        archetype=PP, family=SPS,
        cap_family="single_pass_extreme", area="T11CS.CD6", complexity="L1",
        result_mode="executable_simulation",
        learning="Nhận ra cơ chế giữ-cực-tiểu-chạy qua mô tả 'nhớ giá trị thấp nhất gặp được'.",
        rationale=(
            "Cơ chế ẩn: DUY TRÌ giá trị nhỏ nhất qua một lượt duyệt — đặc trưng find_min. Câu "
            "chữ né tên hàm để kiểm định tuyến theo cơ chế duyệt-giữ-cực-trị thay vì từ khóa."
        ),
    ),

    # ── algorithm.sum_if (single_pass_scan) ──
    _item(
        id="m16-sumif-explicit",
        text="Cho các số 6, 11, 4, 9, 15, 3. Tính tổng các số lớn hơn 5.",
        group="specialized", expect="algorithm.sum_if", route="algorithm.sum_if",
        archetype=EP, family=SPS, live=True,
        cap_family="conditional_accumulator", area="T10.CD5", complexity="L2",
        result_mode="executable_simulation",
        learning="Hiểu tổng có điều kiện là một biến tích lũy chỉ cộng khi phần tử thỏa điều kiện.",
        rationale=(
            "Cơ chế ẩn: biến TỔNG TÍCH LŨY và điều kiện lọc quyết định có cộng phần tử hiện tại "
            "hay không. Học sinh mới lập trình vấp đúng chỗ này — thấy kết quả cuối mà không "
            "thấy biến tổng nhích lên ở mỗi phần tử thỏa điều kiện."
        ),
    ),
    _item(
        id="m16-sumif-paraphrase",
        text=(
            "Các khoản quyên góp của lớp lần lượt 20, 50, 10, 80, 35 nghìn đồng. Duyệt từng "
            "khoản và CỘNG DỒN những khoản từ 30 nghìn trở lên để biết tổng các khoản lớn."
        ),
        group="specialized", expect="algorithm.sum_if", route="algorithm.sum_if",
        archetype=PP, family=SPS,
        cap_family="conditional_accumulator", area="T10.CD5", complexity="L2",
        result_mode="executable_simulation",
        learning="Nhận ra tổng-có-điều-kiện qua mô tả 'cộng dồn những khoản thỏa điều kiện'.",
        rationale=(
            "Cơ chế ẩn: TÍCH LŨY CÓ ĐIỀU KIỆN — duyệt hết dãy, chỉ cộng phần tử thỏa ngưỡng. "
            "Khác đếm (count_if) ở chỗ cộng giá trị chứ không tăng một; câu chữ đời thường kiểm "
            "hệ định tuyến theo cơ chế duyệt-tích-lũy."
        ),
    ),

    # ── algorithm.count_if (single_pass_scan) ──
    _item(
        id="m16-countif-explicit",
        text="Tám bạn có điểm 6; 8,5; 7; 9; 5,5; 8; 4; 9,5. Đếm số bạn đạt từ 8 điểm trở lên.",
        group="specialized", expect="algorithm.count_if", route="algorithm.count_if",
        archetype=EP, family=SPS, live=True,
        cap_family="conditional_accumulator", area="T10.CD5", complexity="L2",
        result_mode="executable_simulation",
        learning="Hiểu biến đếm là trạng thái giữ lại qua các vòng, chỉ tăng khi điều kiện đúng.",
        rationale=(
            "Cơ chế ẩn: biến ĐẾM sống sót giữa các vòng lặp và điều kiện so sánh quyết định có "
            "tăng nó hay không. Duyệt HẾT dãy (khác dừng-sớm của scan) — timeline gắn mã giả "
            "cho xem từng lần biến đếm nhích lên."
        ),
    ),
    _item(
        id="m16-countif-paraphrase",
        text=(
            "Một tủ lạnh được đo nhiệt độ 7 lần: 3, 6, 2, 8, 5, 7, 1 độ C. Duyệt từng lần đo, "
            "mỗi lần nhiệt độ vượt 4 độ thì tăng một biến đếm, để biết bao nhiêu lần tủ quá ấm."
        ),
        group="specialized", expect="algorithm.count_if", route="algorithm.count_if",
        archetype=PP, family=SPS,
        cap_family="conditional_accumulator", area="T10.CD5", complexity="L2",
        result_mode="executable_simulation",
        learning="Nhận ra đếm-có-điều-kiện qua mô tả 'mỗi lần thỏa thì tăng biến đếm', duyệt hết dãy.",
        rationale=(
            "Cơ chế ẩn: ĐẾM CÓ ĐIỀU KIỆN trên toàn dãy — duyệt hết, tăng biến đếm ở mỗi phần tử "
            "thỏa ngưỡng. Đề né tên hàm và kiểm ranh giới với scan (dừng sớm): đây là đếm HẾT dãy."
        ),
    ),

    # ── algorithm.linear_search (single_pass_scan) ──
    _item(
        id="m16-linear-explicit",
        text="Danh sách số báo danh 305, 118, 227, 194, 260. Tìm xem 194 có trong danh sách không.",
        group="specialized", expect="algorithm.linear_search", route="algorithm.linear_search",
        archetype=EP, family=SPS, live=True,
        cap_family="search_path", area="T11CS.CD6", complexity="L1",
        result_mode="executable_simulation",
        learning="Hiểu tìm kiếm tuần tự so sánh BẰNG từng phần tử với giá trị đích và dừng khi khớp.",
        rationale=(
            "Cơ chế ẩn: SO SÁNH BẰNG lần lượt từng phần tử với đích, dừng ngay khi gặp — khác "
            "binary_search (chia đôi) và scan (so bất đẳng thức). Timeline cho thấy vùng đã xét "
            "lớn dần cho tới khi khớp."
        ),
    ),
    _item(
        id="m16-linear-paraphrase",
        text=(
            "Có dãy mã sách 71, 34, 90, 12, 58. Lần lượt so từng mã với 90 và DỪNG NGAY khi gặp "
            "đúng, cho biết nó nằm ở vị trí thứ mấy."
        ),
        group="specialized", expect="algorithm.linear_search", route="algorithm.linear_search",
        archetype=PP, family=SPS,
        cap_family="search_path", area="T11CS.CD6", complexity="L1",
        result_mode="executable_simulation",
        learning="Nhận ra tìm-tuần-tự qua mô tả 'so từng phần tử với giá trị đích, dừng khi gặp'.",
        rationale=(
            "Cơ chế ẩn: DÒ TUYẾN TÍNH so BẰNG một giá trị đích, dừng sớm khi khớp. Đề né tên "
            "'tìm kiếm tuần tự' và kiểm ranh giới với scan: so BẰNG (không bất đẳng thức) → linear_search."
        ),
    ),

    # ── algorithm.binary_search (interval_elimination) ──
    _item(
        id="m16-binsearch-explicit",
        text="Dãy đã sắp tăng dần 3, 8, 15, 22, 30, 41, 55. Tìm nhanh số 30 bằng cách chia đôi phạm vi.",
        group="specialized", expect="algorithm.binary_search", route="algorithm.binary_search",
        archetype=EP, family=IE,
        cap_family="search_path", area="T11CS.CD6", complexity="L2",
        result_mode="executable_simulation",
        learning="Hiểu tìm kiếm nhị phân loại một nửa phạm vi ở mỗi bước nên nhanh hơn tuần tự.",
        rationale=(
            "Cơ chế ẩn: NỬA BỊ LOẠI ở mỗi bước dựa trên so sánh với phần tử giữa. Học sinh nghĩ "
            "'nhảy cóc cho nhanh' mà không thấy phạm vi co lại một nửa mỗi lần — timeline làm hiện "
            "rõ vùng còn xét và vùng vừa bị loại."
        ),
    ),
    _item(
        id="m16-binsearch-paraphrase",
        text=(
            "Danh bạ đã xếp tăng dần: 101, 145, 178, 203, 256, 289. Tìm số 203 bằng cách mỗi bước "
            "xét phần tử ở GIỮA rồi LOẠI nửa không thể chứa nó."
        ),
        group="specialized", expect="algorithm.binary_search", route="algorithm.binary_search",
        archetype=PP, family=IE, live=True,
        cap_family="search_path", area="T11CS.CD6", complexity="L2",
        result_mode="executable_simulation",
        learning="Nhận ra tìm-nhị-phân qua mô tả 'xét phần tử giữa rồi loại nửa không chứa đích'.",
        rationale=(
            "Cơ chế ẩn: LOẠI TRỪ KHOẢNG — xét phần tử giữa rồi bỏ đi nửa không thể chứa đích. Đề "
            "né tên 'nhị phân' để kiểm hệ định tuyến theo cơ chế chia-đôi-loại-nửa trên dãy đã sắp."
        ),
    ),

    # ── algorithm.bubble_sort (comparison_sort — route qua TOKEN) ──
    _item(
        id="m16-bubble-explicit",
        text="Cho dãy 9, 4, 7, 2, 6. Sắp xếp dãy tăng dần bằng thuật toán sắp xếp nổi bọt.",
        group="specialized", expect="algorithm.bubble_sort", route=SORT_TOKEN,
        archetype=EP, family=CS, mech=MECH_BUBBLE,
        cap_family="sorting_movement", area="T11CS.CD6", complexity="L2",
        result_mode="executable_simulation",
        learning="Giải thích một lượt nổi bọt làm gì: so-đổi các cặp kề, phần tử lớn 'nổi' về cuối.",
        rationale=(
            "Cơ chế ẩn: QUYẾT ĐỊNH so sánh → đổi chỗ ở từng cặp KỀ nhau, đuôi đã sắp lớn dần sau "
            "mỗi lượt. Trên giấy học sinh chỉ thấy dãy đầu và cuối; timeline cho xem từng phép "
            "so sánh và đổi chỗ. Route ban đầu là token selector comparison_sort."
        ),
    ),
    _item(
        id="m16-bubble-paraphrase",
        text=(
            "Xếp dãy 8, 3, 6, 1 tăng dần bằng cách lần lượt so sánh HAI phần tử ĐỨNG KỀ nhau và "
            "đổi chỗ nếu phần tử trước lớn hơn, lặp nhiều lượt cho tới cuối dãy."
        ),
        group="specialized", expect="algorithm.bubble_sort", route=SORT_TOKEN,
        archetype=PP, family=CS, mech=MECH_BUBBLE, live=True,
        cap_family="sorting_movement", area="T11CS.CD6", complexity="L2",
        result_mode="executable_simulation",
        learning="Nhận ra cơ chế đổi-chỗ-cặp-kề của nổi bọt qua MÔ TẢ thao tác, không qua tên gọi.",
        rationale=(
            "Cơ chế ẩn: so sánh và ĐỔI CHỖ hai phần tử KỀ nhau — đặc trưng nổi bọt. Đề diễn đạt "
            "cơ chế bằng lời để kiểm hệ định tuyến theo CƠ CHẾ (analyze phát adjacent_compare_swap) "
            "chứ không theo từ khóa tên thuật toán; route ban đầu là token comparison_sort."
        ),
    ),

    # ── algorithm.insertion_sort (comparison_sort — route qua TOKEN) ──
    _item(
        id="m16-insertion-explicit",
        text="Sắp xếp dãy 7, 2, 9, 4, 5 theo thứ tự tăng dần bằng thuật toán sắp xếp chèn.",
        group="specialized", expect="algorithm.insertion_sort", route=SORT_TOKEN,
        archetype=EP, family=CS, mech=MECH_INSERT, live=True,
        cap_family="sorting_movement", area="T11CS.CD6", complexity="L2",
        result_mode="executable_simulation",
        learning="Phân biệt sắp xếp chèn với nổi bọt qua cách phần tử được đưa vào phần đã sắp.",
        rationale=(
            "Cơ chế ẩn: vùng ĐÃ SẮP ở đầu dãy lớn dần, mỗi phần tử mới phải LÙI dần về đúng vị "
            "trí. Kết quả cuối giống nổi bọt nên chỉ diễn biến từng bước mới phân biệt được; "
            "route ban đầu là token comparison_sort (analyze phát shift_into_sorted_prefix)."
        ),
    ),
    _item(
        id="m16-insertion-paraphrase",
        text=(
            "Xếp các lá bài trên tay theo thứ tự tăng dần: lấy TỪNG lá 6, 2, 8, 3, 5 rồi CHÈN mỗi "
            "lá vào đúng vị trí trong phần đầu ĐÃ SẮP xong."
        ),
        group="specialized", expect="algorithm.insertion_sort", route=SORT_TOKEN,
        archetype=PP, family=CS, mech=MECH_INSERT,
        cap_family="sorting_movement", area="T11CS.CD6", complexity="L2",
        result_mode="executable_simulation",
        learning="Nhận ra cơ chế chèn-vào-phần-đã-sắp qua mô tả 'lấy từng phần tử, chèn vào đúng chỗ'.",
        rationale=(
            "Cơ chế ẩn: CHÈN mỗi phần tử vào phần đầu ĐÃ SẮP (dời chỗ để nhường vị trí) — đặc "
            "trưng sắp xếp chèn. Đề né tên thuật toán để kiểm định tuyến theo cơ chế "
            "shift_into_sorted_prefix; route ban đầu là token comparison_sort."
        ),
    ),

    # ── algorithm.scan (single_pass_scan — bounded scan cấu hình) ──
    _item(
        id="m16-scan-explicit",
        text=(
            "Nhiệt độ trung bình bảy ngày lần lượt 31, 33, 30, 36, 32, 38, 29 độ C. Tìm ngày ĐẦU "
            "TIÊN có nhiệt độ vượt quá 35 độ."
        ),
        group="specialized", expect="algorithm.scan", route="algorithm.scan",
        semantic={"kind": "bounded_scan", "stop": "first_match", "found_pos": 3},
        archetype=EP, family=SPS, live=True,
        cap_family="bounded_scan", area="T10.CD5", complexity="L2",
        result_mode="executable_simulation",
        learning="Hiểu duyệt có DỪNG SỚM: vòng lặp kết thúc ngay khi gặp phần tử đầu tiên thỏa điều kiện.",
        rationale=(
            "Cơ chế ẩn: ĐIỀU KIỆN DỪNG SỚM theo bất đẳng thức — khác count_if (duyệt hết) và "
            "linear_search (so BẰNG một đích). LLM CẤU HÌNH scan-interpreter (enum đóng M12) thay "
            "vì cần module mới; interpreter — không phải LLM — sở hữu vị trí dừng/kết quả (R0)."
        ),
    ),
    _item(
        id="m16-scan-paraphrase",
        text=(
            "Một dây chuyền đo áp suất từng bình lần lượt 12, 15, 11, 18, 14, 20 bar. Duyệt lần "
            "lượt và DỪNG lại ở bình đầu tiên có áp suất từ 18 bar trở lên, đánh dấu bình đó."
        ),
        group="specialized", expect="algorithm.scan", route="algorithm.scan",
        semantic={"kind": "bounded_scan", "stop": "first_match", "found_pos": 3},
        archetype=PP, family=SPS,
        cap_family="bounded_scan", area="T10.CD5", complexity="L2",
        result_mode="executable_simulation",
        learning="Nhận ra duyệt-dừng-sớm-theo-ngưỡng qua mô tả 'dừng ở phần tử đầu tiên thỏa bất đẳng thức'.",
        rationale=(
            "Cơ chế ẩn: DUYỆT MỘT LƯỢT với điều kiện dừng theo bất đẳng thức (≥ ngưỡng) rồi đánh "
            "dấu — cấu hình được bằng scan-interpreter. Đề đổi bề mặt (áp suất) để kiểm hệ vẫn "
            "cấu hình scan thay vì ép vào find/count/linear."
        ),
    ),

    # ── logic.and_gate (boolean_composition — KHÔNG mechanism-exposed) ──
    _item(
        id="m16-and-explicit",
        text="Khi nào cổng logic AND hai đầu vào có đầu ra bằng 1? Mô phỏng một cổng AND hai đầu vào.",
        group="specialized", expect="logic.and_gate", route="logic.and_gate",
        archetype=EP, family=BC,
        cap_family="boolean_rule", area="T10.CD1", complexity="L1",
        result_mode="interactive_visualization",
        learning="Hiểu cổng AND: đầu ra bằng 1 khi và chỉ khi cả hai đầu vào bằng 1.",
        rationale=(
            "Cơ chế ẩn: bảng chân trị AID — đầu ra = A AND B, chỉ bằng 1 khi cả hai đầu vào bằng 1. "
            "Học sinh thuộc bảng nhưng bật/tắt từng chân và thấy đầu ra đổi theo mới nối được lý "
            "thuyết với hành vi. Đây là MỘT cổng AND HAI đầu vào THUẬN → mô phỏng chuyên biệt đủ năng lực."
        ),
    ),
    _item(
        id="m16-and-paraphrase",
        text=(
            "Mô phỏng một cổng logic hai đầu vào mà đầu ra chỉ bằng 1 khi CẢ HAI đầu vào cùng "
            "bằng 1, còn lại đầu ra bằng 0."
        ),
        group="specialized", expect="logic.and_gate", route="logic.and_gate",
        archetype=PP, family=BC, live=True,
        cap_family="boolean_rule", area="T10.CD1", complexity="L1",
        result_mode="interactive_visualization",
        learning="Nhận ra cổng AND qua MÔ TẢ bảng chân trị (đầu ra 1 chỉ khi cả hai vào 1), không qua tên 'AND'.",
        rationale=(
            "Cơ chế ẩn: bảng chân trị của phép AND mô tả bằng lời. Một cổng logic HAI đầu vào "
            "thuận, đầu ra 1 chỉ khi cả hai vào 1 — đúng năng lực logic.and_gate (chuyên biệt), "
            "KHÔNG có phủ định/≥3 điều kiện/ghép nhiều mức nên không cần generic."
        ),
    ),

    # ── binary.decimal_to_binary (positional_representation) ──
    _item(
        id="m16-binary-explicit",
        text="Số 156 được biểu diễn trong hệ nhị phân như thế nào? Hãy chỉ rõ những bit trọng số nào đang bật.",
        group="specialized", expect="binary.decimal_to_binary", route="binary.decimal_to_binary",
        archetype=EP, family=PR, mech=MECH_BINW,
        cap_family="data_representation", area="T10.CD1", complexity="L1",
        result_mode="executable_simulation",
        learning="Đổi số thập phân sang nhị phân và giải thích vai trò trọng số của từng bit.",
        rationale=(
            "Cơ chế ẩn: mỗi bit ĐÓNG GÓP một trọng số (128/64/32/16/8/4/2/1) vào giá trị cuối. "
            "Học sinh tính tay ra dãy bit nhưng không thấy TỪNG bit góp phần thế nào; timeline "
            "bật/tắt từng trọng số và cộng dồn cho thấy quan hệ nhân quả bit ↔ giá trị."
        ),
    ),
    _item(
        id="m16-binary-paraphrase",
        text=(
            "Biểu diễn số 89 bằng các ô trọng số 128, 64, 32, 16, 8, 4, 2, 1: chỉ rõ những trọng "
            "số nào cần bật để tổng đúng bằng 89."
        ),
        group="specialized", expect="binary.decimal_to_binary", route="binary.decimal_to_binary",
        archetype=PP, family=PR, mech=MECH_BINW, live=True,
        cap_family="data_representation", area="T10.CD1", complexity="L1",
        result_mode="executable_simulation",
        learning="Nhận ra đổi-nhị-phân qua mô tả trọng số vị trí 128..1, không qua chữ 'nhị phân'.",
        rationale=(
            "Cơ chế ẩn: TRỌNG SỐ VỊ TRÍ cơ số 2 (128..1) — bật các trọng số để tổng bằng giá trị "
            "cần biểu diễn, chính là đổi thập phân sang nhị phân. Đề né chữ 'nhị phân' để kiểm hệ "
            "định tuyến theo cơ chế biểu diễn vị trí (analyze phát binary_positional_weights)."
        ),
    ),

    # ── network.packet_routing (graph_traversal) ──
    _item(
        id="m16-routing-explicit",
        text="Minh hoạ đường đi của một gói tin từ máy tính qua switch, router và ISP tới máy chủ.",
        group="specialized", expect="network.packet_routing", route="network.packet_routing",
        archetype=EP, family=GT,
        cap_family="node_edge_graph+movement", area="T12.CD2", complexity="L2",
        result_mode="executable_simulation",
        learning="Hiểu gói tin đi QUA TỪNG CHẶNG thiết bị chứ không nhảy thẳng tới đích.",
        rationale=(
            "Cơ chế ẩn: các CHẶNG trung gian và đường đi được TÍNH RA từ topology (BFS tất định), "
            "không do người vẽ tùy ý. Học sinh hình dung Internet như đường ống thẳng; đi từng "
            "chặng phá vỡ hình dung đó. Topology cho sẵn → packet_routing (không dựng mạng từng bước)."
        ),
    ),
    _item(
        id="m16-routing-paraphrase",
        text=(
            "Trên một sơ đồ mạng cho sẵn gồm máy khách, hai bộ định tuyến và máy chủ đã nối dây "
            "đầy đủ, cho biết dữ liệu đi QUA TỪNG THIẾT BỊ nào để tới đích."
        ),
        group="specialized", expect="network.packet_routing", route="network.packet_routing",
        archetype=PP, family=GT, live=True,
        cap_family="node_edge_graph+movement", area="T12.CD2", complexity="L2",
        result_mode="executable_simulation",
        learning="Nhận ra định-tuyến-qua-nút qua mô tả 'đi qua từng thiết bị trên topology cho sẵn'.",
        rationale=(
            "Cơ chế ẩn: ĐƯỜNG ĐI qua các NÚT thiết bị trên topology CHO SẴN (BFS không trọng số). "
            "Đề né chữ 'gói tin/định tuyến' và nhấn 'sơ đồ cho sẵn' để phân biệt với dựng mạng "
            "từng bước (generic) và với đóng gói theo tầng (encapsulation)."
        ),
    ),

    # ── network.protocol_encapsulation (layered_pdu_transform) ──
    _item(
        id="m16-encap-explicit",
        text="Mô phỏng cách dữ liệu từ ứng dụng được đóng gói qua các tầng TCP/IP rồi truyền tới máy nhận.",
        group="specialized", expect="network.protocol_encapsulation",
        route="network.protocol_encapsulation",
        archetype=EP, family=LP,
        cap_family="layered_transformation", area="T12.CD2", complexity="L2",
        result_mode="executable_simulation",
        learning="Hiểu dữ liệu được THÊM DẦN thông tin giao thức khi đi xuống từng tầng ở máy gửi.",
        rationale=(
            "Cơ chế ẩn: PDU BIẾN ĐỔI qua từng tầng — mỗi tầng thêm đúng phần thông tin của mình "
            "theo THỨ TỰ cố định. Sơ đồ tĩnh 4 tầng không cho thấy thứ tự thêm/gỡ; engine 9 bước "
            "tự dựng tiến trình đóng gói → truyền → tháo gói (đây là diễn biến, không phải dựng cảnh)."
        ),
    ),
    _item(
        id="m16-encap-paraphrase",
        text=(
            "Khi gửi một tin nhắn, mỗi tầng giao thức lại BỌC THÊM phần thông tin điều khiển của "
            "mình trước khi chuyển xuống tầng dưới; hãy cho thấy gói dữ liệu LỚN DẦN qua bốn tầng "
            "rồi được gỡ ngược lại ở máy nhận."
        ),
        group="specialized", expect="network.protocol_encapsulation",
        route="network.protocol_encapsulation",
        archetype=PP, family=LP, live=True,
        cap_family="layered_transformation", area="T12.CD2", complexity="L2",
        result_mode="executable_simulation",
        learning="Nhận ra đóng-gói-theo-tầng qua mô tả 'mỗi tầng bọc thêm thông tin, gói lớn dần, gỡ ngược ở máy nhận'.",
        rationale=(
            "Cơ chế ẩn: tính ĐỐI XỨNG đóng gói/tháo gói — mỗi tầng thêm PDU khi xuống, gỡ đúng "
            "phần đó theo thứ tự ngược khi lên. Đề né chữ 'TCP/IP' và tả cơ chế bọc-thêm/gỡ-ngược "
            "để phân biệt với đường đi qua nút (packet_routing)."
        ),
    ),

    # ── generic.rule_scene (structural_progressive_representation) — reveal + move ──
    _item(
        id="m16-generic-reveal",
        text=(
            "Mô phỏng quá trình dựng một tam giác ABC hình thành TỪNG BƯỚC: đầu tiên vẽ đoạn AB, "
            "sau đó thêm điểm C, rồi nối AC và BC."
        ),
        group="generic", expect="generic.rule_scene", route="generic.rule_scene",
        semantic={"kind": "progressive_reveal", "min_steps": 3},
        archetype=EP, family=SPR,
        cap_family="structural_construction", area="T11.CD_hinhhoc", complexity="L2",
        result_mode="executable_simulation",
        learning="Hiểu một hình được LẮP GHÉP theo trình tự: điểm rồi đoạn xuất hiện dần.",
        rationale=(
            "Cơ chế ẩn: TRÌNH TỰ hình thành — đối tượng (điểm, đoạn) xuất hiện lần lượt (reveal_"
            "sequence) chứ không có sẵn ngay từ đầu. Mô phỏng chuyên biệt hiển thị cảnh đầy đủ "
            "ngay nên không làm được; generic dựng node+edge theo bước → đúng năng lực DSL."
        ),
    ),
    _item(
        id="m16-generic-move",
        text="Một robot lần lượt di chuyển qua các trạm A → B → C → D → E trên bản đồ cho sẵn.",
        group="generic", expect="generic.rule_scene", route="generic.rule_scene",
        semantic={"kind": "moving_path", "min_len": 4},
        archetype=PP, family=SPR, live=True,
        cap_family="movement_path", area="T11.CD_thuattoan", complexity="L1",
        result_mode="executable_simulation",
        learning="Nhận ra di-chuyển-theo-đường qua mô tả 'đi lần lượt qua các trạm', không có tính toán kết quả.",
        rationale=(
            "Cơ chế ẩn: DI CHUYỂN RỜI RẠC qua danh sách điểm cho sẵn (move_along_path) — không "
            "tính đường đi tối ưu, chỉ chạy theo trình tự đã nêu. Không mô phỏng chuyên biệt nào "
            "khớp (không phải mạng, không phải thuật toán) nhưng DSL biểu diễn được → generic."
        ),
    ),

    # ══════════════════════════════════════════════════════════════════
    # PHỤ LỤC B §2 — 8/8 family ≥1 valid_boundary
    # ══════════════════════════════════════════════════════════════════

    # single_pass_scan: thiếu thông tin optional (nhãn) + cực trị trùng
    _item(
        id="m16-vb-scan-optional",
        text="Một dãy nhiệt độ đo được: 22, 19, 25, 19, 30. Tìm nhiệt độ thấp nhất.",
        group="specialized", expect="algorithm.find_min", route="algorithm.find_min",
        archetype=VB, family=SPS,
        cap_family="single_pass_extreme", area="T11CS.CD6", complexity="L2",
        result_mode="executable_simulation",
        learning="Hệ vẫn chạy đúng khi thiếu thông tin optional (nhãn) và có cực trị trùng nhau.",
        rationale=(
            "Cơ chế ẩn: giữ cực tiểu chạy vẫn tất định khi giá trị nhỏ nhất (19) XUẤT HIỆN HAI "
            "LẦN và đề KHÔNG cho nhãn tên (thông tin optional vắng). Boundary: engine dùng mặc "
            "định hợp lệ, không cần optional để chạy — không phải capability gap."
        ),
        notes="Optional (nhãn) vắng + cực tiểu trùng → engine vẫn tất định; boundary hợp lệ, không gap.",
    ),

    # interval_elimination: (a) đích ABSENT trên dãy đã sắp
    _item(
        id="m16-vb-binsearch-absent",
        text=(
            "Dãy đã sắp tăng dần 2, 5, 9, 14, 21, 30. Tìm số 17 bằng cách chia đôi phạm vi; nếu "
            "không có thì kết luận không tìm thấy."
        ),
        group="specialized", expect="algorithm.binary_search", route="algorithm.binary_search",
        archetype=VB, family=IE,
        cap_family="search_path", area="T11CS.CD6", complexity="L4",
        result_mode="executable_simulation",
        learning="Hiểu tìm kiếm nhị phân kết luận KHÔNG TÌM THẤY khi phạm vi co về rỗng.",
        rationale=(
            "Cơ chế ẩn: LOẠI TRỪ KHOẢNG vẫn chạy khi đích (17) VẮNG MẶT — phạm vi co dần tới rỗng "
            "rồi kết luận không có. Boundary quan trọng: học sinh tưởng nhị phân luôn tìm thấy; "
            "case này cho thấy điều kiện dừng khi khoảng rỗng."
        ),
        notes="Đích absent trên dãy đã sắp → binary_search vẫn ok, kết luận không tìm thấy.",
    ),
    # interval_elimination: (b) input CHƯA sắp → normalize + annotation (CORRECTNESS §9)
    _item(
        id="m16-vb-binsearch-unsorted",
        text=(
            "Cho dãy 27, 4, 51, 13, 38, 9 (chưa được sắp xếp). Tìm nhanh số 38 bằng cách chia đôi "
            "phạm vi tìm kiếm."
        ),
        group="specialized", expect="algorithm.binary_search", route="algorithm.binary_search",
        archetype=VB, family=IE,
        cap_family="search_path", area="T11CS.CD6", complexity="L4",
        result_mode="executable_simulation",
        learning="Thấy hệ TỰ SẮP dãy trước khi chạy nhị phân thay vì từ chối oan vì thiếu từ khóa 'đã sắp'.",
        rationale=(
            "Cơ chế ẩn: interval_elimination CHỈ đúng trên dãy đã có thứ tự. Đề cho dãy CHƯA sắp "
            "nhưng nêu đúng cơ chế ('chia đôi') → validator TỰ SẮP dãy + chú thích sư phạm "
            "(CORRECTNESS §9, normalize-not-refuse), nhãn theo giá trị. Boundary chính sách, không gap."
        ),
        notes="Input chưa sắp → normalize (auto-sort + annotation, CORRECTNESS §9), vẫn expect binary_search ok.",
    ),

    # comparison_sort: dãy có phần tử trùng nhau
    _item(
        id="m16-vb-sort-duplicates",
        text="Sắp xếp dãy 5, 3, 5, 2, 3 tăng dần bằng thuật toán sắp xếp nổi bọt.",
        group="specialized", expect="algorithm.bubble_sort", route=SORT_TOKEN,
        archetype=VB, family=CS, mech=MECH_BUBBLE,
        cap_family="sorting_movement", area="T11CS.CD6", complexity="L2",
        result_mode="executable_simulation",
        learning="Thấy sắp xếp vẫn ổn định/đúng khi dãy có phần tử TRÙNG giá trị.",
        rationale=(
            "Cơ chế ẩn: so-đổi cặp kề vẫn tất định khi có phần tử TRÙNG (5 và 3 lặp) — không đổi "
            "chỗ khi bằng nhau. Boundary: học sinh hay nghi ngờ dãy có trùng; timeline cho thấy "
            "cặp bằng nhau giữ nguyên thứ tự. Route ban đầu là token comparison_sort."
        ),
        notes="Phần tử trùng nhau → comparison_sort vẫn ok; boundary hợp lệ.",
    ),

    # boolean_composition: anti-merge — 3-input AND → generic, KHÔNG and_gate
    _item(
        id="m16-vb-and3-generic",
        text=(
            "Đèn chỉ sáng khi CẢ BA công tắc A, B, C đều bật. Mô phỏng mạch để bật/tắt từng công "
            "tắc và quan sát đèn."
        ),
        group="generic", expect="generic.rule_scene", route="generic.rule_scene",
        semantic={"kind": "boolean_gate", "op": "and"},
        archetype=VB, family=BC,
        cap_family="boolean_rule", area="T10.CD1", complexity="L2",
        result_mode="interactive_visualization",
        learning="Nhận ra AND BA đầu vào vượt năng lực cổng chuyên biệt (2 vào) → phải dùng generic rule.",
        rationale=(
            "Cơ chế ẩn: quy tắc AND ba biến. logic.and_gate CHỈ mô phỏng MỘT cổng AND HAI đầu vào "
            "(classify quy tắc 2: từ BA điều kiện trở lên → generic). Boundary anti-merge: KHÔNG "
            "được gán bừa vào and_gate 'gần giống' — generic biểu diễn rule ba đầu vào qua trung gian."
        ),
        notes="AND 3 đầu vào vượt and_gate (2 vào) → expect generic.rule_scene, KHÔNG and_gate.",
    ),

    # positional_representation: 3 case — 0, 255, vượt phạm vi hợp đồng
    _item(
        id="m16-vb-binary-zero",
        text="Số 0 được biểu diễn trong hệ nhị phân như thế nào?",
        group="specialized", expect="binary.decimal_to_binary", route="binary.decimal_to_binary",
        archetype=VB, family=PR, mech=MECH_BINW,
        cap_family="data_representation", area="T10.CD1", complexity="L2",
        result_mode="executable_simulation",
        learning="Thấy biểu diễn nhị phân của giá trị biên nhỏ nhất (0 = tất cả bit tắt).",
        rationale=(
            "Cơ chế ẩn: trọng số vị trí ở giá trị BIÊN 0 — tất cả bit TẮT, tổng bằng 0. Boundary "
            "dưới của decimalValue (validator: 0–255). Học sinh dễ lúng túng '0 có mấy bit'; "
            "engine cho thấy mọi trọng số tắt vẫn là một biểu diễn hợp lệ."
        ),
        notes="Giá trị biên dưới (0, mọi bit tắt) — trong phạm vi hợp đồng 0–255.",
    ),
    _item(
        id="m16-vb-binary-255",
        text="Số 255 được biểu diễn trong hệ nhị phân như thế nào? Chỉ rõ các bit trọng số đang bật.",
        group="specialized", expect="binary.decimal_to_binary", route="binary.decimal_to_binary",
        archetype=VB, family=PR, mech=MECH_BINW,
        cap_family="data_representation", area="T10.CD1", complexity="L2",
        result_mode="executable_simulation",
        learning="Thấy biểu diễn nhị phân của giá trị biên lớn nhất (255 = tất cả 8 bit bật).",
        rationale=(
            "Cơ chế ẩn: trọng số vị trí ở giá trị BIÊN 255 — cả 8 bit BẬT (128+64+...+1). Boundary "
            "trên của decimalValue (validator: ≤255, bitWidth ≤8). Case cho thấy 8 bit đủ chứa "
            "đúng giá trị lớn nhất một byte không dấu."
        ),
        notes="Giá trị biên trên (255, cả 8 bit bật) — trong phạm vi hợp đồng 0–255.",
    ),
    _item(
        id="m16-vb-binary-overrange",
        text="Số 300 được biểu diễn trong hệ nhị phân như thế nào?",
        group="specialized", expect="binary.decimal_to_binary", route="binary.decimal_to_binary",
        archetype=VB, family=PR, mech=MECH_BINW,
        cap_family="data_representation", area="T10.CD1", complexity="L4",
        result_mode="executable_simulation",
        learning="Kiểm hành vi khi giá trị VƯỢT phạm vi hợp đồng (decimalValue > 255) — validator từ chối cấu trúc.",
        rationale=(
            "Cơ chế ẩn: vẫn là biểu diễn trọng số vị trí cơ số 2, nhưng 300 VƯỢT trần hợp đồng "
            "(validate_binary_config: decimalValue 0–255, bitWidth 1–8). Đây là CONTRACT-ERROR "
            "control: bài vẫn ĐÚNG loại (đổi nhị phân) nên định tuyến binary.decimal_to_binary — "
            "phần biên là validator từ chối cấu trúc → LLM retry/clamp theo hành vi thực, KHÔNG phải capability gap."
        ),
        notes=(
            "Contract-error control: 300 > 255 → validator từ chối cấu trúc (decimalValue phải 0–255) "
            "→ LLM retry/clamp theo hành vi thực. KHÔNG phải capability gap: bài đúng loại, route đúng."
        ),
    ),

    # graph_traversal: topology nhiều đường thay thế — BFS vẫn ok
    _item(
        id="m16-vb-routing-multipath",
        text=(
            "Trên một mạng có máy khách nối tới HAI bộ định tuyến khác nhau, và cả hai bộ định "
            "tuyến đều nối tới máy chủ. Cho biết gói tin đi từ máy khách tới máy chủ theo đường nào."
        ),
        group="specialized", expect="network.packet_routing", route="network.packet_routing",
        archetype=VB, family=GT,
        cap_family="node_edge_graph+movement", area="T12.CD2", complexity="L3",
        result_mode="executable_simulation",
        learning="Thấy BFS chọn một đường đi tất định khi topology có NHIỀU đường thay thế cùng tới đích.",
        rationale=(
            "Cơ chế ẩn: BFS chọn đường ít chặng một cách TẤT ĐỊNH khi có nhiều đường thay thế "
            "(hai router song song). Boundary: đích VẪN reachable nên validate_network_config chấp "
            "nhận; đây là năng lực có sẵn (đường đi không trọng số), không đòi chọn tối ưu theo trọng số."
        ),
        notes=(
            "Quyết định (đã KIỂM validate_network_config): validator TỪ CHỐI topology không có "
            "đường đi ('Không có đường đi từ nguồn tới đích'). Vì vậy KHÔNG viết case unreachable-"
            "expect-ok (tự mâu thuẫn); dùng case nhiều-đường-đều-reachable → BFS chọn tất định, vẫn ok."
        ),
    ),

    # layered_pdu_transform: decapsulation explicit — máy nhận THÁO gói
    _item(
        id="m16-vb-decapsulation",
        text=(
            "Ở máy nhận, một gói tin được THÁO GÓI lần lượt qua các tầng TCP/IP: mỗi tầng gỡ bỏ "
            "phần thông tin của mình để cuối cùng lấy ra dữ liệu gốc. Mô phỏng quá trình tháo gói này."
        ),
        group="specialized", expect="network.protocol_encapsulation",
        route="network.protocol_encapsulation",
        archetype=VB, family=LP,
        cap_family="layered_transformation", area="T12.CD2", complexity="L2",
        result_mode="executable_simulation",
        learning="Thấy tháo gói là quá trình NGƯỢC của đóng gói — mỗi tầng gỡ đúng phần của mình.",
        rationale=(
            "Cơ chế ẩn: tính ĐỐI XỨNG — engine 4 tầng sở hữu CẢ đóng gói lẫn tháo gói "
            "(encapsulate_decapsulate_4layer). Boundary: đề chỉ nhấn CHIỀU THÁO GÓI ở máy nhận, "
            "vẫn thuộc network.protocol_encapsulation (không phải một module riêng cho decapsulation)."
        ),
        notes="Decapsulation explicit (chỉ chiều tháo gói) → vẫn network.protocol_encapsulation.",
    ),

    # structural_progressive_representation: webstatic prebuilt — cảnh tĩnh
    _item(
        id="m16-vb-web-static",
        text=(
            "Hiển thị cấu trúc một trang web gồm phần tiêu đề, một đoạn văn giới thiệu và một chân "
            "trang. Chỉ cần cho xem bố cục, không dựng từng bước."
        ),
        group="generic", expect="generic.rule_scene", route="generic.rule_scene",
        semantic={"kind": "static_structural"},
        archetype=VB, family=SPR,
        cap_family="structural_layout", area="T12.CD4", complexity="L2",
        result_mode="interactive_visualization",
        learning="Nhận ra cảnh TĨNH ('hiển thị cấu trúc') không được ép thành reveal giả.",
        rationale=(
            "Cơ chế ẩn: BỐ CỤC LỒNG NHAU (structural) trình bày TĨNH — cho sẵn, chỉ xem, không "
            "temporal. Boundary của family: đề 'hiển thị/cho xem cấu trúc' → scene_construction "
            "prebuilt + temporal_needs rỗng; semantic check CẤM giả vờ nó hình thành từng bước."
        ),
        notes="Cảnh tĩnh (prebuilt, static_structural) — boundary dưới của structural_progressive.",
    ),

    # ══════════════════════════════════════════════════════════════════
    # PHỤ LỤC B §3 — 8/8 family ≥1 near_miss_gap (group unsupported)
    # (structural_progressive phủ bởi authority_control §5a — đếm cho cả hai lock)
    # ══════════════════════════════════════════════════════════════════

    # comparison_sort: partition đệ quy (quicksort) — mechanism gate
    _item(
        id="m16-nm-sort-partition",
        text=(
            "Sắp xếp dãy 6, 2, 9, 1, 7 tăng dần bằng cách CHIA dãy quanh một phần tử mốc rồi sắp "
            "mỗi phần một cách ĐỆ QUY."
        ),
        group="unsupported", route=None,
        archetype=NM, family=CS, mech=MECH_PARTITION,
        gate="mechanism", error_code=EC_MECH_OWN, algorithmic=True, live=True,
        cap_family="sorting_mechanism_gap", area="ngoài phạm vi sắp xếp đơn giản THPT — phân hoạch đệ quy",
        complexity="L4", result_mode="unsupported",
        learning="Hệ từ chối trung thực cơ chế phân hoạch đệ quy khi không executor nào sở hữu.",
        rationale=(
            "Cơ chế ẩn của quick sort — CHIA quanh mốc + ĐỆ QUY hai nửa (partition_recursive) — "
            "KHÔNG thuộc họ so-sánh-đổi-chỗ tuyến tính mà engine có. Analyze phát prescribed_"
            "procedure partition_recursive; mechanism gate (E4 tầng 1) trả gate_mechanism_ownership "
            "→ capability_gap. Ép về nổi bọt/chèn là dạy SAI cơ chế."
        ),
        notes="Route sorting → token comparison_sort; mechanism gate (tầng 1) chặn partition_recursive không sở hữu.",
    ),

    # single_pass_scan: vòng lặp BIẾN TỰ DO (không dãy số cho sẵn)
    _item(
        id="m16-nm-freevar-loop",
        text=(
            "Cho biến x khởi đầu bằng 5. Mỗi vòng lặp x được NHÂN ĐÔI. Vòng lặp dừng khi x vượt "
            "quá 100. Mô phỏng quá trình thay đổi của x qua từng vòng."
        ),
        group="unsupported", route=None,
        archetype=NM, family=SPS, algorithmic=True, live=True,
        cap_family="control_flow_loop", area="T10.CD5 (mô phỏng thực thi vòng lặp ngoài năng lực v1)",
        complexity="L4", result_mode="unsupported",
        learning="Hệ từ chối trung thực vòng lặp biến tự do (không dãy cho sẵn) thay vì tự tính diễn biến.",
        rationale=(
            "Cơ chế được hỏi là VÒNG LẶP CÓ TRẠNG THÁI trên BIẾN TỰ DO với điều kiện dừng theo "
            "ngưỡng — role arbitrary_algorithm + numeric_threshold manifest cố ý không cover. LLM "
            "tự tính dãy 5→10→20→40→80→160 rồi nhét vào reveal_sequence sẽ là LLM sở hữu tiến "
            "trình (vi phạm R0). KHÔNG ép vào algorithm.scan (scan cần DÃY SỐ cho sẵn)."
        ),
        notes=(
            "Không dãy số cho sẵn → không phải scan (2c). Bắt ở representation plan / classify 4b "
            "như capability_gap (role arbitrary_algorithm không cover); không kèm error_code cụ thể."
        ),
    ),

    # interval_elimination: tìm kiếm NỘI SUY (đoán vị trí theo tỉ lệ)
    _item(
        id="m16-nm-interpolation",
        text=(
            "Tìm số 47 trong dãy đã sắp 5, 12, 23, 38, 47, 60, 71 bằng cách ĐOÁN vị trí phần tử "
            "theo TỈ LỆ giữa giá trị cần tìm và hai đầu mút (thuật toán tìm kiếm nội suy)."
        ),
        group="unsupported", route=None,
        archetype=NM, family=IE, algorithmic=True, live=True,
        cap_family="search_mechanism_gap", area="ngoài phạm vi tìm kiếm THPT — nội suy theo tỉ lệ giá trị",
        complexity="L4", result_mode="unsupported",
        learning="Hệ từ chối trung thực tìm kiếm nội suy — cơ chế đoán-vị-trí-theo-tỉ-lệ không engine nào sở hữu.",
        rationale=(
            "Cơ chế ẩn của tìm kiếm NỘI SUY — ĐOÁN vị trí theo TỈ LỆ giá trị, không phải loại "
            "nửa đều (halve_sorted_interval mà binary_search sở hữu). Kết quả phải TÍNH qua cơ "
            "chế riêng của thuật toán → result_ownership algorithmic → capability_gap (classify 4c). "
            "Không ép vào binary_search 'gần giống' — chia đôi khác đoán theo tỉ lệ."
        ),
        notes=(
            "interval_elimination KHÔNG mechanism-exposed → analyze không phát mechanism family này "
            "(analyze_mechanism_expected phải None). Từ chối dựa trên result_ownership=algorithmic "
            "(classify 4c / computation gate), không phải mechanism gate."
        ),
    ),

    # boolean_composition: ngưỡng k-of-n (ít nhất 2 trong 4) — numeric_threshold
    _item(
        id="m16-nm-threshold-kofn",
        text=(
            "Một đèn báo động sáng khi có ÍT NHẤT 2 trong 4 cảm biến khói phát hiện khói. Mô "
            "phỏng mạch đèn báo động này."
        ),
        group="unsupported", route=None,
        archetype=NM, family=BC, algorithmic=False, live=True,
        cap_family="boolean_threshold_gap", area="T10.CD1 (ngưỡng k-of-n vượt DSL logic v1)",
        complexity="L4", result_mode="unsupported",
        learning="Hệ từ chối trung thực điều kiện NGƯỠNG k-trong-n (k≥2) — vượt DSL rule logic thuần.",
        rationale=(
            "Cơ chế được hỏi là NGƯỠNG k-of-n (ít nhất 2 trong 4) — role numeric_threshold mà "
            "manifest cố ý không cover (rule logic KHÔNG đếm ngưỡng). Phân biệt với 'ít nhất MỘT "
            "trong' (OR thuần, generic được): k≥2 là ngưỡng thật → capability_gap. Không phải "
            "đòi thuật toán (algorithmic_request=False), mà đòi primitive ngưỡng DSL không có."
        ),
        notes=(
            "k-of-n với k=2, n=4 → numeric_threshold role không cover → capability_gap (representation "
            "plan / computation gate). Khác 'ít nhất một trong' (OR → generic). Không kèm error_code cụ thể."
        ),
    ),

    # positional_representation: hex — non_binary_base (hai đường từ chối hợp lệ)
    _item(
        id="m16-nm-hex-gap",
        text="Đổi số 2026 sang hệ thập lục phân (cơ số 16) và giải thích từng bước biểu diễn.",
        group="unsupported", route=None,
        archetype=NM, family=PR, mech=MECH_NONBIN, algorithmic=False, live=True,
        cap_family="positional_representation_base_gap",
        area="T10.CD1 chỉ phủ đổi sang NHỊ PHÂN (Bài 4) — thập lục phân ngoài phạm vi anchor",
        complexity="L4", result_mode="unsupported",
        learning="Hệ từ chối trung thực đổi sang cơ số khác 2 (thập lục phân) — không engine nào sở hữu.",
        rationale=(
            "Cơ chế ẩn của đổi thập lục phân — chia lấy dư LẶP theo cơ số 16, không phải trọng số "
            "bit 8/4/2/1 của nhị phân. non_binary_base là INTENTIONAL_GAP (mechanisms.py): KHÔNG "
            "target nào sở hữu. Ép vào engine nhị phân ra kết quả SAI cơ số im lặng → capability_gap trung thực."
        ),
        notes=(
            "expected_gate=None có chủ đích: CẢ HAI đường từ chối đều hợp lệ tùy classify lượt 1 — "
            "(A) direct-route ownership gate trên binary.decimal_to_binary (gate_mechanism_ownership) "
            "nếu classify về binary; (B) route-mismatch recovery fail-closed (route_mechanism_family_"
            "mismatch) nếu classify về generic. Cả hai đều → capability_gap."
        ),
    ),

    # graph_traversal: đường ngắn nhất theo TỔNG TRỌNG SỐ (Dijkstra)
    _item(
        id="m16-nm-weighted-shortest",
        text=(
            "Cho một mạng các trạm nối nhau, mỗi đường nối có ghi ĐỘ DÀI. Tìm đường đi ngắn nhất "
            "theo TỔNG ĐỘ DÀI từ trạm A tới trạm E."
        ),
        group="unsupported", route=None,
        archetype=NM, family=GT, algorithmic=True, live=True,
        cap_family="algorithmic_computation_gap",
        area="ngoài phạm vi công khai Tin học THPT — đồ thị có trọng số (Dijkstra)",
        complexity="L4", result_mode="unsupported",
        learning="Hệ từ chối trung thực đường-ngắn-nhất-có-trọng-số (Dijkstra) — packet_routing chỉ BFS không trọng số.",
        rationale=(
            "Cơ chế ẩn của đường ngắn nhất CÓ TRỌNG SỐ — khoảng cách tạm, chọn đỉnh gần nhất, nới "
            "cạnh — KHÔNG có engine tất định nào sở hữu (network.packet_routing chỉ minh hoạ BFS "
            "không trọng số; known_gaps ghi rõ Dijkstra). Kết quả phải TÍNH qua cơ chế riêng → "
            "result_ownership algorithmic → capability_gap (classify 4c)."
        ),
        notes=(
            "graph_traversal KHÔNG mechanism-exposed → analyze_mechanism_expected None. Từ chối dựa "
            "trên result_ownership=algorithmic (Dijkstra), không phải mechanism gate. So với packet_"
            "routing known_gaps='đường đi ngắn nhất có trọng số (Dijkstra)'."
        ),
    ),

    # layered_pdu_transform: bắt tay ba bước TCP (protocol state machine)
    _item(
        id="m16-nm-tcp-handshake",
        text=(
            "Mô phỏng quá trình BẮT TAY BA BƯỚC (SYN, SYN-ACK, ACK) để thiết lập một kết nối TCP "
            "giữa máy khách và máy chủ."
        ),
        group="unsupported", route=None,
        archetype=NM, family=LP, algorithmic=False, live=True,
        cap_family="layered_transformation",
        area="T12.CD2 (kiến thức nâng cao ngoài phạm vi v1)",
        complexity="L4", result_mode="unsupported",
        learning="Hệ từ chối trung thực bắt tay ba bước TCP — đòi mô hình trạng thái giao thức mà v1 không có.",
        rationale=(
            "Cơ chế được hỏi (handshake SYN/SYN-ACK/ACK, thiết lập kết nối) đòi mô hình TRẠNG THÁI "
            "GIAO THỨC HAI CHIỀU mà engine encapsulation v1 (9 bước đóng gói MỘT CHIỀU) KHÔNG có. "
            "Cả packet_routing lẫn generic đều không có năng lực máy-trạng-thái giao thức → "
            "unsupported trung thực (đồng nhất chính sách cur-t12-tcp-advanced đã khóa)."
        ),
        notes="Handshake/seq/ACK là protocol state machine ngoài v1 (như cur-t12-tcp-advanced); classify 3d → unsupported.",
    ),

    # ══════════════════════════════════════════════════════════════════
    # PHỤ LỤC B §4 — cross_family_recovery (1 success + 1 failure)
    # ══════════════════════════════════════════════════════════════════

    # (a) recovery-SUCCESS: positional dễ lệch sang generic weighted_sum → hồi phục binary
    _item(
        id="m16-cr-positional-recover",
        text=(
            "Biểu diễn số 45 bằng dãy bit trọng số 32, 16, 8, 4, 2, 1, mỗi bit như một CÔNG TẮC "
            "bật/tắt sao cho tổng đúng bằng 45."
        ),
        group="specialized", expect="binary.decimal_to_binary", route="binary.decimal_to_binary",
        archetype=CR, family=PR, mech=MECH_BINW,
        gate="route_mechanism", recovery=True, live=True,
        cap_family="data_representation", area="T10.CD1", complexity="L3",
        result_mode="executable_simulation",
        learning="Thấy hệ HỒI PHỤC về binary.decimal_to_binary khi classify lượt 1 dễ lệch sang generic weighted_sum.",
        rationale=(
            "Cơ chế ẩn: biểu diễn vị trí cơ số 2 (binary_positional_weights) — 'công tắc trọng số "
            "32/16/8/4/2/1 sao cho tổng = 45' RẤT dễ bị classify nhầm sang generic weighted_sum. "
            "Analyze phát mechanism positional_representation → route-mismatch với generic (family "
            "khác) → ≤1 reclassify → binary.decimal_to_binary (đúng family, sở hữu cơ chế). Recovery thành công."
        ),
        notes=(
            "route_mechanism gate FIRE rồi HỒI PHỤC: nếu classify lượt 1 về generic (family mismatch) "
            "→ reclassify → binary.decimal_to_binary. Nếu classify lượt 1 đã đúng binary thì gate không "
            "fire nhưng route cuối vẫn binary. recovery_route_exists=True; error_code=None (recovery ok)."
        ),
    ),
    # (b) recovery-FAILURE: positional prescribed nhưng bản chất lai không route nào thỏa
    _item(
        id="m16-cr-positional-fail",
        text=(
            "Biểu diễn số 68 theo hệ cơ số NĂM (ngũ phân) bằng các ô trọng số 25, 5, 1, rồi TÔ "
            "ĐẬM những ô được dùng."
        ),
        group="unsupported", route=None,
        archetype=CR, family=PR, mech=MECH_NONBIN,
        gate="route_mechanism", error_code=EC_ROUTE_MISMATCH,
        algorithmic=False, recovery=False, live=True,
        cap_family="positional_representation_base_gap",
        area="T10.CD1 chỉ phủ nhị phân — cơ số 5 ngoài phạm vi, không target nào sở hữu",
        complexity="L4", result_mode="unsupported",
        learning="Hệ FAIL-CLOSED khi cơ chế positional được prescribed nhưng không route nào (binary/generic) thỏa.",
        rationale=(
            "Cơ chế ẩn: biểu diễn vị trí cơ số 5 (non_binary_base) — analyze phát mechanism "
            "positional_representation. binary.decimal_to_binary CHỈ sở hữu cơ số 2 (không nhận cơ "
            "số 5); framing 'vẽ ô, tô đậm' đẩy classify về generic (family mismatch với positional). "
            "Sau ≤1 reclassify VẪN mismatch → fail-closed route_mechanism_family_mismatch. Không route nào thỏa."
        ),
        notes=(
            "recovery_route_exists=False: analyze prescribes positional non_binary_base; binary target "
            "không sở hữu cơ số 5, generic mâu thuẫn family positional → sau 1 reclassify vẫn mismatch "
            "→ route_mechanism_family_mismatch (pipeline trả error_code này, capability_gap)."
        ),
    ),

    # ══════════════════════════════════════════════════════════════════
    # PHỤ LỤC B §5 — authority_control (leak control + representation đối chứng)
    # ══════════════════════════════════════════════════════════════════

    # (a) computation-LEAK control (= structural_progressive near_miss, đếm cả hai lock)
    _item(
        id="m16-ac-computation-leak",
        text=(
            "Vẽ sơ đồ các trạm và đường nối có ghi ĐỘ DÀI, rồi TÍNH và tô đậm đường đi NGẮN NHẤT "
            "theo tổng độ dài giữa hai trạm."
        ),
        group="unsupported", route=None,
        archetype=AC, family=SPR,
        gate="computation", error_code=None, algorithmic=True, live=True,
        cap_family="representation_computation_leak",
        area="ngoài phạm vi — vẽ được cảnh nhưng đòi TÍNH kết quả thuật toán không engine sở hữu",
        complexity="L4", result_mode="unsupported",
        learning="Hệ chặn RÒ RỈ TÍNH TOÁN: cảnh vẽ được nhưng đề đòi TÍNH đường ngắn nhất có trọng số → capability_gap.",
        rationale=(
            "Cơ chế ẩn: đề TRỘN một biểu diễn dựng được (vẽ sơ đồ trạm/đường — structural/relational) "
            "với một KẾT QUẢ THUẬT TOÁN không engine nào sở hữu (đường ngắn nhất có trọng số). Nếu "
            "để generic dựng cảnh rồi khai sẵn đáp án tô đậm thì LLM tự giải thay engine (vi phạm R0). "
            "computation gate (M13) đọc result_ownership=algorithmic → capability_gap. Đây cũng là "
            "near_miss của structural_progressive (muốn dựng cảnh nhưng rò rỉ tính toán)."
        ),
        notes=(
            "computation gate (M13) fire: chosen=generic + result_ownership algorithmic → capability_gap "
            "KHÔNG kèm error_code (đã KIỂM pipeline.py nhánh check_computation_ownership: return "
            "failure_category=capability_gap, không có trường error_code) → expected_error_code=None. "
            "Đếm CHO CẢ near_miss của structural_progressive_representation (§3)."
        ),
    ),
    # (b) representation ĐỐI CHỨNG: chỉ VẼ theo mô tả cho sẵn → generic ok
    _item(
        id="m16-ac-representation-ok",
        text=(
            "Chỉ VẼ sơ đồ các trạm và đường nối theo mô tả cho sẵn, hiện DẦN từng trạm một; không "
            "cần tính toán đường đi nào."
        ),
        group="generic", expect="generic.rule_scene", route="generic.rule_scene",
        semantic={"kind": "progressive_reveal", "min_steps": 2},
        archetype=AC, family=SPR,
        cap_family="structural_construction", area="T12.CD2", complexity="L2",
        result_mode="executable_simulation",
        learning="Đối chứng: chỉ biểu diễn (vẽ, hiện dần) theo mô tả cho sẵn → generic.rule_scene chạy được, KHÔNG bị gate chặn.",
        rationale=(
            "Cơ chế ẩn: DỰNG CẢNH TỪNG BƯỚC (reveal_sequence) thuần biểu diễn — result_ownership "
            "provided (đề cho sẵn cấu trúc, chỉ hiện dần), KHÔNG đòi tính kết quả thuật toán. Đối "
            "chứng DƯƠNG với m16-ac-computation-leak: cùng bề mặt 'trạm và đường nối' nhưng KHÔNG "
            "leak tính toán → computation gate không fire → generic.rule_scene hợp lệ."
        ),
        notes="Đối chứng của m16-ac-computation-leak: không leak tính toán → generic ok, computation gate không fire.",
    ),
]


# ── Registry THAM CHIẾU case pool cũ vào coverage matrix M16 (không chép text) ──
# case_id (pool cũ) → lý do tham chiếu: bằng chứng đã live-verified milestone trước,
# bổ trợ coverage M16 mà không nhân đôi đề.
M16_REFERENCED_CASES: dict[str, str] = {
    # comparison_sort — near-miss selection/quick đã live-verified M14/M15
    "cap-selection-sort-gap": "comparison_sort near-miss (select_extreme_repeated) — live-verified M14/M15",
    "cap-quicksort-gap": "comparison_sort near-miss (partition_recursive) — boundary pool capability",
    "cap-bubble": "comparison_sort positive bubble (explicit tên thuật toán) — flagship M14",
    "cap-insertion": "comparison_sort positive insertion — capability M14",
    "cap-bubble-paraphrase": "comparison_sort paraphrase theo cơ chế — live-verified M14/M15",
    # positional_representation — hex/octal gap + binary positive đã live M15 W1
    "m15-hex-gap": "positional near-miss non_binary_base (hex) — live-verified M15 W1",
    "m15-octal-gap": "positional near-miss non_binary_base (octal) — M15 W1",
    "m15-binary-positive": "positional positive binary — đối chứng dương M15 W1",
    "cur-t10-binary": "positional positive binary (curriculum anchor T10.CD1)",
    # interval_elimination — binsearch unsorted normalize policy đã live M15
    "m15-binsearch-unsorted": "interval_elimination boundary unsorted-normalize — live-verified M15 W1",
    "cur-t11cs-binsearch": "interval_elimination positive (curriculum anchor Bài 19)",
    # single_pass_scan — scan first-above + count/linear contrast đã có tag m12
    "m12-scan-first-above": "single_pass_scan positive scan (first-above-threshold) — M12",
    "m12-scan-contrast-linear": "single_pass_scan contrast linear_search (so BẰNG) — M12",
    "cur-t10-count": "single_pass_scan positive count_if (duyệt hết dãy) — M12 contrast",
    # boolean_composition — nested compose + threshold gap đã live M11
    "m11-nested-canonical": "boolean_composition nested AND(x,OR(y,z)) → generic — M11",
    "m11-paraphrase-atleast": "boolean_composition paraphrase 'ít nhất một trong' (OR thuần) — M11",
    "c-threshold": "boolean_composition threshold gap (2-of-3) — regression baseline",
    # graph_traversal + layered_pdu_transform — routing/encap + TCP advanced gap M10
    "cur-t12-packet": "graph_traversal positive packet_routing (curriculum) — M10",
    "cur-t12-encap1": "layered_pdu_transform positive encapsulation — M10-AI-ROUTE",
    "cur-t12-encap2": "layered_pdu_transform positive decapsulation — M10-AI-ROUTE",
    "cur-t12-tcp-advanced": "layered_pdu_transform near-miss TCP advanced (handshake) — live-locked M10",
    "cap-dijkstra-gap": "graph_traversal near-miss Dijkstra (weighted shortest path) — live-verified M13",
    # structural_progressive_representation — reveal/static/system-flow đã có
    "cap-sysflow-static": "structural_progressive boundary system-flow tĩnh — S2",
    "cur-t12-webbuild": "structural_progressive positive reveal (web build) — curriculum",
    "d-webstatic": "structural_progressive boundary static scene — regression baseline",
    "xd-order-workflow": "structural_progressive positive move_along_path (order workflow) — cross_domain",
}
