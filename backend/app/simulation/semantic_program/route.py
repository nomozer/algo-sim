# -*- coding: utf-8 -*-
"""Ghép các cổng TẤT ĐỊNH của route sinh ngữ nghĩa thành một phán quyết.

VÌ SAO TỒN TẠI: từng mảnh — grounding P2, C₁a, C₁b, C₂, binding fail-closed —
đều đã có và đều đã được test riêng, nhưng **chưa mảnh nào được ghép lại**.
`stage_semantic_program` trước hôm nay không có một ai gọi, và smoke script thì
tự dựng chuỗi riêng (prompt → validate → execute → compile), bỏ qua sạch các
cổng. Đánh giá luận văn mà chạy trên chuỗi ấy là đo một hệ **không phải hệ được
mô tả trong luận văn** — và bất biến #22 cấm đúng điều đó.

HAI TỈ LỆ, KHÔNG PHẢI MỘT. Đây là lý do hàm dưới đây trả về một bản ghi thay vì
một `bool`:

    executable  — máy có CHẠY ĐƯỢC bài này thành mô phỏng không?
    servable    — đã đủ bằng chứng để PHÁT cho học sinh như canonical chưa?

Gộp hai cái làm một là tự bịa ra một con số không tồn tại. Một chương trình chạy
trơn tru nhưng mang nghĩa vụ chưa có checker độc lập thì `executable=True`,
`servable=False`, `verification_gap` — không phải `capability_gap`, vì nói "hệ
không làm được" trong khi nó vừa làm xong là **báo cáo sai năng lực của chính
mình** theo hướng bi quan.

R0 nguyên vẹn: mọi phán quyết ở file này TẤT ĐỊNH, đọc từ contract đã đóng băng
và từ trace do interpreter sinh. Không có một lượt LLM nào.
"""
from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from app.simulation.error_codes import SEMANTIC_FAILURE_CATEGORY, ErrorCode

from .assumption_gate import NOT_APPLICABLE as _GD_KHONG_AP_DUNG
from .assumption_gate import PROVEN_SAFE as _GD_AN_TOAN
from .assumption_gate import UNDETERMINED as _GD_CHUA_RO
from .assumption_gate import MA_CHUA_CHUNG_MINH, MA_LECH_PHEP_DUNG, MA_NHIEU_DINH_NGHIA, MA_PHU_THUOC, kiem_gia_dinh
from .construction_binding import MA_CHUA_DOI_CHIEU, MA_TOA_DO_THAY_DUNG, KetQuaDoiChieu, doi_chieu_phep_dung
from .contract import SemanticProgramSpec
from .coverage_gate import (
    chan_doan_phu_cau_truc,
    check_realized_coverage,
    check_structural_coverage,
)
from .formation import hoan_thien_dung_hinh
from .grounding_gate import NguonDe, check_grounding
from .interpreter import SemanticProgramInterpreter
from .learner_surface import check_learner_surface
from .transport import check_envelope_transport
from .pacer import DEFAULT_PRESENTATION_BUDGET
from .pipeline_adapter import (
    DEFAULT_EXECUTION_BUDGET,
    VisualBindingUnresolved,
    compile_semantic_program_to_envelope,
)
from .ir_static_check import kiem_tinh
from .postconditions import check_postconditions, check_source_invariants
from .request_contract import RequestContract
from .refusal_cause import MA_KHONG_CAT, mat_phang_khong_cat, theo_ma
from .shape_constraint import neu_khoi_da_dien


class SemanticRouteOutcome(BaseModel):
    """Phán quyết đầy đủ của route — đủ để dựng envelope VÀ để chấm benchmark."""

    #: Cổng cuối cùng đã chạy tới. Dùng để chấm A/B mà không phải suy từ mã lỗi.
    stage_reached: str
    #: Máy có dựng được mô phỏng chạy được không (claim A).
    executable: bool
    #: Có đủ bằng chứng để phát canonical không (claim B). `executable` mà
    #: `not servable` chính là `verification_gap`.
    servable: bool
    error_code: str | None = None
    failure_category: str | None = None
    reason: str | None = None
    #: Nghĩa vụ hợp lệ nhưng KHÔNG có checker server-owned (mức yếu, §5.4).
    weak_kinds: list[str] = Field(default_factory=list)
    details: list[str] = Field(default_factory=list)
    #: MÃ CHI TIẾT có cấu trúc của lời từ chối (W12) — vd `GIVEN_VALUE_NOT_IN_
    #: SOURCE`. `error_code` giữ enum rộng; lời cho học sinh chọn theo mã này,
    #: không bóc `details`. `None` ở mọi kết cục không từ chối có mã chi tiết.
    reason_code: str | None = None
    #: Ký hiệu HỌC SINH của thứ bị từ chối (`AD`) — không bao giờ là tên máy.
    reason_subjects: list[str] = Field(default_factory=list)
    #: W17 §15.3 — `SOURCE` · `CONSTRUCTION` · `UNKNOWN` (`refusal_cause`); `None` khi phục vụ.
    refusal_cause: str | None = None
    #: BẰNG CHỨNG NGUỒN của từng GIVEN đã nhận (`GroundingResult.given_evidence`).
    #: Quan trắc, không gác cửa, không vào envelope.
    grounding_given_evidence: list[dict[str, Any]] = Field(default_factory=list)
    #: CHẨN ĐOÁN cổng phủ, dạng máy đọc được — song song với `details`.
    #:
    #: `details` là văn xuôi tiếng Việt cho người đọc; phân loại theo nó phải
    #: khớp chuỗi, và khớp chuỗi đã hỏng một lần ở `sua_duoc`. Bốn mã ở
    #: `coverage_gate.LY_DO_CHAN_DOAN` phân biệt bốn bệnh cần bốn cách chữa
    #: khác nhau — thiếu vật · sai kiểu · không nối được · nối được nhiều vật.
    chan_doan_nghia_vu: list[dict[str, Any]] = Field(default_factory=list)
    #: CHẨN ĐOÁN CỔNG PHỦ theo TỪNG nghĩa vụ (`coverage_gate.chan_doan_phu_cau_truc`).
    #:
    #: Khác `chan_doan_nghia_vu`: có hàng cho cả nghĩa vụ ĐÃ phủ, mỗi nhánh luật
    #: một mã ổn định, con trỏ RFC 6901 vào hợp đồng — và KHÔNG chở tên. Chỉ có
    #: khi route dừng ở `structural_coverage`; `None` ở mọi kết cục khác. Không
    #: vào envelope, không đổi phán quyết.
    coverage_diagnostic: dict[str, Any] | None = None
    #: CHẨN ĐOÁN CỔNG PHỦ TRỰC QUAN (`visual_obligations.chan_doan_truc_quan`).
    #:
    #: Một Ô TRỐNG nữa, cùng lý do với `scene3d` ngay dưới: cổng ấy phải ĐỌC CẢNH,
    #: mà `route` không được biết tới tầng trình bày. `pipeline` chạy cổng sau khi
    #: đổ cảnh vào, rồi đổ chẩn đoán vào đây.
    #:
    #: `None` ở mọi kết cục khác — kể cả khi mọi nghĩa vụ trực quan đều được phủ,
    #: để ca hợp lệ trùng từng byte với trước wave.
    visual_diagnostic: dict[str, Any] | None = None
    exec_status: str | None = None
    total_steps: int | None = None
    frame_count: int | None = None
    #: Trạng thái bộ nhớ CUỐI do interpreter sinh. Đây là thứ duy nhất được đem
    #: so với ground truth độc lập — so với `envelope` là so với thứ đã qua tay
    #: adapter thị giác.
    final_memory: dict[str, Any] | None = None
    envelope: dict[str, Any] | None = None
    #: QUAN TRẮC grounding — không gác cửa, không vào A/B, không tầng nào đọc để
    #: chấm. Có mặt vì PHASE 5 lượt 2 không đo được **mức lệch danh xưng giữa hai
    #: lượt LLM**: mọi ca grounding đều phát cùng một câu `reason`, còn số lượng
    #: giả thiết và trích dẫn hỏng thì mất hẳn. Ghi ra đây để lượt sau đếm được
    #: thay vì suy.
    grounding_assumptions: list[str] = Field(default_factory=list)
    grounding_unresolved_citations: list[str] = Field(default_factory=list)
    #: QUAN TRẮC §7 — cũng KHÔNG gác cửa. Ba con số của chỉ thị SCALE
    #: NORMALIZATION được sinh ở đây thay vì để bộ đo dựng lại từ artifact:
    #: bộ đo dựng lại là bộ đo tự định nghĩa "biện minh" lần thứ hai, và hai
    #: định nghĩa sẽ trôi khỏi nhau đúng như sáu lần trước.
    #:
    #:   `justified_literals` / `unjustified_literals` → tỉ lệ literal có căn cứ
    #:   `constraints_checked` / `constraints_verified` → tỉ lệ ràng buộc nguồn
    #:   được BẢO TOÀN và KIỂM. `checked` là mẫu số, nên nghĩa vụ không có
    #:   checker không lọt vào — chưa thi hành thì không tính là đã kiểm.
    justified_literals: list[str] = Field(default_factory=list)
    unjustified_literals: list[str] = Field(default_factory=list)
    constraints_checked: list[str] = Field(default_factory=list)
    constraints_verified: list[str] = Field(default_factory=list)
    #: THẨM QUYỀN VỀ TÊN — `tên hợp đồng → tên chương trình`, do C₁a giải.
    #:
    #: C₁b, C₂ và `learner_surface` đã hỏi bản đồ này từ lâu. Bộ ĐO thì không:
    #: nó tự hoà giải bằng `khop_ky_hieu`, và ở V3 điều đó biến một chương
    #: trình ĐÚNG thành hai lượt `UNSAFE` — hợp đồng gọi mặt phẳng `(SMN)`, bộ
    #: nhớ gọi `SMN`, `khop_ky_hieu` không bóc được ngoặc, checker mất đối
    #: tượng, và một lỗi TRA TÊN bị đọc thành lỗi HÌNH HỌC (ERRATUM #4).
    #:
    #: Đây là lần thứ BẢY của cùng lớp lỗi. Phát bản đồ ra đây để mọi tầng —
    #: kể cả tầng ngoài `app/` — hỏi CÙNG MỘT thẩm quyền, thay vì viết bản
    #: hoà giải thứ tám.
    resolved_names: dict[str, str] = Field(default_factory=dict)
    #: `NormalizedSourceInvariantGate` — bốn con số của §4: `checked` ·
    #: `passed` · `violated` · `not_checkable`. Rỗng ⇔ lượt chạy chưa tới cổng.
    source_invariant_stats: dict[str, int] = Field(default_factory=dict)
    #: Cảnh 3D của miền hình học — **một Ô TRỐNG, không phải một phép tính**.
    #:
    #: `route` KHÔNG dựng nó và KHÔNG import `scene3d`: hướng phụ thuộc một
    #: chiều (engine không được biết tới tầng trình bày) là thứ
    #: `test_scene3d.py::test_KHONG_module_nao_o_TANG_DUOI_nhap_scene3d` giữ.
    #: Khai kiểu `dict` ở đây cho phép người GỌI đổ vào mà không ai phải nới
    #: ranh giới ấy — `pipeline._dung_scene3d` là người đổ.
    #:
    #: `None` khi bài không phải hình học, hoặc khi chương trình không chạy nổi.
    scene3d: dict[str, Any] | None = None
    #: W14 — bước BỔ SUNG dựng hình theo lớp (`formation.hoan_thien_dung_hinh`) chạy
    #: trước mọi cổng: băm chương trình gốc và chương trình đã bổ sung, trạng thái
    #: từng khối. Quan trắc, không gác cửa, không vào envelope.
    program_sha256_original: str | None = None
    program_sha256_completed: str | None = None
    formation_statuses: dict[str, str] = Field(default_factory=dict)
    #: W14 5a — `UNCHECKED_TRUSTED_FIXTURE` khi người gọi khai `NguonDe.FIXTURE_TIN_CAY`
    #: cho một hợp đồng không đề (nguồn KHÔNG được kiểm); `None` ở mọi trường hợp khác.
    source_check: str | None = None
    #: W15 — chứng chỉ giả định (`assumption_gate.kiem_gia_dinh`): trạng thái và chứng chỉ
    #: (`C0`/`C1`). Quan trắc, không vào envelope; kết cục từ chối ở tầng `assumption`
    #: mang thêm `reason_code`/`reason_subjects` như mọi lời từ chối có mã chi tiết.
    assumption_status: str | None = None
    assumption_certificate: str | None = None
    #: Quyết định U3: `True` ⇔ đề nêu khối đa diện theo từ vựng đóng
    #: (`shape_constraint.neu_khoi_da_dien`) — chỉ khi ấy route TỪ CHỐI theo cổng.
    assumption_enforced: bool | None = None
    #: W18 §16.3 — trạng thái đối chiếu của từng phép dựng điểm (`construction_binding`): đích
    #: chương trình → MATCHED/MISMATCHED/UNVERIFIED/AUXILIARY/OUT_OF_SCOPE, nhãn đích đề →
    #: NOT_REALIZED. Quan trắc, không vào envelope; rỗng ⇔ chưa tới chặng hoặc không có phép dựng.
    construction_binding: dict[str, str] = Field(default_factory=dict)


def _hong(
    stage: str,
    code: ErrorCode,
    reason: str,
    *,
    executable: bool = False,
    details: list[str] | None = None,
    weak: list[str] | None = None,
    **extra: Any,
) -> SemanticRouteOutcome:
    # §15.3: mọi lời từ chối mang nguyên nhân; mã trong bảng ⇒ nguyên nhân của bảng, còn lại UNKNOWN
    # trừ khi nơi từ chối đã phân xử theo đề (`refusal_cause.do_dai_khong_duong`/`mat_phang_khong_cat`).
    extra.setdefault("refusal_cause", theo_ma(extra.get("reason_code")))
    return SemanticRouteOutcome(
        stage_reached=stage,
        executable=executable,
        servable=False,
        error_code=code.value,
        failure_category=SEMANTIC_FAILURE_CATEGORY.get(code.value),
        reason=reason,
        details=details or [],
        weak_kinds=weak or [],
        **extra,
    )


def hong_truoc_khi_dung_ir(
    stage: str, code: ErrorCode, reason: str | None, **extra: Any
) -> SemanticRouteOutcome:
    """Phán quyết cho thất bại xảy ra **trước** khi có IR để thẩm định.

    ─── VÌ SAO HÀM NÀY TỒN TẠI ────────────────────────────────────────────

    Hai chặng LLM có thể hỏng trước khi `verify_and_compile` chạy được lần
    nào: đọc đề không ra hợp đồng, và viết chương trình không qua validator.
    Trước bản này, `pipeline._semantic_route_attempt` trả `None` cho cả hai —
    một kiểu trả về **không chở nổi phán quyết**. Nó vẫn phát `stage_reached`
    và `error_code` cho observer, nên telemetry đúng trong khi envelope giao
    cho học sinh mang `null` ở cả hai ô. Đó chính là `n1` của lượt đo cuối.

    Đặt ở ĐÂY chứ không dựng `SemanticRouteOutcome` thẳng trong `pipeline`:
    `route` là thẩm quyền duy nhất phát phán quyết của tuyến sinh ngữ nghĩa,
    và bản đồ `mã → loại` (`SEMANTIC_FAILURE_CATEGORY`) chỉ được tra ở một
    chỗ. Dựng bản thứ hai trong `pipeline` là cách bảo đảm hai bản sẽ trôi
    khỏi nhau — kho này đã dọn đúng lớp lỗi ấy ba lần.
    """
    return _hong(stage, code, reason or "", **extra)


def verify_and_compile(
    contract: RequestContract,
    spec: SemanticProgramSpec,
    *,
    execution_budget: int = DEFAULT_EXECUTION_BUDGET,
    presentation_budget: int = DEFAULT_PRESENTATION_BUDGET,
    nguon: NguonDe = NguonDe.CAN_DE,
) -> SemanticRouteOutcome:
    """Bọc mỏng quanh `_sau_grounding` để **gắn quan trắc grounding ở MỘT chỗ**.

    Thân hàm có 11 điểm thoát. Gắn tay vào từng chỗ thì lần thêm nhánh tiếp theo
    chắc chắn sót một cái, và sót ở đây là im lặng: trường quan trắc rỗng đọc
    y hệt "không có giả thiết nào", nên số liệu sai mà không ai thấy.

    W14 — DỰNG HÌNH THEO LỚP chạy TRƯỚC mọi cổng, cho chương trình compiler lẫn LLM
    (S4): mọi cổng phía sau, envelope và cảnh (`pipeline._dung_scene3d` gọi cùng hàm
    trên cùng đầu vào) thấy CÙNG một chương trình đã bổ sung — frame k ⇔ trace[k].
    Bảng mặt hỏng là một phán quyết có mã ở tầng `formation`, không phải ngoại lệ.
    """
    dung = hoan_thien_dung_hinh(spec, contract)
    quan_trac_dung = {"program_sha256_original": dung.sha_goc,
                      "program_sha256_completed": dung.sha_hoan_thien,
                      "formation_statuses": dict(dung.trang_thai_theo_khoi)}
    if dung.hong:
        return _hong(
            "formation",
            ErrorCode.SEMANTIC_PROGRAM_INVALID,
            "Bảng mặt của khối không hợp lệ: chỉ số đỉnh ngoài miền hoặc mặt dưới ba đỉnh.",
            details=[f"[SOLID_TOPOLOGY_MALFORMED] {k}" for k in dung.hong],
            reason_code="SOLID_TOPOLOGY_MALFORMED",
            **quan_trac_dung,
        )
    spec = dung.spec
    # W14 5a — đề rỗng không còn mặc nhiên là "chưa kiểm": chỉ `FIXTURE_TIN_CAY` khai
    # tường minh mới đi đường không kiểm nguồn, và kết quả ghi lại điều đó.
    ground = check_grounding(contract, spec, nguon=nguon)
    khong_kiem_nguon = nguon is NguonDe.FIXTURE_TIN_CAY and not (contract.problem_text or "").strip()
    if khong_kiem_nguon:
        quan_trac_dung["source_check"] = "UNCHECKED_TRUSTED_FIXTURE"
    # Cùng lý do "gắn ở MỘT chỗ" như trên: `_sau_grounding` có 11 điểm thoát,
    # nên số ràng buộc đã kiểm được nhét vào một ô do hàm bọc sở hữu thay vì
    # gắn tay ở nhánh nào chạy tới C₂.
    quan_trac: dict[str, Any] = {"checked": [], "verified": [], "ten": {},
                                 "nguon": {}}
    kq = _sau_grounding(
        contract, spec, ground,
        execution_budget=execution_budget,
        presentation_budget=presentation_budget,
        quan_trac=quan_trac,
        khong_kiem_nguon=khong_kiem_nguon,
    )
    return kq.model_copy(update={
        "grounding_assumptions": list(ground.assumptions),
        "grounding_unresolved_citations": list(ground.unresolved_citations),
        "justified_literals": list(ground.justified_literals),
        "unjustified_literals": list(ground.unjustified_literals),
        "grounding_given_evidence": list(ground.given_evidence),
        "constraints_checked": quan_trac["checked"],
        "constraints_verified": quan_trac["verified"],
        "resolved_names": quan_trac["ten"],
        "source_invariant_stats": quan_trac["nguon"],
        **quan_trac_dung,
    })


def _sau_grounding(
    contract: RequestContract,
    spec: SemanticProgramSpec,
    ground,
    *,
    quan_trac: dict[str, Any] | None = None,
    execution_budget: int = DEFAULT_EXECUTION_BUDGET,
    presentation_budget: int = DEFAULT_PRESENTATION_BUDGET,
    khong_kiem_nguon: bool = False,
) -> SemanticRouteOutcome:
    """Contract (đã đóng băng) + IR (LLM viết) → phán quyết tất định.

    THỨ TỰ CÓ Ý NGHĨA, không tuỳ tiện:

    1. **P2 grounding** trước hết — chương trình lấy dữ liệu ở đâu ra. Sai ở đây
       thì mọi kiểm định phía sau đều đang kiểm một bài KHÁC với đề.
    2. **C₁a** trước khi chạy — chương trình có *đường* tạo ra witness không.
       Chạy rồi mới hỏi là lãng phí, và lẫn "không có đường" với "có đường mà
       không đi".
    3. **Thực thi**.
    4. **C₁b** — witness có THẬT SỰ hiện ra trong lượt chạy này không.
    5. **C₂** — hậu điều kiện server-owned.
    6. **Biên dịch** — binding fail-closed (bất biến #34) nói lời cuối.
    """
    if not ground.ok:
        # `ErrorCode` giữ nguyên — đây vẫn là một thất bại grounding, và mở rộng
        # enum là đụng vào bề mặt mọi tầng phía sau đọc. Nhưng mã CHI TIẾT phải
        # lộ ra ở `details`: "khai đáp án làm giả thiết" và "không truy được về
        # đề bài" là hai bệnh khác hẳn nhau, và gộp chúng thì lượt phân loại
        # thất bại sau sẽ đếm nhầm — đúng cái Phase 5 vừa phải khai là thiếu sót.
        chi_tiet = list(ground.unresolved)
        if ground.error_code and ground.error_code != "INPUT_NOT_GROUNDED":
            chi_tiet.insert(0, f"[{ground.error_code}]")
        return _hong(
            "grounding",
            ErrorCode.INPUT_NOT_GROUNDED,
            "Chương trình dùng dữ liệu không truy được về đề bài.",
            details=chi_tiet,
            reason_code=ground.error_code or "INPUT_NOT_GROUNDED",
            reason_subjects=list(ground.refused_givens),
        )

    c1a = check_structural_coverage(contract, spec)
    # Ghi bản đồ tên NGAY khi có, không đợi tới nhánh thành công: một chương
    # trình chết ở C₁a vẫn là chương trình mà bộ đo cần đọc tên cho đúng.
    if quan_trac is not None:
        quan_trac["ten"] = dict(c1a.ten_da_hoa_giai)
    # C₁a trả `ok=False` cho CẢ HAI mức, và chúng hoàn toàn khác nhau:
    #   REQUESTED_OPERATION_UNCOVERED     — không có đường tạo witness ⇒ CHẶN
    #   SEMANTIC_VERIFICATION_UNAVAILABLE — có đường, chỉ thiếu checker ⇒ ĐI TIẾP
    # Chặn cả hai ở đây thì bài mức yếu không bao giờ được chạy, nên
    # `executable` của nó hoá False — tức route tự khai là "không làm được" một
    # bài mà nó làm được. Đó chính là chỗ hai tỉ lệ của luận văn bị bóp thành
    # một, và bóp một cách câm.
    if not c1a.ok and c1a.error_code == "REQUESTED_OPERATION_UNCOVERED":
        return _hong(
            "structural_coverage",
            ErrorCode[c1a.error_code],
            "Chương trình không có đường tạo ra thứ đề bài yêu cầu.",
            details=list(c1a.missing),
            weak=list(c1a.weak_kinds),
            chan_doan_nghia_vu=[c.model_dump(mode="json")
                                for c in c1a.chan_doan],
            # CÙNG NGUỒN với phán quyết: bảng trạng thái chính C₁a vừa ghi tại
            # từng nhánh — không phân tích lại `details`.
            coverage_diagnostic=chan_doan_phu_cau_truc(
                contract, c1a, route_stage="structural_coverage",
                route_code=ErrorCode[c1a.error_code].value),
        )

    # ── THẨM ĐỊNH TĨNH, NGAY TRƯỚC KERNEL (V3 §2–§4) ────────────────────────
    #
    # V3 đo được: 4/7 lượt hỏng chết ở `execution` vì toán hạng — điểm chưa
    # dựng, tỉ lệ `2:1`, sai kiểu. Cả ba đọc được từ chính chương trình. Chết ở
    # runtime nghĩa là mô hình KHÔNG có cơ hội sửa: vòng sửa của
    # `stage_semantic_program` đã đóng trước khi tới đây.
    #
    # Cổng này không đổi phán quyết cho chương trình đúng — nó chỉ đổi CHỖ
    # chương trình sai bị bắt, từ sau kernel lên trước kernel. `ErrorCode` giữ
    # nguyên, chi tiết đi vào `details`, đúng đường mà `grounding` đã đi.
    tinh = kiem_tinh(spec)
    if not tinh.ok:
        return _hong(
            "ir_static",
            ErrorCode.SEMANTIC_PROGRAM_INVALID,
            "Chương trình tham chiếu vật chưa dựng hoặc sai kiểu toán hạng.",
            details=[i.dong() for i in tinh.issues],
            weak=list(c1a.weak_kinds),
        )

    try:
        exec_res = SemanticProgramInterpreter(max_steps=execution_budget).execute(spec)
    except Exception as e:  # interpreter vỡ = hệ không thực thi được bài này
        # `details` phải có LOẠI lỗi tách khỏi lời kể. Đo được ở Wave 3.5: đây
        # là tầng DUY NHẤT trong bốn tầng phát ra `details` rỗng, nên một lượt
        # vỡ ở kernel chỉ để lại một câu tiếng Việt — và phân loại thất bại sau
        # đó không phân biệt được "song song nên không giao" với "chỉ số đỉnh
        # ngoài biên", hai bệnh mà kernel đã cố ý tách bằng mã lỗi riêng.
        ma = getattr(e, "code", None)
        return _hong(
            "execution",
            ErrorCode.SEMANTIC_PROGRAM_INVALID,
            f"Interpreter không thực thi được chương trình: {e}",
            details=[f"[{ma or type(e).__name__}]", str(e)],
            weak=list(c1a.weak_kinds),
            # §15.3: thiết diện rỗng — mặt phẳng ĐỀ cho không cắt khối, hay mặt phẳng hệ tự đặt?
            **(mat_phang_khong_cat(contract, spec, getattr(e, "mat_phang", None)) if ma == MA_KHONG_CAT else {}),
        )

    # Chạm trần thực thi phải BÁO, cấm cắt câm (luật cứng #12). Trace cụt thì
    # mọi kết luận phía sau đều dựa trên một lượt chạy DỞ DANG.
    if exec_res.status == "limit_reached":
        return _hong(
            "execution",
            ErrorCode.INTERPRETER_BUDGET_EXHAUSTED,
            f"Chương trình chạm trần thực thi ({execution_budget} bước) — "
            "hệ báo thay vì cắt câm rồi giao một mô phỏng dở dang.",
            weak=list(c1a.weak_kinds),
            exec_status=exec_res.status,
            total_steps=exec_res.total_steps,
        )

    # Từ đây trở xuống máy ĐÃ chạy xong bài. Mọi thất bại còn lại nói về BẰNG
    # CHỨNG, không nói về năng lực ⇒ `executable=True`.
    da_chay = {
        "executable": True,
        "exec_status": exec_res.status,
        "total_steps": exec_res.total_steps,
        "final_memory": dict(exec_res.final_memory),
        "weak": list(c1a.weak_kinds),
    }

    c1b = check_realized_coverage(contract, spec, exec_res,
                                  ten_da_hoa_giai=c1a.ten_da_hoa_giai)
    if not c1b.ok:
        return _hong(
            "realized_coverage",
            ErrorCode[c1b.error_code],
            "Có đường tạo witness nhưng lượt chạy này không đi qua.",
            details=list(c1b.missing),
            **da_chay,
        )

    # ── W18 §16 · PHÉP DỰNG ĐIỂM GẮN VỚI QUAN HỆ CỦA ĐỀ BẰNG DANH TÍNH ─────────────────────
    #
    # Trước bất biến nguồn: trung điểm sai đoạn mà tên khớp phải nhận lời từ chối CÓ CẤU TRÚC
    # (nguyên nhân CONSTRUCTION, nêu cả hai quan hệ) chứ không phải mã chung của bất biến toạ độ —
    # bất biến ấy giữ làm lưới thứ hai. LỆCH và ĐÍCH ĐẶT BẰNG TOẠ ĐỘ (W20 §17) ⇒ từ chối ở MỌI vùng
    # (lỗi toàn vẹn của chương trình, như U5); CHƯA ĐỐI CHIẾU ⇒ từ chối trong vùng U3, ngoài vùng chỉ
    # ghi. Lỗi bên trong ⇒ coi như chưa đối chiếu. Fixture tin cậy không đề: không có câu nào để gắn —
    # không kiểm (như cổng giả định).
    if not khong_kiem_nguon:
        try:
            dc = doi_chieu_phep_dung(contract, spec, c1a.ten_da_hoa_giai)
        except Exception as e:  # noqa: BLE001
            dc = KetQuaDoiChieu(reason_code=MA_CHUA_DOI_CHIEU,
                                details=(f"CONSTRUCTION_BINDING_ERROR {type(e).__name__}",))
        da_chay["construction_binding"] = dict(dc.trang_thai)
        if dc.reason_code in (MA_LECH_PHEP_DUNG, MA_TOA_DO_THAY_DUNG) or (
                dc.reason_code == MA_CHUA_DOI_CHIEU and neu_khoi_da_dien(contract.problem_text)):
            return _hong(
                "construction_binding",
                ErrorCode.INPUT_NOT_GROUNDED,
                {MA_LECH_PHEP_DUNG: "Phép dựng điểm không dùng đúng thực thể đề nêu.",
                 MA_TOA_DO_THAY_DUNG: "Điểm đề định nghĩa bằng quan hệ bị đặt bằng toạ độ, không được dựng."}.get(
                    dc.reason_code, "Chưa đối chiếu được phép dựng điểm với câu của đề."),
                details=list(dc.details),
                reason_code=dc.reason_code,
                reason_subjects=list(dc.subjects),
                **da_chay,
            )

    # ── P0 · NormalizedSourceInvariantGate ─────────────────────────────────
    #
    # Đặt TRƯỚC C₂ trong thân hàm nhưng SAU thực thi — cả hai điều kiện đều bắt
    # buộc: cần trạng thái cuối để đo, và phải chặn trước khi có gì được phục
    # vụ. Thứ tự với C₂ chọn thế này vì hai cổng hỏi hai câu, và câu ở đây
    # NGUYÊN THUỶ hơn: *"hình dựng ra có đúng dữ kiện đề cho không"*. Một
    # chương trình dựng sai thang thì phán quyết của C₂ về nghĩa vụ nói về một
    # hình khác với hình của đề.
    nguon = check_source_invariants(contract, exec_res,
                                    ten_da_hoa_giai=c1a.ten_da_hoa_giai)
    if quan_trac is not None:
        quan_trac["nguon"] = {
            "checked": nguon.checked, "passed": nguon.passed,
            "violated": len(nguon.violated),
            "not_checkable": len(nguon.not_checkable),
            "unresolved": len(nguon.unresolved),
        }
    if not nguon.ok:
        return _hong(
            "source_invariant",
            ErrorCode.POSTCONDITION_VIOLATED,
            ("Hình dựng ra không khớp dữ kiện đề cho." if nguon.violated
             else "Đề ràng buộc vị trí một điểm mà hệ chưa kiểm chứng được."),
            details=([f"[{nguon.error_code}]"] + list(nguon.violated)
                     + list(nguon.unresolved)),
            **da_chay,
        )

    post = check_postconditions(contract, spec, exec_res,
                                ten_da_hoa_giai=c1a.ten_da_hoa_giai)
    if quan_trac is not None:
        quan_trac["checked"] = list(post.checked)
        quan_trac["verified"] = list(post.verified)
    # C₂ nay có HAI kết cục âm, và chúng khác hẳn nhau:
    #   POSTCONDITION_VIOLATED            — chương trình tự mâu thuẫn
    #   SEMANTIC_VERIFICATION_UNAVAILABLE — checker không biểu diễn được vị từ
    # Gộp chúng là kết tội một chương trình có thể hoàn toàn đúng — lượt pilot 4
    # đo được đúng chuyện đó xảy ra hai lần.
    if post.violations:
        return _hong(
            "postconditions",
            ErrorCode.POSTCONDITION_VIOLATED,
            "Chương trình tự mâu thuẫn với nghĩa vụ nó tự khai.",
            details=list(post.violations),
            **da_chay,
        )
    if post.weak_kinds:
        da_chay["weak"] = sorted(set(da_chay["weak"]) | set(post.weak_kinds))

    # ── W15 · CHỨNG CHỈ GIẢ ĐỊNH ────────────────────────────────────────────
    #
    # Sau hậu điều kiện (cần trace + trạng thái đã kiểm), trước khi có gì được biên dịch
    # để phục vụ. Mọi giá trị SỐ người học thấy phải có chứng chỉ C0/C1; phụ thuộc một
    # kích thước đề không cho, hoặc chưa chứng minh được, đều TỪ CHỐI — không bao giờ
    # gắn nhãn "giả thiết" rồi vẫn tính (W15-D2). Thẩm quyền:
    # `docs/architecture/ASSUMPTION_CERTIFICATE_AMENDMENT.md`. Lỗi bên trong cổng ⇒
    # từ chối có mã (đóng an toàn), không bao giờ HTTP 500.
    #
    # Fixture tin cậy KHÔNG đề (W14 5a, `tests/nguon_fixture.py`): không có câu đề thì
    # không có tiền đề; người gọi đã KHAI không đo bằng chứng nguồn lẫn cổng giả định —
    # ghi lại, không kiểm. Tuyến sản phẩm không bao giờ khai lối này (khoá W14).
    #
    # Quyết định U3 (2026-10-03): cổng tính cho MỌI yêu cầu, nhưng chỉ TỪ CHỐI khi đề nêu
    # một khối đa diện theo từ vựng đóng — vùng có lỗ W12/W14 đã đo và có chứng chỉ C0/C1.
    # Ngoài vùng: ghi trạng thái (`assumption_enforced=False`), hành vi và cổng cũ giữ nguyên.
    gd_chan = not khong_kiem_nguon
    if khong_kiem_nguon:
        gd_status, gd_cc, gd_ma, gd_chi_tiet, gd_chu_the = (
            "UNCHECKED_TRUSTED_FIXTURE", None, None, [], [])
    else:
        try:
            gd_chan = neu_khoi_da_dien(contract.problem_text)
            gd = kiem_gia_dinh(contract, spec, exec_res, c1a.ten_da_hoa_giai,
                               execution_budget=execution_budget)
            gd_status, gd_cc, gd_ma = gd.status, gd.certificate, gd.reason_code
            gd_chi_tiet, gd_chu_the = list(gd.details), list(gd.subjects)
        except Exception as e:  # noqa: BLE001
            gd_status, gd_cc, gd_ma = _GD_CHUA_RO, None, MA_CHUA_CHUNG_MINH
            gd_chi_tiet, gd_chu_the = [f"ASSUMPTION_GATE_ERROR {type(e).__name__}"], []
    # U5: giá trị đọc qua một tên có nhiều định nghĩa với tới (ghi đè, bí danh, khôi phục) là lỗi
    # toàn vẹn của chương trình, không phải câu hỏi về giả định — từ chối ở MỌI vùng.
    gd_chan = gd_chan or any(d.startswith(MA_NHIEU_DINH_NGHIA) for d in gd_chi_tiet)
    ghi_gd = {"assumption_status": gd_status, "assumption_certificate": gd_cc, "assumption_enforced": gd_chan,
              "construction_binding": da_chay.get("construction_binding", {})}
    da_chay.update(ghi_gd)
    if gd_chan and gd_status not in (_GD_AN_TOAN, _GD_KHONG_AP_DUNG):
        return _hong(
            "assumption",
            ErrorCode.INPUT_NOT_GROUNDED,
            ("Đáp số phụ thuộc một kích thước đề bài không cho." if gd_ma == MA_PHU_THUOC
             else "Phép dựng thiết diện không dùng đúng thực thể đề nêu." if gd_ma == MA_LECH_PHEP_DUNG
             else "Chưa chứng minh được đáp số chỉ phụ thuộc dữ kiện đề cho."),
            details=gd_chi_tiet,
            reason_code=gd_ma,
            reason_subjects=gd_chu_the,
            **da_chay,
        )

    try:
        # Interpreter chạy lại bên trong `compile`. Tất định nên kết quả trùng
        # khít; đổi chữ ký public của adapter chỉ để tiết kiệm một lượt chạy
        # thuần tuý không đáng, và sẽ phải sửa kèm bộ test đang khoá nó.
        envelope = compile_semantic_program_to_envelope(
            spec,
            execution_budget=execution_budget,
            presentation_budget=presentation_budget,
        )
    except VisualBindingUnresolved as e:
        return _hong(
            "binding",
            ErrorCode.SEMANTIC_PROGRAM_INVALID,
            f"Hợp đồng thị giác không phân giải được: {e}",
            **da_chay,
        )
    except (ValueError, KeyError, TypeError) as e:
        return _hong(
            "compile",
            ErrorCode.SEMANTIC_PROGRAM_INVALID,
            f"Không biên dịch được envelope: {e}",
            **da_chay,
        )

    # BIÊN VẬN CHUYỂN — chặn TRƯỚC khi envelope rời khỏi đây.
    #
    # `main.py` serialize envelope để ghi cache, tức SAU khi mọi cổng đã nói
    # PASS. Một `Vec3` hay `Fraction` lọt vào envelope sẽ nổ ở đó thành HTTP
    # 500 không địa chỉ — đúng bug GENERALIZATION MATRIX tìm ra. Ở đây nó là
    # một phán quyết có mã, có tầng.
    loi_van_chuyen = check_envelope_transport(envelope)
    if loi_van_chuyen is not None:
        return _hong(
            "transport",
            ErrorCode.SEMANTIC_PROGRAM_INVALID,
            loi_van_chuyen,
            **da_chay,
        )

    # BỀ MẶT HỌC SINH — cổng cuối, và là cổng DUY NHẤT quay về phía màn hình.
    #
    # Mọi cổng phía trên nhìn về phía CHƯƠNG TRÌNH: cú pháp, dữ liệu, phủ nghĩa
    # vụ, hậu điều kiện, binding có phân giải được. Qua hết chúng vẫn còn lọt
    # được đúng thứ đã ship: chương trình chạy đúng, lời kể đúng, envelope sạch —
    # mà ngăn xếp trên hình rỗng suốt bảy bước. Chạy SAU `compile` vì câu hỏi là
    # về những khung SẼ ĐƯỢC PHÁT, không phải về ý định của chương trình.
    surface = check_learner_surface(contract, spec, exec_res, envelope,
                                    ten_da_hoa_giai=c1a.ten_da_hoa_giai)
    if not surface.ok:
        code = ErrorCode.LEARNER_SURFACE_INCOMPLETE
        return SemanticRouteOutcome(
            stage_reached="learner_surface",
            # `executable=True` là CÓ CHỦ ĐÍCH: hệ chạy được bài này. Cái thiếu
            # là đường lên màn hình, không phải năng lực.
            executable=True,
            servable=False,
            error_code=code.value,
            failure_category=SEMANTIC_FAILURE_CATEGORY[code.value],
            reason=(
                "Mô phỏng chạy được nhưng màn hình chưa mang đủ thông tin để "
                "hiểu bài: " + "; ".join(surface.invisible)
            ),
            details=list(surface.invisible),
            weak_kinds=sorted(set(da_chay["weak"])),
            exec_status=exec_res.status,
            total_steps=exec_res.total_steps,
            frame_count=len(envelope["config"]["frames"]),
            final_memory=dict(exec_res.final_memory),
            envelope=envelope,
            **ghi_gd,
        )

    # Mức YẾU: chạy được, biên dịch được, nhưng chưa có checker độc lập cho
    # nghĩa vụ đề đòi ⇒ KHÔNG phát canonical. Đây là `verification_gap`, và nó
    # là chỗ hai tỉ lệ của luận văn tách nhau ra.
    weak_tong = sorted(set(da_chay["weak"]))
    if weak_tong:
        code = ErrorCode.SEMANTIC_VERIFICATION_UNAVAILABLE
        return SemanticRouteOutcome(
            stage_reached="verification",
            executable=True,
            servable=False,
            error_code=code.value,
            failure_category=SEMANTIC_FAILURE_CATEGORY[code.value],
            reason=(
                "Mô phỏng chạy được nhưng hệ chưa có cách kiểm chứng độc lập "
                f"nghĩa vụ: {', '.join(weak_tong)}."
            ),
            weak_kinds=weak_tong,
            exec_status=exec_res.status,
            total_steps=exec_res.total_steps,
            frame_count=len(envelope["config"]["frames"]),
            final_memory=dict(exec_res.final_memory),
            envelope=envelope,
            **ghi_gd,
        )

    return SemanticRouteOutcome(
        stage_reached="served",
        executable=True,
        servable=True,
        exec_status=exec_res.status,
        total_steps=exec_res.total_steps,
        frame_count=len(envelope["config"]["frames"]),
        final_memory=dict(exec_res.final_memory),
        envelope=envelope,
        **ghi_gd,
    )
