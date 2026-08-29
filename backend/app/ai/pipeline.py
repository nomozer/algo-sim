"""Pipeline LLM (M3): analyze → classify → simulate → validate → envelope.

Ranh giới cứng: LLM chỉ trích xuất, phân loại và điền CONFIG đầu vào.
Timeline/diễn biến/kết quả do engine tất định phía frontend sinh ra.
SimulationEnvelope hợp lệ CHỈ được phát hành sau server-side validation —
không bao giờ trả thẳng JSON của Gemini cho frontend (M3 §6).
"""

from __future__ import annotations

import json

from app.simulation.catalog import CATALOG, catalog_text, llm_choices
from app.simulation.completeness_gate import (
    check_represented_coverage,
    check_requested_combination,
)
from app.simulation.computation_gate import check_computation_ownership
from app.simulation.execution_authority_gate import check_execution_authority
from app.simulation.scope import DomainScope, Simulatability
from app.simulation.scope_gate import (
    SCOPE_FAILURE_CATEGORY,
    check_scope_and_simulatability,
)
from app.simulation.pipeline_stages import stage_shortfall_message
from app.simulation.sufficiency_gate import (
    check_input_sufficiency,
    check_input_sufficiency_for_targets,
)
from app.simulation.families import selector_for_token
from app.simulation.mechanism_gate import (
    ROUTE_MECHANISM_FAMILY_MISMATCH_MSG as _MISMATCH_MSG,
    check_mechanism_consistency_for_target,
    check_mechanism_ownership,
    check_variant_consistency,
)
from app.simulation.mechanisms import analyze_exposed_values, canonical_mechanism, mechanism_family
from typing import TYPE_CHECKING

from app.ai.telemetry import stage_scope

if TYPE_CHECKING:  # tránh import vòng lúc chạy: contract kéo theo cả cây pydantic
    from app.simulation.semantic_program.contract import SemanticProgramSpec
    from app.simulation.semantic_program.request_contract import RequestContract
    from app.simulation.semantic_program.route import SemanticRouteOutcome
from app.simulation.operations import analyze_exposed_operations
from app.simulation.error_codes import ErrorCode

#: Trần lượt sửa của `stage_semantic_program`. HẰNG SỐ, không theo độ dài trace —
#: đó là điều giữ cho claim D1 (số lượt LLM chặn bởi call graph) còn đúng. Bằng
#: `stage_simulate` để hai đường không lệch nhau vô cớ.
MAX_SEMANTIC_PROGRAM_ATTEMPTS = 3


def _emit(observer, event_type: str, **data) -> None:
    """M14 §F2 — phát event cho observer THỤ ĐỘNG (None → no-op, hành vi
    production không đổi một bit)."""
    if observer is not None:
        observer.emit(event_type, data)
from app.simulation.dsl.manifest import manifest_capability_summary
from app.simulation.dsl.executor import execute_simulation
from app.simulation.patterns import (
    deterministic_fill,
    instantiate,
    run_gates,
    validate_params,
)
from app.simulation.representation import (
    build_representation_plan,
    check_scene_consistency,
    required_roles,
    scene_mode_guidance,
)
from app.simulation.semantic import check_semantic_compatibility, check_system_flow_consistency
from app.ai.gemini import call_gemini, load_skill

# ── Schema structured output từng stage ───────────────────────

ANALYZE_SCHEMA = {
    "type": "OBJECT",
    "properties": {
        "objects": {"type": "ARRAY", "items": {"type": "STRING"}},
        "data": {
            "type": "ARRAY",
            "items": {
                "type": "OBJECT",
                "properties": {
                    "description": {"type": "STRING"},
                    "values": {"type": "ARRAY", "items": {"type": "NUMBER"}, "nullable": True},
                    "labels": {"type": "ARRAY", "items": {"type": "STRING"}, "nullable": True},
                },
                "required": ["description"],
            },
        },
        "relations": {"type": "ARRAY", "items": {"type": "STRING"}},
        "processes": {"type": "ARRAY", "items": {"type": "STRING"}},
        "constraints": {"type": "ARRAY", "items": {"type": "STRING"}},
        "goal": {"type": "STRING"},
        "input_description": {"type": "STRING"},
        "output_description": {"type": "STRING"},
        # M7.9: năng lực đề CẦN — để classify đối chiếu với năng lực từng mô phỏng
        "required_capabilities": {"type": "ARRAY", "items": {"type": "STRING"}, "nullable": True},
        # "step_by_step" = cảnh được DỰNG/HÌNH THÀNH dần; "prebuilt" = cảnh cho sẵn
        "scene_construction": {
            "type": "STRING",
            "enum": ["prebuilt", "step_by_step"],
            "nullable": True,
        },
        # M7.11: SEMANTIC REQUIREMENTS — vai trò ngữ nghĩa đề cần (taxonomy:
        # structural/textual/logical/numeric/interactive/relational/movement/temporal)
        "entity_roles": {"type": "ARRAY", "items": {"type": "STRING"}, "nullable": True},
        "relation_roles": {"type": "ARRAY", "items": {"type": "STRING"}, "nullable": True},
        "process_roles": {"type": "ARRAY", "items": {"type": "STRING"}, "nullable": True},
        "interaction_needs": {"type": "ARRAY", "items": {"type": "STRING"}, "nullable": True},
        "visual_needs": {"type": "ARRAY", "items": {"type": "STRING"}, "nullable": True},
        "temporal_needs": {"type": "ARRAY", "items": {"type": "STRING"}, "nullable": True},
        # M20 W3: PHẠM VI + KHẢ-MÔ-PHỎNG — LLM KHAI, server PHÁN
        # (`app/simulation/scope_gate.py`). Nằm trong `required` và có `enum`
        # đóng: cổng fail-closed khi THIẾU trường, nên trường phải được structured
        # output bảo đảm chứ không trông vào việc model nhớ khai. Giá trị lấy
        # NGUYÊN từ `app/simulation/scope.py` — khoá bởi test đồng bộ.
        "domain_scope": {
            "type": "STRING",
            "enum": [s.value for s in DomainScope],
        },
        "simulatability": {
            "type": "STRING",
            "enum": [s.value for s in Simulatability],
        },
        # M13: nguồn kết quả cuối của bài — SERVER dùng để chặn "AI tự giải rồi
        # dựng cảnh minh hoạ đáp án" (computation-ownership gate). Bắt buộc +
        # fail-closed: xem app/simulation/computation_gate.py.
        "result_ownership": {
            "type": "STRING",
            "enum": ["provided", "rule_derivable", "algorithmic"],
        },
        # M14 §E4 — cơ chế THỦ TỤC đề YÊU CẦU (nếu ép cụ thể). Nullable +
        # fail-closed: thiếu → mechanism gate xử như KHÔNG khớp owned (không phá
        # analyze domain khác). Mô tả CƠ CHẾ (thao tác), KHÔNG tên thuật toán,
        # KHÔNG kết quả (§O7).
        "prescribed_procedure": {
            "type": "STRING",
            "enum": list(analyze_exposed_values()),
            "nullable": True,
        },
        # M17-RC1 §D — TẤT CẢ cơ chế đề yêu cầu (đề có thể hỏi NHIỀU thao tác).
        # `prescribed_procedure` giữ nguyên vai trò "một cơ chế chính" cho các
        # gate cũ; trường này bổ sung để phát hiện MẤT MÁT NGỮ NGHĨA khi đề hỏi
        # nhiều mà spec chỉ dựng được một.
        "requested_mechanisms": {
            "type": "ARRAY",
            "items": {"type": "STRING", "enum": list(analyze_exposed_values())},
            "nullable": True,
        },
        # M17-RC1 §C1 — TẤT CẢ *mục tiêu* (operation) đề yêu cầu. Đây mới là
        # danh tính đúng của yêu cầu: `find_max` và `find_min` là HAI operation
        # dùng CHUNG mechanism `track_extreme`, nên định danh bằng mechanism
        # (trường trên) gộp chúng thành một và bỏ im lặng một nửa. Enum phủ
        # 9/9 family (mechanism chỉ phơi 3) nên gate nhận được dữ liệu ở MỌI
        # family. Mọi giá trị đều có target/executor thật (dẫn xuất từ CATALOG).
        "requested_operations": {
            "type": "ARRAY",
            "items": {"type": "STRING", "enum": list(analyze_exposed_operations())},
            "nullable": True,
        },
        # M17 W2B-S1 — YÊU CẦU CÓ CẤU TRÚC kèm MỤC TIÊU. `requested_operations`
        # ở trên chỉ nói "làm việc gì"; trường này nói thêm "trên mục tiêu nào",
        # để hai phép đếm trên hai điều kiện khác nhau KHÔNG bị gộp thành một
        # (fixture #10 — mất mát ngữ nghĩa đo được). Mục tiêu khai bằng TRƯỜNG
        # CÓ CẤU TRÚC, KHÔNG phải id tự do do LLM tự đặt.
        "requested_requirements": {
            "type": "ARRAY",
            "nullable": True,
            "items": {
                "type": "OBJECT",
                "properties": {
                    "operation": {"type": "STRING",
                                  "enum": list(analyze_exposed_operations())},
                    "query_group": {"type": "INTEGER", "nullable": True},
                    "filter_column": {"type": "STRING", "nullable": True},
                    "filter_op": {"type": "STRING", "nullable": True},
                    "filter_value": {"type": "STRING", "nullable": True},
                    "aggregate_func": {"type": "STRING", "nullable": True},
                    "aggregate_column": {"type": "STRING", "nullable": True},
                    "projection_columns": {"type": "ARRAY", "items": {"type": "STRING"},
                                           "nullable": True},
                    "sort_column": {"type": "STRING", "nullable": True},
                    "sort_direction": {"type": "STRING", "nullable": True},
                    "limit": {"type": "INTEGER", "nullable": True},
                },
                "required": ["operation"],
            },
        },
        "notes": {"type": "STRING", "nullable": True},
    },
    "required": [
        "objects",
        "data",
        "relations",
        "processes",
        "constraints",
        "goal",
        "input_description",
        "output_description",
        "result_ownership",
        "domain_scope",
        "simulatability",
    ],
}


def _completeness_phase2(
    analysis: dict, target_id: str, config: object, plan: object, observer,
    *, variant: str | None = None,
) -> dict | None:
    """M17-RC1 §D PHA 2 / §C1 — spec ĐÃ CHỐT có bỏ sót yêu cầu nào không?

    MỘT chỗ duy nhất, gọi từ **mọi** đường trả envelope ok (selector fast-path,
    pattern reuse, composed). RC1-C đã bắt được đúng lỗi này một lần: nhánh
    selector `return` trước chỗ gate được cắm nên family sorting lọt cổng. Gom
    về một hàm để không đường nào lặng lẽ bỏ qua được nữa — test
    `test_moi_duong_tra_ok_deu_qua_phase2` khoá bằng cách đếm call site.

    Trả envelope unsupported khi thiếu sót; None khi đủ.
    """
    spec = CATALOG[target_id]
    families = {m.family_id.value for m in spec.family_memberships}
    owned = {m for mb in spec.family_memberships for m in mb.owned_mechanisms}
    verdict = check_represented_coverage(
        analysis, families, owned, config, target_id=target_id, variant=variant,
    )
    _emit(observer, "gate_checked", gate="completeness_represented",
          fired=bool(verdict), reason_code=verdict[0].value if verdict else None)
    if verdict is None:
        return None
    _emit(observer, "envelope", status="unsupported", simulation_id=None,
          failure_category="semantic_incomplete")
    return {
        "status": "unsupported",
        "reason": verdict[1],
        "failure_category": "semantic_incomplete",
        "error_code": verdict[0].value,
        "completeness": verdict[2],
        "representation_plan": plan,
        "analysis": analysis,
    }


def _classify_schema() -> dict:
    return {
        "type": "OBJECT",
        "properties": {
            "status": {"type": "STRING", "enum": ["ok", "unsupported"]},
            "simulation_id": {
                "type": "STRING",
                "nullable": True,
                # M14 §C2 — menu = llm_choices (concrete llm-facing + selector token);
                # bubble/insertion ẩn, comparison_sort thay chỗ.
                "enum": llm_choices(),
            },
            "reason": {"type": "STRING", "nullable": True},
        },
        "required": ["status"],
    }


async def _call_json(
    api_key: str,
    skill: str,
    user_text: str,
    schema: dict,
    temperature: float,
    retries: int,
    on_retry_note: str,
) -> dict:
    """Gọi Gemini + parse JSON, retry khi trả về không phải JSON hợp lệ."""
    prompt = user_text
    for attempt in range(retries + 1):
        # Nhãn stage cho telemetry token (spec §6.1). Dùng ContextVar thay vì
        # tham số của call_gemini: hàm đó có 13 test double, thêm tham số quan
        # trắc vào chữ ký làm gãy hết.
        with stage_scope(skill):
            raw = await call_gemini(api_key, load_skill(skill), prompt, schema, temperature)
        try:
            parsed = json.loads(raw)
            if isinstance(parsed, dict):
                return parsed
        except json.JSONDecodeError:
            pass
        if attempt < retries:
            prompt = f"{user_text}\n\n{on_retry_note}"
    raise RuntimeError(f"Giai đoạn {skill} không trả về JSON hợp lệ sau {retries + 1} lần.")


# ── Các stage ─────────────────────────────────────────────────

async def stage_analyze(text: str, api_key: str) -> dict:
    user = f'Đầu vào:\n"""\n{text}\n"""'
    return await _call_json(
        api_key, "analyze", user, ANALYZE_SCHEMA, 0.1, 1,
        "Lần trước không phải JSON hợp lệ. Trả về đúng một đối tượng JSON theo schema.",
    )


async def stage_semantic_analyze(
    text: str, api_key: str, domain: str | None = None
) -> tuple["RequestContract | None", str | None]:
    """Đề bài → `RequestContract` ĐÃ ĐÓNG BĂNG (dữ liệu đề cho + nghĩa vụ).

    VÌ SAO TÁCH HẲN LƯỢT NÀY, không gộp vào lượt viết chương trình: gộp thì cùng
    một lượt sinh ra cả *nghĩa vụ* lẫn *chương trình*, nên mô hình chỉ việc khai
    nghĩa vụ nào mà chương trình nó vừa viết đã thoả. C₁a khi ấy còn đúng về mặt
    hình thức nhưng không còn kiểm được gì — nó tự đối chiếu một nguồn với chính
    nguồn ấy. Hai lượt tách rời tốn thêm một call và đổi lại giữ cho cổng phủ có
    thật sự là một cổng.

    Server ĐÓNG BĂNG, không chép nguyên lời LLM: `build_request_contract` loại
    nghĩa vụ ngoài taxonomy và mục dữ liệu thiếu `id` ngay tại biên.

    ─── `domain` (Wave 2, sau Phase 5) ──────────────────────────────────────

    `None` = miền Tin học, tức **hành vi trước Wave 2 nguyên vẹn**: cùng skill,
    cùng schema, cùng enum 19 nghĩa vụ. Truyền `hinh_hoc` thì đổi ĐỒNG BỘ ba
    thứ — skill đọc đề, enum nghĩa vụ trong schema, và bộ lọc phía server. Đổi
    thiếu một trong ba là đúng cái lỗ Phase 5 đo được: skill viết chương trình
    đã sang hình học từ lâu, còn skill đọc đề thì không, nên mô hình chọn nghĩa
    vụ Tin học cho bài hình học ở 3/6 ca hợp lệ.
    """
    from app.simulation.semantic_program.analyze_contract import (
        SEMANTIC_ANALYZE_SCHEMA,
        analyze_schema_for,
        build_request_contract,
    )
    from app.simulation.semantic_program.domain_profile import analyze_skill_for

    schema = analyze_schema_for(domain) if domain else SEMANTIC_ANALYZE_SCHEMA
    user = f'Đề bài:\n"""\n{text}\n"""'
    with stage_scope("semantic_analyze"):
        raw = await call_gemini(
            api_key,
            load_skill(analyze_skill_for(domain) if domain else "semantic_analyze"),
            user,
            schema,
            0.1,
        )

    try:
        payload = json.loads(raw)
    except (json.JSONDecodeError, TypeError) as e:
        return None, f"SEMANTIC_ANALYZE_INVALID: JSON không parse được ({e})"
    if not isinstance(payload, dict):
        return None, (
            "SEMANTIC_ANALYZE_INVALID: đầu ra không phải một đối tượng JSON "
            f"(nhận {type(payload).__name__})"
        )
    # `text` đi kèm là bậc P1: `analyze` có thể bỏ trống ô giá trị dù đề ghi rõ
    # literal (đã quan sát: `values=null` cho đề chứa `{[()]}`). Có đề gốc thì
    # server tự neo được literal về span thay vì phụ thuộc model nhớ chép.
    return build_request_contract(payload, problem_text=text, domain=domain), None


def _facts_for_prompt(contract: "RequestContract") -> str:
    """Danh mục dữ liệu đề cho, kèm ĐÚNG `id` mà IR phải ghim vào.

    Không có khối này thì `source_fact_id` là bất khả thi chứ không phải khó:
    lượt viết chương trình chưa từng nhìn thấy hợp đồng, nên không có id nào để
    trích dẫn, và P2 sẽ từ chối 100% chương trình — kể cả chương trình đúng.
    """
    if not contract.input_facts:
        return "Đề không cho dữ liệu cụ thể nào."

    def _hien(f) -> str:
        """Cách VIẾT của một mục dữ liệu, cho MẮT ĐỌC.

        ─── BẪY ĐÃ CẮN, ĐO ĐƯỢC TRÊN LƯỢT LIVE 2026-08-24 ──────────────────
        `f.values` là biểu diễn dành cho GROUNDING: một chuỗi được mở thành
        *toàn bộ + từng ký tự* (`gia_tri_kem_ky_tu`) để chương trình khai đầu
        vào dạng mảng ký tự vẫn qua được P2. Đem nguyên biểu diễn ấy nối bằng
        dấu phẩy thì mục `{[()]}` hiện ra thành:

            Chuỗi đóng mở ngoặc: {[()]}, {, [, (, ), ], }

        — dấu phẩy vừa là ký tự phân cách vừa nằm cạnh toàn dấu ngoặc. Mô hình
        đọc mớ đó rồi khai `['{', '<', '(', ')', '>']`: **bịa ra dấu ngoặc
        nhọn**. Cổng grounding bắt đúng và từ chối, nhưng thứ bị hỏng là CÁCH
        HỎI, không phải mô hình.

        `source_text` là literal ĐÚNG NHƯ NÓ NẰM TRONG ĐỀ, do extractor tất
        định cắt ra kèm span. Có nó thì hiển thị nó — không có cách viết nào
        trung thực hơn thế.
        """
        # CHUẨN HOÁ THANG THẮNG `source_text`. Mục đã viết lại thì `source_text`
        # còn giữ nguyên văn (`4a/5`) — chính là thứ mô hình KHÔNG được dùng
        # nữa. Hiện nó ra thì mô hình lại đi tìm một giá trị cho `a`, tức đúng
        # bế tắc mà phép chuẩn hoá sinh ra để gỡ.
        if f.scale_symbol:
            goc = ", ".join(str(v) for v in f.original_values)
            return f": {', '.join(str(v) for v in f.values)}  (đề viết: {goc})"
        if f.source_text:
            return f': "{f.source_text}"'
        if f.values:
            return f": {', '.join(str(v) for v in f.values)}"
        return " (đề chưa cho giá trị)"

    dong = [f"- id `{f.fact_id}` — {f.label}{_hien(f)}" for f in contract.input_facts]
    dau = ""
    if contract.scale_binding is not None:
        # Nói THẲNG rằng thang đã được chốt, và chốt bởi ai. Không có dòng này
        # thì mô hình thấy `AB = 1` mà vẫn tưởng mình được chọn lại thang.
        b = contract.scale_binding
        dau = (
            f"Đề dùng ký hiệu tỉ lệ tự do `{b.symbol}`. Hệ ĐÃ CHỐT "
            f"`{b.symbol} = {b.canonical_value}` và viết lại các số dưới đây "
            f"theo thang ấy. Dùng đúng những số này; KHÔNG tự chọn giá trị "
            f"khác cho `{b.symbol}`, KHÔNG khai lại `{b.symbol}` như một biến.\n"
        )
    return (dau + "Dữ liệu đề cho (ghim `source_fact_id` về đúng id dưới đây):\n"
            + "\n".join(dong))


def _obligations_for_prompt(contract: "RequestContract") -> str:
    """Danh xưng CHUNG cho hai lượt LLM — container và witness của từng nghĩa vụ.

    VÌ SAO CẦN (đo được ở lượt pilot 3): hai lượt được tách rời có chủ đích, nên
    chúng không dùng chung không gian tên. `semantic_analyze` khai
    `extremum(container='day_so_hoc', witness='so_lon_nhat_nho_hon_100')`, còn
    `semantic_program` đặt tên biến hoàn toàn khác, và C₁a báo đúng là "container
    chưa khai báo". 12/40 case trượt vì đúng khe hở này.

    Việc này KHÔNG làm C₁a rỗng nghĩa. C₁a hỏi *chương trình có SINH RA witness
    không*, không hỏi *nó đặt tên thế nào*. Tính độc lập cần giữ là "hợp đồng
    nêu yêu cầu TRƯỚC khi chương trình được viết", và điều đó vẫn nguyên vẹn:
    nghĩa vụ đã đóng băng xong mới tới lượt viết chương trình.
    """
    if not contract.obligations:
        return "Đề không đòi kết quả cụ thể nào."
    dong = [
        f"- {ob.kind}: dữ liệu bị hỏi nằm trong biến `{ob.container}`, "
        f"kết quả nằm trong biến `{ob.witness}`"
        for ob in contract.obligations
        if ob.witness
    ]
    if not dong:
        return "Đề không đòi kết quả cụ thể nào."
    return (
        "Nghĩa vụ của đề. CẢ HAI tên dưới đây đều phải có mặt trong "
        "`memory_declarations`, đúng từng chữ:\n"
        + "\n".join(dong)
        + "\n(Dãy do đề mô tả mà không liệt kê sẵn thì vẫn phải dựng thành một "
        "biến chứa dữ liệu — mô phỏng cần hiện dãy đó lên, không chỉ tính ra "
        "đáp số.)"
    )


async def stage_semantic_program(
    text: str,
    analysis: dict,
    api_key: str,
    contract: "RequestContract | None" = None,
    observer=None,
    domain: str | None = None,
) -> tuple["SemanticProgramSpec | None", str | None]:
    """LLM tổng hợp `SemanticProgramSpec` — ≤3 lượt, lỗi validator gửi ngược.

    Trả `(spec, None)` khi hợp lệ, `(None, lý_do)` khi hỏng.

    R0 nguyên vẹn: LLM viết CHƯƠNG TRÌNH, không quyết kết quả — interpreter tất
    định mới là authority (luật cứng #11).

    ĐỔI TỪ MỘT LƯỢT → ≤3 (2026-08-23). Bản cũ ghi *"retry ở đây chỉ để cứu lỗi
    parse, không phải để dò dần cho đúng"* — vế sau vẫn đúng và vẫn được giữ,
    nhưng vế đầu hoá ra bao trùm hơn ta tưởng. Tám lượt probe E2E liên tiếp trên
    một đề (ghép ngoặc bằng ngăn xếp, route `serve`, API thật) chết ở TÁM lỗi
    hình dạng KHÁC NHAU, mỗi lần một chỗ: `container` nhận biểu thức, rồi nhận
    literal, `pop` viết như biểu thức, rồi `peek` viết như câu lệnh, biến bool
    dùng thẳng làm điều kiện… Không lỗi nào là hiểu sai đề — chương trình dựng
    đúng nghĩa vụ, đúng cấu trúc dữ liệu, chỉ sai CÁCH VIẾT. Và mỗi lỗi ấy đều
    đã có sẵn một thông báo Pydantic nói đúng chỗ sai.

    Vá từng lớp bằng luật prompt là đuổi theo một biến ngẫu nhiên: sửa xong lớp
    này thì lượt sau model rơi vào lớp khác (`RULES §3c` gọi đây là
    DEEP_HARDENING). Đưa lỗi ngược cho chính nó sửa thì cả LỚP biến mất một lần
    — đúng khuôn `stage_simulate` đã dùng từ M3.

    Trần là HẰNG SỐ, nên claim D1 không suy suyển: số lượt LLM vẫn bị chặn bởi
    call graph chứ không đi theo độ dài trace. Chương trình đúng thì interpreter
    vẫn tự sinh toàn bộ bước mà không tiêu thêm một token nào.

    Cấu trúc và enum do `responseSchema` cưỡng chế (constrained decoding). Nhưng
    đó KHÔNG phải đảm bảo tuyệt đối — Flash có ghi nhận rơi vào vòng lặp lặp
    token trong literal số cho tới `MAX_TOKENS` rồi trả JSON cụt; nên nhánh lỗi
    parse dưới đây là đường sống, không phải phòng thủ thừa.

    ─── `domain` ────────────────────────────────────────────────────────────

    `None` = miền Tin học, tức **hành vi trước đó nguyên vẹn**. Trước bản này
    tên skill viết CỨNG là `"semantic_program"`, nên `geometry_program_generator.md`
    không có một người gọi nào trong `app/` — chỉ harness đo mới với tới nó bằng
    cách bọc `load_skill` từ ngoài. Hệ quả: đề hình học đi qua sản phẩm được
    **viết chương trình bằng prompt Tin học**, và trượt ở chỗ trông như mô hình
    kém trong khi thật ra ta đưa nhầm đề bài cho nó.
    """
    from app.simulation.semantic_program.contract import generate_json_schema
    from app.simulation.semantic_program.domain_profile import program_skill_for
    from app.simulation.semantic_program.validator import validate_semantic_program

    from app.simulation.semantic_program.grammar_card import grammar_card

    skill = program_skill_for(domain) if domain else "semantic_program"

    base = f'Đề bài:\n"""\n{text}\n"""'
    if contract is not None:
        base = f"{base}\n\n{_facts_for_prompt(contract)}"
        base = f"{base}\n\n{_obligations_for_prompt(contract)}"
    # Hợp đồng IR phải đi kèm, vì Gemini KHÔNG nhận được schema của nó (xem
    # `grammar_card.py`). Thiếu nó, mô hình tự đặt tên trường và 38/40 case
    # trượt thẩm định — đo được ở lượt pilot thứ hai.
    base = f"{base}\n\n{grammar_card()}"

    prompt = base
    loi_cuoi = "không rõ"

    for lan in range(MAX_SEMANTIC_PROGRAM_ATTEMPTS):
        with stage_scope("semantic_program"):
            raw = await call_gemini(
                api_key,
                load_skill(skill),
                prompt,
                generate_json_schema(),
                0.1,
            )

        loi: str | None = None
        try:
            payload = json.loads(raw)
        except (json.JSONDecodeError, TypeError) as e:
            loi = f"JSON không parse được ({e})"
        else:
            if not isinstance(payload, dict):
                loi = (
                    "đầu ra không phải một đối tượng JSON "
                    f"(nhận {type(payload).__name__})"
                )
            else:
                val = validate_semantic_program(payload)
                if val.ok:
                    # ─── XUẤT XỨ CŨNG PHẢI GỬI NGƯỢC ────────────────────────
                    #
                    # Vòng sửa này trước đây chỉ gửi lại lỗi SCHEMA. Cổng
                    # grounding thì chạy SAU, ở `route.py`, nên lời từ chối
                    # của nó **không bao giờ tới được mô hình**: chương trình
                    # được sinh đúng một lần rồi bị giết ở hạ nguồn.
                    #
                    # Đo được ở CONFIRMATION_V2: 6/10 chi tiết grounding là
                    # *"có initial_value nhưng thiếu source_fact_id"* trên các
                    # đỉnh dẫn xuất (`C`, `D`, `B'`, `C'`, `D'`, `S`). Mô hình
                    # khai `model_assumption` cho hai đỉnh đầu rồi quên phần
                    # còn lại — một lỗi nó tự sửa được nếu biết mình đã sai.
                    #
                    # ⚠️ KHÔNG nới cổng. Cùng `check_grounding`, cùng phán
                    # quyết, cùng trần 3 lượt; chỉ thêm ĐƯỜNG PHẢN HỒI. Và
                    # cùng khuôn với lỗi schema: gửi lại LỜI TỪ CHỐI, không
                    # gợi ý cách sửa — gợi ý là ta đang viết chương trình hộ.
                    #
                    # Vì sao không nhồi luật này vào prompt: `test_prompt_size_
                    # guard` chặn ở 4800 byte với đúng lý do ấy — *"luật trong
                    # prompt là GỢI Ý, luật trong validator là RÀNG BUỘC"*.
                    if contract is not None:
                        from app.simulation.semantic_program.grounding_gate import (
                            check_grounding,
                        )
                        g = check_grounding(contract, val.spec)
                        if not g.ok and lan < MAX_SEMANTIC_PROGRAM_ATTEMPTS - 1:
                            loi = ("xuất xứ dữ liệu chưa đủ — "
                                   + "; ".join(g.unresolved[:4]))
                            _emit(observer, "semantic_program_attempt",
                                  n=lan, ok=False, message=loi, gate="grounding")
                            prompt = (
                                f"{base}\n\nLần trước bị từ chối vì: {loi}\n"
                                "Hãy sửa ĐÚNG chỗ đó và giữ nguyên phần còn lại.")
                            continue
                    return val.spec, None
                loi = val.error

        loi_cuoi = loi
        _emit(observer, "semantic_program_attempt", n=lan, ok=False, message=loi)
        # Cùng khuôn với `stage_simulate` — lỗi validator là thứ DUY NHẤT gửi
        # ngược. Không gợi ý cách sửa: gợi ý là ta đang viết chương trình hộ.
        prompt = (
            f"{base}\n\nLần trước bị từ chối vì: {loi}\n"
            "Hãy sửa ĐÚNG chỗ đó và giữ nguyên phần còn lại."
        )

    return None, f"SEMANTIC_PROGRAM_INVALID: {loi_cuoi}"


async def stage_classify(
    text: str, analysis: dict, api_key: str, extra_note: str | None = None
) -> dict:
    # M7.8: cho classify thấy NĂNG LỰC thực tế của generic (từ manifest) để
    # định tuyến theo capability, không theo tên môn học → tránh unsupported oan.
    user = (
        f'Đầu vào gốc:\n"""\n{text}\n"""\n\n'
        f"Kết quả phân tích:\n{json.dumps(analysis, ensure_ascii=False)}\n\n"
        f"{catalog_text()}\n\n"
        f"{manifest_capability_summary()}"
    )
    # M15 Task 6: reclassify note ghép CUỐI — extra_note=None → user y NGUYÊN
    # (hành vi cũ bit-một-bit; sync-lock các test hiện có không đổi).
    if extra_note is not None:
        user = f"{user}\n\n{extra_note}"
    result = await _call_json(
        api_key, "classify", user, _classify_schema(), 0.0, 1,
        "Lần trước không phải JSON hợp lệ. Trả về đúng một đối tượng JSON theo schema.",
    )
    # M14: hợp lệ = trong llm_choices (CATALOG concrete llm-facing HOẶC selector token)
    if result.get("status") == "ok" and result.get("simulation_id") not in set(llm_choices()):
        # LLM chọn id ngoài danh mục → coi như không hỗ trợ, không gán bừa
        return {
            "status": "unsupported",
            "reason": "Bài này chưa khớp chắc chắn với mô phỏng nào trong danh mục.",
        }
    return result


async def stage_simulate(
    text: str,
    analysis: dict,
    simulation_id: str,
    api_key: str,
    required_semantic_roles: set[str] | None = None,
    plan: dict | None = None,
    observer=None,
) -> tuple[dict | None, str | None]:
    """Sinh config + VALIDATE cấu trúc + (với generic) KIỂM SCENE-MODE
    CONSISTENCY và SEMANTIC COMPAT; sai → retry tối đa 2 lần kèm thông báo lỗi.

    Trả (config chuẩn hóa, None) hoặc (None, lỗi cuối cùng).
    """
    spec = CATALOG[simulation_id]
    # M7.13A: scene_mode từ Representation Plan là NGUỒN QUYẾT ĐỊNH chế độ cảnh
    # — truyền vào prompt để LLM không tự ép reveal cho cảnh tĩnh (và ngược lại).
    scene_mode = (plan or {}).get("scene_mode") if simulation_id == "generic.rule_scene" else None
    base = (
        f'Đầu vào gốc:\n"""\n{text}\n"""\n\n'
        f"Kết quả phân tích:\n{json.dumps(analysis, ensure_ascii=False)}\n\n"
        f"simulation_id đã chọn: {simulation_id}\n\n{spec.contract}"
    )
    if scene_mode:
        base += f"\n\n{scene_mode_guidance(scene_mode)}"
    prompt = base
    last_error = "không rõ"
    stage_incomplete: dict | None = None

    for _attempt in range(3):
        with stage_scope("simulate"):
            raw = await call_gemini(api_key, load_skill("simulate"), prompt, spec.config_schema, 0.1)
        try:
            candidate = json.loads(raw)
        except json.JSONDecodeError:
            last_error = "Kết quả không phải JSON hợp lệ."
            _emit(observer, "simulate_attempt", n=_attempt, ok=False, error_code=None, message=last_error)
            prompt = f"{base}\n\nLần trước bị từ chối vì: {last_error}\nHãy sửa lại."
            continue
        config, error = spec.validate(candidate)
        if config is None:
            last_error = error or "không rõ"
            _emit(observer, "simulate_attempt", n=_attempt, ok=False, error_code=ErrorCode.STRUCTURAL_INVALID.value, message=last_error)
            prompt = f"{base}\n\nLần trước bị từ chối vì: {last_error}\nHãy sửa lại."
            continue

        # M7.13A: spec ↔ scene_mode phải nhất quán (tất định, check trước semantic)
        if scene_mode:
            mode_error = check_scene_consistency(scene_mode, config)
            if mode_error:
                last_error = mode_error
                _emit(observer, "simulate_attempt", n=_attempt, ok=False, error_code=ErrorCode.SCENE_MODE_MISMATCH.value, message=last_error)
                prompt = f"{base}\n\nLần trước bị từ chối vì: {last_error}\nHãy sửa lại."
                continue

        # M8-PRE (S2): sơ đồ hệ thống thông tin phải nêu CHIỀU luồng dữ liệu.
        # Cổng TẤT ĐỊNH — đo live cho thấy prompt một mình KHÔNG đủ (LLM dựng đúng
        # node vai trò nhưng bỏ qua `directed` → mất chính giá trị sư phạm cần có).
        if simulation_id == "generic.rule_scene":
            flow_error = check_system_flow_consistency(config)
            if flow_error:
                last_error = flow_error
                _emit(observer, "simulate_attempt", n=_attempt, ok=False, error_code=ErrorCode.SYSTEM_FLOW_INVALID.value, message=last_error)
                prompt = f"{base}\n\nLần trước bị từ chối vì: {last_error}\nHãy sửa lại."
                continue

        # M17 W2B-PATCH §A: đề hỏi một QUY TRÌNH nhiều bước mà spec bỏ bước —
        # đây là lỗi SỬA ĐƯỢC, nên báo đích danh bước còn thiếu rồi cho làm
        # lại, thay vì từ chối ngay một đề vốn hợp lệ. Hết lượt vẫn thiếu thì
        # cổng completeness PHA 2 chặn fail-closed (hai lớp, không lớp nào thừa).
        stage_error = stage_shortfall_message(analysis, simulation_id, config)
        if stage_error:
            last_error = stage_error
            # Giữ lại spec HỢP LỆ VỀ CẤU TRÚC nhưng thiếu bước: hết lượt thì
            # trả nó về để cổng completeness PHA 2 từ chối bằng THÔNG ĐIỆP HỌC
            # SINH + bằng chứng máy-đọc — thay vì ném RuntimeError kỹ thuật.
            stage_incomplete = config
            _emit(observer, "simulate_attempt", n=_attempt, ok=False,
                  error_code=ErrorCode.SEMANTIC_INCOMPLETE.value, message=last_error)
            prompt = f"{base}\n\nLần trước bị từ chối vì: {last_error}\nHãy sửa lại."
            continue

        # M7.11: kiểm SEMANTIC COMPAT cho generic — spec phải cover vai trò đề cần
        if required_semantic_roles and simulation_id == "generic.rule_scene":
            compat = check_semantic_compatibility(required_semantic_roles, config)
            if not compat["ok"]:
                if compat["kind"] == "capability_gap":
                    # Vai trò không primitive nào cover → không ép sai, báo gap
                    return None, f"__GAP__:{','.join(compat['missing'])}"
                last_error = (
                    f"Spec chưa thể hiện các vai trò ngữ nghĩa đề cần: "
                    f"{', '.join(compat['missing'])}. Hãy dùng primitive phù hợp với các vai trò này."
                )
                _emit(observer, "simulate_attempt", n=_attempt, ok=False, error_code=ErrorCode.SEMANTIC_INCOMPAT.value, message=last_error)
                prompt = f"{base}\n\nLần trước bị từ chối vì: {last_error}\nHãy sửa lại."
                continue

        # [CEGIS Gate] Thực thi dry-run kiểm chứng bất biến và visual binding
        if simulation_id == "generic.rule_scene":
            exec_report = execute_simulation(config)
            if not exec_report.ok:
                last_error = exec_report.error or "Vi phạm bất biến thực thi mô phỏng."
                _emit(observer, "simulate_attempt", n=_attempt, ok=False, error_code=exec_report.error_code, message=last_error)
                prompt = f"{base}\n\nLần trước bị từ chối do vi phạm kiểm chứng thực thi ({exec_report.error_code}):\n{last_error}\nHãy sửa lại đặc tả cho đúng."
                continue

        _emit(observer, "simulate_attempt", n=_attempt, ok=True, error_code=None, message="")
        return config, None

    if stage_incomplete is not None:
        # Cạn lượt vì THIẾU BƯỚC (không phải spec hỏng): đây là ca "từ chối
        # trung thực", và PHA 2 là nơi DUY NHẤT soạn thông điệp đó.
        return stage_incomplete, None
    return None, last_error


async def stage_simulate_family(
    text: str, analysis: dict, selector, api_key: str, observer=None
) -> tuple[dict | None, str | None]:
    """M14 §E — sinh FamilySpec (selector.config_schema/contract) + validate
    fail-closed + VARIANT-CONSISTENCY (E4 tầng 2, so analysis × variant). Retry
    tối đa 3 lần kèm message lỗi. Trả (family_config, None) hoặc (None, lỗi cuối)."""
    base = (
        f'Đầu vào gốc:\n"""\n{text}\n"""\n\n'
        f"Kết quả phân tích:\n{json.dumps(analysis, ensure_ascii=False)}\n\n"
        f"simulation_id đã chọn: {selector.selector_token}\n\n{selector.contract}"
    )
    prompt = base
    last_error = "không rõ"
    for _attempt in range(3):
        with stage_scope("simulate_family"):
            raw = await call_gemini(api_key, load_skill("simulate"), prompt, selector.config_schema, 0.1)
        try:
            candidate = json.loads(raw)
        except json.JSONDecodeError:
            last_error = "Kết quả không phải JSON hợp lệ."
            _emit(observer, "simulate_attempt", n=_attempt, ok=False, error_code=None, message=last_error)
            prompt = f"{base}\n\nLần trước bị từ chối vì: {last_error}\nHãy sửa lại."
            continue
        config, error = selector.validate_family_spec(candidate)
        if config is None:
            last_error = error or "không rõ"
            _emit(observer, "simulate_attempt", n=_attempt, ok=False, error_code=ErrorCode.FAMILY_SPEC_INVALID.value, message=last_error)
            prompt = f"{base}\n\nLần trước bị từ chối vì: {last_error}\nHãy sửa lại."
            continue
        # E4 tầng 2: variant có khớp cơ chế đề yêu cầu không (không chỉ nhìn FamilySpec)
        mism = check_variant_consistency(analysis, selector, config["variant"])
        if mism is not None:
            last_error = mism[1]
            _emit(observer, "simulate_attempt", n=_attempt, ok=False, error_code=mism[0].value, message=last_error)
            prompt = f"{base}\n\nLần trước bị từ chối vì: {last_error}\nHãy sửa lại."
            continue
        _emit(observer, "simulate_attempt", n=_attempt, ok=True, error_code=None, message="")
        return config, None
    return None, last_error


# ── Pattern reuse (M7.13B) — thay stage_simulate khi có mẫu khớp ──

def _adapt_schema(unresolved: dict) -> dict:
    """Schema structured-output cho stage adapt — SINH TỪ parameter_schema
    của pattern, chỉ chứa đúng các slot chưa resolve."""
    props: dict = {}
    for name, meta in unresolved.items():
        if meta["kind"] == "string":
            props[name] = {"type": "STRING"}
        elif meta["kind"] == "bit":
            props[name] = {"type": "NUMBER"}
        else:  # number_array
            props[name] = {"type": "ARRAY", "items": {"type": "NUMBER"}}
    return {"type": "OBJECT", "properties": props, "required": list(props)}


async def stage_adapt(
    text: str, analysis: dict, pattern_name: str, unresolved: dict, api_key: str
) -> dict:
    """MỘT call LLM nhỏ điền slot chưa resolve — prompt chỉ gồm mô tả slot
    (kèm ví dụ gốc), KHÔNG kèm contract DSL đồ sộ như simulate."""
    slot_lines = "\n".join(
        f'- {name} ({meta["kind"]}'
        + (f', {meta["length"]} số' if meta["kind"] == "number_array" else "")
        + f"): ví dụ từ bài gốc của mẫu: {json.dumps(meta['example'], ensure_ascii=False)}"
        for name, meta in unresolved.items()
    )
    user = (
        f'Đề bài hiện tại:\n"""\n{text}\n"""\n\n'
        f"Kết quả phân tích:\n{json.dumps(analysis, ensure_ascii=False)}\n\n"
        f"Mẫu mô phỏng: {pattern_name}\n"
        f"Các tham số cần điền cho ĐỀ BÀI HIỆN TẠI:\n{slot_lines}"
    )
    return await _call_json(
        api_key, "adapt", user, _adapt_schema(unresolved), 0.1, 1,
        "Lần trước không phải JSON hợp lệ. Trả về đúng một đối tượng JSON theo schema.",
    )


async def try_pattern_reuse(
    text: str, analysis: dict, plan: dict, roles: set[str], api_key: str, pattern_store
) -> tuple[dict | None, dict]:
    """Tầng 2: tìm pattern verified/validated khớp EXACT (scene_mode + roles),
    adapt tham số (deterministic trước, 1 call LLM nhỏ cho phần còn lại) rồi
    chạy ĐỦ 4 cổng. Bất kỳ bước nào fail → (None, meta) để fallback compose —
    không crash, không sửa pattern gốc."""
    row = pattern_store.find(plan["scene_mode"], roles)
    if row is None:
        return None, {"attempted": False}
    meta = {"attempted": True, "pattern_key": row.pattern_key, "adapt_used": False}
    schema = json.loads(row.parameter_schema_json)
    template = json.loads(row.template_json)
    params, unresolved = deterministic_fill(schema, analysis)
    if unresolved:
        meta["adapt_used"] = True
        try:
            llm_params = await stage_adapt(text, analysis, row.name, unresolved, api_key)
        except Exception:
            return None, meta  # adapt hỏng → fallback compose, không poison store
        params.update({k: llm_params[k] for k in unresolved if k in llm_params})
    if validate_params(schema, params) is not None:
        return None, meta
    config, err = run_gates(plan["scene_mode"], roles, instantiate(template, params))
    if config is None or err:
        return None, meta
    pattern_store.bump_usage(row.pattern_key)
    return config, meta


# ── M15 Task 6: route-consistency recovery (bounded, TRƯỚC route-dependent gate) ──

def _refusal_category(analysis: dict) -> str | None:
    """W2C-C1 §L3 — bản chất lời từ chối của classify, suy TẤT ĐỊNH.

    `classify` từ chối trước mọi cổng nên envelope không mang `failure_category`,
    và FE mất tiêu đề đúng. Ở đây dùng LẠI cổng đủ-dữ-kiện dùng chung: nếu cơ
    chế mà CHÍNH analyze khai thuộc một family CÓ target trong danh mục, mà mọi
    target đó đều thiếu dữ kiện bắt buộc, thì đây là **thiếu dữ kiện** chứ không
    phải "ngoài danh mục".

    Không keyword-match đề bài, không thêm stage, không sửa classify. Không suy
    được ⇒ trả None (để trống còn hơn gắn nhãn sai)."""
    from app.simulation.catalog import CATALOG
    from app.simulation.descriptor import ReachabilityLevel

    canonical = canonical_mechanism(analysis.get("prescribed_procedure"))
    if not canonical:
        return None
    family = mechanism_family(canonical)
    targets = [
        sid for sid, spec in CATALOG.items()
        if ReachabilityLevel.AI_REACHABLE_PUBLIC in spec.reachability
        and any(m.family_id.value == family for m in spec.family_memberships)
    ]
    if not targets:
        return None
    verdict = check_input_sufficiency_for_targets(analysis, targets)
    return "insufficient_specification" if verdict is not None else None


def _family_mismatch(analysis: dict, sim_id: str) -> tuple[ErrorCode, str] | None:
    """CHỈ nhánh 3 (family mismatch) — cho cả selector token lẫn direct entry.
    Ownership (nhánh 2) là route-dependent gate, chạy SAU trên FINAL route
    (check_mechanism_consistency_for_target). MỘT nguồn message (_MISMATCH_MSG)."""
    pres = canonical_mechanism(analysis.get("prescribed_procedure"))
    if pres is None:
        return None
    sel = selector_for_token(sim_id)
    fams = (
        {sel.family_id.value}
        if sel is not None
        else {m.family_id.value for m in CATALOG[sim_id].family_memberships}
    )
    if mechanism_family(pres) not in fams:
        return (ErrorCode.ROUTE_MECHANISM_FAMILY_MISMATCH, _MISMATCH_MSG)
    return None


async def classify_with_one_route_recovery(
    text: str, analysis: dict, classification: dict, api_key: str, observer=None
) -> tuple[dict, tuple[ErrorCode, str] | None]:
    """Khóa 3 — bounded, KHÔNG recursion, KHÔNG pipeline thứ hai, KHÔNG gọi
    analyze/simulate, KHÔNG chạy route-dependent gate nào. Trả
    (classification_final, mismatch_gap|None).

    - status ≠ ok → passthrough.
    - không mismatch (nhánh 3) → passthrough.
    - mismatch → phát event + ĐÚNG 1 reclassify (extra_note); reclassify ra
      unsupported → passthrough (từ chối trung thực của classify); reclassify VẪN
      lệch → (second, verdict) để caller fail-closed (KHÔNG lượt 3)."""
    if classification.get("status") != "ok":
        return classification, None
    verdict = _family_mismatch(analysis, classification["simulation_id"])
    if verdict is None:
        return classification, None
    _emit(observer, "gate_checked", gate="route_mechanism", fired=True,
          reason_code=verdict[0].value)
    _emit(observer, "reclassify_attempted",
          from_simulation_id=classification["simulation_id"],
          canonical_prescribed=canonical_mechanism(analysis.get("prescribed_procedure")))
    second = await stage_classify(
        text, analysis, api_key,
        extra_note=(
            "Phân tích xác định cơ chế đề yêu cầu thuộc họ năng lực khác với "
            "simulation_id đã chọn. Chọn lại đúng mô phỏng biểu diễn cơ chế đó, "
            "hoặc trả unsupported."
        ),
    )
    _emit(observer, "reclassify_result", status=second.get("status"),
          simulation_id=second.get("simulation_id"))
    if second.get("status") != "ok":
        return second, None  # từ chối trung thực của classify
    if _family_mismatch(analysis, second["simulation_id"]) is not None:
        return second, verdict  # VẪN lệch → caller fail-closed, KHÔNG lượt 3
    return second, None


# ── Orchestrator ──────────────────────────────────────────────

async def _semantic_shadow(
    text: str, analysis: dict, plan: dict, api_key: str, observer
) -> "SemanticRouteOutcome | None":
    """Quyết định route sinh CÓ ĐƯỢC THỬ hay không — độc lập với classifier.

    Hai cổng, và chỉ hai:

    - **Phạm vi** — đề ngoài môn Tin học thì dù máy dựng được cảnh cũng không
      dựng. `GATE_SCOPE_UNDECLARED` KHÔNG chặn ở đây: nó là lỗi hợp đồng prompt
      chứ không phải phán quyết về đề, và để nó chặn thì route mất lượt vì một
      trường bị thiếu.
    - **Execution authority** — kết quả phải có một authority TẤT ĐỊNH sở hữu.
      R0 không bị nới một milimet; khác biệt duy nhất là hệ nay có interpreter.

    Cố ý KHÔNG hỏi classifier chọn target nào. Hỏi thì claim A tụt xuống thành
    "hệ sinh được mô phỏng cho những bài mà classifier không nhận", tức một
    claim về classifier chứ không phải về route sinh.

    ─── MIỀN QUYẾT ĐỊNH TẤT ĐỊNH, TRƯỚC MỌI LƯỢT LLM ────────────────────────

    `detect_domain` chạy trên VĂN BẢN ĐỀ, ở server, không tốn call. Nó phải nằm
    trước cả cổng phạm vi vì chính cổng ấy cần biết câu hỏi đang hỏi về môn nào.
    """
    from app.simulation.semantic_program.domain_profile import (
        DOMAIN_HINH_HOC,
        co_duong_thuc_thi,
        detect_domain,
    )

    domain = detect_domain(text)
    _emit(observer, "semantic_domain", domain=domain)

    scope = check_scope_and_simulatability(analysis)
    if scope is not None and scope[0] is not ErrorCode.GATE_SCOPE_UNDECLARED:
        # ─── VÌ SAO HÌNH HỌC KHÔNG BỊ CỔNG NÀY PHỦ QUYẾT ────────────────────
        #
        # Đây KHÔNG phải nới cổng — đọc kỹ enum thì rõ. `analyze.md` chỉ cho
        # `domain_scope` bốn giá trị: THPT_INFORMATICS · ADJACENT_CONTEXT ·
        # OUT_OF_SCOPE ("môn khác thật sự: hoá học, vật lí, sinh học") ·
        # AMBIGUOUS. **Không có giá trị nào cho hình học không gian.** Nên với
        # một đề hình học, mô hình buộc phải chọn một nhãn sai, và phán quyết ấy
        # KHÔNG MANG THÔNG TIN. Thay một phán quyết rỗng nghĩa bằng một phép
        # kiểm tất định phía server là SIẾT, không phải nới.
        #
        # Phạm vi ngoại lệ hẹp đúng bằng chỗ cần: chỉ khi bộ dò tất định nói
        # `hinh_hoc`. Đề hoá học không có từ khoá hình học ⇒ `tin_hoc` ⇒ cổng
        # nguyên vẹn, và lời từ chối trung thực vẫn tới học sinh như cũ.
        #
        # Nới ở đây cũng KHÔNG mở đường cho một cảnh chưa ai kiểm: grounding,
        # C₁a, C₁b, C₂ đều còn nguyên phía sau, và `servable` mới là thứ quyết
        # định có phát hay không.
        # ─── CỔNG NÀY CÓ HAI VẾ, VÀ CẢ HAI ĐỀU RỖNG NGHĨA VỚI HÌNH HỌC ──────
        #
        # Bản trước chỉ miễn `GATE_OUT_OF_SCOPE` (vế `domain_scope`). Đo được
        # ở canary V2 2026-08-29: bài A10 (góc đường–mặt) chết ở vế THỨ HAI,
        # `GATE_NOT_SIMULATION_SUITABLE`, ngay trước tầng sinh.
        #
        # Cùng một bệnh: `REQUIRES_SIMULATION` = {INTERACTIVE_MODEL,
        # INTERACTIVE_ARTIFACT, MEANINGFUL_TRACE} — không nhãn nào cho một bài
        # hình học tĩnh, nên mô hình buộc phải chọn nhãn sai và phán quyết ấy
        # KHÔNG MANG THÔNG TIN. Chỉ lộ ở A10 chứ không ở A09 vì cùng dạng đề
        # mô hình khai hai nhãn khác nhau — tức nó ngẫu nhiên, đúng nghĩa đen.
        #
        # ⚠️ Miễn theo LUẬT DƯƠNG, không phải *"là hình học ⇒ luôn mô phỏng
        # được"*. Luật âm ấy sẽ thả đề ngoài năng lực (mặt cầu, nhị diện có
        # miền, Oxyz) đi sâu vào tầng sinh rồi hỏng ở một cổng khó đọc hơn.
        # `co_duong_thuc_thi` đòi đề ánh xạ được tới một nghĩa vụ CÓ CHECKER —
        # bằng chứng rằng hệ có đường biểu diễn và đường thực thi cho nó.
        #
        # Phía sau vẫn nguyên: grounding, C₁a, C₁b, C₂, capability boundary.
        # `servable` mới là thứ quyết định có phát hay không.
        mien = (domain == DOMAIN_HINH_HOC
                and scope[0] in (ErrorCode.GATE_OUT_OF_SCOPE,
                                 ErrorCode.GATE_NOT_SIMULATION_SUITABLE)
                and co_duong_thuc_thi(text, domain))
        if not mien:
            _emit(observer, "semantic_route", stage_reached="scope",
                  executable=False, servable=False,
                  error_code=scope[0].value, reason=scope[1])
            return None
        _emit(observer, "gate_checked", gate="scope", fired=False,
              reason_code=None)

    auth = check_execution_authority(analysis, plan, has_interpreter=True,
                                     domain=domain)
    _emit(observer, "gate_checked", gate="execution_authority",
          fired=bool(auth),
          reason_code=ErrorCode.GATE_RESULT_OWNERSHIP.value if auth else None)
    if auth is not None:
        _emit(observer, "semantic_route", stage_reached="execution_authority",
              executable=False, servable=False,
              error_code=ErrorCode.GATE_RESULT_OWNERSHIP.value, reason=auth)
        return None

    return await _semantic_route_attempt(text, analysis, api_key, observer, domain)


def _dung_scene3d(spec) -> dict | None:
    """`SemanticProgramSpec` → cảnh 3D, hoặc `None` nếu bài không phải hình học.

    ─── VÌ SAO NGƯỜI GHÉP NẰM Ở ĐÂY, KHÔNG Ở `route.py` ────────────────────

    Hướng phụ thuộc một chiều: engine (kernel · validator · interpreter · các
    cổng) KHÔNG được biết tới tầng trình bày, vì khi ấy một thay đổi thẩm mỹ sẽ
    đụng vào thứ đang gác cửa. `test_scene3d.py` giữ luật đó bằng cách cấm **mọi**
    module dưới `app/simulation` import `scene3d`.

    `pipeline` là người GỌI route, không phải một tầng của nó — nên ghép ở đây
    thoả cả hai: cảnh 3D vẫn tới được envelope, mà ranh giới không phải nới một
    milimét nào. `SemanticRouteOutcome.scene3d` chỉ là một Ô TRỐNG kiểu `dict`.

    ─── VÌ SAO CHẠY LẠI INTERPRETER ───────────────────────────────────────

    `verify_and_compile` trả `final_memory` nhưng không trả `trace`, mà timeline
    cần trace đầy đủ. Interpreter tất định và không đọc trạng thái ngoài, nên
    chạy lại cho **đúng kết quả cũ**; `compile_semantic_program_to_envelope`
    trong route cũng đã chạy lại vì cùng lý do, và ghi rõ tiền lệ ấy.

    Bài Tin học trả `None` — cảnh rỗng cũng là `None`: một khung 3D trống không
    nói được gì, và bày nó ra là mời người học đi tìm thứ không có.
    """
    from app.simulation.semantic_program.interpreter import (
        SemanticProgramInterpreter,
    )
    from app.simulation.semantic_program.scene3d import build_scene3d
    from app.simulation.semantic_program.simulation_state import (
        build_simulation_state,
    )

    try:
        ket = SemanticProgramInterpreter().execute(spec)
        canh = build_scene3d(build_simulation_state(spec, ket))
    except Exception:  # noqa: BLE001 — trình bày hỏng KHÔNG được giết phép đo
        # Một lỗi ở tầng cảnh không được làm hỏng một chương trình đã qua mọi
        # cổng. Mất hình còn hơn mất cả kết quả đã kiểm chứng.
        return None
    return canh if canh["objects"] else None


def _la_hinh_hoc(text: str) -> bool:
    """Đề này có thuộc miền hình học không — TẤT ĐỊNH, không hỏi LLM."""
    from app.simulation.semantic_program.domain_profile import (
        DOMAIN_HINH_HOC,
        detect_domain,
    )

    return detect_domain(text) == DOMAIN_HINH_HOC


def _that_bai_hinh_hoc(outcome, analysis: dict, plan: dict, observer) -> dict:
    """Envelope cho đề HÌNH HỌC mà route sinh không phục vụ được.

    Nói đúng thứ đã xảy ra: *hệ hiểu đây là hình học, đã thử dựng, và chương
    trình chưa qua kiểm chứng* — thay vì đổ cho đề bài là "môn khác".

    `outcome` có thể `None`: route dừng trước khi dựng nổi IR. Khi ấy vẫn là
    thất bại của việc SINH, không phải của phạm vi.
    """
    category = "geometry_generation_failed"
    ly_do = getattr(outcome, "reason", None) if outcome is not None else None
    _emit(observer, "envelope", status="unsupported", simulation_id=None,
          failure_category=category)
    return {
        "status": "unsupported",
        # `reason` KỸ THUẬT giữ nguyên — nó nuôi harness và diagnostics. Học
        # sinh đọc `learner_reason`, gắn ở biên API (`learner_messages`).
        "reason": ly_do or "Chưa dựng được chương trình hình học cho đề này.",
        "failure_category": category,
        "error_code": getattr(outcome, "error_code", None) if outcome else None,
        "stage_reached": getattr(outcome, "stage_reached", None) if outcome else None,
        "representation_plan": plan,
        "analysis": analysis,
    }


def _envelope_tu_route_sinh(outcome, analysis: dict, plan: dict, observer) -> dict:
    """Envelope phát từ route sinh — MỘT chỗ dựng, hai chỗ gọi.

    Hai lối vào (nhánh phát bình thường, và nhánh classifier lệch) phải dựng ra
    envelope GIỐNG HỆT nhau. Chép thành hai bản là cách chắc chắn để `source`
    hoặc `representation_plan` thiếu ở đúng một lối vào — thứ chỉ lộ ra khi đọc
    artifact nhiều tuần sau.
    """
    env = dict(outcome.envelope or {})
    env["analysis"] = analysis
    env["representation_plan"] = plan
    env["source"] = "semantic_program"
    # Cảnh 3D đi kèm envelope, KHÔNG thay nó: đường 2D cũ nguyên vẹn, và bài
    # Tin học không có khoá này. Gắn ở đây vì đây là MỘT chỗ dựng envelope duy
    # nhất — hai lối vào phải ra cùng một hình dạng.
    if outcome.scene3d:
        env["scene3d"] = outcome.scene3d
    _emit(observer, "envelope", status="ok",
          simulation_id=env.get("simulation_id"), source="semantic_program")
    return env


async def _semantic_route_attempt(
    text: str, analysis: dict, api_key: str, observer, domain: str | None = None
) -> "SemanticRouteOutcome | None":
    """Hai lượt LLM + toàn bộ cổng tất định. Trả `None` khi chưa dựng nổi IR.

    Mọi thất bại đều được EMIT chứ không nuốt: benchmark cần biết bài hỏng ở
    khâu nào, và "hỏng ở khâu nào" mới là dữ liệu, còn "hỏng" thì không.

    `domain` đi xuống **cả hai** lượt LLM. Đổi một lượt mà quên lượt kia là đúng
    lỗi Phase 5 đo được: skill viết chương trình đã sang hình học, skill đọc đề
    thì không, nên mô hình khai nghĩa vụ Tin học cho bài hình học ở 3/6 ca.
    """
    from app.simulation.semantic_program.route import verify_and_compile

    contract, cerr = await stage_semantic_analyze(text, api_key, domain)
    if contract is None:
        _emit(observer, "semantic_route", stage_reached="semantic_analyze",
              executable=False, servable=False,
              error_code=ErrorCode.SEMANTIC_PROGRAM_INVALID.value, reason=cerr)
        return None

    # Phát KÈM witness của từng nghĩa vụ. Ground truth độc lập không được phép
    # đoán tên biến mà LLM tự đặt — custodian chỉ khai nghĩa vụ và giá trị
    # đúng, còn ánh xạ nghĩa-vụ → tên-biến thì đọc từ contract này.
    _emit(observer, "semantic_contract",
          so_fact=len(contract.input_facts),
          so_nghia_vu=len(contract.obligations),
          kinds=sorted({ob.kind for ob in contract.obligations}),
          obligations=[
              {"kind": ob.kind, "container": ob.container, "witness": ob.witness}
              for ob in contract.obligations
          ])

    spec, serr = await stage_semantic_program(
        text, analysis, api_key, contract, observer=observer, domain=domain
    )
    if spec is None:
        _emit(observer, "semantic_route", stage_reached="semantic_program",
              executable=False, servable=False,
              error_code=ErrorCode.SEMANTIC_PROGRAM_INVALID.value, reason=serr)
        return None

    outcome = verify_and_compile(contract, spec)
    # Cảnh 3D CHỈ dựng khi chương trình đã chạy trọn. Chương trình không qua
    # thẩm định thì không có hình — đó là toàn bộ luận điểm của đề tài, và nếu
    # nới ở đây thì renderer sẽ bày ra thứ chưa ai kiểm.
    if outcome.executable:
        outcome = outcome.model_copy(update={"scene3d": _dung_scene3d(spec)})
    _emit(observer, "semantic_route",
          stage_reached=outcome.stage_reached,
          executable=outcome.executable,
          servable=outcome.servable,
          error_code=outcome.error_code,
          failure_category=outcome.failure_category,
          reason=outcome.reason,
          weak_kinds=outcome.weak_kinds,
          details=outcome.details,
          total_steps=outcome.total_steps,
          frame_count=outcome.frame_count,
          # Trạng thái cuối là thứ DUY NHẤT đem so được với ground truth độc
          # lập. Thiếu nó ở đây thì benchmark chấm được đúng 0 case — và chấm
          # sai theo hướng im lặng, sau khi đã tiêu hết quota.
          final_memory=outcome.final_memory,
          # §7 — ba con số của SCALE NORMALIZATION. Phát cùng chỗ với mọi quan
          # trắc khác: một lượt đo không giữ được chúng thì tỉ lệ literal có
          # căn cứ phải suy ngược từ `details`, và suy ngược là chỗ hai định
          # nghĩa "biện minh" bắt đầu trôi khỏi nhau.
          justified_literals=outcome.justified_literals,
          unjustified_literals=outcome.unjustified_literals,
          constraints_checked=outcome.constraints_checked,
          constraints_verified=outcome.constraints_verified)
    return outcome


async def run_pipeline(
    text: str,
    api_key: str,
    pattern_store=None,
    observer=None,
    semantic_route: str = "off",
) -> dict:
    """Chạy trọn pipeline; trả ValidatedSimulationEnvelope hoặc unsupported.

    Ném RuntimeError khi stage simulate thất bại sau retry (API trả 422).

    M7.13B: `pattern_store` (inject, optional) bật pattern reuse — CHỈ sau
    classify và CHỈ cho generic.rule_scene (bảo vệ specialized selection).
    None → hành vi compose cũ nguyên vẹn.

    M14 §F2: `observer` (inject, optional) THỤ ĐỘNG — thu event có cấu trúc; None
    → hành vi production KHÔNG đổi một bit (evaluation dùng CHUNG orchestration
    này, bất biến #22).
    """
    analysis = await stage_analyze(text, api_key)
    _emit(observer, "analyze_done",
          result_ownership=analysis.get("result_ownership") if isinstance(analysis, dict) else None,
          prescribed_procedure=analysis.get("prescribed_procedure") if isinstance(analysis, dict) else None,
          canonical_prescribed=canonical_mechanism(analysis.get("prescribed_procedure")) if isinstance(analysis, dict) else None)

    # M7.11: Representation Plan TẤT ĐỊNH (analysis → semantic requirements → plan).
    plan = build_representation_plan(analysis)
    _emit(observer, "plan_built", unsupported_capabilities=list(plan.get("unsupported_capabilities", [])))

    # ─── ROUTE SINH NGỮ NGHĨA — chạy TRƯỚC classify, có chủ đích ───
    # Đặt ở đây thì tính độc lập với classifier là CẤU TRÚC, không phải vị trí:
    # không có nhánh nào của classify — kể cả `mismatch_gap` return sớm — chen
    # được vào trước nó.
    #
    # Bản trước đặt khối này SAU `chosen = …`, tưởng là đủ. Lượt chạy pilot đầu
    # tiên cho thấy không: 3/40 case bị `classify_with_one_route_recovery` trả
    # `mismatch_gap` và `run_pipeline` return ngay tại đó, nên route sinh không
    # bao giờ được thử. Claim A khi ấy vẫn phụ thuộc một phần vào classifier
    # legacy — đúng khiếm khuyết đã sửa một lần, sống sót ở nhánh khác.
    #
    # Điều kiện để THỬ là scope + execution authority. Điều kiện để PHÁT thì
    # khác và chặt hơn — nó cần `chosen`, nên nằm ở dưới.
    semantic_outcome = None
    if semantic_route != "off":
        semantic_outcome = await _semantic_shadow(
            text, analysis, plan, api_key, observer
        )

    classification = await stage_classify(text, analysis, api_key)  # lần 1
    _emit(observer, "classify_done",
          status=classification.get("status"), simulation_id=classification.get("simulation_id"))

    # M15 Task 6 (khóa 3, Global Constraint 15): route/mechanism-family consistency
    # + ĐÚNG 1 reclassify TRƯỚC mọi route-dependent gate. Vẫn lệch sau 1 lượt →
    # capability_gap fail-closed (KHÔNG simulate target mâu thuẫn, KHÔNG lượt 3).
    classification, mismatch_gap = await classify_with_one_route_recovery(
        text, analysis, classification, api_key, observer
    )
    if mismatch_gap is not None:
        # Route sinh ĐÃ phục vụ được thì phán quyết lệch của classifier legacy
        # KHÔNG được phủ quyết nó. Cổng mismatch bảo vệ đường module: nó chặn
        # việc simulate một target chuyên biệt mâu thuẫn với cơ chế. Chương
        # trình ngữ nghĩa không đi qua target nào, nên nó không nằm trong tầm
        # bảo vệ ấy — để nguyên `return` ở đây là bắt route sinh chịu hậu quả
        # của một cuộc bầu chọn nó không tham gia.
        #
        # Cùng khiếm khuyết đã sửa cho lượt THỬ (xem chú thích ở nhánh phát bên
        # dưới): lượt thử đã được đưa ra ngoài phán quyết classifier, còn lượt
        # PHÁT thì vẫn nằm sau một `return` của classifier. Đo được trên đề
        # "đảo dãy bằng ngăn xếp": `stage_reached=served, servable=true`, 5
        # khung — rồi envelope trả `unsupported`.
        if (
            semantic_route == "serve"
            and semantic_outcome is not None
            and semantic_outcome.servable
        ):
            return _envelope_tu_route_sinh(semantic_outcome, analysis, plan, observer)
        _emit(observer, "envelope", status="unsupported", simulation_id=None,
              failure_category="capability_gap")
        return {
            "status": "unsupported",
            "reason": mismatch_gap[1],
            "failure_category": "capability_gap",
            "error_code": mismatch_gap[0].value,
            "representation_plan": plan,
            "analysis": analysis,
        }

    # ─── FINAL ROUTE — mọi route-dependent gate chạy DƯỚI dòng này ───
    # M7.11 + M7.14C + M13 Gate B: vai trò không primitive nào cover HOẶC kết
    # quả đòi cơ chế thuật toán không engine nào sở hữu → capability_gap, KHÔNG
    # ép kiến thức vào primitive sai / để AI tự giải rồi dựng cảnh minh hoạ đáp
    # án. Nhưng gate chỉ chặn ĐƯỜNG GENERIC — bài được classify về mô-đun
    # CHUYÊN BIỆT có engine riêng (không dùng DSL) thì đi tiếp bình thường (bug
    # live: sum_if từng bị vạ lây vì analyze gắn numeric_threshold cho điều
    # kiện lọc "lớn hơn 4"). SERVER ra phán quyết cuối, tất định — không đọc
    # text đề (không keyword-patch).
    chosen = classification.get("simulation_id") if classification.get("status") == "ok" else None

    # ─── ROUTE SINH NGỮ NGHĨA — ĐỘC LẬP với phán quyết của classifier ───
    # Đặt NGOÀI nhánh generic có chủ đích. Nếu chỉ chạy khi classifier legacy
    # trả `None`/`generic.rule_scene` thì một held-out case bị classifier chọn
    # nhầm một specialized target sẽ khiến route sinh KHÔNG BAO GIỜ được thử —
    # và claim A ("hệ sinh được mô phỏng cho lớp bài này") hoá ra vẫn phụ thuộc
    # vào catalog classifier, tức đo nhầm thứ.
    #
    # Điều kiện để THỬ là scope + execution authority, không phải target nào
    # được chọn. Điều kiện để PHÁT thì khác và chặt hơn (xem dưới).
    # PHÁT thì vẫn nhường module chuyên biệt: ranh giới phạm vi của đề tài là
    # KHÔNG thay thế 24 module đang có. Route sinh chỉ phục vụ chỗ trống.
    if (
        semantic_route == "serve"
        and semantic_outcome is not None
        and semantic_outcome.servable
        and (chosen is None or chosen == "generic.rule_scene")
    ):
        return _envelope_tu_route_sinh(semantic_outcome, analysis, plan, observer)
    # SHADOW: bằng chứng đã thu qua observer, KHÔNG đổi thứ trả về. Người học
    # vẫn nhận đúng hành vi cũ cho tới khi cổng phát được mở (spec §10.2).

    if chosen is None or chosen == "generic.rule_scene":
        # M20 W3 — PHẠM VI phán TRƯỚC năng lực. Đề ngoài môn Tin học thì dù engine
        # dựng được cảnh cũng không dựng; đề thuộc môn nhưng không có cơ chế để mô
        # phỏng thì dựng cảnh chỉ là trang trí. Trước wave này, thứ duy nhất chặn
        # một đề hoá học là việc LLM tự từ chối — tức phán quyết phạm vi do LLM sở
        # hữu, vi phạm R0. Nay LLM KHAI, server PHÁN. Chi tiết + lý do
        # `AMBIGUOUS` KHÔNG bị từ chối: `simulation/scope_gate.py`.
        scope_gate = check_scope_and_simulatability(analysis)
        _emit(observer, "gate_checked", gate="scope", fired=bool(scope_gate),
              reason_code=scope_gate[0].value if scope_gate else None)

        def _scope_refusal(verdict):
            category = SCOPE_FAILURE_CATEGORY[verdict[0]]
            _emit(observer, "envelope", status="unsupported", simulation_id=None,
                  failure_category=category)
            return {
                "status": "unsupported",
                "reason": verdict[1],
                "failure_category": category,
                "error_code": verdict[0].value,
                "representation_plan": plan,
                "analysis": analysis,
            }

        # `SCOPE_UNDECLARED` KHÔNG phải phán quyết về đề — nó là lỗi hợp đồng
        # prompt. Để nó chặn ngay sẽ nuốt mất lời từ chối THẬT phía dưới: đề đòi
        # `numeric_threshold`/`geometric_locus` đáng được nghe "hệ chưa có cơ chế
        # này", chứ không phải "không rõ đề thuộc môn gì". Nên nó lùi xuống cuối,
        # chạy khi và chỉ khi không cổng nào khác có gì để nói.
        deferred_scope = None
        if scope_gate is not None:
            if scope_gate[0] is ErrorCode.GATE_SCOPE_UNDECLARED:
                deferred_scope = scope_gate
            elif (scope_gate[0] is ErrorCode.GATE_OUT_OF_SCOPE
                  and _la_hinh_hoc(text)):
                # ─── LỜI TỪ CHỐI PHẢI NÓI THẬT ──────────────────────────────
                #
                # Đo được ở lượt smoke 2026-08-25: hệ nhận ra đề là hình học,
                # chạy route sinh 120 GIÂY, chương trình trượt ở cổng phủ — rồi
                # học sinh nhận *"Bài này thuộc môn khác, không nằm trong chương
                # trình Tin học THPT"*. Câu ấy SAI, và sai theo hướng tệ nhất:
                # nó đổ cho ĐỀ BÀI cái lỗi thuộc về HỆ.
                #
                # Cùng một luật với ngoại lệ ở `_semantic_shadow`, và cùng một
                # bộ dò tất định: enum `domain_scope` của `analyze.md` không có
                # giá trị nào cho hình học không gian, nên phán quyết của mô hình
                # ở trường ấy không mang thông tin. Đề hoá học vẫn `tin_hoc` ⇒
                # vẫn nhận đúng lời từ chối cũ.
                return _that_bai_hinh_hoc(semantic_outcome, analysis, plan,
                                          observer)
            else:
                return _scope_refusal(scope_gate)

        gate_reason = check_computation_ownership(analysis, plan)
        _emit(observer, "gate_checked", gate="computation", fired=bool(gate_reason),
              reason_code=ErrorCode.GATE_RESULT_OWNERSHIP.value if gate_reason else None)
        if gate_reason:
            env = {
                "status": "unsupported",
                "reason": gate_reason,
                "failure_category": "capability_gap",
                "representation_plan": plan,
                "analysis": analysis,
            }
            _emit(observer, "envelope", status="unsupported", simulation_id=None,
                  failure_category="capability_gap")
            return env

        # Không cổng nào có phán quyết thật ⇒ giờ mới nói tới lỗi hợp đồng.
        if deferred_scope is not None:
            return _scope_refusal(deferred_scope)

    if classification.get("status") != "ok":
        # W2C-C1 §L3 — GIỮ ĐÚNG BẢN CHẤT LỜI TỪ CHỐI.
        # Live W2C: classify tự từ chối đề "mô phỏng một vòng lặp while" TRƯỚC
        # khi cổng đủ-dữ-kiện kịp chạy, nên envelope không có `failure_category`
        # và FE mất tiêu đề "CHƯA ĐỦ DỮ KIỆN" — học sinh đọc thành "ngoài danh
        # mục" trong khi dạng bài này hệ CÓ mô phỏng, chỉ thiếu dữ kiện.
        # Suy ra nhãn bằng CHÍNH hạ tầng đủ-dữ-kiện dùng chung, trên family mà
        # analyze tự khai — KHÔNG khớp từ khoá đề, KHÔNG thêm stage, KHÔNG sửa
        # classify. Không suy được thì để trống (thà không nhãn còn hơn nhãn sai).
        category = _refusal_category(analysis)
        _emit(observer, "envelope", status="unsupported", simulation_id=None,
              failure_category=category)
        env = {
            "status": "unsupported",
            "reason": classification.get("reason")
            or "Bài này chưa có mô phỏng phù hợp trong danh mục.",
            "representation_plan": plan,
        }
        if category:
            env["failure_category"] = category
        return env

    simulation_id = classification["simulation_id"]

    # M14 §E — NHÁNH FAMILY SELECTOR (vd comparison_sort): mechanism gate (tầng 1)
    # → sinh FamilySpec → resolve TẤT ĐỊNH → validate concrete → envelope mang
    # CONCRETE id (token selector KHÔNG BAO GIỜ là envelope id, §D).
    selector = selector_for_token(simulation_id)
    if selector is not None:
        gate = check_mechanism_ownership(analysis, selector)
        _emit(observer, "gate_checked", gate="mechanism", fired=bool(gate),
              reason_code=gate[0].value if gate else None)
        if gate is not None:
            _emit(observer, "envelope", status="unsupported", simulation_id=None,
                  failure_category="capability_gap")
            return {
                "status": "unsupported",
                "reason": gate[1],
                "failure_category": "capability_gap",
                "error_code": gate[0].value,
                "representation_plan": plan,
                "analysis": analysis,
            }
        # M17-RC1 §C2 — cổng đủ dữ kiện trên nhánh SELECTOR: target cụ thể chỉ
        # biết sau resolve, nên kiểm theo GIAO các nhóm bắt buộc của mọi variant
        # (không đòi thừa). Sorting: mọi biến thể đều cần một dãy số.
        sel_targets = [v.concrete_simulation_id for v in selector.variants]
        sel_suff = check_input_sufficiency_for_targets(analysis, sel_targets)
        _emit(observer, "gate_checked", gate="input_sufficiency",
              fired=bool(sel_suff), reason_code=sel_suff[0].value if sel_suff else None)
        if sel_suff is not None:
            _emit(observer, "envelope", status="unsupported", simulation_id=None,
                  failure_category="insufficient_specification")
            return {
                "status": "unsupported",
                "reason": sel_suff[1],
                "failure_category": "insufficient_specification",
                "error_code": sel_suff[0].value,
                "input_sufficiency": sel_suff[2],
                "representation_plan": plan,
                "analysis": analysis,
            }

        # M17-RC1 §D PHA 1 trên NHÁNH SELECTOR. Bỏ sót ở đây là lỗ THẬT (RC1-C
        # phát hiện): family comparison_sort route qua token nên `_families` ở
        # nhánh direct bên dưới không bao giờ chạy — đề "sắp xếp nổi bọt RỒI
        # chèn" trả ok và bỏ im lặng một nửa. Đúng family duy nhất có tín hiệu
        # analyze giàu nhất lại là family lọt cổng.
        _sel_families = {selector.family_id.value}
        combo = check_requested_combination(analysis, _sel_families)
        _emit(observer, "gate_checked", gate="completeness_requested",
              fired=bool(combo), reason_code=combo[0].value if combo else None)
        if combo is not None:
            _emit(observer, "envelope", status="unsupported", simulation_id=None,
                  failure_category="semantic_incomplete")
            return {
                "status": "unsupported",
                "reason": combo[1],
                "failure_category": "semantic_incomplete",
                "error_code": combo[0].value,
                "completeness": combo[2],
                "representation_plan": plan,
                "analysis": analysis,
            }
        family_config, ferr = await stage_simulate_family(text, analysis, selector, api_key, observer=observer)
        if family_config is None:
            raise RuntimeError(
                f"Không sinh được FamilySpec hợp lệ cho {simulation_id} sau 3 lần thử "
                f"(lỗi cuối: {ferr})."
            )
        concrete_id, concrete_config = selector.resolve(family_config, analysis)
        _emit(observer, "family_resolved", family_id=selector.family_id.value,
              variant=family_config["variant"], concrete_id=concrete_id)
        concrete_spec = CATALOG.get(concrete_id)
        if concrete_spec is None:  # adapter trỏ target không tồn tại (lock C4 chống)
            raise RuntimeError(f"Adapter trỏ tới target không tồn tại: {concrete_id}.")
        validated, verr = concrete_spec.validate(concrete_config)
        if validated is None:  # validation kép qua validator concrete hiện có
            raise RuntimeError(
                f"Config sau adapter không qua validator concrete ({concrete_id}): {verr}"
            )
        # PHA 2 trên nhánh selector: đối chiếu với cái CONCRETE SPEC thực sự
        # biểu diễn (variant ĐÃ resolve, target CỤ THỂ — không phải cả family).
        incomplete = _completeness_phase2(
            analysis, concrete_id, validated, plan, observer,
            variant=family_config["variant"],
        )
        if incomplete is not None:
            return incomplete
        _emit(observer, "envelope", status="ok", simulation_id=concrete_id, source="family_resolved")
        return {
            "status": "ok",
            "simulation_id": concrete_id,
            "domain": concrete_spec.domain,
            "visual_mode": concrete_spec.visual_mode,
            "title": concrete_spec.make_title(validated, analysis),
            "description": f"{analysis.get('input_description', '')} → {analysis.get('output_description', '')}",
            "config": validated,
            "notes": validated.get("notes") if isinstance(validated, dict) else None,
            "analysis": analysis,
            "representation_plan": plan,
            "source": "family_resolved",
            "family_id": selector.family_id.value,
            "variant": family_config["variant"],
        }

    # M15 Task 6 — DIRECT ENTRY (không selector): ownership gate trên FINAL route.
    # Nhánh mismatch (nhánh 3) đã xử ở recovery; ở đây thường chỉ còn ownership
    # (nhánh 2), nhánh mismatch là DEFENSIVE — vẫn fail-closed cùng khuôn.
    direct_verdict = check_mechanism_consistency_for_target(analysis, CATALOG[simulation_id])
    if direct_verdict is not None:
        _emit(observer, "gate_checked", gate="mechanism", fired=True,
              reason_code=direct_verdict[0].value)
        _emit(observer, "envelope", status="unsupported", simulation_id=None,
              failure_category="capability_gap")
        return {
            "status": "unsupported",
            "reason": direct_verdict[1],
            "failure_category": "capability_gap",
            "error_code": direct_verdict[0].value,
            "representation_plan": plan,
            "analysis": analysis,
        }
    else:
        _emit(observer, "gate_checked", gate="mechanism", fired=False, reason_code=None)

    # M17-RC1 §C2 — CỔNG ĐỦ DỮ KIỆN DÙNG CHUNG (TRƯỚC simulate), thay cho gate
    # riêng của tree ở W2A: đề chưa cho dữ kiện bắt buộc của target đã chọn →
    # từ chối thay vì để LLM bịa (dãy số, số cần đổi, cấu trúc cây/đồ thị, mạch
    # logic…). Một cổng, mọi target; khác biệt nằm ở HỢP ĐỒNG
    # (`input_requirements`) + normalizer theo NHÓM dữ kiện, không phải ở code
    # riêng cho từng target. Chỉ sau PASS mới được dựng spec.
    suff_verdict = check_input_sufficiency(analysis, simulation_id)
    _emit(observer, "gate_checked", gate="input_sufficiency",
          fired=bool(suff_verdict),
          reason_code=suff_verdict[0].value if suff_verdict else None)
    if suff_verdict is not None:
        _emit(observer, "envelope", status="unsupported", simulation_id=None,
              failure_category="insufficient_specification")
        return {
            "status": "unsupported",
            "reason": suff_verdict[1],
            "failure_category": "insufficient_specification",
            "error_code": suff_verdict[0].value,
            "input_sufficiency": suff_verdict[2],
            "representation_plan": plan,
            "analysis": analysis,
        }

    # M17-RC1 §D PHA 1 — tập YÊU CẦU tự nó vượt chính sách family (vd đề hỏi cả
    # 4 kiểu duyệt cây trong khi một lần chỉ dựng được một) → chặn TRƯỚC simulate,
    # không tốn lượt LLM và không bao giờ trả lời nửa vời.
    _families = {m.family_id.value for m in CATALOG[simulation_id].family_memberships}
    combo_verdict = check_requested_combination(analysis, _families)
    _emit(observer, "gate_checked", gate="completeness_requested",
          fired=bool(combo_verdict),
          reason_code=combo_verdict[0].value if combo_verdict else None)
    if combo_verdict is not None:
        _emit(observer, "envelope", status="unsupported", simulation_id=None,
              failure_category="semantic_incomplete")
        return {
            "status": "unsupported",
            "reason": combo_verdict[1],
            "failure_category": "semantic_incomplete",
            "error_code": combo_verdict[0].value,
            "completeness": combo_verdict[2],
            "representation_plan": plan,
            "analysis": analysis,
        }

    spec = CATALOG[simulation_id]

    roles = required_roles(analysis)

    # M7.13B tầng 2: pattern reuse CHỈ thay stage_simulate của generic —
    # specialized đi đường cũ nguyên vẹn (không regression selection).
    reuse_meta = {"attempted": False}
    if pattern_store is not None and simulation_id == "generic.rule_scene":
        config, reuse_meta = await try_pattern_reuse(
            text, analysis, plan, roles, api_key, pattern_store
        )
        if config is not None:
            # PHA 2 cũng chạy trên đường TÁI DÙNG PATTERN — đường này bỏ qua
            # stage_simulate nên trước đây trả thẳng envelope ok. Config tái
            # dùng vẫn phải đáp ứng ĐỦ yêu cầu của đề HIỆN TẠI.
            incomplete = _completeness_phase2(analysis, simulation_id, config, plan, observer)
            if incomplete is not None:
                return incomplete
            _emit(observer, "envelope", status="ok", simulation_id=simulation_id, source="pattern_reuse")
            return {
                "status": "ok",
                "simulation_id": simulation_id,
                "domain": spec.domain,
                "visual_mode": spec.visual_mode,
                "title": spec.make_title(config, analysis),
                "description": f"{analysis.get('input_description', '')} → {analysis.get('output_description', '')}",
                "config": config,
                "notes": config.get("notes") if isinstance(config, dict) else None,
                "analysis": analysis,
                "representation_plan": plan,
                "source": "pattern_reuse",
                "pattern_key": reuse_meta.get("pattern_key"),
                "adapt_used": reuse_meta.get("adapt_used", False),
            }

    config, error = await stage_simulate(
        text, analysis, simulation_id, api_key, required_semantic_roles=roles, plan=plan,
        observer=observer,
    )
    if config is None and error and error.startswith("__GAP__:"):
        # Retry lộ ra vai trò không cover được (phòng hờ — thường plan chặn trước)
        missing = error[len("__GAP__:"):]
        _emit(observer, "envelope", status="unsupported", simulation_id=None,
              failure_category="capability_gap")
        return {
            "status": "unsupported",
            "reason": (
                "Đề cần khả năng biểu diễn mà DSL hiện chưa có "
                f"(vai trò: {missing}). Chưa thể mô phỏng đúng bản chất bài này."
            ),
            "failure_category": "capability_gap",
            "representation_plan": plan,
            "analysis": analysis,
        }
    if config is None:
        _emit(observer, "envelope", status="error", simulation_id=None, failure_category="synthesis_exhausted")
        return {
            "status": "error",
            "reason": (
                f"Không sinh được cấu hình mô phỏng hợp lệ sau 3 lần thử (lỗi cuối: {error}). "
                "Hãy diễn đạt lại đề rõ ràng hơn rồi thử lại."
            ),
            "failure_category": "synthesis_exhausted",
            "representation_plan": plan,
            "analysis": analysis,
        }

    # M17-RC1 §D PHA 2 — spec ĐÃ VALIDATE có bỏ sót yêu cầu nào không? Chạy
    # TRƯỚC khi phát envelope (tức trước executor FE). Bất biến: status=ok ⟹
    # dropped_requirements rỗng — không bao giờ trả lời nửa vời rồi báo "xong".
    incomplete = _completeness_phase2(analysis, simulation_id, config, plan, observer)
    if incomplete is not None:
        return incomplete

    # M7.13B: compose-new thành công → thử persist reusable pattern (best-effort;
    # extraction ngoài safe allowlist / round-trip lệch / cổng fail → không lưu).
    if pattern_store is not None and simulation_id == "generic.rule_scene":
        try:
            pattern_store.persist_from_spec(plan["scene_mode"], roles, config)
        except Exception:
            pass  # lỗi persist không được làm hỏng envelope trả người dùng

    _emit(observer, "envelope", status="ok", simulation_id=simulation_id, source="composed")
    return {
        "status": "ok",
        "simulation_id": simulation_id,
        "domain": spec.domain,
        "visual_mode": spec.visual_mode,
        "title": spec.make_title(config, analysis),
        "description": f"{analysis.get('input_description', '')} → {analysis.get('output_description', '')}",
        "config": config,
        "notes": config.get("notes") if isinstance(config, dict) else None,
        "analysis": analysis,
        "representation_plan": plan,
        "source": "composed",
        "reuse_fallback": bool(reuse_meta.get("attempted")),
    }
